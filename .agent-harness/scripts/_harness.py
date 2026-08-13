from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from publication_integrity import (
    PublicationIntegrityError,
    bytes_sha256,
    canonical_target_ref,
    git,
    load_publication_policy,
    mutable_candidate_binding,
    reject_duplicate_stable_patch_ids,
    require_change_set_id,
    require_publication_group_id,
    validate_candidate_binding,
    validate_declared_policy_identity,
)


SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_IDENTITY_RE = re.compile(r"[^\x00-\x1f\x7f]{1,512}")
RISK_TIERS = {"R0", "R1", "R2", "R3"}
CAS_AXES = {"wolfram_xact", "sympy", "sage_singular", "lean"}
ACTIVE_RUN_RELATIVE_PATH = Path(".agent-harness/runtime/ACTIVE_RUN")
LEGACY_ACTIVE_RUN_RELATIVE_PATH = Path(".agent-harness/ACTIVE_RUN")
DEFAULT_MAX_TOTAL_PER_WORK_UNIT = 16
MAX_REVIEW_REREVIEW_EXCEPTION_ASSIGNMENTS = 2
FIRST_REAUTHORIZED_REVIEW_REREVIEW_CUMULATIVE_START = (
    DEFAULT_MAX_TOTAL_PER_WORK_UNIT
    + MAX_REVIEW_REREVIEW_EXCEPTION_ASSIGNMENTS
)
EXECUTION_MODES = {"MANUAL_PR", "AUTO_STACKED_PR", "AUTO_MERGE"}
LIFECYCLE_STATES = (
    "PLANNED",
    "ACTIVE",
    "IMPLEMENTED",
    "VALIDATED",
    "REVIEWED",
    "SEALED",
    "PUSHED",
    "PR_OPEN",
)
GATE_DISPOSITIONS = {
    "PASS",
    "FAIL",
    "INCONCLUSIVE",
    "INELIGIBLE",
    "DEFERRED",
}


class ActiveRunError(RuntimeError):
    """Structured failure while resolving local run state."""

    def __init__(
        self,
        error_code: str,
        message: str,
        **details: str,
    ) -> None:
        super().__init__(f"{error_code}: {message}")
        self.error_code = error_code
        self.message = message
        self.details = details

    def as_dict(self) -> dict[str, str]:
        return {"code": self.error_code, "message": self.message, **self.details}


def validate_execution_mode(mode: object) -> str:
    """Recognize all declared modes while refusing automatic merge authority."""

    if mode not in EXECUTION_MODES:
        raise PublicationIntegrityError(
            "execution_mode must be MANUAL_PR, AUTO_STACKED_PR, or AUTO_MERGE"
        )
    assert isinstance(mode, str)
    if mode == "AUTO_MERGE":
        raise PublicationIntegrityError(
            "AUTO_MERGE is recognized but refused; merge remains HUMAN ONLY"
        )
    return mode


def validate_lifecycle_transition(previous: object, current: object) -> None:
    """Require one adjacent transition in the serial stacked-PR lifecycle."""

    if previous not in LIFECYCLE_STATES or current not in LIFECYCLE_STATES:
        raise PublicationIntegrityError("lifecycle state is not registered")
    previous_index = LIFECYCLE_STATES.index(str(previous))
    current_index = LIFECYCLE_STATES.index(str(current))
    if current_index not in {previous_index, previous_index + 1}:
        raise PublicationIntegrityError(
            f"illegal lifecycle transition: {previous} -> {current}"
        )


def _valid_git_sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _stack_result(errors: list[str]) -> dict[str, object]:
    eligible = not errors
    return {
        "eligible": eligible,
        "disposition": "PASS" if eligible else "INELIGIBLE",
        "retry_budget_cost": 1 if eligible else 0,
        "assurance_budget_cost": 1 if eligible else 0,
        "errors": errors,
    }


def validate_stacked_execution_status(status: Mapping[str, Any]) -> list[str]:
    """Validate the synchronized status authority for one serial PR stack."""

    errors: list[str] = []
    stack = status.get("stacked_pr_execution")
    if not isinstance(stack, Mapping):
        return ["stacked_pr_execution status authority is missing"]
    if stack.get("schema_version") != 1:
        errors.append("stacked_pr_execution schema_version must equal 1")
    try:
        if validate_execution_mode(stack.get("execution_mode")) != "AUTO_STACKED_PR":
            errors.append("stacked recovery authority requires AUTO_STACKED_PR")
    except PublicationIntegrityError as exc:
        errors.append(str(exc))
    if stack.get("merge_policy") != "HUMAN_ONLY":
        errors.append("stack merge_policy must remain HUMAN_ONLY")
    if not is_safe_identifier(stack.get("stack_id")):
        errors.append("stack_id is missing or unsafe")
    if not _valid_git_sha(stack.get("target_sha")):
        errors.append("stack target_sha must be a full Git SHA")
    order = stack.get("pr_order")
    prs = stack.get("prs")
    if (
        not isinstance(order, list)
        or not order
        or any(not is_safe_identifier(item) for item in order)
        or len(order) != len(set(order))
        or not isinstance(prs, Mapping)
        or set(prs) != set(order)
    ):
        return [*errors, "stack PR order and records must match exactly"]
    active_records: list[str] = []
    for index, pr_id in enumerate(order):
        record = prs.get(pr_id)
        if not isinstance(record, Mapping):
            errors.append(f"{pr_id} execution record must be an object")
            continue
        lifecycle = record.get("lifecycle")
        if lifecycle not in LIFECYCLE_STATES:
            errors.append(f"{pr_id} lifecycle is not registered")
            continue
        history = record.get("lifecycle_history")
        if (
            not isinstance(history, list)
            or not history
            or history != list(LIFECYCLE_STATES[: len(history)])
            or history[-1] != lifecycle
        ):
            errors.append(f"{pr_id} lifecycle history is not an ordered prefix")
        lifecycle_index = LIFECYCLE_STATES.index(str(lifecycle))
        if 1 <= lifecycle_index < len(LIFECYCLE_STATES) - 1:
            active_records.append(pr_id)
        expected_predecessor = order[index - 1] if index else None
        if record.get("predecessor_pr") != expected_predecessor:
            errors.append(f"{pr_id} predecessor chain is invalid")
        base_sha = record.get("base_sha")
        if lifecycle != "PLANNED" and not _valid_git_sha(base_sha):
            errors.append(f"{pr_id} active lifecycle requires base_sha")
        if index == 0 and lifecycle != "PLANNED" and base_sha != stack.get("target_sha"):
            errors.append(f"{pr_id} base_sha must equal the canonical stack target")
        if index and lifecycle != "PLANNED":
            predecessor = prs.get(expected_predecessor)
            sealed_head = (
                predecessor.get("sealed_head")
                if isinstance(predecessor, Mapping)
                else None
            )
            if record.get("predecessor_sealed_sha") != sealed_head:
                errors.append(f"{pr_id} predecessor sealed-head binding is invalid")
            if base_sha != sealed_head:
                errors.append(f"{pr_id} base_sha differs from predecessor sealed head")
            if not isinstance(predecessor, Mapping) or predecessor.get("lifecycle") != "PR_OPEN":
                errors.append(f"{pr_id} activated before predecessor PR_OPEN")
        if lifecycle_index >= LIFECYCLE_STATES.index("SEALED") and not _valid_git_sha(
            record.get("sealed_head")
        ):
            errors.append(f"{pr_id} SEALED lifecycle requires sealed_head")
        if lifecycle_index >= LIFECYCLE_STATES.index("PUSHED"):
            pushed_ref = record.get("pushed_ref")
            if not isinstance(pushed_ref, str) or not pushed_ref.startswith("refs/heads/"):
                errors.append(f"{pr_id} PUSHED lifecycle requires pushed_ref")
        if lifecycle == "PR_OPEN":
            pr_url = record.get("pr_url")
            if not isinstance(pr_url, str) or not pr_url.startswith("https://github.com/"):
                errors.append(f"{pr_id} PR_OPEN lifecycle requires a GitHub PR URL")
        dispositions = record.get("gate_dispositions")
        if (
            not isinstance(dispositions, Mapping)
            or not dispositions
            or any(value not in GATE_DISPOSITIONS for value in dispositions.values())
        ):
            errors.append(f"{pr_id} gate dispositions are malformed")
        assurance = record.get("assurance_budget")
        if not isinstance(assurance, Mapping):
            errors.append(f"{pr_id} assurance budget is missing")
        else:
            maximum = assurance.get("maximum")
            consumed = assurance.get("consumed")
            if (
                type(maximum) is not int
                or maximum != DEFAULT_MAX_TOTAL_PER_WORK_UNIT
                or type(consumed) is not int
                or not 0 <= consumed <= maximum
            ):
                errors.append(f"{pr_id} assurance budget is invalid")
    active_pr = stack.get("active_implementation_pr")
    terminal = all(
        isinstance(prs.get(pr_id), Mapping)
        and prs[pr_id].get("lifecycle") == "PR_OPEN"
        for pr_id in order
    )
    if terminal:
        if active_records or active_pr is not None:
            errors.append("terminal AUTO_STACKED_PR stack must have no active PR")
    elif len(active_records) != 1:
        errors.append("AUTO_STACKED_PR requires exactly one active implementation PR")
    elif active_pr != active_records[0]:
        errors.append("active_implementation_pr does not name the active lifecycle")
    if status.get("in_progress") != active_pr:
        errors.append("top-level in_progress disagrees with active implementation PR")
    return errors


def load_stacked_execution_status(repo: str | Path) -> dict[str, Any]:
    """Load the byte-identical canonical and compatibility status mirrors."""

    root_path = Path(repo).resolve()
    canonical = root_path / "docs" / "codex_handoff" / "pr_status.yaml"
    mirror = root_path / "machine_readable" / "pr_status.yaml"
    try:
        canonical_bytes = canonical.read_bytes()
        mirror_bytes = mirror.read_bytes()
    except OSError as exc:
        raise PublicationIntegrityError("stack status mirror is unavailable") from exc
    if canonical_bytes != mirror_bytes:
        raise PublicationIntegrityError("stack status mirrors are not synchronized")
    try:
        payload = yaml.safe_load(canonical_bytes)
    except yaml.YAMLError as exc:
        raise PublicationIntegrityError("stack status YAML is malformed") from exc
    if not isinstance(payload, dict):
        raise PublicationIntegrityError("stack status must be a mapping")
    errors = validate_stacked_execution_status(payload)
    if errors:
        raise PublicationIntegrityError("; ".join(errors))
    return payload


def resolve_candidate_activation_base(
    repo: str | Path,
    status: Mapping[str, Any],
    *,
    work_unit_id: str,
    candidate_ref: str,
) -> str:
    """Resolve the candidate's fork point against its recorded exact stack base."""

    stack = status.get("stacked_pr_execution")
    records = stack.get("prs") if isinstance(stack, Mapping) else None
    record = records.get(work_unit_id) if isinstance(records, Mapping) else None
    declared_base = record.get("base_sha") if isinstance(record, Mapping) else None
    root_path = Path(repo).resolve()
    candidate_sha = str(
        git(root_path, "rev-parse", "--verify", f"{candidate_ref}^{{commit}}")
    ).strip()
    if not _valid_git_sha(candidate_sha):
        raise PublicationIntegrityError("candidate ref did not resolve to a commit")
    if not _valid_git_sha(declared_base):
        # A planned successor intentionally has no base until its predecessor
        # reaches PR_OPEN. Return a real commit so eligibility can report the
        # zero-budget INELIGIBLE disposition instead of a tool error.
        return candidate_sha
    activation_base = str(
        git(root_path, "merge-base", declared_base, candidate_sha)
    ).strip()
    if not _valid_git_sha(activation_base):
        raise PublicationIntegrityError("candidate activation base did not resolve")
    return activation_base


def _shared_worktree_roots(repo: str | Path) -> list[Path]:
    root_path = Path(repo).resolve()
    output = str(git(root_path, "worktree", "list", "--porcelain"))
    roots = [
        Path(line.removeprefix("worktree ")).resolve()
        for line in output.splitlines()
        if line.startswith("worktree ")
    ]
    if root_path not in roots:
        raise PublicationIntegrityError("current worktree is missing from Git inventory")
    return sorted(set(roots), key=lambda item: str(item))


def _shared_stack_run_plans(
    repo: str | Path,
    *,
    stack_id: str,
) -> list[tuple[Path, Path, Mapping[str, Any]]]:
    rows: list[tuple[Path, Path, Mapping[str, Any]]] = []
    for worktree in _shared_worktree_roots(repo):
        runs_root = worktree / ".agent-harness" / "runs"
        if not runs_root.is_dir() or runs_root.is_symlink():
            continue
        for plan_path in sorted(runs_root.glob("*/RUN_PLAN.json")):
            if plan_path.is_symlink() or not plan_path.is_file():
                raise PublicationIntegrityError(
                    f"shared stack RUN_PLAN is not a regular file: {plan_path}"
                )
            try:
                plan = load_json(plan_path)
            except (OSError, json.JSONDecodeError) as exc:
                raise PublicationIntegrityError(
                    f"shared stack RUN_PLAN is malformed: {plan_path}"
                ) from exc
            if not isinstance(plan, Mapping):
                raise PublicationIntegrityError(
                    f"shared stack RUN_PLAN is not an object: {plan_path}"
                )
            if (
                plan.get("execution_mode") == "AUTO_STACKED_PR"
                and plan.get("stack_id") == stack_id
            ):
                rows.append((worktree, plan_path.parent, plan))
    return rows


def shared_active_stack_runs(
    repo: str | Path,
    *,
    stack_id: str,
) -> list[dict[str, str]]:
    """Return active runs for one stack across every registered Git worktree."""

    by_location = {
        (worktree, str(plan.get("run_id"))): plan
        for worktree, _run_dir, plan in _shared_stack_run_plans(
            repo,
            stack_id=stack_id,
        )
    }
    active: list[dict[str, str]] = []
    for worktree in _shared_worktree_roots(repo):
        try:
            run_id = active_run_id(worktree, required=False)
        except ActiveRunError as exc:
            raise PublicationIntegrityError(str(exc)) from exc
        if run_id is None:
            continue
        plan = by_location.get((worktree, run_id))
        if plan is None:
            continue
        active.append(
            {
                "worktree": str(worktree),
                "run_id": run_id,
                "work_unit_id": str(plan.get("work_unit_id") or ""),
            }
        )
    return active


def shared_stack_assignment_count(
    repo: str | Path,
    *,
    stack_id: str,
    work_unit_id: str,
) -> int:
    """Count current-stack assignments across all Git worktrees and runs."""

    count = 0
    for _worktree, run_dir, plan in _shared_stack_run_plans(
        repo,
        stack_id=stack_id,
    ):
        if plan.get("work_unit_id") != work_unit_id:
            continue
        assignments = run_dir / "assignments"
        if assignments.is_symlink() or not assignments.is_dir():
            raise PublicationIntegrityError(
                f"shared stack assignments directory is invalid: {assignments}"
            )
        count += len(sorted(assignments.glob("*.json")))
    return count


def validate_run_execution_fields(
    plan: Mapping[str, Any], *, repo: str | Path
) -> list[str]:
    """Bind a run plan to the active serial-stack status without spending a gate."""

    errors: list[str] = []
    try:
        mode = validate_execution_mode(plan.get("execution_mode"))
    except PublicationIntegrityError as exc:
        return [str(exc)]
    lifecycle = plan.get("lifecycle_state")
    if lifecycle not in LIFECYCLE_STATES:
        errors.append("RUN_PLAN lifecycle_state is not registered")
    gate_disposition = plan.get("gate_disposition")
    if gate_disposition not in GATE_DISPOSITIONS:
        errors.append("RUN_PLAN gate_disposition is not registered")
    production_hash = plan.get("production_hash")
    if production_hash is not None and (
        not isinstance(production_hash, str)
        or SHA256_RE.fullmatch(production_hash) is None
    ):
        errors.append("RUN_PLAN production_hash is invalid")
    dependencies = plan.get("dependency_hashes")
    if (
        not isinstance(dependencies, Mapping)
        or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, str)
            or SHA256_RE.fullmatch(value) is None
            for key, value in dependencies.items()
        )
    ):
        errors.append("RUN_PLAN dependency_hashes are invalid")
    assurance = plan.get("assurance_budget")
    if not isinstance(assurance, Mapping):
        errors.append("RUN_PLAN assurance_budget is missing")
    else:
        maximum = assurance.get("maximum")
        consumed = assurance.get("consumed")
        if (
            type(maximum) is not int
            or maximum != DEFAULT_MAX_TOTAL_PER_WORK_UNIT
            or type(consumed) is not int
            or not 0 <= consumed <= maximum
        ):
            errors.append("RUN_PLAN assurance_budget is invalid")
    if mode == "MANUAL_PR":
        if plan.get("stack_id") is not None:
            errors.append("MANUAL_PR must not name an AUTO_STACKED_PR stack_id")
        return errors
    try:
        status = load_stacked_execution_status(repo)
    except PublicationIntegrityError as exc:
        return [*errors, str(exc)]
    stack = status["stacked_pr_execution"]
    work_unit_id = plan.get("work_unit_id")
    if plan.get("stack_id") != stack.get("stack_id"):
        errors.append("RUN_PLAN stack_id differs from status authority")
    eligibility = evaluate_stack_eligibility(
        status,
        work_unit_id=str(work_unit_id or ""),
        candidate_sha=str(plan.get("activation_base_sha") or ""),
    )
    errors.extend(str(item) for item in eligibility["errors"])
    records = stack.get("prs")
    record = records.get(work_unit_id) if isinstance(records, Mapping) else None
    if isinstance(record, Mapping):
        bindings = {
            "lifecycle_state": record.get("lifecycle"),
            "activation_base_sha": record.get("base_sha"),
            "predecessor_pr": record.get("predecessor_pr"),
            "predecessor_sealed_sha": record.get("predecessor_sealed_sha"),
            "dependency_hashes": record.get("dependency_hashes"),
            "assurance_budget": record.get("assurance_budget"),
        }
        for field, expected in bindings.items():
            if plan.get(field) != expected:
                errors.append(f"RUN_PLAN {field} differs from status authority")
    binding = plan.get("candidate_binding")
    if isinstance(binding, Mapping) and binding.get("state") == "frozen":
        evidence_key = plan.get("evidence_key")
        if not isinstance(evidence_key, Mapping):
            errors.append("frozen AUTO_STACKED_PR run requires evidence_key")
        else:
            try:
                _validate_evidence_key(evidence_key, label="RUN_PLAN evidence_key")
            except PublicationIntegrityError as exc:
                errors.append(str(exc))
            if evidence_key.get("production_hash") != binding.get("production_hash"):
                errors.append("RUN_PLAN evidence_key production hash differs from seal")
            if evidence_key.get("dependency_hashes") != plan.get("dependency_hashes"):
                errors.append("RUN_PLAN evidence_key dependency hashes drifted")
    return errors


def evaluate_stack_eligibility(
    status: Mapping[str, Any],
    *,
    work_unit_id: str,
    candidate_sha: str,
) -> dict[str, object]:
    """Evaluate selected-work eligibility separately from structural DAG validity."""

    errors: list[str] = validate_stacked_execution_status(status)
    stack = status.get("stacked_pr_execution")
    if not isinstance(stack, Mapping):
        return _stack_result(["stacked_pr_execution status authority is missing"])
    try:
        mode = validate_execution_mode(stack.get("execution_mode"))
    except PublicationIntegrityError as exc:
        errors.append(str(exc))
        mode = None
    if stack.get("merge_policy") != "HUMAN_ONLY":
        errors.append("stack merge_policy must remain HUMAN_ONLY")
    if mode != "AUTO_STACKED_PR":
        errors.append("selected stacked work requires AUTO_STACKED_PR")
    order = stack.get("pr_order")
    prs = stack.get("prs")
    if (
        not isinstance(order, list)
        or not order
        or any(not isinstance(item, str) for item in order)
        or len(order) != len(set(order))
        or not isinstance(prs, Mapping)
    ):
        return _stack_result([*errors, "stack PR order or records are malformed"])
    if work_unit_id not in order or work_unit_id not in prs:
        return _stack_result([*errors, f"{work_unit_id} is not registered in the stack"])
    active_pr = stack.get("active_implementation_pr")
    if active_pr != work_unit_id:
        errors.append(
            f"active implementation PR is {active_pr!r}, not {work_unit_id}"
        )
    if status.get("in_progress") != active_pr:
        errors.append("top-level in_progress disagrees with active implementation PR")
    record = prs[work_unit_id]
    if not isinstance(record, Mapping):
        return _stack_result([*errors, f"{work_unit_id} execution record is malformed"])
    if record.get("lifecycle") not in LIFECYCLE_STATES[1:-1]:
        errors.append(
            f"{work_unit_id} lifecycle must be an active pre-PR_OPEN state"
        )
    history = record.get("lifecycle_history")
    if not isinstance(history, list) or not history:
        errors.append(f"{work_unit_id} lifecycle history is missing")
    else:
        expected = list(LIFECYCLE_STATES[: len(history)])
        if history != expected or history[-1] != record.get("lifecycle"):
            errors.append(f"{work_unit_id} lifecycle history is not an ordered prefix")
    index = order.index(work_unit_id)
    base_sha = record.get("base_sha")
    if not _valid_git_sha(candidate_sha):
        errors.append("candidate base is not a full Git SHA")
    if index == 0:
        target_sha = stack.get("target_sha")
        if base_sha != target_sha or candidate_sha != target_sha:
            errors.append("first stacked PR must start at the exact canonical target SHA")
        if record.get("predecessor_pr") is not None:
            errors.append("first stacked PR must not name a stack predecessor")
    else:
        expected_predecessor = order[index - 1]
        predecessor = prs.get(expected_predecessor)
        if record.get("predecessor_pr") != expected_predecessor:
            errors.append(
                f"{work_unit_id} predecessor must be {expected_predecessor}"
            )
        if not isinstance(predecessor, Mapping):
            errors.append(f"{expected_predecessor} execution record is malformed")
        else:
            if predecessor.get("lifecycle") != "PR_OPEN":
                errors.append(
                    f"{expected_predecessor} must reach PR_OPEN before {work_unit_id} activation"
                )
            sealed_head = predecessor.get("sealed_head")
            recorded = record.get("predecessor_sealed_sha")
            if not _valid_git_sha(sealed_head):
                errors.append(f"{expected_predecessor} sealed head is missing")
            if recorded != sealed_head:
                errors.append(
                    f"{work_unit_id} recorded predecessor sealed head does not match"
                )
            if base_sha != sealed_head or candidate_sha != sealed_head:
                errors.append(
                    f"{work_unit_id} must start at the exact predecessor sealed head"
                )
    return _stack_result(errors)


def _validate_evidence_key(value: Mapping[str, Any], *, label: str) -> None:
    production_hash = value.get("production_hash")
    dependencies = value.get("dependency_hashes")
    if not isinstance(production_hash, str) or SHA256_RE.fullmatch(production_hash) is None:
        raise PublicationIntegrityError(f"{label} production_hash is invalid")
    if (
        not isinstance(dependencies, Mapping)
        or any(
            not isinstance(key, str)
            or not key
            or not isinstance(item, str)
            or SHA256_RE.fullmatch(item) is None
            for key, item in dependencies.items()
        )
    ):
        raise PublicationIntegrityError(f"{label} dependency_hashes are invalid")


def evaluate_evidence_freshness(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, object]:
    """Route only production/dependency drift to substantive assurance."""

    _validate_evidence_key(previous, label="previous evidence key")
    _validate_evidence_key(current, label="current evidence key")
    if previous["production_hash"] != current["production_hash"]:
        return {
            "seal_valid": False,
            "substantive_rerun_required": True,
            "stale_dependencies": [],
            "reason": "PRODUCTION_HASH_CHANGED",
        }
    previous_dependencies = dict(previous["dependency_hashes"])
    current_dependencies = dict(current["dependency_hashes"])
    stale = sorted(
        key
        for key in set(previous_dependencies) | set(current_dependencies)
        if previous_dependencies.get(key) != current_dependencies.get(key)
    )
    if stale:
        return {
            "seal_valid": True,
            "substantive_rerun_required": True,
            "stale_dependencies": stale,
            "reason": "DEPENDENCY_HASH_CHANGED",
        }
    return {
        "seal_valid": True,
        "substantive_rerun_required": False,
        "stale_dependencies": [],
        "reason": "EVIDENCE_KEY_UNCHANGED",
    }


def historical_run_ids(repo: Path) -> set[str]:
    """Frozen pre-PR-124 runs that keep validating under schema v1."""

    path = repo / ".agent-harness" / "HISTORICAL_RUNS.json"
    if not path.is_file():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    runs = payload.get("runs", [])
    return {run for run in runs if isinstance(run, str)}


def root() -> Path:
    try:
        text = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if text:
            return Path(text).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    cwd = Path.cwd().resolve()
    if (cwd / ".agent-harness").is_dir():
        return cwd
    here = Path(__file__).resolve()
    return here.parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def confined_repo_file(repo: Path, rel: str, *, label: str) -> Path:
    """Resolve a canonical repository-relative regular file without symlink escape."""

    if not isinstance(rel, str) or not rel:
        raise ValueError(f"{label} must be a non-empty repository-relative path.")
    rel_path = Path(rel)
    if (
        rel_path.is_absolute()
        or ".." in rel_path.parts
        or "\\" in rel
        or rel_path.as_posix() != rel
    ):
        raise ValueError(f"{label} must be canonical and repository-relative: {rel}")
    probe = repo
    for part in rel_path.parts:
        probe = probe / part
        if probe.is_symlink():
            raise ValueError(f"{label} traverses a symlink: {rel}")
    if not probe.is_file():
        raise ValueError(f"{label} is missing or not a regular file: {rel}")
    return probe


def hash_files(repo: Path, files: list[str]) -> tuple[str, list[tuple[str, str]]]:
    digest = hashlib.sha256()
    entries: list[tuple[str, str]] = []
    for rel in files:
        path = confined_repo_file(repo, rel, label="Shared context source")
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        entries.append((rel, file_hash))
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest(), entries


def context_entries(
    repo: Path,
    index: Mapping[str, Any],
) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Resolve the injected Tier-0 sources named by the context index."""

    files = index.get("shared_files")
    pack_files = index.get("pack_files")
    if (
        not isinstance(files, list)
        or not files
        or any(not isinstance(rel, str) for rel in files)
        or len(files) != len(set(files))
    ):
        raise ValueError("shared_files must be a non-empty list of unique paths.")
    if (
        not isinstance(pack_files, list)
        or not pack_files
        or any(not isinstance(rel, str) for rel in pack_files)
        or len(pack_files) != len(set(pack_files))
        or pack_files != files
    ):
        raise ValueError(
            "pack_files must exactly equal shared_files; non-injected references "
            "must not rotate the global context version."
        )
    reference_files = index.get("reference_only_files", [])
    if (
        not isinstance(reference_files, list)
        or any(not isinstance(rel, str) for rel in reference_files)
        or len(reference_files) != len(set(reference_files))
    ):
        raise ValueError("reference_only_files must be a list of unique paths.")
    overlap = sorted(set(files) & set(reference_files))
    if overlap:
        raise ValueError(
            "shared_files and reference_only_files must be disjoint: "
            + ", ".join(overlap)
        )
    version, entries = hash_files(repo, files)
    hashes = dict(entries)
    return version, entries, [(rel, hashes[rel]) for rel in pack_files]


def render_context_pack(
    version: str,
    built_at: str,
    entries: list[tuple[str, str]],
    repo: Path,
) -> str:
    chunks = [
        "# Generated Shared Context View",
        "",
        f"Context version: `{version}`",
        f"Built at: `{built_at}`",
        "",
        (
            "This compact view is generated from the machine context index. "
            "Live HEAD, DAG, status, and active-run context is computed by the "
            "hooks at use time. Reference-only files are read only when an "
            "assignment names them."
        ),
    ]
    for rel, sha in entries:
        text = confined_repo_file(
            repo, rel, label="Context pack source"
        ).read_text(encoding="utf-8")
        chunks.extend(
            [
                "",
                f"---\n\n## Source: `{rel}`\n\nSHA-256: `{sha}`\n",
                text.rstrip(),
            ]
        )
    return "\n".join(chunks).rstrip() + "\n"


def load_validated_context_pack(repo: Path, index: Mapping[str, Any]) -> str:
    """Return the generated view only when index, sources, and rendered bytes agree."""

    actual, entries, pack_entries = context_entries(repo, index)
    if index.get("context_version") != actual:
        raise ValueError("Context sources changed after the generated view was built.")
    if index.get("file_hashes") != dict(entries):
        raise ValueError("CONTEXT_INDEX.json file_hashes do not match shared files.")
    expected = render_context_pack(
        actual,
        str(index.get("built_at", "")),
        pack_entries,
        repo,
    )
    pack_path = confined_repo_file(
        repo,
        ".agent-harness/generated/CONTEXT_PACK.md",
        label="Generated context view",
    )
    actual_text = pack_path.read_text(encoding="utf-8")
    if actual_text != expected:
        raise ValueError("Generated CONTEXT_PACK.md does not match the context index.")
    return actual_text


def active_run_pointer_paths(repo: Path) -> tuple[Path, Path]:
    """Return the local runtime pointer and the pre-MA-01 compatibility path."""

    return (
        repo / ACTIVE_RUN_RELATIVE_PATH,
        repo / LEGACY_ACTIVE_RUN_RELATIVE_PATH,
    )


def _relative_pointer(repo: Path, path: Path) -> str:
    return path.relative_to(repo).as_posix()


def _read_active_run_pointer(repo: Path, path: Path) -> str:
    pointer = _relative_pointer(repo, path)
    if path.is_symlink() or not path.is_file():
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            "The active-run pointer must be a readable regular file containing a safe identifier.",
            pointer=pointer,
        )
    try:
        run_id = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            f"Cannot read the active-run pointer: {exc}",
            pointer=pointer,
        ) from exc
    if not is_safe_identifier(run_id):
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            "The active-run pointer is empty or contains an unsafe identifier.",
            pointer=pointer,
        )
    return run_id


def active_run_id(
    repo: Path,
    *,
    required: bool = True,
) -> str | None:
    """Resolve active local run state without mistaking a dangling pointer for none.

    The runtime pointer is deliberately untracked.  The legacy root pointer is
    read only as an upgrade bridge; a clean clone contains neither.  Invalid or
    conflicting state is always an explicit error, including when ``required``
    is false.
    """

    candidates = [
        path
        for path in active_run_pointer_paths(repo)
        if path.exists() or path.is_symlink()
    ]
    if not candidates:
        if required:
            raise ActiveRunError(
                "NO_ACTIVE_RUN",
                "No active run. Use init_run.py first.",
            )
        return None

    values = [(path, _read_active_run_pointer(repo, path)) for path in candidates]

    distinct = {value for _, value in values}
    if len(distinct) != 1:
        detail = ", ".join(
            f"{_relative_pointer(repo, path)}={value!r}" for path, value in values
        )
        raise ActiveRunError(
            "CONFLICTING_ACTIVE_RUN_POINTERS",
            f"Runtime and legacy active-run pointers disagree: {detail}",
        )

    run_id = values[0][1]
    run_dir = repo / ".agent-harness" / "runs" / run_id
    plan_path = run_dir / "RUN_PLAN.json"
    pointer = _relative_pointer(repo, values[0][0])
    plan = None
    if (
        not run_dir.is_symlink()
        and run_dir.is_dir()
        and not plan_path.is_symlink()
        and plan_path.is_file()
    ):
        try:
            plan = load_json(plan_path)
        except (OSError, json.JSONDecodeError):
            pass
    if not isinstance(plan, Mapping) or plan.get("run_id") != run_id:
        raise ActiveRunError(
            "DANGLING_ACTIVE_RUN",
            "The active-run pointer has no valid matching RUN_PLAN.json target.",
            pointer=pointer,
            run_id=run_id,
        )
    return run_id


def _git_head_state(repo: Path) -> tuple[str, str]:
    """Distinguish a genuine unborn branch from an unreadable Git state."""

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", *args],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ValueError("Git is unavailable; live HEAD cannot be resolved.") from exc

    head_result = run("rev-parse", "--verify", "HEAD^{commit}")
    head = head_result.stdout.strip()
    if head_result.returncode == 0:
        if re.fullmatch(r"[0-9a-f]{40,64}", head) is None:
            raise ValueError("Git returned a malformed HEAD identity.")
        branch_result = run("symbolic-ref", "--quiet", "--short", "HEAD")
        if branch_result.returncode == 0 and branch_result.stdout.strip():
            return head, branch_result.stdout.strip()
        if branch_result.returncode == 1:
            return head, "detached"
        detail = branch_result.stderr.strip() or "symbolic-ref failed"
        raise ValueError(f"Git branch state cannot be resolved: {detail}")

    symbolic = run("symbolic-ref", "--quiet", "HEAD")
    full_ref = symbolic.stdout.strip()
    if (
        symbolic.returncode == 0
        and full_ref.startswith("refs/heads/")
        and full_ref != "refs/heads/"
    ):
        shown = run("show-ref", "--verify", "--quiet", full_ref)
        if shown.returncode == 1:
            return "UNBORN", full_ref.removeprefix("refs/heads/")
        detail = (
            head_result.stderr.strip()
            or shown.stderr.strip()
            or "symbolic HEAD does not resolve to a commit"
        )
        raise ValueError(f"Git HEAD cannot be resolved: {detail}")
    detail = head_result.stderr.strip() or symbolic.stderr.strip() or "rev-parse failed"
    raise ValueError(f"Git HEAD cannot be resolved: {detail}")


def _yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    if match is None:
        return None
    value = match.group(1).strip().strip("'\"")
    return None if value in {"", "null", "~"} else value


def _yaml_top_level_list_count(text: str, key: str) -> int:
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.startswith(f"{key}:")),
        None,
    )
    if start is None:
        return 0
    inline = lines[start].split(":", 1)[1].strip()
    if inline in {"[]", "null", "~"}:
        return 0
    count = 0
    for line in lines[start + 1 :]:
        if line and not line[0].isspace() and not line.startswith("- "):
            break
        if line.startswith("- "):
            count += 1
    return count


def _yaml_pr_mapping_count(text: str) -> int:
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line == "prs:"),
        None,
    )
    if start is None:
        return 0
    count = 0
    for line in lines[start + 1 :]:
        if re.match(r"^  PR-[^:]+:", line) or re.match(r"^- id:\s*PR-", line):
            count += 1
            continue
        if line and not line[0].isspace():
            break
    return count


def resolve_live_context(repo: Path, index: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve transient operational context without creating another state file.

    The byte identities below are internal spawn-context drift seals only.
    They are not scientific provenance and must not be copied into claim,
    novelty, or research-artifact gates.
    """

    sources = index.get("live_sources")
    if not isinstance(sources, Mapping):
        raise ValueError("CONTEXT_INDEX.json must define live_sources.")
    dag_rel = sources.get("dag")
    status_rel = sources.get("status")
    if not isinstance(dag_rel, str) or not isinstance(status_rel, str):
        raise ValueError("live_sources must name string dag and status paths.")

    source_bytes: dict[str, bytes] = {}
    for label, rel in (("dag", dag_rel), ("status", status_rel)):
        path = confined_repo_file(repo, rel, label=f"Live {label} source")
        source_bytes[label] = path.read_bytes()

    dag_text = source_bytes["dag"].decode("utf-8")
    status_text = source_bytes["status"].decode("utf-8")
    head, branch = _git_head_state(repo)

    run_id = active_run_id(repo, required=False)
    run_summary = None
    if run_id is not None:
        plan = load_json(
            repo / ".agent-harness" / "runs" / run_id / "RUN_PLAN.json"
        )
        run_summary = {
            key: plan.get(key)
            for key in (
                "run_id",
                "work_unit_id",
                "change_set_id",
                "publication_group_id",
                "spec_ref",
                "base_ref",
                "head_ref",
                "target_ref",
                "base_sha",
                "candidate_ref",
                "candidate_binding",
                "context_version",
                "status",
            )
        }

    identity_payload = {
        "context_version": index.get("context_version"),
        "head": head,
        "dag_sha256": hashlib.sha256(source_bytes["dag"]).hexdigest(),
        "status_sha256": hashlib.sha256(source_bytes["status"]).hexdigest(),
        "run": run_summary,
    }
    live_context_id = hashlib.sha256(
        json.dumps(
            identity_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return {
        **identity_payload,
        "live_context_id": live_context_id,
        "branch": branch,
        "dag": {
            "path": dag_rel,
            "generated_on": _yaml_scalar(dag_text, "generated_on"),
            "scope": _yaml_scalar(dag_text, "scope"),
            "pr_count": _yaml_pr_mapping_count(dag_text),
        },
        "status": {
            "path": status_rel,
            "generated_on": _yaml_scalar(status_text, "generated_on"),
            "completed": _yaml_top_level_list_count(status_text, "completed"),
            "blocked": _yaml_top_level_list_count(status_text, "blocked"),
            "pending": _yaml_top_level_list_count(status_text, "pending"),
            "in_progress": _yaml_scalar(status_text, "in_progress"),
        },
    }


def format_live_context(state: Mapping[str, Any]) -> str:
    dag = state["dag"]
    status = state["status"]
    run = state.get("run")
    run_text = "none"
    if isinstance(run, Mapping):
        run_text = (
            f"{run.get('run_id')} (status={run.get('status') or 'unspecified'}, "
            f"work_unit={run.get('work_unit_id')}, "
            f"change_set={run.get('change_set_id')}, spec={run.get('spec_ref')})"
        )
    return "\n".join(
        [
            f"Live context ID: {str(state['live_context_id'])[:12]}",
            f"HEAD: {str(state['head'])[:12]} ({state['branch']})",
            (
                f"DAG: {dag['path']} (generated={dag.get('generated_on')}, "
                f"prs={dag.get('pr_count')})"
            ),
            (
                f"Status: {status['path']} (generated={status.get('generated_on')}, "
                f"completed={status.get('completed')}, blocked={status.get('blocked')}, "
                f"pending={status.get('pending')}, "
                f"in_progress={status.get('in_progress') or 'none'})"
            ),
            f"Active run summary: {run_text}",
        ]
    )


def cli_active_run_id(
    repo: Path,
    *,
    required: bool = True,
) -> str | None:
    """Resolve active state for a CLI without leaking a Python traceback."""

    try:
        return active_run_id(repo, required=required)
    except ActiveRunError as exc:
        raise SystemExit(str(exc)) from None


def write_active_run_id(repo: Path, run_id: str) -> Path:
    """Atomically publish a local-only active-run pointer."""

    if not is_safe_identifier(run_id):
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            f"Refusing to write an unsafe active-run identifier: {run_id!r}",
            run_id=run_id,
        )
    path = repo / ACTIVE_RUN_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(run_id + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def clear_active_run_pointers(
    repo: Path,
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Remove only local pointer files; run directories and evidence remain."""

    targets: list[tuple[Path, str]] = []
    for path in active_run_pointer_paths(repo):
        if not path.exists() and not path.is_symlink():
            continue
        pointer = _relative_pointer(repo, path)
        if expected_run_id is not None:
            actual = _read_active_run_pointer(repo, path)
            if actual != expected_run_id:
                raise ActiveRunError(
                    "CONFLICTING_ACTIVE_RUN_POINTERS",
                    "The active-run pointer changed while the run was closing.",
                    pointer=pointer,
                    run_id=actual,
                )
        elif path.is_symlink() or not path.is_file():
            raise ActiveRunError(
                "INVALID_ACTIVE_RUN_POINTER",
                "Refusing to remove a non-regular active-run pointer.",
                pointer=pointer,
            )
        targets.append((path, pointer))

    cleared: list[str] = []
    for path, pointer in targets:
        path.unlink()
        cleared.append(pointer)
    return cleared


def is_safe_identifier(value: object) -> bool:
    return isinstance(value, str) and SAFE_IDENTIFIER_RE.fullmatch(value) is not None


def is_evidence_identity(value: object) -> bool:
    """Accept a bounded stable identity without pretending it is authenticated.

    A cryptographic digest is one valid identity when exact bytes matter, but a
    DOI, dataset release, source path/revision, or review-scope label is also a
    legitimate research identity.  This field is self-declared unless another
    validator explicitly binds it to bytes.
    """

    return (
        isinstance(value, str)
        and value == value.strip()
        and EVIDENCE_IDENTITY_RE.fullmatch(value) is not None
    )


def is_run_local_claim_id(value: object, run_id: str) -> bool:
    """Return whether a non-persistent process question is bound to this run."""

    return is_safe_identifier(value) and str(value).startswith(f"RUN-{run_id}-")


def declared_result_path(run_id: str, assignment_id: str) -> str:
    return f".agent-harness/runs/{run_id}/results/{assignment_id}.json"


def assignment_sha256(assignment: Mapping[str, Any]) -> str:
    """Return the canonical registration seal, excluding the seal field itself."""

    payload = dict(assignment)
    payload.pop("assignment_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_merge_input_manifest(repo: Path, run_dir: Path) -> list[dict[str, Any]]:
    """Hash every run-local input consumed by result merging."""

    paths = [run_dir / "RUN_PLAN.json"]
    for directory in ("assignments", "results", "launches"):
        paths.extend(sorted((run_dir / directory).glob("*.json")))
    rows: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda item: item.relative_to(repo).as_posix()):
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                f"merge input is missing or not a regular file: "
                f"{path.relative_to(repo).as_posix()}"
            )
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(repo).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return rows


def run_merge_input_sha256(rows: list[dict[str, Any]]) -> str:
    return hashlib.sha256(
        json.dumps(
            rows,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def validate_run_plan_payload(
    plan: object,
    *,
    repo: Path,
    run_id: str,
    context_version: str,
) -> list[str]:
    """Validate a run plan without rewriting frozen schema-v1 run history."""

    errors: list[str] = []
    if not isinstance(plan, Mapping):
        return ["RUN_PLAN is not a JSON object"]
    if plan.get("run_id") != run_id:
        errors.append("RUN_PLAN run_id does not match its directory")
    if plan.get("context_version") != context_version:
        errors.append("RUN_PLAN context_version is stale")
    if not is_safe_identifier(plan.get("work_unit_id")):
        errors.append("RUN_PLAN work_unit_id is missing or unsafe")
    schema = plan.get("schema_version")
    if schema == 1:
        return errors
    if schema != 2:
        errors.append("RUN_PLAN schema_version must equal 1 or 2")
        return errors

    try:
        budget = plan.get("budget")
        if not isinstance(budget, Mapping):
            raise PublicationIntegrityError("RUN_PLAN budget must be an object")
        for field, maximum in (
            ("max_concurrent", 4),
            ("max_total", 8),
            (
                "max_total_per_work_unit",
                DEFAULT_MAX_TOTAL_PER_WORK_UNIT,
            ),
            ("max_depth", 2),
        ):
            value = budget.get(field)
            if type(value) is not int or not 1 <= value <= maximum:
                raise PublicationIntegrityError(
                    f"RUN_PLAN budget.{field} must be an integer in [1, {maximum}]"
                )
        validate_review_rereview_budget_exception(
            plan,
            run_id=run_id,
        )
        change_set_id = require_change_set_id(plan.get("change_set_id"))
        publication_group_id = require_publication_group_id(
            plan.get("publication_group_id")
        )
        target_remote, target_branch, target_ref = canonical_target_ref(
            repo, str(plan.get("target_ref") or "")
        )
        if (
            plan.get("target_remote") != target_remote
            or plan.get("target_branch") != target_branch
            or plan.get("target_ref") != target_ref
        ):
            raise PublicationIntegrityError("RUN_PLAN target identity drifted")
        base_sha = str(
            git(repo, "rev-parse", "--verify", f"{target_ref}^{{commit}}")
        ).strip()
        if plan.get("base_sha") != base_sha:
            raise PublicationIntegrityError(
                "RUN_PLAN target moved; rebase and initialize a new candidate run"
            )
        policy_ref = plan.get("integration_policy")
        if not isinstance(policy_ref, Mapping):
            raise PublicationIntegrityError("RUN_PLAN lacks integration_policy")
        policy_bytes, policy = load_publication_policy(
            repo,
            policy_ref.get("path"),
            expected_sha256=str(policy_ref.get("sha256") or ""),
        )
        validate_declared_policy_identity(
            policy,
            change_set_id=change_set_id,
            publication_group_id=publication_group_id,
            target_ref=f"{target_remote}/{target_branch}",
            target_sha=base_sha,
        )
        if policy_ref != {
            "path": policy_ref.get("path"),
            "sha256": bytes_sha256(policy_bytes),
            "policy_id": policy.get("policy_id"),
        }:
            raise PublicationIntegrityError("RUN_PLAN integration_policy drifted")
        expected_publication_budget = {
            field: policy[field]
            for field in (
                "max_open_prs",
                "max_direct_to_target_prs",
                "max_prs_per_change_set",
                "max_stack_depth",
                "max_file_overlap_prs",
            )
        }
        if plan.get("publication_budget") != expected_publication_budget:
            raise PublicationIntegrityError("RUN_PLAN publication budget drifted")
        binding = plan.get("candidate_binding")
        binding_errors = validate_candidate_binding(
            binding,
            repo=repo,
            require_frozen=False,
        )
        if binding_errors:
            raise PublicationIntegrityError("; ".join(binding_errors))
        if isinstance(binding, Mapping) and binding.get("state") == "frozen":
            if binding.get("base_sha") != base_sha:
                raise PublicationIntegrityError(
                    "RUN_PLAN candidate seal is based on a different target"
                )
        if plan.get("publication_mode") != "external_publisher_only":
            raise PublicationIntegrityError(
                "RUN_PLAN publication_mode must be external_publisher_only"
            )
        if plan.get("github_pr_created_by_harness") is not False:
            raise PublicationIntegrityError(
                "RUN_PLAN must record github_pr_created_by_harness=false"
            )
        if plan.get("status") not in {"initialized", "candidate_frozen"}:
            raise PublicationIntegrityError(
                "RUN_PLAN status must be initialized or candidate_frozen"
            )
        if "execution_mode" in plan:
            execution_errors = validate_run_execution_fields(plan, repo=repo)
            if execution_errors:
                raise PublicationIntegrityError("; ".join(execution_errors))
        candidate_ref = plan.get("candidate_ref")
        if not isinstance(candidate_ref, str) or not candidate_ref:
            raise PublicationIntegrityError("RUN_PLAN candidate_ref must be non-empty")
        spec_ref = plan.get("spec_ref")
        confined_repo_file(repo, str(spec_ref or ""), label="RUN_PLAN spec_ref")
        # Keep these names used so a malformed value cannot be normalized away.
        _ = (change_set_id, publication_group_id)
    except (OSError, PublicationIntegrityError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def validate_review_rereview_budget_exception(
    plan: Mapping[str, Any],
    *,
    run_id: str,
) -> Mapping[str, Any] | None:
    """Validate a narrow, owner-authorized reviewer-only budget exception.

    The ordinary cumulative work-unit ceiling remains 16.  An exception may
    authorize at most two named reviewer assignments in exactly one run after
    that ceiling has been exhausted.  A later reauthorization may begin only
    after all earlier two-assignment waves have been consumed.  Every wave must
    carry a fresh human authorization, name at most two reviewers, and bind its
    exact cumulative start.  No form authorizes implementers, adjudicators,
    arbitrary assignment IDs, or a reusable/global increase.
    """

    value = plan.get("budget_exception")
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception must be an object"
        )
    required_fields = {
        "exception_id",
        "kind",
        "run_id",
        "work_unit_id",
        "authorized_by",
        "reason",
        "baseline_limit",
        "additional_assignments",
        "allowed_workflow_role",
        "allowed_assignment_ids",
        "single_use",
    }
    kind = value.get("kind")
    if kind == "single_run_reviewer_rereview_reauthorization":
        required_fields.add("cumulative_start")
    if set(value) != required_fields:
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception fields must exactly match the "
            "review-rereview exception schema"
        )
    if not is_safe_identifier(value.get("exception_id")):
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception.exception_id is missing or unsafe"
        )
    if kind not in {
        "single_run_reviewer_rereview",
        "single_run_reviewer_rereview_reauthorization",
    }:
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception.kind is not a registered "
            "review-rereview exception"
        )
    if value.get("run_id") != run_id:
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception is bound to a different run"
        )
    if value.get("work_unit_id") != plan.get("work_unit_id"):
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception is bound to a different work unit"
        )
    authorized_by = value.get("authorized_by")
    reason = value.get("reason")
    if (
        not isinstance(authorized_by, str)
        or not authorized_by.strip()
        or not EVIDENCE_IDENTITY_RE.fullmatch(authorized_by)
        or not isinstance(reason, str)
        or not reason.strip()
        or not EVIDENCE_IDENTITY_RE.fullmatch(reason)
    ):
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception requires bounded authorization and reason"
        )
    budget = plan.get("budget")
    if not isinstance(budget, Mapping):
        raise PublicationIntegrityError("RUN_PLAN budget must be an object")
    if (
        value.get("baseline_limit") != DEFAULT_MAX_TOTAL_PER_WORK_UNIT
        or budget.get("max_total_per_work_unit")
        != DEFAULT_MAX_TOTAL_PER_WORK_UNIT
    ):
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception cannot alter the ordinary work-unit limit"
        )
    additional = value.get("additional_assignments")
    assignment_ids = value.get("allowed_assignment_ids")
    if (
        type(additional) is not int
        or not 1 <= additional <= MAX_REVIEW_REREVIEW_EXCEPTION_ASSIGNMENTS
        or not isinstance(assignment_ids, list)
        or len(assignment_ids) != additional
        or any(
            not isinstance(item, str) or not is_safe_identifier(item)
            for item in assignment_ids
        )
        or len(set(assignment_ids)) != len(assignment_ids)
    ):
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception must name one or two unique safe "
            "assignment IDs"
        )
    if value.get("allowed_workflow_role") != "reviewer":
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception may authorize only reviewer assignments"
        )
    if value.get("single_use") is not True:
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception must be single_use=true"
        )
    if kind == "single_run_reviewer_rereview_reauthorization":
        cumulative_start = value.get("cumulative_start")
        if (
            type(cumulative_start) is not int
            or cumulative_start
            < FIRST_REAUTHORIZED_REVIEW_REREVIEW_CUMULATIVE_START
            or (
                cumulative_start
                - FIRST_REAUTHORIZED_REVIEW_REREVIEW_CUMULATIVE_START
            )
            % MAX_REVIEW_REREVIEW_EXCEPTION_ASSIGNMENTS
            != 0
        ):
            raise PublicationIntegrityError(
                "RUN_PLAN reviewer rereview reauthorization must begin at an "
                "exact two-assignment wave boundary at or after cumulative "
                f"assignment {FIRST_REAUTHORIZED_REVIEW_REREVIEW_CUMULATIVE_START}"
            )
    return value


def enforce_work_unit_assignment_budget(
    plan: Mapping[str, Any],
    *,
    run_id: str,
    assignment_id: str,
    workflow_role: str,
    cumulative_count: int,
    current_run_assignment_ids: set[str],
) -> None:
    """Fail closed unless an assignment fits the ordinary or narrow exception."""

    budget = plan.get("budget")
    if not isinstance(budget, Mapping):
        raise PublicationIntegrityError("RUN_PLAN budget must be an object")
    ordinary_limit = int(budget.get("max_total_per_work_unit", 0) or 0)
    if cumulative_count < ordinary_limit and plan.get("budget_exception") is None:
        return

    exception = validate_review_rereview_budget_exception(
        plan,
        run_id=run_id,
    )
    if exception is None:
        raise PublicationIntegrityError(
            f"BLOCKED_ASSURANCE_BUDGET_EXHAUSTED: cumulative work-unit budget for "
            f"{plan.get('work_unit_id')}: {cumulative_count}/{ordinary_limit} "
            "(budget spans ALL runs of this work unit; a new run does not "
            "reset it)"
        )

    allowed_ids = set(exception["allowed_assignment_ids"])
    additional = int(exception["additional_assignments"])
    authorized_start = int(
        exception.get("cumulative_start", ordinary_limit)
    )
    if cumulative_count < ordinary_limit:
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception cannot be consumed before the ordinary "
            "work-unit budget is exhausted"
        )
    if cumulative_count < authorized_start:
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception cannot be consumed before its "
            "authorized cumulative start"
        )
    if not current_run_assignment_ids <= allowed_ids:
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception run contains a non-authorized assignment"
        )
    if cumulative_count != authorized_start + len(current_run_assignment_ids):
        raise PublicationIntegrityError(
            "RUN_PLAN budget_exception consumption does not match cumulative "
            "work-unit history"
        )
    if workflow_role != "reviewer" or assignment_id not in allowed_ids:
        raise PublicationIntegrityError(
            "Cumulative work-unit budget exception authorizes only the named "
            "reviewer assignments"
        )
    if len(current_run_assignment_ids) >= additional:
        raise PublicationIntegrityError(
            "Cumulative work-unit budget exception is exhausted"
        )


def _validate_claim_references(
    repo: Path,
    row: Mapping[str, Any],
    *,
    line_number: int,
    errors: list[str],
) -> None:
    """Validate live spec paths and PR-scoped evidence labels, not stored status."""

    spec_refs = row.get("spec_refs")
    evidence_refs = row.get("evidence_refs")
    if spec_refs is None and evidence_refs is None and "evidence_ids" not in row:
        return

    if "evidence_ids" in row:
        errors.append(
            f"claim registry line {line_number} uses duplicate evidence_ids; "
            "evidence_refs is the canonical base field"
        )

    spec_prs: set[str] = set()
    if (
        not isinstance(spec_refs, list)
        or not spec_refs
        or any(not isinstance(ref, str) or not ref for ref in spec_refs)
        or len(spec_refs) != len(set(spec_refs))
    ):
        errors.append(
            f"claim registry line {line_number} spec_refs must be a non-empty "
            "list of unique strings"
        )
    else:
        for index, ref in enumerate(spec_refs):
            rel = ref.split("#", 1)[0]
            try:
                confined_repo_file(
                    repo,
                    rel,
                    label=f"claim registry line {line_number} spec_refs[{index}]",
                )
            except ValueError as exc:
                errors.append(str(exc))
            match = re.fullmatch(
                r"docs/research_program/long_horizon_rescue/pr([0-9]+)_spec[.]yaml",
                rel,
            )
            if match is not None:
                spec_prs.add(match.group(1))

    evidence_prs: set[str] = set()
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or any(not is_evidence_identity(ref) for ref in evidence_refs)
        or len(evidence_refs) != len(set(evidence_refs))
    ):
        errors.append(
            f"claim registry line {line_number} evidence_refs must be a non-empty "
            "list of unique evidence identities"
        )
    else:
        for ref in evidence_refs:
            match = re.fullmatch(r"E-PR([0-9]+)(?:-.+)", ref)
            if match is not None:
                evidence_prs.add(match.group(1))

    if spec_prs and not evidence_prs:
        expected = ", ".join(f"E-PR{number}-*" for number in sorted(spec_prs))
        errors.append(
            f"claim registry line {line_number} has no PR-scoped evidence "
            f"reference; expected one of {expected}"
        )
    foreign_prs = evidence_prs - spec_prs
    if spec_prs and foreign_prs:
        foreign = ", ".join(f"E-PR{number}-*" for number in sorted(foreign_prs))
        errors.append(
            f"claim registry line {line_number} has evidence references without "
            f"matching PR-scoped specs: {foreign}"
        )


def _registered_claim_ids(repo: Path) -> tuple[set[str], list[str]]:
    """Load claim identities only; stored scientific/gate status is not authority."""

    path = repo / ".agent-harness" / "context" / "CLAIM_REGISTRY.jsonl"
    if not path.is_file() or path.is_symlink():
        return set(), ["canonical claim registry is missing or not a regular file"]
    claims: set[str] = set()
    errors: list[str] = []
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"claim registry line {line_number} is invalid JSON: {exc}")
            continue
        claim_id = row.get("claim_id") if isinstance(row, Mapping) else None
        if not is_safe_identifier(claim_id):
            errors.append(
                f"claim registry line {line_number} has a missing or unsafe claim_id"
            )
            continue
        claim_text = str(claim_id)
        if claim_text in claims:
            errors.append(f"claim registry has duplicate claim_id: {claim_text}")
        claims.add(claim_text)
    if not claims:
        errors.append("canonical claim registry contains no claim identities")
    return claims, errors


def validate_claim_registry(repo: Path) -> list[str]:
    """Return current referential errors; stored claim/gate status is ignored."""

    _, errors = _registered_claim_ids(repo)
    path = repo / ".agent-harness" / "context" / "CLAIM_REGISTRY.jsonl"
    if not path.is_file() or path.is_symlink():
        return errors
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(row, Mapping) and is_safe_identifier(row.get("claim_id")):
            _validate_claim_references(
                repo,
                row,
                line_number=line_number,
                errors=errors,
            )
    return errors


def _validate_input_list(
    repo: Path | None,
    values: object,
    *,
    field: str,
    errors: list[str],
    require_hash: bool = False,
) -> None:
    if not isinstance(values, list) or not values:
        errors.append(f"assignment {field} must be a non-empty list")
        return
    for index, item in enumerate(values):
        if not isinstance(item, Mapping):
            errors.append(
                f"assignment {field}[{index}] must contain a path and may "
                "contain sha256"
            )
            continue
        rel = item.get("path")
        has_sha = "sha256" in item
        sha = item.get("sha256")
        if not isinstance(rel, str) or not rel:
            errors.append(f"assignment {field}[{index}] lacks a path")
            continue
        rel_path = Path(rel)
        if (
            rel_path.is_absolute()
            or ".." in rel_path.parts
            or "\\" in rel
            or rel_path.as_posix() != rel
        ):
            errors.append(
                f"assignment {field}[{index}] path must be canonical and "
                f"repository-relative: {rel}"
            )
            continue
        if require_hash and not has_sha:
            errors.append(f"assignment {field}[{index}] requires a sha256")
            continue
        if has_sha and (
            not isinstance(sha, str) or SHA256_RE.fullmatch(sha) is None
        ):
            errors.append(f"assignment {field}[{index}] has an invalid sha256")
            continue
        if repo is not None:
            path = repo / rel_path
            probe = repo
            traverses_symlink = False
            for part in rel_path.parts:
                probe = probe / part
                if probe.is_symlink():
                    traverses_symlink = True
                    break
            if traverses_symlink:
                errors.append(
                    f"assignment {field}[{index}] path traverses a symlink: {rel}"
                )
            elif not path.is_file():
                errors.append(f"assignment {field}[{index}] path missing: {rel}")
            elif has_sha and hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                errors.append(
                    f"assignment {field}[{index}] hash mismatch (stale input): {rel}"
                )


def validate_assignment_payload(
    assignment: object,
    *,
    run_id: str,
    context_version: str,
    assignment_id: str | None = None,
    registry: Mapping[str, Any] | None = None,
    historical_runs: set[str] | None = None,
    repo: Path | None = None,
) -> list[str]:
    """Fail-closed assignment validation (audit H3).

    Schema v2 is mandatory for new runs: unknown ``agent_type`` (not in the
    unique profile registry), empty ``claim_ids`` / ``required_inputs`` /
    ``allowed_tools`` / ``required_outputs``, a missing ``risk_tier``, an
    ``independent`` discovery mode without a rationale, or a CAS agent
    without an axis-bound contract are all registration errors. Runs listed
    in ``.agent-harness/HISTORICAL_RUNS.json`` keep validating under the
    frozen v1 rules so pre-PR-124 envelopes stay auditable.
    """

    errors: list[str] = []
    if not isinstance(assignment, Mapping):
        return ["assignment is not a JSON object"]
    if historical_runs is None:
        historical_runs = historical_run_ids(repo if repo is not None else root())
    historical = run_id in historical_runs

    actual_id = assignment.get("assignment_id")
    run_plan: Mapping[str, Any] | None = None
    if not historical and repo is not None:
        plan_path = repo / ".agent-harness" / "runs" / run_id / "RUN_PLAN.json"
        try:
            loaded_plan = load_json(plan_path)
        except (OSError, json.JSONDecodeError):
            loaded_plan = None
        if isinstance(loaded_plan, Mapping):
            run_plan = loaded_plan
    expected_schema = (
        1
        if historical
        else 3
        if run_plan is not None and run_plan.get("schema_version") == 2
        else 2
    )
    if assignment.get("schema_version") != expected_schema:
        errors.append(f"assignment schema_version must equal {expected_schema}")
    if assignment.get("run_id") != run_id:
        errors.append("assignment run_id does not match ACTIVE_RUN")
    if not is_safe_identifier(actual_id):
        errors.append("assignment_id is missing or unsafe")
    if assignment_id is not None and actual_id != assignment_id:
        errors.append("assignment_id does not match the registered filename")
    if assignment.get("context_version") != context_version:
        errors.append("assignment context_version is stale")
    agent_type = assignment.get("agent_type")
    if not isinstance(agent_type, str) or not agent_type:
        errors.append("assignment agent_type must be non-empty")
    claim_ids = assignment.get("claim_ids")
    if not isinstance(claim_ids, list) or any(
        not is_safe_identifier(item) for item in claim_ids
    ):
        errors.append("assignment claim_ids must be a list of safe identifiers")
    elif len(set(claim_ids)) != len(claim_ids):
        errors.append("assignment claim_ids must be unique")
    if is_safe_identifier(actual_id):
        expected_path = declared_result_path(run_id, str(actual_id))
        if assignment.get("result_path") != expected_path:
            errors.append("assignment result_path is not the canonical unique path")
    if historical:
        return errors

    # --- v2 fail-closed additions -------------------------------------
    if isinstance(claim_ids, list) and not claim_ids:
        errors.append("assignment claim_ids must not be empty")
    seal = assignment.get("assignment_sha256")
    if not isinstance(seal, str) or SHA256_RE.fullmatch(seal) is None:
        errors.append("assignment assignment_sha256 must be a lowercase SHA-256")
    elif seal != assignment_sha256(assignment):
        errors.append("assignment_sha256 does not match the sealed assignment payload")
    if repo is None:
        errors.append("strict assignment validation requires the repository root")
    else:
        registered_claims, claim_registry_errors = _registered_claim_ids(repo)
        errors.extend(claim_registry_errors)
        if isinstance(claim_ids, list):
            for claim_id in claim_ids:
                if (
                    isinstance(claim_id, str)
                    and claim_id not in registered_claims
                    and not is_run_local_claim_id(claim_id, run_id)
                ):
                    errors.append(f"assignment claim_id is not registered: {claim_id}")
    if registry is None:
        try:
            from profile_registry import load_profile_registry

            registry = load_profile_registry(repo if repo is not None else root())
        except Exception as exc:  # fail closed: no registry, no registration
            errors.append(f"profile registry unavailable: {exc}")
            registry = {}
    if isinstance(agent_type, str) and agent_type and registry is not None:
        if agent_type not in registry:
            errors.append(
                f"assignment agent_type {agent_type!r} is not an installed profile"
            )
    if assignment.get("risk_tier") not in RISK_TIERS:
        errors.append(f"assignment risk_tier must be one of {sorted(RISK_TIERS)}")
    _validate_input_list(
        repo, assignment.get("required_inputs"), field="required_inputs", errors=errors
    )
    allowed_tools = assignment.get("allowed_tools")
    if (
        not isinstance(allowed_tools, list)
        or not allowed_tools
        or any(not isinstance(item, str) or not item for item in allowed_tools)
    ):
        errors.append("assignment allowed_tools must be a non-empty string list")
    required_outputs = assignment.get("required_outputs")
    if (
        not isinstance(required_outputs, list)
        or not required_outputs
        or any(not isinstance(item, str) or not item for item in required_outputs)
    ):
        errors.append("assignment required_outputs must be a non-empty string list")
    if assignment.get("discovery_mode") == "independent" and not str(
        assignment.get("independence_rationale") or ""
    ).strip():
        errors.append(
            "discovery_mode=independent requires a non-empty independence_rationale"
        )
    if isinstance(agent_type, str) and agent_type.startswith("cas_"):
        if assignment.get("cas_axis") not in CAS_AXES:
            errors.append(
                f"CAS assignment requires cas_axis in {sorted(CAS_AXES)}"
            )
        contract = assignment.get("cas_contract")
        if not isinstance(contract, Mapping):
            errors.append("CAS assignment requires cas_contract {path, sha256}")
        else:
            _validate_input_list(
                repo,
                [contract],
                field="cas_contract",
                errors=errors,
                require_hash=True,
            )
    if expected_schema == 3:
        if run_plan is None:
            errors.append("schema-v3 assignment requires a schema-v2 RUN_PLAN")
        else:
            for field in (
                "work_unit_id",
                "change_set_id",
                "publication_group_id",
            ):
                if assignment.get(field) != run_plan.get(field):
                    errors.append(
                        f"assignment {field} does not match the registered RUN_PLAN"
                    )
        workflow_role = assignment.get("workflow_role")
        if workflow_role not in {"implementer", "reviewer", "adjudicator"}:
            errors.append(
                "assignment workflow_role must be implementer, reviewer, or adjudicator"
            )
        if workflow_role == "publisher":
            errors.append("publisher is not a subagent workflow role")
        if (
            workflow_role in {"reviewer", "adjudicator"}
            and run_plan is not None
            and assignment.get("candidate_binding")
            != run_plan.get("candidate_binding")
        ):
            errors.append(
                "review assignment candidate_binding does not match the "
                "frozen RUN_PLAN candidate"
            )
        binding_errors = validate_candidate_binding(
            assignment.get("candidate_binding"),
            repo=repo if repo is not None else root(),
            require_frozen=workflow_role in {"reviewer", "adjudicator"},
        )
        errors.extend(f"assignment {item}" for item in binding_errors)
        binding = assignment.get("candidate_binding")
        if (
            workflow_role == "implementer"
            and isinstance(binding, Mapping)
            and binding.get("state") != "mutable"
        ):
            errors.append(
                "implementer assignment cannot mutate an already frozen candidate"
            )
        if (
            workflow_role == "reviewer"
            and isinstance(agent_type, str)
            and registry is not None
            and agent_type in registry
            and registry[agent_type].get("sandbox_mode") != "read-only"
        ):
            errors.append("reviewer workflow_role requires a read-only profile")
    return errors


def compute_effective_context_sha256(
    index: Mapping[str, Any],
    assignment_bytes: bytes,
    role_files: list[tuple[str, str]],
    receipt_fields: Mapping[str, Any],
) -> str:
    """Bind every effective launch input into one hash (audit H2).

    Covers the Tier-0 pack semantic fields (never ``built_at``), the sealed
    assignment bytes (which embed required-input hashes), per-role context
    file hashes, and the launcher/profile/delivery receipt fields. Any drift
    in any component blocks launch.
    """

    digest = hashlib.sha256()
    semantic = {
        "context_version": index.get("context_version"),
        "shared_files": index.get("shared_files"),
        "pack_files": index.get("pack_files"),
        "live_sources": index.get("live_sources"),
        "file_hashes": index.get("file_hashes"),
        "max_injected_chars": index.get("max_injected_chars"),
    }
    digest.update(json.dumps(semantic, sort_keys=True).encode("utf-8"))
    digest.update(b"\0")
    digest.update(assignment_bytes)
    digest.update(b"\0")
    for rel, sha in sorted(role_files):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha.encode("utf-8"))
        digest.update(b"\0")
    receipt_semantic = {
        "context_delivery_mode": receipt_fields.get("context_delivery_mode"),
        "requested_profile": receipt_fields.get("requested_profile"),
        "actual_profile": receipt_fields.get("actual_profile"),
        "config_sha256": receipt_fields.get("config_sha256"),
        "model": receipt_fields.get("model"),
        "sandbox": receipt_fields.get("sandbox"),
        "fork_mode": receipt_fields.get("fork_mode"),
        "attested": receipt_fields.get("attested"),
        "evidence_origin": receipt_fields.get("evidence_origin"),
    }
    digest.update(json.dumps(receipt_semantic, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def role_file_hashes(
    repo: Path, index: Mapping[str, Any], agent_type: str
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    role_files = index.get("role_files", {})
    if not isinstance(role_files, Mapping):
        return rows
    for rel in role_files.get(agent_type, []):
        path = repo / str(rel)
        digest = (
            hashlib.sha256(path.read_bytes()).hexdigest()
            if path.is_file() and not path.is_symlink()
            else "MISSING"
        )
        rows.append((str(rel), digest))
    return rows
