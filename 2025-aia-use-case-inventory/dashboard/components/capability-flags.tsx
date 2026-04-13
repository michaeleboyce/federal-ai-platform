/**
 * Four capability flags (enterprise LLM, coding assistants, agentic AI,
 * custom AI) rendered as an editorial row of hairline-ruled entries.
 * Each line: mono ✓/✗/? mark, mono label, small serif description.
 */

import type { AgencyMaturity } from "@/lib/types";

type Flag = {
  label: string;
  description: string;
  value: number | null;
};

function flagFrom(maturity: AgencyMaturity | null): Flag[] {
  return [
    {
      label: "Enterprise LLM access",
      description: "Agency-wide license or platform for general LLM use",
      value: maturity?.has_enterprise_llm ?? null,
    },
    {
      label: "Coding assistants",
      description: "Copilot, Cursor, or similar deployed for developers",
      value: maturity?.has_coding_assistants ?? null,
    },
    {
      label: "Agentic AI",
      description: "Autonomous agents that plan and act on multi-step tasks",
      value: maturity?.has_agentic_ai ?? null,
    },
    {
      label: "Custom AI systems",
      description: "In-house models or agency-built AI applications",
      value: maturity?.has_custom_ai ?? null,
    },
  ];
}

export function CapabilityFlags({
  maturity,
}: {
  maturity: AgencyMaturity | null;
}) {
  const flags = flagFrom(maturity);

  return (
    <ul className="divide-y divide-border border-t border-b border-border">
      {flags.map((f) => {
        const yes = f.value === 1;
        const unknown = f.value == null;
        const mark = yes ? "✓" : unknown ? "?" : "✗";
        const markColor = yes
          ? "text-[var(--verified)]"
          : unknown
            ? "text-muted-foreground"
            : "text-[var(--stamp)]";
        return (
          <li
            key={f.label}
            className="grid grid-cols-[2rem_minmax(0,12rem)_minmax(0,1fr)] items-baseline gap-x-4 py-3"
          >
            <span
              aria-hidden="true"
              className={`font-mono text-[18px] leading-none ${markColor}`}
            >
              {mark}
            </span>
            <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-foreground">
              {f.label}
            </span>
            <span className="font-body text-sm text-muted-foreground">
              {f.description}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
