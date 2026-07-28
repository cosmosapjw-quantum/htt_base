"""Exact post-closeout compatibility bridge from PR-168 through PR-252.

PR-168's failed-contract receipt is a historical statement that its inventoried
production bytes were unchanged *at that closeout*.  It is not a permanent ban
on later reviewed changes.  This module accepts only a contiguous chain rooted
in the frozen PR-248 receipt and never rewrites the PR-168/PR-248 artifacts.
"""
from __future__ import annotations

import hashlib
import json
import re
import stat
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
EXTENSION_RECEIPT_PATH = (
    "docs/research_program/stat_foundations/"
    "pr252_pr248_integrity_supersession.yaml"
)
EXTENSION_RECEIPT_SHA256 = (
    "4f66b0924db5ced757125aa6455232200502656e80ca913ef3fad5377acdf83a"
)
PR252_AUTHORIZING_RECEIPT_PATH = (
    "docs/research_program/stat_foundations/"
    "pr252_mes_consumer_migration.yaml"
)
PR252_AUTHORIZING_RECEIPT_SHA256 = (
    "a90134895e34aff79e2c22538c012a08b692efe6486a29ce2dfef8db378a5efb"
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


def _regular_repo_file(root: Path, relative: str, *, field: str) -> Path:
    """Return a regular file only when every in-repository component is real."""

    normalized = _safe_path(relative, field)
    current = root
    parts = PurePosixPath(normalized).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except (FileNotFoundError, OSError) as exc:
            raise Pr168SupersessionError(
                f"{field} is missing: {normalized}"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise Pr168SupersessionError(
                f"{field} traverses a symlink: {normalized}"
            )
        if index < len(parts) - 1:
            if not stat.S_ISDIR(info.st_mode):
                raise Pr168SupersessionError(
                    f"{field} parent is not a directory: {normalized}"
                )
        elif not stat.S_ISREG(info.st_mode):
            raise Pr168SupersessionError(
                f"{field} must be a regular file: {normalized}"
            )
    try:
        current.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise Pr168SupersessionError(
            f"{field} escapes the repository: {normalized}"
        ) from exc
    return current


def _exact_bound_file(
    root: Path,
    binding: object,
    *,
    field: str,
    expected_path: str,
    expected_sha256: str,
) -> None:
    if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256"}:
        raise Pr168SupersessionError(
            f"{field} must be an exact path/SHA-256 binding"
        )
    relative = _safe_path(binding["path"], f"{field}.path")
    digest = _sha(binding["sha256"], f"{field}.sha256")
    if relative != expected_path or digest != expected_sha256:
        raise Pr168SupersessionError(f"{field} identity drifted")
    path = _regular_repo_file(root, relative, field=field)
    if _digest(path) != digest:
        raise Pr168SupersessionError(f"{field} bytes do not match the binding")


def _compose_pr252_extension(
    root: Path,
    priors: Mapping[str, str],
    transitions: Mapping[str, str],
    historical_priors: Mapping[str, object],
) -> tuple[dict[str, str], dict[str, str]]:
    path = _regular_repo_file(
        root,
        EXTENSION_RECEIPT_PATH,
        field="PR-252 supersession extension",
    )
    if _digest(path) != EXTENSION_RECEIPT_SHA256:
        raise Pr168SupersessionError(
            "PR-252 supersession extension hash mismatch"
        )
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise Pr168SupersessionError(
            f"invalid PR-252 supersession extension: {exc}"
        ) from exc
    required_top_level = {
        "schema",
        "authority",
        "predecessor",
        "authorizing_receipt",
        "allowed_use",
        "bindings",
    }
    if not isinstance(payload, Mapping) or set(payload) != required_top_level:
        raise Pr168SupersessionError(
            "PR-252 supersession extension has an invalid top-level schema"
        )
    if payload.get("schema") != "htt.pr168.integrity_supersession_extension.v1":
        raise Pr168SupersessionError(
            "unsupported PR-252 supersession extension schema"
        )
    if payload.get("authority") != "PR-252":
        raise Pr168SupersessionError(
            "PR-252 supersession extension authority must be PR-252"
        )
    allowed_use = payload.get("allowed_use")
    if (
        not isinstance(allowed_use, str)
        or not allowed_use.strip()
        or allowed_use != allowed_use.strip()
    ):
        raise Pr168SupersessionError(
            "PR-252 supersession extension allowed_use must be trimmed text"
        )
    _exact_bound_file(
        root,
        payload.get("predecessor"),
        field="predecessor",
        expected_path=RECEIPT_PATH,
        expected_sha256=RECEIPT_SHA256,
    )
    _exact_bound_file(
        root,
        payload.get("authorizing_receipt"),
        field="authorizing_receipt",
        expected_path=PR252_AUTHORIZING_RECEIPT_PATH,
        expected_sha256=PR252_AUTHORIZING_RECEIPT_SHA256,
    )

    rows = payload.get("bindings")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise Pr168SupersessionError(
            "PR-252 supersession extension bindings must be a non-empty list"
        )
    origin = dict(priors)
    terminal = dict(transitions)
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "path",
            "prior_sha256",
            "sha256",
            "reason",
        }:
            raise Pr168SupersessionError(
                "each PR-252 extension binding must have the exact schema"
            )
        relative = _safe_path(row["path"], "extension bindings.path")
        if relative in seen:
            raise Pr168SupersessionError(
                "duplicate PR-252 extension binding path"
            )
        seen.add(relative)
        prior = _sha(
            row["prior_sha256"], "extension bindings.prior_sha256"
        )
        current = _sha(row["sha256"], "extension bindings.sha256")
        reason = row.get("reason")
        if (
            not isinstance(reason, str)
            or not reason.strip()
            or reason != reason.strip()
        ):
            raise Pr168SupersessionError(
                "extension bindings.reason must be trimmed text"
            )
        if relative in terminal:
            expected_prior = terminal[relative]
        else:
            historical_prior = historical_priors.get(relative)
            if historical_prior is None:
                raise Pr168SupersessionError(
                    "PR-252 extension names an unknown predecessor path: "
                    f"{relative}"
                )
            expected_prior = _sha(
                historical_prior,
                f"historical prior for {relative}",
            )
            origin[relative] = expected_prior
            terminal[relative] = expected_prior
        if expected_prior != prior:
            raise Pr168SupersessionError(
                f"PR-252 extension prior digest drifted: {relative}"
            )
        if current == prior:
            raise Pr168SupersessionError(
                f"PR-252 extension binding must change the bytes: {relative}"
            )
        terminal[relative] = current
    return origin, terminal


def _load(repo_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    root = Path(repo_root).resolve()
    receipt_path = _regular_repo_file(
        root,
        RECEIPT_PATH,
        field="PR-248 supersession receipt",
    )
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
        path = _regular_repo_file(root, rel, field=key)
        if _digest(path) != expected:
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
        priors[rel] = prior
        transitions[rel] = current

    receipt_rows = historical["historical_receipt"].get("production_rows", ())
    receipt_priors = {
        row.get("path"): row.get("actual_sha256")
        for row in receipt_rows
        if isinstance(row, Mapping)
    }
    manifest_priors = historical["historical_manifest"].get("input_hashes", {})
    historical_priors = dict(receipt_priors)
    if isinstance(manifest_priors, Mapping):
        for relative, digest in manifest_priors.items():
            existing = historical_priors.get(relative)
            if existing is not None and existing != digest:
                raise Pr168SupersessionError(
                    f"PR-168 historical roots disagree: {relative}"
                )
            historical_priors[relative] = digest
    for rel, prior in priors.items():
        if receipt_priors.get(rel) == prior:
            continue
        if isinstance(manifest_priors, Mapping) and manifest_priors.get(rel) == prior:
            continue
        raise Pr168SupersessionError(
            f"prior digest is not rooted in a PR-168 artifact: {rel}"
        )
    priors, terminal_transitions = _compose_pr252_extension(
        root,
        priors,
        transitions,
        historical_priors,
    )
    for relative, terminal_sha256 in terminal_transitions.items():
        path = _regular_repo_file(
            root,
            relative,
            field="terminal supersession binding",
        )
        if _digest(path) != terminal_sha256:
            raise Pr168SupersessionError(
                f"current bytes do not match terminal supersession binding: "
                f"{relative}"
            )
    return priors, terminal_transitions


def authorized_pr168_transition(
    repo_root: Path,
    *,
    relative_path: str,
    prior_sha256: str,
    current_sha256: str,
) -> bool:
    """Authorize one exact root-to-terminal edge in the registered chain."""
    rel = _safe_path(relative_path, "relative_path")
    prior = _sha(prior_sha256, "prior_sha256")
    current = _sha(current_sha256, "current_sha256")
    priors, transitions = _load(Path(repo_root))
    return priors.get(rel) == prior and transitions.get(rel) == current


__all__ = [
    "EXTENSION_RECEIPT_PATH",
    "EXTENSION_RECEIPT_SHA256",
    "Pr168SupersessionError",
    "PR252_AUTHORIZING_RECEIPT_PATH",
    "PR252_AUTHORIZING_RECEIPT_SHA256",
    "RECEIPT_PATH",
    "RECEIPT_SHA256",
    "authorized_pr168_transition",
]
