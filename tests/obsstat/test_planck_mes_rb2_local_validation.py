from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RB2_HEAD = "0ae0e70791273c13c7b80ac835232c3c63555c5b"
RB2_TREE = "680795842feafa8028b8e2b9fe8e1086c5f12280"


def api():
    path = (
        ROOT
        / "scripts"
        / "observed_runs"
        / "run_planck_mes_rb2_local_validation.py"
    )
    if not path.is_file():
        pytest.fail("exact-head local validation is not implemented", pytrace=False)
    spec = importlib.util.spec_from_file_location("rb2_local_validation_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_log(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return "sha256:" + __import__("hashlib").sha256(payload).hexdigest()


def valid_receipt(module, tmp_path: Path) -> tuple[Path, dict[str, object]]:
    evidence = tmp_path / "private-evidence"
    logs = evidence / "logs"
    evidence.mkdir()
    jobs = []
    for job in module.COMMAND_REGISTRY:
        bindings = {
            "repo": str(tmp_path / "exact-rb2"),
            "runner_temp": str(evidence / "runner-temp" / job["job_id"]),
            "venv": str(evidence / "runtime" / job["job_id"]),
            "python": str(evidence / "runtime" / job["job_id"] / "bin" / "python"),
            "host_python": f"/usr/bin/python{job['python_version']}",
            "rustup": "/home/test/.cargo/bin/rustup",
            "rustc": "/home/test/.cargo/bin/rustc",
            "cargo": "/home/test/.cargo/bin/cargo",
        }
        steps = []
        for index, step in enumerate(job["steps"]):
            stdout = logs / f"{job['job_id']}-{index:02d}.stdout"
            stderr = logs / f"{job['job_id']}-{index:02d}.stderr"
            steps.append(
                {
                    "step_id": step["step_id"],
                    "argv_template": list(step["argv"]),
                    "cwd_template": step["cwd"],
                    "env_template": dict(step.get("env", {})),
                    "argv": module.render_argv(step["argv"], bindings),
                    "cwd": module.render_value(step["cwd"], bindings),
                    "env": {
                        key: module.render_value(value, bindings)
                        for key, value in step.get("env", {}).items()
                    },
                    "returncode": 0,
                    "stdout_log": str(stdout),
                    "stderr_log": str(stderr),
                    "stdout_sha256": _write_log(stdout, b"green\n"),
                    "stderr_sha256": _write_log(stderr, b""),
                }
            )
        jobs.append(
            {
                "job_id": job["job_id"],
                "python_version": job["python_version"],
                "bindings": bindings,
                "state": "PASS",
                "steps": steps,
            }
        )
    payload = {
        "format": module.FORMAT,
        "authority": "EXACT_HEAD_LOCAL_EXECUTION_NOT_GITHUB_CI",
        "github_actions_used": False,
        "head": RB2_HEAD,
        "tree": RB2_TREE,
        "repo_root": str(tmp_path / "exact-rb2"),
        "clean_detached_checkout": True,
        "pre_status": "",
        "post_status": "",
        "workflow_sources": dict(module.EXPECTED_WORKFLOW_SHA256),
        "command_registry_id": module.command_registry_id(),
        "tool_versions": {
            "python3.10": "Python 3.10.20",
            "python3.11": "Python 3.11.15",
            "python3.12": "Python 3.12.13",
            "python3.13": "Python 3.13.7",
            "rustc+1.94.1": "rustc 1.94.1",
            "cargo+1.94.1": "cargo 1.94.1",
        },
        "jobs": jobs,
        "state": "PASS",
    }
    payload["content_id"] = module.receipt_content_id(payload)
    receipt_path = evidence / "local_exact_head_validation.json"
    receipt_path.write_text(json.dumps(payload, sort_keys=True) + "\n")
    return receipt_path, payload


def test_registry_covers_exact_eight_workflow_jobs_and_versions():
    module = api()
    assert [job["job_id"] for job in module.COMMAND_REGISTRY] == [
        "repository-contracts",
        "python-package-smoke",
        "rust-compile",
        "pr04-python-3.10",
        "pr04-python-3.11",
        "pr04-python-3.12",
        "pr04-python-3.13",
        "pr07-portable-gates",
    ]
    assert [job["python_version"] for job in module.COMMAND_REGISTRY[3:7]] == [
        "3.10",
        "3.11",
        "3.12",
        "3.13",
    ]
    step_ids = {
        step["step_id"]
        for job in module.COMMAND_REGISTRY
        for step in job["steps"]
    }
    assert {
        "repository.validate-harness",
        "repository.planck-pr324",
        "package.smoke-contract",
        "rust.cargo-check",
        "pr04.fast-regression",
        "pr07.synthetic-and-cove",
        "pr07.contracts",
        "pr07.checksums",
    } <= step_ids


def test_matching_private_receipt_is_accepted(tmp_path):
    module = api()
    receipt_path, expected = valid_receipt(module, tmp_path)
    actual = module.require_local_validation(
        receipt_path,
        expected_head=RB2_HEAD,
        expected_tree=RB2_TREE,
        repo_root=ROOT,
        verify_checkout=False,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "inside_repo",
        "wrong_head",
        "wrong_tree",
        "github_actions",
        "wrong_registry",
        "missing_job",
        "failed_step",
        "altered_argv",
        "altered_stdout",
        "wrong_content_id",
    ],
)
def test_local_receipt_fails_closed_for_incomplete_or_altered_evidence(
    tmp_path, mutation
):
    module = api()
    receipt_path, payload = valid_receipt(module, tmp_path)
    if mutation == "missing":
        receipt_path.unlink()
    elif mutation == "inside_repo":
        receipt_path = ROOT / "synthetic-local-validation-receipt.json"
        receipt_path.write_text(json.dumps(payload))
    else:
        changed = copy.deepcopy(payload)
        if mutation == "wrong_head":
            changed["head"] = "f" * 40
        elif mutation == "wrong_tree":
            changed["tree"] = "e" * 40
        elif mutation == "github_actions":
            changed["github_actions_used"] = True
        elif mutation == "wrong_registry":
            changed["command_registry_id"] = "sha256:" + "1" * 64
        elif mutation == "missing_job":
            changed["jobs"].pop()
        elif mutation == "failed_step":
            changed["jobs"][0]["steps"][0]["returncode"] = 1
        elif mutation == "altered_argv":
            changed["jobs"][0]["steps"][0]["argv"].append("--bypass")
        elif mutation == "altered_stdout":
            Path(changed["jobs"][0]["steps"][0]["stdout_log"]).write_bytes(
                b"changed\n"
            )
        elif mutation == "wrong_content_id":
            changed["content_id"] = "sha256:" + "2" * 64
        if mutation not in {"altered_stdout", "wrong_content_id"}:
            changed["content_id"] = module.receipt_content_id(changed)
        receipt_path.write_text(json.dumps(changed, sort_keys=True) + "\n")
    try:
        with pytest.raises((module.LocalValidationError, OSError, ValueError)):
            module.require_local_validation(
                receipt_path,
                expected_head=RB2_HEAD,
                expected_tree=RB2_TREE,
                repo_root=ROOT,
                verify_checkout=False,
            )
    finally:
        if mutation == "inside_repo":
            receipt_path.unlink(missing_ok=True)


def test_checkout_verification_rejects_nonmatching_or_dirty_repository(
    tmp_path, monkeypatch
):
    module = api()
    receipt_path, _ = valid_receipt(module, tmp_path)
    answers = iter([RB2_HEAD, RB2_TREE, "", ""])
    monkeypatch.setattr(module, "_git", lambda *args: next(answers))
    monkeypatch.setattr(
        module, "_workflow_hashes", lambda *args: module.EXPECTED_WORKFLOW_SHA256
    )
    module.require_local_validation(
        receipt_path,
        expected_head=RB2_HEAD,
        expected_tree=RB2_TREE,
        repo_root=ROOT,
        verify_checkout=True,
    )
    answers = iter([RB2_HEAD, RB2_TREE, " M tracked.py", ""])
    monkeypatch.setattr(module, "_git", lambda *args: next(answers))
    with pytest.raises(module.LocalValidationError, match="clean"):
        module.require_local_validation(
            receipt_path,
            expected_head=RB2_HEAD,
            expected_tree=RB2_TREE,
            repo_root=ROOT,
            verify_checkout=True,
        )


def test_tool_resolution_preserves_rustup_proxy_entrypoint(tmp_path, monkeypatch):
    module = api()
    target = tmp_path / "rustup"
    target.write_text("proxy target")
    proxy = tmp_path / "rustc"
    proxy.symlink_to(target)
    monkeypatch.setattr(module.shutil, "which", lambda name: str(proxy))
    assert module._resolve_tool("rustc") == str(proxy.absolute())


def test_python_resolution_follows_portable_interpreter_symlink(tmp_path, monkeypatch):
    module = api()
    target = tmp_path / "cpython" / "bin" / "python3.13"
    target.parent.mkdir(parents=True)
    target.write_text("portable interpreter")
    proxy = tmp_path / "bin" / "python3.13"
    proxy.parent.mkdir()
    proxy.symlink_to(target)
    monkeypatch.setattr(module.shutil, "which", lambda name: str(proxy))
    assert module._resolve_python("3.13") == str(target.resolve())


def test_resume_preserves_failed_attempt_and_carries_completed_jobs():
    module = api()
    completed = {
        "job_id": module.COMMAND_REGISTRY[0]["job_id"],
        "state": "PASS",
        "steps": [{"step_id": "completed"}],
    }
    failed = {
        "job_id": module.COMMAND_REGISTRY[1]["job_id"],
        "state": "FAIL",
        "steps": [{"step_id": "failed", "returncode": 1}],
    }
    payload = {
        "state": "FAIL",
        "failure": "python-package-smoke:failed:exit=1",
        "post_status": "",
        "jobs": [completed, failed],
    }
    start_index = module.prepare_resume_payload(payload)
    assert start_index == 1
    assert payload["jobs"] == [completed]
    assert payload["failed_attempts"] == [
        {
            "failure": "python-package-smoke:failed:exit=1",
            "job": failed,
        }
    ]
    assert payload["state"] == "RUNNING"
    assert payload["post_status"] == "PENDING"
    assert "failure" not in payload
