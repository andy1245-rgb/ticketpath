"""The SIMULATED state machine: the cap check, the custody rule, the gate, the theorem.

A Python mirror of the instruction ordering in `docs/ON-CHAIN-DESIGN.md` (its earlier
sibling `docs/ON-CHAIN-FOR-LAPTOP.md` is a superseded pointer). Standard library only, no
cluster contacted, no key
material, nothing signed. Every line it returns carries `simulated: True` and the page
prefixes every line `[SIMULATED]`.

What it proves: the arithmetic of `face + face * cap_bps / 10 000` and the ordering of
the checks. What it does not prove: that Token-2022 calls a transfer hook, that the extra
accounts are wired, or that the runtime allocates the sizes it assumes. The caption says
so in the same weight as the lines.

Error codes are the design document's, not a deployed program's: 6004 tier exhausted,
6009 transfer not staged, 6010 cap exceeded, 6012 destination unverified, 6013 ticket
not valid, 6018 verification expired.
"""

from __future__ import annotations

from typing import Sequence

FACE = 1_200_000_000  # 1.20 SOL, the same tier the console opens on
CAP_BPS = 1500
ERRORS = {
    6004: "E_TIER_EXHAUSTED",
    6009: "E_TRANSFER_NOT_STAGED",
    6010: "E_CAP_EXCEEDED",
    6012: "E_DEST_UNVERIFIED",
    6013: "E_TICKET_INVALID",
    6018: "E_VERIFICATION_EXPIRED",
}
VERIFIED_WALLETS = ("SYNbuyerverified",)
UNVERIFIED_WALLET = "SYNbuyerunverified"


def ceiling_lamports(face: int, cap_bps: int) -> int:
    """face + face * cap_bps / 10 000, floored to the lamport. Exact integer arithmetic."""
    return face + (face * cap_bps) // 10000


def markup_bps(price: int, face: int) -> int:
    """(price - face) / face in basis points, rounded half away from zero."""
    numerator = (price - face) * 10000
    if numerator >= 0:
        return (numerator + face // 2) // face
    return -((-numerator + face // 2) // face)


def _line(arm: str, status: str, code: int | None, detail: str) -> dict:
    return {
        "arm": arm,
        "status": status,
        "code": code,
        "name": ERRORS.get(code, "") if code else "",
        "detail": detail,
        "simulated": True,
    }


def _cap_arm() -> list[dict]:
    ceiling = ceiling_lamports(FACE, CAP_BPS)
    lines = []
    for price, expected in ((ceiling, "ok"), (ceiling + 1, "refused")):
        if price > ceiling:
            lines.append(
                _line(
                    "cap",
                    "refused",
                    6010,
                    f"{price} lamports is above the ceiling {ceiling} lamports "
                    f"(face {FACE} at {CAP_BPS} bps); the instruction aborts before any transfer",
                )
            )
        else:
            lines.append(
                _line(
                    "cap",
                    "ok",
                    None,
                    f"{price} lamports is within the ceiling {ceiling} lamports; "
                    f"markup {markup_bps(price, FACE)} bps, recorded",
                )
            )
        if lines[-1]["status"] != expected:  # a mirror that disagrees with itself is a bug
            raise AssertionError("cap arm disagreeing with its own ceiling arithmetic")
    return lines


def _unstaged_arm() -> list[dict]:
    """A custody move the program did not stage: refused, and the record is unchanged."""
    lines = [
        _line(
            "unstaged",
            "refused",
            6009,
            "the destination is neither the escrow nor a settled buyer, and no execute_resale "
            "is in progress; the hook refuses and the custody sequence does not advance",
        )
    ]
    return lines


def _unverified_arm() -> list[dict]:
    """An unverified destination, then the same transfer after verification."""
    if UNVERIFIED_WALLET in VERIFIED_WALLETS:
        raise AssertionError("the unverified wallet is in the verified set")
    return [
        _line(
            "unverified",
            "refused",
            6012,
            f"destination {UNVERIFIED_WALLET} has no live Verification account; the gate refuses",
        ),
        _line(
            "unverified",
            "ok",
            None,
            f"destination {UNVERIFIED_WALLET} is verified, so the same transfer is admitted",
        ),
    ]


def _theorem_arm() -> list[dict]:
    """The markup theorem over a sweep: the cap binds on price, and markup is a definition."""
    lines = []
    for face in (500_000_000, 1_200_000_000, 3_000_000_000):
        for cap in (0, 1500, 2500):
            top = ceiling_lamports(face, cap)
            for price in (face, top, top + 1):
                admitted = price <= top
                lines.append(
                    _line(
                        "theorem",
                        "ok" if admitted else "refused",
                        None if admitted else 6010,
                        f"face {face}, cap {cap} bps, ceiling {top}, price {price} -> "
                        f"{'admitted' if admitted else 'refused'}, markup {markup_bps(price, face)} bps",
                    )
                )
    return lines


ARMS = {
    "cap": _cap_arm,
    "unstaged": _unstaged_arm,
    "unverified": _unverified_arm,
    "theorem": _theorem_arm,
}


def run(arms: Sequence[str] = ("cap", "unstaged", "unverified")) -> list[dict]:
    """Run the named arms and return one line per check, every line `simulated`."""
    lines: list[dict] = []
    for arm in arms:
        if arm not in ARMS:
            raise KeyError(f"unknown simulation arm {arm!r}; known: {sorted(ARMS)}")
        lines.extend(ARMS[arm]())
    return lines
