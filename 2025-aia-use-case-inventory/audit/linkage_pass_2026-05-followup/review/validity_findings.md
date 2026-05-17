# Validity findings

Reviewer V — mechanical validation of integration CSVs (linkage_pass_2026-05-followup).

## Summary
- Links: 6 OK / 0 FAIL (of 6)
- New products: 106 OK / 1 FAIL / 9 WARN (orphan) (of 107)
- Aliases: 11 OK / 1 FAIL (of 12)
- Hierarchy: 39 OK / 15 FAIL (of 54)
- Cross-CSV: 1 OK / 0 FAIL

## VERDICT: 17 FAIL row(s) — DO NOT apply until resolved.

### Root-cause cluster: missing umbrella parent products

Adding each of these as a new_product row (or clearing the parent on the children that reference it) collapses many rows at once:

| missing canonical | # of rows blocked |
|---|---|
| Nuance Dragon | 2 |
| Amazon Alexa | 1 |
| AWS Translate | 1 |
| Amazon Connect | 1 |
| CoCounsel | 1 |
| ProLaw | 1 |
| Cisco Identity Services Engine | 1 |
| Cisco Secure Network Analytics | 1 |
| Slack | 1 |
| Tableau | 1 |
| NotebookLM | 1 |
| Google Maps | 1 |
| Google Lens | 1 |
| Google Pixel | 1 |
| reCAPTCHA | 1 |

## Failures (must fix before --apply)

| CSV | row | issue | proposed fix |
|---|---|---|---|
| proposed_new_products.csv | 13 | proposed_parent 'Nuance Dragon' not resolved | either add umbrella product 'Nuance Dragon' as a new_product row, or clear the parent field |
| proposed_aliases.csv | 2 | alias 'Microsoft 365' already exists for 'Microsoft 365' | drop — duplicate |
| proposed_hierarchy_edges.csv | 3 | child 'Amazon Alexa' not resolved | add 'Amazon Alexa' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 11 | child 'AWS Translate' not resolved | add 'AWS Translate' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 14 | child 'Amazon Connect' not resolved | add 'Amazon Connect' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 16 | child 'CoCounsel' not resolved | add 'CoCounsel' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 17 | child 'ProLaw' not resolved | add 'ProLaw' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 22 | child 'Cisco Identity Services Engine' not resolved | add 'Cisco Identity Services Engine' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 23 | child 'Cisco Secure Network Analytics' not resolved | add 'Cisco Secure Network Analytics' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 25 | child 'Slack' not resolved | add 'Slack' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 26 | child 'Tableau' not resolved | add 'Tableau' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 41 | child 'NotebookLM' not resolved | add 'NotebookLM' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 45 | child 'Google Maps' not resolved | add 'Google Maps' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 46 | child 'Google Lens' not resolved | add 'Google Lens' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 47 | child 'Google Pixel' not resolved | add 'Google Pixel' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 54 | child 'reCAPTCHA' not resolved | add 'reCAPTCHA' as a new_product, or remove this edge |
| proposed_hierarchy_edges.csv | 55 | parent 'Nuance Dragon' not resolved | add umbrella product 'Nuance Dragon' as a new_product, or remove this edge |

## Warnings (review before --apply)

| CSV | row | warning |
|---|---|---|
| proposed_new_products.csv | 100 | orphan add_product 'Amazon Web Services' — no linking use case |
| proposed_new_products.csv | 101 | orphan add_product 'Thomson Reuters' — no linking use case |
| proposed_new_products.csv | 102 | orphan add_product 'Adobe' — no linking use case |
| proposed_new_products.csv | 103 | orphan add_product 'ServiceNow' — no linking use case |
| proposed_new_products.csv | 104 | orphan add_product 'Cisco' — no linking use case |
| proposed_new_products.csv | 105 | orphan add_product 'Salesforce' — no linking use case |
| proposed_new_products.csv | 106 | orphan add_product 'Microsoft' — no linking use case |
| proposed_new_products.csv | 107 | orphan add_product 'Google' — no linking use case |
| proposed_new_products.csv | 108 | orphan add_product 'Amazon' — no linking use case |
