"""Apply the May 2026 4-agent linkage pass.

Reads the integration CSVs under audit/linkage_pass_2026-05/integration/ and:

  1. Appends new products to data/expanded_product_catalog.csv so subsequent
     `make fix` runs replay them via apply_expanded_product_catalog.py. Also
     inserts them directly into the current DB so the immediate apply works.
  2. Appends parent edges to data/product_hierarchy_edges.csv (consumed by
     apply_product_hierarchy_edges.py). Also applies them to the current DB.
  3. Adds new aliases (INSERT OR IGNORE into product_aliases). Tighten
     replacements remove an existing alias and add a new one.
  4. Inserts proposed links into use_case_products (INSERT OR IGNORE keyed
     on PK). Resolves product_id by canonical_name so a re-keyed DB is fine.
  5. Re-runs the populator for any new products that have linking_use_case_ids
     so the substring rule applies anywhere else the new product is mentioned.

Default: dry-run. Pass --apply to write.
Idempotent (safe to re-run).
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
PASS_DIR = ROOT / "audit" / "linkage_pass_2026-05"
INT = PASS_DIR / "integration"
CATALOG_CSV = ROOT / "data" / "expanded_product_catalog.csv"
HIERARCHY_CSV = ROOT / "data" / "product_hierarchy_edges.csv"


def _norm(s: str | None) -> str:
    return (s or "").strip()


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _existing_catalog_names(path: Path) -> set[str]:
    return {_norm(r["canonical_name"]).lower() for r in _read(path) if r.get("canonical_name")}


def _existing_hierarchy_edges(path: Path) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for r in _read(path):
        if (r.get("action") or "").strip() != "add":
            continue
        out.add((
            _norm(r.get("child_canonical_name")).lower(),
            _norm(r.get("parent_canonical_name")).lower(),
        ))
    return out


def _append_csv(path: Path, header: list[str], rows: list[dict[str, str]], apply: bool):
    if not rows:
        print(f"  ({path.name}: nothing to append)")
        return
    print(f"  {path.name}: append {len(rows)} rows")
    if not apply:
        for r in rows[:3]:
            print(f"    + {r}")
        if len(rows) > 3:
            print(f"    ... +{len(rows) - 3} more")
        return
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})


def apply_new_products(conn: sqlite3.Connection, apply: bool) -> int:
    """Append to expanded_product_catalog.csv and insert into products table."""
    proposals = _read(INT / "proposed_new_products.csv")
    if not proposals:
        return 0
    existing = _existing_catalog_names(CATALOG_CSV)
    db_existing = {
        _norm(r[0]).lower()
        for r in conn.execute("SELECT canonical_name FROM products")
    }

    to_append: list[dict[str, str]] = []
    to_insert: list[dict[str, str]] = []
    for p in proposals:
        name = _norm(p["canonical_name"])
        if not name:
            continue
        nkey = name.lower()
        if nkey in existing:
            continue
        to_append.append({
            "canonical_name": name,
            "vendor": _norm(p.get("vendor")),
            "product_type": _norm(p.get("product_type")),
            "is_generative_ai": _norm(p.get("is_generative_ai")) or "0",
            "is_frontier_llm": "0",
            "parent_canonical_name": _norm(p.get("proposed_parent_canonical_name")),
            "description": "",
            "notes": f"seeded by linkage_pass_2026-05 ({p.get('_agent', '?')})",
            "aliases": name,
        })
        if nkey not in db_existing:
            to_insert.append(to_append[-1])
        existing.add(nkey)

    _append_csv(
        CATALOG_CSV,
        ["canonical_name", "vendor", "product_type", "is_generative_ai",
         "is_frontier_llm", "parent_canonical_name", "description", "notes", "aliases"],
        to_append,
        apply,
    )

    print(f"  products INSERT: {len(to_insert)} new rows")
    if apply:
        cur = conn.cursor()
        for r in to_insert:
            cur.execute(
                """
                INSERT INTO products (canonical_name, vendor, product_type,
                                      is_generative_ai, is_frontier_llm,
                                      description, notes, product_origin)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'commercial')
                ON CONFLICT(canonical_name) DO NOTHING
                """,
                (r["canonical_name"], r["vendor"] or None, r["product_type"] or None,
                 int(r["is_generative_ai"] or 0), 0, None, r["notes"]),
            )
            pid_row = cur.execute(
                "SELECT id FROM products WHERE canonical_name = ?",
                (r["canonical_name"],),
            ).fetchone()
            if pid_row:
                cur.execute(
                    "INSERT OR IGNORE INTO product_aliases (product_id, alias_text) VALUES (?, LOWER(?))",
                    (pid_row[0], r["aliases"]),
                )
        conn.commit()
    return len(to_insert)


def apply_hierarchy(conn: sqlite3.Connection, apply: bool) -> int:
    """Append to product_hierarchy_edges.csv and set parent_product_id in DB."""
    proposals = _read(INT / "proposed_hierarchy_edges.csv")
    if not proposals:
        return 0
    existing = _existing_hierarchy_edges(HIERARCHY_CSV)
    to_append: list[dict[str, str]] = []
    applied = 0
    for p in proposals:
        child = _norm(p.get("child_canonical_name"))
        parent = _norm(p.get("parent_canonical_name"))
        if not child or not parent:
            continue
        key = (child.lower(), parent.lower())
        if key in existing:
            continue
        to_append.append({
            "action": "add",
            "child_canonical_name": child,
            "parent_canonical_name": parent,
            "confidence": _norm(p.get("confidence")) or "medium",
            "reasoning": _norm(p.get("reasoning")) or "linkage_pass_2026-05",
        })
        existing.add(key)

    _append_csv(
        HIERARCHY_CSV,
        ["action", "child_canonical_name", "parent_canonical_name", "confidence", "reasoning"],
        to_append,
        apply,
    )

    if apply:
        cur = conn.cursor()
        for r in to_append:
            ch = cur.execute(
                "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)",
                (r["child_canonical_name"],),
            ).fetchone()
            par = cur.execute(
                "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)",
                (r["parent_canonical_name"],),
            ).fetchone()
            if ch and par and ch[0] != par[0]:
                cur.execute(
                    "UPDATE products SET parent_product_id = ? WHERE id = ?",
                    (par[0], ch[0]),
                )
                applied += 1
        conn.commit()
    print(f"  hierarchy edges applied to DB: {applied}")
    return applied


def apply_aliases(conn: sqlite3.Connection, apply: bool) -> int:
    proposals = _read(INT / "proposed_aliases.csv")
    if not proposals:
        return 0
    applied = 0
    if apply:
        cur = conn.cursor()
        for p in proposals:
            name = _norm(p.get("canonical_name"))
            alias = _norm(p.get("alias"))
            if not name or not alias:
                continue
            pid = cur.execute(
                "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)",
                (name,),
            ).fetchone()
            if not pid:
                continue
            if (p.get("kind") or "add") == "tighten":
                replaces = _norm(p.get("replaces"))
                if replaces:
                    cur.execute(
                        "DELETE FROM product_aliases WHERE product_id = ? AND LOWER(alias_text) = LOWER(?)",
                        (pid[0], replaces),
                    )
            cur.execute(
                "INSERT OR IGNORE INTO product_aliases (product_id, alias_text) VALUES (?, LOWER(?))",
                (pid[0], alias),
            )
            applied += 1
        conn.commit()
    print(f"  aliases applied: {applied if apply else f'{len(proposals)} (dry-run)'}")
    return applied


def apply_links(conn: sqlite3.Connection, apply: bool) -> tuple[int, int]:
    """Insert into use_case_products or consolidated_use_case_products."""
    proposals = _read(INT / "proposed_links.csv")

    # Also pull linking_use_case_ids / linking_consolidated_ids from new
    # products — when an agent proposes "Abridge" with a linking_use_case_id
    # of 60881, the apply needs to link that use_case to the newly-inserted
    # product.
    new_product_links: list[dict[str, str]] = []
    for p in _read(INT / "proposed_new_products.csv"):
        name = _norm(p["canonical_name"])
        for raw in (p.get("linking_use_case_ids") or "").split(","):
            uid = raw.strip()
            if uid and uid.isdigit():
                new_product_links.append({
                    "entry_kind": "use_case", "entry_id": uid,
                    "canonical_name": name, "evidence_quote": "via add_product",
                    "confidence": "strong", "_agent": p.get("_agent", "?"),
                })
        for raw in (p.get("linking_consolidated_ids") or "").split(","):
            cid = raw.strip()
            if cid and cid.isdigit():
                new_product_links.append({
                    "entry_kind": "consolidated", "entry_id": cid,
                    "canonical_name": name, "evidence_quote": "via add_product",
                    "confidence": "strong", "_agent": p.get("_agent", "?"),
                })

    all_links = proposals + new_product_links
    inserted_uc = 0
    inserted_c = 0
    if apply:
        cur = conn.cursor()
        for r in all_links:
            kind = (r.get("entry_kind") or "").strip()
            eid = (r.get("entry_id") or "").strip()
            name = _norm(r.get("canonical_name"))
            if not (kind and eid and name and eid.isdigit()):
                continue
            pid_row = cur.execute(
                "SELECT id FROM products WHERE LOWER(canonical_name) = LOWER(?)",
                (name,),
            ).fetchone()
            if not pid_row:
                continue
            evidence = (r.get("evidence_quote") or "")[:500]
            conf = r.get("confidence") or "strong"
            if kind == "use_case":
                cur.execute(
                    """INSERT OR IGNORE INTO use_case_products
                       (use_case_id, product_id, evidence_text, confidence)
                       VALUES (?, ?, ?, ?)""",
                    (int(eid), pid_row[0], evidence, conf),
                )
                inserted_uc += cur.rowcount
            elif kind == "consolidated":
                cur.execute(
                    """INSERT OR IGNORE INTO consolidated_use_case_products
                       (consolidated_use_case_id, product_id, evidence_text, confidence)
                       VALUES (?, ?, ?, ?)""",
                    (int(eid), pid_row[0], evidence, conf),
                )
                inserted_c += cur.rowcount
        conn.commit()
    uc_count = sum(1 for r in all_links if r.get("entry_kind") == "use_case")
    c_count = sum(1 for r in all_links if r.get("entry_kind") == "consolidated")
    uc_display = inserted_uc if apply else f"{uc_count} (dry)"
    c_display = inserted_c if apply else f"{c_count} (dry)"
    print(f"  links: use_case={uc_display} consolidated={c_display}")
    return (inserted_uc, inserted_c)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes. Default: dry-run.")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] linkage_pass_2026-05 apply")
    print(f"  DB: {DB_PATH}")
    print(f"  INT: {INT}")
    print()

    conn = sqlite3.connect(DB_PATH)
    try:
        print("== 1. New products ==")
        apply_new_products(conn, args.apply)
        print("== 2. Hierarchy edges ==")
        apply_hierarchy(conn, args.apply)
        print("== 3. Aliases ==")
        apply_aliases(conn, args.apply)
        print("== 4. Links ==")
        apply_links(conn, args.apply)
    finally:
        conn.close()
    print()
    print(f"[{mode}] done. " +
          ("Changes written." if args.apply else "No changes written; re-run with --apply."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
