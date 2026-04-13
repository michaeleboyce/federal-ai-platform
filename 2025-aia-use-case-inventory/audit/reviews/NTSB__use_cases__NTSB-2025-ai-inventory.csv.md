# Source
`NTSB-2025-ai-inventory.csv` (NTSB)

# Counts
- Source rows: 4
- Loaded DB rows in `use_cases`: 4
- Tagged rows in `use_case_tags`: 4
- Count reconciliation is clean.

# Findings
- The CSV header is malformed in the raw file: the first field is split across lines as `"Use Case ID\n\n"`. The loader still recovered the row IDs correctly (`NTSB-0001` to `NTSB-0004`), so this does not appear to have caused row loss, but it is a real parsing oddity worth keeping visible in QA.
- Most field-level mappings preserve source meaning. The `use_case_id`, names, stage, impact flag, vendor/system, and narrative fields align with the raw rows.
- Tagging is directionally reasonable for 3 of 4 rows:
  - `10105` Voice to text transcription -> `nlp_specific`, `administrative`, `enterprise_wide` looks plausible.
  - `10106` Semantic Similarity Text Search -> `rag_pipeline` is defensible given the source description about querying historic reports and authoritative documents.
  - `10108` FOIAXpress AI assistant -> `general_llm` is plausible for an assistant that identifies PII/redaction candidates.
- One tag set looks suspicious: `10107` Dataminr is loaded as `entry_type = custom_system` with `ai_sophistication = classical_ml`. The source row says it was `Purchased from a vendor` and describes a subscription service from a third-party vendor; that reads more like a commercial product deployment than an internal custom system. The current `custom_system` classification is likely too strong.
- `deployment_scope = enterprise_wide` for all four rows may be acceptable if this inventory uses agency-wide rollout loosely, but the source text does not clearly justify that label for each case. `10106` in particular reads more like a search capability under development than an enterprise-wide deployment.

# Recommended follow-up
- Recheck the source-to-tag mapping rules for vendor SaaS / subscription entries, especially `Dataminr`.
- Confirm whether the first CSV header cell newline is expected normalization or an upstream export issue.
- Spot-check whether `enterprise_wide` should be softened for the pre-deployment and pilot rows.
