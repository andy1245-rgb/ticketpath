"""Re-check every URL the review names, against the live server on 8788."""

import html as html_module
import re
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8788"


def get(path, method="GET"):
    req = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


def text(html):
    """The page as a reader sees it: entities resolved, tags stripped, whitespace collapsed.

    Entities were left in place, so an assertion on a sentence carrying an apostrophe
    (`the event's own record`) could not match the page it was written from.
    """
    stripped = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    plain = re.sub(r"<[^>]+>", "", stripped)
    return re.sub(r"\s+", " ", html_module.unescape(plain))


CASES = [
    ("cold-start evt_syn_03", "/?event=evt_syn_03", "GET", 200),
    ("default page", "/", "GET", 200),
    ("uncapped evt_syn_04", "/?event=evt_syn_04", "GET", 200),
    ("uncapped event with a typed cap", "/?event=evt_syn_04&capBps=1700", "GET", 200),
    ("band under a typed cap", "/?event=evt_syn_01&capBps=298", "GET", 200),
    ("post-end cut", "/?event=evt_syn_02&asOf=2027-06-01T00:00:00Z", "GET", 200),
    ("evt_syn_07", "/?event=evt_syn_07", "GET", 200),
    ("capBps=0", "/?event=evt_syn_02&capBps=0", "GET", 200),
    ("cut before issue", "/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z", "GET", 200),
    ("completed evt_syn_06", "/?event=evt_syn_06", "GET", 200),
    ("before on-sale", "/?event=evt_syn_02&mode=before_on_sale", "GET", 200),
    ("fee set", "/?event=evt_syn_02&feeLamports=50000000", "GET", 200),
    ("negative net", "/?event=evt_syn_02&feeLamports=5000000000", "GET", 200),
    ("sim", "/?sim=1", "GET", 200),
    ("bad mode", "/?mode=nonsense", "GET", 400),
    ("bad cap", "/?capBps=nope", "GET", 400),
    ("unknown event", "/?event=evt_nope", "GET", 404),
    ("HEAD /", "/", "HEAD", 200),
    ("POST /", "/", "POST", 405),
    ("PUT /", "/", "PUT", 405),
    ("DELETE /", "/", "DELETE", 405),
    ("PATCH /", "/", "PATCH", 405),
    ("TRACE /", "/", "TRACE", 405),
]

fails = []
print("== responses")
for name, path, method, want in CASES:
    status, headers, body = get(path, method)
    is_page = ("<!doctype html>" in body) or method == "HEAD"
    empty = status == 0 or (method != "HEAD" and body == "")
    ok = status == want and is_page and not empty
    print(f"{'ok  ' if ok else 'FAIL'} {name:24s} {method:4s} {path:46s} {status} page={is_page} ctype={headers.get('content-type', '')[:22]}")
    if not ok:
        fails.append((name, status, want))

print("\n== labels")


def body_of(path):
    return get(path)[2]


def check(name, cond, detail=""):
    print(f"{'ok  ' if cond else 'FAIL'} {name}" + (f"   [{detail}]" if detail and not cond else ""))
    if not cond:
        fails.append((name, detail, "label"))


d = text(body_of("/"))
check("default: mode label", "Decision mode: COUNTERFACTUAL" in d)
check("default: required sentence verbatim",
      "this is not a price you could have set; it is what the record implies in hindsight" in d)
check("default: status and date beside it", "status on_sale" in d and "starts 2026-11-21T23:00:00.000Z" in d)
strip = re.search(r"\[FIXTURE\] (\d+) resales on this event", d)
market = re.search(r"in this tier \[FIXTURE\] (\d+) sales of \[FIXTURE\] (\d+) on this event", d)
check("default: strip and market agree on resales",
      bool(strip and market) and strip.group(1) == market.group(2),
      f"{strip.group(1) if strip else '?'} vs {market.group(2) if market else '?'}")
check("default: A1 counts the tier", "In this tier the ledger records [FIXTURE] 9 sales." in d)
check("default: no 'On this event the ledger records'", "On this event the ledger records" not in d)
check("default: A19's counts each carry their own badge",
      "capped at [FIXTURE] 15% over face" in d and "[FIXTURE] 8 of [FIXTURE] 9 recorded resales" in d)
check("default: the cap line is printed where a cap exists",
      "A cap does not hide the price" in d and "No cap applies to this event" not in d)

c = text(body_of("/?event=evt_syn_03"))
check("cold: zero-sale rate carries DECLARED", "[DECLARED] 7.5" in c or "[DECLARED] 7.6" in c)
check("cold: prior named beside it", "posterior mean of the declared Gamma(1, 1) prior" in c)
check("cold: A13 states the prior it uses",
      "the band is the declared literature prior" in c and "the spread across" not in c)
check("cold: one completed count", c.count("event has completed") == 2 or c.count("events have completed") == 2,
      str(c.count("event has completed")))
check("cold: no measured-rate claim", "not measured from the record" in c)

u = text(body_of("/?event=evt_syn_04"))
check("uncapped: no ceiling anywhere",
      "no resale cap, so no ceiling" in u and "resale cap gives a ceiling" not in u and "At the cap" not in u)
check("uncapped: no sentence says a cap hides the top of the distribution",
      "A cap does not hide the price" not in u
      and "No cap applies to this event, so nothing hides the top of the price distribution." in u)

s7 = text(body_of("/?event=evt_syn_07"))
check("evt07: EXACT equality exact",
      "ceiling 1,125,000,000 lamports = face 900,000,000 lamports \u00d7 (10,000 + 2500) / 10,000" in s7)
check("evt07: multiplication checks", 900000000 * (10000 + 2500) // 10000 == 1125000000)
check("evt07: exact SOL", "That is exactly 1.125 SOL." in s7)

z = text(body_of("/?event=evt_syn_02&capBps=0"))
check("cap0: counterfactual written as one",
      "had this cap been enforced" in z and "under the deployed program" not in z)
check("cap0: no payload wrapper", "{'value'" not in z and "of 9 recorded sales" in z)

cu = text(body_of("/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z"))
check("cut before issue: 0 tickets", "[FIXTURE] 0 tickets" in cu)
check("cut before issue: the no-denominator sentence is the true one",
      "No ticket had been issued at this instant" in cu)

# The cap this page prices against, in the three places that used to read the recorded cap.
uc = text(body_of("/?event=evt_syn_04&capBps=1700"))
check("uncapped event with a typed cap: the strip names the cap in force",
      "this page prices against a cap of [DECLARED] 1700 bps" in uc
      and "no resale cap, so no ceiling" not in uc)
check("uncapped event with a typed cap: no sentence denies the ceiling",
      "no ceiling to count against" not in uc and "no ceiling enters the bound" not in uc)
check("uncapped event with a typed cap: A2 names the page's ceiling",
      "the cap this page prices against gives a ceiling" in uc)

# The band's upper end, against the ceiling the page's own cap puts on the tier.
band = text(body_of("/?event=evt_syn_01&capBps=298"))
range298 = re.search(r"Band ([\d.]+) \u2013 ([\d.]+) SOL", band)
check("cap 298: the band stops at the ceiling in force",
      bool(range298) and float(range298.group(2)) <= 1.03 and "at 1.0298 SOL" in band)

# FINAL-PROOF-2 C3: on a page whose cap in force is the higher of the two, the sentence that
# says where the band stops called the record's ceiling `the ceiling the cap in force puts on
# this tier`. It now names the cap that produced the number it prints.
above = text(body_of("/?event=evt_syn_01&capBps=3500"))
check("typed cap above the record's: the band-stop sentence names the recorded cap",
      "the ceiling the recorded cap of [FIXTURE] 2500 bps puts on this tier, at [EXACT] 1.25 SOL" in above
      and "the ceiling the cap in force puts on this tier" not in above)

# FINAL-PROOF-2 C2: this page printed a prior band to 1.26 SOL beside its own stated ceiling of
# 0.84 SOL. The band printed is cut at the ceiling, the cut names the cap that made it, and the
# declared prior's own extent is printed beside it rather than as the band.
cold = text(body_of("/?event=evt_syn_03"))
prior = re.search(
    r"prior band around face: \[UNVALIDATED\] ([\d.]+) SOL \u2013 \[UNVALIDATED\] ([\d.]+) SOL", cold
)
stated = re.search(r"That is exactly ([\d.]+) SOL", cold)
check("cold: the prior band's top is not above the ceiling the page states",
      bool(prior and stated) and float(prior.group(2)) <= float(stated.group(1)),
      f"band {prior.group(2) if prior else '?'} vs ceiling {stated.group(1) if stated else '?'}")
check("cold: the cut is said, with the cap that made the ceiling",
      "That band is cut at the ceiling of [EXACT] 0.84 SOL that the cap of [DECLARED] 2000 bps in force" in cold)
check("cold: the declared prior's own extent is named beside the cut",
      "The declared prior alone runs [UNVALIDATED] 0.65 SOL to [UNVALIDATED] 1.26 SOL" in cold)

# A band end that is a limit is printed at the limit's own digits: 1.725 rounded to 1.73 sits
# above the ceiling it was just cut at, which is the same defect one rounding away.
rounded = text(body_of("/?event=evt_syn_05&capBps=1500"))
check("cut band: the printed top is the ceiling's own digits, not a rounding above it",
      "prior band around face: [UNVALIDATED] 1.40 SOL \u2013 [UNVALIDATED] 1.725 SOL" in rounded
      and "cut at the ceiling of [EXACT] 1.725 SOL" in rounded)

# The denominator stops at the event end, so a static record's rate stops falling.
post = text(body_of("/?event=evt_syn_02&asOf=2027-06-01T00:00:00Z"))
check("post-end cut: the denominator is the event, not the clock",
      "exposure [FIXTURE] 551.8 ticket-days at risk" in post
      and "sale rate in this tier: [FIXTURE] 16.3 per 1,000 ticket-days" in post)

ci = text(body_of("/?event=evt_syn_02&asOf=2026-09-11T11:00:00Z"))
check("cut on the first issue: the strip and the sentence agree",
      "[FIXTURE] 1 ticket" in ci
      and "[FIXTURE] 1 ticket had been issued on this event by this instant" in ci
      and "No ticket had been issued at this instant" not in ci)
check("cut on the first issue: the store count is named as the store's",
      "[FIXTURE] 8 events in the store," in ci and "with any resale at this instant" in ci)

f = text(body_of("/?event=evt_syn_02&feeLamports=50000000"))
check("fee: net line renders",
      "Net to the seller per ticket: 1.33 SOL after the declared fee of 0.05 SOL." in f)
check("fee: no no_fee_model refusal", "no_fee_model" not in f)

n = text(body_of("/?event=evt_syn_02&feeLamports=5000000000"))
check("negative net: refused as a state",
      "short by 3.62 SOL per ticket" in n and "Net to the seller per ticket:" not in n)

b = text(body_of("/?event=evt_syn_02&mode=before_on_sale"))
check("before: mode label", "Decision mode: BEFORE-ON-SALE" in b)
# This assertion used to read the opposite way: it required `[FIXTURE] 0 resales on this event`
# and `[FIXTURE] 0 tickets`, which are false on a store holding 12 of each. The mode excludes
# the rows; it does not unrecord them. It now fails on those sentences and requires the count
# of what was excluded, so the checker cannot pin the defect back in place.
check("before: the excluded record is counted as excluded, not as absent",
      "[FIXTURE] 0 resales on this event" not in b
      and re.search(r"\[FIXTURE\] 0 tickets (?!enter)", b) is None
      and "No ticket had been issued at this instant" not in b)
check("before: both excluded counts are printed",
      "[FIXTURE] 0 resales enter this decision; [FIXTURE] 12 recorded on this event are excluded by the mode" in b
      and "[FIXTURE] 0 tickets enter it; [FIXTURE] 12 recorded on this event are excluded by the mode" in b)
check("before: the no-denominator refusal names the excluded tickets",
      "[FIXTURE] 12 tickets are recorded on this event at this instant, and the BEFORE-ON-SALE "
      "decision mode excludes every one of them" in b)
# This assertion used to require `in this tier [FIXTURE] 0 sales of [FIXTURE] 0 on this event`,
# which is the defect FINAL-PROOF-2 named C1 and found in 240 page states: the store holds 12
# sale rows, the same sentence named 9 excluded, and the event's own slot read zero. It now
# requires the record's count in that slot and fails on a zero, so the checker cannot pin the
# defect back in place.
check("before: the market block's event denominator is the record's count, not the mode's zero",
      "in this tier [FIXTURE] 0 sales of [FIXTURE] 12 on this event enter this decision" in b
      and "sales of [FIXTURE] 0 on this event" not in b
      and "0 sales of 0 on this event" not in b)
check("before: the at-ceiling count is refused where the mode excluded the rows",
      "at the ceiling [FIXTURE] 0" not in b
      and "no at-ceiling count while the event's own record is excluded" in b)
check("before: the market block says the mode excludes the event's rows, and the tier's share",
      "[FIXTURE] 12 recorded sales on this event are excluded by the mode, [FIXTURE] 9 of them "
      "in this tier" in b)
check("before: no primary price", "Recommended primary price" not in b)
check("before: pooled other events named",
      "pooled mean log price-to-face over 4 other events with resale" in b)

done = text(body_of("/?event=evt_syn_06"))
check("completed: counterfactual and status",
      "Decision mode: COUNTERFACTUAL" in done and "status completed" in done)

# The cap refusal is about resale. It said a recommendation above the ceiling was "a price the
# cap forbids", which reads a proportional cap as an absolute one (11-cap-capture-check 10.1).
capzero = text(body_of("/?event=evt_syn_01&capBps=0"))
check("cap refusal: the narrowed claim, not the absolute one",
      "a price the cap forbids" not in capzero
      and "decides how the resale price divides, not what the organizer may charge" in capzero)
check("cap refusal: both numbers unchanged",
      "[DECLARED] 0 bps" in capzero and "[EXACT] 1,000,000,000 lamports" in capzero)

# A status field that cannot follow the decision instant, on the instant the review named.
postcut = text(body_of("/?event=evt_syn_02&asOf=2027-06-01T00:00:00Z"))
check("post-end: the status is named as the loaded field, not the cut's",
      "status on_sale is the store" in postcut
      and "current field, not the status at this decision instant" in postcut
      and "the field and the instant disagree" in postcut)
check("post-end: the plain line is not printed for this cut", "status on_sale \u00b7 starts" not in postcut)
check("TRACE on an API route is 405 with the JSON error, not a 501 page",
      get("/api/events", "TRACE")[0] == 405 and "method_not_allowed" in get("/api/events", "TRACE")[2])
check("TRACE on a path that does not exist is still 404", get("/nope", "TRACE")[0] == 404)

lated = text(body_of("/?event=evt_syn_02&asOf=2027-06-01T00:00:00Z&mode=before_on_sale"))
check("post-end before-on-sale: the premise is not claimed as a decision it could have taken",
      "not a decision that could have been taken at that instant" in lated)

banned = ["under the deployed program", "the flat line below", "{n}", "{'value'"]
for path in ("/", "/?event=evt_syn_03", "/?event=evt_syn_04", "/?event=evt_syn_07",
             "/?event=evt_syn_02&capBps=0", "/?sim=1",
             "/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z", "/?event=evt_syn_02&mode=before_on_sale"):
    body = text(body_of(path))
    for phrase in banned:
        check(f"{path}: no {phrase!r}", phrase not in body)

print("\nFAILURES:", len(fails))
for item in fails:
    print("  ", item)
sys.exit(1 if fails else 0)
