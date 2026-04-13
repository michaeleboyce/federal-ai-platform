# Source
- `CSOSA-2025-ai-inventory.csv`
- Raw source rows: 20
- Loaded `consolidated_use_cases` rows for CSOSA: 20

# Counts
- Row count matches exactly: 20 source rows and 20 DB rows.
- The raw CSV has no blank data rows and the loader preserved all 20 records.
- In the DB, 4 rows have blank `commercial_product` and 4 rows have blank `estimated_licenses_users`, which matches the source pattern.

# Findings
- The main issue is tag linkage. I could not find any CSOSA rows linked in `use_case_tags` for the consolidated table, even though the source context reports every row as tagged. That means the DB does not currently preserve the tagging layer for this file.
- Product mapping is directionally reasonable in the middle of the file, but several rows are lossy or only partially normalized. For example, row 399 collapses `Splunk, Crowdstrike, MS Defender, Qualys. Palo Alto` to `Microsoft Defender`, and row 403 maps cleanly to `SAP Concur` but drops the rest of the source context. That is acceptable only if the intent is canonicalization, not full source preservation.
- A few rows look especially under-specified in the DB because `product_id` and `template_id` are blank even when the source is clearly a product-backed use case. Examples are row 398 (`Google Lens`), row 402 (`Google Maps, Apple Maps`), and row 404 (`Apple iPhone, Google Pixel`). The source meaning is still recoverable, but the loaded records are thinner than the raw file.
- Minor parsing/normalization issue: row 404 is stored as `Apple Iphone` in `commercial_product`, which is a capitalization/spelling drift from the source `Apple iPhone`.

# Recommended follow-up
- Re-run or inspect the tag loader for CSOSA so the consolidated rows are actually linked in `use_case_tags`.
- Verify whether the product canonicalization for rows 399, 402, and 404 is intentionally lossy; if not, preserve the source product string alongside the normalized product.
- Check whether the `Apple Iphone` spelling in row 404 should be normalized to `Apple iPhone`.
