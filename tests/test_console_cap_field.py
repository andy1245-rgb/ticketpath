"""The cap field, the canonical URL and the decision block carry one cap.

The defect this pins: the `capBps` control rendered the event's *recorded* cap
unconditionally, while the canonical URL under it, the refusal headline and the
recommendation all used the cap the page was actually honouring. On
`/?event=evt_syn_02&capBps=0` a judge read a field saying 1500, a URL saying 0 and a
decision saying the cap of 0 bps forbids the price, on one page.

The rule the fix adopts, and the page states it in one line: the control shows the cap
this page prices against (the URL's cap when the URL names one, the event's recorded cap
otherwise), the canonical URL carries that same number, and a blank field falls back to
the recorded cap. An event with no recorded cap says so instead of showing an empty box.

Both ways a regression can hide are asserted: the numbers (field, URL parameter, the
[DECLARED] cap named in the decision block), and the round trip through a real socket,
because a page whose URL and field disagree is only reachable over HTTP.
"""

from __future__ import annotations

import html as html_module
import re
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import canonical_url, make_server

CAPPED = "evt_syn_02"      # records 1500 bps, and eight of nine sales sit on the ceiling
UNCAPPED = "evt_syn_04"    # records no cap
CLOCK = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)


def orchestrator() -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
    )


def rendered(**kwargs) -> tuple[dict, str]:
    engine = orchestrator()
    payload = engine.price_guidance(**kwargs)
    payload["canonicalUrl"] = canonical_url(payload, "http://127.0.0.1:8788")
    return payload, page.render(payload)


def form_value(html: str) -> str:
    """What the cap control displays. The whole point: this is the judge's reading."""
    match = re.search(r'<input id="capBps"[^>]*\bvalue="([^"]*)"', html)
    assert match, "the cap control is on the page"
    return match.group(1)


def visible(html: str) -> str:
    """The HTML as a reader sees it, entities decoded, no tags."""
    return html_module.unescape(re.sub(r"<[^>]+>", "", html))


def canonical_cap(html: str) -> str:
    """The `capBps` parameter of the canonical URL printed under the control."""
    match = re.search(r"canonical URL for this decision: <code>([^<]+)</code>", html)
    assert match, "the canonical URL is on the page"
    query = urllib.parse.urlsplit(html_module.unescape(match.group(1))).query
    return urllib.parse.parse_qs(query).get("capBps", [""])[0]


def decision_block(html: str) -> str:
    start = html.index('aria-label="[UNVALIDATED] the decision"')
    return html[start : html.index("</section>", start)]


class TestTheFieldShowsTheCapInForce(unittest.TestCase):
    def test_a_url_cap_is_what_the_field_shows(self) -> None:
        """The defect, stated as an assertion: 0 in the URL, 0 in the field."""
        _, html = rendered(event_id=CAPPED, cap_bps="0")
        self.assertEqual(form_value(html), "0")
        _, html = rendered(event_id=CAPPED, cap_bps="2500")
        self.assertEqual(form_value(html), "2500")

    def test_no_url_cap_shows_the_event_recorded_cap(self) -> None:
        _, html = rendered(event_id=CAPPED)
        self.assertEqual(form_value(html), "1500")

    def test_the_field_never_shows_the_recorded_cap_when_the_url_names_another(self) -> None:
        for cap in ("0", "100", "2500", "10000"):
            payload, html = rendered(event_id=CAPPED, cap_bps=cap)
            with self.subTest(cap=cap):
                self.assertEqual(payload["event"]["capBps"]["value"], 1500, "the premise: the record says 1500")
                self.assertEqual(form_value(html), cap)


class TestTheCanonicalUrlMatchesTheField(unittest.TestCase):
    def test_field_and_url_carry_the_same_cap_in_every_state(self) -> None:
        states = (
            {"event_id": CAPPED},
            {"event_id": CAPPED, "cap_bps": "0"},
            {"event_id": CAPPED, "cap_bps": "2500"},
            {"event_id": UNCAPPED},
            {"event_id": UNCAPPED, "cap_bps": "2500"},
        )
        for state in states:
            _, html = rendered(**state)
            with self.subTest(state=state):
                self.assertEqual(canonical_cap(html), form_value(html))

    def test_the_canonical_url_reproduces_the_page_it_is_printed_on(self) -> None:
        _, html = rendered(event_id=CAPPED, cap_bps="2500")
        before = canonical_cap(html)
        again = rendered(event_id=CAPPED, cap_bps=before)[1]
        self.assertEqual(canonical_cap(again), before)
        self.assertEqual(form_value(again), "2500")


class TestThePageStatesTheRule(unittest.TestCase):
    def test_the_capped_rule_line_names_the_recorded_cap_it_falls_back_to(self) -> None:
        _, html = rendered(event_id=CAPPED)
        self.assertIn(labels.render("P_CAP_RULE", recorded=1500), visible(html))

    def test_an_uncapped_event_says_the_field_records_no_cap(self) -> None:
        _, html = rendered(event_id=UNCAPPED)
        self.assertEqual(form_value(html), "")
        # an empty box with no explanation is the second half of the defect
        self.assertIn("this event records no cap", visible(html))
        self.assertIn(labels.render("P_CAP_RULE_UNCAPPED"), visible(html))
        self.assertEqual(canonical_cap(html), "")


class TestTheDecisionBlockNamesTheCapInForce(unittest.TestCase):
    def test_a_url_cap_different_from_the_record_is_named_in_the_block(self) -> None:
        for cap in ("0", "2500"):
            _, html = rendered(event_id=CAPPED, cap_bps=cap)
            block = decision_block(html)
            with self.subTest(cap=cap):
                self.assertIn(f"[DECLARED] {cap} bps", block, "the cap in force is on the page")

    def test_the_recorded_cap_is_still_described_as_the_recorded_one(self) -> None:
        block = decision_block(rendered(event_id=CAPPED, cap_bps="2500")[1])
        self.assertIn("[FIXTURE] 15%", block)  # the record's own cap, not reclassified
        self.assertIn(labels.render("P_CAP_ABOVE"), block)

    def test_an_uncapped_event_with_a_url_cap_names_it_without_inventing_a_record_cap(self) -> None:
        block = decision_block(rendered(event_id=UNCAPPED, cap_bps="2500")[1])
        self.assertIn("[DECLARED] 2500 bps", block)
        self.assertIn("records no cap of its own", block)


class TestOverASocket(unittest.TestCase):
    """The judge path: four URLs, fetched, with the field read out of the served HTML."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(0, "127.0.0.1", orchestrator())
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path: str) -> str:
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.read().decode("utf-8")

    def test_the_four_urls_agree(self) -> None:
        cases = (
            ("/?event=evt_syn_02", "1500"),
            ("/?event=evt_syn_02&capBps=0", "0"),
            ("/?event=evt_syn_02&capBps=2500", "2500"),
            ("/?event=evt_syn_04", ""),
        )
        for path, expected in cases:
            html = self.get(path)
            with self.subTest(path=path):
                self.assertEqual(form_value(html), expected)
                self.assertEqual(canonical_cap(html), expected)


if __name__ == "__main__":
    unittest.main()
