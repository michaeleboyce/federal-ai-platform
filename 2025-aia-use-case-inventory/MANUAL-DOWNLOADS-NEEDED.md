# Manual Downloads Needed (April 11, 2026)

URLs that need to be downloaded in a browser due to Cloudflare/WAF blocking automated requests.
Save files to: `data/raw/`

## Blocked by Cloudflare/WAF (have 2025 inventories but curl gets 403/blocked)

1. **HHS** - FY25 AI Use Case Inventory CSV (~474KB)
   - URL: https://www.hhs.gov/sites/default/files/hhs-ai-use-case-inventory-fy25.csv
   - Save as: `HHS-2025-ai-inventory.csv`
   - Landing page: https://www.hhs.gov/programs/topic-sites/ai/use-cases/index.html

2. **State Dept** - 2025 AI Use Case Inventory CSV (~659KB page, but CSV link needs browser)
   - Landing page: https://www.state.gov/department-of-state-2025-ai-inventory/
   - Note: Main page may still show "Technical Difficulties." Try this direct URL:
   - URL: https://www.state.gov/wp-content/uploads/2026/04/Tab-1-2025-AI-Use-Case-Inventory-Reporting-spreadsheet-updated-2026-04-02.csv
   - Save as: `State-2025-ai-inventory.csv`

3. **FCC** - 2025 AI Use Cases XLSX (HTTP/2 stream errors)
   - URL: https://www.fcc.gov/sites/default/files/ai-use-cases.xlsx
   - Save as: `FCC-2025-ai-inventory.xlsx`
   - Full inventory: https://www.fcc.gov/sites/default/files/fcc-ai-use-cases-full-nnventory.xlsx
   - Save as: `FCC-2025-ai-inventory-full.xlsx`
   - Landing page: https://www.fcc.gov/ai

4. **SBA** - 2025 AI Use Case Inventory XLSX (~42KB)
   - Landing page: https://www.sba.gov/about-sba/open-government/ai-inventory
   - Document page: https://www.sba.gov/document/support-sba-ai-use-case-inventory
   - Save as: `SBA-2025-ai-inventory.xlsx`
   - Consolidated: https://www.sba.gov/document/support-sba-consolidated-ai-use-case-inventory
   - Save as: `SBA-2025-ai-inventory-consolidated.xlsx`

5. **DOC** - Likely has 2025 inventory (page updated Feb 2026, Cloudflare blocking)
   - Landing page: https://www.commerce.gov/about/policies/artificial-intelligence-use-cases-inventory
   - Download page: https://www.commerce.gov/files/department-commerce-artificial-intelligence-ai-use-case-inventory
   - Save as: `DOC-2025-ai-inventory.xlsx` or `.csv`

## HTML-only inventories (need scraping or manual copy)

6. **ED** - Department of Education (HTML table, no CSV/XLSX download)
   - URL: https://www.ed.gov/about/ed-overview/artificial-intelligence-ai-guidance
   - Would need to copy table data and save as: `ED-2025-ai-inventory.csv`

7. **USITC** - HTML table only (11 use cases)
   - URL: https://www.usitc.gov/data/ai_inventory
   - Save as: `USITC-2025-ai-inventory.csv`

## Newly discovered agencies NOT in tracker (from missing-agencies search)

8. **TVA** - Tennessee Valley Authority (39 use cases in 2024)
   - URL: https://www.tva.com/information/tva-ai-use-case-inventory
   - Save as: `TVA-2025-ai-inventory.csv` or `.xlsx`

9. **PBGC** - Pension Benefit Guaranty Corporation (updated Feb 2026)
   - URL: https://www.pbgc.gov/about/information-technology/artificial-intelligence
   - Save as: `PBGC-2025-ai-inventory.csv` or `.xlsx`

10. **EAC** - Election Assistance Commission
    - URL: https://www.eac.gov/AI
    - Save as: `EAC-2025-ai-inventory.csv` or `.xlsx`

11. **USTDA** - U.S. Trade and Development Agency (Jan 2026)
    - URL: https://www.ustda.gov/ai/
    - Save as: `USTDA-2025-ai-inventory.csv` or `.xlsx`

12. **GPO** - Government Publishing Office (Dec 2025)
    - URL: https://www.gpo.gov/explore-and-research/government-information/ai
    - Save as: `GPO-2025-ai-inventory.csv` or `.xlsx`

13. **FRTIB** - Federal Retirement Thrift Investment Board
    - URL: https://www.frtib.gov/data/ai_inventory/
    - Save as: `FRTIB-2025-ai-inventory.csv` or `.xlsx`

14. **PRC** - Postal Regulatory Commission
    - URL: https://www.prc.gov/prc-ai-catalog
    - Save as: `PRC-2025-ai-inventory.csv` or `.xlsx`

15. **EXIM** - Export-Import Bank (consolidated COTS CSV, 3KB)
    - URL: https://www.exim.gov/ai-inventory (click "2025 Consolidated AI Use Case Reporting" link)
    - Save as: `EXIM-2025-ai-inventory.csv`

## Agencies with updates to re-download (verification found changes)

- **NSF** updated on server (Feb 10 vs our Feb 3 download) - already re-downloaded
- **FHFA** updated with new URL - already re-downloaded
- **DOJ** note: remote file metadata says "FINAL_2024" - may still be 2024 data at that URL. Verify.
