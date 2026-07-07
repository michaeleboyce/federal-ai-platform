# AUDIT GATE — integration_depth_2026-07

**Status: GREEN** (labeled, Fable-audited, adjudicated — 2026-07-06)

## Population and flow

- 1,573 PILOT or DEPLOYED individually-reported use cases (`input.csv`,
  built from `use_cases` with `stage_normalized IN ('pilot','deployed')`),
  split into 14 agency-grouped batches (`input_batch{1..14}.csv`):
  b1 HHS 255 · b2 DOJ 188 · b3 DOE 176 · b4 VA 159 · b5 DOI 129 ·
  b6 DHS 118 · b7 USDA 86 · b8 ED 77 · b9 FRTIB/NARA/SBA/Treasury 64 ·
  b10 FERC/GPO/NASA/NIGC/PBGC 65 · b11 CFTC/DOT/HUD/NCUA/NTSB/SSA 64 ·
  b12 FCC/FDIC/FHFA/NSF/State 64 · b13 EPA/GSA/OPM/OSHRC/SEC 64 ·
  b14 DOL/EAC/FRB/FTC/NRC 64.
- Flow: Sonnet labeler per batch (`verdicts_batch{N}.csv`, closed
  5-verdict vocabulary) → Fable audit per batch
  (`audit_overrides_batch{N}.csv`: agree/override per sampled row) →
  batch rerun where the audit found a systemic labeling error →
  round-level adjudication (this gate).
- Coverage (adjudication check, csv-module multiset over
  `(agency, use_case_name)`): **1,573/1,573 exact** — no missing, no
  extra, no duplicate drift; each batch's verdicts also match its own
  input batch exactly. Zero vocabulary violations in verdicts and
  overrides.
- Repeated signatures: 14 signatures cover 64 input rows (50 extra
  rows; e.g. ED files the same five "Generative AI - *" templates from
  up to 16 offices, DOJ files same-named rows from two components).
  Every repeat received an identical final verdict — no consistency
  overrides were needed.

## Audit strata (354 rows audited, 22.5%)

- 100% of `low`-confidence labels (101/101 — this round's substitute
  for a separate QC-judge layer; INSTRUCTIONS promised low-confidence
  re-review and the audit delivered it).
- 100% of `agentic_workflow` first-pass verdicts (18/18 — the rare
  class most prone to over-assignment).
- 91% of `unclear` first-pass verdicts (60/66).
- Samples of the remaining verdicts: standalone_chat 60/180,
  workflow_embedded 151/697, system_integrated 64/562. Batch 9 was
  audited 100% (64/64).

## Per-batch audit outcomes

| batch | rows | audited | overrides | override rate (of audited) | rerun attempts |
|---|---|---|---|---|---|
| 1 | 255 | 50 | 2 | 0.040 | 1 |
| 2 | 188 | 37 | 2 | 0.054 | 0 |
| 3 | 176 | 53 | 5 | 0.094 | 0 |
| 4 | 159 | 21 | 3 | 0.143 | 0 |
| 5 | 129 | 21 | 1 | 0.048 | 0 |
| 6 | 118 | 14 | 1 | 0.071 | 0 |
| 7 | 86 | 13 | 1 | 0.077 | 1 |
| 8 | 77 | 20 | 1 | 0.050 | 1 |
| 9 | 64 | 64 | 5 | 0.078 | 1 |
| 10 | 65 | 20 | 2 | 0.100 | 0 |
| 11 | 64 | 10 | 1 | 0.100 | 0 |
| 12 | 64 | 13 | 1 | 0.077 | 0 |
| 13 | 64 | 10 | 1 | 0.100 | 0 |
| 14 | 64 | 8 | 0 | 0.000 | 1 |

Rerun history (orchestration record; `final_rate` = overrides ÷ audited
rows after the final attempt — batch 5 was recorded as `4.8`, i.e.
4.8% = 0.048):

```json
[{"batch":1,"attempts":1,"final_rate":0.04},{"batch":2,"attempts":0,"final_rate":0.054},
 {"batch":3,"attempts":0,"final_rate":0.094},{"batch":4,"attempts":0,"final_rate":0.143},
 {"batch":5,"attempts":0,"final_rate":0.048},{"batch":6,"attempts":0,"final_rate":0.071},
 {"batch":7,"attempts":1,"final_rate":0.077},{"batch":8,"attempts":1,"final_rate":0.05},
 {"batch":9,"attempts":1,"final_rate":0.078},{"batch":10,"attempts":0,"final_rate":0.1},
 {"batch":11,"attempts":0,"final_rate":0.1},{"batch":12,"attempts":0,"final_rate":0.077},
 {"batch":13,"attempts":0,"final_rate":0.1},{"batch":14,"attempts":1,"final_rate":0}]
```

- 26 overrides total (7.3% of audited rows; 1.7% of all rows).
  Directional profile: depth overcalls demoted (system_integrated →
  workflow_embedded ×7, agentic_workflow → system_integrated ×4,
  agentic_workflow/system_integrated → unclear ×2), undercalls promoted
  (standalone_chat → workflow_embedded ×3, workflow_embedded →
  system_integrated ×2), thin filings resolved (unclear →
  standalone_chat ×5, workflow_embedded → unclear/standalone_chat ×3).

## Cross-batch consistency (adjudication spot-checks)

- Bare M365 Copilot rows: 36/41 standalone_chat; the 5 exceptions are
  narrative-justified (Copilot Studio agents "securely connect to data
  and workflows", Copilot for Security against live threat feeds, RAG
  chatbots over a named corpus, VA CT CoPilot in a radiology step).
- ChatGPT (10/11), GitHub Copilot (6/7), Gemini (3/4), Claude (5/6)
  standalone_chat; each exception describes real coupling (e.g. DHS
  PDF Intake feeding USCIS ELIS, EAC inbox routing).
- Rule-2 check: deployed classical-ML/CV rows are 334 system_integrated
  / 199 workflow_embedded; the 15 labeled standalone_chat are all
  consumer-feature filings (Photoshop, Google Translate, browser AI,
  spellcheck) correctly held at rule 3 ("named tool ≠ depth").
- All 13 distinct `agentic_workflow` finals describe explicit multi-step
  autonomy (VA VBMS claims automation, NASA rover autonomy chains, DOE
  ACORN closed-loop control, DOJ autonomous drones).
- No systematic cross-batch inconsistency found; no adjudication-round
  override rows were added.

## Final verdict distribution (after overrides)

Row-weighted, all 1,573 rows:

workflow_embedded 703 (44.7%) · system_integrated 564 (35.9%) ·
standalone_chat 227 (14.4%) · unclear 65 (4.1%) ·
agentic_workflow 14 (0.9%)

Distinct signatures (1,523): workflow_embedded 702 ·
system_integrated 560 · standalone_chat 183 · unclear 65 ·
agentic_workflow 13.

Confidence: high 465 · medium 1,007 · low 101 (all low audited).

## Known limitations

- Labels measure **described** integration depth, not verified reality:
  thin filings bias toward shallower verdicts (rule 1 labels the
  operating state, not plans); `unclear` (4.1%) marks rows where the
  narrative says nothing about coupling. Article phrasing should say
  "describes actual system/workflow integration".
- `standalone_chat` mixes general LLM access with embedded consumer AI
  features (Photoshop, browser AI, grammar checkers) — the ladder
  measures coupling, not product capability, by design.
- ED's batch is dominated by 46 near-duplicate office-level template
  filings ("Generative AI - Text Generation" ×16 etc.), inflating
  row-weighted standalone_chat; distinct-signature counts are given
  above for de-duplicated analysis.
- `agentic_workflow` includes autonomous robotics/CV chains (rovers,
  drones) per the autonomy rule — it is not an "LLM agents" count.
- No separate QC-judge layer ran; the Fable audit's 100% coverage of
  low-confidence and agentic rows stands in for it.
- Not yet applied to the DB — an apply script keyed on
  `(agency, use_case_name)` signatures (never numeric ids) is the next
  step; this gate covers labeling + audit only.

## Gate declaration

Coverage 1,573/1,573; every duplicate signature consistent; zero
closed-vocabulary violations; all per-batch audits complete with no
unresolved systemic issue; cross-batch spot-checks clean.
**The round is GREEN.**
