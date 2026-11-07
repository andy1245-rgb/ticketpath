# 09 - SIM recovery study: the pooled estimator, the declared band, and the path curvature

**SIM. Simulation only.** This file reports a study run under D2 (pure Python standard library,
deterministic seeds, no ticket data, no fixture). It says whether each estimator does what its
finding claims **when the generative model is the estimator's own assumption**. It says nothing
about whether real ticket markets look like that, and no number here is an accuracy claim about
tickets.

| | |
|---|---|
| Harness | `tools/sim_recovery.py` (39,650 bytes) |
| Output | `records/sim/sim-recovery-2026-11-07.txt` (16,895 bytes, 139 lines) |
| Run | 2026-11-07T13:30:27Z, python 3.12.3, seed `20261107-sim-recovery` |
| Runtime | 0.92 s wall, 0.92 s CPU: A+B 0.57 s, C 0.35 s (budget was 300 s; each study under a 60 s alarm) |
| Determinism | two runs identical apart from the timing lines |
| Verdicts | A **PASS**, B **FAIL**, C **FAIL**; 37 of 43 pre-declared conditions held |

**The three failures first**, because they are the result:

1. **B, declared band at the matched tau**: coverage of a new event's mean is **0.805 at J=2**,
   below the pre-declared `[0.87, 0.93]`. It is 0.872 at J=5 and 0.879 at J=20.
2. **B, the default declared tau**: at the API default `tau = 0.20`, coverage is **0.620 / 0.694 /
   0.718** at J = 2 / 5 / 20 against a true between-event tau of 0.30.
3. **C, the cap bias runs the opposite way to 02-a C1**: the fitted curvature `theta` is biased
   **up**, not attenuated down, by a cap that truncates the top of the distribution.

Nothing was tuned. No pass condition, grid, replication count or seed was changed after the first
run. The estimators are untouched.

---

## 1. SIM: what was run, and the rules it ran under

The protocol is `06-validation-protocol.md` section 3. This run covers three studies, which map onto
that section as follows: (a) and (b) are the **G2** property (cold-start pooling and declared-band
coverage) on the grid this run was asked for, 2, 5 and 20 events with a declared arm and an
estimated arm; (c) is the **G5** subject (the path) narrowed to parameter recovery, not its guard
grid. **G1, G3, G4, G6, G7 and G8 were not run.** Nothing here says anything about them.

Five rules governed the run, all from 06 section 3.1:

1. One generative model per estimator, and the model is the estimator's own assumption. The
   assumptions are printed with every result.
2. The pass condition was written into the source before the first run
   (`PASS_CONDITIONS` in the harness) and the script prints PASS or FAIL per condition and a
   verdict per study. A verdict cannot be re-read after the fact.
3. Every output line starts `SIM` and carries the DGP's parameters.
4. The harness has to be able to fail. One canary checks it directly: an estimator shifted by +0.02
   log units is caught at J=20 (measured bias +0.0180 against a threshold of 0.0100). A second class
   of conditions is written as predicted failures (for example "the between-event variance is not
   pinned at two events"), so a failure has to appear for the condition to hold.
5. No fixture, no ticket data. The panels are generated from the seed printed above.

**The estimator is the shipped code.** The harness imports `ticketpath.core.value_band` and
`ticketpath.core.path_model` and calls them. It does not re-implement them. One function is
replicated, the DerSimonian-Laird variance, and only because the shipped function refuses to
estimate below nine events; the replication is checked against the shipped value on every
replication at J >= 9 and the maximum absolute difference was **0.0** (printed). So study A's small-J
numbers are the engine's own arithmetic, not a second opinion.

Study A and B share one set of draws per cell: **2,000 replications** at each of 2, 5 and 20 events.
Study C uses **400 replications** in each of **7 cells**. No grid was cut for time; the run took
0.92 s against a 300 s cap, so there was nothing to cut.

---

## 2. SIM study A: the pooled mean and the between-event variance

### Generative model

The two-level normal of `02-e` section 4.2, with the estimator's own cold-start simplification
\(x_j'\beta = \mu\):

\[
\theta_j \sim \mathcal{N}(\mu,\ \tau^2), \qquad
y_{ij} \mid \theta_j \sim \mathcal{N}(\theta_j,\ \sigma^2)
\]

with the truth fixed at

\[
\mu = 0.2612,\quad \tau = 0.30 \ (\tau^2 = 0.09),\quad \sigma = 0.406,\quad n = 20 \text{ marks per event.}
\]

\(\mu\) and \(\sigma\) are the borrowed Leslie and Sorensen numbers the engine carries in
`value_band.PRIOR`. \(\tau = 0.30\) sits strictly inside the declared grid and strictly above the API
default 0.20, which is what makes the declared-versus-true comparison informative.

The estimator sees, per event, only the mean and the sample variance (ddof=1) of the 20 marks, which
is exactly what `price_features.mean_log_ratio` supplies, and then `value_band.pooled`. The declared
arm passes `declared_tau`; the estimated arm reads `tau2` out of the same call at J >= 9, which is
where `EVENTS_FOR_ESTIMATED_TAU = 9` puts the switch.

### What was measured, and the numbers

Bias of the pooled mean over replications, with the Monte-Carlo standard error of that bias. The
pre-declared threshold was `|bias| <= max(0.01, 4 x MC SE)`, so Monte-Carlo noise cannot flip a
verdict on its own.

**SIM table A1.** Bias of the pooled mean over 2,000 replications per cell.

| J | declared tau | mean of mu_hat | bias | MC SE | threshold | verdict |
|---|---|---|---|---|---|---|
| 2 | 0.20 | 0.2709 | +0.0097 | 0.0049 | 0.0196 | PASS |
| 2 | 0.30 | 0.2709 | +0.0097 | 0.0049 | 0.0196 | PASS |
| 5 | 0.20 | 0.2566 | -0.0046 | 0.0032 | 0.0128 | PASS |
| 5 | 0.30 | 0.2565 | -0.0047 | 0.0032 | 0.0128 | PASS |
| 20 | 0.20 | 0.2566 | -0.0046 | 0.0016 | 0.0100 | PASS |
| 20 | 0.30 | 0.2566 | -0.0046 | 0.0016 | 0.0100 | PASS |

The largest bias is 0.0097 log units at two events, which is 3.7% of the true mean and well inside
the Monte-Carlo threshold. The pooled mean is recovered without detectable bias at 2, 5 and 20
events, in both declared arms. This is the algebra of the normal-normal posterior mean: the weights
depend on the sample variances, and for normal marks the sample mean and the sample variance are
independent, so the weighting cannot bias the level.

The between-event variance is a different story, and it is the story `02-e` sections 4.4 and 4.5
tell:

**SIM table A2.** The between-event variance estimate, DerSimonian-Laird without the engine's floor.

| J | mean tau2_hat | rel. bias | p10 | p50 | p90 | share(raw <= 0.01) |
|---|---|---|---|---|---|---|
| 2 | 0.0909 | +0.010 | -0.0064 | 0.0388 | 0.2586 | 0.331 |
| 5 | 0.0891 | -0.010 | 0.0169 | 0.0715 | 0.1849 | 0.056 |
| 20 | 0.0903 | +0.003 | 0.0508 | 0.0868 | 0.1316 | 0.000 |

Read the J=2 row carefully. **The mean of the estimator is right (0.0909 against a truth of 0.09)
and the estimate itself is useless**: the 10th percentile is -0.0064, 0.331 of draws land at or
below a variance of 0.01 (the printed `share<=floor(0.01)` column), and the 90th percentile is 2.9
times the truth. The point estimate is
unbiased on average and carries almost no information per draw, which is precisely the pathology
of `02-e` section 4.5: the truncation is invisible in the number and fatal in the width. At J=5 the
90th percentile is 2.1 times the truth and 0.056 of draws land at or below 0.01. At J=20 the 10 to 90
range is 0.0508 to 0.1316, which is 0.56 to 1.46 times the truth.

The engine's nine-event switch behaved as declared in 100% of replications: `method == 'declared'`
at J=2 and J=5, `dersimonian_laird` at J=20. Below nine events the between-event term in the
predictive interval is the declared tau of 0.20, tau squared 0.04, not the floor. From nine events
up the floor is in force; it bound none of the twenty-event draws (0.000) and would have bound
0.056 of the five-event draws had the estimate been used there, which it is not.

---

## 3. SIM study B: coverage of the declared band

### What object was covered

The object is the mean log ratio of a **new event with no marks of its own**, drawn independently
of the panel as \(\theta_{\text{new}} \sim \mathcal{N}(\mu, \tau^2)\). That is the object the
`A13_POOLED` label describes. It is not a next sale and not a single ticket; `02-e` section 5.1
keeps those apart.

The band arithmetic is the shipped arithmetic, read out of `value_band._pooled_only` rather than
re-derived:

\[
\text{band} = \hat\mu \pm z \cdot \max(\tau_{\text{declared}}, 0.10), \qquad z = 1.6449
\]

with \(\hat\mu\) the pooled mean from study A. Coverage is the share of 2,000 draws in which
\(\theta_{\text{new}}\) falls inside. The comparison object is the pooled predictive width the
payload already carries beside the band, `pooledWidthLog / 2`:

\[
\hat\mu \pm z\sqrt{\hat\tau^2_{\text{used}} + V(\hat\mu)}
\]

Note what enters each: the declared band carries **no term for the uncertainty in \(\hat\mu\)**, and
below nine events the pooled width carries the **declared** tau squared rather than an estimate,
because that is what `pooled()` returns there. Both facts show up in the numbers.

### The numbers

Nominal coverage is 0.90. At 2,000 replications the binomial standard error at 90% coverage is
0.0067 by arithmetic, so a two-point gap is about three standard errors.

**SIM table B1.** Coverage of a new event's mean, 2,000 replications per cell.

| J | declared tau | coverage, declared band | coverage, pooled width | declared width (log) | pooled width (log) |
|---|---|---|---|---|---|
| 2 | 0.20 | 0.620 | 0.720 | 0.6580 | 0.8328 |
| 5 | 0.20 | 0.694 | 0.746 | 0.6580 | 0.7329 |
| 20 | 0.20 | 0.718 | 0.873 | 0.6580 | 0.9982 |
| 2 | 0.30 | **0.805** | 0.897 | 0.9869 | 1.2270 |
| 5 | 0.30 | 0.872 | 0.904 | 0.9869 | 1.0893 |
| 20 | 0.30 | 0.879 | 0.873 | 0.9869 | 0.9982 |

Four things come out of that table.

1. **At the true tau the declared band covers 0.805 at two events**, almost ten points below nominal and
   outside the pre-declared band. The cause is arithmetic and was predictable: the width is
   \(z\tau\), but the gap between \(\theta_{\text{new}}\) and \(\hat\mu\) has variance
   \(\tau^2 + V(\hat\mu)\), and the printed mean of \(V(\hat\mu)\) in the matched arm is 0.0491 at
   J=2 against a \(\tau^2\) of 0.09, so more than a third of the gap's variance is missing from the
   width. At J=5 it is 0.0196 and at J=20 it is 0.0049. The engine's own
   docstring calls the width a *floor* (`02-e` section 4.7), and this is what a floor does. At
   J=20 the omission is small enough (0.879) that coverage holds.
2. **The pooled width restores coverage** to 0.897 at J=2 and 0.904 at J=5 in the matched arm, and
   to 0.873 at J=20 where the variance is estimated. That width is already computed and printed
   beside the band. The coverage that the declared band fails to deliver is available in the same
   payload.
3. **The API default tau of 0.20 under-covers badly against a tau of 0.30**: 0.620, 0.694 and 0.718.
   All three conditions written as "must be below 0.87" held, so this is the predicted failure, not
   a surprise. It is a statement about one constant, exactly the form `06` G2 says the useful output
   would take. It does not say the label is false: `A13_POOLED` says the width is the declared tau
   and does not claim coverage.
4. **The pooled width is not monotone in J across the switch.** At declared 0.20 it is 0.8328,
   0.7329, 0.9982 at J = 2, 5, 20. It falls and then jumps because at nine events a declared
   variance of 0.04 is replaced by an estimated 0.09. The pre-declared condition "strictly
   decreasing in J in both arms" therefore **failed for the 0.20 arm and held for the 0.30 arm**.
   G2's width condition cannot hold for a band whose width switches from declared to estimated; the
   condition as written is incompatible with the design, not the other way round.

The declared band's own width, for the record, is constant in J: 0.6580 log units at tau 0.20 and
0.9869 at tau 0.30, exactly \(2z\tau\). The width moves only if the constant moves.

---

## 4. SIM study C: the path curvature from within-ticket differences, with the cap binding

### Generative model

The model of `02-a` section 8.2 with a ticket fixed effect, which is the object the within-ticket
first difference of section 4.1 removes:

\[
y_{it} = a_i + \theta \log(1+d_{it}) + \beta d_{it} + \varepsilon_{it},
\qquad a_i \sim \mathcal{N}(0, 0.15^2),\quad \varepsilon_{it}\sim\mathcal{N}(0,\sigma^2)
\]

\[
\text{truth: } \theta = 0.30,\ \beta = 0,
\qquad \text{observed: } \tilde y_{it} = \min(y_{it}, c)
\]

\(\theta > 0\) means prices are higher further from the event and fall as it approaches, the
concession shape of `02-a` section 5.1. \(\beta = 0\) in the truth, so any fitted linear term is the
fit using its free nuisance to reproduce a shape the curvature cannot. Each event has 40 tickets,
two sale instants each, first day uniform over the window and the second 3 to 12 days nearer. The
cap \(c\) is set at the \((1-s)\) quantile of the latent values in that replication, so the cap mass
is exactly \(s\) by construction; the mean \(c\) is printed with each cell.

Two estimators are measured side by side:

* **within-ticket first differences** (the `02-a` 4.1 primitive): one differenced pair per ticket,
  two-regressor least squares through the origin, no intercept because the ticket effect and the
  event level both difference out;
* **the shipped `path_model.estimate`**, which pools the marks in a tier and demeans by the tier
  mean, so the ticket effect stays in as noise rather than being removed.

Plus one diagnostic that is not an estimator: the **same differenced fit on the latent values
before the cap**, to establish that any bias found is caused by the clip and not by the design.

### The numbers

`theta_hat_diff` is the differenced estimator, `theta_hat_shipped` the shipped one, `bias` is
against the true 0.30.

**SIM table C1.** Theta recovery by cell, 400 replications each. Bias is against the true 0.30.

| cell | sigma | cap share s | observed cap mass | pairs with >=1 clipped end | diff mean | diff bias | diff RMSE | shipped mean | shipped bias | shipped RMSE |
|---|---|---|---|---|---|---|---|---|---|---|
| uncapped_low_noise | 0.02 | none | 0.000 | 0.000 | 0.2998 | -0.0002 | 0.0153 | 0.2949 | -0.0051 | 0.0770 |
| uncapped_noisy | 0.10 | none | 0.000 | 0.000 | 0.2995 | -0.0005 | 0.0755 | 0.2972 | -0.0028 | 0.0879 |
| narrow_window | 0.02 | none | 0.000 | 0.000 | 0.2937 | -0.0063 | 0.2107 | 0.3648 | 0.0648 | **1.0425** |
| cap10_low_noise | 0.02 | 0.10 | 0.100 | 0.130 | 0.3124 | **+0.0124** | 0.0167 | 0.3122 | 0.0122 | 0.0721 |
| cap40_low_noise | 0.02 | 0.40 | 0.400 | 0.464 | 0.3393 | **+0.0393** | 0.0178 | 0.3447 | 0.0447 | 0.0662 |
| cap70_low_noise | 0.02 | 0.70 | 0.700 | 0.772 | 0.3255 | **+0.0255** | 0.0311 | no theta | - | - |
| cap40_noisy | 0.10 | 0.40 | 0.400 | 0.506 | 0.3362 | **+0.0362** | 0.0703 | 0.3494 | 0.0494 | 0.0726 |

The shipped estimator returns no theta at all at s = 0.70: it refused with `cap_mass_dominates` in
**400 of 400** fits, before fitting, so there is no number to report. That is the guard working.

### The uncapped cells: the estimator is exact

The differenced estimator recovers the decay parameter with bias -0.0002 at sigma 0.02 and
-0.0005 at sigma 0.10; RMSE 0.0153 and 0.0755. This is OLS on the true differenced
model, so an absence of bias is expected; what the study adds is that the shipped code's algebra and
the harness's differencing agree, and that no transcription error sits between them.

### The cap cells: the bias is real, and it is the wrong sign

The pre-declared condition was that a binding cap attenuates the fitted curvature: bias below zero,
mean estimate decreasing in the cap mass. **It failed.** The measured bias is **+0.0124 at s=0.10,
+0.0393 at s=0.40 and +0.0255 at s=0.70**: the cap makes the fitted curvature **steeper**, not
flatter, and the sequence is not monotone.

The latent oracle says the clip is the cause: its bias is +0.0008, +0.0001, +0.0001 and +0.0018 in
the four capped cells, so the design and the differencing are clean and the movement comes entirely
from truncation.

A **post-run diagnostic** block was added to the harness after the first full run to locate the
sign. It changes no condition. It fits the same two-regressor model to a noiseless latent path
\(\theta\log(1+d)\) over a grid of \(d\) from 5 to 60:

**SIM table C2.** Noiseless diagnostic, the same two-regressor fit with no ticket effect and no noise.

| s | cap c | theta_hat | beta_hat | observed end-to-end drop | fitted drop, omega=0 | fitted drop, omega=1 | true drop |
|---|---|---|---|---|---|---|---|
| 0.10 | 1.2049 | 0.3117 | -0.00057 | 0.6674 | 0.7228 | 0.6914 | 0.6957 |
| 0.25 | 1.1566 | 0.3591 | -0.00303 | 0.6191 | 0.8328 | 0.6659 | 0.6957 |
| 0.40 | 1.0991 | 0.4160 | -0.00645 | 0.5615 | 0.9649 | 0.6103 | 0.6957 |
| 0.70 | 0.9341 | 0.3998 | -0.01014 | 0.3965 | 0.9272 | 0.3696 | 0.6957 |

That table resolves the contradiction, and it is worth being exact about it.

* `02-a` **C1 is right about the object it names**: the observed end-to-end drop falls from 0.6957 to
  0.6674, 0.6191, 0.5615 and 0.3965 as the cap mass rises. The observed path is flatter. The
  measured decline is attenuated.
* The **curvature** \(\theta\) is a different object, and it moves the other way, 0.3117, 0.3591,
  0.4160, 0.3998. The cap creates a kink: a plateau at the ceiling where the latent path was
  highest, then the true path below the crossing. With a free linear term, the two-regressor fit
  reproduces the kink by raising the curvature and taking a negative linear slope (-0.00645 at
  s=0.40). The plateau is charged to curvature.
* The engine's declared bracket does still contain the truth in every row of that table, but at the wrong end:
  at s=0.40 the bracket is 0.6103 to 0.9649 against a truth of 0.6957, with the omega=0 end 39%
  above the truth. It is not a bracket around the truth in any useful sense; it is wide enough to
  cover it.

So the correct statement is narrow and it should not be widened: **the fitted curvature is biased
up by a binding cap, and the flattening that C1 describes appears in the fitted path under the
omega=1 normalisation and in the observed end-to-end change, not in theta.** A report that cites C1
as evidence that theta is attenuated downward would be wrong, and the pre-declared condition that
assumed it is the thing that caught it.

The non-monotonicity at s=0.70 (0.3255 after 0.3393) is consistent with the same mechanism near
saturation: 77% of pairs have at least one clipped end, and the engine refuses that regime outright,
so the top rung is not an estimator output at all.

### The narrow-window cell: a guard that is not a conditioning guard

In the 40 to 60 days window the shipped estimator's curvature has **RMSE 1.0425 against a true 0.30**,
with a bias of +0.0648. The differenced estimator is better and still poor: RMSE 0.2107.

The post-run diagnostic gives the reason: the correlation between \(d\) and \(\log(1+d)\) is
**0.998679** over 40 to 60 days against **0.962077** over 5 to 60, and the variance factor for theta,
\(S_{dd}/\Delta\), is **143.61** against **0.189**. The two regressors are almost the same variable
over a short window, so curvature and slope cannot be separated.

The shipped guard tests `delta <= 1e-12`, an absolute threshold on a quantity with units of
days squared, which is scale-dependent and does not fire here. What kept the number off the page was
the horizon-support guard: 392 of 400 fits returned `outside_support` because the default horizons
(28, 14, 7, 2, 0 days) lie outside a window that starts at 40 days. So the page was protected, but
by the horizon guard, not by any guard on the design. The theta is still computed and returned in the
refusal object.

This is a finding about the guard architecture, not a bug in a calculation. `02-a`'s design
requirement is "at least 5 days of spread", which this cell satisfies comfortably with 20 days of
spread. Twenty days of spread is not the same thing as a well-conditioned design, and only one of the
two is checked.

---

## 5. The SIM pass conditions, in full

43 SIM conditions, decided before the run. 37 held.

### Study A: PASS (all 19 conditions)

| condition | outcome |
|---|---|
| `A.mu`, six cells | PASS, largest bias 0.0097 against a 0.0196 threshold |
| `A.tau_mean`, three J | PASS, relative bias +0.010, -0.010, +0.003 |
| `A.tau_unpinned_small`, J=2 and J=5 | PASS, p10 -0.0064 and 0.0169 |
| `A.tau_pinned_20` | PASS, p10 0.0508 and p90 0.1316 |
| `A.tau_at_floor`, three J | PASS, 0.331, 0.056, 0.000 |
| `A.switch`, three J | PASS, `declared` below nine, `dersimonian_laird` at twenty |
| `A.canary` | PASS, the +0.02 shift is caught |

### Study B: FAIL

| condition | outcome |
|---|---|
| `B.declared_matched`, J=2 | **FAIL**, coverage 0.805 |
| `B.declared_matched`, J=5 | PASS, 0.872 |
| `B.declared_matched`, J=20 | PASS, 0.879 |
| `B.declared_default`, J=2 / 5 / 20 | PASS, 0.620 / 0.694 / 0.718, all below 0.87 as predicted |
| `B.pooled_width`, declared 0.20, J=2 / J=5 | **FAIL**, 0.720 / 0.746 |
| `B.pooled_width`, declared 0.20, J=20 | PASS, 0.873 |
| `B.pooled_width`, declared 0.30, all J | PASS, 0.897 / 0.904 / 0.873 |
| `B.width_shrinks`, declared 0.20 | **FAIL**, 0.8328, 0.7329, 0.9982 |
| `B.width_shrinks`, declared 0.30 | PASS, 1.2270, 1.0893, 0.9982 |

### Study C: FAIL

| condition | outcome |
|---|---|
| `C.diff_uncapped`, two uncapped cells | PASS, bias -0.0002 and -0.0063 |
| `C.diff_noisy` | PASS, bias -0.0005 |
| `C.oracle`, four capped cells | PASS, largest bias +0.0018 |
| `C.cap_direction` | **FAIL**, bias positive in every capped cell and not monotone in s |
| `C.cap_magnitude` | **FAIL**, "relative attenuation" is -0.131 at s=0.40 and -0.085 at s=0.70 |
| `C.guard` | PASS, `cap_mass_dominates` in 1.000 of fits at s=0.70 and 0.000 at s<=0.40 |

---

## 6. What this SIM study proves, and what it does not

**What it proves.** Given the assumptions printed in sections 2 to 4, the shipped pooled estimator
recovers the population mean log ratio without detectable bias at 2, 5 and 20 events; the
between-event variance is unbiased on average at every one of those counts and is not usable per
draw until about twenty events, with a third of two-event draws at or below a variance of 0.01, which
is the declared floor; the
nine-event switch and the floor fire exactly where the code says they do; the declared band, drawn
at \(z\tau\) around an estimated mean, under-covers a new event's mean at two events (0.805) because
it omits the variance of that mean, and the pooled width the payload already carries restores
coverage to 0.897 and 0.904; the default declared tau of 0.20 covers only 0.62 to 0.72 of draws
against a between-event tau of 0.30; the within-ticket differenced estimator recovers a known decay
parameter with essentially no bias when no cap binds; a cap that truncates the top of the
distribution biases the fitted curvature **upward** by 4% to 13% while flattening the observed
end-to-end path as C1 says, the flattening being measured in the noiseless diagnostic; the cap-mass
guard refuses at a 70% mass and never below 40%; and a 20-day window makes the curvature numerically
meaningless (RMSE 1.04 for the shipped fit) with no guard in the engine testing the conditioning of
the design.

**What it does not prove.** It says nothing about ticket markets. The generative model was written
from each estimator's own assumptions, which is what makes the study informative and is also exactly
what limits it: a pass cannot detect a wrong assumption, only a wrong implementation. Nothing here
establishes that event means are normal, that between-event variance is constant, that \(\theta\) is
common across events, that errors are independent, that the cap sits at a quantile of a latent
normal, that tickets are exchangeable, or that any of these numbers transfer to a platform where
tickets are selected into resale, sold in tiers with different faces, and traded on a ledger with
wallet-level clustering. There is no calendar dimension in study C, so it cannot and does not test
the age-period-cohort non-identification of `02-a` section 4.2(3). There is no leakage test, no
missing data, no cap leakage off-platform, and no heterogeneity in \(\theta\). The coverage numbers
are coverage of a *declared* band against one fixed truth; they are not calibration on this platform.
The 0.805 is not "the engine is wrong 20% of the time on tickets". It is the coverage of a floor
that the code, the finding and the label all describe as a declared width, measured against a truth
this study chose.

---

## 7. SIM: what changed, and what did not

* **The engine was not edited.** No bug was found: every number the study produced is what the
  shipped code does, and the two failures are properties of the estimator and of one constant, not
  transcription errors. The instructions were to leave the estimator alone on a failed property, and
  it was left alone.
* **No frontend, no fleet paths, no git operations.** Nothing was committed or pushed.
* **The one change inside the harness after the first run** is the block labelled
  `POST-RUN DIAGNOSTIC`, added to explain the sign that `C.cap_direction` reported. It prints
  descriptive numbers only, and it changed no pass condition, grid, replication count or seed.

**Registry rows this finding implies** (not edited here): `D` model rows for the pooled estimator
and the path estimator gain a SIM row with the conditions above; `B` a row for the demonstrated
upward bias of the path curvature under a binding cap, which corrects the reading of `02-a` C1;
`F` a decision row for the declared-tau constant, where the measured coverage at 0.20 is 0.620 to
0.718 against a tau of 0.30, and a row recording that the width condition in `06` G2 cannot hold
across the declared-to-estimated switch.
