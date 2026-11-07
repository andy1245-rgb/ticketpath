"""Routes a request to adapters and core, decides, and does not calculate.

Every arithmetic result in a response comes from `ticketpath.core`. This file
chooses which core function to call and which adapter to read, wires the injected
clock and the cluster, and attaches the data-source envelope that makes synthetic
data announce itself. If you find addition in here, it is in the wrong file.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Callable

from ticketpath import __version__
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.core import (
    event_analytics,
    event_records,
    ledger_entries,
    pagination,
    resale_stats,
    ticket_records,
    wallet_verification,
)
from ticketpath.core.timeutil import to_iso
from ticketpath.errors import bad_request, not_found

SOURCE_FIXTURE = "synthetic-fixture"
SOURCE_EMPTY = "empty-store"


class Orchestrator:
    """One instance per server process. Holds the adapters and the clock."""

    def __init__(
        self,
        ledger: LedgerAdapter,
        rpc: RpcAdapter,
        pricing_model: PricingModelAdapter,
        cluster: str,
        now: Callable[[], datetime] | None = None,
    ):
        self.ledger = ledger
        self.rpc = rpc
        self.pricing_model = pricing_model
        self.cluster = cluster
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._verification_state = wallet_verification.empty_state()
        self._verification_lock = threading.Lock()

    # -- time and provenance ---------------------------------------------

    def now(self) -> datetime:
        return self._now()

    def data_source(self) -> dict:
        """The envelope every ledger-backed payload carries."""
        if self.ledger.mode == "empty":
            return {
                "mode": SOURCE_EMPTY,
                "synthetic": False,
                "label": self.ledger.label,
                "note": "No ledger exists yet. Nothing was invented to fill it.",
            }
        return {
            "mode": SOURCE_FIXTURE,
            "synthetic": True,
            "label": self.ledger.label,
            "note": (
                "Computed by ticketpath core from fixtures/synthetic_store.json. "
                "Not real ticket data, not a scrape, and not evidence of anything."
            ),
        }

    def verification_source(self) -> dict:
        return {
            "mode": "in-memory-verification",
            "synthetic": False,
            "label": "Wallet verification state is in memory and is lost when the server stops.",
            "note": "Signatures are checked with Ed25519 (RFC 8032) against the submitted public key.",
        }

    def _sourced(self, payload: dict, source: dict | None = None) -> dict:
        body = dict(payload)
        body["dataSource"] = source or self.data_source()
        return body

    # -- health ----------------------------------------------------------

    def health(
        self,
        endpoints_implemented: int,
        endpoints_in_contract: int,
        routes_implemented: int,
    ) -> dict:
        return {
            "service": "ticketpath",
            "version": __version__,
            "status": "ok",
            "now": to_iso(self.now()),
            "dataSource": self.data_source(),
            "chain": self.rpc.program_status(),
            "pricingModel": self.pricing_model.status(),
            "contract": {
                "source": "ticketing-frontend/lib/types.ts + API_CONTRACT.md",
                "endpointsInContract": endpoints_in_contract,
                "endpointsImplemented": endpoints_implemented,
                "routesImplemented": routes_implemented,
                "map": "records/CONTRACT-MAP.md",
            },
        }

    # -- events ----------------------------------------------------------

    def list_events(
        self,
        status: str | None = None,
        city: str | None = None,
        text: str | None = None,
        cursor: str | None = None,
        limit: int = pagination.DEFAULT_LIMIT,
    ) -> dict:
        rows = [
            event
            for event in self.ledger.events()
            if event_records.matches_query(event, status, city, text)
        ]
        rows.sort(key=event_records.sort_key_by_start)
        shaped = [
            event_records.build(row, self.ledger.organizer(row["organizerId"])) for row in rows
        ]
        return self._sourced(pagination.paginate(shaped, cursor, limit))

    def get_event(self, id_or_slug: str) -> dict:
        row = event_records.find(self.ledger.events(), id_or_slug)
        if row is None:
            raise not_found("event", id_or_slug)
        return self._sourced(event_records.build(row, self.ledger.organizer(row["organizerId"])))

    # -- tickets ---------------------------------------------------------

    def _ticket_payload(self, ticket_row: dict) -> dict:
        tier = self.ledger.tier_of_ticket(ticket_row["id"])
        entries = ledger_entries.to_entries(
            self.ledger.raw_entries(ticket_row["id"]),
            {ticket_row["id"]: tier["faceValueLamports"]},
        )
        enforcement = self.rpc.transfer_enforcement(ticket_row["mintAddress"])
        return ticket_records.build(ticket_row, tier, entries, enforcement["enforced"])

    def list_tickets(
        self,
        event_id: str | None = None,
        owner_wallet: str | None = None,
        status: str | None = None,
        cursor: str | None = None,
        limit: int = pagination.DEFAULT_LIMIT,
    ) -> dict:
        rows = [
            ticket
            for ticket in self.ledger.tickets()
            if (event_id is None or ticket["eventId"] == event_id)
            and (owner_wallet is None or ticket["ownerWallet"] == owner_wallet)
            and (status is None or ticket["status"] == status)
        ]
        rows.sort(key=lambda row: row["id"])
        shaped = [self._ticket_payload(row) for row in rows]
        return self._sourced(pagination.paginate(shaped, cursor, limit))

    def get_ticket(self, id_or_mint: str) -> dict:
        row = self.ledger.ticket(id_or_mint)
        if row is None:
            row = next(
                (ticket for ticket in self.ledger.tickets() if ticket["mintAddress"] == id_or_mint),
                None,
            )
        if row is None:
            raise not_found("ticket", id_or_mint)
        return self._sourced(self._ticket_payload(row))

    def resale_history(self, ticket_id: str) -> dict:
        """The core endpoint: full trail plus stats, computed from the ledger rows."""
        row = self.ledger.ticket(ticket_id)
        if row is None:
            raise not_found("ticket", ticket_id)
        tier = self.ledger.tier_of_ticket(ticket_id)
        entries = ledger_entries.to_entries(
            self.ledger.raw_entries(ticket_id),
            {ticket_id: tier["faceValueLamports"]},
        )
        payload = resale_stats.build(row, tier["faceValueLamports"], entries)
        body = self._sourced(payload)
        body["custodyNote"] = (
            "signature and slot are null because no transaction exists: no program is deployed."
        )
        return body

    # -- analytics -------------------------------------------------------

    def event_analytics(self, event_id: str) -> dict:
        event = self.ledger.event(event_id)
        if event is None:
            raise not_found("event", event_id)
        tickets = self.ledger.tickets_for_event(event_id)
        entries = ledger_entries.to_entries(
            self.ledger.raw_entries_for_event(event_id),
            self.ledger.face_by_ticket(event_id),
        )
        payload = event_analytics.build(event, tickets, entries, self.ledger.wallet_regions())
        body = self._sourced(payload)
        body["analyticsNote"] = (
            "avgMarkupBps is the mean of per-sale markups measured against each sale's own "
            "ticket face value, never derived from avgPriceLamports."
        )
        return body

    # -- wallet verification ---------------------------------------------

    def wallet_verification(self, wallet: str) -> dict:
        try:
            address = wallet_verification.normalise_wallet(wallet)
        except wallet_verification.WalletAddressError as exc:
            raise bad_request(str(exc), "wallet_malformed") from exc
        with self._verification_lock:
            payload = wallet_verification.view(self._verification_state, address)
        return self._sourced(payload, self.verification_source())

    def start_verification(self, wallet: str) -> dict:
        try:
            address = wallet_verification.normalise_wallet(wallet)
        except wallet_verification.WalletAddressError as exc:
            raise bad_request(str(exc), "wallet_malformed") from exc
        with self._verification_lock:
            payload = wallet_verification.issue_challenge(
                self._verification_state, address, self.now()
            )
        return self._sourced(payload, self.verification_source())

    def complete_verification(self, wallet: str, body: dict) -> dict:
        try:
            address = wallet_verification.normalise_wallet(wallet)
        except wallet_verification.WalletAddressError as exc:
            raise bad_request(str(exc), "wallet_malformed") from exc
        nonce = body.get("nonce")
        signature = body.get("signature")
        if not isinstance(nonce, str) or not nonce:
            raise bad_request("nonce is required", "nonce_missing")
        if not isinstance(signature, str) or not signature:
            raise bad_request("signature is required", "signature_missing")
        with self._verification_lock:
            try:
                payload = wallet_verification.complete(
                    self._verification_state,
                    address,
                    nonce,
                    signature,
                    self.now(),
                    self.cluster,
                )
            except wallet_verification.VerificationError as exc:
                raise bad_request(str(exc), exc.reason) from exc
        return self._sourced(payload, self.verification_source())

    # -- the pricing seam, not exposed by the contract --------------------

    def price_estimate(self, request: dict) -> dict:
        """Route an engine question to the model seam. Unavailable in this build."""
        enriched = dict(request)
        enriched.setdefault("asOf", to_iso(self.now()))
        return self.pricing_model.estimate(enriched)
