# Source
- `DHS-2025-ai-inventory.csv` for `Department of Homeland Security`
- Raw CSV has 243 rows total: 1 header row, 238 data rows, and 3 trailing blank rows.
- Loaded DB row count matches the usable source row count: 238 rows.

# Counts
- Source usable rows: 238
- Loaded DB rows: 238
- Parsed rows with blank `use_case_id` in DB: 238/238

# Findings
- Row count is consistent, but the primary source identifier was not preserved. The raw CSV first column contains IDs like `DHS-2705`, `DHS-313`, and `DHS-314`, but every loaded `use_case_id` is null. That makes row-level reconciliation back to the source harder than it should be.
- Most tags are directionally plausible for DHS, especially the high-volume `custom_system` / `general_llm` / `administrative` patterns.
- A few tag assignments look off enough to flag. `Commercial Generative AI for Text Generation (AI Chatbot)`, `Commercial Generative AI for Image Generation`, and `Commercial Generative AI for Code Generation` are all tagged `custom_system`, but the source names describe commercial AI products rather than custom in-house systems. These look more like `product_deployment` entries.
- `Synthetic data for improved Automated Threat Recognition (ATR) in checkpoint screening` is tagged `general_llm`, but the source itself reads like a computer-vision / synthetic-data screening use case, not a general LLM workflow. That tag seems directionally weak.

# Recommended follow-up
- Restore or populate `use_case_id` from the source CSV first column so the loaded rows can be traced back cleanly.
- Recheck the three `Commercial Generative AI...` rows and decide whether they should be `product_deployment` instead of `custom_system`.
- Recheck the ATR synthetic-data row and any similar screening/vision use cases that may have been swept into `general_llm` by pattern matching.
