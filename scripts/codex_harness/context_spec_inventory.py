#!/usr/bin/env python3
"""List the regular repository files referenced by the live claim registry."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path


REGISTRY_PATH = ".agent-harness/context/CLAIM_REGISTRY.jsonl"


class ContextSpecInventoryError(ValueError):
    """Raised when a registered spec path is unsafe or unresolved."""


def _confined_regular_file(root: Path, rel: str, *, label: str) -> Path:
    if not isinstance(rel, str) or not rel:
        raise ContextSpecInventoryError(
            f"{label} must be a non-empty repository-relative path."
        )
    if any(character in rel for character in ("\x00", "\n", "\r")):
        raise ContextSpecInventoryError(
            f"{label} must be canonical and repository-relative: {rel!r}"
        )
    rel_path = Path(rel)
    if (
        rel_path.is_absolute()
        or ".." in rel_path.parts
        or "\\" in rel
        or rel_path.as_posix() != rel
    ):
        raise ContextSpecInventoryError(
            f"{label} must be canonical and repository-relative: {rel}"
        )
    probe = root
    for part in rel_path.parts:
        probe = probe / part
        if probe.is_symlink():
            raise ContextSpecInventoryError(f"{label} traverses a symlink: {rel}")
    if not probe.is_file():
        raise ContextSpecInventoryError(
            f"{label} is missing or not a regular file: {rel}"
        )
    return probe


def claim_registry_spec_paths(root: Path) -> tuple[str, ...]:
    """Return fragment-stripped spec paths in stable first-seen order."""

    source_root = root.resolve()
    registry = _confined_regular_file(
        source_root,
        REGISTRY_PATH,
        label="Canonical claim registry",
    )
    seen: set[str] = set()
    paths: list[str] = []
    for line_number, raw in enumerate(
        registry.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ContextSpecInventoryError(
                f"Claim registry line {line_number} is invalid JSON: {exc}"
            ) from None
        if not isinstance(row, Mapping):
            raise ContextSpecInventoryError(
                f"Claim registry line {line_number} must be a JSON object."
            )
        spec_refs = row.get("spec_refs")
        evidence_refs = row.get("evidence_refs")
        if (
            spec_refs is None
            and evidence_refs is None
            and "evidence_ids" not in row
        ):
            continue
        if (
            not isinstance(spec_refs, list)
            or not spec_refs
            or any(not isinstance(ref, str) or not ref for ref in spec_refs)
            or len(spec_refs) != len(set(spec_refs))
        ):
            raise ContextSpecInventoryError(
                f"Claim registry line {line_number} spec_refs must be a non-empty "
                "list of unique strings."
            )
        for ref_index, ref in enumerate(spec_refs):
            rel = ref.split("#", 1)[0]
            _confined_regular_file(
                source_root,
                rel,
                label=(
                    f"Claim registry line {line_number} "
                    f"spec_refs[{ref_index}]"
                ),
            )
            if rel not in seen:
                seen.add(rel)
                paths.append(rel)
    return tuple(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        paths = claim_registry_spec_paths(args.root)
    except (ContextSpecInventoryError, OSError, UnicodeError) as exc:
        print(f"Context spec inventory error: {exc}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
