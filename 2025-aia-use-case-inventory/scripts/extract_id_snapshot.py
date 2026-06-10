"""Extract an old-id → signature snapshot CSV from a historical DB blob.

The 2026-04 retag audits (audit/retag/{general_llm,coding,data_analysis}/
and audit/retag/round2/) recorded `use_case_id`s from the DB as it stood on
2026-04-29. Those AUTOINCREMENT ids do not survive `make fix` rebuilds, so
the apply scripts must translate them to stable signatures. This script
materializes that translation table once, from the dashboard repo's
committed DB at the matching point in history:

    cd dashboard && git show 6ae2bcd:data/federal_ai_inventory_2025.db > /tmp/db-20260413.db
    python3 scripts/extract_id_snapshot.py /tmp/db-20260413.db

Output: audit/retag/id_snapshot_2026-04.csv with columns
    kind        'uc' (use_cases) or 'cons' (consolidated_use_cases)
    old_id      the id as it appears in the 2026-04 audit CSVs
    agency      agency abbreviation
    name        use_case_name (uc) or ai_use_case (cons), verbatim

Verified anchors: 7437 = DHS "Source Code Development Tool",
8713 = DOJ "Code Development", 10265 = State "StateChat".
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audit" / "retag" / "id_snapshot_2026-04.csv"


def main(db_path: str) -> int:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    rows: list[tuple[str, int, str, str]] = []
    for kind, sql in (
        (
            "uc",
            """SELECT u.id, a.abbreviation, u.use_case_name
                 FROM use_cases u JOIN agencies a ON a.id = u.agency_id""",
        ),
        (
            "cons",
            """SELECT c.id, a.abbreviation, c.ai_use_case
                 FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id""",
        ),
    ):
        for r in conn.execute(sql):
            rows.append((kind, r[0], r[1] or "", r[2] or ""))
    conn.close()

    anchors = {(k, i) for k, i, _, _ in rows}
    for want in (("uc", 7437), ("uc", 8713), ("uc", 10265)):
        if want not in anchors:
            print(f"FATAL: anchor {want} missing — wrong snapshot DB?")
            return 1

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "old_id", "agency", "name"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/db-20260413.db"))
