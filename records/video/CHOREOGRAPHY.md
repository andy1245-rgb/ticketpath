# Choreography — shot by shot

Built for `SCRIPT.md` at **125 words per minute**. Total **1:55.0**, five and a half seconds inside the
2:00 cap. Every time below is a cut point, not a suggestion: record to these and the edit is
assembling, not deciding.

## 0. The badge system, and the one rule a viewer can test

| Badge | Wording, exact | Where | On which shots |
|---|---|---|---|
| Synthetic | `SYNTHETIC FIXTURES` | bottom-left plate, 40 px from both edges, 20 px mono, solid background, squared left edge | shots 1–5 and **shot 9** |
| Devnet | `DEVNET · REAL TRANSACTION · SIGNATURE RESOLVES` | same position, a 6 px leader rule on the left so it differs in shape and not only in colour | shots 6–8 |

**The rule a viewer can test without knowing anything about this project:** `SYNTHETIC
FIXTURES` means no number on that frame is a market fact; `DEVNET … SIGNATURE RESOLVES` means
the signature printed on that frame is real and lookupable. That is why the Devnet plate names
the test rather than asserting a status: the console's slot presents a *recorded* artefact and
does not re-read the chain, so "verified" on that page is the file's own hash and not a live
check.

**The switch happens once, at 1:03.9, and it switches back at 1:32.7.** Shot 9 is a
**SYNTHETIC** frame: it holds the console's `What the engine refuses` block, every number in
which comes from the fixture store, and it carries no signature. A Devnet plate there would be
a real-data stamp on a fixture frame for the length of the closing argument.

The plate stands alone; it is not backed by a spoken sentence containing the full wording. The
voice says "these screens run on generated fixtures, labelled here", which is true of the
frame, and the plate says which class the frame is. Earlier drafts of this file claimed the
full sentence was also spoken and printed on the end card. It is not, and it does not need to
be: the plate plus the voice clause is the label.

Badge assets: `assets/cards.html?card=badges` and `?card=badges2`, captured clipped to the
plate at 2× device scale (`REHEARSAL.md` §2), so they are the same pixels on every frame.

## 0.1 Two overlay layers the edit adds

**The lower third.** Four lines, 3–4 s each, same mono as the badges, bottom-centre above the
plate:

| At | Text | Purpose |
|---|---|---|
| 0:49.0 | `the console's own tag: [UNVALIDATED]` | names the warning on the number the voice deliberately does not say |
| 1:03.9 | `synthetic → devnet` | makes the switch visible as well as audible |
| 1:24.0 | `refused: slot 519846008` | gives a judge a mnemonic; the full signature is on the card at 1:11.6 |
| 1:50.9 | `github.com/andy1245-rgb/ticketpath` | the URL, before the end card |

The lower thirds exist because every takeaway in this video is spoken, and a judge watching
muted would otherwise get a scrolling ticket app and no argument. They are removable; the
video works without them and works better with them.

**The cursor.** Hidden, not merely still. A visible pointer on a static panel reads as a screen
waiting for something.

---

## 1. The shot list

### Shot 1 · `0:00.0 → 0:19.7` · beat 1 · **SYNTHETIC**

- **Surface:** `http://<host>/tickets/tkt_00077` — chosen because its status is `Valid` (not
  `Listed for resale`), it has five ledger rows, and its newest row is dated `2026-11-06T18:00Z`,
  inside the event window. Every other fixture ticket's trail is October or earlier, which argues
  against the publish date in a cheat check. The date is still a fixture, and the plate says so.
- **Where the shot starts depends on which build is serving, and that is a measurement.** `curl`
  the page and read it: if it prints `Ownership trail` and `BUNDLED MOCK DATA`, the rebuilt tree is
  being served — start at the top of the page so the app's own note is in the first three seconds.
  If it prints `Custody trail` and a `Mock data — set NEXT_PUBLIC_API_BASE_URL` banner, the
  pre-rebuild bundle is being served — start **below** the banner, because §1.4 forbids that banner
  on any frame, and let the plate carry the label. Measured at 07:49Z: the tree typechecked clean
  and the server was still answering with the pre-rebuild bundle. Re-measure before the take.
- **Choose the ticket for two properties:** the status badge must **not** read `Listed for
  resale` (no marketplace exists, `lib/capabilities.ts`), and the ownership trail must have at
  least three rows so shot 2 arrives on a populated trail.
- **Movement:** one slow scroll of about 200 px over 19 s, header to price path. No cursor. No
  click.
- **Must be legible in the first 3 s:** the product name in the voice and the app's own note.
  The winner sample puts the demo signal at 3.9 s; ours is at 0.0.
- **Do not:** hover a `tx` chip, click the mint address, let the frame reach the
  `Transfer restricted` card (a fixture boolean, `inputs/frontend-inventory.md` §7 item 2), or
  let it reach the `Open the listing form` link (a marketplace affordance that does not exist).

### Shot 2 · `0:19.7 → 0:31.7` · beat 2, first half · **SYNTHETIC**

- **Surface:** same ticket page, scrolled so `Ownership trail` fills the frame.
- **Note the string:** the rebuild renamed `Custody trail` to `Ownership trail`. Check the
  title on the frame before the take; if it has changed again, the shot is still the same shot.
- **Voice over it:** "Every resale is a transaction, with a price and a wallet. One ticket
  becomes a path…"
- **Framing rule:** the plate sits over the trail's lowest visible row and the `tx` chips are
  at the frame edge or out of it. They link to signatures that exist on no cluster, and a chip
  on camera is an affordance whether or not it is clicked.
- **Cut on the word "transaction"**, the word the shot is proving.

### Shot 3 · `0:31.7 → 0:44.7` · beat 2, second half · **SYNTHETIC**

- **Surface:** `http://<host>/organizer?event=<event>` — now headed `For organizers`, with a
  `Resale record` section. Check both strings on the frame.
- **At rest:** the stat tiles, then `Markup distribution`.
- **Movement:** one cut, then a 60 px drift so all six distribution rows are in frame by the end
  of the beat.
- **The voice says the honesty line here** while fixture numbers are on screen.
- **Do not show** `Where tickets ended up`. Its region column prints invented locations as if
  wallets had volunteered them (`inputs/frontend-inventory.md` §7 item 6), and the region
  question is open (`records/F-decision-log.md` Q4).

### Shot 4 · `0:45.7 → 0:54.8` · beat 3, first half · **SYNTHETIC**

- **Surface:** the console, pinned:
  `http://<host>:8788/?event=evt_syn_02&tier=tier_stg_general&capBps=1500&tau=0.2`
- **At rest:** the fixture strip at the top, the tier line, the `[EXACT]` ceiling line, then
  `[UNVALIDATED] Recommended primary price`.
- **Record the console at a 1280 CSS px viewport with 2× device scale**, which puts 15 px body
text at 2.1% of frame height — the legibility floor in §2. At that size the fixture strip sits at
the top of the document and the `[EXACT]` ceiling line is roughly 1,178 CSS px further down, so
the two **cannot** share a 1080-tall frame. Do not solve that by zooming out: at 85% the type falls
to 1.25% and a judge cannot read the number the shot exists for.
- **So the shot is a scroll, not a still.** It opens on the fixture strip and the tier line, drifts
  down about 60 px per second, and arrives on the `[EXACT]` ceiling line by 0:50. Both requirements
  hold: the strip is on screen at the start of the shot, and no number is ever below the legibility
  floor. The plate is on the frame throughout.
- **Movement:** the scroll above, then hold two seconds on the ceiling line. Two seconds is a
  beat; four is a stall.
- **The voice does not say the number** ("the highest price this tier has seen" plays over
  it), and the lower third at 0:49.0 names the tag.
- **The console's `h1` must not be in frame.** It reads `Ticketpath — organizer pricing
  console`, and it is the largest text below the banner: a judge reading a different product
  name on the surface carrying the strongest evidence is the cheapest way to lose the point the
  shot is making. Crop to the decision panel.

### Shot 5 · `0:54.8 → 1:03.9` · beat 3, second half · **SYNTHETIC**

- **Surface:** same console page, scrolled to `What the engine refuses`.
- **In frame: all six rows**, in the console's own order — `not_identified`, `no_demand_response`,
  `no_fee_model`, `cap_mass_dominates`, `no_upper_bound`, `insufficient_events`.
  `cap_mass_dominates` is not optional. The voice gives one reason
  for the missing upper end (the cap hides the top) and another for the missing probability (no
  recorded listing). If the frame shows `no_upper_bound` without the row that explains it, the
  frame and the voice contradict each other.
- **Do not press** `Show the refusal`. It runs the simulated state machine and the panel reads
  `0 arms shown` until pressed; an empty panel on camera reads as broken, and §1.4 forbids it on any
  frame. Measured: the simulation panel ends at y≈2967 and the chain slot begins at y≈2982. Scroll
  so the panel's bottom edge is off-frame, or press the button before the take and record the panel
  populated.

### Shot 6 · `1:03.9 → 1:11.6` · beat 4, first half · **DEVNET** ← the plate switches here

- **Surface:** the console with the recorded instant pinned:
  `http://<host>:8788/?event=evt_syn_02&tier=tier_stg_general&capBps=1500&tau=0.2&asOf=2026-11-07T18:34:29.183Z`
- **In frame:** the `[DEVNET]` slot with its recorded verification line, the signature, the
  slot, the cluster, **and the sentence that reconciles this frame with shot 4**: "This page
  computed its own number under the event's cap of 1500 and face of 1200000000, which are the
  store's, not the file's."
- **That sentence is load-bearing.** Shot 4 shows face 1.20 SOL at 1,500 bps; shot 7 shows face
  1.00 SOL at 2,500 bps. Both are legible. Without the reconciling line, a judge sees one ticket
  with two faces.
- **The voice says nothing about face or cap on this frame.** Those numbers belong to the devnet
  record and are spoken over shot 7, which prints them. Saying them here, over a page computing
  1.20 SOL at 1,500 bps, is the one way to make two right numbers look like a contradiction.
- **The switch is spoken and shown on the same frame:** "Everything before this was generated.
  This signature is not." Lower third: `synthetic → devnet`.
- **Check before roll, with the flag that actually moves.** `chain.state` stays `verified`
  whatever the instant, because it describes the artefact file; `chain.matchesCurrentQuote` is the
  flag that flips. Measured with an `asOf` a day earlier: `state verified | matches False`. The
  assertion before the take is `state == "verified" and matchesCurrentQuote is True`, and it can be
  checked without a server:

  ```bash
  python3 tools/guidance.py --event evt_syn_02 --tier tier_stg_general \
      --as-of 2026-11-07T18:34:29.183Z --cap 1500 --tau 0.20 > /tmp/payload.json
  python3 -c "import json; c=json.load(open('/tmp/payload.json'))['chain']; \
      print(c['state'], c.get('matchesCurrentQuote'), c.get('signature'))"
  ```
- **Do not read aloud** the verification-instant line if it still prints a bare `None`
  (`records/STATE-OF-PROJECT.md` §A6 item 1). Keep the crop above it.

### Shot 7 · `1:11.6 → 1:21.7` · beat 4 · **DEVNET** · asset

- **Asset:** `assets/cards.html?card=admitted`, captured at 1920×1080.
- **Text:** `ADMITTED`, `1,250,000,000 lamports`, the `[EXACT]` arithmetic, the program's log
  line, the full signature, slot 519845933, `api.devnet.solana.com`, and
  `Boundary test run by the team, not a customer purchase.`
- **Voice:** "The record: face one SOL, cap twenty five hundred basis points. A test transfer
  priced at one point two five SOL executes." The record's parameters are spoken here, on the card
  that prints them, and nowhere else.

### Shot 8 · `1:21.7 → 1:31.7` · beat 4 · **DEVNET** · asset

- **Asset:** `assets/cards.html?card=refused`.
- **Text:** `REFUSED`, `1,250,000,001 lamports`, `custom program error 0x177a · 6010
  E_CAP_EXCEEDED`, the log line, the full signature, slot 519846008.
- **Voice:** "One lamport higher, and the program refuses it, error six zero one zero… the chain
  refuses it, not the app."
- **Why a card and not Explorer:** `records/SUBMISSION-PACK.md` §1.4 forbids a terminal or an
  Explorer page on any frame. The card keeps the signature verifiable and the frame clean; the
  same two signatures go in the submission description.

### Shot 9 · `1:32.7 → 1:50.9` · beat 5 · **SYNTHETIC** ← the plate switches back

- **Surface:** the console's `What the engine refuses` block, held. **The block, not the
  `[UNVALIDATED]` badge** — the block is what prints "The model is not fitted", which is the
  sentence the voice is making; the badge says unvalidated, which is a different claim.
- **The plate is SYNTHETIC.** Every number on this frame comes from the fixture store and there
  is no signature on it.
- **Voice:** the whole "what is not built" list.
- **Why it exists:** `Completion` is one of four equally weighted criteria, and the rules tell
  teams to present unfinished work (`inputs/rules-verified-2026-11-08.md` §4).

### Shot 10 · `1:50.9 → 1:55.0` · end card

- **Asset:** `assets/cards.html?card=end`.
- **Four lines, exactly** (`SCRIPT.md` §1 beat 5). No plate: the card carries no figure and no
  signature.
- **Hold 4.1 s**, of which the last 3 s are silent. No music, no fade, no logo animation.
- **Check the URL resolves** before the take and again after any repository rename.

---

## 2. Before you roll: the state checklist

**The frame's own rule, measured, not a preference.** Nothing that carries the argument may be
smaller than **2% of frame height** once captured. The console's body text is 15 px and its
`code` is 13 px; at 1920 CSS px that is 1.2–1.4%, and a judge on a laptop will not read it.
Record the console at a **1280 CSS px viewport with 2× device scale** and crop to the decision
panel, which puts the same text at 2.1%. Check it on a captured frame, not on the page.

**The app (shots 1–3)**

1. `npm run typecheck` passes. It did not at 07:31Z: three call sites passed the wrong props to
   `PriceHistoryChart`. The tree is being rebuilt while this is written — **re-measure, do not
   assume either way**.
2. The chart may or may not draw the dashed cap rule and the `Cap … SOL` chip, depending on
   whether the rebuild has reconciled `capCeilingLamports`. **Look at a captured frame before
   you describe any line.** If it draws, the beat gets stronger and the script may name it; if
   it does not, never say "this dashed line is the cap".
3. The app's own `dataSource` note is in frame for shot 1, and the plate is on every app
   frame regardless.
4. No 404 is reachable by a stray click. At 07:31Z the header's `Events`, `How the cap works`,
   `Sign in` and `Browse events` all landed on `Not found`. Re-check the links before shooting
   the header; if they still 404, start the shot below them and bring the data-source note into
   frame another way.
5. The ticket in shots 1–2 is not badged `Listed for resale`, and the frame never reaches the
   listing panel.
6. One window size for all three app shots: 1280 CSS px wide at 2× device scale, cropped to
   16:9 from the sides only, never top or bottom.

**The console (shots 4–6, 9)**

7. The backend runs and `GET /` returns 200 with the fixture strip in the body.
8. The pinned URL returns the `[EXACT]` line and the `[UNVALIDATED]` recommendation. If another
   session edited the label text, re-read the frame and change the script rather than the screen.
9. The `asOf` URL renders the slot verified **and** the reconciling sentence about the store's
   face and cap is legible.
10. The `h1` `Ticketpath — organizer pricing console` is cropped out of every console shot.
11. Nothing on the page is clicked during a take.

**The chain (shots 6–8)**

12. Both signatures on the cards match `records/devnet-artefacts.json` character for character.
    Paste from the file; never retype.
13. Both still resolve on `api.devnet.solana.com` before the take: the admitted one with
    `err: null`, the refused one with `InstructionError [0, Custom 6010]`.
14. The program id on the card matches the artefact.

**The frame**

15. No terminal, no desktop, no dock, no notification, no second monitor, no bookmark bar.
16. No crop that removes the fixture strip from a console shot, or the plate from an app shot.
17. The capture is made inside the event window: the event closes 18:00Z on 8 November
    (`inputs/rules-verified-2026-11-08.md` §3).

---

## 3. The card text, exact

`assets/cards.html` is the source of truth, and both signatures in it are the full base58
strings from `records/devnet-artefacts.json`. A truncated signature on screen is not checkable,
and checkability is the point of the shot. Rendered at 1920×1080 and measured at 07:55Z: no
overflow, no wrap, `scrollHeight` equals `clientHeight` on all cards.

**ADMITTED**

```
ADMITTED
1,250,000,000 lamports
face 1.000 SOL × (10,000 + 2,500) ÷ 10,000  =  exactly the cap, integer arithmetic
the program's own log line: cap admitted price=1250000000 face=1000000000 cap_bps=2500
signature  E5RCrLwWikWCdHSd5MfqEBowXsmLn2n9fwYjnSwn8NhPi9j7weahbuRhgofu8ca8MVXzQUbvPrJqENDLNab7pJf
slot       519845933
program    5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva
cluster    api.devnet.solana.com
Boundary test run by the team, not a customer purchase. Public: the signature resolves on devnet.
```

**REFUSED**

```
REFUSED
1,250,000,001 lamports
custom program error 0x177a · 6010 E_CAP_EXCEEDED
the program's own log line: cap exceeded price=1250000001 face=1000000000 cap_bps=2500
signature  22dqSriig968nx8aA3YaFVt4CErgNbkwvxFtDKn2MWpcCdnA2KQhFYvhwTWZSpP64wzQjoBeMUKEZLRW1e7jKe79
slot       519846008
program    5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva
cluster    api.devnet.solana.com
Boundary test run by the team, not a customer purchase. Public: the signature resolves on devnet.
```

**END**

```
SeatPass
Pricing from the resale record. Capped on chain.
Pricing layer built at the MLH Solana Hackathon · 6–8 November 2026
github.com/andy1245-rgb/ticketpath
```

---

## 4. Fallback B — if the frontend is not ready

The app is being rebuilt by another session while this is written. If it is not recordable at
capture time, shots 1–3 come from surfaces that are already stable and the argument survives:

| Beat | Fallback surface | What is lost |
|---|---|---|
| 1 | the console's tier and ceiling lines | the product's face; the number still lands |
| 2 | `docs/charts/hops-and-holding.svg` and `markup-vs-time-to-event.svg`, generated, verified, and labelled SYNTHETIC in their own text | the ownership-trail story; the record story survives |
| 3 | unchanged — it is already the console | nothing |

Discipline for that path, and it is not optional:

- the charts render their own `SYNTHETIC` label, the dataset name and the run id; **do not crop
  them out**, because on that path they are the only label on screen;
- the agent counts are spoken as agents, never as people, and price paths are never called
  observed prices (`records/findings/32` §2);
- the plate stays SYNTHETIC for all three shots, and the first Devnet frame is still shot 6.

**Fallback C — if the console will not run.** The `[UNVALIDATED]` beat can be carried by the
card assets alone, and shot 6 can be the artefact rendered as a card. Last resort: it removes
the only frame where a live page computes something, and it is a different, weaker video rather
than the same one.
