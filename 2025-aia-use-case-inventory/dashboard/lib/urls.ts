/**
 * URL-builder helpers so every drill-through "numbers are links" call site
 * produces the same canonical query-string shape that `/use-cases` and
 * `/agencies` parse in their `searchParams` handlers.
 *
 * Always import from here — never hand-roll `/use-cases?foo=bar` strings.
 */

import type { UseCaseFilterInput } from "./types";

// Map of UseCaseFilterInput keys -> URL search-param names used by
// /use-cases/page.tsx `buildFilters`.
const ARRAY_PARAMS: Array<
  [keyof UseCaseFilterInput, string, "number" | "string"]
> = [
  ["agencyIds", "agency_ids", "number"],
  ["productIds", "product_ids", "number"],
  ["templateIds", "template_ids", "number"],
  ["agencyTypes", "agency_type", "string"],
  ["entryTypes", "entry_type", "string"],
  ["aiSophistications", "sophistication", "string"],
  ["deploymentScopes", "scope", "string"],
  ["architectureTypes", "architecture", "string"],
  ["useTypes", "use_type", "string"],
  ["highImpactDesignations", "high_impact", "string"],
  ["bureaus", "bureau", "string"],
  ["maturityTiers", "tier", "string"],
  ["stageBuckets", "stage_bucket", "string"],
];

const BOOL_PARAMS: Array<
  [keyof UseCaseFilterInput, string]
> = [
  ["isCodingTool", "coding_tool"],
  ["isGeneralLLMAccess", "general_llm_access"],
  ["isGenAI", "genai"],
  ["isPublicFacing", "public_facing"],
  ["hasATOorFedRAMP", "has_ato"],
  ["hasMeaningfulRiskDocs", "risk_docs"],
];

/** Build a `/use-cases?...` URL from a filter object. Skips empty arrays. */
export function buildUseCasesUrl(
  filters: Partial<UseCaseFilterInput> & { q?: string } = {},
): string {
  const params = new URLSearchParams();

  if (filters.search) params.set("q", filters.search);
  // Also accept a plain `q` alias for callers that want to skip the
  // UseCaseFilterInput naming.
  const maybeQ = (filters as { q?: string }).q;
  if (maybeQ && !filters.search) params.set("q", maybeQ);

  for (const [key, param] of ARRAY_PARAMS) {
    const value = filters[key] as unknown;
    if (Array.isArray(value) && value.length > 0) {
      params.set(param, value.map((v) => String(v)).join(","));
    }
  }

  for (const [key, param] of BOOL_PARAMS) {
    const value = filters[key] as boolean | undefined;
    if (value === true) params.set(param, "1");
    if (value === false) params.set(param, "0");
  }

  const qs = params.toString();
  return qs ? `/use-cases?${qs}` : "/use-cases";
}

/** Build an `/agencies?...` URL. */
export function buildAgenciesUrl(opts: {
  tier?: string | string[];
  type?: string | string[];
  hasEnterpriseLlm?: boolean;
  hasCoding?: boolean;
  q?: string;
} = {}): string {
  const params = new URLSearchParams();
  const tier = Array.isArray(opts.tier) ? opts.tier.join(",") : opts.tier;
  if (tier) params.set("tier", tier);
  const type = Array.isArray(opts.type) ? opts.type.join(",") : opts.type;
  if (type) params.set("type", type);
  if (opts.hasEnterpriseLlm === true) params.set("llm", "1");
  if (opts.hasEnterpriseLlm === false) params.set("llm", "0");
  if (opts.hasCoding === true) params.set("coding", "1");
  if (opts.hasCoding === false) params.set("coding", "0");
  if (opts.q) params.set("q", opts.q);
  const qs = params.toString();
  return qs ? `/agencies?${qs}` : "/agencies";
}

/** Convenience: single-agency drill-through to use-cases. */
export function agencyUseCasesUrl(
  agencyId: number,
  extra: Partial<UseCaseFilterInput> = {},
): string {
  return buildUseCasesUrl({ ...extra, agencyIds: [agencyId] });
}

/** Convenience: single-product drill-through to use-cases. */
export function productUseCasesUrl(
  productId: number,
  extra: Partial<UseCaseFilterInput> = {},
): string {
  return buildUseCasesUrl({ ...extra, productIds: [productId] });
}

/** Convenience: single-template drill-through to use-cases. */
export function templateUseCasesUrl(
  templateId: number,
  extra: Partial<UseCaseFilterInput> = {},
): string {
  return buildUseCasesUrl({ ...extra, templateIds: [templateId] });
}
