/**
 * Editorial masthead. Big italic nameplate, hairline-ruled navigation, and a
 * small command-palette chip on the right. Designed to sit directly below
 * the Dateline strip so the two together read like a newspaper flag.
 */

import Link from "next/link";
import { NavLink } from "./nav-link";
import { CommandPaletteHint } from "./command-palette";

const LINKS: Array<{ href: string; label: string; kicker: string }> = [
  { href: "/agencies", label: "Agencies", kicker: "I" },
  { href: "/use-cases", label: "Use Cases", kicker: "II" },
  { href: "/products", label: "Products", kicker: "III" },
  { href: "/templates", label: "Templates", kicker: "IV" },
  { href: "/analytics", label: "Analytics", kicker: "V" },
  { href: "/compare", label: "Compare", kicker: "VI" },
  { href: "/about", label: "Colophon", kicker: "§" },
];

export function Navigation() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/92 backdrop-blur supports-[backdrop-filter]:bg-background/75">
      <div className="mx-auto max-w-[1400px] px-4 md:px-8">
        {/* Masthead */}
        <div className="flex items-baseline justify-between gap-6 pt-4 pb-1">
          <Link
            href="/"
            aria-label="Federal AI Use Case Inventory — home"
            className="group inline-flex items-baseline gap-2"
          >
            <span className="font-display italic text-[1.8rem] leading-none tracking-[-0.02em] text-foreground transition-[letter-spacing] duration-500 group-hover:tracking-[-0.005em] md:text-[2.15rem]">
              The Federal AI
            </span>
            <span className="font-display text-[1.8rem] leading-none tracking-[-0.02em] text-foreground md:text-[2.15rem]">
              Inventory
            </span>
          </Link>
          <div className="hidden items-center gap-3 md:flex">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              ⌘K · Lookup
            </span>
            <CommandPaletteHint />
          </div>
        </div>

        {/* Section rail */}
        <nav className="mt-1 flex items-stretch gap-0 overflow-x-auto border-t border-border/70 text-sm">
          {LINKS.map((link) => (
            <NavLink
              key={link.href}
              href={link.href}
              className="group relative -mt-px flex items-baseline gap-2 whitespace-nowrap border-t-2 border-transparent px-3 py-2.5 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:text-foreground data-[active=true]:border-[var(--stamp)] data-[active=true]:text-foreground md:px-4"
            >
              <span
                aria-hidden
                className="text-[9px] font-normal text-muted-foreground/70 group-data-[active=true]:text-[var(--stamp)]"
              >
                {link.kicker}
              </span>
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
