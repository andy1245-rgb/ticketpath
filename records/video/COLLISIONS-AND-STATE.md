# Collisions and tree state at the start of the video run

**Written:** 2026-11-08T07:40Z, at the start of the video-design run, before any
script was drafted. Read-only measurements on this machine; nothing here is
recalled.

This file exists because a video script is a set of claims about a build, and the
build was moving while the script was written. Anything below that turns out to be
stale by recording time is a fact the choreography has to absorb, not a defect in
the plan.

## 1. Two sessions are building in the same directory

Measured from the fleet board at 07:30Z, and from `git status --porcelain` in the
repository root: a feature-build session holds `programs/cap_hook/src/*`,
`ticketpath/onchain/`, `ticketpath/adapters/chain_client.py`, `tools/doc_check.py`,
`tools/swarm_charts.py`, `docs/charts/` and `market_swarm/forge_policy.py`; a
second session holds `programs/region_gate/`, `ticketpath/core/region_caps.py` and
the region law sources. The board names `ticketPricing` at phase `verify`, with
four criticals under repair at 07:30Z.

**Consequence for the video:** no screen may be described as final until a capture
of it exists. The choreography therefore names, for every shot, the state the
screen must be in at capture time and how to tell at a glance that it is in that
state, rather than trusting that today's build is tomorrow's build.

## 2. The frontend is mid-rebuild, and its pages do not currently typecheck against their own components

`../ticketing-frontend` has a single commit, `0208765 baseline: untouched tree
before the SeatPass rebuild`, and the whole rebuild is uncommitted working-tree
state. Measured in the working tree at 07:31Z: `components/PriceHistoryChart.tsx`
exists and `app/events/[eventId]/page.tsx` calls it with props that the component
does not accept.

**Consequence:** the frontend is the intended primary surface of the video, and it
is the least stable surface in the project. Every app shot in the choreography
carries a console-and-charts fallback that shows the same fact from a surface that
is not being edited.

## 3. `/pricing` does not exist in the frontend tree

`records/SUBMISSION-PACK.md` §1 (operator actions, item 1) refers to "the copy's
`/pricing` page" framing at 3,383 px. The rebuilt tree has no `app/pricing/`
route. Either the route is part of the rebuild still to land, or the sentence in
the pack is about a different copy (`../ticketpath-demo`, which the pack names
elsewhere). The pack is not corrected here: it is another session's file and the
operator's call. It is recorded so the choreography does not point a camera at a
route that may not exist.

## 4. The board's operator-decision record is truncated, and one decision is missing

Two `decision` entries were read from the project's board log at 07:08Z. The first
ends mid-sentence at "(6) Feature 10: the…", and there is no item (4) in either
entry. Decisions 1, 2, 3, 5, 7, 8 and 9 are readable in full. **Decision 4 and the
rest of decision 6 are not readable by this run**, so nothing here depends on
them; if either is about the video, the operator should restate it.

## 5. The product name changed after the existing script was written

`records/SUBMISSION-PACK.md` §1.2 is a complete, measured, 264-word script. It
names the product "Ticketpath" and ends on "Nothing is deployed". Both are false of
the tree now: the operator decided at 07:08Z that **SeatPass** is the real product
name, and the program is deployed on devnet with the cap boundary proven. The
script is therefore not a draft to polish; it is a document with two false
sentences and a screen list from before the console, the charts and the frontend
rebuild existed. It is cited here for its measurements, not adopted.

## 6. What this machine can and cannot do for capture — measured

- **A headless browser is installed**, outside this repository: Playwright with a
  full Chromium build. A scripted 1280x720 capture was recorded at 07:32Z and
  produced a `.webm` with a real frame.
- **No system `ffmpeg`, no `arecord`, no `sox`, no OBS** on `PATH` (probed at
  07:33Z). The `ffmpeg` that Playwright ships is a stripped build: `--enable-muxer`
  lists `webm` and `image2` only, and `--enable-encoder` lists `libvpx_vp9` and
  `png` only. A `webm`-to-`mp4` copy at 07:35Z failed with "Unable to choose an
  output format".
- **Consequence for the plan, stated plainly:** this machine can produce a silent
  720p/1080p `.webm` of scripted page states, and cannot produce an `.mp4` and
  cannot record a voice. A narrated video has to be recorded on a machine with a
  normal recorder and a microphone, or the narration has to be recorded elsewhere
  and muxed by a toolchain this machine does not have. This is decision **V1** in
  `OPEN-DECISIONS.md`, and it is the operator's, because it depends on his
  hardware.
