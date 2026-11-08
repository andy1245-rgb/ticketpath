"""One live test, opt-in, against a local validator this file starts and always stops.

    MARKET_SWARM_LIVE=1 python3 -m unittest market_swarm.tests.test_gateway_live -v

It proves the three things a fake cluster cannot: the program deploys and is called, a transfer at
the ceiling lands, and a transfer one lamport over it lands as a *failed* transaction carrying the
program's own 6010 and its own signature. The last read is the on-chain argument for the
single-transaction design: the refused transaction rolled its own `SetPendingPrice` back, so the
record still shows the accepted price.

The whole body is bounded by a wall clock of 240 s and the validator is stopped in `finally`, on
every path. Nothing here touches a public cluster, a funding source, or the network except the
validator's own `--clone` of Token-2022 at boot.
"""

from __future__ import annotations

import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from market_swarm import gateway as gw
from market_swarm.config import EventSpec

#: The hard wall-clock bound for the whole test, timer included.
WALL_CLOCK_SECONDS = 240.0

FACE = 1_000_000_000
CAP_BPS = 2500
CEILING = FACE * (10_000 + CAP_BPS) // 10_000  # 1_250_000_000, the design's own worked pair


@unittest.skipUnless(
    os.environ.get("MARKET_SWARM_LIVE") == "1",
    "live: set MARKET_SWARM_LIVE=1 to start a local validator and spend about two minutes",
)
class LiveGatewayTest(unittest.TestCase):
    def test_a_capped_event_transfers_and_refuses_on_chain(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_dir = Path(tmp.name)
        gateway = gw.make_gateway("local", run_dir=run_dir)
        expired: list[float] = []

        def hard_stop() -> None:
            expired.append(time.monotonic())
            gateway.stop()

        timer = threading.Timer(WALL_CLOCK_SECONDS, hard_stop)
        timer.daemon = True
        started = time.monotonic()
        timer.start()
        try:
            status = gateway.start()
            self.assertEqual(status["cluster"], "local")
            self.assertTrue(status["healthy"], status)
            self.assertIsNotNone(status["program_id"])

            event = gateway.create_event(
                EventSpec(
                    event_id="evt_live",
                    face_lamports=FACE,
                    mode="capped",
                    cap_bps=CAP_BPS,
                    tickets=2,
                    rounds=1,
                    round_seconds=0,
                )
            )
            self.assertEqual(event.ceiling_lamports, CEILING)
            record = event.read_record()
            self.assertEqual(record["face_lamports"], FACE)
            self.assertEqual(record["cap_bps"], CAP_BPS)
            self.assertEqual(record["status"], 1)

            seller = event.open_account("seller")
            buyer = event.open_account("buyer")
            for address in (seller, buyer):
                self.assertRegex(address, r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
            event.stock(3)  # minted to the house; the house seeds the agent below

            # Seed the agent with two tickets at face, so the two transfers under test are a
            # wallet-to-wallet sale, and the refused one still has a ticket to fail against: a
            # refusal caused by an empty account would be the wrong finding entirely.
            for hop in range(2):
                seed = event.transfer(
                    from_label=gw.HOUSE_LABEL, to_label="seller", price_lamports=FACE
                )
                self.assertEqual(seed.status, "ok", f"hop {hop}: {seed.error_code}: {seed.logs}")

            accepted = event.transfer(
                from_label="seller", to_label="buyer", price_lamports=CEILING
            )
            self.assertEqual(accepted.status, "ok", f"{accepted.error_code}: {accepted.logs}")
            self.assertIsNotNone(accepted.signature, "an admitted transfer has a signature")
            self.assertIsNone(accepted.error_code)
            self.assertIsNotNone(accepted.slot)
            self.assertGreaterEqual(accepted.latency_ms, 0)
            self.assertTrue(
                any("ticketpath: cap admitted" in line for line in accepted.logs),
                f"the hook's own log line is missing: {accepted.logs}",
            )
            self.assertEqual(event.read_record()["pending_price_lamports"], CEILING)

            refused = event.transfer(
                from_label="seller", to_label="buyer", price_lamports=CEILING + 1
            )
            self.assertEqual(refused.status, "refused", f"{refused.error_code}: {refused.logs}")
            self.assertEqual(refused.error_code, gw.E_CAP_EXCEEDED, refused.logs)
            self.assertIsNotNone(refused.signature, "a refusal sent with preflight off has its own signature")
            self.assertNotEqual(refused.signature, accepted.signature)
            self.assertIsNotNone(refused.slot)
            self.assertTrue(
                any("ticketpath: cap exceeded" in line for line in refused.logs),
                f"the hook's own log line is missing: {refused.logs}",
            )

            # The atomicity claim, read off the chain: the refused transaction's own staging was
            # rolled back with it, so the record still carries the accepted price. Two separate
            # transactions would have left CEILING + 1 staged here.
            self.assertEqual(event.read_record()["pending_price_lamports"], CEILING)

            # And the refused transfer moved nothing and minted nothing.
            self.assertEqual(gateway._token_balance(event.ticket_account("buyer")), 1)
            self.assertEqual(gateway._token_balance(event.ticket_account("seller")), 1)
            self.assertEqual(gateway._token_balance(event.ticket_account(gw.HOUSE_LABEL)), 1)

            self.assertEqual(gateway.status()["mints"], (event.mint,))
        finally:
            timer.cancel()
            gateway.stop()

        elapsed = time.monotonic() - started
        self.assertEqual(expired, [], "the 240 s wall clock fired and stopped the gateway mid-test")
        self.assertLess(elapsed, WALL_CLOCK_SECONDS)
        self.assertFalse((run_dir / "validator-ledger").exists(), "the ledger is deleted on stop")


if __name__ == "__main__":
    unittest.main()
