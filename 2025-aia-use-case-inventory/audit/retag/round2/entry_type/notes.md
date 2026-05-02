# Round-2 Entry-Type Review — Unresolved Queue

## Inputs
- `audit/review_queue_entry_type_unresolved.csv` (228 rows, 1 header line in
  the count of 236 lines was misleading — actual data rows = 228; counted by
  `csv.DictReader`).
- DB: `data/federal_ai_inventory_2025.db` (read-only).

## Method

These rows are the residue from the prior LLM pass — the ones where the
bench reasoning was "no clear signals". Per the brief, the default action is
`keep_current` and we only flip when an objective signal in the source
record points the other way.

I built a deterministic classifier (`classify.py` in this folder) that pulls
`vendor_name`, `system_name`, `development_type`, `problem_statement`,
`system_outputs`, and `training_data_description` from the DB and then walks
a decision ladder:

0. **Multi-vendor research** — vendor field lists multiple parties + open
   source / Python libraries → `keep_current` (research code, not a product
   deployment).
1. **Rule A — explicit named product in narrative** (M365 Copilot, ChatGPT
   Enterprise, Now Assist, Bedrock, Vertex AI, Palantir, Databricks, etc.).
   Custom-app signal in `use_case_name` (acronym, "chatbot", "assistant",
   "GPT", "wrapper") OR a distinctive non-registry `system_name` →
   `bespoke_application`. Otherwise → `product_deployment`.
2. **Rule B-1 — vendor is a system integrator** (Accenture, Deloitte,
   Leidos, Booz Allen, CGI, SAIC, etc.). Default to `bespoke_application`
   (the SI built something for the agency); never `product_deployment`.
3. **Rule B-2 — vendor is a recognized product company** (Microsoft, Google,
   OpenAI, Anthropic, AWS, Palantir, ServiceNow, UIPath, Databricks,
   Snowflake, ESRI, FLIR, ThruWave, etc.). With a real custom system_name or
   a custom `use_case_name` AND an LLM/cloud API vendor → `bespoke_application`.
   Otherwise → `product_deployment`.
4. **Rule C — `development_type` says in-house and vendor blank** →
   `custom_system`.
5. **Rule D/E — vendor unknown / blank** → `keep_current` (low confidence).

I treated `system_name` values like `"R&D User"`, `"Multiple"`,
`"Redacted for cybersecurity purposes."`, `"CS-CAR-###"`, ATO/SSP plan
identifiers, and bare `"AWS"` / `"Azure"` (matching the vendor) as registry
identifiers, NOT as a custom-built wrapper signal — these are a known
artifact of the DOE submission style and should not push entries toward
`bespoke_application`.

I also distinguished **product vendors** (Microsoft, OpenAI, ServiceNow,
UIPath, etc.) from **system integrators / contractors** (Accenture, Leidos,
CGI Federal, Booz Allen, etc.). The previous mistake on round 1 was
treating SIs as commercial product vendors, which would push genuine
custom-built work into `product_deployment`.

## Outcomes

- **228 rows reviewed**.
- **6 reclassifications** (≈2.6%).
- **222 keep_current**.

The reclassification list (all → `product_deployment`):

| use_case_id | agency | name | reason |
|---|---|---|---|
| 7495 | DHS | Non-Intrusive Inspection (NII) 3D Imaging Tool | vendor=ThruWave, no system_name |
| 7890 | DOE | AI used for predictive modeling | vendor=Microsoft, no custom system name |
| 7896 | DOE | ML to parse open-source text | vendor=Microsoft, registry system_name |
| 7897 | DOE | AI for delivery parking ID | vendor=Cisco, registry system_name |
| 8606 | DOJ | Speech-to-Text Managed Service | vendor=Microsoft+OpenAI, system redacted |
| 9310 | HHS | OFR Robotics & Process Automation (ORPA) | vendor=UIPath, system=UIPath |

By target type: **6 → product_deployment**, **0 → bespoke_application**.

## Why so few reclassifications?

The unresolved queue arrived after the LLM had already made the easy calls.
What's left is mostly:

- **Small/unknown vendors with custom system names** (74 rows). These are
  almost always `bespoke_application` already, and the existing tag is
  defensible — we have no objective lever to move them.
- **Vendor blank + dev_type blank** (14 rows). No signal at all; the OMB
  template entries and similar minimum-disclosure rows.
- **"Both contracting and in-house" dev_type with no vendor** (22 rows). The
  agency is telling us they shared the build; without a named vendor we
  can't confidently call it `product_deployment`.
- **System integrators named with no LLM/API in the narrative** (21 rows).
  Already correctly tagged `bespoke_application` — the integrator built it.

## Agencies most affected

DOE accounted for 3 of the 6 reclassifications (R&D User registry pattern
hides what is actually a series of vendor-product enrollments). DHS, DOJ,
HHS account for 1 each. This matches the prior round-2 audit observation
that DOE's "R&D User" pseudo-system aggregates many genuine
`product_deployment` rows.

## Patterns / concerns

1. **`system_name` registry artifacts (DOE, FTC, DOJ).** Multiple agencies
   submit rows with `system_name` fields that are ATO/cybersecurity plan
   identifiers (`CS-CAR-###`, `Cybersecurity System Security Plan for
   ServiceNow Platform`, `Sentinel Network Services`) rather than the name
   of the AI artifact. These look like custom system names to a regex but
   are really registry pointers. We treat them as not-a-custom-wrapper.

2. **"Redacted for cybersecurity purposes."** DOJ uses this pattern for
   `system_name` whenever a real value would identify a sensitive system.
   We treat redaction as effectively absent.

3. **Multi-vendor research rows (DOI Barrier Island, DOE R&D)** list a
   contractor + a product vendor + open-source libs. These are bespoke
   research code and are already correctly tagged.

4. **Taxonomy gap — "platform tenant"-style entries.** Several FTC rows
   under `Sentinel Network Services` describe agency staff USING Azure
   Databricks / Azure ML on top of an existing FTC platform. The four-way
   taxonomy (`product_deployment` / `product_feature` /
   `bespoke_application` / `custom_system`) doesn't cleanly capture
   "agency-developed work product done inside a vendor platform." Either
   `product_feature` (extending the brief's definition) or `product_deployment`
   would fit; current `product_deployment` is defensible. Worth raising
   with the taxonomy owner.

5. **System-integrator handling.** I chose not to ever reclassify rows
   where the only commercial signal is an SI vendor (Accenture, Leidos,
   etc.) — they are contractors building bespoke work, not COTS resellers.
   This deviates from a literal reading of the brief but matches the
   semantics of the four-way taxonomy.

## No web searches

Searches were not required. All rows resolvable within the DB; ambiguous
ones default to `keep_current` per the brief. `searches.csv` is written
with header only.

## Files

- `resolved.csv` — 228 rows, decision per row.
- `searches.csv` — header only (no live searches needed).
- `classify.py` — the deterministic classifier used to produce `resolved.csv`.
