# Batch 2 adjudication notes — HHS, SBA, SSA, GPO, HUD, NRC, CFTC

## Decision counts

| Action | Count |
|---|---|
| `reject_rename` | 98 |
| `confirm_rename` | 6 |
| `recover_match` | 0 (1 candidate flagged, see below) |
| `split` | 0 |
| `merge` | 0 |
| **Total** | **104** |

All 104 `suggested_rename` pairs in this batch belong to **HHS**. The other
six agencies in the batch (SBA, SSA, GPO, HUD, NRC, CFTC) contributed only
`retired_2024` / `new_2025` residual rows, no queued pairs.

## Headline finding: the HHS `suggested_rename` queue is almost entirely noise

98 of 104 pairs (94%) are `reject_rename`. The Phase-3 fuzzy matcher paired
HHS rows by surface name/keyword overlap, but the underlying narratives are
disjoint and — critically — usually sit in **different bureaus** (ASPR vs
CMS, CDC vs NIH, FDA vs HRSA, etc.). HHS appears to have substantially
re-filed its 2025 inventory: many 2024 ASPR SCCT supply-chain models and the
2024 NIH/NLM literature-indexing suite (MetaMap, MTIX, NLM-Chem, NLM-Gene,
SingleCite, Best Match, Computed Author) have **no 2025 successor at all**
and were paired against unrelated brand-new 2025 use cases. Several 2025
"matches" are bare retired stubs (empty narratives, stage "d) Retired"):
pairs 0, 26, 64, 68, 77, 87, 89, 95.

## The 6 confirmed renames

- **[13]** ChatCDC Enterprise GenAI Chatbot (Data Extraction) → CDC Chatbot -
  Enterprise Data Assistant. Same EDAV chatbot, RAG over document sets;
  high confidence.
- **[27]** Knowledge Management Platform → Knowledge Management Solution.
  Same CMS CEDAR system, NLP/LLM over structured + unstructured data.
- **[34]** Chat Client - Resource Library → Resource Library Assistant.
  Same CMS QPP knowledge-base chatbot.
- **[11]** Global influenza vaccine equity literature review →
  Reviewing Global Influenza Vaccine Literature. Same EDAV LLM
  abstract-screening workflow.
- **[12]** CFA Disease Modeling → CFA Model Studio (medium). Same CDC CFA
  group, same 1CDP platform; 2025 is the productized modeling-infrastructure
  continuation.
- **[31]** FOIA Document Review/Redaction Automation → FOIA REDACTION (FRED)
  TOOL (medium). HHS FOIA-redaction use case; 2024 filed under OIT/OSORA,
  2025 under FDA/CDER as the named "FRED" tool.

## Flagged: one recover_match candidate NOT emitted (slug conflict)

Pair **[49]** (`Information Search from Google` → `AWS Kendra Search tool`)
and pair **[103]** (`Smart Search` → `Agentic Web Search`) are both rejected.
But the *correct* lineage is cross-wired: 2024 `hhs-smart-search` (SAMHSA's
plan to procure AWS Kendra for the SAMHSA STORE) is the genuine predecessor
of 2025 `hhs-aws-kendra-search-tool` (SAMHSA, Kendra, SAMHSA STORE). A
`recover_match` linking `hhs-smart-search` ↔ `hhs-aws-kendra-search-tool`
would be ideal, but both slugs are already consumed by the `reject_rename`
decisions on pairs 49 and 103 — emitting the recover_match would trip the
"one slug, one decision" rule and land in `integration/conflicts.csv`.
**Recommend manual relinkage**: after rejects 49/103 apply, link the freshly
freed `hhs-smart-search` (retired_2024) to `hhs-aws-kendra-search-tool`
(new_2025) as a `renamed` pair.

## Split / merge

No `split` or `merge` detected. The HHS `new_2025` residual list is large
(178 rows) and contains adjacent clusters (e.g. multiple GrantSolutions
tools, multiple Sentinel "use case package" rows, multiple NHLBI Chat
Workflow rows), but none of them trace back to a single 2024 slug present in
this batch — they are genuinely new 2025 filings, not splits of a 2024 use
case. Two 2025 rows are self-declared agency renames ("Renamed: AI-Assisted
Drug Review Letter Drafting", "Renamed: Document Room Submission AI-Assisted
Categorization") but their 2024 partners are not in this batch's residual or
queue, so no decision can be made on them here.

## Residual retired_2024 — checked for recoveries, none found

- SSA `Anomalous iClaim Predictive Model` and `Representative Payee Misuse
  Model`: SSA's 2025 fraud/risk models (PER/TDR, CDR, QDD, SSI
  Redetermination) are all already matched; these two have no 2025
  successor — genuinely retired.
- CFTC `Spoofing Detection AI/ML Project`: no CFTC `new_2025` rows in
  batch — genuinely retired.
- HHS `News from commercial publisher`, `NAMs landscape analysis`,
  `Remediate Adobe PDF documents`: no narrative-matching 2025 row —
  genuinely retired.

## Confidence

All 98 rejects are `high` confidence — the narratives are unambiguously
disjoint. Of the confirms, [12] and [31] are `medium` (genuine lineage but
the use case crossed bureaus / was rescoped between years); the other four
are `high`.
