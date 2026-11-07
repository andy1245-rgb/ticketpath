"""Integer money arithmetic: markup, mean, median, buckets."""

from __future__ import annotations

import unittest

from ticketpath.core import markup


class TestMarkup(unittest.TestCase):
    def test_markup_over_face(self) -> None:
        self.assertEqual(markup.markup_bps(1_250_000_000, 1_000_000_000), 2_500)

    def test_markup_below_face_is_negative(self) -> None:
        self.assertEqual(markup.markup_bps(900_000_000, 1_000_000_000), -1_000)

    def test_markup_at_face_is_zero(self) -> None:
        self.assertEqual(markup.markup_bps(1_000_000_000, 1_000_000_000), 0)

    def test_markup_uses_the_face_it_is_given(self) -> None:
        # Same price against two different tier faces. This is the contract's
        # multi-tier trap in its smallest form.
        self.assertEqual(markup.markup_bps(2_050_000_000, 2_000_000_000), 250)
        self.assertEqual(markup.markup_bps(2_050_000_000, 1_000_000_000), 10_500)

    def test_rounding_is_half_away_from_zero(self) -> None:
        # 1 lamport over a 20000 lamport face is 0.5 bps.
        self.assertEqual(markup.markup_bps(20_001, 20_000), 1)
        self.assertEqual(markup.markup_bps(19_999, 20_000), -1)
        # 1 lamport over a 40000 lamport face is 0.25 bps, which stays zero.
        self.assertEqual(markup.markup_bps(40_001, 40_000), 0)

    def test_non_positive_face_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            markup.markup_bps(100, 0)

        with self.assertRaises(TypeError):
            markup.markup_bps(100.5, 100)  # type: ignore[arg-type]


class TestMeanAndMedian(unittest.TestCase):
    def test_mean_rounds_half_away_from_zero(self) -> None:
        self.assertEqual(markup.mean_int([2_500, -1_000]), 750)
        self.assertEqual(markup.mean_int([2_500, -1_000, 500, 250]), 563)  # 562.5 -> 563
        self.assertEqual(markup.mean_int([-1, -2]), -2)  # -1.5 -> -2

    def test_mean_of_nothing_is_none(self) -> None:
        self.assertIsNone(markup.mean_int([]))

    def test_median_odd_and_even(self) -> None:
        self.assertEqual(markup.median_int([900, 1_050, 1_250]), 1_050)
        self.assertEqual(markup.median_int([900, 1_050, 1_250, 2_050]), 1_150)
        self.assertEqual(markup.median_int([1, 2]), 2)  # 1.5 -> 2, half away from zero
        self.assertIsNone(markup.median_int([]))


class TestBuckets(unittest.TestCase):
    def test_bounds_are_inclusive_lower_exclusive_upper(self) -> None:
        self.assertEqual(markup.bucket_of(-10_000), "At or below face")
        self.assertEqual(markup.bucket_of(0), "At or below face")
        self.assertEqual(markup.bucket_of(1), "0\u201325%")
        self.assertEqual(markup.bucket_of(2_499), "0\u201325%")
        self.assertEqual(markup.bucket_of(2_500), "25\u201350%")
        self.assertEqual(markup.bucket_of(20_000), "Over 200%")

    def test_all_six_buckets_in_order_even_when_empty(self) -> None:
        buckets = markup.markup_distribution([])
        self.assertEqual(
            [bucket["label"] for bucket in buckets],
            [
                "At or below face",
                "0\u201325%",
                "25\u201350%",
                "50\u2013100%",
                "100\u2013200%",
                "Over 200%",
            ],
        )
        self.assertEqual([bucket["count"] for bucket in buckets], [0, 0, 0, 0, 0, 0])
        self.assertEqual(buckets[0]["fromBps"], -10_000)
        self.assertEqual(buckets[-1]["toBps"], None)

    def test_distribution_counts(self) -> None:
        buckets = markup.markup_distribution([2_500, -1_000, 500, 250])
        self.assertEqual([bucket["count"] for bucket in buckets], [1, 2, 1, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
