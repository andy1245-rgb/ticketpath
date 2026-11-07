"""GET /health — the liveness and honesty surface.

Three things a reader has to be able to get from this one response: the server is
up, where the data comes from and whether it is synthetic, and whether the chain
and the pricing model are real yet. All three are answered from adapters, not
from constants in this file.
"""

from __future__ import annotations


def health(
    orchestrator,
    endpoints_implemented: int,
    endpoints_in_contract: int,
    routes_implemented: int,
) -> tuple[int, dict]:
    return 200, orchestrator.health(endpoints_implemented, endpoints_in_contract, routes_implemented)
