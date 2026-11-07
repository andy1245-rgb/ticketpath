"""The on-chain piece, as far as it exists on this machine: a simulated state machine.

`sim.py` is executable and tested. There is no program, no mint and no key material in
this package, and `adapters/chain_client.py` is the honest stub: it builds a quote
commitment and never signs or sends it.
"""
