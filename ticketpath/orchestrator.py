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
from typing import Callable, Mapping

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
DEVNET_ARTEFACT_NAME = "records/devnet-artefacts.json"
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

    The same count is kept per tier, because the market block is scoped to one tier and its
    `0 sales of 0 on this event` was the event-scoped fact printed in a tier-scoped sentence:
    the two zeros are the mode's, and the rows that produce them are in this tier (11-final,
    item 5). The per-tier counts are read off the same ticket rows, so the tier figure can
    never disagree with the tier's own `sales` count about which rows exist.

    `resalesInStore` is the same count with no cut: whether this event's record holds a priced
    sale at any instant. It separates "no resale yet" from "no resale at all", which are two
    different statements about the record and were one sentence on the cold-start page
    (12-final-audit section 4.2).
    """
    tier_of = {ticket["id"]: ticket["tierId"] for ticket in tickets if ticket["eventId"] == event_id}
    own = set(tier_of)
    rows = [row for row in ledger if row["ticketId"] in own]
    at_cut = [row for row in rows if parse(row["occurredAt"]) <= cut]
    by_tier: dict[str, dict[str, int]] = {}
    for row in at_cut:
        if row["kind"] != "sale" or row["priceLamports"] is None:
            continue
        bucket = by_tier.setdefault(tier_of[row["ticketId"]], {"resales": 0})
        bucket["resales"] += 1
    priced = [row for row in rows if row["kind"] == "sale" and row["priceLamports"] is not None]
    return {
        "resales": sum(1 for row in at_cut if row["kind"] == "sale" and row["priceLamports"] is not None),
        "tickets": len({row["ticketId"] for row in at_cut if row["kind"] == "issue"}),
        "resalesInStore": len(priced),
        "byTier": by_tier,
    }


# The record states a decision instant can have, as measured from the store at that instant.
# The mode sentence is chosen from this vocabulary, so no page describes a record the event
# does not have at the instant it is printed for (12-final-audit, property (d)).
RECORD_STATES: tuple[str, ...] = (
    "before_first_ticket",   # no issue row at or before the instant: nothing to read yet
    "issued_no_resale",      # tickets issued, no priced sale at the instant, and none later
    "issued_no_resale_yet",  # tickets issued, no priced sale at the instant, but one later
    "in_market",             # priced sales at the instant, the run has not ended
    "ended_no_resale",       # the run has ended and holds no priced sale at the instant
    "ended_no_ticket",       # the run has ended and no ticket was ever issued at the instant
    "ended_with_resales",    # the run has ended with priced sales on the record
    "cancelled",             # the store's own status says the event was called off
)


def _record_state(event, own: dict, cut: datetime) -> str:
    """Which record the decision instant actually has, from the store's rows at the cut.

    `own` is `_excluded_own_counts` for this event, measured whether or not the mode reads it,
    so the state is a fact about the store and not about the decision mode. The dates decide
    "has ended at this instant", not the status field: the schema carries no instant at which a
    status changed, so a store that still says `on_sale` for an event past its end is finished
    as of the cut (the page says the field and the instant disagree), and a store that says
    `completed` for an event still inside its dates is not finished yet (the page says the
    field is the store's current one). `cancelled` is the one status that decides the sentence
    on its own, because a cancelled run will not produce a completed record at any instant.
    """
    status = event.get("status")
    if status == "cancelled":
        return "cancelled"
    ends_at = event.get("endsAt") or event.get("startsAt")
    try:
        ended = bool(ends_at) and parse(ends_at) <= cut
    except (TypeError, ValueError):
        ended = False
    resales = own.get("resales") or 0
    tickets = own.get("tickets") or 0
    if ended and resales:
        return "ended_with_resales"
    if ended and tickets:
        return "ended_no_resale"
    if ended:
        return "ended_no_ticket"
    if resales:
        return "in_market"
    if tickets:
        return "issued_no_resale_yet" if own.get("resalesInStore") else "issued_no_resale"
    return "before_first_ticket"


def _memo_program_or_none(cluster: str) -> str | None:
    """The memo program id for this server's cluster, or None when the table has no measurement.

    A server can be pointed at any cluster in `server.CLUSTERS`, and a payload field that
    raised on one of them would be a page that cannot render. None is the honest answer and
    the console can say so; a nearby cluster's id would be a lie the page cannot detect.

    This has to be asked before the commitment is built, not after: `quote_commit` resolves the
    same table and raises `UnknownCluster` itself, so a payload that called it first would die
    here having never reached this answer. The `memo_program` argument on `quote_commit` is the
    resolved value this function returned, including the None.
    """
    try:
        return chain_client.memo_program_id(cluster)
    except chain_client.UnknownCluster:
        return None


def _recorded_program(artefact: Mapping, source: str) -> dict | None:
    """The program a *verified* artefact records, labelled with the file it came from.

    This is the one place the payload turns an artefact into a program claim, so the page and
    `/health` cannot disagree about which id was recorded. It carries no deployment claim:
    the adapter that reports it asked no cluster (feature 2, part 3).

    `source` is the path this server actually read. It used to be `DEVNET_ARTEFACT_NAME`, a
    constant, so a verified copy at another path claimed to be the operator's file.
    """
    if artefact.get("state") != "verified" or not artefact.get("programId"):
        return None
    return {
        "programId": artefact["programId"],
        "cluster": artefact.get("cluster"),
        "mint": artefact.get("mint"),
        "source": source,
        "checkedAt": artefact.get("checkedAt"),
        "checkerVersion": artefact.get("checkerVersion"),
    }


# The fields of `load_artefact`'s verified block that the console payload carries. Named once,
# so a field added to the file cannot reach the page by accident, and a field the console
# promised cannot silently disappear from the payload.
RECORDED_FIELDS = (
    "asOf",
    "eventId",
    "tierId",
    "modelVersion",
    "recommendedLamports",
    "signature",
    "slot",
    "blockTime",
    "cluster",
    "mint",
    "programId",
    "memoProgram",
    "memoText",
    "quoteId",
    "quoteHash",
    "checkedAt",
    "checkerVersion",
    "explorer",
    "transfers",
    # The two the page could not show while they were absent from this tuple: the file's own
    # cap and face, which put the resale ceiling below its own recommendation on the shipped
    # record (feature 2 review, the recorded-parameters finding).
    "capBps",
    "faceLamports",
)

# The recorded fields that are numbers, and so reach a payload as a badged wrapper rather
# than as a bare int: `guidance.num` is the only shape a number may have here.
RECORDED_NUMBERS = ("recommendedLamports", "slot", "blockTime", "capBps", "faceLamports")


def _recorded_block(artefact: Mapping, source: str) -> dict:
    """The file's block, with each number carrying its badge and the file it came from.

    A payload number is a wrapper or it is a defect (tests/test_guidance_api.py walks every
    payload). The verified branch used to leak bare ints, and no test reached them because the
    branch was unreachable: the defect this feature fixes hid its own sibling. The value is
    still the file's; the basis names the file and the field.

    A value that is not the type the grammar names is not rendered: a price that is a string
    or a float, a slot that is text, a signature that is an int and an `error` that is an int
    each used to reach `units.num` and take the page down (feature 2 review).
    """
    recorded = {name: artefact.get(name) for name in RECORDED_FIELDS}
    for name in RECORDED_NUMBERS:
        if chain_client.is_whole(recorded.get(name)):
            recorded[name] = _recorded_number(recorded[name], name, source)
        elif recorded.get(name) is not None:
            recorded[name] = None
    transfers = recorded.get("transfers")
    if transfers:
        recorded["transfers"] = {
            leg: _recorded_transfer_row(row, leg, source)
            for leg, row in transfers.items()
            if isinstance(row, Mapping)
        }
    capacity = _recorded_capacity(artefact, source)
    if capacity is not None:
        recorded["capacity"] = capacity
    return recorded


def _recorded_transfer_row(row: Mapping, leg: str, source: str) -> dict:
    """One leg's fields, each kept only at the type its grammar names.

    An `error` that is not a string is kept as a type name rather than as the value: the page
    has to be able to say the file's value is not one, and the value itself is not a thing it
    may print. A missing `error` key means the file says nothing; `error: null` means the chain
    accepted the transfer, and the two are kept apart.
    """
    out: dict = {}
    for name in ("slot", "blockTime", "priceLamports"):
        value = row.get(name)
        if chain_client.is_whole(value):
            out[name] = _recorded_number(value, f"{leg} {name}", source)
    for name in ("signature", "explorer"):
        value = row.get(name)
        if isinstance(value, str) and value:
            out[name] = value
    if "error" in row:
        error = row["error"]
        if isinstance(error, str):
            out["error"] = error
        elif error is not None:
            out["errorNotAString"] = type(error).__name__
        else:
            out["error"] = None
    return out


def _recorded_capacity(artefact: Mapping, source: str) -> dict | None:
    """The ceiling the file's own face and cap imply, and where its recommendation sits.

    `sim.ceiling_lamports` is the integer ceiling the store and the program both use, so the
    arithmetic is core's. What is new is only the comparison: on the shipped record the file
    states face 1,000,000,000 and cap 2,500, which put the ceiling at 1,250,000,000, while the
    recommendation in the same file is 1,380,000,000. The page printed neither the cap nor the
    face, so it could not show it (feature 2 review).
    """
    face, cap = artefact.get("faceLamports"), artefact.get("capBps")
    if not (chain_client.is_whole(face) and chain_client.is_whole(cap)):
        return None
    if not 0 <= cap <= 10000:
        return None
    ceiling = sim.ceiling_lamports(face, cap)
    recommended = artefact.get("recommendedLamports")
    return {
        "ceilingLamports": guidance.num(
            ceiling,
            "EXACT",
            f"face {face} lamports at cap {cap} bps, both as {source} states them",
            None,
        ),
        "recommendedAboveCeiling": (
            recommended > ceiling if chain_client.is_whole(recommended) else None
        ),
    }


def _recorded_number(value: int, field: str, source: str) -> dict:
    """One recorded number, badged and sourced, and says whether the quote hash covers it.

    The badge is the provenance -- the number came out of the devnet artefact file -- and
    `coveredByQuoteHash` is the assurance, because the six hashed fields do not include the
    slot, the block time, the cap, the face or a transfer price. The page renders the second
    fact (`the file states`) and a payload consumer gets both, so no consumer can render an
    unhashed value as something the file lets it check.
    """
    return guidance.num(
        value,
        "DEVNET",
        f"recorded in {source}, field {field}",
        "A_CHAIN_RECORDED",
        # The file states a cap in basis points, and the page prints the cap it prices
        # against in basis points too, so a reader can compare the two without dividing.
        unit="bps" if field.endswith("capBps") else None,
        covered_by_quote_hash=field in chain_client.CANONICAL_FIELDS,
    )


class Orchestrator:
    """One instance per server process. Holds the adapters and the clock."""

    def __init__(
        self,
        ledger: LedgerAdapter,
        rpc: RpcAdapter,
        pricing_model: PricingModelAdapter,
        cluster: str,
        now: Callable[[], datetime] | None = None,
        artefact_path: str | Path | None = None,
    ):
        self.ledger = ledger
        self.rpc = rpc
        self.pricing_model = pricing_model
        self.cluster = cluster
        # The one file the chain slot reads. A path is a parameter rather than a constant so a
        # test (and `tools/console-check.py`) can point the same server at a tampered copy
        # without touching the operator's proven record.
        self.artefact_path = Path(artefact_path) if artefact_path is not None else DEVNET_ARTEFACT_PATH
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

    def artefact_source(self) -> str:
        """The path this server actually read, for the page and for a wrapper's basis.

        `DEVNET_ARTEFACT_NAME` is a display name for the operator's file, and it was printed
        for whatever path was read: a verified copy at another path claimed to be the
        operator's record (feature 2 review, the source-path finding). The display name is
        used only where the path *is* that file.
        """
        if self.artefact_path == DEVNET_ARTEFACT_PATH:
            return DEVNET_ARTEFACT_NAME
        return str(self.artefact_path)

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
            # The same three facts the console's slot prints: what a verified artefact records,
            # what this server was configured with, and the fact that it asked no cluster. One
            # helper builds both, so /health and the page cannot disagree about the program.
            "chain": self.rpc.program_status(
                recorded=_recorded_program(
                    chain_client.load_artefact(self.artefact_path), self.artefact_source()
                )
            ),
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
            "signature and slot are null because this build reads no chain and records no "
            "transaction for this ticket; it reports no deployment of its own."
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

        own_counts = _excluded_own_counts(tickets, ledger, event_id, cut)
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
            # beside the zero that enters the decision. The same count decides the mode
            # sentence in both modes, so it is measured always, not only when it is printed.
            excluded=own_counts if not own_rows else None,
            # Which record this instant has: no ticket yet, tickets and no resale, resales in a
            # run still open, a run that has ended, or an event the store calls cancelled. The
            # mode sentence is chosen by this, so no page claims a completed record it does not
            # have (12-final-audit, property (d)).
            record_state=_record_state(event, own_counts, cut),
            # The loader's own record of what it would not serve. The served list is what every
            # number above is computed from, so the store's total can only be printed beside it
            # by carrying both (N6, 10-final-review).
            held_back=held_back,
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
        """The last block: the recorded quote and the current one, side by side and never merged.

        Two different facts live here and this method keeps them apart.

        *The current quote* is what this page would commit for `as_of`, computed now. It is
        `quoteId`, `quoteHash` and `memoText`, and it is not on any chain.

        *The recorded quote* is the file's, under `recorded`: its own instant, signature,
        slot, block time, mint, program and the two transfer legs. It is present whenever the
        file verifies, whatever the page's instant is, because a file recorded at 18:34 does
        not stop being on devnet when a reader moves the cut to noon (decision MD2).

        `state` therefore answers exactly one question -- did the artefact verify -- and
        `matchesCurrentQuote` answers the other one: is the number on this page the number the
        chain recorded. Before this split, a page whose instant differed from the recorded one
        had the artifact downgraded to `unverified / quote_hash_mismatch` and rendered as
        absent, so a proven devnet transaction was invisible on every page but one.

        `programStatus` is the adapter's own block: what it was configured with, what the file
        records, and the fact that it asked no cluster. It never claims a deployment.
        """
        # Resolved once, before the commitment and not after it. The table cannot name a
        # program for every cluster the server accepts, and a field that raised on one of
        # them would be a page that cannot render, so the id is looked up here and None is a
        # value the payload and the instruction both carry.
        memo_program = _memo_program_or_none(self.cluster)
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
            cluster=self.cluster,
            memo_program=memo_program,
        )
        source = self.artefact_source()
        artefact = chain_client.load_artefact(self.artefact_path)
        verified = artefact.get("state") == "verified"
        recorded = None
        matches = None
        signatures = 0
        if verified:
            # Every field comes off the file. A field the file does not carry is None and the
            # page prints nothing for it; nothing here falls back to the live recommendation.
            recorded = _recorded_block(artefact, source)
            matches = recorded["quoteHash"] == quote["quoteHash"]
            # Counted by the loader from the file's own grammar, so the evidence strip counts
            # the three signatures the page prints rather than one (feature 2 review).
            signatures = artefact.get("signatureCount") or 0
        return {
            "state": artefact["state"],
            "reason": artefact.get("reason"),
            # The reason's own field, for the sentence the page renders beside it: a file on
            # another cluster is refused *by cluster*, and the page names which one.
            "reasonCluster": artefact.get("cluster"),
            "available": chain_client.available(),
            # The path this server read, so a verified copy cannot be printed as the
            # operator's file.
            "source": source,
            # The quote this page computed for its own instant. Never set from the file.
            "quoteId": quote["quoteId"],
            "quoteHash": quote["quoteHash"],
            "memoText": quote["memoText"],
            # The id for this server's cluster, resolved above from the table rather than
            # assumed. A cluster with no measurement answers null: the payload says nothing
            # is known rather than naming a program the cluster may not host.
            "memoProgram": memo_program,
            # How many signatures the recorded file carries, and therefore what the evidence
            # strip counts. A number in the payload is a wrapper; this one is the strip's own
            # count, built once so the page and the strip cannot disagree about it.
            "signaturesRecorded": guidance.num(
                signatures,
                "DEVNET",
                (
                    f"the quote memo and each transfer leg in {source}: {signatures} "
                    "signatures, counted from a file whose quote hash recomputed"
                    if verified
                    else (
                        "no artefact file is present for this server to read, so no signature "
                        "is counted"
                        if artefact["state"] == "absent"
                        else "the artefact file did not verify, so no signature in it is counted"
                    )
                ),
                (
                    "A_CHAIN_RECORDED"
                    if verified
                    else ("devnet_absent" if artefact["state"] == "absent" else "devnet_unverified")
                ),
            ),
            # What the file records, and whether it is the quote on screen. Both None when
            # there is no verified artefact: an absent file proves nothing about either.
            "recorded": recorded,
            "matchesCurrentQuote": matches,
            "programStatus": self.rpc.program_status(
                recorded=_recorded_program(artefact, source)
            ),
        }

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
