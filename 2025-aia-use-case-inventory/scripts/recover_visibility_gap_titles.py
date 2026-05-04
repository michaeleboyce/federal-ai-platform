"""Backfill vendor_name + system_name on general-LLM rows that left those
fields blank but named the product directly in `use_case_name` (or in
the narrative, where high-confidence).

Why this exists:
  Slice B of the visibility-gap audit (audit/visibility_gap/findings.md)
  identified 431 general-LLM use_cases with no vendor_name or
  system_name in `use_cases`, no cots_vendor or tool_vendor in
  `use_case_tags`. ~25 of those are Family A: the title or narrative
  unambiguously names the product. This script writes those values back
  with high confidence.

Idempotency:
  - Each UPDATE is gated on the existing field still being NULL/blank.
    Running twice is a no-op.
  - On dry-run mode (default), prints what would change but writes nothing.
  - Pass --apply to actually write.

Backup:
  data/federal_ai_inventory_2025.db.backup-pre-visibility-gap
  was taken by the audit before any UPDATEs. Do not skip this.

Note on tagging side-effect:
  This script ALSO mirrors vendor → use_case_tags.cots_vendor where
  blank, so the dashboard's existing fallback logic
  (cots_vendor → tool_vendor → use_cases.vendor_name) picks up the new
  signal without further plumbing.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
BACKUP_PATH = ROOT / "data" / "federal_ai_inventory_2025.db.backup-pre-visibility-gap"

# (use_case_id, vendor_name, system_name, source_note)
# All rows have High or Medium-High confidence per findings.md.
RECOVERIES: list[tuple[int, str, str, str]] = [
    # ---- VA ----
    (60999, "Department of Veterans Affairs", "VA GPT",
        "Title is the platform; M-25-21 plan describes VA GPT as VA's internal GenAI chat tool."),
    (60841, "Department of Veterans Affairs", "VA GPT",
        "Title explicitly references VA GPT integration."),
    (60881, "Abridge", "Abridge Ambient Scribe",
        "Commercial AI scribe; vendor named in title."),
    (60882, "Knowtex", "Knowtex Ambient Scribe",
        "Commercial AI scribe; vendor named in title."),
    (60754, "Andesite AI", "Andesite AI",
        "Title + narrative both name Andesite AI; runs on AWS Bedrock + Anthropic Claude Sonnet per system_outputs."),
    (60965, "Microsoft", "Copilot",
        "Title 'CT CoPilot' is Microsoft Copilot family."),
    (61087, "Microsoft", "Copilot",
        "Title 'VA Chat Copilot Meta Pilot' is Microsoft Copilot family."),
    (60824, "OpenAI", "GPT-4",
        "Narrative explicitly: 'develop an internal HelpBot using an LLM model (GPT 4.0)'."),
    (61050, "Microsoft", "Phi-3.5",
        "Title explicitly names Microsoft Phi-3.5 LLM."),

    # ---- HHS ----
    (59644, "Microsoft", "Azure OpenAI",
        "Title is 'NIGMS Azure Open AI' — explicit."),
    (59630, "Microsoft", "SharePoint Document Assistant (OpenAI)",
        "Title is 'Open AI SharePoint Document Assistant'."),
    (59665, "LibreChat", "LibreChat",
        "Title is 'LibreChat' (open-source chat front-end deployed by NHGRI)."),
    (59402, "Microsoft", "Copilot",
        "Title 'RSL Copilot' is Microsoft Copilot family."),

    # ---- NASA ----
    (59920, "Anthropic", "Claude 3.5",
        "Narrative explicitly: 'utilizing Anthropic Claude 3.5 - based large language model'."),
    (59971, "NASA Goddard", "Giovanni GPT",
        "Internal NASA-built GPT; vendor is the agency."),

    # ---- DOJ ----
    (58652, "TechSmith", "Camtasia",
        "Camtasia is a TechSmith product."),
    (58687, "Skillsoft", "Percipio",
        "Percipio is the Skillsoft learning platform."),
    (58734, "Thomson Reuters", "Drafting Assistant",
        "Title explicitly names Thomson Reuters Drafting Assistant."),
    (58744, "Microsoft", "Copilot",
        "Title 'CoPilot' + narrative 'calendaring, meeting summaries, email drafting' = M365 Copilot."),
    (58766, "Adobe", "Adobe Generative",
        "Title 'Adobe' + narrative re image production = Adobe Firefly / Photoshop generative."),
    (58790, "UiPath", "Document Understanding",
        "Title is the UiPath product."),

    # ---- DOC ----
    (57992, "Microsoft", "Azure OpenAI",
        "Title parenthetical '(Azure)' for LLM support."),
    (57996, "Google", "Vertex AI",
        "Title parenthetical '(Google Vertex)'."),
    (58008, "GSA", "USAi.gov",
        "Narrative explicitly: 'USAI.gov, a government-wide generative AI capability provided by GSA'."),
    (58010, "Microsoft", "Microsoft 365 Copilot",
        "Title 'Implement MS365 Copilot in OS'."),
]


def _is_blank(v: str | None) -> bool:
    if v is None:
        return True
    s = str(v).strip().lower()
    return s in {"", "n/a", "none", "tbd", "na", "null"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Actually write. Default is dry-run.")
    parser.add_argument("--db", default=str(DB_PATH))
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found at {db_path}", file=sys.stderr)
        return 1
    if args.apply and not BACKUP_PATH.exists():
        print(
            f"Refusing to apply: backup {BACKUP_PATH} does not exist. "
            "Take a backup first.",
            file=sys.stderr,
        )
        return 2

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    updates_uc = 0
    updates_tag = 0
    skipped = 0
    missing = 0

    for uc_id, vendor, system_name, note in RECOVERIES:
        row = cur.execute(
            "SELECT id, use_case_name, vendor_name, system_name "
            "FROM use_cases WHERE id = ?",
            (uc_id,),
        ).fetchone()
        if row is None:
            print(f"  [missing] use_case id={uc_id} not found")
            missing += 1
            continue

        actions: list[str] = []

        new_vendor = vendor if _is_blank(row["vendor_name"]) else None
        new_system = system_name if _is_blank(row["system_name"]) else None

        if new_vendor is not None or new_system is not None:
            if args.apply:
                cur.execute(
                    "UPDATE use_cases SET "
                    "vendor_name = COALESCE(?, vendor_name), "
                    "system_name = COALESCE(?, system_name) "
                    "WHERE id = ?",
                    (new_vendor, new_system, uc_id),
                )
            updates_uc += 1
            if new_vendor is not None:
                actions.append(f"vendor_name <- {new_vendor!r}")
            if new_system is not None:
                actions.append(f"system_name <- {new_system!r}")

        # mirror vendor into use_case_tags.cots_vendor + cots_product_name
        # so the dashboard's tag-first fallback also sees it
        tag = cur.execute(
            "SELECT id, cots_vendor, cots_product_name "
            "FROM use_case_tags WHERE use_case_id = ?",
            (uc_id,),
        ).fetchone()
        if tag is not None:
            tag_vendor = vendor if _is_blank(tag["cots_vendor"]) else None
            tag_product = system_name if _is_blank(tag["cots_product_name"]) else None
            if tag_vendor is not None or tag_product is not None:
                if args.apply:
                    cur.execute(
                        "UPDATE use_case_tags SET "
                        "cots_vendor = COALESCE(?, cots_vendor), "
                        "cots_product_name = COALESCE(?, cots_product_name) "
                        "WHERE id = ?",
                        (tag_vendor, tag_product, tag["id"]),
                    )
                updates_tag += 1
                if tag_vendor is not None:
                    actions.append(f"tag.cots_vendor <- {tag_vendor!r}")
                if tag_product is not None:
                    actions.append(f"tag.cots_product_name <- {tag_product!r}")

        if not actions:
            skipped += 1
            print(f"  [no-op] {uc_id} ({row['use_case_name']}) — already populated")
        else:
            verb = "APPLY" if args.apply else "DRY"
            print(f"  [{verb}] {uc_id} ({row['use_case_name']}): " + "; ".join(actions))
            print(f"           rationale: {note}")

    if args.apply:
        con.commit()
    con.close()

    print()
    print(f"Summary: use_cases updates={updates_uc}, tag updates={updates_tag}, "
          f"already-populated skips={skipped}, missing rows={missing}")
    if not args.apply:
        print("Dry run. Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
