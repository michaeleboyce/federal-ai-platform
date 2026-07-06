# integration_depth_2026-07 — labeler instructions

Label how deeply each PILOT or DEPLOYED individually-reported use case is
wired into agency work. This measures what the OMB M-25-21 inventory
format does not collect (no interconnection, access, or runtime field
exists) — the labels back the article claim "N% of deployed federal AI
describes actual system/workflow integration."

## Closed verdict vocabulary (exactly one per row)

| verdict | means |
|---|---|
| `standalone_chat` | Staff use the tool directly (chat/copilot/search box) with no described coupling to agency systems or a specific process. General LLM access, drafting help, Q&A, brainstorming. |
| `workflow_embedded` | Built into ONE identified process, form, or pipeline — the AI runs at a specific step (triage of incoming X, summarize each Y, route Z) — but the narrative describes only that single flow, not read/write integration with agency systems of record. |
| `system_integrated` | Reads from and/or writes to identified agency systems or data stores in operation — API/ETL/database coupling, case-management or EHR integration, model outputs feeding a production system, dashboards refreshed from live agency data. |
| `agentic_workflow` | Autonomous multi-step behavior against systems/tools: plans and executes chains of actions, uses tools/APIs on its own, updates systems without a human driving each step. Requires described autonomy, not the word "agent". |
| `unclear` | The narrative genuinely does not say how the AI connects to work (common for thin filings). Say what's missing in reasoning. |

Ladder logic: pick the DEEPEST level the narrative actually describes as
operating. standalone_chat < workflow_embedded < system_integrated <
agentic_workflow.

## Decision rules

1. **Operating, not aspirational.** "Will integrate with…", "we plan to
   connect…" does NOT count — label what the row describes as running at
   its stage. If everything concrete is future-tense, label the current
   state (often `standalone_chat` or `unclear`) and note it.
2. **Classical ML in production usually = `system_integrated`.** A risk
   model scoring live claims inside a case system, CV on an operational
   sensor feed, a forecasting model feeding a production dashboard —
   these read/write real systems even with no LLM anywhere.
3. **Named tool ≠ depth.** "We use ChatGPT/Copilot" alone is
   `standalone_chat` no matter how capable the tool; depth comes from the
   described coupling, not the product.
4. **RAG over agency documents**: retrieval from an agency corpus to
   answer staff questions is `workflow_embedded` (it's coupled to agency
   DATA for one flow) unless it also writes back or spans systems —
   then `system_integrated`.
5. **`agentic_workflow` is rare.** Multi-step autonomy must be described
   (executes actions, chains tools, updates records itself). Chatbots
   with function-calling described only as "answers questions" are not
   agentic.
6. **Human-in-the-loop doesn't reduce depth.** A model whose outputs are
   reviewed before entering the system of record still counts at the
   depth of that coupling.

## Confidence

`high` — the coupling (or its absence) is explicit. `medium` — inferred
from solid context (system names, data flows). `low` — thin narrative;
will be re-reviewed 100% by QC.

## Output contract

- Write `verdicts_batch{N}.csv` (N = your batch number) with EXACTLY:
  `agency,use_case_name,verdict,confidence,reasoning`
- Every input row appears EXACTLY once. Copy `agency` and
  `use_case_name` byte-for-byte from the input CSV (use a python script
  with the csv module — do not hand-retype keys). No numeric ids.
- `reasoning` ≤ 2 sentences citing the narrative evidence (name the
  system/process when one is named).
