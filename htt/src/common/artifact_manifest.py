"""Artifact manifest validation and quarantine helpers.

The canonical manifest dataclass remains ``common.contracts.ArtifactManifest``.
This module adds PR-011 checker utilities for generated artifacts and legacy
figures that need explicit quarantine until provenance metadata exists.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping

from common.contracts import ArtifactManifest
from common.sky_support import validate_sky_facing_artifact_metadata


REQUIRED_ARTIFACT_FIELDS = (
    "owner",
    "implementation_scope",
    "claim_tier",
    "config_hash",
    "input_hashes",
    "caveats",
)

REQUIRED_PROVENANCE_FIELDS = (
    "transfer_source",
    "sky_support_status",
    "null_mock_status",
    "generating_command",
    "git_commit_or_worktree_state",
)

FIGURE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".svg", ".pdf"})
DEFAULT_SCAN_ROOTS = ("figures", "docs")
NATIVE_TRANSFER_SOURCES = frozenset(
    {"native_solver", "BASS_native_provisional", "BASS_native_validated"}
)
NATIVE_TRANSFER_GATES = frozenset(
    {"native_transfer_validated", "native_solver_validation"}
)


@dataclass(frozen=True)
class ManifestIssue:
    path: str
    code: str
    detail: str


@dataclass(frozen=True)
class FigureManifestRecord:
    path: str
    status: str
    reason: str
    manifest_path: str | None = None


@dataclass(frozen=True)
class QuarantineReport:
    scan_roots: tuple[str, ...]
    manifested_figures: tuple[FigureManifestRecord, ...]
    quarantined_figures: tuple[FigureManifestRecord, ...]
    manifest_issues: tuple[ManifestIssue, ...]


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _require_repo_contained(path: Path, repo_root: Path, *, label: str) -> None:
    try:
        path.resolve().relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"{label} must remain within the repository root") from exc


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _as_manifest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    manifest = payload.get("manifest")
    if isinstance(manifest, Mapping):
        combined = dict(manifest)
        for key in REQUIRED_PROVENANCE_FIELDS:
            if key not in combined and key in payload:
                combined[key] = payload[key]
        if "sky_support" not in combined and "sky_support" in payload:
            combined["sky_support"] = payload["sky_support"]
        return combined
    return dict(payload)


def _is_sky_facing_status(status: object) -> bool:
    value = str(status or "").strip()
    if not value:
        return False
    return value not in {
        "not_directional",
        "not_applicable",
        "not_applicable_to_repo_inventory",
        "not_applicable_to_command_matrix",
        "pending_or_unknown_for_existing_directional_artifacts",
    }


def validate_manifest_payload(
    payload: Mapping[str, Any],
    *,
    manifest_path: Path | str,
    expected_artifact_path: str | None = None,
) -> tuple[ManifestIssue, ...]:
    """Return validation issues for one manifest payload.

    The common dataclass validates owner/scope/claim-tier vocabulary. PR-011
    adds non-empty artifact/provenance metadata checks around that dataclass.
    """

    path_text = str(manifest_path)
    manifest_payload = _as_manifest_payload(payload)
    issues: list[ManifestIssue] = []
    for field in (*REQUIRED_ARTIFACT_FIELDS, *REQUIRED_PROVENANCE_FIELDS):
        if field not in manifest_payload:
            issues.append(
                ManifestIssue(
                    path=path_text,
                    code="missing_required_field",
                    detail=f"{field} is required",
                )
            )
        elif _is_empty(manifest_payload[field]):
            issues.append(
                ManifestIssue(
                    path=path_text,
                    code="empty_required_field",
                    detail=f"{field} must be non-empty",
                )
            )

    manifest_field_names = {field.name for field in fields(ArtifactManifest)}
    dataclass_payload = {
        key: value
        for key, value in manifest_payload.items()
        if key in manifest_field_names
    }
    try:
        ArtifactManifest(**dataclass_payload)
    except (TypeError, ValueError) as exc:
        issues.append(
            ManifestIssue(
                path=path_text,
                code="invalid_artifact_manifest",
                detail=str(exc),
            )
        )

    if (
        expected_artifact_path is not None
        and str(manifest_payload.get("artifact_path", "")) != expected_artifact_path
    ):
        issues.append(
            ManifestIssue(
                path=path_text,
                code="artifact_path_mismatch",
                detail=(
                    "artifact_path must match scanned artifact "
                    f"{expected_artifact_path!r}"
                ),
            )
        )

    transfer_source = str(manifest_payload.get("transfer_source", ""))
    passed_gates = {
        str(gate) for gate in manifest_payload.get("passed_gates", ()) or ()
    }
    if (
        transfer_source in NATIVE_TRANSFER_SOURCES
        and passed_gates.isdisjoint(NATIVE_TRANSFER_GATES)
    ):
        issues.append(
            ManifestIssue(
                path=path_text,
                code="native_transfer_without_gate",
                detail=(
                    "native transfer sources require an explicit native "
                    "validation gate"
                ),
            )
        )

    if _is_sky_facing_status(manifest_payload.get("sky_support_status")):
        try:
            validate_sky_facing_artifact_metadata(manifest_payload)
        except ValueError as exc:
            issues.append(
                ManifestIssue(
                    path=path_text,
                    code="invalid_sky_support_metadata",
                    detail=str(exc),
                )
            )

    return tuple(issues)


def sidecar_manifest_candidates(figure_path: Path) -> tuple[Path, Path]:
    base = figure_path.with_suffix("")
    return (
        base.with_name(base.name + ".manifest.json"),
        figure_path.with_name(figure_path.name + ".manifest.json"),
    )


def _existing_sidecar(figure_path: Path, repo_root: Path) -> Path | None:
    for candidate in sidecar_manifest_candidates(figure_path):
        _require_repo_contained(
            candidate,
            repo_root,
            label="manifest sidecar",
        )
        if candidate.exists():
            return candidate
    return None


def _figure_paths(repo_root: Path, scan_roots: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for root_text in scan_roots:
        root = repo_root / root_text
        _require_repo_contained(root, repo_root, label="scan root")
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in candidates:
            if path.suffix.lower() not in FIGURE_SUFFIXES:
                continue
            _require_repo_contained(path, repo_root, label="scanned artifact")
            if path.is_file():
                paths.append(path)
    return sorted(set(paths), key=lambda path: _repo_relative(path, repo_root))


def _load_json(path: Path) -> Mapping[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, Mapping) else None


def build_quarantine_report(
    repo_root: Path | str,
    *,
    scan_roots: Iterable[str] = DEFAULT_SCAN_ROOTS,
) -> QuarantineReport:
    root = Path(repo_root).resolve()
    scan_root_tuple = tuple(scan_roots)
    manifested: list[FigureManifestRecord] = []
    quarantined: list[FigureManifestRecord] = []
    issues: list[ManifestIssue] = []

    for figure_path in _figure_paths(root, scan_root_tuple):
        relative_figure = _repo_relative(figure_path, root)
        sidecar = _existing_sidecar(figure_path, root)
        if sidecar is None:
            quarantined.append(
                FigureManifestRecord(
                    path=relative_figure,
                    status="quarantined",
                    reason="missing_manifest",
                )
            )
            continue

        relative_sidecar = _repo_relative(sidecar, root)
        payload = _load_json(sidecar)
        if payload is None:
            issue = ManifestIssue(
                path=relative_sidecar,
                code="invalid_json",
                detail="manifest sidecar must contain a JSON object",
            )
            issues.append(issue)
            quarantined.append(
                FigureManifestRecord(
                    path=relative_figure,
                    status="quarantined",
                    reason=issue.code,
                    manifest_path=relative_sidecar,
                )
            )
            continue

        manifest_issues = validate_manifest_payload(
            payload,
            manifest_path=Path(relative_sidecar),
            expected_artifact_path=relative_figure,
        )
        issues.extend(manifest_issues)
        if manifest_issues:
            quarantined.append(
                FigureManifestRecord(
                    path=relative_figure,
                    status="quarantined",
                    reason="invalid_manifest",
                    manifest_path=relative_sidecar,
                )
            )
        else:
            manifested.append(
                FigureManifestRecord(
                    path=relative_figure,
                    status="manifested",
                    reason="valid_manifest",
                    manifest_path=relative_sidecar,
                )
            )

    return QuarantineReport(
        scan_roots=scan_root_tuple,
        manifested_figures=tuple(manifested),
        quarantined_figures=tuple(quarantined),
        manifest_issues=tuple(issues),
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _report_config_hash(report: QuarantineReport) -> str:
    payload = {
        "scan_roots": report.scan_roots,
        "manifested": [record.path for record in report.manifested_figures],
        "quarantined": [record.path for record in report.quarantined_figures],
        "issues": [
            {"path": issue.path, "code": issue.code}
            for issue in report.manifest_issues
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _input_hash_rows(report: QuarantineReport, repo_root: Path) -> list[str]:
    rows: list[str] = []
    seen: set[str] = set()
    for record in (*report.manifested_figures, *report.quarantined_figures):
        for relative in (record.path, record.manifest_path):
            if relative is None or relative in seen:
                continue
            path = repo_root / relative
            if path.exists() and path.is_file():
                rows.append(f"- {relative}: `{_file_sha256(path)}`")
                seen.add(relative)
    if rows:
        return rows
    return ["- none: `no_scanned_inputs`"]


def _git_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _worktree_state(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return "dirty" if completed.stdout.strip() else "clean"


def _issue_rows(issues: tuple[ManifestIssue, ...]) -> list[str]:
    if not issues:
        return ["| none | none | none |"]
    return [
        f"| `{issue.path}` | `{issue.code}` | {issue.detail} |"
        for issue in issues
    ]


def _figure_rows(records: tuple[FigureManifestRecord, ...]) -> list[str]:
    if not records:
        return ["| none | none | none |"]
    return [
        "| "
        f"`{record.path}` | "
        f"`{record.reason}` | "
        f"`{record.manifest_path or 'none'}` |"
        for record in records
    ]


def render_quarantine_markdown(
    report: QuarantineReport,
    *,
    repo_root: Path | str,
    output_path: Path | str,
    generating_command: str,
) -> str:
    root = Path(repo_root).resolve()
    output = Path(output_path)
    output_text = (
        _repo_relative(output.resolve(), root)
        if output.is_absolute()
        else output.as_posix()
    )
    lines = [
        "# Quarantined Figure Inventory",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        f"config_hash: `{_report_config_hash(report)}`",
        "input_hashes:",
        *_input_hash_rows(report, root),
        "caveats:",
        "- Quarantine inventory only; listed artifacts are not promoted by this report.",
        "- Missing or invalid manifests block claim-bearing use until provenance is added.",
        "- The checker does not regenerate figures, inspect pixels, or infer scientific meaning.",
        f"generating_command: {generating_command}",
        f"git_commit: {_git_commit(root)}",
        f"worktree_state: {_worktree_state(root)}",
        f"output_path: {output_text}",
        "",
        "## Summary",
        "",
        f"- Scan roots: {', '.join(report.scan_roots) or 'none'}",
        f"- Manifested figures: {len(report.manifested_figures)}",
        f"- Quarantined figures: {len(report.quarantined_figures)}",
        f"- Manifest issues: {len(report.manifest_issues)}",
        "",
        "## Quarantined Figures",
        "",
        "| Path | Reason | Manifest |",
        "| --- | --- | --- |",
        *_figure_rows(report.quarantined_figures),
        "",
        "## Manifested Figures",
        "",
        "| Path | Reason | Manifest |",
        "| --- | --- | --- |",
        *_figure_rows(report.manifested_figures),
        "",
        "## Manifest Issues",
        "",
        "| Manifest | Issue | Detail |",
        "| --- | --- | --- |",
        *_issue_rows(report.manifest_issues),
        "",
    ]
    return "\n".join(lines)
