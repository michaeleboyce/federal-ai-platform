/**
 * Template grid card — editorial.
 *
 * A hairline-ruled block with a thick foreground top-rule. The template text
 * is pulled out at display size in italic (the "quote" of the compendium);
 * an optional small-caps short_name sits above as eyebrow; capability
 * category appears as a stamp-colored mono kicker; bottom row carries
 * usage counters.
 */

import Link from "next/link";
import { formatNumber, humanize } from "@/lib/formatting";
import type { TemplateWithCounts } from "@/lib/types";

type Props = {
  template: TemplateWithCounts;
};

export function TemplateCard({ template }: Props) {
  return (
    <Link
      href={`/templates/${template.id}`}
      className="group flex h-full flex-col border-t-2 border-foreground bg-transparent pt-4 transition-colors hover:border-[var(--stamp)]"
    >
      <div className="flex items-baseline justify-between gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          {template.short_name ? (
            <span className="text-foreground">{template.short_name}</span>
          ) : (
            <span>Template № {String(template.id).padStart(3, "0")}</span>
          )}
        </div>
        {template.is_omb_standard === 1 ? (
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--stamp)]">
            OMB std.
          </span>
        ) : null}
      </div>

      <blockquote className="mt-2 font-display italic text-[1.2rem] leading-[1.2] tracking-[-0.005em] text-foreground group-hover:text-[var(--stamp)]">
        &ldquo;{template.template_text}&rdquo;
      </blockquote>

      {template.capability_category ? (
        <div className="mt-3 font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--stamp)]">
          § {humanize(template.capability_category)}
        </div>
      ) : null}

      <div className="mt-auto grid grid-cols-2 gap-x-4 border-t border-dotted border-border pt-3 font-mono text-[11px] uppercase tracking-[0.12em]">
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-muted-foreground">Agencies</span>
          <span className="tabular-nums text-foreground">
            {formatNumber(template.agency_count)}
          </span>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-muted-foreground">Entries</span>
          <span className="tabular-nums text-foreground">
            {formatNumber(template.use_case_count)}
          </span>
        </div>
      </div>
    </Link>
  );
}
