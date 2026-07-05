"""Apply the band_product_links_2026-07 verdicts to consolidated_use_case_products.

Reads audit/retag/band_product_links_2026-07/links_*.csv (+ optional
audit_overrides.csv; for any slug with an `override` row, the override
rows replace ALL of that slug's proposed links). Verdicts:

  link         -> INSERT the (consolidated row, product) edge.
  new_product  -> same as link, but the product is expected to have been
                  added to data/expanded_product_catalog.csv during the
                  audit-gate integration (apply_expanded_product_catalog.py
                  runs earlier in `make fix`); unresolved names are drops.
  no_product   -> recorded, nothing written.

Products resolve by canonical_name (then alias) — survives products.id
rotation. Consolidated rows resolve by deterministic slug. Confidence is
already `strong|inferred` per the pass instructions (DB CHECK vocabulary).
Unresolved rows -> apply_drops.csv; hard-fail above 2% unresolved.
Idempotent (INSERT OR IGNORE; the link table is wiped+rebuilt upstream
each `make fix` anyway). Wired into `make fix` after
apply_product_queue_review.py.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db import get_connection  # noqa: E402

PASS_DIR = _ROOT / "audit" / "retag" / "band_product_links_2026-07"
VALID_VERDICTS = {"link", "new_product", "no_product"}
VALID_CONFIDENCE = {"strong", "inferred"}
MAX_UNRESOLVED = 0.02


def load_rows() -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    rows: list[dict] = []
    files = sorted(PASS_DIR.glob("links_*.csv"))
    if not files:
        return [], [f"no links_*.csv under {PASS_DIR}"]

    # Read the audit layer FIRST: base rows for overridden slugs are
    # replaced wholesale, so they must not be validated (an override often
    # exists precisely because the base row is malformed).
    override_rows: list[dict] = []
    overridden_slugs: set[str] = set()
    overrides = PASS_DIR / "audit_overrides.csv"
    if overrides.exists():
        with overrides.open() as f:
            for row in csv.DictReader(f):
                if (row.get("audit_verdict") or "override") == "agree":
                    continue
                overridden_slugs.add(row["slug"])
                override_rows.append(row)

    for path in files:
        with path.open() as f:
            for row in csv.DictReader(f):
                if row.get("slug") in overridden_slugs:
                    continue
                rows.append(row)
    rows.extend(override_rows)

    validated: list[dict] = []
    for row in rows:
        src = "audit_overrides.csv" if row.get("audit_verdict") else "links batch"
        if row.get("verdict") not in VALID_VERDICTS:
            errors.append(
                f"{src}: slug={row.get('slug')} bad verdict "
                f"{row.get('verdict')!r}"
            )
            continue
        if row["verdict"] != "no_product" and (
            row.get("confidence") not in VALID_CONFIDENCE
        ):
            errors.append(
                f"{src}: slug={row.get('slug')} bad confidence "
                f"{row.get('confidence')!r} (must be strong|inferred)"
            )
            continue
        validated.append(row)
    return validated, errors


def main() -> int:
    if not sorted(PASS_DIR.glob("links_*.csv")):
        print(
            f"WARNING: no links_*.csv under {PASS_DIR} yet — skipping "
            f"(batches land incrementally)."
        )
        return 0
    rows, errors = load_rows()
    if errors:
        print("VALIDATION ERRORS — nothing written:")
        for e in errors:
            print(f"  - {e}")
        return 1

    conn = get_connection()
    try:
        cuc_by_slug = {
            slug: cid
            for slug, cid in conn.execute(
                "SELECT slug, id FROM consolidated_use_cases WHERE slug IS NOT NULL"
            )
        }
        product_by_name: dict[str, int] = {}
        for name, pid in conn.execute(
            "SELECT LOWER(TRIM(canonical_name)), id FROM products"
        ):
            product_by_name[name] = pid
        for alias, pid in conn.execute(
            "SELECT LOWER(TRIM(alias_text)), product_id FROM product_aliases"
        ):
            product_by_name.setdefault(alias, pid)

        stats = {"linked": 0, "no_product": 0}
        drops: list[dict] = []
        linkable = [r for r in rows if r["verdict"] != "no_product"]
        with conn:
            for row in rows:
                if row["verdict"] == "no_product":
                    stats["no_product"] += 1
                    continue
                cid = cuc_by_slug.get(row["slug"])
                pid = product_by_name.get(
                    (row.get("product_canonical_name") or "").strip().lower()
                )
                if cid is None or pid is None:
                    drops.append(
                        {
                            **row,
                            "_drop_reason": "slug_unresolved"
                            if cid is None
                            else "product_not_in_catalog",
                        }
                    )
                    continue
                conn.execute(
                    """
                    INSERT OR IGNORE INTO consolidated_use_case_products
                        (consolidated_use_case_id, product_id,
                         evidence_text, confidence)
                    VALUES (?,?,?,?)
                    """,
                    (cid, pid, row.get("evidence_text"), row["confidence"]),
                )
                stats["linked"] += 1

        if drops:
            drop_path = PASS_DIR / "apply_drops.csv"
            with drop_path.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(drops[0].keys()))
                w.writeheader()
                w.writerows(drops)
            print(f"{len(drops)} unresolved rows -> {drop_path}")
        unresolved_frac = len(drops) / max(1, len(linkable))
        if unresolved_frac > MAX_UNRESOLVED:
            print(
                f"FATAL: {unresolved_frac:.1%} of link rows unresolved "
                f"(max {MAX_UNRESOLVED:.0%}). If these are new_product "
                f"verdicts, add them to data/expanded_product_catalog.csv "
                f"first."
            )
            return 1
        print(
            f"Applied {stats['linked']} links; {stats['no_product']} "
            f"no_product rows acknowledged."
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
