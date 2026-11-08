# 39 — How a visitor is recognised, so clearing cookies does not cost them their tickets

**Written:** 2026-11-08, 05:56Z to ~07:30Z. **Event:** MLH Solana Hackathon, submission today
15:00Z, platform close 18:00Z. **Status:** research and design only. Nothing was built,
deployed, signed or spent, and nothing was committed or pushed. The operator picks the option.

**The question, in his words:** a visitor to the prototype has a hidden custodial Solana
wallet and their tickets are tokens inside it. There are no payments and no heavy accounts.
If they clear cookies they currently lose access to their own tickets. How should a visitor
be identified so that does not happen?

**What this file answers.**

1. **Phase 1** — each candidate identifier against privacy, cost, abuse and multi-account
   resistance, recovery, hackathon effort, and legal notes marked *not legal advice*. §2, §3.
2. **Phase 2** — three concrete options with a recommendation, how identity maps to the
   hidden wallet, what happens on a lost device, and what the video can show. §4.
3. **Phase 3** — an adversarial review by an agent that did not write the design: attacks,
   failure modes, a test plan, and the observations that would kill the recommendation. §5.

**What this file does not do.** It does not build, it does not choose, and it is not legal
advice. Two facts constrain every option and are stated once here rather than repeated:

- **The operator holds the wallet key.** So "losing tickets" is never a custody loss — the
  server can always re-point a ticket. It is a *record-linkage* loss: the server cannot tell
  that this browser is the same visitor as before. That reorders the whole problem, and §4
  starts from it.
- **A false match is worse than a miss.** A missed match costs a re-scan or a support
  message. A false match puts one visitor's ticket in another visitor's wallet, and on this
  platform a custody hop is a public, signed ledger entry with no rollback. No heuristic may
  merge two visitor records.

## 0. Labels, and what was read

- **MEASURED** — a named page, spec clause or source file says it, and the URL or
  `path:line` is in §7.
- **MEASURED-ABSENT** — the named pages were read and the thing is not on them. An absence
  is also a measurement, and this file uses it.
- **ASSERTED** — reasoning, no source.
- **ESTIMATE** — an hours figure with its basis stated. Never a measurement.
- **UNVERIFIED** — could not be read in this run, or read from a vendor page that blocked the
  fetcher. §8 lists every one.
- **Class A to E** — the programme's evidence classes (`RESEARCH-PROGRAM.md` §4.3). Nothing
  in this file is class A or B: no ticket-market experiment bears on how a visitor is
  recognised. It is class C where a standard or a specification says it, D where it is a
  plausible untested design claim, and E where the measurement does not exist yet.

**Machine state at the time of writing, read not assumed.** The frontend sibling
(`../ticketing-frontend`) identifies a *wallet*, not a visitor: `lib/solana.ts` freezes a
`verificationMessage()` string, `API_CONTRACT.md` documents three routes
(`GET /api/wallets/:wallet/verification`, `POST …/challenge`, `POST …/verification`) and
`ticketpath/api/wallets.py` serves them. `app/my-tickets/MyTicketsClient.tsx` reads tickets by
`ownerWallet` through `@solana/wallet-adapter`. There is **no visitor record, no session
concept and no server-side key generation** in either tree today. The hidden custodial wallet
is the premise of the question, not a shipped feature — this file assumes it because the
operator described it, and says so rather than implying it was verified.

**One machine fact changes the framing, and the adversarial reviewer found it rather than the
first draft.** There is no authentication on the read path: `GET /api/tickets?ownerWallet=`,
`/resale-history` and `/analytics` all answer without a session, and
`ticketpath/core/event_analytics.py` publishes the wallet address in the analytics payload. So a
credential gates **mutation**, while **disclosure is already open**. §5.1 is where that lands,
and §5.8 is what it changed. Read §5.8 before building anything from §4.

---

# 1. The answer in eight lines

| Candidate | Privacy | Cost at 1,000 visitors | Abuse / many identities | Recovery when the device is gone | ESTIMATE effort | Legal marker |
|---|---|---|---|---|---|---|
| **Passkey / WebAuthn** | Best in the list: no PII, credential is non-correlatable by design | **$0**, no published per-auth fee | Raises cost per identity (device + gesture, or a 2FA platform account); does **not** cap the count | Synced passkey only, via the platform account; device-bound passkey is gone | 3–6 h | Art 5(3) applies to the ceremony; the public key is ordinary personal data. *not legal advice* |
| **Email magic link** | Email is durable PII and a marketing list the moment it is reused | **$0.48** (SES, 3,000 mails) to **$20** (Resend Pro) | A mailbox per identity: cheap, not free. Aliases and disposable domains are unaddressed | **Yes, from any device** — the only candidate that truly does this | 10–14 h | The mail is a separate act from the cookie; CASL / CAN-SPAM bite on anything non-transactional. *not legal advice* |
| **Phone OTP** | Highest-value record in the list, and a SIM-swap target | **~$124** for 2,000 verifications (US) | A number costs money, so dearer than an email — but virtual numbers exist | Yes, if the number is still theirs; **no** if it was reassigned | 8–12 h + carrier registration | TCPA consent; US A2P 10DLC needs brand and campaign registration through a provider. *not legal advice* |
| **Recovery code** (printed) | No PII; a secret the operator stores hashed | $0 | None: it is issued, not claimed | **Yes**, typed on any device | 5–8 h | A credential; hashing at rest is the minimum (GDPR Art 32). *not legal advice* |
| **Claim / ticket link** | A URL is a bearer credential; it lands in logs, referrers and forwards | $0 | None | Only if kept | 6–10 h | A link a judge can paste to someone else. *not legal advice* |
| **QR at the door** | The token is on a public chain anyway | $0 | Not an identity: proves a ticket, not a person | No | 3–5 h (rotating) | Nothing specific. *not legal advice* |
| **Sign In With Solana / wallet connect** | Puts custody with the visitor and removes the operator's recovery forever | $0 for the standard | Self-custody is a real barrier to a mass-identity farmer, and irrelevant to a visitor who has no wallet | Depends entirely on their wallet's own backup | 4–8 h | Self-custody shifts the money-transmission question to the visitor. *not legal advice* |
| **Social login (Google / Apple)** | Imports a third party and exactly the "heavy account" the operator refuses | $0 Google; **$99/yr** Apple for web | **Not a sybil barrier**: a Google account is free and bulk-creatable | Yes, while the account lives | 4–6 h Google, 6–10 h Apple | A third-party controller or processor enters the picture. *not legal advice* |
| **Device fingerprint** | Needs consent for the storage and access it performs | $0 | Fails in the attacker's favour: a VM with a spoofed profile is a *fresh* identity | No | 2–4 h | Art 5(3) covers fingerprinting. *not legal advice* |

The two-line version: **nothing in the list proves a person, and nothing needs to.** The job
is to let the operator recognise a returning record without ever guessing. Email is the only
candidate that recovers across devices with no preparation; a passkey is the only one that
recovers with no personal data and no secret the operator can lose; the claim link is the base
layer both of them need.

---

# 2. Phase 1 — what each candidate actually is, with the numbers

## 2.1 Passkey / WebAuthn

**What the relying party gets.** On registration: a credential id, a public key, the AAGUID,
a signature counter, the transports, and two library-derived flags — `credentialDeviceType`
(`singleDevice` / `multiDevice`) and `credentialBackedUp`. On authentication: a signed
assertion and a new counter. No email is required: with a discoverable credential the
authenticator finds the account, and `startAuthentication({ optionsJSON, useBrowserAutofill:
true })` puts it in the browser's autofill. MEASURED (W3C WebAuthn L3 and SimpleWebAuthn docs).

**The privacy result is genuinely better than every other option**, and the spec says it in
its own words: a credential "only identifies credential key pairs and not users directly", and
authenticators deliberately make credentials "not correlatable as belonging to the same user".
Attestation is off by default when the RP asks for `attestationType: 'none'`. MEASURED, spec
§14.1 and §14.2.

**Cost: zero.** `@simplewebauthn/server` 14.1.0 and `@simplewebauthn/browser` 14.0.0 are MIT;
the browser package has zero runtime dependencies; no per-authentication fee is published by
Apple or Google. MEASURED (npm registry metadata and vendor docs). The one real cost is a
version floor: the server package documents **Node LTS 22.x and higher**.

**Abuse: it raises the price of an identity and does not cap the number.** Two claims get
conflated and only one is true. True: a registration needs a live client with an authenticator
and a user gesture, so it is much dearer to automate than an email signup. False: that it
proves one human. One person can register unlimited passkeys on unlimited accounts and the RP
cannot tell, by design. A synced passkey costs an Apple account with 2FA, or a Google account
signed into the device; a device-bound one costs a security key or a wiped device; a VM has no
platform authenticator at all, so it needs a real phone over the hybrid transport. MEASURED /
ASSERTED, itemised in `r1-passkeys.md` §Q5.

**The sharpest measured defect: the user-verification flag is not trustworthy.** passkeys.dev
maintains a table of providers that "have not implemented User Verification in a spec-compliant
manner". Verbatim rows, for `uv=required`: 1Password Extension, Bitwarden Extension,
KeepassXC Extension, Okta Personal Extension, Proton Pass Extension, Proton Pass Native,
Strongbox Native — each recorded as "Handles request without performing UV, sets UV true".
Page state: "Last Updated: Apr 09, 2026". So no business rule may depend on "a human did a
biometric gesture"; the flag proves only that a client said so.

**The defect that decides the architecture: embedded WebViews.** Android, from passkeys.dev
(page state 29 Aug 2026): "WebAuthn is currently not directly supported in embedded WebViews
on Android", while a Custom Tab has "all Web Platform features … including WebAuthn". iOS,
from Apple's own documentation: to use passkeys in a `WKWebView` the service's RP ID must be
"configured as the app's associated domains", and the app "can't use passkeys to authenticate
for services that you haven't configured as the app's associated domains". The in-app browsers
in Instagram, Facebook, LinkedIn and TikTok are `WKWebView`s on iOS and their app is not
associated with our domain. **Therefore a passkey cannot be on the first-arrival path** — and
first arrival is a ticket link opened from a messaging app. It must be an optional upgrade
offered once the visitor is already inside.

**Recovery: WebAuthn gives none.** Recovery is entirely the RP's problem: register a second
credential, fall back to another factor, or reset from the admin side. A device-bound passkey
on a lost phone is gone. A synced one returns on a new device with the same platform account.

**Effort: ESTIMATE 3–6 h** for register plus username-free authenticate on one domain, basis:
four thin route handlers (one library call each), one table with eight columns, two ~20-line
client components. Add 2–4 h if it must survive the in-app-browser problem.

**Two operational traps.** The RP ID is a registrable domain, not an origin, and changing it
later orphans every credential — pick the apex now, never a per-deploy hostname, because a
Vercel preview URL is a different registrable domain. And the ceremony needs HTTPS or
`localhost`; `rpID` must carry no trailing slash or path.

## 2.2 Email magic link

**The defect nobody warns you about, and it is deterministic per tenant.** A magic link is a
bearer token in a URL, and machinery touches that URL before the human does. Microsoft's own
documentation, verbatim: Safe Links "provides URL scanning and rewriting of inbound email
messages during mail flow", URLs "are scanned prior to message delivery, regardless of whether
the URLs are rewritten or not", and the service will "wrap, **detonate**, or otherwise
validate the 'maliciousness' of the link". A GET-consumes-the-token design is therefore dead
for any recipient inside a Defender-protected tenant: the scanner spends the token, the human
clicks a spent link, and sees an error.

**The mitigation is a design, not a workaround:** the emailed URL is a GET of a landing page
that renders a form and consumes nothing; a human button press POSTs the token to consume it.
Scanners do not submit forms. Consequences to build in: "single-use" means single *POST*, the
landing page must not leak the token in a referrer, and the POST needs CSRF protection or it
becomes login-CSRF.

**Cost, measured from the providers' own pages (read 2026-11-08).** Amazon SES $0.16 per
1,000 (0–10M/month), with a production-access request needed: the sandbox allows only verified
recipients, 200 messages per 24 h, 1 per second. Resend free: 3,000/month but **100/day**, so
3,000 in one event day forces an upgrade; Resend Pro $20/month for 50,000. Postmark $15/month
for 10,000. Worked example, 1,000 visitors × 3 emails: **$0.48 on SES**, **$20 on Resend Pro**,
**$15 on Postmark**.

**NIST's current text explicitly permits this use.** SP 800-63B-4, build stamp 26 Aug 2025,
says "Email SHALL NOT be used for out-of-band authentication", and immediately afterwards:
"Confirmation codes that are sent to validate email addresses or are issued as recovery codes
(see Sec. 4.2.1.2) are not authentication processes and not affected by the above
prohibition." A ticket-recovery handle is not an authenticator. MEASURED, quoted verbatim.

**Abuse.** A mailbox per identity is cheap but not free, and a disposable-mail domain is
trivial; nothing in the providers' pages read addresses that. A verified address is a *little*
stickier than an unverified one, and the round trip is the only verification that exists here.
Weak sybil resistance, honestly stated.

**Legal.** *not legal advice.* The session cookie sits under ePrivacy Art 5(3) with "strictly
necessary in order to provide an information society service explicitly requested by the
subscriber" as the only available exemption. CASL s. 6(1) prohibits a commercial electronic
message without consent and s. 6(2) requires sender identification, contact details and an
unsubscribe; a login link is arguably not a CEM, but any second email ("your event is
tomorrow") certainly is. Data that outlives the event is a marketing list — a product decision
that must be taken deliberately, not a side effect.

## 2.3 Phone OTP

**Cost, measured:** Twilio Verify **$0.05 per successful verification** plus **$0.0083 per
SMS** (US), with attempts always charged and failures not charged the base fee. For 1,000
visitors × 2 verifications that is roughly **$124**, against **$0.48** for the equivalent
email volume — about 258 times the price.

**The same-day blocker is not price, it is registration.** US application-to-person messaging
requires 10DLC brand and campaign registration; The Campaign Registry's own page states that
10DLC is a channel "in which Brands and Campaign Service Providers (CSPs) are verified prior to
being allowed to send messages" and that "direct registration with TCR is not available for
Brands". A CSP must register you, and that is a review, not a button.

**NIST restricts it.** "The use of the PSTN for out-of-band verification is restricted"
(Sec. 3.1.3.3), "there is one restricted authenticator: the use of the PSTN for out-of-band
authentication" (Sec. 3.2.9), verifiers "SHOULD consider risk indicators (e.g., device swap,
SIM change, number porting)" and "SHALL ensure that alternative authenticator types are
available". So if SMS ships at all, an unrestricted alternative has to ship with it.

**The structural defect for a wallet.** Numbers are reassigned. Keying a wallet to a phone
number means the number's next owner can be handed the previous owner's tickets, and NIST's
own risk-indicator list is a description of that failure. That alone disqualifies phone as the
*only* handle.

## 2.4 Recovery code and claim link

**These are two different credentials and conflating them is the classic bug.** NIST
SP 800-63B treats a saved recovery code as an authenticator secret "used successfully only
once" (Sec. 3.1.2.2) and requires a used one to be invalidated and replaced (Sec. 4.2.1.1);
OWASP requires reset tokens to be "single use and expire after an appropriate period". Neither
sanctions one artefact that is both a login and a transfer. On this platform the difference is
concrete: a forwarded link that both recovers a session and moves a ticket performs a transfer
the sender may not have intended, and the ledger records it permanently as a signed fact.

**Entropy arithmetic.** 128 random bits, base64url, is 22 characters and unguessable
(2^128 ≈ 3.4 × 10^38). A human-typed code is a different problem: the constraint is not the
attacker's compute but how many characters a person will retype without error. Six decimal
digits is 19.9 bits and is legal only *because* throttling applies. The practical construction
is a 16-character Crockford Base32 code (80 bits) in four groups, normalised before lookup,
with an attempt budget and a lockout — Crockford folds I/L→1 and O→0 so transcription stays
decodable. Crockford is not named by any standards body; it is an engineering choice.

**TTL.** No standard gives a number for a recovery *link*: NIST's 30-day / 24-hour / 12-hour
figures are session reauthentication ceilings, and OWASP says only "an appropriate period".
MEASURED-ABSENT. The honest rule is TTL bounded by the event horizon, plus a one-click reissue
from a live session.

## 2.5 QR and ticket link at the door

Static versus rotating, and the rotation mechanism is RFC 6238 TOTP (or RFC 4226 HOTP) with
published test vectors — 3–5 h of work including the door-side screen and the single-use
record. A screenshot defeats a static code and does not defeat a rotating one. But the more
important finding is conceptual: **no standard defines what a scanned ticket code means** —
not NIST, not the RFCs, not Apple, not Google (MEASURED-ABSENT). A QR is an authorisation to
redeem, not an identity. It proves possession of a ticket, never of a person.

## 2.6 Sign In With Solana, wallet connect, and embedded wallets

**What SIWS actually is, stated precisely because the sloppy version is wrong.** There is no
ratified Solana Foundation standard document. What exists is (a) the **interface**: a wallet
feature named `solana:signIn` in `solana-labs/wallet-standard`, versions `1.0.0` and `1.1.0`,
derived — its own comment says so — from EIP-4361 and CAIP-122; and (b) the **wire format**:
the ABNF in `phantom/sign-in-with-solana`'s README, which *is* the spec in practice. No SIMD,
no Foundation ratification record was found (MEASURED-ABSENT). Do not call it "Solana's
standard" on the video. The wallet, not the dapp, composes the message; the dapp passes
`domain`, `address`, `statement`, `uri`, `version`, `chainId`, `nonce` (at least 8 alphanumeric
characters), `issuedAt` and the rest; the wallet returns
`{ account, signedMessage, signature, signatureType }`.

**The consequence for this product.** A visitor who brings Phantom keeps their keys, and
nothing is lost when cookies clear — but they also have to install an extension, keep a seed
phrase, and the product premise (a wallet made for them, zero setup) is gone. That is a
different product, not a different login.

**Embedded wallet providers, published prices (all read 2026-11-08).** Privy: free 0–499 MAU,
Core $299/month to 2,499 MAU, passkey signup and login documented. Turnkey: pay-as-you-go
$0.10 per signature with 25 free signatures and 1,000 free wallets, keys generated and used
inside attested TEEs, seed export available and permanently recorded, card required past 25
signatures. Web3Auth: free 1,000 monthly active wallets, $0.050 each after; now under a
Consensys banner. Crossmint: 5,000 MAW free then $0.01/MAW, non-custodial, passkey signers,
key export included. Coinbase: $0.005 per wallet operation, 5,000 free operations/month.
Dynamic: $249/month self-serve to 5,000 MAU.

**And the observation that makes all of that optional.** The wallet is already custodial and
the server holds the key. So the wallet is not an identity factor at all: the provider's own
login is the identity, and the wallet address is a record keyed by it. Adding Privy or Turnkey
would buy a better key-management story, not a better identity story, and at 1,000 visitors the
price spread ($0 to $299/month) is smaller than the integration cost.

## 2.7 Social login

**What the RP gets.** Google OpenID Connect: a `sub` that is per-client, plus `email` and
`email_verified`; the default scopes (`openid email profile`) are non-sensitive, so no
verification review is needed — Google's own page: "For the authentication, default scope
(email, profile, openid) is sufficient, you don't need to add any sensitive scopes". Apple:
a `sub`, an optional private-relay address with `is_private_email`, and name and email only on
the first authorisation. Apple on the web needs a Services ID, a key and an **Apple Developer
Program membership at 99 USD per membership year** (Apple's own enrolment page).

**The finding that matters here:** Google's OAuth policy forbids exactly the situation this
product lives in. Verbatim: "A developer must not direct a Google OAuth 2.0 authorization
request to an embedded user-agent under the developer's control", and its own remediation page
calls WebView auth "not recommended" and points to Chrome Custom Tabs. Ticket links open in
in-app browsers. So social login is also not a first-arrival gate, for the same reason a
passkey is not.

**Abuse: not a sybil barrier.** A Google account is free and bulk-creatable; no primary page
establishing Google's abuse posture on account creation was reached in this run, so the claim
is ASSERTED and flagged. Apple costs a device and an Apple Account, which is a real but modest
step up. Social login buys convenience and an email address, not uniqueness.

## 2.8 Device fingerprint, and why it fails

**The entropy is fine and that is not the problem.** Eckersley's PETS 2010 measurement:
**18.1 bits** of entropy for a general browser fingerprint and **18.8** with plugins and fonts,
over 470,161 instances, with 83.6% and 94.2% of browsers unique in the two populations, a
**37.4%** change rate over the study window, and a 99.1% correct-guess rate at a 0.87% false
positive rate. The "34 bits" figure that circulates is **not in the primary source**
(MEASURED-ABSENT). For 2,000 visitors, log2(2000) ≈ 11 bits is all the entropy needed.

**The problem is stability, and the numbers are worse than the entropy is good.** 37.4% of
returning visitors arrive with a changed fingerprint. WebKit caps script-writable storage at
**7 days** without user interaction, caps a JavaScript-set cookie after link decoration at
**24 hours**, and deletes data for classified domains after 30 days of browser use with no
first-party interaction (MEASURED, webkit.org/tracking-prevention). A ticket issued three
weeks before the event is outside every one of those windows on the platform most attendees
will use.

**It fails in the attacker's direction too.** A fingerprint is a *fresh* identity to anyone who
wants one: a VM with a spoofed canvas and WebGL profile defeats the signal, which is the
opposite of what a sybil defence needs.

**And it needs consent.** The EDPB's Guidelines 2/2023 on the technical scope of Art 5(3) are
final, version 2.0, dated 16 October 2024 (MEASURED; the sentence that covers fingerprinting is
UNVERIFIED because the PDF would not download). Recognising a visitor who has not identified
themselves is not "strictly necessary" for a service they requested.

**Verdict: a supporting hint at most, never a key.** If it is used, it ranks "is this you?"
candidates for a one-tap confirmation and never authorises anything on its own. A 0.56%
wrong-guess rate on a 2,000-person event is about 11 people receiving someone else's tickets.

## 2.9 The custody question, because it will be asked

*not legal advice.* FinCEN's 2019 guidance on convertible virtual currency defines money
transmission as "the acceptance of currency, funds, or other value that substitutes for
currency from one person and the transmission of … to another location or person by any means".
**The word "ticket" does not appear as an addressed business model** (MEASURED-ABSENT). A
server that generates a keypair, receives nothing into it, and mints a free non-transferable
admission token satisfies neither element: no acceptance from a person, no transmission to a
different person, no value substituting for currency. On the sources read, that is not money
transmission and not stored value — a reading of two elements against a fact pattern the
guidance does not discuss.

**The reading breaks the moment any of four things becomes true:** a visitor pays and the
operator holds the money; a ticket becomes freely transferable and a secondary price settles
through the operator's key; the operator accepts deposits into the custodial wallet; or the
operator cashes anyone out. A prototype doing none of the four is on the safe side of the line;
one doing any of them needs a lawyer, not a paragraph. The Canadian question is open: FINTRAC's
page 404'd and no Canadian statement is made here.

---

# 3. What Phase 1 establishes, and what it cannot

**Established, and safe to build on:**

1. A passkey cannot gate first arrival, because ticket links open in in-app browsers and
   WebAuthn is documented not to work there. (MEASURED, Apple and passkeys.dev.)
2. A GET-consumes-the-token magic link is broken for any Defender-protected recipient. The
   POST-consume pattern is the fix. (MEASURED, Microsoft Learn.)
3. Email as a recovery handle is inside NIST's own carve-out; SMS is the restricted
   authenticator, and SMS to arbitrary US numbers needs 10DLC registration first. (MEASURED.)
4. Fingerprinting is unstable over exactly the horizon a ticket needs, and it is a consent
   problem, and a false match is unrecoverable. (MEASURED numbers, ASSERTED combination.)
5. Nothing in the candidate list proves a unique person, and nothing here needs to. The
   anti-scalping question is a different question from the returning-visitor question.

**Not established, and no source in this run settles it:**

- Whether any identity scheme actually reduces scalping on a free, non-transferable ticket.
  There is no purchase to gate and no allocation per identity, so "multi-account resistance"
  in this product is mostly about *resale*, and resale is handled by the on-chain cap.
- What a panic-resistant account-recovery UX costs in support load. No published figure.
- Whether the numbers on passkey conversion in real consumer flows exist. MEASURED-ABSENT;
  do not quote one.

---

# 4. Phase 2 — the premise that decides the design

The server holds the wallet keypair. Therefore:

1. The wallet is not custody and not an identity. It is a row owned by a visitor record. Any
   artefact the operator controls the server side of — a link, a code, a passkey, an email —
   is sufficient. The bar is not "unforgeable against the whole internet"; it is "not guessable
   by another visitor, and not transferable by accident".
2. A false match is worse than a miss, so **no heuristic ever merges two visitor records**, and
   no credential is ever the thing the wallet is keyed to.

## 4.1 The shared spine (all three options)

- `visitor` is the root record. One hidden Solana keypair per visitor, generated server-side,
  encrypted at rest, address recorded.
- Credentials attach to `visitor` as separate rows:
  `(kind, secret_hash_or_public_key, created_at, last_used, device_hint)`.
  Kinds: `claim_link`, `passkey`, `recovery_code`, `email`.
- A credential is a pointer to `visitor`. **The wallet is never keyed to a credential**, so
  rotating or deleting one cannot orphan a ticket.
- Two artefacts with two jobs, never conflated: a **recovery credential** is reusable, starts a
  session and never moves a ticket; a **claim/transfer credential** is single use, consumed by
  a POST, and may move exactly one ticket.
- Every link: GET renders and consumes nothing; POST consumes. TTL bounded by the event, with
  one-click reissue from a live session.

## 4.2 Option 1 — the ticket link is the identity (link only)

One 128-bit base64url pass link per visitor, plus one per ticket. Hash at rest. New device =
paste the link. `sha256(token) → visitor → wallet`.

- Cost **$0**. Effort **ESTIMATE 6–10 h**. PII: none.
- Multi-account: unlimited — a new visit is a new wallet and a new link.
- Lost device: works if the link was kept (message to self, bookmark, the organiser's email
  that does not exist). If every link is gone there is no recovery, and the page has to say so.
- **Verdict: this is the base layer both other options need, and on its own it fails the
  operator's own test** — the common failure is a visitor who closed the tab.

## 4.3 Option 2 — ticket link plus email recovery link

The spine, plus one optional verified email. "Email me my link" issues a single-use 128-bit
token; the email is the durable handle. `lower(email) → visitor → wallet`, unique.

- Lost device: same email, new link, tickets back, from any device.
- Multi-account: a mailbox per identity. Cheap at small scale (aliases, disposable domains), so
  it raises cost per identity without capping the count. Say that on the page.
- Cost: **$0.48** (SES, 3,000 mails, sandbox constraints) to **$20/month** (Resend Pro). A
  domain with DKIM is required, which is the same-day risk.
- Effort **ESTIMATE 10–14 h**.
- **Verdict: the only option that works on a brand-new device with no preparation.** It is also
  the option that turns the prototype into the owner of a mailing list, which is a decision,
  not a side effect.

## 4.4 Option 3 — zero PII: ticket link, device passkey, printed recovery code (recommended)

The spine, plus an optional passkey offered *after* the visitor is inside ("keep these tickets
on this device"), plus a 16-character Crockford Base32 recovery code (80 bits) shown once as a
card and required when a device is gone.

- `credential_id → visitor → wallet` for the passkey; a salted password hash of the code →
  visitor. **No personal data stored.** The hash must be a real password scheme with a salt of
  at least 32 bits (NIST SP 800-63B, look-up secrets: below 112 bits they "SHALL be stored in a
  salted and hashed form using a suitable password hashing scheme"); a bare `sha256` of an
  80-bit code does not satisfy it.
- Lost device: a synced passkey returns on a new device with the same platform account; a
  device-bound passkey does not; the printed code restores anywhere, throttled and
  single-use-then-replaced.
- The passkey is an upgrade, never a gate, because of §2.1's WebView measurement.
- Multi-account: a passkey costs a device and a gesture, a synced one costs a 2FA platform
  account. It raises the price and does not cap the count. No rule may depend on the `uv` flag.
- Cost **$0**, no published per-auth fee. The real cost is the Node 22 floor for
  `@simplewebauthn/server` 14.1.0.
- Effort **ESTIMATE** 3–6 h passkey + 5–8 h code, **on top of the 6–10 h spine** = 14–24 h in
  total. The first draft added only the two new artefacts and understated the option; §5.3 has
  the correction and §5.8 what it changed.
- **Verdict as written: recommended for the demo.** It is the only option whose recovery does not depend
  on a stored secret the operator can lose, it stores no personal data, it needs no third-party
  account and no card, and "clear your cookies, keep your tickets" is exactly the same-device
  case a passkey solves. Its gap is stated plainly rather than hidden: a visitor on a new
  device, with no synced platform account and no printed code, is unrecoverable.

## 4.5 Recommendation, and the order to build it

**Option 3 for the demo**, in this order: claim link (the base, and the only thing that has to
work) → passkey (the visible beat) → recovery code card if the hours allow. **Add Option 2's
email path when a domain and a privacy note exist**, because it is the only cross-device
guarantee, and the demo can say "next" honestly instead of implying it.

**But read §5.8 before acting on this section.** The review corrected the effort total (14–24 h,
not 8–14 h), found that reads are unauthenticated so no credential is a gate, and made this
recommendation conditional on the demo having a stable apex domain. The revised call, the
condition, and the one fix that must happen whichever option is chosen are there, not here:
this section is the design as it was reviewed, kept unedited on purpose.

**The alternative reading, so the operator can overrule it.** If the pitch is "nobody ever
loses a ticket", Option 2 is the only honest claim, and Option 3 is the honest *privacy*
claim. Those are two different products and the choice between them is his.

## 4.6 How identity maps to the hidden wallet

```
visitor ──1:1──► solana keypair (server-held, encrypted at rest, address on chain)
   │
   ├── credential(kind=claim_link,    sha256(token))
   ├── credential(kind=passkey,       credential_id + public_key + counter)
   ├── credential(kind=recovery_code, argon2id(code, salt))   # salted: 80 bits < 112
   └── credential(kind=email,         lower(email) unique)          [option 2 only]

ticket ── owned by ──► wallet address ── side effect of ──► visitor
```

Rules that fall out of the diagram and are the whole safety argument:

- Deleting or rotating any credential is a session concern only. Tickets do not move, and the
  wallet address does not change — so an audit of the ledger and an audit of the visitor record
  never contradict each other.
- Adding a second credential to an existing visitor requires a **live session**. There is no
  "add an email by typing an email"; that path is how one person's address gets attached to
  another person's tickets.
- A credential is unique per visitor and a visitor may have several. Two credentials resolving
  to two visitors is *never* auto-merged, even if their emails match; it is a support case.

## 4.7 What happens on a lost device

| Case | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| Cookies cleared, same browser | claim link | email link | **passkey** |
| New browser, same device | claim link | email link | **passkey** |
| New device, same platform account | claim link | email link | synced passkey |
| New device, nothing kept | nothing | **email link** | printed code |
| Everything gone | support, no proof | support, email proof | support, no proof |

The two open cells are the honest limits. Option 3's "support, no proof" is the price of
storing nothing; Option 2's is the price of the mailbox being the account.

## 4.8 What the video can show

1. **0:00–0:20** — open the ticket link on a phone: two tickets, no signup, no wallet popup.
2. **0:20–0:35** — "keep these on this device" → Face ID → done.
3. **0:35–0:55** — **clear cookies on camera**, reload, tickets gone, tap "sign in with
   passkey", Face ID, tickets back. This is the beat that answers the question, and it is
   impossible to fake convincingly.
4. **0:55–1:10** — a second browser: paste the claim link, tickets appear.
5. **1:10–1:25** — the printed recovery code typed into a fresh browser.
6. **1:25–2:00** — cut to the ledger: the wallet, the ticket, the cap refusal on chain.

**What the video cannot show:** an email link without a real domain and a real mailbox; a
Wallet pass without an Apple certificate; and any claim about scalpers being stopped, because
nothing here measures that.

---

# 5. Phase 3 — adversarial review

**The reviewer did not write the design.** It read the design, the six research files and both
trees, and its brief was to break the thing. Its verdict, verbatim in substance:

1. The design's central premise is false against the repository it is being built into. The
   credential is not the gate to the tickets: reads are unauthenticated.
2. Option 3 is the most expensive option presented as the cheapest, because its effort figure
   omits the claim-link spine it sits on. The honest total is 14–24 h against about 8 h left.
3. Option 3's centrepiece beat is an artefact the research says cannot be on the arrival path.
4. The wallet mapping survives credential deletion and dies on registration races, a
   non-atomic claim, a second-device passkey overwrite, and a code whose replacement has
   nowhere to go.
5. **Recommendation: do not ship option 3 today.**

§5.1 to §5.7 are the reviewer's findings. §5.8 is what the orchestrator did with them, including
where it disagreed.

## 5.1 The finding that reframes the whole question

**The read path is unauthenticated.** `ticketpath/server.py` has no authentication anywhere:
`GET /api/tickets?ownerWallet=`, `GET /api/tickets/:id/resale-history` and
`GET /api/events/:id/analytics` all answer without a session, and `ticketpath/core/event_analytics.py`
puts the wallet address in the public payload (`top_destinations`, key `wallet`). Verified in
this tree, not taken on trust.

Three consequences, and they are not small:

- Every credential in all three options guards **mutation only**, while **disclosure is open**.
  A stranger who learns one address can list that visitor's tickets, their whole resale trail,
  and every co-holder of the event.
- **"Zero PII" is false as shipped.** The wallet address is published with the analytics, and
  the address is exactly the join key between the private visitor record and the permanent
  public ledger. "No email address stored" is defensible; "zero PII" is not.
- The question "how do we recognise the returning visitor" is really two questions: who may
  **see**, and who may **move**. The research and this design answered only the second.

## 5.2 Attacks that survived, per option

**Option 1 (link only).** The strongest attacks: the address is publishable, so the link is not
the gate; a link in a URL path leaks through `Referer` without `Referrer-Policy: no-referrer`;
the token table lives in process memory today (`ticketpath/core/wallet_verification.py` says so
in its own header), so every link dies on restart or on a second instance; and the claim-link
state machine has no `issued → reserved → moved` stage, so a token can be consumed before the
chain write lands and the ticket moves nowhere.

**Option 2 (email).** Attacks that survived: Safe Links will also bind a CSRF nonce to the
scanner's cookie jar, which breaks the POST mitigation if the nonce is minted on the GET (the
research's own §2.4 requires the POST to carry a same-session value — the design quoted the
first half of the mitigation and dropped the second); SES sandbox and a cold sending domain
mean the mail does not arrive in front of a judge; `lower(email)` merges two humans who share
an address; and an address kept past the event is a marketing list with a consent problem
attached. The review's own view: option 2 is obviously correct for a paid, mobile, chat-arrived
buyer and obviously wrong for a privacy-first house policy.

**Option 3 (passkey + code).** Attacks that survived: a second-device registration with the
same WebAuthn `user.id` **overwrites the first credential** on Apple platforms, so the device it
worked on yesterday stops working; a recovery code used by someone else locks the owner out
permanently, because NIST requires the used code to be replaced and the replacement has nowhere
to go when the user has no session; a throttle keyed on IP locks the whole venue after one
attacker's guesses; a code delivered as a screenshot syncs to the same platform account as the
synced passkey and is therefore not an independent factor; and the effort figure omits the
spine (§5.3).

**Six more, and these are the ones that change behaviour rather than tidy the prose.** §5.2 is a
selection; the reviewer wrote 29 attacks and these are the six with consequences the table does
not already carry.

- **The link is a transfer credential used as a login (its sharpest single finding).** The spine
  says recovery and transfer are two different artefacts. Option 1 has one artefact and uses it
  for both: a visitor who forwards their pass link to a friend so the friend can collect a
  ticket has logged the friend in as themselves, and the friend can now transfer every other
  ticket. The on-chain record shows transfers signed by the original wallet with no trace of who
  pressed the button. If option 1 ships, the per-ticket link must be provably unable to mint a
  session, and that distinction has to be in the token, not in a comment.
- **"Everything gone" is the modal case, not the edge case.** The visitor opened the link once,
  in Instagram, three weeks ago; the DM has scrolled, there is no mail, there is no bookmark. A
  page that says "you have lost your tickets permanently" at a venue door is a worse outcome
  than a support queue, and option 3 inherits that row because option 1 is its base.
- **Reissue is not revocation.** A mail archive compromise mints a session for the life of the
  visitor. "One-click reissue from a live session" leaves the old link working and requires the
  very session the victim does not have. Revocation is a separate verb and has to exist.
- **The email endpoint is an enumeration oracle.** If `POST /auth/email` differs in response or
  latency between "holds a ticket" and "unknown", it answers "does this person hold a ticket"
  for any address, which is a speaker list and a targeting list. Identical response and
  identical latency, always.
- **A passkey registered in a borrowed browser profile is a silent privilege escalation.** On a
  shared desktop, or a Chrome profile signed into someone else's Google account, the credential
  syncs to that person's devices and authenticates as the visitor indefinitely. `device_hint`
  records a hint, not a human. "Keep these tickets on this device" is a promise the platform
  cannot keep once the credential manager syncs.
- **There is no idempotency key on registration.** `ticketpath/server.py` is a
  `ThreadingHTTPServer` and the only lock in the tree guards the nonce dict, so a double submit
  can create two visitor rows, two wallets and two links, and the browser holds only one of
  them. One hidden keypair per visitor is only true if the insert is unique and idempotent.

## 5.3 The effort correction, which is the one that changes the decision

The design added 3–6 h (passkey) to 5–8 h (code) and called it 8–14 h. But option 3 contains
option 1's spine, which the same file prices at 6–10 h. **The honest total is 14–24 h.** With
about eight hours left, that decides it: at most one new artefact ships, and the spine has to
be budgeted first.

## 5.4 Citation audit

The reviewer checked every load-bearing citation against the research files. Correct as quoted:
the Safe Links pre-delivery scan, the Android and iOS WebView limits, the passkeys.dev
user-verification table, the 80-bit Crockford arithmetic, the 128-bit link arithmetic, the three
email prices, the SimpleWebAuthn version and Node floor, and the SES sandbox rules. Two were
wrong in use:

- **`sha256(code)` for an 80-bit code violates the clause the research itself quotes.** Below
  112 bits, NIST requires "a salted and hashed form using a suitable password hashing scheme",
  salt "at least 32 bits". An 80-bit code is below 112, so the clause applies verbatim; a bare
  `sha256` does not satisfy it. Fixed in §4.4 and §4.6.
- **"Zero PII" is false** (§5.1), and the claimed protection ("a credential deletion cannot
  orphan a ticket") is true and irrelevant to any of the surviving attacks.

## 5.5 Wallet-mapping attacks

- **Concurrent registration:** two browsers registering at once produce two credentials for one
  visitor — fine — but two visitors for one browser if the session is not durable.
- **Second-device passkey:** with one `user.id` per visitor, Apple overwrites; with one per
  credential, discoverable login still works and nothing is overwritten. The design did not
  say which, and that omission is the bug.
- **Claim race:** the token must be reserved before the chain write, and released if the write
  fails, or the visitor is told "already used" while the ticket has moved nowhere.
- **Support re-point:** today the only proof a visitor can offer is the ticket serial, which is
  printed on the ticket being stolen. A re-point needs the claim link or a live session, and
  the reason must be written on the ledger row.
- **`requiresVerifiedWallet` versus a hidden wallet:** `lib/types.ts` gates transfers on a
  verified wallet, and verification is a nonce-plus-signature challenge. A hidden custodial
  wallet has no key the visitor can sign with, so it can **never** satisfy that challenge. The
  event type and the wallet model are currently incompatible and somebody has to decide which
  bends.

## 5.6 Failure modes, with severity

**DEMO** blocks the demo · **TICKET** loses a ticket · **DATA** leaks · **COSMETIC**.

| # | Trigger | Symptom | Who notices | Severity | Cheapest mitigation |
|---|---|---|---|---|---|
| 1 | Read path unauthenticated | none; tickets render for any address | nobody until someone looks | **DATA** | Session-gate ticket reads; replace `wallet` in public payloads with a per-event pseudonym |
| 2 | Live URL is a per-deploy host | passkey sign-in fails after any redeploy | the judge | **DEMO** | Bind to the apex before the first registration |
| 3 | iOS in-app browser | passkey prompt never appears | the visitor, silently | **DEMO** | Detect the WebView, render the link path, never gate on the passkey |
| 4 | Second-device registration overwrites the first passkey | sign-in fails on the device it worked on | the visitor | **TICKET** | One `user.id` per credential, cap per visitor, show the list |
| 5 | Recovery code used by someone else | owner locked out, attacker holds the only live code | the victim, too late | **TICKET** | Deliver the replacement only into a session that existed before use; notify |
| 6 | Claim token consumed before the chain write fails | "already used", ticket moved nowhere | both humans, at the door | **TICKET** | `issued → reserved → moved`, release on failure |
| 7 | Throttle keyed on IP | the whole venue locks out after one attacker | everyone on the venue wifi | **DEMO** | Drop the IP bucket; 80 bits plus a per-token budget is enough |
| 8 | Token in the path, no `Referrer-Policy` | none | nobody | **DATA** | `no-referrer` on the landing route; token in the fragment or the POST body |
| 9 | Credential/attempt state in process memory | every unconsumed link and code dies on restart | the visitor, at the door | **TICKET** | One durable store for visitors, credentials, attempts |
| 10 | Fixture mode during filming | the "tickets gone" beat does not reproduce | the person recording | **DEMO** | Pin the demo to the live backend and assert the mode on screen |
| 11 | Safe Links binds the CSRF nonce to the scanner | "link expired" on the first human click | every Defender-tenant visitor | **DEMO** | Mint the POST nonce on the POST, or accept a nonce minted for the token |
| 12 | SES sandbox or a cold domain | mail never arrives | the judge | **DEMO** | Do not put email on the demo path |
| 13 | Shared family device | a household member sees the portfolio | nobody appropriate | **DATA** | Say it aloud; add a "this device" note and sign-out-everywhere |
| 14 | Support re-points a ticket on a serial | ticket gone | the victim | **TICKET** | Require the claim link or a live session; log a reason |
| 15 | `lower(email)` shared by two humans | two people are one visitor | both | **TICKET** | Do not key on email for the demo |
| 16 | Hidden wallet on a `requiresVerifiedWallet` event | transfer refused forever | the organiser | **TICKET** | Decide: server-verified by fiat, or the gate is organisation-only |

## 5.7 Test plan

The backend exposes `make_server(port, host, orchestrator)`, so the adversarial cases run
in-process with no network. Frontend cases need `next dev` plus Playwright with a virtual
authenticator.

**Backend, automatable today:**

| # | Scenario | Assertion |
|---|---|---|
| B1 | two `POST /api/claim/<token>` in parallel threads | exactly one 200; the other 409 `token_reserved`; exactly one ledger row |
| B2 | claim whose transfer leg is stubbed to fail | token returns to `issued`; a retry succeeds; nothing orphaned |
| B3 | `GET /api/claim/<token>` twenty times | 200 twenty times, token still `issued`, no `last_used` write |
| B4 | scanner simulation: GET with one cookie jar, human GET plus POST with another | the human's POST succeeds (the §5.2 regression) |
| B5 | wrong recovery code × N, with a second visitor on the same IP | first throttled, second untouched (the IP-bucket regression) |
| B6 | correct recovery code | session minted, old code dead, replacement goes only to a pre-existing session |
| B7 | two registrations from one browser in parallel | one visitor, one wallet, one link |
| B8 | `GET /api/tickets?ownerWallet=X` with no session | 401 once reads are gated — today it is 200, and that is the proof of finding 1 |

**Frontend, needs a browser:** passkey register then authenticate; clear all site data then
authenticate (the demo beat); two passes on the same visitor; a WebView user agent falling back
to the link path; a forwarded claim link opened in a second profile; a code typed on a fresh
profile with the wrong code five times and then the right one.

## 5.8 What the orchestrator changed, and where it disagreed

**Adopted, all of it:** the read-path finding (§5.1) and the fix; the effort correction (§5.3);
the salted-hash correction; the `issued → reserved → moved` state machine; one `user.id` per
credential; the IP-throttle removal; `Referrer-Policy` and the token out of the path; the
`requiresVerifiedWallet` conflict; the durable store as a precondition rather than an
afterthought; a real revocation verb rather than reissue; identical response and latency on
the email endpoint; a unique, idempotent insert for the visitor row; and the "the passkey is an
upgrade, never a gate" rule, which the review confirmed with the two vendor sources.

**Disagreed, on evidence, and the operator should see both.** The review's ordering is claim
link → printed code card → stop. I would ship claim link → **passkey** → stop, for three
reasons:

1. **The question asked is cookie clearing, and the passkey is the answer to it.** The printed
   card answers a different question (device loss). §4.8's third beat is the one the operator
   asked for.
2. **The passkey is the cheaper artefact, not the dearer one.** 3–6 h against the card's 5–8 h.
   The review's ordering spends more hours on the less on-point beat.
3. **One of the review's three passkey risks is not real in this tree.** It lists the Node 22
   floor as a cost; the frontend already declares `@types/node ^22` and the local runtime is
   Node 24. The floor is satisfied.

The two risks that *are* real are the same two the review names: **the domain** and **the
in-app browser**. So the revision is conditional, and the condition is a fact I do not have:

- **If the demo runs on a stable apex domain**, the passkey ships. It is offered inside the
  page, never as a gate, and the fallback copy on a WebView is part of the work.
- **If the live URL is a per-deploy host or a preview URL**, the passkey is off — credentials
  die at the next deploy — and the printed card is the fallback beat, exactly as the review
  ordered.

**And the one thing that must happen regardless of which option is picked:** the read path gets
session-gated and the wallet leaves the public payload. Until that is true, no identity scheme
in this file guards anything a stranger cannot already read, and saying "your tickets are safe"
on camera would be a claim the system does not support.

---

# 6. What is left for the operator to decide

1. **Which claim the demo makes.** "Your tickets survive a cleared cookie, and we store no
   email and no phone number" (Option 3) or "you can never lose a ticket, from any device,
   ever" (Option 2). They are different products; §4.5 says why, and both are defensible. Note
   the wording: "zero PII" is not available (§5.1 — the wallet address is published with the
   analytics), so the honest claim is about what is *stored*, not about what is *public*.
2. **Whether an email address may outlive the event.** That single decision turns the
   prototype into a marketing list and moves CASL, CAN-SPAM and GDPR retention into scope.
3. **Whether a real domain and DNS are available today.** Option 2 cannot ship a link that
   reaches a real inbox without one, and the sandbox rules on SES make "just use SES" false.
4. **Whether the email path ships at all for the demo**, given the measured same-day risk, or
   is described as the next step on camera.
5. **Whether the operator wants the recovery-code card printed on camera.** It is the only
   artefact in Option 3 that a judge can hold, and it is 5–8 h of work.

**What this file does not decide:** any of the above. It records what the sources say, what
each option costs in hours and in privacy, what the adversarial reviewer broke, and where the
evidence stops.

---

# 7. Sources

Every row was read on 2026-11-08 unless the row says otherwise. Where a page is listed here as
blocked, that is a measurement and §8 carries it.

## Standards and specifications

| Source | What it establishes |
|---|---|
| `w3.org/TR/webauthn-3/` (WebAuthn Level 3), §5.1.3, §5.8.4, §14.1, §14.2 | RP ID is a registrable domain and a mismatch throws `SecurityError`; `internal` transport means a platform authenticator not removable from the device; the list of "potentially correlatable identifiers"; credentials "only identify credential key pairs and not users directly" and are "not correlatable as belonging to the same user" |
| `pages.nist.gov/800-63-4/sp800-63b.html` (SP 800-63B-4, build stamp 26 Aug 2025) | PSTN out-of-band is the only restricted authenticator (§3.1.3.3, §3.2.9); SIM-swap and porting risk indicators; "Email SHALL NOT be used for out-of-band authentication" and the carve-out for "confirmation codes that are sent to validate email addresses or are issued as recovery codes"; saved recovery codes are single-use and replaced (§3.1.2.2, §4.2.1.1) |
| `eur-lex.europa.eu` ePrivacy Directive 2002/58/EC, Art. 5(3) and Art. 13 | Storage and access on a terminal device needs consent unless strictly necessary for a service the user requested; direct marketing by electronic mail needs prior consent |
| `laws-lois.justice.gc.ca/eng/acts/E-1.6/section-6.html` (CASL s. 6) | Prohibition on a commercial electronic message without consent; sender identification, contact information and unsubscribe required |
| `edpb.europa.eu/…/guidelines-22023-technical-scope-art-53-eprivacy-directive_en` | EDPB Guidelines 2/2023 exist, final version 2.0 dated 16 October 2024 |
| `coveryourtracks.eff.org/static/browser-uniqueness.pdf` (Eckersley, PETS 2010) | 18.1 bits general / 18.8 with plugins and fonts; 470,161 instances; 83.6% and 94.2% unique; 37.4% change rate; 99.1% correct guesses at 0.87% false positives; the 15–20-bit sufficiency argument |
| `webkit.org/tracking-prevention/` | 7-day cap on script-writable storage; 24-hour cap on JS-set cookies after link decoration; 30-day deletion for classified domains; the anti-fingerprinting programme |
| `github.com/phantom/sign-in-with-solana` (README) | The SIWS ABNF and field rules: minimum 8 alphanumeric nonce, the allowed chain ids, the wallet composing the message |
| `raw.githubusercontent.com/solana-labs/wallet-standard/master/packages/core/features/src/signIn.ts` | The `solana:signIn` feature, versions 1.0.0 and 1.1.0, provenance from EIP-4361 and CAIP-122 |
| `docs.phantom.com/developer-powertools/signing-a-message` | Phantom verifies SIWS/SIWE/CAIP-122 fields at signing time |

## Platform and vendor documentation

| Source | What it establishes |
|---|---|
| `developer.apple.com/documentation/authenticationservices/supporting-passkeys` | Passkeys in a `WKWebView` require the RP ID to be an associated domain of the calling app; the app cannot authenticate services it has not configured |
| `passkeys.dev/docs/reference/android/` (state 29 Aug 2026) | WebAuthn is not directly supported in Android embedded WebViews; a Custom Tab has the full browser feature set including WebAuthn; AuthTab from Chrome 137+ |
| `passkeys.dev/docs/reference/ios/` | `WKWebView` runs in the calling app's context and only serves passkeys for the linked RP ID; `ASWebAuthenticationSession` has the full Safari feature set |
| `passkeys.dev/docs/reference/known-issues/` (state 9 Apr 2026) | The table of providers that "have not implemented User Verification in a spec-compliant manner", including the extensions that set UV true without performing UV |
| `passkeys.dev/device-support/` (state 21 Sep 2026) | Synced passkeys Android 9+, iOS 16+, macOS 13+; conditional UI Chrome 108+, Safari 16.1+ |
| `simplewebauthn.dev` docs, `@simplewebauthn/server` 14.1.0 / `browser` 14.0.0 on npm | MIT; the four server calls; empty `allowCredentials` for username-free login; Node LTS 22.x floor; the `rpID`/origin rules including "Do NOT include any trailing /" |
| `learn.microsoft.com/…/defender-office-365/safe-links-about` | URLs "scanned prior to message delivery, regardless of whether the URLs are rewritten or not"; the service will "wrap, detonate, or otherwise validate" a link |
| `developer.android.com/google/play/integrity/overview` | Play Integrity tiers, and that it detects "risky devices and emulated environments" — an Android app API, not reachable from a web page |
| `developer.apple.com/programs/enroll/` | "The Apple Developer Program is 99 USD per membership year" |
| `developers.google.com/identity/protocols/oauth2/policies` | "A developer must not direct a Google OAuth 2.0 authorization request to an embedded user-agent under the developer's control" |
| `support.google.com/faqs/answer/12284343` | WebView OAuth "not recommended", Chrome Custom Tabs recommended |
| `support.google.com/cloud/answer/13463073`, `developers.google.com/identity/gsi/web/guides/get-google-api-clientid` | Sensitive scopes need verification; the default `openid email profile` set does not |
| `docs.turnkey.com/security/secure-enclaves.md`, `docs.turnkey.com/support/dashboard/export-wallet.md`, `turnkey.com/pricing` | Keys generated and used inside attested TEEs; export is permanent and recorded; PAYG $0.10/signature with 25 free signatures and 1,000 free wallets |
| `privy.io/pricing`, `docs.privy.io/authentication/user-authentication/login-methods/passkey.md`, `docs.privy.io/controls/authorization-keys/…/server-export.md` | Free 0–499 MAU, Core $299/month to 2,499; passkey login; server-side export via a key quorum |
| `web3auth.io/pricing.html`, `crossmint.com/pricing`, `docs.cdp.coinbase.com/embedded-wallets/pricing`, `dynamic.xyz/pricing` | Free tiers and per-unit prices as quoted in §2.6 |
| `docs.solflare.com/llms.txt` | Deep-link provider methods; Quick Login cloud backup of the recovery phrase |

## Provider pricing (from the provider's own page, 2026-11-08)

`aws.amazon.com/ses/pricing/` and `docs.aws.amazon.com/ses/latest/dg/request-production-access.html`
($0.16/1,000; sandbox: verified recipients only, 200 per 24 h, 1 per second) ·
`resend.com/pricing` (free 3,000/month, 100/day; Pro $20 for 50,000) ·
`postmarkapp.com/pricing` ($15/month for 10,000) · `mailgun.com/pricing/` ($15 for 10,000) ·
`twilio.com/en-us/verify/pricing` ($0.05 per successful verification) ·
`twilio.com/en-us/sms/pricing/us` and `/ca` ($0.0083 per segment; carrier passthrough examples
AT&T $0.0035, T-Mobile $0.0045) · `campaignregistry.com/` (Brands cannot register directly with
TCR) · `fincen.gov/resources/statutes-regulations/guidance/application-fincens-regulations-certain-business-models`
(FIN-2019-G001).

## Prior work in this repository, cited rather than repeated

`records/findings/17-hackathon-rules-recheck.md` (event rules: code public, secrets out of the
repo, no restriction on which third-party auth service a team may use; prior work is
ineligible) · `records/findings/26-identity-bound-wallets.md` §2 and §6 (proof-of-personhood on
Solana: the Civic sunset, the Solana Attestation Service, ZK passport proofs, and the five
concepts) · `RESEARCH-PROGRAM.md` §4.3, §4.6 (evidence classes, no invented evidence).

---

# 8. Unverified, blocked, and not established

**Pages that refused to be read (a measurement, not an omission).** `fcc.gov` returns HTTP 403
to this host, so no TCPA clause is quoted and none is relied on; `crtc.gc.ca` returns 403, so
the Canadian guidance on whether a login link is a CEM is **absent**, and the CASL analysis
rests on the statute alone; `ico.org.uk` returns 403, so UK PECR wording is asserted by
correspondence with the directive, not read; `fintrac-canafe.gc.ca` returned 404, so the
Canadian custody question is **open**; `help.proofpoint.com` is behind a sign-in wall and the
public product page 404s, so Proofpoint's rewrite behaviour is not characterised;
`mimecast.com`'s URL-protect page 404s; `developer.apple.com` documentation for Sign in with
Apple is JavaScript-only, so the private-relay and first-authorisation details are **asserted**
and flagged.

**Figures that do not exist in any primary source read.** Laperdrix et al.'s "Beauty and the
Beast" numbers (IEEE paywalled, the HAL deposit is behind a proof-of-work wall) — **not
quoted**; a Google 2022 cross-browser fingerprinting paper — **not located**, so the "34 bits"
figure is marked MEASURED-ABSENT and appears nowhere in this file as a measurement; Chrome's
400-day cookie cap — **not reached**; the EDPB sentence that names fingerprinting — the
guideline's date is measured, its PDF would not download; Mozilla's `resistFingerprinting` and
Brave's farbling pages — a stub and a 404.

**Questions no source settles.** Whether a free Apple developer account can create a Pass Type
ID; whether an Android emulator can create a Google-account-backed passkey; which of Instagram,
Facebook, LinkedIn and TikTok use a Custom Tab rather than a raw WebView on Android; whether any
email scanner ever submits a form (no documented case was found, which is not evidence that the
POST mitigation is safe, only that the literature describes GET-based prefetch); Google's own
abuse posture on bulk account creation; any measured install-to-sign-in conversion for wallet
connectors; any measured support-load figure for passwordless recovery.

**Things this run deliberately did not do.** It did not build or deploy anything, did not
create or sign a wallet, did not touch the frontend or the on-chain program, and did not
commit or push. No claim in this file was verified against a running prototype, because there
is no visitor-identity code to run.
