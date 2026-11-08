"""The round runner: intents in, matched trades out, exactly one ledger row per action.

What a round is
---------------
Each round every agent is offered one `MarketView` and returns zero or more `Intent`s. The
runner, never the agent, decides what those intents become. The order in which agents are
offered a decision is a stable seeded shuffle of the agent ids for that
`(run seed, event id, round)`, so a run is reproducible without the shuffle being the
identity permalink to the config file's agent order.

The market this module resolves, in this order
----------------------------------------------
1. `buy` at or below face is a **primary purchase**: house -> agent, if the house has stock
   and the agent holds fewer than `max_holdings` tickets (default 1). Row `hop_index=1`,
   `bid_lamports=None`, `lot_price_lamports=None`.
2. `buy` above face is a **secondary bid**. It is not an action on its own; it is matched
   against asks.
3. `resell` is an **ask**. Asks are sorted by `(price asc, agent_id)`. For each ask the best
   eligible bid wins: highest price first, and at equal price the lower `agent_id`. A bid is
   eligible when its price is at least the ask, its buyer is not frozen, its buyer is under
   its holdings limit, it is not the seller, and the buyer can be charged the *ask* price.
   The transfer executes at the **ask** price -- the seller sets the price and the buyer
   accepts it -- and the row keeps both numbers.
4. An ask nobody meets is **not dropped**: it is written with `status="skipped"` and a
   rationale saying no bid met it. Those rows are the censored observations and they are
   the reason the dataset is worth having.
5. `list` never touches the chain, because `cap_hook` has no listing instruction. It is
   written with `status="ok"`, `signature=None`, `slot=None` and a rationale that says so.

The runner deliberately does **not** pre-filter an ask by the cap. In `capped` mode an ask
above `ceiling_lamports` is sent to the chain and comes back `refused` with
`error_code=6010`; in `monitored` the identical ask is admitted. Filtering or clamping here
would make the two modes produce the same dataset, which would destroy the only comparison
the harness exists to make.

Ticket identity
---------------
The chain sees "one base unit" and keeps no unit counter. `ticket_id` is a **harness label**
assigned when the house stocks a ticket (`<event_id>#0001`, `<event_id>#0002`, ...) and
carried FIFO through every hop, so the dataset can follow one unit and the chain cannot
disagree with it because the chain never held the claim.

Budgets and the kill switch
---------------------------
Exactly one charge per row, which makes `total_actions` and the row count the same number:

- an executed trade charges the **payer** the price (the buyer, on a primary buy or a
  filled resale);
- a refused, skipped or listed action charges the **actor** zero, so the action budget
  still bites even when no lamports moved.

An agent-level `BudgetExceeded` freezes that agent and writes no row for the action it
blocked; a total-level one trips the kill switch, naming which total. The kill switch is
polled before every action and checks three things: a prior trip, the flag file
`<out_dir>/KILL`, and the wall-clock cap. A tripped run stops cleanly, closes every file and
reports `kill_reason`; it does not raise.

Nothing here reads a key, opens a socket, or mentions a cluster other than the one the
config carries. The gateway object is handed in, so the tests never need the real one.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .agents import (
    ACTIONS as INTENT_ACTIONS,
    Holding,
    Intent,
    MarketView,
    Policy,
    Refusal,
    build_policy,
)
from .budget import BudgetExceeded, BudgetTracker
from .config import EventSpec, RunConfig, ceiling_lamports, effective_cap_bps
from .ledger import (
    DISCLAIMER,
    LABEL,
    LEDGER_HEADER,
    SCHEMA_VERSION,
    LedgerWriter,
    TradeRow,
)

#: The label the house is known by to a gateway, when the gateway does not name one itself.
#: `stock()` mints to it; a primary buy moves one unit out of it. The contract never fixes the
#: string, and the shipped gateway calls it something else, so `_house_label` probes the chain
#: object (and, failing that, the module that defined it) instead of assuming this one.
DEFAULT_HOUSE_LABEL = "house"

#: One ticket per agent unless the caller says otherwise. `max_holdings` is a market rule of
#: this harness, not a chain rule: the chain tracks balances, this harness tracks units.
DEFAULT_MAX_HOLDINGS = 1

#: How many recent executed prices a view carries. Enough for a policy to see the level,
#: short enough that the view stays a view.
LAST_PRICE_WINDOW = 5

#: How many live decisions the sidecar keeps, in the agents' own words. A long run would
#: otherwise grow the `.meta.json` without bound; the count of what was dropped is recorded
#: beside it, so a truncated log cannot pass for the whole record.
LLM_LOG_MAX = 500

#: The kill switch's flag file, inside the run's output directory.
KILL_FLAG_NAME = "KILL"

#: Budget refusals that stop the whole run rather than one agent.
TOTAL_BUDGET_KINDS = frozenset({"total_lamports", "total_actions"})

BPS = 10_000


def _derived_seed(*parts: object) -> int:
    """A 64-bit seed from the given parts, stable across processes and hash seeds."""
    material = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


#: The usage counters a live policy is asked to report, in the order a reader expects them.
_ACCOUNTING_FIELDS = ("input", "output", "cache_read", "cache_write", "usd")


def _count(value: object) -> int:
    """A non-negative integer from a count, or zero. A hostile counter must not raise here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return max(0, int(value))


def _reports_live_decisions(policy: object) -> bool:
    """Whether a policy can say which of its decisions a model made.

    Duck-typed on purpose: the runner does not import the money module, and a caller's own
    adapter should be recognised by what it reports rather than by its class. `ForgePolicy`
    carries these four names; every scripted policy in `agents` has only `name`/`decide`.
    """
    return all(
        hasattr(policy, attribute)
        for attribute in ("decisions_real", "decisions_fallback", "decisions_refused", "usage")
    )


def _policy_accounting(policy: object) -> dict | None:
    """One live policy's own numbers, or None for a policy that reports none.

    Never raises: a policy object is the caller's, so a broken `usage` property must leave
    the sidecar with less information, not abort the run after it has already spent money.
    """
    if not _reports_live_decisions(policy):
        return None
    try:
        usage = getattr(policy, "usage", None)
        entry = {
            "agent_id": getattr(policy, "agent_id", None),
            "name": str(getattr(policy, "name", "?")),
            "model": getattr(policy, "model", None),
            "tier": getattr(policy, "tier", None),
            "decisions_real": _count(getattr(policy, "decisions_real", 0)),
            "decisions_fallback": _count(getattr(policy, "decisions_fallback", 0)),
            "decisions_refused": _count(getattr(policy, "decisions_refused", 0)),
        }
        for field in _ACCOUNTING_FIELDS:
            entry[field] = getattr(usage, field, 0)
        entry["total_tokens"] = (
            _count(entry["input"])
            + _count(entry["output"])
            + _count(entry["cache_read"])
            + _count(entry["cache_write"])
        )
        entry["usd"] = float(entry["usd"] or 0.0)
    except Exception:
        return None
    return entry


def _price_ok(value: object) -> bool:
    """A price this harness will act on: a real positive integer, never a bool or a float.

    A policy that returns `1.5`, `True` or `-5` used to abort the whole run out of `_apply`,
    leaving a truncated dataset behind. A malformed order is a broken intent, and a broken
    intent gets a row like any other refusal.
    """
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def markup_bps(price_lamports: int, face_lamports: int) -> int:
    """The markup in basis points relative to **face**, floored, integer only.

    Negative below face, which is a legal price: the hook bounds a resale above and never
    below, so a discounted row has to be representable.
    """
    return (price_lamports - face_lamports) * BPS // face_lamports


@dataclass(frozen=True)
class RunSummary:
    """What a finished (or killed) run did. The contract's fields, no more."""

    run_id: str
    rows: int
    by_status: dict
    by_agent: dict
    total_notional_lamports: int
    kill_reason: str | None
    dataset_paths: tuple[str, ...]
    wall_seconds: float
    #: Tokens and dollars the LLM agents spent, or None when the run used scripted policies.
    #: Last so every existing construction keeps working.
    llm: dict | None = None


class _Kill(Exception):
    """Internal: the kill switch tripped. Caught in `run`, never escapes it."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class _AgentFrozen(Exception):
    """Internal: one agent's budget refused this action, so the action writes no row."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"agent {agent_id} is frozen")


class _EventContext:
    """Everything one event's round loop needs. Plain mutable state, one event at a time."""

    def __init__(
        self, event: EventSpec, chain, writer: LedgerWriter, cap_bps: int, house_label: str
    ) -> None:
        self.event = event
        self.chain = chain
        self.writer = writer
        self.house_label = house_label
        self.cap_bps = cap_bps
        self.ceiling = ceiling_lamports(event.face_lamports, cap_bps)
        self.house_stock = 0
        self.holdings: dict[str, list[Holding]] = {}
        self.refused: dict[str, int] = {}
        self.last_prices: list[int] = []
        self.hops: dict[str, int] = {}
        self.tickets_issued = 0
        self.addresses: dict[str, str | None] = {}
        # What the sidecar reports so a half-finished event cannot pass for a finished one.
        self.completed = False
        self.rounds_completed = 0
        # This event's own row count and statuses. The runner also keeps run-wide counters for its
        # summary, and writing those here made the second event's sidecar claim every row of the
        # run -- measured: `evt_monitored`'s sidecar said `rows: 56, ok: 42` beside a file with 28
        # rows in it. A sidecar describes one dataset, so it counts one dataset.
        self.rows = 0
        self.by_status: dict[str, int] = {}
        # The round every row written during the current pass belongs to. Kept on the context
        # so no action has to thread it through, and no row can silently omit it.
        self.round_no: int | None = None


class SwarmRunner:
    """Runs one config against one gateway. Constructible with a fake; no import of one.

    `clock` is injected so a test never reads the wall clock: it returns epoch seconds.
    `policies` is a test seam (agent_id -> Policy) so the market rules can be exercised with
    exact intents instead of through the scripted policies; left as None, the runner builds
    the configured policy for each agent.
    """

    def __init__(
        self,
        config: RunConfig,
        gateway,
        *,
        clock: Callable[[], float] | None = None,
        policies: Mapping[str, Policy] | None = None,
        max_holdings: int | None = None,
    ) -> None:
        if max_holdings is not None and max_holdings < 1:
            raise ValueError(f"max_holdings: must be at least 1, got {max_holdings}")
        self._config = config
        self._gateway = gateway
        self._clock = clock if clock is not None else time.time
        self._policies = dict(policies) if policies is not None else None
        self._max_holdings = max_holdings
        self._holdings_by_agent = {
            spec.agent_id: max(1, spec.max_holdings) for spec in config.agents
        }
        self._chain_name = self._chain_label()
        self._reset()

    # -- lifecycle ---------------------------------------------------------------

    def _reset(self) -> None:
        self._budget = BudgetTracker(
            self._config.agents,
            self._config.total_budget_lamports,
            self._config.total_budget_actions,
        )
        self._by_status: dict[str, int] = {}
        self._by_agent: dict[str, int] = {
            spec.agent_id: 0 for spec in self._config.agents
        }
        self._notional = 0
        self._run_spent = 0
        self._run_actions = 0
        self._rows = 0
        self._paths: list[Path] = []
        self._writers: list[LedgerWriter] = []
        self._kill_reason: str | None = None
        self._started = 0.0
        # The run-level LLM ledger, built only when the config switched the LLM on. It is
        # shared by every agent's policy, so one cap bounds the whole run rather than each
        # agent independently, and it is rebuilt by `_reset` so a second run() starts clean.
        self._llm_budget = None
        #: The live policies built for the current event and the decisions seen so far, used
        #: only to say in the sidecar which decisions a child made and which fell back.
        self._llm_policies: list = []
        #: The agent ids whose policy reports live accounting, so a dataset row can carry the
        #: policy's own words. Derived from the policy objects, never guessed from the row.
        self._live_agent_ids: set[str] = set()
        self._llm_log: list[dict] = []
        #: The live policies of earlier events, kept because the sidecar describes the run
        #: and not its last event. Their counters are read at the end, never folded on the
        #: way: a caller-supplied policy is the same object across events, so a fold at the
        #: pin event would miss everything it did afterwards.
        self._llm_counted_policies: list = []
        self._llm_log_dropped = 0
        #: Where the live children's cwds, sessions and stderr live. A fresh temp directory,
        #: never under `out_dir`: the gateway keeps its keypairs at `<out_dir>/keys`, and a
        #: prompt-following child should not have a key directory four `..` hops above its cwd.
        self._llm_scratch: Path | None = None
        llm = getattr(self._config, "llm", None)
        if llm is not None and getattr(llm, "enabled", False):
            from .llm import LlmBudget

            self._llm_budget = LlmBudget(
                total_token_budget=llm.total_token_budget,
                cost_cap_usd=llm.cost_cap_usd,
                prices=llm.usd_per_mtok,
            )
            self._llm_scratch = Path(
                tempfile.mkdtemp(prefix=f"market-swarm-{self._config.run_id}-")
            )

    def _chain_label(self) -> str:
        """Where the rows actually came from, read from the gateway, not from the config.

        A config can disagree with the gateway it is handed -- the runner's `gateway` parameter
        is a documented seam, and a `DryRunGateway` with `cluster="devnet"` in the config used
        to label simulated rows `devnet`. That is a "would have happened" row reading as
        "happened", which is the one thing the status vocabulary forbids, so the answer comes
        from the object that did the work: `simulated` is a property of the gateway, and a
        disagreement with the config is refused rather than papered over.
        """
        declared = getattr(self._gateway, "simulated", None)
        if declared is None:
            # A gateway that does not declare it: fall back to the config rather than break
            # every fake. Both shipped gateways declare `simulated`, so the check below is
            # what runs in production.
            simulated = bool(self._config.dry_run)
        else:
            simulated = bool(declared)
        if simulated:
            if declared is not None and not self._config.dry_run:
                raise ValueError(
                    "gateway is simulated but config.dry_run is False: refusing to label "
                    "simulated rows as observations"
                )
            return "simulated"
        if self._config.dry_run and declared is not None:
            raise ValueError(
                "config.dry_run is True but the gateway is not simulated: refusing to halve "
                "the truth in either direction"
            )
        status = getattr(self._gateway, "status", None)
        cluster = self._config.cluster
        if callable(status):
            try:
                reported = status().get("cluster")
            except Exception:
                reported = None
            if reported in ("local", "devnet"):
                cluster = reported
        return "local-validator" if cluster == "local" else "devnet"

    def _program_name(self) -> str:
        """Which program produced the rows, read from the gateway, not from the config.

        The same reasoning as `_chain_label`: the `gateway` argument is a documented seam, so the
        object that did the work is asked first. A gateway that reports a program the config did
        not name is refused rather than relabelled -- the whole point of the switch is that a row
        says which program answered it, and a config naming v1 over a v2 gateway would make every
        row a false statement about its own provenance. A gateway that does not declare one (a
        fake built for a test of the market rules) falls back to the config, which is what the
        shipped gateways make unnecessary.
        """
        reported = getattr(self._gateway, "program", None)
        if reported is None:
            return self._config.program
        if reported != self._config.program:
            raise ValueError(
                f"gateway drives program {reported!r} and the config says {self._config.program!r}: "
                "refusing to label one program's rows with another's name"
            )
        return reported

    def run(self) -> RunSummary:
        """Run every event in config order. Returns, never raises, on a kill."""
        self._reset()
        self._started = self._clock()
        try:
            for event in self._config.events:
                # Budgets are per event. Each event is its own mint, its own record and its own
                # order book, and a trader's limit is what it will commit in that market. A
                # single run-wide pot made the second event systematically poorer than the
                # first -- by the time it opened, the buyers had already spent -- which is a
                # confound, not a market. The run-level kill switch is still run-wide, and
                # `total_notional_lamports` in the summary is the sum across events.
                self._budget = BudgetTracker(
                    self._config.agents,
                    self._config.total_budget_lamports,
                    self._config.total_budget_actions,
                )
                self._run_event(event)
        except _Kill as kill:
            self._kill_reason = kill.reason
        finally:
            for writer in self._writers:
                writer.close()
        return RunSummary(
            run_id=self._config.run_id,
            rows=self._rows,
            by_status=dict(sorted(self._by_status.items())),
            by_agent=dict(self._by_agent),
            total_notional_lamports=self._notional,
            kill_reason=self._kill_reason,
            dataset_paths=tuple(str(path) for path in self._paths),
            wall_seconds=max(0.0, self._clock() - self._started),
            llm=self._llm_meta(),
        )

    # -- one event ---------------------------------------------------------------

    def _run_event(self, event: EventSpec) -> None:
        chain = self._gateway.create_event(event)
        cap_bps = effective_cap_bps(event.mode, event.cap_bps)
        out_dir = Path(self._config.out_dir)
        path = out_dir / f"{self._config.run_id}-{event.event_id}-SYNTHETIC.jsonl"
        # Second gate. Even with validated identifiers, resolve the path and refuse anything
        # that is not inside the run directory the operator named.
        if out_dir.resolve() not in path.resolve().parents:
            raise ValueError(
                f"refusing to write {path.name} outside {out_dir}: a run writes only under the "
                "directory it was given"
            )
        # A second run with the same run_id and event_id would overwrite the first run's
        # dataset, which is how one measured run replaced another on this machine. The
        # dataset is the record; it is never silently replaced.
        if path.exists():
            raise ValueError(
                f"refusing to overwrite {path.name}: a dataset from an earlier run is already "
                "there. Use a new run_id, or a different out_dir, so the earlier record "
                "survives."
            )
        header = dict(LEDGER_HEADER)
        header["run_id"] = self._config.run_id
        header["event_id"] = event.event_id
        header["mode"] = event.mode
        # A dataset that can be separated from its sidecar still has to say whether anything
        # was actually sent, so the header carries it too.
        header["cluster"] = self._chain_name
        header["program"] = self._program_name()
        header["dry_run"] = bool(self._config.dry_run)
        writer = LedgerWriter(path, header=header)
        self._writers.append(writer)
        self._paths.append(path)

        ctx = _EventContext(event, chain, writer, cap_bps, self._house_label(chain))
        try:
            for spec in self._config.agents:
                ctx.holdings[spec.agent_id] = []
                ctx.refused[spec.agent_id] = 0
                ctx.addresses[spec.wallet_label] = chain.open_account(spec.wallet_label)
            chain.stock(event.tickets)
            ctx.house_stock = event.tickets
            policies = self._policies_for(event, cap_bps)
            try:
                for round_no in range(1, event.rounds + 1):
                    ctx.rounds_completed = round_no - 1
                    self._round(ctx, policies, round_no)
                    ctx.rounds_completed = round_no
            except _Kill as kill:
                # Record the reason before the sidecar is written, so the meta file says why
                # the run stopped instead of carrying a null where the answer belongs.
                self._kill_reason = kill.reason
                raise
            ctx.completed = True
        finally:
            writer.close()
            self._write_meta(ctx, path)

    def _policies_for(self, event: EventSpec, cap_bps: int) -> dict[str, Policy]:
        if self._policies is not None:
            chosen = {
                spec.agent_id: self._policies[spec.agent_id] for spec in self._config.agents
            }
            # A caller-supplied policy may be a live adapter that accounts for itself
            # (`ForgePolicy` does). The sidecar has to read those counters rather than
            # assume the seam means scripted agents: a live run through the seam used to
            # publish "Generated by scripted agents", which was simply false.
            self._archive_llm_policies()
            self._llm_policies = [
                policy for policy in chosen.values() if _reports_live_decisions(policy)
            ]
            self._live_agent_ids = {
                str(getattr(policy, "agent_id", agent_id))
                for agent_id, policy in chosen.items()
                if _reports_live_decisions(policy)
            }
            return chosen
        # The intended cap travels on the policy, not the view: in monitored mode the view's
        # cap is the field maximum and a policy that read it would censor itself.
        intended = event.cap_bps if event.cap_bps is not None else cap_bps
        if self._llm_budget is not None:
            # One scratch directory per agent under the run directory, so a live run leaves
            # nothing in the repository and its session files sit beside the dataset that
            # records what the agents decided.
            from .llm import build_llm_policy

            root = self._llm_scratch
            if root is None:  # a runner built by hand with no `_reset` has no scratch yet
                root = Path(tempfile.mkdtemp(prefix=f"market-swarm-{self._config.run_id}-"))
                self._llm_scratch = root
            built = {
                spec.agent_id: build_llm_policy(
                    spec,
                    llm=self._config.llm,
                    budget=self._llm_budget,
                    scratch_root=root,
                    intended_cap_bps=intended,
                )
                for spec in self._config.agents
            }
            self._archive_llm_policies()
            self._llm_policies = list(built.values())
            self._live_agent_ids = {
                policy.agent_id for policy in built.values()
            }
            return built
        return {
            spec.agent_id: build_policy(
                spec,
                face_lamports=event.face_lamports,
                cap_bps=cap_bps,
                intended_cap_bps=intended,
            )
            for spec in self._config.agents
        }

    # -- one round ---------------------------------------------------------------

    def _round(self, ctx: _EventContext, policies: Mapping[str, Policy], round_no: int) -> None:
        ctx.round_no = round_no
        self._ceiling_for_prose = ctx.ceiling
        self._check_kill()
        order = self._decision_order(ctx.event.event_id, round_no)
        decisions: list[Intent | Refusal] = []
        if self._parallel_decisions():
            decisions = self._decide_in_parallel(ctx, policies, round_no, order)
        else:
            for agent_id in order:
                self._check_kill()
                if self._budget.is_frozen(agent_id):
                    continue
                view = self._view(ctx, agent_id, round_no)
                decisions.extend(policies[agent_id].decide(view))
        # A decision is where the money is spent, so the caps are polled once more before any
        # of the collected decisions can become a row: intents and refusals alike. A trip
        # here stops the run and writes no partial round, because a refusal row from a round
        # the run did not apply would contradict the sidecar's own account. The poll sits
        # **above** `_split_refusals`, which is the call that writes; nothing polls between
        # the rows, so a clock that expires mid-write is not observed until the next action.
        self._check_kill()
        intents = self._split_refusals(ctx, decisions)
        self._record_decisions(intents, round_no)
        self._apply(ctx, round_no, intents)

    def _archive_llm_policies(self) -> None:
        """Keep the previous event's policies so the sidecar can read their final counters.

        They are not folded here. The counters are read once at the end: a caller-supplied
        policy is the *same object* for every event, so a total folded when the second event
        was pinned would miss everything that policy did afterwards.
        """
        for policy in self._llm_policies:
            if not any(policy is known for known in self._llm_counted_policies):
                self._llm_counted_policies.append(policy)

    def _record_decisions(self, intents: Sequence[Intent], round_no: int) -> None:
        """Keep what each live agent asked for and said, for the sidecar only.

        The agent's own words would otherwise vanish: the row schema is fixed by the
        contract and the runner writes its own prose into a row's `rationale`. They are kept
        here, bounded to a short log, and written to the `.meta.json` beside the dataset.

        This used to return early whenever the runner had no run-level `LlmBudget`, which
        dropped the words of every child on a run constructed with `policies=` — the very
        run whose sidecar then claimed scripted agents. The condition is now whether any
        policy reports live decisions, not which of the two ways it was wired.
        """
        if self._llm_budget is None and not self._llm_policies:
            return
        for intent in intents:
            if len(self._llm_log) >= LLM_LOG_MAX:
                self._llm_log_dropped += 1
                continue
            self._llm_log.append(
                {
                    "round": round_no,
                    "agent_id": intent.agent_id,
                    "action": intent.action,
                    "price_lamports": intent.price_lamports,
                    "rationale": (intent.rationale or "")[:300],
                }
            )

    def _llm_meta(self) -> dict | None:
        """The sidecar's llm block: the spend, plus which decisions were really the model's.

        Two ways a run can have live decisions and only one of them has a run-level
        `LlmBudget`. The other is the `policies=` seam, where the policies account for
        themselves; that block is built from their counters and says so, and a policy that
        reports nothing produces `provenance: "unknown"` rather than a guess.
        """
        if self._llm_budget is not None:
            block = self._llm_budget.snapshot()
            block["provenance"] = "llm"
        else:
            block = self._policy_provenance()
            if block is None:
                return None
        # Every policy the run used, each counted once at its final value, so a two-event
        # run reports the run and not its last event.
        seen = self._provenance_policies()
        counts = {"real": 0, "fallback": 0, "refused": 0}
        for policy in seen:
            counts["real"] += _count(getattr(policy, "decisions_real", 0))
            counts["fallback"] += _count(getattr(policy, "decisions_fallback", 0))
            counts["refused"] += _count(getattr(policy, "decisions_refused", 0))
        block["decisions_real"] = counts["real"]
        block["decisions_fallback"] = counts["fallback"]
        block["decisions_refused"] = counts["refused"]
        block["decisions_total"] = counts["real"] + counts["fallback"] + counts["refused"]
        reasons = [
            reason
            for policy in seen
            for reason in list(getattr(policy, "fallback_reasons", []))
        ]
        block["fallback_reasons"] = reasons[:20]
        block["decision_log"] = list(self._llm_log)
        block["decision_log_dropped"] = self._llm_log_dropped
        block["scratch_root"] = str(self._llm_scratch) if self._llm_scratch else None
        return block

    def _provenance_policies(self) -> list:
        """Every policy that could have decided something in this run, in order, once each."""
        candidates = list(self._llm_policies)
        if self._policies is not None:
            candidates = list(self._policies.values()) + candidates
        seen: list = []
        for policy in candidates + list(self._llm_counted_policies):
            if not any(policy is known for known in seen):
                seen.append(policy)
        return seen

    def _policy_provenance(self) -> dict | None:
        """The llm block for a run given `policies=` instead of an `llm` config block.

        Returns None when the runner built its own policies (the scripted path, where
        "scripted agents" is a fact) or when no caller-supplied policy reports anything. A
        `ForgePolicy` reports model, tier, tokens and how many decisions a child made, and
        the block is built from that. A run mixing it with a policy that reports nothing gets
        `provenance: "unknown"`: the runner cannot attribute the whole dataset, and calling it
        scripted or a model's would both be inventing it.
        """
        if self._policies is None:
            return None
        # Every policy the caller supplied, not only the ones that report: a run mixing a
        # live adapter with an opaque stub has rows of both kinds, and calling the whole
        # dataset a model's would be the same false claim in the other direction.
        seen = self._provenance_policies()
        entries = [_policy_accounting(policy) for policy in seen]
        described = [entry for entry in entries if entry is not None]
        if not described:
            # Nothing to report. No block is written: a block of zeroes would read as
            # "nothing was spent", which the runner cannot know.
            return None
        block: dict = {
            "provenance": "policy" if len(described) == len(seen) else "unknown",
            "source": "caller-supplied policies (the runner was built with policies=...)",
            "policies": described,
            "total_token_budget": None,
            "cost_cap_usd": None,
            "trip_reason": None,
            "cost_note": "provider-reported estimate, not a bill",
        }
        totals = {field: 0 for field in _ACCOUNTING_FIELDS}
        for entry in described:
            for field in _ACCOUNTING_FIELDS:
                totals[field] += entry[field]
        block.update(totals)
        block["total_tokens"] = (
            block["input"] + block["output"] + block["cache_read"] + block["cache_write"]
        )
        # Model and tier at the top level only when every reporting policy agrees: two
        # agents on different tiers have no single model, and inventing one would be the
        # same kind of quiet false claim this block exists to avoid.
        for attribute, field in (("model", "model"), ("tier", "tier")):
            values = {entry[field] for entry in described}
            block[attribute] = values.pop() if len(values) == 1 else None
        if block["provenance"] == "unknown":
            block["note"] = (
                "provenance unknown: caller-supplied policy. The run cannot say from these "
                "objects which decisions a model made, so this block claims nothing."
            )
        else:
            block["note"] = (
                "accounted by the caller-supplied policies themselves. No run-level "
                "LlmBudget was configured, so there is no run-level token or dollar cap."
            )
        return block

    def _parallel_decisions(self) -> bool:
        """Whether this round may decide agents concurrently.

        Only a live LLM run does, and only up to the configured cap. The decisions are
        independent by construction: every view is built from the same pre-round state and
        the runner applies nothing until the round is over, so concurrency cannot change a
        decision. The scripted path stays serial exactly as it was.
        """
        llm = getattr(self._config, "llm", None)
        return bool(
            self._llm_budget is not None
            and llm is not None
            and int(llm.max_concurrent) > 1
            and len(self._config.agents) > 1
        )

    def _decide_in_parallel(
        self,
        ctx: _EventContext,
        policies: Mapping[str, Policy],
        round_no: int,
        order: Sequence[str],
    ) -> list[Intent | Refusal]:
        """Decide the round in waves of at most `max_concurrent`, in the seeded order.

        The order matters: `_apply` walks the intents and the first bid on a ticket wins, so
        collecting in submission order (not completion order) keeps a live run as
        reproducible as the scripted one. Every future in a wave is waited for, so a failure
        in one agent cannot leave a child running behind the round.

        The kill switch is polled before each wave, not only before the round. That is what
        bounds a token or dollar trip to one wave of in-flight children instead of every
        agent in the round: once a cap has been crossed, no further wave is submitted.
        """
        active = [agent_id for agent_id in order if not self._budget.is_frozen(agent_id)]
        views = {agent_id: self._view(ctx, agent_id, round_no) for agent_id in active}
        workers = max(1, min(int(self._config.llm.max_concurrent), len(active)))
        results: dict[str, list[Intent | Refusal]] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for start in range(0, len(active), workers):
                self._check_kill()
                wave = active[start : start + workers]
                futures = {
                    agent_id: pool.submit(policies[agent_id].decide, views[agent_id])
                    for agent_id in wave
                }
                for agent_id in wave:
                    results[agent_id] = list(futures[agent_id].result())
        return [decision for agent_id in active if agent_id in results
                for decision in results[agent_id]]

    def _decision_order(self, event_id: str, round_no: int) -> list[str]:
        """The seeded shuffle of agent ids for this event and round. Stable, per round."""
        order = [spec.agent_id for spec in self._config.agents]
        random.Random(_derived_seed(self._config.seed, event_id, round_no, "order")).shuffle(order)
        return order

    def _view(self, ctx: _EventContext, agent_id: str, round_no: int) -> MarketView:
        event = ctx.event
        return MarketView(
            round=round_no,
            rounds_left=max(1, event.rounds - round_no + 1),
            event_id=event.event_id,
            mode=event.mode,
            face_lamports=event.face_lamports,
            cap_bps=ctx.cap_bps,
            ceiling_lamports=ctx.ceiling,
            tickets_available=ctx.house_stock,
            holdings=tuple(ctx.holdings[agent_id]),
            last_prices=tuple(ctx.last_prices[-LAST_PRICE_WINDOW:]),
            refused_attempts=ctx.refused[agent_id],
            agent_id=agent_id,
            seed=self._config.seed,
        )

    def _apply(self, ctx: _EventContext, round_no: int, intents: Sequence[Intent]) -> None:
        primaries: list[Intent] = []
        bids: list[Intent] = []
        asks: list[Intent] = []
        listings: list[Intent] = []
        broken: list[Intent] = []
        for intent in intents:
            if intent.agent_id not in ctx.holdings:
                raise ValueError(f"intent for unknown agent {intent.agent_id!r}")
            if intent.action == "buy":
                if not _price_ok(intent.price_lamports):
                    broken.append(intent)
                elif intent.price_lamports <= ctx.event.face_lamports:
                    primaries.append(intent)
                else:
                    bids.append(intent)
            elif intent.action == "resell":
                asks.append(intent)
            elif intent.action == "list":
                listings.append(intent)
            else:
                broken.append(intent)

        # One agent freezing on its budget must not stop the round: the action writes no
        # row and the other agents go on. `_AgentFrozen` is the only exception caught here.
        for intent in sorted(primaries, key=self._intent_key):
            self._act(self._primary_buy, ctx, intent, round_no)
        consumed: set[int] = set()
        for intent in sorted(asks, key=lambda i: (i.price_lamports or 0, i.agent_id)):
            buyer = self._act(self._resell, ctx, intent, bids, round_no)
            if buyer is not None:
                consumed.add(id(buyer))
        for intent in sorted(listings, key=self._intent_key):
            self._act(self._listing, ctx, intent)
        for intent in sorted(broken, key=self._intent_key):
            self._act(self._broken, ctx, intent)
        # Demand-side censoring. An ask nobody meets is already written down, but an unfilled
        # bid used to vanish, which made the dataset structurally blind to the buyer's side:
        # a market with no demand and a market with no supply produced the same absence of
        # rows. Every bid that no ask consumed gets one `skipped` row saying why, so the
        # spread can be measured later instead of inferred from a silence.
        for intent in sorted(bids, key=self._intent_key):
            if id(intent) in consumed:
                continue
            self._act(self._unmet_bid, ctx, intent)

    @staticmethod
    def _act(action, ctx: _EventContext, *args):
        """Run one action, swallowing a per-agent freeze and nothing else.

        `_AgentFrozen` means the agent's own budget refused this action, so the action leaves
        no row; a `_Kill` (a total breach, the flag file, the wall clock) propagates and
        `run()` stops the whole thing cleanly. Returns whatever the action returned, so the
        caller can learn which bid an ask consumed.
        """
        try:
            return action(ctx, *args)
        except _AgentFrozen:
            return None

    @staticmethod
    def _intent_key(intent: Intent) -> tuple:
        return (intent.agent_id, intent.action, intent.price_lamports or 0, intent.ticket_id or "")

    # -- the three actions -------------------------------------------------------

    def _holding_limit(self, agent_id: str) -> int:
        """How many units this agent may hold.

        Each agent's own `max_holdings` is the rule (one seat per participant by default).
        Passing `max_holdings=` to the runner sets a ceiling over all of them, for a test that
        wants to pin the limit; left unset, the config decides. A ceiling that defaulted to 1
        would silently defeat the per-agent field and make a market maker impossible.
        """
        own = self._holdings_by_agent.get(agent_id, DEFAULT_MAX_HOLDINGS)
        if self._max_holdings is None:
            return own
        return min(self._max_holdings, own)

    def _primary_buy(self, ctx: _EventContext, intent: Intent, round_no: int) -> None:
        """House -> agent at or below face. One unit, labelled here, hop 1."""
        agent_id = intent.agent_id
        price = intent.price_lamports
        if price is None:
            self._broken(ctx, intent)
            return
        held = ctx.holdings[agent_id]
        limit = self._holding_limit(agent_id)
        if len(held) >= limit:
            self._skipped(
                ctx, intent,
                f"holds {len(held)} ticket(s), at the limit {limit}; no purchase",
            )
            return
        if ctx.house_stock <= 0:
            self._skipped(ctx, intent, "the house has no stock left for this event")
            return
        try:
            self._budget.check(agent_id, price)
        except BudgetExceeded as exc:
            self._on_budget_refusal(exc)  # freezes and raises _AgentFrozen, or kills
            return
        self._check_kill()
        result = ctx.chain.transfer(
            from_label=ctx.house_label,
            to_label=self._wallet(agent_id),
            price_lamports=price,
            # A primary sale pays no artist fee: the house is selling the artist's own ticket at
            # face, so a fee here would be the artist paying themselves. The fee is on resales.
            charge_artist_fee=False,
            # And no flip tax, for the same reason plus one of its own: the tax is on a resale,
            # and the primary price is the artist's own stock at face, so a tax here would be the
            # artist charging the artist for a ticket that never left the house.
            charge_flip_tax=False,
        )
        if result.status != "ok":
            before, after = self._charge(agent_id, 0)
            self._write(
                ctx, agent_id=agent_id, action="buy", status=result.status,
                rationale=self._outcome_prose(
                    f"primary purchase at {price}",
                    success=False,
                    error_code=result.error_code,
                    tail="the unit stays with the house",
                ),
                price=price, from_wallet=ctx.house_label, to_wallet=self._wallet(agent_id),
                error_code=result.error_code, signature=result.signature, slot=result.slot,
                block_time=result.block_time, latency_ms=result.latency_ms, hop_index=1,
                budget_before=before, budget_after=after,
                policy_note=intent.rationale,
                fee_lamports=self._fee_paid(result),
                result=result,
            )
            return
        before, after = self._charge(agent_id, price)
        ticket_id = self._new_ticket(ctx)
        ctx.house_stock -= 1
        ctx.hops[ticket_id] = 1
        held.append(
            Holding(ticket_id=ticket_id, lot_price_lamports=price, acquired_round=round_no)
        )
        ctx.last_prices.append(price)
        self._write(
            ctx, agent_id=agent_id, action="buy", status="ok",
            rationale=(
                f"primary purchase of one unit from the house at {price}, at or below face "
                f"{ctx.event.face_lamports}; unit labelled {ticket_id} by the harness, the "
                "chain sees one base unit"
            ),
            price=price, ticket_id=ticket_id, from_wallet=ctx.house_label,
            to_wallet=self._wallet(agent_id), signature=result.signature, slot=result.slot,
            block_time=result.block_time, latency_ms=result.latency_ms, hop_index=1,
            budget_before=before, budget_after=after,
            policy_note=intent.rationale,
            # A primary purchase runs through the same `transfer` the resale does, so on an
            # event with a fee policy it pays the fee as well and the row says so. Whether the
            # primary sale should be exempt is a pricing decision, not a wiring one: it would
            # take a second sale path with its own meaning, and the harness has one.
            fee_lamports=self._fee_paid(result),
            # The same transfer carries the tax columns, and its result is the one place they
            # come from: `_write` reads all three off it rather than taking them one at a time.
            result=result,
        )

    def _resell(
        self, ctx: _EventContext, ask: Intent, bids: Sequence[Intent], round_no: int
    ) -> Intent | None:
        """One ask against the best eligible bid, executed at the ask price.

        Returns the bid the ask consumed, or None. The caller uses that to decide which
        bids are still unmet demand and therefore owe a `skipped` row.
        """
        agent_id = ask.agent_id
        price = ask.price_lamports
        if price is None:
            self._broken(ctx, ask)
            return
        held = ctx.holdings[agent_id]
        if not held:
            self._skipped(ctx, ask, f"asks {price} but holds no ticket; nothing to transfer")
            return
        if self._budget.is_frozen(agent_id):
            # The ask is recorded even though it was never placed: a supply-side order that
            # vanishes without a row is indistinguishable from an agent that chose not to
            # sell, and the dataset exists to tell those apart.
            self._write_frozen(ctx, agent_id, "resell", price, ask.ticket_id,
                               "the seller is frozen on its budget, so the ask was not placed",
                               policy_note=ask.rationale)
            return
        holding = self._pick_holding(held, ask.ticket_id)
        buyer = self._best_bid(ctx, ask, bids, price)
        if buyer is None:
            self._skipped(
                ctx, ask,
                f"no bid met the ask {price}: the best bids were below it or ineligible, so "
                "the unit did not move and this row is a censored ask, not a filled one",
            )
            return
        self._check_kill()
        result = ctx.chain.transfer(
            from_label=self._wallet(agent_id),
            to_label=self._wallet(buyer.agent_id),
            price_lamports=price,
            # The fee is on resales, so this sale pays it and says so rather than leaning on the
            # default: the flag is named at every call site so a new one cannot inherit it unseen.
            charge_artist_fee=True,
            # The flip tax is on the same resale and is named the same way: this is the sale it
            # exists for, and a call site that wants it off says so at its own site.
            charge_flip_tax=True,
        )
        hop = ctx.hops.get(holding.ticket_id, 1) + 1
        if result.status != "ok":
            before, after = self._charge(agent_id, 0)
            ctx.refused[agent_id] += 1
            self._write(
                ctx, agent_id=agent_id, action="resell", status=result.status,
                rationale=self._outcome_prose(
                    f"ask {price} matched bid {buyer.price_lamports}",
                    success=False,
                    error_code=result.error_code,
                    tail="the unit stays with the seller",
                ),
                price=price, ticket_id=holding.ticket_id, from_wallet=self._wallet(agent_id),
                to_wallet=self._wallet(buyer.agent_id), bid=buyer.price_lamports,
                lot=holding.lot_price_lamports, error_code=result.error_code,
                signature=result.signature, slot=result.slot, block_time=result.block_time,
                latency_ms=result.latency_ms,
                # No hop: the unit did not move. Writing `hop` here used to record a hop the
                # chain rolled back, which is exactly the kind of quiet fiction this dataset
                # must not contain.
                hop_index=None,
                budget_before=before, budget_after=after,
                policy_note=ask.rationale,
                fee_lamports=self._fee_paid(result),
                result=result,
            )
            return buyer
        buyer_before, buyer_after = self._charge(buyer.agent_id, price)
        held.remove(holding)
        ctx.holdings[buyer.agent_id].append(
            Holding(ticket_id=holding.ticket_id, lot_price_lamports=price, acquired_round=round_no)
        )
        # The row's actor is the seller, so its budget columns are the seller's. The money left
        # the buyer, and an earlier version wrote the buyer's figures under the seller's name,
        # which made `budget_after` grouped by `agent_id` neither agent's spend. The buyer's
        # commitment is stated here instead, and is checked by a test.
        seller_spent = self._spent(agent_id)
        ctx.hops[holding.ticket_id] = hop
        ctx.last_prices.append(price)
        self._write(
            ctx, agent_id=agent_id, action="resell", status="ok",
            rationale=(
                f"ask {price} matched bid {buyer.price_lamports} and executed at the ask; "
                f"the seller set the price and the buyer accepted it, lot was "
                f"{holding.lot_price_lamports}, hop {hop}; buyer {buyer.agent_id} committed "
                f"{price} lamports from its own budget ({buyer_before} -> {buyer_after})"
            ),
            price=price, ticket_id=holding.ticket_id, from_wallet=self._wallet(agent_id),
            to_wallet=self._wallet(buyer.agent_id), bid=buyer.price_lamports,
            lot=holding.lot_price_lamports, signature=result.signature, slot=result.slot,
            block_time=result.block_time, latency_ms=result.latency_ms, hop_index=hop,
            budget_before=seller_spent, budget_after=seller_spent,
            policy_note=ask.rationale,
            fee_lamports=self._fee_paid(result),
            result=result,
        )
        return buyer

    def _unmet_bid(self, ctx: _EventContext, bid: Intent) -> None:
        """A limit order that no ask met. One row, and the reason it went unfilled."""
        self._check_kill()
        price = bid.price_lamports
        if not _price_ok(price):
            self._broken(ctx, bid)
            return
        if self._budget.is_frozen(bid.agent_id):
            why = "the buyer is frozen on its budget, so the bid was not placed"
        elif len(ctx.holdings[bid.agent_id]) >= self._holding_limit(bid.agent_id):
            why = (
                f"the buyer already holds {len(ctx.holdings[bid.agent_id])} ticket(s), the limit "
                f"{self._holding_limit(bid.agent_id)}, so the bid could not be filled"
            )
        else:
            why = (
                f"no ask at or below the bid {price} lamports was offered this round, so the "
                "unit did not move and this row is a censored bid, not a filled one"
            )
        self._skipped(ctx, bid, why)

    def _listing(self, ctx: _EventContext, intent: Intent) -> None:
        """A listing is a harness record. `cap_hook` has no listing instruction."""
        self._check_kill()
        price = intent.price_lamports
        if not _price_ok(price):
            self._broken(ctx, intent)
            return
        before, after = self._charge(intent.agent_id, 0)
        held = ctx.holdings[intent.agent_id]
        ticket_id = self._pick_holding(held, intent.ticket_id).ticket_id if held else None
        self._write(
            ctx, agent_id=intent.agent_id, action="list", status="ok",
            rationale=(
                f"listing at {price} is a harness record only: cap_hook has no listing "
                "instruction, so nothing on chain recorded it and no unit moved"
            ),
            price=price, ticket_id=ticket_id,
            hop_index=ctx.hops.get(ticket_id) if ticket_id is not None else None,
            budget_before=before, budget_after=after,
            policy_note=intent.rationale,
        )

    def _broken(self, ctx: _EventContext, intent: Intent) -> None:
        """An intent this harness cannot read. Recorded as an error, not swallowed."""
        self._check_kill()
        before, after = self._charge(intent.agent_id, 0)
        # The action column is a closed vocabulary, so an unreadable action is written as
        # `unknown` and the intent's own word goes into the rationale rather than into a
        # column a reader groups by.
        action = intent.action if intent.action in INTENT_ACTIONS else "unknown"
        self._write(
            ctx, agent_id=intent.agent_id, action=action, status="error",
            rationale=(
                f"intent {intent.action!r} at price {intent.price_lamports!r} cannot be "
                "applied: a buy or resell needs an integer lamport price"
            ),
            price=intent.price_lamports,
            budget_before=before, budget_after=after,
            policy_note=intent.rationale,
        )

    def _outcome_prose(
        self, subject: str, *, success: bool, error_code: int | None, tail: str
    ) -> str:
        """One sentence about what happened, that cannot describe a send that never happened.

        A dry run predicts the hook's verdict from the same predicate the chain uses, but it
        builds, signs and sends nothing. The row used to say "was sent; the chain refused it",
        which is a sentence about a transaction that did not exist -- exactly the kind of
        quiet fiction the `chain` column is supposed to prevent, in the one field a human
        actually reads.
        """
        if self._chain_name == "simulated":
            if success:
                return (
                    f"{subject}: the hook would admit it. Simulated: no transaction was built, "
                    "signed or sent"
                )
            code = f" with {error_code}" if error_code is not None else ""
            return (
                f"{subject}: the hook would refuse it{code} against the ceiling "
                f"{self._ceiling_for_prose} lamports, so no unit moved. Simulated: no "
                "transaction was built, signed or sent"
            )
        if success:
            return f"{subject} and executed; {tail}"
        code = f" with error code {error_code}" if error_code is not None else ""
        return f"{subject} and was sent; the chain refused it{code}, so {tail}"

    def _write_frozen(
        self, ctx: _EventContext, agent_id: str, action: str, price: int | None,
        ticket_id: str | None, rationale: str, policy_note: str | None = None,
    ) -> None:
        """One row for an action a frozen agent did not take. No charge, no budget movement."""
        spent = self._spent(agent_id)
        self._write(
            ctx, agent_id=agent_id, action=action, status="skipped", rationale=rationale,
            price=price, ticket_id=ticket_id, bid=None, lot=None, hop_index=None,
            budget_before=spent, budget_after=spent, policy_note=policy_note,
        )

    def _skipped(self, ctx: _EventContext, intent: Intent, rationale: str) -> None:
        self._check_kill()
        before, after = self._charge(intent.agent_id, 0)
        self._write(
            ctx, agent_id=intent.agent_id, action=intent.action, status="skipped",
            rationale=rationale, price=intent.price_lamports,
            bid=None, lot=None, hop_index=None,
            budget_before=before, budget_after=after,
            policy_note=intent.rationale,
        )

    def _split_refusals(
        self, ctx: "_EventContext", decisions: Sequence[Intent | Refusal]
    ) -> list[Intent]:
        """Write one `skipped` row per refusal, hand back the intents in arrival order.

        The parallel path collects decisions as a flat list because that is what `_apply`
        consumes; a refusal has to become a row before it gets there, or it would reach
        `_apply` and be classified as a broken intent.
        """
        intents: list[Intent] = []
        for decision in decisions:
            if isinstance(decision, Refusal):
                self._policy_refused(ctx, decision)
            else:
                intents.append(decision)
        return intents

    def _policy_refused(self, ctx: _EventContext, refusal: Refusal) -> None:
        """One `skipped` row for a decision a policy declined to make. No charge, no move.

        This is the live adapter's own cap refusing *before* it spent anything, so the row
        is the honest record: nothing was ordered, nothing moved, and the rationale names
        the cap and its numbers. Recorded as `error` it would blame the market for the
        policy's budget; raised as an exception it would kill the dataset instead of
        carrying the refusal inside it.

        The action is the refusal's own, which `ForgePolicy` sets to `refuse`. It used to
        be `buy`, and every reader that groups by action then counted a decision nobody
        took as a purchase.
        """
        spent = self._spent(refusal.agent_id)
        self._write(
            ctx, agent_id=refusal.agent_id, action=refusal.action, status="skipped",
            rationale=refusal.rationale, price=refusal.price_lamports,
            bid=None, lot=None, hop_index=None,
            budget_before=spent, budget_after=spent,
        )

    # -- matching ----------------------------------------------------------------

    def _best_bid(
        self, ctx: _EventContext, ask: Intent, bids: Sequence[Intent], ask_price: int
    ) -> Intent | None:
        """Highest bid at or above the ask; ties to the lower agent id.

        A bid whose buyer cannot afford the ask is simply not eligible -- that is what a
        limit in an order book means -- so it neither freezes the buyer nor writes a row.
        A bid that would breach a *total* is a run-level event and trips the kill switch.
        """
        ordered = sorted(
            (bid for bid in bids if bid.price_lamports is not None),
            key=lambda bid: (-int(bid.price_lamports), bid.agent_id),
        )
        for bid in ordered:
            price = int(bid.price_lamports)
            if price < ask_price:
                break  # sorted descending: nothing below this can meet the ask either
            if bid.agent_id == ask.agent_id:
                continue
            if self._budget.is_frozen(bid.agent_id):
                continue
            if len(ctx.holdings[bid.agent_id]) >= self._holding_limit(bid.agent_id):
                continue
            try:
                self._budget.check(bid.agent_id, ask_price)
            except BudgetExceeded as exc:
                if exc.kind in TOTAL_BUDGET_KINDS:
                    self._on_budget_refusal(exc)
                continue
            return bid
        return None

    @staticmethod
    def _pick_holding(held: Sequence[Holding], ticket_id: str | None) -> Holding:
        """The named unit if the seller holds it, else the oldest one (FIFO)."""
        if ticket_id is not None:
            for holding in held:
                if holding.ticket_id == ticket_id:
                    return holding
        return held[0]

    # -- budget and kill ---------------------------------------------------------

    def _spent(self, agent_id: str) -> int:
        for entry in self._budget.state().agents:
            if entry.agent_id == agent_id:
                return entry.spent_lamports
        raise KeyError(f"unknown agent_id {agent_id!r}")

    def _on_budget_refusal(self, exc: BudgetExceeded) -> None:
        """A total breach kills the run; an agent breach freezes that one agent."""
        if exc.kind in TOTAL_BUDGET_KINDS:
            raise _Kill(
                f"{exc.kind} breached: agent {exc.agent_id} requested {exc.requested} "
                f"lamports, spent {exc.spent}, limit {exc.limit}"
            ) from exc
        self._budget.freeze(
            exc.agent_id,
            f"{exc.kind}: requested {exc.requested}, spent {exc.spent}, limit {exc.limit}",
        )
        raise _AgentFrozen(exc.agent_id) from exc

    def _charge(self, agent_id: str, lamports: int) -> tuple[int, int]:
        """Check, then charge one action. Returns (spent before, spent after).

        Raises `_AgentFrozen` (no row, agent frozen) or `_Kill` (run stops). Never mutates
        on a refusal: `BudgetTracker` guarantees that, and the row that follows carries the
        truthful before/after.
        """
        before = self._spent(agent_id)
        # The per-agent limits reset per event; the run's total does not. `total_budget_*` was
        # granted once per event by a per-event tracker, so two events doubled it silently.
        if lamports > 0 and self._run_spent + lamports > self._config.total_budget_lamports:
            raise _Kill(
                f"total budget: the run has committed {self._run_spent} of "
                f"{self._config.total_budget_lamports} lamports and this action needs {lamports}"
            )
        if self._run_actions + 1 > self._config.total_budget_actions:
            raise _Kill(
                f"total budget: the run has taken {self._run_actions} of "
                f"{self._config.total_budget_actions} actions"
            )
        try:
            self._budget.check(agent_id, lamports)
        except BudgetExceeded as exc:
            self._on_budget_refusal(exc)
            raise  # unreachable: _on_budget_refusal always raises
        self._budget.charge(agent_id, lamports)
        self._run_spent += lamports
        self._run_actions += 1
        return before, self._spent(agent_id)

    def _check_kill(self) -> None:
        """Before every action: a prior trip, the flag file, the wall clock, then the LLM caps."""
        if self._kill_reason is not None:
            raise _Kill(self._kill_reason)
        flag = Path(self._config.out_dir) / KILL_FLAG_NAME
        if flag.exists():
            raise _Kill(f"kill flag file present: {KILL_FLAG_NAME}")
        cap = self._config.kill_after_seconds
        if cap is not None:
            elapsed = self._clock() - self._started
            if elapsed >= cap:
                raise _Kill(f"wall-clock cap reached: {elapsed:.3f}s of {cap}s")
        # The LLM caps are part of the same switch, not a second one: a tripped token or
        # dollar cap stops the run exactly as the flag file does, and the reason says which.
        if self._llm_budget is not None and self._llm_budget.trip_reason is not None:
            raise _Kill(self._llm_budget.trip_reason)

    # -- writing ----------------------------------------------------------------

    def _wallet(self, agent_id: str) -> str:
        for spec in self._config.agents:
            if spec.agent_id == agent_id:
                return spec.wallet_label
        raise KeyError(f"unknown agent_id {agent_id!r}")

    @staticmethod
    def _house_label(chain) -> str:
        """The label the gateway stocks to, asked of the object rather than imported.

        `CONTRACT.md` never names the house account, so this cannot be a constant: a gateway
        that calls it something else would take every primary buy down with "holds 0
        tickets". The chain object is asked first, the module that defined it second, and
        the default last. Nothing is imported here, so a test's fake gateway still works.
        """
        for candidate in ("house_label", "HOUSE_LABEL"):
            label = getattr(chain, candidate, None)
            if isinstance(label, str) and label:
                return label
        module = sys.modules.get(type(chain).__module__)
        label = getattr(module, "HOUSE_LABEL", None)
        if isinstance(label, str) and label:
            return label
        return DEFAULT_HOUSE_LABEL

    @staticmethod
    def _fee_paid(result) -> int | None:
        """What a transfer reported paying the artist, or `None` if it cannot say.

        Read with `getattr`, not off the class: the gateway is a seam and a test's stand-in
        result is allowed to be smaller than `TransferResult`, exactly as `_house_label`
        assumes of the chain it is handed. A result that predates the fee field reports
        `None`, which the dataset contract reads as "no fee recorded" rather than as "no fee
        paid", and the write below drops both columns for an event that has no policy anyway.
        """
        return getattr(result, "fee_lamports", None)

    @staticmethod
    def _flip_tax_from(result) -> tuple[int | None, int | None, int | None]:
        """What a transfer reported for the flip tax: `(lamports, bps, held_seconds)`.

        One helper rather than three keyword arguments at each sale call site: the three columns
        are one fact about one result, and the two call sites that move a unit hand the whole
        result to `_write`, which reads them here. The same `getattr` rule as `_fee_paid` applies
        -- a stand-in result that predates the tax reports `(None, None, None)` -- and a result
        that has the fields reports the gateway's own numbers, including the 0 for money that a
        refused sale did not move.
        """
        if result is None:
            return (None, None, None)
        return (
            getattr(result, "flip_tax_lamports", None),
            getattr(result, "flip_tax_bps", None),
            getattr(result, "held_seconds", None),
        )

    @staticmethod
    def _new_ticket(ctx: _EventContext) -> str:
        ctx.tickets_issued += 1
        return f"{ctx.event.event_id}#{ctx.tickets_issued:04d}"

    def _ts(self) -> str:
        stamp = datetime.fromtimestamp(self._clock(), tz=timezone.utc)
        return stamp.isoformat(timespec="seconds").replace("+00:00", "Z")

    def _write(
        self,
        ctx: _EventContext,
        *,
        agent_id: str,
        action: str,
        status: str,
        rationale: str,
        price: int | None = None,
        ticket_id: str | None = None,
        from_wallet: str | None = None,
        to_wallet: str | None = None,
        bid: int | None = None,
        lot: int | None = None,
        error_code: int | None = None,
        signature: str | None = None,
        slot: int | None = None,
        block_time: int | None = None,
        latency_ms: int | None = None,
        hop_index: int | None = None,
        budget_before: int = 0,
        budget_after: int = 0,
        round_no: int | None = None,
        policy_note: str | None = None,
        fee_lamports: int | None = None,
        result: object | None = None,
    ) -> None:
        if round_no is None:
            round_no = ctx.round_no
        # The fee columns come from the event, not from each call site: the rate is the same on
        # every row of a fee event, and an event with no policy gets `None` in both, so a
        # dataset from a run that names no fee is byte-identical to one written before the fee
        # existed. `fee_lamports` is passed in by the two actions that move a unit, because it
        # is the only part of a fee that is a fact about one action rather than about an event.
        # Read directly and not with `getattr`: a context whose event lost the field must fail
        # here, where the row is being built, rather than quietly stop charging the fee.
        fee_policy = ctx.event.artist_fee
        if fee_policy is None:
            fee_lamports = None
            artist_fee_bps = None
        else:
            artist_fee_bps = fee_policy.fee_bps
        # The flip tax columns, from the event in the same way and from the result in a different
        # one: the rate and the hold are facts about the sale, and they come off the transfer's
        # own result in one place here rather than being plumbed through every call site. An
        # event with no tax block writes `None` in all three and the row is byte-identical to one
        # written before the tax existed.
        tax_policy = ctx.event.flip_tax
        if tax_policy is None:
            flip_tax_lamports = flip_tax_bps = held_seconds = None
        else:
            flip_tax_lamports, flip_tax_bps, held_seconds = self._flip_tax_from(result)
        # The policy's own words, for an agent whose policy accounts for live decisions. The
        # runner writes the row's prose, and before this the child's sentence existed only in
        # the sidecar's log: a fallback row said what happened on chain and nothing about the
        # model decision that produced it. Bounded, and only for a live agent, so a scripted
        # dataset is byte-for-byte what it was.
        if policy_note and agent_id in self._live_agent_ids:
            rationale = f"{rationale}; policy said: {policy_note[:300]}"
        markup = markup_bps(price, ctx.event.face_lamports) if price is not None else None
        row = TradeRow(
            run_id=self._config.run_id,
            seq=self._rows + 1,
            ts=self._ts(),
            event_id=ctx.event.event_id,
            mode=ctx.event.mode,
            round=round_no,
            rounds_left=(
                None if round_no is None else max(0, ctx.event.rounds - round_no)
            ),
            agent_id=agent_id,
            action=action,
            ticket_id=ticket_id,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            price_lamports=price,
            face_lamports=ctx.event.face_lamports,
            cap_bps=ctx.cap_bps,
            ceiling_lamports=ctx.ceiling,
            markup_bps=markup,
            status=status,
            error_code=error_code,
            signature=signature,
            slot=slot,
            block_time=block_time,
            latency_ms=latency_ms,
            hop_index=hop_index,
            budget_before=budget_before,
            budget_after=budget_after,
            chain=self._chain_name,
            program=self._program_name(),
            rationale=rationale,
            bid_lamports=bid,
            lot_price_lamports=lot,
            fee_lamports=fee_lamports,
            artist_fee_bps=artist_fee_bps,
            flip_tax_lamports=flip_tax_lamports,
            flip_tax_bps=flip_tax_bps,
            held_seconds=held_seconds,
        )
        ctx.writer.write(row)
        self._rows += 1
        ctx.rows += 1
        self._by_status[status] = self._by_status.get(status, 0) + 1
        ctx.by_status[status] = ctx.by_status.get(status, 0) + 1
        self._by_agent[agent_id] = self._by_agent.get(agent_id, 0) + 1
        if status == "ok" and action in ("buy", "resell") and price is not None:
            self._notional += price

    def _write_meta(self, ctx: _EventContext, dataset_path: Path) -> None:
        """A sidecar beside every dataset: what it is, what it cost, and that it is synthetic.

        Wallet addresses are deliberately absent: the dataset names agents by label, and the
        label-to-address map is a run artefact, not something to publish.
        """
        llm = self._llm_meta()
        label = self._provenance_label(llm)
        meta = {
            "record": "meta",
            "synthetic": True,
            "schema_version": SCHEMA_VERSION,
            "label": LABEL,
            "disclaimer": DISCLAIMER,
            "run_id": self._config.run_id,
            # A crashed run left a complete-looking dataset behind, because the sidecar was
            # written on the exception path too and said nothing about completion. Both are
            # now explicit, so a truncated file cannot pass for a finished run.
            "complete": ctx.completed,
            "rounds_completed": ctx.rounds_completed,
            "event_id": ctx.event.event_id,
            "mode": ctx.event.mode,
            "cluster": self._config.cluster,
            "program": self._program_name(),
            # The id the rows were produced against, so the run's central claim is checkable from
            # the sidecar rather than from a config file beside it. Nothing row-level distinguishes
            # the two programs -- both enforce a cap -- so without this a reader has to take
            # `program: v2` on trust. A dry run has no deployed id and says null.
            "program_id": getattr(self._gateway, "program_id", None),
            "dry_run": self._config.dry_run,
            "face_lamports": ctx.event.face_lamports,
            "cap_bps": ctx.cap_bps,
            "ceiling_lamports": ctx.ceiling,
            "tickets": ctx.event.tickets,
            "rounds": ctx.event.rounds,
            "seed": self._config.seed,
            "agents": [
                {
                    "agent_id": spec.agent_id,
                    "policy": spec.policy,
                    "wallet_label": spec.wallet_label,
                    "budget_lamports": spec.budget_lamports,
                    "budget_actions": spec.budget_actions,
                }
                for spec in self._config.agents
            ],
            "budget": self._budget.snapshot(),
            # `provenance` is a separate field on purpose: a run whose caller-supplied
            # policies report no accounting has no llm block to write, and the note must
            # still be able to say that it cannot say. Before this, that case fell through
            # to "scripted agents", which for a live ForgePolicy was simply false.
            "provenance": label,
            "llm": llm,
            # Per-event, not run-wide: this sidecar is read as a description of the file beside
            # it, and a cumulative count there makes the last event claim every earlier event's
            # rows. `RunSummary` is where the run's own totals live.
            "rows": ctx.rows,
            "by_status": dict(sorted(ctx.by_status.items())),
            "kill_reason": self._kill_reason,
            "wall_seconds": max(0.0, self._clock() - self._started),
            "note": self._provenance_note(label),
        }
        path = Path(str(dataset_path).replace(".jsonl", ".meta.json"))
        path.write_text(
            json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _provenance_label(self, llm: dict | None) -> str:
        """`llm`, `policy`, `unknown` or `scripted`, in the terms the sidecar states them.

        `llm` is the wired path, with a run-level `LlmBudget`. `policy` means the caller's
        own policies reported their accounting. `unknown` means the caller supplied
        policies and nothing they report lets this run say which decisions a model made.
        `scripted` is only ever claimed when this runner built the policies itself, from
        the config, out of `agents.POLICIES`.
        """
        if llm is not None:
            return str(llm.get("provenance") or "llm")
        if self._policies is None:
            return "scripted"
        return "unknown"

    def _provenance_note(self, label: str) -> str:
        """What produced these rows, said no more confidently than the run can support.

        The note used to key off `_llm_budget` alone, so a live run given its policies
        through `policies=` published "Generated by scripted agents" — a false sentence
        about a dataset in which every row came from a model.
        """
        if label == "unknown":
            return (
                "Synthetic. Provenance unknown: caller-supplied policy. This run was given "
                "policies that do not report which decisions a model made, so neither this "
                "note nor the llm block claims one. It was produced against a local "
                "validator or in simulation and is not evidence about any real market "
                "price."
            )
        if label in ("llm", "policy"):
            return (
                "Synthetic. Generated by LLM agents, one pi child per decision, against a "
                "local validator or in simulation; it is not evidence about any real market "
                "price. The llm block records the model, the decisions and the spend, and "
                "the decision log keeps the agents' own words."
            )
        return (
            "Synthetic. Generated by scripted agents against a local validator or in "
            "simulation; it is not evidence about any real market price."
        )


__all__ = ["RunSummary", "SwarmRunner", "markup_bps", "DEFAULT_MAX_HOLDINGS"]
