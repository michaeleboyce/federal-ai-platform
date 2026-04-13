"""Populate ``review_queue_llm`` with ambiguous rows for LLM micro-agent review.

Ambiguous rows are:
  - the remaining canonical false positives (is_general_llm_access=1
    AND ai_classification indicates classical/predictive/CV)
  - rows with is_general_llm_access=1 AND blank ai_classification
  - rows whose is_general_llm_access flag flipped between the pre-remediation
    baseline snapshot and the current heuristic value (we detect this by
    recomputing infer_llm_flag and comparing against the stored flag -- after
    retag_llm.py has run, flips are zero, so we also pull the original
    baselines: any row whose current flag differs from what the OLD heuristic
    produced).

For simplicity, we populate:
  - every row matching the canonical FP SQL (small)
  - every row with is_general_llm_access=1 and blank ai_classification
  - every row we explicitly flipped (we re-derive by running infer_llm_flag
    again: rows where the "naive" ai_sophistication-based flag disagrees
    with the new infer_llm_flag are candidates).
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auto_tag import (  # noqa: E402
    LLM_KEYWORDS, AGENTIC_KEYWORDS,
    infer_llm_flag, load_products, load_product_aliases,
    match_product, keyword_any, normalize,
)

DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS review_queue_llm (
    use_case_id INTEGER PRIMARY KEY REFERENCES use_cases(id),
    heuristic_label INTEGER NOT NULL,
    confidence_source TEXT NOT NULL DEFAULT 'heuristic',
    llm_label INTEGER,
    llm_confidence TEXT,
    llm_reasoning TEXT,
    applied INTEGER DEFAULT 0,
    applied_at TEXT
)
"""


def old_heuristic_flag(row, product_id, products_dict):
    """Reproduce the *old* is_general_llm_access logic (pre-B).

    Old rule was:
        ai_soph in ('general_llm','coding_assistant','agentic') -> 1 else 0
    where ai_soph came from infer_ai_sophistication using broad LLM_KEYWORDS.
    We reproduce the decision surface here so we can detect flipped rows.
    """
    ai_class = normalize(row.get("ai_classification") or "")
    name_prob = normalize(
        (row.get("use_case_name") or "") + " "
        + (row.get("problem_statement") or "")
    )

    if product_id:
        prod = products_dict.get(product_id, {})
        ptype = prod.get("product_type", "")
        if ptype == "coding_assistant":
            return 1
        if ptype == "general_llm":
            return 1

    if "agentic" in ai_class or keyword_any(name_prob, AGENTIC_KEYWORDS):
        return 1
    if "generative" in ai_class or keyword_any(name_prob, LLM_KEYWORDS):
        return 1
    return 0


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(CREATE_TABLE_SQL)
        # Only clear heuristic-only rows; preserve any LLM-reviewed rows.
        conn.execute(
            "DELETE FROM review_queue_llm "
            "WHERE llm_label IS NULL AND applied = 0"
        )
        conn.commit()

        aliases_dict = load_product_aliases(conn)
        products_dict = load_products(conn)

        # All candidate rows: anything that could plausibly be wrong.
        # We pull every individual use case (consolidated rows don't have
        # ai_classification, so they're handled separately by ai_soph).
        rows = conn.execute(
            """
            SELECT t.use_case_id, t.is_general_llm_access,
                   u.ai_classification, u.vendor_name, u.use_case_name,
                   u.problem_statement, u.development_type, u.system_name,
                   u.product_id
            FROM use_case_tags t
            JOIN use_cases u ON u.id = t.use_case_id
            """
        ).fetchall()

        # Bucket by reason so we can cap independently (plan caps at 250).
        priority_rows = {}  # canonical FP + blank-class LLM: always include
        flip_rows = {}      # heuristic disagreement: sample if over cap

        for r in rows:
            row_dict = dict(r)
            product_id = r["product_id"]
            if product_id is None:
                search_text = " ".join([
                    r["use_case_name"] or "",
                    r["vendor_name"] or "",
                    r["system_name"] or "",
                    r["problem_statement"] or "",
                ])
                product_id = match_product(search_text, aliases_dict, products_dict)

            new_flag = infer_llm_flag(row_dict, product_id, products_dict)
            old_flag = old_heuristic_flag(row_dict, product_id, products_dict)
            stored = r["is_general_llm_access"]

            ai_class = (r["ai_classification"] or "").strip()
            is_canonical_fp = (
                stored == 1 and ai_class and (
                    "Classical" in ai_class or "Predictive" in ai_class
                    or "Computer Vision" in ai_class
                )
            )
            is_blank_class_llm = stored == 1 and not ai_class
            is_flip = new_flag != old_flag

            if is_canonical_fp or is_blank_class_llm:
                priority_rows[r["use_case_id"]] = stored
            elif is_flip:
                flip_rows[r["use_case_id"]] = stored

        CAP = 250
        priority_ids = list(priority_rows.keys())
        remaining = CAP - len(priority_ids)
        # Deterministic sampling by use_case_id.
        flip_ids_sorted = sorted(flip_rows.keys())
        if remaining > 0 and len(flip_ids_sorted) > remaining:
            # Even stride sample to cover the range.
            step = len(flip_ids_sorted) / remaining
            sampled = [flip_ids_sorted[int(i * step)] for i in range(remaining)]
            flip_ids = sampled
        else:
            flip_ids = flip_ids_sorted

        seen = {}
        for uc_id in priority_ids:
            seen[uc_id] = priority_rows[uc_id]
        for uc_id in flip_ids:
            seen[uc_id] = flip_rows[uc_id]

        conn.executemany(
            "INSERT OR REPLACE INTO review_queue_llm "
            "(use_case_id, heuristic_label, confidence_source) "
            "VALUES (?, ?, 'heuristic')",
            [(uc, flag) for uc, flag in seen.items()],
        )
        conn.commit()

        total = conn.execute(
            "SELECT COUNT(*) FROM review_queue_llm"
        ).fetchone()[0]
        by_label = conn.execute(
            "SELECT heuristic_label, COUNT(*) FROM review_queue_llm "
            "GROUP BY heuristic_label"
        ).fetchall()
        print(f"review_queue_llm populated: {total} rows")
        for r in by_label:
            print(f"  heuristic_label={r[0]}: {r[1]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
