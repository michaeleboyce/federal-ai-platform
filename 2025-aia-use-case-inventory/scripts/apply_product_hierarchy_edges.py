"""Apply parent-child edges to products.parent_product_id from a CSV.

CSV columns: action, child_canonical_name, parent_canonical_name, confidence, reasoning

action='add'    -> set child.parent_product_id = parent.id (overwrites prior parent if any)
action='remove' -> clear child.parent_product_id, but only if it currently equals parent.id

Resolves names case-insensitively against products.canonical_name first,
then product_aliases.alias_text. Bails on cycles or self-parenting.
Reports max chain depth after applying so the dashboard's 5-hop CTE cap
isn't silently exceeded.

Usage:
    python3 scripts/apply_product_hierarchy_edges.py            # dry-run
    python3 scripts/apply_product_hierarchy_edges.py --apply
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "product_hierarchy_edges.csv"


def _resolve(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)", (name,)
    ).fetchone()
    if row:
        return row[0]
    row = conn.execute(
        "SELECT product_id FROM product_aliases WHERE LOWER(alias_text) = LOWER(?)", (name,)
    ).fetchone()
    return row[0] if row else None


def _ancestor_path(conn: sqlite3.Connection, pid: int) -> list[int]:
    """Walk parent_product_id upward from pid; return list including pid."""
    seen = []
    cur = pid
    while cur is not None and cur not in seen:
        seen.append(cur)
        row = conn.execute("SELECT parent_product_id FROM products WHERE id = ?", (cur,)).fetchone()
        cur = row[0] if row else None
    return seen


def _max_depth(conn: sqlite3.Connection) -> tuple[int, list[str]]:
    """Return max parent-chain depth and the longest chain (as canonical names)."""
    rows = conn.execute("SELECT id FROM products WHERE parent_product_id IS NULL").fetchall()
    roots = [r[0] for r in rows]
    best_depth, best_chain_ids = 0, []
    for root in roots:
        children = conn.execute(
            "SELECT id FROM products WHERE parent_product_id = ?", (root,)
        ).fetchall()
        for (cid,) in children:
            chain = _ancestor_path(conn, cid)
            if len(chain) > best_depth:
                best_depth, best_chain_ids = len(chain), chain[::-1]
    names = []
    for pid in best_chain_ids:
        n = conn.execute("SELECT canonical_name FROM products WHERE id = ?", (pid,)).fetchone()
        names.append(n[0] if n else f"<{pid}>")
    return best_depth, names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    rows_added, rows_removed, skipped = [], [], []

    with CSV_PATH.open() as f:
        reader = csv.DictReader(f)
        plan = list(reader)

    if args.apply:
        conn.execute("BEGIN")
    try:
        for row in plan:
            action = row["action"].strip().lower()
            child_name = row["child_canonical_name"].strip()
            parent_name = row["parent_canonical_name"].strip()
            child_id = _resolve(conn, child_name)
            parent_id = _resolve(conn, parent_name)

            if child_id is None:
                skipped.append((action, child_name, parent_name, "child not found"))
                continue
            if parent_id is None:
                skipped.append((action, child_name, parent_name, "parent not found"))
                continue
            if action == "add":
                if child_id == parent_id:
                    skipped.append((action, child_name, parent_name, "self-parenting"))
                    continue
                # Check the proposed parent isn't a descendant of the child (would create a cycle).
                anc_of_parent = _ancestor_path(conn, parent_id)
                if child_id in anc_of_parent:
                    skipped.append((action, child_name, parent_name, "cycle"))
                    continue
                current = conn.execute(
                    "SELECT parent_product_id FROM products WHERE id = ?", (child_id,)
                ).fetchone()[0]
                if current == parent_id:
                    skipped.append((action, child_name, parent_name, "already set"))
                    continue
                if args.apply:
                    conn.execute(
                        "UPDATE products SET parent_product_id = ? WHERE id = ?",
                        (parent_id, child_id),
                    )
                rows_added.append((child_name, parent_name, current, parent_id))
            elif action == "remove":
                current = conn.execute(
                    "SELECT parent_product_id FROM products WHERE id = ?", (child_id,)
                ).fetchone()[0]
                if current != parent_id:
                    skipped.append((action, child_name, parent_name, f"current parent is {current}, not {parent_id}"))
                    continue
                if args.apply:
                    conn.execute(
                        "UPDATE products SET parent_product_id = NULL WHERE id = ?", (child_id,)
                    )
                rows_removed.append((child_name, parent_name))
            else:
                skipped.append((action, child_name, parent_name, "unknown action"))

        if args.apply:
            conn.commit()
    except Exception:
        if args.apply:
            conn.rollback()
        raise

    print(f"plan: {len(plan)} rows")
    print(f"  added:   {len(rows_added)}")
    print(f"  removed: {len(rows_removed)}")
    print(f"  skipped: {len(skipped)}")
    if rows_added:
        print("\nADD:")
        for c, p, prev, new in rows_added:
            prev_label = f"(prev parent={prev})" if prev else "(no prev parent)"
            print(f"  {c} -> {p}  {prev_label}")
    if rows_removed:
        print("\nREMOVE:")
        for c, p in rows_removed:
            print(f"  {c} -> {p}")
    if skipped:
        print("\nSKIPPED:")
        for action, c, p, why in skipped:
            print(f"  [{action}] {c} -> {p}  ({why})")

    depth, chain = _max_depth(conn)
    print(f"\npost-state max parent-chain depth: {depth}  ({' -> '.join(chain)})")
    if depth > 5:
        print("WARNING: depth exceeds dashboard CTE cap of 5 hops; restructure!")

    total_edges = conn.execute(
        "SELECT COUNT(*) FROM products WHERE parent_product_id IS NOT NULL"
    ).fetchone()[0]
    print(f"total parent_product_id edges in products: {total_edges}")

    if not args.apply:
        print("\n(dry-run; pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
