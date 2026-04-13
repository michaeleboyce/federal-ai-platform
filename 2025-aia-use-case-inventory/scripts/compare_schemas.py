#!/usr/bin/env python3
"""
Schema Comparison Script for 2025 AI Use Case Inventories

Compares agency CSV schemas against the official OMB M-25-21 standard.
The canonical format is based on Treasury's implementation with 34 columns.
"""

import csv
import os
from difflib import SequenceMatcher
from pathlib import Path

# Canonical 34-column schema from OMB M-25-21 (based on Treasury's format)
CANONICAL_COLUMNS = [
    # Section 1: Use Case Identifiers (9 columns)
    "Use Case ID",
    "Use Case Name",
    "Bureau/Component",
    "Email Address",
    "Should this AI use case be withheld from public reporting?",
    "Stage of Development",
    "Is the AI use case high-impact?",
    "Justification",
    "Use Case Topic Area",
    # Section 2: Use Case Summary (5 columns)
    "AI Classification",
    "What problem is the AI intended to solve?",
    "What are the expected benefits and positive outcomes from the AI for an agency's mission and/or the general public?",
    "Describe the AI system's outputs.",
    "Date when AI use case became operational or the pilot's start date",
    # Section 3: Documentation (5 columns)
    "Was the system involved in this use case purchased from a vendor or developed under contract(s) or in-house?",
    "Vendor(s) Name",
    "Does this AI use case have an associated Authorization to Operate (ATO)?",
    "System(s) Name",
    "Describe any data used to train, fine-tune, and/or evaluate performance of the model(s) used in this use case.",
    # Section 4: Data & Code (6 columns)
    "If the data is required to be publicly disclosed as an open government data asset, provide a link to the entry on the Federal Data Catalog.",
    "Does this AI use case involve personally identifiable information (PII) that is maintained by the agency?",
    "If publicly available, provide the link to the AI use case's associated Privacy Impact Assessment (PIA), if any.",
    "Which, if any, demographic variables does the AI use case explicitly use as model features?",
    "Does this project include custom-developed code?",
    "If the code is open source, provide the link for the publicly available source code.",
    # Section 5: Risk Management (9 columns)
    "Has pre-deployment testing been conducted for this AI use case?",
    "Has an AI impact assessment been completed for this AI use case?",
    "What are the potential impacts of using the AI for this particular use case and how were they identified?",
    "Has as independent review of the AI use case been conducted?",
    "Is there a process to conduct ongoing monitoring to identify any adverse impacts to the performance and security of the AI functionality, as well as to privacy, civil rights, and civil liberties?",
    "Has the agency established sufficient and periodic training for operators of the AI to interpret and act on the its output and managed associated risks?",
    "Does this AI use case have an appropriate fail-safe that minimizes the risk of significant harm?",
    "Is there an established appeal process in the event that an impacted individual would like to appeal or contest the AI system's outcome?",
    "What steps has the agency taken to consult and incorporate feedback from end users of this AI use case and the public?",
]

# True 2025 inventory files (after DOT and FRB reclassification)
TRUE_2025_FILES = [
    "DHS-2025-ai-inventory.csv",
    "Treasury-2025-ai-inventory.csv",
    "VA-2025-ai-inventory.csv",
    "NASA-2025-ai-inventory.csv",
    "NSF-2025-ai-inventory.csv",
    "NRC-2025-ai-inventory.csv",
    "OPM-2025-ai-inventory.csv",
    "SSA-2025-ai-inventory.csv",
    "NARA-2025-ai-inventory.csv",
    "FHFA-2025-ai-inventory.csv",
    "SEC-2025-ai-inventory.csv",
    "NCUA-2025-ai-inventory.csv",
    "CFTC-2025-ai-inventory.csv",
    "FDIC-2025-ai-inventory.csv",
    "USDA-2025-ai-inventory.csv",
    "DOJ-2025-ai-inventory.csv",
]


def read_csv_headers(filepath: Path) -> tuple[str, list[str], int]:
    """
    Read CSV and detect format type, returning headers.

    Returns:
        tuple: (schema_type, header_list, total_data_rows)
    """
    # Try multiple encodings
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                rows = list(reader)
                break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        return "error", [], 0

    if not rows:
        return "empty", [], 0

    row0 = rows[0]
    row1 = rows[1] if len(rows) > 1 else []

    # Detect format type
    first_cell = row0[0].strip() if row0 and row0[0] else ""

    # Section-based format: Row 0 starts with "SECTION 1:" (possibly with newlines)
    if first_cell.upper().startswith("SECTION 1:") or "SECTION 1:" in first_cell.upper():
        schema_type = "section-based"
        # Headers are in row 1, clean up any newlines/annotations
        headers = [clean_header(h) for h in row1]
        data_rows = len(rows) - 2
    # Title-row format: Row 0 is a title (contains "Inventory" or year reference)
    elif any(x in first_cell for x in ["Inventory", "2025", "2024"]) and not first_cell.upper().startswith("USE CASE"):
        schema_type = "title-row"
        headers = [clean_header(h) for h in row1]
        data_rows = len(rows) - 2
    # Simple format: Row 0 contains actual column headers
    else:
        schema_type = "simple"
        headers = [clean_header(h) for h in row0]
        data_rows = len(rows) - 1

    return schema_type, headers, data_rows


def clean_header(header: str) -> str:
    """Clean up header text by removing newlines, annotations, and extra whitespace."""
    if not header:
        return ""
    # Remove newlines and annotations like [Agency Abbrev.] – [#]
    cleaned = header.replace('\n', ' ').replace('\r', '')
    # Remove common annotation patterns
    if '[Agency Abbrev.]' in cleaned:
        cleaned = cleaned.split('[Agency Abbrev.]')[0]
    return ' '.join(cleaned.split()).strip()


def fuzzy_match_score(s1: str, s2: str) -> float:
    """Calculate fuzzy match score between two strings (0.0 to 1.0)."""
    if not s1 or not s2:
        return 0.0
    # Normalize for comparison
    s1_norm = s1.lower().strip()
    s2_norm = s2.lower().strip()
    # Exact match
    if s1_norm == s2_norm:
        return 1.0
    return SequenceMatcher(None, s1_norm, s2_norm).ratio()


def match_columns(actual_headers: list[str], canonical: list[str], threshold: float = 0.7) -> dict:
    """
    Match actual headers against canonical schema using fuzzy matching.

    Returns:
        dict with matched, missing, and extra columns
    """
    matched = []
    matched_canonical_indices = set()
    matched_actual_indices = set()

    # First pass: exact and high-confidence matches
    for i, actual in enumerate(actual_headers):
        if not actual:
            continue
        best_score = 0.0
        best_canonical_idx = -1
        for j, canonical_col in enumerate(canonical):
            if j in matched_canonical_indices:
                continue
            score = fuzzy_match_score(actual, canonical_col)
            if score > best_score:
                best_score = score
                best_canonical_idx = j

        if best_score >= threshold and best_canonical_idx >= 0:
            matched.append({
                'actual': actual,
                'canonical': canonical[best_canonical_idx],
                'score': best_score,
                'canonical_idx': best_canonical_idx
            })
            matched_canonical_indices.add(best_canonical_idx)
            matched_actual_indices.add(i)

    # Find missing canonical columns
    missing = [canonical[i] for i in range(len(canonical)) if i not in matched_canonical_indices]

    # Find extra columns (not matched to canonical)
    extra = [actual_headers[i] for i in range(len(actual_headers))
             if i not in matched_actual_indices and actual_headers[i]]

    return {
        'matched': matched,
        'missing': missing,
        'extra': extra,
        'matched_count': len(matched),
        'canonical_total': len(canonical)
    }


def analyze_agency(filepath: Path) -> dict:
    """Analyze a single agency's CSV file."""
    agency = filepath.stem.replace('-2025-ai-inventory', '')

    schema_type, headers, data_rows = read_csv_headers(filepath)

    if schema_type == "error":
        return {
            'agency': agency,
            'schema_type': 'error',
            'total_columns': 0,
            'canonical_matched': 0,
            'canonical_missing_count': len(CANONICAL_COLUMNS),
            'extra_count': 0,
            'compliance_pct': 0.0,
            'missing_columns': 'File read error',
            'extra_columns': '',
            'data_rows': 0
        }

    match_result = match_columns(headers, CANONICAL_COLUMNS)

    compliance_pct = (match_result['matched_count'] / match_result['canonical_total']) * 100

    # Truncate long lists for CSV output
    missing_str = '; '.join(match_result['missing'][:5])
    if len(match_result['missing']) > 5:
        missing_str += f' ... (+{len(match_result["missing"]) - 5} more)'

    extra_str = '; '.join(match_result['extra'][:5])
    if len(match_result['extra']) > 5:
        extra_str += f' ... (+{len(match_result["extra"]) - 5} more)'

    return {
        'agency': agency,
        'schema_type': schema_type,
        'total_columns': len(headers),
        'canonical_matched': match_result['matched_count'],
        'canonical_missing_count': len(match_result['missing']),
        'extra_count': len(match_result['extra']),
        'compliance_pct': round(compliance_pct, 1),
        'missing_columns': missing_str,
        'extra_columns': extra_str,
        'data_rows': data_rows
    }


def main():
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data" / "raw"
    output_file = script_dir.parent / "schema-comparison-report.csv"

    print("=" * 70)
    print("2025 AI Use Case Inventory Schema Comparison")
    print("Comparing against OMB M-25-21 standard (34 canonical columns)")
    print("=" * 70)
    print()

    results = []

    for filename in TRUE_2025_FILES:
        filepath = data_dir / filename
        if filepath.exists():
            result = analyze_agency(filepath)
            results.append(result)
            print(f"  {result['agency']:12} | {result['schema_type']:13} | "
                  f"{result['canonical_matched']:2}/{34} cols ({result['compliance_pct']:5.1f}%) | "
                  f"{result['data_rows']} rows")
        else:
            print(f"  {filename}: NOT FOUND")

    print()

    # Write CSV report
    fieldnames = ['agency', 'schema_type', 'total_columns', 'canonical_matched',
                  'canonical_missing_count', 'extra_count', 'compliance_pct',
                  'missing_columns', 'extra_columns']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            # Remove data_rows from CSV output (not in fieldnames)
            row = {k: v for k, v in r.items() if k in fieldnames}
            writer.writerow(row)

    print(f"Report written to: {output_file}")
    print()

    # Group by compliance level
    full_compliance = [r for r in results if r['compliance_pct'] >= 90]
    partial_compliance = [r for r in results if 50 <= r['compliance_pct'] < 90]
    minimal_compliance = [r for r in results if r['compliance_pct'] < 50]

    print("=" * 70)
    print("COMPLIANCE SUMMARY")
    print("=" * 70)

    print(f"\n✓ Full/Near Compliance (≥90%): {len(full_compliance)} agencies")
    for r in sorted(full_compliance, key=lambda x: -x['compliance_pct']):
        print(f"    {r['agency']:12} - {r['compliance_pct']:.1f}% ({r['canonical_matched']}/34 columns)")

    print(f"\n◐ Partial Compliance (50-89%): {len(partial_compliance)} agencies")
    for r in sorted(partial_compliance, key=lambda x: -x['compliance_pct']):
        print(f"    {r['agency']:12} - {r['compliance_pct']:.1f}% ({r['canonical_matched']}/34 columns)")

    print(f"\n✗ Minimal Compliance (<50%): {len(minimal_compliance)} agencies")
    for r in sorted(minimal_compliance, key=lambda x: -x['compliance_pct']):
        print(f"    {r['agency']:12} - {r['compliance_pct']:.1f}% ({r['canonical_matched']}/34 columns)")
        print(f"        → Uses non-standard schema with {r['total_columns']} columns")

    print()

    return results


if __name__ == "__main__":
    main()
