"""Backfill use_cases.use_case_id from raw_json and stamp id_provenance.

Behavior:
  * For every row with use_case_id IS NULL or '':
      - Parse raw_json. Try a known set of header variants, plus any key whose
        normalized form maps to 'use_case_id' via column_maps.
      - If a value is found AND (agency_id, value) is unique across use_cases,
        set use_case_id and id_provenance='backfilled_from_raw_json'.
      - If a (agency_id, value) collision is detected, log it, leave
        use_case_id NULL, set id_provenance='source_missing'.
      - If no value is found, set id_provenance='source_missing'.
  * For rows with non-empty use_case_id, set id_provenance='source'.

Exits non-zero if any row ends with use_case_id IS NULL AND id_provenance IS NULL.

Idempotent: re-running re-stamps provenance and re-attempts backfill.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Allow running as `python scripts/backfill_use_case_id.py` from project root.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from column_maps import map_header_to_canonical  # noqa: E402
from db import apply_migrations, get_connection  # noqa: E402

# Highest-confidence key variants, tried in order before falling back to
# normalized-key search. Listing them explicitly keeps the common path fast and
# gives us a deterministic preference order when a row carries multiple variants.
KNOWN_KEYS = (
    "Use Case ID\n\n[Agency Abbrev.] - [#]",
    "Use Case ID",
    "Use Case Identifier",
    "ID",
)


def _extract_id_from_raw(raw: str | None) -> str | None:
    """Return the use_case_id value from a raw_json blob, or None if not found."""
    if not raw:
        return None
    try:
        rj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(rj, dict):
        return None

    # 1. Fast path: try the known keys verbatim.
    for k in KNOWN_KEYS:
        v = rj.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()

    # 2. Fallback: any key whose normalized form maps to use_case_id.
    for k, v in rj.items():
        if v is None or not str(v).strip():
            continue
        if map_header_to_canonical(k) == "use_case_id":
            return str(v).strip()

    return None


def main() -> int:
    apply_migrations()
    conn = get_connection()
    try:
        # Before counts.
        before = {
            "null_or_empty": conn.execute(
                "SELECT COUNT(*) FROM use_cases WHERE use_case_id IS NULL OR use_case_id = ''"
            ).fetchone()[0],
            "populated": conn.execute(
                "SELECT COUNT(*) FROM use_cases WHERE use_case_id IS NOT NULL AND use_case_id != ''"
            ).fetchone()[0],
            "total": conn.execute("SELECT COUNT(*) FROM use_cases").fetchone()[0],
        }
        print(f"BEFORE: {before}")

        # First pass: mark already-populated rows as 'source'.
        conn.execute(
            "UPDATE use_cases SET id_provenance='source' "
            "WHERE use_case_id IS NOT NULL AND use_case_id != ''"
        )
        conn.commit()

        # If the source file itself repeats an ID within an agency, keep the
        # first row and mark the later rows unresolved so the DB does not
        # expose duplicate "source" IDs as if they were reliable identifiers.
        duplicate_source_collisions = 0
        source_groups: dict[tuple[int, str], list[int]] = defaultdict(list)
        for r in conn.execute(
            "SELECT id, agency_id, use_case_id FROM use_cases "
            "WHERE use_case_id IS NOT NULL AND use_case_id != '' "
            "ORDER BY agency_id, use_case_id, id"
        ):
            source_groups[(r["agency_id"], r["use_case_id"])].append(r["id"])
        for ids in source_groups.values():
            for row_id in ids[1:]:
                conn.execute(
                    """
                    UPDATE use_cases
                       SET use_case_id = NULL,
                           id_provenance = 'source_missing'
                     WHERE id = ?
                    """,
                    (row_id,),
                )
                duplicate_source_collisions += 1
        conn.commit()

        # Build the existing (agency_id, use_case_id) set so we can guard
        # collisions while we backfill.
        taken: set[tuple[int, str]] = set()
        for r in conn.execute(
            "SELECT agency_id, use_case_id FROM use_cases "
            "WHERE use_case_id IS NOT NULL AND use_case_id != ''"
        ):
            taken.add((r["agency_id"], r["use_case_id"]))

        # Pre-extract candidates per row so we can detect collisions BETWEEN
        # backfilled rows in the same agency (not just against existing IDs).
        candidates_by_agency: dict[int, list[tuple[int, str | None]]] = defaultdict(list)
        for r in conn.execute(
            "SELECT id, agency_id, raw_json FROM use_cases "
            "WHERE use_case_id IS NULL OR use_case_id = ''"
        ):
            extracted = _extract_id_from_raw(r["raw_json"])
            candidates_by_agency[r["agency_id"]].append((r["id"], extracted))

        backfilled = 0
        source_missing_no_value = 0
        source_missing_collision = 0
        collision_log: list[tuple[int, str, int]] = []

        for agency_id, rows in candidates_by_agency.items():
            # Within-batch counts for this agency.
            within_batch_counts: dict[str, int] = defaultdict(int)
            for _, val in rows:
                if val:
                    within_batch_counts[val] += 1

            for row_id, val in rows:
                if not val:
                    conn.execute(
                        "UPDATE use_cases SET id_provenance='source_missing' WHERE id=?",
                        (row_id,),
                    )
                    source_missing_no_value += 1
                    continue

                # Collision against an existing source ID, or against another
                # would-be backfill within the same agency.
                if (agency_id, val) in taken or within_batch_counts[val] > 1:
                    conn.execute(
                        "UPDATE use_cases SET id_provenance='source_missing' WHERE id=?",
                        (row_id,),
                    )
                    source_missing_collision += 1
                    collision_log.append((agency_id, val, row_id))
                    continue

                conn.execute(
                    "UPDATE use_cases SET use_case_id=?, id_provenance='backfilled_from_raw_json' "
                    "WHERE id=?",
                    (val, row_id),
                )
                taken.add((agency_id, val))
                backfilled += 1

        conn.commit()

        # After counts.
        after = {
            "null_or_empty": conn.execute(
                "SELECT COUNT(*) FROM use_cases WHERE use_case_id IS NULL OR use_case_id = ''"
            ).fetchone()[0],
            "source": conn.execute(
                "SELECT COUNT(*) FROM use_cases WHERE id_provenance='source'"
            ).fetchone()[0],
            "backfilled_from_raw_json": conn.execute(
                "SELECT COUNT(*) FROM use_cases WHERE id_provenance='backfilled_from_raw_json'"
            ).fetchone()[0],
            "source_missing": conn.execute(
                "SELECT COUNT(*) FROM use_cases WHERE id_provenance='source_missing'"
            ).fetchone()[0],
            "unaccounted": conn.execute(
                "SELECT COUNT(*) FROM use_cases "
                "WHERE use_case_id IS NULL AND id_provenance IS NULL"
            ).fetchone()[0],
        }
        print(f"AFTER:  {after}")
        print(
            f"backfilled={backfilled} "
            f"source_missing_no_value={source_missing_no_value} "
            f"source_missing_collision={source_missing_collision} "
            f"duplicate_source_collision={duplicate_source_collisions}"
        )
        if collision_log:
            print(f"COLLISIONS ({len(collision_log)}):")
            for agency_id, val, row_id in collision_log[:20]:
                print(f"  agency_id={agency_id}  use_case_id={val!r}  row_id={row_id}")
            if len(collision_log) > 20:
                print(f"  ... and {len(collision_log) - 20} more")

        if after["unaccounted"]:
            print(
                f"ERROR: {after['unaccounted']} rows have NULL use_case_id and "
                "NULL id_provenance — provenance not stamped.",
                file=sys.stderr,
            )
            return 1
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
