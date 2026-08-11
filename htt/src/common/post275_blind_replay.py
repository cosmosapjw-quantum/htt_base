"""Fail-closed contracts for the PR-287 fresh blind synthetic lane.

This module defines identities and chronology only.  It never obtains entropy,
constructs a truth mapping, reads historical PR-273 results, or writes an
artifact.  Scientific execution remains blocked until the canonical dependency
activation receipt is complete.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import importlib
import inspect
import json
import math
from pathlib import Path
import re
import sys
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

import yaml
import numpy as np
from scipy.stats import beta as beta_distribution


class BlindReplayContractError(ValueError):
    """Raised when a PR-287 identity or blindness contract is invalid."""


class DependencyActivationStatus(str, Enum):
    ACTIVATED = "ACTIVATED"
    BLOCKED = "BLOCKED"


class BlindReplayStage(str, Enum):
    SPEC_AND_DEPENDENCY_FREEZE = "SPEC_AND_DEPENDENCY_FREEZE"
    CHALLENGE_DESIGN = "CHALLENGE_DESIGN"
    BLIND_ANALYSIS = "BLIND_ANALYSIS"
    REGISTERED_ADJUDICATION = "REGISTERED_ADJUDICATION"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"


class BlindReplayPackKind(str, Enum):
    PACK_A = "PACK_A"
    PACK_B = "PACK_B"
    PACK_C = "PACK_C"


_ACTIVATION_TOKEN = object()
_CHALLENGE_TOKEN = object()
_SUBMISSION_TOKEN = object()
_TRUTH_REFERENCE_TOKEN = object()
_FREEZE_RECEIPT_TOKEN = object()
_HISTORICAL_RECEIPT_TOKEN = object()
_PILLAR_PROJECTION_TOKEN = object()
_DIAGNOSTIC_PACK_TOKEN = object()
_STAGE_ROW_TOKEN = object()
_STAGE_TRACE_TOKEN = object()
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_RAW_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REVIEW_ASSIGNMENT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "assignment_id",
        "agent_type",
        "context_version",
        "work_unit_id",
        "change_set_id",
        "publication_group_id",
        "workflow_role",
        "candidate_binding",
        "independence_mode",
        "risk_tier",
        "claim_ids",
        "task",
        "required_inputs",
        "allowed_tools",
        "required_outputs",
        "result_path",
        "status",
        "assignment_sha256",
    }
)
_REVIEW_RESULT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "assignment_id",
        "context_version",
        "agent_type",
        "work_unit_id",
        "change_set_id",
        "publication_group_id",
        "workflow_role",
        "candidate_binding",
        "independence_mode",
        "status",
        "result_path",
        "assignment_sha256",
        "launch_id",
        "launch_evidence",
        "execution_evidence",
        "files_read",
        "files_read_evidence",
        "started_at",
        "completed_at",
        "tool_versions",
        "commands",
        "artifacts",
        "review_coverage_path",
        "review_coverage_sha256",
        "findings",
        "claim_results",
        "errors",
    }
)
_CANONICAL_SPEC_PATH = "docs/research_program/post_pr275/pr287_spec.yaml"
_CANONICAL_STATUS_PATH = "docs/codex_handoff/pr_status.yaml"
_DEPENDENCY_AUTHORITY = {
    "PR-281": {
        "required_receipt": "docs/PR_DELTAS/pr-281.md",
        "required_terminal": None,
        "terminal_path": None,
    },
    "PR-282": {
        "required_receipt": "docs/generated/pr282_exact_parity_readiness_receipt.json",
        "required_terminal": "PASS_EXECUTABLE_P_EQUIVARIANCE",
        "terminal_path": ("readiness_receipt", "terminal", "g3_outcome"),
    },
    "PR-283": {
        "required_receipt": "docs/generated/pr283_weak_identification_receipt.json",
        "required_terminal": "PASS_WEAK_IDENTIFICATION_ABSTENTION",
        "terminal_path": ("terminal", "g4_outcome"),
    },
    "PR-284": {
        "required_receipt": "docs/generated/pr284_depth_path_doob_receipt.json",
        "required_terminal": "PASS_PREMISE_BOUND_DEPTH_PATH_CALIBRATION",
        "terminal_path": ("terminal_status",),
    },
    "PR-285": {
        "required_receipt": (
            "docs/research_program/post_pr275/pillar_t_adjudication/"
            "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
        ),
        "required_terminal": "PASS_COMPLETE_PILLAR_T_ADJUDICATION",
        "terminal_path": ("terminal",),
    },
    "PR-286": {
        "required_receipt": (
            "docs/research_program/post_pr275/pillar_s_adjudication/"
            "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
        ),
        "required_terminal": "PASS_COMPLETE_PILLAR_S_ADJUDICATION",
        "terminal_path": ("terminal",),
    },
}
_PILLAR_AUTHORITY = {
    "T": {
        "path": (
            "docs/research_program/post_pr275/pillar_t_adjudication/"
            "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
        ),
        "sha256": "270b80e94767b48d58032d96d48f829138f6d5ffa301e9c8eb48bbd72b5c7e66",
    },
    "S": {
        "path": (
            "docs/research_program/post_pr275/pillar_s_adjudication/"
            "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
        ),
        "sha256": "b5ea12647f1d7818da3702b3da8d127f490a15cdef8e37fa8958cfe803b3ee5a",
    },
}
_CASE_IDS = (
    "D01",
    "D02",
    "D03",
    "D04",
    "H01",
    "H02",
    "H03",
    "H04",
    "H05",
    "H06",
    "H07",
    "H08",
)
_SCENARIO_ORDER = (
    "SCALAR_LIMIT",
    "TENSOR_ONLY",
    "MISSING_CHANNEL",
    "COVARIANCE_CORRECT",
    "COVARIANCE_MISSPECIFIED_PAIRED",
    "MULTIPLICITY_STRESS",
    "COVERAGE_FAILURE",
    "WEAK_LOCAL_GLOBAL_OVERLAP",
    "SEPARATED_LOCAL_GLOBAL",
    "OPEN_SET_UNKNOWN",
    "PROVED_DEPTH_PATH",
    "PREMISE_MISSING_DEPTH_PATH",
)
_SCENARIO_ESTIMANDS = {
    "SCALAR_LIMIT": ("scalar_limit_crosswalk", "NOT_APPLICABLE"),
    "TENSOR_ONLY": ("tensor_channel_response", "NOT_APPLICABLE"),
    "MISSING_CHANNEL": ("typed_missingness", "REQUIRED_ABSTENTION"),
    "COVARIANCE_CORRECT": (
        "covariance_calibrated_coverage",
        "CALIBRATED_CONTROL",
    ),
    "COVARIANCE_MISSPECIFIED_PAIRED": (
        "paired_covariance_failure_visibility",
        "MISSPECIFIED_NEGATIVE_CONTROL",
    ),
    "MULTIPLICITY_STRESS": (
        "familywise_error_control",
        "SIMULTANEOUS_FAILURE_VISIBLE",
    ),
    "COVERAGE_FAILURE": (
        "registered_interval_coverage",
        "COVERAGE_FAILURE_VISIBLE",
    ),
    "WEAK_LOCAL_GLOBAL_OVERLAP": (
        "source_separation_abstention",
        "TYPE_UNIDENTIFIED",
    ),
    "SEPARATED_LOCAL_GLOBAL": (
        "source_separation_candidate_eligibility",
        "NOT_APPLICABLE",
    ),
    "OPEN_SET_UNKNOWN": ("open_set_unknown_abstention", "UNKNOWN_CLASS"),
    "PROVED_DEPTH_PATH": (
        "premise_bound_depth_calibration",
        "NOT_APPLICABLE",
    ),
    "PREMISE_MISSING_DEPTH_PATH": (
        "depth_bound_unavailability",
        "MATCHED_MOCKS_REQUIRED",
    ),
}
_SCENARIO_FIELDS = frozenset(
    {
        "scenario_id",
        "partition",
        "data_generating_law_id",
        "estimand_id",
        "analysis_unit",
        "covariance_generator_id",
        "covariance_analysis_id",
        "covariance_generator_matrix",
        "covariance_analysis_matrix",
        "latent_draw_inventory_id",
        "replicate_or_exact_enumeration_rule",
        "exact_enumeration_cell_ids",
        "seed_policy_id",
        "hypothesis_family_id",
        "alpha",
        "simultaneous_method",
        "acceptance_rule_id",
        "expected_negative_control_terminal",
        "mc_precision_rule_id",
    }
)
_CHALLENGE_CASE_FIELDS = frozenset(
    {"case_id", "observable_vector", "covariance_id", "mask_id"}
)
_CASE_ANALYSIS_INPUT_FIELDS = frozenset(
    {
        "case_id",
        "supported_quotient",
        "response_provider_available",
        "local_response_rank",
        "global_response_rank",
        "joint_response_rank",
        "response_class_cardinality",
        "minimum_principal_angle",
        "weak_angle_threshold",
        "weak_identification",
        "unknown_distance",
        "unknown_distance_threshold",
        "response_equivalence",
        "margin_abstention",
        "depth_premise_status",
        "finite_depth_bound",
        "matched_mock_status",
        "covariance_status",
        "raw_p_value",
        "coverage_evidence_mode",
        "coverage_cell_results",
    }
)
_CHALLENGE_FORBIDDEN_KEYS = frozenset(
    {
        "truth",
        "truth_map",
        "truth_mapping",
        "truth_vault",
        "truth_vault_path",
        "truth_vault_reference",
        "scenario_truth",
        "expected_label",
        "expected_labels",
        "expected_terminal",
        "held_out_scenario_mapping",
        "seed",
        "seed_bytes",
        "seed_value",
        "disclosed_seed",
        "reviewer_verdict",
        "historical_pr273_pack",
        "historical_pr273_result",
        "historical_result_number",
        "adjudication",
        "analyst_submission",
    }
)
_SUBMISSION_FORBIDDEN_KEYS = _CHALLENGE_FORBIDDEN_KEYS | {
    "truth_vault_content",
}
_STAGE_LAYOUT = {
    BlindReplayStage.SPEC_AND_DEPENDENCY_FREEZE: (
        frozenset({"spec_content_id", "status_content_id"}),
        frozenset({"dependency_activation_receipt_content_id"}),
    ),
    BlindReplayStage.CHALLENGE_DESIGN: (
        frozenset(
            {
                "dependency_activation_receipt_content_id",
                "challenge_config_content_id",
                "threshold_contract_content_id",
            }
        ),
        frozenset(
            {
                "challenge_content_id",
                "truth_vault_content_id",
                "seed_commitment_content_id",
                "case_inventory_content_id",
            }
        ),
    ),
    BlindReplayStage.BLIND_ANALYSIS: (
        frozenset(
            {
                "challenge_content_id",
                "challenge_config_content_id",
                "threshold_contract_content_id",
            }
        ),
        frozenset({"submission_content_id"}),
    ),
    BlindReplayStage.REGISTERED_ADJUDICATION: (
        frozenset(
            {
                "truth_vault_content_id",
                "submission_content_id",
                "challenge_content_id",
                "threshold_contract_content_id",
            }
        ),
        frozenset(
            {
                "adjudication_content_id",
                "pack_A_content_id",
                "pack_B_content_id",
                "pack_C_content_id",
                "terminal_receipt_content_id",
            }
        ),
    ),
    BlindReplayStage.HISTORICAL_REPLAY: (
        frozenset(
            {"submission_content_id", "historical_pr273_pack_content_id"}
        ),
        frozenset({"historical_replay_receipt_content_id"}),
    ),
}
_PACK_REQUIRED_SURFACES = {
    BlindReplayPackKind.PACK_A: (
        "x_phi",
        "Q_phi",
        "Pi_phi_of_q",
        "F_phi_certified",
        "G_F",
        "SectorStress",
        "support_utilization",
        "partial_identification",
    ),
    BlindReplayPackKind.PACK_B: (
        "rank",
        "principal_angles",
        "covariance_status",
        "weak_identification",
        "abstention",
        "depth_calibration",
        "coverage",
    ),
    BlindReplayPackKind.PACK_C: (
        "x_phi",
        "Q_phi",
        "Pi_phi_of_q",
        "F_phi_certified",
        "G_F",
        "direction_coherence",
        "depth_coherence",
    ),
}
_PACK_OWNER = {
    BlindReplayPackKind.PACK_A: "COMMON",
    BlindReplayPackKind.PACK_B: "HTT",
    BlindReplayPackKind.PACK_C: "MIO",
}
_PACK_FACTORY_MODULE = {
    BlindReplayPackKind.PACK_A: "common.post275_blind_replay",
    BlindReplayPackKind.PACK_B: "htt.infer.post275_blind_replay",
    BlindReplayPackKind.PACK_C: "mio.reports.post275_blind_replay",
}
_PACK_FACTORY_NAME = {
    BlindReplayPackKind.PACK_A: "build_common_pack_a",
    BlindReplayPackKind.PACK_B: "build_htt_pack_b",
    BlindReplayPackKind.PACK_C: "build_mio_pack_c",
}
_PACK_FACTORY_PATH = {
    BlindReplayPackKind.PACK_A: "htt/src/common/post275_blind_replay.py",
    BlindReplayPackKind.PACK_B: "htt/htt/htt/infer/post275_blind_replay.py",
    BlindReplayPackKind.PACK_C: "htt/mio/reports/post275_blind_replay.py",
}
_PACK_FORBIDDEN_KEYS = frozenset(
    {
        "likelihood",
        "posterior",
        "bayes_factor",
        "evidence",
        "truth_probability",
        "family_label",
        "family_candidate",
        "detected_geometry",
        "geometry_detected",
        "truth_certificate",
        "derived_numeric_value_by_common",
    }
)
_PACK_INPUT_IDENTITIES = frozenset(
    {
        "challenge_content_id",
        "submission_content_id",
        "freeze_receipt_content_id",
        "adjudication_content_id",
        "pillar_t_projection_content_id",
        "pillar_s_projection_content_id",
    }
)
_SURFACE_BASE_FIELDS = frozenset(
    {
        "subject_owner",
        "schema_id",
        "content_id",
        "status",
        "allowed_use",
        "forbidden_use",
    }
)
_SURFACE_SEMANTIC_FIELDS = {
    "x_phi": frozenset(
        {"units_normalization_and_frame", "sign_orientation_convention", "value"}
    ),
    "Q_phi": frozenset(
        {"policy_id", "denominator_identity", "zero_denominator_status", "value"}
    ),
    "Pi_phi_of_q": frozenset(
        {"q_threshold", "comparison_rule", "denominator_identity", "value"}
    ),
    "F_phi_certified": frozenset(
        {"ceiling_identity", "sign_clean_status", "admissibility_status", "value"}
    ),
    "G_F": frozenset(
        {
            "ordered_depth_bin_identity",
            "path_identity",
            "covariance_id",
            "null_status",
            "value",
        }
    ),
    "rank": frozenset(
        {
            "local_response_rank",
            "global_response_rank",
            "joint_response_rank",
            "identification_status",
        }
    ),
    "principal_angles": frozenset(
        {"minimum_principal_angle", "weak_threshold", "weak_identification_status"}
    ),
    "covariance_status": frozenset(
        {"generator_covariance_id", "analysis_covariance_id", "covariance_status"}
    ),
    "weak_identification": frozenset(
        {
            "classifier_terminal",
            "precedence_rule_id",
            "response_equivalence",
            "margin_abstention",
        }
    ),
    "abstention": frozenset(
        {"unknown_distance", "unknown_threshold", "abstention_status"}
    ),
    "depth_calibration": frozenset(
        {"premise_status", "finite_bound", "matched_mock_status"}
    ),
    "coverage": frozenset(
        {
            "hypothesis_family_id",
            "simultaneous_method",
            "coverage_status",
            "mc_precision_status",
        }
    ),
    "direction_coherence": frozenset(
        {"direction_frame", "covariance_id", "null_status"}
    ),
    "depth_coherence": frozenset(
        {"ordered_depth_bin_identity", "path_identity", "covariance_id", "null_status"}
    ),
}
_PACK_SHARED_METADATA = frozenset(
    {
        "owner",
        "scope",
        "claim_tier",
        "claim_level",
        "scientific_artifact_mode",
        "transfer_source",
        "config_and_input_identities",
        "synthetic_sky_mask_status",
        "covariance_and_null_status",
        "observed_data_executed",
        "public_use",
        "scientific_status_effect",
        "family_identification_gate",
        "evidence_lane_identity",
        "pr151_partial_data_excluded",
        "likelihood_semantics",
        "prior_applicability_and_identity",
        "units_normalization_and_frame",
        "sign_orientation_convention",
        "surface_semantic_content_ids",
        "seed_commitment_and_disclosure_status",
        "assumptions",
        "caveats",
        "generating_procedure",
        "git_commit_or_worktree_state",
    }
)


def canonical_json_sha256(payload: object) -> str:
    """Return the canonical JSON content identity for a JSON-like payload."""

    try:
        encoded = json.dumps(
            _thaw(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BlindReplayContractError(
            "payload is not finite canonical JSON"
        ) from exc
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _identity(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise BlindReplayContractError(f"{field} must be a sha256 content identity")
    return value


def covariance_matrix_content_id(value: object) -> str:
    """Validate an exact finite SPD covariance and return its semantic ID."""

    try:
        matrix = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise BlindReplayContractError("covariance matrix must be numeric") from exc
    if (
        matrix.ndim != 2
        or matrix.shape[0] == 0
        or matrix.shape[0] != matrix.shape[1]
        or not np.all(np.isfinite(matrix))
        or not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-14)
    ):
        raise BlindReplayContractError(
            "covariance matrix must be finite square and symmetric"
        )
    try:
        np.linalg.cholesky(matrix)
    except np.linalg.LinAlgError as exc:
        raise BlindReplayContractError(
            "covariance matrix must be positive definite"
        ) from exc
    return canonical_json_sha256(
        {
            "domain": "PR287_COVARIANCE_MATRIX_V1",
            "matrix": matrix.tolist(),
        }
    )


def _utc_timestamp(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise BlindReplayContractError(f"{field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise BlindReplayContractError(f"{field} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise BlindReplayContractError(f"{field} must be UTC")
    return value


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        frozen = {str(key): _freeze(item) for key, item in value.items()}
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise BlindReplayContractError("non-finite float is forbidden")
        return value
    raise BlindReplayContractError(
        f"unsupported JSON value type: {type(value).__name__}"
    )


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, list):
        return [_thaw(item) for item in value]
    return value


def _scan_forbidden(value: object, forbidden: frozenset[str], path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in forbidden:
                raise BlindReplayContractError(
                    f"forbidden blind field {key!r} at {path}"
                )
            _scan_forbidden(item, forbidden, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _scan_forbidden(item, forbidden, f"{path}[{index}]")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_file_within(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise BlindReplayContractError("receipt path must be a nonempty string")
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise BlindReplayContractError("receipt path escapes repository root")
    candidate = root / relative_path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise BlindReplayContractError("receipt path escapes repository root") from exc
    cursor = root
    for component in relative_path.parts:
        cursor = cursor / component
        if cursor.is_symlink():
            raise BlindReplayContractError("receipt path traverses a symlink")
    if resolved != candidate or not candidate.is_file():
        raise BlindReplayContractError("receipt is not an existing regular file")
    return candidate


def _declared_file_within(root: Path, path: Path, field: str) -> Path:
    """Validate a caller-supplied spec/status path without resolving aliases first."""

    declared = path.absolute()
    try:
        relative = declared.relative_to(root)
    except ValueError as exc:
        raise BlindReplayContractError(
            f"{field} must be inside the repository root"
        ) from exc
    try:
        return _regular_file_within(root, relative.as_posix())
    except BlindReplayContractError as exc:
        raise BlindReplayContractError(f"{field} is invalid: {exc}") from exc


def _load_mapping(path: Path, field: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise BlindReplayContractError(f"{field} must be a regular file")
    try:
        if path.suffix == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
        else:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise BlindReplayContractError(f"{field} cannot be parsed") from exc
    if not isinstance(value, dict):
        raise BlindReplayContractError(f"{field} must contain a mapping")
    return value


def _repository_root_from_source() -> Path:
    source = Path(__file__).resolve()
    for parent in source.parents:
        expected = parent / "htt/src/common/post275_blind_replay.py"
        if expected.is_file() and expected.resolve() == source:
            return parent
    raise BlindReplayContractError("canonical repository root is unavailable")


_HARNESS_MODULE_PROVENANCE = {
    "publication_integrity": (
        "publication_integrity.py",
        "load_publication_policy",
    ),
    "profile_registry": ("profile_registry.py", "load_profile_registry"),
    "_harness": ("_harness.py", "validate_run_plan_payload"),
    "strict_result_validation": (
        "strict_result_validation.py",
        "load_and_validate_registered_result_file",
    ),
}


def _canonical_harness_validation_modules() -> tuple[
    dict[str, object], tuple[tuple[str, str, str], ...]
]:
    """Resolve every validator module from one repository and bind its bytes."""

    root = _repository_root_from_source()
    scripts_dir = root / ".agent-harness/scripts"
    inserted = False
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
        inserted = True
    modules: dict[str, object] = {}
    provenance: list[tuple[str, str, str]] = []
    try:
        for module_name, (filename, required_symbol) in (
            _HARNESS_MODULE_PROVENANCE.items()
        ):
            declared = scripts_dir / filename
            if declared.is_symlink() or not declared.is_file():
                raise BlindReplayContractError(
                    "canonical harness module provenance is unavailable"
                )
            expected = declared.resolve()
            module = importlib.import_module(module_name)
            module_file = getattr(module, "__file__", None)
            module_spec = getattr(module, "__spec__", None)
            spec_origin = getattr(module_spec, "origin", None)
            loader_path = getattr(getattr(module_spec, "loader", None), "path", None)
            symbol = getattr(module, required_symbol, None)
            code = getattr(symbol, "__code__", None)
            if (
                not isinstance(module_file, str)
                or not module_file
                or Path(module_file).resolve() != expected
                or not isinstance(spec_origin, str)
                or not spec_origin
                or Path(spec_origin).resolve() != expected
                or not isinstance(loader_path, str)
                or not loader_path
                or Path(loader_path).resolve() != expected
                or not callable(symbol)
                or getattr(symbol, "__module__", None) != module_name
                or code is None
                or Path(str(code.co_filename)).resolve() != expected
            ):
                raise BlindReplayContractError(
                    f"canonical harness module provenance drifted: {module_name}"
                )
            modules[module_name] = module
            provenance.append(
                (
                    module_name,
                    expected.relative_to(root).as_posix(),
                    _sha256_file(expected),
                )
            )
    except (ImportError, OSError) as exc:
        raise BlindReplayContractError(
            "canonical harness module provenance is unavailable"
        ) from exc
    finally:
        if inserted:
            sys.path.remove(str(scripts_dir))
    return modules, tuple(provenance)


def _canonical_harness_validation_module():
    """Load the repository's single schema-v3 result-validation kernel.

    PR-287 activation consumes repository-local review evidence, so accepting a
    predecessor must use the same validator as the publication harness.  The
    harness directory is intentionally not a Python package; resolve it from
    this source file and fail closed if another checkout's cached module would
    be used.
    """

    modules, _ = _canonical_harness_validation_modules()
    return modules["strict_result_validation"]


def _validate_review_result_with_canonical_kernel(
    *,
    root: Path,
    run_id: str,
    context_version: str,
    assignment_payload: Mapping[str, object],
    result_payload: Mapping[str, object],
    result_file: Path,
    expected_result_path: str,
) -> None:
    modules, provenance_before = _canonical_harness_validation_modules()
    validator = modules["strict_result_validation"]
    harness = modules["_harness"]
    index = _load_mapping(
        root / ".agent-harness/context/CONTEXT_INDEX.json",
        "harness context index",
    )
    if index.get("context_version") != context_version:
        raise BlindReplayContractError(
            "review context version is not the registered repository context"
        )
    plan_file = root / ".agent-harness" / "runs" / run_id / "RUN_PLAN.json"
    plan = _load_mapping(plan_file, "review RUN_PLAN")
    errors = list(
        harness.validate_run_plan_payload(
            plan,
            repo=root,
            run_id=run_id,
            context_version=context_version,
        )
    )
    if assignment_payload.get("independence_mode") != "blind-results":
        errors.append(
            "predecessor review must use blind-results independence"
        )
    if assignment_payload.get("allowed_sibling_results") not in (None, []):
        errors.append(
            "blind predecessor review cannot authorize sibling-result reads"
        )
    validation = validator.load_and_validate_registered_result_file(
        root,
        result_file,
        run_id=run_id,
        context_version=context_version,
    )
    errors.extend(validation.errors)
    if (
        validation.result_path != result_file
        or validation.assignment != assignment_payload
        or validation.result != result_payload
        or expected_result_path
        != result_file.relative_to(root).as_posix()
    ):
        errors.append("canonical registered review evidence differs from its caller")
    if errors:
        raise BlindReplayContractError(
            "canonical review result validation failed: " + "; ".join(errors)
        )
    modules_after, provenance_after = _canonical_harness_validation_modules()
    if provenance_after != provenance_before or any(
        modules_after[name] is not module for name, module in modules.items()
    ):
        raise BlindReplayContractError(
            "canonical harness module provenance changed during validation"
        )


def _validate_review_coverage_receipt(
    *,
    coverage_file: Path,
    run_id: str,
    assignment_id: str,
    assignment_payload: Mapping[str, object],
    candidate_binding: Mapping[str, object],
) -> None:
    """Validate the self-sealed, candidate-bound portion of reviewer coverage."""

    coverage = _load_mapping(coverage_file, "review coverage")
    unsigned = dict(coverage)
    coverage_seal = unsigned.pop("coverage_sha256", None)
    expected_seal = hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    cells = coverage.get("coverage_cells")
    oracles = coverage.get("independent_oracles")
    binding_fields = {
        "run_id": run_id,
        "assignment_id": assignment_id,
        "change_set_id": assignment_payload.get("change_set_id"),
        "publication_group_id": assignment_payload.get("publication_group_id"),
        "candidate_sha": candidate_binding.get("candidate_sha"),
    }
    for field in (
        "candidate_tree_sha",
        "seal_sha256",
        "diff_sha256",
        "changed_files_sha256",
    ):
        if candidate_binding.get(field) is not None:
            coverage_field = (
                "candidate_seal_sha256" if field == "seal_sha256" else field
            )
            binding_fields[coverage_field] = candidate_binding.get(field)
    if (
        coverage.get("schema_version") != 1
        or coverage_seal != expected_seal
        or any(coverage.get(field) != expected for field, expected in binding_fields.items())
        or coverage.get("first_verdict_read_only") is not True
        or type(coverage.get("correlated_review")) is not bool
        or (
            assignment_payload.get("independence_mode") == "blind-results"
            and coverage.get("correlated_review") is not False
        )
        or not isinstance(coverage.get("completed_at"), str)
        or not coverage.get("completed_at")
        or not isinstance(cells, list)
        or not cells
        or any(
            not isinstance(row, Mapping)
            or not isinstance(row.get("cell"), str)
            or not row.get("cell")
            or row.get("status") not in {"PASS", "NOT_APPLICABLE"}
            or not isinstance(row.get("evidence_refs"), list)
            or (
                row.get("status") == "PASS"
                and not row.get("evidence_refs")
            )
            or not isinstance(row.get("rationale"), str)
            for row in cells
        )
        or len({str(row["cell"]) for row in cells}) != len(cells)
        or not isinstance(oracles, list)
        or (
            assignment_payload.get("risk_tier") in {"R2", "R3"}
            and not oracles
        )
        or any(
            not isinstance(oracle, Mapping)
            or oracle.get("status") != "PASS"
            for oracle in oracles
        )
    ):
        raise BlindReplayContractError(
            "review coverage contradicts the sealed pass result"
        )


def _value_at_path(value: object, path: Sequence[str]) -> object:
    current = value
    for component in path:
        if not isinstance(current, Mapping) or component not in current:
            return None
        current = current[component]
    return current


def _validate_review_receipt(
    *, root: Path, path: object, upstream_id: str, candidate_sha: str
) -> tuple[str, str]:
    review_file = _regular_file_within(root, path)
    payload = _load_mapping(review_file, f"{upstream_id} review receipt")
    binding = payload.get("candidate_binding")
    results = payload.get("results")
    run_id = payload.get("run_id")
    context_version = payload.get("context_version")
    if (
        payload.get("schema_version") != 1
        or payload.get("work_unit_id") != upstream_id
        or not isinstance(run_id, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id)
        or not isinstance(context_version, str)
        or not re.fullmatch(r"[0-9a-f]{64}", context_version)
        or not isinstance(binding, Mapping)
        or binding.get("state") != "frozen"
        or binding.get("candidate_sha") != candidate_sha
        or not isinstance(results, list)
        or not results
    ):
        raise BlindReplayContractError("review receipt candidate binding drifted")
    expected_review_path = f".agent-harness/runs/{run_id}/RUN_SUMMARY.json"
    if review_file.relative_to(root).as_posix() != expected_review_path:
        raise BlindReplayContractError("review receipt path is not registered")
    seen_paths: set[str] = set()
    seen_assignments: set[str] = set()
    for row in results:
        if (
            not isinstance(row, Mapping)
            or row.get("status") != "pass"
            or not isinstance(row.get("assignment_id"), str)
            or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._-]*", str(row.get("assignment_id"))
            )
        ):
            raise BlindReplayContractError("review receipt contains a non-pass result")
        assignment_id = str(row["assignment_id"])
        result_file = _regular_file_within(root, row.get("path"))
        result_relative = result_file.relative_to(root).as_posix()
        expected_result_path = (
            f".agent-harness/runs/{run_id}/results/{assignment_id}.json"
        )
        if (
            result_relative != expected_result_path
            or result_relative in seen_paths
            or assignment_id in seen_assignments
        ):
            raise BlindReplayContractError(
                "review result path or assignment registration drifted"
            )
        seen_paths.add(result_relative)
        seen_assignments.add(assignment_id)
        if row.get("sha256") != _sha256_file(result_file):
            raise BlindReplayContractError("review result content identity drifted")
        result_payload = _load_mapping(result_file, f"{upstream_id} review result")
        assignment_file = _regular_file_within(
            root,
            f".agent-harness/runs/{run_id}/assignments/{assignment_id}.json",
        )
        assignment_payload = _load_mapping(
            assignment_file, f"{upstream_id} review assignment"
        )
        assignment_unsigned = dict(assignment_payload)
        assignment_seal = assignment_unsigned.pop("assignment_sha256", None)
        expected_assignment_seal = hashlib.sha256(
            json.dumps(
                assignment_unsigned, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
        result_binding = result_payload.get("candidate_binding")
        assignment_binding = assignment_payload.get("candidate_binding")
        coverage_path = result_payload.get("review_coverage_path")
        coverage_sha = result_payload.get("review_coverage_sha256")
        coverage_file = None
        if isinstance(coverage_path, str):
            coverage_file = _regular_file_within(root, coverage_path)
        assignment_claim_ids = assignment_payload.get("claim_ids")
        claim_results = result_payload.get("claim_results")
        observed_claim_ids = (
            tuple(
                item.get("claim_id")
                for item in claim_results
                if isinstance(item, Mapping)
            )
            if isinstance(claim_results, list)
            else ()
        )
        artifacts = result_payload.get("artifacts")
        matching_coverage_artifacts = (
            [
                item
                for item in artifacts
                if isinstance(item, Mapping)
                and item.get("path") == coverage_path
                and item.get("sha256") == coverage_sha
                and item.get("producer") == assignment_id
            ]
            if isinstance(artifacts, list)
            else []
        )
        assignment_claim_ids_valid = (
            isinstance(assignment_claim_ids, list)
            and bool(assignment_claim_ids)
            and all(
                isinstance(item, str) and bool(item)
                for item in assignment_claim_ids
            )
            and len(set(assignment_claim_ids)) == len(assignment_claim_ids)
        )
        claim_results_valid = (
            isinstance(claim_results, list)
            and assignment_claim_ids_valid
            and len(claim_results) == len(assignment_claim_ids)
            and all(
                isinstance(item, Mapping)
                and isinstance(item.get("claim_id"), str)
                and item.get("outcome") == "examined_no_findings"
                and item.get("finding_ids") == []
                and isinstance(item.get("summary"), str)
                and bool(item.get("summary"))
                and isinstance(item.get("evidence_refs"), list)
                and bool(item.get("evidence_refs"))
                and all(
                    isinstance(ref, str) and bool(ref)
                    for ref in item.get("evidence_refs", [])
                )
                for item in claim_results
            )
            and set(observed_claim_ids) == set(assignment_claim_ids)
            and len(set(observed_claim_ids)) == len(observed_claim_ids)
        )
        if (
            not _REVIEW_ASSIGNMENT_REQUIRED_FIELDS.issubset(assignment_payload)
            or not _REVIEW_RESULT_REQUIRED_FIELDS.issubset(result_payload)
            or assignment_payload.get("schema_version") != 3
            or assignment_payload.get("run_id") != run_id
            or assignment_payload.get("assignment_id") != assignment_id
            or assignment_payload.get("context_version") != context_version
            or assignment_payload.get("work_unit_id") != upstream_id
            or assignment_payload.get("workflow_role") != "reviewer"
            or not isinstance(assignment_payload.get("agent_type"), str)
            or assignment_payload.get("independence_mode") != "blind-results"
            or not isinstance(assignment_payload.get("risk_tier"), str)
            or not assignment_claim_ids_valid
            or not isinstance(assignment_payload.get("task"), str)
            or not assignment_payload.get("task")
            or not isinstance(assignment_payload.get("required_inputs"), list)
            or not assignment_payload.get("required_inputs")
            or not isinstance(assignment_payload.get("allowed_tools"), list)
            or not assignment_payload.get("allowed_tools")
            or any(
                not isinstance(item, str) or not item
                for item in assignment_payload.get("allowed_tools", [])
            )
            or not isinstance(assignment_payload.get("required_outputs"), list)
            or not assignment_payload.get("required_outputs")
            or any(
                not isinstance(item, str) or not item
                for item in assignment_payload.get("required_outputs", [])
            )
            or assignment_payload.get("status") != "registered"
            or assignment_payload.get("result_path") != expected_result_path
            or not isinstance(assignment_binding, Mapping)
            or assignment_binding.get("state") != "frozen"
            or assignment_binding.get("candidate_sha") != candidate_sha
            or assignment_seal != expected_assignment_seal
            or result_payload.get("schema_version") != 3
            or result_payload.get("run_id") != run_id
            or result_payload.get("assignment_id") != assignment_id
            or result_payload.get("context_version") != context_version
            or result_payload.get("status") != "pass"
            or result_payload.get("work_unit_id") != upstream_id
            or result_payload.get("result_path") != expected_result_path
            or result_payload.get("assignment_sha256") != assignment_seal
            or result_payload.get("agent_type")
            != assignment_payload.get("agent_type")
            or result_payload.get("independence_mode")
            != assignment_payload.get("independence_mode")
            or any(
                result_payload.get(field) != assignment_payload.get(field)
                for field in (
                    "change_set_id",
                    "publication_group_id",
                    "workflow_role",
                )
            )
            or not isinstance(result_binding, Mapping)
            or dict(result_binding) != dict(assignment_binding)
            or result_payload.get("execution_evidence") != "self_declared"
            or result_payload.get("files_read_evidence") != "self_declared"
            or result_payload.get("launch_evidence")
            not in {"verified", "unverified"}
            or (
                result_payload.get("launch_evidence") == "unverified"
                and result_payload.get("launch_id") not in {None, ""}
            )
            or not isinstance(result_payload.get("files_read"), list)
            or not isinstance(result_payload.get("commands"), list)
            or not isinstance(result_payload.get("tool_versions"), Mapping)
            or result_payload.get("findings") != []
            or not claim_results_valid
            or result_payload.get("errors") != []
            or not isinstance(result_payload.get("started_at"), str)
            or not result_payload.get("started_at")
            or not isinstance(result_payload.get("completed_at"), str)
            or not result_payload.get("completed_at")
            or coverage_file is None
            or not isinstance(coverage_sha, str)
            or _RAW_SHA256_RE.fullmatch(coverage_sha) is None
            or _sha256_file(coverage_file) != coverage_sha
            or len(matching_coverage_artifacts) != 1
            or matching_coverage_artifacts[0].get("bytes")
            != coverage_file.stat().st_size
        ):
            raise BlindReplayContractError(
                "review result envelope contradicts the pass summary"
            )
        _validate_review_result_with_canonical_kernel(
            root=root,
            run_id=run_id,
            context_version=context_version,
            assignment_payload=assignment_payload,
            result_payload=result_payload,
            result_file=result_file,
            expected_result_path=expected_result_path,
        )
        _validate_review_coverage_receipt(
            coverage_file=coverage_file,
            run_id=run_id,
            assignment_id=assignment_id,
            assignment_payload=assignment_payload,
            candidate_binding=assignment_binding,
        )
    return review_file.relative_to(root).as_posix(), _sha256_file(review_file)


_STACKED_OPEN_HISTORY = (
    "PLANNED",
    "ACTIVE",
    "IMPLEMENTED",
    "VALIDATED",
    "REVIEWED",
    "SEALED",
    "PUSHED",
    "PR_OPEN",
)
_STACKED_OPEN_IDS = ("PR-283", "PR-284", "PR-285", "PR-286")
_STACKED_REQUIRED_PASS_GATES = (
    "eligibility",
    "implementation",
    "validation",
    "review",
    "seal",
    "push",
    "publication",
)


def _stacked_pr_open_activation_reasons(
    *,
    spec: Mapping[str, object],
    status: Mapping[str, object],
    resolutions: Mapping[str, object],
) -> tuple[dict[str, list[str]], list[str]] | None:
    """Validate the Phase-2 lifecycle authority without replaying stale reviews.

    Predecessor reviewer envelopes remain historical provenance after their
    candidate is sealed.  The current activation authority is instead the
    exact serial lifecycle, immutable sealed-head chain, current terminal
    receipts, and recorded PR_OPEN publication state.
    """

    activation = spec.get("activation_contract")
    if not isinstance(activation, Mapping):
        raise BlindReplayContractError("activation contract is missing")
    if activation.get("authority_mode") != "STACKED_PR_OPEN_EXACT_SEALED_HEAD":
        return None
    if (
        activation.get("required_predecessor_state") != "PR_OPEN"
        or activation.get("review_evidence_role")
        != "HISTORICAL_PROVENANCE_ONLY"
    ):
        raise BlindReplayContractError("stacked activation authority drifted")
    canonical_target = activation.get("canonical_target_sha")
    required_predecessor = activation.get("required_predecessor_sealed_sha")
    if (
        not isinstance(canonical_target, str)
        or _COMMIT_RE.fullmatch(canonical_target) is None
        or not isinstance(required_predecessor, str)
        or _COMMIT_RE.fullmatch(required_predecessor) is None
    ):
        raise BlindReplayContractError("stacked activation SHA authority is invalid")

    by_id = {pr_id: [] for pr_id in _STACKED_OPEN_IDS}
    global_reasons: list[str] = []
    stack = status.get("stacked_pr_execution")
    if not isinstance(stack, Mapping):
        return by_id, ["stacked PR execution authority is missing"]
    rows = stack.get("prs")
    if not isinstance(rows, Mapping):
        return by_id, ["stacked PR lifecycle rows are missing"]
    if stack.get("execution_mode") != "AUTO_STACKED_PR":
        global_reasons.append("stacked execution mode is not AUTO_STACKED_PR")
    if stack.get("merge_policy") not in (None, "HUMAN_ONLY"):
        global_reasons.append("stacked merge policy is not HUMAN_ONLY")
    if stack.get("target_sha") not in (None, canonical_target):
        global_reasons.append("stacked canonical target SHA drifted")
    order = stack.get("pr_order")
    if order is not None and (
        not isinstance(order, list)
        or tuple(order[:5]) != (*_STACKED_OPEN_IDS, "PR-287")
        or len(set(order)) != len(order)
    ):
        global_reasons.append("stacked PR order drifted")
    if stack.get("active_implementation_pr") != "PR-287":
        global_reasons.append("PR-287 is not the only active implementation")
    optional_active = stack.get("active_implementation_prs")
    if optional_active is not None and optional_active != ["PR-287"]:
        global_reasons.append("PR-287 is not the only active implementation")
    active_rows = [
        pr_id
        for pr_id, row in rows.items()
        if isinstance(row, Mapping) and row.get("lifecycle") == "ACTIVE"
    ]
    if active_rows != ["PR-287"]:
        global_reasons.append("PR-287 is not the only active implementation")

    previous_id: str | None = None
    previous_sha = canonical_target
    for pr_id in _STACKED_OPEN_IDS:
        row_reasons = by_id[pr_id]
        row = rows.get(pr_id)
        resolution = resolutions.get(pr_id)
        if not isinstance(row, Mapping):
            row_reasons.append(f"{pr_id}: stacked lifecycle row is missing")
            previous_id = pr_id
            previous_sha = ""
            continue
        if row.get("lifecycle") != "PR_OPEN" or tuple(
            row.get("lifecycle_history", ())
        ) != _STACKED_OPEN_HISTORY:
            row_reasons.append(f"{pr_id}: exact PR_OPEN lifecycle is not complete")
        sealed_head = row.get("sealed_head")
        if (
            not isinstance(sealed_head, str)
            or _COMMIT_RE.fullmatch(sealed_head) is None
        ):
            row_reasons.append(f"{pr_id}: sealed head is missing or invalid")
            sealed_head = ""
        if row.get("base_sha") != previous_sha:
            row_reasons.append(
                f"{pr_id}: base is not the exact predecessor sealed head"
            )
        if row.get("predecessor_pr") != previous_id or row.get(
            "predecessor_sealed_sha"
        ) != (None if previous_id is None else previous_sha):
            row_reasons.append(
                f"{pr_id}: predecessor is not the exact predecessor sealed head"
            )
        gates = row.get("gate_dispositions")
        if not isinstance(gates, Mapping):
            row_reasons.append(f"{pr_id}: gate dispositions are missing")
        else:
            for gate in _STACKED_REQUIRED_PASS_GATES:
                if gates.get(gate) != "PASS":
                    row_reasons.append(f"{pr_id}: {gate} gate is not PASS")
        pushed_ref = row.get("pushed_ref")
        pr_url = row.get("pr_url")
        if not isinstance(pushed_ref, str) or not pushed_ref.startswith(
            "refs/heads/"
        ):
            row_reasons.append(f"{pr_id}: pushed ref is missing")
        if not isinstance(pr_url, str) or not re.fullmatch(
            r"https://github\.com/[^/]+/[^/]+/pull/[1-9][0-9]*", pr_url
        ):
            row_reasons.append(f"{pr_id}: PR_OPEN URL is missing or invalid")
        if not isinstance(resolution, Mapping):
            row_reasons.append(f"{pr_id}: execution resolution is missing")
        elif (
            resolution.get("candidate_sha") != sealed_head
            or resolution.get("sealed_head") != sealed_head
            or resolution.get("pushed_ref") != pushed_ref
            or resolution.get("pr_url") != pr_url
        ):
            row_reasons.append(
                f"{pr_id}: sealed head or publication identity differs from resolution"
            )
        previous_id = pr_id
        previous_sha = sealed_head

    if previous_sha != required_predecessor:
        by_id["PR-286"].append(
            "PR-286: sealed head differs from required predecessor sealed head"
        )
    current = rows.get("PR-287")
    if not isinstance(current, Mapping) or (
        current.get("lifecycle") != "ACTIVE"
        or tuple(current.get("lifecycle_history", ())) != ("PLANNED", "ACTIVE")
        or current.get("base_sha") != required_predecessor
        or current.get("predecessor_pr") != "PR-286"
        or current.get("predecessor_sealed_sha") != required_predecessor
    ):
        global_reasons.append(
            "PR-287 activation is not based on the exact predecessor sealed head"
        )
    return by_id, global_reasons


@dataclass(frozen=True)
class DependencyPredecessorRow:
    upstream_id: str
    resolution: str | None
    candidate_sha: str | None
    status_receipt_path: str | None
    status_receipt_sha256: str | None
    review_receipt_path: str | None
    review_receipt_sha256: str | None
    terminal_receipt_path: str | None
    terminal_receipt_sha256: str | None
    required_terminal: str | None
    satisfied: bool
    reasons: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "upstream_id": self.upstream_id,
            "resolution": self.resolution,
            "candidate_sha": self.candidate_sha,
            "status_receipt_path": self.status_receipt_path,
            "status_receipt_sha256": self.status_receipt_sha256,
            "review_receipt_path": self.review_receipt_path,
            "review_receipt_sha256": self.review_receipt_sha256,
            "terminal_receipt_path": self.terminal_receipt_path,
            "terminal_receipt_sha256": self.terminal_receipt_sha256,
            "required_terminal": self.required_terminal,
            "satisfied": self.satisfied,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class DependencyActivationReceipt:
    status: DependencyActivationStatus
    terminal: str
    spec_content_id: str
    status_content_id: str
    predecessor_rows: tuple[DependencyPredecessorRow, ...]
    reasons: tuple[str, ...]
    _repository_root: Path = field(repr=False, compare=False)
    _spec_path: Path = field(repr=False, compare=False)
    _status_path: Path = field(repr=False, compare=False)
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _ACTIVATION_TOKEN:
            raise BlindReplayContractError(
                "DependencyActivationReceipt must be factory-derived"
            )
        if self.status is DependencyActivationStatus.ACTIVATED:
            if self.terminal != "ACTIVATED_PREDECESSOR_FINAL_SUCCESS":
                raise BlindReplayContractError("activated terminal drifted")
            if self.reasons or not all(row.satisfied for row in self.predecessor_rows):
                raise BlindReplayContractError("activated receipt contains failures")
        elif self.terminal != "BLOCKED_PREDECESSOR_FINAL_SUCCESS":
            raise BlindReplayContractError("blocked terminal drifted")
        object.__setattr__(
            self, "_identity_seal", canonical_json_sha256(self.as_payload())
        )

    @property
    def receipt_content_id(self) -> str:
        current = canonical_json_sha256(self.as_payload())
        if current != self._identity_seal:
            raise BlindReplayContractError("activation receipt identity drifted")
        return current

    def as_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_PR287_DEPENDENCY_ACTIVATION_V1",
            "status": self.status.value,
            "terminal": self.terminal,
            "spec_content_id": self.spec_content_id,
            "status_content_id": self.status_content_id,
            "predecessor_rows": [row.as_payload() for row in self.predecessor_rows],
            "reasons": list(self.reasons),
        }


def build_dependency_activation_receipt(
    *,
    spec_path: Path,
    status_path: Path,
    repository_root: Path,
) -> DependencyActivationReceipt:
    """Purely validate canonical dependency state before any execution side effect."""

    if repository_root.is_symlink():
        raise BlindReplayContractError("repository root must not be a symlink")
    root = repository_root.resolve(strict=True)
    spec_file = _declared_file_within(root, spec_path, "spec")
    status_file = _declared_file_within(root, status_path, "status")
    if spec_file.relative_to(root).as_posix() != _CANONICAL_SPEC_PATH:
        raise BlindReplayContractError("spec must use the canonical PR-287 path")
    if status_file.relative_to(root).as_posix() != _CANONICAL_STATUS_PATH:
        raise BlindReplayContractError("status must use the canonical handoff path")
    spec = _load_mapping(spec_file, "spec")
    status = _load_mapping(status_file, "status")
    contracts = spec.get("dependency_contracts")
    if not isinstance(contracts, list) or not contracts:
        raise BlindReplayContractError("spec dependency contracts are missing")
    completed = status.get("completed", [])
    resolutions = status.get("execution_resolutions", {})
    if not isinstance(completed, list) or not isinstance(resolutions, dict):
        raise BlindReplayContractError("canonical status structure is invalid")
    stacked_validation = _stacked_pr_open_activation_reasons(
        spec=spec,
        status=status,
        resolutions=resolutions,
    )
    stacked_reasons = stacked_validation[0] if stacked_validation is not None else {}
    stacked_global_reasons = (
        stacked_validation[1] if stacked_validation is not None else []
    )
    rows = []
    aggregate_reasons = list(stacked_global_reasons)
    seen = set()
    for raw_contract in contracts:
        if not isinstance(raw_contract, dict):
            raise BlindReplayContractError("dependency contract row is invalid")
        upstream = raw_contract.get("upstream_id")
        if not isinstance(upstream, str) or upstream in seen:
            raise BlindReplayContractError("dependency IDs must be unique strings")
        seen.add(upstream)
        reasons = []
        authority = _DEPENDENCY_AUTHORITY.get(upstream)
        if authority is None:
            raise BlindReplayContractError("dependency inventory contains an unregistered ID")
        for field in ("required_receipt", "required_terminal"):
            if raw_contract.get(field) != authority[field]:
                raise BlindReplayContractError(
                    f"{upstream}: canonical dependency {field} drifted"
                )
        resolution_row = resolutions.get(upstream)
        if not isinstance(resolution_row, dict):
            resolution_row = {}
            reasons.append(f"{upstream}: canonical execution resolution missing")
        required_resolution = raw_contract.get(
            "required_resolution", "COMPLETED_SUCCESS"
        )
        resolution = resolution_row.get("resolution")
        if upstream not in completed:
            reasons.append(f"{upstream}: not in canonical completed set")
        if resolution != required_resolution:
            reasons.append(f"{upstream}: required resolution is not satisfied")
        if resolution_row.get("success_dependency_satisfied") is not True:
            reasons.append(f"{upstream}: success dependency is not satisfied")
        candidate_sha = resolution_row.get("candidate_sha")
        if not isinstance(candidate_sha, str) or _COMMIT_RE.fullmatch(candidate_sha) is None:
            reasons.append(f"{upstream}: candidate SHA is missing or invalid")
            candidate_sha = None
        if resolution_row.get("observed_data_executed") is not False:
            reasons.append(f"{upstream}: observed-data boundary is not false")
        if resolution_row.get("public_use") is not False:
            reasons.append(f"{upstream}: public-use boundary is not false")
        reasons.extend(stacked_reasons.get(upstream, ()))

        status_receipt_path = resolution_row.get("receipt")
        status_receipt_sha = None
        if status_receipt_path is None:
            reasons.append(f"{upstream}: canonical status receipt missing")
        else:
            try:
                status_receipt = _regular_file_within(root, status_receipt_path)
                status_receipt_sha = _sha256_file(status_receipt)
            except BlindReplayContractError as exc:
                reasons.append(f"{upstream}: status receipt invalid: {exc}")

        review_receipt_path = resolution_row.get("review_receipt")
        review_receipt_sha = None
        if review_receipt_path is None:
            reasons.append(f"{upstream}: canonical review receipt missing")
        elif stacked_validation is not None:
            review_relative = Path(str(review_receipt_path))
            if (
                not isinstance(review_receipt_path, str)
                or review_relative.is_absolute()
                or ".." in review_relative.parts
                or review_relative.as_posix()
                != f".agent-harness/runs/{review_relative.parent.name}/RUN_SUMMARY.json"
            ):
                reasons.append(
                    f"{upstream}: historical review provenance path is invalid"
                )
            registered_review_sha = resolution_row.get("review_receipt_sha256")
            if registered_review_sha is not None:
                if (
                    not isinstance(registered_review_sha, str)
                    or _RAW_SHA256_RE.fullmatch(registered_review_sha) is None
                ):
                    reasons.append(
                        f"{upstream}: historical review provenance hash is invalid"
                    )
                else:
                    review_receipt_sha = registered_review_sha
        else:
            try:
                review_receipt_path, review_receipt_sha = _validate_review_receipt(
                    root=root,
                    path=review_receipt_path,
                    upstream_id=upstream,
                    candidate_sha=candidate_sha or "",
                )
            except BlindReplayContractError as exc:
                reasons.append(f"{upstream}: review receipt invalid: {exc}")

        terminal_receipt_path = raw_contract.get("required_receipt")
        required_terminal = raw_contract.get("required_terminal")
        terminal_receipt_sha = None
        terminal_payload = None
        if terminal_receipt_path is None:
            reasons.append(f"{upstream}: required terminal receipt not registered")
        else:
            try:
                terminal_receipt = _regular_file_within(root, terminal_receipt_path)
                terminal_receipt_sha = _sha256_file(terminal_receipt)
                if required_terminal is not None:
                    terminal_payload = _load_mapping(
                        terminal_receipt, f"{upstream} terminal receipt"
                    )
            except BlindReplayContractError as exc:
                reasons.append(f"{upstream}: terminal receipt invalid: {exc}")
        if required_terminal is not None:
            if not isinstance(required_terminal, str):
                reasons.append(f"{upstream}: required terminal is invalid")
            elif terminal_payload is not None and _value_at_path(
                terminal_payload, authority["terminal_path"]
            ) != required_terminal:
                reasons.append(
                    f"{upstream}: schema-defined terminal differs from the requirement"
                )
        satisfied = not reasons
        aggregate_reasons.extend(reasons)
        rows.append(
            DependencyPredecessorRow(
                upstream_id=upstream,
                resolution=resolution if isinstance(resolution, str) else None,
                candidate_sha=candidate_sha,
                status_receipt_path=(
                    status_receipt_path if isinstance(status_receipt_path, str) else None
                ),
                status_receipt_sha256=status_receipt_sha,
                review_receipt_path=(
                    review_receipt_path
                    if isinstance(review_receipt_path, str)
                    else None
                ),
                review_receipt_sha256=review_receipt_sha,
                terminal_receipt_path=(
                    terminal_receipt_path
                    if isinstance(terminal_receipt_path, str)
                    else None
                ),
                terminal_receipt_sha256=terminal_receipt_sha,
                required_terminal=(
                    required_terminal if isinstance(required_terminal, str) else None
                ),
                satisfied=satisfied,
                reasons=tuple(reasons),
            )
        )
    expected_ids = tuple(spec.get("dependencies", ()))
    if expected_ids != tuple(_DEPENDENCY_AUTHORITY):
        raise BlindReplayContractError("canonical dependency inventory drifted")
    if tuple(row.upstream_id for row in rows) != expected_ids:
        aggregate_reasons.append("dependency order differs from the frozen inventory")
    active = not aggregate_reasons and all(row.satisfied for row in rows)
    return DependencyActivationReceipt(
        status=(
            DependencyActivationStatus.ACTIVATED
            if active
            else DependencyActivationStatus.BLOCKED
        ),
        terminal=(
            "ACTIVATED_PREDECESSOR_FINAL_SUCCESS"
            if active
            else "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
        ),
        spec_content_id="sha256:" + _sha256_file(spec_file),
        status_content_id="sha256:" + _sha256_file(status_file),
        predecessor_rows=tuple(rows),
        reasons=tuple(aggregate_reasons),
        _repository_root=root,
        _spec_path=spec_file,
        _status_path=status_file,
        _construction_token=_ACTIVATION_TOKEN,
    )


def require_dependency_activation(
    receipt: DependencyActivationReceipt,
) -> DependencyActivationReceipt:
    if type(receipt) is not DependencyActivationReceipt:
        raise BlindReplayContractError("activation receipt must be factory-derived")
    receipt.receipt_content_id
    rebuilt = build_dependency_activation_receipt(
        spec_path=receipt._spec_path,
        status_path=receipt._status_path,
        repository_root=receipt._repository_root,
    )
    if rebuilt.as_payload() != receipt.as_payload():
        raise BlindReplayContractError("activation authority no longer matches canonical state")
    if receipt.status is not DependencyActivationStatus.ACTIVATED:
        raise BlindReplayContractError("BLOCKED_PREDECESSOR_FINAL_SUCCESS")
    if (
        receipt.terminal != "ACTIVATED_PREDECESSOR_FINAL_SUCCESS"
        or receipt.reasons
        or not receipt.predecessor_rows
        or not all(row.satisfied for row in receipt.predecessor_rows)
    ):
        raise BlindReplayContractError("activation receipt is not internally complete")
    return receipt


@dataclass(frozen=True)
class TypedScenarioBank:
    scenarios: tuple[Mapping[str, object], ...]
    case_assignments: tuple[Mapping[str, str], ...]
    case_inventory_content_id: str
    scenario_bank_content_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR287_TYPED_SCENARIO_BANK_V1",
            "scenarios": [_thaw(row) for row in self.scenarios],
            "case_assignments": [_thaw(row) for row in self.case_assignments],
            "case_inventory_content_id": self.case_inventory_content_id,
        }


def build_typed_scenario_bank(
    *,
    scenarios: Sequence[Mapping[str, object]],
    case_to_scenario: Mapping[str, str],
) -> TypedScenarioBank:
    if isinstance(scenarios, (str, bytes)) or not isinstance(scenarios, Sequence):
        raise BlindReplayContractError("scenario bank must be a sequence")
    frozen_rows = tuple(_freeze(row) for row in scenarios)
    if any(not isinstance(row, Mapping) for row in frozen_rows):
        raise BlindReplayContractError("scenario bank rows must be mappings")
    if tuple(row.get("scenario_id") for row in frozen_rows) != _SCENARIO_ORDER:
        raise BlindReplayContractError("scenario inventory or order drifted")
    for row in frozen_rows:
        if frozenset(row) != _SCENARIO_FIELDS:
            raise BlindReplayContractError("scenario effective field inventory drifted")
        scenario_id = str(row["scenario_id"])
        expected_estimand, expected_terminal = _SCENARIO_ESTIMANDS[scenario_id]
        if (
            row.get("estimand_id") != expected_estimand
            or row.get("expected_negative_control_terminal") != expected_terminal
            or row.get("analysis_unit") != "one_complete_synthetic_challenge_case"
            or row.get("seed_policy_id") != "PR287-CRYPTO-SEED-DERIVATION-V1"
            or row.get("hypothesis_family_id") != "PR287-HELDOUT-FAMILY-V1"
            or row.get("alpha") != 0.05
            or row.get("simultaneous_method") != "Holm-Bonferroni_FWER"
            or row.get("mc_precision_rule_id")
            != "PR287-EXACT-BINOMIAL-HALFWIDTH-004-V1"
            or row.get("replicate_or_exact_enumeration_rule")
            not in {"512_independent_replicates", "exact_finite_enumeration"}
        ):
            raise BlindReplayContractError("scenario statistical contract drifted")
        exact_cell_ids = row.get("exact_enumeration_cell_ids")
        if (
            isinstance(exact_cell_ids, (str, bytes))
            or not isinstance(exact_cell_ids, (list, tuple))
        ):
            raise BlindReplayContractError(
                "exact enumeration cell inventory is missing"
            )
        exact_cell_ids = tuple(exact_cell_ids)
        if row["replicate_or_exact_enumeration_rule"] == "exact_finite_enumeration":
            if (
                len(exact_cell_ids) < 2
                or any(not isinstance(cell_id, str) for cell_id in exact_cell_ids)
                or len(set(exact_cell_ids)) != len(exact_cell_ids)
            ):
                raise BlindReplayContractError(
                    "exact enumeration cell inventory is incomplete"
                )
            for cell_id in exact_cell_ids:
                _identity(cell_id, f"{scenario_id}.exact_enumeration_cell_id")
        elif exact_cell_ids:
            raise BlindReplayContractError(
                "replicate scenario carries exact enumeration cells"
            )
        expected_partition = (
            "development" if _SCENARIO_ORDER.index(scenario_id) < 4 else "held_out"
        )
        if row.get("partition") != expected_partition:
            raise BlindReplayContractError("scenario partition cardinality drifted")
        for field_name in (
            "data_generating_law_id",
            "covariance_generator_id",
            "covariance_analysis_id",
            "latent_draw_inventory_id",
            "acceptance_rule_id",
        ):
            _identity(row.get(field_name), f"{scenario_id}.{field_name}")
        if row["covariance_generator_id"] != covariance_matrix_content_id(
            row["covariance_generator_matrix"]
        ) or row["covariance_analysis_id"] != covariance_matrix_content_id(
            row["covariance_analysis_matrix"]
        ):
            raise BlindReplayContractError(
                "scenario covariance matrix/content identity linkage drifted"
            )

    if not isinstance(case_to_scenario, Mapping) or tuple(case_to_scenario) != _CASE_IDS:
        raise BlindReplayContractError("case/scenario mapping inventory drifted")
    if tuple(case_to_scenario.values()) != _SCENARIO_ORDER:
        raise BlindReplayContractError("case/scenario mapping is not a bijection")
    assignments = tuple(
        _freeze({"case_id": case_id, "scenario_id": case_to_scenario[case_id]})
        for case_id in _CASE_IDS
    )
    by_id = {str(row["scenario_id"]): row for row in frozen_rows}
    correct = by_id["COVARIANCE_CORRECT"]
    misspecified = by_id["COVARIANCE_MISSPECIFIED_PAIRED"]
    if (
        correct["covariance_generator_id"] != correct["covariance_analysis_id"]
        or correct["covariance_generator_matrix"]
        != correct["covariance_analysis_matrix"]
        or misspecified["covariance_generator_id"]
        != correct["covariance_generator_id"]
        or misspecified["covariance_generator_matrix"]
        != correct["covariance_generator_matrix"]
        or misspecified["covariance_analysis_id"]
        == misspecified["covariance_generator_id"]
        or misspecified["covariance_analysis_matrix"]
        == misspecified["covariance_generator_matrix"]
        or misspecified["latent_draw_inventory_id"]
        != correct["latent_draw_inventory_id"]
        or misspecified["data_generating_law_id"]
        != correct["data_generating_law_id"]
    ):
        raise BlindReplayContractError("paired covariance identity contract drifted")
    case_inventory_content_id = canonical_json_sha256(
        {
            "domain": "PR287_CASE_SCENARIO_BIJECTION_V1",
            "case_assignments": [_thaw(row) for row in assignments],
        }
    )
    unsigned = {
        "schema": "HTT_PR287_TYPED_SCENARIO_BANK_V1",
        "scenarios": [_thaw(row) for row in frozen_rows],
        "case_assignments": [_thaw(row) for row in assignments],
        "case_inventory_content_id": case_inventory_content_id,
    }
    return TypedScenarioBank(
        scenarios=frozen_rows,
        case_assignments=assignments,
        case_inventory_content_id=case_inventory_content_id,
        scenario_bank_content_id=canonical_json_sha256(unsigned),
    )


def validate_typed_scenario_bank(bank: TypedScenarioBank) -> TypedScenarioBank:
    if type(bank) is not TypedScenarioBank:
        raise BlindReplayContractError("scenario bank must be factory-derived")
    rebuilt = build_typed_scenario_bank(
        scenarios=bank.scenarios,
        case_to_scenario={
            str(row["case_id"]): str(row["scenario_id"])
            for row in bank.case_assignments
        },
    )
    if bank.unsigned_payload() != rebuilt.unsigned_payload() or (
        bank.scenario_bank_content_id != rebuilt.scenario_bank_content_id
    ):
        raise BlindReplayContractError("scenario bank content identity drifted")
    return bank


def _validate_public_challenge_cases(
    cases: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    frozen_cases = tuple(_freeze(row) for row in cases)
    if any(not isinstance(row, Mapping) for row in frozen_cases):
        raise BlindReplayContractError("challenge cases must be mappings")
    if tuple(row.get("case_id") for row in frozen_cases) != _CASE_IDS:
        raise BlindReplayContractError(
            "challenge case IDs must match the exact D01-D04/H01-H08 order"
        )
    for row in frozen_cases:
        if frozenset(row) != _CHALLENGE_CASE_FIELDS:
            raise BlindReplayContractError("challenge public case schema drifted")
        vector = row.get("observable_vector")
        if (
            isinstance(vector, (str, bytes))
            or not isinstance(vector, (list, tuple))
            or not vector
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in vector
            )
        ):
            raise BlindReplayContractError("challenge observable vector is invalid")
        _identity(row.get("covariance_id"), "covariance_id")
        _identity(row.get("mask_id"), "mask_id")
    return frozen_cases


@dataclass(frozen=True)
class FreshChallenge:
    activation_receipt_content_id: str
    challenge_config_content_id: str
    threshold_contract_content_id: str
    case_inventory_content_id: str
    scenario_bank_content_id: str
    seed_commitment_content_id: str
    cases: tuple[Mapping[str, object], ...]
    challenge_content_id: str
    _activation_receipt: DependencyActivationReceipt = field(
        repr=False, compare=False
    )
    _scenario_bank: TypedScenarioBank = field(repr=False, compare=False)
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CHALLENGE_TOKEN:
            raise BlindReplayContractError("FreshChallenge must be factory-derived")

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(str(row["case_id"]) for row in self.cases)

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_PR287_FRESH_CHALLENGE_V1",
            "activation_receipt_content_id": self.activation_receipt_content_id,
            "challenge_config_content_id": self.challenge_config_content_id,
            "threshold_contract_content_id": self.threshold_contract_content_id,
            "case_inventory_content_id": self.case_inventory_content_id,
            "scenario_bank_content_id": self.scenario_bank_content_id,
            "seed_commitment_content_id": self.seed_commitment_content_id,
            "cases": [_thaw(row) for row in self.cases],
        }

    def as_payload(self) -> dict[str, object]:
        return {
            **self.unsigned_payload(),
            "challenge_content_id": self.challenge_content_id,
        }


def build_fresh_challenge(
    *,
    activation_receipt: DependencyActivationReceipt,
    challenge_config_content_id: str,
    threshold_contract_content_id: str,
    seed_commitment_content_id: str,
    scenario_bank: TypedScenarioBank,
    cases: Sequence[Mapping[str, object]],
) -> FreshChallenge:
    require_dependency_activation(activation_receipt)
    validate_typed_scenario_bank(scenario_bank)
    identities = {
        "activation_receipt_content_id": activation_receipt.receipt_content_id,
        "challenge_config_content_id": _identity(
            challenge_config_content_id, "challenge_config_content_id"
        ),
        "threshold_contract_content_id": _identity(
            threshold_contract_content_id, "threshold_contract_content_id"
        ),
        "case_inventory_content_id": scenario_bank.case_inventory_content_id,
        "scenario_bank_content_id": scenario_bank.scenario_bank_content_id,
        "seed_commitment_content_id": _identity(
            seed_commitment_content_id, "seed_commitment_content_id"
        ),
    }
    frozen_cases = _validate_public_challenge_cases(cases)
    unsigned = {
        "schema": "COMMON_PR287_FRESH_CHALLENGE_V1",
        **identities,
        "cases": [_thaw(row) for row in frozen_cases],
    }
    return FreshChallenge(
        **identities,
        cases=frozen_cases,
        challenge_content_id=canonical_json_sha256(unsigned),
        _activation_receipt=activation_receipt,
        _scenario_bank=scenario_bank,
        _construction_token=_CHALLENGE_TOKEN,
    )


def validate_fresh_challenge(challenge: FreshChallenge) -> FreshChallenge:
    if type(challenge) is not FreshChallenge:
        raise BlindReplayContractError("challenge must be an exact FreshChallenge")
    require_dependency_activation(challenge._activation_receipt)
    validate_typed_scenario_bank(challenge._scenario_bank)
    if (
        challenge.activation_receipt_content_id
        != challenge._activation_receipt.receipt_content_id
        or challenge.scenario_bank_content_id
        != challenge._scenario_bank.scenario_bank_content_id
        or challenge.case_inventory_content_id
        != challenge._scenario_bank.case_inventory_content_id
    ):
        raise BlindReplayContractError("challenge activation authority drifted")
    _validate_public_challenge_cases(challenge.cases)
    for name in (
        "activation_receipt_content_id",
        "challenge_config_content_id",
        "threshold_contract_content_id",
        "case_inventory_content_id",
        "scenario_bank_content_id",
        "seed_commitment_content_id",
    ):
        _identity(getattr(challenge, name), name)
    if challenge.challenge_content_id != canonical_json_sha256(
        challenge.unsigned_payload()
    ):
        raise BlindReplayContractError("challenge content identity drifted")
    return challenge


@dataclass(frozen=True)
class CaseAnalysisResult:
    case_id: str
    supported_quotient: bool
    response_provider_available: bool
    local_response_rank: int
    global_response_rank: int
    joint_response_rank: int
    response_class_cardinality: int
    minimum_principal_angle: float | None
    weak_angle_threshold: float
    weak_identification: bool
    unknown_distance: float | None
    unknown_distance_threshold: float | None
    response_equivalence: bool
    margin_abstention: bool
    classifier_terminal: str
    depth_premise_status: str
    finite_depth_bound: float | None
    matched_mock_status: str
    covariance_status: str
    raw_p_value: float
    coverage_evidence_mode: str
    coverage_cell_results: tuple[int, ...]
    holm_adjusted_p_value: float | None
    scenario_bank_content_id: str
    covariance_generator_id: str
    covariance_analysis_id: str
    coverage_successes: int
    coverage_trials: int
    coverage_cell_results_content_id: str
    coverage_interval: tuple[float, float]
    coverage_status: str
    mc_interval_half_width: float
    mc_precision_status: str
    result_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SUBMISSION_TOKEN:
            raise BlindReplayContractError("CaseAnalysisResult must be factory-derived")

    def input_payload(self) -> dict[str, object]:
        return {
            field_name: getattr(self, field_name)
            for field_name in _CASE_ANALYSIS_INPUT_FIELDS
        }

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR287_CASE_ANALYSIS_RESULT_V1",
            **self.input_payload(),
            "scenario_bank_content_id": self.scenario_bank_content_id,
            "covariance_generator_id": self.covariance_generator_id,
            "covariance_analysis_id": self.covariance_analysis_id,
            "coverage_successes": self.coverage_successes,
            "coverage_trials": self.coverage_trials,
            "coverage_cell_results_content_id": (
                self.coverage_cell_results_content_id
            ),
            "classifier_terminal": self.classifier_terminal,
            "holm_adjusted_p_value": self.holm_adjusted_p_value,
            "coverage_interval": list(self.coverage_interval),
            "coverage_status": self.coverage_status,
            "mc_interval_half_width": self.mc_interval_half_width,
            "mc_precision_status": self.mc_precision_status,
        }

    def as_payload(self) -> dict[str, object]:
        return {**self.unsigned_payload(), "result_content_id": self.result_content_id}


def _finite_probability(value: object, field_name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not 0.0 <= float(value) <= 1.0
    ):
        raise BlindReplayContractError(f"{field_name} must be a finite probability")
    return float(value)


def _classifier_terminal(row: Mapping[str, object]) -> str:
    if row["supported_quotient"] is False:
        return "OUTSIDE_SUPPORTED_QUOTIENT"
    if row["response_provider_available"] is False:
        return "MISSING_RESPONSE_PROVIDER"
    local_rank = int(row["local_response_rank"])
    global_rank = int(row["global_response_rank"])
    joint_rank = int(row["joint_response_rank"])
    if (
        local_rank == 0
        or global_rank == 0
        or joint_rank < local_rank + global_rank
        or row["weak_identification"] is True
    ):
        return "TYPE_UNIDENTIFIED"
    distance = row["unknown_distance"]
    threshold = row["unknown_distance_threshold"]
    if distance is not None and threshold is not None and distance >= threshold:
        return "UNKNOWN_CLASS"
    if (
        row["response_equivalence"] is True
        or row["margin_abstention"] is True
        or int(row["response_class_cardinality"]) != 1
    ):
        return "RESPONSE_EQUIVALENCE_ABSTENTION"
    return "UNIQUE_RESPONSE_CLASS_CANDIDATE"


def _exact_binomial_interval(successes: int, trials: int) -> tuple[float, float]:
    lower = (
        0.0
        if successes == 0
        else float(beta_distribution.ppf(0.025, successes, trials - successes + 1))
    )
    upper = (
        1.0
        if successes == trials
        else float(beta_distribution.ppf(0.975, successes + 1, trials - successes))
    )
    return lower, upper


def build_registered_case_analysis_results(
    rows: Sequence[Mapping[str, object]],
    *,
    scenario_bank: TypedScenarioBank,
) -> tuple[CaseAnalysisResult, ...]:
    validate_typed_scenario_bank(scenario_bank)
    scenarios = {str(row["scenario_id"]): row for row in scenario_bank.scenarios}
    scenario_by_case = {
        str(row["case_id"]): scenarios[str(row["scenario_id"])]
        for row in scenario_bank.case_assignments
    }
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise BlindReplayContractError("case analysis inputs must be a sequence")
    raw_rows = tuple(rows)
    if tuple(row.get("case_id") if isinstance(row, Mapping) else None for row in raw_rows) != _CASE_IDS:
        raise BlindReplayContractError("case analysis inventory drifted")
    checked: list[dict[str, object]] = []
    for row in raw_rows:
        if not isinstance(row, Mapping) or frozenset(row) != _CASE_ANALYSIS_INPUT_FIELDS:
            raise BlindReplayContractError("case analysis input schema drifted")
        item = dict(row)
        for field_name in (
            "supported_quotient",
            "response_provider_available",
            "weak_identification",
            "response_equivalence",
            "margin_abstention",
        ):
            if type(item[field_name]) is not bool:
                raise BlindReplayContractError(f"{field_name} must be Boolean")
        for field_name in (
            "local_response_rank",
            "global_response_rank",
            "joint_response_rank",
            "response_class_cardinality",
        ):
            value = item[field_name]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise BlindReplayContractError(f"{field_name} must be a nonnegative integer")
        if item["joint_response_rank"] > (
            item["local_response_rank"] + item["global_response_rank"]
        ):
            raise BlindReplayContractError(
                "joint response rank exceeds the direct-sum dimension"
            )
        if item["joint_response_rank"] < max(
            item["local_response_rank"], item["global_response_rank"]
        ):
            raise BlindReplayContractError(
                "joint response rank is smaller than a component rank"
            )
        if item["response_class_cardinality"] == 0 and item["response_provider_available"]:
            raise BlindReplayContractError("available response provider has zero classes")
        angle = item["minimum_principal_angle"]
        if angle is not None and (
            isinstance(angle, bool)
            or not isinstance(angle, (int, float))
            or not math.isfinite(float(angle))
            or not 0.0 <= float(angle) <= math.pi / 2
        ):
            raise BlindReplayContractError("minimum principal angle is invalid")
        weak_threshold = item["weak_angle_threshold"]
        if (
            isinstance(weak_threshold, bool)
            or not isinstance(weak_threshold, (int, float))
            or not math.isfinite(float(weak_threshold))
            or not 0.0 <= float(weak_threshold) <= math.pi / 2
            or not math.isclose(float(weak_threshold), 0.2, rel_tol=0.0, abs_tol=0.0)
        ):
            raise BlindReplayContractError("weak-angle threshold drifted")
        zero_component_rank = (
            item["local_response_rank"] == 0
            or item["global_response_rank"] == 0
        )
        nontrivial_intersection = (
            not zero_component_rank
            and item["joint_response_rank"]
            < item["local_response_rank"] + item["global_response_rank"]
        )
        if zero_component_rank and angle is not None:
            raise BlindReplayContractError(
                "zero component rank requires an undefined principal angle"
            )
        if item["response_provider_available"] and not zero_component_rank and angle is None:
            raise BlindReplayContractError(
                "available response provider requires a principal angle"
            )
        if nontrivial_intersection and (
            angle is None or float(angle) != 0.0
        ):
            raise BlindReplayContractError(
                "rank intersection requires a zero principal angle"
            )
        if (
            not zero_component_rank
            and not nontrivial_intersection
            and angle is not None
            and float(angle) == 0.0
        ):
            raise BlindReplayContractError(
                "zero principal angle requires a rank intersection"
            )
        expected_weak = angle is None or float(angle) <= float(weak_threshold)
        if item["weak_identification"] is not expected_weak:
            raise BlindReplayContractError(
                "weak-identification flag contradicts the principal angle"
            )
        distance = item["unknown_distance"]
        threshold = item["unknown_distance_threshold"]
        if (distance is None) != (threshold is None):
            raise BlindReplayContractError("unknown distance and threshold must be paired")
        for field_name in ("unknown_distance", "unknown_distance_threshold"):
            value = item[field_name]
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) < 0
            ):
                raise BlindReplayContractError(f"{field_name} is invalid")
        premise = item["depth_premise_status"]
        bound = item["finite_depth_bound"]
        mocks = item["matched_mock_status"]
        if premise == "PROVED":
            _finite_probability(bound, "finite_depth_bound")
            if mocks != "NOT_REQUIRED":
                raise BlindReplayContractError("proved depth premise mock status drifted")
        elif premise == "MISSING":
            if bound is not None or mocks != "REQUIRED":
                raise BlindReplayContractError(
                    "missing depth premise requires unavailable bound and matched mocks"
                )
        else:
            raise BlindReplayContractError("depth premise status is unregistered")
        scenario = scenario_by_case[str(item["case_id"])]
        expected_covariance_status = (
            "MISSPECIFIED_NEGATIVE_CONTROL"
            if scenario["scenario_id"] == "COVARIANCE_MISSPECIFIED_PAIRED"
            else "REGISTERED_VALID"
        )
        if item["covariance_status"] != expected_covariance_status:
            raise BlindReplayContractError(
                "covariance status contradicts the registered scenario"
            )
        item["raw_p_value"] = _finite_probability(item["raw_p_value"], "raw_p_value")
        evidence_mode = item["coverage_evidence_mode"]
        if evidence_mode != scenario["replicate_or_exact_enumeration_rule"]:
            raise BlindReplayContractError(
                "coverage evidence mode contradicts the registered scenario"
            )
        cells = item["coverage_cell_results"]
        if (
            isinstance(cells, (str, bytes))
            or not isinstance(cells, Sequence)
            or not cells
            or any(type(value) not in {bool, int} or int(value) not in {0, 1} for value in cells)
        ):
            raise BlindReplayContractError("coverage raw cell evidence is invalid")
        frozen_cells = tuple(int(value) for value in cells)
        if evidence_mode == "512_independent_replicates" and len(frozen_cells) != 512:
            raise BlindReplayContractError(
                "coverage raw cells violate the 512-replicate contract"
            )
        if evidence_mode == "exact_finite_enumeration" and len(
            frozen_cells
        ) != len(scenario["exact_enumeration_cell_ids"]):
            raise BlindReplayContractError(
                "coverage raw cells do not exhaust the registered exact inventory"
            )
        if evidence_mode not in {
            "512_independent_replicates",
            "exact_finite_enumeration",
        }:
            raise BlindReplayContractError("coverage evidence mode is unregistered")
        item["coverage_cell_results"] = frozen_cells
        checked.append(item)

    held_out = checked[4:]
    ordered = sorted(
        enumerate(held_out), key=lambda pair: (pair[1]["raw_p_value"], pair[0])
    )
    holm = [0.0] * len(held_out)
    running = 0.0
    for rank, (original_index, row) in enumerate(ordered, start=1):
        adjusted = min(1.0, (len(held_out) - rank + 1) * row["raw_p_value"])
        running = max(running, adjusted)
        holm[original_index] = running

    results: list[CaseAnalysisResult] = []
    for index, row in enumerate(checked):
        cells = tuple(int(value) for value in row["coverage_cell_results"])
        successes = sum(cells)
        trials = len(cells)
        if row["coverage_evidence_mode"] == "exact_finite_enumeration":
            exact_fraction = successes / trials
            interval = (exact_fraction, exact_fraction)
            half_width = 0.0
            precision = "EXACT_FINITE_ENUMERATION"
        else:
            interval = _exact_binomial_interval(successes, trials)
            half_width = (interval[1] - interval[0]) / 2.0
            precision = (
                "SUFFICIENT"
                if half_width <= 0.04
                else "INCONCLUSIVE_MC_PRECISION"
            )
        coverage = (
            "INCONCLUSIVE_MC_PRECISION"
            if precision != "SUFFICIENT"
            and precision != "EXACT_FINITE_ENUMERATION"
            else (
                "TARGET_CONTAINED"
                if interval[0] <= 0.90 <= interval[1]
                else "TARGET_NOT_CONTAINED"
            )
        )
        terminal = _classifier_terminal(row)
        scenario = scenario_by_case[str(row["case_id"])]
        raw_cells_id = canonical_json_sha256(
            {
                "domain": "PR287_RAW_COVERAGE_CELLS_V1",
                "case_id": row["case_id"],
                "mode": row["coverage_evidence_mode"],
                "cells": list(cells),
            }
        )
        unsigned = {
            "schema": "HTT_PR287_CASE_ANALYSIS_RESULT_V1",
            **row,
            "scenario_bank_content_id": scenario_bank.scenario_bank_content_id,
            "covariance_generator_id": scenario["covariance_generator_id"],
            "covariance_analysis_id": scenario["covariance_analysis_id"],
            "coverage_successes": successes,
            "coverage_trials": trials,
            "coverage_cell_results_content_id": raw_cells_id,
            "classifier_terminal": terminal,
            "holm_adjusted_p_value": None if index < 4 else holm[index - 4],
            "coverage_interval": list(interval),
            "coverage_status": coverage,
            "mc_interval_half_width": half_width,
            "mc_precision_status": precision,
        }
        results.append(
            CaseAnalysisResult(
                **row,
                classifier_terminal=terminal,
                holm_adjusted_p_value=None if index < 4 else holm[index - 4],
                scenario_bank_content_id=scenario_bank.scenario_bank_content_id,
                covariance_generator_id=str(scenario["covariance_generator_id"]),
                covariance_analysis_id=str(scenario["covariance_analysis_id"]),
                coverage_successes=successes,
                coverage_trials=trials,
                coverage_cell_results_content_id=raw_cells_id,
                coverage_interval=interval,
                coverage_status=coverage,
                mc_interval_half_width=half_width,
                mc_precision_status=precision,
                result_content_id=canonical_json_sha256(unsigned),
                _construction_token=_SUBMISSION_TOKEN,
            )
        )
    return tuple(results)


def validate_registered_case_analysis_results(
    rows: Sequence[CaseAnalysisResult],
    *,
    scenario_bank: TypedScenarioBank,
) -> tuple[CaseAnalysisResult, ...]:
    if any(type(row) is not CaseAnalysisResult for row in rows):
        raise BlindReplayContractError("case results must be factory-derived")
    rebuilt = build_registered_case_analysis_results(
        tuple(row.input_payload() for row in rows),
        scenario_bank=scenario_bank,
    )
    if tuple(row.as_payload() for row in rows) != tuple(
        row.as_payload() for row in rebuilt
    ):
        raise BlindReplayContractError("case analysis result identity drifted")
    return tuple(rows)


@dataclass(frozen=True)
class FrozenSubmission:
    challenge_content_id: str
    challenge_config_content_id: str
    threshold_contract_content_id: str
    case_inventory_content_id: str
    case_results: tuple[CaseAnalysisResult, ...]
    submission_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SUBMISSION_TOKEN:
            raise BlindReplayContractError("FrozenSubmission must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR287_FROZEN_SUBMISSION_V1",
            "challenge_content_id": self.challenge_content_id,
            "challenge_config_content_id": self.challenge_config_content_id,
            "threshold_contract_content_id": self.threshold_contract_content_id,
            "case_inventory_content_id": self.case_inventory_content_id,
            "case_results": [row.as_payload() for row in self.case_results],
        }

    def as_payload(self) -> dict[str, object]:
        return {
            **self.unsigned_payload(),
            "submission_content_id": self.submission_content_id,
        }


def build_frozen_submission(
    *,
    challenge: FreshChallenge,
    case_results: Sequence[CaseAnalysisResult],
) -> FrozenSubmission:
    validate_fresh_challenge(challenge)
    frozen_results = validate_registered_case_analysis_results(
        case_results, scenario_bank=challenge._scenario_bank
    )
    if tuple(row.case_id for row in frozen_results) != challenge.case_ids:
        raise BlindReplayContractError(
            "submission case inventory differs from the challenge"
        )
    unsigned = {
        "schema": "HTT_PR287_FROZEN_SUBMISSION_V1",
        "challenge_content_id": challenge.challenge_content_id,
        "challenge_config_content_id": challenge.challenge_config_content_id,
        "threshold_contract_content_id": challenge.threshold_contract_content_id,
        "case_inventory_content_id": challenge.case_inventory_content_id,
        "case_results": [row.as_payload() for row in frozen_results],
    }
    return FrozenSubmission(
        challenge_content_id=challenge.challenge_content_id,
        challenge_config_content_id=challenge.challenge_config_content_id,
        threshold_contract_content_id=challenge.threshold_contract_content_id,
        case_inventory_content_id=challenge.case_inventory_content_id,
        case_results=frozen_results,
        submission_content_id=canonical_json_sha256(unsigned),
        _construction_token=_SUBMISSION_TOKEN,
    )


def validate_frozen_submission(
    submission: FrozenSubmission,
    *,
    challenge: FreshChallenge,
) -> FrozenSubmission:
    if type(submission) is not FrozenSubmission:
        raise BlindReplayContractError("submission must be an exact FrozenSubmission")
    validate_fresh_challenge(challenge)
    expected_bindings = (
        challenge.challenge_content_id,
        challenge.challenge_config_content_id,
        challenge.threshold_contract_content_id,
        challenge.case_inventory_content_id,
    )
    actual_bindings = (
        submission.challenge_content_id,
        submission.challenge_config_content_id,
        submission.threshold_contract_content_id,
        submission.case_inventory_content_id,
    )
    if actual_bindings != expected_bindings:
        raise BlindReplayContractError("submission challenge content identity drifted")
    validate_registered_case_analysis_results(
        submission.case_results, scenario_bank=challenge._scenario_bank
    )
    if tuple(row.case_id for row in submission.case_results) != challenge.case_ids:
        raise BlindReplayContractError("submission case inventory drifted")
    if submission.submission_content_id != canonical_json_sha256(
        submission.unsigned_payload()
    ):
        raise BlindReplayContractError("submission content identity drifted")
    return submission


@dataclass(frozen=True)
class TruthVaultReference:
    """Content-only capability reference; it intentionally contains no path or truth."""

    challenge_content_id: str
    seed_commitment_content_id: str
    case_inventory_content_id: str
    truth_vault_content_id: str
    reference_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _TRUTH_REFERENCE_TOKEN:
            raise BlindReplayContractError("TruthVaultReference must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_PR287_TRUTH_VAULT_REFERENCE_V1",
            "challenge_content_id": self.challenge_content_id,
            "seed_commitment_content_id": self.seed_commitment_content_id,
            "case_inventory_content_id": self.case_inventory_content_id,
            "truth_vault_content_id": self.truth_vault_content_id,
        }

    def as_payload(self) -> dict[str, object]:
        return {
            **self.unsigned_payload(),
            "reference_content_id": self.reference_content_id,
        }


def build_truth_vault_reference(
    *, challenge: FreshChallenge, truth_vault_content_id: str
) -> TruthVaultReference:
    validate_fresh_challenge(challenge)
    unsigned = {
        "schema": "COMMON_PR287_TRUTH_VAULT_REFERENCE_V1",
        "challenge_content_id": challenge.challenge_content_id,
        "seed_commitment_content_id": challenge.seed_commitment_content_id,
        "case_inventory_content_id": challenge.case_inventory_content_id,
        "truth_vault_content_id": _identity(
            truth_vault_content_id, "truth_vault_content_id"
        ),
    }
    return TruthVaultReference(
        challenge_content_id=challenge.challenge_content_id,
        seed_commitment_content_id=challenge.seed_commitment_content_id,
        case_inventory_content_id=challenge.case_inventory_content_id,
        truth_vault_content_id=unsigned["truth_vault_content_id"],
        reference_content_id=canonical_json_sha256(unsigned),
        _construction_token=_TRUTH_REFERENCE_TOKEN,
    )


def validate_truth_vault_reference(
    reference: TruthVaultReference, *, challenge: FreshChallenge
) -> TruthVaultReference:
    if type(reference) is not TruthVaultReference:
        raise BlindReplayContractError(
            "truth reference must be an exact TruthVaultReference"
        )
    validate_fresh_challenge(challenge)
    if (
        reference.challenge_content_id,
        reference.seed_commitment_content_id,
        reference.case_inventory_content_id,
    ) != (
        challenge.challenge_content_id,
        challenge.seed_commitment_content_id,
        challenge.case_inventory_content_id,
    ):
        raise BlindReplayContractError("truth reference challenge binding drifted")
    _identity(reference.truth_vault_content_id, "truth_vault_content_id")
    if reference.reference_content_id != canonical_json_sha256(
        reference.unsigned_payload()
    ):
        raise BlindReplayContractError("truth reference content identity drifted")
    return reference


@dataclass(frozen=True)
class SubmissionFreezeReceipt:
    challenge_content_id: str
    challenge_config_content_id: str
    threshold_contract_content_id: str
    case_inventory_content_id: str
    submission_content_id: str
    submission_frozen_at_utc: str
    source_commit_or_external_candidate_seal_id: str
    freeze_receipt_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _FREEZE_RECEIPT_TOKEN:
            raise BlindReplayContractError(
                "SubmissionFreezeReceipt must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "HTT_PR287_SUBMISSION_FREEZE_RECEIPT_V1",
            "challenge_content_id": self.challenge_content_id,
            "challenge_config_content_id": self.challenge_config_content_id,
            "threshold_contract_content_id": self.threshold_contract_content_id,
            "case_inventory_content_id": self.case_inventory_content_id,
            "submission_content_id": self.submission_content_id,
            "submission_frozen_at_utc": self.submission_frozen_at_utc,
            "source_commit_or_external_candidate_seal_id": (
                self.source_commit_or_external_candidate_seal_id
            ),
        }

    def as_payload(self) -> dict[str, object]:
        return {
            **self.unsigned_payload(),
            "freeze_receipt_content_id": self.freeze_receipt_content_id,
        }


def _source_identity(value: object) -> str:
    if not isinstance(value, str) or not (
        _COMMIT_RE.fullmatch(value) is not None
        or _SHA256_RE.fullmatch(value) is not None
    ):
        raise BlindReplayContractError(
            "source identity must be a commit or sha256 candidate-seal identity"
        )
    return value


def build_submission_freeze_receipt(
    *,
    challenge: FreshChallenge,
    submission: FrozenSubmission,
    submission_frozen_at_utc: str,
    source_commit_or_external_candidate_seal_id: str,
) -> SubmissionFreezeReceipt:
    validate_frozen_submission(submission, challenge=challenge)
    unsigned = {
        "schema": "HTT_PR287_SUBMISSION_FREEZE_RECEIPT_V1",
        "challenge_content_id": challenge.challenge_content_id,
        "challenge_config_content_id": challenge.challenge_config_content_id,
        "threshold_contract_content_id": challenge.threshold_contract_content_id,
        "case_inventory_content_id": challenge.case_inventory_content_id,
        "submission_content_id": submission.submission_content_id,
        "submission_frozen_at_utc": _utc_timestamp(
            submission_frozen_at_utc, "submission_frozen_at_utc"
        ),
        "source_commit_or_external_candidate_seal_id": _source_identity(
            source_commit_or_external_candidate_seal_id
        ),
    }
    return SubmissionFreezeReceipt(
        **{key: value for key, value in unsigned.items() if key != "schema"},
        freeze_receipt_content_id=canonical_json_sha256(unsigned),
        _construction_token=_FREEZE_RECEIPT_TOKEN,
    )


def validate_submission_freeze_receipt(
    receipt: SubmissionFreezeReceipt,
    *,
    challenge: FreshChallenge,
    submission: FrozenSubmission,
) -> SubmissionFreezeReceipt:
    if type(receipt) is not SubmissionFreezeReceipt:
        raise BlindReplayContractError(
            "freeze receipt must be an exact SubmissionFreezeReceipt"
        )
    validate_frozen_submission(submission, challenge=challenge)
    expected = (
        challenge.challenge_content_id,
        challenge.challenge_config_content_id,
        challenge.threshold_contract_content_id,
        challenge.case_inventory_content_id,
        submission.submission_content_id,
    )
    actual = (
        receipt.challenge_content_id,
        receipt.challenge_config_content_id,
        receipt.threshold_contract_content_id,
        receipt.case_inventory_content_id,
        receipt.submission_content_id,
    )
    if actual != expected:
        raise BlindReplayContractError("submission freeze binding drifted")
    _utc_timestamp(receipt.submission_frozen_at_utc, "submission_frozen_at_utc")
    _source_identity(receipt.source_commit_or_external_candidate_seal_id)
    if receipt.freeze_receipt_content_id != canonical_json_sha256(
        receipt.unsigned_payload()
    ):
        raise BlindReplayContractError("submission freeze content identity drifted")
    return receipt


@dataclass(frozen=True)
class HistoricalReplayReceipt:
    freeze_receipt_content_id: str
    submission_content_id: str
    historical_source_path: str
    historical_source_sha256: str
    historical_pack_content_id: str
    replay_command: str
    replay_exit_code: int
    legacy_reproduction_only: bool
    terminal: str
    receipt_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _HISTORICAL_RECEIPT_TOKEN:
            raise BlindReplayContractError(
                "HistoricalReplayReceipt must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_PR287_HISTORICAL_REPLAY_RECEIPT_V1",
            "freeze_receipt_content_id": self.freeze_receipt_content_id,
            "submission_content_id": self.submission_content_id,
            "historical_source_path": self.historical_source_path,
            "historical_source_sha256": self.historical_source_sha256,
            "historical_pack_content_id": self.historical_pack_content_id,
            "replay_command": self.replay_command,
            "replay_exit_code": self.replay_exit_code,
            "legacy_reproduction_only": self.legacy_reproduction_only,
            "terminal": self.terminal,
        }

    def as_payload(self) -> dict[str, object]:
        return {**self.unsigned_payload(), "receipt_content_id": self.receipt_content_id}


_HISTORICAL_REPLAY_COMMAND = (
    "python3 -B scripts/codex_harness/build_pr273_blind_synthetic.py --check"
)


def build_historical_replay_receipt(
    *,
    freeze_receipt: SubmissionFreezeReceipt,
    challenge: FreshChallenge,
    submission: FrozenSubmission,
    historical_source_path: str,
    repository_root: Path,
    replay_command: str,
    replay_exit_code: int,
) -> HistoricalReplayReceipt:
    validate_submission_freeze_receipt(
        freeze_receipt,
        challenge=challenge,
        submission=submission,
    )
    if replay_command != _HISTORICAL_REPLAY_COMMAND:
        raise BlindReplayContractError("historical replay command drifted")
    if isinstance(replay_exit_code, bool) or replay_exit_code != 0:
        raise BlindReplayContractError("historical exact replay did not pass")
    if repository_root.is_symlink():
        raise BlindReplayContractError("repository root must not be a symlink")
    root = repository_root.resolve(strict=True)
    source = _regular_file_within(root, historical_source_path)
    payload = _load_mapping(source, "historical PR-273 pack")
    if payload.get("schema") != "htt.pr273.blind_synthetic_diagnostic_pack.v1":
        raise BlindReplayContractError("historical PR-273 schema drifted")
    pack_content_id = _identity(payload.get("content_id"), "historical_pack_content_id")
    unsigned = {
        "schema": "COMMON_PR287_HISTORICAL_REPLAY_RECEIPT_V1",
        "freeze_receipt_content_id": freeze_receipt.freeze_receipt_content_id,
        "submission_content_id": submission.submission_content_id,
        "historical_source_path": historical_source_path,
        "historical_source_sha256": "sha256:" + _sha256_file(source),
        "historical_pack_content_id": pack_content_id,
        "replay_command": replay_command,
        "replay_exit_code": 0,
        "legacy_reproduction_only": True,
        "terminal": "PASS_EXACT_HISTORICAL_PR273_REPLAY",
    }
    return HistoricalReplayReceipt(
        **{key: value for key, value in unsigned.items() if key != "schema"},
        receipt_content_id=canonical_json_sha256(unsigned),
        _construction_token=_HISTORICAL_RECEIPT_TOKEN,
    )


def validate_historical_replay_receipt(
    receipt: HistoricalReplayReceipt,
    *,
    freeze_receipt: SubmissionFreezeReceipt,
    challenge: FreshChallenge,
    submission: FrozenSubmission,
    repository_root: Path,
) -> HistoricalReplayReceipt:
    if type(receipt) is not HistoricalReplayReceipt:
        raise BlindReplayContractError(
            "historical receipt must be an exact HistoricalReplayReceipt"
        )
    rebuilt = build_historical_replay_receipt(
        freeze_receipt=freeze_receipt,
        challenge=challenge,
        submission=submission,
        historical_source_path=receipt.historical_source_path,
        repository_root=repository_root,
        replay_command=receipt.replay_command,
        replay_exit_code=receipt.replay_exit_code,
    )
    if receipt.as_payload() != rebuilt.as_payload():
        raise BlindReplayContractError("historical replay receipt identity drifted")
    return receipt


@dataclass(frozen=True)
class PillarRowProjectionReceipt:
    pillar: str
    source_path: str
    source_file_sha256: str
    source_receipt_content_sha256: str
    source_terminal: str
    rows: tuple[Mapping[str, object], ...]
    terminal_counts: Mapping[str, int]
    projection_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PILLAR_PROJECTION_TOKEN:
            raise BlindReplayContractError(
                "PillarRowProjectionReceipt must be factory-derived"
            )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_PR287_PILLAR_ROW_PROJECTION_V1",
            "pillar": self.pillar,
            "source_path": self.source_path,
            "source_file_sha256": self.source_file_sha256,
            "source_receipt_content_sha256": self.source_receipt_content_sha256,
            "source_terminal": self.source_terminal,
            "rows": [_thaw(row) for row in self.rows],
            "terminal_counts": dict(self.terminal_counts),
        }

    def as_payload(self) -> dict[str, object]:
        return {
            **self.unsigned_payload(),
            "projection_content_id": self.projection_content_id,
        }


def _receipt_content_sha256(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("receipt_content_sha256", None)
    return canonical_json_sha256(unsigned).removeprefix("sha256:")


def _semantic_projection(row: Mapping[str, object]) -> Mapping[str, object]:
    unavailable = "UNAVAILABLE_NOT_RECORDED_BY_SOURCE_SCHEMA"
    source_identity = (
        row.get("source_replay_identity_sha256")
        or row.get("source_statement_identity_sha256")
        or unavailable
    )
    units = row.get("units_normalization_and_frame")
    if units is None:
        legacy_units = {
            key: row[key]
            for key in ("frame_convention", "branch_convention")
            if row.get(key) is not None
        }
        units = legacy_units or unavailable
    covariance_law_coverage = {
        key: row.get(key, unavailable)
        for key in (
            "sampling_law",
            "covariance_assumptions",
            "coverage_evidence",
        )
    }
    projected = {
        "row_id": row.get("row_id"),
        "source_statement_or_replay_identity": source_identity,
        "verdict": row.get("verdict"),
        "evidence_class": row.get(
            "evidence_class", row.get("proof_record_verdict", unavailable)
        ),
        "statement_relation": row.get("statement_relation", unavailable),
        "claim_ceiling": row.get("claim_ceiling", unavailable),
        "units_normalization_and_frame": units,
        "sign_orientation_convention": row.get(
            "sign_orientation_convention", unavailable
        ),
        "prior_applicability_and_identity": row.get(
            "prior_applicability_and_identity", unavailable
        ),
        "covariance_law_coverage_status": covariance_law_coverage,
        "rank_and_identification_scope": row.get(
            "rank_and_identification_scope", unavailable
        ),
        "singular_value_and_principal_angle_status": row.get(
            "singular_value_and_principal_angle_status", unavailable
        ),
        "row_semantic_content_id": canonical_json_sha256(row),
    }
    if not isinstance(projected["row_id"], str) or not isinstance(
        projected["verdict"], str
    ):
        raise BlindReplayContractError("pillar row lacks a typed ID or verdict")
    return _freeze(projected)


def build_pillar_row_projection(
    *, pillar: str, source_path: str, repository_root: Path
) -> PillarRowProjectionReceipt:
    if pillar not in {"T", "S"}:
        raise BlindReplayContractError("pillar must be exactly T or S")
    if repository_root.is_symlink():
        raise BlindReplayContractError("repository root must not be a symlink")
    root = repository_root.resolve(strict=True)
    authority = _PILLAR_AUTHORITY[pillar]
    if source_path != authority["path"]:
        raise BlindReplayContractError(f"Pillar {pillar} source path drifted")
    source = _regular_file_within(root, source_path)
    if _sha256_file(source) != authority["sha256"]:
        raise BlindReplayContractError(f"Pillar {pillar} frozen source bytes drifted")
    payload = _load_mapping(source, f"Pillar {pillar} receipt")
    expected_terminal = f"PASS_COMPLETE_PILLAR_{pillar}_ADJUDICATION"
    if payload.get("terminal") != expected_terminal:
        raise BlindReplayContractError(f"Pillar {pillar} source terminal drifted")
    embedded = payload.get("receipt_content_sha256")
    if not isinstance(embedded, str) or embedded != _receipt_content_sha256(payload):
        raise BlindReplayContractError(f"Pillar {pillar} receipt identity drifted")
    raw_rows = payload.get("rows")
    expected_count = 80 if pillar == "T" else 72
    if not isinstance(raw_rows, list) or len(raw_rows) != expected_count:
        raise BlindReplayContractError(f"Pillar {pillar} row inventory drifted")
    if any(not isinstance(row, Mapping) for row in raw_rows):
        raise BlindReplayContractError(f"Pillar {pillar} contains a malformed row")
    row_ids = tuple(row.get("row_id") for row in raw_rows)
    if any(not isinstance(row_id, str) for row_id in row_ids) or len(set(row_ids)) != len(
        row_ids
    ):
        raise BlindReplayContractError(f"Pillar {pillar} row IDs drifted")
    rows = tuple(_semantic_projection(row) for row in raw_rows)
    allowed_terminals = {
        "PASS",
        "FAIL",
        "INCONCLUSIVE_WITH_RECEIPT",
        "BLOCKED_WITH_RECEIPT",
    }
    counts = {terminal: 0 for terminal in sorted(allowed_terminals)}
    for row in rows:
        verdict = row["verdict"]
        if verdict not in allowed_terminals:
            raise BlindReplayContractError(
                f"Pillar {pillar} contains an unregistered row verdict"
            )
        counts[str(verdict)] += 1
    source_counts = payload.get("summary", {}).get("terminal_counts")
    if source_counts != counts:
        raise BlindReplayContractError(f"Pillar {pillar} terminal counts drifted")
    if pillar == "T" and (counts["FAIL"] != 1 or counts["BLOCKED_WITH_RECEIPT"] != 1):
        raise BlindReplayContractError("Pillar T failed/blocked rows were laundered")
    if pillar == "S" and (
        counts["FAIL"] != 0 or counts["BLOCKED_WITH_RECEIPT"] != 1
    ):
        raise BlindReplayContractError("Pillar S blocked row was laundered")
    unsigned = {
        "schema": "COMMON_PR287_PILLAR_ROW_PROJECTION_V1",
        "pillar": pillar,
        "source_path": source_path,
        "source_file_sha256": "sha256:" + _sha256_file(source),
        "source_receipt_content_sha256": "sha256:" + embedded,
        "source_terminal": expected_terminal,
        "rows": [_thaw(row) for row in rows],
        "terminal_counts": counts,
    }
    return PillarRowProjectionReceipt(
        pillar=pillar,
        source_path=source_path,
        source_file_sha256=unsigned["source_file_sha256"],
        source_receipt_content_sha256=unsigned["source_receipt_content_sha256"],
        source_terminal=expected_terminal,
        rows=rows,
        terminal_counts=MappingProxyType(counts),
        projection_content_id=canonical_json_sha256(unsigned),
        _construction_token=_PILLAR_PROJECTION_TOKEN,
    )


def validate_pillar_row_projection(
    receipt: PillarRowProjectionReceipt, *, repository_root: Path
) -> PillarRowProjectionReceipt:
    if type(receipt) is not PillarRowProjectionReceipt:
        raise BlindReplayContractError(
            "projection must be an exact PillarRowProjectionReceipt"
        )
    rebuilt = build_pillar_row_projection(
        pillar=receipt.pillar,
        source_path=receipt.source_path,
        repository_root=repository_root,
    )
    if (
        receipt.projection_content_id != canonical_json_sha256(receipt.unsigned_payload())
        or receipt.as_payload() != rebuilt.as_payload()
    ):
        raise BlindReplayContractError("pillar row projection identity drifted")
    return receipt


@dataclass(frozen=True)
class DiagnosticPack:
    kind: BlindReplayPackKind
    owner: str
    factory_module: str
    factory_provenance: Mapping[str, str]
    metadata: Mapping[str, object]
    surfaces: Mapping[str, Mapping[str, object]]
    pack_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DIAGNOSTIC_PACK_TOKEN:
            raise BlindReplayContractError("DiagnosticPack must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": f"{self.owner}_PR287_{self.kind.value}_V1",
            "kind": self.kind.value,
            "owner": self.owner,
            "factory_module": self.factory_module,
            "factory_provenance": _thaw(self.factory_provenance),
            "metadata": _thaw(self.metadata),
            "surfaces": _thaw(self.surfaces),
        }

    def as_payload(self) -> dict[str, object]:
        return {**self.unsigned_payload(), "pack_content_id": self.pack_content_id}


def _nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise BlindReplayContractError(f"{field} must be nonempty trimmed text")
    return value


def _nonempty_text_sequence(value: object, field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise BlindReplayContractError(f"{field} must be a nonempty text sequence")
    result = tuple(_nonempty_text(item, field) for item in value)
    if not result:
        raise BlindReplayContractError(f"{field} must be a nonempty text sequence")
    return result


def diagnostic_surface_content_id(
    surface_name: str, payload: Mapping[str, object]
) -> str:
    if not isinstance(payload, Mapping):
        raise BlindReplayContractError("diagnostic surface must be a mapping")
    unsigned = dict(payload)
    unsigned.pop("content_id", None)
    return canonical_json_sha256(
        {
            "domain": "PR287_DIAGNOSTIC_SURFACE_V1",
            "surface_name": surface_name,
            "payload": unsigned,
        }
    )


def _scan_surface_forbidden(value: object, path: str) -> None:
    fragments = (
        "likelihood",
        "posterior",
        "bayes",
        "evidence",
        "truth",
        "detected_geometry",
        "geometry_detected",
    )
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in _PACK_FORBIDDEN_KEYS or any(
                fragment in normalized for fragment in fragments
            ):
                raise BlindReplayContractError(
                    f"forbidden diagnostic surface field {key!r} at {path}"
                )
            _scan_surface_forbidden(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _scan_surface_forbidden(item, f"{path}[{index}]")


_RUNTIME_FORBIDDEN_CLAIM_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\b(?:we )?(?:detected|identified) (?:a |the )?bianchi "
        r"(?:geometry|geometries|family|families)\b",
        r"\b(?:the )?bianchi (?:geometry|geometries|family|families)"
        r"(?: (?:was|were|is|are|has been|have been))? "
        r"(?:detected|identified)\b",
        r"\b(?:detected|identified) (?:a |the )?"
        r"(?:geometry|geometries|family|families) as bianchi\b",
        r"\bnative (?:bianchi )?solver results?\b",
        r"\b(?:mio (?:model )?posterior|posterior from mio)\b",
        r"\bmodel independent truth certificate\b",
        r"\btsc full solver\b",
        r"\bteff full (?:polarisation|polarization) closure\b",
        r"\bexternal transfer validated as native\b",
    )
)


def _runtime_claim_match_is_negated(
    text: str, match: re.Match[str]
) -> bool:
    before = text[max(0, match.start() - 80) : match.start()].rstrip()
    after = text[match.end() : match.end() + 80].lstrip()
    return bool(
        re.search(
            r"(?:\bno|\bwithout|\bnever|\bcannot|\bdoes not claim|"
            r"\bdid not claim|\bis not a|\bare not)\s*$",
            before,
        )
        or re.match(
            r"(?:was|were|is|are|has been|have been)?\s*not\b|"
            r"(?:remains?|is|are|was|were)\s+blocked\b|"
            r"(?:was|were|is|are)\s+forbidden\b|"
            r"(?:was|were|is|are)\s+unavailable\b",
            after,
        )
    )


def _scan_runtime_claim_values(value: object, path: str) -> None:
    if isinstance(value, str):
        normalized = " ".join(
            value.lower().replace("_", " ").replace("-", " ").split()
        )
        for pattern in _RUNTIME_FORBIDDEN_CLAIM_PATTERNS:
            for match in pattern.finditer(normalized):
                if not _runtime_claim_match_is_negated(normalized, match):
                    raise BlindReplayContractError(
                        f"forbidden runtime claim language at {path}"
                    )
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _scan_runtime_claim_values(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _scan_runtime_claim_values(item, f"{path}[{index}]")


def _finite_number(value: object, field_name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise BlindReplayContractError(f"{field_name} must be finite numeric")
    return float(value)


def _validate_surface_semantics(name: str, value: Mapping[str, object]) -> None:
    if name == "x_phi":
        _nonempty_text(value.get("units_normalization_and_frame"), f"{name}.units")
        _nonempty_text(value.get("sign_orientation_convention"), f"{name}.sign")
        _finite_number(value.get("value"), f"{name}.value")
    elif name == "Q_phi":
        _nonempty_text(value.get("policy_id"), f"{name}.policy_id")
        _identity(value.get("denominator_identity"), f"{name}.denominator_identity")
        zero_status = value.get("zero_denominator_status")
        if zero_status == "NONZERO":
            _finite_number(value.get("value"), f"{name}.value")
        elif zero_status == "ZERO_UNDEFINED":
            if value.get("value") is not None:
                raise BlindReplayContractError("Q_phi zero denominator must suppress value")
        else:
            raise BlindReplayContractError("Q_phi zero denominator status drifted")
    elif name == "Pi_phi_of_q":
        _finite_number(value.get("q_threshold"), f"{name}.q_threshold")
        if value.get("comparison_rule") != "greater_than_or_equal":
            raise BlindReplayContractError("Pi comparison rule drifted")
        _identity(value.get("denominator_identity"), f"{name}.denominator_identity")
        _finite_probability(value.get("value"), f"{name}.value")
    elif name == "F_phi_certified":
        _identity(value.get("ceiling_identity"), f"{name}.ceiling_identity")
        sign_clean = value.get("sign_clean_status")
        admissible = value.get("admissibility_status")
        if sign_clean == "PASS" and admissible == "ADMISSIBLE":
            _finite_probability(value.get("value"), f"{name}.value")
        elif sign_clean == "FAIL" and admissible == "INADMISSIBLE":
            if value.get("value") is not None:
                raise BlindReplayContractError(
                    "F value requires sign-clean admissibility"
                )
        else:
            raise BlindReplayContractError("F status state is unregistered")
    elif name == "G_F":
        for field_name in (
            "ordered_depth_bin_identity",
            "path_identity",
            "covariance_id",
        ):
            _identity(value.get(field_name), f"{name}.{field_name}")
        if value.get("null_status") != "REGISTERED_SYNTHETIC_NULL":
            if value.get("value") is not None:
                raise BlindReplayContractError("G_F value requires registered null")
        else:
            _finite_number(value.get("value"), f"{name}.value")
    elif name == "rank":
        ranks = []
        for field_name in (
            "local_response_rank",
            "global_response_rank",
            "joint_response_rank",
        ):
            item = value.get(field_name)
            if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                raise BlindReplayContractError(f"{name}.{field_name} is invalid")
            ranks.append(item)
        if ranks[2] > ranks[0] + ranks[1]:
            raise BlindReplayContractError(
                "joint rank exceeds the direct-sum dimension"
            )
        if ranks[2] < max(ranks[0], ranks[1]):
            raise BlindReplayContractError(
                "joint rank is smaller than a component rank"
            )
        expected = (
            "TYPE_UNIDENTIFIED"
            if ranks[0] == 0 or ranks[1] == 0 or ranks[2] < ranks[0] + ranks[1]
            else "RANK_SEPARABLE_CANDIDATE"
        )
        if value.get("identification_status") != expected:
            raise BlindReplayContractError("rank identification status drifted")
    elif name == "principal_angles":
        raw_angle = value.get("minimum_principal_angle")
        threshold = _finite_number(value.get("weak_threshold"), "weak threshold")
        if not 0.0 <= threshold <= math.pi / 2 or threshold != 0.2:
            raise BlindReplayContractError("principal-angle weak threshold drifted")
        if raw_angle is None:
            expected = "NOT_DEFINED_ZERO_RANK"
        else:
            angle = _finite_number(raw_angle, "minimum angle")
            if not 0.0 <= angle <= math.pi / 2:
                raise BlindReplayContractError("minimum principal angle is invalid")
            expected = (
                "WEAKLY_IDENTIFIED"
                if angle <= threshold
                else "SEPARABLE_CANDIDATE"
            )
        if value.get("weak_identification_status") != expected:
            raise BlindReplayContractError("principal-angle weak status drifted")
    elif name == "covariance_status":
        generator_id = _identity(
            value.get("generator_covariance_id"), "generator covariance"
        )
        analysis_id = _identity(
            value.get("analysis_covariance_id"), "analysis covariance"
        )
        expected = (
            "REGISTERED_VALID"
            if generator_id == analysis_id
            else "MISSPECIFIED_NEGATIVE_CONTROL"
        )
        if value.get("covariance_status") != expected:
            raise BlindReplayContractError(
                "covariance status contradicts generator/analysis identities"
            )
    elif name == "weak_identification":
        if value.get("classifier_terminal") not in {
            "TYPE_UNIDENTIFIED",
            "UNKNOWN_CLASS",
            "RESPONSE_EQUIVALENCE_ABSTENTION",
            "UNIQUE_RESPONSE_CLASS_CANDIDATE",
        }:
            raise BlindReplayContractError("weak-identification terminal drifted")
        _identity(value.get("precedence_rule_id"), "precedence_rule_id")
        if type(value.get("response_equivalence")) is not bool or type(
            value.get("margin_abstention")
        ) is not bool:
            raise BlindReplayContractError(
                "response-equivalence evidence must be Boolean"
            )
    elif name == "abstention":
        distance = _finite_number(value.get("unknown_distance"), "unknown distance")
        threshold = _finite_number(value.get("unknown_threshold"), "unknown threshold")
        expected = "UNKNOWN_CLASS" if distance >= threshold else "WITHIN_REGISTERED_SUPPORT"
        if value.get("abstention_status") != expected:
            raise BlindReplayContractError("open-set abstention status drifted")
    elif name == "depth_calibration":
        premise = value.get("premise_status")
        if premise == "PROVED":
            _finite_probability(value.get("finite_bound"), "finite_bound")
            if value.get("matched_mock_status") != "NOT_REQUIRED":
                raise BlindReplayContractError("depth matched-mock status drifted")
        elif premise == "MISSING":
            if value.get("finite_bound") is not None or value.get("matched_mock_status") != "REQUIRED":
                raise BlindReplayContractError("missing depth premise emitted a bound")
        else:
            raise BlindReplayContractError("depth premise status drifted")
    elif name == "coverage":
        if (
            value.get("hypothesis_family_id") != "PR287-HELDOUT-FAMILY-V1"
            or value.get("simultaneous_method") != "Holm-Bonferroni_FWER"
            or value.get("coverage_status")
            not in {
                "TARGET_CONTAINED",
                "TARGET_NOT_CONTAINED",
                "INCONCLUSIVE_MC_PRECISION",
            }
            or value.get("mc_precision_status")
            not in {
                "SUFFICIENT",
                "INCONCLUSIVE_MC_PRECISION",
                "EXACT_FINITE_ENUMERATION",
            }
        ):
            raise BlindReplayContractError("coverage/multiplicity semantics drifted")
    elif name in {"direction_coherence", "depth_coherence"}:
        fields = (
            ("direction_frame", "covariance_id")
            if name == "direction_coherence"
            else ("ordered_depth_bin_identity", "path_identity", "covariance_id")
        )
        for field_name in fields:
            if field_name.endswith("_id") or field_name.endswith("identity"):
                _identity(value.get(field_name), f"{name}.{field_name}")
            else:
                _nonempty_text(value.get(field_name), f"{name}.{field_name}")
        _nonempty_text(value.get("null_status"), f"{name}.null_status")


def _validate_pack_metadata(
    kind: BlindReplayPackKind,
    metadata: Mapping[str, object],
    surfaces: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    if not isinstance(metadata, Mapping) or not _PACK_SHARED_METADATA.issubset(metadata):
        raise BlindReplayContractError("pack shared metadata is incomplete")
    owner = _PACK_OWNER[kind]
    exact_boundaries = {
        "owner": owner,
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "synthetic_diagnostic",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "scientific_status_effect": "OPEN_UNCHANGED",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "pr151_partial_data_excluded": True,
        "likelihood_semantics": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
        "prior_applicability_and_identity": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
    }
    if any(metadata.get(key) != value for key, value in exact_boundaries.items()):
        raise BlindReplayContractError("pack claim boundary drifted")
    for field in (
        "scope",
        "synthetic_sky_mask_status",
        "covariance_and_null_status",
        "units_normalization_and_frame",
        "sign_orientation_convention",
        "generating_procedure",
    ):
        _nonempty_text(metadata.get(field), field)
    _identity(metadata.get("evidence_lane_identity"), "evidence_lane_identity")
    _source_identity(metadata.get("git_commit_or_worktree_state"))
    _nonempty_text_sequence(metadata.get("assumptions"), "assumptions")
    _nonempty_text_sequence(metadata.get("caveats"), "caveats")
    inputs = metadata.get("config_and_input_identities")
    if not isinstance(inputs, Mapping) or frozenset(inputs) != _PACK_INPUT_IDENTITIES:
        raise BlindReplayContractError("pack input identity inventory drifted")
    for key, value in inputs.items():
        _identity(value, str(key))
    seed_status = metadata.get("seed_commitment_and_disclosure_status")
    if not isinstance(seed_status, Mapping) or frozenset(seed_status) != {
        "seed_commitment_content_id",
        "disclosure_status",
    }:
        raise BlindReplayContractError("seed commitment/disclosure metadata drifted")
    _identity(
        seed_status.get("seed_commitment_content_id"),
        "seed_commitment_content_id",
    )
    if seed_status.get("disclosure_status") != "DISCLOSED_AFTER_SUBMISSION_FREEZE":
        raise BlindReplayContractError("seed disclosure chronology drifted")
    semantic_ids = metadata.get("surface_semantic_content_ids")
    if not isinstance(semantic_ids, Mapping) or tuple(semantic_ids) != tuple(surfaces):
        raise BlindReplayContractError("surface semantic identity inventory drifted")
    for name, surface in surfaces.items():
        if semantic_ids.get(name) != surface.get("content_id"):
            raise BlindReplayContractError("surface semantic content identity drifted")
    _scan_forbidden(metadata, _PACK_FORBIDDEN_KEYS, "metadata")
    _scan_runtime_claim_values(metadata, "metadata")
    return _freeze(metadata)


def _validate_pack_surfaces(
    kind: BlindReplayPackKind, surfaces: Mapping[str, object]
) -> Mapping[str, Mapping[str, object]]:
    required = _PACK_REQUIRED_SURFACES[kind]
    if not isinstance(surfaces, Mapping) or tuple(surfaces) != required:
        raise BlindReplayContractError("pack surface inventory or order drifted")
    frozen: dict[str, Mapping[str, object]] = {}
    for name, value in surfaces.items():
        if isinstance(value, Mapping):
            _scan_surface_forbidden(value, f"surfaces.{name}")
            _scan_runtime_claim_values(value, f"surfaces.{name}")
        expected_fields = _SURFACE_BASE_FIELDS | _SURFACE_SEMANTIC_FIELDS.get(
            name, frozenset()
        )
        if not isinstance(value, Mapping) or frozenset(value) != expected_fields:
            raise BlindReplayContractError(f"surface {name} metadata is incomplete")
        expected_subject = _PACK_OWNER[kind]
        if kind is BlindReplayPackKind.PACK_A:
            if name in {"x_phi", "Q_phi", "Pi_phi_of_q", "F_phi_certified", "G_F"}:
                expected_subject = "MIO"
            elif name in {"SectorStress", "support_utilization"}:
                expected_subject = "OBSSTAT"
            else:
                expected_subject = "COMMON"
        if value.get("subject_owner") != expected_subject:
            raise BlindReplayContractError(f"surface {name} owner drifted")
        _nonempty_text(value.get("schema_id"), f"{name}.schema_id")
        _identity(value.get("content_id"), f"{name}.content_id")
        if value.get("content_id") != diagnostic_surface_content_id(name, value):
            raise BlindReplayContractError(f"surface {name} content identity drifted")
        _nonempty_text(value.get("status"), f"{name}.status")
        _nonempty_text_sequence(value.get("allowed_use"), f"{name}.allowed_use")
        _nonempty_text_sequence(value.get("forbidden_use"), f"{name}.forbidden_use")
        _validate_surface_semantics(name, value)
        frozen[name] = _freeze(value)
    if kind is BlindReplayPackKind.PACK_B:
        ranks = (
            frozen["rank"]["local_response_rank"],
            frozen["rank"]["global_response_rank"],
            frozen["rank"]["joint_response_rank"],
        )
        rank_status = frozen["rank"]["identification_status"]
        angle = frozen["principal_angles"]["minimum_principal_angle"]
        angle_status = frozen["principal_angles"]["weak_identification_status"]
        abstention_status = frozen["abstention"]["abstention_status"]
        zero_component_rank = ranks[0] == 0 or ranks[1] == 0
        intersection = not zero_component_rank and ranks[2] < ranks[0] + ranks[1]
        if (
            (zero_component_rank and angle is not None)
            or (
                not zero_component_rank
                and angle is None
            )
            or (intersection and angle != 0.0)
            or (
                not zero_component_rank
                and not intersection
                and angle == 0.0
            )
        ):
            raise BlindReplayContractError(
                "Pack B rank/principal-angle geometry contradiction"
            )
        equivalence = (
            frozen["weak_identification"]["response_equivalence"]
            or frozen["weak_identification"]["margin_abstention"]
        )
        expected_terminal = (
            "TYPE_UNIDENTIFIED"
            if rank_status == "TYPE_UNIDENTIFIED"
            or angle_status == "WEAKLY_IDENTIFIED"
            else (
                "UNKNOWN_CLASS"
                if abstention_status == "UNKNOWN_CLASS"
                else (
                    "RESPONSE_EQUIVALENCE_ABSTENTION"
                    if equivalence
                    else "UNIQUE_RESPONSE_CLASS_CANDIDATE"
                )
            )
        )
        if frozen["weak_identification"]["classifier_terminal"] != expected_terminal:
            raise BlindReplayContractError(
                "Pack B rank/angle/open-set precedence contradiction"
            )
    return MappingProxyType(frozen)


def _owner_factory_provenance(
    *, kind: BlindReplayPackKind, factory_module: str
) -> tuple[Callable[..., object], Mapping[str, str]]:
    root = _repository_root_from_source()
    relative = _PACK_FACTORY_PATH[kind]
    expected = _regular_file_within(root, relative)
    module = importlib.import_module(factory_module)
    module_file = getattr(module, "__file__", None)
    module_spec = getattr(module, "__spec__", None)
    spec_origin = getattr(module_spec, "origin", None)
    loader_path = getattr(getattr(module_spec, "loader", None), "path", None)
    factory_name = _PACK_FACTORY_NAME[kind]
    factory = getattr(module, factory_name, None)
    code = getattr(factory, "__code__", None)
    if (
        not isinstance(module_file, str)
        or not module_file
        or Path(module_file).resolve() != expected
        or not isinstance(spec_origin, str)
        or not spec_origin
        or Path(spec_origin).resolve() != expected
        or not isinstance(loader_path, str)
        or not loader_path
        or Path(loader_path).resolve() != expected
        or not callable(factory)
        or getattr(factory, "__module__", None) != factory_module
        or code is None
        or Path(str(code.co_filename)).resolve() != expected
    ):
        raise BlindReplayContractError("owner factory provenance drifted")
    provenance = MappingProxyType(
        {
            "module": factory_module,
            "factory_name": factory_name,
            "source_path": relative,
            "source_sha256": _sha256_file(expected),
        }
    )
    return factory, provenance


def _issue_diagnostic_pack(
    *,
    kind: BlindReplayPackKind,
    factory_module: str,
    metadata: Mapping[str, object],
    surfaces: Mapping[str, object],
) -> DiagnosticPack:
    if type(kind) is not BlindReplayPackKind:
        raise BlindReplayContractError("pack kind must be a registered enum")
    if factory_module != _PACK_FACTORY_MODULE[kind]:
        raise BlindReplayContractError("owner factory module substitution detected")
    expected_factory, factory_provenance = _owner_factory_provenance(
        kind=kind, factory_module=factory_module
    )
    caller = inspect.currentframe().f_back
    if (
        not callable(expected_factory)
        or caller is None
        or caller.f_code is not expected_factory.__code__
        or caller.f_globals is not expected_factory.__globals__
    ):
        raise BlindReplayContractError("owner factory call-site substitution detected")
    frozen_surfaces = _validate_pack_surfaces(kind, surfaces)
    frozen_metadata = _validate_pack_metadata(kind, metadata, frozen_surfaces)
    owner = _PACK_OWNER[kind]
    unsigned = {
        "schema": f"{owner}_PR287_{kind.value}_V1",
        "kind": kind.value,
        "owner": owner,
        "factory_module": factory_module,
        "factory_provenance": _thaw(factory_provenance),
        "metadata": _thaw(frozen_metadata),
        "surfaces": _thaw(frozen_surfaces),
    }
    return DiagnosticPack(
        kind=kind,
        owner=owner,
        factory_module=factory_module,
        factory_provenance=factory_provenance,
        metadata=frozen_metadata,
        surfaces=frozen_surfaces,
        pack_content_id=canonical_json_sha256(unsigned),
        _construction_token=_DIAGNOSTIC_PACK_TOKEN,
    )


def build_common_pack_a(
    *, metadata: Mapping[str, object], surfaces: Mapping[str, object]
) -> DiagnosticPack:
    return _issue_diagnostic_pack(
        kind=BlindReplayPackKind.PACK_A,
        factory_module="common.post275_blind_replay",
        metadata=metadata,
        surfaces=surfaces,
    )


def validate_diagnostic_pack(pack: DiagnosticPack) -> DiagnosticPack:
    if type(pack) is not DiagnosticPack:
        raise BlindReplayContractError("pack must be an exact DiagnosticPack")
    if pack.factory_module != _PACK_FACTORY_MODULE.get(pack.kind):
        raise BlindReplayContractError("owner factory module substitution detected")
    _, expected_provenance = _owner_factory_provenance(
        kind=pack.kind, factory_module=pack.factory_module
    )
    if dict(pack.factory_provenance) != dict(expected_provenance):
        raise BlindReplayContractError("owner factory provenance drifted")
    frozen_surfaces = _validate_pack_surfaces(pack.kind, pack.surfaces)
    frozen_metadata = _validate_pack_metadata(
        pack.kind, pack.metadata, frozen_surfaces
    )
    unsigned = {
        "schema": f"{pack.owner}_PR287_{pack.kind.value}_V1",
        "kind": pack.kind.value,
        "owner": pack.owner,
        "factory_module": pack.factory_module,
        "factory_provenance": _thaw(expected_provenance),
        "metadata": _thaw(frozen_metadata),
        "surfaces": _thaw(frozen_surfaces),
    }
    if (
        pack.owner != _PACK_OWNER[pack.kind]
        or pack.unsigned_payload() != unsigned
        or pack.pack_content_id != canonical_json_sha256(unsigned)
    ):
        raise BlindReplayContractError("diagnostic pack identity drifted")
    return pack


@dataclass(frozen=True)
class StageTraceRow:
    stage_id: BlindReplayStage
    input_content_ids: Mapping[str, str]
    output_content_ids: Mapping[str, str]
    status: str
    started_at_utc: str
    completed_at_utc: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _STAGE_ROW_TOKEN:
            raise BlindReplayContractError("StageTraceRow must be factory-derived")

    def as_payload(self) -> dict[str, object]:
        return {
            "stage_id": self.stage_id.value,
            "input_content_ids": dict(self.input_content_ids),
            "output_content_ids": dict(self.output_content_ids),
            "status": self.status,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
        }


@dataclass(frozen=True)
class StageTrace:
    rows: tuple[StageTraceRow, ...]
    trace_content_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _STAGE_TRACE_TOKEN:
            raise BlindReplayContractError("StageTrace must be factory-derived")

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_PR287_STAGE_TRACE_V1",
            "rows": [row.as_payload() for row in self.rows],
        }

    def as_payload(self) -> dict[str, object]:
        return {**self.unsigned_payload(), "trace_content_id": self.trace_content_id}


def _build_stage_row(
    payload: Mapping[str, object], expected_stage: BlindReplayStage
) -> StageTraceRow:
    if not isinstance(payload, Mapping):
        raise BlindReplayContractError("stage trace rows must be mappings")
    try:
        stage = BlindReplayStage(payload.get("stage_id"))
    except (TypeError, ValueError) as exc:
        raise BlindReplayContractError("stage trace contains an unknown stage") from exc
    if stage is not expected_stage:
        raise BlindReplayContractError("stage trace differs from the exact stage order")
    inputs = payload.get("input_content_ids")
    outputs = payload.get("output_content_ids")
    if not isinstance(inputs, Mapping) or not isinstance(outputs, Mapping):
        raise BlindReplayContractError("stage content identities must be mappings")
    expected_inputs, expected_outputs = _STAGE_LAYOUT[stage]
    if frozenset(inputs) != expected_inputs or frozenset(outputs) != expected_outputs:
        raise BlindReplayContractError(
            f"{stage.value} has missing, duplicate, or unregistered content identities"
        )
    frozen_inputs = MappingProxyType(
        {str(key): _identity(value, str(key)) for key, value in inputs.items()}
    )
    frozen_outputs = MappingProxyType(
        {str(key): _identity(value, str(key)) for key, value in outputs.items()}
    )
    if payload.get("status") != "COMPLETED":
        raise BlindReplayContractError("successful stage trace rows must be COMPLETED")
    started = _utc_timestamp(payload.get("started_at_utc"), "started_at_utc")
    completed = _utc_timestamp(payload.get("completed_at_utc"), "completed_at_utc")
    if datetime.fromisoformat(started[:-1] + "+00:00") > datetime.fromisoformat(
        completed[:-1] + "+00:00"
    ):
        raise BlindReplayContractError("stage completion precedes its start")
    return StageTraceRow(
        stage_id=stage,
        input_content_ids=frozen_inputs,
        output_content_ids=frozen_outputs,
        status="COMPLETED",
        started_at_utc=started,
        completed_at_utc=completed,
        _construction_token=_STAGE_ROW_TOKEN,
    )


def _require_link(
    left: Mapping[str, str], left_key: str, right: Mapping[str, str], right_key: str
) -> None:
    if left[left_key] != right[right_key]:
        raise BlindReplayContractError(
            f"stage trace identity linkage drifted for {right_key}"
        )


def build_stage_trace(rows: Sequence[Mapping[str, object]]) -> StageTrace:
    if (
        isinstance(rows, (str, bytes))
        or not isinstance(rows, Sequence)
        or len(rows) != len(BlindReplayStage)
    ):
        raise BlindReplayContractError("stage trace must contain every exact stage once")
    built = tuple(
        _build_stage_row(payload, expected)
        for payload, expected in zip(rows, BlindReplayStage, strict=True)
    )
    for earlier, later in zip(built, built[1:]):
        earlier_completed = datetime.fromisoformat(
            earlier.completed_at_utc[:-1] + "+00:00"
        )
        later_started = datetime.fromisoformat(later.started_at_utc[:-1] + "+00:00")
        if later_started < earlier_completed:
            raise BlindReplayContractError("stage trace chronology is reordered")

    freeze, design, analysis, adjudication, historical = built
    _require_link(
        freeze.output_content_ids,
        "dependency_activation_receipt_content_id",
        design.input_content_ids,
        "dependency_activation_receipt_content_id",
    )
    for key in ("challenge_config_content_id", "threshold_contract_content_id"):
        _require_link(design.input_content_ids, key, analysis.input_content_ids, key)
    _require_link(
        design.output_content_ids,
        "challenge_content_id",
        analysis.input_content_ids,
        "challenge_content_id",
    )
    _require_link(
        design.output_content_ids,
        "challenge_content_id",
        adjudication.input_content_ids,
        "challenge_content_id",
    )
    _require_link(
        design.output_content_ids,
        "truth_vault_content_id",
        adjudication.input_content_ids,
        "truth_vault_content_id",
    )
    _require_link(
        design.input_content_ids,
        "threshold_contract_content_id",
        adjudication.input_content_ids,
        "threshold_contract_content_id",
    )
    _require_link(
        analysis.output_content_ids,
        "submission_content_id",
        adjudication.input_content_ids,
        "submission_content_id",
    )
    _require_link(
        analysis.output_content_ids,
        "submission_content_id",
        historical.input_content_ids,
        "submission_content_id",
    )
    unsigned = {
        "schema": "COMMON_PR287_STAGE_TRACE_V1",
        "rows": [row.as_payload() for row in built],
    }
    return StageTrace(
        rows=built,
        trace_content_id=canonical_json_sha256(unsigned),
        _construction_token=_STAGE_TRACE_TOKEN,
    )


def validate_stage_trace(trace: StageTrace) -> StageTrace:
    if type(trace) is not StageTrace:
        raise BlindReplayContractError("trace must be an exact StageTrace")
    rebuilt = build_stage_trace(tuple(row.as_payload() for row in trace.rows))
    if rebuilt.trace_content_id != trace.trace_content_id:
        raise BlindReplayContractError("stage trace content identity drifted")
    return trace


__all__ = [
    "BlindReplayContractError",
    "BlindReplayPackKind",
    "BlindReplayStage",
    "CaseAnalysisResult",
    "DependencyActivationReceipt",
    "DependencyActivationStatus",
    "DependencyPredecessorRow",
    "DiagnosticPack",
    "FreshChallenge",
    "FrozenSubmission",
    "HistoricalReplayReceipt",
    "PillarRowProjectionReceipt",
    "StageTrace",
    "StageTraceRow",
    "SubmissionFreezeReceipt",
    "TruthVaultReference",
    "TypedScenarioBank",
    "build_common_pack_a",
    "build_dependency_activation_receipt",
    "build_fresh_challenge",
    "build_frozen_submission",
    "build_historical_replay_receipt",
    "build_pillar_row_projection",
    "build_registered_case_analysis_results",
    "build_stage_trace",
    "build_submission_freeze_receipt",
    "build_truth_vault_reference",
    "build_typed_scenario_bank",
    "canonical_json_sha256",
    "covariance_matrix_content_id",
    "diagnostic_surface_content_id",
    "require_dependency_activation",
    "validate_diagnostic_pack",
    "validate_fresh_challenge",
    "validate_frozen_submission",
    "validate_historical_replay_receipt",
    "validate_pillar_row_projection",
    "validate_registered_case_analysis_results",
    "validate_stage_trace",
    "validate_submission_freeze_receipt",
    "validate_truth_vault_reference",
    "validate_typed_scenario_bank",
]
