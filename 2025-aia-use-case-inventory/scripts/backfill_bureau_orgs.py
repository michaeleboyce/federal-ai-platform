"""Backfill use_cases.organization_id and bureau_organization_id from
agency_id + bureau_component free-text.

Strategy varies by agency. Documented in the plan; implemented per-agency below.
Always sets organization_id = top-level org. Sets bureau_organization_id only on
confident match. Multi-bureau strings (DOT comma-lists, DOL pipe-lists) leave
bureau_organization_id NULL and emit to audit/unmapped_bureaus.csv for triage.

Idempotent. Safe to re-run after seed updates.
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
UNMAPPED_CSV = ROOT / "audit" / "unmapped_bureaus.csv"

# Multi-bureau separators we recognize. If the bureau_component contains any of
# these, we assume it names multiple bureaus and don't try to pin it to one.
MULTI_SEP_RE = re.compile(r"\|\||;")
# Note: comma is intentionally NOT a separator. Many legitimate org names
# contain commas ("Research, Education, and Economics"). Pipe and semicolon
# are the only reliable multi-bureau delimiters in the data.


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def build_lookups(conn: sqlite3.Connection) -> tuple[dict, dict]:
    """Return (top_org_by_agency_abbr, bureau_lookup_by_top_org_id).

    bureau_lookup_by_top_org_id is {top_org_id: {normalized_key: org_id}} where
    normalized_key is lowercase abbreviation OR lowercase name OR an alias
    (extracted from description).
    """
    rows = conn.execute(
        """
        SELECT id, name, abbreviation, slug, parent_id, level, hierarchy_path,
               legacy_agency_id, description
          FROM federal_organizations
        """
    ).fetchall()

    by_id = {r["id"]: r for r in rows}

    # Top-level orgs (department + independent), keyed by their bridge to legacy
    # agencies.abbreviation (which is what use_cases.agency_id resolves to).
    top_org_by_agency_abbr: dict[str, dict] = {}
    agency_abbr_by_id = {
        r["id"]: r["abbreviation"]
        for r in conn.execute("SELECT id, abbreviation FROM agencies").fetchall()
    }
    legacy_to_top = {}
    for r in rows:
        if r["parent_id"] is None and r["legacy_agency_id"] is not None:
            legacy_to_top[r["legacy_agency_id"]] = r
            if r["abbreviation"]:
                top_org_by_agency_abbr[r["abbreviation"]] = r

    # For each top-level org, build a reverse lookup of its descendants by
    # abbreviation, name, and aliases (case-insensitive).
    bureau_lookup: dict[int, dict[str, int]] = defaultdict(dict)
    for r in rows:
        if r["parent_id"] is None or not r["hierarchy_path"]:
            continue
        # Determine top ancestor id from hierarchy_path /TOP/.../this/
        parts = [p for p in r["hierarchy_path"].split("/") if p]
        if not parts:
            continue
        top_id = int(parts[0])
        keys: list[str] = []
        if r["abbreviation"]:
            keys.append(r["abbreviation"].lower())
        if r["name"]:
            keys.append(r["name"].lower())
        # Pull aliases from the description field where the seed wrote them.
        # Format: "aliases=<<alias1>>alias2>>...>>"
        desc = r["description"] or ""
        m = re.search(r"aliases=<<(.+?)>>(?=\s|$)", desc)
        if m:
            for alias in m.group(1).split(">>"):
                if alias.strip():
                    keys.append(alias.strip().lower())
        for k in keys:
            bureau_lookup[top_id].setdefault(k, r["id"])

    return top_org_by_agency_abbr, bureau_lookup


def normalize_token(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


AGENCY_WIDE_RE = re.compile(
    r"^(agency|department|enterprise|gov|govt)[\s-]*wide$", re.IGNORECASE
)


MULTI_BUREAU_SPLIT_RE = re.compile(
    r"\|\||\s*;\s*|\s*,\s+|\s+and\s+|\s*/\s*", re.IGNORECASE
)


def _multi_bureau_pieces(b: str) -> list[str]:
    """Return constituent pieces if the string looks multi-bureau, else [].

    No has-abbrev heuristic — we rely on the downstream lookup to discard
    pieces that don't resolve. The full original string is still tried first
    via the default branch, so compound names like 'Research, Education and
    Economics' are unaffected (the full alias matches before the split parts
    are even considered).
    """
    pieces = [p.strip() for p in MULTI_BUREAU_SPLIT_RE.split(b) if p.strip()]
    return pieces if len(pieces) > 1 else []


def candidate_tokens_for(agency_abbr: str, bureau: str) -> list[str]:
    """Per-agency parsing yielding ordered candidate keys to look up.

    The whole-string lookup is tried first; if no match, multi-bureau
    constituents are appended as fallback candidates so a use case tagged
    "CAIO, NETT" still attaches to CAIO when CAIO and NETT both exist.
    """
    b = bureau.strip()
    bl = b.lower()
    candidates: list[str] = []

    # Compute multi-bureau pieces once; we'll append them at the end as
    # fallback candidates regardless of the per-agency parser path.
    multi_parts = _multi_bureau_pieces(b)

    # Generic "agency wide" / "department wide" → top org.
    if AGENCY_WIDE_RE.match(b):
        return ["__top__"]
    # Self-reference: bureau text equals the agency abbr or contains it as
    # the parenthetical (e.g., "DHS", "National Archives & Records (NARA)").
    if bl == agency_abbr.lower():
        return ["__top__"]
    paren_m = re.search(r"\(([^)]+)\)\s*$", b)
    if paren_m and paren_m.group(1).strip().lower() == agency_abbr.lower():
        return ["__top__"]

    if agency_abbr == "HHS":
        # "HHS/CDC", "HHS/FDA/CDER", "HHS/CMS/OIT"
        parts = [p.strip() for p in b.split("/") if p.strip()]
        # Skip the leading "HHS"; try the deepest segment (CDER) first then the
        # second segment (FDA), then any others.
        rest = parts[1:] if parts and parts[0].lower() == "hhs" else parts
        for p in reversed(rest):
            candidates.append(normalize_token(p))
        return _append_multi_parts(candidates, multi_parts)

    if agency_abbr == "DOJ":
        # "Department of Justice / FBI", "Department of Justice / FBI/OCDETF"
        # Strip prefix; try last token then any preceding.
        m = re.match(r"^Department of Justice\s*/\s*(.+)$", b, re.IGNORECASE)
        rest = m.group(1) if m else b
        # Sometimes "Department wide" / "Department Wide" — map to top org.
        if rest.lower().strip() in {"department wide"}:
            return ["__top__"]
        parts = [p.strip() for p in re.split(r"\s*/\s*", rest) if p.strip()]
        for p in reversed(parts):
            candidates.append(normalize_token(p))
        return _append_multi_parts(candidates, multi_parts)

    if agency_abbr == "DOE":
        # "PNNL - Pacific Northwest National Laboratory (SC43 OIM)"
        # Take the leading code before " - "
        head = b.split(" - ", 1)[0]
        candidates.append(normalize_token(head))
        # Also try the parenthetical org code (e.g., "NR" / "EE")
        m = re.search(r"\(([A-Z][A-Za-z0-9 \-]+)\)\s*$", b)
        if m:
            candidates.append(normalize_token(m.group(1)))
        # Fallback: full stripped name
        candidates.append(normalize_token(b))
        return _append_multi_parts(candidates, multi_parts)

    if agency_abbr == "Treasury":
        # "Internal Revenue Service (IRS)" — try parens first, then full name
        m = re.search(r"\(([^)]+)\)\s*$", b)
        if m:
            candidates.append(normalize_token(m.group(1)))
        candidates.append(normalize_token(b.split("(")[0]))
        return _append_multi_parts(candidates, multi_parts)

    if agency_abbr in {"VA", "NASA", "SBA", "ED", "SSA"}:
        # "VHA: Veterans Health Administration" / "GSFC: Goddard Space Flight Center"
        # / "OCIO: Office of the Chief Information Officer" — same ABBR: NAME shape.
        head = b.split(":", 1)[0]
        candidates.append(normalize_token(head))
        if ":" in b:
            tail = b.split(":", 1)[1].strip()
            candidates.append(normalize_token(tail))
        return _append_multi_parts(candidates, multi_parts)

    if agency_abbr == "DHS":
        # Already clean; just lowercase.
        if bl == "dhs":  # self-referential
            return ["__top__"]
        candidates.append(bl)
        return _append_multi_parts(candidates, multi_parts)

    if agency_abbr == "DOI":
        candidates.append(bl)
        return _append_multi_parts(candidates, multi_parts)

    # Default: try the value as a whole, lowercase. Also try first token if it
    # looks like an abbreviation. Also try the parenthetical suffix if any.
    candidates.append(bl)
    first = b.split()[0] if b else ""
    if first and re.match(r"^[A-Z][A-Z0-9]{1,8}$", first):
        candidates.append(first.lower())
    # Trailing parenthetical: "Office of Information Technology (OIT)" → also
    # try "OIT".
    pm = re.search(r"\(([^)]+)\)\s*$", b)
    if pm:
        candidates.append(normalize_token(pm.group(1)))
    # Stripped-of-parens version: "Office of Information Technology"
    if "(" in b:
        candidates.append(normalize_token(b.split("(")[0]))
    return _append_multi_parts(candidates, multi_parts)


def _append_multi_parts(candidates: list[str], multi_parts: list[str]) -> list[str]:
    """Append multi-bureau constituent pieces as fallback candidates. Each
    piece becomes its lowercased self plus any embedded ABBR-shaped first
    token. Preserves earlier candidate priority; appends uniques only."""
    seen = set(candidates)
    for p in multi_parts:
        pl = p.lower().strip()
        if pl and pl not in seen:
            candidates.append(pl)
            seen.add(pl)
        first = p.split()[0] if p else ""
        if first and re.match(r"^[A-Z][A-Z0-9]{1,8}$", first):
            fl = first.lower()
            if fl not in seen:
                candidates.append(fl)
                seen.add(fl)
    return candidates


def main() -> int:
    conn = _open()
    UNMAPPED_CSV.parent.mkdir(parents=True, exist_ok=True)
    unmapped_counter: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"count": 0, "samples": []}
    )

    try:
        with conn:
            top_by_abbr, bureau_lookup = build_lookups(conn)

            # Process individual use_cases
            uc_rows = conn.execute(
                """
                SELECT u.id, u.bureau_component, a.abbreviation
                  FROM use_cases u JOIN agencies a ON a.id = u.agency_id
                """
            ).fetchall()

            stats = {
                "use_cases_total": len(uc_rows),
                "org_id_set": 0,
                "bureau_org_id_set": 0,
                "unmapped": 0,
                "no_bureau": 0,
                "no_top_org": 0,
            }

            for uc in uc_rows:
                agency_abbr = uc["abbreviation"]
                top_org = top_by_abbr.get(agency_abbr)
                if not top_org:
                    stats["no_top_org"] += 1
                    continue

                top_id = top_org["id"]
                conn.execute(
                    "UPDATE use_cases SET organization_id = ? WHERE id = ?",
                    (top_id, uc["id"]),
                )
                stats["org_id_set"] += 1

                bureau = (uc["bureau_component"] or "").strip()
                if not bureau:
                    stats["no_bureau"] += 1
                    continue

                tokens = candidate_tokens_for(agency_abbr, bureau)
                if "__top__" in tokens:
                    # "Department wide" or self-referential: tag with the top
                    # itself (no separate bureau).
                    conn.execute(
                        "UPDATE use_cases SET bureau_organization_id = ? WHERE id = ?",
                        (top_id, uc["id"]),
                    )
                    stats["bureau_org_id_set"] += 1
                    continue

                lookup = bureau_lookup.get(top_id, {})
                target = None
                for tok in tokens:
                    if tok in lookup:
                        target = lookup[tok]
                        break

                if target:
                    conn.execute(
                        "UPDATE use_cases SET bureau_organization_id = ? WHERE id = ?",
                        (target, uc["id"]),
                    )
                    stats["bureau_org_id_set"] += 1
                else:
                    stats["unmapped"] += 1
                    key = (agency_abbr, bureau)
                    bucket = unmapped_counter[key]
                    bucket["count"] += 1
                    if len(bucket["samples"]) < 3:
                        bucket["samples"].append(uc["id"])

            # Process consolidated_use_cases — they have no bureau_component
            # but we still want organization_id populated from agency_id.
            cons_rows = conn.execute(
                """
                SELECT c.id, a.abbreviation
                  FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id
                """
            ).fetchall()
            for c in cons_rows:
                top_org = top_by_abbr.get(c["abbreviation"])
                if top_org:
                    conn.execute(
                        "UPDATE consolidated_use_cases SET organization_id = ? WHERE id = ?",
                        (top_org["id"], c["id"]),
                    )

        # Write unmapped report
        with open(UNMAPPED_CSV, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["agency", "bureau_component", "occurrence_count", "sample_use_case_ids"])
            for (agency, bureau), info in sorted(
                unmapped_counter.items(), key=lambda kv: -kv[1]["count"]
            ):
                w.writerow([agency, bureau, info["count"], "|".join(map(str, info["samples"]))])

        print("[backfill]", stats)
        print(f"[backfill] consolidated rows updated: {len(cons_rows)}")
        print(f"[backfill] unmapped distinct (agency,bureau) pairs: {len(unmapped_counter)} -> {UNMAPPED_CSV}")
        match_rate = stats["bureau_org_id_set"] / max(1, stats["use_cases_total"] - stats["no_bureau"]) * 100
        print(f"[backfill] match rate among rows with non-empty bureau_component: {match_rate:.1f}%")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
