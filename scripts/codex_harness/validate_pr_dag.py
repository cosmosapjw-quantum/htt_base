#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DagInfo:
    prs: tuple[dict[str, Any], ...]
    ids: tuple[str, ...]
    order: tuple[str, ...]
    prereqs: dict[str, tuple[str, ...]]
    children: dict[str, tuple[str, ...]]

    @property
    def edge_count(self) -> int:
        return sum(len(deps) for deps in self.prereqs.values())


def load_yaml(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("backlog YAML must contain a mapping")
    return payload


def _duplicate_values(values: list[str]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})


def _stable_topological_order(ids: list[str], prereqs: dict[str, list[str]]) -> list[str]:
    indeg = {pr_id: 0 for pr_id in ids}
    children: dict[str, list[str]] = defaultdict(list)
    for pr_id in ids:
        for dep in prereqs[pr_id]:
            children[dep].append(pr_id)
            indeg[pr_id] += 1

    q = deque([pr_id for pr_id in ids if indeg[pr_id] == 0])
    order: list[str] = []
    while q:
        current = q.popleft()
        order.append(current)
        for child in children[current]:
            indeg[child] -= 1
            if indeg[child] == 0:
                q.append(child)

    if len(order) != len(ids):
        cycle = [pr_id for pr_id, degree in indeg.items() if degree > 0]
        raise ValueError(f"cycle detected involving: {cycle}")
    return order


def _validate_policy_order(
    policy_order: list[str],
    ids: list[str],
    prereqs: dict[str, list[str]],
) -> list[str]:
    if len(policy_order) != len(set(policy_order)):
        raise ValueError(
            f"duplicate policy.topological_order ids: {_duplicate_values(policy_order)}"
        )

    idset = set(ids)
    policy_set = set(policy_order)
    missing = sorted(idset - policy_set)
    unknown = sorted(policy_set - idset)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing ids: {missing}")
        if unknown:
            parts.append(f"unknown ids: {unknown}")
        raise ValueError("policy.topological_order coverage mismatch: " + "; ".join(parts))

    rank = {pr_id: index for index, pr_id in enumerate(policy_order)}
    violations = [
        f"{dep}->{pr_id}"
        for pr_id, deps in prereqs.items()
        for dep in deps
        if rank[dep] >= rank[pr_id]
    ]
    if violations:
        raise ValueError(
            "policy.topological_order violates dependency order: "
            + ", ".join(violations)
        )
    return policy_order


def validate_backlog(data: dict[str, Any]) -> DagInfo:
    prs_obj = data.get("prs", [])
    if not isinstance(prs_obj, list):
        raise ValueError("prs must be a list")
    prs = []
    for index, pr in enumerate(prs_obj):
        if not isinstance(pr, dict):
            raise ValueError(f"prs[{index}] must be a mapping")
        if not isinstance(pr.get("id"), str) or not pr["id"]:
            raise ValueError(f"prs[{index}] missing string id")
        depends = pr.get("depends", [])
        if depends is None:
            depends = []
        if not isinstance(depends, list) or not all(isinstance(d, str) for d in depends):
            raise ValueError(f"{pr['id']} depends must be a list of strings")
        if len(depends) != len(set(depends)):
            raise ValueError(
                f"{pr['id']} duplicate dependency ids: {_duplicate_values(depends)}"
            )
        prs.append(pr)

    ids = [pr["id"] for pr in prs]
    duplicate_ids = _duplicate_values(ids)
    if duplicate_ids:
        raise ValueError(f"duplicate PR ids: {duplicate_ids}")

    idset = set(ids)
    prereqs = {pr["id"]: list(pr.get("depends") or []) for pr in prs}
    missing_deps = sorted({dep for deps in prereqs.values() for dep in deps if dep not in idset})
    if missing_deps:
        raise ValueError(f"missing dependency ids: {missing_deps}")

    computed_order = _stable_topological_order(ids, prereqs)
    policy_raw = data.get("policy")
    if policy_raw is not None and not isinstance(policy_raw, dict):
        raise ValueError("policy must be a mapping")
    policy = policy_raw or {}
    policy_order = policy.get("topological_order")
    if policy_order is not None:
        if not isinstance(policy_order, list) or not all(
            isinstance(pr_id, str) for pr_id in policy_order
        ):
            raise ValueError("policy.topological_order must be a list of PR ids")
        order = _validate_policy_order(policy_order, ids, prereqs)
    else:
        order = computed_order

    children: dict[str, list[str]] = {pr_id: [] for pr_id in ids}
    for pr_id, deps in prereqs.items():
        for dep in deps:
            children[dep].append(pr_id)

    return DagInfo(
        prs=tuple(prs),
        ids=tuple(ids),
        order=tuple(order),
        prereqs={pr_id: tuple(deps) for pr_id, deps in prereqs.items()},
        children={pr_id: tuple(children[pr_id]) for pr_id in ids},
    )


def render_mermaid(info: DagInfo) -> str:
    titles = {pr["id"]: str(pr.get("title", "")) for pr in info.prs}
    lines = ["flowchart TD"]
    for pr_id in info.order:
        node_id = pr_id.replace("-", "_")
        title = html.escape(titles.get(pr_id, ""), quote=True)
        lines.append(f'  {node_id}["{pr_id}<br/>{title}"]')
    for pr_id in info.order:
        for dep in info.prereqs[pr_id]:
            lines.append(f"  {dep.replace('-', '_')} --> {pr_id.replace('-', '_')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backlog")
    parser.add_argument("--write-mermaid", metavar="PATH")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_yaml(args.backlog)
        info = validate_backlog(data)
        if args.write_mermaid:
            Path(args.write_mermaid).write_text(render_mermaid(info), encoding="utf-8")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "total": len(info.ids),
                    "edges": info.edge_count,
                    "topological_order": list(info.order),
                },
                indent=2,
            )
        )
    else:
        print(f"OK: {len(info.ids)} PRs, DAG valid")
        print("topological_order=" + ",".join(info.order))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
