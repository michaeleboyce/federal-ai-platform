"""Rename use_cases columns to OMB-canonical names where the divergence
adds confusion without offsetting value.

Renames 15 columns. The 5 remaining divergences (`stage_of_development`,
`development_type`, `system_name`, `training_data_description`, `has_ato`)
plus the unique-key column `bureau_component` stay as-is — they're
referenced from too many call sites for the marginal accuracy gain.

Idempotent: each ALTER is guarded by checking PRAGMA table_info.
"""
from __future__ import annotations

import sqlite3

MIGRATION_ID = "002_rename_to_omb_canonical"

# (current_name, omb_canonical_name)
RENAMES = [
    ("withheld_from_public", "is_withheld"),
    ("involves_pii", "has_pii"),
    ("federal_data_catalog_link", "link_to_data"),
    ("pia_link", "pia_url"),
    ("demographic_variables", "demographic_features"),
    ("open_source_link", "code_url"),
    ("pre_deployment_testing", "hi_testing_conducted"),
    ("impact_assessment", "hi_assessment_completed"),
    ("potential_impacts", "hi_potential_impacts"),
    ("independent_review", "hi_independent_review"),
    ("ongoing_monitoring", "hi_ongoing_monitoring"),
    ("operator_training", "hi_training_established"),
    ("has_fail_safe", "hi_failsafe_presence"),
    ("appeal_process", "hi_appeal_process"),
    ("end_user_feedback", "hi_public_consultation"),
]


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}


def apply(conn: sqlite3.Connection) -> None:
    cols = _columns(conn, "use_cases")
    for old, new in RENAMES:
        if old in cols and new not in cols:
            conn.execute(f"ALTER TABLE use_cases RENAME COLUMN {old} TO {new}")
        elif new in cols and old in cols:
            # Both present (shouldn't happen in normal flow, but possible if
            # a partial run left a stale row). Drop the duplicated old.
            # SQLite supports DROP COLUMN since 3.35.
            conn.execute(f"ALTER TABLE use_cases DROP COLUMN {old}")
        # else: already renamed (new present, old absent), or column never
        # existed (table was created from scratch with new names) — no-op.
