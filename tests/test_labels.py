"""The sentence registry, tested in both directions.

Two things have to be true at once, and they pull against each other:

* every allowed sentence renders, with fields substituted, and
* no allowed sentence matches a banned pattern -- while the prohibited sentences do.

The negative forms are the reason the second needs care. "No program is deployed" is a
required sentence; a pattern matching the bare word `deployed` would fail it. So the
patterns are phrases, and `contains_banned` strips the negatives by name first. The test
below checks both halves: the negative passes, and the positive claim next to it fails.
"""

from __future__ import annotations

import unittest

from ticketpath.core import labels

FIELDS = {
    "n": 9,
    "x": 20.7,
    "n_events": 3,
    "m": 2,
    "P": "0.93",
    "s": 4,
    "y": 1.2,
    "d": 8,
    "p1": "1.20",
    "p2": "1.38",
    "c": 15,
    "k": 8,
    "lo": "1.38",
    "hi": "2.25",
    "P_lo": "0.67",
    "P_hi": "1.29",
    "tier": "General",
    "asOf": "2026-11-07T12:00:00Z",
    # the decision-mode, net-line and [EXACT]-ceiling fields
    "name": "Synthetic Stage: Resale Cap Binds",
    "status": "on_sale",
    "startsAt": "2026-11-21T23:00:00.000Z",
    "endsAt": "2026-11-22T02:00:00.000Z",
    "net": "1.33",
    "shortfall": "3.62",
    "fee": "0.05",
    "price": "1.38",
    "lamports": "1,380,000,000",
    "face": "1,200,000,000",
    "cap": 1500,
    # the ceiling a band's upper end is stopped at, in SOL
    "ceiling": "1.38",
    # the cap this page prices against when the URL names one, beside the record's own cap
    "recorded": 1500,
    "sol": "1.38",
    # the refusal that exists because the cap in force forbids the recommendation
    "cap_bps": 0,
    "ceiling_lamports": "1,000,000,000 lamports",
    "row": "led_0002",
    # what a held-back store withheld, said in words rather than as a typed code (N6)
    "reason": "a sale recorded without money",
    "reasons": "a sale recorded without money",
    # the design document the chain slot points at instead of claiming a deployment
    "doc": "docs/ON-CHAIN-DESIGN.md",
    # the chain slot's clause about the quote: its id, its instant and, where a file was
    # recorded on another cluster, which cluster
    "cluster": "testnet",
    "quoteId": "q-18f4ec73dd8d8fd1",
    "liveQuoteId": "q-15ef2d6b36b4f54f",
    "liveAsOf": "2026-11-08T12:00:00.000Z",
    "recordedQuoteId": "q-18f4ec73dd8d8fd1",
    "recordedAsOf": "2026-11-07T18:34:29.183Z",
    # the two recommendations, printed only where they differ
    "rec": "1,380,000,000 lamports",
    "cur": "1,200,000,000 lamports",
}


class TestAllowedSentences(unittest.TestCase):
    def test_every_id_renders_with_sample_fields(self) -> None:
        for label_id in sorted(labels.ALLOWED_IDS):
            with self.subTest(label_id=label_id):
                text = labels.render(label_id, **FIELDS)
                self.assertTrue(text)
                self.assertNotIn("{", text)

    def test_an_unknown_id_raises(self) -> None:
        with self.assertRaises(KeyError):
            labels.render("A99")

    def test_no_allowed_sentence_matches_a_banned_pattern(self) -> None:
        for label_id in sorted(labels.ALLOWED_IDS):
            text = labels.render(label_id, **FIELDS)
            with self.subTest(label_id=label_id):
                self.assertIsNone(labels.contains_banned(text), f"{label_id} matches a banned pattern")

    def test_the_mandatory_sentences_are_the_spec_strings(self) -> None:
        self.assertTrue(labels.render("T1").startswith("SYNTHETIC FIXTURE DATA — every number on this page"))
        self.assertEqual(labels.render("T2"), "This is a bound, not an optimum.")
        self.assertIn("declared width around the record, not a confidence interval", labels.render("T3"))
        self.assertIn("It is not the probability that a listed ticket sells.", labels.render("T4"))
        # T5 is the page's deployment claim. It used to read "No program is deployed on any
        # cluster", which became false on 2026-11-07 when the devnet publish landed a program:
        # the console would have printed that sentence and that program's id on one page
        # (feature 2, part 3). The guarantee it exists for is the half that stays.
        self.assertEqual(
            labels.render("T5"),
            "No deployment is claimed by this page. Nothing on this page is a deployed guarantee.",
        )
        self.assertNotIn("no program is deployed", labels.render("T5").lower())


class TestProhibitedSentences(unittest.TestCase):
    def test_the_sentence_this_build_exists_to_remove_is_banned(self) -> None:
        # The exact string from records/findings/00-adversarial-review-phase1.md section 6.
        # Its presence in BANNED_SOURCES is what makes deleting the prohibition break a test.
        sentence = "This ticket has an X% chance of selling at price p."
        self.assertIsNotNone(labels.contains_banned(sentence))
        self.assertTrue(any("chance of selling" in source for source in labels.BANNED_SOURCES))

    def test_each_prohibited_shape_is_caught(self) -> None:
        cases = [
            "The probability this ticket sells at price p is 40%.",
            "The engine knows what this ticket is worth.",
            "The demand curve is steep.",
            "The price elasticity is 1.4.",
            "The cap correction recovers the true value of the best inventory.",
            "Weather and injuries are irrelevant to pricing.",
            "The sale probability is calibrated.",
            "The resale ledger is complete.",
            "The 41% markup is what the whole market earns.",
            "The engine finds the revenue-maximising primary price.",
            "The cap is the central structural fact of the project.",
            "The asking-versus-realised gap has been measured.",
            "The price should be raised to the cap because demand exceeds it.",
            "1.38 SOL is what this ticket is worth.",
            "The market price was 1.38 SOL.",
            "That is our price prediction.",
            "It is 90% likely to sell.",
            "The program is deployed on devnet.",
            "This is verified on Solana.",
            "We compared it against comparable events.",
            "The probability of sale is high.",
            "Here is the liquidity score.",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNotNone(labels.contains_banned(text), text)

    def test_the_negatives_the_page_needs_are_not_banned(self) -> None:
        cases = [
            "The transfer hook that makes the cap binding is designed, not deployed.",
            "We do not state an upper bound from this record.",
            "Not a prediction: this event has no resales yet.",
            "No prediction: nothing has resold on this platform yet.",
            "The flat line below is the benchmark, not a forecast.",
            # the spec's own required sentence for a candidate cap below a recorded price
            "under the deployed program those transfers would have failed",
            # the file-scoped absent sentence, which is not the project-wide claim
            "No devnet transaction is recorded in the console's artefact file.",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIsNone(labels.contains_banned(text), text)

    def test_the_two_project_wide_negatives_are_caught_now(self) -> None:
        """The guard could never fire on the two claims the feature-2 sweep went looking for.

        `ALLOWED_NEGATIVES` stripped "no program is deployed" and "no devnet transaction has
        been recorded" before any pattern was scanned, so the sentence the page was supposed to
        stop printing could not be caught by the guard that exists to catch it. Both are false
        of a tree with a program and three transactions on devnet, and both are refused now.
        """
        for text in (
            "No program is deployed on any cluster.",
            "No devnet transaction has been recorded.",
            "No on-chain transaction has been recorded for this platform.",
        ):
            with self.subTest(text=text):
                self.assertIsNotNone(labels.contains_banned(text), text)
        self.assertNotIn("no program is deployed", labels.ALLOWED_NEGATIVES)
        self.assertNotIn("no devnet transaction has been recorded", labels.ALLOWED_NEGATIVES)


class TestBadges(unittest.TestCase):
    def test_exactly_eight_badges(self) -> None:
        self.assertEqual(len(labels.BADGES), 8)
        self.assertEqual(labels.badge("FIXTURE"), "[FIXTURE]")
        self.assertEqual(labels.badge("UNVALIDATED"), "[UNVALIDATED]")

    def test_an_unknown_badge_is_a_key_error(self) -> None:
        with self.assertRaises(KeyError):
            labels.badge("VALIDATED")


if __name__ == "__main__":
    unittest.main()
