"""The six scripted trading policies, and the read-only view they decide from.

Every policy is a pure decision function: `decide(view) -> list[Intent]`. No socket, no
clock, no key material, no module-level mutable state, and no randomness beyond
`view.rng()`, which is seeded from `(agent_id, round, run seed)` so the same inputs give
the same stream in a fresh process. That purity is what makes the swarm's dataset
replayable, and it is the only reason a policy is allowed anywhere near the runner.

Prices are integer lamports throughout. The cap predicate on chain is
`price * 10_000 <= face * (10_000 + cap_bps)`, compared in `u128` with no division, so the
largest admissible price is the floor of `face * (10_000 + cap_bps) // 10_000`. Every price
this module emits is computed from integers with `//` and never through a float: a float
would quietly round a boundary case, and the boundary is the whole experiment.

What this module is NOT: evidence about real ticket markets, real resale behaviour, or real
agent rationality. The policies are scripts written to exercise a priced-cap mechanism on a
synthetic event. A run through them measures the mechanism and the ledger, not the market.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping, Protocol

if TYPE_CHECKING:  # typing only; `config` is not imported at run time, so no import cycle
    from market_swarm.config import AgentSpec


#: The closed set of intent actions. `buy` is a primary purchase, `list` is a listing with
#: no chain transaction behind it, `resell` is a custody transfer the cap hook inspects.
ACTIONS: tuple[str, ...] = ("buy", "list", "resell")

#: A bug-catcher, not a market rule: no policy may ever ask for a price this far above
#: face. If one does, its arithmetic is wrong and the run must stop, not trade.
HARD_PRICE_MULTIPLE = 1000


def cap_ceiling(face_lamports: int, cap_bps: int) -> int:
    """The largest admissible price for `face_lamports` at `cap_bps`, exactly.

    Mirrors the on-chain predicate `price * 10_000 <= face * (10_000 + cap_bps)`: the
    ceiling is the integer floor of the right-hand side over 10 000. No float, no rounding
    step that could disagree with the program by one lamport.
    """
    return face_lamports * (10_000 + cap_bps) // 10_000


def _derived_seed(*parts: object) -> int:
    """A 64-bit seed from the given parts, stable across processes and hash seeds."""
    material = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


@dataclass(frozen=True)
class Intent:
    """One thing an agent wants to do this round. The runner, not the agent, applies it."""

    agent_id: str
    action: str
    price_lamports: int | None
    ticket_id: str | None
    rationale: str


@dataclass(frozen=True)
class Refusal:
    """A policy declining to decide, with the reason the dataset records as `skipped`.

    Not an `Intent`: the runner must not apply it, and a refusal wearing an intent's clothes
    would be one more priced order in the book. A policy returns these alongside intents
    when it refused *before* acting - the live `forge` adapter does when its own token cap
    is spent - and the runner writes one `skipped` row and applies nothing. It is not an
    exception, because an exception would kill the dataset instead of recording the
    refusal in it.

    `action` is the row's action, and it is `"refuse"`, not the action the policy would
    otherwise have taken: a decision nobody made is not a buy, and a dataset that said it
    was one would be counted that way by every reader that groups by action.
    """

    agent_id: str
    action: str
    price_lamports: int | None
    rationale: str


@dataclass(frozen=True)
class Holding:
    """A ticket an agent already owns, at the price its lot cost."""

    ticket_id: str
    lot_price_lamports: int
    acquired_round: int


@dataclass(frozen=True)
class MarketView:
    """Everything a policy is allowed to know, and nothing else.

    `cap_bps` and `ceiling_lamports` are the *effective on-chain* values: in monitored mode
    `cap_bps` is the field maximum 65535, so the effective ceiling is far above the event's
    intended markup cap. The intended cap is not in the view on purpose, a policy that
    could see it would censor itself, and the scalper is the policy whose whole job is not
    to. It travels on the policy instead (see `build_policy`).

    `agent_id` and `seed` carry no market information; they exist so `rng()` can derive a
    stream that is reproducible per agent, per round, per run.
    """

    round: int
    rounds_left: int
    event_id: str
    mode: str
    face_lamports: int
    cap_bps: int
    ceiling_lamports: int
    tickets_available: int
    holdings: tuple[Holding, ...]
    last_prices: tuple[int, ...]
    refused_attempts: int
    agent_id: str = ""
    seed: int = 0

    def rng(self) -> random.Random:
        """A fresh generator seeded from (agent_id, round, run seed).

        Deterministic across constructions, across processes and across hash seeds: the
        seed is a sha256 of the parts, never `hash()` of a string.
        """
        return random.Random(_derived_seed(self.agent_id, self.round, self.seed))


class Policy(Protocol):
    """What the runner needs from a policy. Nothing here may touch the world."""

    name: str

    def decide(self, view: MarketView) -> list[Intent | Refusal]: ...


def _check_price(price: object, *, face_lamports: int, agent_id: str, what: str) -> int:
    """Assert a price is a positive int in lamports and inside the sanity bound."""
    if not isinstance(price, int) or isinstance(price, bool):
        raise AssertionError(
            f"{agent_id}: {what} produced {price!r} ({type(price).__name__}), "
            "not an integer lamport amount"
        )
    if price <= 0:
        raise AssertionError(f"{agent_id}: {what} produced non-positive price {price}")
    bound = face_lamports * HARD_PRICE_MULTIPLE
    if price > bound:
        raise AssertionError(
            f"{agent_id}: {what} produced price {price} lamports, above the sanity bound "
            f"{bound} lamports (face {face_lamports} x {HARD_PRICE_MULTIPLE}); the policy "
            "arithmetic is wrong, refusing to trade"
        )
    return price


class _ScriptedPolicy:
    """Shared plumbing: the agent's identity, its face, and the checked `Intent` factory."""

    name: str = "scripted"

    def __init__(
        self,
        spec: "AgentSpec",
        *,
        face_lamports: int,
        cap_bps: int,
        intended_cap_bps: int | None = None,
    ) -> None:
        self.agent_id: str = spec.agent_id
        self.seed: int = int(spec.seed)
        self.face_lamports: int = int(face_lamports)
        self.cap_bps: int = int(cap_bps)
        # The event's intended markup cap, kept off the view so no policy can read the
        # effective cap and mistake it for the intended one. In capped mode they are the
        # same number; in monitored mode `cap_bps` is 65535 and this is the real policy.
        self.intended_cap_bps: int = int(
            cap_bps if intended_cap_bps is None else intended_cap_bps
        )

    def _intent(
        self,
        view: MarketView,
        action: str,
        price_lamports: int | None,
        ticket_id: str | None,
        rationale: str,
    ) -> Intent:
        if action not in ACTIONS:
            raise AssertionError(
                f"{self.agent_id}: unknown action {action!r}; valid actions are {ACTIONS}"
            )
        if price_lamports is not None:
            _check_price(
                price_lamports,
                face_lamports=view.face_lamports,
                agent_id=self.agent_id,
                what=f"a {action} intent",
            )
        return Intent(
            agent_id=self.agent_id,
            action=action,
            price_lamports=price_lamports,
            ticket_id=ticket_id,
            rationale=rationale,
        )

    def _primary_ask(self, view: MarketView) -> int:
        """The primary price this round: the last observed price, else face."""
        return view.last_prices[-1] if view.last_prices else view.face_lamports


class BuyerPolicy(_ScriptedPolicy):
    """Buys one primary ticket, and only when the ask is at or below face.

    Models an attendee with a reservation value at face: it will not pay a markup and it
    wants at most one seat, so once it holds a ticket it never acts again. It is NOT
    evidence that real buyers are capped at face or that they buy once, it is a baseline
    that puts a ticket in the market without expressing a view on price.
    """

    name = "buyer"

    def decide(self, view: MarketView) -> list[Intent]:
        if view.holdings:
            return []
        if view.tickets_available <= 0:
            return []
        ask = self._primary_ask(view)
        if ask > view.face_lamports:
            return []
        return [
            self._intent(
                view,
                "buy",
                ask,
                None,
                f"primary ask {ask} is at or below face {view.face_lamports}; take one",
            )
        ]


_HOLDER_TARGET_BPS: tuple[tuple[int, int], ...] = ((1, 200), (3, 700))
_HOLDER_BASE_TARGET_BPS = 1200


def _holder_target_bps(rounds_left: int) -> int:
    """The markup the holder is asking for, falling as the event approaches."""
    for horizon, bps in _HOLDER_TARGET_BPS:
        if rounds_left <= horizon:
            return bps
    return _HOLDER_BASE_TARGET_BPS


class HolderPolicy(_ScriptedPolicy):
    """Buys once at face, lists near a target markup, and cuts the ask as time runs out.

    It is a seller with a target, not a price taker: at +1200 bps over face it waits, at
    +700 bps inside three rounds it capitulates partially, and at +200 bps in the last two
    rounds it is trying to clear. The ask is clamped to the effective ceiling because a
    listing above it cannot be filled. It is NOT evidence that holders hold out for 12% or
    that their asks decay linearly, the decay here is a script with three steps, chosen to
    make relisting observable in a handful of rounds.
    """

    name = "holder"

    def decide(self, view: MarketView) -> list[Intent]:
        if not view.holdings:
            if view.tickets_available <= 0:
                return []
            return [
                self._intent(
                    view,
                    "buy",
                    view.face_lamports,
                    None,
                    f"acquire one at primary face {view.face_lamports}",
                )
            ]
        holding = view.holdings[0]
        target_bps = _holder_target_bps(view.rounds_left)
        price = min(
            cap_ceiling(view.face_lamports, target_bps), view.ceiling_lamports
        )
        if price <= 0:
            price = 1
        clamped = cap_ceiling(view.face_lamports, target_bps) > view.ceiling_lamports
        return [
            self._intent(
                view,
                "list",
                price,
                holding.ticket_id,
                f"list at +{target_bps} bps over face"
                + (" (clamped to the effective ceiling)" if clamped else "")
                + f", {view.rounds_left} rounds left",
            )
        ]


_FLIPPER_HEADROOM_NUM = 3  # buy under three quarters of the headroom to the ceiling
_FLIPPER_HEADROOM_DEN = 4
_FLIPPER_MARKUP_BPS = 300


class FlipperPolicy(_ScriptedPolicy):
    """Buys under a ceiling-derived threshold, resells just above cost, turns stock fast.

    Its buy threshold is three quarters of the way from face to the effective ceiling, so
    it never pays a price that leaves it no room under the cap. Its ask is +300 bps on its
    own lot price, clamped to the ceiling, and it declines to list at or below cost rather
    than take a loss, a flipper that cannot clear a spread simply stops buying. It is NOT
    evidence that a 3% spread is what real flippers earn; the number is a script parameter
    picked so the cap binds before the spread does.
    """

    name = "flipper"

    def decide(self, view: MarketView) -> list[Intent]:
        ceiling = view.ceiling_lamports
        headroom = max(0, ceiling - view.face_lamports)
        threshold = (
            view.face_lamports
            + headroom * _FLIPPER_HEADROOM_NUM // _FLIPPER_HEADROOM_DEN
        )
        if not view.holdings:
            if view.tickets_available <= 0:
                return []
            ask = self._primary_ask(view)
            if ask > threshold:
                return []
            return [
                self._intent(
                    view,
                    "buy",
                    ask,
                    None,
                    f"ask {ask} is under the ceiling-derived threshold {threshold}; "
                    "buy to flip",
                )
            ]
        holding = view.holdings[0]
        price = min(
            holding.lot_price_lamports * (10_000 + _FLIPPER_MARKUP_BPS) // 10_000, ceiling
        )
        if price <= holding.lot_price_lamports:
            return []  # no room under the cap: hold, do not realise a loss
        return [
            self._intent(
                view,
                "resell",
                price,
                holding.ticket_id,
                f"resell at +{_FLIPPER_MARKUP_BPS} bps over lot "
                f"{holding.lot_price_lamports}, inside the ceiling {ceiling}",
            )
        ]


_SCALPER_EXTRA_BPS_BASE = 200
_SCALPER_EXTRA_BPS_STEP = 100


class ScalperPolicy(_ScriptedPolicy):
    """Attacks the resale cap: prices above it first, then settles at and under it.

    It acquires one ticket at face, then asks above the ceiling for its first N attempts
    (N is 2..4, derived from its seed). Each attempt asks more than the last, so the first
    few rounds are an escalation against the boundary rather than a single probe. Once
    `refused_attempts` shows those were refused it retries at exactly the ceiling, then one
    lamport under it, then lower by one lamport per further refusal, so it still trades
    after the cap has beaten it.

    **Failure to beat the cap is the intended outcome in capped mode. Success is the
    intended outcome in monitored mode.** The two modes exist to measure exactly that
    difference, and this policy is the instrument: it must not censor itself in either.

    In monitored mode the effective on-chain cap is the field maximum (65535 bps), so the
    prices it aims at are far below it and every attempt lands. The price it aims at there
    is the *event's intended* markup cap, which it reads from the policy (`intended_cap_bps`
    passed to `build_policy`), never from `view.cap_bps`, that is the whole difference
    between the modes and the one line that could quietly ruin the experiment.

    It is NOT evidence that real scalpers escalate, that N=2..4 is realistic, or that a
    cap is the right mechanism. It is a probe for one boolean: does the hook refuse.
    """

    name = "scalper"
    over_cap_min = 2
    over_cap_max = 4

    def __init__(
        self,
        spec: "AgentSpec",
        *,
        face_lamports: int,
        cap_bps: int,
        intended_cap_bps: int | None = None,
    ) -> None:
        super().__init__(
            spec,
            face_lamports=face_lamports,
            cap_bps=cap_bps,
            intended_cap_bps=intended_cap_bps,
        )
        # Deterministic from the seed, computed once at construction: no rng in __init__,
        # because construction is not a decision and must not consume a stream.
        self.over_cap_attempts: int = self.over_cap_min + abs(self.seed) % (
            self.over_cap_max - self.over_cap_min + 1
        )

    def _attack_ceiling(self, view: MarketView) -> int:
        """The boundary this policy is attacking: intended in monitored, effective in capped."""
        if view.mode == "monitored":
            return cap_ceiling(view.face_lamports, self.intended_cap_bps)
        return view.ceiling_lamports

    def _over_cap_price(self, view: MarketView, attempt: int) -> int:
        extra_bps = _SCALPER_EXTRA_BPS_BASE + _SCALPER_EXTRA_BPS_STEP * attempt
        price = (
            view.face_lamports
            * (10_000 + self.intended_cap_bps + extra_bps)
            // 10_000
        )
        target = self._attack_ceiling(view)
        if price <= target:
            price = target + 1  # strictly above, always, by at least one lamport
        return price

    def decide(self, view: MarketView) -> list[Intent]:
        if not view.holdings:
            if view.tickets_available <= 0:
                return []
            return [
                self._intent(
                    view,
                    "buy",
                    view.face_lamports,
                    None,
                    f"acquire one at primary face {view.face_lamports} to attack the cap",
                )
            ]
        holding = view.holdings[0]
        target = self._attack_ceiling(view)
        attempts = self.over_cap_attempts
        refused = view.refused_attempts
        if refused < attempts:
            attempt = min(refused, attempts - 1)
            price = self._over_cap_price(view, attempt)
            rationale = (
                f"over-cap attempt {refused + 1}/{attempts}: ask {price} against the "
                f"boundary {target}"
                + (" (intended cap, monitored mode)" if view.mode == "monitored" else "")
            )
        elif refused == attempts:
            price = target
            rationale = (
                f"{attempts} over-cap attempts refused; retry at exactly the boundary "
                f"{target} so the transfer is admissible"
            )
        else:
            under = target - (refused - attempts)
            price = under if under > 0 else 1
            rationale = (
                f"{refused} refusals; retry {target - price} lamports under the boundary "
                f"{target}"
            )
        return [self._intent(view, "resell", price, holding.ticket_id, rationale)]


_SNIPER_ROUNDS = 3


class SniperPolicy(_ScriptedPolicy):
    """Says nothing until the last few rounds, then bids the ceiling in one go.

    Silence is the behaviour being modelled: no intent is emitted while
    `rounds_left > 3`, and then a single aggressive bid at exactly the effective ceiling, never above it, because a bid above it is refused and the sniper knows it. It holds
    what it wins and stops bidding. It is NOT evidence about last-minute demand or bid
    shading; it exists so the dataset contains a buyer whose timing, not whose price
    level, defines it, and so the ledger has late-round bids at the boundary.
    """

    name = "sniper"
    quiet_until_rounds_left = _SNIPER_ROUNDS

    def decide(self, view: MarketView) -> list[Intent]:
        if view.rounds_left > self.quiet_until_rounds_left:
            return []
        if view.holdings:
            return []
        if view.tickets_available <= 0:
            return []
        ceiling = view.ceiling_lamports
        if ceiling <= 0:
            return []
        return [
            self._intent(
                view,
                "buy",
                ceiling,
                None,
                f"{view.rounds_left} rounds left: bid the ceiling {ceiling} exactly, "
                "one lamport above it would be refused",
            )
        ]


_PANIC_HORIZON_ROUNDS = 2
_PANIC_LOSS_BPS: tuple[tuple[int, int], ...] = ((0, 4000), (1, 3000))


def _panic_loss_bps(rounds_left: int) -> int:
    for horizon, bps in _PANIC_LOSS_BPS:
        if rounds_left <= horizon:
            return bps
    return 1500


class PanicPolicy(_ScriptedPolicy):
    """Sells into the deadline and accepts a loss, possibly below face.

    Inside two rounds it resells at a discount on its lot price that deepens as the clock
    runs out: -1500 bps, then -3000, then -4000. It does not respect face, because the
    predicate has no lower bound, the hook only refuses a price *above* the cap, so a sale
    below face is admissible and the ledger must be able to record it. It is NOT evidence
    that real holders panic-sell at these discounts; the discounts are a script parameter
    whose purpose is to produce a negative-markup row the dataset can be checked against.
    """

    name = "panic"

    def decide(self, view: MarketView) -> list[Intent]:
        if not view.holdings:
            # A panic seller is a holder with weak hands, so it has to hold something first.
            # Without this branch the policy is inert: it only ever sells, never acquires, and
            # an agent that never holds never emits an intent at all. It buys at primary face
            # while there is still time, which is what makes the late discount a real loss
            # rather than a sale of something it was given.
            if view.rounds_left <= _PANIC_HORIZON_ROUNDS or view.tickets_available <= 0:
                return []
            return [
                self._intent(
                    view,
                    "buy",
                    view.face_lamports,
                    None,
                    f"accumulate one at primary face {view.face_lamports} while there is time, "
                    f"so a late deadline sale is a realised loss on a real lot",
                )
            ]
        if view.rounds_left > _PANIC_HORIZON_ROUNDS:
            return []
        holding = view.holdings[0]
        loss_bps = _panic_loss_bps(view.rounds_left)
        price = holding.lot_price_lamports * (10_000 - loss_bps) // 10_000
        if price <= 0:
            price = 1
        return [
            self._intent(
                view,
                "resell",
                price,
                holding.ticket_id,
                f"deadline sale at -{loss_bps} bps on lot {holding.lot_price_lamports} "
                f"with {view.rounds_left} rounds left; a price below face is admissible "
                "because the cap only bounds above",
            )
        ]


#: How many units the market maker will absorb. Mirrors the `max_holdings` the run config
#: gives that agent; the runner takes the smaller of the two.
_GREATER_FOOL_INVENTORY = 8

#: How far over face the deep-pocketed buyer will go, in basis points. +5000 is +50%: more
#: than a scalper's first ask on a 2500-bps event, which is the point. If this were at or
#: below the cap, no ask would ever exceed the cap, no transfer would ever be attempted
#: above it, and a `capped` event would produce a dataset identical to a `monitored` one.
_GREATER_FOOL_BID_BPS = 5000


class GreaterFoolPolicy(_ScriptedPolicy):
    """A buyer with deep pockets and no price discipline, bidding above the cap.

    This policy exists for one mechanical reason and it is worth being blunt about it. The
    cap only binds when somebody is willing to pay over it. In a market where every bidder
    respects the ceiling, the largest possible ask is the ceiling itself, no transfer is
    ever attempted above it, and the hook is never exercised -- a capped event and a
    monitored event would produce identical data, which would make the two-mode comparison
    meaningless.

    So one participant bids a fixed +5000 bps over face and keeps bidding while it holds
    nothing. That is the demand a scalper sells into, and it is exactly the participant the
    cap is supposed to stop from being exploited. It is a script parameter, NOT a claim
    about real buyers: real demand at a fixed markup does not exist, and no number from a
    dataset containing this agent is evidence about willingness to pay.
    """

    name = "greater_fool"
    _inventory_limit = _GREATER_FOOL_INVENTORY

    def bid_price(self, view: MarketView) -> int:
        return view.face_lamports * (10_000 + _GREATER_FOOL_BID_BPS) // 10_000

    def decide(self, view: MarketView) -> list[Intent]:
        # It keeps bidding while it has inventory room, which is why the config gives it a
        # `max_holdings` above one. A one-ticket buyer absorbs the single cheapest ask of the
        # round and leaves the market; a market maker absorbs the round, including the
        # over-cap ask the scalper is trying to place, and that is the transfer the cap is
        # there to refuse.
        if len(view.holdings) >= self._inventory_limit:
            return []
        price = self.bid_price(view)
        return [
            self._intent(
                view,
                "buy",
                price,
                None,
                f"bids {price} lamports, +{_GREATER_FOOL_BID_BPS} bps over face, while holding "
                "nothing; the demand that makes a resale cap bind",
            )
        ]


#: Registry name -> policy class. A read-only mapping: the policies are fixed at import,
#: and a test asserts no module-level symbol here is a mutable object.
POLICIES: Mapping[str, type[Policy]] = MappingProxyType(
    {
        "buyer": BuyerPolicy,
        "holder": HolderPolicy,
        "flipper": FlipperPolicy,
        "scalper": ScalperPolicy,
        "sniper": SniperPolicy,
        "panic": PanicPolicy,
        "greater_fool": GreaterFoolPolicy,
    }
)


def build_policy(
    spec: "AgentSpec",
    *,
    face_lamports: int,
    cap_bps: int,
    intended_cap_bps: int | None = None,
) -> Policy:
    """Resolve `spec.policy` to its class and construct it with the agent's seed.

    `cap_bps` is the effective on-chain cap (65535 in monitored mode). `intended_cap_bps` is
    the event's own markup cap, passed separately so a policy can tell the two apart; when
    it is omitted it defaults to `cap_bps`, which is correct for capped mode.
    """
    if face_lamports <= 0:
        raise ValueError(f"face_lamports must be positive, got {face_lamports}")
    if cap_bps < 0:
        raise ValueError(f"cap_bps must be non-negative, got {cap_bps}")
    if intended_cap_bps is not None and intended_cap_bps < 0:
        raise ValueError(
            f"intended_cap_bps must be non-negative, got {intended_cap_bps}"
        )
    policy_name = getattr(spec, "policy", None)
    policy_class = POLICIES.get(policy_name) if isinstance(policy_name, str) else None
    if policy_class is None:
        valid = ", ".join(sorted(POLICIES))
        raise ValueError(
            f"unknown policy {policy_name!r}; valid policies are: {valid}"
        )
    return policy_class(
        spec,
        face_lamports=face_lamports,
        cap_bps=cap_bps,
        intended_cap_bps=intended_cap_bps,
    )
