import Link from "next/link";
import type { ReactNode } from "react";

/* --------------------------------------------------------------------- */
/* Section                                                                */
/* --------------------------------------------------------------------- */
/* A numbered section with a sticky left rail (§, italic display heading, */
/* optional lede) and a content column to its right. Use as the standard  */
/* page-section primitive across the dashboard.                           */
/* --------------------------------------------------------------------- */

export function Section({
  number,
  title,
  lede,
  children,
  className = "mt-16 md:mt-24",
}: {
  number: string;
  title: string;
  lede?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`ink-in grid grid-cols-12 gap-x-6 ${className}`}>
      <header className="col-span-12 mb-8 md:col-span-3">
        <div className="sticky top-32 space-y-1">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--stamp)]">
            § {number}
          </div>
          <h2 className="font-display italic text-[2rem] leading-[0.95] tracking-[-0.02em] text-foreground md:text-[2.6rem]">
            {title}
          </h2>
          {lede ? (
            <p className="mt-3 max-w-xs text-sm leading-snug text-muted-foreground md:pr-6">
              {lede}
            </p>
          ) : null}
        </div>
      </header>
      <div className="col-span-12 md:col-span-9">{children}</div>
    </section>
  );
}

/* --------------------------------------------------------------------- */
/* Figure                                                                 */
/* --------------------------------------------------------------------- */
/* A chart or table with an eyebrow, a thick top rule, and a mono caption */
/* below. The replacement for shadcn Card in editorial pages.             */
/* --------------------------------------------------------------------- */

export function Figure({
  eyebrow,
  caption,
  children,
  className = "",
}: {
  eyebrow?: string;
  caption?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <figure className={className}>
      {eyebrow ? <div className="eyebrow mb-3">{eyebrow}</div> : null}
      <div className="border-t-2 border-foreground pt-4">{children}</div>
      {caption ? (
        <figcaption className="mt-3 font-mono text-[11px] text-muted-foreground">
          {caption}
        </figcaption>
      ) : null}
    </figure>
  );
}

/* --------------------------------------------------------------------- */
/* Eyebrow                                                                */
/* --------------------------------------------------------------------- */

export function Eyebrow({
  children,
  color,
}: {
  children: ReactNode;
  color?: "stamp" | "verified" | "muted";
}) {
  const tone =
    color === "stamp"
      ? "!text-[var(--stamp)]"
      : color === "verified"
        ? "!text-[var(--verified)]"
        : "";
  return <div className={`eyebrow ${tone}`}>{children}</div>;
}

/* --------------------------------------------------------------------- */
/* MonoChip                                                               */
/* --------------------------------------------------------------------- */
/* Monospace agency / code / label chip. Link-aware via an optional href. */
/* --------------------------------------------------------------------- */

export function MonoChip({
  children,
  href,
  title,
  tone = "ink",
  size = "sm",
}: {
  children: ReactNode;
  href?: string;
  title?: string;
  tone?: "ink" | "stamp" | "verified" | "muted";
  size?: "xs" | "sm" | "md";
}) {
  const base =
    "inline-flex items-center border bg-background font-mono font-semibold uppercase tracking-[0.06em] transition-colors";
  const sizing =
    size === "xs"
      ? "px-1.5 py-0.5 text-[10px]"
      : size === "md"
        ? "px-2.5 py-1 text-[12px]"
        : "px-2 py-0.5 text-[11px]";
  const toneClasses =
    tone === "stamp"
      ? "border-border text-foreground hover:border-[var(--stamp)] hover:text-[var(--stamp)]"
      : tone === "verified"
        ? "border-border text-foreground hover:border-[var(--verified)] hover:text-[var(--verified)]"
        : tone === "muted"
          ? "border-border text-muted-foreground hover:text-foreground"
          : "border-border text-foreground hover:border-foreground";

  const className = `${base} ${sizing} ${toneClasses}`;

  if (href) {
    return (
      <Link href={href} title={title} className={className}>
        {children}
      </Link>
    );
  }
  return (
    <span title={title} className={className}>
      {children}
    </span>
  );
}

/* --------------------------------------------------------------------- */
/* Editorial color maps — the single source for enum → hex color          */
/* --------------------------------------------------------------------- */

export const ENTRY_TYPE_COLORS: Record<string, string> = {
  custom_system: "#64748b",
  product_deployment: "#3b82f6",
  bespoke_application: "#8b5cf6",
  generic_use_pattern: "#f59e0b",
  product_feature: "#06b6d4",
};

export const ENTRY_TYPE_LABELS: Record<string, string> = {
  custom_system: "Custom system",
  product_deployment: "Product deployment",
  bespoke_application: "Bespoke application",
  generic_use_pattern: "Generic use pattern",
  product_feature: "Product feature",
};

export const SOPHISTICATION_COLORS: Record<string, string> = {
  general_llm: "#3b82f6",
  coding_assistant: "#8b5cf6",
  agentic: "#a855f7",
  classical_ml: "#64748b",
  computer_vision: "#06b6d4",
  nlp_specific: "#14b8a6",
  predictive_analytics: "#6366f1",
};

export const SOPHISTICATION_LABELS: Record<string, string> = {
  general_llm: "General LLM",
  coding_assistant: "Coding assistant",
  agentic: "Agentic",
  classical_ml: "Classical ML",
  computer_vision: "Computer vision",
  nlp_specific: "NLP (non-generative)",
  predictive_analytics: "Predictive analytics",
};

export const SCOPE_COLORS: Record<string, string> = {
  enterprise_wide: "#10b981",
  department: "#059669",
  bureau: "#3b82f6",
  office: "#f59e0b",
  team: "#f97316",
  pilot: "#64748b",
  unknown: "#94a3b8",
};

export const SCOPE_LABELS: Record<string, string> = {
  enterprise_wide: "Enterprise-wide",
  department: "Department",
  bureau: "Bureau",
  office: "Office",
  team: "Team",
  pilot: "Pilot",
  unknown: "Unknown",
};

export const TIER_ACCENTS: Record<string, string> = {
  leading: "var(--verified)",
  progressing: "var(--ink)",
  early: "var(--highlight)",
  minimal: "oklch(0.7 0.01 60)",
};
