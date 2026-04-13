import { notFound } from "next/navigation";
import Link from "next/link";
import { ExternalLink } from "lucide-react";

import {
  getAgencyByAbbr,
  getUseCasesForAgency,
  getConsolidatedForAgency,
  getProductsForAgency,
  getBureauBreakdown,
  getEntryTypeBreakdown,
  getAISophisticationBreakdown,
  getDeploymentScopeBreakdown,
} from "@/lib/db";
import {
  formatNumber,
  formatPercent,
  formatYoY,
  formatDate,
  agencyTypeLabel,
  maturityTierLabel,
} from "@/lib/formatting";

import { AgencyHeader } from "@/components/agency-header";
import { CapabilityFlags } from "@/components/capability-flags";
import { ProductGrid } from "@/components/product-grid";
import { BureauBreakdown } from "@/components/bureau-breakdown";
import {
  IndividualUseCasesTable,
  ConsolidatedUseCasesTable,
} from "@/components/agency-use-cases-table";
import { DonutChart } from "@/components/charts/donut-chart";
import { HorizontalBarChart } from "@/components/charts/horizontal-bar-chart";
import { MetricTile } from "@/components/metric-tile";

import {
  Section,
  Figure,
  Eyebrow,
  ENTRY_TYPE_COLORS,
  SOPHISTICATION_COLORS,
  SCOPE_COLORS,
} from "@/components/editorial";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ abbr: string }>;
}) {
  const { abbr } = await params;
  const agency = getAgencyByAbbr(abbr);
  if (!agency) return { title: "Agency not found" };
  return {
    title: `${agency.abbreviation} — ${agency.name} | Federal AI Inventory`,
    description: `2025 AI use case inventory for ${agency.name}`,
  };
}

export default async function AgencyDetailPage({
  params,
}: {
  params: Promise<{ abbr: string }>;
}) {
  const { abbr } = await params;
  const agency = getAgencyByAbbr(abbr);
  if (!agency) notFound();

  const maturity = agency.maturity;

  const individual = getUseCasesForAgency(agency.id);
  const consolidated = getConsolidatedForAgency(agency.id);
  const products = getProductsForAgency(agency.id);
  const bureaus = getBureauBreakdown(agency.id);
  const entryTypeBreakdown = getEntryTypeBreakdown(agency.id);
  const sophisticationBreakdown = getAISophisticationBreakdown(agency.id);
  const scopeBreakdown = getDeploymentScopeBreakdown(agency.id);

  const totalEntries =
    (maturity?.total_use_cases ?? individual.length) +
    (maturity?.total_consolidated_entries ?? consolidated.length);

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8 md:py-14">
      <AgencyHeader agency={agency} />

      {/* Ledger row */}
      <section className="ink-in mt-10 grid grid-cols-2 gap-4 md:mt-14 md:grid-cols-4 lg:grid-cols-7">
        <MetricTile label="Individual use cases" value={individual.length} />
        <MetricTile label="Consolidated entries" value={consolidated.length} />
        <MetricTile
          label="Distinct products"
          value={maturity?.distinct_products_deployed ?? 0}
        />
        <MetricTile label="General LLM" value={maturity?.general_llm_count ?? 0} />
        <MetricTile label="Coding tools" value={maturity?.coding_tool_count ?? 0} />
        <MetricTile label="Agentic AI" value={maturity?.agentic_ai_count ?? 0} />
        <MetricTile
          label="YoY growth"
          value={maturity?.year_over_year_growth ?? 0}
          sublabel={formatYoY(maturity?.year_over_year_growth ?? null)}
        />
      </section>

      {/* § I · Portfolio */}
      <Section
        number="I"
        title="Portfolio"
        lede={`How this agency's ${formatNumber(totalEntries)} reported AI uses break down.`}
      >
        <div className="grid gap-x-6 gap-y-10 md:grid-cols-3">
          <Figure
            eyebrow="Fig. 1 · Entry type"
            caption="Share of entries by structural shape."
          >
            <DonutChart
              data={entryTypeBreakdown}
              colorMap={ENTRY_TYPE_COLORS}
              height={260}
              centerSubLabel="entries"
            />
          </Figure>
          <Figure
            eyebrow="Fig. 2 · AI sophistication"
            caption="Share of entries by AI classification tag."
          >
            <DonutChart
              data={sophisticationBreakdown}
              colorMap={SOPHISTICATION_COLORS}
              height={260}
              centerSubLabel="tagged"
            />
          </Figure>
          <Figure
            eyebrow="Fig. 3 · Deployment scope"
            caption="Where the system is available, by scope."
          >
            <HorizontalBarChart
              data={scopeBreakdown}
              colorMap={SCOPE_COLORS}
              height={260}
              labelWidth={120}
            />
          </Figure>
        </div>
      </Section>

      {/* § II · Capabilities */}
      <Section
        number="II"
        title="Capabilities"
        lede="What the 2025 inventory shows this agency has — and does not have."
      >
        <CapabilityFlags maturity={maturity} />
      </Section>

      {/* § III · Products deployed */}
      <Section
        number="III"
        title="Products deployed"
        lede="Canonical AI products linked across this agency's use cases."
      >
        <ProductGrid products={products} />
      </Section>

      {/* § IV · Bureau breakdown — conditionally rendered */}
      {bureaus.length > 0 ? (
        <Section
          number="IV"
          title="Bureau breakdown"
          lede="Use case counts by bureau or component."
        >
          <BureauBreakdown rows={bureaus} />
        </Section>
      ) : null}

      {/* § V · Use cases */}
      <Section
        number={bureaus.length > 0 ? "V" : "IV"}
        title="Use cases"
        lede="Every 2025 entry linked to this agency."
      >
        <Tabs defaultValue="individual">
          <TabsList className="flex h-auto w-full justify-start gap-0 border-b border-border bg-transparent p-0">
            <TabsTrigger
              value="individual"
              className="h-auto rounded-none border-b-2 border-transparent bg-transparent px-4 py-2 font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground shadow-none data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none"
            >
              Individual ({formatNumber(individual.length)})
            </TabsTrigger>
            <TabsTrigger
              value="consolidated"
              className="h-auto rounded-none border-b-2 border-transparent bg-transparent px-4 py-2 font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground shadow-none data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none"
            >
              Consolidated ({formatNumber(consolidated.length)})
            </TabsTrigger>
          </TabsList>
          <TabsContent value="individual" className="pt-6">
            <IndividualUseCasesTable rows={individual} />
          </TabsContent>
          <TabsContent value="consolidated" className="pt-6">
            <ConsolidatedUseCasesTable rows={consolidated} />
          </TabsContent>
        </Tabs>
      </Section>

      {/* § VI · Colophon — filing metadata */}
      <Section
        number={bureaus.length > 0 ? "VI" : "V"}
        title="Colophon"
        lede="Filing metadata for this record."
      >
        <div className="border-t-2 border-foreground pt-4">
          <Eyebrow color="stamp">§ Filing</Eyebrow>
          <dl className="mt-3 grid gap-x-8 gap-y-3 font-mono text-[11px] uppercase tracking-[0.12em] sm:grid-cols-2">
            <Colophon label="Agency type" value={agencyTypeLabel(agency.agency_type)} />
            <Colophon label="Status" value={agency.status ?? "—"} />
            <Colophon
              label="Maturity tier"
              value={maturityTierLabel(maturity?.maturity_tier ?? null)}
            />
            <Colophon
              label="Schema compliance"
              value={
                agency.schema_compliance != null
                  ? formatPercent(agency.schema_compliance)
                  : "—"
              }
            />
            <Colophon label="Last modified" value={formatDate(agency.last_modified)} />
            <Colophon label="Date accessed" value={formatDate(agency.date_accessed)} />
          </dl>

          {agency.notes ? (
            <div className="mt-6 border-t border-dotted border-border pt-4">
              <Eyebrow>Notes</Eyebrow>
              <p className="mt-2 whitespace-pre-wrap font-body text-sm leading-relaxed text-foreground/90">
                {agency.notes}
              </p>
            </div>
          ) : null}

          {agency.csv_download_url ? (
            <div className="mt-6 border-t border-dotted border-border pt-4">
              <Link
                href={agency.csv_download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.16em] text-foreground hover:text-[var(--stamp)]"
              >
                Source CSV
                <ExternalLink className="h-3 w-3" aria-hidden />
              </Link>
            </div>
          ) : null}
        </div>
      </Section>
    </div>
  );
}

function Colophon({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="tabular-nums text-foreground">{value}</dd>
    </div>
  );
}
