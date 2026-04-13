# Editorial Style Guide — "OMB Memorandum"

All pages share a single aesthetic: **warm paper cream + deep editorial ink + vermilion stamp accents + JetBrains Mono data + Instrument Serif italic display**. Think *declassified government memo × NYT long-form × Bloomberg Terminal data density*.

## Fonts (already loaded in `app/layout.tsx`)
- **Instrument Serif** (`font-display`) — italic display headlines, h1/h2/h3, big numbers
- **Fraunces** (`font-body`) — body prose
- **JetBrains Mono** (`font-mono`) — all numbers, codes, labels, kickers, captions, serial numbers

## Color tokens (in `globals.css`)
- `var(--paper)` — background, warm cream
- `var(--ink)` — foreground, near-black
- `var(--stamp)` — vermilion red (§ kickers, highlights, hover)
- `var(--verified)` — forest green (positive, "leading" tier)
- `var(--highlight)` — yellow highlighter (marginalia, emphasis)
- `var(--rule)` — hairline rule color

## Do
- Use `<Section number="I" title="Title" lede="Lede">` from `@/components/editorial` for every major page section
- Use `<Figure eyebrow="Fig. 1 · Name" caption="...">` for every chart or data figure
- Use `<MonoChip href="..." tone="stamp|ink|verified|muted">CODE</MonoChip>` for agency abbreviations and tags
- Use `<Eyebrow color="stamp">§ LABEL</Eyebrow>` above sub-sections
- Apply `italic` class to h1/h2/h3 for display emphasis
- Use monospace `font-mono text-[10px] uppercase tracking-[0.18em]` for eyebrows, captions, serial numbers, filing metadata
- Use `tabular-nums` on all numerical content
- Use 2px `border-t-2 border-foreground` for figure top-rules; 1px `border-b border-dotted border-border` for inline separators
- Use `{" · "}` for mid-line dividers in monospace strings

## Don't
- Don't wrap sections in shadcn Card with rounded corners (radius is 0 now anyway)
- Don't use `style={{ fontStyle: "italic" }}` — use the `italic` class
- Don't use blue/violet gradient heroes or purple→pink shadcn defaults
- Don't use sans-serif for display headings
- Don't use rounded corners anywhere (`radius-*: 0`)
- Don't color-code with a rainbow; stick to the 4-color palette (ink, stamp, verified, highlight)

## Primitives available from `@/components/editorial`
- `Section({ number, title, lede, children, className })`
- `Figure({ eyebrow, caption, children, className })`
- `Eyebrow({ children, color })`
- `MonoChip({ children, href, title, tone, size })`
- `ENTRY_TYPE_COLORS` / `ENTRY_TYPE_LABELS`
- `SOPHISTICATION_COLORS` / `SOPHISTICATION_LABELS`
- `SCOPE_COLORS` / `SCOPE_LABELS`
- `TIER_ACCENTS`

## Shared utils in `@/lib/formatting`
- `humanize(snake_case)` → "Title Case"
- `formatNumber(n)` → "1,234"
- `formatPercent(v)`, `formatYoY(v)`, `formatDate(iso)`, `formatDatelineDate(iso)`

## Page layout
```tsx
<div className="mx-auto w-full max-w-[1400px] px-4 py-10 md:px-8 md:py-14">
  <header className="ink-in grid grid-cols-12 gap-x-6 border-b border-border pb-12">
    {/* left rail (col 3): eyebrow + meta + stamp; sticky on md+ */}
    {/* headline col (col 9): big italic display h1 + lead paragraph */}
  </header>

  <Section number="I" title="…">…</Section>
  <Section number="II" title="…">…</Section>
  …
</div>
```

## Chart conventions
- Charts live inside `<Figure>` components
- Donuts + bars use `colorMap` + `labelMap` from the shared color/label maps
- No chart wrapper backgrounds; rely on the Figure's 2px top-rule
- Captions in `font-mono text-[11px] text-muted-foreground`
