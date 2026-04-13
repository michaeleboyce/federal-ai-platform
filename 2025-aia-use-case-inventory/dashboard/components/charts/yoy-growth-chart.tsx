/**
 * Horizontal bar chart of year-over-year growth per agency. Client Component
 * (Recharts + state for the Top / Bottom / All toggle).
 *
 * Growth values come from `agency_ai_maturity.year_over_year_growth`. The DB
 * stores them as a fraction (e.g. 22.61 = +2261%) or a straight percent — we
 * assume it's already a percent number and render as-is.
 */

"use client";

import * as React from "react";
import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import type { YoYRow } from "@/lib/types";

type ViewMode = "top20" | "bottom20" | "all";

const POSITIVE = "#10b981"; // emerald-500
const NEGATIVE = "#ef4444"; // red-500
const OUTLIER = "#8b5cf6"; // violet-500, reserved for NASA / extreme highs

type ChartRow = {
  abbreviation: string;
  name: string;
  growth: number;
  total: number;
};

export function YoYGrowthChart({ data }: { data: YoYRow[] }) {
  const [mode, setMode] = React.useState<ViewMode>("top20");

  const rows = React.useMemo<ChartRow[]>(
    () =>
      data
        .filter((d) => d.year_over_year_growth != null)
        .map((d) => ({
          abbreviation: d.abbreviation,
          name: d.name,
          growth: d.year_over_year_growth as number,
          total: d.total_use_cases ?? 0,
        }))
        .sort((a, b) => b.growth - a.growth),
    [data],
  );

  const visible = React.useMemo<ChartRow[]>(() => {
    if (mode === "top20") return rows.slice(0, 20);
    if (mode === "bottom20") return rows.slice(-20).reverse();
    return rows;
  }, [mode, rows]);

  // Flip orientation so the biggest bars appear at the top of the chart.
  const display = [...visible].reverse();
  const height = Math.max(260, display.length * 22);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-muted-foreground">Show:</span>
        <Button
          variant={mode === "top20" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("top20")}
        >
          Top 20
        </Button>
        <Button
          variant={mode === "bottom20" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("bottom20")}
        >
          Bottom 20
        </Button>
        <Button
          variant={mode === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("all")}
        >
          All ({rows.length})
        </Button>
      </div>

      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={display}
            layout="vertical"
            margin={{ top: 4, right: 72, bottom: 4, left: 8 }}
          >
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              tickFormatter={(v) => `${v > 0 ? "+" : ""}${Math.round(v)}%`}
            />
            <YAxis
              type="category"
              dataKey="abbreviation"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              width={70}
              interval={0}
            />
            <Tooltip
              cursor={{ fill: "var(--muted)", opacity: 0.4 }}
              contentStyle={{
                background: "var(--popover)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
                color: "var(--popover-foreground)",
              }}
              labelFormatter={(abbr) => {
                const key = String(abbr ?? "");
                const row = display.find((r) => r.abbreviation === key);
                return row ? `${row.name} (${row.abbreviation})` : key;
              }}
              formatter={(value, _name, entry) => {
                const v = Number(value ?? 0);
                const datum = (entry as { payload?: ChartRow }).payload;
                return [
                  `${v > 0 ? "+" : ""}${v.toFixed(1)}%  (${datum?.total ?? 0} use cases)`,
                  "YoY growth",
                ];
              }}
            />
            <Bar dataKey="growth" radius={[0, 4, 4, 0]}>
              {display.map((row) => (
                <Cell
                  key={row.abbreviation}
                  fill={
                    row.growth >= 500
                      ? OUTLIER
                      : row.growth >= 0
                        ? POSITIVE
                        : NEGATIVE
                  }
                />
              ))}
              <LabelList
                dataKey="growth"
                position="right"
                formatter={(value) => {
                  const v = Number(value ?? 0);
                  return `${v > 0 ? "+" : ""}${Math.round(v)}%`;
                }}
                style={{
                  fontSize: 10,
                  fill: "var(--muted-foreground)",
                  fontVariantNumeric: "tabular-nums",
                }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-[11px] text-muted-foreground">
        <LegendSwatch color={OUTLIER} label="Extreme growth (≥ 500%)" />
        <LegendSwatch color={POSITIVE} label="Positive growth" />
        <LegendSwatch color={NEGATIVE} label="Negative growth" />
      </div>
    </div>
  );
}

function LegendSwatch({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        aria-hidden
        className="inline-block h-2.5 w-3 rounded-sm"
        style={{ background: color }}
      />
      {label}
    </span>
  );
}
