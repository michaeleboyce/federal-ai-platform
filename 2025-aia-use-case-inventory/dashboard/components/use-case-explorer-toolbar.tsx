"use client";

/**
 * Toolbar for the Use Cases Explorer that sits above the results grid/table.
 * Editorial aesthetic: flat mono buttons, no rounded corners, vermilion
 * hover tint on the active state.
 *
 * Controls:
 *   - view toggle (table / grid) — URL param `view`
 *   - CSV export for the currently-filtered rows (client-side transform of
 *     the data already fetched on the server)
 *   - pagination (prev/next + page label)
 */

import Link from "next/link";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback, useMemo } from "react";
import type { UseCaseWithTags } from "@/lib/types";
import { Download, LayoutGrid, Table as TableIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function ViewToggle() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const view = searchParams.get("view") === "grid" ? "grid" : "table";

  const setView = useCallback(
    (next: "table" | "grid") => {
      const params = new URLSearchParams(searchParams.toString());
      if (next === "grid") params.set("view", "grid");
      else params.delete("view");
      const qs = params.toString();
      router.push(qs ? `${pathname}?${qs}` : pathname);
    },
    [router, pathname, searchParams],
  );

  return (
    <div className="inline-flex items-stretch border border-border bg-background">
      <button
        type="button"
        onClick={() => setView("table")}
        className={cn(
          "inline-flex items-center gap-1.5 border-r border-border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors",
          view === "table"
            ? "bg-foreground text-background"
            : "text-muted-foreground hover:text-[var(--stamp)]",
        )}
        aria-pressed={view === "table"}
      >
        <TableIcon className="size-3" aria-hidden />
        Table
      </button>
      <button
        type="button"
        onClick={() => setView("grid")}
        className={cn(
          "inline-flex items-center gap-1.5 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors",
          view === "grid"
            ? "bg-foreground text-background"
            : "text-muted-foreground hover:text-[var(--stamp)]",
        )}
        aria-pressed={view === "grid"}
      >
        <LayoutGrid className="size-3" aria-hidden />
        Grid
      </button>
    </div>
  );
}

/** Pure client-side CSV export of the currently-loaded page. */
export function ExportCsvButton({ rows }: { rows: UseCaseWithTags[] }) {
  const onClick = useCallback(() => {
    const headers = [
      "agency_abbreviation",
      "agency_name",
      "use_case_id",
      "slug",
      "use_case_name",
      "bureau_component",
      "stage_of_development",
      "ai_classification",
      "vendor_name",
      "product_name",
      "is_high_impact",
      "entry_type",
      "ai_sophistication",
      "deployment_scope",
      "architecture_type",
      "use_type",
      "is_coding_tool",
      "is_general_llm_access",
      "is_generative_ai",
      "has_ato_or_fedramp",
    ];
    const body = rows.map((r) => [
      r.agency_abbreviation ?? "",
      r.agency_name ?? "",
      r.use_case_id ?? "",
      r.slug ?? "",
      r.use_case_name ?? "",
      r.bureau_component ?? "",
      r.stage_of_development ?? "",
      r.ai_classification ?? "",
      r.vendor_name ?? "",
      r.product_name ?? "",
      r.is_high_impact ?? "",
      r.tags?.entry_type ?? "",
      r.tags?.ai_sophistication ?? "",
      r.tags?.deployment_scope ?? "",
      r.tags?.architecture_type ?? "",
      r.tags?.use_type ?? "",
      r.tags?.is_coding_tool ?? "",
      r.tags?.is_general_llm_access ?? "",
      r.tags?.is_generative_ai ?? "",
      r.tags?.has_ato_or_fedramp ?? "",
    ]);
    const csv = [headers, ...body]
      .map((row) =>
        row
          .map((cell) => {
            const s = String(cell ?? "");
            if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
            return s;
          })
          .join(","),
      )
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ai-use-cases-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }, [rows]);

  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1.5 border border-border bg-background px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-[var(--stamp)] hover:text-[var(--stamp)]"
    >
      <Download className="size-3" aria-hidden />
      Export CSV
    </button>
  );
}

export function Pagination({
  page,
  totalPages,
}: {
  page: number;
  totalPages: number;
}) {
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const buildHref = useMemo(() => {
    return (p: number) => {
      const params = new URLSearchParams(searchParams.toString());
      if (p <= 1) params.delete("page");
      else params.set("page", String(p));
      const qs = params.toString();
      return qs ? `${pathname}?${qs}` : pathname;
    };
  }, [pathname, searchParams]);

  if (totalPages <= 1) return null;

  return (
    <nav className="flex items-center gap-3" aria-label="Pagination">
      <LinkButton href={buildHref(page - 1)} disabled={page <= 1}>
        ← Prev
      </LinkButton>
      <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        Page{" "}
        <span className="tabular-nums text-foreground">{page}</span>
        {" · "}of <span className="tabular-nums">{totalPages}</span>
      </span>
      <LinkButton href={buildHref(page + 1)} disabled={page >= totalPages}>
        Next →
      </LinkButton>
    </nav>
  );
}

function LinkButton({
  href,
  disabled,
  children,
}: {
  href: string;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  if (disabled) {
    return (
      <span className="inline-flex h-7 cursor-not-allowed items-center border border-border px-2.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/50">
        {children}
      </span>
    );
  }
  return (
    <Link
      href={href}
      className="inline-flex h-7 items-center border border-border px-2.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-[var(--stamp)] hover:text-[var(--stamp)]"
    >
      {children}
    </Link>
  );
}
