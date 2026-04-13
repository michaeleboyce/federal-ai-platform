# Source
NCUA `NCUA-2025-ai-inventory.csv` (National Credit Union Administration)

# Counts
- Source rows: 3
- Loaded DB rows: 3
- Count match: yes
- Raw parsing looks structurally intact: the CSV has one header row plus 3 data rows, and each data row has the expected 44 columns.

# Findings
- The row count matches, but the loaded `use_cases` rows do not preserve the source `Use Case ID` values. In the raw CSV the identifiers are `NCUA 01`, `NCUA-02`, and `NCUA-03`, but the DB rows for `id` 10071-10073 have `use_case_id = NULL`. That is a concrete loss of source meaning because the primary source identifier is gone from the loaded record.
- The core content is otherwise preserved well. The three use cases map cleanly to the same names in the DB: `Machine Learning Data Validation`, `Supervisory Stress Testing`, and `Risk Indicator Model`, and the descriptions still read as classical predictive ML used for internal supervision/data-quality work.
- The tags look directionally correct overall. All three rows are sensibly tagged as `custom_system`, `classical_ml`, `enterprise_wide`, and `administrative`, which matches the source text. None of the rows look like generative AI, COTS, or public-facing tools.
- One tag is worth a quick second look: `architecture_type = custom_trained` appears only on `Supervisory Stress Testing` because its training-data field mentions “Vendor sourced.” That may be a reasonable inference, but it is not explicit in the source and the other two rows are tagged `unknown`, so this tag should be treated as weaker than the rest.

# Recommended follow-up
- Backfill or preserve the raw `Use Case ID` field for these rows if the pipeline is expected to retain source identifiers.
- Keep the current tag set unless there is a broader rule for inferring `architecture_type` from training-data wording; if so, apply that rule consistently across similar NCUA rows.
