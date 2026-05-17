# Validity findings

Reviewer V — mechanical validation of integration CSVs (linkage_pass_2026-05).

## Summary
- Links: 105 OK / 6 FAIL (of 111)
- New products: 192 OK / 24 FAIL / 0 WARN (orphan) (of 216)
- Aliases: 7 OK / 0 FAIL (of 7)
- Hierarchy: 16 OK / 22 FAIL (of 38)
- Cross-CSV: 31 OK / 0 FAIL

## VERDICT: 52 FAIL row(s) — DO NOT apply until resolved.

### Root-cause cluster: missing umbrella parent products

The majority of failures are duplicates of a small set of unresolved canonical names. Adding each of these as a new_product row (or clearing the parent on the children that reference it) collapses many rows at once:

| missing canonical | # of rows blocked |
|---|---|
| FDA CDEROne Analytics | 16 |
| GrantSolutions | 12 |
| FTC Sentinel Network Services | 10 |
| Grants.gov AI Tools | 4 |
| ELIS | 2 |

## Failures (must fix before --apply)

| CSV | row | issue | proposed fix |
|---|---|---|---|
| proposed_links.csv | 17 | canonical 'AWS' not in catalog or new_products | either remap to an existing canonical name, or add 'AWS' to proposed_new_products.csv |
| proposed_links.csv | 27 | canonical 'Amazon Comprehend' not in catalog or new_products | either remap to an existing canonical name, or add 'Amazon Comprehend' to proposed_new_products.csv |
| proposed_links.csv | 46 | canonical 'NanCI' not in catalog or new_products | either remap to an existing canonical name, or add 'NanCI' to proposed_new_products.csv |
| proposed_links.csv | 68 | canonical 'VegSpec' not in catalog or new_products | either remap to an existing canonical name, or add 'VegSpec' to proposed_new_products.csv |
| proposed_links.csv | 83 | evidence_quote not substring of row text: 'Output is via a both a chat window or copilot for internal use.' | re-extract evidence_quote verbatim from the source row, or drop the link if no real evidence exists |
| proposed_links.csv | 111 | evidence_quote not substring of row text: 'system_name: Azure GOV' | re-extract evidence_quote verbatim from the source row, or drop the link if no real evidence exists |
| proposed_new_products.csv | 20 | proposed_parent 'ELIS' not resolved | either add umbrella product 'ELIS' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 49 | canonical 'Ultralytics YOLO' already in catalog | remove from new_products and convert any linking rows into proposed_links.csv entries |
| proposed_new_products.csv | 84 | proposed_parent 'FTC Sentinel Network Services' not resolved | either add umbrella product 'FTC Sentinel Network Services' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 85 | proposed_parent 'FTC Sentinel Network Services' not resolved | either add umbrella product 'FTC Sentinel Network Services' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 86 | proposed_parent 'FTC Sentinel Network Services' not resolved | either add umbrella product 'FTC Sentinel Network Services' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 87 | proposed_parent 'FTC Sentinel Network Services' not resolved | either add umbrella product 'FTC Sentinel Network Services' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 88 | proposed_parent 'FTC Sentinel Network Services' not resolved | either add umbrella product 'FTC Sentinel Network Services' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 97 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 98 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 99 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 100 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 101 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 102 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 103 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 104 | proposed_parent 'FDA CDEROne Analytics' not resolved | either add umbrella product 'FDA CDEROne Analytics' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 127 | proposed_parent 'Grants.gov AI Tools' not resolved | either add umbrella product 'Grants.gov AI Tools' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 128 | proposed_parent 'Grants.gov AI Tools' not resolved | either add umbrella product 'Grants.gov AI Tools' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 129 | proposed_parent 'GrantSolutions' not resolved | either add umbrella product 'GrantSolutions' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 130 | proposed_parent 'GrantSolutions' not resolved | either add umbrella product 'GrantSolutions' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 131 | proposed_parent 'GrantSolutions' not resolved | either add umbrella product 'GrantSolutions' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 132 | proposed_parent 'GrantSolutions' not resolved | either add umbrella product 'GrantSolutions' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 133 | proposed_parent 'GrantSolutions' not resolved | either add umbrella product 'GrantSolutions' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 134 | proposed_parent 'GrantSolutions' not resolved | either add umbrella product 'GrantSolutions' as a new_product row, or clear the parent field on this row |
| proposed_new_products.csv | 206 | product_type 'library_management' not in controlled vocab | swap 'library_management' for a value already in data/expanded_product_catalog.csv (likely 'workflow_automation' or 'data_management') |
| proposed_hierarchy_edges.csv | 9 | parent 'ELIS' not resolved | add umbrella product 'ELIS' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 12 | parent 'FTC Sentinel Network Services' not resolved | add umbrella product 'FTC Sentinel Network Services' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 13 | parent 'FTC Sentinel Network Services' not resolved | add umbrella product 'FTC Sentinel Network Services' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 14 | parent 'FTC Sentinel Network Services' not resolved | add umbrella product 'FTC Sentinel Network Services' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 15 | parent 'FTC Sentinel Network Services' not resolved | add umbrella product 'FTC Sentinel Network Services' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 16 | parent 'FTC Sentinel Network Services' not resolved | add umbrella product 'FTC Sentinel Network Services' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 19 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 20 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 21 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 22 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 23 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 24 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 25 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 26 | parent 'FDA CDEROne Analytics' not resolved | add umbrella product 'FDA CDEROne Analytics' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 28 | parent 'Grants.gov AI Tools' not resolved | add umbrella product 'Grants.gov AI Tools' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 29 | parent 'Grants.gov AI Tools' not resolved | add umbrella product 'Grants.gov AI Tools' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 30 | parent 'GrantSolutions' not resolved | add umbrella product 'GrantSolutions' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 31 | parent 'GrantSolutions' not resolved | add umbrella product 'GrantSolutions' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 32 | parent 'GrantSolutions' not resolved | add umbrella product 'GrantSolutions' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 33 | parent 'GrantSolutions' not resolved | add umbrella product 'GrantSolutions' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 34 | parent 'GrantSolutions' not resolved | add umbrella product 'GrantSolutions' as a new_product row, or remove this edge |
| proposed_hierarchy_edges.csv | 35 | parent 'GrantSolutions' not resolved | add umbrella product 'GrantSolutions' as a new_product row, or remove this edge |

## Warnings (review before --apply)

_None._
