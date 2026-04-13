/**
 * Scatter plot: YoY growth (x) × total use-case count (y), colored by
 * maturity tier. Client Component.
 */

"use client";

import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

export type MaturityScatterDatum = {
  agency_id: number;
  name: string;
  abbreviation: string;
  year_over_year_growth: number | null;
  total_use_cases: number | null;
  maturity_tier: string | null;
};

const TIER_COLORS: Record<string, string> = {
  leading: "#10b981",
  progressing: "#3b82f6",
  early: "#f59e0b",
  minimal: "#64748b",
  none: "#a1a1aa",
};

const TIER_LABEL: Record<string, string> = {
  leading: "Leading",
  progressing: "Progressing",
  early: "Early",
  minimal: "Minimal",
  none: "Unranked",
};

type ChartPoint = {
  name: string;
  abbreviation: string;
  growth: number;
  total: number;
  tier: string;
};

export function MaturityScatter({ data }: { data: MaturityScatterDatum[] }) {
  // Group by tier so each series gets its own color + legend entry.
  const buckets = new Map<string, ChartPoint[]>();
  for (const d of data) {
    if (d.year_over_year_growth == null || d.total_use_cases == null) continue;
    const tier = d.maturity_tier ?? "none";
    if (!buckets.has(tier)) buckets.set(tier, []);
    buckets.get(tier)!.push({
      name: d.name,
      abbreviation: d.abbreviation,
      growth: d.year_over_year_growth,
      total: d.total_use_cases,
      tier,
    });
  }

  // Cap x-axis to avoid the NASA outlier squishing everyone else.
  const xCap = 500;

  return (
    <div className="flex flex-col gap-3">
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 12, right: 16, bottom: 44, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              type="number"
              dataKey="growth"
              name="YoY growth"
              domain={[-100, xCap]}
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              tickFormatter={(v) => `${v > 0 ? "+" : ""}${Math.round(v)}%`}
              label={{
                value: "Year-over-year growth (capped at +500%)",
                position: "insideBottom",
                offset: -10,
                style: {
                  fontSize: 11,
                  fill: "var(--muted-foreground)",
                },
              }}
            />
            <YAxis
              type="number"
              dataKey="total"
              name="Use cases"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              label={{
                value: "Total use cases",
                angle: -90,
                position: "insideLeft",
                style: {
                  fontSize: 11,
                  fill: "var(--muted-foreground)",
                },
              }}
            />
            <ZAxis range={[80, 80]} />
            <Tooltip
              cursor={{
                stroke: "var(--muted-foreground)",
                strokeDasharray: "3 3",
              }}
              contentStyle={{
                background: "var(--popover)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
                color: "var(--popover-foreground)",
              }}
              formatter={(value, name) => {
                const v = Number(value ?? 0);
                const n = String(name ?? "");
                if (n === "YoY growth")
                  return [`${v > 0 ? "+" : ""}${v.toFixed(1)}%`, n];
                return [String(v), n];
              }}
              labelFormatter={() => ""}
              content={({ active, payload }) => {
                if (!active || !payload || payload.length === 0) return null;
                const p = payload[0].payload as ChartPoint;
                return (
                  <div className="rounded-md border border-border bg-popover p-2 text-xs text-popover-foreground shadow">
                    <div className="font-semibold">{p.name}</div>
                    <div className="text-muted-foreground">
                      {p.abbreviation} · {TIER_LABEL[p.tier] ?? p.tier}
                    </div>
                    <div className="mt-1 tabular-nums">
                      YoY:{" "}
                      <span className="font-medium">
                        {p.growth > 0 ? "+" : ""}
                        {p.growth.toFixed(1)}%
                      </span>
                    </div>
                    <div className="tabular-nums">
                      Total:{" "}
                      <span className="font-medium">{p.total}</span> use cases
                    </div>
                  </div>
                );
              }}
            />
            {Array.from(buckets.entries()).map(([tier, points]) => (
              <Scatter
                key={tier}
                name={TIER_LABEL[tier] ?? tier}
                data={points.map((p) => ({
                  ...p,
                  // Clamp to xCap so outliers still render at the edge.
                  growth: Math.min(p.growth, xCap),
                }))}
                fill={TIER_COLORS[tier] ?? "#64748b"}
                fillOpacity={0.8}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-wrap gap-3 text-[11px] text-muted-foreground">
        {Array.from(buckets.keys()).map((tier) => (
          <span key={tier} className="inline-flex items-center gap-1.5">
            <span
              aria-hidden
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ background: TIER_COLORS[tier] ?? "#64748b" }}
            />
            {TIER_LABEL[tier] ?? tier}
          </span>
        ))}
      </div>
    </div>
  );
}
