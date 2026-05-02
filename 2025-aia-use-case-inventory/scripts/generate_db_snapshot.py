"""Generate headline-count docs from the current SQLite snapshot."""
from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT = ROOT / "audit" / "db_snapshot.md"


def scalar(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def row(conn: sqlite3.Connection, sql: str):
    return conn.execute(sql).fetchone()


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        counts = {
            "tracked_agencies": scalar(conn, "SELECT COUNT(*) FROM agencies"),
            "loaded_agencies": scalar(conn, "SELECT COUNT(DISTINCT agency_id) FROM inventory_entries"),
            "individual_entries": scalar(conn, "SELECT COUNT(*) FROM use_cases"),
            "consolidated_entries": scalar(conn, "SELECT COUNT(*) FROM consolidated_use_cases"),
            "inventory_entries": scalar(conn, "SELECT COUNT(*) FROM inventory_entries"),
            "canonical_products": scalar(conn, "SELECT COUNT(*) FROM products"),
            "commercial_products": scalar(
                conn,
                "SELECT COUNT(*) FROM products WHERE product_origin = 'commercial'",
            ),
            "agency_internal_products": scalar(
                conn,
                "SELECT COUNT(*) FROM products WHERE product_origin = 'agency_internal_platform'",
            ),
            "product_edges": scalar(conn, "SELECT COUNT(*) FROM entry_product_edges"),
            "linked_entries": scalar(
                conn,
                "SELECT COUNT(*) FROM (SELECT DISTINCT entry_kind, entry_id FROM entry_product_edges)",
            ),
            "distinct_linked_products": scalar(
                conn,
                "SELECT COUNT(DISTINCT product_id) FROM entry_product_edges",
            ),
            "pending_product_reviews": scalar(
                conn,
                "SELECT COUNT(*) FROM review_queue_products WHERE COALESCE(llm_reviewed, 0) = 0",
            ),
            "templates": scalar(conn, "SELECT COUNT(*) FROM use_case_templates"),
            "maturity_rows": scalar(conn, "SELECT COUNT(*) FROM agency_ai_maturity"),
        }
        top_product = row(
            conn,
            """
            SELECT p.canonical_name, COUNT(DISTINCT epe.agency_id) AS agency_count
              FROM products p
              JOIN entry_product_edges epe ON epe.product_id = p.id
             GROUP BY p.id
             ORDER BY agency_count DESC, p.canonical_name COLLATE NOCASE ASC
             LIMIT 1
            """,
        )
    finally:
        conn.close()

    lines = [
        "# Database Snapshot",
        "",
        "Generated from `data/federal_ai_inventory_2025.db`.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}: {value}")
    if top_product is not None:
        lines.extend(
            [
                "",
                "## Top Product",
                "",
                f"- canonical_name: {top_product['canonical_name']}",
                f"- agency_count: {top_product['agency_count']}",
            ]
        )
    lines.append("")

    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
