"""The path: one parameter recovered exactly on a noiseless design, and every guard's reason.

The hand-computed case is the whole justification of the 2x2 solve. Give it marks whose
log ratio is exactly `0.1 + 0.5 * log(1 + d)` and it must return theta = 0.5 and beta = 0.
If it does not, the algebra in `02-a` section 8.3 has been transcribed wrongly, and no
amount of fixture output would reveal that.
"""

from __future__ import annotations

import math
import unittest

from ticketpath.core import path_model

FACE = 1_000_000_000


def mark(price, days, at_ceiling=False):
    return {
        "ticketId": f"t{price}{days}",
        "priceLamports": price,
        "markupBps": round((price - FACE) * 10000 / FACE),
        "occurredAt": "2026-01-01T00:00:00.000Z",
        "daysToEvent": days,
        "atCeiling": at_ceiling,
        "tierFaceLamports": FACE,
    }


def features(marks, spread=None, cap=None, face=FACE):
    spread_days = spread if spread is not None else (max(m["daysToEvent"] for m in marks) - min(m["daysToEvent"] for m in marks) if marks else 0.0)
    return {
        "eventId": "evt",
        "capBpsRecorded": cap,
        "tiers": [
            {
                "tierId": "t",
                "name": "T",
                "faceValueLamports": face,
                "totalSupply": 10,
                "issuedCount": 5,
                "sellThrough": 0.5,
                "capBpsRecorded": cap,
                "capCeilingLamportsRecorded": None if cap is None else face * (10000 + cap) // 10000,
                "marks": marks,
                "atCeilingCount": sum(1 for m in marks if m["atCeiling"]),
                "belowCeilingCount": sum(1 for m in marks if not m["atCeiling"]),
                "highestRecordedLamports": max((m["priceLamports"] for m in marks), default=None),
                "lowestRecordedLamports": min((m["priceLamports"] for m in marks), default=None),
                "exposureTicketDays": 10.0,
                "ticketsNotIssuedAtCut": 0,
                "timeSpreadDays": spread_days,
                "exits": {"sale": len(marks), "transfer": 0, "redeem": 0, "revoke": 0},
            }
        ],
    }


class TestGuards(unittest.TestCase):
    def test_fewer_than_four_marks_is_refused_with_the_flat_benchmark(self) -> None:
        out = path_model.estimate(features=features([mark(FACE, 10), mark(FACE, 9), mark(FACE, 8)]), tier_id="t", anchor_lamports=FACE)
        self.assertFalse(out["available"])
        self.assertEqual(out["reason"], "insufficient_marks")
        self.assertEqual(out["basis"], "martingale")

    def test_a_two_day_spread_is_refused(self) -> None:
        marks = [mark(FACE, 10), mark(FACE, 10), mark(FACE, 9), mark(FACE, 8)]
        out = path_model.estimate(features=features(marks), tier_id="t", anchor_lamports=FACE)
        self.assertFalse(out["available"])
        self.assertEqual(out["reason"], "insufficient_time_spread")

    def test_more_than_half_the_marks_on_the_ceiling_refuses_a_central_statistic(self) -> None:
        marks = [mark(FACE, 10, True), mark(FACE, 9, True), mark(FACE, 8, True), mark(FACE, 5), mark(FACE, 2)]
        out = path_model.estimate(features=features(marks, cap=1500), tier_id="t", anchor_lamports=FACE)
        self.assertFalse(out["available"])
        self.assertEqual(out["reason"], "cap_mass_dominates")

    def test_a_singular_design_is_refused(self) -> None:
        # four marks, all at one horizon, with the spread field asserted to 10: the 2x2
        # normal matrix is exactly singular, which is what the guard exists for.
        marks = [mark(FACE, 20) for _ in range(4)]
        out = path_model.estimate(
            features=features(marks, spread=10.0), tier_id="t", anchor_lamports=FACE
        )
        self.assertFalse(out["available"])
        self.assertEqual(out["reason"], "degenerate_design")

    def test_the_martingale_is_flat_at_the_anchor(self) -> None:
        out = path_model.estimate(features=features([mark(FACE, 10)]), tier_id="t", anchor_lamports=123_000_000)
        self.assertEqual(out["anchorLamports"], 123_000_000)
        for point in out["points"]:
            self.assertEqual(point["lamportsLower"], 123_000_000)
            self.assertEqual(point["lamportsUpper"], 123_000_000)


class TestExactRecovery(unittest.TestCase):
    """y(d) = 0.1 + 0.5 * log(1 + d), four marks, no noise. The solve must return 0.5.

    d = 1, 2, 3, 8  ->  log(1+d) = 0.6931, 1.0986, 1.3863, 2.1972
    y = 0.7931, 0.6493, 0.7931, 1.1986  (0.1 + 0.5 * log(1+d))
    price = 1 SOL * exp(y)
    """

    DAYS = (1, 2, 3, 8)

    def setUp(self) -> None:
        self.marks = [
            mark(int(round(FACE * math.exp(0.1 + 0.5 * math.log(1 + d)))), d) for d in self.DAYS
        ]
        self.out = path_model.estimate(
            features=features(self.marks), tier_id="t", anchor_lamports=FACE, horizon_days=(5, 4)
        )

    def test_theta_is_the_slope_that_generated_the_marks(self) -> None:
        self.assertTrue(self.out["available"], self.out.get("reason"))
        self.assertAlmostEqual(self.out["theta"], 0.5, places=6)

    def test_beta_is_zero_when_the_marks_come_from_curvature_alone(self) -> None:
        self.assertAlmostEqual(self.out["omega1"], self.out["omega0"], delta=2_000_000)

    def test_a_point_inside_the_window_is_the_curve_evaluated_there(self) -> None:
        # y(5) = 0.1 + 0.5 * log(6) = 0.9959 -> 1 SOL * exp(0.9959) = 2.7070 SOL
        expected = FACE * math.exp(0.1 + 0.5 * math.log(6))
        point = next(p for p in self.out["points"] if p["days"] == 5)
        self.assertLess(abs(point["lamportsLower"] - expected) / expected, 1e-4)

    def test_a_horizon_outside_the_observed_window_is_not_quoted(self) -> None:
        out = path_model.estimate(
            features=features(self.marks), tier_id="t", anchor_lamports=FACE, horizon_days=(0,)
        )
        self.assertFalse(out["available"])
        self.assertEqual(out["reason"], "outside_support")
        self.assertTrue(out["fitted"])  # the curvature was estimated; no path value is quoted
        self.assertEqual(out["basis"], "martingale")  # what is drawn is the flat benchmark
        for point in out["points"]:
            self.assertEqual(point["lamportsLower"], FACE)
            self.assertTrue(point["outsideSupport"])

    def test_the_age_period_cohort_limitation_is_in_the_output(self) -> None:
        self.assertIn("age-period-cohort", self.out["identification"])
        self.assertIn("bracket", self.out["identification"])


if __name__ == "__main__":
    unittest.main()
