"""The shipped rules table: what it may and may not claim.

`tests/test_region_caps.py` proves the resolver against a table built to be adversarial. This
file proves the *data* the resolver actually reads, and it is written to fail when a row is
added that the resolver would enforce on weak evidence. The two rules it enforces hardest:

1. **A D- or E-grade row may never produce a cap.** A cap enforced on a secondary source, or on
   a page nobody read, is a legal claim the record cannot support.
2. **An unknown is never a permission.** `instrument_kind: none_identified` and `status:
   unknown` must resolve to `unresolved`; if one ever resolves to `monitored`, the engine is
   reporting "resale is unrestricted here" on the strength of not having looked.

The expected values below are copied from `records/findings/33-a-region-cap-law.md` §0, which is
where a change to the law is meant to land first. When the table changes, this file changes with
it, deliberately.
"""

from __future__ import annotations

import json
import unittest

from ticketpath.core import region_caps as rc

AS_OF = "2026-11-08"


class TestTableShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = rc.load_table()
        cls.raw = json.loads(rc.DEFAULT_TABLE_PATH.read_text())

    def test_version_and_hash_are_present_and_stable(self):
        self.assertRegex(self.table.version, rc.VERSION_RE)
        self.assertEqual(len(self.table.sha256), 64)
        self.assertEqual(rc.load_table().sha256, self.table.sha256)

    def test_every_citation_is_a_real_reference(self):
        for code, rows in self.table.entries.items():
            for row in rows:
                with self.subTest(code=code):
                    self.assertTrue(row.citation.strip(), f"{code} has no citation")
                    self.assertTrue(row.url == "" or row.url.startswith("https://"), f"{code}: {row.url}")
                    if row.status == "in_force":
                        self.assertTrue(row.url, f"{code} cites an in-force instrument but no URL")
                        self.assertTrue(
                            row.quoted_provision.strip(),
                            f"{code} cites an in-force instrument but quotes nothing",
                        )

    def test_no_duplicate_instrument_in_a_jurisdiction(self):
        for code, rows in self.table.entries.items():
            citations = [row.citation for row in rows]
            self.assertEqual(len(citations), len(set(citations)), f"{code} repeats an instrument")

    def test_scope_note_says_what_the_table_is_not(self):
        self.assertIn("legal advice", self.table.scope_note.lower())
        self.assertIn("not a complete survey", self.table.scope_note.lower())


class TestNoWeakEvidenceIsEnforced(unittest.TestCase):
    def setUp(self):
        self.table = rc.load_table()

    def test_no_cap_is_enforced_on_a_d_or_e_row(self):
        offenders = []
        for code, rows in self.table.entries.items():
            for row in rows:
                if row.confidence in ("D", "E"):
                    policy = rc.resolve(code, on_date=AS_OF, table=self.table, declared_event=True)
                    if policy.kind == "capped" and row.jurisdiction in [
                        b.jurisdiction for b in policy.basis
                    ]:
                        # only an offence when the weak row is the one that produced the cap
                        if policy.binding_jurisdiction == row.jurisdiction:
                            offenders.append(f"{code}: {row.citation[:60]} ({row.confidence})")
        self.assertEqual(offenders, [], f"caps enforced on weak evidence: {offenders}")

    def test_none_identified_never_resolves_to_monitored(self):
        codes = [
            code
            for code, rows in self.table.entries.items()
            if all(row.instrument_kind == "none_identified" for row in rows)
        ]
        self.assertTrue(codes, "the table should record the jurisdictions nobody read")
        for code in codes:
            with self.subTest(code=code):
                self.assertEqual(rc.resolve(code, on_date=AS_OF, table=self.table).kind, "unresolved")

    def test_an_announced_instrument_never_binds(self):
        announced = [
            (code, row)
            for code, rows in self.table.entries.items()
            for row in rows
            if row.instrument_kind == "announced_policy" or row.status == "announced"
        ]
        self.assertTrue(announced, "the UK announcement should be in the table")
        for code, _row in announced:
            with self.subTest(code=code):
                policy = rc.resolve(code, on_date=AS_OF, table=self.table, declared_event=True)
                self.assertNotEqual(policy.kind, "capped")


class TestTheRowsTheReportClaims(unittest.TestCase):
    """One assertion per row that changes what the engine does, copied from the finding."""

    def setUp(self):
        self.table = rc.load_table()

    def resolve(self, code, **kw):
        return rc.resolve(code, on_date=kw.pop("on_date", AS_OF), table=self.table, **kw)

    # -- capped ---------------------------------------------------------------------------
    def test_ireland_caps_face_plus_fees_for_declared_events_only(self):
        silent = self.resolve("IE")
        self.assertEqual(silent.kind, "unresolved")
        self.assertEqual(silent.reason, rc.REASON_DESIGNATION_UNKNOWN)
        stated_no = self.resolve("IE", declared_event=False)
        self.assertEqual(stated_no.kind, "monitored")
        self.assertEqual(stated_no.reason, rc.REASON_NOT_DESIGNATED)
        declared = self.resolve("IE", declared_event=True)
        self.assertEqual(declared.kind, "capped")
        self.assertEqual((declared.cap_bps, declared.base), (0, "face_plus_fees"))

    def test_ontario_caps_the_all_in_price_from_april_2026(self):
        before = self.resolve("CA-ON", on_date="2026-04-23")
        after = self.resolve("CA-ON", on_date="2026-04-24")
        self.assertNotEqual(before.kind, "capped")
        self.assertEqual(after.kind, "capped")
        self.assertEqual((after.cap_bps, after.base), (0, "face_plus_fees"))

    def test_quebec_caps_at_the_announced_price(self):
        policy = self.resolve("CA-QC")
        self.assertEqual(policy.kind, "capped")
        self.assertEqual((policy.cap_bps, policy.base), (0, "face"))

    def test_new_south_wales_is_not_a_flat_ten_percent(self):
        policy = self.resolve("AU-NSW")
        self.assertEqual(policy.kind, "capped")
        self.assertEqual(policy.base, "face_plus_fees_capped")
        self.assertEqual(policy.cap_bps, 0)
        self.assertEqual(policy.fee_cap_bps, 1000)
        # face 100, fees 4 -> 104; fees 15 -> 110 (the statute counts at most 10% of face)
        self.assertEqual(rc.cap_base_lamports(100, 4, policy), 104)
        self.assertEqual(rc.cap_base_lamports(100, 15, policy), 110)
        self.assertEqual(rc.cap_base_lamports(100, None, policy), 100)

    def test_south_australia_and_victoria_cap_ten_percent_over_face(self):
        for code in ("AU-SA", "AU-VIC"):
            with self.subTest(code=code):
                policy = self.resolve(code, declared_event=True)
                self.assertEqual(policy.kind, "capped")
                self.assertEqual(policy.base, "face")
                self.assertEqual(policy.cap_bps, 1000)

    def test_victoria_needs_a_declared_event(self):
        self.assertNotEqual(self.resolve("AU-VIC").kind, "capped")

    def test_western_australia_caps_ten_percent_over_face_plus_the_booking_fee(self):
        policy = self.resolve("AU-WA")
        self.assertEqual(policy.kind, "capped")
        self.assertEqual(policy.base, "face_plus_fees")
        self.assertEqual(policy.cap_bps, 1000)

    # -- not capped -----------------------------------------------------------------------
    def test_the_united_kingdom_is_no_cap_and_the_nations_inherit_that_finding(self):
        # The UK row is an all-resale finding of no price cap, so the three nations inherit it;
        # the announced cap is in the audit trail and never binds.
        for code in ("GB", "GB-EAW", "GB-SCT", "GB-NIR"):
            with self.subTest(code=code):
                policy = self.resolve(code)
                self.assertEqual(policy.kind, "monitored")
                self.assertEqual(policy.reason, rc.REASON_NO_CAP)
                self.assertIn("announced", " ".join(r.instrument_kind for r in policy.basis))

    def test_a_sectoral_federal_rule_does_not_answer_a_state_s_price_question(self):
        # US-OH has no row of its own. The federal rows are a bot ban and a disclosure duty;
        # before the fix, inheriting them reported "no cap in force" in a state nobody read.
        policy = self.resolve("US-OH")
        self.assertEqual(policy.kind, "unresolved")
        self.assertIsNone(policy.binding_jurisdiction)
        # and every state code in the table either has its own row or is unresolved
        for code in sorted(self.table.entries):
            if code.startswith("US-") and code != "US-NY":
                with self.subTest(code=code):
                    self.assertNotIn(
                        self.resolve(code).reason, {rc.REASON_OTHER_RESTRICTION}
                    )

    def test_british_columbia_and_California_establish_no_cap(self):
        for code in ("CA-BC", "US-CA"):
            with self.subTest(code=code):
                policy = self.resolve(code)
                self.assertEqual(policy.kind, "monitored")
                self.assertEqual(policy.reason, rc.REASON_NO_CAP)

    def test_belgium_caps_at_zero_markup_over_the_definitive_price(self):
        policy = self.resolve("BE")
        self.assertEqual(policy.kind, "capped")
        self.assertEqual((policy.cap_bps, policy.base), (0, "face_plus_fees"))

    def test_spain_caps_but_only_for_licensed_outlets_so_it_is_unresolved(self):
        # 20% above the box office, art. 67.1; whether a platform is a licensed outlet is not
        # knowable from here, so the row is `unknown` coverage and makes no claim.
        self.assertEqual(self.resolve("ES").kind, "unresolved")

    def test_france_and_italy_regulate_the_channel_not_the_price(self):
        for code in ("FR", "IT"):
            with self.subTest(code=code):
                policy = self.resolve(code)
                self.assertEqual(policy.kind, "monitored")
                self.assertEqual(policy.reason, rc.REASON_NO_CAP)

    def test_massachusetts_is_unresolved_because_only_one_section_was_read(self):
        # The cluster read ch. 140 s. 185A and says so; a licence regime in one section is not a
        # survey of the chapter, so "no cap in Massachusetts" would be a finding nobody made.
        self.assertEqual(self.resolve("US-MA").kind, "unresolved")

    def test_the_federal_rules_are_disclosure_and_bots_only(self):
        for code in ("US", "CA", "AU"):
            with self.subTest(code=code):
                self.assertNotEqual(self.resolve(code).kind, "capped")

    # -- unresolved -----------------------------------------------------------------------
    def test_new_york_and_florida_are_unresolved_not_capped(self):
        ny = self.resolve("US-NY")
        self.assertEqual(ny.kind, "unresolved")   # who the ceiling binds is unsettled
        # the DEFAULT path, with no declared-event flag: Florida's four categories are
        # statutory transaction classes, not a ministerial list, so the flag must not matter
        for declared in (False, True):
            with self.subTest(declared=declared):
                fl = self.resolve("US-FL", declared_event=declared)
                self.assertEqual(fl.kind, "unresolved")
                self.assertEqual(fl.reason, rc.REASON_ABSOLUTE_NEEDS_FX)

    def test_queensland_exists_but_was_not_read(self):
        # An unread cap must not read as permission: this holds with and without the flag.
        for declared in (False, True):
            with self.subTest(declared=declared):
                self.assertEqual(self.resolve("AU-QLD", declared_event=declared).kind, "unresolved")

    def test_the_table_is_the_size_the_report_claims(self):
        # The finding's §0 quotes these numbers; a test makes the sentence checkable.
        self.assertEqual(len(self.table.entries), 82)
        self.assertEqual(sum(len(rows) for rows in self.table.entries.values()), 84)

    def test_unread_jurisdictions_are_unresolved(self):
        for code in ("US-TX", "CA-AB", "PT", "DE", "GR", "AU-TAS", "ZZ"):
            with self.subTest(code=code):
                self.assertEqual(self.resolve(code).kind, "unresolved")


class TestMultiVenueOnTheRealTable(unittest.TestCase):
    def setUp(self):
        self.table = rc.load_table()

    def test_a_tour_is_capped_by_its_strictest_stop(self):
        policy = rc.resolve(
            ["GB", "IE", "CA-ON"], on_date=AS_OF, table=self.table, declared_event=True
        )
        self.assertEqual(policy.kind, "capped")
        self.assertIn(policy.binding_jurisdiction, {"IE", "CA-ON"})

    def test_one_unread_stop_makes_the_tour_unresolved(self):
        policy = rc.resolve(["CA-ON", "US-TX"], on_date=AS_OF, table=self.table)
        self.assertEqual(policy.kind, "unresolved")

    def test_face_only_beats_an_all_in_base_at_the_same_margin(self):
        # WA is +10% over face + fees, VIC is +10% over face. Same number, different base:
        # the face-only rule is the stricter one and must be the one reported.
        policy = rc.resolve(["AU-WA", "AU-VIC"], on_date=AS_OF, table=self.table, declared_event=True)
        self.assertEqual(policy.binding_jurisdiction, "AU-VIC")


if __name__ == "__main__":
    unittest.main()
