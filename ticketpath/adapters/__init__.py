"""The only paths out of this process.

`ledger_adapter` is the sole source of ticket data, `rpc_adapter` the sole path to
a Solana RPC (read-only, disabled by default, and honest that no program is
deployed), and `pricing_model_adapter` the sole seam a pricing model plugs into.
Nothing in `core` imports anything from here.
"""
