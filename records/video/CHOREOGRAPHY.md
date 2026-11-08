# Choreography — a cursor walkthrough of the site

Built for `SCRIPT.md` at **125 words per minute**. Total **1:56.5**, three and a half seconds
inside the 2:00 cap. Every frame is a page of the app. No console page, no generated slates, no
cards, no image montage. A visible cursor moves, hovers and clicks the way a person does.

---

## 0. The one dependency that decides whether this film can exist

Read from the running site on 2026-11-08:

| Page | What it prints today | What the script says |
|---|---|---|
| `/rules`, "Enforcement today" | "The cap program is written. **It is not deployed on any cluster**, so nothing is enforced at runtime today." `programDeployed false` | "This program is deployed on Solana devnet" |
| `/pricing`, "The pricing model" | "**No model is registered.**" `available false` | "The console recommends a primary price as a floor" |

Those two sentences are correct about the *build's own knowledge*: no backend is configured, so the
app asked no cluster and read no engine. They are false about the world. On camera they would
contradict the voice inside the same frame, which is the exact failure this package has spent four
review rounds avoiding.

**So the walkthrough needs the app to render two things it already has a slot for:**

1. `/rules`, "Enforcement today" reads `records/devnet-artefacts.json` when it is present and prints
   the program id, the cluster, the verification instant, the signature, the slot and the block time,
   with its existing `programDeployed` field telling the truth.
2. `/pricing`, "The pricing model" reads the fixture store's engine output and prints the
   recommendation and its refusals, or the engine is run in-process the way the console does.

Both pages already have the section, the layout and the honest-when-empty state. This is wiring a
data file to a panel that exists, not new design. Until it lands, shots 4, 5, 6 and 9 below cannot be
recorded, because their frames would say the opposite of their voice.

**If it does not land before the deadline**, the honest fallback is not "shoot it anyway". It is the
softened script in §5: the record claim survives on `/events` and `/tickets`, and the chain claim
moves out of the voice and into the description, where the two signatures can be pasted as text.

---

## 0.1 The badge, the heading, and the cursor

**One plate, and only where a number is synthetic.** `SYNTHETIC FIXTURES`, 22 px, bottom-left, 2.04%
of a 1080-tall frame, on every frame whose figures come from the fixture store. It becomes
`DEVNET · REAL TRANSACTION · SIGNATURE RESOLVES` on exactly the frames where `/rules` prints the
artefact's signature, and only those.

**One heading per section, and nothing else.** Top-left, small, mono, muted, present for the first
two seconds of each shot then fading out: `the record`, `the ticket`, `the price`, `the cap`. That is
the whole caption layer. No verbatim captions, no lower thirds, no explanatory paragraphs. Four
two-word headings across two minutes is subtle by construction.

**The cursor is the narrator.** It is visible on every shot, it moves in curves rather than straight
lines, it decelerates before it arrives, it pauses on a control before clicking, and it rests
mid-frame during the passages that need reading. It never teleports and it never crosses a click
target without slowing. One click per shot at most, and every click lands on something that exists.

**What a viewer should feel:** someone opened the site and showed it to them. Not a film about a site.

---

## 1. The shot list

### Shot 1 · `0:00.0 → 0:19.7` · beat 1 · `/` · **SYNTHETIC**

- **At rest:** the hero, `The ticket that can't be marked up.` readable without scrolling.
- **Cursor:** enters from the lower centre-right at walking speed, curves up to `Browse events`,
  hovers it, and the button responds. It does not click yet: the first sentence of the film is about
  the problem, not the navigation.
- **Heading:** `SeatPass`.
- **Must be legible:** the hero line and the three promises under it. That is what the voice is
  describing while the cursor waits.

### Shot 2 · `0:19.7 → 0:31.5` · beat 2, first half · `/events/[slug]` · **SYNTHETIC**

- **Action:** the cursor clicks `Browse events`, the events grid appears, it moves to the first
  event card and clicks it.
- **At rest:** the event page, `Face value from` and `Tickets issued` tiles in frame.
- **Heading:** `the record`.
- **Cursor:** rests low and right while the price chart is read, so it never covers the line.

### Shot 3 · `0:31.5 → 0:43.7` · beat 2, second half · same page · **SYNTHETIC**

- **Action:** one scroll of about 300 px, cursor drifting with the content, to `Issued tickets`.
- **Then:** the cursor settles on one ticket row and hovers it, which is the whole gesture: this is
  the ticket the next shot opens.
- **Heading:** `the ticket`.

### Shot 4 · `0:44.7 → 0:53.8` · beat 3, first half · `/tickets/[id]` · **SYNTHETIC**

- **Action:** the click lands and the ticket page opens. The cursor moves up and away from the
  content, then rests.
- **In frame:** the per-ticket record, `Face value`, `Last sale price`, `Peak price`, `Wallets held
  by`.
- **Heading:** `the price`.
- **Requires:** §0 item 2, or the voice and the frame disagree.

### Shot 5 · `0:53.8 → 1:02.9` · beat 3, second half · `/pricing` · **SYNTHETIC**

- **Action:** the cursor moves to the header's `Pricing and data` link and clicks it.
- **In frame:** the recommendation and, beneath it, the refusals with their reasons.
- **Heading:** `the price`.
- **Cursor:** rests off the text block for the whole sentence about what the engine refuses.

### Shot 6 · `1:02.9 → 1:31.2` · beat 4 · `/rules` · **DEVNET** ← the plate switches here

- **Action:** the cursor clicks `How the cap works` in the header, then scrolls to `Enforcement
  today`.
- **In frame:** the predicate, the four arithmetic lines, then the artefact: program id, cluster,
  verification instant, signature, slot, block time.
- **Heading:** `the cap`.
- **This is the shot the film exists for.** It is a real page, a real scroll, a real cursor, and the
  numbers on it are the ones in `records/devnet-artefacts.json`.
- **Requires:** §0 item 1. Without it this page prints "not deployed" and the shot is impossible.

### Shot 7 · `1:31.2 → 1:52.4` · beat 5 · `/pricing` · **SYNTHETIC**

- **Action:** the cursor returns to `Pricing and data` and scrolls to the panel that separates what
  the deployment computes from what it only describes.
- **In frame:** that panel, plus the honest empty states for what is not built.
- **Heading:** `what is not built`.
- **Cursor:** still, low, out of the text.

### Shot 8 · `1:52.4 → 1:56.5` · end

- **Action:** the cursor drifts to the footer and stops. No cut to a slate.
- **In frame:** the site's own footer, with `Built at the Solana x MLH hackathon.` visible.
- **One line, bottom-centre, in the same mono as the plate:** `github.com/andy1245-rgb/ticketpath`.
- **Hold 4.1 s**, the last 3 silent.

---

## 2. Before you roll

**The app**

1. `npm run typecheck` passes, and the build you record is the rebuilt one. Measured 11:0xZ: `:3000`
   serves the pre-rebuild bundle (`Custody trail`, `Enforced on-chain`, `Every transfer is recorded
   on-chain`, a `Mock data` banner). Serve a build and re-check those four strings are gone.
2. **The two panels in §0 render the artefact and the engine.** Check by `curl` on the built site:
   `/rules` must contain the program id and a signature, `/pricing` must contain a recommendation.
   If either prints "not deployed" or "no model", do not record the shot.
3. No frame shows a 404. Click only controls that exist: `Browse events`, an event card, a ticket
   row, and the two header links.
4. The ticket chosen for shots 3 and 4 is `tkt_00077`: `Valid`, five ledger rows, newest row dated
   inside the event window.
5. Never in frame: the `Open the listing form` panel, the `Transfer restricted` card, or any `tx`
   link. All three assert something the build does not do.
6. Text that must be read sits at or above 2% of frame height. Capture at 1280 CSS px with 2x device
   scale, crop to 16:9 from the sides only.

**The cursor and the take**

7. Cursor visible on every shot, moving in curves, slowing before a target, pausing before a click.
8. One click per shot, and the destination already verified to exist.
9. No address bar, no tab switching, no bookmark bar, no notification, no dock.
10. Every shot arrives at its start state before its timecode. Nothing loads on camera.

**The frame**

11. One plate per frame, and the plate switches exactly once, at 1:02.9, and back at 1:31.2.
12. Four headings, two words each, fading in and out. No other text layer.
13. No terminal, no console page, no desktop, no second monitor.

---

## 3. Fallback, if the two panels are not wired

Do not shoot the shots that would contradict their own frame. In order of preference:

1. **Record shots 1 to 5 and 7** (the record, the ticket, and what the pricing page says), and put the
   two signatures and their slots in the submission description as text. The film then makes claims 1
   and 4 on screen and claims 2 and 3 in writing.
2. **Move the chain beat's seconds into the record beats.** The film becomes a slower, more thorough
   walkthrough of the record, which is honest and is the `Learning`/`Completion` story.
3. The one thing not to do is film `/rules` while the voice says "deployed".

---

## 4. What changed from the card version, and why

- **The two signature cards and the end card are gone.** The operator asked for a walkthrough of the
  site with no generated imagery. Every frame is now a page.
- **The console page is gone** for the same reason: it is a second surface with a different look, and
  the walkthrough stays on the product's own site.
- **The cursor is visible**, reversing the earlier "hidden, not merely still" rule, because the
  operator asked for a human experience rather than a scripted scroll.
- **The caption line is now four two-word headings**, because a full burned caption competed with the
  product for attention and the operator asked for subtle.
- **The signature evidence moves from a card to `/rules`**, which is the site's own page for exactly
  this, once its "Enforcement today" panel reads the artefact.
