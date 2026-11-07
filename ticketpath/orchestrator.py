"""Routes a request to adapters and core, decides, and does not calculate.

Every arithmetic result in a response comes from `ticketpath.core`. This file
chooses which core function to call and which adapter to read, wires the injected
clock and the cluster, and attaches the data-source envelope that makes synthetic
data announce itself. If you find addition in here, it is in the wrong file.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ticketpath import __version__
from ticketpath.adapters import chain_client
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.api import guidance
from ticketpath.core import (
    event_analytics,
    event_records,
    intensity,
    labels,
    ledger_entries,
    pagination,
    path_model,
    price_features,
    primary_optimum,
    resale_stats,
    ticket_records,
    value_band,
    wallet_verification,
)
from ticketpath.core.timeutil import parse, to_iso
from ticketpath.errors import ApiError, bad_request, not_found
from ticketpath.onchain import sim

DEVNET_ARTEFACT_PATH = Path(__file__).resolve().parents[1] / "records" / "devnet-artefacts.json"
MODEL_VERSION = "engine-2026-11-07"
TAU_MIN, TAU_MAX = 0.10, 0.406
MAX_CAP_BPS = 10000
# A per-ticket fee is a parameter, and an unbounded one is not a parameter. One million SOL
# per ticket is far above any ticket price this engine will ever price, so anything past it
# is a typo, and the net line is integer arithmetic that does not need to survive 21 digits.
MAX_FEE_LAMPORTS = 10**15

DECISION_MODES = ("counterfactual", "before_on_sale")

SOURCE_FIXTURE = "synthetic-fixture"
SOURCE_EMPTY = "empty-store"


def _excluded_own_counts(tickets, ledger, event_id: str, cut: datetime) -> dict:
    """What the before-on-sale mode refuses to look at, counted at the same cut.

    Ticket rows and priced sale rows on this event at or before the cut. It is a count of
    rows in the store, never an input to a price: the estimator still sees nothing of this
    event's own record. Without it the page printed `0 resales` and `0 tickets` for a store
    that holds 12 of each, which reads as an absent record rather than as an excluded one
    (08-fix-verification 3.1/R1, 10-final-review N4).
    """
    own = {ticket["id"] for ticket in tickets if ticket["eventId"] == event_id}
    at_cut = [row for row in ledger if row["ticketId"] in own and parse(row["occurredAt"]) <= cut]
    return {
        "resales": sum(1 for row in at_cut if row["kind"] == "sale" and row["priceLamports"] is not None),
        "tickets": len({row["ticketId"] for row in at_cut if row["kind"] == "issue"}),
    }


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

    # -- the console's decision: route, do not calculate -------------------

    def price_guidance(
        self,
        *,
        event_id: str | None = None,
        tier_id: str | None = None,
        as_of: str | None = None,
        cap_bps: str | int | None = None,
        fee_lamports: str | int | None = None,
        tau: str | float | None = None,
        show_sim: bool = False,
        mode: str | None = None,
    ) -> dict:
        """Assemble the console payload. Every number in it arrives computed by `core`.

        `mode` is the decision instant, and it is never silent:

        * `counterfactual` (the default) recomputes the value from this event's own record
          and the page says it is a hindsight recomputation.
        * `before_on_sale` is the real primary-price decision: only other events' completed
          resale records and this event's own metadata enter it. Its value block refuses
          when there is no other event to pool.
        """
        cut = self.now() if as_of in (None, "") else self._parse_query_instant(as_of)
        cap_candidate = self._parse_cap(cap_bps)
        fee = self._parse_fee(fee_lamports)
        declared_tau = self._parse_tau(tau)
        decision_mode = self._parse_mode(mode)

        events = list(self.ledger.events())
        tickets = list(self.ledger.tickets())
        ledger = self.ledger.raw_ledger()
        faces = self.ledger.face_by_ticket()
        # An event the loader held back is refused by name, with the reason the loader gave,
        # before anything is computed. It is not a 404: the event exists in the store and the
        # store says why it cannot be priced. Every other event in the store still serves.
        held_back = self.ledger.rejections()
        if event_id not in (None, "") and event_id in held_back:
            raise self._rejection_error(held_back[event_id])
        if not events:
            if held_back:
                raise self._rejection_error(next(iter(held_back.values())))
            raise bad_request("no ledger exists, so there is nothing to price", "no_ledger")

        own_rows = decision_mode == "counterfactual"
        try:
            index = price_features.cross_section(
                events=events,
                tickets=tickets,
                ledger=ledger,
                tier_faces=faces,
                as_of=cut,
                own_record_excluded=None if own_rows else event_id,
            )
        except price_features.FeatureError as exc:
            raise ApiError(422, str(exc), exc.code) from exc
        if event_id in (None, ""):
            event_id, tier_id = price_features.default_selection(index)
        event = next((row for row in events if row["id"] == event_id), None)
        if event is None:
            raise not_found("event", str(event_id))
        if not event["tiers"]:
            raise ApiError(422, labels.render("P_NO_TIER"), "event_has_no_tier")
        if tier_id in (None, ""):
            tier_id = event["tiers"][0]["id"]
        if all(tier["id"] != tier_id for tier in event["tiers"]):
            raise not_found("tier", str(tier_id))

        try:
            features = price_features.build(
                events=events,
                tickets=tickets,
                ledger=ledger,
                tier_faces=faces,
                event_id=event_id,
                as_of=cut,
                use_own_rows=own_rows,
            )
        except price_features.FeatureError as exc:
            raise ApiError(422, str(exc), exc.code) from exc
        pool = value_band.pooled(rows=index, declared_tau=declared_tau)
        # The cap in force on this page: the one in the URL when it carries one, and the
        # recorded cap otherwise. It is one number, resolved once, and it travels into the
        # recommendation as well as into the payload -- otherwise the page says it honours a
        # cap that never reached the arithmetic that produced the price beside it.
        cap_in_force = cap_candidate if cap_candidate is not None else event.get("resalePriceCapBps")
        bands: dict[str, dict] = {}
        paths: dict[str, dict] = {}
        intensities: dict[str, dict] = {}
        recommendations: dict[str, dict] = {}
        for tier in features["tiers"]:
            band = value_band.estimate(
                features=features,
                tier_id=tier["tierId"],
                tau=declared_tau,
                cap_bps_candidate=cap_candidate,
                pool=pool,
                decision_mode=decision_mode,
            )
            if band["regime"] == "capped_and_binding":
                anchor = band["floorLamports"]
            elif band["level"]["available"]:
                anchor = band["level"]["lamports"]
            else:
                anchor = tier["faceValueLamports"]
            rate = intensity.estimate(features=features, tier_id=tier["tierId"], pool=index)
            recommendation = primary_optimum.recommend(
                features=features,
                tier_id=tier["tierId"],
                band=band,
                intensity=rate,
                fee=fee,
                sell_through_floor=None,
                cap_bps_candidate=cap_in_force,
            )
            bands[tier["tierId"]] = band
            paths[tier["tierId"]] = path_model.estimate(
                features=features, tier_id=tier["tierId"], anchor_lamports=anchor
            )
            intensities[tier["tierId"]] = rate
            recommendations[tier["tierId"]] = recommendation

        payload = guidance.build(
            event=event,
            tiers=features["tiers"],
            features=features,
            bands=bands,
            paths=paths,
            intensities=intensities,
            recommendations=recommendations,
            as_of=to_iso(cut),
            data_source=self.data_source(),
            params={
                "tau": declared_tau,
                "capBpsCandidate": cap_in_force,
                "feeLamports": None if fee is None else fee.get("perTicketLamports"),
            },
            events_index=index,
            selected_tier=tier_id,
            pooled=pool,
            decision_mode=decision_mode,
            fixture_sha=self.ledger.build_hash(),
            chain=self._chain_payload(event_id, tier_id, recommendations[tier_id], to_iso(cut)),
            sim=sim.run() if show_sim else [],
            canonical_url="",
            # The before-on-sale mode withholds this event's own rows from the features. The rows
            # are still in the store, so the page may not print them as absent ones: what the
            # mode excluded is measured here, at the same cut, from the same store, and travels
            # beside the zero that enters the decision.
            excluded=_excluded_own_counts(tickets, ledger, event_id, cut) if not own_rows else None,
        )
        payload["modelVersion"] = MODEL_VERSION
        payload["provenance"] = {
            "nullSlotRows": guidance.county(
                features["provenance"]["nullSlotRows"],
                features["event"]["sales"],
                features["event"]["atCeiling"],
                int(pool["eventsWithResale"]),
                "A9",
            ),
            "rowsConsidered": guidance.county(
                features["provenance"]["rowsConsidered"],
                features["event"]["sales"],
                features["event"]["atCeiling"],
                int(pool["eventsWithResale"]),
                "A9",
            ),
            "rowsAfterCut": guidance.county(
                features["provenance"]["rowsAfterCut"],
                features["event"]["sales"],
                features["event"]["atCeiling"],
                int(pool["eventsWithResale"]),
                "A9",
            ),
            "slotFallback": features["provenance"]["slotFallback"],
        }
        return payload

    def _chain_payload(self, event_id: str, tier_id: str, recommendation: dict, as_of: str) -> dict:
        """The last block on the page: verified, or explicitly absent. Never a third state."""
        quote = chain_client.quote_commit(
            quote_id=chain_client.quote_id_for(event_id=event_id, tier_id=tier_id, as_of=as_of),
            recommendation={
                "eventId": event_id,
                "tierId": tier_id,
                "recommendedLamports": recommendation.get("recommendedLamports"),
                "asOf": as_of,
            },
            mint=None,
            model_version=MODEL_VERSION,
        )
        artefact = chain_client.load_artefact(DEVNET_ARTEFACT_PATH)
        chain = {
            "state": artefact["state"],
            "reason": artefact.get("reason", "devnet_absent"),
            "programStatus": self.rpc.program_status(),
            "quoteId": quote["quoteId"],
            "quoteHash": quote["quoteHash"],
            "memoText": quote["memoText"],
            "available": chain_client.available(),
            "memoProgram": chain_client.MEMO_PROGRAM_ID,
        }
        if artefact["state"] == "verified" and artefact.get("quoteHash") == quote["quoteHash"]:
            chain.update(
                {
                    "signature": artefact["signature"],
                    "slot": artefact["slot"],
                    "blockTime": artefact["blockTime"],
                    "cluster": artefact["cluster"],
                }
            )
        elif artefact["state"] == "verified":
            # the file verified, but against a different quote than the one on screen
            chain["state"] = "unverified"
            chain["reason"] = "quote_hash_mismatch"
        return chain

    def _rejection_error(self, rejection: dict) -> ApiError:
        """The loader's typed reason, rendered as the page's refusal for that event."""
        return ApiError(
            422,
            labels.render(rejection["labelId"], **rejection.get("fields", {})),
            rejection["code"],
        )

    def _parse_query_instant(self, raw: str) -> datetime:
        try:
            return parse(raw)
        except Exception as exc:  # noqa: BLE001 - any parse failure is the same 400
            raise bad_request(f"asOf is not an ISO-8601 timestamp: {raw!r}", "as_of_invalid") from exc

    def _parse_cap(self, raw: str | int | None) -> int | None:
        if raw in (None, ""):
            return None  # no candidate cap: the recorded cap is what the record carries
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise bad_request(f"capBps must be an integer number of basis points, got {raw!r}", "cap_invalid") from exc
        if not 0 <= value <= MAX_CAP_BPS:
            raise bad_request(f"capBps must be between 0 and {MAX_CAP_BPS}, got {value}", "cap_invalid")
        return value

    def _parse_fee(self, raw: str | int | None) -> dict | None:
        if raw in (None, ""):
            return None  # no fee model configured: the net line is withheld
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise bad_request(f"feeLamports must be an integer, got {raw!r}", "fee_invalid") from exc
        if value < 0:
            raise bad_request("feeLamports cannot be negative", "fee_invalid")
        if value > MAX_FEE_LAMPORTS:
            raise bad_request(
                f"feeLamports must be at most {MAX_FEE_LAMPORTS}, got {value}", "fee_invalid"
            )
        return {"perTicketLamports": value, "adValoremBps": 0}

    def _parse_mode(self, raw: str | None) -> str:
        """The decision instant. The default is the hindsight recomputation, and it is labelled."""
        if raw in (None, ""):
            return "counterfactual"
        value = str(raw).strip().lower().replace("-", "_")
        if value not in DECISION_MODES:
            raise bad_request(
                f"mode must be one of {', '.join(DECISION_MODES)}, got {raw!r}", "mode_invalid"
            )
        return value

    def _parse_tau(self, raw: str | float | None) -> float:
        if raw in (None, ""):
            return 0.20
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise bad_request(f"tau must be a number, got {raw!r}", "tau_invalid") from exc
        if not TAU_MIN <= value <= TAU_MAX:
            raise bad_request(f"tau must be between {TAU_MIN} and {TAU_MAX}, got {value}", "tau_invalid")
        return value

    # -- the pricing seam, and the one guarantee it owns ------------------

    def engine_model(self, request: dict) -> dict:
        """The console's engine, exposed through the seam, with the same refusals.

        Two shapes for one engine is a cost, and it is paid once here so `/health` cannot
        say "no pricing model" while the console is pricing. `expectedResaleLamports` is
        the recommendation only when the regime supports a point: on a binding event there
        is no point estimate, so it is null rather than a floor dressed as one.
        """
        payload = self.price_guidance(
            event_id=request.get("eventId"), tier_id=request.get("tierId"), as_of=request.get("asOf")
        )
        tier = next((row for row in payload["tiers"] if row.get("selected")), None)
        recommended = tier["recommendation"]["recommendedLamports"] if tier else None
        value = recommended["value"] if isinstance(recommended, dict) else None
        return {
            "modelVersion": MODEL_VERSION,
            "asOf": payload["asOf"],
            "expectedResaleLamports": value,
            "saleProbability": None,
            "saleProbabilityReason": "not_identified",
            "recommendedPrimaryLamports": value,
            "horizonHours": None,
            "basis": (tier["band"]["labelId"] if tier else "no_resale_record"),
        }

    # -- the pricing seam, not exposed by the contract --------------------

    def price_estimate(self, request: dict) -> dict:
        """Route an engine question to the model seam, whatever is registered behind it.

        In the running server that is the console's engine, a rule-based bounded estimator
        with no fitted model; instantiated bare (as `tools/guidance.py` does) the seam has
        nothing registered and answers `available: false` with a reason and no number.
        """
        enriched = dict(request)
        enriched.setdefault("asOf", to_iso(self.now()))
        return self.pricing_model.estimate(enriched)
