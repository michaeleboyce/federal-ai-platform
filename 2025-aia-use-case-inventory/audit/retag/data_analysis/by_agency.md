# Federal Agencies — Analytic / AI-on-Data Environments

Scope: ready-to-use platforms where staff can ingest agency data into a notebook / SQL / ML pipeline and apply LLMs or ML to it. Not just "do you have ChatGPT" — that bar is too low for serious analysis on CUI/PII data.

Sources are a mix of:
- DB rows from `data/federal_ai_inventory_2025.db` (cited as `db_row_<id>`)
- Public agency / vendor documentation (cited as URL)
- GSA's USAi shared-service is a fallback for any participating agency (Aug-2025 launch), not a per-agency win.

Sorted by rating, then by likely scale of the environment.

| Agency | Rating | Platforms (vendor) | Network / Environment | User Population | Confidence | Key Evidence | Notes |
|---|---|---|---|---|---|---|---|
| **HHS** | Strong | CDC **EDAV** (Azure Synapse + Databricks Genie + Azure OpenAI) ; CDC **1CDP** & CDC **Model Studio** (Palantir Foundry/AIP) ; CMS **IDR Cloud** (Snowflake) ; CMS **CMCS DataConnect** (Databricks on AWS) ; ACF **Discover/Horizon/Upstream/Cares** (Palantir) ; NIH **IDAP** (Palantir Foundry) ; NIH **Biowulf** (105k-core HPC) | Azure Gov + AWS GovCloud + on-prem HPC | Thousands of analysts across CDC/CMS/NIH/ACF/HRSA/FDA | High | db_rows 9217-9300 (EDAV), 9226/9250/9316/9317 (1CDP+Model Studio), 9386/9387 (IDR Snowflake), 9563 (NIH IDAP), 9175-9197 (ACF Palantir); cms.gov/tra IDR docs; hpc.nih.gov | Multiple production analyst environments at component level — by far the deepest stack in CFO-Act civilian government. CDC's CFA Model Studio explicitly lets users containerize and deploy their own models. |
| **DHS** | Strong | FEMA **Mosaic** (Databricks-authorized workspace, ATO covered) ; **Palantir Federal Cloud Service / AIP** ($1B BPA renewed 2026) used by ICE/CBP/USCIS/CISA ; CBP **ATAP** (Advanced Trade Analytics Platform) ; USCIS uses **AWS Bedrock** ; CWMD **RAAS** | FedRAMP High, IL5 (PFCS Forward) ; AWS GovCloud | Multi-thousand across components | High | db_row_7497 (Mosaic Databricks), 7559/7589/7591 (Palantir CMA), 7607 (Bedrock USCIS), 7538 (ATAP); siliconangle DHS-Palantir $1B BPA; govconwire DHS Databricks BPA | Real CUI/LES analytic platforms; Palantir is dominant operationally but Databricks is dominant for enterprise data fabric. |
| **DOE** | Strong | Lab HPC at multi-exaflop scale: ORNL (**Frontier**), LANL (**Venado**, **Mission**, **Vision**), LLNL, INL, PNNL, NREL, BNL ; NNSA **DNA-P** (Palantir Foundry) ; PNNL **Databricks** ; LANL & LLNL **AWS** portals ; INL **HPC OpenAI-compatible API** ; NREL **Stratus** (AWS) + Azure ; SRS **Azure GOV** environment | On-prem HPC (incl. classified) ; Azure Gov ; AWS GovCloud | Tens of thousands of researchers across labs | High | db_rows 7912 (PNNL Databricks), 7960/8180 (NNSA DNA-P), 7952 (LANL AWS), 8124/8152 (LLNL), 8154 (INL HPC API), 7916/7928/7945/7946/7951/7957 (NREL); energy.gov NNSA Venado; insidehpc 3-lab federated learning | The richest analytic environment in the federal government, but mission-specific (science/weapons) — not exactly "give a senior policy analyst a notebook." |
| **NASA** | Strong | **HECC** with Pleiades, Aitken, Athena (Jan-2025) ; **NCCS** Discover + Prism GPU cluster ; IBM/NASA **Prithvi** foundation-model program ; some Synapse + Foundry use ; NAS Ames MLflow | On-prem HPC (FISMA-Mod) ; Azure | Thousands of NASA + partner researchers | High | db_rows 9810 (Prithvi), 9997 (Prism GPU cluster), 9684 (MERRAMax), 10037 (Foundry+Synapse), 9656-9658 (MLflow); nas.nasa.gov HECC; nas.nasa.gov NCCS Athena announcement | Heavily science-focused; weak on COTS LLM-on-CUI — but for data analysis at scale, world-class. |
| **State** | Strong | **Funhouse** (Microsoft + Databricks + ZenPoint, SBU-authorized analytic sandbox for data scientists) ; **CfA PFCS** (Palantir AIP) powering **StateChat** + Proving Ground ; CA **Predictive Analytics Platform** ; GPA **NorthStar** | Azure Gov (SBU) ; PFCS FedRAMP High | Department-wide for SBU; bureau-specific for PFCS | High | db_rows 10257 (Funhouse), 10262/10265 (PFCS+StateChat), 10249 (CA), 10277 (NorthStar) | Funhouse is one of the very few rows in the inventory that explicitly describes a *data-scientist sandbox*; State's Center for Analytics is the most analyst-coherent posture in the dataset. |
| **Treasury** | Strong | IRS **Compliance Data Warehouse (CDW)** + RAAS analytic environment (graph DB, embeddings, clustering) ; Palantir contract reported for IRS financial-crimes (Apr 2026) ; **OCC.InfoAssist** is a chatbot, not an analytic platform | On-prem + AWS for IRS CDW | RAAS division ~ hundreds of researchers/economists ; broader IRS exam staff for downstream | High | db_rows 10437/10453 (CDW use cases); irs.gov RAAS IRM 1.1.18; theintercept Palantir-IRS Apr 2026; arXiv 2509.16294 Treasury/IRS AI survey | Strong on tax research; weak public visibility into anything outside IRS RAAS. |
| **VA** | Strong | **VINCI** (HPC environment for VA research, mirrors CDW) ; **Corporate Data Warehouse (CDW)** with ~15M veteran records ; **Andesite** Bedrock SOC accelerator ; some Databricks (eMAMR) ; large VINCI ML user community | On-prem (VINCI) + AWS GovCloud | ~thousands of VA researchers + clinical informaticists | High | db_rows 10841 (CDW+eCaremanager), 10909 (CDW+CX), 10723 (Databricks), 10660 (Andesite Bedrock); research.va.gov/programs/vinci | VINCI predates the AI inventory entirely; it's the cleanest example of a long-running analyst platform that the OMB inventory under-represents. |
| **DOJ** | Moderate-Strong | **Palantir** (multiple components — ATR, EOUSA, FBI, ATF) ; **Databricks** at ATR for forecasting/predictive ; **Azure AI Foundry** for knowledge retrieval ; DEA **Intelligence Data Platform** (PenLink); Informatica CLAIRE | FedRAMP High / IL5 ; Azure Gov | Component-specific | High | db_rows 8474/8673 (Palantir), 8490 (Databricks ATR), 8684 (Azure OpenAI), 8521 (DEA IDP), 8642/8726 (Azure Foundry); fedscoop DOJ AI inventory | Strong analyst access at certain components (FBI, ATF, ATR); patchy across the rest. |
| **DOC** | Moderate | NOAA **Big Data Program** (AWS+Azure+GCP public cloud) ; NIST **HPC** (NIST research cluster) ; Census Bureau is modernizing via CenTAM (cloud + AI/ML) ; ITA used **AWS NLP** | AWS public cloud ; on-prem HPC | Bureau-by-bureau | Medium | db_row 7669 (ITA AWS), 7835 (NIST HPC); noaa.gov NCAI; noaa.gov Big Data | Decentralized: NOAA strong on public-data cloud, NIST strong on HPC, Census in-flight. No single department-wide analyst environment. |
| **DOI** | Moderate | USGS **Vertex AI Document Workbench** ; USGS **Azure OpenAI** ; DOI scientific-data platform (open metadata APIs) ; otherwise lots of small ML projects without a named environment | GCP Assured Workloads + Azure Gov | USGS bureau-specific | Medium | db_rows 8231 (Vertex), 8232 (Azure OpenAI); usgs.gov AI/ML CDI page | Real platform usage at USGS, but not yet department-wide. The "Iris" data-assistant the article prompt mentioned does not appear in the inventory rows for DOI; couldn't verify it exists at DOI under that name (USDA does have an unrelated "IRIS"). |
| **DOT** | Moderate | FHWA Turner-Fairbank **PANDA** (Databricks data-science lab) ; broader USDOT public Databricks customer story (FAA SWIM) ; FAA **Palantir Foundry** for COS event analysis ; Volpe ML/data-strategy work | Azure Gov / unknown | FHWA research center + select FAA programs | High | db_rows 8837 (PANDA Databricks), 8865 (FAA Foundry); databricks.com USDOT case study; highways.dot.gov PANDA pages | PANDA is genuinely a working data-science lab; not yet an enterprise platform. |
| **FTC** | Moderate | **Sentinel Network Services** + **Azure Databricks** + **Azure ML** + Analytic Sandbox | Azure Gov | BCP/DCRO + small bureau-wide | High | db_rows 9099-9114 (Sentinel suite, 9104 Sandbox, 9110 Databricks, 9113 Azure ML) | Small agency, but a notably coherent CUI consumer-protection analytic platform. |
| **HHS subnote** | (covered above) | — | — | — | — | — | (already strong) |
| **NSF** | Moderate | OCIO building **AWS Bedrock + SageMaker + Neptune + Comprehend** environment ; AWS Q + Bedrock for code | AWS GovCloud | OCIO + select RPPR researchers | High | db_rows 10087, 10097 (RPPR explicit AWS service request) | Earnest, in-flight; not yet department-wide. |
| **GSA** | Moderate | **USAi** shared-service (host for other agencies) ; internal **Enterprise Data Solution / D2D / AIOps** ; **AWS SageMaker** for security analytics | AWS GovCloud + GSA's USAi | GSA + 20+ partner agencies via USAi | High | db_row 9150 (SageMaker); gsa.gov/blog/usai launch; tech.gsa.gov AIOps; gsa.gov/about-us/newsroom/news-releases USAi launch | USAi is a chat-eval sandbox, not a data-analysis-on-CUI environment — be careful not to overstate it. |
| **USDA** | Moderate | **EDAPT** (Impala+Tableau) at REE ; **BIGMAP** (Esri GeoPlatform) at NRE ; massive Palantir Foundry contract ($300M, NFSAP, "One Farmer One File") signed for FSA/NRCS/RMA — work began 2025, full rollout by 2028 | TBD (Palantir) ; on-prem (EDAPT) | REE, NRE today; whole agency post-rollout | High | db_rows 10489 (EDAPT), 10554 (BIGMAP); orangeslices USDA-Palantir $300M | Today: moderate. Post-2026 rollout: likely Strong. |
| **SBA** | Moderate | **AWS Bedrock** (FedRAMP) for multi-agent orchestration | AWS GovCloud | OCIO | Medium | db_rows 10146/10147 | Real Bedrock usage but narrow scope. |
| **ED** | Moderate | FSA **EDMAPS** with AWS Bedrock multi-vendor model integration | AWS GovCloud | FSA | Medium | db_row 8886 | Federal Student Aid only; rest of ED weak. |
| **EPA** | Limited-Moderate | **AI-Work** (Azure OpenAI) ; uses GSA USAi ; no enterprise analytic platform surfaced | Azure Gov | OAR/agency-wide for chat | Medium | db_rows 8956/8963; epa.gov AI Strategy Plan 2025 | Chat-based; no Databricks/Snowflake/SageMaker analyst environment found. |
| **DOL** | Limited | Azure OpenAI + AWS general use ; "real-time dashboards, drift detection, alerts" mentioned in 2025 AI strategy ; uses USAi | Azure Gov + AWS | OCIO | Medium | db_row 8778; dol.gov AI Strategies 2025 | Strategy promises infrastructure but no analyst platform identified. |
| **HUD** | Limited | Mostly Skillsoft + M365 ; no analytic platform | unknown | n/a | Low | db_row 9630 | Smaller, no platform surfaced. |
| **OPM** | Limited | Enterprise BI w/ "embedded ML and AI" claim (vendor unclear) | unknown | OPM-wide | Low | opm.gov OCIO Enterprise IT Initiatives | Plausible but no named platform. |
| **SSA** | Limited | **Informatica EDC** (cataloging) ; SSA AI inventory CSV public ; otherwise predictive models on legacy systems | unknown | Limited | Medium | db_row 10227; ssa.gov inventory CSV | Heavy in actuarial/disability ML in legacy mainframe context, not a modern analyst environment. |
| **SEC** | Limited | DERA + OCDO doing semantic-layer/NL query work ; no named platform | unknown | DERA economists | Low | db_row 10184 | SEC has data scientists but inventory doesn't surface their stack. |
| **FDIC** | Limited | Standard COTS template only ; no analytic-platform mention | n/a | n/a | Low | consolidated only | |
| **FRB** | Limited | (Reports as independent) — no platform mention in inventory | n/a | n/a | Low | DB has 38 use cases but none platform-named | Federal Reserve undoubtedly has heavy data-science infrastructure (FED Snowflake/Hadoop/SAS Viya widely reported), just not in this inventory. |
| **FHFA** | Limited | **FMAP** (FHFA Modeling Analytics Platform) — internal | unknown | DHMG | Medium | db_row 9040 | Small but real. |
| **TVA** | Limited | No platform mention | n/a | n/a | Low | | |
| **NRC** | Limited | No platform mention | n/a | n/a | Low | | |
| **NARA** | Limited | NARA chat tool only | n/a | n/a | Low | db_row 9644 | |
| **GPO / NTSB / CFPB / CFTC / NCUA / OPM / EXIM / NMB / NEH / FERC / FRTIB / Peace Corps / EAC / FCC / OSC / PBGC / USTDA / CSOSA / EEOC / FLRA / USCCR / FTSC / CPSC / GAO / USITC / NSF (small) / USAID / USAGM / Presidio Trust / NLRB** | Limited / None | M365 Copilot / ChatGPT / GSA USAi only | n/a | n/a | Low | consolidated COTS template entries only | These are the agencies who would need GSA's USAi or another shared service to do anything beyond Excel. |
| **USAID** | Limited | First federal agency to adopt **ChatGPT Enterprise** ; otherwise no analytic platform | SaaS | agency-wide chat | Medium | fedscoop OpenAI-USAID | Chat ≠ analytic platform. |
| **DoD** (non-reporting in this inventory) | Strong | **Advana** (CDAO enterprise data + analytics platform) ; **Project Maven** (AI/CV/LLMs at NGA) ; service-level AFRL/ARL HPC ; JWICS-side IC-GovCloud analytics | Multi (IL5/IL6, classified networks) | Hundreds of thousands | High (public knowledge) | media.defense.gov Advana 2026 paper; wikipedia Project Maven; defensescoop coverage | Outside this inventory; included for completeness. |
| **ODNI / IC** (non-reporting) | Strong | IC-GovCloud + IC-CCC ; CIA's Osiris/Palantir | Classified networks | IC-wide | High (public knowledge) | | Outside scope of M-25-21 reporting. |

## Confidence-rating summary

- **High** — DB row plus ≥1 independent public source, OR multiple consistent DB rows with explicit platform names and ATO/system context.
- **Medium** — DB row alone with strong implication, OR public source with weak DB corroboration.
- **Low** — Single mention, or strong inference but no direct evidence.

---

## Sub-agency rollup (round-3)

Sub-agency view for AI data-analysis platforms, derived from per-bureau use-case counts and the round-3 review (96 sub-agencies, see `audit/retag/round3/data_analysis/`). Cabinet departments and independent agencies are kept at the parent table above; the rows below are bureaus, labs, centers, and offices within them. Sub-agencies with <5 use cases are excluded as below the data-quality threshold.

### Within HHS (11 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [National Institutes of Health (NIH)](/agencies/hhs-nih) | Strong | IDAP (Palantir Foundry) \| Biowulf (105k-core HPC) \| NBSC (H2O.GPTe) \| NIH Grants Virtual Assistant | NIH researchers / grants reviewers / 1000s | high | db env-rows: 5 NIH rows incl. IDAP fedramp_high_il5 + on_prem SEER + GCP NBSC + AWS GovCloud; hpc.nih.gov Biowulf | Multiple named analytic environments; leading maturity tier; subtree env_count=5 |
| [Centers for Disease Control and Prevention (CDC)](/agencies/hhs-cdc) | Strong | EDAV (Azure Synapse + Databricks Genie + Azure OpenAI) \| 1CDP (Palantir Foundry/AIP) \| Model Studio | CDC epidemiologists / data scientists agency-wide | high | db env-rows: 5 CDC rows incl. 1CDP fedramp_high_il5 (4x) + EDAV azure_gov w/ Databricks | The deepest analyst stack in civilian government per by_agency.md; subtree env_count=5; leading tier |
| [Centers for Medicare and Medicaid Services (CMS)](/agencies/hhs-cms) | Strong | IDR Cloud (Snowflake) \| CMCS DataConnect (Databricks on AWS) | CMS analysts / contractors | high | by_agency.md db_rows 9386/9387 IDR Snowflake; CMS OIT subtree env_count=2 | Inherits Strong from parent + own CMS-OIT env tags; large user base across CMS programs |
| [Administration for Children and Families (ACF)](/agencies/hhs-acf) | Strong | Palantir Discover/Horizon/Upstream/Cares | ACF program analysts | high | by_agency.md db_rows 9175-9197 ACF Palantir | Foundation env_count=0 but parent rollup explicitly names ACF Palantir suite as Strong; inheriting |
| [Office of Information Technology (CMS) (OIT)](/agencies/hhs-cms-oit) | Strong | IDR Cloud \| CMCS DataConnect \| CEDAR | CMS-wide IT and data engineers | high | db env-rows: 2 IDR Cloud rows on aws_govcloud (GDIT) | CMS OIT is the operator of the CMS analytic platforms; env-tagged in DB |
| [Food and Drug Administration (FDA)](/agencies/hhs-fda) | Moderate | Custom In-House AI \| (covered by HHS Anthropic for chat) | FDA reviewers | low | foundation: subtree env_count=1; named_tools mostly Custom In-House | FDA does not name a public analytic platform in its rows; relative to peer HHS components weaker — Moderate floor |
| [Center for Consumer Information and Insurance Oversight (CCIIO)](/agencies/hhs-cms-cciio) | Moderate | (Inherits CMS IDR/DataConnect) | CCIIO actuaries | low | parent CMS rollup | No own env rows; CMS-wide platforms presumably available |
| [Health Resources and Services Administration (HRSA)](/agencies/hhs-hrsa) | Moderate | PRB (AWS GovCloud) \| inherits HHS chat | HRSA program staff | medium | db env-rows: 2 HRSA aws_govcloud rows incl. PRB GDIT | Real AWS GovCloud platform but small scope; not an enterprise analyst sandbox |
| [Center for Drug Evaluation and Research (CDER)](/agencies/hhs-fda-cder) | Limited | Custom In-House AI | CDER reviewers | low | foundation: 0 env rows; only Custom In-House + Teams | No named platform; CDER analytic work likely sits on FDA stacks but not surfaced |
| [Office of Communications (CMS) (OC)](/agencies/hhs-cms-oc) | Limited | GitHub Copilot | n/a | low | foundation: only GitHub Copilot | Coding tool not analytic platform |
| [Agency for Healthcare Research and Quality (AHRQ)](/agencies/hhs-ahrq) | Limited | — | AHRQ researchers | low | foundation: only Microsoft Teams | No platform surfaced |

### Within DHS (7 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [U.S. Immigration and Customs Enforcement (ICE)](/agencies/dhs-ice) | Strong | Palantir Federal Cloud Service / AIP \| Case Management & Analytics (CMA) | Investigations / case-management staff | high | 3 env-tagged rows: PFCS + CMA (FedRAMP High/IL5) | Foundation named_tools confirms Palantir AIP; named CMA is the core ICE operational analytic platform |
| [Federal Emergency Management Agency (FEMA)](/agencies/dhs-fema) | Strong | Mosaic (Databricks workspace) | FEMA mitigation/grants analysts | high | db env-row: Mosaic-authorized Databricks workspace inheriting Mosaic ATO; govconwire DHS Databricks BPA | Foundation named_tools includes Databricks; Mosaic is the named CUI analytic platform |
| [U.S. Customs and Border Protection (CBP)](/agencies/dhs-cbp) | Moderate | ATAP (Advanced Trade Analytics Platform) \| Palantir CMA (via DHS BPA) | Trade & targeting analysts | medium | db_row_7538 (ATAP AWS GovCloud); siliconangle DHS-Palantir BPA | ATAP confirmed in DB on aws_govcloud; CBP also covered by DHS-wide Palantir CMA |
| [U.S. Citizenship and Immigration Services (USCIS)](/agencies/dhs-uscis) | Moderate | AWS Bedrock (Claude) \| ELIS | USCIS adjudication/IT staff | medium | db env-row: USCIS ELIS on aws_govcloud with Claude/Anthropic | Bedrock-on-Anthropic deployment exists; not yet a broadly-used analyst sandbox |
| [Transportation Security Administration (TSA)](/agencies/dhs-tsa) | Limited | — | n/a | low | foundation pack: only Microsoft Teams; no env-tagged rows | No analytic platform surfaced; vendor list is detection/identity tooling not analyst environments |
| [Management Directorate (MGMT)](/agencies/dhs-mgmt) | Limited | — | n/a | low | foundation pack: LIGER + Microsoft Defender; no analytic env | No analyst data-platform; named tools are management/security |
| [Cybersecurity and Infrastructure Security Agency (CISA)](/agencies/dhs-cisa) | Limited | — | CISA cyber analysts (likely on parent stacks) | low | foundation pack: 0 named tools; 0 env rows | No platform surfaced; CISA likely uses Splunk/Palantir at parent level but not in inventory |

### Within DOE (17 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Los Alamos National Laboratory (LANL)](/agencies/doe-lanl) | Strong | LANL HPC (Venado | Mission | Vision) \| AWS GovCloud portal | LANL researchers/weapons program | high |
| [Pacific Northwest National Laboratory (PNNL)](/agencies/doe-pnnl) | Strong | Databricks (R&D User) \| PNNL HPC | PNNL R&D researchers | high | db env-row: PNNL Databricks on aws_govcloud | Foundation named_tools confirms Databricks; named explicitly in by_agency.md as DOE Strong example |
| [Idaho National Laboratory (INL)](/agencies/doe-inl) | Strong | INL HPC OpenAI-compatible API (api.hpc.inl.gov) \| on-prem HPC | INL researchers | high | db env-row: api.hpc.inl.gov on_prem with OpenAI API | Internal LLM-on-HPC service is unusually mature; explicit named system |
| [Oak Ridge National Laboratory (ORNL)](/agencies/doe-ornl) | Strong | Frontier (exascale HPC) \| OLCF | ORNL/OLCF researchers nationally | high | by_agency.md ORNL Frontier; widely public | Inventory subtree env_count=0 but Frontier is the largest exascale HPC in the federal portfolio; treating as Strong on public knowledge |
| [Lawrence Livermore National Laboratory (LLNL)](/agencies/doe-llnl) | Strong | LLNL HPC \| AWS GovCloud | LLNL researchers (incl. classified) | high | db env-row: LLNL AWS GovCloud Multiple/AWS; by_agency.md LLNL | Public knowledge of LLNL ASC-class HPC; even thin inventory rows include AWS GovCloud ATO |
| [National Renewable Energy Laboratory (NREL)](/agencies/doe-nrel) | Strong | Stratus (AWS) \| NREL Azure System | NREL energy researchers | high | db env-row: NREL Stratus + NREL Azure System on on_prem_plus_azure; by_agency.md NREL | Named system + named systems with on-prem+Azure ATO context |
| [Argonne National Laboratory (ANL)](/agencies/doe-anl) | Strong | Argonne ALCF (Aurora exascale) | ALCF researchers nationally | medium | by_agency.md ANL ALCF; widely public | Inventory subtree only 5 rows but ALCF Aurora is exascale-class; like ORNL, inventory undercounts |
| [National Nuclear Security Administration (NNSA)](/agencies/doe-nnsa) | Strong | Decision and Analytics Platform (DNA-P) (Palantir Foundry) | NNSA mission users | high | db env-rows: 2 DNA-P rows on fedramp_high_il5; energy.gov | Strong despite low subtree count: explicit named Foundry deployment with FedRAMP High/IL5 ATO |
| [Brookhaven National Laboratory (BNL)](/agencies/doe-bnl) | Moderate | On-prem HPC (HEP/cosmic frontier ML) | BNL physics researchers | medium | db env-rows: 2 on_prem rows; problem statements describe HPC-AI for HEP | Real HPC use but not a generic analyst sandbox; mission/science specific |
| [Fermi National Accelerator Laboratory (FNAL)](/agencies/doe-fnal) | Moderate | On-prem scientific computing | Fermilab researchers | low | foundation: Custom In-House AI; by_agency.md does not single out FNAL | HEP computing scale is real but inventory rows are thin |
| [National Energy Technology Laboratory (NETL)](/agencies/doe-netl) | Moderate | NETL on-prem HPC | NETL energy R&D staff | medium | db env-row: 1 on_prem row | Named on-prem env in inventory; small scale |
| [SLAC National Accelerator Laboratory (SLAC)](/agencies/doe-slac) | Moderate | SLAC HPC / scientific computing | SLAC physicists | low | foundation: Splunk/Crowdstrike/ServiceNow/Copilot | SLAC undeniably has scientific computing infra; inventory rows don't surface it; conservatively Moderate |
| [Savannah River Site (SRS)](/agencies/doe-srs) | Limited | — | n/a | low | foundation: only Tabnine (coding); 0 env rows | No analytic platform surfaced; SRS is operationally focused |
| [Office of Environmental Management (EM)](/agencies/doe-em) | Limited | — | n/a | low | foundation: Azure OpenAI + GitHub Copilot only | Chat/coding not analytic; no platform surfaced |
| [Naval Reactors (NR)](/agencies/doe-nr) | Limited | — | n/a | low | foundation: ServiceNow + M365 Copilot only | No analytic platform; mission is reactor engineering |
| [Office of Energy Efficiency and Renewable Energy (EE)](/agencies/doe-ee) | Limited | — | n/a | low | foundation: 0 named tools | No platform surfaced (NREL is separate row) |
| [Office of Legacy Management (LM)](/agencies/doe-lm) | Limited | LMGSS (Gemini) | LM staff | medium | db env-row: LMGSS gcp_assured_workloads with Gemini | Single small Gemini deployment; not an analyst data platform |

### Within NASA (7 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Goddard Space Flight Center (GSFC)](/agencies/nasa-gsfc) | Strong | NCCS Discover + Prism GPU cluster \| HECC partner \| Prithvi (IBM/NASA) | GSFC Earth-science researchers + partners | high | db env-rows: 3 GSFC rows incl. Prism GPU cluster on_prem + azure_gov; by_agency.md NASA | Largest subtree in dataset (227); leading tier; Prism GPU cluster explicitly named; world-class HPC |
| [Jet Propulsion Laboratory (JPL)](/agencies/nasa-jpl) | Strong | JPL Supercomputing \| JPL on-prem science computing | JPL mission scientists/engineers | medium | foundation env_count=0 but JPL operates large mission-data systems publicly known | JPL inventory rows undersell its computing footprint; rated Strong on public knowledge of mission data infra |
| [Ames Research Center (ARC)](/agencies/nasa-arc) | Strong | HECC (Pleiades | Aitken | Athena) \| NAS MLflow | Ames + agency-wide HPC users | high |
| [Marshall Space Flight Center (MSFC)](/agencies/nasa-msfc) | Moderate | VEDA-LLM \| Custom In-House AI | MSFC Earth-science staff | medium | db env-row: 1 on_prem Custom In-House; problem statement references VEDA + Microsoft LLM | Real Earth-science AI work but not a generic analyst environment |
| [Langley Research Center (LaRC)](/agencies/nasa-larc) | Moderate | LaRC research computing \| Lessons Learned Bot | LaRC researchers | low | foundation: 0 named tools; 0 env rows | Real research computing exists but inventory thin; conservative Moderate |
| [Johnson Space Center (JSC)](/agencies/nasa-jsc) | Limited | — | JSC mission staff | low | foundation: Azure OpenAI + Gemini chat only | Chat tools not analytic platform |
| [Glenn Research Center (GRC)](/agencies/nasa-grc) | Limited | Custom In-House AI | GRC researchers | low | foundation: only Custom In-House AI | No named platform |

### Within DOJ (11 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Antitrust Division (ATR)](/agencies/doj-atr) | Strong | Databricks \| Azure OpenAI / Azure AI Foundry | ATR economists & litigators | high | db env-rows: ATR Databricks on aws_govcloud + Azure OpenAI on azure_gov; db_row_8490 per by_agency.md | Two distinct named platforms with env tags; ATR has the most coherent analyst stack in DOJ outside FBI |
| [Federal Bureau of Investigation (FBI)](/agencies/doj-fbi) | Moderate | Palantir (likely) \| inventory heavily redacted | FBI investigative analysts | low | by_agency.md DOJ Palantir at multiple components; inventory rows redacted | Almost certainly has Palantir at scale per public reporting; can't independently verify in subtree because rows are redacted; Moderate as floor |
| [Drug Enforcement Administration (DEA)](/agencies/doj-dea) | Moderate | DEA Intelligence Data Platform (PenLink PLX) | DEA intelligence analysts | high | db env-row: DEA SaaS PenLink PLX; db_row_8521 per by_agency | Named analytic platform with vendor; SaaS deployment limits scope vs. on-prem CUI |
| [Bureau of Alcohol Tobacco Firearms and Explosives (ATF)](/agencies/doj-atf) | Moderate | Palantir (FedRAMP High/IL5) | ATF investigators | medium | db env-row: ATF Palantir on fedramp_high_il5 (system redacted) | FedRAMP High Palantir tagged in DB despite redaction |
| [Civil Division (CIV)](/agencies/doj-civ) | Moderate | Unspecified FedRAMP-High/IL5 platform | DOJ Civil litigators | low | db env-row: 1 fedramp_high_il5 row (unnamed) | Some IL5 environment exists in CIV's subtree but unnamed |
| [Federal Bureau of Prisons (FBOP)](/agencies/doj-fbop) | Limited | — | n/a | low | foundation: WellSaid + Photoshop only | No analytic platform; tools are content/media |
| [U.S. Marshals Service (USMS)](/agencies/doj-usms) | Limited | AWS Textract | USMS staff | low | foundation: AWS Textract (OCR service) | Textract is feature-level not analyst environment |
| [Justice Management Division (JMD)](/agencies/doj-jmd) | Limited | — | n/a | low | foundation: 0 named tools | No platform surfaced |
| [Tax Division (TAX)](/agencies/doj-tax) | Limited | AWS Transcribe | n/a | low | foundation: AWS Transcribe | Transcribe is a feature not a platform |
| [Organized Crime Drug Enforcement Task Forces (OCDETF)](/agencies/doj-jmd-ocdetf) | Limited | — | n/a | low | foundation: 0 named tools | No platform surfaced |
| [Office of Justice Programs (OJP)](/agencies/doj-ojp) | None reported | — | n/a | low | foundation: 0 named tools; minimal maturity | Nothing in inventory |

### Within DOC (6 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [National Oceanic and Atmospheric Administration (NOAA)](/agencies/doc-noaa) | Moderate | NOAA Big Data Program (AWS+Azure+GCP) \| NCAI emerging | NOAA scientists across line offices | medium | by_agency.md NOAA BDP; noaa.gov NCAI page | Despite 157 use cases no env-tagged rows in subtree; scale and scientific workload imply real platforms not surfaced in inventory format |
| [National Institute of Standards and Technology (NIST)](/agencies/doc-nist) | Moderate | NIST research HPC cluster | NIST researchers | medium | db_row_7835 (NIST HPC) per by_agency.md | HPC environment exists but inventory has only 7 rows in subtree; under-reported |
| [U.S. Census Bureau (Census)](/agencies/doc-census) | Limited | — | Census IT/data scientists | low | foundation pack: 0 named tools; CenTAM modernization in flight per by_agency.md | No platform surfaced in inventory; FSRDCs is SAS/Stata not LLM/ML |
| [U.S. Patent and Trademark Office (USPTO)](/agencies/doc-uspto) | Limited | — | USPTO examiners (use Claude in chat) | low | foundation pack: Claude + ServiceNow Now Assist | Claude usage is chat-based; no analytic platform surfaced; one targeted web search returned nothing useful |
| [International Trade Administration (ITA)](/agencies/doc-ita) | Limited | — | n/a | low | foundation: ChatGPT+Claude only; by_agency notes ITA used AWS NLP previously | No current named analytic platform |
| [National Telecommunications and Information Administration (NTIA)](/agencies/doc-ntia) | None reported | — | n/a | low | foundation: 0 named tools; 0 env rows | Nothing in inventory |

### Within Treasury (5 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Internal Revenue Service (IRS)](/agencies/treasury-irs) | Strong | Compliance Data Warehouse (CDW) \| RAAS analytic environment | IRS RAAS researchers + exam staff | high | db env-rows: 3 IRS rows on_prem_plus_aws + azure_gov; irs.gov RAAS IRM 1.1.18; theintercept Palantir-IRS | CDW/RAAS is one of the longest-running analyst environments; explicit hybrid env tags |
| [Office of the Comptroller of the Currency (OCC)](/agencies/treasury-occ) | Moderate | OCC.InfoAssist (Azure Gov) \| unnamed in-house AI | OCC bank examiners | medium | db env-row: 1 OCC azure_gov | Real Azure Gov chat/analysis env; by_agency.md notes InfoAssist is a chatbot not a full analyst platform — Moderate not Strong |
| [Office of Financial Research (OFR)](/agencies/treasury-ofr) | Moderate | Custom In-House AI | OFR economists | low | foundation: Custom In-House AI; OFR known publicly to use Snowflake/HPC | OFR has financial-data analytic infra publicly known but inventory rows thin |
| [Bureau of the Fiscal Service (BFS)](/agencies/treasury-bfs) | Limited | — | BFS staff | low | foundation: only N/A vendors | No platform surfaced |
| [Bureau of Engraving and Printing (BEP)](/agencies/treasury-bep) | None reported | — | n/a | low | foundation: 0 named tools; minimal maturity | Nothing in inventory |

### Within VA (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Veterans Health Administration (VHA)](/agencies/va-vha) | Strong | VINCI (CDW research environment) \| Rockies (Databricks + Azure ML) | VA researchers + clinical informaticists | high | db env-row: VHA aws_govcloud Databricks + on_prem; research.va.gov/programs/vinci; govciomedia VA Rockies Databricks | Largest VA subtree (253); leading-research analyst environment predates inventory; strong public + DB evidence |
| [Office of Information & Technology (VA) (OIT)](/agencies/va-oit) | Strong | Andesite (Bedrock SOC accelerator) \| Rockies/Databricks operational | VA OIT operations + SOC | high | db env-rows: 2 VA OIT rows aws_govcloud + on_prem; db_rows 10723 + 10660 per by_agency.md | Leading maturity tier; VA OIT operates the Rockies platform powering VHA research |
| [Veterans Benefits Administration (VBA)](/agencies/va-vba) | Limited | — | VBA claims staff | low | foundation: 0 named tools; 0 env rows | No analytic platform surfaced; VBA claims processing is rules-engine driven |

### Within DOI (6 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [U.S. Geological Survey (USGS)](/agencies/doi-usgs) | Strong | Vertex AI Document Workbench \| Azure OpenAI | USGS bureau-wide / Energy Resources Program | high | db env-rows: 2 USGS rows (gcp_assured_workloads + azure_gov); by_agency.md USGS | Two distinct cloud analytic environments tagged; large subtree (187 rows); foundation tools list confirms ChatGPT + ArcGIS AI |
| [U.S. Fish and Wildlife Service (FWS)](/agencies/doi-fws) | Limited | — | n/a | low | foundation: 0 named tools; 0 env rows | No platform surfaced |
| [Bureau of Reclamation (BOR)](/agencies/doi-bor) | Limited | — | n/a | low | foundation: minimal; 0 env rows | No platform surfaced |
| [Bureau of Land Management (BLM)](/agencies/doi-blm) | Limited | — | n/a | low | foundation: 0 named tools | No platform surfaced |
| [Office of Natural Resources Revenue (ONRR)](/agencies/doi-onrr) | None reported | — | n/a | low | foundation: 0 named tools; minimal maturity | Nothing in inventory |
| [Bureau of Safety and Environmental Enforcement (BSEE)](/agencies/doi-bsee) | None reported | — | n/a | low | foundation: 0 named tools | Nothing in inventory |

### Within USDA (5 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Research Education and Economics (REE)](/agencies/usda-ree) | Strong | EDAPT (Impala + Tableau) | REE / ERS / NASS economists | high | db env-row: REE EDAPT on_prem (Accenture); by_agency.md db_row_10489 | Named REE-wide analytic platform; supports researchers across REE mission area |
| [Natural Resources and Environment (NRE)](/agencies/usda-nre) | Moderate | BIGMAP (Esri GeoPlatform) \| Esri ArcGIS AI on-prem | NRE / Forest Service / NRCS | high | db env-row: NRE on_prem Esri; by_agency.md db_row_10554 BIGMAP | Geospatial analytic platform with explicit on-prem BPA + Esri AI |
| [Farm Production and Conservation (FPAC)](/agencies/usda-fpac) | Limited | — | FSA/NRCS/RMA staff | medium | foundation: 0 named tools; by_agency.md notes USDA-Palantir $300M Foundry signed 2025 for FPAC NFSAP | Today: Limited (rollout starting). Post-2026: likely Strong once NFSAP/One-Farmer-One-File goes live |
| [Marketing and Regulatory Programs (MRP)](/agencies/usda-mrp) | Limited | On-prem (small) | MRP staff | low | db env-row: 1 unnamed on_prem | Single weak env row; no named analyst platform |
| [Food Safety (FoodSafety)](/agencies/usda-foodsafety) | Limited | — | FSIS staff | low | foundation: 0 named tools | No platform surfaced |

### Within State (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Bureau of Consular Affairs (CA)](/agencies/state-ca) | Strong | CA Predictive Analytics Platform | Consular fraud / visa analysts | medium | db env-row: 1 azure_gov; by_agency.md CA Predictive Analytics Platform | Named bureau platform with Azure Gov env; covered explicitly in parent rollup |
| [Bureau of Diplomatic Technology (DT)](/agencies/state-dt) | Strong | Funhouse (Microsoft + Databricks + ZenPoint) \| CfA PFCS (Palantir AIP) \| StateChat \| MED-PLTR | Department-wide SBU + bureau-specific PFCS | high | db env-rows: 4 DT rows: Funhouse azure_gov + 2 PFCS fedramp_high_il5 + MED-PLTR | One of the strongest analyst sandbox postures in the federal dataset; named in by_agency.md |
| [Foreign Service Institute (FSI)](/agencies/state-fsi) | Limited | — | FSI students/staff | low | foundation: 0 named tools; minimal maturity | No platform surfaced |

### Within DOL (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Bureau of Labor Statistics (BLS)](/agencies/dol-bls) | Limited | — | BLS economists | low | foundation: 0 named tools | BLS undoubtedly has SAS/Stata/Python analyst infra but nothing surfaced in M-25-21 |
| [Employment and Training Administration (ETA)](/agencies/dol-eta) | None reported | — | n/a | low | foundation: only N/A | Nothing in inventory |
| [Occupational Safety and Health Administration (OSHA)](/agencies/dol-osha) | None reported | — | n/a | low | foundation: 0 named tools | Nothing in inventory |

### Within SEC (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Office of the Chief Data Officer (SEC) (OCDO)](/agencies/sec-ocdo) | Moderate | Unspecified AWS GovCloud env \| Westlaw AI | DERA economists + OCDO | low | db env-row: 1 unnamed aws_govcloud; by_agency.md SEC DERA semantic-layer work | OCDO is the data office but inventory rows are vague; semantic-layer/NL query work referenced |
| [Office of Information Technology (SEC) (OIT)](/agencies/sec-oit) | Limited | — | SEC IT | low | foundation: 0 named tools | No platform surfaced |
| [Division of Examinations (EXAMS)](/agencies/sec-exams) | Limited | — | SEC examiners | low | foundation: 0 named tools | No platform surfaced; SEC EXAMS likely uses internal Snowflake/SAS but not in inventory |

### Smaller parent agencies (10)

Parent agencies with fewer than 3 in-scope sub-agencies are summarized inline:

- **DOT → Federal Aviation Administration (FAA)** — Strong (high). Foundry/AIP confirmed in narrative; FedRAMP High env tag; FAA also is a Databricks public reference customer
- **DOT → Office of the Chief Artificial Intelligence Officer (CAIO)** — Limited (low). no platform/env signal in subtree
- **ED → Federal Student Aid (FSA)** — Strong (high). Named system + AWS GovCloud + Bedrock multi-model; explicitly the FSA analytic stack
- **SSA → Office of the Chief Information Officer (SSA) (OCIO)** — Moderate (medium). Real cataloging + code modernization stacks; not an analyst LLM-on-data sandbox
- **SBA → Office of the Chief Information Officer (SBA) (OCIO)** — Moderate (high). Real Bedrock usage with multiple frontier model providers; OCIO-scoped
- **FDIC → Division of Resolutions and Receiverships (DRR)** — Limited (low). No platform surfaced
- **FRB → Division of Supervision and Regulation (S&R)** — Limited (low). FRB known to use SAS Viya/Snowflake/Hadoop publicly but not in inventory; rated Limited per CHARTER absence-of-evidence rule
- **FHFA → Office of the Chief Information Officer (OCIO)** — Moderate (medium). Named modeling platform; small scale
- **FTC → Bureau of Consumer Protection (BCP)** — Strong (high). Coherent CUI consumer-protection analytic stack; foundation named_tools includes Leidos Sentinel
- **TVA → Information Technology (TVA) (IT)** — Limited (low). Coding/transcription tools not analytic platform
- **TVA → Power Operations (PO)** — None reported (low). no platform/env signal in subtree
- **EPA → Office of the Administrator (OFA)** — Limited (low). no platform/env signal in subtree

_Source: `audit/retag/round3/data_analysis/sub_agency_rows.csv` (96 rows). Methodology in `audit/retag/round3/data_analysis/notes.md`._
