#!/usr/bin/env python3
"""
Export all SQLite tables to JSON files for backup before PostgreSQL migration.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'fedramp.db'
EXPORT_DIR = Path(__file__).parent / 'sqlite_backup'

def export_table_to_json(conn, table_name):
    """Export a single table to JSON file."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")

    # Get column names
    columns = [description[0] for description in cursor.description]

    # Fetch all rows and convert to dict
    rows = []
    for row in cursor.fetchall():
        row_dict = dict(zip(columns, row))
        rows.append(row_dict)

    # Write to JSON file
    output_file = EXPORT_DIR / f"{table_name}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"✅ Exported {len(rows)} records from '{table_name}' to {output_file.name}")
    return len(rows)

def main():
    """Main export function."""
    print(f"🚀 Exporting SQLite data from: {DB_PATH}")
    print(f"📁 Export directory: {EXPORT_DIR}")
    print()

    # Create export directory
    EXPORT_DIR.mkdir(exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Get list of tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"📊 Found {len(tables)} tables to export:")
    for table in tables:
        print(f"   • {table}")
    print()

    # Export each table
    total_records = 0
    for table in tables:
        count = export_table_to_json(conn, table)
        total_records += count

    conn.close()

    # Create metadata file
    metadata = {
        'export_date': datetime.now().isoformat(),
        'source_database': str(DB_PATH),
        'tables_exported': tables,
        'total_records': total_records
    }

    metadata_file = EXPORT_DIR / '_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print()
    print(f"✅ Export complete!")
    print(f"   Total records exported: {total_records}")
    print(f"   Files created in: {EXPORT_DIR}")
    print()

if __name__ == '__main__':
    main()
