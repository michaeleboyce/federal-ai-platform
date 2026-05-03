---
name: omb-ai-use-case-inventory
description: Use when interpreting the OMB-defined AI use case inventory schema — when reading agency-filed CSV/Excel headers, mapping a column the agency labeled differently to its canonical name, decoding multiple-choice values (with all the casing/punctuation variants seen in the wild), checking which fields are required for which deployment stage, writing or auditing tagging logic that derives from the inventory, or planning a backfill against the source columns. Triggered by: any task that touches `data/raw/<AGENCY>-2025-ai-inventory.{csv,xlsx}`, the `use_cases` table, the `consolidated_use_cases` table, or scripts under `auto_tag.py` / `load_inventories.py` / `scripts/retag_*.py` / `scripts/backfill_*.py`.
---

# OMB AI Use Case Inventory — Schema Reference

The 2025 federal AI use case inventory is defined by **OMB Memorandum M-25-21**, Appendix. Every CFO-Act agency files an inventory with the same 36 columns. This skill documents what each column means, the canonical valid values, and the messy-data variants that show up in practice.

This skill is a **reference**, not a runbook. Read it when you need to know what a column means, what values it accepts, or how to interpret a non-standard value an agency filed.

## When to use this skill

- You're interpreting an OMB-filed inventory column and want to know its semantics, valid values, or what the recoded shorthand means.
- You're writing a backfill or audit script that touches the source columns (e.g., `auto_tag.py`'s field reads, `load_inventories.py`'s mapping).
- You see a value that doesn't match the canonical valid selections and need to know whether it's a known recoding alias or genuinely unmapped.
- You're trying to figure out whether a missing value is a real omission or just a "not required for this stage" omission.
- You're explaining the schema to a teammate or in a doc.

## The high-level shape

The inventory has **36 columns** organized into 5 conceptual sections:

1. **Identifiers** (cols 1–4): id, name, bureau, contact email
2. **Filing posture** (cols 5–7): is_withheld, development_stage, is_high_impact + justification
3. **What the AI does** (cols 8–13): topic_area, classification, problem_solved, benefits, system_outputs, operational_date
4. **How it was built** (cols 14–24): contracting_usage, vendor_name, ATO, data_description, data link, has_pii, PIA, demographic_features, has_custom_code, code_url
5. **High-impact governance** (cols 25–33): pre-deployment testing, AI impact assessment, potential impacts, independent review, ongoing monitoring, operator training, fail-safe, appeal process, public consultation

Plus two columns OMB **adds during consolidation** (not filed by agencies):
- `agency` — the abbreviation (e.g., USDA)
- `agency_name` — the full name (e.g., Department of Agriculture)

## Required-when conditionals (this trips people up)

Columns are only mandatory for use cases past a particular development stage:

| Required when | Columns |
|---|---|
| **Always** | id, use_case_name, agency_bureau, contact_email, is_withheld, development_stage, is_high_impact |
| **Pre-deployment, pilot, deployed** (i.e., not retired) | topic_area, classification, problem_solved, benefits, system_outputs |
| **Pilot or deployed only** | operational_date, contracting_usage, vendor_name (if vendor used), have_ato, system_name_ato (if ATO yes), data_description, has_pii, demographic_features, has_custom_code |
| **High-impact deployed only** | the 9 `hi_*` governance columns |
| **Conditional** | `HI_justification` only when `is_high_impact == "Presumed high-impact, but determined not high impact"` |
| **Optional** | link_to_data, pia_url, code_url |

So an absent value doesn't always indicate non-compliance — check the `development_stage` and `is_high_impact` first.

## The seven `multiple_choice` columns and their canonical values

Use the exact canonical text below when filtering or rendering. The DB stores the canonical form (with the leading "a)", "b)" letters when applicable). Agencies frequently file variant phrasings — see `reference/recoding_maps.md` for the full alias-to-canonical mapping.

- **`is_withheld`** — `a) No` / `b) Yes – ... FOIA exemption` / `c) Yes – disclosure is prohibited by law` / `d) Other`
- **`development_stage`** — `a) Pre-deployment` / `b) Pilot` / `c) Deployed` / `d) Retired`
- **`is_high_impact`** — `a) High-impact` / `b) Presumed high-impact, but determined not high impact` / `c) Not high-impact`
- **`topic_area`** — 15 valid values; see reference. Common alias collapse: many agency-specific topics ("Internal Knowledge Management", "Software Development", "Communications & Public Affairs") fold into the OMB canonical buckets ("Administrative Functions", "Information Technology", "Service Delivery").
- **`classification`** — 6 AI types: Agentic AI, Classical/Predictive ML, Computer Vision, Generative AI, NLP, Reinforcement Learning. Each canonical value is the full sentence (e.g., `"Agentic AI: AI systems that perform tasks or make decisions autonomously with minimal human intervention."`). Agencies often file just the short name; treat as alias.
- **`contracting_usage`** — `a) Purchased from a vendor` / `b) Developed in-house` / `c) Developed with both contracting and in-house resources`
- **`have_ato`**, **`has_pii`**, **`has_custom_code`** — `Yes` / `No`. Common alias: `true`/`false`, `yes`/`no` lowercased.

## The two `select_multiple` columns

Stored as **stringified Python lists** in the consolidated CSV (e.g., `['a) Race/Ethnicity', 'c) Age']`). Use `ast.literal_eval` or split-and-strip to parse. Both columns:

- **`demographic_features`** — 12 valid values (Race/Ethnicity, Sex, Age, Religious Affiliation, Socioeconomic Status, Ability Status, Residency Status, Marital Status, Income, Employment Status, None of the above, Other). The "None of the above" option is `k) None of the above`, NOT empty.
- **`hi_public_consultation`** — 6 valid values (Direct usability testing, Public solicitations, Public hearings, Other, In-progress, CAIO Waived).

## The nine high-impact governance columns

All 9 only required when **`is_high_impact == "a) High-impact"` AND `development_stage == "c) Deployed"`**. Each has a "CAIO Waived" option meaning "the agency CAIO has formally waived this practice and reported the waiver to OMB." Treat waivers as a real signal — they're public and accountability-bearing.

The 9: `hi_testing_conducted`, `hi_assessment_completed`, `hi_potential_impacts` (free text), `hi_independent_review`, `hi_ongoing_monitoring`, `hi_training_established`, `hi_failsafe_presence`, `hi_appeal_process`, `hi_public_consultation`. Each has a 3-to-5-option choice list — see reference for full enumerations.

## Data normalization conventions OMB applies during consolidation

When OMB consolidates agency filings into the public inventory:

1. **Encoding:** UTF-8-SIG (BOM included) for Excel compatibility with em-dashes and the curly quotes that show up in canonical values.
2. **Whitespace:** Leading/trailing whitespace stripped. Internal whitespace preserved (so `"Yes,  with double space"` is left alone).
3. **Recoding maps:** Multiple-choice columns get fuzzy-matched. Examples: `false → No`, `none → None of the above`, `Pre-deployment - The use case... → a) Pre-deployment - The use case...` (leading-letter restored).
4. **List serialization:** Select-multiple columns reformatted to use **alphabetical order** with **semicolon separators** when the agency filed comma-separated. The consolidated CSV uses Python list repr (`['Value 1', 'Value 2']`); the DB-loaded form may flatten to a delimited string.
5. **No silent value invention:** if a value can't be matched to any canonical option via the recoding map, OMB leaves it as filed (with whitespace stripped). Some agencies file unique values per column — these end up as outliers.

## Where the messy data hides (real cases from the 2025 inventory)

- **Curly vs straight apostrophes** in the canonical strings: `agency's` (curly) vs `agency's` (straight). Encoding: UTF-8 vs cp1252 collisions cause `ñ` to appear where `–` (em dash) should be. Watch for `agencyís` / `Pre-deployment ñ`.
- **Letter prefixes vary:** `a) Pre-deployment`, `a)  Pre-deployment` (double space), `a)Pre-deployment` (no space). The recoding map handles all three.
- **Free-text in multiple_choice fields:** agencies sometimes paste a paragraph into `is_withheld` instead of selecting. Treat these as "Other" with original-text in notes.
- **Vendor names:** comma- or pipe-separated lists are common. Don't over-split — `"Aneesh Technologies, 24X7, Ellumen Inc., Deloitte"` is a list of contractors, often none of which is the actual product vendor.
- **`bureau_component`:** the messiest column in practice. Forward-slash hierarchy at HHS (`HHS/CDC`, `HHS/FDA/CDER`), parenthetical org codes at DOE (`PNNL - Pacific Northwest National Laboratory (SC43 OIM)`), pipe-delimited multi-bureau at DOL (`OWCP||VETS||WHD`), prefixed at DOJ (`Department of Justice / FBI`). See `scripts/backfill_bureau_orgs.py` for the per-agency parsers we use.

## Where this maps in our codebase

As of migration `m002_rename_to_omb_canonical.py` (April 2026), 15 DB columns
were renamed to match their OMB canonical names. Most rows below are now
identity mappings; the remaining divergences are intentional and flagged.

| OMB column | DB column (`use_cases` table) | Source script |
|---|---|---|
| `id` | `use_case_id` *(intentional divergence — would conflict with primary key `id`; not renamed)* | `load_inventories.py` |
| `use_case_name` | `use_case_name` | same |
| `agency_bureau` | `bureau_component` *(intentional divergence — heavily referenced; deferred)* | same |
| `contact_email` | `email_address` | same |
| `is_withheld` | `is_withheld` | same |
| `development_stage` | `stage_of_development` *(intentional divergence — 49 refs across dashboard CASE-statement normalization + audit docs; deferred)* | same |
| `is_high_impact` | `is_high_impact` | same |
| `HI_justification` | `justification` | same |
| `topic_area` | `topic_area` | same |
| `classification` | `ai_classification` | same |
| `problem_solved` | `problem_statement` | same |
| `benefits` | `expected_benefits` | same |
| `system_outputs` | `system_outputs` | same |
| `operational_date` | `operational_date` | same |
| `contracting_usage` | `development_type` *(intentional divergence — 66 refs; deferred)* | same |
| `vendor_name` | `vendor_name` | same |
| `have_ato` | `has_ato` *(intentional divergence — 33 refs incl. dashboard ATO availability matrix; deferred)* | same |
| `system_name_ato` | `system_name` *(intentional divergence — 82 refs; deferred due to large audit-doc surface area)* | same |
| `data_description` | `training_data_description` *(intentional divergence — 37 refs incl. test fixtures; deferred)* | same |
| `link_to_data` | `link_to_data` | same |
| `has_pii` | `has_pii` | same |
| `pia_url` | `pia_url` | same |
| `demographic_features` | `demographic_features` | same |
| `has_custom_code` | `has_custom_code` | same |
| `code_url` | `code_url` | same |
| `hi_testing_conducted` | `hi_testing_conducted` | same |
| `hi_assessment_completed` | `hi_assessment_completed` | same |
| `hi_potential_impacts` | `hi_potential_impacts` | same |
| `hi_independent_review` | `hi_independent_review` | same |
| `hi_ongoing_monitoring` | `hi_ongoing_monitoring` | same |
| `hi_training_established` | `hi_training_established` | same |
| `hi_failsafe_presence` | `hi_failsafe_presence` | same |
| `hi_appeal_process` | `hi_appeal_process` | same |
| `hi_public_consultation` | `hi_public_consultation` | same |

The DB also adds derived columns not in the source: `agency_id` (FK to `agencies`), `slug`, `id_provenance`, `organization_id`, `bureau_organization_id`, `product_id`, `template_id`, `raw_json` (the original row preserved for audit).

## Dashboard OMB-vs-IFP labeling

The dashboard distinguishes **OMB-filed fields** (data agencies submitted under
M-25-21) from **IFP-derived fields** (analytical tags, evidence backfills,
product hierarchy, computed maturity rollups). Every `Section` rendered by
the dashboard is labeled with a chip indicating the provenance of what the
reader is about to see.

The chip vocabulary is defined on the `Section` component in
`dashboard/components/editorial.tsx` (which also exports the `SourceLegend`
component used in page footers and at the top of the home page). The
`source` prop accepts these four values:

| `source` value | Chip text shown to readers | Meaning |
|---|---|---|
| `"omb"` | `OMB` | Section displays only OMB-filed fields |
| `"derived"` | `IFP` | Section displays only IFP-added fields (tags, evidence, products, hierarchy) |
| `"omb-derived"` | `OMB → IFP` | Counts/rollups whose inputs are OMB but whose computation is IFP |
| `"mixed"` | `OMB + IFP` | Section displays both kinds (use sparingly; prefer per-Row labeling) |

When writing or editing dashboard pages, every `Section` MUST receive a
`source` prop. If a section truly straddles, prefer labeling individual rows
over reaching for `"mixed"` at the section level.

## Reference files

For per-field detail beyond the high-level summary above:

- `reference/columns.md` — full per-field metadata (all 36 columns) with canonical valid values, original Excel headers, full instructions, and recoding tables.
- `reference/recoding_maps.md` — the messy-alias tables (every variant string seen in the wild and the canonical it folds to). Useful when you encounter an unfamiliar value in source data.

These are NOT loaded by default — Read them when you need the detail.

## What this skill is NOT

- It does NOT document our derived analytical tagging (`use_case_tags` table). For that, see `AGENT_TAGGING_GUIDE.md` in the project root.
- It does NOT document the consolidated/Appendix B template (`consolidated_use_cases` table) — that's a different OMB-supplied form and has its own narrower schema.
- It does NOT replace OMB's official memorandum text. When in doubt, the M-25-21 appendix is canonical; this skill is a derived working reference.
