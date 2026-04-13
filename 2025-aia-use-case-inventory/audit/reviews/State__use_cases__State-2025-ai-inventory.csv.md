# Source
`State-2025-ai-inventory.csv` (`Department of State`)

# Counts
- Source rows: `60`
- Loaded DB rows: `60`
- Row count matched; I did not see dropped or extra records.

# Findings
- The main parsing issue is that the source `Use Case ID` values did not survive into the DB. In the raw CSV, rows begin with IDs like `DOS - 1473`, `DOS - 1530`, and `DOS - 1495`, but `use_cases.use_case_id` is blank for the loaded rows. That breaks traceability back to the source record even though the rest of the row content is present.
- Most row content appears to preserve the source meaning, including stage, classification, and narrative fields. For example, `AI Input in Translation` is loaded as a deployed generative-AI translation workflow with vendor `RWS`/system `Trados`, which matches the source, and `AI-Augmented Declassification Review` is loaded as a deployed classical ML review workflow with contractor `Deloitte`, which also matches the source.
- The tags are broadly directionally plausible for this file, but they are sparse in places. Several obvious product-backed or chatbot-style entries are tagged correctly (`StateChat` as a product deployment with OpenAI involvement; `BudgetChat AI Tool` as a general-LLM RAG workflow), while many rows still have `architecture_type = unknown` and no product-capability tag. That looks like incomplete enrichment rather than a clear mislabel, but it is worth checking if those tags were expected for this source.
- One tag choice that is worth a closer look is `Travel.State.Gov (TSG) Enhanced Search and Chatbot`, which is retired in the source but still tagged `mission_critical` and `general_llm`. The tag is not obviously impossible, but it is a weaker fit than the adjacent rows and may reflect overbroad use-type tagging.

# Recommended follow-up
- Restore or populate `use_case_id` during import so each loaded row can be tied back to the source CSV record.
- Spot-check the tagger on the chatbot/translation rows and on rows left with `architecture_type = unknown` to confirm the enrichment rules are behaving as intended.
