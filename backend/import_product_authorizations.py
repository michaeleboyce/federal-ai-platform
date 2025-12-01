#!/usr/bin/env python3
"""
Import FedRAMP product authorizations from marketplace CSV.

This script:
1. Reads the marketplace CSV file
2. Matches parent/sub agency names to federal_organizations
3. Inserts authorization records into product_authorizations table

Usage:
    python import_product_authorizations.py /path/to/marketplace.csv
"""

import csv
import os
import sys
from collections import defaultdict
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Load environment variables
load_dotenv('.env')
load_dotenv('../frontend/.env.local')

def normalize_name(name: str) -> str:
    """Normalize agency name for matching."""
    if not name:
        return ""
    return name.lower().strip()

def get_federal_organizations(conn) -> dict:
    """Fetch all federal organizations for matching."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, short_name, abbreviation, level, parent_id
        FROM federal_organizations
        WHERE is_active = true
    """)

    orgs = {}
    for row in cursor.fetchall():
        org_id, name, short_name, abbreviation, level, parent_id = row
        # Index by multiple keys for matching
        key = normalize_name(name)
        orgs[key] = org_id

        if short_name:
            orgs[normalize_name(short_name)] = org_id
        if abbreviation:
            orgs[normalize_name(abbreviation)] = org_id

    cursor.close()
    return orgs

def match_agency_to_org(parent_agency: str, sub_agency: str, orgs: dict) -> int | None:
    """
    Try to match CSV agency names to federal_organizations.
    Returns organization ID or None if no match.
    """
    # Skip special values
    if parent_agency == "Legacy JAB Authorization":
        return None
    if parent_agency == "Federal Risk and Authorization Management Program":
        return None

    # Try sub_agency first (more specific)
    if sub_agency:
        normalized = normalize_name(sub_agency)
        if normalized in orgs:
            return orgs[normalized]

    # Try parent_agency
    if parent_agency:
        normalized = normalize_name(parent_agency)
        if normalized in orgs:
            return orgs[normalized]

    # Try removing "Department of " prefix variations
    if parent_agency:
        for prefix in ["Department of ", "Department of the "]:
            if parent_agency.startswith(prefix):
                short = parent_agency[len(prefix):]
                if normalize_name(short) in orgs:
                    return orgs[normalize_name(short)]

    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_product_authorizations.py /path/to/marketplace.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    # Connect to database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)

    print(f"Connecting to database...")
    conn = psycopg2.connect(database_url)

    print("Fetching federal organizations for matching...")
    orgs = get_federal_organizations(conn)
    print(f"  Found {len(orgs)} organization name mappings")

    # Read CSV
    print(f"\nReading CSV: {csv_path}")
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"  Found {len(rows)} authorization rows")

    # Process rows - deduplicate by (fedramp_id, parent_agency, sub_agency)
    print("\nProcessing authorizations...")
    seen = set()
    authorizations = []
    stats = {
        'total': 0,
        'matched': 0,
        'unmatched': 0,
        'skipped': 0,
        'duplicates': 0,
    }

    unmatched_agencies = defaultdict(int)

    for row in rows:
        stats['total'] += 1

        fedramp_id = row.get('FedRAMP ID', '').strip()
        parent_agency = row.get('Parent Agency', '').strip()
        sub_agency = row.get('Sub Agency', '').strip()
        ato_issuance = row.get('ATO Issuance Date', '').strip()
        ato_expiration = row.get('ATO Expiration Date', '').strip()

        if not fedramp_id or not parent_agency:
            stats['skipped'] += 1
            continue

        # Deduplicate by unique key
        dedup_key = (fedramp_id, parent_agency, sub_agency or '')
        if dedup_key in seen:
            stats['duplicates'] += 1
            continue
        seen.add(dedup_key)

        # Try to match to federal_organizations
        org_id = match_agency_to_org(parent_agency, sub_agency, orgs)

        if org_id:
            stats['matched'] += 1
        else:
            stats['unmatched'] += 1
            key = sub_agency if sub_agency else parent_agency
            unmatched_agencies[key] += 1

        authorizations.append((
            fedramp_id,
            org_id,
            parent_agency,
            sub_agency if sub_agency else None,
            ato_issuance if ato_issuance else None,
            ato_expiration if ato_expiration else None,
        ))

    unique_count = stats['matched'] + stats['unmatched']
    print(f"\nMatching statistics:")
    print(f"  Total rows:   {stats['total']}")
    print(f"  Duplicates:   {stats['duplicates']}")
    print(f"  Skipped:      {stats['skipped']}")
    print(f"  Unique auth:  {unique_count}")
    print(f"  Matched:      {stats['matched']} ({100*stats['matched']/unique_count:.1f}% of unique)")
    print(f"  Unmatched:    {stats['unmatched']} ({100*stats['unmatched']/unique_count:.1f}% of unique)")

    if unmatched_agencies:
        print(f"\nTop unmatched agencies:")
        for agency, count in sorted(unmatched_agencies.items(), key=lambda x: -x[1])[:20]:
            print(f"  {count:4d} - {agency}")

    # Clear existing data
    print("\nClearing existing product_authorizations data...")
    cursor = conn.cursor()
    cursor.execute("TRUNCATE product_authorizations RESTART IDENTITY")

    # Insert new data
    print(f"Inserting {len(authorizations)} authorization records...")

    insert_sql = """
        INSERT INTO product_authorizations
        (fedramp_id, organization_id, parent_agency_name, sub_agency_name, ato_issuance_date, ato_expiration_date)
        VALUES %s
        ON CONFLICT (fedramp_id, parent_agency_name, COALESCE(sub_agency_name, '')) DO UPDATE
        SET organization_id = EXCLUDED.organization_id,
            ato_issuance_date = EXCLUDED.ato_issuance_date,
            ato_expiration_date = EXCLUDED.ato_expiration_date
    """

    execute_values(cursor, insert_sql, authorizations, page_size=500)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n✅ Import complete!")
    print(f"   Inserted {len(authorizations)} authorization records")

if __name__ == '__main__':
    main()
