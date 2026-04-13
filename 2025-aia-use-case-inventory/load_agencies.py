"""Load agency-inventory-tracker.csv into the agencies table."""

import csv
from pathlib import Path

from db import get_connection

TRACKER_CSV = Path(__file__).parent / "agency-inventory-tracker.csv"


def load_agencies():
    conn = get_connection()
    try:
        with open(TRACKER_CSV, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if not row.get("agency_name") or not row.get("abbreviation"):
                    continue

                # Parse schema_compliance to float if present
                sc = row.get("schema_compliance", "").strip()
                try:
                    schema_compliance = float(sc) if sc else None
                except ValueError:
                    schema_compliance = None

                # Parse year
                year = row.get("inventory_year", "").strip()
                try:
                    inventory_year = int(year) if year else None
                except ValueError:
                    inventory_year = None

                conn.execute(
                    """
                    INSERT OR REPLACE INTO agencies (
                        name, abbreviation, agency_type, inventory_page_url,
                        csv_download_url, inventory_year, status, schema_compliance,
                        notes, last_modified, date_accessed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["agency_name"].strip(),
                        row["abbreviation"].strip(),
                        row.get("agency_type", "").strip() or None,
                        row.get("inventory_page_url", "").strip() or None,
                        row.get("csv_download_url", "").strip() or None,
                        inventory_year,
                        row.get("status", "").strip() or None,
                        schema_compliance,
                        row.get("notes", "").strip() or None,
                        row.get("last_modified", "").strip() or None,
                        row.get("date_accessed", "").strip() or None,
                    ),
                )
                count += 1
            conn.commit()
            print(f"Loaded {count} agencies")
    finally:
        conn.close()


if __name__ == "__main__":
    load_agencies()
