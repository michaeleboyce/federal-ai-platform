# Round-2 scope review — methodology + recommendation

Scope: `audit/review_queue_scope_unresolved.csv` (166 rows). All 166 are
`question_type=architecture`; zero are deployment_scope questions despite the
filename. All point to `use_cases.id` (no consolidated rows in this batch).

## Method

Each row was processed by reading the full `use_cases` record (Section 1–5
fields plus the agency-authored values from `raw_json`) and matching against
explicit-evidence patterns drawn from the brief's decision rules:

- **rag_pipeline** — `\bRAG\b`, "retrieval-augmented generation", "vector
  database/store", "embedding-based retrieval", "semantic search +
  summari[sz]e/generate", "GenAI-RAG on …", "chat with our docs", "grounded
  in agency documents", etc.
- **agentic_workflow** — "multi-agent", "agentic workflow/system/pipeline",
  "tool use/calling", "planning loop", "autonomous (decide|plan|execute|
  orchestrate)", "agent-based workflow/orchestration", "Agentforce". A
  *secondary* path fired only when `ai_classification = "Agentic AI"` was
  combined with autonomy/multi-agent language *outside the dropdown text
  itself*.
- **fine_tuned** — "fine-tune(d/ing)", "trained on our/agency/internal
  (data|corpus|documents|tickets|cases|filings)", "LoRA", "adapter trained".
  Negation lookbehind: matches were rejected when the preceding 60 chars
  contained no/not/never/none/N/A/without (catches "No training and/or
  fine-tuning done by FAA").
- **custom_trained** — explicit "trained from scratch" / "built our own
  neural network on our data" only.

Two anti-patterns were important:

1. **`raw_json` keys are AIA template prompts** containing the words
   "fine-tune", "train", and "agent" verbatim. Including the keys lights up
   every detector. Solution: only the *values* are concatenated into the
   narrative, never the keys.
2. **`ai_classification = "Agentic AI: AI systems that perform tasks or
   make decisions autonomously with minimal human intervention."`** is a
   dropdown value with "autonomously" embedded. The autonomy regex was
   forced to evaluate against a stripped narrative that removed both the
   `[ai_classification]` line and the dropdown's verbose form, so the
   dropdown alone never triggers a flip — the agency must also describe
   autonomy/multi-agent behavior in their own words.

Default was `keep_current` whenever no explicit evidence cleared the bar.

## Outcomes

| Decision         | Count |
|------------------|-------|
| keep_current     | 132   |
| apply_proposed   | 33    |
| apply_other      | 1     |
| **total**        | 166   |

| Transition                              | Count |
|-----------------------------------------|------:|
| unknown → unknown                       | 83 |
| inference_only → inference_only         | 26 |
| custom_trained → custom_trained         | 19 |
| unknown → rag_pipeline                  | 18 |
| custom_trained → rag_pipeline           | 7  |
| unknown → agentic_workflow              | 7  |
| fine_tuned → fine_tuned                 | 3  |
| inference_only → rag_pipeline           | 2  |
| agentic_workflow → agentic_workflow     | 1  |

All 34 changes carry `confidence=high` and have a concrete evidence quote.

## Surprises

- **HHS/ACF "RAG implementation using commercially-available LLMs …"
  pattern** appears verbatim in 7+ use cases (uc 9175, 9185, 9188, 9195,
  9197, 9198, 9199, 9234) with the current tag set to `custom_trained`.
  These are clearly RAG, not custom-trained. Worth a separate sweep to
  check whether the upstream populator mis-tags ACF Discover/Upstream
  family entries.
- **Negation handling for fine-tune** was not optional — uc 8851 has the
  literal phrase "No training and/or fine-tuning done by FAA" and would
  otherwise have flipped to `fine_tuned`. Other rows likely have similar
  language; the negation guard prevents false positives.
- **NASA/JPL autonomy use cases** (uc 9708, 9779, 9957, 9767, 9980, 10055)
  describe robotics/spacecraft autonomy with multi-agent planning. These
  are legitimately `agentic_workflow` even though they're not the
  LLM-agent flavor most people imagine.
- **AIA template artefacts** dominate the false-positive surface. Any
  future automated tagging pass over `raw_json` MUST exclude the keys.

## Recommendation

**Apply the 34 changes.** They each have a high-confidence narrative quote
and the evidence rule is conservative. The remaining 132 rows should stay
where they are; the LLM was correct to mark them low-confidence and there
is no narrative basis for moving them. Future improvement should come from
agency follow-up rather than re-tagging from the same text.

If you want to be even more conservative, the 7 ACF "RAG implementation"
flips from `custom_trained → rag_pipeline` could be reviewed by an HHS
data steward first — but the training_data_description literally says
"RAG implementation", so the change looks safe.

## Files

- `resolved.csv` — 166 rows with the decisions above.
- `searches.csv` — empty header only; no web search was needed (the task
  brief flagged this would be rare).
