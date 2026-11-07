#!/usr/bin/env python3
"""SIM -- estimator-property study for `records/findings/06-validation-protocol.md` section 3.

WHAT THIS IS. A generator and estimator harness, run under D2 (standard library only,
deterministic seeds, no fixture, no ticket data, nothing read from the ledger). It
answers one question per study: *given a generative model that is exactly the
estimator's own assumption, does the estimator do what the finding says it does?*

It is SIM and nothing else. Every output line is prefixed `SIM`. No number printed here
is an accuracy claim about tickets, and no result here is evidence about whether real
ticket markets look like these generative models. See the closing block and
`records/findings/09-sim-recovery.md`.

THE THREE STUDIES (specified in 06 section 3, narrowed by the run request):

  A  recovery of the pooled mean log price ratio `mu` and of the between-event variance
     `tau2` under a known truth, at 2, 5 and 20 events, in a declared arm and an
     estimated arm.  (02-e sections 4.2-4.5; shipped code `value_band.pooled`.)

  B  coverage of the declared band for a *new event's mean* counted over repeated draws,
     at the same event counts, plus the coverage of the pooled predictive width the
     engine reports beside the band.  (02-e sections 4.3, 4.7, 5.1; shipped arithmetic
     `value_band._pooled_only`.)

  C  the path estimator's recovery of a known decay parameter `theta` from within-ticket
     first differences, including the case where the cap binds and truncates the top of
     the distribution.  (02-a sections 4.1, 6.1 and 8.3; shipped code
     `path_model.estimate`, plus the repeat-sales difference estimator of 02-a 4.1.)

PASS CONDITIONS ARE DECLARED BELOW, BEFORE THE RUN, AND THE SCRIPT PRINTS A VERDICT PER
STUDY. A failed condition is reported and left alone: the estimator is not tuned to make
it pass (06 section 3.3). Where a condition is a *predicted failure* -- e.g. "the
between-event variance is not pinned at two events" -- it is written as a condition that
must hold, so it can fail like any other.

RUNTIME. Target under three minutes; the budget arithmetic is in 06 section 3.4. Each
study runs under a 60 s alarm and reports TIMEOUT rather than losing the others.

A NOTE ON THE ONE BLOCK ADDED LATER. `post_run_diagnostic` at the end of study C was
written after the first full run, to explain the sign that `C.cap_direction` reported.
It prints descriptive numbers only. No pass condition, grid, replication count or seed
was changed after the first run, and none may be.
"""

from __future__ import annotations

import math
import os
import random
import signal
import statistics
import sys
import time

# The shipped estimators are the object of the study. Import them rather than
# re-implementing them: a re-implementation would test the harness, not the engine.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ticketpath.core import path_model, value_band  # noqa: E402

# ---------------------------------------------------------------------------
# THE CONTRACT -- decided before the run. Editing any value below after seeing
# output would void the study; a changed constant needs a dated note in the finding.
# ---------------------------------------------------------------------------

SEED = "20261107-sim-recovery"

#: Truth for studies A and B. `mu` and `sigma` are the borrowed Leslie & Sorensen
#: numbers carried by the engine (`value_band.PRIOR`); `tau` is set at 0.30 so that
#: it sits strictly inside the declared grid and strictly above the API default 0.20,
#: which is what makes the declared-versus-true comparison informative.
MU_TRUE = 0.2612
TAU_TRUE = 0.30
TAU_TRUE2 = TAU_TRUE * TAU_TRUE
SIGMA_TRUE = 0.406

J_GRID = (2, 5, 20)              # events observed
MARKS_PER_EVENT = 20             # resale marks per event
R_POOL = 2000                    # replications per cell (studies A and B)

DECLARED_ARMS = (0.20, 0.30)     # 0.20 = the API default (`_parse_tau`); 0.30 = the truth
Z90 = 1.6449                     # the engine's two-sided 90%
TAU_MIN_ENGINE = 0.10            # `value_band.TAU_MIN`, the declared floor
ENGINE_SWITCH = 9                # `value_band.EVENTS_FOR_ESTIMATED_TAU`

#: Truth and design for study C. `theta` is the decay parameter on log(1+d): prices are
#: higher further from the event and fall as it approaches, which is the concession
#: shape of 02-a 5.1. `beta` is 0 so a non-zero fitted linear term is pure noise.
THETA_TRUE = 0.30
BETA_TRUE = 0.0
TICKET_SD = 0.15                 # ticket fixed-effect spread (differences it out)
PATH_TICKETS = 40                # tickets per event, two observations each
R_PATH = 400                     # replications per cell

PATH_CELLS = (
    # label, sigma (per-observation log noise), cap share s (None = uncapped), d window
    ("uncapped_low_noise", 0.02, None, (5.0, 60.0)),
    ("uncapped_noisy", 0.10, None, (5.0, 60.0)),
    ("narrow_window", 0.02, None, (40.0, 60.0)),
    ("cap10_low_noise", 0.02, 0.10, (5.0, 60.0)),
    ("cap40_low_noise", 0.02, 0.40, (5.0, 60.0)),
    ("cap70_low_noise", 0.02, 0.70, (5.0, 60.0)),
    ("cap40_noisy", 0.10, 0.40, (5.0, 60.0)),
)

#: Pass conditions, one tuple per line of output. `key` groups them into a study.
#: Every condition is a claim about the estimator, not a tolerance to be edited.
PASS_CONDITIONS = {
    # --- Study A ---------------------------------------------------------
    "A.mu": "|bias(mu_hat)| <= max(0.01, 4 x Monte-Carlo SE of the bias) in every cell",
    "A.tau_mean": "|mean(tau2_hat) - tau2_true| / tau2_true <= 0.25 at every J",
    "A.tau_pinned_20": "at J=20: p10(tau2_hat) >= 0.35 tau2_true AND p90 <= 2.0 tau2_true",
    "A.tau_unpinned_small": "at J=2 and J=5: p90(tau2_hat) >= 1.5 tau2_true OR p10 <= 0.5 tau2_true",
    "A.tau_at_floor": "share(raw tau2_hat <= 0.01) >= 0.30 at J=2, >= 0.02 at J=5, <= 0.10 at J=20",
    "A.switch": "method == 'declared' in 100% of fits at J<9; never 'declared' at J>=9",
    "A.canary": "an estimator shifted by +0.02 must be caught: |bias| > max(0.01, 4 x MC SE)",
    # --- Study B ---------------------------------------------------------
    "B.declared_matched": "coverage of the declared band at declared=0.30 in [0.87, 0.93] at every J",
    "B.declared_default": "coverage at declared=0.20 is < 0.87 at every J (under-covers a tau of 0.30)",
    "B.pooled_width": "coverage of mu +/- z sqrt(tau2_hat + varOfMu) in [0.87, 0.93] at every J",
    "B.width_shrinks": "the pooled width is strictly decreasing in J (2 > 5 > 20) in both arms",
    # --- Study C ---------------------------------------------------------
    "C.diff_uncapped": "uncapped cells: |bias(theta_hat_diff)| <= 0.01 and RMSE reported",
    "C.diff_noisy": "noisy uncapped cell: |bias(theta_hat_diff)| <= 0.02",
    "C.cap_direction": "capped cells: bias(theta_hat_diff) < 0 and mean theta_hat strictly decreasing in s",
    "C.cap_magnitude": "relative attenuation >= 10% at s=0.40 and >= 30% at s=0.70",
    "C.guard": "cap_mass_dominates in 100% of fits at s=0.70 and 0% at s<=0.40",
    "C.oracle": "|bias(theta_hat_latent)| <= 0.01 in every capped cell (the attenuation is the clip)",
}

STUDY_OF = {"A": "A", "B": "B", "C": "C"}


# ---------------------------------------------------------------------------
# Plumbing
# ---------------------------------------------------------------------------


class StudyTimeout(Exception):
    pass


def _on_alarm(signum, frame):  # noqa: ARG001
    raise StudyTimeout()


class Report:
    """Collects measured lines and condition verdicts, and prints as it goes."""

    def __init__(self) -> None:
        self.conditions: list[dict] = []
        self.started = time.perf_counter()

    def line(self, text: str) -> None:
        print(text, flush=True)

    def condition(self, study: str, key: str, observed: str, passed: bool, detail: str = "") -> None:
        self.conditions.append({"study": study, "key": key, "observed": observed, "passed": passed, "detail": detail})
        mark = "PASS" if passed else "FAIL"
        self.line(f"SIM | {study} | {mark} | {key} | {observed} | declared: {PASS_CONDITIONS[key]}" + (f" | {detail}" if detail else ""))

    def verdict(self, study: str) -> bool:
        rows = [row for row in self.conditions if row["study"] == study]
        return bool(rows) and all(row["passed"] for row in rows)


def cell_rng(*parts) -> random.Random:
    """A named, reproducible stream. String seeds hash by SHA-512, not by the salted
    builtin `hash`, so the stream is identical across processes and machines."""
    return random.Random(":".join(str(part) for part in (SEED,) + parts))


def quantile(sorted_values, p: float) -> float:
    """Type-7 linear interpolation, the definition `statistics.quantiles` uses."""
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = p * (len(sorted_values) - 1)
    low = int(math.floor(position))
    high = min(low + 1, len(sorted_values) - 1)
    weight = position - low
    return sorted_values[low] * (1.0 - weight) + sorted_values[high] * weight


def _study_timer(seconds: float = 60.0):
    """Context manager: a 60 s per-study alarm, per 06 section 3.4."""

    class _Timer:
        def __enter__(self):
            signal.signal(signal.SIGALRM, _on_alarm)
            signal.setitimer(signal.ITIMER_REAL, seconds)
            return self

        def __exit__(self, exc_type, exc, tb):
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            if isinstance(exc, StudyTimeout):
                raise
            return False

    return _Timer()


# ---------------------------------------------------------------------------
# G1/G2 generative model: the two-level normal the pooled estimator assumes
#   theta_j ~ N(mu, tau^2),  y_ij | theta_j ~ N(theta_j, sigma^2)
# The estimator sees, per event, the mean of n marks and their sample variance
# (ddof=1, exactly `price_features.mean_log_ratio`), and nothing else.
# ---------------------------------------------------------------------------


def draw_pooled_panel(rng: random.Random, j_events: int, n_marks: int, mu: float, tau: float, sigma: float):
    rows = []
    thetas = []
    for index in range(j_events):
        theta = rng.gauss(mu, tau)
        thetas.append(theta)
        marks = [rng.gauss(theta, sigma) for _ in range(n_marks)]
        mean = sum(marks) / n_marks
        within = sum((value - mean) ** 2 for value in marks) / (n_marks - 1)
        rows.append(
            {
                "eventId": f"sim-e{index}",
                "n": n_marks,
                "meanLogRatio": mean,
                "withinVar": within,
                "startedAtCut": True,
                "completedAtCut": True,
            }
        )
    return rows, thetas


def dl_tau2(rows) -> tuple[float, float]:
    """DerSimonian-Laird exactly as `value_band.pooled` writes it, with no floor.

    Replicated here for one reason only: the shipped function refuses to estimate below
    nine events, and the study needs the estimator's own distribution there to test the
    claim that it is useless. The replication is checked against the shipped branch at
    J >= 9 on every replication (`max_abs_diff` is printed) -- so this is the engine's
    arithmetic, not a second opinion.
    """
    y = [row["meanLogRatio"] for row in rows]
    s2 = [row["withinVar"] / row["n"] for row in rows]
    weights = [1.0 / value for value in s2]
    total = sum(weights)
    weighted_mean = sum(weight * yi for weight, yi in zip(weights, y)) / total
    q = sum(weight * (yi - weighted_mean) ** 2 for weight, yi in zip(weights, y))
    denominator = total - sum(weight * weight for weight in weights) / total
    return (q - (len(rows) - 1)) / denominator, q


def declared_band_log(mu: float, declared_tau: float, face: int = 1_000_000_000) -> tuple[float, float]:
    """The shipped cold-start band, in log units, from the shipped arithmetic.

    `value_band._pooled_only` is the object 02-e 4.7 and the A13_POOLED label describe:
    centre = pooled mean, half-width = z * max(declared tau, TAU_MIN). Face 1e9 keeps the
    lamport rounding below 1e-9 in log units.
    """
    out = value_band._pooled_only(face_lamports=face, mu=mu, tau=declared_tau, n_events=0)
    return math.log(out["band"]["loLamports"] / face), math.log(out["band"]["hiLamports"] / face)


def study_a_and_b(report: Report) -> float:
    t0 = time.perf_counter()
    report.line("")
    report.line("=" * 110)
    report.line("SIM STUDY A+B -- pooled mean and between-event variance recovery; declared-band coverage")
    report.line(
        f"SIM | DGP: theta_j ~ N(mu={MU_TRUE}, tau={TAU_TRUE}^2); y_ij|theta_j ~ N(theta_j, sigma={SIGMA_TRUE}^2); "
        f"n_marks={MARKS_PER_EVENT} per event; rejected truth: none"
    )
    report.line(
        f"SIM | grid: J in {list(J_GRID)} (events) x declared tau in {list(DECLARED_ARMS)}; "
        f"R={R_POOL} replications per cell; seed={SEED}"
    )
    report.line("=" * 110)

    max_dl_diff = 0.0
    coverage_rows: dict[tuple[int, float], dict] = {}

    for j_events in J_GRID:
        rng = cell_rng("A", j_events)
        acc = {
            arm: {"mu": [], "mu_se": [], "tau2": [], "method": [], "cover_declared": 0, "width_declared": [], "cover_pooled": 0, "width_pooled": [], "n": 0}
            for arm in DECLARED_ARMS
        }
        raw_tau2: list[float] = []
        for _ in range(R_POOL):
            rows, _thetas = draw_pooled_panel(rng, j_events, MARKS_PER_EVENT, MU_TRUE, TAU_TRUE, SIGMA_TRUE)
            theta_new = rng.gauss(MU_TRUE, TAU_TRUE)          # a new event's mean, no marks of its own

            shipped = {arm: value_band.pooled(rows=rows, declared_tau=arm) for arm in DECLARED_ARMS}
            # The two arms share the data and differ only in the declared tau. At J >= 9
            # `pooled` estimates tau2 and ignores the declared value in its weights, so the
            # arms differ there only through the band width -- which is exactly how the
            # engine draws it.
            raw, _q = dl_tau2(rows)
            raw_tau2.append(raw)

            for arm in DECLARED_ARMS:
                pool = shipped[arm]
                bucket = acc[arm]
                bucket["mu"].append(pool["mu"])
                bucket["mu_se"].append(math.sqrt(pool["varOfMu"]))
                bucket["tau2"].append(pool["tau2"])
                bucket["method"].append(pool["method"])
                lo, hi = declared_band_log(pool["mu"], arm)
                bucket["width_declared"].append(0.5 * (hi - lo))
                bucket["cover_declared"] += int(lo <= theta_new <= hi)
                half = Z90 * math.sqrt(pool["tau2"] + pool["varOfMu"])
                bucket["width_pooled"].append(half)
                bucket["cover_pooled"] += int(pool["mu"] - half <= theta_new <= pool["mu"] + half)
                bucket["n"] += 1

            if j_events >= ENGINE_SWITCH:
                shipped_tau2 = shipped[DECLARED_ARMS[0]]["tau2"]
                floored = max(raw, 0.0)
                if floored < TAU_MIN_ENGINE ** 2:
                    floored = TAU_MIN_ENGINE ** 2
                max_dl_diff = max(max_dl_diff, abs(floored - shipped_tau2))

        raw_sorted = sorted(raw_tau2)
        raw_mean = sum(raw_tau2) / len(raw_tau2)
        rel_bias_tau = (raw_mean - TAU_TRUE2) / TAU_TRUE2
        share_floor = sum(1 for value in raw_tau2 if value <= TAU_MIN_ENGINE ** 2) / len(raw_tau2)
        p10 = quantile(raw_sorted, 0.10)
        p90 = quantile(raw_sorted, 0.90)

        report.line("")
        report.line(
            f"SIM | A | J={j_events} n_marks={MARKS_PER_EVENT} R={R_POOL} | DGP mu={MU_TRUE} tau={TAU_TRUE} "
            f"sigma={SIGMA_TRUE} | tau2_true={TAU_TRUE2:.4f}"
        )
        report.line(
            f"SIM | A | J={j_events} | tau2_hat (DL, no floor): mean={raw_mean:.4f} rel_bias={rel_bias_tau:+.3f} "
            f"p10={p10:.4f} p50={quantile(raw_sorted, 0.50):.4f} p90={p90:.4f} "
            f"share<=floor({TAU_MIN_ENGINE ** 2:.2f})={share_floor:.3f}"
        )

        for arm in DECLARED_ARMS:
            bucket = acc[arm]
            mus = bucket["mu"]
            mean_mu = sum(mus) / len(mus)
            bias = mean_mu - MU_TRUE
            mc_se = statistics.pstdev(mus) / math.sqrt(len(mus))
            threshold = max(0.01, 4.0 * mc_se)
            mean_v_mu = sum(se * se for se in bucket["mu_se"]) / len(bucket["mu_se"])
            report.line(
                f"SIM | A | J={j_events} declared={arm:.2f} | mu_hat mean={mean_mu:.4f} bias={bias:+.4f} "
                f"mc_se={mc_se:.4f} mean_var_of_mu={mean_v_mu:.4f} | method={sorted(set(bucket['method']))}"
            )
            report.condition(
                "A",
                "A.mu",
                f"J={j_events} declared={arm:.2f} bias={bias:+.4f} threshold={threshold:.4f}",
                abs(bias) <= threshold,
            )

            n = bucket["n"]
            cov_d = bucket["cover_declared"] / n
            cov_p = bucket["cover_pooled"] / n
            report.line(
                f"SIM | B | J={j_events} declared={arm:.2f} | coverage_declared={cov_d:.3f} "
                f"(R={n}) width_declared_log={2 * sum(bucket['width_declared']) / n:.4f} | "
                f"coverage_pooled={cov_p:.3f} width_pooled_log={2 * sum(bucket['width_pooled']) / n:.4f}"
            )

            coverage_rows[(j_events, arm)] = {
                "cov_declared": cov_d,
                "cov_pooled": cov_p,
                "width_pooled": 2 * sum(bucket["width_pooled"]) / n,
            }

            if abs(arm - TAU_TRUE) < 1e-12:
                report.condition(
                    "B",
                    "B.declared_matched",
                    f"J={j_events} declared=0.30 coverage={cov_d:.3f}",
                    0.87 <= cov_d <= 0.93,
                )
            else:
                report.condition(
                    "B",
                    "B.declared_default",
                    f"J={j_events} declared={arm:.2f} coverage={cov_d:.3f}",
                    cov_d < 0.87,
                    detail=f"declared {arm:.2f} is below the true tau {TAU_TRUE}",
                )
            report.condition(
                "B",
                "B.pooled_width",
                f"J={j_events} declared={arm:.2f} coverage={cov_p:.3f}",
                0.87 <= cov_p <= 0.93,
            )

        # Mean over arms is not meaningful for coverage; take the matched arm for the pin test.
        report.condition(
            "A",
            "A.tau_mean",
            f"J={j_events} mean_tau2={raw_mean:.4f} rel_bias={rel_bias_tau:+.3f}",
            abs(rel_bias_tau) <= 0.25,
        )
        if j_events == 20:
            pinned = p10 >= 0.35 * TAU_TRUE2 and p90 <= 2.0 * TAU_TRUE2
            report.condition(
                "A",
                "A.tau_pinned_20",
                f"J=20 p10={p10:.4f} p90={p90:.4f} (0.35x={0.35 * TAU_TRUE2:.4f}, 2.0x={2.0 * TAU_TRUE2:.4f})",
                pinned,
            )
        else:
            unpinned = p90 >= 1.5 * TAU_TRUE2 or p10 <= 0.5 * TAU_TRUE2
            report.condition(
                "A",
                "A.tau_unpinned_small",
                f"J={j_events} p10={p10:.4f} p90={p90:.4f} (1.5x={1.5 * TAU_TRUE2:.4f}, 0.5x={0.5 * TAU_TRUE2:.4f})",
                unpinned,
            )
        limit = 0.30 if j_events == 2 else (0.02 if j_events == 5 else 0.10)
        side = ">=" if j_events < 20 else "<="
        report.condition(
            "A",
            "A.tau_at_floor",
            f"J={j_events} share(raw tau2_hat <= 0.01)={share_floor:.3f} required {side} {limit:.2f}",
            share_floor >= limit if j_events < 20 else share_floor <= limit,
        )

        methods_seen = set()
        for bucket in acc.values():
            methods_seen |= set(bucket["method"])
        if j_events < ENGINE_SWITCH:
            report.condition(
                "A",
                "A.switch",
                f"J={j_events} shipped method over all reps={sorted(methods_seen)}",
                methods_seen <= {"declared"},
            )
        else:
            report.condition(
                "A",
                "A.switch",
                f"J={j_events} shipped method over all reps={sorted(methods_seen)}",
                "declared" not in methods_seen,
            )

    report.line("")
    report.line(
        f"SIM | A | replication check: the harness DL formula reproduces the shipped tau2 (after its floor) "
        f"at J>=9 with max_abs_diff={max_dl_diff:.3e}"
    )
    report.line(
        "SIM | A | canary: the same bias test applied to an estimator shifted by +0.02 log units at J=20 "
        "(the harness must call it a failure)"
    )
    canary_rng = cell_rng("A", "canary")
    shifted = []
    for _ in range(R_POOL):
        rows, _ = draw_pooled_panel(canary_rng, 20, MARKS_PER_EVENT, MU_TRUE, TAU_TRUE, SIGMA_TRUE)
        shifted.append(value_band.pooled(rows=rows, declared_tau=0.20)["mu"] + 0.02)
    canary_bias = sum(shifted) / len(shifted) - MU_TRUE
    canary_se = statistics.pstdev(shifted) / math.sqrt(len(shifted))
    canary_threshold = max(0.01, 4.0 * canary_se)
    report.line(
        f"SIM | A | canary J=20 shifted=+0.02 | bias={canary_bias:+.4f} threshold={canary_threshold:.4f} | "
        f"harness verdict={'FAIL(correct)' if abs(canary_bias) > canary_threshold else 'PASS(broken harness)'}"
    )
    report.condition(
        "A",
        "A.canary",
        f"shifted estimator bias={canary_bias:+.4f} exceeds threshold={canary_threshold:.4f}",
        abs(canary_bias) > canary_threshold,
        detail="a harness that cannot fail is evidence about the author, not the estimator (06 3.1(4))",
    )

    for arm in DECLARED_ARMS:
        widths = [coverage_rows[(j, arm)]["width_pooled"] for j in J_GRID]
        report.condition(
            "B",
            "B.width_shrinks",
            f"declared={arm:.2f} pooled widths J={list(J_GRID)} -> {[round(w, 4) for w in widths]}",
            widths[0] > widths[1] > widths[2],
        )
    declared_widths = [2 * Z90 * max(arm, TAU_MIN_ENGINE) for arm in DECLARED_ARMS]
    report.line(
        f"SIM | B | the declared band's own width does not depend on J: "
        f"{[round(w, 4) for w in declared_widths]} for declared {list(DECLARED_ARMS)}"
    )
    return time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Study C: the path. DGP is the estimator's own model with a ticket fixed effect:
#   y_it = a_i + theta log(1 + d_it) + beta d_it + eps_it,  a_i ~ N(0, w^2)
#   observed  y~_it = min(y_it, c),  c chosen at the (1 - s) quantile of latent y
# The ticket effect differences out of a within-ticket pair, which is the primitive of
# 02-a 4.1; the shipped estimator pools marks in a tier and demeans by the tier mean,
# so the ticket effect stays in as noise there. Both are reported.
# ---------------------------------------------------------------------------


def ols_through_origin(pairs):
    """Two-regressor least squares on within-ticket differences, no intercept.

    The ticket fixed effect and the event intercept both vanish in the difference, so
    there is nothing to demean by: solve [Suu Sud; Sud Sdd][theta beta]' = [Suy Sdy]'.
    """
    s_uu = s_ud = s_dd = s_uy = s_dy = 0.0
    for du, dd, dy in pairs:
        s_uu += du * du
        s_ud += du * dd
        s_dd += dd * dd
        s_uy += du * dy
        s_dy += dd * dy
    delta = s_uu * s_dd - s_ud * s_ud
    if delta <= 1e-15:
        return None
    theta = (s_dd * s_uy - s_ud * s_dy) / delta
    return theta


def draw_path_event(rng: random.Random, sigma: float, cap_share, window, n_tickets: int = PATH_TICKETS):
    """One event: `n_tickets` tickets, two sale instants each, latent path plus a cap."""
    days_lo, days_hi = window
    latent = []  # (ticket index, day pair, y pair)
    for _ in range(n_tickets):
        a = rng.gauss(0.0, TICKET_SD)
        first = rng.uniform(days_lo, days_hi)
        gap = rng.uniform(3.0, min(12.0, first - 1.0))
        second = max(1.0, first - gap)
        d1, d2 = first, second
        y1 = a + THETA_TRUE * math.log(1.0 + d1) + BETA_TRUE * d1 + rng.gauss(0.0, sigma)
        y2 = a + THETA_TRUE * math.log(1.0 + d2) + BETA_TRUE * d2 + rng.gauss(0.0, sigma)
        latent.append((d1, d2, y1, y2))

    cap = None
    if cap_share is not None:
        values = sorted([y1 for _, _, y1, _ in latent] + [y2 for _, _, _, y2 in latent])
        cap = quantile(values, 1.0 - cap_share)

    marks = []
    pairs = []
    oracle_pairs = []
    clipped_marks = 0
    clipped_pairs = 0
    for d1, d2, y1, y2 in latent:
        o1, o2 = (y1, y2) if cap is None else (min(y1, cap), min(y2, cap))
        clipped_marks += int(cap is not None and (y1 > cap)) + int(cap is not None and (y2 > cap))
        clipped_pairs += int(cap is not None and (y1 > cap or y2 > cap))
        du = math.log(1.0 + d1) - math.log(1.0 + d2)
        dd = d1 - d2
        pairs.append((du, dd, o1 - o2))
        oracle_pairs.append((du, dd, y1 - y2))
        for day, observed, is_clipped in ((d1, o1, cap is not None and y1 > cap), (d2, o2, cap is not None and y2 > cap)):
            marks.append(
                {
                    "ticketId": f"sim-t{len(marks)}",
                    "priceLamports": max(1, int(round(1_000_000_000 * math.exp(observed)))),
                    "daysToEvent": day,
                    "atCeiling": bool(is_clipped),
                    "tierFaceLamports": 1_000_000_000,
                }
            )
    marks.sort(key=lambda mark: -mark["daysToEvent"])
    return marks, pairs, oracle_pairs, cap, clipped_marks / (2 * n_tickets), clipped_pairs / n_tickets


def path_features(marks, cap):
    face = 1_000_000_000
    days = [mark["daysToEvent"] for mark in marks]
    at_ceiling = sum(1 for mark in marks if mark["atCeiling"])
    cap_bps = None if cap is None else int(round((math.exp(cap) - 1.0) * 10000))
    return {
        "eventId": "sim-evt",
        "capBpsRecorded": cap_bps,
        "tiers": [
            {
                "tierId": "t",
                "name": "T",
                "faceValueLamports": face,
                "totalSupply": 100,
                "issuedCount": 50,
                "sellThrough": 0.5,
                "capBpsRecorded": cap_bps,
                "capCeilingLamportsRecorded": None if cap_bps is None else face * (10000 + cap_bps) // 10000,
                "marks": marks,
                "atCeilingCount": at_ceiling,
                "belowCeilingCount": len(marks) - at_ceiling,
                "highestRecordedLamports": max(mark["priceLamports"] for mark in marks),
                "lowestRecordedLamports": min(mark["priceLamports"] for mark in marks),
                "exposureTicketDays": 100.0,
                "ticketsNotIssuedAtCut": 0,
                "timeSpreadDays": max(days) - min(days),
                "exits": {"sale": len(marks), "transfer": 0, "redeem": 0, "revoke": 0},
            }
        ],
    }


def post_run_diagnostic(report: Report) -> None:
    """POST-RUN DIAGNOSTIC. Added after the first full run, to locate the sign of the cap
    bias that `C.cap_direction` reported. It changes no pass condition, adds no verdict,
    and is printed so the explanation is reproducible by running this file."""
    report.line("")
    report.line(
        "SIM | C | POST-RUN DIAGNOSTIC (added after the first run; no pass condition changed) | "
        "noiseless latent path y = theta log(1+d), theta=0.30, d on a grid over [5, 60]"
    )
    days = [5.0 + index * 0.25 for index in range(221)]
    us = [math.log(1.0 + day) for day in days]
    latent = [THETA_TRUE * value for value in us]
    true_drop = latent[-1] - latent[0]
    for share in (0.10, 0.25, 0.40, 0.70):
        cap = quantile(sorted(latent), 1.0 - share)
        observed = [min(value, cap) for value in latent]
        n = len(days)
        y_bar = sum(observed) / n
        d_bar = sum(days) / n
        u_bar = sum(us) / n
        yt = [value - y_bar for value in observed]
        dt = [value - d_bar for value in days]
        ut = [value - u_bar for value in us]
        s_dd = sum(a * a for a in dt)
        s_du = sum(a * b for a, b in zip(dt, ut))
        s_uu = sum(b * b for b in ut)
        s_dy = sum(a * y for a, y in zip(dt, yt))
        s_uy = sum(b * y for b, y in zip(ut, yt))
        delta = s_dd * s_uu - s_du * s_du
        theta_hat = (s_dd * s_uy - s_du * s_dy) / delta
        beta_hat = (s_uu * s_dy - s_du * s_uy) / delta
        drop_omega0 = theta_hat * (math.log(61.0) - math.log(6.0))
        drop_omega1 = drop_omega0 + beta_hat * 55.0
        report.line(
            f"SIM | C | POST-RUN DIAGNOSTIC | s={share:.2f} c={cap:.4f} theta_hat={theta_hat:.4f} beta_hat={beta_hat:+.5f} | "
            f"observed end-to-end drop={observed[-1] - observed[0]:.4f} vs latent {true_drop:.4f} | "
            f"fitted drop omega=0 {drop_omega0:.4f}, omega=1 {drop_omega1:.4f}, truth {true_drop:.4f}"
        )

    for window in ((5.0, 60.0), (40.0, 60.0)):
        n = 200
        ds = [window[0] + index * (window[1] - window[0]) / (n - 1) for index in range(n)]
        nu = [math.log(1.0 + day) for day in ds]
        d_bar = sum(ds) / n
        u_bar = sum(nu) / n
        dt = [day - d_bar for day in ds]
        ut = [value - u_bar for value in nu]
        s_dd = sum(value * value for value in dt)
        s_du = sum(a * b for a, b in zip(dt, ut))
        s_uu = sum(value * value for value in ut)
        delta = s_dd * s_uu - s_du * s_du
        mean_d = d_bar
        mean_u = u_bar
        cov = sum(a * b for a, b in zip(dt, ut)) / n
        sd_d = math.sqrt(s_dd / n)
        sd_u = math.sqrt(s_uu / n)
        report.line(
            f"SIM | C | POST-RUN DIAGNOSTIC | design window {window}: corr(d, log(1+d))={cov / (sd_d * sd_u):.6f}, "
            f"theta variance factor S_dd/delta={s_dd / delta:.6f} per unit residual variance"
        )


def study_c(report: Report) -> float:
    t0 = time.perf_counter()
    report.line("")
    report.line("=" * 110)
    report.line("SIM STUDY C -- the path estimator: recovery of theta from within-ticket first differences, with the cap binding")
    report.line(
        f"SIM | DGP: y_it = a_i + theta*log(1+d) + beta*d + eps; a_i ~ N(0, {TICKET_SD}^2); eps ~ N(0, sigma^2); "
        f"theta={THETA_TRUE} beta={BETA_TRUE}; {PATH_TICKETS} tickets x 2 observations; "
        f"cap c at the (1-s) quantile of latent y, observed y~ = min(y, c)"
    )
    report.line(f"SIM | grid: {len(PATH_CELLS)} cells x R={R_PATH} replications; seed={SEED}")
    report.line("=" * 110)

    cell_stats = {}
    for label, sigma, cap_share, window in PATH_CELLS:
        rng = cell_rng("C", label)
        theta_diff = []
        theta_shipped = []
        theta_oracle = []
        reasons: dict[str, int] = {}
        cap_mass = []
        pair_clip = []
        caps = []
        for _ in range(R_PATH):
            marks, pairs, oracle_pairs, cap, mass, pair_share = draw_path_event(rng, sigma, cap_share, window)
            cap_mass.append(mass)
            pair_clip.append(pair_share)
            caps.append(cap)
            estimate = ols_through_origin(pairs)
            theta_diff.append(estimate if estimate is not None else float("nan"))
            oracle = ols_through_origin(oracle_pairs)
            theta_oracle.append(oracle if oracle is not None else float("nan"))
            out = path_model.estimate(features=path_features(marks, cap), tier_id="t", anchor_lamports=1_000_000_000)
            reasons[out["reason"] or "fitted"] = reasons.get(out["reason"] or "fitted", 0) + 1
            theta_shipped.append(out["theta"] if out["fitted"] and out["theta"] is not None else float("nan"))

        def stats(values):
            usable = [value for value in values if value == value]
            if not usable:
                return float("nan"), float("nan")
            mean = sum(usable) / len(usable)
            return mean, math.sqrt(sum((v - mean) ** 2 for v in usable) / len(usable))

        def fmt(value):
            return "-" if value != value else f"{value:.4f}"

        mean_d, rmse_d = stats(theta_diff)
        mean_s, rmse_s = stats(theta_shipped)
        mean_o, rmse_o = stats(theta_oracle)
        cell_stats[label] = {
            "mean_d": mean_d,
            "rmse_d": rmse_d,
            "mean_s": mean_s,
            "rmse_s": rmse_s,
            "mean_o": mean_o,
            "reasons": reasons,
            "cap_mass": sum(cap_mass) / len(cap_mass),
            "pair_clip": sum(pair_clip) / len(pair_clip),
            "cap_mean": None if cap_share is None else sum(caps) / len(caps),
            "cap_share": cap_share,
            "sigma": sigma,
            "window": window,
        }
        report.line("")
        report.line(
            f"SIM | C | cell={label} sigma={sigma} s={cap_share} window={window} R={R_PATH} | "
            f"DGP theta={THETA_TRUE} beta={BETA_TRUE} ticket_sd={TICKET_SD}"
        )
        report.line(
            f"SIM | C | cell={label} | observed cap mass={sum(cap_mass) / len(cap_mass):.3f} "
            f"share of ticket pairs with >=1 clipped end={sum(pair_clip) / len(pair_clip):.3f} "
            f"mean c={'-' if cell_stats[label]['cap_mean'] is None else format(cell_stats[label]['cap_mean'], '.4f')}"
        )
        report.line(
            f"SIM | C | cell={label} | theta_hat_diff mean={mean_d:.4f} bias={mean_d - THETA_TRUE:+.4f} rmse={rmse_d:.4f} | "
            f"theta_hat_shipped mean={fmt(mean_s)} bias={fmt(mean_s - THETA_TRUE)} rmse={fmt(rmse_s)} | "
            f"latent_oracle bias={mean_o - THETA_TRUE:+.4f} | shipped reasons={reasons}"
        )

        if cap_share is None and abs(sigma - 0.02) < 1e-12:
            report.condition(
                "C",
                "C.diff_uncapped",
                f"cell={label} bias(theta_diff)={mean_d - THETA_TRUE:+.4f} rmse={rmse_d:.4f}",
                abs(mean_d - THETA_TRUE) <= 0.01,
            )
        if cap_share is None and abs(sigma - 0.10) < 1e-12:
            report.condition(
                "C",
                "C.diff_noisy",
                f"cell={label} bias(theta_diff)={mean_d - THETA_TRUE:+.4f}",
                abs(mean_d - THETA_TRUE) <= 0.02,
            )
        if cap_share is not None:
            report.condition(
                "C",
                "C.oracle",
                f"cell={label} bias(latent oracle)={mean_o - THETA_TRUE:+.4f}",
                abs(mean_o - THETA_TRUE) <= 0.01,
            )

    # Direction and magnitude of the attenuation, read off the low-noise cap ladder.
    ladder = ["uncapped_low_noise", "cap10_low_noise", "cap40_low_noise", "cap70_low_noise"]
    means = [cell_stats[label]["mean_d"] for label in ladder]
    report.line("")
    ladder_text = " -> ".join(
        "s={:.2f}:{:.4f}".format(
            cell_stats[label]["cap_share"] if cell_stats[label]["cap_share"] is not None else 0.0,
            cell_stats[label]["mean_d"],
        )
        for label in ladder
    )
    report.line("SIM | C | attenuation ladder (theta_hat_diff, low noise): " + ladder_text)
    monotone = all(means[i] > means[i + 1] for i in range(len(means) - 1))
    below = all(cell_stats[label]["mean_d"] < THETA_TRUE for label in ladder[1:])
    report.condition(
        "C",
        "C.cap_direction",
        f"means={[round(value, 4) for value in means]} strictly_decreasing={monotone} all_below_truth={below}",
        monotone and below,
    )
    attenuation_40 = 1.0 - cell_stats["cap40_low_noise"]["mean_d"] / THETA_TRUE
    attenuation_70 = 1.0 - cell_stats["cap70_low_noise"]["mean_d"] / THETA_TRUE
    report.condition(
        "C",
        "C.cap_magnitude",
        f"relative attenuation at s=0.40: {attenuation_40:.3f}; at s=0.70: {attenuation_70:.3f}",
        attenuation_40 >= 0.10 and attenuation_70 >= 0.30,
    )
    guard_70 = cell_stats["cap70_low_noise"]["reasons"].get("cap_mass_dominates", 0) / R_PATH
    guard_40 = cell_stats["cap40_low_noise"]["reasons"].get("cap_mass_dominates", 0) / R_PATH
    guard_10 = cell_stats["cap10_low_noise"]["reasons"].get("cap_mass_dominates", 0) / R_PATH
    guard_0 = cell_stats["uncapped_low_noise"]["reasons"].get("cap_mass_dominates", 0) / R_PATH
    report.condition(
        "C",
        "C.guard",
        f"cap_mass_dominates share: s=0.70 {guard_70:.3f}, s=0.40 {guard_40:.3f}, s=0.10 {guard_10:.3f}, uncapped {guard_0:.3f}",
        abs(guard_70 - 1.0) < 1e-12 and guard_40 == 0.0 and guard_10 == 0.0 and guard_0 == 0.0,
    )
    post_run_diagnostic(report)
    return time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    started = time.process_time()
    print("SIM -- estimator-property study. Simulation only: no ticket data, no fixture, no market claim.")
    print(f"SIM | seed={SEED} | python={sys.version.split()[0]} | stdlib only (D2)")
    print(f"SIM | start={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")

    report = Report()
    runtimes = {}
    for name, fn in (("A+B", study_a_and_b), ("C", study_c)):
        try:
            with _study_timer(60.0):
                runtimes[name] = fn(report)
        except StudyTimeout:
            report.line(f"SIM | {name} | TIMEOUT after 60 s -- reported as a failure, not as a null result")
            runtimes[name] = 60.0
            report.condition(name[0], f"{name[0]}.timeout", "study exceeded its 60 s alarm", False)

    print("")
    print("=" * 110)
    print("SIM | VERDICTS")
    overall = True
    for study, label in (
        ("A", "A  pooled mu and tau2 recovery"),
        ("B", "B  declared-band coverage"),
        ("C", "C  path theta from within-ticket differences"),
    ):
        passed = report.verdict(study)
        overall = overall and passed
        failed = []
        for row in report.conditions:
            if row["study"] == study and not row["passed"] and row["key"] not in failed:
                failed.append(row["key"])
        print(f"SIM | {label}: {'PASS' if passed else 'FAIL'}" + (f" | failed: {', '.join(failed)}" if failed else ""))
    total = len(report.conditions)
    held = sum(1 for row in report.conditions if row["passed"])
    print(f"SIM | conditions: {held}/{total} held")
    elapsed = time.perf_counter() - report.started
    print(f"SIM | runtime: A+B {runtimes.get('A+B', 0.0):.2f} s, C {runtimes.get('C', 0.0):.2f} s, total wall {elapsed:.2f} s")
    print(f"SIM | cpu time {time.process_time() - started:.2f} s")
    print("")
    print("SIM | WHAT THIS PROVES: that each shipped estimator does what its finding says it does when the")
    print("SIM | generative model is the estimator's own assumption -- bias, dispersion, coverage, the")
    print("SIM | nine-event switch, the cap-mass guard, and the size and sign of the truncation bias.")
    print("SIM | WHAT IT DOES NOT PROVE: anything about ticket markets. The DGP was written from the")
    print("SIM | estimator's assumptions, so a pass cannot detect a wrong assumption. No number here is an")
    print("SIM | accuracy claim about tickets, and none is evidence that real prices look like this.")
    print("=" * 110)
    return 0 if overall else 0  # a failed study is a result, not a crash


if __name__ == "__main__":
    raise SystemExit(main())
