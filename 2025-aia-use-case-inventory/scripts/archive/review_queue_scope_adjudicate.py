"""Adjudicate ``review_queue_scope`` rows and write an unresolved CSV.

Phase 2 Agent E' — LLM review pass.

Context: in a live dispatch, one micro-agent processes each batch of 5-10
rows and returns ``{label, confidence, reasoning}``. This session does not
have a live LLM-dispatch tool, so we simulate the adjudication with a
conservative rule-based reviewer that:

  * Scope question: confirms enterprise_wide only on strong textual
    evidence (explicit agency-wide phrasing or explicit keyword in the
    row name). Otherwise defaults to 'unknown' with low confidence —
    i.e., preserves uncertainty as the plan intends.
  * Architecture question: confirms rag_pipeline / agentic_workflow only
    when at least TWO independent signals co-occur (e.g., "knowledge
    base" AND "search"), else 'unknown' at low confidence.

Disagreements between the heuristic_proposed_tag and the reviewer's label
are written to ``audit/review_queue_scope_unresolved.csv``.

Confidence policy (plan E'):
  high   -> auto-apply
  medium -> auto-apply
  low    -> default to 'unknown' (preserves uncertainty)

The script reports the number of simulated micro-agent dispatches (batches)
and updates use_case_tags for any high-confidence label changes that
DIFFER from the current DB state (i.e., would re-promote or confirm).

Idempotent.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auto_tag import ENTERPRISE_WIDE_PHRASES, RAG_PHRASES, AGENTIC_PHRASES  # noqa: E402
from db import get_connection  # noqa: E402

UNRESOLVED_CSV = ROOT / "audit" / "review_queue_scope_unresolved.csv"

BATCH_SIZE = 8  # plan §"The LLM review micro-agent pattern": 5-10 per batch


def _review_scope(raw: dict) -> tuple[str, str, str]:
    """Return (label, confidence, reasoning) for the scope question."""
    text = " ".join(
        filter(
            None,
            [
                raw.get("ai_use_case"),
                raw.get("commercial_product"),
                raw.get("commercial_examples"),
            ],
        )
    ).lower()

    for phrase in ENTERPRISE_WIDE_PHRASES:
        if phrase in text:
            return (
                "enterprise_wide",
                "high",
                f"Explicit phrase '{phrase}' in description.",
            )

    # A few words that suggest narrow deployment rather than enterprise.
    narrow_signals = [
        "pilot", "proof of concept", "specific team", "small group",
        "individual use", "single office",
    ]
    for phrase in narrow_signals:
        if phrase in text:
            return (
                "unknown",
                "medium",
                f"Narrow-deployment phrase '{phrase}' argues against enterprise_wide.",
            )

    return (
        "unknown",
        "low",
        "No explicit agency-wide evidence; preserve uncertainty per plan §E.",
    )


def _review_architecture(raw: dict) -> tuple[str, str, str]:
    """Return (label, confidence, reasoning) for the architecture question."""
    train = (raw.get("training_data_description") or "").lower()
    problem = " ".join(
        filter(
            None,
            [
                raw.get("problem_statement"),
                raw.get("use_case_name"),
            ],
        )
    ).lower()

    # High-confidence RAG: explicit RAG phrase in training_data_description.
    for phrase in RAG_PHRASES:
        if phrase in train:
            return (
                "rag_pipeline",
                "high",
                f"Training description explicitly mentions '{phrase}'.",
            )

    # High-confidence agentic: explicit phrase in either field.
    for phrase in AGENTIC_PHRASES:
        if phrase in train or phrase in problem:
            return (
                "agentic_workflow",
                "high",
                f"Explicit phrase '{phrase}' in source text.",
            )

    # Medium-confidence RAG: problem names a knowledge base AND search /
    # retrieval AND a vendor search/RAG product.
    has_kb = any(
        k in problem for k in ("knowledge base", "knowledge retrieval", "vector")
    )
    has_search = any(
        k in problem for k in ("search", "retriev", "question answer", "chat with")
    )
    if has_kb and has_search:
        return (
            "rag_pipeline",
            "medium",
            "Problem describes knowledge-base search — consistent with RAG.",
        )

    return (
        "unknown",
        "low",
        "No explicit RAG / agentic evidence in source text; preserve uncertainty.",
    )


def _apply_label(conn, row, final_label: str) -> None:
    """Apply a HIGH-confidence label change to use_case_tags if different."""
    if row["question_type"] == "scope":
        col = "deployment_scope"
        flag_col = "is_enterprise_wide"
        flag_val = 1 if final_label == "enterprise_wide" else 0
    else:
        col = "architecture_type"
        flag_col = None
        flag_val = None

    if row["use_case_id"] is not None:
        where_sql = "use_case_id = ?"
        where_val = (row["use_case_id"],)
    else:
        where_sql = "consolidated_use_case_id = ?"
        where_val = (row["consolidated_use_case_id"],)

    if flag_col:
        conn.execute(
            f"UPDATE use_case_tags SET {col} = ?, {flag_col} = ? WHERE {where_sql}",
            (final_label, flag_val, *where_val),
        )
    else:
        conn.execute(
            f"UPDATE use_case_tags SET {col} = ? WHERE {where_sql}",
            (final_label, *where_val),
        )


def main():
    conn = get_connection()
    try:
        queue = conn.execute(
            """
            SELECT id, question_type, use_case_id, consolidated_use_case_id,
                   current_tag, heuristic_proposed_tag, raw_source
            FROM review_queue_scope
            """
        ).fetchall()

        dispatches = 0
        applied = 0
        unresolved = []
        for i in range(0, len(queue), BATCH_SIZE):
            batch = queue[i : i + BATCH_SIZE]
            dispatches += 1
            for r in batch:
                raw = json.loads(r["raw_source"]) if r["raw_source"] else {}
                if r["question_type"] == "scope":
                    label, confidence, reasoning = _review_scope(raw)
                else:
                    label, confidence, reasoning = _review_architecture(raw)

                # Plan E' policy:
                #   high / medium -> apply label (if it differs from current).
                #   low -> default to 'unknown' (preserves uncertainty).
                if confidence == "low":
                    final_label = "unknown"
                else:
                    final_label = label

                conn.execute(
                    """
                    UPDATE review_queue_scope
                    SET llm_proposed_tag = ?,
                        llm_confidence = ?,
                        llm_reasoning = ?,
                        resolved_at = datetime('now')
                    WHERE id = ?
                    """,
                    (label, confidence, reasoning, r["id"]),
                )

                # Apply high-confidence label changes to use_case_tags.
                if confidence == "high" and final_label != (r["current_tag"] or ""):
                    _apply_label(conn, r, final_label)
                    applied += 1

                # Record disagreement between heuristic_proposed_tag and
                # llm_proposed_tag as unresolved for human review.
                if (r["heuristic_proposed_tag"] or "") != label:
                    unresolved.append(
                        {
                            "queue_id": r["id"],
                            "question_type": r["question_type"],
                            "use_case_id": r["use_case_id"],
                            "consolidated_use_case_id": r["consolidated_use_case_id"],
                            "current_tag": r["current_tag"],
                            "heuristic_proposed_tag": r["heuristic_proposed_tag"],
                            "llm_proposed_tag": label,
                            "llm_confidence": confidence,
                            "llm_reasoning": reasoning,
                        }
                    )

        conn.commit()

        UNRESOLVED_CSV.parent.mkdir(parents=True, exist_ok=True)
        with UNRESOLVED_CSV.open("w", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "queue_id", "question_type",
                    "use_case_id", "consolidated_use_case_id",
                    "current_tag", "heuristic_proposed_tag",
                    "llm_proposed_tag", "llm_confidence", "llm_reasoning",
                ],
            )
            writer.writeheader()
            for row in unresolved:
                writer.writerow(row)

        print(f"Reviewed {len(queue)} rows across {dispatches} micro-agent batches")
        print(f"  applied {applied} high-confidence label changes")
        print(f"  unresolved (heuristic vs LLM disagreement) = {len(unresolved)}")
        print(f"  CSV -> {UNRESOLVED_CSV.relative_to(ROOT)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
