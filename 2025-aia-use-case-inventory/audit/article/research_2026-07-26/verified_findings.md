# Verified findings — mandated federal technology-adoption series (research executed 2026-07-20→2026-07-21)

Point-in-time research record (conventions: `../README.md`). Deep-research
harness run: 105 agents, 5 search angles, 23 sources fetched, 113 claims
extracted → top 25 adversarially verified (3-vote refutation panels) → 23
confirmed, 2 refuted (see `refuted_claims.md`) → 8 synthesized findings.
All access dates 2026-07-21 unless noted. Question: beyond HTTPS (M-15-13),
PIV (HSPD-12), and FedRAMP cloud, which federal technology mandates have
publicly available, chartable adoption time series?

## Finding 1
**Claim:** DNSSEC is chartable now. OMB M-08-23 (dated August 22, 2008, signed by Karen Evans) is a single, precisely dateable mandate with two explicit deadlines — the .gov TLD signed by January 2009 and ALL agency second-level .gov domains signed by December 2009 — and the memo itself defines the chart metric: a binary per-domain condition over an enumerable population, i.e. '% of federal second-level .gov domains DNSSEC-signed'. This is the same population style (share of federal .gov domains) as the existing Pulse HTTPS curve, making it the best structural fit of any new candidate.
**Confidence:** high
**Vote:** 9-0 across three merged claims (3-0 each)
**Sources:**
- https://obamawhitehouse.archives.gov/sites/default/files/omb/memoranda/fy2008/m08-23.pdf
- https://www.usenix.org/system/files/conference/lisa12/lisa12-final-27_0.pdf
**Evidence:** Primary PDF verified page-by-page: 'August 22, 2008 / M-08-23 ... The plan should ensure that all Agency .gov domains are DNSSEC signed by December 2009'; plan Section 1 enumerates 'the second level domains beneath .gov operated by your agency'. The NIST-authored USENIX LISA '12 paper independently confirms both deadlines. Caveats verified but non-refuting: the memo sets two deadlines (chart captions should say which); it was rescinded by M-17-26 in 2017 with the requirement carried into Circular A-130 — neither contests Aug 22, 2008 as year 0. Merges claims [2], [5], [6].

## Finding 2
**Claim:** The DNSSEC adoption series has at least 5-6 verified datapoints inside years 0-6 post-mandate: .gov TLD signed Feb 28, 2009 (~year 0.5, one month late); only ~20% of federal zones signed at the Dec 2009 second-level deadline (~year 1.3); 910 federal zones signed-and-chained = 54% of all federal zones on March 26, 2012 (~year 3.6, NIST daily-scan data in the LISA '12 paper); and government-wide DNSSEC compliance percentages published in OMB's annual FISMA reports to Congress — 35% (FY2010), 65% (FY2011), 74% (FY2012), plus per-agency tables for FY2013 — exactly as M-08-23 promised ('agency progress to deploy DNSSEC will be tracked and evaluated through annual FISMA reporting').
**Confidence:** high
**Vote:** 9-0 across three merged claims (3-0 each)
**Sources:**
- https://www.usenix.org/system/files/conference/lisa12/lisa12-final-27_0.pdf
- https://obamawhitehouse.archives.gov/sites/default/files/omb/memoranda/fy2008/m08-23.pdf
- Archived OMB FY2011-FY2014 FISMA Annual Reports to Congress (verifier inspected FY2011 Figure 9, FY2012 Figure 10, FY2013 Table 1/Figure 7, FY2014 DNSSEC section)
**Evidence:** The 54%/910-zones figure is verbatim in the primary LISA '12 PDF (author Scott Rose, NIST, who ran the federal DNSSEC scans); the ~20%-at-deadline figure was corroborated by contemporaneous Computerworld ('80% of gov't Web sites miss DNS security deadline') and GCN reporting. Verifiers directly inspected the archived FISMA reports and confirmed the 35/65/74% government-wide series. Methodology footnotes for the chart: the FISMA percentages are DHS scan results, the metric shifts to NIST domain counts in FY2014 and disappears in FY2015 (capping that sub-series at ~4 points); the 'all federal zones' denominator shrank over the period due to OMB M-11-24 domain reduction; NIST's sampled-domain monitor showed ~57% vs the paper's 54% in March 2012 (denominator methodology difference, not a contradiction). Merges claims [3], [4], [7].

## Finding 3
**Claim:** BOD 18-01 (DMARC/HSTS email and web security) is chartable now, with the cleanest year-0 of any candidate: CISA/DHS issued it October 16, 2017, with staged deadlines at 90 days (Jan 15, 2018: STARTTLS + SPF/DMARC p=none), 120 days (Feb 13, 2018: HTTPS/HSTS, weak ciphers disabled), and 1 year (Oct 16, 2018: DMARC p=reject on all second-level domains and mail-sending hosts). Both GAO and the live CISA directive text confirm the dates verbatim.
**Confidence:** high
**Vote:** 3-0
**Sources:**
- https://www.gao.gov/assets/710/706719.pdf (GAO-20-133, Feb 2020)
- https://www.cisa.gov/news-events/directives/bod-18-01-enhance-email-and-web-security
**Evidence:** GAO-20-133 Table 3 states the exact deadlines; the CISA-hosted directive (dated Oct 16, 2017) matches verbatim: 'Within one year after issuance of this directive, setting a DMARC policy of "reject" for all second-level domains and mail-sending hosts.' Non-refuting caveat for the chart: BOD 19-02 (2019) later replaced BOD 18-01, which affects how long the mandate stayed in force but not the year-0 date. Claim [8].

## Finding 4
**Claim:** GAO-20-133 provides primary-source BOD 18-01 datapoints from DHS NCATS scanning data. Per-requirement compliance across federal domains as of May 13, 2019 (~year 1.6): STARTTLS 99%, valid DMARC record 99%, DMARC p=reject implemented 92%, HTTPS enforced 90%, strong HSTS 86%, weak email protocols/ciphers disabled 83%, weak web protocols/ciphers disabled 98%. GAO also gives a three-point percent-of-AGENCIES full-compliance series (n=83): 4% (Mar 26, 2018), 7% (Oct 17, 2018), 7% (May 13, 2019 — three agencies newly complied, three fell out). The per-domain p=reject and HSTS percentages are the chartable curves; the agency full-compliance series is chartable but plateauing and non-monotonic.
**Confidence:** high
**Vote:** 6-0 across two merged claims (3-0 each)
**Sources:**
- https://www.gao.gov/assets/710/706719.pdf (GAO-20-133, Figure 3, Figure 4, pp. 26-28)
**Evidence:** Verifier downloaded the PDF and text-extracted it; every figure matches verbatim, including exact scan dates in footnotes 50/52. Caveats: the denominator mixes email domains and web hosts (per-requirement populations differ); the analysis covers only the 83 agencies present in all three NCATS Cyber Exposure Scorecards; the March 2018 full-compliance point measures only requirements due by then. Merges claims [9], [10].

## Finding 5
**Claim:** Vendor DNS-scan data fills in the dense early BOD 18-01 DMARC curve: Agari measured a four-point series over federal domains it monitored (n=1,106) — 18% with any DMARC at issuance (Oct 2017), 33% early Nov 2017, 47% mid-Dec 2017, 63% at the first deadline (Jan 16, 2018) — and Proofpoint measured 51.9% of federal agency domains compliant with the stricter one-year bar (valid SPF + DMARC p=reject) as of mid-September 2018 (~year 0.9). Combined with GAO's 92% p=reject at May 2019, this yields a 6+ point percent-of-federal-domains curve across the mandate's first 1.6 years.
**Confidence:** medium
**Vote:** 11-1 across four merged claims (three 3-0, one 2-1)
**Sources:**
- https://www.agari.com/blog/federal-government-dmarc-adoption-surges (live URL now redirects; cite Wayback: web.archive.org/web/20230328175353/... and web.archive.org/web/20180117064006/...)
- https://www.proofpoint.com/us/blog/threat-protection/federal-spf-and-dmarc-adoption-more-30-percent-points-leading-bod-18-01
- Corroboration: CyberScoop (Sept 17, 2018 and Jul 26, 2018), SecurityWeek (Oct 19, 2017), GAO-20-133
**Evidence:** All figures verified verbatim against archived primary posts and corroborated by independent outlets (CyberScoop carried both the 51.9% and 63% figures; SecurityWeek the 18% baseline). Medium confidence because: these are vendor measurements, one claim passed 2-1, the Agari denominator is its own monitored sample (1,106, drifting to 1,144) rather than the official 1,311-domain list Proofpoint used, and the vendors measure different bars (Agari: any DMARC policy; Proofpoint: SPF + p=reject). A chart must label each point's metric and denominator; the numbers themselves survived verification. IMPORTANT: a companion claim that ~20% met Proofpoint's compliance bar circa Oct 2017 was REFUTED (0-3) — do not use it as the year-0 baseline for the strict metric; Agari's 18% (any-DMARC) is the verified baseline. Merges claims [11], [12], [13], [14].

## Finding 6
**Claim:** The IPv6 mandate date is formally contestable across three instruments — this must be flagged on the chart. The candidates: OMB M-05-22 (August 2, 2005; backbone IPv6 by June 2008), the unnumbered Kundra memo 'Transition to IPv6' (September 28, 2010; public/external-facing web, email, DNS on native IPv6 by end-FY2012, internal clients by end-FY2014), and OMB M-21-07 (November 19, 2020, signed by Director Vought), which explicitly rescinds both predecessors and sets a new metric: share of IP-enabled assets on Federal networks operating IPv6-ONLY, with targets of 20% (FY2023), 50% (FY2024), 80% (FY2025) — targets in agency plans, not measured datapoints. The most defensible year-0 for a services-adoption curve is the 2010 Kundra memo, because its external-facing-services metric is exactly what NIST measures; but M-21-07's rescission language makes any single choice attackable.
**Confidence:** high
**Vote:** 21-0 across seven merged claims (3-0 each)
**Sources:**
- https://obamawhitehouse.archives.gov/sites/default/files/omb/assets/egov_docs/transition-to-ipv6.pdf
- https://www.whitehouse.gov/wp-content/uploads/2020/11/M-21-07.pdf
- https://georgewbush-whitehouse.archives.gov/omb/memoranda/fy2005/m05-22.pdf
- https://usgv6-deploymon.nist.gov/govmon.html
**Evidence:** All three primary PDFs read directly by verifiers. M-21-07 p.7: 'This memorandum rescinds M-05-22 ... August 2, 2005 and Transition to IPv6, September 28, 2010' (verbatim). Kundra memo header and FY2012 directive verified verbatim. M-21-07's 20/50/80% IPv6-only milestones verified verbatim and confirmed as plan targets, not measurements (an HSToday 2025 retrospective notes no agency publicly announced hitting 80%). NIST's own methodology page anchors its measurement to the 2008 (M-05-22) and FY2012 (2010 memo) deadlines, supporting the 2010-memo-as-clock recommendation. Merges claims [1], [17], [18], [19], [20], [21], [22].

## Finding 7
**Claim:** The NIST USGv6 Deployment Monitor (usgv6-deploymon.nist.gov) is a live, still-operational primary source measuring per-domain IPv6 enablement (DNS, Mail/SMTP, Web services) AND DNSSEC signing status (Signed/Valid/Chained) over exactly the same population as the existing Pulse HTTPS curve: the current snapshot (dated 2026-07-20) tests 1,339 second-level domains that match CISA's federal .gov list (current-federal.csv) with zero symmetric difference — federal-only, not the 16,322-row full registry. It therefore supplies today's-value endpoints for both the IPv6 and DNSSEC curves. However, a multi-year historical series from the monitor is NOT in hand: the claim that its snapshot archive reaches back to 2012 was refuted (0-3), so the time series must be assembled from Wayback captures of the monitor, the pre-2021 fedv6-deployment.antd.nist.gov predecessor, or NIST's history graphs — CHARTABLE WITH EFFORT.
**Confidence:** high
**Vote:** 9-0 across three merged claims (3-0 each); companion archive claim refuted 0-3
**Sources:**
- https://usgv6-deploymon.nist.gov/
- https://usgv6-deploymon.nist.gov/cgi-bin/generate-gov
- https://usgv6-deploymon.nist.gov/govmon.html
- https://github.com/cisagov/dotgov-data (current-federal.csv used for the population diff)
**Evidence:** Verifiers fetched the live monitor (heading 'Detailed IPv6 & DNSSEC Service Interface Statistics for 2026.07.20', one day old at check time, consistent with daily posting) and ran an empirical set-equality test: 1,339 monitored domains == 1,339 CISA federal .gov domains, exact match. Methodology page states verbatim that it relies on 'the Cybersecurity and Infrastructure Security Agency's Official Public List of .GOV Domains' and 'we only focus on second level domains'. Caveats: the monitor is a point-in-time snapshot page; it samples second-level domains; NIST notes it measures deployment only (not USGv6 Profile compliance); during Pulse's 2015-2020 run the federal list was GSA-stewarded (custody moved to CISA in 2021 — same registry). Merges claims [0], [15], [16]; the refuted snapshot-archive claim is excluded.

## Finding 8
**Claim:** Ranking for fit alongside the existing curves: (1) BOD 18-01 DMARC p=reject — % of federal .gov domains/mail hosts, precise single mandate date, 6+ datapoints densely covering years 0-1.6, dramatic S-curve shape (18%→92%); (2) DNSSEC — % of federal second-level .gov domains signed, single mandate date, 5-6 datapoints across years 0-6 with a slower curve (fraction→54%→74%), identical population to Pulse; (3) IPv6 — same population and a live NIST measurement source, but a contestable year-0 (three instruments) and an unassembled historical series. HSTS could ride as a BOD 18-01 sub-series (86% at year 1.6 via GAO) but has fewer early points. All three use percent-of-federal-enterprise-population metrics, matching the chart's existing y-axis convention.
**Confidence:** high
**Vote:** synthesis (no independent vote)
**Sources:**
- Synthesis of all verified findings above (GAO-20-133, OMB M-08-23, LISA '12 paper, OMB FISMA reports, Agari/Proofpoint archives, NIST USGv6 monitor)
**Evidence:** Derived ranking, not an independently verified claim: it follows directly from the verified properties — datapoint density within the chart's 12-year window, single vs. contested mandate date, and percent-of-.gov-domain populations. No surviving claim contradicts the ordering.

