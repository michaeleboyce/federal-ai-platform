# General-Purpose FOUO/CUI LLM Assistants — By Agency

**Scope.** Each row covers a single reporting (or non-reporting) federal agency
and characterizes whether it has deployed a general-purpose chat assistant that
its workforce can use to ask arbitrary text questions, draft documents, summarize
material, etc., approved for FOUO/CUI work. Narrow chatbots over a single
dataset, helpdesk-only Copilots, and customer-facing public chatbots are
**excluded** even when present in the inventory.

**Rating scale**

- **Enterprise** — A named assistant available to most/all staff (>50% of workforce or "agency-wide"), FOUO/CUI authorized, externally verifiable.
- **Broad** — Department-wide or large fraction (10K+ users), or a federated model where major components have their own LLMs.
- **Limited** — Specific bureaus/components/pilots only.
- **None reported** — No general-purpose LLM in inventory or public materials.
- **Unknown** — Conflicting evidence.

**Confidence**: **High** ≥2 independent public sources + DB consistent. **Medium** DB + 1 public source. **Low** DB only or single weak source.

---

## Reporting Agencies (36)

Sorted by rating then by workforce size / scope.

| Agency | Rating | Assistant Name(s) | Platform | Est. Users / Scope | Confidence | Key Evidence | Notes |
|---|---|---|---|---|---|---|---|
| **State** | Enterprise | StateChat | Palantir + Azure OpenAI (GPT‑4o family) | ~45,000 active of ~75,000 (>95% of posts); 3M+ prompts | High | DB row 10265; [FedScoop](https://fedscoop.com/state-departments-ai-chatbot-mobile-app-cable-queries/); [State Enterprise Data & AI Strategy Sept 2025](https://www.state.gov/wp-content/uploads/2025/09/Department-of-State-Enterprise-Data-and-AI-Strategy.pdf) | Largest verifiable enterprise FOUO/SBU LLM deployment in the federal civilian space. Used in promotion-panel selection. DB tag `deployment_scope='bureau'` is **wrong**. |
| **VA** | Enterprise | VA GPT (primary); Ask Sage (pilot) | Not publicly disclosed (likely Azure/OpenAI variant) | ~95K–100K users onboarded (Dec 2024 → Jan 2026) | High | DB rows 10905, 10804; [FedScoop](https://fedscoop.com/va-generative-ai-tools/); [Military.com on OIG memo](https://www.military.com/benefits/veterans-health-care/vas-ai-tools-lack-patient-safety-oversight-watchdog-warns.html); [VA OIG advisory](https://www.vaoig.gov/reports/preliminary-result-advisory-memorandum/review-vhas-use-generative-artificial-intelligence) | OIG flagged that VHA authorized VA GPT and M365 Copilot Chat for use with PHI without National Center for Patient Safety coordination. DB scope is missing/wrong. |
| **DHS** | Enterprise | DHSChat (HQ + 10 components); ChatCBP, CISAChat, LIGER, PAiTH, ICE Enterprise AI Assistant (component-level) | DHSChat platform built in-house; LIGER on Azure OpenAI (GPT‑4o); CISAChat on Microsoft; bureau systems on Azure/Palantir | DHSChat: ~19,000 HQ + pilot users at 10 components | High | DB rows 7594, 7572, 7579, 7499, 7490, 7468; [Nextgov](https://www.nextgov.com/artificial-intelligence/2024/12/dhs-launches-internal-genai-chatbot-leverage-non-public-data/401733/); [HSToday](https://www.hstoday.us/federal-pages/dhs/dhs-launches-dhschat-a-secure-ai-powered-chatbot-to-enhance-internal-operations/); [FedScoop on commercial GenAI revocation](https://fedscoop.com/homeland-security-cuts-off-access-to-chatgpt-and-other-commercial-ai/) | Federated: DHSChat is the HQ-level enterprise tool; components run their own (CBP→ChatCBP, CISA→CISAChat, FPS→LIGER, USCIS→PAiTH, ICE→ICE Enterprise AI). All FOUO/CUI-authorized. DHS revoked commercial GenAI approvals to consolidate on DHSChat. |
| **HHS** | Enterprise | Claude for Government (department-wide); FDA Elsa; NIH ChIRP | Anthropic Claude (HHS-wide, OneGov $1); Elsa on Anthropic Claude in GovCloud; ChIRP on GPT‑4o/STRIDES Azure (also supports Claude) | HHS-wide for Claude+ChatGPT (Dec 2025 memo from Dep. Sec O'Neill). FDA: 11 centers, >70% staff use Elsa voluntarily. NIH: all NIH staff via VPN. | High | DB rows 9448 (Elsa), 9564 (ChIRP); [FedScoop on HHS rollout](https://fedscoop.com/hhs-rolls-out-claude-anthropic-ai-tool/); [Nextgov on Elsa](https://www.nextgov.com/artificial-intelligence/2025/06/fda-unveils-elsa-generative-ai-tool-staff/405761/); [NIH Catalyst on ChIRP](https://irp.nih.gov/catalyst/33/2/chirp-a-chatgpt-model-for-the-nih-intramural-community) | Highly federated. Three independent enterprise LLMs serve different parts of HHS plus a department-wide deal for Claude+ChatGPT layered on top. CDC, HRSA, ACF, CMS run additional narrow chatbots. **At risk:** Trump-era ban on Anthropic in federal agencies (announced Feb 2026) may disrupt HHS Claude rollout — see [Fierce Biotech](https://www.fiercebiotech.com/ai-and-machine-learning/hhs-bans-anthropics-claude-ai-tool-trump-seeks-full-government-blacklisting). |
| **DOT** | Enterprise | Ask Dottie ChatBot Capability; Enterprise Personal Productivity Assistant | Not publicly named (DOT compliance plan describes "secure enterprise AI" capability) | DOT-wide; Productivity Assistant marked "Deployed", Ask Dottie "Pre-deployment" | Medium | DB rows 8812, 8813; [DOT M-25-21 Compliance Plan](https://www.transportation.gov/sites/dot.gov/files/2025-10/DOT_AI_Strategy_Part_III-Compliance_Plan.pdf); [DOT AI page](https://www.transportation.gov/AI) | Two coupled capabilities: a department-wide productivity assistant (deployed) and the Ask Dottie chat capability (pre-deployment). FAA "LLM Document Search" entries (rows 8850–8857) are narrow per-policy systems and NOT counted as general LLM. |
| **GSA** | Enterprise | Enterprise Chatbot (GSAi); Gemini for Google Workspace; USAi.gov as consumer | GSAi (internal chatbot routing through OneGov-backed models); Gemini (Workspace deployment); USAi.gov is the cross-government suite GSA itself uses | GSAi: rolled from 150-pilot → 1,500 → all GSA employees during 2025 | High | DB rows 9147, 9146, 9171; [FedScoop on GSAi](https://fedscoop.com/gsa-generative-ai-tool-doge/); [GSA-Google Gemini OneGov press release](https://www.gsa.gov/about-us/newsroom/news-releases/gsa-google-announce-gemini-onegov-agreement-08212025); [FedTech on USAi.gov](https://fedtechmagazine.com/article/2025/12/tech-trends-2026-gsas-usai-platform-helps-agencies-act-ai-action-plan-perfcon) | GSA is unique: it built the federal-wide USAi.gov chat suite (now used by 15+ agencies) **and** runs its own internal GSAi for staff. |
| **OPM** | Enterprise | M365 Copilot Chat + ChatGPT-5 (both via OneGov); OPM Rexi (separate narrow HR chatbot, not counted) | Microsoft + OpenAI | OPM-wide rollout Sept 2025 to all staff | High | DB rows 10109, 10110, 10111; [FedScoop](https://fedscoop.com/opm-makes-copilot-chatgpt-available-workforce-onegov/); [Nextgov](https://www.nextgov.com/artificial-intelligence/2025/09/opm-adds-openai-its-employees-computers/408232/) | OPM Director Kupor announcement Sept 2025. Anthropic Claude is in sandbox only. OPM Rexi (row 10113) is a narrow HR-focused chatbot, **not** a general-purpose assistant. |
| **NARA** | Enterprise | Generative AI Solutions for Workplace Productivity (Gemini for Google Workspace) | Google | NARA-wide deployed | Medium | DB row 9632; [NARA AI inventory](https://www.archives.gov/data/ai-inventory) | Listed as "Deployed" in NARA inventory. NARA is on Google Workspace agency-wide. |
| **FRTIB** | Enterprise | Microsoft CoPilot (Agency Wide) | Microsoft | "Agency Wide" per inventory | Medium | DB row 9096 | Small agency (~200 staff). DB explicitly marks scope "Agency Wide" and stage "Deployed". |
| **NASA** | Broad / Federated | ChatGSFC (federated NASA-wide); NASA-GPT; ALTIRA (Langley); MSFC Copilot pilot; Anthropic Claude pilot at GSFC | LibreChat-based ChatGSFC; Anthropic Claude Sonnet 3.5 (GSFC + Langley); various | ChatGSFC: >7,000 NASA users across the agency | High | DB rows 9820, 9818, 9821, 9946; [Element 84 on ChatGSFC](https://element84.com/machine-learning/chatgsfc-building-composable-ai-tools-for-nasa-on-open-source-tooling/); [NASA-GPT page](https://www.nas.nasa.gov/SC24/research/project09.php); [FedScoop on Claude at NASA](https://fedscoop.com/nasa-chatbots-treasury-coding-opm-drafting-agencies-deployed-claude/) | Federated by center: GSFC built the most-adopted system (ChatGSFC). No single department-wide tool, but the LibreChat-based ChatGSFC has spread agency-wide. Anthropic ban risk (per FedScoop). |
| **DOE** | Broad / Federated | EnerGPT (HQ); Energy Wizard / ELM (NREL); LivChat (LLNL); ChatGPT Enterprise (LANL); SpyglassGPT (Naval Reactors); ChatSRS (Savannah River); MauroGPT/FuelGPT/Chatlab (INL); MerlinChat (KCNSC); plus Microsoft 365 Copilot at PNNL/ORNL/LANL/INL/SLAC/WAPA/SLAC | Federated: Google Gemini (HQ via Accenture); OpenAI/Azure (LLNL, LANL, NREL); Anthropic (PNNL, LLNL pilots before ban); Microsoft Copilot (lab IT) | At least 8 named systems across HQ + 10+ national labs | High | DB rows 7919, 7951, 7945, 7954, 7906, 7922, 8027, 8040, 8043, 8063, 8068, 8089, 8113, 8124, 8132, 8155, 8159, 8167, 8186, 8187, 8191; [DOE 2025 AI Strategy](https://www.energy.gov/sites/default/files/2025-09/EXEC-2025-010630%20-%20250923_%20DOE%20AI%20Strategy%20VFinal.pdf); [DOE AI inventory](https://www.energy.gov/cet/doe-ai-use-case-inventory) | DOE's structure means each lab has its own "general LLM." HQ has EnerGPT (Google Gemini via Accenture) and EnerGPT Canvas. No single department-wide tool — most extreme example of federation in federal civilian space. |
| **SSA** | Broad | Agency Support Companion (ASC); General Use Chatbot (M365 Copilot Chat) | OpenAI via Microsoft (ASC); M365 Copilot Chat (general pilot) | ASC rolled out April 2025 to SSA employees; Copilot Chat in pilot | High | DB rows 10226, 10238; [Nextgov on ASC rollout](https://www.nextgov.com/artificial-intelligence/2025/04/ssa-rolling-out-new-chatbot-employees/404658/); [SSA AI page](https://www.ssa.gov/ai) | ASC explicitly designed as the agency-wide general-purpose chatbot. Distinct from SSA's narrow tools (Therapy Chatbot, HR Chatbot, Vocational Assessment Tool) which we exclude. |
| **DOJ** | Broad | DOJ CoPilot (Department-wide pre-deployment); component pilots: Internal chatbot (OIG), Policy Chatbot (FBI), DEA OpenAI chatbot, ATR Generative AI Test (Harvey/OpenAI/Perplexity) | M365 Copilot (Dept-wide); various commercial models for components | DOJ CoPilot pre-deployment; multiple component pilots already running | Medium | DB rows 8594, 8608, 8670, 8717, 8732; [FedScoop on DOJ inventory](https://fedscoop.com/justice-department-artificial-intelligence-ai-surveillance-inventory-predictive-technology-algorithm-bias/); [FedScoop on DOJ IT service desk](https://fedscoop.com/justice-department-exploring-generative-ai-to-overhaul-it-service-desk/) | DB row 8594 lists "CoPilot" at "Department of Justice / Department wide" — this is the planned agency-wide Copilot deployment but pre-deployment per inventory. Public reporting of a fully rolled-out DOJ-wide Copilot is **thinner than the previous narrative claim**; downgraded from Enterprise to Broad pending evidence. |
| **Treasury** | Broad / Federated | OCC.Chat & OCC.DocChat (OCC); ChatOFR (OFR); IRS GenAI for ticketing/code; AskBEP (BEP); BFS LLM POCs | OCC: GPT-4o; OFR: multi-LLM in-house; IRS: various incl. IBM WatsonX Code Assistant; mostly Azure | OCC.Chat in production Dec 2024; ChatOFR deployed; IRS ticket gen AI deployed; many BFS POCs | High | DB rows 10360, 10384, 10482; [FedScoop on OCC](https://fedscoop.com/the-comptroller-of-the-currency-looks-to-level-up-its-generative-ai-offerings/); [FedScoop on IRS](https://fedscoop.com/treasury-irs-ai-use-case-inventory/) | Federated by bureau: OCC, OFR, IRS, BEP, BFS, TFI each run their own. No public evidence of a single Treasury-wide assistant. Treasury inventory grew from 54 → 129 use cases in one year. |
| **USDA** | Limited | GovChat (ARS pilot); USDA-wide GenAI IT Support Chatbot (Cal Poly DxHub on Bedrock+Claude); xAI Grok (planned, FedRAMP-pending) | Multi-vendor (Microsoft, Anthropic via AWS Bedrock, planned Grok) | ARS-only general chatbot pilot; HQ IT chatbot is narrow helpdesk | Medium | DB row 10580; [FedScoop on USDA Grok backing](https://fedscoop.com/grok-xai-fedramp-high-authorization-usda/); [USDA AI Strategy 2025](https://www.usda.gov/sites/default/files/documents/usda-ai-strategy-2025.pdf) | No verified USDA-wide general assistant yet. GovChat is ARS-pilot only. Many bureau chatbots in the inventory are narrow. |
| **DOI** | Limited | theKraken (CHS Q Business AI Assistant, USGS pilot); USGS Azure OpenAI ChatGPT (USGS pilot); Everlaw AI (legal review) | Amazon Q Business; Azure OpenAI; Everlaw | All bureau-only pilots | Low | DB rows 8232, 8304, 8303 | No DOI-wide enterprise FOUO LLM verified in DB or public reporting. The narrative reference to "DOI Iris" did not surface in DB or web search; could not confirm. |
| **DOC** | Limited / Federated | DOC Chat (OS); ChatGPT Enterprise (ITA); Claude For Government (ITA); Generative AI Tools Pilot - Global Markets (ITA); LLM support for NIST research; Implement MS365 Copilot in OS | OpenAI, Anthropic, Microsoft, Google Gemini | All bureau-level (OS, ITA, NIST, NOAA, USPTO); DOC Chat is the closest to enterprise but description is empty in DB | Low | DB rows 7847, 7667, 7672, 7665, 7832, 7834, 7850 | DOC is heavily federated (NOAA, NIST, ITA, Census, USPTO). DOC Chat at OS and Implement MS365 Copilot in OS are the only HQ-level entries; both lack detail. NOAA has multiple narrow chatbots that we exclude. |
| **ED** | Broad | MS Copilot (Agency Wide × 14 capability rows); Generative AI - * (FSA OpenAI/Google) | Microsoft 365 Copilot (agency-wide); FSA on OpenAI + Google Distributed Cloud | "Agency Wide" per inventory rows 8939–8953 | Medium | DB rows 8939–8953; ED inventory page | ED's inventory has 15 distinct M365 Copilot capability rows all marked "Agency Wide" + "Deployed" — i.e. it's agency-wide M365 Copilot. Not a custom assistant but qualifies as a broadly available general LLM. Aidan (row 8877) is a narrow FAFSA chatbot (excluded). |
| **NRC** | Limited | Testing industry leading generative AI foundational large language models (OpenAI ChatGPT Enterprise + Google Gemini for Government) | OpenAI + Google | Pre-deployment, agency-wide testing | Medium | DB row 10081; [FedScoop on NRC Azure OpenAI testing](https://fedscoop.com/nuclear-regulatory-commission-in-testing-phase-with-azure-openai/); [NRC FY26 AI Strategic Plan](https://www.nrc.gov/docs/ML2526/ML25269A196.pdf) | No deployed enterprise tool yet; agency in evaluation phase. |
| **EPA** | Limited | Internal GenAI chat tool (May 2025) | Not publicly named (cloud-based) | Internal only; not yet broadly available | Medium | DB rows 8955, 8957, 8959; [EPA AI Strategy 2025](https://www.epa.gov/system/files/documents/2025-10/epa_ai_strategy_plan_final2025.pdf); [AWS Public Sector blog on EPA](https://aws.amazon.com/blogs/publicsector/accelerating-workflows-with-generative-ai-epas-document-processing-journey/) | EPA introduced an internal generative AI chat tool in May 2025 per the AI strategy doc; specific name not surfaced in DB or web. Other EPA inventory rows (Esri assistants, ServiceNow helpdesk) are narrow. |
| **DOL** | Limited | Generative AI Assistant (AI Center) | Azure OpenAI + AWS via Synergy | OCIO-only | Low | DB row 8778; [DOL AI page](https://www.dol.gov/ai) | One mention of an "AI Center" generative assistant tool; appears OCIO-internal. Public DOL reporting focuses on AI Literacy framework rather than internal tools. |
| **SBA** | Limited | OFO multi-LLM pilot (ChatGPT/Bing Copilot/Gemini); SBA.gov Salesforce chatbot (external/narrow, excluded) | Multiple commercial | Pre-deployment, OFO bureau only | Low | DB rows 10117, 10122, 10123, 10124, 10125, 10126, 10127 | Many small pre-deployment pilots, no enterprise rollout. |
| **HUD** | Limited | Microsoft Copilot (OCIO pilot); HUD OIG pilot | Microsoft 365 Copilot | Limited-scope pilot per HUD OIG compliance plan | Medium | DB row 9627; [HUD OIG AI Compliance Plan](https://www.hudoig.gov/sites/default/files/2025-09/ai-compliance-plan.pdf) | Pilot only, opt-in, telemetry-logged, non-sensitive data only. |
| **FDIC** | Limited | Enterprise FDIC Chat (pre-deployment) | Not specified | Pre-deployment | Medium | DB row 9019; [FDIC AI page](https://www.fdic.gov/ai); [FDIC AI Compliance Plan](https://www.fdic.gov/artificial-intelligence-ai-compliance-plan.pdf) | DB and FDIC AI page describe a piloted internal chatbot for policy/procedure questions; not yet enterprise. CFOO Admin/Travel chatbots (RASA-based) are narrow. |
| **FTC** | Limited | Microsoft 365 Copilot (OCIO pilot) | Microsoft | Pilot | Medium | DB row 9108 | Pilot only. |
| **NSF** | Limited | TIP MS Copilot Pilot; M365 AI Builder Summarization | Microsoft | TIP/OCIO pilot; OIA narrow | Low | DB rows 10098, 10101, 10103 | Pre-deployment pilots only. |
| **NRC** (covered above) | | | | | | | |
| **TVA** | Limited | Copilot, ChatSPP, Trade Chat | Microsoft (Copilot); other unspecified | Bureau-level | Low | DB rows 10329, 10338, 10355 | Inventory entries are sparse. TVA has not publicly announced an enterprise-wide LLM. |
| **GPO** | Limited | (1 LLM-tagged use case in DB; details thin) | Unknown | Unknown | Low | DB inventory | Insufficient public info. |
| **SEC** | Limited | "Using AI Large Language Model chat for general tasks/questions" (ENF) | Aretec / Elder Research | ENF division-level deployed | Low | DB row 10176 | Only one "general tasks" entry, division-scoped (ENF). Other SEC entries are narrow. |
| **NCUA** | None reported | — | — | — | Low | DB has 3 NCUA use cases, none general LLM | No general-purpose LLM in inventory. |
| **CFTC** | None reported | — | — | — | Low | DB has 3 CFTC use cases, none general LLM | No general-purpose LLM identified. |
| **FRB** | Limited | Virtual Benefits Assistant (narrow, excluded); Fed-internal AI for code translation | Various | Narrow tools only | Low | DB row 9090; [Fed Compliance Plan](https://www.federalreserve.gov/publications/compliance-plan-for-OMB-memorandum-m-25-21.htm) | Fed Board emphasizes internal AI for code work, not a general staff chatbot. |
| **FERC** | Limited | AI-Enabled Assistant Legal Research (Thomson Reuters) | Thomson Reuters | Pre-deployment, narrow legal | Low | DB row 9038 | Narrow legal-research tool only. |
| **FHFA** | Limited | Oracle LLM integration (retired) | Oracle | Retired | Low | DB row 9045 | Only LLM entry is retired. |
| **NMB** | None reported | — | — | — | Low | DB has 4 NMB use cases, none general | None. |
| **NTSB** | Limited | FOIAXpress AI assistant | OPEXUS | Bureau-only narrow | Low | DB row 10108 | Narrow FOIA tool only. |
| **Peace Corps** | None reported | — | — | — | Low | DB has 0 use cases for Peace Corps | None reported. |
| **USITC** | Enterprise (small) | M365 Copilot (consolidated rows show 1‑100 users on every Appendix B line) | Microsoft | Small agency-wide | Medium | Consolidated rows 546–554 | Small agency where M365 Copilot covers all consolidated patterns. |

## Non-reporting agencies (no 2025 inventory in our DB)

These agencies have no individual `use_cases` row, but the audit found Appendix‑B
consolidated rows for some of them. The "Y on Microsoft Copilot" template line
should NOT be read as an agency-wide deployment without independent confirmation.

| Agency | DB Status | Public knowledge | Rating | Confidence |
|---|---|---|---|---|
| **DoD** | No 2025 individual inventory in our dataset | Pentagon launched **GenAI.mil** Dec 2025 (Google Gemini for unclassified work + others); aiming for ~3M users incl. warfighters/contractors. See [DefenseScoop](https://defensescoop.com/2025/12/09/genai-mil-platform-dod-commercial-ai-models-agentic-tools-google-gemini/). | Enterprise | High |
| **USAID** | No 2025 inventory | Mostly dissolved/restructured under 2025 EO. Public AI activity unclear. | Unknown | Low |
| **ODNI** | No 2025 inventory | Classified ICAM-style tools are out of scope of this audit. | Unknown | Low |
| **CFPB** | No 2025 inventory | No public general-LLM rollout reported. | None reported | Low |
| **EEOC** | No 2025 inventory | No public general-LLM rollout reported. | None reported | Low |
| **GAO** | No 2025 inventory | Legislative agency; not subject to M-25-21. GAO has published AI-on-AI evaluation work but no enterprise chat for staff confirmed. | None reported | Low |
| **EXIM** | No 2025 inventory | None confirmed. | None reported | Low |
| **FLRA** | No 2025 inventory | None confirmed. | None reported | Low |
| **MSPB** | No 2025 inventory | None confirmed. | None reported | Low |
| **NEH** | No 2025 inventory | None confirmed. | None reported | Low |
| **PRC** | No 2025 inventory | None confirmed. | None reported | Low |
| **PT** (Presidio Trust) | No 2025 inventory | None confirmed; very small agency. | None reported | Low |
| **USAGM** | No 2025 inventory | None confirmed. | None reported | Low |
| **USCCR** | No 2025 inventory | None confirmed; very small. | None reported | Low |
| **CPSC** | No 2025 inventory | None confirmed. | None reported | Low |
| **CSOSA** | Appendix‑B only | Marks "Y" on Copilot for 1001‑5000 users; no individual rollout confirmed in news. The `agency_ai_maturity.has_enterprise_llm=1` flag for CSOSA fires solely from this template line. | Limited | Low |
| **EAC** | Appendix‑B only | "Y" on ChatGPT/Claude/Copilot/Perplexity for 1‑100 users — i.e., individual user accounts, not an agency rollout. `has_enterprise_llm=1` is **misleading**. | Limited | Low |
| **FCC** | Appendix‑B only | "Y" on M365 Copilot for 101‑1000 users plus Teams meeting transcription (1001‑5000). No standalone FCC enterprise chatbot in inventory. | Limited | Low |
| **OSC** | Appendix‑B only | "Y" on M365 Copilot for 101‑1000 users; small agency. | Limited | Low |
| **PBGC** | Appendix‑B only | "Y" on M365 Copilot 1001‑5000 users (drafting only). | Limited | Low |
| **USTDA** | Appendix‑B only | "Y" on Microsoft Copilot 101‑1000 (word processor only). | Limited | Low |
| **USITC** | Appendix‑B only | "Y" on M365 Copilot across most patterns 1‑100 users — small agency-wide. | Enterprise (small) | Medium |

---

## Material tag changes (versus existing DB tags)

These are the agency-level claims most affected by this audit; details per row are in `by_row.csv`.

1. **State** — current DB has StateChat tagged `deployment_scope='bureau', is_enterprise_wide=0`. **Should be `enterprise_wide`**: 45,000+ active users is documented.
2. **DHS** — DB scope on DHSChat (row 7594) is empty/component; should be `enterprise_wide` for HQ + multi-component.
3. **VA** — `agency_ai_maturity.has_enterprise_llm=0` (per audit context) is wrong: VA GPT has ~95K–100K users.
4. **DOJ** — `agency_ai_maturity.has_enterprise_llm=0` is wrong **directionally** — DOJ has many active component pilots and a Department-wide CoPilot in pre-deployment — but the user-facing rollout is thinner than the previous "DOJ-wide M365 Copilot" narrative would suggest. Treat as **Broad**, not Enterprise.
5. **DOI** — Cannot confirm an Iris-named DOI-wide assistant in inventory or via web. Downgrade to Limited until corroborated.
6. **DOT** — Confirmed "Ask Dottie" capability and Enterprise Personal Productivity Assistant in DOT compliance plan. Promote to Enterprise.
7. **CSOSA, EAC, FCC, OSC, PBGC, USTDA** — `has_enterprise_llm=1` is technically defensible (these agencies do report Microsoft Copilot use) but **scope is small** (often <100 license bands and only per-task patterns). Re-rate from "Enterprise LLM deployed" → "Limited", since these are individual subscription-level use rather than an agency-built FOUO/CUI assistant.
8. **NLRB** — DB has 0 individual use cases; previous `has_enterprise_llm=1` flag is unsupported. Rate **None reported**.
9. **HHS** — Current DB inventory has 180 rows tagged `is_general_llm_access=1`; many of these are **narrow CDC/CMS chatbots** (Discover User Assistant, NCIRD SmartFind, etc.) misclassified. After correction: 146 rows. The genuine HHS-wide assistant is not a single named system but the recent Anthropic Claude + GSA OneGov ChatGPT department-wide rollout, plus FDA Elsa and NIH ChIRP for those subagencies.

---

## Sub-agency rollup (round-3)

Sub-agency view for general-purpose LLM, derived from per-bureau use-case counts and the round-3 review (96 sub-agencies, see `audit/retag/round3/general_llm/`). Cabinet departments and independent agencies are kept at the parent table above; the rows below are bureaus, labs, centers, and offices within them. Sub-agencies with <5 use cases are excluded as below the data-quality threshold.

### Within HHS (11 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [National Institutes of Health (NIH)](/agencies/hhs-nih) | Enterprise | NIH ChIRP\|ChatGPT\|Azure OpenAI\|Palantir Foundry\|HHS Claude (department-wide) | All NIH staff via VPN (ChIRP); 47/48 LLM use cases enterprise-tagged | high | db_subtree;round1_by_agency.md (HHS row names ChIRP at NIH);NIH Catalyst on ChIRP | ChIRP supports GPT-4o + Claude. Independent NIH-wide LLM beyond the HHS Claude rollout. |
| [Centers for Disease Control and Prevention (CDC)](/agencies/hhs-cdc) | Enterprise | Azure OpenAI\|Palantir AIP (1CDP)\|Databricks\|HHS Claude | CDC workforce — 36/38 LLM use cases enterprise-tagged | high | db_subtree;round1_by_agency.md (HHS row mentions CDC chatbots) | Tier 'leading'. Charter rule: leading => at least Broad; ent_llm_count=36 satisfies Enterprise. |
| [Centers for Medicare and Medicaid Services (CMS)](/agencies/hhs-cms) | Enterprise | CMS AI Workspace\|CEDAR\|GitHub Copilot\|OpenAI API\|HHS Claude | CMS workforce — 31/34 LLM use cases enterprise-tagged | high | db_subtree;round1_by_agency.md (HHS row notes CMS narrow chatbots) | Tier 'leading' + 31 enterprise-LLM use cases. CMS AI Workspace is named in subtree. |
| [Food and Drug Administration (FDA)](/agencies/hhs-fda) | Enterprise | FDA Elsa\|HHS Claude (department-wide) | >70% of FDA staff voluntarily using Elsa across 11 centers | high | db_subtree;round1_by_agency.md (HHS row names FDA Elsa);Nextgov on Elsa | Elsa on Anthropic Claude in GovCloud. Highest-profile component LLM in HHS. |
| [Center for Drug Evaluation and Research (CDER)](/agencies/hhs-fda-cder) | Enterprise | FDA Elsa\|CDEROne Analytics (FISMA-high) | CDER staff covered by FDA Elsa | high | db_subtree;round1_by_agency.md | CDER is the largest FDA center; Elsa coverage cascades. |
| [Administration for Children and Families (ACF)](/agencies/hhs-acf) | Enterprise | ACF Discover (Palantir)\|ACF Horizon (Palantir)\|HHS Claude | ACF workforce — 10/10 LLM use cases enterprise-tagged | high | db_subtree;round1_by_agency.md (HHS row mentions ACF narrow chatbots) | Round-1 noted ACF chatbots; subtree 100% enterprise density. Promote to Enterprise. |
| [Office of Information Technology (OIT)](/agencies/hhs-cms-oit) | Enterprise | CEDAR\|CMS AI Workspace\|OpenAI API | CMS OIT staff — 7/8 LLM use cases enterprise-tagged | high | db_subtree;round1_by_agency.md | OIT is the central CMS IT shop; runs CEDAR and CMS AI Workspace. |
| [Health Resources and Services Administration (HRSA)](/agencies/hhs-hrsa) | Enterprise | (unspecified HRSA LLM)\|UiPath\|HHS Claude | HRSA workforce — 13/14 LLM use cases enterprise-tagged | medium | db_subtree;round1_by_agency.md (HHS row mentions HRSA chatbots) | High enterprise-LLM density (>90%); promote to Enterprise even with thin named tools. |
| [Office of Communications (OC)](/agencies/hhs-cms-oc) | Enterprise | GitHub Copilot\|HHS Claude (cascaded) | CMS Office of Communications — 11/12 LLM use cases enterprise-tagged | medium | db_subtree | Sub-CMS office; cascades from CMS + has its own GitHub Copilot subtree. |
| [Center for Consumer Information and Insurance Oversight (CCIIO)](/agencies/hhs-cms-cciio) | Inherited | HHS Claude\|CMS AI Workspace | CCIIO staff covered by CMS + HHS rollouts | medium | db_subtree;round1_by_agency.md | 3 enterprise-LLM use cases but CCIIO is a CMS sub-component; cascades from CMS. |
| [Agency for Healthcare Research and Quality (AHRQ)](/agencies/hhs-ahrq) | Inherited | HHS Claude (department-wide)\|Microsoft Teams | AHRQ staff covered under HHS-wide rollout | low | db_subtree;round1_by_agency.md | Small AHRQ subtree; only 2 enterprise-LLM use cases tagged. Cascades from HHS. |

### Within DHS (7 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [U.S. Customs and Border Protection (CBP)](/agencies/dhs-cbp) | Enterprise | ChatCBP\|Custom GenAI coding assistant\|DHSChat (HQ-overlay) | CBP-wide (~60K agents/officers); ChatCBP went into production May 2025 | high | db_subtree;FedScoop on chatCBP (https://fedscoop.com/customs-and-border-protection-taps-chatcbp-to-assist-workforce/);DHS use-case inventory CBP page | ChatCBP is a CBP-built FOUO assistant (RAG + SharePoint integration). Component-level Enterprise. |
| [U.S. Immigration and Customs Enforcement (ICE)](/agencies/dhs-ice) | Enterprise | ICE Enterprise AI Assistant\|Palantir AIP/CMA\|DHSChat overlay | ICE-wide via ICE Enterprise AI Assistant; Palantir AIP for investigators | medium | db_subtree;round1_by_agency.md (DHS row) | Round-1 DHS rollup names ICE Enterprise AI Assistant; LES vendor masking limits public visibility. |
| [U.S. Citizenship and Immigration Services (USCIS)](/agencies/dhs-uscis) | Enterprise | PAiTH\|Claude (component access) | USCIS staff via PAiTH | medium | db_subtree;round1_by_agency.md (DHS row names PAiTH at USCIS) | PAiTH named in round-1 as USCIS's component LLM. |
| [Management Directorate (MGMT)](/agencies/dhs-mgmt) | Enterprise | DHSChat\|LIGER (FPS via LMI) | DHS HQ ~19K users; FPS uses LIGER | high | db_subtree;round1_by_agency.md;HSToday on DHSChat;Nextgov on DHSChat | DHS HQ rolled out DHSChat agency-wide for HQ staff; FPS adds LIGER on top. |
| [Cybersecurity and Infrastructure Security Agency (CISA)](/agencies/dhs-cisa) | Enterprise | CISAChat | CISA workforce (~3K) | medium | db_subtree;round1_by_agency.md (DHS row names CISAChat on Microsoft) | CISAChat is component-level enterprise FOUO. |
| [Federal Emergency Management Agency (FEMA)](/agencies/dhs-fema) | Broad | FEMA OCFO GPT\|ReadyAI\|OpenAI API (Azure Commercial) | FEMA OCFO GPT for finance staff; ReadyAI for emergency-prep content | medium | db_subtree;DHS use-case inventory FEMA page | FEMA has multiple Azure OpenAI deployments. FEMA OCFO GPT is the closest to a general staff assistant; ReadyAI is content-focused. |
| [Transportation Security Administration (TSA)](/agencies/dhs-tsa) | Inherited | DHSChat (HQ pilot at TSA) | TSA staff covered under DHSChat 10-component pilot expansion | medium | db_subtree;round1_by_agency.md | TSA does not appear to have its own component LLM; rides DHSChat. |

### Within DOE (17 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Los Alamos National Laboratory (LANL)](/agencies/doe-lanl) | Enterprise | ChatGPT Enterprise\|Microsoft 365 Copilot | LANL workforce (~14K) — round-1 names ChatGPT Enterprise at LANL | high | db_subtree;round1_by_agency.md (DOE row);DOE 2025 AI Strategy | LANL ChatGPT Enterprise is one of the largest lab-level rollouts. |
| [Pacific Northwest National Laboratory (PNNL)](/agencies/doe-pnnl) | Enterprise | Microsoft 365 Copilot\|GitHub Copilot\|Claude\|OpenAI API | PNNL staff (~6K) per round-1 (M365 Copilot + Anthropic Claude pilots) | high | db_subtree;round1_by_agency.md | PNNL named in round-1 as having M365 Copilot + Claude pilots; 23 LLM-tagged use cases. |
| [Idaho National Laboratory (INL)](/agencies/doe-inl) | Enterprise | MauroGPT\|FuelGPT\|Chatlab\|M365 Copilot\|ChatGPT\|Claude | INL workforce (~5K) — multiple custom chatbots + M365 Copilot | high | db_subtree;round1_by_agency.md (names MauroGPT/FuelGPT/Chatlab at INL) | INL is one of the most LLM-active DOE labs. |
| [Savannah River Site (SRS)](/agencies/doe-srs) | Enterprise | ChatSRS\|Tabnine\|Azure GOV | SRS workforce — 13 of 14 LLM use cases tagged enterprise | high | db_subtree;round1_by_agency.md (names ChatSRS at Savannah River) | Maturity tier 'progressing' + 13 enterprise-LLM-tagged use cases is unambiguous. |
| [Lawrence Livermore National Laboratory (LLNL)](/agencies/doe-llnl) | Enterprise | LivChat\|ChatGPT\|Azure OpenAI\|Claude | LLNL workforce (~8K) — LivChat is round-1 named | high | db_subtree;round1_by_agency.md (names LivChat at LLNL) | LivChat is LLNL's lab-wide LLM. |
| [Naval Reactors (NR)](/agencies/doe-nr) | Enterprise | SpyglassGPT\|M365 Copilot\|ServiceNow Now Assist | Naval Reactors workforce — SpyglassGPT named in round-1 | high | db_subtree;round1_by_agency.md (names SpyglassGPT at Naval Reactors) | Custom NR LLM plus M365 Copilot. |
| [National Renewable Energy Laboratory (NREL)](/agencies/doe-nrel) | Enterprise | Energy Wizard / ELM\|OpenAI API\|Azure | NREL staff (~3K) — Energy Wizard is round-1 named | high | db_subtree;round1_by_agency.md (names Energy Wizard / ELM at NREL) | All 7 NREL LLM use cases reference NREL Stratus/Azure. |
| [Oak Ridge National Laboratory (ORNL)](/agencies/doe-ornl) | Broad | Microsoft 365 Copilot\|Microsoft Copilot Studio\|ServiceNow Now Assist | ORNL staff via M365 Copilot Cloud Enclave | medium | db_subtree;round1_by_agency.md (lists ORNL among M365 Copilot DOE labs) | ORNL not named with custom LLM in round-1; runs M365 Copilot. |
| [Office of Environmental Management (EM)](/agencies/doe-em) | Broad | Azure OpenAI\|GitHub Copilot | EM staff using Azure OpenAI deployments | medium | db_subtree (10 of 11 use cases LLM-tagged) | High LLM density (>90%) suggests broad use; not enterprise-flagged. |
| [SLAC National Accelerator Laboratory (SLAC)](/agencies/doe-slac) | Broad | GitHub Copilot\|Microsoft 365 (O365)\|ServiceNow Now Assist | SLAC staff via O365/M365 Copilot per round-1 | medium | db_subtree;round1_by_agency.md (lists SLAC under M365 Copilot labs) | No standalone SLAC chatbot but M365 Copilot present. |
| [Argonne National Laboratory (ANL)](/agencies/doe-anl) | Limited | Argonne IT Infrastructure (1 LLM use case) | Single use case; no named tool | low | db_subtree | Maturity tier 'minimal'. |
| [Office of Legacy Management (LM)](/agencies/doe-lm) | Limited | Gemini | Office of Legacy Management — Gemini in 1 use case | low | db_subtree | Tier minimal; no broad assistant. |
| [Brookhaven National Laboratory (BNL)](/agencies/doe-bnl) | None reported | — | No general LLM in subtree | low | db_subtree (0 LLM-tagged of 34 use cases) | BNL not named in DOE round-1 lab list. No deployment surfaced. |
| [Fermi National Accelerator Laboratory (FNAL)](/agencies/doe-fnal) | None reported | — | No general LLM in subtree | low | db_subtree (0 LLM-tagged of 17 use cases) | Fermi not named in DOE round-1 lab list. |
| [National Energy Technology Laboratory (NETL)](/agencies/doe-netl) | None reported | — | No general LLM in subtree | low | db_subtree (0 LLM-tagged of 15 use cases) | NETL not in round-1 lab roster. |
| [Office of Energy Efficiency and Renewable Energy (EE)](/agencies/doe-ee) | None reported | — | OpenText e-discovery only; no general LLM | low | db_subtree | OpenText Axcelerate/Decisiv are narrow legal-discovery tools, not general LLM. |
| [National Nuclear Security Administration (NNSA)](/agencies/doe-nnsa) | None reported | — | No general LLM in subtree | low | db_subtree (0 LLM-tagged) | NNSA HQ subtree shows no general LLM (the labs roll up separately). |

### Within NASA (7 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Goddard Space Flight Center (GSFC)](/agencies/nasa-gsfc) | Enterprise | ChatGSFC\|Anthropic Claude pilot\|Custom LLM (planned)\|Fine-tuned FLAN | >7,000 NASA users on ChatGSFC (federated agency-wide from GSFC) | high | db_subtree;round1_by_agency.md (NASA row);Element 84 on ChatGSFC;FedScoop on Claude at NASA | Tier 'leading' + ChatGSFC scaled beyond GSFC. The most LLM-active NASA center. |
| [Marshall Space Flight Center (MSFC)](/agencies/nasa-msfc) | Broad | MSFC Copilot pilot\|ChatGSFC (cascaded) | MSFC staff via Copilot pilot + GSFC chat | medium | db_subtree;round1_by_agency.md (NASA row names MSFC Copilot pilot) | MSFC named in round-1 NASA Copilot pilot. |
| [Langley Research Center (LaRC)](/agencies/nasa-larc) | Broad | ALTIRA\|ChatGSFC (cascaded) | LaRC staff — ALTIRA named in round-1 | medium | db_subtree;round1_by_agency.md (NASA row names ALTIRA at Langley);FedScoop on Claude at NASA | ALTIRA + Anthropic Claude pilot at Langley. |
| [Ames Research Center (ARC)](/agencies/nasa-arc) | Broad | ChatGPT\|FAA enclave | Ames staff in approved enclave (ChatGPT) | medium | db_subtree | Tier 'progressing'; one enterprise-LLM use case + ChatGPT named tool. |
| [Jet Propulsion Laboratory (JPL)](/agencies/nasa-jpl) | Limited | (no center-wide LLM named) | JPL — 7 LLM-tagged of 43 use cases; no enterprise tag | low | db_subtree | JPL is Caltech-managed; not in round-1 NASA LLM roster. |
| [Johnson Space Center (JSC)](/agencies/nasa-jsc) | Limited | Azure OpenAI\|Gemini | JSC narrow Azure OpenAI/Gemini use | low | db_subtree | No JSC-wide assistant named. |
| [Glenn Research Center (GRC)](/agencies/nasa-grc) | None reported | — | No LLM-tagged use cases in subtree | low | db_subtree (0 LLM-tagged of 7 use cases) | Glenn not in round-1 NASA LLM roster. |

### Within DOJ (11 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Federal Bureau of Investigation (FBI)](/agencies/doj-fbi) | Broad | FBI Policy Chatbot\|Redacted commercial LLMs | FBI bureau pilot; round-1 names policy chatbot | medium | db_subtree;round1_by_agency.md (DOJ row names FBI policy chatbot);FedScoop FBI inventory | FBI doubled AI use cases YoY; specific policy chatbot named in round-1 evidence. |
| [Drug Enforcement Administration (DEA)](/agencies/doj-dea) | Broad | DEA OpenAI chatbot\|OpenAI API | DEA staff per round-1 (OpenAI chatbot pilot) | medium | db_subtree;round1_by_agency.md (DOJ row names DEA OpenAI chatbot) | 18 LLM-tagged use cases, second-most among DOJ components. |
| [Antitrust Division (ATR)](/agencies/doj-atr) | Broad | Harvey\|OpenAI\|Perplexity\|Azure OpenAI\|Databricks | ATR Generative AI Test pilot per round-1 | medium | db_subtree;round1_by_agency.md (DOJ row names ATR Generative AI Test) | Round-1 names ATR's multi-vendor LLM pilot. |
| [Bureau of Alcohol, Tobacco, Firearms and Explosives (ATF)](/agencies/doj-atf) | Limited | (commercial LLM vendors, redacted) | Component-only narrow use | low | db_subtree (3 LLM-tagged of 34) | ATF not named with general assistant in round-1. |
| [Federal Bureau of Prisons (FBOP)](/agencies/doj-fbop) | Limited | (narrow LLM use; WellSaid for content) | BOP narrow use | low | db_subtree (5 LLM-tagged of 32) | WellSaid Labs is voice-gen, not general LLM. Narrow. |
| [U.S. Marshals Service (USMS)](/agencies/doj-usms) | Limited | AWS Textract\|(redacted) | USMS narrow use | low | db_subtree | Textract is doc OCR, not general LLM. |
| [Civil Division (CIV)](/agencies/doj-civ) | Limited | (unspecified) | Civil Division narrow use | low | db_subtree | No named general assistant. |
| [Tax Division (TAX)](/agencies/doj-tax) | Limited | AWS Transcribe\|LexisNexis | Tax Division narrow legal-research use | low | db_subtree | Transcribe + LexisNexis are not general LLM. |
| [Organized Crime Drug Enforcement Task Forces (OCDETF)](/agencies/doj-jmd-ocdetf) | Limited | (unspecified) | OCDETF narrow use | low | db_subtree | 6 LLM-tagged use cases, no named general assistant. |
| [Office of Justice Programs (OJP)](/agencies/doj-ojp) | None reported | — | No general LLM identified | low | db_subtree | OJP tier minimal. |
| [Justice Management Division (JMD)](/agencies/doj-jmd) | Inherited | DOJ CoPilot (department-wide; pre-deployment) | JMD admin staff covered by DOJ-wide M365 Copilot rollout | medium | db_subtree;round1_by_agency.md (DOJ row names DOJ CoPilot department-wide) | JMD = DOJ HQ admin; covered by department CoPilot. |

### Within DOC (6 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [International Trade Administration (ITA)](/agencies/doc-ita) | Broad | ChatGPT Enterprise\|Claude For Government\|Generative AI Tools Pilot - Global Markets | ITA staff multi-LLM pilot per round-1 | medium | db_subtree;round1_by_agency.md (DOC row enumerates ITA deployments) | ITA is the most LLM-active DOC bureau per round-1. |
| [National Oceanic and Atmospheric Administration (NOAA)](/agencies/doc-noaa) | Limited | Gemini\|Amazon Q\|GitHub Copilot | Pilot/individual-use scope; no NOAA-wide chatbot named | low | db_subtree | NOAA has 157 use cases but only 16 LLM-tagged and 0 enterprise-LLM-tagged. Bureau-wide rollout not confirmed. |
| [U.S. Patent and Trademark Office (USPTO)](/agencies/doc-uspto) | Limited | Claude\|ServiceNow Now Assist | Bureau-level pilot use only | low | db_subtree | Claude tagged but only 2 LLM use cases; not a USPTO-wide rollout. |
| [National Institute of Standards and Technology (NIST)](/agencies/doc-nist) | Limited | Gemini\|Grammarly | Individual-use scope at NIST | low | db_subtree;round1_by_agency.md (DOC row mentions LLM support for NIST research) | No NIST-wide general assistant; Gemini at user level only. |
| [U.S. Census Bureau (Census)](/agencies/doc-census) | None reported | — | No general LLM identified | low | db_subtree | One LLM-tagged use case in subtree; no named general assistant. |
| [National Telecommunications and Information Administration (NTIA)](/agencies/doc-ntia) | None reported | — | No general LLM identified | low | db_subtree | 3 LLM use cases tagged but no named tools or general assistant. |

### Within Treasury (5 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Office of the Comptroller of the Currency (OCC)](/agencies/treasury-occ) | Enterprise | OCC.Chat\|OCC.DocChat | OCC staff in production since Dec 2024 | high | db_subtree;round1_by_agency.md (Treasury row names OCC.Chat & OCC.DocChat);FedScoop on OCC | 25 of 26 use cases LLM-tagged. OCC.Chat is one of the cleanest bureau-level enterprise LLMs. |
| [Office of Financial Research (OFR)](/agencies/treasury-ofr) | Enterprise | ChatOFR (multi-LLM in-house) | OFR staff (small bureau ~200) on ChatOFR | high | db_subtree;round1_by_agency.md (Treasury row names ChatOFR) | ChatOFR named in round-1 as deployed. |
| [Internal Revenue Service (IRS)](/agencies/treasury-irs) | Broad | IRS GenAI for ticketing/code\|Microsoft Teams\|Custom In-House AI | IRS staff with multiple GenAI deployments per round-1 | high | db_subtree;round1_by_agency.md (Treasury row names IRS GenAI for ticketing/code);FedScoop on IRS | 37 LLM-tagged use cases; no single named staff-facing assistant per round-1. |
| [Bureau of the Fiscal Service (BFS)](/agencies/treasury-bfs) | Broad | BFS LLM POCs | BFS staff multi-POC | medium | db_subtree;round1_by_agency.md (Treasury row names BFS LLM POCs) | 19 LLM-tagged use cases; many POCs, no single enterprise system per round-1. |
| [Bureau of Engraving and Printing (BEP)](/agencies/treasury-bep) | Limited | AskBEP | BEP staff narrow | low | db_subtree;round1_by_agency.md (Treasury row names AskBEP) | Tier minimal. |

### Within VA (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Veterans Health Administration (VHA)](/agencies/va-vha) | Enterprise | VA GPT\|M365 Copilot Chat\|ChatGPT\|Databricks | VHA clinicians/staff among VA GPT's 95,000+ users; OIG flagged PHI use | high | db_subtree;round1_by_agency.md (VA row);VA OIG advisory;Military.com on OIG memo | OIG explicitly names VHA as authorizing VA GPT + Copilot Chat for PHI without NCPS coordination. |
| [Office of Information & Technology (OIT)](/agencies/va-oit) | Enterprise | VA GPT (operated by OIT)\|Ask Sage (pilot)\|ServiceNow Now Assist | OIT runs VA GPT for the whole department (95K+ users) | high | db_subtree;round1_by_agency.md;FedScoop on VA generative AI tools | Tier 'leading' + OIT is the bureau that operates VA GPT. |
| [Veterans Benefits Administration (VBA)](/agencies/va-vba) | Enterprise | VA GPT (department-wide)\|M365 Copilot Chat | VBA claims processors among VA GPT users | medium | db_subtree;round1_by_agency.md | VBA staff covered by VA-wide rollout. |

### Within DOI (6 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [U.S. Geological Survey (USGS)](/agencies/doi-usgs) | Broad | theKraken (Amazon Q Business)\|Azure OpenAI ChatGPT\|Esri ArcGIS AI | USGS staff via theKraken pilot + Azure OpenAI ChatGPT | medium | db_subtree;round1_by_agency.md (DOI row names theKraken at USGS) | USGS is the DOI bureau with the most LLM activity (12 LLM-tagged of 187 use cases). |
| [Bureau of Land Management (BLM)](/agencies/doi-blm) | Limited | (unspecified BLM chatbot per DOI round-1 narrative) | Bureau-only narrow use | low | db_subtree (4 LLM-tagged, no named tool) | Round-1 mentions BLM among DOI narrow chatbots. |
| [U.S. Fish and Wildlife Service (FWS)](/agencies/doi-fws) | None reported | — | No general LLM identified | low | db_subtree (2 LLM-tagged, no named tool) | No FWS-named assistant. |
| [Bureau of Reclamation (BOR)](/agencies/doi-bor) | None reported | — | No general LLM identified | low | db_subtree (0 LLM-tagged) | Tier minimal. |
| [Office of Natural Resources Revenue (ONRR)](/agencies/doi-onrr) | None reported | — | No general LLM identified | low | db_subtree (0 LLM-tagged) | Tier minimal. |
| [Bureau of Safety and Environmental Enforcement (BSEE)](/agencies/doi-bsee) | None reported | — | No general LLM identified | low | db_subtree (0 LLM-tagged) | No BSEE assistant. |

### Within USDA (5 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Natural Resources and Environment (NRE)](/agencies/usda-nre) | Limited | Esri ArcGIS AI\|Google NotebookLM | NRE/Forest Service narrow tools | low | db_subtree | Forest Service not running a bureau-wide general LLM. |
| [Research, Education, and Economics (REE)](/agencies/usda-ree) | Limited | Microsoft Copilot Studio\|ARSAzure | ARS bureau pilot (GovChat) per round-1 | medium | db_subtree;round1_by_agency.md (USDA row names GovChat ARS pilot) | ARS sits in REE; GovChat is the round-1-named ARS pilot. |
| [Farm Production and Conservation (FPAC)](/agencies/usda-fpac) | Limited | AI Builder\|UIPath | FPAC narrow analytic use | low | db_subtree | 3 LLM-tagged use cases of 20; no named general assistant. |
| [Food Safety (FoodSafety)](/agencies/usda-foodsafety) | Limited | (unspecified) | FSIS narrow LLM use | low | db_subtree (8 LLM-tagged of 13) | High LLM density but no named tool surfaced. |
| [Marketing and Regulatory Programs (MRP)](/agencies/usda-mrp) | None reported | — | No general LLM in subtree | low | db_subtree (1 LLM-tagged of 16) | Tier minimal. |

### Within State (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Bureau of Diplomatic Technology (DT)](/agencies/state-dt) | Enterprise | StateChat (operated by DT)\|Databricks\|OpenAI API\|Palantir CfA PFCS | DT runs StateChat for the entire Department | high | db_subtree;round1_by_agency.md (State row);FedScoop on StateChat | Bureau of Diplomatic Technology is the bureau that operates StateChat. |
| [Bureau of Consular Affairs (CA)](/agencies/state-ca) | Inherited | StateChat (department-wide) | Consular Affairs staff covered under StateChat 45K rollout | medium | db_subtree;round1_by_agency.md (State row);FedScoop on StateChat | CA does not have its own general LLM but inherits StateChat. |
| [Foreign Service Institute (FSI)](/agencies/state-fsi) | Inherited | StateChat (department-wide) | FSI staff covered under StateChat | low | db_subtree;round1_by_agency.md | Tier 'minimal'; no FSI-specific LLM. |

### Within DOL (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Employment and Training Administration (ETA)](/agencies/dol-eta) | Limited | Azure OpenAI\|AWS | ETA narrow pilot | low | db_subtree | Single Azure OpenAI use case; not broad. |
| [Bureau of Labor Statistics (BLS)](/agencies/dol-bls) | None reported | — | No general LLM in subtree (0 LLM-tagged) | low | db_subtree | BLS uses internal-system tags only; no general assistant. |
| [Occupational Safety and Health Administration (OSHA)](/agencies/dol-osha) | None reported | — | No general LLM in subtree | low | db_subtree | Hololens VR + Amazon PII redaction; not general LLM. |

### Within SEC (3 sub-agencies)

| Sub-agency | Rating | Key systems | Scope / users | Conf. | Key evidence | Notes |
|---|---|---|---|---|---|---|
| [Office of Information Technology (OIT)](/agencies/sec-oit) | Limited | ACES (internal) | OIT narrow | low | db_subtree | No SEC-wide assistant. |
| [Division of Examinations (EXAMS)](/agencies/sec-exams) | Limited | NEAT (Aretec)\|EDP (Aretec/IBM) | Exams division narrow analytic use | low | db_subtree | NEAT/EDP are exam-data tools, not general LLM. |
| [Office of the Chief Data Officer (OCDO)](/agencies/sec-ocdo) | Limited | Westlaw AI\|AI Filing Parser | OCDO narrow tools | low | db_subtree | No general LLM. |

### Smaller parent agencies (10)

Parent agencies with fewer than 3 in-scope sub-agencies are summarized inline:

- **DOT → Federal Aviation Administration (FAA)** — Inherited (medium). Round-1 explicitly excludes FAA LLM Document Search rows from general LLM. FAA inherits DOT.
- **DOT → Office of the Chief Artificial Intelligence Officer (CAIO)** — Inherited (low). parent rated 'Enterprise'; cascade
- **ED → Federal Student Aid (FSA)** — Enterprise (high). Strong enterprise-LLM density at FSA on top of department-wide M365 Copilot.
- **SSA → Office of the Chief Information Officer (OCIO)** — Enterprise (high). OCIO is the SSA bureau that owns ASC, the agency-wide general chatbot.
- **SBA → Office of the Chief Information Officer (OCIO)** — Broad (medium). 13 of 17 use cases LLM-tagged; broadest tool fan-out among small agencies.
- **FDIC → Division of Resolutions and Receiverships (DRR)** — None reported (low). DRR uses CLEAR/RRMP — not general LLM. Enterprise FDIC Chat is at OCIO level (not subtree here).
- **FRB → Division of Supervision and Regulation (S&R)** — None reported (low). Tier minimal; Fed S&R has no general assistant.
- **FHFA → Office of the Chief Information Officer (OCIO)** — Limited (low). Round-1 lists FHFA's only LLM entry as retired.
- **FTC → Bureau of Consumer Protection (BCP)** — Limited (low). Sentinel is a consumer-complaint analytics platform, not a general LLM. FTC parent rating Limited (M365 Copilot pilot).
- **TVA → Information Technology (IT)** — Limited (low). Round-1 lists TVA Copilot/ChatSPP/TradeChat as bureau-level Limited.
- **TVA → Power Operations (PO)** — None reported (medium). no LLM-tagged use cases in subtree
- **EPA → Office of the Administrator (OFA)** — Limited (low). some LLM activity in subtree (llm=2)

_Source: `audit/retag/round3/general_llm/sub_agency_rows.csv` (96 rows). Methodology in `audit/retag/round3/general_llm/notes.md`._
