# FedRAMP Link Queue — Decision-Quality Review

**Date:** 2026-05-03
**Scope:** read-only audit of `fedramp_link_queue` past decisions in `data/federal_ai_inventory_2025.db`
**Snapshot:** queue built 2026-05-02 (all 199 rows created in a single ETL window between 14:47 and 16:23 UTC). No edits since.

## Executive summary

The queue contains 192 product rows (and 7 agency rows, out of scope for this review). All 192 product decisions live entirely in the `decision_notes` column — **`llm_proposed_fedramp_ids` and `llm_reasoning` are empty for every row** (0/192 populated). The decision text is human-grade prose; many rows reference upstream ETL files (`decided_ms.csv`, "Adj-GG accept_N") suggesting decisions were applied in batch.

`fedramp_product_links` is empty (0 rows): **none of the resolved decisions have actually been written to the canonical link table yet.** This audit therefore evaluates the *intent* recorded in `decision_notes`; nothing has been committed downstream.

Headline findings:

1. **Resolved/no_alias (71 rows):** Largely defensible. Most resolutions document "inherits via parent boundary" (Microsoft 365 GCC, Azure Government, AWS GovCloud, Google Workspace, GCP, Palantir Federal Cloud). The reasoning is consistent with FedRAMP inheritance practice. Two rows showed self-contradictory text resolved late (#27 Adobe Firefly), but landed on the right answer.
2. **Resolved/multi_candidate (13 rows):** Picks are plausible. A few rows defaulted to **Moderate** when a **High** SKU was also available for the same vendor (Zscaler ZIA-Government, Palo Alto, Citrix, Microsoft 365 GCC, Palantir PFCS). This is "lowest-impact-default" — not wrong per se, but worth tagging because agencies operating at High would need the High SKU.
3. **Rejected/no_alias (108 rows):** Mostly correct (open-source code, hardware, agency-bespoke, consumer features). **At least 2 likely-wrong rejections**: Altana (FedRAMP Authorized exists, vendor name is exact match), Exiger DDIQ (Exiger Federal Cloud is FedRAMP Authorized — DDIQ likely runs on it). 4 more uncertain (LIGER/LMI Atlas, OPEXUS FOIAXpress, Coleridge ADRF, Wolters Kluwer TeamMate).
4. **Coverage gap (50 products never queued):** Significantly larger than the 43 mentioned in the prompt. Of those 50, **at least 30 have clear FedRAMP authorizations** (ChatGPT, Gemini, Grok, Salesforce Einstein, Slack, Zoom, ServiceNow Now Assist, Crowdstrike Falcon, Wiz, Cohesity, Relativity, Tableau, Asana, Ask Sage, Chainalysis, Cohesity, Crowdstrike, DocketScope, Dynatrace, Google Workspace, Google Cloud Platform, ID.me, Illumio, Informatica, Lookout, Motorola, Perplexity, SAP Concur, SentinelOne, Sprinklr, Veritone, ...). All 50 have `product_origin='commercial'`. None are agency-internal. **The queue was built once on 2026-05-02; products added after that ETL run were not picked up.**

## Decision-quality scorecard

| Category | Total | Reviewed | Likely-correct | Likely-wrong | Uncertain |
|---|---|---|---|---|---|
| Resolved / no_alias (parent inheritance) | 71 | 71 | 69 | 0 | 2 |
| Resolved / multi_candidate | 13 | 13 | 8 | 0 | 5 (Moderate-default when High existed) |
| Rejected / no_alias | 108 | 108 (vendor scan) | 102 | 2 | 4 |
| Products never queued (coverage gap) | 50 | 50 | n/a | n/a | 30+ have FedRAMP listings that were skipped |

"Reviewed" = inspected against `fedramp_products`. The rejected category was scanned via vendor LIKE-match across all 108 rows, not just spot-checked.

## Likely-wrong rejections

These rejections claim "no FedRAMP authorization" but a marketplace entry exists for the same vendor with a plausibly matching product line.

| Queue id | Product | Vendor | FedRAMP entry that exists | Why rejection looks wrong |
|---|---|---|---|---|
| 50 | Altana Atlas | Altana | `FR2413241182` Altana / **Altana Product Network** (Authorized, **High**) | Vendor name is exact match. "Altana Product Network" is Altana's flagship platform; "Altana Atlas" is the Altana product. Almost certainly the same authorization boundary. |
| 135 | Exiger DDIQ | Exiger | `FR2122140784` Covergent Solutions Inc dba Exiger Government Solutions (EGS) / **Exiger Federal Cloud (EFC)** (Authorized, Moderate) | Exiger has a federal cloud authorization. DDIQ is Exiger's flagship due-diligence platform; very likely runs on EFC. Rejection note is "no FedRAMP authorization" but EFC clearly exists. |

## Uncertain rejections (worth a second look)

| Queue id | Product | Vendor | Possible FedRAMP entry | Notes |
|---|---|---|---|---|
| 37 | LIGER Generative AI Toolkit | LMI Consulting, LLC | `FR2524251176` LMI Solutions / Atlas by LMI (In Process, Moderate) | Different LMI entity ("LMI Solutions" vs "LMI Consulting") and different product name, but LMI's federal cloud could host LIGER. Rejection as "in-house/agency-built" may understate the commercial offering. |
| 182 | FOIAXpress AI | OPEXUS | `AGENCYHUDSAAS` AINS dba OPEXUS - eCase (Authorized, Moderate) | OPEXUS has a FedRAMP-authorized eCase product. FOIAXpress is OPEXUS's separate FOIA workflow product; whether it shares the eCase boundary needs vendor confirmation. Current rejection note is reasonable on its face. |
| 187 | Democratizing Data | Coleridge Institute | `FR1819057982` The Coleridge Initiative, Inc. / Administrative Data Research Facility (ADRF) (Authorized, Moderate) | Vendor matches exactly. "Democratizing Data" may be a Coleridge program that runs on ADRF infrastructure. Rejected as "in-house / agency program" but the vendor has a FedRAMP boundary. |
| 153 | UpToDate | Wolters Kluwer | `FR2207643307` Wolters Kluwer / TeamMate FedRAMP (Authorized, Moderate) | TeamMate is Wolters Kluwer's audit product — different product line from UpToDate (clinical reference). Rejection is plausible but the vendor does have a FedRAMP presence; an UpToDate-specific listing should be re-checked. |

## Likely-wrong resolutions

None of the 84 resolved rows pick a clearly-wrong fedramp_id. Two rows have minor concerns:

| Queue id | Product | Concern |
|---|---|---|
| 27 | Adobe Firefly | `decision_notes` contains two contradictory statements separated by `\|`: first "Firefly out of scope," then "covered as a component of Adobe Creative Cloud for Enterprise (Li-SaaS)." The later resolution (Adobe CC for Enterprise) is correct, but the audit trail looks confused. Consider cleaning the field. |
| 174 | H2O GPTe | `decision_notes` says "H2O.AI is FedRAMP Authorized (High)" — the underlying entry exists but is filed as `csp='H20.AI for Government'` (note typo: H**2-zero**.AI). The mapping is correct; the queue text just doesn't capture the exact CSP slug oddity. |

## Multi-candidate decisions audited (all 13)

For each: source_text → chosen CSO. Flags marked when a higher-impact SKU from the same vendor was passed over.

| id | source_text | chosen | impact | also-available | flag |
|---|---|---|---|---|---|
| 21 | Splunk | Splunk Cloud Platform for FedRAMP **High** | High | Splunk Cloud Moderate, Observability Moderate | OK — explicitly chose High |
| 22 | Zscaler | ZIA-Government (SWG-vTIC) | Moderate | **ZIA-Gov High** also existed | "Lowest-impact default"; agency context unknown |
| 23 | Palo Alto Networks | Palo Alto Networks Government Cloud Services | Moderate | **GCS-HIGH** also existed | "Lowest-impact default" |
| 24 | Databricks | Databricks on AWS GovCloud | High | AWS US East/West, Azure Commercial | OK — chose GovCloud over commercial |
| 26 | Esri ArcGIS AI | ArcGIS Online (AGO) | Moderate | Esri Managed Cloud Advanced Plus | OK — AGO is the SaaS users mean |
| 52 | Palantir Federal Cloud Service | PFCS – **Moderate** | Moderate | **PFCS-High** also existed; PFCS-SS also existed | Source text is the exact name "Palantir Federal Cloud Service" — defaulting to Moderate when both High and Moderate share that name is the lowest-impact-default pattern. Worth a second look. |
| 55 | Medallia | Medallia GovCloud | Moderate | Mindful by Medallia | OK — GovCloud is the federal SKU |
| 62 | Okta Adaptive MFA | Okta IDaaS Government High Cloud (GHC) | High | Okta IDaaS Regulated Cloud | OK — chose High |
| 95 | Microsoft 365 | M365 GCC (Moderate) | Moderate | **M365 GCC-High** also existed; Exostar also matched | OK — GCC is the most common; GCC-High is for ITAR/CUI which the inventory text didn't specify |
| 98 | LexisNexis | Lexis+ for Government (Legal) | Moderate | LexisNexis Risk Enterprise Platform | Source text is just "LexisNexis" — could be either Legal or Risk; Legal is the more common Lexis+ branding. Reasonable but ambiguous. |
| 122 | Tenable | Tenable Government Solutions | Moderate | Tenable Cloud Security for US Gov | OK — generic Tenable mention → flagship gov authorization |
| 161 | Citrix | Citrix for Government (Moderate) | Moderate | **Citrix for Government - High** also existed | "Lowest-impact default" |
| 162 | Kiteworks | Kiteworks Secure Gov Cloud | Moderate | Kiteworks Federal Cloud | OK — Secure Gov Cloud is the newer SKU |

**Pattern to note:** when an inventory mention is generic ("Splunk", "Zscaler", "Palo Alto", "Citrix", "Microsoft 365") and the same vendor has both Moderate and High federal SKUs, the resolver picked Moderate 5 times and High 1 time (Splunk, with explicit "Splunk Cloud High is the right SKU" note). The Moderate default may understate the actual deployment when the agency is operating at High; this is a downstream interpretation question rather than a wrong link.

## Products never queued

50 products are in `products` but have no row in `fedramp_link_queue` (link_kind='product'). All 50 are `product_origin='commercial'` — none are agency-internal platforms. The queue was built in a single batch on 2026-05-02; these products were almost certainly added to `products` after that ETL run.

### Breakdown by likely status (manual classification from vendor knowledge + fedramp_products lookup)

**Has a clear FedRAMP authorization (must be queued and resolved):** ~30
- ChatGPT / OpenAI API → `FR2533155773` OpenAI / ChatGPT Enterprise and API Platform (Authorized, Moderate)
- Gemini → `FR2604952026` Google / Gemini for Government (Authorized, Low)
- Grok → `FR2618542150` xAI / Grok for Government (In Process, High)
- Perplexity → `FR2604643715` Perplexity AI / Perplexity Enterprise and API Platform (Authorized, Low)
- Salesforce Einstein → maps to `FR2003061248` Salesforce Government Cloud Plus (High)
- Slack → `FR2230252267` GovSlack (High) or `FR1823447014` Slack (Moderate)
- Zoom → `FR1825941347A` Zoom for Government (Moderate)
- ServiceNow Now Assist → `F1305072116` ServiceNow Government Community Cloud (High)
- Crowdstrike Falcon → `FR1807853629A` CrowdStrike Falcon Platform for Government (High)
- Wiz → `FR2308034636A` Wiz for U.S. Government (High)
- Cohesity → `FR2306445868` Cohesity Cloud Services for Government (Moderate)
- Relativity → `FR2004753002` RelativityOne Government (Moderate)
- Tableau → maps to Salesforce Government Cloud
- Asana → `FR2527132001` Asana (In Process, Moderate)
- Ask Sage → `FR2401839361` Ask Sage (Authorized, High)
- Chainalysis → `FR2334756650` Chainalysis Reactor (Moderate)
- DocketScope → `FR2419537309` DocketScope (Moderate)
- Dynatrace → `FR2016131254` Dynatrace Platform (Moderate)
- Google Workspace → `F1206081364` Google Workspace (High)
- Google Cloud Platform → `FR1805751477` Google Services / GCP (High)
- ID.me → `FR1718334757` ID.me Identity Gateway (Moderate)
- Illumio → `FR2230244107` Illumio Government Cloud (Moderate)
- Informatica → `FR2029331613` IICS (Moderate)
- Lookout → `F1603297883` Lookout Security Platform (Moderate)
- Motorola License Plate Recognition → `FR2118055930` Motorola Solutions Federal Cloud (High)
- SAP Concur → `FR2234550858` Concur Cloud for Public Sector (Moderate)
- SentinelOne → `FR1919071020A` SentinelOne Singularity Platform High (High)
- Sprinklr → `FR2035740126` Sprinklr CXM for Government (Li-SaaS)
- Veritone → `FR1804557312` Veritone iDEMS for Government (Moderate)
- Microsoft 365 Copilot Chat → inherits via M365 GCC (parent inheritance pattern)
- Microsoft Purview → inherits via M365 GCC

**Apple/Google consumer features (likely correctly reject as out-of-scope):** 5
- Apple Face ID, Apple Maps, Google Lens, Google Maps, Google Pixel

**Unlikely to have FedRAMP / open-source / niche / hardware:** ~15
- Cursor (Anysphere) — no listing
- DALL-E (OpenAI) — likely covered by ChatGPT Enterprise & API authorization
- NotebookLM (Google) — would inherit via Google Workspace
- BioRender — no listing
- Canva — no listing
- Magnet Forensics — no listing
- monday.com — no listing
- Sprout Social — no listing
- Synthesia — no listing
- Poolside — no listing
- FS Pro — no listing
- LexisNexis Risk Solutions (already covered by Risk Enterprise Platform) — would resolve to existing entry
- Alteryx — no listing
- Salesforce Einstein → see above (ride Salesforce Gov Cloud)

**Already in queue under different name:** check for collisions
- "LexisNexis Risk Solutions" (id 3095) is a separate product from "LexisNexis" alias seen in queue id 98. Likely should resolve to `FR2611036548`.

## Recommendations

1. **Re-run the queue-builder against the current `products` table.** 50 commercial products are missing from `fedramp_link_queue`. At least 30 of them have unambiguous FedRAMP marketplace entries. Without re-running, those products will never be linked.
2. **Promote resolved decisions into `fedramp_product_links`.** All 84 resolved rows describe an intent but `fedramp_product_links` is empty. The "decision" only matters once it's a row downstream — currently the queue is a notebook, not a source of truth.
3. **Re-examine the 2 likely-wrong rejections** (Altana, Exiger DDIQ) and the 4 uncertain ones (LIGER, FOIAXpress, Democratizing Data, UpToDate). These are vendor-name exact matches against the marketplace — easy to verify with one round of vendor research each.
4. **Capture impact-level intent on multi-candidate Moderate-default picks** (Zscaler, Palo Alto, Citrix, M365 GCC, PFCS). If an agency is documented at High, the link should resolve to the High SKU. Today, 5/13 multi-candidate decisions defaulted to Moderate when High existed for the same vendor.
5. **Clean up the conflicting `decision_notes` on Adobe Firefly (queue id 27).** The field reads as a debate rather than a decision; later cleanup should keep only the final answer.
6. **Add structured fields.** The fact that `llm_proposed_fedramp_ids` and `llm_reasoning` are 0/192 populated, and that `decision_notes` carries free text including parsed prefixes like "Multi-candidate (Adj-GG accept_2):" suggests decisions came from upstream CSVs (`decided_ms.csv`, Adj-GG files in `audit/`). Consider parsing those into `llm_proposed_fedramp_ids` so downstream link-promotion can be automated.
7. **Treat "inherits from parent boundary" as a first-class link kind.** 50+ rows in resolved/no_alias resolve to "rides on M365 GCC / Azure Gov / AWS GovCloud / GCP / Google Workspace / Palantir Federal Cloud." These aren't direct fedramp_id links but they're substantively the right answer. The schema should distinguish "direct authorization" from "inherited via parent boundary" so the dashboard can render that nuance honestly. Without it, all the Microsoft/Google/AWS sub-products will look unlinked.

## Appendix: query reproduction

```sql
-- Resolved / no_alias (71 rows)
SELECT q.id, q.source_text, p.vendor, q.decision_notes
FROM fedramp_link_queue q
JOIN products p ON p.canonical_name = q.source_text
WHERE q.link_kind='product' AND q.status='resolved' AND q.reason='no_alias';

-- Resolved / multi_candidate (13 rows)
SELECT q.id, q.source_text, q.candidate_fedramp_ids, q.decision_notes
FROM fedramp_link_queue q
WHERE q.link_kind='product' AND q.status='resolved' AND q.reason='multi_candidate';

-- Rejected / no_alias (108 rows)
SELECT q.id, q.source_text, p.vendor, q.decision_notes
FROM fedramp_link_queue q
JOIN products p ON p.canonical_name = q.source_text
WHERE q.link_kind='product' AND q.status='rejected' AND q.reason='no_alias';

-- Products never queued (50 rows)
SELECT p.id, p.canonical_name, p.vendor, p.product_origin
FROM products p
WHERE p.canonical_name NOT IN (
  SELECT source_text FROM fedramp_link_queue WHERE link_kind='product'
);
```

## Caveats

- This audit treats `source_text` as the authoritative join key from queue → products (because `inventory_id` values 85–305 do **not** match current `products.id` values 2836–3204; the inventory_id column appears to be a stale ordinal from a prior ETL run). All 192 product rows joined cleanly on `source_text → canonical_name`.
- Vendor LIKE-matching has false negatives. A vendor that renamed itself or that operates under a parent CSP (e.g., "H20.AI for Government" vs "H2O.ai") will be missed by simple substring search. Two such cases (H2O, "Covergent Solutions dba Exiger") were caught here, but others may exist.
- "Likely-wrong" / "uncertain" labels reflect what's visible in `fedramp_products` only. Some require vendor confirmation (does Exiger DDIQ actually ride on EFC? does FOIAXpress share OPEXUS eCase's boundary?). The audit does not assert it knows the answer; it flags rows where the queue's "no FedRAMP" claim is contradicted by a present marketplace entry.
