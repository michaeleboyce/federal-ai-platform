# coding_taxonomy_2026-07 — labeler instructions

Classify every individually-reported use case currently tagged
`is_coding_tool=1` (the article's "70 coding filings") into a closed
coding-tool taxonomy, so the article can state precisely how much of
federal "coding AI" is agentic vs chat vs autocomplete.

Semantics reference: `AGENT_TAGGING_GUIDE.md` (what counts as a coding
tool at all). This round SUBDIVIDES the coding-tagged set; it can also
flag residual false positives (`not_coding`).

## Closed verdict vocabulary (exactly one per row)

| verdict | means |
|---|---|
| `chat_assistant` | Staff ask a general or code-aware chatbot for code help (M365 Copilot code-chat, ChatGPT/Claude used for snippets, internal GPT wrappers). No IDE/pipeline coupling described. |
| `ide_autocomplete` | Completion/suggestion inside an editor (GitHub Copilot in VS/VS Code, CodeWhisperer, Tabnine) WITHOUT autonomous multi-step behavior described. |
| `coding_agent` | An agentic coding tool: plans/executes multi-step coding tasks, edits multiple files, runs commands/tests autonomously (Claude Code, Windsurf/Cascade, Copilot agent-mode/Workspace, Devin-class, "AI writes and executes"). The narrative must describe agentic behavior or name an agent-class product — the word "agent" alone is not enough. |
| `code_analysis_tool` | AI for code understanding/quality/translation rather than authoring: static analysis, code review bots, legacy-code translation/modernization (AveriSource, watsonx Code Assistant for Z), SPL/query generation tools. |
| `not_coding` | Row shouldn't be coding-tagged at all (classifier/autocoder false positive: medical "autocoding", document coding for FOIA/records, budget object-class coding). |
| `unclear` | Narrative genuinely can't distinguish (say why in reasoning). Use sparingly. |

## Decision rules

1. Judge what the row DESCRIBES OPERATING, not aspirations ("we plan to
   explore agents" ≠ coding_agent). Note `stage_normalized` in reasoning
   when it matters.
2. Product name beats vague narrative: GitHub Copilot defaults to
   `ide_autocomplete` unless agent-mode/multi-step autonomy is described;
   ChatGPT/Claude/Gemini chat defaults to `chat_assistant`; Claude Code /
   Windsurf are `coding_agent` by product class.
3. A row covering several tools: label the MOST advanced capability the
   narrative actually describes in use.
4. "Generating code using AI" phrasing with an unnamed tool and no
   workflow detail → `chat_assistant` if prompting is described,
   `unclear` if nothing is.
5. Medical/records/FOIA "coding" → `not_coding` (known autocoder trap:
   DHS LIGER/PAiTH-class classifiers are NOT coding tools).

## Confidence

`high` — product named or behavior explicit. `medium` — inferred from
solid context. `low` — thin narrative; will be re-reviewed 100% by QC.

## Output contract

- Write `verdicts_batch{N}.csv` (N = your batch number) with EXACTLY:
  `agency,use_case_name,verdict,confidence,reasoning`
- Every input row appears EXACTLY once. Copy `agency` and
  `use_case_name` byte-for-byte from the input — never invent, trim, or
  renumber keys. No numeric ids anywhere.
- `reasoning` ≤ 2 sentences citing the narrative evidence.
