# Agent C — Dark-sample triage (slice_c_dark_sample.csv, n=200)

## Decision counts

| Decision | Count | % |
|---|---:|---:|
| unclear | 182 | 91.0% |
| add_product | 12 | 6.0% |
| link | 3 | 1.5% |
| false_positive | 2 | 1.0% |
| add_alias | 1 | 0.5% |
| **Actionable (link + add_product + add_alias)** | **16** | **8.0%** |

## Calibration verdict for the 2,347-row dark population

If this sample is representative, the broader dark population contains roughly
**8% addressable rows** (~190 use cases) where a product can be linked
or a new catalog entry justified from in-source evidence alone. The other
~92% are split between:

- **Title-only filings** (~40%) — agencies that filed a use case name with
  no narrative at all. Nothing to do with these without external research.
- **Genuinely in-house / capability-only** (~50%) — NASA/NOAA/USGS research
  models, CMS analytical workflows, in-house chatbots. These are correctly
  unlinked.

The dark sample is **dominated by NASA (~40 rows)** — almost entirely
in-house research code (CNN/RL/foundation models trained on agency-specific
data). NASA is a calibration outlier; the rest of the dark corpus is likely
slightly more catalog-rich than the headline 8% suggests.

**Recommendation:** a second pass across the 2,347 dark rows is worth
running, but expectations should be modest. Prioritize rows where:

- `development_type = "Purchased from a vendor"` AND `vendor_name` is blank
  but the `use_case_name` itself names a product (e.g., NeuroQuant, Romexis,
  Aquilion, MAGNETOM, Verathon BladderScan — all VA medical-device rows).
- `use_case_name` matches a brand pattern (e.g., "FaceVACS", "RedSeal",
  "Natural Reader") even when the rest of the row is empty.

## Productive findings — catalog gaps to add (12 add_product)

These are real commercial products named verbatim in the dark slice but
absent from the catalog:

| Use case | Proposed canonical | Vendor | Why it's defensible |
|---|---|---|---|
| 61536 DOC | Ex Libris Alma/Primo | Ex Libris (Clarivate) | Title is literally the product name |
| 62935 HHS | Lectora AI | ELB Learning | Well-known eLearning authoring vendor |
| 63697 NASA | LibreChat | LibreChat (OSS) | "powered by LibreChat" with RAG; explicit deployment |
| 63893 State | Cognitec FaceVACS | Cognitec | State CA passport photo QC, named verbatim |
| 63970 TVA | NaturalReader | NaturalReader | Title + "Text-to-speech desktop software" |
| 64364 VA | Planmeca Romexis | Planmeca | Dental imaging vendor; segmentation + implant planning |
| 64383 VA | RedSeal | RedSeal | Cyber-risk analytics; title + attack-path output |
| 64504 VA | Cortechs NeuroQuant | Cortechs.ai | FDA-cleared MRI brain quantification |
| 64505 VA | Siemens MAGNETOM | Siemens Healthineers | Multi-model MAGNETOM family (Vida/Lumina/Aera/Skyra/...) |
| 64506 VA | Hologic 3D Quorum | Hologic | Genius AI mammography reconstruction |
| 64565 VA | Verathon BladderScan Prime PLUS | Verathon | Title + bladder volume measurement |
| 64622 VA | Canon Aquilion ONE AiCE | Canon Medical Systems | CT scanner with AiCE DL reconstruction |

**Pattern:** VA's medical-device dark rows are the single richest seam in
this sample (7 of 12 add_product candidates). These are FDA-cleared imaging
products that VA reliably title-stamps but doesn't populate vendor_name on.

## Linker recall misses (3 link)

These products **are already in the catalog** but the linker missed them
because the name appears only in `problem_statement` / `expected_benefits`:

- **61151 DHS RedactAI → Google Vertex AI (5287)** — "Using Vertex AI and other GCP services"
- **61799 DOE UNSPSC Codes → Microsoft Azure Platform (5131)** — system_name is "Azure GOV"
- **64368 VA SAC → Microsoft AI Builder (5326)** — "Implementing AI Builder will tangibly improve"

This confirms the charter's hypothesis: the linker's vendor/system-only scan
misses real products that show up only in narrative fields. A re-run of the
linker against `problem_statement + expected_benefits + system_outputs` would
catch these without manual review.

## Alias fix (1)

- **63184 HHS cryoDGRN → cryoDRGN (5185)** — agency filed a typo ("DGRN" vs
  "DRGN"). Add `cryoDGRN` as an alias so future typos catch.

## False positives (2)

- **62278 DOJ BOP PATTERN** — system_name literally "Redacted for cybersecurity purposes". Dark by design.
- **64449 VA Sharing RVU Provider Metrics** — Pyramid Analytics is named only as the BI source the AI reads from, not the AI tool itself.

## Surprising findings / data-quality observations

1. **Many NASA rows are filed with placeholder body text** (e.g., 63500
   "Link prediction" for a row titled "Code Assistant Pilot Study"; 63663
   "PIX4DCloud" titled but body is a NASA foundation-model project).
   These are agency filing-quality issues, not catalog issues.

2. **VA's Billie GPT vs BillieGPT POC (64640, 64391)** appear to be the same
   tool filed twice. Cross-reference candidate but no underlying-model
   evidence in either row.

3. **"Digizens" (64405 VA)** sounds product-shaped but I could not
   externally verify a matching commercial vendor in the time budget.
   Left as `unclear` with note for human review.

4. **No mentions of ChatGPT, Claude, Bedrock, GitHub Copilot, M365 Copilot,
   Tabnine, Cursor, Gemini, Llama, Mistral, Databricks, Palantir, etc.**
   in any of the 200 dark rows. That's striking — the dark population is
   genuinely dominated by in-house / OSS / niche-COTS deployments, not by
   the headline frontier-LLM products. This further validates the
   "named-vendor" slices (A/B) as the productive ones for catalog coverage.

## Candidates flagged for human review (not auto-actioned)

These I left as `unclear` but flagged in `notes` for follow-up:

- **64296 VA Clinical AI Agent** — ambient clinical scribe; VA is a known
  Abridge customer. Strong inference but no in-text name.
- **64109 Treasury AI Voiceover for eLearning** — almost certainly WellSaid
  Labs / ElevenLabs / Murf. Vendor field empty.
- **62934 HHS NCHHSTP social listening** — outputs read like Sprinklr.
- **63230 HHS AI-generated podcast** — strongly suggests Google NotebookLM
  (which is in catalog as 4994).
- **62290 DOJ Perimeter Detection Fence (FLIR)** — title names FLIR;
  FLIR 280 HD already in catalog (5273) but no narrative to confirm match.
- **63905 State FOIA 360 AI Matching Tool** — likely AINS FOIAXpress 360
  variant.
- **64617 VA Intelligent 2D** — likely Hologic Genius AI Intelligent 2D.
