# Check
`field_fullness_and_tag_coarseness`

# Method
Counted null/blank/default values in `use_cases`, `consolidated_use_cases`, and `use_case_tags` from `federal_ai_inventory_2025.db`, then grouped by `source_file` to find where blanks and coarse defaults concentrate. Pulled representative rows where `product_capability` is absent, `architecture_type` falls back to `unknown`, and product linkage is missing despite vendor/system naming.

# Findings
- `use_cases.product_capability` is effectively unused: 3,615/3,616 rows are blank. The only populated canonical row is `ED-2025-ai-inventory.xlsx` `8932` (`Generative AI - Image Generation`), which is tagged `image_generation` and linked to `product_id = 34`.
- `use_cases.architecture_type` is mostly a default bucket, not a discriminating tag: 2,113/3,616 rows are `unknown` (58.5%). High-volume files with especially weak architecture signal include `NASA-2025-ai-inventory.csv` (330/425 unknown), `DOC-2025-ai-inventory.xlsx` (175/223), `VA-2025-ai-inventory.csv` (275/367), `HHS-2025-ai-inventory.csv` (255/447), and `FRB-2025-ai-inventory.csv` (31/38).
- Product linkage is thin in the canonical table. Only 473/3,616 `use_cases` rows have `product_id`, and among the 1,313 rows that name a vendor or system, only 332 link to a product record. The weakest large sources are `NASA-2025-ai-inventory.csv` (3/32 named rows linked), `DOJ-2025-ai-inventory.xlsx` (19/188), `Treasury-2025-ai-inventory.csv` (14/129), `DHS-2025-ai-inventory.csv` (14/110), and `HHS-2025-ai-inventory.csv` (52/218).
- `consolidated_use_cases` is better populated but still coarse enough to limit analysis. `product_capability` is blank on 47/192 rows (24.5%), `architecture_type` is `unknown` on 70/192 (36.5%), and `deployment_scope` is `unknown` on 66/192 (34.4%). `deployment_environment` is almost entirely `unknown` across the inventory, with only 5 `azure_gov` exceptions.
- The `product_capability` vocabulary in consolidated rows is narrow: 23 distinct nonblank values across 145 populated rows. `writing`, `search`, and `meetings` alone make up 52.4% of populated values, and the top five labels account for 66.2%. That is too coarse for comparing diverse use cases across agencies.
- Source-level defaulting is widespread. 35 canonical source files have `product_capability` blank on every row, so the field does not provide a stable cross-file signal in the main table. Several of those same files also default to `custom_system` plus `unknown` architecture, which collapses materially different systems into the same tag pattern.

# Examples
- `ED-2025-ai-inventory.xlsx` `8932` (`Generative AI - Image Generation`) is the only canonical row with a populated `product_capability`: `image_generation`, `architecture_type = inference_only`, `product_id = 34`.
- `HHS-2025-ai-inventory.csv` `9174` (`Design Your Facility`) has no vendor/system/product linkage, blank `product_capability`, and `architecture_type = unknown`.
- `NASA-2025-ai-inventory.csv` `9646` (`Anomaly Detection and Precursor Identification in UAV flight data`) shows the same pattern: blank capability, unknown architecture, and no product link.
- `DHS-2025-ai-inventory.csv` `7408` (`AI Resume & ATS App`) is product-backed (`product_id = 3`) but still has blank `product_capability`, which shows the field is not capturing product-level function even when linkage exists.
- `DOL-2025-ai-inventory-consolidated.csv` `407` (`Scheduling and managing social media posts using AI.`) is a generic-use row with blank `product_capability`, `architecture_type = unknown`, and no commercial product or license signal.

# Recommended follow-up
- Treat `product_capability` as incomplete in the canonical table unless a source explicitly supplies it; backfill it where possible or stop treating blank as meaningful.
- Tighten canonical product-linking for rows that mention a vendor or system, especially in `NASA`, `DOJ`, `DHS`, `Treasury`, `HHS`, and `DOE`.
- Replace `unknown` architecture only when the source supports a more specific label; otherwise keep uncertainty explicit rather than collapsing it into a default bucket.
- For consolidated rows, require a more specific capability taxonomy than `writing/search/meetings` when the goal is cross-agency analysis.
