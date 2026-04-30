# Product Queue Review

## Check
- Reviewed `844` unresolved rows from `audit/review_queue_products_unresolved.csv` after excluding the header.
- The queue is dominated by `unmatched_vendor_text` rows (`816` rows) with only `28` `compound_string` rows.
- The recurring decision is not "is this AI?" but "is this a missing alias, a canonical product match, or an agency-specific wrapper that should stay unmapped?"

## Method
- Prioritized `compound_string` rows first, then repeated vendor/product strings, then long-tail singletons.
- Used the existing canonical product set in `federal_ai_inventory_2025.db` plus the proposed alias sample as reference context.
- Applied a conservative human-review rule:
  - `map_now` only when the row is already a clear front-door product family match.
  - `needs_alias` when the product is real and canonicalizable, but the current lookup set is missing the alias.
  - `leave_unmapped` when the text describes an internal system, agency wrapper, or mixed implementation that should not become product canon.
  - `needs_human_call` for multi-product stacks, compound vendor strings, or ambiguous agency/product phrasing.

## Findings
| Disposition | Count | Notes |
| --- | ---: | --- |
| `map_now` | 6 | Clear front-door product-family matches already explicit in the text. |
| `needs_alias` | 137 | Real vendor/product names that look canonicalizable but are missing lookup coverage. |
| `leave_unmapped` | 247 | Agency systems, wrappers, or mixed implementations that should stay out of canon. |
| `needs_human_call` | 454 | Compound stacks, multi-vendor bundles, and ambiguous rows that need a reviewer decision. |

- The queue is heavily concentrated in a few vendor families: Microsoft (`96`), NEC (`37`), Google (`28`), Deloitte (`27`), AWS (`21`), OpenAI (`12`), Guidehouse (`9`), IBM (`7`), and LexisNexis (`5`).
- The biggest semantic clusters are:
  - GenAI productivity products and product families: `ChatGPT Enterprise`, `Gemini for Google Workspace`, `Azure OpenAI`, `Copilot Studio`, `AWS Assisted Software Development`.
  - Identity / biometrics / traveler processing wrappers: `Traveler Verification Service`, `Mobile Fortify`, `IDENT`, `CBP Translate`, `DHSAuthPortal`.
  - Security / operations stacks with multiple vendors in one row: `ServiceNow`, `Tenable`, `Splunk`, `Okta`, `CrowdStrike`, `Lookout`, `Palo Alto Networks`, `Cisco Secure Network Analytics`.
- The alias gap is real, but a large share of the queue is not a lookup problem. It is an interpretation problem: the source text names a real vendor while the actual use case is an agency-owned wrapper or a multi-product implementation.

## Examples
- `map_now`
  - `918` / `7573`: `Meta, OpenAI, Google, Anthropic` for document summarization and content generation.
  - `1294` / `9146`: `Gemini for Google Workspace`.
  - `1458` / `10081`: `OpenAI ChatGPT Enterprise` and `Google Gemini for Government`.
  - `1459` / `10087`: `AWS CodeWhisperer`, `Amazon Q`, and `Bedrock` in one software-development stack.
- `needs_alias`
  - `849` / `7494`: `Clearview AI Traveler Verification System`.
  - `850` / `7495`: `ThruWave NII 3D Imaging Tool`.
  - `851` / `7496`: `Ideation ReadyAI`.
  - `853` / `7500`: `Babel Street Babel`.
- `leave_unmapped`
  - `852` / `7499`: `LMI Consulting, LLC LIGER Generative AI Toolkit` as an agency-specific toolkit wrapper.
  - `855` / `7502`: `CBP Translate` with multiple contractors named in the same row.
  - `856` / `7506`: `Traveler Verification Service` with procured devices and cameras.
  - `857` / `7507`: `NEC Traveler Verification Service` where the use case is really CBP's traveler-processing system.
- `needs_human_call`
  - `845` / `7433`: API security vulnerability technology with multiple product hits already embedded in the text.
  - `846` / `7439`: automated incident creation with `ServiceNow` / `TRM` overlap.
  - `924` / `7588`: `Illumio`, `AttackIQ`, `Cofense`, `Splunk`, `Crowdstrike`, `Polarity` in one stack.
  - `931` / `7596`: `Okta` / `AdaptiveMFA` with mixed vendor and system wording.
  - `1473` / `10138`: `ServiceNow IT Operations Management (ITOM) Predictive AIOps`.
  - `1475` / `10145`: `ServiceNow Vulnerability Response` plus `Tenable`.

## Recommended follow-up
- Seed only the alias candidates that are unambiguous commercial products or vendor families, then re-run the product lookup builder.
- Keep the `leave_unmapped` rows out of canonical product seeding; they are agency systems, not missing products.
- Use a second human pass for the `needs_human_call` bucket before any bulk remap, because that bucket contains the highest risk of collapsing distinct products into one canon row.
- Treat this queue as a coverage and interpretation backlog, not a signal that the lookup model is broken.
