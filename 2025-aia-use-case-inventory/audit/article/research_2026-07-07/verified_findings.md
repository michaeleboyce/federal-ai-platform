# Verified Findings — Enterprise/Government GenAI Adoption Comparators

Deep-research pass conducted 2026-07-06/07 for the IFP federal AI adoption article. 
Each finding below survived 3-vote adversarial verification (an independent verifier panel voting on whether the claim, as worded, is supported by the cited primary/secondary sources). 
Of 25 claims put to verification, 23 were confirmed and 2 were refuted (see `refuted_claims.md`). 
Claim text, confidence, vote, sources, and evidence are reproduced VERBATIM from the research harness output; nothing below has been paraphrased, summarized, or supplemented from outside knowledge.

---

## Finding 1

**Claim:** UK mechanism: the Government Digital Service centrally coordinated a cross-government M365 Copilot trial (30 Sep–31 Dec 2024) covering 20,000 employees across 12 organisations, with each organisation committing to at least 1,000 licences. This was central coordination with bulk per-organisation licence commitments — the report is silent on who procured/paid, it ran in each department's own tenant, and subsequent UK procurement remained departmental, so it should NOT be described as a shared central platform or centralized procurement.

**Confidence:** high

**Vote:** 2-1 (facts verified verbatim; dissent only on procurement-mechanism framing)

**Sources:**

- https://www.gov.uk/government/publications/microsoft-365-copilot-experiment-cross-government-findings-report/microsoft-365-copilot-experiment-cross-government-findings-report-html (accessed 2026-07-06)

**Evidence:** Primary GOV.UK findings report (published 2 June 2025) verified verbatim: 'GDS organised and ran a cross government trial of M365 Copilot from 30 September 2024 to 31 December 2024, involving 20,000 government employees ... each organisation committing to at least 1000 licences'; exactly 12 participating organisations listed. The verifier's dissent concerned only the interpretive tail ('central-platform ... rather than per-agency procurement'), which this wording softens per the verifier's suggested safer phrasing.

---

## Finding 2

**Claim:** UK outcomes were self-reported and shallow for complex work: trial participants self-reported an average 26 minutes/day saved (report's extrapolation: ~13 working days/year if sustained), with the largest single-task saving on drafting documents (24 min); the tool was strong at summarisation/drafting but weak on nuanced, context-heavy tasks requiring judgement. A separate DBT evaluation (Sept 2025) found 'no robust evidence that time savings are leading to improved productivity' and Copilot users doing Excel analysis slower/worse than non-users.

**Confidence:** high

**Vote:** 3-0 (both merged claims)

**Sources:**

- https://www.gov.uk/government/publications/microsoft-365-copilot-experiment-cross-government-findings-report/microsoft-365-copilot-experiment-cross-government-findings-report-html (accessed 2026-07-06)
- https://www.theregister.com/2025/09/04/m365_copilot_uk_government (corroborating DBT coverage)

**Evidence:** Report verbatim: 'On average, users observed a time saving of 26 minutes per day. If this was to be replicated across a full working year, users could save 13 days' and 'The time savings presented throughout are self reported.' Nuance caveats: the 26-min average was computed from survey range midpoints with the top band capped at 60 min; the 'struggles with nuanced or context-heavy data' quote is participant feedback echoed by the report's own conclusion about 'limitations when dealing with complex data.'

---

## Finding 3

**Claim:** UK DWP's own Copilot trial (3,549 licences, Oct 2024–Mar 2025) was opt-in (volunteers, peer nominations, first-come-first-served, managerial discretion — not default-on) and excluded frontline Jobcentre staff; among survey respondents 90% said Copilot saved time (SUR-regression estimate: 19 min/day across 8 routine tasks; largest: information search 26 min, email 25 min, summarising 24 min), 65% reported daily and 30% weekly usage, and 89% of time-savers reported reallocating saved time to other work. All outcomes were self-reported; the evaluation itself warns non-random allocation 'may have led to an overestimation of Copilot's benefits.' DWP subsequently made a Copilot version available to all staff in April 2025.

**Confidence:** high

**Vote:** 3-0 (all three merged claims)

**Sources:**

- https://www.gov.uk/government/publications/an-evaluation-of-dwps-microsoft-copilot-365-trial/an-evaluation-of-dwps-microsoft-365-copilot-trial (published 2026-01-29, accessed 2026-07-06)

**Evidence:** All figures verified verbatim against the primary gov.uk evaluation: '3,549 licences were allocated ... through a mix of volunteers and peer nominations'; 'frontline operational colleagues (such as those in Jobcentres) did not receive any access'; '90% of users indicated that Copilot helped them save time'; SUR 'average saving of 19 minutes per day'; '65% reported daily usage ... additional 30% ... weekly'; '89% reported reallocating time saved.' Denominators are survey respondents (~48% response rate), and the 89% is conditional on those reporting savings.

---

## Finding 4

**Claim:** Australia's speed mechanism was procurement piggybacking: the 6-month whole-of-government Copilot trial (announced 16 Nov 2023; run Jan–Jun 2024; 5,765+ evaluated licenses, up to 7,769 distributed, across 50–60 agencies) chose Copilot explicitly because it was 'nested within existing whole-of-government contracting arrangements with Microsoft' — first licenses were live ~6.5 weeks after the announcement. Allocation was opt-in agency nomination, not default-on, and this was a ~7,700-seat trial, not an enterprise-wide rollout (APS ≈170K).

**Confidence:** high

**Vote:** 3-0 (both merged claims)

**Sources:**

- https://www.digital.gov.au/initiatives/copilot-trial (DTA full evaluation report, accessed 2026-07-06; Wayback captures 2024-10-25 and 2025-04-21)

**Evidence:** Primary DTA evaluation verbatim: 'The trial involved the distribution of over 5,765 Copilot licenses between January to June 2024. The trial was non-randomised, with agencies nominating staff'; 'Agencies received their Copilot licences between 1 January and 1 April 2024'; decision 'predicated on how swiftly and seamlessly Copilot, as a capability nested within existing whole-of-government contracting arrangements with Microsoft, could be deployed.' Internal source inconsistency to footnote: executive summary says 5,765 (evaluation scope) while Appendix A says 7,769 distributed across almost 60 agencies.

---

## Finding 5

**Claim:** Australia is the cleanest evidence that access alone does not produce depth: even with free provisioned licenses, only about one-third of trial participants used Copilot daily; use concentrated on summarisation and rewriting (Word/Teams favoured; Outlook hampered by version/access barriers); the evaluation attributed low engagement to user capability, perceived benefit, convenience and UI — non-access factors. All outcome measures (up to 1 hr/day saved on summarising/drafting/searching; 64% of managers perceiving efficiency uplift; 40% reallocating time) were self-reported, and the evaluation flags self-assessment and selection bias (66% of evaluation contributors had prior GenAI experience) as limitations.

**Confidence:** high

**Vote:** 3-0 (both merged claims)

**Sources:**

- https://www.digital.gov.au/initiatives/copilot-trial (accessed 2026-07-06)
- https://www.digital.gov.au/initiatives/copilot-trial/microsoft-365-copilot-evaluation-report-full
- https://www.itnews.com.au/news/gov-copilot-trial-unsettled-by-usage-metrics-and-unmet-expectations-612580 (accessed 2026-07-06)

**Evidence:** DTA evaluation verbatim: 'Only a third of trial participants across classifications and job families used Copilot daily. Copilot was predominantly used to summarise information and re-write content'; 'The evaluation methodology relies on the trial participants' self-assessed impacts.' iTnews corroborates from usage metrics (46% used it a few times a week, 21% a few times a month). Coexisting positives (86% wanted to keep it) do not contradict the depth finding; the report itself says usage was 'yet to be ingrained in the daily habits of APS staff.'

---

## Finding 6

**Claim:** Singapore achieved the deepest government workforce penetration found anywhere: about 80% of its 150,000 public officers have used Pair Chat, the government's centrally-built general-use chatbot, as of November 2025 — far above the article's ~38% US federal evidenced-access figure (a fortiori, since ever-use implies access; note the metrics/denominators differ: ever-used-among-150K vs evidenced-access-among-747K AI-eligible).

**Confidence:** high

**Vote:** 3-0

**Sources:**

- https://www.mddi.gov.sg/newsroom/mddi-s-response-to-pq-on-progress-of-adopting-ai-tools-within-public-service/ (ministerial PQ response dated 6 Nov 2025, accessed 2026-07-06)

**Evidence:** Primary government source verbatim: 'About 80% of our 150,000 officers have used Pair Chat, the government's general use chatbot.' Earlier GovTech/UNDP snapshot (60K registered, 20K+ weekly active) is consistent with growth; no downward revision found through June 2026.

---

## Finding 7

**Claim:** Singapore's depth mechanism includes a self-service bot-building platform: public officers have created over 20,000 custom AIBots (task-specific RAG chatbots, e.g., HR queries, budget/procurement guidance) — any officer can build one in under 15 minutes on internal knowledge bases up to Restricted/Sensitive-Normal classification. This pushes adoption beyond standalone chat into task-specific workflows, though AIBots are retrieval chatbots, not systems-of-record integrations in the article's 14%-integration sense, and 'created' does not mean actively used.

**Confidence:** high

**Vote:** 3-0

**Sources:**

- https://www.mddi.gov.sg/newsroom/mddi-s-response-to-pq-on-progress-of-adopting-ai-tools-within-public-service/ (accessed 2026-07-06)
- https://www.developer.tech.gov.sg (GovTech AIBots pages, corroborating: 12,000 bots / 40,000 users / 115 agencies by Feb 2025)

**Evidence:** MDDI PQ response verbatim: 'Officers are also using AIBots to create custom chatbots for specific tasks, such as answering HR queries and providing guidance on budget and procurement processes' and 'Over 20,000 of such bots have been created.' Growth trajectory corroborated by GovTech's own platform pages.

---

## Finding 8

**Claim:** Singapore deployed two adoption-acceleration levers absent from the article's five planks: (1) a MANDATORY AI literacy course for all ~150,000 public officers, launched October 2025 (pre-announced by DPM Gan Kim Yong in Sept 2025); and (2) a cross-agency usage LEADERBOARD ranking agencies by AI use, explicitly to drive inter-agency competition — usage telemetry made visible as a deliberate mechanism.

**Confidence:** high

**Vote:** 3-0 (both merged claims); adjacent default-on claim refuted 0-3

**Sources:**

- https://www.mddi.gov.sg/newsroom/mddi-s-response-to-pq-on-progress-of-adopting-ai-tools-within-public-service/ (accessed 2026-07-06)
- https://www.pmo.gov.sg/Newsroom/DPM-Gan-Kim-Yong-at-the-Annual-Public-Service-Leadership-Ceremony-2025 (accessed 2026-07-06)
- https://knowledge.csc.gov.sg/generating-momentum-for-ai-adoption-in-the-public-service/ (CSC ETHOS Issue 27, Jan 2025, accessed 2026-07-06)

**Evidence:** MDDI verbatim: 'The Government also launched a mandatory AI literacy course for all public officers in October this year' (response dated 6 Nov 2025). Leaderboard, first-person from the Director of the Government Data Division: 'we have recently started publishing a leaderboard of agencies with the highest AI use, driving playful competition amongst agencies.' Caveats: the leaderboard source does not specify public vs internal-to-government publication, is single-source, dates to ~late 2024 with no evidence on continuation; do not render as 'publicly publishes.' Note: a related claim that Singapore auto-launched Pair on officers' browsers (default-on provisioning) was REFUTED 0-3 — do not use it.

---

## Finding 9

**Claim:** Accenture is the largest documented enterprise rollout: deploying M365 Copilot to ~743,000 of ~780,000 employees (~93–95%) as of April 2026, with measured monthly-active usage of 89% in one ~200,000-license tranche and 84% of those surveyed saying they would 'deeply miss' the tool — usage telemetry beyond seat counts, but entirely vendor/company-reported from a single joint Microsoft/Accenture announcement.

**Confidence:** medium

**Vote:** 3-0 (both merged claims); adjacent timeline claim refuted 1-2

**Sources:**

- https://news.microsoft.com/source/features/digital-transformation/accenture-is-rolling-out-copilot-to-a-workforce-the-size-of-denver/ (published 2026-04-27, accessed 2026-07-06)
- https://www.itpro.com/technology/artificial-intelligence/accenture-has-been-trialling-microsoft-copilot-since-2023-now-its-rolling-out-the-ai-tool-to-all-743-000-staff (corroborating trade press)

**Evidence:** Microsoft Source feature verbatim: 'rolling out Copilot across its workforce to around 743,000 people'; 'In one tranche of roughly 200,000 licenses, monthly active Copilot usage reached 89%. In a survey of those same employees, 84% said they would deeply miss the tool.' Caveats: 'rolling out' = license provisioning in progress, not verified active usage by 743K; the 89% MAU was measured on the 200K cohort only; the accompanying '97% complete tasks 15x faster' marketing stat should NOT be cited; a staged-timeline claim (Aug 2023 pilot → 2.5 years to near-universal) was REFUTED 1-2 — do not state a decision-to-universal timeline for Accenture.

---

## Finding 10

**Claim:** Accenture credits its adoption to a tailored change-management program layered on top of license provisioning: one-on-one training with leaders, regular feature/use-case communications, group training sessions, and peer support via Viva Engage — training-and-champions infrastructure, not just seats. This is an attribution claim (what the company credits), verified as such; Accenture sells Copilot change-management consulting and has a commercial incentive to credit change management.

**Confidence:** medium

**Vote:** 3-0

**Sources:**

- https://news.microsoft.com/source/features/digital-transformation/accenture-is-rolling-out-copilot-to-a-workforce-the-size-of-denver/ (accessed 2026-07-06)
- IT Pro, SiliconANGLE, The Next Web coverage (2026-04, corroborating Accenture's own statements)

**Evidence:** Source verbatim: 'The effort was driven by a highly tailored change management and adoption program that included one-on-one training with leaders, regular communications highlighting new features and use cases, group training sessions and active participation on Viva Engage.' Accenture separately told IT Pro it 'focused on change management, including making use of Viva Engage' while scaling to 200,000 licenses.

---

## Finding 11

**Claim:** Moderna is the clearest example of an executive target with a deadline: the company set an objective of 100% generative-AI adoption AND proficiency among all digitally-enabled employees within six months (attributed to CEO Stéphane Bancel), stood up a dedicated change-management team, and ran structured workforce-transformation mechanisms: an AI prompt contest seeding a top-100 'Generative AI Champions' cohort, per-business-line office hours, an internal AI forum with 2,000 active weekly participants, CEO/executive-committee town halls, and incentive programs. Safest phrasing: 'executive-set target with a deadline' (source says 'objective,' not 'mandate'); the claim does not assert the target was hit.

**Confidence:** high

**Vote:** 3-0 (both merged claims)

**Sources:**

- https://openai.com/index/moderna/ (OpenAI case study, ~April 2024; verified via Wayback capture 2025-06-13, accessed 2026-07-06)
- https://www.hbs.edu/faculty/Pages/item.aspx?num=66910 (HBS case 625-005, 'Moderna: Democratizing Artificial Intelligence,' Jan 2025)
- https://www.modernatx.com (Moderna first-party blog, 2023-11-29)
- https://intuitionlabs.ai/articles/moderna-ai-adoption-case-study (corroborating, updated 2026-07-05)

**Evidence:** Case study verbatim: 'Moderna's objective was to achieve 100% adoption and proficiency of generative AI by all its people with access to digital solutions in six months ... assigned a team of dedicated experts to drive a bespoke transformation program'; champions/office-hours/forum/town-halls/incentives passage verified word-for-word. Independently corroborated by the HBS case and first-person interviews with Moderna's Head of AI Products. Mechanism claim is historical (rollout-era) and not invalidated by Moderna's 2025 restructuring.

---

## Finding 12

**Claim:** Moderna's reported usage intensity (vendor-published, unaudited): within two months of ChatGPT Enterprise deployment — 750 custom GPTs company-wide, 40% of weekly active users creating GPTs, and an average of 120 ChatGPT Enterprise conversations per user per week. The 120/week figure is strikingly high and appears solely in OpenAI marketing material with no independent audit anywhere; preserve the hedging if cited.

**Confidence:** medium

**Vote:** 3-0 (verified as a reported-figures claim, explicitly labeled vendor/self-reported)

**Sources:**

- https://openai.com/index/moderna/ (verified via Wayback capture 2025-06-13, accessed 2026-07-06)

**Evidence:** Verbatim: 'Within two months of the ChatGPT Enterprise adoption: Moderna had 750 GPTs across the company; 40% of weekly active users created GPTs; Each user has 120 ChatGPT Enterprise conversations per week on average.' All secondary coverage (Constellation, MobiHealthNews, HBS case) traces back to this single OpenAI case study.

---

## Finding 13

**Claim:** The only rigorous coding-agent evidence warns against self-reported productivity data: METR's RCT (16 experienced open-source developers, 246 real issues, early 2025, Cursor Pro with Claude 3.5/3.7 Sonnet) found developers took 19% LONGER with AI allowed (CI +2% to +39%) — while forecasting a 24% speedup beforehand and, even after experiencing the slowdown, still believing AI had sped them up 20%. A ~39-point gap between measured and perceived productivity means self-reported/survey-based coding-AI numbers (and by extension the UK/Australia self-reported time savings) cannot be treated as outcome evidence. METR's Feb 2026 follow-up does NOT retract this but says developers are 'likely more sped up from AI tools now — in early 2026' (weak evidence on magnitude) — cite as a date-stamped early-2025 finding and a methodological warning, not as AI's current effect.

**Confidence:** high

**Vote:** 3-0 (both merged claims)

**Sources:**

- https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ (accessed 2026-07-06)
- https://metr.org/blog/2026-02-24-uplift-update/ (follow-up, restates original finding verbatim)

**Evidence:** METR verbatim: 'When developers are allowed to use AI tools, they take 19% longer to complete issues'; 'developers expected AI to speed them up by 24%, and even after experiencing the slowdown, they still believed AI had sped them up by 20%.' The follow-up discredits only its OWN new experiment's data (selection effects, pay-rate change, timing measurement problems), not the original RCT. METR lists explicit generalizability caveats (experienced devs on mature 1M+ LOC repos; does not show AI fails to speed up most developers).

---

## Finding 14

**Claim:** The counterweight coding-agent datapoint: GitHub and Accenture ran a randomized controlled trial with DevOps telemetry (not surveys) and reported an 8.69% increase in pull requests, 15% increase in PR merge rate, and 84% increase in successful builds among Copilot-enabled Accenture developers — modest, telemetry-measured positive output effects, corroborated by a peer-reviewed companion study (Cui et al., Management Science 2025, 4,867 developers pooled across three firms), though the Accenture-specific estimates are statistically imprecise and the vendor blog omits sample sizes and confidence intervals.

**Confidence:** medium

**Vote:** 2-1

**Sources:**

- https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-in-the-enterprise-with-accenture/ (published 2024-05-13, accessed 2026-07-06)
- SSRN 4945566 / Management Science 2025: Cui, Demirer, Jaffe, Musolff, Peng, Salz, 'The Effects of Generative AI on High-Skilled Work: Evidence from Three Field Experiments with Software Developers'

**Evidence:** GitHub blog verbatim: 'randomized controlled trial (RCT) ... DevOps telemetry ... 8.69% increase in pull requests ... 15% increase to the pull request merge rate ... 84% increase in successful builds.' Verifier caveats: standard errors up to ~28% of pretreatment mean on Accenture-specific estimates; critics (BlueOptima, devclass) argue vendor bias and ~4% real-world gains but do not dispute the RCT or the reported figures.

---

## Finding 15

**Claim:** SYNTHESIS / GAP ANALYSIS: Across every comparator, cheap or free access provisioned quickly was never sufficient for depth — the UK and Australia trials produced shallow, summarisation-centric use despite fast provisioning, which CONFIRMS (not contradicts) the article's framing that the LLM-access mandate succeeded on breadth but not depth, while also warning that the article's remaining planks (certification, scorecards, budget levers, FedRAMP enforcement, inventory reform) are all access/measurement levers of the same kind. The mechanisms that co-occur with deep adoption in the verified evidence, and are missing from the article's five planks, are: (1) a mandatory workforce training requirement (Singapore, Oct 2025); (2) funded champions/change-management infrastructure (Accenture's tailored program; Moderna's top-100 champions cohort, office hours, forums); (3) visible usage telemetry — leaderboards/dashboards ranking agencies by actual use (Singapore) and MAU-style measurement (Accenture 89%) — instead of narrative use-case counting; (4) executive adoption targets with explicit deadlines (Moderna's 100%-in-6-months); and (5) self-service bot/workflow building for non-developers (Singapore's 20,000+ AIBots) as a bridge from chat toward task integration. On coding agents specifically, no comparator government published deployment data at all, and the two RCTs (METR negative for experienced devs; GitHub/Accenture modestly positive via telemetry) suggest the article should frame the federal zero-coding-agents finding as an evaluation-capacity gap rather than assume large forgone productivity.

**Confidence:** medium

**Vote:** synthesis (built only on claims that survived 3-0 or 2-1 verification)

**Sources:**

- Inference across all findings above (each individually verified; see per-finding sources)

**Evidence:** Cross-source pattern: fast access + shallow usage verified independently in UK GDS, UK DWP, and Australia DTA evaluations (all primary government publications); depth mechanisms verified in Singapore MDDI/CSC primary sources and Accenture/Moderna vendor-primary sources. This is a synthesis judgment, not a single verifiable claim — confidence capped at medium because the mechanism-depth correlation is observational (no comparator ran a controlled comparison of mechanisms) and the enterprise depth evidence is vendor-reported.

---
