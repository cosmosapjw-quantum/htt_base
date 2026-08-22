#!/usr/bin/env python3
"""Attended, single-lane Planck identity-admission executor.

This private-workstation runner binds one reviewed worker to an exact clean
candidate and a replayed PR-289 admission.  It does not authorize unattended
execution and does not compute an observable itself.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
HTT_SRC = ROOT / "htt/src"
if str(HTT_SRC) not in sys.path:
    sys.path.insert(0, str(HTT_SRC))

REGISTRY_RELATIVE = Path(
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
LANE = "PLANCK"
PROFILE = "private_single_operator_attended_v1"
WORKER_RELATIVE = "scripts/codex_harness/run_authorized_observational_program.py"
WORKER_ARGUMENTS = ["--identity-worker"]
PLAN_FIELDS = frozenset(
    {
        "analysis_plan_id",
        "bayesian_inference",
        "execution_mode",
        "lane",
        "worker_arguments",
        "worker_path",
    }
)


class ObservationalProgramError(RuntimeError):
    """Raised before any worker starts when the attended contract drifts."""


def canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ObservationalProgramError("value is not canonical finite ASCII JSON") from exc


def content_hash(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _raw_hash(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _strict_json(raw: bytes, label: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ObservationalProgramError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ObservationalProgramError(f"{label} is not JSON") from exc
    if not isinstance(value, Mapping):
        raise ObservationalProgramError(f"{label} must be an object")
    return value


def _git(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(root), *args],
            check=False,
            text=True,
            capture_output=True,
            timeout=30,
            env={"HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ObservationalProgramError(f"candidate Git inspection failed: {exc}") from exc
    if completed.returncode:
        raise ObservationalProgramError(f"candidate Git inspection failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _candidate_identity(root: Path) -> tuple[str, str]:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ObservationalProgramError("candidate worktree must be exactly clean")
    commit = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    tree = _git(root, "rev-parse", "--verify", "HEAD^{tree}")
    if len(commit) != 40 or len(tree) != 40:
        raise ObservationalProgramError("candidate commit or tree identity is malformed")
    return commit, tree


def _relative(value: str, label: str) -> Path:
    pure = PurePosixPath(value)
    if (
        not value
        or pure.is_absolute()
        or pure.as_posix() != value
        or any(part in {"", ".", ".."} for part in pure.parts)
        or "\\" in value
    ):
        raise ObservationalProgramError(f"{label} must be a canonical repository-relative path")
    return Path(*pure.parts)


def _tracked_file(root: Path, value: str, label: str) -> Path:
    relative = _relative(value, label)
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ObservationalProgramError(f"{label} must be a regular file")
    _git(root, "ls-files", "--error-unmatch", "--", relative.as_posix())
    return path


def validate_plan_values(values: object, *, root: Path) -> dict[str, object]:
    if not isinstance(values, Mapping) or set(values) != PLAN_FIELDS:
        raise ObservationalProgramError("attended plan fields drifted or request shell execution")
    if values["lane"] != LANE:
        raise ObservationalProgramError("attended plan permits PLANCK only")
    if values["analysis_plan_id"] != "plan:PR290-PLANCK-LOWELL-V1":
        raise ObservationalProgramError("analysis plan identity is not the registered PLANCK plan")
    if values["execution_mode"] != "identity_only" or values["bayesian_inference"] is not False:
        raise ObservationalProgramError(
            "PR-305 accepts identity-only plans; Bayesian plans require the PR-304 binding path"
        )
    worker_value = values["worker_path"]
    if not isinstance(worker_value, str):
        raise ObservationalProgramError("worker path must be text")
    relative = _relative(worker_value, "worker path")
    if worker_value != WORKER_RELATIVE:
        raise ObservationalProgramError("worker must equal the reviewed Planck identity entrypoint")
    worker = _tracked_file(root, worker_value, "worker")
    raw_arguments = values["worker_arguments"]
    if (
        isinstance(raw_arguments, (str, bytes))
        or not isinstance(raw_arguments, Sequence)
        or len(raw_arguments) > 16
        or any(
            not isinstance(item, str)
            or not item
            or not item.isascii()
            or any(character in item for character in "\0\n\r")
            for item in raw_arguments
        )
    ):
        raise ObservationalProgramError("worker arguments are malformed")
    if list(raw_arguments) != WORKER_ARGUMENTS:
        raise ObservationalProgramError("worker arguments must select the reviewed identity-only mode")
    return {**dict(values), "worker": worker, "worker_arguments": list(raw_arguments)}


def _load_plan(root: Path, plan_path: str) -> tuple[dict[str, object], bytes, Path]:
    import yaml

    path = _tracked_file(root, plan_path, "analysis plan")
    raw = path.read_bytes()
    try:
        payload = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ObservationalProgramError("analysis plan is not valid YAML") from exc
    if not isinstance(payload, Mapping):
        raise ObservationalProgramError("analysis plan document must be a mapping")
    return validate_plan_values(payload.get("attended_execution_plan"), root=root), raw, path


def _load_admission(root: Path, path: Path):
    from common.data_identity import (
        AdmissionStatus,
        DataIdentityError,
        load_lane_registry,
        replay_lane_admission_decision,
    )

    if path.is_symlink() or not path.is_file():
        raise ObservationalProgramError("PR-289 admission must be a regular file")
    raw = path.read_bytes()
    try:
        registry = load_lane_registry(root / REGISTRY_RELATIVE)
        decision = replay_lane_admission_decision(
            _strict_json(raw, "PR-289 admission"), registry=registry
        )
    except (DataIdentityError, ObservationalProgramError) as exc:
        raise ObservationalProgramError(f"PR-289 admission replay rejected: {exc}") from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != LANE
        or not decision.records
        or decision.lane_admission_bundle_id is None
    ):
        raise ObservationalProgramError("PR-289 admission is not complete PLANCK identity admission")
    return decision, raw


def _output_path(root: Path, value: Path) -> Path:
    if not value.is_absolute():
        raise ObservationalProgramError("output directory must be absolute")
    if value.is_symlink():
        raise ObservationalProgramError("output directory must not be a symlink")
    output = value.resolve(strict=False)
    candidate = root.resolve()
    for ancestor, descendant in ((candidate, output), (output, candidate)):
        try:
            descendant.relative_to(ancestor)
        except ValueError:
            continue
        raise ObservationalProgramError("output directory must be disjoint from the candidate worktree")
    if output.exists() and not output.is_dir():
        raise ObservationalProgramError("existing output path must be a directory")
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise ObservationalProgramError("output parent must be an existing regular directory")
    return output


def _environment(output: Path) -> dict[str, str]:
    return {
        "HOME": "/nonexistent",
        "HTT_ATTENDED_LANE": LANE,
        "HTT_ATTENDED_OUTPUT_DIR": str(output),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }


def prepare_execution(
    *,
    lane: str,
    plan_path: str,
    admission_path: Path,
    output_dir: Path,
    timeout_seconds: int,
    root: Path = ROOT,
) -> dict[str, object]:
    if os.geteuid() == 0:
        raise ObservationalProgramError("attended executor never runs as root")
    if lane != LANE:
        raise ObservationalProgramError("replacement PR-305 accepts PLANCK only")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 86_400:
        raise ObservationalProgramError("timeout must be an integer from 1 through 86400")
    root = root.resolve()
    commit, tree = _candidate_identity(root)
    plan, plan_raw, plan_file = _load_plan(root, plan_path)
    decision, admission_raw = _load_admission(root, admission_path)
    output = _output_path(root, output_dir)
    worker = plan["worker"]
    assert isinstance(worker, Path)
    worker_raw = worker.read_bytes()
    environment = _environment(output)
    environment_contract = {
        "python_executable": str(Path(sys.executable).resolve()),
        "variables": environment,
    }
    record_ids = [record.record_id for record in decision.records]
    acceptance = {
        "schema": "htt.attended_execution_acceptance.v1",
        "deployment_profile": PROFILE,
        "lane": LANE,
        "candidate_commit": commit,
        "candidate_tree": tree,
        "worktree_clean": True,
        "admission_decision_sha256": _raw_hash(admission_raw),
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "ordered_record_ids_sha256": content_hash(record_ids),
        "analysis_plan_path": plan_path,
        "analysis_plan_sha256": _raw_hash(plan_raw),
        "worker_path": str(worker.relative_to(root)),
        "worker_sha256": _raw_hash(worker_raw),
        "environment_contract_sha256": content_hash(environment_contract),
        "output_dir": str(output),
        "timeout_seconds": timeout_seconds,
    }
    if _candidate_identity(root) != (commit, tree):
        raise ObservationalProgramError("candidate changed during acceptance construction")
    return {
        "root": root,
        "plan_file": plan_file,
        "admission_file": admission_path,
        "worker": worker,
        "worker_arguments": plan["worker_arguments"],
        "environment": environment,
        "output": output,
        "timeout_seconds": timeout_seconds,
        "acceptance_payload": acceptance,
        "acceptance_hash": content_hash(acceptance),
    }


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(payload) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _spawn_worker(command: list[str], *, root: Path, environment: Mapping[str, str], timeout: int):
    return subprocess.run(
        command,
        cwd=root,
        env=dict(environment),
        shell=False,
        check=False,
        capture_output=True,
        timeout=timeout,
    )


def _output_hashes(output: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    excluded = {".attended.lock", "start.json", "terminal.json"}
    for directory, directory_names, file_names in os.walk(output, followlinks=False):
        base = Path(directory)
        for name in sorted(directory_names) + sorted(file_names):
            path = base / name
            if base == output and name in excluded:
                continue
            if path.is_symlink():
                raise ObservationalProgramError("worker output contains a symlink")
            if path.is_file():
                rows[path.relative_to(output).as_posix()] = _raw_hash(path.read_bytes())
    return dict(sorted(rows.items()))


def execute_prepared(prepared: Mapping[str, object], confirmation: str) -> dict[str, object]:
    expected = prepared["acceptance_hash"]
    if confirmation != expected:
        raise ObservationalProgramError("confirmation hash does not equal the reviewed acceptance hash")
    if os.geteuid() == 0:
        raise ObservationalProgramError("attended executor never runs as root")
    root = prepared["root"]
    output = prepared["output"]
    assert isinstance(root, Path) and isinstance(output, Path)
    acceptance = prepared["acceptance_payload"]
    assert isinstance(acceptance, Mapping)
    if _candidate_identity(root) != (
        acceptance["candidate_commit"], acceptance["candidate_tree"]
    ):
        raise ObservationalProgramError("candidate changed after confirmation")
    for path_key, hash_key in (
        ("plan_file", "analysis_plan_sha256"),
        ("admission_file", "admission_decision_sha256"),
        ("worker", "worker_sha256"),
    ):
        path = prepared[path_key]
        assert isinstance(path, Path)
        if path.is_symlink() or not path.is_file() or _raw_hash(path.read_bytes()) != acceptance[hash_key]:
            raise ObservationalProgramError(f"{path_key} changed after confirmation")
    output.mkdir(mode=0o700, exist_ok=True)
    if output.is_symlink() or not output.is_dir():
        raise ObservationalProgramError("output directory is not regular")
    output_stat = output.stat()
    if output_stat.st_uid != os.geteuid() or output_stat.st_mode & 0o077:
        raise ObservationalProgramError("output directory must be operator-owned with mode 0700")
    lock_path = output / ".attended.lock"
    if lock_path.is_symlink():
        raise ObservationalProgramError("output lock must not be a symlink")
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ObservationalProgramError("output directory is already locked") from exc
        unexpected = sorted(path.name for path in output.iterdir() if path.name != lock_path.name)
        if unexpected:
            raise ObservationalProgramError("output directory is not dedicated and empty")
        started = _timestamp()
        start = {
            "state": "STARTED",
            "acceptance_hash": expected,
            "candidate_commit": acceptance["candidate_commit"],
            "candidate_tree": acceptance["candidate_tree"],
            "lane": LANE,
            "admission_bundle_id": acceptance["lane_admission_bundle_id"],
            "analysis_plan_sha256": acceptance["analysis_plan_sha256"],
            "worker_sha256": acceptance["worker_sha256"],
            "started_at_utc": started,
            "observed_science_executed": False,
        }
        _atomic_json(output / "start.json", start)
        worker = prepared["worker"]
        assert isinstance(worker, Path)
        command = [
            str(Path(sys.executable).resolve()),
            "-B",
            str(worker),
            *prepared["worker_arguments"],
        ]
        stdout = b""
        stderr = b""
        exit_code: int | None = None
        signal_number: int | None = None
        try:
            completed = _spawn_worker(
                command,
                root=root,
                environment=prepared["environment"],
                timeout=prepared["timeout_seconds"],
            )
            stdout = completed.stdout or b""
            stderr = completed.stderr or b""
            exit_code = completed.returncode
            if completed.returncode == 0:
                state = "SUCCEEDED"
            elif completed.returncode < 0:
                state = "SIGNALED"
                signal_number = -completed.returncode
                exit_code = None
            else:
                state = "FAILED"
        except subprocess.TimeoutExpired as exc:
            state = "TIMED_OUT"
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
        except OSError as exc:
            state = "FAILED"
            exit_code = 126
            stderr = str(exc).encode("utf-8", "replace")
        output_error: str | None = None
        try:
            output_hashes = _output_hashes(output)
        except ObservationalProgramError as exc:
            output_hashes = {}
            output_error = str(exc)
            if state == "SUCCEEDED":
                state = "FAILED"
                exit_code = 125
        terminal = {
            "state": state,
            "acceptance_hash": expected,
            "exit_code": exit_code,
            "signal": signal_number,
            "ended_at_utc": _timestamp(),
            "stdout_sha256": _raw_hash(stdout),
            "stderr_sha256": _raw_hash(stderr),
            "output_hashes": output_hashes,
            "output_error": output_error,
            "observed_science_executed": False,
        }
        _atomic_json(output / "terminal.json", terminal)
        return terminal


def _identity_worker() -> int:
    """Acknowledge the already replayed Planck identity without opening data."""

    if os.geteuid() == 0:
        return 2
    if os.environ.get("HTT_ATTENDED_LANE") != LANE:
        return 3
    print(json.dumps({"state": "PLANCK_IDENTITY_REPLAYED", "observed_science_executed": False}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    effective_argv = sys.argv[1:] if argv is None else argv
    if effective_argv == ["--identity-worker"]:
        return _identity_worker()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--print-acceptance", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args(effective_argv)
    try:
        prepared = prepare_execution(
            lane=args.lane,
            plan_path=args.plan,
            admission_path=args.admission,
            output_dir=args.output_dir,
            timeout_seconds=args.timeout_seconds,
        )
        if args.print_acceptance:
            if args.confirm is not None:
                raise ObservationalProgramError("--confirm is valid only with --execute")
            print(
                json.dumps(
                    {
                        "acceptance_hash": prepared["acceptance_hash"],
                        "acceptance": prepared["acceptance_payload"],
                        "observed_science_executed": False,
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.confirm is None:
            raise ObservationalProgramError("--execute requires exact --confirm HASH")
        terminal = execute_prepared(prepared, args.confirm)
        print(json.dumps(terminal, sort_keys=True))
        if terminal["state"] == "SUCCEEDED":
            return 0
        if terminal["state"] == "TIMED_OUT":
            return 124
        if terminal["state"] == "SIGNALED":
            return 128 + int(terminal["signal"])
        return int(terminal["exit_code"] or 1)
    except ObservationalProgramError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
