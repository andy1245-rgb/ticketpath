"""The last-mile list: five items, each held by an assertion that fails on the old code.

Two independent reviews and the cap-capture check name them; this file pins the repair.
Every assertion is written against the rendered page, against the payload the page is built
from, or against a socket, which is where a reader, a judge and a link checker meet the
product.

1. `11-cap-capture-check.md` §10.1: the cap refusal said "a recommendation above that
   ceiling is a price the cap forbids". A cap in basis points over face moves with face, so
   it decides how a resale price divides and constrains the reseller, not what the organizer
   may charge. The refusal's numbers are untouched; only the claim around them changed.
2. `10-final-review.md` N6: a store with one event held back printed `7 events in the store`
   from the served list, while the file carried 8. The store total, the served count and what
   was withheld are now three named facts on one line.
3. N8: the status field is the store's *current* field and cannot follow the decision
   instant, so on `?event=evt_syn_02&asOf=2027-06-01T00:00:00Z` the page printed `status
   on_sale` beside an event that ended seven months earlier. The page now states both and
   says they disagree, and the before-on-sale premise stops claiming it is a decision taken
   before the first issue when the instant is after the end.
4. N9: `TRACE /` answered 501 with Python's own error page, alone among the verbs. It is now
   the same rendered 405 `PUT`, `DELETE` and `PATCH` get.
5. The before-on-sale market block printed the tier's `0 sales` and the event's `0` in a
   sentence that is the tier's, while the strip above it named 12 excluded rows. The block
   now carries the tier-scoped excluded count, from the same scan of the same rows.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import html as html_module
import json
import os
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import make_server

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "synthetic_store.json"
)


def orchestrator(ledger: LedgerAdapter | None = None) -> Orchestrator:
    return Orchestrator(
        ledger or LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
    )


def page_for(ledger: LedgerAdapter | None = None, **query) -> tuple[int, str, dict]:
    """The page and the payload it was rendered from: the same pair the console route makes.

    The query is the API's own keywords (`event_id`, `as_of`, ...), which is how the other
    console tests drive it; the route maps its query string onto these in `console_index`.
    """
    payload = orchestrator(ledger).price_guidance(**query)
    payload["canonicalUrl"] = "http://127.0.0.1:8788/?"
    return 200, page.render(payload), payload


def visible(html: str) -> str:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", without_style)))


def store() -> dict:
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)


def write_store(data: dict) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, handle)
    handle.close()
    return handle.name


def held_back_store() -> tuple[str, dict]:
    """The shipped fixture with one sale recorded without money.

    That is the state the loader refuses per event (`sale_not_priced`), so eight event rows
    exist in the file and seven are served. It is the exact store the final review measured
    `7 events in the store` on.
    """
    data = store()
    own = {ticket["id"] for ticket in data["tickets"] if ticket["eventId"] == "evt_syn_01"}
    for row in data["ledger"]:
        if row["kind"] == "sale" and row["ticketId"] in own:
            row["priceLamports"] = 0
            break
    return write_store(data), data


@contextlib.contextmanager
def serving(ledger: LedgerAdapter | None = None):
    server = make_server(0, "127.0.0.1", orchestrator(ledger))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(url: str, method: str = "GET") -> tuple[int, str]:
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


# -- 1. the cap decides how a resale price divides, not what a primary price may be ---


class TestTheCapRefusalDoesNotClaimTheCapForbidsAPrimaryPrice(unittest.TestCase):
    """11-cap-capture-check §10.1: the absolute-cap sentence, in the one place it shipped."""

    def test_the_refusal_states_the_narrowed_claim_and_keeps_both_its_numbers(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_01", cap_bps="0")
        tier = next(row for row in payload["tiers"] if row["selected"])
        # the premise: the refusal is reached, on this page, for this tier
        self.assertEqual(tier["recommendation"]["refusalCode"], "recommendation_above_cap")
        self.assertEqual(payload["selection"]["capBpsCandidate"]["value"], 0)
        ceiling = 1_000_000_000 * (10_000 + 0) // 10_000
        self.assertEqual(ceiling, 1_000_000_000)
        text = visible(html)
        # the sentence that said the cap forbids a primary price is gone
        self.assertNotIn("a price the cap forbids", text)
        self.assertNotIn("forbids the price", text)
        # and the narrowed claim is on the page, in the registry's own words
        self.assertIn(
            "A cap in basis points over face decides how the resale price divides, not what "
            "the organizer may charge: it forbids a resale price",
            text,
        )
        self.assertIn("The record, not the cap, is what has run out", text)
        # both numbers are the ones that were printed before, at the same precision
        self.assertIn("[DECLARED] 0 bps", text)
        self.assertIn("[EXACT] 1,000,000,000 lamports", text)
        self.assertIn("the ceiling is not a target for the primary price", text)

    def test_the_refusal_number_is_the_cap_arithmetic_and_nothing_else(self) -> None:
        """The item is prose: the ceiling the refusal prints is still face x (10000+cap)/10000."""
        cases = (
            ("evt_syn_01", 0, 1_000_000_000),
            ("evt_syn_02", 1499, 1_200_000_000),
            ("evt_syn_07", 0, 900_000_000),
        )
        for event_id, cap, face in cases:
            with self.subTest(event_id=event_id, cap=cap):
                _, _, payload = page_for(event_id=event_id, cap_bps=str(cap))
                tier = next(row for row in payload["tiers"] if row["selected"])
                # the premise: this pair really does reach the refusal
                self.assertEqual(tier["recommendation"]["refusalCode"], "recommendation_above_cap")
                self.assertEqual(tier["faceValueLamports"]["value"], face)
                printed = tier["recommendation"]["candidateCeilingLamports"]["value"]
                self.assertEqual(printed, face * (10_000 + cap) // 10_000)

    def test_the_label_itself_no_longer_makes_the_absolute_claim(self) -> None:
        sentence = labels.render("recommendation_above_cap", cap_bps="0", ceiling_lamports="1")
        self.assertNotIn("cap forbids", sentence)
        self.assertIn("it forbids a resale price", sentence)


# -- 2. the store's own count, beside what was served and what was withheld -----------


class TestAHeldBackStoreNamesItsStoreTotalServedAndWithheld(unittest.TestCase):
    """N6: `7 events in the store` on a file that carries 8."""

    def test_the_count_is_the_store_and_the_difference_is_named(self) -> None:
        path, data = held_back_store()
        try:
            ledger = LedgerAdapter.from_fixture(path)
            self.assertEqual(len(list(ledger.events())), 7, "the premise: seven events are served")
            self.assertEqual(set(ledger.rejections()), {"evt_syn_01"}, "the premise: one is held back")
            self.assertEqual(len(data["events"]), 8, "the premise: the file carries eight")
            _, html, payload = page_for(ledger, event_id="evt_syn_02")
        finally:
            os.unlink(path)
        text = visible(html)
        # the served count is not printed as the store's
        self.assertNotIn("[FIXTURE] 7 events in the store", text)
        self.assertIn(
            "[FIXTURE] 8 events in the store, [FIXTURE] 7 served, one held back: a sale recorded "
            "without money,",
            text,
        )
        # the typed code stays in the payload and off a page about another event: an engine
        # token in the strip reads as this event's refusal (the rule the console holds).
        self.assertNotIn("sale_not_priced", text)
        # the payload carries the three counts, so the line cannot drift from the store
        evidence = payload["evidence"]
        self.assertEqual(evidence["eventsInStore"]["value"], 8)
        self.assertEqual(evidence["eventsOnPlatform"]["value"], 7)
        self.assertEqual(evidence["eventsHeldBack"]["value"], 1)
        self.assertEqual(evidence["heldBackReasons"], [{"eventId": "evt_syn_01", "code": "sale_not_priced"}])

    def test_a_store_with_nothing_held_back_keeps_the_plain_line(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_02")
        text = visible(html)
        self.assertIn("[FIXTURE] 8 events in the store, [FIXTURE]", text)
        self.assertNotIn("served", text)
        self.assertNotIn("held back", text)
        self.assertEqual(payload["evidence"]["eventsHeldBack"]["value"], 0)

    def test_the_held_back_event_is_still_refused_by_name(self) -> None:
        """The count and the refusal are about the same row, and the refusal did not move."""
        path, _ = held_back_store()
        try:
            ledger = LedgerAdapter.from_fixture(path)
            with self.assertRaises(Exception) as caught:
                orchestrator(ledger).price_guidance(event_id="evt_syn_01")
        finally:
            os.unlink(path)
        self.assertEqual(getattr(caught.exception, "code", None), "sale_not_priced")
        self.assertIn("recorded without money", str(caught.exception))


# -- 3. the status field and the decision instant, when they disagree ------------------


class TestTheStatusIsNotPrintedAsTheStatussAtTheDecisionInstant(unittest.TestCase):
    """N8: `status on_sale` beside a decision instant seven months after the end."""

    def test_a_post_end_instant_states_both_and_says_they_differ(self) -> None:
        _, html, _ = page_for(event_id="evt_syn_02", as_of="2027-06-01T00:00:00Z")
        text = visible(html)
        # both are still on the page: the store's field, and the instant
        self.assertIn("status on_sale is the store's current field, not the status at this", text)
        self.assertIn("decision instant 2027-06-01T00:00:00.000Z", text)
        self.assertIn("ends 2026-11-22T02:00:00.000Z", text)
        # and the disagreement is stated, not left for a reader to notice
        self.assertIn("the field and the instant disagree", text)
        # the old line, which printed the field as if it were the instant's
        self.assertNotIn("status on_sale · starts", text)

    def test_the_same_event_before_it_ends_keeps_the_plain_line(self) -> None:
        _, html, _ = page_for(event_id="evt_syn_02")
        text = visible(html)
        self.assertIn("status on_sale · starts 2026-11-21T23:00:00.000Z", text)
        self.assertNotIn("the field and the instant disagree", text)

    def test_a_completed_event_at_a_post_end_cut_is_not_told_it_disagrees(self) -> None:
        """`evt_syn_06` is `completed`, so the status and a post-end instant agree."""
        _, html, _ = page_for(event_id="evt_syn_06", as_of="2027-06-01T00:00:00Z")
        text = visible(html)
        self.assertIn("status completed · starts", text)
        self.assertNotIn("the field and the instant disagree", text)

    def test_the_before_on_sale_premise_stops_claiming_a_premise_it_cannot_have(self) -> None:
        _, html, _ = page_for(
            event_id="evt_syn_02", as_of="2027-06-01T00:00:00Z", mode="before_on_sale"
        )
        text = visible(html)
        self.assertIn(labels.render("P_MODE_BEFORE"), text)
        self.assertIn(
            "This decision instant is after the event ended, so this is what the before-on-sale "
            "decision would price on the record that exists today, not a decision that could "
            "have been taken at that instant.",
            text,
        )
        # and the plain before-on-sale page does not carry that clause
        _, html, _ = page_for(event_id="evt_syn_02", mode="before_on_sale")
        self.assertNotIn("not a decision that could have been taken", visible(html))


# -- 4. TRACE answers like every other unserved verb ----------------------------------


class TestTraceIs405LikeEveryOtherUnservedVerb(unittest.TestCase):
    """N9: `TRACE /` was 501 with Python's own page, alone among the verbs."""

    def test_trace_on_the_console_is_the_rendered_405(self) -> None:
        with serving() as base:
            status, body = request(base + "/", method="TRACE")
        self.assertEqual(status, 405)
        self.assertIn("<!doctype html>", body)
        self.assertIn("method_not_allowed", body)
        self.assertIn("TRACE is not allowed here", body)
        self.assertNotIn("Unsupported method", body)

    def test_trace_on_an_api_route_is_405_with_the_json_error(self) -> None:
        with serving() as base:
            for path in ("/api/events", "/api/tickets", "/health"):
                with self.subTest(path=path):
                    status, body = request(base + path, method="TRACE")
                    self.assertEqual(status, 405)
                    self.assertIn("method_not_allowed", body)

    def test_trace_on_a_path_that_does_not_exist_is_still_404(self) -> None:
        with serving() as base:
            self.assertEqual(request(base + "/nope", method="TRACE")[0], 404)

    def test_connect_answers_the_same_way_rather_than_pythons_501(self) -> None:
        """The other verb N9 named: a proxy verb is not a tunnel, and it still gets a body."""
        with serving() as base:
            status, body = request(base + "/", method="CONNECT")
            self.assertEqual(status, 405)
            self.assertIn("method_not_allowed", body)
            self.assertNotIn("Unsupported method", body)
            self.assertEqual(request(base + "/nope", method="CONNECT")[0], 404)


# -- 5. the market block counts the excluded rows in the tier it is scoped to ---------


class TestTheBeforeOnSaleMarketBlockCarriesTheTierExcludedCount(unittest.TestCase):
    """Item 5: `0 sales of 0 on this event` under a strip naming 12 excluded rows."""

    def _tier_rows(self, tier_id: str, cut: dt.datetime) -> int:
        data = store()
        tier_of = {ticket["id"]: ticket["tierId"] for ticket in data["tickets"]}
        return sum(
            1
            for row in data["ledger"]
            if row["kind"] == "sale"
            and row["priceLamports"] is not None
            and tier_of.get(row["ticketId"]) == tier_id
            and dt.datetime.fromisoformat(row["occurredAt"].replace("Z", "+00:00")) <= cut
        )

    def test_the_general_tier_names_its_own_nine_excluded_rows(self) -> None:
        cut = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
        self.assertEqual(self._tier_rows("tier_stg_general", cut), 9, "the premise: nine rows in this tier")
        _, html, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        tier = next(row for row in payload["tiers"] if row["selected"])
        self.assertEqual(tier["tierId"], "tier_stg_general")
        self.assertEqual(tier["market"]["sales"]["value"], 0, "the premise: no tier row enters this decision")
        self.assertEqual(payload["decisionMode"]["excludedResales"]["value"], 12, "the strip's count")
        self.assertEqual(payload["decisionMode"]["excludedTierResales"]["value"], 9)
        text = visible(html)
        self.assertIn(
            "in this tier [FIXTURE] 0 sales of [FIXTURE] 0 on this event · "
            "[FIXTURE] 9 recorded sales in this tier are excluded by the mode",
            text,
        )
        # the strip's number and the block's number are the two different facts they are
        self.assertIn("[FIXTURE] 0 resales enter this decision; [FIXTURE] 12 recorded on this event", text)

    def test_the_other_tier_names_its_own_three(self) -> None:
        cut = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
        self.assertEqual(self._tier_rows("tier_stg_front", cut), 3, "the premise: three rows in this tier")
        _, html, payload = page_for(
            event_id="evt_syn_02", mode="before_on_sale", tier_id="tier_stg_front"
        )
        self.assertEqual(payload["decisionMode"]["excludedTierResales"]["value"], 3)
        self.assertIn(
            "[FIXTURE] 3 recorded sales in this tier are excluded by the mode", visible(html)
        )

    def test_a_tier_scoped_count_is_never_larger_than_the_event_one(self) -> None:
        _, _, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        mode = payload["decisionMode"]
        self.assertLessEqual(mode["excludedTierResales"]["value"], mode["excludedResales"]["value"])

    def test_the_counterfactual_page_carries_no_excluded_clause(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_02")
        self.assertIsNone(payload["decisionMode"]["excludedTierResales"])
        text = visible(html)
        self.assertNotIn("are excluded by the mode", text)
        self.assertIn("in this tier [FIXTURE] 9 sales of [FIXTURE] 12 on this event ·", text)

    def test_an_event_with_no_rows_gets_no_clause_about_none(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_08", mode="before_on_sale")
        self.assertEqual(payload["decisionMode"]["excludedTierResales"]["value"], 0)
        self.assertNotIn("recorded sales in this tier are excluded", visible(html))


if __name__ == "__main__":
    unittest.main()
