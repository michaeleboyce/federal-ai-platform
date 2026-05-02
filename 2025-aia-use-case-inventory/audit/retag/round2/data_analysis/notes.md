# Round-2 retag — data-analysis platform mapping

## Scope

Resolving the ambiguous rows from `audit/retag/data_analysis/by_row.csv`:

- Slice A: `confidence='Low'` — 11 rows
- Slice B: `deployment_environment='unknown'` — 29 rows (Slice A is a subset of Slice B)

Note: the `9656-9658` line in `by_row.csv` is a NASA Airport Surface Models range covering 3 distinct DB rows (NASA-21, NASA-22, NASA-23), so the resolved CSV has 31 rows rather than 28. This is the correct expansion.

## Method

1. Pulled `system_name`, `vendor_name`, `problem_statement`, `system_outputs`, `training_data_description` for every row from `data/federal_ai_inventory_2025.db` (read-only).
2. For rows where the narrative explicitly named a cloud (eMAMR → "Databricks and AWS S3"; Hydrology Copilot → "Azure AI Search/Foundry + Synapse"; LMGSS scripting → "Google Gemini") I took that as ground truth.
3. For rows where the narrative was thin or redacted, I applied the agency cloud-posture inference rules from round 1's `notes.md` and ran one targeted web search per ambiguous case (logged in `searches.csv`).

## Agency-cloud inferences I applied (and the reason)

These are public-knowledge inferences, not from the inventory text. Treat them as moderate-confidence, NOT canonical:

- **DHS / CBP** → AWS GovCloud. CBP runs the ACE/CACE AWS Cloud East FedRAMP-Moderate environment; ATAP draws on those source systems. Confirmed via DHS major-systems list.
- **DOJ enterprise analytics** → AWS GovCloud. Databricks at DOJ runs FedRAMP High on AWS GovCloud (per Databricks press release).
- **DOJ eDiscovery (8702)** → marked `fedramp_high_il5` because the narrative names BOTH Relativity One (Azure Gov) and Everlaw (AWS GovCloud) as candidates. Cannot disambiguate — the agency genuinely hasn't picked.
- **DOT FHWA** → AWS GovCloud. DOT's department-wide Databricks rollout (Databricks-USDOT case study referenced in round-1 notes) is on AWS GovCloud; PANDA at Turner-Fairbank is part of that.
- **State Department** → Azure Gov for non-Palantir analytics. State is an Azure-first agency; Databricks at State runs on Azure Gov; NorthStar likewise.
- **Treasury / OCC / IRS** → Azure Gov for GenAI chatbots and assistants. Treasury Cloud is heavily Azure-leaning for LLM workloads (Azure OpenAI in Azure Gov). IRS TP360 is consistent with this.
- **NIH NBSC** → AWS GovCloud. NIH Business System Cloud is AWS-based; H2O.ai's h2oGPTe deploys natively on AWS GovCloud.
- **HRSA** → AWS GovCloud. HRSA Data Warehouse modernization on AWS.
- **FDA HFP analytic platforms (DICE)** → AWS GovCloud (best guess). FDA uses both AWS and Azure Gov; HFP/CARTS/CARA platforms are AWS-leaning per public references. Low confidence.
- **SEC** → AWS GovCloud. SEC's analytic stack (Snowflake/Databricks) runs FedRAMP High on AWS GovCloud per industry analyst reports.
- **SSA** → AWS GovCloud. SSA modernization is AWS-heavy; Informatica EDC instance is AWS-hosted.
- **NASA Aviation Systems Division** → on-prem (NASA HECC). Aviation ML (airport surface models) historically runs on NASA HECC at Ames.
- **NASA Earth Science (Hydrology Copilot)** → Azure Gov. Explicitly stated.
- **DOE NETL / labs** → on-prem HPC. DOE national labs run their own materials/research data platforms on lab HPC.
- **DOE enterprise CDW (7912)** → AWS GovCloud. Vendor=Databricks, system=cloud data warehouse → matches DOE BPA modernization on AWS GovCloud.
- **USDA EDAPT** → on-prem. PIA explicitly cites Cloudera Navigator/Manager on USDA-managed infrastructure.
- **USDA Forest Service GeoPlatform (BIGMAP)** → on-prem. USFS GeoPlatform with Esri ArcGIS Enterprise.
- **GSA pilot (9131)** → AWS GovCloud. GSA enterprise is AWS-heavy.

## Rows I could NOT resolve

| use_case_id | agency | use_case_name | why |
|---|---|---|---|
| 9040 | FHFA | Neural Networks for FMAP | FHFA white paper does not name a cloud; FHFA is too small to have a publicly documented cloud posture. `searched_no_source=1`. |

Marginal calls (kept "filled" but flagged Low confidence in the CSV): 7627 (DHS RAAS, redacted), 8205 (DOE NETL carbon ore), 8521 (DOJ DEA PenLink — vendor SaaS without confirmed gov-cloud), 8610 (DOJ Informatica), 9131 (GSA pilot), 9446 (FDA DICE), 9471 (HRSA chatbot), 10249 (DOS Predictive Analytics Platform — empty narrative), 10530 (USDA IRIS — empty narrative).

## Summary stats (final environments after resolution)

- aws_govcloud: 13
- azure_gov: 7
- on_prem: 7
- gcp_assured_workloads: 1
- saas: 1
- fedramp_high_il5: 1 (DOJ eDiscovery — cannot disambiguate)
- unknown: 1 (FHFA FMAP)

## Caveats for downstream consumers

- These resolutions are best-guess inferences for rows where the agency's own narrative was silent. A "filled" decision with Low confidence is a real candidate for human reviewer override.
- The DB was NOT modified. Only `audit/retag/round2/data_analysis/{resolved,searches}.csv` and this notes file were written.
- The DOJ eDiscovery row (8702) is genuinely two-platform (Relativity Azure Gov + Everlaw AWS GovCloud). If a single-cloud tag is required downstream, use `azure_gov` as a slight lean (RelativityOne is the larger DOJ deployment historically), but `fedramp_high_il5` is the more honest tag.
- PenLink PLX (8521) is a vendor SaaS whose gov-cloud hosting was not publicly documented as of search. Marked `saas`; likely AWS GovCloud per general law-enforcement SaaS norms.
