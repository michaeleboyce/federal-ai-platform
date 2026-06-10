"""Apply the 2024-vs-2025 divergence-queue resolutions to use_case_tags.

audit/retag/2024-vs-2025-divergence/resolutions.csv holds one reviewed
verdict per queue row (the 38 lineage-linked pairs where the verified 2024
tag suggested the 2025 tag was wrong). verdict=fix_2025 rows update the
flagged dimension on the 2025 tag row; keep_2025 rows are no-ops kept for
the record. Signature-resolved; idempotent; in `make fix`.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uc_signature import Resolver  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "audit" / "retag" / "2024-vs-2025-divergence" / "resolutions.csv"

INT_COLS = {
    "is_generative_ai", "is_general_llm_access", "is_coding_tool",
    "is_enterprise_wide", "is_frontier_model",
}
ALLOWED = INT_COLS | {"ai_sophistication", "deployment_scope", "entry_type"}


def main() -> int:
    if not CSV_PATH.exists():
        print(f"[divergence] {CSV_PATH.name} not present yet — skipped")
        return 0
    conn = sqlite3.connect(DB_PATH)
    try:
        res = Resolver(conn)
        stats = {"fixed": 0, "kept": 0, "skipped": 0}
        with conn:
            for row in csv.DictReader(open(CSV_PATH)):
                if (row.get("verdict") or "").strip() != "fix_2025":
                    stats["kept"] += 1
                    continue
                dim = (row.get("flagged_dimension") or "").strip()
                val = (row.get("corrected_value") or "").strip()
                if dim not in ALLOWED or not val:
                    stats["skipped"] += 1
                    continue
                value = int(val) if dim in INT_COLS else val
                for uc_id in res.uc(None, row["agency"], row["use_case_name"]):
                    conn.execute(
                        f"UPDATE use_case_tags SET {dim} = ? WHERE use_case_id = ?",
                        (value, uc_id),
                    )
                    stats["fixed"] += 1
        print(f"[divergence] {stats}")
        res.check("apply_divergence_resolutions")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
