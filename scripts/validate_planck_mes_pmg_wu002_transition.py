#!/usr/bin/env python3
"""Validate the PMG-WU-002 execution-transition package and candidate scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_REL = Path(
    "docs/codex_handoff/planck_mes_pmg_wu002_execution_transition"
)
PACKAGE_ID = "PLANCK_MES_PMG_WU002_EXECUTION_TRANSITION_20260827"
HOST_BRANCH = "changeset/planck-mes-observable-irrep-state-20260827"
WU001_SHA = "47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0"
WU001_TREE = "8abbe9040cb72357387ec3c29f0e1e74921af0ea"
WU001_TERMINAL = Path(
    "docs/generated/planck_mes_irrep_formalism/wu001_terminal.json"
)
EXPECTED_FILES = {
    "PACKAGE_INDEX.yaml",
    "AUTHORITY_AND_SCOPE.yaml",
    "PR419_ACCEPTANCE_BINDING.yaml",
    "VALIDATOR_TRANSITION_CONTRACT.yaml",
    "PMG_WU002_EXECUTION_CONTRACT.yaml",
    "P0_P1_THREAT_CATALOG.json",
    "INVARIANT_TEST_MATRIX.yaml",
    "GUIDE_BINDING.yaml",
    "CODEX_HANDOFF.md",
    "CODEX_HANDOFF_PROMPT.md",
}
VALIDATION_FILES = {
    "scripts/validate_planck_mes_pmg_wu002_transition.py",
    "tests/contracts/test_planck_mes_pmg_wu002_transition.py",
}
ALLOWED_WU002_PATHS = {
    "htt/src/common/mes_premise_normalization.py",
    "htt/src/common/response_bound_observable_state.py",
    "htt/src/common/joint_anisotropy_state.py",
    "htt/src/common/mes_directional_state.py",
    "htt/obsstat/mes_directional_moments.py",
    "htt/src/common/orbit_catalogue_v3.py",
    "tests/contracts/test_global_formalism_boundaries.py",
    "tests/contracts/test_mes_premise_normalization.py",
    "tests/contracts/test_response_bound_observable_state.py",
    "tests/architecture/test_import_boundaries.py",
    "docs/generated/planck_mes_irrep_formalism/wu002_terminal.json",
    "docs/generated/planck_mes_irrep_formalism/migration_status.json",
}
OBJECTIVE_PATHS = {
    "docs/generated/planck_mes_irrep_formalism/wu002_terminal.json",
    "docs/generated/planck_mes_irrep_formalism/migration_status.json",
}
PRODUCTION_PREFIXES = ("htt/src/common/", "htt/obsstat/")
TEST_PREFIXES = ("tests/contracts/", "tests/architecture/")
PLACEHOLDERS = (
    "<accepted-wu001-base>",
    "<REPO_URL_OR_PATH>",
    "<USER_OBJECTIVE>",
    "TBD",
    "TODO",
)


class TransitionValidationError(RuntimeError):
    """Raised when the transition package or candidate diff is invalid."""


def fail(message: str) -> None:
    raise TransitionValidationError(message)


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        fail(f"invalid YAML {path}: {exc}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {path}: {exc}")


def mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        fail(f"{name} must be a mapping")
    return value


def sequence(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        fail(f"{name} must be a sequence")
    return value


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_package(
    root: Path = ROOT,
    *,
    package: Path | None = None,
    check_git: bool = False,
) -> dict[str, object]:
    root = Path(root)
    package = Path(package) if package is not None else root / PACKAGE_REL
    if not package.is_dir():
        fail(f"package directory missing: {package}")

    actual = {path.name for path in package.iterdir() if path.is_file()}
    if actual != EXPECTED_FILES:
        fail(
            "package file set drifted: "
            f"missing={sorted(EXPECTED_FILES-actual)} "
            f"extra={sorted(actual-EXPECTED_FILES)}"
        )

    index = mapping(load_yaml(package / "PACKAGE_INDEX.yaml"), "package index")
    if (
        index.get("schema")
        != "htt.planck_mes_pmg_wu002_transition.package_index.v1"
        or index.get("package_id") != PACKAGE_ID
        or index.get("mode")
        != "EXECUTION_TRANSITION_PACKAGE_NOT_WU002_IMPLEMENTATION"
        or index.get("host_branch") != HOST_BRANCH
        or index.get("active_work_unit") != "PMG-WU-002"
    ):
        fail("package identity drifted")
    if set(index.get("files", [])) != EXPECTED_FILES:
        fail("PACKAGE_INDEX file list drifted")
    if set(index.get("validation_files", [])) != VALIDATION_FILES:
        fail("PACKAGE_INDEX validation files drifted")
    source = mapping(index.get("wu001_implementation_source"), "WU-001 source")
    if source.get("commit") != WU001_SHA or source.get("tree") != WU001_TREE:
        fail("WU-001 implementation authority drifted")
    if (
        index.get("science_code_changed_by_this_package") is not False
        or index.get("science_execution_performed_by_this_package") is not False
        or index.get("raw_data_read_or_mutated") is not False
        or index.get("successor_planning_package") is not False
    ):
        fail("package role flags drifted")

    authority = mapping(
        load_yaml(package / "AUTHORITY_AND_SCOPE.yaml"), "authority"
    )
    wu001 = mapping(authority.get("wu001_source"), "authority WU-001 source")
    if (
        wu001.get("branch") != HOST_BRANCH
        or wu001.get("implementation_commit") != WU001_SHA
        or wu001.get("implementation_tree") != WU001_TREE
        or wu001.get("terminal_state") != "SUCCEEDED"
        or wu001.get("terminal_next_action") != "PMG-WU-002"
    ):
        fail("authority WU-001 binding drifted")
    forbidden_text = "\n".join(authority.get("forbidden_scope", []))
    for required in ("Planck map reads", "raw data mutation", "successor planning"):
        if required not in forbidden_text:
            fail(f"authority forbidden scope lacks {required}")

    pr_binding = mapping(
        load_yaml(package / "PR419_ACCEPTANCE_BINDING.yaml"), "PR binding"
    )
    pull_request = mapping(pr_binding.get("pull_request"), "pull request")
    if (
        pull_request.get("number") != 419
        or pull_request.get("head_branch") != HOST_BRANCH
        or pull_request.get("wu001_implementation_commit") != WU001_SHA
        or pull_request.get("wu001_implementation_tree") != WU001_TREE
    ):
        fail("PR #419 binding drifted")
    acceptance = mapping(pr_binding.get("acceptance_state"), "acceptance state")
    if (
        acceptance.get("human_merge_or_acceptance") != "PENDING"
        or "BLOCKED_UNTIL" not in str(
            acceptance.get("wu002_implementation_permission", "")
        )
        or acceptance.get("package_push_permission") != "ALLOWED"
    ):
        fail("PR acceptance/implementation distinction drifted")

    validator_contract = mapping(
        load_yaml(package / "VALIDATOR_TRANSITION_CONTRACT.yaml"),
        "validator contract",
    )
    candidate = mapping(
        validator_contract.get("candidate_diff_contract"),
        "candidate diff contract",
    )
    if set(candidate.get("allowed_paths", [])) != ALLOWED_WU002_PATHS:
        fail("candidate allowed paths drifted")
    if set(candidate.get("required_objective_paths", [])) != OBJECTIVE_PATHS:
        fail("candidate objective paths drifted")

    work_unit = mapping(
        load_yaml(package / "PMG_WU002_EXECUTION_CONTRACT.yaml"),
        "work unit",
    )
    required_wu_keys = {
        "schema",
        "id",
        "title",
        "authority",
        "objective",
        "risk",
        "scope",
        "preconditions",
        "invariants",
        "failure_modes",
        "implementation",
        "verification",
        "completion_evidence",
        "agent_policy",
        "review_gate",
        "transition",
    }
    if set(work_unit) != required_wu_keys:
        fail("work-unit key set drifted")
    if (
        work_unit.get("schema") != "audit-compiled-work-unit/v1"
        or work_unit.get("id") != "PMG-WU-002"
    ):
        fail("work-unit identity drifted")
    scope = mapping(work_unit.get("scope"), "work-unit scope")
    if set(scope.get("allowed_paths", [])) != ALLOWED_WU002_PATHS:
        fail("work-unit allowed paths drifted")
    if "docs/codex_handoff/**" not in set(scope.get("forbidden_paths", [])):
        fail("successor-package prohibition missing")
    transition = mapping(work_unit.get("transition"), "work-unit transition")
    if "PMG-WU-003" not in str(transition.get("pass_next_executable_action", "")):
        fail("positive PASS transition drifted")
    review = mapping(work_unit.get("review_gate"), "review gate")
    if (
        review.get("read_only_first_pass") is not True
        or review.get("pass_condition") != {"P0": 0, "P1": 0}
        or "at most one targeted repair" not in str(review.get("stopping_rule", ""))
    ):
        fail("review gate drifted")

    catalog = mapping(
        load_json(package / "P0_P1_THREAT_CATALOG.json"), "threat catalog"
    )
    threats = sequence(catalog.get("failure_modes"), "failure modes")
    threat_ids = {row.get("id") for row in threats if isinstance(row, Mapping)}
    if threat_ids != {f"PMG2-FM-{index:03d}" for index in range(1, 9)}:
        fail("failure-mode coverage drifted")
    if any(
        row.get("severity") not in {"P0", "P1"}
        or not str(row.get("detector", "")).strip()
        for row in threats
        if isinstance(row, Mapping)
    ):
        fail("failure-mode detector or severity is invalid")

    matrix_doc = mapping(
        load_yaml(package / "INVARIANT_TEST_MATRIX.yaml"), "matrix"
    )
    rows = sequence(matrix_doc.get("rows"), "matrix rows")
    if {row.get("failure_mode") for row in rows if isinstance(row, Mapping)} != threat_ids:
        fail("threat/matrix coverage drifted")
    for row in rows:
        if (
            not str(row.get("mechanical_detector", "")).strip()
            or row.get("work_unit") != "PMG-WU-002"
            or "PMG-WU-003" not in str(row.get("pass_transition", ""))
        ):
            fail(f"incomplete matrix row: {row.get('failure_mode')}")

    guides = mapping(load_yaml(package / "GUIDE_BINDING.yaml"), "guide binding")
    titles = {
        row.get("title")
        for row in sequence(guides.get("guides"), "guide rows")
        if isinstance(row, Mapping)
    }
    required_titles = {
        "Universal Audit-Compiled Execution Plan / Weak-Agent-Safe Implementation Compiler",
        "Universal Execution-Transition and Anti-Bureaucracy Directive",
        "Adaptive CMB Code Development Protocol",
        "Adaptive CMB Code Research Executor",
    }
    if titles != required_titles:
        fail("guide binding coverage drifted")

    for name in ("CODEX_HANDOFF.md", "CODEX_HANDOFF_PROMPT.md"):
        text = (package / name).read_text(encoding="utf-8")
        for required in (
            "PMG-WU-002",
            "47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0",
            "analysis/planck-mes-pmg-wu002-transition-20260827",
            "PMG-WU-003",
        ):
            if required not in text:
                fail(f"{name} lacks required instruction: {required}")
        for placeholder in PLACEHOLDERS[1:]:
            if placeholder in text:
                fail(f"{name} contains placeholder: {placeholder}")

    terminal_path = root / WU001_TERMINAL
    if terminal_path.exists():
        terminal = mapping(load_json(terminal_path), "WU-001 terminal")
        required_terminal = {
            "schema": "htt.planck_mes_irrep_formalism.work_unit_terminal.v1",
            "work_unit": "PMG-WU-001",
            "state": "SUCCEEDED",
            "next_executable_action": "PMG-WU-002",
            "claim_promotion": False,
            "raw_data_read_or_mutated": False,
            "replay_status": "MATCH_FROZEN_BASELINE",
        }
        for key, expected in required_terminal.items():
            if terminal.get(key) != expected:
                fail(f"WU-001 terminal field drifted: {key}")

    if check_git:
        run_git(root, "cat-file", "-e", f"{WU001_SHA}^{{commit}}")
        if run_git(root, "rev-parse", f"{WU001_SHA}^{{tree}}") != WU001_TREE:
            fail("WU-001 tree identity drifted")
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", WU001_SHA, "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            fail("current HEAD is not descended from exact WU-001 source")

    return {
        "schema": "htt.planck_mes_pmg_wu002_transition.validation.v1",
        "status": "PASS",
        "package_id": PACKAGE_ID,
        "active_work_unit": "PMG-WU-002",
        "wu001_source": WU001_SHA,
        "failure_modes": len(threat_ids),
        "P0": sum(
            row.get("severity") == "P0" for row in threats if isinstance(row, Mapping)
        ),
        "P1": sum(
            row.get("severity") == "P1" for row in threats if isinstance(row, Mapping)
        ),
        "science_executed": False,
    }


def validate_changed_paths(paths: Sequence[str]) -> dict[str, object]:
    normalized = {path.strip() for path in paths if path.strip()}
    if not normalized:
        fail("candidate changed-path list is empty")
    unknown = normalized - ALLOWED_WU002_PATHS
    if unknown:
        fail(f"candidate contains undeclared paths: {sorted(unknown)}")
    if any(
        path.startswith(("docs/codex_handoff/", "/mnt/", "raw/", "downloads/"))
        for path in normalized
    ):
        fail("candidate contains process-package or raw-data paths")
    if not any(path.startswith(PRODUCTION_PREFIXES) for path in normalized):
        fail("candidate has no production implementation path")
    if not any(path.startswith(TEST_PREFIXES) for path in normalized):
        fail("candidate has no focused test path")
    missing_outputs = OBJECTIVE_PATHS - normalized
    if missing_outputs:
        fail(f"candidate lacks required objective outputs: {sorted(missing_outputs)}")
    return {
        "schema": "htt.planck_mes_pmg_wu002_transition.changed_paths.v1",
        "status": "PASS",
        "work_unit": "PMG-WU-002",
        "paths": sorted(normalized),
        "production_present": True,
        "tests_present": True,
        "objective_outputs_present": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-git", action="store_true")
    parser.add_argument(
        "--changed-paths",
        metavar="PATH_OR_DASH",
        help="validate newline-delimited PMG-WU-002 changed paths; '-' reads stdin",
    )
    args = parser.parse_args()
    try:
        if args.changed_paths is not None:
            if args.changed_paths == "-":
                paths = sys.stdin.read().splitlines()
            else:
                paths = Path(args.changed_paths).read_text(encoding="utf-8").splitlines()
            result = validate_changed_paths(paths)
        else:
            result = validate_package(check_git=args.check_git)
    except TransitionValidationError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
