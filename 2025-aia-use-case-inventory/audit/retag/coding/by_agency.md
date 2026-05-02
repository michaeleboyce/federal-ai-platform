# Federal Agencies: AI Coding Assistant Authorization Rollup (2025)

**Source:** Agency-filed 2025 OMB M-25-21 inventories (47 source files, 36 reporting agencies) + targeted public-source corroboration.
**Scope:** Tools that help developers write/edit/review/test/translate code (GitHub Copilot, Amazon Q Developer, Gemini Code Assist, Tabnine, Cursor/Codeium/Windsurf, JetBrains AI, M365 Copilot for code, custom internal coding assistants). Excludes autocoders, classifiers, OCR, and low-code RPA.
**Ratings:** Enterprise/Broad — named tool authorized for most developers across the agency. Limited/Pilot — specific bureaus, labs, or pilots only. None reported — not in inventory or public materials. Unknown — conflicting evidence.
**Confidence:** High = ≥2 independent sources + DB consistent. Medium = DB + 1 source. Low = DB only or single weak source.

## Reporting agencies (have a 2025 M-25-21 filing in dataset)

Sorted by Rating (Enterprise → Limited → None → Unknown), then by approximate user reach.

| Agency | Rating | Tools (vendor) | Scope (orgs / users) | Confidence | Key Evidence | Notes |
|---|---|---|---|---|---|---|
| VA | Enterprise/Broad | GitHub Copilot (Microsoft/GitHub); Ansible Lightspeed (Red Hat/IBM watsonx); custom GenAI coding via VetsEZ | OIT-wide; ~7,000 OIT staff using GitHub, Copilot licenses with 30-day activity policy; VHA + VBA also using AI for code modernization | High | https://department-of-veterans-affairs.github.io/github-handbook/guides/onboarding/getting-copilot-access ; https://github.com/customer-stories/va ; https://department.va.gov/ai/building-the-future-vas-strategy-for-adopting-high-impact-artificial-intelligence-to-improve-services-for-veterans/ ; db_rows 10742, 10743 | VA's AI strategy explicitly names GitHub Copilot as a current pilot; VA-GitHub handbook governs Copilot access. Note: many VA inventory rows tagged with "Copilot" word are clinical (CT CoPilot etc.) — distinct. |
| DOC | Enterprise/Broad (across multiple bureaus) | GitHub Copilot (NOAA, BEA); Amazon Q Developer (NOAA); Gemini Code Assist (NOAA); custom assisted dev (USPTO) | NOAA + BEA + USPTO + Census; bureau-level rather than department-wide | High | db_rows 7643, 7804, 7819, 7828, 7829, 7697, 7678, 7863, 7657, 7802 | DOC has the broadest mix of named coding products of any agency in the dataset. BEA's "GitHub Copilot for Code Modernization" is the most named single deployment. |
| DOE | Limited/Pilot (national-lab-scoped, but very wide across labs) | GitHub Copilot (SLAC, WAPA, PNNL, Hanford); Tabnine (KCNSC, Savannah River); Anthropic Claude (PNNL pilot); ChatGPT Enterprise w/ code (INL); Gemini scripting (Legacy Mgmt); ORNL AI code review; Amazon Q AWS chat (LLNL) | At least 9 distinct national lab / power-marketing entities, each procuring independently | High | db_rows 7947, 8017, 8022, 8033, 8035, 8056, 8068, 8127, 8139, 8043, 8072, 8150, 8152 | DOE is the most fragmented agency. Each lab's M&O contractor procures separately, so this is "broad" in number-of-organizations but not "enterprise" by HQ authorization. Several labs have full deployment (WAPA Github Copilot deployed; SLAC pilot). |
| HHS | Limited/Pilot (multi-OpDiv) | GitHub Copilot (CMS POC); Pingwind AI DevOps (AHRQ); custom code-gen scripts (FDA, HRSA, NIH); ServiceNow Now Assist (CMS CCSQ); Notebooks Hub via OpenAI (NIH); Palantir Foundry pyspark (NIH NIDAP); CDC Palantir AIP (peripheral) | 6+ OpDivs (CMS, FDA, HRSA, NIH, AHRQ, CDC); mostly POCs and office-level | Medium | https://www.hhs.gov/programs/topic-sites/ai/use-cases/index.html ; db_rows 9355, 9450, 9472, 9561, 9563, 9580, 9206, 9333, 9339 | HHS's coding picture is messy because the inventory mixes real coding tools, autocoders (MedCoder, Stem Cell), and platform-help bots. Real coding presence is moderate but office-level rather than department-wide. |
| ED | Enterprise/Broad | OpenAI + Google Distributed Cloud (used for code across 11 program offices); M365 Copilot for code (Agency Wide) | OCIO + 10+ program offices specifically cite code-generation use; M365 Copilot agency-wide | Medium | db_rows 8889–8935 (11 rows), 8952 | ED's "Generative AI - Code Generation" template repeats across program offices with consistent language about generating Python/R/VBA/DAX/Excel code snippets. Plus a separate agency-wide M365 Copilot deployment for code. |
| DOJ | Enterprise/Broad (department-wide) | GitHub Copilot (Department-wide); legacy code modernization tools (Civil Division); FBI data-call code-assist | Listed as "Department wide" with vendors GitHub + Microsoft; not currently tagged as coding tool in DB | High | db_rows 8713, 8742, 8709 ; https://github.com/johnturek/GCCH-Copilot-Chat-Workshop/blob/main/DOJ/README.md (M365 Copilot Chat workshop) | DOJ's "Code Development" use case is explicitly Department-wide with GitHub + Microsoft as vendors and language matching GitHub Copilot ("real-time code completions based on comments and existing code"). Tag is missing in DB (one of the biggest false negatives). |
| SBA | Limited/Pilot | Amazon Q Developer; GitHub Copilot; Amazon Bedrock multi-agent for ColdFusion/COBOL refactoring; Google Gemini code generation | OCIO pre-deployment for both Q Developer and GitHub Copilot in parallel | High | db_rows 10140, 10141, 10146, 10135 | SBA is unusual — they're piloting Q Developer AND GitHub Copilot side-by-side in the same OCIO. Plus a bespoke Bedrock multi-agent system for legacy modernization. |
| SSA | Limited/Pilot | Windsurf (Codeium); IBM watsonx Code Assistant for Z + Broadcom Code for Z; AveriSource code modernization platform | OCIO pre-deployment; mainframe-modernization specific | High | db_rows 10231, 10232, 10228 | SSA picked Windsurf as their developer IDE coding assistant — the only agency in our dataset with Windsurf. Mainframe COBOL/IBM Z modernization is the bigger workstream. |
| Treasury | Limited/Pilot (multi-bureau) | Unspecified GenAI for code (OCC); BFS LLM chatbot/coding/code-translation POCs; IRS modular code assistant + AI-Augmented Software Modernization + Modernization Accelerator | OCC + BFS + IRS bureaus; mostly POC/pilot | Medium | db_rows 10373, 10391, 10395, 10396, 10399, 10444, 10449, 10472 | Treasury has lots of small entries with thin product naming ("N/A" vendor). Real coding-tool footprint exists but it's hard to tell how many real seats. IRS and BFS lead. |
| DHS | Limited/Pilot | FEMA OCFO Code Assist GPT (Azure OpenAI); CBP Source Code Development Tool; CBP CodeGen; ICE Palantir AIP developer tools; commercial GenAI for code (retired) | FEMA + CBP + ICE; bureau/component-level pilots | Medium | db_rows 7437, 7444, 7582, 7591, 7630 ; https://www.dhs.gov/ai/use-case-inventory/cbp | DHS's CBP has multiple pre-deployment custom coding assistants. FEMA OCFO has a deployed Azure-OpenAI-wrapped tool for SQL/Java/COBOL. No agency-wide GitHub Copilot evident in 2025 filing. |
| NSF | Limited/Pilot | AWS CodeWhisperer / Amazon Q / Bedrock | OCIO pre-deployment pilot | High | db_row 10087 | NSF's pilot explicitly evaluates AWS CodeWhisperer (now folded into Q Developer), Q, and Bedrock for developer tooling integration. |
| TVA | Limited/Pilot | GitHub Copilot | IT bureau | Medium | db_row 10330 | Single entry; product named directly. No public corroboration found. |
| DOI | Limited/Pilot | GitHub Copilot (BTFA bureau); ChatGPT for code optimization (USGS) | BTFA + USGS, office-level | Medium | db_rows 8451, 8241 | BTFA pilots GitHub Copilot for SDLC of DME and O&M apps. USGS earthquake/ground-motion code project uses ChatGPT. |
| NASA | Limited/Pilot | Goddard Code Assistant Pilot Study; XMM-GPT (FLAN-fine-tuned); IV&V Static Code AI plugin; HEASARC custom LLM for astrophysics code | GSFC center-level pilots; multiple separate efforts | Medium | db_rows 9852, 10047, 10053, 10021, 9798 (retired) | NASA has multiple in-development center-specific coding assistants but no enterprise GitHub Copilot deployment surfaced in inventory. White Sands prior code-review effort retired. |
| State | Limited/Pilot (retired or pre-deployment) | CodeGen (CA bureau, retired); Databricks Code Assistant (MGT, pre-deployment) | CA + MGT bureaus | Medium | db_rows 10251, 10283 | State's CodeGen (CA bureau) was retired; Databricks Code Assistant (MGT) is in pre-deployment. No GitHub Copilot or Q Developer in 2025 file. |
| EPA | Limited/Pilot | ESRI ArcGIS AI Assistants (generates Python/Arcade code) | OFA office | Medium | db_row 8955 | Only EPA coding-relevant entry is the ESRI AI Assistants (which produce Python/Arcade for GIS workflows). No GitHub Copilot or general developer assistant in 2025 file. |
| NLRB | Limited/Pilot | GitHub Copilot | 1–100 users (consolidated entry) | Low | db_consolidated_503 | NLRB's only mention is a consolidated-template Y for GitHub Copilot at 1–100 users. No individual narrative. |
| FDIC | Limited/Pilot | GitHub Copilot + Appian | 101–1000 users (consolidated entry) | Medium | db_consolidated_470 | FDIC's individual inventory does not surface any coding-tool entry, but the consolidated template marks GitHub Copilot + Appian Y at 101–1000. Suggests a real but quiet deployment. |
| FCC | Limited/Pilot | M365 Copilot + AWS Q Developer + Azure OpenAI | 101–1000 users (consolidated entry) | Medium | db_consolidated_450 | FCC's consolidated entry lists three products including Q Developer specifically. No individual narrative. |
| CSOSA | Limited/Pilot | Microsoft 365 Copilot AI (used for code) | 1001–5000 users (consolidated entry) | Low | db_consolidated_396 | CSOSA's consolidated template marks M365 Copilot for code Y at 1001–5000. Likely M365 Copilot's chat code feature, not a dedicated coding assistant. Treat as M365-incidental. |
| EAC | Limited/Pilot | ChatGPT, Claude, M365 Copilot, Perplexity (all listed) | 1–100 users (consolidated entry) | Low | db_consolidated_430 | EAC's small enough that this is plausibly individual-user-procured general-LLM access being used for code. Not a managed coding-tool deployment. |
| USITC | Limited/Pilot | Microsoft 365 Copilot | 1–100 users (consolidated entry) | Low | db_consolidated_553 | USITC marks M365 Copilot Y at 1–100 for code. Smallest possible footprint. |
| FRTIB | None reported (general M365 only) | — | — | Medium | db_row 9096 | FRTIB filed M365 Copilot for general agency business but no code-specific narrative. KEY_FINDINGS noted "zero coding" — confirmed for code-specific tools. |
| OPM | None reported (general M365 only) | — | — | Medium | db_row 10109 | OPM's M365 Copilot row says "summarization, drafting, and decision support" — no code use cited. |
| HUD | None reported | — | — | Medium | db_row 9627; db_consolidated_490 | HUD M365 Copilot row is "office productivity"; consolidated "Generating code" template marked N. |
| DOL | None reported | — | — | Medium | db_consolidated_411 | DOL's individual file is dominated by autocoders (BLS classification autocoders, NOT coding tools). Consolidated "Generating code" template blank. |
| OSC | None reported | — | — | Medium | db_consolidated_517 | "Generating code" template marked N. |
| PBGC | None reported | — | — | Medium | db_consolidated_537 | "Generating code" template marked N. |
| USTDA | None reported | — | — | Medium | db_consolidated_568 | "Generating code" template marked N. |
| USDA | None reported | — | — | Medium | db_row 10571 | USDA's only Copilot-named entry is Axon+ Copilot Studio chatbot (intranet RAG). No coding-tool entry in 2025 file. |
| FRB | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed; no public counter-evidence found. |
| FHFA | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| NARA | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| GPO | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| FERC | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| NRC | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| NTSB | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| NMB | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| NCUA | None reported | — | — | Low | DB has no coding-named entries | KEY_FINDINGS confirmed. |
| CFTC | None reported | — | — | Low | DB has no coding-named entries; only 3 inventory rows total | KEY_FINDINGS confirmed. |
| FTC | None reported | — | — | Low | db_row 9105 (excluded) | "Developer Productivity" Sentinel Network entry exists but narrative is too thin to call AI coding assistant — Leidos service contract. No code generation evidence. |
| GSA | None reported (developer-tool sense) | — | — | Medium | db_rows reviewed | GSA has multiple AI tools but none in 2025 file is a developer coding assistant. Their Software Supply Chain Security Research is a vulnerability-research tool, not a coding assistant. (Note: GSA runs USAi.gov but USAi is a customer-facing platform, not GSA's own developer tooling.) |
| DOT | None reported | — | — | Low | DB has no coding-named entries | No coding-named entries in 2025 file. |
| SEC | None reported | — | — | Medium | db_row 10184 | SEC's Semantic Layer NL Query is analyst-facing (write SQL without coding), not a developer coding assistant. |

## Non-reporting agencies (no 2025 inventory in dataset)

| Agency | Rating | Notes |
|---|---|---|
| DoD | Unknown (likely Limited) | EXEMPT from M-25-21 reporting. DoD has a Tradewind acquisition pathway used for AI/ML and components are independently piloting M365 Copilot via the Pentagon's GCC High deployment; specific GitHub Copilot enterprise deployments at the service level are reported but not consolidated publicly. |
| ODNI | Unknown | EXEMPT from M-25-21 reporting. |
| USAID | Unknown | Site down at last access. Agency wound down in 2025; remaining functions absorbed by State. |
| GAO | None reported | Legislative branch; exempt. No public coding-tool announcement. |
| EEOC | Unknown | Inventory NOT_FOUND for 2025. |
| CPSC | Unknown | Inventory NOT_FOUND for 2025. |
| CFPB | Unknown | ZERO_USE_CASES filed for 2025. |
| FLRA, MSPB, NEH, Peace Corps | None reported / Zero use cases | Filed zero-use-case statements. |
| PRC | Unknown | Inventory NOT_FOUND. |
| Presidio Trust, USAGM, USCCR | Unknown | 2024 filings only; not refreshed. |
| EXIM | None reported | Filed but ZERO_INDIVIDUAL_CASES. No consolidated-template Y for code. |

## Summary counts

- **Enterprise/Broad confirmed (in dataset):** VA, DOC, ED, DOJ — 4 agencies.
- **Limited/Pilot:** DOE (across many labs), HHS, SBA, SSA, Treasury, DHS, NSF, TVA, DOI, NASA, State, EPA, NLRB, FDIC, FCC, CSOSA, EAC, USITC — 18 agencies.
- **None reported:** FRTIB, OPM, HUD, DOL, OSC, PBGC, USTDA, USDA, FRB, FHFA, NARA, GPO, FERC, NRC, NTSB, NMB, NCUA, CFTC, FTC, GSA, DOT, SEC — 22 agencies (some with high confidence, some with low).
- **Unknown / non-reporting:** DoD, ODNI, USAID, EEOC, CPSC, CFPB, PRC, Presidio Trust, USAGM, USCCR, GAO, FLRA, MSPB, NEH, Peace Corps, EXIM.

---

## Sub-agency rollup (round-3)

Sub-agency view for AI coding tools, derived from per-bureau use-case counts and the round-3 review (96 sub-agencies, see `audit/retag/round3/coding/`). Cabinet departments and independent agencies are kept at the parent table above; the rows below are bureaus, labs, centers, and offices within them. Sub-agencies with <5 use cases are excluded as below the data-quality threshold.

### Within HHS (11 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [National Institutes of Health (NIH)](/agencies/hhs-nih) | Limited/Pilot | Notebooks Hub (OpenAI)\|NIDAP/Foundry Writing-code-using-AI\|Coding translation | Multiple NIH ICs; mix of deployed and pre-deployment | high | db_row_9561,db_row_9563,db_row_9580 | NIH has 3 distinct coding-specific use cases — not enterprise but real and broad. Maturity tier 'leading'. |
| [Centers for Disease Control and Prevention (CDC)](/agencies/hhs-cdc) | Limited/Pilot | CSB MCP AI (infrastructure code generation) | CDC infra admins; pre-deployment | medium | db_row_9307 | One pre-deployment infra-code generation tool. Despite 103 use cases and 'leading' maturity tier |
| [Centers for Medicare and Medicaid Services (CMS)](/agencies/hhs-cms) | Limited/Pilot | GitHub Copilot (WETG POC)\|ServiceNow Now Assist text-to-code\|CEDAR AI Workspace | CMS multi-office (OC/CCSQ/OIT); deployed + POC | high | db_row_9333,db_row_9339,db_row_9355 | Three coding-specific deployments across three CMS offices. GitHub Copilot still POC-level (not enterprise). |
| [Food and Drug Administration (FDA)](/agencies/hhs-fda) | Limited/Pilot | AI-Generated Data Processing and Visualization Code Development | FDA OCS office; pre-deployment | medium | db_row_9450 | FDA has one pre-deployment code-generation use case for Excel/PowerBI/dashboard code. No commercial coding assistant surfaced. |
| [Office of Information Technology (CMS) (OIT)](/agencies/hhs-cms-oit) | Limited/Pilot | CEDAR AI Workspace (Skyward Solutions) | CMS IT developers; deployed | medium | db_row_9333 | CEDAR is a custom code-assist deployed by Skyward — narrow CMS audience. |
| [Health Resources and Services Administration (HRSA)](/agencies/hhs-hrsa) | Limited/Pilot | Code Conversion for PowerBI Migration (unspecified vendor) | HRSA IT; pre-deployment | medium | db_row_9472 | Single PowerBI code-conversion use case. |
| [Office of Communications (CMS) (OC)](/agencies/hhs-cms-oc) | Limited/Pilot | GitHub Copilot (WETG POC) | CMS OC web team; POC | high | db_row_9355 | The single GitHub Copilot POC inside CMS is owned by OC. |
| [Agency for Healthcare Research and Quality (AHRQ)](/agencies/hhs-ahrq) | Limited/Pilot | Pingwind AI DevOps | AHRQ CFACT; pre-deployment | medium | db_row_9206 | Pingwind AI DevOps is the only AHRQ coding-specific entry. |
| [Center for Drug Evaluation and Research (CDER)](/agencies/hhs-fda-cder) | None reported | — | — | medium | — | CDER has 40 use cases but zero coding-specific. Surprising given size. |
| [Administration for Children and Families (ACF)](/agencies/hhs-acf) | None reported | — | — | low | — | No coding-tool entries. |
| [Center for Consumer Information and Insurance Oversight (CCIIO)](/agencies/hhs-cms-cciio) | None reported | — | — | low | — | No coding-tool entries. |

### Within DHS (7 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [U.S. Customs and Border Protection (CBP)](/agencies/dhs-cbp) | Limited/Pilot | Source Code Development Tool\|CodeGen (custom GenAI coding assistants) | CBP component-level pre-deployment pilots | medium | db_row_7437,db_row_7444 | Two pre-deployment custom in-house coding assistants. No GitHub Copilot or commercial coding product; generic LLMs (Gemini/Claude) listed in named_tools are not coding-specific. |
| [U.S. Immigration and Customs Enforcement (ICE)](/agencies/dhs-ice) | Limited/Pilot | Palantir AIP / Case Management & Analytics (AI-Powered Developer Tools) | ICE developers within CMA boundary; deployed | medium | db_row_7591 | Palantir AIP developer-assist (code suggestions |
| [Federal Emergency Management Agency (FEMA)](/agencies/dhs-fema) | Limited/Pilot | OCFO Code Assist GPT (Azure OpenAI/ReadyAI) | FEMA OCFO staff; deployed for SQL/Java/COBOL query gen | high | db_row_7582 | Bespoke Azure-OpenAI wrapper for query/code generation. Real coding-specific deployment. |
| [Transportation Security Administration (TSA)](/agencies/dhs-tsa) | None reported | — | — | medium | — | No coding-specific tool in TSA inventory; only Microsoft Teams generic mention. |
| [U.S. Citizenship and Immigration Services (USCIS)](/agencies/dhs-uscis) | None reported | — | — | medium | — | USCIS named_tools list (Claude) is generic-LLM access — fails the coding rule. |
| [Management Directorate (MGMT)](/agencies/dhs-mgmt) | None reported | — | — | medium | — | LIGER is document drafting (false positive in earlier tagging); no coding tool. |
| [Cybersecurity and Infrastructure Security Agency (CISA)](/agencies/dhs-cisa) | None reported | — | — | low | — | No coding-tool entries in CISA subtree. |

### Within DOE (17 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Pacific Northwest National Laboratory (PNNL)](/agencies/doe-pnnl) | Limited/Pilot | GitHub Copilot (with OpenAI Codex backend) | PNNL R&D users; deployed | high | db_row_7947 | Real GitHub Copilot deployment. Note OpenAI Codex backend is a developer product (counts). |
| [Savannah River Site (SRS)](/agencies/doe-srs) | Limited/Pilot | Tabnine | SRS Enterprise System Boundary; pre-deployment | high | db_row_8139 | Vendor explicitly Tabnine; pre-deployment but real procurement. |
| [Oak Ridge National Laboratory (ORNL)](/agencies/doe-ornl) | Limited/Pilot | AI Enabled Code Review (unspecified vendor) | ORNL pre-deployment | medium | db_row_8056 | Custom AI code-review tool — vendor not named. |
| [Office of Environmental Management (EM)](/agencies/doe-em) | Limited/Pilot | GitHub Copilot (Hanford Accreditation Boundary) | Hanford developers; deployed | high | db_row_8022 | Hanford GitHub Copilot — vendor named |
| [SLAC National Accelerator Laboratory (SLAC)](/agencies/doe-slac) | Limited/Pilot | GitHub Copilot | SLAC developers; pilot stage | high | db_row_8033 | Vendor explicitly GitHub/Microsoft; pilot stage. Round-1 confirmed. |
| [Office of Legacy Management (LM)](/agencies/doe-lm) | Limited/Pilot | Gemini (LMGSS scripting) | LM HQ; deployed for scripting | medium | db_row_8127 | Gemini used specifically for scripting — narrative confirms coding-specific primary use. Borderline (generic LLM) but qualifies under the explicit-coding-purpose carveout. |
| [Los Alamos National Laboratory (LANL)](/agencies/doe-lanl) | None reported | — | — | medium | — | LANL named_tools are M365 Copilot + ChatGPT — generic LLMs only. No coding-specific tool deployed despite 43 use cases. |
| [Idaho National Laboratory (INL)](/agencies/doe-inl) | None reported | — | — | medium | — | INL has ChatGPT Enterprise and Claude with code-generation narrative — generic-LLM rule excludes these as coding tools. |
| [Brookhaven National Laboratory (BNL)](/agencies/doe-bnl) | None reported | — | — | low | — | No coding-tool entries. |
| [Fermi National Accelerator Laboratory (FNAL)](/agencies/doe-fnal) | None reported | — | — | low | — | No coding-tool entries. |
| [National Energy Technology Laboratory (NETL)](/agencies/doe-netl) | None reported | — | — | low | — | No coding-tool entries. |
| [Lawrence Livermore National Laboratory (LLNL)](/agencies/doe-llnl) | None reported | — | — | medium | — | LLNL named_tools include ChatGPT/Azure OpenAI/Amazon Q/Claude — generic LLMs. Q is listed but no coding-specific Q Developer deployment is tagged. Generic-LLM rule excludes. |
| [Naval Reactors (NR)](/agencies/doe-nr) | None reported | — | — | low | — | Only M365/ServiceNow generic tools. |
| [Office of Energy Efficiency and Renewable Energy (EE)](/agencies/doe-ee) | None reported | — | — | low | — | No coding-tool entries. |
| [National Renewable Energy Laboratory (NREL)](/agencies/doe-nrel) | None reported | — | — | low | — | No coding-tool entries despite OpenAI API in named_tools. |
| [Argonne National Laboratory (ANL)](/agencies/doe-anl) | None reported | — | — | low | — | No coding-tool entries. |
| [National Nuclear Security Administration (NNSA)](/agencies/doe-nnsa) | None reported | — | — | low | — | Only ArcGIS AI (GIS classifier) — not a coding tool. NNSA's KCNSC Tabnine deployment is filed under KCNSC which isn't in the 96-list — recommend follow-up. |

### Within NASA (7 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Goddard Space Flight Center (GSFC)](/agencies/nasa-gsfc) | Limited/Pilot | Goddard Code Assistant (Custom LLM planned)\|IV&V Static Code AI plugin | GSFC center-level pilots; pre-deployment | high | db_row_10021,db_row_10047 | Two pre-deployment center-built coding tools. GSFC has 227 use cases and 'leading' maturity but no commercial coding assistant. |
| [Marshall Space Flight Center (MSFC)](/agencies/nasa-msfc) | None reported | — | — | low | — | No coding-tool entries. |
| [Jet Propulsion Laboratory (JPL)](/agencies/nasa-jpl) | None reported | — | — | low | — | No coding-tool entries — surprising given JPL's flight-software profile. |
| [Langley Research Center (LaRC)](/agencies/nasa-larc) | None reported | — | — | low | — | No coding-tool entries. |
| [Ames Research Center (ARC)](/agencies/nasa-arc) | None reported | — | — | low | — | Only ChatGPT generic-LLM access. |
| [Johnson Space Center (JSC)](/agencies/nasa-jsc) | None reported | — | — | low | — | No coding-tool entries; Azure OpenAI/Gemini are generic. |
| [Glenn Research Center (GRC)](/agencies/nasa-grc) | None reported | — | — | low | — | No coding-tool entries. |

### Within DOJ (11 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Civil Division (CIV)](/agencies/doj-civ) | Limited/Pilot | AI-assisted Legacy Code Modernization (unspecified vendor) | Civil Division attorneys/IT; pre-deployment | medium | db_row_8742 | Independent code-modernization workstream beyond DOJ-wide GitHub Copilot. |
| [Federal Bureau of Investigation (FBI)](/agencies/doj-fbi) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | FBI has no own coding-tool entries; DOJ filed 'Code Development' as Department-wide. Inherited rating dropped to low confidence per charter rule 1. |
| [Drug Enforcement Administration (DEA)](/agencies/doj-dea) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | Same as FBI — no own entries. OpenAI API named tool is generic. |
| [Bureau of Alcohol, Tobacco, Firearms and Explosives (ATF)](/agencies/doj-atf) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | No ATF-specific coding entries. |
| [Federal Bureau of Prisons (FBOP)](/agencies/doj-fbop) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | No own entries; WellSaid/Photoshop are not coding tools. |
| [U.S. Marshals Service (USMS)](/agencies/doj-usms) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | No own entries. |
| [Justice Management Division (JMD)](/agencies/doj-jmd) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | JMD is the DOJ-wide IT sponsor — actually the sponsor of the Department-wide row; reasonable to keep as Inherited rather than Enterprise since this is rollup-level. |
| [Tax Division (TAX)](/agencies/doj-tax) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | No own entries; AWS Transcribe is not coding. |
| [Organized Crime Drug Enforcement Task Forces (OCDETF)](/agencies/doj-jmd-ocdetf) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | No own entries. |
| [Antitrust Division (ATR)](/agencies/doj-atr) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | Databricks/Azure OpenAI/OpenAI API are analytics + generic LLM — not coding tools. |
| [Office of Justice Programs (OJP)](/agencies/doj-ojp) | Inherited | — | Covered by DOJ department-wide GitHub Copilot per inventory | low | db_row_8713 | No own entries. |

### Within DOC (6 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [National Oceanic and Atmospheric Administration (NOAA)](/agencies/doc-noaa) | Enterprise/Broad | GitHub Copilot\|Amazon Q Developer\|Gemini Code Assist | Multiple NOAA line offices — fisheries DevSecOps | OpenAPI dev | scientific software | high |
| [U.S. Census Bureau (Census)](/agencies/doc-census) | Limited/Pilot | Statistical package syntax development and debugging (unspecified vendor) | Census statisticians; narrow | medium | db_row_7657 | One coding-tagged use case for stats-package code; vendor unspecified. Likely small. |
| [U.S. Patent and Trademark Office (USPTO)](/agencies/doc-uspto) | Limited/Pilot | Assisted software development (unspecified vendor) | USPTO IT; limited scope | medium | db_row_7863 | Generic 'assisted software development' — vendor not named. Round-1 categorized USPTO as part of DOC's broad mix. |
| [International Trade Administration (ITA)](/agencies/doc-ita) | None reported | — | — | low | — | Only generic LLM (ChatGPT/Claude) named tools — fails coding rule. |
| [National Telecommunications and Information Administration (NTIA)](/agencies/doc-ntia) | None reported | — | — | low | — | No coding-specific entries. |
| [National Institute of Standards and Technology (NIST)](/agencies/doc-nist) | None reported | — | — | medium | — | Surprising absence — NIST has Grammarly + Gemini in named_tools |

### Within Treasury (5 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Internal Revenue Service (IRS)](/agencies/treasury-irs) | Limited/Pilot | Modular Code Assistant\|AI-Augmented Software Modernization\|Modernization Accelerator (retired) | IRS developers + modernization teams; deployed + pilot | high | db_row_10444,db_row_10449,db_row_10472 | IRS has the largest Treasury coding footprint with 3 distinct workstreams. Vendors mostly unspecified ('N/A'). |
| [Office of the Comptroller of the Currency (OCC)](/agencies/treasury-occ) | Limited/Pilot | Software Code Generation (unspecified vendor) | OCC bureau; pilot | medium | db_row_10373 | Single OCC coding pilot; vendor unnamed. |
| [Bureau of the Fiscal Service (BFS)](/agencies/treasury-bfs) | Limited/Pilot | LLM Chatbot for code POC\|FRB AI Code Translation POC | BFS; multiple POCs | medium | db_row_10395,db_row_10399 | Two BFS code-specific pilots. |
| [Office of Financial Research (OFR)](/agencies/treasury-ofr) | None reported | — | — | low | — | No coding-tool entries. |
| [Bureau of Engraving and Printing (BEP)](/agencies/treasury-bep) | None reported | — | — | low | — | No coding-tool entries. |

### Within VA (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Office of Information & Technology (VA) (OIT)](/agencies/va-oit) | Enterprise/Broad | GitHub Copilot\|Ansible Lightspeed\|VetsEZ Middleware Development | VA OIT — ~7000 OIT staff | high | db_row_10742,db_row_10743 | va-oit IS the enterprise locus: VA's department-wide GitHub Copilot deal + Ansible Lightspeed + VetsEZ middleware all sit here. Round-1 confirmed VA's enterprise rating originates here. |
| [Veterans Health Administration (VHA)](/agencies/va-vha) | Inherited | — | Covered by VA OIT-wide GitHub Copilot deal (~7000 OIT staff) | medium | db_row_10742,db_row_10743 | VHA has 253 use cases but zero own coding-tool entries. The VA OIT GitHub Copilot rollout is the relevant signal; VHA inherits per charter rule 1. |
| [Veterans Benefits Administration (VBA)](/agencies/va-vba) | Inherited | — | Covered by VA OIT-wide GitHub Copilot deal | low | db_row_10742 | VBA has no own coding-tool entries but VA's OIT-wide GitHub Copilot deal is described as broadly available. |

### Within DOI (6 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [U.S. Geological Survey (USGS)](/agencies/doi-usgs) | Limited/Pilot | ChatGPT (code optimization for earthquake/ground-motion code) | Single USGS science project; pilot | medium | db_row_8241 | Generic-LLM rule applies cautiously — narrative explicitly cites code optimization as primary purpose for this row. One project only despite 187 use cases. |
| [U.S. Fish and Wildlife Service (FWS)](/agencies/doi-fws) | None reported | — | — | low | — | No coding-tool entries. |
| [Bureau of Reclamation (BOR)](/agencies/doi-bor) | None reported | — | — | low | — | No coding-tool entries. |
| [Bureau of Land Management (BLM)](/agencies/doi-blm) | None reported | — | — | low | — | No coding-tool entries. |
| [Office of Natural Resources Revenue (ONRR)](/agencies/doi-onrr) | None reported | — | — | low | — | No coding-tool entries. |
| [Bureau of Safety and Environmental Enforcement (BSEE)](/agencies/doi-bsee) | None reported | — | — | low | — | No coding-tool entries. |

### Within USDA (5 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Natural Resources and Environment (NRE)](/agencies/usda-nre) | None reported | — | — | medium | — | Despite 76 use cases — NRE is dominated by ESRI ArcGIS AI (GIS classifier) — not coding. |
| [Research, Education, and Economics (REE)](/agencies/usda-ree) | None reported | — | — | low | — | No coding-tool entries. |
| [Farm Production and Conservation (FPAC)](/agencies/usda-fpac) | None reported | — | — | low | — | No coding-tool entries. |
| [Marketing and Regulatory Programs (MRP)](/agencies/usda-mrp) | None reported | — | — | low | — | No coding-tool entries. |
| [Food Safety (FoodSafety)](/agencies/usda-foodsafety) | None reported | — | — | low | — | No coding-tool entries. |

### Within State (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Bureau of Diplomatic Technology (DT)](/agencies/state-dt) | Limited/Pilot | Databricks Code Assistant | State MGT/DT; pre-deployment | medium | db_row_10283 | Per round-1 by_agency.md State has Databricks Code Assistant in MGT/DT pre-deployment. |
| [Bureau of Consular Affairs (CA)](/agencies/state-ca) | None reported | — | — | medium | db_row_10251 | CodeGen was retired per round-1. Counts as no active coding tool. |
| [Foreign Service Institute (FSI)](/agencies/state-fsi) | None reported | — | — | low | — | No coding-tool entries. |

### Within DOL (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Bureau of Labor Statistics (BLS)](/agencies/dol-bls) | None reported | — | — | medium | — | All 'code' entries in BLS are SOC/expenditure/SOII autocoders — explicitly excluded by charter. |
| [Employment and Training Administration (ETA)](/agencies/dol-eta) | None reported | — | — | low | — | No coding-tool entries. |
| [Occupational Safety and Health Administration (OSHA)](/agencies/dol-osha) | None reported | — | — | low | — | No coding-tool entries. |

### Within SEC (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Office of Information Technology (SEC) (OIT)](/agencies/sec-oit) | None reported | — | — | medium | — | SEC's Semantic Layer NL Query is analyst-facing (round-1 excluded). No developer coding assistant. |
| [Division of Examinations (EXAMS)](/agencies/sec-exams) | None reported | — | — | low | — | No coding-tool entries. |
| [Office of the Chief Data Officer (SEC) (OCDO)](/agencies/sec-ocdo) | None reported | — | — | low | — | Westlaw AI is legal research; no coding. |

### Smaller parent agencies (10)

Parent agencies with fewer than 3 in-scope sub-agencies are summarized inline:

- **DOT → Federal Aviation Administration (FAA)** — None reported (medium). Surprising absence given FAA IT modernization workload. SDRS JASC code-picker is an autocoder (excluded). No GitHub Copilot or commercial coding tool surfaced.
- **DOT → Office of the Chief Artificial Intelligence Officer (CAIO)** — None reported (medium). no coding-tagged use cases
- **ED → Federal Student Aid (FSA)** — Limited/Pilot (medium). One of 11 ED program offices filing the same code-generation template. ED parent is Enterprise/Broad; FSA is a program-office instance.
- **SSA → Office of the Chief Information Officer (SSA) (OCIO)** — Enterprise/Broad (high). SSA's whole coding posture is concentrated in OCIO — the only Windsurf in the dataset plus AveriSource for code modernization plus IBM/Broadcom mainframe code-assist.
- **SBA → Office of the Chief Information Officer (SBA) (OCIO)** — Enterprise/Broad (high). SBA OCIO is running Q Developer + GitHub Copilot in parallel plus a Bedrock multi-agent system for ColdFusion/COBOL refactoring. The richest coding-tool stack at office level.
- **FDIC → Division of Resolutions and Receiverships (DRR)** — Inherited (low). DRR has no own coding-tool narratives. FDIC consolidated entry suggests agency-wide footprint reaches DRR.
- **FRB → Division of Supervision and Regulation (S&R)** — None reported (low). No coding-tool entries.
- **FHFA → Office of the Chief Information Officer (OCIO)** — None reported (low). No coding-tool entries; ServiceNow Now Assist named tool is non-coding.
- **FTC → Bureau of Consumer Protection (BCP)** — None reported (low). Leidos Sentinel Network is a service contract — round-1 excluded as not a coding assistant.
- **TVA → Information Technology (TVA) (IT)** — Limited/Pilot (medium). TVA IT is the locus of TVA's GitHub Copilot deployment.
- **TVA → Power Operations (PO)** — None reported (medium). no coding-tagged use cases
- **EPA → Office of the Administrator (OFA)** — None reported (medium). no coding-tagged use cases

_Source: `audit/retag/round3/coding/sub_agency_rows.csv` (96 rows). Methodology in `audit/retag/round3/coding/notes.md`._
