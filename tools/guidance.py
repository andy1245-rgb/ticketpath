"""Print the console payload for a URL's parameters, so the whole surface is CLI-drivable.

    python3 tools/guidance.py --events
    python3 tools/guidance.py --event evt_syn_02 --tier tier_stg_general \
        --as-of 2026-11-07T12:00:00Z --cap 1500 --tau 0.20

The event and tier ids are whatever the store holds, so the CLI lists them rather than
documenting a value the generator can change. The URL is the primary surface; this is
the same payload without a browser, which is what makes it batch-testable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ticketpath.adapters.ledger_adapter import LedgerAdapter  # noqa: E402
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter  # noqa: E402
from ticketpath.adapters.rpc_adapter import RpcAdapter  # noqa: E402
from ticketpath.orchestrator import Orchestrator  # noqa: E402


def build_orchestrator(as_of: str | None) -> Orchestrator:
    """Fixture ledger, RPC off, no model registered outside the seam. Reads nothing else."""
    if as_of is None:
        clock = None
    else:
        from datetime import datetime, timezone

        from ticketpath.core.timeutil import parse

        fixed = parse(as_of)
        clock = lambda: fixed  # noqa: E731 - one line, and the clock is a parameter here
        del datetime, timezone
    return Orchestrator(
        ledger=LedgerAdapter.from_env(),
        rpc=RpcAdapter.from_env("devnet"),
        pricing_model=PricingModelAdapter(),
        cluster="devnet",
        now=clock,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/guidance.py", description="the console payload as JSON")
    parser.add_argument("--events", action="store_true", help="list event and tier ids and exit")
    parser.add_argument("--event")
    parser.add_argument("--tier")
    parser.add_argument("--as-of", dest="as_of")
    parser.add_argument("--cap")
    parser.add_argument("--fee")
    parser.add_argument("--tau")
    parser.add_argument("--sim", action="store_true")
    args = parser.parse_args(argv)

    orchestrator = build_orchestrator(args.as_of)
    if args.events:
        for event in orchestrator.ledger.events():
            tiers = ", ".join(f"{tier['id']} ({tier['name']})" for tier in event["tiers"])
            print(f"{event['id']}  {event['name']}\n    tiers: {tiers}")
        return 0
    payload = orchestrator.price_guidance(
        event_id=args.event,
        tier_id=args.tier,
        as_of=args.as_of,
        cap_bps=args.cap,
        fee_lamports=args.fee,
        tau=args.tau,
        show_sim=args.sim,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
