"""Synthetic full-covariance MES covariance/BiPoSH branch harness.

This module builds a COMMON-owned diagnostic-only ``FullCovMESReport`` for a
caller-supplied covariance/BiPoSH response branch.  It consumes OBSSTAT feature
and null provenance metadata, computes a whitened nuisance-projected response
rank, and emits no HTT likelihood/evidence or MIO certificate content.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any

import numpy as np

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    FullCovMESReport,
    ImplementationScope,
    Owner,
)
from obsstat.null_ensembles import validate_null_feature_payload

__all__ = ["MesCovarianceBoundResult", "build_mes_covariance_bound"]


SCHEMA_VERSION = "htt.statistics.mes_cov_bound.v1"
_CREATED_BY = "htt.statistics.mes_cov_bound.build_mes_covariance_bound"
_DEFAULT_ARTIFACT_PATH = "memory://htt.statistics/mes-covariance-bound"
_DEFAULT_CAVEAT = (
    "COMMON diagnostic-only synthetic covariance/BiPoSH MES branch; keeps the "
    "diagonal MES baseline separate"
)
_REQUIRED_GATES = (
    "full_covariance_supplied",
    "biposh_feature_payload_supplied",
    "typed_null_feature_payload",
    "nuisance_projected_response_rank_sufficient",
    "diagonal_mes_baseline_preserved",
    "no_geometry_or_family_claim",
)
_FORBIDDEN_TEXT_PARTS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "certificate",
    "truth",
    "native solver result",
    "native validation",
    "transfer validated",
    "strictly stronger",
    "replaces diagonal",
    "full covariance " + "mes theorem",
    "universal " + "mes",
    "geometry detected",
    "detected geometry",
    "family identified",
    "family " + "identification",
    "family ranking",
    "morphology compatibility",
)


@dataclass(frozen=True)
class MesCovarianceBoundResult:
    """Diagnostic wrapper around a synthetic covariance/BiPoSH MES report."""

    report: FullCovMESReport
    biposh_feature_payload: Mapping[str, Any] | None
    null_feature_payload: Mapping[str, Any] | None
    synthetic_bound_available: bool
    no_claim_reasons: tuple[str, ...]
    covariance_bound: float | None
    projected_rank: int
    raw_rank: int
    nuisance_rank: int
    rank_threshold: float
    raw_singular_values: tuple[float, ...]
    nuisance_singular_values: tuple[float, ...]
    projected_response_norms: tuple[float, ...]
    condition_number: float | None
    branch_status: str

    def as_payload(self) -> dict[str, Any]:
        definitions = self.report.manifest.statistics_definitions
        null_ref = None
        if self.null_feature_payload is not None:
            null_ref = {
                "null_ensemble_ref": self.null_feature_payload.get("null_ensemble_ref"),
                "look_elsewhere_status": self.null_feature_payload.get(
                    "look_elsewhere_status"
                ),
                "scan_volume_hash": self.null_feature_payload.get("scan_volume_hash"),
                "mock_count": self.null_feature_payload.get("mock_count"),
                "statistic_keys": list(
                    self.null_feature_payload.get("statistic_keys", ())
                ),
                "feature_targets": list(
                    self.null_feature_payload.get("feature_targets", ())
                ),
            }
        biposh_ref = None
        if self.biposh_feature_payload is not None:
            biposh_ref = {
                "entry_hash": self.biposh_feature_payload.get("entry_hash"),
                "representation": self.biposh_feature_payload.get("representation"),
                "model_role": self.biposh_feature_payload.get("model_role"),
                "statistic_role": self.biposh_feature_payload.get("statistic_role"),
                "transfer_source": self.biposh_feature_payload.get("transfer_source"),
                "covariance_status": self.biposh_feature_payload.get(
                    "covariance_status"
                ),
                "null_mock_status": self.biposh_feature_payload.get(
                    "null_mock_status"
                ),
                "norm_summary": self.biposh_feature_payload.get("norm_summary"),
            }
        return _json_ready(
            {
                "owner": Owner.COMMON.value,
                "implementation_scope": ImplementationScope.COMMON.value,
                "claim_tier": self.report.manifest.claim_tier.value,
                "production_status": self.report.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": _manifest_payload(self.report.manifest),
                "branch_role": "synthetic_covariance_biposh_mes_bound",
                "branch_status": self.branch_status,
                "synthetic_bound_available": self.synthetic_bound_available,
                "transfer_source": "none",
                "parameter_block": self.report.parameter_block,
                "diagonal_bound": self.report.diagonal_bound,
                "covariance_bound": self.report.covariance_bound,
                "dynamical_bound": self.report.dynamical_bound,
                "final_bound": self.report.final_bound,
                "information_gain": self.report.information_gain,
                "response_rank": self.report.response_rank,
                "required_response_rank": definitions.get("required_response_rank"),
                "rank_threshold": self.rank_threshold,
                "singular_values": list(self.report.singular_values),
                "raw_singular_values": list(self.raw_singular_values),
                "nuisance_singular_values": list(self.nuisance_singular_values),
                "projected_response_norms": list(self.projected_response_norms),
                "nuisance_rank": self.nuisance_rank,
                "condition_number": self.condition_number,
                "no_claim_reasons": list(self.no_claim_reasons),
                "generating_command": definitions.get("generating_command"),
                "git_commit": self.report.manifest.git_commit,
                "worktree_state": definitions.get("worktree_state"),
                "biposh_feature_ref": biposh_ref,
                "null_feature_ref": null_ref,
                "branch_separation": {
                    "template_mean_branch": "not_evaluated_by_this_module",
                    "covariance_branch": "synthetic_covariance_biposh_bound",
                    "does_not_replace_diagonal_mes": True,
                    "merged_statistic_allowed": False,
                },
                "claim_status": {
                    "inference_status": "not_model_input",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_result",
                    "geometry_status": "blocked_pre_native_atlas",
                    "family_status": "blocked_pre_native_atlas",
                },
                "caveats": list(self.report.manifest.caveats),
            }
        )


def build_mes_covariance_bound(
    *,
    response_vectors: Sequence[Sequence[object]],
    observable_labels: Sequence[object],
    response_labels: Sequence[object],
    full_covariance: Sequence[Sequence[object]] | None,
    diagonal_bound: object,
    rho_synthetic: object,
    parameter_block: object,
    biposh_feature_payload: Mapping[str, object] | None,
    null_feature_payload: Mapping[str, object] | None,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    worktree_state: object | None,
    sky_support_status: object,
    mask_status: object,
    look_elsewhere_trial_count: object,
    nuisance_responses: Sequence[Sequence[object]] = (),
    nuisance_labels: Sequence[object] = (),
    dynamical_bound: object | None = None,
    required_rank: object | None = None,
    rank_atol: object = 1.0e-12,
    rank_rtol: object = 0.0,
    artifact_id: object | None = None,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    git_commit: object | None = None,
    covariance_status: object = "full_positive_definite_covariance_supplied",
    null_mock_status: object = "synthetic_nulls_available",
    caveats: Sequence[object] = (_DEFAULT_CAVEAT,),
) -> MesCovarianceBoundResult:
    """Build a synthetic covariance/BiPoSH branch report with no-claim gates."""

    parameter_block_text = _non_empty(parameter_block, "parameter_block")
    _reject_overclaim_text(
        {
            "parameter_block": parameter_block_text,
            "artifact_id": artifact_id or "",
            "artifact_path": artifact_path,
            "generating_command": generating_command,
            "git_commit": git_commit or "",
            "worktree_state": worktree_state or "",
            "caveats": list(caveats),
        }
    )
    observable_label_tuple = _tuple_of_str(
        observable_labels,
        "observable_labels",
        require_non_empty=True,
    )
    response_label_tuple = _tuple_of_str(
        response_labels,
        "response_labels",
        require_non_empty=True,
    )
    response_matrix = _response_matrix(
        response_vectors,
        len(observable_label_tuple),
        "response_vectors",
    )
    if response_matrix.shape[1] != len(response_label_tuple):
        raise ValueError("response_labels length must match response_vectors")
    nuisance_matrix = _response_matrix(
        nuisance_responses,
        len(observable_label_tuple),
        "nuisance_responses",
        allow_empty=True,
    )
    nuisance_label_tuple = _tuple_of_str(nuisance_labels, "nuisance_labels")
    if nuisance_matrix.shape[1] and len(nuisance_label_tuple) != nuisance_matrix.shape[1]:
        raise ValueError("nuisance_labels length must match nuisance_responses")
    diagonal = _positive_finite(diagonal_bound, "diagonal_bound")
    rho = _positive_finite(rho_synthetic, "rho_synthetic")
    dyn_bound = (
        None
        if dynamical_bound is None
        else _positive_finite(dynamical_bound, "dynamical_bound")
    )
    rank_abs_tol = _nonnegative_finite(rank_atol, "rank_atol")
    rank_rel_tol = _nonnegative_finite(rank_rtol, "rank_rtol")
    config_hash_text = _require_hash(config_hash, "config_hash")
    input_hash_list = list(_require_input_hashes(input_hashes, "input_hashes"))
    command_text = _non_empty(generating_command, "generating_command")
    git_commit_text = None if git_commit is None else _non_empty(git_commit, "git_commit")
    worktree_text = (
        None if worktree_state is None else _non_empty(worktree_state, "worktree_state")
    )
    if git_commit_text is None and worktree_text is None:
        raise ValueError(
            "build_mes_covariance_bound requires git_commit or worktree_state"
        )
    sky_status = _non_empty(sky_support_status, "sky_support_status")
    mask_status_text = _non_empty(mask_status, "mask_status")
    covariance_status_text = _non_empty(covariance_status, "covariance_status")
    null_status_text = _non_empty(null_mock_status, "null_mock_status")
    trial_count = _positive_int(look_elsewhere_trial_count, "look_elsewhere_trial_count")
    caveat_list = tuple(_non_empty(item, "caveat") for item in caveats)
    _reject_overclaim_text(caveat_list)
    expected_rank = (
        response_matrix.shape[1]
        if required_rank is None
        else _positive_int(required_rank, "required_rank")
    )
    if expected_rank > response_matrix.shape[1]:
        raise ValueError("required_rank cannot exceed the number of response vectors")

    no_claim_reasons: list[str] = []
    covariance: np.ndarray | None = None
    if full_covariance is None:
        no_claim_reasons.append("missing_full_covariance")
    else:
        covariance = _covariance_matrix(full_covariance, len(observable_label_tuple))

    biposh_payload = _validate_biposh_payload(
        biposh_feature_payload,
        no_claim_reasons,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
        sky_support_status=sky_status,
        mask_status=mask_status_text,
        covariance_status=covariance_status_text,
        null_mock_status=null_status_text,
    )
    if biposh_payload is not None:
        _reject_overclaim_text(biposh_payload.get("source_metadata", {}))

    null_payload = _validate_null_payload(
        null_feature_payload,
        no_claim_reasons,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
        sky_support_status=sky_status,
        mask_status=mask_status_text,
        covariance_status=covariance_status_text,
        look_elsewhere_trial_count=trial_count,
        expected_observed_feature_ref=(
            None
            if biposh_payload is None
            else str(biposh_payload.get("entry_hash", ""))
        ),
    )
    if null_payload is not None:
        _reject_overclaim_text(null_payload)

    raw_rank = 0
    projected_rank = 0
    nuisance_rank = 0
    rank_threshold = rank_abs_tol
    raw_singular_values: tuple[float, ...] = ()
    projected_singular_values: tuple[float, ...] = ()
    nuisance_singular_values: tuple[float, ...] = ()
    projected_norms: tuple[float, ...] = ()
    condition_number: float | None = None
    covariance_bound: float | None = None
    if covariance is not None:
        whitening = _inverse_sqrt_covariance(covariance)
        white_response = whitening @ response_matrix
        white_nuisance = whitening @ nuisance_matrix
        projector, nuisance_rank, nuisance_singular_values = _nuisance_projector(
            white_nuisance,
            atol=rank_abs_tol,
            rtol=rank_rel_tol,
        )
        projected = projector @ white_response
        raw_singular = np.linalg.svd(white_response, compute_uv=False)
        projected_singular = np.linalg.svd(projected, compute_uv=False)
        raw_rank, _ = _rank_from_singular_values(
            raw_singular,
            atol=rank_abs_tol,
            rtol=rank_rel_tol,
        )
        projected_rank, rank_threshold = _rank_from_singular_values(
            projected_singular,
            atol=rank_abs_tol,
            rtol=rank_rel_tol,
        )
        raw_singular_values = tuple(float(value) for value in raw_singular)
        projected_singular_values = tuple(float(value) for value in projected_singular)
        projected_norms = tuple(float(value) for value in np.linalg.norm(projected, axis=0))
        positive_singular_values = [
            float(value) for value in projected_singular if float(value) > rank_threshold
        ]
        if projected_rank < expected_rank:
            no_claim_reasons.append("response_rank_deficient")
        if any(float(norm) <= rank_threshold for norm in projected_norms):
            no_claim_reasons.append("zero_projected_response")
        if projected_rank >= expected_rank and positive_singular_values:
            smallest_singular = min(positive_singular_values)
            covariance_bound = float(rho / smallest_singular)
            condition_number = float(max(positive_singular_values) / smallest_singular)
        else:
            covariance_bound = None
            condition_number = None

    no_claim_reasons = list(dict.fromkeys(no_claim_reasons))
    synthetic_bound_available = not no_claim_reasons
    if not synthetic_bound_available:
        covariance_bound = None
    candidate_bounds = [diagonal]
    if synthetic_bound_available:
        if dyn_bound is not None:
            candidate_bounds.append(dyn_bound)
        if covariance_bound is not None:
            candidate_bounds.append(covariance_bound)
    final_bound = min(candidate_bounds)
    information_gain = diagonal / final_bound if synthetic_bound_available else 1.0
    claim_tier = (
        ClaimTier.DIAGNOSTIC_ONLY
        if synthetic_bound_available
        else ClaimTier.BLOCKED
    )
    gates = _gate_status(
        synthetic_bound_available=synthetic_bound_available,
        no_claim_reasons=no_claim_reasons,
    )
    production_status = _production_status(no_claim_reasons)
    branch_status = (
        "synthetic_covariance_bound_candidate"
        if synthetic_bound_available
        else "no_claim"
    )
    stats_definitions = {
        "surface": "FullCovMESReport",
        "branch_role": "synthetic_covariance_biposh_mes_bound",
        "parameter_block": parameter_block_text,
        "observable_labels": list(observable_label_tuple),
        "response_labels": list(response_label_tuple),
        "nuisance_labels": list(nuisance_label_tuple),
        "required_response_rank": expected_rank,
        "raw_response_rank": raw_rank,
        "projected_response_rank": projected_rank,
        "nuisance_rank": nuisance_rank,
        "rank_threshold": rank_threshold,
        "rank_atol": rank_abs_tol,
        "rank_rtol": rank_rel_tol,
        "rho_synthetic": rho,
        "covariance_bound": covariance_bound,
        "transfer_source": "none",
        "generating_command": command_text,
        "git_commit": git_commit_text,
        "worktree_state": worktree_text,
        "sky_support_status": sky_status,
        "mask_status": mask_status_text,
        "covariance_status": (
            "missing_full_covariance" if covariance is None else covariance_status_text
        ),
        "null_mock_status": null_status_text,
        "look_elsewhere_trial_count": trial_count,
        "biposh_feature_ref": _biposh_metadata(biposh_payload),
        "null_feature_ref": _null_metadata(null_payload),
        "does_not_replace_diagonal_mes": True,
        "template_mean_branch_evaluated": False,
        "p_values_emitted": False,
        "no_claim_reasons": list(no_claim_reasons),
    }
    manifest = ArtifactManifest(
        artifact_id=str(artifact_id or _stable_hash({
            "schema_version": SCHEMA_VERSION,
            "parameter_block": parameter_block_text,
            "response_labels": list(response_label_tuple),
            "config_hash": config_hash_text,
            "input_hashes": input_hash_list,
        })),
        artifact_path=_non_empty(artifact_path, "artifact_path"),
        owner=Owner.COMMON,
        implementation_scope=ImplementationScope.COMMON,
        claim_tier=claim_tier,
        production_status=production_status,
        created_by=_CREATED_BY,
        git_commit=git_commit_text,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
        code_version=git_commit_text or worktree_text or "unknown",
        schema_version=SCHEMA_VERSION,
        caveats=list(caveat_list),
        required_gates=list(_REQUIRED_GATES),
        passed_gates=gates["passed"],
        failed_gates=gates["failed"],
        statistics_definitions=stats_definitions,
    )
    report = FullCovMESReport(
        parameter_block=parameter_block_text,
        diagonal_bound=diagonal,
        covariance_bound=covariance_bound,
        dynamical_bound=dyn_bound,
        final_bound=float(final_bound),
        information_gain=float(information_gain),
        response_rank=projected_rank,
        singular_values=[float(value) for value in projected_singular_values],
        nuisance_projection_status=(
            "projected"
            if synthetic_bound_available and nuisance_matrix.shape[1]
            else (
                "not_requested"
                if synthetic_bound_available
                else "no_claim:" + ",".join(no_claim_reasons)
            )
        ),
        observable_set=list(observable_label_tuple),
        covariance_assumption=(
            "full_covariance_biposh_synthetic"
            if covariance is not None
            else "missing_full_covariance_biposh"
        ),
        validity_radius=rho if synthetic_bound_available else None,
        manifest=manifest,
    )
    return MesCovarianceBoundResult(
        report=report,
        biposh_feature_payload=_public_biposh_payload(biposh_payload),
        null_feature_payload=_public_null_payload(null_payload),
        synthetic_bound_available=synthetic_bound_available,
        no_claim_reasons=tuple(no_claim_reasons),
        covariance_bound=covariance_bound,
        projected_rank=projected_rank,
        raw_rank=raw_rank,
        nuisance_rank=nuisance_rank,
        rank_threshold=rank_threshold,
        raw_singular_values=raw_singular_values,
        nuisance_singular_values=nuisance_singular_values,
        projected_response_norms=projected_norms,
        condition_number=condition_number,
        branch_status=branch_status,
    )


def _validate_biposh_payload(
    payload: Mapping[str, object] | None,
    no_claim_reasons: list[str],
    *,
    config_hash: str,
    input_hashes: Sequence[str],
    sky_support_status: str,
    mask_status: str,
    covariance_status: str,
    null_mock_status: str,
) -> dict[str, Any] | None:
    if payload is None:
        no_claim_reasons.append("missing_biposh_feature_payload")
        return None
    normalised = _json_ready(dict(payload))
    if normalised.get("owner") != Owner.OBSSTAT.value:
        no_claim_reasons.append("biposh_owner_mismatch")
    if normalised.get("implementation_scope") != ImplementationScope.OBSSTAT.value:
        no_claim_reasons.append("biposh_scope_mismatch")
    if normalised.get("claim_tier") != ClaimTier.DIAGNOSTIC_ONLY.value:
        no_claim_reasons.append("biposh_claim_tier_mismatch")
    if normalised.get("model_role") != "not_model_input":
        no_claim_reasons.append("biposh_model_role_mismatch")
    if normalised.get("statistic_role") != "feature_only":
        no_claim_reasons.append("biposh_statistic_role_mismatch")
    if normalised.get("transfer_source") != "none":
        no_claim_reasons.append("biposh_transfer_source_not_none")
    if not str(normalised.get("entry_hash", "")).startswith("sha256:"):
        no_claim_reasons.append("biposh_entry_hash_missing")
    threshold_policy = normalised.get("threshold_policy")
    if not isinstance(threshold_policy, Mapping):
        no_claim_reasons.append("biposh_threshold_policy_missing")
    else:
        expected_entry_hash = _stable_hash(
            {
                "entries": normalised.get("entries"),
                "convention": normalised.get("convention_metadata"),
                "threshold": threshold_policy.get("absolute_value_threshold"),
            }
        )
        if normalised.get("entry_hash") != expected_entry_hash:
            no_claim_reasons.append("biposh_entry_hash_mismatch")
    if normalised.get("config_hash") != config_hash:
        no_claim_reasons.append("biposh_config_hash_mismatch")
    if list(normalised.get("input_hashes", ())) != list(input_hashes):
        no_claim_reasons.append("biposh_input_hashes_mismatch")
    if normalised.get("sky_support_status") != sky_support_status:
        no_claim_reasons.append("biposh_sky_support_mismatch")
    if normalised.get("mask_status") != mask_status:
        no_claim_reasons.append("biposh_mask_status_mismatch")
    if normalised.get("covariance_status") != covariance_status:
        no_claim_reasons.append("biposh_covariance_status_mismatch")
    if normalised.get("null_mock_status") != null_mock_status:
        no_claim_reasons.append("biposh_null_mock_status_mismatch")
    claim_status = normalised.get("claim_status", {})
    if isinstance(claim_status, Mapping):
        if claim_status.get("inference_status") != "not_model_input":
            no_claim_reasons.append("biposh_inference_status_mismatch")
        if claim_status.get("mio_status") != "not_mio_output":
            no_claim_reasons.append("biposh_mio_status_mismatch")
        if claim_status.get("family_status") != "blocked_pre_native_atlas":
            no_claim_reasons.append("biposh_family_status_mismatch")
    return normalised


def _validate_null_payload(
    payload: Mapping[str, object] | None,
    no_claim_reasons: list[str],
    *,
    config_hash: str,
    input_hashes: Sequence[str],
    sky_support_status: str,
    mask_status: str,
    covariance_status: str,
    look_elsewhere_trial_count: int,
    expected_observed_feature_ref: str | None,
) -> dict[str, Any] | None:
    if payload is None:
        no_claim_reasons.append("missing_null_feature_payload")
        return None
    validate_null_feature_payload(payload)
    normalised = _json_ready(dict(payload))
    feature_targets = set(str(value) for value in normalised.get("feature_targets", ()))
    statistic_keys = set(str(value) for value in normalised.get("statistic_keys", ()))
    if "mes_covariance_bound" not in feature_targets:
        no_claim_reasons.append("null_feature_target_missing")
    if "covariance_response_svd" not in statistic_keys:
        no_claim_reasons.append("null_statistic_key_missing")
    if normalised.get("look_elsewhere_status") != "global_corrected":
        no_claim_reasons.append("null_look_elsewhere_not_global")
    if normalised.get("config_hash") != config_hash:
        no_claim_reasons.append("null_config_hash_mismatch")
    if list(normalised.get("input_hashes", ())) != list(input_hashes):
        no_claim_reasons.append("null_input_hashes_mismatch")
    if normalised.get("sky_support_status") != sky_support_status:
        no_claim_reasons.append("null_sky_support_mismatch")
    if normalised.get("mask_status") != mask_status:
        no_claim_reasons.append("null_mask_status_mismatch")
    if normalised.get("covariance_status") != covariance_status:
        no_claim_reasons.append("null_covariance_status_mismatch")
    if int(normalised.get("look_elsewhere_trials", 0)) != look_elsewhere_trial_count:
        no_claim_reasons.append("null_scan_volume_mismatch")
    observed_feature_ref = str(normalised.get("observed_feature_ref", "")).strip()
    if not observed_feature_ref:
        no_claim_reasons.append("null_observed_feature_ref_missing")
    elif expected_observed_feature_ref and observed_feature_ref != expected_observed_feature_ref:
        no_claim_reasons.append("null_observed_feature_ref_mismatch")
    return normalised


def _gate_status(
    *,
    synthetic_bound_available: bool,
    no_claim_reasons: Sequence[str],
) -> dict[str, list[str]]:
    passed = ["diagonal_mes_baseline_preserved", "no_geometry_or_family_claim"]
    if synthetic_bound_available:
        passed.extend(
            [
                "full_covariance_supplied",
                "biposh_feature_payload_supplied",
                "typed_null_feature_payload",
                "nuisance_projected_response_rank_sufficient",
            ]
        )
        return {"passed": passed, "failed": []}
    failed: list[str] = []
    if "missing_full_covariance" in no_claim_reasons:
        failed.append("full_covariance_supplied")
    if any(str(reason).startswith("biposh_") or reason == "missing_biposh_feature_payload" for reason in no_claim_reasons):
        failed.append("biposh_feature_payload_supplied")
    if any(str(reason).startswith("null_") or reason == "missing_null_feature_payload" for reason in no_claim_reasons):
        failed.append("typed_null_feature_payload")
    if any(reason in no_claim_reasons for reason in ("response_rank_deficient", "zero_projected_response")):
        failed.append("nuisance_projected_response_rank_sufficient")
    return {"passed": passed, "failed": list(dict.fromkeys(failed))}


def _production_status(no_claim_reasons: Sequence[str]) -> str:
    if not no_claim_reasons:
        return "diagnostic_only"
    if "missing_full_covariance" in no_claim_reasons:
        return "blocked_missing_covariance"
    if any(
        str(reason).startswith("null_") or reason == "missing_null_feature_payload"
        for reason in no_claim_reasons
    ):
        return "blocked_missing_null_mocks"
    if any(
        str(reason).startswith("biposh_") or reason == "missing_biposh_feature_payload"
        for reason in no_claim_reasons
    ):
        return "blocked_provenance_mismatch"
    if any(
        reason in no_claim_reasons
        for reason in ("response_rank_deficient", "zero_projected_response")
    ):
        return "blocked_rank_deficient"
    return "diagnostic_only"


def _response_matrix(
    values: Sequence[Sequence[object]],
    n_obs: int,
    name: str,
    *,
    allow_empty: bool = False,
) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of response vectors")
    if not values:
        if allow_empty:
            return np.zeros((n_obs, 0), dtype=float)
        raise ValueError(f"{name} must contain at least one response vector")
    columns = [_finite_vector(value, name) for value in values]
    if any(column.size != n_obs for column in columns):
        raise ValueError(f"{name} entries must have the same length as observable_labels")
    return np.column_stack(columns)


def _finite_vector(values: Sequence[object], name: str) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} entries must be non-string sequences")
    vector = np.asarray(tuple(float(value) for value in values), dtype=float)
    if vector.ndim != 1 or vector.shape[0] == 0:
        raise ValueError(f"{name} entries must be non-empty one-dimensional vectors")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} entries must be finite")
    return vector


def _covariance_matrix(value: object, n_obs: int) -> np.ndarray:
    covariance = np.asarray(value, dtype=float)
    if covariance.shape != (n_obs, n_obs):
        raise ValueError("full_covariance must be square with observable length")
    if not np.all(np.isfinite(covariance)):
        raise ValueError("full_covariance entries must be finite")
    if not np.allclose(covariance, covariance.T, rtol=1.0e-10, atol=1.0e-12):
        raise ValueError("full_covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(covariance)
    if np.any(eigenvalues <= 1.0e-12):
        raise ValueError("full_covariance must be positive definite")
    return covariance.astype(float)


def _inverse_sqrt_covariance(covariance: np.ndarray) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    return eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T


def _rank_from_singular_values(
    singular_values: np.ndarray,
    *,
    atol: float,
    rtol: float,
) -> tuple[int, float]:
    if singular_values.size == 0:
        return 0, float(atol)
    s_max = float(np.max(singular_values))
    threshold = float(atol + rtol * s_max)
    return int(np.sum(singular_values > threshold)), threshold


def _nuisance_projector(
    nuisance_white: np.ndarray,
    *,
    atol: float,
    rtol: float,
) -> tuple[np.ndarray, int, tuple[float, ...]]:
    n_obs = nuisance_white.shape[0]
    if nuisance_white.shape[1] == 0:
        return np.eye(n_obs), 0, ()
    u, singular_values, _ = np.linalg.svd(nuisance_white, full_matrices=False)
    rank, _ = _rank_from_singular_values(singular_values, atol=atol, rtol=rtol)
    if rank == 0:
        return np.eye(n_obs), 0, tuple(float(value) for value in singular_values)
    q = u[:, :rank]
    return np.eye(n_obs) - q @ q.T, rank, tuple(float(value) for value in singular_values)


def _positive_finite(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be positive finite") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be positive finite")
    return number


def _nonnegative_finite(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be non-negative finite") from exc
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be non-negative finite")
    return number


def _positive_int(value: object, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if number <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return number


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _tuple_of_str(
    values: Sequence[object],
    name: str,
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    result = tuple(str(value).strip() for value in values)
    if require_non_empty and not result:
        raise ValueError(f"{name} must contain at least one entry")
    if any(not value for value in result):
        raise ValueError(f"{name} must contain only non-empty strings")
    return result


def _require_hash(value: object, name: str) -> str:
    text = _non_empty(value, name)
    if not text.startswith("sha256:"):
        raise ValueError(f"{name} must start with sha256:")
    return text


def _require_input_hashes(values: Sequence[object], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    hashes = tuple(_require_hash(value, f"{name} entry") for value in values)
    if not hashes:
        raise ValueError(f"{name} must contain at least one entry")
    return hashes


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _biposh_metadata(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {}
    return {
        "entry_hash": payload.get("entry_hash"),
        "representation": payload.get("representation"),
        "model_role": payload.get("model_role"),
        "statistic_role": payload.get("statistic_role"),
        "transfer_source": payload.get("transfer_source"),
        "covariance_status": payload.get("covariance_status"),
        "null_mock_status": payload.get("null_mock_status"),
        "norm_summary": payload.get("norm_summary"),
    }


def _null_metadata(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {}
    return {
        "null_ensemble_ref": payload.get("null_ensemble_ref"),
        "mock_count": payload.get("mock_count"),
        "look_elsewhere_status": payload.get("look_elsewhere_status"),
        "scan_volume_hash": payload.get("scan_volume_hash"),
        "null_mock_status": payload.get("null_mock_status"),
        "observed_feature_ref": payload.get("observed_feature_ref"),
        "feature_targets": list(payload.get("feature_targets", ())),
        "statistic_keys": list(payload.get("statistic_keys", ())),
    }


def _public_biposh_payload(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    public_payload = dict(payload)
    public_payload.pop("p_values", None)
    return _json_ready(public_payload)


def _public_null_payload(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    public_payload = dict(payload)
    public_payload.pop("p_values", None)
    return _json_ready(public_payload)


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    return {
        "artifact_id": manifest.artifact_id,
        "artifact_path": manifest.artifact_path,
        "owner": manifest.owner.value,
        "implementation_scope": manifest.implementation_scope.value,
        "claim_tier": manifest.claim_tier.value,
        "production_status": manifest.production_status,
        "created_by": manifest.created_by,
        "git_commit": manifest.git_commit,
        "config_hash": manifest.config_hash,
        "input_hashes": list(manifest.input_hashes),
        "code_version": manifest.code_version,
        "schema_version": manifest.schema_version,
        "caveats": list(manifest.caveats),
        "required_gates": list(manifest.required_gates),
        "passed_gates": list(manifest.passed_gates),
        "failed_gates": list(manifest.failed_gates),
        "statistics_definitions": _json_ready(manifest.statistics_definitions),
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("payload floats must be finite")
        return value
    return value


def _normalise_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _reject_overclaim_text(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_overclaim_text(key)
            if str(key) == "does_not_establish":
                continue
            _reject_overclaim_text(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _reject_overclaim_text(item)
        return
    if not isinstance(value, (str, bytes)):
        return
    text = _normalise_text(value)
    for part in _FORBIDDEN_TEXT_PARTS:
        if _normalise_text(part) in text:
            raise ValueError(f"metadata contains forbidden claim language: {part}")
