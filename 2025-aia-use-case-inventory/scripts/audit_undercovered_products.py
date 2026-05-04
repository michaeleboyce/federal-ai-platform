"""For products that DO have use_case_products links, check whether free-text
searching their canonical name + aliases turns up additional use cases that
aren't currently linked.

A "gap" is a use case where the product's name/alias appears in the narrative
but the (use_case_id, product_id) pair isn't in use_case_products. Big gaps
suggest alias coverage is incomplete or the populate step missed cases.

Output: audit/undercovered_products_audit.csv plus stdout report.

Skips products with origin='agency_internal_platform' (already audited
separately in audit_unlinked_products.py).
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_CSV = ROOT / "audit" / "undercovered_products_audit.csv"

WORD_BOUNDARY_MIN_LEN = 4
NOISE_ALIASES = {"ai", "ml", "api", "ux", "ui", "the", "and", "use", "tool", "ide"}


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_text_for(conn, alias: str) -> set[int]:
    """Return set of use_case_ids whose narrative contains alias (with word
    boundaries when feasible)."""
    al = alias.strip()
    if not al or al.lower() in NOISE_ALIASES:
        return set()
    if len(al) >= WORD_BOUNDARY_MIN_LEN and re.match(r"^[A-Za-z0-9 .&'-]+$", al):
        like = f"%{al.lower()}%"
        rows = conn.execute(
            """
            SELECT u.id,
                   COALESCE(u.use_case_name,'') || ' ' ||
                   COALESCE(u.system_name,'') || ' ' ||
                   COALESCE(u.vendor_name,'') || ' ' ||
                   COALESCE(u.problem_statement,'') || ' ' ||
                   COALESCE(u.expected_benefits,'') || ' ' ||
                   COALESCE(u.system_outputs,'') AS text
              FROM use_cases u
             WHERE LOWER(
                COALESCE(u.use_case_name,'') || ' ' ||
                COALESCE(u.system_name,'') || ' ' ||
                COALESCE(u.vendor_name,'') || ' ' ||
                COALESCE(u.problem_statement,'') || ' ' ||
                COALESCE(u.expected_benefits,'') || ' ' ||
                COALESCE(u.system_outputs,'')
             ) LIKE ?
            """,
            (like,),
        ).fetchall()
        pat = re.compile(r"\b" + re.escape(al) + r"\b", re.IGNORECASE)
        return {r["id"] for r in rows if pat.search(r["text"])}
    like = f"%{al.lower()}%"
    rows = conn.execute(
        """
        SELECT u.id FROM use_cases u
         WHERE LOWER(
            COALESCE(u.use_case_name,'') || ' ' ||
            COALESCE(u.system_name,'') || ' ' ||
            COALESCE(u.vendor_name,'') || ' ' ||
            COALESCE(u.problem_statement,'')
         ) LIKE ?
        """,
        (like,),
    ).fetchall()
    return {r["id"] for r in rows}


def main() -> int:
    conn = _open()

    linked_products = conn.execute(
        """
        SELECT p.id, p.canonical_name, p.vendor, p.product_type, p.product_origin,
               (SELECT COUNT(*) FROM use_case_products WHERE product_id = p.id) AS n_linked
          FROM products p
         WHERE p.id IN (SELECT DISTINCT product_id FROM use_case_products)
        """
    ).fetchall()

    aliases_by_pid: dict[int, list[str]] = defaultdict(list)
    for r in conn.execute("SELECT product_id, alias_text FROM product_aliases"):
        aliases_by_pid[r["product_id"]].append(r["alias_text"])

    rows_out: list[dict] = []
    for p in linked_products:
        pid = p["id"]
        currently_linked = {r["use_case_id"] for r in conn.execute(
            "SELECT use_case_id FROM use_case_products WHERE product_id = ?", (pid,)
        )}
        terms = list(dict.fromkeys([p["canonical_name"]] + aliases_by_pid.get(pid, [])))
        all_text_hits: set[int] = set()
        for term in terms:
            all_text_hits.update(search_text_for(conn, term))
        # Use cases that appear in text but aren't linked
        gap = all_text_hits - currently_linked
        if not gap:
            continue
        # Sample a few use cases for inspection
        sample_rows = conn.execute(
            f"""
            SELECT u.id, a.abbreviation, u.use_case_name
              FROM use_cases u JOIN agencies a ON a.id = u.agency_id
             WHERE u.id IN ({",".join("?" * min(len(gap), 5))})
            """,
            tuple(list(gap)[:5]),
        ).fetchall()
        gap_agencies = {r["abbreviation"] for r in conn.execute(
            f"""
            SELECT DISTINCT a.abbreviation
              FROM use_cases u JOIN agencies a ON a.id = u.agency_id
             WHERE u.id IN ({",".join("?" * len(gap))})
            """,
            tuple(gap),
        )}
        rows_out.append({
            "product_id": pid,
            "canonical_name": p["canonical_name"],
            "vendor": p["vendor"],
            "product_origin": p["product_origin"] or "",
            "n_currently_linked": p["n_linked"],
            "n_text_matches": len(all_text_hits),
            "n_gap": len(gap),
            "gap_agencies": "|".join(sorted(gap_agencies)),
            "sample_gap_uc_ids": "|".join(str(r["id"]) for r in sample_rows),
            "sample_gap_use_case_names": " | ".join(r["use_case_name"][:50] for r in sample_rows),
        })

    rows_out.sort(key=lambda r: -r["n_gap"])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out else [])
        w.writeheader()
        w.writerows(rows_out)

    print(f"Linked products audited: {len(linked_products)}")
    print(f"Products with potential gaps: {len(rows_out)}")
    print(f"Wrote: {OUT_CSV.relative_to(ROOT)}")
    print()
    print("Top 30 gaps (n_gap = currently-unlinked use cases that mention this product):")
    print(f"  {'pid':>5} {'name':<35} {'linked':>7} {'text':>5} {'gap':>5}  agencies")
    for r in rows_out[:30]:
        print(f"  {r['product_id']:>5} {r['canonical_name'][:35]:<35} "
              f"{r['n_currently_linked']:>7} {r['n_text_matches']:>5} {r['n_gap']:>5}  {r['gap_agencies']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
