/**
 * Vendor market-share chart. Client Component.
 *
 * Renders two side-by-side horizontal bar charts: "Agencies using" and
 * "Total entries", both sorted by the same metric (descending). Well-known
 * vendors get distinct colors; everything else is slate.
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

export type VendorShareDatum = {
  vendor: string;
  agency_count: number;
  use_case_count: number;
};

const VENDOR_COLORS: Record<string, string> = {
  Microsoft: "#2563eb", // blue-600
  OpenAI: "#10b981", // emerald-500
  Anthropic: "#f59e0b", // amber-500
  Google: "#ef4444", // red-500
  Amazon: "#f97316", // orange-500
  AWS: "#f97316",
  Meta: "#8b5cf6",
  GitHub: "#0ea5e9", // sky-500
};

function vendorColor(v: string): string {
  if (VENDOR_COLORS[v]) return VENDOR_COLORS[v];
  // Heuristics for vendor-name variants.
  const lower = v.toLowerCase();
  if (lower.includes("microsoft") || lower.includes("azure"))
    return VENDOR_COLORS.Microsoft!;
  if (lower.includes("openai")) return VENDOR_COLORS.OpenAI!;
  if (lower.includes("anthropic") || lower.includes("claude"))
    return VENDOR_COLORS.Anthropic!;
  if (lower.includes("google") || lower.includes("gemini"))
    return VENDOR_COLORS.Google!;
  if (lower.includes("amazon") || lower.includes("aws"))
    return VENDOR_COLORS.Amazon!;
  if (lower.includes("github")) return VENDOR_COLORS.GitHub!;
  return "#64748b"; // slate-500
}

type Props = {
  data: VendorShareDatum[];
  /** Cap the number of vendors shown (default 12). */
  limit?: number;
};

export function VendorShareChart({ data, limit = 12 }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
        No vendor data available.
      </div>
    );
  }

  const byAgencies = [...data]
    .sort((a, b) => b.agency_count - a.agency_count)
    .slice(0, limit);
  const byEntries = [...data]
    .sort((a, b) => b.use_case_count - a.use_case_count)
    .slice(0, limit);

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <VendorPanel
        title="Agencies using vendor"
        subtitle="Distinct agencies reporting at least one use case"
        data={byAgencies}
        valueKey="agency_count"
      />
      <VendorPanel
        title="Total entries by vendor"
        subtitle="Raw use-case count (products × deployments)"
        data={byEntries}
        valueKey="use_case_count"
      />
    </div>
  );
}

function VendorPanel({
  title,
  subtitle,
  data,
  valueKey,
}: {
  title: string;
  subtitle: string;
  data: VendorShareDatum[];
  valueKey: "agency_count" | "use_case_count";
}) {
  // Reverse for top-down display in a vertical-layout BarChart.
  const display = [...data].reverse();
  const height = Math.max(240, display.length * 28);

  return (
    <div className="flex flex-col gap-2">
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>
      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={display}
            layout="vertical"
            margin={{ top: 4, right: 40, bottom: 4, left: 8 }}
          >
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              allowDecimals={false}
            />
            <YAxis
              type="category"
              dataKey="vendor"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              width={110}
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
              formatter={(value, _name, entry) => {
                const d = (entry as { payload: VendorShareDatum }).payload;
                const v = value as number;
                return [
                  valueKey === "agency_count"
                    ? `${v} agencies · ${d.use_case_count} entries`
                    : `${v} entries · ${d.agency_count} agencies`,
                  d.vendor,
                ];
              }}
              labelFormatter={() => ""}
            />
            <Bar dataKey={valueKey} radius={[0, 4, 4, 0]}>
              {display.map((d) => (
                <Cell key={d.vendor} fill={vendorColor(d.vendor)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
