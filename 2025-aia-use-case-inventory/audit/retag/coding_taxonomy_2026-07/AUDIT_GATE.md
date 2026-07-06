# AUDIT GATE — coding_taxonomy_2026-07

**Status: GREEN** (labeled, audited, cross-batch adjudicated — 2026-07-06)

## Population and flow

- 70 individually-reported use cases currently tagged `is_coding_tool=1`
  (the article's "70 coding filings"), split into 2 batches of 35
  (`input.csv` → `input_batch{1,2}.csv`). Keyed by
  `(agency, use_case_name)` copied byte-for-byte — no numeric ids.
- Flow: Sonnet labeler per batch (`verdicts_batch{N}.csv`) → Fable
  per-batch audit (`audit_overrides_batch{N}.csv`, agree/override rows)
  → rerun-on-systemic (batch relabeled if the audit finds a systemic
  labeling error) → cross-batch consistency close-out (this gate).
- Closed vocabulary: `chat_assistant / ide_autocomplete / coding_agent /
  code_analysis_tool / not_coding / unclear`. Mechanical validation:
  70/70 rows present, exact multiset match input↔verdicts per batch,
  zero vocabulary violations, zero confidence-vocabulary violations.

## Audit strata

Fable audited 21 of 70 verdict rows (30%; 19 unique signatures — two
duplicate-signature rows were each audited twice):

- 100% of `low`-confidence rows (10: 1 in batch 1, 9 in batch 2).
- 100% of `unclear` verdicts (10 pre-override; all but one overlap the
  low-confidence stratum).
- 100% of `coding_agent` verdicts (4: SSA Windsurf; SBA ×3) — the
  article's headline "agentic coding" claim rides on these.
- Decile sample of the remaining high/medium rows (6: ED ×2, Treasury,
  VA, DOC APIgee/Gemini, NASA IV&V).

## Per-batch outcomes and rerun history

| batch | rows | audited | overrides | final rate | rerun attempts |
|---|---|---|---|---|---|
| 1 | 35 | 7 | 0 | 0.000 | 1 |
| 2 | 35 | 14 | 1 | 0.071 | 0 |

Rerun history: `[{"batch":1,"attempts":1,"final_rate":0},
{"batch":2,"attempts":0,"final_rate":0.071}]`

- **Batch 1** was rerun once: the first pass had a systemic
  product-class gap, fixed by an audit amendment (AveriSource and IBM
  watsonx Code Assistant for Z are `code_analysis_tool` by product
  class; Windsurf is `coding_agent` by product class; retired rows with
  self-describing conversion/modernization titles bucket by title).
  The relabeled batch re-audited with zero overrides.
- **Batch 2** needed no rerun; its single override (DOC "Amazon Q
  Developer Pilot": `unclear` → `ide_autocomplete`) aligns bare-product-
  name rows with the labeler's own treatment of bare "GitHub CoPilot"
  rows (product-class default per decision rule 2; the taxonomy lists
  CodeWhisperer, Amazon Q Developer's predecessor, as the autocomplete
  example). Not systemic — an isolated consistency fix.

## Cross-batch consistency close-out (2026-07-06)

Every product/pattern appearing in both batches was re-checked; all
apparent splits resolve under the decision rules and NO new overrides
were required:

- **GitHub Copilot** (14 rows across both batches): `ide_autocomplete`
  default everywhere except (a) "GitHub Copilot for Code Modernization"
  (DOC, title names the modernization function → `code_analysis_tool`,
  same title-beats-default rule batch 1 applied to Treasury's
  "Modernization Accelerator") and (b) SBA's row explicitly describing
  Copilot's autonomous coding agent (assigned issues → independent PRs)
  → `coding_agent` per the taxonomy's explicit agent-mode upgrade. ED's
  "MS Copilot" row is Microsoft 365 Copilot, the taxonomy's named
  code-chat example → `chat_assistant`. Consistent.
- **Gemini**: DOE "Scripting" is Gemini *chat* generating Python from
  prompts → `chat_assistant` (rule 2); DOC rows name Gemini *Code
  Assist*, an IDE product → `ide_autocomplete`. Different products.
- **OpenAI**: prompt-in/snippet-out API wrappers (ED ×12, HHS Notebooks
  Hub, DHS OCFO GPT) → `chat_assistant`; "GitHub Copilot with the
  OpenAI Codex" is the Copilot product (Codex is its engine) →
  `ide_autocomplete`. Consistent.
- **Amazon Q**: bare pilot title → product-class default (post-
  override); SBA rows with explicit "autonomous multi-step" narrative →
  `coding_agent`. Consistent.
- **Palantir AIP** (reviewed edge case, both batch 2): HHS "Writing
  code using AI" (`chat_assistant`) vs DHS "AI-Powered Developer Tools"
  (`ide_autocomplete`). The narratives materially differ — novice users
  prompting for recommended pyspark code vs developer tooling surfacing
  suggested snippets/refactoring recommendations into the dev workflow.
  Both defensible under rule 1 (judge what the row describes
  operating); cleared, no override.
- Duplicate signatures — (ED, "Generative AI - Code Generation") ×12,
  (DOE, "GitHub Copilot") ×2, (SBA, "Developer Code Assistant AI") ×2 —
  are verdict-HOMOGENEOUS within each group, so signature-keyed fan-out
  application is safe.

## Final verdict distribution (after overrides)

| verdict | rows |
|---|---|
| chat_assistant | 25 |
| ide_autocomplete | 18 |
| code_analysis_tool | 14 |
| unclear | 9 |
| coding_agent | 4 |
| not_coding | 0 |
| **total** | **70** |

For the article: of the 70 coding filings, only 4 (5.7%) describe (or
name a product of) agent-class coding; 25 (35.7%) are chat-style code
help; 18 (25.7%) editor autocomplete; 14 (20%) analysis/modernization
rather than authoring; 9 (12.9%) too thin to classify.

## Known limitations

- `not_coding` came back 0 — the round validated rather than pruned the
  upstream `is_coding_tool` tag; residual false positives, if any, were
  not detectable from these narratives.
- 9 rows (12.9%) remain `unclear` — mostly DOC title-only filings and
  retired rows with blank narratives. The agentic-vs-chat split carries
  this irreducible unknown floor; the article should say "at least"
  when quoting bucket counts.
- Product-class defaults (rule 2 + the batch-1 amendment) mean
  thin-narrative rows inherit the named product's class — e.g. DOE's
  Tabnine "Software Implementation Assistant" is `ide_autocomplete` by
  product class even though its narrative describes planning/
  documentation outputs. The taxonomy measures tool class, not observed
  daily use.
- One key embeds a C1 control character (HHS `AI Code Assistance
  \x96 WETG GitHub CoPilot Proof-of-Concept`, U+0096). Verdict and
  override files preserve it byte-for-byte; any apply script must too
  (no whitespace/Unicode normalization on join keys).
- Batch 1's first-pass labels were discarded on rerun; only the
  post-amendment labels are in `verdicts_batch1.csv`.

## Gate declaration

**GREEN.** Coverage is 70/70 with exact per-batch multiset match and a
closed-vocabulary clean sweep; the one systemic issue (batch 1
product-class gap) was resolved by amendment + full relabel and
re-audited to zero overrides; batch 2's single override is applied in
the distribution above; the cross-batch consistency pass found no
inconsistency the per-batch audits missed. No unresolved systemic
issues block application.
