# Federal Agency AI Strategy & Policy Tracker

Coverage matrix for the AI **strategies and policies** of all **45 agencies** in scope —
the 44 agencies that filed a 2025 AI use case inventory plus DoD. Every agency was
searched on **2026-05-21**. Cells show the **publication year(s)** of each document found.

See `README.md` for the OMB M-24-10 / M-25-21 requirement reference and the
`document_type` vocabulary. The full per-document catalog (titles, URLs, local file
paths, supersession status) is in **`documents.csv`**; per-agency search detail and
gaps are in **`coverage.csv`**; per-agency research notes are in **`research_notes.md`**;
the downloaded originals are under **`documents/`**.

## Coverage at a glance

| Metric | Count |
|---|---|
| Agencies searched | 45 / 45 |
| Documents catalogued | 97 |
| — downloaded as original files | 87 |
| — recorded link-only (site blocked scripted download) | 10 |
| Agencies with a public **M-25-21 AI Strategy** | 18 / 45 |
| Agencies with a public **M-25-21 Compliance Plan** | 34 / 45 |
| Agencies with a public **M-24-10 Compliance Plan** (2024) | 16 / 45 |
| Agencies with a standalone **generative-AI policy** | 6 / 45 |
| Agencies with a **pre-memo / standalone AI strategy** | 5 (ED, HHS, NRC, SSA, State) |
| Agencies with **no public AI strategy or policy at all** | 2 / 45 (GPO, NMB) |

## How to read the matrix

- A **year** = a document of that type was found, tagged with its publication year.
- **—** = no such document found publicly (a gap, or not applicable).
- **(also YYYY)** in the strategy column = a pre-memo or standalone AI strategy from
  that year, *separate from* the M-25-21 strategy (which is counted only when a year
  appears before the parenthesis).
- **Other AI policies** = count of directives, governance charters, procurement
  policies, frameworks, and component-agency AI policies (see `documents.csv`).
- 10 documents are link-only — the document is public but the agency site blocked
  scripted download; the verified URL is in `documents.csv`.

## Cabinet departments (15)

| Agency | M-25-21 AI Strategy | M-25-21 Compliance Plan | M-24-10 Compliance Plan | Gen-AI Policy | Other AI policies | Chief AI Officer | Docs |
|---|---|---|---|---|---|---|---|
| **DHS** — Department of Homeland Security | 2025 | 2025 | — | — | 1 | designated | 4 |
| **DOC** — Department of Commerce | 2025 | — | — | — | — | — | 1 |
| **DoD** — Department of Defense | 2026 | — | — | — | 2 | designated | 3 |
| **DOE** — Department of Energy | 2025 | 2025 | 2024 | 2025 | 1 | Helena Fu | 5 |
| **DOI** — Department of the Interior | 2025 | 2025 | 2024 | 2026 | 1 | designated | 5 |
| **DOJ** — Department of Justice | — | — | 2024 | — | 1 | designated | 2 |
| **DOL** — Department of Labor | 2025 | — | — | — | — | Mangala Kuppa | 1 |
| **DOT** — Department of Transportation | 2025 | 2025 | — | — | — | designated | 3 |
| **ED** — Department of Education | (also 2023) | — | 2024 | — | 1 | designated | 3 |
| **HHS** — Department of Health and Human Services | 2025 (also 2025) | 2025 | 2024 | 2025 | — | Clark Minor | 6 |
| **HUD** — Department of Housing and Urban Development | 2025 | 2025 | — | — | 1 | — | 5 |
| **State** — Department of State | 2025 (also 2023) | 2025 | — | — | — | designated | 3 |
| **Treasury** — Department of the Treasury | 2025 | 2025 | — | — | — | Paras Malik | 2 |
| **USDA** — Department of Agriculture | 2025 | 2025 | 2024 | — | — | designated | 3 |
| **VA** — Department of Veterans Affairs | 2026 | 2025 | 2024 | 2023 | 1 | designated | 5 |

## Independent & other agencies (30)

| Agency | M-25-21 AI Strategy | M-25-21 Compliance Plan | M-24-10 Compliance Plan | Gen-AI Policy | Other AI policies | Chief AI Officer | Docs |
|---|---|---|---|---|---|---|---|
| **CFTC** — Commodity Futures Trading Commission | — | 2025 | — | — | — | Janaka Perera | 1 |
| **CSOSA** — Court Services and Offender Supervision Agency | — | 2025 | — | 2025 | — | designated | 2 |
| **EAC** — Election Assistance Commission | — | 2025 | 2024 | — | 1 | designated | 3 |
| **EPA** — Environmental Protection Agency | 2025 | 2025 | — | — | — | designated | 2 |
| **FCC** — Federal Communications Commission | — | 2025 | — | — | — | Arpan Sura | 1 |
| **FDIC** — Federal Deposit Insurance Corporation | — | 2025 | — | — | — | Michael W. Simon | 1 |
| **FERC** — Federal Energy Regulatory Commission | — | 2025 | — | — | — | designated | 1 |
| **FHFA** — Federal Housing Finance Agency | — | 2025 | 2024 | — | — | Tracy Stephan | 2 |
| **FRB** — Federal Reserve Board | — | 2025 | 2024 | — | — | Anderson Monken | 2 |
| **FRTIB** — Federal Retirement Thrift Investment Board | — | — | — | — | 1 | — | 1 |
| **FTC** — Federal Trade Commission | — | 2025 | — | — | — | Mark D. Gray | 1 |
| **GPO** — Government Publishing Office | — | — | — | — | — | — | 0 |
| **GSA** — General Services Administration | 2025 | 2025 | — | — | 1 | Zachary Whitman | 3 |
| **NARA** — National Archives and Records Administration | — | 2025 | — | — | — | Gulam Shakir | 1 |
| **NASA** — National Aeronautics and Space Administration | — | — | 2024 | — | 1 | David Salvagnini | 2 |
| **NCUA** — National Credit Union Administration | — | 2025 | — | — | — | Amber Gravius | 1 |
| **NLRB** — National Labor Relations Board | — | 2025 | 2024 | — | — | David K. Gaston | 2 |
| **NMB** — National Mediation Board | — | — | — | — | — | — | 0 |
| **NRC** — Nuclear Regulatory Commission | 2025 (also 2023) | 2025 | — | — | — | designated | 3 |
| **NSF** — National Science Foundation | 2025 | 2025 | — | — | — | Thu Williams | 2 |
| **NTSB** — National Transportation Safety Board | — | 2025 | 2024 | — | — | designated | 2 |
| **OPM** — Office of Personnel Management | 2025 | 2025 | — | — | — | designated | 2 |
| **OSC** — U.S. Office of Special Counsel | — | 2025 | — | — | — | James Walters | 1 |
| **PBGC** — Pension Benefit Guaranty Corporation | — | 2025 | — | 2026 | — | — | 2 |
| **SBA** — Small Business Administration | — | — | 2024 | — | — | Hartley Caldwell | 1 |
| **SEC** — Securities and Exchange Commission | — | — | 2024 | — | — | Valerie Szczepanik | 1 |
| **SSA** — Social Security Administration | (also 2024) | 2025 | 2024 | — | — | designated | 3 |
| **TVA** — Tennessee Valley Authority | — | 2025 | — | — | — | designated | 1 |
| **USITC** — U.S. International Trade Commission | — | 2025 | — | — | — | William Powers | 1 |
| **USTDA** — U.S. Trade and Development Agency | — | 2025 | — | — | — | designated | 1 |

## Required-document gaps

Under OMB **M-25-21**, CFO Act agencies must publicly post an **AI Strategy** and a
**Compliance Plan** (both due ~Sept 30, 2025).

**No public M-25-21 AI Strategy found (27 of 45):**
DOJ, ED, CFTC, CSOSA, EAC, FCC, FDIC, FERC, FHFA, FRB, FRTIB, FTC, GPO, NARA, NASA, NCUA, NLRB, NMB, NTSB, OSC, PBGC, SBA, SEC, SSA, TVA, USITC, USTDA

Most are small independent agencies that posted a compliance plan with strategy content
folded in. The serious cases are major agencies that published *neither* required
M-25-21 artifact: **DOJ** and **ED** (Cabinet departments), and **NASA**, **SBA**,
**SEC** — each still showing only a 2024 M-24-10 plan. **ED** and **SSA** have a
standalone AI strategy but not the M-25-21 one. **NMB** and **GPO** have published no
formal AI document at all (GPO is a legislative-branch agency outside M-25-21 scope).

**No public M-25-21 Compliance Plan found (11 of 45):**
DOC, DoD, DOJ, DOL, ED, FRTIB, GPO, NASA, NMB, SBA, SEC

(DoD is statutorily exempt from M-25-21; the Federal Reserve is not a CFO Act agency
and files a compliance plan voluntarily without the 180-day strategy obligation.)

## Governing documents (White House & OMB)

The foundation the agency documents above are written in response to. These are *not*
agency policy and are excluded from the agency page counts; they are catalogued in
`documents.csv` with `agency_type = White House / OMB` and stored under
`documents/_governing/`.

| Document | Year | Pages | Status | Implements |
|---|---|---|---|---|
| EO 13960 — Promoting the Use of Trustworthy AI in the Federal Government | 2020 | 5 | In effect | — |
| EO 14110 — Safe, Secure, and Trustworthy Development and Use of AI | 2023 | 36 | Rescinded (EO 14148, 2025) | — |
| EO 14179 — Removing Barriers to American Leadership in AI | 2025 | 2 | In effect | — |
| OMB M-24-10 — Advancing Governance, Innovation, and Risk Management for Agency Use of AI | 2024 | 34 | Superseded (by M-25-21) | EO 14110 |
| OMB M-25-21 — Accelerating Federal Use of AI through Innovation, Governance, and Public Trust | 2025 | 25 | In effect | EO 14179 |
| OMB M-25-22 — Driving Efficient Acquisition of AI in Government | 2025 | 13 | In effect | EO 14179 |

**6 documents, 115 pages.** M-25-21 rescinded and replaced M-24-10; EO 14148 (Jan 2025)
rescinded EO 14110. EO 13960's federal AI use case inventory requirement remains in effect.

## Notes

- **M-25-21 rescinded and replaced M-24-10.** A 2024 M-24-10 compliance plan still
  posted alongside (or instead of) an M-25-21 plan is flagged `superseded=yes` in
  `documents.csv`.
- Document types follow the controlled vocabulary in `README.md`. The use case
  inventory itself is excluded (tracked in the repo-root `agency-inventory-tracker.csv`).
- The **Chief AI Officer** column shows the named officer where the agency disclosed
  one; `designated` means a CAIO exists but was not publicly named. Full status strings
  are in `coverage.csv`.
- Generated 2026-05-21 from five parallel research sweeps.
