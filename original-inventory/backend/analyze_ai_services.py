"""
AI Service Analysis Job using Claude Haiku 4.5
Analyzes FedRAMP products to identify AI, Generative AI, and LLM services
"""
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import anthropic
from dotenv import load_dotenv
from db import get_connection, initialize_database, insert_ai_analysis, clear_ai_analysis, get_ai_stats, record_product_analysis_run

# Load environment variables
load_dotenv()

JSON_PATH = Path(__file__).parent.parent / "data" / "fedramp_products.json"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def load_products() -> List[Dict[str, Any]]:
    """Load all products from JSON"""
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    return data['data']['Products']

def analyze_product_with_claude(product: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyze a single product using Claude Haiku 4.5
    Returns list of AI services found in this product
    """
    # Extract product details
    product_id = product.get('id', '')
    product_name = product.get('cso', '')
    provider = product.get('csp', '')
    description = product.get('service_desc', '')
    services = product.get('all_others', [])
    status = product.get('status', '')
    impact_level = product.get('impact_level', [])
    if isinstance(impact_level, list):
        impact_level = ', '.join(impact_level)
    auth_date = product.get('auth_date', '')

    # Handle agencies field - can be string, list, dict, or None
    agencies = product.get('agency_authorizations', '')
    if isinstance(agencies, list):
        agencies = ', '.join(str(a) for a in agencies)
    elif isinstance(agencies, dict):
        agencies = json.dumps(agencies)
    elif agencies is None:
        agencies = ''
    else:
        agencies = str(agencies)

    if not services:
        return []

    # Create prompt for Claude
    services_list = '\n'.join([f"- {s.strip()}" for s in services[:100]])  # Limit to first 100 services

    prompt = f"""Analyze this FedRAMP cloud product and identify which of its services relate to AI, Generative AI, or Large Language Models.

**Product Information:**
- Provider: {provider}
- Product: {product_name}
- Description: {description[:1000]}...

**Services to Analyze:**
{services_list}

**Instructions:**
For EACH service that relates to AI, Generative AI, or LLMs, return a JSON object with:
- service_name: exact name of the service
- has_ai: true if it's AI-related (general AI, machine learning, ML)
- has_genai: true if it's specifically Generative AI
- has_llm: true if it's specifically for Large Language Models
- relevant_excerpt: brief explanation (1-2 sentences) of why this service is AI-related

Return ONLY a JSON array of services that are AI-related. If no services are AI-related, return an empty array [].

Example format:
[
  {{
    "service_name": "Amazon Bedrock",
    "has_ai": true,
    "has_genai": true,
    "has_llm": true,
    "relevant_excerpt": "Amazon Bedrock is a fully managed service for building and scaling generative AI applications using foundation models including large language models."
  }}
]

IMPORTANT: Only include services that are clearly AI, GenAI, or LLM related. Do not include general cloud services."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse Claude's response
        response_text = message.content[0].text.strip()

        # Extract JSON from response (handle code blocks)
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()

        ai_services = json.loads(response_text)

        # Add product metadata to each service
        results = []
        for service in ai_services:
            results.append({
                'product_id': product_id,
                'product_name': product_name,
                'provider_name': provider,
                'service_name': service.get('service_name', ''),
                'has_ai': service.get('has_ai', False),
                'has_genai': service.get('has_genai', False),
                'has_llm': service.get('has_llm', False),
                'relevant_excerpt': service.get('relevant_excerpt', ''),
                'fedramp_status': status,
                'impact_level': impact_level,
                'agencies': agencies,
                'auth_date': auth_date
            })

        return results

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON for {product_name}: {e}")
        print(f"Response was: {response_text[:200]}...")
        return []
    except Exception as e:
        print(f"❌ Error analyzing {product_name}: {e}")
        return []

def analyze_all_products(max_workers: int = 10, clear_existing: bool = True):
    """Analyze all products in parallel"""

    # Initialize database
    initialize_database()

    # Load products
    products = load_products()
    print(f"📊 Loaded {len(products)} products")

    # Clear existing analysis if requested
    if clear_existing:
        conn = get_connection()
        clear_ai_analysis(conn)
        conn.close()
        print("🗑️  Cleared existing analysis")

    # Analyze in parallel
    print(f"🚀 Starting analysis with {max_workers} workers...")
    print(f"⏱️  Estimated time: {len(products) * 2 / max_workers / 60:.1f} minutes\n")

    conn = get_connection()
    total_ai_services = 0
    processed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_product = {
            executor.submit(analyze_product_with_claude, product): product
            for product in products
        }

        # Process completed tasks
        for future in as_completed(future_to_product):
            product = future_to_product[future]
            processed_count += 1

            try:
                ai_services = future.result()

                # Record that this product was analyzed
                record_product_analysis_run(
                    conn,
                    product.get('id', ''),
                    product.get('cso', ''),
                    product.get('csp', ''),
                    len(ai_services)
                )

                # Save results to database
                for service in ai_services:
                    insert_ai_analysis(conn, service)
                    total_ai_services += 1

                if ai_services:
                    print(f"[{processed_count}/{len(products)}] ✅ {product.get('csp', 'Unknown')} - {product.get('cso', 'Unknown')}: Found {len(ai_services)} AI services")
                else:
                    print(f"[{processed_count}/{len(products)}] ⚪ {product.get('csp', 'Unknown')} - {product.get('cso', 'Unknown')}: No AI services")

                # Commit every 10 products
                if processed_count % 10 == 0:
                    conn.commit()

            except Exception as e:
                print(f"[{processed_count}/{len(products)}] ❌ Error processing {product.get('cso', 'Unknown')}: {e}")

    # Final commit
    conn.commit()

    # Print statistics
    stats = get_ai_stats(conn)
    conn.close()

    print(f"\n{'='*70}")
    print(f"🎉 ANALYSIS COMPLETE!")
    print(f"{'='*70}")
    print(f"📊 Total AI Services Found: {stats['total_ai_services']}")
    print(f"   - AI Services: {stats['count_ai']}")
    print(f"   - Generative AI Services: {stats['count_genai']}")
    print(f"   - LLM Services: {stats['count_llm']}")
    print(f"\n📦 Products with AI: {stats['products_with_ai']} out of {len(products)}")
    print(f"🏢 Providers with AI: {stats['providers_with_ai']}")
    print(f"{'='*70}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyze FedRAMP products for AI services')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers')
    parser.add_argument('--no-clear', action='store_true', help='Don\'t clear existing analysis')

    args = parser.parse_args()

    analyze_all_products(max_workers=args.workers, clear_existing=not args.no_clear)
