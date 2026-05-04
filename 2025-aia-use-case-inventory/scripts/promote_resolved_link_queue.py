"""Promote resolved fedramp_link_queue rows into fedramp_product_links.

Resolves products.id via canonical_name OR alias (queue.inventory_id is
considered authoritative if it points at a current product, else we fall
back to source_text).

Extracts the chosen fedramp_id from decision_notes by:
    1. Direct regex `(?:FR|F1)\\d+[A-Z]*` matched against decision_notes.
       If multiple distinct ids match, this is ambiguous and the row is
       skipped (use accept_N or hand-link instead).
    2. Fallback `accept_N` -> deterministic Nth pick (1-indexed) from the
       structured candidate_fedramp_ids JSON. No guessing.

All extracted ids are validated against fedramp_products before insert.

Inserts with confidence='manual', source='link_queue', notes=full
decision_notes verbatim for provenance. Idempotent via INSERT OR IGNORE
against UNIQUE(inventory_product_id, fedramp_id, source).

Usage:
    python3 scripts/promote_resolved_link_queue.py            # dry-run
    python3 scripts/promote_resolved_link_queue.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

FR_ID_RE = re.compile(r"\b(?:FR|F1)\d+[A-Z]*\b")
ACCEPT_N_RE = re.compile(r"\baccept_(\d+)\b", re.IGNORECASE)


def _resolve_product_id(conn: sqlite3.Connection, inventory_id: int | None, source_text: str) -> int | None:
    if inventory_id is not None:
        row = conn.execute("SELECT 1 FROM products WHERE id = ?", (inventory_id,)).fetchone()
        if row is not None:
            return inventory_id
    row = conn.execute(
        "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)",
        (source_text,),
    ).fetchone()
    if row is not None:
        return row[0]
    row = conn.execute(
        "SELECT product_id FROM product_aliases WHERE LOWER(alias_text) = LOWER(?)",
        (source_text,),
    ).fetchone()
    if row is not None:
        return row[0]
    return None


def _extract_fedramp_ids(decision_notes: str, candidate_json: str | None) -> tuple[list[str], str]:
    """Return (list_of_ids, method) where method is 'regex'|'accept_n'|'none'."""
    notes = decision_notes or ""
    direct = list(dict.fromkeys(FR_ID_RE.findall(notes)))  # dedupe, preserve order
    if direct:
        return direct, "regex"
    m = ACCEPT_N_RE.search(notes)
    if m and candidate_json:
        try:
            candidates = json.loads(candidate_json)
        except json.JSONDecodeError:
            return [], "none"
        idx = int(m.group(1)) - 1  # 1-indexed → 0-indexed
        if 0 <= idx < len(candidates):
            cand = candidates[idx]
            fr_id = cand.get("fedramp_id") if isinstance(cand, dict) else None
            if fr_id:
                return [fr_id], "accept_n"
    return [], "none"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT id, inventory_id, source_text, decision_notes, candidate_fedramp_ids
        FROM fedramp_link_queue
        WHERE link_kind = 'product' AND status = 'resolved'
        ORDER BY id
        """
    ).fetchall()

    proposed = []
    skipped_no_product = []
    skipped_no_id = []
    skipped_ambiguous = []
    skipped_invalid_id = []
    skipped_already = []

    if args.apply:
        conn.execute("BEGIN")
    try:
        for qid, inv_id, source_text, notes, cand_json in rows:
            pid = _resolve_product_id(conn, inv_id, source_text)
            if pid is None:
                skipped_no_product.append((qid, source_text))
                continue
            ids, method = _extract_fedramp_ids(notes or "", cand_json)
            if not ids:
                skipped_no_id.append((qid, source_text))
                continue
            if method == "regex" and len(ids) > 1:
                skipped_ambiguous.append((qid, source_text, ids))
                continue
            for fr_id in ids:
                exists = conn.execute(
                    "SELECT 1 FROM fedramp_products WHERE fedramp_id = ?", (fr_id,)
                ).fetchone() is not None
                if not exists:
                    skipped_invalid_id.append((qid, source_text, fr_id))
                    continue
                already = conn.execute(
                    "SELECT 1 FROM fedramp_product_links "
                    "WHERE inventory_product_id = ? AND fedramp_id = ? AND source = 'link_queue'",
                    (pid, fr_id),
                ).fetchone() is not None
                if already:
                    skipped_already.append((qid, source_text, fr_id))
                    continue
                proposed.append((qid, source_text, pid, fr_id, method, notes))
                if args.apply:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO fedramp_product_links
                            (inventory_product_id, fedramp_id, confidence, source, notes)
                        VALUES (?, ?, 'manual', 'link_queue', ?)
                        """,
                        (pid, fr_id, notes or f"queue_id={qid}"),
                    )

        if args.apply:
            conn.commit()
    except Exception:
        if args.apply:
            conn.rollback()
        raise

    print(f"queue rows scanned: {len(rows)}")
    print(f"  proposed inserts:        {len(proposed)}")
    print(f"  skipped (no product):    {len(skipped_no_product)}")
    print(f"  skipped (no fedramp_id): {len(skipped_no_id)}")
    print(f"  skipped (ambiguous):     {len(skipped_ambiguous)}")
    print(f"  skipped (invalid id):    {len(skipped_invalid_id)}")
    print(f"  skipped (already):       {len(skipped_already)}")

    if proposed:
        print("\nProposed inserts:")
        for qid, src, pid, fr_id, method, _notes in proposed:
            print(f"  q{qid:>3}  pid={pid}  fedramp_id={fr_id:<14}  method={method:<8}  {src!r}")

    if skipped_invalid_id:
        print("\nSkipped: extracted fedramp_id not in fedramp_products:")
        for qid, src, fr_id in skipped_invalid_id:
            print(f"  q{qid:>3}  {src!r}  bad_id={fr_id!r}")

    if skipped_ambiguous:
        print("\nSkipped: multiple FR ids in decision_notes (regex ambiguous):")
        for qid, src, ids in skipped_ambiguous:
            print(f"  q{qid:>3}  {src!r}  ids={ids}")

    if not args.apply:
        print("\n(dry-run; pass --apply to write)")
    else:
        post = conn.execute("SELECT COUNT(*) FROM fedramp_product_links").fetchone()[0]
        print(f"\nfedramp_product_links row count post-apply: {post}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
