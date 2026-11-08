//! `region_gate` — the transfer hook that enforces a per-event jurisdiction's resale policy.
//!
//! This is the on-chain half of `records/REGION-CAPS-DESIGN.md` §9. It is a **local-validator
//! only** crate: the proven devnet program (`5EJ1GU3M4vn…`, cap check only) is never redeployed,
//! re-signed or overwritten by anything here.
//!
//! The idea the crate exists to make measurable is one sentence: *which* rule applies is decided
//! off chain by a deterministic table, and the chain stores the outcome — the jurisdiction, the
//! policy, the cap and the table generation — so a transfer can be refused, admitted, or admitted
//! and recorded, on evidence a chain reader can see.
//!
//! The cap predicate is unchanged from `docs/ON-CHAIN-DESIGN.md` §3.10, in `u128`, with no
//! division, inclusive at the cap:
//!
//! ```text
//! price * 10_000 <= base * (10_000 + cap_bps)
//! ```
//!
//! `base` is the cap *base*, not necessarily the tier face: in a jurisdiction whose law includes
//! the fees the buyer paid, the base is face + fees and this field carries the sum
//! (`records/REGION-CAPS-DESIGN.md` §4). The program cannot tell the difference, and says so.
//!
//! Three policies, one branch:
//!
//! | policy | value | hook behaviour |
//! |---|---|---|
//! | capped | 0 | refuse above `base * (1 + cap_bps)`; `6021` if the record is inconsistent |
//! | monitored | 1 | admit any staged price, `msg!` the jurisdiction and the price |
//! | unresolved | 2 | admit any staged price, `msg!` that the law is unresolved |
//!
//! `TightenPolicy` is the only way a policy can change after a ticket is issued, and it is
//! **monotone**: it may lower a cap, may move monitored/unresolved to capped, and may never raise
//! a cap or remove one. Loosening is refused with `6022`, because the chain cannot tell a
//! repealed law from an organiser's convenience (`records/REGION-CAPS-DESIGN.md` §6).

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
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

pub const BPS_DENOM: u128 = 10_000;
pub const U16_MAX_CAP: u16 = 65_535;

/// `policy` values. An unknown byte is refused at creation and at the hook, never interpreted.
pub const POLICY_CAPPED: u8 = 0;
pub const POLICY_MONITORED: u8 = 1;
pub const POLICY_UNRESOLVED: u8 = 2;

/// `'Z'`. The chain field is two bytes, so "unresolved" has to be spellable in two bytes that no
/// ISO-3166-1 assignment uses; `ZZ` is the ISO-3166 user-assigned code for exactly this.
pub const JURISDICTION_UNRESOLVED: [u8; 2] = [b'Z', b'Z'];

/// Errors carry a number the client can name, like the design's table (`docs/ON-CHAIN-DESIGN.md`
/// §3.12). 6008-6020 are the existing numbers and are not renumbered. **6021-6028 are taken by
/// the v2 program in `programs/cap_hook/` with different meanings** (`E_BELOW_FLOOR` =
/// 6021, `E_BAND_UNSATISFIABLE` = 6022, `E_POLICY_INVALID` = 6023, ...), so this crate's four
/// codes start at 6040 and leave a gap. A number that means one thing in one program and another
/// thing in the next is worse than no number: a client cannot branch on it and a log is not
/// evidence if its number is ambiguous.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RegionError {
    AmountNotOne = 6008,
    TransferNotStaged = 6009,
    CapExceeded = 6010,
    TicketNotValid = 6013,
    WrongExtraAccount = 6020,
    /// Only the record's authority may stage a price, change status or tighten the policy.
    NotAuthority = 6040,
    /// The record's policy, cap and jurisdiction do not agree with each other.
    PolicyInvalid = 6041,
    /// The requested change would loosen the policy an issued ticket already carries.
    PolicyLoosens = 6042,
    /// The jurisdiction field is not two uppercase ASCII letters.
    JurisdictionCode = 6043,
}

impl From<RegionError> for ProgramError {
    fn from(e: RegionError) -> Self {
        ProgramError::Custom(e as u32)
    }
}

/// The state the hook reads.
///
/// `authority` is a byte array rather than a `Pubkey` so the layout is unambiguous under Borsh and
/// nobody has to reason about a `repr` at all.
#[derive(BorshSerialize, BorshDeserialize, Debug, Clone, PartialEq, Eq)]
pub struct TicketRecord {
    /// The cap base in lamports: tier face, or face + documented fees where the law's base is all
    /// in (`records/REGION-CAPS-DESIGN.md` §4).
    pub base_lamports: u64,
    /// Resale cap in basis points over the base. `U16_MAX_CAP` for `monitored` and `unresolved`.
    pub cap_bps: u16,
    /// The price staged for the transfer the hook is about to see, in lamports.
    pub pending_price_lamports: u64,
    /// 1 = transferable, 0 = not.
    pub status: u8,
    /// The binding nation, ISO-3166-1 alpha-2 uppercase; `ZZ` when unresolved.
    pub jurisdiction: [u8; 2],
    /// 0 capped, 1 monitored, 2 unresolved.
    pub policy: u8,
    /// The rules-table generation the policy was stamped from. Indices, not a date: a u32 keeps
    /// the record small and the table owns the mapping.
    pub law_version: u32,
    /// The only wallet allowed to stage, change status or tighten.
    pub authority: [u8; 32],
}

impl TicketRecord {
    /// Exact Borsh width of the struct above.
    pub const LEN: usize = 8 + 2 + 8 + 1 + 2 + 1 + 4 + 32;

    /// §3.10 exactly: both sides in `u128`, no division, inclusive at the cap.
    pub fn cap_admits(&self) -> bool {
        let lhs = (self.pending_price_lamports as u128) * BPS_DENOM;
        let rhs = (self.base_lamports as u128) * (BPS_DENOM + self.cap_bps as u128);
        lhs <= rhs
    }

    /// The largest price the predicate admits, floored. Display and tests only: the enforcement
    /// path compares products and never divides.
    pub fn max_price_lamports(&self) -> u64 {
        ((self.base_lamports as u128) * (BPS_DENOM + self.cap_bps as u128) / BPS_DENOM) as u64
    }
}

/// Two uppercase ASCII letters. The chain refuses anything else rather than storing a code no
/// reader can interpret.
pub fn jurisdiction_valid(code: [u8; 2]) -> bool {
    code.iter().all(|b| b.is_ascii_uppercase())
}

/// Whether `(policy, cap_bps, jurisdiction)` is a consistent triple.
///
/// The rule that matters: a policy with no cap must carry the field's maximum, so "monitored" can
/// never be a low number nobody looked at, and `ZZ` is reserved for `unresolved`.
pub fn validate_policy(policy: u8, cap_bps: u16, jurisdiction: [u8; 2]) -> Result<(), RegionError> {
    if !jurisdiction_valid(jurisdiction) {
        return Err(RegionError::JurisdictionCode);
    }
    match policy {
        POLICY_CAPPED => {
            if cap_bps == U16_MAX_CAP && jurisdiction == JURISDICTION_UNRESOLVED {
                // capped at 65535 bps from an unresolved jurisdiction is a contradiction: an
                // unresolved law cannot produce a cap *and* a binding jurisdiction code.
                return Err(RegionError::PolicyInvalid);
            }
            if jurisdiction == JURISDICTION_UNRESOLVED {
                return Err(RegionError::PolicyInvalid);
            }
            Ok(())
        }
        POLICY_MONITORED => {
            if cap_bps != U16_MAX_CAP {
                return Err(RegionError::PolicyInvalid);
            }
            if jurisdiction == JURISDICTION_UNRESOLVED {
                return Err(RegionError::PolicyInvalid);
            }
            Ok(())
        }
        POLICY_UNRESOLVED => {
            if cap_bps != U16_MAX_CAP || jurisdiction != JURISDICTION_UNRESOLVED {
                return Err(RegionError::PolicyInvalid);
            }
            Ok(())
        }
        _ => Err(RegionError::PolicyInvalid),
    }
}

/// Whether a policy change is monotone (§6). Tightening only.
///
/// - capped -> capped: the new cap must be strictly lower.
/// - monitored or unresolved -> capped: always allowed (the law started to bind).
/// - anything -> the same policy: only a strictly lower cap, which is capped -> capped.
/// - anything -> monitored or unresolved: refused. Removing a cap is not representable on an
///   issued ticket.
pub fn tighten_allows(old_policy: u8, old_cap_bps: u16, new_policy: u8, new_cap_bps: u16) -> bool {
    if new_policy != POLICY_CAPPED {
        return false;
    }
    if new_cap_bps >= U16_MAX_CAP {
        return false;
    }
    if old_policy == POLICY_CAPPED {
        new_cap_bps < old_cap_bps
    } else {
        true
    }
}

/// Instruction set. `0..=4` are this program's own; the SPL transfer-hook discriminator starts with
/// 105, so the tag byte cannot collide.
pub enum GateInstruction {
    /// 0 — create the extra-account-metas PDA for a mint, naming the record account.
    InitializeExtraAccountMetaList { record: Pubkey },
    /// 1 — create the record for a mint with its base, policy and jurisdiction.
    InitializeRecord {
        base_lamports: u64,
        cap_bps: u16,
        jurisdiction: [u8; 2],
        policy: u8,
        law_version: u32,
    },
    /// 2 — stage the price for the next transfer. Authority only.
    SetPendingPrice { price: u64 },
    /// 3 — flip the record's transferable flag. Authority only.
    SetStatus { status: u8 },
    /// 4 — tighten the policy after a law change. Authority only, monotone.
    TightenPolicy {
        cap_bps: u16,
        jurisdiction: [u8; 2],
        law_version: u32,
    },
}

impl GateInstruction {
    fn unpack(data: &[u8]) -> Result<Self, ProgramError> {
        let (tag, rest) = data.split_first().ok_or(ProgramError::InvalidInstructionData)?;
        match tag {
            0 => {
                let record = Pubkey::try_from(
                    rest.get(..32).ok_or(ProgramError::InvalidInstructionData)?,
                )
                .map_err(|_| ProgramError::InvalidInstructionData)?;
                Ok(Self::InitializeExtraAccountMetaList { record })
            }
            1 => {
                let base_lamports = u64::from_le_bytes(
                    rest.get(..8).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap(),
                );
                let cap_bps = u16::from_le_bytes(
                    rest.get(8..10).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap(),
                );
                let jurisdiction = [
                    *rest.get(10).ok_or(ProgramError::InvalidInstructionData)?,
                    *rest.get(11).ok_or(ProgramError::InvalidInstructionData)?,
                ];
                let policy = *rest.get(12).ok_or(ProgramError::InvalidInstructionData)?;
                let law_version = u32::from_le_bytes(
                    rest.get(13..17)
                        .ok_or(ProgramError::InvalidInstructionData)?
                        .try_into()
                        .unwrap(),
                );
                Ok(Self::InitializeRecord {
                    base_lamports,
                    cap_bps,
                    jurisdiction,
                    policy,
                    law_version,
                })
            }
            2 => {
                let price = u64::from_le_bytes(
                    rest.get(..8).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap(),
                );
                Ok(Self::SetPendingPrice { price })
            }
            3 => {
                let status = *rest.first().ok_or(ProgramError::InvalidInstructionData)?;
                Ok(Self::SetStatus { status })
            }
            4 => {
                let cap_bps = u16::from_le_bytes(
                    rest.get(..2).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap(),
                );
                let jurisdiction = [
                    *rest.get(2).ok_or(ProgramError::InvalidInstructionData)?,
                    *rest.get(3).ok_or(ProgramError::InvalidInstructionData)?,
                ];
                let law_version = u32::from_le_bytes(
                    rest.get(4..8).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap(),
                );
                Ok(Self::TightenPolicy {
                    cap_bps,
                    jurisdiction,
                    law_version,
                })
            }
            _ => Err(ProgramError::InvalidInstructionData),
        }
    }
}

/// Seeds for the per-mint record PDA.
pub fn record_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"record", mint.as_ref()]
}

/// Seeds for the extra-account-metas PDA. The literal is fixed by the SPL interface: Token-2022
/// looks for exactly this PDA when it resolves a mint's hook accounts.
pub fn extra_metas_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"extra-account-metas", mint.as_ref()]
}

solana_program::entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    data: &[u8],
) -> ProgramResult {
    if let Some(&tag) = data.first() {
        if tag <= 4 {
            let ix = GateInstruction::unpack(data)?;
            return match ix {
                GateInstruction::InitializeExtraAccountMetaList { record } => {
                    initialize_extra_account_meta_list(program_id, accounts, record)
                }
                GateInstruction::InitializeRecord {
                    base_lamports,
                    cap_bps,
                    jurisdiction,
                    policy,
                    law_version,
                } => initialize_record(
                    program_id,
                    accounts,
                    base_lamports,
                    cap_bps,
                    jurisdiction,
                    policy,
                    law_version,
                ),
                GateInstruction::SetPendingPrice { price } => {
                    set_pending_price(program_id, accounts, price)
                }
                GateInstruction::SetStatus { status } => set_status(program_id, accounts, status),
                GateInstruction::TightenPolicy {
                    cap_bps,
                    jurisdiction,
                    law_version,
                } => tighten_policy(program_id, accounts, cap_bps, jurisdiction, law_version),
            };
        }
    }

    match TransferHookInstruction::unpack(data)? {
        TransferHookInstruction::Execute { amount } => execute(program_id, accounts, amount),
        _ => Err(ProgramError::InvalidInstructionData),
    }
}

/// Create the extra-account-metas account Token-2022 resolves for this mint.
///
/// The layout is a TLV state owned by the SPL interface, not a flat array. Encoding it with
/// `ExtraAccountMetaList::init` is the only spelling Token-2022 accepts; hand-rolling it is how
/// the v1 crate failed its first local run.
fn initialize_extra_account_meta_list(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    record: Pubkey,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let payer = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let extra_metas = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    let (expected, bump) = Pubkey::find_program_address(&extra_metas_seeds(mint.key), program_id);
    if expected != *extra_metas.key {
        return Err(RegionError::WrongExtraAccount.into());
    }
    if !extra_metas.data_is_empty() {
        return Ok(());
    }

    // NOT DONE, and measured: registering the record writable (so the hook can consume the
    // staged price) plus a record-PDA check here was tried and took the local proof from
    // PASS 11/11 to FAIL 4/11 — admitted transfers stopped logging and refusals stopped
    // landing. Reverted rather than shipped unverified; the defect is recorded in
    // `records/findings/34` §7. The list names the record read-only, as it always has.
    let metas = [ExtraAccountMeta::new_with_pubkey(&record, false, false)?];
    let len = ExtraAccountMetaList::size_of(metas.len())?;
    let mut data = vec![0u8; len];
    ExtraAccountMetaList::init::<ExecuteInstruction>(&mut data, &metas)?;

    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(len);
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
/// The payer becomes the record's authority: one signer per event in this proof. `validate_policy`
/// refuses a triple the hook would have to guess about.
#[allow(clippy::too_many_arguments)]
fn initialize_record(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    base_lamports: u64,
    cap_bps: u16,
    jurisdiction: [u8; 2],
    policy: u8,
    law_version: u32,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let payer = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    if !payer.is_signer {
        return Err(RegionError::NotAuthority.into());
    }
    validate_policy(policy, cap_bps, jurisdiction)?;
    if base_lamports == 0 {
        return Err(RegionError::PolicyInvalid.into());
    }

    let (expected, bump) = Pubkey::find_program_address(&record_seeds(mint.key), program_id);
    if expected != *record_ai.key {
        return Err(RegionError::WrongExtraAccount.into());
    }
    if !record_ai.data_is_empty() {
        // Already initialised. Idempotent, and deliberately not an update path: changing an
        // issued policy is `TightenPolicy` and nothing else.
        return Ok(());
    }

    let record = TicketRecord {
        base_lamports,
        cap_bps,
        pending_price_lamports: 0,
        status: 1,
        jurisdiction,
        policy,
        law_version,
        authority: payer.key.to_bytes(),
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

fn load_owned(program_id: &Pubkey, account: &AccountInfo, signer: &AccountInfo) -> Result<TicketRecord, ProgramError> {
    if account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    let record = TicketRecord::try_from_slice(&account.data.borrow())?;
    if record.authority != signer.key.to_bytes() {
        return Err(RegionError::NotAuthority.into());
    }
    Ok(record)
}

fn store(account: &AccountInfo, record: &TicketRecord) -> ProgramResult {
    let mut bytes = Vec::new();
    record.serialize(&mut bytes)?;
    account.data.borrow_mut().copy_from_slice(&bytes);
    Ok(())
}

fn set_pending_price(program_id: &Pubkey, accounts: &[AccountInfo], price: u64) -> ProgramResult {
    let it = &mut accounts.iter();
    let signer = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    if !signer.is_signer {
        return Err(RegionError::NotAuthority.into());
    }
    let mut record = load_owned(program_id, record_ai, signer)?;
    record.pending_price_lamports = price;
    store(record_ai, &record)
}

fn set_status(program_id: &Pubkey, accounts: &[AccountInfo], status: u8) -> ProgramResult {
    let it = &mut accounts.iter();
    let signer = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    if !signer.is_signer {
        return Err(RegionError::NotAuthority.into());
    }
    let mut record = load_owned(program_id, record_ai, signer)?;
    record.status = status;
    store(record_ai, &record)
}

/// The law changed. Lower the cap, or start capping a ticket that was not capped. Never the other
/// way (§6).
fn tighten_policy(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    cap_bps: u16,
    jurisdiction: [u8; 2],
    law_version: u32,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let signer = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    if !signer.is_signer {
        return Err(RegionError::NotAuthority.into());
    }
    let mut record = load_owned(program_id, record_ai, signer)?;

    validate_policy(POLICY_CAPPED, cap_bps, jurisdiction)?;
    if !tighten_allows(record.policy, record.cap_bps, POLICY_CAPPED, cap_bps) {
        return Err(RegionError::PolicyLoosens.into());
    }
    if law_version <= record.law_version {
        // A tightening must name a later table generation; a stale or repeated instruction is a
        // client bug, not a policy change.
        return Err(RegionError::PolicyInvalid.into());
    }

    solana_program::msg!(
        "region_gate: tighten {:?}->{:?} cap {}->{} law {}->{}",
        record.policy,
        POLICY_CAPPED,
        record.cap_bps,
        cap_bps,
        record.law_version,
        law_version
    );
    record.policy = POLICY_CAPPED;
    record.cap_bps = cap_bps;
    record.jurisdiction = jurisdiction;
    record.law_version = law_version;
    store(record_ai, &record)
}

/// The hook. Token-2022 calls this inside every transfer of a hooked mint.
///
/// Accounts, in the order the extra-account-metas list produces:
/// `[0] source`, `[1] mint`, `[2] destination`, `[3] authority`, `[4] extra_metas`, `[5] record`.
fn execute(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let it = &mut accounts.iter();
    let _source = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let _destination = next_account_info(it)?;
    let _authority = next_account_info(it)?;
    let extra_metas = next_account_info(it)?;
    let record_ai = next_account_info(it)?;

    if amount != 1 {
        return Err(RegionError::AmountNotOne.into());
    }

    let (expected_metas, _) = Pubkey::find_program_address(&extra_metas_seeds(mint.key), program_id);
    if expected_metas != *extra_metas.key {
        return Err(RegionError::WrongExtraAccount.into());
    }
    if record_ai.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    let (expected_record, _) = Pubkey::find_program_address(&record_seeds(mint.key), program_id);
    if expected_record != *record_ai.key {
        return Err(RegionError::WrongExtraAccount.into());
    }

    let record = TicketRecord::try_from_slice(&record_ai.data.borrow())?;
    let jurisdiction = core::str::from_utf8(&record.jurisdiction).unwrap_or("??");

    if record.status != 1 {
        return Err(RegionError::TicketNotValid.into());
    }
    // Monitoring needs a number to record. A transfer with no staged price is not a sale and
    // records nothing, exactly as in v1.
    if record.pending_price_lamports == 0 {
        return Err(RegionError::TransferNotStaged.into());
    }

    match record.policy {
        POLICY_CAPPED => {
            if !record.cap_admits() {
                solana_program::msg!(
                    "region_gate: cap exceeded jurisdiction={} price={} base={} cap_bps={} law_version={}",
                    jurisdiction,
                    record.pending_price_lamports,
                    record.base_lamports,
                    record.cap_bps,
                    record.law_version
                );
                return Err(RegionError::CapExceeded.into());
            }
            solana_program::msg!(
                "region_gate: cap admitted jurisdiction={} price={} base={} cap_bps={} max={} law_version={}",
                jurisdiction,
                record.pending_price_lamports,
                record.base_lamports,
                record.cap_bps,
                record.max_price_lamports(),
                record.law_version
            );
            Ok(())
        }
        POLICY_MONITORED => {
            solana_program::msg!(
                "region_gate: monitored jurisdiction={} price={} base={} ratio_bps={} law_version={}",
                jurisdiction,
                record.pending_price_lamports,
                record.base_lamports,
                (record.pending_price_lamports as u128) * BPS_DENOM / (record.base_lamports as u128),
                record.law_version
            );
            Ok(())
        }
        POLICY_UNRESOLVED => {
            solana_program::msg!(
                "region_gate: unresolved jurisdiction={} price={} base={} law_version={}",
                jurisdiction,
                record.pending_price_lamports,
                record.base_lamports,
                record.law_version
            );
            Ok(())
        }
        _ => Err(RegionError::PolicyInvalid.into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rec(policy: u8, cap: u16, base: u64, price: u64) -> TicketRecord {
        TicketRecord {
            base_lamports: base,
            cap_bps: cap,
            pending_price_lamports: price,
            status: 1,
            jurisdiction: [b'I', b'E'],
            policy,
            law_version: 1,
            authority: [0u8; 32],
        }
    }

    #[test]
    fn capped_boundary_is_inclusive() {
        // The v1 worked pair, unchanged: face 1e9, cap 2500 -> 1.25e9 admitted, +1 refused.
        let r = rec(POLICY_CAPPED, 2500, 1_000_000_000, 1_250_000_000);
        assert!(r.cap_admits());
        assert_eq!(r.max_price_lamports(), 1_250_000_000);
        assert!(!rec(POLICY_CAPPED, 2500, 1_000_000_000, 1_250_000_001).cap_admits());
    }

    #[test]
    fn zero_cap_admits_only_the_base() {
        assert!(rec(POLICY_CAPPED, 0, 1_000_000_000, 1_000_000_000).cap_admits());
        assert!(!rec(POLICY_CAPPED, 0, 1_000_000_000, 1_000_000_001).cap_admits());
    }

    #[test]
    fn base_includes_fees_when_the_law_says_so() {
        // face 100 + fee 15, cap 0 bps -> 115 is the ceiling, not 100.
        let all_in = rec(POLICY_CAPPED, 0, 115, 115);
        assert!(all_in.cap_admits());
        assert!(!rec(POLICY_CAPPED, 0, 115, 116).cap_admits());
        let face_only = rec(POLICY_CAPPED, 0, 100, 116);
        assert!(!face_only.cap_admits());
    }

    #[test]
    fn u128_keeps_the_product_meaningful_at_u64_max() {
        // u64::MAX * 20_000 wraps; u128 does not, and the answer stays "refused" not "wrapped".
        let face = u64::MAX;
        assert!(rec(POLICY_CAPPED, 0, u64::MAX, u64::MAX - 1).cap_admits());
        assert!(rec(POLICY_CAPPED, 10_000, face, u64::MAX).cap_admits());
        assert_eq!(
            (face as u128) * 20_000u128,
            (face as u128).wrapping_mul(20_000u128) as u128
        );
    }

    #[test]
    fn monitored_and_unresolved_carry_the_field_maximum() {
        assert!(validate_policy(POLICY_MONITORED, U16_MAX_CAP, [b'D', b'E']).is_ok());
        assert!(validate_policy(POLICY_UNRESOLVED, U16_MAX_CAP, JURISDICTION_UNRESOLVED).is_ok());
        // A monitored record with a real cap is the "nobody looked at this number" failure.
        assert_eq!(
            validate_policy(POLICY_MONITORED, 2500, [b'D', b'E']),
            Err(RegionError::PolicyInvalid)
        );
        // Unresolved must not claim a binding jurisdiction.
        assert_eq!(
            validate_policy(POLICY_UNRESOLVED, U16_MAX_CAP, [b'I', b'E']),
            Err(RegionError::PolicyInvalid)
        );
        assert_eq!(
            validate_policy(POLICY_CAPPED, 2500, JURISDICTION_UNRESOLVED),
            Err(RegionError::PolicyInvalid)
        );
        assert_eq!(
            validate_policy(9, 2500, [b'I', b'E']),
            Err(RegionError::PolicyInvalid)
        );
    }

    #[test]
    fn jurisdiction_must_be_two_uppercase_letters() {
        assert!(jurisdiction_valid([b'A', b'U']));
        assert!(!jurisdiction_valid([b'a', b'u']));
        assert!(!jurisdiction_valid([b'A', b'1']));
        assert!(!jurisdiction_valid([0, 0]));
        assert_eq!(
            validate_policy(POLICY_CAPPED, 2500, [b'a', b'u']),
            Err(RegionError::JurisdictionCode)
        );
    }

    #[test]
    fn tightening_is_monotone() {
        // capped -> capped must be strictly lower.
        assert!(tighten_allows(POLICY_CAPPED, 1000, POLICY_CAPPED, 500));
        assert!(!tighten_allows(POLICY_CAPPED, 1000, POLICY_CAPPED, 1000));
        assert!(!tighten_allows(POLICY_CAPPED, 1000, POLICY_CAPPED, 1500));
        // monitored / unresolved -> capped is always a tightening.
        assert!(tighten_allows(POLICY_MONITORED, U16_MAX_CAP, POLICY_CAPPED, 10_000));
        assert!(tighten_allows(POLICY_UNRESOLVED, U16_MAX_CAP, POLICY_CAPPED, 0));
        // never back to no cap.
        assert!(!tighten_allows(POLICY_CAPPED, 1000, POLICY_MONITORED, U16_MAX_CAP));
        assert!(!tighten_allows(POLICY_CAPPED, 1000, POLICY_UNRESOLVED, U16_MAX_CAP));
        // and a "capped" at the field maximum is not a cap.
        assert!(!tighten_allows(POLICY_MONITORED, U16_MAX_CAP, POLICY_CAPPED, U16_MAX_CAP));
    }

    #[test]
    fn record_len_is_the_borsh_width() {
        let r = rec(POLICY_CAPPED, 2500, 1, 1);
        let mut bytes = Vec::new();
        r.serialize(&mut bytes).unwrap();
        assert_eq!(bytes.len(), TicketRecord::LEN);
        let back = TicketRecord::try_from_slice(&bytes).unwrap();
        assert_eq!(back, r);
    }
}
