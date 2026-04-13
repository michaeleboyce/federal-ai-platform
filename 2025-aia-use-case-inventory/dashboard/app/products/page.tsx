import {
  getAllProducts,
  getProductNamesById,
  getVendorMarketShare,
} from "@/lib/db";
import { ProductsFilters } from "@/components/products-filters";
import { VendorShareChart } from "@/components/charts/vendor-share-chart";
import { Section, Figure } from "@/components/editorial";
import { formatNumber } from "@/lib/formatting";

export const metadata = {
  title: "Products — Federal AI Use Case Inventory 2025",
  description:
    "Browse the commercial AI products reported by federal agencies, with vendor market share and per-product adoption.",
};

export default function ProductsPage() {
  const products = getAllProducts();
  const parentNames = getProductNamesById();
  const vendorShare = getVendorMarketShare();

  const totalAgencyMentions = products.reduce(
    (acc, p) => acc + (p.agency_count ?? 0),
    0,
  );
  const totalEntries = products.reduce(
    (acc, p) => acc + (p.use_case_count ?? 0),
    0,
  );
  const frontierCount = products.filter((p) => p.is_frontier_llm === 1).length;
  const distinctVendors = new Set(
    products.map((p) => p.vendor).filter((v): v is string => Boolean(v)),
  ).size;

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
                No. 002 · Catalogue
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Commercial Inventory
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Vendor × Product × Agency
              </div>
            </div>

            <div className="hidden space-y-3 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground md:block">
              <div className="border-t border-border pt-3">
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Canonical
                </div>
                <div className="text-foreground">
                  {formatNumber(products.length)} products
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Vendors
                </div>
                <div className="text-foreground">
                  {formatNumber(distinctVendors)}
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Raw mentions
                </div>
                <div className="text-foreground">
                  {formatNumber(Object.keys(parentNames).length)}
                </div>
              </div>
              <div>
                <div className="mb-0.5 text-[9px] text-muted-foreground/70">
                  Frontier LLMs
                </div>
                <div className="text-foreground">
                  {formatNumber(frontierCount)}
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display text-[clamp(2.6rem,7vw,6rem)] leading-[0.95] tracking-[-0.03em] text-foreground">
            All AI{" "}
            <em className="inline font-normal italic">products</em>{" "}
            across
            <br />
            American government,
            <br />
            <span className="relative inline-block">
              <span
                aria-hidden
                className="absolute inset-x-[-0.08em] bottom-[0.16em] h-[0.38em] bg-[var(--highlight)]/90"
              />
              <span className="relative">normalised&nbsp;and&nbsp;deduped.</span>
            </span>
          </h1>

          <div className="mt-10 grid grid-cols-12 gap-x-6 gap-y-6">
            <p className="col-span-12 max-w-prose text-[1.05rem] leading-[1.55] text-foreground/85 md:col-span-7">
              <span className="float-left mr-2 font-display italic text-[3.6rem] leading-[0.82] text-foreground">
                F
              </span>
              ederal agencies name the commercial tools they run in hundreds of
              slightly different ways — &ldquo;M365 Copilot,&rdquo;
              &ldquo;Microsoft 365 Copilot,&rdquo; &ldquo;Copilot for M365.&rdquo;
              This catalogue consolidates{" "}
              <span className="font-medium text-foreground">
                {formatNumber(Object.keys(parentNames).length)} raw product
                mentions
              </span>{" "}
              into {formatNumber(products.length)} canonical products, attributes
              each to its vendor, and tallies the agencies and entries that cite
              it. Filter below by vendor, type, or capability; click any card to
              open agency-level adoption.
            </p>

            <div className="col-span-12 md:col-span-4 md:col-start-9 md:self-end">
              <div className="editorial-rule-left space-y-3">
                <div className="eyebrow">By the numbers</div>
                <dl className="space-y-2 font-mono text-sm">
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">Products</dt>
                    <dd className="tabular-nums text-foreground">
                      {formatNumber(products.length)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">Vendors</dt>
                    <dd className="tabular-nums text-foreground">
                      {formatNumber(distinctVendors)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-3 border-b border-dotted border-border pb-1.5">
                    <dt className="text-muted-foreground">
                      Agency × product
                    </dt>
                    <dd className="tabular-nums text-foreground">
                      {formatNumber(totalAgencyMentions)}
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
      {/* § I — VENDOR MARKET SHARE                                    */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="I"
        title="Who sells"
        lede="The vendors named most often, ranked twice: by distinct agencies and by total entries."
      >
        <Figure
          eyebrow="Fig. 1 · Vendor market share"
          caption={
            <>
              Source: <span className="text-foreground">products</span> joined
              with <span className="text-foreground">use_cases</span>; top 12
              vendors per metric.
            </>
          }
        >
          <VendorShareChart data={vendorShare} />
        </Figure>
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § II — CATALOGUE                                             */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="II"
        title="The catalogue"
        lede="Every canonical product, searchable by name, vendor, type, and capability."
      >
        <ProductsFilters products={products} parentNames={parentNames} />
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
            {formatNumber(products.length)} products ·{" "}
            {formatNumber(distinctVendors)} vendors
          </span>
        </div>
      </footer>
    </div>
  );
}
