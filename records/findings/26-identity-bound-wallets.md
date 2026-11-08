# 26: Identity-bound wallets, airlines, and which parts of this design could actually be chain-native

**Written:** 2026-11-07, 21:36Z to 22:20Z. **Tree read at:** commit `33d95b3`, plus an untracked
`records/STATE-OF-PROJECT.md` and untracked findings 20, 23 and 24, none of them mine and none touched.
**Event:** the MLH Solana Hackathon whose criteria and deadlines are analysed in
`records/findings/23-hackathon-score-analysis.md`. Nothing here was committed or pushed.
**Numbering, so nobody hunts for a missing file.** 23 was taken by that score analysis and 24 by its
second-pass reviewer. **25 was taken while this run was in progress**, by
`records/findings/25-solana-first-principles-primer.md`, a primer another worker wrote; that file is not
mine, was not read for this one and was not touched, and this file was renumbered to 26 when it appeared.

**What this file answers, in the operator's own four questions.**

1. **Proof-of-personhood on Solana** (Civic, Solana Attestation Service, ZK passport proofs, Sign Protocol,
   others): how each works, cost, maturity, privacy, and what a team can build in days. §2.
2. **Airlines**: boarding passes, name-matched non-transferable tickets, resale and rebooking, and where a
   ledger helps against where it adds nothing, from IATA and regulator sources. §3.
3. **Which parts of this design become chain-native and which do not.** §5.
4. **Three to five concept options** with effort, risk and fit to the judging criteria. §6.

§4 sits between 2 and 4 because the question "should a ticket be identity-bound at all" has an academic
literature, and the answer it gives is not the one the pitch wants.

**This file does not choose a concept.** The operator decides. Nothing here was built, deployed, signed or
spent.

---

## 0. Labels, and the limits of this run's evidence

- **MEASURED**: a named page, source file or chain read says it, and the URL or `path:line` is in the entry.
- **MEASURED-ABSENT**: the named pages were read and the thing is not on them. An absence is a measurement.
- **ASSERTED**: my reasoning. Where it is a prediction about a judge's score it also carries the programme's
  class **D**, because MLH publishes no scoring scale (`records/findings/23-hackathon-score-analysis.md` §2).
- **ESTIMATE**: an hours figure of mine with its basis stated. Never presented as measured.
- **Class A to E**: the programme's evidence classes from `RESEARCH-PROGRAM.md` §4.3. A means ticket-market
  empirical evidence, B a related market, C theory or established method, D a plausible untested hypothesis,
  E a research opportunity.

**Three limits a reader should know before trusting a row.**

1. **The free search tool was degraded during this run.** It returned no usable result for any query (the
   paid provider's credentials were absent and the keyless fallbacks returned a single news stub), so every
   airline source in §3 was reached by direct URL, by the publisher's own site search or sitemap, or through
   the Internet Archive. Absence findings in §3 are therefore absence *from the URLs reachable this way*, which
   is weaker than a proper search would give. That is stated again where it bites.
2. **No cluster write, no signature, no faucet, no vendor contact.** The rent and fee figures come from the
   live rent sysvar and from `getMinimumBalanceForRentExemption`, both read-only JSON-RPC reads, and from
   source files. "Live on mainnet" in §2 always means *the vendor, its repository or its documentation says
   so*, never *I queried its program*.
3. **One SOL price is used for every dollar figure**, so the dollars move and the SOL does not. The price and
   its timestamp are in §2.5.

---

## 1. The answer in one page

**On identity.** The one product the brief assumes exists, Civic Pass, was switched off during 2025 and its
own announcement says so; its uniqueness check, the only part that proved personhood, sunset on 31 July 2025
(§2.1). The only general-purpose attestation layer genuinely live on Solana is the Solana Foundation's
Solana Attestation Service, and it is a **claim registry, not a verifier**: anyone may issue a credential, so
a verifier's trust is exactly the issuer it was configured with, and its own README says so (§2.2). Every
zero-knowledge passport vendor is Ethereum-first with no Solana verifier, and none of them offers a
private name-equality proof, which is the one predicate "the name on the ticket is my name" needs (§2.3).
World ID does have a Solana program, but it is undocumented by its own vendor, carries no mainnet address,
and trusts a relay (§2.7). A signature, Sign In With Solana, and a hardware seed vault prove key control and
never personhood (§2.8). **A competent team can put a real attestation gate on chain in about three days**
(§2.6), and that is the whole of the good news.

**On airlines.** The name on an airline ticket is enforced by a government-document check at the airport
under 49 CFR 1540.107, not by the ticket, and non-transferability is a contract term whose stated remedy is a
refusal at the gate, with the carrier admitting it "may not notice" a transfer (§3.1, §3.2). The industry's
own move toward a single shared order record is a move toward **centralisation**: IATA Resolution 797 says
the single source of order data "is held in the ORA OMS", one airline's system (§3.4). Every tokenised airline
ticket attempt I could verify kept the airline's system authoritative, and the two most substantial are now
repositioned or wound down (§3.5). A ledger's honest job in air travel is the market and the receipt, not the
seat, the name, the fare rule or the money split (§3.6).

**On the economics, which is the part that should change the pitch.** Non-transferability is a price
discrimination device, not a fraud control (§4.1); banning resale costs 4.1% of gross and 2.9% of net surplus
in the best study we have, and the biggest losers are the people who attend (§4.2); paperless ticketing can
reduce the organiser's revenue (§4.3); refunds are more efficient than resale on average for the
can't-attend case (§4.4); **no study measures whether identity-bound ticketing reduces scalping** (§4.5); and
the measured money is in the price level, where primary auctions roughly doubled performer revenue (§4.6).
What identity buys this product is **data integrity and market design, not valuation** (§4.7).

**On our design.** Three parts are already chain-native (supply at issue, the custody record, the cap check),
two could be without much work (the "who may hold" gate, and a one-person-one-allocation counter), and the
rest should not be (the pricing engine, the documents themselves, the marketplace money, the UI and the
analytics). The wire contract already has a slot that nothing produces: `VerificationMethod` includes
`"identity"`, and `docs/ON-CHAIN-DESIGN.md` §2.5 says `method = 1` is "representable and **never produced**".
That is the gap the operator is asking about, and it is smaller and more specific than "make the app
on-chain" (§5).

**On concepts.** Five shapes survive contact with the evidence, and they differ more in what they destroy
than in what they add. The cheapest two (a soulbound pass, and chain-authoritative ownership) are 3 to 6
hours and one of them kills the product's own input. The two identity concepts are 9 to 12 and 14 to 20 hours
and carry a real chance of not finishing. The airline concept is the most expensive and rebuilds the
marketplace surface the design deliberately cut (§6). **None of the five moves the 0-of-4 materials test
unless the devnet publish also runs**, which is the same 45-minute funding step already recorded in
`records/findings/23-hackathon-score-analysis.md` §5.1 T1 (§6.7).

---

## 2. Proof-of-personhood and identity-bound wallets on Solana

Every mechanism below is asked the same five questions: how it works, cost, maturity, privacy, and what a
team can build in one day and in three.

### 2.1 Civic (Civic Pass, Gateway token, Civic ID): sunset, and the sunset took uniqueness with it

**MEASURED**, Civic's own announcement, "An update on Civic Pass", dated 11 June 2025, read twice in this
run including once by me directly (`https://www.civic.com/news/an-update-on-civic-pass`, 21:43Z and 21:52Z):

> "After careful consideration, we've made the decision to sunset Civic Pass and shift our focus to a new
> suite of live product-updates, and several currently in development."
> "CAPTCHA and Identity Verification will be discontinued on July 1, 2025, and Uniqueness and Liveness
> functionality will sunset on July 31, 2025."

The architecture it used is visible in the surviving gateway framework: a dApp picks a gatekeeper, the
gatekeeper checks identity off chain, and a per-wallet, per-gatekeeper **gateway token** account is minted
that the dApp reads before letting the wallet act. On chain there was one token account; off chain, the
document, the liveness video and the uniqueness check.

Corroborating measurements, all taken 2026-11-07: the vendor homepage now sells a go-to-market agent
("Bryn") and links no identity product (`https://www.civic.com/`, 21:38Z); the sitemap has 328 URLs and none
about passes (`https://www.civic.com/sitemap.xml`, 21:46Z); `https://www.civic.com/civic-pass/` returns
**HTTP 404**; `@civic/solana-gateway-react`'s last publish was 2024-12-04 and
`@civic/solana-gatekeeper-lib`'s was 2024-08-26 (npm registry, 21:46Z); the SDK's source repository
`civicteam/ociv-gatekeeper` returns not-found; and `identity.com` and `gatewaydocs.identity.com`, where the
Gateway Protocol documentation moved, do not resolve (DNS NXDOMAIN, 21:43Z).

**Cost.** MEASURED-ABSENT. No price is reachable because no product is.
**Privacy.** A ledger observer learned that a wallet held a pass from a named gatekeeper, and when. The
uniqueness claim, which is the only one that mattered for a scalping argument, is not certified by any token
minted after July 2025.
**Dev effort.** Not achievable in 1 day or 3: there is no supported path and no maintained authority to issue
a pass.
**Verdict.** A historical design. Any 2026 plan that assumes "Civic Pass on Solana" is working from a dead
product page.

### 2.2 Solana Attestation Service (SAS): live, cheap, and a registry rather than a verifier

**How it works.** One program, three account types, all PDAs (`https://attest.solana.com/` now 301s to
`https://solana.com/docs/tools/attestations`, which returned HTTP 429 behind a bot checkpoint in this run, so
the docs were read as their MDX source in `solana-foundation/solana-com`, and the program's own state
structs were read from source):

| account | fields, from source | who creates it |
|---|---|---|
| **Credential** | `authority`, `name`, `authorized_signers: Vec<Address>` | anyone |
| **Schema** | `credential`, `name`, `description`, `layout: Vec<u8>`, `field_names`, `is_paused`, `version` | the credential's authority |
| **Attestation** | `nonce`, `credential`, `schema`, `data: Vec<u8>`, `signer`, `expiry: i64`, `token_account` | an authorised signer |

The attestation PDA seeds are `[b"attestation", credential, schema, nonce]`, and the reference
implementations pass **the subject's wallet as the nonce**, so an attestation for a wallet is derivable from
`(credential, schema, wallet)` (`README.md`, 21:46Z).

**What that means for trust, in the program's own words.**

> "The `credential` you pass is the issuer you trust: anyone can create a credential and schema, so the check
> is only as strong as that choice."

There is no registry of approved issuers, no reputation, and no verification of a claim's truth. Revocation is
`CloseAttestation`, which closes the account and reclaims its rent, and the README notes the consequence: "A
closed attestation has no account, so revocation needs no extra check." Expiry is an `i64` where 0 means
never, compared against the on-chain clock by the verifier.

SAS can also mint a Token-2022 group whose members are soulbound, and the README carries an unusually honest
warning that the token is not the proof:

> "Holding the token proves neither that the attestation is genuine nor that it is still valid ... the token
> carries no expiry."

The verifier must take the `Attestation` address from the token's metadata, check the mint is the PDA derived
from it, fetch the attestation, check the program owns it, check the credential and the schema, and compare
the expiry.

**Cost, derived from measured inputs.** Transaction base fee 5,000 lamports per signature, of which 50% is
burned (`solana.com/docs/core/fees`, read as MDX, 21:45Z). Rent is `(128 + bytes) × lamports_per_byte`, and
the live `lamports_per_byte` read from the rent sysvar on 2026-11-07T21:47Z is **5,080**, cross-checked against
`getMinimumBalanceForRentExemption` for six sizes, every one an exact match (`165 → 1,488,440`,
`174 → 1,534,160`, `500 → 3,190,240`). So:

| account | bytes | rent | SOL |
|---|---|---|---|
| Attestation, 1-byte payload | 174 | 1,534,160 | 0.00153416 |
| Attestation, 3 small fields | 208 | 1,706,880 | 0.00170688 |
| Credential, one signer | 83 | 1,071,880 | 0.00107188 |
| Schema, small | 126 | 1,290,320 | 0.00129032 |

Rent is a **refundable deposit**, not a fee: it comes back on close. The byte counts above are **derived from
the serialized struct layout**, so they are arithmetic over source rather than a measurement; the rents for
those byte counts are measured. Two warnings. The SDK's
`DEFAULT_LAMPORTS_PER_BYTE` is **6,960**, and mainnet's sysvar says **5,080**, so any local estimate using
`Rent::default()` overstates rent by 37%. And SIMD-0437, whose status field reads *Idea*, proposes stepping the
rate down 6,960, 6,333, 5,080, 2,575, 1,322, 696, so the measured value is a step in a schedule and every rent
number needs a date.

**Maturity.** MEASURED: announced live on mainnet 2025-05-23 by the Solana Foundation's identity group
(`solana-attestation-service.mdx`, 21:41Z); program id `22zoJMtdu4tQc2PzL74ZUT7FrwgB1Udec8DdW4yw4BdG`;
repository MIT, last push 2026-11-06; SDKs `sas-lib` 1.0.10 (2026-09-01) and `@solana/attestation` 2.1.0
(2026-10-05); the changelog's only entry is `## [2.0.0] - 2026-09-25` and it says **"Not yet deployed. The
currently deployed binary predates this version."**; and the full 145-path repository tree contains **no
audit report**, only a `SECURITY.md` with a private disclosure process and CI dependency audits.

**Privacy.** `data` is stored **in the clear**; the docs' own phrase for it is "Keep attestation data on
Solana for transparency and permanence". There is no commitment scheme and no selective disclosure. Because
the PDA is derivable from a wallet you can name, issuer and subject are publicly linkable, and an attestation
carrying a name or a date of birth publishes it permanently. There is **no nullifier**: uniqueness is an
issuer-side policy, not a cryptographic primitive, and a verifier cannot tell whether the issuer enforced it.
The only conforming schema for a ticket is booleans and coarse categories.

**Dev effort.** **1 day**: create a credential, publish a schema, issue one attestation from a server-held
signer, read it back with the JS client. **3 days**: put the verifier **inside another program**, which is what
matters, because there is no verifier program to call; the consuming program receives the attestation account
and must itself check the PDA, the owner, the discriminator, the credential, the schema and the expiry. The
hardest step is that check: "The decoder does not check the discriminator, so the caller must" (README), and a
missing expiry comparison silently accepts stale claims.

### 2.3 ZK passport proofs: strong privacy, and not one of them is on Solana

The common shape: the user's phone reads the NFC chip of an ICAO 9303 e-passport, generates a zero-knowledge
proof about selected fields, and a server or a contract verifies it. What separates the products is which
fields can be proven and where verification lands.

| product | on-chain support, MEASURED | what it proves | price | status |
|---|---|---|---|---|
| **Self** (self.xyz) | **Celo only**; on-chain mode "mints each verified user a soulbound token" on Celo | facts about a government ID ("over 18", "not sanctioned"), disclosed fields | credits per verification (Pre-KYC 25, Age 10, Proof of Human 10); **no USD price published**, dashboard only | open SDK **deprecated** in the vendor's own words: "legacy and deprecated, do not use it for new integrations" |
| **ZKPassport** | Ethereum mainnet, Sepolia, Base. Zero occurrences of "Solana" in its intro, onchain and limitations pages | age, nationality, residency, personhood via a per-ID identifier, KYC attributes, private face match | **no pricing page** (404) | current docs, candid limitations page: ICAO 9303 documents whose issuing country publishes signing certificates only |
| **Rarimo** | its own L2 (chain id 7368) and EVM contracts plus registry replication | uniqueness, humanity, citizenship, age, "any other data contained in the passport" | MEASURED-ABSENT | app + rollup + verifier; audits page exists in the sitemap, not read here |
| **zkPass** | a documented Solana path that is **not** an on-chain ZK verifier: two ECDSA signatures (allocator and validator) returned from its extension | statements about a website's HTTPS response (a zkTLS oracle), not a passport chip | MEASURED-ABSENT | "can also be verified on Solana" is a sentence with no published program behind it |
| **Anon Aadhaar** | Solidity verifier; zero Solana | Aadhaar-only predicates | you pay gas | repos last pushed April 2025, site copyright 2024, old domain NXDOMAIN |
| **Sign Protocol** | EVM chains and chain ids only | attestations, on chain or a hash on chain | no protocol fee published | versioned contracts, current docs |

**The predicate nobody offers.** ZKPassport documents age, nationality, residency, personhood and KYC
attributes. A private **name equality** proof, meaning "the name on this ticket is the name on my document,
without revealing either", is **MEASURED-ABSENT** from its examples. The same absence holds for the others.
That matters because a name-matched airline ticket is the exact case the brief asks about, and the
cryptography for it is not a product anyone is selling.

**Two privacy details worth carrying.** ZKPassport's per-ID identifier is scoped to the verifier's domain, so
two platforms cannot correlate the same passport, but its default identifier "can be recomputed by anyone with
complete knowledge of the ID chip data, including the government that issued the ID". Self's nullifier is
"the same for the same person within your organization" and is derived from the passport number, so the
integrating organisation can link a person across its own flows and nobody else can, provided you trust
Self's server in the backend mode, which you must.

### 2.4 Sign Protocol and the rest of the EVM field

Sign Protocol is an attestation protocol with a schema registry and per-chain proxy contracts. Its networks
page is a table of EVM chain ids with no occurrence of "Solana" on it or in the FAQ. Quadrata is a soulbound
KYC passport on "Ethereum, Polygon, Arbitrum, Optimism, Avalanche, Evmos, and KAVA". Human Passport's on-chain
stamps are on "Arbitrum, Base, Linea, Optimism, Scroll, Shape, ZkSync". All MEASURED, all with zero Solana
occurrences on the page read. Solana ID is an ad-targeting identity graph that "turn[s] targeted ads into
personal perks" with no document binding; SNS is a naming registry. Neither is personhood.

### 2.5 The numbers, in one place

- Base fee **5,000 lamports per signature** (0.000005 SOL), 50% burned, and **charged even if the transaction
  fails**. Priority fee is `ceil(CU price × CU limit / 1,000,000)`, defaults to zero, and is charged on the
  requested limit rather than actual use.
- Rent **`(128 + bytes) × 5,080` lamports**, measured 2026-11-07T21:47Z, refundable on close. The SDK default
  of 6,960 is 37% higher than the live rate.
- **A ticket account** at 165 bytes: 1,488,440 lamports. **A ticket mint** with a transfer hook and a metadata
  pointer at 219 bytes: 1,762,760. **An attestation**: 1,534,160. **A 59-byte verification record**:
  949,960, which is the figure `docs/ON-CHAIN-DESIGN.md` §2.5 already carries, so that document's rent
  arithmetic is right and this file does not "correct" it.
- **Deploying a program** costs rent on the ProgramData account, `(128 + 45 + elf) × 5,080`: a 150 KB program
  is a **0.763 SOL permanent deposit**, and about **1.53 SOL in flight** while the buffer account is funded,
  with the buffer refunded. At the SOL price used below that is about $136 to land $68 of deposit.
- Dollars here use **$89.04 per SOL**, CoinGecko `simple/price`, 2026-11-07T21:46:57Z. All of them move with
  the price and none of them are part of a claim.

### 2.6 What a team can actually build in days

| in 1 day | in 3 days | not in 3 days |
|---|---|---|
| an SAS credential, schema and attestation, issued by a server key and read back | the same, plus a **verifier inside another program** that checks PDA, owner, discriminator, credential, schema and expiry, plus a nullifier PDA and negative tests | a Solana ZK passport verifier: no vendor ships one, and the circuits are not published for Solana |
| a hosted Self or ZKPassport flow checked on your server, on Celo or an EVM chain | a World ID satellite with your own authorised gateway and a nullifier store you write | a private name-equality circuit for the airline case |
| Sign In With Solana and on-chain ownership reads | | a production KYC relationship with any of these vendors |

### 2.7 World ID: a real Solana program, undocumented

An Anchor "satellite" program stores bridged World ID state (Merkle roots, issuer keys, OPRF keys) and
verifies World ID Groth16 proofs. From the repository's own README and source: program id
`BxHvVSWUkStm7RsKySrzyGWV85PNF8TsGTsPEQ3PsVfK`, instructions `initialize`, `set_owner`, `add_gateway`,
`remove_gateway`, `update_root`, `set_issuer_pubkey`, `set_oprf_key`, `verify`, `verify_session`, a
`root_validity_window` defaulting to 3600 seconds, and a tree depth of 30. The relay that pushes state from
World Chain lives in a different repository.

Three measured problems. The program **does not read World Chain**; it trusts whichever gateway signers
`add_gateway` authorised, so on Solana the uniqueness guarantee is only as good as that relay's key custody.
It **stores no nullifiers**: `nullifier: [u8; 32]` is an instruction argument, so a caller that does not
record it can replay the same proof. And it appears **nowhere in the vendor's documentation**: the full docs
index at `docs.world.org/llms.txt` contains zero occurrences of "Solana". The repository was created
2026-07-22, last pushed 2026-10-19, has zero stars and no description, and publishes no mainnet address.

### 2.8 What is not identity: SIWS and the Seed Vault

Sign In With Solana "lets applications authenticate their users and prove ownership of their addresses". A
SIWS signature is an ed25519 signature over a wallet-constructed message, with domain binding and a nonce. It
proves **control of a key at the moment of signing**. It has no name, no document, no issuer, no nullifier and
no registry. Solana Mobile's Seed Vault raises the custody bar, keeping keys in a secure execution environment
with a biometric gate, and changes none of that. Both are prerequisites for a wallet-bound ticket and neither
is personhood. Any "identity-bound ticket" that is SIWS plus a database is a web2 app with a signature on the
front.

### 2.9 Privacy: what a public ledger learns, and what it must never hold

For every mechanism above, the ledger learns a durable, publicly enumerable link between a wallet and "this
wallet passed a check by issuer X", plus a timestamp and, if the schema carries them, coarse attributes.
Nothing here stores the document, which stays with whoever is entitled to hold it. Two consequences:

1. **A nullifier is not anonymity.** It is a stable per-person identifier within its chosen scope. If the
   application writes the wallet-to-nullifier mapping on chain to stop replays, as World ID on Solana forces
   it to, the application has published the very link the proof was meant to hide. The commitment must
   therefore be **derived, not stored**: publish a hash of the nullifier plus a per-event salt, or store the
   mapping off chain.
2. **Attestations carrying personal data are unlawful to publish.** GDPR Article 4(1) makes passport data
   personal data, and Article 17(1) gives a right to erasure that an append-only public ledger cannot honour.
   A hash of a passport number is still personal data, because the number space is small enough to enumerate.
   The only lawful artefact is an attestation **that a check occurred**.

---

## 3. Airlines: where a ledger helps, and where it adds nothing

### 3.1 The ticket is a database record, and the prohibition is a contract term

**MEASURED**, Air New Zealand's conditions of carriage, section 5.3, "Can someone else use my Ticket?",
last updated 16 March 2026 (`https://www.airnewzealand.com/conditions-of-carriage`, 21:44Z):

> "You cannot give or sell your Ticket to anyone else. We only provide travel for the Passenger named on the
> Ticket. If someone else presents your Ticket for travel and we realise that person is not you, we will not
> let them travel. Despite acting reasonably, we may not notice a Ticket has been transferred to another
> person."

The same document defines the ticket as a carrier-held record: "Electronic Ticket: the electronic coupon,
'E-Ticket' or record of your Ticket made by us or in Agent, which is held in our reservations system."

Two things matter more than the prohibition. The remedy is a **refusal at the point of travel**, not a title
dispute, and the carrier **explicitly disclaims the ability to detect a transfer**. The rule is enforced by a
human at a desk. What is prohibited is transfer of the ticket, not of the booking; the booking stays under the
carrier's fare rules.

**On the IATA layer, one honest gap.** I confirmed from IATA's public Passenger Services Conference Resolution
Manual page that the manual exists, that it covers "reservations, passenger and baggage check-in and ticket
issuance", and that it names Resolutions 701, 722, 743, 753, 762, 767, 780, 787 (NDC) and 797 (ONE Order).
I could **not** confirm which resolution carries the "not transferable" text, because the manual is sold rather
than published. **Any resolution number quoted for transferability is unverified** until someone reads the
manual page.

### 3.2 Identity at boarding is a government function, not a ticket function

**MEASURED**, 49 CFR 1540.107:

> "(c) An individual may not enter a sterile area or board an aircraft if the individual does not present a
> verifying identity document as defined in § 1560.3 of this chapter, when requested for purposes of watch
> list matching."

and 49 CFR 1560.3, which defines a verifying identity document as a passport, or a government document
carrying full name, date of birth and photograph, and defines Secure Flight Passenger Data as full name, date
of birth, sex and passport information. The airline is compelled to collect that data at booking and transmit
it; the passenger is compelled to present the document at the airport. Both obligations are statutory.

IATA's One ID programme takes this further: "passengers arrive at the airport Ready to Fly all documents have
been checked remotely and in advance", sharing "digital credentials from their wallet" so that "in the
end-state, passengers can obtain the travel authorization directly from governments". A ledger can carry an
attestation that a check happened. It cannot perform the check, and it adds nothing to a decision a border
agency makes.

**Boarding pass, and an absence.** The Bar Coded Boarding Pass standard is universally known as Resolution
792, and I could **not verify that number**: every IATA page path for it returned 404 in this run, an IATA site
search returned no such page, and the resolution manual's change log does not list it. `792` is therefore
recorded here as unverified. What I could confirm is that IATA's device specification for boarding gate readers
expects biometric validation at the gate and names a US government service as the identity authority.

### 3.3 Name changes and transferability: the market already exists, without a ledger

**MEASURED-ABSENT, and this is the largest gap in this section.** I could not retrieve a single airline page
stating a name-change fee. Of the twelve carriers tried, most returned a JavaScript shell, a timeout, a 403 or
a 404 template, and Delta's contract of carriage truncated before the ticket rules. **No fee figure in this
file is quoted from an airline page, because none was read.** The degraded search tool is the reason this list
is short (§0).

What is measurable is that an airline-sanctioned transfer market exists as a product. TravelX, which ran the
Air Europa and Flybondi NFT ticket programmes, now sells post-booking revenue management, and its own
description of the peer-to-peer module is the answer to "can a token move a seat":

> "The P2P component of TravelX enables passengers to resell, transfer, or gift their tickets within a secure,
> airline-approved framework."
> "RMX seamlessly synchronizes reservations in the airline PSS and automatically issues compensation using the
> airline's credit or voucher system."

A transfer is a **name change written into the airline's passenger service system**, priced by a fare rule,
settled in the airline's own credit instrument. The airline is the registrar. No ledger is required, and the
company that tried the ledger has moved on (§3.5).

### 3.4 The industry's own "one shared record" programme is centralisation

**MEASURED**, IATA Resolution 797, ONE Order, read as the published PDF (621,988 bytes, 21:40Z), whose own
principles say:

> "1.3.3 Before and after delivery, the single source of all data related to an order (i.e. a record of
> passenger data, entitlement and delivery status of services) is held in the ORA OMS."
> "1.3.3.1 The provider of the service(s) shall update the ORA of any status change to services in the order."

The industry's flagship modernisation of the ticket record, replacing PNRs, e-tickets and EMDs with one order,
is explicitly a **single-source-of-truth-in-one-airline's-system** design. Every other party updates it. That
is the opposite architecture to a shared ledger, and it is the industry's own answer.

Around it: NDC (Resolution 787) is a message format problem, not a trust problem; BSP settles "$242B+
annually" at "99.99% on-time" between "400+ participating airlines" and "59,000+ accredited travel agents"
through "centralized collection, distribution, and reconciliation of funds", which is a trusted intermediary
doing exactly the job a ledger would be proposed for; and Resolution 753 mandates that airlines track baggage
at four points and share the scans with interline partners, with a 100% proration penalty for missing
evidence. That last one is the closest to a ledger-shaped problem, and what IATA built is a **reporting
obligation**, not a shared ledger.

### 3.5 Prior tokenised-ticket attempts, verified

| project | what the evidence says now | outcome |
|---|---|---|
| **TravelX / Air Europa / Flybondi** | current homepage leads with "post-booking revenue solution", and contains no occurrence of "NFT", "blockchain" or "Algorand"; the 2023 archive of the same site carries "NFTicket" and a Flybondi adoption headline | repositioned to revenue management; the token is gone from the pitch |
| **Chain4Travel / Camino** | the company's own site: "Chain4Travel AG wound down its operations in spring 2026"; the network survives as an **EVM-compatible, permissioned** chain whose "validators are KYB-verified travel companies" with a "100,000 CAM bond" | operating company wound down; a permissioned club left behind |
| **Blockskye** | current homepage describes corporate travel distribution; no occurrence of "blockchain", "token" or "ledger" | no ledger in the pitch |
| **SITA FlightChain** | the press-release path returns SITA's 404 template and the archive has no capture of it | **unverified**; do not cite a participant list or an outcome |
| **Etherisc flight delay** | vendor site returned 60 characters of text and a Cloudflare interstitial | **unverified** |
| **any Solana airline or air-travel project** | not surfaced and therefore not verified in this run | **MEASURED-ABSENT** |

The pattern across every verified case: the token was a record of entitlement, the legal right to be carried
stayed a contract with a named passenger, and the airline's system stayed authoritative. Nobody verified here
replaced the system of record with a public ledger.

### 3.6 What a ticket token cannot reach

Classified **LEGAL** (a contract or regulation decides it), **SYSTEMS** (an operational record decides it) or
**BOTH**.

| # | constraint | class | why a ledger does not help |
|---|---|---|---|
| 1 | **inventory control** | SYSTEMS (with a contractual edge) | a seat is a unit of authorised capacity decremented in the carrier's inventory host, shared with codeshare and interline partners; only that host can allocate |
| 2 | **fare rules and fare construction** | LEGAL, executed by SYSTEMS | the fare is a set of conditions attached to a journey; a token that changes who flies must re-satisfy the fare engine, which is the airline's. Resale does not change a price, it changes a party to a priced contract |
| 3 | **revenue accounting and interline proration** | BOTH | the money is divided by rule, not by market: Resolution 797 §1.3.5 ties billing to delivery, and Resolution 753's penalty is a proration rule |
| 4 | **agency distribution agreements** | LEGAL | who may sell, with what ticketing authority and liability, comes from accreditation; a secondary market outside them is not distributing, it is reselling a contract the conditions forbid |
| 5 | **the passenger-name record** | LEGAL and SYSTEMS | collected under statute, verified against a document, stored as a field in someone else's database |

**Where a ledger does help:** the market for the right to change a name, and the receipt that proves who paid
whom for it, with a tamper-evident record of the offer and its acceptance. That is a real product and it is
the one TravelX monetises, minus the token. **Where it adds nothing:** the seat, the name, the fare rule, the
money split, and the check at the gate.

---

## 4. The economics of non-transferability, and why it constrains the design

This section exists because the pitch "identity-bound, non-transferable ticket" is an economic intervention,
and the literature on it is older and less flattering than the pitch.

### 4.1 Why tickets are non-transferable: price discrimination, not fraud

**Borenstein and Rose (1994)**, *Competition and Price Dispersion in the U.S. Airline Industry*, Journal of
Political Economy 102(4) 653-683, DOI 10.1086/261950, read as NBER Working Paper 3785: the expected absolute
fare difference between two passengers on the same route is **36% of the average ticket price**, it rises on
more competitive routes, and the restriction structure (advance purchase, minimum stay, Saturday-night stay)
"cannot be justified solely on the basis of shadow capacity costs". **[MEASURED, class A]**

Inside the same paper is the cleanest number in this literature: the no-show cost difference between discount
and full-fare passengers justifies **at most a 6% price differential, "probably 2% or less"** under realistic
assumptions. The discounts are far larger. The fences are discrimination. **[MEASURED, class A]**

**Dana (1998)**, JPE 106(2) 395-422, DOI 10.1086/250014, shows advance-purchase screening survives **without
market power**. **[Theory, class C]** That is why transferability restrictions are a durable feature of
competitive markets rather than a quirk of one seller.

**The economic content of "non-transferable"** is therefore: the restriction must attach to the person, or the
buyer who most values flexibility buys the cheap restricted product through someone else and the menu
collapses. I state that as the mechanism these papers jointly imply; no paper I read derives it in those
words.

### 4.2 What resale does: the best measured answer, and it is a close call

**Leslie and Sorensen (2014)**, *Resale and Rent-Seeking: An Application to Ticket Markets*, Review of Economic
Studies 81(1) 266-300, DOI 10.1093/restud/rdt033, and its working-paper predecessor NBER WP 15476, read in full.
Structural estimates on merged Ticketmaster and eBay/StubHub transaction data, then counterfactuals:

- resale raises **gross surplus 4.1%** against no resale, and **net surplus only 2.9%**, because resale-market
  costs plus increased effort in the primary arrival game absorb **over 33%** of the gain;
- frictionless resale would raise gross surplus 9.4%, but attendees' net surplus would be **2% lower**, and
  **32% worse off** under frictionless resale, with resellers capturing more surplus than they create;
- "the biggest losers from resale are the consumers who actually attend the event";
- for some events, net surplus would be **higher with resale eliminated**;
- the primary allocation under endogenous arrival is already **17% more efficient than random** with no resale
  at all.

**[Empirical, structural; class A for the ticket market, class C for the counterfactuals, which are model
simulations and not experiments.]** The version discrepancy is worth carrying: the 2014 abstract says a third
of the gain is offset, the 2009 working paper says half. The body numbers quoted above are the 2014 ones.

### 4.3 Non-transferability can cost the organiser money

**Cui, Duenyas and Sahin (2014)**, *Should Event Organizers Prevent Resale of Tickets?*, Management Science
60(9) 2160-2179, DOI 10.1287/mnsc.2013.1862: under fixed pricing, organisers "benefit from reductions in
consumers' (and speculators') transaction costs of resale", and paperless, non-transferable ticketing "may
reduce the capacity providers' revenues", including under multiperiod pricing when capacity is small.
**[Theory, class C; conditional on fixed pricing.]**

**Karp and Perloff (2005)**, *When Promoters Like Scalpers*, JEMS 14(2) 477-508, gives the mechanism: resellers
perform the intertemporal sorting a single-price seller cannot. **[Theory, class C]**

### 4.4 The cheaper instrument for the can't-attend case is a refund

**Vollmer (2025)**, *Is Resale Needed in Markets with Refunds?*, RAND Journal of Economics 56(3) 251-268,
DOI 10.1111/1756-2171.12501: on college football data, "because of resale frictions, refunds are more efficient
on average. However, flexible prices make resale more efficient after large aggregate shocks." **[Empirical,
structural; class A. Abstract only; no magnitudes quoted.]**

The UK government's **Waterson review (2016)** is the only real-world document I found that puts a number on
the population: of its own survey respondents, **14% reported a change in financial circumstances** between
purchase and event. Its often-quoted "5% or so of customers ... unable to attend" carries no source in the
document itself. **[Survey, weak class A; the 5% is class D.]**

### 4.5 Nobody has measured whether identity-bound ticketing works

**MEASURED-ABSENT.** I found no peer-reviewed empirical study of the effect of identity-linked or name-bound
ticketing on resale prices or availability. What exists:

| claim | evidence | class |
|---|---|---|
| identity-linked ticketing reduces scalping | asserted in policy documents and design-science papers; **no measurement** | D |
| anti-scalping **laws** raise primary prices and seller revenue (about +$2 baseball, +$10 football season tickets, attendance unchanged) | Depken 2007, Public Choice 130, DOI 10.1007/s11127-006-9072-6, abstract | A, direction informative, magnitudes provisional |
| a technology-targeted ban moves touting rather than ending it (UK, post-2016/2017) | Moretti 2024, International Criminal Justice Review 34(3), DOI 10.1177/10575677241234601, qualitative | A |
| paperless ticketing can reduce organiser revenue | Cui et al 2014 | C |
| self-sovereign identity makes ticketing feasible | Feulner et al 2022, Electronic Markets 32(3), DOI 10.1007/s12525-022-00573-9, design science; the same paper concedes that reliable identification, not the ledger, is the hard part | D for any market outcome |

### 4.6 The result that should reorder the pitch

**Budish and Bhave (2023)**, *Primary-Market Auctions for Event Tickets: Eliminating the Rents of "Bob the
Broker"?*, American Economic Journal: Microeconomics 15(1) 142-170, DOI 10.1257/mic.20180230: Ticketmaster's
primary-market auctions, evaluated against eBay resale values, "substantially improved price discovery,
roughly doubled performer revenues, and, on average, nearly eliminated the arbitrage profits associated with
underpriced tickets". **[Empirical, class A; abstract only.]**

Read against §4.1 to §4.5, this says the rents come from **underpricing at the primary price level**. An
identity-bound ticket at the same face value changes **who wins the rationing**, not how much the seller
captures. Any pitch that leads with stopping scalpers has to answer this, and the answer is not in the
literature.

### 4.7 What identity buys this product, stated narrowly

**It buys data integrity and market design. It does not buy valuation.**

- **Data integrity, and it is a measured gap in our own record.** `records/findings/01-b-identifiability.md`
  states that "whether two wallets are one person is not [identified]" and that Bitcoin-style clustering does
  not transfer because Solana is account-based. An identity commitment makes the person the unit, so
  per-person purchase counts, resale propensity and repeat-reseller behaviour stop being contaminated by
  sybil wallets.
- **Market design.** A per-person allocation cap is the only mechanism that touches the actual scalper
  practice, which is many wallets rather than one high price. `docs/ON-CHAIN-DESIGN.md` §4.2.6 says the design
  "has no sybil resistance at all" and that closing it needs "an identity commitment with a nullifier PDA".
- **Not valuation.** What a seat at an event is worth comes from the event, the seat and the clock. No
  identity mechanism changes the price the engine should charge, and a concept that claims otherwise is
  claiming a mechanism the data does not support.
- **The one measurement nobody has made is the one that matters to us.** No study estimates whether observing
  resale prices improves primary price setting, or by how much (§4.6 is about auctions, not about resale data
  as a pricing input). That is class **E**: a specific research opportunity, and this programme is unusually
  well placed to run it because a ledger records **realised** prices rather than asking prices.

---

## 5. Which parts of this design would become chain-native, and which would not

The design's own account is `docs/ON-CHAIN-DESIGN.md`. Its invariant (§1.1) is: the ticket cannot move without
the program recording the hop, and the program refuses to record a price above the cap. Its stated reason for
using a chain at all is not "scalpers are bad" but that an off-platform resale is **missing data** the pricing
engine can never see (§1.2). That is the test I apply below: does the chain make the engine's input more
complete, or is it decoration.

| part of the design | today | could it be chain-native | verdict and why |
|---|---|---|---|
| **Supply enforced at issue** | chain-native (program) | already is | keep. One sentence, checkable on a laptop |
| **Per-ticket custody record and hops** | chain-native (PDA per ticket, per hop) | already is | keep. This is the engine's input and the reason the chain is there |
| **Resale cap check** | chain-native, because the price is staged in program state before the transfer | already is | keep. A hook cannot see a price; only staged state can carry one |
| **"Who may buy or receive" (holder verification)** | **one verifier key's opinion**; `method = 1` (identity) is "representable and never produced" (`docs/ON-CHAIN-DESIGN.md` §2.5) | **yes, in 9 to 12 hours**, with an SAS attestation read by the hook, or a nullifier PDA | the only identity-shaped gap, and it is already designed for |
| **One person, one allocation** | absent; §4.2.6 says the design "has no sybil resistance at all" | **yes**, with a nullifier PDA plus an off-chain identity check behind it | the mechanism that addresses the real scalper practice; needs a decision about what the chain may remember about a person |
| **Redeem and revoke** | chain-native (program) | already is | keep |
| **The pricing engine** | off chain, standard library, 7.7k lines of product code | **no** | its inputs are off chain, it is compute over data, and the chain adds cost and loses the ability to refuse to answer. The only chain-shaped part is a **quote commitment** (a memo of the quote and its hash), which `tools/devnet_publish.py` already writes |
| **The identity documents themselves** | nowhere | **never** | GDPR, see §2.9. Only "a check occurred" may be published |
| **The marketplace (listing, buy, checkout)** | deliberately absent | **only with an escrow**, 10 to 14 hours, and the design rejected it (§1.3 candidate B) | an escrow binds the money, not the market; it rebuilds the surface the plan forbids |
| **Organiser analytics and the console** | off chain, reading fixtures | **no** | it is a read of state plus computation. Making it "on chain" would be a second copy of the same data |
| **Fiat settlement to organisers** | off chain | **no** | regulated, and the operator holds no licence to do otherwise |
| **Wallet login** | a signed message | **could be**, and cheaply (§6.4) | it changes who is authoritative, not who the person is |

**What the wire contract already anticipates, and what it does not.** The frontend's `lib/types.ts` carries
`VerificationMethod = "wallet_signature" | "identity" | null`, a `flags: string[]` for machine-readable reasons,
and a `region` field that is "non-null only when the wallet voluntarily attached a region". So the contract
already has a place for an identity method and a place for a refusal reason. It has **no** place for a
per-person allocation, a nullifier, or an attestation reference, which means any concept below touches the
wire contract, the design document and the program, in that order.

**Two corrections that fell out of the reading, both small and both real.**

1. **`NonTransferable` is the opposite of what this product needs.** The Token-2022 extension makes every token
   account of the mint reject `Transfer` and `TransferChecked` with `TokenError::NonTransferable`; the docs say
   holders "cannot move them to another token account". There is no transfer path at all, and the mint
   extension is permanent. A resaleable ticket needs the hand-off to **happen and be constrained**, which is
   `TransferHook` (arbitrary policy, amount only) or `PermanentDelegate` (unilateral claw-back). Any concept
   built on "soulbound tickets" deletes the resale record the engine exists to read.
2. **The hook has a sentinel that a future extension could trip.** When Token-2022 invokes a hook from a
   confidential transfer, "the amount is not known to the token program and `u64::MAX` is passed as a
   convention". `programs/cap_hook/src/lib.rs:335` refuses `amount != 1`, so the current hook **fails closed**
   on that sentinel, which is correct by construction and should stay asserted in a test; a hook written as
   `amount <= 1` would fail open.

Also worth recording, because it is the opposite of a correction: `docs/ON-CHAIN-DESIGN.md` §2.8's rent figures
are **right**. They use the live 5,080 lamports per byte, which I re-measured from the rent sysvar, and its
59-byte verification record at 949,960 lamports reproduces exactly. The 6,960 figure that appears in the SDK
default and in most tutorials is 37% high against mainnet today.

---

## 6. Five concepts, with effort, risk and fit

Nothing here is chosen or ranked by preference. The table orders them by estimated hours because that is a
fact about them, not a judgement of them.

| # | concept | in one line | effort (ESTIMATE) | the chain-native part | what it destroys or leaves undone |
|---|---|---|---|---|---|
| **C4** | Chain-authoritative ownership | SIWS login, ownership read from the chain, no backend session | **4 to 6 h** | who is authoritative | proves nothing about a person |
| **C1** | Soulbound pass | `NonTransferable` ticket plus an issuer attestation, no resale | **3 to 5 h** | the binding | the resale record, and therefore the product |
| **C2** | Verified-fan resale gate | SAS attestation plus a nullifier, checked inside the transfer hook | **9 to 12 h** | the gate and the per-person counter | side payments, wash trading, and the truth of the claim |
| **C5** | Airline seat-release receipt | an offer to give a seat back and its acceptance, recorded on chain | **12 to 16 h** | the offer and the receipt | the seat, and the plan's no-marketplace rule |
| **C3** | ZK personhood, no issuer | World ID satellite with our own gateway, or a Groth16 verifier | **14 to 20 h** | the proof and the nullifier | finishability, and the vendor's silence |

**The precondition that applies to all five.** Every materials-test item in
`records/findings/23-hackathon-score-analysis.md` §3.5 is still absent, and no concept below converts one of
them into evidence until the existing devnet publish runs: about 45 minutes of script plus a faucet step the
operator must do himself, because the faucet's own page says AI agents should not use it. **Identity research
does not remove the 0-of-4 problem. It changes what is on chain once that problem is solved.**

### 6.1 C1: the soulbound pass

**What it is.** Mint each ticket with the `NonTransferable` extension and attach an SAS attestation that the
holder passed whatever check the organiser accepts. A ticket cannot leave the wallet it was issued to.

**Chain-native.** The binding, and nothing else. A judge sees an account that cannot move.

**Effort, ESTIMATE 3 to 5 hours.** A mint flag, one attestation, one read. The existing hook and publish
script do most of the work; `programs/cap_hook` becomes unnecessary for these mints because no transfer can
occur.

**Risk.** This is the concept that most needs saying plainly: **it deletes the engine's input.** The product's
argument for a chain (§5, and `docs/ON-CHAIN-DESIGN.md` §1.2) is that every resale is recorded so the observed
markup distribution is complete. Non-transferable means there are no resales. The engine's secondary-market
value estimate, its sale-hazard model and its cap-compliance record all lose their data source, and the pitch
becomes an access-control story wearing a pricing product's clothes. Secondary risk: the extension is
permanent, so a mint made this way cannot be loosened later without issuing a new mint.

**Fit.** Technology: low, because no program is needed (class D, +0 to +1). Design: neutral. Completion: high,
because it is the easiest to finish (+1). Learning: 0. **Materials test: 1 of 4 at best**, an account and
possibly a signature, with no third-party program doing work the product depends on. **Do not do this if the
pricing engine is the submission.**

### 6.2 C2: the verified-fan resale gate

**What it is.** An issuer (the operator's own key for a demo, or a partner) attests on chain that a wallet
belongs to a person who passed a check. The transfer hook reads that attestation and refuses a transfer to a
wallet without one. A nullifier PDA makes a second registration for the same commitment fail because the
account already exists. Optionally a per-wallet holding cap in the hook.

**Chain-native, and this is the most defensible part.** The gate is a program **we** write, reading a program
**we did not write** (SAS), and refusing in the runtime with a code we chose. That is the only concept here
that puts a third-party program into a path the product depends on.

**Effort, ESTIMATE 9 to 12 hours.** Itemised: an SAS credential and schema, 1 h; an issuer script that signs
attestations from a server key with the signer kept out of the parent process, 1.5 h (the pattern already
exists in `tools/solana_sign.py`); the verifier inside the hook, checking PDA, owner, discriminator, credential,
schema and expiry, 3 h, which is the hard part; a nullifier PDA and its second-registration test, 1.5 h;
`ExtraAccountMetaList` changes so the hook is passed the attestation and the nullifier, 1 h; three negative
tests (no attestation, expired attestation, second wallet on one commitment), 1.5 h; wiring the read-back into
the console, 1 h. **If the operator's issuer is a real partner, add the partner's own onboarding time, which I
cannot estimate.**

**Risk, in order of how likely it is to cost the entry.** (1) SAS has **no published audit** and its 2.0.0
release is not the deployed binary. (2) The in-program check has a documented footgun: the decoder does not
check the discriminator, and a missing expiry comparison silently accepts stale claims, so this is the one
place a reviewer must look. (3) The evidence behind the attestation is **one key's opinion**; the design
already says that about the verifier key and it stays true. (4) An attestation carrying a name or a date of
birth is a GDPR defect and must not be built. (5) The chain becomes the thing that decides who may buy a
ticket, which is a product decision the operator has not made.

**Fit.** Technology: **+3 to +5** (class D), because it is the largest single block of new mechanism available
in the window and it is checkable in public. Design: 0 to +1, unless the console shows the refusal. Completion:
+2 to +3. Learning: +1. **Materials test: 3 of 4, or 4 of 4 if the console reads the state back**, and it is
the only concept here that reaches item (c), a program the team did not write doing work the product depends
on. **It does not fix** side payments, wash trading by one person with two attestations from two issuers, or
the marketplace.

**Variant worth naming, because it is the same chain surface and a different product.** Replace "verified
person" with "counted person": publish only a nullifier commitment and no attributes, and use it to dedupe
wallets for the engine's demand model. Cost: about 4 extra hours on top of C2 (engine feature plus tests). What
it buys is §4.7's data integrity: per-person instead of per-wallet demand, and a measurable mass at the cap per
person. What it does not buy is a thing a judge can see in four minutes.

### 6.3 C3: ZK personhood, no issuer

**What it is.** Prove personhood with a zero-knowledge proof instead of trusting an issuer's attestation,
storing only a nullifier so one person cannot register twice. Two routes: the World ID Solana satellite with a
gateway we authorise, or a Groth16 verifier we deploy.

**Chain-native.** The proof check and the nullifier. A Groth16 verify costs 78,293 to 108,762 CU on BN254 for
1 to 8 public inputs (the library author's own benchmark), or 134,766 to 165,238 CU for the BSB22 shape most
passport circuits take, and the proof is about 256 bytes, which fits a 1,232-byte transaction. Verification
costs **no lamports of its own**; compute units are metered, and the only cost is the priority fee you choose
plus the 5,000-lamport base fee.

**Effort, ESTIMATE 14 to 20 hours, and the honest number is that it is not a weekend job.** The World ID route
needs the relay from a different repository, a gateway keypair we control, bridged state, and a nullifier store
we write, without which the same proof can be replayed. The Groth16 route needs a circuit and a verifying key
we do not have: no ZK passport vendor publishes a Solana verifier or a circuit, and writing one is out of
scope. What is achievable is the satellite **with our own gateway**, which means the trust problem is ours and
the claim "no issuer" is false unless the gateway set is public and multi-party.

**Risk.** Highest of the five. The program is undocumented by its vendor, has zero stars, publishes no mainnet
address, and trusts a relay. Substituting a single gateway we run converts a personhood proof into "the
operator says so" with extra steps. Finishability is the binding risk at 19 hours out.

**Fit.** Technology: **+4 to +6** (class D) if it lands, the highest ceiling here. Design: 0. Completion: **-2
to -4** (class D), because a half-finished verifier is worse than no verifier. Learning: +2, honestly earned.
**Materials test: 4 of 4** if it lands, including the third-party program item.

### 6.4 C4: chain-authoritative ownership

**What it is.** Not identity. Sign In With Solana for the session, ownership of the ticket read from the chain
rather than from a backend, and no server-side session store. The wallet is the account; the chain is the
record; the app is a view.

**Chain-native.** Who is authoritative. It is the cheapest true answer to "a chain bolted onto a web2 app",
because it removes a web2 component instead of adding a chain one.

**Effort, ESTIMATE 4 to 6 hours.** SIWS message construction and verification, 2 h; replacing the fixture
ownership read with a chain read against the artefact the publish script writes, 1.5 h; the console's
`[DEVNET]` slot still refuses a non-devnet artefact, so the loader needs no change, 0.5 h; a refusal state for
"wallet does not hold this ticket", 0.5 h.

**Risk.** Does not touch the judging problem it looks like it touches: it proves nothing about a person, and a
judge who hears "identity" will find a login. Low technical risk, medium expectation risk.

**Fit.** Technology: +1. Design: +1 to +2 (class D), because "sign in and see your own tickets from the chain"
is legible in forty seconds. Completion: +2. Learning: 0. **Materials test: 1 to 2 of 4.** It is a complement
to C2, not a substitute for it, and it can be done on top of any other concept.

### 6.5 C5: the airline seat-release receipt

**What it is.** The one airline-shaped idea where a ledger earns its keep. A holder offers the seat back for a
price, the airline (or its agent) accepts, and both the offer and the acceptance are written on chain with the
compensation claim, so the record of who was offered what, when, and what was paid is public and
tamper-evident. The seat never leaves the airline's inventory host, and the money settles as the airline's own
credit or voucher, which is exactly what TravelX's own product description says it does.

**Chain-native.** The offer, the acceptance, the receipt and the compensation claim. **Not** the seat, the name,
the fare rule or the proration (§3.6).

**Effort, ESTIMATE 12 to 16 hours.** Two instructions, an offer PDA, an accept path with a timeout, the
compensation claim, a demo with two wallets, and tests. It is the escrow-lite shape the design already costed
at 10 to 14 hours as candidate B (`docs/ON-CHAIN-DESIGN.md` §1.3) minus the ticket movement.

**Risk.** (1) It rebuilds the marketplace surface the plan forbids, and a reviewer will ask why a
revenue-management product has a bid surface. (2) The airline side is necessarily **simulated**, and a
simulated counterparty is the thing a four-minute judging pass can smell. (3) It does not serve the pricing
engine's input at all, so it is a second product rather than an extension of this one.

**Fit.** Technology: +3 to +5 (class D), because it is real program surface with a real refusal. Design: +2 if
the demo is two wallets and a timer. Completion: -2 to -3 (class D), because it is the largest build. Learning:
+2. **Materials test: 4 of 4** if it lands.

### 6.6 The comparison a judge would make, and it is not the one we would make

`records/findings/23-hackathon-score-analysis.md` §2.5 records that MLH recommends four minutes per project and
stack ranking, and §4.2 records that every verified winner it read had one thin checkable on-chain artefact, a
working end-to-end story, a live URL, and two of four had a path a judge could operate unaided. Measured
against that, the concepts split by **legibility in forty seconds**, not by depth: C1 is legible and wrong, C2
is legible and defensible, C3 is impressive and hard to explain, C4 is invisible but real, C5 needs a second
actor to make sense.

### 6.7 The dependency nobody should miss

C2, C3 and C5 all assume the devnet publish from
`records/findings/23-hackathon-score-analysis.md` §5.1 T1 has run, because until then every claim in this file
is a design rather than an artefact, and the materials test stays 0 of 4. C1 and C4 can be demonstrated without
a cluster but cannot be **evidenced** without one. **The cheapest sequence is therefore not a concept at all:
fund the authority, run the publish, and then choose.** That sequence costs the operator one faucet step and
about 45 minutes, and it is the only step in this file that is not mine to take.

---

## 7. What this file does not decide

Each of these changes the deliverable or carries a rule collision, so each is the operator's.

1. **Is a person-level claim allowed to gate a sale?** Putting "only verified wallets may buy or receive" into
   the transfer hook makes the chain the arbiter of who may attend. That is a product and ethics decision, not
   an engineering one, and it is the difference between C2 being a feature and C2 being a policy.
2. **Which issuer's word counts?** SAS makes trust a configuration choice. A demo can use the operator's own
   key, which proves nothing; a real deployment needs a partner, and the partner is not in this repository.
3. **What may the chain remember about a person?** `docs/ON-CHAIN-DESIGN.md` §4.2.6 already names this as the
   open question behind the nullifier, and §2.9 here says the only lawful artefact is "a check occurred". A
   commitment derived per event is compatible with that; a stored wallet-to-person map is not.
4. **Does the airline thread belong in this submission at all?** The repository is a ticket-pricing engine for
   a Solana-ticketed events platform. An airline concept costs 12 to 16 hours and is a second product (§6.5);
   the airline material may be better used as **one slide of why the ledger boundary is where it is**, which
   costs nothing.
5. **Does the submission claim to stop scalping?** §4.5 says no measurement supports that claim, and §4.6 says
   the money is in the price level. If the pitch says "stops bots", it is asserting something the literature
   contradicts. `docs/ON-CHAIN-DESIGN.md` §4.2.6 already says the design claims nothing about bots, and the
   honest version of that sentence is stronger than the dishonest one.
6. **Soulbound or resaleable?** C1 is the cheapest concept and it deletes the engine's input (§6.1). If C1 is
   chosen for its legibility, the submission should say plainly that the pricing engine's secondary-market
   input is gone for those events.
7. **The `region` field.** The wire contract has a voluntarily attached region on a destination row. Combined
   with an identity attestation that becomes inferable demographic data on a public ledger. That is a privacy
   decision and it is not mine.

---

## 8. What is not documented, so that nobody invents it

- **No audit report for SAS**, in the repository tree I listed (145 paths) or on any page I read.
  MEASURED-ABSENT.
- **No USD price for Self, ZKPassport, Rarimo, zkPass, Sign Protocol or Quadrata.** Self publishes credits with
  no dollar figure; ZKPassport's pricing page returns 404. MEASURED-ABSENT.
- **No Solana support in any ZK passport vendor's documentation.** MEASURED-ABSENT on the specific pages named
  in §2.3. The absence is from those pages, not proof of non-existence.
- **No private name-equality predicate** offered by any vendor I read. MEASURED-ABSENT.
- **No airline name-change fee.** Twelve carrier pages tried, none readable in this run (§3.3). MEASURED-ABSENT,
  and the degraded search tool is why the list is short.
- **No verified IATA resolution number for "not transferable"**, and none for the Bar Coded Boarding Pass
  ("792" is unverified here). MEASURED-ABSENT.
- **No verified chain, date or current status for the Air Europa NFT ticket drop.** Do not repeat "Algorand,
  November 2022" on this file's authority.
- **No measurement of identity-bound ticketing's effect on resale prices or availability.** MEASURED-ABSENT
  across the literature I read (§4.5).
- **No measurement of the value of resale price data as a primary-pricing input.** MEASURED-ABSENT, and it is
  class E, a genuine research opportunity (§4.7).
- **No measurement of the welfare cost of non-transferability** to an individual holder who cannot attend. The
  nearest is Leslie and Sorensen's no-resale counterfactual, which is a bound and not a direct measure.
- **No mainnet verification of any identity program's deployed state.** No program account was queried in this
  run, so "live on mainnet" always means a vendor or repository says so.

---

## 9. Sources

Fetched 2026-11-07 between 21:36Z and 22:00Z unless a row says otherwise. HTTP status is as returned to this
host. `429` rows are bot checkpoints, and where the content was read from the repository that generates the
page, the repository path is given instead.

| # | source | what it established |
|---|---|---|
| 1 | `https://www.civic.com/news/an-update-on-civic-pass` (200, checked twice) | Civic Pass sunset, the two dates, and that uniqueness went with it |
| 2 | `https://www.civic.com/`, `/sitemap.xml`, `/civic-pass/` (200, 200, 404) | the vendor now sells a GTM agent; no identity product |
| 3 | `registry.npmjs.org/@civic%2Fsolana-gateway-react`, `...%2Fsolana-gatekeeper-lib` (200) | last publishes 2024-12-04 and 2024-08-26 |
| 4 | `api.github.com/repos/civicteam/ociv-gatekeeper` (404); `identity.com` (DNS NXDOMAIN) | the SDK source and the protocol docs are gone |
| 5 | `solana-foundation/solana-attestation-service` README, `program/src/state/{credential,schema,attestation}.rs`, `CHANGELOG.md`, `SECURITY.md`, tree (200) | SAS account model, PDA seeds, issuer-trust warning, token-is-not-the-proof warning, 2.0.0 not deployed, no audit file |
| 6 | `solana-foundation/solana-com` `apps/media/content/posts/solana-attestation-service.mdx` (200) | the 2025-05-23 "now live on Solana mainnet" announcement |
| 7 | `.../apps/docs/content/docs/en/tools/attestations/*.mdx` (200) | "Keep attestation data on Solana for transparency and permanence"; the tooling path |
| 8 | `https://attest.solana.com/` (301), `https://solana.com/docs/tools/attestations` (429) | the docs page is behind a checkpoint; content read from the repo |
| 9 | `docs.self.xyz` how-it-works, billing, `llms.txt` (200) | Celo-only on chain, the fact-versus-data model, per-scope nullifier, credit prices, open SDK deprecated |
| 10 | `docs.zkpassport.id` onchain, personhood, kyc, limitations (200); `/pricing` (404) | Ethereum, Sepolia and Base only; one ID per account, scoped; no name-equality predicate; no price |
| 11 | `docs.rarimo.com` zk-passport, on-chain, registry network info (200) | own L2 (chain 7368), EVM contracts, registry replication |
| 12 | `docs.zkpass.org` technical overview, Solana guide (200) | a zkTLS oracle; on Solana two ECDSA signatures, no published program |
| 13 | `anon-aadhaar` README, `pse.dev/projects/anon-aadhaar` (200); old domain NXDOMAIN | Solidity verifier, Aadhaar only, repos idle since April 2025 |
| 14 | `docs.sign.global` networks, FAQ (200) | EVM chain ids only, no Solana |
| 15 | `quadrata.com`, `docs.quadrata.com/integration` (200) | the seven EVM chains named, no Solana |
| 16 | `docs.passport.xyz` smart contracts, `docs.passport.human.tech/llms.txt` (200) | seven EVM mainnets, no Solana |
| 17 | `worldcoin/world-id-protocol-solana` README, `<that repo>/programs/world-id-solana/src/lib.rs`, `.env.example`, repo metadata (200) | the satellite program, its instruction set, the relay dependency, no nullifier account, created 2026-07-22, zero stars |
| 18 | `docs.world.org/llms.txt` (200) | zero occurrences of "Solana" |
| 19 | `phantom/sign-in-with-solana` README (200) | SIWS proves address ownership |
| 20 | `docs.solanamobile.com` Seed Vault (200) | hardware key custody, still key custody |
| 21 | `solana-foundation/solana-com` fees, fee-structure, compute-budget, constants, transaction-structure, program-deployment, account-structure, tokens/extensions/* (200) | 5,000 lamports, priority-fee formula, 1,232 bytes, 1.4M CU, 200k CU default, 10 MiB accounts, the extension semantics |
| 22 | rent sysvar read and `getMinimumBalanceForRentExemption` at 21:47Z, six sizes | the live 5,080 lamports per byte and every rent figure in this file |
| 23 | `anza-xyz/solana-sdk` `rent/src/lib.rs`; SIMD-0194, SIMD-0437 (200) | the formula, the 6,960 default, the step-down schedule |
| 24 | `anza-xyz/agave` `execution_budget.rs`, `syscalls/src/lib.rs` (200) | the alt_bn128 and curve25519 syscall prices, the CU caps |
| 25 | `Lightprotocol/groth16-solana` README (200) | 78,293 to 108,762 CU per verify, the BSB22 range |
| 26 | `solana-program/token-2022` `extension/account_len.rs`, `transfer_hook/*` (200) | the sizing rule, the 174-byte non-transferable account, the `u64::MAX` sentinel |
| 27 | `zkcompression.com` (200) | compressed state about 15,000 lamports per 100-byte record, "requires custom logic", the Helius banner |
| 28 | `airnewzealand.com/conditions-of-carriage` (200) | "You cannot give or sell your Ticket", the e-ticket definition, the "may not notice" disclaimer |
| 29 | `ecfr.gov` title 49 part 1560 and part 1540 (200) | the verifying-identity-document definitions and the boarding prohibition |
| 30 | `iata.org` PSCRM manual page (200) | the manual's scope and the resolution numbers it names |
| 31 | `iata.org` ONE Order page (200) and `oneorder-resolution-797.pdf` (200, 621,988 bytes) | "the single source of all data related to an order ... is held in the ORA OMS" |
| 32 | `iata.org` NDC, BSP, baggage-tracking, One ID, passenger-data, technical peripheral specifications (200) | Res 787, the BSP scale figures, Res 753 and its proration penalty, the One ID vision, biometric gate readers |
| 33 | `travelx.io`, `travelx.io/news` (200); archive snapshot 2023-04-02 (200) | the P2P and PSS description today; NFTicket and Flybondi in the archive |
| 34 | `chain4travel.com`, `camino.network` (200) | "wound down its operations in spring 2026"; permissioned validators |
| 35 | `blockskye.com` (200); `sita.aero` press path (404); `etherisc.com` (403) | no ledger in the current pitch; two projects unverifiable |
| 36 | `eur-lex.europa.eu` GDPR CELEX 32016R0679 (200) | Articles 4(1), 9(1) and 17(1) |
| 37 | Borenstein and Rose 1994, DOI 10.1086/261950, NBER WP 3785 PDF | 36% dispersion; the 6% / 2% no-show bound |
| 38 | Dana 1998, DOI 10.1086/250014 (abstract) | advance-purchase screening without market power |
| 39 | Courty 2003, DOI 10.1257/089533003765888449 (abstract) | the resale puzzle, and that I read only the abstract |
| 40 | Leslie and Sorensen 2014, DOI 10.1093/restud/rdt033, author PDF in full; NBER WP 15476 in full | 4.1% gross, 2.9% net, >33% absorbed, 46% resold, attendees worse off, 17% |
| 41 | Karp and Perloff 2005, DOI 10.1111/j.1530-9134.2005.00049.x (abstract) | promoters may like scalpers |
| 42 | Cui, Duenyas and Sahin 2014, DOI 10.1287/mnsc.2013.1862 (abstract) | paperless ticketing may reduce organiser revenue |
| 43 | Budish and Bhave 2023, DOI 10.1257/mic.20180230 (abstract) | auctions roughly doubled performer revenue |
| 44 | Vollmer 2025, DOI 10.1111/1756-2171.12501 (abstract) | refunds more efficient on average than resale |
| 45 | Depken 2007, DOI 10.1007/s11127-006-9072-6 (abstract) | anti-scalping laws raise prices and seller revenue |
| 46 | Moretti 2024, DOI 10.1177/10575677241234601 (abstract) | UK touting surviving and thriving |
| 47 | Waterson 2016, UK independent review PDF, read in full | the 14% survey figure, the unsourced 5%, and the identity-technology recommendation |
| 48 | Feulner et al 2022, DOI 10.1007/s12525-022-00573-9 (abstract) | SSI feasibility, and that identification is the hard part |
| 49 | Wang and Ye 2016, DOI 10.1287/trsc.2015.0587, author PDF | hidden-city ticketing is a fare-fence artefact; revenue loss up to half of optimal, no more; re-pricing is the optimal response |
| 50 | Sweeting 2012 and NBER WP 14505 (abstract, PDF) | prices cut 40%+ as the event approaches; dynamic pricing worth about 16% of payoff |

Local evidence read: `docs/ON-CHAIN-DESIGN.md` (in full for §1, §2.5, §2.8, §3.9, §4.2, §11, §12),
`docs/ON-CHAIN-FOR-LAPTOP.md`, `records/ON-CHAIN-RECONCILIATION.md`,
`records/findings/01-b-identifiability.md` §4, `records/findings/23-hackathon-score-analysis.md` (in full),
`programs/cap_hook/src/lib.rs` and its README, `tools/devnet_publish.py`, `tools/solana_sign.py`,
`fixtures/README.md`, and the sibling checkout's `lib/types.ts` for the wire contract.

---

*No source file was changed by this pass and nothing was built. One file was written: this one. Nothing was
committed, nothing was pushed, and no command in this pass signed a transaction, wrote to a cluster, touched a
faucet, or spent anything. The only cluster interaction was read-only: the rent sysvar and
`getMinimumBalanceForRentExemption`.*
