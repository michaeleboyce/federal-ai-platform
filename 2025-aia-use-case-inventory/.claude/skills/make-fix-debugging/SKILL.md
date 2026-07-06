---
name: make-fix-debugging
description: Use when `make fix` fails, hangs, or produces a suspicious DB — the operational runbook for the ~58-script rebuild chain. Covers the exit-code-masking trap (never pipe make through grep/tail), mid-chain-death forensics (the wipe-order table and the symptom→cause map, e.g. "LLM counts = 0" means the chain died before corrections re-applied), the decoy 0-byte DB files, backup-* snapshot conventions, the double-run idempotency test, and how to get re-oriented after a failure. Triggered by: a non-zero `make fix`, a tripped band in `audit/checks/`, counts that look wiped or wildly off, or a sqlite query returning "impossible" results mid-investigation.
---

# make fix — Debugging Runbook

`make fix` is a linear chain of ~58 python scripts with documented ordering
invariants. When it breaks, the DB is usually left MID-CHAIN — later-derived
tables wiped or stale — and naive investigation of that half-built DB
produces false conclusions. This runbook is the sequence that avoids the
known traps (each one cost a real debugging cycle at least once).

## Rule 1: capture output; NEVER pipe make through a filter

```bash
# WRONG — the pipeline's exit code is grep's, not make's; a mid-chain
# death looks like success and you'll "verify" a half-built DB:
make fix 2>&1 | grep -E "error|counts"          # DON'T

# RIGHT:
make fix > /tmp/fix.log 2>&1; echo "exit: $?"
grep -nB3 -A10 "Traceback\|FATAL\|Error 1" /tmp/fix.log | tail -30
```

The chain is fail-fast by design (loader gates, normalize guards, apply-
script thresholds, reconciliation asserts) — a failure is ALWAYS visible in
the exit code and log tail. Trust exit codes, not the presence of familiar
output lines.

## Rule 2: know what a mid-chain death leaves behind

`load_inventories.py` DELETEs early (FK order): external evidence,
review_queue_products, product edges (both), `use_case_tags`,
`org_ai_maturity`, column_mappings, omb mirror + audit, year links, then
`use_cases` + `consolidated_use_cases`, and reloads only the last two plus
mappings. EVERYTHING ELSE is rebuilt by later steps — so a death anywhere
in the middle leaves tags/edges/maturity empty or stale.

Symptom → likely cause:

| Symptom in the half-built DB | Meaning |
|---|---|
| `SUM(is_general_llm_access) = 0`, "StateChat row missing" (tag-JOIN tests) | Chain died before/at `auto_tag.py` — tags were wiped and never rebuilt |
| LLM/agentic band tripped but nonzero | A correction script dropped out of the chain after auto_tag, or auto_tag drifted (bands: `audit/checks/check_llm_flags.py`; ±50/±10 exists because auto_tag has ~2-row rebuild jitter) |
| `no such column: product_id`/`template_id` | A script (often resurrected from `scripts/archive/`) still reads the m025-dropped scalars — route through `entry_primary_products` |
| `1:1 uniqueness failed` in year-lineage reconciliation | New/renamed 2025 rows collided with stale committed lineage decisions — see the recovered-twin precedence guards in `scripts/apply_year_match_review.py` |
| "Refusing to apply" + `apply_drops.csv` | >2% of an adjudication round's keys no longer resolve — source data changed; re-adjudicate (see `adjudication-rounds` skill) |
| `error in view X: no such table Y` during a migration | SQLite ALTER revalidates EVERY view — drop dependent views first (m025 is the template) |

Recovery is always the same: fix the cause, run the FULL `make fix` again
(never resume mid-chain), then `python3 -m pytest tests/ audit/checks/ -q`.

## Rule 3: query the right DB

The real DB is **`data/federal_ai_inventory_2025.db`** — always. Historical
0-byte decoys at the repo root (`federal_ai_inventory_2025.db`,
`ai_inventory.db`) have fooled agents into "the tables are missing"
conclusions. The dashboard's copy at `dashboard/data/` must be
shasum-identical after a sync; if they differ mid-investigation, a rebuild
happened after the last sync (or the dashboard's `prebuild` hook auto-copied
a fresh build — it does that whenever `../data/...db` exists).

Also: a `next dev` server holds an OLD sqlite handle across `cp` — restart
it after any DB replacement or you'll chase phantom 500s/corrupt reads.

## Rule 4: ids rotate; snapshots and backups orient you

- Two consecutive `make fix` runs must produce IDENTICAL counts
  (use_cases/consolidated/tags/omb_only) — the standing idempotency test.
  Baseline as of 2026-07-06: 3660 / 901 / 4561 / 0.
- `data/federal_ai_inventory_2025.db.backup-<purpose>-<timestamp>` files are
  pre-change snapshots taken by risky passes; compare against them by
  SIGNATURE (slug/canonical_name), never by id.
- A fresh `backup-*` you didn't create, or `select max(id) from products`
  jumping by hundreds = a sibling agent rebuilt while you worked — refresh
  every id you hold (repo CLAUDE.md hard rules).
- `audit/db_snapshot.md` (regenerated every rebuild by
  `scripts/generate_db_snapshot.py`) is the fastest re-orientation read.

## Rule 5: background the rebuild, don't poll it

The chain takes minutes. Run it as a background task writing to a log file
and act on the completion event; while it runs, do NOT edit any script in
the chain (each step launches `python3` fresh — your edit executes mid-run
and corrupts the run), and do NOT trust sqlite reads of derived tables.

## Cross-references

- Structure/invariants/migration rules: `inventory-db-model`.
- Round mechanics + apply-script contract: `adjudication-rounds`.
- Post-rebuild publication steps (fact sheet, pinned copy, sync, smoke):
  `publish-and-repin`.
