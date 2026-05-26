# Agency workforce + AI-eligible-share backfill

## Why

The `/experience` page on the dashboard estimates per-agency AI seats by
summing license-band midpoints from `consolidated_use_cases.estimated_licenses_users`.
That number conflates "tool entitlements" with "employees who could plausibly
use the tool" and ignores the well-researched `agency_ai_access_evidence`
coverage tiers. We're adding a parallel estimate grounded in:

```
seats_headcount = SUM over bureaus(
    bureau_headcount × bureau.ai_eligible_share × estimated_share_of_eligible
)
```

The two estimates are displayed side-by-side on the dashboard — neither
replaces the other. This plan produces the data the new estimate needs.

## Output

Two destinations, populated via `scripts/apply_agency_workforce.py`:

1. `agency_workforce_profile` (new table, from migration m013) — one row per
   organization at `level IN ('agency', 'bureau')`. Carries `total_headcount`,
   `ai_eligible_share`, dated source URL + verbatim quote, confidence, wave.
2. `agency_ai_access_evidence` extensions (from m013) —
   `estimated_share_of_eligible` REAL, `share_rationale` TEXT,
   `matrix_product_key` TEXT mapping `tool_name` to one of the dashboard's
   7 product family keys.

Calibration priors land at `audit/research/agency_workforce/priors.json`.
Per-agent outputs at `audit/research/agency_workforce/<wave>-<agent>.json`.

## The four waves

### Wave 0 — empirical prior calibration (1 agent)

The dashboard's coverage tiers are: `all`, `most`, `partial`, `pilot`,
`latent`, `unknown`, `none`. Wave 2 needs a default share-of-eligible per
tier when the evidence row's free-text doesn't cite a specific number.

Wave-0 agent:

1. Read every row of `agency_ai_access_evidence`.
2. For rows where `estimated_users` contains a parseable pair like
   `"~100,000 of 470,000"` or `"all VA staff (~470,000); 100,000 onboarded"`,
   extract `(numerator, denominator, coverage_assessment)`.
3. Group the extracted ratios by `coverage_assessment`. Emit median
   share-of-eligible per tier.
4. Output `audit/research/agency_workforce/priors.json`:

```json
{
  "captured_by": "wave-0-priors",
  "captured_at": "2026-05-26T03:00:00Z",
  "priors": {
    "all":     { "default": 0.18, "n": 7,  "median": 0.18, "min": 0.05, "max": 0.40 },
    "most":    { "default": 0.42, "n": 5,  "median": 0.42, "min": 0.20, "max": 0.70 },
    "partial": { "default": 0.20, "n": 4,  "median": 0.20, "min": 0.05, "max": 0.45 },
    "pilot":   { "default": 0.03, "n": 3,  "median": 0.03, "min": 0.01, "max": 0.05 },
    "latent":  { "default": 0.01, "n": 2,  "median": 0.01, "min": 0.005, "max": 0.02 },
    "unknown": { "default": null, "n": 0 },
    "none":    { "default": 0.00, "n": 1 }
  }
}
```

If a tier has zero observations, emit `default: null` rather than guessing —
Wave 2 will fall through to a conservative hand-set value documented in the
applier.

### Wave 1 — headcount + AI-eligible share (6 agents, parallel)

Each agent owns a partition. Partition by agency-size bucket so big agencies
(VA, DHS, HHS) get focused attention without one agent doing 25 small ones:

| Agent | Partition (approx) |
|---|---|
| W1-A | VA + bureaus (~10 organizations) |
| W1-B | DHS + bureaus (CBP, ICE, FEMA, USCIS, TSA, USSS, CISA, USCG, S&T) |
| W1-C | HHS + bureaus (CMS, NIH, CDC, FDA, HRSA, IHS, ACL, ACF, AHRQ, ASPR, SAMHSA) |
| W1-D | DOD-civilian-equivalents, DOJ + bureaus, Treasury + bureaus |
| W1-E | DOI + bureaus, USDA + bureaus, DOE + bureaus, DOC + bureaus, DOT + bureaus, DOL + bureaus, ED + bureaus, State + bureaus, EPA + bureaus, HUD + bureaus |
| W1-F | All remaining (smaller independent agencies; ~22 organizations) |

Per organization:

1. **Headcount.** Source order: OPM FedScope (https://www.fedscope.opm.gov)
   → agency budget justifications (most recent FY) → agency org-chart pages
   → agency Wikipedia page (last resort, mark `confidence='low'`).
   Record verbatim quote + URL + date. Prefer FTE; if total workforce
   includes a significant contractor population (DHS, NASA labs), record
   FTE in `total_headcount` and note the contractor count in `notes`.
2. **AI-eligible share.** Read the bureau's mission description. Exclude
   roles that are predominantly clinical, field, blue-collar, custodial, or
   shift-pattern, and write one-line rationale. Example exclusions:
   - VHA (VA): ~330k clinical/custodial staff → `ai_eligible_share=0.10`
   - USPS letter-carriers / mail handlers → `0.05`
   - CBP frontline officers + USCG enlisted → `0.10`
   - TSA TSO screening workforce → `0.05`
   - BLM/NPS field staff, USDA Forest Service field staff → `0.20`
   - TVA generation/transmission plant staff → `0.15`
   - DOE field-site / national-lab science staff → mixed; aim ~0.65 because
     researchers ARE LLM users
   For knowledge-work-heavy bureaus (OIT, OCIO, OGC, OCFO, OIG, OPM, GSA
   line offices, SBA program offices, FRB Board, FCC, FERC, NASA HQ),
   default `ai_eligible_share=0.85`.
3. Each row gets `wave='1'`, default `confidence='medium'`. Use `'high'`
   when both headcount source is OPM FedScope and eligible-share has a
   citable demographic breakdown; `'low'` when headcount comes from
   Wikipedia.

Output one JSON file per agent: `audit/research/agency_workforce/W1-<agent>.json`.

```json
{
  "captured_by": "W1-A",
  "captured_at": "2026-05-26T03:30:00Z",
  "rows": [
    {
      "organization_slug": "va",
      "level": "agency",
      "total_headcount": 470000,
      "headcount_as_of": "2025-09-30",
      "headcount_source_url": "https://www.va.gov/about_va/vahistory.asp",
      "headcount_source_title": "VA About — total workforce",
      "headcount_quote": "VA employs approximately 470,000 ...",
      "ai_eligible_share": 0.30,
      "ai_eligible_rationale": "~330k VHA clinical/custodial; ~140k OIT/VBA/NCA/admin",
      "ai_eligible_source_url": "https://www.va.gov/oig/pubs/...",
      "confidence": "medium",
      "wave": "1",
      "notes": "Excludes ~50k contractor positions reported in FY25 budget."
    },
    { "organization_slug": "va-vha", "level": "bureau", ... }
  ]
}
```

### Wave 2 — share-of-eligible per evidence row (2 agents)

For every row of `agency_ai_access_evidence`, agents populate:

- `estimated_share_of_eligible` REAL — starts from Wave-0 priors keyed by
  `coverage_assessment`. Adjusts upward when `exact_quote` or
  `estimated_users` cites a specific number (e.g., VA Microsoft Copilot
  `estimated_users="~100,000 of 470,000"` → set share to `100000 / (470000 *
  va_ai_eligible_share)`, not `100000/470000`).
- `matrix_product_key` TEXT — deterministic LIKE map of `tool_name` to one
  of `ms_copilot | github_copilot | chatgpt | claude | gemini | amazon_q |
  agency_built`. Mirrors `bucketsForProduct()` in
  `dashboard/lib/db/experience.ts`. Where no clean mapping exists, leave
  NULL.
- `share_rationale` TEXT — one sentence noting which evidence drove the
  value.

Partition: W2-A handles rows where `agency_abbreviation IN (top 18 by row
count)`, W2-B handles the rest.

### Wave 3 — QA + holes (1 agent)

Re-read every Wave-1 row with `confidence='low'`. Fill (agency, bureau)
rows the partition missed. Append `wave='3'` rows that supersede Wave 1
(latest wave wins — same convention as the 2024 tagging plan).

The dashboard view should resolve "canonical workforce profile per
organization" as: latest-wave row for that `organization_id`.

## Calibration before launch

This plan does NOT require a Wave-0-style calibration of the eligible-share
methodology across agents — Wave 0 calibrates priors numerically from
existing evidence, not from agent agreement. If Wave 1 outputs reveal
disagreement (e.g., agent says VHA is 0.10, another says 0.25 for the same
clinical staff), reconcile in Wave 3.

## Order of operations

```
   Wave 0 (priors)
         ↓
   Wave 1 (6 agents in parallel)
         ↓
   Wave 2 (2 agents in parallel)
         ↓
   Wave 3 (QA + holes)
         ↓
   apply_agency_workforce.py → agency_workforce_profile + access_evidence
         ↓
   Sync DB into dashboard/data/, deploy
```

The dashboard's `/experience` page already gracefully handles all rows
being NULL — today's band-midpoint estimate stays on screen until rows
land. So this can run unsupervised in the background.

## Out of scope

- Contractor-vs-FTE reconciliation across agencies.
- Eligible-share refinements based on occupational category beyond bureau.
- Re-tagging `use_case_tags` for 2024 rows (separate plan).
