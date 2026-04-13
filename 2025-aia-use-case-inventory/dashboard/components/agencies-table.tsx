"use client";

/**
 * Client-side filterable + sortable agency directory. The parent Server
 * Component fetches the full joined dataset once and hands it in as a plain
 * array; this component handles URL-param-driven filters, sorting, and
 * row-level navigation.
 *
 * Styled as an editorial data ledger: no card chrome, hairline-ruled filter
 * strip above, small-caps mono header row with a 2px bottom rule, hairline
 * dividers between rows, italic display for the agency name, mono chips
 * for abbreviations and maturity tier, and `tabular-nums` on every number.
 *
 * Filter state lives in the URL so links are shareable. We use
 * `useSearchParams` to read and `router.replace` to write without pushing a
 * new history entry on every keystroke.
 */

import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState, useTransition } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowUpRight, Check, Minus, Search } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { MonoChip } from "@/components/editorial";
import {
  agencyTypeLabel,
  formatNumber,
  formatYoY,
  maturityTierLabel,
} from "@/lib/formatting";

export type AgencyRow = {
  id: number;
  name: string;
  abbreviation: string;
  agency_type: string | null;
  status: string | null;
  total_use_cases: number;
  total_consolidated_entries: number;
  distinct_products_deployed: number;
  maturity_tier: string | null;
  year_over_year_growth: number | null;
  has_enterprise_llm: number | null;
  has_coding_assistants: number | null;
};

type TriState = "any" | "yes" | "no";

const columnHelper = createColumnHelper<AgencyRow>();

/** Map a maturity tier to a MonoChip tone. */
function tierTone(
  tier: string | null | undefined,
): "verified" | "stamp" | "ink" | "muted" {
  switch (tier) {
    case "leading":
      return "verified";
    case "progressing":
      return "ink";
    case "early":
      return "stamp";
    case "minimal":
      return "muted";
    default:
      return "muted";
  }
}

export function AgenciesTable({ rows }: { rows: AgencyRow[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  // Read initial filter state from URL.
  const initialType = searchParams.get("type") ?? "all";
  const initialTier = searchParams.get("tier") ?? "all";
  const initialLLM = (searchParams.get("llm") as TriState | null) ?? "any";
  const initialCoding = (searchParams.get("coding") as TriState | null) ?? "any";
  const initialQuery = searchParams.get("q") ?? "";

  const [type, setType] = useState<string>(initialType);
  const [tier, setTier] = useState<string>(initialTier);
  const [llm, setLLM] = useState<TriState>(initialLLM);
  const [coding, setCoding] = useState<TriState>(initialCoding);
  const [query, setQuery] = useState<string>(initialQuery);
  const [sorting, setSorting] = useState<SortingState>([
    { id: "total_use_cases", desc: true },
  ]);

  // Sync filters back into URL on change (replace, not push).
  function syncUrl(next: {
    type?: string;
    tier?: string;
    llm?: TriState;
    coding?: TriState;
    q?: string;
  }) {
    const params = new URLSearchParams(searchParams.toString());
    const setOrDelete = (
      key: string,
      value: string | undefined,
      defaultValue: string,
    ) => {
      if (value == null || value === defaultValue) params.delete(key);
      else params.set(key, value);
    };
    setOrDelete("type", next.type ?? type, "all");
    setOrDelete("tier", next.tier ?? tier, "all");
    setOrDelete("llm", next.llm ?? llm, "any");
    setOrDelete("coding", next.coding ?? coding, "any");
    setOrDelete("q", next.q ?? query, "");
    const qs = params.toString();
    startTransition(() => {
      router.replace(qs ? `?${qs}` : "?", { scroll: false });
    });
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows.filter((r) => {
      if (type !== "all" && r.agency_type !== type) return false;
      if (tier !== "all") {
        const t = r.maturity_tier ?? "none";
        if (tier === "none" ? t !== "none" : t !== tier) return false;
      }
      if (llm === "yes" && r.has_enterprise_llm !== 1) return false;
      if (llm === "no" && r.has_enterprise_llm === 1) return false;
      if (coding === "yes" && r.has_coding_assistants !== 1) return false;
      if (coding === "no" && r.has_coding_assistants === 1) return false;
      if (q) {
        if (
          !r.name.toLowerCase().includes(q) &&
          !r.abbreviation.toLowerCase().includes(q)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [rows, type, tier, llm, coding, query]);

  const columns = useMemo(
    () => [
      columnHelper.accessor("abbreviation", {
        header: "Code",
        enableSorting: false,
        cell: (info) => (
          <MonoChip tone="ink" size="xs">
            {info.getValue()}
          </MonoChip>
        ),
      }),
      columnHelper.accessor("name", {
        header: "Agency",
        cell: (info) => (
          <span className="font-display text-[1.05rem] italic leading-tight text-foreground transition-[letter-spacing] group-hover:tracking-[-0.01em] group-hover:underline decoration-[var(--stamp)] underline-offset-[3px]">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor("agency_type", {
        header: "Type",
        cell: (info) => {
          const v = info.getValue();
          if (!v)
            return (
              <span className="font-mono text-[11px] text-muted-foreground">
                —
              </span>
            );
          return (
            <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-muted-foreground">
              {agencyTypeLabel(v)}
            </span>
          );
        },
      }),
      columnHelper.accessor(
        (r) => r.total_use_cases + r.total_consolidated_entries,
        {
          id: "total_use_cases",
          header: "Use cases",
          cell: (info) => {
            const r = info.row.original;
            return (
              <div className="text-right font-mono tabular-nums">
                <div className="text-[13px] font-semibold text-foreground">
                  {formatNumber(info.getValue())}
                </div>
                {r.total_consolidated_entries > 0 ? (
                  <div className="text-[10px] text-muted-foreground">
                    {formatNumber(r.total_use_cases)}
                    {" + "}
                    {formatNumber(r.total_consolidated_entries)}
                  </div>
                ) : null}
              </div>
            );
          },
          sortingFn: "basic",
        },
      ),
      columnHelper.accessor("distinct_products_deployed", {
        header: "Products",
        cell: (info) => (
          <div className="text-right font-mono text-[13px] tabular-nums text-foreground">
            {formatNumber(info.getValue())}
          </div>
        ),
      }),
      columnHelper.accessor("maturity_tier", {
        header: "Maturity",
        cell: (info) => {
          const v = info.getValue();
          return (
            <MonoChip tone={tierTone(v)} size="xs">
              {maturityTierLabel(v)}
            </MonoChip>
          );
        },
      }),
      columnHelper.accessor("year_over_year_growth", {
        header: "YoY",
        cell: (info) => {
          const v = info.getValue();
          if (v == null)
            return (
              <span className="font-mono text-[11px] text-muted-foreground">
                —
              </span>
            );
          const pct = v > 1 ? v : v * 100;
          const color =
            pct > 0
              ? "text-[var(--verified)]"
              : pct < 0
                ? "text-[var(--stamp)]"
                : "text-muted-foreground";
          return (
            <span
              className={`font-mono text-[12px] font-semibold tabular-nums ${color}`}
            >
              {formatYoY(v)}
            </span>
          );
        },
        sortingFn: "basic",
      }),
      columnHelper.accessor("has_enterprise_llm", {
        header: "LLM",
        cell: (info) =>
          info.getValue() === 1 ? (
            <Check
              className="size-4 text-[var(--verified)]"
              aria-label="Yes"
            />
          ) : (
            <Minus
              className="size-4 text-muted-foreground/60"
              aria-label="No"
            />
          ),
      }),
      columnHelper.accessor("has_coding_assistants", {
        header: "Coding",
        cell: (info) =>
          info.getValue() === 1 ? (
            <Check
              className="size-4 text-[var(--verified)]"
              aria-label="Yes"
            />
          ) : (
            <Minus
              className="size-4 text-muted-foreground/60"
              aria-label="No"
            />
          ),
      }),
      columnHelper.accessor("status", {
        header: "Status",
        cell: (info) => {
          const v = info.getValue();
          if (!v)
            return (
              <span className="font-mono text-[11px] text-muted-foreground">
                —
              </span>
            );
          return (
            <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-muted-foreground">
              {v}
            </span>
          );
        },
      }),
    ],
    [],
  );

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Filter strip — flat, hairline-ruled, mono labels ----------------- */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-y border-border py-3">
        <div className="flex min-w-[220px] flex-1 items-center gap-2">
          <Search
            className="size-3.5 text-muted-foreground"
            aria-hidden
          />
          <input
            placeholder="Search name or abbreviation"
            value={query}
            onChange={(e) => {
              const v = e.target.value;
              setQuery(v);
              syncUrl({ q: v });
            }}
            className="w-full border-0 bg-transparent font-mono text-[12px] uppercase tracking-[0.08em] text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <LabeledSelect
            label="Type"
            value={type}
            onChange={(v) => {
              setType(v);
              syncUrl({ type: v });
            }}
            options={[
              { value: "all", label: "All types" },
              { value: "CFO_ACT", label: "CFO Act" },
              { value: "INDEPENDENT", label: "Independent" },
              { value: "LEGISLATIVE", label: "Legislative" },
            ]}
          />
          <LabeledSelect
            label="Tier"
            value={tier}
            onChange={(v) => {
              setTier(v);
              syncUrl({ tier: v });
            }}
            options={[
              { value: "all", label: "All tiers" },
              { value: "leading", label: "Leading" },
              { value: "progressing", label: "Progressing" },
              { value: "early", label: "Early" },
              { value: "minimal", label: "Minimal" },
              { value: "none", label: "Unranked" },
            ]}
          />
          <LabeledSelect
            label="LLM"
            value={llm}
            onChange={(v) => {
              const next = v as TriState;
              setLLM(next);
              syncUrl({ llm: next });
            }}
            options={[
              { value: "any", label: "LLM: Any" },
              { value: "yes", label: "Has enterprise LLM" },
              { value: "no", label: "No enterprise LLM" },
            ]}
          />
          <LabeledSelect
            label="Coding"
            value={coding}
            onChange={(v) => {
              const next = v as TriState;
              setCoding(next);
              syncUrl({ coding: next });
            }}
            options={[
              { value: "any", label: "Coding: Any" },
              { value: "yes", label: "Has coding tools" },
              { value: "no", label: "No coding tools" },
            ]}
          />
        </div>
        <div className="ml-auto font-mono text-[10.5px] uppercase tracking-[0.14em] tabular-nums text-muted-foreground">
          {filtered.length} / {rows.length} shown
        </div>
      </div>

      {/* Table — naked, 2px top rule, hairline row dividers --------------- */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[960px] border-collapse">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b-2 border-foreground">
                {hg.headers.map((h) => {
                  const isSortable = h.column.getCanSort();
                  const isNum =
                    h.column.id === "total_use_cases" ||
                    h.column.id === "distinct_products_deployed" ||
                    h.column.id === "year_over_year_growth";
                  return (
                    <th
                      key={h.id}
                      scope="col"
                      className={`px-3 py-2.5 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground ${
                        isNum ? "text-right" : "text-left"
                      }`}
                    >
                      {h.isPlaceholder ? null : isSortable ? (
                        <button
                          type="button"
                          onClick={h.column.getToggleSortingHandler()}
                          className={`inline-flex items-center gap-1 hover:text-foreground ${
                            isNum ? "ml-auto" : ""
                          }`}
                        >
                          {flexRender(
                            h.column.columnDef.header,
                            h.getContext(),
                          )}
                          <span className="text-[var(--stamp)]">
                            {h.column.getIsSorted() === "asc"
                              ? "↑"
                              : h.column.getIsSorted() === "desc"
                                ? "↓"
                                : ""}
                          </span>
                        </button>
                      ) : (
                        flexRender(
                          h.column.columnDef.header,
                          h.getContext(),
                        )
                      )}
                    </th>
                  );
                })}
                <th scope="col" className="w-8" aria-hidden />
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="group cursor-pointer border-b border-border transition-colors hover:bg-[var(--highlight)]/20"
                onClick={() =>
                  router.push(`/agencies/${row.original.abbreviation}`)
                }
              >
                {row.getVisibleCells().map((cell) => {
                  const isNum =
                    cell.column.id === "total_use_cases" ||
                    cell.column.id === "distinct_products_deployed" ||
                    cell.column.id === "year_over_year_growth";
                  return (
                    <td
                      key={cell.id}
                      className={`px-3 py-3 align-middle ${
                        isNum ? "text-right" : ""
                      }`}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  );
                })}
                <td className="pr-2 text-right">
                  <ArrowUpRight className="ml-auto size-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 group-hover:text-[var(--stamp)]" />
                </td>
              </tr>
            ))}
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + 1}
                  className="py-12 text-center font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground"
                >
                  No agencies match the current filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LabeledSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <label className="inline-flex items-center gap-2">
      <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </span>
      <Select
        value={value}
        onValueChange={(v: string | null) => onChange(v ?? "")}
      >
        <SelectTrigger className="h-8 min-w-[140px] rounded-none border-0 border-b border-border bg-transparent font-mono text-[11px] uppercase tracking-[0.08em] shadow-none focus-visible:border-foreground">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem
              key={o.value}
              value={o.value}
              className="font-mono text-[11px] uppercase tracking-[0.08em]"
            >
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
