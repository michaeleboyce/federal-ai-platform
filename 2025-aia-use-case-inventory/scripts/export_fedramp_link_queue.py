"""Export pending FedRAMP link-queue rows to a CSV for human adjudication.

The CSV format is interchangeable with the dashboard's
`/api/fedramp-queue-export` endpoint — same columns, same row order — so an
adjudicator can edit either one and feed it back into
`scripts/import_fedramp_link_decisions.py`.

Usage (run from `2025-aia-use-case-inventory/`):

    # Vendor groupings (default), all vendors, write to stdout
    python scripts/export_fedramp_link_queue.py

    # Restrict to one vendor, write to a file
    python scripts/export_fedramp_link_queue.py --by=vendor --filter=Microsoft \\
        --out=audit/fedramp_queue_microsoft.csv

    # Group by ambiguity reason ('multi_candidate' | 'no_alias')
    python scripts/export_fedramp_link_queue.py --by=reason --filter=multi_candidate

    # Group by agency (only `link_kind='agency'` rows match)
    python scripts/export_fedramp_link_queue.py --by=agency --filter=VA

Columns (last two are blank — adjudicator fills):

    queue_id, link_kind, inventory_id, inventory_name, source_text, reason,
    candidate_1_fedramp_id, candidate_1_csp, candidate_1_cso, candidate_1_score,
    candidate_2_*, ..., candidate_5_*, decision, decision_notes

Idempotent: rows are sorted by queue_id ascending, so re-running produces a
byte-identical file (apart from any new queue rows added since last run).
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "federal_ai_inventory_2025.db"

MAX_CANDIDATES = 5

# Characters that, when leading a CSV cell, can trigger formula execution
# in Excel / Google Sheets / Numbers. OWASP "CSV injection" / "Formula
# injection" mitigation: prefix any such cell with a single quote.
_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value: object) -> str:
    """Sanitize a CSV cell against spreadsheet formula injection.

    The csv module quotes per RFC 4180, but does NOT defang formula
    triggers. We do that here, conservatively, by prefixing a single
    quote — the canonical Excel/Sheets defense.

    Examples:
        safe_cell("hello")       -> "hello"
        safe_cell("=CMD()")      -> "'=CMD()"
        safe_cell("+1 555-1234") -> "'+1 555-1234"
        safe_cell("\\tfoo")       -> "'\\tfoo"
        safe_cell(None)          -> ""
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in _FORMULA_TRIGGERS:
        return "'" + s
    return s

# ---------------------------------------------------------------------------

BASE_SQL = """
    SELECT q.id          AS queue_id,
           q.link_kind   AS link_kind,
           q.inventory_id,
           q.source_text,
           q.candidate_fedramp_ids,
           q.reason,
           CASE q.link_kind
             WHEN 'product' THEN p.canonical_name
             WHEN 'agency'  THEN a.name
           END AS inventory_name,
           p.vendor      AS product_vendor,
           a.abbreviation AS agency_abbr
      FROM fedramp_link_queue q
      LEFT JOIN products p ON q.link_kind = 'product' AND p.id = q.inventory_id
      LEFT JOIN agencies a ON q.link_kind = 'agency'  AND a.id = q.inventory_id
     WHERE q.status = 'pending'
"""


def _query(conn: sqlite3.Connection, by: str, value: str | None) -> list[sqlite3.Row]:
    sql = BASE_SQL
    params: tuple = ()
    if by == "vendor" and value is not None:
        sql += " AND q.link_kind = 'product' AND COALESCE(p.vendor,'(no vendor)') = ?"
        params = (value,)
    elif by == "reason" and value is not None:
        sql += " AND q.reason = ?"
        params = (value,)
    elif by == "agency" and value is not None:
        sql += " AND q.link_kind = 'agency' AND COALESCE(a.abbreviation,'(no agency)') = ?"
        params = (value,)
    elif by == "vendor":
        sql += " AND q.link_kind = 'product'"
    elif by == "agency":
        sql += " AND q.link_kind = 'agency'"
    # `reason` with no value: no extra filter — return everything pending.

    sql += " ORDER BY q.id ASC"
    return conn.execute(sql, params).fetchall()


def _candidate_columns() -> list[str]:
    cols = []
    for i in range(1, MAX_CANDIDATES + 1):
        cols.extend(
            [
                f"candidate_{i}_fedramp_id",
                f"candidate_{i}_csp",
                f"candidate_{i}_cso",
                f"candidate_{i}_score",
            ]
        )
    return cols


HEADER = [
    "queue_id",
    "link_kind",
    "inventory_id",
    "inventory_name",
    "source_text",
    "reason",
    *_candidate_columns(),
    "decision",
    "decision_notes",
]


def _row_to_record(row: sqlite3.Row) -> dict[str, str]:
    """Flatten a queue row + its candidate JSON into the wide CSV shape.

    Every emitted value is run through `safe_cell` to defang formula-
    injection attempts; the queue's `source_text` is the highest-risk
    field since it carries free-form vendor strings from inventory
    submissions.
    """
    rec: dict[str, str] = {
        "queue_id": safe_cell(row["queue_id"]),
        "link_kind": safe_cell(row["link_kind"]),
        "inventory_id": safe_cell(row["inventory_id"]),
        "inventory_name": safe_cell(row["inventory_name"]),
        "source_text": safe_cell(row["source_text"]),
        "reason": safe_cell(row["reason"]),
        "decision": "",
        "decision_notes": "",
    }
    # Pad/clip candidates to MAX_CANDIDATES.
    candidates: list[dict] = []
    if row["candidate_fedramp_ids"]:
        try:
            decoded = json.loads(row["candidate_fedramp_ids"])
            if isinstance(decoded, list):
                candidates = decoded
        except (TypeError, ValueError):
            candidates = []
    for i in range(MAX_CANDIDATES):
        c = candidates[i] if i < len(candidates) else {}
        # Agencies use parent_agency / parent_slug instead of csp / cso.
        csp = c.get("csp", c.get("parent_agency", ""))
        cso = c.get("cso", c.get("parent_slug", ""))
        score = c.get("score")
        rec[f"candidate_{i + 1}_fedramp_id"] = safe_cell(c.get("fedramp_id", "") or "")
        rec[f"candidate_{i + 1}_csp"] = safe_cell(csp or "")
        rec[f"candidate_{i + 1}_cso"] = safe_cell(cso or "")
        rec[f"candidate_{i + 1}_score"] = (
            "" if score is None else f"{float(score):.3f}"
        )
    return rec


def export(*, by: str, value: str | None, out: Path | None) -> int:
    if not DB.exists():
        raise SystemExit(
            f"DB not found at {DB} — did you run `make all` (or at least "
            f"`load_inventories.py` + `load_fedramp.py` + `link_fedramp.py`) yet?"
        )
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    try:
        rows = _query(conn, by, value)
    finally:
        conn.close()

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        fp = out.open("w", newline="", encoding="utf-8")
    else:
        fp = sys.stdout

    try:
        writer = csv.DictWriter(fp, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            writer.writerow(_row_to_record(row))
    finally:
        if out is not None:
            fp.close()

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--by",
        default="vendor",
        choices=["vendor", "reason", "agency"],
        help="Grouping dimension (default: vendor).",
    )
    parser.add_argument(
        "--filter",
        default=None,
        help="Restrict to a single group key (vendor name, reason, agency abbr).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output file path. If omitted, CSV is written to stdout.",
    )
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else None
    n = export(by=args.by, value=args.filter, out=out_path)
    if out_path is not None:
        print(
            f"Wrote {n} queue row(s) to {out_path} "
            f"(by={args.by}, filter={args.filter or '<all>'})",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
