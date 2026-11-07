"""HTTP entry point: routing only.

Run with `python3 -m ticketpath.server` (or `python3 -m ticketpath.server --port N`).
Binds 127.0.0.1 on port 8788 by default; `TICKETPATH_PORT` overrides it. Port 8787
belongs to another process on this machine and is refused outright rather than
raced for.

What lives here and nowhere else: the route table, HTTP parsing and serialisation,
CORS, and turning an exception into a status code. Every decision about data goes
to the orchestrator, and every number comes from `ticketpath.core`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import parse_qs, unquote, urlsplit

from ticketpath import __version__
from ticketpath.adapters.ledger_adapter import LedgerAdapter, StoreError
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.api import analytics, events, health, tickets, wallets
from ticketpath.errors import ApiError
from ticketpath.orchestrator import Orchestrator

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8788
RESERVED_PORTS = {8787: "the fleet page owns 127.0.0.1:8787"}
DEFAULT_CLUSTER = "devnet"
CLUSTERS = ("devnet", "testnet", "mainnet-beta", "localnet")
MAX_BODY_BYTES = 64 * 1024
CONTRACT_ENDPOINT_COUNT = 9  # API_CONTRACT.md lists nine routes; /health is ours

Handler = Callable[[Orchestrator, dict, dict, dict | None], tuple[int, dict]]

# (method, template segments, handler). A segment starting with ":" binds a path value.
ROUTES: tuple[tuple[str, tuple[str, ...], Handler], ...] = (
    (
        "GET",
        ("health",),
        lambda o, p, q, b: health.health(
            o, implemented_contract_route_count(), CONTRACT_ENDPOINT_COUNT, implemented_route_count()
        ),
    ),
    ("GET", ("api", "events"), lambda o, p, q, b: events.list_events(o, q)),
    ("GET", ("api", "events", ":idOrSlug"), lambda o, p, q, b: events.get_event(o, p["idOrSlug"])),
    ("GET", ("api", "events", ":eventId", "analytics"), lambda o, p, q, b: analytics.get_event_analytics(o, p["eventId"])),
    ("GET", ("api", "tickets"), lambda o, p, q, b: tickets.list_tickets(o, q)),
    ("GET", ("api", "tickets", ":ticketId"), lambda o, p, q, b: tickets.get_ticket(o, p["ticketId"])),
    ("GET", ("api", "tickets", ":ticketId", "resale-history"), lambda o, p, q, b: tickets.get_resale_history(o, p["ticketId"])),
    ("GET", ("api", "wallets", ":wallet", "verification"), lambda o, p, q, b: wallets.get_verification(o, p["wallet"])),
    ("POST", ("api", "wallets", ":wallet", "verification", "challenge"), lambda o, p, q, b: wallets.start_challenge(o, p["wallet"])),
    ("POST", ("api", "wallets", ":wallet", "verification"), lambda o, p, q, b: wallets.complete_verification(o, p["wallet"], b or {})),
)


def implemented_route_count() -> int:
    """Every route this server answers, /health included."""
    return len(ROUTES)


def implemented_contract_route_count() -> int:
    """Routes that satisfy an endpoint in API_CONTRACT.md."""
    return sum(1 for _, template, _ in ROUTES if template[0] == "api")


def match(method: str, path: str) -> tuple[Handler, dict] | tuple[None, list[str]]:
    """Resolve a request. Returns the handler and its path values, or the allowed methods."""
    segments = tuple(unquote(part) for part in path.strip("/").split("/") if part != "")
    allowed: set[str] = set()
    for route_method, template, handler in ROUTES:
        if len(template) != len(segments):
            continue
        values: dict[str, str] = {}
        matched = True
        for template_part, actual in zip(template, segments):
            if template_part.startswith(":"):
                values[template_part[1:]] = actual
            elif template_part != actual:
                matched = False
                break
        if not matched:
            continue
        if route_method == method:
            return handler, values
        allowed.add(route_method)
    return None, sorted(allowed)


class TicketpathHandler(BaseHTTPRequestHandler):
    """Serialises one request to one JSON response. No data decisions in here."""

    server_version = f"ticketpath/{__version__}"
    protocol_version = "HTTP/1.1"
    orchestrator: Orchestrator  # set by the server factory
    allow_origin: str = "*"

    # -- verbs -----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - http.server's naming
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, None)

    # -- plumbing --------------------------------------------------------

    def _handle(self, method: str) -> None:
        split = urlsplit(self.path)
        try:
            handler, extra = match(method, split.path)
            if handler is None:
                if extra:
                    raise ApiError(
                        405,
                        f"{method} is not allowed here; allowed: {', '.join(extra)}",
                        "method_not_allowed",
                    )
                raise ApiError(404, f"no route for {split.path}", "no_route")
            query = {key: values[0] for key, values in parse_qs(split.query, keep_blank_values=True).items()}
            body = self._read_json_body() if method == "POST" else None
            status, payload = handler(self.orchestrator, extra, query, body)
            self._send(status, payload)
        except ApiError as exc:
            self._send(exc.status, exc.payload())
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:  # noqa: BLE001 - a server must not die on one request
            traceback.print_exc(file=sys.stderr)
            self._send(500, {"message": "internal server error", "status": 500, "code": "internal"})

    def _read_json_body(self) -> dict | None:
        length_header = self.headers.get("content-length")
        if length_header is None:
            return None
        try:
            length = int(length_header)
        except ValueError as exc:
            raise ApiError(400, "content-length is not an integer", "body_length_invalid") from exc
        if length == 0:
            return None
        if length > MAX_BODY_BYTES:
            raise ApiError(413, "request body too large", "body_too_large")
        raw = self.rfile.read(length)
        if not raw.strip():
            return None
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(400, "request body is not valid UTF-8 JSON", "body_invalid") from exc
        if not isinstance(parsed, dict):
            raise ApiError(400, "request body must be a JSON object", "body_invalid")
        return parsed

    def _send(self, status: int, payload: dict | None) -> None:
        body = b"" if payload is None else json.dumps(payload, ensure_ascii=False, indent=None).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.send_header("access-control-allow-origin", self.allow_origin)
        self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")
        self.send_header("access-control-max-age", "600")
        self.send_header("cache-control", "no-store")
        self.send_header("x-ticketpath-version", __version__)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - base signature
        sys.stderr.write(f"{self.address_string()} {format % args}\n")


def build_orchestrator() -> Orchestrator:
    """Wire the adapters to the orchestrator. Called once at startup, not at import."""
    cluster = os.environ.get("TICKETPATH_CLUSTER", DEFAULT_CLUSTER).strip()
    if cluster not in CLUSTERS:
        raise StoreError(f"TICKETPATH_CLUSTER must be one of {CLUSTERS}, got {cluster!r}")
    return Orchestrator(
        ledger=LedgerAdapter.from_env(),
        rpc=RpcAdapter.from_env(cluster),
        pricing_model=PricingModelAdapter(),
        cluster=cluster,
    )


def resolve_port(explicit: int | None = None) -> int:
    """Port from the flag, then the environment, then the default. 8787 is refused."""
    if explicit is not None:
        port = explicit
    else:
        raw = os.environ.get("TICKETPATH_PORT")
        try:
            port = int(raw) if raw else DEFAULT_PORT
        except ValueError as exc:
            raise SystemExit(f"TICKETPATH_PORT must be an integer, got {raw!r}") from exc
    if not 1 <= port <= 65535:
        raise SystemExit(f"port {port} is out of range")
    if port in RESERVED_PORTS:
        raise SystemExit(f"refusing to bind port {port}: {RESERVED_PORTS[port]}")
    return port


def make_server(port: int, host: str = DEFAULT_HOST, orchestrator: Orchestrator | None = None) -> ThreadingHTTPServer:
    """Build a server without starting it, so tests can bind an ephemeral port."""
    engine = orchestrator or build_orchestrator()
    handler_class = type("BoundTicketpathHandler", (TicketpathHandler,), {"orchestrator": engine})
    server = ThreadingHTTPServer((host, port), handler_class)
    server.daemon_threads = True
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m ticketpath.server",
        description="ticketpath backend: contract endpoints over a ledger, computed by the core.",
    )
    parser.add_argument("--port", type=int, default=None, help=f"port to bind (default {DEFAULT_PORT})")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"address to bind (default {DEFAULT_HOST})")
    args = parser.parse_args(argv)
    port = resolve_port(args.port)
    orchestrator = build_orchestrator()
    server = make_server(port, args.host, orchestrator)
    source = orchestrator.data_source()
    print(
        f"ticketpath {__version__} listening on http://{args.host}:{port} "
        f"dataSource={source['mode']} synthetic={source['synthetic']} "
        f"cluster={orchestrator.cluster} routes={implemented_route_count()}",
        flush=True,
    )
    if source["synthetic"]:
        print(f"  {source['label']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopping", file=sys.stderr, flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
