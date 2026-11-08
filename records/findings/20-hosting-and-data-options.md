# 20 — Hosting and data: what a judge can click, and what the numbers are allowed to be

**Written:** 2026-11-07T18:44Z → 19:30Z. **Fetch window:** 18:45Z → 19:25Z.
**Deadline defended:** initial submission Sun 2026-11-08 **10:00 ET = 15:00Z**; hard stop 11:45 ET.
At the start of this pass that was **20 h 15 min** away.

**Labels used throughout, and used strictly:**

- **MEASURED** — a command was run on this machine and the output is quoted, or a named URL was
  fetched in the window above and the text is quoted verbatim with its URL.
- **MEASURED-ABSENT** — I fetched or probed the named thing and the claim is not there. Absence from
  a named surface is a measurement, not an inference.
- **ASSERTED** — my reasoning, arithmetic or estimate. Never a claim about what a vendor or a rule says.

No number in this file is recalled. Where an estimate is unavoidable it says so in the sentence.

**Scope discipline, stated because this repo has a public-safety rule about exactly this:** nothing
was downloaded over ~10 KB, no site was scraped (only `robots.txt` and licence/README metadata were
read), no dataset was fetched, no account was created, no service was started or stopped, and the
operator's running processes were not touched. The backend at 8788 was read with GET requests only,
which is what every other pass in this repo has done. **One file written: this one. Nothing committed.**

---

## 0. The answer in one page

**Hosting.** Yes, there is something a judge can click, and it costs about two and a half hours. It is
not a website: it is **82 static HTML files, 1.12 MiB, generated in 0.2 seconds from the console this
repo already serves**, published on **GitHub Pages from the `/docs` folder of this repository**. The
console is a single self-contained HTML document with no scripts, no external assets, and — once the
decision instant is pinned — **byte-identical output for the same URL**: measured, three fetches,
one SHA-256. That makes a snapshot not an approximation of the product but a photograph of it, which
is the strongest thing this project can put in front of a judge in the hours available.

**Cloudflare Pages is the runner-up, not the pick**, and for one measured reason: an account created
this weekend is subject to a documented new-project throttle in its first 48 hours. GitHub Pages needs
no account (the repo is already public), no token, no CLI (`gh` is not installed on this machine), and
it survives after the machine does — which is what the rules actually require of the artefact.

**A live backend is possible and is not the plan.** `cloudflared` quick tunnels need no account and no
domain (quoted), but "have no uptime guarantee", the hostname changes on every restart, and the whole
thing dies with the process. That is a demo for a scheduled window, not a submission link. The stdlib
server is read-only, writes no file anywhere, and caps request bodies at 64 KiB — the containment is
better than it looks — but it has no rate limit, no auth, unbounded threads per connection, and
`Access-Control-Allow-Origin: *`. **Exposing it unhardened on a box that also runs other services is
the one thing here I would refuse to do.**

**Cloudflare Workers cannot run this backend on the free plan**: 10 ms of CPU per request, and the
`threading` module is documented as "not functional" there — `ThreadingHTTPServer` is the server's
entry point. Containers require the paid plan.

**Data.** Keep the fixtures. Do not scrape, and the reason is not squeamishness: two of the six
resale sites serve a bot wall or disallow the event-detail path in `robots.txt`, the four biggest
sites' terms pages return 20–1,400 characters of text to a non-browser client so I could not read the
clauses I would have to quote, and — decisively — **an ask is not a realised transaction, which is the
exact distinction this product exists to make.** The one ticketing dataset on HuggingFace with real
volume ships with its `price` and `faceValue` columns replaced by the literal string `[PREMIUM]`.

**What to do with the data hours instead:** nothing new. The honest move is to make the existing
provenance visible on the page a judge lands on, and to spend the one available hour on a devnet memo
we write ourselves — because that is the only on-chain data this project can obtain that it also
controls the meaning of.

---

## 1. The measured starting point

Everything in this section was read or run in this pass.

### 1.1 The console is a snapshot's dream

| Fact | Value | How |
|---|---|---|
| Page size, default state | **13,726 bytes** | `curl` + `wc -c` |
| `<script>` tags anywhere in the document | **0** | `grep -c "<script"` → 0 |
| External references (`src=`, `<link>`) | **0** | `grep -o 'src="…"\|<link…'` → nothing |
| Stylesheets | **1**, inline `<style>` in `<head>` | head of the document |
| Controls | **1** `<form method="get" action="/">`, 8 named inputs | `console/page.py:159` |
| Same URL twice | **byte-identical** | 3 fetches with `asOf` pinned → one SHA-256, `ab1035fb…` |
| Same URL without `asOf` | **differs every request** | `asOf` defaults to `now()` (`orchestrator.py:705`) |

The last two rows are the whole technical story of this document. The console is a pure function of
its query string **once the clock is a parameter** — and the clock already is a parameter, because
every state is a URL and the URL carries the instant. Pinning it is not a hack; it is using the
interface the console was built with. The page then says the truest possible thing about a snapshot:
*"Nothing after 2026-11-07T18:00:00Z enters any number"* — which is exactly what it says on the live
server too.

### 1.2 The state space is small, and it is not the parameters you would guess

| Dimension | Values | Measured source |
|---|---|---|
| event | **8** | `fixtures/synthetic_store.json` |
| tier | **15** across those 8 | same |
| decision mode | **2** (`counterfactual`, `before_on_sale`) | `console/page.py` |
| cap | recorded cap on **5** events (2500/1500/2000/2500/2500 bps), none on 3 | store, `resalePriceCapBps` |
| `asOf` | free text, defaults to now | `orchestrator.py:705` |
| `tau` | declared 0.2; already inert on binding events | `records/STATE-OF-PROJECT.md` A2 |
| `feeLamports` | blank = no fee model | `docs/BACKEND.md` |
| `sim` | on/off | `console/page.py` |

`tau` and `feeLamports` are therefore not worth gridding: one is dismissed on the page the judge is
most likely to open, the other is a declared input with no default. That leaves event × tier × mode ×
cap, and cap only varies where an event has one.

**Measured, that the cap control is not cosmetic:** for `evt_syn_02` at a pinned instant,

| Query | SHA-256 (first 16) |
|---|---|
| default (no `capBps`) | `80ab30fe0b6721e1` |
| `capBps=1500` (the recorded cap) | `80ab30fe0b6721e1` — identical, as it should be |
| `capBps=800` | `c5baff9b668d498a` |
| `capBps=3000` | `4f5b0062e6c297ef` |

and `capBps=800` renders `recommendation_above_cap` with *"8 of 9 recorded sales"* — the refusal
STATE §A2 records, arriving from a static file exactly as it arrives from the server.

### 1.3 The snapshot, built and counted

I generated the whole grid into a scratch directory and measured it. The grid: every event × tier ×
mode at the recorded cap, plus for each of the five capped events one cap below and one above what the
record supports, plus one `?sim=1` page per event.

```
requests=82   pages=82   bytes=1,172,359 (1.12 MiB)   elapsed=0.20s
public_safety HITS: 0
```

**82 files. 1.12 MiB. A fifth of a second. Zero public-safety hits** — that last number is the one
that decides the plan, because it means committing the snapshot to this public repository will not be
refused by the pre-commit hook, and the operator will not have to argue with his own checker at 2 a.m.
(`tools/public_safety.py` `scan()` over the 82 pages with the real `.public-denylist`, 0 hits.)

Two defects a generator has to fix, both found by reading the output rather than guessing:

1. **The canonical-URL line bakes the loopback host.** The console prints
   `canonical URL for this decision: http://127.0.0.1:8788/?event=…` because it derives its base from
   the request. Served from a static host that sentence is false about where the reader is. It must be
   rewritten to the published URL, or relabelled "(this snapshot)". This is not cosmetic: the whole
   product is the claim that its addresses are checkable.
2. **The form has nowhere to post.** `action="/"` on a static host reloads the same file whatever the
   reader selects. A judge who changes the event dropdown and presses **Recompute** would get the same
   numbers back and conclude either that the page is broken or that the price does not respond to the
   record. **That silent lie is the single biggest risk in this plan** and it is solved in §2.2.

---

## 2. HOSTING option 1 — a static snapshot of the console

### 2.1 What it keeps, exactly

Every number, every badge, every refusal, every sentence, the SHA-256 of the store, the `[DESIGN]`
block, the `[SIMULATED]` state machine, the `[DEVNET]` slot saying no transaction exists. Nothing is
re-rendered by a second renderer, so nothing can drift. The page a judge opens **is** the page the
server produced, byte for byte, and its own banner already says what it is.

### 2.2 What it loses, and the JS-free fallback that gets most of it back

| Lost | Cost to a judge | Fix, in hours |
|---|---|---|
| Arbitrary `asOf` (the clock) | none — a judge was never going to type an ISO timestamp | pinned per page; say so in one line |
| Free-form `capBps` / `feeLamports` / `tau` typing | small; `tau` is inert on the main page already | gridded caps; drop the other two |
| Typos and refusals from bad input | none; the static host 404s instead of explaining | ship the 3 error pages as files |
| The **Recompute** button | **large, and it is the product** | see below |

**The fallback works, and it is plain HTML.** A `<form method="get">` is, at a fixed grid, a set of
links. Replace the form block with four link groups — event, tier, mode, cap — each pointing at the
static file for that state, and the reader can traverse the entire space with no JavaScript at all.
The honest sentence that goes with it:

> **This is a snapshot.** The live console recomputes for any instant and any cap you type. Here the
> grid is fixed: 8 events, 15 tiers, 2 decision modes, and for each capped event three cap settings —
> the recorded one, one below what the record supports, and one above. Every page is the console's own
> bytes for that state. Nothing is simulated at read time.

That sentence is better than a live demo in one respect and worse in another, and both are worth
saying in the submission rather than hiding: better, because a reader can check the claim by fetching
the same URL from the server; worse, because a reader who wants `capBps=1234` cannot have it. A
refusal that names its own boundary is the house style here.

### 2.3 The Next frontend under `output: 'export'` — measured, and it does not fit the deadline

I did not reason about this; I ran it. A copy of the demo app was made in a scratch directory (the
demo tree itself was not written to), `output: "export"` was added to its `next.config.ts`, and
`next build` was run five times, each time fixing the previous error to find the next one. This is the
whole chain, in build order, verbatim from the output:

| # | Blocker | Verbatim error |
|---|---|---|
| 1 | the `/api/console` proxy route | `export const dynamic = "force-dynamic" on page "/api/console" cannot be used with "output: export"` |
| 2 | `/events/[eventId]` | `Page "/events/[eventId]" is missing "generateStaticParams()" so it cannot be used with "output: export" config.` |
| 3 | `/tickets/[ticketId]`, same cause | then, once params were supplied: `Route /tickets/[ticketId] with dynamic = "error" couldn't be rendered statically because it used revalidate: 0 fetch http://127.0.0.1:8788/api/tickets/…` — that is `lib/api.ts:57`, `cache: "no-store"` |
| 4 | `/organizer` | `Route /organizer … couldn't be rendered statically because it used await searchParams` |
| 5 | `/pricing` | `Route /pricing … couldn't be rendered statically because it used await searchParams` — and after that, `headers()` at `app/pricing/page.tsx:81` |

The build got to **93 static pages, 23 of them generated**, before stopping. Every one of these five is
in Next's own published unsupported-features list, which I also fetched and quote:

> "Dynamic Routes with dynamicParams: true · Dynamic Routes without generateStaticParams() · Route
> Handlers that rely on Request · … Rewrites · Redirects · Headers · Proxy · Incremental Static
> Regeneration …"
> — `https://nextjs.org/docs/app/building-your-application/deploying/static-exports`, "Last updated
> August 9, 2026", fetched 18:52Z. Its own sentence: *"If you need to read dynamic values from the
> incoming request, you cannot use a static export."*

**ASSERTED, cost:** exporting the frontend properly is 2–3 hours — two `generateStaticParams`, a
build-time data fetch instead of `no-store`, three pages that currently read `searchParams` rewritten
to read them client-side or to be duplicated per filter, and `/pricing` rebuilt to frame a static file
instead of a proxy. It also throws away the thing that makes `/pricing` good: its frame is proxied
server-side precisely so that no badge can be dropped. **Not before 15:00Z.** It is a real option for
after the event, and it makes the demo permanent without a server, which nothing else does.

**The cheaper substitute, and it is honest:** capture the frontend's pages with `tools/shot.py`
(the browser and the wrapper already exist and are documented in `docs/SHOTS.md`), publish the
captures on the snapshot landing page, and caption each one in words the rules require: *the platform
UI is the company's existing app; the weekend's work is the pricing layer inside it.* That caption is
not decoration — `findings/17` R1 names "the demo UI is a pre-existing platform frontend" as the
single largest disqualification exposure in this entry, and a screenshot with the right caption is
strictly safer than a live iframe with none.

### 2.4 The hosts, compared on what this artefact needs

| Host | $ | Limits that matter here | Operator must do | Set-up | Verdict |
|---|---|---|---|---|---|
| **GitHub Pages** | 0 | 1 GB site, **100 GB/month soft** bandwidth, 10 builds/hour, one site per repo. Source is a **branch + (`/` or `/docs`)** | open Settings → Pages, pick `main` + `/docs`, Save | **~5 min**, no account, no CLI, no token | **PICK** |
| **Cloudflare Pages** | 0 | **static asset requests "free and unlimited"**; 20,000 files; 25 MiB/file; 500 builds/mo; 100 projects | create an account, then `npx wrangler pages deploy <dir>`; OAuth login or an API token in the environment | 15–30 min | runner-up; see the 48 h risk below |
| **Netlify** | 0 | free tier is now **credit-metered: 300 credits/month**, bandwidth billed at **20 credits/GB** | account + `npx netlify deploy --prod --dir=<dir>` | 15 min | fine, worse terms than Pages |
| **Vercel Hobby** | 0 | 100 GB transfer, 200 projects, 100 deploys/day — and "**the Hobby plan restricts users to non-commercial, personal use only**" | account + `npx vercel --prod` | 20 min | not for a company-shaped product |
| **HuggingFace Static Space** | 0 | "Static Spaces are free for everyone" | account + repo upload | 20 min | works, no advantage |

Quotes, all fetched 2026-11-07:

- **GitHub Pages limits**, `https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits`:
  > "GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your
  > online business, e-commerce site, or any other website that is primarily directed at either
  > facilitating commercial transactions or providing commercial software as a service (SaaS)"
  > "Published GitHub Pages sites may be no larger than 1 GB … soft bandwidth limit of 100 GB per
  > month … soft limit of 10 builds per hour"
- **GitHub Pages publishing source**, `…/configuring-a-publishing-source-for-your-github-pages-site`:
  > "GitHub Pages is available in public repositories with GitHub Free … the source folder can either
  > be the root of the repository (`/`) on the source branch or a `/docs` folder on the source branch"
- **Cloudflare Pages limits**, `https://developers.cloudflare.com/pages/platform/limits/`, "Last
  updated Sep 5, 2026": 20,000 files, 25 MiB per file, 500 builds/month, and —
  > "In order to protect against abuse of the service, Cloudflare limits the number of new Pages
  > projects you can create within your first 48 hours of using the service."
- **Cloudflare Pages pricing**, `…/pages/functions/pricing/`, "Last updated Sep 8, 2026":
  > "On both free and paid plans, requests to static assets are free and unlimited"
- **Cloudflare Direct Upload**, `…/pages/get-started/direct-upload/`: `npx wrangler pages deploy
  <BUILD_OUTPUT_DIRECTORY>`, no git connection required, and "you cannot switch to Git integration
  later".
- **Vercel Hobby**, `https://vercel.com/docs/plans/hobby`: "As stated in the fair use guidelines, the
  Hobby plan restricts users to non-commercial, personal use only"; 100 GB Fast Data Transfer.
- **Netlify**, `https://www.netlify.com/pricing/`: Free "$0 forever", "300 credit limit / month",
  "Bandwidth 20 credits per GB".
- **HuggingFace Spaces**, `https://huggingface.co/docs/hub/spaces-overview`: "Hardware CPU Basic 2
  vCPU 16 GB **FREE**" and — decisive for the live-backend option — "creating a Space that runs on
  compute (Gradio or Docker) requires a paid plan, while Static Spaces are free for everyone".

**Why GitHub Pages and not Cloudflare, in one line each:** no account to create (CF's 48-hour throttle
can block a brand-new account on the night before judging); no token anywhere (`gh` is not installed,
so nothing needs a credential in `argv` or in `.env`); the publish step is a `git push`, which this
repo already automates; and the rules *already require* the artefact to stay public forever, so a host
whose storage is the repository is the one host that cannot disappear after the event.

**The GitHub Pages ToS line, faced rather than dodged.** A page that prices tickets is
ticket-industry-shaped, and "primarily directed at … facilitating commercial transactions" is the
clause to look at. ASSERTED: this site has no listing, no cart, no price entry, no ticketing
transaction, and no commercial entity behind it — it renders a research artefact over synthetic data
and refuses to state a number it cannot support. It is also the same content the repository already
publishes under a public MIT licence, which is what rules 12 and 13 require. The residual risk is
small and it is not zero; it is named here so the operator can weigh it rather than discover it.

---

## 3. HOSTING option 2 — the live backend

### 3.1 Cloudflare Tunnel, measured against the docs

> "Quick Tunnels create a temporary trycloudflare.com URL for a local service. **You do not need a
> Cloudflare account or domain.**"
>
> "Anyone with the URL can access your local service." · "The URL stops working when you stop the
> `cloudflared` process."
>
> Limitations: "Quick Tunnels have **no uptime guarantee**." · "Each Quick Tunnel supports up to **200
> in-flight requests**. Additional requests return a 429 response." · "Quick Tunnels do not support
> Server-Sent Events (SSE)." · "Email authentication requires an interactive browser session. It does
> not support non-interactive clients." · "**The hostname changes each time** you create a Quick
> Tunnel."

— `https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/`,
"Last updated Sep 30, 2026", fetched 18:47Z.

That is a complete and honest specification of a hackathon demo link, and it is the reason the plan
below treats the tunnel as a **bonus surface, never as the submission link**. The hostname changing on
every restart is the killer: the submission text is written once and judged hours later.

Two details worth knowing that the docs make possible:

- `--allowed-mail '*@mlh.io'` (or the judge's domain) turns a public console into an email-gated one.
  The visitor needs no Cloudflare account, receives a one-time PIN, and **the flag is the only exposure
  control that exists** — which is worth having if the thing does go up on a box with other services.
- The tunnel dials **out** from the box. Nothing listens on a public interface, the router is
  untouched, and the origin stays `127.0.0.1`. That is a materially smaller blast radius than port
  forwarding, and it is the only reason I would countenance exposing the server at all.

**One thing the tunnel gets right that a snapshot cannot:** the console's canonical-URL line derives
from the request's host, so through a tunnel it prints the *public* URL and is true without an edit.

### 3.2 What an attacker actually reaches — measured on the source, and one load test

| Property | Measured | Consequence if exposed |
|---|---|---|
| Disk writes anywhere in `ticketpath/` | **none** (`grep` for `open(…,"w")`, `write_text`, `mkdir`, `unlink` → no hits) | nothing can be corrupted; the worst case is read + CPU |
| Request body cap | `MAX_BODY_BYTES = 64 * 1024` → `413 body_too_large` | a POST flood cannot exhaust memory through the parser |
| Verbs | GET, HEAD, POST implemented; PUT/DELETE/PATCH/TRACE/CONNECT answered 405/404 with a rendered page; OPTIONS → 204 | no interpreter default pages, no method confusion |
| CORS | `access-control-allow-origin: *` on every JSON response | any page a judge visits can read the API. Harmless here (all data is public and synthetic), wrong as a default |
| Rate limiting | **none** — no counter, no bucket, no delay | the only real control is the tunnel's 200 in-flight cap |
| Concurrency model | `ThreadingHTTPServer`, `daemon_threads = True`, no thread cap, default backlog | one thread per connection, unbounded; keep-alive holds them |
| In-memory state | one dict of verification nonces, pruned on each issue (`wallet_verification.py:75-79`) | bounded by challenges issued in the last 5 minutes, not by a hard cap |
| Load, measured | **50 parallel GETs → 50 × 200**, worst 1.54 s, against 2.1 ms for one request at rest (`STATE-OF-PROJECT.md` A9) | absorbs a judge's browser, degrades ~700× doing it |
| Auth | none | anyone can read everything. Nothing personal is in there, which is the only reason this is acceptable |

**What must be hardened before it faces the internet, in order of how much it buys per minute:**

1. `--allowed-mail` on the tunnel (a flag, no code). Buys the whole thing.
2. A concurrency cap: subclass to a bounded `ThreadingMixIn` or a semaphore in `_handle`. ~20 lines.
   Without it, a slowloris is a one-liner against this process.
3. `TICKETPATH_ALLOW_ORIGIN` set to the tunnel host instead of `*`. One environment variable, no code.
4. **Do not** run it from a shell that also has the operator's other services in scope; run it in its
   own process with its own log. The console already renders a labelled 500 on an exception, so a
   crash costs a page, not the process.

**What I would not do:** expose it on `0.0.0.0`, forward a router port, or put it behind a tunnel that
points at anything other than this one process. The containment claim in the table above ("no disk
writes") is a claim about *this* server; it says nothing about anything else on the machine.

### 3.3 The alternatives, and why they are worse for this window

| Option | Blocker, measured | Verdict |
|---|---|---|
| **Cloudflare Workers (Python)** | Free plan **10 ms CPU per HTTP request**, 100k requests/day, 128 MB. Python Workers: "the full Python Standard Library is available … with the following exceptions", and among the exceptions **`threading` and `multiprocessing` "can be imported, but are not functional"**; "the filesystem is not shared between different isolate instances". `ticketpath.server`'s entry point *is* `ThreadingHTTPServer`. | Not a port of the server; a rewrite of its entry point into a `fetch` handler. **ASSERTED 3–5 h**, and the CPU budget is a coin flip for a 14 KB page under Pyodide. No. |
| **Cloudflare Containers** | "**Available on Workers Paid plan**" | Money, and the operator's call. No. |
| **HuggingFace Docker Space** | "creating a Space that runs on compute (Gradio or Docker) requires a paid plan" | No. |
| **Render free web service** | "Render spins down a Free web service that goes 15 minutes without receiving any inbound traffic" | A judge clicking at 02:00 waits for a cold boot. That is a worse first impression than no link. |
| **ngrok and friends** | require an account and an authtoken for anything beyond an ephemeral session, and interstitial warning pages on free tunnels | Same shape as `cloudflared`, one more credential, no advantage. |

---

## 4. The rule angle — does a hosted URL change the submission?

**No, and the earlier finding already settled it.** Re-verified here against the same documents
`findings/17` quotes, and nothing new was found on any page fetched in this window:

- **No rule requires a deployed or hosted URL, a program, or a devnet transaction.** MEASURED-ABSENT on
  the event page, the five category pages, `standard-hackathon-rules.md`, and `contest-terms.md`.
- The submission field is **one** field: *"Try it out / GitHub Link"*. It legitimately holds the repo
  when there is no demo — the label anticipates both.
- Rules 12 and 13 require the **code** to be public and to stay public; `cheating-response.md` calls
  making a required-public repository private afterwards a disqualification risk. **That is the one
  rule a hosted URL touches, and it touches it in the safe direction:** a static site *inside the
  repository* is published by the same act that keeps the code public. A tunnel URL is not.
- **"Judges may inspect Applications at any time during the judging period"** (`contest-terms.md`).
  A tunnel that is up for a scheduled hour is therefore a partial compliance with a sentence that says
  *any time*. A Pages URL is up for all of it. This is the strongest rules argument for the static
  snapshot, and it is not one I expected to find.

**The new risk a hosted page creates, and it is a real one.** `findings/17` R1: the visible product UI
is a copy of an existing platform frontend, and presenting it as this weekend's work is the largest
disqualification exposure in the entry. A polished hosted site **increases** that exposure if it makes
the frontend look like the deliverable. So the landing page has to do the opposite of what a normal
landing page does: say in the first screen what is this weekend's work (the engine, the console, the
fixtures, the checks) and what is not (the surrounding app, the chain, the data). That costs one
paragraph and it is the highest-value paragraph on the site.

**Hosting ToS** — the only clause that could bite is GitHub Pages' "not … primarily directed at
facilitating commercial transactions", discussed in §2.4. Netlify's credit meter and Vercel's
non-commercial clause are lesser versions of the same shape; Cloudflare's Pages free tier has no
equivalent restriction on static assets.

---

## 5. RECOMMENDATION — one plan, sized to 15:00Z

**Publish a static snapshot of the console on GitHub Pages from `/docs`, with a landing page that says
what is whose, and treat a tunnel as an optional bonus for the judging window.**

| # | Step | Hours | Who | Failure mode, and the fix |
|---|---|---|---|---|
| 1 | **Write the snapshot tool,** under `tools/`: fetch the 82 states with `asOf` pinned, write them to `docs/site/console/`, rewrite the canonical-URL line, replace the form with link groups, write the Pages landing page (`index.html` under `docs/`) | **1.0** | agent | a state 500s → the page is written anyway and labelled; the generator fails loudly on any non-200 |
| 2 | `.nojekyll` in `docs/`, then Settings → Pages → `main` + `/docs` | **0.1** | **operator** | Jekyll build error → 404 on every page. `.nojekyll` removes Jekyll from the path entirely |
| 3 | Landing page: 8 console entry points, the 6 frontend captures captioned, and one paragraph on provenance | **0.5** | agent | a caption that overclaims → R1 exposure. The caption is written in `findings/17`'s own words |
| 4 | Screenshots via `tools/shot.py` into `docs/site/shots/`, committed | **0.3** | agent | 6 PNGs ≈ 1–2 MB on top of 1.1 MiB — well inside 1 GB |
| 5 | Verify from a *different machine's* point of view: fetch the published URL, diff against the server's bytes | **0.3** | agent | the classic failure is a local-only success. The diff is the test |
| 6 | Optional: `cloudflared tunnel --url http://127.0.0.1:8788 --allowed-mail …` for the judging window | **0.3** | operator | dies with the process; hostname changes; say "live until HH:MMZ" and no more |

**Total: 2.4 hours of work, of which the operator's share is one Settings screen.**

**Why this and not the alternatives, in order of the argument's strength:** it is the only option that
needs no account, no token, no CLI and no new software; it is the only one whose artefact is published
by the act the rules already require; it is the only one that is still up in six months; its content
is byte-identical to the server's, which is checkable by anyone; and its total cost is 1.12 MiB in a
repository that is currently 6.3 MB.

**Failure modes, ranked by probability:**

1. **The form posts nowhere / link grid missing a state** (likely if step 1 is rushed). Judge sees the
   same page twice and stops trusting the page. *Fix: the verification in step 5 fetches every link on
   every page and asserts a 200.*
2. **The canonical URL still says `127.0.0.1:8788`** (likely). A hosted page pointing at a loopback
   address is exactly the kind of self-contradiction `records/STATE-OF-PROJECT.md` C5 item 5 says a
   careful judge already finds three of. *Fix: a grep in the generator, `127.0.0.1` → fail.*
3. **A landing page that reads as a normal pitch** (moderately likely). *Fix: the first screen states
   what is not built, before the links.*
4. **GitHub Pages does not serve it** (unlikely; 10-min propagation, and the first build after enabling
   can take a few minutes). *Fix: publish once early, not at 09:40 on Sunday.*
5. **The operator's push job is what publishes**, and it runs on its own schedule. **A commit is not a
   deploy.** *Fix: step 2 ends with the URL answering, verified by someone other than the person who
   clicked Save.*

**What I would spend the hours on instead, and why I am not recommending it:** one devnet memo
transaction carrying the quote id and its hash, read back and rendered in the `[DEVNET]` slot, is
already costed at ~1 hour in `STATE-OF-PROJECT.md` C6 item 2 and it moves the "0 of 4" materials test
that the Top 3 criterion is actually judged on. It is **not** in this plan because it is a different
job with a different failure mode (a keypair, an airdrop, and a read-back that the existing loader
already knows how to verify), and because the two jobs do not compete: hosting is 2.4 hours of a
20-hour budget. If only one happens, the devnet write scores more. If both happen, the entry has a
clickable URL that contains a real chain read, which is the only version of this submission that
answers the Top 3 sentence without an asterisk.

---

## 6. DATA — the five options, measured

The question the operator asked is whether to simulate, scrape, or find real data. The answer turns on
one distinction the project already made its name on, so it is worth restating in the operator's terms:
**an asking price is a claim; a resale is a fact.** Every dataset in this section is a set of claims
except one, and the one is the one we can write ourselves.

### 6.1 Keep the labelled synthetic fixtures — **the recommendation**

| | |
|---|---|
| **What it is** | `fixtures/synthetic_store.json` from `tools/build_fixture_store.py`, seed 20261107: **8 events, 76 tickets, 147 ledger rows, 61 priced sale rows**, deterministic to the byte, three deliberate regimes plus five more |
| **Honesty** | every payload carries `dataSource.synthetic: true`; the loader *refuses* a store that does not declare it; every page carries the banner; the resale over-sampling ratio is stated on all 8 events with the number computed from the rows, not typed |
| **Effort** | **0 h** — it exists, it is checked, and two runs are byte-identical |
| **Risk** | the store resells 62–77% of tickets against ~5.1% in the real market (class A, `01-a` §5). A judge who knows the market sees the density. It is already labelled, in the event descriptions, as 12–15× the real rate |
| **Badge** | `[FIXTURE]` everywhere, plus `[UNVALIDATED]` on every engine output |
| **What a judge thinks** | this team knows its data is not real and said so before I asked |

The only improvement worth hours is the one `STATE-OF-PROJECT.md` C6 already ranks: the provenance
table on the landing page. Provenance is the product here; a richer dataset would undercut it.

### 6.2 A richer simulator calibrated to published statistics — **not before the deadline**

There is a real version of this and it is worth describing precisely, because it is the option most
likely to be attempted badly. `tools/sim_recovery.py` already exists (SIM, estimator-property only,
under decision D2's stdlib constraint) and `tools/build_fixture_store.py` already generates from
declared specs. A *calibrated* generator would replace the declared specs with class-A estimates:

| Parameter | Anchor already in this repo | Class |
|---|---|---|
| share of purchased tickets that resell | ≈5.1% (two independent measurements) | A, `01-a` §5 |
| concentration | top 10% of resellers >70% of resale volume; 46% of concert resales by fans | A, `01-a` §5 |
| seat-quality selection | resold tickets mean seat-quality percentile 0.61 vs 0.50 | A, `01-a` §6 |
| holding duration | **no published distribution** — Sweeting's median eBay purchase is 10 days before the game, which is one point, not a distribution | A for the point, gap for the shape |
| markup distribution | median resale markup in the repo's own record; no peer-reviewed distribution by tier | D |
| hot-event ceiling | most active event 17% resold, resale revenue 37% of that event's primary | A, `01-a` §5 |

**What it would look like honestly:** a generator that draws from those anchors, prints the anchor and
its source beside every parameter it used, labels its output `SIM` (not `FIXTURE`), and **does not
enter any number the console displays** — because a simulator calibrated to published statistics is
still a model, and a price computed from a model over simulated data is a claim about the model.

**Effort:** 4–6 h to do it properly, 1 h to do it dishonestly. **Risk:** the dishonest hour is
available and would look identical on screen, which is exactly why the honest version has to print its
anchors. **What a judge thinks:** the honest version, if they read it, is the strongest Learning
artefact in the entry. **Verdict: after the event.** It changes no number a judge can verify today and
it consumes hours that the hosting plan needs.

### 6.3 Scraping — **no**, and the reason is scientific before it is legal

**6.3.1 What the sites' own machine-readable policies say.** `robots.txt` fetched 18:55Z, verbatim
where it matters:

| Host | `robots.txt` says | Reading |
|---|---|---|
| `www.stubhub.com` | `User-agent: *` + ~40 `Disallow` paths (`/secure/`, `/help/privacy/`, `/AjaxService/` …); event and listing paths not among them; sitemap published | crawling listings is permitted by robots |
| `www.ticketnetwork.com` | `User-agent: *` / `Allow: /` | explicitly permits everything |
| `www.viagogo.com` | sitemaps only, no `Disallow` at all | permits |
| `www.ticketmaster.com` | 101 lines under `User-agent: *`; disallows `/checkout/*`, `/member/*`, `/api/ismds/event`, `/json/search/event/*`, `/*event/*?preselect`; **`/event/` itself is not disallowed** | event pages permitted, machine endpoints not |
| `www.vividseats.com` | `User-agent: *` with `Disallow: /*showDetails`, `/search?searchTerm=*`, `/EventSearch.action*`, `/m/*` | **the event-detail path pattern is disallowed** — the pages a price scraper needs |
| `seatgeek.com` | **MEASURED-ABSENT: no `robots.txt` is served.** The request returns a DataDome interstitial — `"Please enable JS and disable any ad blocker"` plus a `captcha-delivery.com` script | a bot wall, at the edge, before any page |

**6.3.2 The terms of service could not be read from this host, so I will not characterise them.**
This is the honest form of a finding that usually gets written from memory:

| URL | HTTP | bytes | text after stripping script/style |
|---|---|---|---|
| `https://www.stubhub.com/legal/` | 200 | 53 | — |
| `https://www.stubhub.com/legal/policies/terms-of-use` | 200 | 53 | — |
| `https://www.vividseats.com/terms.html` | 200 | 22 | — |
| `https://www.viagogo.com/about/terms` | 200 | 55 | — |
| `https://www.ticketmaster.com/h/terms.html` | 200 | 75,838 | **1,405 characters** |

Every one of those is a client-side shell. **MEASURED-ABSENT: I could not read any anti-scraping
clause from any of the five.** Each URL was fetched twice — once with a plain HTTP client and once
through the extraction tool — and neither returned terms text, so the second attempt is not evidence
that a JS-capable path would succeed. I will not quote a clause I did not read, and I will not assert
what they say. **The
practical consequence is itself the finding:** an agent that intends to scrape these sites cannot
verify that it is allowed to, and "I could not read the terms" is not a defence that a hackathon
conduct review or a sponsor's counsel will accept.

**6.3.3 The argument that actually decides it.** A scraped listing is an **ask**. This product's entire
thesis (`RESEARCH-PROGRAM.md`, `01-a` §6, `F` D1) is that the interesting quantity is the **realised**
resale, and that on this platform a resale is a recorded ledger entry rather than a listing. Ingest
real StubHub asks and the console would compute `face × exp(mean log(ask/face))` — the asking-price
premium, the number the secondary market is *least* honest about, on data with no sale and no custody
hop. `records/STATE-OF-PROJECT.md` C5 item 1 already makes this point about the build; scraping would
make it about the data. **The project would stop being able to say the one sentence it exists to say.**

**6.3.4 And the rules.** MLH's cheat check (`findings/17` §3.8) asks "Did they start before the event?"
and "Is a solo hacker making a really advanced project in a single weekend?" — a scraper built in the
window would answer both badly, and a dataset that took weeks to collect is prior work
(`standard-hackathon-rules.md` digital rule 6). No MLH rule names scraping; the risk is ToS-shaped and
conduct-shaped, not rule-shaped. **Effort 4–8 h. Verdict: no, on all three grounds, and the scientific
one is the one that would survive an argument.**

### 6.4 Public datasets and published figures — the measured inventory

I searched, read metadata, and downloaded nothing above ~10 KB. **No file was retrieved; licences,
sizes and column lists are quoted from dataset cards and API metadata only.**

| Source | What is actually there | Licence / access | Has realised prices? | Usable? |
|---|---|---|---|---|
| **`rebrowser/stubhub-dataset`** (HuggingFace) | "Daily snapshots of StubHub resale ticket **listings**, events, and venues". Claims **148,049,602** listing records, 2024-03-31 → 2026-11-01. The HF artefact is a preview: **"up to 30,000 rows"**, "0.02% of full dataset", ≤1,000 rows/day, last 30 days retained | **CC-BY-NC-4.0**; the full slice is a commercial product behind a vendor site, with a free academic tier | **No** — listings, with `quantity`, `availableQuantities`, `createdAt`, `_firstSeenAt`/`_lastSeenAt`. **And the two columns that would matter are redacted:** "🔒 Premium fields are included in the data files but their values are replaced with `[PREMIUM]`" — `price` and `faceValue` are both 🔒 | **No.** The free sample has no prices, and NC is the wrong licence for a company-shaped product |
| **`streetvisit/uk-resale-ticket-prices`** (HuggingFace) | 4 CSVs, "Summary figures on resale ticket prices for upcoming UK concerts, sport and theatre … from NeedATicket, a free tracker that checks StubHub listings hourly" | **CC-BY-4.0**, `n<1K`, README is 1,004 bytes | **No** — "All figures are aggregates of StubHub **listing** prices (before StubHub's booking fees). No individual listings" | No. Aggregates of asks cannot be reversed into a per-ticket price path, and there are no tickets |
| **Zenodo, `"secondary ticketing"`** (exact phrase) | **0 records** | — | — | **MEASURED-ABSENT.** A broader query returns noise (train tickets, hospital "bed head tickets", airline ticketing market reports) |
| **Zenodo, `ticket resale price dataset`** | 194,903 hits, none ticketing-price-related in the top 8 | — | — | nothing |
| **SeatGeek Platform API** | live and keyed: `GET https://api.seatgeek.com/2/events?per_page=1` → **403** `{"status":403,"message":"Client is required - visit \"https://seatgeek.com/account/develop\"","code":40307}` | requires the operator's own API client id | **No** — event metadata and listings | possible later; **not now**, and not for realised prices |
| **Published figures** (CMA, NSW, CCPC, academic papers) | already in `records/findings/01-a-market-structure.md`, class A/B, with counts and ranges | published documents | aggregates only | **already used, and correctly** |

**One measured detail that closes the question for the biggest candidate:** the StubHub dataset's own
card says the record count ranges to 1B, and the free slice is 0.02% of it with the price columns
redacted. There is no free path from that artefact to a markup distribution. That is not a judgement;
it is in the field table.

### 6.5 On-chain data

**6.5.1 The reading path works from this box, measured.** Both public RPC endpoints answered an
unauthenticated `getVersion` in this window:

```
POST https://api.devnet.solana.com      → 200 {"result":{"feature-set":2681577653,"solana-core":"4.4.0"}}
POST https://api.mainnet-beta.solana.com → 200 {"result":{"feature-set":2681577653,"solana-core":"4.4.0"}}
```

So `getSignaturesForAddress` is available today, with no key and no install. **What is missing is an
address.** Every mint in the fixture is a `SYN…` placeholder; `records/STATE-OF-PROJECT.md` C2 records
0 of 4 on the materials test for exactly that reason.

**6.5.2 The third-party programmes are not readable today.** GET Protocol's documentation host now
answers **401** (a ReadMe.io project behind a login) and `get-protocol.io` serves a 1,692-byte page
whose only content is: *"GET Protocol is now OPEN Ticketing Ecosystem →"*. **MEASURED-ABSENT:** I
could not verify their chain, their contracts or their subgraph in this window. `01-a` §5 recorded
their subgraph and "millions of on-chain smart tickets since 2016" as a **vendor claim** — that status
is unchanged and it is now also unverifiable from here.

**ASSERTED:** there is no public Solana NFT-ticketing program I can name, from this host, that (a) is
identified to me by a primary source fetched today and (b) publishes an indexed transfer history. Any
name I offered would be recalled rather than measured. That is not a finding about Solana; it is a
finding about what I could check in twenty minutes.

**6.5.3 The mapping, so that the one available move is unambiguous.** The repo's ledger row and a
Solana instruction result are close to isomorphic:

| Repo ledger field (`fixtures/synthetic_store.json`, `ledger[]`) | Chain source |
|---|---|
| `signature` (currently `null`) | `getSignaturesForAddress` → `signature` |
| `slot` (currently `null`) | same response → `slot` |
| `occurredAt` | same response → `blockTime` (ISO-8601 in the repo; Unix seconds on chain) |
| `kind` (`issue`/`sale`/`transfer`/`redeem`) | the memo instruction's payload, or the instruction discriminator |
| `priceLamports` | **not on chain unless the transaction carries it** — a memo can, a plain transfer cannot |
| `fromWallet` / `toWallet` | the account keys, or the memo payload |
| `ticketId` | `TicketRecord` PDA (design-only) or the mint address |

**The consequence, and it is the whole of §6.5:** the only on-chain data this project can obtain in the
window is data it writes. That is one memo instruction with the quote id and its SHA-256, signed on
devnet, then read back through `getSignaturesForAddress` and rendered by the `[DEVNET]` slot that
already exists and already gates on `records/devnet-artefacts.json` recomputing its own hash. **~1 h,
already costed in `STATE-OF-PROJECT.md` C6 item 2, and it is worth more than every option in §6.3 and
§6.4 combined** — because it turns "no on-chain data exists" into "here is a transaction, here is the
slot, check it yourself".

---

## 7. What to say about the data in the submission

Not a claim to make about the data — a paragraph to paste, written to be true whichever of the above
happens:

> Every number in this demo is computed from a synthetic fixture generated in this repository: eight
> events, seventy-six tickets, one hundred and forty-seven ledger rows, seed 20261107, deterministic to
> the byte and regenerated by `tools/build_fixture_store.py`. The store resells 62–77% of tickets
> against roughly 5% in the real market, twelve to fifteen times the real rate, deliberately, because a
> record of resales has to contain resales; every event description says so. There is no scrape, no
> purchased dataset and no market feed behind any figure. We did not use the public resale datasets
> that exist: the one with real volume ships its price and face-value columns redacted, and the rest
> are aggregates of asking prices, which is the quantity this product is built to distinguish from a
> realised sale. The engine's outputs are labelled `[UNVALIDATED]` because nothing here has been
> checked against a real resale, and the console refuses the four questions this record cannot answer
> by name.

Two sentences about the chain, added only if the devnet write happens:

> One devnet transaction exists: a memo carrying the quote id and its SHA-256, written this weekend,
> read back with `getSignaturesForAddress` and verified against the hash the console prints. No program
> is deployed and no mint is real; the `[DESIGN]` block on the console says what that means.

---

## 8. MEASURED vs ASSERTED — the index

| Claim | Status |
|---|---|
| Console page is 13,726 bytes, 0 `<script>`, 1 inline `<style>`, 0 external refs, 1 GET form | MEASURED |
| Same URL with a pinned `asOf` is byte-identical (3 fetches, one SHA-256) | MEASURED |
| Default `asOf` is `now()`, so bytes differ per request | MEASURED |
| 82-page full grid = 1.12 MiB, built in 0.20 s, **0 public-safety hits** | MEASURED |
| `capBps` 800 / 1500 / 3000 produce two distinct pages and reproduce `recommendation_above_cap` | MEASURED |
| `output: "export"` fails on the demo app at 5 named points, in the order given, from `next build` | MEASURED |
| 50 parallel GETs → 50×200, worst 1.54 s | MEASURED |
| No disk writes anywhere in `ticketpath/`; 64 KiB body cap; no rate limit; `ACAO: *`; unbounded threads | MEASURED (source) |
| Cloudflare/GitHub/Netlify/Vercel/HF limits and ToS lines | MEASURED (quoted, URLs and fetch dates in §2.4, §3.1, §3.3) |
| Six sites' `robots.txt`; SeatGeek serves a bot wall instead | MEASURED |
| Five ToS pages unreadable from this host (22–1,405 characters of text) | MEASURED-ABSENT |
| StubHub HF dataset: `price`/`faceValue` redacted as `[PREMIUM]`, 30,000-row preview | MEASURED (dataset card) |
| Zenodo `"secondary ticketing"` → 0 records | MEASURED |
| SeatGeek API → 403, client id required | MEASURED |
| Solana devnet + mainnet `getVersion` → 200, `solana-core 4.4.0` | MEASURED |
| GET Protocol docs → 401; site rebranded to OPEN Ticketing Ecosystem | MEASURED |
| **"Exporting the frontend properly is 2–3 hours"** | ASSERTED — measured error chain, estimated labour |
| **"Cloudflare Pages' 48 h throttle can block a new account"** | the throttle is MEASURED and quoted; that it *applies to this account* is ASSERTED (it depends on whether he has one) |
| **"A judge changing the dropdown gets the same page"** | ASSERTED — it is what a static host does with `action="/"`; not executed against a deployed site |
| **"The `[PREMIUM]`-redacted sample cannot yield a markup distribution"** | ASSERTED from the field table; I did not open a data file |
| **"A calibrated simulator is 4–6 h"** | ASSERTED |
| **"The GitHub Pages ToS risk is small"** | ASSERTED, and it is a judgement, not a measurement |

---

## 9. Unanswered questions for the operator

1. **Does he have a Cloudflare account already?** It changes the runner-up from "15–30 min and a real
   risk" to "a better CDN for free". I did not look for credentials and will not.
2. **Is `main` the branch the existing push job publishes, and does he want the snapshot committed to
   it?** A commit is not a deploy; the push job is. I have not touched it.
3. **Does he accept a public GitHub Pages site carrying the company's frontend screenshots?** R1 says
   the frontend is the largest disqualification exposure in the entry, and the caption is only as good
   as the honesty behind it. This is his call, not a tool's.
4. **Does he want the tunnel at all?** It is a bonus, it is gated by `--allowed-mail`, and it needs a
   window he can name. Without a window, it is a link that 404s.
5. **Which comes first if only one hour exists: the hosting snapshot or the devnet memo?** My answer is
   the memo (it moves the criterion Top 3 is judged on); the snapshot moves Completion. He decides.
6. **Does he want the 62–77% over-sampling left as is?** It is labelled on every event and it is
   honest. A judge who knows the market sees 12× the real rate, and the label answers it. Changing it
   would make the console compute over four resale rows and show nothing.
7. **Is any of the existing platform frontend his to publish screenshots of?** `findings/17` R5 (sole
   ownership) and R1 point at the same fact from two directions, and only he can answer it.

---

*One file written. Nothing committed, nothing pushed, no service started or stopped, no dataset
downloaded, no account created.*
