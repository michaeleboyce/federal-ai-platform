"""Load researched AI-access evidence into `agency_ai_access_evidence`.

Reads every `audit/research/ai_access/*.json` file (one per research agent),
validates the shape, resolves agency_id from agency_abbreviation, and
replaces the table contents (idempotent — DELETE then INSERT).

Each JSON file:
{
  "captured_by": "agent1",
  "captured_at": "2026-05-20T12:00:00Z",
  "findings": [
    {
      "agency_abbreviation": "GSA",
      "tool_name": "GSAi",
      "finding": "...",
      "estimated_users": "13000",
      "coverage_assessment": "all",        # all|most|partial|pilot|unknown|none
      "exact_quote": "...",                 # verbatim, or null
      "source_url": "https://...",          # or null
      "source_title": "...",
      "source_date": "2025-06-01",
      "source_type": "press",               # official|press|inventory_field|none
      "confidence": "high",                 # high|medium|low
      "status": "corroborated",             # corroborated|searched_no_source
      "notes": "..."
    }
  ]
}
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db import get_connection  # noqa: E402

RESEARCH_DIR = _ROOT / "audit" / "research" / "ai_access"

# `latent` — a general-purpose chat tool is technically reachable via the
# agency's existing Microsoft 365 licensing (Copilot Chat with commercial
# data protection) but no deliberate agency-wide rollout is documented.
_VALID_STATUS = {"corroborated", "searched_no_source"}
_VALID_COVERAGE = {"all", "most", "partial", "pilot", "latent", "unknown", "none"}
_VALID_CONFIDENCE = {"high", "medium", "low"}
# `primary_attestation` — a first-hand account from a program owner that is
# not (yet) reflected in public reporting.
_VALID_SOURCE_TYPE = {
    "official",
    "press",
    "inventory_field",
    "primary_attestation",
    "none",
}


def _load_files() -> list[dict]:
    if not RESEARCH_DIR.exists():
        raise SystemExit(f"No research directory at {RESEARCH_DIR}")
    files = sorted(RESEARCH_DIR.glob("*.json"))
    if not files:
        raise SystemExit(f"No *.json files in {RESEARCH_DIR}")
    return [json.loads(f.read_text()) for f in files]


def _validate(finding: dict, src_file: str) -> list[str]:
    errs: list[str] = []
    if not finding.get("agency_abbreviation"):
        errs.append(f"{src_file}: finding missing agency_abbreviation")
    if not finding.get("finding"):
        errs.append(f"{src_file}: finding missing 'finding' summary")
    st = finding.get("status")
    if st not in _VALID_STATUS:
        errs.append(f"{src_file}: bad status {st!r}")
    cov = finding.get("coverage_assessment")
    if cov is not None and cov not in _VALID_COVERAGE:
        errs.append(f"{src_file}: bad coverage_assessment {cov!r}")
    conf = finding.get("confidence")
    if conf is not None and conf not in _VALID_CONFIDENCE:
        errs.append(f"{src_file}: bad confidence {conf!r}")
    stype = finding.get("source_type")
    if stype is not None and stype not in _VALID_SOURCE_TYPE:
        errs.append(f"{src_file}: bad source_type {stype!r}")
    # A corroborated row must carry a source URL — unless it rests on a
    # primary attestation (a program owner's first-hand account), which by
    # definition has no public URL.
    if st == "corroborated" and stype != "primary_attestation":
        if not finding.get("source_url"):
            errs.append(f"{src_file}: corroborated finding has no source_url")
    return errs


def main() -> int:
    payloads = _load_files()
    conn = get_connection()
    try:
        # Agency abbreviation -> id (case-insensitive).
        agency_ids = {
            r[0].lower(): r[1]
            for r in conn.execute("SELECT abbreviation, id FROM agencies")
        }

        rows: list[tuple] = []
        errors: list[str] = []
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        for payload in payloads:
            captured_by = payload.get("captured_by", "unknown")
            captured_at = payload.get("captured_at", now)
            for f in payload.get("findings", []):
                errs = _validate(f, captured_by)
                if errs:
                    errors.extend(errs)
                    continue
                abbr = f["agency_abbreviation"]
                rows.append((
                    agency_ids.get(abbr.lower()),
                    abbr,
                    f.get("tool_name"),
                    f["finding"],
                    f.get("estimated_users"),
                    f.get("coverage_assessment"),
                    f.get("exact_quote"),
                    f.get("source_url"),
                    f.get("source_title"),
                    f.get("source_date"),
                    f.get("source_type"),
                    f.get("confidence"),
                    f["status"],
                    f.get("notes"),
                    captured_at,
                    captured_by,
                ))

        if errors:
            print("VALIDATION ERRORS — nothing written:")
            for e in errors:
                print(f"  - {e}")
            return 1

        with conn:
            conn.execute("DELETE FROM agency_ai_access_evidence")
            conn.executemany(
                """
                INSERT INTO agency_ai_access_evidence (
                    agency_id, agency_abbreviation, tool_name, finding,
                    estimated_users, coverage_assessment, exact_quote,
                    source_url, source_title, source_date, source_type,
                    confidence, status, notes, captured_at, captured_by
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                rows,
            )

        corroborated = sum(1 for r in rows if r[12] == "corroborated")
        gaps = sum(1 for r in rows if r[12] == "searched_no_source")
        print(f"Loaded {len(rows)} evidence rows "
              f"({corroborated} corroborated, {gaps} searched-no-source) "
              f"across {len({r[1] for r in rows})} agencies.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
