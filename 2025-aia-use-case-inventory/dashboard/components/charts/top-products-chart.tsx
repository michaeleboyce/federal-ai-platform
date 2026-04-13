"use client";

/**
 * Horizontal bar chart of the top N products by agency adoption. Bars are
 * clickable and navigate to `/products/[id]`. Client component because
 * Recharts relies on browser APIs for layout + interaction.
 */

import { useRouter } from "next/navigation";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type TopProductDatum = {
  id: number;
  name: string;
  vendor: string | null;
  agency_count: number;
  use_case_count: number;
};

export function TopProductsChart({ data }: { data: TopProductDatum[] }) {
  const router = useRouter();

  // Recharts renders the first item at the top when layout="vertical"; we want
  // the biggest bar on top. Ensure sorted ascending so it renders top-down.
  const sorted = [...data].sort((a, b) => a.agency_count - b.agency_count);

  return (
    <div className="h-[360px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={sorted}
          margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
        >
          <CartesianGrid
            horizontal={false}
            strokeDasharray="3 3"
            stroke="var(--border)"
          />
          <XAxis
            type="number"
            stroke="var(--muted-foreground)"
            fontSize={12}
            allowDecimals={false}
          />
          <YAxis
            dataKey="name"
            type="category"
            width={170}
            stroke="var(--muted-foreground)"
            fontSize={12}
            tickFormatter={(v: string) => (v.length > 24 ? `${v.slice(0, 23)}…` : v)}
          />
          <Tooltip
            cursor={{ fill: "var(--muted)" }}
            contentStyle={{
              background: "var(--popover)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value, _name, item) => {
              const payload = (item as { payload?: TopProductDatum } | undefined)
                ?.payload;
              const count = Number(value ?? 0);
              const useCases = payload?.use_case_count ?? 0;
              return [
                `${count} agencies · ${useCases} use cases`,
                payload?.vendor ?? "",
              ] as [string, string];
            }}
          />
          <Bar
            dataKey="agency_count"
            fill="#3b82f6"
            radius={[0, 4, 4, 0]}
            cursor="pointer"
            onClick={(payload: unknown) => {
              const p = payload as { id?: number } | undefined;
              if (p?.id != null) router.push(`/products/${p.id}`);
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
