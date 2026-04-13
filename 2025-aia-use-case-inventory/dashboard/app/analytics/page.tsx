import Link from "next/link";
import {
  getYoYGrowthData,
  getVendorMarketShare,
  getProductAgencyMatrix,
  getMaturityScatterData,
  getArchitectureDistribution,
  getLLMVendorShare,
  getCodingToolAgencies,
  getEnterpriseLLMAgencies,
  getEntryTypeMixByAgency,
  getAnalyticsInsights,
  getGlobalStats,
} from "@/lib/db";
import { formatNumber, formatYoY } from "@/lib/formatting";
import { InsightCard } from "@/components/insight-card";
import { YoYGrowthChart } from "@/components/charts/yoy-growth-chart";
import { VendorShareChart } from "@/components/charts/vendor-share-chart";
import { ProductHeatmap } from "@/components/charts/product-heatmap";
import { MaturityScatter } from "@/components/charts/maturity-scatter";
import {
  ArchitectureDonut,
  LLMVendorDonut,
} from "@/components/charts/architecture-donut";
import { CodingLeaderboard } from "@/components/charts/coding-leaderboard";
import { EntryTypeMixChart } from "@/components/charts/entry-type-mix-chart";
import { Section, Figure } from "@/components/editorial";

export const metadata = {
  title: "Analytics · Federal AI Use Case Inventory",
  description:
    "Ten figures that describe American AI deployment: year-over-year growth, vendor market share, product adoption heatmaps, and other cross-cutting views of the 2025 federal AI inventory.",
};

// Figure index — shown in the sticky left-rail TOC and repeated as the
// eyebrow of each <Figure>. Keep these in sync with the page body.
const FIGURES: Array<{
  num: string;
  id: string;
  title: string;
  section: string;
}> = [
  { num: "01", id: "insights", title: "Headline insights", section: "Adoption" },
  { num: "02", id: "yoy", title: "Year-over-year growth", section: "Growth" },
  { num: "03", id: "vendors", title: "Vendor market share", section: "Market share" },
  { num: "04", id: "heatmap", title: "Product adoption heatmap", section: "Market share" },
  { num: "05", id: "scatter", title: "Maturity × growth × scale", section: "Growth" },
  { num: "06", id: "architecture", title: "Architecture distribution", section: "Adoption" },
  { num: "07", id: "llm-vendors", title: "LLM vendor share", section: "Market share" },
  { num: "08", id: "coding", title: "Coding tool adoption", section: "Reach" },
  { num: "09", id: "enterprise-llm", title: "Enterprise LLM access", section: "Reach" },
  { num: "10", id: "entry-mix", title: "Entry-type mix", section: "Adoption" },
];

export default function AnalyticsPage() {
  const globalStats = getGlobalStats();
  const insights = getAnalyticsInsights();
  const yoy = getYoYGrowthData();
  const vendorShare = getVendorMarketShare();
  const heatmap = getProductAgencyMatrix(15, 20);
  const scatter = getMaturityScatterData();
  const architecture = getArchitectureDistribution();
  const llmVendors = getLLMVendorShare();
  const coding = getCodingToolAgencies();
  const enterpriseLLM = getEnterpriseLLMAgencies();
  const entryMix = getEntryTypeMixByAgency();

  const codingRows = coding.map((c) => ({
    abbreviation: c.abbreviation,
    name: c.name,
    value: c.coding_tool_count,
  }));

  const enterpriseLLMRows = enterpriseLLM
    .filter((r) => r.has_enterprise_llm === 1)
    .map((r) => ({
      abbreviation: r.abbreviation,
      name: r.name,
      value: r.general_llm_count,
      subLabel: "enterprise LLM",
    }));

  const llmVendorTotal = llmVendors.reduce((acc, r) => acc + r.count, 0);

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-14 md:px-8 md:py-20">
      {/* ------------------------------------------------------------ */}
      {/* HERO — nameplate + drop-cap lede                              */}
      {/* ------------------------------------------------------------ */}
      <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-12 md:pb-16">
        <aside className="col-span-12 mb-8 md:col-span-3 md:mb-0">
          <div className="sticky top-32 space-y-4">
            <div>
              <div className="eyebrow mb-1.5 !text-[var(--stamp)]">
                § Analytics / Volume I
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Data Supplement
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Cycle 2025 · Ten Figures
              </div>
            </div>

            <div className="hidden space-y-3 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground md:block">
              <div className="border-t border-border pt-3">
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Corpus
                </div>
                <div className="text-foreground">
                  {formatNumber(globalStats.total_use_cases)} uc ·{" "}
                  {globalStats.total_agencies_with_data} ag
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Method
                </div>
                <div className="text-foreground">
                  live from sqlite
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display text-[clamp(2.6rem,6.5vw,5.4rem)] leading-[0.95] tracking-[-0.03em] text-foreground">
            Ten{" "}
            <em className="inline font-normal italic">figures</em>{" "}
            that describe
            <br />
            American AI
            <br />
            <span className="relative inline-block">
              <span
                aria-hidden
                className="absolute inset-x-[-0.08em] bottom-[0.16em] h-[0.38em] bg-[var(--highlight)]/90"
              />
              <span className="relative">deployment.</span>
            </span>
          </h1>

          <p className="mt-10 max-w-prose text-[1.05rem] leading-[1.55] text-foreground/85">
            <span className="float-left mr-2 font-display italic text-[3.6rem] leading-[0.82] text-foreground">
              {formatNumber(globalStats.total_use_cases).slice(0, 1)}
            </span>
            <span>
              {formatNumber(globalStats.total_use_cases).slice(1)} use cases
            </span>{" "}
            from{" "}
            <span className="font-medium text-foreground">
              {formatNumber(globalStats.total_agencies_with_data)} agencies
            </span>
            , reduced to patterns you can actually reason about. Charts are
            interactive — hover for tooltips, click through to filtered
            use-case lists, toggle between views. The four themes below move
            from <em className="italic">what is deployed</em> through{" "}
            <em className="italic">who deploys it</em>, <em className="italic">
              how fast
            </em>
            , and <em className="italic">how widely</em>.
          </p>
        </div>
      </header>

      {/* ------------------------------------------------------------ */}
      {/* Left-rail index                                               */}
      {/* ------------------------------------------------------------ */}
      <nav
        aria-label="Figures index"
        className="mt-10 grid grid-cols-12 gap-x-6"
      >
        <div className="col-span-12 md:col-span-3">
          <div className="eyebrow mb-3">Index of figures</div>
        </div>
        <ol className="col-span-12 grid grid-cols-1 gap-y-1 border-t-2 border-foreground pt-3 md:col-span-9 md:grid-cols-2">
          {FIGURES.map((f) => (
            <li
              key={f.id}
              className="flex items-baseline gap-3 border-b border-dotted border-border py-1.5 font-mono text-[11px] uppercase tracking-[0.1em]"
            >
              <span className="w-8 tabular-nums text-muted-foreground">
                {f.num}
              </span>
              <Link
                href={`#${f.id}`}
                className="flex-1 text-foreground hover:text-[var(--stamp)]"
              >
                {f.title}
              </Link>
              <span className="text-muted-foreground">{f.section}</span>
            </li>
          ))}
        </ol>
      </nav>

      {/* ------------------------------------------------------------ */}
      {/* § I — ADOPTION                                                */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="I"
        title="Adoption"
        lede="The numbers that set up every chart below, and the shape of what agencies are putting into production."
      >
        <div
          id="insights"
          className="scroll-mt-32 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          <InsightCard
            kicker="A · Enterprise LLM"
            value={`${insights.cfo_act_with_enterprise_llm}/${insights.cfo_act_total}`}
            accent="ink"
            headline={
              <>
                CFO Act agencies with enterprise LLM access in their
                inventory.
              </>
            }
            subtext="Having an enterprise-wide chatbot is nearly table stakes now — but far from universal."
          />
          <InsightCard
            kicker="B · Coding"
            value={formatNumber(insights.github_copilot_agencies)}
            accent="verified"
            headline={<>Agencies that reported deploying GitHub Copilot.</>}
            subtext="Coding copilots are the single fastest-adopted AI category in government."
          />
          <InsightCard
            kicker="C · Top product"
            value={formatNumber(insights.top_product_agencies)}
            accent="ink"
            headline={
              <>
                Agencies deployed{" "}
                <span className="italic">
                  {insights.top_product_name ?? "the leading product"}
                </span>{" "}
                — more than any other product.
              </>
            }
            subtext="COTS dominance is concentrated at the very top of the long tail."
          />
          <InsightCard
            kicker="D · Gap"
            value={formatNumber(insights.zero_coding_agencies)}
            accent="stamp"
            headline={
              <>Agencies reported zero coding tools in their inventory.</>
            }
            subtext="Whether that means truly zero adoption or under-reporting is one of the biggest open questions in the data."
          />
          <InsightCard
            kicker="E · Catalogue"
            value={formatNumber(insights.distinct_products_total)}
            accent="ink"
            headline={
              <>
                Distinct products deployed across the entire federal
                government.
              </>
            }
            subtext="After canonical-name deduplication across 3,600+ raw entries."
          />
          <InsightCard
            kicker="F · Outlier"
            value={
              insights.nasa_yoy_growth != null
                ? formatYoY(insights.nasa_yoy_growth)
                : "—"
            }
            accent="stamp"
            headline={<>NASA's year-over-year growth in reported use cases.</>}
            subtext="The largest outlier in the dataset — see Fig. 02 and Fig. 05."
          />
        </div>

        <p
          id="architecture-note"
          className="mt-14 max-w-prose text-xs text-muted-foreground"
        >
          Architecture inferences require explicit source evidence. ~70% are marked &quot;unknown&quot; to preserve uncertainty.
        </p>
        <div
          id="architecture"
          className="scroll-mt-32 mt-4 grid gap-x-6 gap-y-10 md:grid-cols-2"
        >
          <Figure
            eyebrow="Fig. 06 · Architecture type"
            caption="Inference-only deployments dominate; very little custom training."
          >
            <ArchitectureDonut data={architecture} />
          </Figure>
          <Figure
            eyebrow="Fig. 10 · Entry-type mix"
            caption={
              <span id="entry-mix" className="scroll-mt-32">
                Segments are the derived <code>tag.entry_type</code>:
                product_deployment (COTS/SaaS), custom_system (bespoke
                in-house), generic_use_pattern (&quot;employees use
                ChatGPT&quot;), and so on. Normalize to percent to compare
                agencies of different sizes.
              </span>
            }
          >
            <EntryTypeMixChart data={entryMix} />
          </Figure>
        </div>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § II — MARKET SHARE                                           */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="II"
        title="Market share"
        lede="Who is selling, who is installed, and at how many doors — vendor reach versus vendor footprint."
      >
        <div id="vendors" className="scroll-mt-32 space-y-14">
          <Figure
            eyebrow="Fig. 03 · Vendor share"
            caption="Distinct agencies and total use-case entries for each vendor. Microsoft dominates reach; everyone else is long-tail."
          >
            <VendorShareChart data={vendorShare} />
          </Figure>

          <div id="heatmap" className="scroll-mt-32">
            <Figure
              eyebrow="Fig. 04 · Product adoption heatmap"
              caption="Top 15 products (rows) × top 20 agencies (columns). Darker ink = more reported use cases. Click a cell to drill into the matching entries."
            >
              <ProductHeatmap data={heatmap} />
            </Figure>
          </div>

          <div id="llm-vendors" className="scroll-mt-32">
            <Figure
              eyebrow="Fig. 07 · LLM vendor share"
              caption={
                <>
                  Among the {formatNumber(llmVendorTotal)} general-LLM-access
                  entries.
                </>
              }
            >
              <div className="mx-auto max-w-xl">
                <LLMVendorDonut data={llmVendors} />
              </div>
            </Figure>
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § III — GROWTH                                                */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="III"
        title="Growth"
        lede="Which agencies grew, which shrank, and whether fast growth implies real maturity."
      >
        <div id="yoy" className="scroll-mt-32 space-y-14">
          <Figure
            eyebrow="Fig. 02 · Year-over-year growth"
            caption={
              <>
                Change in reported use cases, 2024 → 2025. Each bar is an
                agency; bars tinted vermilion exceed +500%. NASA's bar is off
                the scale. Source:{" "}
                <code>agency_ai_maturity.year_over_year_growth</code>.
              </>
            }
          >
            <YoYGrowthChart data={yoy} />
          </Figure>

          <div id="scatter" className="scroll-mt-32">
            <Figure
              eyebrow="Fig. 05 · Maturity × growth × scale"
              caption={
                <>
                  Dots are agencies. Position shows growth (x) and reported
                  volume (y); color shows maturity tier. Several &quot;early&quot;
                  agencies are the highest-growth ones, while &quot;leading&quot;
                  agencies tend to have plateaued at higher volumes.
                </>
              }
            >
              <MaturityScatter data={scatter} />
            </Figure>
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § IV — REACH                                                  */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="IV"
        title="Reach"
        lede="Two adoption leaderboards that tell very different stories about how far a technology has spread."
      >
        <div className="grid gap-x-6 gap-y-10 md:grid-cols-2">
          <div id="coding" className="scroll-mt-32">
            <Figure
              eyebrow="Fig. 08 · Coding tool adoption"
              caption="Top 20 agencies by count of coding-assistant use cases. Click an agency to see the underlying inventory."
            >
              <CodingLeaderboard
                rows={codingRows}
                color="var(--verified)"
                unit="coding tool entries"
              />
            </Figure>
          </div>
          <div id="enterprise-llm" className="scroll-mt-32">
            <Figure
              eyebrow="Fig. 09 · Enterprise LLM distribution"
              caption="Agencies with enterprise-wide LLM access, sorted by general-LLM entries in their inventory."
            >
              <CodingLeaderboard
                rows={enterpriseLLMRows}
                color="var(--ink)"
                unit="general-LLM entries"
              />
            </Figure>
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* Colophon                                                      */}
      {/* ------------------------------------------------------------ */}
      <footer className="mt-24 grid grid-cols-12 gap-x-6 border-t-2 border-foreground pt-6">
        <div className="col-span-12 md:col-span-3">
          <div className="eyebrow !text-[var(--stamp)]">Colophon</div>
        </div>
        <p className="col-span-12 font-mono text-[11px] uppercase tracking-[0.1em] leading-relaxed text-muted-foreground md:col-span-9">
          All figures computed live from the local SQLite inventory.
          {" · "}
          Queries in{" "}
          <code className="bg-muted px-1 py-0.5 text-foreground">
            lib/db.ts
          </code>
          {" · "}
          page at{" "}
          <code className="bg-muted px-1 py-0.5 text-foreground">
            app/analytics/page.tsx
          </code>
          .
        </p>
      </footer>
    </div>
  );
}
