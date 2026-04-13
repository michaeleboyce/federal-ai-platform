"""
Load FedRAMP products from CSV into database
"""
import csv
import sys
from pathlib import Path
from db import get_connection, initialize_database, insert_product

CSV_PATH = Path("/Users/michaelboyce/Downloads/marketplace-20251025-111714.csv")

def load_csv_to_database():
    """Parse CSV and load products into database"""

    # Initialize database
    initialize_database()

    # Open connection
    conn = get_connection()

    # Track unique products
    seen_ids = set()
    total_rows = 0
    unique_products = 0

    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                total_rows += 1

                fedramp_id = row.get('FedRAMP ID', '').strip()
                if not fedramp_id:
                    continue

                # Only insert unique FedRAMP IDs (CSV has duplicates for different agencies)
                if fedramp_id not in seen_ids:
                    seen_ids.add(fedramp_id)

                    product_data = {
                        'fedramp_id': fedramp_id,
                        'cloud_service_provider': row.get('Cloud Service Provider', ''),
                        'cloud_service_offering': row.get('Cloud Service Offering', ''),
                        'service_description': row.get('Service Description', ''),
                        'business_categories': row.get('Business Categories', ''),
                        'service_model': row.get('Service Model', ''),
                        'status': row.get('Status', ''),
                        'independent_assessor': row.get('Independent Assessor', ''),
                        'authorizations': row.get('Authorizations', ''),
                        'reuse': row.get('Reuse', ''),
                        'parent_agency': row.get('Parent Agency', ''),
                        'sub_agency': row.get('Sub Agency', ''),
                        'ato_issuance_date': row.get('ATO Issuance Date', ''),
                        'fedramp_authorization_date': row.get('FedRAMP Authorization Date', ''),
                        'annual_assessment_date': row.get('Annual Assessment Date', ''),
                        'ato_expiration_date': row.get('ATO Expiration Date', ''),
                    }

                    insert_product(conn, product_data)
                    unique_products += 1

                    if unique_products % 100 == 0:
                        print(f"Loaded {unique_products} unique products...")
                        conn.commit()

        conn.commit()
        print(f"\n✓ Successfully loaded {unique_products} unique products from {total_rows} total rows")

    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    load_csv_to_database()
