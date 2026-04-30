# Human Review Coordinator

## Check
This file is the coordinator handoff for the human-style review pass executed on `2026-04-12`. It normalizes the legacy `B/C/D/E` queue language to the current audit artifacts, locks the authoritative row counts, and records which output files now own each follow-up stream.

## Method
- Treated the semantic queue files in `audit/` as the source of truth.
- Counted rows with CSV parsing, not line counts, because multiline quoted fields inflate `wc -l` totals in the product queue.
- Collected completed worker outputs and reconciled them against the parsed queue totals.

## Findings
### Queue mapping
| Legacy label | Current artifact | Parsed rows | Owner output |
| --- | --- | ---: | --- |
| `B-queue` | `audit/review_queue_llm_unresolved.csv` | `250` | `audit/human_review_llm_queue.md` |
| `C-queue` | `audit/review_queue_entry_type_unresolved.csv` | `228` | `audit/human_review_entry_type.md` |
| `D-queue` | `audit/review_queue_products_unresolved.csv` | `844` | `audit/human_review_products.md` |
| `D-queue aliases` | `audit/proposed_aliases.csv` | `162` | `audit/human_review_aliases.md` + alias partition CSVs |
| `E-queue` | `audit/review_queue_scope_unresolved.csv` | `166` | `audit/human_review_scope.md` |
| pipeline blocker | LLM rebuild drift | n/a | `audit/human_review_llm_drift.md` |

### Disposition summary
| Stream | Dispositions |
| --- | --- |
| LLM drift | canonical sequence should end with `python scripts/retag_llm.py` before `compute_maturity.py` |
| LLM queue | `134` keep current, `10` flip to `llm`, `12` flip to `non_llm`, `94` needs human escalation |
| alias review | `130` `seed_now`, `31` `hold`, `1` `reject` |
| product queue | `6` `map_now`, `137` `needs_alias`, `247` `leave_unmapped`, `454` `needs_human_call` |
| entry type | `215` `product_deployment`, `13` `custom_system`, `0` `bespoke_application`, `0` `needs_human_call` |
| scope / architecture | `163` `unknown`, `1` `rag_pipeline`, `1` `agentic_workflow`, `1` `fine_tuned` |

### Coordinator notes
- The unresolved product queue is `844` parsed rows, not the larger line-based counts from earlier notes. Multiline quoted CSV fields explain the difference.
- The alias input file had a malformed header. The human-review outputs normalize it into a reviewable shape and partition every alias exactly once.
- The LLM drift stream is the only blocking item for reproducibility. The other streams are review backlogs or approval queues.

## Examples
- Reproducibility blocker: `Makefile:fix` runs `python auto_tag.py` but not `python scripts/retag_llm.py`.
- Queue naming drift: the current repo uses semantic files like `review_queue_products_unresolved.csv`, not standalone `review_queue_d_unresolved.csv`.
- Product interpretation risk: rows like `CBP Traveler Verification Service (TVS)` and `CBP Translate` are better treated as agency-system wrappers than direct product canon.

## Recommended follow-up
- Treat `audit/human_review_llm_drift.md` as the gating artifact before any future `make fix` run is trusted.
- Use the alias partition CSVs as the approval surface for any later `build_lookups.py` seeding.
- Implement queue resolutions in this order:
  1. LLM drift
  2. LLM queue
  3. alias `seed_now`
  4. product queue `needs_alias` / `map_now`
  5. entry type
  6. scope
- Keep the large `needs_human_call` product bucket and `needs human escalation` LLM bucket out of any automatic bulk update.
