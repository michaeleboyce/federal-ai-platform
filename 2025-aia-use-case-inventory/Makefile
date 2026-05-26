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
	# OMB consolidated individually-reported AI use case file — mirror rows,
	# match against DB, populate omb_match_audit. Schema-only DB additions
	# come from migrations/m004; this is the data load. Idempotent.
	python3 load_omb_consolidated.py
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
	python3 scripts/retag_llm.py
	python3 scripts/apply_retag_audit.py
	python3 scripts/apply_round2_audit.py
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
	python3 compute_maturity.py
	# 2024↔2025 year-over-year aggregate rollup — populates the tidy
	# `year_comparison` table (created by migration m010). Phase 2 of the
	# 2024↔2025 comparison project. Reads use_cases_2024 + use_cases.
	# Idempotent (wipe-and-reload). No dashboard surface until Phase 5.
	python3 compute_year_comparison.py
	python3 scripts/compute_org_maturity.py
	# IFP-facing Federal AI Readiness Scorecard — 5-dimension weighted
	# rubric, per agency. Reads agency_ai_maturity + use_cases + tags +
	# fedramp_product_links; writes agency_readiness. Constants mirror
	# dashboard/lib/readiness-rubric.ts. Idempotent.
	python3 scripts/compute_agency_readiness.py
	# Researched public evidence of how widely agencies have deployed
	# general-purpose AI tools. Loads audit/research/ai_access/*.json into
	# agency_ai_access_evidence (table created by migration m008). Idempotent.
	python3 scripts/apply_ai_access_evidence.py
	# Linkage recovery: build_lookups.py wipes products and re-issues IDs each
	# run, which orphans (and SQLite drops) any prior fedramp_product_links and
	# parent_product_id edges. These scripts re-apply that state from the
	# canonical CSVs/decisions. All resolve products by canonical_name so they
	# survive the re-keying. Order matters: merge → rekey queue → hierarchy →
	# promote queue → hand-link CSV. Each is idempotent.
	python3 scripts/merge_duplicate_products.py --apply
	python3 scripts/rekey_fedramp_link_queue.py --apply
	python3 scripts/apply_product_hierarchy_edges.py --apply
	python3 scripts/promote_resolved_link_queue.py --apply
	python3 scripts/apply_fedramp_link_decisions.py --apply
	# auto_tag.py (line 41) sets use_cases.product_id pointing at whatever the
	# tagger matched. Downstream merge_duplicate_products + cleanup_products
	# may then delete those products, leaving stale refs. Clean any reverse-
	# dangle and re-verify before snapshotting. SQLite doesn't enforce FKs
	# without PRAGMA foreign_keys=ON, so this swept-up step prevents the bug
	# class from re-introducing itself on every full rebuild. (Phase 3 will
	# replace this with proper FK enforcement.)
	python3 scripts/relink_stale_use_case_products.py fix-reverse
	python3 scripts/relink_stale_use_case_products.py verify
	python3 scripts/generate_db_snapshot.py
	# OMB-vs-IFP discrepancy report (audit/omb_consolidated_diff_2025.md).
	# Read by humans; complements the live /discrepancies dashboard page.
	python3 scripts/audit_omb_consolidated_diff.py

retag-scope:
	python3 scripts/retag_scope_architecture.py

populate-review-queue-scope:
	python3 scripts/populate_review_queue_scope.py

adjudicate-review-queue-scope:
	python3 scripts/review_queue_scope_adjudicate.py

# Mirror the FedRAMP marketplace into the inventory DB and seed cross-refs.
# Idempotent — safe to re-run after either DB changes.
fedramp:
	python3 load_fedramp.py
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
