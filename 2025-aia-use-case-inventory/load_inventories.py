"""Load all agency inventory files into the database."""

import csv
import json
import re
import sys
from pathlib import Path

import openpyxl

from db import get_connection
from column_maps import (
    CONSOLIDATED_COLUMNS,
    is_consolidated_format,
    map_canonical_headers,
    map_consolidated_headers,
)

DATA_DIR = Path(__file__).parent / "data" / "raw"
ENCODINGS = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]

# Filename -> agency abbreviation mapping
AGENCY_FROM_FILENAME = {
    # Regular files: "{ABBR}-2025-ai-inventory.csv/xlsx"
}


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


def slugify(agency_abbr: str, name: str, idx: int) -> str:
    """Generate a unique slug."""
    base = re.sub(r"[^a-z0-9]+", "-", (name or f"use-case-{idx}").lower()).strip("-")[:80]
    return f"{agency_abbr.lower()}-{base}-{idx}"


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


def load_file(filepath: Path, conn) -> dict:
    """Load a single agency file. Returns stats dict."""
    filename = filepath.name
    agency_abbr = infer_agency_abbr(filename)
    if not agency_abbr:
        return {"file": filename, "skipped": "no agency abbr"}

    # Look up agency_id
    row = conn.execute("SELECT id FROM agencies WHERE abbreviation = ?", (agency_abbr,)).fetchone()
    if not row:
        # Try case-insensitive
        row = conn.execute("SELECT id FROM agencies WHERE LOWER(abbreviation) = LOWER(?)", (agency_abbr,)).fetchone()
    if not row:
        return {"file": filename, "skipped": f"unknown agency {agency_abbr}"}
    agency_id = row["id"]

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

    inserted = 0
    skipped = 0
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

        # Generate slug
        slug_name = primary_key
        slug = slugify(agency_abbr, slug_name, idx)

        # Ensure slug is unique
        existing = conn.execute(f"SELECT id FROM {target_table} WHERE slug = ?", (slug,)).fetchone()
        n = 1
        while existing:
            slug = slugify(agency_abbr, slug_name, idx) + f"-{n}"
            existing = conn.execute(f"SELECT id FROM {target_table} WHERE slug = ?", (slug,)).fetchone()
            n += 1

        if consolidated:
            conn.execute(
                """
                INSERT INTO consolidated_use_cases (
                    agency_id, source_file, slug,
                    ai_use_case, commercial_product, commercial_examples,
                    agency_uses, estimated_licenses_users, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agency_id,
                    filename,
                    slug,
                    db_values.get("ai_use_case"),
                    db_values.get("commercial_product"),
                    db_values.get("commercial_examples"),
                    db_values.get("agency_uses"),
                    db_values.get("estimated_licenses_users"),
                    json.dumps(raw, ensure_ascii=False),
                ),
            )
        else:
            # Build the full INSERT dynamically
            cols = [
                "use_case_id", "use_case_name", "bureau_component", "email_address",
                "withheld_from_public", "stage_of_development", "is_high_impact", "justification",
                "topic_area", "ai_classification", "problem_statement", "expected_benefits",
                "system_outputs", "operational_date", "development_type", "vendor_name",
                "has_ato", "system_name", "training_data_description",
                "federal_data_catalog_link", "involves_pii", "pia_link", "demographic_variables",
                "has_custom_code", "open_source_link",
                "pre_deployment_testing", "impact_assessment", "potential_impacts",
                "independent_review", "ongoing_monitoring", "operator_training",
                "has_fail_safe", "appeal_process", "end_user_feedback",
            ]
            placeholders = ",".join(["?"] * (3 + len(cols) + 1))
            values = [agency_id, filename, slug] + [db_values.get(c) for c in cols] + [json.dumps(raw, ensure_ascii=False)]
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

    # Record column mappings for this file
    for col_idx, hdr in enumerate(headers):
        if not hdr:
            continue
        canonical = mapping.get(col_idx)
        conn.execute(
            "INSERT INTO column_mappings (agency_abbreviation, source_column_name, canonical_column_name, notes) VALUES (?, ?, ?, ?)",
            (agency_abbr, hdr, canonical, f"{'consolidated' if consolidated else 'canonical'} format"),
        )

    conn.commit()
    return {
        "file": filename,
        "agency": agency_abbr,
        "format": "consolidated" if consolidated else "canonical",
        "encoding": encoding_info,
        "header_row": header_idx,
        "inserted": inserted,
        "skipped": skipped,
        "headers_total": len(headers),
        "headers_mapped": len(mapping),
    }


def main():
    conn = get_connection()
    try:
        # Clear existing data
        conn.execute("DELETE FROM column_mappings")
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
