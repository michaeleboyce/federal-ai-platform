# Agentic-tag review — is `ai_sophistication='agentic'` real on this row?

## What this is

The 2025 heuristic tagger matched keywords like "agent", "autonomous",
"automated workflow" and produced 283 `ai_sophistication='agentic'` rows.
Spot checks show clear misfires (a mammogram-reporting system, classical
wildlife-image classification, deterministic schedulers). OMB's own
`ai_classification` column says "Agentic AI" on only ~88 rows. The IFP
article needs a defensible agentic count.

`input.csv` has one row per currently-agentic use case with its narrative
fields and OMB's own classification.

## Decision rule

TRUE agentic (`keep`): the system uses an AI model (usually an LLM or
foundation model) to **plan or decide across multiple steps with limited
human intervention** — tool use, multi-step orchestration, autonomous task
execution, chained reasoning (e.g. an agent that reads a helpdesk ticket,
queries systems, and drafts + routes the fix; MCP/agent-framework
integrations; multi-agent pipelines).

NOT agentic (`reclassify`): pick the best replacement from the canonical
vocabulary {general_llm, coding_assistant, classical_ml, computer_vision,
nlp_specific, predictive_analytics}:
- RPA / deterministic workflow automation with no model-driven planning →
  usually classical_ml (if any ML) — note it in reasoning.
- Classical autonomy (rovers, spacecraft scheduling, control systems,
  route optimization) → classical_ml or predictive_analytics. "Autonomous"
  in aerospace ≠ agentic AI.
- Detection/classification pipelines (wildlife, imagery, fraud scoring) →
  computer_vision or classical_ml.
- A chatbot that just answers questions (no multi-step tool use) →
  general_llm.

Signals to weight: OMB `ai_classification` = "Agentic AI" is a strong KEEP
signal (the agency itself claims it); explicit mention of agent
frameworks, tool calling, MCP, "multi-step", "orchestrates" are strong
KEEPs. The word "autonomous"/"automated" alone is NOT.

When the narrative is too thin to tell, lean on OMB's own classification;
if that is also absent, `keep` only if the name itself is unambiguous
(e.g. "Helpdesk Agent" with agent-framework vendor), else reclassify to
the most concrete alternative and mark confidence=low.

## Output

Write `verdicts_<your-batch>.csv` to this directory with EXACTLY these
columns (signature-keyed; do NOT invent numeric ids):

agency,use_case_name,verdict,final_ai_sophistication,confidence,reasoning

- verdict ∈ {keep, reclassify}
- final_ai_sophistication ∈ {agentic, general_llm, coding_assistant,
  classical_ml, computer_vision, nlp_specific, predictive_analytics}
  (= 'agentic' when verdict=keep)
- confidence ∈ {high, medium, low}
- reasoning: 1–2 sentences quoting the deciding narrative phrase.

Every input row must appear exactly once in your output.
