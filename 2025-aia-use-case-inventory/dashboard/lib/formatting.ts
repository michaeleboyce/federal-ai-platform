/**
 * Small pure formatting helpers shared across server and client components.
 * No DB access, no React, no side effects.
 */

export function formatNumber(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US").format(n);
}

/**
 * Format a fraction as a percent. Accepts either a ratio (0–1) or a percent
 * number (0–100). If the value is > 1 we assume it is already in percent.
 */
export function formatPercent(
  value: number | null | undefined,
  digits = 1,
): string {
  if (value == null || Number.isNaN(value)) return "—";
  const pct = value > 1 ? value : value * 100;
  return `${pct.toFixed(digits)}%`;
}

/** Year-over-year growth. Positive values get a leading '+'. */
export function formatYoY(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const pct = value > 1 ? value : value * 100;
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

/** Format an ISO date string as e.g. "Apr 11, 2026". Null-safe. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Compact zero-padded uppercase form used in the Dateline strip. */
export function formatDatelineDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d
    .toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "2-digit",
    })
    .toUpperCase();
}

/** snake_case → Title Case with spaces. Used for chart legend labels. */
export function humanize(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .split("_")
    .map((p) => (p ? p.charAt(0).toUpperCase() + p.slice(1) : ""))
    .join(" ");
}

/** Human label for the `agency_type` enum stored in the DB. */
export function agencyTypeLabel(type: string | null | undefined): string {
  switch (type) {
    case "CFO_ACT":
      return "CFO Act Agency";
    case "INDEPENDENT":
      return "Independent Agency";
    case "LEGISLATIVE":
      return "Legislative Branch";
    default:
      return type ?? "—";
  }
}

/**
 * Tailwind class string for maturity tier badges. Kept as raw class literals
 * so the Tailwind JIT can see them.
 */
export function maturityTierColor(tier: string | null | undefined): string {
  switch (tier) {
    case "leading":
      return "bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800";
    case "progressing":
      return "bg-blue-100 text-blue-900 border-blue-300 dark:bg-blue-950 dark:text-blue-200 dark:border-blue-800";
    case "early":
      return "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800";
    case "minimal":
      return "bg-zinc-100 text-zinc-900 border-zinc-300 dark:bg-zinc-900 dark:text-zinc-200 dark:border-zinc-700";
    default:
      return "bg-zinc-100 text-zinc-700 border-zinc-300 dark:bg-zinc-900 dark:text-zinc-300 dark:border-zinc-700";
  }
}

export function maturityTierLabel(tier: string | null | undefined): string {
  switch (tier) {
    case "leading":
      return "Leading";
    case "progressing":
      return "Progressing";
    case "early":
      return "Early";
    case "minimal":
      return "Minimal";
    default:
      return "Unranked";
  }
}

/** Shorten long strings for table cells. */
export function truncate(s: string | null | undefined, n = 140): string {
  if (!s) return "";
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

/** Render a boolean-ish SQLite integer as Yes / No / —. */
export function formatBoolFlag(v: number | null | undefined): string {
  if (v === 1) return "Yes";
  if (v === 0) return "No";
  return "—";
}
