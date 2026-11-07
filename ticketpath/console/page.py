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
    cap = value_of(payload["event"]["capBps"])
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
            f'<label for="capBps">capBps (0–10000)<br><input id="capBps" name="capBps" type="number" min="0" max="10000" value="{esc("" if cap is None else cap)}"></label>',
            f'<label for="feeLamports">feeLamports (blank = no fee model)<br><input id="feeLamports" name="feeLamports" type="number" min="0" value="{esc("" if fee is None else fee)}"></label>',
            f'<label for="tau">tau (0.10–0.406)<br><input id="tau" name="tau" type="number" step="0.001" min="0.1" max="0.406" value="{esc(tau)}"></label>',
            '<button type="submit">Recompute</button> ',
            f'<button type="submit" name="sim" value="1">{esc(labels.render("P_SIM_BUTTON"))}</button>',
            "</form>",
            f'<p class="label-sentence">{esc(labels.render("P_ASOF", asOf=payload["asOf"]))}</p>',
        ]
    )


def canonical(payload: Mapping) -> str:
    url = payload.get("canonicalUrl") or ""
    return f'<p>canonical URL for this decision: <code>{esc(url)}</code></p>'


def evidence(payload: Mapping) -> str:
    """The strip spec 1.1 step 3 fixes: one badge per count, carried by the count itself.

    Each number arrives badged from `units.num`. A badge in front of the paragraph as well
    would print it twice for the same fact, so only the nouns live here -- and each one
    agrees in number with its count.
    """
    ev = payload["evidence"]
    tiers = payload["tiers"]
    selected = blocks.selected_tier(payload)
    tiers_text = " · ".join(t["name"] for t in tiers)
    resales = value_of(ev["resales"])
    tickets = value_of(ev["tickets"])
    platform = value_of(ev["eventsOnPlatform"])
    transactions = value_of(ev["onchainTransactions"])
    # A count of tickets at a ceiling exists only where a ceiling does. The uncapped page
    # used to print "0 at the ceiling" beside a regime line that said `uncapped`.
    ceiling_item = (
        f' · {num(ev["atCeiling"])} at the ceiling'
        if value_of(payload["event"]["capBps"]) is not None
        else " · no resale cap, so no ceiling"
    )
    return "".join(
        [
            '<section class="panel evidence" aria-label="[FIXTURE] the evidence">',
            f'<p>{num(ev["resales"])} {plural(resales, "resale")} on this event · '
            f'{num(ev["tickets"])} {plural(tickets, "ticket")}'
            f'{ceiling_item}</p>',
            f'<p>{num(ev["eventsOnPlatform"])} {plural(platform, "event")} on this platform, '
            f'{num(ev["eventsWithResale"])} with any resale</p>',
            f'<p>{num(ev["onchainTransactions"])} {plural(transactions, "on-chain transaction")}</p>',
            f'<p class="label-sentence">[FIXTURE] tiers on this event: {esc(tiers_text)}'
            + (f' · showing {esc(selected["name"])}' if selected else "")
            + "</p>",
            "</section>",
        ]
    )


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
        out.append(
            f'<p>[DEVNET] Verified at {esc(chain.get("checkedAt"))} against api.devnet.solana.com</p>'
            f'<p>[DEVNET] signature <code>{esc(chain["signature"])}</code> · slot '
            f'<span class="n">[DEVNET] {esc(chain["slot"])}</span> · block time '
            f'<span class="n">[DEVNET] {esc(chain["blockTime"])}</span> · cluster {esc(chain.get("cluster"))}</p>'
            f'<p>[DEVNET] quote id <code>{esc(chain["quoteId"])}</code> · quote hash <code>{esc(chain["quoteHash"])}</code></p>'
            f'<p class="label-sentence">{esc(labels.render("P_CHAIN_MEMO"))}</p>'
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
    out.append("</section>")
    return "".join(out)


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
