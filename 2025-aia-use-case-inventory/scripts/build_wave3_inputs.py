"""Build Wave 3 reconciliation input from flagged Wave 2 rows.

Wave 3 reconciles every row that Wave 2 flagged (`use_case_tags_2024` with
`wave IN ('2a','2b')`). For each flagged row, the Wave 3 agent reads:
- The 2024 narrative
- The Wave 1 tag (canonical for this use case before reconciliation)
- The Wave 2 flag(s) + reasoning + any proposed corrected tag fields
- For Wave 2a rows: the matched 2025 row + 2025 IFP tags
- For Wave 2b rows: just the 2024 row

…and produces a `wave='3'` row with the final canonical tag.

Also exports the subset of Wave 2a rows tagged `tagging_error_2025` to
`audit/retag/2024-vs-2025-divergence/queue.csv` for separate manual
remediation of 2025 tags (not part of this plan's deliverables).
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "federal_ai_inventory_2025.db"
DEFAULT_OUT = ROOT / "audit" / "retag" / "2024-tagging"
ERROR_2025_QUEUE = ROOT / "audit" / "retag" / "2024-vs-2025-divergence" / "queue.csv"

# Wave 1 tag fields carried into Wave 3 input as the "current canonical."
W1_FIELDS = (
    "entry_type",
    "is_generative_ai",
    "ai_sophistication",
    "deployment_scope",
    "scope_detail",
    "is_enterprise_wide",
    "is_general_llm_access",
    "is_coding_tool",
    "is_cots_commercial",
    "tool_product_name",
    "tool_vendor",
    "is_microsoft_copilot",
    "is_openai",
    "is_anthropic",
    "is_google",
    "is_github_copilot",
    "is_aws_ai",
    "architecture_type",
    "use_type",
    "is_public_facing",
    "confidence",
    "reasoning",
)

# Wave 2 fields carried in (the divergence flag + the QA agent's proposed
# corrected tags). Same shape as W1 so the Wave 3 agent can compare.
W2_FIELDS = W1_FIELDS + ("quality_flags_json",)

# 2025 mirror fields (only joined for Wave 2a rows).
TAGS_2025_FIELDS = (
    "entry_type",
    "is_generative_ai",
    "ai_sophistication",
    "deployment_scope",
    "is_enterprise_wide",
    "is_general_llm_access",
    "is_coding_tool",
    "is_cots_commercial",
    "tool_product_name",
    "tool_vendor",
    "is_microsoft_copilot",
    "architecture_type",
    "use_type",
)


def _wave1_for(conn, use_case_ids: set[int]) -> dict[int, dict]:
    if not use_case_ids:
        return {}
    placeholders = ",".join(["?"] * len(use_case_ids))
    cols = ", ".join(W1_FIELDS)
    rows = conn.execute(
        f"SELECT use_case_id_2024, {cols} FROM use_case_tags_2024 "
        f"WHERE wave='1' AND use_case_id_2024 IN ({placeholders})",
        list(use_case_ids),
    ).fetchall()
    return {r["use_case_id_2024"]: dict(r) for r in rows}


def _narrative_2024(conn, use_case_ids: set[int]) -> dict[int, dict]:
    if not use_case_ids:
        return {}
    placeholders = ",".join(["?"] * len(use_case_ids))
    rows = conn.execute(
        f"""
        SELECT id, agency_abbreviation, bureau, use_case_name,
               purpose_benefits, outputs, commercial_ai, dev_method, dev_stage
        FROM use_cases_2024 WHERE id IN ({placeholders})
        """,
        list(use_case_ids),
    ).fetchall()
    return {r["id"]: dict(r) for r in rows}


def _matched_2025(conn, use_case_ids: set[int]) -> dict[int, dict]:
    """For 2024 ids with a 2025 match in use_case_year_links, return the
    matched 2025 narrative + IFP tags."""
    if not use_case_ids:
        return {}
    placeholders = ",".join(["?"] * len(use_case_ids))
    rows = conn.execute(
        f"""
        SELECT
            l.uc_2024_id,
            l.uc_2025_id,
            l.lineage_status,
            u25.use_case_name AS name_2025,
            u25.problem_statement AS problem_statement_2025,
            u25.expected_benefits AS expected_benefits_2025,
            u25.system_outputs AS system_outputs_2025,
            u25.ai_classification AS ai_classification_2025,
            u25.vendor_name AS vendor_name_2025,
            u25.system_name AS system_name_2025,
            { ", ".join(f"t25.{f} AS {f}_2025" for f in TAGS_2025_FIELDS) }
        FROM use_case_year_links l
        JOIN use_cases u25 ON u25.id = l.uc_2025_id
        LEFT JOIN use_case_tags t25 ON t25.use_case_id = u25.id
        WHERE l.uc_2024_id IN ({placeholders})
          AND l.lineage_status IN ('continued','renamed','split')
        """,
        list(use_case_ids),
    ).fetchall()
    out: dict[int, dict] = {}
    for r in rows:
        # If a 2024 row has multiple 2025 matches (split), keep them all
        # serialized as JSON so the agent sees the full picture.
        d = dict(r)
        existing = out.get(d["uc_2024_id"])
        if existing is None:
            out[d["uc_2024_id"]] = {**d, "_match_count": 1}
        else:
            existing["_match_count"] += 1
            existing.setdefault("_additional_matches", []).append(
                {k: d[k] for k in d if k not in ("uc_2024_id",)}
            )
    return out


def _flagged_w2_rows(conn) -> list[sqlite3.Row]:
    cols_w2 = ", ".join(W2_FIELDS)
    return conn.execute(
        f"""
        SELECT use_case_id_2024, wave, tagged_by_agent, {cols_w2}
        FROM use_case_tags_2024
        WHERE wave IN ('2a','2b')
        ORDER BY use_case_id_2024, wave, tagged_by_agent
        """
    ).fetchall()


def build(conn, out_dir: Path = DEFAULT_OUT) -> dict[str, int]:
    flagged_rows = _flagged_w2_rows(conn)
    ids = {r["use_case_id_2024"] for r in flagged_rows}
    w1 = _wave1_for(conn, ids)
    narrative = _narrative_2024(conn, ids)
    matched_2025 = _matched_2025(conn, ids)

    # Group Wave 2 flags by use case (a single use case can have both a
    # 2a flag AND a 2b flag in theory; usually just one). The Wave 3 agent
    # sees all flags for the use case together.
    by_uc: dict[int, list[dict]] = {}
    for r in flagged_rows:
        by_uc.setdefault(r["use_case_id_2024"], []).append(dict(r))

    # Wave 3 inputs are partitioned by row count for parallelism: 3 agents
    # take ~equal shares of the flagged universe.
    uc_ids = sorted(by_uc.keys())
    n = len(uc_ids)
    chunk = (n + 2) // 3
    partitions = {
        "P1": uc_ids[:chunk],
        "P2": uc_ids[chunk:chunk * 2],
        "P3": uc_ids[chunk * 2:],
    }

    counts: dict[str, int] = {}
    out_dir_w3 = out_dir / "wave3_inputs"
    out_dir_w3.mkdir(parents=True, exist_ok=True)

    for letter, ucs in partitions.items():
        rows_out = []
        for uc in ucs:
            n_row = narrative.get(uc, {})
            w1_row = w1.get(uc, {})
            w2_rows = by_uc.get(uc, [])
            m25 = matched_2025.get(uc, {})
            # Flatten w2_rows into one dict for CSV — keep the raw flags
            # JSON, the proposed corrected tags from any w2 agent, and the
            # reasoning(s) concatenated.
            w2_flags = []
            w2_reasonings = []
            w2_tagged_by: list[str] = []
            proposed: dict = {}
            for w2 in w2_rows:
                w2_tagged_by.append(w2["tagged_by_agent"])
                if w2.get("quality_flags_json"):
                    try:
                        w2_flags.extend(json.loads(w2["quality_flags_json"]))
                    except Exception:
                        w2_flags.append(w2["quality_flags_json"])
                if w2.get("reasoning"):
                    w2_reasonings.append(w2["reasoning"])
                # Any non-null tag field in the w2 row is a proposed correction.
                for k in W1_FIELDS:
                    if k in ("reasoning", "confidence"):
                        continue
                    v = w2.get(k)
                    if v is not None and v != "":
                        proposed[f"proposed_{k}"] = v
            row = {
                "use_case_id_2024": uc,
                "agency_abbreviation": n_row.get("agency_abbreviation", ""),
                "bureau": n_row.get("bureau", ""),
                "use_case_name": n_row.get("use_case_name", ""),
                "purpose_benefits": n_row.get("purpose_benefits", ""),
                "outputs": n_row.get("outputs", ""),
                "commercial_ai": n_row.get("commercial_ai", ""),
                "dev_method": n_row.get("dev_method", ""),
                "dev_stage": n_row.get("dev_stage", ""),
                "lineage_status": m25.get("lineage_status", "retired_2024"),
                "w2_tagged_by": "|".join(w2_tagged_by),
                "w2_flags_json": json.dumps(sorted(set(w2_flags))),
                "w2_reasoning": " ; ".join(w2_reasonings),
            }
            # Wave 1 current tags
            for k in W1_FIELDS:
                row[f"wave1_{k}"] = w1_row.get(k, "")
            # Proposed corrections (if any)
            for k in W1_FIELDS:
                key = f"proposed_{k}"
                if key not in proposed and k not in ("reasoning",):
                    row[key] = ""
                else:
                    row[key] = proposed.get(key, "")
            # 2025 mirror
            for k in m25:
                if k.startswith("_"):
                    continue
                row[k] = m25[k]
            rows_out.append(row)

        path = out_dir_w3 / f"{letter}.csv"
        if rows_out:
            fieldnames = list(rows_out[0].keys())
            # All rows have the same keys; the only var is the optional
            # `_additional_matches`. Normalize so every row covers every key.
            all_keys: set[str] = set()
            for r in rows_out:
                all_keys.update(r.keys())
            fieldnames = sorted(all_keys)
            with path.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for r in rows_out:
                    w.writerow({k: r.get(k, "") for k in fieldnames})
        else:
            path.write_text("")
        counts[letter] = len(rows_out)

    # Export the tagging_error_2025 side queue.
    ERROR_2025_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    e25_rows = []
    for r in flagged_rows:
        try:
            flags = json.loads(r["quality_flags_json"] or "[]")
        except Exception:
            flags = []
        if "tagging_error_2025" not in flags:
            continue
        uc = r["use_case_id_2024"]
        m25 = matched_2025.get(uc, {})
        narr = narrative.get(uc, {})
        w1_row = w1.get(uc, {})
        e25_rows.append({
            "use_case_id_2024": uc,
            "uc_2025_id": m25.get("uc_2025_id", ""),
            "agency_abbreviation": narr.get("agency_abbreviation", ""),
            "use_case_name_2024": narr.get("use_case_name", ""),
            "use_case_name_2025": m25.get("name_2025", ""),
            "flagged_by": r["tagged_by_agent"],
            "w2_reasoning": r["reasoning"],
            "wave1_is_generative_ai": w1_row.get("is_generative_ai", ""),
            "wave1_ai_sophistication": w1_row.get("ai_sophistication", ""),
            "wave1_deployment_scope": w1_row.get("deployment_scope", ""),
            "wave1_entry_type": w1_row.get("entry_type", ""),
            "tag2025_is_generative_ai": m25.get("is_generative_ai_2025", ""),
            "tag2025_ai_sophistication": m25.get("ai_sophistication_2025", ""),
            "tag2025_deployment_scope": m25.get("deployment_scope_2025", ""),
            "tag2025_entry_type": m25.get("entry_type_2025", ""),
        })
    if e25_rows:
        with ERROR_2025_QUEUE.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(e25_rows[0].keys()))
            w.writeheader()
            for r in e25_rows:
                w.writerow(r)
    counts["error_2025_queue"] = len(e25_rows)

    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        counts = build(conn, args.out)
    finally:
        conn.close()

    for k, v in counts.items():
        print(f"  {k}: {v} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
