"""Narrow contract tests for the required repository-integrity workflow.

This is deliberately not a general GitHub Actions schema validator. It guards
only MA-02's concrete bypass classes: reachability, required-check identity and
permission ceiling, and the presence/order of the promised baseline checks.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/repository-integrity.yml"
DEFAULT_BRANCH = "research/pr04-multicomponent"
CHECKOUT_ACTION = "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09"
SETUP_PYTHON_ACTION = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
REQUIRED_JOBS = {
    "repository-contracts": "Repository contracts",
    "python-package-smoke": "Python package smoke",
    "rust-compile": "Rust compile",
}
REQUIRED_COMMANDS = {
    "repository-contracts": (
        "test ! -e .agent-harness/ACTIVE_RUN",
        "test ! -e .agent-harness/runtime/ACTIVE_RUN",
        "python3 .agent-harness/scripts/validate_harness.py",
        "python -m pip install 'pytest>=8,<9' 'PyYAML>=6,<7'",
        "python scripts/codex_harness/sync_pr_dag_mirrors.py --check",
        (
            "python scripts/codex_harness/validate_pr_dag.py "
            "docs/codex_handoff/pr_backlog.yaml "
            "--status docs/codex_handoff/pr_status.yaml --strict-rescue-slice"
        ),
        (
            "python -m pytest -q "
            "scripts/codex_harness/test_repository_integrity_workflow.py "
            "scripts/codex_harness/test_harness_enforcement.py "
            "scripts/codex_harness/test_codex_assets.py"
        ),
    ),
    "python-package-smoke": (
        "python -m pip install 'setuptools>=68' wheel packaging",
        "python -m pip install -e './htt[dev]'",
        ("python -m compileall -q .agent-harness/scripts scripts/codex_harness htt"),
        (
            'python -c "import bass, common, htt, mio, obsstat, tsc, '
            "tsc_legacy; print('IMPORT_OK')\""
        ),
        "python scripts/codex_harness/run_subset.py package --python python",
    ),
    "rust-compile": (
        "rustup toolchain install 1.94.1 --profile minimal",
        "cargo +1.94.1 check --locked --lib",
    ),
}


def _load_workflow() -> dict[str, Any]:
    # BaseLoader preserves the key `on`; YAML 1.1's default resolver treats it
    # as a boolean and would make this contract silently inspect the wrong key.
    payload = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    assert isinstance(payload, dict)
    return payload


def _shell_commands(job: dict[str, Any]) -> list[str]:
    """Return non-comment run lines with YAML continuations normalized."""

    commands: list[str] = []
    for step in job.get("steps", []):
        if not isinstance(step, dict) or "run" not in step:
            continue
        continued: list[str] = []
        for raw_line in str(step["run"]).splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith("\\"):
                continued.append(line[:-1].rstrip())
                continue
            continued.append(line)
            commands.append(" ".join(continued))
            continued = []
        if continued:
            commands.append(" ".join(continued))
    return commands


def _contract_errors(workflow: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if workflow.get("name") != "Repository integrity":
        errors.append("workflow name drifted")

    triggers = workflow.get("on")
    if not isinstance(triggers, dict):
        errors.append("on must be a trigger mapping")
    else:
        required_events = {"push", "pull_request", "workflow_dispatch"}
        if set(triggers) != required_events:
            errors.append(
                "trigger set must be exactly push, pull_request, workflow_dispatch"
            )
        push = triggers.get("push")
        if push != {"branches": [DEFAULT_BRANCH]}:
            errors.append(
                "push must cover only the default branch without extra filters"
            )
        pull_request = triggers.get("pull_request")
        if pull_request not in (None, ""):
            errors.append("pull_request must be unfiltered")
        for event, config in triggers.items():
            if isinstance(config, dict) and ({"paths", "paths-ignore"} & set(config)):
                errors.append(f"{event} must not use path filters")

    if workflow.get("permissions") != {"contents": "read"}:
        errors.append("workflow permissions must be exactly contents: read")
    if "defaults" in workflow:
        errors.append("workflow must not override the runner's fail-fast shell")

    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return [*errors, "jobs must be a mapping"]
    if set(jobs) != set(REQUIRED_JOBS):
        errors.append("job set must match the three stable required checks exactly")

    for job_id, display_name in REQUIRED_JOBS.items():
        job = jobs.get(job_id)
        if not isinstance(job, dict):
            errors.append(f"missing required job {job_id}")
            continue
        if job.get("name") != display_name:
            errors.append(f"required job name drifted: {job_id}")
        if "permissions" in job:
            errors.append(f"{job_id} must not override permissions")
        if "if" in job:
            errors.append(f"{job_id} must not be conditional")
        if "strategy" in job:
            errors.append(f"{job_id} must not use a matrix or strategy")
        if "defaults" in job:
            errors.append(f"{job_id} must not override the runner's fail-fast shell")
        if job.get("continue-on-error") not in (None, "false"):
            errors.append(f"{job_id} must fail closed")

        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{job_id} must have steps")
            continue
        first = steps[0]
        if not isinstance(first, dict) or first.get("uses") != CHECKOUT_ACTION:
            errors.append(f"{job_id} must start with the pinned checkout action")
        elif first.get("with", {}).get("persist-credentials") != "false":
            errors.append(f"{job_id} checkout must not persist credentials")

        for step in steps:
            if not isinstance(step, dict):
                errors.append(f"{job_id} contains a non-mapping step")
                continue
            if step.get("continue-on-error") not in (None, "false"):
                errors.append(f"{job_id} contains a non-blocking required step")
            if "if" in step:
                errors.append(f"{job_id} contains a conditional required step")
            if "shell" in step:
                errors.append(f"{job_id} overrides the fail-fast shell")
            if "run" in step and "|| true" in str(step["run"]):
                errors.append(f"{job_id} masks a command failure")

        setup_steps = [
            step for step in steps if step.get("uses") == SETUP_PYTHON_ACTION
        ]
        if len(setup_steps) != 1:
            errors.append(f"{job_id} must use the pinned Python setup action once")
        elif setup_steps[0].get("with", {}).get("python-version") != "3.12":
            errors.append(f"{job_id} must use Python 3.12")

        commands = _shell_commands(job)
        if any(
            re.match(r"^set\s+\+(?:e|o\s+errexit)(?:\s*;|$)", command)
            for command in commands
        ):
            errors.append(f"{job_id} disables shell fail-fast behavior")
        for required in REQUIRED_COMMANDS[job_id]:
            if required not in commands:
                errors.append(f"{job_id} missing command: {required}")

        if job_id == "repository-contracts":
            first_run = next(
                (step for step in steps if isinstance(step, dict) and "run" in step),
                None,
            )
            if not isinstance(first_run, dict) or (
                "python3 .agent-harness/scripts/validate_harness.py"
                not in str(first_run.get("run", ""))
            ):
                errors.append(
                    "clean-clone harness validation must be the first run step"
                )

    return errors


def test_repository_integrity_workflow_satisfies_minimal_contract() -> None:
    assert _contract_errors(_load_workflow()) == []


@pytest.mark.parametrize(
    "mutation",
    (
        "remove_push",
        "remove_pull_request",
        "add_paths",
        "add_paths_ignore",
        "add_target",
        "add_push_filter",
    ),
)
def test_rejects_trigger_reachability_mutations(mutation: str) -> None:
    workflow = copy.deepcopy(_load_workflow())
    triggers = workflow["on"]
    if mutation == "remove_push":
        del triggers["push"]
    elif mutation == "remove_pull_request":
        del triggers["pull_request"]
    elif mutation == "add_paths":
        triggers["pull_request"] = {"paths": ["htt/**"]}
    elif mutation == "add_paths_ignore":
        triggers["pull_request"] = {"paths-ignore": ["docs/**"]}
    elif mutation == "add_target":
        triggers["pull_request_target"] = ""
    else:
        triggers["push"]["tags"] = ["v*"]

    assert _contract_errors(workflow)


@pytest.mark.parametrize(
    "mutation",
    (
        "rename_job",
        "elevate_permissions",
        "condition_job",
        "continue_job",
        "continue_step",
        "unpin_checkout",
        "add_matrix",
        "add_privileged_job",
        "condition_step",
        "custom_step_shell",
        "job_shell_default",
        "workflow_shell_default",
    ),
)
def test_rejects_identity_and_security_mutations(mutation: str) -> None:
    workflow = copy.deepcopy(_load_workflow())
    job = workflow["jobs"]["repository-contracts"]
    if mutation == "rename_job":
        job["name"] = "Repository checks"
    elif mutation == "elevate_permissions":
        workflow["permissions"] = {"contents": "write"}
    elif mutation == "condition_job":
        job["if"] = "github.actor != 'example'"
    elif mutation == "continue_job":
        job["continue-on-error"] = "true"
    elif mutation == "continue_step":
        job["steps"][-1]["continue-on-error"] = "true"
    elif mutation == "unpin_checkout":
        job["steps"][0]["uses"] = "actions/checkout@v5"
    elif mutation == "add_matrix":
        job["strategy"] = {"matrix": {"python-version": ["3.11", "3.12"]}}
    elif mutation == "add_privileged_job":
        workflow["jobs"]["privileged-extra"] = {
            "name": "Repository contracts",
            "runs-on": "ubuntu-24.04",
            "permissions": {"contents": "write"},
            "steps": [],
        }
    elif mutation == "condition_step":
        job["steps"][-1]["if"] = "false"
    elif mutation == "custom_step_shell":
        job["steps"][-1]["shell"] = "bash {0}"
    elif mutation == "job_shell_default":
        job["defaults"] = {"run": {"shell": "bash {0}"}}
    else:
        workflow["defaults"] = {"run": {"shell": "bash {0}"}}

    assert _contract_errors(workflow)


@pytest.mark.parametrize(
    "job_id, fragment",
    tuple(
        (job_id, fragment)
        for job_id, fragments in REQUIRED_COMMANDS.items()
        for fragment in fragments
    ),
)
def test_rejects_missing_required_capability(job_id: str, fragment: str) -> None:
    workflow = copy.deepcopy(_load_workflow())
    for step in workflow["jobs"][job_id]["steps"]:
        if "run" in step and fragment in _shell_commands({"steps": [step]}):
            step["run"] = "REMOVED_CAPABILITY"
            break
    else:  # The mutation harness itself must fail closed if the command moves.
        raise AssertionError(f"required command was not found: {fragment}")

    assert _contract_errors(workflow)


@pytest.mark.parametrize(
    "mutation",
    (
        "late_clean_clone",
        "metadata_only_rust",
        "echo_rust",
        "disable_errexit",
        "mask_failure",
    ),
)
def test_rejects_order_and_false_pass_mutations(mutation: str) -> None:
    workflow = copy.deepcopy(_load_workflow())
    if mutation == "late_clean_clone":
        steps = workflow["jobs"]["repository-contracts"]["steps"]
        clean_step = steps.pop(1)
        steps.append(clean_step)
    elif mutation == "metadata_only_rust":
        steps = workflow["jobs"]["rust-compile"]["steps"]
        for step in steps:
            if "run" in step and "cargo +1.94.1 check --locked --lib" in step["run"]:
                step["run"] = "cargo +1.94.1 metadata --locked --no-deps"
                break
    elif mutation == "echo_rust":
        steps = workflow["jobs"]["rust-compile"]["steps"]
        for step in steps:
            if "run" in step and "cargo +1.94.1 check --locked --lib" in step["run"]:
                step["run"] = "echo 'cargo +1.94.1 check --locked --lib'"
                break
    elif mutation == "disable_errexit":
        steps = workflow["jobs"]["repository-contracts"]["steps"]
        steps.insert(1, {"name": "Disable failure", "run": "set +e"})
    else:
        steps = workflow["jobs"]["python-package-smoke"]["steps"]
        next(step for step in steps if "run" in step)["run"] += " || true"

    assert _contract_errors(workflow)
