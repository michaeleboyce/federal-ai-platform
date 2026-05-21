# Federal Agency AI Strategy & Policy Tracker

A catalog of the AI **strategies and policies** federal agencies have published — the
documents themselves, the year each was issued, and how each maps to the artifacts
OMB requires under M-24-10 and M-25-21.

There is no central, public index of these documents. ai.gov and cio.gov host only
White-House-level policy (executive orders, OMB memos); the agency-level strategies
and compliance plans are scattered across individual agency websites with no standard
URL pattern. This tracker closes that gap.

## What's here

| File | What it is |
|---|---|
| `TRACKER.md` | Human-facing coverage matrix — one row per agency, which documents exist, what year. |
| `documents.csv` | Long-format catalog — one row per document, with publication year and OMB-artifact mapping. |
| `coverage.csv` | One row per agency — search status, AI landing page, document counts, gaps. |
| `documents/<AGENCY>/` | The downloaded original documents (PDF / HTML). |

## Scope

- **Agencies:** all 44 agencies that filed a 2025 AI use case inventory, plus DoD
  (inventory-exempt but a major AI-strategy publisher) = **45 agencies**.
- **Time window:** documents published **2023 onward**.
- **Level:** department-level *and* component / sub-agency policies.
- **Included:** AI strategies, OMB compliance plans, generative-AI policies, CAIO
  designations, AI governance charters, AI procurement policies, and any other formal
  AI-related policy or guidance.
- **Excluded:** news / press releases, blog posts, individual use-case or product
  entries, and the AI use case inventory itself (tracked separately in the repo-root
  `agency-inventory-tracker.csv`).

## OMB required-artifact reference

The two governing OMB memoranda and the artifacts they require agencies to produce.
M-25-21 (Trump administration, under EO 14179) **rescinded and replaced** M-24-10
(Biden administration, under EO 14110).

| Artifact | Memo | Deadline | Public? |
|---|---|---|---|
| Chief AI Officer (CAIO) designation | M-24-10 / M-25-21 | 60 days | Notified to OMB; announcement sometimes public |
| AI Governance Board | M-24-10 / M-25-21 | 60 days / 90 days | Internal; charter sometimes posted |
| Compliance Plan | M-24-10 | ~Sept 2024 | **Public** on agency site |
| Compliance Plan | M-25-21 | ~Sept 30, 2025 | **Public** on agency site |
| AI Strategy | M-25-21 | ~Sept 30, 2025 (180 days) | **Public** on agency site |
| Generative AI policy | M-25-21 | ~Dec 29, 2025 (270 days) | Internal; some posted |
| AI procurement policy | M-25-22 | 2025 | Varies |
| AI use case inventory | M-24-10 / M-25-21 | Annual | Public — *tracked elsewhere, not here* |

M-25-21 also collapses M-24-10's separate "safety-impacting" and "rights-impacting" AI
categories into a single **"high-impact AI"** definition.

## `document_type` controlled vocabulary

| Value | Meaning |
|---|---|
| `M-25-21 AI Strategy` | The 180-day agency AI strategy (~Sept 2025). |
| `M-25-21 Compliance Plan` | The 180-day compliance plan (~Sept 2025). |
| `M-24-10 Compliance Plan` | 2024-vintage compliance plan (historical / superseded). |
| `M-24-10 AI Strategy` | Rare 365-day strategy; mostly never produced before M-25-21 replaced it. |
| `Generative AI Policy` | Agency generative-AI acceptable-use policy. |
| `CAIO Designation / Announcement` | Public announcement of a Chief AI Officer. |
| `AI Governance Board Charter` | Publicly posted governance-board charter. |
| `Historical AI Strategy` | Standalone AI strategy from 2023, predating the OMB memos. |
| `AI Procurement Policy` | Agency M-25-22 procurement guidance. |
| `Other Department AI Policy / Guidance` | Catch-all: roadmaps, frameworks, ethics principles, directives, component-agency policies. |

## Methodology

Five research agents each swept ~9 agencies: locating the agency's AI landing page,
identifying every document matching the vocabulary above (2023+), downloading the
original into `documents/<AGENCY>/`, and recording the publication year, source URL,
and OMB-artifact mapping. Every agency was searched and appears in `coverage.csv`
even when no public document was found — that "searched, nothing public" result is
itself a finding. See `documents.csv` `notes` and `access_status` for per-document
caveats (e.g. an M-24-10 plan replaced by an M-25-21 version is flagged `superseded`).
