# May 2026 linkage-pass lossage audit

Run by `scripts/audit_linkage_pass_lossage.py`. Diffs every proposal staged in `audit/linkage_pass_2026-05/integration/*.csv` and `audit/linkage_pass_2026-05-followup/integration/*.csv` against the current state of `data/federal_ai_inventory_2025.db`.

## Summary

| Kind | Staged | Landed | Missing | Cross-table landed |
|---|---:|---:|---:|---:|
| `add_product` | 330 | 326 | 4 | — |
| `link` (proposed_links.csv) | 115 | 113 | 2 | 0 |
| `link_via_add_product` (linking_*_ids columns) | 321 | 314 | 0 | 7 |
| `add_alias` | 19 | 19 | 0 | — |
| `add_hierarchy_edge` | 92 | 90 | 2 | — |

## Missing `add_product` proposals

| _pass | canonical_name | vendor | confidence | _agent |
|---|---|---|---|---|
| linkage_pass_2026-05 | OpenAI Codex | OpenAI | high | agent_b |
| linkage_pass_2026-05 | Grants.gov AI Tools | Grants.gov | medium | fixup_validity |
| linkage_pass_2026-05 | NanCI | National Institutes of Health | high | fixup_validity |
| linkage_pass_2026-05 | VegSpec | U.S. Department of Agriculture | high | fixup_validity |

## Missing `link` proposals

| _pass | _agent | entry_kind | entry_id | canonical_name | _reason |
|---|---|---|---|---|---|
| linkage_pass_2026-05 | agent_a | use_case | 66700 | NanCI | product 'NanCI' not in current DB |
| linkage_pass_2026-05 | agent_a | use_case | 67782 | VegSpec | product 'VegSpec' not in current DB |

## Missing `link_via_add_product` (per linking_*_ids column)

_(none)_

## Missing `add_alias` proposals

_(none)_

## Missing `add_hierarchy_edge` proposals

| _pass | _agent | child_canonical_name | parent_canonical_name | _reason |
|---|---|---|---|---|
| linkage_pass_2026-05 | agent_a | Grants.gov Similar Opportunities | Grants.gov AI Tools | child=ok parent=missing |
| linkage_pass_2026-05 | agent_a | Grants.gov Applicant Help Chatbot | Grants.gov AI Tools | child=ok parent=missing |

