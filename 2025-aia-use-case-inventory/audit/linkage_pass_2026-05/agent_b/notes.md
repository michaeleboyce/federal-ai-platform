# Agent B notes — May 2026 linkage pass

## Scope
Processed 130 input rows across two slices:
- `slice_b_mention_only_individual.csv` — 77 individual use cases where the pre-classifier matched a catalog vendor token in `use_case_name`/`system_name` but `vendor_name` was blank/generic.
- `slice_b_named_consolidated.csv` — 53 consolidated entries with a non-empty `commercial_product`.

Emitted **152 decisions** in `recommendations.json` (a single consolidated row often splits into multiple decisions when `commercial_product` lists several products).

## Decision counts

| Decision | Count |
|---|---:|
| false_positive | 49 |
| link | 39 |
| add_product | 37 |
| unclear | 21 |
| add_alias | 6 |
| **Total** | **152** |

## Mention-only slice — the dominant pattern is spurious sub-string matching

64% of the 77 mention-only rows are `false_positive`. The pre-classifier matched on common English substrings rather than real product mentions. Top offenders:

- **meta** matched on "metadata", "metabolic", "metallic", "Metathesaurus", "meta-analysis" — none of which reference Meta the company. 13 false positives.
- **descript** matched on "description", "descriptors", "descriptive" — 7 false positives.
- **site** matched on "website", "on-site", "mine sites", "research sites", "satellite", "offsite", "site applications" — 11 false positives.
- **axon** matched on "taxonomy" — 4 false positives (DOT/GSA/HHS NLP work).
- **litera** matched on "literature", "literal" — 4 false positives (literature review and ICD coding).
- **articulate** matched on "particulate".
- **cisco** matched on "Francisco".
- **ideation** matched on "Suicidal Ideation" (clinical term).
- **canva** matched on "Canvas" (dashboard).
- **aware** matched on "Awareness".

Real links found in the mention-only slice (high-confidence): `Articulate 360 AI Assistant` (VA, verbatim), `Skillsoft Percipio CAISY` (DOJ), `UiPath Enterprise RPA` (DOJ + VA, several rows), `Microsoft 365 Copilot` (HHS FSAP — narrative explicitly names "copilot for internal use"), `Adobe Creative Cloud Suite` (VA), `Microsoft Power Platform` (FDIC Power Apps + VA Power Automate — both with proposed aliases), `Google Vertex AI` (DOC), `ChatGPT + DALL-E` (DOC), `Elastic Stack` (GSA), `Axon Evidence` (VA Axon Body Camera).

## Consolidated slice — mostly real, with a Big Ten "Copilot" cluster

The named-consolidated slice is largely actionable: 53 rows → 41 link/add_product/add_alias decisions and 12 `unclear`.

The standout cluster is **FRB**, which fills its `commercial_product` with generic boilerplate like "External- Chatbots", "Internal Gov Cloud- Chatbots", "External- Cybersecurity Suites", "External- Smartphone OS", "External- Government Travel System". All 9 FRB rows in this slice ended `unclear` — these placeholders should probably be flagged for the FRB review queue and the agency asked to specify products. The dashboard cannot do anything useful with them.

The "**CoPilot**" string appears 8 times across FTC, NLRB, EAC, DHS — all link to `Microsoft 365 Copilot`. Worth confirming via a single consolidation rule.

Apple's products are mentioned three times for face-unlock: 9368 (FTC "iPhones") and 9408 (Udall "Apple") both link to `Apple Face ID`; 9388 (GSA "Face recognition for GFE phones") and 9606 (PBGC "Native map applications") stayed `unclear` because the agency-named product is ambiguous between Apple and Android.

## Proposed catalog additions (37 add_product decisions)

The most material gaps:

- **Google Colab** (Google) — DOC titles it explicitly; not in catalog.
- **Adobe Sensei** (Adobe; parent: Adobe Creative Cloud Suite) — DOC names it as an AI tool.
- **OpenText Records Management** (OpenText) — DOE; distinct from OpenText Axcelerate already in catalog.
- **Bloomberg Law AI** (Bloomberg) — DOJ; the existing `Bloomberg Government` row is a different product.
- **Amazon SageMaker** (Amazon) — GSA threat detection explicitly names it; high-value omission.
- **Google Coral TPU** (Google) — NASA names it; AI accelerator hardware.
- **Google Earth Engine** (Google) — USDA names it for soil mapping.
- **Elsevier ClinicalKey AI** (Elsevier) — VA names it.
- **Litera Compare** (Litera) — DOC consolidated; distinct from `Litera TOA Builder`.
- **TVEyes Media Monitoring** (TVEyes) — DOE consolidated (misspelled "TV eyes").
- **Doble Test Assistant** (Doble Engineering) — DOE sector-specific.
- **Konica Minolta Dispatcher Paragon** — DOE.
- **DRUID AI, Supportbench, ManageEngine ServiceDesk Plus** — HHS + DOL consolidated helpdesk bucket.
- **Apple News, MediaViz AI, Google News Brief** — HHS / DOL / FLRA / NEA news-curation bucket (Google News Brief is referenced by 4 agencies — definitely worth seeding).
- **Azure Synapse Analytics** (Microsoft; parent: Microsoft Azure Platform) — DHS.
- **Google Calendar** (Google; parent: Google Workspace) — DOT.
- **Genesys Cloud CX** (Genesys) — VA.
- **VA GPT** (VA) — VA-OIG; internal-built, not commercial, but a real catalog entry.
- **Microsoft Viva** (Microsoft) — EPA + NTSB.
- **CWTSatoTravel** — FDIC; weak AI signal, modest confidence.
- **Vyond** (Vyond) — FLRA; AI video creation.
- **Mural** (Mural) — NASA; visual collaboration with AI features.
- **OpenAI Codex** (OpenAI) — OPM code generation.
- **Zendesk AI** (Zendesk) — OPM helpdesk.
- **HackerOne AI** (HackerOne) — SEC security.
- **NetApp ARP/AI** (NetApp) — SEC ransomware protection.

## Proposed alias additions (6 decisions)

- `Microsoft Power Platform`: add `Microsoft Power Apps` (FDIC) and `Microsoft Power Automate` (VA).
- `Adobe Creative Cloud Suite`: add `Adobe Premiere` (DHS consolidated).
- `UiPath Enterprise RPA`: add `UiPath Document Understanding` (DOJ + VA).
- `DALL-E`: add `DALLE3` (DOC, common no-hyphen form).
- `LexisNexis`: add `Law360` (NIGC; Law360 is a major LexisNexis sub-brand).

## What I flagged as `unclear`

- All FRB rows with `External-…` placeholders (8 rows) and one FRB Apple/Android Smartphone-OS face-unlock row.
- HHS NCIRD SmartFind, CDC-State cables, Rabies ML — `system_name="Microsoft"` is too generic to identify the specific MS product.
- SEC ACES (AWS environment but no specific AWS AI product named).
- DOC's "Google Public Sector NLP" and "AWS NLP Classification Text Mining" — title-stamped, no narrative.
- TVA "Cisco ML" — title-only, can't disambiguate which Cisco product.
- DOJ "Open Source Investigative Tool" with redacted vendor.
- VA "VA Chat Copilot Meta Pilot" — title combines multiple products with no narrative.
- DOE consolidated 8949 / 8967 — DOE internal apps, not commercial AI.
- GSA 9388 "Face recognition for GFE phones" and PBGC 9606 "Native map applications".
- FRB 9333 "External- Creative Production Suite".

## Items that need catalog-level engineering attention

1. **The pre-classifier's sub-string matching is producing very low-quality candidates in the mention-only slice** (64% false-positive rate). The "site" / "meta" / "descript" / "litera" / "axon" tokens in particular should require ≥4-char whole-word boundaries plus a vendor co-occurrence check. Consider tightening these alias rules upstream.
2. **FRB's `External- *` boilerplate** in consolidated rows is unactionable. Either pursue agency-specific clarification, or accept that ~14% of consolidated entries are intentionally generic.
3. **"Google News Brief"** is referenced by 4 different agencies — it appears to be a real distinct AI feature (Google's AI-summarized news cards), worth seeding even if confidence on the canonical product page is modest.
4. **"Microsoft 365 Copilot"** absorbs a lot of "Copilot" / "CoPilot" mentions across the consolidated slice. Worth confirming this is the right canonical target (vs. Copilot Chat, Copilot for Security, etc.) — the consolidated taxonomy lumps everything under "Copilot" without distinguishing.
