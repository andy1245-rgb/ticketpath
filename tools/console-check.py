"""Re-check every URL the review names, against the live server on 8788."""

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
    stripped = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", stripped))


CASES = [
    ("cold-start evt_syn_03", "/?event=evt_syn_03", "GET", 200),
    ("default page", "/", "GET", 200),
    ("uncapped evt_syn_04", "/?event=evt_syn_04", "GET", 200),
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
check("before: own record excluded",
      "[FIXTURE] 0 resales on this event" in b and "[FIXTURE] 0 tickets" in b)
check("before: no primary price", "Recommended primary price" not in b)
check("before: pooled other events named",
      "pooled mean log price-to-face over 4 other events with resale" in b)

done = text(body_of("/?event=evt_syn_06"))
check("completed: counterfactual and status",
      "Decision mode: COUNTERFACTUAL" in done and "status completed" in done)

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
