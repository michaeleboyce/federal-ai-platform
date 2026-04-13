"""Export unresolved rows from review_queue_llm to audit/review_queue_llm_unresolved.csv.

"Unresolved" = review_queue_llm.applied = 0. These rows still have the
heuristic label on the canonical use_case_tags.is_general_llm_access column
pending human review; the LLM's proposed label and reasoning live in the
queue row for reference.

Output columns:
    use_case_id, heuristic_label, llm_label, llm_confidence, llm_reasoning,
    agency, use_case_name, ai_classification

Run from 2025-aia-use-case-inventory/:
    python scripts/export_review_queue_llm_unresolved.py
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "federal_ai_inventory_2025.db"
OUT = REPO / "audit" / "review_queue_llm_unresolved.csv"

SQL = """
    SELECT
        q.use_case_id,
        q.heuristic_label,
        q.llm_label,
        q.llm_confidence,
        q.llm_reasoning,
        a.abbreviation AS agency,
        u.use_case_name,
        u.ai_classification
    FROM review_queue_llm q
    JOIN use_cases u ON u.id = q.use_case_id
    JOIN agencies a ON a.id = u.agency_id
    WHERE q.applied = 0
    ORDER BY
        CASE q.llm_confidence
            WHEN 'low' THEN 0
            WHEN 'medium' THEN 1
            WHEN 'high' THEN 2
            ELSE 3
        END,
        a.abbreviation,
        u.use_case_name
"""


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(SQL).fetchall()
    finally:
        conn.close()

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "use_case_id",
            "heuristic_label",
            "llm_label",
            "llm_confidence",
            "llm_reasoning",
            "agency",
            "use_case_name",
            "ai_classification",
        ])
        for r in rows:
            writer.writerow([
                r["use_case_id"],
                r["heuristic_label"],
                r["llm_label"] if r["llm_label"] is not None else "",
                r["llm_confidence"] or "",
                (r["llm_reasoning"] or "").replace("\r\n", " ").replace("\n", " "),
                r["agency"] or "",
                r["use_case_name"] or "",
                r["ai_classification"] or "",
            ])

    print(f"Wrote {len(rows)} unresolved rows -> {OUT}")


if __name__ == "__main__":
    main()
