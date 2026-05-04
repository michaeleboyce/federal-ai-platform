# LLM-family product gap review — notes

Reviewed gaps for: Azure OpenAI (1166), ChatGPT (1167), OpenAI API (1168),
Claude (1169), AWS Bedrock (1176), Llama (1244).
Source: `audit/undercovered_products_audit.csv` reproduced against
`data/federal_ai_inventory_2025.db.pre-omb-align.bak` (the snapshot whose
use_case ids and product_ids match the CSV).

## Decision counts (55 recommendations across 30 unique gap UCs)

| Decision | Count | Notes |
|---|---|---|
| `link` | 29 | 6 + 14 cross-links to Azure OpenAI, 2 ChatGPT, 1 OpenAI API, 2 Claude, 3 Bedrock, 1 Llama |
| `false_positive` | 24 | 20 OpenAI API (all Azure OpenAI deployments) + 4 ChatGPT (3 "ChatGPT-like" comparisons + 1 Azure-hosted GPT) |
| `tighten_alias` | 1 | Drop bare "OpenAI" alias from product 1168 |
| `unclear` | 1 | UC 31959 State Funhouse — generic platform mention |
| `add_alias` | 0 | None needed; populate matcher's catalog is fine, alias **over-coverage** is the issue |

## The dominant pattern: `OpenAI` → `Azure OpenAI` over-match

**17 of 22 OpenAI-API gap rows are Azure OpenAI deployments**, not direct
OpenAI corp API. The populate matcher correctly skipped these (Azure
OpenAI is a separate product 1166). The audit framed them as "gaps" only
because product 1168's alias list contains the bare token `OpenAI`,
which is a substring of every `Azure OpenAI` reference.

Recommended fix (encoded as a single `tighten_alias` rec on product 1168):

- **Remove** the bare alias `OpenAI` from product 1168.
- **Keep** `OpenAI API` as the only safe alias.
- Optionally add: `api.openai.com`, `openai.com API`, `OpenAI direct API`.
- The populate matcher should also explicitly **exclude** rows where the
  string `Azure OpenAI API` co-occurs (UCs 29764 LivChat, 30964 GenAIMeta,
  31208 NHLBI Chat all literally say `Azure OpenAI API`).

After this fix, the 20 OpenAI-API false-positive rows disappear, and the
real gap shrinks to:

- UC 32634 VA — explicit "OpenAI API" mention → link
- UC 31959 State Funhouse — flag for human review
- (UC 31812 OPM "OpenAI ChatGPT" should link to ChatGPT (1167), not the API)

## Real undercoverage worth wiring up

The 14 cross-link recommendations to **Azure OpenAI (1166)** are the
high-value find from this slice. The 1166 product currently has only 12
linked use cases, but the catalog should reasonably show **~30+**. Major
deployments missed:

- DOE Hanford suite (4 UCs: 29630, 29632, 29642, 29645) — system field is
  literally "Microsoft Azure OpenAI". Probably an ingestion edge case.
- HHS NIH cluster: NHLBI Chat (31208), Section 508 Chatbot (31301),
  Portfolio analysis (31293), RCDC enhancement (31302), GenAIMeta (30964),
  IIS Guidance (30926), Brownfields (30658), Summarize comments (30665).
  Likely many of these were previously matched only by EDAV (a different
  product), missing the underlying Azure OpenAI engine.
- DOJ ATR Knowledge retrieval (30386).
- NASA Data Fracking HRP (31499).
- DHS FEMA Spend Plan Analysis (29151).

Most of these are HHS-on-EDAV — coordinate with the EDAV/agency-platform
review, since they should likely link to **both** EDAV (the platform)
and Azure OpenAI (the underlying LLM).

## ChatGPT (1167) clean-up

Three of the five ChatGPT gap UCs were "ChatGPT-like" comparisons
(false_positive). Two real adds:
- 31824 SBA — vendor TBD but ChatGPT named explicitly for planned use.
- 31812 OPM — name literally "OpenAI ChatGPT" used for general staff LLM
  needs. Currently matched into 1168 because of the bare `OpenAI` alias;
  belongs on 1167.

Note: the **ChatGPT vs OpenAI API distinction** is conflated by the
catalog's alias for 1167 including `GPT-4` and `GPT-4o`. This is also
risky — those models are accessed via the OpenAI API too, not just the
ChatGPT product. Did **not** propose a tightening here because the slice
is bounded, but an integrator should consider whether `GPT-4` and
`GPT-4o` should move to a separate "GPT-4 family" model entry or be
shared between 1167/1168/1166.

## Claude / Bedrock / Llama

All 6 gap rows here are real, clean links:
- Claude 1169: NASA ALTIRA + VA CSOC Andesite (Claude Sonnet on Bedrock).
- Bedrock 1176: ED EDMAPS, HHS Exscribo, VA CSOC Andesite.
- Llama 1244: VA Deep-Learning candidate term lists (CodeLlama).

No alias gaps in these three. The Llama product has a single alias
(`Llama`); a future audit could consider adding `Code Llama`, `CodeLlama`,
`Llama 2`, `Llama 3`, `Meta Llama` for completeness, but no current
free-text matches would be added by those.

## Cross-product linking (integration note)

UC 32362 VA CSOC Andesite AI legitimately deploys **three** products
simultaneously: AWS Bedrock + Claude (Sonnet via Bedrock). Recs include
both. UC 32634 VA Deep-Learning legitimately deploys OpenAI API + Llama
(CodeLlama). When the integrator applies these recs, expect this
many-to-many pattern.

## Things flagged for human review

- **UC 31959 State Funhouse** (`unclear`). The narrative says the
  platform "enables use of general purpose AI and ML tools, including
  open source, OpenAI, and Azure AI models". OpenAI is named separately
  from Azure AI, suggesting direct OpenAI API access too. But it's a
  multi-tenant platform; not clear any specific deployment uses it. A
  human reviewer with knowledge of State's AI tooling should confirm.

- **EDAV cross-coordination**. Several HHS UCs (30926, 30964) sit on the
  EDAV platform; the integrator should ensure the resulting product
  links don't double-count or conflict with EDAV's coverage in the
  agency-internal-platform reviewer's slice.
