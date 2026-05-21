# Followup adjudication notes — QA-confirmed recovery set

## What this is

This `agent_followup/` slice is **not** one of the original Stage-2 agency
batches. It is a small QA-confirmed followup pass that recovers 6 genuine
cross-year matches the deterministic matcher missed and that the Stage-2
batch agents could not emit.

The batch agents were blocked by the charter's **one-slug-one-decision**
rule: for four of these six pairs, the 2024 or 2025 slug already appeared
in a batch `reject_rename` decision (the batch correctly rejected a
*different* fuzzy-matched pair and sent the slug to residual). A second
decision on that slug from the same agent would have been a conflict, so
the agents instead documented the genuine successor in prose — e.g.
batch-3 notes name "SmartPD Creator" as the real 2025 successor of the
2024 Position Description Tool, and batch-2 notes recover "Smart Search"
as the real partner of the 2025 SAMHSA Kendra tool.

This followup emits those recoveries as proper `recover_match` decisions.
The integrate conflict detection was updated so a `recover_match` (and
`confirm_rename`) **supersedes** a shared-slug `reject_rename` — the reject
freed the slug to residual, the recover legitimately re-links it; both
decisions are kept and the apply step orders reject before recover.

## Decision counts

QA proposed **6** recoveries. **5 are applied** here; **1 is held back**
(#5, VA GE Portable — see caveat below).

| Action | Count |
|---|---|
| `recover_match` (applied) | 5 |
| `recover_match` (held back) | 1 |
| **Total proposed** | **6** |

## The 6 QA-proposed recoveries

| # | Agency | 2024 → 2025 | Confidence | Status |
|---|---|---|---|---|
| 1 | Treasury | Form 1040X Tax Examiner Assistant → Form 1040X STAR | high | applied |
| 2 | HHS | Smart Search (SAMHSA) → AWS Kendra Search Tool | high | applied |
| 3 | DOE | Position Description Tool → SmartPD Creator | high | applied |
| 4 | FDIC | Deposit Insurance Determination → Provisional Holds Model | high | applied |
| 5 | VA | GE Portable Critical Care Suite 2.x → GE AMX Portable X-ray Machines | medium | **held back** |
| 6 | VA | FlexLine (app/dependency mitigation) → Actions for Application Vulnerabilities | medium | applied |

`recommendations.json` contains the **5 applied** decisions. The held-back
#5 is documented below but deliberately omitted from `recommendations.json`
so the apply step's reconciliation invariant holds.

The VA medium-confidence recovery #6 matches on **name + domain only** —
the 2025 row is a bare stub with no narrative (empty expected_benefits /
system_outputs, filed at the Retired stage). The high-confidence four have
bilateral narrative evidence and are corroborated by the corresponding
batch agents' prose notes.

## Held back — #5 (VA GE Portable Critical Care Suite)

The QA list assumed the 2024 use case `va-ge-portable-critical-care-suite-
2-x` was currently `retired_2024`. It is **not**: the deterministic matcher
already linked it `continued` (exact_name) to an identically-named 2025 use
case (`va-ge-portable-critical-care-suite-2-x`, id 117722, actively
Deployed). The proposed `recover_match` target,
`va-ge-amx-portable-x-ray-machines`, is a separate bare retired stub.

A `recover_match` only deletes a `retired_2024` row for its 2024 slug —
here there is none — so applying it would leave the 2024 row in **both** a
`continued` link (to 117722) and a new `renamed` link (to GE AMX). That
fails the apply script's 1:1 uniqueness assertion (verified empirically:
`AssertionError: 1 uc_2024_id(s) with a duplicate continued/renamed/
retired_2024 link (e.g. (24971, 2))`).

Per the charter's "if you cannot confidently resolve, STOP and report"
clause, #5 is held back. Resolving it properly requires a separate
decision on the matcher's existing exact-name `continued` link — e.g.
treating the 2024 item as a `split` into both the 2025 Critical Care Suite
row and the GE AMX row — which is outside the scope of a single
`recover_match` and would change the expected count deltas.
