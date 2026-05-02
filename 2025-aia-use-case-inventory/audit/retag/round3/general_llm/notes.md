# Round-3 General-LLM Sub-agency Rollups — Methodology and Findings

## Method

1. **Foundation pack first.** Walked all 96 sub-agencies in `sub_agencies.json`. For each I read `subtree_enterprise_llm_count`, `subtree_llm_count`, `named_tools`, `maturity_tier`, and the first five `sample_use_cases`.
2. **Charter decision rules applied mechanically:**
   - `subtree_enterprise_llm_count >= 3` OR `subtree_llm_count >= 10` → at least Broad.
   - `maturity_tier == "leading"` → at least Broad (and in practice Enterprise where the parent rollup confirmed it).
   - Parent-enterprise rollouts (HHS Claude, VA GPT, StateChat, DOT Productivity Assistant) cascade as Inherited where there is no own deployment.
3. **Round-1 narrative is authoritative for parent claims.** I leaned heavily on the named-tool tables in `audit/retag/general_llm/by_agency.md` to identify which bureaus operate the named systems (e.g., DT operates StateChat; OIT operates VA GPT; OCIO operates SSA ASC).
4. **Web search only for ambiguity.** Three searches total — chatCBP scope, FBI policy chatbot, VA GPT/VHA. Logged in `searches.csv`.

## Distribution (n=96)

- Enterprise: 30
- Broad: 15
- Limited: 26
- None reported: 18
- Inherited: 7

The Enterprise tail is concentrated in HHS (9 of 11 sub-agencies rated Enterprise — NIH, CDC, CMS, FDA, FDA-CDER, ACF, CMS-OIT, HRSA, CMS-OC) and DOE national labs (LANL, PNNL, INL, SRS, LLNL, NR, NREL).

## Top editorial finds

1. **HHS sub-agency density is the story.** HHS already had an "Enterprise" parent rating in round-1, but the sub-agency view shows that *eight* HHS bureaus independently meet the Enterprise threshold — i.e., they aren't just covered by the HHS Claude department-wide deal, they each run their own enterprise LLM (Elsa, ChIRP, ACF Discover/Horizon, CEDAR, CMS AI Workspace). HHS is a federation of LLM-enabled bureaus, not a single department.
2. **DOE federation is even more fragmented than round-1 suggested.** Eight national labs (LANL, PNNL, INL, SRS, LLNL, NRel, NR, plus Broad ratings for ORNL, EM, SLAC) cleared the threshold; meanwhile BNL, FNAL, NETL, NNSA HQ have *no* general LLM at all. The "DOE Broad/Federated" parent rating papers over a ~2× variance in lab-level posture.
3. **NASA GSFC is the outlier center.** ChatGSFC (>7K users) plus an Anthropic Claude pilot plus tier 'leading' put GSFC at Enterprise. JSC, GRC, JPL by contrast are Limited / None reported. The NASA "Broad / Federated" parent rating should explicitly note the GSFC concentration.
4. **DOJ "DOJ-wide CoPilot" is misleading at the bureau level.** The department-wide Copilot is pre-deployment, so I rated component bureaus Broad (FBI, DEA, ATR) where they have their own pilots — and Limited / None for ATF, USMS, Tax, OCDETF, OJP. JMD is the only one I rated Inherited because JMD is the HQ admin office and would be the first DOJ user of the department CoPilot once deployed.
5. **OCC.Chat at Treasury is the cleanest bureau-level Enterprise.** 25 of 26 use cases LLM-tagged; in production since Dec 2024. OCC + ChatOFR (also Enterprise) means *two* of Treasury's five sub-agencies run named bureau-wide enterprise LLMs while the parent stays "Broad / Federated."

## Parent ratings worth revising

- **NASA "Broad / Federated"** is fair as a parent rating but obscures that GSFC alone clears Enterprise. An article should say "Broad/Federated, anchored at Goddard."
- **DOJ "Broad"** is generous given that the named department-wide CoPilot is still pre-deployment and only three components (FBI, DEA, ATR) cleared Broad at the bureau level. Consider downgrading parent to "Limited / Federated pilots" pending CoPilot rollout evidence.
- **DOE "Broad / Federated"** could be more precise: Enterprise at 7 labs, None at 4 labs. The mean is "Broad" but the distribution is bimodal.

## Calls I was unsure about

- **HHS-AHRQ / HHS-CCIIO** — both have low subtree LLM counts but inherit HHS Claude. Rated Inherited rather than Limited because the HHS-wide deal is the stronger fact.
- **NASA-LARC** — rated Broad on the strength of round-1's ALTIRA mention, even though LARC's subtree only shows 2 LLM-tagged use cases. The named tool wins.
- **FEMA** — FEMA OCFO GPT is finance-staff scoped; ReadyAI is content-focused. I rated FEMA Broad rather than Enterprise because no single FEMA-wide chatbot is named, but the multi-system Azure OpenAI presence is real.
- **DHS-TSA / DHS-CISA** — gave CISA Enterprise (round-1 names CISAChat) but TSA Inherited (round-1 has no TSA-specific component LLM). The line between component-Enterprise and Inherited is the named-system test.

## Surprises

- **DOE-SRS Savannah River** — tier 'progressing' + `subtree_enterprise_llm_count=13` is the most concentrated bureau-level enterprise-LLM signal in the entire dataset. ChatSRS is real and broadly deployed.
- **HHS-CMS-OC** — 11 of 12 use cases enterprise-LLM-tagged at the CMS Office of Communications level; suggests CMS communications staff are heavy GitHub Copilot + Claude users.
- **DOE-EE Office of Energy Efficiency** — looks like a general-LLM bureau on first glance (8 LLM-tagged use cases) but the systems are OpenText e-discovery only. Rated None reported despite the count.
- **DOJ-FBOP Bureau of Prisons** — 5 LLM-tagged use cases but the named tool is WellSaid Labs (voice generation), not a general LLM. Rated Limited.
