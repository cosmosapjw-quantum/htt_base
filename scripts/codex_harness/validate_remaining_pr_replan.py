#!/usr/bin/env python3
"""Validate the current-code remaining-PR reconciliation artifacts."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import yaml

if __package__:
    from .validate_pr_dag import render_mermaid, validate_backlog
else:
    from validate_pr_dag import render_mermaid, validate_backlog


REPO = Path(__file__).resolve().parents[2]
BACKLOG = REPO / "docs/codex_handoff/pr_backlog.yaml"
STATUS = REPO / "docs/codex_handoff/pr_status.yaml"
CROSSWALK = REPO / "docs/codex_handoff/remaining_pr_crosswalk.csv"
PLAN = REPO / "docs/codex_handoff/REMAINING_PR_EXECUTION_PLAN_KO.md"
MERMAID = REPO / "docs/codex_handoff/pr_dag.mmd"

# Historical non-completed IDs, read from this exact commit's status blob.
# Keep this record independent of the live crosswalk and current card states:
# completion must not permit replacing a historical baseline member.
# No Git history or network is required by the production validator.
FROZEN_BASELINE = {
    "commit": "85e261f49c9df9389946eef74d80c1ccd0509816",
    "status_path": "docs/codex_handoff/pr_status.yaml",
    "status_blob": "4ee78066941f86690b0b6044c9ffd4574fd4a2fc",
    "ids": (
        "PR-151", "PR-155", "PR-156", "PR-157", "PR-158", "PR-159",
        "PR-160", "PR-161", "PR-162", "PR-163", "PR-164", "PR-165",
        "PR-166", "PR-172", "PR-178", "PR-181", "PR-183", "PR-190",
        "PR-191", "PR-192", "PR-193", "PR-194", "PR-195", "PR-196",
        "PR-198", "PR-199", "PR-201", "PR-202", "PR-203", "PR-204",
        "PR-205", "PR-206", "PR-207", "PR-208", "PR-229", "PR-230",
        "PR-231", "PR-232", "PR-233", "PR-234", "PR-235", "PR-236",
        "PR-237", "PR-238", "PR-239", "PR-240", "PR-241", "PR-242",
        "PR-243", "PR-244", "PR-245", "PR-246", "PR-247",
        "PR-MES-R7-SOURCE-IMAGE", "PR-R9-DEPTH-MATHLIB",
    ),
}

ALLOWED_DISPOSITIONS = {
    "IMPLEMENTED_REUSE",
    "PARTIAL_REMAINDER",
    "UNIMPLEMENTED",
    "EXECUTED_FAILED_OR_HELD",
    "EXTERNAL_INPUT_OR_SOLVER",
    "SUPERSEDED_OR_DUPLICATE",
}
REQUIRED_FAMILIES = {
    "docs/codex_handoff/pr_dag_revision.yaml",
    "docs/codex_handoff/pr_dag_research_program.yaml",
    "docs/NON_BASS_COMPLETENESS_WBS_2026-04-20.md",
    "docs/research_program/pr07/pr_registry.yaml",
    "docs/research_program/HTT_VECTOR_TENSOR_MES_TWO_PILLAR_UPGRADE_PLAN_20260730.md",
    "docs/codex_handoff/htt_tensorized_report_first_20260903/THEORY_ONLY_DAG_STATUS_OVERLAY_V29.yaml",
    "docs/research_program/referee_seeded_20260907/03_PROGRAM_DAG.yaml",
    "HTT_PR328_LOCAL_CODEX_HANDOFF_20260831/RUN_PLAN.yaml",
    "docs/DEVELOPMENT_PLAN.md",
    "external_fusion_round3/PR_GATE_MATRIX.json",
    "docs/research_program/tensor_joint_r9/campaign_dag.json",
}
LOCAL_ONLY_PLANNING_SOURCES = {
    "HTT_PR328_LOCAL_CODEX_HANDOFF_20260831/RUN_PLAN.yaml",
}
REQUIRED_PLAN_MARKERS = {
    "85e261f49c9df9389946eef74d80c1ccd0509816",
    "R9-D2-D4-REMAINING-FORMALIZATION-20260922",
    "EXISTING_CHILD_NOT_CLOSED",
    "2,000,000",
    "730,883",
    "HOLD_NOT_COMPUTED",
    "PR-151",
    "EF3:247",
    "새 worktree나 clone을 만들지 않는다",
}


def _load_yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO)} must contain a mapping")
    return payload


def _status_map(status: dict[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in (
        "completed",
        "blocked",
        "pending",
        "dormant_external",
        "background_in_progress",
    ):
        values = status.get(key, [])
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError(f"status.{key} must be a string list")
        for pr_id in values:
            if pr_id in result:
                raise ValueError(f"status duplicates card {pr_id}")
            result[pr_id] = key
    in_progress = status.get("in_progress")
    if in_progress is not None:
        if not isinstance(in_progress, str):
            raise ValueError("status.in_progress must be null or a card id")
        if in_progress in result:
            raise ValueError(f"status duplicates card {in_progress}")
        result[in_progress] = "in_progress"
    return result


def validate() -> dict[str, int]:
    backlog = _load_yaml(BACKLOG)
    info = validate_backlog(backlog)
    status = _load_yaml(STATUS)
    states = _status_map(status)
    backlog_ids = set(info.ids)
    if set(states) != backlog_ids:
        raise ValueError(
            "status coverage mismatch: "
            f"missing={sorted(backlog_ids - set(states))}, "
            f"unknown={sorted(set(states) - backlog_ids)}"
        )

    noncompleted = {pr_id: state for pr_id, state in states.items() if state != "completed"}

    with CROSSWALK.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    canonical_rows = [row for row in rows if row.get("record_type") == "canonical_card"]
    family_rows = [row for row in rows if row.get("record_type") == "planning_family"]
    row_ids = [row.get("original_id", "") for row in canonical_rows]
    if len(row_ids) != len(set(row_ids)):
        raise ValueError("crosswalk contains duplicate canonical card rows")
    baseline_ids = set(row_ids)
    expected_baseline_ids = set(FROZEN_BASELINE["ids"])
    if baseline_ids != expected_baseline_ids:
        raise ValueError(
            f"frozen baseline identity mismatch ({FROZEN_BASELINE['commit']}): "
            f"missing={sorted(expected_baseline_ids - baseline_ids)}, "
            f"extra={sorted(baseline_ids - expected_baseline_ids)}"
        )
    if not set(noncompleted).issubset(baseline_ids):
        raise ValueError(
            "current non-completed card is absent from the baseline crosswalk: "
            f"missing={sorted(set(noncompleted) - baseline_ids)}"
        )
    for row in canonical_rows:
        pr_id = row["original_id"]
        if pr_id not in states:
            raise ValueError(f"crosswalk references missing canonical card {pr_id}")
        if row.get("canonical_status") != states[pr_id]:
            raise ValueError(
                f"{pr_id} crosswalk status {row.get('canonical_status')!r} "
                f"does not match {states[pr_id]!r}"
            )
        if row.get("disposition") not in ALLOWED_DISPOSITIONS:
            raise ValueError(f"{pr_id} has invalid disposition {row.get('disposition')!r}")
        for field in (
            "source_path",
            "current_evidence",
            "remaining_requirement",
            "successor_nodes",
            "activation_condition",
            "claim_boundary",
        ):
            if not row.get(field, "").strip():
                raise ValueError(f"{pr_id} has empty {field}")
        for successor in row["successor_nodes"].split("|"):
            if successor not in backlog_ids:
                raise ValueError(f"{pr_id} references unknown successor {successor}")

    family_keys = [row.get("source_path", "") for row in family_rows]
    family_paths = set(family_keys)
    if len(family_keys) != len(family_paths):
        raise ValueError("crosswalk contains duplicate planning-family source_path rows")
    if family_paths != REQUIRED_FAMILIES:
        raise ValueError(
            "planning-family coverage mismatch: "
            f"missing={sorted(REQUIRED_FAMILIES - family_paths)}, "
            f"extra={sorted(family_paths - REQUIRED_FAMILIES)}"
        )
    for row in family_rows:
        source = REPO / row["source_path"]
        if not source.is_file() and row["source_path"] not in LOCAL_ONLY_PLANNING_SOURCES:
            raise ValueError(f"planning source does not exist: {row['source_path']}")
        if row.get("disposition") not in ALLOWED_DISPOSITIONS:
            raise ValueError(f"planning family has invalid disposition: {row['source_path']}")
        for successor in row["successor_nodes"].split("|"):
            if successor not in backlog_ids:
                raise ValueError(
                    f"planning family {row['source_path']} references unknown successor {successor}"
                )

    plan_text = PLAN.read_text(encoding="utf-8")
    missing_markers = sorted(marker for marker in REQUIRED_PLAN_MARKERS if marker not in plan_text)
    if missing_markers:
        raise ValueError(f"execution plan is missing markers: {missing_markers}")

    canonical_json = json.loads(
        (REPO / "docs/codex_handoff/pr_backlog.json").read_text(encoding="utf-8")
    )
    machine_json = json.loads(
        (REPO / "machine_readable/pr_backlog.json").read_text(encoding="utf-8")
    )
    if canonical_json != backlog or machine_json != backlog:
        raise ValueError("backlog JSON mirrors do not match canonical YAML")
    if BACKLOG.read_bytes() != (REPO / "machine_readable/pr_backlog.yaml").read_bytes():
        raise ValueError("backlog YAML mirror differs")
    if STATUS.read_bytes() != (REPO / "machine_readable/pr_status.yaml").read_bytes():
        raise ValueError("status YAML mirror differs")
    if MERMAID.read_text(encoding="utf-8") != render_mermaid(info):
        raise ValueError("Mermaid DAG does not match canonical backlog")

    extensions = backlog.get("policy", {}).get("strict_extension_cards", [])
    if not isinstance(extensions, list) or set(extensions) - backlog_ids:
        raise ValueError("strict extension registry is invalid")

    return {
        "cards": len(backlog_ids),
        "current_noncompleted": len(noncompleted),
        "baseline_crosswalk_cards": len(canonical_rows),
        "canonical_crosswalk_rows": len(canonical_rows),
        "planning_families": len(family_rows),
        "extensions": len(extensions),
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError, KeyError, csv.Error, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"status": "PASS", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
