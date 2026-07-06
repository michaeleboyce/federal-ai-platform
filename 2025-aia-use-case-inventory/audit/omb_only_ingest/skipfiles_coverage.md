# SKIP_FILES supersession audit — 7 files

Scope: `CSOSA-2025-ai-inventory.csv`, `DOL-2025-ai-inventory-consolidated.csv`,
`FDIC-2025-ai-inventory-consolidated.csv`, `HUD-2025-ai-inventory-consolidated.xlsx`,
`NLRB-2025-ai-inventory.csv`, `USITC-2025-ai-inventory.csv`, `USTDA-2025-ai-inventory.xlsx`
(all `data/raw/`). `load_inventories.py` skips these on the assumption that
`cots-2025-ai-inventory-consolidated.xlsx` carries their rows into
`consolidated_use_cases`. Method: parsed each file directly (csv/openpyxl,
read-only), pulled each agency's `consolidated_use_cases` and `use_cases` rows
from `data/federal_ai_inventory_2025.db` (read-only), matched every file row to
a DB row by normalized AI-use-case label (+ Agency-Use Y/N where the file has
that column), and checked `omb_match_audit` for `omb_only` rows.

**Overall verdict: SUPERSESSION HOLDS for 6 of 7 files. DOL has one dropped
row.**

| Agency | File | Style | File rows | DB consolidated rows | DB use_cases rows | omb_only in omb_match_audit | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| CSOSA | CSOSA-2025-ai-inventory.csv | COTS-grid, full 20-item, has Y/N | 20 | 20 | 0 | 0 | SUPERSESSION HOLDS |
| DOL | DOL-2025-ai-inventory-consolidated.csv | Thin 2-col recap (Commercial Examples, AI Use Case), no Y/N/product-usage columns | 14 | 20 | 41 | 0 | **DROPPED ROW** (1 of 14) |
| FDIC | FDIC-2025-ai-inventory-consolidated.csv | COTS-grid, full 20-item, has Y/N | 20 | 20 | 50 | 0 | SUPERSESSION HOLDS |
| HUD | HUD-2025-ai-inventory-consolidated.xlsx | COTS-grid, full 20-item, has Y/N | 20 | 20 | 11 | 0 | SUPERSESSION HOLDS (1 value-level Y/N drift noted, not a drop) |
| NLRB | NLRB-2025-ai-inventory.csv | COTS-grid, pre-filtered to used items only, no Y/N column | 7 | 20 | 0 | 0 | SUPERSESSION HOLDS |
| USITC | USITC-2025-ai-inventory.csv | COTS-grid, pre-filtered to Y-only rows, has Y/N column (all "Y") | 11 | 20 | 0 | 0 | SUPERSESSION HOLDS |
| USTDA | USTDA-2025-ai-inventory.xlsx | COTS-grid, full 20-item, has Y/N | 20 | 20 | 0 | 0 | SUPERSESSION HOLDS |

None of the 7 agencies has any `omb_only` row in `omb_match_audit`. Where the
agency also filed an M-25-21 narrative file (DOL, FDIC, HUD — loaded, not
skipped), their `use_cases` counts (41 / 50 / 11) match `matched_exact` counts
in `omb_match_audit` exactly, confirming those individually-reported rows are
fully reconciled against the OMB consolidated file. CSOSA/NLRB/USITC/USTDA
filed no narrative use cases at all (0 rows, 0 `omb_match_audit` entries) —
consistent with small agencies that only completed the Appendix‑B/COTS grid.

## CSOSA — CSOSA-2025-ai-inventory.csv

- Style: classic 20-row COTS/Appendix‑B checkbox grid. Columns: `AI Use Case,
  Commercial Examples, Agency Use (Y/N)?, Name of Commercial Product or
  Service Used, Estimated # of Licenses/Users`.
- 20 data rows, all 20 template use-case labels present.
- DB: `consolidated_use_cases` has exactly 20 rows for CSOSA, all
  `source_file = cots-2025-ai-inventory-consolidated.xlsx`. `use_cases` = 0
  (CSOSA filed no narrative use cases).
- Row-by-row match on normalized label + Y/N: **0 misses / 20 file rows.**
  Products and license bands (e.g. "Microsoft M365 Copilot AI", 1001-5000)
  match verbatim between file and DB.
- **Verdict: SUPERSESSION HOLDS.**

## DOL — DOL-2025-ai-inventory-consolidated.csv

- Style: **not** the standard grid. Only two columns: `Commercial Examples,
  AI Use Case` — no Y/N column, no "product actually used" column, no
  license-count column. 14 data rows.
- Rows 1–12 restate 12 of the 20 template use-case labels, each paired with
  a "Commercial Examples" value. Cross-checked: these 12 labels are exactly
  the 12 rows DOL marked `agency_uses = Y` in the COTS aggregate, and the
  "Commercial Examples" text in this file matches DOL's actual
  `commercial_product` value in `consolidated_use_cases` verbatim (e.g.
  "Generating first drafts…" → "ChatGPT, Gemini, Claude" in both). These 12
  are fully superseded.
- Rows 13–14 are **not** part of the standard 20-item template — they are
  DOL-specific free-text AI use cases:
  - Row 13: "Using AI-enabled augmented reality to train inspectors to
    visually assess unsafe environments from a safe location…" / Hololens.
    **Covered elsewhere**: found in `use_cases` id 197324, `use_case_name =
    "Hololens"`, `use_case_id = DOL-08`, loaded from
    `DOL-2025-ai-inventory.csv` (the narrative file, which is NOT skipped).
    Not a drop.
  - Row 14: **"Answering federal regulatory and agency policy questions
    related to acquisition using a generative AI tool." / "Prism Ally"**.
    Searched `use_cases` (all agencies, by name/system/vendor) and
    `consolidated_use_cases` for DOL: no match. There IS a `use_cases` row
    named "PRISM Ally" (id 197722, vendor "Unison"), but it is filed under
    **HHS**, not DOL, from `HHS-2025-ai-inventory.csv` — a different
    agency's use of the same commercial product, not DOL's. DOL's own
    reported use of PRISM Ally for acquisition/regulatory Q&A has no
    counterpart anywhere in the DB.
- **Verdict: DROPPED ROW.** `"Answering federal regulatory and agency policy
  questions related to acquisition using a generative AI tool."` (product:
  Prism Ally, vendor Unison) — DOL's own reported use case — is silently
  lost by skipping `DOL-2025-ai-inventory-consolidated.csv` on the
  assumption the COTS aggregate covers it. It doesn't; the COTS aggregate
  only carries the fixed 20-item template, and this is an agency-supplied
  addendum item outside that template.

## FDIC — FDIC-2025-ai-inventory-consolidated.csv

- Style: full 20-row COTS grid with Y/N, product, and license columns.
- DB: 20 `consolidated_use_cases` rows for FDIC (`source_file = cots-…xlsx`).
  `use_cases` = 50 (from the separate, loaded `FDIC-2025-ai-inventory.csv`
  narrative file).
- Row-by-row match: **0 misses / 20 file rows.** All Y/N flags and product
  strings match the DB rows exactly, including edge cases like "Using
  AI-assisted tools in word processors." (Y, blank product) and "Identifying
  and cataloging items in a storage room…" (Y, blank product).
- **Verdict: SUPERSESSION HOLDS.**

## HUD — HUD-2025-ai-inventory-consolidated.xlsx

- Style: full 20-row COTS grid (Sheet1, `A1:E21`), Y/N + product + license
  columns.
- DB: 20 `consolidated_use_cases` rows for HUD. `use_cases` = 11 (from
  `HUD-2025-ai-inventory.xlsx`, the separate narrative file — note per
  `load_inventories.py` comment, HUD has no CSV narrative version, only the
  xlsx, and that xlsx is loaded, not skipped).
- Row-by-row match: **19 of 20 clean; 1 value-level discrepancy (not a
  drop):** "Unlocking smartphones or other devices without the need for
  passwords or PINs using AI-based facial recognition technology." — the
  skipped file has `Agency Use (Y/N)? = N` (with, inconsistently, a product
  name "Apple iPhone" and license band "1001-5000" filled in anyway), while
  the COTS aggregate in the DB has `agency_uses = Y` for the same row/same
  product. The use case's existence and product are captured either way;
  only the Y/N flag differs between the two source files (the aggregate's
  Y is very plausibly the corrected value, given the file's own N+populated-product
  contradiction). This is a data-quality note, not a coverage gap.
- **Verdict: SUPERSESSION HOLDS** (with the Y/N drift noted above).

## NLRB — NLRB-2025-ai-inventory.csv

- Style: COTS-grid, but pre-filtered by the agency to only the rows it uses
  — no `Agency Use (Y/N)?` column at all. Columns: `AI Use Case, Name of
  Commercial Product or Service Used, Estimated # of Licenses/Users`. 7 data
  rows.
- DB: 20 `consolidated_use_cases` rows for NLRB (all from COTS aggregate,
  the standard 20-item Y/N grid). `use_cases` = 0.
- All 7 file rows correspond, label-for-label and product-for-product, to
  the 7 rows the COTS aggregate marks `agency_uses = Y` for NLRB (e.g.
  "Generating code using AI." → "GitHub CoPilot" in both; "Managing and
  prioritizing internal service or help desk tickets using AI." → "CoPilot,
  ServiceNow" in both). **0 misses / 7 file rows.**
- **Verdict: SUPERSESSION HOLDS.**

## USITC — USITC-2025-ai-inventory.csv

- Style: COTS-grid subset — has an `Agency Use (Y/N)?` column but only rows
  marked "Y" were included (no N rows present). Columns: `AI Use Case,
  Agency Use (Y/N)?, Name of Commercial Product or Service Used, Estimated #
  of Licenses/Users`. 11 data rows (all "Y").
- DB: 20 `consolidated_use_cases` rows for USITC (COTS aggregate). `use_cases`
  = 0. The COTS aggregate actually carries **12** Y rows for USITC — one
  more than the skipped file ("Editing images, videos, or other public
  affairs materials using AI." / M365 Copilot / Y appears in the DB but not
  in this file). That is the DB having *more* than the file, not less — no
  data is lost by skipping the file.
- All 11 file rows matched: **0 misses / 11 file rows.**
- **Verdict: SUPERSESSION HOLDS.**

## USTDA — USTDA-2025-ai-inventory.xlsx

- Style: full 20-row COTS grid (Sheet1, `A1:E21`), Y/N + product + license
  columns.
- DB: 20 `consolidated_use_cases` rows for USTDA. `use_cases` = 0.
- Row-by-row match: **0 misses / 20 file rows.** The 3 "Y" rows (word
  processors/Microsoft Copilot, security controls/Crowdstrike+Qualys,
  unlocking smartphones/Apple iPhone+Lookout) match the DB exactly.
- **Verdict: SUPERSESSION HOLDS.**

## Action needed

Only DOL requires a fix. `DOL-2025-ai-inventory-consolidated.csv` is not a
pure duplicate of the COTS aggregate — it contains one genuinely
agency-specific use case ("Answering federal regulatory and agency policy
questions related to acquisition using a generative AI tool.", product
"Prism Ally") that exists nowhere else in the DB for DOL. Recommend either:
(a) hand-adding this one row to `use_cases` or `consolidated_use_cases` for
DOL via a small backfill script (re-resolving DOL's `agency_id` at write
time per this repo's stale-ID rules), or (b) narrowing the SKIP_FILES
rationale/comment for this file to note the one exception and load it
through a path that only ingests the non-template rows. The other 12 rows in
that file are true duplicates of the COTS aggregate's DOL "Y" rows and
should stay skipped as-is.
