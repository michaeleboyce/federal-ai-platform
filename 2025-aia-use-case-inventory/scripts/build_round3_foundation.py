"""Build the round-3 sub-agency review pack from the live DB.

Output: audit/retag/round3/_foundation/sub_agencies.json — a JSON array of
sub-agency entries the parallel slice agents will rate. Each entry is enough
context to make a per-sub-agency decision without re-running queries.

Filter: include all level='sub_agency' rows, plus level='office' rows with
≥10 subtree use cases. Skip orgs with <5 subtree use cases.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_PATH = ROOT / "audit" / "retag" / "round3" / "_foundation" / "sub_agencies.json"

MIN_SUB_AGENCY_USE_CASES = 5
MIN_OFFICE_USE_CASES = 10


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT fo.id, fo.slug, fo.name, fo.abbreviation, fo.level,
               fo.parent_id, fo.hierarchy_path,
               (
                 SELECT COUNT(*) FROM use_cases uc
                  JOIN federal_organizations fo2 ON fo2.id = uc.bureau_organization_id
                 WHERE fo2.hierarchy_path LIKE fo.hierarchy_path || '%'
               ) AS subtree_use_cases,
               (
                 SELECT COUNT(*) FROM use_cases uc
                  JOIN federal_organizations fo2 ON fo2.id = uc.bureau_organization_id
                  LEFT JOIN use_case_tags t ON t.use_case_id = uc.id
                 WHERE fo2.hierarchy_path LIKE fo.hierarchy_path || '%'
                   AND t.is_general_llm_access = 1
               ) AS subtree_llm_count,
               (
                 SELECT COUNT(*) FROM use_cases uc
                  JOIN federal_organizations fo2 ON fo2.id = uc.bureau_organization_id
                  LEFT JOIN use_case_tags t ON t.use_case_id = uc.id
                 WHERE fo2.hierarchy_path LIKE fo.hierarchy_path || '%'
                   AND t.is_coding_tool = 1
               ) AS subtree_coding_count,
               (
                 SELECT COUNT(*) FROM use_cases uc
                  JOIN federal_organizations fo2 ON fo2.id = uc.bureau_organization_id
                  LEFT JOIN use_case_tags t ON t.use_case_id = uc.id
                 WHERE fo2.hierarchy_path LIKE fo.hierarchy_path || '%'
                   AND t.is_general_llm_access = 1
                   AND t.deployment_scope IN ('enterprise_wide','department')
               ) AS subtree_enterprise_llm_count,
               (
                 SELECT COUNT(*) FROM use_cases uc
                  JOIN federal_organizations fo2 ON fo2.id = uc.bureau_organization_id
                  LEFT JOIN use_case_tags t ON t.use_case_id = uc.id
                 WHERE fo2.hierarchy_path LIKE fo.hierarchy_path || '%'
                   AND t.deployment_environment IS NOT NULL
                   AND t.deployment_environment != 'unknown'
               ) AS subtree_env_count,
               (SELECT maturity_tier FROM org_ai_maturity m WHERE m.organization_id = fo.id) AS maturity_tier
          FROM federal_organizations fo
         WHERE fo.level IN ('sub_agency', 'office')
        """
    ).fetchall()

    # Build a parent-id → top-level abbreviation map by walking hierarchy_path.
    top_by_id = {
        r["id"]: r["abbreviation"]
        for r in conn.execute(
            "SELECT id, abbreviation FROM federal_organizations WHERE parent_id IS NULL"
        ).fetchall()
    }

    def top_abbr(hierarchy_path: str | None) -> str | None:
        if not hierarchy_path:
            return None
        parts = [p for p in hierarchy_path.split("/") if p]
        if not parts:
            return None
        try:
            return top_by_id.get(int(parts[0]))
        except ValueError:
            return None

    out: list[dict] = []
    for r in rows:
        n = r["subtree_use_cases"] or 0
        threshold = MIN_OFFICE_USE_CASES if r["level"] == "office" else MIN_SUB_AGENCY_USE_CASES
        if n < threshold:
            continue

        # Pull a sample of use-case names from this org's subtree
        samples = conn.execute(
            """
            SELECT u.use_case_name, u.system_name, u.vendor_name
              FROM use_cases u
              JOIN federal_organizations fo2 ON fo2.id = u.bureau_organization_id
             WHERE fo2.hierarchy_path LIKE ? || '%'
             ORDER BY (
                CASE WHEN u.system_name IS NOT NULL AND TRIM(u.system_name) != '' THEN 0 ELSE 1 END
             ) ASC, u.id ASC
             LIMIT 8
            """,
            (r["hierarchy_path"],),
        ).fetchall()

        # Distinct named tools/products mentioned in the subtree
        tools = conn.execute(
            """
            SELECT DISTINCT t.tool_product_name
              FROM use_case_tags t
              JOIN use_cases u ON u.id = t.use_case_id
              JOIN federal_organizations fo2 ON fo2.id = u.bureau_organization_id
             WHERE fo2.hierarchy_path LIKE ? || '%'
               AND t.tool_product_name IS NOT NULL
               AND t.tool_product_name != ''
             LIMIT 10
            """,
            (r["hierarchy_path"],),
        ).fetchall()

        out.append({
            "slug": r["slug"],
            "name": r["name"],
            "abbreviation": r["abbreviation"],
            "level": r["level"],
            "parent_agency": top_abbr(r["hierarchy_path"]),
            "subtree_use_cases": n,
            "subtree_llm_count": r["subtree_llm_count"] or 0,
            "subtree_coding_count": r["subtree_coding_count"] or 0,
            "subtree_enterprise_llm_count": r["subtree_enterprise_llm_count"] or 0,
            "subtree_env_count": r["subtree_env_count"] or 0,
            "maturity_tier": r["maturity_tier"],
            "sample_use_cases": [
                {
                    "name": s["use_case_name"],
                    "system_name": s["system_name"],
                    "vendor_name": s["vendor_name"],
                }
                for s in samples
            ],
            "named_tools": [t["tool_product_name"] for t in tools],
        })

    out.sort(key=lambda x: (x["parent_agency"] or "", -x["subtree_use_cases"]))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2))

    print(f"[round3-foundation] {len(out)} sub-agencies in scope")
    by_parent: dict[str, int] = {}
    for e in out:
        p = e["parent_agency"] or "?"
        by_parent[p] = by_parent.get(p, 0) + 1
    for p in sorted(by_parent, key=lambda k: -by_parent[k])[:15]:
        print(f"  {p:>10}: {by_parent[p]:>3} sub-agencies")
    print(f"[round3-foundation] wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
