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

## Narrative-extraction pass

Family-B follow-up. Scanned all 446 remaining "Vendor unspecified"
general-LLM rows (post-Slice B + post-DOJ-retag) for explicit vendor
or product mentions in `problem_statement`, `expected_benefits`, and
`system_outputs`. Conservative extraction: only attribute when the
narrative names the underlying tool ("powered by Azure OpenAI",
"Using Vertex AI"), NOT when it merely analogizes
("ChatGPT-like interface", "such as GPT or BERT", "such as Meta
Llama").

Backup: `data/federal_ai_inventory_2025.db.backup-pre-narrative-extract`.
Script: `scripts/recover_visibility_gap_narrative.py` (idempotent;
re-running with --apply changes 0 rows).

### Recoveries (7 rows)

Agencies covered: DHS (2), DOT (2), HHS (1), NASA (1), TVA (1).

Confidence:
- 4 High: 57602 (Vertex AI/GCP), 57614 (Azure OpenAI Services /
  FEMA Grants ChatBot), 59690 (Azure OpenAI / HHS portfolio
  analysis), 60148 (LibreChat / NASA IV&V Assistant).
- 3 Medium-High: 58999, 59011 (DOT "Copilot" rows mirroring Slice
  B's MS Copilot family attributions), 60427 (TVA bare "Copilot").

Sample evidence quotes:
- 57602: *"Using Vertex AI and other GCP services, the system
  identifies and categorizes content..."* (RedactAI FOIA).
- 57614: *"The AI system, powered by Azure OpenAI Services,
  generates outputs..."* (FEMA Grants Manager ChatBot).
- 59690: *"automates the process of analyzing text...using a
  custom prompt and an Azure OpenAI models"* (HHS grant
  summarizing).
- 60148: *"NASA IV&V AI Assistant powered by LibreChat with
  Retrieval-Augmented Generation"*.

### Patterns observed

- **DHS = Vertex AI + Azure OpenAI shop.** FEMA cites Azure OpenAI
  Services explicitly; another DHS bureau (RedactAI) cites Vertex
  AI on GCP. The remaining 35 DHS unspec rows are Family C
  (umbrella platform-license requests under DHS commercial-GenAI
  authorization — already documented in this file).
- **DOT "Copilot" pattern.** Two FAA/DOT entries name a product
  literally called "Copilot" in the title and reuse Microsoft
  Copilot Studio terminology ("library of actions, pre-programmed
  capabilities") in the narrative. Treated like Slice B's CT/Meta
  Pilot Copilot attributions.
- **TVA = Microsoft Copilot.** Single bare "Copilot" entry with
  generic productivity benefits; matches TVA's public M365
  enterprise rollout. Medium-High by analogy.
- **Speculation rejected.** 59892 NASA REQAL ("such as GPT or
  BERT"), 60194 NSF topic-id ("such as Meta Llama"), 60202 NSF
  Open access LLM (multi-vendor BERT/Gemma/Llama/Mistral/Nemotron
  request) all skipped — narrative is exploratory, not committal.

Net effect: visibility gap dropped **446 → 439** general-LLM
entries without a recoverable vendor (-7, -1.6%). Smaller than the
Slice B title pass (-55) because most narratives in this remaining
pool are genuinely Family C — agencies haven't picked a vendor yet.

### Still murky / follow-ups

- **Treasury (63 unspec).** Largest non-VA bucket. Spot reads show
  Treasury entries are narrative-light (often a paragraph of
  business motivation with no platform name). 60561 EST GPT is the
  flagship example — the "GPT" is the project name, not an OpenAI
  attribution. Likely Family C across the board, but worth a
  dedicated targeted read if the Treasury bucket starts mattering
  for a story.
- **VA GPT vendor**: VA does not publicly disclose what model VA GPT
  runs on. Public M-25-21 plan only says "internal generative AI
  chat tool." Worth a direct inquiry to VA AI program contacts.
- **Multi-vendor LLM-access requests** (60202 NSF, 57788/89/90
  DHS): the narrative names a basket of allowed vendors rather
  than one. Schema can't represent "any of {A,B,C}". Document in
  findings only.
