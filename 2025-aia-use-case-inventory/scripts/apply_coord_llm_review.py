"""Apply coordinator-dispatched LLM review results to the B and D queues.

Reads /tmp/batches/b_{1..5}_results.json and /tmp/batches/d_{1..5}_results.json
produced by the coordinator-spawned micro-agent fan-out, writes results back
to review_queue_llm and review_queue_products, and auto-applies at medium/high
confidence per the plan's apply rule (heuristic ↔ LLM agreement required for
auto-apply; high-confidence LLM disagreements also override heuristic for B).

Run from 2025-aia-use-case-inventory/: `python scripts/apply_coord_llm_review.py`
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "federal_ai_inventory_2025.db"
BATCH_DIR = Path("/tmp/batches")
PROPOSED_ALIASES = REPO / "audit" / "proposed_aliases.csv"


def load_batches(prefix: str, n: int = 5) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        path = BATCH_DIR / f"{prefix}_{i}_results.json"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        rows.extend(json.loads(path.read_text()))
    return rows


def apply_b(conn: sqlite3.Connection) -> dict:
    results = load_batches("b")
    agree = disagree_high = disagree_other = 0
    applied = 0
    for r in results:
        uc_id = r["id"]
        label = r["label"]
        conf = r["confidence"]
        reasoning = r.get("reasoning", "")[:500]
        conn.execute(
            "UPDATE review_queue_llm SET llm_label=?, llm_confidence=?, llm_reasoning=? WHERE use_case_id=?",
            (label, conf, reasoning, uc_id),
        )
        heur = conn.execute(
            "SELECT heuristic_label FROM review_queue_llm WHERE use_case_id=?", (uc_id,)
        ).fetchone()
        if heur is None:
            continue
        heur = heur[0]
        # Apply rule
        should_apply = False
        if conf in ("high", "medium") and heur == label:
            should_apply = True
            agree += 1
        elif conf == "high" and heur != label:
            # High-confidence LLM overrides heuristic
            should_apply = True
            disagree_high += 1
        else:
            disagree_other += 1
        if should_apply:
            conn.execute(
                "UPDATE use_case_tags SET is_general_llm_access=? WHERE use_case_id=?",
                (label, uc_id),
            )
            conn.execute(
                "UPDATE review_queue_llm SET applied=1, applied_at=datetime('now') WHERE use_case_id=?",
                (uc_id,),
            )
            applied += 1
    return {
        "reviewed": len(results),
        "agree_applied": agree,
        "disagree_high_applied": disagree_high,
        "disagree_other_kept_heuristic": disagree_other,
        "applied": applied,
    }


def apply_d(conn: sqlite3.Connection) -> dict:
    results = load_batches("d")
    applied_link = 0
    proposals = []
    for r in results:
        qid = r["queue_id"]
        matched = r.get("matched_product_ids") or []
        conf = r.get("confidence", "low")
        reasoning = r.get("reasoning", "")[:500]
        conn.execute(
            """UPDATE review_queue_products
               SET llm_reviewed=1, llm_proposed_product_ids=?, llm_confidence=?, llm_reasoning=?
               WHERE id=?""",
            (json.dumps(matched), conf, reasoning, qid),
        )
        # Apply matched products at medium/high confidence into use_case_products
        if conf in ("high", "medium") and matched:
            row = conn.execute(
                "SELECT use_case_id, consolidated_use_case_id, source_text FROM review_queue_products WHERE id=?",
                (qid,),
            ).fetchone()
            if row:
                uc_id, cons_id, src = row
                if uc_id:  # only use_case_products has no consolidated path; skip consolidated for now
                    for pid in matched:
                        conn.execute(
                            """INSERT OR IGNORE INTO use_case_products
                               (use_case_id, product_id, evidence_text, confidence)
                               VALUES (?, ?, ?, ?)""",
                            (uc_id, pid, src[:300] if src else None,
                             "strong" if conf == "high" else "inferred"),
                        )
                    applied_link += 1
        prop = r.get("proposed_new_product")
        if prop:
            proposals.append({
                "queue_id": qid,
                "name": prop.get("name", ""),
                "vendor": prop.get("vendor", ""),
                "alias_text": prop.get("alias_text", ""),
                "confidence": conf,
                "reasoning": reasoning,
            })
    # Write proposals to CSV (append or create header)
    header = ["queue_id", "proposed_name", "vendor", "alias_text", "confidence", "reasoning"]
    existing_ids = set()
    if PROPOSED_ALIASES.exists() and PROPOSED_ALIASES.stat().st_size > 0:
        with PROPOSED_ALIASES.open() as f:
            reader = csv.DictReader(f)
            existing_ids = {int(row["queue_id"]) for row in reader if row.get("queue_id", "").isdigit()}
    write_header = not PROPOSED_ALIASES.exists() or PROPOSED_ALIASES.stat().st_size == 0
    with PROPOSED_ALIASES.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        for p in proposals:
            if p["queue_id"] in existing_ids:
                continue
            w.writerow([p["queue_id"], p["name"], p["vendor"], p["alias_text"],
                        p["confidence"], p["reasoning"]])
    return {
        "reviewed": len(results),
        "linked_use_case_products": applied_link,
        "proposed_new_aliases": len(proposals),
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    b_stats = apply_b(conn)
    d_stats = apply_d(conn)
    conn.commit()
    conn.close()
    print("=== B (LLM) ===")
    for k, v in b_stats.items():
        print(f"  {k}: {v}")
    print("=== D (Products) ===")
    for k, v in d_stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
