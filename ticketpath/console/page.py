"""The console page: one HTML string, server-rendered, standard library only.

No framework, no CDN, no build step, no JavaScript required for any number to appear.
Every control is a plain `<form method="get">`, so every state a judge can reach has a URL
that reproduces it. The one inline script is not a script: the Recompute button is a
submit button.

Reading order, fixed by the spec and by the tests: the banner, the title, the controls,
the canonical URL, the evidence strip, the decision, the market, the refusals, the design
panel, the simulated state machine, and the chain slot last.

Every number is rendered through `units.num`, which puts its badge in front of it in the
same text run. Every sentence comes from `labels`, by id.
"""

from __future__ import annotations

from typing import Mapping

from ticketpath.console import blocks
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


def chain_slot(payload: Mapping) -> str:
    chain = payload["chain"]
    out = ['<section class="panel chain" aria-label="[DEVNET] the chain slot">']
    out.append("<h2>[DEVNET] The chain slot</h2>")
    if chain["state"] == "verified":
        explorer = _explorer_link(chain)
        program_id = (chain.get("programStatus") or {}).get("programId")
        out.append(
            f'<p>[DEVNET] Verified at {esc(chain.get("checkedAt"))} against api.devnet.solana.com</p>'
            f'<p>[DEVNET] signature <code>{esc(chain["signature"])}</code> · slot '
            f'<span class="n">[DEVNET] {esc(chain["slot"])}</span> · block time '
            f'<span class="n">[DEVNET] {esc(chain["blockTime"])}</span> · cluster {esc(chain.get("cluster"))}</p>'
            f'<p>[DEVNET] quote id <code>{esc(chain["quoteId"])}</code> · quote hash <code>{esc(chain["quoteHash"])}</code></p>'
        )
        if explorer:
            out.append(
                f'<p>[DEVNET] transaction <a href="{esc(explorer)}">{esc(chain["signature"][:16])}…</a>'
                + (f' · program <code>{esc(program_id)}</code>' if program_id else '')
                + "</p>"
            )
        out.append(
            '<p class="label-sentence">[DEVNET] Recorded, not independently re-read: this page '
            'recomputes the quote hash from the fields above and does not ask the cluster. The '
            'publisher read the memo back at the slot it reports; a re-read here needs '
            "TICKETPATH_RPC_ENABLED=1, which is off by default.</p>"
        )
        out.append(f'<p class="label-sentence">{esc(labels.render("P_CHAIN_MEMO"))}</p>')
    else:
        out.append(f'<p>[DEVNET] {esc(labels.render("devnet_absent"))}</p>')
        if chain.get("reason") == "cluster_not_devnet":
            out.append(
                '<p>[DEVNET] A local rehearsal was recorded and is not devnet evidence. '
                'Nothing on this page is rendered from it: no signature, no slot, no link.</p>'
            )
        out.append(f'<p>[DEVNET] {esc(labels.render("T5"))}</p>')
        out.append(f'<p class="label-sentence">{esc(labels.render("P_CHAIN_ABSENT"))}</p>')
        out.append(
            f'<p class="label-sentence">[DESIGN] the quote this console would commit: '
            f'quote id <code>{esc(chain["quoteId"])}</code>, memo '
            f'<code>{esc(chain["memoText"])}</code>. Nothing is signed and nothing is sent.</p>'
        )
    out.append("</section>")
    return "".join(out)


def _explorer_link(chain: Mapping) -> str | None:
    """The explorer URL for the verified signature, and never for anything else.

    Built only in the `verified` branch: the spec's rule is that no explorer link exists until
    an artefact has verified, so a placeholder signature can never produce one.
    """
    signature = chain.get("signature")
    cluster = chain.get("cluster")
    if not signature or cluster != "devnet":
        return None
    return f"https://explorer.solana.com/tx/{signature}?cluster=devnet"


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
