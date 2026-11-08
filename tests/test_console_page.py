"""The page, tested against the rules rather than against a screenshot.

Four checks matter and each has cost me something to get right:

1. The banner is first, undismissable and not sticky, because a screenshot of the page
   must carry the label even if the crop starts halfway down.
2. Every number is rendered through `units.num`, which puts the badge in the same text
   run, in front of the value. So: every `.n` span starts with a badge, and a count that
   sits inside a sentence is its own `.n` span -- A19's `8 of 9 recorded resales (88.9%)`
   and A1's `records 9 sales` are four and one badged count, not one sentence under the
   panel's badge. Other digits that are not counts are still allowed inside a sentence from
   the registry (a timestamp in the mode line, the lamport equality on the [EXACT] line).
3. No `title=` attribute, so no label lives in a tooltip nobody reads.
4. The prohibited sentences are absent from the visible text of every state.
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
from ticketpath.console import units
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
BADGE_RE = re.compile(r"^\[(FIXTURE|DECLARED|EXACT|UNVALIDATED|REFUSED|DESIGN|SIMULATED|DEVNET)\]")
# A path no run creates, so the absent state is reachable without touching the real artefact.
MISSING_ARTEFACT = Path(tempfile.gettempdir()) / "ticketpath-no-such-artefact.json"


def render(**kwargs) -> tuple[dict, str]:
    # `artefact_path` is the chain slot's seam: a path with no file reaches the absent state
    # without moving the operator's proven record out of the way.
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
    payload["canonicalUrl"] = "http://127.0.0.1:8788/?event=evt&tier=tier&asOf=2026-11-07T12:00:00Z"
    return payload, page.render(payload)


def text_nodes(html: str) -> list[str]:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    without_code = re.sub(r"<code>.*?</code>", "<code></code>", without_style, flags=re.S)
    # A form control's label names the field and its range; it is not a rendered number.
    without_code = re.sub(r"<label.*?</label>", "<label></label>", without_code, flags=re.S)
    return [html_module.unescape(node).strip() for node in re.findall(r">([^<]+)<", without_code)]


def visible_text(html: str) -> str:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return html_module.unescape(re.sub(r"<[^>]+>", "\n", without_style))


def sentence_patterns() -> list[re.Pattern[str]]:
    """Each registry sentence with its fields replaced by a wildcard."""
    templates = (
        list(labels.MANDATORY.values())
        + list(labels.ALLOWED.values())
        + list(labels.PAGE.values())
        + list(labels.REFUSAL_TEXT.values())
    )
    patterns = []
    for template in templates:
        parts = re.split(r"\{[a-zA-Z_]+\}", template)
        patterns.append(re.compile("^" + ".+?".join(re.escape(part) for part in parts) + "$"))
    return patterns


class TestBanner(unittest.TestCase):
    def test_the_banner_is_the_first_element_and_says_the_mandatory_sentence(self) -> None:
        _, html = render()
        self.assertLess(html.index('<div class="banner"'), html.index("<main"))
        self.assertLess(html.index('<div class="banner"'), html.index("<h1"))
        self.assertIn(labels.render("T1"), text_nodes(html))

    def test_the_banner_cannot_be_dismissed_or_hidden_on_scroll(self) -> None:
        _, html = render()
        style = re.search(r"<style>(.*?)</style>", html, flags=re.S).group(1)
        self.assertNotIn("position: sticky", style)
        self.assertNotIn("position:sticky", style)
        self.assertNotIn("display: none", style)
        self.assertNotIn("display:none", style)
        banner = html[html.index('<div class="banner"') : html.index("</div>", html.index('<div class="banner"'))]
        self.assertNotIn("<button", banner)
        self.assertNotIn("onclick", banner)

    def test_the_banner_names_the_store_it_came_from(self) -> None:
        payload, html = render()
        self.assertIn(payload["fixtureBuild"]["sha256"], html)
        self.assertEqual(len(payload["fixtureBuild"]["sha256"]), 64)


class TestEveryNumberCarriesItsBadge(unittest.TestCase):
    """Every number carries its provenance in the same text run: a badge, or the file's status.

    An artefact value the quote hash does not cover used to carry `[DEVNET]`, which claimed a
    provenance the hash does not back. It carries `the file states` instead, and this test
    accepts that marker in place of a badge for exactly those spans.
    """

    def test_every_number_span_begins_with_a_badge(self) -> None:
        states = [
            {},
            {"event_id": "evt_syn_04"},
            {"event_id": "evt_syn_03"},
            {"event_id": "evt_syn_08"},
            {"event_id": "evt_syn_02", "cap_bps": "0"},
            {"show_sim": True},
            {"event_id": "evt_syn_02", "as_of": "2026-09-01T00:00:00Z"},
        ]
        for state in states:
            _, html = render(**state)
            spans = re.findall(r'<span class="n">(.*?)</span>', html, flags=re.S)
            self.assertGreater(len(spans), 5)
            for span in spans:
                with self.subTest(state=state, span=span[:60]):
                    text = span.strip()
                    self.assertTrue(
                        BADGE_RE.match(text) or text.startswith(units.STATED), text
                    )

    def test_the_only_digits_outside_a_badge_are_inside_a_registry_sentence(self) -> None:
        patterns = sentence_patterns()
        for state in ({}, {"event_id": "evt_syn_04"}, {"event_id": "evt_syn_03"}, {"show_sim": True}):
            _, html = render(**state)
            for node in text_nodes(html):
                if not re.search(r"\d", node):
                    continue
                with self.subTest(state=state, node=node[:70]):
                    if BADGE_RE.match(node) or node.startswith(units.STATED):
                        continue
                    self.assertTrue(
                        any(pattern.match(node) for pattern in patterns),
                        f"a number outside a badge and outside a sentence: {node!r}",
                    )

    def test_no_title_attribute_anywhere(self) -> None:
        for state in ({}, {"event_id": "evt_syn_03"}):
            _, html = render(**state)
            self.assertNotIn(" title=", html)
            self.assertNotIn("title='", html)

    def test_the_counts_inside_a19_are_each_their_own_badged_span(self) -> None:
        """Review 3.11, made strict: `8 of 9 (88.9%)` sat under the panel's `[UNVALIDATED]`.

        The four counts in A19 -- the cap in percent, the sales at the ceiling, the sales,
        and the share -- are `[FIXTURE]` facts inside a panel badged `[UNVALIDATED]`, so the
        badge has to travel with each number. Asserted in both directions: the spans exist,
        and with every badged span removed the sentence's digits are gone from the page.
        """
        _, html = render(event_id="evt_syn_02")
        for span in (
            '<span class="n">[FIXTURE] 15%</span>',
            '<span class="n">[FIXTURE] 8</span>',
            '<span class="n">[FIXTURE] 9</span>',
            '<span class="n">[FIXTURE] 88.9%</span>',
        ):
            with self.subTest(span=span):
                self.assertIn(span, html)
        unbaged = html_module.unescape(re.sub(r'<span class="n">.*?</span>', " ", html, flags=re.S))
        self.assertNotRegex(unbaged, r"\d+\.?\d*% over face")
        self.assertNotRegex(unbaged, r"\d+ of \d+ recorded resales")
        self.assertNotRegex(unbaged, r"\(\s*88\.9%\s*\) settled")

    def test_the_count_inside_a1_is_its_own_badged_span(self) -> None:
        _, html = render(event_id="evt_syn_01")
        self.assertIn('<span class="n">[FIXTURE] 6</span> sales.', html)
        unbaged = html_module.unescape(re.sub(r'<span class="n">.*?</span>', " ", html, flags=re.S))
        self.assertNotRegex(unbaged, r"ledger records \d+ sales")


class TestMandatorySentences(unittest.TestCase):
    def test_t1_is_on_every_state(self) -> None:
        for state in ({}, {"event_id": "evt_syn_04"}, {"event_id": "evt_syn_03"}, {"event_id": "evt_syn_08"}):
            _, html = render(**state)
            with self.subTest(state=state):
                self.assertIn(labels.render("T1"), visible_text(html))

    def test_t5_is_on_every_state_where_nothing_verified(self) -> None:
        """T5 is the page's deployment claim, so it is printed where it is true.

        Every state used to reach it because no artefact ever verified inside a test. Now the
        proven record verifies, and a page that prints it may not also say no program is
        deployed on any cluster: the slot carries `P_CHAIN_NOT_ASKED` instead (feature 2,
        part 3). Both halves are asserted, so neither sentence can go missing.
        """
        for state in ({}, {"event_id": "evt_syn_04"}, {"event_id": "evt_syn_03"}, {"event_id": "evt_syn_08"}):
            payload, html = render(**state)
            text = visible_text(html)
            with self.subTest(state=state):
                if payload["chain"]["state"] == "verified":
                    self.assertIn(labels.render("P_CHAIN_NOT_ASKED"), text)
                else:
                    self.assertIn(labels.render("T5"), text)
                self.assertNotIn("No program is deployed on any cluster", text)
        _, absent = render(artefact_path=MISSING_ARTEFACT)
        self.assertIn(labels.render("T5"), visible_text(absent))

    def test_t2_is_on_the_decision_block(self) -> None:
        _, html = render()
        self.assertIn(labels.render("T2"), visible_text(html))

    def test_t3_is_where_a_band_is_shown(self) -> None:
        _, html = render(event_id="evt_syn_04")
        self.assertIn(labels.render("T3"), visible_text(html))

    def test_t4_is_where_a_rate_is_shown(self) -> None:
        _, html = render()
        self.assertIn(labels.render("T4"), visible_text(html))

    def test_the_binding_event_prints_a19_and_never_the_02d_range_line(self) -> None:
        _, html = render()
        text = visible_text(html)
        self.assertIn("the cap is binding", text)
        self.assertIn("We do not state an upper bound from this record.", text)
        self.assertNotIn("We would not argue with any price in that range", text)

    def test_the_uncapped_event_prints_the_range_line_and_the_recommendation(self) -> None:
        _, html = render(event_id="evt_syn_04")
        text = visible_text(html)
        self.assertIn("We would not argue with any price in that range", text)
        self.assertIn("Recommended primary price:", text)

    def test_the_cold_start_prints_the_refusal_and_the_prior_band(self) -> None:
        _, html = render(event_id="evt_syn_03")
        text = visible_text(html)
        self.assertIn("No resale has been recorded on this event, so we will not state a primary price.", text)
        self.assertIn("Not a prediction:", text)
        self.assertIn("The model is not fitted.", text)


class TestNoBannedSentences(unittest.TestCase):
    def test_the_visible_text_of_every_state_passes_the_scan(self) -> None:
        states = [
            {},
            {"event_id": "evt_syn_04"},
            {"event_id": "evt_syn_03"},
            {"event_id": "evt_syn_08"},
            {"event_id": "evt_syn_02", "cap_bps": "0"},
            {"show_sim": True},
        ]
        for state in states:
            payload, html = render(**state)
            with self.subTest(state=state):
                self.assertIsNone(labels.contains_banned(visible_text(html)))
                self.assertIsNone(labels.contains_banned(str(payload)))

    def test_the_page_does_not_say_the_banned_sentence_even_as_an_example(self) -> None:
        _, html = render()
        self.assertNotIn("chance of selling at price", visible_text(html).lower())


class TestAccessibleAndPrintable(unittest.TestCase):
    def test_every_panel_accessible_name_begins_with_its_badge(self) -> None:
        _, html = render()
        names = re.findall(r'aria-label="([^"]+)"', html)
        self.assertGreaterEqual(len(names), 5)
        for name in names:
            with self.subTest(name=name):
                self.assertIsNotNone(BADGE_RE.match(name.strip()))

    def test_no_badge_is_hover_or_focus_only(self) -> None:
        _, html = render()
        style = re.search(r"<style>(.*?)</style>", html, flags=re.S).group(1)
        self.assertNotIn(":hover", style)
        self.assertNotIn("visibility: hidden", style)

    def test_the_badge_and_the_number_are_in_one_text_run(self) -> None:
        _, html = render()
        text = visible_text(html)
        # "12 resales" printed as "[FIXTURE] 12" with the badge first, in that order
        self.assertRegex(text, r"\[FIXTURE\]\s*\n?\s*12")
        # and the tag-stripped page still reads: no badge is delivered by CSS alone
        self.assertIn("[UNVALIDATED]", text)

    def test_no_external_asset_and_no_script(self) -> None:
        """The page loads nothing from off the machine. One anchor is allowed, and it is the
        transaction the artefact itself names: a pointer to the evidence, never an asset.

        The rule used to be asserted as "no https:// anywhere", which held only because a
        verified artefact was unreachable in a test. The anchor's URL is now read out of the
        file, so it cannot exist for a transaction the file does not carry (feature 2).
        """
        payload, html = render()
        self.assertNotIn("<script", html)
        self.assertNotIn("<link", html)
        self.assertNotIn("url(", html)
        self.assertNotIn("src=", html)
        for url in re.findall(r"https://[^\"' <>]+", html):
            with self.subTest(url=url):
                explorer = (payload["chain"].get("recorded") or {}).get("explorer") or {}
                self.assertEqual(url, explorer.get("transaction"))
                self.assertTrue(url.startswith("https://explorer.solana.com/tx/"))

    def test_every_form_control_has_a_name_and_a_label(self) -> None:
        _, html = render()
        inputs = re.findall(r"<(?:input|select|button)\b[^>]*>", html)
        self.assertGreaterEqual(len(inputs), 6)
        for element in inputs:
            with self.subTest(element=element[:60]):
                if element.startswith("<button"):
                    continue
                self.assertIn('name="', element)
        for control_id in re.findall(r'<(?:input|select)[^>]*id="([^"]+)"', html):
            self.assertIn(f'for="{control_id}"', html)


class TestStatesRender(unittest.TestCase):
    def test_the_four_fixture_states_all_render(self) -> None:
        for state in ({}, {"event_id": "evt_syn_03"}, {"event_id": "evt_syn_04"}, {"event_id": "evt_syn_08"}):
            payload, html = render(**state)
            with self.subTest(state=state):
                self.assertIn("<!doctype html>", html)
                self.assertIn("Ticketpath — organizer pricing console", html)
                self.assertEqual(payload["tiers"][0]["refusal"]["saleProbability"], None)

    def test_an_error_renders_as_a_page_not_a_traceback(self) -> None:
        html = page.render_error(status=400, message="capBps must be an integer", code="cap_invalid")
        self.assertIn(labels.render("T1"), visible_text(html))
        self.assertIn("cap_invalid", visible_text(html))
        self.assertNotIn("Traceback", html)


if __name__ == "__main__":
    unittest.main()
