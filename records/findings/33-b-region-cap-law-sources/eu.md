# EU / EEA ticket resale price rules — legal-basis research, cluster "European Union"

Retrieved 2026-11-08. Descriptive only. This is a research record, not legal advice.

Second pass. The first pass read almost no national text and recorded every national row as
`unknown`, because the statute sites are JavaScript shells or bot walls. This pass broke
several of those walls, and the result changes the picture materially:

- **France**: the article was **read in the Journal officiel**. It contains **no price element at
  all** — it is an authorisation rule for habitual resale. The brief's lead statute (loi n° 2012-158)
  was read in full and **does not contain the offence**; the offence is in loi n° 2012-348.
- **Italy**: the *bagarinaggio* comma was **read in the Gazzetta Ufficiale**, and the nominative-ticket
  comma with it. It is a prohibition on selling without being a ticket-system holder, not a percentage
  cap. One discrepancy between the enacted text and AGCOM's rendering is flagged below and matters.
- **Spain**: the 20% figure the brief attributed to Belgium is **real, and Spanish** — RD 2816/1982
  art. 67.1.b. It is also **narrow**: it caps the surcharge of licensed resale outlets only.
- **Belgium**: there is **no 2024–2025 cap law**, and **no 20% allowance**. The 2013 law caps resale at
  the "prix définitif" with **zero** markup. Confirmed from the Constitutional Court's own judgment of
  18 June 2026, which reproduces art. 5 verbatim.
- **Portugal**: `DL 23/2015` is a **media-incentives** instrument, nothing to do with tickets. The
  operative rule appears to be the *crime de especulação* in DL 28/84 art. 35 — but that article was
  **not read**, so the Portuguese row is `D`, not `A`.

## What this run could and could not reach

Worked (text obtained and read):

- `boe.es` — the consolidated RD 2816/1982 in full (official consolidated text, BOE-A-1982-28915).
- `gazzettaufficiale.it` (through the fetcher's proxy pool) — L. 232/2016 art. 1, comma group 501–600,
  verbatim from the Gazzetta; and the conversion law 19A05148.
- `def.finanze.it` — the MEF legislative database, print view of L. 232/2016 art. 1 comma 545-bis with
  its amendment history.
- `fr.const-court.be` — arrêt n° 77/2026 of 18 June 2026 (PDF, text extracted), reproducing art. 5 of
  the Belgian law of 30 July 2013 verbatim.
- Two Journal officiel PDFs hosted off Légifrance: loi n° 2012-158 (JO n° 28 of 2 Feb 2012) and
  loi n° 2012-348 (JO of 13 Mar 2012).
- `senat.fr` — the 2024–2025 comparative table quoting Code pénal art. 313-6-2 and its expose des motifs.
- `agcom.it` — the regulator's secondary-ticketing page.
- `consumerconnect.be`, `portal-cec.consumo.gob.es`, `igac.gov.pt`, `parlamento.pt`, `dgsi.pt`,
  `jurisprudencia.pt`, `cnmc.es`.

Blocked, with the failure quoted:

- `legifrance.gouv.fr` — **`403`, "Just a moment…"**, on every route: plain curl, browser-spoofed
  headers, the fetcher's proxy pool (12 proxies), `r.jina.ai`, and headless Chromium driven through
  Playwright (`Vérification de sécurité en cours … Ray ID: a572685e4dd3fe9e`). Légifrance was **not**
  read; where a fact depends on it, it is flagged.
- `ejustice.just.fgov.be` — `200` with **"Please enable JavaScript to view the page content. Your
  support ID: 7840658572199194826"** (F5/ASM challenge).
- `economie.fgov.be/fr/legislation/loi-du-30-juillet-2013` — same challenge wall
  (**"Your support ID: 3644462778939547703"**).
- `diariodarepublica.pt` — every page is a 2,346-byte OutSystems shell
  (`window.OutSystemsApp = { basePath: '/dr/' }`); `files.dre.pt` PDFs redirect into the same shell
  (`/dr/error`).
- `pgdlisboa.pt` (Procuradoria-Geral Distrital de Lisboa, the standard free consolidated text) —
  connection reset on every attempt (`000`), http and https, `www` and bare host.
- `dre.tretas.org`, `dgsl.pt`, `consumidor.gov.pt`, `portal.oa.pt` (PDF whose fonts are subset-encoded
  — the extracted text is glyph gibberish), `normattiva.it` and `agenziaentrate.gov.it` — `403`
  Cloudflare or `000`.
- `web-fetch`'s `nodriver` transport is unavailable on this host (`ModuleNotFoundError: No module named
  'nodriver'`), and Playwright is not installed for Python (`No module named pip` / `ensurepip`), so the
  browser route was run through the cached Chromium binary with `playwright@1.54.2` from npm.

Consequence: FR, IT, ES and BE are read at first hand. **PT is not.** PT carries `D` and says so.

## Matrix

`cap_basis` reads from the engine's vocabulary. `unknown` means the instrument was not read; it does
not mean "no cap". **Read the coverage column before using any number** — the Spanish percentage cap
is far narrower than its basis suggests.

| member state | cap in force? | basis | coverage | in force from | status |
|---|---|---|---|---|---|
| EU | No instrument located that caps resale price | — | — | — | verified negative for DSA/UCPD/CRD |
| FR | **No price element at all** | `no_price_cap` — organiser authorisation required for habitual resale | all events; binds habitual sellers and intermediaries who "fournissent les moyens" | 2012-03-14 | in force; a reform bill (2024–2025) still before Parliament |
| IT | **No percentage cap**; resale by a non-holder of the ticket system is an administrative offence | `no_price_cap` (the offence is authorisation-based; the only price element is a condition of the safe harbour) | all spectacle tickets; binds sellers and intermediaries; AGCOM enforces | 2017-01-01 | in force; comma 545-bis amended 2025-12-18 |
| ES | **Yes — 20% above the box-office price** | `pct_above_face`, 2000 bps | **licensed resale outlets only** (art. 67.1); street/ambulant resale banned outright (art. 67.2); online resale not capped | 1982-11-26 | in force, consolidated 2023-03-22; a price-cap bill is an *anteproyecto* only |
| BE | **Yes — zero markup** | `face_plus_fees` (the "prix définitif" includes VAT and mandatory add-on services) | all events; habitual resale banned outright, occasional resale capped; buyer may reclaim the excess | 2013-10-01 | in force; upheld by Constitutional Court 2026-06-18 |
| PT | Reported: resale above the organiser's price is a crime | `face` — **reported, not verified** | all events (reported) | unknown | `D` — article not read |
| DE | Unknown | unknown | unknown | unknown | not researched in this pass |
| NL | Unknown | unknown | unknown | unknown | not researched in this pass |
| PL | Unknown | unknown | unknown | unknown | not researched in this pass |
| SE | Unknown | unknown | unknown | unknown | not researched in this pass |
| DK | Unknown | unknown | unknown | unknown | not researched in this pass |
| AT | Unknown | unknown | unknown | unknown | not researched in this pass |
| CZ | Unknown | unknown | unknown | unknown | not researched in this pass |
| HU | Unknown | unknown | unknown | unknown | not researched in this pass |

The shape of the answer, now that the texts are in hand: **Europe does not cap ticket resale price;
it mostly bans or licenses the resale channel.** Of the four jurisdictions read at first hand, one caps
proportionally and only inside a licensed channel (ES), one caps at cost with no markup (BE), and two
contain no price rule at all but an authorisation rule (FR, IT). A rules table that reduces all of
these to "cap bps" would be wrong three times out of four.

---

## EU level

*(Established by the first pass of this run and not re-read here; carried forward unchanged.)*

No adopted EU instrument that caps ticket resale price was located. What was checked, by reading:

**Regulation (EU) 2022/2065 (Digital Services Act).** OJ L 277, 27.10.2022, p. 1–102. In force. The
full official English HTML was downloaded from EUR-Lex and searched: `ticket` occurs **zero** times in
the whole act, `resale` zero times. Recital (6) keeps service-level rules national:
*"This Regulation should apply only to intermediary services and not affect requirements set out in
Union or national law relating to products or services intermediated through intermediary services"*.

**Directive 2005/29/EC (UCPD)** and **Directive 2011/83/EU (CRD)** — base-act HTML searched, `ticket`
zero times in each. Caveat retained: base acts, not consolidated; the 2019/2161 amendments concern
price-reduction announcements, ranking, reviews and personalised pricing, none of them a ticket cap,
but a consolidated-text check is still outstanding.

A "Regulation 2024/… on ticket transparency" was not located. The Digital Fairness Act is **announced**,
not in force; its ticket provisions are unknown, and the Commission page that would have said so
returned 404 at retrieval.

That a national cap is not pre-empted by the DSA follows from recital (6) and from the DSA's own
harmonisation being of *intermediary* duties. Whether a national cap would survive a free-movement or
competition challenge was not researched; no case law was read.

---

## FR — France

**Instrument: Code pénal, art. 313-6-2**, inserted by **loi n° 2012-348 du 12 mars 2012 tendant à
faciliter l'organisation des manifestations sportives et culturelles**, art. 3, I, 1°.

Read at first hand in the Journal officiel (JO of 13 March 2012, texte n° 5 sur 115), hosted at
`https://institut-isbl.fr/wp-content/uploads/sites/3/2014/10/loi_12_mars_2012.pdf`. Légifrance itself
was Cloudflare-blocked on every route, so the JO page image is the primary text used.

Verbatim, from the JO:

> « Art. 313-6-2. Le fait de vendre, d'offrir à la vente ou d'exposer en vue de la vente ou de la
> cession ou de fournir les moyens en vue de la vente ou de la cession des titres d'accès à une
> manifestation sportive, culturelle ou commerciale ou à un spectacle vivant, de manière habituelle et
> sans l'autorisation du producteur, de l'organisateur ou du propriétaire des droits d'exploitation de
> cette manifestation ou de ce spectacle, est puni de 15000 euros d'amende. Cette peine est portée à
> 30000 euros d'amende en cas de récidive.
>
> « Pour l'application du premier alinéa, est considéré comme titre d'accès tout billet, document,
> message ou code, quels qu'en soient la forme et le support, attestant de l'obtention auprès du
> producteur, de l'organisateur ou du propriétaire des droits d'exploitation du droit d'assister à la
> manifestation ou au spectacle. »

**Is there a price element? No.** The offence elements are: selling / offering / exposing / providing
the means to sell, *titles of access to a sporting, cultural or commercial event or a live show*,
**habitually**, **without the authorisation** of the producer, organiser or rights-holder. Price does
not appear. A person reselling their own ticket at cost or at a profit is outside the offence unless
the resale is habitual and unauthorised; a platform that "fournit les moyens" is caught. This is an
authorisation rule, and calling it a price cap would be wrong.

Because the offence is built on "de manière habituelle", the practical effect is that the organiser
controls the secondary channel and its pricing (its own resale platform or none), rather than that a
ceiling is written into the statute.

**Penalty and enforcement.** €15,000 fine, €30,000 on recidivism; art. 3, I, 2° of the same loi also
added art. 313-6-2 to the reference list in art. 313-9 of the Code pénal, which brings attempt and the
aggravated organised-offence rules into play. Ordinary criminal courts; no dedicated ticket-resale
regulator was identified in the texts read.

**Dates and status at 2026-11-08.** Created by the loi of 12 March 2012, published in the JO of
13 March 2012; the article has been in force since 14 March 2012 (the day after publication; a
Légifrance search result also gives "version en vigueur depuis le 14 mars 2012", though Légifrance
itself was not readable). Still in force in 2026.

**The brief's two French leads, checked:**

1. **Loi n° 2012-158** — read in full from its own JO PDF (JO n° 28 of 2 February 2012, 7 pages, text
   extraction complete to the signatures and "Travaux préparatoires"). It is *"visant à renforcer
   l'éthique du sport et les droits des sportifs"*: a sports charter (art. L.131-8-1 code du sport),
   federation rules, doping, broadcasting. **The strings `revente` and `billet` occur zero times.** It
   did not create art. 313-6-2. The Sénat's own 2024 expose des motifs says the rule operates "depuis
   sa mise en œuvre par la loi n° 2012-158" — that attribution is contradicted by the JO text of
   2012-158 and is not adopted here. The brief's pointer to 2012-158 is a dead lead.
2. **A 2023–2026 reform** — there is one, and it is **not law**. *Proposition de loi encadrant
   l'activité des plateformes de revente agissant en qualité de tiers de confiance*, texte n° 194
   (2024-2025) de M. Cédric Chevalier et plusieurs de ses collègues, déposé au Sénat le 7 décembre
   2024. The Sénat's comparative table (`https://www.senat.fr/tableau-historique/ppl24-194.html`) is
   headed "La loi en construction" and reproduces art. 313-6-2 under "Dispositions en vigueur" — which
   is also the second independent official source for the article's current wording, word for word
   identical to the JO. The bill would add a consumer right to resell through an approved
   third-party-trustee platform, with a décret for accreditation — **no price cap in it either**.
   Status: `announced`, not in force.

The expose des motifs is also the clearest statement of what the current rule does, and it is quoted
here because it is the Sénat's own characterisation, not this run's: the law "interdit la revente, par
des tiers, en l'absence d'autorisation expresse des organisateurs d'événements … avec des peines
pouvant atteindre 15 000 euros d'amende et le double en cas de récidive".

## IT — Italy

**Instrument: Legge 11 dicembre 2016, n. 232 (bilancio di previsione 2017), art. 1, comma 545**, read
verbatim from the Gazzetta Ufficiale, testo originario, comma group 501–600
(`gazzettaufficiale.it/atto/serie_generale/caricaArticolo?...art.codiceRedazionale=16G00242&art.progressivo=6`).

Verbatim (the operative sentence):

> « Al fine di contrastare l'elusione e l'evasione fiscale, nonché di assicurare la tutela dei
> consumatori e garantire l'ordine pubblico, la vendita o qualsiasi altra forma di collocamento di
> titoli di accesso ad attività di spettacolo effettuata da soggetto diverso dai titolari, anche sulla
> base di apposito contratto o convenzione, dei sistemi per la loro emissione è punita, salvo che il
> fatto non costituisca reato, con l'inibizione della condotta e con sanzioni amministrative pecuniarie
> da 5.000 euro a 180.000 euro … »

and the exemption, verbatim:

> « Non è comunque sanzionata la vendita o qualsiasi altra forma di collocamento di titoli di accesso
> ad attività di spettacolo effettuata da una persona fisica in modo occasionale, purché senza finalità
> commerciali. »

**Is there a price element? Not in the offence.** The offence is *selling, or any other form of
placing on the market, tickets to spectacle events, by a person other than the holders of the ticket
emission systems*. It is an administrative offence, not a price rule: no percentage, no ceiling, no
"above face value" element. What it does is make commercial secondary ticketing itself unlawful, and
leave a narrow exemption for occasional non-commercial sales by a natural person. **This is a
prohibition on the channel, and must not be encoded as a bps cap.**

**A discrepancy that matters, flagged rather than resolved.** AGCOM's own secondary-ticketing page
quotes the exemption as *"la vendita **ad un prezzo uguale o inferiore a quello nominale** di titoli di
accesso ad attività di spettacolo effettuata da una persona fisica in modo occasionale, purché senza
finalità commerciali"*. The words "ad un prezzo uguale o inferiore a quello nominale" are **not in the
Gazzetta text as enacted**. Either a later amending act added them (so that lawful private resale in
Italy is limited to at-or-below face) or AGCOM is paraphrasing. This run did **not** find the amending
act, so the price condition is recorded as unverified. It changes the engine's behaviour for Italy: if
the condition is real, private resale above face is unlawful; if not, private occasional resale is
unconstrained as to price. **Do not assume either.** The candidate amending vehicle, per commentary
only, is the 2019 budget law; the only 2019 amendment this run could read is the one below, which
touches comma 545-bis, not comma 545.

**Nominative tickets — comma 545-bis**, verbatim from the Gazzetta (text of the conversion law
19A05148, art. 4):

> « 545-bis. A decorrere dal 1° luglio 2019, ferme restando le specifiche disposizioni in materia di
> manifestazioni sportive, per le quali continua ad applicarsi la specifica disciplina di settore, i
> titoli di accesso ad attività di spettacolo in impianti con capienza superiore a 5.000 spettatori sono
> nominativi, previa efficace verifica dell'identità … »

Introduced by **decreto-legge 28 giugno 2019, n. 59**, converted by **legge 8 agosto 2019, n. 81**
(GU n. 188 of 12 August 2019), art. 4 of which added "lo spettacolo viaggiante e" to the exclusions.
The comma excludes travelling shows and opera, symphonic and chamber music, prose, jazz, ballet, dance
and contemporary circus; the Agenzia delle Entrate sets the technical rules by which the primary sites,
authorised box offices and official event sites put nominative tickets back on sale or change the name.

**Amendment after that, read at first hand.** The MEF legislative database (`def.finanze.it`, print of
art. 1 comma 545-bis) states: *"In vigore dal 18/12/2025 — Modificato da: Legge del 02/12/2025 n. 182
Articolo 67"*, and the amended text now reads «Sono esclusi da tale prescrizione lo spettacolo
viaggiante, ivi compresi i parchi di divertimento, e gli spettacoli di attività lirica, sinfonica e
cameristica, prosa, jazz, balletto, danza e circo contemporaneo, nonché le manifestazioni carnevalesche,
i corsi mascherati, le rievocazioni storiche, giostre e manifestazioni similari». So the Italian
nominative-ticket regime was widened in scope of exclusions as recently as 18 December 2025.

**Penalty and enforcement.** Inhibition of the conduct plus administrative fines of €5,000–€180,000;
where the conduct is carried out over electronic communications, removal of content or, in the most
serious cases, blacking out the website, without prejudice to damages claims. Enforcement is expressly
given to **AGCOM** ("L'Autorità per le garanzie nelle comunicazioni e le altre autorità competenti
effettuano i necessari accertamenti e interventi, agendo d'ufficio ovvero su segnalazione degli
interessati"). AGCOM's press pages show it is live: a first sanction of €675,000 against a professional
seller approved 30 July 2025, and an intervention on Milano–Cortina Olympic touting dated 23 January
2026.

**Dates and status at 2026-11-08.** L. 232/2016 in force 1 January 2017; comma 545 and 545-bis still in
force, 545-bis as amended 18 December 2025.

## ES — Spain

**Instrument: Real Decreto 2816/1982, de 27 de agosto, por el que se aprueba el Reglamento General de
Policía de Espectáculos Públicos y Actividades Recreativas**, art. 67. Read in full from the BOE's
consolidated text, `https://www.boe.es/buscar/act.php?id=BOE-A-1982-28915` (BOE-A-1982-28915; BOE
núm. 267 of 6 November 1982; **entrada en vigor 26 November 1982**; consolidated text last updated
**22 March 2023**).

Verbatim, art. 67.1.b:

> « El recargo de reventa no podrá exceder en ningún caso del 20 por 100 sobre el precio marcado para
> el supuesto de venta directa al público en las taquillas o expendedurías de la propia Empresa. »

Verbatim, art. 67.1.a and 67.2, because they define the coverage:

> « a) Las Empresas sólo podrán distribuir entre las Entidades autorizadas para la reventa un máximo del
> 25 por 100 de las localidades de cada clase que no sean objeto de abonos. »
>
> « 2. Queda terminantemente prohibida la venta y la reventa callejera o ambulante de localidades. »

**This is a real 20%-above-face cap — and it is much narrower than a cap.** Art. 67.1 is headed by the
condition "La autorización concedida a las Empresas para vender sus billetes en expendedurías o
despachos especiales, sin recargo alguno, se podrá hacer extensiva a las agrupaciones o asociaciones
que lo soliciten de los Alcaldes". So the 20% ceiling binds **licensed resale outlets** — associations
and groupings authorised by the mayor, capped also at 25% of the non-season-ticket seats — reselling
against the company's own marked box-office price. It is **not** a cap on peer-to-peer resale, on
online secondary platforms, or on a private individual reselling a ticket. The engine must not read
`pct_above_face 2000` off this row and apply it to Spanish online resale. The other half of art. 67 is a
flat prohibition of street and ambulant sale, which is an authorisation/place rule, not a price rule.

**Penalty and enforcement.** Art. 81 lists the infractions and art. 81.34 is the ticket one:
*"La reventa callejera o ambulante de billetes o localidades o la percepción de sobreprecios superiores
a los autorizados."* Art. 67.2 provides seizure of the tickets ("decomiso de las localidades") plus a
fine under arts. 81 ff. Art. 82.3 sets the ceilings: municipal authorities within the limits of local
regime legislation, civil governors up to 500,000 pesetas, the Minister of the Interior up to 1,000,000
pesetas. (The peseta figures are still in the consolidated text as published; they were not read in any
converted form, and no euro figure is asserted here.)

**The brief's "2024 real decreto" — refuted.** No such instrument exists in force. Two things are real
and different:

1. An official Spanish government page — Centro Europeo del Consumidor, under `consumo.gob.es` —
   states that "el Gobierno de España está trabajando en la elaboración de un proyecto de Disposición
   de carácter general sobre las actividades de venta y reventa telemática de entradas para espectáculos
   culturales", i.e. a **draft**. That is the state of the art as of the page read.
2. The vehicle is the **Anteproyecto de Ley de Consumo Sostenible** (Ministerio de Derechos Sociales,
   Consumo y Agenda 2030), approved in first reading by the Consejo de Ministros on 1 July 2025. Per
   press reporting and a CNMC report of February 2026 (IPN/CNMC/053/25), it would limit resale to the
   original price plus the variation of the IPC. **Confidence D** — the draft's text was not obtained;
   the press and the CNMC reference are the only basis. It is `announced`, not in force, at 2026-11-08.

Two verified negatives from the first pass stand and are worth keeping: **Ley 34/2002** (e-commerce) and
**Ley 19/2007** (sports violence) each contain zero occurrences of `reventa` and no ticket-resale
provision. Regional (comunidad autónoma) rules were **not** researched in either pass; if the engine
needs Spain beyond the state level, that is a second layer, not a footnote.

## BE — Belgium

**Instrument: Loi du 30 juillet 2013 relative à la revente de titres d'accès à des événements**
(Moniteur belge 6 September 2013; numéro 2013011413; entry into force **1 October 2013**).

Read at first hand from **Cour constitutionnelle, arrêt n° 77/2026 du 18 juin 2026**
(`https://fr.const-court.be/77/2026.pdf`), which reproduces art. 5 verbatim in a preliminary ruling
referred by the Cour de cassation. The text was cross-checked against two independent Justel mirrors
(`refli.be/fr/lex/2013011413`, `lisloi.be`) for arts. 6 to 9; `ejustice.just.fgov.be` and
`economie.fgov.be` both served bot-walls.

Verbatim, art. 5:

> « § 1er. La revente de manière habituelle est interdite. Le fait d'exposer en vue de la revente de
> manière habituelle, et le fait de fournir les moyens qui seront utilisés pour une revente de manière
> habituelle, sont interdits.
>
> § 2. La revente de manière occasionnelle à un prix supérieur au prix tel que défini à l'article 4,
> § 1er, est interdite. »

**What the cap is, and what it is not.** Two limbs:

- **Habitual resale is banned outright**, at any price, as is exposing for it and providing the means.
- **Occasional resale is permitted only at or below the "prix définitif"** — zero markup. The
  Constitutional Court states what that price includes: *"la taxe sur la valeur ajoutée, toutes autres
  taxes, ainsi que le coût de tous les services à payer obligatoirement en supplément par le
  consommateur (article 2, 6°)"*. So the base is **face plus VAT plus mandatory add-on services**, and
  the value is **no uplift**. Art. 5 § 3 adds a timing ban (no resale before the initial sale begins)
  and § 4 bans selling privileged and promotional tickets that were never initially sold.

**The brief's "20% above face, 2024–2025 law" — refuted on both counts.** There is **no 20% allowance**
in the Belgian text: the permitted margin over the definitive price is zero. And there is **no 2024–2025
cap statute**: the operative and litigated instrument in 2026 is still the 2013 law, as the
Constitutional Court's June 2026 judgment shows. The 20% figure is Spanish, and it is 20% *over the
box-office price for licensed resale outlets* (see §ES). A 20% Belgian allowance would have been
`pct_above_face` / `2000`; the actual value is `face_plus_fees` with **no** markup.

**Penalty and enforcement.** Art. 9: infringements of arts. 4 and 5 are subject to a **level-2 criminal
fine** under art. XV.70 of the Code de droit économique, **or** an administrative fine of the same level
under art. XV.60/20. Art. 8/1–8/3 (inserted by the loi of 29 September 2020, in force 30 November 2020)
route the case: the public prosecutor decides whether to prosecute, transact or mediate, and if it
declines or stays silent for three months, the SPF Économie enforcement agents open the administrative
track. Art. 6 gives the buyer a private right: any amount paid above the art. 4 §1 price is an undue
payment, recoverable from the reseller regardless of whether an earlier reseller also infringed. The
level-2 amount itself was not read, so no figure is given.

**Enforcement in practice.** The Constitutional Court judgment recites the underlying prosecution: a
company — Viagogo GmbH appears among the parties — prosecuted before the Tribunal de première instance
d'Anvers for "avoir participé à la revente habituelle ou occasionnelle de titres d'accès à des événements
à un prix supérieur au prix définitif", convicted 21 April 2022, upheld by the Cour d'appel d'Anvers on
12 September 2024, then on cassation to the Constitutional Court, which on 18 June 2026 held art. 5 does
**not** violate arts. 38 and 127 §1, 1° of the Constitution (the communities' competence over cultural
matters). So: the 2013 cap is not merely on the books; it has been enforced against a major secondary
platform, and it survived a competence challenge in 2026.

**Dates and status at 2026-11-08.** In force since 1 October 2013; amended 2020 (enforcement
procedure) and by the loi of 28 April 2022 (art. 6, in force 1 January 2023, re-pointing the civil
restitution reference); upheld 18 June 2026.

## PT — Portugal

**Not read. Confidence D. The instrument below is identified, not verified.**

What the brief asked to be checked, and what happened:

- **Decreto-Lei n.º 23/2015** — **refuted as a ticket instrument.** A Diário da República search result
  gives its title as *"O regime de incentivos do Estado à comunicação social, atualmente previsto no
  Decreto-Lei n.º 7/2005"* — media incentives. The instrument itself was not read (DRE is a JS shell),
  so this is a refutation from the official catalogue entry, not from the text. Either way it is not a
  ticket-resale rule, and the brief's pairing is a dead lead.
- **A 2024 resale law** — none found. What exists is a **proposal**: DECO PROteste published a
  "PROPOSTA DE REVISÃO LEI DOS ESPETÁCULOS" in July 2026. No adopted 2024–2026 instrument was located.
- **Whether it caps** — two independent secondary sources, concordant, say the operative rule is the
  *crime de especulação* of **Decreto-Lei n.º 28/84, de 20 de janeiro** (Regime das Infrações
  Antieconómicas e Contra a Saúde Pública), **artigo 35.º**:
  - DECO PROteste (18 May 2026): "Vender um bilhete para um espetáculo a um preço superior ao definido
    pela organização do evento é proibido, em Portugal. Considerado crime de especulação, pode ser
    punido com pena de prisão entre seis meses e três anos, e multa não inferior a 100 dias. Se o
    vendedor tiver agido de forma negligente, a pena de prisão aplicável desce para um ano e a multa
    para um mínimo de 40 dias." It adds that resale is permitted only if the seller makes no gain.
  - Diário de Viseu (13 July 2026): same instrument and same penalty bands, and the same point that
    "o que a lei pune não é o ato de revender, mas sim de lucrar com essa revenda".

  Taken together that is a **`face` cap in criminal clothing**: resale at cost is lawful, resale above
  the organiser's price is a crime. But this run did **not** read art. 35.º, so no quote is offered and
  the whole row is `D`.

**Why it was not read — every route, with its failure:**

- `diariodarepublica.pt/dr/detalhe/decreto-lei/28-1984-*` — `200` with a 2,346-byte OutSystems shell
  (`window.OutSystemsApp = { basePath: '/dr/' }`), zero occurrences of `especula`.
- `files.dre.pt/1s/1984/01/01700/01730177.pdf` and `files.diariodarepublica.pt/...` — `301`, resolving
  to `https://diariodarepublica.pt/dr/error`.
- `pgdlisboa.pt/leis/lei_mostra_articulado.php?...nid=172...` — connection reset, `000`, on six attempts
  across http/https, `www` and bare host, with and without TLS 1.2 pinning.
- `dre.tretas.org`, `dgsl.pt/legislacao/decreto-lei-decreto-lei-n-28-84/artigo/35`,
  `consumidor.gov.pt` — `403`, "Just a moment…".
- `portal.oa.pt` PDF (Ordem dos Advogados, an article on art. 35.º) — downloaded, 30 pages, but the
  fonts are subset-encoded and the extracted text is glyph gibberish; unusable as a quote.
- `dgsi.pt` — reachable, and the Tribunal da Relação de Lisboa judgment of 26 January 2023 (proc.
  1031/22.5SILSB.L1-9) confirms art. 35.º n.º 1 al. b) is the *especulação* offence, but on a taxi fare
  and without transcribing the article.

**Enforcement body**: criminal courts and the Ministério Público, on the face of the sources above. A
regulatory role for IGAC was **not** verified; IGAC's site is reachable and its legislation index was
searched, with no ticket-resale page found.

## DE, NL, PL, SE, DK, AT, CZ, HU

Not researched in this pass. Each is one `unknown` row in the JSON below, with no instrument, no
number and no cap asserted. Nothing from the first pass is promoted: the first pass read no instrument
from any of them either, and the brief's expectations about Germany (competition law rather than a
priced rule) remain untested.

---

## What changed from the first pass, in one place

| jurisdiction | first pass | this pass |
|---|---|---|
| FR | `unknown`, source blocked | `A` — art. 313-6-2 read in the JO; **no price element**; loi 2012-158 read and excluded |
| IT | `unknown`, JS shell | `A` — comma 545 and 545-bis read in the Gazzetta; offence is channel-based; 2025 amendment found |
| ES | partial negative | `A` — RD 2816/1982 art. 67 read on BOE; **20% cap, licensed outlets only**; 2024 real decreto refuted |
| BE | `unknown`, "no number asserted" | `A` — art. 5 read via the Constitutional Court; **zero markup over the definitive price**; 20% claim refuted |
| PT | `unknown` | `D` — DL 23/2015 refuted; art. 35.º DL 28/84 identified, not read |

Two brief leads are now dead (FR loi 2012-158, PT DL 23/2015), one is refuted (the Belgian 20%), and
the 20% figure turns out to belong to a 1982 Spanish regulation that only caps licensed resale outlets.

## Unknowns that survive

1. **Italy:** whether the words "ad un prezzo uguale o inferiore a quello nominale" are in the current
   text of comma 545. This is the one open question that changes the answer for a jurisdiction.
2. **Portugal:** art. 35.º of DL 28/84 has not been read. Whether the ticket limb is an alínea of art.
   35, whether there is a separate spectacle-ticket instrument, and the exact penalty bands, all rest on
   secondary sources.
3. **Spain:** the text of the Anteproyecto de Ley de Consumo Sostenible; the IPC mechanism; and the
   regional (comunidad autónoma) rules, which were not researched at all.
4. **Belgium:** the level-2 fine amount under art. XV.70 CDE, and whether any amendment after the
   28 April 2022 law touched arts. 4–6.
5. **France:** whether the Sénat's attribution of art. 313-6-2 to loi 2012-158 has any basis beyond
   error — the JO text of 2012-158 says no.
6. **All five:** the consolidated text on the official statute database (Légifrance, ejustice, DRE,
   Normattiva) was never read directly for FR, BE, PT or IT. The substitutes were the Journal officiel
   page image, a Constitutional Court judgment, the Gazzetta Ufficiale and the MEF database — all
   official, but not the consolidated code.

---

```json
{
  "entries": {
    "EU": [
      {"jurisdiction":"EU","instrument_kind":"none_identified","citation":"Regulation (EU) 2022/2065 (Digital Services Act), OJ L 277, 27.10.2022, p. 1; Directive 2005/29/EC; Directive 2011/83/EU — none contains a ticket-resale price rule","url":"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2065","status":"in_force","in_force_from":null,"in_force_to":null,"applies_to":"none","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"none","summary":"No EU instrument read imposes a ticket-resale price obligation; nothing to penalise at EU level.","max":null},"enforcement_body":"national authorities and courts; no EU ticket-resale price enforcer identified","quoted_provision":"This Regulation should apply only to intermediary services and not affect requirements set out in Union or national law relating to products or services intermediated through intermediary services","notes":"Carried forward from the first pass of this run, not re-read here. Full official English HTML of the DSA searched: 'ticket' 0 occurrences, 'resale' 0. UCPD base act: 'ticket' 0. CRD base act: 'ticket' 0 (base acts, not consolidated; a consolidated check is still outstanding). Recital 6 leaves service-level rules to national law, which is why a per-member-state table is correct. No 'Regulation 2024/... on ticket transparency' was located; the Commission digital-fairness page returned 404, so any Digital Fairness Act is unverified and must be treated as announced, not in force. Whether a national cap would survive a free-movement or competition challenge was not researched.","confidence":"A","retrieved_at":"2026-11-08T05:51:12Z"}
    ],
    "FR": [
      {"jurisdiction":"FR","instrument_kind":"primary_legislation","citation":"Code pénal, art. 313-6-2, inserted by loi n° 2012-348 du 12 mars 2012 tendant à faciliter l'organisation des manifestations sportives et culturelles, art. 3, I, 1°","url":"https://institut-isbl.fr/wp-content/uploads/sites/3/2014/10/loi_12_mars_2012.pdf","status":"in_force","in_force_from":"2012-03-14","in_force_to":null,"applies_to":"all_resale","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"criminal","summary":"Délit: 15 000 EUR fine, 30 000 EUR on recidivism. Art. 3, I, 2° of the same loi added art. 313-6-2 to the art. 313-9 Code pénal list, which brings attempt and the aggravated organised-offence rules into play.","max":"30000 EUR"},"enforcement_body":"ordinary criminal courts; no dedicated ticket-resale regulator identified in the texts read","quoted_provision":"Le fait de vendre [...] des titres d'accès à une manifestation sportive, culturelle ou commerciale ou à un spectacle vivant, de manière habituelle et sans l'autorisation du producteur, de l'organisateur..., est puni de 15000 euros d'amende.","notes":"PRICE ELEMENT: none. The offence is habitual unauthorised resale (or providing the means), so this is an authorisation rule, not a cap. Text read verbatim in the Journal officiel of 13 March 2012 (texte n° 5 sur 115) hosted off Légifrance; Légifrance itself returned a Cloudflare 'Just a moment...' 403 on every route including headless Chromium via Playwright (Ray ID a572685e4dd3fe9e), so the consolidated Code pénal was not read. The article's wording was independently confirmed word-for-word by the Sénat's comparative table (senat.fr/tableau-historique/ppl24-194.html), which lists it under 'Dispositions en vigueur'. in_force_from: JO publication 13 March 2012, in force the following day; a Légifrance search-result snippet also gives 'version en vigueur depuis le 14 mars 2012' but Légifrance was not readable. LEAD CHECKED AND EXCLUDED: loi n° 2012-158 du 1er février 2012 (named in the brief) was read in full from its JO PDF — it concerns sports ethics, a federation charter, doping and broadcasting, and contains ZERO occurrences of 'revente' and 'billet'. It did not create art. 313-6-2, notwithstanding the Sénat's own expose des motifs saying the rule operates 'depuis sa mise en œuvre par la loi n° 2012-158'.","confidence":"A","retrieved_at":"2026-11-08T06:23:26Z"},
      {"jurisdiction":"FR","instrument_kind":"announced_policy","citation":"Proposition de loi encadrant l'activité des plateformes de revente agissant en qualité de tiers de confiance, texte n° 194 (2024-2025), déposé au Sénat le 7 décembre 2024","url":"https://www.senat.fr/tableau-historique/ppl24-194.html","status":"announced","in_force_from":null,"in_force_to":null,"applies_to":"all_resale","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"unknown","summary":"Not in force; no penalty enacted.","max":null},"enforcement_body":"unknown — would create an accreditation regime for platforms, with terms set by décret","quoted_provision":"Tout consommateur a le droit, sans l'autorisation mentionnée au premier alinéa, de revendre sur une plateforme numérique agissant en qualité de tiers de confiance les titres d'accès qu'il a acquis","notes":"BILL, NOT LAW. The Sénat page is headed 'La loi en construction'. It would add a consumer right to resell through an accredited third-party-trustee platform; it contains no price cap either. No date of adoption, no committee stage completed at retrieval. Recorded so the engine does not mistake a pending reform for a price rule.","confidence":"B","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "IT": [
      {"jurisdiction":"IT","instrument_kind":"primary_legislation","citation":"Legge 11 dicembre 2016, n. 232 (bilancio di previsione dello Stato 2017), art. 1, comma 545","url":"https://www.gazzettaufficiale.it/atto/serie_generale/caricaArticolo?art.versione=1&art.idGruppo=1&art.flagTipoArticolo=0&art.codiceRedazionale=16G00242&art.idArticolo=1&art.idSottoArticolo=1&art.idSottoArticolo1=10&art.dataPubblicazioneGazzetta=2016-12-21&art.progressivo=6","status":"in_force","in_force_from":"2017-01-01","in_force_to":null,"applies_to":"all_resale","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"administrative","summary":"Inhibition of the conduct plus administrative fines of 5 000 to 180 000 EUR; where committed over electronic communications, removal of the content or, in the most serious cases, blacking out the website, without prejudice to damages claims.","max":"180000 EUR"},"enforcement_body":"Autorità per le garanzie nelle comunicazioni (AGCOM) and the other competent authorities, acting ex officio or on a report by an interested party","quoted_provision":"la vendita [...] di titoli di accesso ad attività di spettacolo effettuata da soggetto diverso dai titolari ... dei sistemi per la loro emissione è punita ... con sanzioni amministrative pecuniarie da 5.000 euro a 180.000 euro","notes":"PRICE ELEMENT: none in the offence. It bans selling or otherwise placing spectacle tickets on the market by anyone other than the holders of the ticket emission systems; the only exemption is an occasional, non-commercial sale by a natural person. This is a channel prohibition and must not be encoded as a bps cap. Text read verbatim from the Gazzetta Ufficiale testo originario. UNRESOLVED AND MATERIAL: AGCOM's own page quotes the exemption as 'la vendita ad un prezzo uguale o inferiore a quello nominale di titoli di accesso ... effettuata da una persona fisica in modo occasionale, purché senza finalità commerciali'. Those price words are NOT in the Gazzetta text as enacted (which reads only 'effettuata da una persona fisica in modo occasionale, purché senza finalità commerciali'). Either a later amendment added them, or AGCOM paraphrases. This run did not find the amending act; commentary points at the 2019 budget law as the candidate. Do not assume either way: if the condition is real, private resale above face is unlawful. in_force_from is the law's general entry into force (1 January 2017); no article-specific deferral was read for comma 545.","confidence":"A","retrieved_at":"2026-11-08T06:23:26Z"},
      {"jurisdiction":"IT","instrument_kind":"primary_legislation","citation":"Legge 11 dicembre 2016, n. 232, art. 1, comma 545-bis, introduced by decreto-legge 28 giugno 2019, n. 59, convertito dalla legge 8 agosto 2019, n. 81, art. 4; as amended by legge 2 dicembre 2025, n. 182, art. 67","url":"https://def.finanze.it/DocTribFrontend/executePrintArticolo.do?id=%7B69EB8B9F-0FA9-47CD-B934-5004D8C356E4%7D&codiceOrdinamento=0000000000000010000000000000000000000000005459999900002000000000000000000000000000000000000000000000000000000000000000000000000000","status":"in_force","in_force_from":"2019-07-01","in_force_to":null,"applies_to":"all_resale","cap_basis":"no_price_cap","cap_value":null,"penalty":{"kind":"administrative","summary":"Nominative-ticket duty; the sanction for breaching it was not read, so none is asserted. The ticket-resale sanction sits in comma 545.","max":null},"enforcement_body":"Agenzia delle Entrate sets the technical rules; AGCOM is consulted. No enforcement body for the nominative duty itself was read.","quoted_provision":"i titoli di accesso ad attività di spettacolo in impianti con capienza superiore a 5.000 spettatori sono nominativi, previa efficace verifica dell'identità, e riportano la chiara indicazione del nome e del cognome del soggetto che fruisce del titolo di accesso","notes":"Nominative-ticket rule, not a price rule. Venues over 5 000 capacity; identity check at entry; exclusions are travelling shows (now including amusement parks) and opera, symphonic and chamber music, prose, jazz, ballet, dance, contemporary circus, and since 18 December 2025 carnival events, masked parades, historical re-enactments, jousts and similar. The Agenzia delle Entrate sets how primary sites, authorised box offices and official event sites put nominative tickets back on sale or change the holder's name (provvedimento of 27 June 2019, amended 25 September 2025). Sports events keep their own separate regime. Amendment status read at first hand from the MEF legislative database: 'In vigore dal 18/12/2025 — Modificato da: Legge del 02/12/2025 n. 182 Articolo 67'.","confidence":"A","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "ES": [
      {"jurisdiction":"ES","instrument_kind":"secondary_legislation","citation":"Real Decreto 2816/1982, de 27 de agosto, por el que se aprueba el Reglamento General de Policía de Espectáculos Públicos y Actividades Recreativas, art. 67","url":"https://www.boe.es/buscar/act.php?id=BOE-A-1982-28915","status":"in_force","in_force_from":"1982-11-26","in_force_to":null,"applies_to":"all_resale","cap_basis":"pct_above_face","cap_value":{"kind":"bps","bps":2000},"penalty":{"kind":"administrative","summary":"Art. 81.34 makes 'la reventa callejera o ambulante de billetes o localidades o la percepción de sobreprecios superiores a los autorizados' an infraction; art. 67.2 adds seizure of the tickets (decomiso). Sanctioned per art. 82: fine (municipal limits; up to 500 000 pesetas for civil governors, 1 000 000 pesetas for the Minister of the Interior), suspension or prohibition of specific events, deregistration, closure.","max":"1000000 ESP (art. 82.3, Minister of the Interior ceiling, as published)"},"enforcement_body":"municipal authorities, civil governors and the Minister of the Interior (art. 82.3)","quoted_provision":"El recargo de reventa no podrá exceder en ningún caso del 20 por 100 sobre el precio marcado para el supuesto de venta directa al público en las taquillas o expendedurías de la propia Empresa.","notes":"SCOPE LIMIT, read this before using the number. The 20% ceiling is in art. 67.1 for 'las agrupaciones o asociaciones que lo soliciten de los Alcaldes' — resale outlets licensed by the mayor — reselling against the company's own marked box-office price, and they may receive at most 25% of the non-season seats (art. 67.1.a). It does NOT cap peer-to-peer resale, online secondary platforms, or a private individual reselling a ticket. Encoding it as a general 2000 bps cap on Spanish resale would be wrong. The rest of art. 67 is an authorisation and place rule (art. 67.2 bans street and ambulant sale outright). Consolidated text read on BOE (BOE-A-1982-28915, BOE núm. 267 of 6 November 1982, entrada en vigor 26 November 1982, last consolidated update 22 March 2023). Still in force: no repeal marker on art. 67 in the consolidated text.","confidence":"A","retrieved_at":"2026-11-08T06:23:26Z"},
      {"jurisdiction":"ES","instrument_kind":"announced_policy","citation":"Anteproyecto de Ley de Consumo Sostenible (Ministerio de Derechos Sociales, Consumo y Agenda 2030), approved in first reading by the Consejo de Ministros on 1 July 2025 — reported to limit ticket resale to the original price plus the variation of the IPC","url":"https://portal-cec.consumo.gob.es/es/informacion-general/compras-online/reventa-de-entradas","status":"announced","in_force_from":null,"in_force_to":null,"applies_to":"all_resale","cap_basis":"pct_above_face","cap_value":null,"penalty":{"kind":"unknown","summary":"Not in force; no penalty enacted.","max":null},"enforcement_body":"unknown","quoted_provision":"el Gobierno de España está trabajando en la elaboración de un proyecto de Disposición de carácter general sobre las actividades de venta y reventa telemática de entradas para espectáculos culturales","notes":"DRAFT, NOT LAW, as at 2026-11-08. The brief's '2024 real decreto on ticket resale' does not exist in force; what exists is this anteproyecto. The official Centro Europeo del Consumidor page (consumo.gob.es) confirms only that a general instrument is being drafted — it gives no number, no date and no percentage. The IPC-indexed ceiling, the 1 July 2025 Consejo de Ministros first reading, and the CNMC report IPN/CNMC/053/25 of February 2026 recommending transparency first come from press and commentary, hence confidence D. Because the ceiling is indexed rather than fixed, cap_value is null: it is not expressible as bps without a reference month, and inventing one would be fabrication. Regional (comunidad autónoma) rules were not researched in either pass.","confidence":"D","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "BE": [
      {"jurisdiction":"BE","instrument_kind":"primary_legislation","citation":"Loi du 30 juillet 2013 relative à la revente de titres d'accès à des événements (Moniteur belge 6 septembre 2013; numéro 2013011413), articles 2 to 9","url":"https://fr.const-court.be/77/2026.pdf","status":"in_force","in_force_from":"2013-10-01","in_force_to":null,"applies_to":"all_resale","cap_basis":"face_plus_fees","cap_value":null,"penalty":{"kind":"criminal","summary":"Art. 9: infringements of arts. 4 and 5 are subject to a level-2 criminal fine under art. XV.70 of the Code de droit économique, or an administrative fine of the same level under art. XV.60/20. Arts. 8/1-8/3 (inserted 29 September 2020, in force 30 November 2020) let the public prosecutor choose prosecution, transaction or mediation, with the administrative track opening if it declines or stays silent for three months. Art. 6 gives the buyer a civil right to recover any amount paid above the art. 4 §1 price, independently of any earlier infringement.","max":null},"enforcement_body":"criminal courts and the public prosecutor; SPF Économie enforcement agents for the administrative track (Code de droit économique Book XV)","quoted_provision":"§ 1er. La revente de manière habituelle est interdite. § 2. La revente de manière occasionnelle à un prix supérieur au prix tel que défini à l'article 4, § 1er, est interdite.","notes":"CAP BASIS AND VALUE: the ceiling is the 'prix définitif', with ZERO markup — habitual resale is banned outright, and occasional resale may not exceed the definitive price. The Constitutional Court states what that price includes: 'la taxe sur la valeur ajoutée, toutes autres taxes, ainsi que le coût de tous les services à payer obligatoirement en supplément par le consommateur (article 2, 6°)', hence face_plus_fees rather than face. BRIEF'S LEAD REFUTED TWICE: there is no 20% allowance in the Belgian text (the permitted margin is zero) and no 2024-2025 cap statute (the 2013 law is what was litigated in 2026). The 20% figure belongs to Spain's RD 2816/1982 art. 67.1.b. Art. 5 §3 also bans resale before the initial sale begins; §4 bans selling privileged and promotional tickets never initially sold. SOURCE: art. 5 read verbatim from Cour constitutionnelle, arrêt n° 77/2026 du 18 juin 2026 (Preliminary ruling referred by the Cour de cassation; Viagogo GmbH among the parties), which reproduces the provision; arts. 6 to 9 cross-checked against two independent Justel mirrors (refli.be/fr/lex/2013011413, lisloi.be). ejustice.just.fgov.be served 'Please enable JavaScript to view the page content. Your support ID: 7840658572199194826' and economie.fgov.be the same wall ('support ID: 3644462778939547703'), so the Justel consolidated text was not read directly. The level-2 fine amount under art. XV.70 CDE was not read; max is null rather than guessed. Held constitutional on 18 June 2026 against arts. 38 and 127 §1, 1° (communities' cultural competence).","confidence":"A","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "PT": [
      {"jurisdiction":"PT","instrument_kind":"primary_legislation","citation":"Decreto-Lei n.º 28/84, de 20 de janeiro (Regime das Infrações Antieconómicas e Contra a Saúde Pública), artigo 35.º (crime de especulação) — IDENTIFIED, NOT READ","url":"https://diariodarepublica.pt/dr/detalhe/decreto-lei/28-1984-661659","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"all_resale","cap_basis":"face","cap_value":null,"penalty":{"kind":"criminal","summary":"Reported: crime de especulação, prison of six months to three years and a fine of not less than 100 days; in the negligent form, prison up to one year or a fine of not less than 40 days. NOT VERIFIED against the article.","max":"prisão 6 meses a 3 anos, multa não inferior a 100 dias (reported)"},"enforcement_body":"criminal courts and the Ministério Público (reported); no IGAC role for resale was verified","quoted_provision":"","notes":"CONFIDENCE D: the article itself was NOT read, so there is no quote and every element above is reported, not verified. Two sources concordant on the instrument and the penalty bands: DECO PROteste, 18 May 2026 ('crime de especulação, previsto e punido no artigo 35.º do Decreto-Lei n.º 28/84 ... pena de prisão entre seis meses e três anos, e multa não inferior a 100 dias'; resale lawful only if the seller makes no gain) and Diário de Viseu, 13 July 2026 (same instrument, same bands, 'o que a lei pune não é o ato de revender, mas sim de lucrar com essa revenda'). A Tribunal da Relação de Lisboa judgment of 26 January 2023 (proc. 1031/22.5SILSB.L1-9) confirms art. 35.º n.º 1 al. b) DL 28/84 is the especulação offence, but on a taxi fare and without transcribing the article. ROUTES THAT FAILED, verbatim: diariodarepublica.pt returns a 2,346-byte OutSystems shell ('window.OutSystemsApp = { basePath: '/dr/' }'), zero occurrences of 'especula'; files.dre.pt and files.diariodarepublica.pt PDFs 301 into 'https://diariodarepublica.pt/dr/error'; pgdlisboa.pt connection reset (000) on six attempts across http/https, www and bare host; dre.tretas.org, dgsl.pt and consumidor.gov.pt '403 Just a moment...'; portal.oa.pt PDF downloaded but subset-encoded fonts make the extracted text glyph gibberish. LEAD REFUTED: Decreto-Lei n.º 23/2015 (named in the brief) is 'O regime de incentivos do Estado à comunicação social, atualmente previsto no Decreto-Lei n.º 7/2005' per its Diário da República catalogue entry — media incentives, no ticket provision; the instrument was not read, so this refutation rests on the official catalogue entry. No adopted 2024-2026 resale instrument was found; what exists is a DECO PROteste revision proposal of July 2026. cap_basis 'face' is reported, not verified.","confidence":"D","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "DE": [
      {"jurisdiction":"DE","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "NL": [
      {"jurisdiction":"NL","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "PL": [
      {"jurisdiction":"PL","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "SE": [
      {"jurisdiction":"SE","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "DK": [
      {"jurisdiction":"DK","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "AT": [
      {"jurisdiction":"AT","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "CZ": [
      {"jurisdiction":"CZ","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ],
    "HU": [
      {"jurisdiction":"HU","instrument_kind":"none_identified","citation":"","url":"","status":"unknown","in_force_from":null,"in_force_to":null,"applies_to":"unknown","cap_basis":"unknown","cap_value":null,"penalty":{"kind":"unknown","summary":"Not researched in this pass.","max":null},"enforcement_body":"unknown","quoted_provision":"","notes":"not researched in this pass","confidence":"E","retrieved_at":"2026-11-08T06:23:26Z"}
    ]
  }
}
```
