# Open decisions for the operator

Seven. Each one changes what gets recorded, and none of them can be settled by editing a
file in this directory. Ordered by how soon the clock forces them, not by importance.

---

## V1 — Where the video is recorded, and by whom the voice is spoken

**Blocking. This is the only decision that can stop the video existing.**

Measured on this machine at 07:33–07:35Z: no `ffmpeg`, no `arecord`, no `sox`, no OBS on
`PATH`; the `ffmpeg` that Playwright bundles accepts only `webm` and encodes only VP9, so a
webm→mp4 copy fails. Playwright with a full Chromium **is** installed and did produce a real
720p `.webm` of a page at 07:32Z.

**Options**

1. **Record on his own machine** with a normal screen recorder and the built-in microphone.
   The URLs are served over the LAN or run locally from the clone. Needs nothing installed
   here. *(Recommended.)*
2. Record the screen here, silently, and record the voice elsewhere; then mux. That needs a
   toolchain this box does not have, so it becomes an install he did not ask for. Not
   recommended inside the event window.
3. Captions only, no voice. The script reads as captions over the same shots. Loses the
   "demo, not presentation" tone the rules ask for and costs most of beat 1's warmth.

**What it changes:** whether `REHEARSAL.md` §3 passes 2–4 happen on his desk or over the LAN,
and whether Pass 5 can measure the exported file at all.

---

## V2 — The console's own number, and the defect under it

The console recommends **1.38 SOL** at the pinned state. The same page's own record puts the
ceiling at **1.25 SOL** for the artefact's face and cap. The gap is 130,000,000 lamports, and as
of 08:00Z the page **confesses it in its own words**: "The recorded recommendation of 1,380,000,000
lamports is above that ceiling" and "This page computed its own number under the event's cap of
1,500 bps and face of 1,200,000,000 lamports, which are the store's, not the file's."

**Options**

1. **Do not speak the figure; let the screen carry it, and keep the page's confession in frame.**
   This is what `SCRIPT.md` beat 3 and `CHOREOGRAPHY.md` shot 6 now do. The beat still lands,
   because the argument is the refusal and the label, not the number. *(Recommended.)*
2. Fix the console so a recommendation cannot exceed its own record's ceiling, then speak the
   number. Stronger, but it is a code change in another session's tree, and it changes what the
   page says — which changes the shot list too.
3. Say the 1.38 and say nothing about the gap. This is the one option that can cost the entry: the
   page contradicts the spoken claim on the same frame.

**What it changes:** whether beat 3 has a spoken number, and whether shot 6 must show the
confession.

---

## V3 — Which surface is the product's face in the first 30 seconds

**Measured at 07:49Z, and the answer moved.** The rebuilt frontend typechecks clean (exit 0 over
277 files) — and the server is still answering with the **pre-rebuild bundle**, which prints
`Enforced on-chain`, four `tx` links onto signatures that exist on no cluster, and a
`Mock data — set NEXT_PUBLIC_API_BASE_URL` banner the submission pack forbids on any frame. The
tree on disk has fixed all three; the tree on screen has not.

**Options**

1. **Serve the rebuilt build first** (`npm run build && next start` from a copy, not the live dev
   tree), then shoot the app. Best `Design` score and the only surface that looks like a product.
   Cost: a build in a tree another session is editing.
2. **Fallback B** — the console and the generated charts for shots 1–3. Needs no server, is
   labelled in its own text, and costs the product's face but not the argument.
3. **Shoot the served (stale) bundle and crop hard** — never let the `On-chain` card, the `tx`
   chips or the banner into frame. Cheapest, and one stray scroll shows a claim the project's own
   capabilities file says is false.

**Recommendation: option 1 if a build can be served by T-minus 4 hours; otherwise option 2.**
Option 3 is the one to avoid, because the failure mode is a judge seeing `Enforced on-chain` on a
page that never reads the chain.

---

## V4 — The capture date against the no-desktop rule

MLH's cheat-check page instructs a reviewer to ask "Are their Timestamps over the weekend
when they run the demo in any video/screen captures?" Our submission pack forbids a desktop,
a terminal and a notification on any frame.

**Options**

1. **No system clock.** The console's `[DEVNET]` line prints an instant inside the window,
   the end card carries the dates, and the video is published during the event.
   *(Recommended — it is what the plan does now.)*
2. A one-second open on the desktop clock, then cut to the product. Strongest evidence,
   breaches the pack's rule, and puts a machine layout in frame.
3. A title card with the date typed on it. Weakest: a typed date is a claim, not evidence.

**What it changes:** three seconds of the opening and one line of the end card.

---

## V5 — The product is SeatPass; the repository is `ticketpath`

The end card must carry a URL that resolves. The repository's remote is
`andy1245-rgb/ticketpath`, and renaming it is a push-adjacent action that is his alone.

**Options**

1. Keep the repo name and put `ticketpath` on the card. The mismatch is visible for two
   seconds and explainable in the description. *(Recommended, and zero risk.)*
2. Rename the repo to `seatpass` before recording. Cleaner, and it breaks every link already
   written in the record.
3. Put both names on the card. Clutter at the exact moment the card should be cleanest.

---

## V6 — One voice or two

`records/findings/17` risk R4 names MLH's own cheat-check question — "Is a solo hacker
making a really advanced project in a single weekend?" — and says the mitigation is a video
that is explainable, not smaller. A second speaker on the chain beat answers it directly.

**Options**

1. One voice throughout. Simplest to record and to time.
2. Two voices: beat 4 in the teammate's voice. Costs nothing in words and answers R4 with a
   fact rather than a claim.
3. Two voices, splitting at beat 3. More natural, more rehearsal.

**Recommendation:** option 2 if the teammate is available for twenty minutes; otherwise 1.

---

## V7 — Does the Token-2022 sentence stay

Beat 5 spends about four seconds on a measured limitation: on a one-unit ticket a Token-2022
transfer fee takes the whole ticket, which is why the artist fee is not in the build.

**Options**

1. Keep it. It is the strongest `Learning` evidence in the entry — a measured dead end is
   what "did the team stretch themselves" looks like — and it pre-empts the obvious judge
   question "where is the fee feature".
2. Cut it and spend the four seconds on the devnet beat. Safer for pace, and it removes the
   entry's most distinctive technical finding from the only place a judge will hear it.

**Recommendation:** keep it.

---

## One thing that is not a decision but is missing

The board's record of the operator decisions taken at 07:08Z is **truncated**: item (6) ends
mid-sentence at "Feature 10: the…", and there is no item (4) in either entry. Nothing in this
package depends on either, so nothing here is blocked. If either decision touched the product
name, the demo surface or the video, it should be restated.
