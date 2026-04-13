/**
 * Filterable table of use cases (individual or consolidated). Client Component
 * — filter state is local. Data is prepared server-side and passed in as
 * plain-serializable rows.
 */

"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { truncate } from "@/lib/formatting";
import type {
  ConsolidatedWithTags,
  UseCaseWithTags,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const ENTRY_TYPE_COLORS: Record<string, string> = {
  custom_system:
    "bg-slate-100 text-slate-900 border-slate-300 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-700",
  product_deployment:
    "bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-950 dark:text-blue-200 dark:border-blue-800",
  bespoke_application:
    "bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950 dark:text-violet-200 dark:border-violet-800",
  generic_use_pattern:
    "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800",
  product_feature:
    "bg-cyan-100 text-cyan-900 border-cyan-300 dark:bg-cyan-950 dark:text-cyan-200 dark:border-cyan-800",
};

const SCOPE_COLORS: Record<string, string> = {
  enterprise_wide:
    "bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800",
  department:
    "bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-950 dark:text-blue-200 dark:border-blue-800",
  bureau:
    "bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-950 dark:text-blue-200 dark:border-blue-800",
  office:
    "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800",
  team:
    "bg-orange-100 text-orange-900 border-orange-300 dark:bg-orange-950 dark:text-orange-200 dark:border-orange-800",
  pilot:
    "bg-zinc-100 text-zinc-900 border-zinc-300 dark:bg-zinc-900 dark:text-zinc-200 dark:border-zinc-700",
};

function humanize(v: string | null | undefined): string {
  if (!v) return "—";
  return v.replaceAll("_", " ");
}

type IndividualRow = UseCaseWithTags & {
  product_id: number | null;
  product_name?: string | null;
};

// ---------------------------------------------------------------------------
// Individual use cases table
// ---------------------------------------------------------------------------

export function IndividualUseCasesTable({
  rows,
}: {
  rows: IndividualRow[];
}) {
  const [q, setQ] = useState("");
  const [stage, setStage] = useState("");

  const stages = useMemo(() => {
    const set = new Set<string>();
    for (const r of rows) {
      if (r.stage_of_development) set.add(r.stage_of_development);
    }
    return Array.from(set).sort();
  }, [rows]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter((r) => {
      if (stage && r.stage_of_development !== stage) return false;
      if (!needle) return true;
      const hay = [
        r.use_case_name,
        r.bureau_component,
        r.vendor_name,
        r.product_name,
        r.ai_classification,
        r.problem_statement,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(needle);
    });
  }, [rows, q, stage]);

  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No individual use cases reported for this agency.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          type="search"
          placeholder="Search use cases…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="max-w-xs"
        />
        {stages.length > 0 ? (
          <select
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            className="h-8 rounded-lg border border-input bg-background px-2 text-sm"
          >
            <option value="">All stages</option>
            {stages.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        ) : null}
        <span className="ml-auto text-xs text-muted-foreground">
          {filtered.length} of {rows.length}
        </span>
      </div>

      <div className="rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Use case</TableHead>
              <TableHead>Bureau / component</TableHead>
              <TableHead>Stage</TableHead>
              <TableHead>AI classification</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead>Product</TableHead>
              <TableHead>Entry type</TableHead>
              <TableHead>Scope</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((r) => {
              const entryType = r.tags?.entry_type ?? null;
              const scope = r.tags?.deployment_scope ?? null;
              return (
                <TableRow key={r.id}>
                  <TableCell className="max-w-[320px] whitespace-normal">
                    {r.slug ? (
                      <Link
                        href={`/use-cases/${r.slug}`}
                        className="font-medium text-foreground hover:underline"
                      >
                        {r.use_case_name}
                      </Link>
                    ) : (
                      <span className="font-medium text-foreground">
                        {r.use_case_name}
                      </span>
                    )}
                    {r.problem_statement ? (
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {truncate(r.problem_statement, 120)}
                      </p>
                    ) : null}
                  </TableCell>
                  <TableCell className="max-w-[200px] whitespace-normal text-xs text-muted-foreground">
                    {r.bureau_component ?? "—"}
                  </TableCell>
                  <TableCell className="text-xs">
                    {r.stage_of_development ?? "—"}
                  </TableCell>
                  <TableCell className="text-xs">
                    {r.ai_classification ?? "—"}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {r.vendor_name ?? "—"}
                  </TableCell>
                  <TableCell className="text-xs">
                    {r.product_id && r.product_name ? (
                      <Link
                        href={`/products/${r.product_id}`}
                        className="text-foreground hover:underline"
                      >
                        {r.product_name}
                      </Link>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {entryType ? (
                      <Badge
                        variant="outline"
                        className={cn(
                          "capitalize",
                          ENTRY_TYPE_COLORS[entryType],
                        )}
                      >
                        {humanize(entryType)}
                      </Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {scope ? (
                      <Badge
                        variant="outline"
                        className={cn("capitalize", SCOPE_COLORS[scope])}
                      >
                        {humanize(scope)}
                      </Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Consolidated use cases table
// ---------------------------------------------------------------------------

export function ConsolidatedUseCasesTable({
  rows,
}: {
  rows: ConsolidatedWithTags[];
}) {
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((r) =>
      [r.ai_use_case, r.commercial_product, r.agency_uses]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [rows, q]);

  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No consolidated entries reported for this agency.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          type="search"
          placeholder="Search consolidated entries…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="max-w-xs"
        />
        <span className="ml-auto text-xs text-muted-foreground">
          {filtered.length} of {rows.length}
        </span>
      </div>

      <div className="rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>AI use case</TableHead>
              <TableHead>Commercial product</TableHead>
              <TableHead>Agency uses</TableHead>
              <TableHead>Users / licenses</TableHead>
              <TableHead>Entry type</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((r) => {
              const entryType = r.tags?.entry_type ?? null;
              return (
                <TableRow key={r.id}>
                  <TableCell className="max-w-[280px] whitespace-normal font-medium">
                    {r.ai_use_case}
                  </TableCell>
                  <TableCell className="max-w-[220px] whitespace-normal text-xs text-muted-foreground">
                    {r.commercial_product ?? "—"}
                  </TableCell>
                  <TableCell className="max-w-[360px] whitespace-normal text-xs text-muted-foreground">
                    {truncate(r.agency_uses, 180)}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {r.estimated_licenses_users ?? "—"}
                  </TableCell>
                  <TableCell>
                    {entryType ? (
                      <Badge
                        variant="outline"
                        className={cn(
                          "capitalize",
                          ENTRY_TYPE_COLORS[entryType],
                        )}
                      >
                        {humanize(entryType)}
                      </Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
