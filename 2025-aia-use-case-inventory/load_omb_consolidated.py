"""Load the 2025 OMB consolidated individually-reported AI use case file.

This loader is OMB's snapshot of agency filings — distinct from the
per-agency files loaded by `load_inventories.py`. It populates two tables:

  - `omb_consolidated_rows`: a row-for-row mirror of the XLSX (36 columns)
  - `omb_match_audit`:        one row per match attempt (status + drift)

It also writes back to `use_cases.omb_consolidated_id` /
`omb_consolidated_source` / `omb_consolidated_first_seen` /
`omb_consolidated_last_seen` for matched pairs.

Idempotent: re-running replaces `omb_consolidated_rows` for the same
source-file path and rebuilds `omb_match_audit` from scratch (preserving
`first_seen` and human-set `resolution_note` / `resolved_at` fields).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import openpyxl

from column_maps import OMB_CONSOLIDATED_COLUMNS, map_omb_consolidated_headers
from omb_consolidated_match import (
    DRIFT_FIELDS_DEFAULT,
    classify_match,
    detect_drift,
    name_match_score,
    normalize_agency,
    normalize_name,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_FILE = ROOT / "data" / "raw" / "2025_individually_reported_AI_use_cases.xlsx"
SHEET_NAME = "Consolidated Inventory"

# Per-agency rename-threshold overrides. Default 0.40 in
# omb_consolidated_match already catches NSF acronym expansions, so this
# starts empty. Add entries here to be MORE strict for noisy agencies.
_PER_AGENCY_RENAME_THRESHOLD: dict[str, float] = {}

OMB_KEYS = [k for _, k in OMB_CONSOLIDATED_COLUMNS]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_iter(path: Path) -> Iterator[tuple[int, list]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[SHEET_NAME]
    rows = ws.iter_rows(values_only=True)
    blank_or_first = next(rows, None)
    headers = next(rows, None)
    if not headers:
        return
    map_omb_consolidated_headers(list(headers))  # raises if positions drift
    for i, row in enumerate(rows, start=3):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        yield i, list(row)


def _hash_row(canonical: list) -> str:
    blob = json.dumps(
        [(s.strip() if isinstance(s, str) else s) for s in canonical],
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def _replace_omb_rows(conn: sqlite3.Connection, source_file: str) -> None:
    conn.execute(
        "DELETE FROM omb_consolidated_rows WHERE ingest_source_file=?",
        (source_file,),
    )


def _insert_omb_row(
    conn: sqlite3.Connection,
    source_file: str,
    run_at: str,
    idx: int,
    vals: list,
) -> int:
    # Trim to 36 columns (the OMB-defined width); ignore anything past that.
    vals = list(vals)[: len(OMB_KEYS)]
    while len(vals) < len(OMB_KEYS):
        vals.append(None)
    raw_json = json.dumps(dict(zip(OMB_KEYS, vals)), ensure_ascii=False, default=str)
    row_hash = _hash_row(vals)
    cols = (
        ["ingest_source_file", "ingest_run_at", "row_hash", "row_index_in_file"]
        + OMB_KEYS
        + ["raw_json"]
    )
    placeholders = ",".join(["?"] * len(cols))
    cur = conn.execute(
        f"INSERT INTO omb_consolidated_rows({','.join(cols)}) VALUES ({placeholders})",
        [source_file, run_at, row_hash, idx, *vals, raw_json],
    )
    return cur.lastrowid


def _build_db_index(conn: sqlite3.Connection) -> dict:
    """(agency_abbr, normalized_name) -> [db_row_dict].

    Columns are selected with PRAGMA-aware fallbacks so this works against
    both the live DB (which kept legacy names like `development_type` per
    migration m002's intentional divergences) and freshly-built test DBs
    that may have either spelling.
    """
    use_case_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(use_cases)")
    }
    contracting_expr = (
        "COALESCE(uc.contracting_usage, uc.development_type)"
        if "contracting_usage" in use_case_cols and "development_type" in use_case_cols
        else "uc.contracting_usage"
        if "contracting_usage" in use_case_cols
        else "uc.development_type"
    )
    rows = conn.execute(
        f"""
        SELECT uc.id AS db_id, uc.use_case_id, uc.use_case_name,
               uc.stage_of_development, uc.is_high_impact, uc.is_withheld,
               uc.topic_area, uc.ai_classification,
               {contracting_expr} AS contracting_usage,
               uc.vendor_name, uc.has_ato AS have_ato, uc.has_pii,
               uc.has_custom_code, uc.bureau_component,
               a.abbreviation AS agency_abbreviation
        FROM use_cases uc
        JOIN agencies a ON a.id = uc.agency_id
        """
    ).fetchall()
    index: dict[tuple[str | None, str], list[dict]] = {}
    keys = [
        "db_id", "use_case_id", "use_case_name", "stage_of_development",
        "is_high_impact", "is_withheld", "topic_area", "ai_classification",
        "contracting_usage", "vendor_name", "have_ato", "has_pii",
        "has_custom_code", "bureau_component", "agency_abbreviation",
    ]
    for r in rows:
        d = dict(zip(keys, r)) if not isinstance(r, sqlite3.Row) else dict(r)
        agency = normalize_agency(d["agency_abbreviation"])
        # Index by (agency, bureau, name) to disambiguate same-name use cases
        # filed by different bureaus (e.g., ED has 15 distinct "Generative AI -
        # Text Generation" rows, one per bureau, all legitimately separate).
        key = (
            agency,
            normalize_name(d.get("bureau_component")),
            normalize_name(d["use_case_name"]),
        )
        index.setdefault(key, []).append(d)
    return index


def _omb_row_dict(vals: list) -> dict:
    vals = list(vals)[: len(OMB_KEYS)]
    while len(vals) < len(OMB_KEYS):
        vals.append(None)
    return dict(zip(OMB_KEYS, vals))


def _link_use_case(
    conn: sqlite3.Connection,
    db_id: int,
    omb_id: object,
    source: str,
    run_at: str,
    prior: dict,
    key: tuple[str | None, str | None],
) -> None:
    prior_row = prior.get(key)
    first_seen = (
        prior_row["first_seen"] if prior_row and prior_row["first_seen"] else run_at
    )
    omb_id_str = str(omb_id) if omb_id is not None else None
    conn.execute(
        """
        UPDATE use_cases SET
            omb_consolidated_id = ?,
            omb_consolidated_source = ?,
            omb_consolidated_first_seen = COALESCE(omb_consolidated_first_seen, ?),
            omb_consolidated_last_seen = ?
        WHERE id = ?
        """,
        (omb_id_str, source, first_seen, run_at, db_id),
    )


def _record_audit(
    conn: sqlite3.Connection,
    run_at: str,
    omb_id: int | None,
    db_id: int | None,
    agency: str | None,
    name: str | None,
    method: str,
    score: float | None,
    status: str,
    drift: dict,
    prior: dict,
) -> None:
    key = (agency, name)
    prior_row = prior.get(key)
    first_seen = (
        prior_row["first_seen"] if prior_row and prior_row["first_seen"] else run_at
    )
    resolved_at = prior_row["resolved_at"] if prior_row else None
    resolution_note = prior_row["resolution_note"] if prior_row else None
    conn.execute(
        """
        INSERT INTO omb_match_audit(
            ingest_run_at, omb_row_id, use_case_id_db, agency_abbreviation,
            use_case_name, match_method, match_score, match_status,
            drift_fields_json, first_seen, last_seen, resolved_at, resolution_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_at, omb_id, db_id, agency, name, method, score, status,
            json.dumps(drift, ensure_ascii=False, default=str),
            first_seen, run_at, resolved_at, resolution_note,
        ),
    )


def load(conn: sqlite3.Connection, path: Path | str = DEFAULT_FILE) -> None:
    path = Path(path)
    source_file = path.name
    run_at = _now()

    # 1. Snapshot prior audit BEFORE any DELETEs (preserves first_seen/
    # resolved_at/resolution_note across re-ingest).
    prior_audit = {}
    for r in conn.execute(
        "SELECT agency_abbreviation, use_case_name, first_seen, "
        "resolved_at, resolution_note FROM omb_match_audit"
    ):
        if isinstance(r, sqlite3.Row):
            prior_audit[(r["agency_abbreviation"], r["use_case_name"])] = dict(r)
        else:
            agency_abbr, name, first_seen, resolved_at, resolution_note = r
            prior_audit[(agency_abbr, name)] = {
                "first_seen": first_seen,
                "resolved_at": resolved_at,
                "resolution_note": resolution_note,
            }

    # 2. Clear audit FIRST (it FKs into omb_consolidated_rows), then replace
    # the OMB row mirror for this source file.
    conn.execute("DELETE FROM omb_match_audit")
    _replace_omb_rows(conn, source_file)
    omb_row_pairs: list[tuple[int, list]] = []
    for idx, vals in _row_iter(path):
        rid = _insert_omb_row(conn, source_file, run_at, idx, vals)
        omb_row_pairs.append((rid, vals))

    # 3. Build DB index for matching.
    db_index = _build_db_index(conn)
    matched_db_ids: set[int] = set()
    seen_omb_keys: dict[tuple[str | None, str], int] = {}

    # 4. First pass — exact matches and duplicate detection.
    deferred_rows: list[tuple[int, list, str | None]] = []  # rows for fuzzy pass
    for omb_id, vals in omb_row_pairs:
        omb = _omb_row_dict(vals)
        agency = normalize_agency(omb["agency_abbreviation"])
        bureau_norm = normalize_name(omb.get("bureau_component"))
        name_norm = normalize_name(omb["use_case_name"])
        # Verbatim-duplicate detection requires (agency, bureau, name) match.
        # Same name at different bureaus is legitimate (ED has 15 separate
        # "Generative AI - Text Generation" rows across bureaus).
        dup_key = (agency, bureau_norm, name_norm)
        key = dup_key  # also the DB-index key

        if dup_key in seen_omb_keys:
            _record_audit(
                conn, run_at, omb_id, None, agency, omb["use_case_name"],
                "none", None, "duplicate_in_omb", {}, prior_audit,
            )
            continue
        seen_omb_keys[dup_key] = omb_id

        candidates = db_index.get(key, [])
        if candidates:
            db_row = candidates[0]
            matched_db_ids.add(db_row["db_id"])
            drift = detect_drift(db_row, omb, fields=DRIFT_FIELDS_DEFAULT)
            _record_audit(
                conn, run_at, omb_id, db_row["db_id"], agency,
                omb["use_case_name"], "exact_name", 1.0, "matched_exact",
                drift, prior_audit,
            )
            _link_use_case(
                conn, db_row["db_id"], omb["use_case_id_omb"],
                source_file, run_at, prior_audit,
                (agency, omb["use_case_name"]),
            )
        else:
            deferred_rows.append((omb_id, vals, agency))

    # 5. Second pass — fuzzy / suggested_rename / omb_only.
    for omb_id, vals, agency in deferred_rows:
        omb = _omb_row_dict(vals)
        same_agency_rows = [
            d
            for k, lst in db_index.items()
            if k[0] == agency
            for d in lst
            if d["db_id"] not in matched_db_ids
        ]
        best_score, best_db = 0.0, None
        for d in same_agency_rows:
            s = name_match_score(omb["use_case_name"], d["use_case_name"])
            if s > best_score:
                best_score, best_db = s, d

        rename_threshold = _PER_AGENCY_RENAME_THRESHOLD.get(agency, 0.40)
        if best_db is not None and best_score >= 0.85:
            matched_db_ids.add(best_db["db_id"])
            drift = detect_drift(best_db, omb, fields=DRIFT_FIELDS_DEFAULT)
            _record_audit(
                conn, run_at, omb_id, best_db["db_id"], agency,
                omb["use_case_name"], "fuzzy_name", best_score,
                "matched_fuzzy", drift, prior_audit,
            )
            _link_use_case(
                conn, best_db["db_id"], omb["use_case_id_omb"],
                source_file, run_at, prior_audit,
                (agency, omb["use_case_name"]),
            )
        elif best_db is not None and best_score >= rename_threshold:
            _record_audit(
                conn, run_at, omb_id, best_db["db_id"], agency,
                omb["use_case_name"], "fuzzy_name", best_score,
                "suggested_rename", {}, prior_audit,
            )
        else:
            _record_audit(
                conn, run_at, omb_id, None, agency, omb["use_case_name"],
                "none", None, "omb_only", {}, prior_audit,
            )

    # 6. db_only sweep.
    for (agency, _bureau, _name), db_rows in db_index.items():
        for d in db_rows:
            if d["db_id"] in matched_db_ids:
                continue
            _record_audit(
                conn, run_at, None, d["db_id"], agency, d["use_case_name"],
                "none", None, "db_only", {}, prior_audit,
            )

    conn.commit()


def _print_rollup(conn: sqlite3.Connection) -> None:
    print("Audit rollup:")
    for r in conn.execute(
        "SELECT match_status, COUNT(*) FROM omb_match_audit GROUP BY match_status "
        "ORDER BY 2 DESC"
    ):
        if isinstance(r, sqlite3.Row):
            print(f"  {r[0]:<24} {r[1]}")
        else:
            print(f"  {r[0]:<24} {r[1]}")


def main(argv: list[str] | None = None) -> int:
    from db import get_connection
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    path = DEFAULT_FILE
    if argv and len(argv) > 0:
        path = Path(argv[0])
    load(conn, path)
    print(f"Loaded OMB consolidated file from {path}.")
    _print_rollup(conn)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
