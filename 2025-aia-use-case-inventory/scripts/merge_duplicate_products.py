"""Merge duplicate canonical product rows into a single survivor.

Repoints all dependent rows (product_aliases, use_case_products,
consolidated_use_case_products, entry_product_edges, fedramp_product_links,
parent_product_id self-refs) from loser → survivor, preserves the loser's
canonical_name as an alias under the survivor, then deletes the loser.
Asserts post-merge dependent-row totals equal the pre-merge sums.

Decisions for this run (driven by audit/fedramp_linkage_review/03_product_hierarchy.md):
    * NotebookLM (3219) ← Google NotebookLM (3350)
    * Azure AI Document Intelligence (3315) ← Azure AI Vision / Document Intelligence (3383)

The Microsoft 365 (3472) / M365 Apps for Enterprise (3473) pair is intentionally
NOT merged — they are distinct SKUs. The hierarchy phase will set 3473's
parent_product_id = 3472.

Usage:
    python scripts/merge_duplicate_products.py --dry-run   # default
    python scripts/merge_duplicate_products.py --apply
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

MERGES_BY_NAME: list[tuple[str, str]] = [
    ("NotebookLM", "Google NotebookLM"),
    ("Azure AI Document Intelligence", "Azure AI Vision / Document Intelligence"),
]

DEPENDENT_COUNT_QUERIES = [
    ("product_aliases",                "SELECT COUNT(*) FROM product_aliases WHERE product_id = ?"),
    ("use_case_products",              "SELECT COUNT(*) FROM use_case_products WHERE product_id = ?"),
    ("consolidated_use_case_products", "SELECT COUNT(*) FROM consolidated_use_case_products WHERE product_id = ?"),
    ("entry_product_edges",            "SELECT COUNT(*) FROM entry_product_edges WHERE product_id = ?"),
    ("fedramp_product_links",          "SELECT COUNT(*) FROM fedramp_product_links WHERE inventory_product_id = ?"),
    ("parent_of",                      "SELECT COUNT(*) FROM products WHERE parent_product_id = ?"),
]


def _counts(conn: sqlite3.Connection, pid: int) -> dict[str, int]:
    return {name: conn.execute(sql, (pid,)).fetchone()[0] for name, sql in DEPENDENT_COUNT_QUERIES}


def _merge_one(conn: sqlite3.Connection, survivor: int, loser: int, *, apply: bool) -> None:
    surv_row = conn.execute("SELECT id, canonical_name FROM products WHERE id = ?", (survivor,)).fetchone()
    lose_row = conn.execute("SELECT id, canonical_name FROM products WHERE id = ?", (loser,)).fetchone()
    if surv_row is None or lose_row is None:
        print(f"  SKIP: survivor={survivor!r} or loser={loser!r} no longer exists")
        return

    pre_surv = _counts(conn, survivor)
    pre_lose = _counts(conn, loser)
    expected = {k: pre_surv[k] + pre_lose[k] for k in pre_surv}

    # A use case (or alias / FedRAMP package) can be linked to BOTH sides of
    # the merge; repointing those loser rows would violate the UNIQUE
    # constraints. Count the overlaps, subtract them from the expectation,
    # and delete the loser's overlapping rows before the repoint.
    overlaps = {
        "use_case_products": conn.execute(
            """SELECT COUNT(*) FROM use_case_products l
                WHERE l.product_id = ? AND EXISTS (
                    SELECT 1 FROM use_case_products s
                     WHERE s.product_id = ? AND s.use_case_id = l.use_case_id)""",
            (loser, survivor),
        ).fetchone()[0],
        "consolidated_use_case_products": conn.execute(
            """SELECT COUNT(*) FROM consolidated_use_case_products l
                WHERE l.product_id = ? AND EXISTS (
                    SELECT 1 FROM consolidated_use_case_products s
                     WHERE s.product_id = ?
                       AND s.consolidated_use_case_id = l.consolidated_use_case_id)""",
            (loser, survivor),
        ).fetchone()[0],
        "product_aliases": conn.execute(
            """SELECT COUNT(*) FROM product_aliases l
                WHERE l.product_id = ? AND EXISTS (
                    SELECT 1 FROM product_aliases s
                     WHERE s.product_id = ? AND s.alias_text = l.alias_text)""",
            (loser, survivor),
        ).fetchone()[0],
        "fedramp_product_links": conn.execute(
            """SELECT COUNT(*) FROM fedramp_product_links l
                WHERE l.inventory_product_id = ? AND EXISTS (
                    SELECT 1 FROM fedramp_product_links s
                     WHERE s.inventory_product_id = ? AND s.fedramp_id = l.fedramp_id)""",
            (loser, survivor),
        ).fetchone()[0],
    }
    for key, n in overlaps.items():
        expected[key] -= n
    expected["entry_product_edges"] -= (
        overlaps["use_case_products"] + overlaps["consolidated_use_case_products"]
    )
    # The "parent_of" dependents merge identically (children of loser become children of survivor).
    # The loser row itself is deleted, so it doesn't contribute to product_aliases as a row.
    # We add ONE alias for the loser's canonical_name -> survivor, but only if it isn't already
    # present (which it might be — see NotebookLM 3219 already has "Google NotebookLM" alias).
    # The loser's canonical_name will be present as an alias under the survivor after the merge if
    # it is currently an alias of EITHER side (the loser's aliases get repointed to the survivor).
    existing_alias = conn.execute(
        "SELECT 1 FROM product_aliases WHERE product_id IN (?, ?) AND LOWER(alias_text) = LOWER(?)",
        (survivor, loser, lose_row[1]),
    ).fetchone() is not None
    expected_alias_addition = 0 if existing_alias else 1
    expected["product_aliases"] += expected_alias_addition

    print(f"\nMERGE: '{lose_row[1]}' ({loser}) → '{surv_row[1]}' ({survivor})")
    print(f"  pre-survivor: {pre_surv}")
    print(f"  pre-loser:    {pre_lose}")
    print(f"  expected post-survivor: {expected}")
    print(f"  loser canonical_name alias to add: "
          f"{'(already present, skip)' if existing_alias else lose_row[1]!r}")

    if not apply:
        return

    cur = conn.cursor()
    # Drop loser rows that already exist on the survivor side (counted above)
    # so the repoint UPDATEs can't hit the UNIQUE constraints.
    cur.execute(
        """DELETE FROM use_case_products
            WHERE product_id = ? AND use_case_id IN
                  (SELECT use_case_id FROM use_case_products WHERE product_id = ?)""",
        (loser, survivor),
    )
    cur.execute(
        """DELETE FROM consolidated_use_case_products
            WHERE product_id = ? AND consolidated_use_case_id IN
                  (SELECT consolidated_use_case_id FROM consolidated_use_case_products WHERE product_id = ?)""",
        (loser, survivor),
    )
    cur.execute(
        """DELETE FROM product_aliases
            WHERE product_id = ? AND alias_text IN
                  (SELECT alias_text FROM product_aliases WHERE product_id = ?)""",
        (loser, survivor),
    )
    cur.execute(
        """DELETE FROM fedramp_product_links
            WHERE inventory_product_id = ? AND fedramp_id IN
                  (SELECT fedramp_id FROM fedramp_product_links WHERE inventory_product_id = ?)""",
        (loser, survivor),
    )
    cur.execute("UPDATE product_aliases SET product_id = ? WHERE product_id = ?", (survivor, loser))
    cur.execute("UPDATE use_case_products SET product_id = ? WHERE product_id = ?", (survivor, loser))
    cur.execute("UPDATE consolidated_use_case_products SET product_id = ? WHERE product_id = ?", (survivor, loser))
    # entry_product_edges is a VIEW over use_case_products + consolidated_use_case_products; updating
    # the base tables above automatically updates it.
    cur.execute("UPDATE fedramp_product_links SET inventory_product_id = ? WHERE inventory_product_id = ?",
                (survivor, loser))
    cur.execute("UPDATE products SET parent_product_id = ? WHERE parent_product_id = ?", (survivor, loser))
    cur.execute("INSERT OR IGNORE INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
                (survivor, lose_row[1]))
    cur.execute("DELETE FROM products WHERE id = ?", (loser,))

    post_surv = _counts(conn, survivor)
    print(f"  post-survivor: {post_surv}")
    if post_surv != expected:
        raise SystemExit(f"  ASSERTION FAILED: expected {expected}, got {post_surv} — rolling back")
    print("  ok ✓")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually write changes (default: dry-run)")
    args = ap.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        if args.apply:
            conn.execute("BEGIN")
        for surv_name, lose_name in MERGES_BY_NAME:
            surv_row = conn.execute(
                "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)", (surv_name,)
            ).fetchone()
            lose_row = conn.execute(
                "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)", (lose_name,)
            ).fetchone()
            if surv_row is None and lose_row is None:
                print(f"  SKIP: neither {surv_name!r} nor {lose_name!r} exists")
                continue
            if lose_row is None:
                print(f"  SKIP: loser {lose_name!r} no longer exists (merge already applied?)")
                continue
            if surv_row is None:
                print(f"  SKIP: survivor {surv_name!r} not found")
                continue
            _merge_one(conn, surv_row[0], lose_row[0], apply=args.apply)
        if args.apply:
            conn.commit()
            print("\nCOMMITTED")
        else:
            print("\n(dry-run; pass --apply to write)")
    except Exception:
        if args.apply:
            conn.rollback()
            print("\nROLLED BACK")
        raise
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
