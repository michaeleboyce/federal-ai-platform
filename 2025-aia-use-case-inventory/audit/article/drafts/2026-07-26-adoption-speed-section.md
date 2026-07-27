# Draft section — the fastest federal rollout (drafted 2026-07-26)

Point-in-time draft (conventions: `../README.md`). Expands the author's
paragraph on adoption speed for inclusion in the piece. Every number below
traces to the /adoption chart's plotted series (exportable at
`/api/adoption-series.csv`) and the verification records:
`../adoption_baselines_2026-07-06.md`, `../adoption_baselines_2026-07-26.md`,
`../research_2026-07-26/` (3-vote adversarial verification). LLM-access and
cloud figures pulled from the live series 2026-07-26. Companion visual:
**/figures/adoption-curves** (tech clock, mandates marked, per-line sources
below the frame).

---

## The section (ready for inclusion)

Indeed, by most accounts this has been the most rapid adoption of a
software-based technology in the federal government's history. As part of
this research, we charted reported federal technology adoption over time
from publicly available records — GSA's archived domain scans, OMB's annual
FISMA reports to Congress, the FedRAMP marketplace ledger, NIST's live
deployment monitor — and re-based each rollout onto two clocks: years since
the technology became widely available, and years since the federal mandate
that required it.

Generative AI is, perhaps with the sole exception of cloud, the most
visible technology rollout in the federal government's history — and thanks
to the statutorily required AI use case inventory, almost certainly the
most granularly documented. But visibility is not what sets it apart. Speed
from release is. Measured from the date the technology became widely
available, no prior federal adoption we could chart comes close. Three and
a half years after ChatGPT's release, our corroborated floor puts a
general-purpose AI tool in the hands of 39 percent of AI-eligible workers
at the agencies we profiled — 80 percent on the bullish reading that counts
an agency's full eligible workforce from its first corroborated rollout. At
the same age, every predecessor technology was at or near zero inside the
government: three and a half years into the World Wide Web era of HTTPS
(1998), no federal enforcement existed and the mandate was still seventeen
years away; three and a half years after Amazon opened EC2 (early 2010),
not one CFO Act agency held an ATO on a FedRAMP-authorized cloud service,
because FedRAMP did not yet exist; three and a half years after the modern
DNSSEC specifications (2008), OMB was only just issuing the memo that would
require them.

The one plausible rival is the secure web protocol itself — and the
comparison is instructive. HTTPS enforcement on federal websites nearly
quadrupled in the eighteen months after OMB's 2015 HTTPS-Only Standard,
from 16.8 percent of live parent .gov domains to 65.5 percent: the sharpest
post-mandate response in our data. But that sprint began at year
twenty-one of the technology — HTTPS had been in commercial use since
Netscape shipped SSL in 1994. It measured domains flipping a protocol
setting, not employees adopting a new way of working. And it was driven by
a public scoreboard: GSA's Pulse dashboard published every agency's
compliance weekly. DNSSEC, the other security sprint in our data, tells the
same story in miniature — roughly 20 percent of federal domains were signed
at the memo's own 2009 deadline, and the number only climbed (35, 65, 74
percent across FY2010–FY2012) once DHS began scanning every domain and a
cross-agency Tiger Team published the results. In the federal enterprise,
protocol mandates move when someone keeps score; they are also, by
construction, narrow. Nobody's workday changed when a zone file got signed.

Put the mandates themselves on the technology's clock and the compression
is unmistakable: the HTTPS mandate arrived 20.6 years after the technology
entered commercial use, the smart-card login mandate at year 9.2, the
FedRAMP memo at year 5.3, the DNSSEC memo at year 3.5 — and the
government-wide LLM-access mandate at year 2.6. Generative AI is the only
general-purpose work technology in the set whose mandate arrived that
early, and the only one whose mandate landed on an adoption already
underway: when the AI Action Plan directed agencies to make frontier
models available in July 2025, our corroborated floor already stood near 12
percent of eligible workers (46 percent bullish); eleven months later those
readings had climbed to 39 and 80 percent. Prior mandates started federal
adoption clocks. This one accelerated a clock that was already running.

Two honesty notes the chart carries and this section should keep. The
series count different things — domains (HTTPS, DNSSEC), users required to
authenticate (PIV), agencies holding authorizations (cloud), workers with
tool access (generative AI) — so the comparison is about trajectory shape
on comparable clocks, not a shared denominator. And the generative-AI lines
are IFP assessments built from dated, web-corroborated rollout evidence,
not OMB data; evidence publication lags deployment, which means the floor
is a floor twice over — and some of the post-mandate steepness reflects
corroboration catching up with rollouts, not rollouts themselves.

---

## Numbers used, traced

| Claim in text | Value | Source of record |
|---|---|---|
| LLM floor at yr ~3.5 of ChatGPT | 39.3% (2026-06-11) | `federal-llm-access` series (IFP evidence base; /experience methodology) |
| LLM bullish at yr ~3.4 | 80.3% (2026-05-06) | `federal-llm-access-bullish` series |
| Floor / bullish at the mandate (2025-07-23) | ≈12% / ≈46% | same series, points 2025-07-09 (12.1 / 46.3) |
| Cloud at yr 3.5 of EC2 (early 2010) | 0 CFO Act agency ATOs | `cloud-cfo-ato` series starts 2011-12-08 (FedRAMP memo); first ATO step 2013 |
| Cloud crossed 50% of CFO Act agencies | May 2016 (yr 4.5 post-memo) | `cloud-cfo-ato` (marketplace snapshot 2026-06-12; floor) |
| HTTPS 16.8% → 65.5% in 18 months | Jun 2015 → Dec 2016 | GSA archived Pulse scans, IFP-computed (`https-enforces`) |
| HTTPS mandate at yr 20.6 of tech | M-15-13 (2015-06-08) vs Netscape SSL ≈Oct 1994 | `adoption_baselines_2026-07-06.md` |
| DNSSEC ~20% at own deadline; 35/65/74% FY2010–12 | Dec 2009; FY-end points | OMB FY2011/FY2012 FISMA reports (DHS scans); press-corroborated deadline point — `research_2026-07-26/dnssec_series_pins.md` |
| DNSSEC today | 84.4% signed (2026-07-26) | NIST USGv6 monitor, IFP-computed over CISA's 1,338-domain list |
| Mandate lags 20.6 / 9.2 / 5.3 / 3.5 / 2.6 yrs | tech-clock rules | chart clock key; instruments linked in the figure's per-line sources |
| PIV decade of drift, 42→72% in one quarter | FY2010 1.24% → Nov 2015 81% | OMB FISMA reports + 2015 Cybersecurity Sprint results |

## ⚠ Phrasing guardrails

- ⚠ "Most rapid adoption in federal history" — keep the qualifier **"of the
  rollouts we could chart from public records"** (or "by most accounts").
  We verified five mandated series and three consumer baselines; we did NOT
  exhaustively rule out every historical rollout (EFT/DCIA, IRS e-file, and
  others remain unresearched — `research_2026-07-26/caveats_and_open_questions.md`).
- ⚠ Do not call GenAI "the most tracked" without the inventory clause —
  HTTPS's Pulse dashboard was arguably the most publicly tracked rollout;
  the defensible claim is *most granularly documented, via the statutory
  use case inventory*.
- ⚠ HTTPS concession must carry all three qualifiers: post-mandate clock
  only; year ~21 of the technology; domains-not-workers metric.
- ⚠ The 39%/80% pair must always appear with population ("AI-eligible
  workers at IFP-profiled agencies") and the floor/bullish definitions;
  never government-wide workforce.
- ⚠ Post-mandate acceleration (12→39 floor) must carry the evidence-lag
  caveat — corroboration catching up is part of that slope.
- ⚠ Never plot or cite the NIST 54% (Mar 2012) DNSSEC figure as part of the
  FISMA series (different denominator), and never use Proofpoint's "~20% at
  Oct 2017" DMARC baseline (refuted 0-3) — `research_2026-07-26/refuted_claims.md`.
- ⚠ Security-hygiene vs general-purpose: when citing the shrinking mandate
  lag, note DNSSEC/HTTPS are protocol-hygiene mandates (fast lag by
  design); the like-for-like comparison for GenAI is PC / cloud.
