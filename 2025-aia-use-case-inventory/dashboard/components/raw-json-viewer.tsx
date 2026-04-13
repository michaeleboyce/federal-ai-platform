"use client";

/**
 * Collapsible pretty-printer for the `raw_json` column we carry through on
 * every use case. No external syntax-highlighting lib needed — we do a
 * tiny regex-based colorizer.
 *
 * Editorial shell: the `<summary>` trigger is styled as a mono-uppercase
 * section header (no rounded corners, hairline rules). The JSON body
 * keeps its monospace nature — that's the whole point of the viewer — but
 * sits on a flat paper background rather than a pill container.
 *
 * XSS safety: `highlight()` HTML-escapes the entire input *first* (&, <, >
 * replaced) and then only wraps pre-escaped token matches in static
 * <span> tags. No user-controlled bytes ever reach the DOM as raw HTML.
 * The tokenizer's regex only matches JSON-literal shapes, so the matched
 * substrings cannot contain `<` / `>` / `&` after escaping. This is a
 * safe use of `dangerouslySetInnerHTML`.
 */

import { useMemo, useState } from "react";
import { Copy, Check } from "lucide-react";

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function highlight(json: string): string {
  const esc = escapeHtml(json); // trust boundary: escape BEFORE tokenizing
  return esc.replace(
    /("(?:\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = "text-[var(--verified)]"; // number
      if (match.startsWith("&quot;") || match.startsWith('"')) {
        cls = /:\s*$/.test(match)
          ? "text-foreground font-semibold" // key
          : "text-[var(--stamp)]"; // string
      } else if (match === "true" || match === "false") {
        cls = "text-[var(--verified)]";
      } else if (match === "null") {
        cls = "text-muted-foreground";
      }
      return `<span class="${cls}">${match}</span>`;
    },
  );
}

export function RawJsonViewer({ json }: { json: string | null | undefined }) {
  const [copied, setCopied] = useState(false);
  const parsed = useMemo(() => {
    if (!json) return null;
    try {
      return JSON.parse(json);
    } catch {
      return json;
    }
  }, [json]);

  if (!json || !parsed) return null;

  const pretty =
    typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(pretty);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // no-op: clipboard may be unavailable
    }
  };

  return (
    <details className="group border-t-2 border-foreground">
      <summary className="flex cursor-pointer items-center justify-between gap-2 py-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground transition-colors hover:text-foreground">
        <span className="text-foreground">§ Raw JSON</span>
        <span className="group-open:hidden">[ expand ]</span>
        <span className="hidden group-open:inline">[ collapse ]</span>
      </summary>
      <div className="relative border-t border-border">
        <button
          type="button"
          onClick={onCopy}
          className="absolute right-3 top-3 inline-flex items-center gap-1 border border-border bg-background px-2 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-[var(--stamp)] hover:text-[var(--stamp)]"
          aria-label="Copy JSON"
        >
          {copied ? (
            <>
              <Check className="size-3" aria-hidden /> Copied
            </>
          ) : (
            <>
              <Copy className="size-3" aria-hidden /> Copy
            </>
          )}
        </button>
        <pre className="overflow-x-auto px-0 py-4 text-[11.5px] leading-relaxed">
          <code
            className="font-mono"
            // eslint-disable-next-line react/no-danger -- see file-level safety note
            dangerouslySetInnerHTML={{ __html: highlight(pretty) }}
          />
        </pre>
      </div>
    </details>
  );
}
