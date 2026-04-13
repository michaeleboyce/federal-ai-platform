/**
 * Grid view for the Use Cases Explorer. A thin wrapper around
 * `<UseCaseCard>` — no client state needed, so this is a pure RSC.
 *
 * Editorial: 2px top-rule anchoring the whole figure; cards are
 * hairline-ruled rather than shadowed.
 */

import Link from "next/link";
import type { UseCaseWithTags } from "@/lib/types";
import { UseCaseCard } from "./use-case-card";

export function UseCaseGrid({ rows }: { rows: UseCaseWithTags[] }) {
  if (rows.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 border-t-2 border-foreground py-14 text-center">
        <p className="font-display italic text-xl text-foreground">
          No entries match the current filter.
        </p>
        <Link
          href="/use-cases"
          className="inline-flex items-center border border-border bg-background px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-[var(--stamp)] hover:text-[var(--stamp)]"
        >
          Clear filters
        </Link>
      </div>
    );
  }
  return (
    <div className="border-t-2 border-foreground">
      <div className="grid grid-cols-1 gap-0 sm:grid-cols-2 xl:grid-cols-3">
        {rows.map((row) => (
          <UseCaseCard key={row.id} useCase={row} />
        ))}
      </div>
    </div>
  );
}
