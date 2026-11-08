"""`python3 -m market_swarm <verb>`: plan a run, run it, check a dataset, summarise it.

Every verb prints plain lines and exits non-zero when an invariant failed. No verb imports
the gateway at module import time: `run` imports it inside the verb, and only when it is
about to build one, so `plan`, `verify-dataset` and `summarise` never touch a socket or the
Solana toolchain.

`run` refuses without a wall-clock cap. The design promises no unbounded run, and a promise
that lives only in a docstring is not a bound, so the refusal is here rather than in the
config dataclass: a config is allowed to say "no cap" for inspection, and the CLI is what
will not start one.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from .config import (
    ConfigError,
    RunConfig,
    effective_cap_bps,
    load_run_config,
)
from .datasets import DatasetInvalid, summarise, verify_dataset


def _lamports(value: int) -> str:
    return f"{value} lamports"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="market_swarm",
        description=(
            "A synthetic ticket-trading swarm. Everything it produces is generated data, "
            "not evidence about any real market."
        ),
    )
    verbs = parser.add_subparsers(dest="verb", required=True)

    for name, help_text in (
        ("plan", "resolve a config and print what a run would do; starts nothing"),
        ("run", "run the swarm and write a synthetic dataset"),
    ):
        verb = verbs.add_parser(name, help=help_text)
        verb.add_argument("--config", required=True, help="path to a run config JSON file")
        verb.add_argument("--cluster", choices=("local", "devnet"), default=None)
        verb.add_argument(
            "--program",
            choices=("v1", "v2"),
            default=None,
            help=(
                "which cap_hook program this run drives: v1 (deployed on devnet, four tags) or "
                "v2 (local only, seven tags). Defaults to the config's value, then to v1"
            ),
        )
        verb.add_argument("--mode", choices=("capped", "monitored"), default=None,
                          help="override the mode of every event in the config")
        verb.add_argument("--agents", type=int, default=None,
                          help="use the first N configured agents (never invents one)")
        verb.add_argument("--rounds", type=int, default=None,
                          help="override the round count of every event")
        verb.add_argument("--seed", type=int, default=None)
        verb.add_argument("--per-agent-lamports", type=int, default=None,
                          help="override every agent's lamport budget")
        verb.add_argument("--total-lamports", type=int, default=None,
                          help="override the run's total lamport budget")
        verb.add_argument("--kill-after", type=float, default=None, metavar="SECONDS",
                          help="wall-clock cap; run refuses without it")
        verb.add_argument("--out", default=None, metavar="DIR",
                          help="directory for the dataset and the KILL flag file")
        verb.add_argument("--dry-run", action="store_true",
                          help="simulated gateway: no socket, every row chain=simulated")

    # Only `run` can spend: `plan` starts nothing. A config with an enabled `llm` block is
    # one file on disk, so an operator who copied an example would be one command away from
    # a paid run with no acknowledgement anywhere in the transcript. `run` asks for it.
    verbs.choices["run"].add_argument(
        "--acknowledge-cost",
        action="store_true",
        help=(
            "required when the config enables the llm block: one pi child per decision, "
            "paid, up to the caps the config names"
        ),
    )

    verify = verbs.add_parser("verify-dataset", help="check a dataset's invariants")
    verify.add_argument("path")

    summary = verbs.add_parser("summarise", help="count and quantile a dataset")
    summary.add_argument("path")

    forge = verbs.add_parser("forge-policy", help="describe the opt-in LLM policy")
    forge.add_argument("--acknowledge-cost", action="store_true",
                       help="acknowledge that this policy spends money per decision")

    return parser


# -- config resolution ---------------------------------------------------------


def _resolve(args: argparse.Namespace) -> RunConfig:
    """The config file with this command's overrides applied, validated as a whole."""
    overrides: dict = {}
    if args.cluster is not None:
        overrides["cluster"] = args.cluster
    if getattr(args, "program", None) is not None:
        overrides["program"] = args.program
    if args.seed is not None:
        overrides["seed"] = args.seed
    if args.total_lamports is not None:
        overrides["total_budget_lamports"] = args.total_lamports
    if args.kill_after is not None:
        overrides["kill_after_seconds"] = args.kill_after
    if args.out is not None:
        overrides["out_dir"] = args.out
    if getattr(args, "dry_run", False):
        overrides["dry_run"] = True

    config = load_run_config(Path(args.config), overrides=overrides or None)

    if args.mode is not None or args.rounds is not None:
        events = []
        for index, event in enumerate(config.events):
            mode = args.mode if args.mode is not None else event.mode
            if mode != event.mode:
                try:
                    effective_cap_bps(mode, event.cap_bps)  # raises if a cap is now required
                except ValueError as exc:
                    raise ConfigError(f"events[{index}]: {exc}") from exc
            rounds = args.rounds if args.rounds is not None else event.rounds
            if rounds < 1:
                raise ConfigError(f"events[{index}].rounds: must be at least 1, got {rounds}")
            events.append(replace(event, mode=mode, rounds=rounds))
        config = replace(config, events=tuple(events))

    if args.agents is not None:
        if args.agents < 1:
            raise ConfigError(f"agents: must be at least 1, got {args.agents}")
        if args.agents > len(config.agents):
            raise ConfigError(
                f"agents: the config defines {len(config.agents)} agent(s); "
                f"--agents {args.agents} would invent one, which this verb will not do. "
                "Add the agent to the config file instead."
            )
        config = replace(config, agents=config.agents[: args.agents])

    if args.per_agent_lamports is not None:
        if args.per_agent_lamports < 0:
            raise ConfigError(
                f"per-agent-lamports: must not be negative, got {args.per_agent_lamports}"
            )
        config = replace(
            config,
            agents=tuple(
                replace(spec, budget_lamports=args.per_agent_lamports)
                for spec in config.agents
            ),
        )
    return config


# -- verbs ---------------------------------------------------------------------


def _cmd_plan(args: argparse.Namespace) -> int:
    config = _resolve(args)
    print(f"run        {config.run_id}")
    print(f"cluster    {config.cluster}  dry_run={config.dry_run}  seed={config.seed}")
    print(
        f"program    {config.program}"
        + (
            "  (deployed on devnet, four instruction tags)"
            if config.program == "v1"
            else "  (local only, seven instruction tags; a real run cannot be driven yet)"
        )
    )
    print(f"kill-after {'none' if config.kill_after_seconds is None else config.kill_after_seconds}")
    print(f"out        {config.out_dir}")
    for event in config.events:
        cap_bps = effective_cap_bps(event.mode, event.cap_bps)
        ceiling = event.face_lamports * (10_000 + cap_bps) // 10_000
        print(
            f"event      {event.event_id}  mode={event.mode}  face={event.face_lamports}  "
            f"cap_bps={cap_bps}  ceiling={ceiling}  tickets={event.tickets}  "
            f"rounds={event.rounds}  round_seconds={event.round_seconds}"
        )
    for spec in config.agents:
        print(
            f"agent      {spec.agent_id}  policy={spec.policy}  "
            f"budget={_lamports(spec.budget_lamports)}  actions={spec.budget_actions}"
        )
    print(
        f"budgets    total={_lamports(config.total_budget_lamports)}  "
        f"actions={config.total_budget_actions}"
    )
    decision_points = sum(event.rounds for event in config.events) * len(config.agents)
    print(f"actions    at most {decision_points} decision points "
          f"({len(config.agents)} agents x {sum(event.rounds for event in config.events)} rounds)")
    print(f"actions    hard cap {config.total_budget_actions} actions, "
          f"{_lamports(config.total_budget_lamports)} notional")
    if config.kill_after_seconds is None:
        print("note       run will refuse this config: no wall-clock cap is set")
    llm = getattr(config, "llm", None)
    if llm is None or not llm.enabled:
        print("llm        off, scripted policies")
    else:
        print(
            f"llm        on, tier={llm.tier}  per-agent-tokens={llm.per_agent_token_budget}  "
            f"total-tokens={llm.total_token_budget}  timeout={llm.timeout_seconds}s  "
            f"concurrent={llm.max_concurrent}"
        )
        print(
            "llm        cost cap "
            + (
                "none (tokens are still capped)"
                if llm.cost_cap_usd is None
                else f"${llm.cost_cap_usd:g} at the configured usd_per_mtok rates"
            )
        )
        print(
            f"llm        one pi child per decision, at most {decision_points} decisions; "
            "the run trips on the token cap, the cost cap, the flag file or the wall clock"
        )
    return 0


def _build_gateway(config: RunConfig):
    """Import the gateway lazily and build one. Never at module import time.

    `CONTRACT.md` fixes `ChainGateway(cluster, *, run_dir, program, dry_run)` and the runner wave
    assumed a `make_gateway` factory in front of it, so this accepts either: the factory
    called the contract's way, falling back to `make_gateway(config)` if that factory takes
    the config instead. `program` is passed, never defaulted here: the whole point of the
    switch is that the gateway and the dataset agree on which program answered.
    """
    try:
        from market_swarm import gateway as gateway_module
    except ImportError as exc:
        raise RuntimeError(
            "market_swarm.gateway is not importable in this tree "
            f"({exc.__class__.__name__}); the chain gateway is built by another wave and "
            "this verb cannot run without it"
        ) from exc

    factory = getattr(gateway_module, "make_gateway", None)
    if factory is None:
        return gateway_module.ChainGateway(
            config.cluster, run_dir=Path(config.out_dir), dry_run=config.dry_run
        )
    try:
        return factory(
            config.cluster,
            run_dir=Path(config.out_dir),
            dry_run=config.dry_run,
            program=config.program,
        )
    except TypeError:
        return factory(config)


def _cmd_run(args: argparse.Namespace) -> int:
    config = _resolve(args)
    if config.kill_after_seconds is None:
        print(
            "run refuses to start: no wall-clock cap. Pass --kill-after SECONDS (or set "
            "kill_after_seconds in the config).",
            file=sys.stderr,
        )
        return 2
    llm = getattr(config, "llm", None)
    if llm is not None and getattr(llm, "enabled", False) and not args.acknowledge_cost:
        print(
            "run refuses to start: this config enables the llm block, which spends money "
            "on one pi child per decision. Pass --acknowledge-cost when that is the run "
            "you meant, or set \"enabled\": false for a scripted run. `plan` prints the "
            "caps before anything is spent.",
            file=sys.stderr,
        )
        return 2

    from .runner import SwarmRunner

    try:
        gateway = _build_gateway(config)
    except RuntimeError as exc:
        print(f"run cannot start: {exc}", file=sys.stderr)
        return 1

    gateway.start()
    try:
        summary = SwarmRunner(config, gateway).run()
    finally:
        gateway.stop()

    print(f"run        {summary.run_id}")
    print(f"gateway    {config.cluster}  program={config.program}  dry_run={config.dry_run}")
    print(f"rows       {summary.rows}")
    print("status     " + (" ".join(
        f"{name}={count}" for name, count in summary.by_status.items()
    ) or "none"))
    print("agent      " + (" ".join(
        f"{name}={count}" for name, count in summary.by_agent.items()
    ) or "none"))
    # "executed" is a claim about the chain. On a dry run nothing was executed, and the words
    # have to say what actually happened.
    _verb = "would have committed" if config.dry_run else "committed"
    print(f"notional   {_lamports(summary.total_notional_lamports)} {_verb}")
    print(f"kill       {summary.kill_reason or 'none'}")
    if summary.llm is not None:
        llm = summary.llm
        print(
            f"llm        tokens={llm['total_tokens']} of {llm['total_token_budget']} "
            f"(in={llm['input']} out={llm['output']} cache_read={llm['cache_read']} "
            f"cache_write={llm['cache_write']})"
        )
        basis = llm.get("cost_basis", "unpriced")
        usd = (
            "unpriced"
            if basis in ("unpriced", "table_error")
            else f"{llm['usd']:.6f} ({basis})"
        )
        print(
            "llm        usd="
            + usd
            + (
                ""
                if llm["cost_cap_usd"] is None
                else f" of ${llm['cost_cap_usd']:g} cap"
            )
            + " (provider-reported estimate, not a bill)"
        )
        print(
            "llm        decisions "
            f"real={llm.get('decisions_real', 0)} "
            f"fallback={llm.get('decisions_fallback', 0)} "
            f"refused={llm.get('decisions_refused', 0)}"
        )
    print(f"wall       {summary.wall_seconds:.3f}s")
    for path in summary.dataset_paths:
        print(f"dataset    {path}")
    # A kill is a clean stop, not a failed invariant: the summary names why it stopped and
    # the rows already written are the dataset. Only a broken invariant exits non-zero.
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    try:
        result = verify_dataset(Path(args.path))
    except DatasetInvalid as exc:
        print(f"INVALID {Path(args.path).name}")
        for violation in exc.violations:
            print(violation)
        return 2
    print(
        f"PASS {result['path']}: {result['rows']} row(s), schema {result['schema_version']}, "
        f"run {result['run_id']}, event {result['event_id']}, mode {result['mode']}"
    )
    return 0


def _cmd_summarise(args: argparse.Namespace) -> int:
    try:
        result = summarise(Path(args.path))
    except DatasetInvalid as exc:
        print(f"INVALID {Path(args.path).name}")
        for violation in exc.violations:
            print(violation)
        return 2
    print(f"dataset    {result['path']}  rows={result['rows']}  run={result['run_id']}")
    print("status     " + " ".join(
        f"{name}={count}" for name, count in result["by_status"].items()
    ))
    print("action     " + " ".join(
        f"{name}={count}" for name, count in result["by_action"].items()
    ))
    # What became of each kind of intent. Without this, `action buy=7` cannot be read against
    # the two refusals and five censored bids that share the count.
    for action, counts in result["by_action_status"].items():
        print(f"outcome    {action}: " + " ".join(
            f"{name}={count}" for name, count in counts.items()
        ))
    print("mode       " + " ".join(
        f"{name}={count}" for name, count in result["by_mode"].items()
    ))
    for mode, bucket in result["asks_by_mode"].items():
        print(
            f"asks       {mode}: attempts={bucket['attempts']} executed={bucket['executed']} "
            f"skipped={bucket['skipped']} refused={bucket['refused']}"
        )
    for mode, rate in result["refusal_rate_by_mode"].items():
        print(
            f"refusals   {mode}: {rate['refused']} of {rate['attempts']} asks "
            f"({rate['rate_bps']} bps)"
        )
    for mode, q in result["price_quantiles_by_mode"].items():
        print(
            f"prices     {mode}: n={q['n']} min={q['min']} p50={q['p50']} p90={q['p90']} "
            f"max={q['max']}"
        )
    print(f"notional   {_lamports(result['total_notional_lamports'])}")
    print(f"note       {result['note']}")
    return 0


def _cmd_forge(args: argparse.Namespace) -> int:
    print("forge-policy  the LLM policy is opt-in and cost-bearing: one child process per")
    print("              decision, with its own token budget and a run-level cap.")
    if not args.acknowledge_cost:
        print(
            "forge-policy refuses: pass --acknowledge-cost. A market dataset needs "
            "thousands of decisions and this policy pays for each one, so the spend is the "
            "operator's decision, not a default.",
            file=sys.stderr,
        )
        return 1
    try:
        from market_swarm import forge_policy  # noqa: F401
        from market_swarm import llm
    except ImportError as exc:
        print(
            f"forge-policy: the adapter is not present in this build ({exc}).",
            file=sys.stderr,
        )
        return 1
    print("forge-policy acknowledged: the adapter and its personas are importable.")
    print("              turn it on per run with an \"llm\" block in the run config and")
    print("              pass `run --acknowledge-cost`; market_swarm/example-llm-run.json")
    print("              ships with the block disabled. `plan` prints the caps before")
    print("              anything is spent, and `run` prints what was spent.")
    print(f"              personas: {', '.join(sorted(llm.PERSONAS))}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "plan": _cmd_plan,
        "run": _cmd_run,
        "verify-dataset": _cmd_verify,
        "summarise": _cmd_summarise,
        "forge-policy": _cmd_forge,
    }
    try:
        return handlers[args.verb](args)
    except ConfigError as exc:
        print(f"config: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
