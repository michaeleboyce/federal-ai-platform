/**
 * Maturity-tier ledger: four broadsheet-style columns, each a ranked list of
 * agency codes at that tier. Roman-numeral kicker, italic display name, a
 * run-in description, and a dense grid of monospace abbreviations.
 */

import Link from "next/link";

type TierBlock = {
  tier: string;
  count: number;
  agencies: Array<{ id: number; name: string; abbreviation: string }>;
};

type TierMeta = {
  kicker: string;
  label: string;
  description: string;
  accent: string;
};

const TIER_META: Record<string, TierMeta> = {
  leading: {
    kicker: "I",
    label: "Leading",
    description:
      "Department-wide LLM + coding tools + agentic systems, ≥ 50 use cases.",
    accent: "var(--verified)",
  },
  progressing: {
    kicker: "II",
    label: "Progressing",
    description:
      "Real inventory with at least one enterprise-wide LLM deployment.",
    accent: "var(--ink)",
  },
  early: {
    kicker: "III",
    label: "Early",
    description:
      "Any generative AI on the books, typically bureau-scoped pilots.",
    accent: "var(--highlight)",
  },
  minimal: {
    kicker: "IV",
    label: "Minimal",
    description: "Fewer than five use cases, or none that are generative.",
    accent: "oklch(0.7 0.01 60)",
  },
};

export function MaturityTierCard({ tiers }: { tiers: TierBlock[] }) {
  const order = ["leading", "progressing", "early", "minimal"];
  const visible = order
    .map((t) => tiers.find((x) => x.tier === t))
    .filter((t): t is TierBlock => !!t);

  return (
    <div className="grid grid-cols-1 gap-x-8 gap-y-8 border-t-2 border-foreground pt-6 sm:grid-cols-2 lg:grid-cols-4">
      {visible.map((block) => {
        const meta = TIER_META[block.tier];
        return (
          <Link
            key={block.tier}
            href={`/agencies?tier=${block.tier}`}
            className="group block"
          >
            <div className="flex items-baseline gap-2.5 border-b border-border pb-2">
              <span
                className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em]"
                style={{ color: meta.accent }}
              >
                {meta.kicker}
              </span>
              <h3 className="flex-1 font-display italic text-[1.45rem] leading-none text-foreground">
                {meta.label}
              </h3>
              <span className="font-mono text-[2rem] leading-none tabular-nums text-foreground transition-colors group-hover:text-[var(--stamp)]">
                {block.count}
              </span>
            </div>
            <p className="mt-3 text-[0.86rem] leading-snug text-muted-foreground">
              {meta.description}
            </p>
            <div className="mt-4 flex flex-wrap gap-1">
              {block.agencies.map((a) => (
                <span
                  key={a.id}
                  title={a.name}
                  className="inline-flex items-center border border-border bg-background px-1.5 py-0.5 font-mono text-[10.5px] font-semibold tracking-[0.04em] text-foreground group-hover:border-foreground"
                >
                  {a.abbreviation}
                </span>
              ))}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
