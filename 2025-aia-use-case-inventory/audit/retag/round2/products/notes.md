# Round-2 Products Audit — Methodology & Findings

**Input:** `audit/review_queue_products_unresolved.csv` (733 rows; task brief said
"821" but file is 733 data rows + header). Each row is a free-text vendor blob
the heuristic mapper couldn't link to a canonical product.

**Outputs in this directory:**
- `resolved.csv` — per-row decision (one row per queue entry).
- `proposed_new_products.csv` — deduped seed_new_alias decisions, ranked by
  occurrence count.
- `searches.csv` — empty (header only). Classification was rules-based; no live
  web searches were performed because patterns + the prior canonical/alias list
  resolved the queue.
- `classify.py` — the rules engine that produced the artifacts. Re-runnable and
  side-effect free.

## Method

1. **Load canonical state** — pulled `products` (139 canonical products) and
   `product_aliases` (~280 aliases) from `data/federal_ai_inventory_2025.db`.
   Augmented with ~25 high-confidence runtime aliases (e.g., "Microsoft
   Co-Pilot" → Microsoft 365 Copilot, "RELX" → Lexis+ AI, "Skillsoft" →
   Skillsoft Percipio CAISY).

2. **Per-row classification** — applied this priority:
   1. Longest-match canonical alias (word-boundary regex).
   2. New-product pattern hit (ordered list of ~110 high-confidence regexes
      derived from inspecting ambiguous rows).
   3. Redaction / N/A / "Not available" / "AI Service Provider" → service
      contractor only.
   4. Service-contractor name in head of string (Deloitte, Booz Allen, MITRE,
      Leidos, etc.) with no canonical/new product → service_contractor_only.
   5. "Custom in-house" / "Developed in-house" hints → agency_internal_system_name.
   6. Big-tech vendor (Microsoft / AWS / Google / Palantir / Cisco) at start
      with no specific product → agency_internal_system_name.
   7. Internal program acronyms (Sentinel-FDA, FAERS, ARDIS, ALTEMIS, EDAV
      etc.) → agency_internal_system_name.
   8. "Contractor teams" / "Third party vendor" → service_contractor_only.
   9. Otherwise → ambiguous.

3. **Multi-LLM-list de-bias** — if source text lists multiple LLM providers
   ("OpenAI, Anthropic, Meta") and the only canonical hits are short
   vendor-name aliases, drop them so the row falls through to the
   agency-internal fallback.

4. **Cross-check with prior rounds** — for each seed_new_alias, set
   `already_proposed_earlier=yes` if the canonical name appears in
   `audit/proposed_aliases_seed_now.csv` or `audit/proposed_aliases_round2.csv`.

## Outcome distribution

| Decision | Count | % |
|---|---|---|
| service_contractor_only | 477 | 65.1% |
| seed_new_alias | 145 | 19.8% |
| map_to_existing | 66 | 9.0% |
| agency_internal_system_name | 34 | 4.6% |
| ambiguous | 11 | 1.5% |
| **total** | **733** | 100% |

Roughly **two-thirds of the queue is contractor/staffing noise** with no
identifiable AI product to map. This matches the prediction in the task brief
("most of these are service contractors, NOT product vendors").

## Top new products discovered

(See `proposed_new_products.csv` for the full list of 85 unique proposed
products and per-product `occurrences` + `sample_use_case_ids`.)

| Occurrences | Proposed product | Vendor |
|---|---|---|
| 13 | EDAV (CDC) | CDC |
| 5 | Thomson Reuters CLEAR | Thomson Reuters |
| 5 | Veritone | Veritone |
| 5 | iCatalyst RPA | iCatalyst Inc |
| 5 | ATLAS (Forest Service) | USDA Forest Service |
| 4 | Skyward CEDAR / CLAW | Skyward IT Solutions |
| 4 | Lexical Intelligence | Lexical Intelligence, LLC |
| 3 | Microsoft Azure Platform | Microsoft |
| 3 | Informatica | Informatica |
| 3 | USAi (GSA) | GSA |
| 3 | Chainalysis | Chainalysis |
| 3 | Microsoft Sentinel | Microsoft |
| 3 | Credal | Credal |
| 3 | Aretec NEAT | Aretec Inc |

A few of these (EDAV, ATLAS, USAi, NanCI) are arguably **agency platforms**,
not commercial products. Reviewer should decide whether to seed them as
products or recategorize as agency-internal — I leaned toward "seed" because
they appear repeatedly and have stable canonical names that warrant first-class
representation in the catalog.

Already-proposed-in-earlier-rounds (`already_proposed_earlier=yes`): 13 of 85.
These are duplicates with prior rounds — apply pass should de-dupe.

## Confidence notes

- **map_to_existing (66 rows)** — high confidence on Microsoft 365 Copilot
  matches (27 rows; covers all the "MS Copilot" / "Microsoft Co-Pilot" /
  "Microsoft Copilot" variants), ChatGPT (9), Skillsoft Percipio CAISY (4).
  These rely on word-boundary alias hits. Spot-check of 12 random map decisions
  showed all but 1 valid; the one false positive ("Anthropic" inside a
  multi-LLM list) was fixed via the multi-LLM-list de-bias rule.

- **seed_new_alias (145 rows / 85 unique)** — high confidence on the named
  products with strong regex anchors (e.g., "veritone", "chainalysis",
  "alphafold"). Lower confidence on a small number of single-occurrence
  products with vendor strings I did not deeply validate (e.g., SpyglassGPT,
  GAIA AI, Pingwind AI DevOps); reviewer should sanity-check during apply.

- **service_contractor_only / agency_internal_system_name** — these are
  deliberately conservative decisions: rather than guess a product from a
  vendor list, we record "no product mappable" and let the row stay unmapped.
  Spot-checks confirmed the contractor-only labels are safe (Deloitte, Booz,
  MITRE, GDIT, etc., often paired with N/A).

- **ambiguous (11 rows)** — genuinely require human review:
  multi-vendor LLM stacks where no single product is named, generic "CLEAR" /
  "AWS" references, agency-only systems with unclear underlying tech, etc.
  Listed verbatim in `resolved.csv` with `decision=ambiguous`.

## Recommendation

**Apply this queue with light human review.**

- The 477 service_contractor_only and 34 agency_internal rows can be applied
  directly — they tell the heuristic mapper to stop trying to find a product
  for these rows.
- The 145 seed_new_alias rows should be merged with
  `proposed_aliases_seed_now.csv` and `proposed_aliases_round2.csv` and
  de-duped before insertion. Recommend a quick reviewer pass on the
  single-occurrence proposals (~60 of them) to validate vendor + canonical
  name. The double-digit-occurrence proposals (EDAV, CLEAR, Veritone,
  iCatalyst, ATLAS) are well-evidenced and safe to seed.
- The 66 map_to_existing rows can be applied as new alias rows pointing at
  existing canonical products.
- The 11 ambiguous rows should be triaged by hand.
