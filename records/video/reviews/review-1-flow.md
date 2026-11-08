# Review 1: narrative and flow

**Reviewer:** first independent pass. I did not write the script, the choreography or the cards.
**Read, in order:** `SCRIPT.md`, `CHOREOGRAPHY.md`, `inputs/rules-verified-2026-11-08.md`,
`inputs/winner-video-research.md` (§2, §3, §4), `inputs/build-state-matrix.md` (§3, §4). Then
`REHEARSAL.md`, `OPEN-DECISIONS.md` and `assets/cards.html`, which appeared in the directory
between 07:45Z and 07:47Z while this review was being written, plus the console's own
presentation code and stylesheet to check what a frame actually contains.

**How each judgement is grounded.** Three tags, used throughout. MEASURED means a number or a
quoted sentence out of one of those inputs, with the section given. INFERENCE means my reading of
that measurement. TASTE means editorial judgement with no measurement behind it, and there are
three of those: the prominence argument in finding 6, the choice of which three sentences to cut
in finding 9, and finding 15 in full. Everything else rests on a measurement or on a count I ran
myself.
**Not judged here:** whether the claims are true. A separate reviewer audits facts. Where a
claim looked wrong I say so only when the *script contradicts its own screen*, because that is a
comprehension failure, not a factual one.
**The tree moved under me.** `REHEARSAL.md` and `OPEN-DECISIONS.md` did not exist when I started.
Everything below is against `SCRIPT.md` at 07:45Z, `CHOREOGRAPHY.md` at 07:45Z and
`assets/cards.html` at 07:43Z. If any of the three changed after that, re-read the finding it
touches before acting on it.

---

## 1. The word count, measured myself

`wc -w` on the five blockquoted beats in `SCRIPT.md` §1, with `NAME` counted once, which is the
method `SCRIPT.md` §4 states:

| Beat | My count | SCRIPT.md's count | Match |
|---|---|---|---|
| 1 | 37 | 37 | yes |
| 2 | 50 | 50 | yes |
| 3 | 37 | 37 | yes |
| 4 | 53 | 53 | yes |
| 5 | 52 | 52 | yes |
| **total** | **229** | **229** | **yes** |

**`SCRIPT.md`'s count of 229 is right, to the word, on all five beats.** The per-beat timing
column is also right: 37/50/37/53/52 at 125 wpm is 17.8, 24.0, 17.8, 25.4, 25.0 s and 109.9 s of
speech. But the table's own sum is wrong, twice, and the error is inherited by the choreography's
headline. See finding 8.

---

## 2. The seven questions, answered short

**Q1. Does the story hold for 116 seconds?** It holds for 88 and then decelerates. Attention
drops at **1:28.0 to 1:44.0**: shot 9, 16 seconds, one static console panel held with nothing
moving, while the voice reads five things that do not exist. That is the longest still frame in the
cut and it lands immediately after the video's peak. Secondary drop at **0:30.0 to 0:42.8**, the
organiser analytics page, under the most abstract sentence in the script. Findings 7 and 9.

**Q2. Is the order right, product UI before problem?** Yes. The measured norm is unambiguous: 8
of 8 videos with speech name the product or event inside ten seconds and 0 of 8 open with a market
statistic (`winner-video-research.md` §3), and the demo signal in the one measured compliant 2:00
winner arrives at 3.9 s (§2.2). Opening on the UI puts that signal at 0.0. Keep it. Two caveats:
the supporting sentence in `SCRIPT.md` claims more than the research supports (finding 3), and the
real defect in beat 1 is not its order, it is that the beat never says what the product does
(finding 1).

**Q3. Is a refusal a satisfying middle beat?** As written, no. It reads as an excuse, and it is
aimed at the wrong criterion. It can be made to read as rigour with one sentence, and that
sentence already exists verbatim in the console's own labels. Finding 4.

**Q4. Is the closing list strong or does it end on absence?** It ends on absence, twice: six
negatives in 52 words, and the last clause spoken before "Thank you" is a prior-work compliance
statement. The disclosure instinct is right and measured (Puzzlify, §4.4). The volume and the
last position are wrong. Concrete alternative with a word count in finding 7.

**Q5. Does the badge switch read as an argument?** As specified, no. It is a technicality, and it
will not be noticed, because on the frame that carries it nothing else changes and the voice says
a sentence unrelated to it. One change fixes it, and it saves a word. Finding 6.

**Q6. What is doing no work?** Three sentences and about 25 seconds of held frame. Quoted in
finding 9.

**Q7. What would a judge say after one watch?** "A Solana ticket app where the chain caps resale
markup, but the data is fake and the model isn't trained." That is not the sentence the team
wants, and the gap is one clause in beat 1. Finding 1.

---

## 3. Findings

### 1. The first 43 seconds never say what the product does, so the judge's one-sentence summary will be wrong

**(a)** Beat 1, verbatim: `I'm NAME, and this is SeatPass, my demo for the MLH Solana Hackathon.
One face value, set by the organiser. What the seat is worth after that is decided in resale, and
the organiser never sees it.`

**(b)** 37 words and 17.8 seconds, and not one of them says what SeatPass does. They describe the
world the product lives in. The first statement of function in the whole video is at **0:42.8**:
`The engine answers with a floor, not a forecast.` The verb "price" appears earlier only as
`Across an event, that is enough to price the next one`, which asserts a capability without
saying what is delivered. So a judge spends 37% of the video knowing the name and the setting and
not the function. The measured norm covers the name and the event, not the function (§3: product
or event named in 8 of 8), so the norm is satisfied and the judge is still uninformed. The
criteria that suffer are Design and Completion (`rules-verified` §4, equal weight): a judge
cannot score "did the team put thought into the user experience" or "does the hack work" on
something they cannot describe in a sentence. This is the finding that decides the entry.

**(c)** Replace beat 1 with this, which keeps the rule-compliant opening form, states the problem
in one clause, and states the function in the next. It is the end card's own sentence, spoken:

> I'm NAME, and this is SeatPass, my demo for the MLH Solana Hackathon. An organiser sets one face
> value and never learns what the seat resells for. SeatPass prices from that resale record, and
> the chain caps the markup.

**39 words, +2.** It puts "prices" at 0:13 and "caps" at 0:16, both before the beat ends, and it
makes the two halves of the build (off-chain pricing, on-chain cap) audible in the first fifteen
seconds instead of at 0:43 and 1:02.

**(d) BLOCKER.**

---

### 2. The voice describes a valuation; the screen describes a price recommendation

**(a)** Beat 3: `It says the least a seat should fetch from the record`. The console line it plays
over says, verbatim from the label code: `[UNVALIDATED] Recommended primary price: at least {P}
SOL per ticket, {tier} tier.`

**(b)** A judge who only listens hears "this tells you what a seat is worth on resale". A judge
who reads the frame sees "recommended primary price". Those are different products, and the
team's thesis is the second one. The words "primary", "recommend" and "organiser" appear nowhere
in beat 3. Nothing in the video stages the decision the product changes: an organiser choosing a
primary price. The nearest thing is `and the organiser never sees it`, which states the gap and
never says the product closes it. This is the same defect as finding 1 seen from the middle of
the video, and it is why a one-watch summary comes back as "resale" rather than "primary price".

**(c)** Say the screen's own noun, and fix findings 4 and 5 in the same edit, because the three sit
on the same 18.7 seconds and cannot be solved separately. Replace beat 3 in full with:

> The console recommends a primary price and tags it unvalidated: a floor, not a forecast. The
> floor is the highest price this record has seen in the tier. It refuses an upper bound and a
> sale probability, because nothing recorded what a ticket was listed at.

**46 words, from 37. +9**: about 4.3 seconds at 125 wpm. What the three sentences do, against the
four criteria: sentence 1 uses the screen's own noun and names the honesty tag out loud (finding
5, no extra words because it rides on this sentence); sentence 2 gives the floor a mechanism a
judge can check (finding 4); sentence 3 converts two refusals into one cause, which is a claim
about the data rather than about the engine.

Note the constraint in `build-state-matrix.md` §3 item 18: a floor, not an optimum, and the cap is
not the primary price. This wording keeps that distance. If 46 words is too rich for the beat's
slot, drop sentence 2 and the beat returns to 34, but finding 4's defence goes with it and the
refusal is back to reading as an excuse.

**(d) MAJOR.**

---

### 3. The opening's justification claims more evidence than the research has

**(a)** `The first frame is the product, not a title card.` (`SCRIPT.md` §1, beat 1, "Why it opens
this way")

**(b)** The decision is right (see Q2). The justification is not supported by the file it cites.
`winner-video-research.md` §2.3 marks face, title card and problem slide as **Unverified**: "I
have no measurement of any of the three, and I will not infer them from speech." The measured
claims are the spoken name inside ten seconds (§3), the demo-signal proxy at 3.9 s (§2.2), and the
absence of market statistics in openings (§3). A script that cites a norm it does not have is the
kind of sentence that gets inherited by the next session as fact. It also hides the real cost of
the choice: 17.8 seconds of a scroll where the winners have finished orienting at ten.

**(c)** Rewrite the justification to what was measured: "the measured norm is the spoken name and
event inside ten seconds and no market statistic in any opening; the first-frame question is
Unverified, so this is a choice made on the demo-signal proxy, not a measured norm." No effect on
the cut.

**(d) MINOR.**

---

### 4. The refusal is the right beat aimed at the wrong criterion, and the mechanism that would defend it is already written on the page

**(a)** Beat 3 in full: `The engine answers with a floor, not a forecast. It says the least a seat
should fetch from the record, and refuses an upper bound and a sale probability: nothing recorded
what a ticket was listed at.`

**(b)** Three negations, no mechanism, no spoken number. A judge scoring four criteria equally
(`rules-verified` §4) hears this as follows. **Technology**: "did it use a particularly clever
technique?" A refusal is evidence of cleverness only if the judge first sees there was something
to compute; `the least a seat should fetch from the record` is indistinguishable from a lookup, so
the refusal has nothing to be rigorous about. **Completion**: "does the hack work?" A refusal
reads as a hole, and the script's own note attaches this beat to Completion ("what the engine will
not answer is part of what it does"), which is the weakest possible home for it. **Learning**: the
floor/ask distinction is the single most interesting thing the team learned about ticket markets
and the beat does not claim it. **Design**: nothing. And `rules-verified` §4 quotes the criteria
explicitly excluding "how well you pitch", so humility earns nothing on its own. The counter-
example the script cites, Puzzlify (§4.4), is not a refusal: it demoed a built interface and
disclosed one thing that was not running, in the closing seconds.

The fix is not more humility and not more negation. It is one mechanism sentence, and it is
already on the console, verbatim: `Value: at least {m} SOL per ticket. That is a floor, not an
estimate. It is the highest recorded price in this tier, and it is the most this record can
support.` The script spends 11 words on a vague gloss of that and never uses the specific version.

**(c)** Sentence 2 of the replacement in finding 2(c) is the fix:

> The floor is the highest price this record has seen in the tier.

**12 words, replacing 11. +1**, and it is inside the 46-word beat already counted there. Now the
refusal has a cause the judge can see (the record has bids and no asks), the floor has a mechanism
the judge can check against the screen, and the beat reads as rigour under Technology and as a
demonstrated distinction under Learning. One condition: the operator must vouch for "highest
recorded price in the tier" against the estimator, because the console's recommendation and its
own ceiling disagree (decision V2). If he will not vouch for it, use the weaker and still concrete
`a price this record has already seen`.

**(d) MAJOR.**

---

### 5. Four seconds of frozen frame over a number the voice will not name

**(a)** `CHOREOGRAPHY.md` shot 4: `Then hold: nothing moves for four seconds, because the number is
the subject.` And: `The voice does not say the number.`

**(b)** A 10.2 second shot, a third of it frozen, over a figure the script's own note says sits
130,000,000 lamports above the ceiling the same page prints. The reasoning behind keeping the value
out of the voice is sound. The conclusion drawn from it is not: it does not follow that the
existence and the status of the number must also go unnamed. As cut, a judge gets a large number, a
small warning tag they have to read, four seconds of stillness, and nothing said about either. That
is an unexplained red flag in the exact place the video stops moving, and stillness with no speech
over it is the one thing a tired judge will tab away from. `OPEN-DECISIONS.md` V2 already owns the
underlying defect; this finding is only about the cut.

**(c)** Name the label, not the value. Beat 3's replacement in finding 2(c) already opens with
`and tags it unvalidated`, which does this for **zero extra words**, so the only change at the edit
bench is cutting the hold from four seconds to two. Two seconds of stillness is a beat; four is a
stall.

**(d) MAJOR.**

---

### 6. The badge switch is a technicality, and the one change that makes it an argument is free

**(a)** `CHOREOGRAPHY.md` shot 6: `The cut is the argument.` The sentence spoken on that cut is
beat 4's opening: `The cap is the part that isn't a promise.`

**(b)** It is a technicality, for four measurable reasons. The badge is 20 to 22 px mono in a
760×64 plate (`assets/cards.html`), which is 6% of the 132 px verdict on the card next to it and
under 2% of frame height. It is identical and unchanging for 61.5 seconds, 53% of the runtime, so
the eye stops reading it long before it changes. The change is one word. And the frame that
carries the switch, shot 6, is the same console page, the same light background and the same
scroll position family as the two SYNTHETIC console shots before it, so the only thing that moves
on that frame is the plate. Meanwhile the sentence spoken on that frame is an aphorism about
promise-keeping that a judge cannot connect to a badge change they did not see, because the
previous sentence did not mention promises either. The palette inversion that actually reads as
"this is now real" happens at 1:10.0, when the frame goes from warm off-white to near-black for the
cards. The argument is being made eight and a half seconds away from where the eye will feel it.
No measured norm covers badge systems, so the placement rule is measured (research §5.2) and the
prominence judgement is mine.

**(c)** One change, and it is a swap of near-equal length. Replace beat 4's first sentence:

> Everything before this was generated. This is not.

**8 words, replacing 9.** Now the voice states the switch on the frame that carries it, the judge
hears the two-part structure the badges encode, and the near-black cards at 1:10 confirm what the
voice just said. Nothing else needs to move. If one more change is affordable, the optional second
is to give the two plates visibly different geometry, not just different colours, since both are
currently a dark rounded rectangle at the same coordinates.

**(d) MAJOR.**

---

### 7. The last 25 seconds end on a legal qualifier, and the video's best measured fact is framed as an absence

**(a)** Beat 5 in full: `What is not built, we do not show. No marketplace, no checkout. The artist
fee is out because we measured it: on a one-unit ticket a Token-2022 fee takes the whole ticket.
The model is unfitted, and labelled so. The interface is the company's design; the pricing layer is
ours. Thank you.`

And the shot it plays over, `CHOREOGRAPHY.md` shot 9: `1:28.0 → 1:44.0`, `the console's refusal
block held, or the [UNVALIDATED] badge held large. One of them, not both.`

**(b)** Six negatives in 52 words: "not built", "we do not show", "No marketplace", "no checkout",
"is out", "unfitted". Two things are wrong beyond the count.

First, the last clause before the thank-you is `The interface is the company's design; the pricing
layer is ours`, which is a prior-work compliance statement. Whatever its legal value, it is the
last impression, and it is a disclaimer. `rules-verified` §6 says this needs to be "a sentence in
the script"; it does not say it needs to be the final one.

Second, the Token-2022 sentence is the strongest Learning evidence in the entry, and it is
delivered inside a list of absence, introduced by "is out because". A judge scoring Learning
("did the team stretch themselves") is being handed a measured dead end, which is exactly what
that criterion rewards, and it is being handed it as a reason something is missing. `OPEN-
DECISIONS.md` V7 already identifies this sentence as worth keeping. The problem is not that it is
there, it is what surrounds it.

On volume: the only measured winner that disclosed an unfinished app spent two clauses at the end
of a 1:53 video after a full demo (§4.4), and MLH's own instruction is to "present what you have
done even if your hack is broken" (`rules-verified` §4, via the research). Present, not enumerate.
52 words and 25 seconds is 22% of the word budget on the criterion the entry is weakest on.

And the shot under it is the worst frame of the ten. Shot 9 is 16.0 seconds, which makes it the
second-longest shot in the cut, and unlike the 17.8-second opening it has no movement in it: one
panel, held, while the voice enumerates. It also lands directly after the video's peak, so the
sequence a judge experiences is two signature cards at 1:10 to 1:28, then 16 seconds of stillness,
then a 12.9-second card. That is 29 seconds of a 117-second video in which almost nothing on the
screen changes, and it starts at the moment attention is highest.

**(c)** Replace beat 5 with this, which keeps every disclosure, gives the fee finding its own
standing, and ends on the thing the judge just watched:

> No marketplace, no checkout. The model is unfitted, and labelled so. A Token-2022 fee takes a
> whole one-unit ticket, so no fee ships, and we measured that. The interface is the platform's;
> the pricing layer is ours. Two transactions on devnet: one lands, one is refused. That refusal
> is the feature. Thank you.

**53 words, +1** (measured, not estimated: 53 against the current 52). If one of the disclosures has
to go instead, cut `and we measured that` rather than the fee finding, and if the beat is still
long, move the prior-work clause to the end of beat 2 next to the fixture sentence, where it
belongs anyway: both are provenance statements about what is on screen, and beat 2 is where the
screen is first qualified. That move is net zero words and it takes the disclaimer out of the last
position entirely.

For shot 9, the fix is arithmetic, not taste. Beat 5 is 20.6 seconds of speech at 125 wpm, and the
choreography gives it one 16-second held panel followed by a 12.9-second card, which is 9.9 seconds
more screen time than the speech needs. Cut it to two shots of about 10 seconds each, the refusal
block then the `[UNVALIDATED]` badge large, and put the card up at 1:54.0. The choreography
currently forbids exactly that split (`One of them, not both`), and the ban is unnecessary: two
shots inside one beat cost nothing and remove the longest still frame in the cut.

**(d) MAJOR.**

---

### 8. The timing table's arithmetic is wrong by two seconds in the two rows that matter

**(a)** `| 125 wpm | 109.9 s | 1:56.9 | **inside** |`

**(b)** 229 words at 125 wpm is 109.9 s. Plus 2 s of holds plus 3 s of end card is 114.9 s, which
is **1:54.9**, not 1:56.9. The 130 wpm row has the same error: 105.7 + 5 = 1:50.7, printed as
1:52.7. The 110, 119 and 140 rows are correct, so this is a transcription slip in two cells, not a
method error. It matters because `CHOREOGRAPHY.md` opens with the number it produced: "Total
**1:56.9**, three seconds inside the 2:00 cap". The plan is in fact 5.1 seconds inside, which is
better and is also inside the measured 0 to 7 seconds-under band (§1.2, 1:58 / 2:00 / 1:53). The
error is conservative, so no record is at risk. It is still the number the whole plan is timed
against.

**(c)** Correct to 1:54.9 and 1:50.7, and re-derive the choreography's total from the corrected
figure once the card timing is settled (finding 9). A correct total for the plan as written is
**1:54.9**; for the plan with every finding applied, **1:58.3** (236 words, 113.3 s of speech,
which also stays inside the measured band).

**(d) MINOR.**

---

### 9. What is doing no work at 2:00

**(a)** Three sentences and one shot.

1. `What is not built, we do not show.` 10 words, 4.8 seconds. It is a slogan that announces the
   following four sentences, which are the list itself. The list demonstrates the claim; the claim
   adds nothing.
2. `The cap is the part that isn't a promise.` 9 words, 4.3 seconds. It contrasts the cap with a
   promise the video never mentioned, on the frame that needs to carry the badge switch (finding
   6). The switch is the better use of those 9 words and saves one.
3. `That record is the product.` 5 words, 2.4 seconds. Ambiguous in the worst way: a judge can hear
   "they sell data". Beat 1 will have said `SeatPass prices from that resale record` (finding 1),
   which makes this redundant.
4. `CHOREOGRAPHY.md` shot 10, `1:44.0 → 1:56.9`, `Hold 12.9 s`. A static three-line card for 12.9
   seconds is 11% of the video and it contradicts `SCRIPT.md` §4, which budgets the card at 3 s and
   puts it at 1:53.9. Two plans, 9.9 seconds apart, for the last shot. Also: 1280×800 is 16:10, so
   the "one window size" instruction cannot produce a 16:9 frame without bars or a crop, and the
   choreography forbids the crops that would remove the badge or the fixture strip.

**(b)** Two of the three sentences are load-bearing aphorisms that the rest of the script does not
support, and the third is redundant once finding 1 lands. The card timing is unresolved between two
documents, so nobody can record the last ten seconds without deciding which one is right.

**(c)** Cut all three: 24 words, 11.5 seconds. Resolve the card to `1:54.0 → 1:58.0`, which is 4
seconds, is enough for three lines, and replaces the 12.9-second hold in shot 10.

With those three gone and the replacements in findings 1, 2, 4, 5, 7 and 13 applied, the script
measures **236 words** (`wc -w`, run on the rebuilt beats rather than estimated). That is 113.3
seconds of speech at 125 wpm and a **1:58.3** file with two 1-second holds and a 3-second card,
which is inside the cap and 1.7 seconds inside the measured 0 to 7 seconds-under band. It also
raises the pace floor from 120 to **123 wpm**, and the measured median winner reads at 99, so that
is a real cost: if the timed read comes in under 123, drop finding 4's mechanism sentence and the
beat returns to 34 words and the file fits at 118 wpm.

**(d) MAJOR.**

---

### 10. The first claim the video makes is a disclaimer

**(a)** The badge copy on frame from 0:00, verbatim from `assets/cards.html`:
`Synthetic · generated fixture data — not real ticket prices`.

**(b)** At 0:00 the frame tells a judge the numbers are not real before the voice has said what the
product is. That is a 9-word sentence in a solid plate at the bottom left of the opening frame, and
it stays for 61.5 seconds. The placement is correct and measured: research §5.2's operative reading
is to label the data in the frame that shows it, never in a closing disclaimer. The wording is the
problem. Nine words of warning is the loudest caption in a video whose body type on the console is
15 px, so the honesty system is more legible than the evidence it qualifies. Its scope is also
loose: beat 2 says `These screens run on generated fixtures`, which points at the app, and then the
video shows a second product surface for 27 seconds whose figures are also generated and whose only
label is that plate.

**(c)** Shorten the plate to `SYNTHETIC FIXTURES` on every app and console shot, keep the full
sentence for the end card and the submission description. **No words of speech, 7 words removed
from the frame.** The label stays in every frame that carries a number, which is the measured
requirement; it stops competing with the product for the first second.

**(d) MAJOR.**

---

### 11. The two shots the argument depends on are in 12 to 15 px type

**(a)** Beat 3's own on-screen requirement: `the [EXACT] ceiling line, then the [UNVALIDATED]
recommendation, then What the engine refuses with not_identified legible`.

**(b)** The console is a small-type page: body 15 px, `.label-sentence` 15 px, `code` 13 px, `h2`
1.05 rem. Captured with a 1920 CSS px viewport, 15 px occupies 1.39% of frame height and 13 px
occupies 1.20%. At 1280 CSS px it is 1.5× larger, so the same page gives 2.08% and 1.81%. Downscaled
to a 720p player, the 13 px code becomes about 9 px. The custody trail that beat 2 asks the judge to
read (`each hop carrying its price`) is `text-xs`, 12 px, in the component. The rule the cut needs
is not "one window size"; it is a minimum apparent size for text that must be read. Nothing that
carries the argument should sit below 2% of frame height, and the `[EXACT]` line is a 30-word
sentence, so it is not going to be read at all at 1.2%.

**(c)** Record the console at a CSS viewport 1280 px wide with 2× device scale (device scale buys
sharpness, viewport width buys size), and crop shots 4 to 6 so the decision panel occupies the full
frame width. Do the same for the custody trail in shots 2 and 3. State the rule in
`CHOREOGRAPHY.md` §2 as a measurement to check on a captured frame, not as a window size.

**(d) MAJOR.**

---

### 12. Two product names on the same screen, and nothing relating them

**(a)** The console's own page title and `h1`, from its presentation code: `Ticketpath — organizer
pricing console`. The voice, beat 1: `this is SeatPass`.

**(b)** `OPEN-DECISIONS.md` V5 treats the name mismatch as a two-second problem on the end card. It
is bigger than that: the `h1` is 1.35 rem, among the largest type on the page, and it sits directly
under the banner that every console shot must keep in frame, so it is in frame for any shot not
scrolled past it. That is up to 27 seconds of a judge reading a different product name on the
surface that carries the strongest evidence. `CHOREOGRAPHY.md` §2 carefully keeps the app's header
out of frame and says nothing about the console's.

**(c)** Cheapest fix, no words: add the console `h1` to the choreography's list of things that must
not be in frame, and check it per shot. If it cannot be cropped out of shot 4, say the relationship
once instead: `SeatPass runs on the platform's console`. That is 7 words and it also serves
finding 2.

**(d) MINOR.**

---

### 13. The video never says the word Solana about its own work

**(a)** `This program is deployed on devnet: face one SOL, cap twenty five hundred basis points.`

**(b)** "Solana" occurs once in the script, inside the event's name. The partner page a Solana judge
is following says: `Confirm that the winning project actually uses Solana. Ask the team to identify
the integration in its README and show the relevant code, configuration, transaction, deployed
program, or other appropriate evidence during the demonstration` (`rules-verified` §5). The video
does the hard part of that instruction better than most entries and never says the word about its
own build. "devnet" implies Solana to an informed judge, so this is cheap insurance rather than a
hole.

**(c)** `This program is deployed on Solana devnet`. **+1 word.**

**(d) MINOR.**

---

### 14. The rehearsal target band permits an over-length video

**(a)** `REHEARSAL.md` §3 pass 2: `| 1:50 – 1:58 of speech | 116–125 wpm | **the target band** |`

**(b)** At the slow end of that band the plan fails. 1:58 of speech plus 2 s of holds plus 3 s of
card is 2:03, which is an ineligible entry, not a weak one (`rules-verified` §1, rule 1: "2 minute
or less"). `SCRIPT.md` §4 gets the floor right (120 wpm upward for 229 words) and the rehearsal
plan's band is 4 wpm looser at the bottom. This is exactly the class of error the plan says it
exists to prevent: a measurement that passes while the deliverable fails.

**(c)** Set the band to **1:50 to 1:55 of speech**, which is 120 to 125 wpm at 229 words and
123 to 129 wpm at the 236 words the other findings produce, and add the reason: two seconds of
holds and three seconds of card come on top and the file is what gets measured. `REHEARSAL.md` §3
pass 5 already knows this; pass 2 does not.

**(d) MINOR.**

---

### 15. The argument dies on mute, and there is no caption plan

**(a)** Nothing in either document mentions captions. `REHEARSAL.md` §4 offers "captions only" as a
disaster fallback, not as a design choice.

**(b)** Every takeaway a judge must have is spoken, and the on-screen carriers are 12 to 22 px
labels (finding 11) and bracket tags the voice never names. Measured: 10 of 11 winners speak from
t=0 and one silent 3:52 video won anyway (§6), so voice is the norm and silence is survivable.
Whether winners burn captions is Unverified. What is not measured and not knowable from here is
whether this judge watches muted. A muted judge currently gets a scrolling ticket app and no
argument at all.

**(c)** Burn the four load-bearing sentences as lower thirds, cued to the beat they belong to:
finding 1's function clause, finding 4's data sentence, finding 6's switch sentence, and finding
7's close. Four lines is about 40 words of on-screen text across 2:00, which is legible without
becoming a slide deck. **TASTE, and cheap to reverse.**

**(d) MINOR.**

---

## 4. WHAT IS WORKING

These are not consolation. Several are the best decisions in the package and should survive every
revision above.

1. **The runtime decision is correct and measured.** 229 words for a 2:00 cap is derived from a
   median measured pace of 99 wpm across twelve named winners, and the script states the derivation
   and the pace floor it needs. Refusing the 280-word brief on evidence is the single most
   professional thing in these files.

2. **The opening line matches the rule's own example.** `I'm NAME, and this is SeatPass, my demo for
   the MLH Solana Hackathon` is the form `rules-verified` §1 rule 3 gives, and it is what 4 of 5
   MLH winners actually did (§2.1). No invention, no cleverness, no risk.

3. **`nothing recorded what a ticket was listed at` is the best sentence in the script.** It teaches
   a judge something true and non-obvious about ticket markets in 9 words, it explains a refusal
   without excusing it, and it is the kind of sentence that makes a judge believe the team
   understands the data. It should be louder than it is (finding 4), never cut.

4. **`The chain refuses it, not the app.`** The strongest structural idea in the video: it converts
   a boundary test of the team's own code into a claim about the system. It lands exactly when the
   two cards are on screen. This is the line a judge repeats to themselves.

5. **The devnet pair is the right climax and it is placed in the right quarter.** Two transactions,
   one landing and one refused, each with a signature in frame, is precisely the evidence the
   Solana partner page tells a judge to ask for (`rules-verified` §5), and `build-state-matrix.md`
   §4 ranks it as the strongest thing in the whole project because a stranger needs zero trust to
   check it. Spending 26.5 seconds there is correct.

6. **Labelling absence is the right instinct and it is measured.** A winner closed by saying its app
   was not running (§4.4), and MLH's own words invite it. The instinct is right; findings 7 and 10
   are about volume and position, not about the policy.

7. **The cards are properly built.** 132 px verdict, 92 px amount, 26 px signature rows, the
   program's own log line quoted, and a full base58 signature that fits on one line. The hierarchy
   is right and the overflow check is a measurement, not a hope.

8. **The choreography's negative space rules are unusually good.** Keeping the app's header out of
   frame, keeping `tx` chips at the frame edge, not pressing the refusal button that would show `0
   arms shown`, never describing a dashed cap rule that is not drawn. Those are the decisions
   someone makes only after looking at the actual build.

---

## 5. If only three changes happen

1. **Finding 1.** The function sentence in beat 1, +2 words. Without it the judge's one-sentence
   summary is wrong and every other improvement is decoration.
2. **Finding 6.** The 9-word swap for 8 at 1:01.5. The badge system is the video's honesty argument
   and it is currently invisible; this makes it audible and saves a word.
3. **Finding 9 and 7 together.** Cut the three aphorisms (24 words) and rebuild the close around
   what was built (+1 word, ending on `That refusal is the feature`). This removes the static 16
   seconds at 1:28, retires the legal qualifier from the last position, and still discloses
   everything the record requires.

Applied alone, those three give **226 words, 108.5 s of speech, and a 1:53.5 file** with two
1-second holds and a 3-second card, which still fits at 118 wpm. Applied with findings 2, 4, 5 and
13 as well, it is 236 words and **1:58.3**, inside the cap and inside the measured 0 to 7
seconds-under band, at a pace floor of 123 wpm.

---

## 6. Verdict

The bones are right and the problems are in the copy, the framing and three timings, which is the
good case: none of the findings below requires a re-shoot or a different surface. The order is
correct and measured (product and event named inside ten seconds, no market statistic, demo signal
at 0.0 against a norm of 3.9 s). The climax is correct and measured (a real admitted transfer and a
real refused one, each with a signature, which is the exact evidence the partner page tells a judge
to ask for). The honesty system is the most defensible thing in the package and it is under-served
by a badge nobody will notice. The runtime is inside the cap at any pace above 120 wpm and the word
count is exactly what the script says it is.

Against that: the video never says what its product does until 0:43, and never says who decides
anything with it, so a judge's one-sentence summary will describe a resale valuation tool rather
than a primary-pricing engine. Its middle beat refuses three things and shows no mechanism, which
reads as an excuse under the one criterion it was aimed at and earns nothing under the criterion
that excludes pitch quality. Its last 25 seconds list six absences, end on a prior-work clause, sit
on a frozen 16-second frame, and are followed by an end card that two documents disagree about by
9.9 seconds. And its closing argument for the honesty of its own evidence, which is the badge
switch at 1:01.5, is a 20 px plate changing one word while the voice says something unrelated.

The video as specified would score. The video with finding 1, finding 6 and a rebuilt close would be
remembered, and the difference is 226 words against 229, so it costs nothing but the decision.
