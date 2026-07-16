#!/usr/bin/env python3
"""PR-121 tracked-only clean-install and detached replay harness.

The harness builds from the Git *index*, never the ambient worktree.  Its
receipts establish reproducibility mechanics only; they do not validate any
scientific result.  Network access and PR4 data work are outside this command.
"""
from __future__ import annotations

import argparse
import ast
import base64
import csv
from dataclasses import dataclass
import hashlib
import importlib.metadata as importlib_metadata
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile
from typing import Mapping, Sequence
import xml.etree.ElementTree as ET

try:  # Python 3.11+ stdlib; bass-py metadata supplies tomli on Python 3.10.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by import fallback probe
    import tomli as tomllib

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON_SRC = REPO_ROOT / "htt" / "src"
if str(COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(COMMON_SRC))

from common.package_topology import (  # noqa: E402
    PackageTopologyError,
    bind_files,
    canonical_json_bytes,
    canonicalize_sdist,
    declared_package_data,
    inspect_sdist,
    inspect_wheel,
    normalize_ephemeral_paths,
    safe_extract_git_archive,
    sha256_bytes,
    sha256_file,
    tree_hash,
    validate_compatibility_sdist,
    validate_declared_package_data,
    validate_fileless_compatibility_wheel,
    validate_main_wheel,
    validate_receipt_metadata,
    validate_wheel_collision,
    validate_archive_path,
    require_executed_tests,
    verify_wheel_record,
)


DEFAULT_SPEC = Path("docs/research_program/long_horizon_rescue/pr121_spec.yaml")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class HermeticReplayError(RuntimeError):
    """Raised when a replay cell cannot produce authoritative process evidence."""


@dataclass(frozen=True)
class CommandReceipt:
    argv: tuple[str, ...]
    cwd: str
    returncode: int
    stdout_sha256: str
    stderr_sha256: str
    stdout_tail: str
    stderr_tail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "cwd": self.cwd,
            "returncode": self.returncode,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
        }


@dataclass(frozen=True)
class ReplayPolicy:
    path: Path
    raw: Mapping[str, object]
    source_date_epoch: int
    main_project: str
    main_distribution: str
    compatibility_project: str
    compatibility_distribution: str
    exact_dependency: str
    owned_top_levels: tuple[str, ...]
    owner_modules: tuple[tuple[str, str], ...]
    compatibility_aliases: tuple[tuple[str, str], ...]
    install_matrix: tuple[str, ...]
    additional_distributions: tuple[str, ...]
    optional_imports: tuple[str, ...]
    optional_dispositions: Mapping[str, str]
    backlog: str
    status: str
    gate_outputs: str
    fixed_generated_on: str
    fixed_source_commit: str
    json_artifact: str
    markdown_artifact: str
    required_receipt_sections: tuple[str, ...]
    mutations: tuple[str, ...]
    caveats: tuple[str, ...]
    data_scope: Mapping[str, object]


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise HermeticReplayError(f"spec field {field} must be a mapping")
    return value


def _string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HermeticReplayError(f"spec field {field} must be a non-empty string")
    return value.strip()


def _sha256_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise HermeticReplayError(
            f"receipt field {field} must be a 64-character lowercase SHA-256"
        )
    return value


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HermeticReplayError(
            f"receipt field {field} must be a positive integer"
        )
    return value


def _string_list(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise HermeticReplayError(f"spec field {field} must be a non-empty list")
    return tuple(_string(item, field=field) for item in value)


def load_policy(path: Path) -> ReplayPolicy:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - bootstrap failure
        raise HermeticReplayError("PyYAML is required to read the tracked PR-121 spec") from exc
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    spec = _mapping(raw, field="root")
    if spec.get("schema") != "htt.long_horizon.pr121_hermetic.v1":
        raise HermeticReplayError(f"unsupported PR-121 spec schema: {spec.get('schema')!r}")
    if spec.get("pr_id") != "PR-121" or spec.get("owner") != "COMMON":
        raise HermeticReplayError("PR-121 spec identity/owner mismatch")
    if spec.get("claim_tier") != "diagnostic_only" or spec.get("transfer_source") != "none":
        raise HermeticReplayError("PR-121 spec exceeds diagnostic-only/no-transfer scope")
    projects = _mapping(spec.get("projects"), field="projects")
    main = _mapping(projects.get("main"), field="projects.main")
    compat = _mapping(projects.get("compatibility"), field="projects.compatibility")
    if compat.get("fileless") is not True:
        raise HermeticReplayError("compatibility distribution must be fileless")
    main_distribution = _string(main.get("distribution"), field="main.distribution")
    owned = _mapping(spec.get("owned_top_levels"), field="owned_top_levels")
    owner_rows = spec.get("owner_modules")
    alias_rows = spec.get("compatibility_aliases")
    if not isinstance(owner_rows, list) or not isinstance(alias_rows, list):
        raise HermeticReplayError("owner_modules and compatibility_aliases must be lists")
    dependency = _mapping(spec.get("dependency_layer"), field="dependency_layer")
    replay = _mapping(spec.get("replay"), field="replay")
    source_snapshot = _mapping(spec.get("source_snapshot"), field="source_snapshot")
    expected_dependency_policy = {
        "derive_project_dependencies": True,
        "require_record_closure": True,
        "require_content_hashes": True,
        "require_physical_read_only_tree": True,
        "require_content_and_mode_hash_before_after_every_cell": True,
    }
    for key, expected in expected_dependency_policy.items():
        if dependency.get(key) != expected:
            raise HermeticReplayError(
                f"dependency_layer.{key} must be {expected!r}"
            )
    expected_source_policy = {
        "authority": "git_index",
        "require_zero_untracked_inside_snapshot": True,
        "forbid_original_worktree_imports": True,
        "forbid_original_venv_imports": True,
        "network_access": "forbidden",
    }
    for key, expected in expected_source_policy.items():
        if source_snapshot.get(key) != expected:
            raise HermeticReplayError(
                f"source_snapshot.{key} must be {expected!r}"
            )
    expected_replay_policy = {
        "unrelated_cwd_required": True,
        "python_isolated_mode_required": True,
        "sanitize_pythonpath": True,
        "disable_user_site": True,
        "isolate_home_xdg_and_pip_cache": True,
        "isolate_tmpdir_per_cell": True,
        "require_structured_output_identity": True,
        "installed_cli_module": "common.status_snapshot",
        "require_cli_write_and_generated_companion_check": True,
    }
    for key, expected in expected_replay_policy.items():
        if replay.get(key) != expected:
            raise HermeticReplayError(f"replay.{key} must be {expected!r}")
    representative_outputs = _string_list(
        replay.get("representative_outputs"), field="replay.representative_outputs"
    )
    expected_outputs = (
        "status_snapshot.json",
        "claim_ledger.json",
        "status_matrix.md",
    )
    if representative_outputs != expected_outputs:
        raise HermeticReplayError(
            "replay.representative_outputs must be "
            f"{list(expected_outputs)!r}"
        )
    artifacts = _mapping(spec.get("artifacts"), field="artifacts")
    optional_dispositions = _mapping(
        dependency.get("missing_dispositions"), field="missing_dispositions"
    )
    policy = ReplayPolicy(
        path=path,
        raw=spec,
        source_date_epoch=int(spec.get("source_date_epoch", 0)),
        main_project=_string(main.get("path"), field="main.path"),
        main_distribution=main_distribution,
        compatibility_project=_string(compat.get("path"), field="compat.path"),
        compatibility_distribution=_string(
            compat.get("distribution"), field="compat.distribution"
        ),
        exact_dependency=_string(
            compat.get("exact_dependency"), field="compat.exact_dependency"
        ),
        owned_top_levels=_string_list(
            owned.get(main_distribution), field=f"owned_top_levels.{main_distribution}"
        ),
        owner_modules=tuple(
            (
                _string(_mapping(row, field="owner_modules[]").get("owner"), field="owner"),
                _string(_mapping(row, field="owner_modules[]").get("module"), field="module"),
            )
            for row in owner_rows
        ),
        compatibility_aliases=tuple(
            (
                _string(_mapping(row, field="aliases[]").get("canonical"), field="canonical"),
                _string(_mapping(row, field="aliases[]").get("alias"), field="alias"),
            )
            for row in alias_rows
        ),
        install_matrix=_string_list(spec.get("install_matrix"), field="install_matrix"),
        additional_distributions=_string_list(
            dependency.get("additional_distributions"), field="additional_distributions"
        ),
        optional_imports=_string_list(
            dependency.get("optional_imports"), field="optional_imports"
        ),
        optional_dispositions={
            str(key): _string(value, field=f"missing_dispositions.{key}")
            for key, value in optional_dispositions.items()
        },
        backlog=_string(replay.get("backlog"), field="replay.backlog"),
        status=_string(replay.get("status"), field="replay.status"),
        gate_outputs=_string(
            replay.get("gate_outputs"), field="replay.gate_outputs"
        ),
        fixed_generated_on=_string(
            replay.get("fixed_generated_on"), field="replay.fixed_generated_on"
        ),
        fixed_source_commit=_string(
            replay.get("fixed_source_commit"), field="replay.fixed_source_commit"
        ),
        json_artifact=_string(artifacts.get("json"), field="artifacts.json"),
        markdown_artifact=_string(artifacts.get("markdown"), field="artifacts.markdown"),
        required_receipt_sections=_string_list(
            spec.get("required_receipt_sections"), field="required_receipt_sections"
        ),
        mutations=_string_list(spec.get("mutations"), field="mutations"),
        caveats=_string_list(spec.get("caveats"), field="caveats"),
        data_scope=_mapping(spec.get("data_scope"), field="data_scope"),
    )
    expected_cells = {
        f"{kind}_{order}"
        for kind in ("direct", "sdist", "editable")
        for order in ("main_then_compat", "compat_then_main")
    }
    if set(policy.install_matrix) != expected_cells or len(policy.install_matrix) != 6:
        raise HermeticReplayError("install_matrix must contain the exact six PR-121 cells")
    if set(policy.optional_imports) != set(policy.optional_dispositions):
        raise HermeticReplayError("every optional import needs one missing disposition")
    if policy.source_date_epoch <= 0:
        raise HermeticReplayError("source_date_epoch must be a positive frozen value")
    return policy


def sanitized_environment(home: Path, *, source_date_epoch: int) -> dict[str, str]:
    """Return a cache/user-site/network sanitized child environment."""

    home.mkdir(parents=True, exist_ok=True)
    env = {
        "HOME": str(home),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_CACHE_DIR": "1",
        "PIP_NO_INDEX": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "SOURCE_DATE_EPOCH": str(source_date_epoch),
        "TZ": "UTC",
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_CONFIG_HOME": str(home / ".config"),
    }
    return env


def _root_tokens(extra: Mapping[Path, str] | None = None) -> dict[Path, str]:
    roots = {
        Path(sys.prefix).resolve(): "$HOST_VENV",
        REPO_ROOT.resolve(): "$REPO",
    }
    if extra:
        roots.update({path.resolve(): token for path, token in extra.items()})
    return roots


def _normalize_text(value: str, roots: Mapping[Path, str]) -> str:
    normalized = value
    for root, token in sorted(roots.items(), key=lambda item: len(str(item[0])), reverse=True):
        normalized = normalized.replace(str(root), token)
    normalized = normalize_ephemeral_paths(normalized)
    normalized = re.sub(r"\bin \d+(?:\.\d+)?s\b", "in $TIME", normalized)
    normalized = re.sub(r"\b\d+(?:\.\d+)? seconds\b", "$TIME seconds", normalized)
    return normalized


def run_checked(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int = 300,
    receipt_roots: Mapping[Path, str] | None = None,
) -> CommandReceipt:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    roots = _root_tokens(receipt_roots)
    normalized_stdout = _normalize_text(completed.stdout, roots)
    normalized_stderr = _normalize_text(completed.stderr, roots)
    receipt = CommandReceipt(
        argv=tuple(_normalize_text(str(item), roots) for item in argv),
        cwd=_normalize_text(str(cwd.resolve()), roots),
        returncode=completed.returncode,
        stdout_sha256=sha256_bytes(normalized_stdout.encode()),
        stderr_sha256=sha256_bytes(normalized_stderr.encode()),
        stdout_tail="\n".join(normalized_stdout.splitlines()[-12:]),
        stderr_tail="\n".join(normalized_stderr.splitlines()[-12:]),
    )
    if completed.returncode != 0:
        raise HermeticReplayError(
            f"command failed ({completed.returncode}): {' '.join(argv)}\n"
            f"stdout:\n{receipt.stdout_tail}\nstderr:\n{receipt.stderr_tail}"
        )
    return receipt


def run_json_checked(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int = 300,
    receipt_roots: Mapping[Path, str] | None = None,
) -> tuple[object, CommandReceipt]:
    """Run one process and parse its final non-empty stdout line as JSON."""

    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    roots = _root_tokens(receipt_roots)
    normalized_stdout = _normalize_text(completed.stdout, roots)
    normalized_stderr = _normalize_text(completed.stderr, roots)
    receipt = CommandReceipt(
        argv=tuple(_normalize_text(str(item), roots) for item in argv),
        cwd=_normalize_text(str(cwd.resolve()), roots),
        returncode=completed.returncode,
        stdout_sha256=sha256_bytes(normalized_stdout.encode()),
        stderr_sha256=sha256_bytes(normalized_stderr.encode()),
        stdout_tail="\n".join(normalized_stdout.splitlines()[-12:]),
        stderr_tail="\n".join(normalized_stderr.splitlines()[-12:]),
    )
    if completed.returncode != 0:
        raise HermeticReplayError(
            f"JSON command failed ({completed.returncode}): {' '.join(receipt.argv)}\n"
            f"stdout:\n{receipt.stdout_tail}\nstderr:\n{receipt.stderr_tail}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise HermeticReplayError("JSON command produced no stdout")
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise HermeticReplayError(
            f"JSON command final line is invalid: {receipt.stdout_tail}"
        ) from exc
    return payload, receipt


def materialize_index_snapshot(
    *, repo_root: Path, destination: Path, policy: ReplayPolicy, env: Mapping[str, str]
) -> dict[str, object]:
    """Materialize only the declared paths from the Git index tree."""

    declared = declared_index_roots(policy, repo_root=repo_root)
    projection = declared_index_projection(
        repo_root=repo_root, declared=declared, env=env
    )
    diff = subprocess.run(
        ["git", "diff", "--quiet", "--", *declared],
        cwd=repo_root,
        env=dict(env),
        check=False,
    )
    if diff.returncode != 0:
        raise HermeticReplayError(
            "declared tracked worktree bytes differ from the Git index"
        )
    receipt_roots = {
        destination.parent: "$TEMP",
        destination: "$DETACHED",
    }
    tree = run_checked(
        ["git", "write-tree"],
        cwd=repo_root,
        env=env,
        receipt_roots=receipt_roots,
    ).stdout_tail.strip()
    if not tree:
        raise HermeticReplayError("git write-tree returned no tree id")
    archive = destination.parent / "index-snapshot.tar"
    run_checked(
        ["git", "archive", "--format=tar", f"--output={archive}", tree, "--", *declared],
        cwd=repo_root,
        env=env,
        receipt_roots=receipt_roots,
    )
    members = safe_extract_git_archive(archive, destination)
    return {
        "authority": "git_index",
        "authority_id": f"sha256:{projection['hash']}",
        "declared_index_hash": projection["hash"],
        "declared_index_entry_count": projection["entry_count"],
        "archived_roots": list(declared),
        "member_count": len(members),
        "member_manifest_hash": sha256_bytes(canonical_json_bytes(members)),
        "source_tree_hash": tree_hash(destination),
        "contains_git_directory": False,
        "untracked_policy": "excluded_by_git_index_archive",
    }


def declared_index_roots(policy: ReplayPolicy, *, repo_root: Path) -> tuple[str, ...]:
    """Return the non-circular index authority used by write and check.

    Generated receipts and PR bookkeeping are intentionally not in this set.
    The full Git tree id remains useful provenance but cannot be a freshness
    authority because staging those generated outputs necessarily changes it.
    """

    return (
        policy.main_project,
        policy.backlog,
        policy.status,
        policy.gate_outputs,
        policy.path.relative_to(repo_root).as_posix(),
        "scripts/codex_harness/hermetic_replay.py",
        "tests/pr_cards/test_pr_121_hermetic_install_owner_namespace_detached_replay.py",
    )


def declared_index_projection(
    *, repo_root: Path, declared: Sequence[str], env: Mapping[str, str] | None = None
) -> dict[str, object]:
    """Hash modes, staged blobs, stages, and paths for declared index roots."""

    completed = subprocess.run(
        ["git", "ls-files", "-s", "-z", "--", *declared],
        cwd=repo_root,
        env=dict(env) if env is not None else None,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise HermeticReplayError(
            "git ls-files failed for declared inputs: "
            + completed.stderr.decode("utf-8", "replace").strip()
        )
    rows: list[dict[str, str]] = []
    paths: list[str] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
            mode, blob, stage = metadata.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise HermeticReplayError("malformed git index projection row") from exc
        if stage != "0":
            raise HermeticReplayError(f"unmerged index entry in declared inputs: {path}")
        rows.append({"mode": mode, "blob": blob, "stage": stage, "path": path})
        paths.append(path)
    for root in declared:
        if not any(path == root or path.startswith(root.rstrip("/") + "/") for path in paths):
            raise HermeticReplayError(f"declared input is absent from Git index: {root}")
    if not rows:
        raise HermeticReplayError("declared Git index projection is empty")
    rows.sort(key=lambda row: row["path"])
    return {
        "hash": sha256_bytes(canonical_json_bytes(rows)),
        "entry_count": len(rows),
        "rows": rows,
    }


@dataclass(frozen=True)
class DependencyLayer:
    root: Path
    site_packages: Path
    content_hash: str
    file_count: int
    directory_count: int
    distributions: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class BuildArtifacts:
    main_version: str
    compatibility_version: str
    direct_main_wheel: Path
    direct_compatibility_wheel: Path
    main_sdist: Path
    compatibility_sdist: Path
    sdist_main_wheel: Path
    sdist_compatibility_wheel: Path
    receipt: Mapping[str, object]


_DEPENDENCY_MODE_POLICY = "files=0444_or_0555;directories=0555"


def _seal_dependency_tree(root: Path) -> None:
    """Make the shared dependency layer physically non-writable."""

    if not root.is_dir() or root.is_symlink():
        raise HermeticReplayError(f"dependency layer root is not a regular directory: {root}")
    paths = sorted(root.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in paths:
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise HermeticReplayError(f"symlink in dependency layer: {path}")
        if stat.S_ISREG(mode):
            path.chmod(0o555 if mode & 0o111 else 0o444)
        elif stat.S_ISDIR(mode):
            path.chmod(0o555)
        else:
            raise HermeticReplayError(f"non-regular dependency layer entry: {path}")
    root.chmod(0o555)


def _dependency_manifest(root: Path) -> tuple[dict[str, object], ...]:
    """Return a content-and-full-mode manifest, rejecting writable entries."""

    if not root.is_dir() or root.is_symlink():
        raise HermeticReplayError(f"dependency layer root is not a regular directory: {root}")
    rows: list[dict[str, object]] = []
    for path in [root, *sorted(root.rglob("*"))]:
        mode = path.lstat().st_mode
        relative = "." if path == root else path.relative_to(root).as_posix()
        if stat.S_ISLNK(mode):
            raise HermeticReplayError(f"symlink in dependency layer manifest: {relative}")
        permissions = stat.S_IMODE(mode)
        if permissions & 0o222:
            raise HermeticReplayError(
                f"writable shared dependency layer entry: {relative} mode={permissions:04o}"
            )
        if stat.S_ISDIR(mode):
            rows.append(
                {
                    "path": relative,
                    "kind": "directory",
                    "mode": f"{permissions:04o}",
                }
            )
        elif stat.S_ISREG(mode):
            rows.append(
                {
                    "path": relative,
                    "kind": "file",
                    "mode": f"{permissions:04o}",
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        else:
            raise HermeticReplayError(
                f"non-regular dependency layer manifest entry: {relative}"
            )
    return tuple(rows)


def verify_dependency_layer(
    layer: DependencyLayer, *, phase: str
) -> dict[str, object]:
    """Fail when shared dependency bytes, modes, shape, or location drift."""

    try:
        layer.site_packages.resolve().relative_to(layer.root.resolve())
    except ValueError as exc:
        raise HermeticReplayError("dependency site-packages escapes the shared layer") from exc
    if not layer.site_packages.is_dir():
        raise HermeticReplayError("dependency layer site-packages is absent")
    manifest = _dependency_manifest(layer.root)
    content_hash = sha256_bytes(canonical_json_bytes(manifest))
    file_count = sum(row["kind"] == "file" for row in manifest)
    directory_count = sum(row["kind"] == "directory" for row in manifest)
    if content_hash != layer.content_hash:
        raise HermeticReplayError(
            f"dependency layer content/mode drift at {phase}: "
            f"expected={layer.content_hash}, actual={content_hash}"
        )
    if file_count != layer.file_count or directory_count != layer.directory_count:
        raise HermeticReplayError(
            f"dependency layer shape drift at {phase}: "
            f"files={file_count}/{layer.file_count}, "
            f"directories={directory_count}/{layer.directory_count}"
        )
    return {
        "phase": phase,
        "status": "pass",
        "content_mode_hash": content_hash,
        "file_count": file_count,
        "directory_count": directory_count,
        "writable_entry_count": 0,
        "mode_policy": _DEPENDENCY_MODE_POLICY,
    }


def _project_requirements(pyproject_path: Path) -> tuple[Requirement, ...]:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = _mapping(payload.get("project"), field="detached.pyproject.project")
    raw = project.get("dependencies", [])
    if not isinstance(raw, list):
        raise HermeticReplayError("detached project dependencies must be a list")
    try:
        return tuple(Requirement(str(item)) for item in raw)
    except InvalidRequirement as exc:
        raise HermeticReplayError(f"invalid detached project dependency: {exc}") from exc


def _record_rows(distribution: importlib_metadata.Distribution) -> list[list[str]]:
    record = Path(distribution._path) / "RECORD"  # type: ignore[attr-defined]
    if not record.is_file():
        raise HermeticReplayError(
            f"dependency distribution lacks RECORD: {distribution.metadata['Name']}"
        )
    rows = list(csv.reader(record.read_text(encoding="utf-8").splitlines()))
    if not rows or any(len(row) != 3 for row in rows):
        raise HermeticReplayError(f"malformed dependency RECORD: {record}")
    raw_paths = [row[0] for row in rows]
    if len(raw_paths) != len(set(raw_paths)):
        raise HermeticReplayError(f"duplicate dependency RECORD path: {record}")
    self_path = f"{Path(distribution._path).name}/RECORD"  # type: ignore[attr-defined]
    if raw_paths.count(self_path) != 1:
        raise HermeticReplayError(
            f"dependency RECORD must contain exactly one self row: {record}"
        )
    return rows


def _record_source(source_site: Path, source_prefix: Path, raw: str) -> Path:
    if not raw or "\\" in raw or "\x00" in raw:
        raise HermeticReplayError(f"unsafe dependency RECORD path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute():
        raise HermeticReplayError(f"absolute dependency RECORD path: {raw!r}")
    unresolved = source_site / Path(*path.parts)
    if unresolved.is_symlink():
        raise HermeticReplayError(f"dependency RECORD target is a symlink: {raw!r}")
    candidate = unresolved.resolve(strict=True)
    try:
        candidate.relative_to(source_prefix)
    except ValueError as exc:
        raise HermeticReplayError(
            f"dependency RECORD escapes current environment: {raw!r}"
        ) from exc
    if not candidate.is_file():
        raise HermeticReplayError(f"dependency RECORD is not a regular file: {raw!r}")
    return candidate


def _verify_record_digest(path: Path, encoded_hash: str, raw_size: str) -> None:
    if not encoded_hash.startswith("sha256=") or not raw_size.isdigit():
        raise HermeticReplayError(f"dependency RECORD lacks sha256/size: {path}")
    data = path.read_bytes()
    actual = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    if encoded_hash[7:].encode("ascii") != actual:
        raise HermeticReplayError(f"dependency RECORD hash mismatch: {path}")
    if int(raw_size) != len(data):
        raise HermeticReplayError(f"dependency RECORD size mismatch: {path}")


def _requirement_applies(requirement: Requirement) -> bool:
    return requirement.marker is None or requirement.marker.evaluate({"extra": ""})


def build_dependency_layer(
    *, detached_main: Path, destination: Path, additional: Sequence[str]
) -> DependencyLayer:
    """Copy a recursively closed, RECORD-verified layer from this venv.

    The layer preserves every installed RECORD-relative path below the current
    environment prefix, including compiled extension modules, ``*.libs`` and
    console scripts.  It is physically sealed read-only and attached to fresh
    venvs by one target-local ``.pth`` file; no original environment path is
    retained.
    """

    if sys.prefix == sys.base_prefix:
        raise HermeticReplayError("run PR-121 with the repository virtual environment")
    source_prefix = Path(sys.prefix).resolve()
    source_site = Path(sysconfig.get_paths()["purelib"]).resolve()
    try:
        site_relative = source_site.relative_to(source_prefix)
    except ValueError as exc:
        raise HermeticReplayError("current site-packages is outside sys.prefix") from exc
    requirements = list(_project_requirements(detached_main / "pyproject.toml"))
    requirements.extend(Requirement(name) for name in additional)
    selected: dict[str, importlib_metadata.Distribution] = {}
    queue = requirements[:]
    evaluated: list[str] = []
    while queue:
        requirement = queue.pop(0)
        if not _requirement_applies(requirement):
            continue
        if requirement.url is not None:
            raise HermeticReplayError(f"URL dependency is forbidden: {requirement}")
        key = canonicalize_name(requirement.name)
        try:
            distribution = importlib_metadata.distribution(requirement.name)
        except importlib_metadata.PackageNotFoundError as exc:
            raise HermeticReplayError(f"dependency is absent from current venv: {requirement}") from exc
        version = distribution.version
        if requirement.specifier and not requirement.specifier.contains(version, prereleases=True):
            raise HermeticReplayError(
                f"current venv {requirement.name}=={version} violates {requirement.specifier}"
            )
        evaluated.append(str(requirement))
        if key in selected:
            continue
        dist_root = Path(distribution._path).resolve()  # type: ignore[attr-defined]
        try:
            dist_root.relative_to(source_site)
        except ValueError as exc:
            raise HermeticReplayError(
                f"dependency metadata is outside current venv: {requirement.name} at {dist_root}"
            ) from exc
        selected[key] = distribution
        for raw_child in distribution.metadata.get_all("Requires-Dist") or []:
            try:
                queue.append(Requirement(raw_child))
            except InvalidRequirement as exc:
                raise HermeticReplayError(
                    f"invalid installed Requires-Dist for {requirement.name}: {raw_child}"
                ) from exc

    destination.mkdir(parents=True, exist_ok=False)
    target_site = destination / site_relative
    target_site.mkdir(parents=True)
    copied: dict[str, tuple[str, set[str]]] = {}
    dist_rows: list[dict[str, object]] = []
    for key, distribution in sorted(selected.items()):
        name = str(distribution.metadata["Name"])
        record_rows = _record_rows(distribution)
        record_self_seen = False
        generated_bytecode_excluded = 0
        for raw_path, encoded_hash, raw_size in record_rows:
            record_path = PurePosixPath(raw_path)
            if not encoded_hash and not raw_size:
                is_generated_bytecode = (
                    record_path.suffix in {".pyc", ".pyo"}
                    and "__pycache__" in record_path.parts
                )
                is_record_path = (
                    record_path.name == "RECORD"
                    and record_path.parent.name == Path(distribution._path).name
                )
                if is_generated_bytecode:
                    if (
                        not raw_path
                        or "\\" in raw_path
                        or "\x00" in raw_path
                        or record_path.is_absolute()
                        or any(part in {"", ".", ".."} for part in record_path.parts)
                    ):
                        raise HermeticReplayError(
                            f"unsafe generated-bytecode RECORD path: {name}:{raw_path!r}"
                        )
                    generated_bytecode_excluded += 1
                    continue
                if not is_record_path:
                    raise HermeticReplayError(
                        f"unhashed non-bytecode dependency RECORD row: {name}:{raw_path}"
                    )
            source = _record_source(source_site, source_prefix, raw_path)
            relative = source.relative_to(source_prefix).as_posix()
            is_record = source.name == "RECORD" and source.parent == Path(distribution._path)
            if is_record:
                if encoded_hash or raw_size:
                    raise HermeticReplayError(f"dependency RECORD self-row is not blank: {name}")
                record_self_seen = True
            else:
                _verify_record_digest(source, encoded_hash, raw_size)
            digest = sha256_file(source)
            previous = copied.get(relative)
            if previous is not None and previous[0] != digest:
                raise HermeticReplayError(f"dependency layer collision with unequal bytes: {relative}")
            if previous is None:
                target = destination / Path(relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied[relative] = (digest, {name})
            else:
                previous[1].add(name)
        if not record_self_seen:
            raise HermeticReplayError(f"dependency RECORD self-row missing: {name}")
        dist_rows.append(
            {
                "distribution": name,
                "normalized": key,
                "version": distribution.version,
                "record_entries": len(record_rows),
                "copied_record_entries": len(record_rows) - generated_bytecode_excluded,
                "generated_bytecode_excluded": generated_bytecode_excluded,
                "record_sha256": sha256_file(Path(distribution._path) / "RECORD"),
                "requires_dist": sorted(distribution.metadata.get_all("Requires-Dist") or []),
            }
        )
    if not any(".libs/" in path or path.endswith(".so") for path in copied):
        raise HermeticReplayError("dependency layer lacks compiled/.libs RECORD entries")
    _seal_dependency_tree(destination)
    manifest = _dependency_manifest(destination)
    layer = DependencyLayer(
        root=destination,
        site_packages=target_site,
        content_hash=sha256_bytes(canonical_json_bytes(manifest)),
        file_count=sum(row["kind"] == "file" for row in manifest),
        directory_count=sum(row["kind"] == "directory" for row in manifest),
        distributions=tuple(dist_rows),
    )
    verify_dependency_layer(layer, phase="post_seal")
    return layer


def _target_python(environment: Path) -> Path:
    candidate = environment / "bin" / "python"
    if not candidate.exists():
        raise HermeticReplayError(f"fresh environment lacks Python: {environment}")
    return candidate


def create_clean_environment(
    *,
    destination: Path,
    dependency_layer: DependencyLayer,
    env: Mapping[str, str],
    receipt_roots: Mapping[Path, str],
) -> CommandReceipt:
    receipt = run_checked(
        [sys.executable, "-I", "-m", "venv", "--without-pip", str(destination)],
        cwd=destination.parent,
        env=env,
        receipt_roots=receipt_roots,
    )
    candidates = sorted(destination.glob("lib/python*/site-packages"))
    if len(candidates) != 1:
        raise HermeticReplayError(
            f"fresh environment has ambiguous site-packages: {candidates}"
        )
    candidates[0].joinpath("pr121_dependency_layer.pth").write_text(
        str(dependency_layer.site_packages) + "\n", encoding="utf-8"
    )
    return receipt


def _normalize_tree_mtime(root: Path, epoch: int) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            raise HermeticReplayError(f"symlink in build source: {path}")
        if path.is_dir():
            path.chmod(0o755)
        elif path.is_file():
            path.chmod(0o755 if path.stat().st_mode & 0o100 else 0o644)
        os.utime(path, (epoch, epoch))
    root.chmod(0o755)
    os.utime(root, (epoch, epoch))


def _fresh_source(source: Path, destination: Path, *, epoch: int) -> Path:
    if destination.exists():
        raise HermeticReplayError(f"build source already exists: {destination}")
    shutil.copytree(source, destination)
    _normalize_tree_mtime(destination, epoch)
    return destination


def _backend_build(
    *,
    python: Path,
    source: Path,
    output: Path,
    operation: str,
    env: Mapping[str, str],
    receipt_roots: Mapping[Path, str],
) -> tuple[Path, CommandReceipt]:
    if operation not in {"build_wheel", "build_sdist"}:
        raise HermeticReplayError(f"unsupported build backend operation: {operation}")
    output.mkdir(parents=True, exist_ok=False)
    code = (
        "import pathlib,setuptools.build_meta as backend,sys;"
        f"name=backend.{operation}(sys.argv[1]);"
        "print(pathlib.Path(name).name)"
    )
    receipt = run_checked(
        [str(python), "-I", "-c", code, str(output)],
        cwd=source,
        env=env,
        timeout=600,
        receipt_roots=receipt_roots,
    )
    artifact_name = receipt.stdout_tail.splitlines()[-1].strip()
    artifact = output / artifact_name
    if not artifact.is_file():
        matches = sorted(output.iterdir())
        raise HermeticReplayError(
            f"backend did not produce declared artifact {artifact_name!r}; found {matches}"
        )
    return artifact, receipt


def _extract_sdist(source: Path, destination: Path, *, epoch: int) -> Path:
    import tarfile

    destination.mkdir(parents=True, exist_ok=False)
    roots: set[str] = set()
    with tarfile.open(source, "r:*") as archive:
        for member in archive.getmembers():
            normalized = member.name.rstrip("/")
            path = validate_archive_path(normalized)
            roots.add(path.parts[0])
            target = destination.joinpath(*path.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise HermeticReplayError(
                    f"sdist extraction rejects non-regular member: {member.name}"
                )
            source_file = archive.extractfile(member)
            if source_file is None:
                raise HermeticReplayError(f"cannot extract sdist member: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source_file.read())
            target.chmod(0o755 if member.mode & 0o100 else 0o644)
    if len(roots) != 1:
        raise HermeticReplayError(f"sdist extraction found roots: {sorted(roots)}")
    root = destination / next(iter(roots))
    _normalize_tree_mtime(root, epoch)
    return root


def build_project_artifacts(
    *,
    detached: Path,
    work: Path,
    dependency_layer: DependencyLayer,
    policy: ReplayPolicy,
    env: Mapping[str, str],
) -> BuildArtifacts:
    """Build and cross-check direct/sdist wheels from clean source copies."""

    work.mkdir(parents=True, exist_ok=False)
    receipt_roots = {
        work.parent: "$TEMP",
        detached: "$DETACHED",
        dependency_layer.root: "$DEPS",
        work: "$BUILD",
    }
    build_environment = work / "environment"
    environment_receipt = create_clean_environment(
        destination=build_environment,
        dependency_layer=dependency_layer,
        env=env,
        receipt_roots=receipt_roots,
    )
    python = _target_python(build_environment)
    main_source = detached / policy.main_project
    compatibility_source = detached / policy.compatibility_project
    declared_data = declared_package_data(main_source)
    commands: list[dict[str, object]] = [environment_receipt.as_dict()]

    direct_main, command = _backend_build(
        python=python,
        source=_fresh_source(
            main_source, work / "source-direct-main", epoch=policy.source_date_epoch
        ),
        output=work / "out-direct-main",
        operation="build_wheel",
        env=env,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    direct_compat, command = _backend_build(
        python=python,
        source=_fresh_source(
            compatibility_source,
            work / "source-direct-compat",
            epoch=policy.source_date_epoch,
        ),
        output=work / "out-direct-compat",
        operation="build_wheel",
        env=env,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    main_sdist, command = _backend_build(
        python=python,
        source=_fresh_source(
            main_source, work / "source-sdist-main", epoch=policy.source_date_epoch
        ),
        output=work / "out-sdist-main",
        operation="build_sdist",
        env=env,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    main_sdist_canonicalization = canonicalize_sdist(
        main_sdist, source_date_epoch=policy.source_date_epoch
    )
    compat_sdist, command = _backend_build(
        python=python,
        source=_fresh_source(
            compatibility_source,
            work / "source-sdist-compat",
            epoch=policy.source_date_epoch,
        ),
        output=work / "out-sdist-compat",
        operation="build_sdist",
        env=env,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    compat_sdist_canonicalization = canonicalize_sdist(
        compat_sdist, source_date_epoch=policy.source_date_epoch
    )

    main_sdist_inspection = inspect_sdist(main_sdist)
    compat_sdist_inspection = inspect_sdist(compat_sdist)
    main_direct_inspection = inspect_wheel(direct_main)
    compat_direct_inspection = inspect_wheel(direct_compat)
    validate_main_wheel(
        main_direct_inspection,
        expected_distribution=policy.main_distribution,
        owned_top_levels=policy.owned_top_levels,
    )
    validate_fileless_compatibility_wheel(
        compat_direct_inspection,
        expected_distribution=policy.compatibility_distribution,
        exact_dependency=policy.exact_dependency,
        exact_version=main_direct_inspection.version,
    )
    validate_compatibility_sdist(
        compat_sdist_inspection,
        expected_distribution=policy.compatibility_distribution,
        exact_dependency=policy.exact_dependency,
        exact_version=main_direct_inspection.version,
    )
    validate_wheel_collision(main_direct_inspection, compat_direct_inspection)

    extracted_main = _extract_sdist(
        main_sdist, work / "extract-main", epoch=policy.source_date_epoch
    )
    extracted_compat = _extract_sdist(
        compat_sdist, work / "extract-compat", epoch=policy.source_date_epoch
    )
    sdist_main_wheel, command = _backend_build(
        python=python,
        source=extracted_main,
        output=work / "out-wheel-from-main-sdist",
        operation="build_wheel",
        env=env,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    sdist_compat_wheel, command = _backend_build(
        python=python,
        source=extracted_compat,
        output=work / "out-wheel-from-compat-sdist",
        operation="build_wheel",
        env=env,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    main_sdist_wheel_inspection = inspect_wheel(sdist_main_wheel)
    compat_sdist_wheel_inspection = inspect_wheel(sdist_compat_wheel)
    validate_main_wheel(
        main_sdist_wheel_inspection,
        expected_distribution=policy.main_distribution,
        owned_top_levels=policy.owned_top_levels,
    )
    validate_fileless_compatibility_wheel(
        compat_sdist_wheel_inspection,
        expected_distribution=policy.compatibility_distribution,
        exact_dependency=policy.exact_dependency,
        exact_version=main_direct_inspection.version,
    )
    validate_wheel_collision(main_sdist_wheel_inspection, compat_sdist_wheel_inspection)
    if main_direct_inspection.sha256 != main_sdist_wheel_inspection.sha256:
        raise HermeticReplayError(
            "direct and sdist-built main wheels are not byte-identical: "
            f"direct={main_direct_inspection.sha256}/payload={main_direct_inspection.payload_hash}; "
            f"sdist={main_sdist_wheel_inspection.sha256}/payload={main_sdist_wheel_inspection.payload_hash}"
        )
    if compat_direct_inspection.sha256 != compat_sdist_wheel_inspection.sha256:
        raise HermeticReplayError(
            "direct and sdist-built compatibility wheels are not byte-identical"
        )
    package_data_receipts = {
        "direct": validate_declared_package_data(direct_main, declared_data),
        "sdist": validate_declared_package_data(sdist_main_wheel, declared_data),
        "entries": [row.as_dict() for row in declared_data],
    }
    record_receipts = {
        "direct_main": verify_wheel_record(direct_main),
        "direct_compatibility": verify_wheel_record(direct_compat),
        "sdist_main": verify_wheel_record(sdist_main_wheel),
        "sdist_compatibility": verify_wheel_record(sdist_compat_wheel),
    }
    return BuildArtifacts(
        main_version=main_direct_inspection.version,
        compatibility_version=compat_direct_inspection.version,
        direct_main_wheel=direct_main,
        direct_compatibility_wheel=direct_compat,
        main_sdist=main_sdist,
        compatibility_sdist=compat_sdist,
        sdist_main_wheel=sdist_main_wheel,
        sdist_compatibility_wheel=sdist_compat_wheel,
        receipt={
            "commands": commands,
            "main_direct": main_direct_inspection.as_dict(),
            "compatibility_direct": compat_direct_inspection.as_dict(),
            "main_sdist": main_sdist_inspection.as_dict(),
            "compatibility_sdist": compat_sdist_inspection.as_dict(),
            "sdist_canonicalization": {
                "main": main_sdist_canonicalization,
                "compatibility": compat_sdist_canonicalization,
            },
            "main_from_sdist": main_sdist_wheel_inspection.as_dict(),
            "compatibility_from_sdist": compat_sdist_wheel_inspection.as_dict(),
            "package_data": package_data_receipts,
            "wheel_records": record_receipts,
            "direct_sdist_byte_identity": "pass",
        },
    )


_IMPORT_PROBE = r"""
import importlib, importlib.metadata, json, pathlib, sys
owners = json.loads(sys.argv[1])
aliases = json.loads(sys.argv[2])
top_levels = json.loads(sys.argv[3])
project_dists = {name.lower().replace('_', '-') for name in json.loads(sys.argv[4])}
modules = {}
for owner, name in owners:
    module = importlib.import_module(name)
    modules[name] = {
        'owner': owner,
        'origin': str(pathlib.Path(module.__file__).resolve()),
    }
alias_rows = []
for canonical_name, alias_name in aliases:
    canonical = importlib.import_module(canonical_name)
    alias = importlib.import_module(alias_name)
    if canonical is not alias:
        raise RuntimeError(f'alias identity mismatch: {canonical_name} != {alias_name}')
    alias_rows.append({
        'canonical': canonical_name,
        'alias': alias_name,
        'identity': 'same_object',
        'origin': str(pathlib.Path(canonical.__file__).resolve()),
    })
package_owners = importlib.metadata.packages_distributions()
ownership = {}
for top_level in top_levels:
    selected = sorted({
        value for value in package_owners.get(top_level, [])
        if value.lower().replace('_', '-') in project_dists
    })
    ownership[top_level] = selected
print(json.dumps({
    'modules': modules,
    'aliases': alias_rows,
    'ownership': ownership,
    'sys_path': [str(pathlib.Path(item or '.').resolve()) for item in sys.path],
    'python_isolated': bool(sys.flags.isolated),
    'user_site_disabled': not bool(__import__('site').ENABLE_USER_SITE),
}, sort_keys=True, separators=(',', ':')))
"""


_STATUS_REPLAY_CHECK = r"""
from datetime import datetime
import hashlib, json, pathlib, sys
from common.status_snapshot import validate_status_matrix_matches_snapshot

snapshot_path = pathlib.Path(sys.argv[1])
claim_path = pathlib.Path(sys.argv[2])
matrix_path = pathlib.Path(sys.argv[3])
fixed_generated_on = sys.argv[4]
fixed_source_commit = sys.argv[5]
normalized_path = pathlib.Path(sys.argv[6])

def load_canonical(path):
    raw = path.read_text(encoding='utf-8')
    payload = json.loads(raw)
    expected = json.dumps(payload, indent=2, sort_keys=True) + '\n'
    if raw != expected:
        raise RuntimeError(f'non-canonical generated JSON: {path.name}')
    return payload

snapshot = load_canonical(snapshot_path)
claim_ledger = load_canonical(claim_path)
matrix = matrix_path.read_text(encoding='utf-8')
validate_status_matrix_matches_snapshot(matrix, snapshot)

snapshot_metadata = snapshot.get('metadata', {})
claim_metadata = claim_ledger.get('metadata', {})
raw_generated_on = snapshot_metadata.get('generated_on')
if not isinstance(raw_generated_on, str) or not raw_generated_on:
    raise RuntimeError('status CLI omitted generated_on')
datetime.fromisoformat(raw_generated_on)
if claim_metadata.get('generated_on') != raw_generated_on:
    raise RuntimeError('status and claim generated_on values differ')
if snapshot_metadata.get('source_commit') != fixed_source_commit:
    raise RuntimeError('status CLI source_commit override failed')
if claim_metadata.get('source_commit') != fixed_source_commit:
    raise RuntimeError('claim CLI source_commit override failed')

status_rows = snapshot.get('rows', [])
claim_rows = claim_ledger.get('rows', [])
if not isinstance(status_rows, list) or not isinstance(claim_rows, list):
    raise RuntimeError('status CLI rows are not lists')
if [row.get('artifact_id') for row in status_rows] != [
    row.get('artifact_id') for row in claim_rows
]:
    raise RuntimeError('status/claim artifact row identity drift')
if any(row.get('source_commit') != fixed_source_commit for row in status_rows):
    raise RuntimeError('status row source_commit drift')
if any(row.get('source_commit') != fixed_source_commit for row in claim_rows):
    raise RuntimeError('claim row source_commit drift')
if snapshot_metadata.get('input_hashes') != claim_metadata.get('input_hashes'):
    raise RuntimeError('status/claim input hash drift')
if raw_generated_on in matrix:
    raise RuntimeError('status matrix must exclude nondeterministic generated_on')

snapshot = dict(snapshot)
claim_ledger = dict(claim_ledger)
snapshot['metadata'] = {**snapshot_metadata, 'generated_on': fixed_generated_on}
claim_ledger['metadata'] = {**claim_metadata, 'generated_on': fixed_generated_on}
normalized_matrix = matrix
structured = {
    'snapshot': snapshot,
    'claim_ledger': claim_ledger,
    'status_matrix_sha256': hashlib.sha256(normalized_matrix.encode()).hexdigest(),
    'write_check': {
        'cli_module': 'common.status_snapshot',
        'canonical_json_companions': True,
        'status_matrix_parser': 'validate_status_matrix_matches_snapshot',
        'status_matrix_matches_snapshot': True,
        'claim_status_artifact_identity': True,
        'status_matrix_excludes_generated_on': True,
        'generated_on_normalized_to_policy': True,
    },
}
serialized = json.dumps(structured, sort_keys=True, separators=(',', ':')) + '\n'
normalized_path.write_text(serialized, encoding='utf-8')
print(json.dumps({
    'checks': structured['write_check'],
    'structured_hash': hashlib.sha256(serialized.encode()).hexdigest(),
}, sort_keys=True, separators=(',', ':')))
"""

_EXPECTED_STATUS_REPLAY_CHECKS: Mapping[str, object] = {
    "cli_module": "common.status_snapshot",
    "canonical_json_companions": True,
    "status_matrix_parser": "validate_status_matrix_matches_snapshot",
    "status_matrix_matches_snapshot": True,
    "claim_status_artifact_identity": True,
    "status_matrix_excludes_generated_on": True,
    "generated_on_normalized_to_policy": True,
}


_OPTIONAL_PROBE = r"""
import importlib.util, json, sys
print(json.dumps({name: (importlib.util.find_spec(name) is not None) for name in json.loads(sys.argv[1])}, sort_keys=True, separators=(',', ':')))
"""


def _assert_project_probe(
    payload: object,
    *,
    policy: ReplayPolicy,
    cell_root: Path,
    forbidden: Sequence[Path],
) -> Mapping[str, object]:
    probe = _mapping(payload, field="import probe")
    modules = _mapping(probe.get("modules"), field="import probe.modules")
    ownership = _mapping(probe.get("ownership"), field="import probe.ownership")
    if probe.get("python_isolated") is not True or probe.get("user_site_disabled") is not True:
        raise HermeticReplayError("import probe did not run with isolated/user-site-disabled Python")
    for top_level in policy.owned_top_levels:
        if ownership.get(top_level) != [policy.main_distribution]:
            raise HermeticReplayError(
                f"project distribution ownership mismatch for {top_level}: {ownership.get(top_level)}"
            )
    for _, module_name in policy.owner_modules:
        row = _mapping(modules.get(module_name), field=f"module {module_name}")
        origin = Path(_string(row.get("origin"), field=f"origin {module_name}")).resolve()
        try:
            origin.relative_to(cell_root.resolve())
        except ValueError as exc:
            raise HermeticReplayError(
                f"project module {module_name} escaped clean cell: {origin}"
            ) from exc
    serialized = json.dumps(probe, sort_keys=True)
    for path in forbidden:
        if str(path.resolve()) in serialized:
            raise HermeticReplayError(f"clean import leaked forbidden path: {path}")
    return probe


def _probe_imports(
    *,
    python: Path,
    cwd: Path,
    env: Mapping[str, str],
    policy: ReplayPolicy,
    receipt_roots: Mapping[Path, str],
    cell_root: Path,
) -> tuple[Mapping[str, object], CommandReceipt]:
    payload, receipt = run_json_checked(
        [
            str(python),
            "-I",
            "-c",
            _IMPORT_PROBE,
            json.dumps(policy.owner_modules),
            json.dumps(policy.compatibility_aliases),
            json.dumps(policy.owned_top_levels),
            json.dumps([policy.main_distribution, policy.compatibility_distribution]),
        ],
        cwd=cwd,
        env=env,
        receipt_roots=receipt_roots,
    )
    probe = _assert_project_probe(
        payload,
        policy=policy,
        cell_root=cell_root,
        forbidden=(REPO_ROOT, Path(sys.prefix)),
    )
    return probe, receipt


def _mirror_replay_inputs(*, detached: Path, cwd: Path, policy: ReplayPolicy) -> tuple[str, str, str]:
    mirror = cwd / "mirror"
    results: list[str] = []
    for raw in (policy.backlog, policy.status, policy.gate_outputs):
        relative = Path(raw)
        source = detached / relative
        target = mirror / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        results.append(target.relative_to(cwd).as_posix())
    return results[0], results[1], results[2]


def _replay_status(
    *,
    python: Path,
    cwd: Path,
    detached: Path,
    env: Mapping[str, str],
    policy: ReplayPolicy,
    receipt_roots: Mapping[Path, str],
) -> tuple[
    Mapping[str, object],
    str,
    tuple[CommandReceipt, CommandReceipt],
    Mapping[str, object],
]:
    backlog, status, gate_outputs = _mirror_replay_inputs(
        detached=detached, cwd=cwd, policy=policy
    )
    snapshot = "generated/status_snapshot.json"
    claim_ledger = "generated/claim_ledger.json"
    status_matrix = "generated/status_matrix.md"
    normalized = "generated/normalized_replay.json"
    cli_receipt = run_checked(
        [
            str(python),
            "-I",
            "-m",
            "common.status_snapshot",
            "--backlog",
            backlog,
            "--status",
            status,
            "--gate-outputs",
            gate_outputs,
            "--source-commit",
            policy.fixed_source_commit,
            "--write",
            snapshot,
        ],
        cwd=cwd,
        env=env,
        timeout=600,
        receipt_roots=receipt_roots,
    )
    summary, check_receipt = run_json_checked(
        [
            str(python),
            "-I",
            "-c",
            _STATUS_REPLAY_CHECK,
            snapshot,
            claim_ledger,
            status_matrix,
            policy.fixed_generated_on,
            policy.fixed_source_commit,
            normalized,
        ],
        cwd=cwd,
        env=env,
        timeout=600,
        receipt_roots=receipt_roots,
    )
    summary_row = _mapping(summary, field="status replay check summary")
    checks = _mapping(summary_row.get("checks"), field="status replay checks")
    if checks != _EXPECTED_STATUS_REPLAY_CHECKS:
        raise HermeticReplayError(f"installed status CLI check drift: {checks}")
    normalized_path = cwd / normalized
    raw_normalized = normalized_path.read_bytes()
    structured = _mapping(json.loads(raw_normalized), field="status replay")
    if raw_normalized != canonical_json_bytes(structured):
        raise HermeticReplayError("normalized status replay is not canonical JSON")
    structured_hash = sha256_bytes(raw_normalized)
    if summary_row.get("structured_hash") != structured_hash:
        raise HermeticReplayError("installed status parser hash mismatch")
    return (
        structured,
        structured_hash,
        (cli_receipt, check_receipt),
        checks,
    )


def _optional_statuses(
    *,
    python: Path,
    cwd: Path,
    env: Mapping[str, str],
    policy: ReplayPolicy,
    receipt_roots: Mapping[Path, str],
) -> tuple[dict[str, dict[str, object]], CommandReceipt]:
    payload, receipt = run_json_checked(
        [str(python), "-I", "-c", _OPTIONAL_PROBE, json.dumps(policy.optional_imports)],
        cwd=cwd,
        env=env,
        receipt_roots=receipt_roots,
    )
    available = _mapping(payload, field="optional probe")
    rows: dict[str, dict[str, object]] = {}
    for name in policy.optional_imports:
        present = available.get(name)
        if not isinstance(present, bool):
            raise HermeticReplayError(f"optional probe lacks boolean status for {name}")
        rows[name] = {
            "available": present,
            "status": "available_excluded_from_pass_count"
            if present
            else policy.optional_dispositions[name],
            "counted_as_pass": False,
        }
    return rows, receipt


def _pytest_counts(path: Path) -> dict[str, object]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    total = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", 0)) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", 0)) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
    executed = total - skipped
    require_executed_tests(executed, selector="PR-121 clean isolated pytest")
    if failures or errors:
        raise HermeticReplayError(
            f"clean pytest reports failures={failures}, errors={errors}"
        )
    return {
        "total": total,
        "executed": executed,
        "passed": executed - failures - errors,
        "skipped": skipped,
        "failures": failures,
        "errors": errors,
        "blockers": 0,
        "testcases": sorted(
            str(case.attrib.get("name", ""))
            for suite in suites
            for case in suite.iter("testcase")
            if case.attrib.get("name")
        ),
    }


def _run_cell_tests(
    *,
    python: Path,
    cwd: Path,
    env: Mapping[str, str],
    selector: str | Path,
    cell_root: Path,
    receipt_roots: Mapping[Path, str],
) -> tuple[dict[str, object], CommandReceipt]:
    junit = cell_root / "pytest-junit.xml"
    selector_args = (
        ["--pyargs", selector]
        if isinstance(selector, str)
        else [str(selector)]
    )
    receipt = run_checked(
        [
            str(python),
            "-I",
            "-m",
            "pytest",
            "--import-mode=importlib",
            "-p",
            "no:cacheprovider",
            "-q",
            f"--junitxml={junit}",
            *selector_args,
        ],
        cwd=cwd,
        env=env,
        timeout=900,
        receipt_roots=receipt_roots,
    )
    return _pytest_counts(junit), receipt


def _editable_compatibility_receipt(
    *, environment: Path, compatibility_source: Path
) -> dict[str, object]:
    site_candidates = sorted(environment.glob("lib/python*/site-packages"))
    if len(site_candidates) != 1:
        raise HermeticReplayError("cannot locate editable target site-packages")
    site = site_candidates[0]
    dist_infos = sorted(site.glob("htt-*.dist-info"))
    if len(dist_infos) != 1:
        raise HermeticReplayError(f"editable compatibility metadata ambiguous: {dist_infos}")
    record_rows = list(
        csv.reader((dist_infos[0] / "RECORD").read_text(encoding="utf-8").splitlines())
    )
    editable_files: list[Path] = []
    for row in record_rows:
        if len(row) != 3:
            raise HermeticReplayError("malformed editable compatibility RECORD")
        raw = row[0]
        if "__editable__" not in raw:
            continue
        candidate = (site / Path(*PurePosixPath(raw).parts)).resolve()
        try:
            candidate.relative_to(environment.resolve())
        except ValueError as exc:
            raise HermeticReplayError(f"editable compatibility file escapes cell: {raw}") from exc
        if candidate.is_file():
            editable_files.append(candidate)
    mappings: list[object] = []
    namespaces: list[object] = []
    compatibility_root = str(compatibility_source.resolve())
    for path in editable_files:
        if path.suffix not in {".py", ".pth"}:
            continue
        text = path.read_text(encoding="utf-8")
        if compatibility_root in text:
            raise HermeticReplayError(
                "editable compatibility metadata exposes its source-root path"
            )
        if path.suffix != ".py":
            continue
        for node in ast.parse(text, filename=str(path)).body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if not isinstance(target, ast.Name) or target.id not in {"MAPPING", "NAMESPACES"}:
                    continue
                parsed = ast.literal_eval(value)
                if target.id == "MAPPING":
                    mappings.append(parsed)
                else:
                    namespaces.append(parsed)
    if any(value not in ({}, []) for value in [*mappings, *namespaces]):
        raise HermeticReplayError(
            f"editable compatibility finder owns packages: mappings={mappings}, namespaces={namespaces}"
        )
    finder_count = sum(path.suffix == ".py" for path in editable_files)
    pth_count = sum(path.suffix == ".pth" for path in editable_files)
    if finder_count < 1 or pth_count < 1 or not mappings or not namespaces:
        raise HermeticReplayError(
            "editable compatibility evidence is vacuous; expected a finder, .pth, "
            "and observed empty MAPPING/NAMESPACES assignments"
        )
    return {
        "status": "pass",
        "finder_file_count": finder_count,
        "pth_file_count": pth_count,
        "mappings": mappings,
        "namespaces": namespaces,
        "source_root_exposed": False,
    }


def _smoke_selector(
    *, python: Path, cwd: Path, env: Mapping[str, str], receipt_roots: Mapping[Path, str]
) -> tuple[Path, CommandReceipt]:
    code = (
        "import bass.validation.test_d2_regression_anchor as module,json;"
        "print(json.dumps({'path':module.__file__},sort_keys=True,separators=(',',':')))"
    )
    payload, receipt = run_json_checked(
        [str(python), "-I", "-c", code],
        cwd=cwd,
        env=env,
        receipt_roots=receipt_roots,
    )
    row = _mapping(payload, field="smoke selector")
    selector = Path(_string(row.get("path"), field="smoke selector path")).resolve()
    if not selector.is_file():
        raise HermeticReplayError(f"installed smoke selector is absent: {selector}")
    return selector, receipt


def run_install_cell(
    *,
    cell: str,
    index: int,
    root: Path,
    detached: Path,
    dependency_layer: DependencyLayer,
    artifacts: BuildArtifacts,
    policy: ReplayPolicy,
    base_env: Mapping[str, str],
) -> dict[str, object]:
    cell_root = root / cell
    cell_root.mkdir(parents=True, exist_ok=False)
    environment = cell_root / "environment"
    unrelated = cell_root / "unrelated-cwd"
    unrelated.mkdir()
    hostile_pythonpath = cell_root / "hostile-pythonpath"
    hostile_pythonpath.mkdir()
    hostile_user_site = cell_root / "home" / ".local" / "lib" / "python3.12" / "site-packages"
    hostile_user_site.mkdir(parents=True)
    hostile_cache = cell_root / "hostile-cache"
    hostile_cache.mkdir()
    process_tmp = cell_root / "process-tmp"
    process_tmp.mkdir()
    for directory in (unrelated, hostile_pythonpath, hostile_user_site, hostile_cache):
        directory.joinpath("htt.py").write_text(
            "raise RuntimeError('PR121 hostile htt sentinel imported')\n", encoding="utf-8"
        )
        directory.joinpath("sitecustomize.py").write_text(
            "raise RuntimeError('PR121 hostile sitecustomize imported')\n", encoding="utf-8"
        )
    hostile_cache_before = tree_hash(hostile_cache)
    env = dict(base_env)
    env["HOME"] = str(cell_root / "home")
    env["PYTHONPATH"] = str(hostile_pythonpath)
    env["PIP_CACHE_DIR"] = str(hostile_cache)
    env["XDG_CACHE_HOME"] = str(cell_root / "xdg-cache")
    env["TMPDIR"] = str(process_tmp)
    receipt_roots = {
        root.parent: "$TEMP",
        detached: "$DETACHED",
        dependency_layer.root: "$DEPS",
        cell_root: "$CELL",
    }
    dependency_before = verify_dependency_layer(
        dependency_layer, phase=f"{cell}:before"
    )
    commands: list[dict[str, object]] = []
    commands.append(
        create_clean_environment(
            destination=environment,
            dependency_layer=dependency_layer,
            env=env,
            receipt_roots=receipt_roots,
        ).as_dict()
    )
    python = _target_python(environment)
    kind, order = cell.split("_", 1)
    if order not in {"main_then_compat", "compat_then_main"}:
        raise HermeticReplayError(f"invalid cell order: {cell}")
    main_input: Path
    compat_input: Path
    editable_receipt: dict[str, object] | None = None
    pip_common = [str(python), "-I", "-m", "pip", "install", "--no-index"]
    if kind == "direct":
        main_input = artifacts.direct_main_wheel
        compat_input = artifacts.direct_compatibility_wheel
    elif kind == "sdist":
        main_input = artifacts.main_sdist
        compat_input = artifacts.compatibility_sdist
        pip_common.extend(["--no-build-isolation"])
    elif kind == "editable":
        main_input = _fresh_source(
            detached / policy.main_project,
            cell_root / "editable-main",
            epoch=policy.source_date_epoch,
        )
        compat_input = _fresh_source(
            detached / policy.compatibility_project,
            cell_root / "editable-compatibility",
            epoch=policy.source_date_epoch,
        )
        pip_common.extend(["--no-build-isolation"])
    else:
        raise HermeticReplayError(f"invalid cell kind: {cell}")

    if cell == "direct_compat_then_main":
        wheelhouse = cell_root / "wheelhouse"
        wheelhouse.mkdir()
        shutil.copy2(artifacts.direct_main_wheel, wheelhouse / artifacts.direct_main_wheel.name)
        shutil.copy2(
            artifacts.direct_compatibility_wheel,
            wheelhouse / artifacts.direct_compatibility_wheel.name,
        )
        resolver = [
            str(python),
            "-I",
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            f"{policy.compatibility_distribution}=={artifacts.compatibility_version}",
        ]
        commands.append(
            run_checked(
                resolver,
                cwd=unrelated,
                env=env,
                timeout=900,
                receipt_roots=receipt_roots,
            ).as_dict()
        )
        resolution_mode = "normal_offline_resolver_exact_dependency"
    else:
        resolution_mode = "explicit_no_deps_order_probe"
        ordered = (
            (main_input, compat_input)
            if order == "main_then_compat"
            else (compat_input, main_input)
        )
        for artifact in ordered:
            install_tail = (
                ["--no-deps", "-e", str(artifact)]
                if kind == "editable"
                else ["--no-deps", str(artifact)]
            )
            commands.append(
                run_checked(
                    [*pip_common, *install_tail],
                    cwd=unrelated,
                    env=env,
                    timeout=900,
                    receipt_roots=receipt_roots,
                ).as_dict()
            )
    commands.append(
        run_checked(
            [str(python), "-I", "-m", "pip", "check"],
            cwd=unrelated,
            env=env,
            receipt_roots=receipt_roots,
        ).as_dict()
    )
    if kind == "editable":
        editable_receipt = _editable_compatibility_receipt(
            environment=environment, compatibility_source=compat_input
        )

    pre_probe, command = _probe_imports(
        python=python,
        cwd=unrelated,
        env=env,
        policy=policy,
        receipt_roots=receipt_roots,
        cell_root=cell_root,
    )
    commands.append(command.as_dict())
    selector: str | Path
    if index == 0:
        selector = detached / "tests/pr_cards/test_pr_121_hermetic_install_owner_namespace_detached_replay.py"
        selector_kind = "pr121_card"
    else:
        _selector_path, command = _smoke_selector(
            python=python, cwd=unrelated, env=env, receipt_roots=receipt_roots
        )
        commands.append(command.as_dict())
        selector = "bass.validation.test_d2_regression_anchor"
        selector_kind = "installed_d2_smoke_anchor"
    test_counts, command = _run_cell_tests(
        python=python,
        cwd=unrelated,
        env=env,
        selector=selector,
        cell_root=cell_root,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    post_probe, command = _probe_imports(
        python=python,
        cwd=unrelated,
        env=env,
        policy=policy,
        receipt_roots=receipt_roots,
        cell_root=cell_root,
    )
    commands.append(command.as_dict())
    if pre_probe != post_probe:
        raise HermeticReplayError(f"import origins changed across pytest in {cell}")
    optional, command = _optional_statuses(
        python=python,
        cwd=unrelated,
        env=env,
        policy=policy,
        receipt_roots=receipt_roots,
    )
    commands.append(command.as_dict())
    structured, structured_hash, replay_commands, generator_replay = _replay_status(
        python=python,
        cwd=unrelated,
        detached=detached,
        env=env,
        policy=policy,
        receipt_roots=receipt_roots,
    )
    commands.extend(command.as_dict() for command in replay_commands)
    normalized_probe = json.loads(
        _normalize_text(json.dumps(pre_probe), _root_tokens(receipt_roots))
    )
    hostile_cache_after = tree_hash(hostile_cache)
    if hostile_cache_before != hostile_cache_after:
        raise HermeticReplayError("pip hostile cache sentinel changed during clean cell")
    dependency_after = verify_dependency_layer(
        dependency_layer, phase=f"{cell}:after"
    )
    return {
        "cell": cell,
        "status": "pass",
        "kind": kind,
        "order": order,
        "resolution_mode": resolution_mode,
        "tests": {**test_counts, "selector_kind": selector_kind},
        "structured_hash": structured_hash,
        "structured_schema": _mapping(structured.get("snapshot"), field="snapshot")
        .get("metadata", {}),
        "generator_replay": dict(generator_replay),
        "import_probe": normalized_probe,
        "pre_post_origin_identity": "pass",
        "optional_dependencies": optional,
        "editable_compatibility": editable_receipt,
        "commands": commands,
        "dependency_layer_guard": {
            "before": dependency_before,
            "after": dependency_after,
            "unchanged": True,
        },
        "hostile_sentinels": {
            "unrelated_cwd": "ignored",
            "pythonpath": "ignored_by_isolated_mode",
            "user_site": "disabled",
            "pip_cache": "disabled_and_pre_post_immutable",
            "pip_cache_tree_hash": hostile_cache_before,
            "tmpdir_isolation": "per_cell_private",
            "tmpdir_relative_path": f"{cell}/process-tmp",
        },
    }


def _resolve(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def check_existing_receipt(policy: ReplayPolicy) -> None:
    json_path = _resolve(policy.json_artifact)
    markdown_path = _resolve(policy.markdown_artifact)
    raw_json = json_path.read_bytes()
    payload = json.loads(raw_json)
    validate_policy_receipt(policy, payload)
    canonical_render = json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n"
    if raw_json != canonical_render:
        raise HermeticReplayError("PR-121 JSON receipt is not canonical")
    if markdown_path.read_text(encoding="utf-8") != render_markdown(payload):
        raise HermeticReplayError("PR-121 Markdown receipt is stale")
    projection = declared_index_projection(
        repo_root=REPO_ROOT,
        declared=declared_index_roots(policy, repo_root=REPO_ROOT),
    )
    recorded = _mapping(payload.get("source_snapshot"), field="receipt.source_snapshot")
    if recorded.get("declared_index_hash") != projection["hash"]:
        raise HermeticReplayError("declared Git index inputs changed after hermetic receipt")


def assert_no_forbidden_absolute_paths(payload: object, forbidden: Sequence[Path]) -> None:
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    leaked = [str(path.resolve()) for path in forbidden if str(path.resolve()) in serialized]
    if leaked:
        raise HermeticReplayError(f"receipt leaks host absolute paths: {leaked}")


def receipt_content_hash(payload: Mapping[str, object]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {key: value for key, value in payload.items() if key != "receipt_content_hash"}
        )
    )


def _validate_pr4_scope(value: object) -> Mapping[str, object]:
    scope = _mapping(value, field="pr4_scope_firewall")
    expected_keys = {
        "pr3_e2e_download",
        "pr4_download",
        "pr4_data_work",
        "forbidden_actions",
    }
    if set(scope) != expected_keys:
        raise HermeticReplayError(
            f"PR4 scope firewall key drift: {sorted(scope)} != {sorted(expected_keys)}"
        )
    expected_values = {
        "pr3_e2e_download": "complete_analysis_deferred_to_pr150",
        "pr4_download": "not_started",
        "pr4_data_work": "skip_entirely_by_user_scope",
    }
    for key, expected in expected_values.items():
        if scope.get(key) != expected:
            raise HermeticReplayError(f"PR4 scope firewall {key} must be {expected!r}")
    forbidden = scope.get("forbidden_actions")
    expected_forbidden = [
        "PR4 download",
        "PR4 intake",
        "PR4 reduction",
        "PR4 analysis",
        "PR3_PR4 combined result generation",
    ]
    if forbidden != expected_forbidden:
        raise HermeticReplayError("PR4 forbidden action list drift")
    return scope


def _validate_dependency_verification(
    value: object,
    *,
    field: str,
    expected_phase: str,
    expected_hash: str,
    expected_files: int,
    expected_directories: int,
) -> Mapping[str, object]:
    row = _mapping(value, field=field)
    expected = {
        "phase": expected_phase,
        "status": "pass",
        "content_mode_hash": expected_hash,
        "file_count": expected_files,
        "directory_count": expected_directories,
        "writable_entry_count": 0,
        "mode_policy": _DEPENDENCY_MODE_POLICY,
    }
    for key, expected_value in expected.items():
        if row.get(key) != expected_value:
            raise HermeticReplayError(
                f"{field}.{key} must be {expected_value!r}, got {row.get(key)!r}"
            )
    return row


def validate_policy_receipt(
    policy: ReplayPolicy, payload: Mapping[str, object]
) -> None:
    validate_receipt_metadata(payload)
    if payload.get("config_hash") != sha256_file(policy.path):
        raise HermeticReplayError("PR-121 spec/config hash drift")
    missing_sections = sorted(
        section for section in policy.required_receipt_sections if section not in payload
    )
    if missing_sections:
        raise HermeticReplayError(
            f"receipt lacks policy-required sections: {missing_sections}"
        )
    _validate_pr4_scope(payload.get("pr4_scope_firewall"))
    source_snapshot = _mapping(payload.get("source_snapshot"), field="source_snapshot")
    expected_source_shape = {
        "authority": "git_index",
        "authority_id": f"sha256:{source_snapshot.get('declared_index_hash')}",
        "contains_git_directory": False,
        "untracked_policy": "excluded_by_git_index_archive",
    }
    for key, expected in expected_source_shape.items():
        if source_snapshot.get(key) != expected:
            raise HermeticReplayError(
                f"receipt source_snapshot.{key} must be {expected!r}"
            )
    if payload.get("source_tree_hash") != source_snapshot.get("source_tree_hash"):
        raise HermeticReplayError("receipt source tree hash is internally inconsistent")
    dependency = _mapping(payload.get("dependency_layer"), field="dependency_layer")
    if payload.get("dependency_layer_hash") != dependency.get("content_hash"):
        raise HermeticReplayError("receipt dependency layer hash is internally inconsistent")
    if dependency.get("physical_read_only") is not True:
        raise HermeticReplayError("receipt dependency layer is not physically read-only")
    if dependency.get("mode_policy") != _DEPENDENCY_MODE_POLICY:
        raise HermeticReplayError("receipt dependency layer mode policy drift")
    dependency_hash = _sha256_string(
        dependency.get("content_hash"), field="dependency_layer.content_hash"
    )
    dependency_files = _positive_int(
        dependency.get("file_count"), field="dependency_layer.file_count"
    )
    dependency_directories = _positive_int(
        dependency.get("directory_count"), field="dependency_layer.directory_count"
    )
    _validate_dependency_verification(
        dependency.get("baseline_verification"),
        field="dependency_layer.baseline_verification",
        expected_phase="receipt:baseline",
        expected_hash=dependency_hash,
        expected_files=dependency_files,
        expected_directories=dependency_directories,
    )
    build_guard = _mapping(
        dependency.get("build_guard"), field="dependency_layer.build_guard"
    )
    if build_guard.get("unchanged") is not True:
        raise HermeticReplayError("dependency layer build guard is not unchanged")
    for phase in ("before", "after"):
        _validate_dependency_verification(
            build_guard.get(phase),
            field=f"dependency_layer.build_guard.{phase}",
            expected_phase=f"build:{phase}",
            expected_hash=dependency_hash,
            expected_files=dependency_files,
            expected_directories=dependency_directories,
        )
    install_matrix = payload.get("install_matrix")
    if not isinstance(install_matrix, list) or len(install_matrix) != 6:
        raise HermeticReplayError("receipt install matrix must contain six cells")
    observed_cells: set[str] = set()
    matrix_dependency_guards: dict[str, Mapping[str, object]] = {}
    matrix_structured_hashes: set[str] = set()
    for raw_row in install_matrix:
        row = _mapping(raw_row, field="install_matrix[]")
        cell = _string(row.get("cell"), field="install_matrix[].cell")
        observed_cells.add(cell)
        if row.get("status") != "pass":
            raise HermeticReplayError(f"receipt install cell is not passing: {cell}")
        tests = _mapping(row.get("tests"), field=f"install_matrix.{cell}.tests")
        require_executed_tests(tests.get("executed"), selector=cell)
        dependency_guard = _mapping(
            row.get("dependency_layer_guard"),
            field=f"install_matrix.{cell}.dependency_layer_guard",
        )
        if dependency_guard.get("unchanged") is not True:
            raise HermeticReplayError(
                f"dependency layer cell guard is not unchanged: {cell}"
            )
        matrix_dependency_guards[cell] = dependency_guard
        for phase in ("before", "after"):
            _validate_dependency_verification(
                dependency_guard.get(phase),
                field=f"install_matrix.{cell}.dependency_layer_guard.{phase}",
                expected_phase=f"{cell}:{phase}",
                expected_hash=dependency_hash,
                expected_files=dependency_files,
                expected_directories=dependency_directories,
            )
        generator = _mapping(
            row.get("generator_replay"), field=f"install_matrix.{cell}.generator_replay"
        )
        if generator != _EXPECTED_STATUS_REPLAY_CHECKS:
            raise HermeticReplayError(
                f"installed status CLI/parser evidence missing for cell: {cell}"
            )
        structured_hash = _sha256_string(
            row.get("structured_hash"), field=f"install_matrix.{cell}.structured_hash"
        )
        matrix_structured_hashes.add(structured_hash)
        sentinels = _mapping(
            row.get("hostile_sentinels"), field=f"install_matrix.{cell}.hostile_sentinels"
        )
        if sentinels.get("tmpdir_isolation") != "per_cell_private" or sentinels.get(
            "tmpdir_relative_path"
        ) != f"{cell}/process-tmp":
            raise HermeticReplayError(
                f"install cell lacks private TMPDIR evidence: {cell}"
            )
    if observed_cells != set(policy.install_matrix):
        raise HermeticReplayError("receipt install matrix cell identity drift")
    raw_cell_guards = dependency.get("cell_guards")
    if not isinstance(raw_cell_guards, list) or len(raw_cell_guards) != 6:
        raise HermeticReplayError("dependency layer receipt must contain six cell guards")
    top_guards_by_cell: dict[str, Mapping[str, object]] = {}
    for raw_guard in raw_cell_guards:
        guard = _mapping(raw_guard, field="dependency_layer.cell_guards[]")
        cell = _string(guard.get("cell"), field="dependency_layer.cell_guards[].cell")
        top_guards_by_cell[cell] = {
            key: value for key, value in guard.items() if key != "cell"
        }
    top_guard_cells = set(top_guards_by_cell)
    if top_guard_cells != set(policy.install_matrix):
        raise HermeticReplayError("dependency layer cell guard identity drift")
    if top_guards_by_cell != matrix_dependency_guards:
        raise HermeticReplayError("dependency layer top/cell guard evidence drift")
    replay = _mapping(
        payload.get("detached_generator_replay"), field="detached_generator_replay"
    )
    if replay.get("status") != "pass" or replay.get("cell_count") != 6:
        raise HermeticReplayError("detached generator replay is not passing all six cells")
    if replay.get("execution_path") != (
        "python -I -m common.status_snapshot --write plus installed parser check"
    ):
        raise HermeticReplayError("detached generator replay execution path drift")
    if _mapping(replay.get("checks"), field="detached_generator_replay.checks") != (
        _EXPECTED_STATUS_REPLAY_CHECKS
    ):
        raise HermeticReplayError("detached generator replay check evidence drift")
    replay_structured_hash = _sha256_string(
        replay.get("structured_hash"), field="detached_generator_replay.structured_hash"
    )
    if len(matrix_structured_hashes) != 1 or replay_structured_hash not in matrix_structured_hashes:
        raise HermeticReplayError("detached generator structured hash drift")
    recorded_hash = payload.get("receipt_content_hash")
    if recorded_hash != receipt_content_hash(payload):
        raise HermeticReplayError("PR-121 receipt content hash mismatch")
    assert_no_forbidden_absolute_paths(payload, (REPO_ROOT, Path(sys.prefix)))


def render_markdown(payload: Mapping[str, object]) -> str:
    matrix = payload.get("install_matrix", [])
    dependency = _mapping(payload.get("dependency_layer", {}), field="dependency layer")
    replay = _mapping(
        payload.get("detached_generator_replay", {}), field="detached generator replay"
    )
    replay_checks = _mapping(replay.get("checks", {}), field="generator checks")
    optional = _mapping(payload.get("optional_dependency_matrix", {}), field="optional matrix")
    input_hashes = payload.get("input_hashes", [])
    caveats = payload.get("caveats", [])
    lines = [
        "# PR-121 Hermetic Replay Receipt",
        "",
        "- owner: `COMMON`",
        "- implementation_scope: `common`",
        f"- artifact_mode: `{payload.get('artifact_mode')}`",
        f"- allowed_use: `{payload.get('allowed_use')}`",
        "- claim_tier: `diagnostic_only`",
        "- transfer_source: `none`",
        f"- config_hash: `{payload.get('config_hash')}`",
        f"- sky_support_status: `{payload.get('sky_support_status')}`",
        f"- null_mock_status: `{payload.get('null_mock_status')}`",
        f"- source_authority_id: `{payload.get('source_authority_id')}`",
        f"- worktree_state: `{payload.get('worktree_state')}`",
        f"- generated_on: `{payload.get('generated_on')}`",
        f"- generating_command: `{payload.get('generating_command')}`",
        f"- receipt_content_hash: `{payload.get('receipt_content_hash')}`",
        f"- overall_status: `{payload.get('overall_status')}`",
        f"- source_tree_hash: `{payload.get('source_tree_hash')}`",
        f"- dependency_layer_hash: `{payload.get('dependency_layer_hash')}`",
        "",
        "Clean-install/replay success is implementation mechanics only, not scientific validation.",
        "",
        "## Input hashes",
        "",
        "| path | sha256 | size |",
        "| --- | --- | ---: |",
    ]
    if isinstance(input_hashes, list):
        for raw_row in input_hashes:
            if not isinstance(raw_row, Mapping):
                continue
            path = str(raw_row.get("path", "")).replace("|", "\\|")
            lines.append(
                f"| `{path}` | `{raw_row.get('sha256', '')}` | {raw_row.get('size', '')} |"
            )
    lines.extend(["", "## Caveats", ""])
    if isinstance(caveats, list):
        for caveat in caveats:
            lines.append(f"- {caveat}")
    cell_guards = dependency.get("cell_guards", [])
    guard_count = len(cell_guards) if isinstance(cell_guards, list) else 0
    build_guard = dependency.get("build_guard", {})
    build_unchanged = (
        build_guard.get("unchanged") if isinstance(build_guard, Mapping) else None
    )
    phase_rows: list[tuple[str, Mapping[str, object]]] = []
    baseline = dependency.get("baseline_verification")
    if isinstance(baseline, Mapping):
        phase_rows.append(("receipt", baseline))
    if isinstance(build_guard, Mapping):
        for phase in ("before", "after"):
            row = build_guard.get(phase)
            if isinstance(row, Mapping):
                phase_rows.append(("build", row))
    if isinstance(cell_guards, list):
        for raw_guard in cell_guards:
            if not isinstance(raw_guard, Mapping):
                continue
            cell = str(raw_guard.get("cell", ""))
            for phase in ("before", "after"):
                row = raw_guard.get(phase)
                if isinstance(row, Mapping):
                    phase_rows.append((cell, row))
    lines.extend(
        [
            "",
            "## Dependency layer seal",
            "",
            f"- physical_read_only: `{dependency.get('physical_read_only')}`",
            f"- mode_policy: `{dependency.get('mode_policy')}`",
            f"- file_count: `{dependency.get('file_count')}`",
            f"- directory_count: `{dependency.get('directory_count')}`",
            f"- build_guard_unchanged: `{build_unchanged}`",
            f"- verified_cell_guard_count: `{guard_count}`",
            "",
            "### Phase evidence",
            "",
            "| scope | phase | content/mode hash | files | directories | writable |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for scope, row in phase_rows:
        lines.append(
            f"| `{scope}` | `{row.get('phase')}` | "
            f"`{row.get('content_mode_hash')}` | {row.get('file_count')} | "
            f"{row.get('directory_count')} | {row.get('writable_entry_count')} |"
        )
    lines.extend(
        [
            "",
            "## Installed generator replay",
            "",
            f"- status: `{replay.get('status')}`",
            f"- execution_path: `{replay.get('execution_path')}`",
            f"- cell_count: `{replay.get('cell_count')}`",
            f"- structured_hash: `{replay.get('structured_hash')}`",
            f"- fixed_generated_on: `{replay.get('fixed_generated_on')}`",
            f"- fixed_source_commit: `{replay.get('fixed_source_commit')}`",
        ]
    )
    for key, value in sorted(replay_checks.items()):
        lines.append(f"- check.{key}: `{value}`")
    lines.extend(
        [
        "",
        "## Install matrix",
        "",
        "| cell | status | tests executed | tests skipped | structured hash |",
        "| --- | --- | ---: | ---: | --- |",
        ]
    )
    if isinstance(matrix, list):
        for row in matrix:
            if not isinstance(row, Mapping):
                continue
            tests = row.get("tests", {})
            if not isinstance(tests, Mapping):
                tests = {}
            lines.append(
                f"| `{row.get('cell')}` | `{row.get('status')}` | "
                f"{tests.get('executed', 0)} | {tests.get('skipped', 0)} | "
                f"`{row.get('structured_hash', '')}` |"
            )
    lines.extend(["", "## Optional dependencies", ""])
    for name, row in sorted(optional.items()):
        if isinstance(row, Mapping):
            lines.append(f"- `{name}`: `{row.get('status')}` (excluded from pass count)")
    lines.extend(
        [
            "",
            "## PR4 scope firewall",
            "",
            "PR4 download, intake, reduction, and analysis were skipped by explicit user scope.",
            "",
        ]
    )
    return "\n".join(lines)


def build_receipt(policy: ReplayPolicy) -> dict[str, object]:
    """Execute the tracked-only build/install/replay matrix and return evidence."""

    with tempfile.TemporaryDirectory(prefix="htt-pr121-") as raw_temp:
        temp = Path(raw_temp)
        home = temp / "host-home"
        env = sanitized_environment(home, source_date_epoch=policy.source_date_epoch)
        env["TMPDIR"] = str(temp / "process-tmp")
        Path(env["TMPDIR"]).mkdir()
        detached = temp / "detached"
        source_snapshot = materialize_index_snapshot(
            repo_root=REPO_ROOT,
            destination=detached,
            policy=policy,
            env=env,
        )
        _normalize_tree_mtime(detached, policy.source_date_epoch)
        dependency_layer = build_dependency_layer(
            detached_main=detached / policy.main_project,
            destination=temp / "dependency-layer",
            additional=policy.additional_distributions,
        )
        dependency_baseline = verify_dependency_layer(
            dependency_layer, phase="receipt:baseline"
        )
        dependency_build_before = verify_dependency_layer(
            dependency_layer, phase="build:before"
        )
        artifacts = build_project_artifacts(
            detached=detached,
            work=temp / "build",
            dependency_layer=dependency_layer,
            policy=policy,
            env=env,
        )
        dependency_build_after = verify_dependency_layer(
            dependency_layer, phase="build:after"
        )
        matrix_root = temp / "cells"
        matrix_root.mkdir()
        install_matrix = [
            run_install_cell(
                cell=cell,
                index=index,
                root=matrix_root,
                detached=detached,
                dependency_layer=dependency_layer,
                artifacts=artifacts,
                policy=policy,
                base_env=env,
            )
            for index, cell in enumerate(policy.install_matrix)
        ]
        structured_hashes = {str(row["structured_hash"]) for row in install_matrix}
        if len(structured_hashes) != 1:
            raise HermeticReplayError(
                f"detached generator output differs across install cells: {structured_hashes}"
            )
        generator_checks = [
            _mapping(row.get("generator_replay"), field="generator_replay")
            for row in install_matrix
        ]
        if any(checks != generator_checks[0] for checks in generator_checks[1:]):
            raise HermeticReplayError(
                "installed status CLI/parser checks differ across install cells"
            )
        optional_rows = install_matrix[0]["optional_dependencies"]
        for row in install_matrix[1:]:
            if row["optional_dependencies"] != optional_rows:
                raise HermeticReplayError("optional dependency state differs across cells")

        card_tests = set(
            str(item)
            for item in _mapping(
                install_matrix[0].get("tests"), field="first cell tests"
            ).get("testcases", [])
        )
        mutation_test_evidence = {
            "source_tree_injection": "test_source_byte_and_untracked_injection_change_tree_hash",
            "untracked_file_injection": "test_git_index_archive_excludes_untracked_sentinel",
            "wheel_path_collision": "test_wheel_path_collision_is_rejected",
            "compatibility_wheel_python_payload": "test_compatibility_wheel_python_payload_is_rejected",
            "missing_package_data": "test_declared_package_data_missing_resource_is_rejected",
            "source_snapshot_hash_mismatch": "test_bound_input_drift_fails_check",
            "writable_dependency_layer_entry": (
                "test_dependency_layer_mode_or_content_mutation_fails_closed[mode]"
            ),
            "dependency_layer_content_or_mode_drift": (
                "test_dependency_layer_mode_or_content_mutation_fails_closed[content]"
            ),
        }
        mutation_matrix: list[dict[str, object]] = []
        for mutation in policy.mutations:
            if mutation == "install_order_reversal":
                evidence = "both installation orders passed for direct, sdist, and editable"
            elif mutation in {"cwd_relocation", "pythonpath_injection"}:
                evidence = "all six isolated cells ignored the hostile sentinel"
            elif mutation == "local_cache_injection":
                if any(
                    _mapping(row.get("hostile_sentinels"), field="hostile_sentinels").get(
                        "pip_cache"
                    )
                    != "disabled_and_pre_post_immutable"
                    for row in install_matrix
                ):
                    raise HermeticReplayError(
                        "local cache mutation lacks a pre/post immutable tree hash"
                    )
                evidence = (
                    "all six cells disabled pip cache and preserved the hostile-cache "
                    "tree hash across install/build commands"
                )
            else:
                test_name = mutation_test_evidence.get(mutation)
                if test_name is None or not any(
                    name == test_name or name.startswith(test_name + "[")
                    for name in card_tests
                ):
                    raise HermeticReplayError(
                        f"mutation lacks executed isolated test evidence: {mutation}:{test_name}"
                    )
                evidence = f"isolated pytest:{test_name}"
            mutation_matrix.append(
                {"mutation": mutation, "status": "detected_or_isolated", "evidence": evidence}
            )

        bound_inputs = bind_files(
            detached,
            [
                policy.backlog,
                policy.status,
                policy.gate_outputs,
                policy.path.relative_to(REPO_ROOT).as_posix(),
                "scripts/codex_harness/hermetic_replay.py",
                "tests/pr_cards/test_pr_121_hermetic_install_owner_namespace_detached_replay.py",
                f"{policy.main_project}/pyproject.toml",
                f"{policy.compatibility_project}/pyproject.toml",
            ],
        )
        data_scope = dict(policy.data_scope)
        _validate_pr4_scope(data_scope)
        build_receipt_data = dict(artifacts.receipt)
        wheel_records = _mapping(
            build_receipt_data.get("wheel_records"), field="artifact wheel records"
        )
        clean_matrix = [
            {
                "cell": row["cell"],
                "status": row["status"],
                "resolution_mode": row["resolution_mode"],
                "tests": row["tests"],
            }
            for row in install_matrix
        ]
        payload: dict[str, object] = {
            "schema": "htt.pr121.hermetic_replay_receipt.v1",
            "pr_id": "PR-121",
            "owner": "COMMON",
            "implementation_scope": "common",
            "artifact_mode": "governance_diagnostic",
            "allowed_use": "internal_reproducibility_mechanics_only",
            "claim_tier": "diagnostic_only",
            "transfer_source": "none",
            "config_hash": sha256_file(policy.path),
            "input_hashes": list(bound_inputs),
            "sky_support_status": "not_directional",
            "null_mock_status": "not_statistical",
            "caveats": [
                *policy.caveats,
                "Unhashed generated __pycache__ bytecode rows are excluded from the dependency layer; every copied regular RECORD row is hash/size verified.",
            ],
            "generating_command": "venv/bin/python scripts/codex_harness/hermetic_replay.py --write",
            "generated_on": policy.fixed_generated_on,
            "source_authority_id": source_snapshot["authority_id"],
            "worktree_state": "declared_git_index_bound",
            "source_tree_hash": source_snapshot["source_tree_hash"],
            "dependency_layer_hash": dependency_layer.content_hash,
            "overall_status": "pass",
            "environment_lock": {
                "network": "forbidden_pip_no_index",
                "source_date_epoch": policy.source_date_epoch,
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "isolated_mode": "required_and_observed",
                "user_site": "disabled",
                "pytest_import_mode": "importlib",
                "host_paths_in_receipt": "forbidden",
            },
            "source_snapshot": source_snapshot,
            "dependency_layer": {
                "content_hash": dependency_layer.content_hash,
                "file_count": dependency_layer.file_count,
                "directory_count": dependency_layer.directory_count,
                "distributions": list(dependency_layer.distributions),
                "physical_read_only": True,
                "mode_policy": _DEPENDENCY_MODE_POLICY,
                "baseline_verification": dependency_baseline,
                "build_guard": {
                    "before": dependency_build_before,
                    "after": dependency_build_after,
                    "unchanged": True,
                },
                "cell_guards": [
                    {
                        "cell": row["cell"],
                        **dict(
                            _mapping(
                                row.get("dependency_layer_guard"),
                                field="dependency_layer_guard",
                            )
                        ),
                    }
                    for row in install_matrix
                ],
                "record_policy": "hashed_regular_rows_copied; blank_generated_bytecode_rows_excluded; all_other_blank_rows_rejected",
            },
            "wheel_sdist_hashes": build_receipt_data,
            "wheel_record_hashes": dict(wheel_records),
            "clean_install_matrix": clean_matrix,
            "install_matrix": install_matrix,
            "owner_namespace_matrix": [
                {
                    "cell": row["cell"],
                    "ownership": _mapping(
                        _mapping(row["import_probe"], field="probe").get("ownership"),
                        field="ownership",
                    ),
                }
                for row in install_matrix
            ],
            "temp_cwd_import_matrix": [
                {"cell": row["cell"], **dict(row["hostile_sentinels"])}
                for row in install_matrix
            ],
            "compatibility_alias_matrix": [
                {
                    "cell": row["cell"],
                    "aliases": _mapping(row["import_probe"], field="probe").get("aliases"),
                }
                for row in install_matrix
            ],
            "optional_dependency_matrix": optional_rows,
            "detached_generator_replay": {
                "status": "pass",
                "cell_count": len(install_matrix),
                "structured_hash": next(iter(structured_hashes)),
                "fixed_generated_on": policy.fixed_generated_on,
                "fixed_source_commit": policy.fixed_source_commit,
                "inputs": [policy.backlog, policy.status, policy.gate_outputs],
                "execution_path": "python -I -m common.status_snapshot --write plus installed parser check",
                "checks": dict(generator_checks[0]),
            },
            "mutation_matrix": mutation_matrix,
            "pr4_scope_firewall": data_scope,
        }
        missing_sections = sorted(
            section for section in policy.required_receipt_sections if section not in payload
        )
        if missing_sections:
            raise HermeticReplayError(
                f"receipt lacks policy-required sections: {missing_sections}"
            )
        payload["receipt_content_hash"] = receipt_content_hash(payload)
        assert_no_forbidden_absolute_paths(payload, (REPO_ROOT, Path(sys.prefix), temp))
        validate_policy_receipt(policy, payload)
        return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    spec_path = args.spec if args.spec.is_absolute() else REPO_ROOT / args.spec
    policy = load_policy(spec_path)
    try:
        if args.check:
            check_existing_receipt(policy)
            print(f"PR-121 hermetic replay receipt current: {policy.json_artifact}")
            return 0
        payload = build_receipt(policy)
        validate_policy_receipt(policy, payload)
        json_path = _resolve(policy.json_artifact)
        markdown_path = _resolve(policy.markdown_artifact)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_bytes(json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n")
        markdown_path.write_text(render_markdown(payload), encoding="utf-8")
        print(f"wrote {json_path.relative_to(REPO_ROOT)}")
        print(f"wrote {markdown_path.relative_to(REPO_ROOT)}")
        return 0
    except (HermeticReplayError, PackageTopologyError, OSError, ValueError) as exc:
        print(f"PR-121 hermetic replay failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
