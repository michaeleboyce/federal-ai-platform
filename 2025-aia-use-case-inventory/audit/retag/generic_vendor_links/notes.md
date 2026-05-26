# Generic Vendor-Links Retag Pass — Methodology

## What "vendor-as-product" means in this catalog

The `products` table has rows where `LOWER(TRIM(canonical_name)) = LOWER(TRIM(vendor))` — i.e., the
product's name is literally identical to its vendor's name (e.g. `Microsoft / Microsoft`, `Adobe / Adobe`).
There are 96 such "placeholder" products. They fall into two very different camps:

1. **single_product** — the company effectively IS its flagship product. Grammarly, Clearview AI,
   ID.me, Asana, Zoom, Canva, Synthesia, Hyperscience, Wiz, BioRender, etc. For these, the placeholder
   row is a fine canonical product — no retag warranted.
2. **enterprise** — multi-product company where the bare-vendor row is a *catch-basin* absorbing edges
   from any source entry whose `vendor_name` field is just the company name. The actual product
   mentioned in source text is usually more specific (Azure, M365 Copilot, Acrobat, AWS Bedrock,
   Westlaw, Lexis+, etc.). These edges should be redirected to the right specific product.

## Classification rule

A placeholder was tagged **enterprise** if either:

- The vendor appears on the explicit enterprise list (Microsoft, Google, Amazon, Adobe, Splunk,
  Thomson Reuters, LexisNexis — per task spec); OR
- The vendor has at least one *other* product in the catalog (i.e. a sibling row where
  `vendor = <vendor>` and `id != <placeholder id>`). Examples picked up by this rule: Cisco,
  ServiceNow, Salesforce, Veritone.

Everything else is **single_product**. 11 enterprise placeholders, 85 single-product placeholders.

See `placeholder_products.md` for the full classified list with reasoning per row.

## Candidate CSV

`by_row.csv` (268 edges) has one row per `use_case_products` or `consolidated_use_case_products`
edge whose `product_id` is one of the 11 enterprise placeholders. Schema:

```
use_case_id, entry_kind, agency, use_case_name, current_product_id, current_product_name,
vendor_name, system_name, problem_statement, expected_benefits, system_outputs,
training_data_description, regex_hint, proposed_action, proposed_product_id,
proposed_product_name, confidence, evidence_quote, notes
```

`entry_kind` is `use_case` or `consolidated`. For consolidated rows, `vendor_name` ← `commercial_product`,
`system_name` ← `commercial_examples`, `problem_statement` ← `agency_uses`; other source-text columns
are empty (not present in the consolidated schema).

All values written via `csv.QUOTE_ALL` so multiline `problem_statement` text survives Excel/pandas round-trips.

## `regex_hint` heuristic and limits

The `regex_hint` column is a non-binding clue to slice agents: a `;`-joined list of lowercased
keywords detected by word-boundary regex on the concatenation of the source-text fields. Per-vendor
hint lists (e.g. for Microsoft: `azure`, `copilot`, `365`, `teams`, `office`, `outlook`, `power bi`,
`power platform`, `sentinel`, `purview`, `dynamics`, `viva`, `gpt`, `openai`, `github copilot`).
90 / 268 rows (~34%) have at least one hint match.

Limits the slice agents should be aware of:

- Hints are *suggestive*, not authoritative — `clear` matches both Thomson Reuters CLEAR and the
  generic English word; `target` matches both Adobe Target and ordinary "target audience" prose.
- An empty `regex_hint` does NOT mean "leave alone" — many source entries describe the product only
  obliquely or by use, not by named product (e.g. "secure email gateway" without saying "Microsoft
  Defender"). Slice agents must still read the full source text.
- Multi-hint rows (e.g. `azure;openai`) are common for Azure OpenAI deployments — usually disambiguate
  to `Azure OpenAI` (the joint named product) rather than separately to Azure + OpenAI.

## What slice agents do next

Slice agents (a/b/c/d, partitioned cleanly by current placeholder product) will fill in:

- `proposed_action`: typically `retag` (move edge to a specific product) or `keep` (placeholder is
  fine; source text genuinely refers to the company at the enterprise level — e.g. an MOU mentioning
  "Microsoft" generically).
- `proposed_product_id`, `proposed_product_name`: the specific catalog product to retag to. Slice
  agents resolve these by name from the catalog, since IDs can shift across `make fix` runs.
- `confidence`: high / medium / low.
- `evidence_quote`: the smallest snippet of source text that justifies the retag (e.g. "uses Azure
  OpenAI's GPT-4o").
- `notes`: free-form (e.g. "vendor field says 'Microsoft' but system_name = 'Sentinel SIEM'").

## Useful named products already in the catalog (for slice agents)

(Resolve by `canonical_name`; IDs will drift across rebuilds.)

- **Microsoft family**: Microsoft Azure Platform, Azure OpenAI, Azure AI Document Intelligence,
  Azure AI Foundry, Azure AI Translator, Azure Data Factory, Azure Speech, Azure Synapse Analytics,
  Microsoft 365, Microsoft 365 Apps for Enterprise, Microsoft 365 Copilot, Microsoft 365 Copilot Chat,
  Microsoft AI Builder, Microsoft Copilot Studio, Microsoft Copilot for Security, Microsoft Defender,
  Microsoft Discovery, Microsoft Dynamics 365, Microsoft Edge, Microsoft Exchange Server,
  Microsoft HoloLens, Microsoft OneDrive, Microsoft OneNote, Microsoft Outlook, Microsoft Power BI,
  Microsoft Power Platform, Microsoft PowerPoint, Microsoft Project, Microsoft Purview,
  Microsoft Purview eDiscovery, Microsoft Sentinel, Microsoft Skype, Microsoft Teams, Microsoft Viva,
  GitHub Copilot, Microsoft Search in Bing, SQL Server Management Studio, Visual Studio,
  Visual Studio Enterprise.
- **Google family**: Gemini, Google Agentspace, Google Calendar, Google Chrome Generative AI,
  Google Cloud Platform, Google Cloud Vision, Google Colab, Google Coral TPU, Google Earth Engine,
  Google Lens, Google Maps, Google Pixel, Google Translate, Google Vertex AI, Google Workspace,
  NotebookLM, reCAPTCHA.
- **Amazon family**: AWS Bedrock, AWS Kendra, AWS Lex, AWS Rekognition, AWS Textract, AWS Transcribe,
  Amazon Alexa, Amazon CodeWhisperer, Amazon Comprehend, Amazon Q, Amazon SageMaker, Amazon Web Services.
- **Adobe**: Adobe Creative Cloud Suite, Adobe Firefly, Adobe Photoshop, Adobe Premiere Pro, Adobe Sensei.
- **Thomson Reuters**: CoCounsel, ProLaw, Thomson Reuters CLEAR, Westlaw AI.
- **LexisNexis**: Lexis+ AI, Lexis+ Protege, LexisNexis Risk Solutions, NexisXplore.
- **Cisco**: Cisco Identity Services Engine, Cisco Secure Network Analytics.
- **ServiceNow**: ServiceNow IT Operations Management (ITOM) Predictive AIOps, ServiceNow Now Assist.
- **Salesforce**: Salesforce Einstein, Slack, Tableau.
- **Veritone**: Veritone Illuminate.
- **Splunk**: (no siblings yet — slice agent may need to surface "Splunk Enterprise Security",
  "Splunk SOAR", or "Splunk Observability" as proposed new products if source text warrants).

## Apply scope

This is a one-time audit. Once slice agents finish, a downstream apply script will:

1. Read the populated `by_row.csv` and `slice_*.csv` files.
2. Re-resolve `proposed_product_name` to current IDs.
3. Move edges from the placeholder product to the proposed product (or create the product first if
   needed).
4. Bake the corrections into `make fix` (probably via an additive seed or a follow-up
   `scripts/retag_generic_vendor_links.py`) so the corrections persist across future rebuilds.

## CRITICAL implementation notes for the apply script and Validator

Two findings discovered mid-flight that the downstream stages MUST respect. The Validator should
flag any proposal that violates them; the apply script must encode both.

### 1. DB `confidence` vocabulary is `('strong', 'inferred')` — NOT high/medium/low

The CSV `confidence` column is the **agent's confidence in its own proposal** and drives the
high/medium/low **apply gating policy** (`apply_retag_audit.py`-style: only apply
high/medium proposals). It is NOT the value written to the DB.

The DB columns `use_case_products.confidence` and `consolidated_use_case_products.confidence` both
declare `CHECK(confidence IN ('strong', 'inferred'))`. Writing anything else silently violates the
constraint and drops the row (this exact bug just bit `apply_linkage_pass_2026_05.py`; see commit
`400badb` from 2026-05-25 23:12). The apply script must translate:

| CSV `proposed_action`   | CSV `confidence`     | Effect on DB row                                         |
|-------------------------|----------------------|----------------------------------------------------------|
| `relink`                | `high` or `medium`   | UPDATE … SET product_id=<new>, confidence='strong'       |
| `relink`                | `low`                | (SKIP — stays in CSV for human review)                   |
| `delete_or_inferred`    | `high` or `medium`   | UPDATE … SET confidence='inferred' (edge stays, downgrade only) |
| `delete_or_inferred`    | `low`                | (SKIP)                                                   |
| `keep_strong`           | (any)                | no-op (already strong)                                   |

Current distribution at slice-agent time (for sanity-check deltas):

```
use_case_products:        strong=1647, inferred=69
consolidated_use_case_products: strong=667,  inferred=12
```

### 2. Re-resolve product IDs at apply time — do NOT trust CSV `proposed_product_id`

Product IDs are not stable across `make fix` runs. `load_inventories.py` and downstream rebuild
steps rotate `products.id` (Foundation observed Microsoft's id flip from 18253 → 19027 → 19801
during this session alone). Same applies to `use_cases.id` — see `400badb`.

The apply script MUST:

- Re-resolve `current_product_id` from `current_product_name` (the placeholder canonical name) at
  apply time. If the name no longer resolves uniquely → abort with an error, do not guess.
- Re-resolve `proposed_product_id` from `proposed_product_name`. If the name doesn't resolve → log
  and SKIP the row (do NOT write a stale ID).
- Re-resolve `use_case_id` / `consolidated_use_case_id` via the
  `build_old_id_to_signature` / `build_signature_to_new_id` pattern already used by
  `scripts/apply_linkage_pass_2026_05.py` (post-`400badb`). Signature columns:
  `(agency_id, source_file, use_case_name)` for use_cases; analogous for consolidated.

The CSV's `use_case_id` column is the id **as of slice-agent run-time**; treat it as a hint, not as
authoritative.

### 3. Snapshot at slice-agent run-time (2026-05-25 ~23:11)

Captured here so the Validator can compute expected deltas after apply:

```
Microsoft:        id=19801, 141 edges  (target: ~73 inferred after retag)
Google:           id=19802,  55 edges
Amazon:           id=19803,  15 edges
Adobe:            id=19797,  18 edges
Splunk:           id=19061,  12 edges  (all likely → delete_or_inferred; no Splunk siblings in catalog)
Thomson Reuters:  id=19796,  11 edges
LexisNexis:       id=19365,   8 edges
Veritone:         id=19176,   5 edges
Cisco:            id=19799,   3 edges
ServiceNow:       id=19798,   0 edges
Salesforce:       id=19800,   0 edges
                            ----
                            268 edges total
```
