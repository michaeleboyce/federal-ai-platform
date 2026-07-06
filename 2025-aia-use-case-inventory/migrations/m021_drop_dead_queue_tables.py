"""Drop four empty, superseded workflow tables.

- review_queue_entry_type / review_queue_llm / review_queue_scope: one-shot
  review-queue scaffolding from the 2026-04/05 retag rounds. All decisions
  were applied long ago (see scripts/archive/ and audit/retag/); the tables
  have been wiped by every `make fix` since (load_inventories.py cleared
  them) and hold 0 rows. review_queue_products (626 rows, fully
  adjudicated) is KEPT — it documents the product-queue decisions.
- fedramp_link_evidence: created alongside fedramp_product_links but never
  written to (0 rows); link evidence ended up living on the link rows and
  in audit/ artifacts instead.

The scripts that populated/consumed these queues are moved to
scripts/archive/ in the same commit; none of them run in `make fix`.

On a fresh DB the creating migrations still run first and this one drops
the tables afterwards — harmless. Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "021_drop_dead_queue_tables"

DEAD_TABLES = (
    "review_queue_entry_type",
    "review_queue_llm",
    "review_queue_scope",
    "fedramp_link_evidence",
)


def apply(conn: sqlite3.Connection) -> None:
    for table in DEAD_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
