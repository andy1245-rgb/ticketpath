# 00 — Index of the pre-VM direction documents

**Purpose.** `/home/friend/research/mlh-solana-2026/` holds fifteen documents written on
2026-11-06, before this VM and before the session that launched tonight. They are input, not
product. This file exists so the night's orchestrator cannot unknowingly re-litigate a decision
those documents already made, or redo work they already did — and so it can see, in one place,
where they contradict tonight's plan.

**Method.** All fifteen read in full from the read-only source; nothing under
`/home/friend/research` was modified. Status is judged against tonight's eight plan items, which
are referred to below as **(a)**–**(h)** and quoted verbatim where a conflict is marked.

| tag | tonight's plan item, as given |
|---|---|
| (a) | "Ticketpath is an ORGANIZER revenue-management tool that prices primary-market tickets off the resale record - there is no listing, bid, buy or checkout endpoint, and the platform's resale price cap suppresses markup" |
| (b) | "no LLM in the ticket path" |
| (c) | "no resale-listing product path, but the anti-fraud invariant must be on-chain (Token-2022 transfer hook or PDA escrow)" |
| (d) | "the build machine has no solana/anchor/cargo/rustc, so nothing can be deployed here - on-chain work is design-only, flagged ON-CHAIN-FOR-LAPTOP" |
| (e) | "the backend binds port 8788 because 8787 belongs to another process" |
| (f) | "the frontend at /home/friend/ticketing-frontend is live on :3000 and must not be touched" |
| (g) | "stdlib Python only, no new dependencies" |
| (h) | "submission deadline is Sun 2026-11-08 10:00 America/Toronto = 15:00Z, initial, not the 11:45 final" |

**Two checks done while writing this, not assumed.**

1. `which solana anchor cargo rustc spl-token` returns nothing; `~/.local/share/solana` and
   `~/.config/solana` do not exist. (d) is true on this machine.
2. `lib/types.ts` + `API_CONTRACT.md` in the live frontend carry five GET endpoints, one
   resale-history read and two wallet-verification POSTs. There is no listing, bid, buy or
   checkout endpoint anywhere in the contract: (a) is true of the interface tonight must satisfy.

**The working tree moved while this was being written.** At 10:52–10:55Z the night's own build
created `ticketpath/` and `fixtures/` in this repo. Every "exists on disk" answer in §5 was taken
against that state and is dated; nothing in §1–§4 changes because of it.

---

## 1. The fifteen documents

| # | file | what it is | date it states | status against tonight |
|---|---|---|---|---|
| 1 | `01-mlh-events-solana.md` | MLH season structure corrected, 385 event records harvested, the one live Solana Hackathon, its five prize tracks and schedule | Compiled 2026-11-06 (America/Toronto) | **Still valid.** Prize tracks, schedule and the two deadlines are the authority the rest of the corpus cites. Its §2.1 explicitly marks the $1,000 as possibly-per-team: "**INFERENCE (flagged)**". |
| 2 | `02-solana-hack-ecosystem.md` | Solana competition outside MLH: Colosseum, Eternal, `hackathons.solana.com`, Superteam, grants, with exact prize figures | Compiled 2026-11-06 (UTC) | **Still valid, out of scope for tonight.** Nothing here bears on the build; it is the post-weekend map (Dec 5 Perps, Eternal by 2027-03-20). |
| 3 | `03-what-wins-solana.md` | Teardown of 13 flagship Solana hackathons 2020–2026: 45+ winners, verbatim rubrics, win rates, anti-patterns | Compiled 2026-11-06 | **Still valid.** The judge model tonight's rubric research is meant to verify, not re-derive. |
| 4 | `04-mlh-judging-playbook.md` | MLH rules verbatim, CoC, AI-disclosure rules, digital-event rules, judging arithmetic, 20 tactics, submission checklist | Research date 2026-11-06 | **Still valid.** The compliance surface (rules 1–14, digital rules 1–6, the AI-disclosure penalty) still governs Sunday. |
| 5 | `05-attack-plan.md` | Synthesis of 01–04 into three lanes and a 48-hour playbook | Compiled 2026-11-06, ~12:30 ET | **Still valid in its lane analysis; superseded in its clock and its AI-track advice.** §6 "The 48-hour clock" is sized from Fri 12:00 ET; tonight has ~28 h from Sat 10:50Z. §1.3 "Shape 2 — AI track, if not eligible" is overtaken by (b) and by `p3` §4 / `p5` §9. |
| 6 | `p0-deconstruction.md` | What the event rewards: physical facts, prize structure, the four MLH rubric criteria verbatim, "uses Solana for something it's good at" made mechanical, five idea filters | event page "fetched at 2026-11-06 18:13 UTC" | **Still valid.** Its filters (56 person-hours, fails on Ethereum, 15 silent seconds, one wow beat, a true learning story) still govern what may be built. §4.2 recommends an AI-actor/chain-guardrail shape, which (b) removes from the ticket path. |
| 7 | `p1a-prior-winners.md` | Crawl of MLH sponsor-prize winners: 38 Solana-prize winners classified by mechanism (custom program 21%, memo 26%, mint 18%, read-only 18%) | Compiled 2026-11-06 | **Still valid.** The mechanism distribution is what tonight's rubric research should be checking, and it is the evidence that "a working on-chain artefact" is the bar. |
| 8 | `p1b-tech-feasibility.md` | Solana toolchain state Nov 2026: Anchor 1.x, Agave 4.4, the two JS generations, devnet gotchas, three archetypes with hour estimates | Compiled 2026-11-06, 18:15–18:40 UTC | **Still valid as a version reference; §3.2's extension-conflict claim is superseded** by `p2b` §3.1 and `p5` §0, which the document itself flags: "**CORRECTED 2026-11-06 15:30 ET — two claims in this section were wrong.**" Its §1 JS-generation split is the thing to read before anyone installs a package. |
| 9 | `p1c-idea-breadth.md` | 48 candidate ideas screened on five axes, top-8 shortlist, ten named traps | Compiled 2026-11-06 | **CONFLICTS with (a) and (c).** See §2 below — X1, the document's own #1 pick, is a marketplace with a resale page. |
| 10 | `p1d-video-judging.md` | How a digital event is judged, the artefact chain, shot-by-shot 2-minute video template, crowding analysis, production checklist, failure modes | Compiled 2026-11-06 | **Still valid.** The video plan survives the product change intact; it is written about "the working thing", not about tickets. |
| 11 | `p2a-token2022-ticket.md` | Token-2022 `NonTransferable` path, source-level: extension co-existence, the CLI/JS commands, error 0x25, rent costs, runbook | Compiled 2026-11-06, 18:20–18:50 UTC | **CONFLICTS with (d).** §7 is a three-hour runbook that installs the Solana toolchain on the machine it runs on. See §2. |
| 12 | `p2a-verified-spike.md` | The spike, "actually run": mint created, transfer refused, failed transaction landed, extension matrix, burn allowed | "**Verified empirically on this machine, 2026-11-06 ~14:15–14:35 ET.**" | **CONFLICTS with (a) and (d).** See §2. Its six mechanism facts are the corpus's strongest asset; its artefacts are not on this machine or on devnet (§4). |
| 13 | `p2b-scalper-prior-art.md` | Prior art on soulbound ticketing, the honest weakness, which Token-2022 mechanism, the scalp-bot angle, naming, pitch | "Date: 2026-11-06." | **CONFLICTS with (a) and (c).** Its §3.3 is a resale flow end to end. Its §4.3 conclusion ("**Skip**" the real LLM) is the decision (b) inherits. |
| 14 | `p3-decision.md` | The decision document: "a ticket exchange that cannot be scalped", adversarial review as a tired judge, rubric scoring, entry plan, kill criteria, pitch candidates | no date stated; internal evidence puts it after p2b and before `p5`'s 15:30 ET correction | **CONFLICTS with (a) and (c).** See §2. Its §4 AI-track decision is the one (b) rests on. |
| 15 | `p5-build-spec.md` | The build spec and the 1:50 video: corrections to an earlier draft, verified stack, six screens, repo layout, hour-by-hour clock, shot list, README template, submission checklist | "Written 2026-11-06 ~15:00 ET, **corrected ~15:30 ET after the p2b findings were tested**" | **CONFLICTS with (a), (c) and (g).** Also **superseded in its clock**: "~43 hours" against tonight's ~28 h to 15:00Z. See §2. |

---

## 2. The conflicts, quoted

Six documents conflict with tonight's plan. Quoted exactly, with the plan item they contradict.

### `p3-decision.md` — conflicts (a) and (c)

> "**Build: a ticket exchange that cannot be scalped.**"

> "App: a real event listing → purchase → ticket in wallet with a scannable gate pass → a "return to issuer at face" flow that re-mints to the next buyer."

Against **(a)**: an event listing, a purchase, and a re-mint-to-next-buyer flow are exactly the
listing/buy/checkout surface (a) says does not exist and must not be invented. Against **(c)**:
"resale only through the issuer at face" (`§2`, "the fan is not trapped — they can return the
ticket and get their money back, and the next fan buys it at face") is a resale product path.

### `p5-build-spec.md` — conflicts (a), (c) and (g)

> "| Buy | issuer **mints** 1 to the fan |"

> "| 4 | **Try to resell** | A "send to a friend" / "sell to a scalper" action that **fails** — route (c), rendered in-app with the program's own log line |"

> "| 5 | **Return** | Burn → refund confirmed |"

> "## 2. Verified stack — do not deviate"

with `@solana/web3.js`, `@spl-token`, `@solana/wallet-adapter-react` and a Next.js `app/` tree
(§5). Against **(a)**: screens #2, #4 and #5 are buy, resell and return. Against **(c)**: screen
#4 is a resale-listing surface. Against **(g)**: the implementation language and dependency set
are Node packages, not stdlib Python.

### `p1c-idea-breadth.md` — conflicts (a) and (c)

> "X1 · TICKET REFUSES ANY PRICE ABOVE FACE … Chain: Token-2022 mint with a transfer hook that rejects any transfer which is not routed through the marketplace program, and the marketplace program caps the recorded price at face"

> "Build shape: mint with hook, marketplace program that CPIs into transfer and caps price, one resale page."

Against **(a)**: "one resale page" is the resale-listing product path. Against **(c)**: the same.
Note the doc's own §5 sells it with an invented error string, `TransferHook: price exceeds face
value`, which no program emits.

### `p2b-scalper-prior-art.md` — conflicts (a) and (c)

> "**Mint = `NonTransferable` + `PermanentDelegate(authority = issuer)` + `MetadataPointer`/`Metadata` for the seat data. Ticket account = plain ATA. No custom program.**"

> "The resale flow, end to end: FAN A wants out … 2. tx: BurnChecked(ticketAta, mint, 1, authority = PERMANENT_DELEGATE) … 4. tx: createAssociatedTokenAccount(fanB) + MintTo(fanB, 1, authority = mint_authority)"

Against **(a)**: the whole product is the resale flow. Against **(c)**: "Fan B holds the seat" at a
price the issuer set is a resale product path, and the mechanism chosen ("No custom program") is
not the transfer hook or PDA escrow (c) requires.

### `p2a-verified-spike.md` — conflicts (a) and (d)

> "3. **The return path is a burn, not a transfer.** Rewrite the product flow: buy = mint, return = burn + refund, resale = issuer mints to next fan."

Against **(a)**: buy, return and resale are named product flows. Against **(d)**: its §5 runbook
begins

> "# ---- 0. toolchain (no Rust anywhere) ---- sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)""

which is an install on the build host, and `solana-test-validator --reset --ledger /tmp/mlh-ledger`
below it. Nothing in that runbook can be executed on this machine.

### `p2a-token2022-ticket.md` — conflicts (d)

> "## 7. Runbook — copy-paste, in order, ~3h"
> "sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)""
> "solana --version && spl-token --version        # spl-token-cli 5.6.1  MEASURED"

Against **(d)**. The document's own §0 states the constraint it was written under — "**no Rust
toolchain**" — and solves it by installing prebuilt Agave binaries, which is still an install on
the build host and is not available to tonight.

### Two conflicts that are not with tonight's plan but with each other

- `p2a-token2022` §3.2 says "`NonTransferable` + `TransferFeeConfig` is rejected by the runtime";
  `p2b` §3.1 and `p5` §0 say no such conflict rule exists and the pair is merely inert. `p5` §2.3
  records it as "⚠️ disputed … **Do not repeat either claim.**" Treat the combination as unusable
  and undecided, not as settled either way.
- `p1b` §3.2 wrote "`PermanentDelegate` ('issuer can claw back')" and was corrected in place:
  "A `PermanentDelegate` can **never transfer** a `NonTransferable` token … it can only **burn**
  it." Any pitch sentence using "claw back" means burn.

---

## 3. Decisions already made that tonight must honour

Each line names the document and section that made it. These are the decisions; the reasons are
in the source.

### The AI/ML track

1. **No AI-track entry, and no LLM in the loop** — `p3-decision.md` §4: "**AI Track** | **NO — decided by p2b.**"; `p5-build-spec.md` §9: "**SKIP the AI track (p2b: the generic form is a cliché and the bot is scripted). SKIP Gaming**".
2. **A scripted attacker is not an AI entry** — `p2b-scalper-prior-art.md` §4.3: the "Real LLM deciding each step" row is "**Skip.** … It also invites 'so the guardrail is a prompt?'".
3. **The reason the question stays open rather than closed** — `p3` §4 requires a *written* answer with reasons; `NIGHT-BRIEF.md` §6 makes "an AI/ML component costs more than it scores here" a valid finding only if argued from the rubric, not assumed. Tonight may confirm or overturn these two documents, in `F-decision-log.md`, and not silently.
4. **Best Beginner is a live, unconfirmed eligibility question, not a footnote** — `p0-deconstruction.md` §2: "**Best Beginner is a live question, not a footnote.**"; `04-mlh-judging-playbook.md` §4 tactic 13 says confirm the organizer's definition first.

### The product framing

5. **Do not pitch the concept; pitch the implementation** — `p5-build-spec.md` §1.1: "**do not pitch the concept.** The concept is a Devpost trope. Pitch the implementation"; `p2b` §1 verdict: "tired as a slogan, fresh as an implementation".
6. **The named mechanism was chosen and the alternatives were killed with reasons** — `p2b` §5 recommends "Burn and Reissue" and bans "soulbound", "anti-scalp", "protocol" and "fi"; `p3` §1 rejects the framing "Not 'a soulbound ticket.'"
7. **Never say "NFT ticket" on camera** — `p3-decision.md` §2: "Also: do not use the phrase "NFT ticket" anywhere in the video. Say "ticket.""
8. **The "why a blockchain" answer is the one to lead with** — `p5` §1: "**the venue can verify a ticket without trusting our backend, and the issuer cannot secretly sell a 501st ticket for a 500-seat room because the mint's supply is public.** Lead with *the issuer cannot cheat the fan*, not with scalping."
9. **The scam-bot failure must be structural, not narrated** — `p3` §2: "make the bot's failure *structural*, not narrated. It calls the real transfer instruction"; `p2b` §4.2: "**The refusal must come from the standard, not your code.**"
10. **Scope: one seat, one event, one fan** — `p3` §2 "the slice is one seat, one event, one fan. No multi-event browsing, no search, no auth beyond a wallet, no admin panel"; `p5` §4 "Not in scope, at all: search, multiple events, user accounts, an admin panel, notifications, profiles, a database." Tonight's product is a pricing tool, but the anti-scope-creep rule is the same one.

### The on-chain design

11. **The ticket never moves; burn is the only exit** — `p2a-verified-spike.md` §1: "There is no transfer path, ever. The only way a ticket leaves a wallet is a **burn**. … Design around burn, not round-trip transfer."
12. **The refusal is the asset, and its exact strings are known** — `p2a-token2022` §4.2: "**Three strings to hold:** `custom program error: 0x25` (code), `{"InstructionError":[0,{"Custom":37}]}` (machine), `Transfer is disabled for this mint` (human — put this on screen)."
13. **The extension stack that composes** — `p2a-verified-spike` §3.1: `NonTransferable` + `Metadata` + `PermanentDelegate` + `Close`, "✅ **`J8hNmBD7PCuVvNNxL4HSjj3LV9QHwkaUgfseZhRGdjbe`**"; `NonTransferable` + `PermissionedBurn` fails "❌ `custom program error: 0xc` (InvalidInstruction)".
14. **`--decimals 0`, because a ticket is not divisible** — `p5` §2.2: "A ticket is not divisible; 9 decimals is a giveaway that you didn't think about it." (`p2a-verified-spike` §1 in fact shows the CLI defaulting to 9 on its own mint.)
15. **`TOKEN_2022_PROGRAM_ID` must be threaded through every client call** — `p2a-token2022` §4.3/§6.3 and `p5` §2.1: "Every `spl-token` helper must be given `TOKEN_2022_PROGRAM_ID`", or you get `TokenInvalidAccountOwnerError`, "which explains nothing".
16. **Pin the JS stack to one generation, if JS is used at all** — `p1b` §1.3 and `p2a-token2022` §3.1: `@solana/web3.js ^1.99.0`, `@solana/spl-token ^0.4.15`, `@solana/wallet-adapter-react ^0.15.40`; "**Never install `@solana/kit` alongside these.** Two incompatible generations." (`p5` §2.)
17. **The issuer keypair never reaches the browser** — `p5` §5: "The issuer keypair must never reach the browser. Server actions only. A leaked mint authority with `PermanentDelegate` means anyone can burn anyone's ticket."
18. **A client-side limit is not a limit** — `p1b` §4.3: "**A client-side check (`if (amount > MAX) throw`) is not a limit.** … The credible version is a PDA authority." This is the same distinction (c) draws when it says the invariant must be on-chain.

### The demo

19. **Never film the wallet popup** — `p5` §3: "**Do not film the Phantom popup.** Its wording on a failing transaction is unverified"; `p2a-token2022` §4.3 marks it `UNVERIFIED`; `p2a-verified-spike` §7 repeats it.
20. **`simulateTransaction` is the deterministic shot; a real failed transaction is the proof shot** — `p5` §3 route (c) vs (b); `p2a-token2022` §5: "Film (c) as the primary; optionally cut to (a) for 4 seconds of B-roll proof. Skip (b)." (`p5` §3 chooses (c) for the in-app shot and (b) once for an Explorer hash — a deliberate difference from `p2a`, resolved in `p5`'s favour by being the later document.)
21. **The demo must show the refusal before the ticket** — `p3` §2: "the differentiation must be **visible in the first 20 seconds** and must be the refusal, not the ticket."
22. **The video opens on the working product with the hackathon name in frame 1 and in the first spoken sentence** — `p1d` §2.2 and §3.2: "Frame 1 is the working app, mid-flow. Lower-third burns in: `Solana Hackathon — <ProjectName>`."
23. **One unbroken take from the click to the explorer**, plus a terminal confirm of the same signature — `p1d` §6.4: "Five stacked proofs … The strongest version of (1)–(4) is a single unbroken take from the click to the explorer confirmation."
24. **Target 1:50, not 2:00** — `p1d` §2.2: "Design target **1:50**, not 2:00 … a file that lands at 2:03 fails on the letter of the rule."
25. **One sentence of Learning, on camera, is 25% of the score and free** — `p0` §3.1; `04` §4 tactic 8; `p1d` §2.2 at 1:25–1:35.
26. **Declare a small thing and achieve all of it** — `p0` §3.1: "**Completion is 25% and it is binary in the video.**"

### The pitch

27. **The one-sentence pitch is written and rehearsed** — `p2b` §6 primary: "The chain refuses the transfer; the box office takes the return." `p3` §6 leaves the final choice open between three candidates and requires it to survive the "why a chain" attack.
28. **The strongest objection is "soulbound is what a monopoly calls a feature"** — `p2b` §2.1: "**\"non-transferable\" is what a monopoly calls a feature.**" The rehearsed answer (`p2b` §2.2c) is the return-path sentence, not a denial that fans have rights.
29. **If the Ontario resale cap is used, say it as a fact with its enforcement gap** — `p5` §1.2: "Ontario capped resale at face value in April 2026 and began inspections in May, enforced by letters and site visits (CBC). That is an unverifiable rule." See §4 below before quoting it on camera.
30. **Pitches are discouraged; demo, then answer** — `04-mlh-judging-playbook.md` §1.6, MLH verbatim: "**Pitches and presentations are discouraged. You are not judged on the quality of your pitch or the quality of your idea.**"

### Submission mechanics (all still binding tonight)

31. **Submit before the initial 10:00 ET deadline, not 11:45** — `p5` §9: "Submitted before **10:00 AM ET** — the initial deadline, not 11:45"; `p0` §1 calls 10:00 "← the real deadline"; `p1d` §6.6 builds its Sunday backwards from it. This is (h), and it is unanimous across the corpus.
32. **Video locked by 09:30, submission done by 09:50** — `p5` §6 and §9; `p5` §6.1 kill criteria are all timed to this.
33. **MLH Challenges page, not Devpost** — `04` §6: "Every presenting project must be submitted through the event's **Challenges page** … **Devpost, a form, or another platform does not replace this flow.**"
34. **Select every eligible challenge; multi-select is penalty-free** — `04` §4 tactic 1; `p0` §2.
35. **Hackathon name spoken in the first sentence, video ≤2:00, made this weekend, public forever** — `04` §1.5 digital rules 1–3; `p1d` §1.5.
36. **AI tooling disclosed in the README, or disqualification and a report to `cheating@mlh.io`** — `04` §1.4, organizer copy-paste rules verbatim.
37. **Repo public and staying public; first commit inside the event window** — `04` §1.3 rules 12–13 and traps 1 and 3.
38. **No cross-posting this project to another hackathon** — `04` §1.5 rule 5, which kills the lane-B reuse plan in `05` §2.3 ("**you cannot reuse the lane-A repo**").

---

## 4. Claims these documents make that are worth checking rather than trusting

Numbers, competitor claims, judge behaviour, prize structure and anything asserted without a
source. One line each, with the document.

**Prize and event structure**

1. Whether the $1,000 Top-3 microgrant is per team or a single total is **not stated** on the event page — `01-mlh-events-solana.md` §2.1 marks its own reading as "**INFERENCE (flagged)**"; no other document flags it.
2. "One Top-3 finish is worth five track wins" — `p0-deconstruction.md` §2, an inference from the stated prizes, not a published rule.
3. The event window and the ~56 working hours ("46 hours … minus ~14 h sleep, minus ~4 h for video + README") — `p0` §1; arithmetic on unpublished assumptions.
4. Frontier's per-team $10,000 Top-25 amount comes "from Superteam Canada's guide, not Colosseum" — `03-what-wins-solana.md` Appendix B item 4.
5. All win-rate percentages (~4.7% → ~1.0%) are the author's own count of announced slots — `03` §2.3 and Appendix B item 3: "**Prize-slot counts in §0 and §2.3 are my arithmetic**, not official".
6. "565 registered, 0 submissions" for the Dec 5 Perps event is a snapshot and the deadline moved once already — `02-solana-hack-ecosystem.md` §2.2: "**verify again before you sink two weeks into it**".
7. World's Fair's "2,973 submissions … largest in crypto history" and the late-November winners window are the organizer's own framing plus the author's arithmetic — `02` §1.2.
8. "Solana Foundation" as this event's sponsor is **NOT VERIFIED**; the sponsor of record is the string "Solana Q4 2025 - Q4 2026" — `01` §5.4.
9. Whether a non-student may compete is undocumented — `04` §8 item 2 and `05` §1.4 ("**one unresolved gate**"). This decides whether Sunday's entry is legal at all.

**Judging behaviour**

10. "Three minutes per team", "1 project per 4 checked-in hackers", the judge formula and stack ranking are quoted from MLH's organizer guide, which is a **recommendation**, not this event's rulebook — `04` §3; `p1d` §7 lists "whether the 3-round stack ranking is used at all" as unknown.
11. "Assume 100% asynchronous video review" is an inference from a one-hour gap between final submission and closing ceremony, not a published fact — `p1d` §1.2.
12. "The first 20 seconds decide the nomination" / "judges decide in 10 seconds" — `04` §3.1 and `p1d` §3.1, which is honest about it: "the specific "judges decide in 10 seconds" number is **not documented anywhere I could verify**".
13. "63 Loom, 49 YouTube, 8 Vimeo … 139 winning submissions" is Superteam Balkan's count, and `p1d` §2.3 says so ("the 139 count is Superteam Balkan's, not a Colosseum statistic").
14. "21% of winners deployed a custom program; 26% a memo" rests on a sample of 38 recovered from a crawl where "285 pages failed on rate limiting" — `p1a-prior-winners.md` §0 and §4.
15. "36 of 38 winners mention AI/LLM/agent/model in their own write-up" — `p1a` §3 pattern 6; a keyword count over self-written Devpost text.
16. "The ten most likely submissions" and the organizer's crowded-idea lists — `p1d` §4.3, reading the event page's own "Ideas to Get Started" lists; the lists are real, the ranking is judgement.

**Technical and prior-art claims**

17. The census "only **8** live Token-2022 transfer-hook programs across 625 hooked mints" is a third-party GitHub repo "observed 2026-08-08" — `p2b` §1.3; not re-run here.
18. `NonTransferable` + `TransferFeeConfig`: `p1b` §3.2 says rejected, `p2b` §3.1 says no such rule, `p5` §2.3 says "**Do not repeat either claim.**" The disagreement is unresolved and untested.
19. The mint addresses, the failed-transaction signature and the burn signature in `p2a-verified-spike` do not resolve on devnet (checked today, `getAccountInfo`/`getTransaction` return null). They are local-test-validator artefacts and the ledger is gone — see §5 below.
20. "The demo asset exists and **points at devnet**" — `p2a-verified-spike` §6.2. Contradicted by the same document's §2.2, which reports "Signature landed, slot 279" (a local validator), and by the null devnet lookups above.
21. `p5-build-spec.md` §0: "Every command and error string here was executed and verified on this machine" — "this machine" was the pre-VM host, which had Agave; it is not this VM.
22. `p2a-token2022` §2.1's download figure ("84,745,758 bytes"), the `spl-token-cli 5.6.1` version and the tarball contents were measured on a host that had network access to `release.anza.xyz`; tonight's install path is untested and irrelevant under (d).
23. Devnet rent arithmetic "`minimum_balance = (len + 128) × 5080` … a 165-byte account is now 1,488,440 lamports, not 2,039,280" — `p2a-token2022` §6.2, measured against the RPC on the day; worth one RPC call if any cost claim survives into the submission.
24. Faucet limits "**Maximum of 2 requests every 8 hours**" and the CLI "5 SOL per request" — `p1b` §2.3 and `p5` §6; quoted from the faucet page, which also says "AI agents should not use this faucet".
25. Ontario's resale cap: "took effect in April 2026 … inspections in May 2026, with fines of $3,000–$250,000" rests on a single CBC URL, and `p5` §1.2 builds a pitch sentence on it. Corroborate or drop it before it goes on camera.
26. Passbound/EasiTickets as "a live Solana soulbound-ticket product with rotating QR codes" and Fair Line's "makes scalping mathematically impossible" tagline — `p5` §1.1, `p2b` §1.1; competitor claims read off their own pages.
27. XP's "$6.2M" raise is `UNVERIFIED` by the document's own admission — `p2b` §7: "Headline and outlet are reliable; details are not."
28. Devpost search totals (`scalping` → 80, `nft ticket` → 288) are "not exact counts, but the ratio is the message" — `p2b` §1.2.
29. `p3-decision.md` §3's rubric table ("Design **High — this is where we win**", "Completion **High**") is the author's self-assessment against the rubric, not evidence.
30. `p1c` §5's demo error string `TransferHook: price exceeds face value` is invented for illustration; no program emits it. Do not reuse it.

---

## 5. Work these documents describe as done

So the night does not redo it. "Exists on disk" was checked, not assumed.

| document | what it claims to have produced | where it says the artefact is | exists? |
|---|---|---|---|
| `01-mlh-events-solana.md` | 385 per-event prize pages fetched; both season payloads paged to exhaustion; the one live Solana event identified with five prize tracks | no path — findings live in the document | n/a (research in-document) |
| `02-solana-hack-ecosystem.md` | Full state of the non-MLH Solana competition as of 2026-11-06, with exact prize figures | no path | n/a |
| `03-what-wins-solana.md` | 13 hackathons, 45+ winners, verbatim rubrics, computed win rates | no path | n/a |
| `04-mlh-judging-playbook.md` | MLH rules quoted verbatim from primary sources, "all quotes were re-fetched" | no path | n/a |
| `05-attack-plan.md` | Three-lane synthesis with a 48-hour clock | no path | n/a — and its clock is superseded |
| `p0-deconstruction.md` | The event page's physical facts, prizes and rubric, verbatim | no path | n/a |
| `p1a-prior-winners.md` | 672 unique Devpost projects crawled, 87 winners, 38 Solana-prize winners classified | no path, no saved dataset | n/a — the crawl is not stored; re-running it means re-crawling |
| `p1b-tech-feasibility.md` | A verification log of every version number (§8), including live devnet `getVersion`/`getEpochInfo` | no path; the log is the table | n/a |
| `p1c-idea-breadth.md` | 48 screened ideas, top 8, traps | no path | n/a |
| `p1d-video-judging.md` | Shot-by-shot video template and production checklist | no path | n/a |
| `p2a-token2022-ticket.md` | Agave tarball downloaded and its contents listed; `spl-token` 5.6.1 run; rent measured via RPC; extension source read | `~/.local/share/solana/install/active_release/bin` implied by §2.1's installer; no tarball path given | **No.** `~/.local/share/solana` does not exist and no `spl-token` is on PATH. |
| `p2a-verified-spike.md` | A mint created (`EH2kuSM4…`); a four-extension mint (`J8hNmBD7…`); a refused transfer; a failed transaction with a signature (`2Qqpo4t9…`); a delegate burn (`28yD1xDH…`); a Node script `/tmp/mintest/failtx.js`; a validator ledger `/tmp/mlh-ledger` | `/tmp/mintest/failtx.js`, `/tmp/mlh-ledger`, and the four base58 identifiers | **No.** `/tmp/mintest` and `/tmp/mlh-ledger` are absent; all four identifiers return `null` from `api.devnet.solana.com` (apiVersion 4.4.0, slot 519,636,185). The spike ran on a local validator and no durable artefact of it survives anywhere. |
| `p2b-scalper-prior-art.md` | Prior-art table with 23 inline URLs; the mechanism decision; the pitch | no path | n/a |
| `p3-decision.md` | The decision, the adversarial review, kill criteria, pitch candidates | no path | n/a |
| `p5-build-spec.md` | A repo layout — `app/(screens)/page.tsx`, `buy/page.tsx`, `ticket/[mint]/page.tsx`, `gate/page.tsx`, `components/Ticket.tsx`, `components/GatePass.tsx`, `components/RefusalPanel.tsx`, `lib/token2022.ts`, `lib/issuer.ts`, `lib/simulate.ts`, `scripts/mint-ticket.ts`, `scripts/scalpbot.ts`, `docs/README.md` | repo root, unnamed; `p5` §5 | **No.** Checked at 10:55Z: none of the twelve named paths exists, and there is no `.ts`/`.tsx` file anywhere in this repo. `/home/friend/ticketpath` does not exist. A Python package `ticketPricing/ticketpath/` was created at 10:52–10:55Z by tonight's own build — it is a different artefact with none of these files, and it is not evidence that p5's build was ever done. The only UI on disk is the live frontend, which must not be touched (f). |

**The three consequences tonight should carry:**

- **Nothing has to be un-done, because nothing was built.** The pre-VM work is paper. There is no
  code to port, no repo to clean up, no partial implementation to reconcile.
- **The on-chain "proof" is not reproducible in this VM.** Six mechanism facts are recorded and
  trustworthy as source reading; the empirical demonstration of them is gone. Any on-chain claim
  tonight carries `p2a-verified-spike`'s provenance, not tonight's measurement.
- **`p2a-verified-spike` supersedes `p2a-token2022` only where they disagree**, and it says so
  itself ("This supersedes any part of `p2a-token2022-ticket.md` that disagrees with it") —
  except on `TransferFeeConfig`, where `p2b`/`p5` overturn `p1b` and nothing was ever tested.

---

## 6. What this index could not settle

1. **`p3-decision.md` has no date line.** Its dating is inferred from its own cross-references
   (it cites `p2b` as still running in one place and as decided in another) and from `p5`'s
   15:30 ET correction. It is the document to read first if the corpus is ever re-read in order.
2. **Where the old product ends and tonight's begins is a decision, not a fact.** `p3`, `p5`,
   `p2b`, `p1c` and both `p2a` documents were written as one coherent plan — a ticket exchange.
   Tonight's plan keeps their *mechanism research* and rejects their *product surface*. The
   boundary is drawn in §2 and §3 above; if the orchestrator moves it, `F-decision-log.md` is
   where the move gets recorded, per (a)'s own rule: "Any reversal gets written into
   `F-decision-log.md` with its reason; never taken silently."
3. **`p1b` §1.3's JS-generation analysis is unusable under (g) and still worth knowing** if the
   frontend ever needs a client change: the v1 pins it names are the only combination that works
   with `spl-token` and `wallet-adapter`.
