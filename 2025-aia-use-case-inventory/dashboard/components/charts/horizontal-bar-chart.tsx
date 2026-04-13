/**
 * Reusable horizontal bar chart built on top of Recharts. Client Component.
 *
 * For deployment-scope / bureau-breakdown style displays where the label
 * should live on the y-axis and the count determines bar length.
 */

"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type BarDatum = {
  label: string;
  count: number;
};

import { humanize } from "@/lib/formatting";

type Props = {
  data: BarDatum[];
  colorMap?: Record<string, string>;
  palette?: string[];
  height?: number;
  labelWidth?: number;
  labelMap?: Record<string, string>;
};

const DEFAULT_PALETTE = [
  "#10b981",
  "#3b82f6",
  "#f59e0b",
  "#f97316",
  "#64748b",
  "#8b5cf6",
  "#06b6d4",
];

export function HorizontalBarChart({
  data,
  colorMap = {},
  palette = DEFAULT_PALETTE,
  height = 240,
  labelWidth = 120,
  labelMap,
}: Props) {
  const formatLabel = (s: string) => labelMap?.[s] ?? humanize(s);
  const chartData = data
    .filter((d) => d.count > 0)
    .map((d, i) => ({
      label: formatLabel(d.label),
      rawLabel: d.label,
      count: d.count,
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
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 16, left: 4, bottom: 4 }}
        >
          <XAxis type="number" hide />
          <YAxis
            dataKey="label"
            type="category"
            width={labelWidth}
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            cursor={{ fill: "rgba(148,163,184,0.1)" }}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              borderColor: "var(--border)",
              background: "var(--background)",
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {chartData.map((d) => (
              <Cell key={d.rawLabel} fill={d.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
