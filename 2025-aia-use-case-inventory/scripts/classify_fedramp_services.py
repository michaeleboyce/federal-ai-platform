"""Per-service AI classification of FedRAMP "services in scope".

`fedramp_authorized_services` holds the per-package service catalogs from the
marketplace export (e.g. Amazon Bedrock inside the AWS packages, Azure OpenAI
inside Azure Commercial). Each UNIQUE service name gets an AI-relatedness
label so the dashboard can quantify the "shelf inside the shelf": core-AI
services already in scope of packages agencies hold ATOs for.

Taxonomy (same enums as fedramp_ai_classification):
  core_ai      - the service itself is an AI/ML capability: model hosting,
                 LLM platforms/assistants, CV/NLP/speech, ML tooling, agent
                 builders.
  ai_featured  - a broader service that ships material AI/ML capability as a
                 feature.
  not_ai       - no substantive AI capability; marketing mentions alone do
                 not qualify. When unsure, prefer not_ai with low confidence
                 (precision over recall — core_ai rows become article claims).

Workflow (extends the classify_fedramp_ai.py convention with a QC lane):

  1. --export-inputs [--services-file F] [--all] [--limit N]
       Dedupes service names from fedramp_authorized_services, attaches host
       context, hash-skips rows already in the CSV, writes
       audit/fedramp_service_classification/inputs/batch_NN.json.
  2. Labeler micro-agents (cheap model fan-out) write
       results/batch_NN.json: {service, category, confidence, reasoning,
       signals[]}.
  3. --merge [--model M]
       Validates and merges into data/fedramp_service_classification.csv
       with source='llm'.
  4. --export-qc [--seed N]
       Stratified sample from the CSV (100% core_ai + 100% low-confidence +
       25% ai_featured + 10% not_ai) -> qc/inputs/qc_batch_NN.json.
  5. Judge agents (frontier model) write qc/results/qc_batch_NN.json:
       {service, verdict: confirm|overturn, corrected_category?, error_tag?,
       reasoning}.
  6. --apply-qc
       Applies verdicts to the CSV (confirm -> source=qc_confirmed;
       overturn -> corrected category, source=qc_corrected), prints the
       per-labeler-batch overturn rates and per-error_tag rollup that drive
       the correction-loop triggers (batch >10% overturned, or a tag seen
       >=5 times => write a rubric v2 and relabel the affected slice via
       --export-inputs --services-file).

This script never writes the DB; the canonical artifact is the CSV, keyed by
the stable service-name string. The DB apply lives in
scripts/apply_fedramp_service_classification.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
CSV_PATH = ROOT / "data" / "fedramp_service_classification.csv"
WORK_DIR = ROOT / "audit" / "fedramp_service_classification"
INPUTS_DIR = WORK_DIR / "inputs"
RESULTS_DIR = WORK_DIR / "results"
QC_INPUTS_DIR = WORK_DIR / "qc" / "inputs"
QC_RESULTS_DIR = WORK_DIR / "qc" / "results"

BATCH_SIZE = 50
QC_BATCH_SIZE = 40

CSV_FIELDS = [
    "service", "category", "confidence", "reasoning", "signals",
    "model", "input_hash", "classified_at", "source",
]
VALID_CATEGORIES = {"core_ai", "ai_featured", "not_ai"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SOURCES = {"llm", "qc_confirmed", "qc_corrected", "adjudicated", "manual_override"}
VALID_VERDICTS = {"confirm", "overturn"}

# QC sampling rates by stratum (fraction of rows judged).
QC_RATES = {"core_ai": 1.0, "ai_featured": 0.25, "not_ai": 0.10}


def input_hash(service: str, host_ids: list[str]) -> str:
    basis = service + "|" + ",".join(sorted(host_ids))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def load_services(conn: sqlite3.Connection) -> dict[str, dict]:
    """One record per unique service name, with host-package context."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT s.service, s.recency, p.fedramp_id, p.csp, p.cso,
               p.impact_level, p.service_desc
          FROM fedramp_authorized_services s
          JOIN fedramp_products p ON p.fedramp_id = s.fedramp_id
         ORDER BY s.service, p.fedramp_id
        """
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        rec = out.setdefault(r["service"], {
            "service": r["service"],
            "hosts": [],
            "recency": r["recency"],
            "host_service_desc_snippet": (r["service_desc"] or "")[:400],
        })
        rec["hosts"].append({
            "fedramp_id": r["fedramp_id"],
            "csp": r["csp"],
            "cso": r["cso"],
            "impact_level": r["impact_level"],
        })
        if r["recency"] == "last_90":
            rec["recency"] = "last_90"
    for rec in out.values():
        rec["input_hash"] = input_hash(
            rec["service"], [h["fedramp_id"] for h in rec["hosts"]]
        )
    return out


def read_csv() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open() as f:
        return {row["service"]: row for row in csv.DictReader(f)}


def write_csv(rows: dict[str, dict]) -> None:
    with CSV_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for svc in sorted(rows):
            w.writerow({k: rows[svc].get(k, "") for k in CSV_FIELDS})


def cmd_export_inputs(args) -> None:
    conn = sqlite3.connect(DB_PATH)
    services = load_services(conn)
    conn.close()
    if not services:
        print("fedramp_authorized_services is empty — run `make fedramp` first.")
        sys.exit(1)

    restrict: set[str] | None = None
    if args.services_file:
        restrict = {
            line.strip()
            for line in Path(args.services_file).read_text().splitlines()
            if line.strip()
        }
        unknown = restrict - set(services)
        if unknown:
            print(f"services-file names {len(unknown)} unknown services, e.g. "
                  f"{sorted(unknown)[:3]}")
            sys.exit(1)

    existing = read_csv()
    todo = []
    for svc, rec in sorted(services.items()):
        if restrict is not None and svc not in restrict:
            continue
        prior = existing.get(svc)
        if prior and prior.get("source") == "manual_override":
            continue  # human decision pinned; never re-classify
        if restrict is None and not args.all and prior \
                and prior.get("input_hash") == rec["input_hash"]:
            continue
        todo.append(rec)
    n_skipped = len(services) - len(todo)
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
    print(f"unique services in DB: {len(services)}")
    print(f"skipped:               {n_skipped} (hash match, manual_override, or outside --services-file)")
    print(f"to classify:           {len(todo)} in {n_batches} batch files under {INPUTS_DIR}")


def cmd_merge(args) -> None:
    conn = sqlite3.connect(DB_PATH)
    services = load_services(conn)
    conn.close()

    incoming: dict[str, dict] = {}
    errors: list[str] = []
    for path in sorted(RESULTS_DIR.glob("batch_*.json")):
        for row in json.loads(path.read_text()):
            svc = row.get("service")
            if svc not in services:
                errors.append(f"{path.name}: unknown service {svc!r}")
                continue
            if row.get("category") not in VALID_CATEGORIES:
                errors.append(f"{path.name}: {svc} bad category {row.get('category')!r}")
                continue
            if row.get("confidence") not in VALID_CONFIDENCE:
                errors.append(f"{path.name}: {svc} bad confidence {row.get('confidence')!r}")
                continue
            if not (row.get("reasoning") or "").strip():
                errors.append(f"{path.name}: {svc} empty reasoning")
                continue
            signals = [s.strip() for s in (row.get("signals") or []) if s and s.strip()]
            incoming[svc] = {
                "service": svc,
                "category": row["category"],
                "confidence": row["confidence"],
                "reasoning": (row["reasoning"] or "").strip()[:1000],
                "signals": json.dumps(signals[:6]),
                "model": args.model,
                "input_hash": services[svc]["input_hash"],
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
    for svc, row in incoming.items():
        if merged.get(svc, {}).get("source") == "manual_override":
            skipped_manual += 1
            continue
        merged[svc] = row
    pruned = [svc for svc in merged if svc not in services]
    for svc in pruned:
        del merged[svc]
    write_csv(merged)

    print(f"merged rows:           {len(incoming)} (skipped {skipped_manual} manual_override)")
    print(f"pruned (delisted):     {len(pruned)}")
    print(f"CSV coverage:          {len(merged)}/{len(services)} services")
    cats: dict[str, int] = {}
    for r in merged.values():
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    for c in sorted(cats):
        print(f"  {c:<12} {cats[c]}")
    if len(merged) < len(services):
        missing = sorted(set(services) - set(merged))
        print(f"MISSING {len(missing)} services (re-run --export-inputs + agents):")
        for svc in missing[:10]:
            print(f"  {svc}")


def _service_to_batch() -> dict[str, str]:
    """Reconstruct service -> labeler batch file from the persisted inputs."""
    mapping: dict[str, str] = {}
    for path in sorted(INPUTS_DIR.glob("batch_*.json")):
        for rec in json.loads(path.read_text()):
            mapping[rec["service"]] = path.name
    return mapping


def cmd_export_qc(args) -> None:
    merged = read_csv()
    if not merged:
        print("CSV is empty — run --merge first.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    services = load_services(conn)
    conn.close()

    rng = random.Random(args.seed)
    sample: list[dict] = []
    for svc in sorted(merged):
        row = merged[svc]
        if row.get("source") not in ("llm",):
            continue  # already QC'd / adjudicated / pinned
        rate = QC_RATES.get(row["category"], 1.0)
        if row.get("confidence") == "low" or rate >= 1.0 or rng.random() < rate:
            ctx = services.get(svc, {})
            sample.append({
                "service": svc,
                "label": {
                    "category": row["category"],
                    "confidence": row["confidence"],
                    "reasoning": row["reasoning"],
                    "signals": row["signals"],
                },
                "hosts": ctx.get("hosts", []),
                "recency": ctx.get("recency"),
                "host_service_desc_snippet": ctx.get("host_service_desc_snippet", ""),
            })

    QC_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    QC_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in QC_INPUTS_DIR.glob("qc_batch_*.json"):
        old.unlink()
    for i in range(0, len(sample), QC_BATCH_SIZE):
        batch = sample[i: i + QC_BATCH_SIZE]
        path = QC_INPUTS_DIR / f"qc_batch_{i // QC_BATCH_SIZE:02d}.json"
        path.write_text(json.dumps(batch, indent=1))
    n_batches = (len(sample) + QC_BATCH_SIZE - 1) // QC_BATCH_SIZE if sample else 0
    strata: dict[str, int] = {}
    for s in sample:
        strata[s["label"]["category"]] = strata.get(s["label"]["category"], 0) + 1
    print(f"QC sample:             {len(sample)} rows in {n_batches} batches under {QC_INPUTS_DIR}")
    for c in sorted(strata):
        print(f"  {c:<12} {strata[c]}")


def cmd_apply_qc(args) -> None:
    merged = read_csv()
    batch_of = _service_to_batch()

    verdicts: dict[str, dict] = {}
    errors: list[str] = []
    for path in sorted(QC_RESULTS_DIR.glob("qc_batch_*.json")):
        for row in json.loads(path.read_text()):
            svc = row.get("service")
            if svc not in merged:
                errors.append(f"{path.name}: unknown service {svc!r}")
                continue
            if row.get("verdict") not in VALID_VERDICTS:
                errors.append(f"{path.name}: {svc} bad verdict {row.get('verdict')!r}")
                continue
            if row["verdict"] == "overturn" and \
                    row.get("corrected_category") not in VALID_CATEGORIES:
                errors.append(f"{path.name}: {svc} overturn without valid corrected_category")
                continue
            if not (row.get("reasoning") or "").strip():
                errors.append(f"{path.name}: {svc} empty reasoning")
                continue
            verdicts[svc] = row
    if errors:
        print(f"{len(errors)} validation errors:")
        for e in errors[:20]:
            print(" ", e)
        sys.exit(1)

    overturns_by_batch: dict[str, list[int]] = {}
    tag_counts: dict[str, int] = {}
    n_confirm = n_overturn = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for svc, v in verdicts.items():
        row = merged[svc]
        batch = batch_of.get(svc, "?")
        judged, overturned = overturns_by_batch.setdefault(batch, [0, 0])
        overturns_by_batch[batch][0] = judged + 1
        if v["verdict"] == "confirm":
            n_confirm += 1
            row["source"] = "qc_confirmed"
        else:
            n_overturn += 1
            overturns_by_batch[batch][1] = overturned + 1
            tag = (v.get("error_tag") or "untagged").strip()
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            row["category"] = v["corrected_category"]
            row["reasoning"] = (
                f"[QC overturn: {v['reasoning'].strip()}] "
                f"Original: {row['reasoning']}"
            )[:1000]
            row["source"] = "qc_corrected"
        row["classified_at"] = now
    write_csv(merged)

    total = n_confirm + n_overturn
    rate = (n_overturn / total * 100) if total else 0.0
    print(f"verdicts applied:      {total} (confirm {n_confirm} / overturn {n_overturn}, {rate:.1f}%)")
    print("per-labeler-batch overturn rates (correction trigger: >10%):")
    hot_batches = []
    for batch in sorted(overturns_by_batch):
        judged, overturned = overturns_by_batch[batch]
        pct = overturned / judged * 100 if judged else 0.0
        flag = "  <-- TRIGGER" if pct > 10 and judged >= 5 else ""
        if flag:
            hot_batches.append(batch)
        print(f"  {batch:<16} {overturned}/{judged} ({pct:.0f}%){flag}")
    print("per-error_tag rollup (correction trigger: >=5):")
    hot_tags = []
    for tag in sorted(tag_counts, key=tag_counts.get, reverse=True):
        flag = "  <-- TRIGGER" if tag_counts[tag] >= 5 else ""
        if flag:
            hot_tags.append(tag)
        print(f"  {tag:<32} {tag_counts[tag]}{flag}")
    if hot_batches or hot_tags:
        print("CORRECTION LOOP REQUIRED: write corrections/rubric_v2.md, relabel the "
              "affected slice via --export-inputs --services-file, re-QC at 100%.")
    else:
        print("No correction triggers fired.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--export-inputs", action="store_true")
    g.add_argument("--merge", action="store_true")
    g.add_argument("--export-qc", action="store_true")
    g.add_argument("--apply-qc", action="store_true")
    ap.add_argument("--all", action="store_true", help="re-export even hash-matched rows")
    ap.add_argument("--limit", type=int, help="cap exported rows (smoke test)")
    ap.add_argument("--services-file",
                    help="newline-delimited service names to restrict --export-inputs (correction rounds)")
    ap.add_argument("--seed", type=int, default=20260703,
                    help="RNG seed for the QC stratified sample")
    ap.add_argument("--model", default="claude-sonnet-5",
                    help="model id stamped on merged rows")
    args = ap.parse_args()
    if args.export_inputs:
        cmd_export_inputs(args)
    elif args.merge:
        cmd_merge(args)
    elif args.export_qc:
        cmd_export_qc(args)
    else:
        cmd_apply_qc(args)


if __name__ == "__main__":
    main()
