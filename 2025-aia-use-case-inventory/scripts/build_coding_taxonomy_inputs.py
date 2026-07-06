"""Build input slices for the coding_taxonomy_2026-07 adjudication pass.

Population: every individually-reported use case with is_coding_tool=1
(~70 rows). The round classifies each into a closed coding-tool taxonomy
(chat_assistant / ide_autocomplete / coding_agent / code_analysis_tool /
not_coding / unclear) so the article can say how much of federal "coding
AI" is actually agentic. See INSTRUCTIONS.md in the output directory.

Signature-keyed by (agency, use_case_name) — never numeric ids.

Writes audit/retag/coding_taxonomy_2026-07/input.csv + input_batch{1..N}.csv.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_DIR = ROOT / "audit" / "retag" / "coding_taxonomy_2026-07"

COLUMNS = [
    "agency",
    "use_case_name",
    "bureau_component",
    "stage_normalized",
    "tool_product_name",
    "system_name",
    "vendor_name",
    "development_type",
    "problem_statement",
    "expected_benefits",
    "system_outputs",
]


def fetch_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    raw = conn.execute(
        """
        SELECT a.abbreviation                     AS agency,
               uc.use_case_name,
               COALESCE(uc.bureau_component, '')  AS bureau_component,
               COALESCE(uc.stage_normalized, '')  AS stage_normalized,
               COALESCE(t.tool_product_name, '')  AS tool_product_name,
               COALESCE(uc.system_name, '')       AS system_name,
               COALESCE(uc.vendor_name, '')       AS vendor_name,
               COALESCE(uc.development_type, '')  AS development_type,
               COALESCE(uc.problem_statement, '') AS problem_statement,
               COALESCE(uc.expected_benefits, '') AS expected_benefits,
               COALESCE(uc.system_outputs, '')    AS system_outputs
          FROM use_cases uc
          JOIN use_case_tags t ON t.use_case_id = uc.id
          JOIN agencies a ON a.id = uc.agency_id
         WHERE COALESCE(t.is_coding_tool, 0) = 1
         ORDER BY a.abbreviation, uc.use_case_name
        """
    ).fetchall()
    if not raw:
        raise SystemExit("No is_coding_tool=1 rows found — wrong DB?")
    return [{k: r[k] for k in COLUMNS} for r in raw]


def pack_batches(rows: list[dict], n_batches: int) -> list[list[dict]]:
    by_agency: dict[str, list[dict]] = {}
    for r in rows:
        by_agency.setdefault(r["agency"], []).append(r)
    batches: list[list[dict]] = [[] for _ in range(n_batches)]
    for _, agency_rows in sorted(by_agency.items(), key=lambda kv: -len(kv[1])):
        smallest = min(batches, key=len)
        smallest.extend(agency_rows)
    return [b for b in batches if b]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--batches", type=int, default=2)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        rows = fetch_rows(conn)
    finally:
        conn.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def write(path: Path, rs: list[dict]) -> None:
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rs)

    write(OUT_DIR / "input.csv", rows)
    for i, batch in enumerate(pack_batches(rows, args.batches), start=1):
        write(OUT_DIR / f"input_batch{i}.csv", batch)
        agencies = sorted({r["agency"] for r in batch})
        print(f"batch{i}: {len(batch)} rows — {', '.join(agencies)}")
    print(f"total: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
