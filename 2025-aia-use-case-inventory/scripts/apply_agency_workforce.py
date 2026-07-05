"""Load researched agency workforce + AI-eligible-share data.

Reads every `audit/research/agency_workforce/W*.json` file (one per Wave-1
or Wave-3 agent) and every `wave-2-*.json` (Wave-2 share-of-eligible
updates), plus the priors at `audit/research/agency_workforce/priors.json`.

Writes to:
- `agency_workforce_profile` — WIPE-AND-RELOAD, one row per organization
  slug, latest wave wins (Wave 3 supersedes Wave 1). Organizations matched
  by `federal_organizations.slug` at apply time. The wipe matters:
  `seed_federal_hierarchy.py` re-keys `federal_organizations` ids every
  `make fix`, so rows written against a previous generation of ids are
  orphans — upserting on organization_id used to double the table on every
  re-run instead of replacing it.
- `agency_occupation_counts` — WIPE-AND-RELOAD from the `occupations`
  payload (FedScope occupational-series caps for seat-model role strata).
- `agency_ai_access_evidence` — populates `estimated_share_of_eligible`,
  `share_rationale`, `matrix_product_key` on existing rows.

Wave-1/Wave-3 JSON shape:
{
  "captured_by": "W1-A",
  "captured_at": "2026-05-26T03:30:00Z",
  "rows": [
    {
      "organization_slug": "va",
      "level": "agency",                   # or "bureau"
      "total_headcount": 470000,
      "headcount_as_of": "2025-09-30",
      "headcount_source_url": "...",
      "headcount_source_title": "...",
      "headcount_quote": "...",
      "ai_eligible_share": 0.30,
      "ai_eligible_rationale": "...",
      "ai_eligible_source_url": "...",
      "confidence": "medium",
      "wave": "1",
      "notes": "...",
      "contractor_headcount": 95000,          # optional (Wave 3+)
      "denominator_basis": "incl_contractors" # optional (Wave 3+)
    }
  ]
}

Occupations JSON shape (may share a file with `rows` or stand alone):
{
  "captured_by": "W3-occ",
  "captured_at": "2026-07-05T00:00:00Z",
  "occupations": [
    {
      "organization_slug": "sec",
      "occ_series": "2210",
      "occ_label": "Information Technology Management",
      "stratum": "technical",
      "headcount": 1200,
      "as_of": "2025-03",
      "source_url": "...",
      "source_title": "...",
      "notes": "..."
    }
  ]
}

Wave-2 JSON shape:
{
  "captured_by": "W2-A",
  "captured_at": "2026-05-26T04:00:00Z",
  "updates": [
    {
      "agency_abbreviation": "VA",
      "tool_name": "Microsoft Copilot Chat",
      "estimated_share_of_eligible": 0.65,
      "share_rationale": "VA cites ~100k onboarded of 140k AI-eligible.",
      "matrix_product_key": "ms_copilot"
    }
  ]
}

Idempotent. Safe to re-run.
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

RESEARCH_DIR = _ROOT / "audit" / "research" / "agency_workforce"

_VALID_LEVEL = {"agency", "bureau"}
_VALID_CONFIDENCE = {"high", "medium", "low"}
_VALID_WAVE = {"0-calibration", "1", "2", "3"}
_VALID_DENOMINATOR_BASIS = {"federal_employees", "incl_contractors"}
_VALID_OCC_STRATUM = {
    "general",
    "technical",
    "legal",
    "investigative",
    "comms",
    "clinical",
}
_VALID_MATRIX_KEYS = {
    "ms_copilot",
    "github_copilot",
    "chatgpt",
    "claude",
    "gemini",
    "amazon_q",
    "agency_built",
}


def _load_wave_files() -> tuple[list[dict], list[dict], list[dict]]:
    """Return (wave_1_or_3_payloads, wave_2_payloads, occupation_payloads).

    A single file may carry any combination of `rows`, `updates`, and
    `occupations` — each key is collected independently.
    """
    if not RESEARCH_DIR.exists():
        return [], [], []
    w1 = []
    w2 = []
    occ = []
    for path in sorted(RESEARCH_DIR.glob("*.json")):
        if path.name == "priors.json":
            continue
        payload = json.loads(path.read_text())
        if "rows" in payload:
            w1.append((path.name, payload))
        if "updates" in payload:
            w2.append((path.name, payload))
        if "occupations" in payload:
            occ.append((path.name, payload))
    return w1, w2, occ


def _validate_w1_row(row: dict, src: str) -> list[str]:
    errs: list[str] = []
    if not row.get("organization_slug"):
        errs.append(f"{src}: row missing organization_slug")
    lvl = row.get("level")
    if lvl not in _VALID_LEVEL:
        errs.append(f"{src}: bad level {lvl!r}")
    share = row.get("ai_eligible_share")
    if share is not None and not (0.0 <= share <= 1.0):
        errs.append(f"{src}: ai_eligible_share out of [0,1]: {share}")
    conf = row.get("confidence")
    if conf is not None and conf not in _VALID_CONFIDENCE:
        errs.append(f"{src}: bad confidence {conf!r}")
    wave = row.get("wave")
    if wave not in _VALID_WAVE:
        errs.append(f"{src}: bad wave {wave!r}")
    contractors = row.get("contractor_headcount")
    if contractors is not None and (
        not isinstance(contractors, int) or contractors < 0
    ):
        errs.append(f"{src}: bad contractor_headcount {contractors!r}")
    basis = row.get("denominator_basis")
    if basis is not None and basis not in _VALID_DENOMINATOR_BASIS:
        errs.append(f"{src}: bad denominator_basis {basis!r}")
    return errs


def _validate_occupation(occ: dict, src: str) -> list[str]:
    errs: list[str] = []
    for field in ("organization_slug", "occ_series", "occ_label", "as_of",
                  "source_url"):
        if not occ.get(field):
            errs.append(f"{src}: occupation missing {field}")
    if occ.get("stratum") not in _VALID_OCC_STRATUM:
        errs.append(f"{src}: bad occupation stratum {occ.get('stratum')!r}")
    hc = occ.get("headcount")
    if not isinstance(hc, int) or hc < 0:
        errs.append(f"{src}: bad occupation headcount {hc!r}")
    return errs


def _validate_w2_update(upd: dict, src: str) -> list[str]:
    errs: list[str] = []
    if not upd.get("agency_abbreviation"):
        errs.append(f"{src}: update missing agency_abbreviation")
    share = upd.get("estimated_share_of_eligible")
    if share is not None and not (0.0 <= share <= 1.0):
        errs.append(f"{src}: estimated_share_of_eligible out of [0,1]: {share}")
    mpk = upd.get("matrix_product_key")
    if mpk is not None and mpk not in _VALID_MATRIX_KEYS:
        errs.append(f"{src}: bad matrix_product_key {mpk!r}")
    return errs


def _wave_rank(wave: str) -> int:
    order = {"0-calibration": 0, "1": 1, "2": 2, "3": 3}
    return order.get(wave, -1)


def main() -> int:
    w1_files, w2_files, occ_files = _load_wave_files()
    if not w1_files and not w2_files and not occ_files:
        print(f"No JSON files under {RESEARCH_DIR}. Nothing to apply.")
        return 0

    conn = get_connection()
    try:
        org_id_by_slug = {
            r[0]: (r[1], r[2])
            for r in conn.execute(
                "SELECT slug, id, legacy_agency_id FROM federal_organizations"
            )
        }
        agency_id_by_abbr = {
            r[0].lower(): r[1]
            for r in conn.execute("SELECT abbreviation, id FROM agencies")
        }
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        errors: list[str] = []

        # ----- Wave 1 / 3 -----
        # Collect all rows then write only the highest-wave row per slug.
        rows_by_slug: dict[str, dict] = {}
        for src, payload in w1_files:
            captured_by = payload.get("captured_by", "unknown")
            captured_at = payload.get("captured_at", now)
            for row in payload.get("rows", []):
                errs = _validate_w1_row(row, src)
                if errs:
                    errors.extend(errs)
                    continue
                slug = row["organization_slug"]
                if slug not in org_id_by_slug:
                    errors.append(
                        f"{src}: organization_slug {slug!r} not in federal_organizations"
                    )
                    continue
                existing = rows_by_slug.get(slug)
                if (
                    existing is None
                    or _wave_rank(row["wave"]) > _wave_rank(existing["wave"])
                ):
                    rows_by_slug[slug] = {
                        **row,
                        "_captured_by": captured_by,
                        "_captured_at": captured_at,
                    }

        # ----- Wave 2 -----
        w2_updates: list[dict] = []
        for src, payload in w2_files:
            for upd in payload.get("updates", []):
                errs = _validate_w2_update(upd, src)
                if errs:
                    errors.extend(errs)
                    continue
                w2_updates.append(upd)

        # ----- Occupations -----
        occupations: list[dict] = []
        for src, payload in occ_files:
            for occ in payload.get("occupations", []):
                errs = _validate_occupation(occ, src)
                if errs:
                    errors.extend(errs)
                    continue
                if occ["organization_slug"] not in org_id_by_slug:
                    errors.append(
                        f"{src}: occupation organization_slug "
                        f"{occ['organization_slug']!r} not in federal_organizations"
                    )
                    continue
                occupations.append(occ)

        if errors:
            print("VALIDATION ERRORS — nothing written:")
            for e in errors:
                print(f"  - {e}")
            return 1

        # Apply Wave 1/3. Wipe-and-reload: seed_federal_hierarchy.py re-keys
        # federal_organizations every rebuild, so rows written against a
        # previous id generation are unreachable orphans — replacing the
        # whole table from the JSON corpus is the only idempotent shape.
        w1_written = 0
        with conn:
            conn.execute("DELETE FROM agency_workforce_profile")
            for slug, row in rows_by_slug.items():
                org_id, legacy_agency_id = org_id_by_slug[slug]
                agency_id = legacy_agency_id  # may be NULL for some orgs
                conn.execute(
                    """
                    INSERT INTO agency_workforce_profile (
                        organization_id, agency_id, level,
                        total_headcount, headcount_as_of,
                        headcount_source_url, headcount_source_title,
                        headcount_quote, ai_eligible_share,
                        ai_eligible_rationale, ai_eligible_source_url,
                        confidence, wave, tagged_by_agent, notes,
                        contractor_headcount, denominator_basis,
                        captured_at, updated_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        org_id,
                        agency_id,
                        row["level"],
                        row.get("total_headcount"),
                        row.get("headcount_as_of"),
                        row.get("headcount_source_url"),
                        row.get("headcount_source_title"),
                        row.get("headcount_quote"),
                        row.get("ai_eligible_share"),
                        row.get("ai_eligible_rationale"),
                        row.get("ai_eligible_source_url"),
                        row.get("confidence"),
                        row["wave"],
                        row["_captured_by"],
                        row.get("notes"),
                        row.get("contractor_headcount"),
                        row.get("denominator_basis"),
                        row["_captured_at"],
                        row["_captured_at"],
                    ),
                )
                w1_written += 1

            # Apply occupations (wipe-and-reload, same reasoning).
            occ_written = 0
            conn.execute("DELETE FROM agency_occupation_counts")
            for occ in occupations:
                _org_id, legacy_agency_id = org_id_by_slug[
                    occ["organization_slug"]
                ]
                conn.execute(
                    """
                    INSERT INTO agency_occupation_counts (
                        agency_id, organization_slug, occ_series, occ_label,
                        stratum, headcount, as_of, source_url, source_title,
                        notes
                    ) VALUES (?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(organization_slug, occ_series, as_of)
                    DO UPDATE SET
                        headcount    = excluded.headcount,
                        stratum      = excluded.stratum,
                        occ_label    = excluded.occ_label,
                        source_url   = excluded.source_url,
                        source_title = excluded.source_title,
                        notes        = excluded.notes
                    """,
                    (
                        legacy_agency_id,
                        occ["organization_slug"],
                        occ["occ_series"],
                        occ["occ_label"],
                        occ["stratum"],
                        occ["headcount"],
                        occ["as_of"],
                        occ["source_url"],
                        occ.get("source_title"),
                        occ.get("notes"),
                    ),
                )
                occ_written += 1

            # Apply Wave 2.
            # Update by (agency_abbreviation, tool_name) since access
            # evidence has no surrogate key. Multiple rows per agency-tool
            # are rare; if present, we set the share on all of them.
            w2_written = 0
            for upd in w2_updates:
                abbr = upd["agency_abbreviation"]
                tool = upd.get("tool_name")
                params = (
                    upd.get("estimated_share_of_eligible"),
                    upd.get("share_rationale"),
                    upd.get("matrix_product_key"),
                    abbr,
                    tool,
                )
                cur = conn.execute(
                    """
                    UPDATE agency_ai_access_evidence
                       SET estimated_share_of_eligible = ?,
                           share_rationale             = ?,
                           matrix_product_key          = ?
                     WHERE agency_abbreviation = ?
                       AND COALESCE(tool_name, '') = COALESCE(?, '')
                    """,
                    params,
                )
                w2_written += cur.rowcount

        print(
            f"Wrote {w1_written} workforce rows; {occ_written} occupation "
            f"rows; updated {w2_written} access evidence rows."
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
