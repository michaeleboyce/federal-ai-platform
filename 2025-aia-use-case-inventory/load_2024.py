"""Load the raw 2024 (M-24-10) AI use case inventory corpus into the DB.

Phase 1 of the 2024 ↔ 2025 AI use case inventory comparison project (see
`docs/plans/2024-vs-2025-comparison/PLAN.md`). Sibling of `load_inventories.py`.

This loader reads `data/raw/2024_consolidated_ai_inventory_raw_v2.csv` — the
official OMB 2024 consolidated inventory, v2 (2,133 use cases, 62 columns,
cp1252-encoded) — and lands every row in `use_cases_2024` in its **native
M-24-10 shape**. No load-time recoding: 2024 values are stored verbatim;
mapping to the 2025 taxonomy (`IMPACT_TYPE_RECODE_2024` /
`DEV_STAGE_RECODE_2024`) is a later-phase comparison concern, not ingestion.

Idempotent: clears `use_cases_2024` then re-inserts every row.
"""

import csv
import json
import sys
from pathlib import Path

from db import apply_migrations, get_connection
from column_maps_2024 import COLUMN_CROSSWALK_2024, map_2024_headers
from load_inventories import _lookup_agency_id, slugify
from omb_consolidated_match import normalize_agency

CSV_PATH = Path(__file__).parent / "data" / "raw" / "2024_consolidated_ai_inventory_raw_v2.csv"

# The 2024 consolidated inventory is cp1252-encoded. We do NOT route it
# through `load_inventories.read_csv_rows`: that helper's fallback chain tries
# latin-1 before cp1252, and latin-1 decodes every byte *without raising* —
# so the chain "succeeds" on latin-1 but mangles cp1252-specific punctuation
# (byte 0x92, a curly apostrophe in cp1252, becomes a U+0092 C1 control char
# under latin-1). The 2024 narrative fields are full of curly quotes, so we
# decode explicitly as cp1252 here.
ENCODING_2024 = "cp1252"

# The 62 native-2024 data column names, in CSV order. Single source of truth:
# the Phase 0 crosswalk. The migration generates the table DDL from the same
# list, so loader and schema can never disagree.
DATA_FIELDS: list[str] = [e["field"] for e in COLUMN_CROSSWALK_2024]


def load(conn, csv_path: Path = CSV_PATH) -> dict:
    """Clear and reload `use_cases_2024` from the 2024 consolidated CSV.

    Returns a stats dict: rows loaded, agencies resolved, rows skipped, and
    any unresolved-agency tally (expected empty — all 41 2024 agencies
    resolve, `TREAS`→`Treasury` via `normalize_agency`).
    """
    with open(csv_path, encoding=ENCODING_2024) as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        raise ValueError(f"{csv_path} has no data rows")

    headers = [str(h).strip() for h in rows[0]]
    data_rows = [r for r in rows[1:] if any(str(c).strip() for c in r)]

    # Ordinal-aware header mapping. The 2024 CSV repeats the literal
    # "If Other, please explain." header 10×, so map_2024_headers resolves
    # positionally. Expect every one of the 62 columns to resolve.
    mapping = map_2024_headers(headers)
    if len(mapping) != len(COLUMN_CROSSWALK_2024):
        raise ValueError(
            f"expected {len(COLUMN_CROSSWALK_2024)} mapped columns, "
            f"got {len(mapping)} — header layout drifted from the crosswalk"
        )

    # The column index that carries `agency_abbreviation` — used for agency
    # resolution and as the slug prefix.
    abbr_idx = next(
        i for i, field in mapping.items() if field == "agency_abbreviation"
    )
    name_idx = next(
        i for i, field in mapping.items() if field == "use_case_name"
    )

    # Idempotent reload. m011's use_case_year_links has FK→use_cases_2024(id),
    # so it must be cleared first. It is rebuilt later in the pipeline by
    # match_year_over_year.py (wipe-and-reload); the guard keeps this loader
    # runnable against DBs predating m011.
    if conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='use_case_year_links'"
    ).fetchone():
        conn.execute("DELETE FROM use_case_year_links")

    # m014's use_case_tags_2024 also FK-references use_cases_2024(id), but
    # unlike year-links nothing downstream rebuilds it — the multi-wave 2024
    # tag backfill (and its hand-applied corrections) lives only in this
    # table. Snapshot the rows keyed by slug (unique, deterministic on
    # (agency, name, load order)), clear, and re-attach after the reload.
    tags_snapshot: list[tuple[str, tuple]] = []
    tag_cols: list[str] = []
    has_tags_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='use_case_tags_2024'"
    ).fetchone()
    if has_tags_table:
        tag_cols = [
            r[1]
            for r in conn.execute("PRAGMA table_info(use_case_tags_2024)")
            if r[1] not in ("id", "use_case_id_2024")
        ]
        col_list = ", ".join(f"t.{c}" for c in tag_cols)
        tags_snapshot = [
            (row[0], tuple(row[1:]))
            for row in conn.execute(
                f"""SELECT u.slug, {col_list}
                      FROM use_case_tags_2024 t
                      JOIN use_cases_2024 u ON u.id = t.use_case_id_2024"""
            )
        ]
        conn.execute("DELETE FROM use_case_tags_2024")
    conn.execute("DELETE FROM use_cases_2024")

    insert_cols = DATA_FIELDS + ["agency_id", "source_file", "slug", "raw_json"]
    placeholders = ",".join(["?"] * len(insert_cols))
    insert_sql = (
        f"INSERT INTO use_cases_2024 ({','.join(insert_cols)}) "
        f"VALUES ({placeholders})"
    )

    inserted = 0
    skipped = 0
    skipped_unknown_agency: dict[str, int] = {}
    seen_slugs: set[str] = set()
    agency_ids: set[int] = set()

    for idx, data_row in enumerate(data_rows):
        # field name -> verbatim cell value (no recoding).
        field_values: dict[str, str] = {}
        for col_idx, field in mapping.items():
            cell = data_row[col_idx] if col_idx < len(data_row) else ""
            field_values[field] = str(cell).strip() if cell is not None else ""

        raw_abbr = field_values.get("agency_abbreviation", "")
        agency_abbr = normalize_agency(raw_abbr) if raw_abbr else None
        agency_id = _lookup_agency_id(conn, agency_abbr)
        if not agency_id:
            # Defensive: every 2024 agency resolves (verified), but never
            # silently drop a row — tally it instead.
            key = raw_abbr or "(blank)"
            skipped_unknown_agency[key] = skipped_unknown_agency.get(key, 0) + 1
            skipped += 1
            continue
        agency_ids.add(agency_id)

        # Slug is deterministic on (agency, use_case_name). 2024
        # (agency, name) pairs can repeat — disambiguate collisions with a
        # numeric suffix so the UNIQUE constraint never aborts the load.
        use_case_name = field_values.get("use_case_name", "")
        slug = slugify(raw_abbr or agency_abbr, use_case_name, idx)
        if slug in seen_slugs:
            n = 2
            while f"{slug}-{n}" in seen_slugs:
                n += 1
            slug = f"{slug}-{n}"
        seen_slugs.add(slug)

        # raw_json is keyed by crosswalk `field` name (unique 62/62), NOT by
        # the raw CSV header — the repeated "If Other, please explain."
        # header would collapse 10 columns into 1.
        raw_json = json.dumps(field_values, ensure_ascii=False)

        values = (
            [field_values.get(f) for f in DATA_FIELDS]
            + [agency_id, csv_path.name, slug, raw_json]
        )
        conn.execute(insert_sql, values)
        inserted += 1

    # Re-attach the 2024 tag rows to the freshly assigned ids via slug.
    tags_restored = 0
    tags_unresolved = 0
    if tags_snapshot:
        slug_to_id = {
            r[0]: r[1] for r in conn.execute("SELECT slug, id FROM use_cases_2024")
        }
        placeholders_t = ",".join(["?"] * (len(tag_cols) + 1))
        insert_tags_sql = (
            f"INSERT INTO use_case_tags_2024 (use_case_id_2024, {','.join(tag_cols)}) "
            f"VALUES ({placeholders_t})"
        )
        for slug, vals in tags_snapshot:
            new_id = slug_to_id.get(slug)
            if new_id is None:
                tags_unresolved += 1
                continue
            conn.execute(insert_tags_sql, (new_id, *vals))
            tags_restored += 1
        if tags_unresolved / max(len(tags_snapshot), 1) > 0.02:
            conn.rollback()
            raise SystemExit(
                f"load_2024: {tags_unresolved}/{len(tags_snapshot)} 2024 tag "
                "rows failed slug re-attachment — aborting so the tag "
                "backfill is not silently dropped."
            )

    conn.commit()

    return {
        "file": csv_path.name,
        "encoding": ENCODING_2024,
        "inserted": inserted,
        "skipped": skipped,
        "agencies_resolved": len(agency_ids),
        "skipped_unknown_agencies": skipped_unknown_agency,
        "tags_2024_restored": tags_restored,
        "tags_2024_unresolved": tags_unresolved,
    }


def main() -> int:
    conn = get_connection()
    try:
        apply_migrations(conn)
        stats = load(conn)
    finally:
        conn.close()

    print("=== load_2024 ===")
    print(f"file:     {stats['file']} ({stats['encoding']})")
    print(f"loaded:   {stats['inserted']}")
    print(f"skipped:  {stats['skipped']}")
    print(f"agencies: {stats['agencies_resolved']}")
    if stats["skipped_unknown_agencies"]:
        print(f"unresolved agencies: {stats['skipped_unknown_agencies']}")
    print(
        f"2024 tags: {stats['tags_2024_restored']} re-attached, "
        f"{stats['tags_2024_unresolved']} unresolved"
    )
    print(f"{stats['inserted']} loaded, {stats['skipped']} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
