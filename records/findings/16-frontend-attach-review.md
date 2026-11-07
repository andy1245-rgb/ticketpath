# 16: Phase 3 review, the frontend attach

**Reviewed:** 2026-11-07, 17:50Z to 18:10Z.
**Trees read only:** `../ticketpath-demo` (the copy, served on `:3001`) and
`../ticketing-frontend` (the operator's frontend, `:3000`). Neither tree was
written: `tsc`, `next build` and the patch trial all ran in copies under `/tmp`. `:3000`
was read with GET only. `:8787` was not touched. `:8788` was read with GET only. `:3001`
was read with GET only.
**Wrote:** this file, build and measurement scratch under `/tmp` (`fe-review`, `fe-mock`,
`fe-apply`, `measure.mjs`, `navtest.mjs`, `sandbox_test.mjs`, `digits.py`), and seven
screenshots in the shot tool's output directory (`~/tools/shot/out/`). Nothing committed, nothing pushed, no state file touched.
**Was not the builder.** Every claim below was re-derived here. Where the builder's claim
and my measurement agree, the measurement is quoted.

**VERDICT: FIX-FIRST.** The ranked list and the apply-to-the-real-frontend consequences
are in §9.

---

## 0. The questions, answered in the order they were asked

| # | Question | Answer | Where |
|---|---|---|---|
| 1 | SSRF / open proxy / XSS / error honesty / allowlist / `action` rewrite | SSRF closed and tested. XSS escaping holds but the frame is unsandboxed and same-origin. Error paths honest. Allowlist is exactly the console's eight fields. `action` rewrite works and is the only byte the proxy changes, but it leaves one root-relative link unrewritten. | §2 to §5 |
| 2 | Run tsc, the checker and its control, curl the three pages and the card | tsc 0 (canary proves it can fail), build 0. Checker 32/32 on `:3001`, 24 fails on `:3000`. Proxy body is the console's body plus one attribute. No number on `/pricing`, in the frame, or on the card disagrees with the backend. | §1 |
| 3 | Is every sentence on `/pricing` still true; does it imply on-chain anything the repo lacks? | Four sentences do not hold. Nothing implies an on-chain capability the repo lacks: the RPC adapter never opens a socket. | §6 |
| 4 | Screenshots | A working headless browser was available. Seven PNGs in `~/tools/shot/out/`. The frame clips about half the console at 1280 and about two thirds at 390, and at 390 the console's own form is cut off. | §7 |
| 5 | Verdict | FIX-FIRST, nine ranked defects, two of which block applying the patch to the operator's real frontend. | §9 |

---

## 1. What was run, and what it said

### 1.1 TypeScript

```
cp -r ticketpath-demo -> /tmp/fe-review          (no .next, no node_modules, symlink back)
cd /tmp/fe-review && ./node_modules/.bin/tsc --noEmit     -> exit 0
```

The check can fail. Appending `const bad: number = "not a number";` to
`app/api/console/route.ts` gives `route.ts(169,7): error TS2322: Type 'string' is not
assignable to type 'number'`, and the file restored clean afterwards.

### 1.2 Build

```
cd /tmp/fe-review && ./node_modules/.bin/next build       -> exit 0
```

Route table from that build: `/`, `/events/[eventId]`, `/organizer`, `/pricing`,
`/tickets/[ticketId]` and `/api/console` are all dynamic (`f`); `/my-tickets` and
`/verify` are static. `/api/console` at 131 B of server code.

Neither real tree was built. `../ticketpath-demo/.next` was not rewritten, so
the dev server on `:3001` was never disturbed.

### 1.3 The checker, and its control

```
python3 tools/check_frontend_attach.py                        -> 32 passed, 0 failed
python3 tools/check_frontend_attach.py --base http://127.0.0.1:3000 -> 6 passed, 24 failed
```

Both claims reproduce exactly. On `:3000` the 24 failures are all seven parity checks, all nine pricing and proxy checks,
the two route checks whose slug and ticket id come from the backend, the two data-source
labels, the false-claims check and the truncation check. The six that
still pass are the backend line, `route home`, `route organizer`, `route my-tickets`,
`route verify`, and `pricing states no price itself`, and that last one is a **false
pass**: it only asserts that a string is absent, so a 404 page satisfies it. A check that
passes on the control is not a check.

**What the checker cannot see.** Every console assertion is a plain GET to
`/api/console`. Nothing in it renders the frame, so nothing in it notices that the frame
shows the top half of the console (`§7`), that the phone view shows no price, or that
the page's own preamble contradicts the frame directly under it (`§6`). 32/32 is true
and it is not evidence that a reader sees the console.

### 1.4 The proxy changes exactly one thing, and this is the proof

With the state pinned in the URL so nothing is recomputed per request:

```
A='event=evt_syn_06&tier=tier_cpl_standing&asOf=2026-10-01T00:00:00.000Z&capBps=2500&tau=0.2'
curl -s "http://127.0.0.1:8788/?$A"            -o /tmp/d1.html   # 13819 bytes
curl -s "http://127.0.0.1:3001/api/console?$A"  -o /tmp/d2.html   # 13830 bytes
diff /tmp/d1.html /tmp/d2.html    # 6 lines, one attribute:
                                  #   -action="/"   +action="/api/console"
```

Everything else is byte-identical: every figure, every badge, every sentence, the
canonical URL line, the refusal list, the design table, the chain slot. The 11-byte
difference is the attribute. This is the strongest technical result in the patch and it
is the thing to keep.

### 1.5 Digit parity

Re-derived independently of the checker, from `/api/events/<id>/analytics` and
`/api/events/<id>` against the rendered text of the proxied console:

| printed on the console | backend | agrees |
|---|---|---|
| `[FIXTURE] 7 resales on this event` (evt_syn_06) | `analytics.saleCount = 7` | yes |
| `[FIXTURE] 8 tickets` (evt_syn_06) | `issuedCount = 8` | yes |
| `median markup [FIXTURE] 8.0%` | median resale 540,000,000 against face 500,000,000 | yes |
| `mean markup [FIXTURE] 5.9%` | `avgMarkupBps = 586` | yes |
| `[FIXTURE] 16 resales` / `[FIXTURE] 13 tickets` (evt_syn_07) | `saleCount = 16`, `issuedCount = 13` | yes |
| `exposure [FIXTURE] 460.5 ticket-days` | the tier's own exposure in the payload | yes |

The checker's own six parity rows agree too (`13`, `+11%` vs 11.38, `77%` vs 76.9231,
`1.91 SOL` vs 1.908, `35.3 SOL` vs 35.298, `2.12 SOL`, `0.94 SOL`). `/pricing` itself
prints no figure at all: `grep -c SOL` on the page HTML is 0, and the only digits in the
response are Next's inline flight payload and asset hashes. The event-page card prints
none either: it is a title, one sentence and `href="/pricing?event=<id>"`.

The four URLs the brief named, read directly:

| URL | status | bytes |
|---|---|---|
| `/pricing` | 200 | 72437 |
| `/pricing?event=evt_syn_06` | 200 | 72615 (the frame src is `/api/console?event=evt_syn_06`) |
| `/api/console?event=evt_syn_06` | 200 | 13463 |
| `/events/synthetic-river-hall-tiered-cap` | 200 | 173851, containing `href="/pricing?event=evt_syn_07"` |

No number on any of the four surfaces disagrees with the backend. The number problem in
this patch is not arithmetic, it is framing (`§6`).

### 1.6 Does the patch apply to the operator's real frontend?

```
cp -r ticketing-frontend -> /tmp/fe-apply
cd /tmp/fe-apply && patch -p1 --dry-run < /tmp/fe-impl-diff.patch   -> exit 0
                      patch -p1         < /tmp/fe-impl-diff.patch   -> applies
                      ./node_modules/.bin/tsc --noEmit             -> exit 2, 3 errors
```

The three errors:

```
app/pricing/page.tsx(3,33): error TS2307: Cannot find module '@/components/SyntheticNotice'
app/pricing/page.tsx(4,15): error TS2305: Module '"@/lib/types"' has no exported member 'DataSource'
app/pricing/page.tsx(43,50): error TS2339: Property 'dataSource' does not exist on type 'Page<Event>'
```

The patch is textually applicable and does not compile there. It presupposes the
frontend-honesty patch (`SyntheticNotice`, `DataSource`, `Page.dataSource`), which is in
the copy and not in the real frontend. See §9, D8.

---

## 2. Security

### 2.1 SSRF and open-proxy: closed, and tested

The target is built in one place (`route.ts:126`): `origin + "/" + "?" + query`, where
`origin` comes from `CONSOLE_ORIGIN ?? NEXT_PUBLIC_API_BASE_URL` (`route.ts:46-48`), read
from the environment on the server. No part of the request reaches the scheme, host,
port or path. The query is serialised by `URLSearchParams.toString()`, which
percent-encodes `/`, `#`, `&`, `=` and CR/LF.

Attempts against `:3001`, all of which stayed on the fixed host:

| request | result |
|---|---|
| `?event=../../etc/passwd` | 404, the console's own `[REFUSED] not_found` page |
| `?event=%2e%2e%2f%2e%2e%2fetc%2fpasswd` | 404, same page |
| `?event=http://169.254.169.254/latest/meta-data/` | 404, `not_found: event ... not found` |
| `?event=//evil.com/x` | 404, same |
| `?event=evt_syn_06%0d%0aX-Injected:1` | 404, the CRLF encoded and forwarded as a value |
| `/api/console/../events`, `/api/console%2f..%2fevents` | 404 from Next |
| `/api/console/` | 308 to `/api/console` (Next's trailing-slash normalisation) |
| `?bogus=1`, `?Event=x` | 400 with the labelled panel, not sent upstream |
| `?%65vent=evt_syn_06` | 200, percent-decodes to an allowed name |

Redirects are not followed (`redirect: "manual"`, `route.ts:132`) and a 3xx comes back as
a `[UNAVAILABLE]` 502 panel. The response carries only `content-type`, `cache-control`
and `nosniff`; no upstream header and no cookie is forwarded. There is no `Set-Cookie`
surface and no open redirect.

Residual, low, not fixed by this patch: the body is buffered with `upstream.text()` with
no size cap, and `CONSOLE_ORIGIN` is trusted completely (a server operator who points it
at a metadata address gets that page back as HTML). Both are operator-controlled, not
caller-controlled.

### 2.2 XSS: escaping holds, containment does not exist

Reflection was tested at all four interpolated points. Every one is escaped by the
console's own `esc()` before it reaches the document:

```
?event=<script>alert(1)</script>                     -> event &lt;script&gt;alert(1)&lt;/script&gt; not found
?event="><img src=x onerror=alert(1)>                -> &quot;&gt;&lt;img src=x onerror=alert(1)&gt;
?event=evt_syn_06&tier="><svg onload=alert(1)>        -> &quot;&gt;&lt;svg onload=alert(1)&gt;
?event=evt_syn_06&asOf=<img src=x onerror=alert(1)>  -> &#x27;&lt;img src=x onerror=alert(1)&gt;&#x27;
```

The console emits zero `<script>` tags (measured), loads no external resource, and its
own route handler escapes every interpolation in `panel()` with `escapeHtml`
(`route.ts:56-62`, applied to the title, every line, and the fetch error message).

What does not exist:

- the `<iframe>` (`app/pricing/page.tsx:143-147`) carries **no `sandbox` attribute**;
- `/api/console` sets **no `Content-Security-Policy`** and **no `X-Frame-Options`**.

Consequence, measured: the frame is same-origin, so the parent can script the frame's DOM
(`f.contentDocument.documentElement.scrollHeight` reads fine from `/pricing`) and by
symmetry the frame can script the parent. Today that capability is unexercised because
the console has no script. On the operator's real frontend, where the app hosts a
wallet-adapter signature flow, an injected byte anywhere in the console's payload becomes
app-origin script. The containment rests entirely on "the console keeps escaping".

**The fix is proven, not proposed.** A host page on another origin, framing the proxy with
`sandbox="allow-forms"`, renders the console and keeps it working:

```
console rendered (headline): [UNVALIDATED] Recommended primary price: 0.53 SOL per ticket.
frame script can reach parent document: blocked: SecurityError
after submit, cap field: 3000          (Recompute went through /api/console)
```

`allow-forms` with no `allow-same-origin` is sufficient because the console needs forms
and no script. Add `sandbox="allow-forms"` and a CSP of
`default-src 'none'; style-src 'unsafe-inline'; form-action 'self'` on the proxy
response, and both holes close without losing a badge.

Also missing: `/api/console` can be framed by any site. Low for a demo, one header.

---

## 3. Error-path honesty

The four panels the route writes itself, read in full:

| path | status | what it prints | a number? | a green state? |
|---|---|---|---|---|
| unknown parameter (`route.ts:104-113`) | 400 | the offending key and the eight accepted keys, and "the request was not sent to the backend" | no | no |
| no backend configured (`:117-125`) | 500 | names `NEXT_PUBLIC_API_BASE_URL`, says the app is in mock mode, names the command to start the backend | no | no |
| fetch threw (`:135-143`) | 503 | the origin, the exception message, and "This is the proxy reporting the failure, not the console refusing a price" | no | no |
| upstream 3xx (`:145-152`) | 502 | the status number and the target | the HTTP status only | no |

Every one carries `[UNAVAILABLE]` and the same closing line: "Nothing on this panel is a
price. The console itself did not answer, so no figure was computed or shown." Measured
against a dead origin (`CONSOLE_ORIGIN=http://127.0.0.1:9` on `:3101`):

```
503  The pricing console did not answer
     The backend at http://127.0.0.1:9 could not be reached from the app server: fetch failed.
```

No failure path returns 200 and no failure path prints a price. This is the part of the
patch I would defend in front of a judge.

Two deviations from the plan (`records/findings/14-frontend-attach-explore.md:293`) that
matter and are improvements:

1. The plan said "on a dead backend return 200 and one plain sentence". The build returns
   **503**. Browsers render a 503 body inside an iframe, so the reader still sees the
   panel and the status is now truthful to `curl`. Keep it, and say so where the plan is
   recorded.
2. The plan's acceptance said `?event=nope` returns 404 and still renders the console
   error page. It does (measured).

One honesty gap in the failure panel wording: it offers
`python3 -m ticketpath.server --port 8788`. That command has to be run from the
ticketPricing repository root, and the sentence does not say so. A judge who runs it
elsewhere gets an import error and concludes the backend is broken.

---

## 4. The parameter allowlist against the console's real fields

The console's own form (`ticketpath/console/page.py:159-169`) posts exactly:

```
event, tier, mode, asOf, capBps, feeLamports, tau, sim
```

`CONSOLE_PARAMS` (`route.ts:30-39`) is exactly those eight, in that order. Nothing the
console accepts is missing, nothing it ignores is allowed. Checked field by field, and
`sentence`-checked against `controls()`: no ninth field, no `at`, no `sort`.

Three notes:

1. **`at` is an invention** (`route.ts:42`). The console has never accepted it and the
   page never produces it. It is a silent alias that maps an unknown name onto a known
   one, in the one file whose stated purpose is "a typo cannot look like a different
   price". Remove it or document it on the page.
2. **Duplicate keys disagree with the backend.** The proxy uses `forwarded.set(name,
   value)` (`route.ts:110`), so `?event=a&event=b` reaches the console as `b`. The
   backend takes the first (`server.py:246`: `values[0]`), so a direct
   `:8788/?event=a&event=b` prints `a`. `/pricing` appends both (`page.tsx:33`). The
   proxied console and the canonical URL therefore disagree on the same input. One word:
   `append`.
3. **The allowlist's strictness leaks into the page.** `/pricing` forwards every query
   parameter it is given (`page.tsx:30-35`) and lets the proxy refuse. That is defensible
   as a design, but the cost is measured: `curl '/api/console?event=evt_syn_06&utm_source=x'`
   returns 400 with "The console proxy refused this request", so a judge arriving from any
   link with a tracking parameter sees a refusal panel where the price should be, and the
   refusal panel is indistinguishable at a glance from the engine refusing to price.
   Filter on the page to the same eight and print one line naming anything dropped.

---

## 5. The `action="/"` rewrite

It works. Driving the real form through a browser:

```
before:          frame url /api/console?event=evt_syn_06
fill capBps=3000, click Recompute
after:           frame url /api/console?event=evt_syn_06&tier=tier_cpl_standing
                             &mode=counterfactual&asOf=...&capBps=3000&feeLamports=&tau=0.2
                 cap field reads 3000, the page re-rendered
```

Three things the rewrite does not cover, in order of how visible they are:

1. **The error page's back link is left unrewritten.** `page.py:407` renders
   `<a href="/">back to the decision</a>`, and it is the only `href` in the entire console:
   every other console state emits zero `src` and zero `href` (measured across four
   states), which is what makes this a one-line fix and a one-line test. Inside the frame that resolves to the app's
   home page. Measured: on `/pricing?event=nope`, clicking it navigates the *frame* to
   `http://127.0.0.1:3001/`, and the frame then renders the whole app with its own nav
   (5 links) inside a 1800px box. The app inside the app. Fix: rewrite `href="/"` the
   same way as the form action, or better, put the console behind a base tag, or give the
   console a `consolePath` parameter; the one-line version is a second `.replace`.
2. **The address bar stops describing what is on screen** after any Recompute. The frame
   is at `/api/console?...` while the page is still at `/pricing?event=evt_syn_06`. The
   console's head sentence promises "every control is a plain form, so every state a
   judge can reach has a URL"; inside this frame that stops being true for the frame's
   state, and a judge who copies the address bar gets the state before the recompute.
   Acceptable as a known limit, but it should be written down on the page or synced with
   `history.replaceState` from the parent once a `postMessage` exists.
3. **`html.replace` replaces one occurrence.** There is one form today, so this is
   correct now; the comment says so. Worth a test rather than a comment, because the
   console is another repository and both repos run their own suites.

---

## 6. Every sentence on `/pricing`, checked against the frame it introduces

The frame's content for the default state (`/pricing`, no parameters) is the console at
`?event=evt_syn_02`, `status on_sale`, ending 2026-11-22. I read both documents in full
and compared them sentence by sentence.

### 6.1 The opening sentence promises the two things the console refuses

`app/pricing/page.tsx:52-57`:

> what a ticket is realistically worth on resale, how that value moves over the time left
> before the event, the chance it sells at a given price, and the primary price that
> maximises risk-adjusted expected value rather than an assumed markup.

The console, on every state, prints in `[REFUSED] What the engine refuses`:

> `[REFUSED] not_identified: The platform does not record asking prices, so we cannot
> estimate the chance a ticket sells at a specific price. What is shown is what actually
> happened.`
> `[REFUSED] no_demand_response: An interior optimum needs a primary demand response. η and
> q_min are not identified from this record, so the recommendation is a boundary.`

Two of the four deliverables in the page's first sentence are exactly the two the engine
refuses, and the fourth is a boundary rather than a maximiser. The sentence is the
charter's aim (`AGENTS.md:10-13`, `RESEARCH-PROGRAM.md:608`) restated as if it were the
console's output. **It is the first thing a reader meets and it is contradicted by the
refusal list three cards down.** Rewrite it as what the console can and cannot answer, in
the console's own words ("a range, not a point; it refuses the two things this record
cannot identify").

### 6.2 The decision-mode sentence is false for the frame's default state

`app/pricing/page.tsx:128-133`:

> Decision mode: counterfactual unless you choose another in the console's own controls.
> That mode recomputes the value from the event's **completed resale record in hindsight**,
> so the figure is what the record implies and not a price you could have set. The panel
> above the recommendation names the mode in force and says what it excludes.

The console, same screen, two cards below, for the default event:

> `[UNVALIDATED] Decision mode: COUNTERFACTUAL. This page recomputes the value from this
> event's own record as it stands at this decision instant. The event has not ended at this
> instant, so the record read here is the record up to this instant and not a finished one:
> **this page is not hindsight**, it is what the record in hand implies now, and it is not a
> price you could have set.`

The page says hindsight, the console says not hindsight, and both are visible at once in a
single screen, three lines apart (screenshot `review-pricing-1280.png`). This is the
same defect commit `375126f` ("Make the decision-mode sentences true at the printed
instant") removed from inside the console; the new page reintroduces it one level up.

For an event that has ended (`?event=evt_syn_06`, ended 2026-10-03) the console does say
"completed record ... in hindsight", so the page's sentence is right for exactly one of the
two regimes and wrong for the default one.

`and says what it excludes` is also narrower than it reads: only `before_on_sale` prints an
exclusion ("`[FIXTURE] 7 recorded on this event are excluded by the mode`"). In
counterfactual nothing is excluded, so there is nothing for the panel to say.

Fix: derive the sentence from the frame's state, or make it state-neutral ("the panel names
the mode in force, its instant, and what it does and does not read").

### 6.3 "the band around it is the part worth arguing with" is false for a binding-cap event

`page.tsx:72-78`. For evt_syn_07 (the event the checker itself uses for the event-page
card) the console prints no band:

> `[UNVALIDATED] Recommended primary price: at least 1.38 SOL per ticket, General tier.`
> `Value: at least 1.38 SOL per ticket. That is a floor, not an estimate.`
> `Range: 1.38 SOL and up. We do not state an upper bound from this record.`

There is no band to argue with; the figure is a floor and the upper bound is explicitly
refused. Same class as 6.2: a sentence written for one regime, printed above all of them.

### 6.4 The canonical-URL sentence is wrong about the mechanism, and its link is dead off this box

`page.tsx:150-161`:

> The console's canonical URL is built from **its own host header**, so it reads
> `http://127.0.0.1:8788` ... That is where the numbers come from, and it is a plain string
> for anyone reading this from another machine.

`server.py:247-248` builds it from the server's bound address, not from any request header:

```
host, port = self.server.server_address[:2]
status, html = console_index(self.orchestrator, query, base=f"http://{host}:{port}")
```

`grep self.headers` finds only `content-length`. So the mechanism is the bind address. The
value is right on this machine and wrong through any tunnel or reverse proxy, which is how
a judge outside this box would reach the demo. The same sentence promises a URL "for
anyone reading this from another machine" while rendering an `href` to a loopback address;
the link `Open the same state directly on the backend` is dead for everyone but the
operator. (The claim originated in the explore note, `14-frontend-attach-explore.md:269`,
which cites `server.py:96-114` and `:248` for it. The citation is wrong.)

Fix: build the console's canonical from a configured public base (an env var, or the
request's `Host` with an allowlist), and have `/pricing` print the same variable the proxy
actually fetches.

### 6.5 The badge legend is a correct copy of a glossary that lives in another repository, and one gloss is already contradicted

The eight entries at `page.tsx:92-126` reproduce `ticketpath/core/labels.py:33-42` almost
verbatim. Checked entry by entry: all eight present, none invented, none missing. Good.

Two problems:

- It is a copy, across a repository boundary, of a constant that has a test in the backend
  and no test here. When `labels.py` changes, this page silently lies, and nothing in
  either repo can notice.
- The `[DECLARED]` gloss is already contradicted by the console's own sentence. The page
  says "a parameter a person set, not estimated"; the console prints
  `sale rate in this tier: [DECLARED] 7.5 per 1,000 ticket-days` and then
  "The rate above is not measured from the record: it is the posterior mean of the
  declared Gamma(1, 1) prior over the ticket-days at risk". That number is an estimate
  from declared hyperparameters, and the badge is on it.

Fix in one move: stop copying. Have `/pricing` fetch the legend from the backend (a
`/api/badges` route of eight lines, or the payload the console already builds), or delete
the legend and let the console's own badges speak. A second repo's copy of the eight
glosses is exactly the kind of thing that decodes wrong in six weeks.

### 6.6 The new `[UNAVAILABLE]` badge does not exist

The failure panels introduce a ninth badge, `[UNAVAILABLE]` (`route.ts:74`). It is not in
`labels.BADGES`, so no test anywhere knows it, and the page's legend lists eight. A reader
who meets a proxy failure sees a badge the page told them does not exist. Either add it to
the legend and to `BADGES`, or use `[REFUSED]` with a distinct sentence (which is what the
console's own error page does).

### 6.7 What is true, and worth saying so

- "The recommended price is [UNVALIDATED]" holds for every priced state; the badge is on
  the headline in the frame too.
- "The numbers themselves are [FIXTURE]" holds; the store hash is printed in the frame's
  banner.
- "No ticket program is deployed for this build, so no figure on the console came from a
  cluster" holds, and I checked the mechanism rather than the sentence: `RpcAdapter`
  never opens a socket (`rpc_adapter.py:1-12`, no `urllib`/`socket` import), and the chain
  slot prints the absent state.
- "Where the record cannot support a number, the console refuses and names the missing
  observation" holds; `?event=evt_syn_03` (0 resales) returns the refusal with
  `[REFUSED] not_identified`, `no_demand_response`, `no_fee_model` and the cold-start
  text.
- The card on the event page carries no figure and links with the event id, so an event
  with no resale history reaches a page that refuses rather than an empty frame
  (`/events/synthetic-annex-cold-start` -> `?event=evt_syn_03` -> refusal). Verified.
- Nothing on `/pricing` implies an on-chain capability the repo lacks. The legend's
  `[DEVNET]` gloss ("read back from devnet and verified, or explicitly absent") matches the
  console's use, which is always the absent branch in this build.

---

## 7. Screenshots and layout

`~/tools/shot/shot.mjs` works (Playwright 1.65, headless). Three older PNGs already sat in
`~/tools/shot/out/` from 17:55, taken from another session; none of them is of `/pricing`
in its frame, which is why the clipping below had not been seen. The builder's "no
screenshots exist" is consistent with that.

New, in `~/tools/shot/out/`:

| file | what |
|---|---|
| `review-pricing-1280.png` | `/pricing`, full page, 1280 |
| `review-pricing-390.png` | `/pricing`, full page, 390, mobile |
| `review-pricing-refusal-1280.png` | `/pricing?event=nope`, full page, 1280 |
| `review-home-1280.png`, `review-home-390.png` | `/`, full page |
| `review-event-card.png`, `review-event-1280.png` | the new card on evt_syn_07 |

### 7.1 The frame is shorter than the console, in every state

`className="block h-[2200px] w-full border-0 sm:h-[1800px]"` (`page.tsx:146`) is a fixed
height for content whose height is not fixed. Measured, viewport by viewport:

| state | console height at 1280 | frame box | hidden | console height at 390 | hidden |
|---|---|---|---|---|---|
| default (`evt_syn_02`) | 3382 | 1800 | 1582 (47%) | 6727 | 4527 (67%) |
| `?event=evt_syn_06` | 3399 | 1800 | 1599 (47%) | 6627 | 4427 (67%) |
| `?event=evt_syn_03` (refusal) | 3500 | 1800 | 1700 (49%) | 6935 | 4735 (68%) |
| `?event=evt_syn_06&mode=before_on_sale` | 3575 | 1800 | 1775 (50%) | 7315 | 5115 (70%) |
| `evt_syn_04` | 3321 | 1800 | 1521 (46%) | 6497 | 4297 (66%) |
| `evt_syn_06&sim=1` | 3595 | 1800 | 1795 (50%) | 7160 | 4960 (69%) |

Inside the frame the console keeps its own scrollbar, so the content is reachable only by
scrolling a box inside a page. In the 1280 screenshot the frame cuts mid-sentence in the
market panel ("sale rate in this tier: [FIXTURE] 20.6 per 1,000 ticket-days."). The four
panels below the cut are the refusals, the design panel, the state machine and the chain
slot: the honesty payload the page exists to deliver, invisible unless the reader
discovers a nested scrollbar. This is the single most damaging layout fact in the patch, and it is why the
32/32 is not reassuring.

The failure case is the mirror image (`review-pricing-refusal-1280.png`): the console's
error page is about 200px tall, the frame is still 1800px, so a refusal renders as a
1800px empty white box with three lines at the top.

An iframe cannot size to its content without cooperation, so this is a real choice and it
collides with D9:

- **Scripted height.** The parent reads the frame's document (same-origin today) or the
  frame posts its height. Either needs `allow-scripts`, which undoes the sandbox and puts
  us back to §2.2. Correct output, wrong security for a page that will sit beside a wallet.
- **No frame.** A link to the console in a new tab, with the preamble kept on `/pricing`.
  Loses the in-shell look, keeps the sandbox, shows 100% of the console.
- **Tall fixed height, sandbox intact.** One number from the measurement above: 3600px
  covers every desktop state, 7400px would cover the phone states, which is absurd on a
  phone. Honest for a desktop demo, and it over-pads a refusal by 3400px.

My recommendation: the second for the demo, the third if the in-shell look is the point.
Do not ship a frame that hides half the page and calls it the console.

### 7.2 At 390 the console's own form is cut off

Measured: the console document is 586px wide inside a 356px frame, a 230px overflow. The
widest elements are the design table (438px) and the `[DESIGN] 6010 E_CAP_EXCEEDED`
spans (135 to 203px each), and the body inherits that width, so the form renders at 586px
and its right-hand controls fall outside the 356px frame. In `review-pricing-390.png`:

- the `event` select is truncated at the right edge ("Synthetic Stage: Resale Cap Binds — cap");
- the `tier` select is entirely off-screen;
- `capBps` and `tau` sit half outside the frame;
- the frame cuts at the end of the mode panel, so **no price is visible at all**: the
  recommendation, the value line and the refusals are all in the nested scroll;
- the canonical URL line is clipped mid-token.

So on a phone, the page that exists to show a primary price shows none, and the control
that would let a reader pick a second tier is unreachable. The home page's own mobile
overflow is pre-existing and not this patch's (scrollWidth 482 on `:3000`, 536 on `:3001`,
widest element the EventCard in both), but it means the app was never checked at 390
either.

### 7.3 Contrast

Measured from the actual hex values:

| text | ratio | verdict |
|---|---|---|
| console body `#14181d` on `#fbfbfa` | 17.21:1 | fine |
| console `.label-sentence` `#3d434a` on `#fff` | 10.00:1 | fine |
| console footnote `#52514e` on `#fbfbfa`, 13px | 7.67:1 | fine |
| page badge legend, `text-ink-2` 12px | 7.53:1 | fine |
| page footnote, `text-ink-muted` 12px | **3.41:1** | fails AA for normal text |

The footnote at 3.41:1 is the sentence about where the numbers come from, with the one
link on the page. It is the least readable text on the page and it carries the provenance
claim. `--text-muted: #898781` is used across the app, so this is a pre-existing token
choice, but this is the page where it costs something.

### 7.4 What looks good

The nav item fits (1280 header shows Events, Pricing, My tickets, Analytics, Verify
wallet, no wrap). The card on the event page (`review-event-card.png`) is clean: title,
one sentence, a right-aligned "Open for this event", no figure, no badge to lose. The
SyntheticNotice renders the backend's own label verbatim. The frame's own dark banner
against the app's white card reads as a distinct surface rather than a broken one.

The nav is `hidden ... sm:flex` with no mobile fallback, so the new Pricing item is
desktop-only. On a phone `/pricing` is reachable only through an event page's card. That
is pre-existing shell behaviour, but it means the nav item does not make the page
reachable where the page is broken.

---

## 8. The patch as an artifact

- The diff covers five files: `.env.local` (new), `app/api/console/route.ts` (new),
  `app/events/[eventId]/page.tsx` (one card), `app/pricing/page.tsx` (new),
  `components/AppShell.tsx` (one nav line). 396 lines.
- `tools/check_frontend_attach.py` is in the ticketPricing repo, not in the frontend, and
  is therefore not in the patch. That is the right place for it, and it should be named in
  the submission pack as a repo tool, not as part of the frontend change.
- `.env.local` is gitignored in the frontend, so it will never travel with a commit. It
  applies to this demo copy. Applying the patch to the operator's real frontend and
  creating that file there flips the **whole** app from `lib/mock` to `:8788` on the next
  restart, not just `/pricing`. That is the intent for a demo, and it has to be said out
  loud before anyone applies it.
- The patch applies textually to the operator's real frontend and then fails to compile
  (§1.6). It is not standalone.

---

## 9. VERDICT: FIX-FIRST

The patch is a real improvement and its core is sound: the proxy is a closed proxy, the
body it serves is the console's body to the byte, the failure panels are honest, and the
copy hides its testable surface behind 32 passing checks. I would keep all of it.

But the page above the frame states five things that are not true of the frame it
introduces (D1, D2, D3, D6, D7), and it hides the refusals it says it is delivering
(D4, D5). Those are the exact defect class this project has spent four commits removing
from the console, and they are all cheap: every one of them is a change in
`app/pricing/page.tsx` or `app/api/console/route.ts`. Fix them and this ships.

### Ranked defects

Ordered by how much damage the defect does to what the deliverable claims to be.

---

**D1. The first sentence on `/pricing` promises the two outputs the console refuses.**
`app/pricing/page.tsx:52-57`
- Repro: `curl -s http://127.0.0.1:3001/pricing | sed 's/<[^>]*>//g' | head -c 900` for the
  promise; `curl -s 'http://127.0.0.1:3001/api/console' | grep -o '\[REFUSED\] not_identified[^<]*'`
  for the refusal. Both are on screen at once in `review-pricing-1280.png`.
- Why it matters: a judge reads "the chance it sells at a given price, and the primary
  price that maximises risk-adjusted expected value" and then reads the engine refusing
  sale probability by name and returning a boundary instead of an optimum. The page
  amplifies the console's honesty problem rather than fixing it.
- Fix: replace the sentence with what the console answers, in the console's words. For
  example: "It prices the primary market from the resale record as a range, and it prints
  by name the two questions this record cannot answer: the chance a ticket sells at a given
  price, and an interior optimum." Do not restate the charter's aim.

**D2. The decision-mode sentence says "completed record in hindsight" for a frame that
prints "this page is not hindsight".**
`app/pricing/page.tsx:128-133`
- Repro: `curl -s http://127.0.0.1:3001/api/console | grep -o '<p class="mode">.*</p>'`
  (default state, `evt_syn_02`, `on_sale`). Compare with the page text.
- Why it matters: it is the same defect commit `375126f` fixed inside the console, put
  back one level up, on the default view.
- Fix: make the sentence state-neutral and true in both modes ("the panel names the mode
  in force, the decision instant, and what it does and does not read"), or derive it from
  the event's status. Drop "and says what it excludes", which is only true in
  `before_on_sale`.

**D3. "the band around it is the part worth arguing with" is false for the binding-cap
regime.**
`app/pricing/page.tsx:72-78`
- Repro: `curl -s 'http://127.0.0.1:3001/api/console?event=evt_syn_07' | sed 's/<[^>]*>//g' | grep -o 'Value: at least[^.]*\.'`
  There is no band; the console says "a floor, not an estimate" and "We do not state an
  upper bound".
- Fix: say "the range around it, where the record supports one, and the floor where it
  only supports a floor".

**D4. The fixed iframe height hides about half the console at 1280 and two thirds at 390,
including every refusal.**
`app/pricing/page.tsx:146`
- Repro: `node /tmp/measure.mjs` (§7.1), or `review-pricing-1280.png`. The console is
  3382px in the default state; the frame is 1800px; the cut lands mid-sentence in the
  market panel and everything below it is behind a nested scrollbar.
- Why it matters: the page's subtitle promises the badges and the refusals arrive exactly
  as written, and the refusals are the part a reader never sees.
- Fix: size the frame to its content, or stop framing (the three options and the sandbox
  trade-off are in §7.1). If the frame stays, handle the short case too: a refusal is
  200px of content in an 1800px box today.

**D5. The refusal panel's `back to the decision` link loads the app's home page inside the
frame.**
`app/api/console/route.ts:164` (the rewrite covers only the form action)
- Repro: open `http://127.0.0.1:3001/pricing?event=nope`, click "back to the decision".
  The frame navigates to `http://127.0.0.1:3001/` and renders the whole app, nav included,
  inside a 1800px box. Measured in `/tmp/navtest.mjs`.
- Fix: rewrite `href="/"` in the proxied body the same way the form action is rewritten,
  or, better, inject one `<base href="/api/console">` and let every root-relative URL in
  the console resolve inside the proxy. Add a test that asserts no `href="/"` survives.

**D6. `/pricing` names a different origin from the one the proxy fetches.**
`app/pricing/page.tsx:9` (reads `NEXT_PUBLIC_API_BASE_URL`) against
`app/api/console/route.ts:47` (prefers `CONSOLE_ORIGIN`)
- Repro: `CONSOLE_ORIGIN=http://127.0.0.1:9 next start -p 3101` (measured on `:3101`).
  `/api/console` returns the 503 panel naming `127.0.0.1:9`; `/pricing` still prints
  `http://127.0.0.1:8788` four times and renders the link
  `href="http://127.0.0.1:8788/?event=evt_syn_06"`. The page states an origin that is not
  where the numbers come from, on the one line whose job is to say where they come from.
- Fix: export one `consoleOrigin()` from a shared module and use it in both, or drop
  `CONSOLE_ORIGIN` and point the test at `NEXT_PUBLIC_API_BASE_URL`.

**D7. The canonical-URL sentence is wrong about the mechanism and its link is dead off
this box.**
`app/pricing/page.tsx:150-161`
- Repro: read `server.py:247-248` (`self.server.server_address`), then
  `grep -n 'self.headers' ticketpath/server.py` (only `content-length`). The canonical URL
  comes from the bind address, never from a `Host` header.
- Why it matters: through any tunnel or reverse proxy the printed canonical and the "Open
  the same state directly on the backend" link point at a loopback address that only the
  operator can reach, and the sentence says a stranger can read it.
- Fix: build the console's canonical URL from a configured public base and have the page
  print that same value; or delete the sentence's mechanism clause and render the backend
  origin as plain text with no link.

**D8. The patch does not compile against the operator's real frontend.**
`app/pricing/page.tsx:3-4, 43`
- Repro: §1.6. `patch -p1` then `tsc --noEmit` gives TS2307 (`SyntheticNotice`), TS2305
  (`DataSource`) and TS2339 (`dataSource` on `Page<Event>`).
- **This blocks applying the patch to the real frontend.** Fix: rebase the patch on the
  frontend-honesty patch (which is where those three exist) and ship them as one ordered
  series, with the ordering written down in `records/FRONTEND-HONESTY-PATCH.md`.
- Also blocking, and separate: applying it with `.env.local` repoints the operator's whole
  app at `:8788` on the next restart, not only `/pricing`. State that in the application
  note, or make the copy's env file demo-only and leave the operator's absent.

**D9. No `sandbox` on the frame and no CSP on the proxy, on a same-origin document.**
`app/pricing/page.tsx:143-147`, `app/api/console/route.ts:91-99`
- Repro: measured `f.contentDocument` reachable from the parent; and the isolated test in
  `/tmp/sandbox_test.mjs` showing `sandbox="allow-forms"` renders the console, keeps
  Recompute working (`capBps=3000` came back), and blocks parent access with
  `SecurityError`.
- Why it matters: containment rests entirely on the console never emitting a script. On
  the operator's real frontend the app origin carries a wallet adapter.
- Fix: `sandbox="allow-forms"` on the iframe; `Content-Security-Policy: default-src 'none';
  style-src 'unsafe-inline'; form-action 'self'` on `/api/console`. Both verified to work.
- This and D4 pull against each other: the sandbox blocks a scripted auto-height. Take
  the sandbox and drop the frame, or set a tall fixed height (see §7.1). Do not trade the
  sandbox away to fix a layout number.

### Smaller, worth fixing in the same pass

**D10. A tracking parameter turns the price into a refusal.** `/pricing` forwards every
parameter (`page.tsx:30-35`) and the proxy refuses any it does not know
(`route.ts:100-114`). `?event=evt_syn_06&utm_source=x` gives a 400 panel. Filter on the
page to the same eight and print one line naming what was dropped.

**D11. `at` is an invented alias.** `route.ts:42`. The console never accepts it and the
page never sends it. Delete it.

**D12. Duplicate keys are last-wins in the proxy and first-wins in the console.**
`route.ts:110` (`set`) against `server.py:246` (`values[0]`). `?event=a&event=b` shows `b`
through the proxy and `a` directly. One word: `append`.

**D13. `[UNAVAILABLE]` is a ninth badge that no legend or test knows.** `route.ts:74`. Add
it to `labels.BADGES` and to the page legend, or use `[REFUSED]` with a distinct sentence
as the console's own error page does.

**D14. The badge legend is a cross-repo copy, and one gloss is already wrong.**
`page.tsx:92-126` copies `labels.py:33-42`. The `[DECLARED]` gloss says "not estimated"
while the console puts that badge on "the posterior mean of the declared Gamma(1, 1)
prior". Fetch the legend from the backend or drop it.

**D15. The checker cannot see the frame, and one of its checks passes on the control.**
All console assertions are HTTP GETs, so it passes 32/32 with the frame hiding half the
console and the phone view showing no price at all; and on `:3000` it reports `pricing
states no price itself` as a pass, because that check only asserts a string is absent and
a 404 page satisfies it. Add one browser assertion (frame height against content height,
and a price visible in the frame at 390), and make the absence check require the route to
be a 200 first. The control on `:3000` is honest and should stay.

**D16. The 503 panel's fix instruction is missing its working directory.** The panel says
`python3 -m ticketpath.server --port 8788`; that only works from the ticketPricing repo
root. One clause.

### What does not block

- The failure panels restate the console's type scale in inline CSS instead of sharing it,
  and `/pricing` makes one extra `getEvents({limit:1})` round trip per render to read the
  data-source label. Both are fine for this deliverable.
- The home page's 390 horizontal overflow is pre-existing and reproduces on `:3000`.
- `.env.local` being gitignored is correct; no secret is in it.

---

## CORRECTION (2026-11-07T18:55Z) — the verdict is superseded, and here is the status of all sixteen

**Scope:** appended to this file, nothing above rewritten. **Measured:** 18:40Z–18:55Z on the copy and
its proxy, at `origin/main` (`8a5e5e6`). Where a status rests on the fixer's own measurement rather than
mine, the row says so.

**The claim this corrects**, the file's own line near the top:

> **VERDICT: FIX-FIRST.** The ranked list and the apply-to-the-real-frontend consequences are in §9.

**What is true now:** the copy passes its own checks — `python3 tools/check_frontend_attach.py` →
**43 passed, 0 failed**, exit 0, run at 18:40Z. Of the sixteen defects, **eleven are closed outright**,
**three are closed with a residue named below**, and **two are open**. The FIX-FIRST verdict is history:
it was true of the copy at 17:50–18:10Z and it is not true of the copy now. The one thing it was right
about that still stands is D8's consequence — nothing has been applied to the operator's real frontend
tree, and whether it should be is a decision in `records/SUBMISSION-PACK.md` (T10), not a defect.

| # | Defect | Status at 18:55Z | The check that shows it |
|---|---|---|---|
| D1 | the opening sentence promises the two outputs the console refuses | **FIXED** | the served page says the console shows "a floor where it supports only a floor, and a band around the figure where it supports one", and names both refusals |
| D2 | the decision-mode sentence says "completed record in hindsight" for a frame that says the opposite | **FIXED** | the phrase is absent from the served page; one state-neutral line replaces it |
| D3 | "the band around it" is false for the binding-cap regime | **FIXED** | the conditional wording is on the page ("where the record supports a band … where the record supports only a floor") |
| D4 | a fixed iframe height hides half the console | **FIXED** | measured here with a browser: frame box **3,383 px over 3,383 px** of content at 1280, **7,143 over 7,143** at 390, the frame's inner viewport equal to its content height, so no nested scrollbar in either case |
| D5 | `back to the decision` loads the app home page inside the frame | **FIXED** | the refusal panel's link is now `<a href="/api/console">back to the decision`, and no root-relative `href` survives in the proxied body |
| D6 | `/pricing` names a different origin from the one the proxy fetches | **FIXED** | one function reads the origin for both the proxy and the page, and the footnote names the variable it read. The dead-override capture on a scratch port is the fixer's measurement |
| D7 | the canonical-URL sentence is wrong about the mechanism and its link is dead off-box | **FIXED** | the page now states the address is built from the address its own server is bound to, "not from a request's host header", and offers the link only when a probe answers. The dead-link half is the fixer's measurement |
| D8 | the patch does not compile against the real frontend | **RESIDUE: closed as a compile question, open as a decision** | the fixer's: `tsc --noEmit` exit 0 in scratch copies of the real frontend with both patches in series, `diff -rq` identical to the copy, `02` alone failing on the three errors that prove the order matters, and the concatenated patch applying in one `patch -p1` and typechecking. Not re-run by this pass; nothing written to the real tree |
| D9 | no `sandbox`, no CSP, on a same-origin document | **FIXED, with a stated deviation** | served frame carries `sandbox="allow-forms allow-same-origin"`; the proxy serves `content-security-policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'self'`. The extra token is the fixer's judgement call, argued from a measurement: a script appended from the parent did not run, and the proxy refuses script by policy |
| D10 | a tracking parameter turns the price into a refusal | **OPEN** | `?event=evt_syn_06&utm_source=x` through the proxy still returns 400 with an `[UNAVAILABLE]` panel naming the unknown parameter. Deliberately not done, and it is six lines on the page |
| D11 | `at` is an invented alias | **FIXED** | `?at=…` through the proxy returns 400: the alias is gone from both sides |
| D12 | duplicate keys are last-wins in the proxy and first-wins in the console | **FIXED** | `?event=evt_syn_03&event=evt_syn_02` selects `evt_syn_03` through the proxy and directly: one rule on both sides |
| D13 | `[UNAVAILABLE]` is a ninth badge no legend or test knows | **OPEN** | `'[UNAVAILABLE]' in labels.BADGES` → `False`; the badge set is the eight. The page tells the truth about it instead — it is the page's badge, not the engine's — and the backend file was outside the fixer's scope |
| D14 | the legend is a cross-repo copy and one gloss is wrong | **RESIDUE: gloss fixed, copy still a copy** | the `[DECLARED]` gloss no longer says "not estimated"; the checker's badge list is now imported from `ticketpath/core/labels.py` rather than copied and asserts nine of nine, so the copy is checked rather than trusted |
| D15 | the checker cannot see the frame, and one check passes on the control | **RESIDUE: false pass fixed, browser assertion not added** | every `/pricing` check is now gated on the route answering 200, so the absence check that used to pass on the control now fails on it (36 failed there, the fixer's measurement). No browser assertion was added; the checker's docstring now says what it cannot see and quotes the measured frame numbers |
| D16 | the 503 panel's fix instruction is missing its working directory | **FIXED** | `app/api/console/route.ts:155` now reads "Start the backend from the ticketPricing repository root: …", which is where that module imports from |

**What this table is not.** It is not a re-review. Nothing in this file's reasoning about the *defects*
is withdrawn: every one of them was real where it was measured, and the two that remain open are open on
the tree as it stands. What changed is the copy.
