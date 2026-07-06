"""Apply the round-2 review micro-agent results back to the DB.

Reads audit/.review2/p_{1..6}_results.json (product linkage),
audit/.review2/e_{1..5}_results.json (entry_type),
audit/.review2/h_{1..2}_results.json (alias hold dispositions).

Apply rules:
- P: match at confidence in {high, medium} -> INSERT OR IGNORE into
  use_case_products. Proposed new products accumulate in
  audit/proposed_aliases_round2.csv for human approval (same conservative
  gate as round 1).
- E: at confidence in {high, medium} -> UPDATE use_case_tags.entry_type;
  mark applied=1 in review_queue_entry_type. Low-conf left pending.
- H: seed_now -> move queue row to a new audit/proposed_aliases_seed_now_r2.csv;
  reject -> keep in reject file; still_hold -> keep in hold.

Idempotent; safe to re-run.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "federal_ai_inventory_2025.db"
BATCH = REPO / "audit" / ".review2"
PROPOSED = REPO / "audit" / "proposed_aliases_round2.csv"


def load_batches(prefix: str, n: int) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        path = BATCH / f"{prefix}_{i}_results.json"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        rows.extend(json.loads(path.read_text()))
    return rows


def apply_p(conn: sqlite3.Connection) -> dict:
    results = load_batches("p", 6)
    linked = 0
    proposals: list[dict] = []
    for r in results:
        qid = r["queue_id"]
        matched = r.get("matched_product_ids") or []
        conf = r.get("confidence", "low")
        reasoning = r.get("reasoning", "")[:500]
        # Update queue row
        conn.execute(
            """UPDATE review_queue_products
               SET llm_reviewed=1, llm_proposed_product_ids=?, llm_confidence=?, llm_reasoning=?
               WHERE id=?""",
            (json.dumps(matched), conf, reasoning, qid),
        )
        # Apply matches at medium/high confidence
        if conf in ("high", "medium") and matched:
            row = conn.execute(
                "SELECT use_case_id, consolidated_use_case_id, source_text FROM review_queue_products WHERE id=?",
                (qid,),
            ).fetchone()
            if row and row[0]:  # only use_case_products, skip consolidated
                uc_id, _, src = row
                for pid in matched:
                    conn.execute(
                        """INSERT OR IGNORE INTO use_case_products
                           (use_case_id, product_id, evidence_text, confidence)
                           VALUES (?, ?, ?, ?)""",
                        (uc_id, pid, src[:300] if src else None,
                         "strong" if conf == "high" else "inferred"),
                    )
                linked += 1
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
    # Append proposals to round2 CSV
    header = ["queue_id", "proposed_name", "vendor", "alias_text", "confidence", "reasoning"]
    write_header = not PROPOSED.exists() or PROPOSED.stat().st_size == 0
    with PROPOSED.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        for p in proposals:
            w.writerow([p["queue_id"], p["name"], p["vendor"], p["alias_text"], p["confidence"], p["reasoning"]])
    return {"reviewed": len(results), "linked_use_case_products": linked, "proposed_new_products": len(proposals)}


def apply_e(conn: sqlite3.Connection) -> dict:
    results = load_batches("e", 5)
    applied = 0
    for r in results:
        uc_id = r["id"]
        label = r["label"]
        conf = r.get("confidence", "low")
        reasoning = r.get("reasoning", "")[:500]
        conn.execute(
            "UPDATE review_queue_entry_type SET llm_label=?, llm_confidence=?, llm_reasoning=? WHERE use_case_id=?",
            (label, conf, reasoning, uc_id),
        )
        if conf in ("high", "medium"):
            conn.execute(
                "UPDATE use_case_tags SET entry_type=? WHERE use_case_id=?",
                (label, uc_id),
            )
            conn.execute(
                "UPDATE review_queue_entry_type SET applied=1 WHERE use_case_id=?",
                (uc_id,),
            )
            applied += 1
    return {"reviewed": len(results), "applied": applied}


def apply_h(conn: sqlite3.Connection) -> dict:
    """Move hold-file rows based on h_*_results.json dispositions."""
    results = load_batches("h", 2)
    # Load current hold CSV
    hold_path = REPO / "audit" / "proposed_aliases_hold.csv"
    seed_path = REPO / "audit" / "proposed_aliases_seed_now.csv"
    reject_path = REPO / "audit" / "proposed_aliases_reject.csv"
    with hold_path.open() as f:
        hold_rows = list(csv.DictReader(f))
    # Build disposition map by queue_id
    dispo = {str(r["queue_id"]): r for r in results}
    remaining_hold, new_seed, new_reject = [], [], []
    for row in hold_rows:
        qid = str(row.get("queue_id", ""))
        d = dispo.get(qid)
        if not d:
            remaining_hold.append(row)
            continue
        if d["disposition"] == "seed_now":
            row["review_disposition"] = "seed_now"
            row["llm_reasoning"] = d.get("reasoning", row.get("llm_reasoning", ""))[:500]
            new_seed.append(row)
        elif d["disposition"] == "reject":
            row["review_disposition"] = "reject"
            row["llm_reasoning"] = d.get("reasoning", row.get("llm_reasoning", ""))[:500]
            new_reject.append(row)
        else:  # still_hold
            remaining_hold.append(row)
    # Write back. Append seed and reject (don't truncate existing).
    fieldnames = hold_rows[0].keys() if hold_rows else []

    def append_rows(path: Path, rows: list[dict]) -> int:
        if not rows:
            return 0
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(fieldnames))
            if write_header:
                w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fieldnames})
        return len(rows)

    # Rewrite hold with only still_hold rows
    with hold_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames))
        w.writeheader()
        for r in remaining_hold:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    sn = append_rows(seed_path, new_seed)
    rj = append_rows(reject_path, new_reject)
    return {
        "reviewed": len(results),
        "kept_hold": len(remaining_hold),
        "moved_to_seed_now": sn,
        "moved_to_reject": rj,
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    p_stats = apply_p(conn)
    e_stats = apply_e(conn)
    h_stats = apply_h(conn)
    conn.commit()
    conn.close()
    print("=== P (products) ===")
    for k, v in p_stats.items(): print(f"  {k}: {v}")
    print("=== E (entry_type) ===")
    for k, v in e_stats.items(): print(f"  {k}: {v}")
    print("=== H (alias holds) ===")
    for k, v in h_stats.items(): print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
