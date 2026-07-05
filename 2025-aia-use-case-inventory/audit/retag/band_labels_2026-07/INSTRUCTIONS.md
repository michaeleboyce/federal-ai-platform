# Band labels 2026-07 — who does each license band count?

## What this is

The consolidated inventory's `Estimated # of Licenses/Users` band is the
only workforce-scale signal in the 2025 inventory, and the dashboard's
seat estimates were summing it naively — counting the same employees once
per task row, counting CrowdStrike endpoints and Google Maps users as "AI
seats," and producing agency totals 10–25× the actual workforce. This pass
labels every banded row with WHO (or what) the band counts, so the seat
model can aggregate honestly. 58 rows with 10,000+ bands carry 81% of all
seat mass — treat every row as if it will be quoted in an IFP article,
because it will.

`input_batch<N>.csv` has one row per banded consolidated use case:
the use-case narrative (`ai_use_case`), the product string as the agency
wrote it (`commercial_product`, `commercial_examples`), the canonical
products already linked (`linked_products`, `linked_product_types`), the
band, and the agency's total headcount for plausibility checks.

## Labels (all four required per row)

### 1. `unit_counted` — what the number counts
- `employees` — federal staff seats/accounts (the default reading when the
  product is a workplace tool and nothing suggests otherwise).
- `employees_and_contractors` — narrative or agency context says on-site
  contractors are included. Use when band > agency headcount AND the agency
  is known to run a large contractor workforce (DOE labs, NASA centers),
  or the text says "workforce" at a contractor-heavy agency.
- `devices_endpoints` — the number is devices, endpoints, licenses-per-
  machine: security agents (CrowdStrike, Defender), MDM, phone features.
- `public_users` — members of the public: public-facing chatbots, benefit
  portals, consumer map apps used by travelers.
- `applicants_cases` — the band counts applications, cases, or documents
  processed, not people with access.
- `unknown` — genuinely can't tell. Prefer this + `low` confidence over
  guessing.

### 2. `population` — which people (only meaningful for employee-ish units)
- `all_staff` — the whole agency workforce plausibly has access
  (enterprise chat rollout, M365 tenant-wide feature).
- `office_staff` — desk/knowledge workers but not field/clinical/
  operational staff (most "drafting documents with Copilot" rows).
- `occupation:<x>` — a specific occupation. Use the closed vocabulary
  where it fits: `occupation:attorneys`, `occupation:developers`,
  `occupation:agents_investigators`, `occupation:clinicians`,
  `occupation:comms`, `occupation:data_scientists`. A free-tail value is
  allowed when none fits — explain in reasoning.
- `single_component` — one bureau/office, not occupation-defined.
- `unknown`.
For `devices_endpoints` / `public_users` / `applicants_cases` rows, set
population to `unknown` unless the narrative is explicit.

### 3. `org_scope`
- `enterprise` — agency-wide deployment.
- `component` — one bureau/sub-agency (the `bureau` column is a strong
  hint but agencies file inconsistently — read the narrative).
- `unknown`.

### 4. `stratum` — which seat-model population stratum the row belongs to
Default from the linked product types, but THE POPULATION OVERRIDES THE
PRODUCT: Azure OpenAI powering an eDiscovery workflow is `legal`, not
`general`, even though `azure openai` is a general_llm product.
- `general` — general-purpose chat/productivity AI available for arbitrary
  prompts (ChatGPT, Gemini, M365 Copilot, Claude, agency chat tools,
  document drafting/summarizing tasks).
- `technical` — developers/data folks: coding assistants, ML platforms,
  data-analytics AI.
- `legal` — attorneys/legal staff: legal research, eDiscovery.
- `investigative` — agents/investigators: investigative data, forensics.
- `comms` — public affairs: media monitoring, social listening, creative
  suites used by comms shops.
- `clinical` — clinicians: ambient scribes, clinical decision support.
- `excluded_not_seats` — the row shouldn't count toward ANY person-seat
  stratum: security endpoints, biometric door locks, consumer map apps,
  public chatbots, document-processing pipelines with no human "seat."
  (`devices_endpoints`/`public_users`/`applicants_cases` rows are almost
  always `excluded_not_seats`.)

## Worked examples

1. EPA — "Generating first drafts of documents…" / "Azure OpenAI,
   Microsoft365 Copilot" / band 10,000-50,000, headcount 16,000 →
   `employees, all_staff, enterprise, general`, high. The band spans the
   whole workforce; it's a general chat/drafting deployment.
2. DOE — "Managing or implementing security controls…" / "CrowdStrike
   Falcon, Microsoft Defender" / 10,000-50,000 → `devices_endpoints,
   unknown, enterprise, excluded_not_seats`, high. Endpoint agents, not
   people with an AI tool.
3. DOE — "Planning travel routes using AI-driven map applications" /
   "Google Maps, Apple Maps" / 50,000+ → `public_users` (or `employees`
   if you read it as staff phones — either way) + `excluded_not_seats`,
   medium. Consumer ambient AI is not an AI seat.
4. DHS — "AI-Assisted eDiscovery Search" / Relativity-ish / 1001-5000 →
   `employees, occupation:attorneys, component, legal`, medium.
5. DOE — band 10,000-50,000 at a 16,000-headcount agency where the row
   says "NNSS-Microsoft 365" → `employees_and_contractors` (lab/site
   contractors), `all_staff`, `enterprise`, `general`; note the contractor
   read in reasoning.

## Plausibility discipline

Always compare the band to `agency_total_headcount`. A band whose LOWER
bound exceeds the agency's headcount CANNOT be `employees`-only — it is
contractors-inclusive, devices, public, or cases. Say which and why.

## Output

Write `labels_<your-batch>.csv` (e.g. `labels_batch3.csv`) to this
directory with EXACTLY these columns, keyed by `slug` (never invent
numeric ids):

slug,agency,ai_use_case,unit_counted,population,org_scope,stratum,confidence,reasoning

- confidence ∈ {high, medium, low}
- reasoning: 1–2 sentences quoting the phrase that decided it, and noting
  the headcount comparison when it drove the call.

Every input row must appear exactly once in your output. Optional web
search (agency press releases, FedScoop) where a named system is
ambiguous; put the URL in reasoning if used.
