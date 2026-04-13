# 2025 AI Inventory Audit Summary

## Output set
- Source-file reviews: `47` files in [audit/reviews](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/reviews)
- Cross-cut consistency checks: `7` files in [audit/consistency](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency)
- Public evidence downloads: `8` files in [audit/downloads](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/downloads)
- Public verification note: [public_verification_note.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/research/public_verification_note.md)

## Highest-signal findings
1. Source-ID traceability is the biggest structural defect.
`use_cases` has `3,616` rows. Only `1,049` have a populated `use_case_id`. `2,007` more still carry a source ID in `raw_json` but lost it during normalization, and another `560` rows had no source ID in the source payload at all. See [01_id_traceability.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency/01_id_traceability.md).

2. Ingest row counts are mostly reliable.
Across `47` source files, only `2` showed raw-vs-DB count deltas. `DHS` was a harmless trailing-row artifact. `DOI` is the only likely substantive omission: `DOI-0015`, which had a blank use case name but otherwise populated fields. See [02_row_count_and_ingest_integrity.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency/02_row_count_and_ingest_integrity.md).

3. LLM-related tags are materially over-applied.
Out of `1,434` rows carrying at least one LLM-related flag, the audit found `143` suspicious rows. The biggest false-positive clusters are `63` classical/predictive ML rows, `50` NLP/text-analytics rows, and `30` computer-vision rows. See [03_llm_vs_non_llm_classification.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency/03_llm_vs_non_llm_classification.md).

4. Vendor-backed tools are often mislabeled as custom systems.
There are `452` rows across `22` agencies where the source says the system was purchased from a vendor but the tags still say `custom_system`. Largest concentrations are `DOJ` (`137`), `VA` (`100`), `DOE` (`51`), `HHS` (`44`), and `DHS` (`40`). See [04_vendor_product_vs_custom_system.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency/04_vendor_product_vs_custom_system.md).

5. Product mapping quality is decent but not clean.
`cots_product_name` has `58` unmatched values out of `639` populated rows; `tool_product_name` has `24` unmatched values out of `592`. `Microsoft 365 Copilot` and `ServiceNow Now Assist` are both acting as over-broad buckets, and `5` explicit product-use rows are missing a product label entirely. See [05_product_mapping_and_alias_quality.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency/05_product_mapping_and_alias_quality.md).

6. Consolidated scope assignment is too optimistic.
In `consolidated_use_cases`, `111` of `192` rows are tagged `enterprise_wide`, and `29` of those also have `Agency Use (Y/N)? = N`. This is concentrated in `USTDA`, `PBGC`, `OSC`, and `FCC`. See [06_scope_and_maturity_consistency.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency/06_scope_and_maturity_consistency.md).

7. Several fields are too blank or coarse for strong analysis.
`product_capability` is blank on `3,615` of `3,616` canonical rows. `architecture_type` is `unknown` on `2,113` canonical rows (`58.5%`). Only `473` canonical rows have `product_id`. The worst large files for weak product linkage are `NASA`, `DOJ`, `Treasury`, `DHS`, and `HHS`. See [07_field_fullness_and_tag_coarseness.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/consistency/07_field_fullness_and_tag_coarseness.md).

## Representative source-level findings
- [DHS__use_cases__DHS-2025-ai-inventory.csv.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/reviews/DHS__use_cases__DHS-2025-ai-inventory.csv.md): all source IDs lost; commercial generative-AI rows tagged as `custom_system`; ATR row tagged as `general_llm`.
- [DOE__use_cases__DOE-2025-ai-inventory.xlsx.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/reviews/DOE__use_cases__DOE-2025-ai-inventory.xlsx.md): all source IDs lost; vendor-backed rows like `Vectra`, `PassiveLogic`, and `Microsoft` still tagged `custom_system`.
- [GSA__use_cases__GSA-2025-ai-inventory.csv.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/reviews/GSA__use_cases__GSA-2025-ai-inventory.csv.md): `Slack AI` mapped to `Microsoft Teams`; `FAS Vision Agentforce` mapped to `Custom In-House AI`.
- [EPA__use_cases__EPA-2025-ai-inventory.csv.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/reviews/EPA__use_cases__EPA-2025-ai-inventory.csv.md): `Power Automate` document extraction tagged as generative/LLM; `Briefcam` stored as `custom_system`.
- [FRB__use_cases__FRB-2025-ai-inventory.csv.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/reviews/FRB__use_cases__FRB-2025-ai-inventory.csv.md): body-camera management row tagged as computer vision/non-generative despite source generative framing; conference-call monitor likely over-tagged as `general_llm`.
- [FTC__use_cases__FTC-2025-ai-inventory.csv.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/reviews/FTC__use_cases__FTC-2025-ai-inventory.csv.md): transcription and IVR assistant rows over-tagged as `general_llm`.

## Public verification
- DHS public documentation explicitly confirms an updated inventory with `158 active AI use cases` and names `CBP Translate`, `Babel`, `Passive Body Scanner`, `Video Analysis Tool`, and `Hurricane Score`.
- DOE’s public inventory page confirms the 2025 DOE inventory and links the downloadable spreadsheet.
- The downloaded `NatLabRockies/elm` page confirms that ELM applies LLMs to energy research and includes an `energy_wizard` chatbot example.
- NASA and VA public inventory pages were downloaded successfully; the VA page explicitly states `367 AI use cases` in the individual inventory and `13` in the consolidated inventory, and highlights `VA GPT`, `AI-Assisted Software Development`, `STORM`, and the `Payment Redirect Fraud` model.
- Limits: direct HHS download returned `403`, and the inventory-linked `dhs-gov/tasr_lda` GitHub URL returned `404`.

## Recommended next actions
1. Fix canonical ID mapping first and backfill the `2,007` dropped IDs from `raw_json`.
2. Re-run or patch tags for the `143` suspicious LLM false positives.
3. Reclassify the clearest vendor-backed `custom_system` rows to `product_deployment`.
4. Tighten product alias rules, especially for `Microsoft 365 Copilot` and `ServiceNow Now Assist`.
5. Treat `product_capability`, `architecture_type`, and `deployment_scope` as incomplete analytical fields until they are made more specific.
