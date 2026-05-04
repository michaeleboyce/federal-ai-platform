"""Find products with zero use_case_products links AND search every use
case's free-text fields for the product's canonical name + each of its
aliases. Reports candidates that should probably be linked but aren't,
sorted by hit count.

Search strategy: case-insensitive substring match against
COALESCE(use_case_name, system_name, vendor_name, problem_statement,
expected_benefits, system_outputs). For each product, try the canonical
name first, then each alias. A "hit" is a use case whose concatenated
text contains the alias as a substring with word boundaries when
possible (a bare 4+ char alias gets word-boundary checks; very short
or special-character aliases get plain substring).

Output: prints a report sorted by total hit count desc. Does NOT modify
the DB. Run results.csv at audit/unlinked_products_audit.csv for review.
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
OUT_CSV = ROOT / "audit" / "unlinked_products_audit.csv"

# Aliases shorter than this need a word-boundary match to avoid spurious
# substring matches (e.g., "Q" matching "Quality").
WORD_BOUNDARY_MIN_LEN = 4

# Aliases that are too generic to safely match even with boundaries.
# Adding new ones here is the easiest way to suppress false positives.
NOISE_ALIASES = {
    "ai", "ml", "api", "ux", "ui", "the", "and", "use", "tool",
}


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_text_for(conn, alias: str) -> list[dict]:
    """Return matching use cases for a single alias."""
    al = alias.strip()
    if not al or al.lower() in NOISE_ALIASES:
        return []
    if len(al) >= WORD_BOUNDARY_MIN_LEN and re.match(r"^[A-Za-z0-9 .&'-]+$", al):
        # Use SQLite REGEXP via Python — simpler to prefilter with LIKE then
        # confirm with regex word boundaries in Python.
        like = f"%{al.lower()}%"
        candidates = conn.execute(
            """
            SELECT u.id, u.use_case_name, a.abbreviation,
                   COALESCE(u.use_case_name,'') || ' | ' ||
                   COALESCE(u.system_name,'') || ' | ' ||
                   COALESCE(u.vendor_name,'') || ' | ' ||
                   COALESCE(u.problem_statement,'') || ' | ' ||
                   COALESCE(u.expected_benefits,'') || ' | ' ||
                   COALESCE(u.system_outputs,'') AS text
              FROM use_cases u
              JOIN agencies a ON a.id = u.agency_id
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
        # Word-boundary regex in Python
        pat = re.compile(r"\b" + re.escape(al) + r"\b", re.IGNORECASE)
        return [dict(r) for r in candidates if pat.search(r["text"])]
    # Short or special-char alias: plain substring (riskier, but caller
    # opted in by registering a short alias)
    like = f"%{al.lower()}%"
    rows = conn.execute(
        """
        SELECT u.id, u.use_case_name, a.abbreviation
          FROM use_cases u
          JOIN agencies a ON a.id = u.agency_id
         WHERE LOWER(
            COALESCE(u.use_case_name,'') || ' ' ||
            COALESCE(u.system_name,'') || ' ' ||
            COALESCE(u.vendor_name,'') || ' ' ||
            COALESCE(u.problem_statement,'')
         ) LIKE ?
        """,
        (like,),
    ).fetchall()
    return [dict(r) for r in rows]


def main() -> int:
    conn = _open()

    unlinked = conn.execute(
        """
        SELECT p.id, p.canonical_name, p.vendor, p.product_type, p.product_origin
          FROM products p
         WHERE p.id NOT IN (SELECT DISTINCT product_id FROM use_case_products)
         ORDER BY p.canonical_name
        """
    ).fetchall()

    aliases_by_pid: dict[int, list[str]] = defaultdict(list)
    for r in conn.execute("SELECT product_id, alias_text FROM product_aliases"):
        aliases_by_pid[r["product_id"]].append(r["alias_text"])

    rows_out: list[dict] = []
    for p in unlinked:
        pid = p["id"]
        terms_to_search = list(dict.fromkeys([p["canonical_name"]] + aliases_by_pid.get(pid, [])))
        all_hits: dict[int, dict] = {}
        hit_terms: set[str] = set()
        for term in terms_to_search:
            for hit in search_text_for(conn, term):
                all_hits[hit["id"]] = hit
                hit_terms.add(term)
        agency_set = {h["abbreviation"] for h in all_hits.values()}
        if all_hits:
            rows_out.append({
                "product_id": pid,
                "canonical_name": p["canonical_name"],
                "vendor": p["vendor"],
                "product_type": p["product_type"],
                "product_origin": p["product_origin"],
                "n_hits": len(all_hits),
                "n_agencies": len(agency_set),
                "agencies": "|".join(sorted(agency_set)),
                "search_terms_with_hits": "|".join(sorted(hit_terms)),
                "sample_use_case_ids": "|".join(str(h) for h in list(all_hits)[:5]),
                "sample_use_case_names": " | ".join(
                    h["use_case_name"][:60] for h in list(all_hits.values())[:3]
                ),
            })

    # Sort: most hits first, then by name
    rows_out.sort(key=lambda r: (-r["n_hits"], r["canonical_name"]))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out else [
            "product_id", "canonical_name", "vendor", "product_type",
            "product_origin", "n_hits", "n_agencies", "agencies",
            "search_terms_with_hits", "sample_use_case_ids",
            "sample_use_case_names",
        ])
        w.writeheader()
        w.writerows(rows_out)

    print(f"Total products with zero use_case_products links: {len(unlinked)}")
    print(f"Of those, found free-text matches for: {len(rows_out)}")
    print(f"Wrote: {OUT_CSV.relative_to(ROOT)}")
    print()
    print("Top candidates by hit count:")
    print(f"  {'pid':>5} {'name':<40} {'hits':>5} {'ag':>3}  agencies")
    for r in rows_out[:30]:
        print(f"  {r['product_id']:>5} {r['canonical_name'][:40]:<40} "
              f"{r['n_hits']:>5} {r['n_agencies']:>3}  {r['agencies']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
