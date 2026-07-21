# Drop-in draft: the FedRAMP section

_Rewritten 2026-07-21 from a 38-agent research + adversarial-verification
workflow (all URLs fetched and quote-checked; verdicts in the session
workflow journal). Dashboard-derived numbers are pinned by
`audit/checks/check_fedramp_fact_sheet.py`; chronology facts below carry
their own citations. Recommendations intentionally deferred — placeholder
at the end._

**Supersedes in earlier drafts / spoken framings:**
- "ChatGPT Gov was deployed against existing **AWS** services" → it deploys
  into agencies' own **Microsoft Azure** commercial or Azure Government
  tenants.[^13]
- "StateChat launched December 2024 on Claude" → StateChat launched
  **August 2024 on Azure OpenAI models**, with Palantir building the UI and
  LLM integration; Claude (Sonnet 4.5) is documented as its underpinning
  model only by early 2026, and no public source identifies the contract
  vehicle that brought Claude in.[^21][^22][^23]
- "FedRAMP can't see what's inside packages" → FedRAMP publishes scope down
  to the service; it tracks **adoption** only at the package.
- The 20x trio framing "all authorized, level X": ChatGPT Enterprise was
  certified January 9, 2026 — FedRAMP's December guidance anticipated the
  AI cohort completing at **Low**, and OpenAI announced **Moderate** on
  April 27, 2026; the marketplace now displays the Moderate class against
  the original January date. Gemini for Government and Perplexity remain at
  Low.[^16][^17][^18]

---

## The gorilla in the room

Before any federal employee can type a prompt into an AI tool, someone in
their agency has to answer an unglamorous question: is this software safe
enough for government work? Since 2011, the government's answer-machine for
cloud software has been **FedRAMP** — the Federal Risk and Authorization
Management Program, created by an Office of Management and Budget memo and
written into statute in 2022.[^1][^2] The idea is elegant: instead of
every agency separately auditing every product, one deep security review —
conducted by an accredited third-party assessor, producing a package of
evidence any agency can reuse — clears a product for the whole
government.[^3] Congress even added a legal "presumption of adequacy": an
agency is supposed to accept the existing package unless it can show a
demonstrable need for more.[^4] Authorize once, use everywhere.

In practice, the machine was slow and expensive enough to become the
gorilla in the room for every software category — and then AI arrived
moving faster than any category before it. Getting authorized has
historically cost providers anywhere from hundreds of thousands of dollars
to several million — GAO found provider costs of $300,000 to $3.7 million,
and a former FedRAMP director once put the median near $2.25 million plus
a million a year in upkeep — and took, in GSA's own words, "months or even
years."[^5][^6][^7] A decade in, the marketplace had cleared barely 300
products, against a commercial SaaS universe of tens of thousands.[^8]
Agencies responded the way institutions respond to a slow front door: GAO
found them using hundreds of cloud services that had never gone through
FedRAMP at all.[^9]

## 20x: rebuilding the front door

In March 2025 GSA announced **FedRAMP 20x**, the largest overhaul in the
program's history. The pitch: replace the compliance-paperwork model with
automated, continuously-validated "Key Security Indicators," and cut
authorization from months-or-years to weeks.[^10] It moved fast by
government standards. A Low-baseline pilot ran April through September
2025 (26 complete packages submitted; the first four authorizations issued
in late July).[^11] A Moderate-baseline pilot ran November 2025 through
March 2026. And in August 2025 — twelve days after the federal CIO Council
formally asked for it — FedRAMP began fast-tracking conversational AI
under an **AI Prioritization Initiative**.[^12] That is the lane through
which the frontier chat products finally got their own FedRAMP standing:
ChatGPT Enterprise certified January 9, 2026, Gemini for Government
January 21, Perplexity February 1.[^16]

One design choice matters enormously for what follows: a 20x certification
is issued by the **program**, not by a customer agency. Under the old
model, the first authorization existed because some agency sponsored and
adopted the product. Under 20x, a product can be fully "FedRAMP Certified"
with zero agencies attached — agencies still must issue their own
authorization-to-operate before staff can use it.[^19] The front door got
faster. Whether anyone walks through it became a separate question — and,
as we'll see, one that nobody is systematically answering.

## How ChatGPT actually got in

The revealing part of the ChatGPT story is that adoption ran *ahead* of
authorization at every step — through other companies' paperwork.

OpenAI's models first became FedRAMP-usable through **Microsoft's**
authorizations, not OpenAI's: Azure OpenAI Service was folded into Azure
Commercial's FedRAMP High authorization in August 2023, and into Azure
Government's in August 2024.[^13a] When OpenAI launched **ChatGPT Gov** in
January 2025, the product itself held no FedRAMP authorization at all — by
design. It shipped as software agencies deploy inside their *own* Azure
commercial or Azure Government tenants, inheriting the security posture of
infrastructure the government had already blessed, while OpenAI said
FedRAMP accreditation was "in process."[^13][^14] By then OpenAI was
already claiming 90,000 government users; USAID had signed as its first
federal ChatGPT Enterprise customer back in August 2024.[^15]

Then came the price collapse and the fast lane in the same month: GSA's
OneGov deal put ChatGPT Enterprise at $1 per agency for a year (August 6,
2025), and the AI Prioritization Initiative named ChatGPT its first
fast-track candidate (August 25).[^12][^20] Certification followed on
January 9, 2026 — FedRAMP's December guidance had the AI cohort completing
at the Low baseline, where Gemini and Perplexity landed and stayed — and
on April 27, 2026 OpenAI announced it had reached **Moderate**, the level
most agency work actually requires.[^17][^18] By spring 2026 OpenAI was
citing deployments at Pacific Northwest and Los Alamos national labs and
had signed Accenture Federal to push adoption.[^18a]

And the official ledger? As of the June 2026 marketplace snapshot, the
ChatGPT Enterprise listing records exactly one authorization — the
program's own, dated January 9 — and **zero agency reuses**.[^16] A tool
priced at a dollar, certified at Moderate, reportedly in use across the
government, and the system built to track federal adoption shows nobody
using it. Either agencies aren't issuing ATOs, or they're issuing them and
not telling FedRAMP. Both possibilities deserve exploration.

## How Claude actually got in

Anthropic ran the same play with different partners — and never got a
marketplace listing at all. Claude reached secure government environments
through three piggyback routes: Amazon Bedrock, which carried Claude
models inside AWS GovCloud's FedRAMP High boundary (Bedrock reached High
in August 2024; specific Claude models were approved for FedRAMP High and
DoD IL4/5 workloads there in May 2025);[^24] a November 2024
Anthropic–Palantir–AWS partnership aimed at defense and intelligence
workloads;[^25] and, in April 2025, Palantir's **FedStart** program —
explicitly a service that lets a SaaS product run inside Palantir's
existing FedRAMP High accreditation, no FedRAMP journey of its own
required.[^26] Anthropic's own documentation captures the arrangement's
strangeness: it markets "FedRAMP High" Claude while acknowledging the
underlying authorization belongs to someone else.[^27]

The State Department shows what that plumbing produced. **StateChat** —
the department's internal chatbot, launched August 2024 on Azure OpenAI
models with Palantir as integrator — grew to roughly 45,000 active users
by late 2025 and 58,000 by spring 2026, one of the largest enterprise AI
deployments in government.[^21][^22][^28] Its architecture was
deliberately model-agnostic, and by early 2026 the model underneath it was
Claude Sonnet 4.5.[^23] Which means one of the government's flagship AI
deployments ran on a model from a company with zero FedRAMP marketplace
listings — legally, through other companies' authorizations — and the
official record had no way to show it.

The un-adoption was just as invisible to the ledger, and much faster. On
February 27, 2026, a presidential directive ordered agencies to cease
using Anthropic technology; GSA pulled Claude from USAi and the schedules
the same day.[^29] Within weeks State had swapped StateChat's engine to
GPT-4.1.[^23] Anthropic sued; a preliminary injunction issued March 26,
and GSA acknowledged it in early April.[^30] An entire arc — adoption at
department scale, then forced removal, then partial legal reversal — and
the FedRAMP marketplace never recorded a single event of it.

## The pattern, and the accountability gap

Put the two arcs side by side and the pattern is unmistakable. Every
frontier model reached federal employees through a workaround: Microsoft's
authorization (Azure OpenAI, ChatGPT Gov in agency tenants), Amazon's
(Claude on Bedrock in GovCloud), Palantir's (FedStart), GSA's own umbrella
(USAi, serving agencies without per-agency ATOs — a GSA official put the
OneGov channel's reach at nearly 34 million users), or price-collapsed
OneGov deals that made procurement trivial before authorization
existed.[^31][^32] Our analysis of FedRAMP's own scope catalogs makes the
same point structurally: 129 primary-purpose AI services — Bedrock and
Azure OpenAI included — sit inside 34 already-authorized packages, within
legal reach of 46 agencies, mostly invisible at the package level where
adoption is tracked.[^33]

Meanwhile the tracking system itself runs on the honor system. The
marketplace's "reuse" ledger is fed by agencies emailing signed ATO
letters to a FedRAMP inbox; OMB's 2024 memo requires agencies to provide
authorization data, but GAO has twice documented the gap between the
ledger and reality — in 2019 (15 of 24 major agencies using unauthorized
cloud services) and again in 2024 (9 of 24, still).[^34][^35] And 20x, for
all its genuine acceleration, measures its success in *certifications
issued*, not agencies served: its published phase goals are throughput
goals, compliance-industry observers have warned that program-level
certification may never translate into agency adoption, and the program's
architect in Congress raised the oversight question the week it
launched.[^36][^37] No GAO or inspector-general audit of the 20x pipeline
or the reuse ledger's accuracy existed as of mid-2026.[^38]

That is the state of play: the front door has been genuinely rebuilt and
genuinely faster — and the most consequential AI adoption in government
still happens through the side doors, where the public record cannot see
it. FedRAMP acceleration needs to continue. But someone — OMB, GSA, GAO,
or Congress — needs to start measuring the thing the program was built
for: not how fast products get certified, but whether agencies actually
pick them up.

_[Recommendations section to follow.]_

---

## Footnotes

[^1]: OMB, "Security Authorization of Information Systems in Cloud
Computing Environments" (Dec 8, 2011) — the memo establishing FedRAMP.
https://bidenwhitehouse.archives.gov/wp-content/uploads/legacy_drupal_files/omb/assets/egov_docs/fedrampmemo.pdf
(Rescinded and replaced by OMB M-24-15, Jul 25, 2024:
https://www.whitehouse.gov/wp-content/uploads/2024/07/M-24-15-Modernizing-the-Federal-Risk-and-Authorization-Management-Program.pdf)

[^2]: FedRAMP Authorization Act, §5921, FY2023 NDAA (Dec 23, 2022);
overview: Davis Wright Tremaine, "FedRAMP Codified" (Jan 2023).
https://www.dwt.com/blogs/privacy--security-law-blog/2023/01/fedramp-authorization-cloud-services

[^3]: FedRAMP, "Rev 5: Assessors" (3PAO role).
https://www.fedramp.gov/rev5/assessors/

[^4]: 44 U.S.C. §3613 — presumption of adequacy; agencies retain their own
ATO authority.
https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title44-section3613&num=0&edition=prelim

[^5]: GAO-24-106591, "Cloud Security: Federal Authorization Program Usage
Increasing, but Challenges Need to Be Fully Addressed" (Jan 18, 2024) —
provider costs $300K–$3.7M ($12.4M combined across eight providers);
agency sponsorship mostly $69K–$400K; six persistent process obstacles.
https://www.gao.gov/products/gao-24-106591 ·
https://www.gao.gov/assets/gao-24-106591.pdf

[^6]: FedScoop, "Inside what cloud service providers spend to get FedRAMP
authorized" (Sep 9, 2016) — then-director Matt Goodrich: ~$2.25M median,
~$1M/yr continuous monitoring.
https://fedscoop.com/inside-what-cloud-service-providers-spend-to-get-fedramp-authorized/

[^7]: GSA, "GSA announces FedRAMP 20x" (Mar 24, 2025) — "it can take
months or even years."
https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-announces-fedramp-20x-03242025

[^8]: FedRAMP, "FedRAMP Authorizations Hit 300" (Apr 2023).
https://www.fedramp.gov/archive/2023-04-26-fedramp-authorizations-hit-300/

[^9]: GAO-20-126 (Dec 12, 2019) — 15 of 24 CFO Act agencies used ~247
cloud services never authorized through FedRAMP; OMB oversight gaps.
https://www.gao.gov/products/gao-20-126

[^10]: GSA 20x announcement (n.7); FedScoop, "GSA's FedRAMP 20x plan"
(Mar 2025) — Waterman on Key Security Indicators.
https://fedscoop.com/gsa-fedramp-20x-automation-private-sector/

[^11]: FedRAMP, "FedRAMP 20x: Four Months In and Authorizing" (Jul 30,
2025) — first Low cohort; phase stats at https://www.fedramp.gov/20x/
(26 complete Phase 1 packages; Phase 2 Nov 18, 2025–Mar 2026, first
Moderate pilot authorizations Mar 6, 2026).

[^12]: GSA, "FedRAMP to prioritize 20x authorizations for AI" (Aug 25,
2025)
https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-fedramp-prioritize-20x-authorizations-for-ai-08252025
; Federal News Network, "CIO Council asks FedRAMP to prioritize AI tools"
(Aug 2025) — the Aug 12 letter.
https://federalnewsnetwork.com/artificial-intelligence/2025/08/cio-council-asks-fedramp-to-prioritize-ai-tools-for-approval/

[^13]: FedScoop, "OpenAI launches ChatGPT Gov" (Jan 28, 2025) — deploys in
agencies' own Azure commercial / Azure Government cloud.
https://fedscoop.com/openai-launches-chatgpt-gov-hoping-to-further-government-ties/

[^13a]: Microsoft Azure Government blog — Azure OpenAI in Azure
Commercial's FedRAMP High authorization (Aug 1, 2023)
https://devblogs.microsoft.com/azuregov/azure-openai-service-achieves-fedramp-high-authorization/
; in Azure Government (Aug 12, 2024)
https://devblogs.microsoft.com/azuregov/azure-openai-fedramp-high-for-government/

[^14]: Nextgov/FCW, "OpenAI debuts ChatGPT Gov" (Jan 28, 2025) — no
FedRAMP authorization of its own at launch; accreditation "in process."
https://www.nextgov.com/artificial-intelligence/2025/01/openai-debuts-chatgpt-gov-federal-agency-use/402537/

[^15]: FedScoop, "USAID first federal agency customer for ChatGPT
Enterprise" (Aug 19, 2024).
https://fedscoop.com/openai-chatgpt-enterprise-usaid/

[^16]: FedRAMP Marketplace: FR2533155773 (ChatGPT Enterprise and API
Platform — certified since Jan 9, 2026; 1 authorization, 0 reuses as of
the Jun 12, 2026 snapshot)
https://www.fedramp.gov/marketplace/products/FR2533155773/ ; FR2604952026
(Gemini for Government, Low, Jan 21, 2026); FR2604643715 (Perplexity, Low,
Feb 1, 2026).

[^17]: FedRAMP, "Announcing the initial 20x Phase 2 pilot participants"
(Dec 10, 2025) — the three AI offerings "expected to complete FedRAMP 20x
Low authorizations in January."
https://www.fedramp.gov/2025-12-10-announcing-the-initial-20x-phase-2-pilot-participants/
No contemporaneous January record states the level granted on Jan 9; the
live marketplace now displays Class C (Moderate) against the January date.

[^18]: OpenAI, "OpenAI available at FedRAMP Moderate" (announced Apr 27,
2026). https://openai.com/index/openai-available-at-fedramp-moderate/

[^18a]: Accenture Federal Services & OpenAI partnership (May 14, 2026).
https://newsroom.accenture.com/news/2026/accenture-federal-services-and-openai-partner-to-accelerate-secure-ai-adoption-across-the-federal-government

[^19]: Federal News Network, FedRAMP's Nicole Thompson on authorization
confusion (May 20, 2026) — 20x certification vs agency ATOs.
https://federalnewsnetwork.com/it-modernization/2026/05/risk-compliance-exchange-2026-fedramps-nicole-thompson-on-clearing-up-authorization-confusion/

[^20]: GSA–OpenAI OneGov agreement, $1/agency (Aug 6, 2025).
https://www.gsa.gov/about-us/newsroom/news-releases/gsa-announces-new-partnership-with-openai-delivering-deep-discount-to-chatgpt-08062025

[^21]: FedScoop, "State Department's AI chatbot" (Dec 11, 2024) — StateChat
launched August 2024; available to 75,000+ employees.
https://fedscoop.com/state-department-ai-chatbot-email-drafting-northstar-famsearch/

[^22]: Nextgov/FCW, "State's AI chatbot journey started with a
collaboration" (Sep 30, 2024) — Azure OpenAI models; Palantir UI/LLM
integration.
https://www.nextgov.com/artificial-intelligence/2024/09/states-ai-chatbot-journey-started-collaboration/399933/

[^23]: Nextgov/FCW, "State offloads Claude, underpinning model of flagship
StateChat" (Mar 2026) — Claude Sonnet 4.5 was the underpinning model;
swapped for GPT-4.1 after the Feb 27, 2026 directive.
https://www.nextgov.com/acquisition/2026/03/state-offloads-claude-underpinning-model-flagship-statechat/412022/

[^24]: AWS, "Amazon Bedrock achieves FedRAMP High authorization"
(GovCloud, Aug 2024)
https://aws.amazon.com/about-aws/whats-new/2024/08/amazon-bedrock-achieves-fedramp-high-authorization/
; Anthropic, "Claude in Amazon Bedrock reaches FedRAMP High" (Jun 2025).
https://www.anthropic.com/news/claude-in-amazon-bedrock-fedramp-high

[^25]: Business Wire, "Anthropic and Palantir Partner to Bring Claude AI
Models to AWS for U.S. Government Intelligence and Defense Operations"
(Nov 7, 2024) — note: framed around DISA IL6 (classified) accreditation,
not FedRAMP.
https://www.businesswire.com/news/home/20241107699415/en/

[^26]: Business Wire, "Anthropic Joins Palantir's FedStart Program to
Deploy Claude Application" (Apr 17, 2025) — FedRAMP High / IL5 via
Palantir's accredited environment.
https://www.businesswire.com/news/home/20250417172108/en/

[^27]: Anthropic support documentation, "Get started with Claude for
Government" — markets FedRAMP High capability while the underlying ATO is
held through partner infrastructure; Anthropic holds no FedRAMP
marketplace listing of its own (zero Anthropic products in the Jun 12,
2026 marketplace snapshot).
https://support.claude.com/en/articles/14503590-get-started-with-claude-for-government

[^28]: FedScoop, "State Department agentic AI plans" (2026) — 58,000 users,
>98% of the department. https://fedscoop.com/state-department-agentic-ai-plans/

[^29]: GSA, "GSA stands with President Trump on national security AI
directive" (Feb 27, 2026) — removal of Anthropic from USAi and MAS.
https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-stands-with-president-trump-on-national-security-ai-directive-02272026

[^30]: GSA, "Statement on Anthropic preliminary injunction" (Apr 3, 2026);
suits filed Mar 9, 2026; injunction Mar 26, 2026 (N.D. Cal.).
https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-issues-statement-on-anthropic-preliminary-injunction-04032026

[^31]: GSA, "GSA launches USAi" (Aug 14, 2025) — platform telemetry on
usage; agencies access models without individual procurements.
https://www.gsa.gov/about-us/newsroom/news-releases/gsa-launches-usai-to-advance-white-house-americas-ai-action-plan-08142025

[^32]: Nextgov/FCW, "Nearly 34M users across government can leverage AI
through OneGov, GSA official says" (May 15, 2026).
https://www.nextgov.com/artificial-intelligence/2026/05/nearly-34m-users-across-government-can-leverage-ai-through-onegov-gsa-official-says/413588/

[^33]: IFP analysis of FedRAMP marketplace scope catalogs (snapshot Jun 12,
2026): 129 core-AI services in 34 authorized packages; 46 agencies hold an
ATO on ≥1 such package. Interactive:
https://use-case-inventory.vercel.app/fedramp/coverage/spread#services and
https://use-case-inventory.vercel.app/fedramp/coverage/agencies

[^34]: FedRAMP, Agency Authorization Playbook v4.1 (Nov 17, 2025) — ATO
letters emailed to the PMO
https://www.fedramp.gov/resources/documents/Agency_Authorization_Playbook.pdf
; OMB M-24-15 (Jul 25, 2024), authorization-data requirements.
https://www.whitehouse.gov/wp-content/uploads/2024/07/M-24-15-Modernizing-the-Federal-Risk-and-Authorization-Management-Program.pdf

[^35]: GAO-20-126 (2019, n.9) and GAO-24-106591 (2024, n.5) — 15 of 24,
then 9 of 24, CFO Act agencies using cloud services outside FedRAMP.

[^36]: Denisenko & Lee, "Navigating FedRAMP 20x and the continuous
compliance imperative," Nextgov/FCW opinion (Feb 9, 2026) — certification
throughput vs agency adoption. Phase goals: https://www.fedramp.gov/20x/
https://www.nextgov.com/ideas/2026/02/navigating-fedramp-20x-and-continuous-compliance-imperative/411300/

[^37]: Nextgov/FCW, "GSA launches FedRAMP revamp" (Mar 24, 2025) — Rep.
Gerry Connolly's oversight concerns at launch.
https://www.nextgov.com/modernization/2025/03/gsa-launches-fedramp-revamp/404004/

[^38]: Research gap, affirmatively checked Jul 2026: no GAO or IG audit of
the 20x pipeline, KSI data quality, or marketplace-reuse-ledger accuracy
located; 20x success metrics published by FedRAMP are program-throughput
measures.
