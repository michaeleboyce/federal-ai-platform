"""Mirror the FedRAMP marketplace tables into the inventory DB.

Reads from `2025-fedramp/data/fedramp_marketplace.db` (read-only) and writes
mirrors into the inventory DB so the dashboard can query both datasets through
a single SQLite connection — no ATTACH, no second handle.

Five mirrored tables (verbatim mirrors of the source schema):
  - fedramp_products         (642 rows expected)
  - fedramp_authorizations   (3,320 rows expected)
  - fedramp_agencies         (91 rows)
  - fedramp_assessors        (33 rows)
  - fedramp_snapshot         (single row)

Idempotent: TRUNCATE + bulk INSERT each run. Source DB is never modified.

Usage:
    python load_fedramp.py            # apply
    python load_fedramp.py --dry-run  # report row counts; do not write
"""

import argparse
import sqlite3
from pathlib import Path

from db import get_connection

# Source FedRAMP marketplace DB lives in the sibling repo.
FEDRAMP_DB = (
    Path(__file__).parent.parent
    / "2025-fedramp"
    / "data"
    / "fedramp_marketplace.db"
)


# Mirror schema. Column types match the source (see
# 2025-fedramp/data/fedramp_marketplace.db .schema).
MIRROR_SCHEMA = """
CREATE TABLE IF NOT EXISTS fedramp_products (
    fedramp_id TEXT PRIMARY KEY,
    csp TEXT NOT NULL,
    csp_slug TEXT NOT NULL,
    cso TEXT NOT NULL,
    status TEXT NOT NULL,
    authorization_count INTEGER,
    reuse_count INTEGER,
    ready_date TEXT, ready_status TEXT,
    ip_jab_date TEXT, ip_jab_status TEXT,
    ip_prog_date TEXT, ip_prog_status TEXT,
    ip_prog_date2 TEXT,
    ip_agency_date TEXT, ip_agency_status TEXT,
    ip_pmo_date TEXT, ip_pmo_status TEXT,
    auth_date TEXT, auth_type TEXT,
    partnering_agency TEXT,
    annual_assessment_date TEXT,
    independent_assessor TEXT,
    assessor_id INTEGER,
    deployment_model TEXT,
    impact_level TEXT,
    impact_level_number INTEGER,
    service_desc TEXT,
    fedramp_msg TEXT,
    sales_email TEXT, security_email TEXT,
    website TEXT, uei TEXT,
    small_business INTEGER,
    logo TEXT,
    filter_classes TEXT, auth_category TEXT
);
CREATE INDEX IF NOT EXISTS idx_fp_csp ON fedramp_products(csp_slug);
CREATE INDEX IF NOT EXISTS idx_fp_status ON fedramp_products(status);
CREATE INDEX IF NOT EXISTS idx_fp_impact ON fedramp_products(impact_level);
CREATE INDEX IF NOT EXISTS idx_fp_assessor ON fedramp_products(assessor_id);

CREATE TABLE IF NOT EXISTS fedramp_authorizations (
    id INTEGER PRIMARY KEY,
    fedramp_id TEXT NOT NULL,
    agency_id INTEGER,
    sub_agency TEXT,
    ato_type TEXT,
    ato_issuance_date TEXT,
    fedramp_authorization_date TEXT,
    ato_expiration_date TEXT,
    annual_assessment_date TEXT
);
CREATE INDEX IF NOT EXISTS idx_fa_product ON fedramp_authorizations(fedramp_id);
CREATE INDEX IF NOT EXISTS idx_fa_agency  ON fedramp_authorizations(agency_id);
CREATE INDEX IF NOT EXISTS idx_fa_date    ON fedramp_authorizations(ato_issuance_date);

CREATE TABLE IF NOT EXISTS fedramp_agencies (
    id INTEGER PRIMARY KEY,
    parent_agency TEXT NOT NULL UNIQUE,
    parent_slug TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_fag_slug ON fedramp_agencies(parent_slug);

CREATE TABLE IF NOT EXISTS fedramp_assessors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_fas_slug ON fedramp_assessors(slug);

CREATE TABLE IF NOT EXISTS fedramp_snapshot (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    snapshot_date TEXT,
    product_count INTEGER,
    ato_event_count INTEGER,
    agency_count INTEGER,
    csp_count INTEGER,
    assessor_count INTEGER,
    built_at TEXT
);
"""


def _columns_for(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _copy_table(
    src: sqlite3.Connection,
    dst: sqlite3.Connection,
    src_table: str,
    dst_table: str,
    *,
    dry_run: bool,
) -> int:
    """Truncate `dst_table` and copy all rows from `src_table`.

    The destination column order is used as the source-of-truth — the source
    is queried by explicit column names so a column reorder upstream is safe.
    Returns the number of rows written (or that *would* be written in dry-run).
    """
    cols = _columns_for(dst, dst_table)
    select_cols = ", ".join(cols)
    placeholders = ", ".join(["?"] * len(cols))
    src_rows = src.execute(f"SELECT {select_cols} FROM {src_table}").fetchall()

    if dry_run:
        return len(src_rows)

    dst.execute(f"DELETE FROM {dst_table}")
    if src_rows:
        dst.executemany(
            f"INSERT INTO {dst_table} ({select_cols}) VALUES ({placeholders})",
            src_rows,
        )
    return len(src_rows)


def load_fedramp(*, dry_run: bool = False) -> None:
    if not FEDRAMP_DB.exists():
        raise SystemExit(f"FedRAMP marketplace DB not found at {FEDRAMP_DB}")

    src = sqlite3.connect(f"file:{FEDRAMP_DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    dst = get_connection()

    try:
        # Ensure mirror tables exist (idempotent).
        dst.executescript(MIRROR_SCHEMA)

        moves = [
            ("products", "fedramp_products"),
            ("authorizations", "fedramp_authorizations"),
            ("agencies", "fedramp_agencies"),
            ("assessors", "fedramp_assessors"),
            ("snapshot", "fedramp_snapshot"),
        ]
        counts: dict[str, int] = {}
        for src_t, dst_t in moves:
            n = _copy_table(src, dst, src_t, dst_t, dry_run=dry_run)
            counts[dst_t] = n

        if not dry_run:
            dst.commit()
            verb = "Loaded"
        else:
            verb = "Would load"
        for table, n in counts.items():
            print(f"  {verb} {n:,} rows -> {table}")
    finally:
        src.close()
        dst.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report row counts but do not write to the inventory DB.",
    )
    args = parser.parse_args()
    load_fedramp(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
