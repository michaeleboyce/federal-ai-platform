/**
 * 100%-stacked horizontal bars: one bar per agency, five segments by
 * tag.entry_type. Shows *shape* of each agency's inventory — are they mostly
 * COTS deployments? Bespoke builds? Generic patterns?
 */

"use client";

import * as React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";

export type EntryTypeRow = {
  agency_id: number;
  name: string;
  abbreviation: string;
  total: number;
  custom_system: number;
  product_deployment: number;
  bespoke_application: number;
  generic_use_pattern: number;
  product_feature: number;
  unknown: number;
};

type Mode = "percent" | "absolute";

const SEGMENTS: Array<{ key: keyof EntryTypeRow; label: string; color: string }> = [
  { key: "product_deployment", label: "Product deployment", color: "#2563eb" },
  { key: "custom_system", label: "Custom system", color: "#10b981" },
  { key: "bespoke_application", label: "Bespoke application", color: "#8b5cf6" },
  { key: "generic_use_pattern", label: "Generic use pattern", color: "#f59e0b" },
  { key: "product_feature", label: "Product feature", color: "#06b6d4" },
  { key: "unknown", label: "Unknown", color: "#94a3b8" },
];

export function EntryTypeMixChart({
  data,
  initialLimit = 25,
}: {
  data: EntryTypeRow[];
  initialLimit?: number;
}) {
  const [mode, setMode] = React.useState<Mode>("percent");
  const [limit, setLimit] = React.useState(initialLimit);

  const visible = React.useMemo(() => {
    const rows = data.slice(0, limit);
    if (mode === "absolute") return rows;
    return rows.map((r) => {
      const out: Record<string, number | string> = {
        abbreviation: r.abbreviation,
        name: r.name,
        total: r.total,
      };
      for (const seg of SEGMENTS) {
        const raw = r[seg.key] as number;
        out[seg.key] = r.total === 0 ? 0 : (raw / r.total) * 100;
      }
      return out as unknown as EntryTypeRow;
    });
  }, [data, limit, mode]);

  const height = Math.max(320, visible.length * 20);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-muted-foreground">Scale:</span>
        <Button
          variant={mode === "percent" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("percent")}
        >
          Percent
        </Button>
        <Button
          variant={mode === "absolute" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("absolute")}
        >
          Absolute
        </Button>
        <span className="ml-3 text-muted-foreground">Show:</span>
        <Button
          variant={limit === 15 ? "default" : "outline"}
          size="sm"
          onClick={() => setLimit(15)}
        >
          15
        </Button>
        <Button
          variant={limit === 25 ? "default" : "outline"}
          size="sm"
          onClick={() => setLimit(25)}
        >
          25
        </Button>
        <Button
          variant={limit === data.length ? "default" : "outline"}
          size="sm"
          onClick={() => setLimit(data.length)}
        >
          All ({data.length})
        </Button>
      </div>

      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={visible}
            layout="vertical"
            margin={{ top: 4, right: 8, bottom: 30, left: 8 }}
            stackOffset={mode === "percent" ? "expand" : "none"}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              type="number"
              domain={mode === "percent" ? [0, 100] : undefined}
              tickFormatter={(v) =>
                mode === "percent" ? `${Math.round(v)}%` : String(v)
              }
              tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              allowDecimals={false}
            />
            <YAxis
              type="category"
              dataKey="abbreviation"
              tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              width={70}
              interval={0}
            />
            <Tooltip
              cursor={{ fill: "var(--muted)", opacity: 0.3 }}
              contentStyle={{
                background: "var(--popover)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
                color: "var(--popover-foreground)",
              }}
              formatter={(value, name) => {
                const v = Number(value ?? 0);
                return [
                  mode === "percent"
                    ? `${v.toFixed(1)}%`
                    : `${Math.round(v)}`,
                  String(name ?? ""),
                ];
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} iconSize={8} />
            {SEGMENTS.map((seg) => (
              <Bar
                key={seg.key as string}
                dataKey={seg.key as string}
                name={seg.label}
                stackId="a"
                fill={seg.color}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
