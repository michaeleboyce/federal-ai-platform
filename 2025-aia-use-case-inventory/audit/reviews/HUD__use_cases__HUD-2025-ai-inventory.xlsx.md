# Source
- File: `data/raw/HUD-2025-ai-inventory.xlsx`
- Agency: `HUD` / Department of Housing and Urban Development
- Sheet/context: `use_cases`

# Counts
- Source rows: `11`
- Loaded DB rows: `11`
- Tagged rows: `11`
- Untagged rows: `0`

# Findings
- Row count matches exactly, and the workbook rows are preserved in the DB without obvious truncation or row loss.
- The source structure is intact for the main fields. The 2024/2025 split is preserved, including wrapped cell text like the note in `HUD-2024-003` (`Previously "Automating Draft Counterparty Credit Narrative Reports"...`).
- Most tags are directionally plausible, but a few look misclassified or over-normalized:
- `9624` (`Voice of the Customer`) is tagged as `product_deployment`, but the source shows a vendor-backed product stack (`Medallia; Qualtrics`) rather than a custom in-house build. The label summary also indicates `Custom In-House AI`, which is hard to reconcile with the source.
- `9628` (`Amazon Textract for automatic signature identification`) is tagged `ai_sophistication=computer_vision`, which fits the source topic, but the loaded row still has `ai_classification=Natural Language Processing (NLP)`. That classification looks directionally wrong for signature detection / Textract-style OCR.
- `9629` (`Email Assistant`) and `9631` (`FHA Resource Center Chatbot`) are both pre-deployment conversational/use-assistant style entries, but their tag mix is uneven: `9629` is `general_llm` with `is_generative_ai=1`, while `9631` is tagged `general_llm` and `rag_pipeline` even though the source row is a chatbot and should be checked for whether retrieval vs. pure assistant labeling was inferred too aggressively.
- The retired rows `9625` and `9626` are sparsely populated in the source and loaded as such, so the parser likely handled the missing-detail entries correctly. The main risk there is classification confidence, not parsing.

# Recommended follow-up
- Recheck the labeling rules for vendor-backed deployments versus custom systems, especially for `Voice of the Customer` (`9624`).
- Reclassify `Amazon Textract for automatic signature identification` (`9628`) away from NLP if the taxonomy is meant to reflect the visible function rather than the broader AI stack.
- Spot-check the assistant/chatbot rows (`9629`, `9631`) to confirm whether `rag_pipeline` and `general_llm` were assigned from source evidence or inferred from the name alone.
