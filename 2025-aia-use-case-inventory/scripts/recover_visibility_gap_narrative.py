"""Backfill vendor_name + system_name on general-LLM rows whose narrative
(problem_statement / expected_benefits / system_outputs) explicitly cites a
model or platform but whose form fields stayed blank.

Why this exists:
  Family-B follow-up to the visibility-gap audit
  (audit/visibility_gap/findings.md). Slice B handled the title-only
  recoveries (recover_visibility_gap_titles.py). This pass scans the
  narrative fields of the remaining 446 "Vendor unspecified" general-LLM
  rows and writes back the vendor/product where the narrative explicitly
  attributes one. Conservative: only HIGH or MEDIUM-HIGH confidence rows.

Idempotency:
  - Each UPDATE is gated on the existing field still being NULL/blank.
    Running twice is a no-op.
  - On dry-run mode (default), prints what would change but writes nothing.
  - Pass --apply to actually write.

Backup:
  data/federal_ai_inventory_2025.db.backup-pre-narrative-extract
  was taken by the audit before any UPDATEs. Do not skip this.

Note on tagging side-effect:
  This script ALSO mirrors vendor + product into use_case_tags.cots_vendor
  + cots_product_name where blank, so the dashboard's existing fallback
  logic (cots_vendor -> tool_vendor -> use_cases.vendor_name) picks up the
  new signal without further plumbing.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
BACKUP_PATH = ROOT / "data" / "federal_ai_inventory_2025.db.backup-pre-narrative-extract"

# (use_case_id, vendor_name, system_name, source_note)
# All HIGH or MEDIUM-HIGH confidence per narrative reads. Rationale comments
# below cite the explicit narrative quote that justifies attribution.
RECOVERIES: list[tuple[int, str, str, str]] = [
    # ---- DHS ----
    (57602, "Google", "Vertex AI",
        "HIGH: problem_statement explicitly: 'Using Vertex AI and other GCP "
        "services, the system identifies and categorizes content...'"),
    (57614, "Microsoft", "Azure OpenAI",
        "HIGH: system_outputs explicitly: 'The AI system, powered by Azure "
        "OpenAI Services, generates outputs...' (FEMA Grants Manager "
        "ChatBot)."),

    # ---- DOT ----
    (58999, "Microsoft", "Copilot",
        "MEDIUM-HIGH: title 'RMM Analyzer Copilot' + narrative repeatedly "
        "calls it a 'Copilot' for technical operations. Same pattern as "
        "Slice B 60965/61087 attributions."),
    (59011, "Microsoft", "Copilot",
        "MEDIUM-HIGH: title 'Case and Document Management Copilot'; "
        "narrative cites 'library of actions, pre-programmed capabilities' "
        "= Microsoft Copilot Studio terminology."),

    # ---- HHS ----
    (59690, "Microsoft", "Azure OpenAI",
        "HIGH: expected_benefits explicitly: 'automates the process of "
        "analyzing text...using a custom prompt and an Azure OpenAI models'."),

    # ---- NASA ----
    (60148, "LibreChat", "LibreChat",
        "HIGH: problem_statement + expected_benefits explicitly: 'NASA IV&V "
        "AI Assistant powered by LibreChat with Retrieval-Augmented "
        "Generation'."),

    # ---- TVA ----
    (60427, "Microsoft", "Copilot",
        "MEDIUM-HIGH: title 'Copilot' + bare 'Increased efficiency and "
        "productivity' benefit framing matches TVA's known M365 Copilot "
        "enterprise rollout. Same pattern as Slice B's bare-Copilot "
        "attributions."),
]


def _is_blank(v: str | None) -> bool:
    if v is None:
        return True
    s = str(v).strip().lower()
    return s in {"", "n/a", "not available", "none", "tbd", "na", "null", "unknown"}


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
