"""Region-aware caps: the resolver, the arithmetic, and the refusals.

Every expected value here is derived in the test from the inline table it builds, not copied
from `ticketpath/data/region-caps.json`. The shipped table is tested separately in
`tests/test_region_caps_table.py`, because a rule that is wrong in the resolver must fail even
if the shipped data happens to be right, and a row that is wrong must fail even if the resolver
is right.

The inline table is deliberately adversarial: an announced cap that must never bind, a
designated-events cap that must not bind unless the event says it is declared, a cap whose
commencement is in the future, a repealed cap, a fixed-amount cap that must not be approximated,
a jurisdiction with two instruments, and a subdivision that must beat its country.
"""

from __future__ import annotations

import copy
import json
import unittest

from ticketpath.core import region_caps as rc


def _instrument(jurisdiction, **over):
    row = {
        "jurisdiction": jurisdiction,
        "instrument_kind": "primary_legislation",
        "citation": f"Test Instrument ({jurisdiction})",
        "url": "https://example.invalid/instrument",
        "status": "in_force",
        "in_force_from": "2020-01-01",
        "in_force_to": None,
        "applies_to": "all_resale",
        "cap_basis": "pct_above_face",
        "cap_value": {"kind": "bps", "bps": 1000},
        "penalty": {"kind": "civil", "summary": "a fine", "max": "unlimited"},
        "enforcement_body": "the regulator",
        "quoted_provision": "no person shall resell for more than the permitted amount",
        "notes": "test row",
        "confidence": "A",
        "retrieved_at": "2026-11-08T00:00:00Z",
    }
    row.update(over)
    return row


def _table(entries=None, **over):
    raw = {
        "version": "2026-11-08.1",
        "compiled_at": "2026-11-08",
        "scope_note": "test table",
        "country_inheritance": True,
        "entries": copy.deepcopy(entries if entries is not None else _ENTRIES),
    }
    raw.update(over)
    return raw


_ENTRIES = {
    # A plain percentage cap.
    "AA": [_instrument("AA")],
    # Face value only, and only for events the state designates.
    "BB": [_instrument("BB", applies_to="designated_events", cap_basis="face", cap_value=None)],
    # Announced, not law. Must never bind.
    "CC": [
        _instrument(
            "CC",
            instrument_kind="announced_policy",
            status="announced",
            cap_value={"kind": "bps", "bps": 500},
            citation="Government announcement of a cap",
        )
    ],
    # In force, and establishes no price cap.
    "DD": [_instrument("DD", applies_to="all_resale", cap_basis="no_price_cap", cap_value=None)],
    # Face plus the fees the buyer paid.
    "EE": [_instrument("EE", cap_basis="face_plus_fees", cap_value=None)],
    # Face plus the fees paid, but the law counts at most 10% of face of them (the NSW shape).
    "LL": [
        _instrument(
            "LL",
            cap_basis="face_plus_fees_capped",
            cap_value={"kind": "fee_cap_bps", "bps": 1000},
        )
    ],
    # A fixed amount of money. Convertible, not enforceable through a bps field.
    "FF": [
        _instrument(
            "FF",
            cap_basis="absolute",
            cap_value={"kind": "minor_units", "amount": 5000, "currency": "EUR"},
        )
    ],
    # Two instruments: disclosure in force, a cap only announced.
    "GG": [
        _instrument("GG", applies_to="disclosure_only", cap_basis="no_price_cap", cap_value=None),
        _instrument("GG", instrument_kind="announced_policy", status="announced",
                    citation="Announced resale cap", cap_value={"kind": "bps", "bps": 1000}),
    ],
    # Not yet in force.
    "HH": [_instrument("HH", in_force_from="2030-01-01")],
    # Repealed.
    "II": [_instrument("II", status="repealed", in_force_to="2024-01-01")],
    # A loose cap over an all-in base (150% of face + fees) and a tighter one over the face
    # (110%). Basis points alone would pick the wrong one.
    "MM": [_instrument("MM", cap_basis="face_plus_fees", cap_value={"kind": "bps", "bps": 5000})],
    "NN": [_instrument("NN", cap_basis="face", cap_value={"kind": "bps", "bps": 1000})],
    # A country that caps, and a subdivision that caps harder.
    "AU": [_instrument("AU")],
    "AU-NSW": [_instrument("AU-NSW", cap_value={"kind": "bps", "bps": 500})],
    # An in-force price rule with no commencement date is not evidence of a cap.
    "JJ": [_instrument("JJ", cap_basis="face", cap_value=None)],
}


class TestResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = rc.validate_table(_table())

    def resolve(self, codes, **kw):
        return rc.resolve(codes, on_date=kw.pop("on_date", "2026-11-08"), table=self.table, **kw)

    def test_percentage_cap_binds(self):
        policy = self.resolve("AA")
        self.assertEqual(policy.kind, "capped")
        self.assertEqual(policy.cap_bps, 1000)
        self.assertEqual(policy.base, "face")
        self.assertEqual(policy.binding_jurisdiction, "AA")
        self.assertEqual(policy.reason, rc.REASON_LAW_CAPS)

    def test_a_designated_events_cap_needs_the_operator_to_say_which_it_is(self):
        # Three states, not two. Silence is not permission: an unheard-of designation
        # resolves to unresolved, and only an explicit "not designated" is monitored.
        silent = self.resolve("BB")
        self.assertEqual(silent.kind, "unresolved")
        self.assertEqual(silent.reason, rc.REASON_DESIGNATION_UNKNOWN)
        stated_no = self.resolve("BB", declared_event=False)
        self.assertEqual(stated_no.kind, "monitored")
        self.assertEqual(stated_no.reason, rc.REASON_NOT_DESIGNATED)
        declared = self.resolve("BB", declared_event=True)
        self.assertEqual(declared.kind, "capped")
        self.assertEqual(declared.cap_bps, 0)

    def test_announced_policy_never_binds(self):
        policy = self.resolve("CC")
        self.assertEqual(policy.kind, "monitored")
        self.assertIsNone(policy.cap_bps)
        self.assertEqual(policy.reason, rc.REASON_ANNOUNCED_ONLY)

    def test_law_with_no_price_cap_is_monitored_not_unresolved(self):
        policy = self.resolve("DD")
        self.assertEqual(policy.kind, "monitored")
        self.assertEqual(policy.reason, rc.REASON_NO_CAP)

    def test_face_plus_fees_is_a_zero_cap_over_the_all_in_base(self):
        policy = self.resolve("EE")
        self.assertEqual(policy.kind, "capped")
        self.assertEqual(policy.cap_bps, 0)
        self.assertEqual(policy.base, "face_plus_fees")
        base = rc.cap_base_lamports(100, 15, policy)
        self.assertEqual(base, 115)
        self.assertTrue(rc.admits(base, policy.cap_bps, 115))
        self.assertFalse(rc.admits(base, policy.cap_bps, 116))
        # No recorded fee: the base falls back to the face, which is stricter than the law,
        # never looser. The event record says whether the fee was known.
        self.assertEqual(rc.cap_base_lamports(100, None, policy), 100)

    def test_a_fee_pass_through_is_capped_at_the_statutory_share(self):
        # NSW: face + min(fees actually paid, 10% of face).
        policy = self.resolve("LL")
        self.assertEqual(policy.kind, "capped")
        self.assertEqual(policy.base, "face_plus_fees_capped")
        self.assertEqual(policy.fee_cap_bps, 1000)
        self.assertEqual(rc.cap_base_lamports(100, 4, policy), 104)    # fee under the limit
        self.assertEqual(rc.cap_base_lamports(100, 10, policy), 110)   # exactly at it
        self.assertEqual(rc.cap_base_lamports(100, 15, policy), 110)   # fee above it is not counted
        self.assertEqual(rc.cap_base_lamports(100, None, policy), 100) # unknown fee -> stricter
        self.assertEqual(rc.cap_base_lamports(1_000_000_003, 100_000_099, policy), 1_100_000_003)

    def test_absolute_amount_is_unresolved_rather_than_approximated(self):
        policy = self.resolve("FF")
        self.assertEqual(policy.kind, "unresolved")
        self.assertEqual(policy.reason, rc.REASON_ABSOLUTE_NEEDS_FX)

    def test_two_instruments_report_the_restriction_that_exists(self):
        policy = self.resolve("GG")
        self.assertEqual(policy.kind, "monitored")
        self.assertIn(policy.reason, {rc.REASON_OTHER_RESTRICTION, rc.REASON_ANNOUNCED_ONLY})
        # both instruments are in the audit trail, so a reader sees the disclosure duty too
        self.assertEqual(len(policy.basis), 2)

    def test_commencement_after_the_check_date_does_not_bind(self):
        self.assertEqual(self.resolve("HH").reason, rc.REASON_NOT_YET)
        self.assertEqual(self.resolve("HH", on_date="2030-01-01").kind, "capped")

    def test_repealed_does_not_bind(self):
        self.assertEqual(self.resolve("II").reason, rc.REASON_REPEALED)

    def test_unknown_jurisdiction_is_unresolved_not_monitored(self):
        policy = self.resolve("XX")
        self.assertEqual(policy.kind, "unresolved")
        self.assertEqual(policy.reason, rc.REASON_UNKNOWN_JURISDICTION)

    def test_empty_set_is_unresolved(self):
        self.assertEqual(self.resolve([]).kind, "unresolved")
        self.assertEqual(self.resolve("").kind, "unresolved")

    def test_strictest_wins_and_names_the_binding_member(self):
        policy = self.resolve(["DD", "AA"])
        self.assertEqual(policy.kind, "capped")
        self.assertEqual(policy.cap_bps, 1000)
        self.assertEqual(policy.binding_jurisdiction, "AA")
        both = self.resolve(["AA", "AU-NSW"])
        self.assertEqual(both.cap_bps, 500)
        self.assertEqual(both.binding_jurisdiction, "AU-NSW")

    def test_basis_points_are_never_compared_across_bases(self):
        # MM is +50% over face + fees; NN is +10% over face. A bps-only comparison picks MM
        # (5000 > 1000 is false, so it picks NN)... the real test is the reverse: a smaller
        # number over a looser base must not win.
        policy = self.resolve(["MM", "NN"])
        self.assertEqual(policy.binding_jurisdiction, "NN")
        self.assertEqual(policy.base, "face")
        # and a looser base with a smaller number: face_plus_fees at 0 vs face at 1000
        loose = self.resolve("EE")          # 0 bps over face + fees
        tight = self.resolve("AA")          # 1000 bps over face
        self.assertEqual(self.resolve(["EE", "AA"]).binding_jurisdiction, "EE")
        self.assertEqual(loose.cap_bps, 0)
        self.assertEqual(tight.cap_bps, 1000)

    def test_one_unresolved_member_makes_the_event_unresolved(self):
        policy = self.resolve(["AA", "XX"])
        self.assertEqual(policy.kind, "unresolved")
        self.assertEqual(policy.reason, rc.REASON_UNKNOWN_JURISDICTION)

    def test_subdivision_beats_its_country_and_inheritance_fills_the_gap(self):
        self.assertEqual(self.resolve("AU-NSW").cap_bps, 500)
        self.assertEqual(self.resolve("AU-VIC").cap_bps, 1000)
        self.assertEqual(self.resolve("AU-VIC").binding_jurisdiction, "AU")

    def test_codes_are_normalised(self):
        self.assertEqual(self.resolve("aa").cap_bps, 1000)
        self.assertEqual(self.resolve(" au-nsw ").cap_bps, 500)

    def test_resolution_is_deterministic_and_carries_the_table_identity(self):
        first = self.resolve("AA")
        second = self.resolve("AA")
        self.assertEqual(first, second)
        self.assertEqual(first.table_version, "2026-11-08.1")
        self.assertEqual(len(first.table_sha256), 64)

    def test_hash_does_not_depend_on_json_key_order(self):
        raw = _table()
        reordered = copy.deepcopy(raw)
        # rewrite the same content with the top-level keys in a different order
        reordered = {key: reordered[key] for key in reversed(list(reordered))}
        self.assertEqual(
            rc.validate_table(raw).sha256, rc.validate_table(reordered).sha256
        )

    def test_every_emitted_policy_has_a_machine_reason(self):
        for code in _ENTRIES:
            policy = self.resolve(code)
            self.assertIn(policy.kind, rc.POLICIES)
            self.assertTrue(policy.reason)
            self.assertFalse(policy.reason.startswith(" "), policy.reason)


class TestArithmetic(unittest.TestCase):
    def test_ceiling_and_boundary_are_the_on_chain_predicate(self):
        face, cap = 1_000_000_000, 2500
        self.assertEqual(rc.max_price_lamports(face, cap), 1_250_000_000)
        self.assertTrue(rc.admits(face, cap, 1_250_000_000))
        self.assertFalse(rc.admits(face, cap, 1_250_000_001))

    def test_zero_cap_admits_only_the_base(self):
        self.assertTrue(rc.admits(1_000_000_000, 0, 1_000_000_000))
        self.assertFalse(rc.admits(1_000_000_000, 0, 1_000_000_001))

    def test_admits_agrees_with_the_ceiling_for_every_price_either_side(self):
        for face in (1, 3, 999_999_937, 1_000_000_000, 2**40 + 7):
            for cap in (0, 1, 500, 2500, 3333, 10_000, 65_535):
                ceiling = rc.max_price_lamports(face, cap)
                self.assertTrue(rc.admits(face, cap, ceiling))
                self.assertFalse(rc.admits(face, cap, ceiling + 1))

    def test_u64_max_does_not_wrap_because_python_does_not(self):
        face = 2**64 - 1
        self.assertTrue(rc.admits(face, 10_000, 2**64 - 1))
        self.assertFalse(rc.admits(face, 0, face + 1))

    def test_float_is_refused_everywhere(self):
        with self.assertRaises(ValueError):
            rc.admits(100.0, 0, 100)
        with self.assertRaises(ValueError):
            rc.max_price_lamports(100, 0.5)
        with self.assertRaises(ValueError):
            rc.admits(100, True, 100)

    def test_cap_bps_outside_the_u16_field_is_refused(self):
        with self.assertRaises(ValueError):
            rc.max_price_lamports(100, 65_536)
        with self.assertRaises(ValueError):
            rc.admits(100, -1, 100)


class TestConversion(unittest.TestCase):
    FX = {
        "base": "EUR",
        "quote": "LAMPORTS",
        "num": 1_000_000,
        "den": 3,
        "source": "test fixture",
        "as_of": "2026-11-08T00:00:00Z",
    }

    def test_conversion_floors_and_never_rounds_up(self):
        # 5000 minor units * 1_000_000 / 3 = 1_666_666_666.67 -> floor
        self.assertEqual(rc.to_lamports(5000, self.FX), 1_666_666_666)
        # one lamport of rounding is the difference between lawful and a refusal
        self.assertLess(rc.to_lamports(5000, self.FX), 5000 * 1_000_000 / 3)

    def test_conversion_requires_a_stated_source_and_as_of(self):
        for missing in ("source", "as_of", "num", "den", "base", "quote"):
            fx = dict(self.FX)
            fx.pop(missing)
            with self.assertRaises(ValueError):
                rc.to_lamports(100, fx)

    def test_conversion_refuses_a_non_lamport_quote(self):
        fx = dict(self.FX, quote="EUR")
        with self.assertRaises(ValueError):
            rc.to_lamports(100, fx)

    def test_conversion_refuses_a_zero_or_negative_rate(self):
        with self.assertRaises(ValueError):
            rc.to_lamports(100, dict(self.FX, den=0))
        with self.assertRaises(ValueError):
            rc.to_lamports(0, self.FX)


class TestCompare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = rc.validate_table(_table())

    def policy(self, code, **kw):
        return rc.resolve(code, on_date=kw.pop("on_date", "2026-11-08"), table=self.table, **kw)

    def test_tightening_relaxing_and_unchanged(self):
        capped = self.policy("AA")                 # 1000
        tighter = self.policy("AU-NSW")            # 500
        monitored = self.policy("DD")
        announced = self.policy("CC")              # monitored, announced only
        self.assertEqual(rc.compare(capped, tighter), "tightened")
        self.assertEqual(rc.compare(tighter, capped), "relaxed")
        self.assertEqual(rc.compare(capped, capped), "unchanged")
        self.assertEqual(rc.compare(capped, monitored), "relaxed")
        self.assertEqual(rc.compare(monitored, capped), "tightened")
        self.assertEqual(rc.compare(monitored, announced), "unchanged")


class TestDescriptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = rc.validate_table(_table())

    def test_every_description_names_the_table_and_the_date(self):
        for code in _ENTRIES:
            policy = rc.resolve(code, on_date="2026-11-08", table=self.table)
            text = rc.describe(policy)
            self.assertIn("2026-11-08.1", text)
            self.assertIn("2026-11-08", text)
            self.assertIn(policy.kind.rsplit("ed", 1)[0], text)  # capped/monitored/unresolv

    def test_wire_shape_keeps_the_cap_null_unless_it_is_a_cap(self):
        capped = rc.resolve("AA", on_date="2026-11-08", table=self.table)
        monitored = rc.resolve("DD", on_date="2026-11-08", table=self.table)
        self.assertEqual(capped.as_dict()["resalePolicy"], "capped")
        self.assertEqual(capped.contract_cap(), 1000)
        self.assertEqual(monitored.as_dict()["resalePolicy"], "monitored")
        self.assertIsNone(monitored.contract_cap())
        self.assertIsNone(monitored.as_dict()["resaleCapBps"])


class TestTableValidation(unittest.TestCase):
    def test_a_missing_key_is_refused(self):
        raw = _table()
        del raw["entries"]["AA"][0]["penalty"]
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_an_unknown_key_is_refused(self):
        raw = _table()
        raw["entries"]["AA"][0]["invented"] = "x"
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_a_bad_code_is_refused(self):
        raw = _table()
        raw["entries"]["a1"] = [dict(raw["entries"]["AA"][0], jurisdiction="a1")]
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_a_row_must_agree_with_its_key(self):
        raw = _table()
        raw["entries"]["AA"][0]["jurisdiction"] = "BB"
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_a_fee_cap_must_carry_its_own_value_and_be_a_share(self):
        raw = _table()
        raw["entries"]["LL"][0]["cap_value"] = None
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)
        raw = _table()
        raw["entries"]["LL"][0]["cap_value"] = {"kind": "fee_cap_bps", "bps": 10_001}
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_bps_outside_the_field_is_refused(self):
        raw = _table()
        raw["entries"]["AA"][0]["cap_value"] = {"kind": "bps", "bps": 65_536}
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_cap_value_must_match_the_basis(self):
        # A face-based cap may carry a margin (Western Australia: 110% of face + booking fee),
        # so that combination is legal. What is not legal is a percentage cap with no number,
        # or a cap_value on a rule that establishes no cap at all.
        raw = _table()
        raw["entries"]["AA"][0]["cap_basis"] = "face"  # margin stays at 1000 bps
        table = rc.validate_table(raw)
        self.assertEqual(rc.resolve("AA", on_date="2026-11-08", table=table).cap_bps, 1000)
        raw = _table()
        raw["entries"]["AA"][0]["cap_basis"] = "pct_above_face"
        raw["entries"]["AA"][0]["cap_value"] = None
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)
        raw = _table()
        raw["entries"]["DD"][0]["cap_value"] = {"kind": "bps", "bps": 500}
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_a_price_rule_without_a_commencement_date_is_always_in_force(self):
        # Quebec's cap is in force and the instrument page gives no commencement day. `null`
        # means "treat as in force for every check date", not "not in force".
        raw = _table()
        raw["entries"]["AA"][0]["in_force_from"] = None
        table = rc.validate_table(raw)
        self.assertEqual(rc.resolve("AA", on_date="1990-01-01", table=table).kind, "capped")
        self.assertEqual(rc.resolve("AA", on_date="2099-01-01", table=table).kind, "capped")
        # but the row must say why it has no date
        raw["entries"]["AA"][0]["notes"] = ""
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_a_disclosure_rule_may_lack_a_commencement_date(self):
        raw = _table()
        raw["entries"]["GG"][0]["in_force_from"] = None
        rc.validate_table(raw)  # does not raise

    def test_an_empty_entry_list_is_refused(self):
        raw = _table()
        raw["entries"]["AA"] = []
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_a_bad_date_is_refused(self):
        raw = _table()
        raw["entries"]["AA"][0]["in_force_from"] = "2026-02-30"
        with self.assertRaises(rc.TableError):
            rc.validate_table(raw)

    def test_confidence_and_status_are_closed_sets(self):
        for field, value in (("confidence", "F"), ("status", "maybe"), ("applies_to", "sometimes")):
            raw = _table()
            raw["entries"]["AA"][0][field] = value
            with self.assertRaises(rc.TableError):
                rc.validate_table(raw)

    def test_a_bad_on_date_is_refused(self):
        table = rc.validate_table(_table())
        for value in ("2026-13-01", "yesterday", ""):
            with self.assertRaises(ValueError):
                rc.resolve("AA", on_date=value, table=table)


class TestShippedModuleSurface(unittest.TestCase):
    def test_constant_sets_are_the_ones_the_table_validator_uses(self):
        self.assertEqual(rc.POLICIES, ("capped", "monitored", "unresolved"))
        self.assertIn("announced_policy", rc.INSTRUMENT_KINDS)
        self.assertIn("designated_events", rc.APPLIES_TO)
        self.assertEqual(rc.U16_MAX, 65_535)

    def test_default_table_path_is_inside_the_package(self):
        self.assertTrue(str(rc.DEFAULT_TABLE_PATH).endswith("ticketpath/data/region-caps.json"))


class TestEffectiveCeiling(unittest.TestCase):
    """The law and the platform can cap in different bases; the chain holds one number."""

    @classmethod
    def setUpClass(cls):
        cls.table = rc.validate_table(_table())

    def law(self, code, **kw):
        return rc.resolve(code, on_date="2026-11-08", table=self.table, **kw)

    def test_the_law_wins_when_the_all_in_base_is_stricter(self):
        # face 1000 + fee 150, law caps at the total paid (0 bps over 1150) -> 1150.
        # A platform cap of +25% over the face would admit 1250, so the law binds.
        out = rc.effective_ceiling(
            face_lamports=1000, fee_lamports=150, law=self.law("EE"), platform_cap_bps=2500
        )
        self.assertEqual(out.binding_rule, "law")
        self.assertEqual(out.base_lamports, 1150)
        self.assertEqual(out.cap_bps, 0)
        self.assertEqual(out.ceiling_lamports, 1150)

    def test_the_platform_wins_when_its_own_cap_is_stricter(self):
        # law +10% over face = 1100; platform +5% = 1050 -> the platform binds.
        out = rc.effective_ceiling(face_lamports=1000, law=self.law("AA"), platform_cap_bps=500)
        self.assertEqual(out.binding_rule, "platform")
        self.assertEqual(out.base_lamports, 1000)
        self.assertEqual(out.cap_bps, 500)
        self.assertEqual(out.ceiling_lamports, 1050)

    def test_a_monitored_jurisdiction_still_gets_the_platform_ceiling(self):
        out = rc.effective_ceiling(face_lamports=1000, law=self.law("DD"), platform_cap_bps=2500)
        self.assertEqual(out.binding_rule, "platform")
        self.assertEqual(out.ceiling_lamports, 1250)

    def test_no_rule_means_no_ceiling(self):
        self.assertIsNone(
            rc.effective_ceiling(face_lamports=1000, law=self.law("DD"), platform_cap_bps=None)
        )

    def test_the_chain_ceiling_is_exactly_the_stricter_rule_s_ceiling(self):
        # The winner's own base and bps are carried, never re-derived, so the chain admits
        # exactly the ceiling the operator was told applied. A grid across awkward faces,
        # bases and caps, because a single friendly pair proves nothing.
        for face in (1, 7, 999, 1000, 1_000_000_003):
            for fee in (0, 3, 150):
                for platform in (0, 1, 2500, 3333, 10_000, 65_535):
                    law = self.law("EE" if fee else "AA")
                    out = rc.effective_ceiling(
                        face_lamports=face, fee_lamports=fee, law=law, platform_cap_bps=platform
                    )
                    if out is None:
                        continue
                    intended = min(
                        rc.max_price_lamports(
                            rc.cap_base_lamports(face, fee, law), law.cap_bps
                        ),
                        rc.max_price_lamports(face, platform),
                    )
                    self.assertEqual(out.ceiling_lamports, intended)
                    self.assertTrue(rc.admits(out.base_lamports, out.cap_bps, out.ceiling_lamports))
                    self.assertFalse(
                        rc.admits(out.base_lamports, out.cap_bps, out.ceiling_lamports + 1)
                    )

    def test_a_float_platform_cap_is_refused(self):
        with self.assertRaises(ValueError):
            rc.effective_ceiling(face_lamports=1000, law=self.law("DD"), platform_cap_bps=25.0)


if __name__ == "__main__":
    unittest.main()
