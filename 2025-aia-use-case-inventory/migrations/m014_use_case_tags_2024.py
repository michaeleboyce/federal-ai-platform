"""Create `use_case_tags_2024` + `use_case_tags_2024_canonical` view.

Mirrors `use_case_tags` (the 2025 IFP analytical tag schema in db.py) for
`use_cases_2024` rows. The 2025-only foreign keys (`consolidated_use_case_id`,
`product_id`, `template_id`) are dropped. Adds provenance columns the multi-wave
agent backfill needs: `wave`, `tagged_by_agent`, `reasoning`,
`quality_flags_json`, `confidence`.

Each `use_cases_2024` row will end up with at least one row in this table
(Wave 1), optionally a Wave 2a / 2b QA row, and optionally a Wave 3
reconciliation row. The `use_case_tags_2024_canonical` view picks the
latest non-calibration wave per use case.

Populated by `scripts/load_2024_tags.py` from CSVs under
`audit/retag/2024-tagging/{calibration,wave1,wave2a,wave2b,wave3}/`. See
`docs/plans/2024-tagging/PLAN.md`.

Idempotent. Safe to re-run.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "014_use_case_tags_2024"


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        is not None
    )


def _view_exists(conn: sqlite3.Connection, view: str) -> bool:
    return (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name=?",
            (view,),
        ).fetchone()
        is not None
    )


def _index_exists(conn: sqlite3.Connection, name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            (name,),
        ).fetchone()
        is not None
    )


def apply(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "use_case_tags_2024"):
        conn.execute(
            """
            CREATE TABLE use_case_tags_2024 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                use_case_id_2024 INTEGER NOT NULL REFERENCES use_cases_2024(id),

                -- What the entry represents
                entry_type TEXT,
                is_product_capability_entry INTEGER DEFAULT 0,
                product_capability TEXT,

                -- Tool categorization
                is_general_llm_access INTEGER,
                is_coding_tool INTEGER,
                is_cots_commercial INTEGER,
                tool_product_name TEXT,
                tool_vendor TEXT,

                -- Sophistication
                ai_sophistication TEXT,
                is_generative_ai INTEGER,
                is_frontier_model INTEGER,

                -- Deployment scope
                deployment_scope TEXT,
                scope_detail TEXT,
                is_enterprise_wide INTEGER,
                estimated_user_count TEXT,

                -- Architecture
                architecture_type TEXT,
                has_model_training INTEGER,

                -- Product detail
                cots_product_name TEXT,
                cots_vendor TEXT,
                is_microsoft_copilot INTEGER,
                is_openai INTEGER,
                is_anthropic INTEGER,
                is_google INTEGER,
                is_github_copilot INTEGER,
                is_aws_ai INTEGER,

                -- Mission characterization
                use_type TEXT,
                is_public_facing INTEGER,

                -- Governance
                has_meaningful_risk_docs INTEGER,
                high_impact_designation TEXT,
                deployment_environment TEXT,
                has_ato_or_fedramp INTEGER,

                -- Provenance (new for the 2024 multi-wave backfill)
                wave TEXT NOT NULL,
                tagged_by_agent TEXT,
                reasoning TEXT,
                quality_flags_json TEXT,
                confidence TEXT,

                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT,

                UNIQUE (use_case_id_2024, wave, tagged_by_agent)
            )
            """
        )

    indexes = [
        ("idx_uct2024_use_case", "use_case_id_2024"),
        ("idx_uct2024_wave", "wave"),
        ("idx_uct2024_is_gen_ai", "is_generative_ai"),
        ("idx_uct2024_scope", "deployment_scope"),
        ("idx_uct2024_entry_type", "entry_type"),
        ("idx_uct2024_uc_wave", "use_case_id_2024, wave"),
    ]
    for name, cols in indexes:
        if not _index_exists(conn, name):
            conn.execute(
                f"CREATE INDEX {name} ON use_case_tags_2024({cols})"
            )

    # Canonical view: latest non-calibration wave per use case.
    # Wave precedence: 3 > 2a/2b > 1. Calibration is excluded.
    # Implemented via wave_rank so the latest wave wins regardless of
    # insertion order.
    if _view_exists(conn, "use_case_tags_2024_canonical"):
        conn.execute("DROP VIEW use_case_tags_2024_canonical")
    conn.execute(
        """
        CREATE VIEW use_case_tags_2024_canonical AS
        WITH ranked AS (
            SELECT
                t.*,
                CASE wave
                    WHEN '3'  THEN 3
                    WHEN '2a' THEN 2
                    WHEN '2b' THEN 2
                    WHEN '1'  THEN 1
                    ELSE 0
                END AS wave_rank
            FROM use_case_tags_2024 t
            WHERE wave IN ('1', '2a', '2b', '3')
        ),
        best AS (
            SELECT use_case_id_2024, MAX(wave_rank) AS max_rank
            FROM ranked
            GROUP BY use_case_id_2024
        )
        SELECT r.*
        FROM ranked r
        JOIN best b
          ON b.use_case_id_2024 = r.use_case_id_2024
         AND b.max_rank = r.wave_rank
        """
    )
