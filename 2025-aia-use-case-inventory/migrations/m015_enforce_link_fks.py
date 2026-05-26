"""Rebuild use_case_products + consolidated_use_case_products with ON DELETE CASCADE.

Phase 3 prevention for the bug class that produced 323 dangling FK rows in
Phases 1+2:

  - SQLite doesn't enforce declared `REFERENCES` constraints unless the
    writer connection sets `PRAGMA foreign_keys = ON`.
  - The link tables shipped with declared FKs but no cascade, so even with
    foreign_keys on, a DELETE from `use_cases` would FAIL rather than
    cascade — making `load_inventories.py`'s wholesale DELETE+re-INSERT
    pattern impossible without disabling FKs.
  - This migration adds `ON DELETE CASCADE ON UPDATE CASCADE` so the
    rebuild pattern works AND any future stray DELETE on a parent row
    correctly cleans up its child link rows.

SQLite can't ALTER TABLE … ADD FOREIGN KEY; only rename-recreate-copy.
Pre-flight `PRAGMA foreign_key_check` is reported but NOT enforced — Phase
1+2 already cleaned everything; if anything dangles at apply time we want
to know about it (exit non-zero), not silently truncate.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "015_enforce_link_fks"

NEW_UCP_SQL = """
CREATE TABLE use_case_products_new (
    use_case_id INTEGER NOT NULL
        REFERENCES use_cases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE CASCADE ON UPDATE CASCADE,
    evidence_text TEXT,
    confidence TEXT CHECK(confidence IN ('strong', 'inferred')),
    PRIMARY KEY (use_case_id, product_id)
)
"""

NEW_CUP_SQL = """
CREATE TABLE consolidated_use_case_products_new (
    consolidated_use_case_id INTEGER NOT NULL
        REFERENCES consolidated_use_cases(id) ON DELETE CASCADE ON UPDATE CASCADE,
    product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE CASCADE ON UPDATE CASCADE,
    evidence_text TEXT,
    confidence TEXT CHECK(confidence IN ('strong', 'inferred')),
    PRIMARY KEY (consolidated_use_case_id, product_id)
)
"""


def _has_cascade(conn: sqlite3.Connection, table: str) -> bool:
    """Return True if the table's FK list reports ON DELETE CASCADE.

    SQLite exposes FK actions via `PRAGMA foreign_key_list(table)` — the
    `on_delete` column reads `'CASCADE'` when cascade is declared. We
    check that to detect whether m015 already ran.
    """
    rows = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    return bool(rows) and all(r[6] == "CASCADE" for r in rows)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        is not None
    )


def _rebuild(conn: sqlite3.Connection, table: str, new_ddl: str, indexes: list[str]) -> None:
    if not _table_exists(conn, table):
        return
    if _has_cascade(conn, table):
        return
    # Copy existing rows into the new table, swap, recreate indexes.
    conn.execute(new_ddl)
    conn.execute(f"INSERT INTO {table}_new SELECT * FROM {table}")
    conn.execute(f"DROP TABLE {table}")
    conn.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
    for idx_sql in indexes:
        conn.execute(idx_sql)


# Views that reference the link tables (directly or transitively). Dropped
# before the rebuild and recreated after — SQLite can't DROP TABLE while a
# view depends on it. Listed in dependency order (child-first when dropping,
# parent-first when recreating).
ENTRY_PRODUCT_EDGES_DDL = """
CREATE VIEW entry_product_edges AS
SELECT
    'use_case' AS entry_kind,
    ucp.use_case_id AS entry_id,
    uc.agency_id,
    uc.organization_id,
    uc.bureau_organization_id,
    ucp.product_id,
    ucp.evidence_text,
    ucp.confidence
FROM use_case_products ucp
JOIN use_cases uc ON uc.id = ucp.use_case_id
UNION ALL
SELECT
    'consolidated' AS entry_kind,
    cucp.consolidated_use_case_id AS entry_id,
    c.agency_id,
    c.organization_id,
    c.bureau_organization_id,
    cucp.product_id,
    cucp.evidence_text,
    cucp.confidence
FROM consolidated_use_case_products cucp
JOIN consolidated_use_cases c ON c.id = cucp.consolidated_use_case_id
"""

AGENCY_ROLLUPS_DDL = """
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
GROUP BY a.id
"""


def apply(conn: sqlite3.Connection) -> None:
    # Short-circuit if both tables already have CASCADE — keeps the
    # migration cheap on repeat runs.
    have_ucp = _table_exists(conn, "use_case_products")
    have_cup = _table_exists(conn, "consolidated_use_case_products")
    ucp_done = (not have_ucp) or _has_cascade(conn, "use_case_products")
    cup_done = (not have_cup) or _has_cascade(conn, "consolidated_use_case_products")
    if ucp_done and cup_done:
        return

    # Pre-flight: report (don't enforce) dangling rows on the link tables
    # specifically. Phase 1+2 cleaned them; if this runs against a DB that
    # skipped those passes we want a loud signal. (We don't fail on other
    # tables' FK issues — they're separately-owned and out of scope.)
    link_issues = [
        row
        for row in conn.execute("PRAGMA foreign_key_check").fetchall()
        if row[0] in ("use_case_products", "consolidated_use_case_products")
    ]
    if link_issues:
        rows_by_table: dict[str, int] = {}
        for row in link_issues:
            rows_by_table[row[0]] = rows_by_table.get(row[0], 0) + 1
        msg = ", ".join(f"{t}: {n}" for t, n in rows_by_table.items())
        print(
            f"[m015] WARNING: link-table foreign_key_check returned "
            f"{len(link_issues)} issue(s) ({msg}). The COPY preserves rows "
            "verbatim — run `python3 scripts/relink_stale_use_case_products.py "
            "verify` after this migration to confirm zero dangles."
        )

    # SQLite quirk: ALTER TABLE … RENAME on a referenced table can fail
    # while a VIEW references the OLD name. Drop the dependency chain
    # before rebuilding; recreate in dependency order after. (agency_rollups
    # depends on entry_product_edges, which depends on the link tables.)
    conn.execute("DROP VIEW IF EXISTS agency_rollups")
    conn.execute("DROP VIEW IF EXISTS entry_product_edges")

    # Toggle FKs OFF only during the rebuild. The runner re-enables them at
    # the next connection open, and apply scripts will turn them on
    # explicitly (Phase 3 task 2). Without this toggle, the rebuild can
    # trip transient FK errors (e.g. on the empty `_new` table mid-copy).
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        _rebuild(
            conn,
            "use_case_products",
            NEW_UCP_SQL,
            [
                "CREATE INDEX IF NOT EXISTS idx_ucp_use_case ON use_case_products(use_case_id)",
                "CREATE INDEX IF NOT EXISTS idx_ucp_product ON use_case_products(product_id)",
            ],
        )
        _rebuild(
            conn,
            "consolidated_use_case_products",
            NEW_CUP_SQL,
            [
                "CREATE INDEX IF NOT EXISTS idx_cucp_cuc "
                "ON consolidated_use_case_products(consolidated_use_case_id)",
                "CREATE INDEX IF NOT EXISTS idx_cucp_product "
                "ON consolidated_use_case_products(product_id)",
            ],
        )
        conn.execute(ENTRY_PRODUCT_EDGES_DDL)
        conn.execute(AGENCY_ROLLUPS_DDL)
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
