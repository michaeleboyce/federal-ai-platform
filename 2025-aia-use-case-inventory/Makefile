.PHONY: check fix dashboard all clean

check:
	pytest tests/ audit/checks/ -v

fix:
	python load_agencies.py
	python load_inventories.py
	python build_lookups.py
	python auto_tag.py
	python compute_maturity.py

dashboard:
	cd dashboard && npm run build

all: fix check dashboard

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
