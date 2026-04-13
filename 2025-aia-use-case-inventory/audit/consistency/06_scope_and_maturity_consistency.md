# Check
Scope and maturity consistency for `deployment_scope`, `is_enterprise_wide`, and stage interpretation.

# Method
- Reviewed `use_cases`, `consolidated_use_cases`, `use_case_tags`, `agencies`, and the source signals in `bureau_component`, `scope_detail`, `agency_uses`, `estimated_licenses_users`, and `stage_of_development`.
- Looked for systematic over- or under-assignment, not just isolated row-level oddities.
- Compared enterprise-wide flags against explicit agency-wide wording, bureau-specific wording, and license/user-count signals.

# Findings
- The clearest issue is over-assignment of `enterprise_wide` in `consolidated_use_cases`. There are 192 consolidated rows total, 111 are tagged `enterprise_wide`, and 29 of those are also `Agency Use (Y/N)? = N`. In practice, those rows mostly have blank user counts and read like generic product examples rather than confirmed agency-wide deployments.
- That pattern is concentrated in a small set of agencies: USTDA has 9 `enterprise_wide` rows with `agency_uses = N`, PBGC has 7, OSC has 6, FCC has 4, and CSOSA, EAC, and HUD contribute the rest. This is systematic enough to look like a tagging rule issue, not a one-off mistake.
- The use_case table shows a softer version of the same issue: 74 `enterprise_wide` rows are still `pre-deployment` or `pilot`. That is not automatically wrong, but it means the scope label is being used as an intended reach signal rather than a current operating-state signal. I did not see a comparably strong under-assignment pattern.
- Bureau detail usually keeps the tag conservative when the source is clearly local. Rows with bureau-specific scope, such as FDIC `470` (`GitHub Copilot, Appian`) or DOE lab/site entries with explicit bureau names, stay `bureau` even when the product looks broadly deployable. That makes the `enterprise_wide` overreach in the consolidated table stand out more.

# Examples
- `USTDA` `557`, `563`, `565`, `568`, and `575` are all tagged `enterprise_wide` with `Agency Use = N` and blank user counts. The source wording is generic productivity use, and `scope_detail` is only the agency name.
- `PBGC` `533` and `544` show the same pattern: `enterprise_wide`, `Agency Use = N`, no user count, and only agency-level scope detail.
- `FCC` `451` (`Searching for agency information using a knowledge retrieval system`) and `457` (`Finding and booking travel accommodations using AI-powered platforms`) are both `enterprise_wide` with `Agency Use = N`, again without user-count support.
- `CSOSA` `403` (`Finding and booking travel accommodations using AI-powered platforms`) is `enterprise_wide` with `Agency Use = N` and no user count, which is weak evidence for a whole-agency deployment.
- On the maturity side, examples like `DOJ 8533` (`Percipio Skillsoft`), `DOI 8403` (`FBMS UPC Chatbot`), and `ED 8887` (`Department-wide implementation of GSA USAi`) show that pre-deployment or pilot rows can still be labeled enterprise-wide when the source explicitly signals broad intended reach. Those look defensible, but they illustrate that the scope tag is tracking rollout intent more than current maturity.

# Recommended follow-up
- Tighten the enterprise-wide rule for consolidated rows: require explicit agency-wide wording, multi-bureau evidence, or a real user/license signal before setting `enterprise_wide = 1`.
- Treat `Agency Use (Y/N)? = N` plus blank user count as a default warning sign for enterprise-wide scope, especially on generic productivity, travel, search, and scheduling examples.
- Document the intended relationship between stage and scope so reviewers know whether pre-deployment or pilot rows can still be marked `enterprise_wide` when the source says the rollout is agency-wide or department-wide.
