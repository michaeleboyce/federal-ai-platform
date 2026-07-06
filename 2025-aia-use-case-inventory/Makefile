.PHONY: check fix retag-scope fedramp dashboard all clean

check:
	pytest tests/ audit/checks/ -v

fix:
	python3 db.py
	python3 load_agencies.py
	python3 load_inventories.py
	# Raw 2024 (M-24-10) AI use case inventory corpus — 2,133 use cases in
	# native 2024 shape into `use_cases_2024` (table created by migration
	# m009). Phase 1 of the 2024↔2025 comparison project. Idempotent.
	python3 load_2024.py
	# One-row SKIP_FILES exception (2026-07 supersession audit): DOL's
	# non-template Prism Ally addendum, absent from every loaded source.
	python3 scripts/backfill_dol_prism_ally.py
	# OMB consolidated individually-reported AI use case file — mirror rows,
	# match against DB, populate omb_match_audit. Schema-only DB additions
	# come from migrations/m004; this is the data load. Idempotent.
	python3 load_omb_consolidated.py
	# Ingest adjudicated omb_only rows (OMB has them, per-agency sweep
	# missed them) from the mirror into use_cases, keyed by row_hash.
	# Clean no-op until audit/omb_only_ingest/decisions.csv exists. MUST
	# run after load_omb_consolidated (reads the fresh mirror + audit) and
	# before normalize/build_lookups/auto_tag (ingested rows get
	# normalized, slugged, and tagged like loader rows).
	python3 scripts/ingest_omb_only_rows.py
	# Recompute the derived stage_normalized / ai_classification_normalized
	# / high_impact_normalized columns (m016 + m019) — the loader
	# wipe-and-reload clears them every rebuild. Runs AFTER the OMB-only
	# ingest so ingested rows are normalized too. Hard-fails if non-blank
	# values fail to bucket (>5% stage, >1% high-impact — a new free-text
	# variant in a source file).
	python3 scripts/normalize_use_case_fields.py
	# 2024↔2025 deterministic use-case matcher — links use_cases_2024 to
	# use_cases (exact name → fuzzy name → narrative similarity), strictly
	# per-agency, into the `use_case_year_links` table (created by migration
	# m011). Phase 3 of the 2024↔2025 comparison project. Idempotent
	# (wipe-and-reload, preserves first_seen). Also writes
	# audit/year_match_queue.csv — the suggested_rename review queue for
	# Phase 4. No dashboard surface until Phase 5.
	python3 match_year_over_year.py
	# Phase 4 of the 2024↔2025 comparison project. Overlays the committed
	# multi-agent adjudication decisions
	# (audit/year_match_review/integration/proposed_lineage.csv) onto the
	# matcher's freshly-rebuilt baseline: confirm/reject renames, split,
	# merge, recover missed matches; then asserts the ≥1 reconciliation
	# invariant and writes the retired cross-check flags. Idempotent; a
	# clean no-op until the Stage-2 agent pass produces decisions.
	python3 scripts/apply_year_match_review.py
	# Deterministic field-level drift over the 21 directly-comparable
	# column pairs for every 1:1 continued/renamed link — writes
	# use_case_year_links.drift_fields_json. Recoded-field drift is flagged
	# lossy. Idempotent.
	python3 compute_year_lineage_drift.py
	python3 scripts/backfill_use_case_id.py
	python3 build_lookups.py
	python3 auto_tag.py
	# Belt-and-suspenders: re-apply the narrow infer_llm_flag rule via the
	# authoritative retag script so that even if a future auto_tag change
	# re-broadens is_general_llm_access (see auto_tag.py §is_llm for the
	# Agent B design notes), the final DB state stays within the plan's
	# intent. See scripts/retag_llm.py.
	#
	# INVARIANT (2026-07): every correction script between here and the end
	# of `fix` MUST stay ordered after auto_tag.py. The rebuilt DB is gated
	# by absolute bands in audit/checks/check_llm_flags.py (general-LLM
	# distinct 559±50, total 789±50, agentic 66±10; 2026-07-06 baseline,
	# post completeness pass); a tripped band means a correction script
	# dropped out of this chain or auto_tag drifted.
	python3 scripts/retag_llm.py
	python3 scripts/apply_retag_audit.py
	python3 scripts/apply_round2_audit.py
	# 2026-06 capability reviews: per-row adjudication of the low-confidence
	# general-LLM flips (round 3) and the over-tagged 'agentic' rows. Signature
	# -keyed; survives id rotation. See audit/retag/{general_llm_round3,
	# agentic_review}/INSTRUCTIONS.md.
	python3 scripts/apply_capability_reviews.py
	# 2026-07 genai-flag adjudication: Sonnet-labeled verdicts for every row
	# where the keyword-derived is_generative_ai disagreed with the agency's
	# own ai_classification (687 rows, 3 cohorts — the "autonomous"/"chatbot"
	# keyword over-fires plus declared-GenAI under-tags). Signature-keyed;
	# skips with a warning until verdict batches land. MUST run before
	# apply_llm_flag_drift.py, which keeps the last word on the
	# llm_access=1 ⇒ genai=1 invariant. See audit/retag/genai_review_2026-07/.
	python3 scripts/apply_genai_review.py --apply
	# 2026-07 flag-drift adjudication: reconciles rows where
	# is_general_llm_access=1 but is_generative_ai=0 (a contradiction — a
	# general chat LLM is generative by definition). Signature-keyed via
	# uc_signature.Resolver; skips with a warning until verdict batches land.
	python3 scripts/apply_llm_flag_drift.py
	# 2026-07 labeled-depth rounds (m026 columns): coding_tool_type taxonomy
	# over the is_coding_tool filings, and integration_depth over the
	# pilot+deployed rows. Sonnet-labeled, Fable-audited (audit_overrides
	# take precedence), signature-keyed; each skips with a warning until its
	# verdict batches land. See audit/retag/{coding_taxonomy_2026-07,
	# integration_depth_2026-07}/.
	python3 scripts/apply_coding_taxonomy.py --apply
	python3 scripts/apply_integration_depth.py --apply
	# Persist the audits' sources + quotes onto the use cases themselves
	# (use_case_external_evidence) so findings stay traceable in the UI.
	python3 scripts/persist_capability_evidence.py
	# 2024-vs-2025 divergence queue resolutions (38 reviewed rows).
	python3 scripts/apply_divergence_resolutions.py
	python3 scripts/apply_expanded_product_catalog.py
	python3 scripts/populate_use_case_products.py
	python3 scripts/cleanup_products_taxonomy.py
	# Apply curated product attributions from the 3-agent product-gap
	# review (audit/product_gap_review/{noisy,llms,other}/recommendations.json).
	# Adds 22 use_case_products edges that the heuristic populate step
	# misses (mostly Azure OpenAI cases mis-attributed to OpenAI API in
	# narrative fields). Idempotent. Without this in the pipeline, the
	# manual links from commit 4bfbf5a get wiped on every rebuild.
	python3 scripts/apply_product_gap_review.py
	# Apply the 2026-05 generic-vendor-links retag (Microsoft/Google/Adobe/Amazon/
	# Splunk/etc placeholder edges → specific catalog products, or downgrade to
	# confidence='inferred' if the source named the vendor but not a product).
	# See audit/retag/generic_vendor_links/. Idempotent; safe to re-run.
	python3 scripts/apply_generic_vendor_retag.py
	# May 2026 4-agent linkage pass (audit/linkage_pass_2026-05/integration/).
	# Adds ~220 catalog rows, ~38 hierarchy edges, ~7 aliases, and ~220 hand-
	# curated use_case→product links from the multi-agent labeling pass.
	# All inputs are CSV-staged and resolved by canonical_name so this survives
	# the build_lookups.py re-key. Idempotent. See
	# audit/linkage_pass_2026-05/CHARTER.md for context.
	python3 scripts/apply_linkage_pass_2026_05.py --apply
	# Follow-up sprint (audit/linkage_pass_2026-05-followup/): VA medical-imaging
	# dark sweep (~108 new products), broader catalog hierarchy gaps (+54 edges
	# incl. AWS / Google / Microsoft / Thomson Reuters umbrella adds), and
	# alias coverage audit (12 bare-name aliases on parent products that were
	# under-aliased — Microsoft 365 had zero aliases before this pass). Same
	# CSV-staged apply pattern, parameterized via --pass-dir. Idempotent.
	python3 scripts/apply_linkage_pass_2026_05.py --pass-dir audit/linkage_pass_2026-05-followup --apply
	# IFP product-category assignments from the curated audit proposal.
	# Runs AFTER cleanup so it can replace the cleanup step's NULL→
	# 'unclassified' backfill with concrete category labels (e.g.
	# physical_security, developer_tool, threat_intel). Idempotent.
	python3 scripts/apply_product_recategorization.py
	# Split the conflated "OpenAI Codex" product into the deprecated 2021
	# model and the 2025 Codex CLI, and link OPM's consolidated "Codex"
	# COTS row to the CLI. The upstream linkage pass links OPM by a stale
	# row id so the link never lands; this resolves it by stable slug.
	# Runs AFTER both linkage passes and recategorization. Idempotent.
	python3 scripts/apply_codex_split.py
	# 2026-06 product-queue review: resolves the 626 compound/unmatched
	# vendor strings (audit/product_queue_review_2026-06/). Runs AFTER all
	# catalog/alias passes so its seed-guard sees the full alias table.
	python3 scripts/apply_product_queue_review.py
	# 2026-07 band-row product links: connects the ~71 banded consolidated
	# rows that had no canonical product link (seat model needs the tool
	# family). Resolves products by canonical_name, rows by slug; skips with
	# a warning until link batches land.
	python3 scripts/apply_band_product_links.py
	# Federal organizations hierarchy — schema, seed, backfill, sub-agency
	# maturity. Each script is idempotent.
	python3 scripts/run_migrations.py
	# Load the federal AI policy/strategy tracker (CSVs at
	# audit/research/ai_strategies/) into agency_ai_policy_{documents,
	# compliance} (tables created by migration m012). Idempotent
	# wipe-and-reload. Feeds the dashboard's /policy section.
	python3 scripts/load_ai_policy_tracker.py
	python3 scripts/seed_federal_hierarchy.py
	python3 scripts/backfill_bureau_orgs.py
	# Single maturity computation (m023 collapse): agency pass + sub-org
	# pass, both into org_ai_maturity; the agency_ai_maturity VIEW serves
	# legacy readers. (compute_maturity.py archived.)
	python3 scripts/compute_org_maturity.py
	# 2024↔2025 year-over-year aggregate rollup — populates the tidy
	# `year_comparison` table (created by migration m010). Phase 2 of the
	# 2024↔2025 comparison project. Reads use_cases_2024 + use_cases.
	# Idempotent (wipe-and-reload). No dashboard surface until Phase 5.
	python3 compute_year_comparison.py
	# (compute_org_maturity.py already ran above; the final re-derive after
	# all product-link passes happens near the end of the chain.)
	# NOTE (v1.2): compute_agency_readiness.py moved to the END of this
	# chain — it reads fedramp_product_links, which are only fully
	# recovered by the link_fedramp/promote/decisions block far below.
	# Researched public evidence of how widely agencies have deployed
	# general-purpose AI tools. Loads audit/research/ai_access/*.json into
	# agency_ai_access_evidence (table created by migration m008). Idempotent.
	python3 scripts/apply_ai_access_evidence.py
	# Resolve agency_id on every abbreviation-keyed table (m024). MUST run
	# after all the loads that rewrite those tables (load_inventories,
	# load_omb_consolidated, load_ai_policy_tracker, apply_ai_access_evidence
	# above). Fails the build on unresolvable abbreviations outside the
	# documented exception set.
	python3 scripts/backfill_agency_fks.py
	# Researched workforce denominators + FedScope occupational caps for the
	# seat model. Loads audit/research/agency_workforce/*.json into
	# agency_workforce_profile + agency_occupation_counts (m013/m017).
	# Wipe-and-reload: MUST run after seed_federal_hierarchy.py re-keys
	# federal_organizations, or every row it wrote last run is an orphan.
	python3 scripts/apply_agency_workforce.py
	# 2026-07 band population labels: WHO each license band counts
	# (employees/contractors/endpoints/public + population stratum), keyed
	# by durable slug into consolidated_band_labels (m017). The stratified
	# seat model on /experience reads these. Skips with a warning until
	# label batches land.
	python3 scripts/apply_band_labels.py
	# Linkage recovery: build_lookups.py wipes products and re-issues IDs each
	# run, which orphans (and SQLite drops) any prior fedramp_product_links and
	# parent_product_id edges. These scripts re-apply that state from the
	# canonical CSVs/decisions. All resolve products by canonical_name so they
	# survive the re-keying. Order matters: merge → rekey queue → hierarchy →
	# promote queue → hand-link CSV. Each is idempotent.
	python3 scripts/merge_duplicate_products.py --apply
	python3 scripts/rekey_fedramp_link_queue.py --apply
	# Re-seed the heuristic alias_match fedramp links. build_lookups.py's
	# products wipe drops them (they key on products.id) and nothing else in
	# this chain recreates them — without this step every full rebuild loses
	# ~18 authorized-listing links and the fact-sheet unlinked-split pins
	# drift (155/47 -> 170/48). Idempotent: clears only source='alias_match';
	# manual_csv and link_queue rows are never touched. Mirrors `make fedramp`.
	python3 link_fedramp.py --apply
	python3 scripts/apply_product_hierarchy_edges.py --apply
	python3 scripts/promote_resolved_link_queue.py --apply
	python3 scripts/apply_fedramp_link_decisions.py --apply
	# FINAL consistency pass: every product step above can move edges, so the
	# primary-product cache and the maturity snapshot are re-derived last
	# (check_refactor_quality asserts view-is-edge-derived + maturity==rollups;
	# refresh_primary_product_cache.py retired with the m025 column drop.)
	python3 scripts/compute_org_maturity.py
	# Edge-hygiene sweep: merge_duplicate_products + cleanup_products above
	# can delete products; verify no dangling edge rows survive before
	# snapshotting. (fix-reverse is a no-op since m025 dropped the scalar
	# product_id cache it used to clean — kept for muscle memory.)
	python3 scripts/relink_stale_use_case_products.py fix-reverse
	python3 scripts/relink_stale_use_case_products.py verify
	# IFP-facing Federal AI Readiness Scorecard (rubric v1.2) — 5-dimension
	# weighted rubric, per agency. Runs LAST among data passes so it sees
	# the fully-recovered fedramp_product_links and final product edges.
	# Writes agency_readiness + readiness_headline. Constants mirror
	# dashboard/lib/readiness/rubric.ts. Idempotent.
	python3 scripts/compute_agency_readiness.py
	python3 scripts/generate_db_snapshot.py
	# OMB-vs-IFP discrepancy report (audit/omb_consolidated_diff_2025.md).
	# Read by humans; complements the live /discrepancies dashboard page.
	python3 scripts/audit_omb_consolidated_diff.py

retag-scope:
	python3 scripts/retag_scope_architecture.py

# (populate/adjudicate-review-queue-scope targets removed 2026-07: the
# review_queue_scope table was dropped by m021; scripts live in
# scripts/archive/.)

# Mirror the FedRAMP marketplace into the inventory DB and seed cross-refs.
# Idempotent — safe to re-run after either DB changes.
fedramp:
	python3 load_fedramp.py
	# Re-apply the per-product AI classification (LLM pass persisted at
	# data/fedramp_ai_classification.csv) after the mirror reload. Idempotent
	# wipe-and-reload keyed by stable fedramp_id. Exits non-zero if a fresh
	# snapshot added products that are not yet classified — top up the CSV
	# via scripts/classify_fedramp_ai.py first.
	python3 scripts/apply_fedramp_ai_classification.py --apply
	# Same contract for the per-service AI labels (services-in-scope catalog,
	# persisted at data/fedramp_service_classification.csv). Exits non-zero if
	# a fresh snapshot added services not yet labeled — top up via
	# scripts/classify_fedramp_services.py.
	python3 scripts/apply_fedramp_service_classification.py --apply
	# Curated crosswalk: core-AI in-scope services -> inventory products
	# (data/fedramp_service_product_map.csv). String-keyed; survives make fix.
	# Backs the sleeping-services coverage board.
	python3 scripts/apply_fedramp_service_product_map.py --apply
	# Per-product capability labels (LLM pass persisted at
	# data/product_capability_labels.csv) for the sleeping-services
	# "nothing similar deployed" test. Keyed by canonical_name.
	python3 scripts/apply_product_capability_labels.py --apply
	python3 link_fedramp.py --apply
	# Promote resolved fedramp_link_queue decisions into fedramp_product_links.
	# Picks up rows that link_fedramp.py left as 'multi_candidate' or 'no_alias'
	# and were later marked status='resolved' with a parseable fedramp_id
	# (regex FR\d+/F1\d+ or accept_N candidate index). source='link_queue' so
	# the rows survive subsequent link_fedramp.py rebuilds (which only clear
	# source='alias_match').
	python3 scripts/promote_resolved_link_queue.py --apply

dashboard:
	cd dashboard && npm run build

all: fix fedramp check dashboard

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
