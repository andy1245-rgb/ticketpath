"""The value band: three regimes, one estimator, and a width that is declared.

Every expectation is arithmetic written out in the test, with the numbers that produced
it. The band is `face * exp(ybar -/+ z * tau)`; when a test asserts a lamport value it
also shows that expression with its inputs, so the assertion can be checked by hand
without running the module.
"""

from __future__ import annotations

import datetime as dt
import math
import unittest

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.core import price_features, value_band

UTC = dt.timezone.utc
CUT = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
Z = 1.6449  # two-sided 90%, the spec's z
FACE = 1_000_000_000
SOL = 1_000_000_000


def make_tier(tier_id, face, prices, cap=None, at_ceiling=None, name="T"):
    """A TierFeatures row. `at_ceiling` is given explicitly so the test states its own truth."""
    marks = []
    for index, price in enumerate(prices):
        markup = round((price - face) * 10000 / face)
        marks.append(
            {
                "ticketId": f"t{index}",
                "priceLamports": price,
                "markupBps": markup,
                "occurredAt": f"2026-01-0{index + 1}T00:00:00.000Z",
                "daysToEvent": 10.0 - index,
                "atCeiling": bool(at_ceiling[index]) if at_ceiling else (cap is not None and abs(markup - cap) <= 1),
                "tierFaceLamports": face,
            }
        )
    return {
        "tierId": tier_id,
        "name": name,
        "faceValueLamports": face,
        "totalSupply": 100,
        "issuedCount": 4,
        "sellThrough": 0.04,
        "capBpsRecorded": cap,
        "capCeilingLamportsRecorded": None if cap is None else face * (10000 + cap) // 10000,
        "marks": marks,
        "atCeilingCount": sum(1 for mark in marks if mark["atCeiling"]),
        "belowCeilingCount": sum(1 for mark in marks if not mark["atCeiling"]),
        "highestRecordedLamports": max(prices) if prices else None,
        "lowestRecordedLamports": min(prices) if prices else None,
        "exposureTicketDays": 40.0,
        "ticketsNotIssuedAtCut": 0,
        "firstMarkAt": None,
        "lastMarkAt": None,
        "daysToEventAtFirstMark": None,
        "daysToEventAtLastMark": None,
        "timeSpreadDays": 9.0,
        "exits": {"sale": len(prices), "transfer": 0, "redeem": 0, "police": 0},
    }


def make_features(tiers, cap=None):
    marks = sum((row["marks"] for row in tiers), [])
    return {
        "eventId": "evt_test",
        "asOf": CUT.isoformat(),
        "startsAt": "2026-01-11T00:00:00.000Z",
        "name": "test",
        "capBpsRecorded": cap,
        "tiers": tiers,
        "event": {"sales": len(marks), "tickets": 4, "exposureTicketDays": 40.0, "atCeiling": 0},
        "provenance": {},
    }


class TestRegimes(unittest.TestCase):
    def test_capped_and_binding_is_a_cap_with_a_mass_point(self) -> None:
        tier = make_tier("t", 1_200_000_000, [1_380_000_000, 1_380_000_000, 1_236_000_000], cap=1500)
        regime = value_band.classify(features=make_features([tier], cap=1500), tier_id="t")
        self.assertEqual(regime["regime"], "capped_and_binding")
        self.assertEqual(regime["atCeilingCount"], 2)
        self.assertAlmostEqual(regime["shareAtCeiling"], 2 / 3)

    def test_capped_with_no_mass_point_is_its_own_regime(self) -> None:
        tier = make_tier("t", FACE, [1_100_000_000, 900_000_000], cap=2500)
        regime = value_band.classify(features=make_features([tier], cap=2500), tier_id="t")
        self.assertEqual(regime["regime"], "capped_no_mass_point")

    def test_no_cap_is_uncapped(self) -> None:
        tier = make_tier("t", FACE, [1_100_000_000], cap=None)
        regime = value_band.classify(features=make_features([tier], cap=None), tier_id="t")
        self.assertEqual(regime["regime"], "uncapped")

    def test_no_marks_is_no_resale(self) -> None:
        tier = make_tier("t", FACE, [], cap=1500)
        regime = value_band.classify(features=make_features([tier], cap=1500), tier_id="t")
        self.assertEqual(regime["regime"], "no_resale")


class TestBinding(unittest.TestCase):
    """02-b section 3.4: floor only. Any mean, quantile or upper end in this regime is a bug."""

    def setUp(self) -> None:
        self.cap = 1500
        self.tier = make_tier(
            "t", 1_200_000_000, [1_380_000_000, 1_380_000_000, 1_236_000_000], cap=self.cap, at_ceiling=[True, True, False]
        )
        self.features = make_features([self.tier], cap=self.cap)
        self.band = value_band.estimate(
            features=self.features, tier_id="t", tau=0.20, cap_bps_candidate=self.cap
        )

    def test_the_floor_is_the_highest_recorded_price(self) -> None:
        self.assertEqual(self.band["floorLamports"], 1_380_000_000)
        self.assertEqual(self.band["band"]["loLamports"], 1_380_000_000)

    def test_there_is_no_upper_end_and_no_level(self) -> None:
        self.assertTrue(self.band["band"]["noUpperBound"])
        self.assertIsNone(self.band["band"]["hiLamports"])
        self.assertFalse(self.band["level"]["available"])
        self.assertIsNone(self.band["level"]["lamports"])
        self.assertIsNone(self.band["level"]["logRatio"])

    def test_the_label_is_the_bound_trio_and_tau_is_inert(self) -> None:
        self.assertEqual(self.band["labelId"], "A19")
        for row in self.band["sensitivity"]:
            self.assertFalse(row["applicable"])
            self.assertEqual(row["reason"], "no upper tail in this record")


class TestBandArithmetic(unittest.TestCase):
    """Two marks at +20% and +80% over a 1 SOL face; the band is written out by hand.

    y1 = log(1.20) = 0.1823215568
    y2 = log(1.80) = 0.5877866649
    ybar = 0.3850541108
    half = z * tau = 1.6449 * 0.20 = 0.32898
    lo = 1 SOL * exp(0.3850541108 - 0.32898)
    hi = 1 SOL * exp(0.3850541108 + 0.32898)
    """

    def setUp(self) -> None:
        self.tier = make_tier("t", FACE, [1_200_000_000, 1_800_000_000])
        self.features = make_features([self.tier], cap=None)
        self.band = value_band.estimate(features=self.features, tier_id="t", tau=0.20, cap_bps_candidate=None)

    def test_the_point_is_the_geometric_mean_ratio_at_face(self) -> None:
        ybar = (math.log(1.2) + math.log(1.8)) / 2
        self.assertAlmostEqual(self.band["level"]["logRatio"], ybar, places=12)
        self.assertEqual(self.band["level"]["lamports"], int(round(FACE * math.exp(ybar))))
        self.assertEqual(self.band["level"]["basis"], "tier_marks")

    def test_the_band_is_z_times_tau_wide_in_logs(self) -> None:
        ybar = (math.log(1.2) + math.log(1.8)) / 2
        lo = int(round(FACE * math.exp(ybar - Z * 0.20)))
        hi = int(round(FACE * math.exp(ybar + Z * 0.20)))
        self.assertEqual(self.band["band"]["loLamports"], lo)
        self.assertEqual(self.band["band"]["hiLamports"], hi)
        self.assertEqual(self.band["band"]["widthSource"], "declared_tau")

    def test_the_level_sits_inside_its_band(self) -> None:
        self.assertLess(self.band["band"]["loLamports"], self.band["level"]["lamports"])
        self.assertLess(self.band["level"]["lamports"], self.band["band"]["hiLamports"])

    def test_the_width_is_monotone_in_tau_and_the_point_does_not_move(self) -> None:
        widths = []
        for tau in (0.10, 0.20, 0.30, 0.406):
            band = value_band.estimate(features=self.features, tier_id="t", tau=tau, cap_bps_candidate=None)
            widths.append(band["band"]["hiLamports"] - band["band"]["loLamports"])
            self.assertEqual(band["level"]["lamports"], self.band["level"]["lamports"])
        self.assertEqual(widths, sorted(widths))
        self.assertEqual(len(set(widths)), 4)

    def test_the_sensitivity_table_is_the_four_declared_widths(self) -> None:
        taus = [row["tau"] for row in self.band["sensitivity"]]
        self.assertEqual(taus, [0.10, 0.20, 0.30, 0.406])


class TestCappedNoMassPoint(unittest.TestCase):
    def test_the_top_is_capped_at_the_recorded_ceiling_and_a20_is_selected(self) -> None:
        face = 1_000_000_000
        # +20% sales against a +25% cap: the ceiling is 1.25 SOL, above the band's top.
        tier = make_tier("t", face, [1_180_000_000, 1_220_000_000], cap=2500)
        band = value_band.estimate(
            features=make_features([tier], cap=2500), tier_id="t", tau=0.406, cap_bps_candidate=2500
        )
        self.assertEqual(band["regime"], "capped_no_mass_point")
        self.assertTrue(band["band"]["topIsCeiling"])
        self.assertLessEqual(band["band"]["hiLamports"], 1_250_000_000)
        self.assertIn("A20", band["extraLabelIds"])


class TestThinData(unittest.TestCase):
    def test_one_mark_blends_halfway_to_the_event_mean(self) -> None:
        # one tier with a single +50% sale; a second tier with two +10% sales.
        thin = make_tier("thin", FACE, [1_500_000_000])
        other = make_tier("other", FACE, [1_100_000_000, 1_100_000_000])
        band = value_band.estimate(features=make_features([thin, other]), tier_id="thin", tau=0.20, cap_bps_candidate=None)
        event_mean = (math.log(1.5) + math.log(1.1) + math.log(1.1)) / 3
        expected = 0.5 * math.log(1.5) + 0.5 * event_mean  # declared half-and-half, not estimated
        self.assertEqual(band["level"]["basis"], "blended")
        self.assertAlmostEqual(band["level"]["logRatio"], expected, places=12)

    def test_a_tier_with_no_marks_borrows_the_event_mean(self) -> None:
        empty = make_tier("empty", FACE, [])
        other = make_tier("other", FACE, [1_200_000_000, 1_400_000_000])
        band = value_band.estimate(features=make_features([empty, other]), tier_id="empty", tau=0.20, cap_bps_candidate=None)
        self.assertEqual(band["level"]["basis"], "pooled_across_tiers")
        event_mean = (math.log(1.2) + math.log(1.4)) / 2
        self.assertAlmostEqual(band["level"]["logRatio"], event_mean, places=12)

    def test_a_prior_is_not_a_record_so_the_band_is_prior_only(self) -> None:
        empty = make_tier("empty", FACE, [])
        band = value_band.estimate(features=make_features([empty]), tier_id="empty", tau=0.20, cap_bps_candidate=None)
        self.assertEqual(band["level"]["basis"], "prior_only")
        self.assertEqual(band["labelId"], "A12")  # nothing has resold on this platform either
        mu, half = 0.2612, Z * 0.20
        self.assertEqual(band["band"]["loLamports"], int(round(FACE * math.exp(mu - half))))
        self.assertEqual(band["band"]["hiLamports"], int(round(FACE * math.exp(mu + half))))


class TestCandidateCapNeverTruncatesThePast(unittest.TestCase):
    def test_a_candidate_cap_below_a_recorded_price_reports_violations_and_moves_nothing(self) -> None:
        face = 1_000_000_000
        tier = make_tier("t", face, [1_100_000_000, 1_300_000_000], cap=None)
        features = make_features([tier], cap=None)
        untouched = value_band.estimate(features=features, tier_id="t", tau=0.20, cap_bps_candidate=None)
        capped = value_band.estimate(features=features, tier_id="t", tau=0.20, cap_bps_candidate=0)
        self.assertEqual(capped["band"]["loLamports"], untouched["band"]["loLamports"])
        self.assertEqual(capped["band"]["hiLamports"], untouched["band"]["hiLamports"])
        self.assertEqual(capped["capViolations"]["count"], 2)
        self.assertEqual(capped["capViolations"]["of"], 2)


class TestAgainstTheFixtureSnapshot(unittest.TestCase):
    """The spec's worked numbers, recomputed here from the raw rows rather than imported."""

    def setUp(self) -> None:
        adapter = LedgerAdapter.from_fixture()
        self.adapter = adapter
        self.faces = adapter.face_by_ticket()

    def _features(self, event_id: str) -> dict:
        return price_features.build(
            events=list(self.adapter.events()),
            tickets=list(self.adapter.tickets()),
            ledger=self.adapter.raw_ledger(),
            tier_faces=self.faces,
            event_id=event_id,
            as_of=CUT,
        )

    def test_the_uncapped_event_level_is_the_geometric_mean_ratio(self) -> None:
        features = self._features("evt_syn_04")
        band = value_band.estimate(features=features, tier_id="tier_thr_single", tau=0.20, cap_bps_candidate=None)
        marks = features["tiers"][0]["marks"]
        face = features["tiers"][0]["faceValueLamports"]
        by_hand = face * math.exp(sum(math.log(m["priceLamports"] / face) for m in marks) / len(marks))
        self.assertEqual(band["level"]["lamports"], int(round(by_hand)))
        # 0.93 SOL on the 2026-11-07 fixture; the invariant, not the snapshot, is asserted above.
        self.assertAlmostEqual(band["level"]["lamports"] / SOL, 0.93, places=2)

    def test_the_binding_event_is_a_floor_and_never_an_upper_end(self) -> None:
        features = self._features("evt_syn_02")
        band = value_band.estimate(features=features, tier_id="tier_stg_general", tau=0.20, cap_bps_candidate=1500)
        self.assertEqual(band["regime"], "capped_and_binding")
        self.assertIsNone(band["band"]["hiLamports"])
        # face 1.20 SOL at 1500 bps = 1.38 SOL, exact on the lamport
        self.assertEqual(band["floorLamports"], 1_200_000_000 * 11500 // 10000)


class TestPooling(unittest.TestCase):
    def test_no_events_returns_the_borrowed_prior_and_says_so(self) -> None:
        pool = value_band.pooled(rows=[], declared_tau=0.20)
        self.assertEqual(pool["method"], "declared")
        self.assertEqual(pool["mu"], 0.2612)
        self.assertEqual(pool["eventsWithResale"], 0)

    def test_below_nine_events_the_between_event_variance_is_declared(self) -> None:
        rows = [
            {"n": 3, "meanLogRatio": 0.1, "withinVar": 0.02, "startedAtCut": True},
            {"n": 4, "meanLogRatio": 0.2, "withinVar": 0.02, "startedAtCut": True},
        ]
        pool = value_band.pooled(rows=rows, declared_tau=0.20)
        self.assertEqual(pool["method"], "declared")
        self.assertAlmostEqual(pool["tau2"], 0.04)  # 0.20 ** 2, by hand

    def test_the_shrinkage_weight_is_one_half_when_the_variances_match(self) -> None:
        self.assertEqual(value_band.shrink_weight(0.04, 0.04), 0.5)
        self.assertEqual(value_band.shrink_weight(1.0, float("inf")), 0.0)


if __name__ == "__main__":
    unittest.main()
