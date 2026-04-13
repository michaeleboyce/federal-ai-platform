/**
 * Agency detail page header band — editorial. Server Component, no state.
 *
 * Layout: a bordered mono abbreviation badge (square, not circle) on the left,
 * an italic display agency name, a monospace meta line of tags, and a small
 * row of source-of-record links beneath.
 */

import Link from "next/link";
import { MonoChip } from "@/components/editorial";
import { agencyTypeLabel, maturityTierLabel } from "@/lib/formatting";
import type { AgencyWithMaturity } from "@/lib/types";

const STATUS_LABELS: Record<string, string> = {
  FOUND_2025: "2025 Inventory",
  FOUND_2024_ONLY: "2024 Inventory Only",
  NOT_FOUND: "Inventory Not Found",
  EXEMPT: "Exempt",
  ZERO_USE_CASES: "No Use Cases Reported",
  SITE_DOWN: "Site Down",
};

function statusLabel(status: string | null): string {
  if (!status) return "—";
  return STATUS_LABELS[status] ?? status;
}

export function AgencyHeader({ agency }: { agency: AgencyWithMaturity }) {
  const tier = agency.maturity?.maturity_tier ?? null;

  return (
    <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-10">
      {/* Left rail: big mono abbreviation chip + filing meta */}
      <aside className="col-span-12 mb-6 md:col-span-3 md:mb-0">
        <div className="space-y-4 md:sticky md:top-32">
          <div
            aria-hidden="true"
            className="inline-flex items-center justify-center border-2 border-foreground bg-background px-4 py-3 font-mono text-2xl font-semibold uppercase tracking-[0.08em] text-foreground"
          >
            {agency.abbreviation}
          </div>

          <div className="space-y-1 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            <div className="!text-[var(--stamp)]">
              § Agency · {agencyTypeLabel(agency.agency_type)}
            </div>
            {agency.inventory_year ? (
              <div>FY {agency.inventory_year}</div>
            ) : null}
            {agency.status ? <div>{statusLabel(agency.status)}</div> : null}
          </div>
        </div>
      </aside>

      {/* Headline column */}
      <div className="col-span-12 md:col-span-9">
        <h1 className="font-display italic text-[clamp(2.2rem,5vw,3.8rem)] leading-[0.95] tracking-[-0.02em] text-foreground">
          {agency.name}
        </h1>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          {tier ? (
            <MonoChip tone={tier === "leading" ? "verified" : "ink"} size="sm">
              {maturityTierLabel(tier)}
            </MonoChip>
          ) : null}
          {agency.agency_type ? (
            <MonoChip tone="muted" size="sm">
              {agencyTypeLabel(agency.agency_type)}
            </MonoChip>
          ) : null}
          {agency.status ? (
            <MonoChip tone="muted" size="sm">
              {statusLabel(agency.status)}
            </MonoChip>
          ) : null}
        </div>

        {(agency.inventory_page_url || agency.csv_download_url) && (
          <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-dotted border-border pt-3 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            {agency.inventory_page_url ? (
              <Link
                href={agency.inventory_page_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-foreground hover:text-[var(--stamp)]"
              >
                Inventory page
                <span aria-hidden="true">↗</span>
              </Link>
            ) : null}
            {agency.csv_download_url ? (
              <Link
                href={agency.csv_download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-foreground hover:text-[var(--stamp)]"
              >
                Source CSV
                <span aria-hidden="true">↗</span>
              </Link>
            ) : null}
          </div>
        )}
      </div>
    </header>
  );
}
