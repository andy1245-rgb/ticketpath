"""The wallet verification flow over HTTP, with a real Ed25519 signature.

The keypair is a fixed 32-byte seed generated inside this test, signed by
`core.ed25519.sign` (test support), and the wallet address is base58 of the
derived public key. No key material belongs to anyone: it exists for one test
run and gates nothing.

The server's clock is injected, so expiry is tested by moving the clock rather
than by sleeping.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.core import base58, ed25519
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import make_server

SEED = bytes(range(32))
PUBLIC_KEY, _ = ed25519.sign(SEED, b"")  # derive the keypair's public half
WALLET = base58.encode(PUBLIC_KEY)
OTHER_SEED = bytes(range(1, 33))
OTHER_PUBLIC, _ = ed25519.sign(OTHER_SEED, b"")
OTHER_WALLET = base58.encode(OTHER_PUBLIC)


class FakeClock:
    def __init__(self) -> None:
        self.moment = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.moment

    def advance(self, seconds: int) -> None:
        self.moment = self.moment + timedelta(seconds=seconds)


class WalletFlowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        orchestrator = Orchestrator(
            LedgerAdapter.from_fixture(),
            RpcAdapter.from_env("devnet"),
            PricingModelAdapter(),
            "devnet",
            now=self.clock,
        )
        self.server = make_server(0, "127.0.0.1", orchestrator)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def get(self, path: str) -> tuple[int, dict]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def post(self, path: str, body: dict | None = None) -> tuple[int, dict]:
        data = b"" if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path, data=data, method="POST", headers={"content-type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def sign_challenge(self, wallet: str, seed: bytes, challenge: dict) -> dict:
        message = (
            "Verify wallet ownership for ticket issuance.\n"
            "\n"
            f"Wallet: {wallet}\n"
            f"Nonce: {challenge['nonce']}\n"
            "Cluster: devnet"
        ).encode("utf-8")
        _, signature = ed25519.sign(seed, message)
        return {"nonce": challenge["nonce"], "signature": base58.encode(signature)}


class TestUnknownWallet(WalletFlowTestCase):
    def test_unknown_wallet_is_200_and_unverified(self) -> None:
        status, body = self.get(f"/api/wallets/{WALLET}/verification")
        self.assertEqual(status, 200)
        self.assertFalse(body["verified"])
        self.assertIsNone(body["verifiedAt"])
        self.assertIsNone(body["method"])
        self.assertFalse(body["canPurchase"])
        self.assertFalse(body["canReceiveTransfer"])
        self.assertIn("wallet_not_verified", body["flags"])
        self.assertFalse(body["dataSource"]["synthetic"])

    def test_malformed_wallet_is_400(self) -> None:
        status, body = self.get("/api/wallets/not-a-key/verification")
        self.assertEqual(status, 400)
        self.assertEqual(body["code"], "wallet_malformed")


class TestChallengeAndVerify(WalletFlowTestCase):
    def test_full_flow_verifies_then_persists_in_memory(self) -> None:
        status, challenge = self.post(f"/api/wallets/{WALLET}/verification/challenge")
        self.assertEqual(status, 200)
        self.assertEqual(len(challenge["nonce"]), 32)
        self.assertEqual(challenge["expiresAt"], "2026-11-07T12:05:00.000Z")

        status, result = self.post(
            f"/api/wallets/{WALLET}/verification", self.sign_challenge(WALLET, SEED, challenge)
        )
        self.assertEqual(status, 200, result)
        self.assertTrue(result["verified"])
        self.assertEqual(result["method"], "wallet_signature")
        self.assertEqual(result["verifiedAt"], "2026-11-07T12:00:00.000Z")
        self.assertTrue(result["canPurchase"])
        self.assertTrue(result["canReceiveTransfer"])

        _, again = self.get(f"/api/wallets/{WALLET}/verification")
        self.assertTrue(again["verified"])

    def test_a_real_signature_from_the_wrong_key_is_refused(self) -> None:
        _, challenge = self.post(f"/api/wallets/{WALLET}/verification/challenge")
        status, body = self.post(
            f"/api/wallets/{WALLET}/verification", self.sign_challenge(WALLET, OTHER_SEED, challenge)
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["code"], "signature_invalid")

    def test_signing_a_different_message_is_refused(self) -> None:
        _, challenge = self.post(f"/api/wallets/{WALLET}/verification/challenge")
        _, signature = ed25519.sign(SEED, b"some other message")
        status, body = self.post(
            f"/api/wallets/{WALLET}/verification",
            {"nonce": challenge["nonce"], "signature": base58.encode(signature)},
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["code"], "signature_invalid")

    def test_nonce_is_single_use(self) -> None:
        _, challenge = self.post(f"/api/wallets/{WALLET}/verification/challenge")
        body = self.sign_challenge(WALLET, SEED, challenge)
        first, _ = self.post(f"/api/wallets/{WALLET}/verification", body)
        second, error = self.post(f"/api/wallets/{WALLET}/verification", body)
        self.assertEqual(first, 200)
        self.assertEqual(second, 400)
        self.assertEqual(error["code"], "nonce_unknown")

    def test_expired_nonce_is_refused(self) -> None:
        _, challenge = self.post(f"/api/wallets/{WALLET}/verification/challenge")
        body = self.sign_challenge(WALLET, SEED, challenge)
        self.clock.advance(301)
        status, error = self.post(f"/api/wallets/{WALLET}/verification", body)
        self.assertEqual(status, 400)
        self.assertEqual(error["code"], "nonce_expired")

    def test_nonce_issued_to_another_wallet_is_refused(self) -> None:
        _, challenge = self.post(f"/api/wallets/{WALLET}/verification/challenge")
        status, error = self.post(
            f"/api/wallets/{OTHER_WALLET}/verification", self.sign_challenge(OTHER_WALLET, OTHER_SEED, challenge)
        )
        self.assertEqual(status, 400)
        self.assertEqual(error["code"], "nonce_wallet_mismatch")

    def test_missing_fields_and_bad_signature_encoding_are_400(self) -> None:
        _, challenge = self.post(f"/api/wallets/{WALLET}/verification/challenge")
        status, body = self.post(f"/api/wallets/{WALLET}/verification", {"nonce": challenge["nonce"]})
        self.assertEqual(status, 400)
        self.assertEqual(body["code"], "signature_missing")

        status, body = self.post(
            f"/api/wallets/{WALLET}/verification", {"nonce": challenge["nonce"], "signature": "not base 58"}
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["code"], "signature_malformed")

    def test_unknown_wallet_endpoint_requires_a_post(self) -> None:
        status, _ = self.get(f"/api/wallets/{WALLET}/verification/challenge")
        self.assertEqual(status, 405)


if __name__ == "__main__":
    unittest.main()
