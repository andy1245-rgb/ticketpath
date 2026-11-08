"""The off-chain score: covered, below, above, at both bounds, and the refusal cases.

Every expected number is written as an integer literal or an exact expression, never as a
float, because the function under test is specified to return an integer. The huge-realised
case is the one that would fail first if the arithmetic went through a float: `2**64 - 1` is
not exactly representable as a double.
"""

from __future__ import annotations

import hashlib
import json
import unittest

from ticketpath.core import forecast_score as fs


class TestIntervalScore(unittest.TestCase):
    def test_inside_scores_the_width_of_the_band(self) -> None:
        # [90, 110] at 100: no penalty, so 20 lamports * 1e6 micro-lamports.
        self.assertEqual(fs.interval_score_micro(100, 90, 110, 0.2), 20_000_000)
        self.assertEqual(fs.interval_score_micro(100, 90, 110), 20_000_000)

    def test_exactly_at_each_bound_has_no_penalty(self) -> None:
        self.assertEqual(fs.interval_score_micro(90, 90, 110), 20_000_000)
        self.assertEqual(fs.interval_score_micro(110, 90, 110), 20_000_000)
        # And a point band covers only its one value.
        self.assertEqual(fs.interval_score_micro(5, 5, 5), 0)

    def test_below_the_band_adds_the_winkler_penalty(self) -> None:
        # 10 below the low end: 20 + (2/0.2) * 10 = 20 + 100 = 120 lamports.
        self.assertEqual(fs.interval_score_micro(80, 90, 110), 120_000_000)
        self.assertGreater(
            fs.interval_score_micro(80, 90, 110),
            fs.interval_score_micro(90, 90, 110),
        )

    def test_above_the_band_adds_the_same_penalty_on_the_other_side(self) -> None:
        self.assertEqual(fs.interval_score_micro(120, 90, 110), 120_000_000)
        self.assertEqual(
            fs.interval_score_micro(120, 90, 110),
            fs.interval_score_micro(80, 90, 110),
        )

    def test_a_huge_realised_value_stays_exact(self) -> None:
        realised = 2**64 - 1
        low, high = 90, 110
        expected = (high - low + 10 * (realised - high)) * 1_000_000
        self.assertEqual(fs.interval_score_micro(realised, low, high), expected)
        self.assertIsInstance(fs.interval_score_micro(realised, low, high), int)
        # The float path would lose the low bits here; pin the last digit of the exact value.
        self.assertEqual(
            str(fs.interval_score_micro(realised, low, high)),
            str(expected),
        )

    def test_alpha_is_one_fifth_and_the_default(self) -> None:
        self.assertEqual(fs.DEFAULT_ALPHA, 0.2)
        self.assertEqual(fs._alpha_ratio(fs.DEFAULT_ALPHA), (1, 5))
        self.assertEqual(fs._alpha_ratio("1/5"), (1, 5))
        self.assertEqual(fs._alpha_ratio((1, 5)), (1, 5))
        self.assertIn("80% central interval", fs.SCORING_RULE)
        self.assertIn("alpha=1/5", fs.SCORING_RULE)
        # The default and the explicit decimal are the same rule; 0.5 is a different one.
        self.assertEqual(
            fs.interval_score_micro(80, 90, 110),
            fs.interval_score_micro(80, 90, 110, 0.2),
        )
        self.assertEqual(fs.interval_score_micro(80, 90, 110, 0.5), 60_000_000)
        with self.assertRaises(ValueError):
            fs.interval_score_micro(80, 90, 110, 0)
        with self.assertRaises(ValueError):
            fs.interval_score_micro(80, 90, 110, 1)
        with self.assertRaises(TypeError):
            fs.interval_score_micro(80, 90, 110, True)

    def test_the_rule_hash_is_sha256_of_the_canonical_text(self) -> None:
        self.assertEqual(len(fs.SCORING_RULE_HASH), 32)
        self.assertEqual(
            fs.SCORING_RULE_HASH,
            hashlib.sha256(fs.SCORING_RULE.encode("utf-8")).digest(),
        )
        # Re-serialisation: the text travels through JSON in the artefact and must hash the
        # same on the way back. A trailing newline or a different encoding would change it.
        round_tripped = json.loads(json.dumps(fs.SCORING_RULE))
        self.assertEqual(round_tripped, fs.SCORING_RULE)
        self.assertEqual(
            hashlib.sha256(round_tripped.encode("utf-8")).digest(),
            fs.SCORING_RULE_HASH,
        )
        self.assertEqual(fs.SCORING_RULE_HASH.hex(), fs.SCORING_RULE_HASH.hex().lower())

    def test_an_inverted_band_is_refused_not_scored(self) -> None:
        with self.assertRaises(ValueError):
            fs.interval_score_micro(100, 110, 90)

    def test_negative_or_non_integer_lamports_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            fs.interval_score_micro(-1, 0, 10)
        with self.assertRaises(ValueError):
            fs.interval_score_micro(5, -1, 10)
        with self.assertRaises(TypeError):
            fs.interval_score_micro(5.0, 0, 10)
        with self.assertRaises(TypeError):
            fs.interval_score_micro(True, 0, 10)


class TestScoredForecast(unittest.TestCase):
    def test_inside_returns_the_instruction_arguments_and_covered(self) -> None:
        forecast = {"low": 90, "high": 110}
        self.assertEqual(
            fs.scored_forecast(100, forecast),
            {
                "realised_lamports": 100,
                "interval_score_micro": 20_000_000,
                "covered": True,
            },
        )

    def test_below_and_above_are_not_covered(self) -> None:
        below = fs.scored_forecast(80, {"low": 90, "high": 110})
        above = fs.scored_forecast(120, {"low": 90, "high": 110})
        self.assertFalse(below["covered"])
        self.assertFalse(above["covered"])
        self.assertEqual(below["interval_score_micro"], 120_000_000)
        self.assertEqual(above["interval_score_micro"], 120_000_000)

    def test_the_bounds_are_inclusive(self) -> None:
        for realised in (90, 110):
            with self.subTest(realised=realised):
                scored = fs.scored_forecast(realised, {"low": 90, "high": 110})
                self.assertTrue(scored["covered"])
                self.assertEqual(scored["interval_score_micro"], 20_000_000)

    def test_an_object_with_low_and_high_works_like_a_mapping(self) -> None:
        class Band:
            low = 90
            high = 110

        self.assertEqual(fs.scored_forecast(100, Band()), fs.scored_forecast(100, {"low": 90, "high": 110}))

    def test_a_forecast_that_never_existed_is_a_refusal(self) -> None:
        with self.assertRaises(fs.ForecastRefused) as caught:
            fs.scored_forecast(100, None)
        self.assertIn("no forecast exists", caught.exception.reason)

    def test_a_missing_band_is_a_refusal_not_an_infinite_score(self) -> None:
        for forecast in ({}, {"low": 90}, {"high": 110}, {"low": None, "high": 110}):
            with self.subTest(forecast=forecast):
                with self.assertRaises(fs.ForecastRefused):
                    fs.scored_forecast(100, forecast)

    def test_a_refused_forecast_is_a_refusal(self) -> None:
        with self.assertRaises(fs.ForecastRefused):
            fs.scored_forecast(100, {"low": 90, "high": 110, "refused": 1})

    def test_the_two_limits_of_the_on_chain_field(self) -> None:
        # The field is a u64 and the rule multiplies by 1e6. A width of 18,446,744,073,709
        # lamports fits; one lamport more does not, and `LogForecast` refuses it 6031 on chain,
        # so a loggable forecast is always translatable here.
        self.assertEqual(fs.MAX_BAND_WIDTH_LAMPORTS, (2**64 - 1) // 1_000_000)
        self.assertLessEqual(fs.MAX_BAND_WIDTH_LAMPORTS * 1_000_000, fs.MAX_SCORE_MICRO)
        self.assertGreater((fs.MAX_BAND_WIDTH_LAMPORTS + 1) * 1_000_000, fs.MAX_SCORE_MICRO)

        widest = {"low": 0, "high": fs.MAX_BAND_WIDTH_LAMPORTS}
        self.assertEqual(
            fs.scored_forecast(fs.MAX_BAND_WIDTH_LAMPORTS, widest)["interval_score_micro"],
            fs.MAX_SCORE_MICRO - fs.MAX_SCORE_MICRO % 1_000_000,
        )
        with self.assertRaises(fs.ForecastRefused):
            fs.scored_forecast(0, {"low": 0, "high": fs.MAX_BAND_WIDTH_LAMPORTS + 1})

        # A huge miss overflows the field even with a tiny band: 1,844 SOL of miss at alpha 1/5.
        with self.assertRaises(fs.ForecastRefused) as caught:
            fs.scored_forecast(2**64 - 1, {"low": 90, "high": 110})
        self.assertIn("does not fit", caught.exception.reason)
        # The rule itself is still exact and unbounded: it is the wire that has a domain.
        self.assertGreater(
            fs.interval_score_micro(2**64 - 1, 90, 110),
            fs.MAX_SCORE_MICRO,
        )

    def test_a_refusal_is_a_value_error_so_a_caller_cannot_miss_it(self) -> None:
        self.assertTrue(issubclass(fs.ForecastRefused, ValueError))
        with self.assertRaises(ValueError):
            fs.scored_forecast(100, None)


if __name__ == "__main__":
    unittest.main()
