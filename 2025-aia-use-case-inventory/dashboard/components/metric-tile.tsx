import { formatNumber } from "@/lib/formatting";

type Accent = "default" | "stamp" | "verified" | "ink" | "highlight";

const ACCENT_CLASSES: Record<Accent, string> = {
  default: "text-foreground",
  stamp: "text-[var(--stamp)]",
  verified: "text-[var(--verified)]",
  ink: "text-foreground",
  highlight: "text-foreground bg-[var(--highlight)]/50",
};

export function MetricTile({
  label,
  value,
  sublabel,
  accent = "default",
}: {
  label: string;
  value: number | string;
  sublabel?: string;
  accent?: Accent;
}) {
  const display =
    typeof value === "number" ? formatNumber(value) : value || "—";

  return (
    <div className="group flex min-w-0 flex-col gap-1 border-t-2 border-foreground pt-2">
      <div className="eyebrow truncate">{label}</div>
      <div
        className={`font-display text-[2.2rem] leading-[0.95] tracking-[-0.02em] italic ${ACCENT_CLASSES[accent]}`}
      >
        <span className="tabular-nums">{display}</span>
      </div>
      {sublabel ? (
        <div className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-muted-foreground">
          {sublabel}
        </div>
      ) : null}
    </div>
  );
}
