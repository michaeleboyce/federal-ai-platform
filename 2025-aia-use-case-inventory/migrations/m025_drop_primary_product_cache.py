"""Drop the legacy primary-product cache columns + the dead template FK.

Removes:
  - use_cases.product_id            (scalar cache of the primary product —
                                     superseded by the m020
                                     entry_primary_products view over the
                                     authoritative edge tables)
  - use_cases.template_id           (0 rows EVER populated; templates are a
                                     consolidated-entry-only concept)
  - consolidated_use_cases.product_id (same cache, consolidated side)

KEPT: consolidated_use_cases.template_id (legitimately populated 900/900
by auto_tag's template matching).

With these columns gone, the whole cache subsystem retires: auto_tag no
longer writes them, build_lookups no longer NULLs them,
scripts/refresh_primary_product_cache.py is deleted, and
check_refactor_quality's cache==edges assertion becomes moot (the view is
definitionally edge-derived).

Preconditions handled in-order (SQLite DROP COLUMN fails on indexed
columns AND revalidates EVERY view in the schema during ALTER — so any
view that references a dropped view/column must go first):
  1. drop the three covering indexes
  2. drop agency_rollups (references inventory_entries) then
     inventory_entries (references use_cases.template_id)
  3. drop the columns
  4. recreate both views (inventory_entries with NULL AS template_id in
     the use_case arm — same column shape, all consumers unaffected)

Dashboard cutover verified BEFORE this lands: zero readers of
uc.product_id / uc.template_id remain (slice E, 2026-07-06).

Idempotent; tolerant of minimal test fixtures. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "025_drop_primary_product_cache"

INVENTORY_ENTRIES_SQL = """
CREATE VIEW inventory_entries AS
SELECT
    'use_case' AS entry_kind,
    id AS entry_id,
    agency_id,
    organization_id,
    bureau_organization_id,
    NULL AS template_id,
    slug,
    use_case_name AS title,
    source_file,
    0 AS is_consolidated
FROM use_cases
UNION ALL
SELECT
    'consolidated' AS entry_kind,
    id AS entry_id,
    agency_id,
    organization_id,
    bureau_organization_id,
    template_id,
    slug,
    ai_use_case AS title,
    source_file,
    1 AS is_consolidated
FROM consolidated_use_cases;
"""

# Verbatim from m015 (the latest prior recreation).
AGENCY_ROLLUPS_SQL = """
CREATE VIEW agency_rollups AS
SELECT
    a.id AS agency_id,
    COUNT(DISTINCT CASE WHEN ie.entry_kind = 'use_case' THEN ie.entry_id END) AS total_use_cases,
    COUNT(DISTINCT CASE WHEN ie.entry_kind = 'consolidated' THEN ie.entry_id END) AS total_consolidated_entries,
    COUNT(DISTINCT epe.product_id) AS distinct_products_deployed,
    COUNT(epe.product_id) AS product_edge_count
FROM agencies a
LEFT JOIN inventory_entries ie ON ie.agency_id = a.id
LEFT JOIN entry_product_edges epe
  ON epe.agency_id = a.id
 AND epe.entry_kind = ie.entry_kind
 AND epe.entry_id = ie.entry_id
GROUP BY a.id;
"""


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        r[1] == column for r in conn.execute(f"PRAGMA table_info({table})")
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def apply(conn: sqlite3.Connection) -> None:
    drops = [
        ("use_cases", "product_id"),
        ("use_cases", "template_id"),
        ("consolidated_use_cases", "product_id"),
    ]
    pending = [
        (t, c)
        for t, c in drops
        if _table_exists(conn, t) and _column_exists(conn, t, c)
    ]
    if not pending:
        # Columns already gone — but a partially-failed prior run may have
        # left the views missing; restore them before declaring victory.
        if _table_exists(conn, "use_cases"):
            if conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='view' AND name='inventory_entries'"
            ).fetchone() is None:
                conn.executescript(INVENTORY_ENTRIES_SQL)
            if conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='view' AND name='agency_rollups'"
            ).fetchone() is None:
                conn.executescript(AGENCY_ROLLUPS_SQL)
        return

    for idx in (
        "idx_use_cases_product",
        "idx_use_cases_template",
        "idx_consolidated_product",
    ):
        conn.execute(f"DROP INDEX IF EXISTS {idx}")

    # Views are recreated UNCONDITIONALLY below: a partially-failed prior
    # run may have dropped them without dropping the columns, so their
    # absence must not skip recreation.
    conn.execute("DROP VIEW IF EXISTS agency_rollups")
    conn.execute("DROP VIEW IF EXISTS inventory_entries")

    for table, column in pending:
        conn.execute(f"ALTER TABLE {table} DROP COLUMN {column}")

    conn.executescript(INVENTORY_ENTRIES_SQL)
    conn.executescript(AGENCY_ROLLUPS_SQL)
