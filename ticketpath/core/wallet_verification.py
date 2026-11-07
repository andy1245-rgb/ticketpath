"""Nonce lifecycle and the WalletVerification payload, over injected state and clock.

Pure by construction: the state dict and `now` are passed in, so a test can drive
expiry without sleeping and the server owns the only clock. Nothing here touches
a wallet, a chain or a network: the signature check is passed in as `verifier`,
which in production is `ticketpath.core.ed25519.verify`.

State is held in memory by the orchestrator. It is lost when the server stops,
which is why every response's `dataSource` says so.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from ticketpath.core import base58, ed25519, verification_message
from ticketpath.core.timeutil import to_iso

NONCE_TTL_SECONDS = 300
METHOD = "wallet_signature"
FLAG_UNVERIFIED = "wallet_not_verified"


class WalletAddressError(ValueError):
    """The string is not a 32-byte base58 public key."""


class VerificationError(ValueError):
    """A nonce or signature was refused. Carries a machine-readable reason."""

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason


def normalise_wallet(text: str) -> str:
    """Validate a base58 32-byte public key and return it trimmed."""
    wallet = (text or "").strip()
    if not wallet:
        raise WalletAddressError("wallet is required")
    if not base58.looks_like_base58(wallet):
        raise WalletAddressError("wallet is not base58")
    try:
        raw = base58.decode(wallet)
    except base58.Base58Error as exc:
        raise WalletAddressError(str(exc)) from exc
    if len(raw) != 32:
        raise WalletAddressError(f"wallet must decode to 32 bytes, got {len(raw)}")
    return wallet


def empty_state() -> dict:
    """A fresh, empty verification store."""
    return {"challenges": {}, "verified": {}}


def issue_challenge(
    state: dict,
    wallet: str,
    now: datetime,
    ttl_seconds: int = NONCE_TTL_SECONDS,
    nonce_factory: Callable[[], str] | None = None,
) -> dict:
    """Mint one single-use nonce for a wallet and return the contract's reply."""
    factory = nonce_factory or (lambda: secrets.token_hex(16))
    nonce = factory()
    expires_at = now + timedelta(seconds=ttl_seconds)
    state["challenges"][nonce] = {
        "wallet": wallet,
        "expiresAt": expires_at.astimezone(timezone.utc),
        "used": False,
    }
    # Drop anything that has already expired so the dict cannot grow without end.
    for candidate in list(state["challenges"]):
        record = state["challenges"][candidate]
        if record["expiresAt"] <= now.astimezone(timezone.utc):
            state["challenges"].pop(candidate, None)
    return {
        "nonce": nonce,
        "expiresAt": to_iso(expires_at),
    }


def complete(
    state: dict,
    wallet: str,
    nonce: str,
    signature_base58: str,
    now: datetime,
    cluster: str,
    verifier: Callable[[bytes, bytes, bytes], bool] = ed25519.verify,
) -> dict:
    """Verify one signed nonce and return the wallet's verification view.

    The nonce is consumed on any attempt, successful or not, so a captured
    signature cannot be replayed.
    """
    record = state["challenges"].pop(nonce, None)
    if record is None:
        raise VerificationError("unknown or already used nonce", "nonce_unknown")
    if record["wallet"] != wallet:
        raise VerificationError("nonce was issued to a different wallet", "nonce_wallet_mismatch")
    if record["expiresAt"] <= now.astimezone(timezone.utc):
        raise VerificationError("nonce expired, request a new challenge", "nonce_expired")
    try:
        signature = base58.decode(signature_base58)
    except base58.Base58Error as exc:
        raise VerificationError(f"signature is not base58: {exc}", "signature_malformed") from exc
    if len(signature) != 64:
        raise VerificationError(
            f"signature must be 64 bytes, got {len(signature)}", "signature_malformed"
        )
    message = verification_message.build_bytes(wallet, nonce, cluster)
    if not verifier(base58.decode(wallet), signature, message):
        raise VerificationError("signature does not match the message and wallet", "signature_invalid")
    state["verified"][wallet] = {
        "verifiedAt": to_iso(now),
        "method": METHOD,
    }
    return view(state, wallet)


def view(state: dict, wallet: str) -> dict:
    """Contract WalletVerification. An unknown wallet is unverified, not an error."""
    record = state["verified"].get(wallet)
    if record is None:
        return {
            "wallet": wallet,
            "verified": False,
            "verifiedAt": None,
            "method": None,
            "canPurchase": False,
            "canReceiveTransfer": False,
            "flags": [FLAG_UNVERIFIED],
        }
    return {
        "wallet": wallet,
        "verified": True,
        "verifiedAt": record["verifiedAt"],
        "method": record["method"],
        "canPurchase": True,
        "canReceiveTransfer": True,
        # The contract defines `flags` as reasons a capability is false, so a
        # verified wallet has none. That this state is only in memory is said in
        # the payload's dataSource.note, which is where a reader looks for it.
        "flags": [],
    }
