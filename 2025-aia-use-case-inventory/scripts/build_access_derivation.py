"""Generate audit/article/access_derivation.md — the full derivation of the
person-weighted AI-access statistic, per agency, with sources.

Answers "where does ~747K eligible / ~282K with access / ~38% come from?"
and pins the two-denominators rule: the FedScope ~2.31M total federal
civilian workforce is ONLY for sizing the DoD blind spot; person-weighted
access claims use covered-agency headcount x ai_eligible_share.

Read-only; deterministic given the same DB except the Generated line.
Re-run after any rebuild that touches agency_workforce_profile or
agency_ai_access_evidence:

    python3 scripts/build_access_derivation.py
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "federal_ai_inventory_2025.db"
OUT = ROOT / "audit" / "article" / "access_derivation.md"


def main() -> int:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        WITH best AS (
          -- most-available corroborated-or-assessed share per agency, with its evidence row
          SELECT e.agency_id,
                 e.estimated_share_of_eligible AS share,
                 e.coverage_assessment,
                 e.status,
                 e.confidence,
                 e.tool_name,
                 e.source_type,
                 ROW_NUMBER() OVER (
                   PARTITION BY e.agency_id
                   ORDER BY e.estimated_share_of_eligible DESC, e.id
                 ) AS rn
            FROM agency_ai_access_evidence e
           WHERE e.estimated_share_of_eligible IS NOT NULL
        )
        SELECT a.abbreviation,
               w.total_headcount,
               w.headcount_as_of,
               w.headcount_source_title,
               w.ai_eligible_share,
               w.ai_eligible_rationale,
               w.confidence AS workforce_confidence,
               b.share, b.coverage_assessment, b.status, b.confidence AS access_confidence,
               b.tool_name, b.source_type
          FROM agency_workforce_profile w
          JOIN agencies a ON a.id = w.agency_id
          LEFT JOIN best b ON b.agency_id = w.agency_id AND b.rn = 1
         WHERE w.level = 'agency' AND w.total_headcount > 0
         ORDER BY w.total_headcount * COALESCE(w.ai_eligible_share, 0) DESC
        """
    ).fetchall()

    total_head = sum(r["total_headcount"] for r in rows)
    total_elig = sum(r["total_headcount"] * (r["ai_eligible_share"] or 0) for r in rows)
    assessed = [r for r in rows if r["share"] is not None]
    unassessed = [r for r in rows if r["share"] is None]
    with_access = sum(
        r["total_headcount"] * (r["ai_eligible_share"] or 0) * r["share"] for r in assessed
    )
    elig_unassessed = sum(
        r["total_headcount"] * (r["ai_eligible_share"] or 0) for r in unassessed
    )

    L: list[str] = []
    w = L.append
    w("# Derivation — the person-weighted AI-access statistic")
    w("")
    w(f"_Generated {_dt.date.today().isoformat()} by `scripts/build_access_derivation.py`;")
    w("re-run after any rebuild touching `agency_workforce_profile` or")
    w("`agency_ai_access_evidence`. Every input row carries its own source")
    w("columns in the DB; the table below shows them._")
    w("")
    w("## The two denominators — do not conflate")
    w("")
    w("1. **~2.31M** — OPM FedScope total federal non-postal civilian workforce")
    w("   (Sept 2024). ONLY legitimate use: sizing the coverage blind spot")
    w("   (DoD's 772,549 civilians ≈ one-third filed no 2025 inventory).")
    w("   Never the base for an access claim: it includes agencies the data")
    w("   cannot assess and makes no eligibility adjustment.")
    w("2. **The eligible base (below)** — the correct denominator for every")
    w('   person-weighted access claim, and the one matching the mandate\'s own')
    w('   scope ("employees whose work could benefit"): covered-agency')
    w("   headcount x per-agency `ai_eligible_share` (sourced rationale per")
    w("   row: excludes frontline/field staff without government computing).")
    w("")
    w("## The chain")
    w("")
    w(f"| Step | Value | Source |")
    w("|---|---|---|")
    w(f"| Covered agencies with workforce profiles | {len(rows)} | `agency_workforce_profile` level='agency' |")
    w(f"| Total covered civilian headcount | {total_head:,} | per-row FedScope/agency sources (as-of dates in table) |")
    w(f"| AI-eligible after per-agency eligibility share | {round(total_elig):,} | `ai_eligible_share` x headcount, summed |")
    w(f"| Eligible at agencies WITH an access assessment | {round(total_elig - elig_unassessed):,} ({len(assessed)} agencies) | `agency_ai_access_evidence` best share per agency |")
    w(f"| — of whom, estimated WITH access to a general-purpose tool | {round(with_access):,} (~{with_access/total_elig:.0%} of all eligible) | share x eligible, summed |")
    w(f"| Eligible at the {len(unassessed)} UNASSESSED agencies | {round(elig_unassessed):,} (~{elig_unassessed/total_elig:.0%}) | unmeasured, NOT zero |")
    w("")
    w("**Headline form:** of the ~" + f"{round(total_elig/1000)*1000:,}".replace(",000", "K") + " AI-eligible civilian employees at")
    w(f"covered agencies, public evidence supports general-purpose AI access for")
    w(f"roughly {round(with_access):,} (~{with_access/total_elig:.0%}); the remainder work where broad access")
    w("is not publicly evidenced. Attribute to IFP estimates.")
    w("")
    w("## Method caveats (travel with any citation)")
    w("")
    w("- **Simplified max-share model**: this doc takes each agency's single")
    w("  most-available assessed share. The dashboard's seat model")
    w("  (`dashboard/lib/db/experience/seat-model.ts`) is the authoritative")
    w("  estimator (per-tool union with independence assumption, stratum caps,")
    w("  FedScope ceilings) and will differ modestly.")
    w("- Access shares mix corroborated (press/official) and IFP-assessed")
    w("  (`searched_no_source`) rows — the Status column below distinguishes.")
    w("- The 2026-07-05 `/experience` page audit left open defects; derive")
    w("  numbers from the DB (this doc), not from the live page.")
    w("- DoD and the intelligence community are absent from the base entirely")
    w("  (no inventory, no workforce profile row).")
    w("")
    w("## Per-agency derivation")
    w("")
    w("| Agency | Headcount | As of | Eligible share | Eligible | Access share | Tier | Status/conf | Tool |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        elig = r["total_headcount"] * (r["ai_eligible_share"] or 0)
        share = f"{r['share']:.0%}" if r["share"] is not None else "—"
        tier = r["coverage_assessment"] or "no assessment"
        status = (
            f"{r['status']}/{r['access_confidence']}" if r["share"] is not None else "—"
        )
        w(
            f"| {r['abbreviation']} | {r['total_headcount']:,} | {r['headcount_as_of'] or '?'} "
            f"| {r['ai_eligible_share']:.0%} | {round(elig):,} | {share} | {tier} "
            f"| {status} | {r['tool_name'] or '—'} |"
        )
    w("")
    w("_Eligibility rationales, headcount source URLs/titles, and verbatim")
    w("evidence quotes are on the underlying rows (`agency_workforce_profile`,")
    w("`agency_ai_access_evidence`) — cite from there when a per-agency claim")
    w("needs its primary source._")
    w("")

    OUT.write_text("\n".join(L))
    print(f"wrote {OUT} ({len(L)} lines; {len(rows)} agencies)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
