# omb_only adjudication — 2026-07-06

Every use case present in OMB's authoritative consolidated file
(`2025_individually_reported_AI_use_cases.xlsx`) but absent from the
per-agency source sweep was investigated and adjudicated. Verdicts live in
`decisions.csv` (consumed by `scripts/ingest_omb_only_rows.py` in the fix
chain); investigation drafts by three Sonnet agents are in `draft_*.csv`
and `skipfiles_coverage.md`; final verdicts were adjudicated by the lead.

## Headline: the gap was 68 rows, and it had two distinct causes

**Cause 1 — loader name-collision bug (23 of 68, plus 43 more nobody had
noticed).** `load_inventories.py` deduplicated individually-reported rows
by use-case NAME alone; any row whose name collided with an earlier row of
the same agency was silently skipped — even with a distinct `use_case_id`
and `bureau_component`. Multiple bureaus filing the same generically-named
tool ("Microsoft Copilot", "Chatbot", "Veritone", "Salesforce", ED's
templated "Generative AI - …" names) lost all but the first filing.
**Fixed at the root** (2026-07): a row is a duplicate only if
`use_case_id` AND `bureau_component` both match; name twins get `-2`/`-3`
slug tails (first occurrence keeps its slug, so pre-existing slugs are
stable). Recovery: **+66 rows** (use_cases 3549 → 3615), row skips 69 → 3.
The 23 omb_only rows from DOJ/DOE/ED/DHS now load natively from their own
agency files — better provenance than an OMB-mirror ingest — and are NOT
in decisions.csv.

Two knock-on repairs shipped with the fix:
- `scripts/apply_year_match_review.py`: stale `retired_2024`/`new_2025`
  residual verdicts (authored when the 2025 twin was invisible) now yield
  to the fresh baseline's exact-name links (15 + 7 superseded, printed
  per run); `confirm_rename` clears endpoint residuals like
  `recover_match` always did.
- `audit/checks/check_id_traceability.py`: DOJ-0160 allowlisted — DOJ
  itself filed PATTERN twice under one id (OJP and FBOP rows); we
  preserve the source faithfully.

**Cause 2 — rows that exist in NO per-agency source (45 of 68) → all
verdict `ingest`, from the OMB mirror.** Breakdown:

| Agencies | Rows | Why missing |
|---|---:|---|
| PBGC 16, FCC 6, EAC 4, OSC 1 | 27 | Their only per-agency files are the 20-row COTS checkbox grids (correctly deduplicated against the COTS aggregate). Their narrative individually-reported filings exist ONLY in OMB's consolidated file — the SKIP_FILES "superseded" assumption was a category error for these four. |
| NIGC 5, NEA 4, STB 2, OSHRC 1, FCA 3 | 15 | No per-agency narrative file was ever published. All five agencies already exist in `agencies` (created by the COTS aggregate load) — no new agency rows needed. |
| NCUA 3 | 3 | NCUA's sourced per-agency file is a stale 3-row inventory; NCUA filed a fuller inventory directly to OMB (NCUA-12/13/14-2025: Moody's, ADCo, CoStar modeling tools). |

## Lead adjudication notes (overrides / confirmations on the drafts)

- **STB `use_case_id = "TBD"`** (2 rows): kept as filed. The draft
  suggested synthesizing STB-0001/0002 — rejected per the "never invent
  values" rule; `id_provenance='omb_consolidated_ingest'` covers
  traceability.
- **PBGC near-duplicates** (ITSM virtual agent ↔ ServiceNow checkbox row;
  meeting summaries ↔ Teams Premium row; security monitoring ↔ Zscaler
  row): stay `ingest`. A narrative filing with problem statement and stage
  is not a duplicate of a product-capability checkbox; the product-linkage
  passes later in the chain connect them to products.
- **DHS Mobile Fortify (ICE)**: `ingest`, not `duplicate_of` the CBP row —
  DHS itself filed it as a separate ICE-side reportable entry (resolved
  natively by the loader fix; listed here because the draft flagged it).
- **DOL Prism Ally** (not an omb_only row — found by the SKIP_FILES
  supersession audit): the one row genuinely dropped by SKIP_FILES,
  backfilled by `scripts/backfill_dol_prism_ally.py`.

## Follow-up: heuristic-only tags on the new rows

The 111 new rows (66 recovered + 45 ingested) carry auto_tag heuristic
labels only — none went through the 2026-06 capability reviews
(general-LLM round 3, agentic review). Deltas: +83 `is_general_llm_access`
(plausible — the name-collision bug specifically dropped same-named
Copilot/Chatbot/LLM filings), +7 `ai_sophistication='agentic'`
(**worth a review round** — agentic was historically over-tagged 283→59).
Bands re-baselined to 559/789/66; a follow-up capability mini-review of
the 111 rows would firm these up.

## Residual state

After ingest, `omb_match_audit.match_status='omb_only'` must be **0** —
every OMB row is matched, ingested, or explicitly resolved. The
`check_loader_integrity.py` gate holds the bound so the gap can only
shrink; a future OMB republication that adds rows will trip it and demand
a new adjudication round.
