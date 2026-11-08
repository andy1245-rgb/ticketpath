# Australia — resale price law by jurisdiction

Cluster: Commonwealth, NSW, VIC, QLD, SA, WA, TAS, ACT, NT.
Status date: 2026-11-08. Descriptive only. Not legal advice.

Purpose: tell a deterministic rules table, per event jurisdiction, whether resale above
face value is restricted and on what base, so the engine can cap or merely monitor.

## Matrix — cap vs ban vs disclosure-only

| Jurisdiction | Kind | Resale price restricted? | Cap basis | Ceiling | Trigger | Platform bound? |
|---|---|---|---|---|---|---|
| AU-NSW | price cap (general) | yes | face + fees actually paid, fees capped at 10% of face | face + min(fees, 10%×face) | ticket carries a **resale restriction** | yes (advertising publication duty) |
| AU-VIC | price cap (declared events) | yes, only declared events | face, fees **excluded** | 1.10 × face | Ministerial **major event ticketing declaration**, gazetted | no (seller only) |
| AU-SA | price cap (general) | yes | face, fees **excluded** | 1.10 × original supply cost | ticket carries a **resale restriction** | yes (advertising publication duty) |
| AU-WA | price cap (general) | yes | face **including** booking fee/commission | 1.10 × original ticket price | ticket carries a **resale restriction** | yes (advertising publication duty) |
| AU-QLD | price cap (designated events) | yes, for major sports facility events and declared major events | original purchase price | +10% over original price | facility/event designation | not settled |
| AU-TAS | none identified | not established | unknown | unknown | unknown | unknown |
| AU-ACT | none identified | not established | unknown | unknown | unknown | unknown |
| AU-NT | none identified | not established | unknown | unknown | unknown | unknown |
| AU-CTH | disclosure only | no price cap | n/a | n/a | resale platform, sole/dominant purpose | yes (the platform is the regulated party) |

Two different designs are in the table and the engine must not conflate them:

- **NSW, SA, WA** cap resale for *any* ticket that carries a resale restriction, on the
  organiser's own ticket terms. No minister, no gazette, no event list. The default for a
  major event is therefore "capped"; the escape is a ticket with no resale restriction.
- **VIC and QLD** cap only events that have been formally designated. The default is
  "uncapped"; the cap switches on per event.

## AU-NSW — Fair Trading Act 1987 (NSW), Part 4A

**The brief's premises are wrong on two points, and both matter to the rules table.**

1. The ticket provisions are **Part 4A, "Regulation of event ticket transactions"
   (ss 58A–58L)**, inserted by the Fair Trading Amendment (Ticket Scalping and Gift Cards)
   Act 2017 and in force 1 June 2018. Part 6A of the same Act is the Consumer, Trader and
   Tenancy Tribunal's jurisdiction over consumer claims and has nothing to do with tickets.
   There is no "Ticket Scalping Act 2018 (NSW)" in force; the 2017 amendment Act is the
   vehicle.
2. There is **no ministerial declaration of a "major event"** in the NSW resale cap. The
   gate is s 58B: the Part applies to "tickets to sporting or entertainment events in New
   South Wales that are subject to a resale restriction", and a resale restriction is a
   term or condition of the ticket that limits or prohibits resale, including one that
   voids or cancels the ticket on resale.

**The cap is not written as "10%".** Two different ceilings exist, on two different bases.

Resale (the offence), s 58G:

> "The first purchaser of a ticket must not sell the ticket to any other person for an
> amount that exceeds the original acquisition cost of the ticket."
> Maximum penalty: 1,000 penalty units (corporation) or 200 penalty units (individual).
> Subsection (2) puts the same ceiling on any later seller who knows or ought reasonably to
> know the acquisition cost.

And s 58E defines the base:

- **original supply cost** = "the amount for which the ticket was sold to the first
  purchaser by an authorised seller" — the face price (s 58E(1)).
- **transaction cost** = "the cost (**not exceeding 10% of the original supply cost**) of any
  commission, booking fee, payment surcharge or ticket delivery fee incurred by the first
  purchaser of the ticket in connection with the purchase of the ticket" (s 58E(3)).
- **original acquisition cost** = original supply cost **plus** transaction cost (s 58E(2)).

So the resale ceiling is **face + the fees the first purchaser actually paid, with that fee
allowance itself capped at 10% of face**. If the first purchaser paid 4% in fees, the
ceiling is 104%, not 110%. This is the point the regulator's plain-English pages blur when
they say "original cost plus transaction costs which are capped at 10%".

Does "original ticket price" include the fees? The Act does not use that phrase. It uses
*supply cost* (face) and *acquisition cost* (face + fees). Booking fees, commission, card
surcharges and delivery fees are named as **transaction costs**, added on top of supply
cost and then capped — so on the text they are not part of the supply cost. The Act does
not say whether a booking fee bundled into the authorised seller's advertised price is
"the amount for which the ticket was sold" or a separate transaction cost; on the
definitional structure it reads as the latter. That is an interpretive point, recorded
below as unsettled.

Advertising, s 58F(2), is a **different base**: a ticket resale advertisement "must not
specify an amount for the sale of the ticket that is more than **110% of the original
supply cost**", and must state the original supply cost and the bay/row/seat (s 58F(3)).
An advertisement at 110% of face therefore satisfies s 58F while a *sale* at 110% of face
can still breach s 58G if the first purchaser paid less than 10% in fees. A listing engine
that prices at the s 58G ceiling is always safe on s 58F; one that prices at the s 58F
ceiling is not always safe on s 58G.

Other provisions:

- s 58H — supply of a ticket cannot be made contingent on buying other goods or services.
- s 58I — the **owner of an advertising publication** (defined to include any website
  carrying public advertisements, and "any person who conducts the business" of it) must
  ensure no prohibited advertisement is published; 1,000/200 penalty units; defences in
  s 58I(2) require contractual prohibition plus prompt removal after notice.
- s 58J — a resale restriction is **void** to the extent it cancels or invalidates a ticket
  resold for not more than 110% of the original supply cost.
- s 58K — bots: using software to circumvent a ticketing website's security measures and
  buy in breach of the site's published terms is an offence, 1,000/200 penalty units.
- s 58L — the Minister may require notification of the number of tickets available for
  general public sale.

Penalties in dollars: NSW Fair Trading states $110,000 for a corporation and $22,000 for an
individual, with on-the-spot fines of $1,100 and $550 — consistent with 1,000 and 200
penalty units at $110 per unit.

Coverage and extraterritoriality: applies to sellers (first purchaser and later sellers)
and to advertising publication owners. The Act contains no provision extending it to
conduct outside New South Wales; the territorial hook is that the *event* is in New South
Wales (s 58B). Whether a platform hosted outside NSW is caught by s 58I is not addressed.

Source read: the Act as in force, consolidated to 20 June 2025, read from the AustLII
consolidation (the official legislation.nsw.gov.au site serves a Cloudflare challenge to
this host and could not be read). The regulator's 2026 pages were read directly and are
consistent.

## AU-VIC — Major Events Act 2009 (Vic), Part 9A

Part 9A, "Major event ticketing" (ss 182A–182O), inserted by the Major Events Legislation
Amendment (Ticket Scalping and Other Matters) Act 2018 (No. 13 of 2018), commenced
1 June 2018 (version 020 in the official version history). A separate, older regime in
Part 9 covers sports events declared under s 152 ("sports ticketing event declaration"),
with its own offences in ss 166A–166G.

Mechanism: the Minister makes a **major event ticketing declaration** under s 182C, after
giving the organiser notice (s 182A) and allowing a 14-day submission, or on the
organiser's request (s 182B); the Minister must consider whether the event is major having
regard to likely attendee numbers; the declaration must be **published in the Government
Gazette** (s 182C(6)); it may apply to one occasion or generally until revoked
(s 182C(5)); revocable under s 182D; VCAT review under s 168. A declaration cannot be made
if a sports ticketing event declaration is in effect for the same event (s 182C(3)).

The cap, s 182F (6 or more tickets):

> "... at a price that exceeds the combined face value price of all those tickets by more
> than 10%."
> Penalty: 60 penalty units (natural person); 300 penalty units (body corporate).

s 182G (5 or less tickets) repeats the 10% ceiling against the same base, penalty 30
penalty units. Both sections also make **advertising or offering for resale** at above the
ceiling an offence, so a listing is caught before a sale (s 182F(2), s 182G(2)). Aggregate
fine for multiple offences on one day at one event is capped at 600 penalty units (natural
person) and 3,000 (body corporate) (s 182F(3)).

Cap basis — this is the key difference from NSW and WA. "face value price" is defined as
"the price of a ticket that is set or agreed to by the sports event organiser or ticketed
event organiser at the time that the ticket is first sold, **excluding** the cost of any
commission, booking fee, administration fee, surcharge or other cost incurred in connection
with the sale or distribution of the ticket". So the 10% is measured on **face alone**, and
the buyer's fees are not part of the base. A ticket with a $100 face and $9 of fees may be
resold at $110, not $119.90.

Also in Part 9A: s 182E requires the organiser to display the face value price on the
ticket where a declaration applies; ss 182GA–182GF regulate ticket packages (register of
authorised package sellers, advertising content, unauthorised package sales, false claims).

Who is bound: "a person who is not authorised to do so by the ticketed event organiser".
Part 9A contains **no advertising-publication duty** — unlike NSW, SA and WA, a resale
platform is not made directly liable by this Part; the offence sits on the seller who sells
or advertises.

Declarations in force now: the 2026 AFL Grand Final (Brisbane Lions v Fremantle, MCG,
26 September 2026) was declared a major event under the Major Events Act 2009 — Victorian
Government media release, 21 September 2026, which also states the 10% ceiling and a
penalty range of $1,018 to $610,530. No consolidated public register of live declarations
was readable; declarations are published one at a time in the Government Gazette.

No general cap was introduced in 2024–2026: the official version history for the Act shows
the current in-force version effective **7 September 2022** and no later version, so the
ticket scalping Part has not been amended since then, and any general cap would have to sit
in this Act.

Source read: the authorised PDF/Word of version 025 (in force), from
content.legislation.vic.gov.au, plus the official version-history page and the Premier's
release.

## AU-SA — Fair Trading Act 1987 (SA), Part 4A

Part 4A, "Regulation of event ticket transactions" (ss 37A–37N), inserted by the **Fair
Trading (Ticket Scalping) Amendment Act 2018 (SA), No. 20 of 2018**, assented 25 October
2018, commencing by proclamation. Schedule 1 of that Act **repealed s 9 of the Major Events
Act 2013 (SA)**, which had been the earlier event-specific scalping provision — so SA moved
from a designated-event model to a general resale-restriction model, the same shape as NSW.

s 37B: applies to "tickets to sporting or entertainment events in this State that are
subject to a resale restriction", defined as a term or condition limiting or prohibiting
resale, including one that cancels or invalidates the ticket on resale.

s 37G: "A person must not sell a ticket to any other person for an amount that exceeds
110% of the original supply cost of the ticket." Maximum penalty: $100,000 (body corporate),
$20,000 (natural person). Expiation fee: $550.

Cap basis: s 37E(1) defines original supply cost as "the amount for which the ticket was
sold to the first purchaser by an authorised seller, **excluding any transaction cost**",
and s 37E(2) defines transaction cost as commission, booking fee, payment surcharge or
delivery fee. The ceiling is therefore a flat **110% of face**, with fees excluded from the
base and no fee allowance added on top. The practical difference from NSW is real: NSW
allows face + actual fees (at most +10%), SA allows face + 10% regardless of what fees were
paid; SA is looser when fees were under 10% and identical at the 10% mark.

Advertising: s 37F — a ticket resale advertisement must not specify more than 110% of the
original supply cost and must state the original supply cost and the bay/row/seat.
s 37I puts the advertising-publication duty on the publication owner, mirroring NSW s 58I.
s 37K voids a resale restriction to the extent it cancels a ticket resold for not more than
110% of original supply cost. s 37L covers bots on ticketing websites. s 37M lets the
Minister require disclosure of ticket numbers. s 37N requires a review of the Part.

s 37E(3)–(4) deal with free tickets: where nothing was paid, the original supply cost is the
organiser's recommended retail price, proved by a certificate signed by the Commissioner.

Commencement date: fixed by proclamation and **not verified** — recorded as unsettled.

Source read: the amending Act as passed (PDF, legislation.sa.gov.au), which carries the
inserted Part in full; and the current Major Events Act 2013 landing page showing the
provision history.

## AU-WA — Ticket Scalping Act 2021 (WA)

Act No. 17 of 2021, assented 9 September 2021. Part 1 commenced on assent, and the rest on
the day after assent (s 2), so the operative provisions run from 10 September 2021.

Definition, s 3: "ticket scalping" means selling a ticket for admission to an event "for an
amount which exceeds the original ticket price by more than 10%".

s 7: "A person must not sell a ticket for admission to an event for an amount which exceeds
the original ticket price by more than 10%." Penalty: a fine of $20,000.

Cap basis — WA is the one jurisdiction whose base **includes** the buyer's fees. "original
ticket price" means "the amount for which the ticket was purchased when first offered for
retail sale by the event organiser or an authorised ticket seller" and "**includes**, if a
booking fee or other commission was payable to an authorised ticket seller in relation to
that sale, the amount of that fee or commission". So the 10% is measured on face **plus the
original booking fee**, and the resale ceiling sits above it.

Coverage, s 6: applies to tickets for admission to events in Western Australia that are
subject to a resale restriction (s 5, same definition shape as NSW and SA), and — uniquely
among the jurisdictions read here — **extends to conduct occurring outside or partly
outside Western Australia** (s 6(2)). That is the clearest extraterritorial hook in the
cluster and the only one that expressly reaches a platform or seller operating interstate.

Advertising, s 10: a ticket resale advertisement must not specify more than 110% of the
original ticket price, and must state the original ticket price and the bay/row/seat.
s 11: the owner of an advertising publication must ensure no prohibited advertisement is
published, $20,000, with the same contractual-plus-removal defence as NSW. s 9: ticket
supply cannot be made contingent on other purchases, $20,000. s 12: bots — using software
to circumvent a ticketing website's security measures, $100,000.

s 8 voids a resale restriction to the extent it cancels a ticket resold at not more than
110% of the original ticket price. s 13 sets out the Commissioner's functions, including
publishing warnings naming persons. s 14 applies parts of the Fair Trading Act 2010 (WA).
s 17 requires a review after five years.

Enforcement: the Commissioner for Consumer Protection (Consumer Protection WA), which
states it can issue infringement notices of $2,000 per offence and that court fines run to
$20,000 for individuals and $100,000 for corporations.

Source read: the authorised PDF of the Act as at 9 September 2021 from
legislation.wa.gov.au, plus the Consumer Protection WA page (last updated 19 November 2024).

## AU-QLD — Major Sports Facilities Act 2001 and Major Events Act 2014

Queensland regulates resale for **designated** events only, through two instruments rather
than one: the Major Sports Facilities Act 2001 (major sports facility events) and the Major
Events Act 2014 (declared major events). Both prohibit resale of tickets for more than 10%
above the original purchase price, and the Major Sports Facilities Act also prohibits
*buying* at more than 10% above the original price; penalty infringement notices are
prescribed under the State Penalties Enforcement Regulation 2014 and a 2025 amendment Bill
increased them.

This is recorded at lower confidence than the four jurisdictions above: the Queensland
legislation site renders its Act text by JavaScript and its authorised PDF is encrypted, so
the Act itself could not be read from this host. The statements above come from a Queensland
Parliament committee report on the amending Bill (2025), which cites s 30A of the Major
Sports Facilities Act and describes both Acts' prohibition as "resale of tickets for more
than 10% of the original purchase price". The Act number is confirmed
(Major Sports Facilities Act 2001, current in-force version at act-2001-084).

Cap basis and the treatment of fees in the Queensland base are **not settled** here.

## AU-TAS, AU-ACT, AU-NT

No price-cap instrument was identified for Tasmania, the Australian Capital Territory or the
Northern Territory within this run, and no primary or regulator source was read that
affirmatively states the position either way. These three are recorded as
`none_identified` with confidence E — absence of an identified instrument, not evidence that
resale is unregulated. Ticket terms, the Australian Consumer Law (misleading conduct) and
the Commonwealth information standard below still apply to a resale platform serving these
jurisdictions.

## AU-CTH — disclosure only, no price cap

The Commonwealth does not cap resale prices. Two things matter to the engine.

**1. The information standard.** The Competition and Consumer (Australian Consumer Law —
Electronic Ticket Resale Service) Information Standard 2022 (F2022L00475), made under the
Competition and Consumer Act 2010 and, in terms, under s 134(1) of the Australian Consumer
Law. Registered 1 April 2022; by s 2 it commenced the day after the end of six months
beginning on the day of registration (i.e. 1 October 2022 on that arithmetic — derived, not
read off a commencement table). It applies to a service that provides information to a
consumer about a secondary-market supply of a ticket to an event in Australia, where the
information is supplied through an electronic platform whose **sole or dominant purpose** is
to facilitate a market in event tickets (s 6(1)).

s 6(2) requires the platform to display continuously, legibly, prominently and
unambiguously:

> "is a ticket resale service. You are not buying from a primary ticket provider."

together with the total price the consumer would reasonably be expected to pay an authorised
seller, excluding any delivery charge. The Act's own worked example: a $108 primary price
including $8 postage means the displayed comparison figure is $100.

s 5 is important for the rules table: the standard "is not intended to exclude or limit the
operation of a law of a State or Territory that is capable of operating concurrently". The
Commonwealth disclosure duty therefore stacks on top of a state cap; it does not displace
it, and a compliant state-capped listing can still breach the standard if the banner or the
price comparison is missing.

**2. The Australian Consumer Law** applies to resale conduct nationally: s 18 (misleading or
deceptive conduct) and s 29 (false or misleading representations), enforced by the ACCC. The
ACCC's own consumer guidance states that authorised sellers' ticket conditions often
restrict "resale or transfer above their original value" and warns about unauthorised
resellers, but states no price cap — consistent with the standard being disclosure-only.
The ACCC's 2020 proceedings against Viagogo are the enforcement precedent for applying the
ACL to a resale platform; no penalty figure is quoted here because it was not verified from
a primary source in this run.

## What could not be settled from a primary source

- **NSW official text.** legislation.nsw.gov.au and every AustLII host served a Cloudflare
  challenge to this machine. The NSW text quoted here is the AustLII consolidation "as at
  20 June 2025"; the regulator's 2026 pages agree with it, but an amendment between June
  2025 and November 2026 would not have been seen.
- **NSW bundled fees.** Whether a booking fee built into the authorised seller's advertised
  price forms part of "original supply cost" or is a separate "transaction cost" is not
  resolved by the text. The engine's safer reading is the one that treats it as a
  transaction cost, which yields the lower ceiling.
- **SA commencement date** (by proclamation) and any SA amendment after the 2018 insertion.
- **Queensland's Act text**, and therefore its exact cap base, fee treatment, penalty
  amounts and which body enforces it.
- **Victoria's live declaration register.** No consolidated list readable; each declaration
  is gazetted separately. The 2026 AFL Grand Final declaration is confirmed; others are not
  enumerated here.
- **Victoria's s 167** (who may commence proceedings) was in the contents but the body text
  was not extracted; enforcement is attributed to Consumer Affairs Victoria from the
  Premier's release rather than the Act.
- **Tasmania, ACT, NT** — no instrument, and no regulator statement either way.
- **Cross-border platform liability** outside WA: NSW, SA and VIC each attach to an event in
  their own territory and none expressly extends to a listing made elsewhere. Only WA does.

```json
[
  {
    "jurisdiction": "AU-NSW",
    "instrument_kind": "primary_legislation",
    "citation": "Fair Trading Act 1987 (NSW) Part 4A (ss 58A-58L), inserted by Fair Trading Amendment (Ticket Scalping and Gift Cards) Act 2017",
    "url": "https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_act/fta1987117",
    "status": "in_force",
    "in_force_from": "2018-06-01",
    "in_force_to": null,
    "applies_to": "all_resale",
    "cap_basis": "face_plus_fees",
    "cap_value": {"kind":"bps","bps":1000},
    "penalty": {"kind":"criminal","summary":"1,000 penalty units corporation / 200 penalty units individual for resale above original acquisition cost, prohibited advertisements and bot use","max":"$110,000 corporation; $22,000 individual; on-the-spot $1,100 / $550"},
    "enforcement_body": "NSW Fair Trading (Department of Customer Service)",
    "quoted_provision": "The first purchaser of a ticket must not sell the ticket to any other person for an amount that exceeds the original acquisition cost of the ticket.",
    "notes": "Cap is not written as 10%: s 58E defines original acquisition cost as original supply cost plus transaction cost, with transaction cost not exceeding 10% of original supply cost, so the ceiling is face + the fees actually paid, capped at +10%. Advertising ceiling is different: s 58F(2) allows up to 110% of original supply cost. Trigger is a resale restriction in the ticket terms (s 58B), not a ministerial declaration. Part 6A of the Act is Tribunal jurisdiction, unrelated. s 58I puts a duty on advertising publication owners (platforms). Text read from AustLII consolidation as at 20 June 2025; official site served a Cloudflare challenge.",
    "confidence": "A",
    "retrieved_at": "2026-11-08T05:55:00Z"
  },
  {
    "jurisdiction": "AU-VIC",
    "instrument_kind": "primary_legislation",
    "citation": "Major Events Act 2009 (Vic) Part 9A (ss 182A-182O), inserted by Major Events Legislation Amendment (Ticket Scalping and Other Matters) Act 2018 (No. 13 of 2018)",
    "url": "https://www.legislation.vic.gov.au/in-force/acts/major-events-act-2009/042",
    "status": "in_force",
    "in_force_from": "2018-06-01",
    "in_force_to": null,
    "applies_to": "designated_events",
    "cap_basis": "face",
    "cap_value": {"kind":"bps","bps":1000},
    "penalty": {"kind":"criminal","summary":"s 182F: 60 penalty units natural person / 300 body corporate for 6+ tickets; s 182G: 30 penalty units for 5 or less; aggregate capped at 600 / 3,000 penalty units per event per day","max":"3,000 penalty units (body corporate) aggregate; government release cites $1,018 to $610,530"},
    "enforcement_body": "Consumer Affairs Victoria",
    "quoted_provision": "at a price that exceeds the combined face value price of all those tickets by more than 10%",
    "notes": "Applies only where the Minister makes a major event ticketing declaration (s 182C), published in the Government Gazette. 'face value price' expressly excludes commission, booking fee, administration fee, surcharge and distribution cost, so the 10% is on face alone. Advertising and offering for resale are separate offences (s 182F(2), s 182G(2)). No advertising-publication duty on platforms in Part 9A. Version history shows no amendment after 7 September 2022, so no general cap was introduced 2024-2026. 2026 AFL Grand Final declared (Premier release 21 September 2026).",
    "confidence": "A",
    "retrieved_at": "2026-11-08T05:52:00Z"
  },
  {
    "jurisdiction": "AU-SA",
    "instrument_kind": "primary_legislation",
    "citation": "Fair Trading Act 1987 (SA) Part 4A (ss 37A-37N), inserted by Fair Trading (Ticket Scalping) Amendment Act 2018 (SA) No. 20 of 2018",
    "url": "https://www.legislation.sa.gov.au/_legislation-documents/lz/v/a/2018/fair-trading-ticket-scalping-amendment-act-2018_20/2018.20.un.pdf",
    "status": "in_force",
    "in_force_from": null,
    "in_force_to": null,
    "applies_to": "all_resale",
    "cap_basis": "face",
    "cap_value": {"kind":"bps","bps":1000},
    "penalty": {"kind":"criminal","summary":"s 37G maximum penalty $100,000 body corporate / $20,000 natural person; expiation fee $550","max":"$100,000"},
    "enforcement_body": "Consumer and Business Services (SA), Commissioner for Consumer Affairs",
    "quoted_provision": "A person must not sell a ticket to any other person for an amount that exceeds 110% of the original supply cost of the ticket.",
    "notes": "s 37B trigger is a resale restriction in the ticket terms, not a ministerial declaration; the 2018 Act also repealed s 9 of the Major Events Act 2013 (SA), moving SA off a designated-event model. s 37E(1) defines original supply cost as the price paid to the authorised seller excluding any transaction cost, so the ceiling is a flat 110% of face with no allowance for the buyer's fees. s 37I puts the duty on advertising publication owners. Commencement was by proclamation; date not verified.",
    "confidence": "A",
    "retrieved_at": "2026-11-08T05:56:00Z"
  },
  {
    "jurisdiction": "AU-WA",
    "instrument_kind": "primary_legislation",
    "citation": "Ticket Scalping Act 2021 (WA) No. 17 of 2021",
    "url": "https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a147313.html",
    "status": "in_force",
    "in_force_from": "2021-09-10",
    "in_force_to": null,
    "applies_to": "all_resale",
    "cap_basis": "face_plus_fees",
    "cap_value": {"kind":"bps","bps":1000},
    "penalty": {"kind":"criminal","summary":"s 7 resale above the ceiling: $20,000. s 11 publication owner: $20,000. s 9 contingent supply: $20,000. s 12 bots: $100,000","max":"$100,000"},
    "enforcement_body": "Commissioner for Consumer Protection (Consumer Protection WA)",
    "quoted_provision": "A person must not sell a ticket for admission to an event for an amount which exceeds the original ticket price by more than 10%.",
    "notes": "Only jurisdiction read here whose base includes the buyer's fees: s 3 defines original ticket price to include any booking fee or other commission payable to an authorised ticket seller. s 6(2) expressly extends the Act to conduct occurring outside Western Australia, the cluster's only extraterritorial hook. s 5 trigger is a resale restriction in the ticket terms. s 10 advertising ceiling 110%; s 11 publication-owner duty. Consumer Protection WA states infringement notices of $2,000 and court fines to $20,000 individual / $100,000 corporation.",
    "confidence": "A",
    "retrieved_at": "2026-11-08T05:56:00Z"
  },
  {
    "jurisdiction": "AU-QLD",
    "instrument_kind": "primary_legislation",
    "citation": "Major Sports Facilities Act 2001 (Qld) and Major Events Act 2014 (Qld)",
    "url": "https://www.legislation.qld.gov.au/view/whole/html/inforce/current/act-2001-084",
    "status": "in_force",
    "in_force_from": null,
    "in_force_to": null,
    "applies_to": "designated_events",
    "cap_basis": "unknown",
    "cap_value": {"kind":"bps","bps":1000},
    "penalty": {"kind":"unknown","summary":"Penalty units increased by a 2025 amending Bill; amounts not read from the Act","max":"unknown"},
    "enforcement_body": "Queensland Office of Fair Trading; Major Sports Facilities Act administered by the Department of Sport, Racing and Olympic and Paralympic Games",
    "quoted_provision": "prohibit resale of tickets for more than 10% of the original purchase price",
    "notes": "Quote is from the Queensland Parliament committee report on the 2025 amending Bill, not from the Act: the Queensland legislation site renders Act text by JavaScript and its authorised PDF is encrypted, so the Act was not read. Report cites s 30A of the Major Sports Facilities Act, and states the Act also prohibits buying above 10%. Cap basis, fee treatment and exact penalties are unsettled; the 1,000 bps figure reflects the reported 10% ceiling, treated as provisional.",
    "confidence": "D",
    "retrieved_at": "2026-11-08T05:59:00Z"
  },
  {
    "jurisdiction": "AU-TAS",
    "instrument_kind": "none_identified",
    "citation": "none identified",
    "url": "https://www.legislation.tas.gov.au/",
    "status": "unknown",
    "in_force_from": null,
    "in_force_to": null,
    "applies_to": "unknown",
    "cap_basis": "unknown",
    "cap_value": null,
    "penalty": {"kind":"unknown","summary":"none identified","max":"unknown"},
    "enforcement_body": "unknown",
    "quoted_provision": "",
    "notes": "No price-cap instrument located and no regulator statement read either way. Recorded as absence of an identified instrument, not as a finding that resale is unregulated. ACL misleading-conduct rules and the Commonwealth information standard still apply.",
    "confidence": "E",
    "retrieved_at": "2026-11-08T06:00:00Z"
  },
  {
    "jurisdiction": "AU-ACT",
    "instrument_kind": "none_identified",
    "citation": "none identified",
    "url": "https://www.legislation.act.gov.au/",
    "status": "unknown",
    "in_force_from": null,
    "in_force_to": null,
    "applies_to": "unknown",
    "cap_basis": "unknown",
    "cap_value": null,
    "penalty": {"kind":"unknown","summary":"none identified","max":"unknown"},
    "enforcement_body": "unknown",
    "quoted_provision": "",
    "notes": "No price-cap instrument located and no regulator statement read either way. Recorded as absence of an identified instrument, not as a finding that resale is unregulated. ACL misleading-conduct rules and the Commonwealth information standard still apply.",
    "confidence": "E",
    "retrieved_at": "2026-11-08T06:00:00Z"
  },
  {
    "jurisdiction": "AU-NT",
    "instrument_kind": "none_identified",
    "citation": "none identified",
    "url": "https://legislation.nt.gov.au/",
    "status": "unknown",
    "in_force_from": null,
    "in_force_to": null,
    "applies_to": "unknown",
    "cap_basis": "unknown",
    "cap_value": null,
    "penalty": {"kind":"unknown","summary":"none identified","max":"unknown"},
    "enforcement_body": "unknown",
    "quoted_provision": "",
    "notes": "No price-cap instrument located and no regulator statement read either way. Recorded as absence of an identified instrument, not as a finding that resale is unregulated. ACL misleading-conduct rules and the Commonwealth information standard still apply.",
    "confidence": "E",
    "retrieved_at": "2026-11-08T06:00:00Z"
  },
  {
    "jurisdiction": "AU-CTH",
    "instrument_kind": "secondary_legislation",
    "citation": "Competition and Consumer (Australian Consumer Law - Electronic Ticket Resale Service) Information Standard 2022 (Cth), F2022L00475, made under the Competition and Consumer Act 2010 (ACL s 134(1))",
    "url": "https://www.legislation.gov.au/F2022L00475/latest/text",
    "status": "in_force",
    "in_force_from": "2022-10-01",
    "in_force_to": null,
    "applies_to": "disclosure_only",
    "cap_basis": "no_price_cap",
    "cap_value": null,
    "penalty": {"kind":"civil","summary":"Breach of an information standard under the ACL attracts ACCC enforcement; ACL s 18 and s 29 misleading-conduct prohibitions apply to resale platforms","max":"unknown"},
    "enforcement_body": "Australian Competition and Consumer Commission",
    "quoted_provision": "is a ticket resale service. You are not buying from a primary ticket provider.",
    "notes": "Disclosure only, no price cap. Applies to an electronic platform whose sole or dominant purpose is to facilitate a market in event tickets (s 6(1)); s 6(2) requires continuous display of the resale-service statement and the total price a consumer would pay an authorised seller, excluding delivery. s 5 provides the standard does not exclude or limit concurrent State or Territory law, so state caps stack on top. Commencement date derived from s 2 plus registration on 1 April 2022, not read off a commencement table.",
    "confidence": "A",
    "retrieved_at": "2026-11-08T05:58:00Z"
  }
]
```
