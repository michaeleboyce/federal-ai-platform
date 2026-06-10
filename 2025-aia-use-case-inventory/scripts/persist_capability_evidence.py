"""Persist retag-audit sources and quotes into use_case_external_evidence.

The goal: every corrected tag should carry its receipts on the use case
itself — the URL that corroborated it and/or the quoted text that decided
it — so the dashboard's evidence panel and any future fact-check can trace
a finding without digging through audit CSVs.

Sources ingested (all signature-resolved via scripts/uc_signature.py):

  audit/retag/{general_llm,coding,data_analysis}/by_row.csv
      The 2026-04 web-grounded audit. Rows with an http evidence_url
      become status='corroborated' (with evidence_quote as source_quote);
      rows whose evidence is a quote from the inventory's own narrative
      become status='inventory_only'.
      captured_by='retag_2026-04_round1'

  audit/retag/general_llm_round3/verdicts_*.csv
  audit/retag/agentic_review/verdicts_*.csv
      The 2026-06 capability re-reviews. The agent's reasoning (which
      quotes the deciding narrative phrase) is stored in notes; http URLs
      found in the reasoning are lifted into source_url/corroborated.
      captured_by='capability_reviews_2026-06'

Idempotent: clears its own captured_by rows then re-inserts. Wired into
`make fix` after apply_capability_reviews.py.
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uc_signature import Resolver, _norm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
RETAG = ROOT / "audit" / "retag"

ROUND1_BY = "retag_2026-04_round1"
REVIEWS_BY = "capability_reviews_2026-06"
URL_RE = re.compile(r"https?://[^\s\)\]\"']+")


def _insert(conn, uc_id, topic, status, url, quote, confidence, notes, captured_by):
    conn.execute(
        """INSERT INTO use_case_external_evidence
             (use_case_id, topic, status, source_url, source_quote,
              confidence, search_method, captured_at, captured_by, notes)
           VALUES (?, ?, ?, ?, ?, ?, 'retag_audit_csv', ?, ?, ?)""",
        (uc_id, topic, status, url, quote, confidence,
         date.today().isoformat(), captured_by, notes),
    )


def _round1(conn, res: Resolver) -> dict:
    stats = {"corroborated": 0, "inventory_only": 0, "skipped": 0}
    for sub, topic in (("general_llm", "general_llm"), ("coding", "coding"),
                       ("data_analysis", "data_analysis")):
        path = RETAG / sub / "by_row.csv"
        for row in csv.DictReader(open(path)):
            url = (row.get("evidence_url") or "").strip()
            quote = (row.get("evidence_quote") or "").strip()
            notes = (row.get("notes") or "").strip()
            if "-" in (row.get("use_case_id") or ""):  # platform-range rows
                stats["skipped"] += 1
                continue
            if not url.startswith("http") and not quote:
                stats["skipped"] += 1
                continue
            name = (row.get("use_case_name") or "").strip()
            if name.lower().endswith("(consolidated)"):
                stats["skipped"] += 1  # consolidated: no uc evidence target here
                continue
            # Round-1 agents annotated duplicate names with parenthetical
            # disambiguators ("... (Federal Student Aid)") and shorthand the
            # DB doesn't carry. Prefer the variant that actually resolves.
            agency = row.get("agency")
            candidates = [name]
            stripped = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
            if stripped and stripped != name:
                candidates.append(stripped)
            pick = next(
                (c for c in candidates if (_norm(agency), _norm(c)) in res.cur_uc),
                candidates[-1],
            )
            ids = res.uc(None, agency, pick)
            if not ids:
                stats["skipped"] += 1
                continue
            is_web = url.startswith("http")
            for uc_id in ids:
                _insert(
                    conn, uc_id, topic,
                    "corroborated" if is_web else "inventory_only",
                    url if is_web else None, quote[:600] or None,
                    (row.get("confidence") or "").strip().lower() or None,
                    notes[:500] or None, ROUND1_BY,
                )
                stats["corroborated" if is_web else "inventory_only"] += 1
    return stats


def _reviews(conn, res: Resolver) -> dict:
    stats = {"corroborated": 0, "inventory_only": 0, "skipped": 0}
    for directory, topic in ((RETAG / "general_llm_round3", "general_llm_round3"),
                             (RETAG / "agentic_review", "agentic_review")):
        for f in sorted(directory.glob("verdicts_*.csv")):
            for row in csv.DictReader(open(f)):
                reasoning = (row.get("reasoning") or "").strip()
                if not reasoning:
                    stats["skipped"] += 1
                    continue
                ids = res.uc(None, row.get("agency"), row.get("use_case_name"))
                if not ids:
                    stats["skipped"] += 1
                    continue
                m = URL_RE.search(reasoning)
                url = m.group(0).rstrip(".,;") if m else None
                for uc_id in ids:
                    _insert(
                        conn, uc_id, topic,
                        "corroborated" if url else "inventory_only",
                        url, None,
                        (row.get("confidence") or "").strip().lower() or None,
                        reasoning[:500], REVIEWS_BY,
                    )
                    stats["corroborated" if url else "inventory_only"] += 1
    return stats


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        res = Resolver(conn)
        with conn:
            conn.execute(
                "DELETE FROM use_case_external_evidence WHERE captured_by IN (?, ?)",
                (ROUND1_BY, REVIEWS_BY),
            )
            r1 = _round1(conn, res)
            r2 = _reviews(conn, res)
        print("[round1 evidence]  ", r1)
        print("[reviews evidence] ", r2)
        res.check("persist_capability_evidence", max_unresolved=0.05)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
