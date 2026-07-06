"""Create the `entry_primary_products` view.

One row per inventory entry (either kind) naming its PRIMARY product,
derived from the authoritative edge tables with the exact ordering that
`scripts/refresh_primary_product_cache.py` uses to maintain the legacy
scalar cache columns (`use_cases.product_id`,
`consolidated_use_cases.product_id`): strong edges before inferred, then
lowest product_id.

This view is the dashboard's cutover target so the scalar cache columns —
and the refresh subsystem behind them — can be dropped in a later
migration without changing which product name any page shows. Until that
drop lands, the view and the cache are intentionally redundant and a
check asserts they agree (audit/checks/check_refactor_quality.py).

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "020_entry_primary_products_view"

VIEW_SQL = """
DROP VIEW IF EXISTS entry_primary_products;
CREATE VIEW entry_primary_products AS
SELECT entry_kind, entry_id, product_id, product_name FROM (
    SELECT
        'use_case' AS entry_kind,
        ucp.use_case_id AS entry_id,
        ucp.product_id,
        p.canonical_name AS product_name,
        ROW_NUMBER() OVER (
            PARTITION BY ucp.use_case_id
            ORDER BY CASE ucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                     ucp.product_id
        ) AS rn
    FROM use_case_products ucp
    JOIN products p ON p.id = ucp.product_id
) WHERE rn = 1
UNION ALL
SELECT entry_kind, entry_id, product_id, product_name FROM (
    SELECT
        'consolidated' AS entry_kind,
        cucp.consolidated_use_case_id AS entry_id,
        cucp.product_id,
        p.canonical_name AS product_name,
        ROW_NUMBER() OVER (
            PARTITION BY cucp.consolidated_use_case_id
            ORDER BY CASE cucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
                     cucp.product_id
        ) AS rn
    FROM consolidated_use_case_products cucp
    JOIN products p ON p.id = cucp.product_id
) WHERE rn = 1;
"""


def apply(conn: sqlite3.Connection) -> None:
    conn.executescript(VIEW_SQL)
