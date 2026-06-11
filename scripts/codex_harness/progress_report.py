#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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

    checkpoint_due = len(completed) > 0 and len(completed) % checkpoint_every == 0
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
        "current_checkpoint_at": len(completed) if checkpoint_due else None,
        "next_checkpoint_at": next_checkpoint,
        "checkpoint_due": checkpoint_due,
        "checkpoint_artifact": None,
        "previous_checkpoint_completed": None,
        "progress_delta_completed": None,
        "replan_required": False,
        "replan_reason": "checkpoint not due",
    }


def _checkpoint_metadata(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    if not first_line:
        return None
    match = re.match(r"<!-- checkpoint_meta (.*?) -->", first_line[0])
    if not match:
        return None
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(metadata, dict):
        return None
    return metadata


def _latest_checkpoint_metadata(checkpoint_dir: Path, current_completed: int) -> dict[str, Any] | None:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for path in checkpoint_dir.glob("checkpoint_*.md"):
        match = re.fullmatch(r"checkpoint_(\d+)\.md", path.name)
        if not match:
            continue
        checkpoint_number = int(match.group(1))
        if checkpoint_number >= current_completed:
            continue
        metadata = _checkpoint_metadata(path)
        if metadata is None:
            raise ValueError(f"malformed checkpoint metadata: {path}")
        candidates.append((checkpoint_number, metadata))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def _checkpoint_state(report: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    previous_completed = int(previous.get("completed", -1)) if previous else -1
    previous_percent = float(previous.get("percent_complete", -1.0)) if previous else -1.0
    progress_stalled = (
        previous is not None
        and report["completed"] <= previous_completed
        and report["percent_complete"] <= previous_percent
    )
    replan_required = progress_stalled
    replan_reason = (
        "progress did not advance since the previous checkpoint"
        if progress_stalled
        else "progress advanced; no replan required"
    )
    return {
        "previous_checkpoint_completed": previous_completed if previous else None,
        "progress_delta_completed": report["completed"] - previous_completed
        if previous
        else None,
        "replan_required": progress_stalled,
        "replan_reason": replan_reason,
    }


def _checkpoint_markdown(report: dict[str, Any], state: dict[str, Any]) -> str:
    metadata = {
        "completed": report["completed"],
        "total": report["total"],
        "percent_complete": report["percent_complete"],
        "dependency_weighted_percent_complete": report["dependency_weighted_percent_complete"],
        "critical_path_percent_complete": report["critical_path_percent_complete"],
        "replan_required": state["replan_required"],
    }
    blocked = ", ".join(report["blocked"]) or "none"
    unblocked_next = ", ".join(report["unblocked_next"]) or "none"
    critical_path = " -> ".join(report["critical_path"]) or "none"
    replan_text = "yes" if state["replan_required"] else "no"
    lines = [
        f"<!-- checkpoint_meta {json.dumps(metadata, sort_keys=True)} -->",
        f"# Progress checkpoint {report['completed']:03d}",
        "",
        f"- Completed PRs: {report['completed']}/{report['total']} = {report['percent_complete']}%",
        f"- Dependency-weighted completion: {report['dependency_weighted_percent_complete']}%",
        (
            f"- Critical path completion: {report['critical_path_completed']}/"
            f"{report['critical_path_total']} = {report['critical_path_percent_complete']}%"
        ),
        f"- Critical path: {critical_path}",
        f"- Blocked PRs: {blocked}",
        f"- Unblocked next: {unblocked_next}",
        f"- Replan required: {replan_text}",
        f"- Replan reason: {state['replan_reason']}",
        "",
        "Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.",
        "They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.",
    ]
    if state["replan_required"]:
        lines.extend(
            [
                "",
                "## Adversarial replan entry",
                "",
                "- Step-back: the same completed count and percent recurred at a checkpoint.",
                "- Required action: open a small replan PR before further feature work.",
            ]
        )
    return "\n".join(lines) + "\n"


def write_checkpoint(report: dict[str, Any], checkpoint_dir: str | Path) -> Path | None:
    if not report["checkpoint_due"]:
        return None
    output_dir = Path(checkpoint_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    previous = _latest_checkpoint_metadata(output_dir, report["completed"])
    state = _checkpoint_state(report, previous)
    report.update(state)
    checkpoint_path = output_dir / f"checkpoint_{report['completed']:03d}.md"
    checkpoint_path.write_text(_checkpoint_markdown(report, state), encoding="utf-8")
    report["checkpoint_artifact"] = str(checkpoint_path)
    return checkpoint_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backlog")
    parser.add_argument("status")
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--write-checkpoint-dir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        info = validate_backlog(load_yaml(args.backlog))
        completed, blocked = validate_status(load_status(args.status), info)
        report = build_report(info, completed, blocked, args.checkpoint_every)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    checkpoint_path = None
    if args.write_checkpoint_dir:
        try:
            checkpoint_path = write_checkpoint(report, args.write_checkpoint_dir)
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
        if checkpoint_path is not None:
            print(f"Checkpoint artifact: {checkpoint_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
