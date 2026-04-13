/**
 * Colophon footer. Narrow, hairline-ruled, dense with monospaced detail.
 * Echoes the dateline at the top — same typographic vocabulary, same
 * semantic weight.
 */

import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { formatDate } from "@/lib/formatting";

export function SiteFooter({ lastUpdated }: { lastUpdated: string | null }) {
  return (
    <footer className="mt-24 border-t border-border">
      <div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8">
        {/* Upper rule: big italic nameplate */}
        <div className="flex flex-col gap-6 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
          <Link href="/" className="group inline-flex items-baseline gap-2">
            <span className="font-display italic text-[1.5rem] leading-none text-foreground">
              The Federal AI
            </span>
            <span className="font-display text-[1.5rem] leading-none text-foreground">
              Inventory
            </span>
          </Link>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            OMB M-25-21 · Cycle 2025 · Vol. I
          </div>
        </div>

        {/* Lower rule: links + dateline */}
        <div className="mt-6 grid gap-6 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground md:grid-cols-3">
          <div className="space-y-1.5">
            <div className="text-[9px] text-muted-foreground/70">Filed</div>
            <div className="text-foreground">{formatDate(lastUpdated)}</div>
          </div>

          <div className="space-y-1.5">
            <div className="text-[9px] text-muted-foreground/70">Sections</div>
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              <Link href="/about" className="hover:text-[var(--stamp)]">
                Colophon
              </Link>
              <Link href="/compare" className="hover:text-[var(--stamp)]">
                Compare
              </Link>
              <Link href="/analytics" className="hover:text-[var(--stamp)]">
                Analytics
              </Link>
            </div>
          </div>

          <div className="space-y-1.5 md:text-right">
            <div className="text-[9px] text-muted-foreground/70">Source</div>
            <a
              href="https://ai.gov/"
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-center gap-1 hover:text-[var(--stamp)]"
            >
              ai.gov <ExternalLink className="h-3 w-3" aria-hidden />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
