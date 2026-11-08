# United States, federal and states: ticket resale price rules, legal-basis research

Cluster: United States (federal and state). Retrieved 2026-11-08. Descriptive only. This is a
research record, not legal advice.

Five jurisdictions are read at first hand: the two federal instruments, New York, California,
Florida, Massachusetts. Everything else in the brief's list is marked **not checked**. That is
deliberate. A sourced answer for five beats a guessed answer for twenty-seven, and an unread
state must never enter the rules table as "no cap".

## What this run could and could not reach

Recorded first, because it decides which rows are evidence.

Worked:

- `govinfo.gov` full text of Public Law 114-274 (BOTS Act) read in full.
- `ecfr.gov` full text of 16 CFR Part 464 (Rule on Unfair or Deceptive Fees) and 16 CFR 1.98
  (civil penalty amounts) read in full, current as of 2026-11-05.
- `leginfo.legislature.ca.gov` bill text: AB 8 (2023-24) carrying Business and Professions Code
  chapter 21 (§§ 22500 to 22514), and AB 472 (2023-24).
- `nysenate.gov` (OpenLegislation): Arts and Cultural Affairs Law §§ 25.03, 25.05, 25.07, 25.27,
  25.29, 25.35 read in full.
- `leg.state.fl.us`: Florida Statutes 817.36 (2026 edition) read in full.
- `malegislature.gov`: Massachusetts General Laws ch. 140 § 185A read in full.
- `leg.colorado.gov`: reachable, bill pages and bill search both responded.

Blocked, and how:

- `nysenate.gov` and `leginfo.legislature.ca.gov` both return a Cloudflare interstitial to a plain
  fetch ("Just a moment...", 403). Both were reached through a text-extraction reader proxy and
  the statute text came back intact; the content is the official page's text, the transport was
  a proxy. `nysenate.gov` only responded on the bare hostname, not on `www`.
- `public.leginfo.state.ny.us` (the older NY law gateway) timed out repeatedly.
- No headless browser was available on this host, so nothing that needs JavaScript rendering was
  read.
- The web-search tool returned `VERDICT: degraded` on every query (ddg_lite blocked, bing
  failed) and long queries collapsed to a single keyword. Every source above was found by direct
  URL construction, not by search.
- Colorado: three full-text searches of the General Assembly bill search (`ticket resale`,
  `ticketing`, `tickets`) returned no ticket-related bill. That is a search-result fact, not proof
  of absence, and Colorado is recorded as UNVERIFIED.

Four attempts were spent on the wrong Colorado bill number before the search route was abandoned;
the brief's "Colorado 2025 ticket law" was never located, so nothing about it is asserted.

## Matrix

`cap in force?` is the engine's question. `unknown` means the instrument was not read; it does not
mean "no cap". `not checked` means the state was not opened at all.

| state | cap in force? | basis | coverage | status |
|---|---|---|---|---|
| US-FED | No. No price cap in the BOTS Act | no_price_cap | bots_only | in force, read (A) |
| US-FED (FTC) | No. Disclosure of total price only | no_price_cap | disclosure_only | in force 2025-05-12, read (A) |
| NY | Yes, on the operator side: no premium above established price plus lawful taxes. Whether it reaches an independent reseller is not settled by the text read | face | unknown (binds operator, its agents and licensees) | in force, repealed 2027-07-01, read (A) |
| CA | No price cap. Chapter 21 bars restricting resale and requires transferability "at any price"; Penal Code 346 bars above-face selling only on venue grounds without the owner's written permission | no_price_cap | all_resale | in force, read (A) |
| FL | Yes, but conditional: $1 over the original ticket seller's price, escaped by a website that is authorised by the original seller or posts the statutory guarantees and disclosures | absolute ($1 over original price) | designated_events (four enumerated categories) | in force, read (A) |
| MA | No price cap in ch. 140 § 185A. Licensing requirement on resellers and on anyone facilitating resale | no_price_cap | all_resale | in force, read (A), single section only |
| CO | Unknown | unknown | unknown | UNVERIFIED (not located) |
| AR | Unknown | unknown | unknown | not checked |
| CT | Unknown | unknown | unknown | not checked |
| KY | Unknown | unknown | unknown | not checked |
| LA | Unknown | unknown | unknown | not checked |
| MI | Unknown | unknown | unknown | not checked |
| MN | Unknown | unknown | unknown | not checked |
| MS | Unknown | unknown | unknown | not checked |
| MO | Unknown | unknown | unknown | not checked |
| NJ | Unknown | unknown | unknown | not checked |
| PA | Unknown | unknown | unknown | not checked |
| RI | Unknown | unknown | unknown | not checked |
| TN | Unknown | unknown | unknown | not checked |
| WI | Unknown | unknown | unknown | not checked |
| IL | Unknown | unknown | unknown | not checked |
| MD | Unknown | unknown | unknown | not checked |
| VA | Unknown | unknown | unknown | not checked |
| GA | Unknown | unknown | unknown | not checked |
| TX | Unknown | unknown | unknown | not checked |
| WA | Unknown | unknown | unknown | not checked |
| OR | Unknown | unknown | unknown | not checked |
| AZ | Unknown | unknown | unknown | not checked |
| NV | Unknown | unknown | unknown | not checked |

Do not populate a rules table past the five read rows. Twenty-two of the brief's states were not
opened, and Colorado was searched but not found.

---

## 1. Federal

### 1.1 BOTS Act of 2016 (Public Law 114-274, 15 U.S.C. § 45c)

Read in full from govinfo. Approved 14 December 2016, no sunset.

**What it prohibits.** Two things only, and neither is a price:

1. Circumventing "a security measure, access control system, or other technological control or
   measure on an Internet website or online service that is used by the ticket issuer to enforce
   posted event ticket purchasing limits or to maintain the integrity of posted online ticket
   purchasing order rules" (§ 2(a)(1)(A)).
2. Selling or offering to sell, in interstate commerce, an event ticket obtained in violation of
   (1), where the seller "participated directly in or had the ability to control" the circumvention,
   or "knew or should have known" the ticket was so acquired (§ 2(a)(1)(B)).

There is an express research and enforcement exception (§ 2(a)(2)): creating or using software to
investigate a suspected violation, or to do security research on the control measures.

**Confirmed: no price cap.** The Act contains no reference to price, face value, markup or resale
price at all. Its operative verbs are circumvent and sell. A ticket bought at face value by a bot
and resold at cost is still caught if the acquisition was a violation; a ticket bought lawfully can
be resold at any price without offending this Act.

**Scope.** "Event" is defined in § 3(2) as "any concert, theatrical performance, sporting event,
show, or similarly scheduled activity, taking place in a venue with a seating or attendance capacity
exceeding 200 persons" and open to the general public, promoted or with tickets sold in interstate
commerce. So a venue of 200 or fewer is outside it.

**Penalty.** § 2(b) treats a violation as a violation of a rule defining an unfair or deceptive act
or practice under § 18(a)(1)(B) of the FTC Act (15 U.S.C. § 57a(a)(1)(B)). The consequence is the
FTC Act civil penalty in 15 U.S.C. § 45(m)(1)(A). The current adjusted maximum, from 16 CFR 1.98(d)
as displayed in the eCFR current on 2026-11-05, is **$53,088 per violation** for penalties assessed
after 17 January 2025. Note the limit of that claim: the eCFR text read carries the 17 January 2025
adjustment and shows no later amendment, so an inflation adjustment taking effect in January 2026
was not observed in the text read. Treat $53,088 as the figure in the current eCFR, not as a
certified 2026 figure.

**Enforcement.** FTC (§ 2(b)), and state attorneys general as parens patriae for their residents
(§ 2(c)), with a 10-day pre-suit notice to the FTC and an FTC right to intervene. The FTC Act's
own rule is that a state AG action is barred while an FTC action on the same violation is pending
(§ 2(c)(4)).

### 1.2 FTC Rule on Unfair or Deceptive Fees, 16 CFR Part 464

Read in full from the eCFR, which is current as of 2026-11-05 and shows the part with a source note
of 90 FR 2166 (10 January 2025) and a 12 May 2025 change date. **In force.**

**Status, stated precisely.** This is the live-event ticket fee rule, and it is narrower than the
2023 proposal: the final part covers only two "covered goods or services", defined in § 464.1 as
"(1) Live-event tickets; or (2) Short-term lodging". The proposed rule's wider scope over other
industries did not survive into the final text. It has not been rescinded in the eCFR text read.

**What it requires.** § 464.2(a): "It is an unfair and deceptive practice and a violation of this
part for any business to offer, display, or advertise any price of a covered good or service without
clearly and conspicuously disclosing the total price." § 464.2(b) requires the total price to be
more prominent than any other pricing information; § 464.2(c) requires disclosure, before consent to
pay, of the nature, purpose and amount of any excluded fee and of the final amount of payment.
§ 464.3 prohibits misrepresenting any fee. "Total price" in § 464.1 excludes government charges,
shipping charges and optional ancillary goods or services, so those may be left out of the headline
figure if they are then disclosed.

**Is it a cap? No.** It governs what must be displayed and when, not what may be charged. Nothing in
§§ 464.1 to 464.5 sets a maximum price, a maximum markup, or a relationship to face value.

**Relation to state law.** § 464.4(a) does not supersede state law except to the extent of
inconsistency; § 464.4(b) says a state law is not inconsistent if it gives greater consumer
protection. So a state disclosure rule can sit on top, and a state price cap is untouched.

**Who it binds.** Any "business" offering a covered good or service, defined in § 464.1 as "an
individual, corporation, partnership, association, or any other entity that offers goods or services,
including, but not limited to, online, in mobile applications, and in physical locations". Both a
primary seller and a resale marketplace are businesses offering live-event tickets.

### 1.3 Federal: what is not claimed

No federal price cap on ticket resale was located. A "TICKET Act" and other federal ticketing bills
were not researched in this run, so nothing is asserted about their status. Do not read the absence
of a cap here as a statement that no federal bill exists.

---

## 2. New York

Read: Arts and Cultural Affairs Law §§ 25.03, 25.05, 25.07, 25.27, 25.29, 25.35. Sections
25.09 to 25.25 (licensing, bonds, applications) were **not** read.

### 2.1 § 25.29, Unlawful charges in connection with tickets: the price ceiling that is in force

This is the finding that matters and it is not the section most summaries cite.

"No operator of any place of entertainment, or his or her agent, representative, employee or
licensee shall, if a price be charged for admission thereto, exact, demand, accept or receive,
directly or indirectly, any premium or price in excess of the established price plus lawful taxes".

Three carve-outs in the same subdivision: a reasonable service charge for special services (sales
away from the box office, credit card sales, delivery); initial sale by auction; and, in
subdivision 2, an actual cost for physical delivery, with no delivery fee permitted for tickets
delivered electronically or printable by the purchaser. Subdivision 3 gives the Attorney General
concurrent jurisdiction with district attorneys.

- **Cap basis:** face, that is the "established price" as defined in § 25.03(2) (the price fixed at
  the time of sale by the operator, printed on the ticket), plus lawful taxes. Fees are not in the
  base; a service charge is allowed only for "special services".
- **Who is bound:** the operator of the place of entertainment, and its agent, representative,
  employee or licensee. Not, on the face of the words, an independent unlicensed reseller.
- **The open question, stated as open:** whether a reseller licensed under article 25 is a
  "licensee" within § 25.29(1) is not resolvable from the sections read, because the licensing
  provisions that would define it were not read. This is why `applies_to` is `unknown` in the JSON
  rather than `all_resale`. Reading §§ 25.09 to 25.25 would settle it.
- **Penalty:** § 25.35 makes a violation of § 25.27 or § 25.29 a class A misdemeanour, punishable by
  a fine not exceeding $1,000 or two times the defendant's gain, and it applies to a person "whether
  or not domiciled, licensed or registered within the state".
- **Sunset:** § 25.29 carries the note "NB Repealed July 1, 2027". In force now, gone on that date
  unless replaced.

### 2.2 § 25.27: a rewrite already enacted, not yet in force

The consolidated text shows two versions of § 25.27:

- Currently in force "until July 1, 2027": *Commissions to employees of places of entertainment*,
  barring commissions, gratuities or bonuses to venue officers or employees.
- Effective 1 July 2027: *Unlawful charges in connection with theatre tickets*, which is a
  re-enacted and widened version of the price ceiling. It reaches any owner, operating lessee,
  operator, manager, treasurer or assistant treasurer of a theatre, stadium, arena, garden or other
  place of amusement who takes "any premium or price in excess of the regular or established price
  or charge, plus lawful taxes, as printed upon the face of each ticket", and by subdivision 2 it
  "shall also apply to the sale of theatre tickets and tickets for sporting events to persons
  licensed to resell". Penalty in its own text: fine up to $500, or up to one year, or both.

So the direction of travel is a price ceiling that explicitly reaches licensed resellers from
1 July 2027. The engine should carry that as a dated future rule, not as current law. Both the
2027 § 25.27 and the repeal of § 25.29 take effect the same day, which reads like a consolidation
of the two into one section; the text read does not say so in terms.

### 2.3 § 25.07, Ticket prices: disclosure and refunds, no cap

In force, with the note "Effective until July 1, 2027".

- Subdivision 1: the operator must print the established price, or the final auction price if sold
  or resold by auction through the operator or its agent, on the face of each ticket.
- Subdivision 2: anyone who "resells tickets or facilitates the resale or resale auction of tickets
  between independent parties by any means", "regardless of whether or not licensed under this
  article", must guarantee a full refund of the amount paid including all fees if the event is
  cancelled, if the ticket does not grant admission, or if the ticket does not conform to its
  description.
- Subdivision 4: operators, licensees, resellers and platforms "shall disclose the total cost of the
  ticket, inclusive of all ancillary fees that must be paid in order to purchase the ticket", with
  the dollar portion that is a service charge or surcharge shown, displayed in the listing before
  the ticket is selected, not presented more prominently than the total, and with no increase during
  the purchase process other than a disclosed delivery fee.
- **No price cap in this section.** A different § 25.07 text (*Bond*, $1,000 penal sum) is noted as
  effective 1 July 2027, an oddity of the amendment schedule worth flagging: the section number is
  scheduled to change subject entirely.

### 2.4 § 25.05, Ticket speculators

Street and sidewalk selling of tickets in a city or in Nassau County, and soliciting passers-by to
buy, is a misdemeanour. Effective 1 July 2027 per the note on the section. This is a place-of-sale
rule, not a price rule.

**NY summary for the engine:** a face-value ceiling does exist in current law (§ 25.29) but it is
addressed to the operator side and its reach over an independent reseller is unresolved; it sunsets
1 July 2027; a wider version expressly covering licensed resellers of theatre and sporting tickets
takes effect that same day. NY is therefore `monitor` plus a dated flag, not `cap`.

---

## 3. California

Read: Business and Professions Code chapter 21 (§§ 22500 to 22514) as carried in AB 8 (2023-24),
and Penal Code § 346.

### 3.1 The brief's bill number is wrong, and this matters

The brief names "California's 2024 AB 472 (ticket fees/transferability)". **AB 472 in the 2023-24
session is not a ticket bill.** It was read: chapter 331, an act amending Education Code §§ 45190
and 88190 on classified school district and community college employees' compulsory leaves of
absence, approved 7 October 2023. No ticket, fee or transferability provision appears in it.

The ticket fee and transferability law of that period is **AB 8 (2023-24)**, which carries Business
and Professions Code chapter 21, "Ticket Sellers". Anyone building a rules table from the brief's
bill number would fetch the wrong act. Flagged, not silently corrected.

### 3.2 Business and Professions Code chapter 21: what it does

Version read is the file leginfo labels "AMENDED" (the 2023 bill text in the Assembly), not the
chaptered act. Section numbers and text match the operative code sections, but the chaptered version
was not re-read, so the enactment date is left null in the JSON rather than guessed.

- **No price cap, and the opposite is written in.** § 22506(a)(1): a primary contractor shall not
  "restrict by any means the resale of tickets, including tickets in a subscription or season ticket
  package". § 22506(a)(2): no denying entry to a holder of a resold ticket solely because it was
  resold. § 22506(a)(3)(A): a paperless ticketing system may not be used "unless the purchaser is
  given an option to purchase paperless tickets that the purchaser can transfer at any price, and at
  any time, and without additional fees, independent of the primary contractor". § 22506(a)(4): no
  charging a different price based on the form or transferability of the ticket. California law
  therefore affirmatively protects above-face resale and independent transfer.
- **Total price disclosure.** § 22504, as amended by AB 8, bars advertising, displaying or offering
  a ticket without including all fees that must be paid, other than government taxes; the total must
  be shown before selection and must not increase afterwards except a disclosed, reasonable delivery
  fee.
- **Speculative selling.** § 22501 bars taking money without having the ticket, a written contract
  to get it at a stated price, or the statutory disclosure; § 22502 bars promising a price or range
  and failing to deliver at or below it; § 22508 caps a non-refundable service charge on a deposit
  at 10 percent.
- **Free tickets.** § 22507: it is unlawful to resell a ticket "if the ticket was initially offered
  to the public at no charge and access to that ticket is not contingent upon providing a form of
  monetary consideration". This is the one provision in the chapter that reads as a price rule, and
  it is a ban on resale of free tickets, not a markup limit.
- **Bots.** § 22505 mirrors the federal BOTS Act and adds a resale limb, and it applies
  notwithstanding the § 22500(b) exemptions for small sellers, carriers and charities.
- **Penalty.** § 22513: "A violation of this chapter shall constitute a misdemeanor." § 22511 adds a
  specific misdemeanour for the business-address requirement, up to six months or a $2,500 fine or
  both, and a civil penalty up to $2,500 per violation, each ticket being a separate violation,
  brought by the AG, a district attorney, or a city attorney of a city over 750,000. § 22512 gives a
  private right to twice the contracted price where a seller fails to supply at the contracted
  price.
- **Exemptions.** § 22500(b): carrier agents selling with a tour package; a person selling six
  tickets or fewer to one event off the venue premises; a tax-exempt nonprofit selling its own event.

### 3.3 Penal Code § 346

Read in full. Added by Stats. 1972, ch. 529. It makes it a misdemeanour to sell, without the written
permission of the owner or operator of the property, a ticket obtained for resale "at any price which
is in excess of the price that is printed or endorsed upon the ticket, while on the grounds of or in
the stadium, arena, theater, or other place where an event ... is to be held or is being held".

- **Basis:** face, as printed or endorsed.
- **Coverage:** a physical-location offence only. It bites on the venue grounds or in the venue. It
  does not reach an online resale made from elsewhere, and it yields to the owner's written
  permission.
- **Penalty:** misdemeanour; the section states none beyond that.

**CA summary for the engine:** no cap. Chapter 21 is a disclosure, anti-speculation, anti-bot and
transferability regime that expressly protects resale at any price. Penal Code 346 is a venue-grounds
prohibition that an online marketplace does not trigger, but a will-call or box-office collection
point on venue property is a different matter and should be treated as a venue-grounds risk.

---

## 4. Florida: the one state read that has a real, live price cap

Florida Statutes § 817.36, "Resale of tickets", read in full from the 2026 edition. History line ends
at ch. 2010-5, s. 123, so the version read is current and unamended since 2010.

**The cap.** § 817.36(1): "A person or entity that offers for resale or resells any ticket may charge
only $1 above the admission price charged therefor by the original ticket seller of the ticket for
the following transactions". Four categories:

- (a) passage or accommodations on a common carrier in the state, with a carve-out for licensed
  travel agencies;
- (b) multiday or multievent tickets to a park or entertainment complex, or to a concert,
  entertainment event, permanent exhibition or recreational activity inside such a park or complex,
  including an entertainment/resort complex as defined in § 561.01(18);
- (c) event tickets originally issued by a § 501(c)(3) charity, where no more than 3,000 tickets are
  issued per performance, and only if the ticket carries the statutory notice;
- (d) any other tickets resold or offered "through an Internet website, unless such website is
  authorized by the original ticket seller or makes and posts the following guarantees and
  disclosures".

**The escape hatch, which is the whole story for a marketplace.** Category (d) is the residual
category, so ordinary single-event concert and sports tickets resold online fall inside the $1 rule
unless the website either is authorised by the original ticket seller or posts, visibly and before
the transaction completes: a full refund guarantee (including fees, where fees were not disclosed)
for cancellation, denial of admission, or non-delivery; and a disclosure that the operator is not
the issuer, original seller or reseller and does not control pricing, "which may be resold for more
than their original value". A compliant marketplace therefore lifts the cap for category (d)
tickets. A non-compliant one is capped at $1 over the original seller's price.

**Base.** The "admission price charged therefor by the original ticket seller", not face value on the
ticket and not face plus fees. The $1 is a fixed dollar amount, so in the schema it is
`absolute`/`minor_units` 100.

**Territorial reach.** The section is not expressly limited to events in Florida. Paragraph (a) is
limited to common carriers "in this state"; (b) to parks or complexes (the definition is
place-based); (c) to any qualifying charity's tickets; (d) is not expressly limited at all. So for
(d) the text does not answer the cross-border question, which is a live gap for a platform selling
Florida-located events to out-of-state buyers or reselling out-of-state events to Florida residents.

**Other provisions.** § 817.36(2) does not authorise selling at any price on property where an event
is held without the property owner's prior express written consent (the venue-grounds rule). § 817.36(5)
is a separate bots provision: intentionally using or selling software to circumvent a ticket seller's
security or access control attracts a civil penalty of treble the amount for which the tickets were
sold.

**Penalty.** § 817.36(4): a person who knowingly resells in violation is "liable to the state for a
civil penalty equal to treble the amount of the price for which the ticket or tickets were resold".
Civil, payable to the state, not to the buyer.

**FL summary for the engine:** this is the one jurisdiction read where the answer is genuinely
`cap`, but the cap is conditional on channel conduct. Model it as: default $1 over the original
seller's price for the four categories, with a compliance flag that, when the (d) guarantees and
disclosures are posted, switches the rule to monitor.

---

## 5. Massachusetts

Read: General Laws ch. 140 § 185A only. Sections 181 to 185G were not read, so this is a single-section
result, not a chapter conclusion.

**No price term in § 185A.** It is a licensing section. Subsection (a) requires a licence from the
commissioner of occupational licensure for anyone who engages in "the business of selling tickets or
the business of reselling or facilitating a mechanism for 2 or more parties to participate in the
resale of any ticket of admission to any theatrical exhibition, public show or public amusement or
exhibition", whether on or off the premises. Subsection (b) covers the application, the term (until
1 January next after issue) and non-transferability without written permission, and deems a ticket
sold at nothing or below the public price to be a resale.

**Why the wording matters for a marketplace.** "Facilitating a mechanism for 2 or more parties to
participate in the resale" is the widest platform-capture formula found in this run, wider than
California's "platform operator" and wider than New York's "facilitates the resale". On this text a
resale marketplace serving Massachusetts events needs a licence, and the obligation attaches to the
facilitator, not only the seller.

**Cap:** none found in this section. **Penalty for unlicensed activity:** not stated in § 185A, so
recorded as unknown rather than guessed.

---

## 6. Coverage and who is bound: the cross-border question

The brief asks whether a platform transacting a resale across state lines falls in. What the read
instruments actually say:

- **Federal, 16 CFR 464:** binds any "business ... that offers goods or services", with no
  territorial limitation in the text read. A platform displaying a total price to a US consumer is
  in, whoever and wherever it is.
- **Federal, BOTS Act:** requires the ticket to be sold "in interstate commerce", and defines an
  event by reference to a venue over 200 persons whose tickets are sold in interstate commerce. That
  is a broad hook, but it goes to bot-acquired tickets only.
- **California:** "platform operator" is defined as a person or organisation "responsible for
  operating a marketplace that enables consumers to purchase, sell, or resell tickets"
  (§ 22500(a)(2)), and "ticket seller" expressly includes a platform operator (§ 22500(a)(4)). No
  territorial clause in the chapter was read. So the text captures the platform by role and is
  silent on where the platform or the buyer sits.
- **New York:** § 25.07(2) reaches anyone who "resells tickets or facilitates the resale ... between
  independent parties by any means", "regardless of whether or not licensed under this article", and
  § 25.35 extends the criminal penalties to a person "whether or not domiciled, licensed or
  registered within the state". That is the clearest extraterritorial wording in the run, but it
  attaches to conduct, not to a stated territorial test.
- **Florida:** § 817.36(1)(d) has no express territorial limit; paragraphs (a) and (b) are
  place-based by their subject matter. The statute does not say which law governs a Florida-platform
  sale of a Georgia event.
- **Massachusetts:** the licence requirement is framed by subject matter (theatrical exhibition,
  public show, public amusement) and by conduct on or off the premises. No territorial test read.

**Net position, stated as a gap and not as a rule:** no instrument read in this run contains a
territorial connecting factor for a cross-border resale. The engine must not assume that the venue
state governs. For a tour selling to buyers in several states through one marketplace there are at
least three candidate attachments (venue location, buyer residence, platform establishment) and no
instrument read chooses between them. This is the largest unresolved legal question in this cluster
and it is unresolved for a documentary reason, not because the answer is "no rule".

## 7. Dates

| instrument | in force | ends | note |
|---|---|---|---|
| BOTS Act, PL 114-274 | 2016-12-14 | none | no sunset, no amendment found |
| 16 CFR Part 464 | 2025-05-12 | none | 90 FR 2166 (2025-01-10); eCFR current 2026-11-05 shows it in force |
| 16 CFR 1.98 penalties | 2025-01-17 | next adjustment | $53,088 for § 45(m)(1)(A)/(B); no 2026 adjustment observed in the text read |
| CA Penal Code 346 | 1972 | none | Stats. 1972, ch. 529 |
| CA B&P ch. 21 (AB 8) | in force | none | version read was the amended bill text, not the chaptered act; enactment date not verified |
| FL Stat. 817.36 | in force | none | unamended since ch. 2010-5 |
| MA G.L. c. 140 § 185A | in force | none | single section read |
| NY ACA 25.29 | in force | 2027-07-01 (repealed) | replaces into 25.27 |
| NY ACA 25.27 (unlawful charges) | 2027-07-01 | none | enacted, not yet in force |
| NY ACA 25.07 (ticket prices) | in force | 2027-07-01 | § 25.07 becomes "Bond" on that date |

**Bills in progress:** none identified. No state legislature was searched for pending bills in this
run, so this is "none identified", not "none exists".

## 8. Unknowns: exactly what a primary source could not settle

1. **Twenty-two states not opened at all:** AR, CT, KY, LA, MI, MN, MS, MO, NJ, PA, RI, TN, WI, IL,
   MD, VA, GA, TX, WA, OR, AZ, NV. For every one of them the cap question, the cap basis, coverage,
   penalty and dates are unanswered. Their rows are `unknown`/`E`, not "no cap".
2. **Colorado.** The 2025 ticket law the brief describes (fee transparency, transferability, whether
   it caps price) was not located. Three General Assembly bill-search queries returned no
   ticket-related bill, which is a search-index result and not evidence of absence. What would
   settle it: the bill number, resolved through `leg.colorado.gov/bills` by title, or the Colorado
   Revised Statutes consumer-protection article in which the enacted section sits. No fee,
   transferability or cap claim is made.
3. **New York, whether § 25.29 binds an independent reseller.** Requires reading ACA §§ 25.09 to
   25.25 to see how "licensee" is defined and who must be licensed. Until then the NY row is a cap
   that exists but whose reach is unsettled.
4. **New York, what article 25 looks like after 1 July 2027.** The consolidated text shows § 25.29
   repealed, § 25.27 replaced and § 25.07 turned into a bond section on that one date. The
   amending bill and its purpose were not read, so the post-2027 shape of the article is inferred
   from effective-date notes only.
5. **California, whether the chaptered AB 8 differs from the amended text read**, and its operative
   date. The chaptered act was not fetched.
6. **California, whether any local ordinance caps resale.** § 22500(c) preserves local fees and
   taxes; city-level ticket rules were not checked. San Francisco and Los Angeles were not opened.
7. **Massachusetts beyond § 185A.** Whether a cap or a service-charge limit sits in ch. 140
   §§ 181-185G, or in the regulations of the Division of Occupational Licensure, was not checked.
8. **Florida, the cross-border question under § 817.36(1)(d)**, and whether "authorized by the
   original ticket seller" has been interpreted to cover a marketplace with a primary-seller
   integration. No case law read.
9. **Federal 2026 penalty figure.** Only the 17 January 2025 adjustment was read. A 2026 adjustment,
   if one was published, was not observed.
10. **Any federal ticketing bill.** Not researched; nothing asserted.
11. **Every state's penalty and enforcement body**, for any state not in section 5 above.
12. **Whether any of these provisions has been held unconstitutional or narrowed.** No case law was
    read for any jurisdiction. That is a standing caveat on every row: a statute read as written is
    not a statute as enforced.

### Exact next fetches, in priority order

- CO: `leg.colorado.gov/bills` by title, or the Colorado Revised Statutes title 6 consumer article;
  a working search index would shorten this to one query.
- NY: `nysenate.gov/legislation/laws/ACA/25.09` through `25.25` for the licensing definition of
  "licensee", then the amending bill behind the 2027-07-01 notes.
- CA: the chaptered AB 8 text (`leginfo.legislature.ca.gov` bill id `202320240AB8`, chaptered
  version) for the operative date.
- MA: `malegislature.gov` ch. 140 §§ 181 to 185G, and the Division of Occupational Licensure
  regulations for any service-charge limit.
- FL: `leg.state.fl.us` for any 2025 or 2026 amendment after ch. 2010-5, and Florida case law on
  § 817.36(1)(d).
- Then, in order of market size: TX, IL, WA, NJ, PA, TN, GA, VA, MD. For each, the state statute
  house bill-search or the codified commercial-practices article, read for a price term.

---

```json
[
  {"jurisdiction":"US-FED:BOTS","instrument_kind":"primary_legislation","citation":"Better Online Ticket Sales Act of 2016, Pub. L. 114-274, 130 Stat. 1401, codified at 15 U.S.C. § 45c","url":"https://www.govinfo.gov/content/pkg/PLAW-114publ274/html/PLAW-114publ274.htm","status":"in_force","in_force_from":"2016-12-14","in_force_to":null,"applies_to":"bots_only","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"civil","summary":"A violation is treated as a violation of an FTC trade regulation rule; FTC or a state attorney general may sue; civil penalty per violation under 15 U.S.C. § 45(m)(1)(A).","max":"$53,088 per violation (16 CFR 1.98(d), penalties assessed after 2025-01-17)"},"enforcement_body":"Federal Trade Commission; state attorneys general as parens patriae (10-day pre-suit notice to the FTC; FTC may intervene)","quoted_provision":"circumvent a security measure, access control system, or other technological control or measure on an Internet website or online service that is used by the ticket issuer to enforce posted event ticket purchasing limits","notes":"Read in full from govinfo. Two prohibitions only: circumventing ticket-issuer access controls, and selling or offering a ticket obtained in violation where the seller participated in, controlled, knew of or should have known of the circumvention. Research and enforcement use of circumvention software is excepted (§ 2(a)(2)). 'Event' means a venue with seating or attendance capacity exceeding 200 persons, open to the public, promoted or sold in interstate commerce (§ 3(2)), so a 200-or-fewer venue is outside. NO price, face value, markup or resale price term appears anywhere in the Act: a lawfully acquired ticket may be resold at any price without offending it.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-FED:FTC-464","instrument_kind":"secondary_legislation","citation":"16 CFR Part 464, Rule on Unfair or Deceptive Fees, 90 FR 2166 (2025-01-10)","url":"https://www.ecfr.gov/current/title-16/chapter-I/subchapter-D/part-464","status":"in_force","in_force_from":"2025-05-12","in_force_to":null,"applies_to":"disclosure_only","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"civil","summary":"An unfair and deceptive practice and a violation of the part; enforced by the FTC with civil penalties and consumer redress. § 464.4 does not supersede stricter state law.","max":"$53,088 per violation (16 CFR 1.98(d))"},"enforcement_body":"Federal Trade Commission","quoted_provision":"It is an unfair and deceptive practice and a violation of this part for any business to offer, display, or advertise any price of a covered good or service without clearly and conspicuously disclosing the total price.","notes":"eCFR current as of 2026-11-05 shows the part in force with a 2025-05-12 change date; no rescission observed. 'Covered good or service' is defined in § 464.1 as live-event tickets or short-term lodging only, so the final rule is narrower than the 2023 proposal. § 464.2(b) requires the total price to be more prominent than any other pricing; § 464.2(c) requires pre-consent disclosure of excluded fees and the final amount; § 464.3 bars misrepresenting fees. 'Total price' may exclude government charges, shipping and optional ancillary goods or services if they are then disclosed. It is a disclosure rule: no maximum price, markup or face-value relationship anywhere in §§ 464.1-464.5.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-NY:25.29","instrument_kind":"primary_legislation","citation":"N.Y. Arts and Cultural Affairs Law § 25.29 (Unlawful charges in connection with tickets), penalty in § 25.35","url":"https://www.nysenate.gov/legislation/laws/ACA/25.29","status":"in_force","in_force_from":null,"in_force_to":"2027-07-01","applies_to":"unknown","cap_basis":"face","cap_value":null,"penalty":{"kind":"criminal","summary":"§ 25.35: class A misdemeanour, fine not exceeding $1,000 or two times the defendant's gain; applies whether or not domiciled, licensed or registered in the state.","max":"$1,000 or 2x the defendant's gain"},"enforcement_body":"Attorney General, with concurrent jurisdiction with district attorneys (§ 25.29(3))","quoted_provision":"No operator of any place of entertainment, or his or her agent, representative, employee or licensee shall ... exact, demand, accept or receive, directly or indirectly, any premium or price in excess of the established price plus lawful taxes","notes":"The price ceiling that is actually in force in New York, and not the section usually cited. Base is the 'established price' defined in § 25.03(2) (price fixed at time of sale by the operator, printed on the ticket) plus lawful taxes; fees are not in the base. Carve-outs: a reasonable service charge for special services (sales away from the box office, credit card, delivery), initial sale by auction, and actual physical delivery cost, with no delivery fee for electronic or self-printable tickets. appliesto is left 'unknown' deliberately: the text binds the operator and its agents, representatives, employees and licensees, and whether an independent article-25 licensee reseller falls inside 'licensee' cannot be settled without reading ACA §§ 25.09-25.25, which were not read. Sunset note on the section: 'NB Repealed July 1, 2027'.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-NY:25.27-2027","instrument_kind":"primary_legislation","citation":"N.Y. Arts and Cultural Affairs Law § 25.27 (Unlawful charges in connection with theatre tickets), text effective 2027-07-01","url":"https://www.nysenate.gov/legislation/laws/ACA/25.27","status":"not_in_force","in_force_from":"2027-07-01","in_force_to":null,"applies_to":"designated_events","cap_basis":"face","cap_value":null,"penalty":{"kind":"criminal","summary":"Misdemeanour; a conviction for each violation is punishable by a fine of up to $500 or imprisonment of up to one year, or both (penalty stated in the section itself).","max":"$500 and/or 1 year"},"enforcement_body":"Attorney General and district attorneys","quoted_provision":"any premium or price in excess of the regular or established price or charge, plus lawful taxes, as printed upon the face of each ticket or other evidence of the right of entry thereto","notes":"Enacted but not yet in force: the consolidated section currently carries the 'Commissions to employees of places of entertainment' text marked effective until 2027-07-01, and this text takes effect that day, the same day § 25.29 is repealed. Unlike § 25.29 it expressly reaches resellers: subdivision 2 applies the section 'to the sale of theatre tickets and tickets for sporting events to persons licensed to resell'. Read as a consolidation of the § 25.29 ceiling into § 25.27, but the amending bill was not read and that reading is inference from effective-date notes. Carry as a dated future rule, not as current law.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-NY:25.07","instrument_kind":"primary_legislation","citation":"N.Y. Arts and Cultural Affairs Law § 25.07 (Ticket prices)","url":"https://www.nysenate.gov/legislation/laws/ACA/25.07","status":"in_force","in_force_from":null,"in_force_to":"2027-07-01","applies_to":"disclosure_only","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"unknown","summary":"No penalty is stated in § 25.07 itself; the criminal penalties in § 25.35 attach to §§ 25.27 and 25.29 only.","max":null},"enforcement_body":"unknown","quoted_provision":"shall disclose the total cost of the ticket, inclusive of all ancillary fees that must be paid in order to purchase the ticket","notes":"No price cap. Subdivision 1 requires the operator to print the established price (or final auction price) on each ticket. Subdivision 2 requires anyone who resells or 'facilitates the resale or resale auction of tickets between independent parties by any means', 'regardless of whether or not licensed under this article', to guarantee a full refund including all fees on cancellation, denial of admission, or non-conformity with the advertised description. Subdivision 4 requires operators, licensees, resellers and platforms to disclose the total cost inclusive of mandatory ancillary fees, in the listing before selection, with the service-charge portion stated in dollars, not presented more prominently than the total, and no price increase during the purchase process other than a disclosed delivery fee. Section sunsets 2027-07-01, when a 'Bond' text takes the number.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-CA:BP-22500","instrument_kind":"primary_legislation","citation":"Cal. Bus. & Prof. Code ch. 21 (Ticket Sellers), §§ 22500-22514, as carried in AB 8 (2023-24)","url":"https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240AB8","status":"in_force","in_force_from":null,"in_force_to":null,"applies_to":"all_resale","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"criminal","summary":"§ 22513: a violation of the chapter is a misdemeanour. § 22511: up to 6 months or a $2,500 fine, plus a civil penalty up to $2,500 per violation, each ticket a separate violation. § 22512: private liability of twice the contracted price where a seller fails to supply at the contracted price.","max":"$2,500 civil per violation; 6 months and/or $2,500 criminal for § 22511"},"enforcement_body":"Attorney General; district attorneys; city attorneys of cities over 750,000","quoted_provision":"Restrict by any means the resale of tickets, including tickets in a subscription or season ticket package.","notes":"NO price cap, and the chapter protects above-face resale: § 22506(a)(1) bars a primary contractor from restricting resale by any means; (a)(2) bars denying entry to a resold-ticket holder solely because of the resale; (a)(3)(A) bars paperless systems unless the buyer can transfer 'at any price, and at any time, and without additional fees'; (a)(4) bars pricing by form or transferability. § 22504 requires all-in total price disclosure before selection, with no increase after selection except a disclosed delivery fee. § 22501/22502 bar speculative selling and price promises not honoured; § 22508 caps a non-refundable deposit service charge at 10 percent; § 22507 bars resale of tickets initially offered free; § 22505 mirrors the federal BOTS Act and adds a resale limb. § 22500(b) exempts carrier tour packages, a person selling six or fewer tickets off venue premises, and tax-exempt nonprofits selling their own event. Version read is the 'AMENDED' 2023 bill text, not the chaptered act, so the enactment date is left null.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-CA:PEN-346","instrument_kind":"primary_legislation","citation":"Cal. Penal Code § 346 (added Stats. 1972, ch. 529)","url":"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PEN&sectionNum=346","status":"in_force","in_force_from":"1972-01-01","in_force_to":null,"applies_to":"all_resale","cap_basis":"face","cap_value":null,"penalty":{"kind":"criminal","summary":"Misdemeanour; the section states no separate fine or term.","max":null},"enforcement_body":"local prosecutors","quoted_provision":"sells a ticket of admission to the entertainment event, which was obtained for the purpose of resale, at any price which is in excess of the price that is printed or endorsed upon the ticket, while on the grounds of","notes":"A physical-location offence only: selling above the printed price 'while on the grounds of or in the stadium, arena, theater, or other place' where the event is held, and only without the written permission of the property owner or operator. An online resale made from elsewhere is outside it by its own terms; an on-site will-call or box-office collection point on venue property is not. Basis is the price printed or endorsed on the ticket.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-FL","instrument_kind":"primary_legislation","citation":"Fla. Stat. § 817.36 (Resale of tickets), 2026 edition","url":"http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0800-0899/0817/Sections/0817.36.html","status":"in_force","in_force_from":null,"in_force_to":null,"applies_to":"designated_events","cap_basis":"absolute","cap_value":{"kind":"minor_units","amount":100,"currency":"USD"},"penalty":{"kind":"civil","summary":"§ 817.36(4): a person who knowingly resells in violation is liable to the state for a civil penalty of treble the resale price. § 817.36(5): treble the sale amount for using or selling circumvention software.","max":"3x the resale price, payable to the state"},"enforcement_body":"state of Florida (civil action); Department of Revenue for sales tax on resales","quoted_provision":"A person or entity that offers for resale or resells any ticket may charge only $1 above the admission price charged therefor by the original ticket seller of the ticket for the following transactions","notes":"The only jurisdiction read with a live price cap. $1 over the original ticket seller's admission price, applied to four categories: (a) common-carrier passage or accommodations in the state, with a licensed-travel-agency carve-out; (b) multiday or multievent tickets to a park or entertainment complex, including a concert or event inside one; (c) tickets originally issued by a 501(c)(3) charity where no more than 3,000 are issued per performance and the statutory notice is printed; (d) any other tickets resold through an internet website UNLESS the website is authorised by the original ticket seller or posts the statutory refund guarantee and the disclosure that it does not control pricing and that tickets may be resold above original value. Category (d) is the residual class, so the cap is the default for ordinary online resale and compliance is the escape. Base is the original seller's price, not the printed face and not face plus fees. Not expressly limited to events in Florida: (a) says 'in this state' and (b) is place-based, but (d) has no territorial clause, so the cross-border question is unanswered by the text. § 817.36(2) separately bars selling at any price on event property without the owner's prior written consent. Unamended since ch. 2010-5.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-MA:140-185A","instrument_kind":"primary_legislation","citation":"Mass. Gen. Laws ch. 140, § 185A (Resale of tickets; license)","url":"https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXX/Chapter140/Section185A","status":"in_force","in_force_from":null,"in_force_to":null,"applies_to":"all_resale","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"unknown","summary":"Licensing requirement; the penalty for unlicensed resale is not stated in § 185A.","max":null},"enforcement_body":"commissioner of occupational licensure","quoted_provision":"engage in the business of selling tickets or the business of reselling or facilitating a mechanism for 2 or more parties to participate in the resale of any ticket of admission","notes":"No price term in the section read. It is a licensing section: a licence is required to sell tickets, to resell them, or to facilitate a mechanism for two or more parties to participate in a resale, whether on or off the venue premises; licences run to 1 January next after issue and cannot be transferred without written permission; a ticket sold free or below the public price is deemed a resale. 'Facilitating a mechanism for 2 or more parties to participate in the resale' is the widest platform-capture wording found in this run, and it attaches the obligation to the facilitator rather than only the seller. Only § 185A was read: ch. 140 §§ 181-185G and the Division of Occupational Licensure regulations were not, so this is a single-section result and a cap elsewhere in the chapter is neither excluded nor implied.","confidence":"A","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-CO","instrument_kind":"unknown","citation":"UNVERIFIED. The 2025 Colorado ticket resale law described in the brief (fee transparency, transferability, whether it caps price) was not located, so no bill number, section or date is asserted.","url":"https://leg.colorado.gov/bills","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Unknown; no instrument read.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"leg.colorado.gov is reachable and served bill pages normally, but three General Assembly bill-search queries ('ticket resale', 'ticketing', 'tickets') returned no ticket-related bill, which is a search-index result and not evidence that no such law exists. Four fetches were spent on wrong bill numbers before the search route was abandoned; one wrong bill (HB25-1268, a utility on-bill repayment bill, postponed indefinitely) was read far enough to rule it out. No fee, transferability or cap claim is made. What would settle it: the bill number resolved by title, or the Colorado Revised Statutes consumer-protection article in which the enacted section sits.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-AR","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened. 'unknown' records absence of research, not absence of a cap.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-CT","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-KY","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-LA","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-MI","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-MN","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-MS","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-MO","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-NJ","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-PA","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-RI","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-TN","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-WI","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-IL","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-MD","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-VA","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-GA","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-TX","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-WA","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-OR","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-AZ","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"},
  {"jurisdiction":"US-NV","instrument_kind":"unknown","citation":"NOT CHECKED in this run.","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not checked.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"State was not opened.","confidence":"E","retrieved_at":"2026-11-08T06:05:00Z"}
]
```

Two schema notes, so the consumer is not surprised. `jurisdiction` carries a colon suffix where one
jurisdiction has more than one instrument (US-FED:BOTS, US-FED:FTC-464, US-NY:25.29,
US-NY:25.27-2027, US-NY:25.07, US-CA:BP-22500, US-CA:PEN-346, US-MA:140-185A); split on `:` to get
the jurisdiction code. And `instrument_kind` is set to `unknown`, outside the brief's enum, for any
row that was not read, including all not-checked states, because none of the enum values
(`none_identified` included) is honest about a state that was never opened.
