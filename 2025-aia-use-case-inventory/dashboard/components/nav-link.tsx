/**
 * Client-side nav link wrapper. Reads the current path with `usePathname`
 * and exposes an "active" state via a `data-active` attribute so callers
 * can style it however they want with Tailwind's `data-[active=true]:` variant.
 * Legacy class-merging behaviour is preserved for non-styled callers.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

type Props = {
  href: string;
  children: React.ReactNode;
  /** Optional extra classes. If omitted, a sensible default pill style is applied. */
  className?: string;
};

const DEFAULT_CLASSES = cn(
  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
  "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
  "data-[active=true]:bg-accent data-[active=true]:text-accent-foreground",
);

export function NavLink({ href, children, className }: Props) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      data-active={isActive ? "true" : undefined}
      className={className ?? DEFAULT_CLASSES}
    >
      {children}
    </Link>
  );
}
