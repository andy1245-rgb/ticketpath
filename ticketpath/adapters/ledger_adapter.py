"""The only path to ledger data.

Today that data is a JSON file in `fixtures/`, or an empty store. There is no
database, no chain reader and no scrape path here, because none of those exist
yet. When a real ledger arrives it is this file that changes; nothing above it
knows where the rows came from.

The adapter is deliberately strict about its source. A store that does not
declare `meta.synthetic: true` is refused, because the one thing this system must
never do is serve a synthetic ledger that has stopped announcing itself. The
checks below also make the store prove its own internal consistency, so a shape
change cannot quietly turn into a wrong number three layers up.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Mapping

DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "synthetic_store.json"
MODES = ("fixture", "empty")

LEDGER_KINDS = ("issue", "sale", "transfer", "redeem", "revoke")
TICKET_STATUSES = ("valid", "listed", "redeemed", "revoked")
EVENT_STATUSES = ("draft", "on_sale", "sold_out", "completed", "cancelled")


class StoreError(RuntimeError):
    """The store cannot be served as-is. Raised at load, never at request time."""


class LedgerAdapter:
    """Read-only access to events, tickets and ledger rows."""

    def __init__(self, store: Mapping, mode: str, origin: str):
        self._store = store
        self.mode = mode
        self.origin = origin
        self.meta = store["meta"]
        self._events: list[dict] = list(store["events"])
        self._tickets: list[dict] = list(store["tickets"])
        self._ledger: list[dict] = list(store["ledger"])
        self._organizers = {row["id"]: row for row in store["organizers"]}
        self._regions: dict[str, str] = dict(store.get("walletRegions") or {})
        self._tier_by_id, self._tier_by_ticket = self._index_tiers()
        self._entries_by_ticket = self._index_entries()

    # -- loading ---------------------------------------------------------

    @classmethod
    def from_fixture(cls, path: str | os.PathLike[str] | None = None) -> "LedgerAdapter":
        """Load and validate the synthetic store."""
        target = Path(path) if path is not None else DEFAULT_FIXTURE_PATH
        try:
            raw = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise StoreError(f"cannot read ledger fixture at {target}: {exc}") from exc
        try:
            store = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StoreError(f"ledger fixture at {target} is not valid JSON: {exc}") from exc
        adapter = cls(store, mode="fixture", origin=str(target))
        adapter._validate()
        return adapter

    @classmethod
    def empty(cls) -> "LedgerAdapter":
        """An empty store: the honest answer before any ledger exists."""
        return cls(
            {
                "meta": {
                    "synthetic": False,
                    "label": "Empty store. No events, no tickets, no ledger rows exist.",
                    "provenance": "Not a fixture: this is the absence of data, served as absence.",
                    "notFor": "Nothing to estimate from.",
                    "keyConvention": "No keys.",
                    "computedFields": "None.",
                    "missingOnChain": "Everything on-chain.",
                },
                "cluster": "devnet",
                "organizers": [],
                "events": [],
                "tickets": [],
                "ledger": [],
                "walletRegions": {},
            },
            mode="empty",
            origin="empty",
        )

    @classmethod
    def from_env(cls) -> "LedgerAdapter":
        """Fixture unless TICKETPATH_LEDGER_MODE=empty."""
        mode = os.environ.get("TICKETPATH_LEDGER_MODE", "fixture").strip().lower()
        if mode not in MODES:
            raise StoreError(f"TICKETPATH_LEDGER_MODE must be one of {MODES}, got {mode!r}")
        if mode == "empty":
            return cls.empty()
        return cls.from_fixture(os.environ.get("TICKETPATH_FIXTURE_PATH"))

    # -- integrity -------------------------------------------------------

    def _validate(self) -> None:
        if self.meta.get("synthetic") is not True:
            raise StoreError(
                "refusing to serve a ledger store that does not declare meta.synthetic = true; "
                "an unlabelled store cannot be distinguished from real data"
            )
        for organizer in self._organizers.values():
            _require_keys(organizer, ("id", "name", "walletAddress", "verified"), "organizer")
        for event in self._events:
            _require_keys(
                event,
                ("id", "slug", "name", "venue", "city", "startsAt", "status", "tiers", "organizerId"),
                "event",
            )
            if event["status"] not in EVENT_STATUSES:
                raise StoreError(f"event {event['id']} has unknown status {event['status']!r}")
            if event["organizerId"] not in self._organizers:
                raise StoreError(f"event {event['id']} references unknown organizer")
            tier_ids = [tier["id"] for tier in event["tiers"]]
            if len(set(tier_ids)) != len(tier_ids):
                raise StoreError(f"event {event['id']} has duplicate tier ids")
            for tier in event["tiers"]:
                if tier["faceValueLamports"] <= 0:
                    raise StoreError(f"tier {tier['id']} has a non-positive face value")
                if tier["issuedCount"] > tier["totalSupply"]:
                    raise StoreError(f"tier {tier['id']} issued more tickets than its supply")
            tickets_here = [ticket for ticket in self._tickets if ticket["eventId"] == event["id"]]
            if len(tickets_here) != sum(tier["issuedCount"] for tier in event["tiers"]):
                raise StoreError(
                    f"event {event['id']} issuedCount disagrees with its ticket rows "
                    f"({len(tickets_here)} rows)"
                )
            if event.get("totalSupply") is not None and event["totalSupply"] != sum(
                tier["totalSupply"] for tier in event["tiers"]
            ):
                raise StoreError(f"event {event['id']} totalSupply disagrees with its tiers")
            if event.get("issuedCount") is not None and event["issuedCount"] != len(tickets_here):
                raise StoreError(f"event {event['id']} issuedCount disagrees with its ticket rows")

        seen_ids: set[str] = set()
        seen_mints: set[str] = set()
        for ticket in self._tickets:
            _require_keys(
                ticket,
                ("id", "eventId", "tierId", "mintAddress", "serial", "issuedToWallet", "ownerWallet", "status"),
                "ticket",
            )
            if ticket["id"] in seen_ids:
                raise StoreError(f"duplicate ticket id {ticket['id']}")
            if ticket["mintAddress"] in seen_mints:
                raise StoreError(f"duplicate mint address {ticket['mintAddress']}")
            seen_ids.add(ticket["id"])
            seen_mints.add(ticket["mintAddress"])
            if ticket["status"] not in TICKET_STATUSES:
                raise StoreError(f"ticket {ticket['id']} has unknown status {ticket['status']!r}")
            event = next((row for row in self._events if row["id"] == ticket["eventId"]), None)
            if event is None:
                raise StoreError(f"ticket {ticket['id']} references unknown event")
            if ticket["tierId"] not in [tier["id"] for tier in event["tiers"]]:
                raise StoreError(f"ticket {ticket['id']} references a tier of another event")
            entries = self._entries_by_ticket.get(ticket["id"], [])
            issues = [entry for entry in entries if entry["kind"] == "issue"]
            if len(issues) != 1:
                raise StoreError(f"ticket {ticket['id']} must have exactly one issue entry")
            if issues[0]["toWallet"] != ticket["issuedToWallet"]:
                raise StoreError(f"ticket {ticket['id']} issue entry disagrees with issuedToWallet")
            moves = [entry for entry in entries if entry["kind"] in ("sale", "transfer")]
            expected_owner = moves[-1]["toWallet"] if moves else ticket["issuedToWallet"]
            if ticket["ownerWallet"] != expected_owner:
                raise StoreError(
                    f"ticket {ticket['id']} ownerWallet disagrees with the last custody move"
                )

        seen_ledger_ids: set[str] = set()
        for row in self._ledger:
            _require_keys(
                row,
                ("id", "ticketId", "kind", "priceLamports", "signature", "slot", "occurredAt"),
                "ledger row",
            )
            if row["id"] in seen_ledger_ids:
                raise StoreError(f"duplicate ledger id {row['id']}")
            seen_ledger_ids.add(row["id"])
            if row["kind"] not in LEDGER_KINDS:
                raise StoreError(f"ledger row {row['id']} has unknown kind {row['kind']!r}")
            if row["ticketId"] not in seen_ids:
                raise StoreError(f"ledger row {row['id']} references unknown ticket")
            price = row["priceLamports"]
            if price is not None and (not isinstance(price, int) or isinstance(price, bool) or price < 0):
                raise StoreError(f"ledger row {row['id']} has an unusable price")
            if row["kind"] != "sale" and price is not None:
                raise StoreError(
                    f"ledger row {row['id']} is a {row['kind']} with a price; only sales carry money"
                )

    def _index_tiers(self) -> tuple[dict[str, dict], dict[str, dict]]:
        tier_by_id: dict[str, dict] = {}
        tier_by_ticket: dict[str, dict] = {}
        event_tiers = {event["id"]: event["tiers"] for event in self._events}
        for event_id, tiers in event_tiers.items():
            for tier in tiers:
                tier_by_id[f"{event_id}:{tier['id']}"] = tier
        for ticket in self._tickets:
            tier_by_ticket[ticket["id"]] = tier_by_id[f"{ticket['eventId']}:{ticket['tierId']}"]
        return tier_by_id, tier_by_ticket

    def _index_entries(self) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for row in self._ledger:
            grouped.setdefault(row["ticketId"], []).append(row)
        for rows in grouped.values():
            rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
        return grouped

    # -- reads -----------------------------------------------------------

    def events(self) -> Iterable[dict]:
        return list(self._events)

    def event(self, event_id: str) -> dict | None:
        return next((row for row in self._events if row["id"] == event_id), None)

    def organizer(self, organizer_id: str) -> dict:
        return self._organizers[organizer_id]

    def tickets(self) -> Iterable[dict]:
        return list(self._tickets)

    def ticket(self, ticket_id: str) -> dict | None:
        return next((row for row in self._tickets if row["id"] == ticket_id), None)

    def tickets_for_event(self, event_id: str) -> list[dict]:
        return [row for row in self._tickets if row["eventId"] == event_id]

    def tier_of_ticket(self, ticket_id: str) -> dict:
        return self._tier_by_ticket[ticket_id]

    def raw_entries(self, ticket_id: str) -> list[dict]:
        """Raw ledger rows for one ticket, chronological."""
        return list(self._entries_by_ticket.get(ticket_id, []))

    def raw_entries_for_event(self, event_id: str) -> list[dict]:
        """Raw ledger rows for every ticket of an event, chronological."""
        ticket_ids = {row["id"] for row in self._tickets if row["eventId"] == event_id}
        rows = [row for ticket_id in ticket_ids for row in self._entries_by_ticket.get(ticket_id, [])]
        rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
        return rows

    def face_by_ticket(self, event_id: str | None = None) -> dict[str, int]:
        """Each ticket's own tier face value, for markup."""
        if event_id is None:
            return {ticket_id: tier["faceValueLamports"] for ticket_id, tier in self._tier_by_ticket.items()}
        return {
            ticket["id"]: self._tier_by_ticket[ticket["id"]]["faceValueLamports"]
            for ticket in self._tickets
            if ticket["eventId"] == event_id
        }

    def wallet_region(self, wallet: str) -> str | None:
        """Only ever populated when the wallet volunteered a region. Currently never."""
        return self._regions.get(wallet)

    def wallet_regions(self) -> dict[str, str]:
        return dict(self._regions)

    @property
    def label(self) -> str:
        return self.meta.get("label", "")


def _require_keys(row: Mapping, keys: tuple[str, ...], what: str) -> None:
    missing = [key for key in keys if key not in row]
    if missing:
        raise StoreError(f"{what} {row.get('id', '<no id>')} is missing {missing}")
