# Visibility-gap drill — findings

Spot research on the LLM-vendor visibility gap (general-LLM-access entries
with no recoverable vendor or product). Slice B of the visibility-gap
charter — see `audit/visibility_gap/CHARTER.md`. Read 60+ sample rows
across HHS, VA, NASA, DOJ + stretch DHS, DOC.

## Three families of unspecified rows

- **A. Vendor-named-in-title** — `use_case_name` IS the product
  (e.g. `CoPilot`, `Adobe`, `Camtasia`, `LibreChat`, `VA GPT`,
  `NIGMS Azure Open AI`). Deterministically recoverable — handled by
  `scripts/recover_visibility_gap_titles.py` this pass.
- **B. Vendor-named-in-narrative** — narrative cites Claude Sonnet via
  Bedrock, GPT-4, Phi-3.5, etc., but the form fields stayed blank.
  Needs an LLM micro-agent extraction pass with a per-row review queue.
  Out of scope for this slice.
- **C. Truly placeholder** — bureau-level "we plan to use generative
  AI to summarize X" with no platform decision yet. Most CDC,
  NASA-research, and DHS umbrella entries are this family. Not safely
  attributable.

## Per-agency patterns

### VA (60 of 70 unspec, 86%)
VA's house chatbot is **VA GPT** (use_case 60999), described in VA's
M-25-21 plan as serving ~100k users. **Underlying model is not
publicly disclosed** — VA built the wrapper. Multiple rows are
downstream of VA GPT (60841 explicit, 60842 BillieGPT likely).

Other high-confidence wins this pass: Abridge / Knowtex ambient
clinical scribes, Andesite AI (CSOC, runs on AWS Bedrock + Claude
Sonnet per narrative), Microsoft Copilot family (60965, 61087),
Phi-3.5 (61050).

### HHS (84 of 167 unspec, 52%)
NIH and CDC each run their own platforms — NIGMS Azure OpenAI, NHGRI
LibreChat, NIH SharePoint OpenAI assistant. CDC also has 14+
pre-platform pilots that are Family C (no platform decided yet).

### NASA (40 of 50 unspec, 80%)
Mostly research code (Family C). Notable Family B: ALTIRA at LaRC
(use_case 59920) explicitly names **Anthropic Claude 3.5** in its
narrative.

### DOJ (40 of 87 unspec, 46%)
Cleanest target — many DOJ entries put product names in the
`use_case_name` field directly: Camtasia, Percipio, Thomson Reuters
Drafting, CoPilot, Adobe, UiPath. **Tagging issue surfaced**: 58641
R, 58642 Stata, 58643 Matlab are statistical packages misclassified
as `general_llm` and should be re-tagged out (not touched in this
slice — flagged as a follow-up).

### DHS
Three umbrella entries (57788/89/90) are platform-license requests
under DHS's commercial-GenAI authorization — not safely attributable
to one vendor.

### DOC
USAi.gov (GSA platform), NIST Azure/Vertex parentheticals, MS365
Copilot in OS — all High confidence.

## DB updates applied this pass

`scripts/recover_visibility_gap_titles.py` (idempotent; backup at
`data/federal_ai_inventory_2025.db.backup-pre-visibility-gap`):
**25 rows updated** across both `use_cases` (vendor_name + system_name)
and `use_case_tags` (cots_vendor + cots_product_name) so the
dashboard's existing fallback chain in `getLLMVendorShare` picks up
the new signal.

Confidence on the 25 updates:
- 22 High
- 3 Medium-High (60824 E2 HelpBot per narrative "GPT 4.0", 58766 Adobe)

Per-row rationales live in the script itself.

Net effect: **visibility gap dropped 431 → 376** general-LLM entries
without a recoverable vendor (-55, -13%).

## Follow-up DB updates (post-Slice B)

**DOJ retag (applied)**: use_cases 58641 (R), 58642 (Stata),
58643 (Matlab) were misclassified as `general_llm`. Statistical
packages, not generative AI. Updated:

```sql
UPDATE use_case_tags
   SET ai_sophistication = 'classical_ml',
       is_general_llm_access = 0
 WHERE use_case_id IN (58641, 58642, 58643);
```

Net: total general_llm entries 1201 → 1198.

## Still murky / follow-ups

- **VA GPT vendor**: VA does not publicly disclose what model VA GPT
  runs on. Public M-25-21 plan only says "internal generative AI
  chat tool." Worth a direct inquiry to VA AI program contacts.
- **Family B rows** (~30+ across all agencies): narratives mention
  vendors but extraction needs an LLM micro-agent pass. Worth a
  future slice — same pattern as the auto_tag.py heuristics, just
  with broader pattern matching and per-row review.
