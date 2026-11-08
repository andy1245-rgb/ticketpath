"""`python3 -m market_swarm <verb>`: the package's entry point, one line of wiring.

The verbs live in `market_swarm/cli.py`; this file exists only so the entry point the
contract names (`python3 -m market_swarm <verb>`) resolves. Nothing is imported from
`ticketpath/` and nothing here opens a socket.
"""

from .cli import main

raise SystemExit(main())
