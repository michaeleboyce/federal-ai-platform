"use client";

// Client Component — Recharts renders via browser APIs (SVG + ResizeObserver).

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { humanize } from "@/lib/formatting";

export type DonutDatum = {
  label: string;
  count: number;
};

type Props = {
  data: DonutDatum[];
  colorMap?: Record<string, string>;
  palette?: string[];
  height?: number;
  labelMap?: Record<string, string>;
  centerLabel?: string;
  centerSubLabel?: string;
};

const DEFAULT_PALETTE = [
  "#3b82f6",
  "#8b5cf6",
  "#a855f7",
  "#06b6d4",
  "#14b8a6",
  "#6366f1",
  "#64748b",
  "#f59e0b",
  "#f97316",
  "#ef4444",
  "#10b981",
  "#ec4899",
];

export function DonutChart({
  data,
  colorMap = {},
  palette = DEFAULT_PALETTE,
  height = 240,
  labelMap,
  centerLabel,
  centerSubLabel,
}: Props) {
  const total = data.reduce((acc, d) => acc + d.count, 0);
  const display = centerLabel ?? String(total);

  const chartData = data
    .filter((d) => d.count > 0)
    .map((d, i) => ({
      name: labelMap?.[d.label] ?? humanize(d.label),
      rawLabel: d.label,
      value: d.count,
      fill: colorMap[d.label] ?? palette[i % palette.length],
    }));

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-sm text-muted-foreground"
        style={{ height }}
      >
        No data
      </div>
    );
  }

  return (
    <div className="relative w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius="55%"
            outerRadius="85%"
            strokeWidth={1}
            paddingAngle={1}
          >
            {chartData.map((d) => (
              <Cell key={d.rawLabel} fill={d.fill} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 0,
              borderColor: "var(--border)",
              background: "var(--background)",
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11 }}
            iconSize={8}
            verticalAlign="bottom"
            height={36}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center pb-9">
        <span className="font-display text-[2rem] leading-none tabular-nums">
          {display}
        </span>
        {centerSubLabel ? (
          <span className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {centerSubLabel}
          </span>
        ) : null}
      </div>
    </div>
  );
}
