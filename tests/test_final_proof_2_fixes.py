"""FINAL-PROOF-2, C1/C2/C3: the console against its own counts, its own cap and its own clock.

The proof run swept 64 required page states and 724 in all, and found three contradictions and
a checker that certified one of them. This file pins the repairs at the property, not at the
sentence:

* C1, the market block printed `0 sales of 0 on this event` while the same sentence named 9
  excluded rows and the store held 12. The first count is what enters the decision; the second
  is the record's, and the mode's exclusion is said in words.
* C2, the prior band reached 1.26 SOL on a page whose own [EXACT] line stated a ceiling of
  0.84 SOL. The band printed is now cut at the lowest ceiling the page states, the cut is said
  with its source, and the declared prior's own extent is printed beside it. The engine's own
  number is unchanged: only the interval the page calls `the band` is cut.
* C3, the band-stop sentence called the record's ceiling `the ceiling the cap in force puts on
  this tier` whenever the typed cap was the higher of the two. It now names the cap that
  produced the number it prints.

Every test asserts its premise first, so none of them can pass by the fixture having changed.
"""

from __future__ import annotations

import datetime as dt
import html as html_module
import json
import os
import re
import unittest

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.orchestrator import Orchestrator

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "synthetic_store.json")

EVENTS = (
    "evt_syn_01",
    "evt_syn_02",
    "evt_syn_03",
    "evt_syn_04",
    "evt_syn_05",
    "evt_syn_06",
    "evt_syn_07",
    "evt_syn_08",
)
# The four cap states the proof swept, plus the grid points where a band is trimmed.
CAPS = (None, "0", "298", "1000", "1500", "1700", "2500", "3500", "5000", "10000")
MODES = ("counterfactual", "before_on_sale")

RECOMMENDATION_BAND = re.compile(r"Band ([\d.]+) \u2013 ([\d.]+) SOL")
PRIOR_BAND = re.compile(
    r"prior band around face: \[UNVALIDATED\] ([\d.]+) SOL \u2013 \[UNVALIDATED\] ([\d.]+) SOL"
)
BAND_STOPS = re.compile(r"The top of that band is the ceiling the cap in force puts on this tier, at")
BAND_STOPS_RECORDED = re.compile(
    r"The top of that band is the ceiling the recorded cap of \[FIXTURE\] \d+ bps puts on this tier"
)
# Every ceiling the page can print, as (pattern, is_in_lamports).
CEILINGS = (
    # the [EXACT] line under the prior band
    (re.compile(r"That is exactly ([\d.]+) SOL\."), False),
    # the refusal's statement of the ceiling in force
    (re.compile(r"puts the resale ceiling at ([\d,]+) lamports"), True),
    # the sentence that says where the value band stops, on either cap
    (re.compile(r"puts on this tier, at \[EXACT\] ([\d.]+) SOL"), False),
    # the sentence that says which ceiling cut the prior band
    (re.compile(r"cut at the ceiling of \[EXACT\] ([\d.]+) SOL"), False),
)


def printed_ceilings(text: str) -> list[float]:
    """Every ceiling the page states, in SOL, from the sentences that state one."""
    out: list[float] = []
    for pattern, lamports in CEILINGS:
        for match in pattern.finditer(text):
            number = float(match.group(1).replace(",", ""))
            out.append(number / 1e9 if lamports else number)
    return out


def orchestrator() -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
    )


def page_for(**query) -> tuple[str, dict]:
    payload = orchestrator().price_guidance(**query)
    payload["canonicalUrl"] = "http://127.0.0.1:8788/?"
    return page.render(payload), payload


def visible(html: str) -> str:
    """The page as text: tags stripped, whitespace collapsed, and no space before punctuation.

    A badge is its own span, so stripping tags leaves `SOL .` where the page reads `SOL.`;
    the spacing is the rendering's, not the sentence's, and every assertion here is about the
    sentence.
    """
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    text = re.sub(r"\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", without_style)))
    return re.sub(r"\s+([,.;])", r"\1", text).strip()


def store() -> dict:
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)


def sales_per_event() -> dict[str, int]:
    data = store()
    ticket_event = {ticket["id"]: ticket["eventId"] for ticket in data["tickets"]}
    counts: dict[str, int] = {}
    for row in data["ledger"]:
        if row.get("kind") == "sale":
            event = ticket_event.get(row.get("ticketId"))
            counts[event] = counts.get(event, 0) + 1
    return counts


def selected(payload: dict) -> dict:
    return next((tier for tier in payload["tiers"] if tier.get("selected")), payload["tiers"][0])


def value(wrapper) -> float | None:
    return None if not isinstance(wrapper, dict) else wrapper.get("value")


# -- C1: the market block's denominator is the record's count, not the mode's zero ------


class TestTheMarketBlockNeverPrintsAnExcludedCountAsAZero(unittest.TestCase):
    """FINAL-PROOF-2 C1, 240 page states: `0 sales of 0 on this event` under `9 excluded`."""

    def test_the_denominator_is_the_records_count_in_every_before_on_sale_state(self) -> None:
        counts = sales_per_event()
        for event_id in EVENTS:
            if not counts.get(event_id):
                continue  # nothing recorded: there is no zero to mis-scope
            for cap in ("0", "1500", "3500"):
                with self.subTest(event=event_id, cap=cap):
                    html, payload = page_for(event_id=event_id, mode="before_on_sale", cap_bps=cap)
                    excluded = value(payload["decisionMode"]["excludedResales"])
                    self.assertGreater(excluded, 0, "the premise: the store holds sale rows here")
                    text = visible(html)
                    self.assertNotIn(
                        "sales of [FIXTURE] 0 on this event",
                        text,
                        "the event's own count is the record's, and the mode does not unrecord it",
                    )
                    self.assertIn(
                        f"of [FIXTURE] {excluded} on this event enter this decision", text
                    )
                    self.assertIn(
                        f"[FIXTURE] {excluded} recorded sales on this event are excluded by the mode",
                        text,
                        "the exclusion is named at event scope, not only at tier scope",
                    )

    def test_the_tier_share_of_the_excluded_rows_is_named(self) -> None:
        html, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        mode = payload["decisionMode"]
        everything = value(mode["excludedResales"])
        own_tier = value(mode["excludedTierResales"])
        self.assertEqual((everything, own_tier), (12, 9), "the premise: 12 on the event, 9 in General")
        self.assertIn(
            "[FIXTURE] 12 recorded sales on this event are excluded by the mode, "
            "[FIXTURE] 9 of them in this tier",
            visible(html),
        )

    def test_a_tier_with_no_rows_of_its_own_says_where_the_rows_are(self) -> None:
        """The other branch: the tier holds none of the event's rows, and the clause says so."""
        html, payload = page_for(
            event_id="evt_syn_02", mode="before_on_sale", tier_id="tier_stg_general"
        )
        tier = selected(payload)
        self.assertEqual(value(tier["market"]["sales"]), 0, "the premise: nothing enters this tier")
        self.assertEqual(value(payload["decisionMode"]["excludedTierResales"]), 9)
        self.assertIn("of them in this tier", visible(html))

    def test_the_at_ceiling_count_is_not_a_zero_for_excluded_rows(self) -> None:
        """The same zero, one clause to the right: `at the ceiling 0` beside `9 excluded`.

        The strip already refuses this count while the event's own record is excluded; the
        block printed a number the mode never measured.
        """
        html, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        self.assertEqual(value(payload["decisionMode"]["excludedResales"]), 12, "the premise")
        text = visible(html)
        self.assertNotIn("at the ceiling [FIXTURE] 0", text)
        self.assertIn("no at-ceiling count while the event's own record is excluded", text)

    def test_the_counterfactual_still_prints_the_measured_at_ceiling_count(self) -> None:
        html, payload = page_for(event_id="evt_syn_02")
        tier = selected(payload)
        measured = value(tier["market"]["atCeilingCount"])
        self.assertEqual(measured, 8, "the premise: eight recorded sales in this tier at the ceiling")
        self.assertIn(f"at the ceiling [FIXTURE] {measured}", visible(html))

    def test_the_counterfactual_keeps_the_records_own_two_counts(self) -> None:
        html, payload = page_for(event_id="evt_syn_02")
        self.assertIsNone(payload["decisionMode"]["excludedTierResales"], "the premise: no exclusion")
        text = visible(html)
        self.assertIn("in this tier [FIXTURE] 9 sales of [FIXTURE] 12 on this event", text)
        self.assertNotIn("are excluded by the mode", text)


# -- C2: no printed band above a ceiling the page prints --------------------------------


class TestNoBandCrossesACeilingThePageStates(unittest.TestCase):
    """FINAL-PROOF-2 C2, 310 page states: a band to 1.26 SOL above a stated ceiling of 0.84."""

    def test_no_printed_band_top_exceeds_any_printed_ceiling(self) -> None:
        checked = 0
        for event_id in EVENTS:
            for mode in MODES:
                for cap in CAPS:
                    html, payload = page_for(event_id=event_id, mode=mode, cap_bps=cap)
                    text = visible(html)
                    tier = selected(payload)
                    ceilings = printed_ceilings(text)
                    if not ceilings:
                        # A page that states no ceiling still has one in force when a cap is
                        # named; that is the ceiling the band may not cross.
                        face = value(tier["faceValueLamports"])
                        in_force = value(payload["selection"]["capBpsCandidate"])
                        if face is not None and in_force is not None:
                            ceilings = [face * (10_000 + in_force) // 10_000 / 1e9]
                    tops = [
                        float(match.group(2))
                        for pattern in (RECOMMENDATION_BAND, PRIOR_BAND)
                        for match in pattern.finditer(text)
                    ]
                    for top in tops:
                        with self.subTest(event=event_id, mode=mode, cap=cap, top=top):
                            if not ceilings:
                                continue  # no cap and no ceiling: nothing to cross
                            lowest = min(ceilings)
                            checked += 1
                            self.assertLessEqual(
                                top,
                                lowest,
                                f"a band top of {top} SOL under a stated ceiling of {lowest} SOL",
                            )
        self.assertGreater(checked, 100, "the premise: bands were printed and measured")

    def test_the_prior_band_is_cut_at_the_ceiling_and_the_cut_is_said(self) -> None:
        html, payload = page_for(event_id="evt_syn_03")
        band = selected(payload)["band"]
        self.assertEqual(value(band["hiLamports"]), 1_263_019_214, "the premise: the measured prior band")
        self.assertEqual(value(band["ceilingLamports"]), 840_000_000, "the premise: the stated ceiling")
        self.assertIsNotNone(band.get("shownHiLamports"), "the band on the page has a printed upper end")
        text = visible(html)
        self.assertIn(
            "prior band around face: [UNVALIDATED] 0.65 SOL \u2013 [UNVALIDATED] 0.84 SOL", text
        )
        self.assertIn(
            "That band is cut at the ceiling of [EXACT] 0.84 SOL that the cap of "
            "[DECLARED] 2000 bps in force puts on this tier",
            text,
        )
        self.assertIn(
            "The declared prior alone runs [UNVALIDATED] 0.65 SOL to [UNVALIDATED] 1.26 SOL",
            text,
            "the prior's own extent stays on the page, named as the prior's and not as the band",
        )

    def test_the_engine_and_the_page_are_held_apart_not_fudged(self) -> None:
        """The clamp is a display: the computed band still says what the prior says."""
        cases = (
            ("evt_syn_03", None, 1_263_019_214, 840_000_000),
            ("evt_syn_05", "1500", 2_706_469_744, 1_725_000_000),
        )
        for event_id, cap, computed, shown in cases:
            with self.subTest(event=event_id, cap=cap):
                _, payload = page_for(event_id=event_id, cap_bps=cap)
                band = selected(payload)["band"]
                self.assertEqual(value(band["hiLamports"]), computed, "the engine's own number")
                self.assertEqual(value(band.get("shownHiLamports")), shown, "the band the page prints")
                self.assertEqual(value(band.get("ceilingAppliedLamports")), shown, "the ceiling it stops at")
                self.assertLess(value(band.get("shownHiLamports")), value(band["hiLamports"]))

    def test_the_printed_top_of_a_cut_band_is_the_ceiling_digit_for_digit(self) -> None:
        """`1.73` against a ceiling of 1.725 is a band above its own ceiling, by rounding."""
        html, payload = page_for(event_id="evt_syn_05", cap_bps="1500")
        band = selected(payload)["band"]
        self.assertEqual(value(band.get("ceilingAppliedLamports")), 1_725_000_000)
        text = visible(html)
        self.assertIn("prior band around face: [UNVALIDATED] 1.40 SOL \u2013 [UNVALIDATED] 1.725 SOL", text)
        self.assertNotIn("1.73 SOL. That is a band around the declared prior", text)

    def test_a_payload_band_never_shows_a_top_above_a_ceiling_it_states(self) -> None:
        for event_id in EVENTS:
            for mode in MODES:
                for cap in CAPS:
                    _, payload = page_for(event_id=event_id, mode=mode, cap_bps=cap)
                    for tier in payload["tiers"]:
                        band = tier["band"]
                        shown = value(band.get("shownHiLamports"))
                        if shown is None:
                            continue
                        face = value(tier["faceValueLamports"])
                        ceilings = [
                            c
                            for c in (
                                value(band.get("ceilingLamports")),
                                None if cap is None else face * (10_000 + int(cap)) // 10_000,
                            )
                            if c is not None
                        ]
                        if not ceilings:
                            continue  # no cap in force and none recorded: no ceiling exists
                        with self.subTest(event=event_id, tier=tier["tierId"], mode=mode, cap=cap):
                            self.assertLessEqual(shown, min(ceilings))
                            self.assertLessEqual(value(band["shownLoLamports"]), shown)


# -- C3: the band-stop sentence names the ceiling's actual source -----------------------


class TestTheBandStopSentenceNamesTheCeilingsSource(unittest.TestCase):
    """FINAL-PROOF-2 C3, 44 page states: `the ceiling the cap in force puts on this tier`."""

    def test_a_typed_cap_above_the_record_names_the_records_ceiling(self) -> None:
        html, payload = page_for(event_id="evt_syn_01", cap_bps="3500")
        band = selected(payload)["band"]
        self.assertEqual(value(payload["selection"]["capBpsCandidate"]), 3500, "the premise: cap in force")
        self.assertEqual(value(band["boundCeilingLamports"]), 1_250_000_000, "the recorded ceiling")
        self.assertEqual(value(band.get("boundCeilingCapBps")), 2500, "the cap that produced it")
        self.assertEqual(band.get("boundCeilingSource"), "recorded_cap")
        text = visible(html)
        self.assertIn(
            "The top of that band is the ceiling the recorded cap of [FIXTURE] 2500 bps puts on "
            "this tier, at [EXACT] 1.25 SOL, which is below what the cap of [DECLARED] 3500 bps "
            "in force allows, so the range stops at the recorded ceiling.",
            text,
        )
        self.assertNotIn("the ceiling the cap in force puts on this tier", text)

    def test_a_typed_cap_below_the_record_names_the_cap_in_force(self) -> None:
        html, payload = page_for(event_id="evt_syn_01", cap_bps="298")
        band = selected(payload)["band"]
        self.assertEqual(value(payload["selection"]["capBpsCandidate"]), 298, "the premise: cap in force")
        self.assertEqual(value(band["boundCeilingLamports"]), 1_029_800_000)
        self.assertEqual(band.get("boundCeilingSource"), "cap_in_force")
        self.assertIn(
            "The top of that band is the ceiling the cap in force puts on this tier, at 1.0298 "
            "SOL, so the range stops where the cap does.",
            visible(html),
        )

    def test_the_sentence_and_the_number_agree_in_every_state_that_prints_one(self) -> None:
        checked = 0
        for event_id in EVENTS:
            for cap in CAPS:
                html, payload = page_for(event_id=event_id, cap_bps=cap)
                band = selected(payload)["band"]
                if not band.get("topIsCeiling") or value(band.get("boundCeilingLamports")) is None:
                    continue
                if selected(payload)["recommendation"].get("refusalCode") is not None:
                    continue  # no band is printed, so no sentence about one
                if selected(payload)["regime"] == "capped_and_binding":
                    continue  # a binding record states a floor and no upper bound at all

                self.assertIsNotNone(
                    BAND_STOPS.search(visible(html)) or BAND_STOPS_RECORDED.search(visible(html)),
                    "a band whose top is a ceiling must say so",
                )
                text = visible(html)
                face = value(selected(payload)["faceValueLamports"])
                in_force = value(payload["selection"]["capBpsCandidate"])
                recorded = value(payload["event"]["capBps"])
                if band.get("boundCeilingSource") == "recorded_cap":
                    self.assertIsNotNone(recorded)
                    self.assertIsNotNone(in_force)
                    self.assertGreater(in_force, recorded, "the premise: the typed cap is the higher one")
                    claimed = face * (10_000 + recorded) // 10_000
                    self.assertNotIn("the ceiling the cap in force puts on this tier", text)
                else:
                    claimed = face * (10_000 + in_force) // 10_000
                    self.assertIn("the ceiling the cap in force puts on this tier", text)
                self.assertEqual(value(band["boundCeilingLamports"]), claimed)
                checked += 1
        self.assertGreater(checked, 10, "the premise: band-stop sentences were printed")


if __name__ == "__main__":
    unittest.main()
