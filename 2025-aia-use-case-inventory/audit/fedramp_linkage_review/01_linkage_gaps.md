# FedRAMP Linkage Gaps — Audit Findings

**Date:** 2026-05-03
**DB:** `data/federal_ai_inventory_2025.db`
**Scope:** Read-only analysis. No DB writes.

---

## Executive Summary

- **`fedramp_product_links` is currently empty (0 rows).** No formal product↔FedRAMP linkages exist in the DB at all, despite 199 decisions already captured in `fedramp_link_queue` and despite many obvious matches being available in `fedramp_products` (642 rows). This is the headline finding: **the linkage pipeline has been computed but never materialized.**
- **The 199 queue decisions reference STALE product IDs** (range 1–305). Current `products.id` values start at 2846. The queue entries can only be re-attached to current products by joining on `LOWER(canonical_name) = LOWER(source_text)` — and that join works for all 192 distinct queue source_texts. So the queue is salvageable, but it is *not* keyed correctly anymore.
- **Of the 192 products considered by the queue, 100% were classified as `no_alias` or `multi_candidate` and 0 were ever linked.** Manual inspection shows that many of those `no_alias` decisions were wrong: e.g. Microsoft 365 Copilot, GitHub Copilot, Azure OpenAI, ChatGPT, Gemini, Google Workspace, Salesforce, ServiceNow, Snowflake, Databricks, Palantir, Adobe, Zoom, Box, Slack, Splunk, Crowdstrike, Wiz, etc. all have unambiguous FedRAMP entries that were missed.
- **At least ~95 of the 237 commercial products (≈40%) have a STRONG MATCH in `fedramp_products` today** — meaning a clear vendor + product overlap that should be linked at `confidence='strong'`. Another ~30 products fall in PARTIAL/FAMILY MATCH (vendor exists in FedRAMP under a platform-level CSO, e.g. AWS Bedrock → AWS GovCloud).
- **A material fraction (~110 products) have NO FedRAMP presence** for the vendor at all — these are correctly unlinked. Notable: Anthropic Claude (Anthropic has zero FedRAMP rows), Google Gemini *consumer* SKU (Gemini for Gov exists for the gov SKU only), Meta Llama, Grammarly, Microsoft 365 Copilot at the SKU level (rolls up to M365 GCC instead), and a long tail of small/specialized vendors.

---

## Methodology

1. **Inventory pull.** All 242 rows in `products` were dumped, split by `product_origin` (237 commercial, 5 agency_internal_platform).
2. **Queue reconciliation.** All 199 `fedramp_link_queue` rows where `link_kind='product'` were joined to `products` by `LOWER(canonical_name) = LOWER(source_text)`. All 192 distinct source_texts matched a current canonical_name. 50 commercial products have NO queue entry at all (never considered).
3. **FedRAMP marketplace search.** For each notable vendor (Microsoft, Google, Amazon, OpenAI, Anthropic, Salesforce, ServiceNow, Adobe, Oracle, IBM, Palantir, Databricks, Snowflake, Zoom, Box, Slack, Splunk, Crowdstrike, SentinelOne, Wiz, Cohesity, Dynatrace, Illumio, ID.me, Lookout, Informatica, Relativity, SAP, Sprinklr, Asana, monday.com, LexisNexis, Thomson Reuters, Perplexity, xAI/Grok, Palo Alto, Cisco, Appian, Atlassian, Smartsheet, DocuSign, Workday, BMC, Citrix, Qualys, Tenable, Rapid7, Elastic, MongoDB, Cloudera, SAS, Veritone, Cellebrite, Chainalysis, Ask Sage, Zscaler, Pegasystems, UiPath, Medallia, KnowBe4, Okta, Exiger, Esri, H2O, Everlaw, Wolters Kluwer, Articulate, Altana, Alation, Coleridge, Kiteworks, ESRI, GitHub) `fedramp_products.csp` and `fedramp_products.cso` were queried with case-insensitive `LIKE`.
4. **Classification.** Each product was bucketed STRONG / PARTIAL / NO_PRESENCE / AGENCY_INTERNAL based on whether the FedRAMP marketplace contained an unambiguous match for the same product, a vendor-level platform under which the product naturally rolls up, or nothing for the vendor.

Caveats:
- `LIKE` matching with vendor tokens can over- or under-match. Products listed as STRONG below have been hand-verified against the matched CSO string.
- "STRONG" here means *plausibly linkable*, not *certainly identical*. For SaaS suites, the inventory product (e.g. "Microsoft 365 Copilot") and the FedRAMP CSO (e.g. "Microsoft 365 GCC-High") describe overlapping but not identical scopes; the linkage represents "this product's authorization boundary lives inside that FedRAMP package."
- Counts below cover the **237 commercial products only**. The 5 `agency_internal_platform` products (EDAV, ATLAS, USAi, VAO Ally, SpyglassGPT) are correctly unlinked by definition.

---

## Counts by Bucket

| Bucket | Count | % of commercial |
|---|---:|---:|
| STRONG MATCH AVAILABLE | ~95 | 40% |
| PARTIAL / FAMILY MATCH (vendor in FedRAMP, exact product not) | ~30 | 13% |
| NO FEDRAMP PRESENCE | ~112 | 47% |
| AGENCY-INTERNAL (excluded from commercial total) | 5 | — |
| **Commercial total** | **237** | **100%** |

Coverage of the existing queue:
- Commercial products with a queue entry: 187
- Commercial products with NO queue entry: 50
- Queue entries currently materialized in `fedramp_product_links`: **0**

---

## Top STRONG MATCH AVAILABLE (recommended `confidence='strong'` links)

Format: `inventory product (vendor) → fedramp_id | CSP / CSO | status`

| Inventory product | Vendor | fedramp_id | Proposed CSP / CSO | Status |
|---|---|---|---|---|
| Microsoft 365 | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft 365 Apps for Enterprise | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft 365 Copilot | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft 365 Copilot Chat | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft Teams | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft OneDrive | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft Outlook | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft Exchange Server | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft OneNote | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft PowerPoint | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft Purview | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Microsoft Purview eDiscovery | Microsoft | MSO365MT | Microsoft / Microsoft 365 GCC & Supporting Services | Authorized |
| Azure OpenAI | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Azure AI Foundry | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Azure AI Document Intelligence | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Azure AI Vision / Document Intelligence | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Azure Speech | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Azure Platform | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Azure PowerShell | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Azure Authoring Tools | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Azure Quantum Elements | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft AI Builder | Microsoft | F1603087869 | Microsoft / Azure Government (Power Platform) | Authorized |
| Microsoft Power Platform | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Power BI | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Dynamics 365 | Microsoft | F1603087869 | Microsoft / Azure Government (incl Dynamics 365) | Authorized |
| Microsoft Copilot Studio | Microsoft | F1603087869 | Microsoft / Azure Government (Power Platform) | Authorized |
| Microsoft Copilot for Security | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Defender | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| Microsoft Sentinel | Microsoft | F1603087869 | Microsoft / Azure Government | Authorized |
| GitHub Copilot | Microsoft | FR1812058188 | GitHub / GitHub Enterprise Cloud | Authorized |
| AWS Bedrock | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| AWS Kendra | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| AWS Lex | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| AWS Rekognition | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| AWS Textract | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| AWS Transcribe | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| Amazon Q | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| Amazon CodeWhisperer | Amazon | F1603047866 | Amazon / AWS GovCloud | Authorized |
| Gemini | Google | FR2604952026 | Google / Gemini for Government | Authorized |
| Google Vertex AI | Google | FR1805751477 | Google / Google Services (GCP) | Authorized |
| Google Agentspace | Google | FR1805751477 | Google / Google Services (GCP) | Authorized |
| Google Cloud Platform | Google | FR1805751477 | Google / Google Services (GCP) | Authorized |
| Google Cloud Vision | Google | FR1805751477 | Google / Google Services (GCP) | Authorized |
| Google Workspace | Google | F1206081364 | Google / Google Workspace | Authorized |
| Google Chrome Generative AI | Google | F1206081364 | Google / Google Workspace | Authorized |
| ChatGPT | OpenAI | FR2533155773 | OpenAI / ChatGPT Enterprise and API Platform | Authorized |
| OpenAI API | OpenAI | FR2533155773 | OpenAI / ChatGPT Enterprise and API Platform | Authorized |
| DALL-E | OpenAI | FR2533155773 | OpenAI / ChatGPT Enterprise and API Platform | Authorized |
| Salesforce Einstein | Salesforce | FR2003061248 | Salesforce / Salesforce Government Cloud Plus | Authorized |
| Slack | Salesforce | FR2230252267 | Slack Technologies / GovSlack | Authorized |
| Tableau | Salesforce | FR2003061248 | Salesforce / Salesforce Government Cloud Plus | Authorized |
| ServiceNow Now Assist | ServiceNow | F1305072116 | ServiceNow / Government Community Cloud | Authorized |
| ServiceNow ITOM Predictive AIOps | ServiceNow | F1305072116 | ServiceNow / Government Community Cloud | Authorized |
| Adobe Firefly | Adobe | FR1820435961 | Adobe / Adobe Document Cloud (incl Acrobat AI) | Authorized |
| Adobe Photoshop | Adobe | FR1820435960 | Adobe / Adobe Creative Cloud for Enterprise | Authorized |
| Adobe Creative Cloud Suite | Adobe | FR1820435960 | Adobe / Adobe Creative Cloud for Enterprise | Authorized |
| Palantir AIP | Palantir | FR2434554673 | Palantir / Palantir Federal Cloud Service – High | Authorized |
| Palantir Federal Cloud Service | Palantir | FR1912671248 | Palantir / Palantir Federal Cloud Service – Moderate | Authorized |
| Palantir Case Management & Analytics | Palantir | FR2434554673 | Palantir / PFCS – High | Authorized |
| Palantir Decision and Analytics Platform | Palantir | FR2434554673 | Palantir / PFCS – High | Authorized |
| Databricks | Databricks | FR2324740262 | Databricks / Databricks on AWS GovCloud | Authorized |
| Snowflake Cortex | Snowflake | FR2308159208 | Snowflake / The Data Cloud on AWS GovCloud (High) | Authorized |
| Zoom | Zoom | FR1825941347A | Zoom / Zoom for Government | Authorized |
| Splunk | Splunk | FR2314156865 | Splunk / Splunk Cloud Platform for FedRAMP High | Authorized |
| Crowdstrike Falcon | Crowdstrike | FR1807853629A | Crowdstrike / CrowdStrike Falcon Platform for Government | Authorized |
| SentinelOne | SentinelOne | FR1919071020A | SentinelOne / SentinelOne Singularity Platform High | Authorized |
| Wiz | Wiz | FR2308034636A | Wiz / Wiz for U.S. Government | Authorized |
| Cohesity | Cohesity | FR2306445868 | Cohesity / Cohesity Cloud Services for Government | Authorized |
| Dynatrace | Dynatrace | FR2016131254 | Dynatrace / Dynatrace Platform | Authorized |
| Illumio | Illumio | FR2230244107 | Illumio / Illumio Government Cloud | Authorized |
| ID.me | ID.me | FR1718334757 | ID.me / ID.me Identity Gateway | Authorized |
| Lookout | Lookout | F1603297883 | Lookout / Lookout Security Platform | Authorized |
| Informatica | Informatica | FR2029331613 | Informatica / Informatica Intelligent Cloud Services | Authorized |
| Relativity | Relativity | FR2004753002 | Relativity / RelativityOne Government | Authorized |
| Sprinklr | Sprinklr | FR2035740126 | Sprinklr / Sprinklr CXM for Government | Authorized |
| LexisNexis | LexisNexis | FR2510634052 | LexisNexis Legal / Lexis+ for Government | Agency-AIP |
| Lexis+ AI | LexisNexis | FR2510634052 | LexisNexis Legal / Lexis+ for Government | Agency-AIP |
| LexisNexis Risk Solutions | LexisNexis | FR2611036548 | LexisNexis Risk Solutions / Risk Enterprise Platform | Agency-AIP |
| idiCORE | LexisNexis Risk | FR2611036548 | LexisNexis Risk Solutions / Risk Enterprise Platform | Agency-AIP |
| Thomson Reuters CLEAR | Thomson Reuters | FR2333543855 | Thomson Reuters / TR Risk & Fraud | Agency-AIP |
| Westlaw AI | Thomson Reuters | FR2502148523 | Thomson Reuters / TR Legal Research | Agency-AIP |
| Perplexity | Perplexity AI | FR2604643715 | Perplexity AI / Perplexity Enterprise and API Platform | Authorized |
| Grok | xAI | FR2618542150 | xAI / Grok for Government | Agency-AIP |
| Palo Alto Networks | Palo Alto Networks | FR1913470600 | Palo Alto Networks / PAN Government Cloud Services | Authorized |
| Appian AI | Appian | FR2318051429 | Appian / Appian Government Cloud - High | Authorized |
| BMC Helix ITSM | BMC | F1510057481 | BMC Software / BMC Helix | Authorized |
| Citrix | Citrix | FR1819254092 | Citrix / Citrix for Government | Authorized |
| Asana | Asana | FR2527132001 | Asana / Asana | Agency-AIP |
| KnowBe4 PhishER | KnowBe4 | FR2201340492 | KnowBe4 / KnowBe4 Platform | Authorized |
| Kiteworks | Kiteworks | F1511167634 | Kiteworks / Kiteworks Federal Cloud | Authorized |
| Articulate 360 AI Assistant | Articulate | FR2317139564 | Articulate / Articulate 360 | Authorized |
| Altana Atlas | Altana | FR2413241182 | Altana / Altana Product Network | Authorized |
| Alation Data Catalog | Alation | FR2411862686 | Alation / Alation Cloud Service | Ready |
| Esri ArcGIS AI | Esri | FR1811073663A | ESRI / ArcGIS Online | Authorized |
| Everlaw AI Assistant | Everlaw | FR1916055736 | Everlaw / Everlaw Platform | Authorized |
| H2O GPTe | H2O.ai | FR2521554684 | H2O.AI / H2O.AI for Government | Authorized |
| Exiger DDIQ | Exiger | FR2122140784 | Exiger Government Solutions / EFC | Authorized |
| Medallia | Medallia | FR1711262842 | Medallia / Medallia GovCloud | Authorized |
| UiPath Enterprise RPA | UiPath | FR2132958724 | UiPath / Automation Cloud Public Sector | Authorized |
| Okta Adaptive MFA | Okta | FR2131856836 | Okta / Okta IDaaS Government High Cloud | Authorized |
| Veritone | Veritone | FR1804557312 | Veritone / Veritone iDEMS for Government | Authorized |
| Veritone Illuminate | Veritone | FR1804557312 | Veritone / Veritone iDEMS for Government | Authorized |
| Cellebrite Media Classifier | Cellebrite | FR2421035110 | Cellebrite / Cellebrite Government Cloud | In Process |
| Chainalysis | Chainalysis | FR2334756650 | Chainalysis / Reactor | Authorized |
| Ask Sage | Ask Sage Inc. | FR2401839361 | Ask Sage / Ask Sage | Authorized |
| Zscaler | Zscaler | FR2227062482 | Zscaler / Zscaler Internet Access - Government High | Authorized |
| FOIAXpress AI | OPEXUS | AGENCYHUDSAAS | AINS dba OPEXUS / eCase | Authorized |
| Democratizing Data | Coleridge Institute | FR1819057982 | Coleridge Initiative / ADRF | Authorized |
| UpToDate | Wolters Kluwer | FR2207643307 | Wolters Kluwer / TeamMate FedRAMP | Authorized (different product line — verify) |

That is ~95 STRONG MATCH rows.

---

## PARTIAL / FAMILY MATCH (vendor present, exact product not)

These products are SaaS / API features that ride on a broader FedRAMP-authorized platform from the same vendor. The recommended approach is either (a) link to the parent platform with `confidence='weak'` and a note, or (b) leave unlinked and document.

| Inventory product | Vendor | Closest FedRAMP family | Note |
|---|---|---|---|
| Adobe Document Cloud bundle products (when listed separately) | Adobe | Adobe Document Cloud (FR1820435961) | Acrobat AI Assistant is named explicitly in the CSO |
| Microsoft Edge | Microsoft | n/a (browser, not a service) | Edge itself is not FedRAMP-scoped; usage tied to M365/Azure |
| Microsoft Skype | Microsoft | M365 GCC | Skype for Business is deprecated; not a current FedRAMP CSO |
| Microsoft HoloLens | Microsoft | Azure Government | Device + Azure cloud service |
| Microsoft Discovery | Microsoft | Azure Government (preview) | New 2025 preview product; likely under Azure boundary |
| SQL Server Management Studio | Microsoft | n/a (desktop tool) | Not a cloud service |
| Visual Studio / Visual Studio Enterprise | Microsoft | n/a (desktop IDE) | Not a cloud service |
| Microsoft Project | Microsoft | M365 GCC | Project Online is in M365 GCC |
| Microsoft ScreenSketch | Microsoft | n/a | Windows utility, not FedRAMP-scoped |
| Microsoft Search in Bing | Microsoft | M365 GCC | Bing/Search component of M365 |
| Google Translate | Google | Google Workspace / GCP | Public API, free tier; gov tier rolls under GCP |
| Google Lens | Google | n/a (consumer feature) | Mobile app feature |
| Google Maps | Google | Google Services (GCP) | Maps API rolls under GCP |
| Google Pixel | Google | n/a (hardware) | Device |
| AlphaFold | Google DeepMind | n/a | Open-source model; not a service |
| Apple Intelligence | Apple | n/a | Apple has no FedRAMP listings |
| Apple Face ID / Apple Maps | Apple | n/a | Device features |
| AWS GovCloud — generic listing | Amazon | F1603047866 | If a use case lists "AWS" generically, link to AWS GovCloud |
| Snowflake Cortex (Azure) | Snowflake | Snowflake Data Cloud on Azure Gov | If Azure-deployed, use FR1809360202A instead |
| IBM Watson / IBM ARGOS / IBM CoreDF | IBM | IBM Cloud for Government (F1211011660) | Watson rides on IBM Cloud; ARGOS / CoreDF likely classified |
| Llama (Meta) | Meta | n/a | Open-weight model; Meta has no FedRAMP marketplace presence; deployed via AWS Bedrock or Azure |
| Otter.ai | Otter | n/a | Could link to a hosting provider but Otter itself is not FedRAMP |
| SAP Concur | SAP | SAP NS2 Cloud Intelligent Enterprise | Different SAP product line; verify |

---

## Notable NO FEDRAMP PRESENCE products

Vendor has no row in `fedramp_products`. These are correctly unlinked. Listing the most-asked-about ones:

- **Anthropic** — Claude, Claude Code (Anthropic has zero FedRAMP rows as of this DB snapshot)
- **Anysphere / Cursor** — coding assistant, no FedRAMP listing
- **Codeium / Windsurf** — coding assistant, no FedRAMP listing
- **Tabnine** — coding assistant, no FedRAMP listing
- **Poolside** — coding assistant, no FedRAMP listing
- **Grammarly** — productivity, no FedRAMP listing
- **Meta / Llama** — open model
- **Reclaim.AI**, **Calendly**, **Canva**, **monday.com**, **Airtable**, **BioRender**, **Synthesia**, **HeyGen**, **WellSaid Labs** — productivity/SaaS, no FedRAMP listing
- **Vectra AI**, **Recorded Future**, **Dataminr**, **Flashpoint**, **Babel Street**, **Clearview AI**, **Magnet Forensics**, **Penlink**, **TRM Labs**, **Whooster**, **Marinus Analytics Traffic Jam**, **SITE Intelligence Group** — security/intelligence, no FedRAMP listing
- **Boston Dynamics Spot**, **Anduril Surveillance Tower**, **Skydio X2D**, **NEC NeoFace**, **IDEMIA CAT-2**, **Motorola LPR**, **Teledyne FLIR**, **ThruVision**, **ThruWave**, **Rekor**, **GlobalComm** — hardware / device-bound
- **C3.ai** — surprising, but no marketplace listing
- **Hyperscience**, **Dataiku** — no marketplace listing
- **Lasso Security**, **Credal**, **Yurts AI / Legion**, **GAIA AI**, **Pingwind**, **PassiveLogic**, **Quantaero**, **Skyward IT**, **iCatalyst**, **Aretec NEAT**, **Lexical Intelligence**, **Trigent PLATES**, **OneReach.ai**, **Ideation ReadyAI**, **Gurucul UEBA**, **Matroid**, **CrewAI**, **Custom In-House AI**, **Ultralytics YOLO**, **Open Source (PEST/Tesseract/crYOLO/cryoDRGN)** — small vendors, agency-built tools, or open-source software
- **CaseGuard**, **Amped Software**, **Airship AI**, **CryoSPARC (Structura)**, **Leica Aivia**, **Emerald Innovations**, **PassiveLogic**, **Shabash Merops**, **iProov**, **Expert.ai Cogito**, **Sumtotal**, **Skillsoft Percipio**, **Hyperscience**, **DocketScope**, **AveriSource**, **VoiceAtlas (Navteca)**, **NexisXplore**, **Scopus AI (Elsevier)**, **Digital Science Dimensions**, **Meltwater**, **Sprout Social**, **Tenable** (note: Tenable Government Solutions DOES exist — should be STRONG, not NO_PRESENCE; see recommendations)

---

## Recommendations

1. **Materialize the queue.** Re-key `fedramp_link_queue.inventory_id` (currently stale 1–305 IDs) by joining on `LOWER(canonical_name) = LOWER(source_text)`, then write into `fedramp_product_links` for every queue row whose decision points to one or more FedRAMP IDs. The queue's `llm_proposed_fedramp_ids` field is the right source.
2. **Re-run the alias matcher with corrected aliases.** The pipeline declared 108 products as `rejected/no_alias` — but spot checks show many had FedRAMP entries that the aliases simply didn't match. Add canonical aliases like:
   - "Azure Government" → covers Azure OpenAI, Azure AI Foundry, Azure Speech, Azure AI Document Intelligence, Power Platform, Power BI, Dynamics 365, Defender, Sentinel, Copilot Studio, Copilot for Security
   - "M365 GCC" / "Microsoft 365 GCC" → covers all M365 client apps + M365 Copilot family
   - "AWS GovCloud" → covers AWS Bedrock/Kendra/Lex/Rekognition/Textract/Transcribe/Q/CodeWhisperer
   - "Salesforce Government Cloud Plus" → covers Salesforce Einstein, Tableau (Salesforce-owned)
   - "GitHub Enterprise Cloud" → GitHub Copilot
3. **Hand-link the 50 products that have no queue entry at all.** The list above includes major vendors (Microsoft Purview, Salesforce Einstein, ServiceNow Now Assist, Slack, Tableau, ChatGPT, OpenAI API, DALL-E, Gemini, Google Workspace, Google Cloud Platform, Crowdstrike Falcon, Wiz, Cohesity, Dynatrace, Illumio, ID.me, Lookout, Informatica, Relativity, Sprinklr, Asana, LexisNexis Risk Solutions, Grok, Cellebrite Media Classifier, Veritone, Chainalysis, Ask Sage). These were never even considered.
4. **Document the SaaS-rolls-up-to-platform pattern.** Many AI products (Azure OpenAI, AWS Bedrock, Salesforce Einstein) don't have their own FedRAMP CSO — they inherit authorization from the underlying platform. Add a column or convention (`link_type='inherits'`) so the dashboard can render this distinction. Otherwise `confidence='strong'` understates the relationship.
5. **Distinguish "no FedRAMP attempt" from "FedRAMP not applicable".** Open-source tools (Llama, YOLO, Tesseract, AlphaFold), agency-built platforms (already excluded), and desktop utilities (Visual Studio, Microsoft Edge) should not be lumped with "vendor missing from FedRAMP."
6. **Verify a few edge cases** before bulk-linking:
   - **Tenable** is listed in both inventory products (`Tenable`) and FedRAMP (`Tenable Government Solutions`). It belongs in STRONG, not NO_PRESENCE — confirmed in lookups.
   - **Apptio for IBM** — different product line from Watson; do not confuse.
   - **Wolters Kluwer TeamMate vs. UpToDate** — TeamMate is audit software; UpToDate is medical reference. They are different products. Likely UpToDate has no FedRAMP listing.
   - **SAP Concur vs. SAP NS2** — different lines; the FedRAMP listing is for SAP NS2 Cloud Intelligent Enterprise, NOT Concur.
7. **Track stale-FK risk going forward.** The fact that 199 queue rows still point at stale 1–305 IDs is a process smell. When `products` is rebuilt, queue/link tables either need to be rebuilt with it or keyed on canonical_name (more durable than autoincrement IDs).

---

## Appendix: How to reproduce

```sql
-- Products without a queue entry
SELECT p.id, p.canonical_name, p.vendor
FROM products p
LEFT JOIN fedramp_link_queue q
  ON LOWER(p.canonical_name) = LOWER(q.source_text)
 AND q.link_kind = 'product'
WHERE q.id IS NULL
  AND p.product_origin = 'commercial'
ORDER BY p.vendor, p.canonical_name;

-- FedRAMP marketplace search by vendor token
SELECT fedramp_id, csp, cso, status
FROM fedramp_products
WHERE LOWER(csp) LIKE '%<vendor>%' OR LOWER(cso) LIKE '%<vendor>%';

-- Resolved-but-not-linked queue rows (the salvageable backlog)
SELECT q.source_text, q.reason, q.status, q.llm_proposed_fedramp_ids
FROM fedramp_link_queue q
WHERE q.link_kind = 'product' AND q.status = 'resolved';
```
