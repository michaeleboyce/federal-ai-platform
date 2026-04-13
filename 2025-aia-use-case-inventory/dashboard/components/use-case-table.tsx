"use client";

/**
 * Table view for the Use Cases Explorer — editorial edition.
 *
 * Server does the filtering + pagination; this component handles only
 * client-side *sort ordering* of the currently-loaded page. Sort state is
 * held in React state (not URL) because a page of ~100 is small and we
 * don't want to re-run the SQL query just to flip sort direction.
 *
 * Visually: bare editorial rows, 2px top-rule, hairline dividers,
 * monospace columns for agency codes and tags, serif-italic
 * `use_case_name` as the lede.
 */

import Link from "next/link";
import { useMemo, useState } from "react";
import type { UseCaseWithTags } from "@/lib/types";
import { truncate } from "@/lib/formatting";
import { MonoChip } from "@/components/editorial";
import { ArrowDown, ArrowUp, ArrowUpDown, Code2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

type SortKey =
  | "agency"
  | "name"
  | "bureau"
  | "stage"
  | "classification"
  | "vendor"
  | "entry_type"
  | "scope";
type SortDir = "asc" | "desc";

export interface UseCaseTableProps {
  rows: UseCaseWithTags[];
}

export function UseCaseTable({ rows }: UseCaseTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => compareRows(a, b, sortKey));
    if (sortDir === "desc") copy.reverse();
    return copy;
  }, [rows, sortKey, sortDir]);

  const onSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  if (rows.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 border-t-2 border-foreground py-14 text-center">
        <p className="font-display italic text-xl text-foreground">
          No entries match the current filter.
        </p>
        <Link
          href="/use-cases"
          className="inline-flex items-center border border-border bg-background px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-[var(--stamp)] hover:text-[var(--stamp)]"
        >
          Clear filters
        </Link>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-t-2 border-foreground border-b border-border">
            <SortableHead label="Agency" k="agency" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <SortableHead label="Use case" k="name" activeKey={sortKey} dir={sortDir} onSort={onSort} className="min-w-[280px]" />
            <SortableHead label="Bureau" k="bureau" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <SortableHead label="Stage" k="stage" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <SortableHead label="Class." k="classification" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <SortableHead label="Vendor" k="vendor" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <SortableHead label="Entry" k="entry_type" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <SortableHead label="Scope" k="scope" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <th className="w-16 px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Flags
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={row.id}
              className="border-b border-border align-top transition-colors hover:bg-[color-mix(in_oklab,var(--highlight)_14%,transparent)]"
            >
              <td className="px-3 py-3">
                {row.agency_abbreviation && (
                  <MonoChip
                    href={`/agencies/${row.agency_abbreviation}`}
                    tone="stamp"
                    size="xs"
                  >
                    {row.agency_abbreviation}
                  </MonoChip>
                )}
              </td>
              <td className="max-w-[360px] whitespace-normal px-3 py-3">
                <Link
                  href={row.slug ? `/use-cases/${row.slug}` : "#"}
                  className="font-display italic text-[1.05rem] leading-snug text-foreground hover:text-[var(--stamp)] hover:underline"
                >
                  {row.use_case_name}
                </Link>
                {row.problem_statement && (
                  <p className="mt-1 text-[12px] leading-snug text-muted-foreground">
                    {truncate(row.problem_statement, 120)}
                  </p>
                )}
              </td>
              <td className="px-3 py-3 text-[12px] text-muted-foreground">
                {row.bureau_component ?? "—"}
              </td>
              <td className="px-3 py-3">
                {row.stage_of_development ? (
                  <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-foreground">
                    {truncate(stageLabel(row.stage_of_development), 28)}
                  </span>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </td>
              <td className="px-3 py-3 text-[12px] text-muted-foreground">
                {truncate(row.ai_classification ?? "—", 32)}
              </td>
              <td className="px-3 py-3 font-mono text-[11px] uppercase tracking-[0.06em] text-muted-foreground">
                {row.vendor_name ?? "—"}
              </td>
              <td className="px-3 py-3">
                {row.tags?.entry_type ? (
                  <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-foreground">
                    {row.tags.entry_type.replace(/_/g, " ")}
                  </span>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </td>
              <td className="px-3 py-3">
                {row.tags?.deployment_scope ? (
                  <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-foreground">
                    {row.tags.deployment_scope.replace(/_/g, " ")}
                  </span>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </td>
              <td className="px-3 py-3">
                <div className="flex items-center gap-1">
                  {row.tags?.is_coding_tool === 1 && (
                    <Code2
                      className="size-3.5 text-[var(--stamp)]"
                      aria-label="Coding tool"
                    />
                  )}
                  {row.tags?.is_general_llm_access === 1 && (
                    <Sparkles
                      className="size-3.5 text-[var(--verified)]"
                      aria-label="General LLM access"
                    />
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SortableHead({
  label,
  k,
  activeKey,
  dir,
  onSort,
  className,
}: {
  label: string;
  k: SortKey;
  activeKey: SortKey;
  dir: SortDir;
  onSort: (k: SortKey) => void;
  className?: string;
}) {
  const isActive = activeKey === k;
  return (
    <th
      className={cn(
        "px-3 py-2 font-mono text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => onSort(k)}
        className={cn(
          "inline-flex items-center gap-1 transition-colors hover:text-[var(--stamp)]",
          isActive && "text-foreground",
        )}
      >
        {label}
        {isActive ? (
          dir === "asc" ? (
            <ArrowUp className="size-3" aria-hidden />
          ) : (
            <ArrowDown className="size-3" aria-hidden />
          )
        ) : (
          <ArrowUpDown className="size-3 opacity-40" aria-hidden />
        )}
      </button>
    </th>
  );
}

function stageLabel(s: string): string {
  return s.split(/[–\-]/)[0].trim();
}

function compareRows(
  a: UseCaseWithTags,
  b: UseCaseWithTags,
  key: SortKey,
): number {
  const pick = (r: UseCaseWithTags): string => {
    switch (key) {
      case "agency":
        return r.agency_abbreviation ?? "";
      case "name":
        return r.use_case_name ?? "";
      case "bureau":
        return r.bureau_component ?? "";
      case "stage":
        return r.stage_of_development ?? "";
      case "classification":
        return r.ai_classification ?? "";
      case "vendor":
        return r.vendor_name ?? "";
      case "entry_type":
        return r.tags?.entry_type ?? "";
      case "scope":
        return r.tags?.deployment_scope ?? "";
      default:
        return "";
    }
  };
  return pick(a).localeCompare(pick(b), "en", { sensitivity: "base" });
}
