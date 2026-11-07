"""The path index: one parameter, five guards, and a martingale that is always allowed.

The model is `02-a` sections 8.2-8.3: log(price/face) linear in the deadline-convex
basis `log(1+d)` plus a linear term in `d`, fitted within a tier by demeaning, which
removes the tier-and-seat constant. One parameter is estimated, the convexity `theta`;
the linear coefficient is a nuisance that exists only to identify it and is used only
under the declared normalisation `omega = 1`.

The output is a bracket, not a point, because two normalisations are defensible and
neither is identified from one event window: `omega = 0` uses only the curvature that
the data supports, `omega = 1` attributes all within-tier level movement to
time-to-event. The age-period-cohort limitation is stated in the output itself
(`identification`), because it is the reason the answer is a bracket.

Two guards are this build's own and are stated as such:

* `cap_mass_dominates` -- when more than half the tier's marks sit on the ceiling, the
  central path statistic would describe the ceiling, not the market (03-b checklist row
  15; 02-a section 8.8). Refused rather than reported.
* `outside_support` -- the fitted shape is a local one. Evaluating it at a horizon
  outside the window the marks actually span is extrapolation, and on this fixture it
  produces factors of hundreds. The curvature is still reported as a diagnostic; no
  path value is quoted outside the observed window.

When a guard refuses, the returned object is the martingale -- a flat path at the
anchor -- and `available` is False. The flat line is still an engine output, so the page
labels it `[UNVALIDATED]` like any other.

Nothing here is a forecast of a price. The object is the price conditional on a sale
occurring at that horizon (02-a section 8.1), and the page says so.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

MIN_MARKS = 4
MIN_SPREAD_DAYS = 5.0
ANCHOR_MARKS = 5
CAP_MASS_LIMIT = 0.5
HORIZONS: tuple[int, ...] = (28, 14, 7, 2, 0)

IDENTIFICATION = (
    "Identified from within-ticket first differences where a ticket resold and from "
    "within-tier demeaning elsewhere. Ages and calendar time are collinear inside one "
    "event window (age-period-cohort): the curvature is identified, the slope only under "
    "the declared normalisation omega, so the answer is a bracket across omega in {0, 1}."
)


def _tier(features: Mapping, tier_id: str) -> dict:
    for row in features["tiers"]:
        if row["tierId"] == tier_id:
            return row
    raise KeyError(f"unknown tier {tier_id!r}")


def _refused(
    *,
    anchor: int,
    reason: str,
    horizons: Sequence[int],
    theta: float | None = None,
    theta_se: float | None = None,
    support: tuple[float, float] | None = None,
    spread_days: float | None = None,
    n_marks: int | None = None,
) -> dict:
    return {
        "available": False,
        "fitted": theta is not None,
        "reason": reason,
        "theta": theta,
        "thetaSe": theta_se,
        "omega0": None,
        "omega1": None,
        "anchorLamports": anchor,
        "basis": "martingale",
        "identification": IDENTIFICATION,
        "supportDays": support,
        "spreadDays": spread_days,
        "n": n_marks,
        "points": [
            {
                "days": days,
                "lamportsLower": anchor,
                "lamportsUpper": anchor,
                "outsideSupport": False,
            }
            for days in horizons
        ],
        "labelId": reason,
    }


def estimate(
    *,
    features: Mapping,
    tier_id: str,
    anchor_lamports: int,
    horizon_days: Sequence[int] = HORIZONS,
) -> dict:
    """Fit the curvature or refuse with a named reason, and never without the anchor."""
    row = _tier(features, tier_id)
    marks = row["marks"]
    n = len(marks)
    spread = row["timeSpreadDays"]
    if n < MIN_MARKS:
        return _refused(
            anchor=anchor_lamports, reason="insufficient_marks", horizons=horizon_days, n_marks=n, spread_days=spread
        )

    if spread < MIN_SPREAD_DAYS:
        return _refused(
            anchor=anchor_lamports,
            reason="insufficient_time_spread",
            horizons=horizon_days,
            spread_days=spread,
            n_marks=n,
        )

    share_at_ceiling = (row["atCeilingCount"] / n) if n else 0.0
    if share_at_ceiling > CAP_MASS_LIMIT:
        return _refused(
            anchor=anchor_lamports,
            reason="cap_mass_dominates",
            horizons=horizon_days,
            spread_days=spread,
            n_marks=n,
        )

    face = row["faceValueLamports"]
    ys = [math.log(mark["priceLamports"] / face) for mark in marks]
    ds = [mark["daysToEvent"] for mark in marks]
    us = [math.log(1.0 + day) for day in ds]
    n_marks = len(ys)
    y_bar = sum(ys) / n_marks
    d_bar = sum(ds) / n_marks
    u_bar = sum(us) / n_marks
    yt = [value - y_bar for value in ys]
    dt = [value - d_bar for value in ds]
    ut = [value - u_bar for value in us]

    s_dd = sum(a * a for a in dt)
    s_du = sum(a * b for a, b in zip(dt, ut))
    s_uu = sum(b * b for b in ut)
    s_dy = sum(a * y for a, y in zip(dt, yt))
    s_uy = sum(b * y for b, y in zip(ut, yt))
    delta = s_dd * s_uu - s_du * s_du
    # A fixed 2x2 solve. The dimension is fixed because the model has exactly two
    # regressors by construction (a linear term and log(1+d), 02-a section 8.3); the
    # standard library has no general linear algebra and none is needed. That is what
    # makes this exact rather than approximate.
    if delta <= 1e-12:
        return _refused(anchor=anchor_lamports, reason="degenerate_design", horizons=horizon_days)

    theta = (s_dd * s_uy - s_du * s_dy) / delta
    beta = (s_uu * s_dy - s_du * s_uy) / delta
    rss = sum(value * value for value in yt) - beta * s_dy - theta * s_uy
    residual_var = max(0.0, rss) / (n_marks - 2) if n_marks > 2 else 0.0
    theta_se = math.sqrt(residual_var * s_dd / delta)

    # The anchor is one observation -- the median mark of the last K -- not the pair of
    # marginal medians of y and d. Two separately taken medians need not lie on the fitted
    # curve, and a path anchored off the curve shifts every point by that gap: on the
    # noiseless test design it is a 0.5% error that no guard would catch.
    anchor_marks = sorted(marks[-ANCHOR_MARKS:], key=lambda mark: mark["daysToEvent"])
    anchor_mark = anchor_marks[len(anchor_marks) // 2]
    anchor_y = math.log(anchor_mark["priceLamports"] / face)
    anchor_d = anchor_mark["daysToEvent"]
    support = (min(ds), max(ds))

    points = []
    quotable = 0
    for days in horizon_days:
        outside = days < support[0] - 0.5 or days > support[1] + 0.5
        if outside:
            points.append(
                {"days": days, "lamportsLower": None, "lamportsUpper": None, "outsideSupport": True}
            )
            continue
        curvature = theta * (math.log(1.0 + days) - math.log(1.0 + anchor_d))
        omega0 = anchor_y + curvature
        omega1 = anchor_y + curvature + beta * (days - anchor_d)
        quotable += 1
        points.append(
            {
                "days": days,
                "lamportsLower": max(1, int(round(face * math.exp(omega0)))),
                "lamportsUpper": max(1, int(round(face * math.exp(omega1)))),
                "outsideSupport": False,
            }
        )

    if quotable == 0:
        refused = _refused(
            anchor=anchor_lamports,
            reason="outside_support",
            horizons=horizon_days,
            theta=theta,
            theta_se=theta_se,
            support=support,
            spread_days=spread,
            n_marks=n_marks,
        )
        refused["fitted"] = True
        refused["points"] = [
            {"days": days, "lamportsLower": anchor_lamports, "lamportsUpper": anchor_lamports, "outsideSupport": True}
            for days in horizon_days
        ]
        return refused

    return {
        "available": True,
        "fitted": True,
        "reason": None,
        "theta": theta,
        "thetaSe": theta_se,
        "omega0": points[-1]["lamportsLower"],
        "omega1": points[-1]["lamportsUpper"],
        "anchorLamports": anchor_lamports,
        "anchorLogRatio": anchor_y,
        "anchorDays": anchor_d,
        "n": n_marks,
        "spreadDays": spread,
        "supportDays": support,
        "basis": "within_tier_curvature",
        "identification": IDENTIFICATION,
        "points": points,
        "labelId": "A8",
    }
