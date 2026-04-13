import { formatDatelineDate } from "@/lib/formatting";

type Props = {
  lastUpdated: string | null;
};

export function Dateline({ lastUpdated }: Props) {
  const filed = formatDatelineDate(lastUpdated);
  return (
    <div className="w-full border-b border-border bg-background/80 backdrop-blur-[2px]">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground md:px-8">
        <div className="flex items-center gap-3 overflow-hidden">
          <span className="text-foreground">VOL. I</span>
          <span aria-hidden className="hidden text-muted-foreground/60 sm:inline">
            §
          </span>
          <span className="hidden sm:inline">Federal AI Inventory</span>
          <span aria-hidden className="text-muted-foreground/60">/</span>
          <span className="hidden md:inline">Reporting Cycle 2025</span>
          <span aria-hidden className="hidden text-muted-foreground/60 md:inline">
            /
          </span>
          <span className="truncate">OMB M-25-21</span>
        </div>
        <div className="flex items-center gap-3 whitespace-nowrap">
          <span className="hidden sm:inline">Filed</span>
          <span className="text-foreground">{filed}</span>
          <span
            aria-hidden
            className="hidden h-1.5 w-1.5 rounded-full bg-[var(--stamp)] md:inline-block"
          />
        </div>
      </div>
    </div>
  );
}
