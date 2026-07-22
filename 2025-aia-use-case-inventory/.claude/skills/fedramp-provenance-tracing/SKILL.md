---
name: fedramp-provenance-tracing
description: Use when tracing HOW a specific AI tool/product/service reaches federal agencies through FedRAMP's layered records — answering "is X authorized, through what channel, and which agencies can hold it?" (e.g. "Claude for Government is a Palantir tenant service", "M365 Copilot inherits via the M365 GCC package", "which agencies have Bedrock in reach?"). Covers the five visibility channels (own listing, containment, tenancy, infrastructure leverage, off-ledger umbrellas), the dual meaning of the services-in-scope catalog, the mandatory parent-walk CTE, and the ordered lookup recipe with its known traps. Triggered by: any "how did tool X get into agency Y" question, shadow-authorization or piggyback analysis, articles/pages claiming a product is or is not FedRAMP-covered, or extending the spread/shelf boards.
---

# FedRAMP Provenance Tracing — how to cross-reference services, products, and packages

The question "does X have FedRAMP standing?" has NO single-table answer. A
tool can reach agencies through five distinct channels, each recorded (or
not) in a different place. Always check ALL channels before asserting a
tool is "not authorized" or "absent from FedRAMP" — the flagship
counterexample is Anthropic: **zero rows in `fedramp_products`, yet
"Claude for Government (C4G)" is FedRAMP High** as a service in scope of
Palantir's package.

## The five visibility channels (check in this order)

| # | Channel | Where recorded | Example |
|---|---|---|---|
| 1 | Own marketplace listing | `fedramp_products` (match on `csp`/`cso` LIKE) | ChatGPT Enterprise = FR2533155773 |
| 2 | Containment — component of a bigger package | `fedramp_authorized_services` (service in the package's scope catalog) | Amazon Bedrock inside AWS US East/West (Moderate) AND GovCloud (High); Azure OpenAI inside Azure Commercial; M365 Copilot inside M365 GCC |
| 3 | Tenancy — SaaS piggybacking on another company's authorization (Palantir FedStart-style) | ALSO `fedramp_authorized_services` — the scope catalog of the host package doubles as the tenant roster | PFCS-SS (FR2315464863, High) lists C4G, Devin Desktop, AutogenAI Federal, TRM Labs, ConductorAI, Hyperscience… |
| 4 | Infrastructure leverage — "X runs on Y" | `fedramp_leveraged_systems` (system_name strings, messy) | Most SaaS leverages AWS/Azure |
| 5 | Off-ledger umbrellas — OneGov deals, GSA USAi tenancy | **Nowhere in the DB.** Only press/GSA statements | Claude on USAi pre-ban; $1 OneGov deals |

Key insight from channel 2 vs 3: the scope catalog does **double duty**.
For hyperscalers it lists their own components; for accreditation-
piggyback hosts (Palantir) it lists third-party tenants. Same table, two
different business relationships — the data cannot tell you which, so
name the relationship from knowledge of the vendors, not from the join.

## The ordered lookup recipe

Given a tool name `X` (try name variants: "Claude", "Claude for
Government", "C4G", vendor "Anthropic"):

```sql
-- 1. Own listing?
SELECT fedramp_id, cso, status, impact_level, auth_date, reuse_count
  FROM fedramp_products WHERE csp LIKE '%X%' OR cso LIKE '%X%';

-- 2+3. In any scope catalog? (host package + level + recency)
SELECT s.service, p.csp, p.cso, p.impact_level, s.recency
  FROM fedramp_authorized_services s JOIN fedramp_products p USING(fedramp_id)
 WHERE s.service LIKE '%X%';

-- AI label for the service (sidecar; every core_ai/ai_featured row is QC'd)
SELECT category, confidence, source FROM fedramp_ai_service_classification
 WHERE service LIKE '%X%';

-- 4. Leveraged-systems mentions
SELECT p.csp, p.cso FROM fedramp_leveraged_systems ls
  JOIN fedramp_products p USING(fedramp_id) WHERE ls.system_name LIKE '%X%';

-- Which agencies can hold it: ATO holders of every host package found above
SELECT COALESCE(ia.abbreviation, fa.parent_agency) agency, MAX(a.ato_issuance_date)
  FROM fedramp_authorizations a
  JOIN fedramp_agencies fa ON fa.id = a.agency_id
  LEFT JOIN fedramp_agency_links al ON al.fedramp_agency_id = a.agency_id
  LEFT JOIN agencies ia ON ia.id = al.inventory_agency_id
 WHERE a.fedramp_id = :host_fedramp_id GROUP BY fa.id;
```

Dashboard helpers already encapsulate most of this:
`getServicesInScopeForProduct`, `getAiServicesInReachForAgency`,
`getFrontierReachByAgency`, `getAgenciesHoldingAto`
(`dashboard/lib/db/fedramp/spread.ts`, `classification.ts`).

## Connecting to the INVENTORY side (which use cases involve X)

- Product edges: `use_case_products` / `entry_product_edges` → curated
  `products`. **NEVER join `fedramp_product_links` directly** — always go
  through the recursive parent walk (`EFFECTIVE_FEDRAMP_LINKS_CTE`,
  `dashboard/lib/db/shared/sql-fragments.ts`), which lets children
  inherit the parent's FedRAMP link (M365 Copilot → Microsoft 365 → M365
  GCC package). Skipping the walk once inflated an "untraceable COTS"
  count from 415 to 575 by wrongly including Teams, Copilot, Azure
  OpenAI, and Palantir AIP.
- The walk models **vendor families, not tenancy** — by design. Claude
  never walks to Palantir's package because Claude is not a component of
  PFCS; it is a tenant. Tenancy relationships live ONLY in
  `fedramp_authorized_services`. Do not "fix" the product hierarchy to
  encode tenancy.
- Tags: `use_case_tags.is_cots_commercial` (+`cots_product_name`,
  `cots_vendor`) is the direct enterprise-software signal (NOT
  `is_enterprise_wide`, which measures rollout breadth). When
  `cots_product_name` is blank, `use_cases.vendor_name` is usually
  richer (Clearview AI, Dataminr, Anduril…). `has_ato` is the agency's
  self-report (messy enum incl. "Use vendor's ATO or FedRAMP
  authorization"); cross it against the marketplace ATO ledger to split
  "both say no" from "agency says yes, ledger silent".

## Worked example (the pattern this skill exists to preserve)

"How did Claude get into StateChat?" — press record has no answer. Ledger
route: `fedramp_authorized_services` shows *Claude for Government (C4G)*
in scope of PFCS-SS (FR2315464863, High) → ATO holders of that package:
HHS (2024-01), **State (2025-03-13)**, DOE, Treasury, ED → StateChat is
Palantir-integrated and ran Claude Sonnet 4.5 by early 2026. The ATO
does not name StateChat, so present as "the paper trail suggests", never
as established fact.

## Traps

1. **Absence of a listing ≠ absence of authorization** (Anthropic), and
   presence in a scope catalog ≠ any agency enabled it. Guardrail
   phrasing: "in scope of a package the agency holds an ATO for."
2. **The reuse ledger under-records** (agencies email ATO letters to the
   PMO; GAO 2019/2024). Zero reuses ≠ zero adoption; inventory rows can
   show use the ledger never saw (ChatGPT: 248 rows / 22 agencies vs
   reuse_count 0 at snapshot 2026-06-12).
3. **A tool can ride multiple channels at once** (Claude: Bedrock
   containment at High, FedStart tenancy at High, USAi umbrella).
   Inventory rows naming the tool cannot be attributed to a specific
   channel — say so.
4. Scope catalogs come from the raw export's `service_last_90` +
   `all_others` fields (the `authorized_services` field is always empty —
   ingest guard exists). Only ~90 of 659 products publish a catalog;
   absence of a catalog ≠ no components.
5. Snapshot-date everything (`fedramp_snapshot`); tenant rosters and
   levels move. Related skills: `fedramp-data-model` (table semantics),
   `publish-and-repin` (before citing numbers publicly).
