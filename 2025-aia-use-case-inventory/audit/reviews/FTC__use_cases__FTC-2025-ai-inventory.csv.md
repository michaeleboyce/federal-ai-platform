# Source
FTC-2025-ai-inventory.csv (FTC, Federal Trade Commission)

# Counts
- Raw CSV contains 17 physical rows: 16 data rows plus 1 trailing blank row.
- Loaded DB row count matches the source at 16 rows.
- All 16 loaded rows are tagged; no untagged FTC rows showed up in the tag table.

# Findings
- Parsing looks mostly clean. The import preserved all FTC use cases and did not duplicate or drop rows. The only source artifact is the trailing blank row at the end of the CSV.
- The source itself has a few mild data-quality quirks, but they were carried through rather than misparsed: several rows use non-ASCII punctuation in the stage field, and the CSV header for outputs contains mojibake-style apostrophes from the original encoding.
- The tagger is directionally reasonable for the FTC file overall. The long-running Sentinel/Leidos entries are consistently treated as `custom_system`, while the vendor-hosted items like `Microsoft 365 Copilot` are tagged as `product_deployment`.
- One clear semantic mismatch is `FTC-0015 Azure ML`. The raw CSV classifies it as `Generative AI`, but the actual description is a GPU-backed model training/testing platform. The DB tag `classical_ml` is more defensible than the source label, so this row looks like a source labeling problem that the normalization corrected.
- `FTC-0016 DNC IVR Audio File Transcription` is tagged as `general_llm`, but the source description is transcription of IVR audio, which reads more like NLP/transcription than a general LLM use case. That tag is directionally weak.
- `FTC-0013 IVR Automated Voice Assistant` is also tagged `general_llm` and `mission_critical`. The source frames it as a low-value call-handling assistant for consumer inquiries, so `mission_critical` feels overstated.
- `product_capability` is blank across all 16 rows. That is consistent with a use-case inventory, but it means the tag set does not capture the one clear product-style entry (`Microsoft 365 Copilot`) as a distinct capability class.

# Recommended follow-up
- Keep the import as-is; the row count and source preservation look correct.
- Review the FTC tagging rules for audio transcription and IVR assistants so `general_llm` is not overused on non-LLM NLP workflows.
- Consider whether `product_capability` should be populated for product-centric FTC rows, or whether the current schema intentionally leaves that dimension empty for use-case files.
