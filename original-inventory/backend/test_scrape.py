"""Test script to scrape a single product"""
from playwright.sync_api import sync_playwright
from pathlib import Path

HTML_DIR = Path(__file__).parent.parent / "data" / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)

fedramp_id = "FR2513049676"
url = f"https://marketplace.fedramp.gov/products/{fedramp_id}"

print(f"Testing scrape of {url}...")

with sync_playwright() as p:
    print("Launching browser...")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()

    print(f"Navigating to {url}...")
    response = page.goto(url, wait_until='domcontentloaded', timeout=30000)

    print(f"Response status: {response.status}")

    # Accept 200-299 status codes
    if 200 <= response.status < 300:
        print("Waiting for page to load completely...")
        # Wait for the main heading to appear
        try:
            page.wait_for_selector('h1', timeout=10000)
            print("Page content loaded!")
        except:
            print("Timeout waiting for content, but continuing...")

        page.wait_for_timeout(3000)

        html_content = page.content()
        print(f"Got HTML content ({len(html_content)} bytes)")

        html_path = HTML_DIR / f"{fedramp_id}.html"
        html_path.write_text(html_content, encoding='utf-8')
        print(f"Saved to {html_path}")
        print(f"File exists: {html_path.exists()}")
    else:
        print(f"Failed with status {response.status}")

    browser.close()
    print("Done!")
