"""The presentation pass, locked: six defects a reader could see, each one testable.

These are not new rules. Every assertion below is a property the page was always meant to
have and did not: one badge per fact, one statement of a fact per place, a sentence instead
of `None`, a count of one that reads as singular, one name for one quantity, one precision
inside one row. They are written against the rendered page, because that is where a reader
met them, and they read the same stripped text a reader would.

The states are the ones a URL can reach: the four fixtures, the two instants that put one
event (and one sale) in the observation window, a cap below every recorded price, and the
simulation.
"""

from __future__ import annotations

import datetime as dt
import html as html_module
import re
import tempfile
import unittest
from pathlib import Path

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
BADGE = r"\[(?:FIXTURE|DECLARED|EXACT|UNVALIDATED|REFUSED|DESIGN|SIMULATED|DEVNET)\]"
# A path no run creates, so the absent state is reachable without touching the real artefact.
MISSING_ARTEFACT = Path(tempfile.gettempdir()) / "ticketpath-no-such-artefact.json"

STATES = (
    {},
    {"event_id": "evt_syn_03"},
    {"event_id": "evt_syn_04"},
    {"event_id": "evt_syn_08"},
    {"event_id": "evt_syn_01", "as_of": "2026-09-01T00:00:00Z"},
    {"event_id": "evt_syn_01", "as_of": "2026-10-01T00:00:00Z"},
    {"event_id": "evt_syn_01", "cap_bps": "0"},
    {"show_sim": True},
)


def render(**kwargs) -> tuple[dict, str]:
    # `artefact_path` is the chain slot's own seam: naming a missing file reaches the absent
    # state without moving the operator's proven record.
    artefact_path = kwargs.pop("artefact_path", None)
    engine = Orchestrator(
        ledger=LedgerAdapter.from_fixture(),
        rpc=RpcAdapter.from_env("devnet"),
        pricing_model=PricingModelAdapter(),
        cluster="devnet",
        now=lambda: CLOCK,
        artefact_path=artefact_path,
    )
    payload = engine.price_guidance(**kwargs)
    payload["canonicalUrl"] = "http://127.0.0.1:8788/?event=evt&tier=tier"
    return payload, page.render(payload)


def visible_text(html: str) -> str:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return html_module.unescape(re.sub(r"<[^>]+>", " ", without_style))


class TestOneBadgePerFact(unittest.TestCase):
    """Defect 1: `[FIXTURE] [FIXTURE] 12` and `[DEVNET] [DEVNET] 0` on one fact."""

    def test_no_badge_is_printed_outside_the_span_that_carries_one(self) -> None:
        for state in STATES:
            _, html = render(**state)
            with self.subTest(state=state):
                self.assertIsNone(re.search(BADGE + r"\s*<span class=\"n\">", html))

    def test_no_span_carries_two_badges(self) -> None:
        for state in STATES:
            _, html = render(**state)
            for span in re.findall(r'<span class="n">(.*?)</span>', html, flags=re.S):
                with self.subTest(state=state, span=span[:50]):
                    self.assertIsNone(re.search(BADGE + r"\s*" + BADGE, span))


class TestTheBannerSaysItOnce(unittest.TestCase):
    """Defect 2: the cluster sentence in the second and third lines of the banner."""

    def test_the_banner_makes_no_claim_about_any_cluster(self) -> None:
        """Defect 2 was the cluster sentence printed twice. It is now printed nowhere here.

        The banner said "No program is deployed on any cluster", and the chain slot repeated
        it. That sentence is false once a devnet artefact exists (feature 2), so the banner
        names where the two kinds of evidence live instead, and the chain facts are printed
        in the slot with their own sources. Asserted in the stronger direction: the banner
        carries no cluster claim at all, so the defect cannot recur in it.
        """
        _, html = render()
        banner = html[html.index('<div class="banner"') : html.index("</div>", html.index('<div class="banner"'))]
        text = html_module.unescape(re.sub(r"<[^>]+>", " ", banner))
        self.assertNotIn("no program is deployed", text.lower())
        self.assertNotIn("program deployed", text.lower())
        self.assertEqual(text.lower().count("deployed guarantee"), 1, text)

    def test_every_page_says_what_it_did_not_read(self) -> None:
        """The slot's own disclaimer, in whichever form is true of the file.

        T5 where no artefact verified, and the recorded-block sentence where one did: a page
        that renders a real devnet transaction must still say this server asked no cluster.
        """
        for state in STATES:
            _, html = render(**state)
            text = visible_text(html)
            with self.subTest(state=state):
                self.assertTrue(
                    labels.render("T5") in text or labels.render("P_CHAIN_NOT_ASKED") in text,
                    text[-400:],
                )

    def test_t5_is_on_the_panel_when_nothing_verified(self) -> None:
        _, html = render(artefact_path=MISSING_ARTEFACT)
        text = visible_text(html)
        self.assertEqual(text.count("[DEVNET] " + labels.render("T5")), 1)


class TestNoNoneInProse(unittest.TestCase):
    """Defect 3: "The 6 resales span None days and stop 52.3 days before the event"."""

    def test_a_missing_span_reads_as_a_sentence(self) -> None:
        # evt_syn_01 at the server clock already refuses on outside_support with the span
        # present (13.4 days); remove the span and the sentence must still read.
        payload, _ = render(event_id="evt_syn_01")
        for tier in payload["tiers"]:
            if tier["selected"]:
                # the payload shape `guidance.num(None)` produces, and the one
                # `path_model._refused` defaults to
                tier["path"]["spreadDays"]["value"] = None
        text = visible_text(page.render(payload))
        self.assertNotIn("None", text)
        self.assertIn("resales stop", text)
        self.assertIn("outside the window the record covers. No path value is quoted.", text)

    def test_the_sentence_is_unchanged_when_the_span_is_present(self) -> None:
        text = visible_text(render(event_id="evt_syn_01")[1])
        self.assertIn("The 6 resales span 13.4 days and stop 52.3 days before the event", text)


class TestACountOfOneIsSingular(unittest.TestCase):
    """Defect 4: `1 events have completed`, `1 tickets`, `1 sales`."""

    def test_no_plural_noun_follows_a_count_of_one(self) -> None:
        for state in STATES:
            text = visible_text(render(**state)[1])
            with self.subTest(state=state):
                for wrong in (
                    r"\b1 events\b",
                    r"\b1 sales\b",
                    r"\b1 resales\b",
                    r"\b1 tickets\b",
                    r"\b1 other events\b",
                    r"\b1 on-chain transactions\b",
                    r"and 1 have any resale activity",
                ):
                    self.assertIsNone(re.search(wrong, text), wrong)

    def test_the_singular_forms_are_the_ones_printed(self) -> None:
        # evt_syn_03 at the default cut: one event has completed and five have a resale, so
        # the completed count is singular and the resale count is not.
        cold = visible_text(render(event_id="evt_syn_03")[1])
        self.assertIn("The model is not fitted. One event has completed", cold)
        self.assertIn("and 5 have any resale activity", cold)
        # The cold band is the declared literature prior and the sentence now says so. It
        # used to claim it was "the spread across one other event", which it never was.
        self.assertIn("the band is the declared literature prior", cold)
        self.assertNotIn("the spread across", cold)
        one_sale = visible_text(render(event_id="evt_syn_01", as_of="2026-10-01T00:00:00Z")[1])
        self.assertIn("the ledger records one sale.", one_sale)


class TestOneNameForOneQuantity(unittest.TestCase):
    """Defect 5: `Band 0.74 – 1.25 SOL` and then `Range: 0.74 to 1.25 SOL`."""

    def test_the_band_is_named_and_given_once(self) -> None:
        _, html = render(event_id="evt_syn_01")
        text = visible_text(html)
        self.assertEqual(text.count("Band 0.74 – 1.25 SOL."), 1)
        self.assertNotIn("Range: 0.74 to 1.25 SOL.", text)
        self.assertIn("We would not argue with any price in that range.", text)

    def test_the_binding_block_never_names_a_band(self) -> None:
        text = visible_text(render()[1])
        self.assertNotIn("Band ", text)
        self.assertIn("Value: at least 1.38 SOL per ticket.", text)


class TestConsistentPresentation(unittest.TestCase):
    """The two also-checks: one precision inside a row, one unit for one quantity."""

    def test_both_markups_in_the_row_carry_the_same_decimals(self) -> None:
        match = re.search(
            r"median markup\s+" + BADGE + r"\s+([\d.]+)%\s+·\s+mean markup\s+" + BADGE + r"\s+([\d.]+)%",
            visible_text(render()[1]),
        )
        self.assertIsNotNone(match)
        decimals = [len(value.split(".")[1]) if "." in value else 0 for value in match.groups()]
        self.assertEqual(decimals[0], decimals[1], match.group(0))

    def test_a_unit_is_printed_once_per_number(self) -> None:
        for state in STATES:
            text = visible_text(render(**state)[1])
            with self.subTest(state=state):
                self.assertNotIn("ticket-days ticket-days", text)


class TestNoPayloadShapesInProse(unittest.TestCase):
    """The two leaks named in BUILD-REPORT-CONSOLE.md and left for this pass.

    Both were the payload's own repr or an unfilled template reaching the page: `esc()`
    applied to a number wrapper instead of its value, and a refusal rendered with no
    fields so `str.format` never ran.
    """

    def test_the_cap_violation_paragraph_prints_a_count_not_a_wrapper(self) -> None:
        _, html = render(event_id="evt_syn_01", cap_bps="0")
        text = visible_text(html)
        self.assertNotIn("{'value'", text)
        self.assertIn("[FIXTURE] 4 of 6 recorded sales", text)

    def test_the_insufficient_marks_refusal_fills_its_count_and_badges_it(self) -> None:
        for state in ({"event_id": "evt_syn_03"}, {"event_id": "evt_syn_08"}):
            _, html = render(**state)
            with self.subTest(state=state):
                self.assertIn(
                    '<span class="n">[FIXTURE] 0</span> sales is too few to fit a path, '
                    "so no path is quoted.",
                    html,
                )
                self.assertNotIn("{n}", visible_text(html))
                # no path is drawn anywhere on the page, so the sentence may not promise one
                self.assertNotIn("flat line below", visible_text(html))


class TestTheBlocksStillRender(unittest.TestCase):
    """The panels the fixes touched are still on the page in every state."""

    def test_no_state_prints_an_unfilled_template_or_a_wrapper(self) -> None:
        for state in STATES:
            _, html = render(**state)
            text = visible_text(html)
            with self.subTest(state=state):
                self.assertNotIn("{n}", text)
                self.assertNotIn("{'value'", text)

    def test_every_state_still_carries_the_four_panels(self) -> None:
        for state in STATES:
            _, html = render(**state)
            with self.subTest(state=state):
                self.assertIn("The decision", html)
                self.assertIn("The market", html)
                self.assertIn("What the engine refuses", html)
                self.assertIn("The chain slot", html)
                self.assertIn(labels.render("T2"), visible_text(html))


if __name__ == "__main__":
    unittest.main()
