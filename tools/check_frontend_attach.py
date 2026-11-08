#!/usr/bin/env python3
"""Check that a served frontend is attached to the backend, and can actually fail.

Point it at a base URL and it reads the pages the way a judge's browser would read them,
over plain GET, and asserts the things that are true only when the frontend is talking to
the synthetic backend:

  * no mock banner, and the backend's own data-source label on every page that prints
    numbers;
  * the false enforcement claims are gone;
  * /pricing carries the console's badges, a gloss for every one of them including the
    page's own [UNAVAILABLE], and no promise the console refuses; it restates no decision
    mode, states a floor where the record supports only a floor, names the environment
    variable the proxy actually reads, and prints no price of its own;
  * the frame is sandboxed and sized from its content rather than a fixed height;
  * the proxied console computes, refuses, keeps every badge, rewrites the console's
    root-relative form action and link, serves a containment policy, and does not reorder
    a repeated key;
  * the figures on three pages are the API's figures at the precision shown.

The last requirement is the one that matters: a check that cannot fail is not a check.
`--base http://127.0.0.1:3000` points it at the unattached original, where it must fail.

A page that is not there cannot make a false claim, so every /pricing check below fails
when the route is not a 200. Without that gate an absence check passes on a 404 and reports
a defect as a success, which is how one of these checks used to pass on the control.

What this cannot see: nothing here renders. The frame's height against its content, and
whether a price is visible in the frame at 390px, are layout facts and need a browser. They
were measured with tools/shot.py at the time of the fix (the numbers are in the commit-free
report the fix was handed back with): 3383px of frame over 3382px of console at 1280, and
7143 over 7142 at 390, with no scrollbar inside the frame in either case.

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
from pathlib import Path

TIMEOUT_SECONDS = 15.0

# The backend's badge list, imported from the authority rather than copied here, so a badge
# added to `ticketpath/core/labels.py` that the page fails to gloss shows up as a failure.
# The literal is the same eight and exists only so this file still runs from a copy.
try:  # pragma: no cover - the import is the normal path when run from the repository
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ticketpath.core.labels import BADGES as BACKEND_BADGES
except Exception:  # noqa: BLE001 - a copy without the backend is still worth checking
    BACKEND_BADGES = (
        "FIXTURE",
        "DECLARED",
        "EXACT",
        "UNVALIDATED",
        "REFUSED",
        "DESIGN",
        "SIMULATED",
        "DEVNET",
    )

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


def http_get_full(url: str) -> tuple[int, dict[str, str], str]:
    """GET a URL and keep the response headers, for the assertions about the policy."""
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, headers, response.read().decode(charset, "replace")
    except urllib.error.HTTPError as error:
        charset = error.headers.get_content_charset() if error.headers else "utf-8"
        headers = {key.lower(): value for key, value in (error.headers or {}).items()}
        return error.code, headers, error.read().decode(charset or "utf-8", "replace")
    except Exception as error:  # noqa: BLE001 - an unreachable host is a result
        return 0, {}, f"<no response: {error}>"


SCRIPT_OR_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
ANY_TAG = re.compile(r"<[^>]+>")
ABSOLUTE_URL = re.compile(r"https?://[^\s\"'<>\\]+")
IFRAME_TAG = re.compile(r"<iframe\b[^>]*>", re.I)


def page_text(html: str) -> str:
    """The words a reader sees: script and style blocks and tags removed.

    Next inlines its RSC payload, and a dev build inlines the framework's own error payload,
    inside <script>. Scanning the raw bytes for a claim or a URL finds things no reader can
    see, which is how a page can be called wrong for something it never said.
    """
    return re.sub(r"\s+", " ", ANY_TAG.sub(" ", SCRIPT_OR_STYLE.sub(" ", html))).strip()


def origins_in(text: str) -> set[str]:
    """Every absolute scheme://host:port a reader could click, deduplicated."""
    found: set[str] = set()
    for match in ABSOLUTE_URL.finditer(text):
        parts = urllib.parse.urlsplit(match.group(0))
        if parts.netloc:
            found.add(f"{parts.scheme}://{parts.netloc}".lower())
    return found


CANONICAL_EVENT = re.compile(r"event=([A-Za-z0-9_]+)")


def proxied_event_id(html: str) -> str | None:
    """The event the console says it priced, read off its own canonical URL line.

    Two console pages cannot be compared byte for byte: the canonical line carries the
    decision instant to the millisecond and the [DESIGN] slot carries a quote id derived
    from it, so every request differs. The event id is the part a repeated key is about.
    """
    at = html.find("canonical URL for this decision")
    if at < 0:
        return None
    found = CANONICAL_EVENT.search(html, at)
    return found.group(1) if found else None


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

    # -- /pricing: every sentence on it, checked against what the console refuses -------
    # Each check below is gated on the route being a page. An absence check on a 404 passes
    # for the wrong reason: the original frontend has no /pricing, so "the page makes no false
    # promise" was true of a 404 and this checker reported a defect as a success.
    pricing = pages["pricing"]
    negotiated = pages["pricing with event"]
    pricing_status, _ = http_get(f"{base}/pricing")
    up = pricing_status == 200
    words = page_text(pricing)
    origin = urllib.parse.urlsplit(api_base).netloc

    def on_page(*phrases: str) -> tuple[bool, str]:
        """True when every phrase is on the page as a reader sees it."""
        missing = [phrase for phrase in phrases if phrase not in words]
        return (not missing, f"missing {missing}" if missing else "present")

    checks.append(
        Check(
            "pricing frames the console",
            up
            and 'src="/api/console' in pricing
            and f'src="/api/console?event={rich_event["id"]}' in negotiated,
            f'{pricing_status}, frame src "/api/console" and the event is forwarded into it',
            ""
            if up
            else (
                "/pricing is not served: 404 here means the copy being served predates the "
                "page, or the server is still reading lib/mock"
            ),
        )
    )

    # The page's promises, against the console's refusals. The console refuses a
    # price-specific sale probability (`[REFUSED] not_identified`) and an interior optimum
    # (`[REFUSED] no_demand_response`) on every state, so the page may not promise either.
    promises = (
        "maximises risk-adjusted expected value",
        "the chance it sells at a given price, and",
        "how that value moves over the time left",
    )
    admitted = (
        "does not estimate the chance a ticket sells at a given price",
        "boundary rather than an interior optimum",
    )
    claimed = [phrase for phrase in promises if phrase in words]
    owned = [phrase for phrase in admitted if phrase in words]
    checks.append(
        Check(
            "pricing promises no output the console refuses",
            up and not claimed and len(owned) == len(admitted),
            "none of the three promises, both refusals named"
            if up and not claimed and len(owned) == len(admitted)
            else f"still promised {claimed}; refusals named {len(owned)}/{len(admitted)}",
            "the opening sentence must state what the page shows, not the research aim: "
            "the console refuses sale probability and an interior optimum by name",
        )
    )

    # The decision-mode sentence is a function of the record, and the backend's copy changes
    # with it: `completed record ... in hindsight` is true of an event whose run has ended and
    # false of one that has not. A page cannot restate it, so it must not try.
    checks.append(
        Check(
            "pricing restates no decision mode",
            up and "hindsight" not in words and "completed resale record" not in words
            and "decision mode" in words,
            "no hindsight claim; points at the console's own decision panel"
            if up and "hindsight" not in words and "completed resale record" not in words
            else "the page is describing a mode the console chooses for itself",
            "drop the mode sentence and let the frame carry the backend's own, which is "
            "state-aware; the review's D2 quotes both sentences side by side",
        )
    )

    # A binding-cap event prints a floor and no upper bound, so a page that always promises a
    # band is wrong for the regime the checker's own parity event is in.
    band_claim = "the band around it is the part worth arguing with"
    checks.append(
        Check(
            "pricing states a floor where there is no band",
            up and band_claim not in words and "floor" in words,
            "the band is conditional and the floor is named"
            if up and band_claim not in words
            else "the page promises a band for every event",
            "say the band holds where the record supports one, and the floor otherwise",
        )
    )

    # The legend. Every badge the backend can print gets a gloss here, plus the one badge
    # this app writes itself, and no gloss may contradict the sentence beside the number.
    badges = tuple(f"[{name}]" for name in BACKEND_BADGES) + ("[UNAVAILABLE]",)
    missing_badges = [badge for badge in badges if badge not in words]
    checks.append(
        Check(
            "pricing glosses every badge",
            up and not missing_badges,
            f"{len(badges) - len(missing_badges)}/{len(badges)} glossed"
            + (f"; missing {missing_badges}" if missing_badges else ""),
            "the legend must cover the backend's badges (labels.py) and the page's own "
            "[UNAVAILABLE], which the proxy writes when the console does not answer",
        )
    )
    contradicted = "a parameter a person set, not estimated"
    checks.append(
        Check(
            "[DECLARED] gloss matches the console's use",
            up and contradicted not in words and "declared prior" in words,
            "says declaration or a declared prior, which is what the badge is on"
            if up and contradicted not in words and "declared prior" in words
            else "the gloss denies the estimate the console puts that badge on",
            "the console prints [DECLARED] over a posterior mean of a declared prior, so a "
            "gloss that says 'not estimated' contradicts it on the same screen",
        )
    )

    # Where the numbers come from. The page must name the variable the proxy reads, and the
    # only absolute address on it must be the backend's: a page that prints the fallback
    # variable's value while the proxy fetches CONSOLE_ORIGIN states a false origin.
    checks.append(
        Check(
            "pricing names the variable the proxy reads",
            up and "CONSOLE_ORIGIN" in words and "NEXT_PUBLIC_API_BASE_URL" in words,
            "names CONSOLE_ORIGIN and its NEXT_PUBLIC_API_BASE_URL fallback",
            "the page must name the variable that decides the origin, not only the origin",
        )
    )
    printed = origins_in(words)
    stale_mechanism = "built from its own host header"
    checks.append(
        Check(
            "pricing states the backend's origin and no other",
            up and printed == {api_base.rstrip("/").lower()},
            f"printed {sorted(printed)}, backend {api_base.rstrip('/')!r}",
            "the only absolute address on the page must be the origin the proxy fetches; "
            "anything else is a second, false account of where the numbers come from",
        )
    )
    checks.append(
        Check(
            "pricing describes the canonical URL correctly",
            up and stale_mechanism not in words and "bound to" in words,
            "says bound address" if up and stale_mechanism not in words else "still says host header",
            "server.py builds the canonical URL from self.server.server_address",
        )
    )

    # The one link to the backend. It must point at the origin the proxy fetches, and it may
    # only be rendered when there is something there to load.
    link = re.search(r'<a[^>]+href="(https?://[^"]+)"[^>]*>\s*open the same state', pricing)
    checks.append(
        Check(
            "pricing links the backend only where it answers",
            up and (link is None or urllib.parse.urlsplit(link.group(1)).netloc == origin),
            (f"links {link.group(1)}" if link else "no backend link offered")
            + f", backend {origin!r}",
            "a link to an address that does not answer is a dead link; render the address "
            "as text instead",
        )
    )

    checks.append(
        Check(
            "pricing states no price itself",
            up and "Recommended primary price" not in pricing,
            "the page frames the console rather than restating its figure"
            if up and "Recommended primary price" not in pricing
            else (
                f"{pricing_status}, page restates the console's headline"
                if "Recommended primary price" in pricing
                else f"{pricing_status}, the route is not served, so it is not framing anything"
            ),
            "",
        )
    )

    # -- the frame: sandboxed, and sized to the page it holds --------------------------
    frame_tag = IFRAME_TAG.search(pricing)
    tag = frame_tag.group(0) if frame_tag else ""
    checks.append(
        Check(
            "frame is sandboxed",
            up and 'sandbox="allow-forms' in tag,
            tag[:160] if tag else "no iframe on /pricing",
            "the console's document must not be able to script this page; the review's D9 "
            "measured a same-origin frame with no sandbox at all",
        )
    )
    fixed_height = re.search(r"h-\[(\d+)px\]", tag)
    checks.append(
        Check(
            "frame is sized from its content",
            up and bool(tag) and "data-console-frame" in tag and fixed_height is None,
            (
                "no fixed height; the frame measures the document it holds"
                if fixed_height is None
                else f"fixed height h-[{fixed_height.group(1)}px] hides the rest of the console"
            ),
            "a fixed height hid about half the console at 1280 and two thirds at 390, and "
            "drew a three-line refusal as a tall empty box",
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

    # The console owns the backend's site root, so its form action and its one link are
    # written as "/". Inside the proxy those resolve to this app's home page: the form would
    # throw the frame back to the event list and the error page's link would load the whole
    # app inside the frame. Both must arrive rewritten.
    status, error_page = http_get(f"{base}/api/console?event=nonexistent-event")
    checks.append(
        Check(
            "proxy rewrites the console's root-relative link",
            status in (404, 200)
            and 'href="/"' not in error_page
            and 'href="/api/console"' in error_page,
            f"{status}, the console's error page keeps its link inside the proxy"
            if 'href="/api/console"' in error_page
            else f"{status}, the console's error page still links the app root",
            "unrewritten, `back to the decision` loads this app inside the frame "
            "(the review's D5 measured exactly that)",
        )
    )
    checks.append(
        Check(
            "proxy rewrites the console's form action",
            'action="/api/console"' in console and 'action="/"' not in console,
            "the Recompute button posts back through the proxy",
            "unrewritten, Recompute navigates the frame to the app's home page",
        )
    )

    # Containment that does not rest on the console never emitting a script.
    status, headers, _ = http_get_full(f"{base}/api/console?event={rich_event['id']}")
    policy = headers.get("content-security-policy", "")
    checks.append(
        Check(
            "proxy serves a containment policy",
            status == 200 and "default-src 'none'" in policy and "form-action" in policy,
            policy or "no content-security-policy header",
            "the frame is same-origin; without a policy its containment rests entirely on "
            "the console keeping its escaping",
        )
    )

    # A repeated key. The console reads the first (`server.py` takes values[0]), so a proxy
    # that collapsed the pair would answer a different event than the URL names.
    first, one = http_get(f"{base}/api/console?event={rich_event['id']}")
    second, two = http_get(f"{base}/api/console?event={rich_event['id']}&event={thin_event['id']}")
    once, twice = proxied_event_id(one), proxied_event_id(two)
    checks.append(
        Check(
            "proxy forwards a repeated key as given",
            first == second == 200 and once == twice == rich_event["id"],
            f"asked {rich_event['id']} then {rich_event['id']},{thin_event['id']}: "
            f"priced {once!r} and {twice!r}",
            "the console reads the first of a repeated key, so a proxy that keeps the last "
            "one answers a different event than the URL names",
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
