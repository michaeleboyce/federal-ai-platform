.PHONY: check fix retag-scope dashboard all clean

check:
	pytest tests/ audit/checks/ -v

fix:
	python load_agencies.py
	python load_inventories.py
	python build_lookups.py
	python auto_tag.py
	# Belt-and-suspenders: re-apply the narrow infer_llm_flag rule via the
	# authoritative retag script so that even if a future auto_tag change
	# re-broadens is_general_llm_access (see auto_tag.py §is_llm for the
	# Agent B design notes), the final DB state stays within the plan's
	# intent. See scripts/retag_llm.py.
	python scripts/retag_llm.py
	python compute_maturity.py

retag-scope:
	python scripts/retag_scope_architecture.py

populate-review-queue-scope:
	python scripts/populate_review_queue_scope.py

adjudicate-review-queue-scope:
	python scripts/review_queue_scope_adjudicate.py

dashboard:
	cd dashboard && npm run build

all: fix check dashboard

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
