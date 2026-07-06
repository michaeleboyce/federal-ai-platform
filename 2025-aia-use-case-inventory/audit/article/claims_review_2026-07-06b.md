# Claims review — 2026-07-06 (b): scout-research wave

Second same-day review (the morning file `claims_review_2026-07-06.md` is
never edited after the fact). Sources: four research-scout passes (DB +
authorized web research); raw evidence with URLs + access dates preserved
in `research_2026-07-06/`. All web facts accessed **2026-07-06**.

## 1. CORRECTIONS — fix before publishing

### 1.1 The inventory's statutory sunset is 2027-12-23, NOT 2028

The current draft says Congress "sunset the legal requirement … in 2028."
Advancing American AI Act § 7225 (Pub. L. 117-263, at 40 U.S.C. 11301
note): inventories required "continuously thereafter for a period of
5 years" from enactment **2022-12-23** → lapses **2027-12-23**. If a 2028
hook is wanted: "the final mandated inventory would publish in early
2028." Post-sunset the inventory continues only as OMB policy — which is
the reform window. Source: uscode.house.gov (research README).

### 1.2 DoD blind spot ≈ one-third, not "~60% of headcount"

`audit/retag/TODO.md` §5 previously said the DoD gap is "roughly a
60%-of-headcount asterisk" — not defensible against the civilian
denominator. OPM FedScope (Sept 2024): DoD civilian workforce 772,549 of
~2,313,216 federal non-postal civilians ≈ **33%**; somewhat over a third
adding other non-filers + the FedScope-excluded intelligence community.
(60% is only reachable by folding in ~1.3M active-duty military — the
wrong frame for a civilian AI inventory.) TODO.md §5 fixed in this
change set. **The 2.31M total has exactly one legitimate use: sizing this
blind spot.** Person-weighted access claims use the eligible base — see
`access_derivation.md`.

### 1.3 § 3613 "demonstrable need" — the prior draft inverts the statute

The prior draft: "CISOs cannot simply decline to enable … without
documentation [of] demonstrable need." Verbatim statute (44 U.S.C.
§ 3613): **(e)(1)** presumption of adequacy; **(b)** an agency finding a
package "wholly or substantially deficient" SHALL document its reasons;
**(e)(2)(B)** "demonstrable need" is the head-of-agency authority to add
MORE controls — a shield, not a documented duty to decline enablement.
Also: § 3613 governs the AUTHORIZATION decision, not staff enablement.
Accurate framing: the law makes reuse the presumptively-adequate default
and puts the documentation burden on the deviation; the enablement gap
downstream of the ATO is not measured by any official artifact (no GAO
product covers it) — IFP's reach-vs-access data is the original
contribution. Recommendation follows: extend documentation-on-deviation
from authorization to enablement.

### 1.4 Palantir: ceilings vs obligations — label precisely

"DHS $1B BPA / USDA $300M" (fact sheet §6.3) are BPA/IDV **ceilings**.
FPDS **obligations** FY2024–26: DHS $347M, USDA $140M (Palantir total
$3.316B / 194 awards, DoD $2.10B). Both true; never mix the two framings
in one sentence.

## 2. NEW HEADLINE STATS (verified this wave)

1. **~$5M vs $3.3B**: all FY2024–26 contract line items naming a GenAI
   chat/assistant product total ≈ $5M government-wide (ChatGPT $2.2M —
   including a literal $1 "OPENAI CHATGPT ENTERPRISE" OneGov line at the
   FCC — Copilot $1.5M, OpenAI-broad $1.1M, Claude $18,960, Gemini $0),
   vs Palantir's $3.316B. ⚠ Caveats: bundling (Copilot/Gemini ride
   inside M365/Workspace agreements — understates GenAI reach and
   *reinforces* "no new procurement needed"); obligations ≠ ceilings;
   keyword match misses generically-described awards. Raw JSON + query
   scripts in `research_2026-07-06/`.
2. **USAi pinned to primary source**: GSA FY2027 CJ — "15 pilot agencies
   with a substantial list … in the waiting list"; FY2027 transition to
   cost-recovery; funded via FCSF with a cap limiting growth.
3. **20x trio re-verified live 2026-07-06**: ChatGPT Enterprise
   (FR2533155773, auth 2026-01-09), Gemini for Government (FR2604952026,
   2026-01-21), Perplexity (FR2604643715, 2026-02-01) — each 1
   authorization / 0 recorded reuses, ~5–6 months post-auth. ⚠ Ledger
   under-records reuse; phrase as "no recorded reuses".
4. **Dormancy quadrant**: only 4 agencies have ≥20 core-AI services in
   scope of held ATOs AND corroborated low staff access — DOJ (63,
   latent ~1% IFP-assessed), NSF (54, pilot ~0.2%), HUD (41, pilot
   ~0.15%), SBA (41, none 0%). ⚠ "In scope of a package the agency
   holds an ATO for" — never "enabled".
5. **Measurement gap**: 16 high-reach (≥20 services) agencies have no
   access assessment at all (SEC, FDIC, FRB, CFTC, FHFA, PBGC, TVA,
   FRTIB…). Unmeasured ≠ zero; but in people terms the unassessed
   agencies hold only ~32K of the ~747K eligible staff (~4%) — the 22
   assessed agencies cover ~96% of the eligible base. (Populations
   differ by lens: 24-of-46 unassessed in the FedRAMP reach league;
   34-of-56 in the workforce-profile base.) See `access_derivation.md`.
6. **Never-spread aging**: the 26 single-ATO authorized core-AI products
   have a median ~13 months since authorization (oldest 58). **Bedrock
   is in scope of packages held by 28 of 46 agencies** (Moderate + High).
7. **OMB's own concession** (2025 guidance, verbatim): "it is
   impracticable to require individualized reporting for all instances
   of AI that rely on commercial-off-the-shelf products or services."
   Field list (24 base + 9 high-impact) contains no access/user-count/
   integration/infrastructure field; the 2024 template's five
   infrastructure questions were dropped for 2025.
8. **Governance gap**: of 223 deployed + high-impact use cases, the
   inventory records completed independent review for 36 (16%), ongoing
   monitoring 40 (18%), pre-deployment testing 44 (20%); VA (94) and DOJ
   (73) report zero completed reviews; DHS the outlier (26/38). ⚠ Blank
   = "not reported", not proven "not done"; population skews classical
   ML, adjacent to the GenAI thesis.
9. **Readiness ceiling**: 0 of 68 agencies reach IFP tier A or B; top
   composite is FTC 53.7 ("C / Building"). ⚠ IFP's own rubric — "by our
   scorecard".
10. **Hygiene**: 67 distinct GenAI systems operational-in-2024 vanished
    from their agencies' 2025 filings with no Retired trace (HHS 19,
    Treasury 11, DOL 7, DOI 7); +25 more from five agencies that stopped
    filing. Clean exemplar: the 11 IRS voicebots — publicly still
    operational (irs.gov/FedScoop/GAO) yet absent from Treasury's 2025
    inventory. ⚠ Part of the 67 is scope-cleanup (DOL had listed
    "Microsoft Office Suite", "Facebook Mobile App") — lead with branded
    still-running cases; say "no longer reported", never "shut down".
    The Retired stage exists (314 rows) but 26 of 45 filers report zero
    retirements — discipline, not fields.

## 3. ADVERSARIAL FLAGS (respect in the draft)

- **Two agency rankings disagree by design**: volume-weighted
  `org_ai_maturity` (GSA/DOC/VA "leading") vs governance-weighted
  `agency_readiness` (GSA, DOC tier F; VA rank 31). Pick one frame per
  agency or make the divergence the point.
- **GenAI doubling has a scope artifact**: 2025 corpus is ~72% larger
  than 2024's; cleaner cite = 2,171 genuinely-new vs 1,148 continued
  (lineage), with one honest caveat sentence.
- **"Adoption arrived" vs "nobody is ready"**: resolve explicitly —
  breadth is real, depth/governance absent; adoption outran readiness.

## 4. Where each theme's full evidence lives

- Budget: `research_2026-07-06/{usaspending_*.json, query_*.py,
  gsa_fy2027_cj_usai_excerpts.md}`; TMF real-but-lapsed (authority
  expired 2025-12; ~$50M GenAI awards 2024); cloud-first adoption
  baseline (2010 mandate → GAO still critical 2019/2022/2026) for the
  "decade compressed into two years" framing (order-of-magnitude
  contrast only).
- FedRAMP: `research_2026-07-06/fedramp_enforcement_research.md`.
- Inventory reform: `research_2026-07-06/omb_2025_*.md`.
- Angles + workforce: `research_2026-07-06/angles_external_sources.md`.
- Person-weighted access: `access_derivation.md` (built by
  `scripts/build_access_derivation.py`).
