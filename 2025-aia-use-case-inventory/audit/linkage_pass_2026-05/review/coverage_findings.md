# Coverage findings

Reviewer C (coverage). Counterpart to validity review. RNG seed `20260517`.
Narratives verified against `data/federal_ai_inventory_2025.db.backup-pre-m006`
(the snapshot the inputs were generated against; the current `.db` has been
rebuilt and no longer carries the input use_case_ids).

## Per-agent quality

| Agent | input rows | decisions | covered | spot-check defensibility | verdict |
|---|---:|---:|---|---:|---|
| A | 272 | 272 | 272/272 (100%, no dupes, no extras) | 20/20 OK | green |
| B | 130 (77 individual + 53 consolidated) | 152 | 77/77 individual + 53/53 consolidated; expansion factor ~1.17x from multi-product `commercial_product` fields | 19 OK + 1 WEAK = 20/20 defensible | green |
| C | 200 | 200 | 200/200, 1:1 | 20/20 OK | green |
| D | 316 catalog rows | 7 proposals | n/a; mainly compounded by 31 add'l hierarchy edges harvested from A/B `proposed_parent_canonical_name` (integrated total 38) | parents found are correct; many obvious parents MISSED (see below) | yellow |

All four agents covered their assigned slices completely. No missed rows, no
extras, no duplicated `use_case_id`s. The 152 vs. 130 gap for Agent B is the
expected multi-product expansion (e.g., consolidated row "Azure, AWS, Mural"
→ three decisions). Cross-checks of agent counts in `integration/summary.md`
match the raw JSON.

## Dark-sample calibration

- Actionable rate (link + add_product + add_alias): **16/200 = 8.0%**
- Extrapolated to broader 2,347-row dark population: **~190 actionable rows**
  (very imprecise — dark population is heterogeneous and the random sample is
  small).
- Concentration: of the 16 actionable hits, **8 are VA** (50%), almost all
  medical-imaging / device vendors: Verathon BladderScan, Siemens MAGNETOM,
  Hologic 3D Quorum, Canon Aquilion AiCE, Planmeca Romexis, Cortechs
  NeuroQuant, RedSeal, Microsoft AI Builder. Strong signal for a **targeted
  VA medical-imaging second pass** before broadly re-sampling the dark
  population.
- Secondary clusters: HHS (2 — Lectora, cryoDRGN), one each from
  DHS/DOC/DOE/NASA/State/TVA.
- 182 unclear / 2 false_positive among the 200: the dark population is
  *genuinely* dark — most filings without a recognizable named vendor are
  in-house scientific ML, redacted, or one-line stubs. Sampling more rows is
  unlikely to change this composition outside the VA bucket.

## Spot-check WEAK / WRONG cases

| Agent | row | issue |
|---|---|---|
| B | cuc=8998 (DHS) `link → Microsoft 365 Copilot` | WEAK. Evidence is "Azure Synapse Analytics, Copilot" — bare "Copilot" is ambiguous (could be GitHub Copilot or Copilot for M365). Decision is defensible but the alias resolution is thin. |

No WRONG decisions found in the 60-row spot-check.

## Unclear / false_positive sample review

- **15-row unclear sample**: all 15 are defensibly unclear. Most have empty
  `problem_statement`, "Not available" narratives (DOE pattern), or
  in-house scientific ML with no product name. Two borderline candidates
  could arguably have been called differently: FRB cuc=9333
  "External- Creative Production Suite" probably *is* Adobe Creative Cloud,
  and HHS uc=62901 NCIRD SmartFind ChatBots (system_name="Microsoft", dev
  type=contractor) is likely Azure OpenAI / M365 Copilot — but vendor field
  is "N/A" so flagging for human review is reasonable. **No signal that
  agents were systematically over-cautious.** Note: a handful of Agent C
  "unclear" rows on in-house scientific ML (NASA radiative transfer, NASA
  keyword prediction, DOE bio/health) could arguably be `false_positive`
  (in-house custom model, not a deployed product), but `unclear` is also
  defensible since the narrative is too thin to be sure.
- **10-row false_positive sample**: all 10 correct. Agent B is doing
  high-value work here — catching greedy alias matches the linker would
  otherwise propose (Meta vs. "Metathesaurus"/"Metadata", Descript vs.
  "Description", Aware Biometrics vs. "Awareness", Site vs. "Offsite").
  Agent A correctly rejected SBA's Utah-state-website "vendor" and
  Microsoft MSPaint as a non-AI product. These rejections protect the
  downstream catalog from contamination.

## Productive findings

Highest-value catalog additions surfaced:
- **VA medical-imaging vendor cluster** (Siemens MAGNETOM, Canon Aquilion
  AiCE, Hologic 3D Quorum, Planmeca Romexis, Verathon BladderScan, Cortechs
  NeuroQuant) — entire vendor category currently absent from catalog.
- **Federal-system named products** (Agent A's FTC Sentinel family, FDA
  CDEROne family, HHS GrantSolutions family, Grants.gov AI Tools family) —
  these are real DHS/FDA/HHS systems with documented sub-products that the
  catalog has been missing wholesale.
- **DHS-line products**: TVS, RAVEn, ATAP, ELIS, Person-Centric Identity
  Services, Verification Match Model — high-impact gap for the largest
  filer in the inventory.

Hierarchy edges Agent D missed but A/B's `proposed_parent_canonical_name`
correctly recovered (and the integration script honored — confirmed in
`proposed_hierarchy_edges.csv`):
- Adobe Premiere Pro → Adobe Creative Cloud Suite (A)
- Adobe Sensei → Adobe Creative Cloud Suite (B)
- Azure Synapse Analytics → Microsoft Azure Platform (B)
- Azure AI Translator → Microsoft Azure Platform (A)
- Google Calendar → Google Workspace (B)
- 7 FTC Sentinel sub-products → FTC Sentinel Network Services (A)
- 7 GrantSolutions sub-products → GrantSolutions (A)
- 8 FDA CDEROne sub-products → FDA CDEROne Analytics (A)

Hierarchy edges Agent D still missed (catalog snapshot shows parent-less
branded products that obviously belong somewhere):
- `Google Translate`, `Google Maps`, `Google Lens`, `Google Workspace`,
  `NotebookLM`, `Gemini` → arguably `Google Cloud Platform` or a new
  "Google" parent.
- `AWS Bedrock`, `AWS Kendra`, `AWS Lex`, `AWS Rekognition`, `AWS Textract`,
  `AWS Transcribe`, `AWS Translate`, `Amazon Connect` → no Amazon /
  AWS parent in the catalog at all.
- `Microsoft 365`, `GitHub Copilot`, `Microsoft Power Platform`,
  `Microsoft Dynamics 365`, `Microsoft Sentinel` (some now parented),
  `Nuance Dragon` → all parent-less.

These are not blockers for `--apply`, but a follow-up Agent-D-2 pass
focused on AWS / Google / Microsoft 365 hierarchy would noticeably
improve dashboard rollups.

## Verdict

**GREEN LIGHT to proceed to `--apply`.**

Justification:
- All four agents hit 100% coverage of their slices.
- 60-row defensibility spot-check: 59/60 OK + 1/60 WEAK + 0/60 WRONG =
  98% — well above the CHARTER's ≥90% bar per agent.
- False-positive decisions are correct and actively protect catalog
  quality.
- "Unclear" rate is consistent with genuinely-ambiguous source data, not
  agent timidity. The dark population *is* mostly dark.
- 0 conflicts in `integration/conflicts.csv`.
- Integration script correctly harvested hierarchy edges from A/B's
  add_product proposals (38 total vs. Agent D's 7 standalone).

Recommended follow-ups (post-apply, non-blocking):
1. **Targeted VA medical-imaging dark-sample pass** — yield rate there
   appears far above 8%.
2. **Agent-D-2 hierarchy pass** focused on AWS, Google Workspace/Cloud,
   and Microsoft 365 product families.
3. **Tighten `Copilot` / `Meta` / `Site` / `Aware` / `Descript` aliases**
   in the linker — Agent B's false_positives showed these alias matchers
   are too greedy on their own.
