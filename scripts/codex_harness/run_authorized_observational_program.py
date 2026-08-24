#!/usr/bin/env python3
"""Attended, one-at-a-time primary-lane identity-admission executor.

This private-workstation runner binds one reviewed worker to an exact clean
candidate and a replayed PR-289 admission.  It does not authorize unattended
execution and does not compute an observable itself.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import signal
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
WORKER_RELATIVE = "scripts/codex_harness/run_authorized_observational_program.py"
WORKER_ARGUMENTS = ["--identity-worker"]
THREAD_CONTROLS = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
PLANCK_RUNTIME_MODULES = (
    "numpy",
    "numpy.linalg",
    "numpy._core._multiarray_umath",
    "numpy.linalg._umath_linalg",
    "scipy",
    "scipy.linalg",
    "scipy.linalg._fblas",
    "scipy.linalg._flapack",
    "scipy.special",
    "scipy.special._multiufuncs",
    "scipy.special._gufuncs",
    "healpy",
    "healpy.sphtfunc",
    "healpy.pixelfunc",
    "healpy.rotator",
    "healpy._healpy_sph_transform_lib",
    "healpy._sphtools",
    "healpy._healpy_pixel_lib",
)
PLANCK_DISTRIBUTIONS = ("numpy", "scipy", "healpy")
CF4_RUNTIME_MODULES = (
    "numpy",
    "numpy.linalg",
    "numpy._core._multiarray_umath",
    "numpy.linalg._umath_linalg",
)
CF4_DISTRIBUTIONS = ("numpy",)
ACT_RUNTIME_MODULES = (
    "numpy",
    "numpy.linalg",
    "numpy._core._multiarray_umath",
    "numpy.linalg._umath_linalg",
    "healpy",
    "healpy.fitsfunc",
    "healpy.sphtfunc",
    "healpy.pixelfunc",
    "healpy._healpy_sph_transform_lib",
    "healpy._sphtools",
    "healpy._healpy_pixel_lib",
)
ACT_DISTRIBUTIONS = ("numpy", "healpy")
JWST_SN_RUNTIME_MODULES = (
    "numpy",
    "numpy.linalg",
    "numpy._core._multiarray_umath",
    "numpy.linalg._umath_linalg",
    "scipy",
    "scipy.linalg",
    "scipy.stats",
    "scipy.special",
)
JWST_SN_DISTRIBUTIONS = ("numpy", "scipy")
HSC_KIDS_RUNTIME_MODULES = (
    "numpy",
    "numpy.linalg",
    "numpy._core._multiarray_umath",
    "numpy.linalg._umath_linalg",
)
HSC_KIDS_DISTRIBUTIONS = ("numpy",)
OBSERVED_DATA_MARKER = "observed_data_opened.json"
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


@dataclass(frozen=True)
class LaneProfile:
    lane: str
    deployment_profile: str
    analysis_plan_id: str
    science_execution_mode: str
    science_worker_relative: str
    science_worker_arguments: tuple[str, ...]
    result_filename: str
    runtime_modules: tuple[str, ...]
    runtime_distributions: tuple[str, ...]


LANE_PROFILES = {
    profile.lane: profile
    for profile in (
        LaneProfile(
            lane="PLANCK",
            deployment_profile="private_single_operator_attended_v1",
            analysis_plan_id="plan:PR290-PLANCK-LOWELL-V1",
            science_execution_mode="planck_pr3_lowell_operator",
            science_worker_relative="scripts/observed_runs/run_planck_pr3.py",
            science_worker_arguments=("--run-admitted",),
            result_filename="planck_pr3_result.json",
            runtime_modules=PLANCK_RUNTIME_MODULES,
            runtime_distributions=PLANCK_DISTRIBUTIONS,
        ),
        LaneProfile(
            lane="CF4",
            deployment_profile="private_single_operator_attended_v1",
            analysis_plan_id="plan:PR291-CF4-TOMOGRAPHY-V1",
            science_execution_mode="cf4_current_stack_affine_operator",
            science_worker_relative="scripts/observed_runs/run_cf4_current_stack.py",
            science_worker_arguments=("--run-admitted",),
            result_filename="cf4_current_stack_result.json",
            runtime_modules=CF4_RUNTIME_MODULES,
            runtime_distributions=CF4_DISTRIBUTIONS,
        ),
        LaneProfile(
            lane="ACT",
            deployment_profile="private_single_operator_attended_v1",
            analysis_plan_id="plan:PR204-ACT-LENSING-V1",
            science_execution_mode="act_dr6_validated_band_operator",
            science_worker_relative="scripts/observed_runs/run_act_dr6.py",
            science_worker_arguments=("--run-admitted",),
            result_filename="act_dr6_result.json",
            runtime_modules=ACT_RUNTIME_MODULES,
            runtime_distributions=ACT_DISTRIBUTIONS,
        ),
    )
}
JWST_SN_PROFILE = LaneProfile(
    lane="JWST_SN",
    deployment_profile="private_single_operator_attended_v1",
    analysis_plan_id="plan:PR293-JWST-SN-V1",
    science_execution_mode="jwst_sn_row_covariance_operator",
    science_worker_relative="scripts/observed_runs/run_jwst_sn.py",
    science_worker_arguments=("--run-admitted",),
    result_filename="jwst_sn_result.json",
    runtime_modules=JWST_SN_RUNTIME_MODULES,
    runtime_distributions=JWST_SN_DISTRIBUTIONS,
)
HSC_KIDS_PROFILE = LaneProfile(
    lane="HSC_KIDS",
    deployment_profile="private_single_operator_attended_v1",
    analysis_plan_id="plan:PR292-HSC-KIDS-SPIN2-V1",
    science_execution_mode="hsc_kids_typed_spin2_joint_operator",
    science_worker_relative="scripts/observed_runs/run_hsc_kids.py",
    science_worker_arguments=("--run-admitted",),
    result_filename="hsc_kids_result.json",
    runtime_modules=HSC_KIDS_RUNTIME_MODULES,
    runtime_distributions=HSC_KIDS_DISTRIBUTIONS,
)
# Keep the predecessor map byte-compatible for its historical exact-set
# contract while routing every new consumer through the complete registry.
REGISTERED_LANE_PROFILES = {
    **LANE_PROFILES,
    "JWST_SN": JWST_SN_PROFILE,
    "HSC_KIDS": HSC_KIDS_PROFILE,
}


class ObservationalProgramError(RuntimeError):
    """Raised before any worker starts when the attended contract drifts."""


def _lane_profile(lane: object) -> LaneProfile:
    if not isinstance(lane, str) or lane not in REGISTERED_LANE_PROFILES:
        raise ObservationalProgramError(
            "attended executor requires one exact registered primary lane"
        )
    return REGISTERED_LANE_PROFILES[lane]


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
        raise ObservationalProgramError(
            "value is not canonical finite ASCII JSON"
        ) from exc


def content_hash(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _raw_hash(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _strict_json(raw: bytes, label: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ObservationalProgramError(
                    f"{label} contains duplicate key {key!r}"
                )
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
            env={
                "HOME": "/nonexistent",
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": "/usr/bin:/bin",
            },
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ObservationalProgramError(
            f"candidate Git inspection failed: {exc}"
        ) from exc
    if completed.returncode:
        raise ObservationalProgramError(
            f"candidate Git inspection failed: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _candidate_identity(root: Path) -> tuple[str, str]:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ObservationalProgramError("candidate worktree must be exactly clean")
    commit = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    tree = _git(root, "rev-parse", "--verify", "HEAD^{tree}")
    if len(commit) != 40 or len(tree) != 40:
        raise ObservationalProgramError(
            "candidate commit or tree identity is malformed"
        )
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
        raise ObservationalProgramError(
            f"{label} must be a canonical repository-relative path"
        )
    return Path(*pure.parts)


def _tracked_file(root: Path, value: str, label: str) -> Path:
    relative = _relative(value, label)
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ObservationalProgramError(f"{label} must be a regular file")
    _git(root, "ls-files", "--error-unmatch", "--", relative.as_posix())
    return path


def _analysis_plan_file(root: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        return _tracked_file(root, value, "analysis plan")
    if (
        candidate.is_symlink()
        or not candidate.is_file()
        or candidate.absolute() != candidate.resolve()
    ):
        raise ObservationalProgramError(
            "external analysis plan must be an absolute regular file"
        )
    return candidate


def validate_plan_values(
    values: object,
    *,
    root: Path,
    profile: LaneProfile | None = None,
) -> dict[str, object]:
    if not isinstance(values, Mapping) or set(values) != PLAN_FIELDS:
        raise ObservationalProgramError(
            "attended plan fields drifted or request shell execution"
        )
    resolved_profile = _lane_profile(values["lane"])
    if profile is not None and resolved_profile != profile:
        raise ObservationalProgramError("requested lane and attended plan are cross-wired")
    if values["analysis_plan_id"] != resolved_profile.analysis_plan_id:
        raise ObservationalProgramError(
            "analysis plan identity is not registered for the selected lane"
        )
    execution_mode = values["execution_mode"]
    if (
        not isinstance(execution_mode, str)
        or execution_mode
        not in {"identity_only", resolved_profile.science_execution_mode}
        or values["bayesian_inference"] is not False
    ):
        raise ObservationalProgramError(
            "attended plan must select identity-only or the reviewed lane operator"
        )
    science = execution_mode == resolved_profile.science_execution_mode
    worker_value = values["worker_path"]
    if not isinstance(worker_value, str):
        raise ObservationalProgramError("worker path must be text")
    _relative(worker_value, "worker path")
    expected_worker = (
        resolved_profile.science_worker_relative if science else WORKER_RELATIVE
    )
    if worker_value != expected_worker:
        raise ObservationalProgramError(
            "worker must equal the reviewed selected-lane entrypoint"
        )
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
    expected_arguments = (
        list(resolved_profile.science_worker_arguments)
        if science
        else WORKER_ARGUMENTS
    )
    if list(raw_arguments) != expected_arguments:
        raise ObservationalProgramError(
            "worker arguments do not select the reviewed lane mode"
        )
    return {
        **dict(values),
        "worker": worker,
        "worker_arguments": list(raw_arguments),
        "science_execution": science,
        "profile": resolved_profile,
    }


def _load_plan(
    root: Path, plan_path: str, profile: LaneProfile
) -> tuple[dict[str, object], bytes, Path]:
    import yaml

    path = _analysis_plan_file(root, plan_path)
    raw = path.read_bytes()
    try:
        payload = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ObservationalProgramError("analysis plan is not valid YAML") from exc
    if not isinstance(payload, Mapping):
        raise ObservationalProgramError("analysis plan document must be a mapping")
    return (
        validate_plan_values(
            payload.get("attended_execution_plan"), root=root, profile=profile
        ),
        raw,
        path,
    )


def _load_admission(root: Path, path: Path, profile: LaneProfile):
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
        raise ObservationalProgramError(
            f"PR-289 admission replay rejected: {exc}"
        ) from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != profile.lane
        or not decision.records
        or decision.lane_admission_bundle_id is None
    ):
        raise ObservationalProgramError(
            "PR-289 admission is not complete selected-lane identity admission"
        )
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
        raise ObservationalProgramError(
            "output directory must be disjoint from the candidate worktree"
        )
    if output.exists() and not output.is_dir():
        raise ObservationalProgramError("existing output path must be a directory")
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise ObservationalProgramError(
            "output parent must be an existing regular directory"
        )
    return output


def _environment(
    output: Path,
    *,
    profile: LaneProfile,
    science: bool,
    candidate_root: Path = ROOT,
    candidate_commit: str | None = None,
    candidate_tree: str | None = None,
    runtime_contract: Mapping[str, object] | None = None,
) -> dict[str, str]:
    environment = {
        "HOME": "/nonexistent",
        "HTT_ATTENDED_LANE": profile.lane,
        "HTT_ATTENDED_OUTPUT_DIR": str(output),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    if science:
        if not isinstance(runtime_contract, Mapping):
            raise ObservationalProgramError("science runtime contract is missing")
        roots = runtime_contract.get("import_roots")
        if not isinstance(roots, list) or not roots:
            raise ObservationalProgramError("science runtime import roots are missing")
        environment.update(THREAD_CONTROLS)
        environment["HTT_ATTENDED_START_WRITTEN"] = "1"
        if candidate_commit is None or candidate_tree is None:
            raise ObservationalProgramError("science candidate identity is missing")
        environment["HTT_ATTENDED_CANDIDATE_COMMIT"] = candidate_commit
        environment["HTT_ATTENDED_CANDIDATE_TREE"] = candidate_tree
        environment["HTT_ATTENDED_DATA_OPEN_MARKER"] = str(
            output / OBSERVED_DATA_MARKER
        )
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(candidate_root / "htt"), str(candidate_root / "htt/src"), *roots]
        )
    return environment


def _science_runtime_contract(profile: LaneProfile) -> dict[str, object]:
    executable = Path(sys.executable).absolute()
    modules: dict[str, dict[str, str]] = {}
    import_roots: set[str] = set()
    for name in profile.runtime_modules:
        try:
            module = importlib.import_module(name)
        except ImportError as exc:
            raise ObservationalProgramError(
                f"science runtime dependency {name} is unavailable"
            ) from exc
        declared_origin = Path(module.__file__ or "")
        if declared_origin.is_symlink():
            raise ObservationalProgramError(
                f"science runtime dependency {name} origin is a symlink"
            )
        origin = declared_origin.resolve()
        if not origin.is_file():
            raise ObservationalProgramError(
                f"science runtime dependency {name} has no regular origin"
            )
        modules[name] = {
            "origin": str(origin),
            "origin_sha256": _file_hash(origin),
        }
        if name in profile.runtime_distributions:
            modules[name]["version"] = str(module.__version__)
            import_roots.add(str(origin.parent.parent))
    distributions: dict[str, dict[str, str]] = {}
    for name in profile.runtime_distributions:
        distribution = metadata.distribution(name)
        record = distribution.read_text("RECORD")
        if not record:
            raise ObservationalProgramError(
                f"science runtime distribution {name} has no RECORD"
            )
        distributions[name] = {
            "version": distribution.version,
            "record_sha256": _raw_hash(record.encode("utf-8")),
        }
    return {
        "python_executable_path": str(executable),
        "python_executable_sha256": _file_hash(executable),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_cache_tag": sys.implementation.cache_tag,
        "platform_machine": platform.machine(),
        "modules": modules,
        "distributions": distributions,
        "import_roots": sorted(import_roots),
        "thread_controls": dict(THREAD_CONTROLS),
    }


def prepare_execution(
    *,
    lane: str,
    plan_path: str,
    admission_path: Path,
    output_dir: Path,
    timeout_seconds: int,
    data_root: Path | None = None,
    root: Path = ROOT,
) -> dict[str, object]:
    if os.geteuid() == 0:
        raise ObservationalProgramError("attended executor never runs as root")
    profile = _lane_profile(lane)
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 86_400:
        raise ObservationalProgramError(
            "timeout must be an integer from 1 through 86400"
        )
    root = root.resolve()
    commit, tree = _candidate_identity(root)
    plan, plan_raw, plan_file = _load_plan(root, plan_path, profile)
    science = bool(plan["science_execution"])
    if science:
        if (
            data_root is None
            or not data_root.is_absolute()
            or data_root.is_symlink()
            or not data_root.is_dir()
        ):
            raise ObservationalProgramError(
                "science execution requires an absolute regular data root"
            )
        declared_data_root = data_root.absolute()
        if declared_data_root != declared_data_root.resolve():
            raise ObservationalProgramError(
                "science execution forbids symlink-based data roots"
            )
        bound_data_root: Path | None = declared_data_root
    else:
        if data_root is not None:
            raise ObservationalProgramError(
                "identity-only execution forbids a data root"
            )
        bound_data_root = None
    decision, admission_raw = _load_admission(root, admission_path, profile)
    output = _output_path(root, output_dir)
    worker = plan["worker"]
    assert isinstance(worker, Path)
    worker_raw = worker.read_bytes()
    runtime_contract = _science_runtime_contract(profile) if science else None
    environment = _environment(
        output,
        profile=profile,
        science=science,
        candidate_root=root,
        candidate_commit=commit,
        candidate_tree=tree,
        runtime_contract=runtime_contract,
    )
    environment_contract = {
        "python_executable": str(Path(sys.executable).absolute()),
        "variables": environment,
    }
    record_ids = [record.record_id for record in decision.records]
    acceptance = {
        "schema": "htt.attended_execution_acceptance.v1",
        "deployment_profile": profile.deployment_profile,
        "lane": profile.lane,
        "candidate_commit": commit,
        "candidate_tree": tree,
        "worktree_clean": True,
        "admission_decision_sha256": _raw_hash(admission_raw),
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "ordered_record_ids_sha256": content_hash(record_ids),
        "ordered_record_ids": record_ids,
        "analysis_plan_path": plan_path,
        "analysis_plan_id": profile.analysis_plan_id,
        "analysis_plan_sha256": _raw_hash(plan_raw),
        "worker_path": str(worker.relative_to(root)),
        "worker_sha256": _raw_hash(worker_raw),
        "worker_arguments": list(plan["worker_arguments"]),
        "environment_contract_sha256": content_hash(environment_contract),
        "output_dir": str(output),
        "timeout_seconds": timeout_seconds,
        "science_execution": science,
        "result_filename": profile.result_filename,
    }
    if science:
        acceptance["data_root"] = str(bound_data_root)
        acceptance["science_runtime_contract_sha256"] = content_hash(runtime_contract)
    if _candidate_identity(root) != (commit, tree):
        raise ObservationalProgramError(
            "candidate changed during acceptance construction"
        )
    return {
        "root": root,
        "profile": profile,
        "plan_file": plan_file,
        "admission_file": admission_path,
        "worker": worker,
        "worker_arguments": plan["worker_arguments"],
        "environment": environment,
        "output": output,
        "timeout_seconds": timeout_seconds,
        "data_root": bound_data_root,
        "science_runtime_contract": runtime_contract,
        "acceptance_payload": acceptance,
        "acceptance_hash": content_hash(acceptance),
    }


def _timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
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


@dataclass(frozen=True)
class WorkerOutcome:
    returncode: int | None
    state: str


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    for requested_signal in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, requested_signal)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def _spawn_worker(
    command: list[str],
    *,
    root: Path,
    environment: Mapping[str, str],
    timeout: int,
    output: Path,
) -> WorkerOutcome:
    stdout_path = output / "stdout.log"
    stderr_path = output / "stderr.log"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=dict(environment),
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_process_group(process)
            return WorkerOutcome(returncode=None, state="TIMED_OUT")
        except KeyboardInterrupt:
            _terminate_process_group(process)
            return WorkerOutcome(returncode=None, state="INTERRUPTED")
    if returncode == 0:
        state = "SUCCEEDED"
    elif returncode < 0:
        state = "SIGNALED"
    else:
        state = "FAILED"
    return WorkerOutcome(returncode=returncode, state=state)


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
                rows[path.relative_to(output).as_posix()] = _file_hash(path)
    return dict(sorted(rows.items()))


def _observed_data_open_state(
    output: Path, *, science: bool
) -> tuple[bool, str | None]:
    if not science:
        return False, None
    marker = output / OBSERVED_DATA_MARKER
    if not marker.exists():
        return False, None
    if marker.is_symlink() or not marker.is_file():
        return True, "observed-data-open marker is not a regular file"
    try:
        payload = _strict_json(marker.read_bytes(), "observed-data-open marker")
    except (OSError, ObservationalProgramError) as exc:
        return True, str(exc)
    if dict(payload) != {"state": "OBSERVED_DATA_OPEN_ATTEMPTED"}:
        return True, "observed-data-open marker content drifted"
    return True, None


def _confirmation_profile(prepared: Mapping[str, object]) -> LaneProfile:
    """Rebind every value consumed after attended confirmation."""

    acceptance = prepared.get("acceptance_payload")
    expected = prepared.get("acceptance_hash")
    if (
        not isinstance(acceptance, Mapping)
        or not isinstance(expected, str)
        or content_hash(dict(acceptance)) != expected
    ):
        raise ObservationalProgramError("confirmation binding payload drifted")
    profile = _lane_profile(acceptance.get("lane"))
    if (
        prepared.get("profile") != profile
        or acceptance.get("deployment_profile") != profile.deployment_profile
        or acceptance.get("analysis_plan_id") != profile.analysis_plan_id
        or acceptance.get("result_filename") != profile.result_filename
    ):
        raise ObservationalProgramError("confirmation binding lane profile drifted")
    science = acceptance.get("science_execution") is True
    expected_worker = (
        profile.science_worker_relative if science else WORKER_RELATIVE
    )
    expected_arguments = (
        list(profile.science_worker_arguments) if science else WORKER_ARGUMENTS
    )
    root = prepared.get("root")
    worker = prepared.get("worker")
    plan_file = prepared.get("plan_file")
    output = prepared.get("output")
    timeout = prepared.get("timeout_seconds")
    environment = prepared.get("environment")
    if (
        not isinstance(root, Path)
        or not isinstance(worker, Path)
        or not isinstance(plan_file, Path)
        or not isinstance(acceptance.get("analysis_plan_path"), str)
    ):
        raise ObservationalProgramError("confirmation binding path shape drifted")
    if plan_file != _analysis_plan_file(root, acceptance["analysis_plan_path"]):
        raise ObservationalProgramError("confirmation binding plan path drifted")
    try:
        worker_relative = worker.relative_to(root).as_posix()
    except ValueError as exc:
        raise ObservationalProgramError(
            "confirmation binding worker escaped candidate"
        ) from exc
    if (
        worker_relative != expected_worker
        or acceptance.get("worker_path") != expected_worker
        or prepared.get("worker_arguments") != expected_arguments
        or acceptance.get("worker_arguments") != expected_arguments
    ):
        raise ObservationalProgramError("confirmation binding worker drifted")
    if (
        not isinstance(environment, Mapping)
        or content_hash(
            {
                "python_executable": str(Path(sys.executable).absolute()),
                "variables": dict(environment),
            }
        )
        != acceptance.get("environment_contract_sha256")
    ):
        raise ObservationalProgramError("confirmation binding environment drifted")
    if (
        not isinstance(output, Path)
        or str(output) != acceptance.get("output_dir")
        or type(timeout) is not int
        or timeout != acceptance.get("timeout_seconds")
    ):
        raise ObservationalProgramError("confirmation binding output or timeout drifted")
    if science:
        data_root = prepared.get("data_root")
        runtime = prepared.get("science_runtime_contract")
        if (
            not isinstance(data_root, Path)
            or str(data_root) != acceptance.get("data_root")
            or not isinstance(runtime, Mapping)
            or content_hash(dict(runtime))
            != acceptance.get("science_runtime_contract_sha256")
        ):
            raise ObservationalProgramError(
                "confirmation binding science runtime or data root drifted"
            )
    return profile


def execute_prepared(
    prepared: Mapping[str, object], confirmation: str
) -> dict[str, object]:
    expected = prepared["acceptance_hash"]
    if confirmation != expected:
        raise ObservationalProgramError(
            "confirmation hash does not equal the reviewed acceptance hash"
        )
    if os.geteuid() == 0:
        raise ObservationalProgramError("attended executor never runs as root")
    profile = _confirmation_profile(prepared)
    root = prepared["root"]
    output = prepared["output"]
    assert isinstance(root, Path) and isinstance(output, Path)
    acceptance = prepared["acceptance_payload"]
    assert isinstance(acceptance, Mapping)
    if _candidate_identity(root) != (
        acceptance["candidate_commit"],
        acceptance["candidate_tree"],
    ):
        raise ObservationalProgramError("candidate changed after confirmation")
    if acceptance.get("science_execution"):
        if content_hash(_science_runtime_contract(profile)) != acceptance.get(
            "science_runtime_contract_sha256"
        ):
            raise ObservationalProgramError(
                "science runtime changed after confirmation"
            )
        data_root = prepared.get("data_root")
        if (
            not isinstance(data_root, Path)
            or data_root.is_symlink()
            or not data_root.is_dir()
            or str(data_root.resolve()) != acceptance.get("data_root")
        ):
            raise ObservationalProgramError(
                "science data root changed after confirmation"
            )
    for path_key, hash_key in (
        ("plan_file", "analysis_plan_sha256"),
        ("admission_file", "admission_decision_sha256"),
        ("worker", "worker_sha256"),
    ):
        path = prepared[path_key]
        assert isinstance(path, Path)
        if (
            path.is_symlink()
            or not path.is_file()
            or _raw_hash(path.read_bytes()) != acceptance[hash_key]
        ):
            raise ObservationalProgramError(f"{path_key} changed after confirmation")
    output.mkdir(mode=0o700, exist_ok=True)
    if output.is_symlink() or not output.is_dir():
        raise ObservationalProgramError("output directory is not regular")
    output_stat = output.stat()
    if output_stat.st_uid != os.geteuid() or output_stat.st_mode & 0o077:
        raise ObservationalProgramError(
            "output directory must be operator-owned with mode 0700"
        )
    lock_path = output / ".attended.lock"
    if lock_path.is_symlink():
        raise ObservationalProgramError("output lock must not be a symlink")
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ObservationalProgramError(
                "output directory is already locked"
            ) from exc
        unexpected = sorted(
            path.name for path in output.iterdir() if path.name != lock_path.name
        )
        if unexpected:
            raise ObservationalProgramError(
                "output directory is not dedicated and empty"
            )
        started = _timestamp()
        start = {
            "state": "STARTED",
            "acceptance_hash": expected,
            "candidate_commit": acceptance["candidate_commit"],
            "candidate_tree": acceptance["candidate_tree"],
            "lane": profile.lane,
            "admission_bundle_id": acceptance["lane_admission_bundle_id"],
            "analysis_plan_sha256": acceptance["analysis_plan_sha256"],
            "worker_sha256": acceptance["worker_sha256"],
            "started_at_utc": started,
            "observed_data_opened": False,
            "observed_science_executed": False,
        }
        _atomic_json(output / "start.json", start)
        worker = prepared["worker"]
        assert isinstance(worker, Path)
        command = [
            str(Path(sys.executable).absolute()),
            "-B",
            str(worker),
            *prepared["worker_arguments"],
        ]
        exit_code: int | None = None
        signal_number: int | None = None
        try:
            if acceptance.get("science_execution"):
                data_root = prepared["data_root"]
                admission = prepared["admission_file"]
                assert isinstance(data_root, Path) and isinstance(admission, Path)
                command.extend(
                    [
                        "--admission",
                        str(admission),
                        "--data-root",
                        str(data_root),
                        "--output",
                        str(output / profile.result_filename),
                    ]
                )
            completed = _spawn_worker(
                command,
                root=root,
                environment=prepared["environment"],
                timeout=prepared["timeout_seconds"],
                output=output,
            )
            exit_code = completed.returncode
            state = completed.state
            if completed.state == "SIGNALED":
                assert completed.returncode is not None
                signal_number = -completed.returncode
                exit_code = None
        except OSError as exc:
            state = "FAILED"
            exit_code = 126
            (output / "stderr.log").write_text(str(exc), encoding="utf-8")
        observed_data_opened, marker_error = _observed_data_open_state(
            output, science=bool(acceptance.get("science_execution"))
        )
        output_error: str | None = marker_error
        if acceptance.get("science_execution") and state == "SUCCEEDED":
            if not observed_data_opened or marker_error is not None:
                state = "FAILED"
                exit_code = 125
        try:
            output_hashes = _output_hashes(output)
        except ObservationalProgramError as exc:
            output_hashes = {}
            output_error = output_error or str(exc)
            if state == "SUCCEEDED":
                state = "FAILED"
                exit_code = 125
        terminal = {
            "state": state,
            "acceptance_hash": expected,
            "exit_code": exit_code,
            "signal": signal_number,
            "ended_at_utc": _timestamp(),
            "stdout_sha256": (
                _file_hash(output / "stdout.log")
                if (output / "stdout.log").is_file()
                else None
            ),
            "stderr_sha256": (
                _file_hash(output / "stderr.log")
                if (output / "stderr.log").is_file()
                else None
            ),
            "output_hashes": output_hashes,
            "output_error": output_error,
            "observed_data_opened": observed_data_opened,
            "observed_science_executed": observed_data_opened,
        }
        _atomic_json(output / "terminal.json", terminal)
        return terminal


def _identity_worker() -> int:
    """Acknowledge an already replayed primary-lane identity without data."""

    if os.geteuid() == 0:
        return 2
    lane = os.environ.get("HTT_ATTENDED_LANE")
    try:
        _lane_profile(lane)
    except ObservationalProgramError:
        return 3
    print(
        json.dumps(
            {
                "state": f"{lane}_IDENTITY_REPLAYED",
                "observed_science_executed": False,
            },
            sort_keys=True,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    effective_argv = sys.argv[1:] if argv is None else argv
    if effective_argv == ["--identity-worker"]:
        return _identity_worker()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--data-root", type=Path)
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
            data_root=args.data_root,
        )
        if args.print_acceptance:
            if args.confirm is not None:
                raise ObservationalProgramError(
                    "--confirm is valid only with --execute"
                )
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
        if terminal["state"] == "INTERRUPTED":
            return 130
        return int(terminal["exit_code"] or 1)
    except ObservationalProgramError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
