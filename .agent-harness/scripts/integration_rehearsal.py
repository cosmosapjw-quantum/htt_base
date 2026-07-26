#!/usr/bin/env python3
"""Run the policy-registered commands in a temporary latest-target worktree."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from _harness import root
from publication_integrity import (
    PublicationIntegrityError,
    PYTHON_EXECUTABLE_TOKEN,
    bytes_sha256,
    canonical_sha256,
    git,
    load_publication_policy,
    read_repo_json,
    read_regular_bytes,
    remote_target_sha,
    runtime_output_path,
    utc_now,
    validate_candidate_seal_payload,
    validate_integration_receipt_payload,
    write_json_exclusive,
)


def _clean_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_COUNT",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "COVERAGE_PROCESS_START",
    ):
        environment.pop(name, None)
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_SYSTEM"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_ATTR_NOSYSTEM"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run_required_commands(
    worktree: Path,
    commands: list[Mapping[str, Any]],
    *,
    log_dir: Path,
) -> tuple[list[dict[str, Any]], bool]:
    log_dir.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    all_passed = True
    environment = _clean_environment()
    for command in commands:
        command_id = str(command["id"])
        policy_argv = list(command["argv"])
        executable = policy_argv[0]
        if executable == PYTHON_EXECUTABLE_TOKEN:
            invocation_path = Path(os.path.abspath(sys.executable))
        elif Path(executable).is_absolute():
            invocation_path = Path(executable)
        elif "/" in executable:
            invocation_path = Path(os.path.abspath(worktree / executable))
        else:
            located = shutil.which(executable, path=environment.get("PATH"))
            if located is None:
                raise PublicationIntegrityError(
                    f"integration command {command_id} executable is unavailable"
                )
            invocation_path = Path(os.path.abspath(located))
        try:
            executable_realpath = invocation_path.resolve(strict=True)
        except OSError as exc:
            raise PublicationIntegrityError(
                f"integration command {command_id} executable cannot be resolved: {exc}"
            ) from exc
        executable_bytes = read_regular_bytes(
            executable_realpath,
            field=f"integration command {command_id} executable",
        )
        argv = [str(invocation_path), *policy_argv[1:]]
        started = utc_now()
        timed_out = False
        try:
            completed = subprocess.run(
                argv,
                cwd=worktree,
                env=environment,
                capture_output=True,
                check=False,
                timeout=int(command["timeout_seconds"]),
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = 124
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
        completed_at = utc_now()
        stdout_path = log_dir / f"{command_id}.stdout"
        stderr_path = log_dir / f"{command_id}.stderr"
        stdout_path.write_bytes(stdout)
        stderr_path.write_bytes(stderr)
        row = {
            "id": command_id,
            "policy_argv": policy_argv,
            "argv": argv,
            "executable_path": str(invocation_path),
            "executable_realpath": str(executable_realpath),
            "executable_sha256": bytes_sha256(executable_bytes),
            "timeout_seconds": int(command["timeout_seconds"]),
            "started_at": started,
            "completed_at": completed_at,
            "returncode": returncode,
            "timed_out": timed_out,
            "stdout_sha256": bytes_sha256(stdout),
            "stdout_bytes": len(stdout),
            "stderr_sha256": bytes_sha256(stderr),
            "stderr_bytes": len(stderr),
        }
        rows.append(row)
        if returncode != 0:
            all_passed = False
            break
    return rows, all_passed


def create_receipt(
    repo: Path,
    *,
    seal_path: str,
    output_path: str,
) -> Mapping[str, Any]:
    _, _, seal = read_repo_json(repo, seal_path, field="candidate seal")
    policy_ref = seal.get("integration_policy")
    if not isinstance(policy_ref, Mapping):
        raise PublicationIntegrityError("candidate seal lacks integration_policy")
    _, policy = load_publication_policy(
        repo,
        policy_ref.get("path"),
        expected_sha256=str(policy_ref.get("sha256") or ""),
    )
    environment = _clean_environment()
    remote = str(seal.get("target_remote") or "")
    branch = str(seal.get("target_branch") or "")
    live_sha = remote_target_sha(repo, remote, branch)
    git(
        repo,
        "fetch",
        "--no-tags",
        "--no-recurse-submodules",
        remote,
        f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}",
        env=environment,
    )
    seal_errors = validate_candidate_seal_payload(seal, repo=repo)
    if seal_errors:
        raise PublicationIntegrityError("; ".join(seal_errors))
    if live_sha != seal.get("base_sha"):
        raise PublicationIntegrityError(
            "target moved after candidate freeze; rebase, reseal, and re-review"
        )

    output = runtime_output_path(
        repo, output_path, field="integration receipt output"
    )
    log_dir = output.parent / (output.stem + ".logs")
    if log_dir.exists() or log_dir.is_symlink():
        raise PublicationIntegrityError(f"refusing to overwrite integration logs: {log_dir}")

    temp_parent = Path(tempfile.mkdtemp(prefix="htt-prguard-integration-"))
    worktree = temp_parent / "worktree"
    added = False
    started = utc_now()
    rows: list[dict[str, Any]] = []
    passed = False
    merged_tree = ""
    try:
        git(
            repo,
            "-c",
            f"core.hooksPath={os.devnull}",
            "worktree",
            "add",
            "--detach",
            str(worktree),
            live_sha,
            env=environment,
        )
        added = True
        try:
            git(
                worktree,
                "-c",
                "user.name=HTT Publication Rehearsal",
                "-c",
                "user.email=invalid@example.invalid",
                "-c",
                f"core.hooksPath={os.devnull}",
                "merge",
                "--no-commit",
                "--no-ff",
                str(seal["candidate_sha"]),
                env=environment,
            )
        except PublicationIntegrityError as exc:
            rows = [
                {
                    "id": "merge-candidate",
                    "argv": [
                        "git",
                        "merge",
                        "--no-commit",
                        "--no-ff",
                        str(seal["candidate_sha"]),
                    ],
                    "timeout_seconds": 0,
                    "started_at": started,
                    "completed_at": utc_now(),
                    "returncode": 1,
                    "timed_out": False,
                    "stdout_sha256": bytes_sha256(b""),
                    "stdout_bytes": 0,
                    "stderr_sha256": bytes_sha256(str(exc).encode("utf-8")),
                    "stderr_bytes": len(str(exc).encode("utf-8")),
                }
            ]
        else:
            merged_tree = str(
                git(worktree, "write-tree", env=environment)
            ).strip()
            rows, passed = _run_required_commands(
                worktree,
                list(policy["required_commands"]),
                log_dir=log_dir,
            )
    finally:
        if added:
            try:
                git(
                    repo,
                    "-c",
                    f"core.hooksPath={os.devnull}",
                    "worktree",
                    "remove",
                    "--force",
                    str(worktree),
                    env=environment,
                )
            except PublicationIntegrityError:
                pass
        shutil.rmtree(temp_parent, ignore_errors=True)
    completed = utc_now()
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "change_set_id": seal.get("change_set_id"),
        "publication_group_id": seal.get("publication_group_id"),
        "candidate_seal_sha256": seal.get("seal_sha256"),
        "candidate_sha": seal.get("candidate_sha"),
        "candidate_tree_sha": seal.get("candidate_tree_sha"),
        "diff_sha256": seal.get("diff_sha256"),
        "changed_files_sha256": seal.get("changed_files_sha256"),
        "target_remote": remote,
        "target_branch": branch,
        "latest_target_sha": live_sha,
        "integration_policy_sha256": policy_ref.get("sha256"),
        "merged_tree_sha": merged_tree,
        "started_at": started,
        "completed_at": completed,
        "status": "PASS" if passed else "FAIL",
        "commands": rows,
    }
    receipt["receipt_sha256"] = canonical_sha256(
        receipt, omit={"receipt_sha256"}
    )
    write_json_exclusive(output, receipt)
    return receipt


def verify_receipt(
    repo: Path,
    *,
    seal_path: str,
    receipt_path: str,
) -> list[str]:
    _, _, seal = read_repo_json(repo, seal_path, field="candidate seal")
    _, _, receipt = read_repo_json(repo, receipt_path, field="integration receipt")
    policy_ref = seal.get("integration_policy")
    if not isinstance(policy_ref, Mapping):
        return ["candidate seal lacks integration_policy"]
    _, policy = load_publication_policy(
        repo,
        policy_ref.get("path"),
        expected_sha256=str(policy_ref.get("sha256") or ""),
    )
    errors = validate_candidate_seal_payload(seal, repo=repo)
    errors.extend(
        validate_integration_receipt_payload(
            receipt,
            seal=seal,
            policy=policy,
            now=datetime.now(timezone.utc),
            repo=repo,
            log_dir=(
                (repo / receipt_path).parent
                / ((repo / receipt_path).stem + ".logs")
            ),
        )
    )
    if not errors:
        try:
            live_sha = remote_target_sha(
                repo,
                str(seal.get("target_remote") or ""),
                str(seal.get("target_branch") or ""),
            )
        except PublicationIntegrityError as exc:
            errors.append(str(exc))
        else:
            if live_sha != receipt.get("latest_target_sha"):
                errors.append(
                    "remote target moved after integration; rebase, reseal, and re-review"
                )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--seal", required=True)
    create.add_argument("--output", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--seal", required=True)
    verify.add_argument("--receipt", required=True)
    args = parser.parse_args()
    repo = root()
    try:
        if args.command == "create":
            receipt = create_receipt(
                repo, seal_path=args.seal, output_path=args.output
            )
            print(json.dumps(receipt, indent=2))
            if receipt.get("status") != "PASS":
                raise SystemExit(1)
            return
        errors = verify_receipt(
            repo, seal_path=args.seal, receipt_path=args.receipt
        )
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
        if errors:
            raise SystemExit(1)
    except PublicationIntegrityError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
