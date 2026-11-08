"""The two machine-readable surfaces beside the console: `/guidance.json` and `/devnet-record.json`.

Neither is a contract endpoint. `API_CONTRACT.md` lists nine, the frontend's own client
calls those, and `/health` is the tenth route in `ROUTES`; these two are served outside
the route table for the same reason the console at `/` is. They exist because a page is
not a thing a program can read: an operator building a panel needs the refusals and the
recorded devnet artefact as data, and a second implementation of either would be a second
thing to keep true.

`/guidance.json` is a projection of the console payload, not a second computation. The
refusal sentences come from `ticketpath.console.blocks.refusal_lines`, the function the
page itself wraps in `<li>` markup, so a page and this document cannot say different
things about the same refusal. `/devnet-record.json` goes through
`Orchestrator.devnet_record`, so the console's chain slot and this document read one file
through one loader.
"""

from __future__ import annotations

from typing import Mapping

from ticketpath.console import blocks
from ticketpath.console.units import value_of

GUIDANCE_SOURCE = "the console payload, computed by ticketpath.orchestrator.price_guidance"


def guidance_document(payload: Mapping, canonical_url: str) -> dict:
    """The refusals a page can print, their count, and the state they were computed for.

    `count` is the length of the list beside it rather than a number written down: the
    voice that says "an upper bound, a sale probability and four more" is only true for a
    state whose count is six, and a reader who is about to film needs the number the
    server actually printed.
    """
    event = payload["event"]
    tier = blocks.selected_tier(payload)
    refusals = [
        {"code": line.code, "labelId": line.label_id, "sentence": line.sentence}
        for line in blocks.refusal_lines(payload)
    ]
    return {
        "source": GUIDANCE_SOURCE,
        "asOf": payload["asOf"],
        "event": {
            "id": event["id"],
            "name": event["name"],
            "slug": event.get("slug"),
            "capBps": value_of(event.get("capBps")),
        },
        "tier": None if tier is None else {"id": tier["tierId"], "name": tier["name"]},
        "refusals": refusals,
        "count": len(refusals),
        "canonicalUrl": canonical_url,
    }
