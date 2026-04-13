import * as React from "react";
import Link from "next/link";
import {
  type AgencyCompareData,
  getAgencies,
  getAgencyCompareData,
} from "@/lib/db";
import {
  formatNumber,
  formatPercent,
  formatYoY,
  maturityTierLabel,
} from "@/lib/formatting";
import { ComparePicker } from "@/components/compare-picker";
import { ArrowRight, Check, Minus, X } from "lucide-react";
import { DonutChart } from "@/components/charts/donut-chart";
import {
  ENTRY_TYPE_COLORS,
  ENTRY_TYPE_LABELS,
  Figure,
  MonoChip,
} from "@/components/editorial";

export const metadata = {
  title: "Compare agencies · Federal AI Use Case Inventory",
};

function parseAbbrs(raw: string | string[] | undefined): string[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  return String(raw)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function Bool({ v }: { v: number | null | undefined }) {
  if (v === 1)
    return (
      <span className="inline-flex items-center gap-1 text-[var(--verified)]">
        <Check className="size-4" aria-hidden />
        <span className="sr-only">Yes</span>
      </span>
    );
  if (v === 0)
    return (
      <span className="inline-flex items-center gap-1 text-[var(--stamp)]">
        <X className="size-4" aria-hidden />
        <span className="sr-only">No</span>
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground">
      <Minus className="size-4" aria-hidden />
    </span>
  );
}

/** Ordered list of entry-type keys rendered in the strip. */
const ENTRY_TYPE_KEYS: Array<keyof AgencyCompareData["entry_type_mix"]> = [
  "product_deployment",
  "custom_system",
  "bespoke_application",
  "generic_use_pattern",
  "product_feature",
  "unknown",
];

function entryTypeColor(key: string): string {
  return ENTRY_TYPE_COLORS[key] ?? "#94a3b8";
}

function entryTypeLabel(key: string): string {
  return ENTRY_TYPE_LABELS[key] ?? "Unknown";
}

function EntryTypeStrip({ mix }: { mix: AgencyCompareData["entry_type_mix"] }) {
  const total = ENTRY_TYPE_KEYS.reduce((acc, k) => acc + mix[k], 0);
  if (total === 0) {
    return (
      <span className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-muted-foreground">
        no data
      </span>
    );
  }
  return (
    <div className="flex w-full flex-col gap-1.5">
      <div className="flex h-2 w-full overflow-hidden border border-border">
        {ENTRY_TYPE_KEYS.map((k) => {
          const pct = (mix[k] / total) * 100;
          if (pct === 0) return null;
          return (
            <div
              key={k}
              title={`${entryTypeLabel(k)}: ${mix[k]} (${pct.toFixed(1)}%)`}
              style={{ width: `${pct}%`, background: entryTypeColor(k) }}
              className="h-full"
            />
          );
        })}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
        {ENTRY_TYPE_KEYS.filter((k) => mix[k] > 0).map((k) => {
          const pct = (mix[k] / total) * 100;
          return (
            <span key={k} className="inline-flex items-center gap-1 tabular-nums">
              <span
                className="size-2"
                style={{ background: entryTypeColor(k) }}
                aria-hidden
              />
              {pct.toFixed(0)}%
            </span>
          );
        })}
      </div>
    </div>
  );
}

const METRIC_ROWS: Array<{
  key: string;
  label: string;
  render: (d: AgencyCompareData) => React.ReactNode;
}> = [
  {
    key: "total",
    label: "Total use cases",
    render: (d) => formatNumber(d.total_use_cases),
  },
  {
    key: "products",
    label: "Distinct products",
    render: (d) => formatNumber(d.distinct_products_deployed),
  },
  {
    key: "general_llm",
    label: "General LLM count",
    render: (d) => formatNumber(d.general_llm_count),
  },
  {
    key: "coding",
    label: "Coding tool count",
    render: (d) => formatNumber(d.coding_tool_count),
  },
  {
    key: "agentic",
    label: "Agentic AI count",
    render: (d) => formatNumber(d.agentic_ai_count),
  },
  {
    key: "custom",
    label: "Custom system count",
    render: (d) => formatNumber(d.custom_system_count),
  },
  {
    key: "pct_deployed",
    label: "% deployed",
    render: (d) => formatPercent(d.pct_deployed),
  },
  {
    key: "pct_high_impact",
    label: "% high impact",
    render: (d) => formatPercent(d.pct_high_impact),
  },
  {
    key: "pct_risk",
    label: "% with risk docs",
    render: (d) => formatPercent(d.pct_with_risk_docs),
  },
  {
    key: "yoy",
    label: "YoY growth",
    render: (d) => (
      <span
        className={
          d.year_over_year_growth == null
            ? "text-muted-foreground"
            : d.year_over_year_growth > 0
              ? "text-[var(--verified)]"
              : d.year_over_year_growth < 0
                ? "text-[var(--stamp)]"
                : ""
        }
      >
        {formatYoY(d.year_over_year_growth)}
      </span>
    ),
  },
  {
    key: "enterprise_llm",
    label: "Has enterprise LLM",
    render: (d) => <Bool v={d.has_enterprise_llm} />,
  },
  {
    key: "coding_assistants",
    label: "Has coding assistants",
    render: (d) => <Bool v={d.has_coding_assistants} />,
  },
];

/** Tier tone for MonoChip. */
function tierTone(
  tier: string | null | undefined,
): "verified" | "stamp" | "ink" | "muted" {
  switch (tier) {
    case "leading":
      return "verified";
    case "progressing":
      return "ink";
    case "early":
      return "stamp";
    case "minimal":
      return "muted";
    default:
      return "muted";
  }
}

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ a?: string | string[] }>;
}) {
  const sp = await searchParams;
  const raw = parseAbbrs(sp.a);
  const options = getAgencies().map((a) => ({
    id: a.id,
    name: a.name,
    abbreviation: a.abbreviation,
  }));

  // Resolve to canonical abbreviations (case-insensitive), keep order, cap at 4.
  const optionSet = new Map(
    options.map((o) => [o.abbreviation.toUpperCase(), o.abbreviation]),
  );
  const selected: string[] = [];
  for (const s of raw) {
    const canon = optionSet.get(s.toUpperCase());
    if (canon && !selected.includes(canon)) selected.push(canon);
    if (selected.length >= 4) break;
  }

  const compareData: AgencyCompareData[] = selected
    .map((abbr) => getAgencyCompareData(abbr))
    .filter((d): d is AgencyCompareData => d !== null);

  const gridTemplate =
    compareData.length === 0
      ? "grid-cols-1"
      : compareData.length === 1
        ? "grid-cols-[200px_1fr]"
        : compareData.length === 2
          ? "grid-cols-[200px_1fr_1fr]"
          : compareData.length === 3
            ? "grid-cols-[200px_1fr_1fr_1fr]"
            : "grid-cols-[200px_1fr_1fr_1fr_1fr]";

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8 md:py-14">
      {/* ---------------------------------------------------------------- */}
      {/* Editorial masthead                                                */}
      {/* ---------------------------------------------------------------- */}
      <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-12">
        <aside className="col-span-12 mb-8 md:col-span-3 md:mb-0">
          <div className="sticky top-32 space-y-3">
            <div className="eyebrow !text-[var(--stamp)]">§ II · Compare</div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              Cross-section · Up to 4
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              {selected.length === 0
                ? "None selected"
                : `${selected.length} selected`}
            </div>
            <p className="max-w-xs border-t border-border pt-3 text-sm leading-snug text-muted-foreground">
              Pick two to four agencies and line them up across volume,
              capability mix, entry types, and the key flags. The URL carries
              the selection.
            </p>
          </div>
        </aside>

        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display text-[clamp(2.8rem,7vw,5.6rem)] italic leading-[0.95] tracking-[-0.03em] text-foreground">
            Side by side.
          </h1>
          <p className="mt-8 max-w-prose text-[1.02rem] leading-[1.55] text-foreground/85">
            A ledger-style comparison of agencies&rsquo; 2025 AI inventories.
            Agencies run across the top; metrics run down the left. Numbers
            are in tabular mono; charts reveal the shape of each
            portfolio.
          </p>
        </div>
      </header>

      {/* ---------------------------------------------------------------- */}
      {/* Picker                                                            */}
      {/* ---------------------------------------------------------------- */}
      <section className="mt-12">
        <div className="mb-3 flex items-baseline justify-between gap-4 border-b border-border pb-2">
          <div className="eyebrow">Selection</div>
          <div className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-muted-foreground">
            {selected.length}/4 agencies
          </div>
        </div>
        <ComparePicker options={options} selected={selected} />
      </section>

      {compareData.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="mt-16 space-y-16">
          {/* Metric ledger ------------------------------------------------ */}
          <Figure
            eyebrow="Fig. 1 · Metric ledger"
            caption="Agencies across the top, metrics down the side. Numbers in tabular mono."
          >
            <div className="overflow-x-auto">
              <div className={`grid ${gridTemplate} min-w-[720px]`}>
                {/* Header row: metric label column + agency header cells */}
                <div className="border-b-2 border-foreground bg-transparent px-3 py-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  Metric
                </div>
                {compareData.map((d) => (
                  <div
                    key={d.id}
                    className="border-b-2 border-foreground px-3 py-3"
                  >
                    <Link
                      href={`/agencies/${d.abbreviation}`}
                      className="group flex items-center gap-2"
                    >
                      <MonoChip tone="ink" size="sm">
                        {d.abbreviation}
                      </MonoChip>
                      <ArrowRight className="size-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                    </Link>
                    <p className="mt-1.5 line-clamp-2 font-display text-[0.98rem] italic leading-tight text-foreground">
                      {d.name}
                    </p>
                    <div className="mt-2">
                      <MonoChip tone={tierTone(d.maturity_tier)} size="xs">
                        {maturityTierLabel(d.maturity_tier)}
                      </MonoChip>
                    </div>
                  </div>
                ))}

                {/* Metric rows */}
                {METRIC_ROWS.map((row, rowIdx) => (
                  <React.Fragment key={row.key}>
                    <div
                      className={`px-3 py-2.5 font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground ${
                        rowIdx < METRIC_ROWS.length - 1
                          ? "border-b border-border"
                          : ""
                      }`}
                    >
                      {row.label}
                    </div>
                    {compareData.map((d) => (
                      <div
                        key={`${row.key}-${d.id}`}
                        className={`px-3 py-2.5 font-mono text-[13px] tabular-nums text-foreground ${
                          rowIdx < METRIC_ROWS.length - 1
                            ? "border-b border-border"
                            : ""
                        }`}
                      >
                        {row.render(d)}
                      </div>
                    ))}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </Figure>

          {/* Entry-type strips ------------------------------------------- */}
          <Figure
            eyebrow="Fig. 2 · Entry-type mix"
            caption="Shape of each inventory — COTS deployments, custom builds, generic patterns."
          >
            <div className="space-y-4 pt-2">
              {compareData.map((d) => (
                <div
                  key={d.id}
                  className="grid grid-cols-[100px_1fr] items-start gap-4 border-b border-border pb-3 last:border-0 last:pb-0"
                >
                  <Link
                    href={`/agencies/${d.abbreviation}`}
                    className="shrink-0"
                  >
                    <MonoChip tone="ink" size="sm">
                      {d.abbreviation}
                    </MonoChip>
                  </Link>
                  <EntryTypeStrip mix={d.entry_type_mix} />
                </div>
              ))}
            </div>
          </Figure>

          {/* AI sophistication donuts ------------------------------------ */}
          <Figure
            eyebrow="Fig. 3 · AI sophistication mix"
            caption="Tag-based breakdown of each agency's inventory by model / tool class."
          >
            <div
              className={`grid gap-x-6 gap-y-8 pt-2 ${
                compareData.length === 1
                  ? "sm:grid-cols-1"
                  : compareData.length === 2
                    ? "sm:grid-cols-2"
                    : "sm:grid-cols-2 lg:grid-cols-4"
              }`}
            >
              {compareData.map((d) => {
                const total = d.ai_sophistication_mix.reduce(
                  (acc, r) => acc + r.count,
                  0,
                );
                return (
                  <div key={d.id} className="flex flex-col items-center">
                    <div className="mb-3 text-center">
                      <Link href={`/agencies/${d.abbreviation}`}>
                        <MonoChip tone="ink" size="sm">
                          {d.abbreviation}
                        </MonoChip>
                      </Link>
                      <p className="mt-1.5 font-display text-[0.95rem] italic leading-tight text-foreground">
                        {d.name}
                      </p>
                    </div>
                    <div className="w-full">
                      <DonutChart
                        data={d.ai_sophistication_mix}
                        height={200}
                        centerLabel={String(total)}
                        centerSubLabel="entries"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Figure>

          {/* Top products per agency ------------------------------------- */}
          <Figure
            eyebrow="Fig. 4 · Top products"
            caption="Five most-deployed products at each agency, by individual-use-case count."
          >
            <div
              className={`grid gap-x-8 gap-y-6 pt-2 ${
                compareData.length === 1
                  ? "sm:grid-cols-1"
                  : compareData.length === 2
                    ? "sm:grid-cols-2"
                    : "sm:grid-cols-2 lg:grid-cols-4"
              }`}
            >
              {compareData.map((d) => (
                <div key={d.id}>
                  <div className="mb-3 border-b border-border pb-2">
                    <MonoChip tone="ink" size="sm">
                      {d.abbreviation}
                    </MonoChip>
                  </div>
                  {d.top_products.length === 0 ? (
                    <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                      No product-linked use cases.
                    </p>
                  ) : (
                    <ul className="space-y-1.5 text-sm">
                      {d.top_products.map((p) => (
                        <li
                          key={p.id}
                          className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5 last:border-0"
                        >
                          <Link
                            href={`/products/${p.id}`}
                            className="truncate font-display italic text-foreground transition-colors hover:text-[var(--stamp)]"
                            title={p.canonical_name}
                          >
                            {p.canonical_name}
                          </Link>
                          <span className="shrink-0 font-mono text-[11px] tabular-nums text-muted-foreground">
                            {p.use_case_count}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </Figure>
        </div>
      )}
    </div>
  );
}

/**
 * Empty state shown when no agencies are selected. Uses outlined, mono,
 * `border-2 border-foreground` quick-start buttons.
 */
function EmptyState() {
  return (
    <div className="mt-16 border-t-2 border-foreground pt-8">
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-6 text-center">
        <p className="font-display text-[1.4rem] italic leading-snug text-foreground">
          Pick two to four agencies above to line up their AI inventories side
          by side.
        </p>
        <p className="max-w-md text-sm leading-snug text-muted-foreground">
          You&rsquo;ll see volume, capability mix, entry-type distribution, top
          products, and the key binary flags — enterprise LLM, coding tools —
          in a single grid.
        </p>
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          <QuickStart href="/compare?a=HHS&a=DHS" primary>
            Compare HHS vs DHS
          </QuickStart>
          <QuickStart href="/compare?a=VA&a=USDA&a=DOJ">
            VA · USDA · DOJ
          </QuickStart>
          <QuickStart href="/compare?a=NASA&a=DOE&a=NSF&a=Commerce">
            NASA · DOE · NSF · Commerce
          </QuickStart>
        </div>
      </div>
    </div>
  );
}

function QuickStart({
  href,
  children,
  primary,
}: {
  href: string;
  children: React.ReactNode;
  primary?: boolean;
}) {
  const base =
    "inline-flex items-center gap-2 border-2 border-foreground bg-background px-4 py-2 font-mono text-[11px] uppercase tracking-[0.14em] text-foreground transition-all hover:italic hover:bg-foreground hover:text-background";
  const primaryExtra = primary ? "bg-foreground text-background" : "";
  return (
    <Link href={href} className={`${base} ${primaryExtra}`}>
      {children}
    </Link>
  );
}
