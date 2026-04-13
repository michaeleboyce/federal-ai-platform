#!/usr/bin/env python3
"""
Smart matching algorithm to link federal agency AI usage to FedRAMP services.

This script analyzes agency solution types and matches them to FedRAMP products
based on provider names, keywords, and service descriptions.
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import List, Tuple, Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'data'
DB_PATH = DATA_DIR / 'fedramp.db'
JSON_PATH = DATA_DIR / 'fedramp_products.json'

# Matching rules for provider identification
PROVIDER_MATCHERS = {
    'Microsoft': ['azure', 'microsoft', 'microsoft 365', 'm365', 'office 365', 'o365', 'copilot'],
    'Amazon': ['aws', 'amazon', 'govcloud'],
    'Google': ['google', 'gcp', 'google cloud'],
    'IBM': ['ibm', 'watson'],
    'Oracle': ['oracle'],
    'Salesforce': ['salesforce'],
}

def create_matching_table(conn):
    """Create table to store agency-to-service matches."""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agency_service_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agency_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            provider_name TEXT,
            product_name TEXT,
            confidence TEXT NOT NULL,  -- 'high', 'medium', 'low'
            match_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agency_id) REFERENCES agency_ai_usage(id)
        )
    ''')

    conn.commit()
    print("✅ Matching table created")

def find_provider_in_text(text: str) -> Optional[str]:
    """Find provider name in text using keyword matching."""
    if not text:
        return None

    text_lower = text.lower()

    for provider, keywords in PROVIDER_MATCHERS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return provider

    return None

def match_agency_to_products(agency_data: dict, products: List[dict]) -> List[Tuple[dict, str, str]]:
    """
    Match an agency's AI usage to FedRAMP products.

    Returns: List of (product, confidence, reason) tuples
    """
    matches = []

    solution_type = agency_data.get('solution_type', '')
    notes = agency_data.get('notes', '')

    # Skip if purely custom with no cloud provider mentioned
    if solution_type and 'custom' in solution_type.lower() and 'hosted' in solution_type.lower():
        # Check if it mentions being hosted internally (like NASA-GPT)
        if 'internally hosted' in solution_type.lower() or 'non-cloud' in solution_type.lower():
            return matches

    # Combine solution_type and notes for analysis
    search_text = f"{solution_type} {notes}".lower()

    # Find provider
    provider_name = find_provider_in_text(search_text)

    if not provider_name:
        return matches

    # Find products from this provider
    for product in products:
        product_provider = product.get('csp', '')
        product_name = product.get('cso', '')

        # Check if provider matches
        if provider_name.lower() in product_provider.lower():
            confidence = 'medium'  # Default for provider match
            reason = f"Provider match: {provider_name} mentioned in solution type"

            # Check for specific service mentions
            product_services = product.get('all_others', [])

            # Look for specific AI services in the search text
            ai_keywords = ['openai', 'gpt', 'bedrock', 'sagemaker', 'copilot', 'vertex']

            for keyword in ai_keywords:
                if keyword in search_text:
                    # Check if this product has services matching the keyword
                    for service in product_services:
                        if keyword in service.lower():
                            confidence = 'high'
                            reason = f"Direct service match: '{keyword}' found in both agency data and product services"
                            break

            # Add match
            matches.append((product, confidence, reason))

            # For provider-only matches, only return the main/gov products
            if confidence == 'medium':
                # Prioritize GovCloud/Government versions
                if 'gov' in product_name.lower():
                    break  # Use this one

    return matches

def run_matching(conn):
    """Run the matching algorithm for all agencies."""
    cursor = conn.cursor()

    # Load FedRAMP products
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
        products = data['data']['Products']

    print(f"📊 Loaded {len(products)} FedRAMP products")

    # Get all agencies
    cursor.execute('''
        SELECT id, agency_name, agency_category, solution_type, notes
        FROM agency_ai_usage
        WHERE agency_category = 'staff_llm'
    ''')

    agencies = []
    for row in cursor.fetchall():
        agencies.append({
            'id': row[0],
            'agency_name': row[1],
            'category': row[2],
            'solution_type': row[3],
            'notes': row[4]
        })

    print(f"🏛️  Processing {len(agencies)} agencies")
    print()

    # Clear existing matches
    cursor.execute('DELETE FROM agency_service_matches')
    conn.commit()

    total_matches = 0
    agencies_with_matches = 0

    for agency in agencies:
        matches = match_agency_to_products(agency, products)

        if matches:
            agencies_with_matches += 1
            print(f"✓ {agency['agency_name']}")

            for product, confidence, reason in matches:
                cursor.execute('''
                    INSERT INTO agency_service_matches
                    (agency_id, product_id, provider_name, product_name, confidence, match_reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    agency['id'],
                    product['id'],
                    product['csp'],
                    product['cso'],
                    confidence,
                    reason
                ))
                total_matches += 1

                # Show match details
                print(f"  → {product['csp']} - {product['cso']} ({confidence} confidence)")

    conn.commit()

    print()
    print("📈 Matching Results:")
    print(f"   Agencies processed: {len(agencies)}")
    print(f"   Agencies with matches: {agencies_with_matches}")
    print(f"   Total matches found: {total_matches}")

    # Show confidence breakdown
    for conf_level in ['high', 'medium', 'low']:
        cursor.execute('SELECT COUNT(*) FROM agency_service_matches WHERE confidence = ?', (conf_level,))
        count = cursor.fetchone()[0]
        print(f"   {conf_level.capitalize()} confidence: {count}")

def main():
    """Main execution function."""
    print("🔗 Smart Matching: Agency AI Usage → FedRAMP Services")
    print("=" * 60)
    print()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Create matching table
    create_matching_table(conn)
    print()

    # Run matching
    run_matching(conn)
    print()

    # Show some examples
    cursor = conn.cursor()
    print("📋 Sample Matches:")
    cursor.execute('''
        SELECT
            a.agency_name,
            m.provider_name,
            m.product_name,
            m.confidence,
            m.match_reason
        FROM agency_service_matches m
        JOIN agency_ai_usage a ON a.id = m.agency_id
        WHERE m.confidence = 'high'
        LIMIT 5
    ''')

    for row in cursor.fetchall():
        print(f"   • {row[0]}")
        print(f"     ↳ {row[1]} - {row[2]}")
        print(f"     ↳ {row[4]}")
        print()

    conn.close()
    print("✅ Done! Agency-to-service matching complete")
    return 0

if __name__ == '__main__':
    exit(main())
