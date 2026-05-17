# WS1 VA dark-sweep notes

## Decision counts

- Total decisions: 121 (110 individual + 11 consolidated)
- `add_product`: 99
- `link`: 6
- `unclear`: 15 (11 are the consolidated OMB-taxonomy rows, all with agency_uses=N)
- `false_positive`: 1

Of the 316 individual rows, ~99 yielded an `add_product` proposal (~31% productive hit-rate, vs the 15-25% expected). The slice is unusually productive because VA's dark population is dominated by FDA-cleared medical-imaging devices whose use_case_name IS the product name, and whose vendor_name / system_name columns are blank in the export.

## Surprising findings

1. **Medical-imaging vendor explosion.** The "long tail" the charter anticipated is enormous: GE Healthcare alone has 11 distinct products (SIGNA Artist AIR Recon DL, TrueFidelity CT, EchoPAC, Voluson Expert, Critical Care Suite, Vivid iq, Venue Fit, Discovery MI, Omni Legend, Logiq E10, Vivid E80/E90/E95, AMX Portable, Xeleris V, FastStroke). Philips has 5 (EPIQ/Affiniti, QLAB, eCareManager, Vereos PET/CT, Smart Collimation, Voluson). Siemens has 5 (SOMATOM go., MAGNETOM, ACUSON Sequoia, Biograph, syngo, YSIO Max). Brainlab has 4 (Elements, Spine Planning, Cranial Navigation, Cirq). Canon, Medtronic, Hologic each have 3+. The catalog should consider parent rows for these vendors so child products can be hierarchied (Microsoft pattern).
2. **Ambient-scribe cluster.** Four distinct ambient-scribe products are deployed at VA: Abridge, Knowtex, Freed, Lambient. None were in the catalog. Plus Nuance PowerScribe One (radiology variant of Dragon).
3. **VA-internal generative-AI tools.** Five VA-built products: VA Clinical AI Agent, VA VoiceBot, VA AI Assist, VA E2 HelpBot, BillieGPT. All marked `agency_internal_platform` in notes per charter guidance. (VA GPT already in catalog at id 8065.)
4. **Three direct catalog links** beyond the proposals: 78560 → Planmeca Romexis (8079), 78700 → Cortechs NeuroQuant (8081), 78701 → Siemens MAGNETOM (8082), 78702 → Hologic 3D Quorum (8083), 78685 + 78818 → Canon Aquilion ONE AiCE (8085). The seed-name linker missed these because vendor_name was blank — the WS4 fix to expand the scan to expected_benefits and add word-boundary fix should help future passes catch them.
5. **Duplicate rows** in the 316: 78667/78817 both name CVI42; 78587/78836 both are Billie GPT; 78669/78802 both are Siemens Ysio Max; 78703/78825 both are TeraRecon; 78767/78801 both are Avicenna. Integrator should map duplicates to the same staged product_id.

## Catalog-engineering recommendations

- **Add umbrella products** for GE Healthcare, Philips, Siemens Healthineers, Canon Medical Systems, Brainlab, Medtronic, Hologic so the 50+ medical-imaging children can be parented (WS2's slice but worth flagging).
- **Add `medical_imaging` or `radiology_ai` as a product_type** distinct from `clinical_decision_support`. I tagged everything `clinical_decision_support` because it's the closest vocabulary, but a more specific bucket would aid dashboard faceting. (Not done here — out of slice.)
- **Title-only catalog rows** (~30 rows) needed me to lean on external product knowledge. Spot-check confidence flags before applying — most are medium-to-high, but Podimetrics, EarlySense WAVE, Rythm Express, Quantra are confidence=medium/low.

## Unclear flags worth human follow-up

- 78515 Pangaea — possibly Pangaea Data (UK clinical AI) but unconfirmed.
- 78668 VA CART Adenoma Detection (and the VA CART NLP family 78775/78776) — these are in-house VA NLP models, may not warrant separate catalog rows; could be consolidated into a "VA CART NLP Suite" product.
- 78706 Quantra — likely Hologic Quantra but title-only.
- 78854 Rythm Express — likely iRhythm Zio but title-only.

## Out of scope (left as `unclear`)

- All 11 consolidated rows are generic OMB taxonomy items with `agency_uses=N`. VA explicitly does NOT use these. No commercial product is named. All marked `unclear` with high-confidence reasoning that they should be human-skipped.
- ~195 of the 316 individual rows weren't included as decisions because they are clearly VA-internal models with no commercial product (titles like "Smart Claim Check", "Discharge Predictive Model", "Predict Septic Shock in ICU Patients") or too vague to triage. These remain dark; treat as not-actionable for this pass. If reviewer wants explicit `unclear` decisions for every row I can produce them, but that adds noise without information.
