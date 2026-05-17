"""Foundation script for the May 2026 linkage-pass audit.

Reads `data/federal_ai_inventory_2025.db` (read-only) and writes 5 CSVs into
`audit/linkage_pass_2026-05/inputs/`:

  - slice_a_named_vendor_individual.csv     (~279 rows)
  - slice_b_mention_only_individual.csv     (~91 rows)
  - slice_b_named_consolidated.csv          (~53 rows)
  - slice_c_dark_sample.csv                 (200 rows, seeded random)
  - existing_catalog_snapshot.csv           (every product + alias list + parent)

The four labeling agents read these CSVs and emit recommendations.json
under their own subdirectory. See `audit/linkage_pass_2026-05/CHARTER.md`.
"""
from __future__ import annotations

import csv
import random
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT = ROOT / "audit" / "linkage_pass_2026-05" / "inputs"

RANDOM_SEED = 20260516

# Vendor strings that signal "we don't know which product" — used to
# segment named-vendor vs mention-only vs dark.
GENERIC_VENDORS = {
    "", "n/a", "na", "none", "tbd", "unknown", "unkown", "various",
    "multiple", "in-house", "internal", "ai model provider",
    "ai service provider", "vendor proprietary", "open source",
    "open source development", "redacted", "redacted for cybersecurity purposes",
}


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _is_generic(vendor: str | None) -> bool:
    return _norm(vendor) in GENERIC_VENDORS


def _is_dark_text(value: str | None) -> bool:
    n = _norm(value)
    return (not n) or n in GENERIC_VENDORS or n.startswith("redacted")


def _catalog_vendor_strings(conn: sqlite3.Connection) -> set[str]:
    """Set of lowercased vendor strings from the catalog. Used to detect
    mention-only rows (vendor blank but a catalog vendor appears in other
    fields)."""
    return {
        _norm(row[0])
        for row in conn.execute("SELECT DISTINCT vendor FROM products WHERE vendor IS NOT NULL AND vendor <> ''")
        if _norm(row[0])
    }


def _mentions_catalog_vendor(
    text_fields: list[str | None],
    catalog_vendors: set[str],
) -> str | None:
    """Return the longest matching catalog vendor string found in any of
    the text fields, or None. Case-insensitive substring."""
    haystack = " ".join((t or "").lower() for t in text_fields)
    hits = [v for v in catalog_vendors if len(v) >= 4 and v in haystack]
    if not hits:
        return None
    return max(hits, key=len)


def _has_word_boundary_match(haystack: str, alias: str) -> bool:
    """Same boundary semantics as production linker
    (`product_resolution.extract_products`). Returns True iff `alias`
    appears as a whole token in `haystack`."""
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


def _candidate_products(
    conn: sqlite3.Connection,
    text_fields: list[str | None],
    limit: int = 5,
) -> str:
    """Longest-token-match the text against `product_aliases.alias_text`
    and return up to `limit` candidate canonical_names as a `|`-joined
    string. Mirrors `product_resolution.extract_products` exactly — both
    the longest-first ordering AND the word-boundary check — so the
    candidates surfaced here match what the production linker would
    consider. Without the boundary check, short aliases like `meta` or
    `descript` produced ~30 spurious candidates per pass (matches inside
    `metadata`/`descriptors`/etc.) that the labeling agent then had to
    triage as false_positive."""
    haystack = " ".join((t or "").lower() for t in text_fields)
    if not haystack.strip():
        return ""
    rows = conn.execute(
        """
        SELECT p.canonical_name, pa.alias_text
          FROM product_aliases pa
          JOIN products p ON p.id = pa.product_id
         WHERE LENGTH(pa.alias_text) >= 4
         ORDER BY LENGTH(pa.alias_text) DESC
        """
    ).fetchall()
    seen: set[str] = set()
    out: list[str] = []
    for canonical, alias in rows:
        a = alias.lower()
        if _has_word_boundary_match(haystack, a) and canonical not in seen:
            seen.add(canonical)
            out.append(f"{canonical} (via '{alias}')")
            if len(out) >= limit:
                break
    return " | ".join(out)


def _write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
    return len(rows)


def write_slice_a(conn: sqlite3.Connection, catalog_vendors: set[str]) -> int:
    """Named-vendor individual use_cases: vendor_name is non-empty and
    non-generic, and the row has zero product edges."""
    rows = conn.execute(
        """
        SELECT uc.id, a.abbreviation AS agency, uc.use_case_name,
               uc.vendor_name, uc.system_name, uc.development_type,
               uc.ai_classification, uc.problem_statement,
               uc.expected_benefits
          FROM use_cases uc
          JOIN agencies a ON a.id = uc.agency_id
         WHERE uc.vendor_name IS NOT NULL
           AND TRIM(uc.vendor_name) <> ''
           AND NOT EXISTS (SELECT 1 FROM use_case_products ucp WHERE ucp.use_case_id = uc.id)
        ORDER BY uc.id
        """
    ).fetchall()
    out: list[dict[str, object]] = []
    for r in rows:
        (uc_id, agency, name, vendor, system, dev, ai_class,
         problem, benefits) = r
        if _is_generic(vendor):
            continue
        candidates = _candidate_products(
            conn, [name, vendor, system, problem, benefits], limit=5
        )
        out.append({
            "use_case_id": uc_id,
            "agency": agency,
            "use_case_name": name,
            "vendor_name": vendor,
            "system_name": system or "",
            "development_type": dev or "",
            "ai_classification": ai_class or "",
            "problem_statement": (problem or "").replace("\n", " ").strip(),
            "expected_benefits": (benefits or "").replace("\n", " ").strip(),
            "candidate_products": candidates,
            "pre_classification": "high_signal",
        })
    header = [
        "use_case_id", "agency", "use_case_name", "vendor_name", "system_name",
        "development_type", "ai_classification", "problem_statement",
        "expected_benefits", "candidate_products", "pre_classification",
    ]
    return _write_csv(OUT / "slice_a_named_vendor_individual.csv", header, out)


def write_slice_b_individual(conn: sqlite3.Connection, catalog_vendors: set[str]) -> int:
    """Mention-only individual use_cases: vendor_name empty/generic but a
    catalog vendor appears in name/system/problem text."""
    rows = conn.execute(
        """
        SELECT uc.id, a.abbreviation, uc.use_case_name,
               uc.vendor_name, uc.system_name, uc.development_type,
               uc.ai_classification, uc.problem_statement,
               uc.expected_benefits
          FROM use_cases uc
          JOIN agencies a ON a.id = uc.agency_id
         WHERE NOT EXISTS (SELECT 1 FROM use_case_products ucp WHERE ucp.use_case_id = uc.id)
        ORDER BY uc.id
        """
    ).fetchall()
    out: list[dict[str, object]] = []
    for r in rows:
        (uc_id, agency, name, vendor, system, dev, ai_class,
         problem, benefits) = r
        if not _is_generic(vendor):
            continue  # belongs in slice A, not B
        # Mention-only signal must appear in name or system fields — those
        # are deliberate vendor identifiers. Problem/benefits text often
        # mentions vendors casually ("similar to Copilot in functionality")
        # and produces too much noise.
        mention = _mentions_catalog_vendor(
            [name, system], catalog_vendors
        )
        if not mention:
            continue
        candidates = _candidate_products(
            conn, [name, system, problem, benefits], limit=5
        )
        out.append({
            "use_case_id": uc_id,
            "agency": agency,
            "use_case_name": name,
            "vendor_name": vendor or "",
            "system_name": system or "",
            "development_type": dev or "",
            "ai_classification": ai_class or "",
            "problem_statement": (problem or "").replace("\n", " ").strip(),
            "expected_benefits": (benefits or "").replace("\n", " ").strip(),
            "candidate_products": candidates,
            "matched_catalog_vendor": mention,
            "pre_classification": "medium_signal",
        })
    header = [
        "use_case_id", "agency", "use_case_name", "vendor_name", "system_name",
        "development_type", "ai_classification", "problem_statement",
        "expected_benefits", "candidate_products", "matched_catalog_vendor",
        "pre_classification",
    ]
    return _write_csv(OUT / "slice_b_mention_only_individual.csv", header, out)


def write_slice_b_consolidated(conn: sqlite3.Connection) -> int:
    """Named-product consolidated entries: commercial_product is non-empty
    and non-generic, and the row has zero edges."""
    rows = conn.execute(
        """
        SELECT c.id, a.abbreviation, c.ai_use_case,
               c.commercial_product, c.commercial_examples,
               c.agency_uses
          FROM consolidated_use_cases c
          JOIN agencies a ON a.id = c.agency_id
         WHERE c.commercial_product IS NOT NULL
           AND TRIM(c.commercial_product) <> ''
           AND NOT EXISTS (
             SELECT 1 FROM consolidated_use_case_products cucp
              WHERE cucp.consolidated_use_case_id = c.id
           )
        ORDER BY c.id
        """
    ).fetchall()
    out: list[dict[str, object]] = []
    for r in rows:
        (cu_id, agency, name, product, examples, uses) = r
        if _is_generic(product):
            continue
        # Reuse candidate_products against ai_use_case + commercial_product
        # + agency_uses (NOT commercial_examples — it's boilerplate).
        candidates = _candidate_products(
            conn, [name, product, uses], limit=5
        )
        out.append({
            "consolidated_use_case_id": cu_id,
            "agency": agency,
            "ai_use_case": name,
            "commercial_product": product,
            "agency_uses": (uses or "").replace("\n", " ").strip(),
            "commercial_examples_snippet": (examples or "").replace("\n", " ").strip()[:200],
            "candidate_products": candidates,
            "pre_classification": "high_signal",
        })
    header = [
        "consolidated_use_case_id", "agency", "ai_use_case",
        "commercial_product", "agency_uses",
        "commercial_examples_snippet", "candidate_products",
        "pre_classification",
    ]
    return _write_csv(OUT / "slice_b_named_consolidated.csv", header, out)


def write_slice_c_dark_sample(
    conn: sqlite3.Connection,
    catalog_vendors: set[str],
    n: int = 200,
) -> int:
    """Stratified random sample of 'dark' individual use_cases: vendor
    blank/generic AND no catalog vendor mentioned anywhere. Seeded RNG so
    re-runs produce identical samples."""
    rows = conn.execute(
        """
        SELECT uc.id, a.abbreviation, uc.use_case_name,
               uc.vendor_name, uc.system_name, uc.development_type,
               uc.ai_classification, uc.problem_statement,
               uc.expected_benefits
          FROM use_cases uc
          JOIN agencies a ON a.id = uc.agency_id
         WHERE NOT EXISTS (SELECT 1 FROM use_case_products ucp WHERE ucp.use_case_id = uc.id)
        ORDER BY uc.id
        """
    ).fetchall()
    dark: list[tuple] = []
    for r in rows:
        (_, _, name, vendor, system, _, _, problem, benefits) = r
        if not _is_generic(vendor):
            continue
        if _mentions_catalog_vendor([name, system, problem, benefits], catalog_vendors):
            continue
        dark.append(r)
    rng = random.Random(RANDOM_SEED)
    sample = rng.sample(dark, min(n, len(dark)))
    sample.sort(key=lambda x: x[0])  # stable order by use_case_id
    out: list[dict[str, object]] = []
    for r in sample:
        (uc_id, agency, name, vendor, system, dev, ai_class,
         problem, benefits) = r
        out.append({
            "use_case_id": uc_id,
            "agency": agency,
            "use_case_name": name,
            "vendor_name": vendor or "",
            "system_name": system or "",
            "development_type": dev or "",
            "ai_classification": ai_class or "",
            "problem_statement": (problem or "").replace("\n", " ").strip(),
            "expected_benefits": (benefits or "").replace("\n", " ").strip(),
            "pre_classification": "dark_sample",
        })
    header = [
        "use_case_id", "agency", "use_case_name", "vendor_name", "system_name",
        "development_type", "ai_classification", "problem_statement",
        "expected_benefits", "pre_classification",
    ]
    return _write_csv(OUT / "slice_c_dark_sample.csv", header, out)


def write_catalog_snapshot(conn: sqlite3.Connection) -> int:
    """Every catalog product with vendor, type, genai flags, parent,
    alias list, and current edge count. Agent D consumes this."""
    rows = conn.execute(
        """
        SELECT p.id, p.canonical_name, p.vendor, p.product_type,
               p.is_generative_ai, p.is_frontier_llm,
               parent.canonical_name AS parent_canonical_name,
               GROUP_CONCAT(pa.alias_text, '|') AS aliases,
               (SELECT COUNT(*) FROM use_case_products ucp WHERE ucp.product_id = p.id)
                 + (SELECT COUNT(*) FROM consolidated_use_case_products cucp WHERE cucp.product_id = p.id)
                 AS edge_count
          FROM products p
          LEFT JOIN products parent ON parent.id = p.parent_product_id
          LEFT JOIN product_aliases pa ON pa.product_id = p.id
         GROUP BY p.id
         ORDER BY p.vendor COLLATE NOCASE, p.canonical_name COLLATE NOCASE
        """
    ).fetchall()
    out: list[dict[str, object]] = []
    for r in rows:
        (pid, name, vendor, ptype, genai, frontier, parent, aliases, edges) = r
        out.append({
            "product_id": pid,
            "canonical_name": name,
            "vendor": vendor or "",
            "product_type": ptype or "",
            "is_generative_ai": genai or 0,
            "is_frontier_llm": frontier or 0,
            "parent_canonical_name": parent or "",
            "aliases": aliases or "",
            "edge_count": edges or 0,
        })
    header = [
        "product_id", "canonical_name", "vendor", "product_type",
        "is_generative_ai", "is_frontier_llm", "parent_canonical_name",
        "aliases", "edge_count",
    ]
    return _write_csv(OUT / "existing_catalog_snapshot.csv", header, out)


def main() -> int:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    OUT.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        catalog_vendors = _catalog_vendor_strings(conn)
        counts = {
            "slice_a_named_vendor_individual": write_slice_a(conn, catalog_vendors),
            "slice_b_mention_only_individual": write_slice_b_individual(conn, catalog_vendors),
            "slice_b_named_consolidated": write_slice_b_consolidated(conn),
            "slice_c_dark_sample": write_slice_c_dark_sample(conn, catalog_vendors),
            "existing_catalog_snapshot": write_catalog_snapshot(conn),
        }
    finally:
        conn.close()

    print("Wrote inputs to", OUT)
    for k, v in counts.items():
        print(f"  {k:<40s} {v:>4d} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
