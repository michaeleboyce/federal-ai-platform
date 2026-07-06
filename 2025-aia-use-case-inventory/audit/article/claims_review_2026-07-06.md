# Claims review — 2026-07-06

Point-in-time review of the article drafts against the live DB and the
FedRAMP fact base. **This file is never edited after the fact** — a later
review gets a new dated file, so the record of when each thing was known
stays intact. Conventions: `audit/article/README.md`.

Drafts reviewed:
- `drafts/2026-07-06-adoption-article-draft.md` (current working draft)
- `drafts/mandate-moment-prior-draft.md` (superseded prior draft)

## 0. Dates legend

| What | Date |
|---|---|
| This review / all DB verifications below | 2026-07-06 |
| `fact_sheet.md` generation (against `data/federal_ai_inventory_2025.db`) | 2026-07-06 |
| FedRAMP marketplace snapshot in the DB | 2026-06-12 |
| Live fedramp.gov re-check of the 20x trio listings | 2026-07-03 |
| Press-source URL fetch-verification for §7 beats | 2026-07-03/05 |

## 1. Verified claims (safe to publish, phrased as noted)

### "Claude Code" appears exactly once in the whole corpus — VERIFIED 2026-07-06

The new draft's flagship claim ("In the thousands of use cases listed,
only once … is 'Claude Code' mentioned") is exactly right.

- **Method:** full-row scan (every column, including `raw_json`) of both
  `use_cases` (3,660 rows) and `consolidated_use_cases` (901 rows — the
  900-row Appendix-B grid plus the DOL PRISM/Ally addendum),
  case-insensitive match on `claude code`.
- **The one hit:** DOI's Appendix-B consolidated template row for
  **"Generating code using AI."**, `commercial_product` = "GitHub Copilot
  for Visual Studio; Schoology; Claude Code; Splunk AI Assistant for SPL
  (Splunk Search Processing Language)".
- **Phrasing constraint (guardrail 5):** this is a template *checkbox
  listing*, not an individual use case filing and not evidence of a
  managed deployment. The draft's wording — "under a single line about
  the Department of the Interior's use of AI to generate code" — is
  correct; keep it that precise.
- **Pinned:** `audit/checks/check_article_guardrails.py::test_claude_code_appears_exactly_once`
  (signature-keyed; a source reload that changes the count fails `make check`).
  Also surfaced in `fact_sheet.md` §2.

### "Claude" (any form) appears in 11 individual use cases — VERIFIED 2026-07-06

DHS (PDF Intake for myUSCIS), DOC (Anthropic - Claude For Government),
DOE ×3 (Claude Anthropic Enterprise; Anthropic Claude; Anthropic Claude
Pilot), NASA ×2 (ChatGSFC; General AI LLM Chatbot for NASA CUI Data),
OPM (Anthropic Claude), VA (CSOC AI Analyst Accelerator / Andesite AI),
EAC ×2 (Internal Generative AI Tools for Staff Productivity; Routing
emails from shared inboxes). Any Claude-related framing must carry the
Anthropic cease-use date-stamp (see §2).

## 2. Stale prior-draft claims — DO NOT REUSE

Each entry: the prior-draft claim → the superseding fact with event dates
→ where the current number lives.

### 2.1 "The full ChatGPT enterprise is actually not yet FedRAMP'ed; it is in-progress"

**Stale.** ChatGPT Enterprise and API Platform was authorized
**2026-01-09** (Moderate, 20x); Gemini for Government **2026-01-21**
(Low); Perplexity Enterprise **2026-02-01** (Low). As of the
**2026-07-03** live check, each shows one program-level authorization and
**zero recorded agency reuses** — the sharper current fact is that
adoption routed around the ledger (OneGov, USAi), which *strengthens* the
prior draft's "the problem is what happens after authorization" argument.
Source: `fact_sheet.md` §7 Beats 2–3; pins in
`check_fedramp_fact_sheet.py`.

### 2.2 Any Anthropic-positive framing without a date-stamp

**Stale.** Presidential cease-use directive **2026-02-27**; GSA removed
Claude from USAi and terminated the MAS listings (FedScoop, 2026-02-27 —
fetch-verified 2026-07-03/05). "HHS rolled out Claude in December
[2025]" is only publishable with the ban date-stamped. The prior draft's
"Claude 4 to Claude 5" trial-authorization example and "Anthropic's
models … achieved FedRAMP high" line both need rework.

### 2.3 "Only HHS has publicly deployed [USAi/OneGov] at scale / GSA partnering with 15 agencies"

**Stale.** As of **2026-04** (Nextgov/FCW), USAi serves 15 agencies with
a waitlist and moves to cost-recovery pricing in FY2027 — no longer free,
which matters for the budget-lever section. Source: `fact_sheet.md` §7
Beat 3, footnote 7 of `fedramp_section_draft.md`.

### 2.4 "Only three agencies—VA, NIH, and CBP—have publicly adopted coding agent-specific solutions"

**Stale.** The 2025 inventory shows **70** individually-filed
coding-assistant use cases across **16 agencies** (ED 13, HHS 10, DOC 9,
DOE 8, Treasury 6, DHS 6, …), 26 of them deployed. The *direction*
survives — coding lags chat badly, and agentic coding specifically is
nearly absent (see §1 Claude Code) — but "only three" is not defensible.
Source: `fact_sheet.md` §2 (row-by-row audited).

### 2.5 Enterprise-GenAI agency counts

**Use 21 (2024) → 24 (2025).** Never reuse: the 15-agency
enterprise-LLM list in `KEY_FINDINGS.md` (pre-correction artifact, file
now carries a deprecation banner), or the 15→12 figure from earlier
drafts (artifact of unapplied scope corrections — `fact_sheet.md` §1
caveat). The 2025 list of 24 is in `fact_sheet.md` §1.

## 3. Placeholder → source mapping (new draft)

| Placeholder / gap in the 2026-07-06 draft | Fill from |
|---|---|
| "[statistics here]" after "bore fruit" | `fact_sheet.md` §0/§1/§5: 3,660 individual use cases (2,133 in 2024); GenAI 527 → 1,005 by IFP tag; deployed GenAI 200 → 311; 699 net-new GenAI capabilities; 561 general-purpose LLM-access entries; enterprise-wide GenAI 21 → 24 agencies |
| "average civil servant … you likely [fill in]" before/after vignette | IFP access tiers, `fact_sheet.md` §7 Beat 4 (State ~95–100%, DOE ~81%, HHS ~50% vs Treasury ~5%, HUD ~0.15%, SBA 0%) + `audit/retag/general_llm/by_agency.md` |
| "SBA or HUD are still lagging" | §7 Beat 4 rows — SBA holds ATOs on packages with 41 core-AI services in scope, 0% identified staff access; HUD pilot ~0.15% |
| unfinished "use case inventories still do not clarify is" | §3 analytics-opacity point: the inventory format cannot answer "can an analyst use AI on real agency data" |
| FedRAMP / "What is preventing the next step" material | `fedramp_section_draft.md` (drop-in, numbers pinned) |
| coding-gap section | §2 stage mix (26 deployed / 22 pre-deployment / 9 pilot) + §1 Claude Code fact above |

## 4. Claims needing OUTSIDE sourcing before publication

1. **"we have heard tell … other agencies have been able to adopt it as
   well—DHS, DoW"** — anecdote, no public source yet. Note the data
   cannot corroborate OR refute: DoD/DoW filed no 2025 individual
   inventory (TODO.md §5 — the "60%-of-headcount asterisk"), and DHS's
   filings show custom GenAI coding assistants but not Claude Code.
   Tracked in `audit/retag/TODO.md` §2.
2. **"compressed a normally decade-long process into a couple of
   years"** — the DB gives the AI-side slope (GenAI roughly doubled YoY;
   24 agencies enterprise-wide) but the comparison needs an external
   historical baseline (cloud / PC / email federal adoption curves).
   Tracked in `audit/retag/TODO.md` §2.
3. **"over [fill in here] pages of strategies and policies since 2023"**
   — needs research; not derivable from this DB.
4. Prior-draft carried-over items still owed press verification
   (TODO.md §2): DOJ-wide GitHub Copilot, VA OIG Jan-2026 PHI advisory,
   DHS commercial-AI revocation counter-trend.
