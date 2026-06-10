"""Signature-based id resolution for the 2026-04 retag apply scripts.

The retag audit CSVs under audit/retag/ carry `use_case_id`s from the
2026-04 DB snapshot. Those AUTOINCREMENT ids rotate on every `make fix`
(see CLAUDE.md "Multi-agent safety"), so applying them verbatim silently
no-ops — or worse. This module translates:

    old id ──(audit/retag/id_snapshot_2026-04.csv)──▶ (agency, name)
           ──(live DB lookup)────────────────────────▶ current id(s)

A signature may fan out to several current ids when an agency filed the
same use-case name more than once; corrections are applied to all of them
(they describe the same system). Resolution is tracked per label and
`Resolver.check()` exits non-zero when the unresolved fraction exceeds the
threshold — a rebuild must never silently drop an audit again.

Fuzzy fallback: when an exact signature misses (name edited since April),
we accept a unique same-agency candidate with difflib ratio ≥ 0.92.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "audit" / "retag" / "id_snapshot_2026-04.csv"

FUZZY_RATIO = 0.92
DEFAULT_MAX_UNRESOLVED = 0.02


def _norm(s: str | None) -> str:
    return " ".join((s or "").strip().lower().split())


class Resolver:
    """Resolves 2026-04 snapshot ids (or raw signatures) to current DB ids."""

    def __init__(self, conn: sqlite3.Connection):
        # old id -> signature, from the committed snapshot
        self.snap_uc: dict[int, tuple[str, str]] = {}
        self.snap_cons: dict[int, tuple[str, str]] = {}
        with open(SNAPSHOT) as f:
            for row in csv.DictReader(f):
                sig = (_norm(row["agency"]), _norm(row["name"]))
                if row["kind"] == "uc":
                    self.snap_uc[int(row["old_id"])] = sig
                else:
                    self.snap_cons[int(row["old_id"])] = sig

        # live signature -> [current ids]
        self.cur_uc: dict[tuple[str, str], list[int]] = {}
        for r in conn.execute(
            """SELECT u.id, a.abbreviation, u.use_case_name
                 FROM use_cases u JOIN agencies a ON a.id = u.agency_id"""
        ):
            self.cur_uc.setdefault((_norm(r[1]), _norm(r[2])), []).append(r[0])
        self.cur_cons: dict[tuple[str, str], list[int]] = {}
        for r in conn.execute(
            """SELECT c.id, a.abbreviation, c.ai_use_case
                 FROM consolidated_use_cases c JOIN agencies a ON a.id = c.agency_id"""
        ):
            self.cur_cons.setdefault((_norm(r[1]), _norm(r[2])), []).append(r[0])

        # per-agency name lists for the fuzzy fallback (use_cases only)
        self._agency_names: dict[str, list[tuple[str, tuple[str, str]]]] = {}
        for (ag, name), _ids in self.cur_uc.items():
            self._agency_names.setdefault(ag, []).append((name, (ag, name)))

        self.stats = {"exact": 0, "fuzzy": 0, "fanout_extra": 0, "unresolved": 0}
        self.unresolved: list[str] = []

    # -- internals ---------------------------------------------------------
    def _fuzzy(self, sig: tuple[str, str]) -> tuple[str, str] | None:
        ag, name = sig
        best: tuple[float, tuple[str, str]] | None = None
        second = 0.0
        for cand_name, cand_sig in self._agency_names.get(ag, []):
            r = SequenceMatcher(None, name, cand_name).ratio()
            if best is None or r > best[0]:
                second = best[0] if best else 0.0
                best = (r, cand_sig)
            elif r > second:
                second = r
        if best and best[0] >= FUZZY_RATIO and best[0] > second:
            return best[1]
        return None

    def _resolve(
        self,
        sig: tuple[str, str] | None,
        table: dict[tuple[str, str], list[int]],
        context: str,
        allow_fuzzy: bool,
    ) -> list[int]:
        if sig is None:
            self.stats["unresolved"] += 1
            self.unresolved.append(context)
            return []
        ids = table.get(sig)
        if ids:
            self.stats["exact"] += 1
            self.stats["fanout_extra"] += len(ids) - 1
            return ids
        if allow_fuzzy and table is self.cur_uc:
            fsig = self._fuzzy(sig)
            if fsig is not None:
                self.stats["fuzzy"] += 1
                ids = table[fsig]
                self.stats["fanout_extra"] += len(ids) - 1
                return ids
        self.stats["unresolved"] += 1
        self.unresolved.append(f"{context} sig={sig!r}")
        return []

    # -- public ------------------------------------------------------------
    def uc(
        self,
        old_id: int | None,
        agency: str | None = None,
        name: str | None = None,
    ) -> list[int]:
        """Current use_cases ids for a 2026-04 id and/or a CSV signature.

        Prefers the CSV's own (agency, name) columns when given; falls back
        to the snapshot signature for old-id-only files.
        """
        sig = None
        if agency and name:
            sig = (_norm(agency), _norm(name))
        elif old_id is not None:
            sig = self.snap_uc.get(old_id)
        ctx = f"uc old_id={old_id}"
        # If the CSV signature misses, try the snapshot one before fuzzy.
        if sig is not None and sig not in self.cur_uc and old_id in self.snap_uc:
            snap_sig = self.snap_uc[old_id]
            if snap_sig in self.cur_uc:
                sig = snap_sig
        return self._resolve(sig, self.cur_uc, ctx, allow_fuzzy=True)

    def cons(self, old_id: int | None) -> list[int]:
        sig = self.snap_cons.get(old_id) if old_id is not None else None
        return self._resolve(sig, self.cur_cons, f"cons old_id={old_id}", False)

    def cons_by_signature(self, agency: str | None, name: str | None) -> list[int]:
        """Resolve a consolidated (Appendix B) entry by agency + name.

        Tolerates the trailing period the OMB file uses ("Generating code
        using AI.") that audit CSVs tend to drop.
        """
        ag, nm = _norm(agency), _norm(name)
        for candidate in (nm, nm + ".", nm.rstrip(".")):
            ids = self.cur_cons.get((ag, candidate))
            if ids:
                self.stats["exact"] += 1
                self.stats["fanout_extra"] += len(ids) - 1
                return ids
        self.stats["unresolved"] += 1
        self.unresolved.append(f"cons sig=({ag!r}, {nm!r})")
        return []

    def uc_or_cons(self, old_id: int | None) -> tuple[list[int], list[int]]:
        """For files whose id column mixes both tables (searches.csv)."""
        if old_id is None:
            return [], []
        if old_id in self.snap_uc:
            return self.uc(old_id), []
        if old_id in self.snap_cons:
            return [], self.cons(old_id)
        self.stats["unresolved"] += 1
        self.unresolved.append(f"uc_or_cons old_id={old_id}")
        return [], []

    def check(self, label: str, max_unresolved: float = DEFAULT_MAX_UNRESOLVED) -> None:
        """Print the resolution report; exit non-zero above the threshold."""
        attempted = self.stats["exact"] + self.stats["fuzzy"] + self.stats["unresolved"]
        frac = (self.stats["unresolved"] / attempted) if attempted else 0.0
        print(
            f"[resolution:{label}] exact={self.stats['exact']} "
            f"fuzzy={self.stats['fuzzy']} fanout_extra={self.stats['fanout_extra']} "
            f"unresolved={self.stats['unresolved']} ({frac:.1%})"
        )
        for u in self.unresolved[:20]:
            print(f"    UNRESOLVED {u}")
        if len(self.unresolved) > 20:
            print(f"    ... and {len(self.unresolved) - 20} more")
        if frac > max_unresolved:
            print(
                f"FATAL [{label}]: unresolved fraction {frac:.1%} exceeds "
                f"{max_unresolved:.0%} — refusing to continue (silent no-op guard)."
            )
            sys.exit(1)
