# 15 — visionHelper (`vh.py`): where it is, where it is not, and how to screenshot this box without a browser

Run 2026-11-07 17:35–17:40 UTC on `friend-vm` (`friend@friend-vm`, kernel host name `friend-vm`).
Read only. Nothing committed, no repository file touched. Scratch output went to `/tmp/vh-shim/`.
One unauthenticated `GET /` was sent to `:3000` and `:8787` as part of the port survey (status codes only,
no interaction, no state change); everything else in this record concerns `:8788` and `:3001`.

---

## 1. Bottom line

| question | answer |
|---|---|
| Is `vh.py` on this box? | **No.** Not anywhere on the filesystem. |
| Is the pi skill that wraps it here? | **Yes**, `/home/friend/.pi/profiles/registry/vision-helper/SKILL.md`. |
| Is the `vision` profile here? | **Yes**, in `/home/friend/.pi/profiles/config.json`, but `active` is `default`. |
| Can a screenshot be taken here today? | **No real browser screenshot.** No browser binary, no X display, no Playwright/Puppeteer cache. |
| Is there a working fallback? | **Yes, and it was run end to end.** `sharp` (libvips 8.17.3 + librsvg 2.61.2 + pango) renders a page's text to a legible PNG. |
| Can that PNG be fed to `vh.py`? | **No**, because `vh.py` is absent. That is the whole failure. |

The skill survived the migration. The 24 KB of code it documents did not.

---

## 2. Exact paths

### Present on this box

| path | what | size / mtime |
|---|---|---|
| `/home/friend/.pi/profiles/registry/vision-helper/SKILL.md` | the skill, complete and readable | 9,364 B, 2026-11-06 19:41 |
| `/home/friend/.pi/profiles/config.json` | contains the `vision` profile (model pin, hidden-skill list, `systemPrompt` that names `vh.py`) | 6,040 B, 2026-11-06 19:41 |
| `/home/friend/.pi/agent/auth.json` | the credential file pi and any `vh.py` would read | 639 B, 2026-11-07 16:24 |

### Absent from this box

| path | status |
|---|---|
| `/home/friend/visionHelper/` | `ls: cannot access '/home/friend/visionHelper': No such file or directory` |
| `/home/friend/visionHelper/vh.py` | same |
| `/home/friend/.pi/agent/skills/` | does not exist at all |
| `/home/friend/.agents/` | does not exist at all |
| `/home/friend/.claude/skills/` | exists but holds only `agent-manager`, no vision skill |
| `vh` on `PATH` | absent. `/home/friend/.local/bin` holds exactly three entries, and `vh` is not one of them. |

Searched and found nothing: every top level directory under `/home/friend` (including `tools`, `reports`,
`research`, `emoney`, `loginsw`, `hackathonPrep`, `ticketPricing`, `ticketpath-demo`, `ticketing-frontend`,
his three unrelated tooling trees, `.pi`, `.local`, `.claude`, `.config`, `.cache`, `.npm`, `.nvm`),
plus `/opt`, `/srv`, `/usr/local`, `/usr/bin`, `/usr/local/bin`, `/root`, `/etc/skel`.
`/home/andrew` does not exist, and neither does `/home/friend/mnt` (the dell321 mount is gone).

A literal `find / -name vh.py` could not be run: the bashguard blocks any recursive walk that reaches the
sshfs mount, and it fires on `find` from `/` or from `/home/friend` regardless of `-prune`. Every search
above was therefore scoped to one named directory per command. No `locate`/`plocate` database exists.

---

## 3. Why it is missing, in the record's own words

This is not a mystery and it is not damage. `~/visionHelper` was deliberately left behind by the transfer.

`/home/friend/reports/T2-inventory.md` L179 (the source box inventory):

> `| ~/visionHelper | 3.5 GB (≈1 MB code, vh.py 24 KB) | T* | code yes, sessions/ 3.5 GB no | Backs
> vision-helper skill + the vision profile. **Code has 0 hardcoded paths.** |`

`/home/friend/reports/T5-transfer.md` §9, item 9 lists what was not carried:

> `usage.jsonl`, `visionHelper`, `listenmatch`, `toolInterfacer`, `sync-tools`, `cmdcs`.
> "Not carried, because the manifest did not list them"

So: about 1 MB of code, zero hardcoded paths, and it was skipped only because the manifest did not name it.
The skill, the profile and the credential file all came across; the program they describe did not.

---

## 4. Full usage

### The command that was asked for, and its exact output

```
$ timeout 20 python3 /home/friend/visionHelper/vh.py --help
python3: can't open file '/home/friend/visionHelper/vh.py': [Errno 2] No such file or directory
exit=2
```

There is no `--help` text to quote. `vh.py` cannot be asked for one, because it is not on the disk.

### The usage text that does exist here

Quoted verbatim from `SKILL.md` (the only authoritative usage on this box). Everything below the `---`
marker is the skill's own words:

```
## Usage

```bash
cd /home/friend/visionHelper

# single image (default: handwriting mode, 2 passes)
./vh.py run /path/shot.png -p

# messy page: domain vocabulary biases recognition
./vh.py run shot.png -p --vocab "COMPENG,2DI4,Karnaugh,flip-flop"

# diagram → prose + nodes/edges JSON
./vh.py run diagram.png --mode diagram -p

# bulk, 4 at a time, one session per file, single pass (cheap tier)
./vh.py run ~/Pictures/Screenshots -j 4 --passes 1

# several pages of one document in a single session
# (turn-hungry: prefer -j unless the pages need shared context)
./vh.py run p1.png p2.png p3.png --group -p

# pin one model, or override the fallback chain for one run
./vh.py run shot.png -p --model deepseek/deepseek-v4.1-flash-fast --no-fallback
./vh.py run shot.png -p --fallback-chain google/gemini-3.8-flash

# what is available, what can see images, and what it costs
./vh.py providers

# independent repeats; pairwise CER is the real confidence signal
./vh.py run p.png --runs 2 -p

# watch a screenshot folder (transcribes as files land)
./vh.py watch ~/Pictures/Screenshots --once --existing -p

# score a transcript against ground truth
./vh.py eval --gt truth.txt --pred sessions/<id>/result.txt
```

The skill adds: "Result text lands on stdout with `-p`, in `sessions/<id>/result.txt`, and with `--out FILE`
wherever asked. Everything else — budgets, turn caps, image retention, reasoning level, `--max-dim` — is in
`./vh.py run --help`; do not restate it here."

That last sentence is the one that now points at nothing. `./vh.py run --help` is not available on this box,
so the full flag surface (budgets, turn caps, `--max-dim`, image retention, reasoning level) cannot be
enumerated from here. Only the flags the skill chose to show are known: `run`, `watch`, `eval`, `providers`,
`stats`, `sessions`, `-p`, `-j`, `--group`, `--passes`, `--runs`, `--mode`, `--vocab`, `--model`,
`--no-fallback`, `--fallback-chain`, `--out`, `--max-dim`, `--max-cost`, `--max-turns`.

### The two ways to run it, per the skill

1. Under the `vision` profile: `/profile use vision` inside a session. The profile pins
   `commandcode/deepseek/deepseek-v4.1-flash`, sets `effort: low`, and hides 26 registry skills.
2. From any profile, because the CLI is self contained: `cd /home/friend/visionHelper && ./vh.py run shot.png -p`.

The skill also records that `pi --profile vision` **does not work on pi 1.2.0** (the flag is never
registered, `Error: Unknown option: --profile`). This box runs `@earendil-works/pi-coding-agent@1.2.0`, so
that still applies if the tool is restored.

---

## 5. What it does

`vh.py` is **not** a screenshot tool. It is an image reader. It takes an image that already exists and drives
a vision model over it in a tool loop: crop, zoom, deskew, perspective correction, OpenCV line segmentation,
nested sub-runs. It is built for handwriting, whiteboards, diagrams and dense page screenshots.

- Modes: handwriting (default, survey pass then a targeted review of low-confidence segments),
  `--mode diagram` (prose plus nodes/edges JSON).
- Uncertainty channel in the output: `[illegible]`, `[word?]`, `[margin: ...]`, `~~struck~~`, `^inserted^`.
- It logs per session under `sessions/<id>/` (`events.jsonl`, `stats.json`, `transcript.md`) and rolls up
  cost with `./vh.py stats`.
- It explicitly warns calling agents not to pass base64 image data into their own context.

So the direction of the pipeline matters: **something else has to produce the image**; `vh.py` only reads it.
That is exactly the gap this box has.

---

## 6. Model and credentials

### Models (from the skill and from `config.json`, untested here because the tool is absent)

| path | model | basis |
|---|---|---|
| primary | `commandcode` / `deepseek/deepseek-v4.1-flash` | flat fee plan, $0 marginal |
| fallback 1 | `commandcode` / `deepseek/deepseek-v4-flash-vision-exp` | same |
| fallback 2 | `openrouter` / `google/gemini-3.8-flash` | metered, roughly 10x marginal |

Fallback triggers only on `image_rejected` (400/415/422 complaining about image or modality) or
`empty_output` (two consecutive replies with no tool call and no content). A 429, a timeout or a network
error is a retry, not a fallback.

### Credentials, names only, no values printed

`vh.py` per the skill resolves keys "from pi": credentials come from `~/.pi/agent/auth.json`, model list and
`images` capability from `pi --list-models`. The provider code confirms the search order
(`pi-commandcode-provider/src/api-key.ts`): `~/.commandcode/auth.json`, then `~/.pi/agent/auth.json`, then
`~/.omp/agent/auth.json`.

Keys present in `/home/friend/.pi/agent/auth.json` on this box (names only, values never read out):

| key path | state |
|---|---|
| `commandcode.key` | set |
| `commandcode.type` | set |
| `apiKey` | set (legacy direct form) |
| `anthropic.access` | set |
| `anthropic.refresh` | set |
| `anthropic.expires` | set |

**`openrouter` is absent.** The third fallback (`google/gemini-3.8-flash` on openrouter) has no credential
here, so it would fail even if `vh.py` were restored. Primary and fallback 1 both run on commandcode and are
covered.

Environment variable **names** the commandcode provider honours (read from its source, no values involved):

```
COMMANDCODE_API_BASE
COMMANDCODE_MODELS_URL
COMMANDCODE_MODELS_CACHE
COMMANDCODE_AUTH_TIMEOUT_MS
COMMANDCODE_ZDR
CMD_ZDR
```

No API key env var is used, the key is read from the file above. `/home/friend/.profile` exports
`CLAUDE_CODE_OAUTH_TOKEN` and `NVM_DIR`; neither is a vision credential. `/home/friend/.env` exists and was
not read.

---

## 7. Screenshot capability on this box

### Browsers: none

| probe | result |
|---|---|
| `chromium`, `chromium-browser`, `google-chrome`, `google-chrome-stable`, `chrome`, `firefox`, `firefox-esr` on `PATH` | none found |
| `/snap/bin/*`, `/opt/google`, `/opt/chromium*`, `/opt/firefox*` | no such paths |
| `dpkg -l | grep -iE 'chrom|firefox|wkhtml'` | no packages |
| `headless_shell`, `chrome`, `chromium`, `firefox`, `chrome-linux*` under `.cache`, `.local`, `tools`, `.pi`, `ticketPricing` | none |
| `playwright`, `puppeteer`, `puppeteer-core` in any `node_modules` | none |
| `~/.cache/ms-playwright` | does not exist |
| `DISPLAY` | empty, no `/tmp/.X11-unix`, no `Xvfb`, no `xvfb-run` |
| `wkhtmltoimage`, `wkhtmltopdf`, `cutycapt`, `rsvg-convert`, `convert`, `magick`, `weasyprint` | none installed |

`apt-cache policy` shows both "browsers" are snap transitional wrappers, which need snapd, which is not
present:

```
chromium-browser: Candidate: 2:1snap1-0ubuntu2   (Installed: none)
firefox:          Candidate: 1:1snap1-0ubuntu5   (Installed: none)
```

System libraries a real Chromium would need (14 checked): 3 present (`libnss3.so`, `libdrm.so.2`,
`libxkbcommon.so.0`), **11 missing** (`libatk-1.0`, `libatk-bridge-2.0`, `libcups`, `libXcomposite`,
`libXdamage`, `libXfixes`, `libXrandr`, `libgbm`, `libasound`, `libpango-1.0`, `libcairo`).

### Python: bare

`PIL`, `playwright`, `selenium`, `imgkit`, `html2image`, `weasyprint`, `cairosvg`, `pyppeteer`, `mss`,
`pytesseract` are all `ModuleNotFoundError`. Only `requests 2.31.0` is present.

Worse, there is no way to install any of them right now: `python3 -m pip` reports
`No module named pip`, `python3 -m ensurepip` reports `No module named ensurepip`, and
`python3 -m venv /tmp/venvprobe` fails with *"You may need to use sudo with that command. After installing
the python3-venv package"*. `uv` is absent (T5 recorded this too).

### Node: this is where the rasteriser is

`node v24.22.2`, `npm 11.19.1`. Global packages are only `@anthropic-ai/claude-code`, `npm`, `corepack`, and
`@earendil-works/pi-coding-agent`. But **`sharp` is installed inside the two frontend checkouts**:
`/home/friend/ticketing-frontend/node_modules/sharp` and `/home/friend/ticketpath-demo/node_modules/sharp`.

`sharp 0.34.5` bundles a complete rendering stack and reports it itself:

```
libvips 8.17.3, rsvg 2.61.2, pango 1.57.0, cairo 1.18.4, fontconfig 2.17.1,
harfbuzz 12.1.0, freetype 2.14.1, glib 2.86.1, png 1.6.50, webp 1.6.0
```

That is SVG to PNG with real text shaping, no browser required. Verified directly: a 400x100 SVG containing
`ABCDEF` rasterised with 1,544 dark pixels, so the glyphs are actually drawn and not a blank rectangle.

Fonts exist even though fontconfig's command line tools do not: `/usr/share/fonts/truetype/dejavu/` holds 8
faces (`DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`, `DejaVuSansMono*.ttf`, `DejaVuSerif*.ttf`). `fc-list`,
`fc-match` and `fc-cache` are all absent binaries, and `fc-list` therefore prints nothing, but sharp's
bundled fontconfig reads the directory and finds them. This is a trap worth knowing: "fc-list is empty" here
does **not** mean "no fonts".

### Can it be installed?

The brief assumed a browser might need sudo. **It does not.** `sudo -n -l` on this box reports
`(ALL : ALL) ALL` for `friend`, so sudo is passwordless and `sudo -n apt-get install` would run unattended.
Network egress is open (`pypi.org` 200, `github.com` 200).

So the honest blocker is not capability, it is **authorisation**. Installing a browser is a change to the
machine plus a ~170 MB download, and that is the operator's call, not mine.

Practical routes, if he says yes:

- `cd /home/friend/ticketing-frontend && npm i -D playwright && npx playwright install chromium`
  then `sudo -n npx playwright install-deps chromium` for the 11 missing libraries.
  Gives real pixel screenshots including CSS layout, charts, canvas and images.
- `sudo -n apt-get install -y wkhtmltopdf` (candidate `0.12.6-2build2`, a real deb, not a snap wrapper).
  Older engine, but adequate for a text-heavy console page and much smaller than Chromium.
- Restoring `~/visionHelper` from the source box (about 1 MB of code, 0 hardcoded paths per T2) needs no
  sudo at all.

---

## 8. How to screenshot `:8788` and `:3001` and feed it to `vh.py`

### What is actually running

```
LISTEN 127.0.0.1:8788  python3          -> GET / = HTTP 200, 13,726 B, <title>Ticketpath — organizer pricing console</title>
LISTEN *:3001          next-server      -> GET / = HTTP 200, 118,917 B, <title>Events</title>
LISTEN 0.0.0.0:3000    next-server      (not touched beyond a status code)
LISTEN 127.0.0.1:8787  MainThread       (not touched beyond a status code)
```

### The intended chain, once `vh.py` exists

```bash
# 1. image of :8788 (with a real browser)
npx playwright screenshot --viewport-size=1440,900 --full-page \
    http://127.0.0.1:8788/ /tmp/vh-shim/8788.png

# 2. read it
cd /home/friend/visionHelper && ./vh.py run /tmp/vh-shim/8788.png -p --passes 1 \
    --vocab "capBps,feeLamports,lamports,resale,tier,asOf,ISO-8601,tau,decision mode,counterfactual"
```

`--passes 1` and a `--vocab` are the right shape for a UI screenshot: it is printed text, not handwriting, so
the default survey-plus-review pass buys nothing. The vocab list is the page's own field names, which are
exactly the tokens a vision model mangles.

### The same chain with `:3001`

```bash
npx playwright screenshot --viewport-size=1440,900 --full-page \
    http://127.0.0.1:3001/ /tmp/vh-shim/3001.png
cd /home/friend/visionHelper && ./vh.py run /tmp/vh-shim/3001.png -p --passes 1
```

`:3001` is the frontend copy (title `Events`, 118,917 B of HTML), so it is heavier on layout and iconography
and would benefit more from a real browser than `:8788` does. `:8788` is a mostly textual console, which is
why the text render below reads it almost completely.

### The chain that actually works on this box today

No browser, so the renderer is `sharp` + `pango`. Script at `/tmp/vh-shim/texrender.py`, rasteriser at
`/tmp/vh-shim/_raster.js`. It fetches the URL with `urllib`, strips `script`/`style`/`head`/`svg`, treats
block tags and inline tags as line separators, unescapes entities, collapses whitespace, wraps to the pixel
width using DejaVu Sans Mono's 0.60209 em advance, emits an SVG, and hands that SVG to `sharp`.

```bash
python3 /tmp/vh-shim/texrender.py http://127.0.0.1:8788/ /tmp/vh-shim/8788-live.png \
    --width 1240 --font 15 --title "Ticketpath organizer pricing console - 127.0.0.1:8788"
```

Two things it needs that are easy to get wrong: `NODE_PATH=/home/friend/ticketing-frontend/node_modules` so
`require('sharp')` resolves from a script living in `/tmp` (Node resolves from the script's directory, not
the cwd), and `density: 96` in sharp, which rasterises the SVG at 96/72 = 1.333x, so a 1240-unit wide SVG
comes out 1653 px wide. That upscale is what makes 15 px text legible to a vision model.

### Feeding it to `vh.py`

```bash
cd /home/friend/visionHelper && ./vh.py run /tmp/vh-shim/8788-live.png -p --passes 1
```

That is the exact command. It cannot run here:

```
$ timeout 20 python3 /home/friend/visionHelper/vh.py run /tmp/vh-shim/8788-live.png -p --passes 1
python3: can't open file '/home/friend/visionHelper/vh.py': [Errno 2] No such file or directory
```

The PNG is ready and nothing else is missing from the inputs. The single missing component is the program.

---

## 9. The worked example, actually run

Target `http://127.0.0.1:8788/` (the organizer pricing console). Real output, pasted.

### Step 1, fetch

```
$ curl -s http://127.0.0.1:8788/ -o /tmp/vh-8788.html -w 'http=%{http_code} type=%{content_type} bytes=%{size_download}\n'
http=200 type=text/html; charset=utf-8 bytes=13726

$ grep -o '<title>[^<]*</title>' /tmp/vh-8788.html
<title>Ticketpath — organizer pricing console</title>
```

### Step 2, render (no browser)

```
$ python3 /tmp/vh-shim/texrender.py http://127.0.0.1:8788/ /tmp/vh-shim/8788-live.png \
      --width 1240 --font 15 --title "Ticketpath organizer pricing console - 127.0.0.1:8788"
{
  "src": "http://127.0.0.1:8788/",
  "text_lines": 91,
  "wrapped_lines": 116,
  "svg": "/tmp/vh-shim/8788-live.png.svg",
  "png": "/tmp/vh-shim/8788-live.png",
  "dims": "1240x2538",
  "raster": "{\"ok\":true,\"format\":\"png\",\"width\":1653,\"height\":3384,\"channels\":4,\"premultiplied\":false,\"size\":900996}"
}

$ file /tmp/vh-shim/8788-live.png
/tmp/vh-shim/8788-live.png: PNG image data, 1653 x 3384, 8-bit/color RGBA, non-interlaced
```

Ink check on the actual pixels, so this is not an empty canvas:

```
{"w":1653,"h":3384,"ch":4,"darkPx":331269,"totalPx":5593752,"inkPct":"5.92"}
```

### Step 3, what came out

Read back from the PNG itself. This is the text as rendered, condensed for this record:

```
Ticketpath organizer pricing console - 127.0.0.1:8788
SYNTHETIC FIXTURE DATA — every number on this page is computed from a synthetic fixture generated in this
repository. Not real ticket data. No accuracy claim is made or implied.
No program is deployed on any cluster. The [DESIGN] block at the bottom says what that means.
fixture build: 15e6f6611652ae43f3967e110e2feeffde0cc2ace13ea868ff3abb0012bb9bfa
Ticketpath — organizer pricing console
event
Synthetic Hall: Cap Present, Not Binding — capped no mass point
Synthetic Stage: Resale Cap Binds — capped and binding
Synthetic Annex: Cold Start, No Resales — no resale
Synthetic Theatre: Uncapped Markup Spread — uncapped
Demo Arena East: Resale Switched Off — no resale
Demonstration Annex: Completed Run — capped no mass point
Synthetic River Hall: Cap Binds On One Tier — capped and binding
Synthetic Studio: Draft, Nothing Issued — no resale
tier
General — capped and binding
Front — capped and binding
decision mode
counterfactual — recomputed from this event's own record
before on-sale — other events only
asOf (ISO-8601 UTC)
capBps (0–10000)
feeLamports (blank = no fee model)
tau (0.10–0.406)
Recompute
Show the refusal
Nothing after 2026-11-07T17:37:45.140Z enters any number, and the URL carries the instant.
The cap field shows the resale cap this page prices against and the canonical URL carries the same number:
clear the field and submit to fall back to this event's recorded cap of 1500 bps.
canonical URL for this decision:
http://127.0.0.1:8788/?event=evt_syn_02&tier=tier_stg_general&asOf=2026-11-07T17%3A37%3A45.140Z&capBps=1500&tau=0.2
[FIXTURE] 12 resales on this event · [FIXTURE] 12 tickets · [FIXTURE] 9 at the ceiling
[FIXTURE] 8 events in the store, [FIXTURE] 5 with any resale at this instant
```

That is the console's real live text, including the live `asOf` instant, the canonical URL with its query
string, and the `1500 bps` recorded cap. A vision model would read this correctly.

### Step 4, the same chain on `:3001`, to prove it generalises

```
{
  "src": "http://127.0.0.1:3001/",
  "text_lines": 86,
  "wrapped_lines": 89,
  "svg": "/tmp/vh-shim/3001-frontend.png.svg",
  "png": "/tmp/vh-shim/3001-frontend.png",
  "dims": "1240x2034",
  "raster": "{\"ok\":true,\"format\":\"png\",\"width\":1653,\"height\":2712,\"channels\":4,\"premultiplied\":false,\"size\":294761}"
}
```

Read back:

```
Frontend copy on 127.0.0.1:3001 - / (Events)
Ticketpath
Events
My tickets
Analytics
Verify wallet
devnet
Events
Tickets are minted as wallet-bound tokens. Every transfer and resale price is recorded against the ticket
for the life of the event.
SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data. No ticket program is
deployed for this build, so every price and custody row here is simulated.
Demonstration Annex: Completed Run
Demonstration Annex · London
Completed
Doors
```

### Step 5, hand it to `vh.py`

```
$ timeout 20 python3 /home/friend/visionHelper/vh.py run /tmp/vh-shim/8788-live.png -p --passes 1
python3: can't open file '/home/friend/visionHelper/vh.py': [Errno 2] No such file or directory
```

**This is where the example ends.** Steps 1 to 4 are real and complete. Step 5 fails on a missing file, not
on a missing capability, not on credentials, not on network.

### One defect found and fixed during this run

First pass on `:3001` rendered the nav as `EventsMy ticketsAnalyticsVerify wallet`, because stripping `<a>`
tags without a separator joins link runs. Fixed by treating `a`, `span`, `code`, `em`, `strong`, `b`, `i`,
`small`, `time`, `abbr` as inline separators. The corrected output is what appears above. Worth recording
because it is the kind of silent corruption a vision model would faithfully transcribe as a single token.

---

## 10. What is missing, and the ranked options

| # | option | cost | needs his yes | gets a real screenshot | gets a vision read |
|---|---|---|---|---|---|
| 1 | Share the existing PNG into a pi session with the `read` tool | free, already done in this session | no | no | **yes** |
| 2 | Copy `~/visionHelper` from the source box (about 1 MB, 0 hardcoded paths) | free | yes, and it needs a route to that box | no | **yes** |
| 3 | Keep the `sharp` text renderer (`/tmp/vh-shim/texrender.py`) | free | no | text only | **yes** |
| 4 | `npx playwright install chromium` + `install-deps` | ~170 MB, free bandwidth, passwordless sudo | **yes, this changes the machine** | **yes** | yes, with 2 |
| 5 | `apt-get install wkhtmltopdf` | small | yes | yes, weaker engine | yes, with 2 |

Option 1 is the cheapest and it is already proven: the images in this run were read back and verified
in-session. For a handful of page checks, `vh.py` is not needed at all. What it buys is the tool loop
(crop/zoom/deskew on demand), per-session cost logging, `stats`, `eval` against ground truth, batch `-j`,
and `watch` on a folder. That is worth restoring for bulk work, and it is overkill for one page.

My recommendation, in order:

1. **Restore `~/visionHelper` from the source box.** It is 1 MB of clean code that the record already
   certifies as having zero hardcoded paths, and it is the only option that brings back the cost logging and
   CER scoring. Also confirm whether he wants `sessions/` (3.5 GB) with it. I cannot reach that box from
   here: `~/.ssh/config` lists only `github.com`, `known_hosts` lists only `github.com`, and there is no key
   or host entry for it. I am not going to guess at his accounts or hunt for credentials.
2. **Until then, use the `sharp` renderer for anything textual**, and read the PNG in a pi session rather
   than through `vh.py`.
3. **Only install Chromium if the visual layout is the question.** CSS, charts, canvas and images do not
   survive a text render, and `:3001` is the page where that matters. Passwordless sudo makes it a two
   command job, but it is a machine change and it is his to authorise.

One more gap to name: if the second fallback matters to him, `openrouter` has no credential in
`~/.pi/agent/auth.json` on this box, so `google/gemini-3.8-flash` could not be reached even with `vh.py`
restored. Primary and first fallback are both commandcode and both covered.

---

## 11. Reproduction, and what was verified where

Everything above was measured on `friend-vm` in this session, not inferred from the skill's prose or from
the migration reports. The three exceptions, each labelled as such in the text: `vh.py`'s internal
behaviour and its model fallback contract come from `SKILL.md` (unverifiable here, the program is absent),
and the reason for its absence comes from `T2-inventory.md` L179 and `T5-transfer.md` §9 item 9.

```bash
# absence
ls -la /home/friend/visionHelper
timeout 20 python3 /home/friend/visionHelper/vh.py --help

# skill and profile
ls -la /home/friend/.pi/profiles/registry/vision-helper/
python3 -c "import json;print(json.load(open('/home/friend/.pi/profiles/config.json')))"

# no browser
for b in chromium chrome firefox wkhtmltoimage playwright; do command -v $b; done
for l in libatk-1.0.so.0 libgbm.so.1 libpango-1.0.so.0; do ldconfig -p | grep -q "$l" && echo "OK $l" || echo "MISS $l"; done
ls -d /home/friend/.cache/ms-playwright; echo "DISPLAY=[$DISPLAY]"

# the rasteriser
node -e "console.log(require('sharp').versions)"   # run from ticketing-frontend
ls /usr/share/fonts/truetype/dejavu/

# the working chain
python3 /tmp/vh-shim/texrender.py http://127.0.0.1:8788/ /tmp/vh-shim/8788-live.png --width 1240 --font 15
file /tmp/vh-shim/8788-live.png
```

Scratch artefacts, all under `/tmp`, none in any repository:
`/tmp/vh-shim/texrender.py`, `/tmp/vh-shim/_raster.js`, `/tmp/vh-shim/8788-live.png` (900,996 B),
`/tmp/vh-shim/8788-live.png.svg`, `/tmp/vh-shim/3001-frontend.png` (294,761 B), `/tmp/vh-shim/3001-frontend.png.svg`.

Did not touch: `:3000` and `:8787` beyond one status-code `GET` each, his three unrelated tooling trees
beyond a filename search for `vh.py`, and any file in `ticketPricing` other than this
one. Nothing committed.
