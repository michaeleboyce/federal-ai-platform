"""Apply 2026-04 retag-audit corrections from audit/retag/*/by_row.csv.

Three agent-produced CSVs:
  - audit/retag/general_llm/by_row.csv   (FOUO LLM scope/flag corrections)
  - audit/retag/coding/by_row.csv        (coding-tool flag + product name)
  - audit/retag/data_analysis/by_row.csv (deployment_environment backfill)

Conservative policy: auto-apply only medium/high-confidence corrections.
Low-confidence rows stay in the CSVs as pending human review. The companion
audit/retag/{general_llm,coding,data_analysis}/by_agency.md rollups remain
the article-grade artifacts; this script just realigns the DB to them.

Idempotent: re-running produces the same end state.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
LLM_CSV = ROOT / "audit" / "retag" / "general_llm" / "by_row.csv"
CODING_CSV = ROOT / "audit" / "retag" / "coding" / "by_row.csv"
DATA_CSV = ROOT / "audit" / "retag" / "data_analysis" / "by_row.csv"

ENTERPRISE_SCOPES = {"enterprise_wide", "department"}


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _has_tag_row(conn: sqlite3.Connection, use_case_id: int) -> bool:
    return conn.execute(
        "SELECT 1 FROM use_case_tags WHERE use_case_id = ?", (use_case_id,)
    ).fetchone() is not None


def _int(s: str) -> int | None:
    s = (s or "").strip()
    if s in {"", "NA"}:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def apply_general_llm(conn: sqlite3.Connection) -> dict:
    """Apply only the evidence-bearing scope corrections.

    The agent produced 274 is_general_llm_access flips, all marked low-confidence
    and derived from name-pattern heuristics. We do NOT auto-apply those.
    What we DO apply: deployment_scope/is_enterprise_wide on rows with an
    explicit evidence_url or evidence_quote — these are the agent's web-verified
    enterprise-rollout corrections (StateChat, VA GPT, DHSChat, etc.).
    """
    stats = {"scope_updates": 0, "skipped_no_evidence": 0, "skipped_no_tag": 0}
    with open(LLM_CSV) as f:
        for row in csv.DictReader(f):
            uc_id = _int(row["use_case_id"])
            scope = (row.get("corrected_deployment_scope") or "").strip()
            has_evidence = bool(
                (row.get("evidence_url") or "").strip()
                or (row.get("evidence_quote") or "").strip()
            )
            if uc_id is None or not scope:
                continue
            if not has_evidence:
                stats["skipped_no_evidence"] += 1
                continue
            if not _has_tag_row(conn, uc_id):
                stats["skipped_no_tag"] += 1
                continue
            is_enterprise = 1 if scope in ENTERPRISE_SCOPES else 0
            conn.execute(
                """
                UPDATE use_case_tags
                SET deployment_scope = ?, is_enterprise_wide = ?
                WHERE use_case_id = ?
                """,
                (scope, is_enterprise, uc_id),
            )
            stats["scope_updates"] += 1
    return stats


def apply_coding(conn: sqlite3.Connection) -> dict:
    """Apply medium+high-confidence coding corrections.

    Updates: is_coding_tool (flips both directions), tool_product_name,
    deployment_scope (when explicit). Skips low-confidence rows.
    """
    stats = {
        "flips_to_1": 0, "flips_to_0": 0, "product_name_set": 0,
        "scope_updates": 0, "skipped_low": 0, "skipped_no_tag": 0,
    }
    with open(CODING_CSV) as f:
        for row in csv.DictReader(f):
            uc_id = _int(row["use_case_id"])
            if uc_id is None:
                continue
            confidence = (row.get("confidence") or "").strip().lower()
            if confidence not in {"high", "medium"}:
                stats["skipped_low"] += 1
                continue
            if not _has_tag_row(conn, uc_id):
                stats["skipped_no_tag"] += 1
                continue
            current = _int(row["current_is_coding_tool"])
            corrected = _int(row["corrected_is_coding_tool"])
            product = (row.get("tool_product") or "").strip()
            scope = (row.get("corrected_deployment_scope") or "").strip()

            if corrected is not None and corrected != current:
                conn.execute(
                    "UPDATE use_case_tags SET is_coding_tool = ? WHERE use_case_id = ?",
                    (corrected, uc_id),
                )
                if corrected == 1:
                    stats["flips_to_1"] += 1
                else:
                    stats["flips_to_0"] += 1
            if product:
                conn.execute(
                    """
                    UPDATE use_case_tags
                    SET tool_product_name = COALESCE(NULLIF(tool_product_name,''), ?)
                    WHERE use_case_id = ?
                    """,
                    (product, uc_id),
                )
                stats["product_name_set"] += 1
            if scope:
                is_enterprise = 1 if scope in ENTERPRISE_SCOPES else 0
                conn.execute(
                    """
                    UPDATE use_case_tags
                    SET deployment_scope = ?, is_enterprise_wide = ?
                    WHERE use_case_id = ?
                    """,
                    (scope, is_enterprise, uc_id),
                )
                stats["scope_updates"] += 1
    return stats


def apply_data_analysis(conn: sqlite3.Connection) -> dict:
    """Backfill deployment_environment for medium+high-confidence rows
    where the agent named a concrete environment (not 'unknown').
    """
    stats = {"env_set": 0, "skipped_low": 0, "skipped_unknown": 0, "skipped_no_tag": 0}
    with open(DATA_CSV) as f:
        for row in csv.DictReader(f):
            uc_id = _int(row["use_case_id"])
            if uc_id is None:
                continue
            confidence = (row.get("confidence") or "").strip().lower()
            env = (row.get("deployment_environment") or "").strip()
            if confidence not in {"high", "medium"}:
                stats["skipped_low"] += 1
                continue
            if not env or env == "unknown":
                stats["skipped_unknown"] += 1
                continue
            if not _has_tag_row(conn, uc_id):
                stats["skipped_no_tag"] += 1
                continue
            conn.execute(
                "UPDATE use_case_tags SET deployment_environment = ? WHERE use_case_id = ?",
                (env, uc_id),
            )
            stats["env_set"] += 1
    return stats


def main() -> int:
    conn = _open()
    try:
        with conn:
            llm = apply_general_llm(conn)
            coding = apply_coding(conn)
            data = apply_data_analysis(conn)
        print("[general_llm] ", llm)
        print("[coding]      ", coding)
        print("[data_analysis]", data)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
