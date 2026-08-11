"""Fail-closed activation contract for post-PR275 observed-data lanes.

PR-290 uses this module only to decide whether the Planck lane is still
blocked and to build a non-execution receipt.  The module deliberately has no
OBSSTAT import and no observed-data reader.  Identity admission, an externally
authenticated human execution receipt, and a complete numerical operator are
separate gates; none can be inferred from another.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import datetime
import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Mapping, Sequence

import yaml


SCHEMA_VERSION = "common.observed_lane_activation.v1"
NONEXECUTION_RECEIPT_SCHEMA = "htt.pr290.planck_nonexecution_receipt.v1"
HUMAN_AUTHORIZATION_SCHEMA = "common.human_execution_authorization.v1"

_SPEC_REL = Path("docs/research_program/post_pr275/pr290_spec.yaml")
_STATUS_REL = Path("docs/codex_handoff/pr_status.yaml")
_IDENTITY_REL = Path("docs/generated/pr289_data_identity_v2_receipt.json")
_PR289_REGISTRY_REL = Path(
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
_PR289_REQUIRED_SOURCE_PATHS = (
    "docs/harness/CLAIM_LEDGER.md",
    _PR289_REGISTRY_REL.as_posix(),
    "docs/research_program/post_pr275/data_runbooks.yaml",
    "docs/research_program/post_pr275/pr289_publication_policy.json",
    "docs/research_program/post_pr275/pr289_spec.yaml",
    (
        "docs/research_program/vector_tensor/data_admission/"
        "PR274_ADMISSION_RESULT.json"
    ),
    (
        "docs/research_program/vector_tensor/data_admission/"
        "PR274_DATA_IDENTITY_REGISTRY.yaml"
    ),
    "htt/src/common/data_identity.py",
    "scripts/codex_harness/run_pr289_data_identity_v2.py",
    "tests/contracts/test_data_identity_registry_v2.py",
)
_EXPECTED_PR289_REGISTRY_CONTENT_ID = (
    "sha256:78e3ec41833db433b560ebf839e0ee9375f77879a629e4ce70900bfb959bbef0"
)
_EXPECTED_PLANCK_COMPONENTS = (
    "smica_map",
    "commander_map",
    "smica_mask",
    "commander_mask",
    "smica_beam",
    "commander_beam",
    "smica_window_operator",
    "commander_window_operator",
    "smica_covariance",
    "commander_covariance",
    "pixelization",
    "native_selection",
    "ffp10_null_inventory",
)
_PR287_TERMINAL_REL = Path(
    "docs/generated/pr287_fresh_blind_typed_replay_receipt.json"
)
_PR288_TERMINAL_REL = Path("docs/generated/pr288_bayesian_semantics_receipt.json")
_AUTH_REL = Path(
    "docs/research_program/post_pr275/data_runs/planck/"
    "H_PLANCK_EXECUTION_AUTHORIZATION.json"
)
_EXPECTED_PREDECESSORS = ("PR-202", "PR-287", "PR-288", "PR-289")
_EXPECTED_REQUIRED_TERMINALS = {
    "PR-287": "PASS_FRESH_BLIND_TYPED_REPLAY",
    "PR-288": "PASS_BAYESIAN_SEMANTICS_REPAIR",
    "PR-289": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
}
_EXPECTED_TERMINAL_RECEIPTS = {
    "PR-287": (
        _PR287_TERMINAL_REL,
        "HTT_PR287_FRESH_BLIND_TYPED_REPLAY_RECEIPT_V1",
        "receipt_content_id",
    ),
    "PR-288": (
        _PR288_TERMINAL_REL,
        "HTT_PR288_BAYESIAN_SEMANTICS_RECEIPT_V1",
        "receipt_content_id",
    ),
    "PR-289": (
        _IDENTITY_REL,
        "common.data_identity_v2_preflight_receipt.v1",
        "receipt_content_id",
    ),
}
_EXPECTED_TERMINALS = (
    "BLOCKED_CONTRACT_INVALID",
    "BLOCKED_PREDECESSOR_FINAL_SUCCESS",
    "BLOCKED_DATA_IDENTITY_ADMISSION",
    "BLOCKED_HUMAN_EXECUTION_AUTHORIZATION",
    "BLOCKED_OPERATOR_IMPLEMENTATION",
    "READY_FOR_ATTENDED_PLANCK_EXECUTION",
    "PASS_PLANCK_OBSERVED_LANE_REBOOT",
)
_SHA_RE = re.compile(r"(?:sha256:)?[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_HUMAN_FIELDS = frozenset(
    {
        "schema",
        "status",
        "lane_id",
        "gate_id",
        "analysis_plan_id",
        "authorized_scope",
        "lane_admission_bundle_id",
        "exact_admission_record_ids",
        "human_authority_identity",
        "authority_key_id",
        "issued_at_utc",
        "expires_at_utc",
        "nonce",
        "authorization_domain",
        "authorization_hmac_sha256",
    }
)
_EXPECTED_ALLOWED_USES = (
    "typed Planck operator composition on explicitly synthetic fixtures",
    "fail-closed dependency admission and authorization preflight",
    "future attended execution planning after a distinct human authorization",
)
_EXPECTED_FORBIDDEN_USES = (
    "automatic observed execution",
    "use of PR-151 partial acquisition",
    "SMICA-only generalization",
    "diagonal covariance or undeconvolved-mask headline",
    "native solver or transfer validation",
    "anisotropy source or Bianchi-family identification",
    "public or manuscript claim from preactivation evidence",
)
_EXPECTED_ARTIFACT_OWNERSHIP = {
    "delivery_orchestration": "HTT",
    "observable_features_morphology_axes_and_null_features": "OBSSTAT",
    "activation_manifests_provenance_and_semantic_guards": "COMMON",
    "model_dependent_likelihood_posterior_evidence": (
        "HTT_NOT_EXECUTED_BY_PREACTIVATION"
    ),
    "mio_diagnostic_crosscheck": "NOT_AN_ACTIVE_PR290_ESTIMAND",
    "tsc_teff": "LEGACY_ONLY",
}
_EXPECTED_FUTURE_RESULT_METADATA = (
    "artifact_owner",
    "scope",
    "claim_tier",
    "claim_level",
    "scientific_artifact_mode",
    "transfer_source",
    "allowed_uses",
    "forbidden_uses",
    "exact_admitted_record_ids",
    "lane_admission_bundle_id",
    "human_authorization_receipt_sha256",
    "sky_support_status",
    "mask_id",
    "beam_id",
    "pixel_window_id",
    "harmonic_convention_id",
    "units_id",
    "covariance_id",
    "covariance_status",
    "null_ensemble_id",
    "null_mock_status",
    "feature_order_id",
    "look_elsewhere_family_id",
    "response_id",
    "generating_procedure",
    "source_bindings",
    "git_commit_or_external_candidate_seal_id",
    "worktree_state",
    "caveats",
    "receipt_content_sha256",
)
_EXPECTED_OBSERVATION_PRODUCTS = ("SMICA", "Commander")
_EXPECTED_MAP_PRODUCT_IDS = {
    "SMICA": "planck:pr3:smica:lowell:v1",
    "Commander": "planck:pr3:commander:lowell:v1",
}
_EXPECTED_OPERATOR_IDENTITY_FIELDS = (
    "pipeline_id",
    "map_product_id",
    "mask_id",
    "beam_id",
    "harmonic_convention_id",
    "estimator_family_id",
    "covariance_id",
    "null_ensemble_id",
    "look_elsewhere_family_id",
    "response_id",
    "units_id",
    "pixel_window_id",
    "feature_order_id",
    "mask_deconvolution_id",
)
_EXPECTED_IMPLEMENTATION_READINESS = {
    "beam_pixel_normalization": "BLOCKED_IMPLEMENTATION_UNAVAILABLE",
    "mask_deconvolution": "BLOCKED_UNDECONVOLVED",
    "multipole_vectors": "BLOCKED_EXTRACTOR_UNAVAILABLE",
    "joint_covariance": "BLOCKED_FEATURE_VECTOR_UNREGISTERED",
    "global_response": "BLOCKED_UNBOUND_GLOBAL_RESPONSE",
}
_EXPECTED_ACTIVE_ESTIMAND_STATUS = {
    "local_boost": "synthetic_operator_contract_only",
    "global_tilt": "BLOCKED_UNBOUND_GLOBAL_RESPONSE",
    "local_global_rank": "NOT_MEASURED",
    "Q": "BLOCKED_NO_DEPARTURE_BUNDLE_BUDGET",
    "F": "BLOCKED_NO_SIGN_CLEAN_XC_AND_CEILING",
    "Pi": "BLOCKED_NO_Q_OR_F_MEASURE",
    "G_F": "NOT_APPLICABLE_NO_DEPTH_AXIS",
    "likelihood_prior_posterior_evidence": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
}
_EXPECTED_SYNTHETIC_FIXTURE = {
    "fixture_id": "PR290-SYNTHETIC-LOWELL-OPERATOR-V1",
    "purpose": "operator_identity_shape_sign_and_permutation_tests_only",
    "required_component_rows": ["SMICA", "Commander"],
    "cannot_support": [
        "observed_number",
        "p_value",
        "morphology_claim",
        "public_figure",
    ],
}
_EXPECTED_CURRENT_ALLOWED_OUTPUTS = (
    "preactivation_nonexecution_receipt",
    "synthetic_operator_test_evidence",
)
_EXPECTED_CURRENT_FORBIDDEN_OUTPUTS = (
    "observed_alm_or_cl",
    "observed_power_tensor_or_poles",
    "observed_biposh_or_parity",
    "observed_sector_stress_or_response",
    "observed_p_value_or_exceedance",
    "observed_component_separation_comparison",
    "claim_bearing_figure",
)
REQUIRED_NONEXECUTION_SOURCE_PATHS = frozenset(
    {
        _SPEC_REL.as_posix(),
        "docs/research_program/post_pr275/pr290_publication_policy.json",
        _STATUS_REL.as_posix(),
        _IDENTITY_REL.as_posix(),
        _PR288_TERMINAL_REL.as_posix(),
        *_PR289_REQUIRED_SOURCE_PATHS,
        "docs/harness/CLAIM_LEDGER.md",
        "htt/src/common/observed_lane_activation.py",
        "htt/obsstat/planck_post275_lane.py",
        "htt/obsstat/boost_biposh_residual.py",
        "tests/integration/test_planck_post275_lane.py",
        "scripts/codex_harness/run_pr290_planck_lane.py",
    }
)
_EXPECTED_GENERATION_FIELDS = frozenset(
    {
        "source_commit_or_external_candidate_seal_id",
        "worktree_state",
        "exact_replay_environment",
    }
)
_DECISION_TOKEN = object()


class ObservedLaneActivationError(ValueError):
    """Raised when a PR-290 activation or receipt contract is malformed."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ObservedLaneActivationError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def canonical_json_bytes(payload: object) -> bytes:
    """Return the exact canonical JSON domain used by PR-290 content seals."""

    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ObservedLaneActivationError("payload is not canonical JSON") from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(16 << 20):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _normalize_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise ObservedLaneActivationError(f"{label} must be a SHA-256 digest")
    return value if value.startswith("sha256:") else "sha256:" + value


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise ObservedLaneActivationError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def _strict_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ObservedLaneActivationError(
                    f"{label} contains non-finite JSON constant {value}"
                )
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ObservedLaneActivationError(f"{label} is not strict JSON") from exc
    if not isinstance(payload, dict):
        raise ObservedLaneActivationError(f"{label} must be a JSON object")
    return payload


def _yaml_mapping(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload = yaml.load(
            path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader
        )
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ObservedLaneActivationError(f"{label} is not valid YAML") from exc
    if not isinstance(payload, dict):
        raise ObservedLaneActivationError(f"{label} must be a mapping")
    return payload


def _repository_root(value: Path) -> Path:
    candidate = Path(value)
    if candidate.is_symlink() or not candidate.is_dir():
        raise ObservedLaneActivationError("repository root must be a regular directory")
    return candidate.resolve(strict=True)


def _regular_file_within(root: Path, relative: Path, *, label: str) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise ObservedLaneActivationError(f"{label} path escaped repository root")
    cursor = root
    for part in relative.parent.parts:
        cursor /= part
        try:
            mode = cursor.lstat().st_mode
        except OSError as exc:
            raise ObservedLaneActivationError(f"{label} parent is missing") from exc
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ObservedLaneActivationError(
                f"{label} parent must be a regular directory"
            )
    path = root / relative
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ObservedLaneActivationError(f"{label} is missing") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ObservedLaneActivationError(f"{label} must be a regular file")
    if metadata.st_nlink != 1:
        raise ObservedLaneActivationError(f"{label} must be a single-link file")
    if not path.resolve(strict=True).is_relative_to(root):
        raise ObservedLaneActivationError(f"{label} resolved outside repository")
    return path


def _optional_regular_file_within(
    root: Path, relative: Path, *, label: str
) -> Path | None:
    path = root / relative
    if not path.exists() and not path.is_symlink():
        return None
    return _regular_file_within(root, relative, label=label)


def _parse_utc(value: object, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("+00:00"):
        raise ObservedLaneActivationError(f"{label} must be explicit UTC")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ObservedLaneActivationError(f"{label} is invalid") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ObservedLaneActivationError(f"{label} must be UTC")
    return parsed


def _validate_spec(spec: Mapping[str, object]) -> None:
    if spec.get("pr_id") != "PR-290":
        raise ObservedLaneActivationError("PR-290 specification identity drifted")
    if spec.get("change_set_id") != "CS-PR290-PLANCK-REBOOT":
        raise ObservedLaneActivationError("PR-290 change-set identity drifted")
    if spec.get("publication_group_id") != "PG-PR290-PLANCK-REBOOT":
        raise ObservedLaneActivationError("PR-290 publication identity drifted")
    boundary = spec.get("scientific_boundary")
    if not isinstance(boundary, Mapping):
        raise ObservedLaneActivationError("scientific boundary is missing")
    if (
        boundary.get("claim_tier") != "diagnostic_only"
        or boundary.get("claim_level")
        != {"scheme": "roadmap_rescue_v1", "level": "C2"}
        or boundary.get("scientific_artifact_mode") != "observed_data_conditional"
        or boundary.get("transfer_source") != "none"
        or boundary.get("observed_data_executed") is not False
        or boundary.get("public_use") is not False
        or boundary.get("family_identification_gate")
        != "BLOCKED_PRE_NATIVE_ATLAS"
        or boundary.get("maximum_future_result")
        != (
            "OBSERVED_DESCRIPTIVE_OR_PIPELINE_CONDITIONAL_"
            "MORPHOLOGY_COMPATIBILITY"
        )
    ):
        raise ObservedLaneActivationError("scientific boundary was relaxed")
    dependency = spec.get("dependency_contract")
    if not isinstance(dependency, Mapping) or tuple(
        dependency.get("required_success_prs", ())
    ) != _EXPECTED_PREDECESSORS:
        raise ObservedLaneActivationError("predecessor inventory drifted")
    if dependency.get("required_terminals") != _EXPECTED_REQUIRED_TERMINALS:
        raise ObservedLaneActivationError("required predecessor terminals drifted")
    if dependency.get("terminal_receipt_paths") != {
        pr_id: receipt[0].as_posix()
        for pr_id, receipt in _EXPECTED_TERMINAL_RECEIPTS.items()
    }:
        raise ObservedLaneActivationError("predecessor receipt paths drifted")
    pipeline = spec.get("pipeline_contract")
    if not isinstance(pipeline, Mapping) or (
        tuple(pipeline.get("observation_products", ()))
        != _EXPECTED_OBSERVATION_PRODUCTS
        or pipeline.get("map_product_ids") != _EXPECTED_MAP_PRODUCT_IDS
        or pipeline.get("identical_observation_null_pipeline") is not True
        or tuple(pipeline.get("required_identity_fields", ()))
        != _EXPECTED_OPERATOR_IDENTITY_FIELDS
        or pipeline.get("implementation_readiness")
        != _EXPECTED_IMPLEMENTATION_READINESS
        or pipeline.get("response_and_active_estimand_status")
        != _EXPECTED_ACTIVE_ESTIMAND_STATUS
        or pipeline.get("synthetic_contract_fixture")
        != _EXPECTED_SYNTHETIC_FIXTURE
    ):
        raise ObservedLaneActivationError("Planck pipeline contract drifted")
    data = spec.get("data_identity_contract")
    if not isinstance(data, Mapping) or (
        data.get("lane_id") != "PLANCK"
        or data.get("product_id") != "PLANCK_PR3_LOWELL_BUNDLE"
        or data.get("registry_path") != _PR289_REGISTRY_REL.as_posix()
        or data.get("registry_content_id")
        != _EXPECTED_PR289_REGISTRY_CONTENT_ID
        or tuple(data.get("required_source_binding_paths", ()))
        != _PR289_REQUIRED_SOURCE_PATHS
        or data.get("required_analysis_plan_id")
        != "plan:PR290-PLANCK-LOWELL-V1"
        or data.get("required_admission_status") != "ADMITTED_IDENTITY_ONLY"
        or tuple(data.get("required_components", ()))
        != _EXPECTED_PLANCK_COMPONENTS
        or data.get("required_native_identity_schema")
        != "common.planck_native_identity.v1"
        or data.get("canonical_record_replay") != "required"
    ):
        raise ObservedLaneActivationError("Planck identity contract drifted")
    human = spec.get("human_execution_gate")
    if not isinstance(human, Mapping) or (
        human.get("gate_id") != "H-PLANCK"
        or human.get("receipt_path") != _AUTH_REL.as_posix()
        or human.get("receipt_schema") != HUMAN_AUTHORIZATION_SCHEMA
        or human.get("authorized_scope")
        != "admitted_planck_observed_execution"
        or human.get("authority_key_id") != "H-PLANCK-OWNER-HMAC-V1"
        or human.get("key_path_environment_variable")
        != "HTT_H_PLANCK_AUTHORITY_KEY_FILE"
        or human.get("max_authorization_ttl_seconds") != 1800
    ):
        raise ObservedLaneActivationError("H-PLANCK authorization contract drifted")
    output = spec.get("output_contract")
    if not isinstance(output, Mapping) or (
        output.get("preactivation_receipt")
        != (
            "docs/research_program/post_pr275/data_runs/planck/"
            "PR290_NONEXECUTION_RECEIPT.json"
        )
        or output.get("observed_result_directory")
        != "docs/research_program/post_pr275/data_runs/planck/results"
        or tuple(output.get("current_allowed_outputs", ()))
        != _EXPECTED_CURRENT_ALLOWED_OUTPUTS
        or tuple(output.get("current_forbidden_outputs", ()))
        != _EXPECTED_CURRENT_FORBIDDEN_OUTPUTS
    ):
        raise ObservedLaneActivationError("nonexecution output contract drifted")
    future = output.get("future_observed_result_contract")
    if not isinstance(future, Mapping) or (
        future.get("current_status") != "DISABLED_PREACTIVATION"
        or future.get("schema") != "htt.pr290.planck_observed_result.v1"
        or tuple(future.get("required_metadata", ()))
        != _EXPECTED_FUTURE_RESULT_METADATA
        or future.get("activation_rule")
        != (
            "unreachable until the schema validator and negative tests are "
            "implemented"
        )
    ):
        raise ObservedLaneActivationError("future observed-result contract drifted")
    if tuple(spec.get("allowed_uses", ())) != _EXPECTED_ALLOWED_USES:
        raise ObservedLaneActivationError("allowed-use boundary drifted")
    if tuple(spec.get("forbidden_uses", ())) != _EXPECTED_FORBIDDEN_USES:
        raise ObservedLaneActivationError("forbidden-use boundary drifted")
    if spec.get("artifact_ownership") != _EXPECTED_ARTIFACT_OWNERSHIP:
        raise ObservedLaneActivationError("artifact ownership drifted")
    if tuple(spec.get("terminal_precedence", ())) != _EXPECTED_TERMINALS:
        raise ObservedLaneActivationError("terminal precedence drifted")


def _terminal_receipt_snapshot(
    *, root: Path, pr_id: str, expected_terminal: str
) -> tuple[dict[str, object], tuple[str, ...]]:
    relative, expected_schema, content_field = _EXPECTED_TERMINAL_RECEIPTS[pr_id]
    reasons: list[str] = []
    try:
        path = _regular_file_within(
            root, relative, label=f"{pr_id} terminal receipt"
        )
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
    if payload.get("schema") != expected_schema:
        reasons.append(f"{pr_id}: terminal receipt schema mismatch")
    if payload.get("terminal") != expected_terminal:
        reasons.append(f"{pr_id}: terminal receipt token mismatch")
    observed_content = payload.get(content_field)
    unsigned = dict(payload)
    unsigned.pop(content_field, None)
    expected_content = "sha256:" + hashlib.sha256(
        canonical_json_bytes(unsigned)
    ).hexdigest()
    if observed_content != expected_content:
        reasons.append(f"{pr_id}: terminal receipt content identity mismatch")
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


def _validate_pr289_receipt_provenance(
    *, root: Path, identity: Mapping[str, object]
) -> None:
    source_bindings = identity.get("source_bindings")
    if not isinstance(source_bindings, Mapping) or set(source_bindings) != set(
        _PR289_REQUIRED_SOURCE_PATHS
    ):
        raise ObservedLaneActivationError(
            "PR-289 source binding inventory drifted"
        )
    for relative in _PR289_REQUIRED_SOURCE_PATHS:
        path = _regular_file_within(
            root,
            Path(relative),
            label=f"PR-289 source binding {relative}",
        )
        declared = _normalize_digest(
            source_bindings.get(relative),
            label=f"PR-289 source binding {relative}",
        )
        if declared != _sha256_file(path):
            raise ObservedLaneActivationError(
                f"PR-289 source binding mismatch: {relative}"
            )

    registry_path = _regular_file_within(
        root, _PR289_REGISTRY_REL, label="PR-289 lane registry"
    )
    registry = _strict_json(registry_path, label="PR-289 lane registry")
    registry_content_id = "sha256:" + hashlib.sha256(
        canonical_json_bytes(registry)
    ).hexdigest()
    if registry_content_id != _EXPECTED_PR289_REGISTRY_CONTENT_ID:
        raise ObservedLaneActivationError(
            "canonical PR-289 registry content identity drifted"
        )
    if identity.get("registry_content_id") != registry_content_id:
        raise ObservedLaneActivationError(
            "PR-289 receipt registry content identity mismatch"
        )


def _dependency_snapshot(
    spec: Mapping[str, object], status: Mapping[str, object], *, root: Path
) -> tuple[tuple[dict[str, object], ...], tuple[str, ...]]:
    dependency = spec["dependency_contract"]
    assert isinstance(dependency, Mapping)
    required_terminals = dependency.get("required_terminals", {})
    if not isinstance(required_terminals, Mapping):
        raise ObservedLaneActivationError("required predecessor terminals are invalid")
    completed = status.get("completed", ())
    resolutions = status.get("execution_resolutions", {})
    if not isinstance(completed, Sequence) or isinstance(completed, (str, bytes)):
        raise ObservedLaneActivationError("canonical completed inventory is invalid")
    if not isinstance(resolutions, Mapping):
        raise ObservedLaneActivationError("execution resolutions are invalid")
    rows: list[dict[str, object]] = []
    all_reasons: list[str] = []
    for pr_id in _EXPECTED_PREDECESSORS:
        reasons: list[str] = []
        row = resolutions.get(pr_id)
        if not isinstance(row, Mapping):
            row = {}
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
        expected_terminal = required_terminals.get(pr_id)
        if expected_terminal is not None and not isinstance(expected_terminal, str):
            raise ObservedLaneActivationError(
                f"{pr_id}: required terminal must be a string"
            )
        terminal_receipt: dict[str, object] | None = None
        if expected_terminal is not None and not reasons:
            if row.get("terminal") != expected_terminal:
                reasons.append(f"{pr_id}: canonical terminal token mismatch")
            terminal_receipt, terminal_reasons = _terminal_receipt_snapshot(
                root=root,
                pr_id=pr_id,
                expected_terminal=expected_terminal,
            )
            reasons.extend(terminal_reasons)
        rows.append(
            {
                "pr_id": pr_id,
                "resolution": row.get("resolution"),
                "candidate_sha": candidate_sha,
                "required_terminal": expected_terminal,
                "canonical_terminal": row.get("terminal"),
                "terminal_receipt": terminal_receipt,
                "success_dependency_satisfied": row.get(
                    "success_dependency_satisfied"
                ),
                "observed_data_executed": row.get("observed_data_executed"),
                "public_use": row.get("public_use"),
                "satisfied": not reasons,
                "reasons": reasons,
            }
        )
        all_reasons.extend(reasons)
    return tuple(rows), tuple(all_reasons)


def _load_pr289_identity_module(
    *, root: Path, identity: Mapping[str, object]
) -> object:
    source_bindings = identity.get("source_bindings")
    if not isinstance(source_bindings, Mapping):
        raise ObservedLaneActivationError(
            "PR-289 receipt source bindings are malformed"
        )
    relative = Path("htt/src/common/data_identity.py")
    module_path = _regular_file_within(
        root, relative, label="PR-289 data identity module"
    )
    expected_sha = _normalize_digest(
        source_bindings.get(relative.as_posix()),
        label="PR-289 data identity module binding",
    )
    if _sha256_file(module_path) != expected_sha:
        raise ObservedLaneActivationError(
            "PR-289 data identity module bytes differ from the receipt"
        )
    module_name = "_htt_pr290_data_identity_" + hashlib.sha256(
        (str(module_path.resolve()) + expected_sha).encode("utf-8")
    ).hexdigest()
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    if module_spec is None or module_spec.loader is None:
        raise ObservedLaneActivationError(
            "PR-289 data identity module loader is unavailable"
        )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules.pop(module_name, None)
    sys.modules[module_name] = module
    try:
        module_spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise ObservedLaneActivationError(
            "PR-289 data identity module execution failed"
        ) from exc
    expected_origin = module_path.resolve()
    required_symbols = (
        "load_lane_registry",
        "replay_lane_admission_decision",
        "build_not_authorized_receipt",
    )
    if (
        Path(str(getattr(module, "__file__", ""))).resolve()
        != expected_origin
        or _sha256_file(module_path) != expected_sha
        or any(
            not callable(getattr(module, symbol, None))
            or Path(getattr(module, symbol).__code__.co_filename).resolve()
            != expected_origin
            for symbol in required_symbols
        )
    ):
        sys.modules.pop(module_name, None)
        raise ObservedLaneActivationError(
            "PR-289 data identity module origin or bytes drifted"
        )
    return module


def _planck_identity_snapshot(
    *,
    root: Path,
    spec: Mapping[str, object],
    identity: Mapping[str, object],
) -> tuple[dict[str, object], tuple[str, ...]]:
    data = spec["data_identity_contract"]
    assert isinstance(data, Mapping)
    decisions = identity.get("lane_decisions")
    authorizations = identity.get("authorization_receipts")
    if not isinstance(decisions, list) or not isinstance(authorizations, list):
        raise ObservedLaneActivationError("PR-289 receipt inventories are invalid")
    decision_rows = [
        row
        for row in decisions
        if isinstance(row, Mapping) and row.get("lane_id") == "PLANCK"
    ]
    authorization_rows = [
        row
        for row in authorizations
        if isinstance(row, Mapping) and row.get("lane_id") == "PLANCK"
    ]
    if len(decision_rows) != 1 or len(authorization_rows) != 1:
        raise ObservedLaneActivationError("PLANCK receipt row is missing or duplicated")
    decision = decision_rows[0]
    authorization = authorization_rows[0]
    reasons: list[str] = []
    if decision.get("product_id") != data.get("product_id"):
        reasons.append("PLANCK product identity differs from the specification")
    if decision.get("status") != data.get("required_admission_status"):
        reasons.append("PLANCK identity is not ADMITTED_IDENTITY_ONLY")
    replayed = None
    expected_authorization = None
    try:
        identity_module = _load_pr289_identity_module(
            root=root, identity=identity
        )
        registry_path = _regular_file_within(
            root, _PR289_REGISTRY_REL, label="PR-289 lane registry"
        )
        registry = identity_module.load_lane_registry(registry_path)
        replayed = identity_module.replay_lane_admission_decision(
            decision, registry=registry
        )
        if replayed.as_payload() != dict(decision):
            raise ObservedLaneActivationError(
                "PLANCK admission payload is not canonical after replay"
            )
        lane = registry.lane("PLANCK")
        expected_authorization = identity_module.build_not_authorized_receipt(
            lane, replayed
        ).as_payload()
    except Exception as exc:
        reasons.append(f"PLANCK canonical native-record replay failed: {exc}")

    record_ids: list[str] = []
    component_ids: list[str] = []
    native_profile_ids: set[str] = set()
    normalized_bundle = None
    if replayed is not None:
        record_ids = [record.record_id for record in replayed.records]
        component_ids = [record.component_id for record in replayed.records]
        native_profile_ids = {
            record.native_identity_profile_id for record in replayed.records
        }
        normalized_bundle = replayed.lane_admission_bundle_id
        if tuple(component_ids) not in ((), _EXPECTED_PLANCK_COMPONENTS):
            reasons.append("PLANCK canonical native component inventory drifted")
        if record_ids and (
            len(native_profile_ids) != 1
            or any(
                record.native_identity_profile.get("schema")
                != "common.planck_native_identity.v1"
                for record in replayed.records
            )
        ):
            reasons.append("PLANCK canonical native profile identity drifted")
    if not record_ids:
        reasons.append("PLANCK exact admission record IDs are absent")
    if (
        authorization.get("analysis_plan_id")
        != data.get("required_analysis_plan_id")
        or authorization.get("required_human_gate_id") != "H-PLANCK"
    ):
        reasons.append("PR-289 authorization identity differs from PR-290")
    if tuple(authorization.get("exact_admission_record_ids", ())) != tuple(record_ids):
        reasons.append("PR-289 authorization record IDs differ from admission")
    if expected_authorization is None or dict(authorization) != expected_authorization:
        reasons.append(
            "PR-289 authorization is not the canonical native admission projection"
        )
    snapshot = {
        "receipt_schema": identity.get("schema"),
        "aggregate_status": identity.get("aggregate_status"),
        "lane_id": "PLANCK",
        "product_id": decision.get("product_id"),
        "admission_status": decision.get("status"),
        "lane_admission_bundle_id": normalized_bundle,
        "record_ids": record_ids,
        "record_count": len(record_ids),
        "component_ids": component_ids,
        "native_identity_profile_ids": sorted(native_profile_ids),
        "canonical_record_replay": replayed is not None,
        "pr289_authorization_status": authorization.get("status"),
        "analysis_plan_id": authorization.get("analysis_plan_id"),
        "required_human_gate_id": authorization.get("required_human_gate_id"),
        "satisfied": not reasons,
        "reasons": reasons,
    }
    return snapshot, tuple(reasons)


def _external_key_path(
    human: Mapping[str, object], explicit: Path | None
) -> Path | None:
    if explicit is not None:
        return Path(explicit)
    environment_name = human.get("key_path_environment_variable")
    if not isinstance(environment_name, str):
        return None
    value = os.environ.get(environment_name)
    return Path(value) if value else None


def _verify_external_human_authorization(
    *,
    root: Path,
    spec: Mapping[str, object],
    status: Mapping[str, object],
    identity_snapshot: Mapping[str, object],
    authority_key_path: Path | None,
    evaluated_at_utc: str,
) -> tuple[dict[str, object], tuple[str, ...]]:
    human = spec["human_execution_gate"]
    assert isinstance(human, Mapping)
    reasons: list[str] = []
    status_events = status.get("external_events", {})
    status_row = (
        status_events.get("H-PLANCK", {})
        if isinstance(status_events, Mapping)
        else {}
    )
    status_value = status_row.get("status") if isinstance(status_row, Mapping) else None
    receipt_path = _optional_regular_file_within(
        root, _AUTH_REL, label="H-PLANCK authorization receipt"
    )
    trusted_digest = human.get("trusted_hmac_key_sha256")
    if trusted_digest is None:
        reasons.append("H-PLANCK trusted HMAC key is unprovisioned")
    elif not isinstance(trusted_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", trusted_digest
    ):
        reasons.append("H-PLANCK trusted HMAC key digest is invalid")
    key_path = _external_key_path(human, authority_key_path)
    if key_path is None:
        reasons.append("H-PLANCK external authority key is unavailable")
    if receipt_path is None:
        reasons.append("H-PLANCK authorization receipt is missing")
    if reasons:
        return (
            {
                "gate_id": "H-PLANCK",
                "canonical_status": status_value,
                "status": "NOT_AUTHORIZED",
                "receipt_path": _AUTH_REL.as_posix(),
                "receipt_sha256": None,
                "satisfied": False,
                "reasons": reasons,
            },
            tuple(reasons),
        )
    assert key_path is not None and receipt_path is not None
    if not key_path.is_absolute():
        reasons.append("H-PLANCK authority key path must be absolute")
        key = b""
    else:
        try:
            metadata = key_path.lstat()
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
            ):
                raise OSError
            resolved_key = key_path.resolve(strict=True)
            if resolved_key.is_relative_to(root):
                reasons.append("H-PLANCK authority key must remain outside repository")
                key = b""
            else:
                key = key_path.read_bytes()
        except OSError:
            reasons.append("H-PLANCK authority key must be a single-link regular file")
            key = b""
    if key and hashlib.sha256(key).hexdigest() != trusted_digest:
        reasons.append("H-PLANCK authority key digest mismatch")
    try:
        receipt = _strict_json(receipt_path, label="H-PLANCK authorization receipt")
    except ObservedLaneActivationError as exc:
        reasons.append(str(exc))
        receipt = {}
    if receipt and frozenset(receipt) != _HUMAN_FIELDS:
        reasons.append("H-PLANCK authorization field inventory drifted")
    unsigned = {
        key_name: value
        for key_name, value in receipt.items()
        if key_name != "authorization_hmac_sha256"
    }
    observed_hmac = receipt.get("authorization_hmac_sha256")
    if (
        not isinstance(observed_hmac, str)
        or re.fullmatch(r"[0-9a-f]{64}", observed_hmac) is None
        or not key
        or not hmac.compare_digest(
            observed_hmac,
            hmac.new(key, canonical_json_bytes(unsigned), hashlib.sha256).hexdigest(),
        )
    ):
        reasons.append("H-PLANCK authorization HMAC verification failed")
    exact_values = {
        "schema": HUMAN_AUTHORIZATION_SCHEMA,
        "status": "AUTHORIZED",
        "lane_id": "PLANCK",
        "gate_id": "H-PLANCK",
        "analysis_plan_id": "plan:PR290-PLANCK-LOWELL-V1",
        "authorized_scope": "admitted_planck_observed_execution",
        "authority_key_id": "H-PLANCK-OWNER-HMAC-V1",
        "authorization_domain": "lane_data_execution",
    }
    for field_name, expected in exact_values.items():
        if receipt.get(field_name) != expected:
            reasons.append(f"H-PLANCK authorization {field_name} mismatch")
    if status_value != "AUTHORIZED":
        reasons.append("canonical H-PLANCK status is not AUTHORIZED")
    if receipt.get("lane_admission_bundle_id") != identity_snapshot.get(
        "lane_admission_bundle_id"
    ):
        reasons.append("H-PLANCK admission bundle mismatch")
    if tuple(receipt.get("exact_admission_record_ids", ())) != tuple(
        identity_snapshot.get("record_ids", ())
    ):
        reasons.append("H-PLANCK admission record IDs mismatch")
    authority_identity = receipt.get("human_authority_identity")
    if not isinstance(authority_identity, str) or not authority_identity.strip():
        reasons.append("H-PLANCK human authority identity is absent")
    nonce = receipt.get("nonce")
    if not isinstance(nonce, str) or len(nonce) < 16:
        reasons.append("H-PLANCK nonce is absent or too short")
    try:
        issued = _parse_utc(receipt.get("issued_at_utc"), label="issued_at_utc")
        expires = _parse_utc(receipt.get("expires_at_utc"), label="expires_at_utc")
        evaluated = _parse_utc(evaluated_at_utc, label="evaluated_at_utc")
        ttl = (expires - issued).total_seconds()
        if ttl <= 0 or ttl > int(human["max_authorization_ttl_seconds"]):
            reasons.append("H-PLANCK authorization TTL exceeds the frozen limit")
        if issued > evaluated:
            reasons.append("H-PLANCK authorization is not yet valid")
        if evaluated >= expires:
            reasons.append("H-PLANCK authorization is expired")
    except ObservedLaneActivationError as exc:
        reasons.append(str(exc))
    snapshot = {
        "gate_id": "H-PLANCK",
        "canonical_status": status_value,
        "status": "AUTHORIZED_VERIFIED" if not reasons else "NOT_AUTHORIZED",
        "receipt_path": _AUTH_REL.as_posix(),
        "receipt_sha256": _sha256_file(receipt_path),
        "authority_key_id": receipt.get("authority_key_id"),
        "human_authority_identity": authority_identity,
        "issued_at_utc": receipt.get("issued_at_utc"),
        "expires_at_utc": receipt.get("expires_at_utc"),
        "nonce": nonce,
        "satisfied": not reasons,
        "reasons": reasons,
    }
    return snapshot, tuple(reasons)


def _operator_snapshot(spec: Mapping[str, object]) -> dict[str, object]:
    pipeline = spec.get("pipeline_contract")
    if not isinstance(pipeline, Mapping):
        raise ObservedLaneActivationError("pipeline contract is missing")
    readiness = pipeline.get("implementation_readiness")
    if not isinstance(readiness, Mapping):
        raise ObservedLaneActivationError("pipeline readiness contract is missing")
    required = _EXPECTED_IMPLEMENTATION_READINESS
    for field_name, expected in required.items():
        if readiness.get(field_name) != expected:
            raise ObservedLaneActivationError(
                f"pipeline readiness {field_name} drifted"
            )
    return {
        **required,
        "response_and_active_estimand_status": dict(
            _EXPECTED_ACTIVE_ESTIMAND_STATUS
        ),
        "status": "BLOCKED_OPERATOR_IMPLEMENTATION",
        "satisfied": False,
    }


@dataclass(frozen=True)
class PlanckActivationDecision:
    terminal: str
    reasons: tuple[str, ...]
    dependency_snapshot: tuple[dict[str, object], ...]
    data_identity_snapshot: dict[str, object]
    human_gate_snapshot: dict[str, object]
    operator_snapshot: dict[str, object]
    spec_content_id: str
    status_content_id: str
    data_identity_content_id: str
    numeric_outputs_written: tuple[str, ...] = ()
    observed_data_executed: bool = False
    network_or_download_side_effect: bool = False
    _construction_token: InitVar[object] = None
    _seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DECISION_TOKEN:
            raise ObservedLaneActivationError(
                "PlanckActivationDecision must be factory-derived"
            )
        if self.terminal not in _EXPECTED_TERMINALS:
            raise ObservedLaneActivationError("activation terminal is unregistered")
        if (
            self.numeric_outputs_written
            or self.observed_data_executed is not False
            or self.network_or_download_side_effect is not False
        ):
            raise ObservedLaneActivationError(
                "preactivation decision cannot carry execution side effects"
            )
        if self.terminal.startswith("BLOCKED_") and not self.reasons:
            raise ObservedLaneActivationError("blocked activation needs explicit reasons")
        object.__setattr__(
            self,
            "_seal",
            hashlib.sha256(canonical_json_bytes(self._unsigned_payload())).hexdigest(),
        )

    def _unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": SCHEMA_VERSION,
            "terminal": self.terminal,
            "reasons": list(self.reasons),
            "dependency_snapshot": [dict(row) for row in self.dependency_snapshot],
            "data_identity_snapshot": dict(self.data_identity_snapshot),
            "human_gate_snapshot": dict(self.human_gate_snapshot),
            "operator_snapshot": dict(self.operator_snapshot),
            "spec_content_id": self.spec_content_id,
            "status_content_id": self.status_content_id,
            "data_identity_content_id": self.data_identity_content_id,
            "numeric_outputs_written": list(self.numeric_outputs_written),
            "observed_data_executed": self.observed_data_executed,
            "network_or_download_side_effect": self.network_or_download_side_effect,
        }

    def as_payload(self) -> dict[str, object]:
        payload = self._unsigned_payload()
        if hashlib.sha256(canonical_json_bytes(payload)).hexdigest() != self._seal:
            raise ObservedLaneActivationError("activation decision identity drifted")
        return payload


def build_planck_activation_decision(
    *,
    repository_root: Path,
    authority_key_path: Path | None = None,
    evaluated_at_utc: str = "2026-08-09T00:00:00+00:00",
) -> PlanckActivationDecision:
    """Evaluate all PR-290 gates without importing OBSSTAT or touching output paths."""

    root = _repository_root(repository_root)
    spec_path = _regular_file_within(root, _SPEC_REL, label="PR-290 spec")
    status_path = _regular_file_within(root, _STATUS_REL, label="canonical status")
    identity_path = _regular_file_within(
        root, _IDENTITY_REL, label="PR-289 identity receipt"
    )
    try:
        spec = _yaml_mapping(spec_path, label="PR-290 spec")
        _validate_spec(spec)
        status = _yaml_mapping(status_path, label="canonical status")
        identity = _strict_json(identity_path, label="PR-289 identity receipt")
        _validate_pr289_receipt_provenance(root=root, identity=identity)
        dependencies, dependency_reasons = _dependency_snapshot(
            spec, status, root=root
        )
        identity_snapshot, identity_reasons = _planck_identity_snapshot(
            root=root, spec=spec, identity=identity
        )
        if identity_reasons:
            status_events = status.get("external_events", {})
            status_row = (
                status_events.get("H-PLANCK", {})
                if isinstance(status_events, Mapping)
                else {}
            )
            human_snapshot = {
                "gate_id": "H-PLANCK",
                "canonical_status": (
                    status_row.get("status")
                    if isinstance(status_row, Mapping)
                    else None
                ),
                "status": "NOT_AUTHORIZED",
                "receipt_path": _AUTH_REL.as_posix(),
                "receipt_sha256": None,
                "satisfied": False,
                "reasons": ["PLANCK admission must precede authorization"],
            }
            human_reasons = tuple(human_snapshot["reasons"])
        else:
            human_snapshot, human_reasons = _verify_external_human_authorization(
                root=root,
                spec=spec,
                status=status,
                identity_snapshot=identity_snapshot,
                authority_key_path=authority_key_path,
                evaluated_at_utc=evaluated_at_utc,
            )
        operator_snapshot = _operator_snapshot(spec)
        if dependency_reasons:
            terminal = "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
            reasons = dependency_reasons
        elif identity_reasons:
            terminal = "BLOCKED_DATA_IDENTITY_ADMISSION"
            reasons = identity_reasons
        elif human_reasons:
            terminal = "BLOCKED_HUMAN_EXECUTION_AUTHORIZATION"
            reasons = human_reasons
        elif not operator_snapshot["satisfied"]:
            terminal = "BLOCKED_OPERATOR_IMPLEMENTATION"
            reasons = tuple(
                f"{key}: {value}"
                for key, value in operator_snapshot.items()
                if key not in {"status", "satisfied"}
            )
        else:  # pragma: no cover - current preactivation intentionally unreachable
            terminal = "READY_FOR_ATTENDED_PLANCK_EXECUTION"
            reasons = ()
    except ObservedLaneActivationError as exc:
        return PlanckActivationDecision(
            terminal="BLOCKED_CONTRACT_INVALID",
            reasons=(str(exc),),
            dependency_snapshot=(),
            data_identity_snapshot={"satisfied": False, "reasons": [str(exc)]},
            human_gate_snapshot={"satisfied": False, "reasons": [str(exc)]},
            operator_snapshot={"satisfied": False, "reasons": [str(exc)]},
            spec_content_id=_sha256_file(spec_path),
            status_content_id=_sha256_file(status_path),
            data_identity_content_id=_sha256_file(identity_path),
            _construction_token=_DECISION_TOKEN,
        )
    return PlanckActivationDecision(
        terminal=terminal,
        reasons=tuple(reasons),
        dependency_snapshot=dependencies,
        data_identity_snapshot=identity_snapshot,
        human_gate_snapshot=human_snapshot,
        operator_snapshot=operator_snapshot,
        spec_content_id=_sha256_file(spec_path),
        status_content_id=_sha256_file(status_path),
        data_identity_content_id=_sha256_file(identity_path),
        _construction_token=_DECISION_TOKEN,
    )


def build_planck_nonexecution_receipt(
    *,
    decision: PlanckActivationDecision,
    source_bindings: Mapping[str, str],
    generation_identity: Mapping[str, object],
) -> dict[str, object]:
    """Build the claim-safe receipt for one blocked PR-290 preactivation."""

    if type(decision) is not PlanckActivationDecision:
        raise ObservedLaneActivationError("decision must be factory-derived")
    decision.as_payload()
    if decision.terminal in {
        "READY_FOR_ATTENDED_PLANCK_EXECUTION",
        "PASS_PLANCK_OBSERVED_LANE_REBOOT",
    }:
        raise ObservedLaneActivationError("a nonexecution receipt requires a blocker")
    if not source_bindings:
        raise ObservedLaneActivationError("source bindings must be non-empty")
    normalized_bindings: dict[str, str] = {}
    for relative, digest in source_bindings.items():
        if not isinstance(relative, str):
            raise ObservedLaneActivationError("source binding path is invalid")
        path = Path(relative)
        if (
            path.is_absolute()
            or ".." in path.parts
            or relative in normalized_bindings
        ):
            raise ObservedLaneActivationError("source binding path is invalid")
        normalized_bindings[relative] = _normalize_digest(
            digest, label=f"source binding {relative}"
        )
    expected_sources = set(REQUIRED_NONEXECUTION_SOURCE_PATHS)
    for row in decision.dependency_snapshot:
        terminal_receipt = row.get("terminal_receipt")
        if isinstance(terminal_receipt, Mapping) and terminal_receipt.get(
            "file_sha256"
        ) is not None:
            path = terminal_receipt.get("path")
            if isinstance(path, str):
                expected_sources.add(path)
    if set(normalized_bindings) != expected_sources:
        raise ObservedLaneActivationError("source binding inventory drifted")
    if frozenset(generation_identity) != _EXPECTED_GENERATION_FIELDS:
        raise ObservedLaneActivationError("generation identity field inventory drifted")
    source_identity = _normalize_digest(
        generation_identity.get("source_commit_or_external_candidate_seal_id"),
        label="generation source identity",
    )
    if generation_identity.get("worktree_state") != (
        "source_hash_bound_dirty_or_committed"
    ):
        raise ObservedLaneActivationError("generation worktree state drifted")
    if generation_identity.get("exact_replay_environment") != (
        "repository_python_contract"
    ):
        raise ObservedLaneActivationError("generation replay environment drifted")
    normalized_generation = {
        "source_commit_or_external_candidate_seal_id": source_identity,
        "worktree_state": "source_hash_bound_dirty_or_committed",
        "exact_replay_environment": "repository_python_contract",
    }
    payload: dict[str, object] = {
        "schema": NONEXECUTION_RECEIPT_SCHEMA,
        "pr_id": "PR-290",
        "terminal": decision.terminal,
        "reasons": list(decision.reasons),
        "dependency_snapshot": [dict(row) for row in decision.dependency_snapshot],
        "data_identity_snapshot": dict(decision.data_identity_snapshot),
        "human_gate_snapshot": dict(decision.human_gate_snapshot),
        "operator_snapshot": dict(decision.operator_snapshot),
        "numeric_outputs_written": [],
        "observed_data_executed": False,
        "network_or_download_side_effect": False,
        "owner_scope_and_claim_boundary": {
            "delivery_owner": "HTT",
            "artifact_owners": {
                "observable_features_and_null_features": "OBSSTAT",
                "activation_manifests_and_semantic_guards": "COMMON",
                "model_dependent_inference": "HTT_NOT_EXECUTED",
            },
            "scope": "Planck preactivation nonexecution only",
            "claim_tier": "diagnostic_only",
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
            "scientific_artifact_mode": "preactivation_nonexecution",
            "transfer_source": "none",
            "sky_support_status": "NOT_READ",
            "covariance_status": "NOT_EVALUATED",
            "null_mock_status": "NOT_EXECUTED",
            "allowed_uses": [
                "fail-closed preactivation diagnostics",
                "synthetic contract tests",
            ],
            "forbidden_uses": [
                "observed numerical result",
                "public scientific use",
                "native transfer or solver validation",
                "anisotropy source or Bianchi-family claim",
            ],
            "caveats": [
                "identity admission and H-PLANCK authorization are separate",
                "mask deconvolution and multipole-vector extraction remain blocked",
                "PR-151 partial acquisition is not an input",
            ],
        },
        "generation_identity": normalized_generation,
        "generating_procedure": (
            "python3 -B scripts/codex_harness/run_pr290_planck_lane.py build"
        ),
        "source_bindings": dict(sorted(normalized_bindings.items())),
        "spec_content_id": decision.spec_content_id,
        "status_content_id": decision.status_content_id,
        "data_identity_content_id": decision.data_identity_content_id,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    payload["receipt_content_sha256"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    return payload


__all__ = [
    "HUMAN_AUTHORIZATION_SCHEMA",
    "NONEXECUTION_RECEIPT_SCHEMA",
    "REQUIRED_NONEXECUTION_SOURCE_PATHS",
    "ObservedLaneActivationError",
    "PlanckActivationDecision",
    "build_planck_activation_decision",
    "build_planck_nonexecution_receipt",
    "canonical_json_bytes",
]
