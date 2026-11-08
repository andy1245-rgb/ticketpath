#!/usr/bin/env python3
"""Build `fixtures/synthetic_store.json`: one generated, labelled synthetic store.

Nothing here is real ticket data. The store exists so the backend has an internally
consistent record to compute over before any program is deployed, and so the demo
frontend has enough shape to show three pricing regimes. Every event carries a
sentence on screen saying what it is.

Run it from anywhere:

    python3 tools/build_fixture_store.py            # write the store, print invariants
    python3 tools/build_fixture_store.py --check    # verify without writing
    python3 tools/build_fixture_store.py --dump     # write to stdout, touch nothing

Determinism: the whole store is a pure function of SEED, the specs below and this
file's own bytes. No clock, no network, no third-party import. Run it twice and the
file is identical; `--check` exists so that claim is testable in CI rather than
remembered.

The three regimes the store has to carry (records/FIXTURE-STORE.md has the full
account):

  * `cap_present_not_binding`  - resale history, a cap on the event, no sale at it
  * `cap_binding`              - resale history, most sales sitting exactly on the cap
  * `cold_start`               - tickets issued, no resale row at all

Plus an uncapped spread, a resale-disabled event, a completed run with redemptions,
a tier-conditional cap, and a draft event with nothing issued.

Invariants enforced here and asserted again in `tests/test_fixture_store.py`:

  1. every wallet and mint begins with `SYN` and base58-decodes to exactly 32 bytes
  2. no two addresses share a truncated form (`first4 + last4`), so a custody trail
     can never read as one wallet handing a ticket to itself
  3. every sale price is an exact integer function of that ticket's own tier face
     and an integer basis-point markup, so `markupBps` recomputes exactly
  4. every non-sale ledger row carries a null price
  5. per ticket: rows strictly increasing in time, one `issue` first, every sale
     after it, and no `redeem` before the last sale
  6. custody links: each row's `fromWallet` is the previous row's `toWallet`; no
     sale from a wallet to itself
  7. tier `issuedCount` equals that tier's ticket rows; event totals equal the sum
     of their tiers
  8. the regime facts above, one assertion per event
  9. every event name, event description and organizer name carries a marker that
     says this is synthetic demonstration data
 10. every event description states that resale is deliberately over-sampled for
     demonstration and gives the ratio against the real market's ~5.1% resale
     share, computed from the rows rather than typed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = REPO_ROOT / "fixtures" / "synthetic_store.json"

SEED = 20261107
UTC = timezone.utc

# The store's own reference point: every row in it happened before this, so the
# file cannot describe a future sale. The server's clock is later than this.
REFERENCE_LATEST = datetime(2026, 11, 6, 23, 59, tzinfo=UTC)

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ADDRESS_PREFIX = "SYN"
ADDRESS_LENGTH = 43
TAG_LENGTH = 4
BODY_LENGTH = ADDRESS_LENGTH - len(ADDRESS_PREFIX) - TAG_LENGTH

# A sale to one of these wallets then that wallet reselling is what makes the
# record show a repeat reseller. Names are internal; only addresses are stored.
RESELLER_SLOTS = 3


# -- base58, implemented here so the generator owes the package nothing -------

def b58_encode(data: bytes) -> str:
    number = int.from_bytes(data, "big")
    digits: list[str] = []
    while number:
        number, remainder = divmod(number, 58)
        digits.append(ALPHABET[remainder])
    leading_zeros = 0
    for byte in data:
        if byte:
            break
        leading_zeros += 1
    return "1" * leading_zeros + "".join(reversed(digits))


def b58_decode(text: str) -> bytes:
    number = 0
    for character in text:
        position = ALPHABET.find(character)
        if position < 0:
            raise ValueError(f"not a base58 character: {character!r}")
        number = number * 58 + position
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading_ones = len(text) - len(text.lstrip("1"))
    return b"\x00" * leading_ones + body


def _fixed_digits(number: int, width: int) -> str:
    digits: list[str] = []
    for _ in range(width):
        number, remainder = divmod(number, 58)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))


def _body(name: str, width: int) -> str:
    """Deterministic, well-spread base58 body for one address name."""
    characters: list[str] = []
    block = hashlib.sha256(name.encode("utf-8")).digest()
    while len(characters) < width:
        for byte in block:
            characters.append(ALPHABET[byte % 58])
            if len(characters) == width:
                break
        block = hashlib.sha256(block).digest()
    return "".join(characters)


class AddressBook:
    """Allocates placeholder addresses that announce themselves and stay distinct.

    The address is a 43-character base58 string: `SYN`, a deterministic body, and a
    four-character tag carrying the allocation counter. The tag makes the truncated
    form (`shortAddress` keeps the first four and last four characters) unique for
    every address in the store, which is what stops a custody trail reading as one
    wallet handing a ticket to itself.
    """

    def __init__(self) -> None:
        self._by_name: dict[str, str] = {}
        self._addresses: list[str] = []
        self._tags: set[str] = set()
        self._truncations: set[tuple[str, str]] = set()
        self._counter = 0

    def address(self, name: str) -> str:
        if name in self._by_name:
            return self._by_name[name]
        if self._counter >= 58 ** TAG_LENGTH:
            raise AssertionError("address space exhausted; widen the tag")
        # Scramble the counter: 7919 is coprime with 58, so this is a bijection
        # mod 58**4 and every tag stays unique, but the tails do not read as a
        # ramp (1111, 1112, ...) the way an unscrambled counter would.
        tag = _fixed_digits((self._counter * 7919 + 104729) % (58 ** TAG_LENGTH), TAG_LENGTH)
        text = f"{ADDRESS_PREFIX}{_body(f'{ADDRESS_PREFIX}:{name}', BODY_LENGTH)}{tag}"
        data = b58_decode(text)
        if len(data) != 32:
            raise AssertionError(f"{text!r} decodes to {len(data)} bytes, not 32")
        if b58_encode(data) != text:
            raise AssertionError(f"{text!r} does not round-trip through base58")
        truncation = (text[:4], text[-4:])
        if truncation in self._truncations:
            raise AssertionError(f"two addresses truncate to {truncation}")
        if tag in self._tags:
            raise AssertionError(f"duplicate tag {tag}")
        self._counter += 1
        self._by_name[name] = text
        self._addresses.append(text)
        self._tags.add(tag)
        self._truncations.add(truncation)
        return text

    @property
    def addresses(self) -> list[str]:
        return list(self._addresses)


# -- event specs -------------------------------------------------------------

def at(month: int, day: int, hour: int = 12, minute: int = 0, year: int = 2026) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


ORGANIZERS = [
    {
        "id": "org_syn_01",
        "name": "Synthetic Promotions Co-operative (demonstration)",
        "wallet": "organizer:org_syn_01",
    },
    {
        "id": "org_syn_02",
        "name": "Demonstration Events Lab (synthetic)",
        "wallet": "organizer:org_syn_02",
    },
    {
        "id": "org_syn_03",
        "name": "Fixture Organizing Group (synthetic)",
        "wallet": "organizer:org_syn_03",
    },
]

EVENT_SPECS = [
    {
        "key": "evt_syn_01",
        "slug": "synthetic-hall-cap-not-binding",
        "code": "HAL",
        "name": "Synthetic Hall: Cap Present, Not Binding",
        "venue": "Demonstration Hall North",
        "city": "Toronto",
        "starts": at(12, 5, 0, 30),
        "ends": at(12, 5, 3, 30),
        "status": "on_sale",
        "organizer": "org_syn_01",
        "cap": 2500,
        "resale": True,
        "verified": True,
        "regime": "cap_present_not_binding",
        "description": (
            "Synthetic demonstration record: a three-tier event with a +25% resale "
            "cap that no recorded sale reaches, generated by "
            "tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_hal_floor", "name": "Floor", "face": 1_000_000_000, "supply": 120, "issued": 6},
            {"id": "tier_hal_balcony", "name": "Balcony", "face": 2_500_000_000, "supply": 60, "issued": 5},
            {"id": "tier_hal_box", "name": "Box", "face": 5_000_000_000, "supply": 20, "issued": 3},
        ],
        "issue_from": at(9, 24, 9),
        "issue_window_hours": 288,
        "step_min_hours": 36,
        "step_max_hours": 144,
        "plan": "cap_present_not_binding",
    },
    {
        "key": "evt_syn_02",
        "slug": "synthetic-stage-cap-binding",
        "code": "STG",
        "name": "Synthetic Stage: Resale Cap Binds",
        "venue": "Sample Stage B",
        "city": "Hamilton",
        "starts": at(11, 21, 23),
        "ends": at(11, 22, 2),
        "status": "on_sale",
        "organizer": "org_syn_01",
        "cap": 1500,
        "resale": True,
        "verified": True,
        "regime": "cap_binding",
        "description": (
            "Synthetic demonstration record: the +15% resale cap binds on this event "
            "and most recorded sales sit exactly on it, generated by "
            "tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_stg_general", "name": "General", "face": 1_200_000_000, "supply": 200, "issued": 8},
            {"id": "tier_stg_front", "name": "Front", "face": 3_000_000_000, "supply": 80, "issued": 4},
        ],
        "issue_from": at(9, 10, 10),
        "issue_window_hours": 240,
        "step_min_hours": 36,
        "step_max_hours": 120,
        "plan": "cap_binding",
    },
    {
        "key": "evt_syn_03",
        "slug": "synthetic-annex-cold-start",
        "code": "ANX",
        "name": "Synthetic Annex: Cold Start, No Resales",
        "venue": "Fixture Room 1",
        "city": "Mississauga",
        "starts": at(12, 12, 1),
        "ends": at(12, 12, 4),
        "status": "on_sale",
        "organizer": "org_syn_02",
        "cap": 2000,
        "resale": True,
        "verified": False,
        "regime": "cold_start",
        "description": (
            "Synthetic demonstration record with no resale row at all, so the "
            "cold-start path reads a genuinely empty history, generated by "
            "tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_anx_standing", "name": "Standing", "face": 700_000_000, "supply": 90, "issued": 6},
            {"id": "tier_anx_seated", "name": "Seated", "face": 1_400_000_000, "supply": 40, "issued": 4},
        ],
        "issue_from": at(10, 10, 9),
        "issue_window_hours": 192,
        "step_min_hours": 48,
        "step_max_hours": 120,
        "plan": "cold_start",
    },
    {
        "key": "evt_syn_04",
        "slug": "sample-theatre-uncapped-spread",
        "code": "THR",
        "name": "Synthetic Theatre: Uncapped Markup Spread",
        "venue": "Sample Theatre",
        "city": "Kitchener",
        "starts": at(11, 14, 0),
        "ends": at(11, 14, 3),
        "status": "on_sale",
        "organizer": "org_syn_02",
        "cap": None,
        "resale": True,
        "verified": True,
        "regime": "uncapped_spread",
        "description": (
            "Synthetic demonstration record with no resale cap, so markups above "
            "+25% and sales below face both appear, generated by "
            "tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_thr_single", "name": "General Admission", "face": 800_000_000, "supply": 150, "issued": 11},
        ],
        "issue_from": at(9, 1, 11),
        "issue_window_hours": 240,
        "step_min_hours": 24,
        "step_max_hours": 96,
        "plan": "uncapped_spread",
    },
    {
        "key": "evt_syn_05",
        "slug": "demo-arena-east-resale-off",
        "code": "ARE",
        "name": "Demo Arena East: Resale Switched Off",
        "venue": "Demo Arena East",
        "city": "Ottawa",
        "starts": at(1, 16, 1, year=2027),
        "ends": at(1, 16, 4, year=2027),
        "status": "on_sale",
        "organizer": "org_syn_03",
        "cap": None,
        "resale": False,
        "verified": False,
        "regime": "resale_disabled",
        "description": (
            "Synthetic demonstration record from an organizer that has switched "
            "resale off, so the absence of transfer rows means what it says, "
            "generated by tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_are_lower", "name": "Lower Bowl", "face": 1_500_000_000, "supply": 100, "issued": 5},
            {"id": "tier_are_upper", "name": "Upper Bowl", "face": 2_400_000_000, "supply": 60, "issued": 3},
        ],
        "issue_from": at(10, 15, 10),
        "issue_window_hours": 144,
        "step_min_hours": 48,
        "step_max_hours": 120,
        "plan": "resale_disabled",
    },
    {
        "key": "evt_syn_06",
        "slug": "demonstration-annex-completed",
        "code": "CPL",
        "name": "Demonstration Annex: Completed Run",
        "venue": "Demonstration Annex",
        "city": "London",
        "starts": at(10, 3, 23, 30),
        "ends": at(10, 4, 2),
        "status": "completed",
        "organizer": "org_syn_02",
        "cap": 2500,
        "resale": True,
        "verified": True,
        "regime": "completed_run",
        "description": (
            "Synthetic demonstration record of a completed run: every ticket is "
            "redeemed at the door after its last recorded sale, generated by "
            "tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_cpl_standing", "name": "Standing", "face": 500_000_000, "supply": 40, "issued": 8},
        ],
        "issue_from": at(8, 1, 9),
        "issue_window_hours": 288,
        "step_min_hours": 48,
        "step_max_hours": 144,
        "plan": "completed_run",
    },
    {
        "key": "evt_syn_07",
        "slug": "synthetic-river-hall-tiered-cap",
        "code": "RIV",
        "name": "Synthetic River Hall: Cap Binds On One Tier",
        "venue": "Sample Hall, River Room",
        "city": "Guelph",
        "starts": at(11, 28, 0, 30),
        "ends": at(11, 28, 3),
        "status": "on_sale",
        "organizer": "org_syn_01",
        "cap": 2500,
        "resale": True,
        "verified": True,
        "regime": "tier_cap_binding",
        "description": (
            "Synthetic demonstration record where the +25% cap binds on the "
            "cheapest tier and not on the two above it, so per-tier markup stays "
            "visible, generated by tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_riv_gallery", "name": "Gallery", "face": 900_000_000, "supply": 80, "issued": 5},
            {"id": "tier_riv_mezzanine", "name": "Mezzanine", "face": 1_800_000_000, "supply": 60, "issued": 5},
            {"id": "tier_riv_box", "name": "Box", "face": 3_600_000_000, "supply": 30, "issued": 3},
        ],
        "issue_from": at(9, 20, 9),
        "issue_window_hours": 240,
        "step_min_hours": 48,
        "step_max_hours": 120,
        "plan": "tier_cap_binding",
    },
    {
        "key": "evt_syn_08",
        "slug": "fixture-studio-draft",
        "code": "STD",
        "name": "Synthetic Studio: Draft, Nothing Issued",
        "venue": "Fixture Studio",
        "city": "St. Catharines",
        "starts": at(2, 20, 0, year=2027),
        "ends": at(2, 20, 3, year=2027),
        "status": "draft",
        "organizer": "org_syn_03",
        "cap": None,
        "resale": True,
        "verified": False,
        "regime": "nothing_issued",
        "description": (
            "Synthetic demonstration record with nothing issued and nothing sold, "
            "so a draft event reads as empty rather than as zero, generated by "
            "tools/build_fixture_store.py, not a real show."
        ),
        "tiers": [
            {"id": "tier_std_single", "name": "General Admission", "face": 1_000_000_000, "supply": 60, "issued": 0},
        ],
        "issue_from": at(11, 1, 9),
        "issue_window_hours": 24,
        "step_min_hours": 48,
        "step_max_hours": 96,
        "plan": "nothing_issued",
    },
]

# A ticket's trail is a list of steps. A step is ("sale", markup_bps) or
# ("transfer",). The showcase ticket is fixed so the demo's four-row custody trail
# (issue, priced sale, unpriced gift, priced sale) is always present and always
# readable by hand.
SHOWCASE_STEPS = {
    "evt_syn_01": [("sale", 1800), ("transfer",), ("sale", -600)],
}


def _markup(plan: str, spec: dict, tier_index: int, rng: random.Random) -> int:
    """One intended markup in basis points, drawn from that regime's rule."""
    if plan == "cap_present_not_binding":
        return rng.randrange(-800, 1851, 50)
    if plan == "cap_binding":
        return spec["cap"] if rng.random() < 0.78 else rng.choice([300, 700, 1100])
    if plan == "uncapped_spread":
        return rng.choice([-3000, -1500, -400, 200, 900, 2500, 4000, 7000, 9000])
    if plan == "completed_run":
        return rng.choice([0, 500, 800, 1200, -1000])
    if plan == "tier_cap_binding":
        if tier_index == 0:
            return spec["cap"] if rng.random() < 0.80 else rng.choice([400, 1200])
        return rng.choice([200, 600, 900, 1200, 1400])
    raise AssertionError(f"unknown plan {plan!r}")


# How a resale event divides its tickets: (never resold, exactly one sale). The
# store over-samples resale on purpose, because it exists to exercise a resale
# computation; it is not a sample of any market and must not be read as one.
TRAIL_SHAPES = {
    "cap_present_not_binding": (0.50, 0.35),
    "cap_binding": (0.45, 0.35),
    "uncapped_spread": (0.45, 0.35),
    "completed_run": (0.35, 0.40),
    "tier_cap_binding": (0.45, 0.35),
}
GIFT_SHARE = 0.20

# The real-market figure the store's own density has to be read against, quoted
# from `records/findings/01-a-market-structure.md` §5: ~5% of purchased tickets
# resell, and 1.9m of 37.1m is 5.1%. Two independent measurements, class A.
# A reader who notices that this store resells most of its tickets has to be told
# that the density is a construction choice, not a market rate, on the same
# screen as the number.
REAL_RESALE_SHARE_PCT = 5.1
OVER_SAMPLED_MARKER = "deliberately over-sampled"


def sampling_clause(events: list[dict], tickets: list[dict], ledger: list[dict]) -> str:
    """One sentence: how far this store over-samples resale, and against what.

    The figures are computed from the rows so the sentence cannot drift from the
    store. Percentages are floored at the low end and rounded up at the high end,
    which is why it reads 62% to 77% rather than 62.5% to 76.9%.
    """
    resold = {row["ticketId"] for row in ledger if row["kind"] == "sale"}
    shares: list[tuple[int, int]] = []
    for event in events:
        issued = [ticket for ticket in tickets if ticket["eventId"] == event["id"]]
        if not issued:
            continue
        sold = sum(1 for ticket in issued if ticket["id"] in resold)
        if sold:
            shares.append((sold, len(issued)))
    if not shares:
        raise AssertionError("no event has a resale, so there is no ratio to state")
    low_pct = min(sold * 100 // issued for sold, issued in shares)
    high_pct = max(-(-sold * 100 // issued) for sold, issued in shares)
    low_ratio = max(1, round(low_pct / REAL_RESALE_SHARE_PCT))
    high_ratio = max(low_ratio, round(high_pct / REAL_RESALE_SHARE_PCT))
    return (
        f"The record is {OVER_SAMPLED_MARKER} for demonstration: {low_pct}% to {high_pct}% of "
        f"tickets resold at least once on the events that have resales, against "
        f"~{REAL_RESALE_SHARE_PCT}% of purchased tickets in the real market (class A), "
        f"{low_ratio} to {high_ratio} times the real rate."
    )


def plan_steps(spec: dict, ticket_index: int, tier_index: int, rng: random.Random) -> list[tuple]:
    """The trail a ticket gets, as markup intentions. Prices are derived below."""
    showcase = SHOWCASE_STEPS.get(spec["key"])
    if showcase is not None and ticket_index == 0:
        return list(showcase)

    plan = spec["plan"]
    if plan in ("cold_start", "resale_disabled", "nothing_issued"):
        return []

    def sale() -> tuple:
        return ("sale", _markup(plan, spec, tier_index, rng))

    # Every third ticket belongs to a flipper: bought by a shared reseller wallet
    # and resold, so the record shows a repeat reseller rather than one-off
    # holders. This is the only forced shape beyond the showcase ticket.
    if ticket_index > 0 and ticket_index % 4 == 0:
        return [sale(), sale()]

    never, once = TRAIL_SHAPES[plan]
    roll = rng.random()
    if roll < never:
        return []
    if roll < never + once:
        return [sale()]
    if rng.random() < GIFT_SHARE:
        return [sale(), ("transfer",), sale()]
    return [sale(), sale()]


# -- building ----------------------------------------------------------------

def stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:00.000Z")


def build_store() -> dict:
    rng = random.Random(SEED)
    addresses = AddressBook()

    organizers = [
        {
            "id": organizer["id"],
            "name": organizer["name"],
            "walletAddress": addresses.address(organizer["wallet"]),
            "verified": False,
        }
        for organizer in ORGANIZERS
    ]

    events: list[dict] = []
    tickets: list[dict] = []
    ledger: list[dict] = []
    ticket_number = 0
    ledger_number = 0

    for spec in EVENT_SPECS:
        event_tickets: list[dict] = []
        for tier_index, tier in enumerate(spec["tiers"]):
            for _seat in range(tier["issued"]):
                ticket_number += 1
                ticket_index = len(event_tickets)
                ticket_id = f"tkt_syn_{ticket_number:04d}"
                issuee = addresses.address(f"issuee:{ticket_id}")
                issue_at = spec["issue_from"] + timedelta(hours=rng.randrange(spec["issue_window_hours"]))

                rows: list[tuple[str, str | None, str | None, int | None, datetime]] = []
                rows.append(("issue", None, issuee, None, issue_at))

                holder = issuee
                cursor = issue_at
                steps = plan_steps(spec, ticket_index, tier_index, rng)
                for step_index, step in enumerate(steps):
                    cursor = cursor + timedelta(
                        hours=rng.randrange(spec["step_min_hours"], spec["step_max_hours"] + 1)
                    )
                    if step[0] == "transfer":
                        target = addresses.address(f"gift:{ticket_id}:{step_index}")
                        rows.append(("transfer", holder, target, None, cursor))
                        holder = target
                        continue
                    markup = step[1]
                    if markup == spec["cap"] and spec["cap"] is not None:
                        pass  # a recorded sale exactly on the cap: the binding case
                    price = tier["face"] * (10_000 + markup) // 10_000
                    if price * 10_000 != tier["face"] * (10_000 + markup):
                        raise AssertionError(
                            f"{ticket_id}: markup {markup} does not divide exactly on face {tier['face']}"
                        )
                    target = _buyer_for(spec, ticket_index, step_index, len(steps), ticket_id, holder, rng, addresses)
                    rows.append(("sale", holder, target, price, cursor))
                    holder = target

                redeemed_at = None
                if spec["plan"] == "completed_run":
                    last = rows[-1][4]
                    redeemed_at = max(spec["starts"] + timedelta(minutes=5), last + timedelta(hours=2))
                    redeemed_at = redeemed_at + timedelta(minutes=rng.randrange(0, 90))
                    rows.append(("redeem", holder, None, None, redeemed_at))

                for kind, from_wallet, to_wallet, price, occurred in rows:
                    ledger_number += 1
                    ledger.append(
                        {
                            "id": f"led_{ledger_number:04d}",
                            "ticketId": ticket_id,
                            "kind": kind,
                            "fromWallet": from_wallet,
                            "toWallet": to_wallet,
                            "priceLamports": price,
                            "signature": None,
                            "slot": None,
                            "occurredAt": stamp(occurred),
                        }
                    )

                ticket = {
                    "id": ticket_id,
                    "eventId": spec["key"],
                    "tierId": tier["id"],
                    "mintAddress": addresses.address(f"mint:{ticket_id}"),
                    "serial": f"{spec['code']}-{ticket_index + 1:04d}",
                    "issuedToWallet": issuee,
                    "ownerWallet": holder,
                    "status": "redeemed" if redeemed_at is not None else "valid",
                    "redeemedAt": stamp(redeemed_at) if redeemed_at is not None else None,
                }
                event_tickets.append(ticket)
                tickets.append(ticket)

        tiers = [
            {
                "id": tier["id"],
                "name": tier["name"],
                "faceValueLamports": tier["face"],
                "totalSupply": tier["supply"],
                "issuedCount": tier["issued"],
            }
            for tier in spec["tiers"]
        ]
        events.append(
            {
                "id": spec["key"],
                "slug": spec["slug"],
                "name": spec["name"],
                "description": spec["description"],
                "venue": spec["venue"],
                "city": spec["city"],
                "startsAt": stamp(spec["starts"]),
                "endsAt": stamp(spec["ends"]),
                "imageUrl": None,
                "organizerId": spec["organizer"],
                "status": spec["status"],
                "resaleEnabled": spec["resale"],
                "resalePriceCapBps": spec["cap"],
                # Region-aware resale caps (`records/REGION-CAPS-DESIGN.md`): the jurisdiction
                # the event is sold into. Every venue in this fixture is an invented Ontario
                # city, so every event is CA-ON, and Ontario's cap (in force 2026-04-24, over
                # the total price paid) is what `region_caps.resolve` returns for the events
                # whose start is after that date. The field is the INPUT to the policy; the
                # policy itself is derived per request and never stored here.
                "jurisdiction": spec.get("jurisdiction", "CA-ON"),
                "requiresVerifiedWallet": spec["verified"],
                "totalSupply": sum(tier["supply"] for tier in spec["tiers"]),
                "issuedCount": len(event_tickets),
                "tiers": tiers,
                # Metadata for a human reading the file. Not served: the contract's
                # Event type has no field for it, and event_records.build drops it.
                "demoRegime": spec["regime"],
            }
        )

    # Every description says how far the record over-samples resale. One sentence,
    # appended once, computed once: the density stays as it is and the label
    # explains it, so a reader who knows the real rate reads the resale share as
    # documentation of a construction rather than as a market measurement.
    clause = sampling_clause(events, tickets, ledger)
    for event in events:
        event["description"] = f"{event['description']} {clause}"

    return {
        "meta": {
            "synthetic": True,
            "label": (
                "SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, "
                "not real ticket data."
            ),
            "generator": "tools/build_fixture_store.py",
            "seed": SEED,
            "provenance": (
                "Produced by tools/build_fixture_store.py from the event specs in that "
                "file. Not scraped, not hand-edited, not derived from ticketpath or any "
                "market dataset, and never from ticketing-frontend/lib/mock."
            ),
            "notFor": (
                "Must not be used to estimate, validate or report any result. Every "
                "response carrying it also carries dataSource.synthetic = true."
            ),
            "keyConvention": (
                "Every wallet and mint begins with SYN and base58-decodes to 32 bytes, "
                "so it is shape-valid and still unmistakably a placeholder. No account "
                "exists on any cluster and no explorer will find one."
            ),
            "computedFields": (
                "Ledger rows carry priceLamports only. markupBps is computed by "
                "ticketpath.core.markup from each ticket's own tier face value, and "
                "every price here was built from an integer markup so that "
                "recomputation is exact."
            ),
            "missingOnChain": (
                "signature and slot are null on every row because this store is "
                "synthetic: it is generated from a seed rather than observed, and "
                "no transaction was read to produce any row. A program is deployed "
                "on devnet, and records/onchain-v2-devnet.json is the record of the "
                "run that did it; none of its transactions is a row here."
            ),
        },
        "cluster": "devnet",
        "organizers": organizers,
        "events": events,
        "tickets": tickets,
        "ledger": ledger,
        "walletRegions": {},
    }


def _buyer_for(
    spec: dict,
    ticket_index: int,
    step_index: int,
    step_count: int,
    ticket_id: str,
    seller: str,
    rng: random.Random,
    addresses: AddressBook,
) -> str:
    """Who buys. Named wallets are reused so the record shows repeat resellers."""
    is_final_step = step_index == step_count - 1
    is_flipper_purchase = step_index == 0 and ticket_index > 0 and ticket_index % 4 == 0
    if is_flipper_purchase:
        candidate = addresses.address(f"reseller:{(ticket_index // 4) % RESELLER_SLOTS}")
    elif is_final_step and ticket_index % 3 == 1:
        candidate = addresses.address(f"holder:{spec['code']}:{ticket_index % 2}")
    else:
        candidate = addresses.address(f"buyer:{ticket_id}:{step_index}")
    if candidate == seller:
        candidate = addresses.address(f"buyer:{ticket_id}:{step_index}:alt")
    return candidate


# -- verification ------------------------------------------------------------

def _markup_exact(price: int, face: int, intended_bps: int) -> int:
    """Recompute markup the way ticketpath.core.markup does: halves away from zero."""
    numerator = (price - face) * 10_000
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), face)
    if remainder * 2 >= face:
        quotient += 1
    value = sign * quotient
    if value != intended_bps:
        raise AssertionError(f"markup recomputed as {value}, built as {intended_bps}")
    return value


def verify(store: dict) -> list[str]:
    """Assert every invariant this generator claims, and return the human lines."""
    lines: list[str] = []
    organizers = {row["id"]: row for row in store["organizers"]}
    events = {row["id"]: row for row in store["events"]}
    tickets = {row["id"]: row for row in store["tickets"]}
    tier_face = {
        f"{event['id']}:{tier['id']}": tier["faceValueLamports"]
        for event in store["events"]
        for tier in event["tiers"]
    }
    rows_by_ticket: dict[str, list[dict]] = {ticket_id: [] for ticket_id in tickets}
    for row in store["ledger"]:
        if row["ticketId"] not in rows_by_ticket:
            raise AssertionError(f"ledger row {row['id']} references unknown ticket")
        rows_by_ticket[row["ticketId"]].append(row)

    # 1 and 2: addresses
    all_addresses = [organizer["walletAddress"] for organizer in store["organizers"]]
    all_addresses += [ticket["mintAddress"] for ticket in store["tickets"]]
    for ticket in store["tickets"]:
        all_addresses += [ticket["issuedToWallet"], ticket["ownerWallet"]]
    for row in store["ledger"]:
        for side in ("fromWallet", "toWallet"):
            if row[side]:
                all_addresses.append(row[side])
    unique_addresses = sorted(set(all_addresses))
    truncations = set()
    for address in unique_addresses:
        if not address.startswith(ADDRESS_PREFIX):
            raise AssertionError(f"address {address!r} does not carry the {ADDRESS_PREFIX} prefix")
        if len(b58_decode(address)) != 32:
            raise AssertionError(f"address {address!r} is not 32 bytes")
        truncation = (address[:4], address[-4:])
        if truncation in truncations:
            raise AssertionError(f"two addresses truncate to {truncation[0]}...{truncation[1]}")
        truncations.add(truncation)
    lines.append(f"addresses: {len(unique_addresses)} distinct, all {ADDRESS_PREFIX}*, 32 bytes, "
                 f"{len(truncations)} distinct truncations")

    # 3, 4, 5, 6: ledger row rules
    sale_count = 0
    for ticket_id, rows in rows_by_ticket.items():
        if not rows:
            raise AssertionError(f"ticket {ticket_id} has no ledger rows")
        ticket = tickets[ticket_id]
        face = tier_face[f"{ticket['eventId']}:{ticket['tierId']}"]
        rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
        if rows[0]["kind"] != "issue":
            raise AssertionError(f"ticket {ticket_id} does not start with its issue row")
        if sum(1 for row in rows if row["kind"] == "issue") != 1:
            raise AssertionError(f"ticket {ticket_id} has more than one issue row")
        if rows[0]["toWallet"] != ticket["issuedToWallet"]:
            raise AssertionError(f"ticket {ticket_id} issue row disagrees with issuedToWallet")
        if rows[0]["fromWallet"] is not None:
            raise AssertionError(f"ticket {ticket_id} issue row has a sender")
        previous_wallet = ticket["issuedToWallet"]
        previous_time = rows[0]["occurredAt"]
        last_sale_time = None
        for row in rows[1:]:
            if row["occurredAt"] <= previous_time:
                raise AssertionError(f"ticket {ticket_id} timestamps are not strictly increasing")
            previous_time = row["occurredAt"]
            if row["kind"] == "sale":
                if row["priceLamports"] is None:
                    raise AssertionError(f"sale row {row['id']} has no price")
                if row["fromWallet"] == row["toWallet"]:
                    raise AssertionError(f"sale row {row['id']} is a self transfer")
                intended = (row["priceLamports"] - face) * 10_000 // face
                if row["priceLamports"] * 10_000 % face != 0:
                    raise AssertionError(f"sale row {row['id']} price is not an exact bps of face")
                _markup_exact(row["priceLamports"], face, intended)
                sale_count += 1
                last_sale_time = row["occurredAt"]
            elif row["priceLamports"] is not None:
                raise AssertionError(f"{row['kind']} row {row['id']} carries a price")
            if row["kind"] != "issue" and row["fromWallet"] != previous_wallet:
                raise AssertionError(f"row {row['id']} does not continue the custody chain")
            previous_wallet = row["toWallet"] if row["toWallet"] is not None else previous_wallet
        if ticket["ownerWallet"] != previous_wallet:
            raise AssertionError(f"ticket {ticket_id} ownerWallet disagrees with the trail")
        if ticket["status"] == "redeemed":
            redeems = [row for row in rows if row["kind"] == "redeem"]
            if len(redeems) != 1:
                raise AssertionError(f"ticket {ticket_id} is redeemed without one redeem row")
            if last_sale_time is not None and redeems[0]["occurredAt"] <= last_sale_time:
                raise AssertionError(f"ticket {ticket_id} is redeemed before it was sold")
            if ticket["redeemedAt"] != redeems[0]["occurredAt"]:
                raise AssertionError(f"ticket {ticket_id} redeemedAt disagrees with its redeem row")
        elif any(row["kind"] == "redeem" for row in rows):
            raise AssertionError(f"ticket {ticket_id} has a redeem row but is not redeemed")
        for row in rows:
            if row["occurredAt"] > REFERENCE_LATEST.strftime("%Y-%m-%dT%H:%M:%S.000Z"):
                raise AssertionError(f"row {row['id']} is later than the store's reference point")
            event = events[ticket["eventId"]]
            if row["kind"] == "redeem":
                if not event["startsAt"] <= row["occurredAt"] <= event["endsAt"]:
                    raise AssertionError(f"row {row['id']} is redeemed outside its event's run")
            elif row["occurredAt"] >= event["startsAt"]:
                raise AssertionError(f"row {row['id']} happens after its event has started")
    lines.append(f"ledger: {len(store['ledger'])} rows over {len(tickets)} tickets, "
                 f"{sale_count} priced sales, custody chains linked, timestamps strict")

    # 7: declared counts agree with the rows
    for event in store["events"]:
        event_tickets = [ticket for ticket in store["tickets"] if ticket["eventId"] == event["id"]]
        if events[event["id"]]["issuedCount"] != len(event_tickets):
            raise AssertionError(f"event {event['id']} issuedCount disagrees with its tickets")
        if event["totalSupply"] != sum(tier["totalSupply"] for tier in event["tiers"]):
            raise AssertionError(f"event {event['id']} totalSupply disagrees with its tiers")
        for tier in event["tiers"]:
            here = sum(1 for ticket in event_tickets if ticket["tierId"] == tier["id"])
            if tier["issuedCount"] != here:
                raise AssertionError(f"tier {tier['id']} issuedCount disagrees with its tickets")
        if len(event_tickets) > 25:
            raise AssertionError(
                f"event {event['id']} has {len(event_tickets)} tickets; the frontend shows 25"
            )
    lines.append(f"counts: {len(store['events'])} events, {len(tickets)} tickets, "
                 f"every tier and event total matches its rows, no event above 25 tickets")

    # 8: the regimes the demo needs
    def sales_of(event_id: str) -> list[dict]:
        ticket_ids = {ticket["id"] for ticket in store["tickets"] if ticket["eventId"] == event_id}
        return [
            row
            for row in store["ledger"]
            if row["ticketId"] in ticket_ids and row["kind"] == "sale"
        ]

    def markups_of(event_id: str) -> list[int]:
        values = []
        for row in sales_of(event_id):
            ticket = tickets[row["ticketId"]]
            face = tier_face[f"{ticket['eventId']}:{ticket['tierId']}"]
            values.append((row["priceLamports"] - face) * 10_000 // face)
        return values

    def regime(name: str) -> dict:
        found = [event for event in store["events"] if event["demoRegime"] == name]
        if len(found) != 1:
            raise AssertionError(f"regime {name} appears {len(found)} times")
        return found[0]

    # cap present, not binding
    event = regime("cap_present_not_binding")
    markups = markups_of(event["id"])
    if not markups:
        raise AssertionError("the not-binding regime has no sales")
    if max(markups) >= event["resalePriceCapBps"]:
        raise AssertionError("a sale in the not-binding regime reaches the cap")
    if min(markups) >= 0:
        raise AssertionError("the not-binding regime has no sale below face")
    lines.append(
        f"regime cap_present_not_binding: {event['id']}, {len(markups)} sales, "
        f"markups {min(markups)}..{max(markups)} bps against a {event['resalePriceCapBps']} bps cap"
    )

    # cap binding
    event = regime("cap_binding")
    markups = markups_of(event["id"])
    at_cap = sum(1 for value in markups if value == event["resalePriceCapBps"])
    if not markups or at_cap * 100 < 60 * len(markups):
        raise AssertionError("the binding regime does not cluster at the cap")
    if max(markups) > event["resalePriceCapBps"]:
        raise AssertionError("a sale in the binding regime exceeds the cap")
    lines.append(
        f"regime cap_binding: {event['id']}, {at_cap} of {len(markups)} sales exactly on the "
        f"{event['resalePriceCapBps']} bps cap"
    )

    # cold start: no sale row anywhere on the event
    for name in ("cold_start", "resale_disabled", "nothing_issued"):
        event = regime(name)
        if sales_of(event["id"]):
            raise AssertionError(f"{name} has a sale row")
        lines.append(
            f"regime {name}: {event['id']}, "
            f"{len([t for t in store['tickets'] if t['eventId'] == event['id']])} tickets, 0 sales"
        )
    if regime("resale_disabled")["resaleEnabled"]:
        raise AssertionError("the resale-disabled event has resale enabled")
    if regime("nothing_issued")["issuedCount"] != 0:
        raise AssertionError("the draft event issues tickets")

    # uncapped spread reaches above +25% and below face
    event = regime("uncapped_spread")
    markups = markups_of(event["id"])
    if event["resalePriceCapBps"] is not None:
        raise AssertionError("the uncapped regime carries a cap")
    if max(markups) <= 2500 or min(markups) >= 0:
        raise AssertionError("the uncapped regime is not a spread")
    lines.append(
        f"regime uncapped_spread: {event['id']}, {len(markups)} sales, "
        f"markups {min(markups)}..{max(markups)} bps, no cap"
    )

    # completed run: every ticket redeemed after its last sale
    event = regime("completed_run")
    for ticket in store["tickets"]:
        if ticket["eventId"] == event["id"] and ticket["status"] != "redeemed":
            raise AssertionError("a completed-run ticket is not redeemed")
    lines.append(
        f"regime completed_run: {event['id']}, "
        f"{len([t for t in store['tickets'] if t['eventId'] == event['id']])} tickets, all redeemed"
    )

    # tier-conditional cap: at cap on the cheapest tier, below it above
    event = regime("tier_cap_binding")
    cheapest = min(event["tiers"], key=lambda tier: tier["faceValueLamports"])
    for row in sales_of(event["id"]):
        ticket = tickets[row["ticketId"]]
        face = tier_face[f"{ticket['eventId']}:{ticket['tierId']}"]
        markup = (row["priceLamports"] - face) * 10_000 // face
        if ticket["tierId"] == cheapest["id"]:
            if markup > event["resalePriceCapBps"]:
                raise AssertionError("a cheap-tier sale exceeds the cap")
        elif markup >= event["resalePriceCapBps"]:
            raise AssertionError("an expensive-tier sale reaches the cap")
    lines.append(
        f"regime tier_cap_binding: {event['id']}, cap binds on {cheapest['id']} only"
    )

    # 9: labels
    marker_hits = 0
    for event in store["events"]:
        for field in ("name", "description"):
            if not any(marker in event[field].lower() for marker in ("synthetic", "demo")):
                raise AssertionError(f"event {event['id']} {field} carries no synthetic marker")
            marker_hits += 1
    for organizer in store["organizers"]:
        if "synthetic" not in organizer["name"].lower() and "demonstration" not in organizer["name"].lower():
            raise AssertionError(f"organizer {organizer['id']} carries no marker")
        marker_hits += 1
    labelled = [event for event in store["events"] if OVER_SAMPLED_MARKER in event["description"]]
    for event in store["events"]:
        if OVER_SAMPLED_MARKER not in event["description"]:
            raise AssertionError(f"event {event['id']} description omits the sampling clause")
    lines.append(
        f"labelling: {marker_hits} name/description/organizer strings carry a marker, "
        f"{len(labelled)}/{len(store['events'])} descriptions state the resale over-sampling"
    )

    # volume and variety
    if not 40 <= len(tickets) <= 120:
        raise AssertionError(f"{len(tickets)} tickets is outside the documented 40..120")
    if not 6 <= len(store["events"]) <= 9:
        raise AssertionError("the store does not hold 6..9 events")
    for field in ("venue", "city"):
        values = [event[field] for event in store["events"]]
        if len(set(values)) != len(values):
            raise AssertionError(f"two events share a {field}")
    if len({event["startsAt"] for event in store["events"]}) != len(store["events"]):
        raise AssertionError("two events share a start time")
    structures = [
        (
            len(event["tiers"]),
            tuple(tier["faceValueLamports"] for tier in event["tiers"]),
            tuple(tier["totalSupply"] for tier in event["tiers"]),
        )
        for event in store["events"]
    ]
    if len(set(structures)) != len(structures):
        raise AssertionError("two events share a tier structure")
    tier_shapes = {len(event["tiers"]) for event in store["events"]}
    multi = [event for event in store["events"] if len({tier["faceValueLamports"] for tier in event["tiers"]}) > 1]
    if not multi:
        raise AssertionError("no event has more than one face value")
    lines.append(
        f"variety: {len(tier_shapes)} distinct tier counts and {len(structures)} distinct tier "
        f"structures, {len(multi)} multi-tier events with distinct faces, unique "
        f"venue/city/start per event"
    )

    # the per-tier-markup demonstration: a sale on a tier that is not the event's
    # cheapest, priced above the cheapest face. Measured against the cheapest face
    # it would read as a large markup; measured against its own tier face it is a
    # small one. A store without such a sale cannot show the difference.
    demonstration = None
    for event in store["events"]:
        lowest = min(tier["faceValueLamports"] for tier in event["tiers"])
        for row in sales_of(event["id"]):
            ticket = tickets[row["ticketId"]]
            face = tier_face[f"{ticket['eventId']}:{ticket['tierId']}"]
            if face > lowest:
                own = (row["priceLamports"] - face) * 10_000 // face
                wrong = (row["priceLamports"] - lowest) * 10_000 // lowest
                if own > 0 and wrong > own:
                    demonstration = (row["id"], event["id"], own, wrong)
                    break
        if demonstration:
            break
    if demonstration is None:
        raise AssertionError("no sale prices a ticket above the cheapest face on another tier")
    lines.append(
        f"per-tier markup: sale {demonstration[0]} on {demonstration[1]} reads "
        f"{demonstration[2]} bps against its own tier face and {demonstration[3]} bps "
        f"against the cheapest face"
    )

    # the custody-trail demonstration: one ticket whose trail is issue, priced
    # sale, unpriced gift, priced sale, so the demo's four-row card is real.
    shaped = [
        ticket_id
        for ticket_id, rows in rows_by_ticket.items()
        if [row["kind"] for row in rows] == ["issue", "sale", "transfer", "sale"]
    ]
    if not shaped:
        raise AssertionError("no ticket has the issue, sale, transfer, sale shape")
    lines.append(f"custody shape: {len(shaped)} tickets are issue, sale, gift, sale")

    # at least one wallet sells on more than one ticket: the repeat-reseller feature
    sellers: dict[str, set[str]] = {}
    for row in store["ledger"]:
        if row["kind"] == "sale":
            sellers.setdefault(row["fromWallet"], set()).add(row["ticketId"])
    repeat_sellers = {wallet: tickets for wallet, tickets in sellers.items() if len(tickets) > 1}
    if not repeat_sellers:
        raise AssertionError("no wallet sells on more than one ticket")
    biggest = max(len(ticket_ids) for ticket_ids in repeat_sellers.values())
    lines.append(
        f"behaviour: {len(repeat_sellers)} wallets sell on more than one ticket, "
        f"busiest sells {biggest}"
    )
    return lines


def dumps(store: dict) -> str:
    return json.dumps(store, indent=2, ensure_ascii=True) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify the file on disk matches a fresh build")
    parser.add_argument("--dump", action="store_true", help="print the store, write nothing")
    args = parser.parse_args(argv)

    store = build_store()
    lines = verify(store)
    payload = dumps(store)

    print(f"build_fixture_store.py: seed {SEED}, {len(store['events'])} events, "
          f"{len(store['tickets'])} tickets, {len(store['ledger'])} ledger rows")
    print("invariants enforced and asserted:")
    for line in lines:
        print(f"  [ok] {line}")

    if args.dump:
        sys.stdout.write(payload)
        return 0

    if args.check:
        on_disk = STORE_PATH.read_text(encoding="utf-8")
        if on_disk != payload:
            print(f"  [FAIL] {STORE_PATH} does not match a fresh build", file=sys.stderr)
            return 1
        print(f"  [ok] {STORE_PATH.relative_to(REPO_ROOT)} matches a fresh build exactly")
        return _load_through_adapter()

    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(payload, encoding="utf-8")
    print(f"  [ok] wrote {STORE_PATH.relative_to(REPO_ROOT)} ({len(payload)} bytes)")
    return _load_through_adapter()


def _load_through_adapter() -> int:
    """Prove the file the backend actually reads accepts it, refusals and all.

    The adapter holds an event back rather than refusing the store, so "it loaded" is not
    enough: a store the generator wrote may contain an event the engine cannot price, and
    `--check` must fail on one. Anything the loader will not serve is a failed build here.
    """
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from ticketpath.adapters.ledger_adapter import LedgerAdapter, StoreError
        from ticketpath.core import base58 as core_base58
    except ImportError as exc:  # pragma: no cover - only when run outside the repo
        print(f"  [skip] adapter cross-check unavailable: {exc}")
        return 0
    try:
        adapter = LedgerAdapter.from_fixture(STORE_PATH)
    except StoreError as exc:
        print(f"  [FAIL] the adapter refuses the store: {exc}", file=sys.stderr)
        return 1
    rejected = adapter.rejections()
    if rejected:
        for event_id, reason in rejected.items():
            print(f"  [FAIL] {event_id} cannot be priced: {reason['code']}", file=sys.stderr)
        return 1
    for event in adapter.events():
        for tier in event["tiers"]:
            assert tier["issuedCount"] >= 0
    for address in (
        [row["mintAddress"] for row in adapter.tickets()]
        + [row["ownerWallet"] for row in adapter.tickets()]
        + [row["issuedToWallet"] for row in adapter.tickets()]
        + [adapter.organizer(event["organizerId"])["walletAddress"] for event in adapter.events()]
    ):
        if core_base58.encode(core_base58.decode(address)) != address:
            raise AssertionError(f"{address!r} disagrees with ticketpath.core.base58")
    print("  [ok] LedgerAdapter.from_fixture accepts it; ticketpath.core.base58 round-trips every address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
