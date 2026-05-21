# 2024 ↔ 2025 AI Use Case Inventory — Comparability Matrix

Phase 0 deliverable. The authoritative, column-by-column disposition of the
2024 (M-24-10) inventory against the 2025 (M-25-21) schema. Every later phase —
the loader, the matcher, the dashboard — cites this file when deciding whether a
field can be honestly compared.

**Source of truth:** `column_maps_2024.py` (`COLUMN_CROSSWALK_2024`). If the two
ever disagree, the module wins — this file is the human-readable mirror.

## Column count

The live 2024 file (`data/raw/2024_consolidated_ai_inventory_raw_v2.csv`,
cp1252) ships **62 columns**. Early planning notes said 54 — that figure is the
count of *distinct header strings*: the 2024 form repeats the literal header
`"If Other, please explain."` nine times and `"If No, please explain."` once
(ten follow-up columns, two distinct strings → 62 columns, 54 unique strings).
The crosswalk has one entry per real column, so it has **62 entries** and
nothing is silently dropped. The ten repeated-header columns resolve
positionally (by CSV ordinal), not by text.

## Disposition summary

| Comparability | Count | Meaning |
|---|---:|---|
| `directly_comparable` | 21 | Same concept, same value space — compare as-is. |
| `recoded` | 4 | Same concept, different value taxonomy — comparison needs a (lossy) value recode. |
| `2024_only` | 37 | No 2025 equivalent — cannot be compared. |
| **Total** | **62** | |

The 37 `2024_only` columns break down as: 10 "If Other/No" follow-up metadata
columns, 7 agency-readiness/infrastructure questions, 3 HISP columns, 3 date
columns, plus 14 other M-24-10 questions M-25-21 dropped (COTS self-ID, IQA,
SAOP, PIID, code-access, data-docs, internal-review, autonomy, AI-notice,
adverse-impact, disparity-mitigation, opt-out, public-info, topic-area-other).

## The 62 columns

| # | 2024 column | snake_case | 2025 target | comparability | notes |
|---:|---|---|---|---|---|
| 0 | Use Case Name | `use_case_name` | `use_case_name` | directly_comparable | Title of the AI use case; same concept both years. |
| 1 | Agency | `agency` | `agency_name` | directly_comparable | Agency full name; OMB-added consolidation column both years. |
| 2 | Agency Abbreviation | `agency_abbreviation` | `agency_abbreviation` | directly_comparable | Agency abbreviation; OMB-added consolidation column both years. |
| 3 | Bureau | `bureau` | `bureau_component` | directly_comparable | Sub-agency org; free text, messy both years but same concept. |
| 4 | Use Case Topic Area | `topic_area` | `topic_area` | directly_comparable | Topic area; enum drifted but concept shared and dashboard already collapses topic aliases. |
| 5 | Other (Use Case Topic Area) | `topic_area_other` | — | 2024_only | Free-text "Other" detail for topic_area; metadata. |
| 6 | Is the AI use case found in the below list of general commercial AI products and services? | `commercial_ai` | — | 2024_only | 2024 COTS self-ID; 2025 split COTS into a separate Appendix B inventory. |
| 7 | What is the intended purpose and expected benefits of the AI? | `purpose_benefits` | `expected_benefits` | recoded | 2024 combines problem + benefits; M-25-21 splits into two fields. Lossy. |
| 8 | Describe the AI system's outputs. | `outputs` | `system_outputs` | directly_comparable | Free-text system outputs; same concept both years. |
| 9 | Stage of Development | `dev_stage` | `stage_of_development` | recoded | 2024 5-value SDLC enum vs 2025 4-value posture enum. See `DEV_STAGE_RECODE_2024`. |
| 10 | Is the AI use case rights-impacting, safety-impacting, both, or neither? | `impact_type` | `is_high_impact` | recoded | Taxonomies do NOT map 1:1. See `IMPACT_TYPE_RECODE_2024` (lossy). |
| 11 | Date Initiated | `date_initiated` | — | 2024_only | M-25-21 collapsed four date fields into one; no home. |
| 12 | Date when Acquisition and/or Development began | `date_acq_dev_began` | — | 2024_only | M-25-21 collapsed four date fields into one; no home. |
| 13 | Date Implemented | `date_implemented` | `operational_date` | recoded | Closest analogue to operational_date, but 2025 conflates pilot-start and deployment dates. Approximate. |
| 14 | Date Retired | `date_retired` | — | 2024_only | 2025 expresses retirement via the "Retired" stage, not a date. |
| 15 | Was the AI system involved in this use case developed (or is it to be developed) under contract(s) or in-house? | `dev_method` | `development_type` | directly_comparable | Contracting vs in-house vs both; same three-way value space. |
| 16 | Provide the Procurement Instrument Identifier(s) (PIID) of the contract(s) used. | `contract_piids` | — | 2024_only | M-25-21 dropped the PIID column entirely. |
| 17 | Is this AI use case supporting a High-Impact Service Provider (HISP) public-facing service? | `hisp_support` | — | 2024_only | HISP block; M-25-21 dropped HISP reporting. |
| 18 | Which HISP is the AI use case supporting? | `hisp_name` | — | 2024_only | HISP block; M-25-21 dropped HISP reporting. |
| 19 | Which public-facing service is the AI use case supporting? | `public_service` | — | 2024_only | HISP block; M-25-21 dropped HISP reporting. |
| 20 | Does this AI use case disseminate information to the public? | `public_info` | — | 2024_only | Information-dissemination question; M-25-21 has no equivalent. |
| 21 | How is the agency ensuring compliance with Information Quality Act guidelines, if applicable? | `iqa_compliance` | — | 2024_only | Information Quality Act compliance; M-25-21 dropped it. |
| 22 | Does this AI use case involve personally identifiable information (PII) that is maintained by the agency? | `contains_pii` | `has_pii` | directly_comparable | PII Yes/No; same concept and value space. |
| 23 | Has the Senior Agency Official for Privacy (SAOP) assessed the privacy risks associated with this AI use case? | `saop_review` | — | 2024_only | SAOP privacy-risk review; M-25-21 replaced it with the optional pia_url link, not a comparable Yes/No. |
| 24 | Do you have access to an enterprise data catalog or agency-wide data repository...? | `data_catalog` | — | 2024_only | Agency-readiness/infrastructure question; M-25-21 dropped the readiness block. |
| 25 | If Other, please explain. | `data_catalog_other` | — | 2024_only | Free-text "Other" detail for data_catalog; metadata. |
| 26 | Describe any agency-owned data used to train, fine-tune, and/or evaluate performance of the model(s) used in this use case. | `agency_data` | `training_data_description` | directly_comparable | Free-text training-data description; same concept (2024 scopes to agency-owned, 2025 broader but compatible). |
| 27 | Is there available documentation for the model training and evaluation data...? | `data_docs` | — | 2024_only | Training-data documentation-maturity scale; M-25-21 dropped it. |
| 28 | Which, if any, demographic variables does the AI use case explicitly use as model features? | `demo_features` | `demographic_features` | directly_comparable | Demographic model features; multi-select, near-identical value lists. |
| 29 | If Other, please explain. | `demo_features_other` | — | 2024_only | Free-text "Other" detail for demo_features; metadata. |
| 30 | Does this project include custom-developed code? | `custom_code` | `has_custom_code` | directly_comparable | Custom-code Yes/No; same concept and value space. |
| 31 | Does the agency have access to the code associated with the AI use case? | `code_access` | — | 2024_only | Code-access tri-state; M-25-21 keeps only the optional code_url link. |
| 32 | If the code is open-source, provide the link for the publicly available source code. | `code_link` | `code_url` | directly_comparable | Optional link to public source code; same concept. |
| 33 | Does this AI use case have an associated Authority to Operate (ATO) for an AI system? | `has_ato` | `has_ato` | directly_comparable | ATO Yes/No; same concept and value space. |
| 34 | System Name | `system_name` | `system_name` | directly_comparable | ATO system name; free text, same concept. |
| 35 | How long have you waited for the necessary developer tools to implement the AI use case? | `dev_tools_wait` | — | 2024_only | Agency-readiness block; M-25-21 dropped the readiness/infrastructure questions. |
| 36 | For this AI use case, is the required IT infrastructure provisioned via a centralized intake form or process inside the agency? | `infra_provisioned` | — | 2024_only | Agency-readiness block; M-25-21 dropped it. |
| 37 | If Other, please explain. | `infra_provisioned_other` | — | 2024_only | Free-text "Other" detail for infra_provisioned; metadata. |
| 38 | Do you have a process in place to request access to computing resources for model training and development...? | `compute_request` | — | 2024_only | Agency-readiness block; M-25-21 dropped it. |
| 39 | If Other, please explain. | `compute_request_other` | — | 2024_only | Free-text "Other" detail for compute_request; metadata. |
| 40 | Has communication regarding the provisioning of your requested resources been timely? | `timely_resources` | — | 2024_only | Agency-readiness block; M-25-21 dropped it. |
| 41 | If Other, please explain. | `timely_resources_other` | — | 2024_only | Free-text "Other" detail for timely_resources; metadata. |
| 42 | How are existing data science tools, libraries, data products, and internally-developed AI infrastructure being re-used...? | `existing_reuse` | — | 2024_only | Agency-readiness block; M-25-21 dropped it. |
| 43 | Has information regarding the AI use case... been made available for review and feedback within the agency? | `internal_review` | — | 2024_only | Internal-documentation-availability scale; M-25-21 dropped it. |
| 44 | Has your agency requested an extension to implement the minimum risk management practices for this AI use case? | `extension_request` | — | 2024_only | M-24-10 risk-practice extension request; M-25-21 has no equivalent gating field. |
| 45 | Has an AI impact assessment been conducted for this AI use case? | `impact_assessment` | `hi_assessment_completed` | directly_comparable | AI impact assessment status; near-identical value list both years. |
| 46 | Has the AI use case been tested in operational or real-world environments...? | `real_world_testing` | `hi_testing_conducted` | directly_comparable | Pre-deployment/real-world testing; same concept. |
| 47 | What are the key risks from using the AI for this particular use case and how were they identified? | `key_risks` | `hi_potential_impacts` | directly_comparable | Free-text foreseeable-risk identification; 2024 "key risks" == 2025 "potential impacts". |
| 48 | Has an independent evaluation of the AI use case been conducted? | `independent_eval` | `hi_independent_review` | directly_comparable | Independent evaluation/review status; same concept. |
| 49 | Is there a process to monitor performance of the AI system's functionality... as part of the post-deployment plan...? | `monitor_postdeploy` | `hi_ongoing_monitoring` | directly_comparable | Post-deployment ongoing monitoring; same concept. |
| 50 | For this particular use case, can the AI carry out a decision or action without direct human involvement...? | `autonomous_impact` | — | 2024_only | Autonomy/human-involvement question; M-25-21 dropped it. |
| 51 | If Other, please explain. | `autonomous_impact_other` | — | 2024_only | Free-text "Other" detail for autonomous_impact; metadata. |
| 52 | How is the agency providing reasonable and timely notice regarding the use of AI...? | `ai_notice` | — | 2024_only | AI-notice mechanism; M-25-21 dropped it. |
| 53 | If Other, please explain. | `ai_notice_other` | — | 2024_only | Free-text "Other" detail for ai_notice; metadata. |
| 54 | Is the AI used to significantly influence or inform decisions or actions that could have an adverse or negative impact...? | `adverse_impact` | — | 2024_only | Adverse-decision-influence question; M-25-21 dropped it. |
| 55 | What steps has the agency taken to detect and mitigate significant disparities in the model's performance across demographic groups...? | `disparity_mitigation` | — | 2024_only | Demographic-disparity detection/mitigation; M-25-21 dropped this free-text field. |
| 56 | What steps has the agency taken to consult and incorporate feedback from groups affected by this AI use case? | `stakeholder_consult` | `hi_public_consultation` | directly_comparable | Public/affected-group consultation; same concept. |
| 57 | If Other, please explain. | `stakeholder_consult_other` | — | 2024_only | Free-text "Other" detail for stakeholder_consult; metadata. |
| 58 | Is there an established fallback and escalation process for this AI use case in the event that an impacted individual or group would like to appeal...? | `appeal_process` | `hi_appeal_process` | directly_comparable | Appeal/contest process; same concept and value space. |
| 59 | If No, please explain. | `no_appeal_reason` | — | 2024_only | Free-text "If No" detail for appeal_process; metadata. |
| 60 | Where practicable... is there an established mechanism for individuals to opt-out from the AI functionality in favor of a human alternative? | `opt_out` | — | 2024_only | Opt-out mechanism; M-25-21 dropped it. |
| 61 | If Other, please explain. | `opt_out_other` | — | 2024_only | Free-text "Other" detail for opt_out; metadata. |

## The `recoded` columns in detail

Four columns share a concept with 2025 but need a value transform:

| 2024 column | 2025 target | Recode map | Lossy? |
|---|---|---|---|
| `dev_stage` (Stage of Development) | `stage_of_development` | `DEV_STAGE_RECODE_2024` | Partly — `Acquisition and/or Development` → `a) Pre-deployment` and `Implementation and Assessment` → `b) Pilot` are approximations; the others are clean. |
| `impact_type` (rights/safety/both/neither) | `is_high_impact` | `IMPACT_TYPE_RECODE_2024` | Always — there is no 2024 analogue of the 2025 `b) Presumed high-impact, but determined not high impact` middle tier. |
| `purpose_benefits` | `expected_benefits` | none (field split) | Yes — one 2024 field carries both problem + benefits; M-25-21 splits it into `problem_statement` + `expected_benefits`. Only the benefits half is mapped. |
| `date_implemented` | `operational_date` | none (semantic drift) | Yes — 2025 `operational_date` conflates pilot-start and full-deployment dates; 2024 keeps them separate. |

`IMPACT_TYPE_RECODE_2024`: `Rights-Impacting` / `Safety-Impacting` / `Both` →
`a) High-impact`; `Neither` → `c) Not high-impact`. Every entry carries
`lossy: True`.

`DEV_STAGE_RECODE_2024`: `Initiated` → `a) Pre-deployment`;
`Acquisition and/or Development` → `a) Pre-deployment` (lossy);
`Implementation and Assessment` → `b) Pilot` (lossy);
`Operation and Maintenance` → `c) Deployed`; `Retired` → `d) Retired`.

## 2025-only columns (no 2024 source)

For a complete two-way picture, these M-25-21 `use_cases` columns have **no
2024 equivalent** — they cannot be back-filled from the 2024 corpus and any
2024-vs-2025 comparison must treat them as 2025-only:

| 2025 DB column | Why it has no 2024 source |
|---|---|
| `ai_classification` | The AI-type taxonomy (Agentic AI, Classical/Predictive ML, Computer Vision, Generative AI, NLP, Reinforcement Learning) **did not exist** in the 2024 form. This is the single biggest "cannot compare" gap — AI type cannot be compared year over year. |
| `is_withheld` | M-25-21 added the public-reporting-withholding question; 2024 had no per-row withholding field. |
| `justification` (`HI_justification`) | Tied to the M-25-21 `b) Presumed high-impact...` tier, which has no 2024 analogue. |
| `problem_statement` | M-25-21 split 2024's combined `purpose_benefits` into `problem_statement` + `expected_benefits`; the problem half has no standalone 2024 column. |
| `link_to_data` | M-25-21 added the optional Federal Data Catalog link; 2024 had no equivalent optional link field. |
| `pia_url` | M-25-21 added the optional Privacy Impact Assessment link; 2024 captured only the SAOP-review Yes/No (`saop_review`), not a link. |
| `hi_training_established` | M-25-21 governance column (operator training); 2024 had no operator-training question. |
| `hi_failsafe_presence` | M-25-21 governance column (fail-safe presence); 2024's nearest neighbors (`opt_out`, `appeal_process`) are different concepts. |

The restructured `hi_*` governance block is **partly** sourced from 2024: five
`hi_*` columns map cleanly from 2024 (`hi_assessment_completed`,
`hi_testing_conducted`, `hi_potential_impacts`, `hi_independent_review`,
`hi_ongoing_monitoring`, `hi_appeal_process`, `hi_public_consultation` — see the
`directly_comparable` rows above), but `hi_training_established` and
`hi_failsafe_presence` are genuinely 2025-only.

## Honest-comparison takeaways

- **21 of 62** 2024 columns are directly comparable — name, agency, bureau,
  topic area, outputs, contracting method, PII, training data, demographic
  features, custom code, ATO, and most of the high-impact governance block.
- **Impact tier is not comparable.** 2024's rights/safety/both/neither ≠ 2025's
  high-impact tiers; treat any impact comparison as lossy and flag it.
- **AI type is not comparable.** 2024 has no `ai_classification` column.
- **Counting methodology changed.** 2025 split COTS into a separate Appendix B
  inventory; 2024 (`commercial_ai`) folded COTS self-ID into the main form. The
  naive total-count delta is not apples-to-apples.
- **The agency-readiness block is gone.** Seven M-24-10 infrastructure/readiness
  questions have no M-25-21 home — that whole analytical lens is 2024-only.
