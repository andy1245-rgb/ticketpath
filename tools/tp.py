#!/usr/bin/env python3
"""The backend's command line: one verb per surface, and the commit gate.

Run it as `python3 tools/tp.py <verb>`; from anywhere, `python3 <repo>/tools/tp.py`.

What it is for. Every route this repository serves has two readers: a browser (the
console) and a person at a terminal. The browser path was always there. This is the
terminal path, so the whole backend can be driven, read and batch-tested without a
browser and without importing `ticketpath` into the caller's process.

Three rules the output obeys, because they are the rules the product obeys:

1. Provenance travels with every line. A line the CLI composes carries the badge of the
   source it read -- `[FIXTURE]` when the API says `dataSource.synthetic` is true,
   `[DECLARED]` when the ledger is the declared-empty one. A page the server rendered is
   passed through with its own badges where the page put them, and a line of page text
   that carries none gets the source badge in front, so no line is ever badge-free.
2. A refusal is printed, never stripped. A 4xx is the API's answer and it is shown with
   its message and its typed code; the exit code is what changes.
3. No number is recomputed here. Counts are counted from what the route returned, money
   is printed in the integer lamports the route sent, and nothing is converted to SOL by
   this file.

Exit codes, the same for every verb:

    0   ok: the server answered and the answer is the product
    1   a check failed, or the route answered 4xx/5xx (the refusal is printed in full)
    2   usage: a flag, a verb or an argument is wrong
    3   the server did not answer; the line printed names how to start it

Standard library only, like the rest of the tree. No dependency was added for this.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "http://127.0.0.1:8788"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_UNREACHABLE = 3

DEFAULT_TIMEOUT = 15.0

# Ports this machine already uses for something else. The gate's ephemeral server must
# never land on one of them: 8788 is the operator's server, 8787 is the fleet page, and
# 3000/3001 are the frontend.
RESERVED_PORTS = frozenset({8787, 8788, 3000, 3001})

# Where an independent property sweep lives when a review left one on the box: named by
# this variable, never written into this file. The sweep takes the base URL as its first
# argument and imports nothing from this repository, which is exactly why it is preferred
# over the project's own checker -- it cannot share a bug with the thing it checks. Its
# location is configuration because a scratch path is the operator's machine, and this
# file is published. Unset means the optional sweep is skipped and `sweep` says so, then
# uses `tools/console-check.py`; with neither tool present that is a failed check.
AUDIT_SWEEP_ENV = "TP_SWEEP"

BADGE_TOKEN = re.compile(r"\[[A-Z][A-Z0-9_]{2,}\]")


class Unreachable(Exception):
    """No HTTP answer: the server is down, the port is wrong, or nothing replied in time."""


class Usage(Exception):
    """The command line itself is wrong."""


# -- provenance ------------------------------------------------------------


def badge_for(payload: dict | None) -> str:
    """The badge the API's own envelope implies, never one invented here.

    `dataSource.synthetic` true is a fixture: `[FIXTURE]`. Anything else is a mode a
    person declared (today the only other ledger mode is `empty`), and its counts are a
    declared state rather than a measurement: `[DECLARED]`.
    """
    source = (payload or {}).get("dataSource") or {}
    if source.get("synthetic"):
        return "[FIXTURE]"
    return "[DECLARED]"


def provenance_line(payload: dict | None) -> str | None:
    """The API's own provenance sentence, verbatim, when the envelope carries one."""
    source = (payload or {}).get("dataSource") or {}
    label = (source.get("label") or "").strip()
    if not label:
        return None
    return f"{badge_for(payload)} {label}"


# -- transport -------------------------------------------------------------


def normalise_base(raw: str) -> str:
    base = (raw or "").strip().rstrip("/")
    if base.startswith("http://") or base.startswith("https://"):
        return base
    raise Usage(f"--base must start with http:// or https://, got {raw!r}")


def fetch(base: str, path: str, timeout: float) -> tuple[int, str, bytes]:
    """One GET, bounded. Returns (status, content-type, body).

    A 4xx is a response, not an exception: the caller decides what to do with it, and no
    route's refusal is swallowed here. Only the absence of an answer raises.
    """
    url = base + path
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.headers.get("content-type", ""), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("content-type", "") if exc.headers else "", exc.read()
    except urllib.error.URLError as exc:
        raise Unreachable(str(exc.reason)) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise Unreachable(f"no answer within {timeout:g}s") from exc
    except (ConnectionError, OSError) as exc:
        raise Unreachable(str(exc)) from exc


def fetch_json(base: str, path: str, timeout: float) -> tuple[int, dict]:
    status, content_type, body = fetch(base, path, timeout)
    text = body.decode("utf-8", "replace")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # An HTML page where JSON was expected is a server that answered with something
        # else. Say so with the bytes it sent rather than pretending the route is empty.
        return status, {"message": f"expected JSON, the route sent {content_type or 'no content type'}", "code": "not_json", "body": text[:400]}
    if not isinstance(payload, dict):
        return status, {"message": "expected a JSON object", "code": "not_json", "body": str(payload)[:400]}
    return status, payload


def start_hint(base: str) -> str:
    return (
        f"start it with: python3 -m ticketpath.server    (from {REPO_ROOT}; "
        f"it binds 127.0.0.1:8788 by default, and this CLI is pointed at {base})"
    )


# -- HTML to text, the way a browser shows it ------------------------------


SKIP_TAGS = frozenset({"style", "script", "noscript", "template", "head"})
BLOCK_TAGS = frozenset(
    {
        "p", "div", "section", "main", "header", "footer", "article", "aside", "nav",
        "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table", "thead", "tbody",
        "tr", "form", "fieldset", "dl", "dt", "dd", "pre", "blockquote", "figure",
        "figcaption", "hr", "br", "option",
    }
)


class _Text(HTMLParser):
    """Collect the text a browser would put on the page, block boundaries kept.

    `convert_charrefs=True` (the default) resolves entities, so a sentence carrying an
    apostrophe is the sentence it was written from. Style and script bodies are dropped:
    a browser shows neither, and CSS in the middle of a price is a lie about the page.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0

    def _line_has_text(self) -> bool:
        return bool("".join(self.out).rsplit("\n", 1)[-1].strip())

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in SKIP_TAGS:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "li":
            self.out.append("\n")
            self.out.append("- ")
        elif tag in ("td", "th"):
            # A cell separator between cells, never in front of the first one: a leading
            # `| ` is not what a browser shows at the start of a table row.
            if self._line_has_text():
                self.out.append(" | ")
        elif tag in BLOCK_TAGS:
            self.out.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in BLOCK_TAGS:
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.out.append(data)


def html_to_lines(markup: str) -> list[str]:
    """Plain text, one visible line per line, whitespace collapsed, no empty lines."""
    parser = _Text()
    parser.feed(markup)
    parser.close()
    lines = [" ".join(raw.split()) for raw in "".join(parser.out).splitlines()]
    return [line for line in lines if line]


def badge_lines(lines: list[str], badge: str) -> list[str]:
    """Prefix a source badge to any page line that carries no badge of its own.

    A page line that already shows a badge keeps exactly the one the server gave it:
    doubling `[FIXTURE] [EXACT] 1.25 SOL` would put a badge on a number that did not earn
    it. A line with no badge -- a heading, a mode label, a refusal's prose -- gets the
    badge of the source it was rendered from.
    """
    out = []
    for line in lines:
        out.append(line if BADGE_TOKEN.search(line) else f"{badge} {line}")
    return out


# -- printing --------------------------------------------------------------


def emit(lines, as_json: bool = False, payload=None, out=None) -> None:
    stream = out or sys.stdout
    if as_json:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        return
    for line in lines:
        stream.write(line + "\n")


def refusal_lines(status: int, payload: dict) -> list[str]:
    """The API's refusal, in its own words, with its typed code and its status."""
    message = str(payload.get("message") or "the route refused the request")
    code = payload.get("code") or "refused"
    return [f"[REFUSED] {status} {message} (code {code})"]


def int_text(value) -> str:
    return f"{value:,}" if isinstance(value, int) else str(value)


# -- verbs -----------------------------------------------------------------


def cmd_health(args) -> int:
    status, payload = fetch_json(args.base, "/health", args.timeout)
    badge = badge_for(payload)
    if status >= 400:
        emit(refusal_lines(status, payload))
        return EXIT_FAIL
    source = payload.get("dataSource") or {}
    chain = payload.get("chain") or {}
    model = payload.get("pricingModel") or {}
    contract = payload.get("contract") or {}
    chain_badge = "[DEVNET]" if chain.get("programDeployed") else "[DESIGN]"
    lines = [
        f"{badge} {payload.get('service')} {payload.get('version')} - {payload.get('status')} - now {payload.get('now')}",
        f"{badge} data source {source.get('mode')} - synthetic: {str(source.get('synthetic')).lower()}",
    ]
    label = provenance_line(payload)
    if label:
        lines.append(label)
    lines.append(
        f"{chain_badge} chain {chain.get('cluster')} - program deployed: "
        f"{str(chain.get('programDeployed')).lower()} - rpc enabled: "
        f"{str(chain.get('rpcEnabled')).lower()} - reason {chain.get('reason')}"
    )
    lines.append(
        f"{chain_badge} pricing seam {model.get('kind')} - fitted: "
        f"{str(model.get('fitted')).lower()} - available: {str(model.get('available')).lower()}"
    )
    lines.append(
        f"[EXACT] contract {contract.get('endpointsImplemented')} of "
        f"{contract.get('endpointsInContract')} endpoints - "
        f"{contract.get('routesImplemented')} routes - map {contract.get('map')}"
    )
    emit(lines, args.json, {"status": status, "badge": badge, "health": payload})
    return EXIT_OK


def event_lines(item: dict, badge: str, detail: bool) -> list[str]:
    cap = item.get("resalePriceCapBps")
    cap_text = "no cap" if cap is None else f"cap {cap} bps"
    tiers = item.get("tiers") or []
    lines = [
        f"{badge} {item.get('id')} {item.get('name')} - {item.get('status')} - "
        f"starts {item.get('startsAt')} - ends {item.get('endsAt')} - {len(tiers)} "
        f"{'tier' if len(tiers) == 1 else 'tiers'} - {cap_text} - issued "
        f"{int_text(item.get('issuedCount'))}/"
        f"{int_text(item.get('totalSupply'))}"
    ]
    if not detail:
        return lines
    organizer = item.get("organizer") or {}
    lines.append(
        f"{badge} venue {item.get('venue')}, {item.get('city')} - organizer "
        f"{organizer.get('id')} ({'verified' if organizer.get('verified') else 'unverified'}) - "
        f"resale enabled: {str(item.get('resaleEnabled')).lower()}"
    )
    for tier in tiers:
        lines.append(
            f"{badge} tier {tier.get('id')} {tier.get('name')} - face "
            f"{int_text(tier.get('faceValueLamports'))} lamports - issued "
            f"{int_text(tier.get('issuedCount'))} of {int_text(tier.get('totalSupply'))}"
        )
    lines.append(
        f"[DECLARED] wallet verification required: "
        f"{str(item.get('requiresVerifiedWallet')).lower()} - transfer restricted: "
        f"{str(item.get('transferRestricted')).lower() if item.get('transferRestricted') is not None else 'not reported'}"
    )
    if item.get("description"):
        lines.append(f"{badge} description: {item['description']}")
    return lines


def cmd_events(args) -> int:
    query = {"limit": str(args.limit)} if args.limit else {}
    if args.cursor:
        query["cursor"] = args.cursor
    path = "/api/events" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    status, payload = fetch_json(args.base, path, args.timeout)
    if status >= 400:
        emit(refusal_lines(status, payload))
        return EXIT_FAIL
    badge = badge_for(payload)
    items = payload.get("items") or []
    lines = [f"{badge} {len(items)} events on this page"]
    for item in items:
        lines.extend(event_lines(item, badge, detail=False))
    if payload.get("nextCursor"):
        lines.append(
            f"{badge} more events follow: --cursor {payload['nextCursor']}"
        )
    emit(lines, args.json, {"status": status, "badge": badge, "events": payload})
    return EXIT_OK


def cmd_event(args) -> int:
    path = "/api/events/" + urllib.parse.quote(args.event_id, safe="")
    status, payload = fetch_json(args.base, path, args.timeout)
    if status >= 400:
        emit(refusal_lines(status, payload), args.json, {"status": status, "event": payload})
        return EXIT_FAIL
    badge = badge_for(payload)
    lines = event_lines(payload, badge, detail=True)
    label = provenance_line(payload)
    if label:
        lines.append(label)
    emit(lines, args.json, {"status": status, "badge": badge, "event": payload})
    return EXIT_OK


def cmd_tickets(args) -> int:
    query = {"limit": str(args.limit)} if args.limit else {}
    if args.cursor:
        query["cursor"] = args.cursor
    if args.event:
        # The route's own parameter name is `eventId`; sending `event` here would be a flag
        # that quietly does nothing, which is worse than a flag that is absent.
        query["eventId"] = args.event
    path = "/api/tickets" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    status, payload = fetch_json(args.base, path, args.timeout)
    if status >= 400:
        emit(refusal_lines(status, payload))
        return EXIT_FAIL
    badge = badge_for(payload)
    items = payload.get("items") or []
    lines = [f"{badge} {len(items)} tickets on this page"]
    for item in items:
        last = item.get("lastSalePriceLamports")
        last_text = "no sale recorded" if last is None else (
            f"last sale {int_text(last)} lamports"
        )
        lines.append(
            f"{badge} {item.get('id')} {item.get('eventId')}/{item.get('tierId')} - "
            f"serial {item.get('serial')} - {item.get('status')} - face "
            f"{int_text(item.get('faceValueLamports'))} lamports - {last_text} - "
            f"{int_text(item.get('transferCount'))} "
            f"{'transfer' if item.get('transferCount') == 1 else 'transfers'}"
        )
    if payload.get("nextCursor"):
        lines.append(f"{badge} more tickets follow: --cursor {payload['nextCursor']}")
    emit(lines, args.json, {"status": status, "badge": badge, "tickets": payload})
    return EXIT_OK


def cmd_history(args) -> int:
    ticket = urllib.parse.quote(args.ticket_id, safe="")
    status, payload = fetch_json(args.base, f"/api/tickets/{ticket}/resale-history", args.timeout)
    if status >= 400:
        emit(refusal_lines(status, payload), args.json, {"status": status, "history": payload})
        return EXIT_FAIL
    badge = badge_for(payload)
    lines = [
        f"{badge} {payload.get('ticketId')} - face "
        f"{int_text(payload.get('faceValueLamports'))} lamports"
    ]
    for entry in payload.get("entries") or []:
        price = entry.get("priceLamports")
        price_text = "no price recorded" if price is None else f"{int_text(price)} lamports"
        markup = entry.get("markupBps")
        markup_text = "" if markup is None else f" - markup {int_text(markup)} bps"
        lines.append(
            f"{badge} {entry.get('id')} {entry.get('kind')} {entry.get('occurredAt')} - "
            f"{price_text}{markup_text}"
        )
    stats = payload.get("stats") or {}
    lines.append(
        f"{badge} {int_text(stats.get('saleCount'))} sales, "
        f"{int_text(stats.get('transferCount'))} transfers, avg markup "
        f"{int_text(stats.get('avgMarkupBps'))} bps, peak "
        f"{int_text(stats.get('peakPriceLamports'))} lamports, last "
        f"{int_text(stats.get('lastPriceLamports'))} lamports, volume "
        f"{int_text(stats.get('totalVolumeLamports'))} lamports, "
        f"{int_text(stats.get('uniqueWallets'))} wallets"
    )
    if payload.get("custodyNote"):
        lines.append(f"[DECLARED] {payload['custodyNote']}")
    label = provenance_line(payload)
    if label:
        lines.append(label)
    emit(lines, args.json, {"status": status, "badge": badge, "history": payload})
    return EXIT_OK


def price_path(args) -> str:
    """The console route's own query grammar. Discovered from ticketpath/server.py.

    There is no JSON guidance route in this tree: `GET /` *is* the guidance surface over
    HTTP, every control is a query parameter, and the payload is marshalled by
    `ticketpath/api/guidance.py` inside the server. So this builds the URL the page
    documents and the page's own text is the answer.
    """
    params: list[tuple[str, str]] = [("event", args.event_id)]
    if args.tier:
        params.append(("tier", args.tier))
    if args.cap is not None:
        params.append(("capBps", str(args.cap)))
    if args.at:
        params.append(("asOf", args.at))
    if args.mode:
        params.append(("mode", args.mode))
    return "/?" + urllib.parse.urlencode(params)


def page_payload(url: str, status: int, badge: str, lines: list[str], kind: str) -> dict:
    return {
        "command": kind,
        "url": url,
        "status": status,
        "badge": badge,
        "lines": lines,
        # There is no JSON guidance route to forward; the page text is the payload this
        # tree serves, so it is what --json carries rather than a reconstruction of it.
        "note": "page text as a browser shows it; the guidance payload itself is served only as this page",
    }


def render_page(base: str, path: str, timeout: float, kind: str, args) -> int:
    status, content_type, body = fetch(base, path, timeout)
    text = body.decode("utf-8", "replace")
    if "html" not in (content_type or "").lower():
        # A JSON route answered where a page was expected. Print its refusal in full.
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"message": text[:400] or "empty body", "code": "not_json"}
        if not isinstance(payload, dict):
            payload = {"message": str(payload)[:400], "code": "not_json"}
        lines = refusal_lines(status, payload)
        emit(lines, args.json, {"url": base + path, "status": status, "body": payload}, args.out)
        return EXIT_FAIL
    lines = html_to_lines(text)
    badge = "[FIXTURE]"
    status_probe, health = fetch_json(base, "/health", timeout)
    if status_probe < 400:
        badge = badge_for(health)
    lines = badge_lines(lines, badge)
    header = [f"{badge} {kind} {base}{path} - {status} - {len(lines)} lines"]
    emit(header + lines, args.json, page_payload(base + path, status, badge, lines, kind), args.out)
    return EXIT_OK if status < 400 else EXIT_FAIL


def cmd_price(args) -> int:
    return render_page(args.base, price_path(args), args.timeout, "price", args)


def cmd_page(args) -> int:
    path = args.path
    if not path.startswith("/"):
        path = "/" + path
    return render_page(args.base, path, args.timeout, "page", args)


# -- sweep -----------------------------------------------------------------


def audit_sweep() -> Path | None:
    """The independent sweep named by $TP_SWEEP, or None when the variable is unset."""
    value = os.environ.get(AUDIT_SWEEP_ENV, "").strip()
    return Path(value).expanduser() if value else None


def sweep_tool(root: Path = REPO_ROOT, audit: Path | None = None) -> Path | None:
    """The independent sweep if it is on the box, else the project's own checker."""
    if audit is None:
        audit = audit_sweep()
    for candidate in (audit, root / "tools" / "console-check.py"):
        if candidate is not None and candidate.is_file():
            return candidate
    return None


def sweep_command(tool: Path, base: str) -> list[str]:
    """The independent sweep takes the base as its argument; the project's reads TP_BASE."""
    if tool.name == "sweep.py":
        return [sys.executable, str(tool), base]
    return [sys.executable, str(tool)]


def cmd_sweep(args) -> int:
    status, health = fetch_json(args.base, "/health", args.timeout)
    if status >= 400:
        emit(refusal_lines(status, health))
        return EXIT_FAIL
    badge = badge_for(health)
    independent = audit_sweep()
    tool = sweep_tool(audit=independent)
    if tool is None:
        emit([f"{badge} no sweep tool: ${AUDIT_SWEEP_ENV} is unset or names a missing "
              "file, and tools/console-check.py is missing"])
        return EXIT_FAIL
    environment = dict(os.environ)
    environment["TP_BASE"] = args.base
    command = sweep_command(tool, args.base)
    if not args.json:
        lines = [f"{badge} sweep against {args.base} using {tool}"]
        if independent is None:
            lines.append(
                f"{badge} ${AUDIT_SWEEP_ENV} is unset: the optional independent sweep was "
                "skipped, and this is the project's own checker"
            )
        elif tool != independent:
            lines.append(
                f"{badge} ${AUDIT_SWEEP_ENV} names {independent}, which is not on the box: "
                "the optional sweep was skipped, and this is the project's own checker"
            )
        emit(lines)
    try:
        run = subprocess.run(
            command, cwd=str(REPO_ROOT), env=environment, capture_output=True, text=True,
            timeout=max(args.timeout * 12, 120.0),
        )
    except subprocess.TimeoutExpired:
        emit([f"{badge} sweep did not finish inside its bound; it was killed"])
        return EXIT_FAIL
    output = (run.stdout or "") + (run.stderr or "")
    if not args.json:
        # Verbatim: the sweep's findings are its own report, and re-wording them here would
        # be a second opinion dressed as the first one. With --json they travel inside the
        # document instead of ahead of it, so the output stays parseable.
        for line in output.splitlines():
            sys.stdout.write(line + "\n")
    # tools/console-check.py ends with `FAILURES: N`; the independent sweep says
    # `violations: N`. Either is the failure count; neither is invented if absent.
    found = re.search(r"FAILURES:\s*(\d+)|violations:\s*(\d+)", output)
    count = (found.group(1) or found.group(2)) if found else "unknown"
    verdict = "ok" if run.returncode == 0 else "FAILED"
    emit([f"{badge} sweep {verdict} - exit {run.returncode} - FAILURES: {count}"],
         args.json, {"tool": str(tool), "base": args.base, "badge": badge,
                     "exit": run.returncode, "failures": count,
                     "output": output.splitlines()})
    return EXIT_OK if run.returncode == 0 else EXIT_FAIL


# -- the gate --------------------------------------------------------------


def pick_free_port(avoid=RESERVED_PORTS) -> int:
    """A port nothing is listening on, never one of the machine's named ports."""
    for _ in range(64):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        if port not in avoid and port > 1024:
            return port
    raise RuntimeError("no free port found outside the reserved ports")


def _tail(path: Path, lines: int = 30) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return text.splitlines()[-lines:]


def _run(command, cwd: Path, env: dict, timeout: float) -> tuple[int, str]:
    """A bounded child. A timeout is a failure with a sentence, not an exception."""
    try:
        completed = subprocess.run(
            command, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout
        )
        return completed.returncode, (completed.stdout or "") + (completed.stderr or "")
    except subprocess.TimeoutExpired as exc:
        partial = ""
        if exc.stdout:
            partial += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", "replace")
        if exc.stderr:
            partial += exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", "replace")
        return 124, partial + f"\n[gate] the command exceeded its {timeout:g}s bound and was killed\n"


ACCESS_LOG = re.compile(r'^\d+\.\d+\.\d+\.\d+ "')

def failure_tail(output: str, lines: int = 40) -> list[str]:
    """The part of a failing run worth reading: no access log, no dot progress bar."""
    kept = [
        line for line in output.splitlines()
        if not ACCESS_LOG.match(line) and not re.fullmatch(r"[.sFEW]*", line.strip())
    ]
    return kept[-lines:]


def parse_tests(output: str) -> tuple[int | None, bool, str]:
    """`Ran 471 tests` plus the verdict unittest printed under it."""
    ran = re.search(r"^Ran (\d+) tests? in ", output, re.MULTILINE)
    count = int(ran.group(1)) if ran else None
    if re.search(r"^OK", output, re.MULTILINE):
        return count, True, "OK"
    failed = re.search(r"^FAILED \((.*)\)", output, re.MULTILINE)
    if failed:
        return count, False, f"FAILED ({failed.group(1)})"
    return count, False, "no verdict"


def parse_console_failures(output: str) -> int | None:
    """The `FAILURES: N` line tools/console-check.py prints before it exits."""
    match = re.search(r"FAILURES:\s*(\d+)", output)
    return int(match.group(1)) if match else None


def run_gate(
    *,
    quick: bool = False,
    tests_command: list[str] | None = None,
    console_command: list[str] | None = None,
    health_timeout: float = 20.0,
    tests_timeout: float = 150.0,
    console_timeout: float = 60.0,
    out=None,
) -> int:
    """Tests, then the console checks, against an ephemeral server this function owns.

    The server is killed on every exit path: pass, fail, timeout, exception. That is the
    property the commit hook depends on, because a hook that leaves a server bound to a
    port is a hook that breaks the next run.

    `--quick` runs the unit tests alone, under a tighter bound, and starts no server: a
    pre-commit hook may not wait on a page render, and the unit tests bind their own
    ephemeral servers already.
    """
    stream = out or sys.stdout
    started = time.monotonic()

    def say(line: str) -> None:
        stream.write(line + "\n")
        stream.flush()

    tests = tests_command or [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    # The suite runs against the documented default: `test_boundaries` pins
    # `resolve_port()` to 8788, which is only true when TICKETPATH_PORT is unset. The
    # gate therefore takes that variable out of the child's environment instead of
    # inheriting whatever this shell happens to export, and hands its own server its port
    # with the explicit flag, which wins over the environment anyway.
    environment = {key: value for key, value in os.environ.items() if key != "TICKETPATH_PORT"}
    position = {"tests": None, "tests_ok": False, "console": None, "badge": "[EXACT]"}

    def summary(verdict: str) -> str:
        tests_text = "tests not run" if position["tests"] is None else (
            f"tests={position['tests']} {'OK' if position['tests_ok'] else 'FAILED'}"
        )
        if position["console"] is None:
            console_text = "console-check skipped" if quick else "console-check not run"
        else:
            console_text = f"console-check FAILURES: {position['console']}"
        wall = time.monotonic() - started
        return f"{position['badge']} gate {verdict} - {tests_text} - {console_text} - wall={wall:.1f}s"

    server = None
    log_path = None
    try:
        if not quick:
            port = pick_free_port()
            base = f"http://127.0.0.1:{port}"
            handle = tempfile.NamedTemporaryFile(
                prefix="tp-gate-", suffix=".log", delete=False
            )
            log_path = Path(handle.name)
            server = subprocess.Popen(
                [sys.executable, "-m", "ticketpath.server", "--port", str(port)],
                cwd=str(REPO_ROOT), env=environment, stdout=handle, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            handle.close()
            deadline = time.monotonic() + health_timeout
            ready = False
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    break
                try:
                    with urllib.request.urlopen(base + "/health", timeout=2) as response:
                        if response.status == 200:
                            ready = True
                            break
                except Exception:  # noqa: BLE001 - not up yet is the expected state
                    time.sleep(0.1)
            if not ready:
                say(f"[EXACT] gate FAILED - the ephemeral server on {base} did not answer /health")
                for line in _tail(log_path):
                    say(f"  {line}")
                say(summary("FAILED"))
                return EXIT_UNREACHABLE
            say(f"[EXACT] gate server {base} (working tree, {REPO_ROOT})")
            source = fetch_json(base, "/health", 5)[1]
            position["badge"] = badge_for(source)
            say(provenance_line(source) or f"{position['badge']} data source declared by the server")

        # A pre-commit hook may not hold a terminal for a minute and a half; the quick
        # gate is bounded so that a hung test is a refused commit, not a stuck shell.
        budget = min(tests_timeout, 55.0) if quick else tests_timeout
        code, output = _run(tests, REPO_ROOT, environment, budget)
        position["tests"], position["tests_ok"], detail = parse_tests(output)
        if position["tests"] is None:
            position["tests_ok"] = False
        say(f"{position['badge']} unittest: {detail}"
            + ("" if position["tests"] is None else f" - {position['tests']} tests"))
        if code != 0 or not position["tests_ok"]:
            for line in failure_tail(output):
                say(f"  {line}")
            say(summary("FAILED"))
            return EXIT_FAIL

        if quick:
            say(summary("ok"))
            return EXIT_OK

        console = console_command or [sys.executable, str(REPO_ROOT / "tools" / "console-check.py")]
        environment["TP_BASE"] = base
        code, output = _run(console, REPO_ROOT, environment, console_timeout)
        position["console"] = parse_console_failures(output)
        if position["console"] is None:
            position["console"] = 0 if code == 0 else 1
        failures = output.splitlines()
        ok_lines = sum(1 for line in failures if line.startswith("ok  "))
        fail_lines = sum(1 for line in failures if line.startswith("FAIL "))
        say(f"{position['badge']} console-check: {ok_lines} ok, {fail_lines} failed, "
            f"FAILURES: {position['console']}")
        if code != 0 or position["console"]:
            for line in failures[-40:]:
                say(f"  {line}")
            say(summary("FAILED"))
            return EXIT_FAIL
        say(summary("ok"))
        return EXIT_OK
    finally:
        if server is not None:
            if server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)
            # A killed server that left a child behind would keep the port. Nothing in
            # ticketpath.server forks, so the check is about the port, not a process tree.
        if log_path is not None:
            try:
                log_path.unlink()
            except OSError:
                pass


def cmd_gate(args) -> int:
    return run_gate(quick=args.quick)


# -- argument parsing ------------------------------------------------------


def _common(parser: argparse.ArgumentParser, *, suppress: bool) -> None:
    """Global flags, accepted before or after the verb.

    The sub-parser copies suppress their defaults so a flag written before the verb is
    not overwritten by a sub-parser default when it is absent after the verb.
    """
    default = argparse.SUPPRESS if suppress else DEFAULT_BASE
    parser.add_argument("--base", default=default, metavar="URL",
                        help=f"server base URL (default {DEFAULT_BASE})")
    parser.add_argument("--json", action="store_true",
                        default=argparse.SUPPRESS if suppress else False,
                        help="machine-readable output instead of one line per fact")
    timeout_default = argparse.SUPPRESS if suppress else DEFAULT_TIMEOUT
    parser.add_argument("--timeout", type=float, default=timeout_default, metavar="SECONDS",
                        help=f"per-request timeout (default {DEFAULT_TIMEOUT:g}s)")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    _common(common, suppress=True)

    parser = argparse.ArgumentParser(
        prog="tools/tp.py",
        description="The Ticketpath backend from a terminal: every route as a verb, plus the commit gate.",
        epilog=(
            "exit codes: 0 ok, 1 a check failed or the route refused, 2 usage, "
            "3 the server did not answer"
        ),
    )
    _common(parser, suppress=False)
    verbs = parser.add_subparsers(dest="command", required=True, metavar="VERB")

    verbs.add_parser("health", parents=[common], help="GET /health: liveness, source, honesty")
    events = verbs.add_parser("events", parents=[common], help="GET /api/events")
    events.add_argument("--limit", type=int, default=None)
    events.add_argument("--cursor", default=None)
    event = verbs.add_parser("event", parents=[common], help="GET /api/events/<id>")
    event.add_argument("event_id")
    tickets = verbs.add_parser("tickets", parents=[common], help="GET /api/tickets")
    tickets.add_argument("--limit", type=int, default=None)
    tickets.add_argument("--cursor", default=None)
    tickets.add_argument("--event", default=None, help="only tickets for this event id")
    history = verbs.add_parser("history", parents=[common], help="GET /api/tickets/<id>/resale-history")
    history.add_argument("ticket_id")
    price = verbs.add_parser(
        "price", parents=[common],
        help="the console/guidance route for one event, printed as text",
    )
    price.add_argument("event_id")
    price.add_argument("--tier", default=None)
    price.add_argument("--cap", default=None, metavar="BPS")
    price.add_argument("--mode", default=None, choices=("counterfactual", "before_on_sale"))
    price.add_argument("--at", default=None, metavar="ISO")
    page = verbs.add_parser("page", parents=[common], help="fetch an HTML page and print it as text")
    page.add_argument("path")
    verbs.add_parser("sweep", parents=[common], help="run the four property checks against the server")
    gate = verbs.add_parser("gate", parents=[common], help="the commit gate: tests plus console checks")
    gate.add_argument("--quick", action="store_true", help="unit tests only, under 60s, no server")
    return parser


COMMANDS = {
    "health": cmd_health,
    "events": cmd_events,
    "event": cmd_event,
    "tickets": cmd_tickets,
    "history": cmd_history,
    "price": cmd_price,
    "page": cmd_page,
    "sweep": cmd_sweep,
    "gate": cmd_gate,
}


def main(argv: list[str] | None = None, out=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse's own usage error, already printed
        return int(exc.code) if isinstance(exc.code, int) else EXIT_USAGE
    args.out = out
    try:
        args.base = normalise_base(args.base)
        return COMMANDS[args.command](args)
    except Usage as exc:
        sys.stderr.write(f"tp.py: {exc}\n")
        return EXIT_USAGE
    except Unreachable as exc:
        sys.stderr.write(f"tp.py: no server at {args.base}: {exc}\n")
        sys.stderr.write(f"tp.py: {start_hint(args.base)}\n")
        return EXIT_UNREACHABLE
    except BrokenPipeError:
        # `tp.py events | head` closed the pipe; that is not an error worth a traceback.
        try:
            sys.stdout.close()
        except OSError:
            pass
        return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
