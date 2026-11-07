"""Live check of the three engine-unpriceable stores, over a socket.

The loader does not raise on these stores: it holds the offending event back with a typed
reason and keeps serving the rest, which is the rule that stops one malformed row from
turning a whole store into a refusal. This script starts a real server per store on an
ephemeral port, asks for the held-back event's page, then asks for a healthy event on the
same server, and prints the status, the typed code and whether a page came back for each.

Before the loader learned these three states, every one of them left the handler with no
response at all (`HTTP 000`, "Empty reply from server").
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


def store_line(html):
    """The evidence strip's account of the store, tag-stripped: the total and what was served.

    N6: the noun `in the store` was printed from the served list, so a store of eight events
    with one held back read `7 events in the store`. The healthy page must now name the
    store's own total, the served count and that one was withheld.
    """
    stripped = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    visible = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", stripped))
    found = re.search(
        r"\[FIXTURE\] (\d+) events in the store, \[FIXTURE\] (\d+) served, one held back", visible
    )
    return (int(found.group(1)), int(found.group(2))) if found else None


def code_of(html):
    visible = re.sub(r"<[^>]+>", " ", html)
    for code in ("sale_not_priced", "sale_after_event_start", "event_has_no_tier", "console_error"):
        if code in visible:
            return code
    return ""


# (name, store, the held-back event's URL, the code it must print, a healthy event's URL,
# the code that page must not print). The second URL is the half the old behaviour failed:
# one bad event used to refuse every event in the store.
CASES = [
    (
        "zero-priced sale",
        zero_priced_sale(),
        "/?event=evt_syn_01",
        "sale_not_priced",
        "/?event=evt_syn_04",
    ),
    (
        "sale after start",
        late_store_fixture(),
        "/?event=evt_syn_04&asOf=2026-11-14T12:00:00Z",
        "sale_after_event_start",
        "/?event=evt_syn_01",
    ),
    ("event with no tiers", tierless_event(), "/?event=evt_syn_03", "event_has_no_tier", "/?event=evt_syn_02"),
    ("event with no tiers / default", tierless_event(), "/", "", "/?event=evt_syn_02"),
]

failures = 0
for name, data, path, want, healthy_path in CASES:
    with serving(data) as base:
        status, body = ask(base + path)
        is_page = "<!doctype html>" in body
        code = code_of(body)
        ok = status != 0 and is_page and code == want
        failures += 0 if ok else 1
        print(
            f"{'ok  ' if ok else 'FAIL'} {name:32s} {path:44s} "
            f"status={status} page={is_page} code={code or '-'}"
        )
        status, body = ask(base + healthy_path)
        code = code_of(body)
        rest_ok = status == 200 and "<!doctype html>" in body and not code
        failures += 0 if rest_ok else 1
        print(
            f"{'ok  ' if rest_ok else 'FAIL'} {'  the rest still prices':32s} "
            f"{healthy_path:44s} status={status} page={'<!doctype html>' in body} code={code or '-'}"
        )
        served = store_line(body)
        counted = len(data["events"])
        counted_ok = served == (counted, counted - 1)
        failures += 0 if counted_ok else 1
        print(
            f"{'ok  ' if counted_ok else 'FAIL'} {'  the store count is the store':32s} "
            f"file={counted} page={served}"
        )

print("\nFAILURES:", failures)
sys.exit(1 if failures else 0)
