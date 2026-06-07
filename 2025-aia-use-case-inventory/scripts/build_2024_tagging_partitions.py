"""Split `use_cases_2024` into agency partitions (A–F) per
`docs/plans/2024-tagging/PLAN.md` Wave 1, and emit one CSV per partition.

Each row in the output CSV gives a Wave-1 subagent everything it needs:
the narrative columns + the lineage_status (joined from
`use_case_year_links`). No 2025 tags are leaked — `lineage_status` is the
match outcome, not the 2025 row's content.

Output:
    audit/retag/2024-tagging/inputs/A.csv
    audit/retag/2024-tagging/inputs/B.csv
    ...
    audit/retag/2024-tagging/inputs/F.csv
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = ROOT / "audit" / "retag" / "2024-tagging" / "inputs"

# Partitions per PLAN.md §Wave 1. Agency abbreviations as they appear in
# `use_cases_2024.agency_abbreviation`.
PARTITIONS = {
    "A": ["HHS", "VA"],
    "B": ["DOJ", "DOC", "DOE"],
    "C": ["DOT", "DHS", "TREAS", "FRB"],
    "D": ["USDA", "DOI", "USAID"],
    "E": ["STATE", "GSA", "DOL", "ED", "EPA", "SSA"],
    # F is "all remaining agencies"; filled in at runtime so a newly-loaded
    # agency doesn't silently get dropped.
    "F": None,
}

CSV_COLUMNS = (
    "id",
    "agency_abbreviation",
    "bureau",
    "use_case_name",
    "purpose_benefits",
    "outputs",
    "commercial_ai",
    "dev_method",
    "dev_stage",
    "topic_area",
    "lineage_status",
)


def _all_agency_abbrs(conn: sqlite3.Connection) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT agency_abbreviation FROM use_cases_2024 "
            "WHERE agency_abbreviation IS NOT NULL"
        ).fetchall()
    ]


def _resolve_partitions(conn: sqlite3.Connection) -> dict[str, list[str]]:
    resolved: dict[str, list[str]] = {}
    claimed: set[str] = set()
    for letter, abbrs in PARTITIONS.items():
        if abbrs is None:
            continue
        resolved[letter] = abbrs
        claimed.update(abbrs)
    all_abbrs = set(_all_agency_abbrs(conn))
    resolved["F"] = sorted(all_abbrs - claimed)
    return resolved


def _rows_for_agencies(
    conn: sqlite3.Connection, abbrs: list[str]
) -> list[sqlite3.Row]:
    if not abbrs:
        return []
    placeholders = ",".join(["?"] * len(abbrs))
    # GROUP_CONCAT in the join collapses the rare case of multiple lineage
    # links per use_case (id 32100 has 3 — a 1-to-many `split`). Without
    # the GROUP BY, that row gets emitted 3× in the partition.
    return conn.execute(
        f"""
        SELECT
            u.id,
            u.agency_abbreviation,
            COALESCE(u.bureau, '') AS bureau,
            COALESCE(u.use_case_name, '') AS use_case_name,
            COALESCE(u.purpose_benefits, '') AS purpose_benefits,
            COALESCE(u.outputs, '') AS outputs,
            COALESCE(u.commercial_ai, '') AS commercial_ai,
            COALESCE(u.dev_method, '') AS dev_method,
            COALESCE(u.dev_stage, '') AS dev_stage,
            COALESCE(u.topic_area, '') AS topic_area,
            COALESCE(GROUP_CONCAT(DISTINCT l.lineage_status), '') AS lineage_status
        FROM use_cases_2024 u
        LEFT JOIN use_case_year_links l ON l.uc_2024_id = u.id
        WHERE u.agency_abbreviation IN ({placeholders})
        GROUP BY u.id
        ORDER BY u.agency_abbreviation, u.id
        """,
        abbrs,
    ).fetchall()


def build(
    conn: sqlite3.Connection, out_dir: Path = DEFAULT_OUT
) -> dict[str, int]:
    partitions = _resolve_partitions(conn)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for letter, abbrs in partitions.items():
        rows = _rows_for_agencies(conn, abbrs)
        path = out_dir / f"{letter}.csv"
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(CSV_COLUMNS)
            for r in rows:
                w.writerow([r[c] for c in CSV_COLUMNS])
        counts[letter] = len(rows)
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        counts = build(conn, args.out)
    finally:
        conn.close()

    total = sum(counts.values())
    for letter, n in counts.items():
        print(f"  {letter}: {n} rows")
    print(f"total: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
