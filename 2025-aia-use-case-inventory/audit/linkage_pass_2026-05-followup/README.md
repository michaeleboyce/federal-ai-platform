# Linkage Pass FOLLOW-UP — May 2026

Three-workstream follow-up to `audit/linkage_pass_2026-05/`. Drives
individual coverage from 30.4% → **37.6%** (1,336 / 3,549 use cases now
linked, vs 1,079 after the prior pass and 832 baseline).

## Headline outcome

| Metric | Pre-followup | Post-followup | Δ |
|---|---:|---:|---:|
| products | 537 | 643 | **+106** |
| products with parent | 80 | 134 | **+54** |
| use_case_products | 1,236 | 1,711 | **+475** |
| consolidated edges | 651 | 671 | +20 |
| use_cases with ≥1 link | 1,079 | 1,336 | **+257** |
| individual coverage | 30.4% | **37.6%** | +7.2 pts |

The replay multiplier — **+376 of the +475 use_case edges came from
`make fix`, not the direct apply** — is the main story. Once
WS3's 12 bare-name aliases (Microsoft 365 had zero aliases before this
pass; Power BI, Synapse Analytics, OneDrive etc.) land in `product_aliases`,
the heuristic `populate_use_case_products` picks them up across the
entire 3,549-row corpus.

## Workstream breakdown

| WS | Slice | Decisions | Key outputs |
|---|---|---:|---|
| WS1 | VA dark sweep (316 indiv + 11 cons) | 121 | 99 add_product, 6 link, 15 unclear, 1 false_positive. **31% hit rate** vs 8% all-agency baseline — VA medical-imaging really is concentrated. |
| WS2 | Catalog hierarchy gaps | 62 | 53 hierarchy edges + 9 umbrella add_products (Amazon, Amazon Web Services, Google, Microsoft, Thomson Reuters, ServiceNow, Cisco, Salesforce, Adobe). |
| WS3 | Alias coverage audit (30 thinly-aliased parents) | 31 | 12 add_alias, 17 false_positive, 2 unclear. Biggest find: **Microsoft 365 had zero aliases**. |
| WS4 | Code change (no agent) | — | `product_resolution.use_case_search_text` now includes `expected_benefits`. `scripts/seed_linkage_pass_inputs.py:_candidate_products` now applies word-boundary check (mirrors production linker). |

## Pipeline

1. `scripts/seed_linkage_pass_2026_05_followup_inputs.py` (Foundation)
2. 3 parallel Claude Code labelers (WS1, WS2, WS3) + 1 code-review on WS4
3. `scripts/integrate_linkage_pass.py --pass-dir audit/linkage_pass_2026-05-followup`
4. 2 parallel reviewers (Validity + Coverage)
5. `scripts/apply_linkage_pass_2026_05.py --pass-dir audit/linkage_pass_2026-05-followup --apply`
6. `make fix` (full replay; +376 edges from WS3 aliases + WS4 scan extension)

## Notable findings to lift up

- **VA medical-imaging long tail**: 11 GE Healthcare products, 6 Philips,
  6 Siemens Healthineers, 4 Brainlab, 3 Medtronic, 3 Canon, plus Aidoc,
  RapidAI, Avicenna, iCAD, ScreenPoint Transpara, Volpara, Whiterabbit,
  VUNO, Volta Medical, Butterfly, CathWorks FFRangio, TeraRecon, Lantheus
  aPROMISE, Edwards Acumen HPI, iRhythm Zio.
- **Ambient scribe cluster**: Abridge + Knowtex + Freed + Lambient +
  Nuance PowerScribe One — 5 vendors newly catalogued.
- **VA-internal AI products**: VA Clinical AI Agent, VA VoiceBot, VA AI
  Assist, E2 HelpBot, BillieGPT (5 federal-built products vendor =
  "U.S. Department of Veterans Affairs").
- **Microsoft 365 alias gap** (WS3): the entire Office suite was nearly
  unfindable by the linker because Microsoft 365 had no `Microsoft 365`
  alias — only "Microsoft 365 Copilot" longest-match absorption
  prevented total dark spots.

## Reviewer verdicts

- Coverage Reviewer C: **GREEN** — 100% defensibility on 60 spot-checks
  (60 OK / 0 WEAK / 0 WRONG); 31% WS1 hit-rate justified by corpus.
- Validity Reviewer V: 17 FAILs reported, all **false alarms** — the
  validator's catalog snapshot was missing children that actually exist
  in the live DB. Verified via direct sqlite lookup before apply; all
  apply targets resolved.

## Replay safety

All CSVs (`expanded_product_catalog.csv`, `product_hierarchy_edges.csv`)
are extended in place. Wired into `Makefile fix` after the first
linkage-pass apply line. Idempotent.

## Out of scope (deferred)

- Non-VA dark sweep (NASA 384, HHS 245, DOI 219, DOC 195 etc.). Agent C
  validated WS1's high hit-rate is medical-imaging-specific; other
  agencies' dark rows skew toward research code / generic in-house tools
  with much lower expected yield.
- Google Cloud Platform mis-typed as `general_llm`/`is_generative_ai=1`
  (WS2 flagged). Out of scope but worth a separate retag.
- Palantir Federal Cloud Service silent gap in WS2 coverage (Reviewer C
  flagged).
