"""One-time follow-up: apply the 7 alias_existing entries that the
auto-integrator skipped because their target was specified in the agent's
notes field rather than in a structured parent_path/abbreviation pair.

Re-runnable safely (it just adds aliases to existing nodes).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# (parent_path_to_target, target_abbreviation_or_name, [aliases_to_add])
MANUAL_ALIASES = [
    (["TVA"], "ER", ["External Communications"]),
    (["EPA"], "OFA", ["AO"]),
    (["DOJ"], "UST", ["USTP", "Department of Justice / USTP"]),
    (["Treasury"], "Mint", ["United States Mint", "USM", "United States Mint (USM)"]),
    (["VA"], "ODS", ["Office of the Deputy Secretary of VA"]),
    (["FDIC"], "OGC", ["Legal Division"]),
]


def find_node(tree: list[dict], path: list[str], target_abbr_or_name: str) -> dict | None:
    """Walk path through ORG_TREE, then find a child matching the abbreviation
    or name."""
    cursor_list = tree
    for abbr in path:
        node = next((n for n in cursor_list if (n.get("abbreviation") or "") == abbr), None)
        if node is None:
            return None
        cursor_list = node.get("children") or []
    target = next(
        (n for n in cursor_list
         if (n.get("abbreviation") or "") == target_abbr_or_name
         or (n.get("name") or "") == target_abbr_or_name),
        None,
    )
    return target


def add_alias(node: dict, alias: str) -> bool:
    aliases = node.setdefault("aliases", [])
    if alias and alias not in aliases:
        aliases.append(alias)
        return True
    return False


def main() -> int:
    # Import the (post-integration) seed and mutate in memory
    from data.federal_hierarchy_seed import ORG_TREE  # noqa: E402

    # Reuse the serializer from apply_unmapped_research
    from scripts.apply_unmapped_research import write_seed_file  # noqa: E402

    added = 0
    not_found = []
    for path, target, aliases in MANUAL_ALIASES:
        node = find_node(ORG_TREE, path, target)
        if node is None:
            not_found.append((path, target))
            continue
        for a in aliases:
            if add_alias(node, a):
                added += 1

    write_seed_file(ORG_TREE)
    print(f"[manual-aliases] added {added} aliases across {len(MANUAL_ALIASES) - len(not_found)} nodes")
    if not_found:
        print(f"[manual-aliases] WARNING: targets not found:")
        for p, t in not_found:
            print(f"  {' > '.join(p)} > {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
