# `topic_area` normalization — cleanup pass (Slice B)

Normalizes `use_cases.topic_area` values that were stored verbatim from
agency M-25-21 inventories. Source data exhibited cosmetic drift (mixed
case, en-/em-dashes, double spaces, blank-string vs. NULL) that
inflated the distinct-value count without representing real semantic
distinctions.

Implementation:

- `auto_tag.normalize_topic_area(raw) -> str | None` — pure helper.
- `load_inventories.py` (~line 358) — applied at ingest, before
  INSERT into `use_cases`.
- `scripts/normalize_topic_areas_inplace.py` — one-shot in-place
  migration for the live DB. Idempotent; running twice is a no-op.

## Merge rules (deliberately conservative)

1. `None` or blank-after-trim ⇒ `None`. (Empty string is not a meaningful
   distinct value separate from NULL.)
2. En-dash (`–` U+2013) and em-dash (`—` U+2014) ⇒ ASCII hyphen `-`.
3. Collapse runs of internal whitespace (incl. NBSP) to a single ASCII
   space; trim outer whitespace.
4. Case-only duplicates collapse to the titlecased canonical:
   - `"Administrative functions"` ⇒ `"Administrative Functions"`.
5. **Not merged** (genuinely distinct values, do NOT widen):
   - `"Cybersecurity"` vs `"Cybersecurity Operations"`.
   - `"Information Technology"` vs `"IT Operations & Infrastructure Management"`.
   - `"Other"`, `"Other (use other text field)"`, and the `"Other - …"`
     specifics.

The case-canonical map lives in `auto_tag._TOPIC_AREA_CASE_CANONICAL`.
Add a row only when an agency demonstrably files the same canonical
phrase in a different casing.

## Distinct-count delta

Distinct `topic_area` values, before vs. after the in-place migration
(`SELECT COUNT(DISTINCT topic_area) FROM use_cases`):

| Stage  | Distinct |
| ------ | -------- |
| Before | **37**   |
| After  | **34**   |

Three buckets collapsed:

1. `''` ⇒ `NULL` (eliminates one distinct value)
2. `'Administrative functions'` ⇒ `'Administrative Functions'`
3. `'Other – Economic & Financial'` and `'Other  – Economic & Financial'`
   (note double space) ⇒ `'Other - Economic & Financial'` (eliminates one
   distinct value relative to the two pre-existing variants — the new
   ASCII-hyphen form did not previously exist in the table).

Total rows updated: **307** (267 blank-to-NULL + 33 + 1 em-dash variants
+ 6 case-fold).

## Per-change row counts (from migration log)

```
'' -> None: 267
'Other – Economic & Financial' -> 'Other - Economic & Financial': 33
'Administrative functions' -> 'Administrative Functions': 6
'Other  – Economic & Financial' -> 'Other - Economic & Financial': 1
```

## Re-running

```bash
python3 scripts/normalize_topic_areas_inplace.py --dry-run   # preview
python3 scripts/normalize_topic_areas_inplace.py             # apply
```

A second invocation reports `Rows updated: 0`.

## Verification snapshot

After-state distribution (counts ≥ 1) confirmed via:

```sql
SELECT topic_area, COUNT(*) FROM use_cases GROUP BY topic_area ORDER BY topic_area;
```

`NULL` row count went from **293** to **560** (gained the 267 ex-blank
rows). `'Administrative Functions'` went from 439 to 445. The new
`'Other - Economic & Financial'` row carries 34 (33 + 1 from the two
em-dash variants).
