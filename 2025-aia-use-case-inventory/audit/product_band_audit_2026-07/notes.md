# Product band audit 2026-07 — auditor notes

Reviewed all 102 products in `inputs/products_on_banded_rows.csv` against the
four charter checks. Web search used to verify actual product capabilities
for ~20 ambiguous/unfamiliar entries (Ask Sage, USAi, VAO Ally, Unison PRISM,
Doble Test Assistant, FS Pro, Flashpoint, Meltwater, Sprout Social, Medallia,
Relativity, Salesforce Einstein, Genesys Cloud CX, Credal, GrammarlyGO).

## Counts (28 proposed changes across 22 products)

| Field | # rows changed |
|---|---|
| `is_generative_ai` | 12 |
| `product_type` | 12 |
| `is_frontier_llm` | 3 |
| `parent_canonical_name` | 1 |
| `vendor` | 0 |

No vendor errors found — all vendor fields checked out (including
less-obvious cases like GitHub Copilot→Microsoft, Slack/Tableau→Salesforce,
Windsurf→Codeium, Nuance Dragon→"Nuance (Microsoft)").

## Most consequential change

**Synthesia**: `product_type` `computer_vision` → `media_analysis`. Synthesia
is an AI text-to-video avatar generator, functionally identical to HeyGen and
Vyond — both already correctly typed `media_analysis` in this same dataset.
Under the current `computer_vision` label it is **excluded** from seat
modeling entirely; under `media_analysis` its seats land in the **comms**
stratum. Synthesia sits on 2 banded rows with a max band of **50,000+**, so
this single fix moves a large population from "excluded" to "counted" —
the only excluded↔counted flip identified in this audit, at the top band.

Runner-up: **Salesforce Einstein** `is_generative_ai` 0→1 and
`product_type` ml_platform→productivity, also at the 50,000+ max band. The
gen-AI flag fix is high confidence (Einstein Copilot/Agentforce is well
documented, and the row's own logged example use case — "improving the
quality of written communications" — is itself a generative-writing task).
The type change is only medium confidence because "Salesforce Einstein" as
filed could plausibly mean either the classic predictive-ML features or the
newer generative Copilot layer, and I couldn't distinguish which from the
data given.

**Microsoft 365** (the base office suite, not Copilot) was typed
`coding_assistant` — an unambiguous data error with no defensible reading,
at a 10,000-50,000 band. Flagged both `product_type` (→ productivity, high
confidence) and `is_generative_ai` (1→0, medium — the genAI-specific
behavior is already tracked separately under "Microsoft 365 Copilot").

## Systemic pattern: `is_generative_ai=0` on products whose sole purpose is generative AI

Six products — Perplexity, Ask Sage, Azure AI Foundry, USAi (GSA), Palantir
AIP, Credal — were flagged `is_generative_ai=0` despite being generative-AI
gateways or agent platforms by design (plus Grammarly, Relativity, Windsurf,
Salesforce Einstein, and Unison PRISM for product-specific reasons). This
looks like a batch-tagging gap rather than isolated errors — worth checking
whether these were auto-tagged from an older product description that
predates each vendor's 2023-2025 genAI rollout, or whether they were
manually seeded and simply missed the pass.

## Uncertain / not flagged (deliberately left alone)

- **"Adobe" (generic, band 3, 10,000-50,000)** and **"Google" (generic, band
  3, 10,000-50,000)** — these look like agency filings that named the vendor
  without specifying a product. Could plausibly need `is_generative_ai=1`
  given how AI-heavy both companies' current offerings are, but there's no
  way to tell which underlying product was meant, so no recommendation.
- **VAO Ally (GSA)** — could not confirm this is a distinct generative/agent
  product from search; "VAO" appears to be an acquisition-lifecycle
  guidance/resource platform, and "Ally" may just be a feature name within
  it, not a GenAI agent. Current values (`agent_platform`, gen=0) may or may
  not be right — flagging with real confidence would be guessing.
- **Microsoft 365 Copilot (row 1, not the "Chat" variant)** — arguably
  should be `productivity` rather than `general_llm` for consistency with
  how ServiceNow Now Assist (an embedded copilot) is typed, but both map to
  the same "general" stratum and the "chat vs. embedded assistant" line is
  genuinely blurry for Microsoft's Copilot family. Left unchanged.
- **Amazon Q `is_frontier_llm=1`** — Amazon Q is Bedrock-based, not itself a
  frontier model, which would argue for frontier=0 (matching GitHub
  Copilot's and ServiceNow Now Assist's frontier=0 treatment of similarly
  "wrapped" assistants). But Amazon Q Business is also a broad general-chat
  workplace assistant like ChatGPT/M365 Copilot Chat (both frontier=1), and
  the dataset isn't internally consistent enough on this distinction to call
  it either way with confidence.
- **Microsoft Copilot for Security `parent_canonical_name`** — currently
  parents to "Microsoft 365," but Security Copilot is billed and deployed
  separately from M365 (per-SCU pricing, tied to Azure/Defender), so
  "Microsoft" alone might be the more accurate parent. Small band (1,
  101-1000); not confident enough to recommend a specific fix.
- **Google Workspace as Google Calendar's parent** — initially looked like
  an inconsistency (every other Google product here parents directly to
  "Google"), but on reflection this mirrors Microsoft's own tiered
  convention (Microsoft → Microsoft 365 → Teams/Outlook/Defender), so a
  Google → Google Workspace → Calendar tier is plausibly *more* correct than
  the flatter alternative. Left unchanged.
- **FS Pro** — verified via search: this is Information Mapping's "FS Pro AI
  Assistant," a genuinely generative-AI Word add-in for structured
  documentation. Current values (`productivity`, gen=1) are already
  correct — no change needed, included here only because it was one of the
  harder identities to pin down.

## Surprising finding

Two direct competitors in the same functional category ended up in
different strata purely from inconsistent tagging: **Synthesia**
(text-to-video avatars) was `computer_vision` (excluded) while **HeyGen**
(same product category) was `media_analysis` (counted, comms stratum) in
the same input file. This is exactly the kind of silent stratum-mismatch
the charter was written to catch, and it likely wouldn't have surfaced
without the two products appearing side-by-side in the same banded-rows
sample.
