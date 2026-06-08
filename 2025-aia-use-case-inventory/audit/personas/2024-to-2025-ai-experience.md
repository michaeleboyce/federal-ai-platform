# Opening the Laptop: How the Federal Experience of AI Changed, 2024 → 2025

*Eight grounded portraits of what generative AI actually felt like to use inside
federal agencies across two inventory cycles — built from the OMB AI Use Case
Inventories (M-24-10 and M-25-21), IFP's analytical tags, and federal trade-press
reporting.*

---

## Capacity, by the numbers

First, the unambiguous part: federal AI capacity grew sharply on every axis between
the two cycles. The portraits below are about *how* that capacity arrived and how
unevenly it landed — not a decline.

| Measure (distinct use cases) | 2024 | 2025 | Change |
|---|---|---|---|
| Total AI use cases | 2,133 | 3,549 | **+66%** |
| Generative-AI use cases | 527 | 969 | **+84%** |
| Generative AI deployed / in production | ~200 | 468 | **~2.3×** |
| Enterprise-wide generative AI | 28 | 213 | **7.6×** |
| New generative-AI capabilities introduced in 2025 | — | 643 | net new |

Two caveats keep the growth honest. The enterprise-wide expansion is **concentrated**:
of the 213 enterprise-wide GenAI use cases, **HHS alone accounts for 175** — strip it
out and the rest of government shares ~38. And the *number of agencies* with any
enterprise-wide GenAI actually edged **down** (15 → 12): capacity deepened where it
already existed rather than spreading to new agencies. Where a single agency looks
like it lost ground (IRS), it is a filing/consolidation artifact, not a capability
loss — GAO counted 126 active IRS AI use cases in June 2025, far more than the public
inventory shows.

---

## The frame

The federal AI story is usually told in totals: thousands of use cases, hundreds
of generative-AI deployments, year-over-year growth charts. But a count of systems
is not the same as a description of experience. The more revealing question is the
one a single employee asks on a Monday morning: *when I open my laptop, what AI is
actually available to me — and what am I still forbidden to do with it?*

Answered that way, the 2024 baseline is striking. Of the 41 agencies in the 2024
inventory, only **15** had any enterprise-wide generative AI at all — and most of
those were small independent agencies (EEOC, NCUA, FHFA, USCCR) that had simply
switched on Microsoft 365 Copilot. Among the **ten largest agencies by use-case
count, nine had zero enterprise-wide generative AI** in 2024. For the typical
federal employee at a major mission agency, "the agency is doing AI" and "I have AI
at my desk" were two entirely different statements.

By 2025 the picture had moved — unevenly, and in two opposite directions at once.
Some agencies **consolidated**, shedding generic "we use ChatGPT" filings down to
what actually shipped; others **built out** explosively, standing up a purpose-built
chatbot for nearly every bureau. The net growth number hides both motions. What it
also hides is the thing these portraits make visible: the gap between an agency
*having* AI and an employee *using* it on real work — a gap defined less by the
models than by permission, data boundaries, and the slow machinery of authorization.

What follows are eight portraits. Each opens with the same device — *if you opened
your laptop that year, here is what you'd find* — and each is anchored to specific
inventory rows (named, with deployment stage and scope) and to dated trade-press
reporting. Where the data is thin or a claim is inferred, it is flagged.

**A note on one name.** DHSChat, the rollout that anchors the USCIS story, was
introduced under DHS Chief AI Officer **Michael Boyce** — and the asylum-interview
training tool's "I want them to hallucinate" design rationale is his on the record.
The portraits below are written from the perspective of the people these systems
were built for.

---

## 1. USCIS — the immigration officer: allowed to use AI on everything except the actual case

**If you were an Immigration Services Officer in early 2024**, you opened your
laptop to a quietly extraordinary note: DHS had conditionally approved ChatGPT,
Bing/Copilot, Claude 2, and DALL·E 2 for employee use. You could set up an account
with your USCIS email today. The catch was in the same memo — open-source,
publicly available information *only*. No case data, no applicant records, nothing
that lived in ELIS, nothing marked FOUO. You could ask Claude to explain a legal
concept; the moment your work touched a real A-Number, you were on your own. The AI
was cordoned off from the actual job.

Underneath that, real machine-learning infrastructure was already running, mostly
invisible: the **ELIS Evidence Classifier** (which by USCIS's own estimate had
eliminated ~24 million manual page-scrolls and helped push the share of cases
hitting a 30-day adjudication from ~30% to 58%), automated name/DOB harvesting,
sentence-similarity fraud scanning. You didn't prompt these; results just appeared.
The one place an employee was actively *inside* generative AI was a pilot: the
**Large Language Models for an Officer Training Tool** (Implementation &
Assessment, ~$5M), an interview simulator for asylum officers. Its designer leaned
into the model's unreliability on purpose — *"I also want them to hallucinate…
because you're often, in real life, working with an interpreter and there's a lot
of confusion"* (DHS AI Corps director Michael Boyce, Nextgov, July 2024).

**The turn came in December 2024.** Secretary Mayorkas announced **DHSChat** to
19,000+ HQ staff across 10 components — *"like ChatGPT for DHS, but approved for use
with non-classified but internal information"* including FOUO and CUI. *"I wouldn't
want to communicate hubris… humility is required,"* he told Axios (Dec 17, 2024).
By May 2025 DHS CIO Antoine McCord had ordered components to *restrict* commercial
ChatGPT/Claude and cancel the subscriptions (FedScoop, May 23, 2025): the
free-range window closed as the secure internal one opened.

**By the 2025 inventory**, the training pilot had graduated to a deployed **AI
Interview Simulator**; a production **Claude 3.7 (Bedrock) PDF-intake pipeline** was
extracting structured data from real myUSCIS filings; a document-translation
service and **PAiTH** (six role-specific agents, incl. legal research on USCIS's own
INA corpus) were pre-deployment; and the biometrics stack (fingerprint-quality
checks, I-765 face validation hitting court-mandated 30-day deadlines) kept
expanding. The wall between AI and the work was coming down tool by tool — each one
routed through ATO, data-quality review, and pilot first. *A November 2024
post-pilot review (David Larrimore, MeriTalk) found data quality needed
"substantially" more work — which is why DHSChat touched internal documents, not
case records.*

*Sources: Nextgov (Jul/Dec 2024), FedScoop (Oct 2024; May 2025), Axios (Dec 2024),
MeriTalk (Nov 2024), ACT-IAC Evidence Classifier case study. Thin: PAiTH has no
vendor/press yet (DB problem-statement only).*

---

## 2. VA — the clinician: surrounded by AI pilots, almost none on her desk

**If you were a primary-care physician at a VA Medical Center in 2024**, you opened
your laptop to a patient schedule and a VistA (or Oracle Cerner) EHR — and, if you
were at one of a handful of innovation-forward sites, a bulletin about a pilot you
*might* be eligible to join. AI lived in conference rooms and project pages, not at
your desk. The defining fact was documentation: VA clinicians spent an estimated
30–50% of clinical time on notes, much of it after hours, and burnout was VHA's
declared #1 workforce crisis. *"It's solving the problem of physicians having this
overwhelming documentation burden,"* VA AI Product Lead Dr. Kaeli Yuen told MeriTalk
(May 2024); Deputy Undersecretary Dr. Susan Kirsh called the ambient-scribe pilot
*"transformative."*

In the inventory, the ambient scribe was logged simply as **"Ambient AI scribe,"
stage: Initiated, scope: pilot** — an accurate description of how it felt from the
exam room: *initiated, not yet yours.* The live clinical AI sat elsewhere — the
**3M/Solventum Computer-Assisted Coding** tool (O&M) helped coders, not you. VA's
CAIO Charles Worthington named the gap precisely: *"we're in that awkward stage
where most of these tools are a different window… flipping back and forth"*
(FedScoop, Jul 15, 2024).

**By late 2025 the scribe was real.** In October, VA launched the Ambient AI Scribe
at **10 named VA Medical Centers** (Abridge at five, Knowtex — a $15M award
replacing Nuance — at the other five). *"VA Doctors Can Finally Look You in the
Eye,"* ran Military.com (Dec 17, 2025): ~2 hours/day saved at Palo Alto, 800K+
veterans through the pilot, eye contact replacing screen-staring.

**And yet the sharpest line in the entire dataset is here.** VA filed **367** AI use
cases in 2025, 253 inside VHA — and exactly **one** is tagged enterprise-wide
generative AI: **E2 HelpBot**, a travel-expense assistant from the Deputy
Secretary's office, *still pre-deployment.* Every scribe, coding tool, and oncology
classifier operated at bureau or pilot scope. A January 2026 VA OIG review found
VHA had authorized GenAI chat tools for use with patient data but had *"no formal
mechanism"* to manage the patient-safety risk (Nextgov, Jan 15, 2026). The gap
between "the agency has AI" and "I have AI" was, for VA, the whole story.

*Sources: MeriTalk (May 2024), FedScoop (Jul 2024), Military.com (Dec 2025),
Nextgov/FCW (Jan 2026), Becker's, Fierce Healthcare, VA OIG. Flag: E2 HelpBot is the
only enterprise-wide GenAI row and it was not yet live at filing — deployed
enterprise-wide GenAI at VA in 2025 ≈ zero.*

---

## 3. IRS — the revenue agent: an early mover, and a disappearing act in the filing

**If you were an IRS revenue agent or phone assistor in 2024**, you opened your
laptop to an agency that looked like an AI leader. **Microsoft 365 Copilot** was in
enterprise pilot across multiple business areas; Criminal Investigation had its own
Copilot deployment. If you worked the phones, your calls were absorbed by one of the
largest voicebot fleets in government — **eleven** distinct bots (Where's My Refund,
Economic Impact Payment, Advance Child Tax Credit, ACS, AUR, and more), most in
Operation & Maintenance. IRS conversational AI logged nearly **25 million sessions**
in the 2025 filing season, up from 5 million the year before (GAO-26-107522). The
IRS's 2024 footprint: 49 use cases, 28 generative, **4 enterprise-wide.**

**By the 2025 inventory, IRS had effectively vanished from the enterprise tier.**
All four enterprise Copilot use cases came back `retired_2024`. All eleven voicebots:
`retired_2024`. Of 54 tracked Treasury use cases, **32 retired.** Zero new
enterprise-wide IRS use cases.

The honest read is that this is mostly a *filing* story, not a capability collapse.
Two forces explain most of it. **(a)** The Copilot deployments were explicitly
time-boxed validations — filed as "Initiated" and "Acquisition & Development,"
language for security/benefit tests rather than permanent rollouts — and several
concluded on their own terms. **(b)** Reporting consolidation: M-25-21 tightened
what counts as a distinct "use case," and the eleven granular voicebots collapsed
into a smaller set of surviving entries (a "Taxpayer Services Chatbot" and an
"SBSE - Payments Topics Chatbot" continued) — a consolidation the IRS's own taxpayer
advisory council (ETAAC) had *explicitly recommended* in November 2024, warning that
parallel multi-vendor bot channels "may create taxpayer confusion" and prevent the
bots from learning optimally (FedScoop). The decisive evidence that capability did
not actually evaporate: GAO counted **126 active IRS AI use cases as of June 2025** —
far more than either the 2024 filing or the linked-2025 snapshot shows, and the 25M
session count confirms the voicebots were still serving taxpayers. The public
inventory reflects what IRS chose to report under the revised schema, not everything
running.

From inside, the felt narrative was one of churn rather than loss. In 2024, AI was
clearing your call queue and IRMA (the Internal Revenue Manual Research Aid) was
sparing you a hunt through a 15,000-page manual. By 2025 the named Copilot pilots
you'd seen had closed, the voicebots had been folded into fewer consolidated
chatbots, and the tools that survived — ERC chatbot, Taxpayer Services chatbot, the
contract-document assistant — were bureau-scoped production systems. The agency's
*ambition* (IRMA, examiner assistants, the CI evidence-transcription work) was
intact; the tidy enterprise-Copilot story of 2024 simply didn't reappear in the
2025 filing.

*Sources: GAO-26-107522 & GAO-26-108418, FedScoop (ETAAC consolidation report, Nov
2024; Treasury 2025 inventory, Jan 2026), TIGTA (Nov 2024). The "pilot-conclusion
vs. reporting-consolidation" split is the honest read; GAO's 126-active count and
ETAAC's standing call to consolidate bot channels are the key evidence that the
inventory drop overstates any real capability loss.*

---

## 4. State — the diplomat: StateChat, and a year's declassification in 20 minutes

**If you were a Foreign Service Officer in 2024**, you opened your laptop on the
unclassified OpenNet to find **StateChat** — built on Palantir AIP + Azure OpenAI,
approved for Sensitive But Unclassified material — waiting for a prompt. It launched
in August 2024; in week one, 1,900 officers sent a first prompt and the system
fielded 10,000+ queries in a single day. You could paste a draft cable and ask for
ALDAC-style tightening, or feed a foreign press summary and get English back in
seconds. State framed it modestly — *"think of it as your intern."*

The constraint was architectural: StateChat ran only on OpenNet. Classified
reporting stayed on JWICS/SIPRNet, breaking the AI workflow at exactly the moments
of highest stakes. Adoption was uneven — concentrated in translation pilots (J/TIP),
foreign-assistance NLP (F), and media analytics (R). Parallel tools helped:
**Northstar** ingested ~1M global news articles/day across 100+ languages (est.
180,000 PD hours saved/year); **FAMSearch** (Oct 2024) put natural-language query
over the 25,000-page Foreign Affairs Manual.

Beneath all of it ran the quietly remarkable **Machine Learning Declassification
Program**: the Systematic Review Program faces 650,000+ cables/year by 2030, ~6× a
human team's capacity. The model matched reviewer accuracy at 97–99% and replicated
*"a year's labor… in just 20 minutes of computing time"* (American Historical
Association, Oct 2023). In 2025 it's the deployed **AI-Augmented Declassification
Review** (vendor Deloitte), targeting an 80% labor reduction.

**By 2025, StateChat had gone from "Implementation & Assessment" to "Deployed,"**
serving ~40,000–75,000 users globally, with custom GPTs launched in January 2026 and
agentic capabilities on the roadmap. CIO Kelly Fletcher described embassy adoption
growing *"by orders of magnitude."* Secretary Blinken put aggregate savings at
*"tens of thousands of hours."* The unclassified layer of diplomacy — press
analysis, summarization, translation drafts, onboarding synthesis — was now
AI-assisted; the classified cable remained hand-crafted.

*Sources: FedScoop (multiple), State Magazine (Dec 2024), AHA (Oct 2023), Federal
News Network (Oct 2023), State Enterprise AI Strategy (2023/2025). Flag: the 2025
`enterprise_wide` flag reads 0 despite department-wide reach — likely a schema
artifact; press consistently describes StateChat as agency-wide.*

---

## 5. CDC — the epidemiologist: ChatCDC didn't die, it graduated

**If you were a CDC epidemiologist in early 2024**, you opened your laptop to a new
intranet tile: **ChatCDC**, a generative chatbot on Azure OpenAI running inside
CDC's own ATO envelope on the EDAV platform. CDC's acting Chief AI Officer Travis
Hoppe later described the milestone to FedScoop (Sept 18, 2025): CDC was *"the first
federal agency to make ChatGPT available for all of its workers back in 2023."* By
the 2024 filing, five of seven ChatCDC sub-use-cases were already at Operation &
Maintenance. The tile wasn't a pilot; it was expected infrastructure.

You could paste a 40-page MMWR draft and get a structured abstract; ask a RAG variant
(the "Bring Your Own Enterprise Data" mode, opened to a test group Nov 5, 2024) to
search internal SharePoint for prior reports on a pathogen; generate Python for a
SAS-to-Python migration without borrowing a data engineer. Constraints were real —
no PII-laden surveillance data, no live database connection; you worked with
documents. The payoff was tracked from the start: by September 2025 Hoppe reported
**~10,000 workers, 1.2 million chats, ~41,000 hours saved, and a 500%+ ROI**
(FedScoop).

The 2025 lineage *looks* discontinuous — three ChatCDC sub-use-cases show
`retired_2024` — but it's a graduation, not a death. Four were renamed/consolidated;
the brand "ChatCDC" was retired while the tool matured into the enterprise-wide
**"CDC Chatbot"** (now `is_enterprise_wide=1`, Deployed). CDC's public site refers
only to "CDC Chatbot." In fall 2025 the floor rose again department-wide: HHS made
ChatGPT available across the department, then in December rolled out **Anthropic's
Claude for Government**, with Deputy Secretary Jim O'Neill telling staff they could
*"use either tool or compare responses between them"* (FedScoop, Dec 3, 2025).

**By 2025 the analyst's mission toolkit had expanded sharply** (CDC use cases 55 →
103). **Deep Research for Public Health** (OpenAI API) compressed multi-day
literature synthesis into a single run (CDC's internal eval: 94% of prompts
high-quality within ~30 min; 92% of SMEs reporting substantial gains). **SEDRIC +
Palantir AIP** added AI receipt-reading to foodborne-outbreak investigations used by
450+ investigators across all 50 states. **NewsScape** summarized thousands of
articles/day for outbreak signals; the **School Closure Awareness System** monitored
~45,000 districts. Hoppe's own guidance drew the line the tools couldn't cross —
advising *against* agentic tools for *"situations requiring professional judgment"*
(FedScoop, Mar 2026). The AI cleared the synthesis and retrieval layer; the
epidemiologic call stayed human.

*Sources: FedScoop (Sept 2025; Dec 2025; Mar 2026; Feb 2026), Nextgov/FCW (Jan
2025), CDC.gov AI success stories. Flag: the 41K-hours / 500%-ROI / 92%-SME figures
are CDC self-reported.*

---

## 6. DOE / Savannah River — the nuclear engineer: from zero to twenty-one in a year

**If you were a nuclear operations engineer at the Savannah River Site in 2024**,
you opened your laptop to a filing cabinet pretending to be software. The SRS stack
of DOE Orders, NNSA directives, and SRNS procedures runs to hundreds of active
instruments — DOE O 422.1 (Conduct of Operations), 426.2A (nuclear-facility
qualification), facility safety-basis documents — every one a multi-hundred-page PDF,
none searchable in any way that helped at 7:45 AM in front of an operations
supervisor. You navigated by bookmark and institutional memory. And at a site with
an aging nuclear workforce, when the person who *knew* retired, the answer was just
gone. The 2024 inventory shows exactly two SRS rows, both from the national lab,
neither touching the 10,000+ operational workforce. Enterprise GenAI: zero.

**By 2025, Savannah River had one of the densest single-site AI portfolios in the
federal inventory — 21 enterprise-wide use cases, built largely in-house** on Azure
AI Services. The two tools the contractor chose to announce publicly are
**ChatSRS** (general chat, built on OpenAI/ChatGPT via Microsoft) and **AskHR** —
*"There's a lot of hype around AI. We focus on the practical and pragmatic
application of this technology,"* SRS CIO-office director Len Bowers told local media
(WFXG; SRNS press release, 2024). The rest of the fleet, **as disclosed in the OMB
inventory**, rides on the **AccessAI** secure RAG gateway (queries stay inside the
authorized perimeter — the entire point at a nuclear site): **DIRECTIVES** (RAG over
DOE/NNSA directive content — ask it what the current order requires instead of
cross-referencing three PDFs), **Ask CAS** (corrective-action/issues management),
**Ask IT**, **Ask Alan** (interactive qualification training), **mass3**
(STEM-tuned LLMs), **Report Assistant** ("management spends excessive hours
generating and reformatting reports").

The inventory states the anxiety it answers, verbatim: *"Reducing risk of losing
institutional knowledge associated with an aging workforce. Ensure time to
proficiency for junior operators is minimized."* A new engineer with two years in
could now reach an answer that used to require four years of accumulated mental map.

*Sources: HPCwire/DOE-EM (May 2026), WFXG-TV, SRNS press release (2024), Augusta
Business Daily. Honesty flag: only ChatSRS and AskHR have independent press
confirmation; AccessAI, DIRECTIVES, Ask CAS, Ask IT, Ask Alan, mass3 are real filed
inventory rows but DB-only — presented here as "the fleet as disclosed in the OMB
inventory," and all 21 are filed "Pre-deployment" (authorized and deploying, not
fully adopted).*

---

## 7. USDA — the farm-loan officer: a chatbot for every program

**If you were a Farm Service Agency farm-loan officer in 2024**, you opened your
laptop to essentially nothing built for you. Your resource was the Farm Loan Programs
handbook series — 1-FLP through 4-FLP — dense multi-hundred-page regulatory
documents, where a single amendment could arrive as a 200-page PDF mid-quarter,
authoritative but unsearchable in any way that helped while a farmer waited across
the desk. USDA filed exactly **4** generative-AI use cases department-wide in 2024;
for a county loan officer, that was effectively zero. And it wasn't merely absence —
it was prohibition: USDA had formally rated ChatGPT *"high risk"* in March 2023 and
barred third-party generative AI on government equipment, standing up a Generative
AI Review Board that October to vet tools case by case (FedScoop). The institutional
bottleneck wasn't willingness — FSA officers are mission-driven — it was the volume
of technical policy that had to live in one person's head, behind a governance gate
every future chatbot would have to clear.

**By 2025, USDA had gone from 4 to ~24 generative-AI use cases — nearly every bureau
spun one up.** Closest to home: the **FSA FLP Chatbot** (Farm Production &
Conservation; AWS; Pilot) — a RAG chatbot indexed on the 1-FLP–4-FLP corpus,
*"researching program handbooks and generating contextually and factually accurate
responses from highly technical Farm Loan Program information."* Instead of "I think
this is in subpart B, let me check," you type *"current interest rates for direct
farm-ownership loans for beginning farmers?"* and get cited handbook language back.

The pattern across USDA is unmistakable and uniform: every bureau built a RAG chatbot
around its own worst knowledge bottleneck. A Forest Service employee got **ASKTERRA**
(plain-language queries over geospatial data for non-GIS specialists), the **FVS
Helpdesk Chatbot**, a **GIS Help Desk** bot, **Turbo plan** (accelerating NEPA
planning for the Wildfire Crisis Strategy). Food Safety got an inspector drafting
assistant and the **PHIS Export Library Assistant**. The architecture repeats: RAG,
bureau scope, mostly pre-deployment or pilot, no enterprise rollouts. The technology
was ready; ATO and governance were the rate limiter — a May 2026 USDA OIG review
found the department had *"prioritized making use of the technology over setting up
controls,"* with nearly no AI systems carrying a formal authority to operate
(Nextgov). That gap is exactly why the FLP Chatbot reaching *pilot* is a milestone,
not a slow walk. The handbook stopped being something you page through. It answers
your questions.

*Sources: FedScoop (USDA GAIRB / ChatGPT high-risk determination, 2023), Nextgov/FCW
(USDA OIG, May 2026), USDA FY25-26 AI Strategy & AI Inventory, FSA handbook series,
Federal Register (Aug 2024). Flag: the specific chatbots (FLP Chatbot, ASKTERRA, FVS
helpdesk) are DB rows only — no dedicated trade-press coverage; ASKTERRA (internal)
is distinct from the commercial ASKTERRA.io; GovChat likely internal Copilot
branding.*

---

## 8. SSA — the disability examiner: one of the few with enterprise GenAI, and a deep adjudication stack

**If you were a disability claims examiner at SSA in 2024**, you opened your laptop
to a desktop already crowded with AI. The visible newcomer was the **Agency Support
Companion (ASC)** — an enterprise-wide generative chatbot on OpenAI's API; you
watched a 4-minute orientation, agreed never to paste an SSN, and could use it to
draft, summarize, or research. It knew nothing about your cases (no system
connection, an explicit PII prohibition) — but it was *there,* enterprise-wide, one
of the very few agencies that had done that by the 2024 filing. The turnaround had
been fast: as recently as November 2023, SSA had temporarily *blocked* third-party
generative AI on agency devices as a security precaution (FedScoop); within months,
its own governed version was rolled out to everyone.

The backlog was the defining fact: 1.26 million claims pending by May 2024, waits up
to 7.7 months. Into that, AI had been embedded for years — Chief AI Officer Brian
Peltier noted SSA had used AI *"for many years"* before the GenAI wave. **IMAGEN**
read the thousand-page medical file and told the examiner which 23 pages carried a
listing-level finding — credited by Peltier with a **157% year-over-year jump in
disability processing rates**, deployed across 17 states. **Insight** (flagging
quality issues in draft ALJ decisions since ~2018 — support, never decision),
**PATH** (routing likely-favorable cases to faster on-the-record decisions),
**QDD** (expediting clearly-favorable claims), pre-effectuation/targeted-denial
review models, Hyperscience document processing. The generative layer (ASC) was
sealed off from claimant data; the predictive and NLP layer was woven through every
stage of a claim.

**By 2025, twelve use cases were new — SSA's largest single-year AI expansion.** The
**Vocational Assessment Assistant Tool (VAAT)** automated the Dictionary-of-
Occupational-Titles job-code lookup and transferable-skills scaffolding of
residual-functional-capacity analysis — the tedious part of deciding what work a
claimant can still do. **HeaRT** (nationwide March 2025, Microsoft) used GenAI to
transcribe the ~500,000 annual disability hearings, saving $5M/year. The **Policy
Assistance Tool (PAT)** grounded natural-language policy search in SSA documentation,
a more reliable path than the generic ASC for recalling the exact regulatory criteria
for an impairment.

For the examiner, the felt difference was concrete: VAAT removed the
vocational-lookup grind, HeaRT meant never hunting for a hearing recording, PAT sped
policy questions. The throughline matched the rest of government — AI taking the
retrieval, transcription, and scaffolding tasks so the judgment-intensive part of
adjudicating a disability claim stayed with the human examiner.

*Sources: FedScoop (SSA GenAI block, Nov 2023; SecurityStat/Peltier modernization),
Federal News Network (May 2025), Nextgov/FCW (Apr 2025), SSA.gov/ai & SSA blog (Mar
2025), NASI Task Force (Apr 2025). Flag: VAAT has no independent press (DB only); the
IMAGEN 157% figure is SSA-reported (Peltier); ASC's "enterprise-wide in 2024" is the
DB's scale characterization, not a precise launch date.*

---

## What the eight have in common

**1. Permission, not just capability.** The DHS officer's 2024→2025 shift was less
about a new tool than a clear answer to "am I allowed to use this on my actual
work?" Across agencies, the binding constraint in 2024 was rarely the model — it was
the data boundary (sensitive/classified), the ATO, and the governance scaffolding.
2025's biggest unlocks (DHSChat, StateChat, CDC Chatbot) were fundamentally
*permission* infrastructure: a secure perimeter that let AI finally touch internal
data.

**2. Two opposite motions at once.** Agencies that over-reported generic AI in 2024
(IRS's voicebot fleet, ED's 49 identical "Generative AI Usage" filings) *consolidated*;
agencies that had near-nothing (Savannah River 0→21, USDA 4→24) *built out*. The
net "growth" number hides both.

**3. The enterprise gap is the real divide.** Enterprise-wide GenAI use cases nearly
quintupled (28→213), but the *number of agencies* with any actually shrank (15→12) —
the growth concentrated heavily (HHS alone = 175 of 213). VA is the extreme case: 100+
GenAI tools, exactly one enterprise-wide, and it wasn't even live. "The agency has
AI" and "I have AI" remained different sentences.

**4. The chatbot-per-bottleneck pattern.** The dominant 2025 shape is uniform: a RAG
chatbot indexed on one bureau's worst document pile (farm-loan handbooks, DOE
directives, the Foreign Affairs Manual, the IRM, FVS docs), bureau scope, often
still pre-deployment. The same architecture, replicated hundreds of times — federal
AI in 2025 is less a single transformation than a thousand local answers to the same
institutional-knowledge problem.

---

*Generated from `data/federal_ai_inventory_2025.db` (2024 M-24-10 + 2025 M-25-21
inventories, IFP analytical tags) and federal trade-press reporting, by an
eight-agent research team, 2026-06-07. Each persona's full long-form version and
complete evidence appendix (every DB row + every cited URL) is preserved in the
team transcript. Figures reflect the inventory as tagged; where a tool's scope flag
or self-reported metric is uncertain, it is flagged inline.*
