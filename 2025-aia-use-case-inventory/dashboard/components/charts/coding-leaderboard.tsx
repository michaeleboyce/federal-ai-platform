/**
 * Horizontal-bar leaderboard chart. Reused by:
 *  - "Coding tool adoption leaderboard"
 *  - "Enterprise LLM distribution"
 *
 * Clicking a bar navigates to the agency detail page.
 */

"use client";

import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export type LeaderboardRow = {
  abbreviation: string;
  name: string;
  value: number;
  /** Optional annotation shown in muted text to the right of the abbreviation. */
  subLabel?: string;
};

type Props = {
  rows: LeaderboardRow[];
  /** Render the top N rows (default 20). */
  limit?: number;
  /** Color of the filled bar. */
  color?: string;
  /** Unit label for the tooltip ("use cases", "entries", etc.). */
  unit?: string;
};

export function CodingLeaderboard({
  rows,
  limit = 20,
  color = "#2563eb",
  unit = "use cases",
}: Props) {
  const visible = React.useMemo(
    () => rows.filter((r) => r.value > 0).slice(0, limit),
    [rows, limit],
  );

  const max = visible[0]?.value ?? 0;

  if (visible.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
        No agencies met the threshold.
      </div>
    );
  }

  return (
    <ol className="flex flex-col gap-1">
      {visible.map((row, idx) => {
        const pct = max === 0 ? 0 : (row.value / max) * 100;
        return (
          <li key={row.abbreviation}>
            <Link
              href={`/agencies/${row.abbreviation.toLowerCase()}`}
              className="group grid grid-cols-[28px_96px_1fr_48px] items-center gap-2 rounded px-1 py-1 text-xs hover:bg-muted/60"
              title={`${row.name} — ${row.value} ${unit}`}
            >
              <span className="tabular-nums text-muted-foreground">
                {idx + 1}.
              </span>
              <span className="truncate font-medium text-foreground">
                {row.abbreviation}
                {row.subLabel ? (
                  <span className="ml-1 text-[10px] text-muted-foreground">
                    {row.subLabel}
                  </span>
                ) : null}
              </span>
              <span
                className={cn(
                  "relative h-4 w-full overflow-hidden rounded",
                  "bg-zinc-100 dark:bg-zinc-800",
                )}
              >
                <span
                  aria-hidden
                  className="block h-full rounded transition-opacity group-hover:opacity-85"
                  style={{ width: `${pct}%`, background: color }}
                />
              </span>
              <span className="text-right font-mono tabular-nums text-foreground">
                {row.value}
              </span>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
