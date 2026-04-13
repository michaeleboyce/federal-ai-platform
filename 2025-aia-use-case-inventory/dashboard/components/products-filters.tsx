/**
 * Client-side filter bar + grid for the /products page — editorial.
 *
 * A thin ruled row above the grid with monospace labels and native
 * <input>/<select> controls styled as hairline boxes. No shadcn Card,
 * no Select-in-Card; filters feel like the filing strip of a broadsheet.
 */

"use client";

import { useMemo, useState } from "react";
import { ProductCard } from "@/components/product-card";
import { humanize, formatNumber } from "@/lib/formatting";
import type { ProductWithCounts } from "@/lib/types";

type SortKey = "agency_count" | "use_case_count" | "name";

type Props = {
  products: ProductWithCounts[];
  /** id → canonical_name, used so cards can show "Part of: <parent>". */
  parentNames: Record<number, string>;
};

const ALL = "__all__";

const PRODUCT_TYPES = [
  "LLM",
  "coding_assistant",
  "security_tool",
  "productivity",
  "legal_research",
  "nlp_specific",
  "computer_vision",
  "ml_platform",
  "custom",
];

const fieldClass =
  "h-8 min-w-0 border border-border bg-background px-2 font-mono text-[11px] uppercase tracking-[0.08em] text-foreground focus:border-foreground focus:outline-none";

export function ProductsFilters({ products, parentNames }: Props) {
  const [search, setSearch] = useState("");
  const [vendor, setVendor] = useState<string>(ALL);
  const [productType, setProductType] = useState<string>(ALL);
  const [frontierOnly, setFrontierOnly] = useState(false);
  const [genaiOnly, setGenaiOnly] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("agency_count");

  const vendors = useMemo(() => {
    const set = new Set<string>();
    for (const p of products) if (p.vendor) set.add(p.vendor);
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [products]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const rows = products.filter((p) => {
      if (q && !p.canonical_name.toLowerCase().includes(q)) return false;
      if (vendor !== ALL && p.vendor !== vendor) return false;
      if (productType !== ALL && p.product_type !== productType) return false;
      if (frontierOnly && p.is_frontier_llm !== 1) return false;
      if (genaiOnly && p.is_generative_ai !== 1) return false;
      return true;
    });
    rows.sort((a, b) => {
      if (sortKey === "name")
        return a.canonical_name.localeCompare(b.canonical_name);
      if (sortKey === "use_case_count")
        return b.use_case_count - a.use_case_count;
      return b.agency_count - a.agency_count;
    });
    return rows;
  }, [products, search, vendor, productType, frontierOnly, genaiOnly, sortKey]);

  return (
    <div className="flex flex-col gap-8">
      <div className="border-y-2 border-foreground py-3">
        <div className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-[1.6fr_1fr_1fr_1fr]">
          <FilterField label="Search">
            <input
              type="search"
              placeholder="Product name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={fieldClass + " w-full"}
            />
          </FilterField>

          <FilterField label="Vendor">
            <select
              value={vendor}
              onChange={(e) => setVendor(e.target.value)}
              className={fieldClass + " w-full"}
            >
              <option value={ALL}>All vendors</option>
              {vendors.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Type">
            <select
              value={productType}
              onChange={(e) => setProductType(e.target.value)}
              className={fieldClass + " w-full"}
            >
              <option value={ALL}>All types</option>
              {PRODUCT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {humanize(t)}
                </option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Sort">
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
              className={fieldClass + " w-full"}
            >
              <option value="agency_count">Agencies, desc</option>
              <option value="use_case_count">Entries, desc</option>
              <option value="name">Name, A–Z</option>
            </select>
          </FilterField>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-dotted border-border pt-3 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={frontierOnly}
              onChange={(e) => setFrontierOnly(e.target.checked)}
              className="h-3.5 w-3.5 accent-[var(--stamp)]"
            />
            Frontier LLM only
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={genaiOnly}
              onChange={(e) => setGenaiOnly(e.target.checked)}
              className="h-3.5 w-3.5 accent-[var(--stamp)]"
            />
            Generative AI only
          </label>
          <span className="ml-auto">
            <span className="tabular-nums text-foreground">
              {formatNumber(filtered.length)}
            </span>{" "}
            / {formatNumber(products.length)} products
          </span>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex h-40 items-center justify-center border border-dashed border-border font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          — No products match these filters —
        </div>
      ) : (
        <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              parentName={
                p.parent_product_id != null
                  ? (parentNames[p.parent_product_id] ?? null)
                  : null
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--stamp)]">
        {label}
      </span>
      {children}
    </label>
  );
}
