"""Bound WU-006 admission helpers; no map access, scoring, or self-issued review.

The existing RB2 validation functions remain the trusted upstream verifier.
This module binds their accepted output to the downstream candidate and its
external review. It does not replace local validation with a CI badge.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Mapping, Sequence

RB2_HEAD = "0ae0e70791273c13c7b80ac835232c3c63555c5b"
RB2_CODE_HEAD = "32c9b828ef92a569b36067a8daedcef8f11b4c30"
RB2_CODE_TREE = "57cbbe79107404c069389b90363a747ff6bc4bf4"
RB2_MANIFEST_ID = "sha256:02c54e3487d6d9d4a1859114218e33663a5817b86a18e6170c25456d06cba9cc"
REVIEW_FORMAT = "PLANCK_MES_WU006_FRESH_REVIEW_V1"
_OID = re.compile(r"^[0-9a-f]{40}$")
_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class AdmissionError(RuntimeError):
    """The named candidate/artifacts do not have the required admission."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _identity(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise AdmissionError(f"malformed {label}")
    return value


def content_id(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
    return "sha256:" + hashlib.sha256(b"planck_mes_observable_irrep_analysis\0" + encoded).hexdigest()


def rebind_result_record(old: Mapping[str, object], predecessor: Mapping[str, object]) -> dict[str, object]:
    """Change provenance only after verifying the preserved result's identity."""
    record = copy.deepcopy(dict(old))
    recorded_id = record.pop("content_id", None)
    if recorded_id != content_id(record):
        raise AdmissionError("provisional result content identity differs")
    record["predecessor_admission"] = copy.deepcopy(dict(predecessor))
    record["content_id"] = content_id(record)
    return record


def validate_review_binding(
    review: Mapping[str, object], *, candidate_head: str, candidate_tree: str,
    result_content_id: str, predecessor_terminal_sha256: str,
    artifact_sha256: Mapping[str, str], figure_names: Sequence[str],
) -> None:
    """Validate an external receipt without producing or modifying one."""
    if not isinstance(review, Mapping):
        raise AdmissionError("external review must be an object")
    expected = {
        "format": REVIEW_FORMAT, "work_unit": "PMG-WU-006", "state": "PASS",
        "candidate_git_head": _identity(candidate_head, _OID, "candidate head"),
        "candidate_git_tree": _identity(candidate_tree, _OID, "candidate tree"),
        "result_content_id": _identity(result_content_id, _SHA, "result identity"),
        "predecessor_terminal_sha256": _identity(predecessor_terminal_sha256, _SHA, "predecessor identity"),
    }
    if any(review.get(key) != value for key, value in expected.items()):
        raise AdmissionError("external review code/result/predecessor binding differs")
    if (any(type(review.get(key)) is not int or review[key] != 0 for key in ("P0", "P1"))
            or review.get("independent_read_only_first_pass") is not True
            or type(review.get("repair_rounds_used")) is not int
            or review["repair_rounds_used"] not in (0, 1)):
        raise AdmissionError("external review is not a bounded zero-finding verdict")
    findings = review.get("findings")
    if not isinstance(findings, list) or any(
        not isinstance(f, Mapping) or f.get("severity") not in {"P2", "P3"} for f in findings
    ):
        raise AdmissionError("external review contains blocking or malformed findings")
    for name, digest in artifact_sha256.items():
        if not isinstance(name, str) or Path(name).name != name:
            raise AdmissionError("artifact role is not a filename")
        _identity(digest, _SHA, "artifact digest")
    if review.get("objective_output_sha256") != dict(artifact_sha256):
        raise AdmissionError("external review artifact identity set differs")
    visual = {name: {"single_column_3.3in": "PASS", "double_column_6.8in": "PASS"} for name in figure_names}
    if review.get("visual_inspection") != visual:
        raise AdmissionError("external visual inspection is missing, pending, or for different figures")


def validate_predecessor(carrier_dir: Path, repo_root: Path) -> dict[str, object]:
    """Reuse reviewed RB2 validators and pin this transition's admitted input."""
    from scripts.observed_runs.export_planck_paired300_irrep_carrier import validate_portable_completion
    from obsstat.planck_paired300_evidence import verify_portable_artifact_manifest

    carrier_dir, repo_root = Path(carrier_dir), Path(repo_root)
    try:
        terminal = json.loads((carrier_dir / "terminal.json").read_text(encoding="ascii"))
        review = json.loads((carrier_dir / "fresh_review.json").read_text(encoding="ascii"))
    except (OSError, ValueError) as exc:
        raise AdmissionError("reviewed RB2 predecessor evidence is missing") from exc
    if (not isinstance(terminal, dict) or not isinstance(review, dict)
            or terminal.get("format") != "PLANCK_PR3_PAIRED300_REVIEWED_TERMINAL_V1"
            or terminal.get("implementation_git_head") != RB2_CODE_HEAD
            or terminal.get("implementation_git_tree") != RB2_CODE_TREE
            or terminal.get("artifact_manifest_content_id") != RB2_MANIFEST_ID
            or any(type(terminal.get(k)) is not int or terminal[k] != 0 for k in ("P0_remaining", "P1_remaining"))
            or review.get("independent_read_only_first_pass") is not True):
        raise AdmissionError("reviewed RB2 predecessor identity or verdict differs")
    try:
        validated = validate_portable_completion(carrier_dir)
        manifest = verify_portable_artifact_manifest(
            manifest_path=carrier_dir / "artifact_manifest.json", output_root=carrier_dir,
            frozen_scalar_package_path=repo_root / "docs/generated/pr315_planck_smica_feature_replay.npz",
        )
    except (OSError, ValueError, RuntimeError) as exc:
        raise AdmissionError("reviewed RB2 predecessor verification failed") from exc
    if validated != terminal or manifest.get("content_id") != RB2_MANIFEST_ID:
        raise AdmissionError("reviewed RB2 predecessor manifest differs")
    return {
        "work_unit": "PMG-WU-005", "evidence_git_head": RB2_HEAD,
        "reviewed_code_head": RB2_CODE_HEAD, "reviewed_code_tree": RB2_CODE_TREE,
        "terminal_sha256": file_sha256(carrier_dir / "terminal.json"),
        "fresh_review_sha256": file_sha256(carrier_dir / "fresh_review.json"),
        "artifact_manifest_content_id": RB2_MANIFEST_ID,
    }


def _git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(["git", "-C", str(root), *arguments], text=True, capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AdmissionError("candidate Git identity unavailable") from exc
    if result.returncode:
        raise AdmissionError("candidate Git identity or required ancestry unavailable")
    return result.stdout.strip()


def candidate_identity(repo_root: Path, *, output_dir: Path) -> tuple[str, str]:
    """Bind review to a committed code candidate, allowing evidence-only dirt."""
    root = Path(repo_root).resolve()
    head = _identity(_git(root, "rev-parse", "HEAD"), _OID, "current head")
    tree = _identity(_git(root, "rev-parse", "HEAD^{tree}"), _OID, "current tree")
    _git(root, "merge-base", "--is-ancestor", RB2_HEAD, head)
    output = Path(output_dir).resolve()
    allowed = output.relative_to(root).as_posix() + "/" if output.is_relative_to(root) else None
    changed = set(_git(root, "diff", "--name-only", "HEAD").splitlines())
    changed.update(_git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    if any(not allowed or not path.startswith(allowed) for path in changed if path):
        raise AdmissionError("source or unrelated worktree changes exist after candidate commit")
    return head, tree


def artifact_hashes(output: Path, names: Sequence[str]) -> dict[str, str]:
    root = Path(output).resolve()
    hashes: dict[str, str] = {}
    for name in names:
        path = root / name
        if Path(name).name != name or path.is_symlink() or not path.is_file():
            raise AdmissionError("review artifact is missing or unsafe")
        hashes[name] = file_sha256(path)
    return hashes
