# Screenshots for visual review

A headless browser on this box, for looking at pages the way a person sees them:
layout, overflow, clipping, contrast, whether a badge is actually visible.

It is a **dev tool, not a runtime dependency**. The browser lives at
`~/tools/shot/`, outside this repository. Nothing in `tools/shot.py` is imported
by the backend, and no Python or Node package is added to this project. The
backend stays stdlib.

## What is installed

| Piece | Where |
|---|---|
| Playwright (npm package) | `~/tools/shot/node_modules` |
| Chromium headless shell 158 | `~/.cache/ms-playwright/chromium_headless_shell-1254` |
| Full Chromium 158 (optional) | `~/.cache/ms-playwright/chromium-1254` |
| Screenshot tool | `~/tools/shot/shot.mjs` |
| Install record (every package) | `~/tools/shot/INSTALL.log` |

System libraries were installed to satisfy the browser binaries. 24 packages for
the headless shell, 15 more for the full build, all new, none upgraded, none
removed. The exact names and commands are in `INSTALL.log`.

Disk: 21M for `~/tools/shot`, 701M for `~/.cache/ms-playwright` (413M of it the
full Chromium build, which is optional), 232 MiB of system libraries, so 954 MiB
in total. Dropping the full Chromium build would save 413M if space is ever
tight; the headless shell alone is enough for every capture above.

## The wrapper

```bash
python3 tools/shot.py <url> <out.png> [--width N] [--height N] [--full] [--mobile] [--json]
```

Prints the absolute PNG path on stdout.

```bash
mkdir -p ~/shots
python3 tools/shot.py http://127.0.0.1:8788/ ~/shots/console.png
python3 tools/shot.py http://127.0.0.1:8788/ ~/shots/console-full.png --full
python3 tools/shot.py http://127.0.0.1:8788/ ~/shots/console-390.png --mobile --full
python3 tools/shot.py http://127.0.0.1:3001/ ~/shots/frontend.png --width 1280
```

`~/shots` is a scratch directory of your choosing: parent directories are created, and a
capture is scratch output, so it goes outside the repository rather than into it.

| Flag | Meaning |
|---|---|
| `--width N` | viewport width, default 1280 |
| `--height N` | viewport height, default 800 |
| `--full` | capture the whole scrollable page, not just the viewport |
| `--mobile` | 390x844 window with a mobile user agent (overrides `--width`) |
| `--json` | print the tool's JSON report instead of the path |

`--mobile` gives a true 390 CSS px window, so the capture is 390 wide and
narrow-width breakage is visible. It deliberately does not use mobile device
emulation: with emulation, a page that omits `<meta name="viewport">` is laid out
at the 980px default and the capture comes out 980 wide, which hides exactly the
breakage you are looking for. When a page has no viewport meta the tool says so
on stderr, because on a real phone that page renders zoomed out no matter how
good its CSS is. The tool exposes true device emulation as `--device-mobile` if
you want to see what a phone actually shows.

Exit codes:

| Code | Meaning |
|---|---|
| 0 | PNG written |
| 1 | capture failed: page unreachable, browser error, unwritable output |
| 3 | cannot run: node missing, `~/tools/shot/shot.mjs` missing, bad arguments |

Every capture is capped at **30 seconds** by the tool, and the wrapper adds a 45s
subprocess timeout so a wedged browser can never block a review loop.

## The tool directly

`tools/shot.py` is a thin wrapper. The real work is:

```bash
node ~/tools/shot/shot.mjs <url> <out.png> [--width N] [--height N] \
     [--full] [--mobile] [--device-mobile] [--wait ms] [--json] \
     [--channel headless-shell|full]
```

Useful extras the wrapper does not expose:

- `--wait ms` — fixed settle time before the shot (default 600ms).
- `--json` — reports page title, HTTP status, `scrollWidth`, `scrollHeight`,
  whether there is **horizontal overflow**, and the widest offending element,
  plus any page errors. This is the fastest way to catch a layout that breaks
  sideways without looking at the image.
- `--channel full` — use the complete Chromium build instead of the headless
  shell. Slower to start; occasionally renders things the shell does not.

Example, catching sideways overflow in one line:

```bash
node ~/tools/shot/shot.mjs http://127.0.0.1:8788/ ~/shots/c.png --width 390 --full --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['horizontalOverflow'], d['widestElement'])"
```

The tool also freezes CSS animations and transitions and hides the caret, so two
runs of the same page produce comparable images.

## Reading the images

Captures are PNGs; any image reader can view them, and an agent with image input
should read the PNG rather than infer the layout from the HTML. Look for:
horizontal overflow at narrow widths, text clipped at a container edge, contrast
below readable (grey-on-grey, dark-on-dark), badges or counts that should be
visible but are not, and content that pushes a button or link off-screen.

## Servers this is used against

| Port | What |
|---|---|
| 8788 | SeatPass console (default page) |
| 3001 | frontend copy |
| 3002 | second frontend copy, when running |

`:3000` is not to be touched. Neither is `:8787`, nor the `:8788` process itself:
screenshots are read-only HTTP GETs against a page that is already running.

## Reinstalling from scratch

```bash
mkdir -p ~/tools/shot && cd ~/tools/shot
npm i playwright
npx playwright install chromium
# then, if a launch fails on shared libs, find exactly which:
ldd ~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell \
  | grep "not found"
# and install only those, on Ubuntu 24.04:
sudo -n apt-get install -y --no-install-recommends \
  libatk1.0-0t64 libatk-bridge2.0-0t64 libxcomposite1 libxdamage1 libxfixes3 \
  libxrandr2 libgbm1 libasound2t64 libatspi2.0-0t64
```

On 24.04 the package names carrying the `t64` suffix are the correct ones; the
unsuffixed names resolve to nothing.

## First-run observations, 2026-11-07

Two captures taken while proving the tool, recorded here so the numbers are not
lost with the session.

At 1280 the console is clean: title *SeatPass — organizer pricing console*,
no horizontal overflow, no page errors, one centred column about 990px wide.

At 390 both pages overflow horizontally:

| Page | scrollWidth at 390 | Worst offender |
|---|---|---|
| console `:8788` | 586 | `select#event`, 533px wide (a native `<select>` sizes itself to its longest option) |
| frontend `:3001` | 536 | event card `a.group.block`, 520px wide |

Neither page declares a `<meta name="viewport">`. The console's DESIGN table is
also 438px at its narrowest, so it cannot fit 390 without wrapping or scrolling.
