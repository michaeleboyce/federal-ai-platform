import Link from "next/link";
import {
  getAgencyMaturity,
  getAgencyTypeByTier,
  getGlobalStats,
  getMaturityTierSummary,
  getRecentlyModifiedAgencies,
  getTopProducts,
} from "@/lib/db";
import { formatDate, formatNumber } from "@/lib/formatting";
import { MaturityTierCard } from "@/components/maturity-tier-card";
import { TopProductsChart } from "@/components/charts/top-products-chart";
import { AgencyTypeChart } from "@/components/charts/agency-type-chart";
import { Section, Figure, MonoChip } from "@/components/editorial";
import { buildUseCasesUrl } from "@/lib/urls";

export default function HomePage() {
  const stats = getGlobalStats();
  const maturity = getAgencyMaturity();
  const tiers = getMaturityTierSummary();
  const topProducts = getTopProducts(10);
  const agencyTypeData = getAgencyTypeByTier();
  const recent = getRecentlyModifiedAgencies(5);

  const distinctProducts = maturity.reduce(
    (acc, row) => acc + (row.maturity?.distinct_products_deployed ?? 0),
    0,
  );
  const codingEntries = maturity.reduce(
    (acc, row) => acc + (row.maturity?.coding_tool_count ?? 0),
    0,
  );

  const missingEnterpriseLLM = maturity
    .filter((a) => (a.maturity?.has_enterprise_llm ?? 0) === 0)
    .map((a) => ({ id: a.id, abbr: a.abbreviation, name: a.name }))
    .sort((a, b) => a.abbr.localeCompare(b.abbr));
  const missingCoding = maturity
    .filter((a) => (a.maturity?.has_coding_assistants ?? 0) === 0)
    .map((a) => ({ id: a.id, abbr: a.abbreviation, name: a.name }))
    .sort((a, b) => a.abbr.localeCompare(b.abbr));

  // Aggregate rollups across agency maturity rows.
  const reportingAgencies = maturity.length;
  const totalEntries = stats.total_use_cases + stats.total_consolidated;
  const agenciesWithEnterpriseLLM = maturity.filter(
    (a) => (a.maturity?.has_enterprise_llm ?? 0) === 1,
  ).length;
  const agenciesWithCoding = maturity.filter(
    (a) => (a.maturity?.has_coding_assistants ?? 0) === 1,
  ).length;
  const agenciesWithAgentic = maturity.filter(
    (a) => (a.maturity?.has_agentic_ai ?? 0) === 1,
  ).length;
  const agenciesWithCustom = maturity.filter(
    (a) => (a.maturity?.has_custom_ai ?? 0) === 1,
  ).length;
  const agenticEntries = maturity.reduce(
    (acc, row) => acc + (row.maturity?.agentic_ai_count ?? 0),
    0,
  );
  const genAIEntries = stats.total_genai_entries;

  const pct = (n: number, d: number): string =>
    d === 0 ? "—" : `${Math.round((n / d) * 100)}%`;

  const topProductsData = topProducts.map((p) => ({
    id: p.id,
    name: p.canonical_name,
    vendor: p.vendor,
    agency_count: p.agency_count,
    use_case_count: p.use_case_count,
  }));

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-14 md:px-8 md:py-20">
      {/* ------------------------------------------------------------ */}
      {/* HERO — editorial nameplate + drop-cap lead                    */}
      {/* ------------------------------------------------------------ */}
      <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-14 md:pb-20">
        {/* Left margin: filing meta */}
        <aside className="col-span-12 mb-8 md:col-span-3 md:mb-0">
          <div className="sticky top-32 space-y-4">
            <div>
              <div className="eyebrow mb-1.5 !text-[var(--stamp)]">
                No. 001 · Filed
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Research Memorandum
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                OMB M-25-21 · Cycle 2025
              </div>
            </div>

            <div className="relative inline-flex w-fit">
              <div className="stamp">Preliminary</div>
            </div>

            <div className="hidden space-y-3 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground md:block">
              <div className="border-t border-border pt-3">
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Aggregate
                </div>
                <div className="text-foreground">
                  <Link
                    href={buildUseCasesUrl({})}
                    className="transition-colors hover:text-[var(--stamp)]"
                  >
                    {formatNumber(stats.total_use_cases)} uc
                  </Link>{" "}
                  ·{" "}
                  <Link
                    href={buildUseCasesUrl({})}
                    className="transition-colors hover:text-[var(--stamp)]"
                  >
                    {formatNumber(stats.total_consolidated)} cons
                  </Link>
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Coverage
                </div>
                <div className="text-foreground">
                  <Link
                    href="/agencies"
                    className="transition-colors hover:text-[var(--stamp)]"
                  >
                    {stats.total_agencies_with_data}/{stats.total_agencies}{" "}
                    agencies
                  </Link>
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Catalogue
                </div>
                <div className="text-foreground">
                  <Link
                    href="/products"
                    className="transition-colors hover:text-[var(--stamp)]"
                  >
                    {stats.total_products} products
                  </Link>{" "}
                  ·{" "}
                  <Link
                    href="/templates"
                    className="transition-colors hover:text-[var(--stamp)]"
                  >
                    {stats.total_templates} templates
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Headline column */}
        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display text-[clamp(2.8rem,7.5vw,6.4rem)] leading-[0.95] tracking-[-0.03em] text-foreground">
            An inventory of{" "}
            <em className="inline font-normal italic">everything</em>{" "}
            American
            <br />
            government says it is doing with
            <br />
            <span className="relative inline-block">
              <span
                aria-hidden
                className="absolute inset-x-[-0.08em] bottom-[0.16em] h-[0.38em] bg-[var(--highlight)]/90"
              />
              <span className="relative">artificial&nbsp;intelligence.</span>
            </span>
          </h1>

          <div className="mt-10 grid grid-cols-12 gap-x-6 gap-y-6">
            <p className="col-span-12 max-w-prose text-[1.05rem] leading-[1.55] text-foreground/85 md:col-span-7">
              <span className="float-left mr-2 font-display italic text-[3.6rem] leading-[0.82] text-foreground">
                F
              </span>
              orty-four federal agencies filed{" "}
              <span className="font-medium text-foreground">
                {formatNumber(stats.total_use_cases)} individual use cases
              </span>{" "}
              and {formatNumber(stats.total_consolidated)} consolidated entries
              to the Office of Management and Budget for the 2025 reporting
              cycle. This inventory collects them all in one place, normalizes
              the schema, tags each record for the questions that matter, and
              lets you drill from an enterprise-wide rollout of Microsoft
              Copilot at the Department of State down to a single line-item on
              a rural-land classifier at the USDA.
            </p>

            <div className="col-span-12 md:col-span-4 md:col-start-9 md:self-end">
              <div className="editorial-rule-left space-y-3">
                <div className="eyebrow">By the numbers</div>
                <dl className="space-y-2 font-mono text-sm">
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">Use cases</dt>
                    <dd className="tabular-nums text-foreground">
                      <Link
                        href={buildUseCasesUrl({})}
                        className="transition-colors hover:text-[var(--stamp)]"
                      >
                        {formatNumber(stats.total_use_cases)}
                      </Link>
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">Agencies</dt>
                    <dd className="tabular-nums text-foreground">
                      <Link
                        href="/agencies"
                        className="transition-colors hover:text-[var(--stamp)]"
                      >
                        {stats.total_agencies_with_data}
                      </Link>
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">Products</dt>
                    <dd className="tabular-nums text-foreground">
                      <Link
                        href="/products"
                        className="transition-colors hover:text-[var(--stamp)]"
                      >
                        {distinctProducts}
                      </Link>
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3">
                    <dt className="text-muted-foreground">Coding entries</dt>
                    <dd className="tabular-nums text-foreground">
                      <Link
                        href={buildUseCasesUrl({ isCodingTool: true })}
                        className="transition-colors hover:text-[var(--stamp)]"
                      >
                        {formatNumber(codingEntries)}
                      </Link>
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------ */}
      {/* § I — AT A GLANCE                                             */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="I"
        title="At a glance"
        lede={`What ${reportingAgencies} reporting agencies collectively say about their AI.`}
      >
        <div className="space-y-10">
          <div>
            <div className="mb-3 eyebrow">
              Entry mix · of {formatNumber(totalEntries)} reported AI uses (individual + consolidated)
            </div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-5 md:grid-cols-4">
              <StatGlance
                label="Coding assistants"
                count={stats.total_coding_entries}
                pct={pct(stats.total_coding_entries, totalEntries)}
                href={buildUseCasesUrl({ isCodingTool: true })}
                accent="verified"
              />
              <StatGlance
                label="Generative AI"
                count={genAIEntries}
                pct={pct(genAIEntries, totalEntries)}
                href={buildUseCasesUrl({ isGenAI: true })}
                accent="stamp"
              />
              <StatGlance
                label="Agentic AI"
                count={agenticEntries}
                pct={pct(agenticEntries, totalEntries)}
                href={buildUseCasesUrl({ aiSophistications: ["agentic"] })}
              />
              <StatGlance
                label="High-impact"
                count={undefined}
                pct={undefined}
                sublabel="see filter"
                href={buildUseCasesUrl({ highImpactDesignations: ["high_impact"] })}
              />
            </div>
          </div>

          <div>
            <div className="mb-3 eyebrow">
              Stage mix · of {formatNumber(stats.total_use_cases)} individual use cases
            </div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-5 md:grid-cols-4">
              <StatGlance
                label="Pre-deployment"
                count={stats.stage_bucket_counts.pre_deployment}
                pct={pct(stats.stage_bucket_counts.pre_deployment, stats.total_use_cases)}
                href={buildUseCasesUrl({ stageBuckets: ["pre_deployment"] })}
              />
              <StatGlance
                label="Pilot"
                count={stats.stage_bucket_counts.pilot}
                pct={pct(stats.stage_bucket_counts.pilot, stats.total_use_cases)}
                href={buildUseCasesUrl({ stageBuckets: ["pilot"] })}
              />
              <StatGlance
                label="Deployed"
                count={stats.stage_bucket_counts.deployed}
                pct={pct(stats.stage_bucket_counts.deployed, stats.total_use_cases)}
                href={buildUseCasesUrl({ stageBuckets: ["deployed"] })}
                accent="verified"
              />
              <StatGlance
                label="Retired"
                count={stats.stage_bucket_counts.retired}
                pct={pct(stats.stage_bucket_counts.retired, stats.total_use_cases)}
                href={buildUseCasesUrl({ stageBuckets: ["retired"] })}
              />
            </div>
          </div>

          <div>
            <div className="mb-3 eyebrow">
              Agency coverage · of {reportingAgencies} reporting
            </div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-5 md:grid-cols-4">
              <StatGlance
                label="With enterprise LLM"
                count={agenciesWithEnterpriseLLM}
                pct={pct(agenciesWithEnterpriseLLM, reportingAgencies)}
                href={buildUseCasesUrl({ isGeneralLLMAccess: true })}
                accent="stamp"
              />
              <StatGlance
                label="With coding assistants"
                count={agenciesWithCoding}
                pct={pct(agenciesWithCoding, reportingAgencies)}
                href={buildUseCasesUrl({ isCodingTool: true })}
                accent="verified"
              />
              <StatGlance
                label="With agentic AI"
                count={agenciesWithAgentic}
                pct={pct(agenciesWithAgentic, reportingAgencies)}
                href={buildUseCasesUrl({ aiSophistications: ["agentic"] })}
              />
              <StatGlance
                label="With custom AI"
                count={agenciesWithCustom}
                pct={pct(agenciesWithCustom, reportingAgencies)}
                href={buildUseCasesUrl({ entryTypes: ["custom_system"] })}
              />
            </div>
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § II — MATURITY LEDGER                                        */}
      {/* ------------------------------------------------------------ */}
      <Section number="II" title="The ledger" lede="How agencies sort.">
        <MaturityTierCard tiers={tiers} />
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § II — ADOPTION                                               */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="III"
        title="What they run"
        lede="The ten most widely deployed AI products, weighted by agencies reporting them."
      >
        <div className="grid gap-x-6 gap-y-10 md:grid-cols-5">
          <Figure
            className="md:col-span-3"
            eyebrow="Fig. 1 · Product adoption"
            caption={
              <>
                Source: <span className="text-foreground">use_cases</span>{" "}
                joined with{" "}
                <span className="text-foreground">products</span>; top 10 by
                distinct agencies.
              </>
            }
          >
            <TopProductsChart data={topProductsData} />
          </Figure>
          <Figure
            className="md:col-span-2"
            eyebrow="Fig. 2 · Agency type × tier"
            caption="Agencies with inventory data, grouped by type and maturity tier."
          >
            <AgencyTypeChart data={agencyTypeData} />
          </Figure>
        </div>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § III — GAPS                                                  */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="IV"
        title="What is missing"
        lede="The absences tell a story the presences do not."
      >
        <div className="grid gap-x-8 gap-y-10 md:grid-cols-2">
          <GapList
            kicker="A"
            title="Agencies without an enterprise LLM"
            note={
              <>
                <Link
                  href={buildUseCasesUrl({ isGeneralLLMAccess: false })}
                  className="font-medium text-foreground transition-colors hover:text-[var(--stamp)]"
                >
                  {missingEnterpriseLLM.length} of {maturity.length}
                </Link>{" "}
                reporting agencies do not list department- or enterprise-wide
                access to a general-purpose language model.
              </>
            }
            items={missingEnterpriseLLM}
            tone="stamp"
          />
          <GapList
            kicker="B"
            title="Agencies without coding assistants"
            note={
              <>
                <Link
                  href={buildUseCasesUrl({ isCodingTool: false })}
                  className="font-medium text-foreground transition-colors hover:text-[var(--stamp)]"
                >
                  {missingCoding.length} of {maturity.length}
                </Link>{" "}
                reporting agencies have no recorded deployment of GitHub
                Copilot, Claude Code, CodeWhisperer, or any coding tool.
              </>
            }
            items={missingCoding}
            tone="ink"
          />
        </div>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § IV — LAST-MODIFIED                                          */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="V"
        title="Most recent filings"
        lede="Five agencies whose inventories have moved most recently."
      >
        <ul className="divide-y divide-border border-y-2 border-foreground">
          {recent.map((a, i) => (
            <li
              key={a.id}
              className="group grid grid-cols-[2.25rem_3.75rem_1fr_auto] items-baseline gap-x-3 py-3 text-[0.95rem] md:grid-cols-[2.75rem_5rem_1fr_auto] md:gap-x-5"
            >
              <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                {String(i + 1).padStart(2, "0")}
              </span>
              <Link
                href={`/agencies/${a.abbreviation}`}
                className="font-mono text-sm font-semibold tracking-[0.04em] text-foreground hover:text-[var(--stamp)]"
              >
                {a.abbreviation}
              </Link>
              <Link
                href={`/agencies/${a.abbreviation}`}
                className="truncate font-display text-[1.08rem] italic text-foreground transition-[letter-spacing] group-hover:tracking-[-0.01em]"
              >
                {a.name}
              </Link>
              <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
                {formatDate(a.last_modified)}
              </span>
            </li>
          ))}
          {recent.length === 0 ? (
            <li className="py-3 text-sm text-muted-foreground">
              No modification timestamps recorded.
            </li>
          ) : null}
        </ul>
      </Section>
    </div>
  );
}

function GapList({
  kicker,
  title,
  note,
  items,
  tone,
}: {
  kicker: string;
  title: string;
  note: React.ReactNode;
  items: Array<{ id: number; abbr: string; name: string }>;
  tone: "stamp" | "ink";
}) {
  return (
    <div>
      <div className="mb-3 flex items-baseline gap-3 border-t-2 border-foreground pt-3">
        <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--stamp)]">
          {kicker}
        </span>
        <h3 className="font-display italic text-[1.35rem] leading-tight text-foreground md:text-[1.55rem]">
          {title}
        </h3>
      </div>
      <p className="mb-4 max-w-prose text-[0.95rem] leading-[1.55] text-muted-foreground">
        {note}
      </p>
      <ul className="flex flex-wrap gap-1.5">
        {items.length === 0 ? (
          <li className="font-mono text-xs uppercase tracking-[0.14em] text-muted-foreground">
            None —
          </li>
        ) : (
          items.map((a) => (
            <li key={a.id}>
              <MonoChip
                href={`/agencies/${a.abbr}`}
                title={a.name}
                tone={tone}
              >
                {a.abbr}
              </MonoChip>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}

const ACCENT_COLOR: Record<string, string> = {
  stamp: "text-[var(--stamp)]",
  verified: "text-[var(--verified)]",
  default: "text-foreground",
};

function StatGlance({
  label,
  count,
  pct,
  sublabel,
  href,
  accent = "default",
}: {
  label: string;
  count: number | undefined;
  pct: string | undefined;
  sublabel?: string;
  href: string;
  accent?: keyof typeof ACCENT_COLOR;
}) {
  return (
    <Link
      href={href}
      className="group flex min-w-0 flex-col gap-1 border-t-2 border-foreground pt-2 transition-colors"
    >
      <div className="eyebrow truncate">{label}</div>
      <div className="flex items-baseline gap-2">
        <span
          className={`font-display text-[2.4rem] italic leading-[0.95] tracking-[-0.02em] tabular-nums transition-colors group-hover:text-[var(--stamp)] ${ACCENT_COLOR[accent]}`}
        >
          {pct ?? "—"}
        </span>
        {count != null && (
          <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            {formatNumber(count)}
          </span>
        )}
      </div>
      {sublabel ? (
        <div className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-muted-foreground">
          {sublabel}
        </div>
      ) : null}
    </Link>
  );
}
