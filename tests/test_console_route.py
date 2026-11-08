"""`GET /` over a real socket: HTML, the banner, and the four states by URL alone.

The judge's path, tested as the judge walks it: open the URL, change a query parameter,
and every state a control can reach has a URL that reproduces it. `/api/*` is untouched
-- the contract routes keep their JSON and their status codes -- and the console is not
one of them, because it is not a contract endpoint.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import canonical_url, make_server


def _orchestrator() -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc),
    )


class ConsoleRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(0, "127.0.0.1", _orchestrator())
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path: str) -> tuple[int, str, str]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as response:
                return response.status, response.read().decode("utf-8"), response.headers.get("content-type", "")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8"), exc.headers.get("content-type", "")

    def test_root_serves_html_with_the_banner_first(self) -> None:
        status, body, content_type = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(labels.render("T1"), body)
        self.assertLess(body.index('<div class="banner"'), body.index("<h1"))
        self.assertIn("SeatPass — organizer pricing console", body)

    def test_the_console_is_not_a_contract_route(self) -> None:
        status, body, content_type = self.get("/api/events")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertIn('"items"', body)

    def test_favicon_answers_no_content(self) -> None:
        status, body, _ = self.get("/favicon.ico")
        self.assertEqual(status, 204)
        self.assertEqual(body, "")

    def test_every_state_is_reachable_by_query_parameter(self) -> None:
        cases = {
            "/?event=evt_syn_04": "Synthetic Theatre",
            "/?event=evt_syn_03": "Synthetic Annex",
            "/?event=evt_syn_02&capBps=0": "above this cap",
            "/?sim=1": "[SIMULATED]",
            "/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z": "No resale has been recorded",
        }
        for path, marker in cases.items():
            status, body, _ = self.get(path)
            with self.subTest(path=path):
                self.assertEqual(status, 200)
                self.assertIn(marker, body)

    def test_a_bad_cap_is_a_400_rendered_as_a_page(self) -> None:
        status, body, content_type = self.get("/?capBps=not-a-number")
        self.assertEqual(status, 400)
        self.assertIn("text/html", content_type)
        self.assertIn("cap_invalid", body)
        self.assertIn(labels.render("T1"), body)
        self.assertNotIn("Traceback", body)

    def test_a_bad_as_of_is_a_400_with_the_documented_code(self) -> None:
        status, body, _ = self.get("/?asOf=nonsense")
        self.assertEqual(status, 400)
        self.assertIn("as_of_invalid", body)

    def test_an_unknown_event_is_a_404_rendered_as_a_page(self) -> None:
        status, body, _ = self.get("/?event=evt_nope")
        self.assertEqual(status, 404)
        self.assertIn("not_found", body)
        self.assertIn("back to the decision", body)

    def test_the_canonical_url_round_trips(self) -> None:
        status, body, _ = self.get("/?event=evt_syn_04&tau=0.3")
        self.assertEqual(status, 200)
        start = body.index("canonical URL for this decision:")
        fragment = body[start : start + 400]
        self.assertIn("event=evt_syn_04", fragment)
        self.assertIn("tau=0.3", fragment)
        status2, body2, _ = self.get(fragment[fragment.index("http") : fragment.index("</code>")].replace(self.base, ""))
        self.assertEqual(status2, 200)
        self.assertIn("0.3", body2)

    @unittest.skipUnless(
        (Path(__file__).resolve().parents[1] / "records" / "devnet-artefacts.json").exists(),
        "the operator's proven record is not on disk",
    )
    def test_the_served_page_carries_the_recorded_devnet_transaction(self) -> None:
        """The judge's surface, over a socket: the page, not the payload.

        The defect feature 2 fixes was invisible from inside the orchestrator and visible
        here: `/` answered with "No devnet transaction has been recorded" while the record
        on disk verified. Both directions are asserted: the recorded facts are printed, and
        the absent sentence is not.
        """
        artefact = Path(__file__).resolve().parents[1] / "records" / "devnet-artefacts.json"
        record = json.loads(artefact.read_text(encoding="utf-8"))
        status, body, _ = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(record["signature"], body)
        self.assertIn(str(record["slot"]), body)
        self.assertIn(record["mint"], body)
        self.assertIn("1,250,000,000", body)
        self.assertIn("6010", body)
        # The sentence is about the quote now, not about "the number": the two
        # recommendations on this page are the same number and the old sentence said they
        # were different (feature 2 review).
        self.assertIn("is not the quote the file records", body)
        # One number, printed once: the recorded recommendation and the page's own are equal
        # here, so the sentence says so instead of printing 1.38 SOL twice and calling it a
        # disagreement.
        self.assertIn("The recorded recommendation is <span", body)
        self.assertIn("recommends the same number", body)
        self.assertNotIn("No devnet transaction has been recorded", body)

        instant = f"/?event={record['eventId']}&tier={record['tierId']}&asOf={record['asOf']}"
        status, body, _ = self.get(instant)
        self.assertEqual(status, 200)
        self.assertIn("is the quote the file records", body)
        self.assertNotIn("is not the quote the file records", body)


class CanonicalUrlTest(unittest.TestCase):
    def test_only_supplied_parameters_appear(self) -> None:
        payload = {
            "event": {"id": "e"},
            "selection": {
                "tierId": "t",
                "capBpsCandidate": {"value": None},
                "feeLamports": {"value": 0},
                "tau": {"value": 0.2},
            },
            "asOf": "2026-11-07T12:00:00.000Z",
            "sim": [],
        }
        url = canonical_url(payload, "http://127.0.0.1:8788")
        self.assertIn("event=e", url)
        self.assertIn("feeLamports=0", url)
        self.assertNotIn("capBps", url)  # an unset cap is not written as a value
        self.assertNotIn("sim", url)


class TestAnUnmeasuredClusterStillServes(unittest.TestCase):
    """`TICKETPATH_CLUSTER=testnet`: the payload carries no memo program and the page answers.

    Before this test, `_chain_payload` passed the cluster straight to `quote_commit`, which
    raised `UnknownCluster` three lines before the field was filled: every `price_guidance()`
    on testnet died, the console's `/` route turned it into HTTP 500, and `chain.memoProgram`
    was never null because it was never reached. Feature-1 review finding 2, measured there.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.orchestrator = Orchestrator(
            LedgerAdapter.from_fixture(),
            RpcAdapter.from_env("testnet"),
            PricingModelAdapter(),
            "testnet",
            now=lambda: datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc),
        )
        cls.server = make_server(0, "127.0.0.1", cls.orchestrator)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path: str) -> tuple[int, str, str]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as response:
                return response.status, response.read().decode("utf-8"), response.headers.get("content-type", "")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8"), exc.headers.get("content-type", "")

    def test_the_payload_carries_a_null_memo_program_rather_than_raising(self) -> None:
        payload = self.orchestrator.price_guidance(event_id="evt_syn_01")
        self.assertIn("memoProgram", payload["chain"])
        self.assertIsNone(payload["chain"]["memoProgram"])
        # The field is null because the cluster has no measurement, not because the rest of
        # the commitment went missing with it.
        self.assertTrue(payload["chain"]["quoteId"].startswith("q-"))
        self.assertTrue(payload["chain"]["memoText"].startswith("ticketpath:quote:"))
        self.assertIn(payload["chain"]["quoteHash"], payload["chain"]["memoText"])

    def test_the_console_answers_two_hundred_on_a_cluster_it_cannot_name(self) -> None:
        status, body, _ = self.get("/")
        self.assertEqual(status, 200, body[:300])
        self.assertIn("seatpass", body.lower())

    def test_a_measured_cluster_still_names_its_id(self) -> None:
        # The guard that keeps the test above from passing on a field somebody deleted: the
        # devnet server names the devnet id through the same code path.
        payload = _orchestrator().price_guidance(event_id="evt_syn_01")
        self.assertEqual(payload["chain"]["memoProgram"], "Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH")


if __name__ == "__main__":
    unittest.main()
