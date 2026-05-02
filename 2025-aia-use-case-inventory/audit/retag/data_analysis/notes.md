# Methodology, limitations, and caveats — Analytic Platform mapping

## What "Strong / Moderate / Limited" means here

The question we're trying to answer is: *if you handed a senior agency analyst CUI / PII / FOUO data and asked them to use an LLM or ML model to produce a real analytical product (not a slide deck, not a chat answer), do they have a place to do that?*

Strong = yes, in production, today, used by real analysts, FedRAMP/equivalent authorized for the data class involved.
Moderate = yes for one bureau, or yes-but-still-rolling-out, or only for specific data types.
Limited / None = no — best they can do is Excel + Power BI + ad-hoc requests + GSA's chat sandbox.

## Method used

1. Token search across `use_cases` (`use_case_name`, `bureau_component`, `problem_statement`, `expected_benefits`, `system_outputs`, `system_name`, `vendor_name`, `training_data_description`, plus `raw_json`) for the platforms listed in the prompt — Databricks, SageMaker, Bedrock, Vertex, BigQuery, Azure ML, Microsoft Fabric, Synapse, Snowflake, Cortex, Palantir/Foundry, Domino, Anaconda, JupyterHub, Posit/RStudio, MLflow, Kubeflow, Azure OpenAI, Anthropic, LangChain, PyTorch/TensorFlow, Ray.
2. Token search for known custom-platform names (EDAV, 1CDP, IDAP, IDR, Mosaic, DNA-P, PFCS, NorthStar, ATAP, PANDA, FMAP, EDAPT, BIGMAP, CDW, RAAS, VINCI, HECC, NCCS, Biowulf, ORNL, LANL, INL, etc.).
3. Hand-read of every match to confirm it's a platform/environment claim rather than a passing reference. (Lots of "posit" / "jupyter" / "fabric" matches were noise — substring of "deposit", "production", or generic uses; filtered out.)
4. Public-source augmentation via web search:
   - CMS docs (cms.gov/tra Data_Management) for IDR Cloud & DataConnect.
   - hpc.nih.gov for Biowulf.
   - nas.nasa.gov/hecc for NASA HECC + Athena.
   - research.va.gov/programs/vinci for VINCI.
   - irs.gov/irm/part1/irm_01-001-018 for IRS RAAS.
   - gsa.gov for USAi launch and EDS.
   - Vendor case studies (Databricks-USDOT, Palantir-DHS $1B BPA, Palantir-USDA $300M).
5. Per-agency rating + confidence based on whether DB and public sources agreed.

## Why this dimension is genuinely hard

- **The M-25-21 inventory format is not designed to surface analytic platforms.** It captures use cases, not infrastructure. Agencies sometimes name the platform in `system_name`, sometimes in `vendor_name`, sometimes only in `problem_statement` narrative, sometimes nowhere. Two use cases on the same platform can look completely different in the export.
- **`deployment_environment` in `use_case_tags` is "unknown" on 100% of rows.** That field is unusable.
- **`architecture_type` is unknown on ~58.5% of rows.** Also unreliable for this question.
- **The consolidated COTS template (`consolidated_use_cases`)** is dominated by Microsoft Copilot, ChatGPT, Adobe, and GitHub Copilot. It does not surface analytic platforms. Of 192 consolidated entries, zero name Databricks, Snowflake, Palantir, SageMaker, Bedrock, Vertex, BigQuery, Foundry, or Domino in the `commercial_product` field. The COTS framing actively conceals this dimension.
- **Big agencies with massive analytic stacks have *underweight* representation.** DoD doesn't report under M-25-21 the way civilian agencies do — Advana, Project Maven, JWICS analytics, and service-level platforms aren't in this dataset. ODNI / IC similarly. So a naive read of the inventory understates the federal AI-on-data picture by an enormous amount.
- **The question "who has access" rarely surfaces in the data at all.** I made my best inference from bureau scoping (e.g., NREL only vs. all of DOE) but this is the weakest part of every row.

## Agencies where I genuinely couldn't get a clear answer

- **SEC / FRB / FDIC / NCUA / CFTC / CFPB.** Financial regulators almost certainly use Snowflake and/or Databricks (industry analyst reports + Federal Reserve job postings + OCC technology vendor lists). But the inventory rows don't surface platforms. I have rated them Limited based on direct evidence; if anything I am under-rating them.
- **Census Bureau.** Big modernization initiative (CenTAM) is in flight but the platform endpoint is TBD. Census also runs the Federal Statistical Research Data Centers (FSRDCs) which is a real CUI analyst environment for 1000+ researchers, but it's primarily an SAS/Stata environment, not LLM/ML — a different question than the one we're scoring.
- **Department of Labor.** Their 2025 AI Strategy mentions infrastructure but doesn't name a platform.
- **DOI's "Iris" data assistant.** The article-prompt mentioned this; I couldn't find a DOI tool by that name in either the inventory or DOI public materials. USDA has an unrelated app named "IRIS." If the article uses Iris-at-DOI as an example, verify before publication.
- **DOJ FBI.** Heavy operational use of Palantir (clear), but the inventory is heavily redacted ("Redacted for cybersecurity purposes") and the inventory undersells what's likely there.
- **Treasury sub-bureaus.** OCC, FinCEN, BFS, and Treasury Departmental Offices likely have stacks; only IRS RAAS comes through clearly.

## "This is the dimension we should be most humble about" — caveat for the article

If the article touches on which agencies are ready vs. not for serious data analysis with AI, please be careful with the following:

1. **Absence of evidence is not evidence of absence in this inventory.** A "Limited" rating means *we couldn't find it in the inventory and a quick web pass*, not that the agency has no analyst platform. Especially true for financial regulators and IC-adjacent components.
2. **A Palantir / Databricks contract is not the same as broad analyst access.** The DHS $1B Palantir BPA and the USDA $300M Foundry contract sound like agency-wide capabilities; in practice they are operational case-management platforms with a small number of authorized power users. The ratings in `by_agency.md` try to reflect actual analyst access, but this is fuzzy.
3. **GSA's USAi (Aug 2025) is a real shared-service equalizer for chat-based use cases.** It is *not* an analyst data-pipeline environment, despite some press coverage that conflates the two. Don't credit small agencies with USAi as if it solves the analytic-platform question.
4. **The Strong-rated agencies are Strong because of *components*, not departments.** "HHS is Strong" really means "CDC is strong, CMS is strong, NIH is strong, ACF has Palantir." A broad department-level claim of strength masks enormous variance — a CDC epidemiologist has a wildly different toolset than an OASH policy analyst even though both work for the same Secretary.
5. **The OMB inventory format will keep underselling this dimension** until the template asks "what platform did you use?" as a structured field. That's the single biggest reform that would let an analysis like this be done with confidence.
6. **Be careful with vendor case studies.** Databricks, Palantir, and Snowflake federal-customer pages are partial sources of truth — they list customers but rarely scope or scale, and they have an obvious incentive to claim broad usage.

## Reproducibility

Every row in `by_row.csv` cites either a `db_row_<id>` (look up via `sqlite3 data/federal_ai_inventory_2025.db "SELECT * FROM use_cases WHERE id = <id>"`) or a public URL pattern referenced in `by_agency.md`. The DB was not modified at any point.

## Time spent

~75 minutes. Of that, ~30 minutes on DB token search and noise filtering, ~25 minutes on web augmentation for the bigger agencies, and ~20 minutes on writing this analysis up.
