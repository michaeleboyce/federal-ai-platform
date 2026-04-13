/**
 * Product × agency heatmap. Client Component — renders an HTML grid (not
 * SVG) because Recharts doesn't have a good heatmap primitive and we get
 * better accessibility this way.
 */

"use client";

import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export type ProductHeatmapData = {
  products: Array<{
    id: number;
    canonical_name: string;
    vendor: string | null;
    total: number;
  }>;
  agencies: Array<{
    id: number;
    name: string;
    abbreviation: string;
    total: number;
  }>;
  cells: Array<{ product_id: number; agency_id: number; count: number }>;
};

function intensityClass(count: number, max: number): string {
  if (count === 0 || max === 0) return "bg-zinc-50 dark:bg-zinc-900";
  const ratio = count / max;
  if (ratio <= 0.05) return "bg-blue-50 dark:bg-blue-950/40";
  if (ratio <= 0.15) return "bg-blue-100 dark:bg-blue-900/60";
  if (ratio <= 0.3) return "bg-blue-200 dark:bg-blue-800";
  if (ratio <= 0.5) return "bg-blue-400 dark:bg-blue-700";
  if (ratio <= 0.75) return "bg-blue-500 dark:bg-blue-600";
  return "bg-blue-600 dark:bg-blue-500";
}

function textClass(count: number, max: number): string {
  if (count === 0 || max === 0) return "text-zinc-400";
  const ratio = count / max;
  return ratio > 0.3 ? "text-white" : "text-zinc-800 dark:text-zinc-100";
}

export function ProductHeatmap({ data }: { data: ProductHeatmapData }) {
  const { products, agencies, cells } = data;

  const cellMap = React.useMemo(() => {
    const m = new Map<string, number>();
    for (const c of cells) m.set(`${c.product_id}:${c.agency_id}`, c.count);
    return m;
  }, [cells]);

  const max = React.useMemo(() => {
    let m = 0;
    for (const c of cells) if (c.count > m) m = c.count;
    return m;
  }, [cells]);

  if (products.length === 0 || agencies.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
        Not enough data to render the heatmap.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-max">
        {/* Header row: agency abbreviations */}
        <div
          className="grid items-end"
          style={{
            gridTemplateColumns: `minmax(220px, 260px) repeat(${agencies.length}, 36px)`,
          }}
        >
          <div />
          {agencies.map((a) => (
            <div
              key={a.id}
              className="h-20 text-[10px] font-medium text-muted-foreground"
              style={{
                writingMode: "vertical-rl",
                transform: "rotate(180deg)",
                lineHeight: 1,
              }}
              title={`${a.name} — ${a.total} use cases`}
            >
              {a.abbreviation}
            </div>
          ))}
        </div>

        {/* Data rows */}
        {products.map((p) => (
          <div
            key={p.id}
            className="grid items-center"
            style={{
              gridTemplateColumns: `minmax(220px, 260px) repeat(${agencies.length}, 36px)`,
            }}
          >
            <div
              className="truncate pr-3 text-xs font-medium text-foreground"
              title={`${p.canonical_name}${p.vendor ? ` · ${p.vendor}` : ""} — ${p.total} use cases`}
            >
              <Link
                href={`/products?id=${p.id}`}
                className="hover:underline"
              >
                {p.canonical_name}
              </Link>
              {p.vendor ? (
                <span className="ml-1 text-[10px] text-muted-foreground">
                  {p.vendor}
                </span>
              ) : null}
            </div>
            {agencies.map((a) => {
              const count = cellMap.get(`${p.id}:${a.id}`) ?? 0;
              const key = `${p.id}:${a.id}`;
              if (count === 0) {
                return (
                  <div
                    key={key}
                    className={cn(
                      "m-0.5 h-8 rounded text-center text-[10px]",
                      intensityClass(0, max),
                    )}
                    aria-label={`${p.canonical_name} × ${a.abbreviation}: 0`}
                  />
                );
              }
              return (
                <Link
                  key={key}
                  href={`/use-cases?agency=${a.abbreviation}&product=${p.id}`}
                  className={cn(
                    "m-0.5 flex h-8 items-center justify-center rounded text-[10px] font-semibold tabular-nums transition-opacity hover:opacity-80",
                    intensityClass(count, max),
                    textClass(count, max),
                  )}
                  title={`${p.canonical_name} at ${a.abbreviation}: ${count} use case${count === 1 ? "" : "s"} — click to filter`}
                >
                  {count}
                </Link>
              );
            })}
          </div>
        ))}

        {/* Legend */}
        <div className="mt-3 flex items-center gap-2 text-[11px] text-muted-foreground">
          <span>0</span>
          <span className={cn("h-3 w-6 rounded-sm", intensityClass(1, 100))} />
          <span className={cn("h-3 w-6 rounded-sm", intensityClass(5, 100))} />
          <span className={cn("h-3 w-6 rounded-sm", intensityClass(20, 100))} />
          <span className={cn("h-3 w-6 rounded-sm", intensityClass(50, 100))} />
          <span className={cn("h-3 w-6 rounded-sm", intensityClass(80, 100))} />
          <span className={cn("h-3 w-6 rounded-sm", intensityClass(100, 100))} />
          <span>{max}+ use cases</span>
        </div>
      </div>
    </div>
  );
}
