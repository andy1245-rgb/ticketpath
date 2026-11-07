"""Request validation and response serialisation, one module per contract area.

Handlers take the orchestrator plus already-parsed query or body values, validate
them against the contract's allowed values, call the orchestrator, and return
(status, payload). They contain no arithmetic and no data access.
"""
