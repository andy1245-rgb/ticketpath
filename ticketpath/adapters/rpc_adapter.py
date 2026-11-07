"""The only path to a Solana RPC. Read-only, disabled by default, honest when on.

There is no program deployed, no mint and no cluster account that belongs to this
project, so the adapter's answer today is a structured "no program deployed"
rather than a number. It never opens a socket: `enabled` only decides whether the
answer says "not checked" or "checked, nothing there", and even that second state
is unreachable in this build because there is no program id to check against.

`Ticket.transferRestricted` in the contract is defined as whether the restriction
is *actually enforced on-chain right now*, not whether the event config asks for
it. Until a program is deployed the only true answer is false, and that is what
this adapter returns.
"""

from __future__ import annotations

import os

NOT_DEPLOYED = "no_program_deployed"
DISABLED = "rpc_disabled"
NO_PROGRAM_ID = "no_program_id_configured"


class RpcAdapter:
    """Read-only chain queries. Every method returns a dict that says what was checked."""

    def __init__(self, enabled: bool, rpc_url: str | None, program_id: str | None, cluster: str):
        self.enabled = enabled
        self.rpc_url = rpc_url
        self.program_id = program_id
        self.cluster = cluster

    @classmethod
    def from_env(cls, cluster: str) -> "RpcAdapter":
        """Off unless TICKETPATH_RPC_ENABLED is exactly "1". No network at import time."""
        enabled = os.environ.get("TICKETPATH_RPC_ENABLED", "").strip() == "1"
        return cls(
            enabled=enabled,
            rpc_url=os.environ.get("TICKETPATH_RPC_URL") or None,
            program_id=os.environ.get("TICKETPATH_PROGRAM_ID") or None,
            cluster=cluster,
        )

    def transfer_enforcement(self, mint_address: str) -> dict:
        """Whether transfers of this mint are actually restricted on-chain right now."""
        if not self.enabled:
            reason = DISABLED
            detail = "the RPC adapter is disabled; nothing about the chain was read"
        elif not self.program_id:
            reason = NO_PROGRAM_ID
            detail = "no program id is configured, so there is nothing to query"
        else:
            reason = NOT_DEPLOYED
            detail = "no transfer-hook program is deployed by this project on any cluster"
        return {
            "mintAddress": mint_address,
            "enforced": False,
            "checked": False,
            "reason": reason,
            "detail": detail,
            "cluster": self.cluster,
        }

    def program_status(self) -> dict:
        """Small status block for /health. Never claims a deployment."""
        return {
            "programDeployed": False,
            "rpcEnabled": self.enabled,
            "programId": None,
            "cluster": self.cluster,
            "reason": DISABLED if not self.enabled else NOT_DEPLOYED,
            "designDoc": "docs/ON-CHAIN-FOR-LAPTOP.md",
        }
