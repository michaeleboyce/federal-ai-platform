"""Phase 5 — parent-child product hierarchy + research-validated FedRAMP corrections.

This script does TWO things, both idempotent:

1) Set `products.parent_product_id` for known sub-products. Where a parent
   platform doesn't yet exist as an inventory product (e.g. there is no
   "Microsoft 365" platform row for Microsoft 365 Copilot), it is created
   with `product_type='platform'`. New platforms also get a couple of
   product_aliases rows for future name-matching.

2) Apply 7 web-research-validated FedRAMP link corrections (Microsoft 365
   Copilot, Claude, Adobe Firefly, Hyperscience, TRM Labs, GitHub Copilot
   commentary, plus a C3.ai check). Corresponding `fedramp_link_queue`
   rows previously marked `rejected` are flipped to `resolved` with a
   note pointing at the new link.

New product links are written with `confidence='manual'`,
`source='research_w1_w2_w3'`, and a long-form note pulled from the
research summary. `manual_csv` rows are NEVER touched. Re-running the
script is safe — we use INSERT OR IGNORE on the unique
(inventory_product_id, fedramp_id, source) constraint.

Usage:
    python link_parent_products.py            # dry-run
    python link_parent_products.py --apply    # write changes
"""

from __future__ import annotations

import argparse
from typing import Optional

from db import get_connection


# Source label for every link this script writes. Same string is used for the
# uniqueness key so re-running is a no-op.
SOURCE_LABEL = "research_w1_w2_w3"


# ---------------------------------------------------------------------------
# Parent-platform definitions. If `canonical_name` already exists in `products`
# we re-use that row; otherwise we INSERT a new row (and seed a couple of
# aliases so the heuristic matcher in link_fedramp.py can pick it up later).
# ---------------------------------------------------------------------------
PLATFORM_SEEDS = [
    # canonical_name              vendor       product_type     aliases
    ("Microsoft 365",             "Microsoft", "platform",      ["M365", "Microsoft 365 GCC", "Office 365"]),
    ("Microsoft Azure Platform",  "Microsoft", "cloud_platform",["Azure", "Azure Government", "Microsoft Azure"]),
    ("AWS",                       "Amazon",    "cloud_platform",["Amazon Web Services", "AWS GovCloud"]),
    ("Google Cloud Platform",     "Google",    "cloud_platform",["GCP", "Google Cloud"]),
    ("Google Workspace",          "Google",    "platform",      ["Google Workspace", "GSuite"]),
    ("Adobe Creative Cloud Suite","Adobe",     "platform",      ["Adobe Creative Cloud", "Adobe CC"]),
    ("Palantir Federal Cloud Service", "Palantir", "platform",  ["PFCS", "Palantir Federal Cloud"]),
]


# Sub-product → parent platform canonical_name. When parent doesn't exist it
# will be created from PLATFORM_SEEDS.
PARENT_LINKS: list[tuple[str, str]] = [
    # canonical_name               -> parent canonical_name
    ("Microsoft 365 Copilot",        "Microsoft 365"),
    ("Microsoft Copilot for Security","Microsoft 365"),
    ("Microsoft Copilot Studio",     "Microsoft 365"),
    ("Microsoft 365 Apps for Enterprise", "Microsoft 365"),
    ("Microsoft Teams",              "Microsoft 365"),

    ("Azure OpenAI",                 "Microsoft Azure Platform"),
    ("Azure AI Foundry",             "Microsoft Azure Platform"),
    ("Azure AI Document Intelligence","Microsoft Azure Platform"),
    ("Azure AI Vision / Document Intelligence","Microsoft Azure Platform"),
    ("Azure Speech",                 "Microsoft Azure Platform"),

    ("AWS Bedrock",                  "AWS"),
    ("AWS Kendra",                   "AWS"),
    ("AWS Lex",                      "AWS"),
    ("AWS Rekognition",              "AWS"),
    ("AWS Textract",                 "AWS"),
    ("AWS Transcribe",               "AWS"),
    ("Amazon Q",                     "AWS"),
    ("Amazon CodeWhisperer",         "AWS"),

    ("Google Vertex AI",             "Google Cloud Platform"),
    ("Google Cloud Vision",          "Google Cloud Platform"),
    ("Google Translate",             "Google Cloud Platform"),
    ("Google Agentspace",            "Google Cloud Platform"),
    ("Gemini",                       "Google Cloud Platform"),
    ("Google NotebookLM",            "Google Workspace"),
    ("Google Chrome Generative AI",  "Google Workspace"),

    ("Adobe Firefly",                "Adobe Creative Cloud Suite"),
    ("Adobe Photoshop",              "Adobe Creative Cloud Suite"),

    ("Hyperscience",                 "Palantir Federal Cloud Service"),
    ("TRM Labs Blockchain Analysis Platform", "Palantir Federal Cloud Service"),
    ("Palantir AIP",                 "Palantir Federal Cloud Service"),
]


# 7 research-validated FedRAMP corrections.
# Each: (inv_product_canonical, fedramp_id, notes, also_resolve_queue_for_inv_id)
CORRECTIONS: list[dict] = [
    {
        "inv_id": 85,  # Microsoft 365 Copilot
        "links": [
            ("MSO365MT",
             "Covered as feature of parent M365 GCC Moderate boundary; "
             "GCC tenant only — commercial-tenant Copilot is out of scope."),
            ("F1603087869",
             "Also covered via Azure Government High boundary; GCC-High "
             "tenant — commercial Copilot out of scope."),
        ],
        "queue_resolution": "Resolved by W1/W2/W3 research: M365 Copilot is a feature of M365 GCC and Azure Gov High boundaries (GCC tenant only).",
    },
    {
        "inv_id": 94,  # Claude
        "links": [
            ("F1603047866",
             "Claude has no standalone FedRAMP package; Claude 3/3.5/3.7 are "
             "FedRAMP High via AWS Bedrock GovCloud (May 2025). Caveat: "
             "Feb 2026 federal-use directive may affect availability."),
            ("FR2434554673",
             "Claude available FedRAMP High via Palantir FedStart on PFCS "
             "(April 2025)."),
        ],
        "queue_resolution": "Resolved by W1/W2/W3 research: Claude rides AWS Bedrock GovCloud (May 2025) and Palantir FedStart (Apr 2025) — High in both.",
    },
    {
        "inv_id": 118,  # Adobe Firefly
        "links": [
            ("FR1820435960",
             "Firefly is a component of Adobe Creative Cloud for Enterprise "
             "(Li-SaaS authorized)."),
        ],
        "queue_resolution": "Resolved by W1/W2/W3 research: Adobe Firefly is covered as a component of Adobe Creative Cloud for Enterprise (Li-SaaS).",
    },
    {
        "inv_id": 162,  # Hyperscience
        "links": [
            ("FR2434554673",
             "FedRAMP High Authorized via Palantir PFCS-SS named sub-service, "
             "2024-12-17."),
        ],
        "queue_resolution": "Resolved by W1/W2/W3 research: Hyperscience runs as PFCS-SS named sub-service on Palantir Federal Cloud (High, 2024-12-17).",
    },
    {
        "inv_id": 143,  # TRM Labs
        "links": [
            ("FR2434554673",
             "FedRAMP High Authorized via Palantir PFCS-SS named sub-service, "
             "2024-12-17 (was Moderate Sept 2024)."),
        ],
        "queue_resolution": "Resolved by W1/W2/W3 research: TRM Labs runs as PFCS-SS named sub-service on Palantir Federal Cloud (High, 2024-12-17; was Moderate Sept 2024).",
    },
    {
        "inv_id": 88,  # GitHub Copilot — keep existing FR1812058188 link, add cautionary note via NEW row
        "links": [
            ("FR1812058188",
             "CAUTION: Li-SaaS covers GHEC at low impact only; Copilot itself "
             "is NOT in this boundary today. GHEC-DR FedRAMP Moderate in "
             "process (announced Oct 2024). Best-effort link until GHEC-DR "
             "authorization completes."),
        ],
        "queue_resolution": None,  # not currently rejected — already resolved
    },
    # C3.ai (inv 176) handled separately below — we look up dynamically.
]


# Platform-level FedRAMP links. These anchor inheritance. We DO NOT touch
# rows that already exist with source='manual_csv' or 'alias_match'; this
# section simply adds research-sourced rows where the platform was missing
# a link entirely.
PLATFORM_LINKS: list[tuple[str, str, str]] = [
    # platform canonical_name             fedramp_id     notes
    ("Microsoft 365",                     "MSO365MT",
     "M365 GCC Moderate boundary — anchors inheritance for M365 Copilot, "
     "Copilot for Security, Copilot Studio, etc."),
    ("AWS",                               "F1603047866",
     "AWS GovCloud High boundary — anchors inheritance for Bedrock, Kendra, "
     "Lex, Rekognition, Textract, Transcribe, Q, CodeWhisperer."),
    ("Palantir Federal Cloud Service",    "FR2434554673",
     "Palantir Federal Cloud Service - High; current authorization. Sub-products "
     "(PFCS-SS named services like Hyperscience, TRM Labs) inherit via this row."),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_product_by_canonical(conn, name: str) -> Optional[int]:
    row = conn.execute(
        "SELECT id FROM products WHERE canonical_name = ? LIMIT 1",
        (name,),
    ).fetchone()
    return row["id"] if row else None


def _ensure_platform(conn, name: str, vendor: str, product_type: str,
                     aliases: list[str], apply: bool) -> tuple[int, bool]:
    """Return (product_id, created). Idempotent."""
    existing = _find_product_by_canonical(conn, name)
    if existing is not None:
        return existing, False
    if not apply:
        # Dry-run: pretend we'd create, but return -1 sentinel.
        return -1, True
    cur = conn.execute(
        """
        INSERT INTO products (canonical_name, vendor, product_type, description, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, vendor, product_type,
         f"Platform-level inventory row for {name}; created by Phase-5 hierarchy seed.",
         "Created by link_parent_products.py to anchor parent_product_id walk."),
    )
    pid = cur.lastrowid
    for alias in aliases:
        conn.execute(
            "INSERT OR IGNORE INTO product_aliases (product_id, alias_text) VALUES (?, ?)",
            (pid, alias),
        )
    return pid, True


def _set_parent(conn, child_id: int, parent_id: int, apply: bool) -> bool:
    """Set parent_product_id if not already that value. Returns True if changed."""
    row = conn.execute(
        "SELECT parent_product_id FROM products WHERE id = ?", (child_id,)
    ).fetchone()
    if row is None:
        return False
    if row["parent_product_id"] == parent_id:
        return False
    if apply:
        conn.execute(
            "UPDATE products SET parent_product_id = ? WHERE id = ?",
            (parent_id, child_id),
        )
    return True


def _insert_link(conn, inv_id: int, fedramp_id: str, notes: str,
                 apply: bool) -> bool:
    """Insert (inv_id, fedramp_id, source='research_w1_w2_w3') if not present.
    Returns True if a row would be (or was) inserted."""
    existing = conn.execute(
        """SELECT 1 FROM fedramp_product_links
            WHERE inventory_product_id = ?
              AND fedramp_id = ?
              AND source = ?""",
        (inv_id, fedramp_id, SOURCE_LABEL),
    ).fetchone()
    if existing:
        return False
    if apply:
        conn.execute(
            """INSERT OR IGNORE INTO fedramp_product_links (
                  inventory_product_id, fedramp_id, confidence, source, score, notes
               ) VALUES (?, ?, 'manual', ?, NULL, ?)""",
            (inv_id, fedramp_id, SOURCE_LABEL, notes),
        )
    return True


def _resolve_queue_row(conn, inv_id: int, decision_notes: str, apply: bool) -> bool:
    """Flip rejected → resolved for the given inventory_id (link_kind='product').
    Returns True if any row was updated."""
    rows = conn.execute(
        """SELECT id FROM fedramp_link_queue
            WHERE link_kind='product' AND inventory_id = ? AND status='rejected'""",
        (inv_id,),
    ).fetchall()
    if not rows:
        return False
    if apply:
        conn.execute(
            """UPDATE fedramp_link_queue
                  SET status='resolved',
                      decision_notes = COALESCE(decision_notes, '') ||
                          CASE WHEN COALESCE(decision_notes, '')='' THEN '' ELSE ' | ' END || ?,
                      updated_at = datetime('now')
                WHERE link_kind='product' AND inventory_id = ? AND status='rejected'""",
            (decision_notes, inv_id),
        )
    return True


def _check_c3ai(conn) -> str:
    """C3.ai inv id is 176 per Phase-5 brief. Look it up in fedramp_products.
    If present, link with research note. If not, leave a marker note in the
    inventory product so future runs surface the gap."""
    inv_row = conn.execute(
        "SELECT id, canonical_name FROM products WHERE canonical_name = 'C3 AI' LIMIT 1"
    ).fetchone()
    if inv_row is None:
        return "C3.ai not in inventory products — skipping."

    fr_rows = conn.execute(
        "SELECT fedramp_id, csp, cso FROM fedramp_products "
        "WHERE csp LIKE '%C3%' OR cso LIKE '%C3%'"
    ).fetchall()
    if not fr_rows:
        return f"C3.ai (inv id={inv_row['id']}): not in FedRAMP DB snapshot — Dec 11 2025 announcement may not yet be reflected."
    return f"C3.ai (inv id={inv_row['id']}): found {len(fr_rows)} FedRAMP rows: {[r['fedramp_id'] for r in fr_rows]}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(apply: bool) -> None:
    conn = get_connection()
    try:
        # --- 1) Ensure parent platforms exist -----------------------------
        platform_ids: dict[str, int] = {}
        platforms_created: list[str] = []
        for name, vendor, ptype, aliases in PLATFORM_SEEDS:
            pid, created = _ensure_platform(conn, name, vendor, ptype, aliases, apply)
            if pid > 0:
                platform_ids[name] = pid
            if created:
                platforms_created.append(name)

        # --- 2) Set parent_product_id for sub-products --------------------
        parent_changes: list[tuple[str, str]] = []  # (child, parent)
        skipped_no_child: list[str] = []
        for child_name, parent_name in PARENT_LINKS:
            child_id = _find_product_by_canonical(conn, child_name)
            parent_id = platform_ids.get(parent_name) or _find_product_by_canonical(conn, parent_name)
            if child_id is None:
                skipped_no_child.append(child_name)
                continue
            if parent_id is None or parent_id < 0:
                # Parent not yet created (dry-run) — skip but note.
                continue
            if child_id == parent_id:
                continue  # never self-parent
            if _set_parent(conn, child_id, parent_id, apply):
                parent_changes.append((child_name, parent_name))

        # Special: GitHub Copilot (id 88) currently parents under M365 Copilot
        # (id 85). That's wrong — clear it. (No GitHub-Enterprise platform row
        # in inventory; leaving parent NULL is correct.)
        gh = conn.execute(
            "SELECT id, parent_product_id FROM products WHERE id = 88"
        ).fetchone()
        if gh and gh["parent_product_id"] == 85:
            if apply:
                conn.execute(
                    "UPDATE products SET parent_product_id = NULL WHERE id = 88"
                )
            parent_changes.append(("GitHub Copilot", "(cleared bogus M365-Copilot parent)"))

        # --- 3) Apply 7 corrections (FedRAMP link inserts) ----------------
        link_changes: list[str] = []
        queue_resolutions: list[int] = []
        for c in CORRECTIONS:
            inv_id = c["inv_id"]
            for fedramp_id, notes in c["links"]:
                if _insert_link(conn, inv_id, fedramp_id, notes, apply):
                    link_changes.append(f"  inv#{inv_id} -> {fedramp_id}")
            if c.get("queue_resolution") and _resolve_queue_row(
                conn, inv_id, c["queue_resolution"], apply
            ):
                queue_resolutions.append(inv_id)

        # --- 3.5) Platform-level FedRAMP anchor links --------------------
        platform_link_changes: list[str] = []
        for plat_name, fr_id, notes in PLATFORM_LINKS:
            pid = platform_ids.get(plat_name) or _find_product_by_canonical(conn, plat_name)
            if pid is None or pid < 0:
                continue
            if _insert_link(conn, pid, fr_id, notes, apply):
                platform_link_changes.append(f"  inv#{pid} ({plat_name}) -> {fr_id}")

        # --- 4) C3.ai check -----------------------------------------------
        c3_msg = _check_c3ai(conn)

        if apply:
            conn.commit()

        verb = "WROTE" if apply else "WOULD WRITE"
        print(f"\n=== Phase 5 hierarchy + corrections ({'APPLY' if apply else 'DRY-RUN'}) ===")
        print(f"\nPlatforms created: {len(platforms_created)}")
        for n in platforms_created:
            print(f"  + {n}")
        print(f"\nParent links {verb.lower()}: {len(parent_changes)}")
        for child, parent in parent_changes:
            print(f"  {child}  -> {parent}")
        if skipped_no_child:
            print(f"\nSkipped (child not in inventory): {len(skipped_no_child)}")
            for n in skipped_no_child:
                print(f"  - {n}")
        print(f"\nFedRAMP link rows {verb.lower()}: {len(link_changes)}")
        for line in link_changes:
            print(line)
        print(f"\nPlatform-anchor link rows {verb.lower()}: {len(platform_link_changes)}")
        for line in platform_link_changes:
            print(line)
        print(f"\nQueue rows resolved: {len(queue_resolutions)} → {queue_resolutions}")
        print(f"\nC3.ai status: {c3_msg}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Persist changes (default: dry-run)")
    args = parser.parse_args()
    run(apply=args.apply)


if __name__ == "__main__":
    main()
