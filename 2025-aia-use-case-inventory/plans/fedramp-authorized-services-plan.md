# Plan: FedRAMP authorized-services ingest + AI labeling — "the shelf inside the shelf"

**Status: Phases 1–4 complete (2026-07-04); ALL PHASES COMPLETE (1–4: 2026-07-04; 5–7: 2026-07-05). Fact sheet §7 + drop-in draft at audit/article/; §7 numbers machine-pinned by audit/checks/check_fedramp_fact_sheet.py.** Check boxes as phases complete; each phase ends with a
verification gate. Written 2026-07-03, revised 2026-07-04 (QC loop + surface
map); numbers reflect the 2026-06-12 snapshot.

## Why

FedRAMP's raw marketplace JSON lists the **services in scope** for 90 of 659
products (1,918 rows, 1,591 unique service names) — including Amazon Bedrock
and SageMaker inside the AWS packages, Azure OpenAI inside Azure Commercial,
and Gemini Enterprise / Vertex AI inside Google Services. Our ingest missed
all of it: `build_db.py` reads the `authorized_services` field (empty for
every product) instead of `all_others` + `service_last_90`, so
`product_authorized_services` has 0 rows and the dashboard can't see the
service level at all.

Goal: ingest the service rows, label each unique service name
(core_ai / ai_featured / not_ai) with cheap parallel Sonnet subagents, QC the
labels with a frontier-model judge (with a correction loop for systematic
errors), integrate as a sidecar table, and roll the result across the
dashboard's surfaces in two waves — each tied to a specific beat of the
article narrative (see the map below).

## How this feeds the article — narrative map

The article's FedRAMP argument has three beats plus a payoff. Each dashboard
surface below exists to make one beat citable:

| Beat | Claim | Surface that carries it |
|---|---|---|
| 1. The shelf is stocked, nothing moves | 26/35 authorized core-AI products never spread past one ATO; 10/48 ATO'd pairs corroborated | `/fedramp/coverage/spread` §I–II (live) |
| 2. The 20x zeros | ChatGPT/Gemini/Perplexity: program authorization, zero recorded agency reuse | `/fedramp/coverage/spread` §III (live) |
| 3. Adoption routed around the ledger | OneGov + USAi + **services inside packages** — the third channel, currently the only unquantified one | spread §IV rewrite + new "shelf inside the shelf" section (Wave A) |
| 4. **Payoff: the gap is agency-internal** | Laggard agencies (DOJ ~1%, HUD ~0.15%, SBA ~0 coverage) already hold ATOs on packages with Bedrock / Azure OpenAI in scope — frontier capability was legally in reach at the very agencies where employees have nothing | per-agency join (Wave B) + fact-sheet numbers |

Beat 4 is the new capability this plan unlocks: it converts "authorized ≠
available to staff" from an inference into a per-agency, per-service lookup —
the strongest single artifact this data can hand the article.

## Ground rules (read before any phase)

- **Multi-agent safety** (per repo CLAUDE.md): `fedramp_id` (TEXT, FedRAMP's
  own ID) and service-name strings are stable keys — use ONLY these in CSVs
  and results files. Never emit or consume integer row ids.
- Back up `data/federal_ai_inventory_2025.db` before Phase 2's reload.
- Labeler agents own ONLY their assigned `results/batch_NN.json` file. No DB
  access, no shared files. Integration is a single-writer step in Phase 4.
- Every LLM label persists its `reasoning` and verbatim `signals`; every QC
  verdict and correction persists its own reasoning next to the original
  (never overwrite the first-pass label — append, with `source` tracking).
- After any DB rebuild: `cp data/federal_ai_inventory_2025.db dashboard/data/`
  + `shasum` parity check before any dashboard commit.

---

## Phase 1 — Upstream ingest fix (`2025-fedramp/`)

**Files:** `2025-fedramp/scripts/build_db.py`, `2025-fedramp/tests/`

- [x] In `build_db.py` (~L404), populate `pas_rows` from `all_others` and
  `service_last_90` instead of the always-empty `authorized_services`.
  Extend the table to carry provenance and recency:
  `product_authorized_services (fedramp_id TEXT, service TEXT, recency TEXT
  CHECK (recency IN ('last_90','older')))` (~L232 DDL).
- [x] Add a loud regression guard: if a snapshot yields 0 total service rows
  while >0 products have non-empty `all_others`, exit non-zero.
- [x] Rebuild: `cd 2025-fedramp && python3 scripts/build_db.py`.
- [x] Pytest: ≥1,900 rows; AWS US East/West package contains 'Amazon
  Bedrock'; Azure package contains 'Azure OpenAI'.

**Gate:** `SELECT COUNT(*), COUNT(DISTINCT service) FROM
product_authorized_services` ≈ 1918 / 1591; pytest green.

## Phase 2 — Mirror into the inventory DB (`2025-aia-use-case-inventory/`)

**Files:** `load_fedramp.py` (MIRROR_SCHEMA + `moves` list ~L193)

- [x] Add mirror table `fedramp_authorized_services` (same columns + indexes
  on `fedramp_id` and `service`); add the pair to `moves`.
- [x] Back up the inventory DB, then run **`make fedramp`** (standard chain:
  reload, re-apply product classification, re-link, promote queue).
- [x] `pytest tests/ -q` (52 tests); compare `fedramp_product_links` count
  before/after — must be unchanged.

**Gate:** mirror row count matches Phase 1; existing tests green.

## Phase 3 — Labeling fan-out + frontier-model QC + correction loop

**New files:** `scripts/classify_fedramp_services.py` (exporter),
`audit/fedramp_service_classification/{inputs,results,qc,corrections}/`

### 3a. Label (cheap, wide)

- [x] Exporter: dedupe the 1,591 service names; attach context (host
  packages, csp, a `service_desc` snippet from the host); write
  `inputs/batch_NN.json` at ~50/batch → **~32 batches**.
- [x] Spawn parallel labeler subagents — `model: "sonnet"` (Sonnet 5), low
  effort, ~8 concurrent. Each reads one input batch, writes ONLY its
  `results/batch_NN.json`:
  `{service, category, confidence, reasoning, signals: [verbatim cues]}`.
  Rubric v1: `core_ai` = the service itself is an AI/ML capability (Bedrock,
  SageMaker, Azure OpenAI, Comprehend, Vertex/Gemini, Dialogflow);
  `ai_featured` = ships material AI as a feature; unsure → `not_ai` + low
  confidence (precision over recall — the article cites these).

### 3b. QC with a smarter model (stratified, adversarial)

- [x] Judge agents on the **frontier model** (main-loop model / `model:
  "opus"` if delegated; judging is where the capability spend belongs):
  - **100% of `core_ai`** labels (these become article claims),
  - **25% random of `ai_featured`**, **10% random of `not_ai`**,
  - **100% of `confidence: low`** rows regardless of category.
- [x] Each judge verdict → `qc/batch_NN.json`: `{service, verdict:
  confirm|overturn, corrected_category?, error_tag?, reasoning}`. Judges are
  prompted to **refute**, not rubber-stamp, and to assign an `error_tag`
  from a shared taxonomy they may extend (e.g. `marketing-name-confusion`,
  `infra-with-ml-feature-overcall`, `security-analytics-undercall`,
  `search-vs-ai-ambiguity`).

### 3c. Correction loop (triggered, not unconditional)

- [x] Aggregate QC: per-batch error rate + per-tag counts across batches.
- [x] **Trigger conditions** for a correction round:
  - any batch with >10% overturns, or
  - any `error_tag` appearing ≥5 times across batches (a *systematic*
    mistake, i.e. rubric flaw rather than noise).
- [x] Correction round: amend the rubric with explicit counter-examples
  drawn from the overturned rows (rubric v2 written to
  `corrections/rubric_v2.md`); **relabel only the affected slice** — the
  overturned rows plus every unsampled row matching the systematic tag's
  pattern (e.g. all services whose names match the confused pattern), with
  fresh Sonnet agents on rubric v2; re-QC the relabeled slice at 100%.
- [x] Loop until: overturn rate <5% on the final QC pass AND no un-remediated
  systematic tag. Residual one-off disagreements adjudicated by the main
  loop, reasoning persisted, `source: adjudicated`.
- [x] Consolidate to `data/fedramp_service_classification.csv`, keyed by
  service name, with `source ∈ {llm, qc_confirmed, qc_corrected, adjudicated}`
  so the provenance of every label is auditable.

**Gate:** 1,591/1,591 labeled; every `core_ai` row is `qc_confirmed`,
`qc_corrected`, or `adjudicated` (none ships on a single unreviewed pass);
correction-loop exit criteria met; CSV + rubric versions committed.

## Phase 4 — Integrate labels into the DB (single writer)

**New file:** `scripts/apply_fedramp_service_classification.py`

- [x] Sidecar table `fedramp_ai_service_classification (service TEXT PRIMARY
  KEY, category, confidence, reasoning, signals, model, classified_at,
  source)` — wipe-and-reload from the CSV, idempotent, exits non-zero if the
  mirror contains service names missing from the CSV (top-up signal, same
  contract as the product-level apply).
- [x] Wire into the `fedramp:` Makefile target after the product-level apply.
- [x] Run; sync DB to `dashboard/data/`; `pytest tests/ -q`.

**Gate:** Bedrock / Azure OpenAI / Gemini Enterprise present as `core_ai`;
core_ai service count plausible (~40–80); join to
`fedramp_authorized_services` clean.

## Phase 5 — Dashboard Wave A: quantify channel #3 (narrative beat 3)

**Files:** `lib/db/fedramp/spread.ts` (+ types, index re-exports),
`app/fedramp/coverage/spread/page.tsx` + new
`_sections/services-table.tsx`, `lib/db/fedramp/coverage.ts` (hub),
`app/fedramp/coverage/page.tsx`, Vitest + fixture schema.

- [x] Helpers (guard on table existence; section hides when absent):
  `getAiServicesInScope()` (core_ai service × host package × count of
  inventory-mapped agencies holding the package ATO) and
  `getAiServiceShelfCounts()` (headline: distinct core-AI services in scope;
  distinct agencies holding ≥1 package containing ≥1 core-AI service).
- [x] **Spread page**: new section between §III (20x trio) and §IV — "The
  shelf inside the shelf": headline stats + table (service · host package ·
  impact level · agencies holding the package). Rewrite §IV's third-channel
  sentence to cite the now-live number instead of asserting the channel
  exists. Method footer notes raw-snapshot provenance + the three-definition
  distinction.
- [x] **Coverage hub**: extend the "Two ways to be AI" definition band to
  three ways (linkage / listing classification / **service scope**) — the
  distinction is load-bearing and the hub is where readers learn definitions.
  Add one stat card ("Core-AI services in scope inside authorized packages —
  N across M packages") linking to the spread section anchor.
- [x] Vitest for both helpers (fixture rows incl. a package with a core_ai
  service and an agency ATO).

**Gate:** tsc + vitest green; dev smoke; every displayed number cross-checked
against direct sqlite3; hub card ↔ spread section numbers agree.

## Phase 6 — Dashboard Wave B: per-agency + per-product depth (beat 4)

**Files:** `app/fedramp/marketplace/products/[id]/page.tsx`,
`app/fedramp/coverage/agencies/[abbr]/page.tsx` (+ its `_sections/`),
`lib/db/fedramp/` helpers.

- [x] **Marketplace product detail**: render the in-scope services list for
  the 90 products that have one, with core_ai/ai_featured chips (Bedrock
  visibly flagged inside the AWS listing). This is the verification surface
  a fact-checking reader lands on.
- [x] **Per-agency coverage drill** (`/fedramp/coverage/agencies/[abbr]`):
  additive section "Frontier-adjacent services in reach" — core-AI services
  inside packages THIS agency holds an ATO for, with issued dates. This is
  beat 4's per-agency lookup.
- [x] **The article's money query**, exposed as a small table on the same
  drill (and exported for the fact sheet): agencies ranked by
  (core-AI services in reach) × (IFP coverage estimate from
  `agency_ai_access_evidence`) — i.e. DOJ/HUD/SBA holding Bedrock-bearing
  packages against ~0–1% employee coverage. Label IFP estimates with the
  standard provenance chip; do NOT imply the agency enabled the service —
  copy must say "in scope of a package the agency holds," nothing stronger.
- [x] Nav discoverability: no new routes in Wave B (sections on existing
  pages), so no nav changes; hub + spread cross-link the agency drills.

**Gate:** tsc + vitest + dev smoke on 3 agency drills (DOJ, HUD, VA) and the
AWS + Azure product pages; copy review against the "in scope ≠ enabled"
guardrail.

## Phase 7 — Article artifacts + ship

- [x] Update `audit/article/fact_sheet.md`: new citable numbers (core-AI
  services in scope; N agencies holding Bedrock-bearing packages; the beat-4
  join for the laggard agencies) + correct the prior "FedRAMP can't see
  services" claim to "FedRAMP scopes to the service but tracks adoption only
  to the package."
- [x] ETL repo commit (build_db, load, classify/apply scripts, CSV, audit
  artifacts, rubric versions); dashboard commit after shasum parity; push;
  poll production; live-verify spread section, hub band, one product page,
  one agency drill.
- [x] Post-ship: add the beat-4 table to the article draft's FedRAMP section
  with footnotes to the live pages.

## Agent topology summary

| Stage | Who | Parallelism | Owns |
|---|---|---|---|
| Phases 1–2 foundation | main loop | serial | build_db.py, load_fedramp.py, DB |
| 3a labeling | Sonnet 5, low effort | ~8 concurrent, 32 batches | one results/batch_NN.json each |
| 3b QC judging | frontier model (Opus/main-loop tier) | parallel over QC batches | qc/batch_NN.json each |
| 3c correction | Sonnet 5 relabelers on rubric v2 + frontier re-QC | targeted slices only | corrections/* |
| Adjudication | main loop | serial | final CSV |
| Phases 4–7 integration | main loop, single writer | serial | apply script, DB, dashboard |

## Rollback

Every step is additive (new tables, sidecar classification, new sections).
Rollback = restore the Phase-2 DB backup, or drop
`fedramp_authorized_services` / `fedramp_ai_service_classification`; all
dashboard sections hide themselves when the tables are absent.
