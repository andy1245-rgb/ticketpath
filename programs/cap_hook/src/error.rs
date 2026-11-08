//! Error codes. A number a client can name, so the console can print a sentence instead of
//! `custom program error: 0x1785`.
//!
//! # The numbering is an interface
//!
//! `docs/ON-CHAIN-DESIGN.md` §3.12 owns 6000..6020 and this program must not renumber them,
//! because a code that means one thing in one release and another thing in the next is worse
//! than no code: a client cannot branch on it, and a log is not evidence if its number is
//! ambiguous. So the reserved gaps stay gaps.
//!
//! | code | name | who raises it |
//! |---|---|---|
//! | 6008 | `E_AMOUNT_NOT_ONE` | hook |
//! | 6009 | `E_TRANSFER_NOT_STAGED` | hook |
//! | 6010 | `E_CAP_EXCEEDED` | hook |
//! | 6011 | `E_RESALE_DISABLED` | **not used here.** Reserved by §3.12 for the transfer gate. |
//! | 6012 | `E_DEST_UNVERIFIED` | **not used here.** Reserved by §3.12 for the destination gate. |
//! | 6013 | `E_TICKET_NOT_VALID` | hook |
//! | 6014..6019 | §3.12's `E_PRICE_ZERO`, `E_SELF_TRANSFER`, `E_NOT_OWNER`, `E_DEST_MISMATCH`, `E_VERIFICATION_EXPIRED`, `E_WRONG_TOKEN_PROGRAM` | **not used here.** The bigger design's instructions; this program does not implement them. |
//! | 6020 | `E_NOT_A_TICKET` (this program: `E_WRONG_EXTRA_ACCOUNT`) | any instruction handed a PDA that is not the one it derives |
//!
//! New in v2, and each one is a predicate that did not exist before v2:
//!
//! | code | name | raised when |
//! |---|---|---|
//! | 6021 | `E_BELOW_FLOOR` | a staged price is below the record's floor, floor > 0 |
//! | 6022 | `E_BAND_UNSATISFIABLE` | a band no record could satisfy: a floor above the cap ceiling at `InitializeRecord`, or `low > high` at `PublishBand`/`LogForecast` |
//! | 6023 | `E_POLICY_INVALID` | `policy` is neither 0 (capped) nor 1 (monitored) |
//! | 6024 | `E_FORECAST_EXISTS` | `LogForecast` for an `as_of_unix` whose forecast account already exists |
//! | 6025 | `E_ALREADY_SCORED` | `ScoreForecast` for a forecast whose score account already exists |
//! | 6026 | `E_NOT_AUTHORITY` | a signer that is not the key the write requires: the record's `authority` on tags 2, 3, 4 and 5, or the mint's authority on tag 1 |
//! | 6027 | `E_REBATE_NOT_DUE` | `ClaimRebate` when the hold is unknown or zero, or the holder's share of the pool floors to 0 |
//! | 6028 | `E_REBATE_UNAVAILABLE` | `ClaimRebate` when the Token-2022 CPI leg is refused, or a clause it needs is absent |
//!
//! Added after the v2 review (`records/findings/37-program-v2-review-fixes.md`), each one a
//! refusal that had no code because the program did not make the check:
//!
//! | code | name | raised when |
//! |---|---|---|
//! | 6029 | `E_FORECAST_BACKDATED` | `LogForecast` with an `as_of_unix` earlier than the clock minus `FORECAST_BACKDATE_TOLERANCE_SECONDS` |
//! | 6030 | `E_SCORE_BELOW_WIDTH` | `ScoreForecast` with an `interval_score_micro` below `(high - low) * 1_000_000`, which no honest score can be |
//! | 6031 | `E_BAND_TOO_WIDE` | a forecast wider than `MAX_BAND_WIDTH_LAMPORTS`, whose width alone does not fit the `u64` the score field is |
//! | 6032 | `E_BAND_EMPTY` | `PublishBand` with `sample_n == 0` and `refused == 0`: a band resting on no observations that is not a refusal |
//! | 6033 | `E_AS_OF_AHEAD` | `PublishBand` with `as_of_slot` above the slot the write lands in |
//!
//! 6020 has two names on purpose and the documentation says so rather than pretending
//! otherwise: §3.12 spells it `E_NOT_A_TICKET` for a record account handed to the wrong
//! instruction, and v1 spelled the same condition `E_WRONG_EXTRA_ACCOUNT` because that is
//! what it checks. Both are "the account you passed is not the account I derive", which is
//! one predicate with one number.

/// The program's refusals. `From` turns each into `ProgramError::Custom(n)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TicketpathError {
    /// The transfer was for more than one ticket.
    AmountNotOne = 6008,
    /// The record has not been staged for a transfer.
    TransferNotStaged = 6009,
    /// The price staged on the record is above the cap.
    CapExceeded = 6010,
    /// The record is not in a transferable state.
    TicketNotValid = 6013,
    /// The wrong account was passed in the extra-account-metas list, or at a PDA position.
    WrongExtraAccount = 6020,
    /// The staged price is below the record's floor, and the record has a floor.
    BelowFloor = 6021,
    /// A band that no price could satisfy: a floor above the ceiling, or low above high.
    BandUnsatisfiable = 6022,
    /// `policy` was neither 0 (capped) nor 1 (monitored).
    PolicyInvalid = 6023,
    /// This `(mint, as_of_unix)` forecast already exists. Immutability, not a race.
    ForecastExists = 6024,
    /// This forecast already has a score. Immutability, not a race.
    AlreadyScored = 6025,
    /// The signer is not the key this write requires: the record's authority on tags 2, 3, 4
    /// and 5, the mint's authority on tag 1.
    NotAuthority = 6026,
    /// Nothing is due: the hold is unknown or is too short for the share to round up from 0.
    RebateNotDue = 6027,
    /// The rebate could not be paid: a Token-2022 CPI leg was refused, or a clause it needs
    /// (a transfer-fee mint, a fee authority PDA, a pool account) is missing.
    RebateUnavailable = 6028,
    /// The forecast's `as_of_unix` is older than the clock's stated tolerance allows: a
    /// forecast that can be dated in the past cannot be told from a post-hoc claim.
    ForecastBackdated = 6029,
    /// The score is below the width of the band it scores, which no interval score can be:
    /// the width term is the floor of the rule.
    ScoreBelowWidth = 6030,
    /// The band is wider than `MAX_BAND_WIDTH_LAMPORTS`, so its width in micro-lamports does
    /// not fit the `u64` the score field is and no score for it could be stored.
    BandTooWide = 6031,
    /// A band with no observations (`sample_n == 0`) that is not a refusal: a number with
    /// nothing behind it and no statement that it is a refusal either.
    BandEmpty = 6032,
    /// The band's `as_of_slot` is above the slot the write landed in: the estimate claims to
    /// be from the future.
    AsOfAhead = 6033,
}

impl From<TicketpathError> for solana_program::program_error::ProgramError {
    fn from(e: TicketpathError) -> Self {
        solana_program::program_error::ProgramError::Custom(e as u32)
    }
}
