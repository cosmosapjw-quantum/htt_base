"""Exact post-closeout compatibility bridge from PR-168 to PR-248.

PR-168's failed-contract receipt is a historical statement that its inventoried
production bytes were unchanged *at that closeout*.  It is not a permanent ban
on later reviewed changes.  This module accepts only the exact transitions in a
hash-rooted PR-248 receipt and never rewrites the PR-168 artifacts.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

import yaml


RECEIPT_PATH = (
    "docs/research_program/stat_foundations/"
    "pr248_pr168_integrity_supersession.yaml"
)
RECEIPT_SHA256 = (
    "a3b76513a4f3868f723f7d591f4a56a399e47665e04c9a8e95ba17aa132a12c2"
)
_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class Pr168SupersessionError(ValueError):
    """Raised when the PR-248 bridge cannot be authenticated."""


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise Pr168SupersessionError(f"{field} must be a non-empty canonical path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise Pr168SupersessionError(f"{field} must be repository-relative")
    if path.as_posix() != value:
        raise Pr168SupersessionError(f"{field} must use canonical POSIX form")
    return value


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise Pr168SupersessionError(f"{field} must be a lowercase SHA-256")
    return value


def _load(repo_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    root = Path(repo_root).resolve()
    receipt_path = root / RECEIPT_PATH
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise Pr168SupersessionError("PR-248 supersession receipt is missing")
    if _digest(receipt_path) != RECEIPT_SHA256:
        raise Pr168SupersessionError("PR-248 supersession receipt hash mismatch")
    payload = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise Pr168SupersessionError("PR-248 supersession receipt must be a mapping")
    if payload.get("schema") != "htt.pr168.integrity_supersession.v1":
        raise Pr168SupersessionError("unsupported PR-168 supersession schema")
    if payload.get("authority") != "PR-248":
        raise Pr168SupersessionError("PR-168 supersession authority must be PR-248")

    historical: dict[str, dict] = {}
    for key in ("historical_receipt", "historical_manifest"):
        binding = payload.get(key)
        if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256"}:
            raise Pr168SupersessionError(f"{key} must be an exact hash binding")
        rel = _safe_path(binding["path"], f"{key}.path")
        expected = _sha(binding["sha256"], f"{key}.sha256")
        path = root / rel
        if path.is_symlink() or not path.is_file() or _digest(path) != expected:
            raise Pr168SupersessionError(f"{key} bytes do not match the receipt")
        historical[key] = json.loads(path.read_text(encoding="utf-8"))

    rows = payload.get("bindings")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise Pr168SupersessionError("bindings must be a non-empty list")
    transitions: dict[str, str] = {}
    priors: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "path",
            "prior_sha256",
            "sha256",
            "reason",
        }:
            raise Pr168SupersessionError("each binding must have the exact schema")
        rel = _safe_path(row["path"], "bindings.path")
        if rel in transitions:
            raise Pr168SupersessionError("duplicate supersession path")
        prior = _sha(row["prior_sha256"], "bindings.prior_sha256")
        current = _sha(row["sha256"], "bindings.sha256")
        if prior == current:
            raise Pr168SupersessionError("supersession must change the bytes")
        if not isinstance(row["reason"], str) or not row["reason"].strip():
            raise Pr168SupersessionError("supersession reason must be non-empty")
        path = root / rel
        if path.is_symlink() or not path.is_file() or _digest(path) != current:
            raise Pr168SupersessionError(
                f"current bytes do not match supersession binding: {rel}"
            )
        priors[rel] = prior
        transitions[rel] = current

    receipt_rows = historical["historical_receipt"].get("production_rows", ())
    receipt_priors = {
        row.get("path"): row.get("actual_sha256")
        for row in receipt_rows
        if isinstance(row, Mapping)
    }
    manifest_priors = historical["historical_manifest"].get("input_hashes", {})
    for rel, prior in priors.items():
        if receipt_priors.get(rel) == prior:
            continue
        if isinstance(manifest_priors, Mapping) and manifest_priors.get(rel) == prior:
            continue
        raise Pr168SupersessionError(
            f"prior digest is not rooted in a PR-168 artifact: {rel}"
        )
    return priors, transitions


def authorized_pr168_transition(
    repo_root: Path,
    *,
    relative_path: str,
    prior_sha256: str,
    current_sha256: str,
) -> bool:
    """Return true only for one exact, receipt-rooted PR-168 -> PR-248 edge."""
    rel = _safe_path(relative_path, "relative_path")
    prior = _sha(prior_sha256, "prior_sha256")
    current = _sha(current_sha256, "current_sha256")
    priors, transitions = _load(Path(repo_root))
    return priors.get(rel) == prior and transitions.get(rel) == current


__all__ = [
    "Pr168SupersessionError",
    "RECEIPT_PATH",
    "RECEIPT_SHA256",
    "authorized_pr168_transition",
]
