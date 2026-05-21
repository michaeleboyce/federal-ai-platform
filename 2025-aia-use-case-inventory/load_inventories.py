"""Load all agency inventory files into the database."""

import csv
import json
import re
import sys
from pathlib import Path

import openpyxl

from db import apply_migrations, get_connection
from column_maps import (
    CONSOLIDATED_COLUMNS,
    is_consolidated_format,
    map_canonical_headers,
    map_consolidated_headers,
)
from auto_tag import normalize_topic_area
from data.federal_hierarchy_seed import ORG_TREE

DATA_DIR = Path(__file__).parent / "data" / "raw"
ENCODINGS = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]

# Filename -> agency abbreviation mapping
AGENCY_FROM_FILENAME = {
    # Regular files: "{ABBR}-2025-ai-inventory.csv/xlsx"
}


def _norm_agency_name(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _build_agency_name_index() -> dict[str, str]:
    """Walk the seed tree (incl. descendants) and build name → abbreviation.

    Used to resolve free-text agency names from multi-agency inventory files
    (e.g. the 2025 OMB consolidated COTS file's `Agency` column). Single source
    of truth: edits go in `data/federal_hierarchy_seed.py`.

    Top-level orgs win on collision: if a sub-org and a top-level org share an
    alias, the top-level abbreviation is preserved. (We populate top-level
    last; their writes overwrite earlier sub-org writes.)
    """
    index: dict[str, str] = {}

    def _walk_descendants(nodes: list[dict]) -> None:
        for n in nodes:
            abbr = n.get("abbreviation")
            if abbr:
                if name := n.get("name"):
                    index[_norm_agency_name(name)] = abbr
                for alias in n.get("aliases") or []:
                    index[_norm_agency_name(alias)] = abbr
            children = n.get("children") or []
            if children:
                _walk_descendants(children)

    # Pass 1: descendants (sub-orgs) — only those with their own abbreviation.
    for node in ORG_TREE:
        children = node.get("children") or []
        if children:
            _walk_descendants(children)

    # Pass 2: top-level orgs (override any sub-org collisions).
    for node in ORG_TREE:
        abbr = node.get("abbreviation")
        if not abbr:
            continue
        if name := node.get("name"):
            index[_norm_agency_name(name)] = abbr
        for alias in node.get("aliases") or []:
            index[_norm_agency_name(alias)] = abbr
    return index


_AGENCY_NAME_INDEX: dict[str, str] | None = None


def resolve_agency_abbr_from_name(name: str | None) -> str | None:
    """Look up an agency abbreviation from a free-text agency name."""
    global _AGENCY_NAME_INDEX
    if _AGENCY_NAME_INDEX is None:
        _AGENCY_NAME_INDEX = _build_agency_name_index()
    return _AGENCY_NAME_INDEX.get(_norm_agency_name(name))


def infer_agency_abbr(filename: str) -> str | None:
    """Extract agency abbreviation from filename."""
    # Strip extensions and suffixes
    name = filename.replace(".csv", "").replace(".xlsx", "")
    # "AGENCY-2025-ai-inventory" or "AGENCY-2025-ai-inventory-consolidated"
    m = re.match(r"^([A-Za-z]+)-20\d{2}-ai-inventory", name)
    if m:
        return m.group(1).upper()
    return None


def is_consolidated_filename(filename: str) -> bool:
    return "consolidated" in filename.lower()


def slugify(agency_abbr: str, name: str, idx: int | None = None) -> str:
    """Generate a deterministic slug.

    Idempotent: derived only from (agency_abbr, name). The optional `idx` is
    appended only when the caller needs a fallback for empty/duplicate names.
    """
    base = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")[:80]
    if not base:
        base = f"use-case-{idx if idx is not None else 0}"
    return f"{agency_abbr.lower()}-{base}"


def read_csv_rows(filepath: Path) -> tuple[list[list], str]:
    """Read CSV with encoding detection. Returns (rows, encoding)."""
    for enc in ENCODINGS:
        try:
            with open(filepath, encoding=enc) as f:
                reader = csv.reader(f)
                rows = list(reader)
            return rows, enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {filepath}")


def read_xlsx_rows(filepath: Path) -> tuple[list[list], str]:
    """Read XLSX, return rows from the best data sheet."""
    wb = openpyxl.load_workbook(str(filepath), read_only=True, data_only=True)
    # Prefer sheet with most data rows, excluding "Selections", "OMB Terms", etc.
    SKIP_SHEETS = {"selections", "sheet2", "sheet3", "sheet4", "omb terms for high impact"}
    best_sheet = None
    best_rows = 0
    for sn in wb.sheetnames:
        if sn.strip().lower() in SKIP_SHEETS:
            continue
        ws = wb[sn]
        # Count non-empty rows in first 5 cols
        count = 0
        for row in ws.iter_rows(values_only=True, max_col=10):
            if any(c is not None and str(c).strip() for c in row):
                count += 1
        if count > best_rows:
            best_rows = count
            best_sheet = sn
    if not best_sheet:
        best_sheet = wb.sheetnames[0]

    ws = wb[best_sheet]
    rows = []
    for row in ws.iter_rows(values_only=True):
        # Truncate trailing empty cols (handle EAC phantom cols)
        cells = list(row)
        # Remove trailing None values
        while cells and cells[-1] is None:
            cells.pop()
        rows.append([c if c is not None else "" for c in cells])
    wb.close()
    return rows, best_sheet


def find_header_row(rows: list[list]) -> int:
    """Find the row index that contains real column headers.

    Section-based files have 'SECTION 1:' text in row 0 and real headers in row 1.
    Some files have a title row at 0 and headers at 1 or 2.
    Simple files have headers in row 0.
    """
    for i, row in enumerate(rows[:5]):
        # Skip empty rows
        non_empty = [str(c).strip() for c in row if c and str(c).strip()]
        if not non_empty:
            continue
        # If row starts with "SECTION 1", next row is headers
        first_cell = str(row[0]) if row else ""
        if first_cell.startswith("SECTION "):
            continue
        # If row has a title like "2025 DOC AI Use Case Inventory" in one cell and rest empty
        non_empty_count = sum(1 for c in row if c and str(c).strip())
        if non_empty_count <= 2 and i < 2:
            continue
        # If "Use Case ID" or "Use Case Name" or "AI Use Case" is present, this is the header row
        joined = " ".join(non_empty).lower()
        if any(marker in joined for marker in ["use case id", "use case name", "ai use case", "tool/application", "use case identifier", "intended purpose"]):
            return i
    return 0


def clean_header(h) -> str:
    """Clean a header string."""
    if h is None:
        return ""
    s = str(h).strip()
    # Replace weird unicode
    s = s.replace("\u0092", "'").replace("\u0096", "-").replace("\u2013", "-")
    return s


def _lookup_agency_id(conn, abbr: str | None) -> int | None:
    if not abbr:
        return None
    row = conn.execute(
        "SELECT id FROM agencies WHERE abbreviation = ?", (abbr,)
    ).fetchone()
    if not row:
        row = conn.execute(
            "SELECT id FROM agencies WHERE LOWER(abbreviation) = LOWER(?)", (abbr,)
        ).fetchone()
    return row["id"] if row else None


def load_file(filepath: Path, conn) -> dict:
    """Load a single agency file. Returns stats dict."""
    filename = filepath.name
    file_agency_abbr = infer_agency_abbr(filename)

    # Read file
    if filepath.suffix == ".csv":
        rows, enc = read_csv_rows(filepath)
        encoding_info = enc
    else:
        rows, sheet = read_xlsx_rows(filepath)
        encoding_info = f"xlsx:{sheet}"

    if len(rows) < 2:
        return {"file": filename, "skipped": "no data rows"}

    # Find header row and strip cleanly
    header_idx = find_header_row(rows)
    headers = [clean_header(c) for c in rows[header_idx]]
    data_rows = rows[header_idx + 1:]

    # Filter out rows that are completely empty
    data_rows = [r for r in data_rows if any(str(c).strip() for c in r)]

    # Determine format: consolidated vs canonical
    consolidated = is_consolidated_format(headers) or is_consolidated_filename(filename)

    if consolidated:
        mapping = map_consolidated_headers(headers)
        target_table = "consolidated_use_cases"
    else:
        mapping = map_canonical_headers(headers)
        target_table = "use_cases"

    # Multi-agency mode: an "Agency" column was mapped, so each row carries
    # its own agency. Used by the 2025 OMB consolidated COTS aggregate file.
    multi_agency = consolidated and ("agency_name" in mapping.values())
    source_format = (
        "cots_aggregate_2025" if multi_agency
        else ("consolidated_per_agency" if consolidated else "canonical_m2521")
    )

    file_agency_id = None
    if not multi_agency:
        # Single-agency mode (original behavior): resolve agency from filename.
        if not file_agency_abbr:
            return {"file": filename, "skipped": "no agency abbr"}
        file_agency_id = _lookup_agency_id(conn, file_agency_abbr)
        if not file_agency_id:
            return {"file": filename, "skipped": f"unknown agency {file_agency_abbr}"}

    inserted = 0
    skipped = 0
    skipped_unknown_agency: dict[str, int] = {}
    for idx, data_row in enumerate(data_rows):
        # Build dict of DB columns -> values
        db_values = {}
        raw = {}
        for col_idx, cell in enumerate(data_row):
            cell_val = str(cell).strip() if cell is not None else ""
            if col_idx < len(headers):
                hdr = headers[col_idx]
                if hdr:
                    raw[hdr] = cell_val
            if col_idx in mapping:
                db_col = mapping[col_idx]
                # Don't overwrite existing non-empty value (in case of duplicate mappings)
                if db_col and (db_col not in db_values or not db_values[db_col]):
                    db_values[db_col] = cell_val

        # Skip rows with no useful data
        if consolidated:
            primary_key = db_values.get("ai_use_case", "").strip()
        else:
            primary_key = db_values.get("use_case_name", "").strip() or db_values.get("use_case_id", "").strip()

        if not primary_key:
            skipped += 1
            continue

        # Resolve per-row agency in multi-agency mode; otherwise reuse file-level.
        if multi_agency:
            row_agency_name = (db_values.get("agency_name") or "").strip()
            row_agency_abbr = resolve_agency_abbr_from_name(row_agency_name)
            row_agency_id = _lookup_agency_id(conn, row_agency_abbr)
            if not row_agency_id:
                skipped_unknown_agency[row_agency_name or "(blank)"] = (
                    skipped_unknown_agency.get(row_agency_name or "(blank)", 0) + 1
                )
                skipped += 1
                continue
        else:
            row_agency_abbr = file_agency_abbr
            row_agency_id = file_agency_id

        # Slug is deterministic on (agency, primary_key). If two rows produce
        # the same slug (e.g. duplicate use-case names within one file) the
        # second one gets a numeric tail. Across files we rely on the UNIQUE
        # constraint + INSERT OR IGNORE to avoid double-loading the same row.
        slug = slugify(row_agency_abbr, primary_key)
        existing = conn.execute(
            f"SELECT id FROM {target_table} WHERE slug = ?", (slug,)
        ).fetchone()
        if existing:
            # Same (agency, primary_key) is already loaded from another file.
            # Skip — the COTS aggregate is canonical for these 45 agencies'
            # consolidated rows; per-agency files (if any) are superseded.
            skipped += 1
            continue

        if consolidated:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO consolidated_use_cases (
                    agency_id, source_file, slug,
                    ai_use_case, commercial_product, commercial_examples,
                    agency_uses, estimated_licenses_users, raw_json,
                    source_format
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_agency_id,
                    filename,
                    slug,
                    db_values.get("ai_use_case"),
                    db_values.get("commercial_product"),
                    db_values.get("commercial_examples"),
                    db_values.get("agency_uses"),
                    db_values.get("estimated_licenses_users"),
                    json.dumps(raw, ensure_ascii=False),
                    source_format,
                ),
            )
            if cur.rowcount == 0:
                skipped += 1
                continue
        else:
            # Normalize topic_area at ingest (em-dash -> hyphen, whitespace
            # collapse, case-only dedupe, blank -> NULL). See
            # `audit/cleanup_pass/topic_area_normalization_log.md`.
            if "topic_area" in db_values:
                db_values["topic_area"] = normalize_topic_area(db_values["topic_area"])
            # Build the full INSERT dynamically
            cols = [
                "use_case_id", "use_case_name", "bureau_component", "email_address",
                "is_withheld", "stage_of_development", "is_high_impact", "justification",
                "topic_area", "ai_classification", "problem_statement", "expected_benefits",
                "system_outputs", "operational_date", "development_type", "vendor_name",
                "has_ato", "system_name", "training_data_description",
                "link_to_data", "has_pii", "pia_url", "demographic_features",
                "has_custom_code", "code_url",
                "hi_testing_conducted", "hi_assessment_completed", "hi_potential_impacts",
                "hi_independent_review", "hi_ongoing_monitoring", "hi_training_established",
                "hi_failsafe_presence", "hi_appeal_process", "hi_public_consultation",
            ]
            placeholders = ",".join(["?"] * (3 + len(cols) + 1))
            values = [row_agency_id, filename, slug] + [db_values.get(c) for c in cols] + [json.dumps(raw, ensure_ascii=False)]
            conn.execute(
                f"""
                INSERT INTO use_cases (
                    agency_id, source_file, slug,
                    {",".join(cols)},
                    raw_json
                ) VALUES ({placeholders})
                """,
                values,
            )

        inserted += 1

        # Also record column mappings
        # (only do this once per file - done after loop)

    # Record column mappings for this file. For multi-agency files we record
    # under a synthetic abbreviation so the row stays distinct from per-agency
    # mappings that other files may produce.
    mappings_abbr = file_agency_abbr or "MULTI"
    for col_idx, hdr in enumerate(headers):
        if not hdr:
            continue
        canonical = mapping.get(col_idx)
        conn.execute(
            "INSERT INTO column_mappings (agency_abbreviation, source_column_name, canonical_column_name, notes) VALUES (?, ?, ?, ?)",
            (mappings_abbr, hdr, canonical, f"{source_format} format"),
        )

    conn.commit()
    result: dict = {
        "file": filename,
        "agency": file_agency_abbr or "MULTI",
        "format": source_format,
        "encoding": encoding_info,
        "header_row": header_idx,
        "inserted": inserted,
        "skipped": skipped,
        "headers_total": len(headers),
        "headers_mapped": len(mapping),
    }
    if skipped_unknown_agency:
        result["skipped_unknown_agencies"] = skipped_unknown_agency
    return result


def main():
    conn = get_connection()
    try:
        apply_migrations(conn)
        # Clear existing data. Order matters under FK constraints — every
        # table that REFERENCES use_cases(id) or consolidated_use_cases(id)
        # must be cleared first. The m004 migration added two such tables
        # (omb_match_audit FK→use_cases; omb_consolidated_rows is FK-free
        # but is rebuilt from the OMB XLSX so we clear it for consistency).
        conn.execute("DELETE FROM use_case_external_evidence")
        conn.execute("DELETE FROM review_queue_products")
        conn.execute("DELETE FROM review_queue_llm")
        conn.execute("DELETE FROM review_queue_scope")
        conn.execute("DELETE FROM review_queue_entry_type")
        conn.execute("DELETE FROM use_case_products")
        conn.execute("DELETE FROM consolidated_use_case_products")
        conn.execute("DELETE FROM use_case_tags")
        conn.execute("DELETE FROM agency_ai_maturity")
        conn.execute("DELETE FROM org_ai_maturity")
        conn.execute("DELETE FROM column_mappings")
        # m004 OMB consolidated provenance — clear before use_cases since
        # omb_match_audit has FK→use_cases(id).
        conn.execute("DELETE FROM omb_match_audit")
        conn.execute("DELETE FROM omb_consolidated_rows")
        # m011 year-over-year lineage — use_case_year_links has
        # FK→use_cases(id) (and FK→use_cases_2024(id)). Clear before
        # use_cases. match_year_over_year.py rebuilds it later in the
        # pipeline (wipe-and-reload).
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='use_case_year_links'"
        ).fetchone():
            conn.execute("DELETE FROM use_case_year_links")
        conn.execute("DELETE FROM use_cases")
        conn.execute("DELETE FROM consolidated_use_cases")
        conn.commit()

        files = sorted([f for f in DATA_DIR.iterdir() if f.is_file() and f.suffix in (".csv", ".xlsx")])
        # Explicit skip list for duplicates/outdated files
        SKIP_FILES = {
            "DOI-2025-ai-inventory.xlsx",  # XLSX is 2024 data, CSV is correct 2025
            "DHS-2025-ai-inventory.xlsx",  # CSV has same data
            "FRB-2025-ai-inventory.xlsx",  # CSV has same data
            # HUD-2025-ai-inventory.xlsx is kept -- no CSV version exists
            "NARA-2025-ai-inventory.xlsx",  # CSV has same data
            "NASA-2025-ai-inventory.xlsx",  # CSV has same data
            "NSF-2025-ai-inventory.xlsx",  # CSV has same data
            "VA-2025-ai-inventory.xlsx",  # CSV has same data
            # Per-agency consolidated/Appendix-B files — superseded by the
            # 2025 OMB consolidated COTS aggregate (cots-2025-ai-inventory-
            # consolidated.xlsx) which carries the canonical 20-template grid
            # for all 45 small/CFO-Act agencies. Loading both would duplicate
            # rows under different source_file values.
            "CSOSA-2025-ai-inventory.csv",
            "DOL-2025-ai-inventory-consolidated.csv",
            "EAC-2025-ai-inventory.xlsx",
            "FCC-2025-ai-inventory.xlsx",
            "FDIC-2025-ai-inventory-consolidated.csv",
            "HUD-2025-ai-inventory-consolidated.xlsx",
            "NLRB-2025-ai-inventory.csv",
            "OSC-2025-ai-inventory.xlsx",
            "PBGC-2025-ai-inventory.csv",
            "USITC-2025-ai-inventory.csv",
            "USTDA-2025-ai-inventory.xlsx",
        }

        results = []
        for f in files:
            if f.name in SKIP_FILES:
                results.append({"file": f.name, "skipped": "duplicate/outdated"})
                continue

            try:
                result = load_file(f, conn)
                results.append(result)
                print(f"{f.name}: {result}")
            except Exception as e:
                print(f"ERROR loading {f.name}: {e}")
                results.append({"file": f.name, "error": str(e)})

        # Summary
        print("\n=== SUMMARY ===")
        total = sum(r.get("inserted", 0) for r in results)
        by_format = {}
        for r in results:
            fmt = r.get("format", r.get("skipped") or r.get("error"))
            by_format[fmt] = by_format.get(fmt, 0) + r.get("inserted", 0)
        print(f"Total inserted: {total}")
        print(f"By format: {by_format}")

        uc = conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0]
        cu = conn.execute("SELECT COUNT(*) FROM consolidated_use_cases").fetchone()[0]
        print(f"use_cases: {uc}, consolidated_use_cases: {cu}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
