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
    "acde06633e651e7015bf5976e33e59a44332c2634aed259d60b71df5707451d3"
)
PR252_AUTHORIZING_RECEIPT_PATH = (
    "docs/research_program/stat_foundations/"
    "pr252_mes_consumer_migration.yaml"
)
PR252_AUTHORIZING_RECEIPT_SHA256 = (
    "5a65eeed591f0312e8a984d6cabe5aab636adda92dae1cc39e69f9fbe0c0b0b8"
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
    path = root / relative
    if path.is_symlink() or not path.is_file() or _digest(path) != digest:
        raise Pr168SupersessionError(f"{field} bytes do not match the binding")


def _compose_pr252_extension(
    root: Path,
    priors: Mapping[str, str],
    transitions: Mapping[str, str],
    historical_priors: Mapping[str, object],
) -> tuple[dict[str, str], dict[str, str]]:
    path = root / EXTENSION_RECEIPT_PATH
    if path.is_symlink() or not path.is_file():
        raise Pr168SupersessionError("PR-252 supersession extension is missing")
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
        path = root / relative
        if (
            path.is_symlink()
            or not path.is_file()
            or _digest(path) != terminal_sha256
        ):
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
