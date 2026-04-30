# LLM Drift Review

## Check
`make fix` is not reproducing the corrected LLM state. The full rebuild path still ends at `python auto_tag.py`, while the stable corrective pass is `scripts/retag_llm.py`.

## Method
Reviewed the pipeline entrypoint and the two tagging paths:
- [Makefile](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/Makefile:6)
- [auto_tag.py](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/auto_tag.py:289)
- [scripts/retag_llm.py](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/scripts/retag_llm.py:1)
- [tests/test_llm_tagging.py](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/tests/test_llm_tagging.py:1)
- [audit/remediation-report.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/remediation-report.md:1)
- [audit/dashboard-regressions.md](/Users/michaelboyce/Documents/Programming/ifp/ai-use-case-inventory/2025-aia-use-case-inventory/audit/dashboard-regressions.md:1)

## Findings
`Makefile:fix` runs a broad rebuild and ends with `python auto_tag.py` before `compute_maturity.py`. There is no `retag_llm.py` step in the canonical rebuild path, so the LLM correction is not protected as the last writer.

`auto_tag.py` is a full tagging pass, not a surgical LLM repair. The LLM decision lives inside `infer_llm_flag()`, but the script also recomputes product matching, template matching, entry type, architecture, scope, and related downstream tags in `tag_use_case()`. That makes the output dependent on the whole rebuild state, not just the LLM fix.

`scripts/retag_llm.py` is the narrow corrective path. It imports `infer_llm_flag()` from `auto_tag.py`, recomputes the flag for each row, and updates only `use_case_tags.is_general_llm_access`. It does not touch any other tag column. That is why it is the practical source of truth for the repaired LLM state.

The test file encodes the intended precedence, but it also confirms the operational split: the unit-tested rule is `infer_llm_flag()`, while the production correction is the retag script. The remediation report shows the corrected state (`88 -> 9` false positives), and the dashboard note documents that running the full `make fix` path can push false positives back to about `71`. That means the rebuild path is not idempotent with the repaired state.

## Examples
- `Makefile:6-11` runs `python auto_tag.py` as part of `fix`; it does not run `scripts/retag_llm.py`.
- `auto_tag.py:289-342` defines the LLM flag rules, but `auto_tag.py:585+` applies them as part of a wider full-row tagging pass.
- `scripts/retag_llm.py:1-5` states it only updates `is_general_llm_access`.
- `scripts/retag_llm.py:72-134` recomputes the flag across every row and writes only that one column.
- `tests/test_llm_tagging.py:52-134` expects classical/predictive/CV rows to stay `0` unless there is a named LLM override or a general-LLM product.

## Recommended follow-up
Make `scripts/retag_llm.py` the canonical post-pass for the LLM flag and stop treating `python auto_tag.py` as the final authority for that column. The safe command sequence is:

`python load_agencies.py`
`python load_inventories.py`
`python build_lookups.py`
`python auto_tag.py`
`python scripts/retag_llm.py`
`python compute_maturity.py`

If this is meant to remain a `make fix` workflow, the `fix` target should be updated later so the retag step happens after the full rebuild, not before or omitted entirely.
