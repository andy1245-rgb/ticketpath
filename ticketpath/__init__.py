"""ticketpath: a primary-market pricing engine fed by a resale record.

Package layout, one job per file:
  server.py       HTTP entry, routing only
  api/            request validation and response serialisation per contract area
  core/           pure functions: no network, no chain, no clock except an injected now()
  adapters/       the only paths to ledger data, Solana RPC and the pricing model
  orchestrator.py routes a request to adapters and core, and does not calculate
"""

__version__ = "0.1.0"
