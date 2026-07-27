# Adoption baselines — DNSSEC addition, researched 2026-07-20→26

Point-in-time research record (conventions: `README.md`). This file **adds
one baseline series** to the set documented in
`adoption_baselines_2026-07-06.md`, which remains authoritative for the
Federal HTTPS, PIV, FedRAMP/Cloud First, and workplace-PC series. Full
verification record: `research_2026-07-26/` (deep-research round executed
2026-07-20→21, 3-vote adversarial verification; implementation pins
2026-07-26).

The plotted series ships in the dashboard repo at
`dashboard/lib/data/adoption-series.ts` (id **`dnssec-gov`**), renders at
**/adoption** and **/figures/adoption-curves**, and exports with full
provenance + clock metadata at `/api/adoption-series.csv`.

### Federal DNSSEC on .gov — OMB M-08-23

- Mandate: OMB M-08-23 "Securing the Federal Government's Domain Name System
  Infrastructure", **2008-08-22** (Karen Evans). Two deadlines: .gov TLD
  signed by **January 2009** (done 2009-02-28, one month late); ALL agency
  second-level .gov domains signed by **December 2009**. Rescinded by
  M-17-26 (2017) with the requirement carried into Circular A-130 — the
  year-0 date is uncontested.
- Technology clock (dashboard `introduced`): **2005-03-01** — DNSSEC-bis
  final specs (RFC 4033–4035, March 2005), the redesigned protocol agencies
  actually deployed. Mandate lag ≈ **3.5 years**, consistent with the
  chart's practical-availability convention (HTTPS ≈1994 Netscape, smart
  cards ≈1995). The original RFC 2535 (1999) predates it but was
  operationally unworkable (key-handling redesign → DNSSEC-bis).
- Metric: share of federal second-level .gov domains DNSSEC-signed.
  Plotted points:
  - **2009-12-31 · ~20%** (approx) — at the memo's own second-level
    deadline; press-corroborated (Computerworld "80% of gov't Web sites
    miss DNS security deadline"; GCN).
  - **2010-09-30 · 35%**, **2011-09-30 · 65%**, **2012-09-30 · 74%** — the
    government-wide "DNSSEC Implementation" percentages from OMB's FISMA
    Annual Reports to Congress (FY2011 report p.8 + Figure 9; FY2012 report
    p.25 + Figure 10), measured by DHS scans, not agency self-reports.
    Verified against the archived PDFs 2026-07-26
    (`research_2026-07-26/dnssec_series_pins.md`).
  - **2026-07-26 · 84.4%** (approx) — IFP-computed from NIST's live USGv6
    deployment monitor over CISA's 1,338-domain federal list (1,129 zones
    signed; the stricter signed+valid+chained "Good" share is 81.8%).
- Cross-check / do-not-mix: NIST's LISA '12 zone-count series reports
  **54% signed-and-chained (910 zones) on 2012-03-26** — a different
  denominator (all enumerated federal zones) than the FISMA DHS scans;
  plotting it would produce a false 65%→54%→74% dip. Cross-check only.
  NIST's sampled monitor showed ~57% at the same date (methodology
  difference, not a contradiction).
- Story shape: ~20% at the mandate's own deadline; the climb to 74% by
  FY2012 followed DHS scanning + the 2011 cross-agency Tiger Team's weekly
  scoreboard — measurement, not the memo, moved the number (same lesson as
  Pulse for HTTPS; BOD 18-01 later locked in the HTTPS gains).
- Deprecated / do-not-use (recorded in `research_2026-07-26/refuted_claims.md`):
  the NIST monitor's snapshot archive does NOT provide a ready historical
  series back to 2012 (claim refuted 0-3); any post-2012 fill-in must be
  assembled from Wayback captures.
