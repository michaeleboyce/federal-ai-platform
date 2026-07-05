"""Build input slices for the llm_flag_drift_2026-07 adjudication pass.

Targets every `use_case_tags` row with `is_general_llm_access = 1 AND
COALESCE(is_generative_ai, 0) = 0`. A general-purpose chat LLM is by
definition generative AI, so each such row is either (a) tagger drift —
the genai flag was missed, (b) a wrong LLM-access flag (embedded copilot,
NLP pipeline), or rarely (c) a defensible exception the reviewer must
explain.

Signature-keyed by (agency, use_case_name) — never numeric ids — with the
same narrative columns as audit/retag/general_llm_round3/input.csv so the
decision rule text can be reused verbatim.

Writes `audit/retag/llm_flag_drift_2026-07/input_batch{1..N}.csv` plus a
combined `input.csv`.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_DIR = ROOT / "audit" / "retag" / "llm_flag_drift_2026-07"

COLUMNS = [
    "agency",
    "use_case_name",
    "bureau_component",
    "current_is_general_llm_access",
    "current_is_generative_ai",
    "ai_sophistication",
    "tool_product_name",
    "stage_of_development",
    "ai_classification",
    "system_name",
    "vendor_name",
    "problem_statement",
    "expected_benefits",
    "system_outputs",
]


def fetch_rows(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT a.abbreviation                       AS agency,
               uc.use_case_name,
               COALESCE(uc.bureau_component, '')    AS bureau_component,
               t.is_general_llm_access              AS current_is_general_llm_access,
               COALESCE(t.is_generative_ai, 0)      AS current_is_generative_ai,
               COALESCE(t.ai_sophistication, '')    AS ai_sophistication,
               COALESCE(t.tool_product_name, '')    AS tool_product_name,
               COALESCE(uc.stage_of_development, '') AS stage_of_development,
               COALESCE(uc.ai_classification, '')   AS ai_classification,
               COALESCE(uc.system_name, '')         AS system_name,
               COALESCE(uc.vendor_name, '')         AS vendor_name,
               COALESCE(uc.problem_statement, '')   AS problem_statement,
               COALESCE(uc.expected_benefits, '')   AS expected_benefits,
               COALESCE(uc.system_outputs, '')      AS system_outputs
          FROM use_cases uc
          JOIN use_case_tags t ON t.use_case_id = uc.id
          JOIN agencies a ON a.id = uc.agency_id
         WHERE t.is_general_llm_access = 1
           AND COALESCE(t.is_generative_ai, 0) = 0
         ORDER BY a.abbreviation, uc.use_case_name
        """
    ).fetchall()
    if not rows:
        raise SystemExit("No drift rows found — already adjudicated?")
    return [dict(zip(COLUMNS, r)) for r in rows]


def pack_batches(rows: list[dict], n_batches: int) -> list[list[dict]]:
    by_agency: dict[str, list[dict]] = {}
    for r in rows:
        by_agency.setdefault(r["agency"], []).append(r)
    batches: list[list[dict]] = [[] for _ in range(n_batches)]
    for _, agency_rows in sorted(
        by_agency.items(), key=lambda kv: -len(kv[1])
    ):
        smallest = min(batches, key=len)
        smallest.extend(agency_rows)
    return [b for b in batches if b]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--batches", type=int, default=6)
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
