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

Verified unreferenced by `Makefile`, `tests/`, and the other scripts before
archiving. If you need to understand a current tag's origin, start with
`auto_tag.py` and the `audit/retag/` rollups, not these.
