"""The recommendation: a boundary, an exact consequence table, and four refusals.

The consequence arithmetic is exact and is checked by hand:
`requiredSellThrough(c) = face * sellThrough / c`
with face 1.20 SOL, sellThrough 0.04 -> 0.048 SOL per offered seat, so at 1.38 SOL the
tier must sell 0.048 / 1.38 = 0.0347826... of its seats to hold the same revenue.
"""

from __future__ import annotations

import unittest

from ticketpath.core import primary_optimum

FACE = 1_200_000_000
CEILING = 1_380_000_000


def features(at_ceiling=8, sales=9, sell_through=0.04):
    marks = [
        {
            "ticketId": f"t{i}",
            "priceLamports": CEILING,
            "markupBps": 1500,
            "occurredAt": "2026-09-14T00:00:00.000Z",
            "daysToEvent": 60.0,
            "atCeiling": i < at_ceiling,
            "tierFaceLamports": FACE,
        }
        for i in range(sales)
    ]
    return {
        "eventId": "evt",
        "capBpsRecorded": 1500,
        "tiers": [
            {
                "tierId": "t",
                "name": "General",
                "faceValueLamports": FACE,
                "totalSupply": 200,
                "issuedCount": int(sell_through * 200),
                "sellThrough": sell_through,
                "capBpsRecorded": 1500,
                "capCeilingLamportsRecorded": CEILING,
                "marks": marks,
                "atCeilingCount": at_ceiling,
                "belowCeilingCount": sales - at_ceiling,
                "highestRecordedLamports": CEILING,
                "lowestRecordedLamports": CEILING,
                "exposureTicketDays": 400.0,
                "ticketsNotIssuedAtCut": 0,
                "timeSpreadDays": 10.0,
                "exits": {"sale": sales, "transfer": 0, "redeem": 0, "revoke": 0},
            }
        ],
    }


def band(regime="capped_and_binding", level=None, lo=CEILING, hi=None):
    return {
        "regime": regime,
        "floorLamports": CEILING if regime == "capped_and_binding" else None,
        "level": {
            "available": level is not None,
            "lamports": level,
            "basis": "tier_marks" if level is not None else "prior_only",
            "n": 9,
        },
        "band": {"loLamports": lo, "hiLamports": hi, "noUpperBound": hi is None},
        "labelId": "A19" if regime == "capped_and_binding" else "A2",
        "extraLabelIds": [],
    }


INTENSITY = {"sales": 9, "exposureTicketDays": 400.0, "salesPerTicketDay": 0.0225}


class TestBinding(unittest.TestCase):
    def test_the_recommendation_is_the_floor_and_says_at_least(self) -> None:
        out = primary_optimum.recommend(
            features=features(), tier_id="t", band=band(), intensity=INTENSITY, fee=None, sell_through_floor=None
        )
        self.assertEqual(out["recommendedLamports"], CEILING)
        self.assertTrue(out["recommendedIsFloor"])
        self.assertTrue(out["noUpperBound"])
        self.assertEqual(out["bandLamports"], [CEILING, None])
        self.assertEqual(out["labelId"], "A19")
        self.assertFalse(out["refused"])


class TestUncapped(unittest.TestCase):
    def test_the_recommendation_is_the_level_inside_the_band(self) -> None:
        lo, level, hi = 670_000_000, 930_000_000, 1_290_000_000
        out = primary_optimum.recommend(
            features=features(at_ceiling=0),
            tier_id="t",
            band=band(regime="uncapped", level=level, lo=lo, hi=hi),
            intensity=INTENSITY,
            fee=None,
            sell_through_floor=None,
        )
        self.assertEqual(out["recommendedLamports"], level)
        self.assertFalse(out["recommendedIsFloor"])
        self.assertEqual(out["bandLamports"], [lo, hi])
        self.assertTrue(lo < out["recommendedLamports"] < hi)


class TestRefusals(unittest.TestCase):
    def test_no_resale_is_refused_with_the_input_that_would_change_it(self) -> None:
        out = primary_optimum.recommend(
            features=features(at_ceiling=0, sales=0),
            tier_id="t",
            band=band(regime="no_resale", level=None, lo=None, hi=None),
            intensity=INTENSITY,
            fee=None,
            sell_through_floor=None,
        )
        self.assertTrue(out["refused"])
        self.assertEqual(out["refusalCode"], "no_resale_record")
        self.assertIn("a completed resale on this event", out["requiredInputs"])
        self.assertIsNone(out["recommendedLamports"])

    def test_a_prior_only_level_is_refused_rather_than_priced(self) -> None:
        out = primary_optimum.recommend(
            features=features(at_ceiling=0),
            tier_id="t",
            band=band(regime="uncapped", level=None, lo=1, hi=2),
            intensity=INTENSITY,
            fee=None,
            sell_through_floor=None,
        )
        self.assertTrue(out["refused"])
        self.assertEqual(out["refusalCode"], "no_resale_record")
        self.assertIsNone(out["recommendedLamports"])

    def test_the_interior_optimum_is_refused_on_every_path(self) -> None:
        cases = [
            band(),
            band(regime="uncapped", level=930_000_000, lo=670_000_000, hi=1_290_000_000),
            band(regime="no_resale", level=None, lo=None, hi=None),
        ]
        for case in cases:
            out = primary_optimum.recommend(
                features=features(), tier_id="t", band=case, intensity=INTENSITY, fee=None, sell_through_floor=None
            )
            with self.subTest(regime=case["regime"]):
                codes = [row["code"] for row in out["refusals"]]
                self.assertIn("no_demand_response", codes)

    def test_no_fee_withholds_net_revenue_and_leaves_the_recommendation_alone(self) -> None:
        without = primary_optimum.recommend(
            features=features(), tier_id="t", band=band(), intensity=INTENSITY, fee=None, sell_through_floor=None
        )
        with_fee = primary_optimum.recommend(
            features=features(),
            tier_id="t",
            band=band(),
            intensity=INTENSITY,
            fee={"perTicketLamports": 0, "adValoremBps": 0},
            sell_through_floor=None,
        )
        self.assertIsNone(without["netRevenue"])
        self.assertEqual(with_fee["recommendedLamports"], without["recommendedLamports"])
        # 1.38 SOL with no fee: 1.38 per ticket, x 8 issued = 11.04 SOL for the tier
        self.assertEqual(with_fee["netRevenue"]["perTicket"], CEILING)
        self.assertEqual(with_fee["netRevenue"]["perTier"], CEILING * 8)

    def test_a_per_unit_fee_moves_only_the_net_line(self) -> None:
        out = primary_optimum.recommend(
            features=features(),
            tier_id="t",
            band=band(),
            intensity=INTENSITY,
            fee={"perTicketLamports": 80_000_000, "adValoremBps": 0},
            sell_through_floor=None,
        )
        self.assertEqual(out["recommendedLamports"], CEILING)
        self.assertEqual(out["netRevenue"]["perTicket"], CEILING - 80_000_000)


class TestConsequence(unittest.TestCase):
    def test_required_sell_through_is_face_times_sell_through_over_the_candidate(self) -> None:
        out = primary_optimum.recommend(
            features=features(),
            tier_id="t",
            band=band(),
            intensity=INTENSITY,
            fee=None,
            sell_through_floor=None,
            candidates=[CEILING],
        )
        row = out["consequence"][0]
        self.assertEqual(row["candidateLamports"], CEILING)
        self.assertAlmostEqual(row["requiredSellThrough"], 0.048 / 1.38, places=12)
        self.assertAlmostEqual(row["requiredSellThrough"], 0.034782608695652174, places=15)

    def test_the_observed_revenue_per_seat_is_face_times_sell_through(self) -> None:
        out = primary_optimum.recommend(
            features=features(sell_through=0.04),
            tier_id="t",
            band=band(),
            intensity=INTENSITY,
            fee=None,
            sell_through_floor=None,
            candidates=[FACE],
        )
        row = next(r for r in out["consequence"] if r["candidateLamports"] == FACE)
        self.assertEqual(row["observedRevenuePerSeatLamports"], 48_000_000)
        self.assertAlmostEqual(row["requiredSellThrough"], 0.04, places=12)  # at face, unchanged


class TestNoGridSearch(unittest.TestCase):
    def test_the_module_has_no_likelihood_and_no_maximiser(self) -> None:
        source = primary_optimum.__doc__ or ""
        self.assertIn("fabricated likelihood", source)
        self.assertEqual(primary_optimum.INTERIOR_REQUIRED_INPUTS, ("eta", "q_min", "a completed sell-through series"))


if __name__ == "__main__":
    unittest.main()
