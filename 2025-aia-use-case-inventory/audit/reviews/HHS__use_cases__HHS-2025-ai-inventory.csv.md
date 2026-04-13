# Source
- `HHS-2025-ai-inventory.csv` for `Department of Health and Human Services`
- Raw CSV has 447 data rows and 1 header row; no blank trailing rows were present in the source file.
- Loaded DB row count matches the source exactly: 447 `use_cases` rows and 447 `use_case_tags` rows for this file.

# Counts
- Source data rows: 447
- Loaded DB rows: 447
- Tagged DB rows: 447
- Blank loaded `use_case_id` values: 447/447

# Findings
- Cardinality is correct and the CSV parses cleanly at the row level. The raw file has 33 columns, and the loaded DB row count matches the source exactly.
- The main parsing weakness is identifier loss: the source’s first-column identifiers were not preserved into `use_cases.use_case_id`, so every loaded row is harder to reconcile back to the original spreadsheet than it should be.
- Most tags are directionally plausible for HHS. The bulk of the file clusters around `custom_system`, `bureau`, `administrative`, and `rag_pipeline`, which fits the source descriptions for ACF/HHS internal assistants, policy tools, and document-review workflows.
- A few rows look misclassified or at least worth rechecking. `Structuring Notice of Concern Data` is tagged `computer_vision` and `custom_trained`, but the source text says it is using secure commercially available LLMs and explicitly says there is no training or fine-tuning. That looks like an over-fit on the tag side.
- `Qualitative Analysis` is another weak spot: the source describes vendor tools like NVivo, Qualtrics, Credal, and Ask Sage, but the row is tagged `nlp_specific` with `rag_pipeline`. That is directionally less convincing than the surrounding HHS rows that clearly describe RAG-style LLM assistants.
- `Builder Buddy` is tagged `agentic_workflow`, which matches the source better than most of the row set, but the source also says `No` custom-developed code and `Credal` as the vendor/system. It reads more like a vendor product deployment than a custom system, so the `custom_system` entry type deserves a spot check.

# Recommended follow-up
- Backfill or preserve the source’s first-column identifier in `use_cases.use_case_id` so row-level traceability is not lost.
- Recheck `Structuring Notice of Concern Data` and `Qualitative Analysis` against the tagging rules; both look like they may have been mapped to the wrong AI family or architecture bucket.
- Spot-check a few vendor-hosted rows such as `Builder Buddy` to confirm whether `custom_system` is the intended entry type for HHS product-style deployments.
