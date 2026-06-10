"""Apply the 2026-06 product-queue review verdicts.

audit/product_queue_review_2026-06/verdicts_batch*.csv hold one verdict per
review_queue_products row (the 626 compound/unmatched vendor strings).
For each verdict this script:

  map_to_existing        link the use case to the named catalog product(s)
                         (INSERT OR IGNORE, confidence='inferred')
  propose_new            seed the product ("Name (Vendor)") then link
  false_positive /
  agency_internal_system /
  unclear                no edge; verdict recorded on the queue row only

Every verdict also marks the matching queue row llm_reviewed=1 with the
reviewer's reasoning, keyed by (use case signature, source_text prefix) —
NEVER by queue id, which rotates with every rebuild. Idempotent; wired
into `make fix` after the queue is rebuilt.
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
DIR = ROOT / "audit" / "product_queue_review_2026-06"

DECISIONS = {
    "map_to_existing", "propose_new", "agency_internal_system",
    "false_positive", "unclear",
}


def _product_id(conn, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM products WHERE canonical_name = ?", (name,)
    ).fetchone()
    if row:
        return row[0]
    row = conn.execute(
        "SELECT product_id FROM product_aliases WHERE LOWER(alias_text) = LOWER(?)",
        (name,),
    ).fetchone()
    return row[0] if row else None


def main() -> int:
    files = sorted(DIR.glob("verdicts_batch*.csv"))
    if not files:
        print("[product-queue] no verdict files yet — skipped")
        return 0
    conn = sqlite3.connect(DB_PATH)
    try:
        res = Resolver(conn)
        stats = {
            "linked": 0, "products_seeded": 0, "queue_marked": 0,
            "no_edge_verdicts": 0, "unknown_product": 0, "bad_rows": 0,
        }
        with conn:
            for f in files:
                for row in csv.DictReader(open(f)):
                    decision = (row.get("decision") or "").strip()
                    if decision not in DECISIONS:
                        stats["bad_rows"] += 1
                        continue
                    uc_ids = res.uc(None, row.get("agency"), row.get("use_case_name"))
                    if not uc_ids:
                        stats["bad_rows"] += 1
                        continue
                    reasoning = (row.get("reasoning") or "").strip()[:500]
                    confidence = (row.get("confidence") or "").strip().lower()

                    # House policy (matches apply_retag_audit): only
                    # medium/high-confidence verdicts create edges or seed
                    # products. Low-confidence verdicts are recorded on the
                    # queue row for a human pass but change nothing.
                    if confidence == "low" and decision in {"map_to_existing", "propose_new"}:
                        decision = "low_confidence_deferred"

                    # Seed proposed products first so mapping can hit them.
                    if decision == "propose_new":
                        prop = (row.get("proposed_new") or "").strip()
                        if prop:
                            name, vendor = prop, None
                            if prop.endswith(")") and "(" in prop:
                                name, _, v = prop.rpartition("(")
                                name, vendor = name.strip(), v.rstrip(")").strip()
                            if name and _product_id(conn, name) is None:
                                conn.execute(
                                    """INSERT INTO products (canonical_name, vendor,
                                         product_type, is_generative_ai, is_frontier_llm, notes)
                                       VALUES (?, ?, 'other', 0, 0,
                                               'seeded by product_queue_review_2026-06')""",
                                    (name, vendor),
                                )
                                conn.execute(
                                    "INSERT OR IGNORE INTO product_aliases (product_id, alias_text) "
                                    "VALUES (last_insert_rowid(), ?)",
                                    (name,),
                                )
                                stats["products_seeded"] += 1
                            row["mapped_products"] = " ;; ".join(
                                x for x in [(row.get("mapped_products") or "").strip(), name] if x
                            )
                        decision = "map_to_existing"

                    if decision == "map_to_existing":
                        names = [
                            n.strip()
                            for n in (row.get("mapped_products") or "").split(";;")
                            if n.strip()
                        ]
                        for n in names:
                            pid = _product_id(conn, n)
                            if pid is None:
                                stats["unknown_product"] += 1
                                continue
                            for uc_id in uc_ids:
                                conn.execute(
                                    """INSERT OR IGNORE INTO use_case_products
                                         (use_case_id, product_id, evidence_text, confidence)
                                       VALUES (?, ?, ?, 'inferred')""",
                                    (uc_id, pid, f"product_queue_review_2026-06: {reasoning}"),
                                )
                                stats["linked"] += 1
                    else:
                        stats["no_edge_verdicts"] += 1

                    src = (row.get("source_text") or "")[:500]
                    for uc_id in uc_ids:
                        stats["queue_marked"] += conn.execute(
                            """UPDATE review_queue_products
                                  SET llm_reviewed = 1,
                                      llm_confidence = ?,
                                      llm_reasoning = ?
                                WHERE use_case_id = ?
                                  AND substr(COALESCE(source_text,''), 1, 500) = ?""",
                            (confidence or None,
                             f"{decision}: {reasoning}", uc_id, src),
                        ).rowcount
        print(f"[product-queue] {stats}")
        res.check("apply_product_queue_review")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
