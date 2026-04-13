"""Surgical migration: recompute ``deployment_scope`` and ``architecture_type``
for every row in ``use_case_tags`` using the evidence-gated inference in
``auto_tag.infer_scope()`` and ``auto_tag.infer_architecture()``.

Phase 2 Agent E. Leaves every other tag column untouched.

Prints the before/after distribution for both columns and the count of rows
demoted to ``'unknown'`` for each.

Usage::

    python scripts/retag_scope_architecture.py

Idempotent; safe to re-run.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

# Ensure the project root is on sys.path so ``auto_tag`` and ``db`` import
# cleanly when the script is invoked from anywhere.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auto_tag import (  # noqa: E402  (sys.path tweak must precede)
    infer_architecture,
    infer_scope,
    load_products,
)
from db import get_connection  # noqa: E402


def _row_to_dict(row):
    return {k: (v if v is not None else "") for k, v in dict(row).items()}


def _distribution(conn, column: str) -> Counter:
    rows = conn.execute(
        f"SELECT {column}, COUNT(*) FROM use_case_tags GROUP BY {column}"
    ).fetchall()
    return Counter({(r[0] or "NULL"): r[1] for r in rows})


def _print_distribution(label: str, before: Counter, after: Counter) -> None:
    print(f"\n{label} distribution")
    print("-" * (len(label) + 13))
    keys = sorted(set(before) | set(after))
    width = max((len(str(k)) for k in keys), default=10)
    print(f"  {'value'.ljust(width)}  {'before':>7}  {'after':>7}  {'delta':>7}")
    for k in keys:
        b = before.get(k, 0)
        a = after.get(k, 0)
        d = a - b
        sign = "+" if d > 0 else ""
        print(f"  {str(k).ljust(width)}  {b:>7}  {a:>7}  {sign}{d:>6}")


def retag() -> None:
    conn = get_connection()
    try:
        before_scope = _distribution(conn, "deployment_scope")
        before_arch = _distribution(conn, "architecture_type")

        products_dict = load_products(conn)

        # Pull every tag row along with its source row (canonical or consolidated).
        # The product_id lives on the source row, not the tag row.
        tag_rows = conn.execute(
            """
            SELECT id, use_case_id, consolidated_use_case_id
            FROM use_case_tags
            """
        ).fetchall()

        updated = 0
        demoted_to_unknown_scope = 0
        demoted_to_unknown_arch = 0

        for tag in tag_rows:
            tid = tag["id"]
            if tag["use_case_id"] is not None:
                src = conn.execute(
                    """
                    SELECT uc.*, a.abbreviation AS agency_abbr
                    FROM use_cases uc JOIN agencies a ON a.id = uc.agency_id
                    WHERE uc.id = ?
                    """,
                    (tag["use_case_id"],),
                ).fetchone()
                is_consolidated = False
            else:
                src = conn.execute(
                    """
                    SELECT c.*, a.abbreviation AS agency_abbr
                    FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id
                    WHERE c.id = ?
                    """,
                    (tag["consolidated_use_case_id"],),
                ).fetchone()
                is_consolidated = True

            if src is None:
                continue

            row_dict = _row_to_dict(src)
            product_id = row_dict.get("product_id") or None

            # Previous values for delta tracking.
            prev = conn.execute(
                "SELECT deployment_scope, architecture_type FROM use_case_tags WHERE id = ?",
                (tid,),
            ).fetchone()
            prev_scope = prev["deployment_scope"]
            prev_arch = prev["architecture_type"]

            if is_consolidated:
                scope, scope_detail = infer_scope(
                    row_dict, is_consolidated=True, bureau="", agency_abbr=row_dict.get("agency_abbr", "")
                )
            else:
                scope, scope_detail = infer_scope(
                    row_dict,
                    is_consolidated=False,
                    bureau=row_dict.get("bureau_component", ""),
                    agency_abbr=row_dict.get("agency_abbr", ""),
                )

            arch, has_train = infer_architecture(row_dict, products_dict, product_id)

            is_enterprise = 1 if scope == "enterprise_wide" else 0

            conn.execute(
                """
                UPDATE use_case_tags
                SET deployment_scope = ?,
                    scope_detail = ?,
                    is_enterprise_wide = ?,
                    architecture_type = ?,
                    has_model_training = ?
                WHERE id = ?
                """,
                (scope, scope_detail, is_enterprise, arch, has_train, tid),
            )
            updated += 1

            if prev_scope != "unknown" and scope == "unknown":
                demoted_to_unknown_scope += 1
            if prev_arch != "unknown" and arch == "unknown":
                demoted_to_unknown_arch += 1

        conn.commit()

        after_scope = _distribution(conn, "deployment_scope")
        after_arch = _distribution(conn, "architecture_type")

        print(f"\nRetagged {updated} use_case_tags rows")
        print(f"  rows demoted to deployment_scope='unknown': {demoted_to_unknown_scope}")
        print(f"  rows demoted to architecture_type='unknown': {demoted_to_unknown_arch}")

        _print_distribution("deployment_scope", before_scope, after_scope)
        _print_distribution("architecture_type", before_arch, after_arch)
    finally:
        conn.close()


if __name__ == "__main__":
    retag()
