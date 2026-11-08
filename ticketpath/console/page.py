"""The console page: one HTML string, server-rendered, standard library only.

No framework, no CDN, no build step, no JavaScript required for any number to appear.
Every control is a plain `<form method="get">`, so every state a judge can reach has a URL
that reproduces it. The one inline script is not a script: the Recompute button is a
submit button.

Reading order, fixed by the spec and by the tests: the banner, the title, the controls,
the canonical URL, the evidence strip, the decision, the market, the refusals, the design
panel, the simulated state machine, and the chain slot last.

Every number carries its provenance in its own text run, and there are two provenances. A
number the artefact's quote hash covers is rendered through `units.num` with a badge; a
number the hash does not cover is rendered through `units.num` with `units.STATED` instead,
because a badge on it would be a claim the file cannot back (feature 2, the forged-signature
finding). Every sentence comes from `labels`, by id.
"""

from __future__ import annotations

from typing import Mapping

from ticketpath.console import blocks, units
from ticketpath.console.units import esc, num, plural, value_of
from ticketpath.core import labels

TITLE = "Ticketpath — organizer pricing console"

STYLE = """
:root { color-scheme: light; }
body { font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
       margin: 0; padding: 0 0 3rem; color: #14181d; background: #fbfbfa; }
.banner { background: #14181d; color: #fff; padding: 0.9rem 1.2rem; font-size: 15px; line-height: 1.45; }
.banner strong { letter-spacing: 0.02em; }
main { max-width: 62rem; margin: 0 auto; padding: 0 1.2rem; }
h1 { font-size: 1.35rem; margin: 1.2rem 0 0.6rem; }
h2 { font-size: 1.05rem; margin: 0 0 0.6rem; letter-spacing: 0.01em; }
.panel { background: #fff; border: 1px solid #d7d7d2; border-radius: 6px;
         padding: 1rem 1.1rem; margin: 1rem 0; }
.decision { border-width: 2px; border-color: #14181d; }
.decision .headline { font-size: 1.45rem; font-weight: 700; line-height: 1.3; margin: 0.2rem 0 0.8rem; }
.decision .floor, .decision .range { font-weight: 700; font-size: 1.05rem; }
.violation { border-left: 4px solid #8a1c1c; padding-left: 0.7rem; }
.warning { border-left: 4px solid #7a5c00; padding-left: 0.7rem; }
.mode { background: #14181d; color: #fff; border-left: 8px solid #8a1c1c; padding: 0.7rem 0.8rem;
        font-size: 16px; line-height: 1.45; margin: 0.2rem 0 0.6rem; }
.mode strong { font-weight: 700; letter-spacing: 0.01em; }
.mode-detail { color: #3d434a; font-size: 15px; margin: 0 0 0.8rem; font-variant-numeric: tabular-nums; }
.label-sentence { color: #3d434a; font-size: 15px; }
.n, .badge { font-size: inherit; font-variant-numeric: tabular-nums; }
.badge { font-weight: 700; letter-spacing: 0.02em; }
.chip { border: 1px solid #9a9a94; border-radius: 999px; padding: 0 0.5rem; font-size: 15px; }
form { background: #fff; border: 1px solid #d7d7d2; border-radius: 6px; padding: 0.9rem 1.1rem; }
label { display: inline-block; margin: 0 1rem 0.6rem 0; font-size: 15px; }
input, select { font: inherit; padding: 0.2rem 0.3rem; border: 1px solid #b9b9b3; border-radius: 4px; }
button { font: inherit; padding: 0.3rem 0.9rem; border: 1px solid #14181d; border-radius: 4px;
         background: #14181d; color: #fff; cursor: pointer; }
table { border-collapse: collapse; width: 100%; font-size: 15px; }
th, td { border-bottom: 1px solid #e2e2dd; text-align: left; padding: 0.35rem 0.4rem; vertical-align: top; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; word-break: break-all; }
ul { padding-left: 1.1rem; }
li { margin: 0.25rem 0; }
"""


def render(payload: Mapping) -> str:
    """The whole page. Interpolation goes through `html.escape`; numbers through `units`."""
    parts = [
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
        f"<title>{esc(TITLE)}</title>",
        f"<style>{STYLE}</style></head><body>",
        banner(payload),
        "<main>",
        f"<h1>{esc(TITLE)}</h1>",
        controls(payload),
        canonical(payload),
        evidence(payload),
        blocks.decision(payload),
        blocks.market(payload),
        blocks.refusals(payload),
        design_panel(payload),
        simulation(payload),
        chain_slot(payload),
        "</main></body></html>",
    ]
    return "".join(parts)


def banner(payload: Mapping) -> str:
    """Spec 1.1 step 1: T1, the design pointer, and the store hash. Three lines, once each.

    T5 is not printed here. Spec 2.3 puts it on the chain slot in its absent state, and
    printing it here as well restated "No program is deployed on any cluster" twice in the
    first two lines of the page.
    """
    sha = payload["fixtureBuild"]["sha256"]
    return "".join(
        [
            '<div class="banner" role="note">',
            f"<p><strong>{esc(labels.render('T1'))}</strong></p>",
            f"<p>{esc(labels.render('P_BANNER_2'))}</p>",
            f'<p>fixture build: <code>{esc(sha)}</code></p>',
            "</div>",
        ]
    )


def controls(payload: Mapping) -> str:
    selected_event = payload["event"]["id"]
    selected_tier = payload["selection"]["tierId"]
    options = []
    for row in payload["events"]:
        label = f"{row['name']} — {row['regime'].replace('_', ' ')}"
        mark = " selected" if row["selected"] else ""
        options.append(f'<option value="{esc(row["id"])}"{mark}>{esc(label)}</option>')
    event_select = (
        '<label for="event">event<br><select id="event" name="event">' + "".join(options) + "</select></label>"
    )
    tier_options = []
    for tier in payload["tiers"]:
        mark = " selected" if tier["selected"] else ""
        tier_options.append(
            f'<option value="{esc(tier["tierId"])}"{mark}>{esc(tier["name"])} — {esc(tier["regime"].replace("_", " "))}</option>'
        )
    tier_select = (
        '<label for="tier">tier<br><select id="tier" name="tier">'
        + "".join(tier_options)
        + "</select></label>"
    )
    # The field carries the cap this page prices against, which is the one in the URL when
    # the URL names one and the event's recorded cap otherwise. It used to carry the
    # recorded cap unconditionally, so `?capBps=0` printed a decision against a 0 bps cap
    # beside a field reading 1500 and a canonical URL reading 0.
    cap_in_force = value_of(payload["selection"]["capBpsCandidate"])
    recorded_cap = value_of(payload["event"]["capBps"])
    cap_label = (
        "capBps (0–10000)"
        if recorded_cap is not None
        else "capBps (0–10000, this event records no cap)"
    )
    cap_rule = (
        labels.render("P_CAP_RULE_UNCAPPED")
        if recorded_cap is None
        else labels.render("P_CAP_RULE", recorded=int(recorded_cap))
    )
    fee = payload["selection"]["feeLamports"]["value"]
    tau = payload["selection"]["tau"]["value"]
    mode = (payload.get("decisionMode") or {}).get("mode") or "counterfactual"
    mode_select = (
        '<label for="mode">decision mode<br><select id="mode" name="mode">'
        + "".join(
            f'<option value="{esc(value)}"{" selected" if mode == value else ""}>{esc(text)}</option>'
            for value, text in (
                ("counterfactual", "counterfactual — recomputed from this event's own record"),
                ("before_on_sale", "before on-sale — other events only"),
            )
        )
        + "</select></label>"
    )
    return "".join(
        [
            '<form method="get" action="/">',
            event_select,
            tier_select,
            mode_select,
            f'<label for="asOf">asOf (ISO-8601 UTC)<br><input id="asOf" name="asOf" type="text" size="24" value="{esc(payload["asOf"])}"></label>',
            f'<label for="capBps">{esc(cap_label)}<br><input id="capBps" name="capBps" type="number" min="0" max="10000" value="{esc("" if cap_in_force is None else cap_in_force)}"></label>',
            f'<label for="feeLamports">feeLamports (blank = no fee model)<br><input id="feeLamports" name="feeLamports" type="number" min="0" value="{esc("" if fee is None else fee)}"></label>',
            f'<label for="tau">tau (0.10–0.406)<br><input id="tau" name="tau" type="number" step="0.001" min="0.1" max="0.406" value="{esc(tau)}"></label>',
            '<button type="submit">Recompute</button> ',
            f'<button type="submit" name="sim" value="1">{esc(labels.render("P_SIM_BUTTON"))}</button>',
            "</form>",
            f'<p class="label-sentence">{esc(labels.render("P_ASOF", asOf=payload["asOf"]))}</p>',
            f'<p class="label-sentence">{esc(cap_rule)}</p>',
        ]
    )


def canonical(payload: Mapping) -> str:
    url = payload.get("canonicalUrl") or ""
    return f'<p>canonical URL for this decision: <code>{esc(url)}</code></p>'


def _numbered(sentence: str, numbers: list) -> str:
    """A registry sentence whose counts each keep their own badge, in the order they appear.

    The sentence is the registry's, with one `\x00` marker per count; each marker is replaced
    by the rendered number, so a count in a sentence travels with its badge exactly as a count
    in a `<p>` does. `blocks._sentence` does the same job by name; this one is by position
    because a strip fragment is one clause with at most two counts in it.
    """
    parts = sentence.split("\x00")
    out = []
    for index, part in enumerate(parts):
        out.append(esc(part))
        if index < len(numbers):
            out.append(num(numbers[index]))
    return "".join(out)


def evidence(payload: Mapping) -> str:
    """The strip spec 1.1 step 3 fixes: one badge per count, carried by the count itself.

    Each number arrives badged from `units.num`. A badge in front of the paragraph as well
    would print it twice for the same fact, so only the nouns live here -- and each one
    agrees in number with its count.

    Two branches are about scope, and both used to be about the wrong cap or the wrong
    record. The ceiling item follows the cap this page prices against, not the event's
    recorded one, and it says which of the two it is counting against. In the before-on-sale
    mode the counts say how many rows enter the decision and how many the mode excludes,
    because a bare `0 resales` over a store that holds 12 says the record is absent.
    """
    ev = payload["evidence"]
    tiers = payload["tiers"]
    selected = blocks.selected_tier(payload)
    tiers_text = " · ".join(t["name"] for t in tiers)
    resales = value_of(ev["resales"])
    tickets = value_of(ev["tickets"])
    transactions = value_of(ev["onchainTransactions"])
    in_force = value_of(payload["selection"]["capBpsCandidate"])
    recorded = value_of(payload["event"]["capBps"])
    mode = payload.get("decisionMode") or {}
    excluded_resales = mode.get("excludedResales")
    excluded_tickets = mode.get("excludedTickets")
    if mode.get("usesOwnRecord") is False and excluded_resales is not None:
        # The rows are in the store and the mode does not read them. Say both counts.
        counts = (
            _numbered(labels.render("P_STRIP_EXCLUDED_RESALES", n="\x00", m="\x00"), [ev["resales"], excluded_resales])
            + " · "
            + _numbered(labels.render("P_STRIP_EXCLUDED_TICKETS", n="\x00", m="\x00"), [ev["tickets"], excluded_tickets])
        )
        ceiling_item = " · " + esc(labels.render("P_STRIP_EXCLUDED_CEILING"))
    else:
        counts = f'{num(ev["resales"])} {plural(resales, "resale")} on this event · ' f'{num(ev["tickets"])} {plural(tickets, "ticket")}'
        if in_force is None:
            # No cap in force and none recorded: there is no ceiling to count against.
            ceiling_item = " · no resale cap, so no ceiling"
        elif recorded is None:
            # A cap in force and no recorded cap: the count of sales at the ceiling is a count
            # against a ceiling this record never had, so it is not printed; the cap the page
            # prices against is named instead.
            ceiling_item = " · " + _numbered(
                labels.render("P_STRIP_CAP_UNCAPPED_RECORD", cap="\x00"),
                [payload["selection"]["capBpsCandidate"]],
            )
        elif in_force != recorded:
            # Both exist and they differ: the count is against the record's own cap, and the
            # noun says so rather than leaving the page's cap to be assumed.
            ceiling_item = f' · {num(ev["atCeiling"])} at the recorded ceiling'
        else:
            ceiling_item = f' · {num(ev["atCeiling"])} at the ceiling'
    return "".join(
        [
            '<section class="panel evidence" aria-label="[FIXTURE] the evidence">',
            f"<p>{counts}{ceiling_item}</p>",
            _store_line(ev),
            f'<p>{num(ev["onchainTransactions"])} {plural(transactions, "on-chain transaction")}</p>',
            f'<p class="label-sentence">[FIXTURE] tiers on this event: {esc(tiers_text)}'
            + (f' · showing {esc(selected["name"])}' if selected else "")
            + "</p>",
            "</section>",
        ]
    )


def _store_line(ev: Mapping) -> str:
    """The store's own event total, and -- only where it differs -- what was withheld.

    The noun `in the store` is the store's, not the cut's: the schema carries no instant at
    which an event was created, so the count of events cannot follow the decision instant,
    and `on this platform` presented a whole-store total as a fact about the instant under a
    line that says nothing after the instant enters any number. That noun then had to survive
    the loader's per-event rejection, which serves fewer events than the file carries: `7
    events in the store` on a store of 8 (N6, 10-final-review). So the store total is served
    plus held back, the served count is named beside it, and why each event was withheld is
    said in words where a reader meets the number. With nothing held back -- every shipped
    store -- the line is the one number it always was.
    """
    stored = ev["eventsInStore"]
    served = ev["eventsOnPlatform"]
    held = ev.get("eventsHeldBack")
    held_count = 0 if held is None else int(value_of(held) or 0)
    line = f'<p>{num(stored)} {plural(value_of(stored), "event")} in the store, '
    if held_count:
        reasons = _held_back_reasons(ev)
        if held_count == 1:
            # One withheld event reads as `one held back: ...` with no digit, like A1_ONE.
            reason = reasons[0] if reasons else "the loader gave no reason"
            withheld = labels.render("P_HELD_BACK_ONE", reason=esc(reason))
        else:
            withheld = labels.render(
                "P_HELD_BACK_MANY",
                n=num(held),
                reasons=esc("; ".join(reasons) or "the loader gave no reason"),
            )
        line += f"{num(served)} served, {withheld}, "
    return line + f'{num(ev["eventsWithResale"])} with any resale at this instant</p>'


def _held_back_reasons(ev: Mapping) -> list[str]:
    """Why each withheld event was withheld, in the label registry's own words.

    The typed codes travel in the payload (`heldBackReasons`) and on each refused event's own
    page, where the reader asked about it. A page about a different event says what was
    withheld in words: an engine token in the strip is the class of defect the console spent
    three passes removing, and `sale_not_priced` on a healthy event's page reads as that
    event's refusal.
    """
    out: list[str] = []
    for row in ev.get("heldBackReasons", []):
        label_id = f"held_back_{row.get('code')}"
        try:
            phrase = labels.render(label_id)
        except KeyError:
            phrase = f"a reason the loader did not name ({row.get('code')})"
        if phrase not in out:
            out.append(phrase)
    return out


def design_panel(payload: Mapping) -> str:
    rows = (
        ("list_for_resale", "price within the ceiling implied by face and cap_bps", "6010 E_CAP_EXCEEDED"),
        ("execute_resale", "price re-checked at execution", "6010 E_CAP_EXCEEDED"),
        ("execute_resale", "destination verified when the event requires it", "6012 E_DEST_UNVERIFIED"),
        ("transfer hook", "minting, escrow-routed, or a settlement in progress", "6009 E_TRANSFER_NOT_STAGED"),
        ("mint_ticket", "tier supply not exhausted", "6004 E_TIER_EXHAUSTED"),
        ("redeem_ticket", "ticket valid and not revoked", "6013 E_TICKET_INVALID"),
    )
    body = "".join(
        f'<tr><td><span class="n">[DESIGN] {esc(instruction)}</span></td>'
        f"<td>{esc(check)}</td>"
        f'<td><span class="n">[DESIGN] {esc(code)}</span></td></tr>'
        for instruction, check, code in rows
    )
    return "".join(
        [
            '<section class="panel chain-design" aria-label="[DESIGN] the program">',
            "<h2>[DESIGN] The program, as designed</h2>",
            f"<p>{esc(labels.render('P_CHAIN_DESIGN'))}</p>",
            f"<p>{esc(labels.render('P_CHAIN_INVARIANT'))}</p>",
            "<table><thead><tr><th>instruction</th><th>check</th><th>error</th></tr></thead><tbody>",
            body,
            "</tbody></table>",
            "</section>",
        ]
    )


def simulation(payload: Mapping) -> str:
    lines = payload.get("sim") or []
    out = ['<section class="panel simulation" aria-label="[SIMULATED] the state machine">']
    out.append("<h2>[SIMULATED] The state machine</h2>")
    out.append(f'<p class="label-sentence">{esc(labels.render("P_CHAIN_CAPTION"))}</p>')
    if not lines:
        out.append(f'<p>[SIMULATED] 0 arms shown. Use “{esc(labels.render("P_SIM_BUTTON"))}” to run them.</p>')
    else:
        out.append("<ul>")
        for line in lines:
            code = f'{line["code"]} {line["name"]}' if line["code"] else "no error"
            out.append(
                f'<li><span class="n">[SIMULATED] {esc(line["arm"])} · {esc(line["status"])} · {esc(code)}'
                f' — {esc(line["detail"])}</span></li>'
            )
        out.append("</ul>")
    out.append("</section>")
    return "".join(out)


# The two transfer legs, in the order a reader meets them. The names are the page's, for the
# keys the file uses; the values beside them are only ever the file's.
LEG_NAMES = (("acceptedAtCap", "at the cap"), ("refusedOverCap", "one lamport over the cap"))

# The one explorer host this page will link to. The URL is the file's, but escaping is not the
# whole answer for a URL: `javascript:` and `data:` escape cleanly and execute when clicked, so
# the scheme and the host are checked and a URL that fails is printed as text, never as a link
# (feature 2 review). Parsed by hand rather than through `urllib.parse`, because this module
# speaks no HTTP and `tests/test_boundaries.py` holds that line.
EXPLORER_PREFIX = "https://"
EXPLORER_HOSTS = ("explorer.solana.com",)


def _is_explorer_url(url: str) -> bool:
    """True only for an https URL whose authority is exactly an explorer host.

    An authority carrying userinfo or a port is refused rather than trimmed: the publisher
    writes neither, and `https://explorer.solana.com@elsewhere.example/` is a link to
    elsewhere that a `startswith` would wave through. Whitespace and control characters are
    refused because a browser may strip them and read a different URL from the one checked.
    """
    if any(char.isspace() or ord(char) < 0x20 for char in url):
        return False
    if "\\" in url or not url.startswith(EXPLORER_PREFIX):
        return False
    authority = url[len(EXPLORER_PREFIX):].split("/", 1)[0]
    if "@" in authority or ":" in authority:
        return False
    return authority.lower() in EXPLORER_HOSTS


def chain_slot(payload: Mapping) -> str:
    """The recorded quote, then the three program facts. Never the live quote as a chain one.

    `state` decides which block is true of the file: verified renders the recorded quote with
    its own instant and its own two transfers, unverified renders why it failed, absent renders
    the quote this console would commit and nothing else. `matchesCurrentQuote` is a separate
    sentence, because "the file verified" and "this page's quote is that quote" are two
    different facts and a page that merges them lies about one of them (decision MD2).
    """
    chain = payload["chain"]
    out = ['<section class="panel chain" aria-label="[DEVNET] the chain slot">']
    out.append("<h2>[DEVNET] The chain slot</h2>")
    if chain["state"] == "verified":
        out.extend(_recorded_quote(payload, chain))
    else:
        out.extend(_not_verified(chain))
    out.extend(_program_facts(chain))
    out.append("</section>")
    return "".join(out)


def _stored_number(value, kind: str = "count") -> str:
    """A recorded number printed as the file states it, or nothing if it is not a wrapper.

    The quote hash covers six fields and a slot, a block time, a cap, a face or a transfer
    price is not one of them. Those numbers keep `units.num`'s formatting and lose its badge:
    a badge there would be a provenance claim the file cannot back.
    """
    if not isinstance(value, Mapping):
        return ""
    return num(value, kind, mark=units.STATED)


def _recorded_quote(payload: Mapping, chain: Mapping) -> list[str]:
    """The artefact's own fields, printed as recorded. A None field prints nothing."""
    recorded = chain.get("recorded") or {}
    out: list[str] = []
    # The checker's own clock and its own version: neither is a chain fact, so neither carries
    # a devnet badge. It used to be printed as `[DEVNET] 2026-11-08T00:50:25.281Z`.
    checked = recorded.get("checkedAt")
    checker = recorded.get("checkerVersion")
    if checked or checker:
        line = "The file verified."
        if checked:
            line += f" The checker wrote <code>{esc(checked)}</code>"
        if checker:
            line += f" with checker <code>{esc(checker)}</code>"
        out.append(f'<p class="label-sentence">{line}.</p>')

    # The six fields the quote hash covers, in one line, so the badge on each number below is
    # a claim the hash backs.
    covered = []
    if recorded.get("quoteId"):
        covered.append(f'quote id <code>{esc(recorded["quoteId"])}</code>')
    if recorded.get("quoteHash"):
        covered.append(f'quote hash <code>{esc(recorded["quoteHash"])}</code>')
    if recorded.get("asOf"):
        covered.append(f'recorded at <code>{esc(recorded["asOf"])}</code>')
    if recorded.get("eventId"):
        covered.append(f'event <code>{esc(recorded["eventId"])}</code>')
    if recorded.get("tierId"):
        covered.append(f'tier <code>{esc(recorded["tierId"])}</code>')
    if recorded.get("modelVersion"):
        covered.append(f'model <code>{esc(recorded["modelVersion"])}</code>')
    if covered:
        out.append("<p>[DEVNET] " + " · ".join(covered) + "</p>")

    # Is the quote on this page the quote the file records, and what do the two numbers say?
    out.extend(_match_sentence(payload, chain))

    # Everything the hash does not cover. One line, one label, no badges: the file states it.
    stated = []
    if recorded.get("signature"):
        stated.append(f'signature <code>{esc(recorded["signature"])}</code>')
    slot_cell = _stored_number(recorded.get("slot"))
    if slot_cell:
        stated.append(f"slot {slot_cell}")
    block_time_cell = _stored_number(recorded.get("blockTime"))
    if block_time_cell:
        stated.append(f"block time {block_time_cell}")
    if recorded.get("cluster"):
        stated.append(f'cluster {esc(recorded["cluster"])}')
    if recorded.get("mint"):
        stated.append(f'mint <code>{esc(recorded["mint"])}</code>')
    if recorded.get("programId"):
        stated.append(f'program <code>{esc(recorded["programId"])}</code>')
    if recorded.get("memoProgram"):
        stated.append(f'memo program <code>{esc(recorded["memoProgram"])}</code>')
    face_cell = _stored_number(recorded.get("faceLamports"), "lamports")
    if face_cell:
        stated.append(f"face {face_cell}")
    cap_cell = _stored_number(recorded.get("capBps"), "integer")
    if cap_cell:
        stated.append(f"cap {cap_cell}")
    if stated:
        out.append(
            '<p class="label-sentence">The file states, and the quote hash does not cover: '
            + " · ".join(stated)
            + "</p>"
        )

    # One sentence for a reader who will not read seven lines of markup: which fields the hash
    # covers, and that the rest is the writer's assertion.
    out.append(
        f'<p class="label-sentence">{esc(labels.render("P_CHAIN_FILE_COVERAGE"))}</p>'
    )

    transfers = recorded.get("transfers") or {}
    rows = _transfer_rows(transfers)
    if rows:
        out.append(
            '<table><thead><tr><th>transfer (the file\'s own leg key)</th><th>price</th>'
            "<th>signature</th><th>slot</th><th>result</th></tr></thead><tbody>"
        )
        out.extend(rows)
        out.append("</tbody></table>")

    out.extend(_recorded_parameters(payload, chain))

    signature = recorded.get("signature")
    explorer = _explorer_link(chain)
    if explorer and isinstance(signature, str) and signature:
        out.append(
            f'<p>transaction <a href="{esc(explorer)}"><code>{esc(signature[:16])}…</code></a></p>'
        )
    elif isinstance(signature, str) and signature:
        # No link: the file's URL is not an https address on the explorer host, so the
        # signature is printed and nothing is clickable.
        out.append(f'<p>transaction <code>{esc(signature)}</code></p>')

    out.append(
        f'<p class="label-sentence">{esc(labels.render("P_CHAIN_NOT_REREAD"))}</p>'
    )
    out.append(f'<p class="label-sentence">{esc(labels.render("P_CHAIN_MEMO"))}</p>')
    return out


def _recorded_parameters(payload: Mapping, chain: Mapping) -> list[str]:
    """The cap and face the file states, the ceiling they imply, and where its number sits.

    The page printed neither the cap nor the face, so it could not show that the recorded
    recommendation (1,380,000,000 on the shipped record) is above the recorded ceiling its own
    cap and face imply (1,250,000,000). The page's own cap and face are named beside them only
    where they differ from the file's, because that difference is why the agreement above is
    about the quote and the number and not about the parameters.
    """
    recorded = chain.get("recorded") or {}
    capacity = recorded.get("capacity") or {}
    face = recorded.get("faceLamports")
    cap = recorded.get("capBps")
    ceiling = capacity.get("ceilingLamports")
    if not (isinstance(face, Mapping) and isinstance(ceiling, Mapping)):
        return []
    out = [
        "<p>"
        + blocks.sentence(
            "P_CHAIN_RECORDED_PARAMETERS",
            {"ceiling": num(ceiling, "lamports")},
        )
        + "</p>"
    ]
    recommendation = recorded.get("recommendedLamports")
    above = capacity.get("recommendedAboveCeiling")
    if isinstance(recommendation, Mapping) and above is not None:
        label_id = (
            "P_CHAIN_RECOMMENDED_ABOVE_CEILING"
            if above
            else "P_CHAIN_RECOMMENDED_INSIDE_CEILING"
        )
        out.append(
            "<p>" + blocks.sentence(label_id, {"rec": num(recommendation, "lamports")}) + "</p>"
        )

    # The page's own parameters, named only where they are not the file's: that difference is
    # why the agreement above is about the quote and the number, not about the parameters.
    selection = payload.get("selection")
    live_cap = selection.get("capBpsCandidate") if isinstance(selection, Mapping) else None
    tier = blocks.selected_tier(payload)
    live_face = (tier or {}).get("faceValueLamports")
    if isinstance(live_cap, Mapping) and isinstance(live_face, Mapping):
        same = value_of(live_cap) == value_of(cap) and value_of(live_face) == value_of(face)
        if not same:
            out.append(
                "<p>"
                + blocks.sentence(
                    "P_CHAIN_PAGE_PARAMETERS",
                    {"cap": num(live_cap, "integer"), "face": num(live_face, "lamports")},
                )
                + "</p>"
            )
    return out


def _transfer_rows(transfers: Mapping) -> list[str]:
    """One row per leg the file records: its price, its signature, its slot, its outcome.

    The row's label is the file's own leg key, not a name this page made up: the page used to
    print "at the cap" beside a price 130,000,000 lamports below the ceiling it printed on the
    same page (feature 2 review). Each value is printed only at the type its grammar names, so
    a price that is a string, a slot that is text or a signature that is an int renders as
    nothing instead of taking the page down.
    """
    rows = []
    for leg, row in transfers.items():
        if not isinstance(row, Mapping):
            continue
        price_cell = _stored_number(row.get("priceLamports"), "lamports")
        signature = row.get("signature")
        signature_cell = (
            f"<code>{esc(signature)}</code>" if isinstance(signature, str) and signature else ""
        )
        slot_cell = _stored_number(row.get("slot"))
        if "errorNotAString" in row:
            result_cell = "the file's error is not a string, so it is not shown"
        elif "error" in row:
            error = row["error"]
            if isinstance(error, str) and error:
                result_cell = f'refused by the chain, as the file states: <code>{esc(error)}</code>'
            else:
                result_cell = "accepted, as the file states"
        else:
            result_cell = ""
        rows.append(
            f"<tr><td><code>{esc(leg)}</code></td><td>{price_cell}</td><td>{signature_cell}</td>"
            f"<td>{slot_cell}</td><td>{result_cell}</td></tr>"
        )
    return rows


def _match_sentence(payload: Mapping, chain: Mapping) -> list[str]:
    """Whether the quote on the page is the quote the file records, and what the numbers say.

    Two statements, kept apart. The first is about the number: the recorded recommendation and
    the page's own, printed twice only where they differ. The second is about the quote: its
    id and its instant. They used to be one sentence saying "the number on this page ... is
    not the number the chain recorded" on a page printing 1.38 SOL twice (feature 2 review).
    """
    recorded = chain.get("recorded") or {}
    matches = chain.get("matchesCurrentQuote")
    decision = payload.get("decision")
    live = decision.get("recommendedLamports") if isinstance(decision, Mapping) else None
    recommendation = recorded.get("recommendedLamports")
    out: list[str] = []
    if isinstance(recommendation, Mapping) and isinstance(live, Mapping):
        if value_of(recommendation) == value_of(live):
            out.append(
                "<p>"
                + blocks.sentence("P_CHAIN_RECOMMENDED_SAME", {"rec": num(recommendation, "lamports")})
                + "</p>"
            )
        else:
            out.append(
                "<p>"
                + blocks.sentence(
                    "P_CHAIN_RECOMMENDED_DIFFER",
                    {"rec": num(recommendation, "lamports"), "cur": num(live, "lamports")},
                )
                + "</p>"
            )
    recorded_id, recorded_as_of = recorded.get("quoteId"), recorded.get("asOf")
    live_id, live_as_of = chain.get("quoteId"), payload.get("asOf")
    if matches is True and recorded_id and recorded_as_of:
        out.append(
            f'<p>{esc(labels.render("P_CHAIN_QUOTE_AGREE", quoteId=recorded_id, asOf=recorded_as_of))}</p>'
        )
    elif matches is False and all((recorded_id, recorded_as_of, live_id, live_as_of)):
        out.append(
            f'<p>{esc(labels.render("P_CHAIN_QUOTE_DISAGREE", liveQuoteId=live_id, liveAsOf=live_as_of, recordedQuoteId=recorded_id, recordedAsOf=recorded_as_of))}</p>'
        )
    return out


def _not_verified(chain: Mapping) -> list[str]:
    """Absent, or present and unverified, with the reason named rather than summarised.

    The two are kept apart by their first sentence. A file that exists and fails a check is
    not the same record as no file at all, so the absent sentence is printed only where the
    file is absent; printing both in the unverified state made a tampered artefact read like
    an empty disk (decision MD2: three states stay distinct).
    """
    reason = chain.get("reason")
    out = []
    if chain["state"] == "unverified":
        out.append(
            f'<p>[DEVNET] Unverified: {esc(_reason_sentence(reason, chain))} '
            f'<code>{esc(reason or "devnet_unverified")}</code></p>'
        )
        if reason == "cluster_not_devnet" and chain.get("reasonCluster") == "localnet":
            # The rehearsal sentence is for a rehearsal. Every non-devnet cluster used to get
            # it, so a testnet file was described as a local run and the word testnet appeared
            # nowhere on the page (feature 2 review).
            out.append(
                '<p>[DEVNET] A local rehearsal was recorded and is not devnet evidence. '
                'Nothing on this page is rendered from it: no signature, no slot, no link.</p>'
            )
    else:
        out.append(f'<p>[DEVNET] {esc(labels.render("devnet_absent"))}</p>')
    out.append(f'<p>[DEVNET] {esc(labels.render("T5"))}</p>')
    out.append(f'<p class="label-sentence">{esc(labels.render("P_CHAIN_ABSENT"))}</p>')
    out.append(
        f'<p class="label-sentence">[DESIGN] the quote this console would commit: '
        f'quote id <code>{esc(chain["quoteId"])}</code>, memo '
        f'<code>{esc(chain["memoText"])}</code>. Nothing is signed and nothing is sent.</p>'
    )
    return out


def _reason_sentence(reason: str | None, chain: Mapping) -> str:
    """The registry's sentence for a typed reason, and a named fallback for an unknown one."""
    label_id = reason or "devnet_unverified"
    cluster = chain.get("reasonCluster")
    if label_id == "cluster_not_devnet" and not isinstance(cluster, str):
        label_id = "cluster_not_devnet_unnamed"
    fields = {"cluster": cluster}
    try:
        return labels.render(label_id, **fields)
    except KeyError:
        return "The console does not know this reason, and reports it rather than guessing."


def _program_facts(chain: Mapping) -> list[str]:
    """Three claims, three sources: the file's program, this server's silence, the design doc."""
    status = chain.get("programStatus") or {}
    recorded = status.get("recorded") or {}
    out = []
    if recorded.get("programId"):
        cluster = recorded.get("cluster")
        source = recorded.get("source")
        out.append(
            f'<p>[DEVNET] {esc(labels.render("P_CHAIN_PROGRAM_RECORDED"))} '
            f'<code>{esc(recorded["programId"])}</code>'
            + (f" for cluster {esc(cluster)}" if cluster else "")
            + (f", recorded in <code>{esc(source)}</code>" if source else "")
            + "</p>"
        )
    if chain.get("memoProgram") is None:
        # A cluster the table has no measurement for. The payload answers null and the page
        # used to say nothing at all, so a testnet server looked like a devnet one.
        out.append(
            f'<p class="label-sentence">'
            f'{esc(labels.render("P_CHAIN_NO_MEMO_PROGRAM", cluster=status.get("cluster") or "unknown"))}</p>'
        )
    if not status.get("askedCluster"):
        out.append(f'<p>[DEVNET] {esc(labels.render("P_CHAIN_NOT_ASKED"))}</p>')
    design_doc = status.get("designDoc")
    if design_doc:
        out.append(
            f'<p>[DESIGN] {esc(labels.render("P_CHAIN_DESIGN_POINTER", doc=design_doc))}</p>'
        )
    return out


def _explorer_link(chain: Mapping) -> str | None:
    """The explorer URL the artefact records, and only when it is https on the explorer host.

    A link is a pointer, not evidence. Reading it out of the file means the page cannot point
    at a transaction the file does not name; a link for a placeholder signature is impossible
    because the recorded block is only rendered when the file verified. HTML-escaping a URL is
    not enough on its own: `javascript:` and `data:` escape cleanly and run when clicked, so
    the scheme and the host are checked and anything else is printed as text.
    """
    recorded = chain.get("recorded") or {}
    explorer = recorded.get("explorer")
    if not isinstance(explorer, Mapping):
        return None
    url = explorer.get("transaction")
    if not isinstance(url, str) or not url:
        return None
    if not _is_explorer_url(url):
        return None
    return url


def render_error(*, status: int, message: str, code: str) -> str:
    """Errors render as a page, never as a stack trace, because a demo cannot show one."""
    return "".join(
        [
            '<!doctype html><html lang="en"><head><meta charset="utf-8">',
            f"<title>{esc(TITLE)}</title>",
            f"<style>{STYLE}</style></head><body>",
            '<div class="banner" role="note">',
            f"<p><strong>{esc(labels.render('T1'))}</strong></p>",
            f"<p>{esc(labels.render('T5'))}</p>",
            "</div><main>",
            f"<h1>{esc(TITLE)}</h1>",
            f'<p class="violation">[REFUSED] <span class="n">[REFUSED] {esc(status)}</span> {esc(code)}: {esc(message)}</p>',
            '<p><a href="/">back to the decision</a></p>',
            "</main></body></html>",
        ]
    )
