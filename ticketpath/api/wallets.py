"""The three wallet-verification routes.

An unknown wallet is 200 with `verified: false`, because any wallet may connect.
A malformed wallet string, a missing body field, a bad nonce or a bad signature
is 400 with a `message`, which is what the contract asks for.
"""

from __future__ import annotations


def get_verification(orchestrator, wallet: str) -> tuple[int, dict]:
    """WalletVerification. Unknown wallets are unverified, not 404."""
    return 200, orchestrator.wallet_verification(wallet)


def start_challenge(orchestrator, wallet: str) -> tuple[int, dict]:
    """{nonce, expiresAt}. The nonce is single use and expires in five minutes."""
    return 200, orchestrator.start_verification(wallet)


def complete_verification(orchestrator, wallet: str, body: dict) -> tuple[int, dict]:
    """Body {nonce, signature}. Signature is base58 of a 64-byte detached Ed25519 sig."""
    return 200, orchestrator.complete_verification(wallet, body)
