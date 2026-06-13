"""Synthetic full-covariance MES template-bound harness.

The module builds a COMMON-owned diagnostic-only ``FullCovMESReport`` for the
deterministic template-mean branch.  It consumes OBSSTAT template-fit and null
provenance metadata, emits no HTT likelihood/evidence, and leaves the diagonal
MES baseline intact whenever a synthetic branch gate is missing.
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
from obsstat.template_fit import (
    CovarianceAssumption,
    OrientationScanMetadata,
    TemplateFitDiagnostic,
    fit_template_diagnostic,
)

__all__ = ["MesTemplateBoundResult", "build_mes_template_bound"]


SCHEMA_VERSION = "htt.statistics.mes_template_bound.v1"
_CREATED_BY = "htt.statistics.mes_template_bound.build_mes_template_bound"
_DEFAULT_ARTIFACT_PATH = "memory://htt.statistics/mes-template-bound"
_DEFAULT_CAVEAT = (
    "COMMON diagnostic-only synthetic template-mean MES branch; keeps the "
    "diagonal MES baseline separate"
)
_REQUIRED_GATES = (
    "full_covariance_supplied",
    "template_response_rank_sufficient",
    "typed_null_feature_payload",
    "diagonal_mes_baseline_preserved",
    "no_universal_mes_claim",
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
class MesTemplateBoundResult:
    """Diagnostic wrapper around a synthetic template-branch MES report."""

    report: FullCovMESReport
    template_fit: TemplateFitDiagnostic | None
    template_fit_payload: Mapping[str, Any] | None
    null_feature_payload: Mapping[str, Any] | None
    synthetic_bound_available: bool
    no_claim_reasons: tuple[str, ...]
    template_bound: float | None
    template_norm_weighted: float | None
    branch_status: str

    def as_payload(self) -> dict[str, Any]:
        manifest = _manifest_payload(self.report.manifest)
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
        return _json_ready(
            {
                "owner": Owner.COMMON.value,
                "implementation_scope": ImplementationScope.COMMON.value,
                "claim_tier": self.report.manifest.claim_tier.value,
                "production_status": self.report.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": manifest,
                "branch_role": "synthetic_template_mean_mes_bound",
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
                "singular_values": list(self.report.singular_values),
                "template_bound": self.template_bound,
                "template_norm_weighted": self.template_norm_weighted,
                "no_claim_reasons": list(self.no_claim_reasons),
                "generating_command": definitions.get("generating_command"),
                "git_commit": self.report.manifest.git_commit,
                "worktree_state": definitions.get("worktree_state"),
                "template_fit": self.template_fit_payload,
                "null_feature_ref": null_ref,
                "branch_separation": {
                    "template_mean_branch": "synthetic_template_mean_bound",
                    "covariance_branch": "not_evaluated_by_this_module",
                    "does_not_replace_diagonal_mes": True,
                    "universal_mes_claim": False,
                    "merged_statistic_allowed": False,
                },
                "claim_status": {
                    "inference_status": "not_model_input",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_result",
                    "covariance_anomaly_status": "not_evaluated",
                },
                "caveats": list(self.report.manifest.caveats),
            }
        )


def build_mes_template_bound(
    *,
    observed: Sequence[object],
    template: Sequence[object],
    full_covariance: Sequence[Sequence[object]] | None,
    diagonal_bound: object,
    rho_synthetic: object,
    parameter_block: object,
    orientation_scan: OrientationScanMetadata,
    null_feature_payload: Mapping[str, object] | None,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    worktree_state: object | None,
    dynamical_bound: object | None = None,
    template_label: object = "synthetic_template",
    rank_tolerance: object = 1.0e-12,
    artifact_id: object | None = None,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    git_commit: object | None = None,
    caveats: Sequence[object] = (_DEFAULT_CAVEAT,),
) -> MesTemplateBoundResult:
    """Build a synthetic template-mean branch report with no-claim gates."""

    parameter_block_text = _non_empty(parameter_block, "parameter_block")
    template_label_text = _non_empty(template_label, "template_label")
    _reject_overclaim_text(
        {
            "parameter_block": parameter_block_text,
            "template_label": template_label_text,
            "artifact_id": artifact_id or "",
            "artifact_path": artifact_path,
            "generating_command": generating_command,
            "git_commit": git_commit or "",
            "worktree_state": worktree_state or "",
            "caveats": list(caveats),
        }
    )
    if not isinstance(orientation_scan, OrientationScanMetadata):
        raise TypeError("orientation_scan must be OrientationScanMetadata")

    observed_vec = _finite_vector(observed, "observed")
    template_vec = _finite_vector(template, "template")
    if observed_vec.shape != template_vec.shape:
        raise ValueError("observed and template vectors must have the same shape")
    diagonal = _positive_finite(diagonal_bound, "diagonal_bound")
    rho = _positive_finite(rho_synthetic, "rho_synthetic")
    rank_tol = _nonnegative_finite(rank_tolerance, "rank_tolerance")
    dyn_bound = (
        None
        if dynamical_bound is None
        else _positive_finite(dynamical_bound, "dynamical_bound")
    )
    config_hash_text = _require_hash(config_hash, "config_hash")
    input_hash_list = list(_require_input_hashes(input_hashes, "input_hashes"))
    command_text = _non_empty(generating_command, "generating_command")
    git_commit_text = None if git_commit is None else _non_empty(git_commit, "git_commit")
    worktree_text = (
        None if worktree_state is None else _non_empty(worktree_state, "worktree_state")
    )
    if git_commit_text is None and worktree_text is None:
        raise ValueError("build_mes_template_bound requires git_commit or worktree_state")
    caveat_list = tuple(_non_empty(item, "caveat") for item in caveats)
    _reject_overclaim_text(caveat_list)

    covariance_assumption: CovarianceAssumption | None = None
    covariance_metadata: dict[str, Any] | None = None
    no_claim_reasons: list[str] = []
    if full_covariance is None:
        no_claim_reasons.append("missing_full_covariance")
    else:
        covariance_assumption = CovarianceAssumption.full_covariance(full_covariance)
        covariance_assumption._require_dimension(observed_vec.shape[0])
        covariance_metadata = covariance_assumption.to_metadata(
            vector_length=observed_vec.shape[0]
        )

    null_payload = _validate_null_payload(
        null_feature_payload,
        no_claim_reasons,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
        orientation_scan=orientation_scan,
        covariance_assumption=covariance_assumption,
    )
    if null_payload is not None:
        _reject_overclaim_text(null_payload)
    public_null_payload = _public_null_payload(null_payload)

    template_norm: float | None = None
    template_fit: TemplateFitDiagnostic | None = None
    template_fit_payload: Mapping[str, Any] | None = None
    response_rank = 0
    singular_values: list[float] = []
    template_bound: float | None = None
    if covariance_assumption is not None:
        template_norm = float(covariance_assumption.weighted_dot(template_vec, template_vec))
        if math.isfinite(template_norm) and template_norm > 0.0:
            response_scale = math.sqrt(template_norm)
            response_rank = 1 if response_scale > rank_tol else 0
            singular_values = [response_scale]
            if response_rank:
                template_fit = fit_template_diagnostic(
                    observed=observed_vec,
                    template=template_vec,
                    orientation_scan=orientation_scan,
                    covariance_assumption=covariance_assumption,
                    template_label=template_label_text,
                    config_hash=config_hash_text,
                    input_hashes=input_hash_list,
                    generating_command=command_text,
                    git_commit=git_commit_text,
                    worktree_state=worktree_text,
                )
                template_fit_payload = template_fit.to_feature_payload()
                template_bound = float(rho / response_scale)
        else:
            no_claim_reasons.append("response_rank_deficient")
    if covariance_assumption is not None and response_rank == 0:
        no_claim_reasons.append("response_rank_deficient")
    no_claim_reasons = list(dict.fromkeys(no_claim_reasons))

    synthetic_bound_available = not no_claim_reasons
    candidate_bounds = [diagonal]
    covariance_bound = template_bound if synthetic_bound_available else None
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
    production_status = _production_status(no_claim_reasons)
    gates = _gate_status(
        synthetic_bound_available=synthetic_bound_available,
        no_claim_reasons=no_claim_reasons,
    )
    null_metadata = _null_metadata(null_payload)
    stats_definitions = {
        "surface": "FullCovMESReport",
        "branch_role": "synthetic_template_mean_mes_bound",
        "parameter_block": parameter_block_text,
        "template_label": template_label_text,
        "template_norm_weighted": template_norm,
        "rho_synthetic": rho,
        "template_bound": covariance_bound,
        "transfer_source": "none",
        "generating_command": command_text,
        "git_commit": git_commit_text,
        "worktree_state": worktree_text,
        "sky_support_status": orientation_scan.sky_support_status,
        "mask_status": orientation_scan.mask_status,
        "covariance_status": (
            "missing_full_covariance"
            if covariance_assumption is None
            else covariance_assumption.covariance_status
        ),
        "null_mock_status": null_metadata.get("null_mock_status", "not_supplied"),
        "look_elsewhere_status": null_metadata.get("look_elsewhere_status"),
        "does_not_replace_diagonal_mes": True,
        "universal_mes_claim": False,
        "p_values_emitted": False,
        "no_claim_reasons": list(no_claim_reasons),
    }
    if covariance_metadata is not None:
        stats_definitions["covariance_assumption"] = covariance_metadata
    if null_metadata:
        stats_definitions["null_feature_ref"] = null_metadata
    manifest = ArtifactManifest(
        artifact_id=str(artifact_id or _stable_hash({
            "schema_version": SCHEMA_VERSION,
            "parameter_block": parameter_block_text,
            "template_label": template_label_text,
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
        response_rank=response_rank,
        singular_values=singular_values,
        nuisance_projection_status=(
            "not_requested_template_mean_branch"
            if synthetic_bound_available
            else "no_claim:" + ",".join(no_claim_reasons)
        ),
        observable_set=[f"observable_{idx}" for idx in range(observed_vec.shape[0])],
        covariance_assumption=(
            "full_covariance_template_mean_synthetic"
            if covariance_assumption is not None
            else "missing_full_covariance_template_mean"
        ),
        validity_radius=rho if synthetic_bound_available else None,
        manifest=manifest,
    )
    return MesTemplateBoundResult(
        report=report,
        template_fit=template_fit,
        template_fit_payload=template_fit_payload,
        null_feature_payload=public_null_payload,
        synthetic_bound_available=synthetic_bound_available,
        no_claim_reasons=tuple(no_claim_reasons),
        template_bound=covariance_bound,
        template_norm_weighted=template_norm,
        branch_status=(
            "synthetic_template_bound_candidate"
            if synthetic_bound_available
            else "no_claim"
        ),
    )


def _validate_null_payload(
    payload: Mapping[str, object] | None,
    no_claim_reasons: list[str],
    *,
    config_hash: str,
    input_hashes: Sequence[str],
    orientation_scan: OrientationScanMetadata,
    covariance_assumption: CovarianceAssumption | None,
) -> dict[str, Any] | None:
    if payload is None:
        no_claim_reasons.append("missing_null_feature_payload")
        return None
    validate_null_feature_payload(payload)
    normalised = _json_ready(dict(payload))
    feature_targets = set(str(value) for value in normalised.get("feature_targets", ()))
    statistic_keys = set(str(value) for value in normalised.get("statistic_keys", ()))
    if "mes_template_bound" not in feature_targets:
        no_claim_reasons.append("null_feature_target_missing")
    if "template_delta_chi2" not in statistic_keys:
        no_claim_reasons.append("null_statistic_key_missing")
    if normalised.get("look_elsewhere_status") != "global_corrected":
        no_claim_reasons.append("null_look_elsewhere_not_global")
    if normalised.get("config_hash") != config_hash:
        no_claim_reasons.append("null_config_hash_mismatch")
    if list(normalised.get("input_hashes", ())) != list(input_hashes):
        no_claim_reasons.append("null_input_hashes_mismatch")
    if normalised.get("sky_support_status") != orientation_scan.sky_support_status:
        no_claim_reasons.append("null_sky_support_mismatch")
    if normalised.get("mask_status") != orientation_scan.mask_status:
        no_claim_reasons.append("null_mask_status_mismatch")
    if (
        covariance_assumption is not None
        and normalised.get("covariance_status")
        != covariance_assumption.covariance_status
    ):
        no_claim_reasons.append("null_covariance_status_mismatch")
    if int(normalised.get("look_elsewhere_trials", 0)) != int(
        orientation_scan.orientation_count
    ):
        no_claim_reasons.append("null_scan_volume_mismatch")
    if not str(normalised.get("observed_feature_ref", "")).strip():
        no_claim_reasons.append("null_observed_feature_ref_missing")
    return normalised


def _null_metadata(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {}
    return {
        "null_ensemble_ref": payload.get("null_ensemble_ref"),
        "mock_count": payload.get("mock_count"),
        "look_elsewhere_status": payload.get("look_elsewhere_status"),
        "scan_volume_hash": payload.get("scan_volume_hash"),
        "null_mock_status": payload.get("null_mock_status"),
        "feature_targets": list(payload.get("feature_targets", ())),
        "statistic_keys": list(payload.get("statistic_keys", ())),
    }


def _public_null_payload(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    public_payload = dict(payload)
    public_payload.pop("p_values", None)
    return _json_ready(public_payload)


def _gate_status(
    *,
    synthetic_bound_available: bool,
    no_claim_reasons: Sequence[str],
) -> dict[str, list[str]]:
    passed = ["diagonal_mes_baseline_preserved", "no_universal_mes_claim"]
    if synthetic_bound_available:
        passed.extend(
            [
                "full_covariance_supplied",
                "template_response_rank_sufficient",
                "typed_null_feature_payload",
            ]
        )
        return {"passed": passed, "failed": []}
    failed: list[str] = []
    if "missing_full_covariance" in no_claim_reasons:
        failed.append("full_covariance_supplied")
    if "response_rank_deficient" in no_claim_reasons:
        failed.append("template_response_rank_sufficient")
    if any(str(reason).startswith("null_") or reason == "missing_null_feature_payload" for reason in no_claim_reasons):
        failed.append("typed_null_feature_payload")
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
    return "diagnostic_only"


def _finite_vector(values: Sequence[object], name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.ndim != 1 or vector.shape[0] == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} entries must be finite")
    return vector.astype(float)


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


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


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
