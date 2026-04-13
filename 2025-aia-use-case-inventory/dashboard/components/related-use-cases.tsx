/**
 * Compact list of related use cases — editorial edition.
 * Data is fetched server-side in the page; this component just renders.
 */

import Link from "next/link";
import { MonoChip } from "@/components/editorial";

export interface RelatedItem {
  id: number;
  slug: string | null;
  use_case_name: string;
  agency_abbreviation: string;
}

export function RelatedUseCases({
  title,
  items,
  emptyMessage,
}: {
  title: string;
  items: RelatedItem[];
  emptyMessage: string;
}) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="border-b border-border pb-1 font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-foreground">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          {emptyMessage}
        </p>
      ) : (
        <ul className="flex flex-col">
          {items.map((item) => (
            <li
              key={item.id}
              className="border-b border-dotted border-border last:border-b-0"
            >
              <Link
                href={item.slug ? `/use-cases/${item.slug}` : "#"}
                className="flex items-start gap-2 py-2 transition-colors hover:bg-[color-mix(in_oklab,var(--highlight)_12%,transparent)]"
              >
                <MonoChip tone="muted" size="xs">
                  {item.agency_abbreviation}
                </MonoChip>
                <span className="line-clamp-2 text-[13px] leading-snug text-foreground">
                  {item.use_case_name}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
