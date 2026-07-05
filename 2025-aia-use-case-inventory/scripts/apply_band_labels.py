"""Apply the band_labels_2026-07 population labels to the DB.

Reads every `labels_*.csv` under audit/retag/band_labels_2026-07/, overlays
`audit_overrides.csv` (the Fable audit layer — overrides win; `agree`
verdicts mark the row audited without changing labels), resolves each
`slug` to the current `consolidated_use_cases.id`, and wipe-and-reloads
`consolidated_band_labels` (table created by migration m017).

Resolution: slugs are deterministic (`slugify(agency_abbr, key)`) and
survive rebuilds, so slug lookup is the primary key. If source text was
re-edited and a slug drifted, a difflib fallback on (agency, ai_use_case)
at ratio >= 0.92 catches it. Hard-fails when the unresolved fraction
exceeds 2% (a rebuild must never silently drop the labeling pass) — same
contract as scripts/uc_signature.py::Resolver. Unresolved rows are logged
to `apply_drops.csv`.

Idempotent. Safe to re-run. Wired into `make fix` after migrations.
"""
from __future__ import annotations

import csv
import sys
from difflib import SequenceMatcher
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db import get_connection  # noqa: E402

PASS_DIR = _ROOT / "audit" / "retag" / "band_labels_2026-07"
FUZZY_RATIO = 0.92
MAX_UNRESOLVED = 0.02

VALID = {
    "unit_counted": {
        "employees",
        "employees_and_contractors",
        "devices_endpoints",
        "public_users",
        "applicants_cases",
        "unknown",
    },
    "org_scope": {"enterprise", "component", "unknown"},
    "stratum": {
        "general",
        "technical",
        "legal",
        "investigative",
        "comms",
        "clinical",
        "excluded_not_seats",
    },
    "confidence": {"high", "medium", "low"},
}
POPULATION_FIXED = {
    "all_staff",
    "office_staff",
    "single_component",
    "unknown",
}


def _norm(s: str | None) -> str:
    return " ".join((s or "").strip().lower().split())


def _validate(row: dict, src: str) -> list[str]:
    errs = []
    for field, vocab in VALID.items():
        if row.get(field) not in vocab:
            errs.append(f"{src}: slug={row.get('slug')} bad {field}"
                        f"={row.get(field)!r}")
    pop = row.get("population") or ""
    if pop not in POPULATION_FIXED and not pop.startswith("occupation:"):
        errs.append(f"{src}: slug={row.get('slug')} bad population={pop!r}")
    if not row.get("slug"):
        errs.append(f"{src}: row missing slug")
    return errs


def load_labels() -> tuple[dict[str, dict], list[str]]:
    """Returns (labels by slug with audit overlay applied, errors)."""
    errors: list[str] = []
    labels: dict[str, dict] = {}
    label_files = sorted(PASS_DIR.glob("labels_*.csv"))
    if not label_files:
        return {}, [f"no labels_*.csv under {PASS_DIR}"]

    # Slugs with an `override` audit verdict are replaced wholesale — the
    # base row must not be validated (overrides often exist precisely
    # because the base row is malformed, e.g. out-of-vocabulary stratum).
    overridden: set[str] = set()
    overrides = PASS_DIR / "audit_overrides.csv"
    if overrides.exists():
        with overrides.open() as f:
            for row in csv.DictReader(f):
                if row.get("audit_verdict") == "override":
                    overridden.add(row.get("slug", ""))

    for path in label_files:
        with path.open() as f:
            for row in csv.DictReader(f):
                slug = row.get("slug", "")
                if slug in overridden:
                    # Placeholder; the override pass below fills the fields.
                    labels[slug] = {
                        **row,
                        "labeler": f"sonnet:{path.stem.replace('labels_', '')}",
                        "audited": 0,
                        "audit_verdict": None,
                        "audit_reasoning": None,
                    }
                    continue
                errs = _validate(row, path.name)
                if errs:
                    errors.extend(errs)
                    continue
                if slug in labels:
                    errors.append(f"{path.name}: duplicate slug {slug}")
                    continue
                labels[slug] = {
                    **row,
                    "labeler": f"sonnet:{path.stem.replace('labels_', '')}",
                    "audited": 0,
                    "audit_verdict": None,
                    "audit_reasoning": None,
                }

    if overrides.exists():
        with overrides.open() as f:
            for row in csv.DictReader(f):
                slug = row.get("slug", "")
                base = labels.get(slug)
                if base is None:
                    errors.append(
                        f"audit_overrides.csv: slug {slug!r} not in labels"
                    )
                    continue
                verdict = row.get("audit_verdict")
                if verdict not in {"agree", "override", "escalated"}:
                    errors.append(
                        f"audit_overrides.csv: slug {slug} bad audit_verdict"
                        f"={verdict!r}"
                    )
                    continue
                base["audited"] = 1
                base["audit_verdict"] = verdict
                base["audit_reasoning"] = row.get("audit_reasoning")
                if verdict == "override":
                    errs = _validate(row, "audit_overrides.csv")
                    if errs:
                        errors.extend(errs)
                        continue
                    for field in (
                        "unit_counted",
                        "population",
                        "org_scope",
                        "stratum",
                        "confidence",
                        "reasoning",
                    ):
                        base[field] = row[field]
                    base["labeler"] = "fable-audit"
                elif verdict == "escalated":
                    # Undecidable after audit — surface, don't hide.
                    base["population"] = "unknown"
                    base["confidence"] = "low"
    return labels, errors


def main() -> int:
    if not sorted(PASS_DIR.glob("labels_*.csv")):
        print(
            f"WARNING: no labels_*.csv under {PASS_DIR} yet — skipping "
            f"(batches land incrementally)."
        )
        return 0
    labels, errors = load_labels()
    if errors:
        print("VALIDATION ERRORS — nothing written:")
        for e in errors:
            print(f"  - {e}")
        return 1

    conn = get_connection()
    try:
        live = {
            slug: (cid, _norm(agency), _norm(name))
            for slug, cid, agency, name in conn.execute(
                """
                SELECT c.slug, c.id, a.abbreviation, c.ai_use_case
                  FROM consolidated_use_cases c
                  JOIN agencies a ON a.id = c.agency_id
                 WHERE c.estimated_licenses_users IS NOT NULL
                   AND c.estimated_licenses_users != ''
                """
            )
        }
        by_sig = {}
        for slug, (cid, agency, name) in live.items():
            by_sig.setdefault(agency, []).append((name, cid, slug))

        resolved: dict[str, tuple[int, dict]] = {}
        drops: list[dict] = []
        for slug, row in labels.items():
            if slug in live:
                resolved[slug] = (live[slug][0], row)
                continue
            # Fuzzy fallback on (agency, ai_use_case).
            agency = _norm(row.get("agency"))
            name = _norm(row.get("ai_use_case"))
            candidates = [
                (SequenceMatcher(None, name, cand_name).ratio(), cid, cslug)
                for cand_name, cid, cslug in by_sig.get(agency, [])
                if cslug not in resolved
            ]
            candidates = [c for c in candidates if c[0] >= FUZZY_RATIO]
            if len(candidates) == 1:
                _, cid, cslug = candidates[0]
                row = {**row, "slug": cslug}
                resolved[cslug] = (cid, row)
            else:
                drops.append(
                    {**row, "_drop_reason": "slug_unresolved"
                     if not candidates else "fuzzy_ambiguous"}
                )

        unresolved_frac = len(drops) / max(1, len(labels))
        if drops:
            drop_path = PASS_DIR / "apply_drops.csv"
            with drop_path.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(drops[0].keys()))
                w.writeheader()
                w.writerows(drops)
            print(f"{len(drops)} unresolved rows -> {drop_path}")
        if unresolved_frac > MAX_UNRESOLVED:
            print(
                f"FATAL: {unresolved_frac:.1%} of label rows unresolved "
                f"(max {MAX_UNRESOLVED:.0%}). Refusing to apply."
            )
            return 1

        with conn:
            conn.execute("DELETE FROM consolidated_band_labels")
            for slug, (cid, row) in resolved.items():
                conn.execute(
                    """
                    INSERT INTO consolidated_band_labels (
                        consolidated_use_case_id, slug, unit_counted,
                        population, org_scope, stratum, confidence,
                        reasoning, labeler, audited, audit_verdict,
                        audit_reasoning
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        cid,
                        slug,
                        row["unit_counted"],
                        row["population"],
                        row["org_scope"],
                        row["stratum"],
                        row["confidence"],
                        row.get("reasoning"),
                        row["labeler"],
                        row["audited"],
                        row["audit_verdict"],
                        row["audit_reasoning"],
                    ),
                )
        n_banded = conn.execute(
            """
            SELECT COUNT(*) FROM consolidated_use_cases
             WHERE estimated_licenses_users IS NOT NULL
               AND estimated_licenses_users != ''
            """
        ).fetchone()[0]
        print(
            f"Applied {len(resolved)} band labels "
            f"({n_banded} banded rows live; "
            f"{sum(1 for _, (_, r) in resolved.items() if r['audited'])} audited)."
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
