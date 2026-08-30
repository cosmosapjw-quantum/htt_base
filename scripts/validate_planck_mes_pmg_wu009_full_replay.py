#!/usr/bin/env python3
"""Validate the PMG-WU-009 local replay package without touching raw data."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_ROOT = REPO_ROOT / "docs/codex_handoff/planck_mes_pmg_wu009_full_replay_local_execution"
PACKAGE_ID = "PLANCK_MES_PMG_WU009_FULL_REPLAY_LOCAL_EXECUTION_20260830"
CONFIG_SCHEMA = "htt.planck_mes_pmg_wu009.instantiated_execution.v1"
EXPECTED_AUTHORITY = {
    "accepted_design_commit": "bda8e489bff7c26fb5fb03fba59360028d01a2fe",
    "accepted_design_tree": "aa734e7933efc6f763d49aaf9f0d9c1bdad6b3b1",
    "scientific_base_commit": "5e81ed1635b8fe6fc944829a9fab7ab8d5b8c654",
}
REPOSITORY_AUTHORITY_HASHES = {
    "docs/superpowers/specs/2026-08-30-planck-mes-wu009-full-replay-theorem-reconciliation-design.md":
        "0fd0fd545279337903fa941e2add03c7dd99eef109f286e1e8eed3d3800372a2",
    "docs/superpowers/plans/2026-08-30-planck-mes-wu009-full-replay-theorem-reconciliation.md":
        "0a9e1c74dfe843ef4fac3c944ad8a8d05a6fb3daa61a5a8fcfc40bf0d5f90523",
    "docs/codex_handoff/planck_mes_pmg_wu009_full_replay_local_execution/AUTHORITY_BINDING.yaml":
        "0779cbe9d593131f645962afcb3ba5882c75275e13c8ef669e18d4a9f8bb048a",
    "docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json":
        "aeabb89ca8fae2f343d72e2933ada8f106a6f35864abc59ac6d7973e5f70ce62",
    "docs/generated/planck_pr3_paired300_irrep_carrier/terminal.json":
        "bf82c1e2be03c9fe1c3ca8a4ef148a84be4d7b999cb31af5c617882fe1e0decb",
    "docs/generated/planck_mes_smica_cmbonly_999_irrep/terminal.json":
        "a0adb549fd43be4f79386605d1cb40c9cda62627e260efcffa50540a536279fe",
    "docs/generated/planck_mes_irrep_injection_power/terminal.json":
        "0126d55c050d01bd7a371ab9a8093fdb378e4c92f4f74c0656b90c1879a2b3d6",
}
EVIDENCE_RECEIPT_SCHEMA = "htt.planck_mes_pmg_wu009.evidence_receipt.v1"
EVIDENCE_ARTIFACT_SCHEMA = "htt.planck_mes_pmg_wu009.evidence_artifact.v1"
RECEIPT_ARTIFACT_ROLES = {
    "EB_OPERATOR_IDENTITY": {"operator_manifest"},
    "EB_RESPONSE": {"response_matrix", "rank_diagnostic", "condition_diagnostic"},
    "EB_LEAKAGE": {"pure_e_injection", "pure_b_injection", "out_of_band_alias"},
    "EB_TRANSFER": {"coefficient_transfer"},
    "NULL_IDENTITY": {"null_bundle_manifest"},
    "NULL_COVARIANCE": {
        "te_covariance",
        "polarization_noise",
        "mapmaking_systematics",
        "b_mode_hypothesis",
    },
    "NULL_PIPELINE": {"rowwise_pipeline", "adaptive_replay"},
}
EXPECTED_XACT_VERSION = "xAct 1.3.0"
EXPECTED_XACT_ARCHIVE_SHA256 = "7a6c5f600868a3922668b020a15c0692f76574ff2a559808c62d460cef1b07be"
CONFIG_FIELDS = {
    "schema",
    "package_id",
    "execution_phase",
    "authority",
    "runtime",
    "toolchains",
    "inspection",
    "outputs",
    "temperature_inverse",
    "polarization",
    "claims",
    "product_admissions",
    "terminals",
}
PACKAGE_FILES = {
    "PACKAGE_INDEX.yaml",
    "AUTHORITY_BINDING.yaml",
    "DATA_AVAILABILITY_BINDING.yaml",
    "WU009_EXECUTION_CONTRACT.yaml",
    "D9_RECIPE_TEMPLATE.yaml",
    "D9_LANE_TERMINALS.yaml",
    "CODEX_HANDOFF.md",
    "CODEX_HANDOFF_PROMPT.md",
}
LANES = {"D.9.0", "D.9.A", "D.9.B", "D.9.C", "D.9.D", "D.9.E", "D.9.F", "D.9.G", "D.9.H", "D.9.Z"}
LANE_PREREQUISITES = {
    "D.9.0": [],
    "D.9.A": ["D.9.0"],
    "D.9.B": ["D.9.0"],
    "D.9.C": ["D.9.B"],
    "D.9.D": ["D.9.0"],
    "D.9.E": ["D.9.0"],
    "D.9.F": ["D.9.A", "D.9.B", "D.9.C", "D.9.D", "D.9.E"],
    "D.9.G": ["D.9.F"],
    "D.9.H": ["D.9.G"],
    "D.9.Z": ["D.9.0", "D.9.A", "D.9.B", "D.9.C", "D.9.D", "D.9.E", "D.9.F", "D.9.G", "D.9.H"],
}
CLAIM_FIELDS = {
    "same_sky_role",
    "independent_replication",
    "product_substitution",
    "claim_promotion",
    "physical_cause_identified",
    "bianchi_family_identified",
    "foreground_exclusion",
    "cross_field_role",
    "joint_rv_role",
    "amplitude_conditional_role",
    "shared_data_evalue_multiplication",
    "new_observed_rank",
}
APPROVED_TERMINALS = {
    "PRODUCT_NOT_PRESENT",
    "EXTERNAL_SOURCE_BLOCKED",
    "CONVENTION_UNRESOLVED",
    "TRANSFER_FUNCTION_UNRESOLVED",
    "TRANSFER_UNSUPPORTED_L2_L3",
    "SPIN2_TRANSFORM_INVALID",
    "POLARIZATION_BASIS_COVARIANCE_FAILURE",
    "PARITY_CONVENTION_FAILURE",
    "CUT_SKY_LOWELL_NOT_IDENTIFIED",
    "EB_LEAKAGE_UNCONTROLLED",
    "BLOCKED_BY_T_CONDITIONED_POLARIZATION",
    "HARMONIC_STF_ROUNDTRIP_FAILURE",
    "STF_INTERTWINER_FAILURE",
    "MODE_UNUSABLE_PRODUCT_LIMITATION",
    "NULL_CALIBRATION_UNAVAILABLE",
    "MORPHOLOGY_COMPUTED_NULL_CALIBRATION_UNAVAILABLE",
    "NULL_BUNDLE_DEPENDENCE_UNRESOLVED",
    "NULL_NOT_JOINTLY_MATCHED",
    "ROW_EXCHANGEABILITY_UNPROVEN",
    "CONDITIONAL_CALIBRATION_APPROXIMATE",
    "MORPHOLOGY_COMPUTED_UNCERTAINTY_DOMINATED",
    "SYSTEMATICS_LIMITED",
    "SAME_SKY_ROBUSTNESS_ONLY",
    "EXPLORATORY_ONLY",
    "BLOCKED_BY_MOVED_AUTHORITY",
    "BLOCKED_BY_MISSING_THEOREM_DOSSIER",
    "BLOCKED_BY_DOSSIER_IDENTITY_MISMATCH",
    "NOT_IDENTIFIED_FROM_COMMITTED_CARRIER",
    "NOT_ADMISSIBLE_MISSING_ABSOLUTE_T_MONOPOLE_DIPOLE",
    "BLOCKED_BY_NON_EQUIVARIANT_ADAPTATION",
    "BLOCKED_BY_DEGENERATE_STRATUM",
    "BLOCKED_BY_NULL_EXCHANGEABILITY_FAILURE",
    "BLOCKED_BY_REPLAY_MISMATCH",
    "BLOCKED_BY_REVIEW_FINDING",
    "NO_ADMISSIBLE_NEW_RESULT",
    "SUCCEEDED_NO_CLAIM_PROMOTION",
    "SUCCEEDED_WITH_TYPED_LIMITATIONS_NO_CLAIM_PROMOTION",
}
OUTPUT_BEARING_TERMINALS = {
    "MORPHOLOGY_COMPUTED_NULL_CALIBRATION_UNAVAILABLE",
    "CONDITIONAL_CALIBRATION_APPROXIMATE",
    "MORPHOLOGY_COMPUTED_UNCERTAINTY_DOMINATED",
    "SYSTEMATICS_LIMITED",
    "SAME_SKY_ROBUSTNESS_ONLY",
    "EXPLORATORY_ONLY",
    "SUCCEEDED_NO_CLAIM_PROMOTION",
    "SUCCEEDED_WITH_TYPED_LIMITATIONS_NO_CLAIM_PROMOTION",
}
FORBIDDEN_SCAN_PATTERNS = (
    re.compile(r"(^|\s)find\s"),
    re.compile(r"(^|\s)du\s"),
    re.compile(r"rglob\s*\("),
    re.compile(r"glob\s*\(\s*['\"]\*\*"),
    re.compile(r"os\.walk\s*\("),
    re.compile(r"Path\.walk\s*\("),
    re.compile(r"\*\*/\*"),
)
FORBIDDEN_CLAIM_PATTERNS = (
    re.compile(r"bianchi.{0,40}(identif|detect|attribut)", re.IGNORECASE),
    re.compile(r"foreground.{0,40}(ruled\s*out|exclud|identified)", re.IGNORECASE),
    re.compile(r"independent\s+(cosmic\s+)?replication", re.IGNORECASE),
    re.compile(r"unconditional.{0,40}wasserstein", re.IGNORECASE),
)


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.startswith("<")


def _concrete_identity(value: Any) -> bool:
    return _nonempty(value) and value.strip().upper() not in {
        "USER_SUPPLIED",
        "UNKNOWN",
        "UNRESOLVED",
        "REPLACE_ME",
        "TBD",
    }


def _is_git_worktree(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if completed.returncode != 0:
        return False
    try:
        top_level = Path(completed.stdout.strip()).resolve(strict=True)
        requested = path.resolve(strict=True)
    except OSError:
        return False
    return top_level == requested


def _derive_executable_version(executable: Path, argument: str) -> str | None:
    try:
        completed = subprocess.run(
            [str(executable), argument],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or completed.stderr.strip() or None


def _validate_repository_authority(path: Path, errors: list[str]) -> None:
    """Bind declared commits to tracked, content-addressed local authority files."""
    for relative, expected in REPOSITORY_AUTHORITY_HASHES.items():
        candidate = path / relative
        if not candidate.is_file():
            errors.append(f"REPOSITORY_AUTHORITY_FILE_MISSING:{relative}")
            continue
        if _sha256(candidate) != expected:
            errors.append(f"REPOSITORY_AUTHORITY_WORKTREE_HASH_MISMATCH:{relative}")
        try:
            tracked = subprocess.run(
                ["git", "-C", str(path), "ls-files", "--error-unmatch", "--", relative],
                check=False,
                capture_output=True,
                timeout=5,
            )
            committed = subprocess.run(
                ["git", "-C", str(path), "show", f"HEAD:{relative}"],
                check=False,
                capture_output=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            errors.append(f"REPOSITORY_AUTHORITY_GIT_READ_FAILED:{relative}")
            continue
        if tracked.returncode != 0:
            errors.append(f"REPOSITORY_AUTHORITY_FILE_UNTRACKED:{relative}")
        if committed.returncode != 0:
            errors.append(f"REPOSITORY_AUTHORITY_HEAD_OBJECT_MISSING:{relative}")
        elif hashlib.sha256(committed.stdout).hexdigest() != expected:
            errors.append(f"REPOSITORY_AUTHORITY_HEAD_HASH_MISMATCH:{relative}")


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _valid_receipt_metrics(label: str, metrics: Any) -> bool:
    if not isinstance(metrics, Mapping):
        return False
    if label == "EB_OPERATOR_IDENTITY":
        return (
            set(metrics) == {"coefficient_level", "operator_id", "target_mode_count"}
            and metrics.get("coefficient_level") is True
            and _concrete_identity(metrics.get("operator_id"))
            and type(metrics.get("target_mode_count")) is int
            and metrics.get("target_mode_count") == 24
        )
    if label == "EB_RESPONSE":
        condition = metrics.get("condition_number")
        ceiling = metrics.get("condition_ceiling")
        return (
            set(metrics) == {"condition_ceiling", "condition_number", "rank"}
            and type(metrics.get("rank")) is int
            and metrics.get("rank") == 24
            and _finite_number(condition)
            and _finite_number(ceiling)
            and 0.0 < float(condition) <= float(ceiling)
        )
    if label == "EB_LEAKAGE":
        required = {"out_of_band_alias_test", "pure_b_injection", "pure_e_injection"}
        return set(metrics) == required and all(metrics.get(name) is True for name in required)
    if label == "EB_TRANSFER":
        return (
            set(metrics) == {"target_mode_count", "transfer_bound"}
            and type(metrics.get("target_mode_count")) is int
            and metrics.get("target_mode_count") == 24
            and metrics.get("transfer_bound") is True
        )
    if label == "NULL_IDENTITY":
        return (
            set(metrics) == {"bundle_id", "row_count"}
            and _concrete_identity(metrics.get("bundle_id"))
            and type(metrics.get("row_count")) is int
            and metrics.get("row_count") >= 2
        )
    if label == "NULL_COVARIANCE":
        required = {
            "b_mode_hypothesis_declared",
            "mapmaking_systematics_included",
            "polarization_noise_included",
            "te_covariance_preserved",
        }
        return set(metrics) == required and all(metrics.get(name) is True for name in required)
    if label == "NULL_PIPELINE":
        required = {"adaptive_selection_rerun", "complete_rowwise_replay", "row_equivariant"}
        return set(metrics) == required and all(metrics.get(name) is True for name in required)
    if label.startswith("LANE_MANIFEST:"):
        return set(metrics) == {"lane"} and metrics.get("lane") == label.split(":", 1)[1]
    return False


def _validate_bound_receipt(
    value: Any,
    label: str,
    errors: list[str],
    seen_receipt_paths: set[Path] | None = None,
    seen_artifact_paths: set[Path] | None = None,
    seen_source_paths: set[Path] | None = None,
) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"MISSING_BOUND_RECEIPT:{label}")
        return
    if set(value) != {"path", "sha256"}:
        errors.append(f"BOUND_RECEIPT_SCHEMA_MISMATCH:{label}")
        return
    raw_path = value.get("path")
    expected = value.get("sha256")
    if not _nonempty(raw_path) or not Path(raw_path).is_absolute():
        errors.append(f"BOUND_RECEIPT_PATH_INVALID:{label}")
        return
    path = Path(raw_path)
    resolved_path = path.resolve(strict=False)
    if seen_receipt_paths is not None:
        if resolved_path in seen_receipt_paths:
            errors.append(f"BOUND_RECEIPT_ROLE_SUBSTITUTION:{label}")
        seen_receipt_paths.add(resolved_path)
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        errors.append(f"BOUND_RECEIPT_IDENTITY_INVALID:{label}")
        return
    if not path.is_file():
        errors.append(f"BOUND_RECEIPT_UNRESOLVED:{label}")
        return
    if _sha256(path) != expected:
        errors.append(f"BOUND_RECEIPT_HASH_MISMATCH:{label}")
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(f"BOUND_RECEIPT_CONTENT_INVALID:{label}")
        return
    expected_state = "SEALED" if label.startswith("LANE_MANIFEST:") else "PASS"
    if (
        not isinstance(payload, Mapping)
        or set(payload) != {"schema", "package_id", "evidence_kind", "state", "metrics", "artifacts"}
        or payload.get("schema") != EVIDENCE_RECEIPT_SCHEMA
        or payload.get("package_id") != PACKAGE_ID
        or payload.get("evidence_kind") != label
        or payload.get("state") != expected_state
        or not _valid_receipt_metrics(label, payload.get("metrics"))
    ):
        errors.append(f"BOUND_RECEIPT_CONTENT_INVALID:{label}")
        return
    expected_roles = (
        {"lane_manifest"}
        if label.startswith("LANE_MANIFEST:")
        else RECEIPT_ARTIFACT_ROLES.get(label, set())
    )
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(expected_roles):
        errors.append(f"BOUND_RECEIPT_ARTIFACT_SET_INVALID:{label}")
        return
    actual_roles: set[str] = set()
    metrics_digest = hashlib.sha256(
        json.dumps(payload["metrics"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    for artifact in artifacts:
        if not isinstance(artifact, Mapping) or set(artifact) != {"role", "path", "sha256"}:
            errors.append(f"BOUND_RECEIPT_ARTIFACT_SCHEMA_INVALID:{label}")
            continue
        role = artifact.get("role")
        artifact_path_raw = artifact.get("path")
        artifact_sha = artifact.get("sha256")
        if not isinstance(role, str):
            errors.append(f"BOUND_RECEIPT_ARTIFACT_ROLE_INVALID:{label}")
            continue
        actual_roles.add(role)
        if not _nonempty(artifact_path_raw) or not Path(artifact_path_raw).is_absolute():
            errors.append(f"BOUND_RECEIPT_ARTIFACT_PATH_INVALID:{label}:{role}")
            continue
        artifact_path = Path(artifact_path_raw)
        resolved_artifact = artifact_path.resolve(strict=False)
        if resolved_artifact == resolved_path:
            errors.append(f"BOUND_RECEIPT_ARTIFACT_ROLE_SUBSTITUTION:{label}:{role}")
        if seen_artifact_paths is not None:
            if resolved_artifact in seen_artifact_paths:
                errors.append(f"BOUND_RECEIPT_ARTIFACT_ROLE_SUBSTITUTION:{label}:{role}")
            seen_artifact_paths.add(resolved_artifact)
        if (
            not isinstance(artifact_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", artifact_sha) is None
            or not artifact_path.is_file()
            or _sha256(artifact_path) != artifact_sha
        ):
            errors.append(f"BOUND_RECEIPT_ARTIFACT_IDENTITY_INVALID:{label}:{role}")
            continue
        try:
            artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append(f"BOUND_RECEIPT_ARTIFACT_CONTENT_INVALID:{label}:{role}")
            continue
        if (
            not isinstance(artifact_payload, Mapping)
            or set(artifact_payload)
            != {
                "schema",
                "package_id",
                "evidence_kind",
                "role",
                "receipt_metrics_sha256",
                "source",
            }
            or artifact_payload.get("schema") != EVIDENCE_ARTIFACT_SCHEMA
            or artifact_payload.get("package_id") != PACKAGE_ID
            or artifact_payload.get("evidence_kind") != label
            or artifact_payload.get("role") != role
            or artifact_payload.get("receipt_metrics_sha256") != metrics_digest
        ):
            errors.append(f"BOUND_RECEIPT_ARTIFACT_CONTENT_INVALID:{label}:{role}")
            continue
        source = artifact_payload.get("source")
        if not isinstance(source, Mapping) or set(source) != {"path", "sha256"}:
            errors.append(f"BOUND_RECEIPT_SOURCE_SCHEMA_INVALID:{label}:{role}")
            continue
        source_path_raw = source.get("path")
        source_sha = source.get("sha256")
        if not _nonempty(source_path_raw) or not Path(source_path_raw).is_absolute():
            errors.append(f"BOUND_RECEIPT_SOURCE_PATH_INVALID:{label}:{role}")
            continue
        source_path = Path(source_path_raw)
        resolved_source = source_path.resolve(strict=False)
        if resolved_source in {resolved_path, resolved_artifact}:
            errors.append(f"BOUND_RECEIPT_SOURCE_ROLE_SUBSTITUTION:{label}:{role}")
        if seen_source_paths is not None:
            if resolved_source in seen_source_paths:
                errors.append(f"BOUND_RECEIPT_SOURCE_ROLE_SUBSTITUTION:{label}:{role}")
            seen_source_paths.add(resolved_source)
        if (
            not isinstance(source_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", source_sha) is None
            or not source_path.is_file()
            or _sha256(source_path) != source_sha
        ):
            errors.append(f"BOUND_RECEIPT_SOURCE_IDENTITY_INVALID:{label}:{role}")
            continue
        try:
            source_text = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            source_text = ""
        if any(pattern.search(source_text) for pattern in FORBIDDEN_CLAIM_PATTERNS):
            errors.append(f"FORBIDDEN_CLAIM_TEXT_IN_SOURCE:{label}:{role}")
        for text in _claim_strings(artifact_payload):
            if any(pattern.search(text) for pattern in FORBIDDEN_CLAIM_PATTERNS):
                errors.append(f"FORBIDDEN_CLAIM_TEXT_IN_ARTIFACT:{label}:{role}:{text}")
    if actual_roles != expected_roles:
        errors.append(f"BOUND_RECEIPT_ARTIFACT_SET_INVALID:{label}")
    for text in _claim_strings(payload):
        if any(pattern.search(text) for pattern in FORBIDDEN_CLAIM_PATTERNS):
            errors.append(f"FORBIDDEN_CLAIM_TEXT_IN_RECEIPT:{label}:{text}")


def _claim_strings(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        strings: list[str] = []
        for item in value.values():
            strings.extend(_claim_strings(item))
        return strings
    if isinstance(value, list):
        return [text for item in value for text in _claim_strings(item)]
    return [value] if isinstance(value, str) else []


def validate_package(package_root: Path | str = DEFAULT_PACKAGE_ROOT) -> list[str]:
    root = Path(package_root)
    errors: list[str] = []
    if not root.is_dir():
        return [f"PACKAGE_MISSING:{root}"]
    actual = {path.name for path in root.iterdir()}
    if actual != PACKAGE_FILES:
        errors.append(f"PACKAGE_FILE_SET_MISMATCH:expected={sorted(PACKAGE_FILES)} actual={sorted(actual)}")
        return errors
    try:
        index = _load_yaml(root / "PACKAGE_INDEX.yaml")
        authority = _load_yaml(root / "AUTHORITY_BINDING.yaml")
        availability = _load_yaml(root / "DATA_AVAILABILITY_BINDING.yaml")
        contract = _load_yaml(root / "WU009_EXECUTION_CONTRACT.yaml")
        recipe = _load_yaml(root / "D9_RECIPE_TEMPLATE.yaml")
        terminals = _load_yaml(root / "D9_LANE_TERMINALS.yaml")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"PACKAGE_PARSE_ERROR:{exc}"]

    if index.get("package_id") != PACKAGE_ID:
        errors.append("PACKAGE_ID_MISMATCH")
    declared = index.get("files")
    if not isinstance(declared, dict) or set(declared) != PACKAGE_FILES:
        errors.append("PACKAGE_INDEX_FILE_SET_MISMATCH")
    else:
        for name, entry in declared.items():
            if name == "PACKAGE_INDEX.yaml":
                if not isinstance(entry, Mapping) or entry.get("sha256") != "SELF_EXCLUDED":
                    errors.append("PACKAGE_INDEX_SELF_POLICY_INVALID")
                continue
            expected = entry.get("sha256") if isinstance(entry, Mapping) else None
            if expected != _sha256(root / name):
                errors.append(f"PACKAGE_HASH_MISMATCH:{name}")

    if authority.get("package_id") != PACKAGE_ID or authority.get("formal_dossier", {}).get("status") != "REQUIRED_NOT_MATERIALIZED_HERE":
        errors.append("AUTHORITY_BINDING_INVALID")
    if (
        authority.get("accepted_design", {}).get("commit") != EXPECTED_AUTHORITY["accepted_design_commit"]
        or authority.get("accepted_design", {}).get("tree") != EXPECTED_AUTHORITY["accepted_design_tree"]
        or authority.get("scientific_base", {}).get("commit") != EXPECTED_AUTHORITY["scientific_base_commit"]
    ):
        errors.append("AUTHORITY_BINDING_MISMATCH")
    if availability.get("raw_access", {}).get("inventory_mode") != "USER_SUPPLIED_EXPLICIT_MANIFEST_ONLY":
        errors.append("EXPLICIT_MANIFEST_POLICY_REQUIRED")
    runtime_fields = set(contract.get("runtime_required", []))
    required_runtime = {"REPO_ROOT", "OUTPUT_ROOT", "PLANCK_RAW_ROOT", "THEOREM_DOSSIER", "THEOREM_DOSSIER_SHA256", "XACT_PARENT"}
    if not required_runtime.issubset(runtime_fields):
        errors.append("RUNTIME_BINDINGS_INCOMPLETE")
    if contract.get("github_actions_allowed") is not False or contract.get("raw_recursive_scans_allowed") is not False:
        errors.append("EXECUTION_PROHIBITIONS_INCOMPLETE")
    if contract.get("authority_required") != EXPECTED_AUTHORITY:
        errors.append("EXECUTION_AUTHORITY_CONTRACT_INVALID")
    if contract.get("toolchain_identities_required") != {
        "python": "ABSOLUTE_EXECUTABLE_MATCHING_SHA256_AND_DERIVED_DOUBLE_DASH_VERSION",
        "wolfram": "ABSOLUTE_EXECUTABLE_MATCHING_SHA256_AND_DERIVED_DASH_VERSION",
        "xact": {
            "parent": "ABSOLUTE_EXISTING_PARENT_MATCHING_XACT_PARENT",
            "version": EXPECTED_XACT_VERSION,
            "source_archive_sha256": EXPECTED_XACT_ARCHIVE_SHA256,
        },
    }:
        errors.append("TOOLCHAIN_IDENTITY_CONTRACT_INVALID")
    input_contract = contract.get("input_contract", {})
    if (
        input_contract.get("validated_inspection_commands") != "MUST_BE_EMPTY"
        or input_contract.get("explicit_manifest_sha256") != "REQUIRED_AND_CONTENT_VERIFIED"
        or input_contract.get("repository_root") != "EXISTING_GIT_WORKTREE"
        or input_contract.get("repository_authority", {}).get("mode")
        != "CONTENT_BOUND_TRACKED_AUTHORITY_FILES_AT_HEAD_AND_WORKTREE"
        or input_contract.get("repository_authority", {}).get("files")
        != REPOSITORY_AUTHORITY_HASHES
    ):
        errors.append("READ_ONLY_INPUT_CONTRACT_INCOMPLETE")
    evidence = contract.get("polarization_evidence_required", {})
    if (
        evidence.get("eb_operator")
        != ["identity_receipt", "response_receipt", "leakage_receipt", "transfer_receipt"]
        or evidence.get("matched_joint_null")
        != ["identity_receipt", "covariance_receipt", "pipeline_receipt"]
        or evidence.get("receipt_content_contract", {}).get("schema")
        != EVIDENCE_RECEIPT_SCHEMA
        or evidence.get("receipt_content_contract", {}).get("exact_top_level_fields")
        != ["schema", "package_id", "evidence_kind", "state", "metrics", "artifacts"]
        or evidence.get("receipt_content_contract", {}).get("artifact_schema")
        != EVIDENCE_ARTIFACT_SCHEMA
        or evidence.get("receipt_content_contract", {}).get("role_substitution_allowed")
        is not False
        or evidence.get("receipt_content_contract", {}).get("source_bytes_sha256_required")
        is not True
        or evidence.get("receipt_content_contract", {}).get("hash_only_receipts_allowed")
        is not False
    ):
        errors.append("POLARIZATION_EVIDENCE_CONTRACT_INCOMPLETE")
    claim_contract = contract.get("claim_contract", {})
    if (
        claim_contract.get("exact_registered_fields_only") is not True
        or claim_contract.get("claim_promotion") is not False
        or claim_contract.get("physical_cause_identified") is not False
        or claim_contract.get("bianchi_family_identified") is not False
        or claim_contract.get("foreground_exclusion") is not False
        or claim_contract.get("shared_data_evalue_multiplication") is not False
    ):
        errors.append("CLAIM_CONTRACT_INCOMPLETE")

    naming = recipe.get("carrier_naming", {})
    if naming.get("raw_q") != "Q_stokes" or naming.get("irrep_q") != "Q_irrep[X]" or naming.get("irrep_o") != "O_irrep[X]":
        errors.append("CARRIER_NAMING_INVALID")
    polarization = recipe.get("polarization_contract", {})
    operator = polarization.get("cut_sky_eb_operator", {})
    if polarization.get("q_u_spin") != 2 or operator.get("target_mode_count") != 24:
        errors.append("POLARIZATION_TEMPLATE_INCOMPLETE")
    if operator.get("missing_mode_policy") != "ABSTAIN_NEVER_ZERO_OR_PRIOR_FILL":
        errors.append("EB_MISSING_MODE_POLICY_INVALID")
    if polarization.get("matched_joint_null", {}).get("rerun_complete_pipeline_per_row") != "REQUIRED":
        errors.append("MATCHED_NULL_TEMPLATE_INCOMPLETE")

    if set(terminals.get("approved_terminal_states", [])) != APPROVED_TERMINALS:
        errors.append("TERMINAL_REGISTRY_MISMATCH")
    lane_records = terminals.get("lanes", [])
    if not isinstance(lane_records, list) or {item.get("lane") for item in lane_records if isinstance(item, Mapping)} != LANES:
        errors.append("LANE_REGISTRY_MISMATCH")
    for item in lane_records if isinstance(lane_records, list) else []:
        if item.get("phase_state") != "PREREGISTERED" or item.get("terminal_state") is not None:
            errors.append(f"FABRICATED_INITIAL_TERMINAL:{item.get('lane')}")
    if set(terminals.get("final_terminal_record_fields", [])) != {
        "lane",
        "phase_state",
        "terminal_state",
        "prerequisites",
        "manifest_receipt",
    }:
        errors.append("FINAL_TERMINAL_SCHEMA_CONTRACT_INVALID")
    if terminals.get("aggregate_state_policy", {}).get(
        "SUCCEEDED_WITH_TYPED_LIMITATIONS_NO_CLAIM_PROMOTION"
    ) != "D9_Z_ONLY":
        errors.append("D9_AGGREGATE_POLICY_INVALID")
    if (
        set(terminals.get("output_bearing_terminal_states", [])) != OUTPUT_BEARING_TERMINALS
        or terminals.get("dependency_policy")
        != "OUTPUT_BEARING_LANES_MAY_CONSUME_ONLY_OUTPUT_BEARING_PREREQUISITES"
        or terminals.get("manifest_receipt_schema")
        != "ABSOLUTE_EXISTING_PATH_PLUS_MATCHING_SHA256_AND_PARSED_CONTENT"
    ):
        errors.append("D9_DEPENDENCY_CONTRACT_INVALID")

    handoff = (root / "CODEX_HANDOFF.md").read_text(encoding="utf-8")
    prompt = (root / "CODEX_HANDOFF_PROMPT.md").read_text(encoding="utf-8")
    for required in ("no raw/CAS execution occurred here", "No GitHub Actions"):
        if required.lower() not in handoff.lower():
            errors.append(f"HANDOFF_REQUIRED_STATEMENT_MISSING:{required}")
    if "NO_ADMISSIBLE_NEW_RESULT" not in prompt or "SUCCEEDED_NO_CLAIM_PROMOTION" not in prompt:
        errors.append("HANDOFF_PROMPT_CLAIM_CEILING_MISSING")
    return errors


def validate_instantiated(config_path: Path | str) -> list[str]:
    path = Path(config_path)
    try:
        config = _load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"CONFIG_PARSE_ERROR:{exc}"]
    errors: list[str] = []
    if set(config) != CONFIG_FIELDS:
        errors.append("CONFIG_FIELD_SET_MISMATCH")
    if config.get("schema") != CONFIG_SCHEMA:
        errors.append("CONFIG_SCHEMA_MISMATCH")
    if config.get("package_id") != PACKAGE_ID:
        errors.append("PACKAGE_ID_MISMATCH")
    authority = config.get("authority")
    if not isinstance(authority, Mapping) or dict(authority) != EXPECTED_AUTHORITY:
        errors.append("AUTHORITY_BINDING_MISMATCH")
    execution_phase = config.get("execution_phase")
    if execution_phase not in {"PREFLIGHT", "FINAL_SEAL"}:
        errors.append("EXECUTION_PHASE_INVALID")
    runtime = config.get("runtime") if isinstance(config.get("runtime"), Mapping) else {}
    required_runtime = ("REPO_ROOT", "OUTPUT_ROOT", "PLANCK_RAW_ROOT", "THEOREM_DOSSIER", "THEOREM_DOSSIER_SHA256", "XACT_PARENT")
    for name in required_runtime:
        if not _nonempty(runtime.get(name)):
            errors.append(f"MISSING_RUNTIME_IDENTITY:{name}")
    for name in ("REPO_ROOT", "OUTPUT_ROOT", "PLANCK_RAW_ROOT", "THEOREM_DOSSIER", "XACT_PARENT"):
        value = runtime.get(name)
        if _nonempty(value) and not Path(value).is_absolute():
            errors.append(f"RUNTIME_PATH_NOT_ABSOLUTE:{name}")
    if _nonempty(runtime.get("REPO_ROOT")):
        repository = Path(runtime["REPO_ROOT"])
        if not _is_git_worktree(repository):
            errors.append("REPO_ROOT_NOT_GIT_WORKTREE")
        else:
            _validate_repository_authority(repository, errors)
    for name in ("OUTPUT_ROOT", "PLANCK_RAW_ROOT", "XACT_PARENT"):
        value = runtime.get(name)
        if _nonempty(value) and Path(value).is_absolute() and not Path(value).is_dir():
            errors.append(f"RUNTIME_DIRECTORY_UNRESOLVED:{name}")

    raw_roots: list[Path] = []
    declared_raw = runtime.get("RAW_ROOTS", [])
    if isinstance(declared_raw, list):
        for value in declared_raw:
            if not _nonempty(value):
                errors.append("RAW_ROOT_IDENTITY_INVALID")
                continue
            if not Path(value).is_absolute():
                errors.append(f"RAW_ROOT_PATH_NOT_ABSOLUTE:{value}")
            raw_path = Path(value)
            if raw_path.is_absolute() and not raw_path.is_dir():
                errors.append(f"RAW_ROOT_UNRESOLVED:{value}")
            raw_roots.append(raw_path.resolve(strict=False))
    else:
        errors.append("RAW_ROOTS_INVALID")
    if _nonempty(runtime.get("PLANCK_RAW_ROOT")):
        raw_roots.append(Path(runtime["PLANCK_RAW_ROOT"]).resolve(strict=False))
    if _nonempty(runtime.get("OUTPUT_ROOT")):
        output_path = Path(runtime["OUTPUT_ROOT"])
        output_root = output_path.resolve(strict=False)
        if not output_path.is_absolute() or any(output_root == raw or _within(output_root, raw) for raw in raw_roots):
            errors.append("OUTPUT_ROOT_INSIDE_RAW_ROOT")
        outputs = config.get("outputs", [])
        if not isinstance(outputs, list) or not outputs:
            errors.append("OUTPUT_PATHS_REQUIRED")
        else:
            for value in outputs:
                candidate_path = Path(str(value))
                if not candidate_path.is_absolute():
                    errors.append(f"OUTPUT_PATH_NOT_ABSOLUTE:{value}")
                candidate = candidate_path.resolve(strict=False)
                if not _within(candidate, output_root):
                    errors.append(f"OUTPUT_PATH_ESCAPE:{value}")
                if any(candidate == raw or _within(candidate, raw) for raw in raw_roots):
                    errors.append(f"OUTPUT_PATH_UNDER_RAW_ROOT:{value}")

    dossier_sha = runtime.get("THEOREM_DOSSIER_SHA256")
    dossier = Path(runtime["THEOREM_DOSSIER"]) if _nonempty(runtime.get("THEOREM_DOSSIER")) else None
    if not isinstance(dossier_sha, str) or re.fullmatch(r"[0-9a-f]{64}", dossier_sha) is None:
        errors.append("DOSSIER_IDENTITY_REQUIRED")
    elif dossier is None or not dossier.is_file():
        errors.append("DOSSIER_LOCATOR_UNRESOLVED")
    elif _sha256(dossier) != dossier_sha:
        errors.append("BLOCKED_BY_DOSSIER_IDENTITY_MISMATCH")

    toolchains = config.get("toolchains") if isinstance(config.get("toolchains"), Mapping) else {}
    if set(toolchains) != {"python", "wolfram", "xact"}:
        errors.append("TOOLCHAIN_SCHEMA_MISMATCH")
    for name, version_argument in (("python", "--version"), ("wolfram", "-version")):
        identity = toolchains.get(name)
        if not isinstance(identity, Mapping) or set(identity) != {"executable", "version", "sha256"}:
            errors.append(f"TOOLCHAIN_SCHEMA_MISMATCH:{name}")
            continue
        if not _concrete_identity(identity.get("version")):
            errors.append(f"MISSING_TOOLCHAIN_IDENTITY:{name}")
            continue
        executable = identity.get("executable")
        if (
            not _nonempty(executable)
            or not Path(executable).is_absolute()
            or not Path(executable).is_file()
            or not os.access(executable, os.X_OK)
        ):
            errors.append(f"TOOLCHAIN_EXECUTABLE_UNRESOLVED:{name}")
            continue
        executable_path = Path(executable)
        declared_hash = identity.get("sha256")
        if (
            not isinstance(declared_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", declared_hash) is None
            or _sha256(executable_path) != declared_hash
        ):
            errors.append(f"TOOLCHAIN_HASH_MISMATCH:{name}")
        derived_version = _derive_executable_version(executable_path, version_argument)
        if derived_version is None or identity.get("version") != derived_version:
            errors.append(f"TOOLCHAIN_VERSION_MISMATCH:{name}")
    xact_identity = toolchains.get("xact")
    if not isinstance(xact_identity, Mapping) or set(xact_identity) != {"parent", "version", "source_archive"}:
        errors.append("TOOLCHAIN_SCHEMA_MISMATCH:xact")
    elif not _concrete_identity(xact_identity.get("version")):
        errors.append("MISSING_TOOLCHAIN_IDENTITY:xact")
    else:
        xact_parent = xact_identity.get("parent")
        if (
            not _nonempty(xact_parent)
            or not Path(xact_parent).is_absolute()
            or not Path(xact_parent).is_dir()
            or xact_parent != runtime.get("XACT_PARENT")
        ):
            errors.append("XACT_PARENT_IDENTITY_MISMATCH")
        if xact_identity.get("version") != EXPECTED_XACT_VERSION:
            errors.append("XACT_VERSION_MISMATCH")
        source_archive = xact_identity.get("source_archive")
        if not isinstance(source_archive, Mapping) or set(source_archive) != {"path", "sha256"}:
            errors.append("XACT_ARCHIVE_IDENTITY_REQUIRED")
        else:
            archive_path = source_archive.get("path")
            archive_sha = source_archive.get("sha256")
            if (
                not _nonempty(archive_path)
                or not Path(archive_path).is_absolute()
                or not Path(archive_path).is_file()
            ):
                errors.append("XACT_ARCHIVE_UNRESOLVED")
            elif (
                archive_sha != EXPECTED_XACT_ARCHIVE_SHA256
                or _sha256(Path(archive_path)) != EXPECTED_XACT_ARCHIVE_SHA256
            ):
                errors.append("XACT_ARCHIVE_HASH_MISMATCH")
    inspection = config.get("inspection") if isinstance(config.get("inspection"), Mapping) else {}
    if set(inspection) != {"explicit_manifest", "explicit_manifest_sha256", "recursive_scan", "commands"}:
        errors.append("INSPECTION_SCHEMA_MISMATCH")
    if inspection.get("recursive_scan") is not False:
        errors.append("RECURSIVE_SCAN_FORBIDDEN:recursive_scan")
    commands = inspection.get("commands", [])
    if not isinstance(commands, list):
        errors.append("INSPECTION_COMMANDS_INVALID")
    else:
        for command in commands:
            if any(pattern.search(str(command)) for pattern in FORBIDDEN_SCAN_PATTERNS):
                errors.append(f"RECURSIVE_SCAN_FORBIDDEN:{command}")
        if commands:
            errors.append("READ_ONLY_INSPECTION_COMMANDS_REQUIRED")
    explicit_manifest = inspection.get("explicit_manifest")
    if _nonempty(explicit_manifest) and not Path(explicit_manifest).is_absolute():
        errors.append("EXPLICIT_INPUT_MANIFEST_PATH_NOT_ABSOLUTE")
    if not _nonempty(explicit_manifest) or not Path(explicit_manifest).is_file():
        errors.append("EXPLICIT_INPUT_MANIFEST_REQUIRED")
    else:
        manifest_path = Path(explicit_manifest)
        manifest_sha = inspection.get("explicit_manifest_sha256")
        if (
            not isinstance(manifest_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", manifest_sha) is None
            or _sha256(manifest_path) != manifest_sha
        ):
            errors.append("EXPLICIT_INPUT_MANIFEST_HASH_MISMATCH")
        try:
            manifest_text = manifest_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append("EXPLICIT_INPUT_MANIFEST_CONTENT_INVALID")
        else:
            if any(pattern.search(manifest_text) for pattern in FORBIDDEN_CLAIM_PATTERNS):
                errors.append("FORBIDDEN_CLAIM_TEXT_IN_INPUT_MANIFEST")

    temperature = config.get("temperature_inverse") if isinstance(config.get("temperature_inverse"), Mapping) else {}
    if not all(temperature.get(name) is True for name in ("has_absolute_temperature", "includes_monopole", "includes_dipole")):
        errors.append("ABSOLUTE_T_MONOPOLE_DIPOLE_REQUIRED")

    polarization = config.get("polarization") if isinstance(config.get("polarization"), Mapping) else {}
    if polarization.get("q_u_spin") != 2 or polarization.get("stokes_fields") != ["I", "Q_stokes", "U"]:
        errors.append("IQU_SPIN2_CONTRACT_REQUIRED")
    operator = polarization.get("eb_operator") if isinstance(polarization.get("eb_operator"), Mapping) else {}
    target = operator.get("target_mode_count")
    rank = operator.get("rank")
    if operator.get("coefficient_level") is not True or target != 24 or rank != target:
        errors.append("EB_OPERATOR_FULL_RANK_REQUIRED")
    condition = operator.get("condition_number")
    ceiling = operator.get("condition_ceiling")
    bounded = (
        operator.get("bounded") is True
        and isinstance(condition, (int, float))
        and not isinstance(condition, bool)
        and isinstance(ceiling, (int, float))
        and not isinstance(ceiling, bool)
        and math.isfinite(float(condition))
        and math.isfinite(float(ceiling))
        and 0.0 < float(condition) <= float(ceiling)
    )
    if not bounded:
        errors.append("EB_OPERATOR_UNBOUNDED")
    if not all(operator.get(name) is True for name in ("pure_e_injection", "pure_b_injection", "out_of_band_alias_test")):
        errors.append("EB_OPERATOR_INJECTION_TESTS_REQUIRED")
    seen_receipt_paths: set[Path] = set()
    seen_artifact_paths: set[Path] = set()
    seen_source_paths: set[Path] = set()
    for field, label in (
        ("identity_receipt", "EB_OPERATOR_IDENTITY"),
        ("response_receipt", "EB_RESPONSE"),
        ("leakage_receipt", "EB_LEAKAGE"),
        ("transfer_receipt", "EB_TRANSFER"),
    ):
        _validate_bound_receipt(
            operator.get(field),
            label,
            errors,
            seen_receipt_paths,
            seen_artifact_paths,
            seen_source_paths,
        )
    matched_null = polarization.get("matched_joint_null") if isinstance(polarization.get("matched_joint_null"), Mapping) else {}
    if matched_null.get("matched") is not True or matched_null.get("reruns_complete_pipeline_per_row") is not True:
        errors.append("MATCHED_POLARIZATION_NULL_REQUIRED")
    for field, label in (
        ("identity_receipt", "NULL_IDENTITY"),
        ("covariance_receipt", "NULL_COVARIANCE"),
        ("pipeline_receipt", "NULL_PIPELINE"),
    ):
        _validate_bound_receipt(
            matched_null.get(field),
            label,
            errors,
            seen_receipt_paths,
            seen_artifact_paths,
            seen_source_paths,
        )

    claims = config.get("claims") if isinstance(config.get("claims"), Mapping) else {}
    if set(claims) != CLAIM_FIELDS:
        errors.append("CLAIM_SCHEMA_MISMATCH")
    if claims.get("same_sky_role") != "SAME_SKY_ROBUSTNESS_ONLY" or claims.get("independent_replication") is not False:
        errors.append("SAME_SKY_INDEPENDENCE_FORBIDDEN")
    if claims.get("product_substitution") is not False:
        errors.append("PRODUCT_SUBSTITUTION_FORBIDDEN")
    if claims.get("claim_promotion") is not False:
        errors.append("CLAIM_PROMOTION_FORBIDDEN")
    for name in (
        "physical_cause_identified",
        "bianchi_family_identified",
        "foreground_exclusion",
        "shared_data_evalue_multiplication",
    ):
        if claims.get(name) is not False:
            errors.append(f"FORBIDDEN_CLAIM_FLAG:{name}")
    for name in ("cross_field_role", "joint_rv_role", "amplitude_conditional_role"):
        if claims.get(name) != "EXPLORATORY_ONLY":
            errors.append(f"EXPLORATORY_ROLE_REQUIRED:{name}")
    if type(claims.get("new_observed_rank")) is not bool:
        errors.append("NEW_OBSERVED_RANK_FLAG_INVALID")
    elif claims["new_observed_rank"] and execution_phase != "FINAL_SEAL":
        errors.append("NEW_OBSERVED_RANK_BEFORE_FINAL_SEAL")
    for value in _claim_strings(claims):
        if any(pattern.search(value) for pattern in FORBIDDEN_CLAIM_PATTERNS):
            errors.append(f"FORBIDDEN_CLAIM_TEXT:{value}")
    for key in set(claims) - CLAIM_FIELDS:
        if any(pattern.search(str(key)) for pattern in FORBIDDEN_CLAIM_PATTERNS):
            errors.append(f"FORBIDDEN_CLAIM_TEXT:{key}")
    for value in _claim_strings(config):
        if any(pattern.search(value) for pattern in FORBIDDEN_CLAIM_PATTERNS):
            errors.append(f"FORBIDDEN_CLAIM_TEXT:{value}")
    admissions = config.get("product_admissions", [])
    if not isinstance(admissions, list):
        errors.append("PRODUCT_ADMISSIONS_INVALID")
    else:
        for item in admissions:
            if not isinstance(item, Mapping) or set(item) != {"requested_product", "admitted_product"}:
                errors.append("PRODUCT_ADMISSION_SCHEMA_MISMATCH")
                continue
            if item.get("requested_product") != item.get("admitted_product"):
                errors.append("PRODUCT_SUBSTITUTION_FORBIDDEN")

    terminals = config.get("terminals", [])
    if not isinstance(terminals, list):
        errors.append("TERMINAL_RECORDS_INVALID")
    else:
        terminal_lanes: list[str] = []
        terminal_states: dict[str, str] = {}
        for item in terminals:
            if not isinstance(item, Mapping):
                errors.append("TERMINAL_RECORD_INVALID")
                continue
            lane = item.get("lane")
            if lane not in LANES:
                errors.append(f"UNKNOWN_LANE:{lane}")
            else:
                terminal_lanes.append(lane)
                terminal_states[lane] = item.get("terminal_state")
            if item.get("terminal_state") not in APPROVED_TERMINALS:
                errors.append(f"UNKNOWN_TERMINAL_STATE:{item.get('terminal_state')}")
            if execution_phase == "FINAL_SEAL":
                if set(item) != {"lane", "phase_state", "terminal_state", "prerequisites", "manifest_receipt"}:
                    errors.append(f"FINAL_TERMINAL_SCHEMA_MISMATCH:{lane}")
                if item.get("phase_state") != "EXECUTED":
                    errors.append(f"FINAL_TERMINAL_NOT_EXECUTED:{lane}")
                if lane in LANE_PREREQUISITES and item.get("prerequisites") != LANE_PREREQUISITES[lane]:
                    errors.append(f"LANE_PREREQUISITE_MISMATCH:{lane}")
                _validate_bound_receipt(
                    item.get("manifest_receipt"),
                    f"LANE_MANIFEST:{lane}",
                    errors,
                    seen_receipt_paths,
                    seen_artifact_paths,
                    seen_source_paths,
                )
        duplicate_lanes = sorted({lane for lane in terminal_lanes if terminal_lanes.count(lane) > 1})
        for lane in duplicate_lanes:
            errors.append(f"DUPLICATE_TERMINAL_LANE:{lane}")
        if execution_phase == "PREFLIGHT" and terminals:
            errors.append("PREFLIGHT_TERMINALS_MUST_BE_EMPTY")
        if execution_phase == "FINAL_SEAL" and (
            set(terminal_lanes) != LANES or len(terminal_lanes) != len(LANES)
        ):
            missing = sorted(LANES - set(terminal_lanes))
            extra = sorted(set(terminal_lanes) - LANES)
            errors.append(
                f"FINAL_SEAL_LANE_COVERAGE_MISMATCH:missing={missing}:extra={extra}"
            )
        if execution_phase == "FINAL_SEAL":
            if terminal_states.get("D.9.Z") == "SUCCEEDED_NO_CLAIM_PROMOTION":
                errors.append("D9_Z_AGGREGATE_TERMINAL_INVALID")
            for lane, state in terminal_states.items():
                if lane != "D.9.Z" and state == "SUCCEEDED_WITH_TYPED_LIMITATIONS_NO_CLAIM_PROMOTION":
                    errors.append(f"AGGREGATE_TERMINAL_ON_NONAGGREGATE_LANE:{lane}")
                if lane != "D.9.Z" and state in OUTPUT_BEARING_TERMINALS:
                    failed = [
                        prerequisite
                        for prerequisite in LANE_PREREQUISITES.get(lane, [])
                        if terminal_states.get(prerequisite) not in OUTPUT_BEARING_TERMINALS
                    ]
                    if failed:
                        errors.append(
                            f"FAILED_PREREQUISITE_CONSUMED:{lane}:prerequisites={failed}"
                        )
            if claims.get("new_observed_rank") is True and terminal_states.get("D.9.Z") != "SUCCEEDED_WITH_TYPED_LIMITATIONS_NO_CLAIM_PROMOTION":
                errors.append("NEW_OBSERVED_RANK_WITHOUT_D9_Z_SUCCESS")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("package", "instantiated"), required=True)
    parser.add_argument("--package-root", type=Path, default=DEFAULT_PACKAGE_ROOT)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "package":
        if args.config is not None:
            parser.error("--config is only valid in instantiated mode")
        errors = validate_package(args.package_root)
    else:
        if args.config is None:
            parser.error("--config is required in instantiated mode")
        errors = validate_instantiated(args.config)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"VALID:{args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
