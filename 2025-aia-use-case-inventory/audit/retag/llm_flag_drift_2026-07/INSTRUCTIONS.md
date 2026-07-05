# LLM flag drift 2026-07 — reconcile `is_general_llm_access` vs `is_generative_ai`

## What this is

341 rows in `use_case_tags` carry `is_general_llm_access = 1` while
`is_generative_ai = 0`. A general-purpose chat LLM is by definition
generative AI, so every such row is a contradiction with exactly three
possible resolutions. This pass adjudicates each one so the /experience
page's definition counts (999 GenAI / 803 LLM-access / 182 enterprise)
stop containing rows that IFP's own tags disagree about.

`input_batch<N>.csv` has one row per contradiction with both current
flags and the row's narrative fields.

## Verdicts

- `set_genai` — the row genuinely IS general LLM access (chat-style
  arbitrary prompts, internal work, broadly available) and the missing
  `is_generative_ai` was tagger drift. → final flags (1, 1).
- `clear_llm_access` — the LLM-access flag is wrong: an embedded copilot
  inside one business app, a narrow single-dataset chatbot, a document-
  processing pipeline, a coding-only tool, a public-facing widget, or a
  classical-ML/NLP system mislabeled. → final flags (0, whatever genai
  should be — usually 0, but a genai document pipeline is (0, 1)).
- `keep_current` — a defensible exception where the row really is
  general-purpose full-text assistance yet not generative (rare; think
  pure retrieval/semantic-search with no generation). You must explain
  why the search tool generates nothing.

## Decision rule for "general LLM access" (same as round 1/round 3)

A row IS a general-purpose FOUO/CUI LLM assistant when ALL of:

(a) staff can submit **arbitrary text prompts** (chat-style), not just a
    fixed workflow;
(b) it is approved/intended for internal government work (FOUO/CUI-class
    use, not a public-facing widget);
(c) it is **broadly available** to staff rather than scoped to one
    workflow, one dataset, or one narrow user group.

NOT general LLM access: ServiceNow Now Assist and other embedded copilots
inside a single business app; narrow customer-service chatbots over one
dataset; per-policy document search; document-processing pipelines that
happen to use an LLM; coding-only tools; public-facing chatbots.

Edge guidance:
- M365 Copilot / Gemini Workspace deployments count as general LLM access
  (and are generative — `set_genai`).
- "Semantic search and summarization" systems: summarization IS
  generation. If staff prompt it freely across a broad corpus it's
  `set_genai`; if it's one investigation dataset's search UI it's
  `clear_llm_access` (narrow workflow) — and note whether genai should
  still be 1 for the summarization component.
- When the narrative is too thin to tell, prefer `keep_current` with
  confidence=low and say so in the reasoning.

## Output

Write `verdicts_<your-batch>.csv` to this directory with EXACTLY these
columns (signature-keyed; do NOT invent numeric ids):

agency,use_case_name,verdict,final_is_general_llm_access,final_is_generative_ai,confidence,reasoning

- verdict ∈ {set_genai, clear_llm_access, keep_current}
- final flags ∈ {0,1} — what the DB should say after this pass
- confidence ∈ {high, medium, low}
- reasoning: 1–2 sentences quoting the narrative phrase that decided it.

Every input row must appear exactly once in your output. Optional web
search where a named system is ambiguous; note the URL in reasoning.
