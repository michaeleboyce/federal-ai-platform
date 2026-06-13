"""Seed the unlinked-AI review CSV: FedRAMP products classified as AI with no
inventory link, plus top-5 inventory-product candidates for curation.

Reads the fedramp_ai_classification table (run
scripts/apply_fedramp_ai_classification.py --apply first) and emits
audit/fedramp_ai_classification/unlinked_review.csv. A curator (human or LLM
agent) fills decision_canonical_name (an EXACT products.canonical_name to
link, or 'none' to confirm the product is genuinely absent from the
inventory) and decision_notes. Accepted rows are then copied into
data/fedramp_link_decisions.csv (canonical_name, fedramp_id, confidence,
source, notes) and applied via scripts/apply_fedramp_link_decisions.py
--apply — the established FedRAMP-first curation path. fedramp_link_queue is
NOT used here: its schema (inventory_id NOT NULL) is inventory-first.

Products that remain unlinked after curation are the true "FedRAMP-authorized
AI, absent from the inventory" population shown on
/fedramp/coverage/unlinked-ai.

Review artifact, not state — not wired into make.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from link_fedramp import (  # noqa: E402
    _load_inventory_products, _score_overlap, _substring_match, _tokenize,
)

DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT_CSV = ROOT / "audit" / "fedramp_ai_classification" / "unlinked_review.csv"

FIELDS = [
    "fedramp_id", "csp", "cso", "category", "confidence", "reasoning",
    "status", "impact_level", "ato_count",
    "candidate_inventory_products",
    "decision_canonical_name", "decision_notes",
]


def candidates_for(fr_combined: str, inv_products: list[dict], k: int = 5) -> str:
    fr_tokens = _tokenize(fr_combined)
    scored = []
    for inv in inv_products:
        best = 0.0
        for phrase in inv["phrases"]:
            s = _score_overlap(_tokenize(phrase), fr_tokens)
            if _substring_match(phrase, fr_combined):
                s = max(s, 0.9)
            best = max(best, s)
        if best >= 0.34:
            scored.append((best, inv["name"]))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return "; ".join(f"{name} ({score:.2f})" for score, name in scored[:k])


def main() -> None:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT c.fedramp_id, p.csp, p.cso, c.category, c.confidence,
               c.reasoning, p.status, p.impact_level,
               (SELECT COUNT(*) FROM fedramp_authorizations a
                 WHERE a.fedramp_id = p.fedramp_id) AS ato_count
          FROM fedramp_ai_classification c
          JOIN fedramp_products p ON p.fedramp_id = c.fedramp_id
         WHERE c.category IN ('core_ai', 'ai_featured')
           AND c.fedramp_id NOT IN
               (SELECT fedramp_id FROM fedramp_product_links)
         ORDER BY ato_count DESC, p.csp, p.cso
        """
    ).fetchall()
    inv_products = _load_inventory_products(conn)
    conn.close()

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({
                **{k: r[k] for k in FIELDS if k in r.keys()},
                "candidate_inventory_products": candidates_for(
                    f"{r['csp']} {r['cso']}", inv_products
                ),
                "decision_canonical_name": "",
                "decision_notes": "",
            })
    print(f"wrote {len(rows)} unlinked AI products -> {OUT_CSV}")


if __name__ == "__main__":
    main()
