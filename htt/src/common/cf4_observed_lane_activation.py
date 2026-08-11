"""Fail-closed CF4 observed-lane preactivation for PR-291.

The decision layer reads only repository control artifacts.  It deliberately
has no OBSSTAT import and no CF4 catalogue path or reader.  A predecessor
success receipt, exact PR-289 identity admission, a separately provisioned
external HMAC-bound H-CF4 receipt, and a complete numerical operator are
non-substitutable gates.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
import hashlib
from pathlib import Path
import re
from typing import Mapping, Sequence

from common.observed_lane_activation import (
    ObservedLaneActivationError,
    _normalize_digest,
    _optional_regular_file_within,
    _parse_utc,
    _regular_file_within,
    _repository_root,
    _sha256_file,
    _strict_json,
    _load_pr289_identity_module,
    _validate_pr289_receipt_provenance,
    _yaml_mapping,
    canonical_json_bytes,
)


SCHEMA_VERSION = "common.cf4_observed_lane_activation.v1"
NONEXECUTION_RECEIPT_SCHEMA = "htt.pr291.cf4_nonexecution_receipt.v1"
HUMAN_AUTHORIZATION_SCHEMA = "common.human_execution_authorization.v1"

_SPEC_REL = Path("docs/research_program/post_pr275/pr291_spec.yaml")
_POLICY_REL = Path("docs/research_program/post_pr275/pr291_publication_policy.json")
_STATUS_REL = Path("docs/codex_handoff/pr_status.yaml")
_IDENTITY_REL = Path("docs/generated/pr289_data_identity_v2_receipt.json")
_PR289_REGISTRY_REL = Path(
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
_PR287_REL = Path("docs/generated/pr287_fresh_blind_typed_replay_receipt.json")
_AUTH_REL = Path(
    "docs/research_program/post_pr275/data_runs/cf4/"
    "H_CF4_EXECUTION_AUTHORIZATION.json"
)
_PR289_REQUIRED_SOURCE_PATHS = (
    "docs/harness/CLAIM_LEDGER.md",
    _PR289_REGISTRY_REL.as_posix(),
    "docs/research_program/post_pr275/data_runbooks.yaml",
    "docs/research_program/post_pr275/pr289_publication_policy.json",
    "docs/research_program/post_pr275/pr289_spec.yaml",
    "docs/research_program/vector_tensor/data_admission/PR274_ADMISSION_RESULT.json",
    "docs/research_program/vector_tensor/data_admission/PR274_DATA_IDENTITY_REGISTRY.yaml",
    "htt/src/common/data_identity.py",
    "scripts/codex_harness/run_pr289_data_identity_v2.py",
    "tests/contracts/test_data_identity_registry_v2.py",
)
_EXPECTED_REGISTRY_CONTENT_ID = (
    "sha256:78e3ec41833db433b560ebf839e0ee9375f77879a629e4ce70900bfb959bbef0"
)
_EXPECTED_PR289_RECEIPT_CONTENT_ID = (
    "sha256:4e2aa483abfa1c63777bad1b678058ae17a6e7108ad43475176367b634b8f74e"
)
_EXPECTED_CF4_COMPONENTS = (
    "catalogue",
    "row_selection",
    "covariance",
    "frame_definition",
    "sign_convention",
    "units_contract",
    "grouping_definition",
    "depth_definition",
    "zoa_definition",
)
_EXPECTED_PREDECESSORS = ("PR-201", "PR-287", "PR-289")
_EXPECTED_REQUIRED_TERMINALS = {
    "PR-287": "PASS_FRESH_BLIND_TYPED_REPLAY",
    "PR-289": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
}
_EXPECTED_RECEIPTS = {
    "PR-287": (
        _PR287_REL,
        "HTT_PR287_FRESH_BLIND_TYPED_REPLAY_RECEIPT_V1",
        None,
    ),
    "PR-289": (
        _IDENTITY_REL,
        "common.data_identity_v2_preflight_receipt.v1",
        _EXPECTED_PR289_RECEIPT_CONTENT_ID,
    ),
}
_EXPECTED_IDENTITY_FIELDS = (
    "pipeline_id",
    "catalogue_product_id",
    "grouping_id",
    "row_identity_id",
    "selection_id",
    "coordinate_frame_id",
    "sign_orientation_convention_id",
    "distance_scale_id",
    "velocity_estimator_id",
    "estimand_id",
    "depth_path_id",
    "zone_of_avoidance_mask_id",
    "covariance_id",
    "nuisance_box_id",
    "response_id",
    "units_id",
    "feature_order_id",
    "null_or_matched_mock_id",
)
_EXPECTED_ESTIMAND_ORDER = (
    "release_row_group_selection_identity",
    "distance_velocity_frame_and_sign_conventions",
    "radial_monopole_plus_bulk_and_shear_design",
    "full_joint_covariance_and_finite_rank_check",
    "depth_and_zone_of_avoidance_nested_support_path",
    "orbit_invariant_and_eigenspace_drift",
    "shared_nuisance_structural_identified_set",
    "registered_weak_identification_abstention",
    "matched_mock_or_proved_path_calibration",
    "source_separation_unidentified_directions",
    "legacy_projection_without_p0_rescue",
)
_EXPECTED_ADMISSION_SHORTCUTS = (
    "catalogue_name_or_release_label_only",
    "symlink_hardlink_or_root_alias",
    "grouping_without_exact_row_and_selection_identity",
    "covariance_label_without_exact_component_identity",
    "frame_sign_or_units_label_without_exact_component_identity",
    "grouping_depth_or_zoa_label_without_exact_component_identity",
    "admission_inferred_as_execution_authorization",
)
_EXPECTED_READINESS = {
    "exact_admitted_catalogue": "BLOCKED_DATA_IDENTITY_ADMISSION",
    "full_covariance": "BLOCKED_ADMITTED_COVARIANCE_UNAVAILABLE",
    "shared_nuisance_identified_set": "SYNTHETIC_OPERATOR_CONTRACT_ONLY",
    "depth_zoa_path": "SYNTHETIC_OPERATOR_CONTRACT_ONLY",
    "orbit_and_eigenspace_drift": "SYNTHETIC_OPERATOR_CONTRACT_ONLY",
    "local_global_rank": "NOT_MEASURED",
}
_EXPECTED_SYNTHETIC_FIXTURE = {
    "fixture_id": "PR291-SYNTHETIC-CF4-TYPED-PIPELINE-V1",
    "purpose": "shape_units_rank_covariance_depth_and_abstention_tests_only",
    "cannot_support": [
        "observed_number",
        "p_value",
        "anomaly",
        "global_tilt",
        "public_figure",
    ],
}
_EXPECTED_CURRENT_ALLOWED_OUTPUTS = (
    "preactivation_nonexecution_receipt",
    "synthetic_operator_test_evidence",
)
_EXPECTED_CURRENT_FORBIDDEN_OUTPUTS = (
    "observed_monopole_bulk_or_shear",
    "observed_covariance_or_significance",
    "observed_depth_zoa_path",
    "observed_orbit_or_eigenspace_drift",
    "observed_identified_set_or_endpoint",
    "p0_or_velocity_shape_rescue",
    "claim_bearing_figure",
)
_EXPECTED_OUTPUT_CONTAINMENT = {
    "preflight_before_payload_generation": True,
    "existing_parents_must_be_regular_directories": True,
    "receipt_must_be_regular_single_link_or_absent": True,
    "symlink_hardlink_nonregular_and_escape_refused": True,
    "same_directory_temporary_then_atomic_replace": True,
    "observed_result_directory_must_remain_absent_while_blocked": True,
}
_EXPECTED_FUTURE_METADATA = (
    "artifact_owner",
    "scope",
    "claim_tier",
    "claim_level",
    "scientific_artifact_mode",
    "transfer_source",
    "observed_data_executed",
    "public_use",
    "family_identification_gate",
    "scientific_status_effect",
    "allowed_uses",
    "forbidden_uses",
    "exact_admitted_record_ids",
    "lane_admission_bundle_id",
    "human_authorization_receipt_sha256",
    "catalogue_product_id",
    "grouping_id",
    "row_identity_id",
    "selection_id",
    "coordinate_frame_id",
    "sign_orientation_convention_id",
    "distance_scale_id",
    "velocity_estimator_id",
    "estimand_id",
    "units_id",
    "covariance_id",
    "covariance_status",
    "sky_support_status",
    "null_mock_status",
    "depth_path_id",
    "zone_of_avoidance_mask_id",
    "nuisance_box_id",
    "response_id",
    "feature_order_id",
    "null_or_matched_mock_id",
    "generating_procedure",
    "source_bindings",
    "git_commit_or_external_candidate_seal_id",
    "worktree_state",
    "caveats",
    "receipt_content_sha256",
)
_EXPECTED_FUTURE_STATUS_VALUE_CONTRACT = {
    "sky_support_status": {
        "allowed_values": ["VALIDATED_REGISTERED_SKY_SUPPORT"],
        "missing_unknown_or_not_evaluated": "REJECT",
    },
    "null_mock_status": {
        "allowed_values": ["VALIDATED_REGISTERED_NULL_OR_MATCHED_MOCK"],
        "missing_unknown_or_not_evaluated": "REJECT",
    },
}
_EXPECTED_FIXED_FIREWALL = {
    "artifact_owner": "OBSSTAT",
    "claim_tier": "diagnostic_only",
    "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
    "scientific_artifact_mode": "observed_data_conditional",
    "transfer_source": "none",
    "observed_data_executed": True,
    "public_use": False,
    "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    "scientific_status_effect": "OPEN_UNCHANGED",
}
_EXPECTED_FUTURE_CONTENT_BINDING_RULE = (
    "receipt_content_sha256 must equal SHA-256 over the complete unsigned "
    "result payload, including predecessor receipt identities, admitted "
    "record and bundle identities, authorization identity, and all source "
    "bindings."
)
_EXPECTED_TERMINALS = (
    "BLOCKED_CONTRACT_INVALID",
    "BLOCKED_PREDECESSOR_FINAL_SUCCESS",
    "BLOCKED_DATA_IDENTITY_ADMISSION",
    "BLOCKED_HUMAN_EXECUTION_AUTHORIZATION",
    "BLOCKED_OPERATOR_IMPLEMENTATION",
    "READY_FOR_ATTENDED_CF4_EXECUTION",
    "PASS_CF4_OBSERVED_LANE_REBOOT",
)
_EXPECTED_ALLOWED_USES = (
    "typed CF4 operator composition on explicitly synthetic fixtures",
    "fail-closed dependency identity and authorization preflight",
    "future attended execution planning after distinct admission and H-CF4 authorization",
)
_EXPECTED_FORBIDDEN_USES = (
    "automatic observed execution",
    "P0 or velocity-shape headline use is forbidden",
    "diagonal covariance or favourable-endpoint shortcut",
    "physical-vorticity or global-tilt claim from the WF curl diagnostic",
    "potential-flow claim from the WF curl diagnostic",
    "native solver or transfer validation",
    "anisotropy source or Bianchi-family identification",
    "public or manuscript claim from preactivation evidence",
)
_EXPECTED_OWNERSHIP = {
    "delivery_orchestration": "HTT",
    "observable_velocity_features_covariance_and_null_features": "OBSSTAT",
    "activation_manifests_provenance_and_semantic_guards": "COMMON",
    "model_dependent_likelihood_posterior_evidence": (
        "HTT_NOT_EXECUTED_BY_PREACTIVATION"
    ),
    "mio_diagnostic_crosscheck": "NOT_AN_ACTIVE_PR291_ESTIMAND",
    "tsc_teff": "LEGACY_ONLY",
}
_EXPECTED_MUTATIONS = frozenset(
    {
        "MU291-DEPENDENCY-SUBSTITUTION",
        "MU291-ADMISSION-AS-AUTHORIZATION",
        "MU291-REGISTRY-SOURCE-FORGERY",
        "MU291-GATE-ID-ALIAS",
        "MU291-GROUP-ROW-SELECTION-COLLAPSE",
        "MU291-DIAGONAL-COVARIANCE",
        "MU291-DEPTH-SUPPORT-DRIFT",
        "MU291-ZOA-MASK-DRIFT",
        "MU291-WEAK-ID-POINT-ESTIMATE",
        "MU291-FAVOURABLE-ENDPOINT",
        "MU291-PIPELINE-SPREAD-AS-CONFIDENCE",
        "MU291-P0-RESURRECTION",
        "MU291-CURL-PHYSICS-OVERCLAIM",
        "MU291-POTENTIAL-FLOW-OVERCLAIM",
        "MU291-NATIVE-ROLE-REPLAY",
        "MU291-UNREGISTERED-RANK-REDUCTION",
        "MU291-BLOCKED-NUMERIC-WRITE",
        "MU291-OUTPUT-ALIAS",
        "MU291-CLAIM-PROMOTION",
    }
)
_EXPECTED_GENERATION_FIELDS = frozenset(
    {
        "source_commit_or_external_candidate_seal_id",
        "worktree_state",
        "exact_replay_environment",
    }
)
_SHA_RE = re.compile(r"(?:sha256:)?[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_DECISION_TOKEN = object()

CF4_NONEXECUTION_SOURCE_PATHS = frozenset(
    {
        _SPEC_REL.as_posix(),
        _POLICY_REL.as_posix(),
        _STATUS_REL.as_posix(),
        _IDENTITY_REL.as_posix(),
        *_PR289_REQUIRED_SOURCE_PATHS,
        "docs/harness/CLAIM_LEDGER.md",
        "htt/src/common/observed_lane_activation.py",
        "htt/src/common/cf4_observed_lane_activation.py",
        "htt/src/common/depth_path.py",
        "htt/src/common/sky_support.py",
        "htt/obsstat/cf4_post275_lane.py",
        "tests/integration/test_cf4_post275_lane.py",
        "scripts/codex_harness/run_pr290_planck_lane.py",
        "scripts/codex_harness/run_pr291_cf4_lane.py",
    }
)


class Cf4ObservedLaneActivationError(ObservedLaneActivationError):
    """Raised when the CF4 preactivation contract fails closed."""


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Cf4ObservedLaneActivationError(f"{name} must be a mapping")
    return value


def _validate_spec(spec: Mapping[str, object]) -> None:
    if spec.get("pr_id") != "PR-291":
        raise Cf4ObservedLaneActivationError("PR-291 specification identity drifted")
    if spec.get("change_set_id") != "CS-PR291-CF4-REBOOT":
        raise Cf4ObservedLaneActivationError("PR-291 change-set identity drifted")
    if spec.get("publication_group_id") != "PG-PR291-CF4-REBOOT":
        raise Cf4ObservedLaneActivationError("PR-291 publication identity drifted")
    boundary = _require_mapping(spec.get("scientific_boundary"), "scientific boundary")
    if (
        boundary.get("claim_tier") != "diagnostic_only"
        or boundary.get("claim_level")
        != {"scheme": "roadmap_rescue_v1", "level": "C2"}
        or boundary.get("scientific_artifact_mode") != "observed_data_conditional"
        or boundary.get("transfer_source") != "none"
        or boundary.get("observed_data_executed") is not False
        or boundary.get("public_use") is not False
        or boundary.get("family_identification_gate") != "BLOCKED_PRE_NATIVE_ATLAS"
        or boundary.get("maximum_future_result")
        != "COVARIANCE_AND_NUISANCE_CONDITIONAL_MORPHOLOGY_COMPATIBILITY"
    ):
        raise Cf4ObservedLaneActivationError("scientific boundary was relaxed")
    dependency = _require_mapping(spec.get("dependency_contract"), "dependency contract")
    if (
        tuple(dependency.get("required_success_prs", ())) != _EXPECTED_PREDECESSORS
        or dependency.get("required_terminals") != _EXPECTED_REQUIRED_TERMINALS
        or dependency.get("terminal_receipt_paths")
        != {key: value[0].as_posix() for key, value in _EXPECTED_RECEIPTS.items()}
        or dependency.get("expected_receipt_content_ids")
        != {key: value[2] for key, value in _EXPECTED_RECEIPTS.items()}
    ):
        raise Cf4ObservedLaneActivationError("predecessor contract drifted")
    data = _require_mapping(spec.get("data_identity_contract"), "data identity contract")
    if (
        data.get("lane_id") != "CF4"
        or data.get("product_id") != "CF4_GROUP_CATALOGUE_BUNDLE"
        or data.get("registry_path") != _PR289_REGISTRY_REL.as_posix()
        or data.get("registry_content_id") != _EXPECTED_REGISTRY_CONTENT_ID
        or tuple(data.get("required_source_binding_paths", ()))
        != _PR289_REQUIRED_SOURCE_PATHS
        or data.get("preflight_receipt_path") != _IDENTITY_REL.as_posix()
        or data.get("required_admission_status") != "ADMITTED_IDENTITY_ONLY"
        or tuple(data.get("required_components", ()))
        != _EXPECTED_CF4_COMPONENTS
        or data.get("required_analysis_plan_id")
        != "plan:PR291-CF4-TOMOGRAPHY-V1"
        or tuple(data.get("forbidden_admission_shortcuts", ()))
        != _EXPECTED_ADMISSION_SHORTCUTS
    ):
        raise Cf4ObservedLaneActivationError("CF4 identity contract drifted")
    human = _require_mapping(spec.get("human_execution_gate"), "human execution gate")
    authenticity = _require_mapping(
        human.get("authenticity_contract"), "human authenticity contract"
    )
    freshness = _require_mapping(
        human.get("freshness_contract"), "human freshness contract"
    )
    if (
        human.get("gate_id") != "H-CF4"
        or human.get("current_status") != "NOT_AUTHORIZED"
        or human.get("receipt_path") != _AUTH_REL.as_posix()
        or human.get("receipt_schema") != HUMAN_AUTHORIZATION_SCHEMA
        or human.get("authorized_scope") != "admitted_cf4_observed_execution"
        or human.get("authorization_domain") != "lane_data_execution"
        or human.get("authority_key_id") != "H-CF4-OWNER-HMAC-V1"
        or human.get("key_path_environment_variable")
        != "HTT_H_CF4_AUTHORITY_KEY_FILE"
        or human.get("trusted_hmac_key_sha256") is not None
        or human.get("max_authorization_ttl_seconds") != 1800
        or authenticity.get("method") != "external_owner_hmac_sha256"
        or authenticity.get("canonicalization")
        != "sorted_compact_ascii_json_without_authorization_hmac_sha256"
        or authenticity.get("status_alignment_required") is not True
        or authenticity.get("exact_admission_bundle_and_record_ids_required")
        is not True
        or authenticity.get("ordinary_agent_can_mint") is not False
        or authenticity.get("current_trust_anchor_state")
        != "UNPROVISIONED"
        or freshness
        != {
            "issued_at_and_expires_at_utc_required": True,
            "evaluated_at_must_be_in_half_open_interval": (
                "[issued_at_utc, expires_at_utc)"
            ),
            "nonce_required": True,
            "future_executor_must_consume_nonce_once": True,
        }
    ):
        raise Cf4ObservedLaneActivationError("H-CF4 authorization contract drifted")
    pipeline = _require_mapping(spec.get("pipeline_contract"), "pipeline contract")
    units = _require_mapping(
        pipeline.get("units_and_sign_contract"), "units and sign contract"
    )
    full_covariance = _require_mapping(
        pipeline.get("full_covariance_contract"), "full covariance contract"
    )
    depth = _require_mapping(
        pipeline.get("depth_and_zoa_contract"), "depth and ZoA contract"
    )
    weak = _require_mapping(
        pipeline.get("weak_identification_contract"), "weak identification contract"
    )
    legacy = _require_mapping(pipeline.get("legacy_disposition"), "legacy disposition")
    if (
        tuple(pipeline.get("exact_estimand_order", ()))
        != _EXPECTED_ESTIMAND_ORDER
        or tuple(pipeline.get("required_identity_fields", ()))
        != _EXPECTED_IDENTITY_FIELDS
        or units
        != {
            "distance_unit": "Mpc",
            "radial_velocity_unit": "km_per_s",
            "bulk_vector_unit": "km_per_s",
            "shear_tensor_unit": "km_per_s_per_Mpc",
            "monopole_unit": "km_per_s",
            "coordinate_frame": "Galactic_cartesian_right_handed",
            "radial_velocity_sign": "positive_receding",
            "distance_velocity_conversion_identity_required": True,
        }
        or full_covariance.get("diagonal_shortcut_allowed") is not False
        or full_covariance.get("same_catalogue_cross_estimand_dependence_required")
        is not True
        or full_covariance.get("covariance_positive_definite_or_registered_rank_reduction")
        is not True
        or full_covariance.get("feature_order_and_effective_rank_required") is not True
        or full_covariance.get("rank_method")
        != "covariance_whitened_column_normalized_svd"
        or full_covariance.get("relative_singular_floor") != 1.0e-12
        or full_covariance.get("covariance_condition_limit") != 1.0e12
        or full_covariance.get("unregistered_rank_reduction") != "REJECT"
        or full_covariance.get("current_status")
        != "BLOCKED_ADMITTED_COVARIANCE_UNAVAILABLE"
        or depth.get("support_order") != "nested_near_to_far"
        or depth.get("shared_row_identity_required") is not True
        or depth.get("transport_identity_required") is not True
        or depth.get("zoa_mask_identity_required") is not True
        or tuple(depth.get("native_role_cross_binding_required", ()))
        != (
            "catalogue",
            "row_selection",
            "covariance",
            "grouping_definition",
            "depth_definition",
            "zoa_definition",
        )
        or depth.get("arbitrary_shell_reordering_forbidden") is not True
        or depth.get("current_status") != "SYNTHETIC_CONTRACT_ONLY"
        or weak.get("weak_status") != "WEAKLY_IDENTIFIED"
        or weak.get("required_action") != "RESPONSE_EQUIVALENCE_ABSTENTION"
        or weak.get("response_rank_method")
        != "covariance_whitened_column_normalized_svd"
        or weak.get("relative_singular_floor") != 1.0e-12
        or weak.get("eigengap_method") != "spectral_scale_relative"
        or weak.get("relative_eigengap_floor") != 1.0e-10
        or weak.get("favourable_endpoint_as_point_estimate_forbidden") is not True
        or weak.get("pipeline_spread_as_statistical_confidence_forbidden") is not True
        or weak.get("local_global_point_identification_forbidden") is not True
        or pipeline.get("gate_receipts")
        != {
            "G4": "weak_identification_produces_abstention",
            "G5": "depth_path_carries_nested_support_and_transport_identities",
            "G6": "path_calibration_has_proved_premise_or_matched_mock_fallback",
            "G7": "source_separation_preserves_covariance_supported_unidentified_directions",
        }
        or legacy.get("old_p0_headline_status") != "RETIRED_NO_RESCUE"
        or legacy.get("velocity_shape_headline_status") != "RETIRED_NO_RESCUE"
        or legacy.get("wf_curl_div_ratio") != 0.0089
        or legacy.get("wf_curl_div_status")
        != "STABLE_LEGACY_STENCIL_LIMITED_SELF_CONSISTENCY"
        or legacy.get("physical_vorticity_claim") != "FORBIDDEN"
        or legacy.get("potential_flow_claim") != "FORBIDDEN"
        or pipeline.get("implementation_readiness") != _EXPECTED_READINESS
        or pipeline.get("synthetic_contract_fixture") != _EXPECTED_SYNTHETIC_FIXTURE
    ):
        raise Cf4ObservedLaneActivationError("CF4 pipeline contract drifted")
    output = _require_mapping(spec.get("output_contract"), "output contract")
    future = _require_mapping(
        output.get("future_observed_result_contract"), "future observed result contract"
    )
    if (
        output.get("preactivation_receipt")
        != "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json"
        or output.get("observed_result_directory")
        != "docs/research_program/post_pr275/data_runs/cf4/results"
        or tuple(output.get("current_allowed_outputs", ()))
        != _EXPECTED_CURRENT_ALLOWED_OUTPUTS
        or tuple(output.get("current_forbidden_outputs", ()))
        != _EXPECTED_CURRENT_FORBIDDEN_OUTPUTS
        or output.get("output_containment") != _EXPECTED_OUTPUT_CONTAINMENT
        or future.get("current_status") != "DISABLED_PREACTIVATION"
        or future.get("schema") != "htt.pr291.cf4_observed_result.v1"
        or future.get("canonicalization")
        != "sorted_compact_ascii_json_without_receipt_content_sha256"
        or future.get("content_binding_rule")
        != _EXPECTED_FUTURE_CONTENT_BINDING_RULE
        or tuple(future.get("required_metadata", ())) != _EXPECTED_FUTURE_METADATA
        or future.get("status_value_contract")
        != _EXPECTED_FUTURE_STATUS_VALUE_CONTRACT
        or future.get("fixed_firewall_values") != _EXPECTED_FIXED_FIREWALL
        or future.get("activation_rule")
        != "unreachable_until_validator_negative_tests_and_all_external_gates_exist"
    ):
        raise Cf4ObservedLaneActivationError("CF4 output contract drifted")
    mutations = spec.get("mutation_registry")
    if not isinstance(mutations, Sequence) or isinstance(mutations, (str, bytes)):
        raise Cf4ObservedLaneActivationError("mutation registry is invalid")
    mutation_ids = {
        row.get("mutation_id")
        for row in mutations
        if isinstance(row, Mapping)
    }
    if mutation_ids != _EXPECTED_MUTATIONS:
        raise Cf4ObservedLaneActivationError("mutation registry drifted")
    if tuple(spec.get("allowed_uses", ())) != _EXPECTED_ALLOWED_USES:
        raise Cf4ObservedLaneActivationError("allowed-use boundary drifted")
    if tuple(spec.get("forbidden_uses", ())) != _EXPECTED_FORBIDDEN_USES:
        raise Cf4ObservedLaneActivationError("forbidden-use boundary drifted")
    if spec.get("artifact_ownership") != _EXPECTED_OWNERSHIP:
        raise Cf4ObservedLaneActivationError("artifact ownership drifted")
    if tuple(spec.get("terminal_precedence", ())) != _EXPECTED_TERMINALS:
        raise Cf4ObservedLaneActivationError("terminal precedence drifted")


def _terminal_snapshot(
    *, root: Path, pr_id: str, expected_terminal: str
) -> tuple[dict[str, object], tuple[str, ...]]:
    relative, expected_schema, expected_content = _EXPECTED_RECEIPTS[pr_id]
    try:
        path = _regular_file_within(root, relative, label=f"{pr_id} terminal receipt")
        payload = _strict_json(path, label=f"{pr_id} terminal receipt")
    except ObservedLaneActivationError:
        return (
            {
                "path": relative.as_posix(),
                "file_sha256": None,
                "content_id": None,
                "schema": None,
                "terminal": None,
                "satisfied": False,
            },
            (f"{pr_id}: authoritative terminal receipt is unavailable or invalid",),
        )
    reasons: list[str] = []
    if payload.get("schema") != expected_schema:
        reasons.append(f"{pr_id}: terminal receipt schema mismatch")
    if payload.get("terminal") != expected_terminal:
        reasons.append(f"{pr_id}: terminal receipt token mismatch")
    observed_content = payload.get("receipt_content_id")
    unsigned = dict(payload)
    unsigned.pop("receipt_content_id", None)
    recomputed = "sha256:" + hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    if observed_content != recomputed:
        reasons.append(f"{pr_id}: terminal receipt content identity mismatch")
    if expected_content is None:
        reasons.append(f"{pr_id}: frozen terminal receipt identity is unregistered")
    elif observed_content != expected_content:
        reasons.append(f"{pr_id}: frozen terminal receipt identity mismatch")
    return (
        {
            "path": relative.as_posix(),
            "file_sha256": _sha256_file(path),
            "content_id": observed_content,
            "schema": payload.get("schema"),
            "terminal": payload.get("terminal"),
            "satisfied": not reasons,
        },
        tuple(reasons),
    )


def _dependency_snapshot(
    spec: Mapping[str, object], status: Mapping[str, object], *, root: Path
) -> tuple[tuple[dict[str, object], ...], tuple[str, ...]]:
    dependency = _require_mapping(spec["dependency_contract"], "dependency contract")
    completed = status.get("completed", ())
    resolutions = status.get("execution_resolutions", {})
    if not isinstance(completed, Sequence) or isinstance(completed, (str, bytes)):
        raise Cf4ObservedLaneActivationError("canonical completed inventory is invalid")
    if not isinstance(resolutions, Mapping):
        raise Cf4ObservedLaneActivationError("execution resolutions are invalid")
    rows: list[dict[str, object]] = []
    all_reasons: list[str] = []
    for pr_id in _EXPECTED_PREDECESSORS:
        row = resolutions.get(pr_id)
        row = row if isinstance(row, Mapping) else {}
        reasons: list[str] = []
        if pr_id not in completed:
            reasons.append(f"{pr_id}: not in canonical completed set")
        if row.get("resolution") != "COMPLETED_SUCCESS":
            reasons.append(f"{pr_id}: completion resolution is not success")
        if row.get("success_dependency_satisfied") is not True:
            reasons.append(f"{pr_id}: success dependency is not satisfied")
        if row.get("observed_data_executed") is not False:
            reasons.append(f"{pr_id}: observed-data boundary is not false")
        if row.get("public_use") is not False:
            reasons.append(f"{pr_id}: public-use boundary is not false")
        candidate_sha = row.get("candidate_sha")
        if not isinstance(candidate_sha, str) or _COMMIT_RE.fullmatch(candidate_sha) is None:
            reasons.append(f"{pr_id}: candidate SHA is missing or invalid")
        expected_terminal = _EXPECTED_REQUIRED_TERMINALS.get(pr_id)
        receipt: dict[str, object] | None = None
        if expected_terminal is not None and not reasons:
            if row.get("terminal") != expected_terminal:
                reasons.append(f"{pr_id}: canonical terminal token mismatch")
            receipt, receipt_reasons = _terminal_snapshot(
                root=root, pr_id=pr_id, expected_terminal=expected_terminal
            )
            reasons.extend(receipt_reasons)
        rows.append(
            {
                "pr_id": pr_id,
                "resolution": row.get("resolution"),
                "candidate_sha": candidate_sha,
                "required_terminal": expected_terminal,
                "canonical_terminal": row.get("terminal"),
                "terminal_receipt": receipt,
                "success_dependency_satisfied": row.get("success_dependency_satisfied"),
                "observed_data_executed": row.get("observed_data_executed"),
                "public_use": row.get("public_use"),
                "satisfied": not reasons,
                "reasons": reasons,
            }
        )
        all_reasons.extend(reasons)
    return tuple(rows), tuple(all_reasons)


def _identity_snapshot(
    *,
    root: Path,
    spec: Mapping[str, object],
    identity: Mapping[str, object],
) -> tuple[dict[str, object], tuple[str, ...]]:
    if identity.get("schema") != "common.data_identity_v2_preflight_receipt.v1":
        raise Cf4ObservedLaneActivationError("PR-289 receipt schema drifted")
    if identity.get("terminal") != "PASS_DATA_IDENTITY_V2_PREFLIGHT":
        raise Cf4ObservedLaneActivationError("PR-289 receipt terminal drifted")
    unsigned = dict(identity)
    observed_content = unsigned.pop("receipt_content_id", None)
    recomputed = "sha256:" + hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    if (
        observed_content != recomputed
        or observed_content != _EXPECTED_PR289_RECEIPT_CONTENT_ID
    ):
        raise Cf4ObservedLaneActivationError(
            "PR-289 receipt content identity drifted"
        )

    data = _require_mapping(spec["data_identity_contract"], "data identity contract")
    decisions = identity.get("lane_decisions")
    authorizations = identity.get("authorization_receipts")
    if not isinstance(decisions, list) or not isinstance(authorizations, list):
        raise Cf4ObservedLaneActivationError(
            "PR-289 lane inventories are invalid"
        )
    decision_rows = [
        row
        for row in decisions
        if isinstance(row, Mapping) and row.get("lane_id") == "CF4"
    ]
    authorization_rows = [
        row
        for row in authorizations
        if isinstance(row, Mapping) and row.get("lane_id") == "CF4"
    ]
    if len(decision_rows) != 1 or len(authorization_rows) != 1:
        raise Cf4ObservedLaneActivationError(
            "CF4 identity rows are missing or duplicated"
        )
    decision = decision_rows[0]
    authorization = authorization_rows[0]
    reasons: list[str] = []
    if decision.get("product_id") != data.get("product_id"):
        reasons.append("CF4 product identity differs from the specification")
    if decision.get("status") != data.get("required_admission_status"):
        reasons.append("CF4 identity is not ADMITTED_IDENTITY_ONLY")

    replayed = None
    expected_authorization = None
    lane = None
    try:
        identity_module = _load_pr289_identity_module(
            root=root, identity=identity
        )
        registry_path = _regular_file_within(
            root, _PR289_REGISTRY_REL, label="PR-289 lane registry"
        )
        registry = identity_module.load_lane_registry(registry_path)
        lane = registry.lane("CF4")
        if tuple(lane.expected_component_sequence) != _EXPECTED_CF4_COMPONENTS:
            raise Cf4ObservedLaneActivationError(
                "CF4 native component role inventory drifted"
            )
        replayed = identity_module.replay_lane_admission_decision(
            decision, registry=registry
        )
        if replayed.as_payload() != dict(decision):
            raise Cf4ObservedLaneActivationError(
                "CF4 admission payload is not canonical after replay"
            )
        expected_authorization = identity_module.build_not_authorized_receipt(
            lane, replayed
        ).as_payload()
    except Exception as exc:
        reasons.append(f"CF4 canonical native-record replay failed: {exc}")

    record_ids: list[str] = []
    component_ids: list[str] = []
    native_profile_ids: set[str] = set()
    native_profile: dict[str, object] | None = None
    normalized_bundle = None
    if replayed is not None:
        record_ids = [record.record_id for record in replayed.records]
        component_ids = [record.component_id for record in replayed.records]
        native_profile_ids = {
            record.native_identity_profile_id for record in replayed.records
        }
        normalized_bundle = replayed.lane_admission_bundle_id
        if tuple(component_ids) not in ((), _EXPECTED_CF4_COMPONENTS):
            reasons.append("CF4 canonical native component inventory drifted")
        if record_ids:
            if (
                len(native_profile_ids) != 1
                or any(
                    record.native_identity_profile.get("schema")
                    != "common.cf4_native_identity.v1"
                    for record in replayed.records
                )
            ):
                reasons.append("CF4 canonical native profile identity drifted")
            else:
                native_profile = dict(replayed.records[0].native_identity_profile)
    if not record_ids:
        reasons.append("CF4 exact nine-role admission records are absent")

    if (
        authorization.get("analysis_plan_id")
        != data.get("required_analysis_plan_id")
        or authorization.get("required_human_gate_id") != "H-CF4"
    ):
        reasons.append("PR-289 authorization identity differs from PR-291")
    if tuple(authorization.get("exact_admission_record_ids", ())) != tuple(
        record_ids
    ):
        reasons.append("PR-289 authorization record IDs differ from admission")
    if expected_authorization is None or dict(authorization) != expected_authorization:
        reasons.append(
            "PR-289 authorization is not the canonical native admission projection"
        )

    snapshot = {
        "receipt_schema": identity.get("schema"),
        "aggregate_status": identity.get("aggregate_status"),
        "lane_id": "CF4",
        "product_id": decision.get("product_id"),
        "admission_status": decision.get("status"),
        "lane_admission_bundle_id": normalized_bundle,
        "record_ids": record_ids,
        "record_count": len(record_ids),
        "component_ids": component_ids,
        "native_identity_profile_ids": sorted(native_profile_ids),
        "native_identity_profile": native_profile,
        "canonical_record_replay": replayed is not None,
        "pr289_authorization_status": authorization.get("status"),
        "analysis_plan_id": authorization.get("analysis_plan_id"),
        "required_human_gate_id": authorization.get("required_human_gate_id"),
        "satisfied": not reasons,
        "reasons": reasons,
    }
    return snapshot, tuple(reasons)

def _human_snapshot(
    *, root: Path, status: Mapping[str, object], dependencies_satisfied: bool, identity_satisfied: bool
) -> tuple[dict[str, object], tuple[str, ...]]:
    path = _optional_regular_file_within(root, _AUTH_REL, label="H-CF4 authorization receipt")
    external_events = status.get("external_events", {})
    event = external_events.get("H-CF4") if isinstance(external_events, Mapping) else None
    canonical_status = event.get("status") if isinstance(event, Mapping) else None
    if not dependencies_satisfied:
        status_value = "NOT_EVALUATED_PREDECESSOR_BLOCKED"
    elif not identity_satisfied:
        status_value = "NOT_EVALUATED_IDENTITY_BLOCKED"
    else:
        status_value = "NOT_AUTHORIZED"
    reasons = (
        "H-CF4 trusted HMAC key is unprovisioned and no authorization is accepted",
    )
    return (
        {
            "gate_id": "H-CF4",
            "status": status_value,
            "canonical_status": canonical_status,
            "receipt_path": _AUTH_REL.as_posix(),
            "receipt_present": path is not None,
            "receipt_file_sha256": _sha256_file(path) if path is not None else None,
            "authentication_mode": "external_owner_hmac_sha256",
            "authority_key_id": "H-CF4-OWNER-HMAC-V1",
            "trusted_hmac_key_sha256": None,
            "ordinary_agent_can_mint": False,
            "authorized": False,
            "reasons": list(reasons),
        },
        reasons,
    )


@dataclass(frozen=True)
class Cf4ActivationDecision:
    terminal: str
    reasons: tuple[str, ...]
    dependency_snapshot: tuple[dict[str, object], ...]
    data_identity_snapshot: dict[str, object]
    human_authorization_snapshot: dict[str, object]
    operator_snapshot: dict[str, object]
    evaluated_at_utc: str
    observed_data_executed: bool = False
    numeric_outputs_written: tuple[str, ...] = ()
    network_or_download_side_effect: bool = False
    public_use: bool = False
    family_identification_gate: str = "BLOCKED_PRE_NATIVE_ATLAS"
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DECISION_TOKEN:
            raise Cf4ObservedLaneActivationError("Cf4ActivationDecision must be factory-built")
        if self.terminal not in _EXPECTED_TERMINALS:
            raise Cf4ObservedLaneActivationError("unknown CF4 terminal")
        if self.observed_data_executed or self.numeric_outputs_written:
            raise Cf4ObservedLaneActivationError("preactivation cannot execute or emit numbers")
        if self.network_or_download_side_effect or self.public_use:
            raise Cf4ObservedLaneActivationError("preactivation side effect boundary drifted")
        if self.family_identification_gate != "BLOCKED_PRE_NATIVE_ATLAS":
            raise Cf4ObservedLaneActivationError("family-identification gate drifted")
        object.__setattr__(
            self,
            "_identity_seal",
            "sha256:" + hashlib.sha256(canonical_json_bytes(self._payload())).hexdigest(),
        )

    def _payload(self) -> dict[str, object]:
        return {
            "schema": SCHEMA_VERSION,
            "terminal": self.terminal,
            "reasons": list(self.reasons),
            "dependency_snapshot": list(self.dependency_snapshot),
            "data_identity_snapshot": self.data_identity_snapshot,
            "human_authorization_snapshot": self.human_authorization_snapshot,
            "operator_snapshot": self.operator_snapshot,
            "evaluated_at_utc": self.evaluated_at_utc,
            "observed_data_executed": self.observed_data_executed,
            "numeric_outputs_written": list(self.numeric_outputs_written),
            "network_or_download_side_effect": self.network_or_download_side_effect,
            "public_use": self.public_use,
            "family_identification_gate": self.family_identification_gate,
        }

    @property
    def content_id(self) -> str:
        if "sha256:" + hashlib.sha256(canonical_json_bytes(self._payload())).hexdigest() != self._identity_seal:
            raise Cf4ObservedLaneActivationError("CF4 decision drifted after construction")
        return self._identity_seal

    def as_payload(self) -> dict[str, object]:
        return {**self._payload(), "decision_content_id": self.content_id}


def build_cf4_activation_decision(
    *, repository_root: Path, evaluated_at_utc: str = "2026-08-09T00:00:00+00:00"
) -> Cf4ActivationDecision:
    try:
        root = _repository_root(repository_root)
        spec = _yaml_mapping(
            _regular_file_within(root, _SPEC_REL, label="PR-291 specification"),
            label="PR-291 specification",
        )
        _validate_spec(spec)
        status = _yaml_mapping(
            _regular_file_within(root, _STATUS_REL, label="canonical status"),
            label="canonical status",
        )
        identity_path = _regular_file_within(root, _IDENTITY_REL, label="PR-289 receipt")
        identity = _strict_json(identity_path, label="PR-289 receipt")
        _validate_pr289_receipt_provenance(root=root, identity=identity)
        dependency_rows, dependency_reasons = _dependency_snapshot(spec, status, root=root)
        identity_row, identity_reasons = _identity_snapshot(
            root=root, spec=spec, identity=identity
        )
        human_row, human_reasons = _human_snapshot(
            root=root,
            status=status,
            dependencies_satisfied=not dependency_reasons,
            identity_satisfied=not identity_reasons,
        )
        _parse_utc(evaluated_at_utc, label="evaluated_at_utc")
    except Cf4ObservedLaneActivationError:
        raise
    except ObservedLaneActivationError as exc:
        raise Cf4ObservedLaneActivationError(str(exc)) from exc
    readiness = _require_mapping(
        _require_mapping(spec["pipeline_contract"], "pipeline contract")[
            "implementation_readiness"
        ],
        "implementation readiness",
    )
    operator_reasons = [
        f"{name}: {value}"
        for name, value in readiness.items()
        if value not in {"SYNTHETIC_OPERATOR_CONTRACT_ONLY"}
    ]
    operator = {
        **dict(readiness),
        "observed_operator_ready": False,
        "observed_data_executed": False,
        "claim_tier": "diagnostic_only",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "reasons": operator_reasons,
    }
    if dependency_reasons:
        terminal = "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
        reasons = dependency_reasons
    elif identity_reasons:
        terminal = "BLOCKED_DATA_IDENTITY_ADMISSION"
        reasons = identity_reasons
    elif human_reasons:
        terminal = "BLOCKED_HUMAN_EXECUTION_AUTHORIZATION"
        reasons = human_reasons
    elif operator_reasons:
        terminal = "BLOCKED_OPERATOR_IMPLEMENTATION"
        reasons = tuple(operator_reasons)
    else:
        terminal = "READY_FOR_ATTENDED_CF4_EXECUTION"
        reasons = ()
    return Cf4ActivationDecision(
        terminal=terminal,
        reasons=tuple(reasons),
        dependency_snapshot=dependency_rows,
        data_identity_snapshot=identity_row,
        human_authorization_snapshot=human_row,
        operator_snapshot=operator,
        evaluated_at_utc=evaluated_at_utc,
        _construction_token=_DECISION_TOKEN,
    )


def build_cf4_nonexecution_receipt(
    *,
    decision: Cf4ActivationDecision,
    source_bindings: Mapping[str, object],
    generation_identity: Mapping[str, object],
) -> dict[str, object]:
    if type(decision) is not Cf4ActivationDecision:
        raise TypeError("decision must be an exact Cf4ActivationDecision")
    decision.as_payload()
    expected_sources = set(CF4_NONEXECUTION_SOURCE_PATHS)
    for row in decision.dependency_snapshot:
        terminal = row.get("terminal_receipt")
        if isinstance(terminal, Mapping) and terminal.get("file_sha256") is not None:
            path = terminal.get("path")
            if isinstance(path, str):
                expected_sources.add(path)
    if not isinstance(source_bindings, Mapping) or set(source_bindings) != expected_sources:
        raise Cf4ObservedLaneActivationError("nonexecution source inventory drifted")
    normalized_sources = {
        path: _normalize_digest(source_bindings[path], label=f"source binding {path}")
        for path in sorted(expected_sources)
    }
    if not isinstance(generation_identity, Mapping) or set(generation_identity) != (
        _EXPECTED_GENERATION_FIELDS
    ):
        raise Cf4ObservedLaneActivationError("generation identity field inventory drifted")
    source_identity = generation_identity.get(
        "source_commit_or_external_candidate_seal_id"
    )
    if not isinstance(source_identity, str) or (
        _SHA_RE.fullmatch(source_identity) is None
        and _COMMIT_RE.fullmatch(source_identity) is None
    ):
        raise Cf4ObservedLaneActivationError("generation source identity is invalid")
    for field_name in ("worktree_state", "exact_replay_environment"):
        value = generation_identity.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise Cf4ObservedLaneActivationError(f"{field_name} is invalid")
    payload = {
        "schema": NONEXECUTION_RECEIPT_SCHEMA,
        "pr_id": "PR-291",
        "owner": "HTT",
        "contributors": ["OBSSTAT", "COMMON"],
        "scope": "CF4 observed-lane preactivation and synthetic operator contract",
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "observed_data_conditional",
        "transfer_source": "none",
        "observed_data_executed": False,
        "numeric_outputs_written": [],
        "network_or_download_side_effect": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "scientific_status_effect": "OPEN_UNCHANGED",
        "terminal": decision.terminal,
        "reasons": list(decision.reasons),
        "decision": decision.as_payload(),
        "allowed_uses": list(_EXPECTED_ALLOWED_USES),
        "forbidden_uses": list(_EXPECTED_FORBIDDEN_USES),
        "source_bindings": normalized_sources,
        "generation_identity": dict(generation_identity),
        "caveats": [
            "PR-201, PR-287, and PR-289 are not canonically completed-success dependencies.",
            "The PR-289 CF4 identity row is REJECTED_NOT_PRESENT.",
            "H-CF4 has no provisioned trusted HMAC key and accepts no authorization.",
            "No observed CF4 catalogue bytes are read, transformed, or summarized.",
            "The 0.0089 legacy ratio is not evidence for physical vorticity or cosmic potential flow.",
        ],
    }
    return {
        **payload,
        "receipt_content_sha256": "sha256:"
        + hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
    }


__all__ = [
    "CF4_NONEXECUTION_SOURCE_PATHS",
    "HUMAN_AUTHORIZATION_SCHEMA",
    "NONEXECUTION_RECEIPT_SCHEMA",
    "SCHEMA_VERSION",
    "Cf4ActivationDecision",
    "Cf4ObservedLaneActivationError",
    "build_cf4_activation_decision",
    "build_cf4_nonexecution_receipt",
    "canonical_json_bytes",
]
