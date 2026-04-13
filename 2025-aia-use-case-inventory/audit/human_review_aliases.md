# Alias Review Summary

## Check
Reviewed all `162` proposed alias rows from [proposed_aliases.csv](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/proposed_aliases.csv). The source file had a malformed header, so the output CSVs normalize the raw six-column row shape into the canonical schema: `queue_id`, `canonical_product_id`, `proposed_alias`, `source_vendor`, `source_label`, `llm_confidence`, `llm_reasoning`, and `review_disposition`.

> Schema note: the first column is `queue_id` (a `review_queue_products.id`, e.g. 847–1079), NOT a canonical `products.id`. `canonical_product_id` is a new nullable column for the handful of cases where an alias should map to an existing canonical product; when NULL, the row indicates "create a new `products` row with `proposed_alias` as canonical_name." All rows in this cut currently have `canonical_product_id` NULL — no reviewer note explicitly mapped to an existing canonical id.

## Method
Applied a conservative human-style rubric: seed only clear commercial product/vendor aliases, hold internal agency systems and compound implementations, and reject aliases that are too broad or would collapse distinct product families. Each input row was assigned exactly once. A second pass (see Amendments) repartitioned rows to fix duplicates, cross-partition contradictions, agency-wrapper leakage, open-source leakage, and parent/variant collisions.

## Findings (post-amendment counts)
- `99` rows approved for `seed_now`.
- `40` rows held for manual follow-up (internal systems, compound deployments, agency wrappers, or vendor/system conflations).
- `5` rows rejected as over-broad, open-source, or non-AI software.
- `18` rows moved to `proposed_aliases_dedup_drop.csv` — duplicates of a kept canonical row. These can later become aliases pointing to the single canonical product.
- The strongest cluster for hold decisions remains the DHS/CBP-style system names: `TVS`, `RAVEn`, `ATS`, `ELIS`, `PCIS`, `VIEW/CVAS`, `ARGOS`, `VIS`, `BET`, and similar branded agency systems.
- Most remaining `seed_now` rows are usable commercial aliases and look ready to seed into lookup-building after final human approval.

## Examples
- `seed_now`: `FLIR 280 HD`, `Clearview AI`, `LIGER Generative AI Toolkit`, `Dataminr First Alert`, `Microsoft Power BI`, `TRM Labs Blockchain Analysis Platform`, `Palantir Decision and Analytics Platform (DNA-P)`.
- `hold`: `CBP Traveler Verification Service (TVS)`, `Repository for Analytics in a Virtualized Environment (RAVEn)`, `EnerGPT`, `LISA Chatbot`, `Chatlab`, `Automated Targeting System (ATS)`, `ARGOS`, `Biometrics Enrollment Tool (BET)`.
- `reject`: bare `Palantir` (guardrail), `Ultralytics YOLO`, `Tesseract OCR`, `Elastic Stack (ELK)`, `PEST`.
- `dedup_drop`: 6 of 7 duplicate `NEC NeoFace` rows, bare `TRM Labs`, bare `Microsoft Bing`, bare `Dataminr`, etc.

## Recommended follow-up
- Seed the `seed_now` file after a final spot-check.
- Keep the `hold` bucket out of `build_lookups.py` until those rows are resolved.
- Treat the `reject` rows as guardrail examples for over-broad vendor-only aliases, open-source libraries, and non-AI software.
- Consider using `dedup_drop` rows later as `product_aliases` entries pointing at the kept canonical row, rather than discarding them.

## Amendments (data-quality pass)
A follow-up repartition fixed six classes of issues flagged by a prior reviewer:

1. **Schema fix (all 4 CSVs).** Renamed `product_id` → `queue_id` to reflect that the column holds `review_queue_products.id`, not `products.id`. Added nullable `canonical_product_id` column so the seed can distinguish "create new canonical" (NULL) from "map alias to existing canonical X" (populated).
2. **Collapsed 10 duplicate-alias groups in `seed_now`** (kept 1 canonical row per group, moved the rest to `proposed_aliases_dedup_drop.csv`):
   - `NEC NeoFace` — 7 rows collapsed to 1 (kept queue_id=868, dropped 857, 858, 859, 860, 866, 874).
   - `Salesforce Einstein` — kept 915, dropped 1053.
   - `Palantir Case Management & Analytics (CMA)` — kept 925, dropped 927.
   - `Microsoft OneNote` — kept 974, dropped 1049 (MUI variant).
   - `Microsoft OneDrive` — kept 1015, dropped 1026 (MUI variant).
   - `Microsoft AI Builder` — kept 1031, dropped 978.
   - `Google Cloud Platform` — kept 998, dropped 992.
   - `Boston Dynamics Spot` — kept 966, dropped 951.
   - `Altana Atlas` — kept 904, dropped 890.
   - `Tabnine` — kept 994, dropped 1034.
3. **Resolved 2 cross-partition contradictions** (moved `seed_now` copy to `hold` where the other copy was already held):
   - `Automated Targeting System (ATS)` — queue_id 898 moved to hold (899 was already hold).
   - `Person Centric Identity Services (PCIS)` — queue_id 914 moved to hold (884 was already hold).
4. **Clarified Palantir reject.** The reject for bare `Palantir` (queue_id=967) now explicitly says it applies to the BARE alias only; the three specific Palantir sub-products (`CMA`, `Federal Cloud Service`, `DNA-P`) remain in `seed_now`.
5. **Moved 8 agency-wrapper / in-house systems out of `seed_now` into `hold`** (same criterion as TVS/RAVEn/ELIS): `ARGOS` (881), `Biometrics Enrollment Tool` (909), `Verification Information System (VIS)` (882), `AIS Resume Screening` (873), `Low-Pfa Screening Algorithm` (877), `PDRI Exam Proctor Support` (892), `Starlo Position Description Tool` (917), `Acoustic Signature AI for Gunshot Detection` (848).
6. **Moved 3 open-source / generic / non-AI rows to `reject`**: `Ultralytics YOLO` (1067), `Tesseract OCR` (1017), `Elastic Stack (ELK)` (995). Also moved `PEST` (1021) from `hold` to `reject` (groundwater modeling software, not AI).
7. **Collapsed 3 parent/variant pairs** (kept the more specific variant, demoted the bare vendor to dedup_drop): `TRM Labs` (862) → `TRM Labs Blockchain Analysis Platform` (905); `Microsoft Bing` (968) → `Microsoft Search in Bing` (1008); `Dataminr` (887) → `Dataminr First Alert` (932). Verified `Visual Studio` (1014) + `Visual Studio Enterprise` (972) are kept separate (distinct SKUs: Community free vs Enterprise paid).

### Final counts

| CSV | Old | New |
|---|---|---|
| `proposed_aliases_seed_now.csv` | 130 | 99 |
| `proposed_aliases_hold.csv` | 31 | 40 |
| `proposed_aliases_reject.csv` | 1 | 5 |
| `proposed_aliases_dedup_drop.csv` | (new) | 18 |
| **Total** | **162** | **162** |

Verification: pandas load + sqlite cross-check confirms (a) no duplicate `proposed_alias` values in `seed_now` and (b) all 99 `queue_id`s resolve to real rows in `review_queue_products`.
