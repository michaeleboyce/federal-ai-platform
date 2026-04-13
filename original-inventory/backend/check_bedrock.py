"""
Quick script to check if Amazon Bedrock is included in AWS GovCloud FedRAMP authorization
"""
import json
from pathlib import Path

JSON_PATH = Path(__file__).parent.parent / "data" / "fedramp_products.json"

def check_bedrock():
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)

    products = data['data']['Products']

    # Find AWS products
    aws_products = [p for p in products if 'AWS' in p.get('csp', '').upper() or 'AMAZON' in p.get('csp', '').upper()]

    print("=" * 80)
    print("CHECKING FOR AMAZON BEDROCK IN AWS FEDRAMP AUTHORIZATIONS")
    print("=" * 80)

    for product in aws_products:
        print(f"\nProduct: {product['cso']}")
        print(f"Provider: {product['csp']}")
        print(f"FedRAMP ID: {product['id']}")

        if product.get('all_others'):
            services = product['all_others']
            print(f"Total Services: {len(services)}")

            # Check for Bedrock
            bedrock_services = [s for s in services if 'bedrock' in s.lower()]

            if bedrock_services:
                print("\n✅ AMAZON BEDROCK FOUND!")
                for service in bedrock_services:
                    print(f"   - {service.strip()}")
            else:
                print("\n❌ Amazon Bedrock NOT found in this product")

            # Also show some other AI/ML services
            ai_services = [s for s in services if any(term in s.lower() for term in ['ai', 'sagemaker', 'comprehend', 'rekognition', 'lex', 'polly', 'transcribe', 'translate', 'kendra'])]

            if ai_services:
                print(f"\n🤖 Other AI/ML Services Found ({len(ai_services)}):")
                for service in ai_services[:10]:  # Show first 10
                    print(f"   - {service.strip()}")
                if len(ai_services) > 10:
                    print(f"   ... and {len(ai_services) - 10} more")
        else:
            print("No services list available for this product")

        print("-" * 80)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Check all products for Bedrock
    products_with_bedrock = []
    for product in products:
        if product.get('all_others'):
            if any('bedrock' in s.lower() for s in product['all_others']):
                products_with_bedrock.append(product)

    print(f"\nTotal FedRAMP products: {len(products)}")
    print(f"Products with Amazon Bedrock: {len(products_with_bedrock)}")

    if products_with_bedrock:
        print("\nProducts that include Amazon Bedrock:")
        for p in products_with_bedrock:
            print(f"  - {p['csp']} - {p['cso']} (ID: {p['id']})")

if __name__ == "__main__":
    check_bedrock()
