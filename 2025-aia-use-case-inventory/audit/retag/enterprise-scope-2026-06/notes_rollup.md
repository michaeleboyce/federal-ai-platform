# Enterprise-scope correction pass — rollup (2026-06-09/10)

## Why

The "agencies with enterprise-wide GenAI" year comparison read **15 → 12** (a
decline). Investigation showed it was a tagging artifact in **both** directions:

1. **2024 undercount** — the 2024 tagger used a `department` deployment-scope
   value (17 GenAI rows) that was never mapped into `is_enterprise_wide`.
   Smoking gun: DHS "Commercial Generative AI for Text Generation" is the same
   use case both years — `department`/ew=0 in 2024, `enterprise_wide`/ew=1 in 2025.
2. **2025 undercount** — the tagger recorded the OWNING office (OCIO/MGMT) as
   the deployment scope for agency-wide tools. Web-verified mislabels included
   SSA's ASC (all employees, Apr 2025), StateChat (~45k users per State's
   M-25-21 compliance plan — the filing itself says "the Department's
   enterprise Generative AI-powered chatbot"), OPM ChatGPT/Copilot (all
   workers, Sept 2025, GSA OneGov $1 deal), and DHS-Chat (19k+ staff,
   10 components).
3. **2025 overclaims** — DOE's 12 "enterprise" rows were Savannah River *site*
   tools (the site's "Enterprise System Boundary" ≠ DOE-wide) or NNSA program
   rows; ED's FSA bureau products, SEC/NTSB office pipelines, FERC's role-scoped
   legal tool were also tagged enterprise.

## Definition applied

`enterprise_wide` = available to (nearly) the entire FILING AGENCY's workforce
(department-wide for departments). An OCIO *operating* a tool for the whole
agency is enterprise; an HQ office using a tool for its own work is not.
A site/center/lab (SRS, Goddard, the DOE labs) is a bureau-equivalent.
Role-scoped department-wide systems (DOJ Westlaw, DOI FBMS) count as
enterprise (reach spans the enterprise) — flagged in reasoning.

## Inputs / outputs (this directory)

- `2025_bureau_candidates.csv`, `2024_department_rows.csv`,
  `2025_enterprise_claims_nonHHS.csv` — extraction (pre-correction DB).
- `decisions_slice1.csv` (agent-reviewed, DHS/DOE/DOI/DOJ, 85 rows),
  `decisions_slice2.csv` (DOL→VA, 48 rows), `decisions_sweep.csv` (rows the
  OCIO filter missed — ED's "MS Copilot - *" ×13 with scope_detail literally
  "Agency Wide", FRTIB ×2, StateChat, DOT OST ×3 — plus reconciliation rows),
  `decisions_2024_department.csv` (17), `decisions_2025_claims.csv` (38).
  Every row carries reasoning + evidence URL where available.
- Apply: `scripts/apply_enterprise_scope_corrections_2026_06.py`
  (signature-resolved, idempotent, vocab-validating; ids never trusted from CSVs).

## Parallel-pass reconciliation

A sibling session applied an overlapping correction pass earlier the same
evening (commit `e495543`). Three-way diff (extraction vs sibling vs this
review) found: 68 clean applies, 4 sibling decisions accepted/normalized
(DOE Scripting→office, SBA Amazon Q→office, NSF TIP + NRC eval rows whose
`pilot` scope value is invalid 2025 vocab), 4 vocabulary normalizations of
sibling rows (`department` on 2025 rows → `enterprise_wide`: DOJ CoPilot,
FTC Copilot, SSA General Use Chatbot; OPM Claude kept enterprise per the
reach-vs-maturity rule), 1 substantive override (NASA ChatGSFC: center-wide ≠
agency-wide, same rule as SRS), and 3 sibling upgrades accepted with vocab
normalization (DOE EnerGPT, GSA Gemini, NASA-GPT — NASA-GPT low confidence).

## Result

|  | 2024 | 2025 |
|---|---|---|
| Agencies w/ enterprise-wide GenAI | 15 → **21** | 21 → **24** |
| Enterprise-wide GenAI use cases | 28 → **44** | 220 → **233** |

The published "15 → 12 decline" is an artifact — corrected: **21 → 24**, with
the 2025 growth concentrated (HHS 166 of 233) and the *character* shifting
from permissions/embedded-COTS (2024) to operated products (2025).

2024 top-10 agencies note: after correction, 6 of the 10 largest 2024 filers
had some enterprise GenAI; the "nine of ten had zero" line is retired. VA,
USDA, DOE were the large agencies at zero.

## Deferred

- Non-GenAI 2024 `department`-scope rows: not reviewed (same vocab gap likely).
- SBA "Employee Center AI Search" / "Employee Work Prioritization AI Agent" and
  TVA/Treasury TCSC rows: kept bureau on low confidence — revisit with evidence.
- NASA-GPT enterprise claim: low confidence, needs press/compliance-plan evidence.
- `use_case_tags.deployment_scope` vocab check constraint (prevent
  `pilot`/`department` regressions) — candidate migration.
