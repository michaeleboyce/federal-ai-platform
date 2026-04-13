import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getAllProducts,
  getChildProducts,
  getConsolidatedCountForProduct,
  getProductById,
  getProductsByVendor,
  getUseCasesForProduct,
} from "@/lib/db";
import { ProductCard } from "@/components/product-card";
import { Section, MonoChip, Eyebrow } from "@/components/editorial";
import { formatNumber, humanize, truncate } from "@/lib/formatting";

type ProductPageProps = { params: Promise<{ id: string }> };

export async function generateMetadata(props: ProductPageProps) {
  const { id } = await props.params;
  const idNum = Number(id);
  if (!Number.isFinite(idNum)) return { title: "Product — not found" };
  const product = getProductById(idNum);
  if (!product) return { title: "Product — not found" };
  return {
    title: `${product.canonical_name} — Federal AI Inventory`,
    description: product.description ?? undefined,
  };
}

export default async function ProductDetailPage(props: ProductPageProps) {
  const { id } = await props.params;
  const idNum = Number(id);
  if (!Number.isFinite(idNum)) notFound();

  const product = getProductById(idNum);
  if (!product) notFound();

  const useCases = getUseCasesForProduct(idNum);
  const consolidatedCount = getConsolidatedCountForProduct(idNum);
  const children = getChildProducts(idNum);

  let parent: { id: number; canonical_name: string } | null = null;
  if (product.parent_product_id != null) {
    const p = getProductById(product.parent_product_id);
    if (p) parent = { id: p.id, canonical_name: p.canonical_name };
  }

  const related = product.vendor
    ? getProductsByVendor(product.vendor, product.id).slice(0, 8)
    : [];

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8 md:py-14">
      {/* Breadcrumb */}
      <nav className="mb-6 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
        <Link
          href="/products"
          className="hover:text-[var(--stamp)]"
        >
          ← All products
        </Link>
      </nav>

      {/* ------------------------------------------------------------ */}
      {/* HERO                                                         */}
      {/* ------------------------------------------------------------ */}
      <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-12">
        <aside className="col-span-12 mb-8 md:col-span-3 md:mb-0">
          <div className="sticky top-32 space-y-4">
            <div>
              <div className="eyebrow mb-1.5 !text-[var(--stamp)]">
                Product № {String(product.id).padStart(3, "0")}
              </div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                {product.vendor ?? "Unknown vendor"}
              </div>
              {product.product_type ? (
                <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                  {humanize(product.product_type)}
                </div>
              ) : null}
            </div>

            <div className="flex flex-wrap gap-1.5">
              {product.is_frontier_llm === 1 ? (
                <MonoChip tone="stamp" size="xs">
                  Frontier
                </MonoChip>
              ) : null}
              {product.is_generative_ai === 1 ? (
                <MonoChip tone="ink" size="xs">
                  GenAI
                </MonoChip>
              ) : null}
              {parent ? (
                <MonoChip
                  tone="muted"
                  size="xs"
                  href={`/products/${parent.id}`}
                  title={`Part of: ${parent.canonical_name}`}
                >
                  ⤷ {parent.canonical_name}
                </MonoChip>
              ) : null}
            </div>
          </div>
        </aside>

        <div className="col-span-12 md:col-span-9">
          <h1 className="font-display italic text-[clamp(2.4rem,6vw,5rem)] leading-[0.98] tracking-[-0.02em] text-foreground">
            {product.canonical_name}
          </h1>

          {product.vendor ? (
            <div className="mt-3 font-mono text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
              by <span className="text-foreground">{product.vendor}</span>
            </div>
          ) : null}

          {product.description ? (
            <p className="mt-8 max-w-prose text-[1.05rem] leading-[1.55] text-foreground/85">
              {product.description}
            </p>
          ) : null}

          {product.notes ? (
            <p className="mt-3 max-w-prose font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
              Notes · {product.notes}
            </p>
          ) : null}

          {/* Stat ledger */}
          <div className="mt-10 grid grid-cols-3 gap-x-6 border-t-2 border-foreground pt-4">
            <StatCell label="Agencies" value={product.agencies.length} />
            <StatCell label="Total entries" value={product.use_case_count} />
            <StatCell
              label="Consolidated"
              value={consolidatedCount}
            />
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------ */}
      {/* § I — ALIASES + SUBPRODUCTS                                  */}
      {/* ------------------------------------------------------------ */}
      {product.aliases.length > 0 || children.length > 0 ? (
        <Section
          number="I"
          title="Also filed as"
          lede="Raw names and sub-products folded into this canonical record."
        >
          <div className="space-y-8">
            {product.aliases.length > 0 ? (
              <div>
                <Eyebrow color="stamp">§ Aliases</Eyebrow>
                <ul className="mt-3 flex flex-wrap gap-1.5">
                  {product.aliases.map((alias) => (
                    <li key={alias}>
                      <MonoChip tone="muted" size="xs">
                        {alias}
                      </MonoChip>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {children.length > 0 ? (
              <div>
                <Eyebrow color="stamp">
                  § Sub-products ({children.length})
                </Eyebrow>
                <ul className="mt-3 flex flex-wrap gap-1.5">
                  {children.map((c) => (
                    <li key={c.id}>
                      <MonoChip
                        tone="ink"
                        size="sm"
                        href={`/products/${c.id}`}
                      >
                        {c.canonical_name}
                      </MonoChip>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </Section>
      ) : null}

      {/* ------------------------------------------------------------ */}
      {/* § II — AGENCIES USING                                        */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="II"
        title="Who runs it"
        lede={`${formatNumber(product.agencies.length)} agencies report this product. Ranked by distinct entries.`}
      >
        {product.agencies.length === 0 ? (
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            — No agencies reported this product —
          </p>
        ) : (
          <ul className="divide-y divide-border border-y-2 border-foreground">
            {product.agencies.map((a, i) => (
              <li
                key={a.id}
                className="group grid grid-cols-[2.25rem_4.5rem_1fr_auto] items-baseline gap-x-3 py-3 md:grid-cols-[2.75rem_5rem_1fr_auto] md:gap-x-5"
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
                  className="truncate font-display text-[1.05rem] italic text-foreground transition-[letter-spacing] group-hover:tracking-[-0.01em]"
                >
                  {a.name}
                </Link>
                <span className="font-mono text-[11px] uppercase tracking-[0.1em] tabular-nums text-muted-foreground">
                  {formatNumber(a.count)} entries
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § III — LINKED USE CASES                                     */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="III"
        title="Linked entries"
        lede={`${formatNumber(useCases.length)} individual use cases reference this product.`}
      >
        {useCases.length === 0 ? (
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            — No detailed use cases reference this product —
          </p>
        ) : (
          <>
            <ul className="divide-y divide-border border-y-2 border-foreground">
              {useCases.slice(0, 200).map((uc) => (
                <li
                  key={uc.id}
                  className="grid grid-cols-[4rem_1fr_auto] items-baseline gap-x-4 py-3 md:grid-cols-[4rem_1fr_10rem_auto]"
                >
                  <Link
                    href={`/agencies/${uc.agency_abbreviation}`}
                    className="font-mono text-[11px] font-semibold uppercase tracking-[0.06em] text-foreground hover:text-[var(--stamp)]"
                  >
                    {uc.agency_abbreviation}
                  </Link>
                  <div className="min-w-0">
                    {uc.slug ? (
                      <Link
                        href={`/use-cases/${uc.slug}`}
                        className="font-display text-[1rem] italic leading-snug text-foreground hover:text-[var(--stamp)]"
                      >
                        {truncate(uc.use_case_name, 120)}
                      </Link>
                    ) : (
                      <span className="font-display text-[1rem] italic leading-snug text-foreground">
                        {truncate(uc.use_case_name, 120)}
                      </span>
                    )}
                    {uc.bureau_component ? (
                      <div className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
                        {truncate(uc.bureau_component, 60)}
                      </div>
                    ) : null}
                  </div>
                  <span className="hidden font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground md:inline">
                    {uc.stage_of_development ?? "—"}
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    {uc.tags?.entry_type
                      ? humanize(uc.tags.entry_type)
                      : "—"}
                  </span>
                </li>
              ))}
            </ul>
            {useCases.length > 200 ? (
              <p className="mt-3 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Showing first 200 of {formatNumber(useCases.length)} entries.
              </p>
            ) : null}
          </>
        )}
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § IV — RELATED                                               */}
      {/* ------------------------------------------------------------ */}
      {related.length > 0 ? (
        <Section
          number="IV"
          title={`More from ${product.vendor}`}
          lede="Other products by the same vendor filed in this year's inventory."
        >
          <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {related.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </Section>
      ) : null}

      {/* ------------------------------------------------------------ */}
      {/* Footer caption                                               */}
      {/* ------------------------------------------------------------ */}
      <footer className="mt-20 border-t-2 border-foreground pt-4 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
          <span>
            Product record ·{" "}
            <span className="text-foreground">
              {product.canonical_name}
            </span>
          </span>
          <span>
            {formatNumber(product.agencies.length)} agencies ·{" "}
            {formatNumber(product.use_case_count)} entries
          </span>
        </div>
      </footer>
    </div>
  );
}

function StatCell({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-display text-[2.2rem] leading-none tabular-nums text-foreground md:text-[2.8rem]">
        {formatNumber(value)}
      </div>
    </div>
  );
}

// Pre-render known product IDs at build time.
export function generateStaticParams() {
  return getAllProducts().map((p) => ({ id: String(p.id) }));
}
