# RUN — the console, in one command

```bash
cd <repository root>   # the directory holding ticketpath/, records/, docs/
python3 -m ticketpath.server
```

Then open **http://127.0.0.1:8788/**

Python 3 standard library only. No install, no build step, no JavaScript needed for any
number to appear. Port 8788; 8787 is refused outright because another process owns it.
`TICKETPATH_PORT` overrides.

## The one call that says where the data comes from

```bash
curl -s http://127.0.0.1:8788/health | head -c 400
```

`dataSource.synthetic` is `true`, `chain.programDeployed` is `false`,
`chain.designDoc` is `docs/ON-CHAIN-DESIGN.md`, and `pricingModel.modelVersion` is
`engine-2026-11-07` — the engine the console serves, with `pricingModel.fitted` set to
`false`, because no model was trained.

## Every state has a URL

| State | URL |
|---|---|
| the default: the event whose resale cap binds | `/` |
| the uncapped event, where a band is admissible | `/?event=evt_syn_04` |
| an event with no resales (the cold start) | `/?event=evt_syn_03` |
| a draft event with nothing issued | `/?event=evt_syn_08` |
| before the first sale: every count drops to zero | `/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z` |
| a candidate cap below the recorded prices | `/?event=evt_syn_02&capBps=0` |
| a declared τ at the top of the grid | `/?event=evt_syn_04&tau=0.406` |
| the simulated state machine | `/?sim=1` |

The canonical URL for whatever is on screen is printed under the controls.

## Without a browser

```bash
python3 tools/guidance.py --events
python3 tools/guidance.py --event evt_syn_04 --as-of 2026-11-07T12:00:00Z | head -40
```

## Tests

```bash
python3 -m unittest discover -s tests
```

Standard library only, no network outside an ephemeral-port server; the run prints the count.
The suites that matter for the console are
`tests/test_console_page.py` (badges, banner, no banned sentence), `tests/test_guidance_api.py`
(every number labelled) and `tests/test_console_route.py` (the URL, over a socket).
