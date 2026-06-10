"""Recompute `use_cases.stage_normalized` and `ai_classification_normalized`.

Runs on every `make fix` immediately after `load_2024.py` (the loader
wipes/re-inserts `use_cases`, so these derived columns must be recomputed
each rebuild). Schema comes from migrations/m016_normalized_columns.py,
which this script applies first (the migration ledger makes that a no-op
when already applied).

The stage CASE is the single source of truth shared with the dashboard —
`dashboard/lib/db/shared/sql-fragments.ts` (STAGE_BUCKET_SQL) reads the
column instead of re-deriving once this ships; keep the two in sync if the
bucketing ever changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_connection  # noqa: E402
from scripts.run_migrations import apply_migrations  # noqa: E402

STAGE_SQL = """
UPDATE use_cases SET stage_normalized = CASE
    WHEN stage_of_development IS NULL OR TRIM(stage_of_development) = ''
      THEN 'unknown'
    WHEN LOWER(stage_of_development) LIKE '%retired%' THEN 'retired'
    WHEN LOWER(stage_of_development) LIKE '%pilot%' THEN 'pilot'
    WHEN LOWER(stage_of_development) LIKE '%deployed%' THEN 'deployed'
    WHEN LOWER(stage_of_development) LIKE '%production%' THEN 'deployed'
    WHEN LOWER(stage_of_development) LIKE '%operation and maintenance%' THEN 'deployed'
    WHEN LOWER(stage_of_development) LIKE '%pre-deployment%'
      OR LOWER(stage_of_development) LIKE '%pre deployment%'
      OR LOWER(stage_of_development) LIKE '%development or acquisition%'
      OR LOWER(stage_of_development) LIKE '%acquisition and/or development%'
      OR LOWER(stage_of_development) IN
         ('ideation', 'sandbox', 'initiated', 'being evaluated')
      THEN 'pre_deployment'
    ELSE 'unknown'
END
"""

# Order matters: 'agentic' before 'generative' (no current overlap, but an
# "Agentic AI: generative..." definition string must stay Agentic), LLM
# wording maps to Generative AI, bare "machine learning" variants map to
# the classical bucket.
AI_CLASS_SQL = """
UPDATE use_cases SET ai_classification_normalized = CASE
    WHEN ai_classification IS NULL OR TRIM(ai_classification) = ''
      OR LOWER(TRIM(ai_classification)) = 'n/a'
      THEN 'Unspecified'
    WHEN LOWER(ai_classification) LIKE '%agentic%' THEN 'Agentic AI'
    WHEN LOWER(ai_classification) LIKE '%generative%'
      OR LOWER(ai_classification) LIKE '%large language model%'
      THEN 'Generative AI'
    WHEN LOWER(ai_classification) LIKE '%computer vision%' THEN 'Computer Vision'
    WHEN LOWER(ai_classification) LIKE '%natural language%'
      OR LOWER(ai_classification) LIKE '%(nlp)%'
      OR LOWER(ai_classification) LIKE '%named-entity recognition%'
      THEN 'Natural Language Processing'
    WHEN LOWER(ai_classification) LIKE '%reinforcement learning%'
      THEN 'Reinforcement Learning'
    WHEN LOWER(ai_classification) LIKE '%classical%'
      OR LOWER(ai_classification) LIKE '%predictive%'
      OR LOWER(ai_classification) LIKE '%machine learning%'
      THEN 'Classical/Predictive Machine Learning'
    ELSE 'Other'
END
"""


def main() -> int:
    conn = get_connection()
    try:
        apply_migrations(conn)
        with conn:
            conn.execute(STAGE_SQL)
            conn.execute(AI_CLASS_SQL)
        stage = conn.execute(
            "SELECT stage_normalized, COUNT(*) FROM use_cases GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()
        klass = conn.execute(
            "SELECT ai_classification_normalized, COUNT(*) FROM use_cases GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()
        print("=== normalize_use_case_fields ===")
        print("stage_normalized:", {r[0]: r[1] for r in stage})
        print("ai_classification_normalized:", {r[0]: r[1] for r in klass})
        # Blank filings legitimately land in 'unknown' (~290 rows); the guard
        # is for NON-blank variants the CASE failed to bucket.
        unmatched = conn.execute(
            """SELECT COUNT(*) FROM use_cases
                WHERE stage_normalized = 'unknown'
                  AND TRIM(COALESCE(stage_of_development,'')) != ''"""
        ).fetchone()[0]
        total = sum(n for _, n in stage)
        if unmatched / max(total, 1) > 0.01:
            print(
                f"FATAL: {unmatched} non-blank stage values failed to bucket — "
                "a new free-text variant slipped past the CASE; extend STAGE_SQL."
            )
            return 1
        print(f"non-blank unmatched stage values: {unmatched}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
