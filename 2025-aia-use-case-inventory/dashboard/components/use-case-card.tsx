/**
 * A single Use Case card, used by the grid view and the "related use cases"
 * list on the detail page. Server-renderable (no client state).
 *
 * Editorial: no shadcn Card, no shadow, no rounded corners. Each card is
 * a cell in a hairline-ruled grid — borders on the right + bottom create
 * the grid without needing outer dividers. The use-case name reads as a
 * display italic; the agency code is a MonoChip.
 */

import Link from "next/link";
import type { UseCaseWithTags } from "@/lib/types";
import { MonoChip } from "@/components/editorial";
import { truncate } from "@/lib/formatting";
import { Code2, Sparkles, ShieldCheck } from "lucide-react";

export function UseCaseCard({
  useCase,
  compact = false,
}: {
  useCase: UseCaseWithTags;
  compact?: boolean;
}) {
  const tags = useCase.tags;
  const href = useCase.slug ? `/use-cases/${useCase.slug}` : "#";

  return (
    <article className="group flex h-full flex-col gap-3 border-b border-r border-border p-4 transition-colors hover:bg-[color-mix(in_oklab,var(--highlight)_12%,transparent)]">
      <div className="flex items-start justify-between gap-2">
        {useCase.agency_abbreviation && (
          <MonoChip
            href={`/agencies/${useCase.agency_abbreviation}`}
            tone="stamp"
            size="xs"
          >
            {useCase.agency_abbreviation}
          </MonoChip>
        )}
        <div className="flex items-center gap-1">
          {tags?.is_coding_tool === 1 && (
            <Code2
              className="size-3.5 text-[var(--stamp)]"
              aria-label="Coding tool"
            />
          )}
          {tags?.is_general_llm_access === 1 && (
            <Sparkles
              className="size-3.5 text-[var(--verified)]"
              aria-label="General LLM access"
            />
          )}
          {tags?.has_ato_or_fedramp === 1 && (
            <ShieldCheck
              className="size-3.5 text-[var(--verified)]"
              aria-label="Has ATO / FedRAMP"
            />
          )}
        </div>
      </div>

      <Link href={href} className="group/name">
        <h3 className="font-display italic text-[1.15rem] leading-[1.15] tracking-[-0.01em] text-foreground group-hover/name:text-[var(--stamp)] line-clamp-3">
          {useCase.use_case_name}
        </h3>
      </Link>

      {!compact && useCase.problem_statement && (
        <p className="line-clamp-3 text-[12.5px] leading-snug text-muted-foreground">
          {truncate(useCase.problem_statement, 200)}
        </p>
      )}

      <div className="mt-auto flex flex-wrap gap-1.5 border-t border-dotted border-border pt-2 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
        {tags?.entry_type && (
          <span>{tags.entry_type.replace(/_/g, " ")}</span>
        )}
        {tags?.entry_type && tags?.ai_sophistication && <span>·</span>}
        {tags?.ai_sophistication && (
          <span>{tags.ai_sophistication.replace(/_/g, " ")}</span>
        )}
        {(tags?.entry_type || tags?.ai_sophistication) &&
          tags?.deployment_scope && <span>·</span>}
        {tags?.deployment_scope && (
          <span>{tags.deployment_scope.replace(/_/g, " ")}</span>
        )}
        {useCase.vendor_name && (
          <span className="ml-auto max-w-[60%] truncate text-foreground">
            {truncate(useCase.vendor_name, 30)}
          </span>
        )}
      </div>
    </article>
  );
}
