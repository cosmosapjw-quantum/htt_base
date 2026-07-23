#!/usr/bin/env python3
"""Check major-package imports against one frozen architecture baseline.

This scanner covers production Python sources only.  Existing reverse edges and
non-trivial strongly connected components are grandfathered explicitly; their
removal is allowed, while a new forbidden edge or SCC expansion fails.
"""
from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any

PACKAGE_ROOTS: dict[str, tuple[str, ...]] = {
    "bass": ("htt/bass",),
    "common": ("htt/src/common",),
    "htt": ("htt/htt",),
    "mio": ("htt/mio",),
    "obsstat": ("htt/obsstat",),
    "tsc": ("htt/tsc", "htt/tsc_legacy", "htt/teff"),
}

IMPORT_OWNERS = {
    "bass": "bass",
    "common": "common",
    "htt": "htt",
    "mio": "mio",
    "obsstat": "obsstat",
    "teff": "tsc",
    "tsc": "tsc",
    "tsc_legacy": "tsc",
}

# Intended dependency direction from AGENTS.md.  Existing departures from this
# set are frozen below rather than rewritten in this boundary-only PR.
ALLOWED_EDGES = frozenset(
    {
        ("bass", "common"),
        ("htt", "bass"),
        ("htt", "common"),
        ("htt", "mio"),
        ("htt", "obsstat"),
        ("mio", "common"),
        ("mio", "obsstat"),
        ("obsstat", "common"),
        ("tsc", "common"),
    }
)

# Filled from the current integration branch after the first scanner run.
BASELINE_VIOLATIONS: frozenset[tuple[str, str]] = frozenset()
BASELINE_NONTRIVIAL_SCCS: tuple[frozenset[str], ...] = ()

_EXCLUDED_PARTS = frozenset(
    {
        "__pycache__",
        "build",
        "dist",
        "test",
        "tests",
    }
)


def _iter_production_sources(
    repo_root: Path,
) -> tuple[list[tuple[str, Path]], list[str]]:
    sources: list[tuple[str, Path]] = []
    missing_roots: list[str] = []
    seen_paths: set[Path] = set()

    for owner, relative_roots in PACKAGE_ROOTS.items():
        owner_found = False
        for relative_root in relative_roots:
            root = repo_root / relative_root
            if not root.is_dir():
                continue
            owner_found = True
            for path in sorted(root.rglob("*.py")):
                relative_parts = path.relative_to(root).parts
                if any(part in _EXCLUDED_PARTS for part in relative_parts):
                    continue
                if path.name.startswith("test_") or path.name.endswith("_test.py"):
                    continue
                resolved = path.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                sources.append((owner, path))
        if not owner_found:
            missing_roots.append(owner)

    return sources, missing_roots


def _import_targets(tree: ast.AST) -> Iterable[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.module or ""


def scan_repository(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    sources, missing_roots = _iter_production_sources(root)
    edge_files: dict[tuple[str, str], set[str]] = {}
    parse_errors: list[dict[str, str]] = []

    for owner, path in sources:
        relative_path = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative_path)
        except (OSError, UnicodeError, SyntaxError) as exc:
            parse_errors.append({"file": relative_path, "error": str(exc)})
            continue

        for imported_name in _import_targets(tree):
            top_level = imported_name.partition(".")[0]
            target = IMPORT_OWNERS.get(top_level)
            if target is None or target == owner:
                continue
            edge_files.setdefault((owner, target), set()).add(relative_path)

    edges = frozenset(edge_files)
    components = nontrivial_sccs(frozenset(PACKAGE_ROOTS), edges)
    return {
        "nodes": sorted(PACKAGE_ROOTS),
        "edges": [
            {
                "source": source,
                "target": target,
                "files": sorted(edge_files[(source, target)]),
            }
            for source, target in sorted(edges)
        ],
        "edge_set": edges,
        "nontrivial_sccs": components,
        "missing_roots": sorted(missing_roots),
        "parse_errors": parse_errors,
        "source_count": len(sources),
    }


def nontrivial_sccs(
    nodes: frozenset[str],
    edges: frozenset[tuple[str, str]],
) -> tuple[frozenset[str], ...]:
    adjacency = {
        node: sorted(target for source, target in edges if source == node)
        for node in nodes
    }
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[frozenset[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in adjacency[node]:
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])

        if lowlinks[node] != indices[node]:
            return
        component: set[str] = set()
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.add(member)
            if member == node:
                break
        if len(component) > 1:
            components.append(frozenset(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)

    return tuple(sorted(components, key=lambda item: tuple(sorted(item))))


def assess_edges(
    *,
    nodes: frozenset[str],
    edges: frozenset[tuple[str, str]],
    allowed_edges: frozenset[tuple[str, str]] = ALLOWED_EDGES,
    baseline_violations: frozenset[tuple[str, str]] = BASELINE_VIOLATIONS,
    baseline_sccs: tuple[frozenset[str], ...] = BASELINE_NONTRIVIAL_SCCS,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    current_violations = edges - allowed_edges
    for source, target in sorted(current_violations - baseline_violations):
        findings.append(
            {
                "kind": "new_forbidden_edge",
                "source": source,
                "target": target,
            }
        )

    for component in nontrivial_sccs(nodes, edges):
        if not any(component <= baseline for baseline in baseline_sccs):
            findings.append(
                {
                    "kind": "scc_growth",
                    "component": sorted(component),
                }
            )

    return findings


def check_repository(repo_root: Path) -> dict[str, Any]:
    report = scan_repository(repo_root)
    findings: list[dict[str, Any]] = []
    findings.extend(
        {"kind": "missing_package_root", "owner": owner}
        for owner in report["missing_roots"]
    )
    findings.extend(
        {"kind": "parse_error", **error}
        for error in report["parse_errors"]
    )
    findings.extend(
        assess_edges(
            nodes=frozenset(report["nodes"]),
            edges=report["edge_set"],
        )
    )
    return {
        "status": "PASS" if not findings else "FAIL",
        "source_count": report["source_count"],
        "edges": report["edges"],
        "nontrivial_sccs": [
            sorted(component) for component in report["nontrivial_sccs"]
        ],
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()

    result = check_repository(args.repo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
