# Slice 1 notes — DHS / DOE / DOI / DOJ (85 rows)

Reviewed: 85 rows (DHS 2, DOE 11, DOI 2, DOJ 70). Source: `2025_bureau_candidates.csv`, rows identified by signature (agency, use_case_name, bureau_component). No DB writes performed (SELECT-only).

## Counts by decision

| proposed_scope | count |
|---|---|
| enterprise_wide | 8 |
| bureau (unchanged) | 76 |
| office (downgrade) | 1 |
| unknown | 0 |

Confidence on the 8 enterprise upgrades: 5 high, 3 medium.

## Enterprise upgrades

1. **DHS / DHS-Chat (MGMT)** — high. FedScoop/Axios/Nextgov coverage confirms 19,000+ HQ staff plus pilots in all 10 operating components; MGMT is the owning office, not the scope. (https://fedscoop.com/chatgpt-meet-chatdhs-homeland-security-ai-bot/)
2. **DOJ / ServiceNow (Department Wide)** — high. DOJ-wide IT helpdesk automation serving any employee with an IT request.
3. **DOJ / Westlaw AI legal research (Department Wide)** — high. Centrally provided subscription for attorneys across all components.
4. **DOJ / BriefCatch (Department Wide)** — high. Deployed legal-writing tool, department-wide filing.
5. **DOJ / CoPilot (Department wide)** — high on scope, but note it is pre-deployment.
6. **DOJ / Business Intelligence Tools / Tableau (Department wide)** — medium: enterprise platform, analyst-heavy user base.
7. **DOJ / FOIA Production Tools (Department wide)** — medium: deployed across all components but the users are FOIA professionals, not the general workforce.
8. **DOI / FBMS UPC Chatbot (OCIO)** — medium: FBMS is DOI's single integrated finance/acquisition system for all bureaus; narrative targets "DOI staff that initiate purchase requests" department-wide. Pre-deployment.

## Confirmed correct as bureau (notable)

- **DHS / LIGER GenAI Toolkit (MGMT)** — narrative and DHS's MGMT inventory page are explicit that this instance is "LIGER for FPS" (Federal Protective Service). Correctly bureau despite being a marquee-sounding tool.
- **DOE / PARSGPT (PM HQ)** — web search found no evidence of DOE-wide reach; narrative says the audience is PM Analysts in the Office of Project Management. Kept bureau (medium).
- All DOE NR/EHSS/EE/GDO/LM rows are program-office tools (Naval Reactors runs its own IT enclave) — bureau.
- All DOJ component rows (FBI, DEA, CIV, ATR, TAX, ATF, USMS, FBOP, EOUSA, EOIR, OIG, CRT, ENRD, OPR, PAO, COPS, USTP, PARDON, JMD/OCDETF) — bureau.

## Downgrade

- **DOE / MAPPRITE (EHSS)** → `office`: narrative scopes it to "EHSS-51 business workflows", a single numbered office within EHSS.

## Ambiguous — needs a human call

1. **DOJ / UFMS ChatBot (JMD)** — UFMS is DOJ's department-wide financial system, so users span every component, but only the finance-user population. Kept bureau (medium); reasonable people could call it enterprise_wide. Same logic applies to **Internal Finance ChatBot (JMD / Workiva)**, kept bureau.
2. **DOJ / FOIA Production Tools** — proposed enterprise_wide on the department-wide filing, but if the bar is "(nearly) the entire workforce", a human may prefer to keep it bureau-equivalent; it is a functional (FOIA-staff) population deployed in every component.
3. **DOJ / Managing Document Digital Signatures (DEA)** — narrative mentions collecting signatures "from DOJ personnel", but it is a DEA pre-deployment initiative. Kept bureau (medium).
4. **DOI / FBMS UPC Chatbot** — proposed enterprise_wide but pre-deployment and functionally scoped to purchase-request initiators; medium confidence.
5. **DOJ / Hootsuite (PAO)** — arguably `office` (single Office of Public Affairs); kept bureau to stay consistent with DOJ's component-level filing convention.
