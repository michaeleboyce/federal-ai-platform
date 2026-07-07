# Adoption baselines & policy-volume fills — researched 2026-07-06

Point-in-time research record (conventions: `README.md`). Resolves two of the
outside-sourcing items in `claims_review_2026-07-06.md` §4:

- §4.2 — the "compressed a normally decade-long process" comparison now has
  external baselines (below).
- §4.3 — the "over [fill in] pages of strategies and policies since 2023"
  placeholder now has a DB-backed number (below).

All external facts fetch-verified **2026-07-06** unless noted. The plotted
series + full provenance ship on the dashboard at **/adoption** (exportable at
`/api/adoption-series.csv`); the policy tracker exports at
`/api/policy-documents.csv`.

## 1. The policy-pages fill (§4.3) — VERIFIED against the DB 2026-07-06

Source: `agency_ai_policy_documents` (m012, tracker accessed **2026-05-21**).

| Cut | Docs | Agencies | Pages |
|---|---|---|---|
| Agency-issued (excl. White House/OMB), all ≥2023 by construction | 97 | 43 | **1,171** (+4 docs without page counts) |
| … in-force only (superseded excluded) | 79 | — | 978 |
| Everything incl. EOs + OMB memos | 103 | 45 | 1,286 |

**Publishable phrasing:** "over 1,100 pages" (bulletproof floor: "over 1,000"
if counting only in-force documents). Every agency-issued document in the
tracker is 2023+ — the earliest pre-2023 row is the 2020 AI EO (governing doc).
Year slope: 6 docs (2023) → 21 (2024) → 67 (2025) → 8 (2026 to date).
Live on the dashboard: /policy §I tiles ("all since 2023" + publishing-agencies
tile added 2026-07-06).

## 2. Adoption baselines (§4.2)

### Federal HTTPS — the strongest federal mandate→majority curve

- Mandate: OMB M-15-13, **2015-06-08**; deadline **2016-12-31**.
- IFP-computed from GSA's archived weekly scans
  (github.com/GSA/https, `compliance/m-15-13/data/parents-*.csv`, 82 weekly
  snapshots 2015-06-13 → 2016-12-31; denominator = live parent .gov domains,
  ~1,130–1,190/scan):
  - **Enforces HTTPS** (defaults-to or strictly-forces): **16.8% → 65.5%**
    in ~18.5 months (matches Digital.gov's published ~65%, Jan 2017).
  - **Supports HTTPS** (valid, no downgrade): **24.5% → 67.0%**.
  - Press "~80% support by Jan 2017" uses a looser measure — do not mix.
- Full monthly series checked into the dashboard repo:
  `dashboard/lib/data/adoption-series.ts` (ids `https-enforces`,
  `https-supports`).

### Workplace PC — the organic decade-plus baseline

% of employed US adults using a computer at work (Census CPS supplements /
BLS ciuaw.pdf): 1984 ~25% → 1989 ~37% → 1993 45.8% → 1997 49.4% →
2001 ~54% → 2003 56.1%. Crossed 50% around 2000–2003 — roughly two decades
from IBM PC (1981-08-12) to workplace majority. No mandate.

### Federal PIV / strong authentication — mandate drift, crisis snap

HSPD-12 mandate **2004-08-27**. PIV login use: FY2010 **1.24%** → FY2013
~20% required → 2015 Cyber Sprint (post-OPM breach): **42% → 72%** in one
quarter; **81%** by 2015-11-16 (FY2015 FISMA report). Caveat: metric
definitions vary across OMB reports (cards *issued* ≠ *used for login*).

### Federal cloud — the mandate that did NOT compress

Cloud First **2010-12-09**; FedRAMP policy memo **2011-12-08**. ~3% of
federal IT spend on cloud FY2015–17 (GAO-19-58). FedRAMP authorizations:
~20 (2016) → 100 (2018) → 200 (2020-09) → <350 (2024) → 502 (early 2026).

### Household context (OWID, CC BY)

Years to ~50% of US households: smartphone ~3, social media ~5–6,
internet ~7–8, PC ~9–11 from first survey (19 from IBM PC launch).
CSV: ourworldindata.org/grapher/technology-adoption-by-households-in-the-united-states

### External validation to cite

**Bick, Blandin & Deming, "The Rapid Adoption of Generative AI"** (NBER WP
32966; Management Science 2025): workplace GenAI adoption **28% within 2
years** of ChatGPT vs ~25% PC use three years after the 1981 IBM PC.
Differentiate: theirs is a household survey of the general economy; the
article's contribution is the federal enterprise — the historically slower
adopter.

### The GenAI side (DB, verified 2026-07-06)

Individual use cases 2,133 → 3,660; GenAI (IFP tag) 527 → 1,005; deployed
GenAI 200 → 311; enterprise-wide GenAI 21 → 24 agencies. ChatGPT
**2022-11-30** → AI Action Plan LLM-access mandate **2025-07-23** = **~2.6
years** (the /adoption chart's vermilion reference line).

## 3. The lessons layer (published /adoption §III, same-day addendum)

Six sourced "lessons" angles now documented on the dashboard at /adoption
§III, each with inline citations. Facts added beyond §2 above:

- **Pulse was a public scoreboard**: GSA/18F ran pulse.cio.gov as a public,
  weekly-updated HTTPS compliance dashboard (code: github.com/18F/pulse);
  BOD 18-01 (cyber.dhs.gov/bod/18-01, 2017) locked the gains in. The
  "scoreboard is the mechanism" argument: the one compressed mandate had
  public measurement; Cloud First and HSPD-12 did not.
- **Duo "State of the Auth" 2FA series** (self-reported US survey): 28%
  had ever used 2FA (2017) → 79% (2021). duo.com/blog 2019 + 2021 report
  posts, fetch-verified 2026-07-06. Contrast: 81% federal strong-auth by
  2015-11 → "government can outrun industry."
- **Integration-depth + bureau-divergence** (IFP-adjudicated, live at
  /figures/integration-depth and /figures/bureau-divergence): operating
  GenAI is shallow/standalone; all coding-agent filings pre-deployment;
  enterprise-LLM qualification diverges within departments (HHS all opdivs
  qualify, DOJ none, DOE bimodal).
- **Zero-reuse trio** (from fact_sheet.md §7, pinned): ChatGPT Enterprise
  auth 2026-01-09, Gemini for Government 2026-01-21, Perplexity Enterprise
  2026-02-01 — zero recorded reuses at the 2026-07-03 live check.
- **AAAIA §7225 sunset 2027-12-23** (Pub. L. 117-263, Div. G, Title LXXII,
  Subtitle B; enacted 2022-12-23, 5-year inventory requirement). The draft's
  "codified into law through 2028" is WRONG — do not reuse; say the mandate
  runs through December 23, 2027.

## 4. Framing constraints (editor-proofing, mirrored on /adoption)

1. Do NOT claim "fastest-adopted technology ever" (contested; sign-up stats).
   Claim: the federal enterprise — historically the slow adopter — moved at
   consumer-technology pace.
2. Never plot counts on a %-adoption axis; use-case counts measure
   institutional adoption, not employee share.
3. Label metric + population per series (HTTPS supports ≠ enforces; PIV
   issued ≠ used; households ≠ workforce ≠ federal enterprise).
4. The cloud baseline pre-empts "it's just the mandate": Cloud First was a
   mandate too and still took a decade.
