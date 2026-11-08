"""The mutation harness: proof that the artist-fee tests can fail.

`test_artist_fee.py` asserts what the module does. This file asks the other question — if the
module did something else, would anybody notice? It is built from two tables:

- **properties**, each a function that takes a loaded module and raises `AssertionError` (or any
  other exception) if the module breaks one rule. They take the module as an argument rather
  than importing `market_swarm.artist_fee` directly, so the same property can be run against a
  modified copy;
- **mutations**, each a single source-text replacement applied to a temporary copy of
  `market_swarm/artist_fee.py`, which is then loaded under its own name with `importlib`. Every
  mutation must break at least one property. One that breaks none is a hole in the suite and
  this file **fails** naming it — it does not skip, because a skipped hole is a hole.

The unmutated source is run through the same properties as a control. Without it, a property
table that raised on everything would look like a suite that caught every mutation.

The mutations are the ones the build spec names — float division, the ceiling that killed the
Token-2022 fee, the removed fee-exceeds-price guard, the inverted zero-fee omission, the removed
self-transfer check, the swapped instruction order, the raised `MAX_FEE_BPS` and the removed
`u64` bound — plus the ones a reader would try next: a widened bincode tag, a non-writable
destination, a missing wallet-length check, a 0 price allowed through, a changed denominator and
bools accepted as rates.

No network, no validator, no key: a mutation is text, and a property is arithmetic.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from market_swarm import artist_fee

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "market_swarm" / "artist_fee.py"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")

SELLER = artist_fee.dp.base58.encode(bytes(range(1, 33)))
ARTIST = artist_fee.dp.base58.encode(bytes(range(33, 65)))
SHORT_WALLET = artist_fee.dp.base58.encode(bytes(range(1, 32)))
LONG_WALLET = artist_fee.dp.base58.encode(bytes(range(1, 34)))

PRICE = 1_000_000_000
BPS = 500
FEE = 50_000_000


# -- the property table ------------------------------------------------------


def refusal(module, call, what: str):
    """The `ArtistFeeError` a call must raise; an `AssertionError` if it raised nothing."""
    try:
        result = call()
    except module.ArtistFeeError as exc:
        return exc
    raise AssertionError(f"{what}: expected ArtistFeeError, got {result!r}")


def legs(module):
    """Two stand-ins for the instructions this module does not build."""
    return (
        module.dp.Instruction(program_id=module.dp.SYSTEM_PROGRAM, accounts=(), data=b"\x0b"),
        module.dp.Instruction(program_id=module.dp.SYSTEM_PROGRAM, accounts=(), data=b"\x0c"),
    )


def sale(module, **overrides):
    """A sale at the design's worked pair, with any argument replaced."""
    stage, move = legs(module)
    arguments = {
        "stage": stage,
        "move": move,
        "seller": SELLER,
        "artist_wallet": ARTIST,
        "price_lamports": PRICE,
        "fee_bps": BPS,
    }
    arguments.update(overrides)
    return module.sale_instructions(**arguments)


def property_arithmetic(module) -> None:
    """The pinned table, and an `int` (not a `float`, not a `bool`) coming back."""
    cases = {
        (19, 500): 0,
        (20, 500): 1,
        (1, 9_999): 0,
        (1, 10_000): 1,
        (0, 500): 0,
        (0, 10_000): 0,
        (PRICE, BPS): FEE,
        (PRICE, 0): 0,
        (PRICE, 10_000): PRICE,
    }
    for (price, bps), expected in sorted(cases.items()):
        got = module.fee_lamports(price_lamports=price, fee_bps=bps)
        assert got == expected, f"fee_lamports({price}, {bps}) = {got!r}, expected {expected}"
        assert type(got) is int, f"fee_lamports({price}, {bps}) returned {type(got).__name__}"


def property_floor_not_ceiling(module) -> None:
    """Floor, stated independently of the module's own expression.

    A ceiling is the defect that made the token fee unusable: it takes a whole unit out of a
    1-unit sale. In lamports that is the same rule, so these four cases are the whole argument.
    """
    for price, bps in ((19, 500), (20, 500), (1, 9_999), (999, 1), (0, 10_000)):
        fee = module.fee_lamports(price_lamports=price, fee_bps=bps)
        assert fee == price * bps // 10_000, f"fee_lamports({price}, {bps}) = {fee}, not floored"
    assert module.fee_lamports(price_lamports=19, fee_bps=500) == 0, "a ceiling charges 1 of 19"
    assert module.fee_lamports(price_lamports=1, fee_bps=9_999) == 0, "a ceiling takes the ticket"


def property_fee_never_exceeds_the_price(module) -> None:
    """The bound that makes floor safe: an accepted rate never charges more than the sale."""
    for price in (0, 1, 19, 20, 999, 1_000_000, PRICE, 2**64 - 1):
        for bps in (0, 1, 250, 500, 2_500, 9_999, 10_000):
            fee = module.fee_lamports(price_lamports=price, fee_bps=bps)
            assert 0 <= fee <= price, f"fee_lamports({price}, {bps}) = {fee}, outside 0..{price}"
    for bps in (10_001, 20_000, 2**40):
        try:
            fee = module.fee_lamports(price_lamports=2**64 - 1, fee_bps=bps)
        except module.ArtistFeeError:
            continue
        assert fee <= 2**64 - 1, f"{bps} bps on a full-price sale charges {fee}, above the price"


def property_constants_are_pinned(module) -> None:
    """The two constants the spec fixes, and the refusal that depends on them."""
    assert module.FEE_BPS_DENOMINATOR == 10_000, f"denominator {module.FEE_BPS_DENOMINATOR}"
    assert module.MAX_FEE_BPS == 10_000, f"MAX_FEE_BPS {module.MAX_FEE_BPS}"
    assert module.U64_MAX == 2**64 - 1, f"U64_MAX {module.U64_MAX}"
    accepted = module.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=10_000)
    assert accepted.fee_bps == 10_000
    refusal(
        module,
        lambda: module.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=10_001),
        "a rate above the maximum",
    )
    refusal(
        module,
        lambda: module.fee_lamports(price_lamports=PRICE, fee_bps=10_001),
        "a rate above the maximum",
    )


def property_zero_fee_omits_the_leg(module) -> None:
    """A zero fee is two instructions, and neither of them is a transfer."""
    stage, move = legs(module)
    for price, bps in ((PRICE, 0), (19, BPS)):
        built = module.sale_instructions(
            stage=stage,
            move=move,
            seller=SELLER,
            artist_wallet=ARTIST,
            price_lamports=price,
            fee_bps=bps,
        )
        assert len(built) == 2, f"{bps} bps on {price} lamports built {len(built)} instructions"
        assert built[0] is stage, "the stage was not the first instruction"
        assert built[1] is move, "a zero fee still inserted an instruction before the move"


def property_three_instructions_in_order(module) -> None:
    """`(stage, fee, move)`, in that order, by identity."""
    stage, move = legs(module)
    built = sale(module, stage=stage, move=move)
    assert len(built) == 3, f"a positive fee built {len(built)} instructions"
    assert built[0] is stage, "the stage must be first: the hook reads a staged price"
    assert built[2] is move, "the token move must be last: the fee is paid before the ticket"
    assert built[1] is not stage and built[1] is not move, "the middle leg is the fee transfer"


def property_fee_leg_pays_the_artist(module) -> None:
    """The middle instruction is a System transfer, seller to artist, for exactly the fee."""
    leg = sale(module)[1]
    assert leg.program_id == module.dp.SYSTEM_PROGRAM, f"program {leg.program_id}"
    assert len(leg.accounts) == 2, f"{len(leg.accounts)} accounts on the fee leg"
    source, destination = leg.accounts
    assert (source.pubkey, source.is_signer, source.is_writable) == (SELLER, True, True), (
        f"the source is {source.pubkey}, signer={source.is_signer}, writable={source.is_writable}"
    )
    assert (destination.pubkey, destination.is_signer, destination.is_writable) == (
        ARTIST,
        False,
        True,
    ), f"the destination is {destination.pubkey} with flags {destination.is_signer},{destination.is_writable}"
    assert leg.data == bytes([2, 0, 0, 0]) + FEE.to_bytes(8, "little"), f"data {leg.data.hex()}"


def property_self_transfer_refused(module) -> None:
    """An artist who is the seller is a fee that moves nothing, so it is refused."""
    error = refusal(module, lambda: sale(module, artist_wallet=SELLER), "an artist who is the seller")
    assert "artist_wallet" in str(error), f"the refusal blamed {str(error)!r}"


def property_zero_price_refused(module) -> None:
    """A staged 0 reads on chain as 'nothing staged' and is refused with 6009."""
    for price in (0, -1):
        error = refusal(module, lambda price=price: sale(module, price_lamports=price), f"a price of {price}")
        assert "price_lamports" in str(error), f"the refusal blamed {str(error)!r}"


def property_fee_beyond_u64_refused(module) -> None:
    """The sale is refused as a fee, not as a transfer amount the caller never passed."""
    error = refusal(
        module,
        lambda: sale(module, price_lamports=2**64, fee_bps=10_000),
        "a fee beyond u64",
    )
    assert "fee_lamports" in str(error), f"the refusal blamed {str(error)!r}"


def property_transfer_bounds_and_bytes(module) -> None:
    """1..2**64-1, and 12 bytes of bincode: a u32 tag of 2 then the amount."""
    for bad in (0, -1, 2**64, True, 1.0, "1"):
        refusal(
            module,
            lambda bad=bad: module.system_transfer_instruction(
                source=SELLER, destination=ARTIST, lamports=bad
            ),
            f"a transfer of {bad!r}",
        )
    for amount in (1, 255, 256, FEE, 2**64 - 1):
        instruction = module.system_transfer_instruction(
            source=SELLER, destination=ARTIST, lamports=amount
        )
        expected = bytes([2, 0, 0, 0]) + amount.to_bytes(8, "little")
        assert instruction.data == expected, (
            f"transfer data for {amount} is {instruction.data.hex()}, expected {expected.hex()}"
        )
        assert instruction.program_id == module.dp.SYSTEM_PROGRAM


def property_wallet_is_32_bytes(module) -> None:
    """Base58 is not a length check: a 31- or 33-byte string decodes happily and is wrong."""
    for bad in (SHORT_WALLET, LONG_WALLET, "", "0OIl", b"\x00" * 32):
        error = refusal(
            module,
            lambda bad=bad: module.ArtistFeePolicy(artist_wallet=bad, fee_bps=BPS),
            f"a wallet of {bad!r}",
        )
        assert "artist_wallet" in str(error), f"the refusal blamed {str(error)!r}"
    assert module.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS).artist_wallet == ARTIST


def property_bools_and_floats_refused(module) -> None:
    """`True` is an `int` in Python and a money bug in a rate, a price or an amount."""
    for bad in (True, False, 500.0):
        refusal(
            module,
            lambda bad=bad: module.fee_lamports(price_lamports=PRICE, fee_bps=bad),
            f"a rate of {bad!r}",
        )
    for bad in (True, 1.5):
        refusal(
            module,
            lambda bad=bad: module.fee_lamports(price_lamports=bad, fee_bps=BPS),
            f"a price of {bad!r}",
        )


def property_mapping_round_trip(module) -> None:
    """A policy round-trips, the field path is reported, and an unknown key is refused.

    The non-builder review of finding 42 found a mutation that survived because this property
    probed exactly one unknown key name: a module that whitelisted any *other* name looked
    innocent. The key set is a list now, including the names a reader would reach for first, so a
    whitelist that is wrong for any of them fails here.
    """
    policy = module.ArtistFeePolicy.from_mapping(
        {"artist_wallet": ARTIST, "fee_bps": BPS}, field="events[0].artist_fee"
    )
    assert policy.to_dict() == {"artist_wallet": ARTIST, "fee_bps": BPS}, f"to_dict {policy.to_dict()}"
    for unknown in ("rate", "fee", "bps", "artist", "wallet", "artistWallet", "FeeBps"):
        error = refusal(
            module,
            lambda name=unknown: module.ArtistFeePolicy.from_mapping(
                {"artist_wallet": ARTIST, "fee_bps": BPS, name: 1}, field="events[0].artist_fee"
            ),
            f"an unknown key {unknown!r}",
        )
        assert "events[0].artist_fee" in str(error) and unknown in str(error), (
            f"the message for {unknown!r} is {str(error)!r}"
        )
    error = refusal(
        module,
        lambda: module.ArtistFeePolicy.from_mapping(
            {"artist_wallet": ARTIST}, field="events[0].artist_fee"
        ),
        "a missing key",
    )
    assert "events[0].artist_fee.fee_bps" in str(error), f"the message is {str(error)!r}"


def property_the_two_constants_are_independent(module) -> None:
    """The rate bound and the denominator are two rules, not one number under two names.

    Both are 10 000 today, so dividing by the wrong one is invisible at runtime. This property
    moves `MAX_FEE_BPS` and asserts the arithmetic does not move with it: a module whose division
    used the rate bound fails here the moment the bound is retuned, which is the bug the module's
    own comment says the two names exist to prevent.
    """
    saved = module.MAX_FEE_BPS
    try:
        for raised in (20_000, 5_000):
            module.MAX_FEE_BPS = raised
            got = module.fee_lamports(price_lamports=PRICE, fee_bps=BPS)
            assert got == FEE, (
                f"with MAX_FEE_BPS = {raised}, fee_lamports({PRICE}, {BPS}) = {got!r}, expected "
                f"{FEE}: the rate bound is being used as the basis-point denominator"
            )
    finally:
        module.MAX_FEE_BPS = saved


PROPERTIES = (
    ("arithmetic", property_arithmetic),
    ("floor-not-ceiling", property_floor_not_ceiling),
    ("fee-never-exceeds-price", property_fee_never_exceeds_the_price),
    ("constants-pinned", property_constants_are_pinned),
    ("zero-fee-omits-the-leg", property_zero_fee_omits_the_leg),
    ("three-instructions-in-order", property_three_instructions_in_order),
    ("fee-leg-pays-the-artist", property_fee_leg_pays_the_artist),
    ("self-transfer-refused", property_self_transfer_refused),
    ("zero-price-refused", property_zero_price_refused),
    ("fee-beyond-u64-refused", property_fee_beyond_u64_refused),
    ("transfer-bounds-and-bytes", property_transfer_bounds_and_bytes),
    ("wallet-is-32-bytes", property_wallet_is_32_bytes),
    ("mapping-round-trip", property_mapping_round_trip),
    ("constants-independent", property_the_two_constants_are_independent),
    ("bools-and-floats-refused", property_bools_and_floats_refused),
)


# -- the mutation table ------------------------------------------------------

#: Each entry is `(name, old_text, new_text)`. `old_text` must appear exactly once in the source:
#: a table entry that no longer matches the file is a stale mutation, and this file fails on it
#: rather than silently passing.
MUTATIONS = (
    (
        "float-division",
        "    return price * bps // FEE_BPS_DENOMINATOR",
        "    return price * bps / FEE_BPS_DENOMINATOR",
    ),
    (
        "ceiling-rounding",
        "    return price * bps // FEE_BPS_DENOMINATOR",
        "    return (price * bps + FEE_BPS_DENOMINATOR - 1) // FEE_BPS_DENOMINATOR",
    ),
    (
        "fee-exceeds-price-guard-removed",
        "    return _require_int(value, field, minimum=0, maximum=MAX_FEE_BPS)",
        "    return _require_int(value, field, minimum=0)",
    ),
    (
        "zero-fee-omission-inverted",
        "    if fee == 0:\n        return (stage, move)",
        "    if fee < 0:\n        return (stage, move)",
    ),
    (
        "self-transfer-allowed",
        "    if policy.artist_wallet == seller:",
        '    if policy.artist_wallet == "":',
    ),
    (
        "instruction-order-swapped",
        "    return (stage, transfer, move)",
        "    return (transfer, stage, move)",
    ),
    ("max-fee-bps-raised", "MAX_FEE_BPS = 10_000", "MAX_FEE_BPS = 20_000"),
    ("fee-u64-bound-removed", "    if fee > U64_MAX:", "    if fee > 2**200:"),
    (
        "transfer-u64-bound-removed",
        '    amount = _require_int(lamports, "lamports", minimum=1, maximum=U64_MAX)',
        '    amount = _require_int(lamports, "lamports", minimum=1)',
    ),
    (
        "bincode-tag-widened",
        '    data = SYSTEM_TAG_TRANSFER.to_bytes(4, "little") + amount.to_bytes(8, "little")',
        '    data = SYSTEM_TAG_TRANSFER.to_bytes(8, "little") + amount.to_bytes(8, "little")',
    ),
    (
        "destination-not-writable",
        "        accounts=(dp.AccountMeta(source, True, True), dp.AccountMeta(destination, False, True)),",
        "        accounts=(dp.AccountMeta(source, True, True), dp.AccountMeta(destination, False, False)),",
    ),
    ("wallet-length-check-removed", "    if len(raw) != _PUBKEY_LEN:", "    if False:"),
    ("zero-price-check-loosened", "    if price <= 0:", "    if price < 0:"),
    ("denominator-changed", "FEE_BPS_DENOMINATOR = 10_000", "FEE_BPS_DENOMINATOR = 1_000"),
    (
        "bools-accepted",
        "    if isinstance(value, bool) or not isinstance(value, int):",
        "    if not isinstance(value, int):",
    ),
    # The two the non-builder review of finding 42 wrote and this table did not catch. They are
    # here so the properties added beside them are proven to work: a mutation in the table is a
    # claim that some property notices it.
    (
        "denominator-swapped-for-the-rate-bound",
        "    return price * bps // FEE_BPS_DENOMINATOR",
        "    return price * bps // MAX_FEE_BPS",
    ),
    (
        "unknown-key-whitelist-widened",
        "        unknown = sorted(set(raw) - _POLICY_FIELDS)",
        '        unknown = sorted(set(raw) - {"fee"})',
    ),
)

#: The eight the build spec names. Named separately so deleting one is a failing test rather
#: than a quietly shorter table.
REQUIRED_MUTATIONS = frozenset(
    {
        "float-division",
        "ceiling-rounding",
        "fee-exceeds-price-guard-removed",
        "zero-fee-omission-inverted",
        "self-transfer-allowed",
        "instruction-order-swapped",
        "max-fee-bps-raised",
        "fee-u64-bound-removed",
    }
)


# -- the harness -------------------------------------------------------------


def failures(module) -> list[str]:
    """Every property the loaded module breaks, by property name and reason."""
    broken = []
    for name, property_function in PROPERTIES:
        try:
            property_function(module)
        except Exception as exc:  # noqa: BLE001 - any breakage counts against the mutant
            broken.append(f"{name} ({type(exc).__name__}: {exc})")
    return broken


class MutationHarness(unittest.TestCase):
    """Loads temp copies of `artist_fee.py` and runs the property table against each."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._directory = tempfile.TemporaryDirectory(prefix="artist-fee-mutants-")
        cls.directory = Path(cls._directory.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._directory.cleanup()

    def load(self, text: str, label: str):
        """A module object from `text`, loaded from a file of its own.

        The copy computes its own `REPO_ROOT` from `__file__` and puts a temporary directory on
        `sys.path` while it imports. That is restored straight afterwards so one mutant cannot
        change the import path the next one sees. The module is registered in `sys.modules` for
        the duration of the load because `dataclasses` resolves a class's namespace through
        `sys.modules[cls.__module__]`, and a module object that is not registered there makes
        `@dataclass` raise before the mutation can be tested.
        """
        path = self.directory / f"{label}.py"
        path.write_text(text, encoding="utf-8")
        module_name = f"artist_fee_mutant_{label}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec is not None and spec.loader is not None, f"could not load {label}"
        module = importlib.util.module_from_spec(spec)
        saved_path = list(sys.path)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(module_name, None)
            sys.path[:] = saved_path
        return module

    def test_the_control_passes_the_same_properties(self) -> None:
        """The unmutated source passes. Without this, a table that raised on everything would
        look like a suite that caught every mutation."""
        broken = failures(self.load(SOURCE, "control"))
        self.assertEqual(broken, [], f"the property table rejects the real module: {broken}")

    def test_every_mutation_is_caught(self) -> None:
        """Each mutation must break at least one property, and one that does not is named."""
        inapplicable: list[str] = []
        survivors: list[str] = []
        for name, old, new in MUTATIONS:
            occurrences = SOURCE.count(old)
            if occurrences != 1:
                inapplicable.append(f"{name}: its source text appears {occurrences} times")
                continue
            module = self.load(SOURCE.replace(old, new, 1), name.replace("-", "_"))
            if not failures(module):
                survivors.append(name)
        self.assertEqual(inapplicable, [], f"stale mutations that no longer apply: {inapplicable}")
        self.assertEqual(
            survivors,
            [],
            f"these mutations survived, so the suite has a hole in it: {survivors}",
        )

    def test_the_table_covers_the_mutations_the_spec_names(self) -> None:
        missing = REQUIRED_MUTATIONS - {name for name, _, _ in MUTATIONS}
        self.assertEqual(missing, set(), f"the table dropped a required mutation: {sorted(missing)}")

    def test_every_mutation_changes_something(self) -> None:
        for name, old, new in MUTATIONS:
            with self.subTest(mutation=name):
                self.assertNotEqual(old, new, f"{name} replaces text with itself")

    def test_a_change_that_breaks_nothing_is_reported_as_a_survivor(self) -> None:
        """The detection the harness turns on itself: a source edit no property sees is a
        survivor, which is exactly what `test_every_mutation_is_caught` fails on."""
        harmless = SOURCE.replace("#: The largest rate", "#: the largest rate", 1)
        self.assertNotEqual(harmless, SOURCE, "the behaviour-preserving control did not apply")
        self.assertEqual(failures(self.load(harmless, "harmless")), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
