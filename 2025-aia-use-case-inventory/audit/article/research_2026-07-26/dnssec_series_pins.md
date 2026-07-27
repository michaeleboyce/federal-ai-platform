# DNSSEC series — implementation-time pins (executed 2026-07-26)

Point-in-time record of the two facts pinned against primary sources when
the `dnssec-gov` series was added to `dashboard/lib/data/adoption-series.ts`.
Everything below was fetched and computed **2026-07-26**.

## 1. The 2026 endpoint — NIST USGv6 deployment monitor

- Source: https://usgv6-deploymon.nist.gov/cgi-bin/generate-gov
  ("Detailed IPv6 & DNSSEC Service Interface Statistics for **2026.07.26**"),
  methodology at https://usgv6-deploymon.nist.gov/govmon.html.
- Population: **1,338 federal second-level .gov domains** (the monitor
  tracks CISA's official federal .gov list; the 2026-07-21 verification pass
  found the sets identical — the count was 1,339 on 2026-07-20 and 1,338 on
  2026-07-26; the list shifts by a domain or two day to day).
- Computation (IFP, from the raw per-domain table — each domain's DNSSEC
  cell is a Signed/Valid/Chained triple per the govmon.html legend):

  | DNSSEC state | Count | Share |
  |---|---|---|
  | Good `S/V/C` (signed, valid, chained from .gov) | 1,095 | **81.8%** |
  | Island `S/?/B` | 24 | 1.8% |
  | Error `S/I/C` | 10 | 0.7% |
  | Error `U/I/C` | 24 | 1.8% |
  | Unsigned `U/-/-` | 185 | 13.8% |
  | **Signed (any `S…`)** | **1,129** | **84.4%** |

- **Plotted value: 84.4** (share whose zone is DNSSEC-signed — first letter
  `S`), dated 2026-07-26, `approx: true`. "Signed" is the closest measure to
  the FISMA-report metric the rest of the series uses; the stricter
  fully-working "Good" share (81.8%) is recorded here and in the dashboard
  method notes. Denominator differs from the FY2010–FY2012 FISMA scans
  (agency-enumerated zones then; CISA registry now) — flagged in the series
  note and both chart captions.

## 2. The FISMA-report percentages — verified against the archived PDFs

Both PDFs fetched from obamawhitehouse.archives.gov and text-verified
2026-07-26:

- **FY2011 FISMA Annual Report to Congress**
  https://obamawhitehouse.archives.gov/sites/default/files/omb/assets/egov_docs/fy11_fisma.pdf
  - p.8 capability table: "DNSSEC Implementation **35% 65%**" (FY2010 →
    FY2011 columns).
  - p.25 narrative (Figure 9 section): "…wide compliance rate at **35% in
    FY 2010 to 65% in FY 2011**. The DNSSEC values were measured using an
    automated tool developed by DHS."
- **FY2012 FISMA Annual Report to Congress**
  https://obamawhitehouse.archives.gov/sites/default/files/omb/assets/egov_docs/fy12_fisma.pdf
  - p.25 capability table: "DNSSEC Implementation **65% 74%**" (FY2011 →
    FY2012 columns).
  - p.31 narrative (Figure 10 section): "…compliance rate at **65% in
    FY 2011 to 74% in FY 2012** as measured by the DHS Cybersecurity
    [capability tool]."

FY points are plotted at fiscal-year end (09-30) per the PIV-series
convention. The Dec-2009 ~20%-at-deadline point is press-corroborated
(Computerworld "80% of gov't Web sites miss DNS security deadline"; GCN),
carried from the 2026-07-21 verified round (`verified_findings.md`
Finding 2) with `approx: true`.

## Do-not-mix note

The NIST LISA '12 zone-count figure (**54% signed-and-chained, 910 zones,
2012-03-26**) is deliberately NOT plotted: its denominator (all enumerated
federal zones) differs from the FISMA DHS-scan series, and mixing them
produces a false 65%→54%→74% dip. It remains a cross-check only
(`verified_findings.md` Finding 2; NIST's sampled monitor showed ~57% at the
same date — methodology difference, not a contradiction).
