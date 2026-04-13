import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getAllTemplates,
  getEntriesForTemplate,
  getTemplateById,
} from "@/lib/db";
import { Section, MonoChip } from "@/components/editorial";
import { formatNumber, humanize, truncate } from "@/lib/formatting";

type TemplatePageProps = { params: Promise<{ id: string }> };

export async function generateMetadata(props: TemplatePageProps) {
  const { id } = await props.params;
  const idNum = Number(id);
  if (!Number.isFinite(idNum)) return { title: "Template — not found" };
  const template = getTemplateById(idNum);
  if (!template) return { title: "Template — not found" };
  return {
    title: `${template.short_name ?? "Template"} — Federal AI Inventory`,
    description: template.template_text,
  };
}

export default async function TemplateDetailPage(props: TemplatePageProps) {
  const { id } = await props.params;
  const idNum = Number(id);
  if (!Number.isFinite(idNum)) notFound();

  const template = getTemplateById(idNum);
  if (!template) notFound();

  const entries = getEntriesForTemplate(idNum);

  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8 md:py-14">
      {/* Breadcrumb */}
      <nav className="mb-6 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
        <Link
          href="/templates"
          className="hover:text-[var(--stamp)]"
        >
          ← All templates
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
                Template № {String(template.id).padStart(3, "0")}
              </div>
              {template.short_name ? (
                <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-foreground">
                  {template.short_name}
                </div>
              ) : null}
              {template.capability_category ? (
                <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                  § {humanize(template.capability_category)}
                </div>
              ) : null}
            </div>

            <div className="flex flex-wrap gap-1.5">
              {template.is_omb_standard === 1 ? (
                <MonoChip tone="stamp" size="xs">
                  OMB standard
                </MonoChip>
              ) : null}
            </div>
          </div>
        </aside>

        <div className="col-span-12 md:col-span-9">
          <blockquote className="font-display italic text-[clamp(2rem,5vw,3.8rem)] leading-[1.08] tracking-[-0.015em] text-foreground">
            &ldquo;{template.template_text}&rdquo;
          </blockquote>

          {template.notes ? (
            <p className="mt-6 max-w-prose font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
              Notes · {template.notes}
            </p>
          ) : null}

          {/* Stat ledger */}
          <div className="mt-10 grid grid-cols-3 gap-x-6 border-t-2 border-foreground pt-4">
            <StatCell label="Agencies" value={template.agencies.length} />
            <StatCell label="Entries" value={template.use_case_count} />
            <StatCell
              label="Products paired"
              value={template.products.length}
            />
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------ */}
      {/* § I — AGENCIES                                               */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="I"
        title="Who adopted it"
        lede={`${formatNumber(template.agencies.length)} agencies filed this phrasing at least once.`}
      >
        {template.agencies.length === 0 ? (
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            — No agencies reported this template —
          </p>
        ) : (
          <ul className="divide-y divide-border border-y-2 border-foreground">
            {template.agencies.map((a, i) => (
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
      {/* § II — PRODUCTS PAIRED                                       */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="II"
        title="Paired products"
        lede={`${formatNumber(template.products.length)} distinct products were named alongside this template.`}
      >
        {template.products.length === 0 ? (
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            — No products are paired with this template —
          </p>
        ) : (
          <ul className="divide-y divide-border border-y-2 border-foreground">
            {template.products.map((p, i) => (
              <li
                key={p.id}
                className="grid grid-cols-[2.25rem_1fr_auto] items-baseline gap-x-3 py-3 md:grid-cols-[2.75rem_1fr_10rem_auto] md:gap-x-5"
              >
                <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <Link
                  href={`/products/${p.id}`}
                  className="truncate font-display text-[1.05rem] italic text-foreground hover:text-[var(--stamp)]"
                >
                  {p.canonical_name}
                </Link>
                <span className="hidden font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground md:inline">
                  {p.vendor ?? "—"}
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.1em] tabular-nums text-muted-foreground">
                  {formatNumber(p.count)} entries
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* § III — ALL ENTRIES                                          */}
      {/* ------------------------------------------------------------ */}
      <Section
        number="III"
        title="All entries"
        lede={`${formatNumber(entries.length)} individual and consolidated entries reference this template.`}
      >
        {entries.length === 0 ? (
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            — No entries reference this template —
          </p>
        ) : (
          <>
            <ul className="divide-y divide-border border-y-2 border-foreground">
              {entries.slice(0, 300).map((e, i) => (
                <li
                  key={`${e.use_case_id ?? "c"}-${e.agency_id}-${i}`}
                  className="grid grid-cols-[4rem_1fr_auto] items-baseline gap-x-4 py-3 md:grid-cols-[4rem_1fr_1fr_auto]"
                >
                  <Link
                    href={`/agencies/${e.agency_abbreviation}`}
                    className="font-mono text-[11px] font-semibold uppercase tracking-[0.06em] text-foreground hover:text-[var(--stamp)]"
                  >
                    {e.agency_abbreviation}
                  </Link>
                  <div className="min-w-0">
                    {e.product_id != null ? (
                      <Link
                        href={`/products/${e.product_id}`}
                        className="font-display text-[1rem] italic leading-snug text-foreground hover:text-[var(--stamp)]"
                      >
                        {e.product_name}
                      </Link>
                    ) : (
                      <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
                        — no product —
                      </span>
                    )}
                    {e.vendor ? (
                      <div className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
                        {e.vendor}
                      </div>
                    ) : null}
                  </div>
                  <span className="hidden font-mono text-[10px] leading-snug text-muted-foreground md:inline">
                    {truncate(e.commercial_examples, 120) || "—"}
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
                    {truncate(e.estimated_licenses_users, 40) || "—"}
                  </span>
                </li>
              ))}
            </ul>
            {entries.length > 300 ? (
              <p className="mt-3 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                Showing first 300 of {formatNumber(entries.length)} entries.
              </p>
            ) : null}
          </>
        )}
      </Section>

      {/* ------------------------------------------------------------ */}
      {/* Footer caption                                               */}
      {/* ------------------------------------------------------------ */}
      <footer className="mt-20 border-t-2 border-foreground pt-4 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
          <span>
            Template record ·{" "}
            <span className="text-foreground">
              № {String(template.id).padStart(3, "0")}
            </span>
            {template.short_name ? (
              <>
                {" · "}
                <span className="text-foreground">{template.short_name}</span>
              </>
            ) : null}
          </span>
          <span>
            {formatNumber(template.agencies.length)} agencies ·{" "}
            {formatNumber(entries.length)} entries
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

export function generateStaticParams() {
  return getAllTemplates().map((t) => ({ id: String(t.id) }));
}
