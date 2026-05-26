"""Audit landing rate of May 2026 linkage-pass proposals against current DB.

Reads the integration CSVs under BOTH passes:
  - audit/linkage_pass_2026-05/integration/
  - audit/linkage_pass_2026-05-followup/integration/

…and compares each staged proposal to the current `data/federal_ai_inventory_2025.db`.
Emits `audit/linkage_pass_2026-05/lossage_report.md` summarizing landing rates per
kind and itemizing every proposal that didn't make it.

Four proposal kinds tracked:
  - add_product           — proposed_new_products.csv
  - link                  — proposed_links.csv (entry_kind = use_case | consolidated)
  - link_via_add_product  — proposed_new_products.csv's linking_use_case_ids /
                            linking_consolidated_ids columns (these are the
                            `evidence_text='via add_product'` rows that Phase 1
                            just repaired)
  - add_alias             — proposed_aliases.csv
  - add_hierarchy_edge    — proposed_hierarchy_edges.csv

Resolution of stale use_case_ids / consolidated_use_case_ids in the link checks
reuses `scripts/relink_stale_use_case_products` helpers.

Read-only. Idempotent. Re-run any time to refresh the report.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "federal_ai_inventory_2025.db"
PRIMARY = ROOT / "audit" / "linkage_pass_2026-05"
FOLLOWUP = ROOT / "audit" / "linkage_pass_2026-05-followup"
REPORT_PATH = PRIMARY / "lossage_report.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relink_stale_use_case_products import (  # noqa: E402
    build_old_id_to_signature,
    build_signature_to_new_id,
    scan_backup_signatures,
)


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _product_id_by_name(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        _norm(name): pid
        for pid, name in conn.execute("SELECT id, canonical_name FROM products")
    }


def _alias_set(conn: sqlite3.Connection) -> set[tuple[int, str]]:
    return {
        (pid, _norm(alias))
        for pid, alias in conn.execute(
            "SELECT product_id, alias_text FROM product_aliases"
        )
    }


def _parent_of(conn: sqlite3.Connection) -> dict[int, int | None]:
    return {
        pid: parent
        for pid, parent in conn.execute(
            "SELECT id, parent_product_id FROM products"
        )
    }


def _ucp_set(conn: sqlite3.Connection) -> set[tuple[int, int]]:
    return {
        (uc_id, pid)
        for uc_id, pid in conn.execute(
            "SELECT use_case_id, product_id FROM use_case_products"
        )
    }


def _cup_set(conn: sqlite3.Connection) -> set[tuple[int, int]]:
    return {
        (c_id, pid)
        for c_id, pid in conn.execute(
            "SELECT consolidated_use_case_id, product_id FROM consolidated_use_case_products"
        )
    }


def _resolve_entry(
    raw_id: str,
    entry_kind: str,
    old_to_sig: dict[int, tuple[str, str]],
    sig_to_new: dict[tuple[str, str], int],
) -> tuple[int | None, str | None]:
    """Return (new_id, reason_if_missing). reason is None on success."""
    try:
        old_id = int(raw_id)
    except (TypeError, ValueError):
        return None, "non-integer entry_id"
    sig = old_to_sig.get(old_id)
    if sig is None:
        return None, f"no signature for old_id={old_id}"
    expected_prefix = "__uc__" if entry_kind == "use_case" else "__c__"
    if not sig[0].startswith(expected_prefix):
        # Cross-table — caller can interpret
        return None, f"signature prefix mismatch (got {sig[0][:6]}, want {expected_prefix})"
    new_id = sig_to_new.get(sig)
    if new_id is None:
        return None, f"signature {sig} not in current DB"
    return new_id, None


def _hydrate_backup_signatures(old_to_sig: dict[int, tuple[str, str]], needed: list[str]) -> None:
    """Lazy backup-scan fallback for any ids not in the slice inputs."""
    missing: set[int] = set()
    for raw in needed:
        try:
            missing.add(int(raw))
        except (TypeError, ValueError):
            continue
    missing -= set(old_to_sig.keys())
    if not missing:
        return
    print(f"audit: scanning backups for {len(missing)} ids missing from slice inputs…")
    recovered = scan_backup_signatures(missing)
    old_to_sig.update(recovered)
    print(f"  recovered {len(recovered)} via backups")


def audit() -> dict:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        pname_to_id = _product_id_by_name(conn)
        alias_set = _alias_set(conn)
        parent_of = _parent_of(conn)
        ucp_set = _ucp_set(conn)
        cup_set = _cup_set(conn)

        # Aggregate proposals from both passes
        proposed_products: list[dict] = []
        proposed_links: list[dict] = []
        proposed_aliases: list[dict] = []
        proposed_hierarchy: list[dict] = []
        for pass_dir in (PRIMARY, FOLLOWUP):
            integration = pass_dir / "integration"
            for row in _read(integration / "proposed_new_products.csv"):
                row["_pass"] = pass_dir.name
                proposed_products.append(row)
            for row in _read(integration / "proposed_links.csv"):
                row["_pass"] = pass_dir.name
                proposed_links.append(row)
            for row in _read(integration / "proposed_aliases.csv"):
                row["_pass"] = pass_dir.name
                proposed_aliases.append(row)
            for row in _read(integration / "proposed_hierarchy_edges.csv"):
                row["_pass"] = pass_dir.name
                proposed_hierarchy.append(row)

        # Build signature resolver (with backup hydration for stale ids)
        old_to_sig = build_old_id_to_signature()
        sig_to_new = build_signature_to_new_id(conn)
        needed_ids: list[str] = []
        for r in proposed_links:
            needed_ids.append(r.get("entry_id", ""))
        for r in proposed_products:
            for col in ("linking_use_case_ids", "linking_consolidated_ids"):
                for tok in (r.get(col, "") or "").split(","):
                    t = tok.strip()
                    if t:
                        needed_ids.append(t)
        _hydrate_backup_signatures(old_to_sig, needed_ids)

        # ====== add_product ======
        product_results = {"landed": [], "missing": []}
        for r in proposed_products:
            name = _norm(r["canonical_name"])
            pid = pname_to_id.get(name)
            if pid:
                product_results["landed"].append({**r, "_pid": pid})
            else:
                product_results["missing"].append(r)

        # ====== link (proposed_links.csv) ======
        link_results = {"landed": [], "missing": [], "cross_table_landed": []}
        for r in proposed_links:
            target_name = _norm(r["canonical_name"])
            pid = pname_to_id.get(target_name)
            if pid is None:
                link_results["missing"].append(
                    {**r, "_reason": f"product '{r['canonical_name']}' not in current DB"}
                )
                continue
            entry_kind = r["entry_kind"]
            new_id, reason = _resolve_entry(r["entry_id"], entry_kind, old_to_sig, sig_to_new)
            if new_id is None:
                # Try cross-table fallback
                alt_kind = "consolidated" if entry_kind == "use_case" else "use_case"
                cross_id, _ = _resolve_entry(r["entry_id"], alt_kind, old_to_sig, sig_to_new)
                if cross_id is not None:
                    target_set = cup_set if alt_kind == "consolidated" else ucp_set
                    if (cross_id, pid) in target_set:
                        link_results["cross_table_landed"].append(
                            {**r, "_resolved_id": cross_id, "_landed_table": alt_kind}
                        )
                        continue
                link_results["missing"].append({**r, "_reason": reason})
                continue
            target_set = ucp_set if entry_kind == "use_case" else cup_set
            if (new_id, pid) in target_set:
                link_results["landed"].append(
                    {**r, "_resolved_id": new_id, "_pid": pid}
                )
            else:
                link_results["missing"].append(
                    {**r, "_resolved_id": new_id, "_pid": pid, "_reason": "no row in target link table"}
                )

        # ====== link_via_add_product (linking_*_ids on proposed_new_products) ======
        via_results = {"landed": [], "missing": [], "cross_table_landed": []}
        for r in proposed_products:
            target_name = _norm(r["canonical_name"])
            pid = pname_to_id.get(target_name)
            if pid is None:
                continue  # product itself didn't land; counted in product_results.missing
            for kind, col in (
                ("use_case", "linking_use_case_ids"),
                ("consolidated", "linking_consolidated_ids"),
            ):
                for tok in (r.get(col, "") or "").split(","):
                    raw = tok.strip()
                    if not raw:
                        continue
                    new_id, reason = _resolve_entry(raw, kind, old_to_sig, sig_to_new)
                    if new_id is None:
                        # cross-table fallback
                        alt_kind = "consolidated" if kind == "use_case" else "use_case"
                        cross_id, _ = _resolve_entry(raw, alt_kind, old_to_sig, sig_to_new)
                        if cross_id is not None:
                            target_set = cup_set if alt_kind == "consolidated" else ucp_set
                            if (cross_id, pid) in target_set:
                                via_results["cross_table_landed"].append(
                                    {
                                        "canonical_name": r["canonical_name"],
                                        "kind": kind,
                                        "resolved_id": cross_id,
                                        "landed_table": alt_kind,
                                    }
                                )
                                continue
                        via_results["missing"].append(
                            {
                                "canonical_name": r["canonical_name"],
                                "entry_kind": kind,
                                "raw_id": raw,
                                "_pass": r["_pass"],
                                "_reason": reason,
                            }
                        )
                        continue
                    target_set = ucp_set if kind == "use_case" else cup_set
                    if (new_id, pid) in target_set:
                        via_results["landed"].append(
                            {"canonical_name": r["canonical_name"], "kind": kind, "id": new_id}
                        )
                    else:
                        via_results["missing"].append(
                            {
                                "canonical_name": r["canonical_name"],
                                "entry_kind": kind,
                                "raw_id": raw,
                                "resolved_id": new_id,
                                "_pass": r["_pass"],
                                "_reason": "no row in target link table",
                            }
                        )

        # ====== alias ======
        alias_results = {"landed": [], "missing": []}
        for r in proposed_aliases:
            target_name = _norm(r["canonical_name"])
            pid = pname_to_id.get(target_name)
            if pid is None:
                alias_results["missing"].append(
                    {**r, "_reason": f"product '{r['canonical_name']}' not in DB"}
                )
                continue
            if (pid, _norm(r["alias"])) in alias_set:
                alias_results["landed"].append({**r, "_pid": pid})
            else:
                alias_results["missing"].append(
                    {**r, "_pid": pid, "_reason": "alias not in product_aliases"}
                )

        # ====== hierarchy ======
        hier_results = {"landed": [], "missing": []}
        for r in proposed_hierarchy:
            child = pname_to_id.get(_norm(r["child_canonical_name"]))
            parent = pname_to_id.get(_norm(r["parent_canonical_name"]))
            if child is None or parent is None:
                hier_results["missing"].append(
                    {
                        **r,
                        "_reason": (
                            f"child={'missing' if not child else 'ok'} "
                            f"parent={'missing' if not parent else 'ok'}"
                        ),
                    }
                )
                continue
            if parent_of.get(child) == parent:
                hier_results["landed"].append({**r, "_child": child, "_parent": parent})
            else:
                actual = parent_of.get(child)
                hier_results["missing"].append(
                    {
                        **r,
                        "_child": child,
                        "_parent_expected": parent,
                        "_parent_actual": actual,
                        "_reason": f"child.parent_product_id={actual!r}, expected={parent!r}",
                    }
                )

        return {
            "products": product_results,
            "links": link_results,
            "via_add_product": via_results,
            "aliases": alias_results,
            "hierarchy": hier_results,
        }
    finally:
        conn.close()


def write_report(results: dict) -> None:
    def n(kind: str) -> tuple[int, int]:
        r = results[kind]
        landed = len(r["landed"])
        missing = len(r["missing"])
        return landed, missing

    p_landed, p_missing = n("products")
    l_landed, l_missing = n("links")
    l_cross = len(results["links"]["cross_table_landed"])
    v_landed, v_missing = n("via_add_product")
    v_cross = len(results["via_add_product"]["cross_table_landed"])
    a_landed, a_missing = n("aliases")
    h_landed, h_missing = n("hierarchy")

    out: list[str] = []
    out.append("# May 2026 linkage-pass lossage audit")
    out.append("")
    out.append(
        "Run by `scripts/audit_linkage_pass_lossage.py`. Diffs every "
        "proposal staged in `audit/linkage_pass_2026-05/integration/*.csv` "
        "and `audit/linkage_pass_2026-05-followup/integration/*.csv` "
        "against the current state of `data/federal_ai_inventory_2025.db`."
    )
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append("| Kind | Staged | Landed | Missing | Cross-table landed |")
    out.append("|---|---:|---:|---:|---:|")
    out.append(f"| `add_product` | {p_landed + p_missing} | {p_landed} | {p_missing} | — |")
    out.append(
        f"| `link` (proposed_links.csv) | {l_landed + l_missing + l_cross} | {l_landed} | {l_missing} | {l_cross} |"
    )
    out.append(
        f"| `link_via_add_product` (linking_*_ids columns) | {v_landed + v_missing + v_cross} | {v_landed} | {v_missing} | {v_cross} |"
    )
    out.append(f"| `add_alias` | {a_landed + a_missing} | {a_landed} | {a_missing} | — |")
    out.append(f"| `add_hierarchy_edge` | {h_landed + h_missing} | {h_landed} | {h_missing} | — |")
    out.append("")

    def _section(title: str, rows: list[dict], cols: list[str]) -> None:
        out.append(f"## {title}")
        out.append("")
        if not rows:
            out.append("_(none)_")
            out.append("")
            return
        out.append("| " + " | ".join(cols) + " |")
        out.append("|" + "|".join(["---"] * len(cols)) + "|")
        for r in rows:
            cells = [str(r.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols]
            out.append("| " + " | ".join(cells) + " |")
        out.append("")

    _section(
        "Missing `add_product` proposals",
        results["products"]["missing"],
        ["_pass", "canonical_name", "vendor", "confidence", "_agent"],
    )
    _section(
        "Missing `link` proposals",
        results["links"]["missing"],
        ["_pass", "_agent", "entry_kind", "entry_id", "canonical_name", "_reason"],
    )
    _section(
        "Missing `link_via_add_product` (per linking_*_ids column)",
        results["via_add_product"]["missing"],
        ["_pass", "canonical_name", "entry_kind", "raw_id", "_reason"],
    )
    _section(
        "Missing `add_alias` proposals",
        results["aliases"]["missing"],
        ["_pass", "_agent", "canonical_name", "alias", "_reason"],
    )
    _section(
        "Missing `add_hierarchy_edge` proposals",
        results["hierarchy"]["missing"],
        ["_pass", "_agent", "child_canonical_name", "parent_canonical_name", "_reason"],
    )

    if results["links"]["cross_table_landed"]:
        _section(
            "Cross-table landed (link routed to opposite table)",
            results["links"]["cross_table_landed"],
            ["_pass", "_agent", "entry_kind", "entry_id", "_landed_table", "canonical_name"],
        )

    REPORT_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {REPORT_PATH}")
    print(
        f"  add_product:           {p_landed}/{p_landed + p_missing} landed ({p_missing} missing)"
    )
    print(
        f"  link:                  {l_landed}/{l_landed + l_missing + l_cross} landed "
        f"({l_missing} missing, {l_cross} cross-table)"
    )
    print(
        f"  link_via_add_product:  {v_landed}/{v_landed + v_missing + v_cross} landed "
        f"({v_missing} missing, {v_cross} cross-table)"
    )
    print(f"  add_alias:             {a_landed}/{a_landed + a_missing} landed ({a_missing} missing)")
    print(
        f"  add_hierarchy_edge:    {h_landed}/{h_landed + h_missing} landed ({h_missing} missing)"
    )


def main() -> int:
    results = audit()
    write_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
