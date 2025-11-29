#!/usr/bin/env python3
"""
Load agency AI tools data from Excel into the database.

This script reads the all-generative-ai-chatbots.xlsx file and populates:
- agency_ai_profiles: One row per agency
- agency_ai_tools: One row per tool (multiple tools per agency possible)
"""

import os
import re
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from typing import Optional

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL',
    'postgresql://neondb_owner:npg_cs0yhB2pztYU@ep-frosty-art-ah7kkpfj-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')

# Excel file path
EXCEL_FILE = '/Users/michaelboyce/Documents/Jobs/IFP/all-generative-ai-chatbots.xlsx'


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    return text


def map_deployment_status(status: Optional[str]) -> str:
    """Map Excel deployment status to database enum."""
    if not status:
        return 'no_public_internal_assistant'
    status_lower = status.lower()
    if 'all_staff' in status_lower or status_lower == 'all_staff':
        return 'all_staff'
    elif 'pilot' in status_lower or 'limited' in status_lower:
        return 'pilot_or_limited'
    else:
        return 'no_public_internal_assistant'


def map_product_type(ptype: Optional[str]) -> str:
    """Map Excel product type to database enum."""
    if not ptype:
        return 'none_identified'
    ptype_lower = ptype.lower().replace(' ', '_')
    valid_types = ['staff_chatbot', 'coding_assistant', 'document_automation', 'none_identified']
    return ptype_lower if ptype_lower in valid_types else 'none_identified'


def map_availability(avail: Optional[str]) -> Optional[str]:
    """Map Excel availability to text."""
    if not avail:
        return None
    avail_lower = str(avail).lower()
    if avail_lower in ['yes', 'true', '1']:
        return 'yes'
    elif avail_lower in ['no', 'false', '0']:
        return 'no'
    elif 'subset' in avail_lower:
        return 'subset'
    return avail_lower


def map_pilot_flag(pilot: Optional[str]) -> bool:
    """Map pilot/limited to boolean."""
    if not pilot:
        return False
    pilot_lower = str(pilot).lower()
    return pilot_lower in ['yes', 'true', '1', 'pilot', 'limited']


def main():
    print(f"Reading Excel file: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE, header=1)  # Header is in row 1 (0-indexed)

    print(f"Found {len(df)} rows")
    print(f"Columns: {list(df.columns)}")

    # Connect to database
    print(f"\nConnecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Clear existing data
    print("Clearing existing data...")
    cur.execute("DELETE FROM agency_ai_tools")
    cur.execute("DELETE FROM agency_ai_profiles")
    conn.commit()

    # Group rows by agency
    agencies = {}
    used_slugs = set()

    for _, row in df.iterrows():
        agency_name = row.get('AgencyName', '')
        if not agency_name or pd.isna(agency_name):
            continue

        abbreviation = row.get('Abbreviation', '')
        if pd.isna(abbreviation):
            abbreviation = None

        # Create unique key for agency
        agency_key = f"{agency_name}|{abbreviation or ''}"

        if agency_key not in agencies:
            # Generate unique slug
            base_slug = slugify(f"{abbreviation or agency_name}")
            slug = base_slug
            counter = 1
            while slug in used_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            used_slugs.add(slug)

            agencies[agency_key] = {
                'agency_name': agency_name,
                'abbreviation': abbreviation,
                'parent': row.get('Parent') if not pd.isna(row.get('Parent')) else None,
                'slug': slug,
                'department_level_name': row.get('DepartmentLevelName') if not pd.isna(row.get('DepartmentLevelName')) else None,
                'deployment_status': map_deployment_status(row.get('DeploymentStatus_2025_11')),
                'tools': []
            }

        # Add tool if product name exists and is not "none_identified"
        product_name = row.get('ProductName', '')
        product_type = row.get('ProductType', '')

        if product_name and not pd.isna(product_name) and product_name.lower() != 'none_identified':
            tool = {
                'product_name': product_name,
                'product_type': map_product_type(product_type),
                'available_to_all_staff': map_availability(row.get('AvailableToAllStaff')),
                'is_pilot_or_limited': map_pilot_flag(row.get('PilotOrLimited')),
                'coding_assistant_flag': str(row.get('CodingAssistantFlag', '')) if not pd.isna(row.get('CodingAssistantFlag')) else None,
                'internal_or_sensitive_data': str(row.get('InternalOrSensitiveData', '')) if not pd.isna(row.get('InternalOrSensitiveData')) else None,
                'citation_chicago': str(row.get('CitationChicago', '')) if not pd.isna(row.get('CitationChicago')) else None,
                'citation_accessed_date': str(row.get('CitationAccessedDate', '')) if not pd.isna(row.get('CitationAccessedDate')) else None,
                'citation_url': str(row.get('CitationURL', '')) if not pd.isna(row.get('CitationURL')) else None,
            }
            agencies[agency_key]['tools'].append(tool)

    print(f"\nProcessed {len(agencies)} unique agencies")

    # Insert agencies
    print("\nInserting agency profiles...")
    profile_count = 0
    tool_count = 0

    for agency_key, agency_data in agencies.items():
        # Calculate summary flags
        tools = agency_data['tools']
        has_staff_chatbot = any(t['product_type'] == 'staff_chatbot' for t in tools)
        has_coding_assistant = any(t['product_type'] == 'coding_assistant' for t in tools)
        has_document_automation = any(t['product_type'] == 'document_automation' for t in tools)
        tool_count_val = len(tools)

        # Insert profile
        cur.execute("""
            INSERT INTO agency_ai_profiles
            (agency_name, abbreviation, slug, department_level_name, parent_abbreviation,
             deployment_status, has_staff_chatbot, has_coding_assistant, has_document_automation, tool_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            agency_data['agency_name'],
            agency_data['abbreviation'],
            agency_data['slug'],
            agency_data['department_level_name'],
            agency_data['parent'],
            agency_data['deployment_status'],
            has_staff_chatbot,
            has_coding_assistant,
            has_document_automation,
            tool_count_val
        ))

        profile_id = cur.fetchone()[0]
        profile_count += 1

        # Insert tools
        for i, tool in enumerate(tools):
            tool_slug = slugify(f"{agency_data['slug']}-{tool['product_name']}-{i}")

            cur.execute("""
                INSERT INTO agency_ai_tools
                (agency_profile_id, product_name, product_type, slug, available_to_all_staff,
                 is_pilot_or_limited, coding_assistant_flag, internal_or_sensitive_data,
                 citation_chicago, citation_accessed_date, citation_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                profile_id,
                tool['product_name'],
                tool['product_type'],
                tool_slug,
                tool['available_to_all_staff'],
                tool['is_pilot_or_limited'],
                tool['coding_assistant_flag'],
                tool['internal_or_sensitive_data'],
                tool['citation_chicago'],
                tool['citation_accessed_date'],
                tool['citation_url']
            ))
            tool_count += 1

    conn.commit()

    print(f"\n✅ Import complete!")
    print(f"   - Agency profiles: {profile_count}")
    print(f"   - AI tools: {tool_count}")

    # Verify counts
    cur.execute("SELECT COUNT(*) FROM agency_ai_profiles")
    db_profiles = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM agency_ai_tools")
    db_tools = cur.fetchone()[0]

    print(f"\nDatabase verification:")
    print(f"   - agency_ai_profiles: {db_profiles} rows")
    print(f"   - agency_ai_tools: {db_tools} rows")

    # Show sample data
    print("\nSample agency profiles:")
    cur.execute("""
        SELECT agency_name, abbreviation, has_staff_chatbot, has_coding_assistant, tool_count
        FROM agency_ai_profiles
        ORDER BY tool_count DESC
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"   {row[1] or row[0]}: {row[4]} tools (chatbot: {row[2]}, coding: {row[3]})")

    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
