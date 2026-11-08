"""An opt-in `Policy` that lets one real `pi` child make one trading decision.

This module is a money switch, not a default. **One decision costs one child process.** On
the measured subforge history the same cheap tier has a p90 of ~207k output tokens per run
(median ~92k) and a median wall clock of 10.8 minutes, so a hundred decisions is roughly
20 million output tokens and tens of hours. That is the operator's call, never this
module's: constructing `ForgePolicy` raises `CostNotAcknowledged` until the caller passes
`acknowledge_cost=True`. The default path for dataset generation is the scripted policies
in `market_swarm.agents`, a dataset that costs a child process per decision is a research
toy, not a data source.

What it reuses from subforge, the adapter in the installed
`~/.pi/agent/extensions/pi-subforge/index.ts` (written up in
`records/findings/30-subforge-what-it-is.md`): the spawn argv
`pi --mode rpc --session-dir <dir> --name forge:<name> --model <provider>/<model>:<effort>`,
the prompt as one JSON line on stdin, one JSON object per line on stdout, completion on
`agent_end` with `willRetry` false, token totals summed from assistant `message_end`
records, and the three-step reap (abort over stdin, SIGTERM at 250 ms, SIGKILL at 5 s),
plus process-group kill so a `pi` child's own bash subprocesses die with it.

That reap is the parent's work and the wall clock is the parent's clock. The argv gives
the child **no limit of its own**: `maxRunSeconds` is this module's deadline, and
`start_new_session=True` puts the child in its own process group precisely so it outlives
a signal aimed at the parent. So a SIGKILLed parent leaks a spending `pi` child with no
wall clock and no token cap on it. The cap is parent-side; it holds while the parent is
alive, and nothing here claims otherwise.

Two things forge gets wrong that this module does not: it counts only `input`/`output`
(so cache reads and cache writes are free as far as its budget is concerned, this module
sums all four), and it writes `finished` at the first `agent_end` of an auto-retry chain
(this module requires `willRetry` to be false). A `finished` run is also not a success:
a provider failure emits `agent_end` with zero usage, so a reply is only accepted if it
parsed *and* the child reported tokens.

The child is a general agent, not a function call. What the key guarantee here is and is
not, in one place (`records/findings/31-trading-swarm-harness-design.md` is the design
record): this module passes no path in the prompt and handles no key material, but it
cannot sandbox a `pi` process, and it does not claim to.

Two optional constructor arguments shape the child without changing that: `system_prompt`
text, when given, is written to `<cwd>/.pi/SYSTEM.md` with an empty `.pi/APPEND_SYSTEM.md`
beside it, so the child reads a trusted project persona instead of inheriting the
operator's global `<agent-dir>/SYSTEM.md` on every turn; `extra_argv` is appended verbatim
to the spawn argv after `--model`, and is where the caller's sandbox flags go. Neither one
is a sandbox: a `pi` child launched with its default tool surface still has that tool
surface, and what removes it is the flags -- which this module passes through exactly as
handed to it and never invents, defaults or guesses on the caller's behalf.

`ForgeBudget` is the adapter's own money switch, and it is a hard one: a reservation is
made **before** a child is spawned, so a decision that would exceed the per-decision or
the total token cap is refused with nothing spent and nothing spawned. A refused decision
returns `agents.Refusal`, which the runner records as a `skipped` row; it is not an
exception, because an exception would kill the dataset instead of carrying the refusal
inside it. `timeout_seconds` is subforge's per-run `maxRunSeconds`, applied by this
module's own deadline and reap: no child is spawned without one, but the child does not
enforce it (see the parent-side note above).

Measured against a real provider on 2026-11-08 (`records/findings/41-...`): the wire carries
usage on assistant `message_end` records, repeats the in-flight message's usage on every
`message_update`, and also attaches the same message object to `turn_end`; counting every
record that happens to carry a `message` therefore bills one assistant message twice. Only
`message_end` is summed here, and `message_update` is read as a running total for the
message still streaming so the cap can fire before the message is finished. An update that
arrives after its own message's `message_end` repeats a total already billed, so it is
ignored rather than charged again.

What that cap can and cannot do: with no `message_update` in the stream, the only record
carrying usage is the `message_end`, which arrives after the tokens are bought. A cap
checked on that record records the overrun; it does not prevent it. A cap that can only
fire after the charge is not a cap on the charge, and this module does not pretend one is.
"""

from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from market_swarm import agents

#: Tier name -> (provider, model id, effort), copied from the active profile config.
#: All three name the same model and differ only by effort, which is why a wrong tier is
#: invisible in the output, hence `_model_for_tier` raises on an unknown name instead of
#: falling back to "no --model" the way subforge does (234 of 1,135 measured runs did).
TIER_MODELS: dict[str, tuple[str, str, str]] = {
    "low": ("commandcode", "deepseek/deepseek-v4.1-flash", "low"),
    "default": ("commandcode", "deepseek/deepseek-v4.1-flash", "high"),
    "best": ("commandcode", "deepseek/deepseek-v4.1-flash", "max"),
}

#: Scratch root, relative on purpose: no home path appears in this module, and the child's
#: cwd is a fresh, empty directory under it, never the repository. This is a git-ignored
#: run directory, not a repository path: nothing here is source, code or a dataset.
#:
#: It is resolved to an absolute path before the argv is built. Measured on a real child:
#: `--session-dir` and `cwd` are both relative, and `pi` resolves the former against the
#: latter, so a relative session dir landed at `<work>/<scratch>/<agent>/decision-1/session`
#: instead of beside the work directory. Two live children made that directory tree before
#: it was found.
SCRATCH_ROOT = Path(".swarm-runs") / "forge"

#: subforge's reap constants, `index.ts:591-601`: abort, SIGTERM at 250 ms, SIGKILL at 5 s.
REAP_TERM_GRACE_SECONDS = 0.25
REAP_KILL_GRACE_SECONDS = 5.0

#: How much observed price history the prompt carries. The view is already small; the
#: whole ledger never goes into a prompt.
LAST_PRICES_IN_PROMPT = 5

#: The default per-decision token cap: one child may not burn more than the measured p90
#: output of a cheap-tier forge run (~207k, rounded up to 250k). It is deliberately a
#: *per-child* figure and not the policy's whole budget: a reservation of the entire budget
#: would serialise every concurrent decision, because a second child could not be promised
#: any tokens at all. A caller with a smaller budget is still bounded by `token_budget`; the
#: reservation is the smaller of the two, so **admission** is never oversubscribed. It is not
#: a bound on the provider's bill: a child that burns more than its reservation is charged
#: for what it burned, `settle` records the overrun, and every later decision refuses.
DEFAULT_MAX_DECISION_TOKENS = 250_000

#: The exact reply contract, repeated verbatim in the prompt.
REPLY_CONTRACT = (
    'Reply with exactly one JSON object and nothing else: '
    '{"action": "buy" | "list" | "resell", "price_lamports": <integer>, '
    '"rationale": "<short>"}. No prose, no code fence, no extra keys.'
)

_PROMPT_PREFIX = (
    "You are one ticket-trading agent in a synthetic market. Prices are integer lamports. "
    "buy is a primary purchase; list puts an ask on a ticket you already hold; resell "
    "sells a ticket you already hold. "
    + REPLY_CONTRACT
    + " Your view is the JSON on the next line.\n"
)

#: The child's environment whitelist. Deliberately small: no wallet path, no keypair
#: variable, no cloud credential leaks into a process that only needs to reach its model.
_ENV_WHITELIST = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "TMPDIR")


class CostNotAcknowledged(RuntimeError):
    """Raised when a `ForgePolicy` is built without `acknowledge_cost=True`."""


@dataclass(frozen=True)
class Usage:
    """What one child actually cost: the four billed counters and the USD figure.

    A plain value with element-wise addition, so a decision can accumulate its own usage
    and hand it to the policy as one delta. It validates nothing: every producer is in
    this module, and `usage_from_record` is the single place the wire is interpreted.
    """

    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    usd: float = 0.0

    @property
    def total(self) -> int:
        """All four billed counters, not forge's two."""
        return self.input + self.output + self.cache_read + self.cache_write

    def __add__(self, other: "Usage") -> "Usage":
        if not isinstance(other, Usage):
            return NotImplemented
        return Usage(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_read=self.cache_read + other.cache_read,
            cache_write=self.cache_write + other.cache_write,
            usd=round(self.usd + other.usd, 12),
        )


class ForgeBudgetExceeded(RuntimeError):
    """A spend the adapter's own budget refuses, before any child is spawned.

    `kind` is "decision_tokens", "total_tokens" or "overrun", so a caller can branch on
    the refusal without parsing the message.
    """

    def __init__(self, kind: str, reason: str) -> None:
        self.kind = kind
        self.reason_text = reason
        super().__init__(f"{kind}: {reason}")


@dataclass(frozen=True)
class BudgetPosition:
    """An immutable snapshot of what the adapter's budget has seen."""

    decisions: int
    tokens: int
    total_tokens: int
    reserved_tokens: int
    max_decision_tokens: int
    seconds: float
    usd: float
    overrun: str | None

    @property
    def tokens_remaining(self) -> int:
        return self.total_tokens - self.tokens - self.reserved_tokens


class ForgeBudget:
    """The adapter's own hard caps, in the style of `market_swarm.budget`.

    Three rules, copied from `BudgetTracker` because a budget that disagrees with itself is
    not a budget:

    - **A check never mutates.** `reserve` either hands back a token reservation or raises,
      leaving every counter exactly as it was, so a refused decision leaves no trace.
    - **Reserve before spending.** The reservation is taken before the child is spawned, so
      two concurrent decisions cannot both spend the last of the cap; the reservation *is*
      the spend until the child settles it.
    - **Settle records the truth.** A child that burned more than its reservation is charged
      for what it actually burned - the money is gone - and the overrun is named, so every
      later `reserve` refuses instead of pretending the cap still holds.

    `max_decision_tokens` is the per-decision cap; the policy's `timeout_seconds` is the
    per-decision wall clock; `total_tokens` is the cap for the whole policy instance. Seconds
    and dollars are tracked and reported because the operator's ceiling is stated in
    dollars, but tokens and wall clock are what the budget can refuse *before* spending.
    """

    def __init__(self, *, total_tokens: int, max_decision_tokens: int) -> None:
        for name, value in (
            ("total_tokens", total_tokens),
            ("max_decision_tokens", max_decision_tokens),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name}: expected an integer, got {type(value).__name__}")
            if value <= 0:
                raise ValueError(f"{name}: must be positive, got {value}")
        self._total_tokens = int(total_tokens)
        self._max_decision_tokens = int(max_decision_tokens)
        self._lock = threading.Lock()
        self._spent_tokens = 0
        self._reserved_tokens = 0
        self._decisions = 0
        self._seconds = 0.0
        self._usd = 0.0
        self._overrun: str | None = None

    # -- read-only surface ------------------------------------------------------------

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def max_decision_tokens(self) -> int:
        return self._max_decision_tokens

    def position(self) -> BudgetPosition:
        """The immutable snapshot the caller records next to a decision."""
        with self._lock:
            return self._position_locked()

    def _position_locked(self) -> BudgetPosition:
        return BudgetPosition(
            decisions=self._decisions,
            tokens=self._spent_tokens,
            total_tokens=self._total_tokens,
            reserved_tokens=self._reserved_tokens,
            max_decision_tokens=self._max_decision_tokens,
            seconds=self._seconds,
            usd=self._usd,
            overrun=self._overrun,
        )

    # -- the two transitions budget.py has ---------------------------------------------

    def reserve(self) -> int:
        """Reserve this decision's token allowance, or raise. Never mutates on a refusal.

        Returns the number of tokens the next child may burn before it is killed. It is
        the smaller of the per-decision cap and the remaining total, so the *reservations*
        never exceed the total, and it is held until `settle` or `cancel`. The provider's
        bill can still exceed it: a child that overshoots is charged for what it burned and
        `settle` records the overrun, which refuses every later decision.
        """
        with self._lock:
            if self._overrun is not None:
                raise ForgeBudgetExceeded("overrun", self._overrun)
            headroom = self._total_tokens - self._spent_tokens - self._reserved_tokens
            if headroom <= 0:
                raise ForgeBudgetExceeded(
                    "total_tokens",
                    f"the adapter's token cap is spent: {self._spent_tokens} of "
                    f"{self._total_tokens} tokens across {self._decisions} decision(s), "
                    f"{self._reserved_tokens} more reserved",
                )
            reserved = min(self._max_decision_tokens, headroom)
            self._reserved_tokens += reserved
            return reserved

    def cancel(self, reserved: int) -> None:
        """Return a reservation that never became a child. Spend and decision count unchanged."""
        with self._lock:
            self._reserved_tokens = max(0, self._reserved_tokens - int(reserved))

    def settle(self, reserved: int, usage: Usage, seconds: float) -> BudgetPosition:
        """Record what a child actually burned and release its reservation.

        The charge is the observed usage, not the reservation: a child that overshot is
        charged for what it burned (the tokens are already paid for) and the overrun is
        recorded so nothing further may spend. Never raises: a decision that happened must
        be countable.
        """
        with self._lock:
            self._reserved_tokens = max(0, self._reserved_tokens - int(reserved))
            self._spent_tokens += int(usage.total)
            self._decisions += 1
            self._seconds = round(self._seconds + max(0.0, float(seconds)), 3)
            self._usd = round(self._usd + float(usage.usd), 12)
            if self._spent_tokens > self._total_tokens and self._overrun is None:
                self._overrun = (
                    f"a child burned {usage.total} tokens and took the adapter to "
                    f"{self._spent_tokens} of its {self._total_tokens} token cap; no "
                    "further decision may spend"
                )
            return self._position_locked()


class _Timeout(Exception):
    """The wall clock ran out before the child completed."""


class _Budget(Exception):
    """The per-agent token budget was exceeded mid-stream."""


class _BadReply(Exception):
    """The child answered, but not with a valid intent."""


def _model_for_tier(tier: str) -> str:
    """Resolve a tier name to the exact `--model` string subforge would pass."""
    entry = TIER_MODELS.get(tier)
    if entry is None:
        raise ValueError(
            f"unknown tier {tier!r}; valid tiers are {sorted(TIER_MODELS)}. "
            "An unknown tier in subforge silently spawns with no --model at all, and the "
            "registry keeps the bogus name; this module refuses instead."
        )
    provider, model, effort = entry
    return f"{provider}/{model}:{effort}"


def spawn_argv(
    *, session_dir: Path, name: str, model: str, extra: Sequence[str] = ()
) -> list[str]:
    """The documented argv, in the documented order (`buildSpawnArgs`, index.ts:450-458).

    `extra` is appended verbatim after `--model`, and is where the caller's sandbox flags
    go. This module never invents them: what removes a `pi` child's tool surface is those
    flags, and they are the caller's to name.
    """
    argv = [
        "pi",
        "--mode",
        "rpc",
        "--session-dir",
        str(session_dir),
        "--name",
        f"forge:{name}",
        "--model",
        model,
    ]
    argv.extend(extra)
    return argv


def _num(value: Any) -> float | None:
    """A number, or None: bools are ints in Python and are not counters here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def usage_from_record(record: dict) -> Usage:
    """The single source of truth for what an assistant `message_end` cost.

    All four billed counters plus `cost.total` (USD). Forge sums only `input` and
    `output` (`index.ts:625-628`), so cache reads and cache writes are invisible to its
    budget; here they count. Anything that is not an assistant message or not a dict of
    usage contributes a zero `Usage`, never an exception.
    """
    message = record.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return Usage()
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return Usage()
    return _usage_from_payload(usage)


def inflight_usage(record: dict) -> Usage:
    """The usage of the assistant message still streaming, or zero.

    *[pi]* `toJsonEvent` strips `message` from a `message_update` and puts the in-flight
    message's usage at the top level, repeating it on every delta. It is therefore a running
    total for one message and must never be added to completed messages; read as a total it
    closes the mid-stream blind spot, because the cap can fire before the message ends.
    """
    if record.get("type") != "message_update":
        return Usage()
    usage = record.get("usage")
    if not isinstance(usage, dict):
        return Usage()
    return _usage_from_payload(usage)


def missing_usage(record: dict) -> bool:
    """Whether an assistant `message_end` carries **no** `usage` block at all.

    Distinct from a usage block of zeros, which is what a failed request reports. A missing
    block is a reporting gap: the decision was billed and this module cannot say for how
    much. Charging it as zero would hide the spend and disable the token cap at the same
    time, so it gets its own diagnosis and the row says the cost is unknown, not zero.
    """
    if record.get("type") != "message_end":
        return False
    message = record.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return False
    return not isinstance(message.get("usage"), dict)


def _message_id(record: dict) -> str | None:
    """The assistant message's own id, when the wire carries one; None otherwise.

    Used only to recognise a `message_update` that arrives after its message's
    `message_end`, so a duplicate cannot be billed twice. The wire this was measured on
    does not always carry one, which is why the dedupe also works by value.
    """
    message = record.get("message")
    if isinstance(message, dict):
        value = message.get("id")
        if isinstance(value, str) and value:
            return value
    value = record.get("messageId")
    if isinstance(value, str) and value:
        return value
    return None


def _usage_from_payload(usage: dict) -> Usage:
    """The four billed counters and `cost.total` from one usage object.

    Negative and non-finite values are clamped to zero rather than trusted. The child is a
    process obeying a prompt, and a negative counter would subtract from a cap: a run could
    then report "under budget" while it kept spending, which is the one arithmetic result
    a cap must not be able to produce. A real provider never reports one; a bug does.
    """
    counters: dict[str, int] = {}
    for key, field in (
        ("input", "input"),
        ("output", "output"),
        ("cacheRead", "cache_read"),
        ("cacheWrite", "cache_write"),
    ):
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            counters[field] = max(0, value)
        else:
            counters[field] = 0
    usd = 0.0
    cost = usage.get("cost")
    if isinstance(cost, dict):
        total = _num(cost.get("total"))
        if total is not None and total == total and total not in (float("inf"), float("-inf")):
            usd = max(0.0, float(total))
    return Usage(usd=usd, **counters)


def _write_line(stream: Any, payload: dict) -> None:
    """One JSON object and a newline, to a text or a binary stream."""
    data = json.dumps(payload, separators=(",", ":")) + "\n"
    try:
        stream.write(data.encode("utf-8"))
    except TypeError:
        stream.write(data)
    stream.flush()


def _fileno(stream: Any) -> int | None:
    """The pipe's fd, or None for an object that is not a real pipe (the test fake)."""
    try:
        return stream.fileno()
    except (AttributeError, OSError, ValueError):
        return None


def _extract_json_objects(text: str) -> list[dict]:
    """Every complete top-level JSON object in `text`, in order.

    A reply may be bare JSON, a code fence, or a sentence with objects in it. The contract
    asks for exactly one object, and a reply that carries two is a contract violation, not
    a choice: taking the first would let a model answer twice and have the harness pick,
    silently. So this returns all of them and `_parse_reply` refuses more than one. An
    object nested inside another is not counted twice: the scan resumes after the end of
    the object it matched.
    """
    if not text:
        return []
    stripped = text.strip()
    try:
        candidate = json.loads(stripped)
    except (ValueError, TypeError):
        candidate = None
    if isinstance(candidate, dict):
        return [candidate]

    found: list[dict] = []
    start = stripped.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        end = -1
        for index in range(start, len(stripped)):
            char = stripped[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index
                    break
        if end == -1:
            start = stripped.find("{", start + 1)
            continue
        try:
            candidate = json.loads(stripped[start : end + 1])
        except (ValueError, TypeError):
            candidate = None
        if isinstance(candidate, dict):
            found.append(candidate)
            start = stripped.find("{", end + 1)
        else:
            start = stripped.find("{", start + 1)
    return found



def default_spawn(argv: list[str], *, cwd: str) -> subprocess.Popen:
    """The real spawn: the documented argv, a fresh empty cwd, an own process group.

    The two directories the argv names are created here, not in the decision path, so a
    test that injects `spawn` never touches the filesystem. The child inherits only the
    whitelisted environment variables above: it gets no path and no key material from us.

    stderr goes to a **file** beside the session directory, not to DEVNULL and not to a pipe.
    DEVNULL threw away the only diagnosis a spawn-time failure has (`pi` complains on stderr
    about a dead cwd, a missing provider or a bad model), and an undrained pipe would
    deadlock a chatty child. The path is attached to the process so `_stderr_tail` can quote
    the last few hundred bytes in the failure reason and `_reap` can close the handle.
    """
    work = Path(cwd)
    work.mkdir(parents=True, exist_ok=True)
    session_dir = Path(argv[argv.index("--session-dir") + 1])
    session_dir.mkdir(parents=True, exist_ok=True)
    log_path = session_dir.parent / "stderr.log"
    log = log_path.open("wb")
    env = {key: os.environ[key] for key in _ENV_WHITELIST if key in os.environ}
    try:
        child = subprocess.Popen(  # noqa: S603 - argv is built here, never from a prompt
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=log,
            start_new_session=True,
        )
    except BaseException:
        log.close()
        raise
    # Two attributes, not a wrapper class: `_reap` and the failure prose read them with
    # `getattr`, so a fake child in a test (which has neither) is unaffected.
    child.forge_stderr_log = log  # type: ignore[attr-defined]
    child.forge_stderr_path = log_path  # type: ignore[attr-defined]
    return child


def _signal_child(child: Any, sig: int) -> None:
    """SIGTERM/SIGKILL the child's process group when it is real, the child when it is not.

    A fake child in a test owns no pid, so it must never reach `os.killpg`: an arbitrary
    number there could name a live process. `subprocess.Popen` is the discriminator.
    """
    try:
        if child.poll() is not None:
            return
    except Exception:
        return
    if isinstance(child, subprocess.Popen):
        try:
            os.killpg(os.getpgid(child.pid), sig)
            return
        except (ProcessLookupError, PermissionError, OSError):
            pass
        try:
            child.send_signal(sig)
        except (ProcessLookupError, OSError):
            pass
        return
    method = getattr(child, "terminate" if sig == signal.SIGTERM else "kill", None)
    if method is not None:
        try:
            method()
        except Exception:
            pass


def _reap(child: Any) -> None:
    """The documented three-step kill, on every path, guarded at each step.

    abort over stdin -> SIGTERM after 250 ms -> SIGKILL after 5 s -> close stdin (pi turns
    stdin EOF into `shutdown()` with exit 0). A `pi --mode rpc` child never exits by
    itself, so skipping this leaves a live process holding a session.
    """
    if child is None:
        return
    try:
        _write_line(child.stdin, {"id": "end", "type": "abort"})
    except Exception:
        pass
    exited_quietly = False
    try:
        child.wait(timeout=REAP_TERM_GRACE_SECONDS)
        exited_quietly = True
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    if not exited_quietly:
        _signal_child(child, signal.SIGTERM)
        try:
            child.wait(timeout=REAP_KILL_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        if child.poll() is None:
            _signal_child(child, signal.SIGKILL)
            try:
                child.wait(timeout=1.0)
            except Exception:
                pass
    try:
        child.stdin.close()
    except Exception:
        pass
    log = getattr(child, "forge_stderr_log", None)
    if log is not None:
        try:
            log.close()
        except Exception:
            pass
    stdout = getattr(child, "stdout", None)
    if stdout is not None:
        try:
            stdout.close()
        except Exception:
            pass


class ForgePolicy:
    """One `pi` child per decision, with a scripted fallback behind every failure.

    Not a sandbox and not a guarantee that the model answered well: the guarantee is that a
    dead, slow, broke or incoherent child produces a deterministic scripted intent (marked
    `forge-fallback:`) instead of stalling the run or emitting a priced trade nobody
    checked. The fallback class is fixed at construction from `spec.policy`; an instance is
    built per view because the scripted policies take the event's face and cap.
    """

    name: str = "forge"

    def __init__(
        self,
        spec: Any,
        *,
        tier: str = "low",
        token_budget: int,
        max_concurrent: int = 2,
        timeout_seconds: float = 180,
        spawn: Callable[..., Any] | None = None,
        acknowledge_cost: bool = False,
        system_prompt: str | None = None,
        extra_argv: Sequence[str] = (),
        on_usage: Callable[[Usage], None] | None = None,
        kill_check: Callable[[], None] | None = None,
        scratch_root: Path | None = None,
        intended_cap_bps: int | None = None,
        max_decision_tokens: int | None = None,
        observation_path: Path | str | None = None,
    ) -> None:
        if not acknowledge_cost:
            raise CostNotAcknowledged(
                "ForgePolicy spends money: one decision is one `pi` child, and the "
                "measured p90 is ~207k output tokens per child. Pass "
                "acknowledge_cost=True only when the operator has decided to pay for it; "
                "the scripted policies in market_swarm.agents are the default path."
            )
        self.agent_id: str = str(spec.agent_id)
        self.seed: int = int(getattr(spec, "seed", 0))
        self.tier: str = tier
        self.model: str = _model_for_tier(tier)
        budget = int(token_budget)
        if budget <= 0:
            raise ValueError(f"token_budget must be positive, got {token_budget}")
        self.token_budget: int = budget
        if int(max_concurrent) < 1:
            raise ValueError(f"max_concurrent must be at least 1, got {max_concurrent}")
        self.max_concurrent: int = int(max_concurrent)
        self.timeout_seconds: float = float(timeout_seconds)
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be positive, got {timeout_seconds}")
        self.spawn: Callable[..., Any] = spawn or default_spawn
        self._system_prompt: str | None = system_prompt
        self._extra_argv: tuple[str, ...] = tuple(extra_argv)
        self._on_usage: Callable[[Usage], None] | None = on_usage
        self._kill_check: Callable[[], None] | None = kill_check
        #: The organizer's intended markup cap, as distinct from the on-chain `cap_bps` the
        #: view carries. In `monitored` mode the view's cap is the u16 field maximum, so a
        #: policy that read only the view would aim 6x higher than the scripted policies it
        #: is meant to be compared with. The view stays as it is; this fills the prompt and
        #: the fallback with the same fact the scripted path gets.
        self._intended_cap_bps: int | None = (
            None if intended_cap_bps is None else int(intended_cap_bps)
        )
        self._scratch_root: Path = (
            Path(scratch_root) if scratch_root is not None else SCRATCH_ROOT
        )

        policy_name = getattr(spec, "policy", None)
        fallback_class = agents.POLICIES.get(policy_name) if isinstance(policy_name, str) else None
        if fallback_class is None:
            raise ValueError(
                f"spec.policy {policy_name!r} has no scripted policy to fall back to; "
                f"valid policies are {sorted(agents.POLICIES)}"
            )
        self._fallback_class: type = fallback_class

        #: Whether the current reservation was settled in `_decide_with_child`'s finally.
        #: One policy instance serves one agent, and that agent decides one at a time, so
        #: this needs no lock; the flag exists so an early failure can return the reservation.
        self._reservation_settled: bool = True
        self._semaphore = threading.Semaphore(self.max_concurrent)
        self._lock = threading.Lock()
        self._usage: Usage = Usage()
        self._decisions: int = 0
        #: The adapter's own caps. `token_budget` is the cap for the whole instance and
        #: `max_decision_tokens` the cap for one child; both are checked by reservation
        #: *before* a child exists, so a refusal leaves the counters untouched.
        self.max_decision_tokens: int = (
            DEFAULT_MAX_DECISION_TOKENS
            if max_decision_tokens is None
            else int(max_decision_tokens)
        )
        self._budget = ForgeBudget(
            total_tokens=self.token_budget, max_decision_tokens=self.max_decision_tokens
        )
        self._observation_path: Path | None = (
            Path(observation_path) if observation_path is not None else None
        )
        self._observations: list[dict] = []
        #: Provenance counters, read by the runner into the dataset's sidecar. A decision the
        #: child made is not the same evidence as a decision the fallback made, and a dataset
        #: that cannot say which is which is not a record of a live run.
        self.decisions_real: int = 0
        self.decisions_fallback: int = 0
        #: Decisions the adapter declined to take because its own cap was spent. Counted
        #: apart from both of the above so the provenance block adds up to the decisions the
        #: run actually took.
        self.decisions_refused: int = 0
        self.fallback_reasons: list[str] = []

    # -- budget accounting ------------------------------------------------------------

    @property
    def usage(self) -> Usage:
        """The aggregate `Usage` across every child this agent has spawned so far."""
        with self._lock:
            return self._usage

    @property
    def tokens_spent(self) -> int:
        """Tokens observed across every child this agent has spawned so far."""
        with self._lock:
            return self._usage.total

    def _charge(self, delta: Usage) -> None:
        """Fold one decision's usage in, then hand the same delta to the callback."""
        with self._lock:
            self._usage = self._usage + delta
        if self._on_usage is not None:
            self._on_usage(delta)

    @property
    def budget(self) -> BudgetPosition:
        """What the adapter's own caps have seen: tokens, seconds, dollars, any overrun."""
        return self._budget.position()

    @property
    def observations(self) -> tuple[dict, ...]:
        """One subforge-shaped row per child spawned, oldest first."""
        with self._lock:
            return tuple(self._observations)

    # -- prompt and scratch -----------------------------------------------------------

    def _prompt(self, view: agents.MarketView) -> str:
        """A compact JSON view and the reply contract. No path, no key, no ledger dump."""
        cap_bps = int(view.cap_bps)
        ceiling = int(view.ceiling_lamports)
        intended = self._intended_cap_bps
        if intended is not None and int(view.mode == "monitored"):
            # The chain would admit more; the organizer said this. Both facts are true and
            # the child needs both to behave like the scripted scalper it replaces.
            cap_bps = intended
            ceiling = int(view.face_lamports) * (10_000 + intended) // 10_000
        holdings = [
            {"ticket": holding.ticket_id, "lot": int(holding.lot_price_lamports)}
            for holding in view.holdings[:3]
        ]
        payload = {
            "round": int(view.round),
            "rounds_left": int(view.rounds_left),
            "face_lamports": int(view.face_lamports),
            "cap_bps": cap_bps,
            "ceiling_lamports": ceiling,
            "tickets_available": int(view.tickets_available),
            "holdings": holdings,
            "last_prices": [int(price) for price in view.last_prices[-LAST_PRICES_IN_PROMPT:]],
            "refused_attempts": int(view.refused_attempts),
        }
        return _PROMPT_PREFIX + json.dumps(payload, separators=(",", ":")) + "\n"

    def _scratch(self) -> tuple[Path, Path]:
        """A fresh base dir for this decision, and the empty cwd under it.

        Absolute, always. A relative base would be handed to `pi` as `--session-dir` while
        the child's cwd is `.../work`, and `pi` resolves the flag against its own cwd, so
        the session and its file landed *inside* the work directory on both live children
        that were tried before this was fixed.
        """
        with self._lock:
            self._decisions += 1
            index = self._decisions
        base = (self._scratch_root / self.agent_id / f"decision-{index:05d}").resolve()
        return base, base / "work"

    def _write_persona(self, work: Path) -> None:
        """Write the trusted project prompt the child will read instead of the global one.

        A trusted project `.pi/SYSTEM.md` replaces the operator's global
        `<agent-dir>/SYSTEM.md`, and `.pi/APPEND_SYSTEM.md` replaces the global append;
        without both, a spawned child inherits a 14 KB foreign rulebook on every turn.
        Only called when a system prompt was configured, so a test that passes none
        touches no disk at all.
        """
        assert self._system_prompt is not None
        pi_dir = work / ".pi"
        pi_dir.mkdir(parents=True, exist_ok=True)
        (pi_dir / "SYSTEM.md").write_text(self._system_prompt, encoding="utf-8")
        (pi_dir / "APPEND_SYSTEM.md").write_text("", encoding="utf-8")

    # -- one decision -----------------------------------------------------------------

    def decide(self, view: agents.MarketView) -> list[agents.Intent | agents.Refusal]:
        failure: str | None = None
        intents: list[agents.Intent] | None = None

        if self._kill_check is not None:
            try:
                self._kill_check()
            except Exception as exc:  # a kill order, not a spawn problem
                self._note_fallback(f"run killed: {exc}")
                return self._fallback(view, f"run killed: {exc}")

        try:
            reserved = self._budget.reserve()
            self._reservation_settled = False
        except ForgeBudgetExceeded as exc:
            # Refused before a child exists. The row is the record: a scripted trade here
            # would be a decision the operator did not pay for, and raising would kill the
            # dataset instead of carrying the refusal inside it.
            return [self._refusal(exc)]

        if not self._semaphore.acquire(timeout=self.timeout_seconds):
            self._budget.cancel(reserved)
            self._reservation_settled = True
            failure = "no concurrency slot within the wall clock"
        else:
            try:
                intents, failure = self._decide_with_child(view, reserved)
            finally:
                self._semaphore.release()

        if failure is not None:
            # A failure before the child path was entered (a persona write, say) never reaches
            # `_decide_with_child`'s settle, so its reservation is returned here rather than
            # left reserved for the rest of the run.
            if not self._reservation_settled:
                self._budget.cancel(reserved)
            self._note_fallback(failure)
            return self._fallback(view, failure)
        with self._lock:
            self.decisions_real += 1
        return intents or []

    def _refusal(self, exc: ForgeBudgetExceeded) -> agents.Refusal:
        """The refusal a spent budget returns, in place of a scripted trade.

        `action="refuse"` is the dataset's word for a decision that was not taken. It used
to be `"buy"`, which made every summary of a refused run count the refusal as a buy.
        """
        with self._lock:
            self.decisions_refused += 1
        return agents.Refusal(
            agent_id=self.agent_id,
            action="refuse",
            price_lamports=None,
            rationale=(
                f"forge-refused: {exc}. The live policy declined to decide, so no order "
                "was placed and nothing moved; this is a skipped decision, not a trade."
            ),
        )

    def _note_fallback(self, reason: str) -> None:
        """Record why a decision fell back, bounded so a broken provider cannot grow it."""
        with self._lock:
            self.decisions_fallback += 1
            if len(self.fallback_reasons) < 20:
                self.fallback_reasons.append(reason[:200])

    def _decide_with_child(
        self, view: agents.MarketView, reserved: int
    ) -> tuple[list[agents.Intent] | None, str | None]:
        base, work = self._scratch()
        if self._system_prompt is not None:
            try:
                self._write_persona(work)
            except OSError as exc:
                # A filesystem failure must not escape `decide`: the caller's round loop
                # would lose the whole dataset, and this is one decision's problem. The
                # reservation is settled in the caller's failure path by `cancel` below.
                return None, f"could not write the persona: {type(exc).__name__}: {exc}"
        argv = spawn_argv(
            session_dir=base / "session",
            name=self.agent_id,
            model=self.model,
            extra=self._extra_argv,
        )
        index = int(base.name.split("-")[-1])
        started_at = _utc_now()
        started = time.monotonic()
        spent = Usage()
        inflight = Usage()
        #: Usage of the message that ended most recently, and the ids of messages already
        #: billed. Both exist for one reason: an update that arrives after its message's
        #: `message_end` repeats a total that has already been charged, and the `finally`
        #: below adds the in-flight total, so without this the same message is billed twice.
        last_ended: Usage | None = None
        ended_messages: set[str] = set()
        #: True when any assistant message ended with no `usage` block at all and no in-flight
        #: total to stand in for it: part of the charge was never reported, so the row's
        #: counters are withheld rather than written as a zero that reads as free.
        cost_unknown = False
        #: The same question for the message that ended last, which is the answer this
        #: decision is taken from. An error record with no usage followed by a priced answer
        #: does not make the answer unpriced.
        unpriced_answer = False
        #: How many JSON objects the accepted reply contained. Recorded, so a reader can see
        #: the child honoured the one-object contract instead of trusting the adapter to say.
        reply_objects: int | None = None
        text_parts: list[str] = []
        done = False
        reason: str | None = None
        provider_error: str | None = None
        session_id: str | None = None
        status = "failed"
        child: Any = None

        try:
            try:
                child = self.spawn(argv, cwd=str(work))
            except Exception as exc:  # spawn error, missing executable, bad cwd
                reason = f"spawn error: {type(exc).__name__}: {exc}"
                return None, reason

            try:
                _write_line(
                    child.stdin,
                    {"id": "p-1", "type": "prompt", "message": self._prompt(view)},
                )
                # Forge asks for the state right after the prompt and keeps `sessionId`
                # (`index.ts:743`). It costs no model tokens, and it is the key that ties
                # this child to the provider's own per-request accounting.
                _write_line(child.stdin, {"id": "st-1", "type": "get_state"})
            except Exception as exc:
                reason = f"prompt write failed: {type(exc).__name__}: {exc}"
                return None, reason

            deadline = time.monotonic() + self.timeout_seconds
            try:
                for raw in self._iter_records(child, deadline):
                    record = _decode_record(raw)
                    if record is None:
                        continue
                    kind = record.get("type")
                    if kind == "message_end":
                        # One assistant message ends exactly once. `turn_end` and
                        # `agent_end` carry the same message object again, so a counter
                        # that sums every record with a `message` bills it twice.
                        ended_usage = usage_from_record(record)
                        unpriced_answer = False
                        if missing_usage(record):
                            if inflight.total:
                                # No usage on the end, but the stream reported one for this
                                # message: the update is the only accounting it has.
                                ended_usage = inflight
                            else:
                                cost_unknown = True
                                unpriced_answer = True
                        spent = spent + ended_usage
                        last_ended = ended_usage
                        inflight = Usage()
                        message_id = _message_id(record)
                        if message_id is not None:
                            ended_messages.add(message_id)
                        # Cleared by a clean end: a provider error that retried to a good
                        # answer is not the reason to throw that paid answer away.
                        provider_error = _stop_error(record)
                    elif kind == "message_update":
                        # A running total for the message still streaming, repeated on every
                        # delta: never added to the completed sum by itself. An update that
                        # lands after its message has ended is that message's total again.
                        message_id = _message_id(record)
                        if message_id is not None and message_id in ended_messages:
                            continue
                        candidate = inflight_usage(record)
                        repeated = last_ended is not None and candidate == last_ended
                        if message_id is None and repeated:
                            # No id on the wire: a total identical to the one that just ended
                            # is that message's trailing repeat. If a later message really did
                            # open with identical counters, its own `message_end` still bills
                            # it; only the mid-stream reading of that one message is lost.
                            continue
                        inflight = candidate
                    elif kind == "response" and record.get("id") == "st-1":
                        session_id = _session_id(record)
                    if spent.total + inflight.total > reserved:
                        # Enforced mid-stream: the tokens are being spent as this line
                        # arrives, so waiting for agent_end would already be too late.
                        raise _Budget(
                            f"per-decision token cap {reserved} reached mid-stream; "
                            f"{spent.total + inflight.total} tokens observed"
                        )
                    collected = _assistant_text(record)
                    if collected:
                        text_parts.append(collected)
                    if kind == "agent_end" and not record.get("willRetry"):
                        done = True
                        break
            except _Timeout:
                status = "timeout"
                reason = f"timed out after {self.timeout_seconds:g}s"
            except _Budget as exc:
                reason = str(exc) or "token budget exceeded mid-stream"
            except OSError as exc:
                reason = f"stdout read failed: {type(exc).__name__}: {exc}"

            if reason is None and not done:
                returncode = child.poll()
                reason = (
                    f"child exited {returncode}"
                    if returncode not in (None, 0)
                    else "stream ended without a non-retrying agent_end"
                )
            if reason is None and provider_error is not None:
                # Forge would write `finished` here. The child itself said the request
                # failed, and its own sentence is the only diagnosis the registry lacks.
                reason = f"child reported a failed request: {provider_error}"
            if reason is None and unpriced_answer:
                # A reporting gap, not a free decision. The tokens were bought and the
                # stream did not say how many, so the row says the cost is unknown.
                reason = (
                    "an assistant message carried no usage block: this decision's cost is "
                    "unknown, not zero"
                )
            if reason is None and spent.total == 0:
                # Forge would call this `finished`. A zero-token run is a provider
                # failure, and a priced trade from it would be a fabricated number.
                reason = "zero tokens reported"
            if reason is None:
                try:
                    intent, reply_objects = self._parse_reply("".join(text_parts), view)
                except _BadReply as exc:
                    reason = str(exc)
                else:
                    status = "finished"
                    return [intent], None
            return None, reason
        finally:
            if inflight.total:
                # Killed or timed out with a message in flight: those tokens were billed
                # too, so they are charged before the row is written.
                spent = spent + inflight
                inflight = Usage()
            elapsed = max(0.0, time.monotonic() - started)
            tail = _stderr_tail(child) if reason is not None else ""
            if tail and reason is not None and tail not in reason:
                reason = f"{reason} [stderr: {tail}]"
            poll = getattr(child, "poll", None)
            # Charge, then settle, then reap, then read the exit code. The order is
            # load-bearing twice: `_charge` hands the delta to the caller's sink, which is
            # allowed to raise a run-kill and would skip a reap written in the same `try`,
            # and `poll()` before the reap reports `None` for a child that is reaped a
            # moment later.
            try:
                self._charge(spent)
            finally:
                self._budget.settle(reserved, spent, elapsed)
                self._reservation_settled = True
                _reap(child)
                self._observe(
                    index=index,
                    status=status,
                    reason=reason,
                    usage=spent,
                    seconds=elapsed,
                    session_id=session_id,
                    base=base,
                    work=work,
                    started_at=started_at,
                    exit_code=poll() if callable(poll) else None,
                    cost_unknown=cost_unknown,
                    reply_objects=reply_objects,
                )

    def _observe(
        self,
        *,
        index: int,
        status: str,
        reason: str | None,
        usage: Usage,
        seconds: float,
        session_id: str | None,
        base: Path,
        work: Path,
        started_at: str,
        exit_code: int | None,
        cost_unknown: bool = False,
        reply_objects: int | None = None,
    ) -> None:
        """One registry-shaped row: what this child cost, and how it ended.

        The field names are subforge's `Run` interface, so a row here reads like a row in
        `~/.pi/agent/subforge/runs.jsonl`. This module never writes that file - it belongs
        to the extension and is another program's state - it appends to `observation_path`
        when one was given and keeps the rows in memory either way. A child that burned
        tokens and then failed still gets its row: the cost is real.

        `cost_unknown` marks a child with at least one assistant message whose stream carried
        no usage at all. Its counters are written as `null`, not `0`: a zero would claim the
        decision was free, and the whole point of the row is to say what it cost. The
        counters are withheld even when a later message reported its own, because a total
        that is missing a message is not the total. `replyObjects` is how many JSON objects
        the accepted reply carried, or null when no reply was accepted.
        """
        row = {
            "runId": f"forge-{self.agent_id}-{index:05d}",
            "name": f"forge:{self.agent_id}",
            "tier": self.tier,
            "model": self.model,
            "status": status,
            "startedAt": started_at,
            "endedAt": _utc_now(),
            "sessionId": session_id,
            "sessionDir": str(base / "session"),
            "cwd": str(work),
            "tokensIn": None if cost_unknown else usage.input,
            "tokensOut": None if cost_unknown else usage.output,
            "cacheRead": None if cost_unknown else usage.cache_read,
            "cacheWrite": None if cost_unknown else usage.cache_write,
            "costUsd": None if cost_unknown else usage.usd,
            "costUnknown": cost_unknown,
            "replyObjects": reply_objects,
            "maxRunSeconds": self.timeout_seconds,
            "seconds": round(seconds, 3),
            "exitCode": exit_code,
            "reason": reason,
        }
        with self._lock:
            self._observations.append(row)
        if self._observation_path is not None:
            self._observation_path.parent.mkdir(parents=True, exist_ok=True)
            with self._observation_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, separators=(",", ":")) + "\n")

    def _iter_records(self, child: Any, deadline: float) -> Iterable[Any]:
        """Line-delimited records from the pipe, bounded by the wall clock.

        On a real pipe the read is `select`-driven with the remaining time as its timeout,
        which closes the blind spot the research documented in the naive `for line in
        stdout` sketch: a silent child cannot hang the swarm. On anything else (the test
        fake) the iterable is non-blocking by construction, and the per-record deadline
        check still makes a slow producer time out rather than run forever.
        """
        stream = child.stdout
        fd = _fileno(stream)
        if fd is None:
            for raw in stream:
                if time.monotonic() > deadline:
                    raise _Timeout
                yield raw
            return

        selector = selectors.DefaultSelector()
        selector.register(fd, selectors.EVENT_READ)
        buffer = b""
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise _Timeout
                if not selector.select(remaining):
                    raise _Timeout
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if time.monotonic() > deadline:
                        raise _Timeout
                    yield line
            if buffer.strip():
                yield buffer
        finally:
            selector.close()

    def _parse_reply(
        self, text: str, view: agents.MarketView
    ) -> tuple[agents.Intent, int]:
        """Validate the reply against the intent contract before it can become a trade.

        Returns the intent and how many JSON objects the reply carried. More than one is
        refused rather than silently resolved to the first: a reply with two intents in it
        is a child that did not follow the contract, and picking one would hide that.
        """
        objects = _extract_json_objects(text)
        if not objects:
            raise _BadReply("reply contained no JSON object")
        if len(objects) > 1:
            raise _BadReply(
                f"reply contained {len(objects)} JSON objects; the contract is exactly one"
            )
        payload = objects[0]
        action = payload.get("action")
        if action not in agents.ACTIONS:
            raise _BadReply(f"action {action!r} is not one of {agents.ACTIONS}")
        price = payload.get("price_lamports")
        if isinstance(price, bool) or not isinstance(price, int):
            raise _BadReply(
                f"price_lamports {price!r} is not an integer; floats are refused because "
                "a lamport is not divisible"
            )
        if price <= 0:
            raise _BadReply(f"price_lamports {price} is not positive")
        if view.mode == "capped":
            # The event's own ceiling, not just the sanity bound. The prompt tells the child
            # this number, and in capped mode a price above it is a transaction the hook
            # would refuse: refusing it here costs nothing, and a live child that
            # hallucinated a price would otherwise buy a real refused attempt.
            ceiling = agents.cap_ceiling(int(view.face_lamports), int(view.cap_bps))
            if price > ceiling:
                raise _BadReply(
                    f"price_lamports {price} is above the event ceiling {ceiling} "
                    f"(face {view.face_lamports} at {view.cap_bps} bps); capped mode would "
                    "refuse it on chain"
                )
        bound = int(view.face_lamports) * agents.HARD_PRICE_MULTIPLE
        if price > bound:
            raise _BadReply(
                f"price_lamports {price} is above the sanity bound {bound} "
                f"(face x {agents.HARD_PRICE_MULTIPLE})"
            )
        ticket_id: str | None = None
        if action in ("list", "resell"):
            if not view.holdings:
                raise _BadReply(f"action {action!r} with no holding to act on")
            ticket_id = view.holdings[0].ticket_id
        rationale = payload.get("rationale")
        rationale = str(rationale).strip()[:200] if rationale else "no rationale given"
        return agents.Intent(
            agent_id=self.agent_id,
            action=action,
            price_lamports=price,
            ticket_id=ticket_id,
            rationale=f"forge: {rationale}",
        ), len(objects)

    # -- fallback ---------------------------------------------------------------------

    def _fallback(self, view: agents.MarketView, reason: str) -> list[agents.Intent]:
        """The scripted policy's decision for this view, labelled with the failure."""
        policy = self._fallback_class(
            _FallbackSpec(self.agent_id, self.seed),
            face_lamports=view.face_lamports,
            # The scripted policy is built with the intended cap in `monitored` mode, the
            # same value `runner._policies_for` gives it. A fallback priced off the field
            # maximum would be a different instrument from the scripted agent it stands in
            # for, and the dataset would not be comparable.
            cap_bps=(
                self._intended_cap_bps
                if self._intended_cap_bps is not None and view.mode == "monitored"
                else view.cap_bps
            ),
        )
        intents = policy.decide(view)
        note = f"forge-fallback: {reason}"
        return [
            replace(intent, rationale=f"{note}; {intent.rationale}") for intent in intents
        ]


class _FallbackSpec:
    """The two fields a scripted policy reads off an `AgentSpec`."""

    __slots__ = ("agent_id", "policy", "seed")

    def __init__(self, agent_id: str, seed: int) -> None:
        self.agent_id = agent_id
        self.policy = ""
        self.seed = seed


def _decode_record(raw: Any) -> dict | None:
    """One stdout line to a dict, or None for a malformed line (skipped, as forge does)."""
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    if not isinstance(raw, str):
        return None
    line = raw.strip()
    if not line:
        return None
    try:
        record = json.loads(line)
    except (ValueError, TypeError):
        return None
    return record if isinstance(record, dict) else None


def _utc_now() -> str:
    """A UTC ISO-8601 stamp with milliseconds, the format the subforge rows carry."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _session_id(record: dict) -> str | None:
    """The `sessionId` from a `get_state` response, or None for anything else."""
    data = record.get("data")
    if isinstance(data, dict):
        value = data.get("sessionId")
        if isinstance(value, str) and value:
            return value
    return None


def _stop_error(record: dict) -> str | None:
    """The child's own sentence for an assistant message that stopped on an error.

    Finding 30 measured that a provider failure still emits `agent_end`, so forge records
    `finished` with `0/0` and no diagnosis anywhere. The diagnosis is on the wire:
    `stopReason: "error"` plus `errorMessage` on the assistant `message_end`. This reads it,
    bounded, so a provider failure is reported as one instead of as a zero-token success.
    """
    message = record.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return None
    if message.get("stopReason") != "error":
        return None
    text = message.get("errorMessage")
    return str(text).strip()[:200] if text else "stopReason=error"


def _stderr_tail(child: Any, limit: int = 400) -> str:
    """The last few hundred bytes the child wrote to stderr, flattened onto one line.

    Returns "" for a fake child (no log path attached) and for an unreadable log, so the
    failure prose never depends on this having worked.
    """
    path = getattr(child, "forge_stderr_path", None)
    if path is None:
        return ""
    try:
        data = Path(path).read_bytes()[-limit:]
    except OSError:
        return ""
    return " ".join(data.decode("utf-8", "replace").split())[-limit:]


def _usage_tokens(record: dict) -> int:
    """All four billed counters from an assistant message, not forge's two.

    Kept as the counting helper callers and existing tests already import; the parsing
    itself lives in `usage_from_record`, so a counter is never read two different ways.
    """
    return usage_from_record(record).total


def _assistant_text(record: dict) -> str:
    """Text blocks of an assistant `message_end`, exactly as forge extracts them."""
    if record.get("type") != "message_end":
        return ""
    message = record.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return ""
    blocks = message.get("content")
    if not isinstance(blocks, list):
        return ""
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
            parts.append(str(block["text"]))
    return "".join(parts)
