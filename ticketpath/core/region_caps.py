"""The region-aware resale policy table: deterministic, offline, integer-only.

This module answers one question, and answers it the same way every time:

    given the jurisdictions an event is sold into, and the date the law is being
    checked against, is resale above a limit restricted, unrestricted, or unknown?

It is not a legal opinion and it does not decide which law applies to a cross-border
resale. It reads `ticketpath/data/region-caps.json` — one row per jurisdiction, each
carrying the instrument, its dates, its basis, its penalty and the confidence we have in
it — and returns an immutable `CapPolicy`.

Four properties are the reason this is a module and not a prompt:

1. **No network, no clock.** `on_date` is a parameter. `resolve()` cannot consult the
   internet, the system clock or a model.
2. **Announced is not law.** `instrument_kind` has `announced_policy` as a first-class
   value and `status` has `announced`; neither is ever binding.
3. **Strictest wins.** A multi-venue event is capped if any of its binding jurisdictions
   caps, and unresolved if any of them is unresolved. A tour cannot be shown lawful on
   the strength of its easiest stop.
4. **Integers all the way down.** Basis points and lamports are integers, and the one
   conversion (a fixed statutory amount into lamports) is exact rational arithmetic with
   a floor, chosen because a floor makes the cap stricter than the statute, never looser.

`records/REGION-CAPS-DESIGN.md` is the design this file implements; `§` references below
point into it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_TABLE_PATH = Path(__file__).resolve().parents[1] / "data" / "region-caps.json"

BPS_DENOM = 10_000
U16_MAX = 65_535

#: The three outcomes. `unresolved` is not a synonym for `monitored`: it says we could not
#: establish the law from a primary source, and an event carrying it may not claim lawfulness.
POLICIES = ("capped", "monitored", "unresolved")

INSTRUMENT_KINDS = (
    "primary_legislation",
    "secondary_legislation",
    "regulator_guidance",
    "announced_policy",
    "none_identified",
)
STATUSES = ("in_force", "announced", "not_in_force", "repealed", "unknown")
APPLIES_TO = (
    "all_resale",
    "designated_events",
    "enumerated_events",
    "primary_sale",
    "bots_only",
    "disclosure_only",
    "none",
    "unknown",
)
CAP_BASES = (
    "face",
    "face_plus_fees",
    "face_plus_fees_capped",
    "pct_above_face",
    "absolute",
    "margin_absolute",
    "no_price_cap",
    "unknown",
)
BASES = ("face", "face_plus_fees", "face_plus_fees_capped")

#: How tight a base is when two candidates tie on basis points at a zero fee. A cap over the
#: face admits less than a cap over face + fees, and a fee-capped base sits between them. The
#: lamport decision is `effective_ceiling`'s, with the real face and fee; this ordering exists
#: so `resolve()` never picks a rule that is looser merely because its number looks smaller.
BASE_TIGHTNESS = {"face": 0, "face_plus_fees_capped": 1, "face_plus_fees": 2}
CONFIDENCES = ("A", "B", "C", "D", "E")

#: `GB-EAW`, `AU-NSW`, `CA-ON`, `US-CA`, or a bare `IE`. Uppercase by construction.
CODE_RE = re.compile(r"^[A-Z]{2}(-[A-Z0-9]{1,3})?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.\d+$")

# Machine-readable reasons. A screen can branch on these without parsing prose.
REASON_LAW_CAPS = "law_caps_bps"
REASON_NO_CAP = "no_cap_in_force"
REASON_ANNOUNCED_ONLY = "announced_only"
REASON_NOT_YET = "not_yet_in_force"
REASON_REPEALED = "repealed"
REASON_NOT_DESIGNATED = "not_a_designated_event"
REASON_DESIGNATION_UNKNOWN = "designation_not_stated"
REASON_NOT_RESALE = "not_a_resale_rule"
REASON_OTHER_RESTRICTION = "other_restriction_only"
REASON_UNKNOWN_JURISDICTION = "unknown_jurisdiction"
REASON_NO_INSTRUMENT = "no_instrument_identified"
REASON_UNKNOWN_LAW = "law_status_unknown"
REASON_ABSOLUTE_NEEDS_FX = "absolute_needs_fx"
REASON_MIXED = "mixed_strictest_wins"

#: Which single reason a policy reports when several instruments contributed none. The order
#: is by how much the fact tells a reader, not by severity: "a cap exists but this event is not
#: designated" explains more than "there is a disclosure duty", which explains more than "a cap
#: was announced". Unknown law and no-instrument sit last because they are the weakest evidence.
REASON_PRIORITY = (
    REASON_UNKNOWN_JURISDICTION,
    REASON_DESIGNATION_UNKNOWN,
    REASON_NOT_DESIGNATED,
    REASON_OTHER_RESTRICTION,
    REASON_NOT_RESALE,
    REASON_ANNOUNCED_ONLY,
    REASON_NOT_YET,
    REASON_REPEALED,
    REASON_ABSOLUTE_NEEDS_FX,
    REASON_UNKNOWN_LAW,
    REASON_NO_INSTRUMENT,
    REASON_NO_CAP,
    REASON_LAW_CAPS,
    REASON_MIXED,
)


def _best_reason(reasons: Sequence[str]) -> str:
    """The most informative reason, with unknown members sorted last rather than raising."""
    return min(
        reasons,
        key=lambda reason: REASON_PRIORITY.index(reason)
        if reason in REASON_PRIORITY
        else len(REASON_PRIORITY),
    )

ROW_KEYS = (
    "jurisdiction",
    "instrument_kind",
    "citation",
    "url",
    "status",
    "in_force_from",
    "in_force_to",
    "applies_to",
    "cap_basis",
    "cap_value",
    "penalty",
    "enforcement_body",
    "quoted_provision",
    "notes",
    "confidence",
    "retrieved_at",
)
TABLE_KEYS = ("version", "compiled_at", "scope_note", "country_inheritance", "entries")


class TableError(ValueError):
    """The rules table is malformed. Raised at load, never at resolution time."""


@dataclass(frozen=True)
class LegalBasis:
    """One instrument, exactly as the table states it. No field is inferred."""

    jurisdiction: str
    instrument_kind: str
    citation: str
    url: str
    status: str
    in_force_from: str | None
    in_force_to: str | None
    applies_to: str
    cap_basis: str
    cap_value: Mapping[str, Any] | None
    penalty: Mapping[str, Any]
    enforcement_body: str
    quoted_provision: str
    confidence: str
    notes: str
    retrieved_at: str
    stricter_than_law: bool = False

    def as_dict(self) -> dict:
        return {
            "jurisdiction": self.jurisdiction,
            "instrumentKind": self.instrument_kind,
            "citation": self.citation,
            "url": self.url,
            "status": self.status,
            "inForceFrom": self.in_force_from,
            "inForceTo": self.in_force_to,
            "appliesTo": self.applies_to,
            "capBasis": self.cap_basis,
            "capValue": dict(self.cap_value) if self.cap_value else None,
            "penalty": dict(self.penalty),
            "enforcementBody": self.enforcement_body,
            "quotedProvision": self.quoted_provision,
            "confidence": self.confidence,
            "notes": self.notes,
            "retrievedAt": self.retrieved_at,
            "stricterThanLaw": self.stricter_than_law,
        }


@dataclass(frozen=True)
class CapPolicy:
    """The resolved policy for one event. Immutable; safe to stamp and store."""

    kind: str                       # "capped" | "monitored" | "unresolved"
    cap_bps: int | None             # None unless kind == "capped"
    base: str                       # "face" | "face_plus_fees" | "face_plus_fees_capped"
    fee_cap_bps: int | None         # face_plus_fees_capped only: the most of the fee the law counts
    binding_jurisdiction: str | None
    jurisdictions: tuple[str, ...]
    table_version: str
    table_sha256: str
    basis: tuple[LegalBasis, ...]
    reason: str
    as_of: str

    def as_dict(self) -> dict:
        """The additive wire shape (`records/REGION-CAPS-DESIGN.md` §9, §11)."""
        return {
            "resalePolicy": self.kind,
            "resaleCapBps": self.cap_bps,
            "capBasis": self.base,
            "feeCapBps": self.fee_cap_bps,
            "bindingJurisdiction": self.binding_jurisdiction,
            "jurisdictions": list(self.jurisdictions),
            "lawTableVersion": self.table_version,
            "lawTableSha256": self.table_sha256,
            "lawReason": self.reason,
            "lawAsOf": self.as_of,
            "lawBasis": [row.as_dict() for row in self.basis],
        }

    def contract_cap(self) -> int | None:
        """`Event.resalePriceCapBps`: the number only when the policy is a real cap."""
        return self.cap_bps if self.kind == "capped" else None


# -- loading and validation ---------------------------------------------------


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TableError(message)


def _iso(value: Any, field: str, where: str) -> str | None:
    if value is None:
        return None
    _require(isinstance(value, str) and bool(DATE_RE.match(value)), f"{where}: {field} must be YYYY-MM-DD or null, got {value!r}")
    try:
        date.fromisoformat(value)
    except ValueError as exc:  # 2026-02-30 matches the shape and is not a day
        raise TableError(f"{where}: {field} is not a real date: {value!r}") from exc
    return value


def _validate_cap_value(cap_basis: str, cap_value: Any, where: str) -> dict | None:
    """The margin over the base, or the fee cap, or nothing.

    The base and the margin are orthogonal: Western Australia caps at 110% of a base that is
    the face *plus* the original booking fee, so an all-in base can carry a non-zero margin.
    `cap_value: null` means 0 bps over a face-ish base (the common case: Ireland, Ontario,
    Quebec) and is the only spelling allowed for `no_price_cap` and `unknown`.
    """
    if cap_basis == "no_price_cap":
        _require(cap_value is None, f"{where}: cap_value must be null for cap_basis 'no_price_cap'")
        return None
    if cap_basis in ("face", "face_plus_fees"):
        if cap_value is None:
            return None
        _require(isinstance(cap_value, Mapping), f"{where}: cap_value must be null or an object")
        _require(cap_value.get("kind") == "bps", f"{where}: cap_value.kind must be 'bps'")
        bps = cap_value.get("bps")
        _require(isinstance(bps, int) and not isinstance(bps, bool), f"{where}: cap_value.bps must be an int")
        _require(0 <= bps <= U16_MAX, f"{where}: cap_value.bps must be 0..{U16_MAX}, got {bps}")
        return {"kind": "bps", "bps": bps}
    if cap_basis == "pct_above_face":
        _require(isinstance(cap_value, Mapping), f"{where}: pct_above_face needs cap_value")
        _require(cap_value.get("kind") == "bps", f"{where}: cap_value.kind must be 'bps'")
        bps = cap_value.get("bps")
        _require(isinstance(bps, int) and not isinstance(bps, bool), f"{where}: cap_value.bps must be an int")
        _require(0 <= bps <= U16_MAX, f"{where}: cap_value.bps must be 0..{U16_MAX}, got {bps}")
        return {"kind": "bps", "bps": bps}
    if cap_basis == "face_plus_fees_capped":
        _require(isinstance(cap_value, Mapping), f"{where}: face_plus_fees_capped needs cap_value")
        _require(cap_value.get("kind") == "fee_cap_bps", f"{where}: cap_value.kind must be 'fee_cap_bps'")
        bps = cap_value.get("bps")
        _require(isinstance(bps, int) and not isinstance(bps, bool), f"{where}: cap_value.bps must be an int")
        _require(0 <= bps <= BPS_DENOM, f"{where}: cap_value.bps must be 0..{BPS_DENOM}, got {bps}")
        return {"kind": "fee_cap_bps", "bps": bps}
    if cap_basis in ("absolute", "margin_absolute"):
        _require(isinstance(cap_value, Mapping), f"{where}: {cap_basis} needs cap_value")
        _require(cap_value.get("kind") == "minor_units", f"{where}: cap_value.kind must be 'minor_units'")
        amount = cap_value.get("amount")
        currency = cap_value.get("currency")
        _require(isinstance(amount, int) and not isinstance(amount, bool) and amount > 0, f"{where}: cap_value.amount must be a positive int")
        _require(isinstance(currency, str) and re.match(r"^[A-Z]{3}$", currency), f"{where}: cap_value.currency must be ISO-4217")
        return {"kind": "minor_units", "amount": amount, "currency": currency}
    # "unknown" carries whatever the research recorded, and resolves to unresolved.
    _require(cap_value is None or isinstance(cap_value, Mapping), f"{where}: cap_value must be null or an object")
    return dict(cap_value) if cap_value else None


def _row(code: str, raw: Mapping[str, Any]) -> LegalBasis:
    where = f"entry {code}"
    _require(isinstance(raw, Mapping), f"{where}: must be an object")
    missing = [key for key in ROW_KEYS if key not in raw]
    _require(not missing, f"{where}: missing keys {missing}")
    extra = [key for key in raw if key not in ROW_KEYS and key != "stricter_than_law"]
    _require(not extra, f"{where}: unknown keys {extra} (the shape is closed)")
    stricter = raw.get("stricter_than_law", False)
    _require(isinstance(stricter, bool), f"{where}: stricter_than_law must be a boolean")
    _require(raw["jurisdiction"] == code, f"{where}: jurisdiction field {raw['jurisdiction']!r} disagrees with its key")
    _require(bool(CODE_RE.match(code)), f"{where}: not an ISO-3166 code or subdivision")
    _require(raw["instrument_kind"] in INSTRUMENT_KINDS, f"{where}: instrument_kind {raw['instrument_kind']!r}")
    if raw["instrument_kind"] == "announced_policy":
        # "Announced is not law" is a cross-field rule, not a convention. An announced policy
        # cannot be in force, and no edit to `status` alone can make it bind.
        _require(
            raw["status"] in ("announced", "not_in_force"),
            f"{where}: an announced_policy row cannot have status {raw['status']!r}",
        )
    _require(raw["status"] in STATUSES, f"{where}: status {raw['status']!r}")
    _require(raw["applies_to"] in APPLIES_TO, f"{where}: applies_to {raw['applies_to']!r}")
    _require(raw["cap_basis"] in CAP_BASES, f"{where}: cap_basis {raw['cap_basis']!r}")
    _require(raw["confidence"] in CONFIDENCES, f"{where}: confidence {raw['confidence']!r}")
    for field in ("citation", "url", "enforcement_body", "notes", "quoted_provision"):
        _require(isinstance(raw[field], str), f"{where}: {field} must be a string")
    _require(raw["citation"] != "", f"{where}: an entry with no citation is not evidence")
    _require(isinstance(raw["penalty"], Mapping), f"{where}: penalty must be an object")
    _require("kind" in raw["penalty"], f"{where}: penalty.kind is required")
    start = _iso(raw["in_force_from"], "in_force_from", where)
    end = _iso(raw["in_force_to"], "in_force_to", where)
    if start and end:
        _require(start <= end, f"{where}: in_force_from {start} is after in_force_to {end}")
    if raw["status"] == "in_force" and raw["cap_basis"] in ("face", "face_plus_fees", "pct_above_face", "absolute"):
        # A price rule may legitimately have no recorded commencement date: Quebec's cap comes
        # from a 2011 amendment and the row's primary source does not give the day. `null` means
        # "no date recorded, treat as in force for every check date", and the row's notes say so.
        # It never means "not in force": that is what `status` and `in_force_from` on a dated row
        # are for, and `_binding` only skips a row whose dates exclude the check date.
        _require(raw["notes"] != "", f"{where}: an in-force price rule with no commencement date must say so in notes")
    return LegalBasis(
        jurisdiction=code,
        instrument_kind=raw["instrument_kind"],
        citation=raw["citation"],
        url=raw["url"],
        status=raw["status"],
        in_force_from=start,
        in_force_to=end,
        applies_to=raw["applies_to"],
        cap_basis=raw["cap_basis"],
        cap_value=_validate_cap_value(raw["cap_basis"], raw["cap_value"], where),
        penalty=dict(raw["penalty"]),
        enforcement_body=raw["enforcement_body"],
        quoted_provision=raw["quoted_provision"],
        confidence=raw["confidence"],
        notes=raw["notes"],
        retrieved_at=raw["retrieved_at"],
        stricter_than_law=stricter,
    )


@dataclass(frozen=True)
class Table:
    """The parsed rules table.

    A jurisdiction maps to **a tuple of instruments**, not one instrument: the United Kingdom
    has an in-force disclosure law *and* an announced price cap, and a table with one row per
    code would have to throw one of them away. Resolution considers every instrument, and the
    announced one is never binding.
    """

    version: str
    compiled_at: str
    scope_note: str
    country_inheritance: bool
    entries: Mapping[str, tuple[LegalBasis, ...]]
    sha256: str

    def rows_for(self, code: str) -> tuple[LegalBasis, ...]:
        """Exact subdivision first, then the country — but only its all-resale rows.

        Inheritance exists for the case where a country's law genuinely governs the
        subdivision (the UK's Consumer Rights Act extends to Scotland and Northern Ireland;
        the Australian Consumer Law applies in every state). It must NOT let a country's
        sectoral rule (a federal bot ban, a disclosure duty) answer the price question for a
        state nobody read: `US` -> `US-OH` used to return `monitored`, a positive finding of no
        cap in Ohio, on the strength of a federal disclosure rule. So a parent contributes only
        rows whose coverage is `all_resale`; with no such row the subdivision is unknown.
        """
        if not code:
            return ()
        if code in self.entries:
            return self.entries[code]
        country = code.split("-", 1)[0]
        if self.country_inheritance and country != code:
            parent = self.entries.get(country, ())
            return tuple(row for row in parent if row.applies_to == "all_resale")
        return ()


def validate_table(raw: Mapping[str, Any]) -> Table:
    """Validate a parsed table and return it with its canonical hash."""
    _require(isinstance(raw, Mapping), "table must be an object")
    missing = [key for key in TABLE_KEYS if key not in raw]
    _require(not missing, f"table: missing keys {missing}")
    _require(isinstance(raw["entries"], Mapping) and raw["entries"], "table: entries must be a non-empty object")
    version = raw["version"]
    _require(isinstance(version, str) and bool(VERSION_RE.match(version)), f"table: version must be YYYY-MM-DD.N, got {version!r}")
    _require(isinstance(raw["compiled_at"], str) and raw["compiled_at"], "table: compiled_at must be a non-empty string")
    if DATE_RE.match(raw["compiled_at"]):
        date.fromisoformat(raw["compiled_at"])
    _require(isinstance(raw["scope_note"], str) and raw["scope_note"], "table: scope_note must be a non-empty string")
    _require(isinstance(raw["country_inheritance"], bool), "table: country_inheritance must be a boolean")
    entries: dict[str, tuple[LegalBasis, ...]] = {}
    for code, rows in raw["entries"].items():
        _require(isinstance(rows, list) and rows, f"entry {code}: must be a non-empty list of instruments")
        entries[code] = tuple(_row(code, row) for row in rows)
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return Table(
        version=version,
        compiled_at=raw["compiled_at"],
        scope_note=raw["scope_note"],
        country_inheritance=raw["country_inheritance"],
        entries=entries,
        sha256=digest,
    )


def load_table(path: str | Path | None = None) -> Table:
    target = Path(path) if path is not None else DEFAULT_TABLE_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TableError(f"rules table not found: {target}") from exc
    except json.JSONDecodeError as exc:
        raise TableError(f"rules table is not valid JSON: {target}: {exc}") from exc
    return validate_table(raw)


# -- resolution ---------------------------------------------------------------


def normalise(jurisdiction: str) -> str:
    """`ie ` -> `IE`, `au-nsw` -> `AU-NSW`. Anything else is returned stripped and uppercased."""
    return (jurisdiction or "").strip().upper()


def _parse_on_date(on_date: str | date) -> str:
    text = on_date.isoformat() if isinstance(on_date, date) else str(on_date).strip()
    if not DATE_RE.match(text):
        raise ValueError(f"on_date must be YYYY-MM-DD, got {on_date!r}")
    date.fromisoformat(text)
    return text


def _binding(row: LegalBasis, on_date: str) -> tuple[bool, str | None]:
    """(is_binding_for_this_date, reason_it_is_not)."""
    if row.confidence in ("D", "E"):
        # A secondary source, or a page nobody read, cannot justify a refusal. The finding says
        # so; making it structural means a later table edit cannot break the rule.
        return False, REASON_UNKNOWN_LAW
    if row.status != "in_force":
        return False, {
            "announced": REASON_ANNOUNCED_ONLY,
            "not_in_force": REASON_NOT_YET,
            "repealed": REASON_REPEALED,
            "unknown": REASON_UNKNOWN_LAW,
        }.get(row.status, REASON_UNKNOWN_LAW)
    if row.in_force_from and on_date < row.in_force_from:
        return False, REASON_NOT_YET
    if row.in_force_to and on_date > row.in_force_to:
        return False, REASON_REPEALED
    return True, None


def _candidate(row: LegalBasis) -> tuple[int | None, str]:
    """Turn a binding row into `(cap_bps or None, base)`, or raise for an unrepresentable rule."""
    if row.cap_basis == "no_price_cap":
        return None, "face"
    if row.cap_basis == "face":
        return int(row.cap_value["bps"]) if row.cap_value else 0, "face"
    if row.cap_basis == "face_plus_fees":
        return int(row.cap_value["bps"]) if row.cap_value else 0, "face_plus_fees"
    if row.cap_basis == "face_plus_fees_capped":
        # The fee-capped base carries a margin of 0: no jurisdiction read for this table has
        # both a fee cap and a margin, and if one appears it needs its own field rather than a
        # second meaning for cap_value.
        return 0, "face_plus_fees_capped"
    if row.cap_basis == "pct_above_face":
        assert row.cap_value is not None
        return int(row.cap_value["bps"]), "face"
    if row.cap_basis in ("absolute", "margin_absolute"):
        # A fixed amount of money in a currency the chain does not speak: Florida's "$1 over the
        # original seller's price" is a margin, and a fixed ceiling is a ceiling, but neither is
        # a basis-points rule. `to_lamports` can convert one with an explicit FX snapshot; the
        # resolver will not pretend the conversion happened.
        raise _NeedsFx(row)
    raise _UnknownLaw(row)


class _NeedsFx(Exception):
    def __init__(self, row: LegalBasis):
        self.row = row


class _UnknownLaw(Exception):
    def __init__(self, row: LegalBasis):
        self.row = row


def resolve(
    jurisdictions: Sequence[str] | str,
    *,
    on_date: str | date,
    table: Table | None = None,
    declared_event: bool | None = None,
) -> CapPolicy:
    """The one resolution function. See `records/REGION-CAPS-DESIGN.md` §3.

    Deterministic: the same arguments and the same table always give the same answer. A
    caller that wants to sell into an `unresolved` jurisdiction has to acknowledge it in
    its own creation path; this function will not soften its own answer.

    `declared_event` has three states and they are not two. `True` means the operator states
    the event is designated; `False` means the operator states it is not; `None` (the default)
    means nobody has said, and a rule that applies only to designated events then resolves to
    `unresolved`, not to `monitored`. The difference is the whole point: the designation
    registers are not machine-readable here, so "undeclared" is an absence of information,
    and treating it as permission would let an operator opt out of a cap by saying nothing.
    """
    if isinstance(jurisdictions, str):
        jurisdictions = [jurisdictions]
    codes = tuple(normalise(code) for code in jurisdictions if normalise(code))
    as_of = _parse_on_date(on_date)
    active = table or load_table()

    if not codes:
        return CapPolicy(
            kind="unresolved", cap_bps=None, base="face", fee_cap_bps=None,
            binding_jurisdiction=None, jurisdictions=(), table_version=active.version,
            table_sha256=active.sha256, basis=(), reason=REASON_UNKNOWN_JURISDICTION, as_of=as_of,
        )

    basis: list[LegalBasis] = []
    capped: list[tuple[int, str, LegalBasis]] = []
    monitored_rows: list[LegalBasis] = []
    reasons: list[str] = []
    missing = False

    for code in codes:
        rows = active.rows_for(code)
        if not rows:
            missing = True
            reasons.append(REASON_UNKNOWN_JURISDICTION)
            continue
        basis.extend(rows)
        for row in rows:
            if row.instrument_kind == "announced_policy":
                # Skipped whatever its status says: the cross-field rule above should have
                # refused a bad row at load, and this is the belt to that braces.
                reasons.append(REASON_ANNOUNCED_ONLY)
                continue
            if row.instrument_kind == "none_identified":
                # Nothing was located. That is the weakest possible evidence and it must never
                # read as "resale is unrestricted": the policy is unresolved.
                reasons.append(REASON_NO_INSTRUMENT)
                missing = True
                continue
            binding, why_not = _binding(row, as_of)
            if not binding:
                reasons.append(why_not or REASON_UNKNOWN_LAW)
                if why_not == REASON_UNKNOWN_LAW:
                    # An instrument whose status could not be established cannot be counted as
                    # a finding of no cap. Unresolved, not monitored.
                    missing = True
                continue
            if row.cap_basis == "unknown":
                # A law exists and nobody read what it requires. This must come before the
                # designated-events gate: otherwise an unread designated-events cap reads as
                # "no cap in force" for every event the operator has not marked.
                reasons.append(REASON_UNKNOWN_LAW)
                missing = True
                continue
            if row.applies_to == "designated_events":
                if declared_event is None:
                    reasons.append(REASON_DESIGNATION_UNKNOWN)
                    missing = True
                    continue
                if declared_event is False:
                    reasons.append(REASON_NOT_DESIGNATED)
                    continue
            if row.applies_to == "primary_sale":
                reasons.append(REASON_NOT_RESALE)
                continue
            if row.applies_to in ("bots_only", "disclosure_only", "none"):
                reasons.append(REASON_OTHER_RESTRICTION)
                continue
            if row.applies_to == "unknown":
                reasons.append(REASON_UNKNOWN_LAW)
                missing = True
                continue
            try:
                cap_bps, base = _candidate(row)
            except _NeedsFx:
                # A fixed money amount cannot be enforced exactly through a basis-points field
                # over a base that the statute did not fix (§3.7, §5). Say so; do not approximate.
                reasons.append(REASON_ABSOLUTE_NEEDS_FX)
                missing = True
                continue
            except _UnknownLaw:
                reasons.append(REASON_UNKNOWN_LAW)
                missing = True
                continue
            if cap_bps is None:
                monitored_rows.append(row)
            else:
                capped.append((cap_bps, base, row))

    if missing:
        return CapPolicy(
            kind="unresolved", cap_bps=None, base="face", fee_cap_bps=None,
            binding_jurisdiction=None, jurisdictions=codes, table_version=active.version,
            table_sha256=active.sha256,
            basis=tuple(basis),
            reason=_best_reason(reasons) if reasons else REASON_UNKNOWN_LAW,
            as_of=as_of,
        )

    if capped:
        # Basis points are only comparable within one base. At a zero fee every base reduces to
        # the face, so the bps ordering is exact; ties are broken by the tighter base
        # (`BASE_TIGHTNESS`), which holds for every fee, not just zero.
        cap_bps, base, row = min(
            capped, key=lambda item: (item[0], BASE_TIGHTNESS[item[1]], item[2].jurisdiction)
        )
        fee_cap = (
            int(row.cap_value["bps"])
            if base == "face_plus_fees_capped" and row.cap_value is not None
            else None
        )
        reason = REASON_LAW_CAPS if len(capped) == 1 and not monitored_rows else REASON_MIXED
        return CapPolicy(
            kind="capped", cap_bps=cap_bps, base=base, fee_cap_bps=fee_cap,
            binding_jurisdiction=row.jurisdiction, jurisdictions=codes,
            table_version=active.version, table_sha256=active.sha256,
            basis=tuple(basis), reason=reason, as_of=as_of,
        )

    if monitored_rows:
        row = monitored_rows[0]
        return CapPolicy(
            kind="monitored", cap_bps=None, base="face", fee_cap_bps=None,
            binding_jurisdiction=row.jurisdiction, jurisdictions=codes,
            table_version=active.version, table_sha256=active.sha256,
            basis=tuple(basis), reason=REASON_NO_CAP, as_of=as_of,
        )

    # Nothing bound at all: every row was announced, repealed, not yet in force, a bot ban,
    # a disclosure duty, or no instrument was found. Those are different facts and the reason
    # says which; the policy is the same, because none of them is a price cap.
    reason = _best_reason(reasons) if reasons else REASON_NO_CAP
    return CapPolicy(
        kind="monitored", cap_bps=None, base="face", fee_cap_bps=None,
        binding_jurisdiction=None, jurisdictions=codes, table_version=active.version,
        table_sha256=active.sha256, basis=tuple(basis), reason=reason, as_of=as_of,
    )


# -- arithmetic ---------------------------------------------------------------


def cap_base_lamports(face_lamports: int, fee_lamports: int | None, policy: CapPolicy) -> int:
    """The number the cap multiplies (§4).

    A `face` policy uses the tier face. A `face_plus_fees` policy needs the documented fee,
    and refuses to guess it: the base is exactly `face + fee` in lamports.
    """
    if isinstance(face_lamports, bool) or not isinstance(face_lamports, int) or face_lamports <= 0:
        raise ValueError(f"face_lamports must be a positive integer, got {face_lamports!r}")
    if policy.base == "face":
        return face_lamports
    if fee_lamports is not None and (
        isinstance(fee_lamports, bool) or not isinstance(fee_lamports, int) or fee_lamports < 0
    ):
        raise ValueError(f"fee_lamports must be a non-negative integer, got {fee_lamports!r}")
    fee = fee_lamports or 0
    if policy.base == "face_plus_fees":
        # No recorded fee means the base is the face, which makes the ceiling STRICTER than
        # the law rather than looser. The event record says whether the fee was known.
        return face_lamports + fee
    if policy.base == "face_plus_fees_capped":
        if policy.fee_cap_bps is None:
            raise ValueError("face_plus_fees_capped policy carries no fee_cap_bps")
        # NSW: the base is face plus the fees the first purchaser actually paid, but the law
        # counts at most 10% of face of them. `min` here is the statute's own limit.
        counted = min(fee, face_lamports * policy.fee_cap_bps // BPS_DENOM)
        return face_lamports + counted
    raise ValueError(f"unknown cap base {policy.base!r}")


def max_price_lamports(base_lamports: int, cap_bps: int) -> int:
    """floor(base * (10000 + cap) / 10000). Display only; `admits` never divides."""
    if isinstance(base_lamports, bool) or not isinstance(base_lamports, int) or base_lamports < 0:
        raise ValueError(f"base_lamports must be a non-negative integer, got {base_lamports!r}")
    if isinstance(cap_bps, bool) or not isinstance(cap_bps, int) or not 0 <= cap_bps <= U16_MAX:
        raise ValueError(f"cap_bps must be an integer 0..{U16_MAX}, got {cap_bps!r}")
    return base_lamports * (BPS_DENOM + cap_bps) // BPS_DENOM


def admits(base_lamports: int, cap_bps: int, price_lamports: int) -> bool:
    """The on-chain predicate, off chain, exactly: `p * 10_000 <= base * (10_000 + cap)`."""
    for name, value in (("base_lamports", base_lamports), ("price_lamports", price_lamports)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
    if isinstance(cap_bps, bool) or not isinstance(cap_bps, int) or not 0 <= cap_bps <= U16_MAX:
        raise ValueError(f"cap_bps must be an integer 0..{U16_MAX}, got {cap_bps!r}")
    return price_lamports * BPS_DENOM <= base_lamports * (BPS_DENOM + cap_bps)


def to_lamports(amount_minor: int, fx: Mapping[str, Any]) -> int:
    """A fixed statutory amount in minor units -> lamports, exactly, floored (§5).

    `fx` is `{base, quote, num, den, source, as_of}` where `num/den` is lamports per minor
    unit of `base` and `quote` must be the platform's unit, `LAMPORTS`. Floor division is
    deliberate: the resulting cap is never above the statutory amount.
    """
    if isinstance(amount_minor, bool) or not isinstance(amount_minor, int) or amount_minor <= 0:
        raise ValueError(f"amount_minor must be a positive integer, got {amount_minor!r}")
    required = ("base", "quote", "num", "den", "source", "as_of")
    missing = [key for key in required if key not in fx]
    if missing:
        raise ValueError(f"fx snapshot is missing {missing}")
    if fx["quote"] != "LAMPORTS":
        raise ValueError(f"fx.quote must be 'LAMPORTS', got {fx['quote']!r}")
    num, den = fx["num"], fx["den"]
    for name, value in (("num", num), ("den", den)):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"fx.{name} must be a positive integer, got {value!r}")
    return amount_minor * num // den


# -- comparison over time -----------------------------------------------------


def compare(issued: CapPolicy, current: CapPolicy) -> str:
    """How the law moved for an already-issued ticket (§6).

    `unchanged`, `tightened`, `relaxed` or `relabelled`. `tighten_allows` on chain accepts
    `tightened`; `relaxed` is refused there by design and recorded off chain instead.
    """
    def rank(policy: CapPolicy) -> tuple[int, int]:
        if policy.kind == "capped":
            assert policy.cap_bps is not None
            return (0, policy.cap_bps)
        return (1, 0)

    if issued.kind == "capped" and current.kind == "capped" and issued.base != current.base:
        # Same kind, different base: the labels `tightened`/`relaxed` cannot carry it, and
        # calling it `unchanged` would silently keep the looser ceiling.
        return "changed_base"

    old, new = rank(issued), rank(current)
    if issued.kind == "capped" and current.kind == "capped":
        assert issued.cap_bps is not None and current.cap_bps is not None
        if current.cap_bps < issued.cap_bps:
            return "tightened"
        if current.cap_bps > issued.cap_bps:
            return "relaxed"
        return "unchanged"
    if old[0] > new[0]:
        return "tightened"
    if old[0] < new[0]:
        return "relaxed"
    return "unchanged" if issued.kind == current.kind else "relabelled"


def describe(policy: CapPolicy) -> dict:
    """One-paragraph, plain-English rendering for a screen or a CLI line."""
    where = policy.binding_jurisdiction or ",".join(policy.jurisdictions) or "no jurisdiction"
    if policy.kind == "capped":
        basis = policy.base.replace("_", " ")
        return (
            f"capped at {policy.cap_bps} bps over the {basis} ({where}); "
            f"table {policy.table_version}, checked {policy.as_of}"
        )
    if policy.kind == "monitored":
        return (
            f"monitored: no resale price cap in force ({where}, {policy.reason}); "
            f"table {policy.table_version}, checked {policy.as_of}"
        )
    return (
        f"unresolved: the law could not be established ({where}, {policy.reason}); "
        f"table {policy.table_version}, checked {policy.as_of}"
    )


def jurisdictions(table: Table | None = None) -> dict[str, str]:
    """`{code: status}` for a listing, so a caller never types a code it cannot resolve.

    A code with more than one instrument reports the strongest status present, so a listing
    never hides an in-force instrument behind an announced one.
    """
    active = table or load_table()
    order = ("in_force", "announced", "not_in_force", "unknown", "repealed")
    return {
        code: min((row.status for row in rows), key=order.index)
        for code, rows in sorted(active.entries.items())
    }


def iter_rows(table: Table | None = None) -> Iterable[LegalBasis]:
    active = table or load_table()
    for code in sorted(active.entries):
        yield from active.entries[code]


# -- the enforced ceiling: law and platform policy, the stricter of the two ---------------


@dataclass(frozen=True)
class EffectiveCeiling:
    """What the chain should hold for one event, and which rule produced it.

    The law and the platform can both cap, in different bases (Ontario's cap is over the
    total price paid; a platform's own demo cap is over the tier face). The chain holds one
    `base` and one `cap_bps`, so the two have to be combined in **price space**, not by
    comparing basis points. The result is always the stricter ceiling, and `binding_rule`
    says which rule produced it so a screen never attributes a product decision to a law.
    """

    base_lamports: int
    cap_bps: int
    ceiling_lamports: int
    binding_rule: str          # "law" | "platform"
    law_policy: CapPolicy
    platform_cap_bps: int | None

    def as_dict(self) -> dict:
        return {
            "enforcedBaseLamports": self.base_lamports,
            "enforcedCapBps": self.cap_bps,
            "enforcedCeilingLamports": self.ceiling_lamports,
            "bindingRule": self.binding_rule,
            "platformCapBps": self.platform_cap_bps,
        }


def effective_ceiling(
    *,
    face_lamports: int,
    fee_lamports: int | None = None,
    law: CapPolicy,
    platform_cap_bps: int | None = None,
) -> EffectiveCeiling | None:
    """Combine the law's cap and the platform's own cap, in lamports, strictly.

    - Both capped: the lower ceiling wins, and `binding_rule` names it.
    - Law capped, no platform cap: the law's.
    - Law monitored or unresolved, platform capped: the platform's, and `binding_rule` says
      `platform`, because the ceiling is a product decision and not a legal one.
    - Neither: `None`, which means "no ceiling to put on chain".

    The chosen ceiling is the winning rule's own ceiling, carried as that rule's own `base`
    and `cap_bps`. It is never re-derived from the ceiling in lamports: re-deriving a basis
    point from an already-floored ceiling loses up to a basis point of the base, which would
    make the chain stricter than the rule the operator was told applied. The one place a
    conversion is unavoidable is a fixed statutory amount, and that path never reaches the
    chain (`resolve` returns `unresolved` for it).
    """
    if platform_cap_bps is not None and (
        isinstance(platform_cap_bps, bool)
        or not isinstance(platform_cap_bps, int)
        or not 0 <= platform_cap_bps <= U16_MAX
    ):
        raise ValueError(f"platform_cap_bps must be an integer 0..{U16_MAX}, got {platform_cap_bps!r}")

    law_base = cap_base_lamports(face_lamports, fee_lamports, law) if law.kind == "capped" else None
    law_ceiling = (
        max_price_lamports(law_base, law.cap_bps)
        if law_base is not None and law.cap_bps is not None
        else None
    )
    platform_ceiling = (
        max_price_lamports(face_lamports, platform_cap_bps) if platform_cap_bps is not None else None
    )

    if law_ceiling is None and platform_ceiling is None:
        return None
    if law_ceiling is not None and platform_ceiling is None:
        base, cap_bps, rule = law_base, int(law.cap_bps), "law"
    elif platform_ceiling is not None and law_ceiling is None:
        base, cap_bps, rule = face_lamports, platform_cap_bps, "platform"
    elif law_ceiling <= platform_ceiling:
        base, cap_bps, rule = law_base, int(law.cap_bps), "law"
    else:
        base, cap_bps, rule = face_lamports, platform_cap_bps, "platform"

    assert base is not None and base > 0 and cap_bps is not None
    admitted = max_price_lamports(base, cap_bps)
    return EffectiveCeiling(
        base_lamports=base,
        cap_bps=cap_bps,
        ceiling_lamports=admitted,
        binding_rule=rule,
        law_policy=law,
        platform_cap_bps=platform_cap_bps,
    )
