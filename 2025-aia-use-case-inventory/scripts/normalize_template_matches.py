"""Recover template matches that were lost to cosmetic variation in source data.

Agencies filed the OMB Appendix B templates with minor whitespace / punctuation
drift (dropped periods, stray newlines, "AI powered" vs. "AI-powered"). The
initial template matcher used exact-text equality and left ~4 consolidated rows
unlinked even though they obviously belong to an existing template. This
script:

  1. Inserts two agency-specific extensions as non-OMB-standard templates
     (DOL augmented-reality inspector training, DOL regulatory Q&A).
  2. Re-matches every consolidated_use_cases row against the templates using a
     normalized text key (strip trailing punctuation, collapse whitespace,
     normalize "AI powered" -> "AI-powered").

Idempotent — safe to re-run.
"""

from pathlib import Path
import re
import sqlite3
import sys

DB = Path(__file__).parent.parent / "data" / "federal_ai_inventory_2025.db"


NON_STANDARD_TEMPLATES = [
    (
        "Using AI-enabled augmented reality to train inspectors to visually "
        "assess unsafe environments from a distance.",
        "ar_inspector_training",
        "training",
        "DOL — not part of OMB Appendix B 20-item standard.",
    ),
    (
        "Answering federal regulatory and agency policy questions related to "
        "acquisition using a generative AI tool.",
        "regulatory_qa",
        "knowledge",
        "DOL — not part of OMB Appendix B 20-item standard.",
    ),
]


_WHITESPACE_RE = re.compile(r"\s+")
_TRAILING_PUNCT_RE = re.compile(r"[.,;:\s]+$")


def normalize(s: str) -> str:
    if not s:
        return ""
    s = _WHITESPACE_RE.sub(" ", s).strip()
    s = s.replace("AI powered", "AI-powered")
    s = _TRAILING_PUNCT_RE.sub("", s)
    return s.lower()


def main() -> int:
    if not DB.exists():
        print(f"DB not found: {DB}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))

    # 1. Insert the two non-standard templates (idempotent on short_name).
    inserted = 0
    for text, short, category, notes in NON_STANDARD_TEMPLATES:
        already = conn.execute(
            "SELECT 1 FROM use_case_templates WHERE short_name = ?", (short,)
        ).fetchone()
        if already:
            continue
        conn.execute(
            "INSERT INTO use_case_templates "
            "(template_text, short_name, capability_category, is_omb_standard, notes) "
            "VALUES (?, ?, ?, 0, ?)",
            (text, short, category, notes),
        )
        inserted += 1
    print(f"Inserted {inserted} non-standard templates.")

    # 2. Build normalized lookup from ALL templates.
    templates = {
        normalize(row[1]): row[0]
        for row in conn.execute(
            "SELECT id, template_text FROM use_case_templates"
        ).fetchall()
    }

    # 3. Re-link every consolidated row.
    rows = conn.execute(
        "SELECT id, ai_use_case, template_id FROM consolidated_use_cases"
    ).fetchall()

    relinked_new = 0
    relinked_updated = 0
    cleared = 0
    for rid, text, current_tid in rows:
        new_tid = templates.get(normalize(text))
        if new_tid == current_tid:
            continue
        conn.execute(
            "UPDATE consolidated_use_cases SET template_id = ? WHERE id = ?",
            (new_tid, rid),
        )
        if new_tid is None:
            cleared += 1
        elif current_tid is None:
            relinked_new += 1
        else:
            relinked_updated += 1

    print(
        f"Re-linked {relinked_new} previously unlinked rows; "
        f"updated {relinked_updated} re-classified rows; "
        f"cleared {cleared} dangling links."
    )

    conn.commit()

    # 4. Coverage report.
    coverage = conn.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM consolidated_use_cases WHERE template_id IS NOT NULL),
          (SELECT COUNT(*) FROM consolidated_use_cases WHERE template_id IS NULL),
          (SELECT COUNT(*) FROM consolidated_use_cases)
        """
    ).fetchone()
    linked, unlinked, total = coverage
    print(
        f"\nConsolidated template coverage: {linked}/{total} linked "
        f"({linked * 100 // total}%), {unlinked} unlinked."
    )

    final = conn.execute(
        """
        SELECT t.id, t.short_name, t.is_omb_standard,
               (SELECT COUNT(*) FROM consolidated_use_cases WHERE template_id = t.id) AS n
          FROM use_case_templates t
         ORDER BY t.is_omb_standard DESC, n DESC, t.id
        """
    ).fetchall()
    print("\nTemplate usage (OMB standard first):")
    for tid, short, is_std, n in final:
        marker = "§" if is_std else "*"
        print(f"  {marker} {tid:>2}  {short:<28}  {n}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
