# Round 3 — adjudicate the low-confidence `is_general_llm_access` flips

## What this is

The 2026-04 general-LLM audit (`audit/retag/general_llm/`) proposed 274
flips of `is_general_llm_access` derived from name-pattern heuristics, all
marked low-confidence and never applied. This round adjudicates each one
with a per-row read of the inventory narrative, so the chatbot-adoption
numbers in the IFP article trace to a reviewed verdict, not a regex.

`input.csv` has one row per pending flip with the proposal and the row's
narrative fields (problem_statement, expected_benefits, system_outputs,
system_name, vendor, stage, OMB ai_classification).

## Decision rule (same as round 1, audit/retag/general_llm/notes.md)

A row IS a general-purpose FOUO/CUI LLM assistant (`final=1`) when ALL of:

(a) staff can submit **arbitrary text prompts** (chat-style), not just a
    fixed workflow;
(b) it is approved/intended for internal government work (FOUO/CUI-class
    use, not a public-facing widget);
(c) it is **broadly available** to staff rather than scoped to one
    workflow, one dataset, or one narrow user group.

NOT general LLM access (`final=0`): ServiceNow Now Assist and other
embedded copilots inside a single business app; narrow customer-service
chatbots over one dataset; per-policy document search; document-processing
pipelines that happen to use an LLM; coding-only tools; public-facing
chatbots.

Edge guidance:
- M365 Copilot / Gemini Workspace deployments count as `1` (arbitrary
  prompts, broad availability) even though they ride an office suite.
- "ChatGPT/Claude/Gemini sandbox for evaluation" counts as `1` only if the
  narrative says staff broadly can use it; a 5-person evaluation pilot is
  still `1` (the flag is about kind, not scale — scope is a separate tag),
  but a single-workflow integration is `0`.
- When the narrative is too thin to tell, prefer `keep_current` with
  confidence=low and say so in the reasoning.

## Output

Write `verdicts_<your-batch>.csv` to this directory with EXACTLY these
columns (signature-keyed; do NOT invent numeric ids):

agency,use_case_name,verdict,final_is_general_llm_access,confidence,reasoning

- verdict ∈ {confirm_proposed, keep_current}
- final_is_general_llm_access ∈ {0,1} (what the DB should say)
- confidence ∈ {high, medium, low}
- reasoning: 1–2 sentences quoting the narrative phrase that decided it.

Every input row must appear exactly once in your output. Optional web
search (FedScoop/Nextgov/agency sites) where a named system is ambiguous;
note the URL in reasoning if used.
