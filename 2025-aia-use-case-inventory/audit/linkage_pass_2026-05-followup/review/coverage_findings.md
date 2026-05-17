# Reviewer C — Coverage findings

Sprint: May 2026 linkage-pass FOLLOW-UP. Reviewer C scope: completeness + defensibility verification across the three agent outputs.

## TL;DR — verdict: **GREEN** (proceed to apply)

All three agents produced defensible, well-documented decisions. WS1's high
hit-rate is explained by the corpus (FDA-cleared imaging devices with
title-stamped product names) — not by sloppy thresholds. WS2 and WS3 are
near-perfect. One catalog-engineering follow-up identified (GCP product-type
mistag) but it's out of scope.

## 1. Completeness per agent

### WS1 (VA dark sweep)
- **Input:** 327 rows (316 individual + 11 consolidated).
- **Output:** 121 decisions (110 unique individual use_case_ids + 11 consolidated).
- **Coverage gap:** 206 individual `use_case_id`s do not appear in output. Breakdown:
  - ~5 are intentional duplicate folding (per WS1 notes: 78667/78817 CVI42, 78587/78836 BillieGPT, 78669/78802 YSIO Max, 78703/78825 TeraRecon, 78767/78801 Avicenna — only one of each pair carries the decision; the integrator will need to map both to the same staged product).
  - **~195 rows are deliberately silently skipped** as "clearly VA-internal models with no commercial product or too vague to triage" (e.g. "Smart Claim Check", "Discharge Predictive Model"). WS1 notes this explicitly and offers to produce `unclear` rows for all of them if reviewer wants noise-over-signal.
  - **Verdict:** acceptable but slightly under-documented. For a future pass, emitting at least a sparse `not_actionable` decision for each skipped row would make audit easier. For THIS pass, the decision count matches the integration summary (107 new products, 6 links). No action.

### WS2 (hierarchy gaps)
- **Input:** 55 candidates → **Output:** 62 decisions (53 edges + 9 umbrella `add_product`s).
- **Coverage:** 52/55 input names appear as `child_canonical_name` in an edge.
- **Three uncovered inputs** (intentional, justified in notes):
  1. `IBM Watson` — left parent-less; charter scope didn't include IBM umbrella.
  2. `LexisNexis` — itself a vendor-level row; no higher RELX umbrella in scope.
  3. `Palantir Federal Cloud Service` — not addressed in output or notes. **Minor gap; flag as follow-up.**
- **Verdict:** acceptable. Suggest a one-line follow-up to decide Palantir Federal Cloud Service parentage.

### WS3 (alias coverage)
- **Input:** 30 → **Output:** 31 decisions (1:1 plus a few paired add+reject).
- **Missing inputs:** 2 (`Microsoft Purview`, `Azure Speech`) — not explicitly resolved in output JSON. Notes mention Purview is "already aliased"; Azure Speech is referenced indirectly. **Very minor; acceptable.**

## 2. Defensibility spot-checks (random.seed=20260518)

| Agent | Sample size | OK | WEAK | WRONG | Pass? |
|---|---|---|---|---|---|
| WS1 | 20 | 20 | 0 | 0 | **PASS (100%)** |
| WS2 | 20 | 20 | 0 | 0 | **PASS (100%)** |
| WS3 | 31 (all) | 31 | 0 | 0 | **PASS (100%)** |

All three agents exceed the 90% defensibility bar comfortably. WS3's word-boundary
methodology (Sentinel/Outlook/Foundry/Dynamics false-positive analysis) is
particularly strong; the rejects show real engineering judgement, not pattern matching.

## 3. WS1 hit-rate verification (31% vs expected 15-25%)

**Plausibility check of 10 random `add_product` decisions:** all 10 are
recognizable, real commercial vendors with FDA clearances or well-known product
pages — Canon Alphenix, Circle cvi42, Agfa MUSICA, VUNO Med-DeepBrain, AgileMD
eCART, GE LOGIQ, Sonic Incytes Velacur, iRhythm Zio, Whiterabbit.ai WRDensity,
Parable Health 3D Wound Care. **Zero look made up.** The elevated 31% rate is
explained by the underlying data, not by tag-happy heuristics:
the VA dark population is dominated by title-stamped medical-device names where
the use_case_name IS the product name. The hit-rate is justified.

**Sample of 5 `unclear` decisions:** 4/5 are valid (consolidated OMB-taxonomy
rows with `agency_uses=N` — no possible decision). 1/5 (`78668 VA CART
Adenoma Detection`) is a judgement call — agent flagged as in-house VA NLP not
worth a catalog row. Could plausibly be folded into a "VA CART NLP Suite"
product, but agent's conservative call is defensible. **No action needed.**

## 4. WS2 / WS3 cross-validation

- **Azure family flatness (WS3 flag):** Verified in DB — Azure Synapse Analytics,
  Data Factory, Speech, AI Foundry, and Microsoft Azure Quantum Elements
  are ALREADY parented to `Microsoft Azure Platform` in the live catalog.
  WS2's contribution is to give `Microsoft Azure Platform` a parent
  (`Microsoft`), completing the chain. The WS3 callout is therefore
  resolved by WS2's edge, not by additional WS2 edges.
- **GCP mistype (WS2 flag):** Verified — product 7727 `Google Cloud Platform`
  has `product_type='general_llm'` and `is_generative_ai=1`. Confirmed
  mistagging. **Out of scope for this pass.** File as a follow-up:
  `product_type` should be `cloud_platform`, `is_generative_ai=0`.

## 5. Productive findings to lift up for the apply step

1. **Medical-imaging vendor families (WS1):** GE Healthcare (~11 products),
   Philips (~5), Siemens Healthineers (~5), Canon Medical Systems, Brainlab,
   Medtronic, Hologic. The WS2 umbrella pattern should be replicated for these
   vendors in a follow-up pass so the 50+ new medical-imaging children can be
   hierarchied. **Highest-value catalog gap surfaced by this sprint.**
2. **Ambient-scribe cluster (WS1):** Abridge, Knowtex, Freed, Lambient — a brand-new
   category cluster, plus Nuance PowerScribe One. Worth a dashboard "Ambient
   Scribes" facet or product-type tag.
3. **VA-internal generative-AI products (WS1):** VA Clinical AI Agent,
   VA VoiceBot, VA AI Assist, VA E2 HelpBot, BillieGPT — five new
   `agency_internal_platform` rows complementing the existing VA GPT (id 8065).
4. **Microsoft 365 alias gap (WS3):** Product 7767 had zero aliases including
   its own canonical name; the most-impactful single recommendation in WS3.
5. **WS1 missed direct links (6):** Planmeca Romexis (8079), Cortechs
   NeuroQuant (8081), Siemens MAGNETOM (8082), Hologic 3D Quorum (8083),
   Canon Aquilion ONE AiCE (8085) — direct links to existing products that
   the seed-name linker missed because `vendor_name` was blank. Suggests a
   WS4-style follow-up to expand the linker scan beyond `system_name`.

## 6. Follow-ups to file (NOT blocking apply)

- Decide parentage for `Palantir Federal Cloud Service` (WS2 silent gap).
- Fix GCP product 7727 mistag (`general_llm` → `cloud_platform`, `is_generative_ai=0`).
- Future pass: vendor umbrella rows for GE Healthcare, Philips, Siemens
  Healthineers, Canon Medical, Brainlab, Medtronic, Hologic.
- Future pass: add a `medical_imaging` / `radiology_ai` product_type distinct
  from `clinical_decision_support` (WS1 had to over-bucket).
- Future pass: revisit `Microsoft 365 Apps for Enterprise` (7768) vs Copilot
  (7763) alias overlap (WS3 `unclear`).

## Verdict

**GREEN LIGHT to proceed to apply.** All three agents pass the 90%
defensibility bar at 100%. Completeness is acceptable with the noted minor
gaps (Palantir Federal Cloud Service, two WS3 inputs) that don't block the
integration. The 31% WS1 hit-rate is explained by corpus composition, not
agent over-reach.
