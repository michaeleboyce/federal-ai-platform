# Research 2026-07-26 — mandated federal technology-adoption series

Point-in-time research record (conventions: `../README.md`). Two passes are
recorded here:

1. **Deep-research round, executed 2026-07-20→21** — question: beyond the
   three mandated adoption series already charted on /adoption (HTTPS
   per M-15-13, PIV per HSPD-12, FedRAMP cloud per the 2011 memo), which
   other federal technology mandates have publicly available, chartable
   adoption time series? Method: 105 agents, 5 search angles, 23 sources
   fetched, 113 claims extracted → top 25 verified by 3-vote adversarial
   refutation panels → **23 confirmed, 2 refuted** → 8 synthesized findings.
   Access dates 2026-07-21 unless a file says otherwise.
2. **Implementation pins, executed 2026-07-26** — the two facts pinned
   directly against primary sources when the DNSSEC series was added to the
   dashboard (`dashboard/lib/data/adoption-series.ts`, id `dnssec-gov`;
   visual at /adoption and /figures/adoption-curves).

Headline answer: **DNSSEC (.gov signing, OMB M-08-23) and DMARC/HSTS (CISA
BOD 18-01) are chartable now; IPv6 is chartable with effort** (contestable
year-0 across three instruments + an unassembled historical series). The
DNSSEC series shipped 2026-07-26. EFT/direct deposit (DCIA 1996), IRS e-file
(RRA 1998), M-22-09 MFA, e-invoicing, GPEA, M-19-21 records, EMV, Login.gov,
and FITARA/data-center metrics were NOT reached by verification this round —
treat as unresearched, not NOT-CHARTABLE (see
`caveats_and_open_questions.md`).

| File | What it is |
|---|---|
| `verified_findings.md` | The 8 synthesized findings, per-finding Claim / Confidence / Vote / Sources / Evidence. Citable beats come from here. |
| `dnssec_series_pins.md` | The 2026-07-26 implementation pins: NIST monitor endpoint computation (84.4% signed of 1,338 domains) and FISMA PDF verifications (35/65/74%). |
| `sources.md` | All 23 fetched sources — URL, quality, search angle, claim count. |
| `refuted_claims.md` | The 2 refuted claims — DO-NOT-USE list with consequences. |
| `caveats_and_open_questions.md` | 7 caveats (incl. the unresearched-candidates list) + 4 open questions (IPv6 Wayback assembly, EFT/IRS follow-up, BOD 18-01 extension, DNSSEC denominator reconciliation). |

The baseline block for the plotted DNSSEC series lives at
`../adoption_baselines_2026-07-26.md` (sibling of the 2026-07-06 record,
which remains authoritative for the HTTPS/PIV/FedRAMP/workplace-PC series).
