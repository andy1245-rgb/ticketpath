"""The only path to a Solana RPC. Read-only, disabled by default, honest when on.

This adapter never opens a socket, on any flag. What it *can* do is tell the console whether
someone asked for a live read, and it says so rather than pretending a check happened.

**The flag meant to enable a re-read, and why it enables nothing on its own.** Three
environment variables are read through `from_env`:

    TICKETPATH_RPC_ENABLED=1                 # off unless this is exactly "1"
    TICKETPATH_RPC_URL=https://api.devnet.solana.com
    TICKETPATH_PROGRAM_ID=<program id>       # the cap-check program the artefact names

With all three set, `transfer_enforcement` says `not_queried` instead of `rpc_disabled`, and
`program_status` reports the configured id. **It still does not read the chain.** The console's
`[DEVNET]` slot is rendered from `records/devnet-artefacts.json`, which
`tools/devnet_publish.py` wrote after reading the memo back at the slot it reports: that is
*recorded, not independently re-read*, and it is the safe default on a demo laptop. Turning
these three on is what a live re-read would need and is not that re-read; building it is not
part of this build. The page says so itself: it reads "a live re-read is not implemented in
this build" where it used to tell a reader to set `TICKETPATH_RPC_ENABLED=1`, which promised
a mechanism no code here has (feature 2 review, critical finding).

`program_status` keeps three claims apart, because they have three different sources and
only one of them is a read:

  * `programId` is the id this adapter was **configured** with, or None;
  * `recorded` is the program a **verified artefact file** names, labelled as recorded;
  * `askedCluster` is false and `programDeployed` is false because this build **asked
    nothing**, not because there is no program. A `false` here means "not read", and a
    caller that renders it as "absent from the cluster" is misquoting it.

`Ticket.transferRestricted` in the contract is defined as whether the restriction
is *actually enforced on-chain right now*, not whether the event config asks for
it, so this adapter returns false with a reason. The artefact says what is on chain; this
adapter says what it has read, which is nothing.
"""

from __future__ import annotations

import os
from typing import Mapping

DISABLED = "rpc_disabled"
NO_PROGRAM_ID = "no_program_id_configured"
NOT_QUERIED = "not_queried"


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
        elif not self.rpc_url:
            reason = NO_PROGRAM_ID
            detail = "no RPC url is configured, so there is nothing to query"
        else:
            reason = NOT_QUERIED
            detail = (
                "a program id and an RPC url are configured, but this build opens no socket: "
                "the recorded artefact is the only chain evidence, not a live read"
            )
        return {
            "mintAddress": mint_address,
            "enforced": False,
            "checked": False,
            "reason": reason,
            "detail": detail,
            "cluster": self.cluster,
        }

    def program_status(self, recorded: Mapping | None = None) -> dict:
        """What this adapter was told, what a file records, and what it asked. Three answers.

        `programDeployed` stays false because this adapter does not ask the cluster and did
        not read a deployment. That is not pessimism and it is not a statement about devnet:
        it is the boundary. `askedCluster` says the same thing in the positive, so a reader
        cannot read the `false` as "no program is deployed".

        `recorded`, when a caller has one, is the block a *verified* artefact file carries,
        passed in by the caller that loaded it: this adapter never opens a file. It is
        labelled with its source, so a recorded id can never be mistaken for a read one.
        """
        return {
            "programDeployed": False,
            "askedCluster": False,
            "rpcEnabled": self.enabled,
            "programId": self.program_id,
            "cluster": self.cluster,
            "reason": DISABLED if not self.enabled else NOT_QUERIED,
            "detail": (
                "this server asked no cluster, so it reports no deployment; a program id here "
                "was configured or recorded, and neither is a read"
            ),
            "designDoc": "docs/ON-CHAIN-DESIGN.md",
            "recorded": dict(recorded) if recorded else None,
        }
