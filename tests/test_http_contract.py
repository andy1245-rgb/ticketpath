"""The wire, end to end, over a real socket on an ephemeral port.

This is the acceptance test for the contract: status codes, shapes, sorting,
filters, the CORS headers the frontend needs, and the honesty fields a judge can
read. It never binds 8788 (or 8787): the port is 0, chosen by the OS.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import CONTRACT_ENDPOINT_COUNT, make_server


def _orchestrator() -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc),
    )


class ServerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(0, "127.0.0.1", _orchestrator())
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path: str) -> tuple[int, dict, dict]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8")), dict(response.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8")), dict(exc.headers)

    def post(self, path: str, body: dict | None = None) -> tuple[int, dict, dict]:
        data = b"" if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=data,
            method="POST",
            headers={"content-type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8")), dict(response.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8")), dict(exc.headers)


class TestHealth(ServerTestCase):
    def test_health_reports_version_and_source(self) -> None:
        status, body, _ = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "ticketpath")
        self.assertTrue(body["version"])
        self.assertEqual(body["dataSource"]["mode"], "synthetic-fixture")
        self.assertTrue(body["dataSource"]["synthetic"])
        self.assertIn("SYNTHETIC", body["dataSource"]["label"])
        self.assertFalse(body["chain"]["programDeployed"])
        self.assertFalse(body["pricingModel"]["available"])
        self.assertEqual(body["contract"]["endpointsInContract"], CONTRACT_ENDPOINT_COUNT)
        self.assertEqual(body["contract"]["endpointsInContract"], 9)
        self.assertEqual(body["contract"]["endpointsImplemented"], 9)
        # nine contract endpoints plus /health
        self.assertEqual(body["contract"]["routesImplemented"], 10)

    def test_health_is_json_utf8(self) -> None:
        _, _, headers = self.get("/health")
        self.assertIn("application/json", headers["content-type"])


class TestEvents(ServerTestCase):
    def test_list_is_sorted_by_start_and_paginates(self) -> None:
        status, body, _ = self.get("/api/events")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 2)
        self.assertIsNone(body["nextCursor"])
        starts = [event["startsAt"] for event in body["items"]]
        self.assertEqual(starts, sorted(starts))
        self.assertEqual(body["items"][0]["id"], "evt_fixture_2")  # 2026-10-01 starts first

    def test_list_pagination(self) -> None:
        status, body, _ = self.get("/api/events?limit=1")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["nextCursor"], "1")
        status, second, _ = self.get(f"/api/events?limit=1&cursor={body['nextCursor']}")
        self.assertEqual(status, 200)
        self.assertEqual(len(second["items"]), 1)
        self.assertNotEqual(second["items"][0]["id"], body["items"][0]["id"])
        self.assertIsNone(second["nextCursor"])

    def test_filters(self) -> None:
        _, by_status, _ = self.get("/api/events?status=completed")
        self.assertEqual([event["id"] for event in by_status["items"]], ["evt_fixture_2"])
        _, by_city, _ = self.get("/api/events?city=Toronto")
        self.assertEqual(len(by_city["items"]), 2)
        _, by_text, _ = self.get("/api/events?q=annex")
        self.assertEqual([event["id"] for event in by_text["items"]], ["evt_fixture_2"])

    def test_bad_filter_is_400_not_an_empty_page(self) -> None:
        status, body, _ = self.get("/api/events?status=almost_on_sale")
        self.assertEqual(status, 400)
        self.assertIn("message", body)

    def test_bad_limit_and_cursor_are_400(self) -> None:
        for path in ("/api/events?limit=0", "/api/events?limit=abc", "/api/events?cursor=-1"):
            with self.subTest(path=path):
                status, body, _ = self.get(path)
                self.assertEqual(status, 400)
                self.assertIn("message", body)

    def test_detail_by_id_and_by_slug(self) -> None:
        _, by_id, _ = self.get("/api/events/evt_fixture_1")
        _, by_slug, _ = self.get("/api/events/fixture-hall-session")
        self.assertEqual(by_id["id"], by_slug["id"])
        self.assertEqual(by_slug["slug"], "fixture-hall-session")
        self.assertEqual(by_slug["organizer"]["id"], "org_fixture_1")
        self.assertFalse(by_slug["organizer"]["verified"])
        self.assertEqual(len(by_slug["tiers"]), 2)
        self.assertEqual(by_slug["totalSupply"], 150)
        self.assertEqual(by_slug["issuedCount"], 4)

    def test_missing_event_is_404_with_a_message(self) -> None:
        status, body, _ = self.get("/api/events/evt_nope")
        self.assertEqual(status, 404)
        self.assertIn("not found", body["message"])


class TestTickets(ServerTestCase):
    def test_owner_wallet_filters_on_current_owner_not_issuee(self) -> None:
        _, current, _ = self.get("/api/tickets?ownerWallet=FXTUREacct411111111111111111111111111111111")
        self.assertEqual([ticket["id"] for ticket in current["items"]], ["tkt_fixture_0001"])
        # w1 issued tkt_0001 but no longer holds it.
        _, issuee, _ = self.get("/api/tickets?ownerWallet=FXTUREacct111111111111111111111111111111111")
        self.assertEqual(issuee["items"], [])

    def test_status_and_event_filters(self) -> None:
        _, redeemed, _ = self.get("/api/tickets?status=redeemed")
        self.assertEqual([ticket["id"] for ticket in redeemed["items"]], ["tkt_fixture_0004"])
        _, by_event, _ = self.get("/api/tickets?eventId=evt_fixture_1")
        self.assertEqual(len(by_event["items"]), 4)
        _, bad, _ = self.get("/api/tickets?status=almost_valid")
        self.assertEqual(bad["code"], "status_invalid")

    def test_detail_by_id_and_mint(self) -> None:
        _, by_id, _ = self.get("/api/tickets/tkt_fixture_0003")
        _, by_mint, _ = self.get("/api/tickets/FXTUREmint311111111111111111111111111111111")
        self.assertEqual(by_id["id"], by_mint["id"])
        self.assertEqual(by_id["faceValueLamports"], 2_000_000_000)
        self.assertEqual(by_id["transferCount"], 1)
        self.assertEqual(by_id["lastSalePriceLamports"], 2_050_000_000)

    def test_resale_history_is_the_real_computation(self) -> None:
        status, body, _ = self.get("/api/tickets/tkt_fixture_0001/resale-history")
        self.assertEqual(status, 200)
        self.assertEqual(
            body["stats"],
            {
                "saleCount": 2,
                "transferCount": 3,
                "avgMarkupBps": 750,
                "peakPriceLamports": 1_250_000_000,
                "lastPriceLamports": 900_000_000,
                "totalVolumeLamports": 2_150_000_000,
                "uniqueWallets": 4,
            },
        )
        self.assertEqual(len(body["entries"]), 4)
        self.assertTrue(body["dataSource"]["synthetic"])

    def test_missing_ticket_is_404(self) -> None:
        status, body, _ = self.get("/api/tickets/tkt_nope/resale-history")
        self.assertEqual(status, 404)
        self.assertIn("not found", body["message"])


class TestAnalytics(ServerTestCase):
    def test_analytics_endpoint(self) -> None:
        status, body, _ = self.get("/api/events/evt_fixture_1/analytics")
        self.assertEqual(status, 200)
        self.assertEqual(body["eventId"], "evt_fixture_1")
        self.assertEqual(body["saleCount"], 4)
        self.assertEqual(body["avgMarkupBps"], 563)
        self.assertEqual(body["medianResalePriceLamports"], 1_150_000_000)
        self.assertEqual(body["resoldShare"], 0.75)
        self.assertEqual(len(body["markupDistribution"]), 6)
        self.assertEqual([point["date"] for point in body["priceSeries"]], ["2026-11-02", "2026-11-03", "2026-11-04"])

    def test_missing_event_analytics_is_404(self) -> None:
        status, _, _ = self.get("/api/events/evt_nope/analytics")
        self.assertEqual(status, 404)


class TestRouting(ServerTestCase):
    def test_unknown_route_is_404(self) -> None:
        status, body, _ = self.get("/api/nowhere")
        self.assertEqual(status, 404)
        self.assertEqual(body["code"], "no_route")

    def test_wrong_method_is_405(self) -> None:
        status, body, _ = self.post("/api/events")
        self.assertEqual(status, 405)
        self.assertEqual(body["code"], "method_not_allowed")

    def test_cors_headers_are_present_for_the_frontend(self) -> None:
        _, _, headers = self.get("/health")
        lowered = {key.lower(): value for key, value in headers.items()}
        self.assertEqual(lowered["access-control-allow-origin"], "*")
        self.assertIn("POST", lowered["access-control-allow-methods"])
        self.assertIn("content-type", lowered["access-control-allow-headers"])

    def test_options_preflight(self) -> None:
        request = urllib.request.Request(self.base + "/api/wallets/x/verification", method="OPTIONS")
        with urllib.request.urlopen(request, timeout=10) as response:
            self.assertEqual(response.status, 204)
            self.assertIn("access-control-allow-methods", {k.lower() for k in response.headers})


if __name__ == "__main__":
    unittest.main()
