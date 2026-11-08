"""The live-LLM layer: seven personas, the sandbox flags, and the run-wide money cap.

Three things live here and nothing else.

`PERSONAS` is the strategy each agent is asked to play, written as a system prompt for the
child. It is the same seven objectives the scripted policies in `market_swarm.agents`
implement, restated in plain English so a model given the same view is being asked the
same question. A persona is not evidence: it says the market is synthetic and that its
numbers are not evidence about real tickets, in the prompt itself, because the child has
no other way to know.

`hardened_flags` is the argv that turns a general `pi` child into one model call. This is
the module's one real guarantee and its limit is worth stating plainly: the flags remove
the child's tool surface, its context files and every installed extension except the model
provider, so the only thing it can do is answer. They do not sandbox a process that
ignores its own argv, and they are a list, not a judge.

`LlmBudget` is the run-wide cap, because `ForgePolicy`'s token budget is per agent and a
swarm of ten agents each inside its own budget is a swarm with no budget. It counts all
four billed counters and the reported dollar cost, is thread-safe because policies may
decide concurrently, and trips once: the first reason wins and later charges cannot
overwrite it.

What this module is NOT: a claim that a model-driven policy is better than a scripted one,
and a source of any number. Every figure it reports was reported to it by a child.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

#: The provider extension, relative to the operator's home. Kept as a relative fragment so
#: no home path is hardcoded in this module; `_default_provider_extension` expands it once
#: at import and the caller may override the path without touching this file.
_PROVIDER_EXTENSION_RELATIVE = "~/.pi/agent/npm/node_modules/pi-commandcode-provider/index.ts"


def _default_provider_extension(override: str | None = None) -> str:
    """The provider extension path, expanded from home unless `override` names one.

    The override is returned as given, not expanded and not checked: a test or a caller on
    another machine may point at a checkout, and whether that file exists is the child's
    problem to fail on, not this function's to guess.
    """
    if override is not None:
        return str(override)
    return os.path.expanduser(_PROVIDER_EXTENSION_RELATIVE)


#: The resolved path to the one extension a hardened child keeps. Without it there is no
#: `commandcode/...` provider on the child's side, and `--model` cannot resolve at all.
PROVIDER_EXTENSION: str = _default_provider_extension()

def _reply_instruction() -> str:
    """`forge_policy.REPLY_CONTRACT`, imported here rather than at module scope.

    The contract is quoted verbatim in every persona, never paraphrased: the child is graded
    on exactly the string `forge_policy` parses, so a drift between the two would be a
    silent change to what a valid reply means. The import is inside the function so this
    module has no import-time dependency on the module that spends the money.
    """
    from market_swarm.forge_policy import REPLY_CONTRACT

    return REPLY_CONTRACT


_NOT_EVIDENCE = (
    "The market is synthetic and every number in your view comes from a script, so it is "
    "not evidence about real tickets, real prices or how real people behave."
)

_NO_TOOLS = (
    "You have no tools available: you cannot read a file, run a command or reach a network, "
    "and your only output is the JSON contract below. "
)


def _personas() -> dict[str, str]:
    """The seven prompts, built once at import with the reply contract quoted in each.

    Each prompt is three parts and a contract: the objective, the statement that the market
    is synthetic and its numbers are not evidence, the statement that no tool is available,
    and then `REPLY_CONTRACT` verbatim. The objective is restated from the scripted policy of
    the same name in `market_swarm.agents`, so a model and a script given the same view are
    being asked the same question.
    """
    reply_instruction = _reply_instruction()
    return {
        "buyer": (
            "You are the buyer in a synthetic ticket market. Your objective is a seat "
            "at or near face value, so you take the primary ask while it is at or below "
            "face and you never pay a markup. Once you hold a ticket you stop, because "
            "one seat at face is the whole of what you want. "
            + _NOT_EVIDENCE
            + " "
            + _NO_TOOLS
            + reply_instruction
        ),
        "holder": (
            "You are the holder in a synthetic ticket market. Your objective is to hold "
            "a ticket to the last round and list it at a target markup over face, cutting "
            "the ask as the event approaches instead of dumping it early. You buy one "
            "ticket at face when you hold nothing, then relist, and a listing above the "
            "ceiling cannot fill. "
            + _NOT_EVIDENCE
            + " "
            + _NO_TOOLS
            + reply_instruction
        ),
        "flipper": (
            "You are the flipper in a synthetic ticket market. Your objective is to buy "
            "below the ceiling-derived threshold, relist once a markup over your cost is "
            "reachable inside the cap, and turn the same ticket over quickly rather than "
            "wait for a better price. When no markup is reachable inside the cap you "
            "stop buying rather than sell at a loss. "
            + _NOT_EVIDENCE
            + " "
            + _NO_TOOLS
            + reply_instruction
        ),
        "scalper": (
            "You are the scalper in a synthetic ticket market. Your objective is to "
            "relist as high as the on-chain cap allows, probing above it first and "
            "settling at the boundary once a transfer has been refused. A refusal is "
            "information about the cap, not a reason to stop, so you keep placing asks "
            "that a buyer might accept. "
            + _NOT_EVIDENCE
            + " "
            + _NO_TOOLS
            + reply_instruction
        ),
        "sniper": (
            "You are the sniper in a synthetic ticket market. Your objective is to wait "
            "through the early rounds and buy cheap in the last round, when the sellers "
            "are the ones under time pressure. You emit nothing while plenty of rounds "
            "remain, then make one bid and keep what it wins. "
            + _NOT_EVIDENCE
            + " "
            + _NO_TOOLS
            + reply_instruction
        ),
        "panic": (
            "You are the panic seller in a synthetic ticket market. Your objective is "
            "to sell low when prices fall, accepting a loss on your lot rather than "
            "carry a ticket you cannot clear before the deadline. You buy one ticket "
            "while there is time, then cut your ask round after round as the clock runs "
            "out, and a price below face is allowed because the cap only bounds above. "
            + _NOT_EVIDENCE
            + " "
            + _NO_TOOLS
            + reply_instruction
        ),
        "greater_fool": (
            "You are the greater fool in a synthetic ticket market. Your objective is "
            "to buy high in the later rounds, bidding above face and above the cap for "
            "as long as you have room to hold another ticket. You do not discipline your "
            "own price, because the demand you represent is exactly the demand a resale "
            "cap exists to refuse. "
            + _NOT_EVIDENCE
            + " "
            + _NO_TOOLS
            + reply_instruction
        ),
    }


PERSONAS: Mapping[str, str] = MappingProxyType(_personas())


def persona_for(policy_name: str) -> str:
    """The system prompt for a policy name, or `ValueError` naming the names that work.

    Deliberately strict: a typo in a run config must stop the run, not quietly hand the
    child a prompt about a different strategy and write the result into the dataset.
    """
    try:
        return PERSONAS[policy_name]
    except KeyError:
        raise ValueError(
            f"unknown policy {policy_name!r}; valid personas are {sorted(PERSONAS)}"
        ) from None


def hardened_flags(provider_extension: str | None = None) -> tuple[str, ...]:
    """The argv that leaves one model call and nothing else, in this exact order.

    Each entry is here for a specific reason:

    - `--no-extensions` drops every installed extension, which on this machine includes several
      unrelated ones as well as the model provider.
    - `-e <provider>` then re-adds exactly one of them. Without the provider extension the
      child has no `commandcode/...` provider, and `--model commandcode/...` cannot resolve,
      so the child never starts.
    - `--approve` trusts the scratch project directory, which is what lets its
      `.pi/SYSTEM.md` replace the operator's global prompt instead of being appended to it.
    - `--no-context-files` keeps `AGENTS.md` and anything else the child might walk up into
      out of its context, so the repository is not in the prompt.
    - `--no-skills`, `--no-mcp` and `--no-prompt-templates` remove the other three ways a
      child can acquire behaviour the caller did not write.
    - `--no-tools` is the load-bearing one: with it the child has no file, shell or network
      tool surface at all, so an injected instruction in a market view has nothing to run.

    What this returns is a list of arguments. It cannot stop a `pi` build that ignores its
    own flags, and it is not a container.
    """
    extension = _default_provider_extension(provider_extension)
    return (
        "--no-extensions",
        "-e",
        extension,
        "--no-tools",
        "--no-skills",
        "--no-context-files",
        "--no-mcp",
        "--no-prompt-templates",
        "--approve",
    )


class LlmKilled(RuntimeError):
    """The run-wide cap is spent. Carries the reason so the CLI can write it verbatim."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason: str = str(reason)


def _as_int(value: object) -> int:
    """An integer count, or 0 for anything that is not one. Never raises."""
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _as_float(value: object) -> float:
    """A dollar figure, or 0.0 for anything that is not one. Never raises."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    return number if number == number else 0.0  # NaN is not a cost


def _money(value: float) -> str:
    """A dollar amount with the trailing zeros trimmed, so a message reads as a number."""
    text = f"{value:.12f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


class LlmBudget:
    """The run-wide token and dollar cap, shared by every live policy in the run.

    `ForgePolicy`'s own `token_budget` is per agent, and a swarm of ten agents each inside
    its own budget is a swarm with no budget. This object is the one the whole run shares:
    it accumulates all four billed counters plus the reported dollar cost, and it trips
    once.

    Two properties matter more than the arithmetic. It is thread-safe, because policies may
    be deciding concurrently and a lost increment is a lost cap. And `charge` never raises:
    it runs inside the child's stream loop, where a raise would abandon a live process; the
    kill is `check`, which the policy calls before its next decision. `trip_reason` is
    first-wins, so the reason the run reports is the reason it actually stopped, not the
    last one to notice.
    """

    def __init__(
        self,
        *,
        total_token_budget: int,
        cost_cap_usd: float | None = None,
        prices: Any = None,
    ) -> None:
        if isinstance(total_token_budget, bool) or not isinstance(total_token_budget, int):
            raise TypeError(
                "total_token_budget must be an int, got "
                f"{total_token_budget!r} ({type(total_token_budget).__name__})"
            )
        if total_token_budget <= 0:
            raise ValueError(
                f"total_token_budget must be positive, got {total_token_budget}; a cap of "
                "zero would trip on the first charge and a negative one is not a cap"
            )
        if cost_cap_usd is not None:
            if isinstance(cost_cap_usd, bool) or not isinstance(cost_cap_usd, (int, float)):
                raise TypeError(
                    f"cost_cap_usd must be a float or None, got {cost_cap_usd!r}"
                )
            if float(cost_cap_usd) <= 0:
                raise ValueError(
                    f"cost_cap_usd must be positive or None, got {cost_cap_usd}; pass None "
                    "for no dollar cap rather than zero"
                )
        self._total_token_budget: int = total_token_budget
        self._cost_cap_usd: float | None = (
            None if cost_cap_usd is None else float(cost_cap_usd)
        )
        #: A `config.PriceTable`-shaped object with `cost_usd(usage)`, or None. Used only
        #: when a child reports no cost of its own; a configured cap must still be measured.
        self._prices = prices
        self._lock = threading.Lock()
        self._input: int = 0
        self._output: int = 0
        self._cache_read: int = 0
        self._cache_write: int = 0
        self._usd: float = 0.0
        #: Which source produced the dollars, so the meta sidecar can say it honestly.
        self._usd_from_stream: float = 0.0
        self._usd_from_table: float = 0.0
        self._pricing_errors: int = 0
        self._trip_reason: str | None = None

    # -- accumulation -----------------------------------------------------------------

    def charge(self, usage: object) -> None:
        """Fold one child's reported usage in, and trip if this crosses a cap.

        `usage` is `forge_policy.Usage`-shaped: `.input`, `.output`, `.cache_read`,
        `.cache_write` and `.usd`, and a `.total` that is the sum of the first four. Any
        field that is missing or not a number counts as zero rather than raising, because a
        provider that omits a counter is a reporting gap and not a reason to lose the
        tokens it did report.
        """
        # Clamped at zero: a negative counter must never subtract from a cap. The child is
        # a process reading a prompt, and a bug that reports -1000 tokens could otherwise
        # keep a run under its limit while it spent the money.
        delta_input = max(0, _as_int(getattr(usage, "input", 0)))
        delta_output = max(0, _as_int(getattr(usage, "output", 0)))
        delta_read = max(0, _as_int(getattr(usage, "cache_read", 0)))
        delta_write = max(0, _as_int(getattr(usage, "cache_write", 0)))
        delta_usd = max(0.0, _as_float(getattr(usage, "usd", 0.0)))
        stream_usd = delta_usd
        pricing_failed = False
        if delta_usd == 0.0 and self._prices is not None:
            # The provider reported no cost for this request. Fall back to the configured
            # rates rather than silently counting the spend as free; a cap that cannot see
            # a charge is not a cap.
            try:
                delta_usd = float(self._prices.cost_usd(usage))
            except Exception:
                delta_usd = 0.0
                pricing_failed = True
        with self._lock:
            self._input += delta_input
            self._output += delta_output
            self._cache_read += delta_read
            self._cache_write += delta_write
            # Rounded on every fold: a float sum of a thousand small charges drifts in the
            # twelfth decimal, and a cap compared against drifting noise trips on rounding.
            self._usd = round(self._usd + delta_usd, 12)
            if pricing_failed:
                self._pricing_errors += 1
                # A dollar cap that cannot be measured is not a cap. The run stops rather
                # than reporting "under cap" forever while the money leaves.
                if self._cost_cap_usd is not None and self._trip_reason is None:
                    self._trip_reason = (
                        "llm cost cap unmeasurable: the configured price table raised on "
                        f"{self._pricing_errors} request(s)"
                    )
            if stream_usd > 0:
                self._usd_from_stream = round(self._usd_from_stream + stream_usd, 12)
            elif delta_usd > 0:
                self._usd_from_table = round(self._usd_from_table + delta_usd, 12)
            if self._trip_reason is not None:
                return
            spent = self._input + self._output + self._cache_read + self._cache_write
            if spent > self._total_token_budget:
                self._trip_reason = (
                    f"llm token budget exceeded: {spent} of "
                    f"{self._total_token_budget} tokens"
                )
                return
            if self._cost_cap_usd is not None and self._usd > self._cost_cap_usd:
                self._trip_reason = (
                    f"llm cost cap exceeded: ${_money(self._usd)} of "
                    f"${_money(self._cost_cap_usd)}"
                )

    def check(self) -> None:
        """Raise `LlmKilled` if the run is over budget, else return None.

        This is the kill switch: `ForgePolicy` calls it before spending on a child, so the
        cap stops the next decision rather than the one already in flight.
        """
        reason = self.trip_reason
        if reason is not None:
            raise LlmKilled(reason)

    # -- reporting ---------------------------------------------------------------------

    @property
    def usage(self) -> Any:
        """The aggregate as a `forge_policy.Usage`, which is what a caller already handles.

        Imported here rather than at module scope so this module has no import-time
        dependency on the policy that spends the money.
        """
        from .forge_policy import Usage

        with self._lock:
            return Usage(
                input=self._input,
                output=self._output,
                cache_read=self._cache_read,
                cache_write=self._cache_write,
                usd=round(self._usd, 12),
            )

    @property
    def usd(self) -> float:
        """Dollars spent so far, as reported by the children themselves."""
        with self._lock:
            return round(self._usd, 12)

    @property
    def trip_reason(self) -> str | None:
        """The first cap that was crossed, or None while the run is still allowed."""
        with self._lock:
            return self._trip_reason

    def snapshot(self) -> dict:
        """The whole state as plain JSON-serialisable values, for the run's meta sidecar.

        `usd` is rounded to twelve decimals: the figure comes from float sums of tiny
        numbers, and a meta file carrying `0.000041099999999999` invites a reader to think
        the precision means something.
        """
        with self._lock:
            return {
                "trip_reason": self._trip_reason,
                "total_tokens": self._input
                + self._output
                + self._cache_read
                + self._cache_write,
                "input": self._input,
                "output": self._output,
                "cache_read": self._cache_read,
                "cache_write": self._cache_write,
                "usd": round(self._usd, 12),
                "total_token_budget": self._total_token_budget,
                "cost_cap_usd": self._cost_cap_usd,
                "cost_basis": self._cost_basis(),
                "cost_note": "provider-reported estimate, not a bill",
                "pricing_errors": self._pricing_errors,
            }

    def _cost_basis(self) -> str:
        """Where the dollar figure came from, so a meta file never implies billing.

        `stream` means the provider computed it per request; `table` means the configured
        `usd_per_mtok` rates were applied to the reported tokens; `unpriced` means neither,
        and the dollars shown are zero because nobody measured them, not because they were
        free.
        """
        if self._usd_from_stream > 0 and self._usd_from_table > 0:
            return "mixed"
        if self._usd_from_stream > 0:
            return "stream"
        if self._usd_from_table > 0:
            return "table"
        if self._pricing_errors > 0:
            return "table_error"
        return "unpriced"


#: The repository this module lives in, resolved once. A child's cwd may not be inside it:
#: the run directory holds the gateway's keypairs and the tree is the operator's work.
_REPO_ROOT = Path(__file__).resolve().parents[1]


def _checked_scratch_root(scratch_root: Any) -> Path:
    """Refuse a child cwd inside the repository, and return the resolved path otherwise.

    The tool surface is already empty (`--no-tools`), and this is the second layer: the cwd
    a prompt-following child is given is never inside the tree that holds the code, the
    datasets or the keypairs. A live run uses a temp directory; this refuses the accident.
    """
    resolved = Path(scratch_root).expanduser().resolve()
    if resolved == _REPO_ROOT or _REPO_ROOT in resolved.parents:
        raise ValueError(
            f"scratch_root {resolved} is inside the repository {_REPO_ROOT}; a live child's "
            "cwd belongs outside the tree, so it can never sit beside the keypairs under "
            "the run directory"
        )
    return resolved


def build_llm_policy(
    spec: Any,
    *,
    llm: Any,
    budget: LlmBudget,
    scratch_root: Any,
    spawn: Any = None,
    intended_cap_bps: int | None = None,
) -> Any:
    """A `ForgePolicy` wired to one persona, the hardened flags, and the run-wide cap.

    `llm` is the run's LLM block, read for `tier`, `per_agent_token_budget`, `max_concurrent`
    and `timeout_seconds`. `on_usage` feeds every child's reported usage into the shared
    `budget`, and `kill_check` is the same object's `check`, so the cap that stops the run
    is the cap the policies report into.

    The import is inside the function on purpose: `forge_policy` is the spending path and
    this module must be importable without it, which also keeps the dependency one-way.
    """
    from .forge_policy import ForgePolicy

    return ForgePolicy(
        spec,
        tier=llm.tier,
        token_budget=llm.per_agent_token_budget,
        max_decision_tokens=getattr(
            llm, "per_decision_token_budget", llm.per_agent_token_budget
        ),
        max_concurrent=llm.max_concurrent,
        timeout_seconds=llm.timeout_seconds,
        acknowledge_cost=True,
        spawn=spawn,
        system_prompt=persona_for(spec.policy),
        extra_argv=hardened_flags(),
        on_usage=budget.charge,
        kill_check=budget.check,
        scratch_root=_checked_scratch_root(scratch_root),
        intended_cap_bps=intended_cap_bps,
    )
