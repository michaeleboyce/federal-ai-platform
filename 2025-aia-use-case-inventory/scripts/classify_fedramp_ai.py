"""Per-product AI classification of the FedRAMP marketplace mirror.

Every row in ``fedramp_products`` gets an independent AI-relatedness label so
the dashboard can surface FedRAMP-authorized AI tools that never appear in
any agency AI use case inventory (the existing coverage analysis only sees
FedRAMP products *linked* to inventory products via fedramp_product_links).

Taxonomy (mirrors the dashboard methodology box):
  core_ai      - the product's primary purpose is AI/ML: model hosting, LLM
                 platforms/assistants, CV/NLP/speech services, ML tooling,
                 AI-first analytics.
  ai_featured  - a broader product that ships material AI/ML capability as a
                 feature (security analytics with ML detection, "Copilot in
                 X", document platforms with AI extraction).
  not_ai       - no substantive AI capability; marketing mentions alone do
                 not qualify.

Workflow (repo convention: build inputs -> LLM micro-agent review -> merge ->
idempotent apply; see build_review_queue_llm.py / apply_llm_review.py):

  1. python3 scripts/classify_fedramp_ai.py --export-inputs
       Reads fedramp_products (+ business functions + service models) from
       the inventory DB, computes input_hash per row, skips rows already in
       data/fedramp_ai_classification.csv with a matching hash (incremental
       across marketplace snapshots; --all forces a full re-run), and writes
       batched input JSON to audit/fedramp_ai_classification/inputs/.
  2. LLM micro-agents (Claude agent fan-out) read each inputs/batch_NN.json
       and write results/batch_NN.json rows:
       {fedramp_id, category, confidence, reasoning, signals[]}.
  3. python3 scripts/classify_fedramp_ai.py --merge
       Validates agent output (enums, verbatim-signal spot check, coverage)
       and merges into data/fedramp_ai_classification.csv (sorted by
       fedramp_id for stable diffs). Rows with source='manual_override' in
       the CSV always win over incoming LLM rows.
  4. python3 scripts/apply_fedramp_ai_classification.py --apply
       Loads the CSV into the fedramp_ai_classification table.

This script never writes the DB; the canonical artifact is the CSV, keyed by
the stable fedramp_id (safe across `make fix` id rotations).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "fedramp_ai_classification.csv"
WORK_DIR = ROOT / "audit" / "fedramp_ai_classification"
INPUTS_DIR = WORK_DIR / "inputs"
RESULTS_DIR = WORK_DIR / "results"

BATCH_SIZE = 60

CSV_FIELDS = [
    "fedramp_id", "csp", "cso", "category", "confidence", "reasoning",
    "signals", "model", "input_hash", "classified_at", "source",
]
VALID_CATEGORIES = {"core_ai", "ai_featured", "not_ai"}
VALID_CONFIDENCE = {"high", "medium", "low"}


def input_hash(row: dict) -> str:
    basis = "|".join([
        row.get("csp") or "",
        row.get("cso") or "",
        row.get("service_desc") or "",
        ",".join(sorted(row.get("business_functions") or [])),
    ])
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def load_products(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT p.fedramp_id, p.csp, p.cso, p.status, p.impact_level,
               p.deployment_model, p.service_desc
          FROM fedramp_products p
         ORDER BY p.fedramp_id
        """
    ).fetchall()
    bf: dict[str, list[str]] = {}
    for r in conn.execute(
        "SELECT fedramp_id, function FROM fedramp_business_functions"
    ):
        bf.setdefault(r["fedramp_id"], []).append(r["function"])
    sm: dict[str, list[str]] = {}
    for r in conn.execute(
        "SELECT fedramp_id, model FROM fedramp_service_models"
    ):
        sm.setdefault(r["fedramp_id"], []).append(r["model"])
    out = []
    for r in rows:
        d = dict(r)
        d["business_functions"] = sorted(bf.get(r["fedramp_id"], []))
        d["service_models"] = sorted(sm.get(r["fedramp_id"], []))
        d["input_hash"] = input_hash(d)
        out.append(d)
    return out


def read_csv() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open() as f:
        return {row["fedramp_id"]: row for row in csv.DictReader(f)}


def write_csv(rows: dict[str, dict]) -> None:
    with CSV_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for fid in sorted(rows):
            w.writerow({k: rows[fid].get(k, "") for k in CSV_FIELDS})


def cmd_export_inputs(args) -> None:
    conn = sqlite3.connect(DB_PATH)
    products = load_products(conn)
    conn.close()
    existing = read_csv()
    todo = []
    for p in products:
        prior = existing.get(p["fedramp_id"])
        if prior and prior.get("source") == "manual_override":
            continue  # human decision pinned; never re-classify
        if not args.all and prior and prior.get("input_hash") == p["input_hash"]:
            continue
        todo.append(p)
    n_skipped = len(products) - len(todo)
    if args.limit:
        todo = todo[: args.limit]

    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in INPUTS_DIR.glob("batch_*.json"):
        old.unlink()

    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i: i + BATCH_SIZE]
        path = INPUTS_DIR / f"batch_{i // BATCH_SIZE:02d}.json"
        path.write_text(json.dumps(batch, indent=1))
    n_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE if todo else 0
    print(f"products in DB:        {len(products)}")
    print(f"already classified:    {n_skipped} (hash match or manual_override)")
    print(f"to classify:           {len(todo)} in {n_batches} batch files under {INPUTS_DIR}")


def cmd_merge(args) -> None:
    conn = sqlite3.connect(DB_PATH)
    products = {p["fedramp_id"]: p for p in load_products(conn)}
    conn.close()

    incoming: dict[str, dict] = {}
    errors: list[str] = []
    for path in sorted(RESULTS_DIR.glob("batch_*.json")):
        for row in json.loads(path.read_text()):
            fid = row.get("fedramp_id")
            if fid not in products:
                errors.append(f"{path.name}: unknown fedramp_id {fid!r}")
                continue
            if row.get("category") not in VALID_CATEGORIES:
                errors.append(f"{path.name}: {fid} bad category {row.get('category')!r}")
                continue
            if row.get("confidence") not in VALID_CONFIDENCE:
                errors.append(f"{path.name}: {fid} bad confidence {row.get('confidence')!r}")
                continue
            if not (row.get("reasoning") or "").strip():
                errors.append(f"{path.name}: {fid} empty reasoning")
                continue
            signals = row.get("signals") or []
            desc = products[fid].get("service_desc") or ""
            verbatim = [s for s in signals if s and s in desc]
            incoming[fid] = {
                "fedramp_id": fid,
                "csp": products[fid]["csp"],
                "cso": products[fid]["cso"],
                "category": row["category"],
                "confidence": row["confidence"],
                "reasoning": (row["reasoning"] or "").strip()[:1000],
                "signals": json.dumps(verbatim),
                "model": args.model,
                "input_hash": products[fid]["input_hash"],
                "classified_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "llm",
            }
    if errors:
        print(f"{len(errors)} validation errors:")
        for e in errors[:20]:
            print(" ", e)
        sys.exit(1)

    merged = read_csv()
    skipped_manual = 0
    for fid, row in incoming.items():
        if merged.get(fid, {}).get("source") == "manual_override":
            skipped_manual += 1
            continue
        merged[fid] = row
    # prune rows for products no longer on the marketplace
    pruned = [fid for fid in merged if fid not in products]
    for fid in pruned:
        del merged[fid]
    write_csv(merged)

    classified = len(merged)
    print(f"merged rows:           {len(incoming)} (skipped {skipped_manual} manual_override)")
    print(f"pruned (delisted):     {len(pruned)}")
    print(f"CSV coverage:          {classified}/{len(products)} products")
    cats = {}
    for r in merged.values():
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    for c in sorted(cats):
        print(f"  {c:<12} {cats[c]}")
    if classified < len(products):
        missing = sorted(set(products) - set(merged))
        print(f"MISSING {len(missing)} products (re-run --export-inputs + agents):")
        for fid in missing[:10]:
            print(f"  {fid}  {products[fid]['csp']} / {products[fid]['cso']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--export-inputs", action="store_true")
    g.add_argument("--merge", action="store_true")
    ap.add_argument("--all", action="store_true", help="re-export even hash-matched rows")
    ap.add_argument("--limit", type=int, help="cap exported rows (smoke test)")
    ap.add_argument("--model", default="claude-fable-5",
                    help="model id stamped on merged rows")
    args = ap.parse_args()
    if args.export_inputs:
        cmd_export_inputs(args)
    else:
        cmd_merge(args)


if __name__ == "__main__":
    main()
