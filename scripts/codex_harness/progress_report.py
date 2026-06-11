#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from validate_pr_dag import DagInfo, load_yaml, validate_backlog


def _as_id_list(status: dict[str, Any], key: str) -> list[str]:
    value = status.get(key, []) or []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"status {key} must be a list of PR ids")
    duplicate = sorted({item for item in value if value.count(item) > 1})
    if duplicate:
        raise ValueError(f"duplicate {key} PR ids: {duplicate}")
    return value


def load_status(path: str | Path) -> dict[str, Any]:
    status_path = Path(path)
    if not status_path.exists():
        return {}
    status = yaml.safe_load(status_path.read_text(encoding="utf-8")) or {}
    if not isinstance(status, dict):
        raise ValueError("status YAML must contain a mapping")
    return status


def validate_status(status: dict[str, Any], info: DagInfo) -> tuple[set[str], set[str]]:
    completed_list = _as_id_list(status, "completed")
    blocked_list = _as_id_list(status, "blocked")
    idset = set(info.ids)

    unknown_completed = sorted(set(completed_list) - idset)
    if unknown_completed:
        raise ValueError(f"unknown completed PR ids: {unknown_completed}")

    unknown_blocked = sorted(set(blocked_list) - idset)
    if unknown_blocked:
        raise ValueError(f"unknown blocked PR ids: {unknown_blocked}")

    completed = set(completed_list)
    blocked = set(blocked_list)
    overlap = sorted(completed & blocked)
    if overlap:
        raise ValueError(f"PR ids cannot be both completed and blocked: {overlap}")

    incomplete_dependencies = [
        f"{dep}->{pr_id}"
        for pr_id in info.order
        if pr_id in completed
        for dep in info.prereqs[pr_id]
        if dep not in completed
    ]
    if incomplete_dependencies:
        raise ValueError(
            "completed PRs have incomplete dependencies: "
            + ", ".join(incomplete_dependencies)
        )

    in_progress = status.get("in_progress")
    if in_progress is not None:
        if not isinstance(in_progress, str):
            raise ValueError("status in_progress must be a PR id or null")
        if in_progress not in idset:
            raise ValueError(f"unknown in_progress PR id: {in_progress}")
        if in_progress in completed or in_progress in blocked:
            raise ValueError(
                f"in_progress PR id cannot be completed or blocked: {in_progress}"
            )

    return completed, blocked


def longest_critical_path(info: DagInfo) -> list[str]:
    if not info.ids:
        return []

    rank = {pr_id: index for index, pr_id in enumerate(info.order)}
    best_path: dict[str, list[str]] = {}
    for pr_id in info.order:
        dep_paths = [best_path[dep] for dep in info.prereqs[pr_id]]
        if dep_paths:
            dep_paths.sort(key=lambda path: (-len(path), [rank[item] for item in path]))
            path = [*dep_paths[0], pr_id]
        else:
            path = [pr_id]
        best_path[pr_id] = path

    return sorted(
        best_path.values(),
        key=lambda path: (-len(path), [rank[item] for item in path]),
    )[0]


def dependency_weighted_percent(info: DagInfo, completed: set[str]) -> float:
    weights = {pr_id: 1 + len(info.children[pr_id]) for pr_id in info.ids}
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    completed_weight = sum(weight for pr_id, weight in weights.items() if pr_id in completed)
    return round(100 * completed_weight / total_weight, 2)


def build_report(info: DagInfo, completed: set[str], blocked: set[str], checkpoint_every: int) -> dict[str, Any]:
    if checkpoint_every <= 0:
        raise ValueError("--checkpoint-every must be positive")

    unblocked = [
        pr_id
        for pr_id in info.order
        if pr_id not in completed
        and pr_id not in blocked
        and all(dep in completed for dep in info.prereqs[pr_id])
    ]
    critical_path = longest_critical_path(info)
    critical_done = sum(1 for pr_id in critical_path if pr_id in completed)
    next_checkpoint = ((len(completed) // checkpoint_every) + 1) * checkpoint_every

    return {
        "total": len(info.ids),
        "completed": len(completed),
        "blocked": [pr_id for pr_id in info.order if pr_id in blocked],
        "percent_complete": round(100 * len(completed) / len(info.ids), 2) if info.ids else 0.0,
        "dependency_weighted_percent_complete": dependency_weighted_percent(info, completed),
        "critical_path": critical_path,
        "critical_path_completed": critical_done,
        "critical_path_total": len(critical_path),
        "critical_path_percent_complete": round(100 * critical_done / len(critical_path), 2)
        if critical_path
        else 0.0,
        "unblocked_next": unblocked[:10],
        "next_checkpoint_at": next_checkpoint,
        "checkpoint_due": len(completed) > 0 and len(completed) % checkpoint_every == 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backlog")
    parser.add_argument("status")
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        info = validate_backlog(load_yaml(args.backlog))
        completed, blocked = validate_status(load_status(args.status), info)
        report = build_report(info, completed, blocked, args.checkpoint_every)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"Completed {report['completed']}/{report['total']} = "
            f"{report['percent_complete']}%"
        )
        print(
            "Dependency-weighted completion:",
            f"{report['dependency_weighted_percent_complete']}%",
        )
        print(
            "Critical path:",
            " -> ".join(report["critical_path"]),
            f"({report['critical_path_percent_complete']}%)",
        )
        print("Unblocked next:", ", ".join(report["unblocked_next"]) or "none")
        print("Checkpoint due:", report["checkpoint_due"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
