/**
 * The region rules table, as this demo reads it.
 *
 * GENERATED from `ticketpath/core/region_caps.py` by calling `resolve()` and
 * `effective_ceiling()` on 2026-11-08 for each jurisdiction below, at a 1 SOL face and
 * a 2500 bps platform cap. Table version and sha256 are the ones the resolver returned,
 * so a reader can check these rows against `ticketpath/data/region-caps.json` directly.
 * Nothing here is hand-written and nothing here is a legal opinion.
 */
export type RegionRow = {
  jurisdiction: string;
  resalePolicy: "capped" | "monitored" | "unresolved";
  resaleCapBps: number | null;
  lawReason: string;
  bindingJurisdiction: string | null;
  ceilingLamports: number;
  bindingRule: string;
  enforcedCapBps: number;
  instrumentKind: string | null;
  citation: string | null;
  confidence: string | null;
  lawTableVersion: string;
  lawTableSha256: string;
  tableStatus: string;
};

export const LAW_TABLE_VERSION = '2026-11-08.1';
export const LAW_TABLE_SHA256 = '4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106';
export const LAW_AS_OF = "2026-11-08";

export const REGIONS: RegionRow[] = 
[
  {
    "jurisdiction": "GB",
    "resalePolicy": "monitored",
    "resaleCapBps": null,
    "lawReason": "no_cap_in_force",
    "bindingJurisdiction": "GB",
    "ceilingLamports": 1250000000,
    "bindingRule": "platform",
    "enforcedCapBps": 2500,
    "instrumentKind": "primary_legislation",
    "citation": "Consumer Rights Act 2015 (c. 15), ss. 90-95 (secondary ticketing); as amended by Digital Economy Act 2017 (c. 30) s. 105 and Digital Markets, Competition and Consumers Act 2024 (c. 13) s. 216",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "GB primary_legislation in_force, GB announced_policy announced"
  },
  {
    "jurisdiction": "IE",
    "resalePolicy": "unresolved",
    "resaleCapBps": null,
    "lawReason": "designation_not_stated",
    "bindingJurisdiction": null,
    "ceilingLamports": 1250000000,
    "bindingRule": "platform",
    "enforcedCapBps": 2500,
    "instrumentKind": "primary_legislation",
    "citation": "Sale of Tickets (Cultural, Entertainment, Recreational and Sporting Events) Act 2021 (No. 21 of 2021), s. 15; commenced by S.I. No. 398/2021",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "IE primary_legislation in_force"
  },
  {
    "jurisdiction": "CA-ON",
    "resalePolicy": "capped",
    "resaleCapBps": 0,
    "lawReason": "law_caps_bps",
    "bindingJurisdiction": "CA-ON",
    "ceilingLamports": 1000000000,
    "bindingRule": "law",
    "enforcedCapBps": 0,
    "instrumentKind": "primary_legislation",
    "citation": "Ticket Sales Act, 2017, S.O. 2017, c. 33, Sched. 3, s. 2(3), as enacted by Plan to Protect Ontario Act (Budget Measures), 2026, S.O. 2026, c. 2, Sched. 16, s. 4(2)",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "CA-ON primary_legislation in_force"
  },
  {
    "jurisdiction": "US",
    "resalePolicy": "monitored",
    "resaleCapBps": null,
    "lawReason": "other_restriction_only",
    "bindingJurisdiction": null,
    "ceilingLamports": 1250000000,
    "bindingRule": "platform",
    "enforcedCapBps": 2500,
    "instrumentKind": "primary_legislation",
    "citation": "Better Online Ticket Sales Act of 2016, Public Law 114-274, 15 U.S.C. section 45c",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "US primary_legislation in_force, US secondary_legislation in_force"
  },
  {
    "jurisdiction": "US-NY",
    "resalePolicy": "unresolved",
    "resaleCapBps": null,
    "lawReason": "law_status_unknown",
    "bindingJurisdiction": null,
    "ceilingLamports": 1250000000,
    "bindingRule": "platform",
    "enforcedCapBps": 2500,
    "instrumentKind": "primary_legislation",
    "citation": "New York Arts and Cultural Affairs Law, s. 25.29 (unlawful charges in connection with tickets), with s. 25.35 (penalties); NB repealed 2027-07-01",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "US-NY primary_legislation in_force"
  },
  {
    "jurisdiction": "AU",
    "resalePolicy": "monitored",
    "resaleCapBps": null,
    "lawReason": "other_restriction_only",
    "bindingJurisdiction": null,
    "ceilingLamports": 1250000000,
    "bindingRule": "platform",
    "enforcedCapBps": 2500,
    "instrumentKind": "secondary_legislation",
    "citation": "Competition and Consumer (Australian Consumer Law - Electronic Ticket Resale Service) Information Standard 2022 (Cth), F2022L00475, made under the Australian Consumer Law (Competition and Consumer Act 2010) s. 134(1)",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "AU secondary_legislation in_force"
  },
  {
    "jurisdiction": "FR",
    "resalePolicy": "monitored",
    "resaleCapBps": null,
    "lawReason": "no_cap_in_force",
    "bindingJurisdiction": "FR",
    "ceilingLamports": 1250000000,
    "bindingRule": "platform",
    "enforcedCapBps": 2500,
    "instrumentKind": "primary_legislation",
    "citation": "Code penal art. 313-6-2, as amended by loi n 2012-158; read in the Journal officiel",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "FR primary_legislation in_force"
  },
  {
    "jurisdiction": "CA-QC",
    "resalePolicy": "capped",
    "resaleCapBps": 0,
    "lawReason": "law_caps_bps",
    "bindingJurisdiction": "CA-QC",
    "ceilingLamports": 1000000000,
    "bindingRule": "law",
    "enforcedCapBps": 0,
    "instrumentKind": "primary_legislation",
    "citation": "Consumer Protection Act, CQLR c. P-40.1, ss. 236.0.1 and 236.1-236.6",
    "confidence": "A",
    "lawTableVersion": "2026-11-08.1",
    "lawTableSha256": "4748d2d1f2f05e320dfefa2215ed1e9ec0df1b0d5e1367c4383b6bc113f41106",
    "tableStatus": "CA-QC primary_legislation in_force"
  }
];
