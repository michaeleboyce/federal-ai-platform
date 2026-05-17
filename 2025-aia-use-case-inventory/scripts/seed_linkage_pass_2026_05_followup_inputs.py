"""Foundation script for the May 2026 linkage-pass FOLLOW-UP audit.

Reads `data/federal_ai_inventory_2025.db` read-only and writes 4 CSVs into
`audit/linkage_pass_2026-05-followup/inputs/`:

  - ws1_va_dark_individual.csv       (~323 rows — VA dark-unlinked use_cases)
  - ws1_va_dark_consolidated.csv     (~30-40 rows — VA dark-unlinked consolidated)
  - ws2_hierarchy_gap_candidates.csv (~60-100 rows — parent-less products in major vendor families)
  - ws3_alias_coverage_candidates.csv (~30 rows — thinly-aliased parents + sample unlinked mentions)

See `audit/linkage_pass_2026-05-followup/CHARTER.md` for the decision rubric.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT = ROOT / "audit" / "linkage_pass_2026-05-followup" / "inputs"

GENERIC_VENDORS = {
    "", "n/a", "na", "none", "tbd", "unknown", "unkown", "various",
    "multiple", "in-house", "internal", "ai model provider",
    "ai service provider", "vendor proprietary", "open source",
    "open source development", "redacted",
    "redacted for cybersecurity purposes",
}

# Vendor families WS2 sweeps for missing umbrella / sub-product parenting.
TARGET_VENDOR_FAMILIES = [
    "Microsoft", "Google", "Amazon", "Amazon Web Services", "AWS",
    "Adobe", "IBM", "Palantir", "Cisco", "Oracle", "ServiceNow",
    "Salesforce", "LexisNexis", "Thomson Reuters",
]


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _is_generic(v: str | None) -> bool:
    return _norm(v) in GENERIC_VENDORS


def _has_word_boundary_match(haystack: str, alias: str) -> bool:
    """Mirrors `product_resolution.extract_products` boundary logic."""
    if not haystack or not alias:
        return False
    idx = 0
    while True:
        pos = haystack.find(alias, idx)
        if pos < 0:
            return False
        before_ok = pos == 0 or not haystack[pos - 1].isalnum()
        end = pos + len(alias)
        after_ok = end == len(haystack) or not haystack[end].isalnum()
        if before_ok and after_ok:
            return True
        idx = pos + 1


def _catalog_vendor_strings(conn: sqlite3.Connection) -> set[str]:
    return {
        _norm(r[0])
        for r in conn.execute(
            "SELECT DISTINCT vendor FROM products WHERE vendor IS NOT NULL AND vendor <> ''"
        )
        if _norm(r[0])
    }


def _mentions_catalog_vendor(text_fields: list[str | None], vendors: set[str]) -> bool:
    haystack = " ".join((t or "").lower() for t in text_fields)
    return any(len(v) >= 4 and _has_word_boundary_match(haystack, v) for v in vendors)


def _write_csv(path: Path, header: list[str], rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
    return len(rows)


def write_ws1_individual(conn: sqlite3.Connection, vendors: set[str]) -> int:
    """VA, vendor blank/generic, no catalog vendor mention, no edge."""
    rows = conn.execute(
        """
        SELECT uc.id, uc.use_case_name, uc.vendor_name, uc.system_name,
               uc.development_type, uc.ai_classification,
               uc.problem_statement, uc.expected_benefits
          FROM use_cases uc
          JOIN agencies a ON a.id = uc.agency_id
         WHERE a.abbreviation = 'VA'
           AND NOT EXISTS (SELECT 1 FROM use_case_products ucp WHERE ucp.use_case_id = uc.id)
        ORDER BY uc.id
        """
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        uc_id, name, vendor, system, dev, ai_class, problem, benefits = r
        if not _is_generic(vendor):
            continue  # already in slice A of the prior pass
        if _mentions_catalog_vendor([name, system], vendors):
            continue  # already in slice B of the prior pass
        out.append({
            "use_case_id": uc_id,
            "agency": "VA",
            "use_case_name": name,
            "vendor_name": vendor or "",
            "system_name": system or "",
            "development_type": dev or "",
            "ai_classification": ai_class or "",
            "problem_statement": (problem or "").replace("\n", " ").strip(),
            "expected_benefits": (benefits or "").replace("\n", " ").strip(),
            "pre_classification": "va_dark",
        })
    header = [
        "use_case_id", "agency", "use_case_name", "vendor_name", "system_name",
        "development_type", "ai_classification", "problem_statement",
        "expected_benefits", "pre_classification",
    ]
    return _write_csv(OUT / "ws1_va_dark_individual.csv", header, out)


def write_ws1_consolidated(conn: sqlite3.Connection) -> int:
    """VA consolidated entries with no edge."""
    rows = conn.execute(
        """
        SELECT c.id, c.ai_use_case, c.commercial_product,
               c.commercial_examples, c.agency_uses
          FROM consolidated_use_cases c
          JOIN agencies a ON a.id = c.agency_id
         WHERE a.abbreviation = 'VA'
           AND NOT EXISTS (
             SELECT 1 FROM consolidated_use_case_products cucp
              WHERE cucp.consolidated_use_case_id = c.id
           )
        ORDER BY c.id
        """
    ).fetchall()
    out: list[dict] = []
    for cu_id, name, product, examples, uses in rows:
        out.append({
            "consolidated_use_case_id": cu_id,
            "agency": "VA",
            "ai_use_case": name,
            "commercial_product": product or "",
            "agency_uses": (uses or "").replace("\n", " ").strip(),
            "commercial_examples_snippet": (examples or "").replace("\n", " ").strip()[:200],
            "pre_classification": "va_dark_consolidated",
        })
    header = [
        "consolidated_use_case_id", "agency", "ai_use_case",
        "commercial_product", "agency_uses",
        "commercial_examples_snippet", "pre_classification",
    ]
    return _write_csv(OUT / "ws1_va_dark_consolidated.csv", header, out)


def write_ws2_hierarchy(conn: sqlite3.Connection) -> int:
    """Parent-less products in target vendor families."""
    placeholders = ",".join("?" for _ in TARGET_VENDOR_FAMILIES)
    rows = conn.execute(
        f"""
        SELECT p.id, p.canonical_name, p.vendor, p.product_type,
               p.is_generative_ai, p.is_frontier_llm,
               GROUP_CONCAT(pa.alias_text, '|') AS aliases,
               (SELECT COUNT(*) FROM use_case_products WHERE product_id = p.id)
                 + (SELECT COUNT(*) FROM consolidated_use_case_products WHERE product_id = p.id)
                 AS edge_count
          FROM products p
          LEFT JOIN product_aliases pa ON pa.product_id = p.id
         WHERE p.parent_product_id IS NULL
           AND p.vendor IN ({placeholders})
         GROUP BY p.id
         ORDER BY p.vendor COLLATE NOCASE, p.canonical_name COLLATE NOCASE
        """,
        TARGET_VENDOR_FAMILIES,
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        pid, name, vendor, ptype, genai, frontier, aliases, edges = r
        out.append({
            "product_id": pid,
            "canonical_name": name,
            "vendor": vendor or "",
            "product_type": ptype or "",
            "is_generative_ai": genai or 0,
            "is_frontier_llm": frontier or 0,
            "aliases": aliases or "",
            "edge_count": edges or 0,
        })
    header = [
        "product_id", "canonical_name", "vendor", "product_type",
        "is_generative_ai", "is_frontier_llm", "aliases", "edge_count",
    ]
    return _write_csv(OUT / "ws2_hierarchy_gap_candidates.csv", header, out)


def write_ws3_aliases(conn: sqlite3.Connection) -> int:
    """Top 30 catalog products by sibling count whose alias_count ≤ 2,
    plus up to 5 sample unlinked use_cases where the bare product name
    appears in narrative but no edge exists.
    """
    # First, find candidate parent products: thinly aliased, popular vendor
    cands = conn.execute(
        """
        WITH alias_counts AS (
            SELECT product_id, COUNT(*) AS n FROM product_aliases GROUP BY product_id
        ),
        siblings AS (
            SELECT vendor, COUNT(*) AS sib FROM products
             WHERE vendor IS NOT NULL AND vendor <> ''
             GROUP BY vendor
        )
        SELECT p.id, p.canonical_name, p.vendor, p.product_type,
               COALESCE(ac.n, 0) AS alias_count,
               s.sib AS vendor_sibling_count,
               (SELECT COUNT(*) FROM use_case_products WHERE product_id = p.id)
                 + (SELECT COUNT(*) FROM consolidated_use_case_products WHERE product_id = p.id)
                 AS edge_count
          FROM products p
          LEFT JOIN alias_counts ac ON ac.product_id = p.id
          LEFT JOIN siblings s ON s.vendor = p.vendor
         WHERE COALESCE(ac.n, 0) <= 2
           AND s.sib >= 5
         ORDER BY s.sib DESC, edge_count DESC
         LIMIT 30
        """
    ).fetchall()

    out: list[dict] = []
    for pid, name, vendor, ptype, alias_count, sib_count, edges in cands:
        # Find up to 5 unlinked use_cases that mention this product's name
        # in their narrative — gives the agent concrete evidence to reason
        # about alias safety.
        samples = []
        sample_rows = conn.execute(
            """
            SELECT uc.id, a.abbreviation, uc.use_case_name,
                   SUBSTR(COALESCE(uc.problem_statement, ''), 1, 200) AS snippet
              FROM use_cases uc
              JOIN agencies a ON a.id = uc.agency_id
             WHERE NOT EXISTS (
                 SELECT 1 FROM use_case_products ucp WHERE ucp.use_case_id = uc.id
             )
               AND (
                   LOWER(uc.use_case_name)       LIKE '%' || LOWER(?) || '%'
                OR LOWER(uc.system_name)         LIKE '%' || LOWER(?) || '%'
                OR LOWER(uc.problem_statement)   LIKE '%' || LOWER(?) || '%'
                OR LOWER(uc.expected_benefits)   LIKE '%' || LOWER(?) || '%'
               )
             LIMIT 5
            """,
            (name, name, name, name),
        ).fetchall()
        for s in sample_rows:
            samples.append(f"uc{s[0]} ({s[1]}): {s[2]}")
        # Existing aliases for this product
        aliases = [
            r[0]
            for r in conn.execute(
                "SELECT alias_text FROM product_aliases WHERE product_id = ? ORDER BY LENGTH(alias_text)",
                (pid,),
            )
        ]
        out.append({
            "product_id": pid,
            "canonical_name": name,
            "vendor": vendor or "",
            "product_type": ptype or "",
            "alias_count": alias_count,
            "vendor_sibling_count": sib_count,
            "edge_count": edges or 0,
            "existing_aliases": " | ".join(aliases),
            "sample_unlinked_mentions": " || ".join(samples),
        })
    header = [
        "product_id", "canonical_name", "vendor", "product_type",
        "alias_count", "vendor_sibling_count", "edge_count",
        "existing_aliases", "sample_unlinked_mentions",
    ]
    return _write_csv(OUT / "ws3_alias_coverage_candidates.csv", header, out)


def main() -> int:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        vendors = _catalog_vendor_strings(conn)
        counts = {
            "ws1_va_dark_individual": write_ws1_individual(conn, vendors),
            "ws1_va_dark_consolidated": write_ws1_consolidated(conn),
            "ws2_hierarchy_gap_candidates": write_ws2_hierarchy(conn),
            "ws3_alias_coverage_candidates": write_ws3_aliases(conn),
        }
    finally:
        conn.close()
    print("Wrote inputs to", OUT)
    for k, v in counts.items():
        print(f"  {k:<40s} {v:>4d} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
