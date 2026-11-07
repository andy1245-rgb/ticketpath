# Phase 2 — The rubric, what scored at the last MLH blockchain event, and the on-chain artefact this machine can actually produce

**Status:** complete for Phase 2 purposes. **Written:** 2026-11-07T11:01Z. **Agent:** `p2-rubric`.
**Scope:** what actually scores at the MLH Solana Hackathon (2026-11-06 → 11-08, online); what the
published judging criteria are, verbatim, and what they exclude; what the closest available winner
record says about why projects won; what "not a chain bolted onto a web2 app" requires operationally;
what a two-minute video has to contain; and the minimum on-chain artefact that can be produced given
that this build machine has no `solana`, `anchor`, `cargo` or `rustc`.
**Authority:** the event's own pages, MLH's published rules and organizer guides, and primary winner
records. Nothing here is inferred from a blog post about a source.

**Evidence labels.** The brief for this file asks for MEASURED / ASSERTED, and that is what is used:
**MEASURED** = a source states it, and the URL is in the entry; **ASSERTED** = my reasoning, not a
claim about what anyone said. Two sub-labels are used where the distinction matters:
**MEASURED-ABSENT** = I read the named page in full on 2026-11-07 and the claim is not on it (absence
is a measurement, not an inference); **MEASURED (translated)** = the source is not in English and the
quotation is my translation, with the original linked.
The programme's A–E classes (`records/README.md`) describe evidence about ticket markets. They do not
apply to a document about a hackathon's rules, and forcing them on would be false precision. Where a
claim here would need a market-evidence class, it is marked ASSERTED instead.

---

## What I concluded

The rubric is **not** four equal quarters of a startup pitch, and the biggest strategic fact of the
weekend is not the rubric at all: **the field is seven submissions with the submission window still
open.** Three of seven place. That converts the problem from "differentiate against a crowd" into "be
complete enough that a tired judge can see it work", which is a very different build.

Ranked by expected value, given 26 hours of build time left:

1. **The only written criterion for the top prize is one sentence, and it is a materials test.**
   Verbatim from the event page: *"We're looking for a working product that uses Solana for something
   it's good at (speed, low fees, composability, on-chain ownership), not a chain bolted onto a web2
   app."* A judge applies it by looking for four things: an account that belongs to the project, a
   transaction signature, a program that is not the team's own code doing the work, and the app reading
   that state back. Today the repo has none of the four. That is the whole gap.
2. **MLH's published rubric is four equally weighted criteria — Technology, Design, Completion,
   Learning — and it explicitly excludes idea quality, pitch quality, code quality and problem fit.**
   So a pricing engine does not score for being a good pricing engine. It scores for visibly working,
   looking designed, and demonstrating that the team learned something. Design is 25%, it is the
   cheapest quarter to win, and the current build has no interface at all.
3. **The weighting quoted in the brief (25/25/25/25 originality / technical complexity / theme
   adherence / practical implementation) is not published anywhere I could reach.** MEASURED-ABSENT on
   the event page, the canonical mlh.com event page, the five challenge-category pages, the standard
   hackathon rules, the judging plan and the organizer rule page. What is published is item 2 plus the
   per-track one-liners. Do not build against originality: MLH's own rules say *"How good the idea is.
   Again, hackathons aren't about coming up with innovative ideas"* is **not** judged.
4. **There are no past MLH Solana Hackathon winners to study, because this is the first one.** The
   Partnered Hackathon series lists exactly two events, this one and Midnight on 13–15 November, both
   upcoming; the 2027 season payload lists one Solana event. The usable winner record is the adjacent
   one: MLH "Best Use of Solana" prizes at member events (verified spot-checks below) and the MLH x
   Midnight July partnered hackathon's seven winners, where the sponsor published what they had in
   common.
5. **What the closest winner record says, in order: deployed, complete, driven by the sponsor
   primitive, explainable in one sentence.** Midnight's write-up puts deployment first as the
   differentiator ("two teams reached Preprod; everything else stayed on a local node"), then "a
   completed layer: contract, tests and interface", then "primitives used because the design required
   them", then "a use case someone else can explain in one sentence". That ordering is the build order.
6. **The video is the artefact that gets watched, and it must be a demo recording, not a pitch.** MLH
   requires ≤2 minutes, recorded that weekend, with the hackathon's name spoken at the start, public
   forever; MLH's judging plan says the video *"should be a demo of their hack, not a presentation"* and
   the rules say pitches are discouraged and pitch quality is not judged. Forty seconds of the working
   thing with one uncut on-chain confirmation beats any narrative.
7. **A judge's first click is the video, second is the demo URL, third is the repo.** The submission form
   collects project link, name, description, technologies used, demo URL, and which challenges (B9). The
   event's own schedule leaves one hour between the final submission and the closing ceremony with no
   judging session (A2), and no submissions gallery is published yet (measured:
   `/events/solana-hackathon/submissions` returns "Page Not Found"). ASSERTED from those three: during
   judging a judge sees only the submitted fields and MLH's internal view, so nothing you did not submit
   lends context.
8. **The on-chain artefact this machine can produce is a read, not a write.** No `solana`, `anchor`,
   `cargo` or `rustc` here; `node` v24.22.2 is here and devnet is reachable from here. The write has to
   happen on the operator's laptop (Agave + spl-token) or be produced from node with `@solana/web3.js` +
   `@solana/spl-token`, then read back here over JSON-RPC. Anything else is a plan that cannot run.

### The Sunday build must contain, by 10:00 ET

1. **A public repo, first commit inside the weekend window, with a LICENSE and a README that has an
   integration section.** Rule 12 and 13 make this a prize condition, and MLH's own winner-selection
   guidance for challenge prizes names a public repo. Today this repo's remote is
   `git@github.com:andy1245-rgb/ticketpath.git` and there is no `LICENSE` file.
2. **One page a judge can open without a login that shows the product, not the API.** The current build
   is a Python HTTP service (`ticketpath/`, 2,109 lines) with no frontend. Rendering JSON to a judge
   scores zero on Design (25%) and reads as "no product" on Completion.
3. **A devnet account that belongs to this project, named in the README and shown in the UI.** Minimum:
   a Token-2022 mint for the event or the ticket, address and cluster in the README, the address
   rendered in the page.
4. **One confirmed devnet transaction signature, linked to Explorer, with its block time visible on
   screen.** This is one of the four artefacts the sponsor's published evidence check names.
5. **One transaction the chain refused or an edge case the code rejects, shown as a real signature or a
   real error code.** Every verified winner below that scored on technology did this: an error code, a
   refusal, a verify button. It is the cheapest visible proof that logic exists off the happy path.
6. **The app reading the chain back, not printing a constant.** The repo already has a read-only RPC
   adapter that honestly answers "no program deployed"; wire it to the real address so the number on
   screen comes from a call a judge could repeat.
7. **Every number on screen labelled with its source and whether it is synthetic.** solGPU, a verified
   MLH Solana prize winner, won with "every number names its source and its capture time" and a receipt
   the judge could re-verify. The repo's resale/markup numbers come from `fixtures/synthetic_store.json`
   and must say so.
8. **A 1:50 video: product in frame 1, hackathon name in the first sentence, one uncut on-chain
   confirmation, one sentence of Learning, an end card that is readable when paused.**
9. **README sections: what Solana is doing here, mint/program id, cluster, a signature link, stack, AI
   tool disclosure, team, run instructions.** The AI disclosure is not optional; the stated penalty is
   disqualification and a report to `cheating@mlh.io`.
10. **A submission on the mlh.com Challenges page with every eligible category selected, done before
    10:00 ET, not 11:45.** "One submission can enter every category it qualifies for."

### Do not waste time on

- **A custom Anchor program.** `p1a-prior-winners.md` classifies 8 of its 38 sampled Solana-prize
  winners as having deployed one (21%); a memo or a token configuration won as often, and the three I
  re-read by hand split two programs to one memo (D2, D3, D4). There is no Rust toolchain here (E1) and
  the deploy gate would eat the weekend.
- **Originality, market sizing, or a business narrative.** MLH's rules exclude idea quality and problem
  fit from the rubric; the pitch quality exclusion is explicit.
- **A second video.** The Colosseum pitch-video/technical-video split does not exist here; the cap is
  one 2-minute file.
- **Code quality, refactors, coverage.** *"If your code isn't production ready, we're not going to mark
  you down."*
- **A second event.** Digital rule 5 forbids submitting the same project to another hackathon; the
  Solana Foundation's December event is therefore out of bounds for this repo.
- **An "AI agent" wrapper.** It is item 1 and 2 of the organizer's own AI idea list, so it is the most
  crowded shape of the weekend, and the AI track pays $100 per member against Top 3's $1,000 per team.

---

## Evidence

### A. The event itself

**A1. MEASURED.** Event: "Solana Hackathon", type "Partnered Hackathon", hosted online, "Friday
November 6, 2026 12:00PM to Nov 8, 1:00PM EST". The canonical page carries a live submission counter
reading **7 Submissions** at 2026-11-07T10:59Z, and a deadline field reading "Submissions close Nov 8,
1:00 PM EST". https://www.mlh.com/events/solana-hackathon (and the events.mlh.com twin,
https://events.mlh.com/events/15200-solana-hackathon).

**A2. MEASURED.** The event page's schedule, verbatim times: Sunday 7:00 AM PT / **10:00 AM ET**
"Initial Submission due on MLH Challenges"; Sunday 8:45 AM PT / **11:45 AM ET** "Hacking Ends / Final
Submission due on MLH Challenges"; Sunday 9:00 AM PT / 12:00 PM ET "Closing Ceremony". There is no
judging block anywhere in the schedule. Same URLs as A1.

**A3. MEASURED.** Prize tracks, five, verbatim: "Top 3 Overall — $1,000 USD microgrant for your team to
continue building"; "AI Track — Each winning team member will receive a $100 digital gift card"; same
wording for DeFi, Gaming and Best Beginner. The Top 3 criterion, verbatim: *"We're looking for a
working product that uses Solana for something it's good at (speed, low fees, composability, on-chain
ownership), not a chain bolted onto a web2 app."* Best Beginner eligibility, verbatim: *"Teams made up
of >50% first-time hackers are eligible for this prize track."* Same URLs as A1.

**A4. MEASURED.** The five prize categories also exist as separate pages, each with a one-line
description and no judging criteria beyond it, and each carrying the line: **"One submission can enter
every category it qualifies for."** E.g. https://www.mlh.com/events/solana-hackathon/challenges/01a1a6ef-1328-c2f4-f126-f0506a239a09
(Top 3 Overall) and
https://www.mlh.com/events/solana-hackathon/challenges/01a1a6f0-dde1-f6fe-c748-37c36c7d45e6 (Best
Beginner Hack).

**A5. MEASURED-ABSENT.** The numeric weighting in the brief — "25/25/25/25 — originality, technical
complexity, theme adherence, practical implementation" — does not appear on: the events.mlh.com event
page; the mlh.com canonical event page; any of the five challenge-category pages; the standard
hackathon rules; the judging plan; the organizer rule page. A keyless web search for the phrase set
returned no MLH source (search conditions in §G). What the event page publishes is A3; what MLH
publishes for criteria is B1.

**A6. MEASURED.** This is the first MLH Solana Hackathon. The Partnered Hackathon series page lists
exactly two events, both upcoming: "Solana Hackathon, November 6th–8th, 2026" and "Midnight Hackathon,
November 13th–15th, 2026". The 2027 season payload
(https://www.mlh.com/seasons/2027/events) contains one Solana event, this one.
https://events.mlh.com/series/partnered-hackathon

**A7. MEASURED.** There is no public submissions gallery for this event: `/events/solana-hackathon/submissions`
returns "Page Not Found". A judge therefore cannot browse other entries, and nothing outside your
submitted fields and your video carries context.

**A8. MEASURED.** The event page's "Contest Terms and Conditions" link (`https://hackp.ac/ContestTerms`
→ `https://mlh.link/ContestTerms`) resolves to `https://mlh.com/` — a meta-refresh to the homepage, not
a terms document. So the terms of this specific event are not reachable from its own registration form.

### B. MLH's published criteria, verbatim

**B1. MEASURED.** *"Teams will be judged on these four criteria for MLH digital events or MLH categories
at an in person event. Judges will weigh the criteria equally."* — **Technology** ("How technically
impressive was the hack? … Did the technology involved make you go 'Wow'?"), **Design** ("Did the team
put thought into the user experience? … for a website, this might be about how beautiful the CSS or
graphics are"), **Completion** ("Does the hack work? Did the team achieve everything they wanted?"),
**Learning** ("Did the team stretch themselves? Did they try to learn something new?"). And: *"These
criteria will guide judges but ultimately judges are free to make decisions based on their gut feeling
of which projects are the most impressive and most deserving."*
https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md

**B2. MEASURED.** The same page's explicit exclusions, verbatim: *"How good your code is … If your code
isn't production ready, we're not going to mark you down."* · *"How well you pitch. Hacking is about
building and learning, not about selling."* · *"How good the idea is. Again, hackathons aren't about
coming up with innovative ideas."* · *"How well the project solves a problem."* Same URL as B1.

**B3. MEASURED.** Demos section, verbatim: *"You are strongly encouraged to present a demo of what you
have built. Pitches and presentations are discouraged. You are not judged on the quality of your pitch
or the quality of your idea. As you are judged on what you built, you'll only hurt yourself by not
showing a demo."* Same URL as B1.

**B4. MEASURED.** Digital submission rules, verbatim: 1. *"We require all teams to submit a 2 minute or
less demo video. Your video must be created the weekend of the hackathon."* 2. *"Your video must remain
public post event to be eligible for prizes. If your video is not public, new winners may be selected."*
3. *"Your demo video must state the name of the hackathon at the beginning of the video. Ex. 'Hey I'm
Sam and this is my demo for CorgiHacks.'"* 4. registration steps. 5. *"You are not allowed to submit
your project to other hackathons."* 6. *"You can not submit a project that includes prior work."* Same
URL as B1.

**B5. MEASURED.** Rules 6, 9, 10, 12, 13 of the standard rules: all work done during the hackathon; an
idea may predate the event but *"as long as they do not re-use code or other project materials"*;
*"Working on a project before the event and open-sourcing it for the sole purpose of using the code
during the event is against the spirit of the rules and is not allowed"*; code must be public; *"Your
code must remain public post event to be eligible for prizes. If your repo and video are not public, new
winners may be selected."* Same URL as B1.

**B6. MEASURED.** AI rules, verbatim: *"Teams may use AI to assist them while coding …"* and *"Teams
should be honest and transparent about the AI code tools they used. This includes listing them in their
project submissions and answering questions when talking to organizers, judges, and other hackers."*
Same URL as B1. The organizer-side copy is harsher and is quoted in the organizer guide: *"You may use
LLM/ChatGPT/AI, but must state how you did so … Your project should not be a reskin of an existing AI
tool… If you do not credit your AI usage, you will be disqualified and reported to cheating@mlh.io"*
https://guide.mlh.com/general-information/judging-and-submissions/rules-for-your-hackathon.md

**B7. MEASURED.** How judging is actually run and scored: *"They only have 3 minutes per team"*; the
time budget is *"4 mins per project. 2 minutes for presentation + demo, 1 minute for questions from
judges and score compilations, and 1 minute for judge travel"*; *"The goal is to have each project seen
at least 3 times"*; scoring is stack ranking — *"Ask each judge to view their projects and report back
their top 3 best/favorite projects"*, 3/2/1 points, because *"Some judges are super nice, and might give
higher scores overall than a stricter judge"*; small categories *"can instead have 1-2 subject matter
experts who are familiar with the category view just those projects and pick the winner that best fits
the category"*; and *"Do a cheating check on all winners before you announce."* One more line matters
for a product-shaped entry: *"Focus on learning over profit … rarely do those people win hackathons
because they spent their time creating a product rather than awesome technology."*
https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md

**B8. MEASURED.** MLH's own published shortlist of what to look for when picking a challenge winner, and
the only MLH page I found that names originality: *"Look for projects that: Meet the challenge
requirements · Work well enough to demonstrate · Use the relevant technology as an important part of the
project · Show originality, learning, or thoughtful technical work · Explain clearly what the team built
and how it works."* Note the order: demonstrability second, originality fourth, and originality is
offered as an alternative to learning or technical work, not a category of its own.
https://hacktoberfest-handbook.mlh.com/project-submissions-and-judging-for-hacktoberfest-hack-day

**B9. MEASURED.** The submission fields, from the same page: *"Enter the project link, project name,
description, and technologies used. Add a demo URL if the team has one. Under Which challenge(s) are
you submitting to?, select every Hacktoberfest, partner, and local challenge the project is eligible to
enter."* And: *"The same project can appear once for every challenge it selected."* Same URL as B8.

### C. The Solana evidence standard

**C1. MEASURED.** The sponsor's published evidence requirement, verbatim: *"Judging Evidence — Confirm
that the winning project actually uses Solana. Ask the team to identify the integration in its README
and show the relevant code, configuration, transaction, deployed program, or other appropriate evidence
during the demonstration."* Page marked "Last reviewed: August 2026", written for Hack Days rather than
this partnered event. https://hackdays-guide.mlh.com/partner-programs/solana

**C2. MEASURED.** The same page's statement of what Solana wants built, verbatim: *"Create an
interactive application that uses onchain state, ownership, or transactions"*; *"Build a community,
gaming, creator, payments, or finance experience powered by Solana"*; *"Connect a web or mobile
application to Solana as a fast, efficient backend"*; *"Use Solana to power something people will want
to try"*. Same URL as C1. Note that "a chain bolted onto a web2 app" is contradicted by the sponsor's
own fourth option, which is precisely web2-plus-Solana-as-backend. The two documents are in tension;
the stricter one is the event page and the stricter one is the one a judge for this event will read.

**C3. MEASURED.** The Solana partner challenge has since moved from generic to protocol-specific. The
current Hacktoberfest module is "Best Use of the Solana Agent Registry", judged by: *"Confirm that the
winning project uses the Solana Agent Registry as an important part of the experience. Ask the team to
show the relevant code and the registration, reputation, feedback, validation, or other onchain
interaction during its demonstration. The project must be published in a public GitHub repository with
an open-source license."* (Last updated 2 months before 2026-11-07.)
https://hacktoberfest-handbook.mlh.com/hack-days-partner-modules/partner-challenge-solana

### D. The closest winner record, verified rather than carried

**D1. MEASURED (translated).** The MLH x Midnight partnered hackathon, 17–19 July 2026, "84 teams", seven
winners across two tracks. The sponsor's write-up states what the winners had in common, in this order:
the sponsor primitive was used because the design required it (commitments, nullifiers, Merkle
membership — and *eight* of the evaluated entries used no private data at all); **a completed layer**
(contract, tests and interface, with half-finished frontends common in the field); **deployment** (two
teams reached the public testnet, "everything else stayed on a local node"); and **a use case someone
else can explain in one sentence**. It calls Moonray *"the most complete product in this field: working
contracts, real tests, a finished interface, and a playable Preprod deployment"*, and ProveNow *"a great
example of a project with a clearly defined problem, completed end to end"*. It also says plainly that
testing on a local node *"is entirely normal and expected in a 48-hour weekend hackathon"* — which is the
sentence that keeps a devnet-only artefact honest rather than apologetic.
https://note.com/midnight_jpn/n/nbc5d338ae2be (publisher's Japanese translation of
https://midnight.network/blog/celebrating-seven-winners-from-mlh-x-midnight-july-hack, dated 2026-08-20;
the English page is behind a Vercel checkpoint from this host).

**D2. MEASURED.** Weenie Beanie, `MLH Prize: Best Use of Solana` at SwampHacks XII: *"two custom Solana
programs written in Rust and Anchor 1.2.1 … .reputation mints the Token-2022 NonTransferable Soulbound
credential"*, escrowed on devnet with a Java client. This is the exact primitive `p5-build-spec.md`
proposes, already carrying an MLH Solana prize. https://devpost.com/software/weenie-beanie

**D3. MEASURED.** solGPU, `[MLH] Best Use of Solana` at Knight Hacks IX, from the team's own write-up:
*"no token, no transfer and no custom program, which kept the trust story for our users"*, with a
"Verify receipt" button that *"re-checks five things against the chain"*, and *"Every number names its
source and its capture time."* Its own "what's next" says *"update our Solana integration to include
actual transactions."* A memo-only submission took the prize eleven days before this event.
https://devpost.com/software/solgpu

**D4. MEASURED.** LOKA Pay, `[MLH] Best Use of Solana` at Hacklanta 26: an Anchor program, a
`SerialUsed` error 6011 refusal reproduced on demand, four public devnet signatures, and a
judge-facing *"seven-stop judge guide"* at a public URL. Its write-up also states the AI-disclosure line
(*"we used AI coding assistants while building"*) and the sentence that should govern every claim in
our own submission: *"if someone can't check a claim without logging in, it doesn't count."*
https://devpost.com/software/loka-pay

**D5. MEASURED.** Devpost's video guidance, which is the platform MLH's own guide points at: *"it's
often one of the first things that judges, voters, and those checking out your software will review"*;
*"explain what your app does … in the first few seconds of your video … treat the opening seconds of
your video as you would a movie trailer or TV ad"*; use *"a screencast (a video screen capture with audio
narration)"* rather than a marketing video; and *"uploading your video could take anywhere from a few
minutes to several hours or more."* https://help.devpost.com/article/84-video-making-best-practices

### E. This machine, measured

**E1. MEASURED.** At 2026-11-07T10:48Z on the build host: `solana` NOT INSTALLED, `anchor` NOT
INSTALLED, `cargo` NOT INSTALLED, `rustc` NOT INSTALLED, `node` v24.22.2, `npm` 11.19.1. No
`~/.local/share/solana`, no `~/.cargo`. (`p2a-verified-spike.md` says its commands were "executed and
verified on this machine"; whatever machine that was, it is not the one I am on, and the outputs cannot
be reproduced from here.)

**E2. MEASURED.** Devnet is reachable from this host: `getHealth` → `{"result":"ok"}`; `getVersion` →
`{"solana-core":"4.4.0","feature-set":2681577653}`; `getEpochInfo` → slot 519,636,501, epoch 1202.
The Token-2022 program account `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` exists and is executable
on devnet. `https://api.devnet.solana.com`, JSON-RPC, queried directly.

**E3. MEASURED.** Rent-exempt minimums on devnet, measured rather than quoted: 82 bytes = 1,066,800
lamports (0.001067 SOL); 165 bytes = 1,488,440; 300 bytes = 2,174,240; 561 bytes = 3,500,120; 700 bytes
= 4,206,240. So a mint account with extensions costs a few thousandths of a devnet SOL, not a balance.

**E4. MEASURED.** The devnet faucet states: *"Maximum of 2 requests every 8 hours"*, and offers a GitHub
sign-in to *"unlock a higher airdrop limit"*. It also states, verbatim: *"I am an AI Agent — AI agents
should not use this faucet. Use one of these programmatic methods to obtain devnet SOL instead"*, listing
`solana airdrop 2 <WALLET> --url devnet`, a proof-of-work faucet, and a local validator.
https://faucet.solana.com/ Because of that line, the airdrop is the operator's action, not mine.

**E5. MEASURED.** A node-only mint path exists and needs no Rust: `@solana/spl-token` 0.4.15 is the
current npm release and its published type surface contains
`createInitializeNonTransferableMintInstruction(mint, programId)` and
`createInitializePermanentDelegateInstruction(mint, delegate, programId)`, plus metadata-pointer and
token-metadata modules, and getters `getNonTransferable(mint)` / `getPermanentDelegate(mint)`.
`@solana/web3.js`'s current tag is 3.2.0 and 1.99.x is published alongside it.
https://unpkg.com/@solana/spl-token@0.4.14/lib/types/instructions/initializeNonTransferableMint.d.ts ·
https://registry.npmjs.org/@solana/spl-token/latest · https://registry.npmjs.org/@solana/web3.js
Read from the published package over HTTP; nothing was installed.

**E6. MEASURED.** The repo today: remote `git@github.com:andy1245-rgb/ticketpath.git`, branch `main`,
two commits, no `LICENSE`, and the code is a Python 3 stdlib HTTP service (`ticketpath/`, 2,109 lines,
routes over `/api/...`, tests, synthetic fixtures) with no frontend. `ticketpath/adapters/rpc_adapter.py`
returns `no_program_deployed` by design and is off unless `TICKETPATH_RPC_ENABLED=1`.

### F. What "not a chain bolted onto a web2 app" means operationally

**F1. ASSERTED.** The sentence names a materials test, not a depth test. It does not ask for much chain
work; it asks that the chain work be load-bearing. A judge with sixty seconds applies it by looking for
four things, in this order: (a) an address that belongs to this project; (b) a transaction signature
with a block time; (c) a program in that transaction that the team did not write, doing something the
product depends on; (d) the product reading that state back rather than echoing a constant. Where any one
of the four is missing, the sentence fails regardless of how good the pricing model is.

**F2. ASSERTED.** Corollary, and the uncomfortable one: a pricing engine is, by construction, a web2 app
unless the price or the ticket lives on the chain. The version of this product that fails is "a
regression on scraped resale data with a Solana logo". The version that passes is "the quote the
organizer charges is written to devnet before the sale opens, so it cannot be re-cut afterwards, and the
ticket is an owned on-chain object whose supply is public" — because then the chain is doing the thing
the product claims (commitment and ownership), not decorating it. This also happens to be one of the
organizer's own published AI-track ideas, *"Verifiable AI: on-chain records of model outputs, datasets or
provenance"* (A3's page), which is the cheapest honest way to make a model's output the on-chain object.

**F3. ASSERTED.** For this event the *stated* bar is stricter than the observed awarding behaviour at
member events, where memo-only and even read-only entries took Solana prizes (D3, and `p1a-prior-winners.md`
§4's classification). At a partnered event, with MLH staff and the sponsor in the loop, assume the stated
bar is enforced. Build to the sentence, not to the lowest precedent.

### G. Search conditions, stated

No Brave credentials on this host (`web-search --check` reports keyless providers only, and every
`free-search` call logged "brave … Missing credentials"). All discovery was keyless: one flat pile per
query over DuckDuckGo-Lite / MWMBL and friends, plus direct fetches of the pages cited. Quoted
multi-term boolean queries return zero results on these engines, so the absence finding in A5 is
"no source surfaced for the phrase set across three query formulations", not an exhaustive web crawl. It
is supported much more strongly by the page-by-page reads listed in A5, which are exhaustive for MLH's
own documentation of this event.

---

## What this overturns from the pre-existing documents

Each line names the document, the claim, and what replaces it.

1. **`p1a`'s premise and the brief's request for "MLH Solana hackathon past winners" — overturned.**
   This is the first MLH Solana Hackathon (A6). There are no winners of this event to study. The
   substitute record is MLH x Midnight's partnered-event winners (D1) and the 38 member-event "Best Use
   of Solana" winners in `p1a`, three of which I re-read and confirm exactly (D2, D3, D4).
2. **The 25/25/25/25 rubric in the brief — overturned as unsourced.** Not on any MLH or event page I
   could reach (A5). The published criteria are B1's four equally weighted lines plus A3's one-sentence
   prize criteria. The consequence is not cosmetic: building for "originality" spends hours on a criterion
   MLH explicitly excludes (B2), while "Design" at 25% is unbuilt in this repo.
3. **`03-what-wins-solana.md` §4.5's "ignore the tracks, aim Top 3" (`R10`) — partially overturned.**
   The prize asymmetry is real and verified (A3), but the strategic fact is now the field size: 7
   submissions with the window open (A1). Top 3 of 7 is not a long shot to be rationed; it is the default
   outcome if the thing is complete. The recommendation survives; its reason changes from "tracks are
   worthless" to "there is no crowd to differentiate against, so completeness dominates differentiation".
   And entering tracks is free — "One submission can enter every category it qualifies for" (A4) — so the
   only reason to skip one is honesty, not scarcity (`p3-decision.md` §4 stands on that ground).
4. **`04-mlh-judging-playbook.md` §1.6's resolution of the pitch contradiction — confirmed, with one
   sharpening.** MLH really does say pitches are discouraged and pitch quality is not judged (B3), and the
   judging plan really does say the video *"should be a demo of their hack, not a presentation"* (B7). The
   sharpening: at this event the video is not a pitch at all, so `03`'s Colosseum pitch structure (founder
   market fit, traction, market size) is not merely unnecessary, it is counter-productive — B2 excludes the
   content it would carry.
5. **`p1d-video-judging.md` §4.1's field-size estimate — corrected.** It estimated "~100 projects" from
   MLH's "1 project per 4 checked-in hackers". The measured counter is 7 with the window open (A1). Treat
   any pre-event field estimate as superseded by the counter, and re-read it before the video script is
   locked.
6. **`p1d` §1.2's "treat this as 100% asynchronous video review" — confirmed and strengthened.** No
   judging block in the schedule (A2) and no public gallery (A7). A judge's entire exposure is your
   fields plus your video.
7. **`p5-build-spec.md` §0's "every command and error string here was executed and verified on this
   machine" — corrected for this machine.** No Solana toolchain is present on the build host now (E1).
   The `p2a` outputs may well be real, but they cannot be reproduced here, so any plan that assumes
   `spl-token` or `solana-test-validator` is available has to be re-pointed at the operator's laptop.
8. **`03` §4.5's description of the standing MLH Solana prize — updated.** "Best Use of Solana" across
   member events is still the pattern (D2–D4), but the sponsor's current Hacktoberfest challenge is
   protocol-specific — "Best Use of the Solana Agent Registry" — and its winner criterion explicitly
   requires a public repo with an open-source licence (C3). A licence file is now a checkable
   requirement somewhere in this sponsor family, and this repo has none (E6).
9. **`p1a` §4's "composition wins by a wide margin; a memo is the most common mechanism" — confirmed by
   spot-check, not overturned.** Three of three re-read exactly as recorded (D2 uses two Anchor programs
   plus a Token-2022 NonTransferable; D3 is a memo and says so; D4 is an Anchor program with a reproduced
   error code). The classification stands; it is now sampled rather than taken whole.
10. **`p1a` §6's "the stated bar is stricter than observed awarding behaviour" — confirmed, and it now
    has a second data point.** The sponsor's own two pages disagree with each other: C2 invites
    "Solana as a fast, efficient backend" while A3 forbids "a chain bolted onto a web2 app" (C2). Name
    the tension if a judge raises it; do not resolve it by choosing the lenient reading.

---

## Does a judge clicking a pricing tool see a working thing on Solana?

**No. Not today.** Measured: there is no mint, no program, no signature, no frontend, and the only RPC
code in the repo answers `no_program_deployed` by design (E6). A judge who clicked a demo URL right now
would see nothing at all, because there is no demo URL. The rest of this section is what to do about it
without planning a deploy that cannot happen here.

### The minimum on-chain artefact that makes the answer yes

Ranked, cheapest first. Each tier is judged only by whether a judge can confirm it unaided.

- **Tier 0 — fails.** The page says "on Solana", the README says "Solana", and there is no address. This
  is the state `A3`'s sentence is written to reject.
- **Tier 1 — the minimum that passes.** One devnet account that belongs to this project, and one
  confirmed signature that touched it, both named in the README and both rendered in the product:
  - a **Token-2022 mint** created with `spl-token` on the operator's laptop (`--program-2022`,
    `--enable-non-transferable`, `--enable-metadata`, `--enable-permanent-delegate`, `--decimals 0`) as
    the ticket or the event's seat supply; and
  - the **mint address + cluster** in the README integration section, and the address and its live
    supply read over RPC and shown on the page (the repo's `rpc_adapter.py` already exists for exactly
    this read and is honest about doing nothing); and
  - **one confirmed signature** from minting one ticket, linked to Explorer.
  Cost: a few thousandths of a devnet SOL (E3), obtainable by the operator from the faucet or by
  `solana airdrop` (E4). This tier satisfies C1's four artefacts (README integration, configuration,
  transaction, and — because the Token-2022 program does the work — a program id that is not ours) but it
  is still "a chain attached to a pricing app".
- **Tier 2 — the version that answers the sentence.** Add one instruction that makes the *pricing output*
  the on-chain object: a memo (or metadata field) carrying a quote id and a hash of the quote, written
  before the sale opens, so the organizer's price is committed in public and cannot be re-cut. Then the
  chain is doing the thing the product claims. One transaction, no custom program, and it is the
  organizer's own published idea ("Verifiable AI: on-chain records of model outputs, datasets or
  provenance", A3). The refusal to show alongside it is then cheap and honest: re-submitting the same
  quote id must fail, and the failure is the chain's, not the UI's.
- **Tier 3 — do not attempt here.** A custom Anchor program, a mainnet deploy, or a transfer-hook
  implementation. No Rust toolchain (E1), and the verified winner record says a program is a
  differentiator rather than a requirement (D3).

### What can be simulated honestly, and how to label it

The rule is one line: **the chain artefacts must be real or absent; everything else may be simulated if
the screen says so.**

| Element | Can it be simulated? | How it must be labelled |
|---|---|---|
| Resale / ledger history the model prices from | Yes — it already is (`fixtures/synthetic_store.json`) | On the page and in the README: "synthetic fixture, not real transactions" and no accuracy, backtest or lift number attached to it |
| The buyer and the organizer wallets | Yes, devnet keypairs | "devnet" badge next to every address; never "live" or "production" |
| The model's coefficients / calibration | Yes, illustrative | "illustrative parameters, not calibrated" wherever a number from it appears |
| The mint, the signature, the RPC read | **No** | If the transaction did not happen, do not show a signature, an "on-chain" badge or an explorer link |
| Users, volume, traction | **No** | Nothing invented. D1's finding is that the winning entries were judged on what existed |

Three labelling habits, each copied from a verified winner rather than invented: every number names its
source and capture time (D3); a public page where any claim can be re-checked without a login (D4); and
the word devnet in the video, in the UI and in the first paragraph of the README, unprompted, because
the alternative is a judge discovering it and discounting everything else.

---

## Open questions this file does not close

1. **What "Initial Submission" means.** The schedule has a 10:00 ET deadline labelled "Initial
   Submission" and an 11:45 ET deadline labelled "Final Submission" (A2). Nothing published says whether
   the 10:00 submission can be edited afterwards. `p5` §9's advice to submit before 10:00 is safe under
   either reading; treating 10:00 as a hard freeze is the only risk-free assumption.
2. **Who judges.** `p5` assumes MLH staff plus sponsor DevRel. Unpublished. `p3-decision.md` §4's
   argument for skipping the AI track is unaffected either way.
3. **Whether standard rules apply to this event.** The rules file says organizers may use these "or
   their own"; the event page links terms that resolve to the MLH homepage (A8). The 2-minute video rule
   and the hackathon-name rule are the ones to comply with unconditionally; they are cheap and a
   violation is unrecoverable at 11:45.
4. **The final field size.** 7 now; submissions close 2026-11-08 13:00 ET (A1). Re-read the counter
   before locking the video, not after.
5. **The English original of D1.** The Vercel checkpoint on `midnight.network` blocked it from this host;
   the translation is the publisher's own, but a quote checked against the original would be better.

---

## Sources

Read in full on 2026-11-07 unless noted.

1. https://www.mlh.com/events/solana-hackathon — prize categories, submission counter, deadline field
2. https://events.mlh.com/events/15200-solana-hackathon — schedule, track text, ideas lists, registration questions
3. https://www.mlh.com/events/solana-hackathon/challenges/01a1a6ef-1328-c2f4-f126-f0506a239a09 — Top 3 Overall
4. https://www.mlh.com/events/solana-hackathon/challenges/01a1a6f0-dde1-f6fe-c748-37c36c7d45e6 — Best Beginner Hack
5. https://www.mlh.com/events/solana-hackathon/submissions — 404, measured
6. https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md — criteria, digital rules, AI rules, demo guidance
7. https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md — 4 min/project, 3 rounds, stack ranking, cheat check
8. https://guide.mlh.com/general-information/judging-and-submissions/rules-for-your-hackathon.md — organizer rule set, AI disclosure penalty
9. https://hacktoberfest-handbook.mlh.com/project-submissions-and-judging-for-hacktoberfest-hack-day — submission fields, winner-selection bullets
10. https://hacktoberfest-handbook.mlh.com/hack-days-partner-modules/partner-challenge-solana — current Solana challenge, licence requirement
11. https://hackdays-guide.mlh.com/partner-programs/solana — Judging Evidence, "what can you build"
12. https://events.mlh.com/series/partnered-hackathon — series membership, two upcoming events
13. https://www.mlh.com/seasons/2027/events — season payload, one Solana event
14. https://hackp.ac/ContestTerms → https://mlh.link/ContestTerms → https://mlh.com/ — measured redirect
15. https://note.com/midnight_jpn/n/nbc5d338ae2be — MLH x Midnight winners (translation of the 2026-08-20 post)
16. https://midnight.network/blog/celebrating-seven-winners-from-mlh-x-midnight-july-hack — original, blocked by Vercel checkpoint from this host
17. https://devpost.com/software/weenie-beanie — SwampHacks XII, MLH Prize: Best Use of Solana
18. https://devpost.com/software/solgpu — Knight Hacks IX, [MLH] Best Use of Solana
19. https://devpost.com/software/loka-pay — Hacklanta 26, [MLH] Best Use of Solana
20. https://help.devpost.com/article/84-video-making-best-practices — video guidance
21. https://faucet.solana.com/ — "Maximum of 2 requests every 8 hours", AI-agent notice
22. https://api.devnet.solana.com — JSON-RPC: getHealth, getVersion, getEpochInfo, getAccountInfo(Token-2022), getMinimumBalanceForRentExemption
23. https://registry.npmjs.org/@solana/spl-token/latest · https://registry.npmjs.org/@solana/web3.js — published versions
24. https://unpkg.com/@solana/spl-token@0.4.14/lib/types/instructions/initializeNonTransferableMint.d.ts — and `.../initializePermanentDelegate.d.ts`, `.../extensions/index.d.ts`
