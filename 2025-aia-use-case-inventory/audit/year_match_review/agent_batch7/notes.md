# Batch 7 — year-match review notes (USAID, DOJ, State, EPA, NSF, DOT, FERC, USCCR)

## Decision counts

| action | count |
|---|---|
| reject_rename | 56 |
| confirm_rename | 4 |
| recover_match | 1 |
| split | 0 |
| merge | 0 |
| **total** | **61** |

All 60 `suggested_rename` pairs adjudicated (4 confirm + 56 reject); 1 additional
`recover_match` from the residual lists.

## Headline finding: the matcher's DOJ pairings are essentially noise

DOJ contributed 45 of the 60 `suggested_rename` pairs. Of those, only **3**
hold up (confirms: Drone Technology, ThomsonReuters CLEAR legal research,
Procurement Data Synthesis tool). The other 42 are reject. The fuzzy matcher
paired DOJ rows on weak name-token overlap with no narrative continuity —
e.g. `Airship` (video surveillance) → `Palantir`; `DocketScope` (comment
dedup) → `Adobe Photoshop`; `Grammarly` → `Diagram Creation`; `PATTERN`
(recidivism risk) → `Smartphone OS features`.

Root cause: DOJ re-architected its entire 2025 filing. DEA submitted ~9
identical generic "Data & Analytics Tools: Publicly-Available N" rows in
2024 and a different generic FBI catalog in 2025 ("Faster FBI operations"
boilerplate). EOIR and the litigating divisions filed brand-new
E.O.-14179/M-25-21-styled initiatives. There is little true 1:1 lineage to
recover; the 2024→2025 relationship is a wholesale rewrite, not renames.

## State: every suggested_rename is a reject

All 11 State pairs are reject. Each 2024 row carries the explicit text
"This project is retired" / "This was retired" — they are genuinely dead
pilots (deepfake detector, topic modeling, Louvain community detection,
forecasting, etc.). The matcher paired each retired pilot with an unrelated
live 2025 use case on shallow name overlap (e.g. retired `Forecasting` →
`FA.gov RedactAid`). No lineage exists.

## Confirms (4)

- **DOJ Drone Technology → Autonomous Drone Detection and Monitoring** —
  near-verbatim narrative; same DEA autonomous-navigation use case.
- **DOJ ThomsonReuters CLEAR → AI-powered Legal Research** — same AI legal
  research; 2025 narrative explicitly says it builds on Westlaw/Lexis
  subscriptions. A genuine rename/rollup.
- **DOJ Data & Analytics procurement tool → Procurement Data Triage Tool** —
  same procurement-data categorization tool; 2024 name carries the matching
  procurement ID. Medium confidence (terse narratives).
- **EPA ML-assisted literature screening → Living Literature Review** — same
  reference-ranking screening system; 2025 expanded the NAAQS context.

## Recovery (1)

- **DOJ `doj-jaws` → `doj-jaws-text-to-speech-assistant-for-accessibility`** —
  a clean matcher miss. Same JAWS text-to-speech accessibility product, same
  audio-description/text-summary outputs; only the 2025 name was lengthened.
  Both rows sat as `retired_2024` / `new_2025`.

## USAID — correctly all retired

USAID filed 137 use cases in 2024 and zero in 2025 (agency dismantled; DB
confirms 0 rows in `use_cases`). All 137 `retired_2024` USAID rows are
genuine retirements — no recovery attempted, per charter instruction.

## No splits or merges

I checked the DOJ residual for split/merge candidates. DOJ's 2025 generic
rows ("Optical Character Recognition Tool 1/2/3", "Redaction Tool 1/2",
multiple chatbots) superficially look like they could be splits of 2024
generic rows, but the narratives are too thin and generic ("Faster FBI
operations", "Text") to establish bilateral evidence that a *specific* 2024
use case became *specific* 2025 ones. Charter principle 2 requires real
bilateral narrative evidence; none of the DOJ N:M candidates clear that bar,
so no split/merge decisions were emitted.

## Low-confidence flags

The DEA "Data & Analytics Tools: Publicly-Available N" rejects (pairs
6–15) are marked `medium` — the 2024 rows are nine near-identical generic
templates, so while no individual pairing is defensible, it is conceivable
one of these generic 2024 rows loosely underlies a 2025 successor. I
rejected all on the absence of distinguishing narrative continuity.
`doj-goblin` was rejected at medium confidence because its 2025 narrative
is empty (no evidence either way).

## Pairs I could not fully resolve

None left unresolved — all 60 adjudicated. The only genuine uncertainty is
the cluster of medium-confidence DEA generic-template rejects noted above.
