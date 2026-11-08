"""`market_swarm`: a synthetic ticket-trading swarm, separate from `ticketpath`.

This package is its own thing. Nothing in `ticketpath/` imports it and it imports
nothing from `ticketpath/`; the two share a repository and nothing else. It exists to
drive the real `cap_hook` transfer hook on a local validator (or devnet) with agents,
and to write every action into a dataset that is labelled synthetic in every file.

Standard library only, on purpose: the repository has zero runtime dependencies and this
package keeps that. Tests are `unittest`, run from the repository root:

    python3 -m unittest discover -s market_swarm/tests -t .

The submodules are added in waves. This wave has the data plane only: `config` (what a
run is), `budget` (what an agent may spend) and `ledger` (where every action lands).
The chain, agent and runner modules come later and are not imported here.
"""
