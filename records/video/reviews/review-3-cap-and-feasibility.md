# Review 3: the 2:00 cap, measured, and whether every shot can be recorded

**Reviewer:** third independent pass. I did not write the script, the choreography, the cards or
the console. I wrote nothing outside `records/video/reviews/` and a scratch directory, started no
server, installed nothing, and edited nothing in either tree.

**Read:** `SCRIPT.md`, `CHOREOGRAPHY.md`, `REHEARSAL.md`, `OPEN-DECISIONS.md`,
`COLLISIONS-AND-STATE.md`, `inputs/rules-verified-2026-11-08.md` (§1, §3, §5, §7),
`inputs/winner-video-research.md` §4.1, `inputs/frontend-inventory.md` (§1, §6, §8),
`records/SUBMISSION-PACK.md` §1.4, `assets/cards.html`, `reviews/review-1-flow.md`. Then I opened
the two trees and measured them.

**Tags.** MEASURED means a number I computed or a string I read in a file or a rendered page, with
the command and its output shown. INFERENCE means my reading of a measurement. Everything in Part A
and Part B is MEASURED unless it says otherwise.

**The tree moved while this was being written, and that is a finding, not a preamble.** Files
appeared in `records/video/` during the review (`OPEN-DECISIONS.md` 07:47Z, `README.md` 07:52Z,
`REHEARSAL.md` 07:47Z, `reviews/` 07:52Z) and **`SCRIPT.md` was rewritten at 07:54Z, between my
first read and my second.** My first pass counted the old text; Part A below is recomputed on the
file as it stands now, and §A1 says what changed. `../ticketing-frontend` is mid-rebuild by another
session: 57 files under `app/`, `components/` and `lib/` were modified in the 90 minutes before I
opened it, the newest at 07:47Z. Nothing below blames the plan for that. It does say which claims
the movement invalidates.

---

# PART A — cap compliance, measured

## A1. The words, counted myself

The five beats are blockquotes in `SCRIPT.md` §1. I extracted them to files and ran `wc -w` on each:

```
$ wc -w beat1.txt beat2.txt beat3.txt beat4.txt beat5.txt
  39 beat1.txt
  53 beat2.txt
  40 beat3.txt
  53 beat4.txt
  43 beat5.txt
 228 total
```

| Beat | Words | `SCRIPT.md` claims | Agrees? |
|---|---|---|---|
| 1 | **39** | 39 | yes |
| 2 | **53** | 53 | yes |
| 3 | **40** | 40 | yes |
| 4 | **53** | 53 | yes |
| 5 | **43** | 43 | yes |
| **total** | **228** | **228** | **yes** |

**On "is the 229 right":** the file I was given to review said 229, and at 07:44Z that was correct —
`wc -w` on that text returned 37 / 50 / 37 / 53 / 52 = 229. The file was rewritten at 07:54Z. The
current file says 228 and the current text is 228. **Both counts were right about their own text.
The count has never been the defect.** `NAME` counted as one word is correct: substituting a
six-character name changes nothing (`sed 's/NAME/Andrew/' | wc -w` → 228).

**One caveat that matters later.** `wc -w` counts written tokens. Three are spoken as more:

```
$ grep -oE '[A-Za-z0-9]+-[A-Za-z0-9]+|[0-9][0-9.]*' all.txt
one-unit
Token-2022
```

- `Token-2022` is spoken "token twenty twenty-two": 1 token, **4 words** (+3).
- `one-unit` is 1 token, **2 words** (+1).
- `MLH` spelled out is 1 token, **3 words** (+2).
- `SOL` is spoken "sol", one word, so nothing is owed there.

That is **234 spoken words**, not 228. Every duration below is computed both ways.

## A2. Durations at five paces, with the holds and the card as `SCRIPT.md` §4 specifies them

Speech is `words × 60 / wpm`. Holds and the card are `SCRIPT.md` §4's own quantities: **two
1-second holds and a 4-second card** (the current revision, table `| pace | speech | + 2 s holds +
4 s card |`).

| wpm | b1 (39) | b2 (53) | b3 (40) | b4 (53) | b5 (43) | speech | +2 s holds +4 s card | as mm:ss |
|---|---|---|---|---|---|---|---|---|
| 110 | 21.27 | 28.91 | 21.82 | 28.91 | 23.45 | 124.36 | 130.36 | **2:10.4** |
| 120 | 19.50 | 26.50 | 20.00 | 26.50 | 21.50 | 114.00 | 120.00 | **2:00.0** |
| 125 | 18.72 | 25.44 | 19.20 | 25.44 | 20.64 | 109.44 | 115.44 | **1:55.4** |
| 130 | 18.00 | 24.46 | 18.46 | 24.46 | 19.85 | 105.23 | 111.23 | **1:51.2** |
| 140 | 16.71 | 22.71 | 17.14 | 22.71 | 18.43 | 97.71 | 103.71 | **1:43.7** |

Same arithmetic on the **234 spoken words** the three tokens actually cost:

| wpm | speech (234 words) | +2 s holds +4 s card | as mm:ss |
|---|---|---|---|
| 120 | 117.00 | 123.00 | **2:03.0** |
| 123 | 114.15 | 120.15 | **2:00.1** |
| 125 | 112.32 | 118.32 | **1:58.3** |
| 130 | 108.00 | 114.00 | **1:54.0** |
| 140 | 100.29 | 106.29 | **1:46.3** |

`SCRIPT.md` §4's six rows are arithmetically correct to the tenth for the 228-word reading. I
checked every cell: 114.0, 115.9, 109.4, 105.2, 97.7 and the totals 2:10.4 / 2:01.9 / 2:00.0 /
1:55.4 / 1:51.2 / 1:43.7 all reproduce. **This revision's table is clean, which the previous one was
not** (see §A5).

## A3. The slowest pace that is still under 2:00

Solving `words × 60 / w + holds + card < 120`:

| Reading | Floor |
|---|---|
| 228 written words, 2 s holds, 4 s card | **120.0 wpm** (`228×60/114 = 120.00`) |
| 234 spoken words, 2 s holds, 4 s card | **123.2 wpm** (`234×60/114 = 123.16`) |
| 228 written words, 0 s holds, 4 s card | 118.0 wpm |

**The file's claims.** The header says "inside the cap at any pace above **120 wpm**"; §4 says
"comfortably inside 2:00 from **122 wpm** upward". The true floor on the written count is exactly
120.0 wpm, so the header is right at the boundary (120.0 is 2:00.0 on the nose, and its own table
says so: "exactly on the line — not good enough"), and §4 is conservative by 2 wpm. **Both are
defensible; the two numbers should be one number, and it should be 123 wpm because that is the
floor once `Token-2022`, `one-unit` and `MLH` are spoken.**

**Where the claim was wrong, and by how much, is the previous revision, which is what the brief
quotes.** That text said "inside the cap at any pace above 119 wpm" and "inside 2:00 from 120 wpm
upward", against 229 words. `CHOREOGRAPHY.md` (last written 07:45Z, unchanged) budgets **four**
1-second holds, not two, and under four holds the floor is `229×60/113 = 121.6 wpm`: at 120 wpm
that plan is **2:01.5, over by 1.5 s**, and at 121 wpm, 2:00.6, over by 0.6 s. So the old claim was
wrong by **1.6 wpm** against the choreography it was written for, and an eligible entry became
ineligible at any pace in the 120–121 band. The current script survives that particular error
because it cut to two holds.

## A4. Reading it aloud at 125 wpm: what the clock does not pay for

I read all five beats at 125 wpm and measured syllables, because "can it be said" is a syllable
question and the word count is not:

```
beat1: 39 words  ~ 57 syllables  3.04 syllables/s in a 18.72 s slot
beat2: 53 words  ~ 78 syllables  3.07 in a 25.44 s slot
beat3: 40 words  ~ 62 syllables  3.23 in a 19.20 s slot
beat4: 53 words  ~ 82 syllables  3.22 in a 25.44 s slot
beat5: 43 words  ~ 68 syllables  3.29 in a 20.64 s slot
```

Every beat sits between 3.0 and 3.3 syllables per second, which is slow conversational English and
is comfortably sayable. **No sentence in the script is impossible at 125 wpm.** The problems are
local and they are all the same kind: a written token that costs more than one spoken word, in a
beat that has no slack. **And they land in the wrong order** — beat 5 is both the densest beat
(3.29 syl/s) and the beat that owes the most unpaid words (+4), so the two costs multiply where
there is least room, while beat 4, which carries every number in the video, is the second least
dense (3.22) and has the most room of the two.

| Sentence | Beat | What it costs | Verdict |
|---|---|---|---|
| "my demo for the **MLH** Solana Hackathon" | 1 | 39 tokens in an 18.72 s slot, and if `MLH` is spelled it needs 18.95 s — the overrun has **no hold after beat 1** to absorb it | Say "MLH" as letters only if the take has already run fast. Otherwise this eats 0.25 s out of shot 2 |
| "cap twenty five hundred basis points. A transfer at one point two five SOL executes." | 4 | already written out in words, so the count is honest; three /f/ and /p/ clusters in one line | fine — beat 4 is the least dense beat after beat 1 (3.22 syl/s) and carries every number slowly without losing the slot |
| "error six zero one zero" | 4 | written out; five words, no cluster | fine |
| "a **Token-2022** fee takes a whole **one-unit** ticket" | 5 | 43 tokens in a 20.64 s slot at the densest syllable rate in the script (3.29/s), and spoken it is **47 words = 22.56 s, 1.9 s over its own budget** | this is the one sentence that cannot be said in its allotted time as written |
| "Two transactions on devnet: one lands, one is refused." | 5 | 9 words, fine to say; **lands at 1:43.8–1:48.1**, which is 16 s after the last signature card left the screen (see finding 4) | speakable, wrongly placed |

So: **the §A2 table at 125 wpm gives 1:55.4; the same script read the way it is written gives
1:58.3.** The 3.1 s of headroom the table shows is really **1.7 s**, and 1.7 s is one breath.

## A5. `CHOREOGRAPHY.md` against my arithmetic

The shot boundaries, as written:

| Shot | Range | Length |
|---|---|---|
| 1 | 0:00.0 → 0:17.8 | 17.8 |
| 2 | 0:17.8 → 0:30.0 | 12.2 |
| 3 | 0:30.0 → 0:42.8 | 12.8 |
| 4 | 0:42.8 → 0:53.0 | 10.2 |
| 5 | 0:53.0 → 1:01.5 | 8.5 |
| 6 | 1:01.5 → 1:10.0 | 8.5 |
| 7 | 1:10.0 → 1:19.0 | 9.0 |
| 8 | 1:19.0 → 1:28.0 | 9.0 |
| 9 | 1:28.0 → 1:44.0 | 16.0 |
| 10 | 1:44.0 → 1:56.9 | 12.9 |
| **total** | | **116.9 s = 1:56.9** |

**The shot boundaries are internally consistent and add to 1:56.9.** They encode the *old* script
(229 words, four 1-second holds). Against it, my arithmetic: 109.92 s of speech + 4.0 s of holds +
3.0 s of card = 116.92 s. Every block agrees **to within 0.06 s**, which is one-decimal rounding and
not an error:

| Block | Choreography | My arithmetic | Delta |
|---|---|---|---|
| shot 1 | 17.8 | 17.76 | +0.04 |
| shots 2–3 (beat 2 + 1 hold) | 25.0 | 24.00 + 1.00 = 25.00 | 0.00 |
| shots 4–5 (beat 3 + 1 hold) | 18.7 | 17.76 + 1.00 = 18.76 | **−0.06** |
| shots 6–8 (beat 4 + 1 hold) | 26.5 | 25.44 + 1.00 = 26.44 | **+0.06** |
| shots 9–10 (beat 5 + 1 hold + 3 s card) | 28.9 | 24.96 + 1.00 + 3.00 = 28.96 | **−0.06** |
| **total** | 116.9 | 116.92 | **−0.02** |

**No shot boundary is off by a tenth of a second.** The largest single error is 0.06 s. I want that
said plainly because review 1's finding 8 concluded the opposite: it read `SCRIPT.md`'s table as two
transcription slips, recomputed the plan at 1:54.9, and called the error "conservative". The 1:56.9
is not a slip. `CHOREOGRAPHY.md` spends four one-second holds — you can see them in the boundaries,
where 0:17.8 → 0:42.8 is 25.0 s against 24.0 s of speech, and 1:28.0 → 1:56.9 is 28.9 s against
24.96 s of speech — and 109.9 + 4 + 3 really is 116.9. Deleting two holds to reach 1:54.9 would
mean deleting two hold points the shot list needs.

**What is genuinely wrong is the old `SCRIPT.md` §4, and it is worth recording because the same
author wrote the new one.** Two errors, 4.0 s and 2.0 s:

- Its row `| four held beats | +4.0 s | 1:57.9 |` claims 109.9 + 4.0 = 1:57.9. It is 1:53.9. The
  next row, `| end card | +3.0 s | 2:00.9 |`, inherits the same +4.0 s. The file then wrote "Hold
  on: that last row is over the cap by 0.9 s" — a panic over an error it had invented. The real
  figure was 1:56.9, inside by 3.1 s on the first try.
- Its "fix" sentence — "put at most **two** one-second holds in, and the end card runs 3 s →
  1:56.9" — is wrong by 2.0 s: 109.9 + 2 + 3 = 1:54.9. Two wrong computations landed on the right
  total.
- Its pace table mixed the two variants: the 110, 119 and 140 rows are computed with two holds, the
  125 and 130 rows with four. The old `CHOREOGRAPHY.md` was right the whole time.

**And the two live documents now disagree, because `CHOREOGRAPHY.md` was not re-cut with the new
script.** It still carries the 229-word boundaries:

| Boundary | `CHOREOGRAPHY.md` | `SCRIPT.md` (07:54Z) | Delta |
|---|---|---|---|
| beat 1 ends | 0:17.8 | 0:18.7 | **−0.9 s** |
| beat 2 ends | 0:42.8 | 0:44.2 | **−1.4 s** |
| beat 3 ends / badge switch | 1:01.5 | 1:03.4 | **−1.9 s** |
| beat 4 ends | 1:28.0 | 1:28.8 | **−0.8 s** |
| end of speech | 1:53.9 | 1:49.4 | **+4.5 s** |
| **file length** | **1:56.9** | **1:55.4** | **+1.5 s** |
| end-card hold | 12.9 s (shot 10) | 4.0 s (§4 table) or 7.3 s (beat 5 heading, "from 1:48.1") | **8.9 s / 5.2 s** |

So the badge switch now fires **1.9 s before beat 4 begins**, which defeats the exact thing beat 4
was rewritten to achieve ("the switch in the ear at the same instant it happens on the frame"). And
`SCRIPT.md` disagrees with itself about its own card: beat 5's heading says the card runs from
1:48.1 to 1:55.4 (7.3 s) while §4 budgets 4.0 s (1:51.4 → 1:55.4). Three documents, three end-card
lengths: 12.9 s, 7.3 s, 4.0 s.

---

# PART B — feasibility, by inspection of the actual tree

## B0. The one measurement the whole of shots 1–3 depends on

The frontend **typechecks now**, which `CHOREOGRAPHY.md` §2 item 1 and `REHEARSAL.md` §6 item 2 both
say it does not:

```
$ npx --no-install tsc --noEmit --incremental false
EXIT:0
$ npx --no-install tsc --noEmit --incremental false --listFiles | grep -c '/app/\|/components/\|/lib/'
277
```

Zero diagnostics over 277 project files, at 07:49Z. That is a change since the inventory was
written and it is real. It does **not** mean the rebuild is on screen: the bundle being served dates
from before it (B4).

## B1. Per-shot verdicts

Evidence column: `file:line` is read from source; "served" is what a running server actually
returned; "rendered" is `ticketpath.console.page.render(payload)` measured in a 1920×1080 headless
browser from a file, which is the same HTML the console serves.

| # | Shot | Verdict | Evidence |
|---|---|---|---|
| 1 | ticket page, stat row → price path, 120 px scroll | **RECORDABLE WITH CAVEAT** | The route exists and the served page renders. But the two file generations print different strings (§B2). Ticket criterion satisfiable: `tkt_00077` is `Valid`, 5 ledger rows, newest row `2026-11-06T18:00Z` (inside the event window). Chart: one 498×187 SVG, `dashed: 0`, strokes `var(--gridline) var(--baseline) var(--series-1) var(--surface-1)` — accent line draws, cap rule absent, as promised |
| 2 | ownership trail, prices and markup per hop | **RECORDABLE WITH CAVEAT** | `Ownership trail` is the rebuilt heading (`app/tickets/[ticketId]/page.tsx:196`); the served page still says `Custody trail`. Row labels `Issued to` / `Bought by` / `Transferred to` exist in the rebuilt `components/OwnershipTrail.tsx:19-22`. `tx` chips: present on the served build, **gone** in the rebuild — `lib/api.ts:90-96` nulls `signature` for all 253 fixture rows at the seam, so the trail prints the honest no-link row |
| 3 | organizer analytics, 4 tiles, markup distribution | **RECORDABLE WITH CAVEAT** | Served: h1 `Resale analytics`, four tiles, `Markup distribution`, six buckets — exactly as choreographed. Rebuilt: h1 `For organizers` (`app/organizer/page.tsx:65`) and **six** tiles (`Resale volume`, `Sales`, `Average markup`, `Median resale price`, `Resold share`, `Holders`, lines 132-190). `Markup distribution` at :190, six buckets intact. `Where tickets ended up` at :205 still prints fixture cities (`lib/api.ts:113` reads `region` straight from the wallet fixture, e.g. `Indianapolis, IN`) — the do-not-show rule still binds |
| 4 | console, `[EXACT]` ceiling + `[UNVALIDATED]` recommendation | **RECORDABLE WITH CAVEAT** | Rendered: recommendation at y=1111, `[EXACT] ceiling 1,380,000,000 lamports` at y=1186, both inside one viewport. **The fixture strip is at y=30 and cannot share a frame with them** — 1201 px apart at 1920×1080, so the choreography's "the fixture strip … stays in frame for every console shot" is false today. The console is **not serving** (see B4) |
| 5 | console, `What the engine refuses` | **RECORDABLE** | Rendered panel spans y=1969–2348 (379 px): `[REFUSED] What the engine refuses` at 1986, `not_identified` 2026, `no_upper_bound` ~2210, `insufficient_events` 2249. All six refusals fit in one 1080 frame. `0 arms shown` and the button label `Show the refusal` exist (`ticketpath/console/page.py:357`, `labels.py` P_SIM_BUTTON). Caveat: **six** rows, not the three named, and the three named are interleaved with `no_demand_response`, `no_fee_model`, `cap_mass_dominates` |
| 6 | console `[DEVNET]` slot at the pinned `asOf` | **RECORDABLE WITH CAVEAT** | `chain.state = verified`, `matchesCurrentQuote = True` at `asOf=2026-11-07T18:34:29.183Z`. The chain panel is 1138 px tall — taller than a frame — but everything the shot names sits between y=3039 (`The file verified. The checker wrote 2026-11-08T00:50:25.281Z`) and y=3545 (admitted signature `E5RCrLwW…ab7pJf`, `the file states 519845933`), so one frame at scroll ≈3030 holds it. At that offset the `[SIMULATED] 0 arms shown` panel (ends 2967) is **out** of frame by 63 px — which §1.4 requires and the choreography does not say |
| 7 | `cards.html?card=admitted` | **RECORDABLE** | 1920×1080 exactly, `scrollW/H = 1920/1080`, no element outside the card box except the DEVNET plate deliberately at 40 px from the edges. 87-character signature on **one line** (dd height 34 px = 1 line). Signature and slot match `records/devnet-artefacts.json` character for character. Text renders `Admitted`, not `ADMITTED` — `.verdict` has no `text-transform` |
| 8 | `cards.html?card=refused` | **RECORDABLE** | Same measurements. Signature is 88 characters, also one line, matches the artefact. `custom program error 0x177a · 6010 E_CAP_EXCEEDED` renders |
| 9 | console refusal block or `[UNVALIDATED]` badge held | **RECORDABLE WITH CAVEAT** | Same surface and the same framing constraint as shot 4. The refusal panel alone (y=1969–2348) is comfortably framable |
| 10 | end card | **RECORDABLE** | 1920×1080, no overflow, four rendered lines: `SeatPass` / `Pricing from the resale record. Capped on chain.` / `Built at the MLH Solana Hackathon · 6–8 November 2026` / `github.com/andy1245-rgb/ticketpath`. Matches `CHOREOGRAPHY.md` §3; does **not** match `SCRIPT.md`'s three-line block (finding 9) |

**Nothing in the ten shots is NOT RECORDABLE on the page or asset side.** Four are recordable
unconditionally; six need one of the framing decisions in Part B2–B5. The blocker is the recorder,
not the shots (B6).

## B2. The frontend: two generations, and the camera sees the older one

```
$ curl -s -o t.html -w '%{http_code}' http://<local>/tickets/tkt_00017
200
$ grep -o 'Custody trail\|Resale record\|Enforced on-chain\|Mock data[^<]*' t.html | sort | uniq -c
      2 Custody trail
      2 Enforced on-chain
      1 Mock data — set
```

The page a camera would record **right now** is the pre-rebuild one: `Custody trail`, `Wallets held
by`, `On-chain / Enforced on-chain`, four `tx` links on the trail, `Not yet scanned`, and this
sentence at the foot of the card:

```
Every transfer is recorded on-chain. Price and custody history is public for all issued tickets.
```

That sentence is false of this tree (the record is a fixture and `lib/api.ts` reports
`rpcEnabled: false`), and `SUBMISSION-PACK.md` §1.4 forbids the `Mock data` banner that sits above
it on the same page. The working tree on disk has fixed all of it, and the working tree is not what
the server serves. So:

- Record the served page today and you get the choreography's exact strings **and** three defects
  the plan forbids in frame.
- Record the rebuilt page and shots 1–3 need re-wording, because `Custody trail` → `Ownership
  trail`, `Wallets held by` → `Wallets held`, `Resale analytics` → `For organizers`, four tiles →
  six.

`REHEARSAL.md` §6 item 2 assumes typecheck-green means "a build and not a dev server's best effort".
It does not: the build that is serving predates the tree that typechecks.

## B3. The console: strings intact, one guard testing the wrong flag

Every string the shots quote still exists verbatim, verified by rendering the payload with no
server (see B5):

```
'[EXACT]'                         count=2
'Recommended primary price'       count=1
'[UNVALIDATED]'                   count=5
'What the engine refuses'         count=1
'not_identified'                  count=1
'no_upper_bound'                  count=1
'insufficient_events'             count=1
'[DEVNET]'                        count=9
'The file verified'               count=1
'Show the refusal'                count=2
'0 arms shown'                    count=1
'[SIMULATED]'                     count=3
```

The exact rendered lines, at `asOf=2026-11-07T18:34:29.183Z`:

```
[UNVALIDATED] Recommended primary price: at least 1.38 SOL per ticket, General tier.
[EXACT] ceiling 1,380,000,000 lamports = face 1,200,000,000 lamports × (10,000 + 1500) / 10,000
[DEVNET] The chain slot
The file verified. The checker wrote 2026-11-08T00:50:25.281Z with checker devnet-publish-2026-11-07.
[DEVNET] quote id q-18f4ec73dd8d8fd1 · quote hash d90cb033… · recorded at 2026-11-07T18:34:29.183Z …
The face and cap the file states put the resale ceiling at [EXACT] 1,250,000,000 lamports.
The recorded recommendation of [DEVNET] 1,380,000,000 lamports is above that ceiling.
This page computed its own number under the event's cap of [DECLARED] 1,500 bps and face of
[FIXTURE] 1,200,000,000 lamports, which are the store's, not the file's.
```

**The `[DEVNET]` slot renders verified for the pinned `asOf`, and the page now confesses the
130,000,000-lamport gap itself.** That is better than the plan claims: `SCRIPT.md` beat 3 says the
figure "stays on screen tagged `[UNVALIDATED]`" because speaking it "invites a judge with a
calculator". The page hands the judge the calculator answer, labelled, in the same frame. The
concession is in shot 6's frame whether you plan it or not.

**But the choreography's pre-roll guard checks the wrong field.** Shot 6 says "the slot must read
verified for exactly that `asOf`. Any other instant renders unverified." I tested a different
instant:

```
$ guidance.py … --as-of 2026-11-07T12:00:00Z
state verified | matches False
```

`state` stays `verified` because it describes the artefact file; `matchesCurrentQuote` is the flag
that flips. An operator applying the written check would pass a frame that says "this page's
number is not the file's number".

## B4. What is actually running

- The **console is not serving**: a bounded request for the pinned URL returned HTTP `000`
  (connection refused). Shots 4, 5, 6 and 9 require starting it first. I did not start it.
- The **frontend is serving**, from `../ticketing-frontend`, answering 200 with the pre-rebuild
  bundle described in B2. A second listener from the same checkout answered 404 to every route. A
  third server, from a copy elsewhere, answered 500.

## B5. Rendering the console payload with no server — yes, two ways, both proven

This is the answer to "can a shot be verified before recording without starting a server". Yes:

```bash
# 1. the payload, exactly as the URL would build it
python3 tools/guidance.py --event evt_syn_02 --tier tier_stg_general \
    --as-of 2026-11-07T18:34:29.183Z --cap 1500 --tau 0.20 > payload.json

# 2. the page the console would serve, as HTML
python3 -c "import json,sys; sys.path.insert(0,'.'); \
  from ticketpath.console import page; \
  print(page.render(json.load(open('payload.json'))))" > console.html
```

`tools/guidance.py:1-8` states the intent ("Print the console payload for a URL's parameters… the
same payload without a browser, which is what makes it batch-testable") and it works: `--events`
lists eight events and their tiers; the pinned invocation exits 0. `page.render()` takes the payload
and returns the full document with its inline stylesheet, so it renders identically from `file://`
and its element offsets can be measured. Every framing number in this review was measured that way.
**`CHOREOGRAPHY.md` should replace "check before roll" with these two commands**, because they are
cheaper and they test the flag that matters.

## B6. The charts, and the recorder

**Fallback charts exist and label themselves, in their own visible text.** `docs/charts/` holds
`hops-and-holding.svg`, `markup-vs-time-to-event.svg`, `price-path-evt_capped.svg`,
`price-path-evt_monitored.svg`, `ticket-hop.svg` and an `index.html`. Each SVG carries a red banner
`SYNTHETIC`, the sentence `synthetic simulation data - not evidence about any real ticket market`,
both dataset file names with a run id and a truncated sha256, and `DRY RUN: a simulated gateway
returned what the hook would have done. No transaction was built, signed or sent; every row reads
chain=simulated.` Fallback B is the safest surface in the package.

**The recorder is the one thing that cannot do the job, and it is unchanged since 07:33Z.**
Measured now:

```
$ for c in ffmpeg ffprobe obs recordmydesktop wf-recorder gst-launch-1.0 kazam peek \
           gnome-screenshot scrot import xwd arecord sox pactl convert magick blender; do …; done
ffmpeg MISSING   obs MISSING   recordmydesktop MISSING   wf-recorder MISSING
gst-launch-1.0 MISSING   kazam MISSING   peek MISSING   gnome-screenshot MISSING
scrot MISSING   import MISSING   xwd MISSING   arecord MISSING   sox MISSING
pactl MISSING   convert MISSING   magick MISSING   blender MISSING

$ ls /dev/snd
seq  timer                     # no capture device

$ echo "$XDG_SESSION_TYPE $DISPLAY $WAYLAND_DISPLAY"
tty

$ python3 -c "import PIL" → MISSING ; import cv2 → MISSING ; import numpy → MISSING
```

Browsers: no system Chromium, Chrome, Firefox or Edge. Playwright's Chromium is present, plus its
stripped ffmpeg:

```
$ ffmpeg-linux -muxers   → D/E: image2, webm          (nothing else)
$ ffmpeg-linux -encoders → V: png, libvpx-vp9         (no audio encoder at all)
```

I confirmed the video path works: a 2-second `recordVideo` capture produced a real 1280×720 `.webm`.

So, precisely: **this machine can record a silent `.webm` of scripted page states, and nothing
else.** It cannot record a voice (no capture device, no audio encoder), cannot produce an `.mp4`
(no muxer), cannot burn a badge in post (no ImageMagick, no PIL, no `numpy`, no editor), cannot
concatenate shots, and cannot mux. Every one of those is needed by the plan as written: the badges
are "burned in by the edit" (`CHOREOGRAPHY.md` §1), the shots are separate takes that must be
joined, and the whole video is narrated. This is decision **V1** and it is still open.

---

# PART C — rules

| # | Requirement | Verdict | Basis |
|---|---|---|---|
| 6 | Nothing on screen the rules or the pack forbid | **CONDITIONAL PASS** | The plan's own "do not" list is correct and complete for the surfaces it knows about. Two gaps: the served frontend page carries the `Mock data` banner and `Enforced on-chain` (§1.4 and inventory §7 item 2) unless the frame is cropped below them, and the console's `[SIMULATED] 0 arms shown` panel sits **15 px above** the `[DEVNET]` slot that shot 6 needs — §1.4 says that panel must not appear on any frame, and the choreography has no instruction that keeps it out (finding 5). No terminal, desktop or Explorer page is planned anywhere. Both signatures are public cluster facts, not credentials |
| 7a | 2:00 or less | **PASS at 125 wpm, FAIL below 123** | 1:55.4 as counted, 1:58.3 with the three elongated tokens, floor 123.2 wpm. Rule 1 of `rules-verified` §1 is a cap on the file, and the file is what `REHEARSAL.md` pass 5 measures |
| 7b | Created the weekend of the hackathon | **PASS if recorded before 18:00Z today** | The tree, the script and the cards are all dated 2026-11-08. Nothing in the video is archival footage |
| 7c | Hackathon named at the beginning | **PASS** | Beat 1, words 10-13 of 39: "my demo for the MLH Solana Hackathon", spoken at ≈4.8 s, inside the ten-second window the winner sample supports. Beat 4 also says "Solana devnet", which the previous revision never said at all |
| 7d | Video public | **NOT VERIFIABLE HERE — operator action** | Nothing in the repository can attest to a publish setting. It must be public before 18:00Z and stay public after judging (`rules-verified` §1 rule 2) |
| 7e | The capture-date expectation the cheat check looks for | **CONDITIONAL PASS** | The evidence that exists: the console prints `The checker wrote 2026-11-08T00:50:25.281Z` and `recorded at 2026-11-07T18:34:29.183Z`, both inside the window; the end card carries 6–8 November. What is missing is any app frame inside the window — of 253 fixture ledger rows exactly **one** is dated 6–8 November, and it is on `tkt_00077`. A reviewer scrubbing shots 1–2 sees October dates |
| 8 | The URL on the end card is the real remote | **PASS** | `git remote -v` → `origin git@github.com:andy1245-rgb/ticketpath.git` (fetch and push). The card renders `github.com/andy1245-rgb/ticketpath`. Same repository name, character for character. The card URL cannot be resolved from here without network access; that is `REHEARSAL.md` §2.5's job and it is unticked |

---

# FINDINGS

Ordered by what can lose the entry. Every fix is a change to a document or to a shot, not to the
product.

### 1. The choreography was not re-cut for the new script, so every beat boundary is 0.8–1.9 s early and the badge switch fires before the sentence that explains it — **MAJOR**

`SCRIPT.md` was rewritten at 07:54Z to 228 words with new durations (0:18.7 / 0:44.2 / 1:03.4 /
1:28.8 / 1:49.4, card from 1:48.1 or 1:51.4, file 1:55.4). `CHOREOGRAPHY.md` last changed at 07:45Z
and still carries the 229-word boundaries (0:17.8 / 0:42.8 / 1:01.5 / 1:28.0 / 1:44.0 / 1:56.9).
Measured deltas in §A5. The consequence that matters is not the 1.5 s on the total: it is that the
SYNTHETIC→DEVNET switch is scheduled at 1:01.5 and beat 4's new opening line — "Everything before
this was generated. This is not." — does not begin until 1:03.4. Beat 4 was rewritten specifically
to put the switch "in the ear at the same instant it happens on the frame", and the stale shots put
it 1.9 s early.

**Fix:** re-cut all ten shot boundaries from the §A2 table at 125 wpm, and put the switch at the
first word of beat 4, 1:03.4. Then pick one end-card length and use it in all three documents
(finding 3).

### 2. The 1:55.4 assumes 228 short words; spoken as written the script is 234 and the true floor is 123 wpm, not 120 — **MAJOR**

`wc -w` counts `Token-2022` as one word and it is four, `one-unit` as one and it is two, `MLH` as
one and it is three. At 125 wpm that is 1:58.3, not 1:55.4, so the file's headroom is 1.7 s, and the
slowest eligible pace is 123.2 wpm rather than the 120 in the header. Against a measured winner
median of 99 wpm, a 123 wpm floor is a real constraint, and `REHEARSAL.md`'s pass-2 band
("1:50 – 1:58 of speech") still admits reads that fail it.

**Fix:** change `SCRIPT.md`'s header "above 120 wpm" and §4's "from 122 wpm" to **123 wpm**, and
change `REHEARSAL.md` §3 pass 2's band to **1:48–1:52 of speech**, against a hard ceiling of
**1:54.0** (120 s − 2 s of holds − 4 s of card). If the first timed read comes in slower, cut beat
5's Token-2022 clause — 16 words, 7.7 s — which is the only sentence in the script that cannot be
said in its own slot.

### 3. Three documents, three end-card lengths — **MAJOR**

`CHOREOGRAPHY.md` shot 10 holds the card **12.9 s** (1:44.0 → 1:56.9). `SCRIPT.md` §4 budgets
**4.0 s**. `SCRIPT.md` beat 5's own heading says the card runs from **1:48.1**, which is 7.3 s and
starts 1.3 s before the last word is spoken. 12.9 s of a static card is 11% of a 2:00 video.

**Fix:** card at 1:51.4 → 1:55.4, 4.0 s, in all three files, with the last spoken words over the
first second of it. Rewrite shot 10's boundary and `SCRIPT.md` beat 5's heading to match.

### 4. The strongest sentence in the close is spoken 16 seconds after the shot it describes — **MAJOR**

Beat 5's new line "Two transactions on devnet: one lands, one is refused. That refusal is the
feature." falls at **1:43.8–1:50.5** at 125 wpm. The two signature cards (shots 7 and 8) leave the
screen at 1:28.0. So the sentence that closes the argument is delivered over the console refusal
panel and the end card, while the two admissions it names are long gone. `SCRIPT.md` beat 4 says
"The chain refuses it, not the app" over the same cards earlier, so the new line is also a repeat.

**Fix:** either move the two cards later (shots 7–8 at 1:38–1:52, console at 1:28–1:38, card 1:52)
so the sentence lands on them, or cut the sentence and spend the 4.8 s on the Token-2022 finding.
Do not leave it where it is: it is the only claim in the video a judge can verify in one click.

### 5. The `[SIMULATED] 0 arms shown` panel sits 15 px above the `[DEVNET]` slot, and the pack forbids it on any frame — **MAJOR**

`SUBMISSION-PACK.md` §1.4: "The console's `The state machine` panel untouched, reading `0 arms
shown` … " must not appear on any frame. `CHOREOGRAPHY.md` shot 5 tells the operator not to press
the button, which guarantees the panel reads `0 arms shown` and leaves it on screen. Rendered
offsets: the simulation panel spans y=2795–2967, the chain slot starts at y=2982. A frame scrolled
to the chain slot's top excludes it by 63 px; a frame scrolled to the refusals (y=1969) includes
neither.

**Fix:** add one line to shots 5 and 6 — "scroll so the `[SIMULATED]` panel is entirely above the
viewport; its bottom edge must be off-frame" — and add the measured offset (chain panel top at
y=2982, simulation bottom at y=2967) to `CHOREOGRAPHY.md` §2 as the check. Alternatively press the
button before the take and record the panel populated, which §1.4 does not forbid.

### 6. The `[EXACT]` ceiling line and the fixture strip cannot share a 1080 frame — **MAJOR**

Shot 4 requires "the fixture strip at the very top (it stays in frame for every console shot)" and
the `[EXACT]` ceiling line. Rendered: strip at y=30, ceiling at y=1186 — **1201 px apart**, more
than a 1080 viewport. And `SUBMISSION-PACK.md` §1.4 makes it a rule: "Any number on screen without
the `SYNTHETIC FIXTURE DATA` strip above it … That includes the console, whose strip is the first
element on the page."

**Fix, and it is measurable:** record the console at 85% browser zoom, which puts the strip at y≈25
and the ceiling line at y≈1008 in a 1080 frame (1201 × 0.85 = 1021). The second option is a taller
viewport and a scale on export, which needs an editor this machine does not have (finding 10). Say
in §2 which one, and check it on a captured frame.

### 7. The console's own `[EXACT]` line contradicts the numbers beat 4 speaks — **MAJOR**

Beat 4: "face one SOL, cap twenty five hundred basis points… one point two five SOL executes."
Shot 4's frame, at the pinned URL, says: `[EXACT] ceiling 1,380,000,000 lamports = face
1,200,000,000 lamports × (10,000 + 1500) / 10,000`. Two different records — the fixture store's
`evt_syn_02` (face 1.20 SOL, cap 1500 bps) and the devnet artefact for the same event and tier (face
1.0 SOL, cap 2500 bps) — and the video shows one while saying the other. I tested pinning
`capBps=2500` to line them up: the `[EXACT]` line does not change, because it is computed from the
tier's recorded cap in force, not from the declared one. `matchesCurrentQuote` stays `True` either
way.

**Fix:** the numbers cannot be reconciled without a code change, so move the voice instead. In beat
4 say the devnet numbers only while a card is on screen (shots 7–8 carry
`face 1.000 SOL × (10,000 + 2,500) ÷ 10,000` and `1,250,000,000 lamports`), and over shots 4–6 say
what the screen says: "the engine's floor sits at the ceiling this record allows". The console does
not print an `[UNVALIDATED]` bps figure in the decision panel, so nothing on those frames has to be
spoken.

### 8. Shots 1–3 record the pre-rebuild bundle, which carries three of the four defects the plan exists to avoid — **MAJOR**

The rebuild typechecks clean (277 files, exit 0) and is **not** what the running server serves. The
served page prints `On-chain / Enforced on-chain`, four `tx` links onto signatures that exist on no
cluster, `Every transfer is recorded on-chain`, and the `Mock data — set NEXT_PUBLIC_API_BASE_URL`
banner — three claims the inventory ranks as dishonest (§7 items 1-3) and one banner §1.4 forbids.
The choreography's do-not rules assume the rebuilt page: `Enforced on-chain` and the `tx` chips no
longer exist in source, and `Custody trail` no longer exists either.

**Fix:** decide this as V3 and write the answer down, because both branches are cheap now and
expensive at 17:30. Either (a) record the served page and crop hard — the `On-chain` card must never
be in frame, which means no downward scroll past the trail and no scrollbar grabbed to the bottom,
and the banner is already off-screen if shot 1 starts at the stat row — or (b) take **Fallback B**
for shots 1–3, which needs no server, is already labelled, and costs the product's face but not the
argument. Given that the served build is stale and another session is mid-edit, (b) is the lower
risk of the two today.

### 9. The end card in `SCRIPT.md` does not match the end card in `cards.html`, and the file's version uses an em dash — **MINOR**

`SCRIPT.md` beat 5 prints three lines: `SeatPass — pricing from the resale record, capped on chain` /
`…6–8 November 2026` / `github.com/andy1245-rgb/ticketpath`. `cards.html` renders four lines with
`Pricing from the resale record.` / `Capped on chain.` and a `·` before the date, and it is measured
clean at 1920×1080. `CHOREOGRAPHY.md` §3 agrees with the card. So `SCRIPT.md` is the odd one out,
and its `—` is a character the operator's own writing rules do not use.

**Fix:** delete `SCRIPT.md`'s three-line block and replace it with "the card text is
`assets/cards.html?card=end`, measured at 1920×1080", which removes the possibility of two sources.

### 10. The badges cannot be burned in on this machine, and neither can the shots be joined or the voice added — **MAJOR**

No `ffmpeg`, no OBS, no ImageMagick, no PIL, no `numpy`, no editor; the bundled ffmpeg has only
`image2` and `webm` muxers and only `png` and `libvpx-vp9` encoders, with no audio encoder at all;
`/dev/snd` has no capture device; the session is `tty` with no display. The plan needs three things
this machine cannot do: burn the SYNTHETIC/DEVNET plates in ("burned in by the edit", §1),
concatenate ten shots into one file, and carry a voice. `REHEARSAL.md` §1 says this correctly for
the voice; it does not say it for the badges or the join, which are the same problem.

**Fix:** treat the whole video as a laptop job (V1 option 1), and keep this machine's role to what it
provably does: render and measure the cards, render and measure the console frames, verify the
strings, and hand over exact scroll offsets. If the badges must come from here, capture them with
the badge already in the DOM rather than in post, which is what `cards.html?card=badges` is for.

### 11. The pre-roll check on the `[DEVNET]` slot tests `state`, and the flag that matters is `matchesCurrentQuote` — **MINOR**

Measured: at an `asOf` one day earlier, `state` is still `verified` while `matchesCurrentQuote`
becomes `False`. The choreography says any other instant "renders unverified", which is not what the
code does.

**Fix:** replace `CHOREOGRAPHY.md` §2 item 9 with the two `guidance.py` / `page.render()` commands
from §B5 and the assertion `chain.state == "verified" and chain.matchesCurrentQuote is True`.

### 12. Line 6 of the choreography's badge table specifies a badge the assets do not render — **MINOR**

The table says "22 px mono"; the strip is `font:600 20px/1` and measures 20 px
(`assets/cards.html:47`). It also says the wording is `SYNTHETIC · generated fixture data — not real
ticket prices` while `.strip` sets `text-transform:uppercase`, so the frames read
`SYNTHETIC · GENERATED FIXTURE DATA — NOT REAL TICKET PRICES`. Measured: plate 760×64, text 632 px
wide, 107 px of slack, no clipping.

**Fix:** change "22 px" to "20 px" and note that the plate renders in caps.

### 13. `CHOREOGRAPHY.md` shot 5 requires three refusal rows; the console prints six — **MINOR**

Rendered order: `not_identified`, `no_demand_response`, `no_fee_model`, `cap_mass_dominates`,
`no_upper_bound`, `insufficient_events`. The three the shot names are present and in the stated
relative order, but three others sit between them, and the panel is 379 px tall so all six are in
frame whether you plan it or not.

**Fix:** say "all six refusals in frame, in this order", which is stronger than the three: it shows
the engine declining four different ways, and it costs no seconds.

### 14. No app frame carries a timestamp inside the event window — **MINOR**

Of 253 fixture ledger rows, **one** is dated 6–8 November 2026 (`tkt_00077`, a transfer at
`2026-11-06T18:00Z`). Every other ticket's trail is July–November 2026, and `tkt_00001`'s is
October. A cheat-check reviewer scrubbing the first 43 seconds sees pre-weekend dates on screen.

**Fix:** shoot `tkt_00077` for shots 1–2. It satisfies both of the choreography's criteria — status
`Valid`, not `Listed`, and 5 ledger rows — and its newest row is inside the window. The dates are
still labelled fixtures by the badge; this only stops the frame arguing against the publish date.

### 15. `REHEARSAL.md` pass 5 checks the file, but pass 2 — the pass that decides whether a take is worth making — passes reads that cannot fit — **MINOR**

Pass 2's table: "1:50 – 1:58 of speech → the target band". 1:58 of speech plus 2 s of holds plus a
4 s card is **2:04**, an ineligible entry. The hard ceiling on speech is **114.0 s = 1:54.0**
whatever the word count; what differs is the pace that reaches it — 120 wpm at 228 words, 123.2 at
the 234 the script is actually spoken as. Pass 2's upper bound is four seconds past the ceiling.

**Fix:** set pass 2's band to 1:48–1:52 of speech and add the sentence "the card and the holds come
on top, so a stopwatch past 1:54 is a failed take, not a slow one".

### 16. `REHEARSAL.md` §2.1 reports a card measurement that no longer matches the assets — **MINOR**

It says "the 87-character signature fits on one line at 1404 px with no wrap". Measured now: the
admitted signature is 87 characters on one line, the refused signature is **88** characters, also
one line, and the `dd` is 34 px tall in both, so the conclusion holds. The number 1404 px I cannot
reproduce as anything; the text box measures 632 px for a badge and the rows grid is
`200px + 1fr` inside 1640 px.

**Fix:** quote the measurement that is checkable — "both signatures render on one line; `dd` height
34 px = one line at 26 px/1.3" — or drop the pixel figure.

---

# What must be true before the first take

A checklist. Every line is a check that has a pass condition, and the ones I could run are marked.

**The time**

1. A timed read of the current 228-word script, out loud, at or above **123 wpm** — i.e. speech
   under **1:52**. Add 2 s of holds and a 4 s card. If the read is slower, cut beat 5's Token-2022
   clause and re-time. *(Not yet run: no one has read this revision aloud.)*
2. One end-card length agreed and written into `SCRIPT.md` §4, `SCRIPT.md` beat 5 and
   `CHOREOGRAPHY.md` shot 10: **4.0 s, 1:51.4 → 1:55.4.**
3. All ten shot boundaries in `CHOREOGRAPHY.md` re-cut from the current script, with the badge
   switch at **1:03.4**, not 1:01.5.

**The frame**

4. The console checked with `tools/guidance.py` + `page.render()` and `matchesCurrentQuote is True`
   at the pinned `asOf`. *(Passes today.)*
5. Shot 6's scroll offset measured so the `[SIMULATED] 0 arms shown` panel is off-frame: chain
   panel top y=2982, simulation bottom y=2967, so scroll to ≈3030. *(Measured today.)*
6. Shot 4's framing decided: either 85% zoom so the strip (y=30) and the ceiling line (y=1186) share
   a frame, or the pack's strip rule formally relaxed for console frames because every number
   carries its own inline `[FIXTURE]` badge. *(Not decided.)*
7. Shots 1–3 decided between the served pre-rebuild page and **Fallback B**. If the served page:
   no frame may contain the `On-chain` card, the `Mock data` banner or a `tx` chip. *(Not decided;
   the tree is mid-edit right now.)*
8. The ticket for shots 1–2 chosen: `tkt_00077` — `Valid`, 5 rows, newest row inside the event
   window. *(Measured today.)*

**The machine**

9. A machine with a screen recorder, a microphone and a video editor, decided and confirmed by a
   five-second test recording played back. This machine cannot record a voice, cannot encode audio,
   cannot make an `.mp4`, and cannot burn a badge in. *(Decision V1, still open.)*

**The truth**

10. `git remote -v` still reads `andy1245-rgb/ticketpath`, and the end card's URL still opens.
    *(Remote confirmed today; the URL has not been opened from here.)*
11. Both devnet signatures still resolve — admitted with `err: null`, refused with `Custom 6010`.
    *(Not run: needs network.)*
12. The three cards re-rendered and re-measured at 1920×1080 after the last text edit: `scrollW/H` =
    1920/1080, both signatures on one line. *(Passes today.)*
13. Nothing on any frame is a terminal, a desktop, a bookmark bar, an Explorer page, the `Mock data`
    banner, or `0 arms shown`.

**The submission**

14. The video is published **public** before 18:00Z and both signatures are in the description.
    *(Operator only.)*
