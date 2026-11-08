//! `cap_hook` — the smallest transfer hook that can refuse a resale.
//!
//! Imported from the scratch crate `ticketpath-hook`, where it was first deployed and
//! exercised against a local validator (records/findings/18-onchain-install-and-test.md).
//! The crate name changed on import; nothing else did, and the program id is a property
//! of the deploy keypair, not of this name.
//!
//! The design is docs/ON-CHAIN-DESIGN.md §1.3, §3.9 and §3.10: Token-2022 calls this
//! program inside `Execute` on every transfer of a hooked mint, and the program refuses
//! when the staged resale price is above the ticket's cap, or below its floor.
//!
//! What a hook can and cannot see is the whole point of §1.3. Token-2022 hands the hook
//! `amount`, the source and destination token accounts, the mint and its authority. **It
//! never hands over a price** — there is no price field in an SPL transfer. So the cap is
//! only enforceable over a price that arrived some other way. Here that is a `record`
//! account this program owns, staged in a previous instruction, and named in the mint's
//! extra-account-metas list. The hook reads it and refuses; it cannot invent it.
//!
//! The instructions this program adds beyond `Execute` exist so the state can be created,
//! written and staged: initialise the extra-account-metas list (0), initialise a record (1),
//! stage a price (2), flip the transferable flag (3), publish a band (4), log a forecast (5)
//! and score it (6). In the real design (§1.4) the staging instruction is the escrow or the
//! listing, not a free-standing `set_price`; this is the minimum that can be measured. What it
//! is not any more is open to strangers: the record's `authority` signs the writes that move
//! the price, the status or a satellite, and the mint's own authority signs the record's
//! creation.
//!
//! v2 (MD3) is the record in `state.rs` and the numbers in `error.rs`; this file is the
//! instruction wire format and the hook. `InitializeRecord` carries the floor, the
//! jurisdiction and the policy as well as face and cap, the hook refuses below the floor
//! with 6021, a `monitored` record (policy 1) refuses on neither price predicate and says
//! so in its log line, and every admitted transfer writes `held_since_unix` and clears the
//! staged price so that one staging admits one sale.
//!
//! Tags 4..6 are the forecast log: `PublishBand` (4) writes the rewritable head of the
//! public feed, `LogForecast` (5) creates one immutable forecast per `(mint, as_of_unix)`,
//! and `ScoreForecast` (6) creates one immutable score per forecast without touching the
//! forecast it scores. ClaimRebate (7, MD4) is not implemented here.
//!
//! Cap predicate, verbatim from §3.10, in `u128` with no division:
//!
//! ```text
//! price * 10_000 <= face * (10_000 + cap_bps)
//! ```
//!
//! Inclusive at the cap: face 1_000_000_000 with cap 2500 admits exactly 1_250_000_000
//! and refuses 1_250_000_001.
//!
//! Floor predicate (feature 6), also inclusive and also division-free:
//!
//! ```text
//! band_low == 0 || price >= band_low
//! ```

mod error;
mod state;

#[cfg(test)]
mod tests;

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    clock::Clock,
    entrypoint::ProgramResult,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};
use spl_tlv_account_resolution::{account::ExtraAccountMeta, state::ExtraAccountMetaList};
use spl_transfer_hook_interface::instruction::{ExecuteInstruction, TransferHookInstruction};

pub use error::TicketpathError;
pub use state::{
    band_satisfiable, band_seeds, ceiling_lamports, extra_metas_seeds, forecast_seeds,
    held_seconds, rebate_admits, rebate_bps, rebate_lamports, record_seeds, score_seeds, Band,
    Forecast, Score, TicketRecord, HOLD_FULL_SECONDS, JURISDICTION_UNSPECIFIED,
    MAX_BAND_WIDTH_LAMPORTS, POLICY_CAPPED, POLICY_MONITORED, REBATE_FEE_BPS, SCORE_MICRO_SCALE,
};

/// The version byte every satellite account carries. A reader refuses a version it does not
/// know; this program writes only this one.
pub const SATELLITE_VERSION: u8 = 1;

/// Instruction set. `0..=6` are this program's own; anything else falls through to the
/// SPL transfer-hook discriminator, whose first byte is 105, so they cannot collide.
pub enum HookInstruction {
    /// 0 — create the extra-account-metas PDA for a mint, naming the record account.
    ///
    /// No arguments. The record named in the list is `["record", mint]`, derived here from the
    /// mint account, so there is nothing for a caller to get wrong: a list that named any
    /// other account would be a list this program never creates and could never correct,
    /// because the list is create-once.
    InitializeExtraAccountMetaList,
    /// 1 — create the record for a mint.
    ///
    /// Wire bytes after the tag, little-endian, in this order: `face` u64 (8), `cap_bps`
    /// u16 (2), `band_low` u64 (8), `jurisdiction` [u8; 2] (2), `policy` u8 (1). That is
    /// 21 argument bytes behind a 1-byte tag, 22 in total. `jurisdiction` is two raw bytes,
    /// uppercase ISO-3166-1 alpha-2, `ZZ` for unspecified; it is stored as written.
    InitializeRecord {
        face: u64,
        cap_bps: u16,
        band_low: u64,
        jurisdiction: [u8; 2],
        policy: u8,
    },
    /// 2 — stage the price for the next transfer. `[authority (signer), record, mint]`.
    SetPendingPrice { price: u64 },
    /// 3 — flip the record's transferable flag. `[authority (signer), record, mint]`.
    SetStatus { status: u8 },
    /// 4 — write the head of the public price feed for a mint.
    ///
    /// Wire bytes after the tag, little-endian, at these offsets: `low` u64 (0, 8),
    /// `high` u64 (8, 8), `as_of_slot` u64 (16, 8), `sample_n` u32 (24, 4), `refused`
    /// u8 (28, 1), `model_hash` [u8; 32] (29, 32). That is 61 argument bytes behind a
    /// 1-byte tag, 62 in total.
    PublishBand {
        low: u64,
        high: u64,
        as_of_slot: u64,
        sample_n: u32,
        refused: u8,
        model_hash: [u8; 32],
    },
    /// 5 — create the one forecast for `(mint, as_of_unix)`.
    ///
    /// Wire bytes after the tag, little-endian, at these offsets: `low` u64 (0, 8),
    /// `high` u64 (8, 8), `as_of_unix` i64 (16, 8), `sample_n` u32 (24, 4),
    /// `model_hash` [u8; 32] (28, 32), `scoring_rule_hash` [u8; 32] (60, 32). That is
    /// 92 argument bytes behind a 1-byte tag, 93 in total.
    LogForecast {
        low: u64,
        high: u64,
        as_of_unix: i64,
        sample_n: u32,
        model_hash: [u8; 32],
        scoring_rule_hash: [u8; 32],
    },
    /// 6 — create the one score for a forecast. The forecast is read-only here.
    ///
    /// Wire bytes after the tag, little-endian, at these offsets: `realised_lamports`
    /// u64 (0, 8), `interval_score_micro` u64 (8, 8). That is 16 argument bytes behind a
    /// 1-byte tag, 17 in total.
    ScoreForecast {
        realised_lamports: u64,
        interval_score_micro: u64,
    },
}

impl HookInstruction {
    fn unpack(data: &[u8]) -> Result<Self, ProgramError> {
        let (tag, rest) = data
            .split_first()
            .ok_or(ProgramError::InvalidInstructionData)?;
        match tag {
            0 => Ok(Self::InitializeExtraAccountMetaList),
            1 => {
                // 8 + 2 + 8 + 2 + 1 = 21. The offsets are the wire contract a client codes
                // against, so they are written out rather than inferred from the fields.
                let face = u64::from_le_bytes(
                    rest.get(..8)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let cap_bps = u16::from_le_bytes(
                    rest.get(8..10)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let band_low = u64::from_le_bytes(
                    rest.get(10..18)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let jurisdiction: [u8; 2] = rest
                    .get(18..20)
                    .ok_or(ProgramError::InvalidInstructionData)?
                    .try_into()
                    .unwrap();
                let policy = *rest.get(20).ok_or(ProgramError::InvalidInstructionData)?;
                Ok(Self::InitializeRecord {
                    face,
                    cap_bps,
                    band_low,
                    jurisdiction,
                    policy,
                })
            }
            2 => {
                let price = u64::from_le_bytes(
                    rest.get(..8)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                Ok(Self::SetPendingPrice { price })
            }
            3 => {
                let status = *rest.first().ok_or(ProgramError::InvalidInstructionData)?;
                Ok(Self::SetStatus { status })
            }
            4 => {
                // The offsets are the wire contract a client codes against, written out
                // rather than inferred, for the same reason tag 1's are.
                let low = u64::from_le_bytes(
                    rest.get(..8)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let high = u64::from_le_bytes(
                    rest.get(8..16)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let as_of_slot = u64::from_le_bytes(
                    rest.get(16..24)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let sample_n = u32::from_le_bytes(
                    rest.get(24..28)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let refused = *rest.get(28).ok_or(ProgramError::InvalidInstructionData)?;
                let model_hash: [u8; 32] = rest
                    .get(29..61)
                    .ok_or(ProgramError::InvalidInstructionData)?
                    .try_into()
                    .unwrap();
                Ok(Self::PublishBand {
                    low,
                    high,
                    as_of_slot,
                    sample_n,
                    refused,
                    model_hash,
                })
            }
            5 => {
                let low = u64::from_le_bytes(
                    rest.get(..8)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let high = u64::from_le_bytes(
                    rest.get(8..16)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let as_of_unix = i64::from_le_bytes(
                    rest.get(16..24)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let sample_n = u32::from_le_bytes(
                    rest.get(24..28)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let model_hash: [u8; 32] = rest
                    .get(28..60)
                    .ok_or(ProgramError::InvalidInstructionData)?
                    .try_into()
                    .unwrap();
                let scoring_rule_hash: [u8; 32] = rest
                    .get(60..92)
                    .ok_or(ProgramError::InvalidInstructionData)?
                    .try_into()
                    .unwrap();
                Ok(Self::LogForecast {
                    low,
                    high,
                    as_of_unix,
                    sample_n,
                    model_hash,
                    scoring_rule_hash,
                })
            }
            6 => {
                let realised_lamports = u64::from_le_bytes(
                    rest.get(..8)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                let interval_score_micro = u64::from_le_bytes(
                    rest.get(8..16)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                Ok(Self::ScoreForecast {
                    realised_lamports,
                    interval_score_micro,
                })
            }
            _ => Err(ProgramError::InvalidInstructionData),
        }
    }
}

/// True when the record account is named writable in the mint's extra-account-metas list.
///
/// It is `true` because v2's hook writes `held_since_unix` into the record on every admitted
/// transfer, and Token-2022 builds its CPI from this list: a record marked read-only here
/// arrives read-only at `execute` and could not be written there.
///
/// A metas account created by v1 (record read-only) is not rewritten by this program, and
/// `execute` checks `is_writable` before writing, so a v1 list still resolves and still
/// refuses on price. The only difference is that its record keeps `held_since_unix == 0`,
/// which is the documented "unknown hold", and `ClaimRebate` refuses an unknown hold rather
/// than paying it on a guess.
pub const RECORD_META_WRITABLE: bool = true;

/// The one extra account the hook needs, flagged as `execute` needs it.
fn record_extra_meta(record: &Pubkey) -> Result<ExtraAccountMeta, ProgramError> {
    ExtraAccountMeta::new_with_pubkey(record, false, RECORD_META_WRITABLE)
}

/// The jurisdiction as two characters for a log line.
///
/// The program stores the pair as written and does not validate it (see `state.rs`), so a
/// pair that is not valid UTF-8 is logged as `??` rather than breaking the log. `ZZ` means
/// the issuer named no jurisdiction.
fn jurisdiction_text(jurisdiction: &[u8; 2]) -> &str {
    core::str::from_utf8(jurisdiction).unwrap_or("??")
}

/// What the two price predicates decided, and which rule decided it. See [`admit`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Admission {
    /// Policy 0: the cap and the floor were enforced, and the price passed both.
    Capped,
    /// Policy 1: neither price predicate refused, and the log line says so.
    Monitored,
}

/// The whole price decision for one staged transfer, and the only place the policy branch
/// lives. Pure: no accounts, no clock, so a unit test can flip a predicate and watch it fail.
pub fn admit(record: &TicketRecord) -> Result<Admission, TicketpathError> {
    if !record.enforces() {
        // Monitored: the prices are recorded, not enforced. Not a skip of the hook, which
        // has already refused amount != 1 and an unstaged transfer before reaching here.
        return Ok(Admission::Monitored);
    }
    // The cap first: a price can be above the cap and above the floor, and "too high" is
    // the answer a seller needs. Inclusive at the cap, and division-free.
    if !record.cap_admits() {
        return Err(TicketpathError::CapExceeded);
    }
    if !record.floor_admits() {
        return Err(TicketpathError::BelowFloor);
    }
    Ok(Admission::Capped)
}

/// The refusals `InitializeRecord` makes about its own arguments, before any account exists.
///
/// Separated from the instruction so the two numbers can be tested without a runtime; the
/// instruction calls this and creates nothing when it refuses.
pub fn validate_initialize(
    face: u64,
    cap_bps: u16,
    band_low: u64,
    policy: u8,
) -> Result<(), TicketpathError> {
    if policy != POLICY_CAPPED && policy != POLICY_MONITORED {
        return Err(TicketpathError::PolicyInvalid);
    }
    // A floor above the ceiling is unsatisfiable: no price is both >= floor and <= ceiling,
    // so the ticket could never transfer and the record would be a brick that looks like a
    // ticket. `band_satisfiable` is the product form, so it does not round.
    if !band_satisfiable(face, cap_bps, band_low) {
        return Err(TicketpathError::BandUnsatisfiable);
    }
    Ok(())
}

solana_program::entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    data: &[u8],
) -> ProgramResult {
    // Our own opcodes are 0..=6 and the SPL execute discriminator starts with 105, so
    // the tag byte is unambiguous.
    if let Some(&tag) = data.first() {
        if tag <= 6 {
            let ix = HookInstruction::unpack(data)?;
            return match ix {
                HookInstruction::InitializeExtraAccountMetaList => {
                    initialize_extra_account_meta_list(program_id, accounts)
                }
                HookInstruction::InitializeRecord {
                    face,
                    cap_bps,
                    band_low,
                    jurisdiction,
                    policy,
                } => initialize_record(
                    program_id,
                    accounts,
                    face,
                    cap_bps,
                    band_low,
                    jurisdiction,
                    policy,
                ),
                HookInstruction::SetPendingPrice { price } => {
                    set_pending_price(program_id, accounts, price)
                }
                HookInstruction::SetStatus { status } => set_status(program_id, accounts, status),
                HookInstruction::PublishBand {
                    low,
                    high,
                    as_of_slot,
                    sample_n,
                    refused,
                    model_hash,
                } => publish_band(
                    program_id, accounts, low, high, as_of_slot, sample_n, refused, model_hash,
                ),
                HookInstruction::LogForecast {
                    low,
                    high,
                    as_of_unix,
                    sample_n,
                    model_hash,
                    scoring_rule_hash,
                } => log_forecast(
                    program_id,
                    accounts,
                    low,
                    high,
                    as_of_unix,
                    sample_n,
                    model_hash,
                    scoring_rule_hash,
                ),
                HookInstruction::ScoreForecast {
                    realised_lamports,
                    interval_score_micro,
                } => score_forecast(
                    program_id,
                    accounts,
                    realised_lamports,
                    interval_score_micro,
                ),
            };
        }
    }

    // Token-2022 calling us inside a transfer.
    match TransferHookInstruction::unpack(data)? {
        TransferHookInstruction::Execute { amount } => execute(program_id, accounts, amount),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

/// Create the extra-account-metas account Token-2022 resolves for this mint.
///
/// The layout is a TLV state owned by the SPL interface, not a flat array: it is a
/// `TlvState` discriminator plus a `PodSlice<ExtraAccountMeta>`. Hand-rolling it is how
/// this failed the first time (the transfer resolved no such account); encoding it with
/// `ExtraAccountMetaList::init` is the only spelling Token-2022 accepts.
///
/// The record named in the list is derived from the mint, not passed in. The list is
/// create-once and there is no instruction that rewrites one, so an argument that named the
/// wrong account would fix it for good: `execute` derives the record for the mint and would
/// refuse every transfer of that mint with 6020, with no way back. Deriving removes the
/// argument and the failure together.
fn initialize_extra_account_meta_list(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let it = &mut accounts.iter();
    let payer = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let extra_metas = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    let (expected, bump) = Pubkey::find_program_address(&extra_metas_seeds(mint.key), program_id);
    if expected != *extra_metas.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    if !extra_metas.data_is_empty() {
        // Idempotent: a second call is a no-op, not a failure to explain. It is also why a
        // v1 list survives: this program never rewrites one, and `execute` reads its flags.
        return Ok(());
    }

    // One extra account: the record, writable since v2 because the hook writes
    // `held_since_unix` into it. `RECORD_META_WRITABLE` carries the whole argument.
    let (record, _record_bump) = Pubkey::find_program_address(&record_seeds(mint.key), program_id);
    let metas = [record_extra_meta(&record)?];
    let len = ExtraAccountMetaList::size_of(metas.len())?;
    let mut data = vec![0u8; len];
    ExtraAccountMetaList::init::<ExecuteInstruction>(&mut data, &metas)?;

    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(len);
    // A PDA has no private key: the create must be signed by this program with the
    // seeds that derive it, or the runtime refuses with a missing-signature error.
    let bump_seed = [bump];
    let seeds: [&[u8]; 3] = [b"extra-account-metas", mint.key.as_ref(), &bump_seed];
    invoke_signed(
        &system_instruction::create_account(
            payer.key,
            extra_metas.key,
            lamports,
            len as u64,
            program_id,
        ),
        &[payer.clone(), extra_metas.clone(), system_program.clone()],
        &[&seeds],
    )?;
    extra_metas.data.borrow_mut().copy_from_slice(&data);
    Ok(())
}

/// Create the record for `mint`, owned by this program and derived from the mint.
///
/// The record's `authority` is the mint's own authority, and that key has to sign. Without it
/// the first caller of this instruction became the record's authority and fixed `cap_bps`,
/// `band_low` and `policy` for good, because nothing rewrites them afterward: any keypair could
/// have taken a mint's resale policy for itself. Reading the mint account costs 82 bytes and one
/// comparison, and the base `Mint` layout is unchanged by Token-2022's extensions, so the
/// authority sits at the same offset it always has.
///
/// What it does not buy: the mint authority is the issuer, so it can still create a record with
/// any cap it likes, and this does not prove the mint is a ticket or that the record belongs to
/// a real event. What it does buy is that the party who sets the policy is the party who issued
/// the token, and nobody else. A mint with no mint authority (`COption` = 0, a fixed-supply
/// mint) can never have a record created: fail-closed, and stated in the README.
fn initialize_record(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    face: u64,
    cap_bps: u16,
    band_low: u64,
    jurisdiction: [u8; 2],
    policy: u8,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let payer = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    let mint_authority = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    let (expected, bump) = Pubkey::find_program_address(&record_seeds(mint.key), program_id);
    if expected != *record_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    if !record_ai.data_is_empty() {
        // Idempotent, as before: an existing record is not re-initialised and its arguments
        // are not re-validated, so a retry of a landed instruction is not a failure.
        return Ok(());
    }
    if !mint_authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    let issuer = mint_authority_of(mint)?;
    if issuer != Some(*mint_authority.key) {
        return Err(TicketpathError::NotAuthority.into());
    }
    validate_initialize(face, cap_bps, band_low, policy)?;

    let record = TicketRecord {
        face_value_lamports: face,
        cap_bps,
        pending_price_lamports: 0,
        status: 1,
        band_low_lamports: band_low,
        jurisdiction,
        policy,
        // 0 = unknown: this record has never moved, so the hook has never run on it.
        held_since_unix: 0,
        // The mint's authority: the only signer this instruction accepted, so the key that
        // fixes the cap is the key that issued the ticket. Not the holder, not the rent payer.
        authority: *mint_authority.key,
    };
    let mut bytes = Vec::new();
    record.serialize(&mut bytes)?;

    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(bytes.len());
    let bump_seed = [bump];
    let seeds: [&[u8]; 3] = [b"record", mint.key.as_ref(), &bump_seed];
    invoke_signed(
        &system_instruction::create_account(
            payer.key,
            record_ai.key,
            lamports,
            bytes.len() as u64,
            program_id,
        ),
        &[payer.clone(), record_ai.clone(), system_program.clone()],
        &[&seeds],
    )?;
    record_ai.data.borrow_mut().copy_from_slice(&bytes);
    Ok(())
}

/// The mint's authority, out of the base `Mint` layout: `COption<Pubkey>` at offset 0, which
/// is a 4-byte tag (`0` = none, `1` = present) followed by the key. Token-2022 appends
/// extensions after the 82-byte base account and does not move it.
///
/// `None` is a mint with no authority, and `initialize_record` refuses it with 6026: a mint
/// nobody can sign for cannot authorise a policy.
fn mint_authority_of(mint_ai: &AccountInfo) -> Result<Option<Pubkey>, ProgramError> {
    let data = mint_ai.data.borrow();
    if data.len() < 82 {
        return Err(ProgramError::InvalidAccountData);
    }
    let tag = u32::from_le_bytes(
        data.get(..4)
            .ok_or(ProgramError::InvalidAccountData)?
            .try_into()
            .unwrap(),
    );
    match tag {
        0 => Ok(None),
        1 => {
            let key: [u8; 32] = data
                .get(4..36)
                .ok_or(ProgramError::InvalidAccountData)?
                .try_into()
                .unwrap();
            Ok(Some(Pubkey::new_from_array(key)))
        }
        // A COption tag that is neither 0 nor 1 is not a mint this program can read.
        _ => Err(ProgramError::InvalidAccountData),
    }
}

/// The record, for a write that has to be authorised: the owner, the address, the length and
/// the signer, in that order, before a single byte is read or written.
///
/// The length check is not decoration. `try_from_slice` only refuses a buffer of the wrong
/// size, so any program-owned account of exactly 70 bytes would deserialise as a record; today
/// the band (102), forecast (165) and score (58) are the only other ones, and their lengths are
/// what stops tags 2 and 3 writing them. Comparing the length to `TicketRecord::LEN` states
/// that fact where it is relied on, and the derivation check is what makes the account *the*
/// record for the mint rather than merely a record-shaped one.
fn checked_record_for_write(
    program_id: &Pubkey,
    authority: &AccountInfo,
    record_ai: &AccountInfo,
    mint_key: &Pubkey,
) -> Result<TicketRecord, ProgramError> {
    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    if record_ai.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    let (expected, _) = Pubkey::find_program_address(&record_seeds(mint_key), program_id);
    if expected != *record_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    if record_ai.data_len() != TicketRecord::LEN {
        return Err(ProgramError::InvalidAccountData);
    }
    let record = TicketRecord::try_from_slice(&record_ai.data.borrow())?;
    if !record.authorises(authority.key) {
        return Err(TicketpathError::NotAuthority.into());
    }
    Ok(record)
}

/// Stage a price. Accounts: `[authority (signer), record (writable), mint]`.
///
/// The signer must be the record's authority or the record's own policy can be moved by
/// anyone: a staged price is what the hook admits against, so whoever can stage can make any
/// resale admissible and can change the number the chain records as the sale price.
fn set_pending_price(program_id: &Pubkey, accounts: &[AccountInfo], price: u64) -> ProgramResult {
    let it = &mut accounts.iter();
    let authority = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    let mint = next_account_info(it)?;

    let mut record = checked_record_for_write(program_id, authority, record_ai, mint.key)?;
    record.pending_price_lamports = price;
    let mut bytes = Vec::new();
    record.serialize(&mut bytes)?;
    record_ai.data.borrow_mut().copy_from_slice(&bytes);
    Ok(())
}

/// Flip the transferable flag. Accounts: `[authority (signer), record (writable), mint]`.
///
/// Same authorisation as `set_pending_price` and for the same reason: `status = 0` refuses
/// every later transfer of the ticket with 6013, which is a permanent freeze if a stranger can
/// do it.
fn set_status(program_id: &Pubkey, accounts: &[AccountInfo], status: u8) -> ProgramResult {
    let it = &mut accounts.iter();
    let authority = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    let mint = next_account_info(it)?;

    let mut record = checked_record_for_write(program_id, authority, record_ai, mint.key)?;
    record.status = status;
    let mut bytes = Vec::new();
    record.serialize(&mut bytes)?;
    record_ai.data.borrow_mut().copy_from_slice(&bytes);
    Ok(())
}

// -- the forecast log (tags 4..6) --------------------------------------------

/// `low > high` is a band no price can be inside, so both the band and a forecast refuse it
/// with 6022. Equal ends are a point interval and are legal.
pub fn validate_band(low: u64, high: u64) -> Result<(), TicketpathError> {
    if low > high {
        return Err(TicketpathError::BandUnsatisfiable);
    }
    Ok(())
}

/// The forecast is a band as well, and the same 6022 covers the same mistake. It is a
/// separate name so a test can fail on the forecast path and not on the band path alone.
pub fn validate_forecast(low: u64, high: u64) -> Result<(), TicketpathError> {
    validate_band(low, high)
}

/// How late a forecast may be logged, in seconds, before it is a backdated claim (`6029`).
///
/// The number has to be larger than the skew between a client's clock and the validator's and
/// the time a transaction takes to land, and smaller than anything that would let an outcome be
/// seen first. Both of those are seconds; five minutes is comfortably outside the first and
/// nowhere near the second. It is a constant so the limit is a stated rule and not a judgement
/// made at each call site.
pub const FORECAST_BACKDATE_TOLERANCE_SECONDS: i64 = 300;

/// `as_of_unix` must not be older than the clock minus [`FORECAST_BACKDATE_TOLERANCE_SECONDS`].
///
/// This is the only check on the clock that a create-once log can make, and it is one-sided on
/// purpose. A forecast dated in the *future* is a pre-registration: its bytes are fixed now and
/// they are about an instant that has not happened, so it cannot encode an outcome. A forecast
/// dated in the past beyond the tolerance is the opposite: it can be written after the result is
/// known and still read as though it came first. What remains after this check is the residual
/// `state.rs::Forecast` states: publishing at the as-of rather than before it cannot be detected.
pub fn validate_forecast_time(as_of_unix: i64, now_unix: i64) -> Result<(), TicketpathError> {
    let earliest = now_unix.saturating_sub(FORECAST_BACKDATE_TOLERANCE_SECONDS);
    if as_of_unix < earliest {
        return Err(TicketpathError::ForecastBackdated);
    }
    Ok(())
}

/// A band's width must fit the score field's micro-lamport scale (`6031`).
///
/// `interval_score_micro` is a `u64` and the rule multiplies lamports by
/// [`SCORE_MICRO_SCALE`], so a band wider than [`MAX_BAND_WIDTH_LAMPORTS`] has a width term that
/// cannot be stored: no score for that forecast could exist. A forecast that can never be scored
/// is not a forecast, so it is refused where it is committed, not at scoring time.
pub fn validate_band_width(low: u64, high: u64) -> Result<(), TicketpathError> {
    if high.saturating_sub(low) > MAX_BAND_WIDTH_LAMPORTS {
        return Err(TicketpathError::BandTooWide);
    }
    Ok(())
}

/// A score can never be below the width of the band it scores (`6030`).
///
/// The width term is the floor of the interval score: `S = (u - l) + penalty`, and the penalty
/// is zero at either bound and positive outside. So `(high - low) * SCORE_MICRO_SCALE` is a
/// lower bound any honest score satisfies, and the check costs one multiplication.
///
/// It is the only direction the chain can check. Nothing here recomputes the penalty term, so an
/// overstated error, a number larger than the rule gives, is stored without complaint. The score
/// is the authority's assertion above that floor; see `state.rs::Score`.
pub fn validate_interval_score(
    low: u64,
    high: u64,
    interval_score_micro: u64,
) -> Result<(), TicketpathError> {
    let width_micro = (high.saturating_sub(low) as u128) * (SCORE_MICRO_SCALE as u128);
    if (interval_score_micro as u128) < width_micro {
        return Err(TicketpathError::ScoreBelowWidth);
    }
    Ok(())
}

/// `refused` is a flag, not a count: stored and logged as 0 or 1.
pub fn normalised_refused(refused: u8) -> u8 {
    if refused == 0 {
        0
    } else {
        1
    }
}

/// The refusals `PublishBand` makes about its own arguments, before any account is read.
///
/// Order: an inverted band is `6022` (it is not a band at all), an `as_of_slot` above the slot
/// the write lands in is `6033` (an estimate from the future), and a band with no observations
/// that is not a refusal is `6032` (a number with nothing behind it).
pub fn validate_publish(
    low: u64,
    high: u64,
    as_of_slot: u64,
    published_slot: u64,
    sample_n: u32,
    refused: u8,
) -> Result<(), TicketpathError> {
    validate_band(low, high)?;
    if as_of_slot > published_slot {
        return Err(TicketpathError::AsOfAhead);
    }
    if sample_n == 0 && refused == 0 {
        return Err(TicketpathError::BandEmpty);
    }
    Ok(())
}

/// Decode the record named by `mint`, and refuse a record at any other address or owner.
///
/// The record is the authority register for every satellite write, and deriving it from the
/// mint is what stops a caller pointing a band at a record for a different ticket.
fn checked_record(
    program_id: &Pubkey,
    record_ai: &AccountInfo,
    mint_key: &Pubkey,
) -> Result<TicketRecord, ProgramError> {
    if record_ai.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    let (expected, _) = Pubkey::find_program_address(&record_seeds(mint_key), program_id);
    if expected != *record_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    if record_ai.data_len() != TicketRecord::LEN {
        // A 70-byte account that is not a record is not decodable as one by shape alone; the
        // length is the first thing that says so, before `try_from_slice` reads a field.
        return Err(ProgramError::InvalidAccountData);
    }
    Ok(TicketRecord::try_from_slice(&record_ai.data.borrow())?)
}

/// Create a program-owned PDA with `space` bytes, signed by the seeds that derive it.
fn create_pda_account<'a>(
    payer: &AccountInfo<'a>,
    account: &AccountInfo<'a>,
    system_program: &AccountInfo<'a>,
    program_id: &Pubkey,
    space: usize,
    seeds: &[&[u8]],
) -> ProgramResult {
    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(space);
    invoke_signed(
        &system_instruction::create_account(
            payer.key,
            account.key,
            lamports,
            space as u64,
            program_id,
        ),
        &[payer.clone(), account.clone(), system_program.clone()],
        &[seeds],
    )
}

/// The band a `PublishBand` with these arguments writes. Pure, so a unit test can inspect
/// the value without a runtime or a clock. `refused` is normalised to 0 or 1 here, in the one
/// place the account is built, so every caller and every log line agrees with the stored byte.
pub fn band_for_write(
    low: u64,
    high: u64,
    as_of_slot: u64,
    published_slot: u64,
    sample_n: u32,
    refused: u8,
    model_hash: [u8; 32],
    authority: [u8; 32],
) -> Band {
    Band {
        version: SATELLITE_VERSION,
        low,
        high,
        as_of_slot,
        published_slot,
        sample_n,
        refused: normalised_refused(refused),
        model_hash,
        authority,
    }
}

/// The account a forecast writes. Pure, for the same reason.
pub fn forecast_for_write(
    mint: [u8; 32],
    low: u64,
    high: u64,
    as_of_unix: i64,
    sample_n: u32,
    model_hash: [u8; 32],
    scoring_rule_hash: [u8; 32],
    created_slot: u64,
    authority: [u8; 32],
) -> Forecast {
    Forecast {
        version: SATELLITE_VERSION,
        mint,
        low,
        high,
        as_of_unix,
        sample_n,
        model_hash,
        scoring_rule_hash,
        created_slot,
        authority,
    }
}

/// Write the rewritable head of the public feed. `published_slot` is `Clock::slot`, not
/// `Clock::unix_timestamp`: the account stores two slot fields (`as_of_slot` from the model,
/// `published_slot` from this write) and neither is a unix time. The unix instant lives in
/// the forecast, which is the account a consumer reads for a decision as of a time.
fn publish_band(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    low: u64,
    high: u64,
    as_of_slot: u64,
    sample_n: u32,
    refused: u8,
    model_hash: [u8; 32],
) -> ProgramResult {
    let published_slot = Clock::get()?.slot;
    publish_band_at(
        program_id,
        accounts,
        low,
        high,
        as_of_slot,
        sample_n,
        refused,
        model_hash,
        published_slot,
    )
}

/// `PublishBand` with the clock supplied, so the branch can be unit-tested on the host.
fn publish_band_at(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    low: u64,
    high: u64,
    as_of_slot: u64,
    sample_n: u32,
    refused: u8,
    model_hash: [u8; 32],
    published_slot: u64,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let authority = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    let band_ai = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    validate_publish(low, high, as_of_slot, published_slot, sample_n, refused)?;
    let record = checked_record(program_id, record_ai, mint.key)?;
    if !record.authorises(authority.key) {
        return Err(TicketpathError::NotAuthority.into());
    }

    let (expected, bump) = Pubkey::find_program_address(&band_seeds(mint.key), program_id);
    if expected != *band_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }

    let band = band_for_write(
        low,
        high,
        as_of_slot,
        published_slot,
        sample_n,
        refused,
        model_hash,
        record.authority.to_bytes(),
    );
    let mut bytes = Vec::new();
    band.serialize(&mut bytes)?;

    if band_ai.data_is_empty() {
        let bump_seed = [bump];
        let seeds: [&[u8]; 3] = [b"band", mint.key.as_ref(), &bump_seed];
        create_pda_account(
            authority,
            band_ai,
            system_program,
            program_id,
            Band::LEN,
            &seeds,
        )?;
        band_ai.data.borrow_mut().copy_from_slice(&bytes);
        solana_program::msg!(
            "ticketpath: band created low={} high={} as_of_slot={} published_slot={} sample_n={} refused={}",
            band.low,
            band.high,
            band.as_of_slot,
            band.published_slot,
            band.sample_n,
            band.refused,
        );
    } else {
        // The head is rewritable on purpose; the forecast log is the history.
        if band_ai.owner != program_id {
            return Err(ProgramError::IncorrectProgramId);
        }
        if band_ai.data_len() != Band::LEN {
            return Err(ProgramError::InvalidAccountData);
        }
        band_ai.data.borrow_mut().copy_from_slice(&bytes);
        solana_program::msg!(
            "ticketpath: band rewritten low={} high={} as_of_slot={} published_slot={} sample_n={} refused={}",
            band.low,
            band.high,
            band.as_of_slot,
            band.published_slot,
            band.sample_n,
            band.refused,
        );
    }
    Ok(())
}

/// Create the one forecast for `(mint, as_of_unix)`. `created_slot` is `Clock::slot` and
/// `now_unix` is `Clock::unix_timestamp`, both read in the same call so the two cannot disagree.
fn log_forecast(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    low: u64,
    high: u64,
    as_of_unix: i64,
    sample_n: u32,
    model_hash: [u8; 32],
    scoring_rule_hash: [u8; 32],
) -> ProgramResult {
    let clock = Clock::get()?;
    log_forecast_at(
        program_id,
        accounts,
        low,
        high,
        as_of_unix,
        sample_n,
        model_hash,
        scoring_rule_hash,
        clock.slot,
        clock.unix_timestamp,
    )
}

/// `LogForecast` with the clock supplied. Every refusal returns before `create_account`, so a
/// refused call cannot consume the PDA (and the runtime's transaction rollback would undo the
/// create even if it did).
fn log_forecast_at(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    low: u64,
    high: u64,
    as_of_unix: i64,
    sample_n: u32,
    model_hash: [u8; 32],
    scoring_rule_hash: [u8; 32],
    created_slot: u64,
    now_unix: i64,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let authority = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    let forecast_ai = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    validate_forecast(low, high)?;
    // The band must be one a score could represent, and the as-of must not be a date in the
    // past dressed up as a prediction. Both are refusals about the arguments, before an account
    // is read, so a refused call leaves the PDA empty.
    validate_band_width(low, high)?;
    validate_forecast_time(as_of_unix, now_unix)?;
    let record = checked_record(program_id, record_ai, mint.key)?;
    if !record.authorises(authority.key) {
        return Err(TicketpathError::NotAuthority.into());
    }

    // The seed is the signed little-endian i64, exactly as `state.rs::forecast_seeds`
    // documents; the temporary lives until the create below.
    let as_of_bytes = as_of_unix.to_le_bytes();
    let (expected, bump) =
        Pubkey::find_program_address(&[b"forecast", mint.key.as_ref(), &as_of_bytes], program_id);
    if expected != *forecast_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    // Create-once: existence is the refusal. The bytes are not compared or rewritten.
    if !forecast_ai.data_is_empty() {
        return Err(TicketpathError::ForecastExists.into());
    }

    let forecast = forecast_for_write(
        mint.key.to_bytes(),
        low,
        high,
        as_of_unix,
        sample_n,
        model_hash,
        scoring_rule_hash,
        created_slot,
        record.authority.to_bytes(),
    );
    let mut bytes = Vec::new();
    forecast.serialize(&mut bytes)?;

    let bump_seed = [bump];
    let seeds: [&[u8]; 4] = [b"forecast", mint.key.as_ref(), &as_of_bytes, &bump_seed];
    create_pda_account(
        authority,
        forecast_ai,
        system_program,
        program_id,
        Forecast::LEN,
        &seeds,
    )?;
    forecast_ai.data.borrow_mut().copy_from_slice(&bytes);
    solana_program::msg!(
        "ticketpath: forecast logged low={} high={} as_of_unix={} sample_n={} created_slot={} created_unix={}",
        low,
        high,
        as_of_unix,
        sample_n,
        created_slot,
        now_unix,
    );
    Ok(())
}

/// Create the one score for a forecast. The forecast account is read and never written:
/// it is not in this function's mutable set, and the write below targets the score PDA.
fn score_forecast(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    realised_lamports: u64,
    interval_score_micro: u64,
) -> ProgramResult {
    let scored_slot = Clock::get()?.slot;
    score_forecast_at(
        program_id,
        accounts,
        realised_lamports,
        interval_score_micro,
        scored_slot,
    )
}

/// `ScoreForecast` with the clock supplied.
fn score_forecast_at(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    realised_lamports: u64,
    interval_score_micro: u64,
    scored_slot: u64,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let scorer = next_account_info(it)?;
    let forecast_ai = next_account_info(it)?;
    let score_ai = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    if !scorer.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    if forecast_ai.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    if forecast_ai.data_len() != Forecast::LEN {
        return Err(ProgramError::InvalidAccountData);
    }
    let forecast = Forecast::try_from_slice(&forecast_ai.data.borrow())?;
    if forecast.authority != scorer.key.to_bytes() {
        return Err(TicketpathError::NotAuthority.into());
    }

    let (expected, bump) = Pubkey::find_program_address(&score_seeds(forecast_ai.key), program_id);
    if expected != *score_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    if !score_ai.data_is_empty() {
        return Err(TicketpathError::AlreadyScored.into());
    }

    // Existence first, then the rule: a second score is a duplicate whatever number it carries,
    // and the duplicate refusal is the more useful answer. Past that, the one bound the chain can
    // check: the width term is the floor of the interval score, so a smaller number is not a
    // score under any reading of the rule. There is no upper check and there cannot be one
    // without the rule text on chain; see `state.rs::Score`.
    validate_interval_score(forecast.low, forecast.high, interval_score_micro)?;

    let score = Score {
        version: SATELLITE_VERSION,
        realised_lamports,
        interval_score_micro,
        // The chain recalculates coverage from the forecast's own ends, so the flag cannot
        // disagree with the interval that was committed before the outcome.
        covered: if forecast.covers(realised_lamports) {
            1
        } else {
            0
        },
        scored_slot,
        scorer: scorer.key.to_bytes(),
    };
    let mut bytes = Vec::new();
    score.serialize(&mut bytes)?;

    let bump_seed = [bump];
    let seeds: [&[u8]; 3] = [b"score", forecast_ai.key.as_ref(), &bump_seed];
    create_pda_account(
        scorer,
        score_ai,
        system_program,
        program_id,
        Score::LEN,
        &seeds,
    )?;
    score_ai.data.borrow_mut().copy_from_slice(&bytes);
    solana_program::msg!(
        "ticketpath: forecast scored realised={} interval_score_micro={} covered={} scored_slot={}",
        realised_lamports,
        interval_score_micro,
        score.covered,
        scored_slot,
    );
    Ok(())
}

/// The hook. Token-2022 calls this inside every transfer of a hooked mint.
///
/// Accounts, in the order the extra-account-metas list produces (§3.9):
/// `[0] source`, `[1] mint`, `[2] destination`, `[3] authority`, `[4] extra_metas`, `[5] record`.
/// The record is read and, on an admitted transfer, written.
fn execute(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let it = &mut accounts.iter();
    let _source = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let _destination = next_account_info(it)?;
    let _authority = next_account_info(it)?;
    let extra_metas = next_account_info(it)?;
    let record_ai = next_account_info(it)?;

    // 1. One ticket at a time. A hook that admits `amount > 1` admits a bulk dump.
    if amount != 1 {
        return Err(TicketpathError::AmountNotOne.into());
    }

    // 2. The extra-account-metas account is the one Token-2022 should have resolved for
    //    this mint. Without this check a caller could pass any account positionally.
    let (expected_metas, _) =
        Pubkey::find_program_address(&extra_metas_seeds(mint.key), program_id);
    if expected_metas != *extra_metas.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }

    // 3. The record must be ours and must be the record for this mint.
    if record_ai.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    let (expected_record, _) = Pubkey::find_program_address(&record_seeds(mint.key), program_id);
    if expected_record != *record_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }

    let mut record = TicketRecord::try_from_slice(&record_ai.data.borrow())?;

    // 4. The ticket must be in a transferable state.
    if record.status != 1 {
        return Err(TicketpathError::TicketNotValid.into());
    }

    // 5. Nothing staged, nothing to check: the transfer is not a sale.
    if record.pending_price_lamports == 0 {
        return Err(TicketpathError::TransferNotStaged.into());
    }

    // 6. The price. The cap and the floor when the record enforces them, nothing when it
    //    does not, and one log line per outcome so the chain records which rule ran.
    match admit(&record) {
        Ok(Admission::Capped) => solana_program::msg!(
            "ticketpath: cap admitted price={} face={} cap_bps={} band_low={} jurisdiction={}",
            record.pending_price_lamports,
            record.face_value_lamports,
            record.cap_bps,
            record.band_low_lamports,
            jurisdiction_text(&record.jurisdiction),
        ),
        Ok(Admission::Monitored) => solana_program::msg!(
            "ticketpath: policy=monitored price={} face={} cap_bps={} band_low={} jurisdiction={}",
            record.pending_price_lamports,
            record.face_value_lamports,
            record.cap_bps,
            record.band_low_lamports,
            jurisdiction_text(&record.jurisdiction),
        ),
        Err(TicketpathError::CapExceeded) => {
            solana_program::msg!(
                "ticketpath: cap exceeded price={} face={} cap_bps={} jurisdiction={}",
                record.pending_price_lamports,
                record.face_value_lamports,
                record.cap_bps,
                jurisdiction_text(&record.jurisdiction),
            );
            return Err(TicketpathError::CapExceeded.into());
        }
        Err(TicketpathError::BelowFloor) => {
            solana_program::msg!(
                "ticketpath: below floor price={} band_low={} face={} jurisdiction={}",
                record.pending_price_lamports,
                record.band_low_lamports,
                record.face_value_lamports,
                jurisdiction_text(&record.jurisdiction),
            );
            return Err(TicketpathError::BelowFloor.into());
        }
        Err(e) => return Err(e.into()),
    }

    // 7. An admitted transfer consumes the staging, and is when the clock starts for the rebate.
    //
    //    `pending_price_lamports = 0` is the one-stage-one-sale rule: with nothing staged, the
    //    next transfer of this ticket is refused `6009` at step 5, so an authority has to stage
    //    the price of each sale it admits. Without this clear, one staging admitted every later
    //    transfer at that price for the life of the record, which read as a cap over a price the
    //    seller paid once.
    //
    //    0 stays 0 for `held_since_unix` when the record arrived read-only (a v1 metas account),
    //    which is "unknown" rather than a fabricated hold: the holder's share is then refused,
    //    not guessed. A read-only record cannot have the staging cleared either, so on that path
    //    one staging does admit more than one transfer. That path is the v1 metas shape, which
    //    this program never creates under its own id (the list is seeded by the program id), and
    //    the log line below says so rather than leaving it to be inferred.
    if record_ai.is_writable {
        record.pending_price_lamports = 0;
        record.held_since_unix = Clock::get()?.unix_timestamp;
        let mut bytes = Vec::new();
        record.serialize(&mut bytes)?;
        record_ai.data.borrow_mut().copy_from_slice(&bytes);
    } else {
        solana_program::msg!(
            "ticketpath: held_since_unix not written and the staged price not consumed, record is read-only jurisdiction={}",
            jurisdiction_text(&record.jurisdiction),
        );
    }
    Ok(())
}
