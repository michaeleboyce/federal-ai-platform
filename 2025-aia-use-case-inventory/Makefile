.PHONY: check fix retag-scope fedramp dashboard all clean

check:
	pytest tests/ audit/checks/ -v

fix:
	python3 db.py
	python3 load_agencies.py
	python3 load_inventories.py
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
	# IFP product-category assignments from the curated audit proposal.
	# Runs AFTER cleanup so it can replace the cleanup step's NULL→
	# 'unclassified' backfill with concrete category labels (e.g.
	# physical_security, developer_tool, threat_intel). Idempotent.
	python3 scripts/apply_product_recategorization.py
	# Federal organizations hierarchy — schema, seed, backfill, sub-agency
	# maturity. Each script is idempotent.
	python3 scripts/run_migrations.py
	python3 scripts/seed_federal_hierarchy.py
	python3 scripts/backfill_bureau_orgs.py
	python3 compute_maturity.py
	python3 scripts/compute_org_maturity.py
	python3 scripts/generate_db_snapshot.py

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

dashboard:
	cd dashboard && npm run build

all: fix fedramp check dashboard

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
