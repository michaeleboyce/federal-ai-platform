# Source
`GPO-2025-ai-inventory.csv` (`GPO`, Government Publishing Office)

# Counts
- Source rows: 10
- Loaded DB rows: 10
- Blank rows in source: 0
- Header/parse issues: none observed

# Findings
- The source file is cleanly parsed and the DB preserves the full row count. The five CSV columns map sensibly into the loaded records, with `AI Use Case Name` and `Summary of Use Case` carried through as `use_case_name` and `problem_statement`.
- The main issue is tag direction, not ingestion. Most rows are tagged as `custom_system` with `enterprise_wide` / `inference_only`, which is plausible for internally deployed GPO tools, but several rows read more like product features than custom AI systems.
- `Internet Browser` (`id` 9119) and `DevOps` (`id` 9122) are tagged as `product_feature`, which matches the source better than the other rows, but `DevOps` is still described as “the ability to create dedicated AI projects,” so it is borderline and may be closer to process/tooling than an AI use case.
- The generative-AI flags appear directionally correct only for the LLM-style entries: `Internet Browser` (`id` 9119) and `Document Summarization and Text to Podcast Conversion` (`id` 9124) are the only rows marked `is_generative_ai = 1`, which fits the source. The remaining rows are classical NLP / ML / search use cases and look reasonable.
- The `ai_classification` field is populated with the source’s free-text AI technique descriptions rather than a normalized category. That is acceptable if intended, but it means the name is a little misleading: e.g. `Audio Transcription` stores “Cloud based commercial-off-the-shelf pre-trained NLP models.” and `Threat Detection` stores a narrative about malware detection rather than a canonical label.

# Recommended follow-up
- Keep the parsed rows as-is; there is no evidence of row loss or delimiter corruption.
- Spot-check whether `DevOps` should remain tagged as an AI use case/product feature or be excluded from AI inventory labeling.
- If downstream consumers expect normalized classifications, rename or remap `ai_classification` so it is clear it contains source prose, not a controlled vocabulary.
