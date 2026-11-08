"""What a run is: the frozen specs, the cap arithmetic, and the one loader.

The cap arithmetic here is the off-chain half of the on-chain predicate in
`programs/cap_hook/src/lib.rs`:

    price * 10_000 <= face * (10_000 + cap_bps)

`ceiling_lamports` returns the largest price that predicate admits, so the two can be
checked against each other (and the tests do check them against each other). Both are
integer arithmetic with no float anywhere: lamports are integers, basis points are
integers, and a float would put a rounding error into a money value.

The on-chain code casts both sides to `u128` before multiplying because a `u64` product
wraps silently: `u64::MAX * 20_000` is far past 2**64, and the wrapped result would read
as a small number and could admit a price above the cap. Python integers do not wrap, so
the same bug cannot occur here, but the lesson still applies: keep the arithmetic exact
and never route it through a float.

`cluster` is one of `{"local", "devnet"}` and nothing else. There is deliberately no
branch, default or override in this module that can name mainnet: a config that says
anything else fails before a socket opens.

`program` is one of `{"v1", "v2"}` and says which of the two `cap_hook` programs the run
drives. They are not two versions of one thing: v1 is the four-tag program deployed on
devnet, v2 is a different program id with seven tags (the floor, the jurisdiction and policy
bytes, the hold clock) that has only ever run on a local validator. A row is an observation
of one program, so the run states which, and the pairs that cannot exist are refused here
rather than discovered as a dataset full of errors.
"""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:  # an annotation only: the module that defines it is imported where it is used
    from .artist_fee import ArtistFeePolicy
    from .flip_tax import FlipTaxPolicy

# The u16 field maximum. `cap_bps` is a `u16` in the record account, so 65535 is the
# largest markup the field can express; that is how "uncapped / monitored" is realised
# through the real program rather than through a special case in the hook.
U16_MAX = 65535
BPS_DENOMINATOR = 10_000

MODES = frozenset({"capped", "monitored"})
CLUSTERS = frozenset({"local", "devnet"})

#: The two programs. `v1` is the four-tag program deployed on devnet: `InitializeExtraAccountMetaList`,
#: `InitializeRecord`, `SetPendingPrice`, `SetStatus`, and the bytes a devnet reader is reading.
#: `v2` is a different program id with seven tags, adding the floor, the jurisdiction and policy
#: bytes and the hold clock; it has only ever run on a local `solana-test-validator` built from this
#: tree. The wire format of each is in `market_swarm/wire.py`, and the address each one deploys at
#: is pinned in `market_swarm/gateway.py`, because "which program" is answered by an address and
#: not by a name.
PROGRAMS = frozenset({"v1", "v2"})

#: The pairings that can exist. `v1` is deployed on devnet and can also be deployed locally from its
#: own keypair, so it pairs with either cluster. `v2` has no devnet deployment at all: a v2 run
#: there would deploy nothing, read the v1 program's answers and label them v2's, which is a run
#: whose proof cannot exist. So `v2` pairs with `local` and nothing else.
PROGRAM_CLUSTERS = {"v1": frozenset({"local", "devnet"}), "v2": frozenset({"local"})}

#: `v1`, and the reason is what exists rather than what is newest. v1 is the program deployed on
#: devnet, and every config in this tree was written before the field existed -- both example configs
#: and every fixture the tests build omit it -- so v1 is what those runs have been driving and a
#: default of v1 keeps every one of them valid. A default of `v2` would fail on the only cluster
#: that serves a program at all; any other default would be a run whose program nobody chose.
PROGRAM_DEFAULT = "v1"

# Defaults for the optional fields of a run config, stated once and used by the loader.
# Everything not listed here is required: a run should not silently invent its cluster,
# its events or its budgets.
RUN_ID_DEFAULT = None  # None means "generate one with run_id()"
KILL_AFTER_SECONDS_DEFAULT = None
OUT_DIR_DEFAULT = "market_swarm/runs"
DRY_RUN_DEFAULT = False
SEED_DEFAULT = 0


class ConfigError(ValueError):
    """A run config that cannot be used, naming the field that is wrong."""


#: The cheapest tier is the default for every agent. The three tiers on the active profile
#: name the same model and differ only in effort, so the tier is a spend knob, not a model
#: choice; `low` is the one a data-collection run can afford.
LLM_TIER_DEFAULT = "low"
LLM_PER_AGENT_TOKENS_DEFAULT = 60_000
#: The most any one decision may burn. Measured decisions in this session ran 136 to 2,300
#: tokens, so 8,000 is several times the observed shape and still stops a child that loops.
#: Without it the adapter reserves the whole per-agent budget for one child, which would let
#: a single bad reply spend everything the agent had.
LLM_PER_DECISION_TOKENS_DEFAULT = 8_000
LLM_TOTAL_TOKENS_DEFAULT = 250_000
LLM_MAX_CONCURRENT_DEFAULT = 2
LLM_TIMEOUT_SECONDS_DEFAULT = 90.0

#: Fields of the optional `llm` block. Everything but `enabled` has a stated default,
#: because a run that turns the LLM on should not have to restate the safe shape.
_LLM_FIELDS = frozenset(
    {
        "enabled", "tier", "per_agent_token_budget", "per_decision_token_budget",
        "total_token_budget", "max_concurrent", "timeout_seconds", "cost_cap_usd",
        "usd_per_mtok",
    }
)
_PRICE_FIELDS = frozenset({"input", "output", "cache_read", "cache_write"})


@dataclass(frozen=True)
class PriceTable:
    """USD per million tokens, used only when the child reports no cost of its own."""

    input: float
    output: float
    cache_read: float
    cache_write: float

    def cost_usd(self, usage) -> float:
        """The dollar cost of one `forge_policy.Usage`, at these rates."""
        return (
            usage.input * self.input
            + usage.output * self.output
            + usage.cache_read * self.cache_read
            + usage.cache_write * self.cache_write
        ) / 1_000_000


@dataclass(frozen=True)
class LlmConfig:
    """The money switch for a run, plus the caps that bound it.

    Two currencies, both hard: tokens (what the provider bills) and dollars (what the
    provider says it billed, read per decision from the child's own stream). The dollar cap
    is optional only because a provider that reports no cost cannot be capped in dollars;
    when a cost cap is set, a price table must be supplied, and the loader refuses the config
    otherwise. Nothing here is ever defaulted to a price: an invented rate would make the cap
    a fiction.
    """

    enabled: bool
    tier: str
    per_agent_token_budget: int
    per_decision_token_budget: int
    total_token_budget: int
    max_concurrent: int
    timeout_seconds: float
    cost_cap_usd: float | None
    usd_per_mtok: PriceTable | None



@dataclass(frozen=True)
class AgentSpec:
    """One agent's identity and its hard spend limits."""

    agent_id: str
    policy: str            # registry name, see agents.POLICIES
    wallet_label: str
    seed: int
    budget_lamports: int
    budget_actions: int

    #: How many units this agent may hold at once. One is the default because a ticket is a
    #: seat: most participants hold one. It is a field rather than a run-wide constant because
    #: a market maker has to be able to absorb several, and a market maker is what makes a
    #: resale cap bind at all -- with every participant holding at most one, the largest ask
    #: anyone can attempt is the cheapest ask, and the cap is never reached.
    max_holdings: int = 1


@dataclass(frozen=True)
class EventSpec:
    """One ticket event: its face value, its cap mode, and its simulated size."""

    event_id: str
    face_lamports: int
    mode: str              # "capped" | "monitored"
    cap_bps: int | None    # required for capped; ignored (field max) for monitored
    tickets: int
    rounds: int
    round_seconds: int     # simulated time-to-event step, never a real sleep by default

    #: The artist fee the seller pays on every resale of this event, or `None` for no fee.
    #: It trails the required fields and it defaults, so every existing config, test and
    #: constructor call keeps its meaning: a run that does not name a fee is charged nothing and
    #: is otherwise identical to the run before this field existed. The policy is parsed by the
    #: module that owns the arithmetic (`market_swarm/artist_fee.py`) rather than restated here,
    #: so the two bounds -- the rate and the wallet -- have exactly one definition.
    artist_fee: ArtistFeePolicy | None = None

    #: The flip tax the seller pays on a quick resale, or `None` for no tax. Like the fee it is
    #: last and it defaults, so every existing config, test and constructor call keeps its
    #: meaning: an event that does not name a block is charged no tax and is otherwise identical
    #: to the event before this field existed. The block is opt-in on top of that -- a block
    #: without `"enabled": true` carries a policy that is off -- and the policy is parsed by the
    #: module that owns the arithmetic (`market_swarm/flip_tax.py`) rather than restated here.
    flip_tax: FlipTaxPolicy | None = None


@dataclass(frozen=True)
class RunConfig:
    """A whole run: which events, which agents, what the run may spend in total."""

    run_id: str
    cluster: str            # "local" | "devnet"
    events: tuple[EventSpec, ...]
    agents: tuple[AgentSpec, ...]
    total_budget_lamports: int
    total_budget_actions: int
    kill_after_seconds: float | None
    out_dir: Path
    dry_run: bool
    seed: int
    #: "v1" | "v2", the program this run drives. Defaulted and last among the plain fields for the
    #: reason `PROGRAM_DEFAULT` gives, so a config written before the switch still loads as the run
    #: it always was.
    program: str = PROGRAM_DEFAULT
    llm: LlmConfig | None = None


def effective_cap_bps(mode: str, cap_bps: int | None) -> int:
    """The `cap_bps` value that goes into the record account for this mode.

    In "capped" mode the caller must say the cap, as an integer in the u16 field range.
    In "monitored" mode there is no cap to say: the field is filled with its maximum,
    65535, so the record still carries a number. That is not "no cap": the hook still
    refuses any price above `face * (1 + 6.5535)` (65535 bps), and nothing above it can
    be expressed through this field at all.
    """
    if mode not in MODES:
        raise ValueError(f"mode: expected one of {sorted(MODES)}, got {mode!r}")
    if mode == "monitored":
        return U16_MAX
    if isinstance(cap_bps, bool) or not isinstance(cap_bps, int):
        raise ValueError(
            f"cap_bps: required as an integer between 0 and {U16_MAX} when mode is "
            f"capped, got {cap_bps!r}"
        )
    if not 0 <= cap_bps <= U16_MAX:
        raise ValueError(f"cap_bps: must be between 0 and {U16_MAX}, got {cap_bps}")
    return cap_bps


def ceiling_lamports(face: int, cap_bps: int) -> int:
    """The largest price the on-chain predicate admits, as an exact integer.

    `face * (10_000 + cap_bps) // 10_000`, floored to the lamport. The predicate itself
    is `price * 10_000 <= face * (10_000 + cap_bps)` with both sides in u128 on chain,
    so this floor is exactly the largest integer price that satisfies it. No float is
    used anywhere: lamports are integers and this must stay exact at u64-sized faces.
    """
    if isinstance(face, bool) or not isinstance(face, int):
        raise ValueError(f"face: expected an integer number of lamports, got {face!r}")
    if face < 0:
        raise ValueError(f"face: must not be negative, got {face}")
    if isinstance(cap_bps, bool) or not isinstance(cap_bps, int):
        raise ValueError(f"cap_bps: expected an integer, got {cap_bps!r}")
    if not 0 <= cap_bps <= U16_MAX:
        raise ValueError(f"cap_bps: must be between 0 and {U16_MAX}, got {cap_bps}")
    return face * (BPS_DENOMINATOR + cap_bps) // BPS_DENOMINATOR


_LAST_RUN_ID: str | None = None


def run_id(*, now: float | None = None) -> str:
    """A run id: `sw` + a compact UTC timestamp + 4 random hex characters.

    Example: `sw20261107T185000Z1a2b`. The random tail makes ids distinct across
    machines and processes; the loop below makes two calls in the same second distinct
    within one process, so a test can assert that without a sleep and without a flake.
    """
    global _LAST_RUN_ID
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
    candidate = f"sw{stamp}{secrets.token_hex(2)}"
    while candidate == _LAST_RUN_ID:
        candidate = f"sw{stamp}{secrets.token_hex(2)}"
    _LAST_RUN_ID = candidate
    return candidate


def _require_int(value: Any, field: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    """An integer field, refusing bools (which are ints) and floats."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field}: expected an integer, got {type(value).__name__}")
    if value < minimum:
        raise ConfigError(f"{field}: must be at least {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{field}: must be at most {maximum}, got {value}")
    return value


#: What an identifier that becomes part of a file name may contain. A `run_id` or an
#: `event_id` is concatenated into the dataset path, so a stray `../` would write outside the
#: run directory. The config is the operator's file, not an attack surface, but a typo must
#: not be able to do that either, so the shape is checked rather than trusted.
_IDENTIFIER_MAX = 64


def _require_identifier(value: Any, field: str) -> str:
    """A string safe to put in a file name: letters, digits, dot, dash, underscore."""
    text = _require_text(value, field)
    if len(text) > _IDENTIFIER_MAX:
        raise ConfigError(f"{field}: must be at most {_IDENTIFIER_MAX} characters")
    bad = sorted({character for character in text if not (character.isalnum() or character in "._-")})
    if bad:
        raise ConfigError(
            f"{field}: {text!r} contains {bad}; an identifier that becomes part of a path "
            "may use only letters, digits, dot, dash and underscore"
        )
    if text.startswith(".") or text.endswith("."):
        raise ConfigError(f"{field}: {text!r} must not start or end with a dot")
    return text


def _require_text(value: Any, field: str) -> str:
    """A non-empty string field."""
    if not isinstance(value, str):
        raise ConfigError(f"{field}: expected a string, got {type(value).__name__}")
    if not value.strip():
        raise ConfigError(f"{field}: must not be empty")
    return value


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigError(f"{field}: expected an object, got {type(value).__name__}")
    return value


def _no_unknown_keys(raw: Mapping[str, Any], allowed: frozenset[str], field: str) -> None:
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ConfigError(f"{field}: unknown field(s) {', '.join(unknown)}")


_AGENT_FIELDS = frozenset(
    {"agent_id", "policy", "wallet_label", "seed", "budget_lamports", "budget_actions",
     "max_holdings"}
)
#: Fields an agent may omit. Only the holdings limit, because 1 is the right default for a
#: participant and the market maker is the exception that states it explicitly.
_AGENT_OPTIONAL_FIELDS = frozenset({"max_holdings"})
#: Fields an event may omit. `cap_bps` because monitored mode has no cap to state, `artist_fee`
#: because a fee is opt-in, and `flip_tax` for the same reason plus one: a tax block that is
#: present but not enabled is a policy that is off, and an absent block is the same policy.
_EVENT_OPTIONAL_FIELDS = frozenset({"cap_bps", "artist_fee", "flip_tax"})
_EVENT_FIELDS = frozenset(
    {"event_id", "face_lamports", "mode", "cap_bps", "tickets", "rounds", "round_seconds",
     "artist_fee", "flip_tax"}
)
_RUN_FIELDS = frozenset(
    {
        "run_id", "cluster", "program", "events", "agents", "total_budget_lamports",
        "total_budget_actions", "kill_after_seconds", "out_dir", "dry_run", "seed",
        "llm",
    }
)


def _require_number(value: Any, field: str, *, minimum: float = 0.0) -> float:
    """A positive finite float. Bools are refused because they are ints in disguise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{field}: expected a number, got {type(value).__name__}")
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        raise ConfigError(f"{field}: must be finite")
    if number < minimum:
        raise ConfigError(f"{field}: must be at least {minimum}, got {number}")
    return number


def _parse_llm(raw: Any) -> LlmConfig | None:
    """The optional LLM block. Absent or disabled means the scripted policies, by default."""
    if raw is None:
        return None
    block = _require_mapping(raw, "llm")
    _no_unknown_keys(block, _LLM_FIELDS, "llm")
    enabled = block.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ConfigError(f"llm.enabled: expected a boolean, got {type(enabled).__name__}")

    tier = _require_text(block.get("tier", LLM_TIER_DEFAULT), "llm.tier")
    if tier not in _llm_tier_names():
        # Refused at load so `plan` catches it. The adapter also refuses an unknown tier,
        # but it does so after the validator has booted and the dataset file is open, which
        # is the worst possible moment to learn a one-letter typo.
        raise ConfigError(
            f"llm.tier: expected one of {sorted(_llm_tier_names())}, got {tier!r}"
        )
    per_agent = _require_int(
        block.get("per_agent_token_budget", LLM_PER_AGENT_TOKENS_DEFAULT),
        "llm.per_agent_token_budget", minimum=1,
    )
    per_decision = _require_int(
        block.get("per_decision_token_budget", LLM_PER_DECISION_TOKENS_DEFAULT),
        "llm.per_decision_token_budget", minimum=1,
    )
    if per_decision > per_agent:
        raise ConfigError(
            "llm.per_decision_token_budget: must not exceed llm.per_agent_token_budget, "
            f"else one decision could spend an agent's whole allowance ({per_decision} > {per_agent})"
        )
    total = _require_int(
        block.get("total_token_budget", LLM_TOTAL_TOKENS_DEFAULT),
        "llm.total_token_budget", minimum=1,
    )
    if total < per_agent:
        raise ConfigError(
            "llm.total_token_budget: must be at least llm.per_agent_token_budget, else the "
            f"first agent alone can trip the run ({total} < {per_agent})"
        )
    concurrent = _require_int(
        block.get("max_concurrent", LLM_MAX_CONCURRENT_DEFAULT), "llm.max_concurrent", minimum=1
    )
    # The measured safe concurrency on one credential is two or three; four simultaneous
    # children produced provider timeouts on every one. A config may choose fewer, not more.
    if concurrent > 3:
        raise ConfigError(
            "llm.max_concurrent: at most 3; four simultaneous children on one credential "
            "produced provider timeouts on all four (records/findings/30)"
        )
    timeout = _require_number(
        block.get("timeout_seconds", LLM_TIMEOUT_SECONDS_DEFAULT), "llm.timeout_seconds",
        minimum=0.001,
    )

    cost_cap_raw = block.get("cost_cap_usd")
    cost_cap: float | None = None
    if cost_cap_raw is not None:
        cost_cap = _require_number(cost_cap_raw, "llm.cost_cap_usd")
        if cost_cap <= 0:
            # Zero is not a cap: the first charge would already be past it, and the value
            # would be read as "no cap" by a person skimming the config. Say null instead.
            raise ConfigError(
                "llm.cost_cap_usd: must be greater than zero; use null for no dollar cap"
            )

    prices_raw = block.get("usd_per_mtok")
    prices: PriceTable | None = None
    if prices_raw is not None:
        table = _require_mapping(prices_raw, "llm.usd_per_mtok")
        _no_unknown_keys(table, _PRICE_FIELDS, "llm.usd_per_mtok")
        prices = PriceTable(
            input=_require_number(table["input"], "llm.usd_per_mtok.input"),
            output=_require_number(table["output"], "llm.usd_per_mtok.output"),
            cache_read=_require_number(table["cache_read"], "llm.usd_per_mtok.cache_read"),
            cache_write=_require_number(table["cache_write"], "llm.usd_per_mtok.cache_write"),
        )
    if enabled and cost_cap is not None and prices is None:
        # A cap with no way to measure against it is the one arrangement this module will
        # not accept: it would report "under cap" forever while the money left.
        raise ConfigError(
            "llm.cost_cap_usd: requires llm.usd_per_mtok as well, so the cap can be measured "
            "even when a child reports no cost of its own. The harness refuses a cap it "
            "cannot measure."
        )

    return LlmConfig(
        enabled=enabled,
        tier=tier,
        per_agent_token_budget=per_agent,
        per_decision_token_budget=per_decision,
        total_token_budget=total,
        max_concurrent=concurrent,
        timeout_seconds=timeout,
        cost_cap_usd=cost_cap,
        usd_per_mtok=prices,
    )


def _parse_agent(raw: Any, index: int) -> AgentSpec:
    field = f"agents[{index}]"
    spec = _require_mapping(raw, field)
    _no_unknown_keys(spec, _AGENT_FIELDS, field)
    for required in sorted(_AGENT_FIELDS - _AGENT_OPTIONAL_FIELDS):
        if required not in spec:
            raise ConfigError(f"{field}.{required}: required field is missing")
    return AgentSpec(
        agent_id=_require_text(spec["agent_id"], f"{field}.agent_id"),
        policy=_require_text(spec["policy"], f"{field}.policy"),
        wallet_label=_require_text(spec["wallet_label"], f"{field}.wallet_label"),
        seed=_require_int(spec["seed"], f"{field}.seed", minimum=-(2**63)),
        budget_lamports=_require_int(spec["budget_lamports"], f"{field}.budget_lamports"),
        budget_actions=_require_int(spec["budget_actions"], f"{field}.budget_actions"),
        max_holdings=_require_int(
            spec.get("max_holdings", 1), f"{field}.max_holdings", minimum=1
        ),
    )


def _parse_event(raw: Any, index: int) -> EventSpec:
    field = f"events[{index}]"
    spec = _require_mapping(raw, field)
    _no_unknown_keys(spec, _EVENT_FIELDS, field)
    for required in sorted(_EVENT_FIELDS - _EVENT_OPTIONAL_FIELDS):
        if required not in spec:
            raise ConfigError(f"{field}.{required}: required field is missing")

    mode = _require_text(spec["mode"], f"{field}.mode")
    if mode not in MODES:
        raise ConfigError(f"{field}.mode: expected one of {sorted(MODES)}, got {mode!r}")

    cap_bps = spec.get("cap_bps")
    if mode == "capped":
        if cap_bps is None:
            raise ConfigError(f"{field}.cap_bps: required when mode is capped")
        _require_int(cap_bps, f"{field}.cap_bps", maximum=U16_MAX)
    elif cap_bps is not None:
        # Ignored for the cap itself, but if it is present it must still be a u16:
        # a value the record account cannot hold is a config bug, not a no-op.
        _require_int(cap_bps, f"{field}.cap_bps", maximum=U16_MAX)

    # The fee block is parsed by the module that owns the arithmetic, and its refusal is
    # re-raised as this module's error: a caller catches one type from a config load, and it
    # is `ConfigError`, not something it would have to import a second module to name. The
    # message is passed through unchanged, so the field path it carries -- for instance
    # "events[2].artist_fee.fee_bps" -- still says which event and which key.
    artist_fee = None
    fee_raw = spec.get("artist_fee")
    if fee_raw is not None:
        from .artist_fee import ArtistFeeError, ArtistFeePolicy

        try:
            artist_fee = ArtistFeePolicy.from_mapping(fee_raw, field=f"{field}.artist_fee")
        except ArtistFeeError as exc:
            raise ConfigError(str(exc)) from exc

    # The flip tax block, parsed the same way and re-raised the same way. Its one extra input is
    # the artist fee's wallet: an omitted `artist_wallet` inherits it, because the tax is paid to
    # the artist, and a block that names a different wallet is refused by the policy module rather
    # than quietly redirecting the money. The field path it reports is the event's, so a bad rate
    # in a several-event config says which event.
    flip_tax = None
    tax_raw = spec.get("flip_tax")
    if tax_raw is not None:
        from .flip_tax import FlipTaxError, FlipTaxPolicy

        default_wallet = None if artist_fee is None else artist_fee.artist_wallet
        try:
            flip_tax = FlipTaxPolicy.from_mapping(
                tax_raw, field=f"{field}.flip_tax", default_wallet=default_wallet
            )
        except FlipTaxError as exc:
            raise ConfigError(str(exc)) from exc

    # The combined take, on an event that turns the tax on: the seller pays the fee and the tax
    # out of one price, so their sum is what a quick resale costs. Above 10 000 bps the seller
    # pays to sell, which is not a price the checkout may build, so it is refused at load rather
    # than at the first sale. A tax with no fee cannot reach this: its own rate is bounded by
    # `flip_tax.MAX_BPS`, which is 10 000, and the bound is checked when the schedule is built.
    if flip_tax is not None and flip_tax.enabled and artist_fee is not None:
        from .flip_tax import combined_take_bps

        combined = combined_take_bps(
            artist_fee_bps=artist_fee.fee_bps, schedule=flip_tax.schedule
        )
        if combined > BPS_DENOMINATOR:
            raise ConfigError(
                f"{field}.artist_fee.fee_bps: {artist_fee.fee_bps} bps plus "
                f"{field}.flip_tax.schedule.full_bps: {flip_tax.schedule.full_bps} bps is "
                f"{combined} bps of the sale price, and the seller pays both. A take above "
                f"{BPS_DENOMINATOR} bps means the seller pays to sell, so this event is refused."
            )

    return EventSpec(
        event_id=_require_identifier(spec["event_id"], f"{field}.event_id"),
        face_lamports=_require_int(spec["face_lamports"], f"{field}.face_lamports", minimum=1),
        mode=mode,
        cap_bps=cap_bps,
        tickets=_require_int(spec["tickets"], f"{field}.tickets"),
        rounds=_require_int(spec["rounds"], f"{field}.rounds", minimum=1),
        round_seconds=_require_int(spec["round_seconds"], f"{field}.round_seconds"),
        artist_fee=artist_fee,
        flip_tax=flip_tax,
    )


def load_run_config(path: Path, *, overrides: Mapping | None = None) -> RunConfig:
    """Read a JSON run config, validate every field, apply `overrides`, return it frozen.

    `overrides` is a flat mapping of top-level field names, applied after the file is
    read and before anything is validated, so an override goes through exactly the same
    checks as a value that came from the file. An unknown key in either place is an
    error rather than a silently ignored typo.

    Defaults, all stated above as module constants: `run_id` is generated, `out_dir` is
    `market_swarm/runs`, `dry_run` is False, `seed` is 0, `kill_after_seconds` is None, and
    `program` is `v1` -- the program every run in this tree has driven, and the only one
    deployed anywhere. Everything else is required. Every failure is one `ConfigError` whose
    message names the field.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"config: cannot read {path.name}: {exc.strerror}") from exc
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config: not valid JSON: {exc.msg} at line {exc.lineno}") from exc

    config = _require_mapping(raw, "config")
    config = dict(config)
    _no_unknown_keys(config, _RUN_FIELDS, "config")

    if overrides is not None:
        if not isinstance(overrides, Mapping):
            raise ConfigError("overrides: expected a mapping of top-level fields")
        _no_unknown_keys(overrides, _RUN_FIELDS, "overrides")
        config.update(overrides)

    for required in ("cluster", "events", "agents", "total_budget_lamports",
                     "total_budget_actions"):
        if required not in config:
            raise ConfigError(f"{required}: required field is missing")

    cluster = _require_text(config["cluster"], "cluster")
    if cluster not in CLUSTERS:
        raise ConfigError(f"cluster: expected one of {sorted(CLUSTERS)}, got {cluster!r}")

    program = _require_text(config.get("program", PROGRAM_DEFAULT), "program")
    if program not in PROGRAMS:
        raise ConfigError(f"program: expected one of {sorted(PROGRAMS)}, got {program!r}")
    if cluster not in PROGRAM_CLUSTERS[program]:
        # Named, and named with the reason: this is the pair that would otherwise produce a
        # dataset nobody can use. v2 is a different program id and has never been deployed to
        # devnet, so a v2 run there would send v1's instructions to v1's program and record the
        # answers as v2's -- noise that looks like a result.
        raise ConfigError(
            f"program: {program!r} cannot be paired with cluster {cluster!r}. v2 has no devnet "
            "deployment and never has had one, so a v2 run there would read v1's answers and "
            "call them v2's: a run whose proof cannot exist. v2 pairs with \"local\". v1 pairs "
            "with either cluster, because v1 is the program deployed on devnet."
        )

    events_raw = config["events"]
    if not isinstance(events_raw, (list, tuple)):
        raise ConfigError("events: expected a list of event objects")
    events = tuple(_parse_event(item, index) for index, item in enumerate(events_raw))
    if not events:
        raise ConfigError("events: at least one event is required")
    event_ids = [event.event_id for event in events]
    if len(set(event_ids)) != len(event_ids):
        raise ConfigError("events: event_id values must be unique")

    agents_raw = config["agents"]
    if not isinstance(agents_raw, (list, tuple)):
        raise ConfigError("agents: expected a list of agent objects")
    agents = tuple(_parse_agent(item, index) for index, item in enumerate(agents_raw))
    if not agents:
        raise ConfigError("agents: at least one agent is required")
    agent_ids = [agent.agent_id for agent in agents]
    if len(set(agent_ids)) != len(agent_ids):
        raise ConfigError("agents: agent_id values must be unique")

    run_identifier = config.get("run_id")
    if run_identifier is None:
        run_identifier = run_id()
    else:
        run_identifier = _require_identifier(run_identifier, "run_id")

    kill_after = config.get("kill_after_seconds", KILL_AFTER_SECONDS_DEFAULT)
    if kill_after is not None:
        if isinstance(kill_after, bool) or not isinstance(kill_after, (int, float)):
            raise ConfigError("kill_after_seconds: expected a positive number or null")
        if kill_after <= 0:
            raise ConfigError(f"kill_after_seconds: must be positive, got {kill_after}")

    out_dir_raw = config.get("out_dir", OUT_DIR_DEFAULT)
    out_dir = Path(_require_text(out_dir_raw, "out_dir"))

    dry_run = config.get("dry_run", DRY_RUN_DEFAULT)
    if not isinstance(dry_run, bool):
        raise ConfigError(f"dry_run: expected a boolean, got {type(dry_run).__name__}")

    seed = _require_int(config.get("seed", SEED_DEFAULT), "seed", minimum=-(2**63))
    llm = _parse_llm(config.get("llm"))
    if llm is not None and llm.enabled:
        unknown_policies = sorted(
            {agent.policy for agent in agents} - set(_scripted_policy_names())
        )
        if unknown_policies:
            raise ConfigError(
                "llm.enabled: every agent's policy needs a persona and a scripted fallback; "
                f"these have neither: {', '.join(unknown_policies)}"
            )

    return RunConfig(
        run_id=run_identifier,
        cluster=cluster,
        events=events,
        agents=agents,
        total_budget_lamports=_require_int(
            config["total_budget_lamports"], "total_budget_lamports"
        ),
        total_budget_actions=_require_int(
            config["total_budget_actions"], "total_budget_actions"
        ),
        kill_after_seconds=kill_after,
        out_dir=out_dir,
        dry_run=dry_run,
        seed=seed,
        program=program,
        llm=llm,
    )


def _llm_tier_names() -> tuple[str, ...]:
    """The tiers the adapter knows, imported late so config stays a pure data module."""
    from .forge_policy import TIER_MODELS

    return tuple(TIER_MODELS)


def _scripted_policy_names() -> tuple[str, ...]:
    """The policy registry's names, imported late so config stays a pure data module."""
    from .agents import POLICIES

    return tuple(POLICIES)
