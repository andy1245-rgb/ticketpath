//! Account layouts, PDA seeds, and every predicate the program branches on.
//!
//! One file, because the byte layout is the contract: `ticketpath/onchain/v2.py` decodes
//! these same bytes and the two are only kept honest by a test that reads an account this
//! program wrote (tests/test_onchain_v2_live.py). Every `LEN` below is asserted against
//! `BorshSerialize::serialize(bytes).len()` in `tests.rs`, so a field added without its
//! length is a failing test and not a silent layout change.
//!
//! Borsh, little-endian, no length prefix on any field. No Anchor discriminator: the tag
//! byte in the instruction data is the whole discriminator, and the account kind is implied
//! by the PDA it sits at.

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::pubkey::Pubkey;

/// `policy` value 0: the cap and the floor are enforced. The default.
pub const POLICY_CAPPED: u8 = 0;
/// `policy` value 1: the cap and the floor are recorded and logged but not enforced.
///
/// What this does NOT do: it does not disable the hook. The hook still runs, still refuses
/// `amount != 1` and still refuses a transfer with nothing staged, and it still writes
/// `held_since_unix`. "Monitored" means the two price predicates stop refusing, and the log
/// line says `policy=monitored` so the chain itself records that the cap was not the reason.
pub const POLICY_MONITORED: u8 = 1;

/// The jurisdiction code used when an event has none. Two capital letters for every real
/// ISO-3166-1 alpha-2 code, so `ZZ` is the only value in the domain that is not a country,
/// and it is legal on purpose: refusing it would force an issuer to name a jurisdiction they
/// do not have. MD3 fixes the meaning.
pub const JURISDICTION_UNSPECIFIED: [u8; 2] = *b"ZZ";

/// How long a holder must hold for the flip-tax rebate to reach its full rate.
///
/// **This is the demo's value and not a market's.** The flip tax exists to make a quick flip
/// pay less than a long hold, so the production number is weeks. Sixty seconds is chosen so
/// that the rebate can be observed inside one bounded local-validator run; the arithmetic is
/// a pure function of this constant and `rebate_lamports` is unit-tested either side of it,
/// so changing the number changes the rate and nothing else.
pub const HOLD_FULL_SECONDS: i64 = 60;

/// The flip tax rate the rebate is a share of, in basis points (MD4: 1500 = 15%).
///
/// Read from a constant rather than from the mint's `TransferFeeConfig` because parsing that
/// extension means this program would have to agree with Token-2022 about a pod layout, and
/// a program that reads a rate and a program that charges a rate must be the same number:
/// the one that charges it is Token-2022, configured at mint creation by whoever holds the
/// config authority. So this constant is the *policy* number the rebate divides by, and the
/// mint is configured to match it. A mismatch is a business error the chain cannot see, and
/// the README says so.
pub const REBATE_FEE_BPS: u16 = 1500;

/// The state the hook reads and writes. MD3's table, in MD3's order.
///
/// `authority` is the mint's authority at the moment the record was created: the signature
/// `InitializeRecord` requires, so the key that fixes the cap, the floor and the policy is the
/// key that issued the ticket and nobody else. It is also the only signer allowed to stage a
/// price, flip `status`, publish a band, log a forecast or write a score. It is not the ticket
/// holder: it is the party accountable for the numbers this record and its satellites assert.
#[derive(BorshSerialize, BorshDeserialize, Debug, Clone, PartialEq, Eq)]
pub struct TicketRecord {
    /// Face value of this ticket's tier, in lamports. The cap is a multiple of this.
    pub face_value_lamports: u64,
    /// Resale cap in basis points over face. 2500 means +25%; the wire convention.
    pub cap_bps: u16,
    /// The price staged for the transfer the hook is about to see, in lamports. The hook
    /// clears it when it admits the transfer, so one staging admits one sale: the next
    /// transfer with nothing staged is refused `6009`.
    pub pending_price_lamports: u64,
    /// 1 = transferable, 0 = not.
    pub status: u8,
    /// A price below this is refused. 0 means no floor, and there is no way to tell "no
    /// floor" from "a floor of zero lamports" — which is the same thing, and saying so is
    /// cheaper than a flag.
    pub band_low_lamports: u64,
    /// ISO-3166-1 alpha-2, two uppercase ASCII bytes; `ZZ` = unspecified (MD3, feature 10).
    /// The program does not validate the country: a wrong code is a wrong statement by the
    /// issuer, not a malformed account, and there is no list on chain to check against.
    pub jurisdiction: [u8; 2],
    /// 0 = capped, 1 = monitored. See `POLICY_*`.
    pub policy: u8,
    /// Unix seconds at which the current holder acquired the ticket, written by the hook on
    /// every admitted transfer. 0 = unknown, which is what a ticket that has never moved
    /// carries: the hook is the only writer, and it has not run.
    pub held_since_unix: i64,
    /// The only signer allowed to write this record or its satellites. See the struct comment.
    pub authority: Pubkey,
}

impl TicketRecord {
    /// 8 + 2 + 8 + 1 + 8 + 2 + 1 + 8 + 32. Asserted against a real serialization in tests.rs.
    pub const LEN: usize = 70;

    /// §3.10, exactly: both sides in `u128`, no division anywhere, inclusive at the cap.
    pub fn cap_admits(&self) -> bool {
        let lhs = (self.pending_price_lamports as u128) * 10_000u128;
        let rhs = (self.face_value_lamports as u128) * (10_000u128 + self.cap_bps as u128);
        lhs <= rhs
    }

    /// The floor (feature 6), inclusive: a price equal to the floor is admitted.
    ///
    /// `band_low_lamports == 0` means no floor, and the predicate is true for every price.
    /// This is deliberately a second predicate and not `cap_admits` with an extra term: the
    /// two bounds have separate error codes because a client has to tell a seller whether
    /// their ask was too high or too low, and one code for both is a message that reads
    /// "your price is wrong" and nothing else.
    pub fn floor_admits(&self) -> bool {
        self.band_low_lamports == 0 || self.pending_price_lamports >= self.band_low_lamports
    }

    /// True when `key` is the record's authority. Compared as a key, never as an index.
    pub fn authorises(&self, key: &Pubkey) -> bool {
        self.authority == *key
    }

    /// True when the two price predicates still refuse. `monitored` records the price.
    pub fn enforces(&self) -> bool {
        self.policy == POLICY_CAPPED
    }
}

/// The public price feed (feature 8). MD3's layout; `["band", mint]`.
///
/// Rewritable on purpose: the head of a published band moves as new evidence arrives, and the
/// history of it is the forecast log, not this account. A consumer that wants the band as of a
/// decision reads the forecast, not this. `published_slot` is this program's clock and
/// `as_of_slot` is the model's: they answer different questions and both are stored.
#[derive(BorshSerialize, BorshDeserialize, Debug, Clone, PartialEq, Eq)]
pub struct Band {
    /// 1. Bumped only by a layout change, and a reader must refuse a version it does not know.
    pub version: u8,
    pub low: u64,
    pub high: u64,
    /// The slot the model says the estimate is as of.
    pub as_of_slot: u64,
    /// The slot this write landed in. `as_of_slot` above it is refused `6033`: an estimate
    /// dated after the write that carried it is a claim about the future, and the as-of is the
    /// publisher's word either way.
    pub published_slot: u64,
    /// How many observations the estimate rests on. A band with n = 1 is an anecdote and the
    /// account says so rather than leaving the consumer to guess. `sample_n == 0` is refused
    /// `6032` unless `refused` is set: no observations and no refusal is a number with nothing
    /// behind it and no statement that it is a refusal.
    pub sample_n: u32,
    /// Non-zero when the publisher is stating a refusal (the model declined to price), in
    /// which case `low`/`high` are the fallback bounds. Normalised to 0 or 1 on write, so the
    /// stored byte is a flag and not a count.
    pub refused: u8,
    pub model_hash: [u8; 32],
    pub authority: [u8; 32],
}

impl Band {
    /// 1 + 8 + 8 + 8 + 8 + 4 + 1 + 32 + 32.
    pub const LEN: usize = 102;
}

/// One immutable forecast (feature 4). MD3's layout; `["forecast", mint, as_of_unix_le]`.
///
/// Create-once. There is no instruction that rewrites one, and `LogForecast` refuses if the
/// account already exists (`6024`), so a forecast cannot be revised after the outcome is known.
/// That refusal is the whole of what the account proves, and here is what it does not prove.
///
/// **A create-once account can still be created after the fact.** Rewriting is refused;
/// *creating* the account for an instant that has already passed is the same measurement
/// problem with one extra step. The one thing the chain can check is the clock: `LogForecast`
/// refuses an `as_of_unix` earlier than the clock minus `FORECAST_BACKDATE_TOLERANCE_SECONDS`
/// (`6029`), so a forecast cannot be backdated beyond that tolerance. What it cannot stop is an
/// authority that publishes *at* (or, within the tolerance, just after) the instant it claims to
/// be as-of: a forecast written at the as-of and a forecast written five minutes before it are
/// the same bytes to this program. So the account proves "this band was committed no later than
/// its as-of plus the stated tolerance, and never changed after", which is a real constraint on
/// a revision and not a proof that the model could not see the outcome.
#[derive(BorshSerialize, BorshDeserialize, Debug, Clone, PartialEq, Eq)]
pub struct Forecast {
    pub version: u8,
    /// Carried inside the account as well as in the seeds, so a decoded forecast names its
    /// own mint without the reader having to also hold the mint. 32 bytes is cheap; a
    /// mis-paired decode is not.
    pub mint: [u8; 32],
    pub low: u64,
    pub high: u64,
    /// Unix seconds the forecast is *about*. Also a seed component: one forecast per instant.
    pub as_of_unix: i64,
    pub sample_n: u32,
    pub model_hash: [u8; 32],
    /// Hash of the scoring rule that will be applied. Committed here, before the outcome, so
    /// the score cannot be computed under a rule chosen afterwards.
    pub scoring_rule_hash: [u8; 32],
    pub created_slot: u64,
    pub authority: [u8; 32],
}

impl Forecast {
    /// 1 + 32 + 8 + 8 + 8 + 4 + 32 + 32 + 8 + 32.
    pub const LEN: usize = 165;

    /// True when `realised` falls inside the published interval, inclusive at both ends.
    /// Inclusive because the interval is a statement about the closed range; a model that
    /// says [a, b] and is graded as covering b only on the open side is graded against a
    /// rule it did not publish.
    pub fn covers(&self, realised: u64) -> bool {
        self.low <= realised && realised <= self.high
    }
}

/// The score of one forecast (feature 4's second half). `["score", forecast]`.
///
/// Create-once, for the same reason the forecast is: a score that can be rewritten is not a
/// check on anything. `interval_score_micro` is stored in whatever micro-units the scoring rule
/// defines, and the rule's hash is in the forecast, so the number and its definition travel
/// together.
///
/// **The number is an assertion, and the chain checks only one side of it.** `ScoreForecast`
/// recomputes `covered` from the forecast's own ends, so that flag cannot disagree with the
/// interval that was committed first. It does not recompute the interval score: the rule's
/// penalty term depends on the realised price and on the hit/miss distance, and the program has
/// no rule text to run. What it does check is the direction that cannot be faked downward: the
/// width term is the floor of the rule, so a score below `(high - low) * 1_000_000` is refused
/// (`6030`). An **overstated** error is undetectable here: an authority can write any number
/// from the width upward, including one far worse than the rule gives. A consumer that needs
/// the true score recomputes it from the forecast, the realised price and the committed rule
/// hash; the account records what the authority claimed, and that it could not claim a score
/// better than the band's own width.
#[derive(BorshSerialize, BorshDeserialize, Debug, Clone, PartialEq, Eq)]
pub struct Score {
    pub version: u8,
    pub realised_lamports: u64,
    pub interval_score_micro: u64,
    /// 1 when the realised price fell inside the forecast's interval, else 0.
    pub covered: u8,
    pub scored_slot: u64,
    pub scorer: [u8; 32],
}

impl Score {
    /// 1 + 8 + 8 + 1 + 8 + 32.
    pub const LEN: usize = 58;
}
/// The ceiling in lamports, `face * (10_000 + cap_bps) / 10_000`, floored.
///
/// **Display and validation only.** The admission predicate is `cap_admits`, which compares
/// products and never divides (§3.10 point 2). This function exists for two callers that need
/// a number rather than a comparison: `InitializeRecord`'s band check, which is written as a
/// product too, and a client formatting "max resale". Nothing on the admission path divides.
pub fn ceiling_lamports(face: u64, cap_bps: u16) -> u128 {
    (face as u128) * (10_000u128 + cap_bps as u128) / 10_000u128
}

/// False when `band_low` is above the ceiling, which would make every price refusable.
///
/// A floor above the ceiling is an unsatisfiable pair: no price is both `<= ceiling` and
/// `>= floor`, so the ticket could never transfer, and the record would be a brick that looks
/// like a ticket. The check is a product comparison for the same reason the cap is:
/// `band_low <= floor(face*(10000+cap)/10000)` iff
/// `band_low*10000 <= face*(10000+cap)` for integers, and the second form never rounds.
pub fn band_satisfiable(face: u64, cap_bps: u16, band_low: u64) -> bool {
    if band_low == 0 {
        return true;
    }
    (band_low as u128) * 10_000u128 <= (face as u128) * (10_000u128 + cap_bps as u128)
}

/// Seconds the current holder has held, clamped at zero. `0` also means "unknown".
///
/// A clock can go backwards between the write and the read (an operator restarting a ledger,
/// a validator whose clock is not the one that wrote the field). Clamping is the choice that
/// pays nothing rather than paying the maximum.
pub fn held_seconds(held_since_unix: i64, now: i64) -> i64 {
    now.saturating_sub(held_since_unix).max(0)
}

/// The share, in basis points, of the withheld fee a holder of `held` seconds has earned:
/// `REBATE_FEE_BPS * min(held, HOLD_FULL) / HOLD_FULL`.
///
/// Clamped at the top, so holding longer than `HOLD_FULL` earns nothing extra. That is what
/// makes it a tax on flipping rather than a rebate for hoarding.
pub fn rebate_bps(held: i64) -> u64 {
    let clamped = held.clamp(0, HOLD_FULL_SECONDS) as u128;
    // At most `REBATE_FEE_BPS`, so the quotient is far inside a u64; the cast is the value,
    // not a truncation.
    ((REBATE_FEE_BPS as u128) * clamped / (HOLD_FULL_SECONDS as u128)) as u64
}

/// The largest amount the pool may pay a holder who has held `held` seconds.
///
/// `pool * rebate_bps(held) / 10_000`, floored, in `u128` so no intermediate wraps. The
/// result is `u64` because a token amount is a `u64`; the division is by 10_000 with a
/// numerator bounded by `u64::MAX * 1500`, so the quotient always fits.
pub fn rebate_lamports(pool_lamports: u64, held: i64) -> u64 {
    let numerator = (pool_lamports as u128) * (rebate_bps(held) as u128);
    (numerator / 10_000u128) as u64
}

/// The predicate form of [`rebate_lamports`], with no division: true when `amount` is no more
/// than the holder's share of `pool`.
///
/// This is the pair §3.10 asks for on the cap, applied to the rebate. `rebate_lamports`
/// floors, so `rebate_admits(pool, held, rebate_lamports(pool, held))` is true and the next
/// lamport is false; the unit test asserts both sides.
pub fn rebate_admits(pool_lamports: u64, held: i64, amount: u64) -> bool {
    let clamped = held.clamp(0, HOLD_FULL_SECONDS) as u128;
    let lhs = (amount as u128) * (HOLD_FULL_SECONDS as u128) * 10_000u128;
    let rhs = (pool_lamports as u128) * (REBATE_FEE_BPS as u128) * clamped;
    lhs <= rhs
}

// -- the score's domain -------------------------------------------------------
//
// `interval_score_micro` is a `u64`, and the rule multiplies lamports by 1_000_000, so the
// field can hold at most 18_446_744_073_709 lamports of band width. Both numbers are stated
// here rather than at the call sites: the limit is a property of the field, and a client, a
// test and the program have to agree on it.

/// The scale the scoring rule uses, `micro-lamports per lamport`.
pub const SCORE_MICRO_SCALE: u64 = 1_000_000;

/// The widest band whose width alone still fits `interval_score_micro`:
/// `MAX_BAND_WIDTH_LAMPORTS * 1_000_000 <= u64::MAX`. 18_446_744_073_709 lamports is about
/// 18,446.7 SOL. A wider forecast can never be scored, so `LogForecast` refuses it (`6031`)
/// instead of writing a forecast that can never have a score.
pub const MAX_BAND_WIDTH_LAMPORTS: u64 = u64::MAX / SCORE_MICRO_SCALE;

// -- PDA seeds ---------------------------------------------------------------
//
// Each returns the seed slices without the bump; the caller appends `[bump]` for
// `invoke_signed`. The instruction always re-derives with `find_program_address` and compares
// against the account it was handed, so a client cannot pass an account at the right address
// for a different mint.

/// `["record", mint]` — the hook's record, one per mint.
pub fn record_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"record", mint.as_ref()]
}

/// `["extra-account-metas", mint]` — the literal is fixed by the SPL interface.
pub fn extra_metas_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"extra-account-metas", mint.as_ref()]
}

/// `["band", mint]` — the public feed's head.
pub fn band_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"band", mint.as_ref()]
}

/// `["forecast", mint, as_of_unix_le_i64]` — one forecast per (mint, instant).
///
/// The `as_of_unix` bytes are a temporary the caller owns (`to_le_bytes()`), so the caller
/// builds the three-slice array: `[b"forecast", mint.as_ref(), &as_of_bytes]`. This function
/// is the first two seeds and exists so the literal is spelled once.
pub fn forecast_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"forecast", mint.as_ref()]
}

/// `["score", forecast]` — one score per forecast.
pub fn score_seeds(forecast: &Pubkey) -> [&[u8]; 2] {
    [b"score", forecast.as_ref()]
}

/// `["fee-authority", mint]` — the mint's `withdraw_withheld_authority`, a PDA this program
/// signs for. It is an authority that nobody can use except through `ClaimRebate`.
pub fn fee_authority_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"fee-authority", mint.as_ref()]
}

/// `["rebate-pool", mint]` — owns the pool token account the withheld fees are harvested into.
pub fn rebate_pool_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"rebate-pool", mint.as_ref()]
}
