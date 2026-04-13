/**
 * Cmd+K / Ctrl+K command palette. Client Component.
 *
 * Data is fetched server-side in the root layout and passed in as a serializable
 * prop (`index`). The palette itself is pure client interaction — cmdk handles
 * fuzzy-matching and keyboard navigation.
 */

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import type { CommandPaletteIndex } from "@/lib/db";
import {
  BarChart3,
  Box,
  Building2,
  FileText,
  Home,
  LayoutDashboard,
  ListFilter,
  ScrollText,
  SplitSquareHorizontal,
  Telescope,
} from "lucide-react";

type Props = {
  index: CommandPaletteIndex;
};

const QUICK_LINKS: Array<{
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  { href: "/", label: "Home", icon: Home },
  { href: "/agencies", label: "Agencies", icon: Building2 },
  { href: "/use-cases", label: "Use Cases", icon: ListFilter },
  { href: "/products", label: "Products", icon: Box },
  { href: "/templates", label: "Templates", icon: ScrollText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/compare", label: "Compare", icon: SplitSquareHorizontal },
  { href: "/about", label: "About", icon: FileText },
];

export function CommandPalette({ index }: Props) {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const go = React.useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router],
  );

  // Cap per-group rendering so the list stays snappy.
  const useCasesTrimmed = index.useCases.slice(0, 300);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search agencies, products, templates, use cases…" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Quick links">
          {QUICK_LINKS.map(({ href, label, icon: Icon }) => (
            <CommandItem
              key={href}
              value={`link ${label}`}
              onSelect={() => go(href)}
            >
              <Icon className="size-4" />
              <span>{label}</span>
              <CommandShortcut>{href}</CommandShortcut>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Agencies">
          {index.agencies.map((a) => (
            <CommandItem
              key={`agency-${a.id}`}
              value={`agency ${a.abbreviation} ${a.name}`}
              onSelect={() => go(`/agencies/${a.abbreviation}`)}
            >
              <Building2 className="size-4" />
              <span className="font-medium tabular-nums mr-1 text-muted-foreground">
                {a.abbreviation}
              </span>
              <span className="truncate">{a.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Products">
          {index.products.map((p) => (
            <CommandItem
              key={`product-${p.id}`}
              value={`product ${p.canonical_name} ${p.vendor ?? ""}`}
              onSelect={() => go(`/products/${p.id}`)}
            >
              <Box className="size-4" />
              <span className="truncate">{p.canonical_name}</span>
              {p.vendor ? (
                <span className="text-xs text-muted-foreground ml-auto">
                  {p.vendor}
                </span>
              ) : null}
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Templates">
          {index.templates.map((t) => (
            <CommandItem
              key={`template-${t.id}`}
              value={`template ${t.short_name ?? ""} ${t.template_text}`}
              onSelect={() => go(`/templates/${t.id}`)}
            >
              <ScrollText className="size-4" />
              <span className="truncate">
                {t.short_name ?? t.template_text.slice(0, 80)}
              </span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Use cases">
          {useCasesTrimmed.map((uc) => (
            <CommandItem
              key={`uc-${uc.id}`}
              value={`usecase ${uc.use_case_name} ${uc.agency_abbreviation}`}
              onSelect={() => uc.slug && go(`/use-cases/${uc.slug}`)}
            >
              <Telescope className="size-4" />
              <span className="font-medium tabular-nums mr-1 text-muted-foreground">
                {uc.agency_abbreviation}
              </span>
              <span className="truncate">{uc.use_case_name}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}

/**
 * Small client-side "Press ⌘K" hint for the nav bar. Clicks also open the
 * palette by dispatching a synthetic keydown so the same `useEffect` handles it.
 */
export function CommandPaletteHint() {
  const trigger = () => {
    window.dispatchEvent(
      new KeyboardEvent("keydown", { key: "k", metaKey: true }),
    );
  };
  return (
    <button
      type="button"
      onClick={trigger}
      className="group inline-flex items-center gap-2 border border-border bg-background px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-[var(--stamp)] hover:text-[var(--stamp)]"
      aria-label="Open command palette"
    >
      <LayoutDashboard className="h-3 w-3" aria-hidden />
      <span>Index</span>
      <kbd className="border border-border bg-background px-1 py-[1px] text-[9px] tracking-widest group-hover:border-[var(--stamp)]">
        ⌘K
      </kbd>
    </button>
  );
}
