# Sub-agency rollups — Data Analysis dimension

## Method

For each of 96 sub-agencies in `_foundation/sub_agencies.json` I:

1. Read the foundation entry (`subtree_use_cases`, `subtree_env_count`, `named_tools`,
   `maturity_tier`).
2. Cross-checked the parent agency block in `data_analysis/by_agency.md`.
3. For sub-agencies with `subtree_env_count > 0`, ran a single bulk SQL
   query against `use_case_tags` joined to `use_cases` and
   `federal_organizations`, pulling `deployment_environment`,
   `tool_product_name`, `tool_vendor`, `system_name`, `vendor_name` for
   the relevant slugs. That single query covered ~44 high-signal slugs
   in one shot and provided the bulk of evidence.
4. Ran 4 web searches (logged in `searches.csv`) only for ambiguous
   cases: USPTO, FBI, NOAA, and VHA/VINCI confirmation.

I did not modify the DB. The bulk SQL output is the basis for nearly
every "Strong" or "Moderate" call where a named platform is cited.

## Rating distribution

- Strong: 29
- Moderate: 24
- Limited: 36
- None reported: 7

The Strong tail is heavier than I expected going in. Most of those are
HHS, NASA, DOE labs, DHS components, and State DT — places where the
foundation pack already named Databricks / Palantir / HPC clusters.

## Sub-agencies that earned higher than parent suggested

- **DOJ ATR (Antitrust Division)** — parent DOJ rated Moderate-Strong
  but ATR specifically has *both* Databricks (AWS GovCloud) and Azure
  OpenAI (Azure Gov) tagged in DB. ATR is the cleanest analyst stack
  in DOJ outside FBI's redacted footprint and arguably deserves Strong
  on its own.
- **FAA (within DOT)** — parent DOT rated Moderate, but FAA AIR is
  using Palantir Foundry/AIP per a use-case problem statement, plus
  FAA SWIM is a Databricks public reference customer. FAA reads as
  Strong; it pulls DOT's average up.
- **State DT** — parent State rated Strong as expected, but DT alone
  has *4* env-tagged rows (Funhouse + 3 PFCS deployments) in a
  12-use-case subtree. That density is unusual.
- **VA OIT** — leading maturity tier in foundation pack; operates the
  "Rockies" platform that includes Databricks + Azure ML and powers
  VHA research. The VA inventory undersells how concentrated VA's
  stack is in OIT.
- **NNSA** — only 5 use cases in subtree but DNA-P (Palantir Foundry)
  is FedRAMP High/IL5 and explicitly named twice. Strong despite low
  volume.

## Surprises and limitations

- **DOE labs split by mission, not by name brand.** ORNL, ANL, LANL,
  LLNL, NREL, PNNL, INL all earned Strong, but for different reasons
  (Frontier exascale at ORNL; Aurora at ANL; Venado at LANL; AWS
  GovCloud portals at LANL/LLNL; Databricks at PNNL; on-prem
  OpenAI-compatible API at INL; Stratus + Azure at NREL). Do not
  conflate them: a senior policy analyst at NREL has a *very*
  different stack than a weapons-program physicist at LANL.
- **CDC, NIH, CMS each individually earn Strong**, which is why HHS as
  a parent is Strong. The parent rating masks the fact that FDA at
  the same department only earns Moderate (no named analytic platform
  in its rows beyond "Custom In-House AI"). FDA's true posture is
  almost certainly higher than what the inventory shows; this is the
  single biggest "absence of evidence ≠ evidence of absence" in HHS.
- **FBI gets Moderate as a floor**, not because the evidence is strong
  but because the inventory is heavily redacted and public reporting
  on FBI Palantir use is extensive. A Limited rating would be wrong
  in the other direction.
- **FRB / SEC / FDIC / SBA financial-regulator pattern**: all rated
  Limited or None reported. As `notes.md` (round 1) warned, this
  almost certainly under-represents reality. I held the line because
  the CHARTER says rate from inventory + targeted web; I cannot
  verify a Snowflake/Databricks footprint at FRB from public sources
  alone.
- **USDA FPAC is rated Limited today** because the $300M Palantir
  Foundry contract for NFSAP / One-Farmer-One-File is in early
  rollout. By 2027 this will likely be Strong. Worth flagging for
  the article so the snapshot is dated accurately.

## Calls I'm least sure about

- USPTO Limited — likely under-rated; 15 inventory rows is too few to
  judge. One web search returned nothing useful.
- NOAA Moderate — 157 use cases but zero env-tagged rows. The Big
  Data Program is real but its analyst-access scope is unclear.
- JPL Strong — given on inventory thinness alone but JPL's mission
  computing is too well known to call Limited.
- SEC OCDO Moderate — DERA economists undeniably do quantitative work
  on CUI but the inventory rows are vague.

Word count: ~470.
