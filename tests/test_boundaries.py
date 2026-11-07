"""The boundaries that keep this build honest, tested as boundaries.

1. No module reaches a network or a chain: only adapters may, and today the only
   adapter that could (RPC) does not open a socket at all.
2. The core is pure: it never imports an adapter or the orchestrator.
3. `lib/mock`, the frontend's fixture directory, is referenced nowhere in the
   package. Our fixtures are separate, labelled files.
4. The model seam refuses rather than inventing a number.
5. Port 8787 can never be bound by this server.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.server import DEFAULT_PORT, resolve_port

PACKAGE = Path(__file__).resolve().parents[1] / "ticketpath"

ALLOWED_ROOTS = {
    "__future__",
    "argparse",
    "datetime",
    "hashlib",
    "http",
    "json",
    "os",
    "pathlib",
    "secrets",
    "sys",
    "threading",
    "traceback",
    "typing",
    "urllib",
}
NETWORK_ROOTS = {"socket", "ssl", "http", "urllib", "subprocess", "asyncio"}


def _sources() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _imported_roots(text: str) -> set[str]:
    roots: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("from ") and " import " in stripped:
            roots.add(stripped.split()[1].split(".")[0])
        elif stripped.startswith("import "):
            for part in stripped[len("import ") :].split(","):
                name = part.strip().split(" as ")[0].strip()
                if name:
                    roots.add(name.split(".")[0])
    return roots


class TestBoundaries(unittest.TestCase):
    def test_no_package_file_reaches_for_the_frontend_fixtures(self) -> None:
        for path in _sources():
            with self.subTest(path=path.name):
                self.assertNotIn("lib/mock", _read(path))
                for fixture_name in ("events.json", "tickets.json", "ledger.json", "wallets.json"):
                    self.assertNotIn(fixture_name, _read(path))

    def test_only_the_server_speaks_http(self) -> None:
        for path in _sources():
            roots = _imported_roots(_read(path))
            reachable = roots & NETWORK_ROOTS
            with self.subTest(path=path.name):
                if path.name == "server.py":
                    self.assertEqual(reachable, {"http", "urllib"})
                else:
                    self.assertEqual(reachable, set(), f"{path.name} imports {reachable}")

    def test_core_imports_nothing_from_above_it(self) -> None:
        for path in sorted((PACKAGE / "core").rglob("*.py")):
            text = _read(path)
            with self.subTest(path=path.name):
                self.assertNotIn("ticketpath.adapters", text)
                self.assertNotIn("ticketpath.orchestrator", text)
                self.assertNotIn("ticketpath.api", text)
                self.assertNotIn("ticketpath.server", text)

    def test_core_has_no_ambient_clock(self) -> None:
        for path in sorted((PACKAGE / "core").rglob("*.py")):
            text = _read(path)
            with self.subTest(path=path.name):
                self.assertNotIn("datetime.now(", text)
                self.assertNotIn("time.time(", text)
                self.assertNotIn("utcnow(", text)

    def test_no_third_party_imports(self) -> None:
        for path in _sources():
            for root in _imported_roots(_read(path)):
                if root == "ticketpath":
                    continue
                with self.subTest(path=path.name, module=root):
                    self.assertIn(root, ALLOWED_ROOTS, f"unexpected dependency {root}")


class TestRpcAdapterNeverPretends(unittest.TestCase):
    def test_disabled_by_default(self) -> None:
        adapter = RpcAdapter.from_env("devnet")
        self.assertFalse(adapter.enabled)
        answer = adapter.transfer_enforcement("FXTUREmint111111111111111111111111111111111")
        self.assertFalse(answer["enforced"])
        self.assertFalse(answer["checked"])
        self.assertEqual(answer["reason"], "rpc_disabled")

    def test_enabled_without_a_program_id_still_claims_nothing(self) -> None:
        adapter = RpcAdapter(enabled=True, rpc_url=None, program_id=None, cluster="devnet")
        answer = adapter.transfer_enforcement("FXTUREmint111111111111111111111111111111111")
        self.assertFalse(answer["enforced"])
        self.assertFalse(answer["checked"])
        self.assertEqual(answer["reason"], "no_program_id_configured")

    def test_program_status_never_claims_a_deployment(self) -> None:
        status = RpcAdapter.from_env("devnet").program_status()
        self.assertFalse(status["programDeployed"])
        self.assertIsNone(status["programId"])


class TestPricingSeam(unittest.TestCase):
    def test_no_model_means_no_number(self) -> None:
        adapter = PricingModelAdapter()
        self.assertFalse(adapter.available)
        estimate = adapter.estimate({"ticketId": "tkt_fixture_0001", "asOf": "2026-11-07T12:00:00.000Z"})
        self.assertFalse(estimate["available"])
        self.assertEqual(estimate["basis"], "no_model_registered")
        self.assertIsNone(estimate["expectedResaleLamports"])
        self.assertIsNone(estimate["saleProbability"])
        self.assertIsNone(estimate["recommendedPrimaryLamports"])
        self.assertIsNone(estimate["modelVersion"])

    def test_a_registered_model_is_passed_through_unchanged(self) -> None:
        adapter = PricingModelAdapter()
        adapter.register(
            lambda request: {
                "modelVersion": "test-0",
                "asOf": request["asOf"],
                "expectedResaleLamports": 1_000,
                "saleProbability": 0.5,
                "recommendedPrimaryLamports": 900,
                "horizonHours": 24,
                "basis": "test",
            },
            "test-0",
        )
        estimate = adapter.estimate({"asOf": "2026-11-07T12:00:00.000Z"})
        self.assertTrue(estimate["available"])
        self.assertEqual(estimate["expectedResaleLamports"], 1_000)
        self.assertEqual(estimate["modelVersion"], "test-0")

    def test_a_model_that_returns_the_wrong_shape_is_refused(self) -> None:
        adapter = PricingModelAdapter()
        adapter.register(lambda request: {"expectedResaleLamports": 1}, "broken-0")
        with self.assertRaises(ValueError):
            adapter.estimate({})


class TestPortRules(unittest.TestCase):
    def test_default_is_8788(self) -> None:
        self.assertEqual(resolve_port(), DEFAULT_PORT)
        self.assertEqual(DEFAULT_PORT, 8788)

    def test_8787_is_refused(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            resolve_port(8787)
        self.assertIn("8787", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
