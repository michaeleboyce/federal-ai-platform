# Catalog gaps — products proposed but not in catalog

These are products the slice agents proposed (with high or medium confidence) but
which don't exist as canonical entries in the `products` table. They are NOT blockers
for this retag (those rows will be skipped or downgraded), but each one is a
catalog-expansion follow-up.

## Direct gaps detected by validator (re-resolution against live DB)

Total distinct proposed names missing from catalog: **0**

_(0 means slice agents only proposed products that already exist in the catalog —
they avoided naming products they knew were absent, instead writing `delete_or_inferred`
for those cases. The follow-up section below lists those known absences.)_

| Proposed product | Rows | Vendor (suggested) | Suggested product_type | Sample agency · use-case |
|---|---|---|---|---|

## Known gaps surfaced by slice agents (follow-up catalog work)

These were flagged in the slice agents' reports as products the agents would have
proposed if they existed in the catalog. The slice agents instead wrote
`delete_or_inferred` for these rows, which means the placeholder edge will be kept
but downgraded to `inferred` — a safe outcome but missed precision.

| Suggested new product | Vendor | Suggested product_type | Approx rows that would benefit |
|---|---|---|---|
| Splunk Enterprise Security | Splunk | security_tool | 4-5 |
| Splunk SOAR | Splunk | security_tool | 2-3 |
| Splunk ITSI | Splunk | observability | 1-2 |
| Splunk AI Assistant for SPL | Splunk | LLM_assistant | 1-2 |
| Splunk Cloud | Splunk | observability | 1-2 |
| Splunk Observability | Splunk | observability | 1-2 |
| Adobe Acrobat | Adobe | productivity | 4-6 |
| Adobe Acrobat AI Assistant | Adobe | LLM_assistant | 2-3 |
| Veritone Redact | Veritone | media_processing | 1-2 |
| Veritone aiWARE | Veritone | platform | 1-2 |
| Veritone Digital Media Hub | Veritone | media_processing | 1 |
| Google BigQuery | Google | analytics | 2-3 |
| Google Document AI | Google | document_ai | 2-3 |
| Google Looker | Google | analytics | 1-2 |
| Google Cloud Storage | Google | cloud_storage | 1 |
| Amazon Polly | Amazon | speech | 1-2 |
| Amazon Q Business | Amazon | LLM_assistant | 2-3 |
| Amazon Q Developer | Amazon | coding_assistant | 1-2 |
| Amazon Textract | Amazon | document_ai | 1-2 |
| Accurint | LexisNexis | investigative_search | 1-2 |
| Law360 | LexisNexis | legal_research | 1 |
| Thomson Reuters Drafting Assistant | Thomson Reuters | legal_research | 1 |

## Notes

- These are **not blockers** — the apply script will downgrade affected rows to
  `inferred` without retag, and they will surface again in a follow-up audit.
- For Splunk especially, the source text often clearly names a specific Splunk product
  (ES / SOAR / ITSI / Observability) — adding those would unlock ~12 downgrades.
- For Adobe Acrobat — the catalog has Creative Cloud / Firefly / Photoshop / Premiere /
  Sensei but no Acrobat row; Acrobat is the most common Adobe deployment in inventory.
- The Amazon catalog uses `Amazon Q` as a single umbrella + `AWS Textract`; splitting into
  Q Business / Q Developer and adding Textract under the `Amazon` vendor would be cleaner.