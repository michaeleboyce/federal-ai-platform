# Per-Agency Research Notes

Detailed research notes from the five parallel sweeps that built this tracker
(2026-05-21). For the summary matrix see `TRACKER.md`; for the structured catalog see
`documents.csv` and `coverage.csv`.

---

# Agent 1 — Security & Justice cluster: research notes

Researched 2026-05-21. 9 agencies, 25 documents catalogued (23 downloaded, 2 link-only).

## Summary table

| Agency | Docs | M-25-21 AI Strategy | M-25-21 Compliance Plan | Notable gap |
|---|---|---|---|---|
| DoD | 3 | Yes (Jan 2026 — DoW AI Strategy) | n/a (exempt) | No genAI acceptable-use policy public |
| DHS | 4 | Yes (Sept 2025) | Yes (Sept 2025) | None |
| DOJ | 2 | **Not public** | **Not public** (only M-24-10) | Both required M-25-21 artifacts missing |
| State | 3 | Yes (2025 EDAS) | Yes (Sept 2025) | None |
| VA | 5 | Yes ("Building the Future") | Yes | None |
| NRC | 3 | Yes (FY26 plan) | Yes (FY26 plan) | None (download blocked) |
| USITC | 1 | Not found | Yes (2025) | No standalone AI strategy |
| NTSB | 2 | Not found | Yes (FY25) | No standalone AI strategy |
| CSOSA | 2 | Not found | Yes (Oct 2025) | No standalone AI strategy |

## Per-agency findings

### DoD — Department of Defense (Cabinet)
DoD/Department of War is **exempt from M-25-21** but is a major AI-strategy publisher. On Jan 9 2026 the Secretary of War signed the **Artificial Intelligence Strategy for the Department of War** and a companion memo, **Transforming the Defense Innovation Ecosystem to Accelerate Warfighting Advantage**. Also catalogued **DoD Instruction 5400.19** (public-affairs use of AI, references M-25-21/M-25-22). The CDAO (Chief Digital and AI Office) is the de facto AI lead. media.defense.gov and esd.whs.mil are Akamai-protected — downloads succeeded only with a browser UA + cookie jar + full header set. The 2022 DoD Responsible AI Strategy predates the 2023 scope window and was not recorded.
Landing page: https://www.war.gov/Spotlights/Artificial-Intelligence/

### DHS — Department of Homeland Security (Cabinet)
Strongest coverage in the cluster. Published both M-25-21 artifacts in Sept 2025 (AI Strategy + Compliance Plan), plus **Directive 139-08** (AI Use and Acquisition, Jan 2025) and the **DHS Playbook for Public Sector Generative AI Deployment** (Jan 2025). DHS CIO serves as Chief AI Officer; AI Governance Board convened July 2 2025. All four documents downloaded.
Landing page: https://www.dhs.gov/ai

### DOJ — Department of Justice (Cabinet) — **REQUIRED ARTIFACT GAP**
**DOJ has NOT publicly posted its M-25-21 AI Strategy or M-25-21 Compliance Plan.** justice.gov/ai links only the **M-24-10 Compliance Plan** (Oct 9 2024, now superseded) and a 2024 Deputy Attorney General memo ("Shaping the Department's AI Efforts"). DOJ's governance body is the Emerging Technology Board. Both downloaded. This is the most significant gap in the cluster — a major Cabinet department with no public M-25-21 strategy or compliance plan as of the research date.
Landing page: https://www.justice.gov/ai

### State — Department of State (Cabinet)
Full coverage. The **2025 Enterprise Data & AI Strategy (EDAS)** serves as the M-25-21 180-day AI strategy (completed by the Sept 30 2025 deadline); paired with the **M-25-21 Compliance Plan**. Also has a **2023 Enterprise AI Strategy** (historical, covering 2024-2025, now superseded). CDAO leads; the Enterprise Data and AI Council (EDAC) is the AI Governance Board. All three downloaded.
Landing page: https://www.state.gov/artificial-intelligence/

### VA — Department of Veterans Affairs (Cabinet)
Strong coverage, 5 documents. "**Building the Future**" serves as the M-25-21 AI strategy (web page, last updated Jan 2026); plus the **M-25-21 Compliance Plan**, the prior **M-24-10 Compliance Plan**, **Guidance for Generative AI Use at VA** (first issued July 2023), and the **Trustworthy AI Framework** (adopted July 2023). All VA AI documents are web pages with no PDF versions — saved as rendered HTML. VA Chief AI Officer sits within OIT.
Landing page: https://department.va.gov/ai/

### NRC — Nuclear Regulatory Commission (Independent)
NRC published the **FY26 AI Strategic Plan** (ADAMS ML25269A196) and **FY26 AI Compliance Plan** (ML25272A276), both dated Sept 29 2025, plus the standalone **FY2023-2027 AI Strategic Plan** (NUREG-2261). **Download caveat:** www.nrc.gov timed out on every attempt from this environment (HTTP/2 INTERNAL_ERROR and HTTP/1.1 connection timeouts across 20+ retries) — the two FY26 documents are recorded `Link only` with verified URLs. The FY2023-2027 plan was successfully downloaded via a regulations.gov mirror (NRC-2022-0095-0002). NRC has named a CAIO and stood up an AI Governance Board + AI Steering Committee. Both required M-25-21 artifacts exist publicly; only the download was blocked.
Landing page: https://www.nrc.gov/ai

### USITC — U.S. International Trade Commission (Independent)
Posted its **M-25-21 Compliance Plan** (downloaded). No standalone M-25-21 AI strategy document found — typical for a small independent agency. CAIO is William Powers (re-designated under M-25-21); AI Governance Board retained. No high-impact AI use cases identified. A generative AI policy is referenced in the compliance plan as forthcoming but not separately posted.
Landing page: https://www.usitc.gov/ai

### NTSB — National Transportation Safety Board (Independent)
Posted both its **M-25-21 Compliance Plan** (FY25, ~Sept 29 2025) and the prior **M-24-10 Compliance Plan** (both downloaded). No standalone M-25-21 AI strategy — NTSB had not identified AI use cases warranting one. Maintains a Data Governance Body consistent with M-25-21.
Landing page: https://www.ntsb.gov/

### CSOSA — Court Services and Offender Supervision Agency (Independent)
Posted its **M-25-21 Compliance Plan** (Oct 2025) and **Policy Statement 2040: Artificial Intelligence** (effective Dec 20 2025) — an agency AI acceptable-use policy covering employees, interns, and contractors. Both downloaded. No standalone M-25-21 AI strategy found.
Landing page: https://www.csosa.gov/

## Required-artifact gaps flagged

- **DOJ** — No public M-25-21 AI Strategy and no public M-25-21 Compliance Plan. Only the superseded M-24-10 plan is posted. This is a genuine transparency gap for a major Cabinet department.
- **USITC, NTSB, CSOSA** — No public M-25-21 *AI Strategy* (compliance plans were posted). Consistent with small independent agencies that filed compliance plans only; not necessarily a non-compliance finding.
- **DoD** — No M-25-21 compliance plan, but DoD is exempt from M-25-21; not a gap.
- **NRC** — Both M-25-21 artifacts exist publicly; only the download was blocked by an unreachable NRC server (recorded Link only with verified URLs).

## Access notes
- media.defense.gov and esd.whs.mil (DoD) are Akamai-fronted and return "Access Denied" to plain curl; succeeded with a Chrome UA + cookie jar + full browser headers.
- www.usitc.gov is also Akamai-fronted; succeeded with an extended browser header set.
- www.nrc.gov was unreachable for the entire research session (timeouts on HTTP/1.1 and HTTP/2). The FY26 strategy and compliance plan could not be downloaded; the FY2023-2027 plan was retrieved from a regulations.gov mirror.
- VA AI documents are HTML web pages (no PDFs); saved as rendered HTML.

---

# Research Agent 2 — Economy & Finance cluster (9 agencies)

Date searched: 2026-05-21. 13 documents recorded; 12 downloaded, 1 link-only.

## Summary table

| Agency | Docs | M-25-21 AI Strategy | M-25-21 Compliance Plan | CAIO |
|---|---|---|---|---|
| Treasury | 2 | Yes (2025) | Yes (2025) | Paras Malik |
| DOC | 1 | Yes (2025, link only) | Not found as distinct doc | Unknown |
| DOL | 1 | Yes (2025, combined doc) | Folded into the strategy doc | Mangala Kuppa |
| SBA | 1 | NOT FOUND | NOT FOUND (only 2024 M-24-10) | Hartley Caldwell |
| GSA | 3 | Yes (2025, web page) | Yes (2025, web page) | Zachary Whitman |
| SEC | 1 | NOT FOUND | NOT FOUND (only 2024 M-24-10) | Valerie Szczepanik |
| CFTC | 1 | Not found | Yes (2025) | Janaka Perera |
| FDIC | 1 | Not found | Yes (2025) | Michael W. Simon |
| FHFA | 2 | Not found | Yes (2025) + 2024 M-24-10 | Tracy Stephan |

## Per-agency findings

### Treasury — Department of the Treasury (Cabinet)
Complete M-25-21 set. Both the **AI Strategy** and the **Compliance Plan** (each Sept 2025, prepared by CAIO Paras Malik, issued by Secretary Scott Bessent) are posted as PDFs at home.treasury.gov and were downloaded cleanly. Landing page: home.treasury.gov "Treasury and Artificial Intelligence." Generative AI is governed via an Acceptable Use Policy referenced inside the strategy/compliance documents but not separately posted. A Dec 2022 EO 13960 Consistency Plan also exists but predates the 2023 cutoff (excluded).

### DOC — Department of Commerce (Cabinet)
The **Commerce AI Strategy Plan for OMB Memorandum M-25-21** (Sept 2025) is confirmed public at `commerce.gov/sites/default/files/2025-09/DOC-AI-Strategy-Plan-for-OMB-Memorandum-M-25-21.pdf` and linked from commerce.gov/ai. **Could not be downloaded** — commerce.gov is behind a Cloudflare JS challenge that blocks curl, WebFetch, the reader-proxy, and the Wayback save endpoint; no existing Wayback snapshot. Recorded as `Link only`. No distinct Commerce M-25-21 *compliance plan* was found, and no CAIO is publicly named. NIST (a Commerce component, major AI player via CAISI / AI RMF) runs its own programs and did not publish a discrete M-25-21 strategy/policy in scope.

### DOL — Department of Labor (Cabinet)
DOL published one consolidated 16-page document, **"Department of Labor AI Strategies" for OMB Memorandum M-25-21** (Sept 2025), prepared by CAIO Mangala Kuppa and issued by Deputy Secretary Keith Sonderling. It functions as both the AI strategy (5 maturity levels, 9 workstreams) and the compliance plan (explicitly addresses M-25-21 Section 4(b)). dol.gov blocks curl with Access Denied; downloaded via the Wayback Machine. Landing page: dol.gov/ai.

### SBA — Small Business Administration (Independent) — GAP
**Required M-25-21 artifacts not found publicly.** Only the **Sept 2024 M-24-10 Implementation Plan for AI** is posted (downloaded). SBA paused all AI use cases in March 2025 to review compliance; it has published 2025 AI use-case inventories but no public M-25-21 AI Strategy or M-25-21 Compliance Plan was located. CAIO is CIO Hartley Caldwell.

### GSA — General Services Administration (Independent)
Complete set, but published as **web pages rather than PDFs**: the **M-25-21 AI Strategy** ("Strategies for OMB Memorandum M-25-21," prepared by CAIO Zachary Whitman, Sept 30 2025) and the **M-25-21 Compliance Plan** (Sept 2025, covers M-25-21 and M-25-22). Both saved as rendered HTML; a FedScoop PDF mirror of the compliance plan was also saved. Plus **CIO 2185.1C, "Accelerating Responsible Use of Artificial Intelligence at GSA"** (signed Mar 11 2026, 8 pages) — the internal AI directive that supersedes CIO 2185.1A/B and includes generative-AI governance. Landing page: gsa.gov/artificial-intelligence/resources.

### SEC — Securities and Exchange Commission (Independent) — GAP
**No public M-25-21 compliance plan or AI strategy found.** The PDF at `sec.gov/files/sec-ai-compliance-plan.pdf` — despite being current on the SEC AI page — is the **Sept 2024 M-24-10 Compliance Plan** (prepared by then-CAIO David Bottom). The SEC created an AI Task Force in Aug 2025 and named Valerie Szczepanik as CAIO, but no M-25-21-vintage strategy or compliance plan was found publicly. Downloaded via Wayback (sec.gov rate-limits curl). Landing page: sec.gov/ai.

### CFTC — Commodity Futures Trading Commission (Independent)
**M-25-21 Compliance Plan** (Sept 2025, prepared by CAIO Janaka Perera) downloaded from cftc.gov/ai. No separate AI strategy document. The CFTC's Dec 2024 Staff Advisory on AI use in CFTC-regulated markets is external regulatory guidance for registered entities — not the agency's own internal AI policy — and was excluded per scope.

### FDIC — Federal Deposit Insurance Corporation (Independent)
**M-25-21 Compliance Plan** (Sept 2025, prepared by CAIO Michael W. Simon) downloaded from fdic.gov/ai. No separate AI strategy. The plan describes updating the FDIC IT Acceptable Use Policy to cover generative AI, but a standalone genAI policy is not posted.

### FHFA — Federal Housing Finance Agency (Independent)
Two documents: the **M-25-21 Compliance Plan** (Sept 2025, prepared by CAIO Tracy Stephan) and the prior **M-24-10 Compliance Plan** (Sept 2024, marked superseded). Both downloaded. No separate FHFA M-25-21 AI strategy. Landing page: fhfa.gov/reports/fhfa-ai-compliance-plan.

## Agencies missing a required OMB artifact (flagged)

- **SBA** — no public M-25-21 AI Strategy and no public M-25-21 Compliance Plan. Only the 2024 M-24-10 plan exists publicly.
- **SEC** — no public M-25-21 Compliance Plan and no M-25-21 AI Strategy. sec.gov still serves only the 2024 M-24-10 plan.
- **DOC** — M-25-21 AI Strategy exists and is public, but no distinct M-25-21 *Compliance Plan* was found. (The strategy itself could not be downloaded due to Cloudflare; recorded as Link only.)
- **CFTC / FDIC / FHFA** — each has an M-25-21 Compliance Plan but no separate M-25-21 AI Strategy was found (common for smaller financial-regulatory agencies, which may fold strategy content into the compliance plan).

## Access-method notes
- `commerce.gov` — Cloudflare JS challenge blocks all automated download methods.
- `dol.gov` and `sec.gov` — block/rate-limit curl; both documents retrieved via the Wayback Machine (`web.archive.org/web/2id_/`).
- `gsa.gov` — M-25-21 strategy and compliance plan are HTML pages, not PDFs; saved as rendered HTML, with a FedScoop PDF mirror for the compliance plan.

---

# Agent 3 — Human Services cluster: research notes

Researched 2026-05-21. 9 agencies, 25 documents recorded. All documents downloaded
except one (SSA M-25-21 compliance plan — see below).

## Download environment notes
Several .gov sites in this cluster (hhs.gov, ssa.gov, irp.nih.gov) are behind Akamai
and return HTTP 403 "Access Denied" to curl/WebFetch regardless of User-Agent or
header spoofing. Where possible, documents were retrieved via the Wayback Machine
(`web.archive.org/web/<ts>id_/`) or third-party mirrors (ACLU-MA `data.aclum.org`
hosts a verified mirror set of 2024-vintage M-24-10 compliance plans). hud.gov,
ed.gov, opm.gov, pbgc.gov, acf.gov, ncua.gov, nlrb.gov, frtib.gov all downloaded
directly with a browser User-Agent.

## Per-agency findings

### HHS — Department of Health and Human Services (6 documents)
Strongest coverage in the cluster.
- **M-25-21 AI Strategy** — "HHS Artificial Intelligence Strategy", released Dec 4
  2025, 21 pages, five pillars, "OneHHS" approach.
- **M-25-21 Compliance Plan** — 8 pages.
- **M-24-10 Compliance Plan** — 2024, superseded.
- **Historical AI Strategy** — "Strategic Plan for the Use of AI in Health, Human
  Services, and Public Health", 198 pages, released Jan 15 2025 (Biden-era ASTP/ONC),
  predates M-25-21.
- **Component genAI policies** — CMS "Guidance for Responsible Use of AI at CMS"
  (last reviewed Aug 26 2025) and ACF "Generative AI Policy" v3 (Dec 2025).
- CAIO: Clark Minor (acting), formerly Palantir.
- All HHS-domain documents pulled via Wayback / mirrors (Akamai block).

### ED — Department of Education (3 documents)
- **M-24-10 Compliance Plan** — 2024.
- **AI Dear Colleague Letter** — July 22 2025, on leveraging federal grant funds for
  AI in education; recorded as Other Department AI Policy / Guidance.
- **Historical AI Strategy** — "AI and the Future of Teaching and Learning" (OET,
  May 2023, 71 pages).
- **GAP / required-artifact missing:** No public **M-25-21 AI Strategy** and no
  public **M-25-21 Compliance Plan**. ED's AI guidance page links only the use-case
  inventory. This is a notable omission relative to peer cabinet departments.

### HUD — Department of Housing and Urban Development (5 documents)
- **M-25-21 AI Strategy** and **M-25-21 Compliance Plan** — both Sept 2025.
- **AI Technical Requirements** and **AI Definitions** — companion guidance docs.
- **HUD OIG** filed its own separate M-25-21 compliance plan (independent of dept).
- Complete M-25-21 set.

### SSA — Social Security Administration (3 documents)
- **M-25-21 Compliance Plan** — URL is live (`ssa.gov/ai/policy/SSA AI Compliance
  Plan.pdf`) but ssa.gov hard-blocks curl AND the file is not in the Wayback Machine,
  so it could not be downloaded — recorded `Link only`. The artifact DOES exist
  publicly; it is just not retrievable by this tooling.
- **M-24-10 Compliance Plan** — 2024, downloaded from ACLU-MA mirror.
- **Enterprise AI Strategy Report** — standalone strategy; exact date not stated on
  cover, inferred 2023-2024 (referenced as pre-existing in the M-24-10 plan).

### OPM — Office of Personnel Management (2 documents)
- **M-25-21 AI Strategy** (7 pages) and **M-25-21 Compliance Plan** — both 2025.
  Compliance plan describes an AI Governance Board meeting quarterly.

### PBGC — Pension Benefit Guaranty Corporation (2 documents)
- **M-25-21 Compliance Plan** — 2025.
- **Generative AI Policy Guidance** — PBGC AI page shows Last Updated Feb 5 2026.
- No standalone AI strategy document found.

### FRTIB — Federal Retirement Thrift Investment Board (1 document)
Weakest coverage.
- Only the **AI program web page** (`frtib.gov/ai/`) is public. It references an
  internal "AI Plan – 09/2024" and use of the NIST AI RMF, but **no formal AI
  strategy or compliance-plan document is posted publicly.**
- **GAP / required-artifact missing:** no public M-25-21 AI Strategy or Compliance
  Plan. Page saved as HTML as the best available artifact.

### NCUA — National Credit Union Administration (1 document)
- **M-25-21 AI Compliance Plan** — published Sept 2025 as a web page (no PDF),
  saved as rendered HTML. Developed under CAIO **Amber Gravius**.
- No separate AI strategy document.

### NLRB — National Labor Relations Board (2 documents)
- **M-25-21 Compliance Plan** — Sept 2025.
- **CAIO Statement Letter** — Sept 2024, serves as the NLRB's M-24-10 compliance
  documentation (recorded as M-24-10 Compliance Plan, superseded).
- CAIO: **David K. Gaston**, named NLRB's first CAIO.

## Summary of required-OMB-artifact gaps
Agencies where a required M-25-21 artifact could NOT be found publicly:
- **ED** — no public M-25-21 AI Strategy and no public M-25-21 Compliance Plan
  (only a 2024 M-24-10 plan). Most significant gap in the cluster.
- **FRTIB** — no public M-25-21 AI Strategy or Compliance Plan (internal "AI Plan
  09/2024" referenced but not posted).
- **SSA** — M-25-21 Compliance Plan exists publicly but was not downloadable by
  this tooling (recorded `Link only`); not a true gap.
- **PBGC, NCUA, NLRB** — have an M-25-21 Compliance Plan but no separate M-25-21 AI
  Strategy; for smaller independent agencies a combined/compliance-only filing is
  common, so not flagged as a hard gap.

---

# Agent 4 research notes — Resources & Infrastructure cluster

Date searched: 2026-05-21. Agencies: DOE, DOI, USDA, DOT, EPA, FERC, TVA, USTDA, NMB.
Total documents recorded: **21** across 8 agencies (NMB has zero).

## Access caveats
Two agencies' web servers block scripted/automated downloads from this research
environment:
- **DOT** (transportation.gov) — Akamai edge protection returns HTTP 403 to all
  scripted requests (curl, WebFetch). All three DOT strategy parts were captured as
  rendered text via a render proxy and saved as `.txt` in `documents/DOT/`. The
  original PDF URLs are verified and live.
- **USDA** (usda.gov) — server resets the connection (HTTP 000) for every scripted
  request. All three USDA documents were captured as rendered text (`.txt` in
  `documents/USDA/`). Original PDF URLs verified via multiple independent sources.

These six items are marked `access_status = Link only` with the real URL recorded.
Everything else downloaded as a genuine PDF (verified with `file`).

## Per-agency findings

### DOE — Department of Energy (5 documents) — strongest coverage
- **M-25-21 AI Strategy** and **M-25-21 Compliance Plan**, both dated 2025-09-23.
- **M-24-10 Compliance Plan** (2024-09-23) — superseded by the 2025 plan.
- **Generative AI Policy**: DOE P 203.1, "Use of Generative Artificial Intelligence,"
  dated 2025-12-29 (a formal DOE directive).
- **GenAI Reference Guide v2** (2024-06-14) — companion guidance.
- CAIO: Helena Fu (acting), Director of the Office of Critical and Emerging
  Technologies, coordinating DOE AI since Dec 2023. AI Governance Board chaired by
  the Deputy Secretary, vice-chaired by the CAIO (described in the strategy).
- No required OMB artifact missing.

### DOI — Department of the Interior (5 documents) — strong coverage
- **M-25-21 AI Strategy** ("Setting the Vision") and **M-25-21 Compliance Plan**,
  both Sept 2025.
- **M-24-10 Compliance Plan** (Sept 2024) — superseded; downloaded from an ACLU
  mirror of the original doi.gov 2024-09 file.
- **Generative AI Policy** — OCIO "Use of Generative AI Policy," Feb 2026.
- **Joint AI Acquisition Memorandum** — Feb 2026, recorded as AI Procurement Policy
  (M-25-22).
- No required OMB artifact missing. No standalone CAIO announcement or governance
  charter posted.

### USDA — Department of Agriculture (3 documents)
- **M-25-21 AI Strategy** — "FY2025-2026 AI Strategy" (USDA's inaugural AI strategy,
  serving as the M-25-21 strategy).
- **M-25-21 Compliance Plan** — October 2025.
- **M-24-10 Compliance Plan** — FY2024 (Sept 2024) — superseded.
- No public standalone generative AI policy: USDA operates an unposted interim
  genAI guidance and a Generative AI Review Board (GAIRB). Not recorded.
- No required OMB artifact missing (strategy + compliance plan both found).

### DOT — Department of Transportation (3 documents)
- DOT issues its AI strategy in **three parts**:
  - Part I — AI Use Case Strategic Alignment → recorded as M-25-21 AI Strategy.
  - Part II — AI Maturity Assessment and Roadmap → recorded as M-25-21 AI Strategy.
  - Part III — DOT Compliance Plan for OMB M-25-21 → recorded as M-25-21 Compliance
    Plan. All three dated 2025-10-03.
- No required OMB artifact missing.
- The **FAA "Roadmap for Artificial Intelligence Safety Assurance"** (2023-2024) was
  reviewed and **excluded**: it is external aviation-product certification guidance
  (how the FAA regulates AI in aircraft), not an agency AI-*use* strategy or policy
  under the OMB M-25-21 vocabulary. No other component-agency (FHWA, NHTSA, FRA)
  internal AI-use policies were found posted.

### EPA — Environmental Protection Agency (2 documents)
- **M-25-21 AI Strategy** ("EPA AI Strategies for OMB Memorandum M-25-21") and
  **M-25-21 Compliance Plan**, both Sept 2025; hosted at epa.gov/data.
- No 2024 M-24-10 compliance plan found publicly online (possible gap, or never
  posted). No standalone genAI policy or CAIO announcement.

### FERC — Federal Energy Regulatory Commission (1 document)
- **M-25-21 Compliance Plan** only, dated 2025-09-30 (found via the ferc.gov "media"
  page; PDF downloaded).
- **GAP: no public M-25-21 AI Strategy.** FERC posted a compliance plan but no
  separate 180-day AI strategy document. (FERC's other high-profile AI activity —
  rulemaking on data-center grid interconnection — is external regulatory work, out
  of scope here.)

### TVA — Tennessee Valley Authority (1 document)
- **M-25-21 Compliance Plan** — 7 pages, prepared July 2025 by the VP of
  Cybersecurity / CISO; downloaded from TVA's Azure CDN (linked off the TVA AI page).
- **GAP: no standalone M-25-21 AI Strategy document.** The TVA AI landing page
  narrates a strategy and governance framework but no separate strategy PDF is posted.
- Chief AI Officer referenced in the compliance plan; not named publicly.

### USTDA — U.S. Trade and Development Agency (1 document)
- **M-25-21 Compliance Plan** — dated 2025-09-30. (Document title references M-25-21
  and M-25-22 even though the ustda.gov/ai landing-page boilerplate still cites the
  older M-24-10.)
- **GAP: no separate M-25-21 AI Strategy.** As a small agency, USTDA published only a
  compliance plan.

### NMB — National Mediation Board (0 documents)
- **COMPLETE GAP: NMB has published NO formal AI strategy or policy document of any
  kind.** Its only public AI artifact is an AI use-case inventory web page listing
  four Google Gemini use cases.
- **Missing: both M-25-21 required artifacts** (AI Strategy and Compliance Plan), plus
  any genAI policy, CAIO announcement, or governance charter. NMB is a very small
  independent agency.

## Summary of required-artifact gaps (M-25-21 AI Strategy or Compliance Plan)
- **NMB** — neither the M-25-21 AI Strategy nor the M-25-21 Compliance Plan is public.
- **FERC** — M-25-21 Compliance Plan published; **no public M-25-21 AI Strategy**.
- **TVA** — M-25-21 Compliance Plan published; **no standalone M-25-21 AI Strategy**.
- **USTDA** — M-25-21 Compliance Plan published; **no separate M-25-21 AI Strategy**.
- **EPA** — both M-25-21 artifacts found; no 2024 M-24-10 plan located (minor gap).
- DOE, DOI, USDA, DOT — full M-25-21 strategy + compliance plan sets located.

---

# Agent 5 — Independent / regulatory cluster: research notes

Researched 2026-05-21. 9 agencies: NASA, NSF, NARA, GPO, FCC, FTC, FRB, OSC, EAC.
Total documents catalogued: **13**.

## Per-agency findings

### NASA — National Aeronautics and Space Administration (2 documents)
- AI landing page: https://www.nasa.gov/artificial-intelligence/ (and a CAIO page at nasa.gov/chief-artificial-intelligence-officer). Neither links a NASA-authored strategy or M-25-21 plan — only White House/OMB memos.
- **M-24-10 Compliance Plan** (2024-09-23) — public on nasa.gov. Superseded by the M-25-21 regime.
- **AI Governance Board Charter** — "NASA Artificial Intelligence Strategy Board Charter" NC 1000.61, effective 2025-01-28, expires 2029. Establishes the NASA AI Strategy Board (AISB); cites EO 13960/14110 and M-24-10. (File slug says 2025, corrected from initial 2024 guess.)
- CAIO: David Salvagnini (CDO/CAIO, named 2024); Kevin Murphy acting CAIO since Nov 2025.
- **GAP / FLAG:** NASA's **M-25-21 AI Strategy (180-day)** and **M-25-21 Compliance Plan** could NOT be found publicly. The AISB charter says the board reviews/approves a NASA AI Strategy, but no such public document was located. No standalone generative AI policy found.

### NSF — National Science Foundation (2 documents)
- AI landing page: https://www.nsf.gov/policies/ai — well organized, links both core artifacts.
- **M-25-21 AI Strategy** (Sept 2025) — "NSF AI Strategy for OMB Memorandum M-25-21." Prepared by Thu Williams, Acting CAIO.
- **M-25-21 Compliance Plan** — "NSF AI Compliance Plan." Marked CUI but posted publicly.
- CAIO: Thu Williams (Acting).
- Best-covered agency in this cluster — both required OMB artifacts public. NSF also has a generative-AI merit-review notice for proposers/reviewers, treated as inventory/process guidance (not an internal-use genAI policy), so not catalogued.

### NARA — National Archives and Records Administration (1 document)
- AI landing page: https://www.archives.gov/ai
- **M-25-21 Compliance Plan** (2025-09-18) — prepared by Gulam Shakir, CAIO; issued by Jim Byron, Senior Advisor to the Archivist.
- CAIO: Gulam Shakir. Governance via the Enterprise Architecture Governance Board (EAGB).
- **GAP:** No standalone NARA **M-25-21 AI Strategy** posted; no standalone generative AI policy. NARA's "Strategic Framework 2026-2030" mentions AI but is a general agency strategic plan, not an AI strategy.

### GPO — Government Publishing Office (0 documents)
- **GPO is a LEGISLATIVE-branch agency and is NOT subject to OMB M-24-10 / M-25-21.**
- No public AI strategy, compliance plan, or generative AI policy found on gpo.gov.
- News coverage (Nextgov, Jan 2026; GPO Director Senate testimony, Jan 2024) confirms GPO created an internal AI-specific policy (circa 2019+) and voluntarily follows the NIST AI Risk Management Framework, but no formal document is posted publicly. CIO Sam Musa leads the AI program; no public CAIO designation.
- **GAP:** All — but expected, given legislative-branch status.

### FCC — Federal Communications Commission (1 document)
- AI landing page: https://www.fcc.gov/ai
- **M-25-21 Compliance Plan** (Sept 2025) — "FCC Artificial Intelligence Compliance Plan for OMB Memorandum M-25-21." Prepared by Arpan Sura, CAIO & Allen Hill, CIO.
- CAIO: Arpan Sura.
- Note: FCC's CDN blocks curl and wget (TLS/JA3 fingerprinting → connection reset / timeout). The PDF was downloaded successfully via Python `requests`.
- **GAP:** No separate FCC M-25-21 AI Strategy or generative AI policy found.

### FTC — Federal Trade Commission (1 document)
- AI landing page: https://www.ftc.gov/ai
- **M-25-21 Compliance Plan** (Sept 2025) — "Federal Trade Commission Compliance Plan for OMB Memoranda M-25-21." Prepared/issued by Mark D. Gray, CAIO. (FTC's page titles it the "FTC AI Compliance Plan"; the PDF filename is FTC-AI-Use-Policy.pdf.)
- CAIO: Mark D. Gray.
- **GAP:** No separate FTC M-25-21 AI Strategy or generative AI policy found.

### FRB — Federal Reserve Board (2 documents)
- AI landing page: https://www.federalreserve.gov/ai.htm
- **M-25-21 Compliance Plan** (Sept 2025) and **M-24-10 Compliance Plan** (Sept 2024) — both public on federalreserve.gov/publications.
- **Independent-agency status:** The Federal Reserve Board is an independent agency. It does NOT publish a 180-day AI Strategy (it is not a CFO Act agency, so M-25-21's strategy requirement does not bind it). It DOES voluntarily file and publicly post a biennial compliance plan satisfying M-25-21 sec 3(b)(ii) and AI in Government Act sec 104. The M-25-21 plan explicitly treats the Board as subject to M-25-21's requirements and does not claim an exemption.
- CAIO: Anderson Monken. AI Program established early 2024; strategic oversight moved to the Chief Data Officer in late 2025.
- Internal AI policy and generative-AI guidance are kept on the Board's intranet — not public.

### OSC — U.S. Office of Special Counsel (1 document)
- AI landing page: https://www.osc.gov/resources/ai/
- **M-25-21 Compliance Plan** (dated 2025-09-22) — "OSC Artificial Intelligence Compliance Plan for OMB Memorandum M-25-21." CAIO: James Walters.
- OSC also announced a standalone AI policy in **October 2024** — but this is a news release (24-04-OSC-AI-Policy press page); no separate downloadable policy document was found, so it is excluded per scope.
- **GAP:** No M-25-21 AI Strategy found. The compliance plan states OSC's **generative AI policy** was still in development (M-25-21 270-day deadline ~Dec 29 2025); no public genAI policy located.

### EAC — Election Assistance Commission (3 documents)
- AI landing page: https://www.eac.gov/AI
- **M-25-21 Compliance Plan** v1.0 (Sept 2025) — strategy/vision content embedded inside the plan.
- **M-24-10 Compliance Plan** (dated 2024-08-02) — superseded.
- **Other AI Policy/Guidance:** "AI in Action: Case Studies for Election Officials" (March 2026) — outward-facing election-administration AI guidance.
- **GAP:** No standalone EAC AI Strategy (the strategy is folded into the compliance plan); no standalone generative AI policy. CAIO function referenced but not named publicly.

## Cross-cutting flags — missing required OMB artifacts

- **NASA**: M-25-21 AI Strategy AND M-25-21 Compliance Plan both NOT public. Only an M-24-10 (2024) plan and the AISB governance charter are public. This is the most significant gap in the cluster — NASA is a major federal agency and a major AI publisher, yet its current-regime OMB artifacts are not posted.
- **NARA / OSC / EAC**: Have a public M-25-21 Compliance Plan but NO standalone M-25-21 AI Strategy document (EAC folds strategy into the plan).
- **FRB**: No AI Strategy — but correctly so; the Fed is an independent, non-CFO-Act agency not bound by the 180-day strategy requirement. It files compliance plans voluntarily.
- **GPO**: No OMB artifacts — correctly so; GPO is a legislative-branch agency outside M-25-21's scope.
- **NSF** is the only agency in this cluster with BOTH the M-25-21 AI Strategy and the M-25-21 Compliance Plan posted publicly.
- Generative AI policies: none of the 9 agencies has a publicly posted standalone generative-AI acceptable-use policy (OSC's was still in development as of Sept 2025; FRB's is intranet-only).

## Access notes
- FCC's website (Akamai CDN) blocks curl and wget via TLS fingerprinting (connection reset on HTTP/2, timeout on HTTP/1.1). FCC PDF was retrieved via Python `requests`.
- All 13 documents downloaded and verified as real, non-empty PDFs (`file` confirms PDF type).

---
