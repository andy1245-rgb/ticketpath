"""The two production sale call sites, and the flags that decide who the seller pays.

The artist fee is charged on a **resale**. `EventChain.transfer` takes
`charge_artist_fee: bool = True`, so a primary buy that forgets the flag charges the artist a fee on
the artist's own ticket, and no behavioural test would notice a third call site that did — the runner
would still run, the sale would still land, and the row would read `fee_lamports: 50 000 000` on a
primary purchase.

The flip tax has the same shape and the same default (`charge_flip_tax: bool = True`), so it has the
same failure mode and this file guards both: a call site that names one flag and inherits the other
charges the artist for a ticket the house already owned, or charges no tax on the sale the tax exists
for, and no row would say so.

This file is the guard for that: it reads `market_swarm/runner.py` and requires every
`chain.transfer(` call in it to name both flags explicitly. It is a source check on purpose, in the
style of `test_gateway.py`'s approved-`dp`-units test, because the thing worth pinning is not what
the current two call sites do but that a new one cannot arrive silently.

No cluster, no socket: a file, a regular expression and the values the runner passes.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
RUNNER = PACKAGE / "runner.py"
GATEWAY = PACKAGE / "gateway.py"

#: How many characters after `chain.transfer(` the argument block may run. Wide enough for a call
#: site with its own comment explaining why it charges or does not, narrow enough that a flag on a
#: different sale far below cannot excuse a missing one.
WINDOW = 800


def call_sites(source: str) -> list[str]:
    """The text of every `chain.transfer(` argument block in `source`."""
    return [
        source[match.start():match.start() + WINDOW]
        for match in re.finditer(r"chain\.transfer\(", source)
    ]


class TheFeeIsChargedWhereItIsIntended(unittest.TestCase):
    def setUp(self) -> None:
        self.source = RUNNER.read_text(encoding="utf-8")

    def test_the_runner_has_the_two_sale_call_sites_this_guard_is_about(self) -> None:
        """A primary buy and a resale. A third one means this file needs a decision, not a pass."""
        found = call_sites(self.source)
        self.assertEqual(
            len(found), 2,
            f"runner.py has {len(found)} chain.transfer( call sites; each must name "
            "charge_artist_fee explicitly, and a new one needs its own decision here",
        )

    def test_every_call_site_names_the_flag_explicitly(self) -> None:
        for index, block in enumerate(call_sites(self.source), start=1):
            self.assertIn(
                "charge_artist_fee=", block,
                f"call site {index} does not pass charge_artist_fee, so it inherits the default "
                "(True) and would charge the artist a fee on whatever sale it builds",
            )

    def test_every_call_site_names_the_tax_flag_explicitly(self) -> None:
        for index, block in enumerate(call_sites(self.source), start=1):
            self.assertIn(
                "charge_flip_tax=", block,
                f"call site {index} does not pass charge_flip_tax, so it inherits the default "
                "(True) and would charge the flip tax on whatever sale it builds",
            )

    def test_the_primary_buy_does_not_charge_and_the_resale_does(self) -> None:
        blocks = call_sites(self.source)
        primary, resale = blocks[0], blocks[1]
        self.assertIn("from_label=ctx.house_label", primary, "the first call site is the primary buy")
        self.assertIn("charge_artist_fee=False", primary)
        self.assertIn("charge_artist_fee=True", resale)
        self.assertNotIn("ctx.house_label", resale, "the second call site is the resale")
        # The tax follows the fee at both sites: neither is on a primary sale, both are on a resale.
        self.assertIn("charge_flip_tax=False", primary)
        self.assertIn("charge_flip_tax=True", resale)


class TheParameterExistsWhereItIsClaimed(unittest.TestCase):
    """A name in a doc and a name in a signature can drift; this pins both classes."""

    def test_both_transfer_methods_take_the_flag_with_the_same_default(self) -> None:
        source = GATEWAY.read_text(encoding="utf-8")
        self.assertEqual(
            source.count("charge_artist_fee: bool = True"),
            2,
            "EventChain.transfer and DryRunEventChain.transfer both declare the flag, defaulting "
            "to charging, so a caller that says nothing gets the resale behaviour",
        )

    def test_both_transfer_methods_take_the_tax_flag_with_the_same_default(self) -> None:
        source = GATEWAY.read_text(encoding="utf-8")
        self.assertEqual(
            source.count("charge_flip_tax: bool = True"),
            2,
            "the tax flag is declared on both transfer methods with the fee flag's default, so a "
            "caller that says nothing gets the resale behaviour for both payments",
        )


if __name__ == "__main__":  # pragma: no cover - a convenience, not a path a test takes
    unittest.main()
