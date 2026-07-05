"""Build input slices for the product_capability_2026_07 labeling pass.

One row per canonical product with >=1 entry_product_edges row (only these
can make an agency a "lead user" or satisfy the sleeping-services
"nothing similar deployed" test). Each row carries what a labeling agent
needs to assign capability categories: name, vendor, product_type, the
generative-AI flags already on the product, its parent, how widely it is
used, and up to three evidence snippets from linked use cases.

Rows are keyed by `canonical_name` (durable across rebuilds) — never
numeric ids. Slices are vendor-grouped so a labeler sees a vendor's
product family together: vendors are packed greedily into N batches
balanced by row count.

Writes `audit/retag/product_capability_2026_07/input_batch{1..N}.csv`
plus a combined `input.csv`.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_DIR = ROOT / "audit" / "retag" / "product_capability_2026_07"

COLUMNS = [
    "canonical_name",
    "vendor",
    "product_type",
    "is_generative_ai_hint",
    "is_frontier_llm_hint",
    "parent_product",
    "description",
    "edge_count",
    "agency_count",
    "sample_use_snippets",
]


def fetch_rows(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT p.canonical_name,
               COALESCE(p.vendor, '')            AS vendor,
               COALESCE(p.product_type, '')      AS product_type,
               COALESCE(p.is_generative_ai, '')  AS is_generative_ai_hint,
               COALESCE(p.is_frontier_llm, '')   AS is_frontier_llm_hint,
               COALESCE(pp.canonical_name, '')   AS parent_product,
               COALESCE(p.description, '')       AS description,
               COUNT(e.entry_id)                 AS edge_count,
               COUNT(DISTINCT e.agency_id)       AS agency_count
          FROM products p
          JOIN entry_product_edges e ON e.product_id = p.id
          LEFT JOIN products pp ON pp.id = p.parent_product_id
         GROUP BY p.id
         ORDER BY COALESCE(NULLIF(p.vendor, ''), p.canonical_name), p.canonical_name
        """
    ).fetchall()
    out = []
    for r in rows:
        d = dict(zip(COLUMNS[:-1], r))
        snippets = conn.execute(
            """
            SELECT e.evidence_text FROM entry_product_edges e
              JOIN products p ON p.id = e.product_id
             WHERE p.canonical_name = ?
               AND e.evidence_text IS NOT NULL AND e.evidence_text != ''
             LIMIT 3
            """,
            (d["canonical_name"],),
        ).fetchall()
        d["sample_use_snippets"] = " | ".join(
            s[0].replace("\n", " ")[:200] for s in snippets
        )
        out.append(d)
    if not out:
        raise SystemExit("No edged products found — wrong DB?")
    return out


def pack_batches(rows: list[dict], n_batches: int) -> list[list[dict]]:
    """Greedy bin-packing by vendor (fallback: own name), largest first."""
    by_vendor: dict[str, list[dict]] = {}
    for r in rows:
        by_vendor.setdefault(r["vendor"] or r["canonical_name"], []).append(r)
    batches: list[list[dict]] = [[] for _ in range(n_batches)]
    for _, vendor_rows in sorted(by_vendor.items(), key=lambda kv: -len(kv[1])):
        smallest = min(batches, key=len)
        smallest.extend(vendor_rows)
    return [b for b in batches if b]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--batches", type=int, default=5)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        rows = fetch_rows(conn)
    finally:
        conn.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def write(path: Path, rs: list[dict]) -> None:
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rs)

    write(OUT_DIR / "input.csv", rows)
    batches = pack_batches(rows, args.batches)
    for i, batch in enumerate(batches, start=1):
        write(OUT_DIR / f"input_batch{i}.csv", batch)
        print(f"batch{i}: {len(batch)} rows")
    print(f"total: {len(rows)} rows across {len(batches)} batches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
