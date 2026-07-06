"""Apply review_queue_llm labels back to use_case_tags.is_general_llm_access.

Rule (plan §B.8):
    UPDATE is_general_llm_access = llm_label
    WHERE llm_confidence IN ('high','medium')
      AND heuristic_label = llm_label

Everything else (disagreements, low-confidence, or NULL llm labels) is left
at its heuristic value and exported to ``audit/review_queue_llm_unresolved.csv``
for human follow-up.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
UNRESOLVED_CSV = ROOT / "audit" / "review_queue_llm_unresolved.csv"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # Auto-apply: agreement + medium/high confidence.
        applied = conn.execute(
            """
            UPDATE use_case_tags
            SET is_general_llm_access = (
                SELECT r.llm_label FROM review_queue_llm r
                WHERE r.use_case_id = use_case_tags.use_case_id
            )
            WHERE use_case_id IN (
                SELECT use_case_id FROM review_queue_llm
                WHERE llm_confidence IN ('high','medium')
                  AND heuristic_label = llm_label
            )
            """
        ).rowcount
        conn.execute(
            """
            UPDATE review_queue_llm
            SET applied = 1, applied_at = datetime('now')
            WHERE llm_confidence IN ('high','medium')
              AND heuristic_label = llm_label
              AND applied = 0
            """
        )
        conn.commit()
        print(f"Auto-applied {applied} rows (agreement + high/medium confidence)")

        # Export unresolved rows for human review.
        unresolved = conn.execute(
            """
            SELECT r.use_case_id,
                   u.use_case_id as source_use_case_id,
                   a.abbreviation as agency,
                   u.use_case_name,
                   u.ai_classification,
                   u.vendor_name,
                   r.heuristic_label,
                   r.llm_label,
                   r.llm_confidence,
                   r.llm_reasoning,
                   r.applied
            FROM review_queue_llm r
            JOIN use_cases u ON u.id = r.use_case_id
            JOIN agencies a ON a.id = u.agency_id
            WHERE r.applied = 0
            ORDER BY r.use_case_id
            """
        ).fetchall()

        UNRESOLVED_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(UNRESOLVED_CSV, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "internal_use_case_id", "source_use_case_id", "agency",
                "use_case_name", "ai_classification", "vendor_name",
                "heuristic_label", "llm_label", "llm_confidence",
                "llm_reasoning", "applied",
            ])
            for r in unresolved:
                w.writerow([r[k] for k in r.keys()])

        print(f"Exported {len(unresolved)} unresolved rows to {UNRESOLVED_CSV.relative_to(ROOT)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
