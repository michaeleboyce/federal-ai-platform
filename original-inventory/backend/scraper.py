"""
Web scraper for FedRAMP marketplace product pages using Playwright
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from db import get_connection, update_scrape_status, get_unscraped_products, get_scrape_stats

HTML_DIR = Path(__file__).parent.parent / "data" / "html"
BASE_URL = "https://marketplace.fedramp.gov/products"
MAX_WORKERS = 5  # Reduced for browser-based scraping

def scrape_product_page_with_browser(fedramp_id: str) -> tuple[str, bool, str]:
    """
    Scrape a single product page using Playwright
    Returns: (fedramp_id, success, html_content_or_error)
    """
    url = f"{BASE_URL}/{fedramp_id}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()

            # Navigate to page with timeout
            response = page.goto(url, wait_until='networkidle', timeout=30000)

            # Check if page loaded successfully
            if response and response.status == 200:
                # Wait a bit for any dynamic content
                page.wait_for_timeout(1000)

                # Get the HTML content
                html_content = page.content()

                # Save HTML to file
                html_path = HTML_DIR / f"{fedramp_id}.html"
                html_path.write_text(html_content, encoding='utf-8')

                browser.close()

                # Return relative path for database
                relative_path = f"data/html/{fedramp_id}.html"
                return fedramp_id, True, relative_path
            else:
                browser.close()
                error_msg = f"HTTP {response.status if response else 'No response'}"
                return fedramp_id, False, error_msg

    except PlaywrightTimeoutError:
        error_msg = f"Timeout loading {fedramp_id}"
        print(error_msg, file=sys.stderr)
        return fedramp_id, False, error_msg
    except Exception as e:
        error_msg = f"Error scraping {fedramp_id}: {str(e)}"
        print(error_msg, file=sys.stderr)
        return fedramp_id, False, error_msg

def scrape_all_products(max_workers: int = MAX_WORKERS):
    """Scrape all unscraped products from database"""

    # Ensure HTML directory exists
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    # Get connection and unscraped products
    conn = get_connection()
    products = get_unscraped_products(conn)

    if not products:
        print("No products to scrape!")
        stats = get_scrape_stats(conn)
        print(f"Stats: {stats['scraped']}/{stats['total']} products already scraped")
        conn.close()
        return

    print(f"Starting scrape of {len(products)} products with {max_workers} workers...")
    print("Using Playwright browser automation for scraping...")

    success_count = 0
    error_count = 0

    # Use ThreadPoolExecutor for concurrent scraping
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_id = {
            executor.submit(scrape_product_page_with_browser, p['fedramp_id']): p['fedramp_id']
            for p in products
        }

        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_id), 1):
            fedramp_id, success, result = future.result()

            if success:
                # Update database
                update_scrape_status(conn, fedramp_id, result)
                success_count += 1
                print(f"[{i}/{len(products)}] ✓ Scraped {fedramp_id}")
            else:
                error_count += 1
                print(f"[{i}/{len(products)}] ✗ Failed {fedramp_id}: {result}")

            # Commit every 25 products
            if i % 25 == 0:
                conn.commit()
                print(f"Progress: {success_count} success, {error_count} errors")

    # Final commit
    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"Scraping complete!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(products)}")
    print(f"HTML files saved to: {HTML_DIR}")
    print(f"{'='*60}")

def get_stats():
    """Print scraping statistics"""
    conn = get_connection()
    stats = get_scrape_stats(conn)
    conn.close()

    print(f"\nScraping Statistics:")
    print(f"  Total products: {stats['total']}")
    print(f"  Scraped: {stats['scraped']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Progress: {stats['scraped']/stats['total']*100:.1f}%\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scrape FedRAMP marketplace products')
    parser.add_argument('--stats', action='store_true', help='Show scraping statistics')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='Number of concurrent workers')

    args = parser.parse_args()

    if args.stats:
        get_stats()
    else:
        scrape_all_products(max_workers=args.workers)
