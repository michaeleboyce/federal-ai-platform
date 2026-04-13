"use client";

/**
 * Sidebar filter panel for the Use Cases Explorer — editorial edition.
 *
 * Every control reads/writes to URL search params so the page can remain
 * a Server Component and the filtering is done in SQL on the server.
 *
 * Multi-select groups are represented as comma-separated param values
 * (e.g. `?entry_type=custom_system,product_deployment`). Single-value
 * filters (search, agency_type) also live in query params. Toggles use
 * a `1` / absent convention.
 *
 * Visually: flat, hairline-ruled sections; mono uppercase labels; no
 * shadcn Card wrapper. Matches the newspaper-filing aesthetic shared
 * across the dashboard.
 */

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback, useMemo, useState, useTransition } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { ChevronDown, Search, X } from "lucide-react";

export interface FilterOption {
  value: string;
  label: string;
}

export interface UseCaseFiltersProps {
  agencies: Array<{ id: number; name: string; abbreviation: string }>;
  products: Array<{ id: number; canonical_name: string; vendor: string | null }>;
  facets: {
    agencyTypes: string[];
    tagEntryTypes: string[];
    tagDeploymentScopes: string[];
    tagAISophistications: string[];
    tagArchitectureTypes: string[];
    tagUseTypes: string[];
    tagHighImpactDesignations: string[];
  };
}

// Human labels for enum values. Anything missing falls back to titleCase
// (see below). Only define entries where we want custom wording.
const LABELS: Record<string, string> = {
  CFO_ACT: "CFO Act Agency",
  INDEPENDENT: "Independent Agency",
  LEGISLATIVE: "Legislative Branch",

  custom_system: "Custom system",
  product_deployment: "Product deployment",
  bespoke_application: "Bespoke application",
  generic_use_pattern: "Generic use pattern",
  product_feature: "Product feature",

  enterprise_wide: "Enterprise-wide",
  department: "Department",
  bureau: "Bureau",
  office: "Office",
  team: "Team",
  pilot: "Pilot",
  unknown: "Unknown",

  general_llm: "General LLM",
  coding_assistant: "Coding assistant",
  agentic: "Agentic",
  classical_ml: "Classical ML",
  computer_vision: "Computer vision",
  nlp_specific: "NLP-specific",
  predictive_analytics: "Predictive analytics",

  inference_only: "Inference only",
  rag_pipeline: "RAG pipeline",
  fine_tuned: "Fine-tuned",
  custom_trained: "Custom trained",
  agentic_workflow: "Agentic workflow",

  mission_critical: "Mission-critical",
  administrative: "Administrative",
  it_operations: "IT operations",
  cybersecurity: "Cybersecurity",
  research: "Research",

  high_impact: "High impact",
  presumed_not_high_impact: "Presumed not high impact",
  not_high_impact: "Not high impact",
};

function labelFor(value: string): string {
  if (LABELS[value]) return LABELS[value];
  return value
    .split(/[_\s]+/)
    .map((w) => (w.length > 0 ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

function parseCsv(v: string | null | undefined): string[] {
  if (!v) return [];
  return v
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

function toggleInCsv(csv: string | null | undefined, value: string): string {
  const set = new Set(parseCsv(csv));
  if (set.has(value)) set.delete(value);
  else set.add(value);
  return Array.from(set).join(",");
}

export function UseCaseFilters({
  agencies,
  products,
  facets,
}: UseCaseFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [searchDraft, setSearchDraft] = useState<string>(
    searchParams.get("q") ?? "",
  );
  const [agencyQuery, setAgencyQuery] = useState<string>("");
  const [productQuery, setProductQuery] = useState<string>("");

  const currentParams = useMemo(
    () => new URLSearchParams(searchParams.toString()),
    [searchParams],
  );

  const pushParams = useCallback(
    (next: URLSearchParams) => {
      next.delete("page");
      const qs = next.toString();
      const href = qs ? `${pathname}?${qs}` : pathname;
      startTransition(() => {
        router.push(href);
      });
    },
    [router, pathname],
  );

  const setSingle = useCallback(
    (key: string, value: string | null) => {
      const next = new URLSearchParams(currentParams.toString());
      if (value && value.length > 0) next.set(key, value);
      else next.delete(key);
      pushParams(next);
    },
    [currentParams, pushParams],
  );

  const toggleMulti = useCallback(
    (key: string, value: string) => {
      const next = new URLSearchParams(currentParams.toString());
      const updated = toggleInCsv(next.get(key), value);
      if (updated.length > 0) next.set(key, updated);
      else next.delete(key);
      pushParams(next);
    },
    [currentParams, pushParams],
  );

  const toggleBool = useCallback(
    (key: string) => {
      const next = new URLSearchParams(currentParams.toString());
      if (next.get(key) === "1") next.delete(key);
      else next.set(key, "1");
      pushParams(next);
    },
    [currentParams, pushParams],
  );

  const clearAll = useCallback(() => {
    startTransition(() => router.push(pathname));
  }, [router, pathname]);

  const submitSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setSingle("q", searchDraft.trim() || null);
    },
    [searchDraft, setSingle],
  );

  const selectedAgencyIds = parseCsv(currentParams.get("agency_ids"));
  const selectedAgencyTypes = parseCsv(currentParams.get("agency_type"));
  const selectedEntryTypes = parseCsv(currentParams.get("entry_type"));
  const selectedSophistication = parseCsv(currentParams.get("sophistication"));
  const selectedProductIds = parseCsv(currentParams.get("product_ids"));
  const selectedScopes = parseCsv(currentParams.get("scope"));
  const selectedArchitectures = parseCsv(currentParams.get("architecture"));
  const selectedUseTypes = parseCsv(currentParams.get("use_type"));
  const selectedHighImpact = parseCsv(currentParams.get("high_impact"));

  const activeCount =
    Array.from(currentParams.keys()).filter((k) => k !== "view" && k !== "page")
      .length;

  const filteredAgencies = useMemo(() => {
    const q = agencyQuery.trim().toLowerCase();
    if (!q) return agencies;
    return agencies.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.abbreviation.toLowerCase().includes(q),
    );
  }, [agencies, agencyQuery]);

  const filteredProducts = useMemo(() => {
    const q = productQuery.trim().toLowerCase();
    if (!q) return products;
    return products.filter(
      (p) =>
        p.canonical_name.toLowerCase().includes(q) ||
        (p.vendor ?? "").toLowerCase().includes(q),
    );
  }, [products, productQuery]);

  return (
    <aside
      className={cn(
        "flex w-full flex-col text-sm",
        isPending && "opacity-60",
      )}
      aria-label="Filters"
    >
      {/* Panel header — editorial eyebrow + hairline rule. */}
      <div className="flex items-end justify-between gap-2 border-b-2 border-foreground pb-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--stamp)]">
            § Filter
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            {activeCount > 0 ? (
              <>
                <span className="tabular-nums text-foreground">
                  {activeCount}
                </span>{" "}
                active
              </>
            ) : (
              <>No filter applied</>
            )}
          </div>
        </div>
        {activeCount > 0 && (
          <button
            type="button"
            onClick={clearAll}
            className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground hover:text-[var(--stamp)]"
          >
            Clear
            <X className="size-3" aria-hidden />
          </button>
        )}
      </div>

      {/* Full-text search */}
      <form onSubmit={submitSearch} className="flex flex-col gap-1.5 pt-4">
        <MonoLabel>Search</MonoLabel>
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            value={searchDraft}
            onChange={(e) => setSearchDraft(e.currentTarget.value)}
            placeholder="name, problem, vendor…"
            className="border-border bg-transparent pl-7 font-mono text-[12px]"
          />
        </div>
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          ↵ Enter to query
        </p>
      </form>

      {/* Agency Type */}
      <FilterGroup title="Agency type">
        {facets.agencyTypes.map((v) => (
          <CheckRow
            key={v}
            checked={selectedAgencyTypes.includes(v)}
            onToggle={() => toggleMulti("agency_type", v)}
            label={labelFor(v)}
          />
        ))}
      </FilterGroup>

      {/* Agency (searchable) */}
      <FilterGroup title="Agency" defaultOpen={false}>
        <div className="mb-2">
          <Input
            value={agencyQuery}
            onChange={(e) => setAgencyQuery(e.currentTarget.value)}
            placeholder="Find agency…"
            className="h-7 border-border bg-transparent font-mono text-[11px]"
          />
        </div>
        <div className="max-h-56 overflow-y-auto pr-1">
          {filteredAgencies.map((a) => (
            <CheckRow
              key={a.id}
              checked={selectedAgencyIds.includes(String(a.id))}
              onToggle={() => toggleMulti("agency_ids", String(a.id))}
              label={
                <span className="flex items-baseline gap-2">
                  <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.06em] text-foreground">
                    {a.abbreviation}
                  </span>
                  <span className="truncate text-[12px] text-muted-foreground">
                    {a.name}
                  </span>
                </span>
              }
            />
          ))}
          {filteredAgencies.length === 0 && (
            <p className="py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              No matches
            </p>
          )}
        </div>
      </FilterGroup>

      {/* Entry type */}
      <FilterGroup title="Entry type">
        {facets.tagEntryTypes.map((v) => (
          <CheckRow
            key={v}
            checked={selectedEntryTypes.includes(v)}
            onToggle={() => toggleMulti("entry_type", v)}
            label={labelFor(v)}
          />
        ))}
      </FilterGroup>

      {/* AI sophistication */}
      <FilterGroup title="AI sophistication">
        {facets.tagAISophistications.map((v) => (
          <CheckRow
            key={v}
            checked={selectedSophistication.includes(v)}
            onToggle={() => toggleMulti("sophistication", v)}
            label={labelFor(v)}
          />
        ))}
      </FilterGroup>

      {/* Product */}
      <FilterGroup title="Product" defaultOpen={false}>
        <div className="mb-2">
          <Input
            value={productQuery}
            onChange={(e) => setProductQuery(e.currentTarget.value)}
            placeholder="Find product…"
            className="h-7 border-border bg-transparent font-mono text-[11px]"
          />
        </div>
        <div className="max-h-56 overflow-y-auto pr-1">
          {filteredProducts.map((p) => (
            <CheckRow
              key={p.id}
              checked={selectedProductIds.includes(String(p.id))}
              onToggle={() => toggleMulti("product_ids", String(p.id))}
              label={
                <span className="flex flex-col">
                  <span className="truncate text-[12px] text-foreground">
                    {p.canonical_name}
                  </span>
                  {p.vendor && (
                    <span className="truncate font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
                      {p.vendor}
                    </span>
                  )}
                </span>
              }
            />
          ))}
          {filteredProducts.length === 0 && (
            <p className="py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              No matches
            </p>
          )}
        </div>
      </FilterGroup>

      {/* Deployment scope */}
      <FilterGroup title="Deployment scope">
        {facets.tagDeploymentScopes.map((v) => (
          <CheckRow
            key={v}
            checked={selectedScopes.includes(v)}
            onToggle={() => toggleMulti("scope", v)}
            label={labelFor(v)}
          />
        ))}
      </FilterGroup>

      {/* Architecture type */}
      <FilterGroup title="Architecture" defaultOpen={false}>
        {facets.tagArchitectureTypes.map((v) => (
          <CheckRow
            key={v}
            checked={selectedArchitectures.includes(v)}
            onToggle={() => toggleMulti("architecture", v)}
            label={labelFor(v)}
          />
        ))}
      </FilterGroup>

      {/* Use type */}
      <FilterGroup title="Use type">
        {facets.tagUseTypes.map((v) => (
          <CheckRow
            key={v}
            checked={selectedUseTypes.includes(v)}
            onToggle={() => toggleMulti("use_type", v)}
            label={labelFor(v)}
          />
        ))}
      </FilterGroup>

      {/* High impact designation */}
      <FilterGroup title="High-impact">
        {facets.tagHighImpactDesignations.map((v) => (
          <CheckRow
            key={v}
            checked={selectedHighImpact.includes(v)}
            onToggle={() => toggleMulti("high_impact", v)}
            label={labelFor(v)}
          />
        ))}
      </FilterGroup>

      {/* Boolean toggles */}
      <FilterGroup title="Attributes">
        <CheckRow
          checked={currentParams.get("coding_tool") === "1"}
          onToggle={() => toggleBool("coding_tool")}
          label="Coding tool"
        />
        <CheckRow
          checked={currentParams.get("general_llm_access") === "1"}
          onToggle={() => toggleBool("general_llm_access")}
          label="General LLM access"
        />
        <CheckRow
          checked={currentParams.get("genai") === "1"}
          onToggle={() => toggleBool("genai")}
          label="Generative AI"
        />
        <CheckRow
          checked={currentParams.get("public_facing") === "1"}
          onToggle={() => toggleBool("public_facing")}
          label="Public facing"
        />
        <CheckRow
          checked={currentParams.get("has_ato") === "1"}
          onToggle={() => toggleBool("has_ato")}
          label="ATO / FedRAMP"
        />
        <CheckRow
          checked={currentParams.get("risk_docs") === "1"}
          onToggle={() => toggleBool("risk_docs")}
          label="Meaningful risk docs"
        />
      </FilterGroup>
    </aside>
  );
}

// -- presentational helpers ---------------------------------------------------

function MonoLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="font-mono text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
      {children}
    </span>
  );
}

function FilterGroup({
  title,
  children,
  defaultOpen = true,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="flex flex-col gap-2 border-t border-border pt-4 mt-4">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center justify-between gap-2 text-left font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground hover:text-foreground"
        aria-expanded={open}
      >
        {title}
        <ChevronDown
          className={cn(
            "size-3 transition-transform",
            open ? "rotate-180" : "rotate-0",
          )}
          aria-hidden
        />
      </button>
      {open && <div className="flex flex-col gap-0.5">{children}</div>}
    </div>
  );
}

function CheckRow({
  checked,
  onToggle,
  label,
}: {
  checked: boolean;
  onToggle: () => void;
  label: React.ReactNode;
}) {
  return (
    <label
      className={cn(
        "flex cursor-pointer items-center gap-2 px-1 py-1 text-[13px] transition-colors",
        "hover:text-[var(--stamp)]",
        checked && "text-foreground",
      )}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggle}
        className="size-3.5 rounded-none border border-border text-foreground focus:ring-1 focus:ring-ring"
      />
      <span className="min-w-0 flex-1 truncate">{label}</span>
    </label>
  );
}
