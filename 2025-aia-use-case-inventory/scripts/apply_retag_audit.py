"""Apply 2026-04 retag-audit corrections from audit/retag/*/by_row.csv.

Three agent-produced CSVs:
  - audit/retag/general_llm/by_row.csv   (FOUO LLM scope/flag corrections)
  - audit/retag/coding/by_row.csv        (coding-tool flag + product name)
  - audit/retag/data_analysis/by_row.csv (deployment_environment backfill)

Conservative policy: auto-apply only medium/high-confidence corrections.
Low-confidence rows stay in the CSVs as pending human review. The companion
audit/retag/{general_llm,coding,data_analysis}/by_agency.md rollups remain
the article-grade artifacts; this script just realigns the DB to them.

Rows are resolved by (agency, use_case_name) signature via
scripts/uc_signature.py — NEVER by the CSVs' raw `use_case_id`s, which
belong to the 2026-04 id space and rotate on every `make fix`. The resolver
hard-fails the build if more than 2% of rows cannot be matched, so this
apply pass can never silently no-op again (which it did, undetected,
between 2026-05 and 2026-06: StateChat stayed `bureau`, DOJ's
department-wide coding deployment stayed untagged).

Idempotent: re-running produces the same end state.
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
LLM_CSV = ROOT / "audit" / "retag" / "general_llm" / "by_row.csv"
CODING_CSV = ROOT / "audit" / "retag" / "coding" / "by_row.csv"
DATA_CSV = ROOT / "audit" / "retag" / "data_analysis" / "by_row.csv"

ENTERPRISE_SCOPES = {"enterprise_wide", "department"}


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _int(s: str) -> int | None:
    s = (s or "").strip()
    if s in {"", "NA"}:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _ids(res: Resolver, row: dict) -> list[int]:
    return res.uc(
        _int(row.get("use_case_id", "")),
        row.get("agency"),
        row.get("use_case_name"),
    )


def apply_general_llm(conn: sqlite3.Connection, res: Resolver) -> dict:
    """Apply only the evidence-bearing scope corrections.

    The agent produced 274 is_general_llm_access flips, all marked low-confidence
    and derived from name-pattern heuristics. We do NOT auto-apply those
    (they are queued for the round-3 micro-agent review). What we DO apply:
    deployment_scope/is_enterprise_wide on rows with an explicit evidence_url
    or evidence_quote — these are the agent's web-verified enterprise-rollout
    corrections (StateChat, VA GPT, DHSChat, etc.).
    """
    stats = {"scope_updates": 0, "skipped_no_evidence": 0}
    with open(LLM_CSV) as f:
        for row in csv.DictReader(f):
            scope = (row.get("corrected_deployment_scope") or "").strip()
            has_evidence = bool(
                (row.get("evidence_url") or "").strip()
                or (row.get("evidence_quote") or "").strip()
            )
            # `corrected_deployment_scope` doubles as a free-text column on
            # no-change rows; only canonical scope values are corrections.
            if scope not in {
                "enterprise_wide", "department", "bureau", "office", "team", "pilot",
            }:
                continue
            if not has_evidence:
                stats["skipped_no_evidence"] += 1
                continue
            is_enterprise = 1 if scope in ENTERPRISE_SCOPES else 0
            for uc_id in _ids(res, row):
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


def apply_coding(conn: sqlite3.Connection, res: Resolver) -> dict:
    """Apply medium+high-confidence coding corrections.

    Updates: is_coding_tool (flips both directions), tool_product_name,
    deployment_scope (when explicit). Skips low-confidence rows.
    """
    stats = {
        "flips_to_1": 0, "flips_to_0": 0, "product_name_set": 0,
        "scope_updates": 0, "skipped_low": 0,
    }
    with open(CODING_CSV) as f:
        for row in csv.DictReader(f):
            confidence = (row.get("confidence") or "").strip().lower()
            if confidence not in {"high", "medium"}:
                stats["skipped_low"] += 1
                continue
            current = _int(row["current_is_coding_tool"])
            corrected = _int(row["corrected_is_coding_tool"])
            product = (row.get("tool_product") or "").strip()
            scope = (row.get("corrected_deployment_scope") or "").strip()

            # Appendix-B template entries were audited under names like
            # "Generating code using AI (consolidated)" — they live in
            # consolidated_use_cases, keyed by consolidated_use_case_id.
            name = (row.get("use_case_name") or "").strip()
            if name.lower().endswith("(consolidated)"):
                base = name[: name.lower().rfind("(consolidated)")].strip()
                for cons_id in res.cons_by_signature(row.get("agency"), base):
                    if corrected is not None and corrected != current:
                        conn.execute(
                            "UPDATE use_case_tags SET is_coding_tool = ? WHERE consolidated_use_case_id = ?",
                            (corrected, cons_id),
                        )
                        stats["flips_to_1" if corrected == 1 else "flips_to_0"] += 1
                continue

            for uc_id in _ids(res, row):
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


def apply_data_analysis(conn: sqlite3.Connection, res: Resolver) -> dict:
    """Backfill deployment_environment for medium+high-confidence rows
    where the agent named a concrete environment (not 'unknown').
    """
    stats = {"env_set": 0, "skipped_low": 0, "skipped_unknown": 0, "skipped_platform_rows": 0}
    with open(DATA_CSV) as f:
        for row in csv.DictReader(f):
            confidence = (row.get("confidence") or "").strip().lower()
            env = (row.get("deployment_environment") or "").strip()
            if confidence not in {"high", "medium"}:
                stats["skipped_low"] += 1
                continue
            if not env or env == "unknown":
                stats["skipped_unknown"] += 1
                continue
            # Agency-platform synthesis rows span an id RANGE ("9099-9114");
            # they describe an environment, not a single inventory row, and
            # are consumed by the by_agency.md rollup instead.
            if "-" in (row.get("use_case_id") or ""):
                stats["skipped_platform_rows"] += 1
                continue
            for uc_id in _ids(res, row):
                conn.execute(
                    "UPDATE use_case_tags SET deployment_environment = ? WHERE use_case_id = ?",
                    (env, uc_id),
                )
                stats["env_set"] += 1
    return stats


def main() -> int:
    conn = _open()
    try:
        res = Resolver(conn)
        with conn:
            llm = apply_general_llm(conn, res)
            coding = apply_coding(conn, res)
            data = apply_data_analysis(conn, res)
        print("[general_llm]  ", llm)
        print("[coding]       ", coding)
        print("[data_analysis]", data)
        res.check("apply_retag_audit")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
