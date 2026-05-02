"""Create use_case_external_evidence table and backfill from agent CSVs.

This table records what we know about a use case beyond the inventory itself:
- Corroborating external sources (press, agency announcement, vendor case study)
- Per-row searches that found no external source
- Agent reviews that verified the inventory narrative without finding an
  external source (because the search was at the agency level)

States:
  corroborated         — non-inventory URL or substantive quote attached
  searched_no_source   — explicit per-row search performed, nothing found
  inventory_only       — reviewed against inventory text only

Idempotent: drops/recreates the table on each run, then backfills.
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

CAPTURED_BY = "agent_2026-04_retag_audit"
CAPTURED_AT = "2026-04-29"

DDL = """
CREATE TABLE IF NOT EXISTS use_case_external_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    use_case_id INTEGER REFERENCES use_cases(id),
    consolidated_use_case_id INTEGER REFERENCES consolidated_use_cases(id),
    topic TEXT NOT NULL,
    status TEXT NOT NULL,
    source_url TEXT,
    source_quote TEXT,
    confidence TEXT,
    search_method TEXT,
    captured_at TEXT NOT NULL,
    captured_by TEXT NOT NULL,
    notes TEXT,
    CHECK ((use_case_id IS NOT NULL) <> (consolidated_use_case_id IS NOT NULL)),
    CHECK (status IN ('corroborated','searched_no_source','inventory_only')),
    CHECK (status != 'corroborated' OR source_url IS NOT NULL OR source_quote IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_evidence_use_case ON use_case_external_evidence(use_case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_consolidated ON use_case_external_evidence(consolidated_use_case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_topic ON use_case_external_evidence(topic);
CREATE INDEX IF NOT EXISTS idx_evidence_status ON use_case_external_evidence(status);
"""


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    # Idempotent backfill: clear rows captured by this run, keep manual additions.
    conn.execute(
        "DELETE FROM use_case_external_evidence WHERE captured_by = ?",
        (CAPTURED_BY,),
    )


def _resolve_target(conn: sqlite3.Connection, csv_id: str) -> tuple[int | None, int | None]:
    """Map a CSV use_case_id field to (use_case_id, consolidated_use_case_id).
    Most CSVs use the use_cases.id directly. Coding CSV also has a few rows
    that point to consolidated_use_cases.id (the 'db_consolidated_X' refs).
    Detect by trying use_cases first, falling back to consolidated.
    """
    try:
        n = int(csv_id)
    except ValueError:
        return None, None
    if conn.execute("SELECT 1 FROM use_cases WHERE id = ?", (n,)).fetchone():
        return n, None
    if conn.execute("SELECT 1 FROM consolidated_use_cases WHERE id = ?", (n,)).fetchone():
        return None, n
    return None, None


def backfill_general_llm(conn: sqlite3.Connection) -> dict:
    stats = {"corroborated": 0, "skipped_no_evidence": 0, "skipped_no_target": 0}
    with open(LLM_CSV) as f:
        for row in csv.DictReader(f):
            url = (row.get("evidence_url") or "").strip()
            quote = (row.get("evidence_quote") or "").strip()
            if not (url.startswith("http") or quote):
                stats["skipped_no_evidence"] += 1
                continue
            uc_id, cons_id = _resolve_target(conn, row["use_case_id"])
            if uc_id is None and cons_id is None:
                stats["skipped_no_target"] += 1
                continue
            conn.execute(
                """
                INSERT INTO use_case_external_evidence
                    (use_case_id, consolidated_use_case_id, topic, status,
                     source_url, source_quote, confidence,
                     search_method, captured_at, captured_by, notes)
                VALUES (?, ?, 'general_llm', 'corroborated', ?, ?, ?,
                        'agent_web_verification_agency_level', ?, ?, ?)
                """,
                (
                    uc_id, cons_id,
                    url if url.startswith("http") else None,
                    quote or None,
                    (row.get("confidence") or "").strip().lower() or None,
                    CAPTURED_AT, CAPTURED_BY,
                    (row.get("notes") or "").strip() or None,
                ),
            )
            stats["corroborated"] += 1
    return stats


def backfill_topic_inventory_only(
    conn: sqlite3.Connection, csv_path: Path, topic: str
) -> dict:
    """For coding/data_analysis CSVs: write inventory_only rows for medium+
    high-confidence reviewed rows. These represent agent-verified inventory
    narrative, with external context inherited from the agency-level rollup.
    """
    stats = {"inventory_only": 0, "skipped_low": 0, "skipped_no_target": 0}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            confidence = (row.get("confidence") or "").strip().lower()
            if confidence not in {"high", "medium"}:
                stats["skipped_low"] += 1
                continue
            uc_id, cons_id = _resolve_target(conn, row["use_case_id"])
            if uc_id is None and cons_id is None:
                stats["skipped_no_target"] += 1
                continue
            quote = (row.get("evidence_quote") or "").strip()
            conn.execute(
                """
                INSERT INTO use_case_external_evidence
                    (use_case_id, consolidated_use_case_id, topic, status,
                     source_url, source_quote, confidence,
                     search_method, captured_at, captured_by, notes)
                VALUES (?, ?, ?, 'inventory_only', NULL, ?, ?,
                        'agent_inventory_review_with_agency_web_context', ?, ?, ?)
                """,
                (
                    uc_id, cons_id, topic,
                    quote or None,
                    confidence,
                    CAPTURED_AT, CAPTURED_BY,
                    (row.get("notes") or "").strip() or None,
                ),
            )
            stats["inventory_only"] += 1
    return stats


def main() -> int:
    conn = _open()
    try:
        with conn:
            _ensure_table(conn)
            llm = backfill_general_llm(conn)
            coding = backfill_topic_inventory_only(conn, CODING_CSV, "coding")
            data = backfill_topic_inventory_only(conn, DATA_CSV, "data_analysis")

        print("[general_llm]   ", llm)
        print("[coding]        ", coding)
        print("[data_analysis] ", data)

        totals = conn.execute(
            """
            SELECT topic, status, COUNT(*) AS n
            FROM use_case_external_evidence
            GROUP BY topic, status
            ORDER BY topic, status
            """
        ).fetchall()
        print("\nFinal evidence rows by (topic, status):")
        for r in totals:
            print(f"  {r['topic']:>14}  {r['status']:>20}  {r['n']:>5}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
