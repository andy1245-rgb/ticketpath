"""The independent review's fix list, each item held by a test that fails on the old code.

`records/findings/07-engine-review.md` sections 3, 4 and 6 name the defects; this file pins
the repair. Every assertion is written against the rendered page or against a socket, which
is where a reader and a link checker meet the product.

The eight items, in the review's order:

1. the console is total: a pricing exception renders a labelled page, and the three stores
   the loader accepts but the engine cannot price refuse with a typed reason;
2. the two renderer fixes on the judge path stay fixed;
3. the sentences are true (A1's scope, A13's source, A17's completed count, A2/A16 on an
   uncapped event, the zero-sale rate, the fee refusal and the net line);
4. the decision instant is explicit, in two modes, and a completed event's own resales are
   never silently reused as if they had been available beforehand;
5. the [EXACT] ceiling is exact at its displayed precision;
6. the ticket count is cut-aware;
7. the fee arithmetic is integer, bounded, and a negative net is a state;
8. HEAD mirrors GET and POST to the console is a 405.
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
from unittest import mock

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import blocks
from ticketpath.core import labels, primary_optimum
from ticketpath.core.timeutil import parse
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import console_index, make_server

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
FIXTURE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "synthetic_store.json")
COUNTERFACTUAL_SENTENCE = "this is not a price you could have set; it is what the record implies in hindsight"

# The sentences that deny an event's own record rather than say the decision mode excludes it.
# Patterns, not one string: the before-on-sale page said it three ways, and a fix to one of them
# would leave the others. Written against the claim, so the old wording is inside the set.
SENTENCES_THAT_DENY_THE_OWN_RECORD = tuple(
    re.compile(pattern)
    for pattern in (
        r"no resale has been recorded on this event",
        r"this event has no resale record",
        r"this event has no resales",
        r"there are no resales on this event",
        r"no resale rows? exist for this event",
        r"this event sold nothing",
    )
)


# -- harness --------------------------------------------------------------


def orchestrator(ledger: LedgerAdapter | None = None, clock: dt.datetime = CLOCK) -> Orchestrator:
    return Orchestrator(
        ledger or LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: clock,
    )


def page_for(**query) -> tuple[int, str]:
    status, html = console_index(orchestrator(), query, base="http://127.0.0.1:8788")
    return status, html


def visible(html: str) -> str:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", without_style)))


def write_store(store: dict) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(store, handle)
    handle.close()
    return handle.name


def fixture_store() -> dict:
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)


@contextlib.contextmanager
def serving(store: dict | None = None, engine: Orchestrator | None = None):
    """A real server on an ephemeral port, for the states that need a socket."""
    path = write_store(store) if store is not None else None
    led = LedgerAdapter.from_fixture(path) if path else LedgerAdapter.from_fixture()
    server = make_server(0, "127.0.0.1", engine or orchestrator(led))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if path:
            os.unlink(path)


def request(url: str, method: str = "GET") -> tuple[int, dict, str]:
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, dict(response.headers), response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode("utf-8")


# -- item 1: the console is total -----------------------------------------


class TestTheConsoleIsTotal(unittest.TestCase):
    """C1: `console_index` sat outside the handler's try and caught only `ApiError`."""

    def test_a_pricing_exception_renders_a_labelled_page_not_an_empty_reply(self) -> None:
        engine = orchestrator()
        boom = mock.Mock(side_effect=RuntimeError("engine blew up"))
        with mock.patch.object(engine, "price_guidance", boom):
            status, html = console_index(engine, {}, base="http://127.0.0.1:8788")
        self.assertEqual(status, 500)
        self.assertIn("<!doctype html>", html)
        self.assertIn("console_error", visible(html))
        self.assertIn(labels.render("T1"), visible(html))
        self.assertNotIn("Traceback", html)

    def test_the_handler_catches_the_console_too(self) -> None:
        """Belt and braces: the call is inside the handler's try, so even a raise escapes
        into a response. Without the move this closed the connection with no status."""
        with serving() as base, mock.patch(
            "ticketpath.server.console_index", side_effect=RuntimeError("outside the try")
        ):
            status, headers, body = request(base + "/")
            self.assertEqual(status, 500)
            self.assertIn("application/json", headers.get("content-type", ""))
            self.assertIn("internal", body)
            # and the process is still serving
            self.assertEqual(request(base + "/health")[0], 200)

    def test_a_zero_priced_sale_refuses_with_a_typed_reason(self) -> None:
        store = fixture_store()
        for row in store["ledger"]:
            if row["kind"] == "sale" and row["ticketId"].startswith("tkt_syn_") and row["eventId" if False else "id"]:
                row["priceLamports"] = 0
                break
        status, html = self._console(store, {"event": "evt_syn_04"})
        self.assertEqual(status, 422)
        self.assertIn("sale_not_priced", visible(html))
        self.assertIn("<!doctype html>", html)

    def test_a_sale_after_the_event_started_refuses_with_a_typed_reason(self) -> None:
        store = fixture_store()
        events = {row["id"]: row for row in store["events"]}
        by_ticket: dict[str, list[dict]] = {}
        for row in store["ledger"]:
            by_ticket.setdefault(row["ticketId"], []).append(row)
        event_of = {ticket["id"]: ticket["eventId"] for ticket in store["tickets"]}
        moved = False
        for ticket_id, rows in by_ticket.items():
            if event_of[ticket_id] != "evt_syn_04":
                continue
            rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
            if rows[-1]["kind"] == "sale":
                # one hour after the event opened: a negative time-to-event, which the
                # engine may not price and the loader accepts
                rows[-1]["occurredAt"] = "2026-11-14T01:00:00.000Z"
                moved = True
                break
        self.assertTrue(moved)
        self.assertGreater(parse("2026-11-14T01:00:00.000Z"), parse(events["evt_syn_04"]["startsAt"]))
        status, html = self._console(store, {"event": "evt_syn_04", "asOf": "2026-11-14T12:00:00Z"})
        self.assertEqual(status, 422)
        self.assertIn("sale_after_event_start", visible(html))

    def test_an_event_with_no_tier_refuses_with_a_typed_reason(self) -> None:
        store = fixture_store()
        for event in store["events"]:
            if event["id"] == "evt_syn_03":
                event["tiers"] = []
                event.pop("totalSupply", None)
                event.pop("issuedCount", None)
        store["tickets"] = [ticket for ticket in store["tickets"] if ticket["eventId"] != "evt_syn_03"]
        kept = {ticket["id"] for ticket in store["tickets"]}
        store["ledger"] = [row for row in store["ledger"] if row["ticketId"] in kept]
        status, html = self._console(store, {"event": "evt_syn_03"})
        self.assertEqual(status, 422)
        self.assertIn("event_has_no_tier", visible(html))
        self.assertIn(labels.render("P_NO_TIER"), visible(html))

    def test_the_tierless_event_does_not_break_the_default_page(self) -> None:
        store = fixture_store()
        for event in store["events"]:
            if event["id"] == "evt_syn_03":
                event["tiers"] = []
                event.pop("totalSupply", None)
                event.pop("issuedCount", None)
        store["tickets"] = [ticket for ticket in store["tickets"] if ticket["eventId"] != "evt_syn_03"]
        kept = {ticket["id"] for ticket in store["tickets"]}
        store["ledger"] = [row for row in store["ledger"] if row["ticketId"] in kept]
        status, html = self._console(store, {})
        self.assertEqual(status, 200)
        self.assertIn("<!doctype html>", html)

    def _console(self, store: dict, query: dict) -> tuple[int, str]:
        path = write_store(store)
        try:
            engine = orchestrator(LedgerAdapter.from_fixture(path))
            return console_index(engine, query, base="http://127.0.0.1:8788")
        finally:
            os.unlink(path)

    def test_a_malformed_store_still_answers_over_a_socket(self) -> None:
        """The review's `HTTP 000`: no status, no body, connection closed."""
        store = fixture_store()
        for row in store["ledger"]:
            if row["kind"] == "sale":
                row["priceLamports"] = 0
                break
        with serving(store) as base:
            status, headers, body = request(base + "/?event=evt_syn_04")
            self.assertEqual(status, 422)
            self.assertIn("text/html", headers.get("content-type", ""))
            self.assertIn("sale_not_priced", body)


# -- item 2: the two renderer fixes, pinned -------------------------------


class TestTheRendererFixesStayFixed(unittest.TestCase):
    def test_the_cap_violation_sentence_prints_counts_not_wrappers(self) -> None:
        _, html = page_for(event="evt_syn_01", capBps="0")
        text = visible(html)
        self.assertIn("[FIXTURE] 4 of 6 recorded sales", text)
        self.assertNotIn("{'value'", text)
        self.assertNotIn("'badge'", text)

    def test_the_insufficient_marks_refusal_fills_and_badges_its_count(self) -> None:
        _, html = page_for(event="evt_syn_03")
        self.assertIn('<span class="n">[FIXTURE] 0</span> sales is too few to fit a path', html)
        self.assertNotIn("{n}", visible(html))

    def test_the_insufficient_marks_sentence_promises_nothing_that_is_not_drawn(self) -> None:
        text = visible(page_for(event="evt_syn_03")[1])
        self.assertNotIn("flat line below", text)
        self.assertNotIn("flat line", text)


# -- item 3: every label true ---------------------------------------------


class TestA1CountsTheTierAndSaysSo(unittest.TestCase):
    def test_a1_names_the_tier_its_count_comes_from(self) -> None:
        text = visible(page_for(event="evt_syn_01")[1])
        self.assertIn("In this tier the ledger records 6 sales.", text)
        self.assertNotIn("On this event the ledger records 6 sales", text)

    def test_the_strip_and_the_market_block_agree_on_the_event_count(self) -> None:
        text = visible(page_for()[1])
        strip = re.search(r"\[FIXTURE\] (\d+) resales on this event", text)
        market = re.search(r"in this tier \[FIXTURE\] (\d+) sales of \[FIXTURE\] (\d+) on this event", text)
        self.assertIsNotNone(strip, text[:600])
        self.assertIsNotNone(market, text[:600])
        self.assertEqual(strip.group(1), market.group(2), "the event resale count differs between blocks")
        self.assertLessEqual(int(market.group(1)), int(market.group(2)))

    def test_every_event_states_the_tier_scope(self) -> None:
        for event in ("evt_syn_01", "evt_syn_02", "evt_syn_07"):
            with self.subTest(event=event):
                payload = orchestrator().price_guidance(event_id=event)
                tier = blocks.selected_tier(payload)
                text = visible(page_for(event=event)[1])
                self.assertIn(f"In this tier the ledger records {tier['market']['sales']['value']} sale", text)


class TestA13NamesTheBandItUses(unittest.TestCase):
    def test_the_cold_band_is_said_to_be_the_declared_prior(self) -> None:
        text = visible(page_for(event="evt_syn_03")[1])
        self.assertIn("the band is the declared literature prior", text)
        self.assertNotIn("the spread across", text)

    def test_the_band_on_the_page_is_the_one_the_sentence_describes(self) -> None:
        """0.70 x e^(0.2612 -/+ 1.6449 x 0.20) rounded, which is what `prior_only` computes."""
        import math

        face = 700_000_000
        lo = round(face * math.exp(0.2612 - 1.6449 * 0.20))
        hi = round(face * math.exp(0.2612 + 1.6449 * 0.20))
        payload = orchestrator().price_guidance(event_id="evt_syn_03")
        tier = blocks.selected_tier(payload)
        self.assertEqual(tier["band"]["loLamports"]["value"], lo)
        self.assertEqual(tier["band"]["hiLamports"]["value"], hi)


class TestA17CountsCompletedEventsOnce(unittest.TestCase):
    def test_one_completed_count_for_the_whole_page(self) -> None:
        # 2026-11-21T23:30Z: two events have ended (evt_syn_06, evt_syn_04); three started.
        text = visible(page_for(event="evt_syn_03", asOf="2026-11-21T23:30:00Z")[1])
        self.assertEqual(text.count("2 events have completed"), 2, text[text.find("The model is not fitted"):][:400])
        self.assertNotIn("3 events have completed", text)

    def test_the_page_counts_completed_and_not_started(self) -> None:
        payload = orchestrator().price_guidance(event_id="evt_syn_03", as_of="2026-11-21T23:30:00Z")
        self.assertEqual(payload["pooled"]["eventsCompleted"]["value"], 2)
        self.assertNotEqual(payload["pooled"]["eventsInWindow"]["value"], 2)


class TestACapIsOnlyMentionedWhereOneExists(unittest.TestCase):
    def test_the_uncapped_page_never_borrows_the_capped_sentence(self) -> None:
        text = visible(page_for(event="evt_syn_04")[1])
        self.assertIn("This event has no resale cap, so no ceiling enters the bound.", text)
        self.assertNotIn("the resale cap gives a ceiling", text)
        self.assertNotIn("At the cap", text)
        self.assertNotIn("at the ceiling", text)
        self.assertNotIn("the cap is a rule about the future", text)

    def test_a_capped_page_still_says_both(self) -> None:
        text = visible(page_for(event="evt_syn_01")[1])
        self.assertIn("the resale cap gives a ceiling", text)
        self.assertIn("At the cap", text)


class TestTheZeroSaleRateIsNotAMeasuredRate(unittest.TestCase):
    def test_the_badge_the_basis_and_the_sentence_all_name_the_prior(self) -> None:
        payload = orchestrator().price_guidance(event_id="evt_syn_03")
        tier = blocks.selected_tier(payload)
        rate = tier["market"]["per1000TicketDays"]
        self.assertEqual(rate["badge"], "DECLARED")
        self.assertEqual(rate["labelId"], "A1_ZERO")
        self.assertIn("Gamma(1, 1) prior", rate["basis"])
        self.assertIn("0 sales over", rate["basis"])
        text = visible(page_for(event="evt_syn_03")[1])
        self.assertIn("is not measured from the record", text)
        self.assertIn("posterior mean of the declared Gamma(1, 1) prior", text)
        self.assertIn("[DECLARED] 7.", text)  # the number's own badge, in front of it

    def test_zero_sales_means_zero_sales_in_the_strip(self) -> None:
        text = visible(page_for(event="evt_syn_03")[1])
        self.assertIn("[FIXTURE] 0 resales on this event", text)


class TestTheFeeControlIsHonest(unittest.TestCase):
    def test_the_no_fee_refusal_is_conditional_on_no_fee(self) -> None:
        self.assertIn("no_fee_model", visible(page_for(event="evt_syn_02")[1]))
        self.assertNotIn("no_fee_model", visible(page_for(event="evt_syn_02", feeLamports="50000000")[1]))

    def test_the_net_line_renders_when_a_fee_is_set(self) -> None:
        text = visible(page_for(event="evt_syn_02", feeLamports="50000000")[1])
        self.assertIn("Net to the seller per ticket: 1.33 SOL after the declared fee of 0.05 SOL.", text)

    def test_a_fee_above_the_price_is_a_state_not_a_negative_price(self) -> None:
        text = visible(page_for(event="evt_syn_02", feeLamports="5000000000")[1])
        self.assertIn("would leave the seller short by 3.62 SOL per ticket", text)
        self.assertIn("A negative net is not a price", text)
        self.assertNotIn("Net to the seller per ticket:", text)
        self.assertNotIn("-3.62", text)


# -- item 4: the decision instant -----------------------------------------


class TestTheDecisionInstantIsExplicit(unittest.TestCase):
    def test_the_default_page_is_a_labelled_counterfactual(self) -> None:
        text = visible(page_for()[1])
        self.assertIn("Decision mode: COUNTERFACTUAL", text)
        self.assertIn(COUNTERFACTUAL_SENTENCE, text)
        # the event's status and date are beside it
        self.assertIn("status on_sale", text)
        self.assertIn("starts 2026-11-21T23:00:00.000Z", text)
        self.assertIn("decision instant 2026-11-07T12:00:00.000Z", text)

    def test_a_completed_event_is_shown_as_a_hindsight_recomputation(self) -> None:
        status, html = page_for(event="evt_syn_06")
        self.assertEqual(status, 200)
        text = visible(html)
        self.assertIn("Decision mode: COUNTERFACTUAL", text)
        self.assertIn(COUNTERFACTUAL_SENTENCE, text)
        self.assertIn("status completed", text)
        self.assertIn("starts 2026-10-03T23:30:00.000Z", text)

    def test_the_label_is_unmissable(self) -> None:
        _, html = page_for()
        block = re.search(r'<p class="mode">(.*?)</p>', html, flags=re.S)
        self.assertIsNotNone(block)
        self.assertIn(COUNTERFACTUAL_SENTENCE, html_module.unescape(block.group(1)))
        self.assertIn('class="mode"', html)
        self.assertIn("border-left: 8px", html)

    def test_before_on_sale_is_reachable_and_uses_only_other_events(self) -> None:
        status, html = page_for(event="evt_syn_02", mode="before_on_sale")
        self.assertEqual(status, 200)
        text = visible(html)
        self.assertIn("Decision mode: BEFORE-ON-SALE", text)
        self.assertIn("this event's own ledger rows are excluded", text)
        self.assertNotIn("Recommended primary price", text)
        # and the band that is shown is the pooled record of the other events, named as such
        self.assertIn("pooled mean log price-to-face over 4 other events with resale", text)
        # the count in the refusal is the count in the band label: one pool, one number
        refusal = re.search(r"pooled record of (\d+) other events on this platform", text)
        band = re.search(r"pooled mean log price-to-face over (\d+) other events with resale", text)
        self.assertIsNotNone(refusal, text[:2000])
        self.assertEqual(refusal.group(1), band.group(1))

    def test_no_sentence_says_this_event_has_no_resale_record(self) -> None:
        """The event has rows; the mode excludes them, and no sentence may say otherwise.

        The claim class, not one string: anything that tells the reader this event's own
        resales do not exist is false while the store holds them. The premise is asserted
        first, so the test cannot pass by the rows having gone away.
        """
        store = fixture_store()
        own_tickets = {ticket["id"] for ticket in store["tickets"] if ticket["eventId"] == "evt_syn_02"}
        own_sales = [
            row for row in store["ledger"] if row["ticketId"] in own_tickets and row["kind"] == "sale"
        ]
        self.assertGreater(len(own_sales), 0, "the premise: this event does have recorded sales")
        text = visible(page_for(event="evt_syn_02", mode="before_on_sale")[1])
        for claim in SENTENCES_THAT_DENY_THE_OWN_RECORD:
            with self.subTest(claim=claim.pattern):
                self.assertIsNone(
                    claim.search(text),
                    f"the page says {claim.pattern!r} while {len(own_sales)} sale rows exist on this event",
                )
        # what it says instead: the mode excludes the rows, and the pool is named as the source
        self.assertIn("excluded by the BEFORE-ON-SALE decision mode", text)
        self.assertIn("pooled record of 4 other events on this platform", text)

    def test_before_on_sale_refuses_the_value_block_when_there_is_nothing_to_pool(self) -> None:
        store = fixture_store()
        keep = {"evt_syn_02"}
        store["events"] = [event for event in store["events"] if event["id"] in keep]
        kept = {ticket["id"] for ticket in store["tickets"] if ticket["eventId"] in keep}
        store["tickets"] = [ticket for ticket in store["tickets"] if ticket["id"] in kept]
        store["ledger"] = [row for row in store["ledger"] if row["ticketId"] in kept]
        path = write_store(store)
        try:
            engine = orchestrator(LedgerAdapter.from_fixture(path))
            status, html = console_index(engine, {"event": "evt_syn_02", "mode": "before_on_sale"}, base="http://x")
        finally:
            os.unlink(path)
        text = visible(html)
        self.assertEqual(status, 200)
        self.assertIn(labels.render("before_on_sale_no_pool"), text)
        self.assertNotIn("prior band around face", text)

    def test_the_mode_is_in_the_canonical_url_and_the_controls(self) -> None:
        payload = orchestrator().price_guidance(event_id="evt_syn_02", mode="before_on_sale")
        status, html = console_index(orchestrator(), {"event": "evt_syn_02", "mode": "before_on_sale"}, base="http://h")
        self.assertIn("mode=before_on_sale", html)
        self.assertIn('name="mode"', html)
        self.assertNotIn("mode=", console_index(orchestrator(), {}, base="http://h")[1].split("canonical URL")[1][:400])

    def test_a_bad_mode_is_a_400_and_not_a_silent_default(self) -> None:
        status, html = page_for(mode="whenever")
        self.assertEqual(status, 400)
        self.assertIn("mode_invalid", visible(html))


# -- item 5: the [EXACT] line ---------------------------------------------


class TestTheExactLineIsExact(unittest.TestCase):
    def test_the_ceiling_is_printed_in_lamports_with_its_own_multiplication(self) -> None:
        text = visible(page_for(event="evt_syn_07")[1])
        self.assertIn(
            "[EXACT] ceiling 1,125,000,000 lamports = face 900,000,000 lamports "
            "× (10,000 + 2500) / 10,000",
            text,
        )
        self.assertIn("That is exactly 1.125 SOL.", text)
        self.assertEqual(900_000_000 * 12_500 // 10_000, 1_125_000_000)
        self.assertNotIn("1.12 SOL = face 0.90 SOL", text)

    def test_every_binding_event_prints_an_equality_that_holds(self) -> None:
        for event in ("evt_syn_02", "evt_syn_07"):
            with self.subTest(event=event):
                text = visible(page_for(event=event)[1])
                match = re.search(r"ceiling ([\d,]+) lamports = face ([\d,]+) lamports × \(10,000 \+ (\d+)\) / 10,000", text)
                self.assertIsNotNone(match, text[:800])
                ceiling, face, cap = (int(value.replace(",", "")) for value in match.groups())
                self.assertEqual(ceiling, face * (10_000 + cap) // 10_000)


# -- item 6: the ticket count is cut-aware --------------------------------


class TestTheTicketCountIsCutAware(unittest.TestCase):
    def test_a_cut_before_the_first_issue_counts_no_ticket(self) -> None:
        text = visible(page_for(event="evt_syn_02", asOf="2026-09-01T00:00:00Z")[1])
        self.assertIn("[FIXTURE] 0 tickets", text)
        self.assertNotIn("[FIXTURE] 12 tickets", text)

    def test_the_count_is_the_issue_rows_at_the_cut(self) -> None:
        store = fixture_store()
        cut = parse("2026-09-01T00:00:00Z")
        event_tickets = {ticket["id"] for ticket in store["tickets"] if ticket["eventId"] == "evt_syn_02"}
        issued = {
            row["ticketId"]
            for row in store["ledger"]
            if row["ticketId"] in event_tickets and row["kind"] == "issue" and parse(row["occurredAt"]) <= cut
        }
        payload = orchestrator().price_guidance(event_id="evt_syn_02", as_of="2026-09-01T00:00:00Z")
        self.assertEqual(payload["evidence"]["tickets"]["value"], len(issued))
        self.assertEqual(payload["evidence"]["tickets"]["value"], 0)

    def test_a_later_cut_counts_the_tickets_issued_by_then(self) -> None:
        """The count is the issue rows at or before the cut, and it moves with the cut.

        The assertion it replaces compared the count to itself. The hand count is taken
        from the store's own issue rows, so a count that ignores the cut (12 at every
        instant) fails on the first cut and a count that ignores issue rows fails on both.
        """
        store = fixture_store()
        own_tickets = {ticket["id"] for ticket in store["tickets"] if ticket["eventId"] == "evt_syn_02"}
        issues = [
            row for row in store["ledger"] if row["ticketId"] in own_tickets and row["kind"] == "issue"
        ]
        instants = sorted(row["occurredAt"] for row in issues)
        self.assertGreater(len(instants), 1, "the store must issue at more than one instant")
        engine = orchestrator()
        counts = []
        for cut in ("2026-09-01T00:00:00Z", instants[0], instants[-1]):
            expected = sum(1 for row in issues if parse(row["occurredAt"]) <= parse(cut))
            count = engine.price_guidance(event_id="evt_syn_02", as_of=cut)["evidence"]["tickets"]["value"]
            self.assertEqual(count, expected, f"count at {cut}")
            counts.append(count)
        self.assertLess(counts[0], counts[1])
        self.assertLess(counts[1], counts[2])


# -- item 7: fee arithmetic ------------------------------------------------


class TestTheFeeArithmetic(unittest.TestCase):
    def test_the_net_line_is_integer_arithmetic(self) -> None:
        """A float anywhere in this path changes a lamport, and one lamport is a wrong number.

        The page's own fee control carries a per-ticket fee only, so `gross - fee` is the
        same answer in a float and in an integer there: the earlier version of this test
        compared the payload to `gross - fee` and passed with float arithmetic restored. The
        money path's other half -- the half-up rounding of
        `(price * (10000 - ad_valorem) + 5000) // 10000` -- is where the two differ, so that
        is asserted directly on the function that owns it, with values only integer
        arithmetic produces.
        """
        payload = orchestrator().price_guidance(event_id="evt_syn_02", fee_lamports="50000000")
        recommendation = blocks.selected_tier(payload)["recommendation"]
        gross = recommendation["recommendedLamports"]["value"]
        net = recommendation["netRevenue"]["perTicket"]["value"]
        self.assertIsInstance(net, int)
        self.assertEqual(net, gross - 50_000_000)

        for price, ad_valorem, expected in (
            # 930,549,431 x 5000 / 10000 is x.5: rounding up gives ...716, truncating ...715
            (930_549_431, 5000, 465_274_716),
            # beyond 2**53 a float cannot hold the product: every float form gives ...496
            (2**53 + 1, 5000, 4_503_599_627_370_497),
        ):
            with self.subTest(price=price, ad_valorem=ad_valorem):
                out = primary_optimum.recommend(
                    features={
                        "tiers": [
                            {
                                "tierId": "t",
                                "faceValueLamports": 1_000_000_000,
                                "sellThrough": 0.5,
                                "issuedCount": 2,
                                "marks": [],
                            }
                        ]
                    },
                    tier_id="t",
                    band={
                        "regime": "uncapped",
                        "floorLamports": None,
                        "level": {"available": True, "lamports": price, "basis": "level"},
                        "band": {"loLamports": price, "hiLamports": price},
                    },
                    intensity={},
                    fee={"perTicketLamports": 0, "adValoremBps": ad_valorem},
                    sell_through_floor=None,
                    candidates=[price],
                )
                self.assertEqual(out["netRevenue"]["perTicket"], expected)
                self.assertIsInstance(out["netRevenue"]["perTicket"], int)

    def test_a_fee_past_the_maximum_is_refused_before_it_is_computed(self) -> None:
        status, html = page_for(event="evt_syn_02", feeLamports="999999999999999999999")
        self.assertEqual(status, 400)
        self.assertIn("fee_invalid", visible(html))

    def test_the_maximum_fee_is_accepted_and_still_renders_a_state(self) -> None:
        payload = orchestrator().price_guidance(event_id="evt_syn_02", fee_lamports=str(10**15))
        net = blocks.selected_tier(payload)["recommendation"]["netRevenue"]
        self.assertTrue(net["negative"])

    def test_a_negative_net_is_not_rendered_as_a_price(self) -> None:
        text = visible(page_for(event="evt_syn_02", feeLamports="5000000000")[1])
        self.assertIn("[REFUSED] The declared fee", text)
        self.assertNotIn("[EXACT] Net to the seller per ticket: -", text)


# -- item 8: headers and methods ------------------------------------------


class TestMethodsAndHeaders(unittest.TestCase):
    def test_head_mirrors_the_get_headers(self) -> None:
        with serving() as base:
            get_status, get_headers, get_body = request(base + "/")
            head_status, head_headers, head_body = request(base + "/", method="HEAD")
        self.assertEqual(head_status, 200)
        self.assertEqual(head_status, get_status)
        self.assertIn("text/html", head_headers.get("content-type", ""))
        self.assertEqual(head_headers.get("content-length"), str(len(get_body.encode("utf-8"))))
        self.assertEqual(head_body, "")

    def test_post_to_the_console_is_405_not_404(self) -> None:
        with serving() as base:
            status, headers, body = request(base + "/", method="POST")
        self.assertEqual(status, 405)
        self.assertIn("method_not_allowed", body)

    def test_an_unknown_path_is_still_404(self) -> None:
        with serving() as base:
            self.assertEqual(request(base + "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
