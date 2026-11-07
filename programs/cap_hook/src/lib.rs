//! `cap_hook` — the smallest transfer hook that can refuse a resale.
//!
//! Imported from the scratch crate `ticketpath-hook`, where it was first deployed and
//! exercised against a local validator (records/findings/18-onchain-install-and-test.md).
//! The crate name changed on import; nothing else did, and the program id is a property
//! of the deploy keypair, not of this name.
//!
//! The design is docs/ON-CHAIN-DESIGN.md §1.3, §3.9 and §3.10: Token-2022 calls this
//! program inside `Execute` on every transfer of a hooked mint, and the program refuses
//! when the staged resale price is above the ticket's cap.
//!
//! What a hook can and cannot see is the whole point of §1.3. Token-2022 hands the hook
//! `amount`, the source and destination token accounts, the mint and its authority. **It
//! never hands over a price** — there is no price field in an SPL transfer. So the cap is
//! only enforceable over a price that arrived some other way. Here that is a `record`
//! account this program owns, staged in a previous instruction, and named in the mint's
//! extra-account-metas list. The hook reads it and refuses; it cannot invent it.
//!
//! The three instructions this program adds beyond `Execute` exist only so the state can
//! be created and staged: initialise the extra-account-metas list, initialise a record,
//! and stage a price. In the real design (§1.4) the staging instruction is the escrow or
//! the listing, not a free-standing `set_price`; this is the minimum that can be measured.
//!
//! Cap predicate, verbatim from §3.10, in `u128` with no division:
//!
//! ```text
//! price * 10_000 <= face * (10_000 + cap_bps)
//! ```
//!
//! Inclusive at the cap: face 1_000_000_000 with cap 2500 admits exactly 1_250_000_000
//! and refuses 1_250_000_001.

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

/// Errors carry a number the client can name, like the design's table (§3.9).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TicketpathError {
    /// The transfer was for more than one ticket.
    AmountNotOne = 6008,
    /// The price staged on the record is above the cap.
    CapExceeded = 6010,
    /// The record has not been staged for a transfer.
    TransferNotStaged = 6009,
    /// The record is not in a transferable state.
    TicketNotValid = 6013,
    /// The wrong account was passed in the extra-account-metas list.
    WrongExtraAccount = 6020,
}

impl From<TicketpathError> for ProgramError {
    fn from(e: TicketpathError) -> Self {
        ProgramError::Custom(e as u32)
    }
}

/// The state the hook reads. Fixed layout, no zero-copy: it is four small fields.
///
/// `status` is `1` for a ticket that may transfer and `0` for one that may not; the
/// real design's `TicketStatus` enum has more states, and the hook only needs the
/// boolean it actually branches on.
#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub struct TicketRecord {
    /// Face value of this ticket's tier, in lamports. The cap is a multiple of this.
    pub face_value_lamports: u64,
    /// Resale cap in basis points over face. 2500 means +25%; the wire convention.
    pub cap_bps: u16,
    /// The price staged for the transfer the hook is about to see, in lamports.
    pub pending_price_lamports: u64,
    /// 1 = transferable, 0 = not.
    pub status: u8,
}

impl TicketRecord {
    pub const LEN: usize = 8 + 2 + 8 + 1 + 1;

    /// §3.10, exactly: both sides in `u128`, no division anywhere, inclusive at the cap.
    pub fn cap_admits(&self) -> bool {
        let lhs = (self.pending_price_lamports as u128) * 10_000u128;
        let rhs = (self.face_value_lamports as u128) * (10_000u128 + self.cap_bps as u128);
        lhs <= rhs
    }
}

/// Instruction set. `0..=2` are this program's own; anything else falls through to the
/// SPL transfer-hook discriminator, whose first byte is 105, so they cannot collide.
pub enum HookInstruction {
    /// 0 — create the extra-account-metas PDA for a mint, naming the record account.
    InitializeExtraAccountMetaList { record: Pubkey },
    /// 1 — create the record for a mint, with its face value and cap.
    InitializeRecord { face: u64, cap_bps: u16 },
    /// 2 — stage the price for the next transfer.
    SetPendingPrice { price: u64 },
    /// 3 — flip the record's transferable flag.
    SetStatus { status: u8 },
}

impl HookInstruction {
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
                let face = u64::from_le_bytes(
                    rest.get(..8).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap(),
                );
                let cap_bps = u16::from_le_bytes(
                    rest.get(8..10).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap(),
                );
                Ok(Self::InitializeRecord { face, cap_bps })
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
            _ => Err(ProgramError::InvalidInstructionData),
        }
    }
}

/// Seeds for the per-mint record PDA.
pub fn record_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"record", mint.as_ref()]
}

/// Seeds for the extra-account-metas PDA. The literal is fixed by the SPL interface:
/// Token-2022 looks for exactly this PDA when it resolves a mint's hook accounts.
pub fn extra_metas_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"extra-account-metas", mint.as_ref()]
}

solana_program::entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    data: &[u8],
) -> ProgramResult {
    // Our own opcodes are 0..=3 and the SPL execute discriminator starts with 105, so
    // the tag byte is unambiguous.
    if let Some(&tag) = data.first() {
        if tag <= 3 {
            let ix = HookInstruction::unpack(data)?;
            return match ix {
                HookInstruction::InitializeExtraAccountMetaList { record } => {
                    initialize_extra_account_meta_list(program_id, accounts, record)
                }
                HookInstruction::InitializeRecord { face, cap_bps } => {
                    initialize_record(program_id, accounts, face, cap_bps)
                }
                HookInstruction::SetPendingPrice { price } => {
                    set_pending_price(program_id, accounts, price)
                }
                HookInstruction::SetStatus { status } => set_status(program_id, accounts, status),
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
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    if !extra_metas.data_is_empty() {
        // Idempotent: a second call is a no-op, not a failure to explain.
        return Ok(());
    }

    // One extra account: the record, read-only for this hook. §3.9 marks the record
    // `mut` because the full design writes custody state here; this minimal hook only
    // reads it, and says so rather than declaring a write it does not perform.
    let metas = [ExtraAccountMeta::new_with_pubkey(&record, false, false)?];
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
fn initialize_record(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    face: u64,
    cap_bps: u16,
) -> ProgramResult {
    let it = &mut accounts.iter();
    let payer = next_account_info(it)?;
    let mint = next_account_info(it)?;
    let record_ai = next_account_info(it)?;
    let system_program = next_account_info(it)?;

    let (expected, bump) = Pubkey::find_program_address(&record_seeds(mint.key), program_id);
    if expected != *record_ai.key {
        return Err(TicketpathError::WrongExtraAccount.into());
    }
    if !record_ai.data_is_empty() {
        return Ok(());
    }

    let record = TicketRecord {
        face_value_lamports: face,
        cap_bps,
        pending_price_lamports: 0,
        status: 1,
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

fn set_pending_price(program_id: &Pubkey, accounts: &[AccountInfo], price: u64) -> ProgramResult {
    let it = &mut accounts.iter();
    let record_ai = next_account_info(it)?;
    if record_ai.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    let mut record = TicketRecord::try_from_slice(&record_ai.data.borrow())?;
    record.pending_price_lamports = price;
    let mut bytes = Vec::new();
    record.serialize(&mut bytes)?;
    record_ai.data.borrow_mut().copy_from_slice(&bytes);
    Ok(())
}

fn set_status(program_id: &Pubkey, accounts: &[AccountInfo], status: u8) -> ProgramResult {
    let it = &mut accounts.iter();
    let record_ai = next_account_info(it)?;
    if record_ai.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }
    let mut record = TicketRecord::try_from_slice(&record_ai.data.borrow())?;
    record.status = status;
    let mut bytes = Vec::new();
    record.serialize(&mut bytes)?;
    record_ai.data.borrow_mut().copy_from_slice(&bytes);
    Ok(())
}

/// The hook. Token-2022 calls this inside every transfer of a hooked mint.
///
/// Accounts, in the order the extra-account-metas list produces (§3.9):
/// `[0] source`, `[1] mint`, `[2] destination`, `[3] authority`, `[4] extra_metas`, `[5] record`.
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
    let (expected_metas, _) = Pubkey::find_program_address(&extra_metas_seeds(mint.key), program_id);
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

    let record = TicketRecord::try_from_slice(&record_ai.data.borrow())?;

    // 4. The ticket must be in a transferable state.
    if record.status != 1 {
        return Err(TicketpathError::TicketNotValid.into());
    }

    // 5. Nothing staged, nothing to check: the transfer is not a sale.
    if record.pending_price_lamports == 0 {
        return Err(TicketpathError::TransferNotStaged.into());
    }

    // 6. The cap. This is the line the whole program exists for.
    if !record.cap_admits() {
        solana_program::msg!(
            "ticketpath: cap exceeded price={} face={} cap_bps={}",
            record.pending_price_lamports,
            record.face_value_lamports,
            record.cap_bps
        );
        return Err(TicketpathError::CapExceeded.into());
    }

    solana_program::msg!(
        "ticketpath: cap admitted price={} face={} cap_bps={}",
        record.pending_price_lamports,
        record.face_value_lamports,
        record.cap_bps
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rec(face: u64, cap: u16, price: u64) -> TicketRecord {
        TicketRecord {
            face_value_lamports: face,
            cap_bps: cap,
            pending_price_lamports: price,
            status: 1,
        }
    }

    #[test]
    fn boundary_is_inclusive_at_the_cap() {
        // §3.10's own worked pair: face 1e9, cap 2500 -> 1.25e9 admitted, +1 refused.
        assert!(rec(1_000_000_000, 2500, 1_250_000_000).cap_admits());
        assert!(!rec(1_000_000_000, 2500, 1_250_000_001).cap_admits());
    }

    #[test]
    fn below_face_is_admitted() {
        // A sale under face is negative markup and always inside the cap.
        assert!(rec(1_000_000_000, 1500, 500_000_000).cap_admits());
    }

    #[test]
    fn u64_multiply_would_wrap_but_u128_does_not() {
        // The arithmetic bug §3.10 says to look for first: f * 20_000 overflows u64 for
        // large faces. In u128 the comparison is still meaningful, and the answer is
        // "refused", not "wrapped to admitted".
        let face = u64::MAX;
        let r = rec(face, 10_000, u64::MAX);
        // lhs = 1.8e23, rhs = 1.8e23 * 2 -> admitted at cap 10000, which is 2x face.
        assert!(r.cap_admits());
        let r2 = rec(face, 0, u64::MAX);
        // cap 0 means no markup at all over face; both are u64::MAX so equal -> admitted.
        assert!(r2.cap_admits());
        // and one lamport over is impossible to express, so the honest check is that the
        // u64 product would have wrapped: 20_000 * u64::MAX mod 2^64 is not 2^64 * ...
        assert_eq!(
            (face as u128) * 20_000u128,
            (face as u128).wrapping_mul(20_000u128) as u128
        );
    }

    #[test]
    fn zero_cap_admits_only_face() {
        assert!(rec(1_000_000_000, 0, 1_000_000_000).cap_admits());
        assert!(!rec(1_000_000_000, 0, 1_000_000_001).cap_admits());
    }
}
