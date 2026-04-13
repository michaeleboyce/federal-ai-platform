import {
  getAgencyOptions,
  getProductOptions,
  getUseCaseFacets,
  getUseCasesFiltered,
  getGlobalStats,
} from "@/lib/db";
import { formatNumber } from "@/lib/formatting";
import type { UseCaseFilterInput } from "@/lib/types";
import { UseCaseFilters } from "@/components/use-case-filters";
import { MobileFiltersSheet } from "@/components/mobile-filters-sheet";
import { UseCaseTable } from "@/components/use-case-table";
import { UseCaseGrid } from "@/components/use-case-grid";
import {
  ExportCsvButton,
  Pagination,
  ViewToggle,
} from "@/components/use-case-explorer-toolbar";

export const metadata = {
  title: "Use Cases · Federal AI Inventory",
  description:
    "Browse all reported AI use cases across federal agencies. Filter by agency, entry type, AI sophistication, product, and more.",
};

const PAGE_SIZE = 100;

type Search = Record<string, string | string[] | undefined>;

function first(v: string | string[] | undefined): string | undefined {
  if (Array.isArray(v)) return v[0];
  return v;
}

function parseCsv(v: string | string[] | undefined): string[] {
  const s = first(v);
  if (!s) return [];
  return s
    .split(",")
    .map((x) => x.trim())
    .filter((x) => x.length > 0);
}

function buildFilters(sp: Search): UseCaseFilterInput & { page: number } {
  const page = Math.max(1, Number.parseInt(first(sp.page) ?? "1", 10) || 1);

  const filters: UseCaseFilterInput & { page: number } = {
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
    page,
  };

  const q = first(sp.q);
  if (q) filters.search = q;

  const agencyIds = parseCsv(sp.agency_ids)
    .map((id) => Number.parseInt(id, 10))
    .filter((n) => Number.isFinite(n));
  if (agencyIds.length > 0) filters.agencyIds = agencyIds;

  const agencyTypes = parseCsv(sp.agency_type);
  if (agencyTypes.length > 0) filters.agencyTypes = agencyTypes;

  const productIds = parseCsv(sp.product_ids)
    .map((id) => Number.parseInt(id, 10))
    .filter((n) => Number.isFinite(n));
  if (productIds.length > 0) filters.productIds = productIds;

  const entryTypes = parseCsv(sp.entry_type);
  if (entryTypes.length > 0) filters.entryTypes = entryTypes;

  const sophistications = parseCsv(sp.sophistication);
  if (sophistications.length > 0) filters.aiSophistications = sophistications;

  const scopes = parseCsv(sp.scope);
  if (scopes.length > 0) filters.deploymentScopes = scopes;

  const archs = parseCsv(sp.architecture);
  if (archs.length > 0) filters.architectureTypes = archs;

  const useTypes = parseCsv(sp.use_type);
  if (useTypes.length > 0) filters.useTypes = useTypes;

  const highImpact = parseCsv(sp.high_impact);
  if (highImpact.length > 0) filters.highImpactDesignations = highImpact;

  if (first(sp.coding_tool) === "1") filters.isCodingTool = true;
  if (first(sp.general_llm_access) === "1") filters.isGeneralLLMAccess = true;
  if (first(sp.genai) === "1") filters.isGenAI = true;
  if (first(sp.public_facing) === "1") filters.isPublicFacing = true;
  if (first(sp.has_ato) === "1") filters.hasATOorFedRAMP = true;
  if (first(sp.risk_docs) === "1") filters.hasMeaningfulRiskDocs = true;

  return filters;
}

/** Spell an integer as words for the editorial headline. Falls back to the
 *  numeric form for values outside the small range we're likely to see. */
function spellOut(n: number): string {
  if (n < 0 || n >= 1_000_000) return formatNumber(n);
  const ones = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
  ];
  const tens = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
  ];
  const sayHundreds = (x: number): string => {
    if (x === 0) return "";
    const h = Math.floor(x / 100);
    const rem = x % 100;
    const parts: string[] = [];
    if (h > 0) parts.push(`${ones[h]} hundred`);
    if (rem > 0) {
      if (rem < 20) parts.push(ones[rem]);
      else {
        const t = Math.floor(rem / 10);
        const o = rem % 10;
        parts.push(o === 0 ? tens[t] : `${tens[t]}-${ones[o]}`);
      }
    }
    return parts.join(" ");
  };
  const thousands = Math.floor(n / 1000);
  const rest = n % 1000;
  const parts: string[] = [];
  if (thousands > 0) parts.push(`${sayHundreds(thousands)} thousand`);
  if (rest > 0) parts.push(sayHundreds(rest));
  return parts.join(" ").trim() || "zero";
}

export default async function UseCasesPage({
  searchParams,
}: {
  searchParams: Promise<Search>;
}) {
  const sp = await searchParams;
  const filters = buildFilters(sp);
  const page = filters.page;
  const view = first(sp.view) === "grid" ? "grid" : "table";

  const [{ rows, total }, agencies, products, facets, stats] = await Promise.all([
    Promise.resolve(getUseCasesFiltered(filters)),
    Promise.resolve(getAgencyOptions()),
    Promise.resolve(getProductOptions()),
    Promise.resolve(getUseCaseFacets()),
    Promise.resolve(getGlobalStats()),
  ]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const firstRow = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const lastRow = Math.min(total, page * PAGE_SIZE);

  const totalInDb = stats.total_use_cases + stats.total_consolidated;

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8 md:py-14">
      {/* ------------------------------------------------------------ */}
      {/* EDITORIAL HEADER — filing meta + big italic counter           */}
      {/* ------------------------------------------------------------ */}
      <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-10 md:pb-14">
        <aside className="col-span-12 mb-6 md:col-span-3 md:mb-0">
          <div className="sticky top-32 space-y-3">
            <div className="eyebrow !text-[var(--stamp)]">
              § II · Use Cases
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              N = <span className="tabular-nums">{formatNumber(totalInDb)}</span>
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              Filtered ·{" "}
              <span className="tabular-nums text-foreground">
                {formatNumber(total)}
              </span>
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              OMB M-25-21 · Cycle 2025
            </div>
          </div>
        </aside>
        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display italic text-[2.6rem] leading-[0.98] tracking-[-0.02em] text-foreground md:text-[4.2rem]">
            {spellOut(totalInDb)}
          </h1>
          <p className="mt-3 font-display italic text-[1.4rem] leading-tight tracking-[-0.01em] text-muted-foreground md:text-[1.8rem]">
            uses of artificial intelligence, reported by federal agencies.
          </p>
          <p className="mt-6 max-w-[56ch] text-[0.95rem] leading-relaxed text-foreground/80">
            Every individual and consolidated entry disclosed under OMB
            Memorandum M-25-21. Filter in the left rail; the table and grid
            views below update instantly. Export the current page as CSV at
            any time.
          </p>
        </div>
      </header>

      {/* ------------------------------------------------------------ */}
      {/* EXPLORER — filter rail + results pane                         */}
      {/* ------------------------------------------------------------ */}
      <div className="mt-10 grid grid-cols-1 gap-10 lg:grid-cols-[260px,1fr] lg:gap-8">
        {/* Filter rail.
           Scroll fix: the outer cell is *not* height-constrained. We
           only make the inner panel sticky on lg+, and cap its own
           height so it can scroll when it exceeds the viewport. The
           previous version set `h-[calc(100vh-6rem)] overflow-y-auto`
           on the outer cell, which created a nested scroll container
           competing with the window scrollbar and made page scrolling
           feel "strange". */}
        <div className="min-w-0">
          <div className="lg:sticky lg:top-32 lg:max-h-[calc(100vh-10rem)] lg:overflow-y-auto lg:pr-2">
            <MobileFiltersSheet triggerLabel="Filter use cases">
              <UseCaseFilters
                agencies={agencies}
                products={products}
                facets={{
                  agencyTypes: facets.agencyTypes,
                  tagEntryTypes: facets.tagEntryTypes,
                  tagDeploymentScopes: facets.tagDeploymentScopes,
                  tagAISophistications: facets.tagAISophistications,
                  tagArchitectureTypes: facets.tagArchitectureTypes,
                  tagUseTypes: facets.tagUseTypes,
                  tagHighImpactDesignations: facets.tagHighImpactDesignations,
                }}
              />
            </MobileFiltersSheet>
          </div>
        </div>

        <section className="flex min-w-0 flex-col gap-6">
          {/* Toolbar — mono-styled bar. */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-y-2 border-foreground py-2.5">
            <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              Showing{" "}
              <span className="tabular-nums text-foreground">
                {formatNumber(firstRow)}–{formatNumber(lastRow)}
              </span>
              {" · "}of{" "}
              <span className="tabular-nums text-foreground">
                {formatNumber(total)}
              </span>
              {total !== stats.total_use_cases && (
                <>
                  {" · "}
                  <span className="tabular-nums">
                    {formatNumber(stats.total_use_cases)}
                  </span>
                  {" "}total records
                </>
              )}
            </p>
            <div className="flex items-center gap-2">
              <ViewToggle />
              <ExportCsvButton rows={rows} />
            </div>
          </div>

          {view === "grid" ? (
            <UseCaseGrid rows={rows} />
          ) : (
            <UseCaseTable rows={rows} />
          )}

          <div className="flex justify-center pt-2">
            <Pagination page={page} totalPages={totalPages} />
          </div>
        </section>
      </div>
    </div>
  );
}
