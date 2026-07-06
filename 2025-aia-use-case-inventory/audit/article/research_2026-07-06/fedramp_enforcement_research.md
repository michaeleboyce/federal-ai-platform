# FedRAMP enforcement research — sourced brief

All external facts below carry a source URL and access date. Access date for
every item: **2026-07-06**. Compiled by fedramp-scout. DB work remains
read-only; this file is web research only.

---

## 1. Statutory hook — 44 U.S.C. § 3613 "Roles and responsibilities of agencies"

Source: Cornell Law School, Legal Information Institute —
https://www.law.cornell.edu/uscode/text/44/3613 (accessed 2026-07-06).
Statute enacted by the FedRAMP Authorization Act, Title LIX of the James M.
Inhofe National Defense Authorization Act for FY2023 (Pub. L. 117-263),
codified at 44 U.S.C. §§ 3607–3616.

Verbatim provisions (quoted from LII):

- **(e)(1) Presumption of adequacy:** "The assessment of security controls
  and materials within the authorization package for a FedRAMP authorization
  shall be presumed adequate for use in an agency authorization to operate
  cloud computing products and services."

- **(b) Documentation of deficiency:** "Upon completing an assessment or
  authorization activity with respect to a particular cloud computing
  product or service, if an agency determines that the information and data
  the agency has reviewed under paragraph (2) or (3) of subsection (a) is
  wholly or substantially deficient for the purposes of performing an
  authorization of the cloud computing product or service, the head of the
  agency shall document as part of the resulting FedRAMP authorization
  package the reasons for this determination."

- **(e)(2)(B) Demonstrable need (preserved authority):** "the authority of
  the head of any agency to make a determination that there is a demonstrable
  need for additional security requirements beyond the security requirements
  included in a FedRAMP authorization for a particular control
  implementation."

### Interpretation nuance (IMPORTANT for the brief — do not overclaim)

1. **§ 3613 governs the AUTHORIZATION decision, not staff enablement.** The
   presumption of adequacy is about whether Agency B may rely on an existing
   package to issue its own ATO — NOT about whether an agency must switch on
   an in-scope service (Bedrock) for employees. The DB-observed dormancy
   ("in scope of a package the agency holds" vs "staff can use it") is
   downstream of the ATO and is an internal enablement/policy choice the
   statute does not compel. Keep the statutory claim to "the law makes reuse
   / presumption of adequacy the default," not "the law requires enabling."

2. **"Demonstrable need" is a SHIELD to add controls, not a duty to decline.**
   (e)(2)(B) preserves an agency's authority to impose ADDITIONAL security
   requirements when it can show a demonstrable need — it is not a documented
   duty an agency must discharge before declining to enable a tool. The
   article premise as drafted ("CISOs decline to enable without documenting
   demonstrable need") slightly inverts the statute. Stronger framing: the
   statute puts the documentation burden on the DEVIATION — an agency that
   finds a package "wholly or substantially deficient" must put its reasons
   on the record (subsection (b)); reuse is the presumptively-adequate default.

---

## 2. 20x frontier trio — live marketplace re-check (2026-07-06)

Each listing fetched today from fedramp.gov. All three still show
**Authorizations 1 / Reuse 0**, ~5–6 months after authorization.

| Product | fedramp_id | URL | Status / level | Auth date | Auth ct | Reuse ct |
|---|---|---|---|---|---|---|
| ChatGPT Enterprise and API Platform | FR2533155773 | https://www.fedramp.gov/marketplace/products/FR2533155773/ | FedRAMP Certified, Class C (Moderate), 20x Program path | 2026-01-09 | 1 | 0 |
| Gemini for Government | FR2604952026 | https://www.fedramp.gov/marketplace/products/FR2604952026/ | FedRAMP Certified, Class B (Low), 20x Program path | 2026-01-21 | 1 | 0 |
| Perplexity Enterprise and API Platform | FR2604643715 | https://www.fedramp.gov/marketplace/products/FR2604643715/ | FedRAMP Certified, Class B (Low), 20x Program path | 2026-02-01 | 1 | 0 |

All accessed 2026-07-06. Confirms fact_sheet §7 beat 2 holds at today's date
(guardrail 11 date-stamp satisfied).

Notes:
- Product-name nuance: the FR2604643715 marketplace page renders "Perplexity
  Enterprise and API Platform" (matches DB `cso`), though press/search titles
  sometimes call it "Perplexity Enterprise Pro for Government."
- Marketplace uses "FedRAMP Certified" + "Class C/B" labels for 20x listings;
  the DB stores these as status "FedRAMP Authorized" + impact_level
  "Moderate"/"Low". Same facts, different label vocabulary — don't treat as a
  discrepancy.
- Reuse counter phrasing rule still applies: "0 recorded reuses" is the
  ledger/counter value, an upper bound on dormancy, not proof of zero adoption
  (adoption routes through OneGov/USAi, per fact_sheet beat 3).

---

## 3. GAO / oversight artifacts on reuse & post-authorization friction

- **GAO-24-106591 (2024), "Cloud Security: Federal Authorization Program
  Usage Increasing, but Challenges Need to Be Fully Addressed."** Best recent
  anchor for reuse friction. https://www.gao.gov/products/gao-24-106591 ·
  PDF https://www.gao.gov/assets/gao-24-106591.pdf · FedScoop writeup
  https://fedscoop.com/agency-fedramp-usage-increased-but-challenges-persist-watchdog-finds/
  (all accessed 2026-07-06).
- **GAO-26-107530 (2026), "Cloud Computing: Federal Government Needs to
  Address Procurement Challenges."** Six agency-reported cloud-procurement
  challenges incl. time/cost/complexity of FedRAMP authorization and vendors
  choosing not to pursue/maintain authorization.
  https://files.gao.gov/reports/GAO-26-107530/index.html · PDF
  https://www.gao.gov/assets/gao-26-107530.pdf (accessed 2026-07-06).
- **GAO-20-126 (2019/2020), "…Agencies Increased Their Use of the Federal
  Authorization [Program]…":** older baseline. 15 agencies reported not always
  using FedRAMP; some maintained their own authorization processes, making
  cross-agency reuse harder. https://www.gao.gov/assets/gao-20-126.pdf
  (accessed 2026-07-06).

These document authorization/reuse friction (the "authorize once, reuse
everywhere" premise underperforming), NOT specifically the staff-enablement
gap — no GAO artifact found that measures post-ATO enablement of in-scope
services. That downstream gap remains IFP's original contribution.

## 4. "Demonstrable need" as an enablement gate — NOT found in OMB policy

OMB M-25-21 ("Accelerating Federal Use of AI…", 2025-04-03,
https://www.whitehouse.gov/... / agency compliance plans) does not use
"demonstrable need" as a CISO enablement gate; its "high-impact AI" regime is
about rights/safety-impacting systems, not FedRAMP service enablement. The
only statutory "demonstrable need" is § 3613(e)(2)(B) (additional-controls
authority). The closest CONCRETE enablement gate in the corpus is HUD OIG's
M-25-21 compliance plan scoping Copilot to "opt-in, telemetry-logged,
non-sensitive data only" (already in audit/retag/general_llm/by_agency.md).
Recommend the article either cite § 3613 accurately or source the
"demonstrable need to decline" premise to a specific agency policy that
actually uses that language (none found in this pass).

FedRAMP reuse guidance primary sources (agency-facing):
- Agency Authorization Playbook v4.1 (2025-11-17):
  https://www.fedramp.gov/resources/documents/Agency_Authorization_Playbook.pdf
- "Reusing Authorizations for Cloud Products" quick guide:
  https://www.fedramp.gov/resources/documents/Reusing_Authorizations_for_Cloud_Products_Quick_Guide.pdf
  (both accessed 2026-07-06).
