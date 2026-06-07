# Wave 2 QA rubric

Wave 1 produced one tag row per 2024 use case (`use_case_tags_2024` with
`wave='1'`). Wave 2 is the **QA pass** that flags rows needing reconciliation.

## What you produce

A CSV where **each row is one flagged use case** that needs Wave 3 review.
Rows that look fine in Wave 1 should NOT be emitted. The loader appends
to `use_case_tags_2024` with `wave='2a'` (for matched pairs) or `wave='2b'`
(for retired_2024).

## CSV columns

Required: `use_case_id_2024, tagged_by_agent, quality_flags_json, reasoning, confidence`.

Plus, when you propose a **corrected tag** (i.e., your reading differs
from Wave 1), include the corrected tag values in their normal columns:
`entry_type, is_generative_ai, ai_sophistication, deployment_scope,
is_general_llm_access, is_coding_tool, tool_product_name, tool_vendor,
…`. These get carried into Wave 3 as the proposed fix.

`quality_flags_json` is a JSON array of one or more flags from the
taxonomy below.

## Wave 2a: matched-pair QA (continued / renamed / split)

You see the 2024 row, the 2024 Wave 1 tags, the matched 2025 row, AND
the 2025 IFP tags (`*_2025` suffix). Decide which of the four cases
applies — emit a row only if any of them does:

- **`material_divergence`** — the 2024 vs 2025 tags differ on
  `is_generative_ai`, `ai_sophistication`, `entry_type`, OR
  `deployment_scope` shifts by more than one tier
  (enterprise_wide→bureau is material; bureau→office is not).
- **`drift_legitimate`** — same use case, but the agency legitimately
  changed posture. Example: 2024 pilot of one team using ChatGPT →
  2025 enterprise-wide ChatGPT Enterprise rollout. The tags differ but
  both are correct for their year. Apply this flag (often together with
  `material_divergence`).
- **`tagging_error_2024`** — re-reading the 2024 narrative tells you
  Wave 1 missed something. Propose a corrected tag.
- **`tagging_error_2025`** — Wave 1 was right; the existing 2025 tag is
  the wrong one. Apply this flag — this routes the row to a separate
  manual remediation queue (we do NOT change 2025 tags from this wave).

A single row can carry multiple flags (e.g., `["drift_legitimate","material_divergence"]`).

## Wave 2b: unmatched-2024 sanity (retired_2024)

No 2025 mirror to compare against. Flag if any of these are true:

- **`internal_inconsistency`** — the Wave 1 tag is self-contradictory.
  Example: `is_generative_ai=1, ai_sophistication='classical_ml'` is
  impossible.
- **`misclassified_lifecycle`** — `dev_stage` in 2024 says
  "Operation and Maintenance" or "Implementation and Assessment" but
  the use case is listed as `retired_2024` in lineage, suggesting the
  agency silently dropped a live system rather than legitimately
  aging it off. (Lineage already labels this; just flag if Wave 1's
  scope/sophistication don't match a dropped-live tag.)
- **`tool_vendor_unverified`** — Wave 1 inferred a commercial vendor
  (`is_cots_commercial=1` and a non-empty `tool_product_name`) but the
  evidence is thin. Set `confidence='low'` and propose a corrected
  tag if needed.

## What NOT to flag

- Rows where Wave 2024 / Wave 1 tags look perfectly fine — skip them.
- Rows where the 2024 and 2025 tags are equivalent under sensible
  semantic equivalence (e.g., 2024 says `general_llm` and 2025 says
  `general_llm` even if vendor names differ — that's not a divergence).
- Rows where the 2025 tag is missing entirely (the LEFT JOIN may have
  found no 2025 tag row; flag those as `2025_tags_missing` only if
  doing so is informative).

## Output mechanics

- `tagged_by_agent` should be `wave2a-continued`, `wave2a-renamed-split`,
  or `wave2b-retired` matching your partition.
- `reasoning` is one sentence per row, citing the specific divergence:
  e.g., "2024 says general_llm + bureau; 2025 says general_llm +
  enterprise_wide; CISA's CISAChat went agency-wide between cycles —
  drift_legitimate."
- `confidence`: `low` / `medium` / `high` for your QA judgement.
- Use the Python `csv` module. `mkdir -p` your output dir first.
- Expected emit rate: roughly 10–25% of input rows flagged (i.e., 100–400
  flagged out of 1,425 Wave-2a; 50–200 out of 710 Wave-2b). If you flag
  every row OR almost none, re-read this rubric.
