# General-Purpose FOUO/CUI LLM Audit — Methodology, Surprises, Gaps

## Method

1. **Candidate selection.** Pulled all `use_cases` rows where any of `is_general_llm_access`, `is_microsoft_copilot`, `is_openai`, `is_anthropic`, `is_google` was 1, OR where the use case name matched any of `chat`, `copilot`, `gpt`, `claude`, `gemini`, `llm`, `ai assistant`, `generative`, `llama`, `anthropic`. That returned 1,154 rows. Also pulled 60 matching consolidated (Appendix B) rows.
2. **Per-row review.** For every candidate I read `use_case_name`, `bureau_component`, `problem_statement`, `expected_benefits`, `system_outputs`, `system_name`, `vendor_name`, `stage_of_development`, and `training_data_description`. Many entries are sparse (DOC's most named systems have empty problem/benefits/outputs).
3. **Decision rule.** A row is a "general-purpose FOUO LLM assistant" if (a) staff can submit arbitrary text prompts, (b) the system is approved for FOUO/CUI work, and (c) it is broadly available rather than narrowly scoped to one workflow or one dataset. ServiceNow Now Assist, narrow customer-service chatbots over a single dataset, and per-policy LLM document searches are excluded.
4. **Heuristic correction.** The Python pass in `by_row.csv` walks all candidates and re-flags `corrected_is_general_llm_access` based on (i) known enterprise system names, (ii) M365 Copilot / Gemini Workspace patterns, and (iii) a NARROW name list / pattern list (FOIA, helpdesk, HR, customer-service, navigator, etc.).
5. **Web verification.** I searched FedScoop, Nextgov, MeriTalk, agency press releases, OMB compliance plans, and AI strategy PDFs for each of the top-12 reporting agencies and the named systems most likely to qualify. Where I had ≥2 corroborating public sources, I marked the agency rating "High" confidence.
6. **Output.** Three files written to `audit/retag/general_llm/`: `by_agency.md`, `by_row.csv` (1,148 rows reviewed; 158 changed flags), and this notes file.

## Surprises

- **State's tag was the most wrong.** StateChat is the largest verifiable enterprise FOUO LLM in the federal civilian space (45K active users of a ~75K workforce, used in promotion-panel decisions), yet the DB has it as `deployment_scope='bureau', is_enterprise_wide=0`. The brief flagged this; web confirmed.
- **VA GPT scale.** ~95K–100K onboarded users at VA. That's nearly 30% of all federal civilian general-LLM users right there. The Jan 2026 OIG advisory says VA authorized VA GPT and M365 Copilot Chat for use with PHI without National Center for Patient Safety coordination, which is genuinely newsworthy for an article.
- **HHS Claude rollout (Dec 2025).** HHS deployed Anthropic Claude department-wide via OneGov, with a memo from Deputy Secretary O'Neill telling staff to "use either AI tool or ask both and compare" (referring to Claude vs ChatGPT). This is on top of FDA Elsa and NIH ChIRP. Then Anthropic was banned across federal agencies in Feb 2026 — so this rollout may already be unwinding by the time an article publishes.
- **DHS revoked commercial AI access.** DHS revoked previous approvals for commercial GenAI to consolidate on DHSChat. Most other agencies are doing the opposite, layering OneGov ChatGPT/Claude/Copilot on top of bureau pilots. DHS's posture is the most distinctive in the federal civilian space.
- **DOJ-wide Copilot is thinner than the prior narrative.** The audit context said "DOJ (M365 Copilot DOJ-wide)" as a confident expectation, but the DB lists DOJ "CoPilot" as `Department of Justice / Department wide` at **Pre-deployment** stage. Public reporting on a fully rolled-out DOJ-wide Copilot is sparse. I rated DOJ "Broad" rather than "Enterprise" pending better evidence.
- **DOT "Ask Dottie" is real but pre-deployment.** Confirmed in DOT's M-25-21 compliance plan PDF. Web search initially returned an unrelated Branching Minds product; the agency primary source resolved it.
- **DOC has no clear HQ chatbot.** The DB has "DOC Chat" (row 7847) at the OS bureau, but no `problem_statement`, no `vendor`, nothing. ITA has multiple individual deployments (ChatGPT Enterprise, Claude For Government). Otherwise DOC is a confederation of NIST, NOAA, Census, USPTO each with their own narrow systems.
- **Education's "MS Copilot" rows.** ED has 15 separate use case rows for "MS Copilot - X" all marked Agency Wide + Deployed (rows 8939–8953). This is just M365 Copilot rebranded as 15 capabilities. Counted as broad, not enterprise.
- **Federation in DOE and NASA.** Each DOE national lab has its own LLM (LANL ChatGPT Enterprise, LLNL LivChat, NREL Energy Wizard/ELM, PNNL Microsoft 365 Copilot + Anthropic Claude, KCNSC Merlin, INL MauroGPT/FuelGPT/Chatlab, SRS ChatSRS, Naval Reactors SpyglassGPT). Similarly NASA has at least ChatGSFC (>7K users), NASA-GPT, ALTIRA at Langley, MSFC Copilot pilot, GSFC Anthropic Claude pilot. Neither agency has a unified department-wide chatbot.
- **Treasury is similarly federated.** OCC, OFR, IRS, BEP, BFS each have their own. OCC.Chat is in production for OCC; ChatOFR for OFR; IRS has many narrow deployments and a productivity push.

## Gaps and unconfirmed claims

- **DOI Iris** — context narrative referenced "DOI's Iris" but neither the DB nor public web returned it. The DB has theKraken (CHS Q Business) at USGS, Everlaw at OCIO, USGS Azure OpenAI ChatGPT, and a few BLM/FWS/SOL chatbots — all bureau-level. Rated DOI **Limited** until somebody points to the Iris source.
- **DOJ-wide Copilot rollout details** — no public press release with user counts. Treated as Broad on the basis of the DB Department-wide entry alone.
- **EPA internal chatbot name** — the EPA AI strategy mentions "an internal generative AI chat tool" launched May 2025 but does not name it. Three EPA inventory rows (8955 Esri, 8957 SF182, 8959 Helpdesk) are all narrow.
- **Treasury / IRS** — IRS has many GenAI use cases for tickets/code/forms but no single staff-facing general assistant has been named publicly. Coded as Broad / Federated.
- **DoD** — out of M-25-21 individual scope but GenAI.mil (Dec 2025, Google Gemini for unclassified work) was confirmed via DefenseScoop. Listed in non-reporting table.
- **OPM Rexi (row 10113)** — narrow HR-focused chatbot, not general LLM. The agency's enterprise general LLMs are M365 Copilot Chat + ChatGPT-5 via OneGov.
- **CSOSA / EAC / FCC / OSC / PBGC / USTDA / NLRB** — `agency_ai_maturity.has_enterprise_llm=1` is misleading where these agencies only checked "Y" on Microsoft Copilot in the OMB Appendix B template, often for very small license bands. Re-rated to "Limited" or "None reported".

## Rows where the source itself looks wrong/misleading

- DB row 10238 (SSA "General Use Chatbot"): the DB lists vendor as "Microsoft - M365 Copilot Chat" but the use case name is generic. This is the SSA's M365 Copilot Chat pilot.
- DB row 9627 (HUD Microsoft Copilot): listed as a department-wide use case but per HUD OIG's compliance plan, this is a limited-scope OIG pilot only — naming is misleading.
- DB row 7847 (DOC "DOC Chat"): completely empty fields except the name. This is a placeholder entry, not a verified deployment.
- DB row 9038 (FERC "AI Enabled Assistant Legal Research"): name suggests broad, system_name is N/A and stage is Pre-deployment; effectively only a Thomson Reuters legal research subscription.
- DB rows 8939–8953 (ED "MS Copilot - X"): 15 rows are 15 different "capabilities" of the same Microsoft 365 Copilot license, not 15 separate systems.
- DB row 9818 (NASA-GPT): name and DB suggest enterprise but stage is "Pre-deployment" — NASA-GPT publicly described in NTRS materials but rollout state is unclear.
- DB row 7951 (DOE Energy Wizard): real and deployed but only at NREL — naming overstates scope. NREL is now branded "National Laboratory of the Rockies" (rebranding noted in late 2025 reporting).
- DB rows 7405, 7413, 7424, 7431, 7437, 7438, 7440, 7442, 7466, 7467, etc. (DHS): tagged `is_general_llm_access=1` but the use case names indicate narrow purpose-built systems (forensics triage, ATR synthetic data, named entity resolution, etc.) — these are false positives from the prior heuristic tagging. Heuristic corrected list moves these to 0.

## Limitations

- **Web evidence is uneven.** Some agency AI inventory pages list use cases without describing user counts or whether the assistant is FOUO-approved. I gave these "Medium" or "Low" confidence rather than guessing.
- **The Anthropic federal ban (Feb 2026)** is potentially the single biggest disruptor to this picture. It may invalidate the HHS Claude department-wide rollout, NASA's GSFC Anthropic pilot, and parts of DOE's lab pilots within ~6 months. An article should explicitly anchor a "rated as of" date.
- **OneGov free Copilot (Sept 2025)** means many small agencies tagged "M365 Copilot" in their inventories now have access to a FOUO-approved general LLM at zero marginal cost. The boundary between "Limited" and "Broad" for these small agencies will move quickly through 2026.
- **I did not verify ATO / FedRAMP authorization claims** beyond what the DB and primary agency sources stated. Multiple agencies use the phrase "FedRAMP-authorized" loosely (e.g., FedRAMP Moderate underlying cloud vs FedRAMP High for the application).
- **Time-budgeted at ~5 minutes per agency** — for the 36 reporting agencies and ~16 non-reporters that's ~3 hours of net research, fitting within the 60–90 minute target after parallelization. Smaller agencies with no public AI office got cursory treatment.

## Concerns for an article

1. **VA OIG safety memo** is the most pointed accountability story: VA is using VA GPT and M365 Copilot Chat with PHI without coordinating with their patient-safety center.
2. **Anthropic ban whiplash** — agencies that just rolled out Claude (HHS, OPM, NASA pilots, DOE labs) are now likely walking it back. Worth a sidebar.
3. **State's promotion-panel use** — using StateChat to help select foreign service officers for promotion panels is a discrete consequential decision that's documented.
4. **DOGE's GSAi rollout** — went 150 → 1,500 → all GSA in roughly 3 months; one of the fastest civilian agency rollouts.
5. **DHS's "revoke commercial AI" posture** is genuinely countercurrent.
6. **Counting issue in `agency_ai_maturity.has_enterprise_llm`** — the existing flag is unreliable in both directions and an article that cites it without re-derivation would be wrong.
