# External sources for angles-scout research
All URLs accessed 2026-07-06.

## DoD / non-filer headcount blind spot
- Total federal executive-branch non-postal civilian employment: **2,313,216 (Sept 2024)** / 2,278,730 (March 2024). Source: OPM FedScope, via Pew Research Center, "What the data says about federal workers" (updated 2025-01-07), https://www.pewresearch.org/short-reads/2025/01/07/what-the-data-says-about-federal-workers/ ; FedScope portal https://www.fedscope.opm.gov/
- Largest federal civilian employers, Sept 2024 (OPM), via USAFacts "How many people work for the federal government?" (updated 2025-11-12), https://usafacts.org/articles/how-many-people-work-for-the-federal-government/ :
  - Department of Defense (civilian): **772,549**
  - Department of Veterans Affairs: 482,831
  - Department of Homeland Security: 227,566
- Computed: DoD civilian 772,549 / 2,313,216 = **33.4% (~one third)** of the federal non-postal civilian workforce. (Some secondary summaries say ~36%; the direct FedScope division is ~33%.)
- NOTE: audit TODO §5's "~60%-of-headcount asterisk" is an overstatement for the civilian denominator. DoD alone ≈ a third; all non-filers + the entirely-FedScope-excluded intelligence community (ODNI etc.) push it to somewhat over a third.

## IRS voicebots — silently-dropped-system corroboration
- IRS's own page: "New voice bot options mean faster service and less wait time for taxpayers", https://www.irs.gov/newsroom/new-voice-bot-options-mean-faster-service-and-less-wait-time-for-taxpayers
- IRS "Using voice and chat bots to improve the collection taxpayer experience", https://www.irs.gov/about-irs/using-voice-and-chat-bots-to-improve-the-collection-taxpayer-experience
- FedScoop, "IRS's AI voicebots and chatbots have room to grow, advisory panel says", https://fedscoop.com/irs-ai-chatbot-voicebot-taxpayer-service/
- GAO, "Inside the IRS's Use of Artificial Intelligence", https://www.gao.gov/blog/inside-irs-use-artificial-intelligence
- Timeline: first chatbot Dec 2021; first collection voicebot Jan 2022; authenticated voicebot June 2022; FY2024 performance data reported (voicebots still operational); Agentforce rollout late 2025. The voicebots remained operational through 2024-2025.
- DB cross-check: 11 IRS voicebot rows in the 2024 inventory at "Operation and Maintenance"; ZERO voicebot rows in Treasury's 2025 inventory; only 3 voicebot rows in the entire 2025 corpus, all non-IRS (DHS, DOE, VA).

## Retirement-reporting mechanism (M-25-21)
- OMB M-25-21 requires CAIOs to update the AI use-case inventory annually; the 2025 inventory streamlined stages to Pre-Deployment / Pilot / Deployed / Retired. Source coverage: Inside Government Contracts (Covington), https://www.insidegovernmentcontracts.com/2025/04/omb-issues-first-trump-2-0-era-requirements-for-ai-use-and-procurement-by-federal-agencies/ ; DHS AI use-case inventory page (updates "annually ... and periodically throughout the year"), https://www.dhs.gov/ai/use-case-inventory
- Implication: a "Retired" stage exists in the schema, so the mechanism to report retirements is present; the DB shows only disciplined agencies (VA/HHS/DHS/State) use it, while others drop rows silently.
