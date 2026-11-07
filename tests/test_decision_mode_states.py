"""Property (d): the mode sentence is true at the printed instant, one test per state class.

`records/findings/12-final-audit.md` measured 360 grid states and found 60 (d) violations,
all of them the same defect: the before-on-sale mode sentence claimed the decision is taken
before this event's first ticket is issued, at instants when the page itself printed 12 to 16
tickets and resales as excluded by the mode. It also read two reader-facing claims that its
counted rule did not catch: the counterfactual said `this event's own completed record ...
in hindsight` on the default page, whose event starts in 14 days, and on the cold-start page,
which prints `No resale has been recorded on this event` four lines above it.

The fix is mode logic and wording only: the orchestrator measures which record the instant
actually has, and the sentence is chosen from that. No number in the payload moves.

Each test below is written against the rendered page and the store at the cut, and each one
fails on the tree the audit measured (`dd07282`), where every state printed the two fixed
words. The assertions are grouped by the seven states the vocabulary names:

    before_first_ticket   no issue row at or before the instant
    issued_no_resale      tickets issued, no priced sale at the instant, none later either
    issued_no_resale_yet  tickets issued, no sale at the instant, one later
    in_market             sales at the instant, the run has not ended
    ended_no_resale       the run has ended and holds no priced sale at the instant
    ended_no_ticket       the run has ended and no ticket was issued at the instant
    ended_with_resales    the run has ended with priced sales on the record
    cancelled             the store's own status says the event was called off

The last three classes are the ones the audit named as the requirement: a completed event with
resales, an event with no resales at any instant, an event cancelled (the schema carries the
status; the shipped fixture has no such row, so the test writes one).
"""

from __future__ import annotations

import datetime as dt
import html as html_module
import json
import os
import re
import tempfile
import unittest

from ticketpath import orchestrator as orchestrator_module
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.core import labels
from ticketpath.core.timeutil import parse
from ticketpath.orchestrator import Orchestrator

# The vocabulary is read off the module rather than imported by name so this file can be
# dropped into the tree the audit measured (`dd07282`) and each state fails on its own
# sentence, instead of the whole file failing to import. The build report records that run.
RECORD_STATES = getattr(
    orchestrator_module,
    "RECORD_STATES",
    (
        "before_first_ticket",
        "issued_no_resale",
        "issued_no_resale_yet",
        "in_market",
        "ended_no_resale",
        "ended_no_ticket",
        "ended_with_resales",
        "cancelled",
    ),
)

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "synthetic_store.json"
)

# The two halves of the old fixed sentence, each true of exactly one state.
COMPLETED_RECORD_CLAIM = "this event's own completed record"
HINDSIGHT_CLAIM = "it is what the record implies in hindsight"
# The guarantee a counterfactual carries in every state.
NOT_A_PRICE_CLAUSE = "not a price you could have set"
# The premise the before-on-sale sentence may print only where it is true.
FIRST_ISSUE_PREMISE = "before this event's first ticket is issued"
# The guarantee a before-on-sale page carries in every state: the event's own rows never enter.
OWN_ROWS_EXCLUDED = "ledger rows are excluded"
OWN_ROWS_NEVER_READ = "never reads this event's own ledger rows"
OWN_ROWS_NONE_TO_EXCLUDE = "holds no row for the mode to exclude"


def fixture_store() -> dict:
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)


def write_store(data: dict) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, handle)
    handle.close()
    return handle.name


def orchestrator(ledger: LedgerAdapter | None = None, clock: dt.datetime = CLOCK) -> Orchestrator:
    return Orchestrator(
        ledger or LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: clock,
    )


def page_for(ledger: LedgerAdapter | None = None, clock: dt.datetime = CLOCK, **query):
    """The page and the payload it was rendered from, the pair the console route makes."""
    payload = orchestrator(ledger, clock).price_guidance(**query)
    payload["canonicalUrl"] = "http://127.0.0.1:8788/?"
    return 200, page.render(payload), payload


def visible(html: str) -> str:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", without_style)))


def mode_sentence(text: str) -> str:
    """The one sentence the mode label contributes, and nothing after it."""
    found = re.search(r"Decision mode: (?:COUNTERFACTUAL|BEFORE-ON-SALE)\..*?(?= Event | A cap )", text)
    if found is None:
        raise AssertionError(f"no mode sentence on the page: {text[:400]}")
    return found.group(0)


def rows_for(store: dict, event_id: str, cut: dt.datetime) -> dict:
    """The store's own answer to "what does this event's record hold at this instant".

    Read from `fixtures/synthetic_store.json`, never from the page: resales at the cut,
    tickets at the cut, and resales at any instant.
    """
    own = {t["id"] for t in store["tickets"] if t["eventId"] == event_id}
    sale = lambda row: row["kind"] == "sale" and row.get("priceLamports") is not None  # noqa: E731
    priced = [row for row in store["ledger"] if row["ticketId"] in own and sale(row)]
    at_cut = [row for row in store["ledger"] if row["ticketId"] in own and parse(row["occurredAt"]) <= cut]
    return {
        "resales_at_cut": sum(1 for row in at_cut if sale(row)),
        "tickets_at_cut": len({row["ticketId"] for row in at_cut if row["kind"] == "issue"}),
        "resales_in_store": len(priced),
    }


def state_of(event: dict, rows: dict, cut: dt.datetime) -> str:
    """The state the page must report, from the definition in the audit's section 3.

    Restated here rather than imported from the orchestrator, so the page and this test agree
    only if both are true of the store.
    """
    if event["status"] == "cancelled":
        return "cancelled"
    ends_at = event.get("endsAt") or event["startsAt"]
    ended = parse(ends_at) <= cut
    if ended and rows["resales_at_cut"]:
        return "ended_with_resales"
    if ended and rows["tickets_at_cut"]:
        return "ended_no_resale"
    if ended:
        return "ended_no_ticket"
    if rows["resales_at_cut"]:
        return "in_market"
    if rows["tickets_at_cut"]:
        return "issued_no_resale_yet" if rows["resales_in_store"] else "issued_no_resale"
    return "before_first_ticket"


class TestTheModeSentenceDescribesTheRecordItHas(unittest.TestCase):
    """One test per state class. Each asserts the claim that state may make, and the one it may not."""

    def assert_reads(
        self,
        text: str,
        *,
        must: tuple[str, ...] = (),
        must_not: tuple[str, ...] = (),
        where: str = "",
    ) -> None:
        for phrase in must:
            self.assertIn(phrase, text, f"{where}: the page must say {phrase!r}")
        for phrase in must_not:
            self.assertNotIn(phrase, text, f"{where}: the page may not say {phrase!r}")

    # 1. Before its on-sale, nothing issued: there is no record of this event's prices.
    def test_before_the_first_ticket_the_page_does_not_claim_a_record(self) -> None:
        """`evt_syn_08` has issued nothing, and `evt_syn_02` at 2026-07-01 has issued nothing yet."""
        for event_id, clock in (
            ("evt_syn_08", CLOCK),
            ("evt_syn_02", dt.datetime(2026, 7, 1, tzinfo=UTC)),
        ):
            with self.subTest(event=event_id, clock=clock.date()):
                _, html, payload = page_for(clock=clock, event_id=event_id)
                text = visible(html)
                self.assert_reads(
                    mode_sentence(text),
                    must=(NOT_A_PRICE_CLAUSE, "first ticket has not been issued"),
                    must_not=(COMPLETED_RECORD_CLAIM, HINDSIGHT_CLAIM),
                    where="before_first_ticket",
                )
                # and the whole page carries no completed-record claim either
                self.assertNotIn(COMPLETED_RECORD_CLAIM, text)
                self.assertEqual(payload["decisionMode"]["recordState"], "before_first_ticket")
                self.assertEqual(
                    payload["decisionMode"]["labelId"], "P_MODE_COUNTERFACTUAL_NOT_STARTED"
                )

    # 2. In market with resales: a partial record, not a finished one, not hindsight.
    def test_an_event_in_market_is_not_a_completed_record(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_02")
        text = visible(html)
        self.assert_reads(
            mode_sentence(text),
            must=(NOT_A_PRICE_CLAUSE, "record as it stands at this decision instant"),
            must_not=(COMPLETED_RECORD_CLAIM, HINDSIGHT_CLAIM),
            where="in_market",
        )
        # the premise the state contradicts: the event starts 14 days after the instant
        self.assertIn("starts 2026-11-21T23:00:00.000Z", text)
        self.assertIn("decision instant 2026-11-07T12:00:00.000Z", text)
        self.assertEqual(payload["decisionMode"]["recordState"], "in_market")
        self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_COUNTERFACTUAL_OPEN")

    # 3. Completed with resales: the always-accepted reading, kept.
    def test_a_completed_event_keeps_the_hindsight_reading(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_06")
        text = visible(html)
        self.assert_reads(
            mode_sentence(text),
            must=(COMPLETED_RECORD_CLAIM, HINDSIGHT_CLAIM, NOT_A_PRICE_CLAUSE),
            where="ended_with_resales",
        )
        self.assertEqual(payload["decisionMode"]["recordState"], "ended_with_resales")
        self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_COUNTERFACTUAL")

    # 4. No resales at any instant: the record is empty, so the band is the prior.
    def test_an_event_with_no_resale_at_any_instant_says_the_record_is_empty(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_03")
        text = visible(html)
        self.assert_reads(
            mode_sentence(text),
            must=("holds no resale at any instant", "declared prior", NOT_A_PRICE_CLAUSE),
            must_not=(COMPLETED_RECORD_CLAIM, HINDSIGHT_CLAIM),
            where="issued_no_resale",
        )
        # the page's own refusal and the state sentence agree instead of contradicting
        self.assertIn("No resale has been recorded on this event", text)
        self.assertEqual(payload["decisionMode"]["recordState"], "issued_no_resale")
        self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_COUNTERFACTUAL_NO_RESALE_AT_ALL")

    # 5. Cancelled: the schema carries the status, so the sentence must handle it.
    def test_a_cancelled_event_is_read_as_cancelled(self) -> None:
        data = fixture_store()
        for event in data["events"]:
            if event["id"] == "evt_syn_02":
                event["status"] = "cancelled"
        path = write_store(data)
        try:
            ledger = LedgerAdapter.from_fixture(path)
            _, html, payload = page_for(ledger=ledger, event_id="evt_syn_02")
            text = visible(html)
            self.assert_reads(
                mode_sentence(text),
                must=("records this event as cancelled", NOT_A_PRICE_CLAUSE),
                must_not=(COMPLETED_RECORD_CLAIM, HINDSIGHT_CLAIM),
                where="cancelled",
            )
            self.assertEqual(payload["decisionMode"]["recordState"], "cancelled")
            self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_COUNTERFACTUAL_CANCELLED")
            _, html, payload = page_for(ledger=ledger, event_id="evt_syn_02", mode="before_on_sale")
            text = visible(html)
            self.assert_reads(
                mode_sentence(text),
                must=("records this event as cancelled", OWN_ROWS_NEVER_READ),
                must_not=(FIRST_ISSUE_PREMISE,),
                where="cancelled, before-on-sale",
            )
            self.assertEqual(payload["decisionMode"]["recordState"], "cancelled")
            self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_BEFORE_CANCELLED")
        finally:
            os.unlink(path)

    # 6. Before-on-sale, after the first issue: the premise is gone, the exclusion stays.
    def test_a_before_on_sale_page_does_not_claim_resales_the_record_lacks(self) -> None:
        """`evt_syn_03` has issued 10 tickets and recorded no resale at any instant."""
        _, html, payload = page_for(event_id="evt_syn_03", mode="before_on_sale")
        text = visible(html)
        self.assert_reads(
            mode_sentence(text),
            must=(OWN_ROWS_EXCLUDED, "already has tickets on its record but no resale"),
            must_not=("resales on its record", FIRST_ISSUE_PREMISE),
            where="issued_no_resale, before-on-sale",
        )
        self.assertEqual(payload["decisionMode"]["recordState"], "issued_no_resale")
        self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_BEFORE_NO_RESALE")

    def test_the_before_on_sale_premise_is_printed_only_where_it_is_true(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        text = visible(html)
        self.assert_reads(
            mode_sentence(text),
            must=(OWN_ROWS_EXCLUDED, "not the price the organizer could have charged"),
            must_not=(FIRST_ISSUE_PREMISE,),
            where="in_market, before-on-sale",
        )
        self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_BEFORE_ISSUED")
        # the same mode at an instant before the first issue keeps the premise, because it is true
        clock = dt.datetime(2026, 7, 1, tzinfo=UTC)
        _, html, payload = page_for(clock=clock, event_id="evt_syn_02", mode="before_on_sale")
        self.assertEqual(payload["decisionMode"]["labelId"], "P_MODE_BEFORE")
        self.assertIn(labels.render("P_MODE_BEFORE"), visible(html))

    # 7. The status field ahead of the instant: named as the store's field, not the instant's.
    def test_a_completed_status_before_the_recorded_end_is_named_as_the_field(self) -> None:
        """`evt_syn_06` is `completed` and its recorded end is 90 minutes after the cut."""
        clock = dt.datetime(2026, 10, 4, 0, 30, tzinfo=UTC)
        _, html, payload = page_for(clock=clock, event_id="evt_syn_06")
        text = visible(html)
        self.assert_reads(
            text,
            must=(
                "status completed is the store's current field",
                "The instant is before the recorded end, so at that instant the event had not ended",
            ),
            must_not=("the field and the instant disagree",),
            where="field ahead of the instant",
        )
        self.assertEqual(payload["decisionMode"]["recordState"], "in_market")


class TestEveryStateKeepsBothGuarantees(unittest.TestCase):
    """The two distinctions the earlier review required, asserted on every state.

    A counterfactual recomputation is never presented as a price the organizer could have set,
    and a before-on-sale decision never uses this event's own rows. Both survive the rewording
    across the whole grid: 8 events, both modes, four instants, both tiers where an event has
    two.
    """

    def test_no_state_claims_a_record_or_a_premise_the_instant_contradicts(self) -> None:
        data = fixture_store()
        events = {event["id"]: event for event in data["events"]}
        checked = 0
        for event_id, event in sorted(events.items()):
            cuts = [
                dt.datetime(2026, 7, 1, tzinfo=UTC),
                parse(event["startsAt"]) + dt.timedelta(hours=1),
                parse(event["endsAt"]) + dt.timedelta(days=10),
                CLOCK,
            ]
            for cut in cuts:
                rows = rows_for(data, event_id, cut)
                for mode in ("counterfactual", "before_on_sale"):
                    with self.subTest(event=event_id, cut=cut.isoformat(), mode=mode):
                        _, html, payload = page_for(
                            clock=cut,
                            event_id=event_id,
                            mode=mode,
                            as_of=cut.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        )
                        text = visible(html)
                        sentence = mode_sentence(text)
                        ended = parse(event.get("endsAt") or event["startsAt"]) <= cut
                        # (i) the guarantee each mode carries, in every state
                        if mode == "counterfactual":
                            self.assertIn(NOT_A_PRICE_CLAUSE, sentence)
                        else:
                            self.assertTrue(
                                OWN_ROWS_EXCLUDED in sentence
                                or OWN_ROWS_NEVER_READ in sentence
                                or OWN_ROWS_NONE_TO_EXCLUDE in sentence,
                                sentence,
                            )
                        # (ii) no completed-record claim before the run has ended
                        if not ended or event["status"] == "cancelled":
                            self.assertNotIn(COMPLETED_RECORD_CLAIM, sentence)
                            self.assertNotIn(HINDSIGHT_CLAIM, sentence)
                        # (ii-b) no claim of a row the store does not hold at the instant: a
                        # sentence may not say the event has resales where it has none, nor
                        # tickets where none have been issued
                        if not rows["resales_at_cut"]:
                            self.assertNotIn("resales on its record", sentence)
                        if not rows["tickets_at_cut"]:
                            self.assertNotIn("already has tickets", sentence)
                        # (iii) the before-on-sale premise only where no ticket has been issued
                        if not rows["tickets_at_cut"]:
                            if mode == "before_on_sale" and not ended and event["status"] != "cancelled":
                                self.assertIn(FIRST_ISSUE_PREMISE, sentence)
                        else:
                            self.assertNotIn(FIRST_ISSUE_PREMISE, text)
                        # (iv) the page reports the state the store gives
                        state = payload["decisionMode"]["recordState"]
                        self.assertIn(state, RECORD_STATES)
                        self.assertEqual(state, state_of(event, rows, cut))
                        checked += 1
        self.assertEqual(checked, 8 * 4 * 2)


class TestTheModeExcludedLabelsAreScoped(unittest.TestCase):
    """The three labels beside the excluded rows said the tier had no record at all."""

    def test_the_regime_chip_does_not_deny_the_rows_the_mode_excludes(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        text = visible(html)
        self.assertEqual(payload["decisionMode"]["excludedTierResales"]["value"], 9, "the premise")
        self.assertIn("regime [FIXTURE] no sale in this decision", text)
        self.assertNotIn("regime [FIXTURE] no resale", text)

    def test_the_insufficient_marks_refusal_says_whose_zero_it_is(self) -> None:
        _, html, payload = page_for(event_id="evt_syn_02", mode="before_on_sale")
        text = visible(html)
        self.assertEqual(payload["decisionMode"]["excludedResales"]["value"], 12, "the premise")
        self.assertIn("[FIXTURE] 0 sales enter this decision, which is too few to fit a path", text)
        self.assertNotIn("[FIXTURE] 0 sales is too few to fit a path", text)

    def test_the_rationing_sentence_is_printed_only_where_a_sale_sits_on_the_ceiling(self) -> None:
        zero_tier = visible(page_for(event_id="evt_syn_01")[1])
        self.assertIn("at the ceiling [FIXTURE] 0", zero_tier)
        self.assertIn(labels.render("A16_NONE"), zero_tier)
        self.assertNotIn(labels.render("A16"), zero_tier)
        sold_at_ceiling = visible(page_for(event_id="evt_syn_02")[1])
        self.assertIn(labels.render("A16"), sold_at_ceiling)


if __name__ == "__main__":
    unittest.main()
