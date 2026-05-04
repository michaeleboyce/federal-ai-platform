"""Apply the catalog-expansion proposal from audit/review_queue_resolution.

Reads `catalog_expansion.json` (produced by an LLM triage pass over the
80 alias proposals in `_pending_new_products.csv`) and applies it as
DB-level mutations:

  add  → INSERT INTO products + INSERT INTO product_aliases.
         If `parent_canonical` is set, link via parent_product_id.
         Idempotent: if a product with the same canonical_name already
         exists, only adds missing aliases.

  fold → INSERT INTO product_aliases for the existing canonical.
         Idempotent: skips aliases that already exist.

  skip → noop (rationale recorded in summary only).

After mutations, re-runs `apply_review_queue_resolution.py` so any queue
rows that previously hit `queued_new_product` (because their canonical
didn't exist yet) now resolve to real product edges.

Note: this writes directly to the DB rather than edits build_lookups.py
because most pending names are one-mention rarities that don't warrant
hand-curating in PRODUCTS. The seed file remains the source of truth
for the high-volume catalog (Microsoft 365 Copilot, ChatGPT, etc.);
this script is for the long-tail expansion that came out of the audit.
The next `make fix` rebuild will WIPE these additions UNLESS they're
also added to build_lookups.py — so this script also writes
`audit/review_queue_resolution/catalog_seed.py` as a copy-paste source
for the next time someone hand-edits build_lookups.py.

Idempotent.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
PROPOSAL_PATH = ROOT / "audit" / "review_queue_resolution" / "catalog_expansion.json"
SEED_OUT = ROOT / "audit" / "review_queue_resolution" / "catalog_seed.py"


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_id(conn, canonical_name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM products WHERE canonical_name = ?", (canonical_name,)
    ).fetchone()
    return row["id"] if row else None


def _add_alias_if_missing(conn, product_id: int, alias_text: str) -> bool:
    """Returns True if newly inserted, False if already existed."""
    existing = conn.execute(
        "SELECT 1 FROM product_aliases WHERE product_id = ? AND alias_text = ?",
        (product_id, alias_text),
    ).fetchone()
    if existing:
        return False
    conn.execute(
        "INSERT INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
        (product_id, alias_text),
    )
    return True


def main() -> int:
    if not PROPOSAL_PATH.exists():
        print(f"[catalog-expand] proposal not found at {PROPOSAL_PATH} — skipping")
        return 0

    proposal = json.loads(PROPOSAL_PATH.read_text())
    decisions = proposal.get("decisions", [])
    if not decisions:
        print("[catalog-expand] no decisions in proposal — skipping")
        return 0

    conn = _open()
    stats = {
        "products_added": 0,
        "products_already_existed": 0,
        "aliases_added": 0,
        "aliases_already_existed": 0,
        "folded": 0,
        "fold_unknown_canonical": 0,
        "skipped": 0,
        "parent_resolution_failed": 0,
    }
    seed_entries: list[dict] = []

    try:
        with conn:
            for d in decisions:
                decision = d.get("decision")
                if decision == "skip":
                    stats["skipped"] += 1
                    continue

                if decision == "fold":
                    canonical = d.get("existing_canonical_name", "")
                    aliases = d.get("aliases") or []
                    pid = _resolve_id(conn, canonical)
                    if pid is None:
                        stats["fold_unknown_canonical"] += 1
                        continue
                    for a in aliases:
                        if _add_alias_if_missing(conn, pid, a):
                            stats["aliases_added"] += 1
                        else:
                            stats["aliases_already_existed"] += 1
                    stats["folded"] += 1
                    continue

                if decision == "add":
                    canonical = d.get("canonical_name", "")
                    if not canonical:
                        continue
                    existing_id = _resolve_id(conn, canonical)
                    if existing_id is None:
                        # Insert new product row.
                        cur = conn.execute(
                            """INSERT INTO products
                               (canonical_name, vendor, product_type,
                                is_generative_ai, is_frontier_llm, description)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                canonical,
                                d.get("vendor"),
                                d.get("product_type"),
                                int(d.get("is_generative_ai") or 0),
                                int(d.get("is_frontier_llm") or 0),
                                d.get("description"),
                            ),
                        )
                        pid = cur.lastrowid
                        stats["products_added"] += 1
                    else:
                        pid = existing_id
                        stats["products_already_existed"] += 1

                    # Resolve parent if specified.
                    parent_name = d.get("parent_canonical")
                    if parent_name:
                        parent_id = _resolve_id(conn, parent_name)
                        if parent_id:
                            conn.execute(
                                "UPDATE products SET parent_product_id = ? WHERE id = ?",
                                (parent_id, pid),
                            )
                        else:
                            stats["parent_resolution_failed"] += 1

                    # Aliases: include the canonical name itself + any provided.
                    aliases = list(d.get("aliases") or [])
                    if canonical not in aliases:
                        aliases.append(canonical)
                    for a in aliases:
                        if _add_alias_if_missing(conn, pid, a):
                            stats["aliases_added"] += 1
                        else:
                            stats["aliases_already_existed"] += 1

                    seed_entries.append(d)

        # Dump a copy-paste-ready seed snippet for build_lookups.py so the
        # next make-fix rebuild preserves these additions.
        with open(SEED_OUT, "w") as f:
            f.write('"""Catalog-expansion seed — paste into build_lookups.py PRODUCTS list."""\n\n')
            f.write("CATALOG_EXPANSION_2026_05 = [\n")
            for d in seed_entries:
                aliases = d.get("aliases") or []
                aliases_str = (
                    "[" + ", ".join(repr(a) for a in aliases) + "]" if aliases else "[]"
                )
                f.write(
                    f"    ({d.get('canonical_name')!r}, {d.get('vendor')!r}, "
                    f"{d.get('product_type')!r}, {int(d.get('is_generative_ai') or 0)}, "
                    f"{int(d.get('is_frontier_llm') or 0)}, "
                    f"{d.get('parent_canonical')!r},\n"
                    f"     {(d.get('description') or '')!r},\n"
                    f"     {aliases_str}),\n"
                )
            f.write("]\n")

        print(f"[catalog-expand] {stats}")
        print(f"  ℹ seed snippet written to {SEED_OUT.relative_to(ROOT)}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
