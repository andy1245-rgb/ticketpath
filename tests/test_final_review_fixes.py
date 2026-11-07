"""The four defects the final independent review failed honesty on, held by tests.

`records/findings/10-final-review.md` names them N1 to N4. Each test here is written
against the rendered page or against the features at a cut, and each one fails on the
behaviour before the fix: the fix pass reverted the code for all four and recorded the
failures in `records/BUILD-REPORT-CONSOLE.md` (2026-11-07, the section after the five
earlier fix reports).

1. N1: three branches that ask "does this page have a cap?" read the event's recorded cap
   while the page priced against the cap typed into the URL. On `?event=evt_syn_04&capBps=1700`
   the strip, `A2` and the market block each said there was no cap and no ceiling, on a page
   that named a cap, counted seven sales above its ceiling, and printed a band under it.
2. N2: the recommendation's band was never trimmed to the cap in force, so it carried an
   upper end above a ceiling the page refuses to cross. On `?event=evt_syn_01&capBps=298`
   it printed `Band 0.74 - 1.25 SOL` beside a page ceiling of 1.0298 SOL.
3. N3: the ticket-day denominator ran past the event end, so on a static record the measured
   rate fell as the cut advanced (20.7 to 4.3 per 1,000 ticket-days for the same nine sales).
4. N4: the before-on-sale page printed `0 resales`, `0 tickets` and `No ticket had been
   issued` for a store holding 12 of each. The mode excludes the rows; it does not unrecord
   them.
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
from ticketpath.console import blocks
from ticketpath.core import labels, price_features
from ticketpath.orchestrator import Orchestrator

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
FIXTURE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "synthetic_store.json")

# The sentences that deny a ceiling on a page that has one. Patterns, because the same
# claim was made three ways and a fix to one wording would leave the others.
SENTENCES_THAT_DENY_THE_CEILING = (
    re.compile(r"no resale cap, so no ceiling"),
    re.compile(r"This event has no resale cap, so there is no ceiling to count against"),
    re.compile(r"This event has no resale cap, so no ceiling enters the bound"),
    re.compile(r"This event records no cap, so no ceiling"),
)

# The sentences that state the excluded record as an absent one.
SENTENCES_THAT_SAY_THE_ROWS_ARE_ABSENT = (
    re.compile(r"\[FIXTURE\] 0 resales on this event"),
    re.compile(r"No ticket had been issued at this instant"),
    re.compile(r"\[FIXTURE\] 0 tickets (?!enter)"),
)


def orchestrator() -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
    )


def page_for(**query) -> tuple[int, str, dict]:
    payload = orchestrator().price_guidance(**query)
    payload["canonicalUrl"] = "http://127.0.0.1:8788/?"
    from ticketpath.console import page

    return 200, page.render(payload), payload


def visible(html: str) -> str:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", without_style)))


def store() -> dict:
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)


# -- 1. every branch that talks about the cap reads the cap the decision uses ----


class TestTheCapInForceReachesEverySentenceAboutTheCap(unittest.TestCase):
    """N1: three branches read the recorded cap while the page priced against another."""

    def test_an_uncapped_event_with_a_typed_cap_names_that_cap_in_all_three(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_04", cap_bps="1700")
        # the premise: no recorded cap, and a cap in force of 1700 bps
        self.assertIsNone(payload["event"]["capBps"]["value"])
        self.assertEqual(payload["selection"]["capBpsCandidate"]["value"], 1700)
        ceiling = 800_000_000 * (10_000 + 1700) // 10_000
        self.assertEqual(ceiling, 936_000_000)
        # the premise: the page counts sales above that ceiling
        count = payload["tiers"][0]["band"]["capViolations"]["count"]["value"]
        self.assertEqual(count, 7)
        text = visible(html)
        for claim in SENTENCES_THAT_DENY_THE_CEILING:
            with self.subTest(claim=claim.pattern):
                self.assertIsNone(claim.search(text), f"the page says {claim.pattern!r} while it prices against 1700 bps")
        # 1. the evidence strip
        self.assertIn(
            "no resale cap is recorded on this event, so its sales have no ceiling to be counted "
            "against; this page prices against a cap of [DECLARED] 1700 bps",
            text,
        )
        # 2. the A2 sentence in the decision block
        self.assertIn(labels.render("A2_CAP_IN_FORCE_UNCAPPED"), text)
        self.assertNotIn(labels.render("A2_UNCAPPED"), text)
        # 3. the market block, four lines above the violation line
        self.assertIn(
            "and the sales above that cap are counted in the decision.",
            text,
        )
        self.assertNotIn(labels.render("P_NO_CAP"), text)

    def test_a_capped_event_priced_against_another_cap_says_which_ceiling_it_counts(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_01", cap_bps="298")
        self.assertEqual(payload["event"]["capBps"]["value"], 2500)
        self.assertEqual(payload["selection"]["capBpsCandidate"]["value"], 298)
        text = visible(html)
        # the at-ceiling count is against the record's own cap, and both blocks say so
        self.assertIn("at the recorded ceiling", text)
        self.assertNotIn("This event has no resale cap", text)
        self.assertIn(labels.render("A2"), text)

    def test_no_page_priced_against_a_cap_says_it_has_none(self) -> None:
        """The property, swept: every uncapped event against every cap a judge might type."""
        for event_id in ("evt_syn_04", "evt_syn_05", "evt_syn_08"):
            for cap in ("0", "1", "500", "1700", "2500", "10000"):
                with self.subTest(event=event_id, cap=cap):
                    _, html, payload = page_for(event_id=event_id, cap_bps=cap)
                    self.assertIsNone(payload["event"]["capBps"]["value"], "the premise: uncapped event")
                    self.assertEqual(payload["selection"]["capBpsCandidate"]["value"], int(cap))
                    text = visible(html)
                    for claim in SENTENCES_THAT_DENY_THE_CEILING:
                        self.assertIsNone(claim.search(text), f"{claim.pattern!r} at cap {cap}")
                    self.assertIn(f"[DECLARED] {int(cap)} bps", text)


# -- 2. the band stops at the ceiling the page refuses to cross ------------------


class TestTheBandStopsAtTheCeilingThePageEnforces(unittest.TestCase):
    """N2: the band carried an upper end above a ceiling the page says it will not cross."""

    def test_the_band_top_is_the_candidate_ceiling_on_a_capped_event(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_01", cap_bps="298")
        tier = blocks.selected_tier(payload)
        face = tier["faceValueLamports"]["value"]
        ceiling = face * (10_000 + 298) // 10_000
        self.assertEqual(ceiling, 1_029_800_000)
        hi = tier["recommendation"]["bandHiLamports"]["value"]
        self.assertLessEqual(hi, ceiling, "the band's upper end is above the ceiling in force")
        self.assertEqual(hi, ceiling)
        self.assertEqual(tier["band"]["boundCeilingLamports"]["value"], ceiling)
        text = visible(html)
        self.assertIn("The top of that band is the ceiling the cap in force puts on this tier, at 1.0298 SOL, "
                      "so the range stops where the cap does.", text)
        self.assertNotIn("Band 0.74 – 1.25 SOL", text)

    def test_the_band_top_is_the_candidate_ceiling_on_an_uncapped_event(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_04", cap_bps="1632")
        tier = blocks.selected_tier(payload)
        ceiling = tier["faceValueLamports"]["value"] * (10_000 + 1632) // 10_000
        self.assertEqual(ceiling, 930_560_000)
        self.assertEqual(tier["recommendation"]["bandHiLamports"]["value"], ceiling)
        self.assertIn("at 0.93056 SOL", visible(html))

    def test_no_printed_band_exceeds_the_ceiling_in_force(self) -> None:
        """The property, swept over every event, tier and cap a URL can carry."""
        checked = 0
        for event_id in ("evt_syn_01", "evt_syn_02", "evt_syn_03", "evt_syn_04", "evt_syn_05",
                         "evt_syn_06", "evt_syn_07", "evt_syn_08"):
            for cap in ("0", "1", "298", "1000", "1500", "1700", "2500", "10000"):
                _, html, payload = page_for(event_id=event_id, cap_bps=cap)
                text = visible(html)
                for tier in payload["tiers"]:
                    ceiling = tier["faceValueLamports"]["value"] * (10_000 + int(cap)) // 10_000
                    hi = tier["recommendation"].get("bandHiLamports")
                    if hi is None or hi.get("value") is None:
                        continue
                    with self.subTest(event=event_id, tier=tier["tierId"], cap=cap):
                        checked += 1
                        self.assertLessEqual(
                            hi["value"], ceiling, "a band top above the ceiling the page refuses to cross"
                        )
                        self.assertLessEqual(tier["band"]["loLamports"]["value"], hi["value"])
                    # and where that top is printed, the digits are the ceiling, not a rounding
                    # of it that reads above the ceiling
                    if tier["selected"] and tier["recommendation"]["refusalCode"] is None and tier["band"]["topIsCeiling"]:
                        with self.subTest(event=event_id, tier=tier["tierId"], cap=cap, printed=True):
                            match = re.search(r"Band ([\d.]+) – ([\d.]+) SOL", text)
                            self.assertIsNotNone(match, text[:400])
                            self.assertEqual(float(match.group(2)), hi["value"] / 1e9)
        self.assertGreater(checked, 0, "the sweep never reached a band")


# -- 3. the ticket-day denominator stops at the event end -----------------------


def ticket(ticket_id, tier_id="tier_a", event_id="evt_t"):
    return {"id": ticket_id, "eventId": event_id, "tierId": tier_id, "mintAddress": "SYNmint" + ticket_id}


def tier(tier_id="tier_a", face=1_000_000_000, supply=10, issued=3):
    return {"id": tier_id, "name": "A", "faceValueLamports": face, "totalSupply": supply, "issuedCount": issued}


def event(ends_at, tiers, cap=1500, event_id="evt_t"):
    return {
        "id": event_id,
        "name": "Test event",
        "city": "Testville",
        "status": "on_sale",
        "startsAt": "2026-01-11T00:00:00.000Z",
        "endsAt": ends_at,
        "resalePriceCapBps": cap,
        "tiers": tiers,
    }


def row(row_id, ticket_id, kind, occurred_at, price=None):
    return {
        "id": row_id,
        "ticketId": ticket_id,
        "kind": kind,
        "fromWallet": None,
        "toWallet": "SYNwallet",
        "priceLamports": price,
        "signature": None,
        "slot": None,
        "occurredAt": occurred_at,
    }


class TestTheDenominatorStopsAtTheEventEnd(unittest.TestCase):
    """N3: exposure ran past the end, so a static record's measured rate fell with the clock.

    A ticket is at risk from its issue row to the first of: the cut, the redeem row, and the
    end of the event it admits to. The test below is three tickets, one redeemed, an event
    that ends one day after the issues, and a cut ten days after them.
    """

    def _features(self, ends_at, as_of):
        tickets = [ticket("tkt_a"), ticket("tkt_b"), ticket("tkt_c")]
        ledger = [
            row("l1", "tkt_a", "issue", "2026-01-01T00:00:00.000Z"),
            row("l2", "tkt_b", "issue", "2026-01-02T00:00:00.000Z"),
            row("l3", "tkt_c", "issue", "2026-01-03T00:00:00.000Z"),
            row("l4", "tkt_a", "redeem", "2026-01-03T00:00:00.000Z"),
        ]
        return price_features.build(
            events=[event(ends_at, [tier()])],
            tickets=tickets,
            ledger=ledger,
            tier_faces={t["id"]: 1_000_000_000 for t in tickets},
            event_id="evt_t",
            as_of=as_of,
        )

    def test_a_cut_ten_days_after_a_one_day_event_counts_one_day(self) -> None:
        # a: issue 01-01, redeemed 01-03 -> 2.0; b: issue 01-02 to the end 01-04 -> 2.0;
        # c: issue 01-03 to the end 01-04 -> 1.0
        by_hand = {"tkt_a": 2.0, "tkt_b": 2.0, "tkt_c": 1.0}
        cut = dt.datetime(2026, 1, 11, 0, 0, 0, tzinfo=UTC)
        features = self._features("2026-01-04T00:00:00.000Z", cut)
        self.assertEqual(features["tiers"][0]["exposureTicketDays"], sum(by_hand.values()))
        # the old behaviour, for contrast: min(cut, redeem) - issue, with no event end
        self.assertEqual(2.0 + 9.0 + 8.0, 19.0)

    def test_the_end_of_the_event_is_the_last_instant_of_exposure(self) -> None:
        for cut in ("2026-01-04T00:00:00Z", "2026-06-01T00:00:00Z", "2027-06-01T00:00:00Z"):
            with self.subTest(cut=cut):
                features = self._features(
                    "2026-01-04T00:00:00.000Z",
                    dt.datetime.fromisoformat(cut.replace("Z", "+00:00")),
                )
                self.assertEqual(features["tiers"][0]["exposureTicketDays"], 5.0)

    def test_an_event_with_no_recorded_end_is_stopped_by_the_cut_alone(self) -> None:
        features = self._features(None, dt.datetime(2026, 1, 11, 0, 0, 0, tzinfo=UTC))
        self.assertEqual(features["tiers"][0]["exposureTicketDays"], 19.0)

    def test_a_cut_before_the_end_is_unchanged(self) -> None:
        features = self._features("2026-01-04T00:00:00.000Z", dt.datetime(2026, 1, 3, 12, 0, 0, tzinfo=UTC))
        # a 2.0, b 1.5, c 0.5: every stop is the cut, so the end changes nothing
        self.assertEqual(features["tiers"][0]["exposureTicketDays"], 4.0)

    def test_the_page_rate_stops_falling_once_the_cut_passes_the_event(self) -> None:
        cuts = ("2026-11-22T02:00:00Z", "2026-11-22T03:00:00Z", "2026-12-31T00:00:00Z", "2027-06-01T00:00:00Z")
        seen = []
        for cut in cuts:
            _, html, _ = page_for(event_id="evt_syn_02", as_of=cut)
            text = visible(html)
            exposure = re.search(r"exposure \[FIXTURE\] ([\d.,]+) ticket-days at risk", text)
            rate = re.search(r"sale rate in this tier: \[FIXTURE\] ([\d.]+) per 1,000", text)
            self.assertIsNotNone(exposure, text[:600])
            self.assertIsNotNone(rate, text[:600])
            seen.append((exposure.group(1), rate.group(1)))
        # one value for the four cuts, from the event end onward
        self.assertEqual(len(set(seen)), 1, seen)
        self.assertEqual(seen[0][0], "551.8")
        self.assertEqual(seen[0][1], "16.3")
        # and the cut before the end still measures its own window
        _, html, _ = page_for(event_id="evt_syn_02", as_of="2026-11-07T12:00:00Z")
        self.assertIn("exposure [FIXTURE] 435.1 ticket-days at risk", visible(html))

    def test_the_cold_start_rate_stops_falling_after_the_event(self) -> None:
        """The state the review measured 0.7 per 1,000 on, now 2.9 at every post-end cut."""
        for cut in ("2026-12-12T04:00:00Z", "2027-06-01T00:00:00Z"):
            with self.subTest(cut=cut):
                _, html, _ = page_for(event_id="evt_syn_03", as_of=cut)
                text = visible(html)
                self.assertIn("exposure [FIXTURE] 339.4 ticket-days at risk", text)
                self.assertIn("sale rate in this tier: [DECLARED] 2.9 per 1,000 ticket-days", text)
        _, html, _ = page_for(event_id="evt_syn_03")
        self.assertIn("exposure [FIXTURE] 131.4 ticket-days at risk", visible(html))


# -- 4. the before-on-sale page counts the excluded rows as excluded ------------


class TestTheBeforeOnSaleStripSaysTheRowsAreExcluded(unittest.TestCase):
    """N4: `0 resales`, `0 tickets` and `No ticket had been issued` for a store holding 12."""

    def _own_rows(self, event_id="evt_syn_02", cut="2026-11-07T12:00:00Z"):
        data = store()
        own = {t["id"] for t in data["tickets"] if t["eventId"] == event_id}
        at_cut = dt.datetime.fromisoformat(cut.replace("Z", "+00:00"))
        rows = [
            r for r in data["ledger"]
            if r["ticketId"] in own and dt.datetime.fromisoformat(r["occurredAt"].replace("Z", "+00:00")) <= at_cut
        ]
        sales = [r for r in rows if r["kind"] == "sale" and r["priceLamports"] is not None]
        issues = {r["ticketId"] for r in rows if r["kind"] == "issue"}
        return len(sales), len(issues)

    def test_the_strip_counts_what_enters_and_what_the_mode_excludes(self) -> None:
        sales, issues = self._own_rows()
        self.assertEqual((sales, issues), (12, 12), "the premise: 12 sale rows and 12 ticket rows exist")
        _, html, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        self.assertIs(payload["decisionMode"]["usesOwnRecord"], False)
        text = visible(html)
        for claim in SENTENCES_THAT_SAY_THE_ROWS_ARE_ABSENT:
            with self.subTest(claim=claim.pattern):
                self.assertIsNone(claim.search(text), f"the page says {claim.pattern!r} while the store holds 12")
        self.assertIn(
            "[FIXTURE] 0 resales enter this decision; [FIXTURE] 12 recorded on this event are "
            "excluded by the mode",
            text,
        )
        self.assertIn(
            "[FIXTURE] 0 tickets enter it; [FIXTURE] 12 recorded on this event are excluded by the mode",
            text,
        )
        self.assertIn("no at-ceiling count while the event's own record is excluded", text)

    def test_the_no_denominator_refusal_names_the_excluded_tickets(self) -> None:
        _, html, _ = page_for(event_id="evt_syn_02", mode="before_on_sale")
        text = visible(html)
        self.assertIn(
            "[FIXTURE] 12 tickets are recorded on this event at this instant, and the BEFORE-ON-SALE "
            "decision mode excludes every one of them, so no ticket-day of exposure enters this "
            "denominator and the rate has none.",
            text,
        )
        self.assertNotIn("No ticket had been issued at this instant", text)

    def test_the_payload_basis_names_the_store_count_and_the_exclusion(self) -> None:
        _, _, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        tickets = payload["evidence"]["tickets"]
        self.assertEqual(tickets["value"], 0)
        self.assertIn("12 ticket rows exist in the store", tickets["basis"])
        self.assertIn("the decision mode excludes them", tickets["basis"])
        self.assertEqual(payload["decisionMode"]["excludedResales"]["value"], 12)
        self.assertEqual(payload["decisionMode"]["excludedTickets"]["value"], 12)

    def test_an_event_with_no_rows_keeps_the_sentence_that_is_true_there(self) -> None:
        """`evt_syn_08` has issued nothing: no rows are excluded, so none are counted as such."""
        sales, issues = self._own_rows("evt_syn_08")
        self.assertEqual((sales, issues), (0, 0), "the premise: this event has no rows at the cut")
        _, html, payload = page_for(event_id="evt_syn_08", mode="before_on_sale")
        self.assertEqual(payload["decisionMode"]["excludedTickets"]["value"], 0)
        text = visible(html)
        self.assertIn("No ticket had been issued at this instant, so there is no denominator.", text)
        self.assertNotIn("excludes every one of them", text)
        self.assertNotIn("tickets are recorded on this event at this instant", text)

    def test_the_counterfactual_page_still_counts_the_record_it_reads(self) -> None:
        _, html, _ = page_for(event_id="evt_syn_02")
        text = visible(html)
        self.assertIn("[FIXTURE] 12 resales on this event", text)
        self.assertIn("[FIXTURE] 12 tickets", text)


if __name__ == "__main__":
    unittest.main()
