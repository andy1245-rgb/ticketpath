"""The event's additive jurisdiction keys, on the real fixture rows.

`lib/types.ts` has no jurisdiction field and this repository does not edit the frontend, so
the field is served as an additive key beside the contract's own (`tests/test_contract_conformance.py`
declares them). Two properties matter and are tested here:

1. The keys are **derived per request** from the event row's `jurisdiction` and `startsAt`;
   nothing is stored twice.
2. `Event.resalePriceCapBps` keeps its meaning — the organiser's configured cap — and the
   number the chain would actually hold is `enforcedCap.enforcedCapBps`. They differ exactly
   when a law is stricter, and the test proves the difference exists rather than assuming it.
"""

from __future__ import annotations

import unittest

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.core import event_records, region_caps


def _rows():
    adapter = LedgerAdapter.from_fixture()
    event = adapter._events[0]
    organizer = adapter._organizers[event["organizerId"]]
    return event, organizer


class TestAdditiveKeys(unittest.TestCase):
    def setUp(self):
        self.event, self.organizer = _rows()

    def build(self, **over):
        return event_records.build({**self.event, **over}, self.organizer)

    def test_every_event_in_the_fixture_declares_ontario(self):
        self.assertEqual(self.event["jurisdiction"], "CA-ON")

    def test_the_keys_are_present_even_when_unknown(self):
        event = dict(self.event)
        event.pop("jurisdiction")
        payload = event_records.build(event, self.organizer)
        for key in (
            "jurisdiction",
            "resalePolicy",
            "resalePolicyReason",
            "lawTableVersion",
            "lawAsOf",
            "lawBasis",
            "enforcedCap",
        ):
            self.assertIn(key, payload)
        self.assertIsNone(payload["jurisdiction"])
        self.assertIsNone(payload["resalePolicy"])
        self.assertEqual(payload["lawBasis"], [])
        self.assertIsNone(payload["enforcedCap"])

    def test_ontario_caps_a_2026_12_event_and_the_law_is_stricter_than_the_platform(self):
        payload = self.build()
        self.assertEqual(payload["jurisdiction"], "CA-ON")
        self.assertEqual(payload["resalePolicy"], "capped")
        self.assertEqual(payload["resalePolicyReason"], region_caps.REASON_LAW_CAPS)
        self.assertEqual(payload["lawTableVersion"], region_caps.load_table().version)
        # the organiser's own configured cap is still what the contract field says
        self.assertEqual(payload["resalePriceCapBps"], self.event["resalePriceCapBps"])
        # The ceiling is per tier, because a cap is a multiple of the ticket's own face; an
        # event-wide number would be wrong by the tier ratio, so `enforcedCap` is null here
        # and the per-tier list is the honest shape.
        self.assertIsNone(payload["enforcedCap"])
        self.assertEqual(len(payload["enforcedCapByTier"]), len(self.event["tiers"]))
        faces = {tier["id"]: tier["faceValueLamports"] for tier in self.event["tiers"]}
        for row in payload["enforcedCapByTier"]:
            with self.subTest(tier=row["tierId"]):
                self.assertEqual(row["bindingRule"], "law")
                self.assertEqual(row["enforcedCapBps"], 0)
                self.assertEqual(row["enforcedBaseLamports"], faces[row["tierId"]])
                self.assertEqual(row["enforcedCeilingLamports"], row["enforcedBaseLamports"])
                self.assertEqual(row["platformCapBps"], self.event["resalePriceCapBps"])

    def test_a_single_ceiling_is_emitted_only_when_every_tier_agrees(self):
        event = dict(self.event)
        event["tiers"] = [
            {**tier, "faceValueLamports": 1_000_000_000} for tier in self.event["tiers"]
        ]
        payload = event_records.build(event, self.organizer)
        self.assertIsNotNone(payload["enforcedCap"])
        self.assertEqual(payload["enforcedCap"]["enforcedBaseLamports"], 1_000_000_000)
        self.assertEqual(len(payload["enforcedCapByTier"]), len(event["tiers"]))

    def test_a_platform_cap_can_be_the_one_that_binds(self):
        # a monitored jurisdiction with a configured platform cap: the ceiling is the product's
        payload = self.build(jurisdiction="GB", resalePriceCapBps=1000)
        self.assertEqual(payload["resalePolicy"], "monitored")
        for row in payload["enforcedCapByTier"]:
            self.assertEqual(row["bindingRule"], "platform")
            self.assertEqual(row["enforcedCapBps"], 1000)

    def test_no_configured_cap_and_no_law_means_no_ceiling(self):
        payload = self.build(jurisdiction="GB", resalePriceCapBps=None)
        self.assertEqual(payload["resalePolicy"], "monitored")
        self.assertIsNone(payload["enforcedCap"])

    def test_a_policy_without_a_cap_never_renders_a_bound_of_its_own(self):
        # The rule a screen depends on: a number under `enforcedCap…` is either the law's or the
        # platform's, and `bindingRule` names which. `monitored` and `unresolved` may carry the
        # platform's own number and nothing else; with no platform cap they may carry no number at
        # all. Swept over every code in the table because a table edit is where this would break,
        # and no single example would notice. One tier, so `enforcedCap` is emitted and compared
        # with the per-tier row instead of being null.
        event = {**self.event, "tiers": [self.event["tiers"][0]]}
        face = event["tiers"][0]["faceValueLamports"]
        seen = {"capped": 0, "monitored": 0, "unresolved": 0}
        for code in sorted(region_caps.jurisdictions()):
            for platform in (None, 2500):
                with self.subTest(jurisdiction=code, platformCapBps=platform):
                    payload = event_records.build(
                        {**event, "jurisdiction": code, "resalePriceCapBps": platform},
                        self.organizer,
                    )
                    policy = payload["resalePolicy"]
                    seen[policy] += 1
                    (row,) = payload["enforcedCapByTier"]
                    if policy == "capped":
                        # the law or the platform capped it; either way a number belongs here
                        self.assertIn("enforcedCapBps", row)
                        self.assertIn(row["bindingRule"], ("law", "platform"))
                        self.assertEqual(payload["enforcedCap"]["enforcedCapBps"], row["enforcedCapBps"])
                        continue
                    if platform is None:
                        # nothing to enforce, so nothing to show: a zero here would read as a cap
                        # at face value that nobody set and no law imposes
                        self.assertNotIn("enforcedCapBps", row)
                        self.assertIsNone(payload["enforcedCap"])
                        continue
                    # the platform's own cap, carried unchanged and attributed to the platform
                    self.assertEqual(row["bindingRule"], "platform")
                    self.assertEqual(row["enforcedCapBps"], platform)
                    self.assertEqual(row["platformCapBps"], platform)
                    self.assertEqual(row["enforcedBaseLamports"], face)
                    self.assertEqual(row["enforcedCeilingLamports"], face * (10_000 + platform) // 10_000)
        # a sweep that only reached one outcome would have proved nothing about the other two
        self.assertTrue(all(seen.values()), seen)

    def test_an_irish_event_needs_the_operator_to_state_the_designation(self):
        # Silence is not permission: Ireland's cap applies to designated events, the register
        # is not machine-readable here, and an event nobody has classified is unresolved.
        self.assertEqual(self.build(jurisdiction="IE")["resalePolicy"], "unresolved")
        self.assertEqual(
            self.build(jurisdiction="IE", declaredEvent=False)["resalePolicy"], "monitored"
        )
        self.assertEqual(
            self.build(jurisdiction="IE", declaredEvent=True)["resalePolicy"], "capped"
        )

    def test_an_unread_jurisdiction_is_unresolved_and_carries_the_reason(self):
        payload = self.build(jurisdiction="US-TX")
        self.assertEqual(payload["resalePolicy"], "unresolved")
        self.assertEqual(payload["resalePolicyReason"], region_caps.REASON_NO_INSTRUMENT)
        # an unresolved law still lets the organiser's own cap bind, and says which rule it was
        for row in payload["enforcedCapByTier"]:
            self.assertEqual(row["bindingRule"], "platform")

    def test_the_law_basis_is_a_citation_a_reader_can_follow(self):
        payload = self.build()
        self.assertTrue(payload["lawBasis"])
        row = payload["lawBasis"][0]
        self.assertEqual(row["jurisdiction"], "CA-ON")
        self.assertTrue(row["url"].startswith("https://"))
        self.assertIn("Ticket Sales Act", row["citation"])
        self.assertIn(row["confidence"], ("A", "B", "C", "D", "E"))

    def test_the_resolution_uses_the_event_start_date_not_today(self):
        # The same row before and after Ontario's 2026-04-24 commencement must differ, and
        # nothing about the machine's clock may change that.
        before = self.build(startsAt="2026-04-23T00:30:00.000Z")
        after = self.build(startsAt="2026-04-24T00:30:00.000Z")
        self.assertNotEqual(before["resalePolicy"], "capped")
        self.assertEqual(after["resalePolicy"], "capped")

    def test_an_unparseable_start_date_yields_no_policy_rather_than_a_guess(self):
        payload = self.build(startsAt="")
        self.assertIsNone(payload["resalePolicy"])
        self.assertIsNone(payload["resalePolicyReason"])
        self.assertIsNone(payload["enforcedCap"])


if __name__ == "__main__":
    unittest.main()
