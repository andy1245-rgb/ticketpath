# Region-aware resale caps — the legal basis (phase 1)

**Written:** 2026-11-08. **Method:** five parallel primary-source research agents, one per cluster
(United Kingdom and Ireland; Canada; Australia; United States; European Union), each told to read the
instrument itself, quote it, and record every gap rather than fill it. This file is the synthesis;
the five cluster records it summarises are in `records/findings/33-b-region-cap-law-sources/` and are
the evidence. **This is not legal advice, and it is not a complete survey of any jurisdiction.**

**Classification.** Programme §4.3 applies, but with a specific reading for this file: a claim here
is **A** when the instrument's own text was read (the statute, the regulation, the public law), **B**
when an official government or regulator page states it, **D** when only a secondary source states
it, **E** when it is unknown. Every row below carries its class. A **D** or **E** row is not a
finding and the engine must not enforce it.

**The question the engine asks of this file is narrow:** for a given event jurisdiction and a given
sale date, is resale above a limit restricted by law, and if so what is the limit measured against?
It does not ask whether a platform *should* cap, and this file does not answer that.

---

## 0. The answer, in one table

The table the code reads is `ticketpath/data/region-caps.json` (version `2026-11-08.1`, 82 codes, 84
instruments). This is the human reading of it. "Announced" is a first-class status: it means a
government has said it will do something and has not.

| Jurisdiction | Price cap in force? | Instrument | Base | Coverage | Class |
|---|---|---|---|---|---|
| **IE** | **Yes**, 0 bps over the original sale price | Sale of Tickets Act 2021 s. 15 | face **+ primary fees** | designated venues/events only | A |
| **CA-ON** | **Yes**, 0 bps over the total price paid | Ticket Sales Act 2017 s. 2(3), added 2026 | face **+ primary fees** | all resale | A |
| **CA-QC** | **Yes**, 0 bps over the announced price | Consumer Protection Act s. 236.1 | face | all resale | A |
| **AU-NSW** | **Yes**, face + min(fees paid, 10% of face) | Fair Trading Act 1987 (NSW) Part 4A | face + **capped** fees | all resale | A |
| **AU-SA** | **Yes**, 110% of face | Fair Trading Act 1987 (SA) Part 4A | face | all resale | A |
| **AU-WA** | **Yes**, 110% of (face + booking fee) | Ticket Scalping Act 2021 (WA) | face **+ fees**, with a margin | all resale | A |
| **AU-VIC** | **Yes**, 110% of face | Major Events Act 2009 (Vic) Part 9A | face, fees excluded | gazetted declarations only | A |
| **GB** (all three nations) | **No.** A cap was announced 2025-11-19 and is not law | Consumer Rights Act 2015 ss. 90-95 | — | no price cap (disclosure duties only) | A (law), B (announcement) |
| **CA-BC** | **No** (the Act expressly does not regulate price) | Ticket Sales Act SBC 2019 | — | disclosure, refunds, bots | A |
| **US-CA** | **No** general cap | Bus. & Prof. Code ch. 21 | — | disclosure/transfer | A |
| **US-MA** | **Unknown**: one section read, the chapter was not surveyed | MGL ch. 140 s. 185A | — | licensing | A (the section), E (the chapter) |
| **US-NY** | A ceiling exists but **who it binds is unsettled** | Arts & Cultural Affairs Law s. 25.29 | established price + taxes | operator and its agents; reseller status unresolved | A (text), UNVERIFIED (scope) |
| **US-FL** | **Yes**, but a **$1 margin** over the original seller's price, four categories | Fla. Stat. s. 817.36 | face + $1 (a money amount) | enumerated transactions; escapable by an authorised site | A |
| **AU-QLD** | A law exists; its terms were **not read** | Major Sports Facilities Act 2001 (Qld) | unknown | designated facilities | D (reported) |
| **EU** | **No EU instrument caps ticket resale price** | DSA, UCPD, CRD read | — | — | A |
| FR, IT, ES, BE, PT | **Not established in this pass** | national statutes behind JS/bot walls | — | — | E |
| CA-AB, MB, SK, NS, NB, PE, NL, YT, NT, NU; AU-TAS, ACT, NT; US-AR…US-NV (22 states); DE, NL, PL, SE, DK, AT, CZ, HU, GR | **Unknown** | nothing located, or not opened | — | — | E |

**Three sentences that matter more than the table.** (1) The United Kingdom's cap is announced
policy, not law, and a table that treated it as law would refuse lawful sales in the largest market
in this dataset. (2) Ontario added a price cap in April 2026, so the same event sold before and after
that date is governed by two different rules; this is exactly the "law changed after sale" case the
design has to handle. (3) Most of the world is *unknown*, not *unrestricted*, and an engine that
reports "monitored" for an unknown jurisdiction is lying by omission.

---

## 0.1 What changed after the phase-1 review, and why

A non-builder reviewer read this file, the five cluster records, the table and the resolver, and found
four defects that made the record say something the code did not do. All four are fixed, and the tests
that would have caught them now exist:

1. **A "no cap" finding leaked across a border.** Country inheritance let `US-OH` (no row of its own)
   inherit the two federal rows and report `monitored`, a positive finding of no cap in a state nobody
   read. Inheritance now carries only a parent's `all_resale` rows, so a sectoral rule (a federal bot
   ban, a disclosure duty) can never answer a state's price question. Every US state and DC now has a
   row of its own, most saying `not checked`.
2. **Florida and Queensland read as "no cap" on the default path.** The designated-events gate ran
   before the "is this basis readable?" check, so an unread cap (Queensland) and a fixed-dollar margin
   (Florida) both fell through to `monitored` unless the operator passed a flag. An unread basis is now
   checked first: both are `unresolved` with and without the flag. Florida's coverage is also corrected
   from `designated_events` to `enumerated_events`: its four categories are statutory transaction
   classes, not a ministerial list.
3. **"Announced is not law" was a convention, not a rule.** The only gate was `status != in_force`, so
   flipping the UK announcement's status made it bind. A row whose `instrument_kind` is
   `announced_policy` may now only carry `announced` or `not_in_force`, checked at load, and such a row
   is skipped by the resolver whatever its status says.
4. **Ontario and Quebec over-claimed their bases.** Ontario's row is deliberately stricter than the
   statute (the law allows the resale side's own fees; this table does not) and now says so in a
   `stricter_than_law` field rather than only in prose. Quebec's base reads the announced price as the
   tier face; that equivalence is an assumption of the mapping and is now labelled as one. The
   Ontario commencement's second half (definitions, 1 July 2026) is recorded in the row's notes.

The reviewer's remaining findings are recorded as open in `records/findings/34-region-caps-build.md`
§7 rather than silently dropped: the cluster records' own JSON blocks still carry the pre-correction
shapes (NSW `face_plus_fees`, Florida `absolute`), which is why the table is the authority and the
cluster files are evidence; a ticket-terms condition in the NSW/SA/WA triggers is not representable in
`applies_to` yet; and an absolute-margin rule cannot be enforced by this engine at all, only reported
as unresolved.

## 1. United Kingdom and Ireland — `33-b-region-cap-law-sources/uk-ie.md`

**The United Kingdom has no resale price cap.** What it has is Consumer Rights Act 2015 ss. 90-95, a
disclosure regime: the face value must be disclosed, the seat and the seller must be identified, and
a breach carries a civil penalty of up to GBP 5,000 per breach (s. 93(9)). It applies in England and
Wales, Scotland and Northern Ireland; none of the three nations has a resale price instrument of its
own, and a search of the Scottish Parliament's bill feed found no bill on tickets, touting or resale.

**The announced cap is not law.** On 19 November 2025 the government announced that resale above the
original price plus unavoidable fees would be made illegal, with a cap on resale-platform fees, a
platform duty to monitor, a ban on bulk purchase and CMA penalties up to 10% of global turnover. No
bill, no instrument and no commencement were identified. Class B for the announcement, and the
instrument kind in the table is `announced_policy` so that it can never bind.

**Ireland is the real thing, and it is narrower than it looks.** The Sale of Tickets (Cultural,
Entertainment, Recreational and Sporting Events) Act 2021 s. 15 provides that "a secondary ticket
seller shall not sell a ticket or ticket package for a relevant event for a price exceeding the
original sale price", commenced 31 July 2021. The base is face **plus the fees the first buyer paid**
(s. 2 defines the original sale price to include any additional charge or fee). It applies only to a
"relevant event": an event in a designated venue (s. 7) or a designated event (s. 9), and the
Minister maintains the register under s. 14. Contravention is a criminal offence: class B fine and/or
up to six months summarily for a first offence, up to EUR 100,000 and/or two years on indictment.
Advertising above the original price is a separate offence (s. 15(2)). Charities and amateur sports
clubs are exempt (s. 18).

**Unverified in Ireland:** which venues and events are currently on the s. 14 register (gov.ie
blocked or 404ed on every route tried), and whether s. 15 reaches a platform transacting wholly
outside the State. The engine therefore treats an Irish event as capped **only when the operator
marks it as a declared event**; an undeclared Irish event resolves to monitored and says why.

## 2. Canada — `33-b-region-cap-law-sources/canada.md`

**Two provinces cap, and one of them started in 2026.** Ontario's Ticket Sales Act 2017 gained
s. 2(3) in the Plan to Protect Ontario Act (Budget Measures), 2026, in force 24 April 2026: a
secondary sale may not exceed "the total price paid when the ticket was purchased from the primary
seller, plus any applicable fees, service charges and taxes charged by the secondary seller". Quebec's
Consumer Protection Act s. 236.1 caps resale at "the price announced by the vendor authorized by the
producer", with a written-consent route around it that the platform cannot verify.

**The rest of Canada does not cap.** Federal law is the Competition Act's drip-pricing rule (the
advertised price must be attainable). British Columbia's Ticket Sales Act is a disclosure, refund and
bot-ban regime and its regulator states plainly that it "doesn't regulate ticket prices". Manitoba's
Consumer Protection Act contains no occurrence of "ticket". Nine provinces and territories were not
establishably cleared: their official statute indexes 404ed, served a JavaScript shell, or refused
this host. Those rows say `none_identified`/`unknown`, which resolves to **unresolved**, never to
"unrestricted".

**The 2026 date is the interesting one for the engine:** an event sold before 24 April 2026 and
resold after it is governed by a law that did not exist at issue. Ontario is the test case for the
design's "law changed after sale" rule.

## 3. Australia — `33-b-region-cap-law-sources/australia.md`

**Four state designs, not one national rule, and the brief's NSW premise is wrong.** NSW has no
"Ticket Scalping Act 2018" in force and no ministerial declaration; the operative law is Part 4A of
the Fair Trading Act 1987 (NSW), ss. 58A-58L, in force 1 June 2018, and the trigger is a **resale
restriction in the ticket's own terms** (s. 58B).

**NSW's cap is not a flat 10%.** s. 58G bars selling above the "original acquisition cost", and
s. 58E builds that as the original supply cost plus the transaction cost the first purchaser actually
paid, **with that transaction cost capped at 10% of the original supply cost**. The ceiling is
therefore `face + min(fees paid, 10% × face)`. The advertisement ceiling is a different and looser
number (s. 58F(2): 110% of supply cost), so a sale at 110% of face can breach s. 58G while its own
advertisement complies. Penalties are 1,000/200 penalty units ($110,000/$22,000), and s. 58I puts a
duty on advertising-publication owners, which reaches platforms. This shape is why the engine has a
`face_plus_fees_capped` basis rather than a `pct_above_face` shortcut.

- **SA:** Fair Trading Act 1987 (SA) Part 4A, inserted 2018, a flat 110% of the original supply cost,
  with fees excluded from the base, triggered by a resale restriction in the ticket terms.
- **WA:** Ticket Scalping Act 2021, 110% of a base that **includes** the original booking fee; the
  only jurisdiction read here that expressly reaches conduct outside its borders (s. 6(2)).
- **VIC:** Major Events Act 2009 Part 9A, 110% of face with fees expressly excluded, but only for
  events the Minister declares in the Gazette. No general cap was introduced 2024-2026; the version
  history shows no amendment after 7 September 2022.
- **QLD:** a law exists (Major Sports Facilities Act 2001) and its terms were **not read** — the site
  renders by JavaScript and its authorised PDF is encrypted. The 10% figure is from a parliamentary
  committee report, so the row is `cap_basis: unknown` and resolves to unresolved. A D-grade claim is
  not enforced.
- **TAS, ACT, NT:** nothing located and no regulator statement either way. Unresolved.
- **Commonwealth:** the Australian Consumer Law's Electronic Ticket Resale Service Information
  Standard 2022 is disclosure only, and s. 5 expressly preserves state and territory law, so the
  state caps stack on top of it.

## 4. United States — `33-b-region-cap-law-sources/us.md`

**Federal law does not cap price.** The BOTS Act of 2016 (15 U.S.C. § 45c) prohibits circumventing
ticket-purchase controls and selling tickets obtained that way; the FTC's Rule on Unfair or Deceptive
Fees (16 CFR Part 464, in force 12 May 2025) requires the total price to be disclosed. Neither caps a
resale price.

**Two states have a live price rule, and both are conditional.**

- **Florida** s. 817.36 caps resale at "$1 above the admission price charged therefor by the original
  ticket seller", for four enumerated categories (common-carrier passage; multiday tickets to a park
  or entertainment complex; tickets issued by a 501(c)(3) charity under 3,000 tickets per
  performance; and a fourth category in the text), and a website authorised by the original seller,
  or one that posts the statutory guarantees, escapes it. This is a **margin in money**, not a
  percentage, which is why the table has a `margin_absolute` basis for it and why it resolves to
  unresolved rather than being approximated into lamports.
- **New York** s. 25.29 of the Arts and Cultural Affairs Law bars an operator, or its "agent,
  representative, employee or licensee", from taking any premium above the established price plus
  lawful taxes. It is repealed on 1 July 2027 unless replaced. **Whether an independent reseller is a
  "licensee" is not settled by the sections that were read**, and that is why the row's coverage is
  `unknown` and the engine reports unresolved instead of claiming a cap it cannot place.

**California has no general cap** and deliberately so: Business and Professions Code chapter 21 (AB 8,
2023-24) bars restricting resale and requires transferability at any price. The brief's citation for
it was AB 472, which is a bill about classified school employees. Massachusetts ch. 140 § 185A is a
licensing regime. **Twenty-two of the brief's states were not opened**; their rows say `not checked`,
which is not the same as "no cap" and resolves to unresolved.

## 5. European Union — `33-b-region-cap-law-sources/eu.md`

**No EU instrument caps ticket resale price.** The Digital Services Act (Reg. (EU) 2022/2065), the
Unfair Commercial Practices Directive and the Consumer Rights Directive were read and contain no
ticket-resale price rule; capping price is a member-state matter.

**The member states were not established in this pass, and that is the honest result. None of FR,
IT, ES, BE, PT, DE, NL, PL, SE, DK, AT, CZ, HU or GR has a row in the table**: they resolve to
`unresolved` because no row exists, not because a row says "unknown". The EU-level finding (no EU
instrument caps price) is a statement about the EU's competence, not a rule any event can be sold
under, so it is deliberately not a row either: a code called `EU` would imply an EU-wide rule that
does not exist. The first
attempt read the EU-level instruments and then hit JavaScript shells and bot walls on the national
gazettes: Légifrance returned a Cloudflare challenge, Normattiva serves the article body by
JavaScript, and the Portuguese and Greek gazettes would not render. A retry with PDF and browser
routes was dispatched; **whatever it establishes belongs in a later version of the table.** Until
then, FR, IT, ES, BE, PT, DE, NL, PL, SE, DK, AT, CZ, HU and GR are `unknown` and resolve to
unresolved. France in particular is expected to have a resale-authorisation offence in Code pénal
art. 313-6-2 rather than a price cap, but expected is not read, and it is not in the table.

---

## 6. What this changes in the engine

1. **Three policies, not two.** `capped`, `monitored`, `unresolved`. `monitored` is a positive finding
   that a place does not cap; `unresolved` is the absence of a finding. Collapsing them would make
   every unread jurisdiction read as permission.
2. **The base is part of the law, not a formatting choice.** Ireland and Ontario cap over the all-in
   price the first buyer paid; Victoria and Quebec cap over face with fees excluded; NSW caps over
   face plus the fees actually paid but counts at most 10% of them; Florida's is a margin in dollars.
   The chain holds one base and one cap, so the base is chosen by whichever rule is strictest and the
   event record carries the split.
3. **Announced is a status.** The UK announcement is stored, is visible, and never binds. The same
   field carries a bill at third reading.
4. **Dates are load-bearing.** Ontario from 24 April 2026, Ireland from 31 July 2021, New York until
   1 July 2027. A resolution is always against a date, and the same event can resolve differently on
   either side of one.
5. **Absolute amounts are not approximated.** Florida's $1 margin and any fixed ceiling need an FX
   snapshot with a stated source and time; without one the event is unresolved. A guessed exchange
   rate in a legal ceiling is worse than no ceiling.

## 7. The unknowns, as a register

| # | Unknown | Why it matters | What would settle it |
|---|---|---|---|
| 1 | Which Irish venues and events are on the s. 14 register | the cap applies only to relevant events | the register on gov.ie, or the Minister's designation orders |
| 2 | Whether Ireland's s. 15 reaches a platform wholly outside the State | cross-border sales | the Act's territorial wording plus a court's reading, or the Department's guidance |
| 3 | FR, IT, ES, BE, PT: cap, authorisation rule, or nothing | five EU markets | the retry in flight; national gazette PDFs |
| 4 | Queensland's cap basis, fee treatment and penalties | a state with a real law | a host that can decrypt the PDF, or the Government Gazette |
| 5 | Whether New York's s. 25.29 reaches an independent reseller | the only live US ceiling on the east coast | ss. 25.09-25.25 (the licensing provisions) |
| 6 | 22 US states, 10 Canadian provinces and territories, TAS/ACT/NT, and 13 EU member states | those events resolve to unresolved | one statute per jurisdiction, read |
| 7 | Whether a mid-event tightening binds tickets already sold | the engine can enforce a tightening, but should it? | a legal question for the operator; the design only makes it possible |
| 8 | Whether the platform may be stricter than the law | product policy | the operator's decision; the design supports it and says which rule bound |

## 8. Provenance and how to check this file

- The table: `ticketpath/data/region-caps.json`, version `2026-11-08.1`. Its canonical SHA-256 is
  stamped into every resolved policy and into the harness log, so an enforcement decision can be
  reproduced from the file that made it.
- The resolver: `ticketpath/core/region_caps.py`. 54 unit tests, `tests/test_region_caps.py`; the
  shipped table's own invariants are checked in `tests/test_region_caps_table.py`.
- A row is only added here after a primary source was read. Where the source could not be read, the
  row is `unknown` and this file says which wall stopped it. No row was filled from intuition, and
  the two "expected" findings that were checked and failed (the UK cap is not law; NSW is not a flat
  10%) are recorded as corrections rather than quietly dropped.
- Re-verifying a row means fetching its `url` and reading its `quoted_provision`. If the quote is not
  in the page, the row is wrong and the version must bump.
