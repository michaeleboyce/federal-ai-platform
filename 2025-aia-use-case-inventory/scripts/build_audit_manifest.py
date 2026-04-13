"""Build per-source audit artifacts for the 2025 AI inventory database.

The output is designed to support parallel review agents:
- audit/manifest.json: detailed per-source metadata and suspect rows
- audit/source_summary.csv: compact source-level summary
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import DB_PATH, get_connection
from load_inventories import DATA_DIR, clean_header, find_header_row, read_csv_rows, read_xlsx_rows

AUDIT_DIR = ROOT / "audit"
MANIFEST_PATH = AUDIT_DIR / "manifest.json"
SUMMARY_PATH = AUDIT_DIR / "source_summary.csv"

USE_CASE_FIELDS = [
    "use_case_name",
    "bureau_component",
    "vendor_name",
    "system_name",
    "ai_classification",
    "problem_statement",
    "development_type",
    "training_data_description",
    "has_custom_code",
]

CONSOLIDATED_FIELDS = [
    "ai_use_case",
    "commercial_product",
    "commercial_examples",
    "agency_uses",
    "estimated_licenses_users",
]

TAG_ENUM_FIELDS = [
    "entry_type",
    "product_capability",
    "ai_sophistication",
    "deployment_scope",
    "architecture_type",
    "use_type",
    "deployment_environment",
]


def read_raw_file(filepath: Path) -> dict[str, Any]:
    if filepath.suffix.lower() == ".csv":
        rows, source_detail = read_csv_rows(filepath)
        source_kind = "csv"
    elif filepath.suffix.lower() == ".xlsx":
        rows, source_detail = read_xlsx_rows(filepath)
        source_kind = "xlsx"
    else:
        raise ValueError(f"Unsupported source file type: {filepath}")

    if not rows:
        return {
            "source_kind": source_kind,
            "source_detail": source_detail,
            "header_row_index": None,
            "headers": [],
            "raw_row_count": 0,
            "non_empty_row_count": 0,
            "blank_row_count": 0,
        }

    header_idx = find_header_row(rows)
    headers = [clean_header(c) for c in rows[header_idx]]
    data_rows = rows[header_idx + 1 :]
    non_empty_rows = [r for r in data_rows if any(str(c).strip() for c in r)]
    return {
        "source_kind": source_kind,
        "source_detail": source_detail,
        "header_row_index": header_idx,
        "headers": headers,
        "raw_row_count": len(data_rows),
        "non_empty_row_count": len(non_empty_rows),
        "blank_row_count": len(data_rows) - len(non_empty_rows),
    }


def get_source_records(conn) -> list[dict[str, Any]]:
    sql = """
    SELECT
      'use_cases' AS table_name,
      u.source_file,
      a.abbreviation AS agency_abbr,
      a.name AS agency_name,
      COUNT(*) AS row_count
    FROM use_cases u
    JOIN agencies a ON a.id = u.agency_id
    GROUP BY u.source_file, a.abbreviation, a.name

    UNION ALL

    SELECT
      'consolidated_use_cases' AS table_name,
      c.source_file,
      a.abbreviation AS agency_abbr,
      a.name AS agency_name,
      COUNT(*) AS row_count
    FROM consolidated_use_cases c
    JOIN agencies a ON a.id = c.agency_id
    GROUP BY c.source_file, a.abbreviation, a.name

    ORDER BY agency_abbr, table_name, source_file
    """
    return [dict(row) for row in conn.execute(sql)]


def get_table_fields(table_name: str) -> list[str]:
    return USE_CASE_FIELDS if table_name == "use_cases" else CONSOLIDATED_FIELDS


def get_name_field(table_name: str) -> str:
    return "use_case_name" if table_name == "use_cases" else "ai_use_case"


def fetch_distribution(conn, query: str, params: tuple[Any, ...]) -> dict[str, int]:
    result = {}
    for row in conn.execute(query, params):
        key = row["key"] if row["key"] is not None else ""
        result[str(key)] = row["n"]
    return result


def field_completeness(conn, table_name: str, source_file: str, fields: list[str]) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM {table_name} WHERE source_file = ?",
        (source_file,),
    ).fetchone()["n"]
    if total == 0:
        return result

    for field in fields:
        n = conn.execute(
            f"""
            SELECT COUNT(*) AS n
            FROM {table_name}
            WHERE source_file = ?
              AND {field} IS NOT NULL
              AND TRIM(CAST({field} AS TEXT)) <> ''
            """,
            (source_file,),
        ).fetchone()["n"]
        result[field] = {
            "non_empty_count": n,
            "non_empty_pct": round(n / total, 4),
        }
    return result


def source_tag_summary(conn, table_name: str, source_file: str) -> dict[str, Any]:
    if table_name == "use_cases":
        join_sql = """
        FROM use_cases s
        LEFT JOIN use_case_tags t ON t.use_case_id = s.id
        WHERE s.source_file = ?
        """
    else:
        join_sql = """
        FROM consolidated_use_cases s
        LEFT JOIN use_case_tags t ON t.consolidated_use_case_id = s.id
        WHERE s.source_file = ?
        """

    counts = conn.execute(
        f"""
        SELECT
          COUNT(*) AS source_rows,
          COUNT(t.id) AS tagged_rows,
          SUM(CASE WHEN t.id IS NULL THEN 1 ELSE 0 END) AS untagged_rows
        {join_sql}
        """,
        (source_file,),
    ).fetchone()

    distributions = {}
    for field in TAG_ENUM_FIELDS:
        distributions[field] = fetch_distribution(
            conn,
            f"""
            SELECT COALESCE(NULLIF(TRIM(CAST(t.{field} AS TEXT)), ''), '<blank>') AS key,
                   COUNT(*) AS n
            {join_sql}
              AND t.id IS NOT NULL
            GROUP BY 1
            ORDER BY n DESC, key
            """,
            (source_file,),
        )

    bool_fields = [
        "is_general_llm_access",
        "is_coding_tool",
        "is_cots_commercial",
        "is_generative_ai",
        "is_frontier_model",
        "is_enterprise_wide",
        "has_model_training",
        "is_microsoft_copilot",
        "is_openai",
        "is_anthropic",
        "is_google",
        "is_github_copilot",
        "is_aws_ai",
        "is_public_facing",
        "has_meaningful_risk_docs",
    ]
    bool_distributions = {}
    for field in bool_fields:
        bool_distributions[field] = fetch_distribution(
            conn,
            f"""
            SELECT COALESCE(CAST(t.{field} AS TEXT), '<null>') AS key,
                   COUNT(*) AS n
            {join_sql}
              AND t.id IS NOT NULL
            GROUP BY 1
            ORDER BY n DESC, key
            """,
            (source_file,),
        )

    return {
        "source_rows": counts["source_rows"],
        "tagged_rows": counts["tagged_rows"],
        "untagged_rows": counts["untagged_rows"] or 0,
        "tag_distributions": distributions,
        "bool_distributions": bool_distributions,
    }


def top_products_and_templates(conn, table_name: str, source_file: str) -> dict[str, dict[str, int]]:
    id_field = "use_case_id" if table_name == "use_cases" else "consolidated_use_case_id"
    if table_name == "use_cases":
        source_table = "use_cases"
        source_name = "use_case_name"
        product_source_col = "u.product_id"
        template_source_col = "u.template_id"
    else:
        source_table = "consolidated_use_cases"
        source_name = "u.ai_use_case"
        product_source_col = "u.product_id"
        template_source_col = "u.template_id"

    product_query = f"""
    SELECT COALESCE(p.canonical_name, '<blank>') AS key, COUNT(*) AS n
    FROM {source_table} u
    LEFT JOIN products p ON p.id = {product_source_col}
    WHERE u.source_file = ?
    GROUP BY 1
    ORDER BY n DESC, key
    LIMIT 10
    """
    template_query = f"""
    SELECT COALESCE(t.short_name, t.template_text, '<blank>') AS key, COUNT(*) AS n
    FROM {source_table} u
    LEFT JOIN use_case_templates t ON t.id = {template_source_col}
    WHERE u.source_file = ?
    GROUP BY 1
    ORDER BY n DESC, key
    LIMIT 10
    """
    sample_query = f"""
    SELECT u.id, {source_name} AS name
    FROM {source_table} u
    WHERE u.source_file = ?
    ORDER BY u.id
    LIMIT 10
    """
    return {
        "top_products": fetch_distribution(conn, product_query, (source_file,)),
        "top_templates": fetch_distribution(conn, template_query, (source_file,)),
        "sample_rows": [dict(row) for row in conn.execute(sample_query, (source_file,))],
    }


def suspect_rows(conn, table_name: str, source_file: str, limit: int = 25) -> list[dict[str, Any]]:
    if table_name == "use_cases":
        name_col = "u.use_case_name"
        join_col = "t.use_case_id = u.id"
        suspect_sql = f"""
        SELECT
          u.id,
          {name_col} AS name,
          COALESCE(u.vendor_name, '') AS vendor_name,
          COALESCE(u.system_name, '') AS system_name,
          COALESCE(u.development_type, '') AS development_type,
          COALESCE(u.ai_classification, '') AS ai_classification,
          COALESCE(t.entry_type, '') AS entry_type,
          COALESCE(t.ai_sophistication, '') AS ai_sophistication,
          COALESCE(t.architecture_type, '') AS architecture_type,
          COALESCE(t.deployment_scope, '') AS deployment_scope,
          COALESCE(t.tool_product_name, '') AS tool_product_name,
          COALESCE(t.tool_vendor, '') AS tool_vendor,
          COALESCE(p.canonical_name, '') AS linked_product,
          CASE
            WHEN t.id IS NULL THEN 'missing_tag'
            WHEN t.is_general_llm_access = 1 AND COALESCE(t.ai_sophistication, '') NOT IN ('general_llm', 'coding_assistant', 'agentic') THEN 'llm_flag_vs_sophistication'
            WHEN t.is_coding_tool = 1 AND COALESCE(t.ai_sophistication, '') <> 'coding_assistant' THEN 'coding_flag_vs_sophistication'
            WHEN u.vendor_name <> '' AND p.canonical_name IS NULL AND COALESCE(t.tool_product_name, '') = '' THEN 'vendor_present_no_product'
            WHEN p.canonical_name <> '' AND COALESCE(t.is_cots_commercial, 0) = 0 THEN 'linked_product_not_marked_cots'
            WHEN COALESCE(t.deployment_scope, '') = 'enterprise_wide' AND COALESCE(u.bureau_component, '') <> '' THEN 'enterprise_scope_with_bureau'
            WHEN COALESCE(t.architecture_type, '') IN ('fine_tuned', 'custom_trained') AND COALESCE(t.has_model_training, 0) = 0 THEN 'training_architecture_without_training_flag'
            ELSE 'other'
          END AS suspect_reason
        FROM use_cases u
        LEFT JOIN use_case_tags t ON {join_col}
        LEFT JOIN products p ON p.id = u.product_id
        WHERE u.source_file = ?
          AND (
            t.id IS NULL
            OR (t.is_general_llm_access = 1 AND COALESCE(t.ai_sophistication, '') NOT IN ('general_llm', 'coding_assistant', 'agentic'))
            OR (t.is_coding_tool = 1 AND COALESCE(t.ai_sophistication, '') <> 'coding_assistant')
            OR (u.vendor_name IS NOT NULL AND TRIM(u.vendor_name) <> '' AND p.canonical_name IS NULL AND COALESCE(t.tool_product_name, '') = '')
            OR (p.canonical_name IS NOT NULL AND COALESCE(t.is_cots_commercial, 0) = 0)
            OR (COALESCE(t.deployment_scope, '') = 'enterprise_wide' AND COALESCE(u.bureau_component, '') <> '')
            OR (COALESCE(t.architecture_type, '') IN ('fine_tuned', 'custom_trained') AND COALESCE(t.has_model_training, 0) = 0)
          )
        ORDER BY u.id
        LIMIT ?
        """
    else:
        name_col = "u.ai_use_case"
        join_col = "t.consolidated_use_case_id = u.id"
        suspect_sql = f"""
        SELECT
          u.id,
          {name_col} AS name,
          COALESCE(u.commercial_product, '') AS vendor_name,
          '' AS system_name,
          '' AS development_type,
          '' AS ai_classification,
          COALESCE(t.entry_type, '') AS entry_type,
          COALESCE(t.ai_sophistication, '') AS ai_sophistication,
          COALESCE(t.architecture_type, '') AS architecture_type,
          COALESCE(t.deployment_scope, '') AS deployment_scope,
          COALESCE(t.tool_product_name, '') AS tool_product_name,
          COALESCE(t.tool_vendor, '') AS tool_vendor,
          COALESCE(p.canonical_name, '') AS linked_product,
          CASE
            WHEN t.id IS NULL THEN 'missing_tag'
            WHEN COALESCE(u.commercial_product, '') <> '' AND p.canonical_name IS NULL AND COALESCE(t.tool_product_name, '') = '' THEN 'commercial_product_no_link'
            WHEN COALESCE(t.entry_type, '') <> 'generic_use_pattern' THEN 'unexpected_entry_type_for_consolidated'
            WHEN p.canonical_name IS NOT NULL AND COALESCE(t.is_cots_commercial, 0) = 0 THEN 'linked_product_not_marked_cots'
            ELSE 'other'
          END AS suspect_reason
        FROM consolidated_use_cases u
        LEFT JOIN use_case_tags t ON {join_col}
        LEFT JOIN products p ON p.id = u.product_id
        WHERE u.source_file = ?
          AND (
            t.id IS NULL
            OR (COALESCE(u.commercial_product, '') <> '' AND p.canonical_name IS NULL AND COALESCE(t.tool_product_name, '') = '')
            OR COALESCE(t.entry_type, '') <> 'generic_use_pattern'
            OR (p.canonical_name IS NOT NULL AND COALESCE(t.is_cots_commercial, 0) = 0)
          )
        ORDER BY u.id
        LIMIT ?
        """
    return [dict(row) for row in conn.execute(suspect_sql, (source_file, limit))]


def summarize_manifest(manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in manifest:
        rows.append(
            {
                "agency_abbr": item["agency_abbr"],
                "table_name": item["table_name"],
                "source_file": item["source_file"],
                "db_rows": item["db_row_count"],
                "raw_non_empty_rows": item["raw_file"]["non_empty_row_count"],
                "row_delta": item["raw_file"]["non_empty_row_count"] - item["db_row_count"],
                "tagged_rows": item["tag_summary"]["tagged_rows"],
                "untagged_rows": item["tag_summary"]["untagged_rows"],
                "suspect_rows": len(item["suspect_rows"]),
                "header_row_index": item["raw_file"]["header_row_index"],
                "source_detail": item["raw_file"]["source_detail"],
            }
        )
    return rows


def write_summary_csv(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with SUMMARY_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_manifest() -> dict[str, Any]:
    conn = get_connection()
    manifest_items = []
    try:
        for source in get_source_records(conn):
            filepath = DATA_DIR / source["source_file"]
            raw_file = read_raw_file(filepath)
            fields = get_table_fields(source["table_name"])
            manifest_items.append(
                {
                    **source,
                    "file_path": str(filepath),
                    "db_path": str(DB_PATH),
                    "db_row_count": source["row_count"],
                    "raw_file": raw_file,
                    "field_completeness": field_completeness(conn, source["table_name"], source["source_file"], fields),
                    "tag_summary": source_tag_summary(conn, source["table_name"], source["source_file"]),
                    "label_summary": top_products_and_templates(conn, source["table_name"], source["source_file"]),
                    "suspect_rows": suspect_rows(conn, source["table_name"], source["source_file"]),
                }
            )
    finally:
        conn.close()

    summary_rows = summarize_manifest(manifest_items)
    report = {
        "generated_from": str(DB_PATH),
        "source_dir": str(DATA_DIR),
        "source_count": len(manifest_items),
        "manifest": manifest_items,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_summary_csv(summary_rows)
    return report


def print_overview(report: dict[str, Any]) -> None:
    table_counts = Counter(item["table_name"] for item in report["manifest"])
    by_agency = defaultdict(int)
    for item in report["manifest"]:
        by_agency[item["agency_abbr"]] += 1

    overview = {
        "source_count": report["source_count"],
        "table_counts": dict(table_counts),
        "agencies_covered": len(by_agency),
        "sources_with_untagged_rows": sum(1 for item in report["manifest"] if item["tag_summary"]["untagged_rows"]),
        "sources_with_suspects": sum(1 for item in report["manifest"] if item["suspect_rows"]),
        "manifest_path": str(MANIFEST_PATH),
        "summary_path": str(SUMMARY_PATH),
    }
    print(json.dumps(overview, indent=2))


if __name__ == "__main__":
    print_overview(build_manifest())
