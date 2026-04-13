/**
 * Agency multi-picker for the /compare page. Client Component.
 *
 * URL is the source of truth: `?a=HHS&a=DHS&a=State`. Selection changes push a
 * new URL; the server re-renders the comparison grid with fresh data.
 *
 * Visual: flat, hairline-ruled combobox strip; selected agencies are rendered
 * as mono-code chips with italic display names; the search input is a naked
 * underlined line, not a rounded pill.
 */

"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { X } from "lucide-react";

type AgencyOption = {
  id: number;
  name: string;
  abbreviation: string;
};

const MAX_AGENCIES = 4;

export function ComparePicker({
  options,
  selected,
}: {
  options: AgencyOption[];
  selected: string[];
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = React.useState("");
  const [openDropdown, setOpenDropdown] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Close the dropdown on outside click.
  React.useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpenDropdown(false);
      }
    };
    window.addEventListener("mousedown", onClick);
    return () => window.removeEventListener("mousedown", onClick);
  }, []);

  const updateSelected = React.useCallback(
    (next: string[]) => {
      const params = new URLSearchParams(searchParams.toString());
      params.delete("a");
      for (const abbr of next) params.append("a", abbr);
      router.push(`/compare?${params.toString()}`);
    },
    [router, searchParams],
  );

  const selectedSet = new Set(selected.map((s) => s.toUpperCase()));
  const available = options.filter(
    (o) => !selectedSet.has(o.abbreviation.toUpperCase()),
  );
  const filtered = query
    ? available.filter(
        (o) =>
          o.abbreviation.toLowerCase().includes(query.toLowerCase()) ||
          o.name.toLowerCase().includes(query.toLowerCase()),
      )
    : available;

  const atCap = selected.length >= MAX_AGENCIES;

  return (
    <div ref={containerRef} className="relative flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        {selected.length === 0 ? (
          <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            No agencies selected —
          </span>
        ) : (
          selected.map((abbr) => {
            const opt = options.find(
              (o) => o.abbreviation.toUpperCase() === abbr.toUpperCase(),
            );
            return (
              <span
                key={abbr}
                className="inline-flex items-center gap-2 border border-border bg-background px-2 py-1"
                title={opt?.name ?? abbr}
              >
                <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.08em] text-foreground">
                  {opt?.abbreviation ?? abbr}
                </span>
                {opt?.name ? (
                  <span className="hidden max-w-[200px] truncate font-display text-[13px] italic text-muted-foreground sm:inline">
                    {opt.name}
                  </span>
                ) : null}
                <button
                  type="button"
                  onClick={() =>
                    updateSelected(selected.filter((a) => a !== abbr))
                  }
                  className="text-muted-foreground transition-colors hover:text-[var(--stamp)]"
                  aria-label={`Remove ${abbr}`}
                >
                  <X className="size-3.5" />
                </button>
              </span>
            );
          })
        )}

        <div className="relative ml-auto w-full sm:w-72">
          <div className="flex items-baseline border-b border-border focus-within:border-foreground">
            <span className="shrink-0 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              Add
            </span>
            <input
              type="text"
              placeholder={
                atCap
                  ? `Max ${MAX_AGENCIES} agencies`
                  : "search name or abbreviation…"
              }
              value={query}
              disabled={atCap}
              onChange={(e) => {
                setQuery(e.target.value);
                setOpenDropdown(true);
              }}
              onFocus={() => setOpenDropdown(true)}
              className="ml-2 w-full border-0 bg-transparent py-1.5 font-mono text-[12px] uppercase tracking-[0.06em] text-foreground placeholder:text-muted-foreground/70 focus:outline-none disabled:text-muted-foreground"
            />
          </div>
          {openDropdown && filtered.length > 0 && !atCap ? (
            <div className="absolute right-0 top-full z-20 mt-1 max-h-72 w-full overflow-y-auto border border-border bg-background shadow-lg">
              {filtered.slice(0, 30).map((o) => (
                <button
                  key={o.id}
                  type="button"
                  onClick={() => {
                    updateSelected([...selected, o.abbreviation]);
                    setQuery("");
                    setOpenDropdown(false);
                  }}
                  className="flex w-full items-baseline gap-3 border-b border-border px-3 py-2 text-left last:border-0 hover:bg-[var(--highlight)]/30"
                >
                  <span className="w-14 shrink-0 font-mono text-[11px] font-semibold uppercase tracking-[0.08em] tabular-nums text-foreground">
                    {o.abbreviation}
                  </span>
                  <span className="truncate font-display text-[14px] italic text-foreground">
                    {o.name}
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {selected.length > 0 ? (
          <button
            type="button"
            onClick={() => updateSelected([])}
            className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground transition-colors hover:text-[var(--stamp)]"
          >
            Clear all
          </button>
        ) : null}
      </div>

      {selected.length > 0 ? (
        <p className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-muted-foreground">
          Comparing {selected.length} of up to {MAX_AGENCIES} · share this URL
          to share the comparison.
        </p>
      ) : null}
    </div>
  );
}
