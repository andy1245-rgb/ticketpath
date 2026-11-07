"""Live check of the three loader-valid, engine-unpriceable stores, over a socket.

Each store is accepted by `LedgerAdapter.from_fixture` -- the loader raises nothing -- and
each used to leave the handler with no response at all (`HTTP 000`, "Empty reply from
server"). This script starts a real server per store on an ephemeral port, asks for the
page, and prints the status, the typed code and whether a page came back.
"""

import contextlib
import datetime as dt
import json
import os
import re
import sys
import tempfile
import threading
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import make_server

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
FIXTURE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "synthetic_store.json")


def store():
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)


def zero_priced_sale():
    data = store()
    for row in data["ledger"]:
        if row["kind"] == "sale":
            row["priceLamports"] = 0
            return data
    raise SystemExit("no sale row to zero")


def tierless_event():
    data = store()
    for event in data["events"]:
        if event["id"] == "evt_syn_03":
            event["tiers"] = []
            event.pop("totalSupply", None)
            event.pop("issuedCount", None)
    data["tickets"] = [ticket for ticket in data["tickets"] if ticket["eventId"] != "evt_syn_03"]
    kept = {ticket["id"] for ticket in data["tickets"]}
    data["ledger"] = [row for row in data["ledger"] if row["ticketId"] in kept]
    return data


def late_store_fixture():
    """evt_syn_04 opens 2026-11-14T00:00Z; put its last sale an hour after that."""
    data = store()
    event_of = {ticket["id"]: ticket["eventId"] for ticket in data["tickets"]}
    grouped = {}
    for row in data["ledger"]:
        grouped.setdefault(row["ticketId"], []).append(row)
    for ticket_id, rows in grouped.items():
        if event_of[ticket_id] != "evt_syn_04":
            continue
        rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
        if rows[-1]["kind"] == "sale":
            rows[-1]["occurredAt"] = "2026-11-14T01:00:00.000Z"
            return data
    raise SystemExit("no sale row to move")


@contextlib.contextmanager
def serving(data):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, handle)
    handle.close()
    engine = Orchestrator(
        LedgerAdapter.from_fixture(handle.name),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
    )
    server = make_server(0, "127.0.0.1", engine)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        os.unlink(handle.name)


def ask(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 - the point is to catch "Empty reply"
        return 0, f"{type(exc).__name__}: {exc}"


def code_of(html):
    visible = re.sub(r"<[^>]+>", " ", html)
    for code in ("sale_not_priced", "sale_after_event_start", "event_has_no_tier", "console_error"):
        if code in visible:
            return code
    return ""


CASES = [
    ("zero-priced sale", zero_priced_sale(), "/?event=evt_syn_04"),
    ("sale after start", late_store_fixture(), "/?event=evt_syn_04&asOf=2026-11-14T12:00:00Z"),
    ("event with no tiers", tierless_event(), "/?event=evt_syn_03"),
    ("event with no tiers / default", tierless_event(), "/"),
]

failures = 0
for name, data, path in CASES:
    with serving(data) as base:
        status, body = ask(base + path)
        is_page = "<!doctype html>" in body
        ok = status != 0 and is_page
        failures += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'} {name:32s} {path:44s} status={status} page={is_page} code={code_of(body) or '-'}")

print("\nFAILURES:", failures)
sys.exit(1 if failures else 0)
