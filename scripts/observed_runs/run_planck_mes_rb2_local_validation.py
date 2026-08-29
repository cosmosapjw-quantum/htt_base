#!/usr/bin/env python3
"""Run the RB2 workflow-equivalent gate locally, without GitHub Actions.

This is an explicit exact-head execution path.  It is neither a GitHub CI
result nor scientific claim authority.  The fixed command registry is derived
from the three tracked workflow files at the accepted RB2 head.  Checkout,
setup-action, and artifact-upload transport are replaced by a clean detached
worktree check, local virtual environments, and private command logs.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Mapping, Sequence


RB2_HEAD = "0ae0e70791273c13c7b80ac835232c3c63555c5b"
RB2_TREE = "680795842feafa8028b8e2b9fe8e1086c5f12280"
FORMAT = "HTT_RB2_EXACT_HEAD_LOCAL_VALIDATION_V1"
AUTHORITY = "EXACT_HEAD_LOCAL_EXECUTION_NOT_GITHUB_CI"
RECEIPT_NAME = "local_exact_head_validation.json"
EXPECTED_WORKFLOW_SHA256 = {
    ".github/workflows/repository-integrity.yml": (
        "sha256:d4175f55f9f326bd37ed8f26d69e09433c025425ffbe7a73781c4c96cad81efc"
    ),
    ".github/workflows/pr04-theory-gates.yml": (
        "sha256:b181eb723f44a02ef0d7152364e3b2b4fd38c17c03f5296d4eb0b601c641c9b6"
    ),
    ".github/workflows/pr07-audit-repair-gates.yml": (
        "sha256:485d6230ac3159843abc04b71086f91f5b357eda8277f02c6caf74be198b53f1"
    ),
}
_OID = re.compile(r"^[0-9a-f]{40}$")
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class LocalValidationError(RuntimeError):
    """The explicit exact-head local execution evidence is not admissible."""


def _step(
    step_id: str,
    *argv: str,
    cwd: str = "{repo}",
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    base_env = {
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "RUNNER_TEMP": "{runner_temp}",
    }
    base_env.update(dict(env or {}))
    return {
        "step_id": step_id,
        "argv": tuple(argv),
        "cwd": cwd,
        "env": base_env,
    }


def _venv_steps(prefix: str, install: Sequence[Sequence[str]]) -> list[dict[str, object]]:
    steps = [
        _step(f"{prefix}.venv", "{host_python}", "-m", "venv", "{venv}"),
    ]
    for index, arguments in enumerate(install, start=1):
        steps.append(
            _step(f"{prefix}.install-{index}", "{python}", "-m", "pip", *arguments)
        )
    return steps


_REPOSITORY_STEPS = [
    *_venv_steps(
        "repository",
        (
            ("install", "pytest>=8,<9", "PyYAML>=6,<7", "numpy>=1.26,<3"),
            ("install", "healpy==1.19.0"),
            ("install", "-e", "{repo}/htt"),
        ),
    ),
    _step(
        "repository.validate-harness",
        "{python}",
        ".agent-harness/scripts/validate_harness.py",
    ),
    _step(
        "repository.sync-dag",
        "{python}",
        "scripts/codex_harness/sync_pr_dag_mirrors.py",
        "--check",
    ),
    _step(
        "repository.validate-dag",
        "{python}",
        "scripts/codex_harness/validate_pr_dag.py",
        "docs/codex_handoff/pr_backlog.yaml",
        "--status",
        "docs/codex_handoff/pr_status.yaml",
        "--strict-rescue-slice",
    ),
    _step(
        "repository.harness-contracts",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "scripts/codex_harness/test_repository_integrity_workflow.py",
        "scripts/codex_harness/test_harness_enforcement.py",
        "scripts/codex_harness/test_codex_assets.py",
    ),
    _step(
        "repository.mes-recovery-validator",
        "{python}",
        "scripts/validate_mes_methodology_recovery_contract.py",
        "--json",
    ),
    _step(
        "repository.mes-recovery-contracts",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/contracts/test_mes_methodology_recovery_contract.py",
    ),
    _step(
        "repository.mes-stack-validator",
        "{python}",
        "scripts/validate_mes_stack_integration_plan.py",
    ),
    _step(
        "repository.mes-stack-contracts",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/contracts/test_mes_stack_integration_plan.py",
    ),
    _step(
        "repository.extended-data-validator",
        "{python}",
        "scripts/validate_planck_mes_extended_data_plan.py",
    ),
    _step(
        "repository.extended-data-contracts",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/contracts/test_planck_mes_extended_data_plan.py",
    ),
    _step(
        "repository.irrep-plan-validator",
        "{python}",
        "scripts/validate_planck_mes_irrep_global_formalism_plan.py",
        "--no-git",
    ),
    _step(
        "repository.irrep-plan-contracts",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/contracts/test_planck_mes_irrep_global_formalism_plan.py",
    ),
    _step(
        "repository.wu002-transition-validator",
        "{python}",
        "scripts/validate_planck_mes_pmg_wu002_transition.py",
        "--check-git",
    ),
    _step(
        "repository.wu002-transition-contracts",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/contracts/test_planck_mes_pmg_wu002_transition.py",
    ),
    _step(
        "repository.observational-quarantine",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/contracts/test_obsdata_figures.py",
        "tests/obsstat/test_pr151_invalidation_boundary.py",
        "tests/contracts/test_pr303_pr289_integration.py",
    ),
    _step(
        "repository.pr304-authorization",
        "{python}",
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        "tests/contracts/test_human_execution_authorization.py",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr304-bayesian",
        "{python}",
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        "tests/htt/test_bayesian_production.py",
        "tests/contracts/test_observed_bayesian_readiness.py",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr304-identity",
        "{python}",
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        "tests/contracts/test_data_identity_registry_v2.py",
        "tests/contracts/test_pr303_pr289_integration.py",
        "-k",
        "not test_receipt_generation_identity_is_interpreter_alias_independent",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr304-preflight",
        "{python}",
        "-B",
        "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "preflight",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr304-sync",
        "{python}",
        "-B",
        "scripts/codex_harness/sync_pr_dag_mirrors.py",
        "--check",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr304-dag",
        "{python}",
        "-B",
        "scripts/codex_harness/validate_pr_dag.py",
        "docs/codex_handoff/pr_backlog.yaml",
        "--status",
        "docs/codex_handoff/pr_status.yaml",
        "--strict-rescue-slice",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr304-claim-language",
        "{python}",
        "-B",
        "scripts/check_claim_language.py",
        "--strict-missing",
        "htt/src/common/human_execution_authorization.py",
        "htt/htt/htt/infer/bayesian_production.py",
        "docs/PR_DELTAS/pr-304.md",
        "docs/research_program/post_pr275/pr304_spec.yaml",
        "docs/research_program/post_pr275/human_authority_registry.json",
        "docs/research_program/post_pr275/human_authority_registry.signature.json",
        "docs/research_program/post_pr275/trusted_launcher_contract.md",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step("repository.pr304-diff-check", "git", "diff", "--check"),
    _step(
        "repository.pr309-tests",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/integration/test_jwst_sn_current_stack.py",
        "tests/contracts/test_authorized_observational_program.py",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr309-synthetic",
        "{python}",
        "scripts/observed_runs/run_jwst_sn.py",
        "--synthetic-profile",
        "--output",
        "{runner_temp}/pr309-jwst-synthetic.json",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr310-321-tests",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/integration/test_hsc_kids_current_stack.py",
        "tests/contracts/test_pr321_reaudit_plan.py",
        "tests/contracts/test_authorized_observational_program.py",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr310-synthetic",
        "{python}",
        "scripts/observed_runs/run_hsc_kids.py",
        "--synthetic-profile",
        "--rows",
        "full",
        "--output",
        "{runner_temp}/pr310-hsc-kids-synthetic.json",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.planck-pr324",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/integration/test_planck_pr3_admission_preparation.py",
        "tests/integration/test_planck_pr3_current_stack.py",
        "tests/integration/test_planck_pr3_operator.py",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.planck-pr324-claims",
        "{python}",
        "scripts/check_claim_language.py",
        "--strict-missing",
        "docs/PR_DELTAS/pr-315.md",
        "docs/research_program/post_pr275/pr315_planck_smica_rerun_report.md",
    ),
    _step(
        "repository.pr311-tests",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "tests/integration/test_desi_successor_formalism.py",
        "tests/obsstat/test_pr151_invalidation_boundary.py",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.pr311-synthetic",
        "{python}",
        "scripts/observed_runs/run_desi_bgs_bright.py",
        "--synthetic-profile",
        "--rows",
        "full",
        "--output",
        "{runner_temp}/pr311-desi-synthetic.json",
        env={"PYTHONPATH": "{repo}/htt:{repo}/htt/src:{repo}/htt/htt"},
    ),
    _step(
        "repository.architecture",
        "{python}",
        "-m",
        "pytest",
        "-q",
        "scripts/architecture/test_import_boundaries.py",
    ),
]

_PACKAGE_STEPS = [
    *_venv_steps(
        "package",
        (
            ("install", "setuptools>=68", "wheel", "packaging"),
            ("install", "-e", "{repo}/htt[dev]"),
        ),
    ),
    _step(
        "package.compile",
        "{python}",
        "-m",
        "compileall",
        "-q",
        ".agent-harness/scripts",
        "scripts/codex_harness",
        "htt",
    ),
    _step(
        "package.compile-architecture",
        "{python}",
        "-m",
        "compileall",
        "-q",
        "scripts/architecture",
    ),
    _step(
        "package.imports",
        "{python}",
        "-c",
        "import bass, common, htt, mio, obsstat, tsc, tsc_legacy; print('IMPORT_OK')",
    ),
    _step(
        "package.smoke-contract",
        "{python}",
        "scripts/codex_harness/run_subset.py",
        "package",
        "--python",
        "{python}",
    ),
]

_RUST_STEPS = [
    *_venv_steps("rust", ()),
    _step("rust.install-toolchain", "{rustup}", "toolchain", "install", "1.94.1", "--profile", "minimal"),
    _step("rust.rustc-version", "{rustc}", "+1.94.1", "--version"),
    _step("rust.cargo-version", "{cargo}", "+1.94.1", "--version"),
    _step(
        "rust.cargo-check",
        "{cargo}",
        "+1.94.1",
        "check",
        "--locked",
        "--lib",
        env={"PYO3_PYTHON": "{python}"},
    ),
]


def _pr04_steps() -> list[dict[str, object]]:
    return [
        *_venv_steps(
            "pr04",
            (
                ("install", "--upgrade", "pip"),
                ("install", "-e", "{repo}/htt[dev]"),
            ),
        ),
        _step("pr04.compile", "{python}", "-m", "compileall", "-q", "htt"),
        _step(
            "pr04.imports",
            "{python}",
            "-c",
            "import htt; import htt.htt.core.ssot; import bass; import mio; print('IMPORT_OK')",
            env={"PYTHONPATH": "{repo}:{repo}/htt"},
        ),
        _step(
            "pr04.theorem-gates",
            "{python}",
            "-m",
            "unittest",
            "discover",
            "-s",
            "research_gates/pr04/tests",
            "-p",
            "test_pr04_*.py",
            "-v",
            env={"PYTHONPATH": "{repo}:{repo}/htt"},
        ),
        _step(
            "pr04.architecture",
            "{python}",
            "scripts/architecture/check_import_boundaries.py",
            "--repo",
            ".",
        ),
        _step(
            "pr04.fast-regression",
            "{python}",
            "-m",
            "pytest",
            "-m",
            "smoke or fast or ci",
            "-q",
            cwd="{repo}/htt",
        ),
        _step(
            "pr04.lowell",
            "{python}",
            "-m",
            "pytest",
            "tests/obsstat/test_lowell_poles.py",
            "tests/obsstat/test_shell_alms.py",
            "-q",
        ),
    ]


_PR07_STEPS = [
    *_venv_steps(
        "pr07",
        (
            ("install", "--upgrade", "pip"),
            ("install", "-e", "{repo}/htt[dev]"),
        ),
    ),
    _step(
        "pr07.forbidden-dependencies",
        "{python}",
        "research_gates/pr04/tools/verify_forbidden_dependencies.py",
        "--repo",
        ".",
        env={"PYTHONPATH": "{repo}:{repo}/htt:{repo}/htt/htt:{repo}/htt/src"},
    ),
    _step(
        "pr07.pr04-regression",
        "{python}",
        "-m",
        "unittest",
        "discover",
        "-s",
        "research_gates/pr04/tests",
        "-p",
        "test_pr04_*.py",
        "-v",
        env={"PYTHONPATH": "{repo}:{repo}/htt:{repo}/htt/htt:{repo}/htt/src"},
    ),
    _step(
        "pr07.repair-gates",
        "{python}",
        "-m",
        "unittest",
        "discover",
        "-s",
        "research_gates/pr07/tests",
        "-p",
        "test_pr07_*.py",
        "-v",
        env={"PYTHONPATH": "{repo}:{repo}/htt:{repo}/htt/htt:{repo}/htt/src"},
    ),
    _step(
        "pr07.synthetic-and-cove",
        "{python}",
        "scripts/run_pr07_experiments.py",
        env={"PYTHONPATH": "{repo}:{repo}/htt:{repo}/htt/htt:{repo}/htt/src"},
    ),
    _step(
        "pr07.cove",
        "{python}",
        "scripts/cove_verify_pr07.py",
        env={"PYTHONPATH": "{repo}:{repo}/htt:{repo}/htt/htt:{repo}/htt/src"},
    ),
    _step(
        "pr07.contracts",
        "{python}",
        "-m",
        "pytest",
        "tests/contracts/test_pr07_audit_repair.py",
        "-q",
        env={"PYTHONPATH": "{repo}:{repo}/htt:{repo}/htt/htt:{repo}/htt/src"},
    ),
    _step(
        "pr07.checksums",
        "sha256sum",
        "docs/generated/pr07_paper_a.json",
        "docs/generated/pr07_paper_b.json",
        "docs/generated/pr07_k1_global_synthetic.json",
        "docs/generated/pr07_k5_hierarchical_synthetic.json",
        "docs/generated/pr07_k6_affine_ensemble_synthetic.json",
        "docs/generated/pr07_cove_report.json",
        env={"PYTHONPATH": "{repo}:{repo}/htt:{repo}/htt/htt:{repo}/htt/src"},
    ),
]

COMMAND_REGISTRY = (
    {"job_id": "repository-contracts", "python_version": "3.12", "steps": tuple(_REPOSITORY_STEPS)},
    {"job_id": "python-package-smoke", "python_version": "3.12", "steps": tuple(_PACKAGE_STEPS)},
    {"job_id": "rust-compile", "python_version": "3.12", "steps": tuple(_RUST_STEPS)},
    *(
        {
            "job_id": f"pr04-python-{version}",
            "python_version": version,
            "steps": tuple(_pr04_steps()),
        }
        for version in ("3.10", "3.11", "3.12", "3.13")
    ),
    {"job_id": "pr07-portable-gates", "python_version": "3.12", "steps": tuple(_PR07_STEPS)},
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def command_registry_id() -> str:
    return _sha256_bytes(b"htt-rb2-local-command-registry\0" + _canonical_bytes(COMMAND_REGISTRY))


def receipt_content_id(payload: Mapping[str, object]) -> str:
    content = dict(payload)
    content.pop("content_id", None)
    return _sha256_bytes(b"htt-rb2-local-validation-receipt\0" + _canonical_bytes(content))


def render_value(value: str, bindings: Mapping[str, str]) -> str:
    try:
        return value.format_map(dict(bindings))
    except KeyError as exc:
        raise LocalValidationError(f"command binding is missing: {exc.args[0]}") from exc


def render_argv(argv: Sequence[str], bindings: Mapping[str, str]) -> list[str]:
    return [render_value(value, bindings) for value in argv]


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode:
        raise LocalValidationError("exact-head checkout Git identity is unavailable")
    return result.stdout.strip()


def _workflow_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in EXPECTED_WORKFLOW_SHA256:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise LocalValidationError("tracked workflow source is missing or unsafe")
        hashes[relative] = _file_sha256(path)
    return hashes


def _assert_private_regular_file(path: Path, repo_root: Path, label: str) -> Path:
    raw = Path(path)
    if not raw.is_absolute() or raw.is_symlink() or not raw.is_file():
        raise LocalValidationError(f"{label} must be an absolute regular file")
    resolved = raw.resolve()
    if resolved.is_relative_to(repo_root.resolve()):
        raise LocalValidationError(f"{label} must remain outside the repository")
    return resolved


def _validate_tool_versions(value: object) -> None:
    expected = {
        "python3.10": "Python 3.10",
        "python3.11": "Python 3.11",
        "python3.12": "Python 3.12",
        "python3.13": "Python 3.13",
        "rustc+1.94.1": "rustc 1.94.1",
        "cargo+1.94.1": "cargo 1.94.1",
    }
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise LocalValidationError("local tool-version inventory differs")
    if any(not isinstance(value[key], str) or not value[key].startswith(prefix) for key, prefix in expected.items()):
        raise LocalValidationError("local tool version differs from the workflow matrix")


def require_local_validation(
    receipt_path: Path,
    *,
    expected_head: str = RB2_HEAD,
    expected_tree: str = RB2_TREE,
    repo_root: Path,
    verify_checkout: bool = True,
) -> dict[str, object]:
    """Validate private local evidence; never infer GitHub CI success from it."""
    if _OID.fullmatch(expected_head) is None or _OID.fullmatch(expected_tree) is None:
        raise LocalValidationError("expected RB2 Git identity is malformed")
    receipt = _assert_private_regular_file(Path(receipt_path), Path(repo_root), "local receipt")
    try:
        payload = json.loads(receipt.read_text(encoding="ascii"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise LocalValidationError("local validation receipt is unreadable") from exc
    if not isinstance(payload, dict):
        raise LocalValidationError("local validation receipt must be an object")
    expected_scalars = {
        "format": FORMAT,
        "authority": AUTHORITY,
        "github_actions_used": False,
        "head": expected_head,
        "tree": expected_tree,
        "clean_detached_checkout": True,
        "pre_status": "",
        "post_status": "",
        "workflow_sources": EXPECTED_WORKFLOW_SHA256,
        "command_registry_id": command_registry_id(),
        "state": "PASS",
    }
    if any(payload.get(key) != value for key, value in expected_scalars.items()):
        raise LocalValidationError("exact-head local validation identity or state differs")
    if payload.get("content_id") != receipt_content_id(payload):
        raise LocalValidationError("local validation receipt content identity differs")
    _validate_tool_versions(payload.get("tool_versions"))
    recorded_root_value = payload.get("repo_root")
    if not isinstance(recorded_root_value, str) or not Path(recorded_root_value).is_absolute():
        raise LocalValidationError("local validation checkout path is malformed")
    recorded_root = Path(recorded_root_value)
    if verify_checkout:
        if (
            _git(recorded_root, "rev-parse", "HEAD") != expected_head
            or _git(recorded_root, "rev-parse", "HEAD^{tree}") != expected_tree
            or _git(recorded_root, "status", "--porcelain=v1", "--untracked-files=all")
            or _git(recorded_root, "branch", "--show-current")
        ):
            raise LocalValidationError("local validation checkout is not exact, clean, and detached")
        if _workflow_hashes(recorded_root) != EXPECTED_WORKFLOW_SHA256:
            raise LocalValidationError("local validation workflow source bytes differ")
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != len(COMMAND_REGISTRY):
        raise LocalValidationError("local validation job inventory differs")
    for job, expected_job in zip(jobs, COMMAND_REGISTRY, strict=True):
        if not isinstance(job, Mapping):
            raise LocalValidationError("local validation job record is malformed")
        if (
            job.get("job_id") != expected_job["job_id"]
            or job.get("python_version") != expected_job["python_version"]
            or job.get("state") != "PASS"
        ):
            raise LocalValidationError("local validation job identity or state differs")
        bindings = job.get("bindings")
        required_bindings = {
            "repo",
            "runner_temp",
            "venv",
            "python",
            "host_python",
            "rustup",
            "rustc",
            "cargo",
        }
        if not isinstance(bindings, Mapping) or set(bindings) != required_bindings or any(
            not isinstance(value, str) or not Path(value).is_absolute()
            for value in bindings.values()
        ):
            raise LocalValidationError("local validation command bindings differ")
        if bindings["repo"] != recorded_root_value:
            raise LocalValidationError("local validation command repository binding differs")
        expected_steps = expected_job["steps"]
        steps = job.get("steps")
        if not isinstance(steps, list) or len(steps) != len(expected_steps):
            raise LocalValidationError("local validation step inventory differs")
        for step, expected_step in zip(steps, expected_steps, strict=True):
            if not isinstance(step, Mapping):
                raise LocalValidationError("local validation step record is malformed")
            argv_template = list(expected_step["argv"])
            env_template = dict(expected_step.get("env", {}))
            expected_values = {
                "step_id": expected_step["step_id"],
                "argv_template": argv_template,
                "cwd_template": expected_step["cwd"],
                "env_template": env_template,
                "argv": render_argv(argv_template, bindings),
                "cwd": render_value(expected_step["cwd"], bindings),
                "env": {
                    key: render_value(value, bindings)
                    for key, value in env_template.items()
                },
                "returncode": 0,
            }
            if any(step.get(key) != value for key, value in expected_values.items()):
                raise LocalValidationError("local validation command identity or exit state differs")
            for stream in ("stdout", "stderr"):
                digest = step.get(f"{stream}_sha256")
                if not isinstance(digest, str) or _SHA.fullmatch(digest) is None:
                    raise LocalValidationError("local validation log digest is malformed")
                log_value = step.get(f"{stream}_log")
                if not isinstance(log_value, str):
                    raise LocalValidationError("local validation log path is missing")
                log = _assert_private_regular_file(Path(log_value), Path(repo_root), "local command log")
                if _file_sha256(log) != digest:
                    raise LocalValidationError("local validation command log content differs")
    return payload


def _resolve_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise LocalValidationError(f"required local workflow tool is missing: {name}")
    # rustc/cargo are rustup proxy symlinks; resolving them changes argv[0] to
    # ``rustup`` and therefore queries the manager rather than the requested
    # toolchain executable.  Preserve the absolute proxy entrypoint.
    return str(Path(path).absolute())


def _resolve_python(version: str) -> str:
    path = shutil.which(f"python{version}")
    if path is None:
        raise LocalValidationError(
            f"required local workflow tool is missing: python{version}"
        )
    # uv/portable Python launchers are symlinks whose resolved interpreter
    # carries the correct stdlib prefix into ``python -m venv``.
    return str(Path(path).resolve())


def _version(argv: Sequence[str]) -> str:
    result = subprocess.run(argv, text=True, capture_output=True, timeout=60, check=False)
    if result.returncode:
        raise LocalValidationError(f"local workflow tool version failed: {Path(argv[0]).name}")
    return (result.stdout or result.stderr).strip()


def _write_receipt(path: Path, payload: Mapping[str, object]) -> None:
    body = dict(payload)
    body["content_id"] = receipt_content_id(body)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(body, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False)
        + "\n",
        encoding="ascii",
    )
    os.replace(temporary, path)


def prepare_resume_payload(payload: dict[str, object]) -> int:
    """Preserve one failed attempt and carry preceding PASS jobs forward."""
    jobs = payload.get("jobs")
    failure = payload.get("failure")
    attempts = payload.get("failed_attempts", [])
    if (
        payload.get("state") != "FAIL"
        or not isinstance(jobs, list)
        or not jobs
        or not isinstance(failure, str)
        or not isinstance(attempts, list)
        or attempts
    ):
        raise LocalValidationError("local validation is not eligible for one resume")
    failed = [index for index, job in enumerate(jobs) if isinstance(job, Mapping) and job.get("state") == "FAIL"]
    if failed != [len(jobs) - 1]:
        raise LocalValidationError("local validation failure position is not resumable")
    index = failed[0]
    for position, job in enumerate(jobs):
        if not isinstance(job, Mapping) or job.get("job_id") != COMMAND_REGISTRY[position]["job_id"]:
            raise LocalValidationError("local validation resume job identity differs")
        if position < index and job.get("state") != "PASS":
            raise LocalValidationError("local validation resume has an unpassed prefix")
    failed_job = copy.deepcopy(jobs[index])
    payload["failed_attempts"] = [
        {"failure": failure, "job": failed_job}
    ]
    payload["jobs"] = jobs[:index]
    payload.pop("failure", None)
    payload.pop("content_id", None)
    payload["state"] = "RUNNING"
    payload["post_status"] = "PENDING"
    return index


def execute_local_validation(
    repo_root: Path, evidence_dir: Path, *, resume: bool = False
) -> tuple[Path, dict[str, object]]:
    """Execute every fixed local-equivalent job and write one private receipt."""
    repo = Path(repo_root).resolve()
    evidence_raw = Path(evidence_dir)
    if not evidence_raw.is_absolute() or evidence_raw.is_symlink():
        raise LocalValidationError("use an absolute non-symlink local evidence directory")
    if resume and (not evidence_raw.is_dir() or evidence_raw.is_symlink()):
        raise LocalValidationError("resume requires the existing private evidence directory")
    if not resume and evidence_raw.exists():
        raise LocalValidationError("use a new absolute local evidence directory")
    evidence = evidence_raw.resolve()
    if evidence.is_relative_to(repo):
        raise LocalValidationError("local validation evidence must remain outside Git")
    if (
        _git(repo, "rev-parse", "HEAD") != RB2_HEAD
        or _git(repo, "rev-parse", "HEAD^{tree}") != RB2_TREE
        or _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
        or _git(repo, "branch", "--show-current")
    ):
        raise LocalValidationError("execution requires the clean detached exact RB2 checkout")
    workflow_sources = _workflow_hashes(repo)
    if workflow_sources != EXPECTED_WORKFLOW_SHA256:
        raise LocalValidationError("RB2 workflow source bytes differ")
    tools = {
        version: _resolve_python(version)
        for version in ("3.10", "3.11", "3.12", "3.13")
    }
    rustup, rustc, cargo = (_resolve_tool(name) for name in ("rustup", "rustc", "cargo"))
    tool_versions = {
        **{f"python{version}": _version([path, "--version"]) for version, path in tools.items()},
        "rustc+1.94.1": _version([rustc, "+1.94.1", "--version"]),
        "cargo+1.94.1": _version([cargo, "+1.94.1", "--version"]),
    }
    _validate_tool_versions(tool_versions)
    logs = evidence / "logs"
    runtime = evidence / "runtime"
    runner_temp = evidence / "runner-temp"
    receipt = evidence / RECEIPT_NAME
    if resume:
        if any(path.is_symlink() or not path.is_dir() for path in (logs, runtime, runner_temp)):
            raise LocalValidationError("local validation resume directories are missing or unsafe")
        try:
            payload = json.loads(receipt.read_text(encoding="ascii"))
        except (OSError, UnicodeError, ValueError) as exc:
            raise LocalValidationError("failed local receipt is unreadable") from exc
        if not isinstance(payload, dict) or payload.get("content_id") != receipt_content_id(payload):
            raise LocalValidationError("failed local receipt content identity differs")
        required = {
            "format": FORMAT,
            "authority": AUTHORITY,
            "github_actions_used": False,
            "head": RB2_HEAD,
            "tree": RB2_TREE,
            "repo_root": str(repo),
            "clean_detached_checkout": True,
            "pre_status": "",
            "post_status": "",
            "workflow_sources": workflow_sources,
            "command_registry_id": command_registry_id(),
            "tool_versions": tool_versions,
            "state": "FAIL",
        }
        if any(payload.get(key) != value for key, value in required.items()):
            raise LocalValidationError("failed local receipt is not the exact resumable attempt")
        start_index = prepare_resume_payload(payload)
        failed_job_id = str(COMMAND_REGISTRY[start_index]["job_id"])
        failed_runtime = runtime / failed_job_id
        if failed_runtime.exists():
            if failed_runtime.is_symlink() or not failed_runtime.resolve().is_relative_to(runtime.resolve()):
                raise LocalValidationError("failed runtime path is unsafe")
            shutil.rmtree(failed_runtime)
        failed_temp = runner_temp / failed_job_id
        if failed_temp.exists():
            rejected_temp = runner_temp / f"rejected-attempt-1-{failed_job_id}"
            if rejected_temp.exists() or failed_temp.is_symlink():
                raise LocalValidationError("failed runner-temp path is unsafe")
            failed_temp.rename(rejected_temp)
        log_prefix = "resume-1-"
    else:
        evidence.mkdir(parents=True, exist_ok=False)
        logs.mkdir()
        runtime.mkdir()
        runner_temp.mkdir()
        payload = {
            "format": FORMAT,
            "authority": AUTHORITY,
            "github_actions_used": False,
            "head": RB2_HEAD,
            "tree": RB2_TREE,
            "repo_root": str(repo),
            "clean_detached_checkout": True,
            "pre_status": "",
            "post_status": "PENDING",
            "workflow_sources": workflow_sources,
            "command_registry_id": command_registry_id(),
            "tool_versions": tool_versions,
            "jobs": [],
            "state": "RUNNING",
        }
        start_index = 0
        log_prefix = ""
    _write_receipt(receipt, payload)
    failure: str | None = None
    for job in COMMAND_REGISTRY[start_index:]:
        job_id = str(job["job_id"])
        version = str(job["python_version"])
        venv = runtime / job_id
        job_temp = runner_temp / job_id
        job_temp.mkdir()
        bindings = {
            "repo": str(repo),
            "runner_temp": str(job_temp),
            "venv": str(venv),
            "python": str(venv / "bin" / "python"),
            "host_python": tools[version],
            "rustup": rustup,
            "rustc": rustc,
            "cargo": cargo,
        }
        job_record: dict[str, object] = {
            "job_id": job_id,
            "python_version": version,
            "bindings": bindings,
            "state": "RUNNING",
            "steps": [],
        }
        payload["jobs"].append(job_record)
        for index, step in enumerate(job["steps"]):
            step_id = str(step["step_id"])
            argv_template = list(step["argv"])
            env_template = dict(step.get("env", {}))
            argv = render_argv(argv_template, bindings)
            cwd = render_value(str(step["cwd"]), bindings)
            rendered_env = {
                key: render_value(value, bindings) for key, value in env_template.items()
            }
            stdout = logs / f"{log_prefix}{job_id}-{index:02d}-{step_id.replace('.', '_')}.stdout"
            stderr = logs / f"{log_prefix}{job_id}-{index:02d}-{step_id.replace('.', '_')}.stderr"
            print(f"LOCAL_GATE_STEP_START {job_id} {step_id}", flush=True)
            started = time.monotonic()
            try:
                with stdout.open("wb") as stdout_handle, stderr.open("wb") as stderr_handle:
                    result = subprocess.run(
                        argv,
                        cwd=cwd,
                        env={**os.environ, **rendered_env},
                        stdout=stdout_handle,
                        stderr=stderr_handle,
                        timeout=3600,
                        check=False,
                    )
                returncode = result.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                returncode = 124 if isinstance(exc, subprocess.TimeoutExpired) else 127
                with stderr.open("ab") as handle:
                    handle.write(f"\nLOCAL_EXECUTION_ERROR {type(exc).__name__}\n".encode("ascii"))
            step_record = {
                "step_id": step_id,
                "argv_template": argv_template,
                "cwd_template": step["cwd"],
                "env_template": env_template,
                "argv": argv,
                "cwd": cwd,
                "env": rendered_env,
                "returncode": returncode,
                "duration_seconds": round(time.monotonic() - started, 6),
                "stdout_log": str(stdout),
                "stderr_log": str(stderr),
                "stdout_sha256": _file_sha256(stdout),
                "stderr_sha256": _file_sha256(stderr),
            }
            job_record["steps"].append(step_record)
            if returncode:
                job_record["state"] = "FAIL"
                failure = f"{job_id}:{step_id}:exit={returncode}"
                print(f"LOCAL_GATE_STEP_FAIL {failure}", flush=True)
                break
            print(f"LOCAL_GATE_STEP_PASS {job_id} {step_id}", flush=True)
            _write_receipt(receipt, payload)
        if failure:
            break
        job_record["state"] = "PASS"
        _write_receipt(receipt, payload)
    post_status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    post_branch = _git(repo, "branch", "--show-current")
    payload["post_status"] = post_status
    if failure is None and not post_status and not post_branch and len(payload["jobs"]) == len(COMMAND_REGISTRY):
        payload["state"] = "PASS"
        shutil.rmtree(runtime)
    else:
        payload["state"] = "FAIL"
        payload["failure"] = failure or "CHECKOUT_DIRTY_OR_ATTACHED_AFTER_EXECUTION"
    _write_receipt(receipt, payload)
    final = json.loads(receipt.read_text(encoding="ascii"))
    if final.get("state") == "PASS":
        require_local_validation(
            receipt,
            expected_head=RB2_HEAD,
            expected_tree=RB2_TREE,
            repo_root=repo,
            verify_checkout=True,
        )
    return receipt, final


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        receipt, payload = execute_local_validation(
            arguments.repo_root, arguments.evidence_dir, resume=arguments.resume
        )
    except (LocalValidationError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {"state": "BLOCKED_LOCAL_VALIDATION", "error": str(exc)},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 3
    print(
        json.dumps(
            {
                "state": payload.get("state"),
                "head": payload.get("head"),
                "tree": payload.get("tree"),
                "authority": payload.get("authority"),
                "receipt": str(receipt),
                "content_id": payload.get("content_id"),
            },
            sort_keys=True,
        )
    )
    return 0 if payload.get("state") == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
