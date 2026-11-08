# Review 4: does it hold?

**Fourth pass, read-only except this file.** I wrote no line of the script, the choreography,
the rehearsal plan, the cards or the reviews. I ran no subagents. I started no server and
edited nothing outside this file. Where a number appears below, the command that produced it
is either pasted or named, and the arithmetic is printed.

**The tree moved under this review, and it moved twice.** Every claim below is against this
snapshot, taken at 08:08Z to 08:12Z:

| File | Last write | Bytes |
|---|---|---|
| `SCRIPT.md` | 08:05:21Z | 13,578 |
| `CHOREOGRAPHY.md` | 08:05:24Z | 19,407 |
| `REVIEWS.md` | 08:05:24Z | 6,822 |
| `REHEARSAL.md` | 08:05:40Z | 13,244 |
| `assets/cards.html` | 08:00:25Z | 6,511 |
| `reviews/review-1-flow.md` | 07:55:14Z | 35,999 |
| `reviews/review-2-honesty.md` | 08:07:35Z | 22,767 |
| `reviews/review-3-cap-and-feasibility.md` | 07:59:19Z | 45,677 |

Two consequences, both material to how this report should be read.

1. **The four package documents were rewritten at 08:05Z, while I was on my first read.** My
   first pass counted 220 written words and a 1:54.5 file against the 07:55 text. The text on
   disk now says 221 and 1:55.0. Everything in section B is recomputed from the current files,
   and I say so where the earlier numbers differed.
2. **`review-2-honesty.md` was rewritten at 08:07:35Z, after the package it audits was fixed.**
   It now opens "**Verdict.** No blockers and no majors" and its findings are renumbered: its
   finding 1 is "beat 3's tier scope" and its finding 2 is "That refusal is the feature". The
   blockers this review was asked to verify (the two-word fixes in beat 4) are no longer
   numbered findings in that file. **The finding numbers used in section A for review 2 are the
   numbers in the version `REVIEWS.md` describes** (two blockers, six majors, the 07:58 text),
   because that is the version the disposition table is about. I checked each one against the
   files on disk, not against the review's own status claims.

A third thing to know before reading section A: `REVIEWS.md` records 17 dispositions for 45
findings. The mapping is by theme, not by number. So for most findings I answer from the file,
and where `REVIEWS.md` does claim a disposition I check the claim rather than repeat it.

---

# A. Fix verification

Verdicts: APPLIED, PARTLY APPLIED (fixed in one document and not in another, or fixed with a
residual), NOT APPLIED, WRONGLY REJECTED. No finding in the three reviews turns out to be
wrongly rejected: every rejection `REVIEWS.md` records (the caption layer, the full synthetic
sentence, moving the cards, a 3 s card) is a taste or sequencing call, not a factual error, and
I have not reopened any of them.

## A1. Review 1, blocker and majors (10 rows)

| # | Sev | Finding, one line | Verdict | Evidence, current text |
|---|---|---|---|---|
| 1 | BLOCKER | The product's function is missing until 0:43 | **APPLIED** | `SCRIPT.md:27-28`: "SeatPass prices from that resale record, and the chain caps the markup." Measured at 125 wpm: "SeatPass prices" begins after 29 spoken words = **0:13.9** (the file claims 0:13; 0.9 s earlier than it lands, but inside the same second). `SCRIPT.md:44-46` records the choice as a proxy, not a norm: "This is a choice made on the demo-signal proxy, not a measured norm." |
| 2 | MAJOR | Voice says valuation, screen says price recommendation | **APPLIED** | `SCRIPT.md:76`: "The console recommends a primary price as a floor, not a forecast". The "tags it unvalidated" half of the same fix moved off the voice onto the lower third: `CHOREOGRAPHY.md:42`: "0:49.0 | `the console's own tag: [UNVALIDATED]`". The words "primary", "recommend" and "organiser" are all now in beat 3. |
| 4 | MAJOR | The refusal has no mechanism the judge can check | **APPLIED** | `SCRIPT.md:76-77`: "the highest price this tier has seen". Measured against the console's own claim, which review 2 quotes at `labels.py:279-281` ("the highest recorded price in this tier"). The scope word is now the console's scope word. |
| 5 | MAJOR | Four seconds of frozen frame over a number the voice will not name | **APPLIED** | `CHOREOGRAPHY.md:116`: "Hold two seconds. Two is a beat; four is a stall." The label is named on the frame by the lower third above. |
| 6 | MAJOR | The badge switch is a technicality | **APPLIED** | `SCRIPT.md:97`: "Everything before this was generated. This signature is not." `CHOREOGRAPHY.md:154-155`: "**The switch is spoken and shown on the same frame:** ... Lower third: `synthetic → devnet`." Cost 1 word, as predicted. |
| 7 | MAJOR | The last 25 s end on a legal qualifier; shot 9 is the worst frame in the cut | **PARTLY APPLIED** | The copy half landed: the prior-work clause is at `SCRIPT.md:66-68` (beat 2), and the close ends on `SCRIPT.md:131` "That chain refusal is the feature." The frame half did not: shot 9 is still one held surface and it is now **longer**, `CHOREOGRAPHY.md:192`: "### Shot 9 · `1:32.7 → 1:50.9` · beat 5 · **SYNTHETIC**", which is **18.2 s**, 15.8% of the file and the longest shot in the cut that does not move. Review 1 asked for two ~10 s shots. `REVIEWS.md` records no disposition for the split, so it was neither taken nor rejected, it was dropped. |
| 9 | MAJOR | Three sentences and a 12.9 s card do no work | **APPLIED** | All three sentences are gone (grep for "What is not built", "isn't a promise", "That record is the product" returns nothing in `SCRIPT.md`). The card is resolved to one length: `CHOREOGRAPHY.md:203-208` "### Shot 10 · `1:50.9 → 1:55.0`" and "**Hold 4.1 s**". |
| 10 | MAJOR | Nine words of disclaimer on frame 1 | **APPLIED** | `SCRIPT.md:57`: "**SYNTHETIC FIXTURES** plate on both". `assets/cards.html:101`: `<div class="strip syn" id="strip-syn">Synthetic fixtures</div>`. The full sentence is on neither the plate nor the card. |
| 11 | MAJOR | The argument sits in 12 to 15 px type | **PARTLY APPLIED** | The rule is stated and measured: `CHOREOGRAPHY.md:216-219`, "Nothing that carries the argument may be smaller than **2% of frame height** once captured ... Record the console at a **1280 CSS px viewport with 2× device scale**". But shot 4 then instructs 85% zoom (`:112`), and at a 1280 CSS px viewport 85% zoom puts 15 px type at **1.77%**, below the rule's own floor. See D1: the two fixes cannot both be obeyed. |
| 12 | MINOR | Two product names on the same screen | **APPLIED** | `CHOREOGRAPHY.md` shot 4: "**The console's `h1` must not be in frame.**" and checklist item 10. |

## A2. Review 1, the minors the fixes touched

| # | Finding | Verdict | Evidence |
|---|---|---|---|
| 3 | The opening's justification claims more than the research has | **APPLIED** | `SCRIPT.md:44-46`: "**Unverified** in that research: whether the first *frame* should be product or title card ... not a measured norm." |
| 8 | The timing table's arithmetic is wrong in two rows | **APPLIED** | Every cell of `SCRIPT.md:193-202` now reproduces. The table is right, and its headline total is right. Its two per-beat rows were still computed from the wrong count until 08:05Z; they are correct now (see B1). |
| 13 | The video never says Solana about its own work | **APPLIED** | `SCRIPT.md:97-98`: "This program is deployed on Solana devnet." |
| 14 | The rehearsal band permits an over-length video | **PARTLY APPLIED** | `REHEARSAL.md:119-126` now ends "**The ceiling is 1:54 of speech, whatever the word count.**" The band's own top label is still wrong: it prints "1:47 - 1:52 of speech | 121-126 wpm" and 1:47 at 227 words is **127.3 wpm** (B5). |
| 15 | The argument dies on mute | **APPLIED as recorded** | `CHOREOGRAPHY.md` §0.1, four lower thirds. `REVIEWS.md` records this as TASTE and kept. Not reopened. |

## A3. Review 2, the two blockers and six majors

Numbering as in the 07:58 text that `REVIEWS.md` summarises.

| # | Sev | Finding, one line | Verdict | Evidence, current text |
|---|---|---|---|---|
| 1 | BLOCKER | "This is not." spoken over a frame of generated numbers | **PARTLY APPLIED** | In the script: `SCRIPT.md:97` "This signature is not." In the shot: `CHOREOGRAPHY.md:154-155` as above. **In the sheet he reads aloud it is not fixed:** `REHEARSAL.md:210`, "> **4.** Everything before this was generated. / This is not." That is the sentence review 2 called the one that would sink the entry, still sitting in §5 of the rehearsal plan, which pass 1 tells him to read the breath points off. |
| 2 | BLOCKER | "A transfer at 1.25 SOL executes" implied money moved | **PARTLY APPLIED** | `SCRIPT.md:98-99`: "A test transfer priced at one point two five SOL executes." **`REHEARSAL.md:211-212` still reads:** "> Solana devnet: / face one SOL, / cap twenty five hundred basis points. / A transfer at one point two five SOL executes." Two words of the fix are missing from the only document a mouth reads. |
| 3 | MAJOR | One reason given for two refusals, and wrong for the upper bound | **APPLIED** | `SCRIPT.md:77-78`: "the cap hides the top, and nothing recorded a listing." `CHOREOGRAPHY.md:128-133` requires "**In frame: all six rows**", with `cap_mass_dominates` named as "not optional". Both halves of the fix, in both documents. |
| 4 | MAJOR | Record parameters given to the program | **PARTLY APPLIED** | `SCRIPT.md:98`: "The record: face one SOL". `CHOREOGRAPHY.md:177`: "The record's parameters are spoken here, on the card that prints them, and nowhere else." **`REHEARSAL.md:210-211` still says:** "This program is DEPLOYED on Solana devnet: / face one SOL". The colon is unchanged. |
| 5 | MAJOR | The plate asserts and lets nobody test | **PARTLY APPLIED** | The spec is right: `CHOREOGRAPHY.md:12` "`DEVNET · REAL TRANSACTION · SIGNATURE RESOLVES`", and the overlay asset matches, `assets/cards.html:104`. **The two cards do not:** `assets/cards.html:71` and `:87` both read `<div class="badge dev">DEVNET · real transaction</div>`. Shots 7 and 8 are captured from those cards at 1920×1080 (`CHOREOGRAPHY.md` shots 7 and 8, "Asset"), so the wording review 2 asked to replace is baked into two of the three Devnet frames. `CHOREOGRAPHY.md` §3's ADMITTED and REFUSED blocks list no badge line at all, so the document cannot catch it. |
| 6 | MAJOR | "labelled so" is true only on one of two surfaces shot 9 allowed | **APPLIED** | `CHOREOGRAPHY.md:194-197`: "**The block, not the `[UNVALIDATED]` badge** ... the badge says unvalidated, which is a different claim." The alternative was deleted, not kept as an option. |
| 7 | MAJOR | Shot 9 carried a DEVNET plate over a fixture frame | **APPLIED** | `CHOREOGRAPHY.md:192`: shot 9 is "**SYNTHETIC** ← the plate switches back", and `:21-24` gives the reason. |
| 8 | MAJOR | The compensating sentence for the short plate does not exist | **APPLIED** | `CHOREOGRAPHY.md:26-30`: "The plate stands alone; it is not backed by a spoken sentence containing the full wording ... Earlier drafts of this file claimed the full sentence was also spoken and printed on the end card. It is not, and it does not need to be." The claim is gone rather than the mitigation invented. `assets/cards.html` end card confirms it is not printed. |

## A4. Review 3, majors

| # | Sev | Finding, one line | Verdict | Evidence, current text |
|---|---|---|---|---|
| 1 | MAJOR | The choreography was not re-cut, so every boundary is 0.8-1.9 s early | **PARTLY APPLIED** | Eight of the script's nine beat boundaries now appear verbatim in the shot list (0:00.0, 0:19.7, 0:44.7, 1:03.9, 1:31.7, 1:32.7, 1:50.9, 1:55.0), and the badge switch moved from 1:01.5 to the beat-4 frame. The ninth did not land: `SCRIPT.md:74` starts beat 3 at **0:45.7**, `CHOREOGRAPHY.md:106` starts shot 4 at **0:44.7**, and `CHOREOGRAPHY.md:94` ends shot 3 at **0:43.7** where the script ends beat 2 at 0:44.7. And `CHOREOGRAPHY.md:21` still says "**The switch happens once, at 1:02.9, and it switches back at 1:31.3**", against the shot list's 1:03.9 and 1:32.7. |
| 2 | MAJOR | 228 short words, not 234 spoken, and the floor is not 120 | **PARTLY APPLIED** | `SCRIPT.md:4`: "221 written words, 227 as spoken", and `:216`: "227 spoken words is inside 2:00 from 120 wpm upward", which is arithmetically correct (floor 119.5, B5). **`REHEARSAL.md:187` still says** "The script is 229 words", and `:121` still mislabels the band's top as 126 rather than 127.3. |
| 3 | MAJOR | Three documents, three end-card lengths | **PARTLY APPLIED** | `SCRIPT.md:202` "4.1 s (3 of them silent)" and `CHOREOGRAPHY.md:208` "**Hold 4.1 s**, of which the last 3 s are silent" agree with each other. **`SCRIPT.md:207` still says** "+ 2 s holds + 4 s of card", **`REHEARSAL.md:125-126` still says** "four seconds of card", and **`REVIEWS.md:80` still says** "the card is 7 s". Three lengths remain across four documents. The "3 of them silent" is also now wrong in both places that print it (B3). |
| 4 | MAJOR | The strongest sentence in the close is spoken 16 s after its shot | **APPLIED, by a different cut** | The sentence is gone: `SCRIPT.md:140` records "the repeated 'two transactions on devnet' sentence was cut", and beat 5 now ends on the refusal the frame is showing. `REVIEWS.md` records the refusal of the *move* and this as the substitute. No residual. |
| 5 | MAJOR | The `[SIMULATED] 0 arms shown` panel is 15 px above the chain slot | **PARTLY APPLIED** | The offsets and the instruction exist, but on the wrong shot: `CHOREOGRAPHY.md:133-137` puts them in shot 5, which is scrolled to the refusals, where the panel is not in frame. Shot 6, the one that scrolls to the chain slot, carries no such instruction and no offset. Measured on the rendered page: the `What the engine refuses` heading is at y=1986, the last refusal row at y=2249, and the `Show the refusal` control at y=2912, so at shot 5's scroll position the panel that must not appear is 663 px out of frame and the instruction is inert. Shot 6, the one that must frame the chain slot further down, carries no offset and no rule. |
| 6 | MAJOR | The `[EXACT]` ceiling line and the fixture strip cannot share a 1080 frame | **PARTLY APPLIED** | The instruction landed: `CHOREOGRAPHY.md:112-115` "**Record the console at 85% browser zoom.**" But the number behind it is wrong and the instruction collides with A1 row 11. Measured on the rendered page (B6): strip at y=30, `[EXACT]` line at y=1186, so the gap is **1156 px, not the 1201 px** printed in `CHOREOGRAPHY.md:113` and `REVIEWS.md:49`. The conclusion survives at a 1920×1080 viewport and fails at the 1280×720 one §2 mandates. |
| 7 | MAJOR | The console's `[EXACT]` line contradicts the numbers beat 4 speaks | **APPLIED** | `SCRIPT.md:117-119`: "The devnet numbers are spoken **only while the cards are on screen**". `CHOREOGRAPHY.md:151`: "**The voice says nothing about face or cap on this frame.**" Beat 4's own words match the card, not the console page, and the card prints them (`assets/cards.html:63`). |
| 8 | MAJOR | Shots 1-3 record the pre-rebuild bundle | **APPLIED as a conditional** | `CHOREOGRAPHY.md:64-71` now branches on what `curl` returns and names the forbidden strings for each branch. The decision itself (V3) is still the operator's, which is what the finding asked for. |
| 10 | MAJOR | The badges cannot be burned in, the shots cannot be joined, the voice cannot be added | **NOT APPLIED** | `REHEARSAL.md` §1 still reports the machine's limits correctly, and the plan still requires "burned in by the edit" plates plus ten joined shots plus a voice. Decision V1 is open. This is a decision, not a text defect, and nothing in the last three hours moved it. |

Review 3's minors, for completeness: **11** (`matchesCurrentQuote`) APPLIED, the two commands and
the assertion are in `CHOREOGRAPHY.md` shot 6 and `REHEARSAL.md` §2.4. **12** (22 px mono) NOT
APPLIED, `CHOREOGRAPHY.md:11` still says "22 px mono" and the overlay asset is `font:600 20px/1`
(`assets/cards.html`, `.strip`). **13** (six rows) APPLIED, `CHOREOGRAPHY.md:128`. **14**
(`tkt_00077`) APPLIED, `CHOREOGRAPHY.md:60`. **15** (pass 2 passes failing reads) PARTLY,
`REHEARSAL.md:171` still says "the badge changes exactly once, at 1:01.5". **16** (1404 px) NOT
APPLIED, `REHEARSAL.md:46` unchanged.

---

# B. Numbers, recomputed

Every number below is mine. Where the documents print something else, the difference is stated.

## B1. The words

```
$ python3  # extract the five blockquotes under '### Beat N' in SCRIPT.md
$ wc -w beat1.txt beat2.txt beat3.txt beat4.txt beat5.txt
  39 beat1.txt
  52 beat2.txt
  38 beat3.txt
  58 beat4.txt
  34 beat5.txt
 221 total
$ cat beat1.txt ... beat5.txt > all.txt && wc -w all.txt
221 all.txt
$ grep -o -E 'MLH|Token-2022|one-unit' all.txt | sort | uniq -c
      1 MLH
      1 Token-2022
      1 one-unit
```

| Beat | Written | Spoken | Difference |
|---|---|---|---|
| 1 | 39 | 41 | `MLH` = 3 |
| 2 | 52 | 52 | none |
| 3 | 38 | 38 | none |
| 4 | 58 | 58 | none |
| 5 | 34 | 38 | `Token-2022` = 4, `one-unit` = 2 |
| **total** | **221** | **227** | +6 |

`SCRIPT.md:4` and `:16` say 221 and 227. Both are right. `SCRIPT.md:10` says "**Why 220 and not
the 280 the brief asked for**", which is the same file disagreeing with itself by one word; the
count is 221. `REVIEWS.md:20` says "from 229 to 221", right. `REVIEWS.md:71` says "220 written
and 226 spoken", wrong by one on both counts and inconsistent with `REVIEWS.md:20`.

## B2. The beats at 125 wpm, the holds, the card, the file

Speech is `words x 60 / 125`.

| Beat | Spoken | Duration | Ends at |
|---|---|---|---|
| 1 | 41 | 19.68 s | 0:19.68 |
| 2 | 52 | 24.96 s | 0:44.64 |
| hold | | 1.00 s | 0:45.64 |
| 3 | 38 | 18.24 s | 1:03.88 |
| 4 | 58 | 27.84 s | 1:31.72 |
| hold | | 1.00 s | 1:32.72 |
| 5 | 38 | 18.24 s | 1:50.96 |
| end card | | 4.10 s | 1:55.06 |

| File | Value | Against the documents |
|---|---|---|
| speech alone | 227 words = **108.96 s** | `SCRIPT.md:211` prints 109.0 at 125 wpm; the pace table's header still says "speech (226)" while its cells are computed from 227 |
| + 2 s holds + 4.1 s card | **115.06 s = 1:55.1** | `SCRIPT.md:4`, `CHOREOGRAPHY.md:3` print 1:55.0. The 0.06 s is the sum of rounded per-beat cells, not an error |
| + 2 s holds + 4.0 s card | 114.96 s = 1:54.96 | this is the model `SCRIPT.md:207` and `REHEARSAL.md:125` use |
| + 2 s holds + 7.0 s card | 117.96 s = 1:58.0 | this is the model `REVIEWS.md:80` still uses |

Every version is inside 2:00. The cap margin is **4.9 s** on the plan as choreographed.

## B3. The card

| Statement | Source | Recompute |
|---|---|---|
| card runs 1:50.9 to 1:55.0 | `SCRIPT.md:201-202`, `CHOREOGRAPHY.md:203` | 4.1 s. Correct. |
| "3 of them silent" | `SCRIPT.md:202`, `CHOREOGRAPHY.md:208` | The last word lands at **1:50.96** and the card starts at **1:50.9**, so the card carries **0.0 s of voice and 4.1 s of silence**. The parenthetical is **1.1 s** wrong in both documents. It is a leftover from the 7 s card: 7.0 - 4.0 = 3.0 was right when the card was 7 s. |
| "Hold 4.1 s" | `CHOREOGRAPHY.md:208` | matches the boundary arithmetic |
| "the card is 7 s" | `REVIEWS.md:80` | 1:50.9 + 7.0 = 1:57.9, which no live document says |

## B4. Every shot boundary, summed

```
shot |   in    |   out   | length
  1  |  0:00.0 |  0:19.7 |   19.7
  2  |  0:19.7 |  0:31.5 |   11.8
  3  |  0:31.5 |  0:43.7 |   12.2
  4  |  0:44.7 |  0:54.8 |   10.1
  5  |  0:54.8 |  1:03.9 |    9.1
  6  |  1:03.9 |  1:11.6 |    7.7
  7  |  1:11.6 |  1:21.7 |   10.1
  8  |  1:21.7 |  1:31.7 |   10.0
  9  |  1:32.7 |  1:50.9 |   18.2
 10  |  1:50.9 |  1:55.0 |    4.1
sum of shot lengths = 113.0 s
gaps with no shot assigned: [(43.7, 44.7, 1.0), (91.7, 92.7, 1.0)]
sum + gaps = 115.0 s = 1:55.0
```

**The ten boundaries and the two 1.0 s gaps sum to 1:55.0, which is the total the file claims.**
Two 1.0 s windows belong to no shot. The first is where beat 2's last two words ("is ours")
actually land (B7), so it is not silent; the second is a real pause before the switch back.

## B5. The pace floor, and the rehearsal band against it

Solving `227 x 60 / w + holds + card <= 120`:

```
card 4.0s:  w >= 227*60/114.0 = 119.474 wpm  -> slowest whole wpm that fits = 120 (file 119.500 s)
card 4.1s:  w >= 227*60/113.9 = 119.579 wpm  -> slowest whole wpm that fits = 120 (file 119.600 s)
card 7.0s:  w >= 227*60/111.0 = 122.703 wpm  -> slowest whole wpm that fits = 123 (file 119.732 s)
```

| Reading the floor | Floor |
|---|---|
| **as choreographed (2 s holds, 4.1 s card)** | **119.6 wpm** |
| as `SCRIPT.md` §4's pace table models it (4.0 s card) | 119.5 wpm |
| on the 226 spoken words `SCRIPT.md:207` and `REVIEWS.md:71` still print | 119.0 wpm |
| if the card is the 7 s `REVIEWS.md:80` records | 122.7 wpm |

`SCRIPT.md:216` says "inside 2:00 from 120 wpm upward". At 227 words that is right: 119 wpm
produces 2:00.4 and its own table says "over". The floor is 119.5, so 120 clears it by 0.0 s
of margin at the boundary and 0.5 wpm of slack. `REVIEWS.md:71` reaches the same 120 from 226
words, where the true floor would be 119.0, so its answer is right and its inputs are stale.

The rehearsal band, recomputed at 227 words:

```
1:45 of speech =  129.7 wpm
1:47 of speech =  127.3 wpm
1:52 of speech =  121.6 wpm
1:54 of speech =  119.5 wpm
```

| `REHEARSAL.md:119-123` prints | Recomputed | Verdict |
|---|---|---|
| under 1:45 = faster than 129 | 129.7 | correct |
| 1:47 - 1:52 = 121-126 | **121.6 - 127.3** | the top label is **1.3 wpm** low |
| 1:52 - 1:54 = 119-121 | 119.5 - 121.6 | correct to the whole wpm |
| over 1:54 = slower than 119 | 119.5 and slower | correct, and 1:54 now sits **exactly on the floor**, so the last passing band is a single point wide. A read at 1:54 produces a 1:55.1 file. |

**Against the floor, pass 2 is now correct at the bottom and mislabelled at the top.** That is
the opposite of the defect review 1 finding 14 and review 3 finding 15 found, and it is a
straight improvement.

## B6. The one geometry number both documents get wrong

Rendered the pinned payload through `tools/guidance.py` and `page.render()` with no server, then
measured the DOM in headless Chromium at four viewports:

```
cssWidth  1280  stripY 30 (STRONG)  exactY 1208  gap 1178
cssWidth  1506  stripY 30 (STRONG)  exactY 1208  gap 1178
cssWidth  1920  stripY 30 (STRONG)  exactY 1186  gap 1156
cssWidth  2259  stripY 30 (STRONG)  exactY 1186  gap 1156
```

`CHOREOGRAPHY.md:113` prints "at y≈30 and the `[EXACT]` ceiling line at y≈1186 ... **1201 px
apart**". 1186 - 30 = **1156**. The 1201 is 45 px wrong, and `REVIEWS.md:49` repeats it. The
y values themselves are right.

Fit conditions, using the measured gap:

```
1280x720 CSS viewport (2x scale)
   zoom 1.00: visible CSS height   720.0  vs gap 1178  -> does not fit; 15 px type = 2.08% of frame height
   zoom 0.85: visible CSS height   847.1  vs gap 1178  -> does not fit; 15 px type = 1.77% of frame height
   zoom 0.60: visible CSS height  1200.0  vs gap 1178  -> FITS;         15 px type = 1.25% of frame height
1920x1080 CSS viewport (1x)
   zoom 1.00: visible CSS height  1080.0  vs gap 1156  -> does not fit; 15 px type = 1.39% of frame height
   zoom 0.85: visible CSS height  1270.6  vs gap 1156  -> FITS;         15 px type = 1.18% of frame height
```

## B7. Each shot's voice against its slot

| Shot | Span | Words it must carry | Time at 125 wpm | Slack |
|---|---|---|---|---|
| 1 | 19.7 | beat 1, 41 | 19.68 | +0.02 |
| 2-3 | 24.0 | beat 2, 52 | 24.96 | **-0.96** |
| 4-5 | 19.2 | beat 3, 38 | 18.24 | +0.96 |
| 6 | 7.7 | "Everything before this was generated. This signature is not. This program is deployed on Solana devnet." (16) | 7.68 | +0.02 |
| 7 | 10.1 | "The record: face one SOL... A test transfer priced at one point two five SOL executes." (22) | 10.56 | **-0.46** |
| 8 | 10.0 | "One lamport higher... not the app." (20) | 9.60 | +0.40 |
| 9 | 18.2 | beat 5, 38 | 18.24 | -0.04 |
| 10 | 4.1 | silent | 0 | +4.10 |

Beat 2's slot needs **130 wpm** and beat 3's accepts **118.8**, so the cut between shot 3 and
shot 4 is the one place where a 125 wpm read does not fit the plan as drawn: the last two words
of beat 2 land at 1:44.64, in what the shot list shows as a 1.0 s hold. Shot 7's words need
0.46 s more than its card holds, so "executes" falls onto the REFUSED card.

## B8. The read sheet, measured

`REHEARSAL.md` §5, extracted and stripped of the breath slashes and the bold beat numbers:

```
  39 read1.txt      (script beat 1: 39)
  53 read2.txt      (script beat 2: 52)
  38 read3.txt      (script beat 3: 38)
  53 read4.txt      (script beat 4: 58)
  34 read5.txt      (script beat 5: 34)
 217 total         (script total:      221)
```

Beat 4 is **five words short** of the script, and the five missing words are exactly the three
fixes: "This **signature** is not" (-1), "**The record:**" (-2), "A **test** transfer **priced**
at" (-2). Beat 2 is one word long ("labelled in frame" where the script says "labelled here").

---

# C. Consistency across the four documents

1. **Word count.** `SCRIPT.md` 221 written / 227 spoken. `REVIEWS.md:20` 221. `REVIEWS.md:71`
   220 written / 226 spoken. `SCRIPT.md:10` "Why 220". `REHEARSAL.md:187` 229. `CHOREOGRAPHY.md`
   states no count. Four different numbers across the four documents for one script.
2. **Pace floor.** `SCRIPT.md:216` 120. `REVIEWS.md:71` 120. `REHEARSAL.md:121` labels the band
   121-126, implying a 127.3 top. The arithmetic floor is **119.5** (4.1 s card) and **122.7**
   if `REVIEWS.md:80`'s 7 s card is real. Three answers.
3. **End-card start.** All three that state it agree: **1:50.9** (`SCRIPT.md:128`, `:202`,
   `CHOREOGRAPHY.md:203`). `REVIEWS.md` does not state one. No disagreement.
4. **End-card length.** **4.1 s** (`SCRIPT.md:202`, `CHOREOGRAPHY.md:208`), **4.0 s**
   (`SCRIPT.md:207`, `REHEARSAL.md:125`), **7.0 s** (`REVIEWS.md:80`). Three lengths, and the
   "3 of them silent" parenthetical is 1.1 s wrong in both places that print it.
5. **Badge wording.** `SYNTHETIC FIXTURES` is consistent in `SCRIPT.md:57`,
   `CHOREOGRAPHY.md:11` and `assets/cards.html:101`. `DEVNET · REAL TRANSACTION · SIGNATURE
   RESOLVES` is in `CHOREOGRAPHY.md:12` and `assets/cards.html:104`, and **not** on the two
   card plates, `assets/cards.html:71` and `:87`, which read `DEVNET · real transaction`. Shots 7
   and 8 are those cards. `SCRIPT.md` states no Devnet wording at all.
6. **Switch times.** `CHOREOGRAPHY.md:21` **1:02.9** and **1:31.3**. `CHOREOGRAPHY.md:43` lower
   third at **1:02.9**. `CHOREOGRAPHY.md` shots 6 and 9: **1:03.9** and **1:32.7**.
   `REHEARSAL.md:171` **1:01.5**, and "changes exactly once" when it changes twice. Three pairs
   of numbers.
7. **Ticket id.** `CHOREOGRAPHY.md:60` `tkt_00077`. `REVIEWS.md:58` `tkt_00077`. `SCRIPT.md` and
   `REHEARSAL.md` never name it (`SCRIPT.md:226` says only "the one fixture ticket chosen for
   shots 1-2"). No contradiction, one gap.
8. **Refusal rows in frame.** 6 in `SCRIPT.md:81` and `:87`; 6 in `CHOREOGRAPHY.md:128-133` with
   the order given and `cap_mass_dominates` flagged not optional; 6 in `REVIEWS.md:32` and
   `:51`; `REHEARSAL.md` silent. Consistent, four for four.
9. **Beat 2 and beat 3 boundaries.** `SCRIPT.md`: beat 2 ends 0:44.7, hold to 0:45.7, beat 3
   runs to 1:03.9. `CHOREOGRAPHY.md`: shot 3 (beat 2, second half) ends **0:43.7**, shot 4 (beat
   3, first half) starts **0:44.7**. The two documents are 1.0 s apart on the same two beats,
   and the script's version is the correct one (beat 2 is 24.96 s from 0:19.7).
10. **The quoted floor sentence.** `CHOREOGRAPHY.md:118` still puts the voice's words in
    quotation marks as "the highest price this **record** has seen"; `SCRIPT.md:76-77` and
    `REHEARSAL.md:207` say "**tier**". The choreography is quoting a superseded line.
11. **The end card's line count.** `CHOREOGRAPHY.md:206` "**Three lines, exactly**";
    `assets/cards.html` end card and `CHOREOGRAPHY.md`'s own §3 END block both render **four**.
12. **Badge type size and shape.** `CHOREOGRAPHY.md:11` "22 px mono, solid background, squared
    left edge". The overlay asset is `font:600 20px/1`, `border-radius:4px`, and only the Devnet
    variant has the squared left edge (`assets/cards.html`, `.strip` and `.strip.dev`). The row
    describes a plate that exists in neither asset.
13. **`ADMITTED` / `REFUSED` caps.** `CHOREOGRAPHY.md` §3 prints them in caps; `assets/cards.html`
    renders `Admitted` and `Refused` in mixed case with no `text-transform`. Review 3 measured
    this and it has not changed.

---

# D. New damage

Nothing here is fatal. Two items are MAJOR, and one of those two is a collision between two
fixes that were each correct on their own.

**D1. MAJOR. The 2% legibility rule and the 85% zoom rule cannot both be obeyed on the console.**
`CHOREOGRAPHY.md:216` sets the floor ("nothing that carries the argument may be smaller than
**2% of frame height**"), `:218` sets the viewport ("a **1280 CSS px viewport with 2× device
scale**"), and shot 4 `:112` sets the zoom ("**85% browser zoom**"). The 85% figure was derived
at a 1920×1080 viewport, where it works: 1156 px gap against 1270 CSS px of visible height. At
the 1280×720 viewport §2 mandates, the gap measured is **1178 CSS px** against **847** of
visible height at 85%, so the strip and the `[EXACT]` line still cannot share the frame, and the
zoom that would fit them (about 60%) puts 15 px type at **1.25%**, well under the 2% floor. The
two instructions were applied independently, each from a different review, and neither was
re-measured against the other. Someone has to decide which rule gives for shot 4. My reading:
keep the 2% rule, accept that the strip is off frame on the console shots, and lean on the page's
own tags, since the recommendation line carries `[UNVALIDATED]`, the ceiling line carries
`[EXACT]`, and the rest of the page's figures carry their own `[FIXTURE]` chips (measured: the
counts row is six individually badged chips, and the `3 on-chain transactions` chip is badged
`[DEVNET]`). That resolution is the operator's call, not mine.

**D2. MAJOR. The rehearsal read sheet still speaks both blockers.** `REHEARSAL.md:210-212` is the
only text in the package that a mouth reads out loud, pass 1 says to read it, and it carries
"This is not.", "A transfer at one point two five SOL executes." and "This program is DEPLOYED on
Solana devnet: / face one SOL". Measured at B8: beat 4 of the read sheet is 53 words against the
script's 58, and the five missing words are the three fixes. Every other document was corrected
at 08:05; this one was corrected in beats 1, 3 and 5 and missed in beat 4. If the take is read
from this sheet, the video ships both of review 2's blockers with the script claiming they are
fixed.

**D3. MINOR. Shot 7's voice is 0.46 s longer than its card.** "A test transfer priced at one
point two five SOL executes" needs 10.56 s in a 10.1 s slot (B7), so "executes" lands on the
REFUSED card. Shot 8 then has 0.40 s of slack it does not use. Net, the two cards' voice fits,
but the sentence that says the transfer succeeded finishes over the frame that shows a refusal.

**D4. MINOR. The lower third about the refused slot points at the admitted card.**
`CHOREOGRAPHY.md:44`: "1:24.0 | `refused: slot 519846008` | gives a judge a mnemonic; the full
signature is on the card at **1:11.6**". The card at 1:11.6 is shot 7, the ADMITTED card; the
refused card is shot 8, 1:21.7 to 1:31.7. The lower third fires on the right frame and cites the
wrong one.

**D5. MINOR. Shot 2's cut instruction does not match its own in-point.** `CHOREOGRAPHY.md` shot 2:
"**Cut on the word 'transaction'**". At 125 wpm that word is spoken at **0:21.6** (it is the 5th
word of beat 2, which starts at 0:19.68) and the shot's in-point is **0:19.7**, so the cut as
drawn lands **1.9 s** before the word. The instruction is right and the number is not; an editor
following the numbers will cut early.

**D6. MINOR. Shot 9 is now the longest still frame in the cut, and it grew.** 18.2 s
(1:32.7 to 1:50.9), 15.8% of the file, one held panel. Before the 08:05 rewrite it was 14.8 s.
Review 1 asked for it to be split into two ~10 s shots; `REVIEWS.md` neither took nor rejected
the split, and the effect of the rewrite was to lengthen the shot the finding was about.

**D7. MINOR. The card plates on shots 7 and 8 ship the superseded wording.** See A3 row 5 and
C5. Not a false claim, a missing test: the frame says the transaction is real and does not say
what a viewer can do with it, which is the distinction review 2 asked for and the overlay asset
already gets right.

**D8. MINOR. A 1.0 s gap that is not silent, and one that is.** The shot list leaves 43.7-44.7
and 91.7-92.7 unassigned. The first is filled by beat 2's last two words (B7), so it is a hold
on shot 3 with speech over it; the second is a genuine pause. The plan budgets "2 s of holds"
and gets them, but not where the shot list shows them. No effect on the total.

**D9. MINOR. `REVIEWS.md` records a card length no live document uses.** "the card is 7 s,
because the URL needs to be readable and the last 3 s are silent anyway" (`REVIEWS.md:80`). The card is
4.1 s and every second of it is silent. The rejection it defends was about a 3 s proposal, and
4.1 s satisfies that argument just as well, so the decision is not wrong; the sentence describing
it is.

**Things I checked for damage and did not find.** No beat repeats itself: the `chain` echo between
beat 4's "The chain refuses it, not the app" and beat 5's "That chain refusal is the feature" is
the fix that gave the pronoun an antecedent, and it reads as a bookend, not a repeat. No sentence
is unsayable at 125 wpm: beat 1 is 3.0 syllables a second by review 3's count and every beat's
required pace is between 118.8 and 130.0 wpm (B7). No frame contradicts the voice on the same
frame: the admitted card prints the arithmetic the voice speaks, the refused card prints the
error the voice speaks, the refusal block prints "The model is not fitted" under "The model is
unfitted", and shot 6's strip is scoped by its own text ("every number on this page is computed
from a synthetic fixture ... The chain slot at the bottom prints what a verified devnet artefact
records"), so it does not contradict "This signature is not". The three rewrites of the close did
not leave a dangling clause: "That chain refusal" has a referent in beat 4 and in the block on
screen. Beat 1 and the end card both say "prices from the resale record / capped on chain", which
is a callback and not a repetition.

---

# E. The one thing

Change `REHEARSAL.md` §5, beat 4, to the words in `SCRIPT.md:97-99`: "This signature is not.",
"The record: face one SOL, cap twenty five hundred basis points", "A test transfer priced at one
point two five SOL executes". That is the single change worth making before the take, because it
is the only place in the package where a fix that every document now claims is absent from the
only artefact a human actually performs, and because the two sentences it still carries are the
two the second review called blockers: one claims a whole frame for the chain when the same frame
prints fixture counts, and one implies a customer paid 1.25 SOL when the transaction moved one
token of a 0-decimal mint and no SOL at all. Everything else in this report is either a framing
decision the operator can make in the edit (D1), a document disagreeing with itself about a
number that lands inside the cap whichever version you use (C1, C4, C6), or a plate whose
wording is already correct on the asset that gets composited (D7). This one is different in kind:
it is a recording risk, it costs five words and about a minute, it is measurable (the read sheet
is 53 words against the script's 58, B8), and if it is missed the video's most checkable beat goes
out with both of its known false claims intact while the script says they were fixed.
