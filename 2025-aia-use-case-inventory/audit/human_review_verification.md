# Verification

## Check
The human-review outputs are internally consistent. All review queues reconcile to the parsed CSV row counts, the alias partition files cover the full alias set exactly once, and the LLM-drift recommendation is unambiguous.

## Method
I compared the six review artifacts against the source queue CSVs and the alias partition CSVs:
- [human_review_llm_drift.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/human_review_llm_drift.md)
- [human_review_llm_queue.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/human_review_llm_queue.md)
- [human_review_aliases.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/human_review_aliases.md)
- [human_review_products.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/human_review_products.md)
- [human_review_entry_type.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/human_review_entry_type.md)
- [human_review_scope.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/human_review_scope.md)

I checked the parsed CSV row counts directly rather than relying on the older queue-label shorthand in the prose notes.

## Findings

### Row accounting
| Artifact | Parsed input rows | Output totals | Reconciles |
| --- | ---: | ---: | --- |
| `review_queue_llm_unresolved.csv` | 250 | 134 keep current + 10 flip to llm + 12 flip to non_llm + 94 human escalation = 250 | Yes |
| `proposed_aliases.csv` | 162 | 130 seed_now + 31 hold + 1 reject = 162 | Yes |
| `review_queue_products_unresolved.csv` | 844 | 6 map_now + 137 needs_alias + 247 leave_unmapped + 454 needs_human_call = 844 | Yes |
| `review_queue_entry_type_unresolved.csv` | 228 | 215 product_deployment + 13 custom_system = 228 | Yes |
| `review_queue_scope_unresolved.csv` | 166 | 163 unknown + 1 rag_pipeline + 1 agentic_workflow + 1 fine_tuned = 166 | Yes |

- The alias partitions sum to `162` exactly once, with no duplicate row appearing across `seed_now`, `hold`, and `reject`.
- The queue review counts reconcile to the parsed CSV row counts for every queue above.
- The earlier “604 D-queue” note is stale; the actual parsed product queue is `844` rows, and the review artifact reflects that file.
- No direct contradiction showed up between alias and product review results. The overlap is expected: approved aliases are the missing lookup coverage that the product queue asks for, while the product queue still keeps agency-system wrappers and ambiguous bundles unmapped.
- The LLM-drift recommendation is unambiguous: `scripts/retag_llm.py` is the corrective source of truth for `is_general_llm_access`, and `make fix` should not be treated as authoritative unless it ends with that retag pass.

## Examples
- `proposed_aliases_seed_now.csv` includes clear commercial aliases such as `Clearview AI`, `Dataminr`, and `ServiceNow IT Operations Management (ITOM) Predictive AIOps`, which matches the product queue's `needs_alias` demand.
- `proposed_aliases_hold.csv` keeps agency-specific systems such as `CBP Traveler Verification Service (TVS)` out of canon, which matches the product queue's `leave_unmapped` treatment for wrapper-style rows.
- `human_review_llm_queue.md` and `human_review_llm_drift.md` agree on the same correction strategy: keep explicit classical/CV/NLP rows non-LLM unless a named frontier model overrides them, and preserve `retag_llm.py` as the final LLM repair step.

## Recommended follow-up
- Use the approved alias seed file as the input to the lookup builder after a spot-check.
- Treat the product queue's `needs_human_call` bucket as the remaining manual review backlog, not as a failure of the alias partitioning.
- Keep `scripts/retag_llm.py` as the last LLM-touching pass in any rebuild workflow.
