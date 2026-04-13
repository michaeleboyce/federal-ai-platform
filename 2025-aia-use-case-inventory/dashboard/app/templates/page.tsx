import { getAllTemplates } from "@/lib/db";
import { TemplatesFilters } from "@/components/templates-filters";
import { CapabilityCategoryChart } from "@/components/charts/capability-category-chart";
import { Section, Figure } from "@/components/editorial";
import { formatNumber } from "@/lib/formatting";

export const metadata = {
  title: "Templates — Federal AI Use Case Inventory 2025",
  description:
    "OMB Appendix B standard use-case templates and the agencies that adopted them verbatim.",
};

export default function TemplatesPage() {
  const templates = getAllTemplates();

  // Aggregate usage by capability_category for the bar chart.
  const byCategory = new Map<string, number>();
  for (const t of templates) {
    const cat = t.capability_category ?? "uncategorized";
    byCategory.set(cat, (byCategory.get(cat) ?? 0) + t.use_case_count);
  }
  const chartData = Array.from(byCategory.entries())
    .map(([category, use_case_count]) => ({ category, use_case_count }))
    .sort((a, b) => b.use_case_count - a.use_case_count);

  const totalEntries = templates.reduce((a, t) => a + t.use_case_count, 0);
  const ombStandard = templates.filter((t) => t.is_omb_standard === 1).length;
  const distinctCategories = byCategory.size;

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-14 md:px-8 md:py-20">
      {/* ------------------------------------------------------------ */}
      {/* HERO — editorial nameplate                                   */}
      {/* ------------------------------------------------------------ */}
      <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-12 md:pb-16">
        <aside className="col-span-12 mb-8 md:col-span-3 md:mb-0">
          <div className="sticky top-32 space-y-4">
            <div>
              <div className="eyebrow mb-1.5 !text-[var(--stamp)]">
                No. 003 · Compendium
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                OMB Appendix B
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Boilerplate language
              </div>
            </div>

            <div className="hidden space-y-3 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground md:block">
              <div className="border-t border-border pt-3">
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Templates
                </div>
                <div className="text-foreground">
                  {formatNumber(templates.length)}
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  OMB standard
                </div>
                <div className="text-foreground">
                  {formatNumber(ombStandard)} of{" "}
                  {formatNumber(templates.length)}
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Categories
                </div>
                <div className="text-foreground">
                  {formatNumber(distinctCategories)}
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Verbatim entries
                </div>
                <div className="text-foreground">
                  {formatNumber(totalEntries)}
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display text-[clamp(2.6rem,7vw,6rem)] leading-[0.95] tracking-[-0.03em] text-foreground">
            The{" "}
            <em className="inline font-normal italic">boilerplate</em> that
            <br />
            most of the federal
            <br />
            <span className="relative inline-block">
              <span
                aria-hidden
                className="absolute inset-x-[-0.08em] bottom-[0.16em] h-[0.38em] bg-[var(--highlight)]/90"
              />
              <span className="relative">
                government&nbsp;copied&nbsp;verbatim.
              </span>
            </span>
          </h1>

          <div className="mt-10 grid grid-cols-12 gap-x-6 gap-y-6">
            <p className="col-span-12 max-w-prose text-[1.05rem] leading-[1.55] text-foreground/85 md:col-span-7">
              <span className="float-left mr-2 font-display italic text-[3.6rem] leading-[0.82] text-foreground">
                O
              </span>
              MB Appendix B supplied agencies with{" "}
              <span className="font-medium text-foreground">
                {formatNumber(ombStandard)} standard use-case templates
              </span>{" "}
              — short capability descriptions like &ldquo;employees use AI to
              summarize meetings.&rdquo; Many agencies filed these verbatim.
              Reviewing them side-by-side surfaces which capabilities the
              federal government most consistently admits to deploying, and
              which agencies went beyond the template to describe bespoke work.
            </p>

            <div className="col-span-12 md:col-span-4 md:col-start-9 md:self-end">
              <div className="editorial-rule-left space-y-3">
                <div className="eyebrow">By the numbers</div>
                <dl className="space-y-2 font-mono text-sm">
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">Templates</dt>
                    <dd className="tabular-nums text-foreground">
                      {formatNumber(templates.length)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">OMB standard</dt>
                    <dd className="tabular-nums text-foreground">
                      {formatNumber(ombStandard)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">Categories</dt>
                    <dd className="tabular-nums text-foreground">
                      {formatNumber(distinctCategories)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3">
                    <dt className="text-muted-foreground">Entries</dt>
                    <dd className="tabular-nums text-foreground">
                      {formatNumber(totalEntries)}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------ */}
      {/* § I — CATEGORY VOLUME                                        */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="I"
        title="Volume by category"
        lede="Which capability categories attracted the most verbatim filings."
      >
        <Figure
          eyebrow="Fig. 1 · Use-case volume by capability"
          caption={
            <>
              Source: <span className="text-foreground">use_case_templates</span>{" "}
              with per-template entry counts aggregated by{" "}
              <span className="text-foreground">capability_category</span>.
            </>
          }
        >
          <CapabilityCategoryChart data={chartData} />
        </Figure>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § II — COMPENDIUM                                            */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="II"
        title="The compendium"
        lede="Every template on file, quoted at display size. Filter by capability or OMB-standard status."
      >
        <TemplatesFilters templates={templates} />
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* Footer caption                                               */}
      {/* ------------------------------------------------------------ */}
      <footer className="mt-20 border-t-2 border-foreground pt-4 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
          <span>
            Filed · Federal AI Use Case Inventory ·{" "}
            <span className="text-foreground">2025 cycle</span>
          </span>
          <span>
            {formatNumber(templates.length)} templates ·{" "}
            {formatNumber(totalEntries)} entries
          </span>
        </div>
      </footer>
    </div>
  );
}
