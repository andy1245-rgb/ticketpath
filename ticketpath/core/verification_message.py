"""The verification message, rebuilt byte for byte.

`API_CONTRACT.md` freezes this: the frontend has the wallet sign
`verificationMessage()` from `lib/solana.ts`, and the backend must reproduce the
same bytes or every in-flight nonce is invalid. Five lines, `\\n` joined, no
trailing newline. The cluster comes from configuration because a signature made
against "devnet" cannot verify against "mainnet-beta".

tests/test_verification_message.py pins the exact bytes, including the empty line
and the absence of a trailing newline.
"""

from __future__ import annotations

CLUSTERS = ("devnet", "testnet", "mainnet-beta", "localnet")


def build(wallet: str, nonce: str, cluster: str) -> str:
    """The exact UTF-8 string the wallet signs."""
    return "\n".join(
        (
            "Verify wallet ownership for ticket issuance.",
            "",
            f"Wallet: {wallet}",
            f"Nonce: {nonce}",
            f"Cluster: {cluster}",
        )
    )


def build_bytes(wallet: str, nonce: str, cluster: str) -> bytes:
    """The same message as UTF-8 bytes, which is what the verifier consumes."""
    return build(wallet, nonce, cluster).encode("utf-8")
