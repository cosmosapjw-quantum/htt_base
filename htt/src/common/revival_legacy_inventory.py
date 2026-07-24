"""PR-209: immutable legacy inventory, disposition graph and no-direct-import scan.

The legacy `bianchi_defect`/`HTT`/`MIO` project is preserved as immutable,
hash-bound research evidence. Every legacy object carries a pinned sha256 and a
KEEP_INTERFACE / KEEP_MATH / REBUILD_PRE_SOLVER / SOLVER_BENCHMARK /
MUTATION_FIXTURE / RETIRE_RESULT / HYPOTHESIS_ONLY disposition. Nothing legacy
is importable on a production path -- only clean-room successors are. This
module (a) verifies the on-disk drop against the pinned ledger (any deleted or
altered member breaks the check), (b) adjudicates each object into a disposition
class, and (c) scans repo production paths for any direct legacy import.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# Disposition classes grouped by salvage action.
KEEP_CLASSES = {"KEEP_INTERFACE", "KEEP_MATH", "KEEP_VISUAL_LANGUAGE"}
REBUILD_CLASSES = {"REBUILD_PRE_SOLVER", "SOLVER_BENCHMARK"}
MUTATION_CLASSES = {"MUTATION_FIXTURE"}
RETIRE_CLASSES = {"RETIRE_RESULT", "HYPOTHESIS_ONLY"}
ALL_DISPOSITIONS = KEEP_CLASSES | REBUILD_CLASSES | MUTATION_CLASSES | RETIRE_CLASSES

# Production import roots that must never name a legacy module directly.
PRODUCTION_ROOTS = ("htt/src", "htt/obsstat", "scripts/codex_harness", "bass")
# Legacy module basenames whose direct import would be a provenance breach.
_LEGACY_IMPORT_PATTERNS = [
    re.compile(r"^\s*from\s+legacy_sources[.\s]"),
    re.compile(r"^\s*import\s+legacy_sources\b"),
    re.compile(r"^\s*from\s+htt_legacy_revival"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_ledger(ledger_path: Path) -> list[dict]:
    return json.loads(ledger_path.read_text(encoding="utf-8"))["items"]


def _inventory_path(drop_root: Path, relative: str) -> Path:
    """Resolve one ledger member without escaping or following symlinks."""
    if not isinstance(relative, str) or not relative:
        raise ValueError("legacy inventory path must be a non-empty string")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise ValueError(f"legacy inventory path escapes the drop: {relative!r}")

    candidate = drop_root.joinpath(*pure.parts)
    current = drop_root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(
                f"legacy inventory path crosses a symlink: {relative!r}"
            )
    try:
        candidate.resolve(strict=False).relative_to(
            drop_root.resolve(strict=False)
        )
    except ValueError as exc:
        raise ValueError(
            f"legacy inventory path escapes the drop: {relative!r}"
        ) from exc
    return candidate


@dataclass(frozen=True)
class InventoryRow:
    path: str
    disposition: str
    expected_sha: str
    actual_sha: str | None
    present: bool

    @property
    def matches(self) -> bool:
        return self.present and self.actual_sha == self.expected_sha


def verify_inventory(ledger: list[dict], drop_root: Path) -> list[InventoryRow]:
    """Hash every pinned legacy object under the drop and compare to the ledger."""
    rows = []
    for item in ledger:
        p = _inventory_path(drop_root, item["path"])
        present = p.is_file()
        actual = sha256_file(p) if present else None
        rows.append(InventoryRow(item["path"], item["disposition"],
                                 item["sha256"], actual, present))
    return rows


def archive_integrity(drop_root: Path, ledger: list[dict]) -> list[dict]:
    """CRC-test the immutable archive zips and count members."""
    out = []
    for item in ledger:
        if not item["path"].endswith(".zip"):
            continue
        p = _inventory_path(drop_root, item["path"])
        if not p.is_file():
            out.append({"path": item["path"], "present": False, "bad_crc": "MISSING"})
            continue
        with zipfile.ZipFile(p) as z:
            members = len([n for n in z.namelist() if not n.endswith("/")])
            out.append({"path": item["path"], "present": True,
                        "members": members, "bad_crc": z.testzip()})
    return out


def adjudicate(disposition: str) -> str:
    if disposition in KEEP_CLASSES:
        return "KEEP"
    if disposition in REBUILD_CLASSES:
        return "REBUILD"
    if disposition in MUTATION_CLASSES:
        return "MUTATION"
    if disposition in RETIRE_CLASSES:
        return "RETIRE"
    raise ValueError(f"unknown disposition {disposition!r}")


def disposition_counts(ledger: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {"KEEP": 0, "REBUILD": 0, "MUTATION": 0, "RETIRE": 0}
    for item in ledger:
        counts[adjudicate(item["disposition"])] += 1
    return counts


def scan_no_direct_import(repo_root: Path, extra_roots: tuple[str, ...] = ()) -> list[dict]:
    """Scan production roots for any direct legacy import. Zero hits required."""
    hits = []
    for root in PRODUCTION_ROOTS + extra_roots:
        base = repo_root / root
        if not base.exists():
            continue
        for py in base.rglob("*.py"):
            try:
                text = py.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                for pat in _LEGACY_IMPORT_PATTERNS:
                    if pat.match(line):
                        hits.append({"file": py.relative_to(repo_root).as_posix(),
                                     "line": lineno, "text": line.strip()})
    return hits
