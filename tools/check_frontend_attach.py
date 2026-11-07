#!/usr/bin/env python3
"""Check that a served frontend is attached to the backend, and can actually fail.

Point it at a base URL and it reads the pages the way a judge's browser would read them,
over plain GET, and asserts the things that are true only when the frontend is talking to
the synthetic backend:

  * no mock banner, and the backend's own data-source label on every page that prints
    numbers;
  * the false enforcement claims are gone;
  * /pricing carries the console's [UNVALIDATED] and [FIXTURE] badges and the mode
    sentence, and states no price of its own;
  * the proxied console computes, refuses, and keeps every badge;
  * the figures on three pages are the API's figures at the precision shown.

The last requirement is the one that matters: a check that cannot fail is not a check.
`--base http://127.0.0.1:3000` points it at the unattached original, where it must fail.

Standard library only, GET only, no browser. Nothing here writes to either tree.

    python3 tools/check_frontend_attach.py                       # the copy on :3001
    python3 tools/check_frontend_attach.py --base http://127.0.0.1:3000   # must fail
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from decimal import Decimal

TIMEOUT_SECONDS = 15.0

# Strings that are only false when the app is reading fixtures. They are quoted from the
# original tree, and each one is a claim about enforcement or custody that no build of
# this code can keep: nothing is on a chain, and nothing is enforced at transfer time.
FALSE_CLAIMS = (
    "Mock data",
    "enforced at transfer time",
    "before a transfer will succeed",
    "Enforced on-chain",
    "Every transfer is recorded on-chain",
)

# StatTile renders <p class="text-xs text-ink-2">LABEL</p> then the figure in a
# tracking-tight paragraph. dt/dd pairs in the detail card render as siblings.
TILE_LABEL = '<p class="text-xs text-ink-2">{label}</p>'
TILE_VALUE = re.compile(r'tracking-tight">([^<]{1,60})</p>')
DETAIL_PAIR = '<dt class="text-ink-2">{term}</dt>'
DETAIL_VALUE = re.compile(r'<dd class="[^"]{0,40}">([^<]{1,60})</dd>')
SHORT_ADDRESS = re.compile(r">([1-9A-Za-z]{4}\u2026[1-9A-Za-z]{4})<")
FULL_ADDRESS = re.compile(r'title="([1-9A-Za-z]{32,44})"')


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str
    fix: str = ""


class Backend:
    """The API the frontend is supposed to be reading, read directly for comparison."""

    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        status, body = self.fetch("/api/events?limit=100")
        if status != 200:
            raise SystemExit(
                f"FAIL  backend {self.base}/api/events -> {status}\n"
                "      start it first: python3 -m ticketpath.server --port 8788"
            )
        page = json.loads(body)
        self.events: list[dict] = page["items"]
        self.label: str = page["dataSource"]["label"]
        self.tickets: list[dict] = json.loads(self.fetch("/api/tickets?limit=100")[1])["items"]

    def fetch(self, path: str) -> tuple[int, str]:
        return http_get(self.base + path)

    def analytics(self, event_id: str) -> dict:
        return json.loads(self.fetch(f"/api/events/{event_id}/analytics")[1])

    def resale_history(self, ticket_id: str) -> dict:
        return json.loads(self.fetch(f"/api/tickets/{ticket_id}/resale-history")[1])


def http_get(url: str) -> tuple[int, str]:
    """GET a URL and return (status, text). A dead server is a result, not a crash."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, response.read().decode(charset, "replace")
    except urllib.error.HTTPError as error:
        charset = error.headers.get_content_charset() if error.headers else "utf-8"
        return error.code, error.read().decode(charset or "utf-8", "replace")
    except Exception as error:  # noqa: BLE001 - unreachable is a finding, not a traceback
        return 0, f"<no response: {error}>"


def tile(page: str, label: str) -> str | None:
    """The figure under a StatTile label, or None if the label is not on the page."""
    marker = TILE_LABEL.format(label=label)
    at = page.find(marker)
    if at < 0:
        return None
    found = TILE_VALUE.search(page, at)
    return found.group(1).strip() if found else None


def detail(page: str, term: str) -> str | None:
    """The value paired with a <dt> term in the detail card, or None."""
    marker = DETAIL_PAIR.format(term=term)
    at = page.find(marker)
    if at < 0:
        return None
    found = DETAIL_VALUE.match(page, at + len(marker))
    return found.group(1).strip() if found else None


def displayed_number(text: str) -> tuple[Decimal, int]:
    """Parse a rendered figure: "14", "+5.8%", "33.22 SOL", "1 SOL"."""
    raw = text.strip()
    negative = raw.startswith("-")
    raw = raw.lstrip("+-").strip()
    for suffix in ("%", "SOL"):
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)].strip()
    raw = raw.replace(",", "")
    decimals = len(raw.split(".")[1]) if "." in raw else 0
    value = Decimal(raw)
    return (-value if negative else value), decimals


def reads_as(text: str | None, actual: float) -> bool:
    """True when `text` is `actual` at the precision it is shown to.

    A page that rounds 5.75 bps-free percent to "+5.8%" is right; one that shows "+5.7%"
    is not, and a tolerance tight enough to catch that is half a unit in the last digit.
    """
    if text is None:
        return False
    try:
        value, decimals = displayed_number(text)
    except Exception:  # noqa: BLE001 - "—", "" and "n/a" are all "no figure"
        return False
    tolerance = Decimal("0.5") * (Decimal(10) ** -decimals) + Decimal("1e-9")
    return abs(value - Decimal(repr(float(actual)))) <= tolerance


def parity(name: str, text: str | None, actual: float, source: str, fix: str) -> Check:
    ok = reads_as(text, actual)
    return Check(
        name=name,
        ok=ok,
        detail=f"{text!r} vs API {actual:.6g} ({source})",
        fix="" if ok else fix,
    )


def run(base: str, api_base: str) -> list[Check]:
    checks: list[Check] = []
    backend = Backend(api_base)

    scored = [(event, backend.analytics(event["id"])) for event in backend.events]
    rich_event, rich_stats = max(scored, key=lambda pair: pair[1]["saleCount"])
    thin_event, thin_stats = min(scored, key=lambda pair: pair[1]["saleCount"])

    ticket_id, ticket_history = "", {"entries": []}
    for candidate in backend.tickets:
        history = backend.resale_history(candidate["id"])
        if any(entry.get("priceLamports") is not None for entry in history["entries"]):
            ticket_id, ticket_history = candidate["id"], history
            break

    priced = [
        entry["priceLamports"]
        for entry in ticket_history["entries"]
        if entry.get("priceLamports") is not None
    ]

    checks.append(
        Check(
            "backend",
            True,
            f"{api_base} serves {len(backend.events)} events and {len(backend.tickets)} tickets; "
            f"parity event {rich_event['id']} ({rich_stats['saleCount']} resales), "
            f"refusing event {thin_event['id']} ({thin_stats['saleCount']} resales)",
        )
    )

    # -- the pages a judge reaches, fetched as the browser would ---------------------
    routes: tuple[tuple[str, str, bool], ...] = (
        ("home", "/", True),
        ("event page", f"/events/{rich_event['slug']}", True),
        ("ticket page", f"/tickets/{ticket_id}", True),
        ("organizer", f"/organizer?event={rich_event['id']}", True),
        ("pricing", "/pricing", False),
        ("pricing with event", f"/pricing?event={rich_event['id']}", False),
        ("my-tickets", "/my-tickets", False),
        ("verify", "/verify", False),
    )

    pages: dict[str, str] = {}
    for name, path, prints_numbers in routes:
        status, body = http_get(base + path)
        pages[name] = body
        checks.append(
            Check(
                f"route {name} ({path})",
                status == 200,
                f"{status}, {len(body)} bytes",
                ""
                if status == 200
                else (
                    f"the page must exist on {base}; 404 here means the copy being served "
                    "predates the pricing page, or the slug/ticket came from a backend this "
                    "frontend is not reading (is NEXT_PUBLIC_API_BASE_URL set and was the "
                    "server restarted?)"
                ),
            )
        )
        if status == 200 and prints_numbers:
            checks.append(
                Check(
                    f"backend label on {name}",
                    backend.label in body,
                    f"expects {backend.label[:36]!r}",
                    ""
                    if backend.label in body
                    else "the page is not printing the backend's own data-source label; "
                    "it is either reading lib/mock or dropping the dataSource block",
                )
            )

    found_claims = sorted(
        {claim for page in pages.values() for claim in FALSE_CLAIMS if claim in page}
    )
    checks.append(
        Check(
            "false enforcement claims absent",
            not found_claims,
            "none of the five are on any page"
            if not found_claims
            else f"still present: {found_claims}",
            "" if not found_claims else "apply docs/frontend-honesty.patch to the served tree",
        )
    )

    # -- /pricing: badges, the mode sentence, and no price of its own ----------------
    pricing = pages["pricing"]
    negotiated = pages["pricing with event"]
    checks.append(
        Check(
            "pricing frames the console",
            'src="/api/console' in pricing and f'src="/api/console?event={rich_event["id"]}' in negotiated,
            f'frame src "/api/console" and the event is forwarded into it',
            "" if 'src="/api/console' in pricing else "app/pricing/page.tsx is missing or not served",
        )
    )
    for badge in ("[UNVALIDATED]", "[FIXTURE]"):
        checks.append(
            Check(
                f"pricing states {badge}",
                badge in pricing,
                f"{pricing.count(badge)} on the page",
                "" if badge in pricing else "the preamble must name the badge it is relying on",
            )
        )
    mode_sentence = "Decision mode:"
    checks.append(
        Check(
            "pricing carries the mode sentence",
            mode_sentence in pricing,
            mode_sentence if mode_sentence in pricing else "missing",
            "" if mode_sentence in pricing else "the page must say which decision mode the frame is in",
        )
    )
    origin = urllib.parse.urlsplit(api_base).netloc
    checks.append(
        Check(
            "pricing names the backend origin",
            origin in pricing,
            f"expects {origin!r}",
            "" if origin in pricing else "the page must name where the numbers come from",
        )
    )
    checks.append(
        Check(
            "pricing states no price itself",
            "Recommended primary price" not in pricing,
            "the page links the console rather than restating its figure"
            if "Recommended primary price" not in pricing
            else "the page is restating the console's headline without its badge",
            "",
        )
    )

    # -- the proxy: it computes, it refuses, and it keeps every badge ---------------
    for name, event_id, wanted in (
        ("console computes", rich_event["id"], ("Recommended primary price",)),
        ("console refuses", thin_event["id"], ("[REFUSED]",)),
    ):
        status, body = http_get(f"{base}/api/console?event={event_id}")
        missing = [needle for needle in wanted if needle not in body]
        checks.append(
            Check(
                f"proxy {name} (event={event_id})",
                status == 200 and not missing,
                f"{status}, {body.count('[FIXTURE]')} [FIXTURE], "
                f"{body.count('[UNVALIDATED]')} [UNVALIDATED], {body.count('[REFUSED]')} [REFUSED]"
                + (f"; missing {missing}" if missing else ""),
                ""
                if status == 200 and not missing
                else "GET the proxy directly to see the labelled panel it returned",
            )
        )

    status, console = http_get(f"{base}/api/console?event={rich_event['id']}")
    checks.append(
        Check(
            "proxy keeps the badges",
            status == 200 and console.count("[FIXTURE]") >= 10 and "[UNVALIDATED]" in console,
            f"{console.count('[FIXTURE]')} [FIXTURE], {console.count('[UNVALIDATED]')} [UNVALIDATED]",
            "" if status == 200 else "the proxy is not answering",
        )
    )
    status, refused = http_get(f"{base}/api/console?bogusParameter=1")
    checks.append(
        Check(
            "proxy refuses an unknown parameter",
            status == 400,
            f"{status}",
            "" if status == 400 else "the proxy must not forward parameters the console ignores",
        )
    )

    # -- parity: the figure on the page is the API's figure ------------------------
    event_page = pages["event page"]
    organizer = pages["organizer"]
    ticket_page = pages["ticket page"]

    checks.append(
        parity(
            "parity event tickets issued",
            tile(event_page, "Tickets issued"),
            float(rich_event["issuedCount"]),
            "issuedCount",
            "the event page is not showing the API's issuedCount",
        )
    )
    checks.append(
        parity(
            "parity event average markup",
            tile(event_page, "Average markup"),
            rich_stats["avgMarkupBps"] / 100,
            "analytics.avgMarkupBps",
            "the event page is not showing the API's avgMarkupBps",
        )
    )
    checks.append(
        parity(
            "parity event resold share",
            tile(event_page, "Resold at least once"),
            rich_stats["resoldShare"] * 100,
            "analytics.resoldShare",
            "the event page is not showing the API's resoldShare",
        )
    )
    checks.append(
        parity(
            "parity organizer median",
            tile(organizer, "Median resale price"),
            rich_stats["medianResalePriceLamports"] / 1e9,
            "analytics.medianResalePriceLamports",
            "the organizer page is not showing the API's median resale price",
        )
    )
    checks.append(
        parity(
            "parity organizer volume",
            tile(organizer, "Total resale volume"),
            rich_stats["totalVolumeLamports"] / 1e9,
            "analytics.totalVolumeLamports",
            "the organizer page is not showing the API's total resale volume",
        )
    )
    if priced:
        checks.append(
            parity(
                "parity ticket volume",
                detail(ticket_page, "Total resale volume"),
                sum(priced) / 1e9,
                "sum of resale-history prices",
                "the ticket page is not showing the API's resale history",
            )
        )
        checks.append(
            parity(
                "parity ticket last sale",
                tile(ticket_page, "Last sale price"),
                priced[-1] / 1e9,
                "last priced resale",
                "the ticket page is not showing the API's last sale",
            )
        )

    # -- the truncation tell: two different wallets must not look the same ----------
    # The page carries the full address in each pill's title attribute, so the mapping
    # full -> short is checkable. Repeats of one wallet are fine; two wallets sharing a
    # short form are the bug, because then a reader cannot tell them apart.
    forms: dict[str, str] = {}
    for found in FULL_ADDRESS.finditer(ticket_page):
        short = SHORT_ADDRESS.search(ticket_page, found.end(), found.end() + 400)
        if short:
            forms.setdefault(found.group(1), short.group(1))
    collisions = sorted(
        short for short in set(forms.values()) if list(forms.values()).count(short) > 1
    )
    checks.append(
        Check(
            "addresses truncate distinctly",
            len(forms) >= 2 and not collisions,
            (
                f"{len(forms)} distinct wallets, {len(forms) - len(collisions)} distinct short forms"
                + (f"; {collisions[:3]} claimed by more than one wallet" if collisions else "")
                + f" (checked on {ticket_id})"
            )
            if forms
            else f"no address pill rendered on {ticket_id} (see the ticket page route above)",
            ""
            if len(forms) >= 2 and not collisions
            else (
                "the payload behind this page has two wallets sharing a short form, so the page "
                "cannot tell them apart; that is a property of the payload, not of the renderer"
                if forms
                else "nothing to compare until the ticket page renders"
            ),
        )
    )

    return checks


def report(checks: list[Check], base: str, api_base: str) -> int:
    failed = [check for check in checks if not check.ok]
    print(f"frontend attach check")
    print(f"  frontend  {base}")
    print(f"  backend   {api_base}")
    print("")
    for check in checks:
        mark = "PASS" if check.ok else "FAIL"
        print(f"{mark}  {check.name}: {check.detail}")
        if not check.ok and check.fix:
            print(f"      fix: {check.fix}")
    print("")
    if failed:
        print(f"{len(checks) - len(failed)} passed, {len(failed)} failed")
        for check in failed:
            print(f"  failed: {check.name}")
        return 1
    print(f"{len(checks)} passed, 0 failed")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Assert that a served frontend is attached to the synthetic backend.",
    )
    parser.add_argument("--base", default="http://127.0.0.1:3001", help="frontend base URL")
    parser.add_argument(
        "--api-base", default="http://127.0.0.1:8788", help="backend base URL to compare against"
    )
    args = parser.parse_args(argv)
    checks = run(args.base.rstrip("/"), args.api_base.rstrip("/"))
    return report(checks, args.base, args.api_base)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
