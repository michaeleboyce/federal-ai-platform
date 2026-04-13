/**
 * Client-side filter bar + grid for the /templates page — editorial.
 */

"use client";

import { useMemo, useState } from "react";
import { TemplateCard } from "@/components/template-card";
import { formatNumber, humanize } from "@/lib/formatting";
import type { TemplateWithCounts } from "@/lib/types";

type Props = {
  templates: TemplateWithCounts[];
};

type SortKey = "use_case_count" | "agency_count" | "short_name";

const ALL = "__all__";

const CAPABILITY_CATEGORIES = [
  "writing",
  "coding",
  "search",
  "meetings",
  "email",
  "data_viz",
  "travel",
  "productivity",
  "privacy",
  "cybersecurity",
  "it_operations",
];

const fieldClass =
  "h-8 min-w-0 border border-border bg-background px-2 font-mono text-[11px] uppercase tracking-[0.08em] text-foreground focus:border-foreground focus:outline-none";

export function TemplatesFilters({ templates }: Props) {
  const [category, setCategory] = useState<string>(ALL);
  const [ombOnly, setOmbOnly] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("use_case_count");

  const categories = useMemo(() => {
    const set = new Set<string>();
    for (const t of templates)
      if (t.capability_category) set.add(t.capability_category);
    for (const c of CAPABILITY_CATEGORIES) set.add(c);
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [templates]);

  const filtered = useMemo(() => {
    const rows = templates.filter((t) => {
      if (category !== ALL && t.capability_category !== category) return false;
      if (ombOnly && t.is_omb_standard !== 1) return false;
      return true;
    });
    rows.sort((a, b) => {
      if (sortKey === "short_name")
        return (a.short_name ?? "").localeCompare(b.short_name ?? "");
      if (sortKey === "agency_count") return b.agency_count - a.agency_count;
      return b.use_case_count - a.use_case_count;
    });
    return rows;
  }, [templates, category, ombOnly, sortKey]);

  return (
    <div className="flex flex-col gap-8">
      <div className="border-y-2 border-foreground py-3">
        <div className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-[2fr_1fr]">
          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--stamp)]">
              Capability category
            </span>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={fieldClass + " w-full"}
            >
              <option value={ALL}>All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {humanize(c)}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--stamp)]">
              Sort
            </span>
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
              className={fieldClass + " w-full"}
            >
              <option value="use_case_count">Entries, desc</option>
              <option value="agency_count">Agencies, desc</option>
              <option value="short_name">Name, A–Z</option>
            </select>
          </label>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-dotted border-border pt-3 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={ombOnly}
              onChange={(e) => setOmbOnly(e.target.checked)}
              className="h-3.5 w-3.5 accent-[var(--stamp)]"
            />
            OMB standard only
          </label>
          <span className="ml-auto">
            <span className="tabular-nums text-foreground">
              {formatNumber(filtered.length)}
            </span>{" "}
            / {formatNumber(templates.length)} templates
          </span>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex h-40 items-center justify-center border border-dashed border-border font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          — No templates match these filters —
        </div>
      ) : (
        <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((t) => (
            <TemplateCard key={t.id} template={t} />
          ))}
        </div>
      )}
    </div>
  );
}
