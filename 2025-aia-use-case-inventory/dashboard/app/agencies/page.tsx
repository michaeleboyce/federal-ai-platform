import { Suspense } from "react";
import { getAgencyMaturity } from "@/lib/db";
import { AgenciesTable, type AgencyRow } from "@/components/agencies-table";
import { MetricTile } from "@/components/metric-tile";
import { formatNumber } from "@/lib/formatting";

export const metadata = {
  title: "Agencies · Federal AI Use Case Inventory",
};

export default function AgenciesPage() {
  const rows = getAgencyMaturity();

  const tableRows: AgencyRow[] = rows.map((a) => ({
    id: a.id,
    name: a.name,
    abbreviation: a.abbreviation,
    agency_type: a.agency_type,
    status: a.status,
    total_use_cases: a.maturity?.total_use_cases ?? 0,
    total_consolidated_entries: a.maturity?.total_consolidated_entries ?? 0,
    distinct_products_deployed: a.maturity?.distinct_products_deployed ?? 0,
    maturity_tier: a.maturity?.maturity_tier ?? null,
    year_over_year_growth: a.maturity?.year_over_year_growth ?? null,
    has_enterprise_llm: a.maturity?.has_enterprise_llm ?? null,
    has_coding_assistants: a.maturity?.has_coding_assistants ?? null,
  }));

  const total = tableRows.length;
  const withLLM = tableRows.filter((r) => r.has_enterprise_llm === 1).length;
  const withCoding = tableRows.filter(
    (r) => r.has_coding_assistants === 1,
  ).length;
  const leading = tableRows.filter((r) => r.maturity_tier === "leading").length;
  const customHeavy = rows.filter(
    (a) => (a.maturity?.custom_system_count ?? 0) >= 10,
  ).length;

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8 md:py-14">
      {/* ---------------------------------------------------------------- */}
      {/* Editorial masthead                                                */}
      {/* ---------------------------------------------------------------- */}
      <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-12">
        <aside className="col-span-12 mb-8 md:col-span-3 md:mb-0">
          <div className="sticky top-32 space-y-3">
            <div className="eyebrow !text-[var(--stamp)]">§ I · Agencies</div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              Directory · Filing Index
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              Cycle 2025 · {formatNumber(total)} agencies
            </div>
            <p className="max-w-xs border-t border-border pt-3 text-sm leading-snug text-muted-foreground">
              Click any row to open the per-agency detail page. Filters are
              reflected in the URL so every view is shareable.
            </p>
          </div>
        </aside>

        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display text-[clamp(2.4rem,6vw,5rem)] italic leading-[0.95] tracking-[-0.03em] text-foreground">
            Sixty agencies,
            <br />
            ranked and compared.
          </h1>
          <p className="mt-8 max-w-prose text-[1.02rem] leading-[1.55] text-foreground/85">
            Every agency that filed a 2025 AI use-case inventory, side by side.
            Sort by volume, product breadth, or year-over-year growth; filter
            by type, maturity tier, or capability flags.
          </p>

          {/* Four-column ledger ------------------------------------------ */}
          <div className="mt-10 grid grid-cols-2 gap-x-6 gap-y-6 md:grid-cols-4">
            <MetricTile
              label="Enterprise LLM"
              value={`${withLLM}/${total}`}
              sublabel="Have a dept-wide model"
              accent="verified"
            />
            <MetricTile
              label="Coding tools"
              value={`${withCoding}/${total}`}
              sublabel="Copilot, Claude, etc."
              accent="ink"
            />
            <MetricTile
              label="Leading tier"
              value={`${leading}/${total}`}
              sublabel="Most mature filings"
              accent="stamp"
            />
            <MetricTile
              label="Custom-AI heavy"
              value={`${customHeavy}/${total}`}
              sublabel="≥ 10 custom systems"
              accent="highlight"
            />
          </div>
        </div>
      </header>

      {/* ---------------------------------------------------------------- */}
      {/* Directory table                                                   */}
      {/* ---------------------------------------------------------------- */}
      <section className="mt-16 md:mt-20">
        <div className="mb-6 flex items-baseline justify-between gap-4 border-b border-border pb-3">
          <div className="eyebrow">Fig. 1 · Directory</div>
          <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            Sortable · {formatNumber(total)} rows
          </div>
        </div>

        <Suspense fallback={null}>
          <AgenciesTable rows={tableRows} />
        </Suspense>
      </section>
    </div>
  );
}
