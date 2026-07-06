"""Realign the use_case_templates table with what agencies actually filed.

The initial seed in build_lookups.py included a handful of invented templates
(spelling-grammar, translation, redaction, threat-detection, audio-transcription)
that are NOT in OMB's Appendix B. Meanwhile five templates that ARE in the
filed data were missing (social-media scheduling, travel-route planning,
device-unlock, image editing, storage cataloging), and the security-controls
template_text was truncated relative to OMB's wording, causing agency entries
to never fuzzy-match.

Run this script once to:
  1. Update the security-controls template text.
  2. Delete the five invented templates (all unreferenced by data).
  3. Insert the five real missing templates.
  4. Re-backfill template_id on consolidated_use_cases by exact text match
     (after stripping trailing punctuation + normalizing whitespace).
"""

from pathlib import Path
import sqlite3
import sys

DB = Path(__file__).parent.parent / "data" / "federal_ai_inventory_2025.db"


INVENTED_TO_REMOVE = (
    "spelling_grammar",
    "translation",
    "redaction",
    "threat_detection",
    "audio_transcription",
)

SECURITY_CONTROLS_NEW_TEXT = (
    "Managing or implementing security controls for information systems "
    "(e.g., cybersecurity) using AI."
)

NEW_TEMPLATES = [
    (
        "Scheduling and managing social media posts using AI.",
        "social_media_scheduling",
        "productivity",
    ),
    (
        "Planning travel routes using AI-driven map applications.",
        "travel_routes",
        "travel",
    ),
    (
        "Unlocking smartphones or other devices without the need for passwords "
        "or PINs using AI-based facial recognition.",
        "device_unlock",
        "security",
    ),
    (
        "Editing images, videos, or other public affairs materials using AI.",
        "media_editing",
        "writing",
    ),
    (
        "Identifying and cataloging items in a storage room using AI-driven "
        "image recognition.",
        "storage_cataloging",
        "operations",
    ),
]


def normalize(s: str) -> str:
    return " ".join((s or "").split()).rstrip(".").lower()


def main() -> int:
    if not DB.exists():
        print(f"DB not found: {DB}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. Update security-controls text.
    cur = conn.execute(
        "UPDATE use_case_templates SET template_text = ? WHERE short_name = 'security_controls'",
        (SECURITY_CONTROLS_NEW_TEXT,),
    )
    print(f"Updated security_controls text ({cur.rowcount} row).")

    # 2. Delete the invented templates.
    deleted = 0
    for short in INVENTED_TO_REMOVE:
        ref = conn.execute(
            "SELECT (SELECT COUNT(*) FROM use_cases WHERE template_id = t.id) "
            "+ (SELECT COUNT(*) FROM consolidated_use_cases WHERE template_id = t.id) AS c "
            "FROM use_case_templates t WHERE short_name = ?",
            (short,),
        ).fetchone()
        if ref and ref[0] > 0:
            print(
                f"  Skipping delete of {short}: still referenced by {ref[0]} rows.",
                file=sys.stderr,
            )
            continue
        cur = conn.execute(
            "DELETE FROM use_case_templates WHERE short_name = ?",
            (short,),
        )
        deleted += cur.rowcount
    print(f"Deleted {deleted} invented templates.")

    # 3. Insert the real missing templates (idempotent on short_name).
    inserted = 0
    for text, short, category in NEW_TEMPLATES:
        existing = conn.execute(
            "SELECT 1 FROM use_case_templates WHERE short_name = ?",
            (short,),
        ).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO use_case_templates "
            "(template_text, short_name, capability_category, is_omb_standard) "
            "VALUES (?, ?, ?, 1)",
            (text, short, category),
        )
        inserted += 1
    print(f"Inserted {inserted} new templates.")

    # 4. Re-backfill template_id on consolidated_use_cases by normalized match.
    templates = {
        normalize(row[1]): row[0]
        for row in conn.execute(
            "SELECT id, template_text FROM use_case_templates"
        ).fetchall()
    }

    rows = conn.execute(
        "SELECT id, ai_use_case, template_id FROM consolidated_use_cases"
    ).fetchall()

    relinked = 0
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
        else:
            relinked += 1

    print(f"Re-linked {relinked} consolidated rows; cleared {cleared} dangling links.")

    conn.commit()

    # 5. Report the new distribution.
    final = conn.execute(
        """
        SELECT t.id, t.short_name,
               (SELECT COUNT(*) FROM consolidated_use_cases WHERE template_id = t.id) AS n
          FROM use_case_templates t
         ORDER BY n DESC, t.id
        """
    ).fetchall()
    print("\nTemplate usage now:")
    for tid, short, n in final:
        marker = "." if n > 0 else "!"
        print(f"  {marker} {tid:>2}  {short:<28}  {n}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
