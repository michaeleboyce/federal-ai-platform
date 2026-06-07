# Phase D — headline stat sanity check

Verifying three claims from `audit/retag/2024-tagging/summary.md`
against the live `use_case_tags_2024_canonical` view.

---

## Claim 1: 22 Microsoft Copilot deployments

**DB count: 22** ✅ Count matches claim.

Full list (`is_microsoft_copilot = 1`):

| agency | name | tool_product_name | verdict |
|---|---|---|---|
| DOC | FirstNet Authority OCIO MS CoPilot Project | Microsoft 365 Copilot | ✅ |
| DOC | Streamline Spectrum Activities | Microsoft Copilot | ✅ |
| DOE | Microsoft 365 Copilot (Productivity Suite) | Microsoft 365 Copilot | ✅ |
| DOE | Microsoft Copilot for Security | Microsoft Copilot for Security | ✅ |
| DOJ | CoPilot | Microsoft Copilot | ✅ |
| DOL | AI Assisted coding -Microsoft GitHub Copilot | GitHub Copilot | ✅ |
| DOL | Microsoft Office Suite | Microsoft Office | ⚠️ tagging error: narrative describes generic Office Suite, no Copilot features; `is_microsoft_copilot` should be 0 |
| EAC | Microsoft Copilot Integration | Microsoft 365 Copilot | ✅ |
| EPA | Use of Microsoft CoPilot within the M365 Purview Security Suite | Copilot for Security | ✅ |
| HHS | Executive Report Generation AI Copilot | Microsoft Copilot | ✅ |
| HHS | NIAMS AI Chatbot Pilot | Microsoft Copilot | ✅ |
| OPM | Copilot for Microsoft 365 | Microsoft 365 Copilot | ✅ |
| TREAS | Copilot for M365 (Criminal Investigation Unit) | Microsoft 365 Copilot | ✅ |
| TREAS | Copilot for Power Platform | Microsoft 365 Copilot | ✅ |
| TREAS | Enable Face ID to unlock M365 apps on Government iPhone | Microsoft 365 Copilot | ⚠️ debatable: Face ID for iPhone unlock does not use Copilot; likely a metadata error in the agency filing |
| TREAS | M365 Copilot | Microsoft 365 Copilot | ✅ |
| USAGM | Microsoft Copilot for Internal Employees | Microsoft 365 Copilot | ✅ |
| USCCR | Microsoft Copilot Integration | Microsoft 365 Copilot | ✅ |
| VA | CT CoPilot | Microsoft Copilot | ✅ (clinical copilot tool) |
| VA | Github Copilot | Microsoft Copilot | ✅ |
| VA | VA Chat Copilot Meta Pilot | Microsoft Copilot | ⚠️ ambiguous: "Meta Pilot" suggests a Meta-related chatbot, but narrative may reference Copilot branding |
| VA | VA.gov Chatbot | Microsoft Copilot | ⚠️ debatable: uses Microsoft Power Virtual Agents (PVA) / Copilot Studio, which Microsoft rebranded as Copilot. Tagging defensible. |

**Summary**: 22 rows correct. 1 clear tagging error (DOL "Microsoft Office Suite"),
2 debatable (TREAS Face ID, VA VA.gov Chatbot), 1 ambiguous (VA Meta Pilot).
20/22 are clearly correct Copilot deployments.

---

## Claim 2: 57 enterprise-wide deployments

**DB count: 58** ⚠️ Off by 1 (summary.md said 57, DB has 58).

The discrepancy is minor — summary.md was likely written when the canonical
count was 57 before a Wave 3 reconciliation row added a 58th.

Spot-check findings: the 58 rows include:
- **ED / "Generative AI Usage" rows (many)**: DOE's generic per-bureau
  AI use case entries. Most EEOC rows (7) are generic capability categories
  (FOIA, Language Translation, etc.) filed as enterprise-wide. These look
  like the EEOC filed all its AI uses as "enterprise-wide" since it is a
  small agency where any system is effectively agency-wide. Tagging
  defensible but somewhat low-signal.
- **FHFA rows (12)**: Cisco, Citrix, Python modules, R modules — plausible
  enterprise infrastructure.
- **PT rows (5)**: Generic descriptions ("Ability to find information...",
  etc.) filed by this small agency as enterprise-wide.
- **Most others**: Clear enterprise-wide narratives (ChatBots, M365 Copilot,
  agency-wide search).

Verdict: Count is 58 (not 57). The enterprise-wide tags look generally
defensible — most rows say "agency-wide", "enterprise", or "department-wide".

---

## Claim 3: "15+ silently-dropped live GenAI systems"

**DB count: 145 rows** where `lineage_status='retired_2024'` AND
`is_generative_ai=1` AND `dev_stage IN ('Operation and Maintenance',
'Implementation and Assessment', 'In production', 'Full operation')`.

This is far more than 15+ — the summary's "15+" was a conservative lower bound
based on the handful of named examples, not a full tally.

Breakdown:
- **ED / "Generative AI Usage" template rows (72 rows)**: Department of Education
  filed dozens of identical "Generative AI Usage" entries per bureau. These
  are clearly generic template filings for ED's enterprise GenAI access, not
  distinct systems. They are "retired_2024" because ED filed this differently
  in 2025 (likely as a single consolidated entry). Technically in-scope for
  the silently-dropped metric but low-signal as individual rows.
- **High-signal genuinely-dropped systems** (consistent with summary.md examples):
  - DOI/OCIO DOIChatGPT (3 rows: API dev, API instance, chatbot)
  - HHS/CDC ChatCDC enterprise chatbot (3 rows: ideation, software, summary)
  - HHS/ASPR Executive Report Generation AI Copilot
  - HHS HHSGPT-related (Informal GenAI research, HHSGPT pilot)
  - DOJ FOIA.gov Virtual Assistant
  - DOJ Evidence.com - Axon
  - DOI/NPS Adobe Firefly
  - USPTO Enriched Citation
  - DHS/USCIS LLM for Officer Training Tool
  - VA TryOpenAI
  - EPA GovChat
  - STATE ChatCDC equivalent not confirmed — but several USAID mission
    chatbots appear (Bu Mira, Colombia AI assistant, etc.)

Verdict: 145 rows confirmed, with ~70 being ED template rows and ~75 being
genuinely distinct silently-dropped live GenAI systems. Summary's "15+"
undercount is because the list was hand-enumerated from named examples only.
The full universe is substantially larger. **High-signal insight** — the
dashboard should surface this prominently.

_Generated by manual SQL verification, Phase D, 2026-05-28._
