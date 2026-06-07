"""Apply verified 2024 IFP tag corrections to use_case_tags_2024.

A verification pass over use_case_tags_2024_canonical found a set of
impossible-invariant violations and individual auditor findings. This
script fixes them in place, across ALL waves of each use case.

SAFETY (per CLAUDE.md): never trust a stale id. Every use_case_id_2024 is
re-resolved by (agency_abbreviation, use_case_name) on the live connection
immediately before each UPDATE. Idempotent: rows already at the target
value are logged as SKIP and left untouched.

Default: dry-run. Pass --apply to write.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"

# Buckets that cannot coexist with is_generative_ai (mirrors the invariant
# checker's rule 1). When we flip genai=1 on a row that still carries one of
# these, we'd manufacture a new impossible violation — so we bump the
# sophistication to 'general_llm' (same remediation as A9 / QBIQ).
NON_GENAI_SOPHISTICATIONS = frozenset(
    {"classical_ml", "computer_vision", "predictive_analytics"}
)


def resolve_ids(
    conn: sqlite3.Connection,
    agency: str,
    name_like: str,
    extra_like: str | None = None,
) -> list[tuple[int, str]]:
    """Re-resolve current use_case_id_2024 values by stable signature.

    Returns [(id, use_case_name)]. extra_like is OR-ed against use_case_name
    so a single finding spanning two name patterns resolves in one call.
    """
    sql = (
        "SELECT id, use_case_name FROM use_cases_2024 "
        "WHERE agency_abbreviation = ? AND (use_case_name LIKE ?"
    )
    params: list[object] = [agency, name_like]
    if extra_like is not None:
        sql += " OR use_case_name LIKE ?"
        params.append(extra_like)
    sql += ") ORDER BY id"
    return [(r[0], r[1]) for r in conn.execute(sql, params).fetchall()]


def update_field(
    conn: sqlite3.Connection,
    label: str,
    use_case_id: int,
    use_case_name: str,
    field: str,
    target: int | str,
    apply: bool,
) -> None:
    """Set `field` = target across ALL waves of one use case, idempotently."""
    cur = conn.cursor()
    rows = cur.execute(
        f"SELECT id, wave, {field} FROM use_case_tags_2024 "
        "WHERE use_case_id_2024 = ? ORDER BY wave",
        (use_case_id,),
    ).fetchall()
    if not rows:
        print(f"  [{label}] uc={use_case_id} '{use_case_name}': NO TAG ROWS")
        return
    to_change = [(tid, wave, cur_val) for tid, wave, cur_val in rows if cur_val != target]
    if not to_change:
        print(
            f"  [{label}] uc={use_case_id} '{use_case_name}': "
            f"SKIP (already correct, {field}={target}, {len(rows)} wave(s))"
        )
        return
    waves = ", ".join(f"{w}({cv}->{target})" for _, w, cv in to_change)
    print(
        f"  [{label}] uc={use_case_id} '{use_case_name}': "
        f"SET {field}={target} on {len(to_change)}/{len(rows)} wave row(s): {waves}"
    )
    if apply:
        for tid, _, _ in to_change:
            cur.execute(
                f"UPDATE use_case_tags_2024 SET {field} = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (target, tid),
            )


def set_generative(
    conn: sqlite3.Connection,
    label: str,
    use_case_id: int,
    use_case_name: str,
    apply: bool,
) -> None:
    """Set is_generative_ai=1 AND repair any non-generative sophistication.

    Flipping genai=1 on a row whose ai_sophistication is classical_ml /
    computer_vision / predictive_analytics would create a fresh rule-1
    impossible violation. For those rows we also bump sophistication to
    'general_llm' (same remediation pattern as A9)."""
    update_field(conn, label, use_case_id, use_case_name, "is_generative_ai", 1, apply)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, wave, ai_sophistication FROM use_case_tags_2024 "
        "WHERE use_case_id_2024 = ? ORDER BY wave",
        (use_case_id,),
    ).fetchall()
    stale = [
        (tid, wave, soph)
        for tid, wave, soph in rows
        if soph in NON_GENAI_SOPHISTICATIONS
    ]
    if not stale:
        return
    waves = ", ".join(f"{w}({s}->general_llm)" for _, w, s in stale)
    print(
        f"  [{label}] uc={use_case_id} '{use_case_name}': "
        f"+ bump ai_sophistication on {len(stale)} wave row(s): {waves}"
    )
    if apply:
        for tid, _, _ in stale:
            cur.execute(
                "UPDATE use_case_tags_2024 SET ai_sophistication = 'general_llm', "
                "updated_at = datetime('now') WHERE id = ?",
                (tid,),
            )


def group_a_llm_access(conn: sqlite3.Connection, apply: bool) -> None:
    """A1-A8: is_general_llm_access=1 implies generative AI."""
    print("== GROUP A: impossible-invariant fixes ==")
    # Match any llm_access=1 use case that still needs work: genai not yet
    # set, OR genai set but the sophistication bucket is still a
    # non-generative one. The second clause keeps the sophistication bump
    # reachable on idempotent re-runs (once genai is flipped, the first
    # clause alone would no longer select the row).
    soph_list = ", ".join(f"'{s}'" for s in sorted(NON_GENAI_SOPHISTICATIONS))
    rows = conn.execute(
        f"""
        SELECT DISTINCT u.id, u.agency_abbreviation, u.use_case_name
        FROM use_case_tags_2024 t
        JOIN use_cases_2024 u ON u.id = t.use_case_id_2024
        WHERE t.is_general_llm_access = 1
          AND (
                (t.is_generative_ai IS NULL OR t.is_generative_ai = 0)
             OR t.ai_sophistication IN ({soph_list})
          )
        ORDER BY u.id
        """
    ).fetchall()
    print(f"  A1-A8: {len(rows)} use case(s) needing genai/sophistication repair")
    for uc_id, agency, name in rows:
        # re-resolve by signature immediately before write
        resolved = resolve_ids(conn, agency, name)
        match = next((rid for rid, _ in resolved if rid == uc_id), None)
        if match is None:
            print(f"  [A1-A8] uc={uc_id} '{name}': COULD NOT RE-RESOLVE, skipping")
            continue
        set_generative(conn, "A1-A8", match, name, apply)


def group_a9(conn: sqlite3.Connection, apply: bool) -> None:
    """A9: GSA 'Test Fit Layouts' — genai=1 + ai_sophistication='computer_vision'.

    Narrative (QBIQ pilot): "rapidly test-fit spaces ... utilize
    visualizations"; outputs are "Floor plan and 3D conceptual layouts".
    This is AI-generated layout design, not traditional CV recognition —
    so the generative flag is correct and the sophistication bucket is
    wrong. Set ai_sophistication='general_llm'.
    """
    for uc_id, name in resolve_ids(conn, "GSA", "%Test Fit%"):
        update_field(conn, "A9", uc_id, name, "ai_sophistication", "general_llm", apply)


def group_a10(conn: sqlite3.Connection, apply: bool) -> None:
    """A10: USAGM 'Microsoft Copilot for Internal Employees' —
    is_enterprise_wide=1 but deployment_scope='bureau'."""
    for uc_id, name in resolve_ids(conn, "USAGM", "%Copilot%"):
        update_field(conn, "A10", uc_id, name, "deployment_scope", "enterprise_wide", apply)


def group_b(conn: sqlite3.Connection, apply: bool) -> None:
    print("== GROUP B: Phase B auditor findings ==")
    # B1: DOL Microsoft Office Suite — not Copilot
    for uc_id, name in resolve_ids(conn, "DOL", "%Office Suite%"):
        update_field(conn, "B1", uc_id, name, "is_microsoft_copilot", 0, apply)
    # B2: VA FAQ Dashboard — is generative
    for uc_id, name in resolve_ids(conn, "VA", "%FAQ%"):
        set_generative(conn, "B2", uc_id, name, apply)
    # B3: VA Speech/Sentiment — not generative
    for uc_id, name in resolve_ids(conn, "VA", "%Speech%", "%Sentiment%"):
        update_field(conn, "B3", uc_id, name, "is_generative_ai", 0, apply)
    # B4: VA Adobe Creative Cloud — is generative
    for uc_id, name in resolve_ids(conn, "VA", "%Adobe%"):
        set_generative(conn, "B4", uc_id, name, apply)
    # B5: VA Transcription Services — not generative
    for uc_id, name in resolve_ids(conn, "VA", "%Transcription%"):
        update_field(conn, "B5", uc_id, name, "is_generative_ai", 0, apply)
    # B6: DOJ DEA Crypto — not generative
    for uc_id, name in resolve_ids(conn, "DOJ", "%Crypto%"):
        update_field(conn, "B6", uc_id, name, "is_generative_ai", 0, apply)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes. Default: dry-run.")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] 2024 tag corrections")
    print(f"  DB: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        group_a_llm_access(conn, args.apply)
        group_a9(conn, args.apply)
        group_a10(conn, args.apply)
        group_b(conn, args.apply)
        if args.apply:
            conn.commit()
    finally:
        conn.close()

    print()
    print(f"[{mode}] done. " +
          ("Changes written." if args.apply else "No changes written; re-run with --apply."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
