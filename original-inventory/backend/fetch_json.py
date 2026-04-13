"""
Fetch FedRAMP marketplace data from official JSON API
This is much better than scraping HTML pages!
"""
import requests
import json
from pathlib import Path

JSON_URL = "https://raw.githubusercontent.com/GSA/marketplace-fedramp-gov-data/refs/heads/main/data.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "fedramp_products.json"

def fetch_and_save_json():
    """Fetch JSON data from official source and save locally"""
    print(f"Fetching data from: {JSON_URL}")

    response = requests.get(JSON_URL, timeout=30)
    response.raise_for_status()

    data = response.json()

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully saved JSON data to: {OUTPUT_FILE}")

    # Print some stats
    products = data.get('data', {}).get('Products', [])
    print(f"✓ Total products: {len(products)}")

    if products:
        print(f"✓ Sample product ID: {products[0]['id']}")
        print(f"✓ Available fields: {', '.join(products[0].keys())}")

    return data

if __name__ == "__main__":
    fetch_and_save_json()
