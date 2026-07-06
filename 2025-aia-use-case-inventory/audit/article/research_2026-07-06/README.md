# Web-research evidence — 2026-07-06 scout passes

Sourced material gathered by the four research scouts (budget, FedRAMP,
integration, angles) on 2026-07-06. Every external fact in these files
carries a source URL; **access date for everything here = 2026-07-06**
unless a file says otherwise. Findings are synthesized (with caveats) in
`../claims_review_2026-07-06b.md`; this directory is the raw evidence.

| File | What it is | Primary sources |
|---|---|---|
| `angles_external_sources.md` | FedScope workforce sizing (DoD ≈ 772,549 civilians ≈ ⅓ of ~2.31M federal civilian workforce — corrects the old "~60%" note), IRS voicebot silently-dropped exemplar, retirement-reporting mechanism | OPM FedScope via Pew/USAFacts; irs.gov newsroom; FedScoop; GAO |
| `fedramp_enforcement_research.md` | 44 U.S.C. § 3613 verbatim ((e)(1) presumption of adequacy, (b) deficiency documentation, (e)(2)(B) demonstrable need) + the authorization-vs-enablement scoping analysis; live 20x trio re-check (each 1 authorization / 0 recorded reuses as of 2026-07-06); GAO anchors (GAO-24-106591, GAO-26-107530, GAO-20-126) | Cornell LII; fedramp.gov listings FR2533155773 / FR2604952026 / FR2604643715; gao.gov |
| `omb_2025_data_dictionary.md`, `omb_2025_reporting_instructions.md`, `omb_2025_data_sourcing_summary.md`, `omb_2025_data_standardization_report.md` | OMB's official 2025 inventory guidance materials (the per-field instructions; the "impracticable to require individualized reporting" concession; the 24 base + 9 high-impact field list; DoD/IC exclusions) | https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory (the full `guidance_2025_reporting_FINAL.pdf` was downloaded but is NOT committed — fetch from the repo above) |
| `gsa_fy2027_cj_usai_excerpts.md` | USAi/FCSF excerpts from GSA's FY2027 Congressional Justification: "15 pilot agencies with a substantial list … in the waiting list"; FY2027 cost-recovery transition; FCSF funding structure (full 14.4MB PDF not committed — URL inside) | gsa.gov |
| `query_usaspending.py`, `query_keywords.py`, `query_verify.py` | The exact USAspending API queries behind the FY2024–26 obligation figures (reproducible) | api.usaspending.gov |
| `usaspending_ai_vendors_raw.json` | Raw award results: Palantir $3.316B / 194 awards; per-vendor AI-adjacent obligations | USAspending API |
| `usaspending_keywords_raw.json` | Raw keyword-search line items: ChatGPT $2.2M (incl. the $1 FCC OneGov line), Copilot $1.5M, Claude $18,960, Gemini $0 | USAspending API |
| `toptier_agencies.json` | USAspending toptier agency reference used by the queries | USAspending API |

Statutory sunset note (verified 2026-07-06): Advancing American AI Act
§ 7225 requires inventories "continuously … for a period of 5 years" from
enactment 2022-12-23 → the mandate lapses **2027-12-23** (not 2028; the
last mandated inventory would *publish* early 2028).
Source: https://uscode.house.gov/view.xhtml?req=%28title%3A40+section%3A11301+edition%3Aprelim%29
