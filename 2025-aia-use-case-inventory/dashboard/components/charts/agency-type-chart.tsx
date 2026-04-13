"use client";

/**
 * Stacked bar chart comparing agency_type groups (CFO_ACT, INDEPENDENT, etc.)
 * broken down by maturity tier.
 */

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
import { agencyTypeLabel } from "@/lib/formatting";

export type AgencyTypeDatum = {
  agency_type: string;
  leading: number;
  progressing: number;
  early: number;
  minimal: number;
  none: number;
};

const TIER_COLORS: Record<string, string> = {
  leading: "#10b981", // emerald-500
  progressing: "#3b82f6", // blue-500
  early: "#f59e0b", // amber-500
  minimal: "#64748b", // slate-500
  none: "#cbd5e1", // slate-300
};

export function AgencyTypeChart({ data }: { data: AgencyTypeDatum[] }) {
  const shaped = data.map((d) => ({ ...d, label: agencyTypeLabel(d.agency_type) }));

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={shaped} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="label" stroke="var(--muted-foreground)" fontSize={12} />
          <YAxis stroke="var(--muted-foreground)" fontSize={12} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              background: "var(--popover)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="leading" stackId="a" fill={TIER_COLORS.leading} />
          <Bar dataKey="progressing" stackId="a" fill={TIER_COLORS.progressing} />
          <Bar dataKey="early" stackId="a" fill={TIER_COLORS.early} />
          <Bar dataKey="minimal" stackId="a" fill={TIER_COLORS.minimal} />
          <Bar dataKey="none" stackId="a" fill={TIER_COLORS.none} name="unranked" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
