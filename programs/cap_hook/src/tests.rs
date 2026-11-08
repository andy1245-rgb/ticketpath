//! Unit tests for the record, the two price predicates, the wire format and the flag the
//! extra-account-metas list has to carry.
//!
//! Every test here is written to fail when the thing it names flips: the cap boundary, the
//! floor boundary, the policy branch, the byte layout, the rebate curve, the u64/u128
//! difference, and the writable flag. A test that would still pass with the predicate
//! inverted is not in this file.
//!
//! What is not here, and why: the branch of `execute` that writes the clock needs a real
//! runtime, because `Clock::get` has no stub on the host. `execute` is therefore called below
//! only on the read-only path, which does not read the clock, and the price decision it takes
//! is `admit`, which is pure. That an admitted transfer on a writable record stores the
//! timestamp it read is what the local-validator run has to prove.

use super::*;
use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::pubkey::Pubkey;
use spl_tlv_account_resolution::state::ExtraAccountMetaList;
use spl_transfer_hook_interface::instruction::ExecuteInstruction;
use std::mem::offset_of;

/// A capped record with no floor, which is the v1 shape as v2 stores it.
fn capped(face: u64, cap_bps: u16, price: u64) -> TicketRecord {
    TicketRecord {
        face_value_lamports: face,
        cap_bps,
        pending_price_lamports: price,
        status: 1,
        band_low_lamports: 0,
        jurisdiction: *b"CA",
        policy: POLICY_CAPPED,
        held_since_unix: 0,
        authority: Pubkey::new_from_array([7u8; 32]),
    }
}

/// The same record, with a floor and/or a different policy.
fn with(mut record: TicketRecord, band_low: u64, policy: u8) -> TicketRecord {
    record.band_low_lamports = band_low;
    record.policy = policy;
    record
}

// -- the cap, unchanged from v1 ---------------------------------------------------------

#[test]
fn cap_boundary_is_inclusive_and_one_lamport_over_is_refused() {
    // §3.10's own worked pair: face 1e9, cap 2500 -> 1.25e9 admitted, +1 refused. Through
    // `admit`, so this fails if the boundary moves or the predicate inverts.
    assert_eq!(
        admit(&capped(1_000_000_000, 2500, 1_250_000_000)),
        Ok(Admission::Capped)
    );
    assert_eq!(
        admit(&capped(1_000_000_000, 2500, 1_250_000_001)),
        Err(TicketpathError::CapExceeded)
    );
    // Cap 0 means no markup at all: face itself is the ceiling.
    assert_eq!(
        admit(&capped(1_000_000_000, 0, 1_000_000_000)),
        Ok(Admission::Capped)
    );
    assert_eq!(
        admit(&capped(1_000_000_000, 0, 1_000_000_001)),
        Err(TicketpathError::CapExceeded)
    );
    // Under face is negative markup and always inside the cap.
    assert_eq!(
        admit(&capped(1_000_000_000, 2500, 1)),
        Ok(Admission::Capped)
    );
}

// -- the floor, new in v2 ---------------------------------------------------------------

#[test]
fn floor_boundary_is_inclusive_and_zero_means_no_floor() {
    // Equal to the floor is admitted; one lamport below it is not.
    assert_eq!(
        admit(&with(
            capped(1_000_000_000, 2500, 500_000_000),
            500_000_000,
            POLICY_CAPPED
        )),
        Ok(Admission::Capped)
    );
    assert_eq!(
        admit(&with(
            capped(1_000_000_000, 2500, 499_999_999),
            500_000_000,
            POLICY_CAPPED
        )),
        Err(TicketpathError::BelowFloor)
    );
    // band_low == 0 is no floor, not a floor of zero lamports: the smallest price any
    // transfer can stage gets through, and the cap is still the thing that refuses.
    assert_eq!(
        admit(&with(capped(1_000_000_000, 2500, 1), 0, POLICY_CAPPED)),
        Ok(Admission::Capped)
    );
    assert_eq!(
        admit(&with(
            capped(1_000_000_000, 2500, 1_250_000_001),
            0,
            POLICY_CAPPED
        )),
        Err(TicketpathError::CapExceeded)
    );
}

#[test]
fn a_floor_above_the_ceiling_is_unsatisfiable() {
    // A floor above the ceiling admits no price at all, so the record would be a brick that
    // looks like a ticket. `band_satisfiable` is the product form and must agree with
    // `ceiling_lamports` exactly at the boundary.
    assert_eq!(ceiling_lamports(1_000_000_000, 2500), 1_250_000_000);
    assert!(band_satisfiable(1_000_000_000, 2500, 1_250_000_000));
    assert!(!band_satisfiable(1_000_000_000, 2500, 1_250_000_001));
    assert!(band_satisfiable(1_000_000_000, 2500, 0));

    for (face, cap, low) in [
        (1_000_000_000u64, 2500u16, 0u64),
        (1_000_000_000, 0, 1_000_000_000),
        (1_000_000_000, 0, 1_000_000_001),
        (1_000_000_000, 2500, 1_250_000_000),
        (1_000_000_000, 2500, 1_250_000_001),
        (999_999_999, 3333, 333_299_966),
        (999_999_999, 3333, 333_299_967),
    ] {
        assert_eq!(
            band_satisfiable(face, cap, low),
            (low as u128) <= ceiling_lamports(face, cap),
            "band_satisfiable({face}, {cap}, {low}) disagrees with ceiling_lamports"
        );
    }

    // And `InitializeRecord` refuses it with 6022, before any account is created.
    assert_eq!(
        validate_initialize(1_000_000_000, 2500, 1_250_000_001, POLICY_CAPPED),
        Err(TicketpathError::BandUnsatisfiable)
    );
    assert_eq!(
        validate_initialize(1_000_000_000, 2500, 1_250_000_000, POLICY_CAPPED),
        Ok(())
    );
}

#[test]
fn policy_two_is_not_a_policy() {
    // 0 and 1 are the domain (state.rs `POLICY_*`); everything else is 6023, and it is
    // refused before the band check so a caller gets the first wrong thing first.
    assert_eq!(
        validate_initialize(1_000_000_000, 2500, 0, POLICY_CAPPED),
        Ok(())
    );
    assert_eq!(
        validate_initialize(1_000_000_000, 2500, 0, POLICY_MONITORED),
        Ok(())
    );
    assert_eq!(
        validate_initialize(1_000_000_000, 2500, 0, 2),
        Err(TicketpathError::PolicyInvalid)
    );
    assert_eq!(
        validate_initialize(1_000_000_000, 2500, 0, u8::MAX),
        Err(TicketpathError::PolicyInvalid)
    );
    // Both wrong: the policy is reported, not the band.
    assert_eq!(
        validate_initialize(1_000_000_000, 2500, 2_000_000_000, 7),
        Err(TicketpathError::PolicyInvalid)
    );
}

// -- the policy branch ------------------------------------------------------------------

#[test]
fn monitored_admits_what_capped_refuses() {
    // Over the cap: the capped record refuses, the monitored one records and admits.
    let over = 1_250_000_001;
    let under = 399_999_999;
    let floor = 400_000_000;
    let face = 1_000_000_000;
    let cap = 2500;

    assert_eq!(
        admit(&with(capped(face, cap, over), floor, POLICY_CAPPED)),
        Err(TicketpathError::CapExceeded)
    );
    assert_eq!(
        admit(&with(capped(face, cap, over), floor, POLICY_MONITORED)),
        Ok(Admission::Monitored)
    );

    assert_eq!(
        admit(&with(capped(face, cap, under), floor, POLICY_CAPPED)),
        Err(TicketpathError::BelowFloor)
    );
    assert_eq!(
        admit(&with(capped(face, cap, under), floor, POLICY_MONITORED)),
        Ok(Admission::Monitored)
    );

    // The branch is the policy and not the price: the same admitted price reports `Capped`
    // on a capped record and `Monitored` on a monitored one, which is what makes the log
    // line able to say the cap was not the reason.
    let inside = 1_000_000_000;
    assert_eq!(
        admit(&with(capped(face, cap, inside), floor, POLICY_CAPPED)),
        Ok(Admission::Capped)
    );
    assert_eq!(
        admit(&with(capped(face, cap, inside), floor, POLICY_MONITORED)),
        Ok(Admission::Monitored)
    );
}

// -- the layout is the wire contract ----------------------------------------------------

#[test]
fn len_constants_equal_the_real_serializations() {
    // Every field is non-zero and distinct, so a field dropped from the struct or from LEN
    // shows up as a mismatch rather than as two zero blocks that happen to agree.
    let record = TicketRecord {
        face_value_lamports: 1_000_000_000,
        cap_bps: 2_500,
        pending_price_lamports: 1_250_000_000,
        status: 1,
        band_low_lamports: 400_000_000,
        jurisdiction: *b"CA",
        policy: POLICY_MONITORED,
        held_since_unix: 1_760_000_000,
        authority: Pubkey::new_from_array([7u8; 32]),
    };
    let band = Band {
        version: 1,
        low: 11,
        high: 22,
        as_of_slot: 33,
        published_slot: 44,
        sample_n: 55,
        refused: 0,
        model_hash: [2u8; 32],
        authority: [3u8; 32],
    };
    let forecast = Forecast {
        version: 1,
        mint: [4u8; 32],
        low: 111,
        high: 222,
        as_of_unix: 1_760_000_000,
        sample_n: 7,
        model_hash: [5u8; 32],
        scoring_rule_hash: [6u8; 32],
        created_slot: 888,
        authority: [8u8; 32],
    };
    let score = Score {
        version: 1,
        realised_lamports: 1_000_000_000,
        interval_score_micro: 2_000_000,
        covered: 1,
        scored_slot: 999,
        scorer: [9u8; 32],
    };

    let mut r = Vec::new();
    record.serialize(&mut r).unwrap();
    let mut b = Vec::new();
    band.serialize(&mut b).unwrap();
    let mut f = Vec::new();
    forecast.serialize(&mut f).unwrap();
    let mut s = Vec::new();
    score.serialize(&mut s).unwrap();

    assert_eq!(
        r.len(),
        TicketRecord::LEN,
        "TicketRecord::LEN is not the real length"
    );
    assert_eq!(b.len(), Band::LEN, "Band::LEN is not the real length");
    assert_eq!(
        f.len(),
        Forecast::LEN,
        "Forecast::LEN is not the real length"
    );
    assert_eq!(s.len(), Score::LEN, "Score::LEN is not the real length");
    assert_eq!(TicketRecord::LEN, 70);
    assert_eq!(Band::LEN, 102);
    assert_eq!(Forecast::LEN, 165);
    assert_eq!(Score::LEN, 58);

    // Round-trip: Borsh is positional, so a reordered pair of fields of the same width
    // would still be 70 bytes and would fail here.
    assert_eq!(TicketRecord::try_from_slice(&r).unwrap(), record);
    assert_eq!(Band::try_from_slice(&b).unwrap(), band);
    assert_eq!(Forecast::try_from_slice(&f).unwrap(), forecast);
    assert_eq!(Score::try_from_slice(&s).unwrap(), score);
}

#[test]
fn record_wire_offsets_are_the_documented_ones() {
    // The offsets a python decoder has to code against, pinned. A field inserted in the
    // middle passes the LEN test above and fails this one, which is the point.
    let record = TicketRecord {
        face_value_lamports: 0x0102_0304_0506_0708,
        cap_bps: 0x090a,
        pending_price_lamports: 0x1112_1314_1516_1718,
        status: 0x19,
        band_low_lamports: 0x2122_2324_2526_2728,
        jurisdiction: *b"CA",
        policy: 0x2b,
        held_since_unix: 0x3132_3334_3536_3738,
        authority: Pubkey::new_from_array([0x41u8; 32]),
    };
    let mut bytes = Vec::new();
    record.serialize(&mut bytes).unwrap();

    assert_eq!(&bytes[0..8], &0x0102_0304_0506_0708u64.to_le_bytes());
    assert_eq!(&bytes[8..10], &0x090au16.to_le_bytes());
    assert_eq!(&bytes[10..18], &0x1112_1314_1516_1718u64.to_le_bytes());
    assert_eq!(bytes[18], 0x19);
    assert_eq!(&bytes[19..27], &0x2122_2324_2526_2728u64.to_le_bytes());
    assert_eq!(&bytes[27..29], b"CA".as_slice());
    assert_eq!(bytes[29], 0x2b);
    assert_eq!(&bytes[30..38], &0x3132_3334_3536_3738i64.to_le_bytes());
    assert_eq!(&bytes[38..70], &[0x41u8; 32][..]);
}

#[test]
fn initialize_record_takes_21_argument_bytes_after_the_tag() {
    // The exact payload a client builds: tag, then face, cap_bps, band_low, jurisdiction,
    // policy, little-endian, in that order.
    let mut wire = vec![1u8];
    wire.extend_from_slice(&1_000_000_000u64.to_le_bytes());
    wire.extend_from_slice(&2_500u16.to_le_bytes());
    wire.extend_from_slice(&400_000_000u64.to_le_bytes());
    wire.extend_from_slice(b"CA");
    wire.push(POLICY_CAPPED);
    assert_eq!(wire.len(), 22, "1 tag byte + 21 argument bytes");

    match HookInstruction::unpack(&wire).unwrap() {
        HookInstruction::InitializeRecord {
            face,
            cap_bps,
            band_low,
            jurisdiction,
            policy,
        } => {
            assert_eq!(face, 1_000_000_000);
            assert_eq!(cap_bps, 2_500);
            assert_eq!(band_low, 400_000_000);
            assert_eq!(&jurisdiction, b"CA");
            assert_eq!(policy, POLICY_CAPPED);
        }
        _ => panic!("tag 1 must unpack as InitializeRecord"),
    }

    // One byte short is invalid data, not a silently zero-padded instruction: a v1 client
    // sending only face and cap would otherwise create a record with no jurisdiction and a
    // cap-only policy.
    assert!(matches!(
        HookInstruction::unpack(&wire[..21]),
        Err(ProgramError::InvalidInstructionData)
    ));
}

// -- the rebate curve (MD4), which `ClaimRebate` will use ------------------------------

#[test]
fn rebate_lamports_at_zero_half_full_and_beyond_full() {
    // REBATE_FEE_BPS = 1500 of the pool at a full hold, HOLD_FULL_SECONDS = 60.
    let pool = 1_000_000u64;
    assert_eq!(rebate_bps(0), 0);
    assert_eq!(rebate_bps(HOLD_FULL_SECONDS / 2), 750);
    assert_eq!(rebate_bps(HOLD_FULL_SECONDS), 1_500);
    assert_eq!(
        rebate_bps(HOLD_FULL_SECONDS * 10),
        1_500,
        "the curve is clamped, not linear"
    );
    assert_eq!(
        rebate_bps(-5),
        0,
        "a clock that went backwards earns nothing"
    );

    assert_eq!(rebate_lamports(pool, 0), 0);
    assert_eq!(rebate_lamports(pool, HOLD_FULL_SECONDS / 2), 75_000);
    assert_eq!(rebate_lamports(pool, HOLD_FULL_SECONDS), 150_000);
    assert_eq!(rebate_lamports(pool, HOLD_FULL_SECONDS * 10), 150_000);
    assert_eq!(rebate_lamports(pool, -5), 0);

    // The predicate form and the computed amount agree exactly, and the next lamport is
    // refused: that is the pair §3.10 asks for, applied to the rebate.
    for held in [
        0,
        1,
        HOLD_FULL_SECONDS / 2,
        HOLD_FULL_SECONDS,
        HOLD_FULL_SECONDS * 10,
    ] {
        let due = rebate_lamports(pool, held);
        assert!(
            rebate_admits(pool, held, due),
            "held {held}: the computed share must pass"
        );
        assert!(
            !rebate_admits(pool, held, due + 1),
            "held {held}: one lamport over the computed share must be refused"
        );
    }
}

// -- the arithmetic the cap rests on ----------------------------------------------------

#[test]
fn the_cap_comparison_cannot_be_done_in_u64() {
    // face 1e12, cap 0, price 1_844_674_407_370_956 (the first price whose *10_000 wraps).
    // The true answer is "refused": the price is 1_844x face. The u64 product wraps to
    // 8_384, which is *below* face * 10_000, so a u64 implementation admits it. This is the
    // case the u128 predicate exists for, and `admit` must refuse it.
    let face = 1_000_000_000_000u64;
    let price = 1_844_674_407_370_956u64;
    assert_eq!(
        price.wrapping_mul(10_000),
        8_384,
        "the premise of this test: the u64 product wraps to 8_384"
    );
    assert!(
        8_384u64 <= face.wrapping_mul(10_000),
        "a u64 comparison says admitted, which is the wrong answer"
    );
    assert_eq!(
        admit(&capped(face, 0, price)),
        Err(TicketpathError::CapExceeded)
    );
}

#[test]
fn u128_at_u64_max_stays_meaningful() {
    // The products do not fit in u64, and the comparison is still the right one: at cap 0
    // the ceiling is exactly u64::MAX, so u64::MAX itself is admitted.
    assert!((u64::MAX as u128) * 20_000u128 > u64::MAX as u128);
    assert_eq!(ceiling_lamports(u64::MAX, 0), u64::MAX as u128);
    assert_eq!(admit(&capped(u64::MAX, 0, u64::MAX)), Ok(Admission::Capped));
    assert_eq!(
        admit(&capped(u64::MAX, 0, u64::MAX - 1)),
        Ok(Admission::Capped)
    );

    // At the largest cap every u64 price is inside the ceiling, and the ceiling itself is
    // larger than any u64, so nothing can be refused for being too high.
    let max_cap = u16::MAX;
    assert!(ceiling_lamports(u64::MAX, max_cap) > u64::MAX as u128);
    assert_eq!(
        admit(&capped(u64::MAX, max_cap, u64::MAX)),
        Ok(Admission::Capped)
    );

    // Division-free and ceiling agree wherever both are representable.
    for (face, cap, price) in [
        (1_000_000_000u64, 2500u16, 1_250_000_000u64),
        (1_000_000_000, 2500, 1_250_000_001),
        (u64::MAX, 0, u64::MAX),
        (u64::MAX, 2500, u64::MAX),
        (u64::MAX, u16::MAX, 1),
    ] {
        assert_eq!(
            capped(face, cap, price).cap_admits(),
            (price as u128) <= ceiling_lamports(face, cap),
            "cap_admits({face}, {cap}, {price}) disagrees with ceiling_lamports"
        );
    }
}

// -- the extra-account-metas flag -------------------------------------------------------

#[test]
fn the_extra_meta_marks_the_record_writable() {
    // Why this test exists: v2's hook writes `held_since_unix` into the record, so the list
    // Token-2022 builds its CPI from has to mark the record writable. A silent `false` here
    // is a hook that runs, refuses on price, and never records a hold.
    assert!(RECORD_META_WRITABLE);

    let record = Pubkey::new_from_array(std::array::from_fn(|i| {
        (i as u8).wrapping_mul(7).wrapping_add(11)
    }));

    // 1. The call site's own flags, resolved the way Token-2022 resolves a plain pubkey.
    let meta = record_extra_meta(&record).unwrap();
    let resolved = meta.resolve(&[], &Pubkey::default(), |_| None).unwrap();
    assert_eq!(resolved.pubkey, record);
    assert!(
        resolved.is_writable,
        "the record must be writable or the hook cannot write it"
    );
    assert!(!resolved.is_signer, "the record is never a signer");

    // 2. The same flag in the initialised TLV list, which is the bytes that outlive the
    //    instruction. Locate the struct by the pubkey it carries and read the pod flags.
    let metas = [record_extra_meta(&record).unwrap()];
    let len = ExtraAccountMetaList::size_of(metas.len()).unwrap();
    let mut data = vec![0u8; len];
    ExtraAccountMetaList::init::<ExecuteInstruction>(&mut data, &metas).unwrap();

    let at = data
        .windows(32)
        .position(|w| w == record.as_ref())
        .expect("the record pubkey must be in the initialised list");
    let start = at - offset_of!(ExtraAccountMeta, address_config);
    assert_eq!(
        data[start + offset_of!(ExtraAccountMeta, discriminator)],
        0,
        "a plain pubkey meta, not a PDA"
    );
    assert_eq!(data[start + offset_of!(ExtraAccountMeta, is_signer)], 0);
    assert_eq!(
        data[start + offset_of!(ExtraAccountMeta, is_writable)],
        1,
        "the initialised list marks the record read-only"
    );
}

// -- the v1 metas shape: a read-only record still has to work ---------------------------

/// The six accounts `execute` reads, in the order the extra-account-metas list produces,
/// with the record at the key the hook derives for `mint`.
///
/// Leaked boxes because `AccountInfo` borrows its lamports and data for its whole life and a
/// test that calls `execute` twice needs two independent sets; a leaked buffer in a test is
/// cheaper to read than a struct that owns six fields.
fn execute_accounts<'a>(
    program_id: &'a Pubkey,
    mint: &'a Pubkey,
    record_key: &'a Pubkey,
    metas_key: &'a Pubkey,
    record_data: &'a mut [u8],
    record_writable: bool,
) -> Vec<AccountInfo<'a>> {
    let token_program: &'a Pubkey = Box::leak(Box::new(Pubkey::new_unique()));
    let source: &'a Pubkey = Box::leak(Box::new(Pubkey::new_unique()));
    let destination: &'a Pubkey = Box::leak(Box::new(Pubkey::new_unique()));
    let authority: &'a Pubkey = Box::leak(Box::new(Pubkey::new_unique()));
    let e1: &'a mut [u8] = Box::leak(Box::new([0u8; 0]));
    let e2: &'a mut [u8] = Box::leak(Box::new([0u8; 0]));
    let e3: &'a mut [u8] = Box::leak(Box::new([0u8; 0]));
    let e4: &'a mut [u8] = Box::leak(Box::new([0u8; 0]));
    let e5: &'a mut [u8] = Box::leak(Box::new([0u8; 0]));
    let l1: &'a mut u64 = Box::leak(Box::new(0u64));
    let l2: &'a mut u64 = Box::leak(Box::new(0u64));
    let l3: &'a mut u64 = Box::leak(Box::new(0u64));
    let l4: &'a mut u64 = Box::leak(Box::new(0u64));
    let l5: &'a mut u64 = Box::leak(Box::new(0u64));
    let l6: &'a mut u64 = Box::leak(Box::new(0u64));
    vec![
        AccountInfo::new(source, false, true, l1, e1, token_program, false, 0),
        AccountInfo::new(mint, false, false, l2, e2, token_program, false, 0),
        AccountInfo::new(destination, false, true, l3, e3, token_program, false, 0),
        AccountInfo::new(authority, true, false, l4, e4, program_id, false, 0),
        AccountInfo::new(metas_key, false, false, l5, e5, program_id, false, 0),
        AccountInfo::new(
            record_key,
            false,
            record_writable,
            l6,
            record_data,
            program_id,
            false,
            0,
        ),
    ]
}

#[test]
fn a_read_only_record_still_enforces_the_price_and_is_not_written() {
    // The v1 metas shape: the record arrives read-only. The hook must not fail because of it,
    // must not write it, and must not become a bypass. The writable branch reads the clock
    // (`Clock::get`), which does not exist on the host, so that half is what the local
    // validator proves; this half is provable here.
    let program_id = Pubkey::new_unique();
    let mint = Pubkey::new_unique();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(&mint), &program_id);
    let (metas_key, _) = Pubkey::find_program_address(&extra_metas_seeds(&mint), &program_id);

    let mut data = Vec::new();
    capped(1_000_000_000, 2500, 1_250_000_000)
        .serialize(&mut data)
        .unwrap();
    let before = data.clone();
    {
        let accounts = execute_accounts(
            &program_id,
            &mint,
            &record_key,
            &metas_key,
            &mut data,
            false,
        );
        assert_eq!(execute(&program_id, &accounts, 1), Ok(()));
    }
    assert_eq!(data, before, "a read-only record must not be written");

    let mut data = Vec::new();
    capped(1_000_000_000, 2500, 1_250_000_001)
        .serialize(&mut data)
        .unwrap();
    {
        let accounts = execute_accounts(
            &program_id,
            &mint,
            &record_key,
            &metas_key,
            &mut data,
            false,
        );
        assert_eq!(
            execute(&program_id, &accounts, 1),
            Err(ProgramError::Custom(6010)),
            "the v1 metas shape must not be a way around the cap"
        );
    }
}

// -- the forecast log, tags 4..6 -------------------------------------------------------
//
// These tests call the `*_at` forms, which take the slot instead of reading `Clock::get`.
// On the host the clock sysvar is unsupported, so a test that called the public wrapper
// would fail for the wrong reason; the wrapper is one line and the local validator proves
// the clock write. What is tested here is every predicate that returns before any create,
// plus the band's rewrite branch, which needs no runtime at all.

/// A unique key leaked for the test's lifetime: `AccountInfo` borrows its key and data.
fn leak_pubkey() -> &'static Pubkey {
    Box::leak(Box::new(Pubkey::new_unique()))
}

/// Owned bytes leaked for the test's lifetime, readable again after the call.
fn leak_bytes(bytes: Vec<u8>) -> &'static mut [u8] {
    Box::leak(bytes.into_boxed_slice())
}

/// An `AccountInfo` with its own lamports, so five of them can coexist in one vector.
fn satellite_account<'a>(
    key: &'a Pubkey,
    is_signer: bool,
    is_writable: bool,
    data: &'a mut [u8],
    owner: &'a Pubkey,
) -> AccountInfo<'a> {
    AccountInfo::new(
        key,
        is_signer,
        is_writable,
        Box::leak(Box::new(0u64)),
        data,
        owner,
        false,
        0,
    )
}

fn record_bytes_for(authority: &Pubkey) -> Vec<u8> {
    let mut record = capped(1_000_000_000, 2500, 0);
    record.authority = *authority;
    let mut bytes = Vec::new();
    record.serialize(&mut bytes).unwrap();
    bytes
}

fn forecast_bytes_for(authority: &Pubkey) -> Vec<u8> {
    let mut forecast = forecast_for_write(
        [4u8; 32],
        100,
        200,
        1_760_000_000,
        7,
        [5u8; 32],
        [6u8; 32],
        88,
        [8u8; 32],
    );
    forecast.authority = authority.to_bytes();
    let mut bytes = Vec::new();
    forecast.serialize(&mut bytes).unwrap();
    bytes
}

fn score_bytes_for(scorer: &Pubkey) -> Vec<u8> {
    let score = Score {
        version: SATELLITE_VERSION,
        realised_lamports: 1,
        interval_score_micro: 2,
        covered: 1,
        scored_slot: 3,
        scorer: scorer.to_bytes(),
    };
    let mut bytes = Vec::new();
    score.serialize(&mut bytes).unwrap();
    bytes
}

#[test]
fn band_publish_rewrites_the_head_and_stamps_the_program_clock() {
    // `PublishBand` is init-or-write on purpose: the head follows new evidence, and the
    // history is the forecast log. This test fails if the rewrite branch is turned into a
    // refusal, or if the second write leaves any field of the first behind.
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let authority_key = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let (band_key, _) = Pubkey::find_program_address(&band_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));
    let band_key = Box::leak(Box::new(band_key));

    let record_data = leak_bytes(record_bytes_for(authority_key));
    let mut initial = Vec::new();
    band_for_write(1, 2, 3, 4, 5, 0, [6u8; 32], authority_key.to_bytes())
        .serialize(&mut initial)
        .unwrap();
    let band_data = leak_bytes(initial);
    assert_eq!(band_data.len(), Band::LEN);

    {
        let accounts = vec![
            satellite_account(authority_key, true, true, leak_bytes(vec![]), program_id),
            satellite_account(record_key, false, false, record_data, program_id),
            satellite_account(band_key, false, true, &mut *band_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            publish_band_at(program_id, &accounts, 10, 20, 7, 9, 1, [0xAA; 32], 123),
            Ok(())
        );
        drop(accounts);
    }
    let first = Band::try_from_slice(band_data).unwrap();
    assert_eq!(
        first,
        band_for_write(10, 20, 7, 123, 9, 1, [0xAA; 32], authority_key.to_bytes())
    );
    assert_eq!(first.version, SATELLITE_VERSION);
    assert!(first.published_slot >= first.as_of_slot);

    // Second publish: the same PDA, different bytes in every field that can move.
    let record_data = leak_bytes(record_bytes_for(authority_key));
    {
        let accounts = vec![
            satellite_account(authority_key, true, true, leak_bytes(vec![]), program_id),
            satellite_account(record_key, false, false, record_data, program_id),
            satellite_account(band_key, false, true, &mut *band_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            publish_band_at(program_id, &accounts, 11, 21, 8, 10, 0, [0xBB; 32], 124),
            Ok(())
        );
        drop(accounts);
    }
    let second = Band::try_from_slice(band_data).unwrap();
    assert_eq!(
        second,
        band_for_write(11, 21, 8, 124, 10, 0, [0xBB; 32], authority_key.to_bytes())
    );
    assert_eq!(
        &band_data[..],
        &{
            let mut bytes = Vec::new();
            second.serialize(&mut bytes).unwrap();
            bytes
        }[..]
    );
}

#[test]
fn a_non_authority_cannot_publish_log_or_score() {
    // One record authority, three different writes, one refusal. The check is on the
    // record's `authority` (band/forecast) or the forecast's `authority` (score), never on
    // "someone signed it".
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let owner = leak_pubkey();
    let intruder = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));

    // 4: band
    let (band_key, _) = Pubkey::find_program_address(&band_seeds(mint), program_id);
    let band_key = Box::leak(Box::new(band_key));
    let band_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(intruder, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(owner)),
                program_id,
            ),
            satellite_account(band_key, false, true, &mut *band_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            publish_band_at(program_id, &accounts, 10, 20, 1, 1, 0, [0u8; 32], 2),
            Err(ProgramError::Custom(6026))
        );
        drop(accounts);
    }
    assert!(
        band_data.is_empty(),
        "a refused publish must not create the band"
    );

    // 5: forecast
    let (forecast_key, _) = Pubkey::find_program_address(
        &[b"forecast", mint.as_ref(), &1_760_000_000i64.to_le_bytes()],
        program_id,
    );
    let forecast_key = Box::leak(Box::new(forecast_key));
    let forecast_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(intruder, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(owner)),
                program_id,
            ),
            satellite_account(forecast_key, false, true, &mut *forecast_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            log_forecast_at(
                program_id,
                &accounts,
                10,
                20,
                1_760_000_000,
                1,
                [1u8; 32],
                [2u8; 32],
                3,
                // The clock is the as-of: the time rule is not what this test is about.
                1_760_000_000,
            ),
            Err(ProgramError::Custom(6026))
        );
        drop(accounts);
    }
    assert!(
        forecast_data.is_empty(),
        "a refused log must not create the forecast"
    );

    // 6: score
    let (score_key, _) = Pubkey::find_program_address(&score_seeds(forecast_key), program_id);
    let score_key = Box::leak(Box::new(score_key));
    let score_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(intruder, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                forecast_key,
                false,
                false,
                leak_bytes(forecast_bytes_for(owner)),
                program_id,
            ),
            satellite_account(score_key, false, true, &mut *score_data, program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            score_forecast_at(program_id, &accounts, 150, 7, 9),
            Err(ProgramError::Custom(6026))
        );
        drop(accounts);
    }
    assert!(
        score_data.is_empty(),
        "a refused score must not create the score"
    );
}

#[test]
fn forecast_and_score_are_create_once() {
    // Immutability, not a race: an existing account is refused before the arguments can be
    // compared, and the bytes that are there stay there.
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let authority_key = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));
    let as_of = 1_760_000_000i64;
    let (forecast_key, _) = Pubkey::find_program_address(
        &[b"forecast", mint.as_ref(), &as_of.to_le_bytes()],
        program_id,
    );
    let forecast_key = Box::leak(Box::new(forecast_key));

    let existing = forecast_bytes_for(authority_key);
    let forecast_data = leak_bytes(existing.clone());
    {
        let accounts = vec![
            satellite_account(authority_key, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(authority_key)),
                program_id,
            ),
            satellite_account(forecast_key, false, true, &mut *forecast_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            log_forecast_at(
                program_id,
                &accounts,
                1,
                2,
                as_of,
                1,
                [1u8; 32],
                [2u8; 32],
                3,
                as_of,
            ),
            Err(ProgramError::Custom(6024))
        );
        drop(accounts);
    }
    assert_eq!(
        &forecast_data[..],
        &existing[..],
        "a refused log must not rewrite the forecast"
    );

    let (score_key, _) = Pubkey::find_program_address(&score_seeds(forecast_key), program_id);
    let score_key = Box::leak(Box::new(score_key));
    let existing_score = score_bytes_for(authority_key);
    let score_data = leak_bytes(existing_score.clone());
    {
        let accounts = vec![
            satellite_account(authority_key, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                forecast_key,
                false,
                false,
                leak_bytes(forecast_bytes_for(authority_key)),
                program_id,
            ),
            satellite_account(score_key, false, true, &mut *score_data, program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            score_forecast_at(program_id, &accounts, 150, 9, 10),
            Err(ProgramError::Custom(6025))
        );
        drop(accounts);
    }
    assert_eq!(
        &score_data[..],
        &existing_score[..],
        "a refused score must not rewrite the score"
    );
}

#[test]
fn low_above_high_is_refused_and_leaves_no_account() {
    // 6022 on both satellite writes, at the predicate and through the instruction. Equal
    // ends are a legal point interval; one lamport the other way is not.
    assert_eq!(validate_band(1, 1), Ok(()));
    assert_eq!(validate_band(0, u64::MAX), Ok(()));
    assert_eq!(validate_band(2, 1), Err(TicketpathError::BandUnsatisfiable));
    assert_eq!(validate_forecast(1, 1), Ok(()));
    assert_eq!(
        validate_forecast(2, 1),
        Err(TicketpathError::BandUnsatisfiable)
    );

    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let authority_key = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));

    let (band_key, _) = Pubkey::find_program_address(&band_seeds(mint), program_id);
    let band_key = Box::leak(Box::new(band_key));
    let band_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(authority_key, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(authority_key)),
                program_id,
            ),
            satellite_account(band_key, false, true, &mut *band_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            publish_band_at(program_id, &accounts, 2, 1, 0, 0, 0, [0u8; 32], 0),
            Err(ProgramError::Custom(6022))
        );
        drop(accounts);
    }
    assert!(band_data.is_empty(), "a refused band must not exist");

    let as_of = 1_760_000_000i64;
    let (forecast_key, _) = Pubkey::find_program_address(
        &[b"forecast", mint.as_ref(), &as_of.to_le_bytes()],
        program_id,
    );
    let forecast_key = Box::leak(Box::new(forecast_key));
    let forecast_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(authority_key, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(authority_key)),
                program_id,
            ),
            satellite_account(forecast_key, false, true, &mut *forecast_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            log_forecast_at(
                program_id,
                &accounts,
                2,
                1,
                as_of,
                0,
                [0u8; 32],
                [0u8; 32],
                0,
                as_of,
            ),
            Err(ProgramError::Custom(6022))
        );
        drop(accounts);
    }
    assert!(
        forecast_data.is_empty(),
        "a refused forecast must not exist"
    );

    // The legal point interval is written, so the test above is not passing because every
    // band is refused. A pre-existing head takes the rewrite branch, which needs no rent
    // sysvar on the host.
    let mut initial = Vec::new();
    band_for_write(1, 2, 3, 4, 5, 0, [0u8; 32], authority_key.to_bytes())
        .serialize(&mut initial)
        .unwrap();
    let band_data = leak_bytes(initial);
    let record_data = leak_bytes(record_bytes_for(authority_key));
    {
        let accounts = vec![
            satellite_account(authority_key, true, true, leak_bytes(vec![]), program_id),
            satellite_account(record_key, false, false, record_data, program_id),
            satellite_account(band_key, false, true, &mut *band_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            publish_band_at(program_id, &accounts, 5, 5, 1, 1, 0, [0u8; 32], 2),
            Ok(())
        );
        drop(accounts);
    }
    let point = Band::try_from_slice(band_data).unwrap();
    assert_eq!((point.low, point.high), (5, 5));
}

#[test]
fn a_refused_forecast_does_not_consume_the_pda() {
    // Two different refusals, both on an empty forecast account. The account is still empty
    // after each, which is the predicate ordering the live run relies on: a failed create
    // must not leave a zeroed PDA that a later call would read as an existing forecast.
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let owner = leak_pubkey();
    let intruder = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));
    let as_of = 1_760_000_000i64;
    let (forecast_key, _) = Pubkey::find_program_address(
        &[b"forecast", mint.as_ref(), &as_of.to_le_bytes()],
        program_id,
    );
    let forecast_key = Box::leak(Box::new(forecast_key));
    let forecast_data = leak_bytes(vec![]);

    {
        let accounts = vec![
            satellite_account(intruder, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(owner)),
                program_id,
            ),
            satellite_account(forecast_key, false, true, &mut *forecast_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            log_forecast_at(
                program_id,
                &accounts,
                10,
                20,
                as_of,
                1,
                [1u8; 32],
                [2u8; 32],
                3,
                as_of,
            ),
            Err(ProgramError::Custom(6026))
        );
        drop(accounts);
    }
    assert!(forecast_data.is_empty());

    {
        let accounts = vec![
            satellite_account(owner, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(owner)),
                program_id,
            ),
            satellite_account(forecast_key, false, true, &mut *forecast_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            log_forecast_at(
                program_id,
                &accounts,
                20,
                10,
                as_of,
                1,
                [1u8; 32],
                [2u8; 32],
                3,
                as_of,
            ),
            Err(ProgramError::Custom(6022))
        );
        drop(accounts);
    }
    assert!(
        forecast_data.is_empty(),
        "the PDA is still unclaimed after two refusals"
    );
}

#[test]
fn tags_four_five_and_six_take_their_documented_argument_bytes() {
    // The wire a client builds, byte by byte. Lengths are pinned; a field inserted in the
    // middle changes the length or the offsets and fails here.
    let mut band = vec![4u8];
    band.extend_from_slice(&10u64.to_le_bytes());
    band.extend_from_slice(&20u64.to_le_bytes());
    band.extend_from_slice(&30u64.to_le_bytes());
    band.extend_from_slice(&40u32.to_le_bytes());
    band.push(1);
    band.extend_from_slice(&[0xAAu8; 32]);
    assert_eq!(band.len(), 62, "1 tag byte + 61 argument bytes");
    match HookInstruction::unpack(&band).unwrap() {
        HookInstruction::PublishBand {
            low,
            high,
            as_of_slot,
            sample_n,
            refused,
            model_hash,
        } => {
            assert_eq!(
                (low, high, as_of_slot, sample_n, refused),
                (10, 20, 30, 40, 1)
            );
            assert_eq!(model_hash, [0xAAu8; 32]);
        }
        _ => panic!("tag 4 must unpack as PublishBand"),
    }
    assert!(matches!(
        HookInstruction::unpack(&band[..61]),
        Err(ProgramError::InvalidInstructionData)
    ));

    let mut forecast = vec![5u8];
    forecast.extend_from_slice(&10u64.to_le_bytes());
    forecast.extend_from_slice(&20u64.to_le_bytes());
    forecast.extend_from_slice(&(-7i64).to_le_bytes());
    forecast.extend_from_slice(&40u32.to_le_bytes());
    forecast.extend_from_slice(&[0xBBu8; 32]);
    forecast.extend_from_slice(&[0xCCu8; 32]);
    assert_eq!(forecast.len(), 93, "1 tag byte + 92 argument bytes");
    match HookInstruction::unpack(&forecast).unwrap() {
        HookInstruction::LogForecast {
            low,
            high,
            as_of_unix,
            sample_n,
            model_hash,
            scoring_rule_hash,
        } => {
            assert_eq!((low, high), (10, 20));
            assert_eq!(as_of_unix, -7, "the seed is a signed i64");
            assert_eq!(sample_n, 40);
            assert_eq!(model_hash, [0xBBu8; 32]);
            assert_eq!(scoring_rule_hash, [0xCCu8; 32]);
        }
        _ => panic!("tag 5 must unpack as LogForecast"),
    }
    assert!(matches!(
        HookInstruction::unpack(&forecast[..92]),
        Err(ProgramError::InvalidInstructionData)
    ));

    let mut score = vec![6u8];
    score.extend_from_slice(&1_000_000_000u64.to_le_bytes());
    score.extend_from_slice(&2_000_000u64.to_le_bytes());
    assert_eq!(score.len(), 17, "1 tag byte + 16 argument bytes");
    match HookInstruction::unpack(&score).unwrap() {
        HookInstruction::ScoreForecast {
            realised_lamports,
            interval_score_micro,
        } => {
            assert_eq!(realised_lamports, 1_000_000_000);
            assert_eq!(interval_score_micro, 2_000_000);
        }
        _ => panic!("tag 6 must unpack as ScoreForecast"),
    }
    assert!(matches!(
        HookInstruction::unpack(&score[..16]),
        Err(ProgramError::InvalidInstructionData)
    ));
}

// -- the review's refusals: authentication, one stage one sale, and the clock -----------
//
// Everything below was added after `records/findings/37-program-v2-review-fixes.md`. Each test
// names the predicate it bites: invert the predicate and this file says which test failed, which
// is the mutation the finding file records.

/// The three accounts tags 2 and 3 read, in order: `[authority (signer), record, mint]`.
fn record_write_accounts<'a>(
    authority: &'a Pubkey,
    authority_signs: bool,
    record_key: &'a Pubkey,
    record_data: &'a mut [u8],
    mint: &'a Pubkey,
    program_id: &'a Pubkey,
) -> Vec<AccountInfo<'a>> {
    vec![
        satellite_account(authority, authority_signs, false, leak_bytes(vec![]), program_id),
        satellite_account(record_key, false, true, record_data, program_id),
        satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
    ]
}

#[test]
fn tags_two_and_three_require_the_records_authority() {
    // The measured exploit, as a unit test: the record's authority signs and the write lands;
    // any other signer is refused 6026 and the bytes do not move. Before this check, tags 2 and
    // 3 asked only "is this account owned by this program", so the phase-1 buyer could stage a
    // price of 1 and then set status 0 on someone else's ticket.
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let owner = leak_pubkey();
    let intruder = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));

    // The authority's own write is admitted, and it is the price that is stored.
    let record_data = leak_bytes(record_bytes_for(owner));
    {
        let accounts = record_write_accounts(owner, true, record_key, &mut *record_data, mint, program_id);
        assert_eq!(set_pending_price(program_id, &accounts, 1_234_567_890), Ok(()));
        drop(accounts);
    }
    assert_eq!(
        TicketRecord::try_from_slice(record_data).unwrap().pending_price_lamports,
        1_234_567_890
    );

    // The intruder signs the same instruction. 6026, and not one byte changes.
    let before = record_data.to_vec();
    {
        let accounts = record_write_accounts(intruder, true, record_key, &mut *record_data, mint, program_id);
        assert_eq!(
            set_pending_price(program_id, &accounts, 1),
            Err(ProgramError::Custom(6026))
        );
        drop(accounts);
    }
    assert_eq!(&record_data[..], &before[..], "a refused stage must not write");

    let before = record_data.to_vec();
    {
        let accounts = record_write_accounts(intruder, true, record_key, &mut *record_data, mint, program_id);
        assert_eq!(
            set_status(program_id, &accounts, 0),
            Err(ProgramError::Custom(6026)),
            "a stranger must not be able to freeze a ticket with 6013 forever"
        );
        drop(accounts);
    }
    assert_eq!(&record_data[..], &before[..], "a refused status flip must not write");
    assert_eq!(
        TicketRecord::try_from_slice(record_data).unwrap().status,
        1,
        "the ticket is still transferable"
    );

    // The right key that did not sign is not the right key: no signature, no write.
    let before = record_data.to_vec();
    {
        let accounts = record_write_accounts(owner, false, record_key, &mut *record_data, mint, program_id);
        assert_eq!(
            set_status(program_id, &accounts, 0),
            Err(ProgramError::MissingRequiredSignature)
        );
        drop(accounts);
    }
    assert_eq!(&record_data[..], &before[..]);
}

#[test]
fn tags_two_and_three_refuse_an_account_that_is_not_the_record_for_the_mint() {
    // The address check, which is what makes the length check a second line and not the only
    // one. A 70-byte account that deserialises as a record, sitting at a satellite's address,
    // cannot be written by tags 2 or 3 because it is not `["record", mint]`.
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let other_mint = leak_pubkey();
    let owner = leak_pubkey();
    let (band_key, _) = Pubkey::find_program_address(&band_seeds(mint), program_id);
    let band_key = Box::leak(Box::new(band_key));

    let mut fake_record = record_bytes_for(owner);
    assert_eq!(fake_record.len(), TicketRecord::LEN, "the test's premise");
    let fake = leak_bytes(fake_record.clone());
    {
        let accounts = record_write_accounts(owner, true, band_key, &mut *fake, mint, program_id);
        assert_eq!(
            set_status(program_id, &accounts, 0),
            Err(ProgramError::Custom(6020)),
            "a record-shaped account at a non-record address is 6020, not a write"
        );
        drop(accounts);
    }
    assert_eq!(&fake[..], &fake_record[..]);

    // A 102-byte band handed to tag 3 at the record's own address is refused before Borsh reads
    // it: the length is compared to `TicketRecord::LEN` first.
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));
    let mut band_shaped = Vec::new();
    band_for_write(1, 2, 3, 4, 5, 0, [0u8; 32], [0u8; 32])
        .serialize(&mut band_shaped)
        .unwrap();
    assert_eq!(band_shaped.len(), Band::LEN);
    let wide = leak_bytes(band_shaped.clone());
    {
        let accounts = record_write_accounts(owner, true, record_key, &mut *wide, mint, program_id);
        assert_eq!(
            set_status(program_id, &accounts, 0),
            Err(ProgramError::InvalidAccountData)
        );
        drop(accounts);
    }
    assert_eq!(&wide[..], &band_shaped[..]);

    // And the record for a *different* mint is a different address, so it is 6020 as well.
    let record_data = leak_bytes(record_bytes_for(owner));
    {
        let accounts = record_write_accounts(owner, true, record_key, &mut *record_data, other_mint, program_id);
        assert_eq!(
            set_status(program_id, &accounts, 0),
            Err(ProgramError::Custom(6020))
        );
        drop(accounts);
    }
}

#[test]
fn the_hook_refuses_a_bulk_transfer_an_unstaged_transfer_and_a_disabled_ticket() {
    // 6008, 6009 and 6013 were declared, documented and never executed by any test: every
    // `execute(` call in this file passed `amount = 1` on a staged, transferable record. Each
    // refusal below returns before the clock is read, so all three are reachable on the host.
    let program_id = Pubkey::new_unique();
    let mint = Pubkey::new_unique();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(&mint), &program_id);
    let (metas_key, _) = Pubkey::find_program_address(&extra_metas_seeds(&mint), &program_id);

    // 6008: two tickets in one transfer is a bulk dump, refused before anything is read.
    let mut data = Vec::new();
    capped(1_000_000_000, 2500, 1_000_000_000)
        .serialize(&mut data)
        .unwrap();
    {
        let accounts = execute_accounts(&program_id, &mint, &record_key, &metas_key, &mut data, false);
        assert_eq!(
            execute(&program_id, &accounts, 2),
            Err(ProgramError::Custom(6008)),
            "a hook that admits amount > 1 admits a bulk dump"
        );
        drop(accounts);
    }

    // 6009: nothing staged, so this transfer is not a sale and the price has not been verified.
    let mut data = Vec::new();
    capped(1_000_000_000, 2500, 0).serialize(&mut data).unwrap();
    {
        let accounts = execute_accounts(&program_id, &mint, &record_key, &metas_key, &mut data, false);
        assert_eq!(
            execute(&program_id, &accounts, 1),
            Err(ProgramError::Custom(6009)),
            "an unstaged transfer must not be treated as a sale"
        );
        drop(accounts);
    }

    // 6013: the record says the ticket is not transferable, and it is checked before the price.
    let mut data = Vec::new();
    let mut disabled = capped(1_000_000_000, 2500, 1_000_000_000);
    disabled.status = 0;
    disabled.serialize(&mut data).unwrap();
    {
        let accounts = execute_accounts(&program_id, &mint, &record_key, &metas_key, &mut data, false);
        assert_eq!(
            execute(&program_id, &accounts, 1),
            Err(ProgramError::Custom(6013)),
            "status 0 must refuse the transfer, staged price or not"
        );
        drop(accounts);
    }
}

#[test]
fn an_admitted_transfer_clears_the_staged_price_so_one_stage_is_one_sale() {
    // The clear is a write inside `execute`'s writable branch, and that branch reads
    // `Clock::get`, which does not exist on the host: the write itself is proven by the live run
    // (proof `b` re-reads the record and finds `pending_price_lamports == 0` after an admitted
    // transfer). What can be pinned here is the code path and the consequence.
    let source = include_str!("lib.rs");
    assert!(
        source.contains("record.pending_price_lamports = 0;"),
        "an admitted transfer must consume the staging"
    );
    // Inside the writable branch, and before the clock write: both fields are written by one
    // serialisation, and a clear placed after the `else` would never run on the read-only path.
    let clear = source.find("record.pending_price_lamports = 0;").unwrap();
    let writable = source.find("if record_ai.is_writable {").unwrap();
    let clock = source
        .find("record.held_since_unix = Clock::get()?.unix_timestamp;")
        .unwrap();
    assert!(writable < clear && clear < clock, "the clear belongs in the writable branch");

    // The consequence: the guard that refuses 6009 is step 5 of `execute`, and the field it reads
    // is the one the clear zeroes. A record with nothing staged admits nothing.
    assert!(source.contains("if record.pending_price_lamports == 0 {"));
    let record = capped(1_000_000_000, 2500, 0);
    assert_eq!(record.pending_price_lamports, 0);
    assert_eq!(record.status, 1, "status 1 and nothing staged is the 6009 case");

    // Staging is what makes a sale admissible, once: the same price staged again admits again,
    // and that is the seller's next sale, not this one repeating.
    let mut staged = record;
    staged.pending_price_lamports = 900_000_000;
    assert_eq!(admit(&staged), Ok(Admission::Capped));
}

#[test]
fn a_forecast_cannot_be_backdated_beyond_the_tolerance() {
    // 6029. The clock is the only fact a create-once log can check, and it is checked one-sided:
    // a future as-of is a pre-registration, a past as-of beyond the tolerance is a claim that
    // the model already knew the answer.
    let now = 1_794_120_524i64;
    assert_eq!(
        validate_forecast_time(now - 301, now),
        Err(TicketpathError::ForecastBackdated)
    );
    assert_eq!(validate_forecast_time(now - 300, now), Ok(()));
    assert_eq!(validate_forecast_time(now, now), Ok(()));
    assert_eq!(validate_forecast_time(now + 60, now), Ok(()));
    assert_eq!(
        validate_forecast_time(1_760_000_000, now),
        Err(TicketpathError::ForecastBackdated),
        "the artefact's own as-of was 394.9 days before the write"
    );

    // Through the instruction: an empty forecast account is still empty afterwards, because the
    // refusal returns before `create_account`.
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let owner = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));
    let as_of = now - 31_536_000;
    let (forecast_key, _) = Pubkey::find_program_address(
        &[b"forecast", mint.as_ref(), &as_of.to_le_bytes()],
        program_id,
    );
    let forecast_key = Box::leak(Box::new(forecast_key));
    let forecast_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(owner, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(owner)),
                program_id,
            ),
            satellite_account(forecast_key, false, true, &mut *forecast_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            log_forecast_at(
                program_id, &accounts, 10, 20, as_of, 1, [1u8; 32], [2u8; 32], 3, now
            ),
            Err(ProgramError::Custom(6029))
        );
        drop(accounts);
    }
    assert!(forecast_data.is_empty(), "a refused log must not create the forecast");

    // A band too wide to score is refused at the same place, before any account exists.
    assert_eq!(validate_band_width(0, MAX_BAND_WIDTH_LAMPORTS), Ok(()));
    assert_eq!(
        validate_band_width(0, MAX_BAND_WIDTH_LAMPORTS + 1),
        Err(TicketpathError::BandTooWide)
    );
    assert!(
        (MAX_BAND_WIDTH_LAMPORTS as u128) * 1_000_000u128 <= u64::MAX as u128,
        "the widest band's width term must fit the score field"
    );
    assert!(
        ((MAX_BAND_WIDTH_LAMPORTS as u128) + 1) * 1_000_000u128 > u64::MAX as u128,
        "one lamport wider does not fit, which is why the bound is where it is"
    );
}

#[test]
fn a_forecast_too_wide_to_score_is_refused_at_log_time() {
    // 6031. The score field is a u64 and the rule multiplies by 1_000_000, so a band wider than
    // MAX_BAND_WIDTH_LAMPORTS can never have a score: `LogForecast` refuses it instead of writing
    // a forecast that nothing can ever grade. This is the other half of the domain the Python
    // rule states; a forecast that is loggable is always translatable into a score instruction.
    let now = 1_794_120_524i64;
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let owner = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));
    let as_of = now;
    let (wide_key, _) = Pubkey::find_program_address(
        &[b"forecast", mint.as_ref(), &as_of.to_le_bytes()],
        program_id,
    );
    let wide_key = Box::leak(Box::new(wide_key));
    let wide_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(owner, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                record_key,
                false,
                false,
                leak_bytes(record_bytes_for(owner)),
                program_id,
            ),
            satellite_account(wide_key, false, true, &mut *wide_data, program_id),
            satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            log_forecast_at(
                program_id,
                &accounts,
                0,
                MAX_BAND_WIDTH_LAMPORTS + 1,
                as_of,
                1,
                [1u8; 32],
                [2u8; 32],
                3,
                now
            ),
            Err(ProgramError::Custom(6031))
        );
        drop(accounts);
    }
    assert!(wide_data.is_empty(), "a refused log must not create the forecast");
}

#[test]
fn a_score_below_the_band_width_is_refused_and_a_covered_miss_is_recorded_as_zero() {
    // 6030 is the one bound the chain can check: the width term is the floor of the interval
    // score, so a smaller number is not a score under any reading of the rule. u64::MAX for a
    // [1, 2] band was accepted before this check; it is still accepted for a band whose width
    // is 1, because the chain cannot see an overstated error at all. That is the residual.
    let low = 900_000_000u64;
    let high = 1_100_000_000u64;
    let width_micro = 200_000_000_000_000u64;
    assert_eq!(validate_interval_score(low, high, width_micro), Ok(()));
    assert_eq!(
        validate_interval_score(low, high, width_micro - 1),
        Err(TicketpathError::ScoreBelowWidth)
    );
    assert_eq!(
        validate_interval_score(1, 2, u64::MAX),
        Ok(()),
        "the chain cannot detect an overstated error: u64::MAX for a width of 1 is stored"
    );

    // Through the instruction: an existing forecast, no score, an understated score.
    let program_id = leak_pubkey();
    let owner = leak_pubkey();
    let system = leak_pubkey();
    let forecast_key = leak_pubkey();
    let (score_key, _) = Pubkey::find_program_address(&score_seeds(forecast_key), program_id);
    let score_key = Box::leak(Box::new(score_key));
    let score_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(owner, true, true, leak_bytes(vec![]), program_id),
            satellite_account(
                forecast_key,
                false,
                false,
                leak_bytes(forecast_bytes_for(owner)),
                program_id,
            ),
            satellite_account(score_key, false, true, &mut *score_data, program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            score_forecast_at(program_id, &accounts, 1_000_000_000, 1, 9),
            Err(ProgramError::Custom(6030))
        );
        drop(accounts);
    }
    assert!(score_data.is_empty(), "a refused score must not create the score");

    // `Score::covers`' false branch, which no artefact had ever produced: a realised price one
    // lamport outside either end is not covered, and the flag is stored as 0 rather than 1.
    let forecast = forecast_for_write(
        [4u8; 32],
        100,
        200,
        1_760_000_000,
        7,
        [5u8; 32],
        [6u8; 32],
        88,
        [8u8; 32],
    );
    assert!(forecast.covers(100));
    assert!(forecast.covers(200));
    assert!(forecast.covers(150));
    assert!(!forecast.covers(99));
    assert!(!forecast.covers(201));
    let miss = Score {
        version: SATELLITE_VERSION,
        realised_lamports: 201,
        interval_score_micro: 10_100_000_000,
        covered: if forecast.covers(201) { 1 } else { 0 },
        scored_slot: 9,
        scorer: [8u8; 32],
    };
    let mut bytes = Vec::new();
    miss.serialize(&mut bytes).unwrap();
    assert_eq!(bytes[17], 0, "a miss must store covered = 0");
}

#[test]
fn a_band_with_no_observations_or_an_as_of_in_the_future_is_refused() {
    // 6032 and 6033, both on `PublishBand`. `sample_n = 0` with `refused = 0` is a number with
    // nothing behind it and no statement that it is a refusal; an `as_of_slot` above the slot the
    // write lands in is an estimate dated after the write that carried it.
    assert_eq!(
        validate_publish(10, 20, 3, 5, 0, 0),
        Err(TicketpathError::BandEmpty)
    );
    assert_eq!(validate_publish(10, 20, 3, 5, 0, 1), Ok(()));
    assert_eq!(validate_publish(10, 20, 3, 5, 1, 0), Ok(()));
    assert_eq!(
        validate_publish(10, 20, 6, 5, 1, 0),
        Err(TicketpathError::AsOfAhead)
    );
    assert_eq!(validate_publish(10, 20, 5, 5, 1, 0), Ok(()));
    // The band predicate still comes first: an inverted band is not a band at all.
    assert_eq!(
        validate_publish(20, 10, 6, 5, 0, 0),
        Err(TicketpathError::BandUnsatisfiable)
    );

    // `refused` is a flag, not a count: 7 is stored and logged as 1.
    assert_eq!(normalised_refused(7), 1);
    assert_eq!(normalised_refused(255), 1);
    assert_eq!(normalised_refused(0), 0);
    let normalised = band_for_write(10, 20, 3, 5, 4, 7, [0u8; 32], [0u8; 32]);
    assert_eq!(normalised.refused, 1);

    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let owner = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));
    let (band_key, _) = Pubkey::find_program_address(&band_seeds(mint), program_id);
    let band_key = Box::leak(Box::new(band_key));
    let mut initial = Vec::new();
    band_for_write(1, 2, 3, 4, 5, 0, [0u8; 32], owner.to_bytes())
        .serialize(&mut initial)
        .unwrap();
    let band_data = leak_bytes(initial.clone());

    for (args, expected) in [
        // (low, high, as_of_slot, sample_n, refused, published_slot)
        ((10u64, 20u64, 3u64, 0u32, 0u8, 5u64), 6032),
        ((10, 20, 6, 1, 0, 5), 6033),
    ] {
        let (low, high, as_of_slot, sample_n, refused, published_slot) = args;
        {
            let accounts = vec![
                satellite_account(owner, true, true, leak_bytes(vec![]), program_id),
                satellite_account(
                    record_key,
                    false,
                    false,
                    leak_bytes(record_bytes_for(owner)),
                    program_id,
                ),
                satellite_account(band_key, false, true, &mut *band_data, program_id),
                satellite_account(mint, false, false, leak_bytes(vec![]), program_id),
                satellite_account(system, false, false, leak_bytes(vec![]), program_id),
            ];
            assert_eq!(
                publish_band_at(
                    program_id,
                    &accounts,
                    low,
                    high,
                    as_of_slot,
                    sample_n,
                    refused,
                    [0u8; 32],
                    published_slot
                ),
                Err(ProgramError::Custom(expected))
            );
            drop(accounts);
        }
        assert_eq!(
            &band_data[..],
            &initial[..],
            "a refused publish must not change a band"
        );
    }
}

/// The 82-byte base `Mint` layout: `COption<Pubkey>` authority, supply, decimals, is_initialized,
/// freeze authority. Only the first 36 bytes are read by `mint_authority_of`, and Token-2022
/// appends extensions after the 82, which is why the base layout is the whole of the contract.
fn mint_bytes(authority: Option<&Pubkey>) -> Vec<u8> {
    let mut data = vec![0u8; 82];
    if let Some(key) = authority {
        data[0..4].copy_from_slice(&1u32.to_le_bytes());
        data[4..36].copy_from_slice(key.as_ref());
    }
    data
}

#[test]
fn the_record_needs_the_mints_authority_to_sign_its_creation() {
    // 6026 on tag 1. Before this check any keypair could create a record and become its
    // authority, fixing the cap, the floor and the policy for good. The positive path needs the
    // rent sysvar, so it is the live run that proves it; every refusal is here.
    let program_id = leak_pubkey();
    let mint = leak_pubkey();
    let issuer = leak_pubkey();
    let stranger = leak_pubkey();
    let system = leak_pubkey();
    let (record_key, _) = Pubkey::find_program_address(&record_seeds(mint), program_id);
    let record_key = Box::leak(Box::new(record_key));

    // The parser itself, on the layout the chain stores.
    let mint_data = leak_bytes(mint_bytes(Some(issuer)));
    {
        let account = satellite_account(mint, false, false, &mut *mint_data, program_id);
        assert_eq!(mint_authority_of(&account).unwrap(), Some(*issuer));
    }
    let mint_data = leak_bytes(mint_bytes(None));
    {
        let account = satellite_account(mint, false, false, &mut *mint_data, program_id);
        assert_eq!(mint_authority_of(&account).unwrap(), None);
    }
    let mut bad_tag = mint_bytes(Some(issuer));
    bad_tag[0..4].copy_from_slice(&2u32.to_le_bytes());
    let mut bad_tag = leak_bytes(bad_tag);
    {
        let account = satellite_account(mint, false, false, &mut *bad_tag, program_id);
        assert_eq!(
            mint_authority_of(&account),
            Err(ProgramError::InvalidAccountData),
            "a COption tag that is neither 0 nor 1 is not a mint this program reads"
        );
    }

    // A mint that names an authority, signed by someone else: 6026, and no record.
    let mint_data = leak_bytes(mint_bytes(Some(issuer)));
    let record_data = leak_bytes(vec![]);
    {
        let accounts = vec![
            satellite_account(stranger, true, true, leak_bytes(vec![]), program_id),
            satellite_account(mint, false, false, &mut *mint_data, program_id),
            satellite_account(record_key, false, true, &mut *record_data, program_id),
            satellite_account(stranger, true, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            initialize_record(program_id, &accounts, 1_000_000_000, 2500, 0, *b"ZZ", POLICY_CAPPED),
            Err(ProgramError::Custom(6026)),
            "a key that is not the mint's authority must not fix the policy"
        );
        drop(accounts);
    }
    assert!(record_data.is_empty(), "a refused create must leave no record");

    // The issuer's key, not signing: no signature, no record. The signer IS the mint authority
    // here, so this asserts the signature and not the key comparison.
    let mint_data = leak_bytes(mint_bytes(Some(issuer)));
    {
        let accounts = vec![
            satellite_account(issuer, true, true, leak_bytes(vec![]), program_id),
            satellite_account(mint, false, false, &mut *mint_data, program_id),
            satellite_account(record_key, false, true, leak_bytes(vec![]), program_id),
            satellite_account(issuer, false, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            initialize_record(program_id, &accounts, 1_000_000_000, 2500, 0, *b"ZZ", POLICY_CAPPED),
            Err(ProgramError::MissingRequiredSignature)
        );
        drop(accounts);
    }

    // A mint with no authority can authorise nobody: 6026, fail-closed.
    let mint_data = leak_bytes(mint_bytes(None));
    {
        let accounts = vec![
            satellite_account(issuer, true, true, leak_bytes(vec![]), program_id),
            satellite_account(mint, false, false, &mut *mint_data, program_id),
            satellite_account(record_key, false, true, leak_bytes(vec![]), program_id),
            satellite_account(issuer, true, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            initialize_record(program_id, &accounts, 1_000_000_000, 2500, 0, *b"ZZ", POLICY_CAPPED),
            Err(ProgramError::Custom(6026))
        );
        drop(accounts);
    }

    // An account shorter than a mint (82 bytes) is not a mint this program can read.
    let short = leak_bytes(vec![0u8; 81]);
    {
        let accounts = vec![
            satellite_account(issuer, true, true, leak_bytes(vec![]), program_id),
            satellite_account(mint, false, false, &mut *short, program_id),
            satellite_account(record_key, false, true, leak_bytes(vec![]), program_id),
            satellite_account(issuer, true, false, leak_bytes(vec![]), program_id),
            satellite_account(system, false, false, leak_bytes(vec![]), program_id),
        ];
        assert_eq!(
            initialize_record(program_id, &accounts, 1_000_000_000, 2500, 0, *b"ZZ", POLICY_CAPPED),
            Err(ProgramError::InvalidAccountData)
        );
        drop(accounts);
    }
}

#[test]
fn tag_zero_takes_no_argument_because_the_record_is_derived_from_the_mint() {
    // The argument was the defect: a create-once list naming a caller-supplied record could be
    // pointed at the wrong account once and refused every transfer with 6020 forever after. The
    // unpack now reads no bytes at all, so there is nothing to get wrong.
    match HookInstruction::unpack(&[0]).unwrap() {
        HookInstruction::InitializeExtraAccountMetaList => {}
        _ => panic!("tag 0 must unpack as InitializeExtraAccountMetaList"),
    }
    assert!(matches!(
        HookInstruction::unpack(&[]),
        Err(ProgramError::InvalidInstructionData)
    ));
    // The record the list names is the derived one, and this is the derivation `execute` uses.
    let program_id = Pubkey::new_unique();
    let mint = Pubkey::new_unique();
    let (record, _) = Pubkey::find_program_address(&record_seeds(&mint), &program_id);
    let meta = record_extra_meta(&record).unwrap();
    let resolved = meta.resolve(&[], &Pubkey::default(), |_| None).unwrap();
    assert_eq!(resolved.pubkey, record);
}

#[test]
fn the_monitored_log_line_names_the_face_so_the_ceiling_can_be_recomputed() {
    // A log line has no testable return value on the host, so the assertion is on the format
    // string that produces it. It fails if `face=` is dropped from the monitored branch, which
    // is the state the review found: the capped line carried the face and the monitored one did
    // not, so a monitored admission could not be checked against its own ceiling.
    let source = include_str!("lib.rs");
    assert!(
        source.contains("ticketpath: policy=monitored price={} face={} cap_bps={} band_low={} jurisdiction={}"),
        "the monitored line must carry the face, like the capped one"
    );
    assert!(source.contains("ticketpath: cap admitted price={} face={} cap_bps={}"));
}
