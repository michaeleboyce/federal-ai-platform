# Recoding Maps — Source-Value Aliases

For each multiple_choice and select_multiple column, this file lists the **alias strings** seen in agency filings that fold to each canonical value. Use this when:

- You encounter a non-canonical value in source data and want to know whether it's a known alias or genuinely unmapped.
- You're writing data-load logic that needs to be tolerant of agency formatting variants.

The aliases below come from OMB's published recoding map for the 2025 inventory plus our own load-time observations (`load_inventories.py`). New unmapped variants surface in audit work — when you find one, decide whether it belongs in an existing canonical bucket and update this file accordingly.

---

## `is_withheld`

| Canonical | Aliases seen |
|---|---|
| `a) No` | `No` |
| `b) Yes – agency has determined that there's a risk to disclosure, such as a harm to an interest protected by a FOIA exemption` | `Yes – agency has determined that there's a risk to disclosure, such as a harm to an interest protected by a FOIA exemption` |
| `c) Yes – disclosure is prohibited by law` | `Yes – disclosure is prohibited by law"` (trailing quote — OMB typo) |
| `d) Other` | `Other` |

---

## `development_stage`

The most-recoded column. Agencies file all manner of casing, punctuation, and legacy-2024-format variants.

| Canonical | Aliases seen |
|---|---|
| `a) Pre-deployment – The use case is in a development or acquisition status.` | `pre-deployment - the use case is in a development or acquisition status`, `pre-deployment`, `Acquisition and/or Development`, `a) a) Pre-deployment – The use case is in a development or acquisition status.` (double-prefix), `a) Pre-deployment ñ The use case is in a development or acquisition status.` (encoding glitch: `ñ` should be em-dash) |
| `b) Pilot – The use case has been deployed in a limited test or pilot capacity.` | `b)  Pilot – The use case has been deployed...` (double-space after `b)`), `b)  b)  Pilot – ...` (double-prefix double-space), `pilot - the use case has been deployed in a limited test or pilot capacity`, `pilot`, `Initiated`, encoding-glitch `ñ` variant |
| `c) Deployed – The use case is being actively authorized or utilized to support the functions or mission of an agency.` | `c)  Deployed – ...`, `deployed - the use case is being actively authorized...`, `deployed`, `Operation and Maintenance`, encoding-glitch `ñ` variant |
| `d) Retired – The use case was reported in the agency's prior year's inventory, but its development and/or use has since been discontinued.` | `d) Retired – The use case was reported in the agency's prior year's inventory, but its development and/or use has since been discontinued.` (curly apostrophe variant), `retired`, encoding-glitch `agencyís`/`yearís`/`ñ` variants |

---

## `is_high_impact`

| Canonical | Aliases seen |
|---|---|
| `a) High-impact` | `High-impact`, `yes` |
| `b) Presumed high-impact, but determined not high impact` | `Presumed high-impact, but determined not high impact`, `b) Presumed high-impact but determined not high-impact` (no comma) |
| `c) Not high-impact` | `Not high-impact`, `no` |

---

## `topic_area`

This column has the broadest fuzzy-matching because agencies often invent finer-grained topics. The OMB-canonical bucket each one folds to:

| Canonical | Aliases seen (agency-filed finer-grained topics) |
|---|---|
| `Energy and the Environment` | `Energy & the Environment` |
| `Health and Medical` | `Health & Medical` |
| `Procurement and Financial Management` | `Procurement & Financial Management` |
| `Cybersecurity` | `Cybersecurity Operations` |
| `Administrative Functions` | `Internal Knowledge Management & Staff Support`, `Admin Functions` |
| `Service Delivery` | `Communications & Public Affairs`, `Strategic Planning & Policy Analysis`, `Customer Service & Public Engagement`, `Audit, Compliance & Risk Management`, `Employee Productivity & Collaboration`, `Business Development & Technical Assistance`, `Loan Program Operations`, `Records Management`, `This potentially crosses all EPA business lines`, `eDiscovery matters` |
| `Information Technology` | `Software Development & Engineering`, `IT Operations & Infrastructure Management`, `Data Analytics & Business Intelligence` |
| `Other – Economic & Financial` | `Other  – Economic & Financial` (double-space) |

---

## `classification`

| Canonical | Aliases seen |
|---|---|
| `Agentic AI: AI systems that perform tasks or make decisions autonomously with minimal human intervention.` | `Agentic AI`, `agentic-ai` |
| `Classical/Predictive Machine Learning: ...` | `Classical/Predictive Machine Learning`, `Machine Learning`, `Machine Learning (Classification/Prediction)`, `Classical ML`, `Intelligent Automations (AIOps)`, `Intelligent Automation (AIOps)` |
| `Computer Vision: AI that processes and interprets visual data (e.g., images and videos).` | `Computer Vision`, `Computer Vision - AI that processes and interprets visual data (e.g.; images and videos).` (semicolon variant) |
| `Generative AI: AI that generates new or synthetic content (e.g., images, videos, audio, text, code).` | `Generative AI`, `Gen AI`, `GenAI`, `Generative AI; Natural Language Processing (NLP)` (compound — fold to GenAI as primary), `AI-Enabled Application` |
| `Natural Language Processing: AI that processes, interprets, and shares information in human language.` | `Natural Language Processing (NLP)`, `Natural Language Processing`, `NLP` |
| `Reinforcement Learning: AI trained through trial and error using rewards and penalties to optimize decision-making policies.` | `Reinforcement Learning` |

---

## `contracting_usage`

| Canonical | Aliases seen |
|---|---|
| `a) Purchased from a vendor` | `Purchased from a vendor` (×2 in source — once with double-space artifact), `vendor`, `Exclusively developed with contract/external resources.`, `Vendor Purchased`, `a)ÝPurchased from a vendor` (encoding glitch — Ý should be space), `Developed with contracting resources.` |
| `b) Developed in-house` | `Developed in house`, `In-house Development` (×2), `Developed in-house`, `in house`, `in-house`, `No contract/external resources used in development.` |
| `c) Developed with both contracting and in-house resources` | `Developed with both contracting and in-house resources` (×2), `in house and contractor`, `in house & contractor`, `Developed with a combination of in-house and contract/external resources.`, `Both, the AI was developed by a vendor but it was substantially customized in-house or by a contractor`, `Contracting and In House` |

---

## `have_ato`

| Canonical | Aliases seen |
|---|---|
| `Yes` | `true`, `yes`, `Use vendor's ATO or FedRAMP authorization`, `In-progress - ATO process underway` |
| `No` | `false`, `no` |

---

## `has_pii`

| Canonical | Aliases seen |
|---|---|
| `Yes` | `b) Yes`, `true`, agency-narrative substitutions like `Yes (incidental PII may be involved through authenticated platform users)`, `Yes - System logs may contain user identifiers`, `Yes - Employee names and communications`, `Yes - Customer contact and account information`, `Yes - Loan applicant and business owner PII`, `Yes - Business and individual information in audit records` |
| `No` | `a) No`, `false`, `No - General content generation and research`, `Depends on data sources analyzed`, `No - Code and technical documentation only` |

**Note:** When an agency provides narrative qualifications like "Yes (incidental PII)" or "Depends on data sources", the recoded value loses that nuance. Original text remains in the source CSV; check `raw_json` if you need the full annotation.

---

## `has_custom_code`

| Canonical | Aliases seen |
|---|---|
| `Yes` | `true` |
| `No` | `false` |

---

## `demographic_features` (select_multiple)

| Canonical | Aliases seen |
|---|---|
| `a) Race/Ethnicity` | `a) Race/Ethnicity`, `race`, `ethnicity`, `race / ethnicity` |
| `b) Sex` | `Sex`, `sex/gender`, `Sex/Gender` |
| `c) Age` | `Age` |
| `d) Religious Affiliation` | `Religious Affiliation` |
| `e) Socioeconomic Status` | `Socioeconomic Status` |
| `f) Ability Status` | `Ability Status` |
| `g) Residency Status` | `Residency Status` |
| `h) Marital Status` | `Marital Status` |
| `i) Income` | `Income`, `l) income` (mis-prefix) |
| `j) Employment Status` | `Employment Status` |
| `k) None of the above` | `None of the above`, `None`, `na`, `n/a`, `not applicable` |
| `l) Other` | `Other`, `I) Other` (capital-I instead of lowercase-l), `i) other` (mis-prefix) |

---

## `hi_testing_conducted`, `hi_assessment_completed`

Both columns share the same 3-option enum and use the same aliases:

| Canonical | Aliases seen |
|---|---|
| `a) Yes` | `Yes` |
| `b) In-progress` | `In-progress` |
| `c) Agency CAIO has waived this minimum practice and reported such waiver to OMB` | `waived`, `Agency CAIO has waived this minimum practice and reported such waiver to OMB` |

---

## `hi_independent_review`

| Canonical | Aliases seen |
|---|---|
| `a) Yes – by another appropriate agency office or reviewer not directly involved in the AI's development` | `yes – by another appropriate agency office or reviewer not directly involved in the ai's development` (lowercased) |
| `b) Yes – by an agency AI oversight board not directly involved in the AI's development` | `Yes – by an agency AI oversight board not directly involved in the AI's development` |
| `c) Yes – by the CAIO` | `Yes – by the CAIO` |
| `d) In-progress` | `In-progress` |
| `e) Agency CAIO has waived this minimum practice and reported such waiver to OMB` | `waived`, `Agency CAIO has waived this minimum practice and reported such waiver to OMB` |

---

## `hi_ongoing_monitoring`

| Canonical | Aliases seen |
|---|---|
| `a) Yes, sufficient monitoring protocols have been established` | `Yes, sufficient monitoring protocols have been established`, `yes` |
| `b) Development of monitoring protocols is in-progess` (sic — preserves OMB typo) | `Development of monitoring protocols is in-progess`, `Development of monitoring protocols is in-progress` (correctly spelled), `in-progress` |
| `c) Agency CAIO has waived this minimum practice and reported such waiver to OMB` | `Agency CAIO has waived this minimum practice and reported such waiver to OMB`, `wavied` (sic — typo seen in agency filings) |

---

## `hi_training_established`

| Canonical | Aliases seen |
|---|---|
| `a) Yes, sufficient and periodic training has been established` | `Yes, sufficient and periodic training has been established`, `yes` |
| `b) Establishment of sufficient and periodic training is in-progress` | `Establishment of sufficient and periodic training is in-progress`, `in-progress` |
| `c) Agency CAIO has waived this minimum practice and reported such waiver to OMB` | `Agency CAIO has waived this minimum practice and reported such waiver to OMB`, `waived` |

---

## `hi_failsafe_presence`

| Canonical | Aliases seen |
|---|---|
| `a) Yes` | `yes` |
| `b) Not applicable` | `n/a`, `NA`, `not applicable` |
| `c) In-progress` | `In-progress` |
| `d) Agency CAIO has waived this minimum practice and reported such waiver to OMB` | `waived`, `Agency CAIO has waived this minimum practice and reported such waiver to OMB` |

---

## `hi_appeal_process`

| Canonical | Aliases seen |
|---|---|
| `a) Yes, an appropriate appeal process has been established` | `Yes`, `Yes, an appropriate appeal process has been established` |
| `b) Not applicable` | `n/a`, `NA`, `not applicable` |
| `c) Establishment of an appropriate appeal process is in-progress` | `In-progress`, `Establishment of an appropriate appeal process is in-progress` |
| `d) Law, operational limitations, or governmentwide guidance precludes an opportunity for an individual to appeal` | `Law, operational limitations, or governmentwide guidance precludes an opportunity for an individual to appeal`, `precluded` |
| `e) Agency CAIO has waived this minimum practice and reported such waiver to OMB` | `Agency CAIO has waived this minimum practice and reported such waiver to OMB`, `waived` |

---

## `hi_public_consultation` (select_multiple)

| Canonical | Aliases seen |
|---|---|
| `a) Direct usability testing` | `Direct usability testing` |
| `b) General solicitations of feedback and comments from the public` | `General solicitations of feedback and comments from the public` |
| `c) Public hearings or meetings ` (trailing space in source) | `Public hearings or meetings ` |
| `d) Other` | `Other` |
| `e) In-progress` | `In-progress` |
| `f) Agency CAIO has waived this minimum practice and reported such waiver to OMB` | `Agency CAIO has waived this minimum practice and reported such waiver to OMB`, `waived` |

---

## Patterns to recognize across columns

When you encounter a value not in any alias table above, check first whether it matches one of these systemic patterns:

- **Encoding glitches** — `ñ` (U+00F1) instead of `–` (em dash, U+2013), `ís` instead of `'s`, `Ý` instead of a non-breaking space. These come from cp1252-vs-UTF-8 collisions during agency export. The data is structurally fine; the recoding map normalizes them.
- **Letter-prefix double-up** — `a) a) Pre-deployment` instead of `a) Pre-deployment`. Common when an agency adds a prefix to a value that OMB already prefixed.
- **Lowercase variants** — `yes`/`no`/`in-progress` lowercased throughout. OMB normalizes these.
- **Boolean substitutions** — `true`/`false` filed in fields that take `Yes`/`No`. Map to canonical.
- **Narrative qualifications** — `Yes - <agency-specific elaboration>`. Strip elaboration; map to `Yes`. Original elaboration stays in `raw_json`.
- **Agency-specific topic names** — finer-grained topic_area values that need to fold to OMB buckets. See the `topic_area` table above.
- **Multi-bureau strings in `agency_bureau`** — pipe-delimited (`OWCP||VETS||WHD`), comma-delimited (`CAIO, NETT`), forward-slash-prefixed (`HHS/CDC`), parenthetical-suffixed (`PNNL - Pacific Northwest National Laboratory (SC43 OIM)`), department-prefixed (`Department of Justice / FBI`). Each agency has a distinct convention; see `scripts/backfill_bureau_orgs.py` for the parsers.
