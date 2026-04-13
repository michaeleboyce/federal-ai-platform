# Check
`id_traceability`

# Method
Reviewed `use_cases.use_case_id` and `consolidated_use_cases` in `federal_ai_inventory_2025.db`, then compared the normalized columns to the preserved `raw_json` payloads. For canonical rows, I checked whether the source ID field was populated in the loaded column and whether the raw payload still carried an ID key/value when the normalized field was blank.

# Findings
The canonical `use_cases` table is the only place where source identifiers should be traceable. It has 3,616 rows total; 1,049 rows have a populated `use_case_id` and 2,567 are blank. Of the blank rows, 2,007 still contain an ID in `raw_json`, so the identifier was present in the source payload but dropped during normalization. The remaining 560 rows have no ID field in `raw_json` either, so those source files did not provide a usable identifier to preserve.

`consolidated_use_cases` is different: it has no `use_case_id` column, and none of its 192 `raw_json` payloads contain an ID-like key. Traceability at the source-ID level is not available there by design, so it should not be treated the same as canonical inventory rows.

The dropped-ID cases are concentrated in a specific set of canonical source files. Largest losses are `NASA-2025-ai-inventory.csv` (425), `DOE-2025-ai-inventory.xlsx` (340), `DOJ-2025-ai-inventory.xlsx` (314), `DOI-2025-ai-inventory.csv` (246), and `DHS-2025-ai-inventory.csv` (238). Additional affected files include `ED-2025-ai-inventory.xlsx` (77), `SEC-2025-ai-inventory.csv` (60), `State-2025-ai-inventory.csv` (60), `FDIC-2025-ai-inventory.csv` (50), `DOL-2025-ai-inventory.csv` (41), `SBA-2025-ai-inventory.xlsx` (34), `SSA-2025-ai-inventory.csv` (33), `EPA-2025-ai-inventory.csv` (29), `FHFA-2025-ai-inventory.csv` (16), `NARA-2025-ai-inventory.csv` (14), `HUD-2025-ai-inventory.xlsx` (11), `FERC-2025-ai-inventory.xlsx` (6), `FRTIB-2025-ai-inventory.csv` (6), `NRC-2025-ai-inventory.csv` (4), and `NCUA-2025-ai-inventory.csv` (3).

The rows with no source ID at all are limited to `HHS-2025-ai-inventory.csv` (447), `TVA-2025-ai-inventory.csv` (59), `GSA-2025-ai-inventory.csv` (49), and `OPM-2025-ai-inventory.csv` (5). Those blanks appear to reflect missing source identifiers rather than a normalization loss.

# Examples
- Preserved in normalized form: `7402` / `CFTC-2025-ai-inventory.csv` / `Anomaly Detection for Data Quality` with `use_case_id = CFTC-001`.
- Preserved in normalized form despite a different raw header: `9115` / `GPO-2025-ai-inventory.csv` / `Audio Transcription` with `use_case_id = 1`.
- Dropped during normalization: `7405` / `DHS-2025-ai-inventory.csv` / `Smartphone Information Forensics Triage` has `raw_json` ID `DHS-2705` but blank `use_case_id`.
- No source ID in raw payload: `9174` / `HHS-2025-ai-inventory.csv` / `Design Your Facility` has a blank `use_case_id` and no ID key in `raw_json`.

# Recommended follow-up
Fix the canonical ingest to map all source ID header variants into `use_cases.use_case_id`, then backfill the 2,007 dropped rows from `raw_json` and re-run a traceability check. Separate the four no-ID source files from true normalization losses so future audits can distinguish missing source data from extractor failures.
