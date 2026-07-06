# Archived one-off scripts

Scripts here were applied once during a specific tagging/audit wave and are
no longer part of the `make fix` chain. They are kept for provenance — the
audit trail of how the `use_case_tags` layer was developed — not for re-use.
Their effects are baked into the committed DB and (where they encode durable
rules) re-expressed in the authoritative `auto_tag.py` / `scripts/retag_*.py`
passes that `make fix` runs.

| Script | Wave | Applied | Purpose |
|---|---|---|---|
| `_tag_wave1_D.py` | Wave 1 (D) | May 2026 | First-pass multi-agent tagging, batch D. |
| `_wave1_E_tag.py` | Wave 1 (E) | May 2026 | First-pass multi-agent tagging, batch E. |
| `wave2b_retired_qa.py` | Wave 2b | May 2026 | QA pass over `retired_2024` lineage tags. |
| `wave3_reconcile_P1.py` | Wave 3 (P1) | May 2026 | Reconciliation pass, partition 1. |
| `wave3_reconcile_P2.py` | Wave 3 (P2) | May 2026 | Reconciliation pass, partition 2. |
| `wave3_reconcile_P3.py` | Wave 3 (P3) | May 2026 | Reconciliation pass, partition 3. |
| `apply_coord_llm_review.py` | LLM review | May 2026 | Applied coordinator-dispatched LLM review results (B/D queues). |
| `apply_llm_review.py` | LLM review | May 2026 | Applied review_queue_llm labels (table dropped by m021). |
| `apply_review2.py` | Round 2 | May 2026 | Applied round-2 micro-agent product/entry_type results. |
| `build_review_queue_llm.py` | LLM review | May 2026 | Populated review_queue_llm (table dropped by m021). |
| `export_review_queue_llm_unresolved.py` | LLM review | May 2026 | Exported unresolved review_queue_llm rows (table dropped by m021). |
| `populate_review_queue_scope.py` | Scope queue | May 2026 | Populated review_queue_scope (table dropped by m021). |
| `review_queue_scope_adjudicate.py` | Scope queue | May 2026 | Adjudicated review_queue_scope rows (table dropped by m021). |
| `compute_maturity.py` | Maturity | Jun 2026 | Old agency-level maturity computation — superseded by `compute_org_maturity.py` (m023 collapse). |
| `migrate_add_hierarchy.py` | Hierarchy | May 2026 | Pre-runner DDL one-off; ALTERs the now-view `agency_ai_maturity` — would error if re-run. |
| `retag_entry_type.py` | Entry type | May 2026 | Surgical entry_type recompute; reads the m025-dropped scalar columns — would error if re-run. |
| `fix_templates.py` | Templates | May 2026 | One-off template relink; reads the m025-dropped `use_cases.template_id` — would error if re-run. |
| `generate_remediation_report.py` | Remediation | Apr 2026 | Point-in-time remediation report; reads the m025-dropped `use_cases.product_id` — would error if re-run. |

Verified unreferenced by `Makefile`, `tests/`, and the other scripts before
archiving. If you need to understand a current tag's origin, start with
`auto_tag.py` and the `audit/retag/` rollups, not these.
