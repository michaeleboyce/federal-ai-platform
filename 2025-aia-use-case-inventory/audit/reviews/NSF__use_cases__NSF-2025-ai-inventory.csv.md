# Source
NSF-2025-ai-inventory.csv (`use_cases`)

# Counts
- Source row count: 23 non-empty data rows
- Loaded DB row count: 23
- Parsing looks consistent: the CSV has 25 raw rows total, with 2 blank rows and a single header row at index 1

# Findings
- Row count matches exactly, so there is no evidence of dropped or duplicated source records in the load.
- The source meaning is mostly preserved, but a few tags look directionally off for the actual AI pattern described in the text.
- `AII-48` / `NSF AI-Ready RPPR Data` is tagged as `bespoke_application` with `general_llm`, `rag_pipeline`, and `is_generative_ai=1`, but the source reads like a multi-service data engineering / analytics workflow around AWS Bedrock, SageMaker, Neptune, and Comprehend rather than a single bespoke LLM app.
- `AII-56` / `Comparison of proposal similarities at different levels of NSF organization` is a similarity-scoring / embedding comparison task, but it is tagged `nlp_specific` with `rag_pipeline`; that label set implies retrieval-generation behavior that is not supported by the source text.
- `AII-33` / `Exploring the use of BERTopic Modeling for a portfolio analysis` is correctly not marked generative, but it is still worth flagging as a representative example of the file's broader pattern: several rows are labeled with LLM-style tags even when the source describes classic NLP or clustering rather than generation.
- The rest of the tags look broadly plausible at a high level, especially the product-specific rows such as ServiceNow, Microsoft Copilot, Textract, and CodeWhisperer.

# Recommended follow-up
- Revisit the tagger rules for non-generative NLP workloads so similarity, topic-modeling, and classification rows do not drift into `general_llm`/`rag_pipeline` unless the source explicitly describes those behaviors.
- Spot-check whether `AII-48` should be treated as an AWS platform integration or a true AI application, because that classification changes both `entry_type` and the AI-specific tags.
