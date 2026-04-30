# Check
Reviewed `audit/review_queue_entry_type_unresolved.csv` against `AGENT_TAGGING_GUIDE.md` and the existing source-review notes.

# Method
- Defaulted to `product_deployment` when the source names a vendor/product and does not clearly show agency-built system logic.
- Kept `custom_system` only when the source is clearly in-house or vendor-blind.
- Used `bespoke_application` only when there is explicit agency-specific assembly or integration on top of vendor components.

# Findings
- Parsed queue rows: `228`.
- Final dispositions:
  - `product_deployment`: `215`
  - `custom_system`: `13`
  - `bespoke_application`: `0`
  - `needs_human_call`: `0`
- The queue is dominated by one pattern: the heuristic label says `bespoke_application`, but the source text points to a named vendor/product and the reviewer should treat it as `product_deployment`.
- The remaining rows are legitimate `custom_system` cases with no vendor signal and in-house wording.
- This queue does not need a separate human escalation bucket if the conservative rule above is applied consistently.

# Examples
- `7492` `FLIR 280 HD` -> `product_deployment` because the source names `FLIR` directly and gives no custom-build evidence.
- `7495` `Non-Intrusive Inspection (NII) 3D Imaging Tool` -> `product_deployment` because the source names `ThruWave` and the evidence reads like deployment, not an agency-built product.
- `7502` `CBP Translate` -> `product_deployment` because the source lists vendor organizations and the description is a deployed service, not a custom system.
- `7568` `CBP Careers Bot - Leo` -> `product_deployment` because `Salesforce Einstein` is named and there is no explicit source evidence of a separate custom build.
- `7405` `Smartphone Information Forensics Triage` -> `custom_system` because the row has no vendor signal and the source-review note describes it as a DHS in-house system.
- `7866` `DOE AI for Operations Center` -> `custom_system` because the source-review note shows an in-house DOE system with no commercial product anchor.
- `8766` `Determine Occupation Codes from Text (NIOCCS)` -> `custom_system` because the source-review note provides no vendor/product evidence.

# Recommended follow-up
- Treat the current queue resolution as the working rule for downstream tagging: vendor/product named plus no explicit build evidence means `product_deployment`.
- Require explicit evidence before using `bespoke_application` on future reviews.
- Leave the 13 in-house rows as `custom_system` unless a source-review pass finds a real vendor anchor.
