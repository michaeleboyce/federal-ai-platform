# Source
FDIC-2025-ai-inventory.csv (Federal Deposit Insurance Corporation), reviewed against `use_cases` in `federal_ai_inventory_2025.db`.

# Counts
- Source rows: 50
- Loaded DB rows: 50
- Row count matches exactly; no obvious drop/duplication at the table level.
- All 50 loaded rows have blank `use_case_id` in the DB, so the source identifier was not preserved for traceability.

# Findings
- Parsing appears broadly intact for the main fields, but the DB loses the source case ID entirely. In the raw CSV, rows are keyed like `FDIC - 25` / `FDIC-22` / `FDIC – 3`; in the DB, `use_case_id` is blank for every loaded row, which makes row-to-source reconciliation harder than it should be.
- Tagging is directionally right for some rows, but several are too generic or slightly off on AI type.
  - `FDIC Deposit Insurance Misrepresentation` is reasonably tagged as `product_deployment`, but the source explicitly says the system uses natural language processing and references `Meltwater`; the DB’s `ai_sophistication=nlp_specific` and `is_cots_commercial=1` look right, but the product label is too sparse for audit use because it only stores `Meltwater` and not the broader source context.
  - `Plain Language Policy Assistant`, `Knowledge Article Generation`, and `Generative Artificial Intelligence (AI) for Legal Research` are all tagged `general_llm`/`rag_pipeline`, which is plausible from the names and narrative text, but the labels are still quite high-level compared with the source descriptions. They should be treated as inferred, not asserted facts.
  - `AI Assisted Data Collection` is tagged `computer_vision` and `custom_trained`, which matches the source text about extracting structured data from bank PDF documents and the use of `Microsoft Power Apps`.
- The retired rows look systematically under-described in the DB. Many have only `stage_of_development` populated and no AI classification or vendor/system fields, even when the source row contains meaningful descriptive text. That may be acceptable for retired cases, but it reduces the auditability of those records.

# Recommended follow-up
- Preserve the source case identifier in `use_case_id` or an equivalent field for all rows.
- Spot-check the tagger on the vendor-backed and generative-AI rows, especially `FDIC-22` and `FDIC - 25`, to ensure the product and AI-sophistication labels are not being flattened too aggressively.
- If retired rows are intentionally sparse, document that convention; otherwise, backfill the obvious source text into the DB so reviews can cite stronger evidence.
