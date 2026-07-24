"""Gated local/global mixture-likelihood skeleton for HTT.

The skeleton composes the PR-060 response-rank audit, PR-061 local-null FPR
gate, and PR-062 survey/systematic FPR gate. It keeps local boost, global
tilt, survey/systematic, and noise blocks separate. It rejects canonical
x/Q/Pi/F/G-style names as primitive fitted parameters and emits only
noncanonical diagnostic fit scores after the gates pass.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
)
from common.enum_compat import StrEnum

from htt.departure.response_overlap import (
    ResponseOverlapAudit,
    require_rank_audit_for_model_run,
)
from htt.nulls.local_boost_depth_null import (
    LocalBoostNullFprReport,
    evaluate_global_tilt_local_null_gate,
)
from htt.nulls.selection_response_depth import (
    SurveySystematicNullFprReport,
    evaluate_survey_systematic_null_gate,
)

__all__ = [
    "LocalGlobalMixtureBlock",
    "LocalGlobalMixtureReport",
    "LocalGlobalMixtureSpec",
    "build_local_global_mixture_report",
]


SCHEMA_VERSION = "htt.departure.local_global_mixture.v1"
_CREATED_BY = "htt.departure.local_global_mixture.build_local_global_mixture_report"
_DEFAULT_ARTIFACT_PATH = "memory://htt/departure/local_global_mixture.json"
_ALLOWED_KINDS = ("local_boost", "global_tilt", "survey_systematic", "noise")
_REQUIRED_KINDS = frozenset(_ALLOWED_KINDS)
_DESIGN_KINDS = ("local_boost", "global_tilt", "survey_systematic")
_FULL_DESIGN_RANK_ATOL = 1.0e-12
_FULL_DESIGN_RANK_RTOL = 0.0
_FULL_DESIGN_CONDITION_LIMIT = 1.0e8
_RESPONSE_MATCH_RTOL = 1.0e-10
_RESPONSE_MATCH_ATOL = 1.0e-12
_GENERATED_FUNCTIONAL_NAMES = {
    "f",
    "g",
    "g_f",
    "gf",
    "f_total",
    "g_total",
    "g_total_f",
    "g_f_total",
}
_DEFAULT_CAVEATS = (
    "pre_solver_skeleton",
    "diagnostic_only_pre_native_solver",
    "local_null_fpr_prerequisite_not_model_weight",
    "survey_systematic_fpr_prerequisite_not_model_weight",
    "does_not_identify_bianchi_family",
    "no_native_solver_values",
)


def _non_empty(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _optional_non_empty(value: object | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _non_empty(value, field_name)


def _finite_float(value: object, field_name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{field_name} must be a finite numeric value, not boolean")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite")
    return out


def _vector(values: Sequence[object], field_name: str) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a non-string vector")
    vector = np.asarray(tuple(float(value) for value in values), dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"{field_name} must be a non-empty vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{field_name} must contain finite values")
    return vector


def _covariance(value: object, n_obs: int) -> np.ndarray:
    covariance = np.asarray(value, dtype=float)
    if covariance.shape != (n_obs, n_obs):
        raise ValueError("covariance must be square with observable-vector length")
    if not np.all(np.isfinite(covariance)):
        raise ValueError("covariance must contain finite values")
    if not np.allclose(covariance, covariance.T, rtol=1.0e-10, atol=1.0e-12):
        raise ValueError("covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(covariance)
    if np.any(eigenvalues <= 1.0e-12):
        raise ValueError("covariance must be positive definite")
    return covariance


def _input_hashes(values: Sequence[object], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise ValueError(f"{field_name} must be a non-empty sequence")
    out = tuple(_non_empty(value, field_name) for value in values)
    return out


def _json_ready(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, np.ndarray):
        return [_json_ready(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("payload floats must be finite")
        return value
    return value


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    payload = _json_ready(asdict(manifest))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a mapping")
    return payload


def _generated_parameter_name(name: str) -> bool:
    lowered = name.strip().lower()
    return lowered in _GENERATED_FUNCTIONAL_NAMES


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _block_by_kind(
    blocks: Sequence["LocalGlobalMixtureBlock"],
) -> dict[str, "LocalGlobalMixtureBlock"]:
    return {block.kind: block for block in blocks}


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


def _full_design_rank_gate(
    spec: "LocalGlobalMixtureSpec",
) -> tuple[dict[str, object], tuple[str, ...]]:
    blocks = _block_by_kind(spec.blocks)
    design = np.column_stack(
        [np.asarray(blocks[kind].response, dtype=float) for kind in _DESIGN_KINDS]
    )
    whitening = _inverse_sqrt_covariance(np.asarray(spec.covariance, dtype=float))
    whitened_design = whitening @ design
    singular_values = np.linalg.svd(whitened_design, compute_uv=False)
    rank, threshold = _rank_from_singular_values(
        singular_values,
        atol=_FULL_DESIGN_RANK_ATOL,
        rtol=_FULL_DESIGN_RANK_RTOL,
    )
    expected_rank = len(_DESIGN_KINDS)
    condition_number: float | None
    min_singular = float(np.min(singular_values)) if singular_values.size else 0.0
    if rank < expected_rank or min_singular <= threshold:
        condition_number = None
    else:
        condition_number = float(float(np.max(singular_values)) / min_singular)

    blocked: list[str] = []
    if rank < expected_rank:
        blocked.append("full_design_rank_deficient")
    if condition_number is not None and condition_number > _FULL_DESIGN_CONDITION_LIMIT:
        blocked.append("full_design_condition_too_high")

    return (
        {
            "allowed": not blocked,
            "response_kinds": list(_DESIGN_KINDS),
            "rank": rank,
            "expected_rank": expected_rank,
            "singular_values": [float(value) for value in singular_values],
            "rank_threshold": threshold,
            "condition_number": condition_number,
            "condition_limit": _FULL_DESIGN_CONDITION_LIMIT,
            "covariance_source": "LocalGlobalMixtureSpec.covariance",
            "whitening": "eigh_inverse_sqrt",
        },
        tuple(blocked),
    )


def _response_consistency_gate(
    spec: "LocalGlobalMixtureSpec",
    audit: ResponseOverlapAudit | None,
) -> tuple[dict[str, object], tuple[str, ...]]:
    if audit is None:
        return (
            {
                "allowed": False,
                "checked": False,
                "blocked_reason": "response_overlap_rank_audit_missing",
            },
            (),
        )

    blocks = _block_by_kind(spec.blocks)
    local_response = np.asarray(blocks["local_boost"].response, dtype=float)
    global_response = np.asarray(blocks["global_tilt"].response, dtype=float)
    audit_local = np.asarray(audit.local_boost_response, dtype=float)
    audit_global = np.asarray(audit.global_tilt_response, dtype=float)
    local_match = bool(
        local_response.shape == audit_local.shape
        and np.allclose(
            local_response,
            audit_local,
            rtol=_RESPONSE_MATCH_RTOL,
            atol=_RESPONSE_MATCH_ATOL,
        )
    )
    global_match = bool(
        global_response.shape == audit_global.shape
        and np.allclose(
            global_response,
            audit_global,
            rtol=_RESPONSE_MATCH_RTOL,
            atol=_RESPONSE_MATCH_ATOL,
        )
    )
    blocked: list[str] = []
    if not local_match:
        blocked.append("response_overlap_local_response_mismatch")
    if not global_match:
        blocked.append("response_overlap_global_response_mismatch")
    return (
        {
            "allowed": not blocked,
            "checked": True,
            "audit_artifact_id": audit.artifact_id,
            "rtol": _RESPONSE_MATCH_RTOL,
            "atol": _RESPONSE_MATCH_ATOL,
            "local_response_matches_audit": local_match,
            "global_tilt_response_matches_audit": global_match,
        },
        tuple(blocked),
    )


def _report_sky_support_status(_spec: "LocalGlobalMixtureSpec") -> str:
    return "not_directional"


def _report_null_mock_status(
    spec: "LocalGlobalMixtureSpec",
    *,
    ready: bool,
) -> str:
    if ready:
        return "local_and_survey_systematic_null_fpr_prerequisites_recorded"
    if (
        spec.local_null_fpr_report is not None
        or spec.survey_systematic_null_fpr_report is not None
    ):
        return "partial_null_fpr_prerequisites_recorded"
    return "missing_local_and_survey_systematic_null_fpr_prerequisites"


def _git_commit_or_worktree_state(spec: "LocalGlobalMixtureSpec") -> str:
    return spec.git_commit or spec.worktree_state or "unknown"


@dataclass(frozen=True)
class LocalGlobalMixtureBlock:
    """One explicitly owned block in the HTT local/global mixture skeleton."""

    name: str
    kind: str
    response: Sequence[object]
    parameter_name: str
    field_id: str
    role: str | None = None

    def __post_init__(self) -> None:
        name = _non_empty(self.name, "LocalGlobalMixtureBlock.name")
        kind = _non_empty(self.kind, "LocalGlobalMixtureBlock.kind")
        if kind not in _ALLOWED_KINDS:
            raise ValueError(f"unknown mixture block kind {kind!r}")
        parameter_name = _non_empty(
            self.parameter_name,
            "LocalGlobalMixtureBlock.parameter_name",
        )
        if _generated_parameter_name(parameter_name):
            raise ValueError(
                f"{parameter_name} is a generated functional, not a primitive parameter"
            )
        if kind in {"local_boost", "global_tilt"} and parameter_name == "beta":
            raise ValueError("local and global tilt cannot share a single beta field")
        field_id = _non_empty(self.field_id, "LocalGlobalMixtureBlock.field_id")
        response = _vector(self.response, "LocalGlobalMixtureBlock.response")
        role = (
            {
                "local_boost": "observer_side_local_boost",
                "global_tilt": "source_background_side_global_tilt_candidate",
                "survey_systematic": "observer_side_survey_systematic_nuisance",
                "noise": "covariance_noise_floor",
            }[kind]
            if self.role is None
            else _non_empty(self.role, "LocalGlobalMixtureBlock.role")
        )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self,
            "response",
            tuple(float(item) for item in response),
        )
        object.__setattr__(self, "parameter_name", parameter_name)
        object.__setattr__(self, "field_id", field_id)
        object.__setattr__(self, "role", role)

    @staticmethod
    def require_collection(
        blocks: Sequence["LocalGlobalMixtureBlock"],
        *,
        n_obs: int | None = None,
    ) -> tuple["LocalGlobalMixtureBlock", ...]:
        if isinstance(blocks, (str, bytes)) or not blocks:
            raise ValueError("mixture blocks must be a non-empty sequence")
        out = tuple(blocks)
        if not all(isinstance(block, LocalGlobalMixtureBlock) for block in out):
            raise TypeError("mixture blocks must contain LocalGlobalMixtureBlock")
        kinds = {block.kind for block in out}
        missing = sorted(_REQUIRED_KINDS - kinds)
        if missing:
            raise ValueError(
                "mixture blocks must include local_boost, global_tilt, "
                "survey_systematic, and noise; missing " + ", ".join(missing)
            )
        duplicates = sorted(
            kind for kind in kinds if sum(block.kind == kind for block in out) > 1
        )
        if duplicates:
            raise ValueError(f"mixture blocks require one block per kind: {duplicates}")
        if n_obs is not None:
            bad = [block.name for block in out if len(block.response) != n_obs]
            if bad:
                raise ValueError(f"block response length mismatch: {bad}")
        params = [block.parameter_name for block in out]
        if len(set(params)) != len(params):
            raise ValueError("mixture blocks must use distinct primitive parameters")
        local = next(block for block in out if block.kind == "local_boost")
        global_tilt = next(block for block in out if block.kind == "global_tilt")
        if (
            local.field_id == global_tilt.field_id
            or local.parameter_name == global_tilt.parameter_name
        ):
            raise ValueError("local and global tilt cannot share a single beta field")
        field_ids = [block.field_id for block in out]
        if len(set(field_ids)) != len(field_ids):
            raise ValueError("mixture blocks must use distinct field IDs")
        return out

    def as_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "role": self.role,
            "response": list(self.response),
            "parameter_name": self.parameter_name,
            "field_id": self.field_id,
            "generated_functional_input": False,
        }


@dataclass(frozen=True)
class LocalGlobalMixtureSpec:
    """Inputs and prerequisite gates for one local/global mixture evaluation."""

    observable_vector: Sequence[object]
    covariance: object
    blocks: Sequence[LocalGlobalMixtureBlock]
    response_overlap_audit: ResponseOverlapAudit | None
    artifact_id: object
    config_hash: object
    input_hashes: Sequence[object]
    generating_command: object
    local_null_fpr_report: LocalBoostNullFprReport | None = None
    survey_systematic_null_fpr_report: SurveySystematicNullFprReport | None = None
    local_null_report_hash: str | None = None
    survey_systematic_null_config_hash: str | None = None
    survey_systematic_null_input_hashes: Sequence[str] | None = None
    survey_systematic_null_report_hash: str | None = None
    response_overlap_config_hash: str | None = None
    selection_metadata_hash: str | None = None
    survey_axis_hash: str | None = None
    artifact_path: object = _DEFAULT_ARTIFACT_PATH
    worktree_state: object | None = None
    git_commit: object | None = None
    transfer_source: object = "none"
    caveats: Sequence[object] = _DEFAULT_CAVEATS

    def __post_init__(self) -> None:
        observable = _vector(self.observable_vector, "observable_vector")
        covariance = _covariance(self.covariance, observable.size)
        blocks = LocalGlobalMixtureBlock.require_collection(
            self.blocks,
            n_obs=observable.size,
        )
        artifact_id = _non_empty(self.artifact_id, "artifact_id")
        artifact_path = _non_empty(self.artifact_path, "artifact_path")
        config_hash = _non_empty(self.config_hash, "config_hash")
        input_hashes = _input_hashes(self.input_hashes, "input_hashes")
        generating_command = _non_empty(self.generating_command, "generating_command")
        git_commit = _optional_non_empty(self.git_commit, "git_commit")
        worktree_state = _optional_non_empty(self.worktree_state, "worktree_state")
        if git_commit is None and worktree_state is None:
            raise ValueError("LocalGlobalMixtureSpec requires git_commit or worktree_state")
        transfer_source = _non_empty(self.transfer_source, "transfer_source")
        if transfer_source != "none":
            raise ValueError("PR-063 mixture skeleton only supports transfer_source='none'")
        caveats = tuple(_non_empty(item, "caveat") for item in self.caveats)
        if not caveats:
            raise ValueError("LocalGlobalMixtureSpec.caveats must be non-empty")
        object.__setattr__(
            self,
            "observable_vector",
            tuple(float(item) for item in observable),
        )
        object.__setattr__(
            self,
            "covariance",
            tuple(tuple(float(item) for item in row) for row in covariance),
        )
        object.__setattr__(self, "blocks", blocks)
        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "artifact_path", artifact_path)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "transfer_source", transfer_source)
        object.__setattr__(self, "caveats", caveats)
        object.__setattr__(
            self,
            "survey_systematic_null_input_hashes",
            (
                None
                if self.survey_systematic_null_input_hashes is None
                else tuple(self.survey_systematic_null_input_hashes)
            ),
        )


@dataclass(frozen=True)
class LocalGlobalMixtureReport:
    """HTT-owned gated local/global mixture-likelihood skeleton report."""

    manifest: ArtifactManifest
    spec: LocalGlobalMixtureSpec
    block_payloads: Mapping[str, Mapping[str, object]]
    gate_payloads: Mapping[str, object]
    generated_functionals: Mapping[str, object]
    evaluation_status: str
    blocked_reasons: tuple[str, ...]
    total_log_likelihood: float | None
    residual_chi2: float | None
    transfer_source: str = "none"

    def as_payload(self) -> dict[str, Any]:
        return _json_ready(
            {
                "owner": Owner.HTT.value,
                "implementation_scope": ImplementationScope.HTT.value,
                "claim_tier": self.manifest.claim_tier.value,
                "production_status": self.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": _manifest_payload(self.manifest),
                "transfer_source": self.transfer_source,
                "config_hash": self.manifest.config_hash,
                "input_hashes": list(self.manifest.input_hashes),
                "sky_support_status": _report_sky_support_status(self.spec),
                "null_mock_status": _report_null_mock_status(
                    self.spec,
                    ready=self.evaluation_status == "ready_diagnostic_likelihood",
                ),
                "git_commit_or_worktree_state": _git_commit_or_worktree_state(
                    self.spec
                ),
                "evaluation_status": self.evaluation_status,
                "total_log_likelihood": self.total_log_likelihood,
                "residual_chi2": self.residual_chi2,
                "primitive_parameters": [
                    block.parameter_name for block in self.spec.blocks
                ],
                "blocks": {
                    kind: dict(payload)
                    for kind, payload in sorted(self.block_payloads.items())
                },
                "gates": dict(self.gate_payloads),
                "generated_functionals": dict(self.generated_functionals),
                "claim_status": {
                    "owner": "HTT",
                    "mixture_status": self.evaluation_status,
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_result",
                    "family_status": "blocked_pre_native_atlas",
                },
                "generating_command": self.spec.generating_command,
                "git_commit": self.spec.git_commit,
                "worktree_state": self.spec.worktree_state,
                "blocked_reasons": list(self.blocked_reasons),
                "caveats": list(self.manifest.caveats),
            }
        )


def build_local_global_mixture_report(
    spec: LocalGlobalMixtureSpec,
    *,
    parameter_values: Mapping[str, object],
) -> LocalGlobalMixtureReport:
    """Evaluate the gated HTT local/global mixture skeleton."""

    if not isinstance(spec, LocalGlobalMixtureSpec):
        raise TypeError("spec must be a LocalGlobalMixtureSpec")
    values = dict(parameter_values)
    blocked_reasons: list[str] = []
    audit_for_match = (
        spec.response_overlap_audit
        if isinstance(spec.response_overlap_audit, ResponseOverlapAudit)
        else None
    )
    rank_payload: dict[str, object]
    try:
        audit = require_rank_audit_for_model_run(spec.response_overlap_audit)
        rank_payload = {
            "allowed": True,
            "artifact_id": audit.artifact_id,
            "config_hash": audit.manifest.config_hash,
            "rank_status": audit.rank_status,
            "rho_LB_GT": audit.rho_LB_GT,
        }
    except (RuntimeError, TypeError) as exc:
        blocked_reasons.append(str(exc).replace("rank audit blocks model run: ", ""))
        rank_payload = {"allowed": False, "blocked_reason": str(exc)}

    response_consistency_payload, response_consistency_reasons = (
        _response_consistency_gate(spec, audit_for_match)
    )
    blocked_reasons.extend(response_consistency_reasons)

    full_design_payload, full_design_reasons = _full_design_rank_gate(spec)
    blocked_reasons.extend(full_design_reasons)

    local_gate = evaluate_global_tilt_local_null_gate(
        spec.local_null_fpr_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        report_hash=spec.local_null_report_hash,
        response_overlap_config_hash=spec.response_overlap_config_hash,
    )
    blocked_reasons.extend(local_gate.blocked_reasons)
    survey_gate = evaluate_survey_systematic_null_gate(
        spec.survey_systematic_null_fpr_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=spec.survey_systematic_null_config_hash,
        input_hashes=spec.survey_systematic_null_input_hashes,
        report_hash=spec.survey_systematic_null_report_hash,
        response_overlap_config_hash=spec.response_overlap_config_hash,
        selection_metadata_hash=spec.selection_metadata_hash,
        survey_axis_hash=spec.survey_axis_hash,
        require_external_bindings=spec.survey_systematic_null_fpr_report is not None,
    )
    blocked_reasons.extend(survey_gate.blocked_reasons)

    for block in spec.blocks:
        if block.parameter_name not in values:
            blocked_reasons.append(f"parameter_missing:{block.parameter_name}")
            continue
        if _generated_parameter_name(block.parameter_name):
            blocked_reasons.append(f"generated_functional_parameter:{block.parameter_name}")
            continue
        parameter = _finite_float(values[block.parameter_name], block.parameter_name)
        if block.kind == "noise" and parameter < 0.0:
            blocked_reasons.append("noise_parameter_negative")

    blocked_reasons = list(_dedupe(blocked_reasons))
    ready = not blocked_reasons
    total_log_likelihood: float | None = None
    residual_chi2: float | None = None
    block_payloads: dict[str, dict[str, object]] = {}
    generated_functionals: dict[str, object] = {
        "status": "blocked" if not ready else "generated",
        "fit_attenuation_score": None,
        "gaussian_density_score": None,
        "survey_penalized_fit_score": None,
        "canonical_xqpi_fg_labels_used": False,
    }
    if ready:
        observed = np.asarray(spec.observable_vector, dtype=float)
        base_covariance = np.asarray(spec.covariance, dtype=float)
        prediction = np.zeros_like(observed, dtype=float)
        noise_variance = np.zeros_like(observed, dtype=float)
        block_quadratics: dict[str, float] = {}
        for block in spec.blocks:
            response = np.asarray(block.response, dtype=float)
            theta = _finite_float(values[block.parameter_name], block.parameter_name)
            if block.kind == "noise":
                noise_variance += (theta * response) ** 2
                block_quadratics[block.kind] = float(np.sum(noise_variance))
            else:
                prediction += theta * response
        covariance = base_covariance + np.diag(noise_variance)
        sign, logdet = np.linalg.slogdet(covariance)
        if sign <= 0 or not math.isfinite(float(logdet)):
            blocked_reasons.append("covariance_logdet_invalid")
            ready = False
        else:
            residual = observed - prediction
            solution = np.linalg.solve(covariance, residual)
            residual_chi2 = float(residual @ solution)
            total_log_likelihood = float(
                -0.5
                * (
                    residual_chi2
                    + float(logdet)
                    + observed.size * math.log(2.0 * math.pi)
                )
            )
            precision = np.linalg.inv(covariance)
            for block in spec.blocks:
                response = np.asarray(block.response, dtype=float)
                theta = _finite_float(values[block.parameter_name], block.parameter_name)
                if block.kind != "noise":
                    block_quadratics[block.kind] = float(
                        (theta * response) @ precision @ (theta * response)
                    )
            f_total = float(math.exp(max(-60.0, min(60.0, -0.5 * residual_chi2))))
            g_total = float(math.exp(max(-60.0, min(60.0, total_log_likelihood))))
            survey_q = max(0.0, block_quadratics.get("survey_systematic", 0.0))
            generated_functionals = {
                "status": "generated",
                "fit_attenuation_score": f_total,
                "gaussian_density_score": g_total,
                "survey_penalized_fit_score": float(f_total / (1.0 + survey_q)),
                "canonical_xqpi_fg_labels_used": False,
            }

    for block in spec.blocks:
        theta = values.get(block.parameter_name)
        block_payloads[block.kind] = {
            **block.as_payload(),
            "parameter_value": None if theta is None else float(theta),
            "log_likelihood_contribution": (
                None
                if total_log_likelihood is None
                else (
                    total_log_likelihood
                    if block.kind == "noise"
                    else None
                )
            ),
            "separate_mixture_block": True,
        }

    if ready:
        claim_tier = ClaimTier.CONDITIONAL
        production_status = "diagnostic_only"
        evaluation_status = "ready_diagnostic_likelihood"
        failed_gates: list[str] = []
    else:
        claim_tier = ClaimTier.BLOCKED
        evaluation_status = "blocked_missing_prerequisites"
        if any("rank" in reason for reason in blocked_reasons):
            production_status = "blocked_rank_deficient"
        elif any("mismatch" in reason or "required" in reason for reason in blocked_reasons):
            production_status = "blocked_provenance_mismatch"
        else:
            production_status = "blocked_missing_null_mocks"
        failed_gates = blocked_reasons
        total_log_likelihood = None
        residual_chi2 = None
        generated_functionals = {
            "status": "blocked",
            "fit_attenuation_score": None,
            "gaussian_density_score": None,
            "survey_penalized_fit_score": None,
            "canonical_xqpi_fg_labels_used": False,
        }

    input_hashes = _manifest_input_hashes(spec)
    manifest = ArtifactManifest(
        artifact_id=spec.artifact_id,
        artifact_path=spec.artifact_path,
        owner=Owner.HTT,
        implementation_scope=ImplementationScope.HTT,
        claim_tier=claim_tier,
        production_status=production_status,  # type: ignore[arg-type]
        created_by=_CREATED_BY,
        git_commit=spec.git_commit,
        config_hash=_report_config_hash(spec),
        input_hashes=input_hashes,
        code_version=spec.git_commit or spec.worktree_state or "unknown",
        schema_version=SCHEMA_VERSION,
        caveats=list(spec.caveats),
        required_gates=[
            "response_overlap_rank_ready",
            "local_null_fpr_gate_ready",
            "survey_systematic_null_fpr_gate_ready",
            "local_global_beta_fields_separate",
            "generated_functionals_not_primitive_parameters",
            "response_overlap_audit_responses_match_blocks",
            "full_local_global_survey_design_rank_ready",
        ],
        passed_gates=(
            [
                "response_overlap_rank_ready",
                "local_null_fpr_gate_ready",
                "survey_systematic_null_fpr_gate_ready",
                "local_global_beta_fields_separate",
                "generated_functionals_not_primitive_parameters",
                "response_overlap_audit_responses_match_blocks",
                "full_local_global_survey_design_rank_ready",
            ]
            if ready
            else [
                "local_global_beta_fields_separate",
                "generated_functionals_not_primitive_parameters",
            ]
        ),
        failed_gates=failed_gates,
        statistics_definitions={
            "surface": "LocalGlobalMixtureReport",
            "local_null_fpr_gate": local_gate.to_metadata(),
            "survey_systematic_null_fpr_gate": survey_gate.to_metadata(),
            "response_overlap_rank_gate": rank_payload,
            "response_overlap_audit_response_consistency_gate": (
                response_consistency_payload
            ),
            "full_local_global_survey_design_rank_gate": full_design_payload,
            "block_roles": {block.kind: block.role for block in spec.blocks},
            "generated_functionals": (
                "fit_attenuation_score, gaussian_density_score, and "
                "survey_penalized_fit_score are noncanonical diagnostic "
                "values computed after primitive block parameters are evaluated"
            ),
            "authorization_scope": "local_global_discrimination_candidate_only",
            "production_ceiling": "diagnostic_only_pre_native_solver",
        },
    )
    return LocalGlobalMixtureReport(
        manifest=manifest,
        spec=spec,
        block_payloads=block_payloads,
        gate_payloads={
            "response_overlap_rank_gate": rank_payload,
            "response_overlap_audit_response_consistency_gate": (
                response_consistency_payload
            ),
            "full_local_global_survey_design_rank_gate": full_design_payload,
            "local_null_fpr_gate": local_gate.to_metadata(),
            "survey_systematic_null_fpr_gate": survey_gate.to_metadata(),
        },
        generated_functionals=generated_functionals,
        evaluation_status=evaluation_status,
        blocked_reasons=tuple(blocked_reasons),
        total_log_likelihood=total_log_likelihood,
        residual_chi2=residual_chi2,
        transfer_source=spec.transfer_source,
    )


def _report_config_hash(spec: LocalGlobalMixtureSpec) -> str:
    return _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "artifact_id": spec.artifact_id,
            "config_hash": spec.config_hash,
            "blocks": [block.as_payload() for block in spec.blocks],
            "covariance": spec.covariance,
            "observable_vector": spec.observable_vector,
        }
    )


def _manifest_input_hashes(spec: LocalGlobalMixtureSpec) -> list[str]:
    inputs: list[str] = [*spec.input_hashes]
    if spec.response_overlap_audit is not None:
        inputs.append(spec.response_overlap_audit.manifest.config_hash)
        inputs.extend(str(item) for item in spec.response_overlap_audit.input_hashes)
    if spec.local_null_fpr_report is not None:
        inputs.append(spec.local_null_fpr_report.report_hash)
        inputs.extend(str(item) for item in spec.local_null_fpr_report.manifest.input_hashes)
    if spec.survey_systematic_null_fpr_report is not None:
        inputs.append(spec.survey_systematic_null_fpr_report.report_hash)
        inputs.extend(
            str(item)
            for item in spec.survey_systematic_null_fpr_report.manifest.input_hashes
        )
    return list(dict.fromkeys(inputs))
