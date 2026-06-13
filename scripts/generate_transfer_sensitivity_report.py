#!/usr/bin/env python3
"""Generate the COMMON transfer-sensitivity report for current result surfaces.

This script inventories transfer dependence and downstream result-card status.
It does not evaluate transfer functions, implement a native low-ell solver, or
turn transfer metadata family labels into morphology or classification claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
HTT_ROOT = REPO_ROOT / "htt"
COMMON_ROOT = HTT_ROOT / "src"
for root in (COMMON_ROOT, HTT_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from bass.transfer.registry import (  # noqa: E402
    default_external_transfer_adapter_registry,
)
from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from common.semantic_guards.no_overclaim import scan_text  # noqa: E402
from common.transfer_registry import validate_transfer_dependent_result  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "docs" / "generated" / "transfer_sensitivity_report.md"
SCHEMA_VERSION = "common.transfer_sensitivity_report.v1"
EXTERNAL_TRANSFER_SOURCES = {
    "AniCLASS_external",
    "external_transfer",
    "empirical_proxy",
}
NATIVE_TRANSFER_SOURCES = {
    "BASS_native_provisional",
    "BASS_native_validated",
}
EXPECTED_DOWNSTREAM_TRANSFER_STATUSES = {
    "mio.departure_report.sections": "section_inherits_external_or_proxy_transfer_metadata",
    "mio.budget_spec.external_transfer": "requires_transfer_spec_id_and_validated_transfer_metadata",
    "bass.budget_ceiling_policy_result": "external_or_proxy_candidate_remains_pre_solver_metadata",
    "bass.atlas_entry_lite.current_external_proxy": "metadata_only_not_observed_data",
    "bass.native_schema.future_only": "schema_only_non_consumable_no_values",
}
ALLOWED_DOWNSTREAM_TRANSFER_STATUSES = set(EXPECTED_DOWNSTREAM_TRANSFER_STATUSES.values()) | {
    "transfer_conditional_result_card",
    "native_validated_result_card",
    "no_external_or_proxy_transfer_source_in_payload",
}
REPORT_CAVEATS = (
    "This COMMON report inventories transfer dependence only.",
    "External/proxy transfer paths remain transfer-conditional result surfaces.",
    "Future native low-ell solver adapters are schema-only until solver artifacts and validation gates exist.",
    "Family labels in transfer metadata are provenance labels, not morphology or classification claims.",
    "This report is not HTT evidence, not a MIO certificate, and not a transfer calibration result.",
)
INPUT_PATHS = (
    Path("scripts/generate_transfer_sensitivity_report.py"),
    Path("htt/src/common/transfer_registry.py"),
    Path("htt/bass/transfer/registry.py"),
    Path("htt/bass/transfer/aniclass_adapter.py"),
    Path("htt/bass/atlas/atlas_entry.py"),
    Path("htt/bass/atlas/budget_ceiling_optimizer.py"),
    Path("htt/mio/formalism/budget_spec.py"),
    Path("htt/mio/reports/departure_report.py"),
    Path("docs/PR_DELTAS/pr-080.md"),
    Path("docs/PR_DELTAS/pr-082.md"),
    Path("docs/PR_DELTAS/pr-083.md"),
    Path("docs/PR_DELTAS/pr-056.md"),
)


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes() -> list[str]:
    hashes: list[str] = []
    missing: list[str] = []
    for relative in INPUT_PATHS:
        path = REPO_ROOT / relative
        if not path.exists():
            missing.append(relative.as_posix())
            continue
        hashes.append(f"{relative.as_posix()}:{_file_sha256(path)}")
    if missing:
        raise FileNotFoundError(
            "transfer sensitivity report required inputs are missing: "
            + ", ".join(missing)
        )
    return hashes


def _config_hash(input_hashes: Sequence[str]) -> str:
    encoded = json.dumps(list(input_hashes), sort_keys=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _worktree_state() -> str:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return "dirty" if completed.stdout.strip() else "clean"


def _command_from_args(argv: list[str] | None) -> str:
    command_args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", "scripts/generate_transfer_sensitivity_report.py", *command_args])


def _clean_text(value: object) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|").strip()


def _json_cell(value: object) -> str:
    return _clean_text(json.dumps(value, sort_keys=True, default=str))


def collect_current_transfer_rows() -> list[dict[str, object]]:
    """Return current external/proxy transfer dependencies from PR-080 adapters."""

    registry = default_external_transfer_adapter_registry()
    rows: list[dict[str, object]] = []
    for transfer_id in sorted(registry.transfer_ids()):
        adapter = registry.get(transfer_id)
        metadata = adapter.metadata()
        validate_transfer_dependent_result(metadata)
        transfer_source = str(metadata["transfer_source"])
        if transfer_source not in EXTERNAL_TRANSFER_SOURCES:
            continue
        row = {
            "row_id": f"transfer.{transfer_id}",
            "row_kind": "current_transfer_dependency",
            "owner": "BASS",
            "implementation_scope": str(metadata["implementation_scope"]),
            "claim_tier": str(metadata["claim_tier"]),
            "production_status": str(metadata["production_status"]),
            "transfer_id": transfer_id,
            "transfer_source": transfer_source,
            "transfer_conditional": bool(metadata["transfer_conditional"]),
            "native_solver_result": bool(metadata["native_solver_result"]),
            "family_provenance_label": str(metadata["family"]),
            "family_label_role": "provenance_only_not_classification",
            "observable_kind": str(metadata["observable_kind"]),
            "normalization": str(metadata["normalization"]),
            "calibration_status": str(metadata["calibration_status"]),
            "valid_range": dict(metadata["valid_range"]),  # type: ignore[arg-type]
            "callable_path": str(metadata["callable_path"]),
            "callable_input_domain": dict(metadata["callable_input_domain"]),  # type: ignore[arg-type]
            "valid_range_role": str(metadata["valid_range_role"]),
            "source_ref": str(metadata["source_ref"]),
            "passed_validation_gates": list(metadata["passed_validation_gates"]),  # type: ignore[arg-type]
            "config_hash": _stable_hash(
                {
                    "transfer_id": transfer_id,
                    "transfer_source": transfer_source,
                    "callable_path": metadata["callable_path"],
                    "valid_range": metadata["valid_range"],
                    "callable_input_domain": metadata["callable_input_domain"],
                }
            ),
            "input_hashes": [
                "htt/bass/transfer/registry.py:" + _file_sha256(REPO_ROOT / "htt/bass/transfer/registry.py"),
                "htt/bass/transfer/aniclass_adapter.py:"
                + _file_sha256(REPO_ROOT / "htt/bass/transfer/aniclass_adapter.py"),
            ],
            "sky_support_status": "not_directional",
            "null_mock_status": "not_statistical",
            "caveats": list(metadata["caveats"]),  # type: ignore[arg-type]
        }
        rows.append(row)
    return rows


def collect_downstream_surface_rows() -> list[dict[str, object]]:
    """Return downstream result-card surfaces that expose transfer status."""

    surfaces = [
        {
            "row_id": "mio.departure_report.sections",
            "owner": "MIO",
            "implementation_scope": "mio",
            "claim_tier": "diagnostic_only",
            "result_card": "DepartureReport x_C/Q/Pi/F/G_F sections",
            "transfer_source": "per_section",
            "transfer_conditional_status": "section_inherits_external_or_proxy_transfer_metadata",
            "source_path": "htt/mio/reports/departure_report.py",
            "required_fields": [
                "transfer_source_summary",
                "transfer_provenance_by_section",
                "sky_support_status_by_section",
                "covariance_status_by_section",
                "null_mock_status_by_section",
            ],
            "claim_boundary": "diagnostic_only_no_posterior_no_classification",
            "sky_support_status": "per_section",
            "null_mock_status": "per_section",
        },
        {
            "row_id": "mio.budget_spec.external_transfer",
            "owner": "MIO",
            "implementation_scope": "mio",
            "claim_tier": "diagnostic_only",
            "result_card": "BudgetSpec external_transfer denominator policy",
            "transfer_source": "external_or_proxy_when_policy_external_transfer",
            "transfer_conditional_status": "requires_transfer_spec_id_and_validated_transfer_metadata",
            "source_path": "htt/mio/formalism/budget_spec.py",
            "required_fields": [
                "denominator_policy",
                "transfer_source",
                "transfer_spec_id",
                "transfer_metadata",
                "native_morphology_atlas_status",
            ],
            "claim_boundary": "denominator_sensitivity_not_certified_filling_for_external_transfer",
            "sky_support_status": "explicit_field",
            "null_mock_status": "explicit_field",
        },
        {
            "row_id": "bass.budget_ceiling_policy_result",
            "owner": "BASS",
            "implementation_scope": "bass_py",
            "claim_tier": "diagnostic_only",
            "result_card": "BudgetCeilingPolicyResult and MIO reference payload",
            "transfer_source": "candidate_transfer_source",
            "transfer_conditional_status": "external_or_proxy_candidate_remains_pre_solver_metadata",
            "source_path": "htt/bass/atlas/budget_ceiling_optimizer.py",
            "required_fields": [
                "transfer_source",
                "transfer_spec_id",
                "transfer_metadata",
                "prior",
                "admissible_set",
                "rank_status",
            ],
            "claim_boundary": "ceiling_policy_metadata_not_evidence",
            "sky_support_status": "not_directional_or_depth_metadata",
            "null_mock_status": "not_statistical_or_depth_metadata",
        },
        {
            "row_id": "bass.atlas_entry_lite.current_external_proxy",
            "owner": "BASS",
            "implementation_scope": "bass_py",
            "claim_tier": "diagnostic_only",
            "result_card": "AtlasEntryLite external/proxy transfer metadata",
            "transfer_source": "AniCLASS_external_or_empirical_proxy",
            "transfer_conditional_status": "metadata_only_not_observed_data",
            "source_path": "htt/bass/atlas/atlas_entry.py",
            "required_fields": [
                "transfer_id",
                "transfer_source",
                "transfer_metadata",
                "entry_hash",
                "native_solver_result",
                "consumable_as_result",
            ],
            "claim_boundary": "side_by_side_metadata_not_classification",
            "sky_support_status": "not_directional",
            "null_mock_status": "not_statistical",
        },
        {
            "row_id": "bass.native_schema.future_only",
            "owner": "BASS",
            "implementation_scope": "bass_py",
            "claim_tier": "blocked",
            "result_card": "future native adapter schema",
            "transfer_source": "BASS_native_provisional",
            "transfer_conditional_status": "schema_only_non_consumable_no_values",
            "source_path": "htt/bass/transfer/native_adapter.py",
            "required_fields": [
                "schema_status",
                "returns_values",
                "outputs_available",
                "consumable_as_result",
            ],
            "claim_boundary": "not_current_transfer_result",
            "sky_support_status": "not_directional",
            "null_mock_status": "not_statistical",
        },
    ]
    rows: list[dict[str, object]] = []
    for surface in surfaces:
        path = REPO_ROOT / str(surface["source_path"])
        if not path.exists():
            raise FileNotFoundError(
                "transfer sensitivity report downstream source is missing: "
                f"{surface['source_path']}"
            )
        row = dict(surface)
        row.update(
            {
                "row_kind": "downstream_result_card_surface",
                "production_status": "diagnostic_only",
                "config_hash": _stable_hash(surface),
                "input_hashes": [
                    f"{surface['source_path']}:{_file_sha256(path)}"
                ],
                "generating_command": "source-code surface inventory",
                "git_commit_or_worktree_state": f"{_git_commit()}+{_worktree_state()}",
                "caveats": [
                    "Surface row records required provenance plumbing only.",
                    "It is not a numerical transfer calculation or inference result.",
                ],
            }
        )
        rows.append(row)
    return rows


def summarize_downstream_result_card_payload(
    *,
    row_id: str,
    payload: Mapping[str, object],
    source_path: str,
    generating_command: str,
) -> dict[str, object]:
    """Summarize one existing result-card payload without merging evidence terms."""

    transfer_by_section = payload.get("transfer_provenance_by_section")
    sources: list[str] = []
    transfer_spec_ids: list[str] = []
    transfer_metadata_by_section: list[Mapping[str, object]] = []
    if isinstance(transfer_by_section, Mapping):
        for value in transfer_by_section.values():
            if not isinstance(value, Mapping):
                continue
            source = str(value.get("transfer_source", "none"))
            if source and source != "none":
                sources.append(source)
            spec_id = value.get("transfer_spec_id")
            if spec_id:
                transfer_spec_ids.append(str(spec_id))
            metadata = value.get("transfer_metadata")
            if isinstance(metadata, Mapping):
                transfer_metadata_by_section.append(metadata)
    transfer_source = "none"
    if sources:
        unique_sources = sorted(set(sources))
        transfer_source = unique_sources[0] if len(unique_sources) == 1 else "mixed_by_section"
    native_sources = set(sources) & NATIVE_TRANSFER_SOURCES
    if "BASS_native_provisional" in native_sources:
        raise ValueError(
            "BASS_native_provisional payloads are schema-only and not consumable"
        )
    if "BASS_native_validated" in native_sources:
        if not transfer_metadata_by_section:
            raise ValueError(
                "BASS_native_validated payloads require transfer metadata and validation gates"
            )
        for metadata in transfer_metadata_by_section:
            validate_transfer_dependent_result(metadata)
    is_transfer_conditional = any(source in EXTERNAL_TRANSFER_SOURCES for source in sources)
    has_native_validated = bool(native_sources)
    row = {
        "row_id": row_id,
        "row_kind": "downstream_result_card_payload",
        "owner": str(payload.get("owner", "unknown")),
        "implementation_scope": str(payload.get("implementation_scope", "unknown")),
        "claim_tier": str(payload.get("claim_tier", "unknown")),
        "production_status": str(payload.get("production_status", "unknown")),
        "result_card": str(payload.get("report_role", "result_card_payload")),
        "transfer_source": transfer_source,
        "transfer_spec_ids": sorted(set(transfer_spec_ids)),
        "transfer_conditional": is_transfer_conditional,
        "transfer_conditional_status": (
            "transfer_conditional_result_card"
            if is_transfer_conditional
            else (
                "native_validated_result_card"
                if has_native_validated
                else "no_external_or_proxy_transfer_source_in_payload"
            )
        ),
        "source_path": source_path,
        "config_hash": str(payload.get("config_hash", _stable_hash(payload))),
        "input_hashes": list(payload.get("input_hashes", ()))  # type: ignore[arg-type]
        if isinstance(payload.get("input_hashes", ()), Sequence)
        and not isinstance(payload.get("input_hashes", ()), (str, bytes))
        else [],
        "sky_support_status": "payload_by_section",
        "null_mock_status": "payload_by_section",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": f"{_git_commit()}+{_worktree_state()}",
        "caveats": [
            "Payload summary preserves per-section transfer provenance.",
            "It does not create posterior, evidence, certificate, or classification terms.",
        ],
    }
    return row


def build_transfer_sensitivity_report(
    *,
    command: str,
    artifact_path: Path = DEFAULT_OUTPUT,
    extra_result_card_payloads: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    input_hashes = _input_hashes()
    config_hash = _config_hash(input_hashes)
    git_commit = _git_commit()
    worktree_state = _worktree_state()
    metadata = {
        "artifact_id": "common.transfer_sensitivity_report",
        "artifact_path": _repo_relative(artifact_path),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "scripts.generate_transfer_sensitivity_report",
        "git_commit": git_commit,
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "code_version": f"{git_commit}+{worktree_state}",
        "schema_version": SCHEMA_VERSION,
        "transfer_source": "none",
        "report_subject_transfer_sources": sorted(EXTERNAL_TRANSFER_SOURCES),
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "caveats": list(REPORT_CAVEATS),
        "generating_command": command,
        "git_commit_or_worktree_state": f"{git_commit}+{worktree_state}",
        "required_gates": [
            "current_external_transfer_rows_present",
            "downstream_result_cards_mark_transfer_conditional",
            "no_external_transfer_as_native",
            "no_classification_claims",
        ],
        "passed_gates": [
            "current_external_transfer_rows_present",
            "downstream_result_cards_mark_transfer_conditional",
            "no_external_transfer_as_native",
            "no_classification_claims",
        ],
        "failed_gates": [],
        "statistics_definitions": {
            "current_transfer_rows": "PR-080 external/proxy transfer metadata inventory",
            "downstream_result_card_rows": "result-card surfaces requiring transfer status",
        },
    }
    downstream_rows = collect_downstream_surface_rows()
    for index, payload in enumerate(extra_result_card_payloads, 1):
        downstream_rows.append(
            summarize_downstream_result_card_payload(
                row_id=f"payload.extra.{index}",
                payload=payload,
                source_path="extra_result_card_payload",
                generating_command=command,
            )
        )
    report = {
        "metadata": metadata,
        "current_transfer_rows": collect_current_transfer_rows(),
        "downstream_result_card_rows": downstream_rows,
    }
    validate_transfer_sensitivity_report(report, expected_artifact_path=artifact_path)
    return report


def validate_transfer_sensitivity_report(
    report: Mapping[str, object],
    *,
    expected_artifact_path: Path = DEFAULT_OUTPUT,
) -> None:
    metadata = report.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("transfer sensitivity report requires metadata")
    validate_manifest_payload(
        metadata,
        manifest_path=expected_artifact_path,
        expected_artifact_path=_repo_relative(expected_artifact_path),
    )

    current_rows = report.get("current_transfer_rows")
    if not isinstance(current_rows, Sequence) or isinstance(current_rows, (str, bytes)):
        raise ValueError("current_transfer_rows must be a sequence")
    if not current_rows:
        raise ValueError("external-transfer sensitivity is absent from report")
    for row in current_rows:
        if not isinstance(row, Mapping):
            raise ValueError("current transfer row must be a mapping")
        source = str(row.get("transfer_source", ""))
        if source not in EXTERNAL_TRANSFER_SOURCES:
            raise ValueError(f"unexpected current transfer_source {source!r}")
        if row.get("transfer_conditional") is not True:
            raise ValueError("current transfer row must be transfer_conditional")
        if row.get("native_solver_result") is not False:
            raise ValueError("external/proxy transfer row cannot be native output")
        if row.get("claim_tier") != "conditional":
            raise ValueError("current transfer row claim_tier must be conditional")
        validate_transfer_dependent_result(row_as_transfer_metadata(row))

    downstream_rows = report.get("downstream_result_card_rows")
    if not isinstance(downstream_rows, Sequence) or isinstance(
        downstream_rows,
        (str, bytes),
    ):
        raise ValueError("downstream_result_card_rows must be a sequence")
    downstream_by_id: dict[str, Mapping[str, object]] = {}
    for row in downstream_rows:
        if not isinstance(row, Mapping):
            raise ValueError("downstream result-card row must be a mapping")
        row_id = str(row.get("row_id", ""))
        if row_id:
            downstream_by_id[row_id] = row
        _validate_downstream_row_transfer_status(row)
        _validate_downstream_row_input_hashes(row)
    missing_downstream = sorted(
        set(EXPECTED_DOWNSTREAM_TRANSFER_STATUSES) - set(downstream_by_id)
    )
    if missing_downstream:
        raise ValueError(
            "downstream result-card rows are missing: "
            + ", ".join(missing_downstream)
        )
    for row_id, expected_status in EXPECTED_DOWNSTREAM_TRANSFER_STATUSES.items():
        actual_status = str(
            downstream_by_id[row_id].get("transfer_conditional_status", "")
        )
        if actual_status != expected_status:
            raise ValueError(
                f"downstream result-card row {row_id} has transfer status "
                f"{actual_status!r}, expected {expected_status!r}"
            )

    rendered = render_transfer_sensitivity_markdown(report)
    issues = scan_text(rendered, path=DEFAULT_OUTPUT)
    if issues:
        first = issues[0]
        raise ValueError(
            f"forbidden claim language in transfer report: "
            f"{first.rule_id} line {first.line}"
        )


def _validate_downstream_row_input_hashes(row: Mapping[str, object]) -> None:
    row_hashes = row.get("input_hashes", ())
    if isinstance(row_hashes, (str, bytes)) or not isinstance(row_hashes, Sequence):
        raise ValueError("downstream result-card row input_hashes must be a sequence")
    if any(str(item).endswith(":missing") for item in row_hashes):
        raise ValueError("downstream result-card row has missing source hash")


def _validate_downstream_row_transfer_status(row: Mapping[str, object]) -> None:
    status = str(row.get("transfer_conditional_status", ""))
    if status not in ALLOWED_DOWNSTREAM_TRANSFER_STATUSES:
        raise ValueError(f"unknown downstream transfer status {status!r}")
    source = str(row.get("transfer_source", ""))
    if source == "BASS_native_provisional" and status != "schema_only_non_consumable_no_values":
        raise ValueError("BASS_native_provisional rows must be schema-only")
    if source == "BASS_native_validated" and status != "native_validated_result_card":
        raise ValueError("BASS_native_validated rows require explicit native status")


def row_as_transfer_metadata(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "transfer_id": row["transfer_id"],
        "transfer_source": row["transfer_source"],
        "family": row["family_provenance_label"],
        "valid_range": row["valid_range"],
        "observable_kind": row["observable_kind"],
        "normalization": row["normalization"],
        "calibration_status": row["calibration_status"],
        "caveats": row["caveats"],
        "source_ref": row["source_ref"],
        "passed_validation_gates": row["passed_validation_gates"],
    }


def render_transfer_sensitivity_markdown(report: Mapping[str, object]) -> str:
    metadata = report["metadata"]
    assert isinstance(metadata, Mapping)
    current_rows = report["current_transfer_rows"]
    downstream_rows = report["downstream_result_card_rows"]
    assert isinstance(current_rows, Sequence)
    assert isinstance(downstream_rows, Sequence)
    lines = [
        "# Transfer Sensitivity Report",
        "",
        "This COMMON diagnostic report inventories current transfer-conditional result surfaces and records which downstream report-card fields inherit external/proxy transfer provenance.",
        "",
        "## Artifact Metadata",
        "",
        f"artifact_id: {metadata['artifact_id']}",
        f"artifact_path: {metadata['artifact_path']}",
        f"owner: {metadata['owner']}",
        f"implementation_scope: {metadata['implementation_scope']}",
        f"claim_tier: {metadata['claim_tier']}",
        f"production_status: {metadata['production_status']}",
        f"transfer_source: {metadata['transfer_source']}",
        f"report_subject_transfer_sources: {', '.join(metadata['report_subject_transfer_sources'])}",  # type: ignore[arg-type]
        f"sky_support_status: {metadata['sky_support_status']}",
        f"null_mock_status: {metadata['null_mock_status']}",
        f"config_hash: `{metadata['config_hash']}`",
        "input_hashes:",
    ]
    for input_hash in metadata["input_hashes"]:  # type: ignore[index]
        lines.append(f"- `{input_hash}`")
    lines.extend(
        [
            "caveats:",
            *[f"- {caveat}" for caveat in metadata["caveats"]],  # type: ignore[index]
            f"generating_command: {metadata['generating_command']}",
            f"git_commit_or_worktree_state: {metadata['git_commit_or_worktree_state']}",
            "",
            "## Current Transfer Dependencies",
            "",
            "| transfer_id | source | claim_tier | conditional | non_native | observable | calibration | callable | input_domain | caveat_count |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in current_rows:
        assert isinstance(row, Mapping)
        lines.append(
            "| "
            f"{_clean_text(row['transfer_id'])} | "
            f"{_clean_text(row['transfer_source'])} | "
            f"{_clean_text(row['claim_tier'])} | "
            f"{_clean_text(row['transfer_conditional'])} | "
            f"{_clean_text(not bool(row['native_solver_result']))} | "
            f"{_clean_text(row['observable_kind'])} | "
            f"{_clean_text(row['calibration_status'])} | "
            f"{_clean_text(row['callable_path'])} | "
            f"{_json_cell(row['callable_input_domain'])} | "
            f"{len(row['caveats'])} |"  # type: ignore[arg-type]
        )
    lines.extend(
        [
            "",
            "Family labels above are provenance labels only; they are not classification claims.",
            "Current external/proxy paths have no passed native validation gates in this report.",
            "",
            "## Downstream Result-Card Status",
            "",
            "| row_id | owner | scope | claim_tier | result_card | transfer_source | transfer_status | sky_support | null_mock | boundary |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in downstream_rows:
        assert isinstance(row, Mapping)
        lines.append(
            "| "
            f"{_clean_text(row['row_id'])} | "
            f"{_clean_text(row['owner'])} | "
            f"{_clean_text(row['implementation_scope'])} | "
            f"{_clean_text(row['claim_tier'])} | "
            f"{_clean_text(row['result_card'])} | "
            f"{_clean_text(row['transfer_source'])} | "
            f"{_clean_text(row['transfer_conditional_status'])} | "
            f"{_clean_text(row['sky_support_status'])} | "
            f"{_clean_text(row['null_mock_status'])} | "
            f"{_clean_text(row['claim_boundary']) if 'claim_boundary' in row else 'diagnostic_only'} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- This report may support the claim that current listed outputs are transfer-conditional under explicit external/proxy provenance.",
            "- This report does not validate transfer calibration, does not produce HTT evidence, and does not create a MIO certificate.",
            "- Future native adapter rows remain schema-only and non-consumable until external solver artifacts and validation gates exist.",
            "- Scalar diagnostics, report-card rows, and transfer metadata do not classify a Bianchi family.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the COMMON transfer sensitivity report."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown report path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the target path and report without writing it.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = _command_from_args(argv)
    target = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    report = build_transfer_sensitivity_report(
        command=command,
        artifact_path=target,
    )
    rendered = render_transfer_sensitivity_markdown(report)
    if args.dry_run:
        print(f"COMMON transfer sensitivity report -> {_repo_relative(target)}")
        print(rendered)
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    print(f"wrote {_repo_relative(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
