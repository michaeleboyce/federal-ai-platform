"""Apply LLM-resolved review_queue_products decisions.

Reads `recommendations.json` from each slice under
`audit/review_queue_resolution/{a_first_third,b_middle_third,c_last_third}/`
and applies them to the DB.

Per-decision behavior:

  link
    Insert (use_case_id|consolidated_use_case_id, product_id) into the
    appropriate edges table with confidence='inferred', evidence_text from
    the rec's evidence_quote. Skip if edge already exists. Mark the queue
    row llm_reviewed=1.

  add_alias
    Insert into product_aliases (product_id, alias_text). Looks up
    product_id by canonical_name. If canonical_name doesn't exist, queue
    a follow-up by writing to audit/review_queue_resolution/_pending_new_products.csv
    with the proposed name + alias text — does NOT auto-create products.
    Mark the queue row llm_reviewed=1.

  agency_internal_system
    No edge insert (the use case is already classifiable as custom_system
    via auto_tag.infer_entry_type). Mark the queue row llm_reviewed=1
    with llm_reasoning='agency_internal_system'.

  false_positive
    Mark the queue row llm_reviewed=1 with llm_reasoning='false_positive'.

  unclear
    Mark the queue row llm_reviewed=1 with llm_reasoning='unclear' so it's
    excluded from re-review without a human pass.

Idempotent: re-running counts existing edges as 'already_linked' and
counts already-marked queue rows as 'already_reviewed'.

Reads only — does NOT delete edges or aliases. To revert a decision,
set the queue row's llm_reviewed back to 0 and edit recommendations.json.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
RESOLUTION_DIR = ROOT / "audit" / "review_queue_resolution"
SLICES = ["a_first_third", "b_middle_third", "c_last_third"]


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_product_id(conn, canonical_name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM products WHERE canonical_name = ?",
        (canonical_name,),
    ).fetchone()
    return row["id"] if row else None


def _get_queue_row(conn, queue_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, use_case_id, consolidated_use_case_id, llm_reviewed "
        "FROM review_queue_products WHERE id = ?",
        (queue_id,),
    ).fetchone()


def _mark_reviewed(conn, queue_id: int, reasoning: str) -> None:
    conn.execute(
        "UPDATE review_queue_products SET llm_reviewed = 1, "
        "llm_reasoning = COALESCE(llm_reasoning, ?) WHERE id = ?",
        (reasoning, queue_id),
    )


def _insert_edge(
    conn,
    queue_row: sqlite3.Row,
    product_id: int,
    evidence: str,
) -> str:
    """Returns 'linked', 'already_linked', or 'no_target'."""
    if queue_row["use_case_id"] is not None:
        existing = conn.execute(
            "SELECT 1 FROM use_case_products WHERE use_case_id = ? AND product_id = ?",
            (queue_row["use_case_id"], product_id),
        ).fetchone()
        if existing:
            return "already_linked"
        conn.execute(
            "INSERT INTO use_case_products (use_case_id, product_id, evidence_text, confidence) "
            "VALUES (?, ?, ?, 'inferred')",
            (queue_row["use_case_id"], product_id, evidence[:500]),
        )
        return "linked"
    if queue_row["consolidated_use_case_id"] is not None:
        existing = conn.execute(
            "SELECT 1 FROM consolidated_use_case_products "
            "WHERE consolidated_use_case_id = ? AND product_id = ?",
            (queue_row["consolidated_use_case_id"], product_id),
        ).fetchone()
        if existing:
            return "already_linked"
        conn.execute(
            "INSERT INTO consolidated_use_case_products "
            "(consolidated_use_case_id, product_id, evidence_text, confidence) "
            "VALUES (?, ?, ?, 'inferred')",
            (queue_row["consolidated_use_case_id"], product_id, evidence[:500]),
        )
        return "linked"
    return "no_target"


def _insert_alias_or_queue(
    conn,
    canonical_name: str,
    alias_text: str,
    pending_writer,
    reason_extra: str,
) -> str:
    """Returns 'aliased', 'alias_exists', or 'queued_new_product'."""
    pid = _resolve_product_id(conn, canonical_name)
    if pid is None:
        pending_writer.writerow(
            {"canonical_name": canonical_name, "alias_text": alias_text, "extra": reason_extra}
        )
        return "queued_new_product"
    existing = conn.execute(
        "SELECT 1 FROM product_aliases WHERE product_id = ? AND alias_text = ?",
        (pid, alias_text),
    ).fetchone()
    if existing:
        return "alias_exists"
    conn.execute(
        "INSERT INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
        (pid, alias_text),
    )
    return "aliased"


def main() -> int:
    if not RESOLUTION_DIR.exists():
        print(f"[review-queue] dir not found: {RESOLUTION_DIR} — skipping")
        return 0

    pending_path = RESOLUTION_DIR / "_pending_new_products.csv"
    pending_f = open(pending_path, "w", newline="")
    pending_writer = csv.DictWriter(
        pending_f, fieldnames=["canonical_name", "alias_text", "extra"]
    )
    pending_writer.writeheader()

    conn = _open()
    stats = {
        "linked": 0,
        "already_linked": 0,
        "no_target": 0,
        "aliased": 0,
        "alias_exists": 0,
        "queued_new_product": 0,
        "agency_internal_system": 0,
        "false_positive": 0,
        "unclear": 0,
        "skipped_unknown_canonical": 0,
        "skipped_no_queue_row": 0,
        "queue_rows_reviewed": 0,
    }

    try:
        with conn:
            for slice_name in SLICES:
                rec_path = RESOLUTION_DIR / slice_name / "recommendations.json"
                if not rec_path.exists():
                    print(f"  {slice_name}: no recommendations.json — skipping")
                    continue
                recs = json.loads(rec_path.read_text())
                print(f"  {slice_name}: {len(recs)} recommendations")
                touched_queue_ids: set[int] = set()
                for rec in recs:
                    qid = rec.get("id")
                    decision = rec.get("decision")
                    if qid is None or decision is None:
                        continue
                    qrow = _get_queue_row(conn, qid)
                    if qrow is None:
                        stats["skipped_no_queue_row"] += 1
                        continue
                    touched_queue_ids.add(qid)

                    if decision == "link":
                        canonical = rec.get("canonical_name", "")
                        pid = _resolve_product_id(conn, canonical)
                        if pid is None:
                            stats["skipped_unknown_canonical"] += 1
                            continue
                        result = _insert_edge(
                            conn, qrow, pid, rec.get("evidence_quote") or canonical
                        )
                        stats[result] += 1

                    elif decision == "add_alias":
                        canonical = rec.get("canonical_name", "")
                        alias = rec.get("alias_text") or rec.get("evidence_quote", "")
                        if not (canonical and alias):
                            stats["skipped_unknown_canonical"] += 1
                            continue
                        result = _insert_alias_or_queue(
                            conn,
                            canonical,
                            alias.strip(),
                            pending_writer,
                            rec.get("rationale", "")[:200],
                        )
                        stats[result] += 1

                    elif decision == "agency_internal_system":
                        stats["agency_internal_system"] += 1
                    elif decision == "false_positive":
                        stats["false_positive"] += 1
                    elif decision == "unclear":
                        stats["unclear"] += 1

                # Mark every touched queue row reviewed (using the dominant
                # decision per row as the reasoning — for compound rows this
                # may understate but is a reasonable single-tag).
                for qid in touched_queue_ids:
                    decisions = sorted(
                        {r.get("decision", "") for r in recs if r.get("id") == qid}
                    )
                    reasoning = "+".join(decisions)
                    _mark_reviewed(conn, qid, reasoning)
                    stats["queue_rows_reviewed"] += 1

        print(f"[review-queue] {stats}")
        if stats["queued_new_product"] > 0:
            print(
                f"  ℹ {stats['queued_new_product']} alias proposals reference unknown "
                f"canonical names — see {pending_path.relative_to(ROOT)}"
            )
    finally:
        conn.close()
        pending_f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
