"""The sentence registry: what the engine may say, and what it must never say.

Every static sentence the console prints comes from here, by id. `core` returns
ids, never sentences, so the api and the console cannot drift from this file and a
reviewer has one place to read.

Two lists, both enforced by tests:

* ALLOWED -- T1-T5 (the mandatory sentences) and A1-A20 (the object sentences),
  from records/BUILD-SPEC-NIGHT.md section 2.3 and 2.6.
* BANNED -- X1-X20, the phrases from the same tables and from
  records/findings/00-adversarial-review-phase1.md section 6. A literal match of any
  of them on the page or in a payload is a test failure. X1 is the sentence this
  build exists to remove: a price-specific sale probability.

Why the negatives are listed by name. X18 bans `deployed` as a claim and requires the
negative forms ("no program is deployed"). A grep for the bare word would fail on the
sentence that makes the page honest, so `contains_banned` strips the negative phrases
by name before it scans. That is the spec's own instruction (section 2.6) and it is
tested in both directions.

No number lives in this file, for the same reason: a sentence registry that also
holds values is a second source of truth.
"""

from __future__ import annotations

import re
from typing import Mapping

# -- badges ---------------------------------------------------------------

BADGES: tuple[str, ...] = (
    "FIXTURE",      # computed from fixtures/synthetic_store.json: generated, not real
    "DECLARED",     # a parameter a person set, not estimated
    "EXACT",        # arithmetic true by definition, carries no uncertainty
    "UNVALIDATED",  # an engine output; nothing checked against a real resale
    "REFUSED",      # the engine declines and names the missing observation
    "DESIGN",       # design only; nothing compiled, deployed or run on a cluster
    "SIMULATED",    # produced by the Python mirror; no cluster contacted
    "DEVNET",       # read back from devnet and verified, or explicitly absent
)


def badge(name: str) -> str:
    """`[FIXTURE]` and so on. Raises on an unknown name so a typo cannot ship."""
    if name not in BADGES:
        raise KeyError(f"unknown badge {name!r}")
    return f"[{name}]"


# -- the mandatory sentences ---------------------------------------------

MANDATORY: Mapping[str, str] = {
    "T1": (
        "SYNTHETIC FIXTURE DATA — every number on this page is computed from a synthetic "
        "fixture generated in this repository. Not real ticket data. No accuracy claim is "
        "made or implied."
    ),
    "T2": "This is a bound, not an optimum.",
    "T3": (
        "The band is a declared width around the record, not a confidence interval, and it "
        "has not been checked against what this event sold for."
    ),
    "T4": (
        "That is a transaction rate for the ticket population, marginalised over whether the "
        "ticket was ever offered. It is not the probability that a listed ticket sells."
    ),
    "T5": "No program is deployed on any cluster. Nothing on this page is a deployed guarantee.",
}

# -- the object sentences -------------------------------------------------

ALLOWED: Mapping[str, str] = {
    # A1 counts the tier, because the rate beside it is the tier's: `intensity.estimate`
    # divides the tier's sales by the tier's exposure. The sentence used to say "on this
    # event" while the number in it was the tier's, so it read 6 where the strip read 14.
    "A1": (
        "In this tier the ledger records {n} sales. The sale rate above is this tier's own: "
        "its sales over its ticket-days at risk. That is a transaction rate for the ticket "
        "population, not the probability that a listed ticket sells."
    ),
    "A1_ONE": (
        "In this tier the ledger records one sale. The sale rate above is this tier's own: "
        "its sales over its ticket-days at risk. That is a transaction rate for the ticket "
        "population, not the probability that a listed ticket sells."
    ),
    # Zero sales. The number beside this sentence is the posterior mean of a declared
    # Gamma(1, 1) prior, not 0/exposure, so the sentence may not present it as a measured
    # rate: it names the prior, and it says the number moves as exposure grows.
    "A1_ZERO": (
        "In this tier the ledger records no sale. The rate above is not measured from the "
        "record: it is the posterior mean of the declared Gamma(1, 1) prior over the "
        "ticket-days at risk, so it falls as that exposure grows and it is not zero. That "
        "is a transaction rate for the ticket population, not the probability that a listed "
        "ticket sells."
    ),
    "A2": (
        "The resale value of this ticket is bounded. The last recorded sale gives a floor, "
        "the resale cap gives a ceiling, and the interval is wide because the ledger records "
        "sales, not listings."
    ),
    # The uncapped page has no ceiling, so it may not borrow the capped sentence.
    "A2_UNCAPPED": (
        "The resale value of this ticket is bounded. The last recorded sale gives a floor, "
        "the declared width gives a band, and the interval is wide because the ledger "
        "records sales, not listings. This event has no resale cap, so no ceiling enters "
        "the bound."
    ),
    # An uncapped event priced against a cap typed into the page: there is a ceiling, and it
    # belongs to the page's policy rather than to the record. The sentence names which one,
    # because `A2`'s "the resale cap gives a ceiling" would read as a cap this event has.
    "A2_CAP_IN_FORCE_UNCAPPED": (
        "The resale value of this ticket is bounded. The last recorded sale gives a floor, "
        "the cap this page prices against gives a ceiling, and the interval is wide because "
        "the ledger records sales, not listings. This event records no cap of its own, so "
        "that ceiling is the page's and not the record's."
    ),
    "A3": (
        "On this event the cap binds: tickets sold at the cap are recorded at the ceiling, so "
        "their value is at least the cap. How far above it we cannot say from this record."
    ),
    "A4": (
        "The primary price recommendation is a range, not a point. It is based on the resale "
        "value signal and the primary sell-through observation; it does not use a resale "
        "sale-probability curve."
    ),
    "A5": (
        "The value index is a set of ratios across events and tiers, normalised to a base "
        "period. It does not give an absolute price level without an external anchor."
    ),
    "A6": (
        "The fee basis is a parameter, not an estimate. If the recorded price is the buyer's "
        "gross, the seller's net is lower by the fee schedule, and the recommendation changes "
        "with the fee model."
    ),
    "A7": (
        "The sale indicator is calibrated on the full ticket population. No price "
        "distribution is calibrated, and we quote no coverage number for a price."
    ),
    "A8": (
        "The estimate is a bound with a stated width. The width is driven by the missing "
        "listing exposure and the cap truncation."
    ),
    "A9": (
        "The ledger is complete only conditional on enforcement: wallet handoff and "
        "off-platform settlement leave no row, and we do not impute them."
    ),
    "A10": (
        "The cap is a ceiling on the resale price and therefore on the buyer's outside "
        "option; it is a floor on value, not a target for the primary price."
    ),
    "A11": (
        "This is a class-C bound from the schema and a class-B prior from the literature; it "
        "is not a measured result on this platform."
    ),
    "A12": (
        "No prediction: nothing has resold on this platform yet, so this band comes from "
        "published ticket markets and has not been checked against a single sale here."
    ),
    # The cold band in the counterfactual mode is `value_band.prior_only`: the literature
    # prior widened by the declared tau. It is not a spread measured across other events,
    # and the sentence used to say it was. A band built by pooling other events is A13_POOLED.
    "A13": (
        "Not a prediction: this event has no resales yet, so the band is the declared "
        "literature prior on the log price-to-face ratio, widened by the declared τ on "
        "each side. It is not a spread measured across other events, and it has not been "
        "checked against a single sale here."
    ),
    "A13_POOLED": (
        "Not a prediction: this decision excludes this event's own resale rows, so the "
        "band's centre is the pooled mean log price-to-face over {n_events} other events "
        "with resale, and its width is the declared τ on each side. It has not been checked "
        "against what this event sold for."
    ),
    "A14": (
        "Recommended primary price: {P} SOL per ticket. This is a bound, not an optimum. It "
        "is the highest price at which this event still fills on the evidence available: {s}% "
        "of the tier sold at {y} SOL with {d} days to go, and resale clearing at {m} SOL. "
        "Above {P} we cannot show that the house still fills, and we will not recommend a "
        "price we cannot defend."
    ),
    "A15": (
        "The platform does not record asking prices, so we cannot estimate the chance a "
        "ticket sells at a specific price. What is shown is what actually happened."
    ),
    "A16": "At the cap — a rationing point, not a market-clearing price.",
    "A17": (
        "The model is not fitted. {n_events} events have completed in the observation window "
        "and {m} have any resale activity, so the between-event dispersion cannot be "
        "estimated and no out-of-sample score exists. What follows is the pooled prior with "
        "its width declared, not estimated."
    ),
    "A17_ONE": (
        "The model is not fitted. One event has completed in the observation window and "
        "{m} have any resale activity, so the between-event dispersion cannot be "
        "estimated and no out-of-sample score exists. What follows is the pooled prior "
        "with its width declared, not estimated."
    ),
    "A17_ONE_M": (
        "The model is not fitted. {n_events} events have completed in the observation "
        "window and one has any resale activity, so the between-event dispersion cannot be "
        "estimated and no out-of-sample score exists. What follows is the pooled prior "
        "with its width declared, not estimated."
    ),
    "A17_ONE_ONE": (
        "The model is not fitted. One event has completed in the observation window and it "
        "has resale activity, so the between-event dispersion cannot be estimated and no "
        "out-of-sample score exists. What follows is the pooled prior with its width "
        "declared, not estimated."
    ),
    "A18": (
        "One ticket sold twice: {p1} → {p2} SOL over {d} days. One pair is a fact, not an "
        "index."
    ),
    # The four counts in A19 -- the cap in percent, the sales at the ceiling, the sales, and
    # the share -- each carry their own badge: the sentence sits in a panel badged
    # `[UNVALIDATED]` while every one of its numbers is a `[FIXTURE]` count, so the block's
    # badge alone let a reader take a record count for an engine output. The percent signs
    # moved out of the template and into the badged number (`15%`, `88.9%`), so the printed
    # digits are unchanged.
    "A19": (
        "The resale price in this tier is capped at {c} over face, and the cap is binding: "
        "{k} of {n} recorded resales ({s}) settled at exactly the ceiling. Those buyers each "
        "paid the most the platform allows, so the record shows what was paid, not what "
        "buyers would have paid, and every sale the ceiling turned away is missing from it "
        "entirely."
    ),
    "A20": (
        "This tier has a resale cap and no sale has reached it. We cannot tell from this "
        "record whether the cap binds: the absence of a sale at the ceiling is not evidence "
        "that the ceiling does not bind."
    ),
}

# -- the page's fixed prose, by id (the page may print an id, never a literal) -----

PAGE: Mapping[str, str] = {
    "P_CAPLINE": "A cap does not hide the price; it hides the top of the price distribution.",
    # The same idea on an event whose regime is `uncapped`. The capped sentence was printed on
    # every page, including the ones whose own regime line says `uncapped` and whose cap field
    # is null, where it read as a claim about a cap this event does not have.
    "P_CAPLINE_UNCAPPED": (
        "No cap applies to this event, so nothing hides the top of the price distribution."
    ),
    "P_HEAD": "Recommended primary price: {P} SOL per ticket.",
    "P_HEAD_FLOOR": "Recommended primary price: at least {P} SOL per ticket, {tier} tier.",
    "P_BAND": "Band {P_lo} – {P_hi} SOL.",
    "P_RANGE": "We would not argue with any price in that range.",
    "P_A19_VALUE": (
        "Value: at least {m} SOL per ticket. That is a floor, not an estimate. It is the "
        "highest recorded price in this tier, and it is the most this record can support."
    ),
    "P_A19_RANGE": "Range: {lo} SOL and up. We do not state an upper bound from this record.",
    "P_ASOF": "Nothing after {asOf} enters any number, and the URL carries the instant.",
    "P_COLD_CHANGE": "One completed resale on this event, or a completed event like it, is what would change this.",
    "P_CHAIN_INVARIANT": (
        "A ticket moves only through an instruction this program processes, the price is "
        "checked against face + face × cap_bps / 10 000 at execution, and a transfer to "
        "anything but the escrow or the settled buyer fails inside the token program."
    ),
    "P_CHAIN_DESIGN": (
        "No program is deployed on any cluster. What follows is the invariant, the "
        "instruction set and a simulation; none of it is a deployed guarantee."
    ),
    "P_CHAIN_CAPTION": (
        "A Python mirror of the state machine, standard library only, no cluster "
        "contacted; it proves the arithmetic and the ordering, not that Token-2022 calls "
        "a hook."
    ),
    "P_CHAIN_ABSENT": (
        "The console shows this state until a devnet signature has been verified against "
        "api.devnet.solana.com. No signature is ever typed into this page by hand."
    ),
    "P_CHAIN_MEMO": (
        "This is the pricing decision committed on devnet before the sale opens, so it "
        "cannot be re-cut afterwards — and the transfer hook that makes the cap binding "
        "is designed, not deployed."
    ),
    "P_SIM_BUTTON": "Show the refusal",
    "P_FEE_WITHHELD": "The net value line is withheld until a fee is supplied; the recommendation does not depend on an ad-valorem fee.",
    "P_NO_LEDGER": "No ledger exists. Nothing was invented to fill it.",
    "P_BANNER_2": (
        "No program is deployed on any cluster. The [DESIGN] block at the bottom says what "
        "that means."
    ),
    "P_TAU_INERT": "There is no upper tail in this record for τ to widen, so the control is inert here.",
    "P_BAND_ON_PRIOR": "That is a band around the declared prior, not a price for this ticket.",
    "P_CAP_ABOVE": (
        "Raising the cap changes what we will learn from the next sales, not what this "
        "record says."
    ),
    "P_CAP_FORWARD": (
        "A recorded price is a fact about the past; the cap is a rule about the future."
    ),
    "P_NO_TIER": "This event has no tier to price, so there is nothing to show.",
    "P_MODE_COUNTERFACTUAL": (
        "Decision mode: COUNTERFACTUAL. This page recomputes the value from this event's own "
        "completed record: this is not a price you could have set; it is what the record "
        "implies in hindsight."
    ),
    "P_MODE_BEFORE": (
        "Decision mode: BEFORE-ON-SALE. This is the decision as it is taken before this "
        "event's first ticket is issued: only other events' completed resale records and "
        "this event's own metadata enter it, and this event's own ledger rows are excluded."
    ),
    "P_MODE_EVENT": (
        "Event {name} · status {status} · starts {startsAt} · ends {endsAt} · decision "
        "instant {asOf}."
    ),
    "P_NET": (
        "Net to the seller per ticket: {net} SOL after the declared fee of {fee} SOL."
    ),
    "P_NET_NEGATIVE": (
        "The declared fee of {fee} SOL per ticket is larger than the recommended price of "
        "{price} SOL, so a sale at that price would leave the seller short by {shortfall} "
        "SOL per ticket. A negative net is not a price, so the line is refused rather than "
        "printed as one."
    ),
    "P_NO_CAP": "This event has no resale cap, so there is no ceiling to count against.",
    # The same clause where the event records no cap and the page prices against one. The two
    # sentences above and below it were printed on a page that had a ceiling, counted seven
    # sales above it, and offered a band whose top the cap had not trimmed (N1, N2).
    "P_MARKET_NO_RECORDED_CAP": (
        "This event records no resale cap, so its sales have no ceiling to be counted "
        "against. This page prices against a cap of {cap}, and the sales above that cap are "
        "counted in the decision."
    ),
    # The evidence strip's ceiling item, on the same state: the count of sales at the ceiling
    # is a count against the record's cap, and this event has none.
    "P_STRIP_CAP_UNCAPPED_RECORD": (
        "no resale cap is recorded on this event, so its sales have no ceiling to be counted "
        "against; this page prices against a cap of {cap}"
    ),
    # The band's upper end is stopped at the ceiling the cap in force puts on the tier. Said
    # where it happens, because `We would not argue with any price in that range` beside a
    # band above the page's own ceiling is the contradiction this sentence closes (N2).
    "P_BAND_STOPS": (
        "The top of that band is the ceiling the cap in force puts on this tier, at "
        "{ceiling} SOL, so the range stops where the cap does."
    ),
    # The before-on-sale strip counts the excluded rows as excluded. `0 resales` and
    # `0 tickets` were printed for a store holding 12 of each, which says the record does not
    # exist rather than that this mode does not read it (N4).
    "P_STRIP_EXCLUDED_RESALES": (
        "{n} resales enter this decision; {m} recorded on this event are excluded by the mode"
    ),
    "P_STRIP_EXCLUDED_TICKETS": (
        "{n} tickets enter it; {m} recorded on this event are excluded by the mode"
    ),
    "P_STRIP_EXCLUDED_CEILING": (
        "no at-ceiling count while the event's own record is excluded"
    ),
    "P_EXACT_CEILING": (
        "ceiling {lamports} lamports = face {face} lamports × (10,000 + {cap}) / 10,000 "
        "— integer arithmetic on the tier face, not an estimate. That is exactly {sol} SOL."
    ),
    "P_CEILING_NONE": "no resale cap on this event, so no ceiling: face {face} SOL.",
    # The cap field and the canonical URL under it carry the cap this page prices against,
    # and on the page with no capBps parameter that cap is the event's recorded one. The
    # two sentences say which number the reader is looking at, so a field that shows 2500
    # while the record's own cap is 1500 is read as two facts and not as a contradiction.
    "P_CAP_RULE": (
        "The cap field shows the resale cap this page prices against and the canonical URL "
        "carries the same number: clear the field and submit to fall back to this event's "
        "recorded cap of {recorded} bps."
    ),
    "P_CAP_RULE_UNCAPPED": (
        "This event records no cap, so a blank field means no cap and this page prices "
        "against none: type a number to price against that cap, and the canonical URL "
        "carries it."
    ),
    # The decision block names the cap in force whenever it is not the record's own. The
    # recorded sales are still described under the cap they were made under; the two
    # numbers are named so the reader never has to reconcile them.
    "P_CAP_IN_FORCE": (
        "This page prices against a cap of {cap}. The record was made under a cap of "
        "{recorded}, so the recorded sales are described under that cap, not this one."
    ),
    "P_CAP_IN_FORCE_UNCAPPED": (
        "This page prices against a cap of {cap}. This event records no cap of its own, so "
        "no recorded sale is reclassified by this one."
    ),
}

# -- the refusal sentences (section 4.8) ----------------------------------

REFUSAL_TEXT: Mapping[str, str] = {
    "no_ledger": "No ledger exists. Nothing was invented to fill it.",
    "no_resale_record": "No resale has been recorded on this event, so we will not state a primary price.",
    # The same refusal where the rows exist and the mode declines to use them. `no_resale_record`
    # is true only of an event with no rows at or before the cut; on the before-on-sale page the
    # event's rows are in the store and excluded, so that sentence was false there. The count is
    # the same pooled count the band label prints, interpolated rather than assumed.
    "no_resale_record_excluded": (
        "This event's own resale rows are excluded by the BEFORE-ON-SALE decision mode, so "
        "its record supplies no price here; the band on this page is the pooled record of "
        "{n_events} other events on this platform, and a pooled band is not a price for this "
        "ticket, so no primary price is stated."
    ),
    "no_resale_record_excluded_no_pool": (
        "This event's own resale rows are excluded by the BEFORE-ON-SALE decision mode, and "
        "no other event on this platform has a resale record, so there is nothing to pool "
        "and no primary price is stated."
    ),
    "no_upper_bound": "We do not state an upper bound from this record.",
    # The two store states the loader holds an event back for, typed at load. A sale with no
    # money and a sale dated after the event starts are not prices the engine can read, and
    # the row is named so a reader can go and look at it.
    "sale_not_priced": (
        "Row {row} is a sale recorded without money, so this event cannot be priced: a zero "
        "resale price has no ratio to face value, and no number for this event is stated."
    ),
    "sale_after_event_start": (
        "Row {row} is a sale dated after this event starts, so this event cannot be priced: "
        "the time from that sale to the event is negative, and no number for this event is "
        "stated."
    ),
    # The cap in force on the page is a hard ceiling on the recommendation, in the same
    # integer arithmetic the store uses. When it sits below the price this record supports,
    # the record's recommendation is a price the policy forbids, and the ceiling is not
    # printed in its place: a cap is a floor on value, not a target for a primary price.
    "recommendation_above_cap": (
        "The cap of {cap_bps} in force on this page puts the resale ceiling at "
        "{ceiling_lamports}, below the price this record supports, so no primary "
        "price is stated: a recommendation above that ceiling is a price the cap forbids, "
        "and the ceiling is not a target for the primary price."
    ),
    # No flat path is drawn anywhere in the console, so the sentence may not promise one.
    "insufficient_marks": "{n} sales is too few to fit a path, so no path is quoted.",
    "insufficient_marks_one": "One sale is too few to fit a path, so no path is quoted.",
    "before_on_sale_no_pool": (
        "No other event on this platform has a resale record, so there is nothing to pool "
        "for a before-on-sale value and we will not state one."
    ),
    "insufficient_time_spread": "The {n} resales span {d} days; 5 days of spread are required to separate time from the level.",
    "degenerate_design": "The resales are too clustered in time to separate curvature from drift.",
    "no_exposure": "No ticket had been issued at this instant, so there is no denominator.",
    # The same refusal where the rows exist and the mode excludes them. `No ticket had been
    # issued at this instant` is true of a cut before the first issue and false on the
    # before-on-sale page, where the store holds the ticket rows and the mode declines to read
    # them (N4). The count is the excluded count, not the zero that enters the decision.
    "no_exposure_excluded": (
        "{n} tickets are recorded on this event at this instant, and the BEFORE-ON-SALE "
        "decision mode excludes every one of them, so no ticket-day of exposure enters this "
        "denominator and the rate has none."
    ),
    "no_exposure_excluded_one": (
        "{n} ticket is recorded on this event at this instant, and the BEFORE-ON-SALE "
        "decision mode excludes it, so no ticket-day of exposure enters this denominator and "
        "the rate has none."
    ),
    # The same refusal where a ticket *had* been issued and no ticket-day of exposure has
    # elapsed: a cut exactly on the first issue instant. The old sentence said no ticket had
    # been issued, beside a strip that said `[FIXTURE] 1 ticket`. The count is the strip's own
    # wrapper, so the two cannot disagree; the zero case keeps the sentence that is true there.
    "no_exposure_issued": (
        "{n} tickets had been issued on this event by this instant, but no ticket-day of "
        "exposure has elapsed in this tier, so the rate has no denominator."
    ),
    "no_exposure_issued_one": (
        "{n} ticket had been issued on this event by this instant, but no ticket-day of "
        "exposure has elapsed in this tier, so the rate has no denominator."
    ),
    "not_identified": (
        "The platform does not record asking prices, so we cannot estimate the chance a "
        "ticket sells at a specific price. What is shown is what actually happened."
    ),
    "no_demand_response": (
        "An interior optimum needs a primary demand response. η and q_min are not identified "
        "from this record, so the recommendation is a boundary."
    ),
    "no_fee_model": (
        "No fee model is configured. The recommendation does not depend on an ad-valorem fee; "
        "the net value line does, so it is withheld."
    ),
    "insufficient_events": (
        "The event count is below the floor for a between-event quantity, so the dispersion "
        "is declared rather than estimated."
    ),
    "cap_mass_dominates": (
        "More than half of this tier's recorded sales sit on the ceiling, so a central "
        "path statistic would describe the ceiling, not the market. No path value is "
        "quoted."
    ),
    "outside_support": (
        "The {n} resales span {d} days and stop {k} days before the event, so the "
        "requested horizons fall outside the window the record covers. No path value is "
        "quoted."
    ),
    "outside_support_no_span": (
        "The {n} resales stop {k} days before the event, so the requested horizons fall "
        "outside the window the record covers. No path value is quoted."
    ),
    # A counterfactual, written as one. The banner says no program is deployed, so this
    # sentence may not call it "the deployed program".
    "cap_would_refuse": (
        "{k} of {n} recorded sales in this tier are above this cap; had this cap been "
        "enforced, those transfers would have failed, so this record could not exist."
    ),
    "devnet_absent": "No devnet transaction has been recorded.",
    "rpc_disabled": "Chain status not read: the RPC adapter is disabled. No program is deployed either way.",
}

ALLOWED_IDS: frozenset[str] = (
    frozenset(MANDATORY) | frozenset(ALLOWED) | frozenset(PAGE) | frozenset(REFUSAL_TEXT)
)

# -- what the engine must stop saying -------------------------------------

# Phrases, not single words: `deployed` alone appears inside the sentence that makes
# the page honest, and X18 bans the claim, not the denial.
BANNED_SOURCES: tuple[str, ...] = (
    r"this ticket has an? [^.]{0,40}chance of selling",
    r"chance of selling at price",
    r"the probability this ticket sells at price",
    r"knows what (?:this|the) ticket is worth",
    r"\bthe demand curve is\b",
    r"\bthe price elasticity is\b",
    r"cap correction recovers",
    r"(?:are|is) irrelevant to pricing",
    r"sale probability is calibrated",
    r"resale ledger is complete",
    r"what the whole market earns",
    r"revenue[- ]maximi[sz]ing primary price",
    r"central structural fact",
    r"(?:asking|ask)[- ]versus[- ]realised gap has been measured",
    r"raised to the cap because",
    r"\bis what this ticket is worth\b",
    r"\bmarket price\b",
    r"\blive price\b",
    r"\breal-time price\b",
    r"\b(?:is|as|that is) (?:a|an|the|our|its) (?:price )?(?:prediction|forecast)\b",
    r"\bexpected price\b",
    r"\b90% likely\b",
    r"\bcalibrated to\b",
    r"\baccurate to ±",
    r"\bconfidence: high\b",
    r"\bis deployed\b",
    r"\bhas been deployed\b",
    r"\bwas deployed\b",
    r"\bverified on solana\b",
    r"\bis on-chain\b",
    r"\bthe on-chain record\b",
    r"\bcomparable events\b",
    r"\bprobability of sale\b",
    r"\bchance it sells\b",
    r"\bliquidity score\b",
    r"\bsell-through forecast\b",
)

BANNED_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(source, re.IGNORECASE) for source in BANNED_SOURCES
)

# The negatives the page needs, allowed by name (spec section 2.6). Stripped from the
# text before the patterns are scanned, case-insensitively.
ALLOWED_NEGATIVES: tuple[str, ...] = (
    "no program is deployed",
    "not deployed",
    "no devnet transaction has been recorded",
    "no on-chain transaction has been recorded",
    "we do not state an upper bound",
    "not a prediction",
    "no prediction",
    "not a forecast",
)


def contains_banned(text: str) -> str | None:
    """Return the first banned pattern's source, or None. The page and the payload use this."""
    cleaned = text.lower()
    for phrase in ALLOWED_NEGATIVES:
        cleaned = cleaned.replace(phrase, " ")
    for pattern in BANNED_PATTERNS:
        if pattern.search(cleaned):
            return pattern.pattern
    return None


def render(label_id: str, **fields: object) -> str:
    """The sentence for an id, with fields substituted. KeyError on an unknown id."""
    if label_id in MANDATORY:
        template = MANDATORY[label_id]
    elif label_id in ALLOWED:
        template = ALLOWED[label_id]
    elif label_id in PAGE:
        template = PAGE[label_id]
    elif label_id in REFUSAL_TEXT:
        template = REFUSAL_TEXT[label_id]
    else:
        raise KeyError(f"unknown label id {label_id!r}")
    return template.format(**fields) if fields else template
