# Agent A notes — slice_a_named_vendor_individual

Input: 272 individual use cases with a named vendor that the linker couldn't
match to any catalog product.

## Decision counts

| Decision | Count |
|---|---:|
| `add_product` | 174 |
| `link` | 69 |
| `unclear` | 21 |
| `false_positive` | 8 |
| **Total** | **272** |

By confidence: high 96, medium 119, low 57. 28 of the 174 `add_product`
proposals nominate a `proposed_parent_canonical_name` (Adobe Premiere → Adobe
Creative Cloud Suite; SSDM/Module-3/Annual-Report-CMC → FDA CDEROne
Analytics; Sentinel sub-modules → FTC Sentinel Network Services; etc.). 109
distinct vendors are proposed.

## Themes / patterns

1. **Linker-recall losses (69 `link` decisions).** A lot of straightforward
   misses — vendor names that just needed aliases:
   - `Invariant Corporation` → existing `Invariant Acoustic Signature AI`
   - `Airship` → existing `Airship AI Platform` (Airship Outpost is the same
     vendor)
   - `Tesseract` (vendor) → existing `Tesseract OCR`
   - `iCatalyst Inc` → existing `iCatalyst RPA` (5 ED use cases, all same
     vendor, all unlinked — the linker is too literal about the trailing
     "RPA")
   - `Skyward Solutions` / `Skyward IT Solutions` → existing
     `Skyward CEDAR/CLAW` (CMS Chat, AI Workspace, CLAW are three sibling
     CEDAR modules)
   - `Aretec Inc` → existing `Aretec NEAT` (3 SEC use cases, all NEAT
     modules)
   - `SkillSoft` / `Skillsoft/Percipio` → existing `Skillsoft Percipio CAISY`
     (the canonical's vendor co-occurrence aliasing is too tight)
   - `Dataminer` (typo) → `Dataminr First Alert`
   - `RELX (Lexis)` → `Lexis+ AI`
   - `CLEAR` / `Thomson Reuters CLEAR` — vendor literally `CLEAR` (4 FDIC
     filings) need an alias
   - `UIPath Studio` / `UI Path` / `UIPath` — case/spacing variants

   The linker is consistently brittle on (a) ALLCAPS variants, (b) "Inc"
   suffixes, (c) vendor-name-only mentions where the filing's
   `system_name` matches the canonical and the vendor is the company.

2. **Federal in-house builds with integrator vendors (most of `add_product`).**
   For the high-value DHS, FDA, USCIS, NIH, HRSA, State filings the vendor
   field is the contracting partner (Deloitte, Booz Allen, Guidehouse, GDIT,
   SAIC, Steampunk, MetroIBR, ManTech, Peraton, Mindpetal, etc.), not a
   product vendor. I proposed canonical names that name the federal owner
   plus the system (e.g., "USCIS Verification Match Model", "ATS Trade Entity
   Risk Model", "HRSA Knowledge Navigator", "State Department AI Research
   Engine (AIRE)"). These should probably get a uniform parent like
   "Custom In-House AI" — flagged as future hierarchy work for Agent D.

3. **DOE shape-of-data problem.** ~20 DOE rows have vendor `"Not available"`,
   `"Microsoft"` (because Azure is the host), `"AWS"`, or even `"NLP"` /
   `"Python"`. I marked obvious non-vendor strings as `false_positive` or
   `unclear`, and kept named DOE-lab tools as `add_product` (Merlin, COREII,
   MAPPRITE, LANL AI Portal, SRNS in-house tools). Microsoft Visual C++
   runtime / MSPaint rows (3 of them) are textbook `false_positive`:
   `"AI was automatically integrated into the product without an identified
   benefit"` — these should probably be filtered out before the linker even
   sees them.

4. **FDA CDEROne is a hierarchy waiting to happen.** 8 Deloitte-built FDA
   modules (Module-3 facilities, DMF facilities, Real World Data, packaging,
   annual report CMC, application-DMF reference, regulatory starting
   materials, supply chain role classification) all share `CDEROne
   Analytics: FISMA-high environment` as system. I proposed a parent
   `FDA CDEROne Analytics`; Agent D should add that as a real catalog row.

5. **FTC Sentinel similarly.** Leidos-built modules (PSC classification,
   chatbot, graph analytics, sandbox, dev productivity) all on Sentinel
   Network Services. Same hierarchy pattern — parent
   `FTC Sentinel Network Services`.

6. **GrantSolutions** is a real federal shared service with 6 sibling
   modules (Text Analyzer, AI Writing Assistant, Recipient Risk, NCC
   Approval, NCC Review, Helpdesk Agent). Proposed canonical name
   `GrantSolutions` as parent — currently absent from catalog.

7. **Zvolvant** is a small business with 5 FERC contracts — proposed
   sibling products for each FERC use case rather than one umbrella product,
   because each use case is functionally distinct.

## Things I flagged `unclear` (21)

- 4 DHS "Law Enforcement Sensitive (LES)" rows where both vendor and system
  are redacted. Nothing to canonicalize.
- ~15 DOE rows with vendor = "Not available", "Third Party Vendor",
  garbled date strings, or contract-PIID-only.
- 1 FDIC OIG forensics row with 5 vendors and no clear primary product.

## Things I flagged `false_positive` (8)

- 3 DOE Microsoft Visual C++/MSPaint rows ("AI was automatically integrated
  into the product without an identified benefit") — Microsoft auto-flagged
  these but they're not AI deployments.
- 2 vendor-string-is-not-a-vendor: `Python`, `NLP`.
- 1 vendor-string-is-a-standards-body: `Open Geospatial Consortium`.
- 1 vendor-string-is-a-URL: `https://startup.utah.gov/business-plan/`.
- 1 SBA Utah business plan (state-government link, not an AI product).

## Catalog gaps worth highlighting

- **AWS Comprehend** — referenced explicitly by DOL PII Redaction (62475)
  for the AWS PII scrubber. No catalog row.
- **Azure Speech** is in the catalog but **Azure AI Translator** is not
  (proposed; State Dept TIP report translation).
- **Microsoft SQL Server Intelligent Query Processing** is proposed for
  FHFA (62699) — distinct from Azure Platform proper.
- **Equifax background screening** is proposed; not present.
- **TransUnion TLOxp** is proposed (DOJ EOIR background checks); not
  present.
- **Axon** (the body-cam + AI redaction product) is missing entirely;
  proposed.
- **JAWS Screen Reader** (Freedom Scientific) is missing; proposed.
- **Ultralytics YOLO** (object detection library used by DOI for boat
  traffic) is missing; proposed.
- **Adobe Premiere Pro** is missing as a child of Adobe Creative Cloud
  Suite — proposed.
- **NanCI** exists in catalog (id missing in this run; flagged for V) and
  has a clean filing at HHS 63151.

## Verification

All 272 `evidence_quote` strings are verbatim substrings of the source
text (use_case_name | vendor_name | system_name | development_type |
problem_statement | expected_benefits). Quotes were generated, then a
post-pass replaced any paraphrased quotes with the longest in-source
sentence that fit the ≤120-char budget. 0 remaining misses.
