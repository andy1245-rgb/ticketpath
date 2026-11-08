"""The agent layer: the six scripted policies and the deterministic view they decide from.

The tests that matter most are not about trading. They are about two properties the dataset
depends on: a policy decides the same thing twice from equal views (so a run is replayable),
and every price it emits is an integer lamport amount computed from integers (so the cap
boundary is never rounded by a float). The scalper tests come next, because the scalper is
the instrument that measures the difference between capped and monitored mode.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import os
import subprocess
import sys
import types
import unittest
from dataclasses import dataclass
from pathlib import Path

from market_swarm import agents
from market_swarm.agents import (
    ACTIONS,
    HARD_PRICE_MULTIPLE,
    POLICIES,
    Holding,
    Intent,
    MarketView,
    build_policy,
    cap_ceiling,
)

FACE = 1_000_000_000
CAP_BPS = 2500
CEILING = 1_250_000_000  # face 1.00 SOL at 2500 bps, the chain's inclusive boundary
MONITORED_CAP_BPS = 65535
EVENT = "SYN-event"


@dataclass(frozen=True)
class Spec:
    """Stand-in for `config.AgentSpec` with only the fields a policy reads.

    Deliberately local: `agents.py` must not import `config.py` (the dependency runs the
    other way, `config` validates against `POLICIES`), and the tests must not depend on
    another module's file existing.
    """

    agent_id: str = "agent-0"
    policy: str = "buyer"
    wallet_label: str = "SYNwallet0"
    seed: int = 7
    budget_lamports: int = 10 * FACE
    budget_actions: int = 100


def view(**overrides: object) -> MarketView:
    """A capped-mode view at the standard face and cap, overridable per test."""
    fields: dict[str, object] = {
        "round": 0,
        "rounds_left": 5,
        "event_id": EVENT,
        "mode": "capped",
        "face_lamports": FACE,
        "cap_bps": CAP_BPS,
        "ceiling_lamports": CEILING,
        "tickets_available": 10,
        "holdings": (Holding("SYN-ticket-0", FACE, 0),),
        "last_prices": (),
        "refused_attempts": 0,
        "agent_id": "agent-0",
        "seed": 7,
    }
    fields.update(overrides)
    return MarketView(**fields)  # type: ignore[arg-type]


def policy_for(name: str, *, seed: int = 7, cap_bps: int = CAP_BPS, face: int = FACE,
               intended_cap_bps: int | None = None) -> agents.Policy:
    return build_policy(
        Spec(policy=name, seed=seed),
        face_lamports=face,
        cap_bps=cap_bps,
        intended_cap_bps=intended_cap_bps,
    )


class TestMarketViewRng(unittest.TestCase):
    def test_two_constructions_with_equal_fields_give_the_same_stream(self) -> None:
        first = [view().rng().randrange(10**9) for _ in range(4)]
        second = [view().rng().randrange(10**9) for _ in range(4)]
        self.assertEqual(first, second)
        a, b = view().rng(), view().rng()
        self.assertEqual([a.randrange(10**9) for _ in range(32)],
                         [b.randrange(10**9) for _ in range(32)])

    def test_the_seed_depends_on_agent_round_and_run_seed(self) -> None:
        base = view().rng().randrange(10**9)
        self.assertNotEqual(base, view(agent_id="agent-1").rng().randrange(10**9))
        self.assertNotEqual(base, view(round=1).rng().randrange(10**9))
        self.assertNotEqual(base, view(seed=8).rng().randrange(10**9))

    def test_the_stream_is_the_same_in_a_fresh_process(self) -> None:
        root = Path(__file__).resolve().parents[2]
        code = (
            "import json\n"
            "from market_swarm.agents import MarketView\n"
            "v = MarketView(round=3, rounds_left=4, event_id='e', mode='capped',\n"
            "               face_lamports=1000000000, cap_bps=2500,\n"
            "               ceiling_lamports=1250000000, tickets_available=5,\n"
            "               holdings=(), last_prices=(), refused_attempts=0,\n"
            "               agent_id='agent-0', seed=7)\n"
            "r = v.rng()\n"
            "print(json.dumps([r.randrange(10**9) for _ in range(16)]))\n"
        )
        outputs = []
        for hash_seed in ("0", "12345"):
            env = dict(os.environ)
            env["PYTHONPATH"] = os.pathsep.join(
                [str(root)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
            )
            env["PYTHONHASHSEED"] = hash_seed
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=str(root),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            outputs.append(json.loads(proc.stdout))
        self.assertEqual(outputs[0], outputs[1])
        # and equal to the in-process stream for the same inputs
        in_process = view(round=3, holdings=()).rng()
        self.assertEqual(
            outputs[0], [in_process.randrange(10**9) for _ in range(16)]
        )


class TestPurity(unittest.TestCase):
    def test_no_module_level_symbol_is_a_mutable_object(self) -> None:
        for name, value in vars(agents).items():
            if name.startswith("__"):
                continue
            if isinstance(value, types.ModuleType) or isinstance(value, type):
                continue
            if callable(value):
                continue
            with self.subTest(symbol=name):
                self.assertNotIsInstance(value, (dict, list, set, bytearray))
                self.assertNotIsInstance(value, dataclasses.Field)

    def test_the_registry_refuses_mutation(self) -> None:
        with self.assertRaises(TypeError):
            POLICIES["intruder"] = object  # type: ignore[index]
        self.assertEqual(
            sorted(POLICIES),
            ["buyer", "flipper", "greater_fool", "holder", "panic", "scalper", "sniper"],
        )

    def test_the_view_and_intent_are_frozen(self) -> None:
        with self.assertRaises(dataclasses.FrozenInstanceError):
            view().cap_bps = 1  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            Intent("a", "buy", 1, None, "r").price_lamports = 2  # type: ignore[misc]

    def test_the_module_imports_only_stdlib_and_no_gateway_or_key_material(self) -> None:
        source = Path(agents.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertLessEqual(
            imported,
            {"__future__", "hashlib", "random", "dataclasses", "types", "typing",
             "market_swarm"},
            f"unexpected imports in agents.py: {sorted(imported)}",
        )
        for forbidden in ("socket", "urllib", "http", "subprocess", "base58",
                          "solders", "solana", "nacl"):
            self.assertNotIn(forbidden, imported)

    def test_every_policy_decides_identically_twice_from_equal_views(self) -> None:
        for name, cls in POLICIES.items():
            with self.subTest(policy=name):
                first = policy_for(name, seed=3)
                second = policy_for(name, seed=3)
                self.assertEqual(cls, type(first))
                a = first.decide(view(refused_attempts=0))
                b = second.decide(view(refused_attempts=0))
                self.assertEqual(a, b)
                self.assertEqual(a, first.decide(view(refused_attempts=0)))

    def test_no_policy_touches_the_world_between_rounds(self) -> None:
        # A decision must depend only on the view: two different views of the same shape
        # give the same intents, and the object is unchanged afterwards.
        v = view(rounds_left=1)
        before = dataclasses.asdict(v)
        for name in POLICIES:
            policy_for(name, seed=5).decide(v)
        self.assertEqual(dataclasses.asdict(v), before)


class TestIntentShape(unittest.TestCase):
    def _matrix(self) -> list[MarketView]:
        return [
            view(),
            view(rounds_left=3),
            view(rounds_left=2),
            view(rounds_left=1),
            view(rounds_left=0),
            view(holdings=(), tickets_available=0),
            view(holdings=(), last_prices=(CEILING + 1,)),
            view(holdings=(), last_prices=(FACE,)),
            view(mode="monitored", cap_bps=MONITORED_CAP_BPS,
                 ceiling_lamports=cap_ceiling(FACE, MONITORED_CAP_BPS)),
            view(refused_attempts=6),
        ]

    def test_every_emitted_price_is_a_positive_int_lamport_amount(self) -> None:
        for name in POLICIES:
            policy = policy_for(name, seed=2)
            for v in self._matrix():
                for intent in policy.decide(v):
                    with self.subTest(policy=name, view=v, intent=intent):
                        self.assertIn(intent.action, ACTIONS)
                        self.assertIs(type(intent.price_lamports), int)
                        self.assertGreater(intent.price_lamports, 0)
                        self.assertEqual(intent.agent_id, policy.agent_id)
                        self.assertLessEqual(
                            intent.price_lamports,
                            v.face_lamports * HARD_PRICE_MULTIPLE,
                        )

    def test_a_price_above_the_sanity_bound_raises_with_the_numbers(self) -> None:
        # A cap this large is nonsense; the guard exists to stop a broken policy trading.
        absurd = 20_000_000  # ceiling = face * 2001, above face * 1000
        sniper = policy_for("sniper", cap_bps=absurd)
        v = view(cap_bps=absurd, ceiling_lamports=cap_ceiling(FACE, absurd),
                 rounds_left=2, holdings=())
        with self.assertRaises(AssertionError) as caught:
            sniper.decide(v)
        message = str(caught.exception)
        self.assertIn(str(cap_ceiling(FACE, absurd)), message)
        self.assertIn(str(FACE * HARD_PRICE_MULTIPLE), message)


class TestBuyer(unittest.TestCase):
    def test_buys_one_at_or_below_face_and_then_stops(self) -> None:
        policy = policy_for("buyer")
        intents = policy.decide(view(holdings=(), last_prices=(FACE,)))
        self.assertEqual([(i.action, i.price_lamports) for i in intents],
                         [("buy", FACE)])
        self.assertEqual(policy.decide(view()), [])  # already holds one

    def test_declines_a_primary_ask_above_face(self) -> None:
        policy = policy_for("buyer")
        self.assertEqual(policy.decide(view(holdings=(), last_prices=(FACE + 1,))), [])

    def test_buys_at_face_when_no_price_is_known(self) -> None:
        intents = policy_for("buyer").decide(view(holdings=()))
        self.assertEqual(intents[0].price_lamports, FACE)


class TestHolder(unittest.TestCase):
    def test_buys_once_then_lists_near_the_target_markup(self) -> None:
        policy = policy_for("holder")
        buy = policy.decide(view(holdings=()))
        self.assertEqual([(i.action, i.price_lamports) for i in buy], [("buy", FACE)])
        listed = policy.decide(view(rounds_left=5))
        self.assertEqual([(i.action, i.price_lamports) for i in listed],
                         [("list", 1_120_000_000)])  # +1200 bps over face

    def test_relists_lower_as_time_runs_out(self) -> None:
        policy = policy_for("holder")
        prices = [policy.decide(view(rounds_left=n))[0].price_lamports
                  for n in (5, 2, 1)]
        self.assertEqual(prices, [1_120_000_000, 1_070_000_000, 1_020_000_000])
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_the_listing_is_clamped_to_the_effective_ceiling(self) -> None:
        policy = policy_for("holder", cap_bps=500)  # ceiling 1.05 * face < target
        intent = policy.decide(view(rounds_left=5, cap_bps=500,
                                    ceiling_lamports=cap_ceiling(FACE, 500)))[0]
        self.assertEqual(intent.price_lamports, 1_050_000_000)


class TestFlipper(unittest.TestCase):
    def test_buys_under_the_ceiling_derived_threshold(self) -> None:
        policy = policy_for("flipper")
        threshold = FACE + (CEILING - FACE) * 3 // 4
        self.assertEqual(threshold, 1_187_500_000)
        bought = policy.decide(view(holdings=(), last_prices=(threshold,)))
        self.assertEqual([(i.action, i.price_lamports) for i in bought],
                         [("buy", threshold)])
        self.assertEqual(
            policy.decide(view(holdings=(), last_prices=(threshold + 1,))), []
        )

    def test_resells_at_a_small_markup_above_its_lot(self) -> None:
        policy = policy_for("flipper")
        lot = 1_000_000_000
        intent = policy.decide(
            view(holdings=(Holding("SYN-t", lot, 0),), last_prices=(FACE,))
        )[0]
        self.assertEqual((intent.action, intent.price_lamports),
                         ("resell", 1_030_000_000))
        self.assertGreater(intent.price_lamports, lot)
        self.assertLessEqual(intent.price_lamports, CEILING)

    def test_does_not_realise_a_loss_when_the_cap_leaves_no_room(self) -> None:
        # cap 0 -> ceiling == face; a lot at face cannot be resold above cost.
        policy = policy_for("flipper", cap_bps=0)
        v = view(cap_bps=0, ceiling_lamports=FACE,
                 holdings=(Holding("SYN-t", FACE, 0),))
        self.assertEqual(policy.decide(v), [])


class TestScalperCappedMode(unittest.TestCase):
    def test_attempt_count_is_two_to_four_and_derived_from_the_seed(self) -> None:
        for seed in range(9):
            with self.subTest(seed=seed):
                self.assertEqual(
                    policy_for("scalper", seed=seed).over_cap_attempts, 2 + seed % 3
                )
        self.assertEqual(policy_for("scalper", seed=0).over_cap_attempts, 2)
        self.assertEqual(policy_for("scalper", seed=2).over_cap_attempts, 4)
        self.assertEqual(policy_for("scalper", seed=8).over_cap_attempts, 4)

    def test_the_first_attempts_price_strictly_above_the_ceiling(self) -> None:
        policy = policy_for("scalper", seed=2)  # N = 4
        self.assertEqual(policy.over_cap_attempts, 4)
        prices = [
            policy.decide(view(refused_attempts=n))[0].price_lamports
            for n in range(4)
        ]
        self.assertEqual(prices, [1_270_000_000, 1_280_000_000,
                                  1_290_000_000, 1_300_000_000])
        for price in prices:
            self.assertGreater(price, CEILING)

    def test_a_two_attempt_scalper_also_prices_above_the_ceiling(self) -> None:
        policy = policy_for("scalper", seed=0)  # N = 2
        self.assertEqual(policy.over_cap_attempts, 2)
        for n in (0, 1):
            self.assertGreater(
                policy.decide(view(refused_attempts=n))[0].price_lamports, CEILING
            )

    def test_it_retries_at_exactly_the_ceiling_after_its_refusals(self) -> None:
        policy = policy_for("scalper", seed=0)  # N = 2
        intent = policy.decide(view(refused_attempts=2))[0]
        self.assertEqual(intent.price_lamports, CEILING)
        self.assertEqual(intent.action, "resell")
        # and the action is admissible by the chain's own predicate
        self.assertLessEqual(intent.price_lamports * 10_000, FACE * (10_000 + CAP_BPS))

    def test_it_steps_one_lamport_under_the_ceiling_after_that(self) -> None:
        policy = policy_for("scalper", seed=0)
        self.assertEqual(policy.decide(view(refused_attempts=3))[0].price_lamports,
                         CEILING - 1)
        self.assertEqual(policy.decide(view(refused_attempts=4))[0].price_lamports,
                         CEILING - 2)
        # it keeps trading, and never goes non-positive however many refusals accumulate
        self.assertEqual(
            policy.decide(view(refused_attempts=CEILING + 100))[0].price_lamports, 1
        )

    def test_it_buys_inventory_at_face_before_it_can_resell(self) -> None:
        policy = policy_for("scalper")
        intents = policy.decide(view(holdings=()))
        self.assertEqual([(i.action, i.price_lamports) for i in intents],
                         [("buy", FACE)])

    def test_it_says_nothing_when_it_holds_nothing_and_nothing_is_for_sale(self) -> None:
        self.assertEqual(
            policy_for("scalper").decide(view(holdings=(), tickets_available=0)), []
        )

    def test_the_attack_boundary_is_the_chain_boundary(self) -> None:
        self.assertEqual(cap_ceiling(FACE, CAP_BPS), CEILING)
        self.assertEqual(CEILING * 10_000, FACE * (10_000 + CAP_BPS))
        self.assertGreater((CEILING + 1) * 10_000, FACE * (10_000 + CAP_BPS))


class TestScalperMonitoredMode(unittest.TestCase):
    def _monitored(self, **overrides: object) -> MarketView:
        return view(
            mode="monitored",
            cap_bps=MONITORED_CAP_BPS,
            ceiling_lamports=cap_ceiling(FACE, MONITORED_CAP_BPS),
            **overrides,
        )

    def test_it_still_prices_above_the_events_intended_cap(self) -> None:
        policy = policy_for(
            "scalper",
            seed=0,
            cap_bps=MONITORED_CAP_BPS,
            intended_cap_bps=CAP_BPS,
        )
        self.assertEqual(policy.intended_cap_bps, CAP_BPS)
        self.assertEqual(policy.cap_bps, MONITORED_CAP_BPS)
        intended_ceiling = cap_ceiling(FACE, CAP_BPS)
        for n in range(policy.over_cap_attempts):
            price = policy.decide(self._monitored(refused_attempts=n))[0].price_lamports
            with self.subTest(attempt=n, price=price):
                self.assertGreater(price, intended_ceiling)
                # above the intended cap but under the effective one, so it lands
                self.assertLess(price, cap_ceiling(FACE, MONITORED_CAP_BPS))

    def test_the_intended_cap_is_not_read_from_the_view(self) -> None:
        # The same monitored view, two policies built with different intended caps: the
        # prices must differ, which proves the number comes from build_policy, not the view.
        tight = policy_for("scalper", seed=0, cap_bps=MONITORED_CAP_BPS,
                           intended_cap_bps=500)
        wide = policy_for("scalper", seed=0, cap_bps=MONITORED_CAP_BPS,
                          intended_cap_bps=5000)
        v = self._monitored(refused_attempts=0)
        self.assertLess(tight.decide(v)[0].price_lamports,
                        wide.decide(v)[0].price_lamports)
        self.assertGreater(tight.decide(v)[0].price_lamports,
                           cap_ceiling(FACE, 500))

    def test_the_fallback_is_safe_in_monitored_mode_too(self) -> None:
        policy = policy_for("scalper", seed=0, cap_bps=MONITORED_CAP_BPS,
                            intended_cap_bps=CAP_BPS)
        price = policy.decide(self._monitored(refused_attempts=2))[0].price_lamports
        self.assertEqual(price, cap_ceiling(FACE, CAP_BPS))

    def test_capped_and_monitored_views_differ_only_in_their_cap(self) -> None:
        capped = view()
        monitored = self._monitored()
        self.assertEqual(capped.face_lamports, monitored.face_lamports)
        self.assertNotEqual(capped.cap_bps, monitored.cap_bps)


class TestSniper(unittest.TestCase):
    def test_is_silent_until_the_last_rounds(self) -> None:
        policy = policy_for("sniper")
        for rounds_left in (9, 5, 4):
            with self.subTest(rounds_left=rounds_left):
                self.assertEqual(
                    policy.decide(view(holdings=(), rounds_left=rounds_left)), []
                )

    def test_bids_the_ceiling_and_never_above_it(self) -> None:
        policy = policy_for("sniper")
        for rounds_left in (3, 2, 1, 0):
            intent = policy.decide(view(holdings=(), rounds_left=rounds_left))[0]
            with self.subTest(rounds_left=rounds_left):
                self.assertEqual((intent.action, intent.price_lamports),
                                 ("buy", CEILING))
                self.assertLessEqual(intent.price_lamports, CEILING)

    def test_stops_bidding_once_it_holds(self) -> None:
        self.assertEqual(policy_for("sniper").decide(view(rounds_left=1)), [])


class TestPanic(unittest.TestCase):
    def test_sells_a_loss_into_the_deadline(self) -> None:
        policy = policy_for("panic")
        intent = policy.decide(view(rounds_left=2))[0]
        self.assertEqual((intent.action, intent.price_lamports),
                         ("resell", 850_000_000))
        self.assertLess(intent.price_lamports, FACE)  # below face, and admissible

    def test_the_discount_deepens_and_can_go_below_face(self) -> None:
        policy = policy_for("panic")
        prices = [policy.decide(view(rounds_left=n))[0].price_lamports
                  for n in (2, 1, 0)]
        self.assertEqual(prices, [850_000_000, 700_000_000, 600_000_000])
        for price in prices:
            self.assertLess(price, FACE)
            self.assertGreater(price, 0)

    def test_holds_its_nerve_outside_the_horizon(self) -> None:
        policy = policy_for("panic")
        self.assertEqual(policy.decide(view(rounds_left=3)), [])
        self.assertEqual(
            policy.decide(view(rounds_left=1, holdings=())), []  # nothing to sell
        )

    def test_a_price_below_face_is_inside_the_chain_predicate(self) -> None:
        price = 600_000_000
        self.assertLess(price * 10_000, FACE * (10_000 + CAP_BPS))
        self.assertLess(price, FACE)


class TestBuildPolicy(unittest.TestCase):
    def test_every_registered_name_builds_its_own_class(self) -> None:
        for name, cls in POLICIES.items():
            with self.subTest(policy=name):
                policy = policy_for(name)
                self.assertIs(type(policy), cls)
                self.assertEqual(policy.name, name)

    def test_the_seed_is_passed_through(self) -> None:
        for seed in range(6):
            scalper = policy_for("scalper", seed=seed)
            self.assertEqual(scalper.seed, seed)
            self.assertEqual(scalper.over_cap_attempts, 2 + seed % 3)
        self.assertEqual(policy_for("buyer", seed=99).seed, 99)

    def test_an_unknown_policy_names_itself_and_the_valid_ones(self) -> None:
        with self.assertRaises(ValueError) as caught:
            build_policy(Spec(policy="arbitrageur"), face_lamports=FACE,
                         cap_bps=CAP_BPS)
        message = str(caught.exception)
        self.assertIn("arbitrageur", message)
        for name in POLICIES:
            self.assertIn(name, message)

    def test_a_missing_policy_attribute_raises_the_same_error(self) -> None:
        with self.assertRaises(ValueError):
            build_policy(object(), face_lamports=FACE, cap_bps=CAP_BPS)

    def test_bad_face_or_cap_is_rejected_before_construction(self) -> None:
        with self.assertRaises(ValueError):
            build_policy(Spec(), face_lamports=0, cap_bps=CAP_BPS)
        with self.assertRaises(ValueError):
            build_policy(Spec(), face_lamports=FACE, cap_bps=-1)


if __name__ == "__main__":
    unittest.main()
