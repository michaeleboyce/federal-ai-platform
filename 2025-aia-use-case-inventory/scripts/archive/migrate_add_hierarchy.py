"""Add the federal_organizations hierarchy table and related FK columns.

DDL only — does not seed or backfill. Idempotent: safe to re-run.
Pairs with scripts/seed_federal_hierarchy.py and scripts/backfill_bureau_orgs.py.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

DDL = """
CREATE TABLE IF NOT EXISTS federal_organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT,
    abbreviation TEXT,
    slug TEXT NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES federal_organizations(id),
    level TEXT NOT NULL
        CHECK (level IN ('department','independent','sub_agency','office','component')),
    hierarchy_path TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    sam_org_id TEXT,
    cgac_code TEXT,
    agency_code TEXT,
    is_cfo_act_agency INTEGER NOT NULL DEFAULT 0,
    is_cabinet_department INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    description TEXT,
    website TEXT,
    legacy_agency_id INTEGER REFERENCES agencies(id),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fed_org_parent ON federal_organizations(parent_id);
CREATE INDEX IF NOT EXISTS idx_fed_org_level ON federal_organizations(level);
CREATE INDEX IF NOT EXISTS idx_fed_org_abbreviation ON federal_organizations(abbreviation);
CREATE INDEX IF NOT EXISTS idx_fed_org_hierarchy_path ON federal_organizations(hierarchy_path);
CREATE INDEX IF NOT EXISTS idx_fed_org_cfo_act ON federal_organizations(is_cfo_act_agency);
CREATE INDEX IF NOT EXISTS idx_fed_org_legacy ON federal_organizations(legacy_agency_id);

-- Sub-agency maturity rows live in their own table to avoid the
-- agency_ai_maturity.agency_id NOT NULL UNIQUE constraint. Same column shape
-- as agency_ai_maturity (minus the agency_id) for convenient reuse.
CREATE TABLE IF NOT EXISTS org_ai_maturity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL UNIQUE REFERENCES federal_organizations(id),
    total_use_cases INTEGER,
    distinct_products_deployed INTEGER,
    generative_ai_count INTEGER,
    coding_tool_count INTEGER,
    general_llm_count INTEGER,
    classical_ml_count INTEGER,
    agentic_ai_count INTEGER,
    custom_system_count INTEGER,
    has_enterprise_llm INTEGER,
    has_coding_assistants INTEGER,
    has_agentic_ai INTEGER,
    has_custom_ai INTEGER,
    pct_deployed REAL,
    pct_high_impact REAL,
    pct_with_risk_docs REAL,
    maturity_tier TEXT,
    notes TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_org_maturity_tier ON org_ai_maturity(maturity_tier);
"""

# Columns we conditionally add to existing tables — guarded by introspection
EXTENSIONS = [
    ("use_cases", "organization_id", "INTEGER REFERENCES federal_organizations(id)"),
    ("use_cases", "bureau_organization_id", "INTEGER REFERENCES federal_organizations(id)"),
    ("consolidated_use_cases", "organization_id", "INTEGER REFERENCES federal_organizations(id)"),
    ("consolidated_use_cases", "bureau_organization_id", "INTEGER REFERENCES federal_organizations(id)"),
    ("agency_ai_maturity", "organization_id", "INTEGER REFERENCES federal_organizations(id)"),
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_use_cases_org ON use_cases(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_use_cases_bureau_org ON use_cases(bureau_organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_consolidated_org ON consolidated_use_cases(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_consolidated_bureau_org ON consolidated_use_cases(bureau_organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_maturity_org ON agency_ai_maturity(organization_id)",
]


def existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            conn.executescript(DDL)
            stats = {"added_columns": 0, "skipped_existing": 0}
            for table, col, type_decl in EXTENSIONS:
                cols = existing_columns(conn, table)
                if col in cols:
                    stats["skipped_existing"] += 1
                    continue
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {type_decl}")
                stats["added_columns"] += 1
            for stmt in INDEXES:
                conn.execute(stmt)
        print(f"[migrate] {stats}")
        # Sanity check
        n = conn.execute(
            "SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' AND name='federal_organizations'"
        ).fetchone()["n"]
        print(f"[migrate] federal_organizations table present: {bool(n)}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
