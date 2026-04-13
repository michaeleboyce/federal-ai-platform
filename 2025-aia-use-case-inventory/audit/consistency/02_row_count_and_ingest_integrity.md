# row_count_and_ingest_integrity

## Check
Compare raw non-empty source rows to loaded database rows, while separating harmless title/header/trailing-blank artifacts from real ingest loss or duplication.

## Method
Used `audit/manifest.json` and `audit/source_summary.csv` to locate count deltas, then inspected the affected raw CSV rows and the SQLite `use_cases` table in `data/federal_ai_inventory_2025.db`.

## Findings
- Only 2 of 47 source files show a raw-vs-DB count delta.
- No file shows duplication in the load (`db_rows` never exceeds the source count).
- `DHS-2025-ai-inventory.csv`: 239 raw non-empty source rows vs 238 loaded rows. The gap is explained by one trailing malformed row outside the substantive data block, not a missing use case.
- `DOI-2025-ai-inventory.csv`: 247 raw non-empty source rows vs 246 loaded rows. The skipped record is `DOI-0015` at source row 237; it has a blank use case name but is otherwise populated, so this is the only likely substantive omission in the audit.
- Net impact: 1 skipped malformed/incomplete record in DOI (~0.4% of DOI source rows); no substantive row loss in DHS.

## Examples
- `DHS-2025-ai-inventory.csv`, row 243: almost entirely blank, with only a stray backtick in one cell. This looks like trailing junk after the real data block.
- `DOI-2025-ai-inventory.csv`, row 237 (`DOI-0015`): blank use case name, but populated bureau (`FWS`), email, stage, classification, problem statement, benefits, and operational date. This is the row the ingest appears to have dropped.

## Recommended follow-up
- Backfill or explicitly document `DOI-0015` if the blank title is accidental.
- No ingest correction appears necessary for DHS; the extra row is a cleanup issue in the source extract, not a data-loss issue.
