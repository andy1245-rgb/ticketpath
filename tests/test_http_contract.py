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

from tests import store_arithmetic as arith
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import CONTRACT_ENDPOINT_COUNT, ENGINE_DESCRIPTION, make_server


def _orchestrator() -> Orchestrator:
    model = PricingModelAdapter()
    engine = Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        model,
        "devnet",
        now=lambda: datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc),
    )
    model.register(engine.engine_model, "engine-2026-11-07", **ENGINE_DESCRIPTION)  # same wiring as the server
    return engine


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
        # A model is registered now (the console's engine), so the health block says so.
        # It also says the chain has no program, which registering a model must not blur.
        self.assertTrue(body["pricingModel"]["available"])
        self.assertEqual(body["pricingModel"]["modelVersion"], "engine-2026-11-07")
        # Available is not the same claim as fitted. The block has to separate them, or a
        # reader of /health alone reads "model" and assumes a calibration that does not exist.
        self.assertEqual(body["pricingModel"]["kind"], "rule-based-bounded-estimator")
        self.assertIs(body["pricingModel"]["fitted"], False)
        self.assertIn("no fitted model behind it", body["pricingModel"]["note"])
        # The chain pointer goes to the live design, not the superseded one.
        self.assertEqual(body["chain"]["designDoc"], "docs/ON-CHAIN-DESIGN.md")
        self.assertFalse(body["chain"]["programDeployed"])
        self.assertIsNone(body["chain"]["programId"])
        self.assertEqual(body["contract"]["endpointsInContract"], CONTRACT_ENDPOINT_COUNT)
        self.assertEqual(body["contract"]["endpointsInContract"], 9)
        self.assertEqual(body["contract"]["endpointsImplemented"], 9)
        # nine contract endpoints plus /health
        self.assertEqual(body["contract"]["routesImplemented"], 10)

    def test_health_is_json_utf8(self) -> None:
        _, _, headers = self.get("/health")
        self.assertIn("application/json", headers["content-type"])


class TestEvents(ServerTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.store = arith.load()
        cls.ordered = sorted(
            arith.events(cls.store), key=lambda row: (row["startsAt"], row["id"])
        )

    def test_list_is_sorted_by_start_and_matches_the_store(self) -> None:
        status, body, _ = self.get("/api/events?limit=200")
        self.assertEqual(status, 200)
        self.assertEqual([event["id"] for event in body["items"]], [row["id"] for row in self.ordered])
        self.assertIsNone(body["nextCursor"])
        starts = [event["startsAt"] for event in body["items"]]
        self.assertEqual(starts, sorted(starts))

    def test_list_pagination_walks_the_whole_store_in_order(self) -> None:
        seen: list[str] = []
        cursor = None
        for _ in range(len(self.ordered) + 1):
            path = "/api/events?limit=1" + (f"&cursor={cursor}" if cursor else "")
            status, body, _ = self.get(path)
            self.assertEqual(status, 200)
            self.assertEqual(len(body["items"]), 1)
            seen.append(body["items"][0]["id"])
            cursor = body["nextCursor"]
            if cursor is None:
                break
        self.assertEqual(seen, [row["id"] for row in self.ordered])
        status, body, _ = self.get("/api/events?limit=1")
        self.assertEqual(body["nextCursor"], "1")

    def test_filters(self) -> None:
        status = arith.events(self.store)[0]["status"]
        expected = [row["id"] for row in self.ordered if row["status"] == status]
        _, by_status, _ = self.get(f"/api/events?status={status}&limit=200")
        self.assertEqual([event["id"] for event in by_status["items"]], expected)

        city = arith.events(self.store)[0]["city"]
        expected = [
            row["id"]
            for row in self.ordered
            if row["city"].lower() == city.lower()
        ]
        _, by_city, _ = self.get(f"/api/events?city={city}&limit=200")
        self.assertEqual([event["id"] for event in by_city["items"]], expected)

        needle = arith.events(self.store)[0]["name"].split(":")[0].split()[0].lower()
        expected = [
            row["id"]
            for row in self.ordered
            if needle in f"{row['name']} {row['venue']}".lower()
        ]
        _, by_text, _ = self.get(f"/api/events?q={needle}&limit=200")
        self.assertEqual([event["id"] for event in by_text["items"]], expected)
        self.assertTrue(expected, "the needle has to match at least one event")

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
        row = self.ordered[0]
        status, by_id, _ = self.get(f"/api/events/{row['id']}")
        _, by_slug, _ = self.get(f"/api/events/{row['slug']}")
        self.assertEqual(status, 200)
        self.assertEqual(by_id["id"], by_slug["id"])
        self.assertEqual(by_slug["slug"], row["slug"])
        self.assertEqual(by_slug["organizer"]["id"], row["organizerId"])
        self.assertFalse(by_slug["organizer"]["verified"])
        self.assertEqual(len(by_slug["tiers"]), len(row["tiers"]))
        self.assertEqual(by_slug["totalSupply"], sum(tier["totalSupply"] for tier in row["tiers"]))
        self.assertEqual(
            by_slug["issuedCount"], len(arith.tickets_for_event(self.store, row["id"]))
        )
        self.assertTrue(by_slug["description"].lower().startswith("synthetic demonstration record"))

    def test_missing_event_is_404_with_a_message(self) -> None:
        status, body, _ = self.get("/api/events/evt_nope")
        self.assertEqual(status, 404)
        self.assertIn("not found", body["message"])


class TestTickets(ServerTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.store = arith.load()

    def test_owner_wallet_filters_on_current_owner_not_issuee(self) -> None:
        moved = next(
            row
            for row in arith.tickets(self.store)
            if row["ownerWallet"] != row["issuedToWallet"]
            and row["issuedToWallet"]
            not in {other["ownerWallet"] for other in arith.tickets(self.store)}
        )
        _, current, _ = self.get(f"/api/tickets?ownerWallet={moved['ownerWallet']}&limit=200")
        ids = [ticket["id"] for ticket in current["items"]]
        self.assertIn(moved["id"], ids)
        self.assertTrue(all(ticket["ownerWallet"] == moved["ownerWallet"] for ticket in current["items"]))
        # The original issuee no longer holds it, and holds nothing else.
        _, issuee, _ = self.get(f"/api/tickets?ownerWallet={moved['issuedToWallet']}&limit=200")
        self.assertEqual(issuee["items"], [])

    def test_status_and_event_filters(self) -> None:
        status = arith.first_ticket_with_sales(self.store)["status"]
        expected = [
            row["id"] for row in arith.tickets(self.store) if row["status"] == status
        ]
        _, by_status, _ = self.get(f"/api/tickets?status={status}&limit=200")
        self.assertEqual([ticket["id"] for ticket in by_status["items"]], sorted(expected))

        busiest = max(
            arith.events(self.store),
            key=lambda row: len(arith.tickets_for_event(self.store, row["id"])),
        )
        expected = [
            row["id"]
            for row in arith.tickets(self.store)
            if row["eventId"] == busiest["id"]
        ]
        _, by_event, _ = self.get(f"/api/tickets?eventId={busiest['id']}&limit=200")
        self.assertEqual([ticket["id"] for ticket in by_event["items"]], sorted(expected))
        _, bad, _ = self.get("/api/tickets?status=almost_valid")
        self.assertEqual(bad["code"], "status_invalid")

    def test_detail_by_id_and_mint(self) -> None:
        ticket = arith.first_ticket_with_sales(self.store)
        expected = arith.ticket_totals(self.store, ticket["id"])
        _, by_id, _ = self.get(f"/api/tickets/{ticket['id']}")
        _, by_mint, _ = self.get(f"/api/tickets/{ticket['mintAddress']}")
        self.assertEqual(by_id["id"], by_mint["id"])
        for field, value in expected.items():
            self.assertEqual(by_id[field], value, field)

    def test_resale_history_is_the_real_computation(self) -> None:
        ticket = arith.first_ticket_with_sales(self.store, minimum=2)
        status, body, _ = self.get(f"/api/tickets/{ticket['id']}/resale-history")
        self.assertEqual(status, 200)
        self.assertEqual(body["stats"], arith.ticket_stats(self.store, ticket["id"]))
        self.assertEqual(
            [entry["id"] for entry in body["entries"]],
            [row["id"] for row in arith.entries_for(self.store, ticket["id"])],
        )
        self.assertTrue(body["dataSource"]["synthetic"])

    def test_missing_ticket_is_404(self) -> None:
        status, body, _ = self.get("/api/tickets/tkt_nope/resale-history")
        self.assertEqual(status, 404)
        self.assertIn("not found", body["message"])


class TestAnalytics(ServerTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.store = arith.load()

    def test_analytics_endpoint(self) -> None:
        event = arith.first_event_with_sales(self.store, minimum=3)
        status, body, _ = self.get(f"/api/events/{event['id']}/analytics")
        self.assertEqual(status, 200)
        expected = arith.event_analytics(self.store, event["id"])
        for field, value in expected.items():
            self.assertEqual(body[field], value, field)

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
