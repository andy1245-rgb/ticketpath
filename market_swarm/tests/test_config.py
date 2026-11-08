"""The run config: the frozen specs, the cap arithmetic, and the loader's refusals.

The cap tests check the Python arithmetic against the on-chain predicate itself
(`programs/cap_hook/src/lib.rs`), not against a remembered number: the ceiling is
admitted and one lamport above it is refused.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from market_swarm.config import (
    AgentSpec,
    CLUSTERS,
    ConfigError,
    EventSpec,
    PROGRAM_CLUSTERS,
    PROGRAM_DEFAULT,
    PROGRAMS,
    RunConfig,
    U16_MAX,
    ceiling_lamports,
    effective_cap_bps,
    load_run_config,
    run_id,
)


def _agent(**overrides) -> dict:
    base = {
        "agent_id": "a1",
        "policy": "buyer",
        "wallet_label": "wallet-a1",
        "seed": 7,
        "budget_lamports": 1_000,
        "budget_actions": 5,
    }
    base.update(overrides)
    return base


def _event(**overrides) -> dict:
    base = {
        "event_id": "evt1",
        "face_lamports": 1_000_000_000,
        "mode": "capped",
        "cap_bps": 2500,
        "tickets": 10,
        "rounds": 4,
        "round_seconds": 60,
    }
    base.update(overrides)
    return base


def _config(**overrides) -> dict:
    base = {
        "cluster": "local",
        "events": [_event()],
        "agents": [_agent()],
        "total_budget_lamports": 1_000,
        "total_budget_actions": 5,
    }
    base.update(overrides)
    return base


def _load(config) -> RunConfig:
    """Write a config to a temp file and load it, exactly as the CLI will."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return load_run_config(path)


class TestSpecsAreFrozen(unittest.TestCase):
    def test_an_agent_spec_cannot_be_mutated(self) -> None:
        spec = _load(_config()).agents[0]
        with self.assertRaises(FrozenInstanceError):
            spec.budget_lamports = 1  # type: ignore[misc]

    def test_an_event_spec_cannot_be_mutated(self) -> None:
        spec = _load(_config()).events[0]
        with self.assertRaises(FrozenInstanceError):
            spec.cap_bps = 0  # type: ignore[misc]

    def test_a_run_config_cannot_be_mutated(self) -> None:
        config = _load(_config())
        with self.assertRaises(FrozenInstanceError):
            config.cluster = "devnet"  # type: ignore[misc]

    def test_events_and_agents_are_tuples(self) -> None:
        config = _load(_config())
        self.assertIsInstance(config.events, tuple)
        self.assertIsInstance(config.agents, tuple)


class TestEffectiveCapBps(unittest.TestCase):
    def test_capped_returns_the_cap_it_was_given(self) -> None:
        self.assertEqual(effective_cap_bps("capped", 2500), 2500)
        self.assertEqual(effective_cap_bps("capped", 0), 0)
        self.assertEqual(effective_cap_bps("capped", U16_MAX), 65535)

    def test_monitored_returns_the_field_maximum_and_ignores_the_cap(self) -> None:
        self.assertEqual(effective_cap_bps("monitored", None), 65535)
        self.assertEqual(effective_cap_bps("monitored", 2500), 65535)

    def test_capped_without_a_cap_raises_and_names_the_field(self) -> None:
        with self.assertRaises(ValueError) as caught:
            effective_cap_bps("capped", None)
        self.assertIn("cap_bps", str(caught.exception))

    def test_a_cap_outside_the_u16_field_raises(self) -> None:
        for bad in (-1, 65536):
            with self.subTest(bad=bad), self.assertRaises(ValueError) as caught:
                effective_cap_bps("capped", bad)
            self.assertIn("cap_bps", str(caught.exception))

    def test_a_non_integer_cap_raises(self) -> None:
        for bad in (2500.0, True, "2500"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                effective_cap_bps("capped", bad)

    def test_an_unknown_mode_raises(self) -> None:
        with self.assertRaises(ValueError) as caught:
            effective_cap_bps("mainnet", 2500)
        self.assertIn("mode", str(caught.exception))


class TestCeilingMatchesTheOnChainPredicate(unittest.TestCase):
    FACE = 1_000_000_000
    CAP_BPS = 2500

    def test_the_known_ceiling(self) -> None:
        self.assertEqual(ceiling_lamports(self.FACE, self.CAP_BPS), 1_250_000_000)

    def test_the_ceiling_is_admitted_and_one_lamport_above_is_refused(self) -> None:
        # The predicate, exactly as programs/cap_hook/src/lib.rs states it:
        # price * 10_000 <= face * (10_000 + cap_bps), both sides in u128.
        ceiling = ceiling_lamports(self.FACE, self.CAP_BPS)
        rhs = self.FACE * (10_000 + self.CAP_BPS)
        self.assertLessEqual(ceiling * 10_000, rhs)
        self.assertGreater((ceiling + 1) * 10_000, rhs)

    def test_a_zero_cap_admits_only_face(self) -> None:
        self.assertEqual(ceiling_lamports(self.FACE, 0), self.FACE)
        self.assertGreater((self.FACE + 1) * 10_000, self.FACE * 10_000)

    def test_a_floor_is_taken_not_a_rounding(self) -> None:
        # face * 1.0001 is not an integer number of lamports; the floor is the largest
        # price the integer predicate admits.
        ceiling = ceiling_lamports(9, 1)  # 9 * 10001 // 10000 = 9.0009 -> 9
        self.assertEqual(ceiling, 9)
        self.assertGreater((ceiling + 1) * 10_000, 9 * (10_000 + 1))

    def test_the_result_is_an_int_at_u64_sized_faces(self) -> None:
        # A u64 product wraps on chain, which is why the hook casts to u128; Python does
        # not wrap, and this asserts the arithmetic stays exact and integral anyway.
        face = 2**64 - 1
        ceiling = ceiling_lamports(face, U16_MAX)
        self.assertIs(type(ceiling), int)
        self.assertEqual(ceiling, face * (10_000 + U16_MAX) // 10_000)
        self.assertGreater(ceiling, face)

    def test_bad_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            ceiling_lamports(-1, 2500)
        with self.assertRaises(ValueError):
            ceiling_lamports(self.FACE, 65536)
        with self.assertRaises(ValueError):
            ceiling_lamports(self.FACE, 2500.0)


class TestRunId(unittest.TestCase):
    PATTERN = re.compile(r"^sw\d{8}T\d{6}Z[0-9a-f]{4}$")

    def test_the_shape_is_sw_timestamp_and_four_hex_characters(self) -> None:
        self.assertRegex(run_id(), self.PATTERN)

    def test_two_calls_differ(self) -> None:
        self.assertNotEqual(run_id(), run_id())

    def test_an_injected_clock_is_used_for_the_timestamp(self) -> None:
        # 2026-11-07T18:50:00Z == 1794077400 seconds since the epoch.
        self.assertTrue(run_id(now=1_794_077_400).startswith("sw20261107T185000Z"))


class TestLoadRunConfig(unittest.TestCase):
    def test_a_minimal_config_loads_with_explicit_defaults(self) -> None:
        config = _load(_config())
        self.assertTrue(config.run_id.startswith("sw"))
        self.assertEqual(config.cluster, "local")
        self.assertEqual(config.kill_after_seconds, None)
        self.assertEqual(config.out_dir, Path("market_swarm/runs"))
        self.assertIs(config.dry_run, False)
        self.assertEqual(config.seed, 0)
        self.assertEqual(config.total_budget_lamports, 1_000)
        self.assertEqual(config.total_budget_actions, 5)

    def test_every_declared_field_is_read(self) -> None:
        config = _load(
            _config(
                run_id="run-fixed",
                cluster="devnet",
                kill_after_seconds=2.5,
                out_dir="somewhere/else",
                dry_run=True,
                seed=42,
                total_budget_lamports=9_000,
                total_budget_actions=90,
            )
        )
        self.assertEqual(config.run_id, "run-fixed")
        self.assertEqual(config.cluster, "devnet")
        self.assertEqual(config.kill_after_seconds, 2.5)
        self.assertEqual(config.out_dir, Path("somewhere/else"))
        self.assertIs(config.dry_run, True)
        self.assertEqual(config.seed, 42)

        agent = config.agents[0]
        self.assertEqual(agent.agent_id, "a1")
        self.assertEqual(agent.policy, "buyer")
        self.assertEqual(agent.wallet_label, "wallet-a1")
        self.assertEqual(agent.seed, 7)
        self.assertEqual(agent.budget_lamports, 1_000)
        self.assertEqual(agent.budget_actions, 5)

        event = config.events[0]
        self.assertEqual(event.event_id, "evt1")
        self.assertEqual(event.face_lamports, 1_000_000_000)
        self.assertEqual(event.mode, "capped")
        self.assertEqual(event.cap_bps, 2500)
        self.assertEqual(event.tickets, 10)
        self.assertEqual(event.rounds, 4)
        self.assertEqual(event.round_seconds, 60)

    def test_a_monitored_event_needs_no_cap(self) -> None:
        event = _load(_config(events=[_event(mode="monitored", cap_bps=None)])).events[0]
        self.assertEqual(event.mode, "monitored")
        self.assertIsNone(event.cap_bps)

    def test_overrides_are_applied_and_validated_like_file_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text(json.dumps(_config()), encoding="utf-8")
            config = load_run_config(path, overrides={"cluster": "devnet", "seed": 3})
            self.assertEqual(config.cluster, "devnet")
            self.assertEqual(config.seed, 3)
            with self.assertRaises(ConfigError) as caught:
                load_run_config(path, overrides={"cluster": "mainnet"})
            self.assertIn("cluster", str(caught.exception))

    def test_an_unknown_override_is_refused_rather_than_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text(json.dumps(_config()), encoding="utf-8")
            with self.assertRaises(ConfigError) as caught:
                load_run_config(path, overrides={"clusters": "devnet"})
            self.assertIn("clusters", str(caught.exception))

    def test_no_cluster_other_than_local_or_devnet_loads(self) -> None:
        for bad in ("mainnet", "mainnet-beta", "testnet", "LOCAL"):
            with self.subTest(bad=bad), self.assertRaises(ConfigError) as caught:
                _load(_config(cluster=bad))
            self.assertIn("cluster", str(caught.exception))

    def test_the_module_names_no_mainnet_cluster_literal(self) -> None:
        source = (Path(__file__).parents[1] / "config.py").read_text(encoding="utf-8")
        self.assertNotIn('"mainnet"', source)

    def test_a_missing_required_field_is_named(self) -> None:
        for missing in ("cluster", "events", "agents", "total_budget_lamports",
                        "total_budget_actions"):
            raw = _config()
            del raw[missing]
            with self.subTest(missing=missing), self.assertRaises(ConfigError) as caught:
                _load(raw)
            self.assertIn(missing, str(caught.exception))

    def test_an_unknown_top_level_field_is_named(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(extra="nope"))
        self.assertIn("extra", str(caught.exception))

    def test_a_wrong_type_names_the_field(self) -> None:
        cases = [
            ("seed", "seven"),
            ("total_budget_lamports", 1.5),
            ("total_budget_actions", True),
            ("dry_run", "yes"),
            ("kill_after_seconds", 0),
            ("events", {}),
            ("agents", "a1"),
        ]
        for field, value in cases:
            with self.subTest(field=field), self.assertRaises(ConfigError) as caught:
                _load(_config(**{field: value}))
            self.assertIn(field, str(caught.exception))

    def test_a_negative_budget_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(total_budget_lamports=-1))
        self.assertIn("total_budget_lamports", str(caught.exception))

    def test_an_empty_agents_or_events_list_is_refused(self) -> None:
        for field in ("agents", "events"):
            with self.subTest(field=field), self.assertRaises(ConfigError) as caught:
                _load(_config(**{field: []}))
            self.assertIn(field, str(caught.exception))

    def test_duplicate_agent_or_event_ids_are_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(agents=[_agent(), _agent()]))
        self.assertIn("agent_id", str(caught.exception))
        with self.assertRaises(ConfigError) as caught:
            _load(_config(events=[_event(), _event()]))
        self.assertIn("event_id", str(caught.exception))

    def test_every_event_field_is_required_except_cap_bps(self) -> None:
        for missing in ("event_id", "face_lamports", "mode", "tickets", "rounds",
                        "round_seconds"):
            bad = _event()
            del bad[missing]
            with self.subTest(missing=missing), self.assertRaises(ConfigError) as caught:
                _load(_config(events=[bad]))
            self.assertIn(missing, str(caught.exception))

    def test_every_agent_field_is_required(self) -> None:
        for missing in ("agent_id", "policy", "wallet_label", "seed", "budget_lamports",
                        "budget_actions"):
            bad = _agent()
            del bad[missing]
            with self.subTest(missing=missing), self.assertRaises(ConfigError) as caught:
                _load(_config(agents=[bad]))
            self.assertIn(missing, str(caught.exception))

    def test_a_capped_event_without_a_cap_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(events=[_event(mode="capped", cap_bps=None)]))
        self.assertIn("cap_bps", str(caught.exception))

    def test_an_unknown_mode_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(events=[_event(mode="free")]))
        self.assertIn("mode", str(caught.exception))

    def test_a_face_of_zero_or_a_zero_round_count_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(events=[_event(face_lamports=0)]))
        self.assertIn("face_lamports", str(caught.exception))
        with self.assertRaises(ConfigError) as caught:
            _load(_config(events=[_event(rounds=0)]))
        self.assertIn("rounds", str(caught.exception))

    def test_an_unknown_field_inside_an_agent_is_named(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(agents=[_agent(wallet="w")]))
        self.assertIn("wallet", str(caught.exception))

    def test_malformed_json_and_a_non_object_top_level_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ConfigError) as caught:
                load_run_config(path)
            self.assertIn("JSON", str(caught.exception))
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_run_config(path)


class TestProgramSwitch(unittest.TestCase):
    """Which program a run drives, and the pairs that cannot exist.

    v1 is deployed on devnet and can be deployed locally, so it pairs with either cluster. v2 has
    only ever run on a local validator, so `v2` + `devnet` is refused at load: a v2 run there would
    read v1's answers and record them as v2's.
    """

    def test_a_config_that_omits_the_program_loads_as_v1(self) -> None:
        config = _load(_config())
        self.assertEqual(config.program, "v1")
        self.assertEqual(config.program, PROGRAM_DEFAULT)

    def test_the_default_is_stable_and_is_what_the_explicit_value_gives(self) -> None:
        omitted = _load(_config())
        explicit = _load(_config(program="v1"))
        self.assertEqual(omitted.program, explicit.program)
        self.assertEqual(_load(_config()).program, omitted.program, "two loads, one answer")
        self.assertIn(PROGRAM_DEFAULT, PROGRAMS)

    def test_v1_loads_with_either_cluster(self) -> None:
        for cluster in ("local", "devnet"):
            with self.subTest(cluster=cluster):
                self.assertEqual(_load(_config(cluster=cluster, program="v1")).program, "v1")

    def test_v2_loads_with_the_local_cluster(self) -> None:
        config = _load(_config(cluster="local", program="v2"))
        self.assertEqual(config.program, "v2")
        self.assertEqual(config.cluster, "local")

    def test_v2_with_devnet_is_refused_and_says_why(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            _load(_config(cluster="devnet", program="v2"))
        message = str(caught.exception)
        self.assertIn("program", message)
        self.assertIn("v2", message)
        self.assertIn("devnet", message)
        self.assertIn("no devnet deployment", message)
        self.assertIn("proof cannot exist", message)
        self.assertIn('v2 pairs with "local"', message)
        self.assertIn("v1 pairs with either cluster", message)

    def test_an_unknown_program_is_refused(self) -> None:
        for bad in ("v3", "V1", "one", ""):
            with self.subTest(program=bad), self.assertRaises(ConfigError) as caught:
                _load(_config(program=bad))
            self.assertIn("program", str(caught.exception))

    def test_the_program_can_be_overridden_through_the_same_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text(json.dumps(_config(cluster="local")), encoding="utf-8")
            selected = load_run_config(path, overrides={"program": "v2"})
            self.assertEqual(selected.program, "v2")
            # An override is validated like a file value: the impossible pair is still refused.
            with self.assertRaises(ConfigError) as caught:
                load_run_config(path, overrides={"program": "v2", "cluster": "devnet"})
            self.assertIn("devnet", str(caught.exception))
            with self.assertRaises(ConfigError):
                load_run_config(path, overrides={"program": "v3"})

    def test_the_loader_enforces_exactly_the_declared_pairings(self) -> None:
        # Table-driven on purpose: a pairing added to `PROGRAM_CLUSTERS` and not to the loader, or
        # the other way round, fails here rather than in a run that changed its meaning.
        self.assertEqual(set(PROGRAM_CLUSTERS), set(PROGRAMS))
        for program, clusters in sorted(PROGRAM_CLUSTERS.items()):
            for cluster in sorted(CLUSTERS):
                with self.subTest(program=program, cluster=cluster):
                    if cluster in clusters:
                        self.assertEqual(
                            _load(_config(cluster=cluster, program=program)).program, program
                        )
                    else:
                        with self.assertRaises(ConfigError):
                            _load(_config(cluster=cluster, program=program))

    def test_v1_pairs_with_both_clusters_and_v2_with_local_only(self) -> None:
        self.assertEqual(PROGRAM_CLUSTERS["v1"], frozenset({"local", "devnet"}))
        self.assertEqual(PROGRAM_CLUSTERS["v2"], frozenset({"local"}))


class TestSpecsStillConstructDirectly(unittest.TestCase):
    def test_the_dataclasses_are_usable_without_the_loader(self) -> None:
        # The runner builds nothing, but tests of the other modules need a plain spec.
        spec = AgentSpec("a1", "buyer", "wallet-a1", 1, 10, 2)
        self.assertEqual(spec.budget_lamports, 10)
        event = EventSpec("evt1", 1_000, "monitored", None, 1, 1, 0)
        self.assertEqual(event.mode, "monitored")


if __name__ == "__main__":
    unittest.main()
