"""The three content blocks: the decision, the market, and the refusals.

Split out of `page.py` because the four states of the decision block plus the market
and the refusal panel are more prose than a page shell should hold. Same rules apply:
every number goes through `units.num`, every sentence through `labels.render`.
"""

from __future__ import annotations

from typing import Mapping

from ticketpath.core import labels
from ticketpath.console.units import (
    bps_text,
    esc,
    lamports_text,
    money,
    num,
    pct_text,
    plural,
    sol_exact,
    sol_text,
    value_of,
)


def selected_tier(payload: Mapping) -> dict | None:
    tiers = payload.get("tiers") or []
    for tier in tiers:
        if tier.get("selected"):
            return tier
    return tiers[0] if tiers else None


def decision(payload: Mapping) -> str:
    """The largest thing on the page, and the only block whose wording is regime-dependent."""
    tier = selected_tier(payload)
    if tier is None:
        return f'<section class="panel"><p>{esc(labels.render("no_resale_record"))}</p></section>'
    out = ['<section class="panel decision" aria-label="[UNVALIDATED] the decision">']
    out.append("<h2>[UNVALIDATED] The decision</h2>")
    out.extend(decision_mode(payload))
    out.append(f"<p>{esc(labels.render('P_CAPLINE'))}</p>")
    out.append(tier_name_line(tier))
    if tier["regime"] == "capped_and_binding":
        out.append(_binding(payload, tier))
    elif tier["regime"] == "no_resale":
        out.append(_cold(payload, tier))
    else:
        out.append(_banded(payload, tier))
    out.append(f'<p class="label-sentence">[UNVALIDATED] {esc(labels.render("T2"))}</p>')
    if tier["band"]["capViolations"]["count"]["value"]:
        count = tier["band"]["capViolations"]["count"]
        out.append(
            f'<p class="violation"><span class="n">[FIXTURE] {esc(count["value"])} of '
            f'{esc(value_of(tier["band"]["capViolations"]["of"]))} recorded sales</span> in this tier are above this cap; '
            'had this cap been enforced, those transfers would have failed, so this record could not exist.</p>'
        )
    candidate = value_of(payload["selection"]["capBpsCandidate"])
    recorded = value_of(payload["event"]["capBps"])
    if recorded is not None:
        # The cap is a rule about a future this event has; an uncapped event has no such rule.
        out.append(f'<p class="label-sentence">{esc(labels.render("P_CAP_FORWARD"))}</p>')
    if candidate is not None and recorded is not None and candidate > recorded:
        out.append(f'<p class="label-sentence">{esc(labels.render("P_CAP_ABOVE"))}</p>')
    out.append("</section>")
    return "".join(out)


def decision_mode(payload: Mapping) -> list[str]:
    """The decision instant, unmissable: which record this number came from.

    Two modes and no third. The counterfactual carries the required sentence verbatim, and
    both modes carry the event's status and dates, so a hindsight recomputation can never be
    read as a price that was set.
    """
    mode = payload.get("decisionMode") or {}
    sentence = labels.render(mode.get("labelId") or "P_MODE_COUNTERFACTUAL")
    badge = "[UNVALIDATED]" if mode.get("mode") == "counterfactual" else "[DECLARED]"
    return [
        f'<p class="mode">{badge} <strong>{esc(sentence)}</strong></p>',
        f'<p class="mode-detail">{esc(_mode_event_line(payload, mode))}</p>',
    ]


def _mode_event_line(payload: Mapping, mode: Mapping) -> str:
    event = payload["event"]
    return labels.render(
        "P_MODE_EVENT",
        name=event["name"],
        status=mode.get("eventStatus") or event.get("status") or "unknown",
        startsAt=mode.get("eventStartsAt") or event["startsAt"],
        endsAt=mode.get("eventEndsAt") or "not recorded",
        asOf=mode.get("asOf") or payload["asOf"],
    )


def tier_name_line(tier: Mapping) -> str:
    return (
        f'<p class="tier">[FIXTURE] tier: <strong>{esc(tier["name"])}</strong> · '
        f'face {money(tier["faceValueLamports"])} · regime '
        f'<span class="chip">[FIXTURE] {esc(tier["regime"].replace("_", " "))}</span></p>'
    )


def _binding(payload: Mapping, tier: Mapping) -> str:
    floor = tier["recommendation"]["bandLoLamports"] or tier["band"]["loLamports"]
    cap_bps = value_of(payload["event"]["capBps"])
    ceiling = value_of(tier["band"]["loLamports"])
    at_ceiling = value_of(tier["market"]["atCeilingCount"])
    sales = value_of(tier["market"]["sales"])
    share = (at_ceiling / sales) if sales else 0.0
    cap_percent = (cap_bps / 100.0) if cap_bps is not None else None
    out = [
        f'<p class="headline">[UNVALIDATED] {esc(labels.render("P_HEAD_FLOOR", P=sol_exact(value_of(floor)), tier=tier["name"]))}</p>',
        f'<p class="exact">{esc(_exact_ceiling_line(tier, cap_bps))}</p>',
        f'<p>{esc(labels.render("A19", c=_trim(cap_percent), k=at_ceiling, n=sales, s=pct_text(share)))}</p>',
        f'<p class="floor">{esc(labels.render("P_A19_VALUE", m=sol_exact(value_of(floor))))}</p>',
        f'<p class="range">{esc(labels.render("P_A19_RANGE", lo=sol_exact(value_of(floor))))}</p>',
        f'<p class="label-sentence">[DECLARED] τ {esc(_trim(value_of(tier["band"]["tau"])))} · '
        f'[REFUSED] {esc(labels.render("P_TAU_INERT"))}</p>',
    ]
    out.append(_net_line(payload, tier))
    return "".join(out)


def _exact_ceiling_line(tier: Mapping, cap_bps) -> str:
    """The [EXACT] line, exact at its displayed precision.

    The ceiling is an integer number of lamports, so it is printed in lamports beside the
    integer multiplication that produces it. Printing it in SOL at two decimal places made
    `1.12 = 0.90 x 1.25` false: 0.90 x 1.25 is 1.125, and no rounding of 1.125 to two
    decimals keeps that equality true.
    """
    ceiling = value_of(tier["band"]["ceilingLamports"])
    face = value_of(tier["faceValueLamports"])
    if ceiling is None or cap_bps is None:
        return labels.render("P_CEILING_NONE", face=sol_exact(face))
    return "[EXACT] " + labels.render(
        "P_EXACT_CEILING",
        lamports=lamports_text(ceiling),
        face=lamports_text(face),
        cap=int(cap_bps),
        sol=sol_exact(ceiling),
    )


def _net_line(payload: Mapping, tier: Mapping) -> str:
    """The net line: rendered when a fee is set, refused when the fee is above the price.

    The fee is the declared parameter the page carries in the controls, not a number
    recomputed here, and the arithmetic is `core`'s integer subtraction.
    """
    recommendation = tier["recommendation"]
    net = recommendation.get("netRevenue")
    if net is None:
        return ""
    per_ticket = value_of(net["perTicket"])
    fee = value_of(payload["selection"]["feeLamports"])
    if net.get("negative"):
        return (
            f'<p class="warning">[REFUSED] '
            f'{esc(labels.render("P_NET_NEGATIVE", fee=sol_exact(fee), price=sol_exact(value_of(recommendation["recommendedLamports"])), shortfall=sol_exact(abs(per_ticket))))}</p>'
        )
    return (
        f'<p class="label-sentence">[EXACT] '
        f'{esc(labels.render("P_NET", net=sol_exact(per_ticket), fee=sol_exact(fee)))}</p>'
    )


def _banded(payload: Mapping, tier: Mapping) -> str:
    recommendation = tier["recommendation"]
    level = recommendation["recommendedLamports"]
    lo = recommendation["bandLoLamports"]
    hi = recommendation["bandHiLamports"]
    out = [f'<p class="headline">[UNVALIDATED] {esc(labels.render("P_HEAD", P=sol_text(value_of(level))))}</p>']
    if lo is not None and hi is not None:
        out.append(
            f'<p class="range">[UNVALIDATED] {esc(labels.render("P_BAND", P_lo=sol_text(value_of(lo)), P_hi=sol_text(value_of(hi))))}</p>'
        )
    out.append(f'<p class="label-sentence">[FIXTURE] basis: {esc(recommendation["basis"])} · '
               f'{esc(labels.render("T3"))}</p>')
    if lo is not None and hi is not None:
        out.append(
            f'<p class="range">[UNVALIDATED] {esc(labels.render("P_RANGE"))}</p>'
        )
    out.append(f'<p>{esc(labels.render("A4"))}</p>')
    if tier["regime"] == "capped_no_mass_point":
        out.append(f'<p class="warning">[UNVALIDATED] {esc(labels.render("A20"))}</p>')
    a2 = "A2" if value_of(payload["event"]["capBps"]) is not None else "A2_UNCAPPED"
    out.append(f'<p class="label-sentence">[UNVALIDATED] {esc(labels.render(a2))}</p>')
    out.append(_net_line(payload, tier))
    return "".join(out)


def _cold(payload: Mapping, tier: Mapping) -> str:
    band = tier["band"]
    lo, hi = band["loLamports"], band["hiLamports"]
    cap_bps = value_of(payload["event"]["capBps"])
    out = [f'<p class="headline">[REFUSED] {esc(labels.render("no_resale_record"))}</p>']
    if band.get("refusalCode") == "before_on_sale_no_pool":
        out.append(f'<p class="warning">[REFUSED] {esc(labels.render("before_on_sale_no_pool"))}</p>')
    elif lo is not None and hi is not None:
        out.append(
            f'<p class="range">[UNVALIDATED] prior band around face: '
            f'{money(lo)} – {money(hi)}. {esc(labels.render("P_BAND_ON_PRIOR"))}</p>'
        )
        out.append(f'<p class="label-sentence">[UNVALIDATED] {esc(_band_prior_label(payload, tier))}</p>')
    out.extend(
        [
            f'<p class="label-sentence">[UNVALIDATED] {esc(_fitted_label(payload))}</p>',
            f'<p class="label-sentence">[UNVALIDATED] {esc(labels.render("A11"))}</p>',
            f'<p class="exact">{esc(_exact_ceiling_line(tier, cap_bps))}</p>',
            f'<p class="label-sentence">{esc(labels.render("P_COLD_CHANGE"))}</p>',
        ]
    )
    return "".join(out)


def _band_prior_label(payload: Mapping, tier: Mapping) -> str:
    """The sentence for the band that is actually on the page, with its real source."""
    label_id = tier["band"]["labelId"]
    n_events = value_of(payload["pooled"]["eventsWithResale"])
    return labels.render(label_id, n_events=n_events)


def _fitted_label(payload: Mapping) -> str:
    # Completed events, and the same count the refusal panel prints: one number for one
    # clause. It used to pass `eventsWithResale` here and `eventsInWindow` there.
    n_completed = value_of(payload["pooled"]["eventsCompleted"])
    m_with_resale = value_of(payload["pooled"]["eventsWithResale"])
    label_id, fields = _a17_label(n_completed, m_with_resale)
    return labels.render(label_id, **fields)


def _a17_label(n_events, m) -> tuple[str, dict]:
    """A17 with its two counts agreeing in number. One event reads as one event."""
    if n_events == 1 and m == 1:
        return "A17_ONE_ONE", {}
    if n_events == 1:
        return "A17_ONE", {"m": m}
    if m == 1:
        return "A17_ONE_M", {"n_events": n_events}
    return "A17", {"n_events": n_events, "m": m}


def _trim(value) -> str:
    if value is None:
        return "—"
    text = f"{float(value):.1f}"
    return text[:-2] if text.endswith(".0") else text


def market(payload: Mapping) -> str:
    """The market block, scoped out loud.

    Every count here is the tier's, and the sentence says so; the event total is printed
    beside it, because the evidence strip prints the event total and two numbers about
    resales on one page may not look like a contradiction.
    """
    tier = selected_tier(payload)
    if tier is None:
        return '<section class="panel"><h2>[FIXTURE] The market</h2><p>[REFUSED] no ledger.</p></section>'
    market = tier["market"]
    cap_bps = value_of(payload["event"]["capBps"])
    out = ['<section class="panel market" aria-label="[FIXTURE] the market">']
    out.append("<h2>[FIXTURE] The market</h2>")
    ceiling_clause = (
        f'at the ceiling {num(market["atCeilingCount"])} — {esc(labels.render("A16"))}'
        if cap_bps is not None
        else esc(labels.render("P_NO_CAP"))
    )
    out.append(
        f'<p>in this tier {num(market["sales"])} {plural(value_of(market["sales"]), "sale")} of '
        f'{num(market["eventSales"])} on this event · '
        f'median markup {bps_text(market["medianMarkupBps"], trim=False)} · '
        f'mean markup {bps_text(market["meanMarkupBps"], trim=False)} · '
        f'{ceiling_clause}</p>'
    )
    repeat = market.get("repeatSale")
    if repeat:
        out.append(
            f'<p>[FIXTURE] {esc(labels.render("A18", p1=sol_text(value_of(repeat["p1Lamports"])), p2=sol_text(value_of(repeat["p2Lamports"])), d=round(value_of(repeat["days"]), 1)))}</p>'
        )
    rate = market["salesPerTicketDay"]
    if rate is not None:
        sales = value_of(market["sales"])
        prior = bool(market.get("salesPerTicketDayIsPrior"))
        label_id = "A1_ZERO" if prior else ("A1_ONE" if sales == 1 else "A1")
        # The rate is a number, so it goes on the page through `units.num` with its own
        # badge in front of it -- `[DECLARED]` when it is a prior posterior mean, never
        # `[FIXTURE]` as if the record had measured it.
        out.append(f'<p>sale rate in this tier: {num(market["per1000TicketDays"], "rate")}.</p>')
        out.append(f'<p>{esc(labels.render(label_id, n=sales))}</p>')
        out.append(f'<p class="label-sentence">[{_badge(prior)}] {esc(labels.render("T4"))}</p>')
        out.append(f'<p>exposure {num(market["exposureTicketDays"], "float")} at risk.</p>')
    else:
        out.append(f'<p>[REFUSED] {esc(labels.render("no_exposure"))}</p>')
    out.append("</section>")
    return "".join(out)


def _badge(is_prior: bool) -> str:
    """The badge the rate above carries, for the sentence that describes it."""
    return "DECLARED" if is_prior else "FIXTURE"


def refusals(payload: Mapping) -> str:
    """Always present, never empty. Each line names the missing observation or the censoring."""
    tier = selected_tier(payload)
    lines = []
    for entry in payload["refusals"]:
        code = entry["code"]
        label_id = entry["labelId"]
        if code == "path_answered" and tier is not None:
            theta = tier["path"]["theta"]
            lines.append(
                f'<li>[UNVALIDATED] path curvature: {num(theta, "log")} (log units per log day) · '
                f'{esc(tier["path"]["identification"])}</li>'
            )
            continue
        fields = _refusal_fields(entry, payload, tier)
        if label_id == "insufficient_marks" and tier is not None:
            # One sale is not one sale's worth of plural: the singular sentence exists.
            label_id = "insufficient_marks_one" if value_of(tier["market"]["sales"]) == 1 else "insufficient_marks"
            if label_id == "insufficient_marks_one":
                lines.append(f'<li>[REFUSED] {esc(code)}: {esc(labels.render(label_id))}</li>')
                continue
            lines.append(
                f'<li>[REFUSED] {esc(code)}: {_count_sentence(label_id, tier["market"]["sales"], fields)}</li>'
            )
            continue
        if label_id == "A17":
            label_id, fields = _a17_label(fields.get("n_events"), fields.get("m"))
        elif label_id == "outside_support":
            label_id, fields = _span_label(label_id, fields)
        try:
            sentence = labels.render(label_id, **fields)
        except KeyError:
            sentence = code
        lines.append(f"<li>[REFUSED] {esc(code)}: {esc(sentence)}</li>")
    out = ['<section class="panel refusals" aria-label="[REFUSED] what the engine refuses">']
    out.append("<h2>[REFUSED] What the engine refuses</h2>")
    out.append("<ul>" + "".join(lines) + "</ul>")
    out.append("</section>")
    return "".join(out)


def _count_sentence(label_id: str, count: Mapping, fields: Mapping) -> str:
    """A refusal whose count keeps the badge it carries everywhere else on the page.

    The sentence comes from the registry with a marker where the count goes, so the wording
    is the registry's, and `units.num` puts the badge in front of the value in the same text
    run, exactly as the evidence and market blocks do.
    """
    marker = "\x00"
    head, _, tail = labels.render(label_id, **{**fields, "n": marker}).partition(marker)
    return f"{esc(head)}{num(count)}{esc(tail)}"


def _refusal_fields(entry: Mapping, payload: Mapping, tier: Mapping | None) -> dict:
    if entry["labelId"] == "insufficient_marks" and tier is not None:
        return {"n": value_of(tier["market"]["sales"])}
    if entry["labelId"] == "A17":
        return {
            "n_events": value_of(payload["pooled"]["eventsCompleted"]),
            "m": value_of(payload["pooled"]["eventsWithResale"]),
        }
    if entry["labelId"] in ("insufficient_time_spread", "outside_support") and tier is not None:
        path = _path_numbers(tier)
        return {"n": path["n"], "d": path["d"], "k": path["k"]}
    if entry["labelId"] == "cap_would_refuse" and tier is not None:
        return {"k": value_of(tier["band"]["capViolations"]["count"]), "n": tier["band"]["capViolations"]["of"]}
    return {}


def _path_numbers(tier: Mapping) -> dict:
    """Counts for a path refusal sentence, read from the badged payload numbers."""
    market = tier["market"]
    path = tier["path"]
    return {
        "n": value_of(market["sales"]),
        "d": _round(value_of(path["spreadDays"]), 1),
        "k": _round(value_of(path["supportDays"][0]) if path.get("supportDays") else None, 1),
    }


def _round(value, digits: int = 1):
    return None if value is None else round(float(value), digits)


def _span_label(label_id: str, fields: Mapping) -> tuple[str, dict]:
    """A missing span reads as a sentence, not as `None`.

    `outside_support` is the one refusal whose evidence can arrive incomplete: the payload
    permits an absent `spreadDays` (the api's `num()` returns a wrapper with no value for
    it, and `path_model._refused` defaults it to None). When it is absent the clause that
    needs it is dropped, and the rest of the refusal -- the count, the stop, the missing
    window, the withheld value -- is unchanged. `insufficient_time_spread` is not rewritten:
    its span is the reason it refuses, so it must never be quietly dropped.
    """
    if fields.get("d") is None and fields.get("k") is not None:
        return "outside_support_no_span", {"n": fields.get("n"), "k": fields.get("k")}
    return label_id, dict(fields)
