"""Response-overlap and rank audit for local/global HTT discrimination."""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np
from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
)
from common.enum_compat import StrEnum
from common.transfer_registry import (
    TransferSource,
    validate_transfer_dependent_result,
)

SCHEMA_VERSION = "htt.response_overlap_audit.v1"
DEFAULT_CAVEAT = (
    "ResponseOverlapAudit is a pre-inference HTT diagnostic rank audit; "
    "it does not authorize model-dependent inference runs."
)

_FORBIDDEN_KEYS = (
    "posterior",
    "posterior_odds",
    "log_evidence",
    "lnb",
    "likelihood",
    "evidence_weight",
    "bayes_factor",
    "model_weight",
    "mio_certificate",
    "truth_certificate",
    "family_rank",
    "best_family",
    "geometry_label",
    "native_solver_label",
)
_FORBIDDEN_TERMS = (
    "posterior",
    "posterior odds",
    "evidence",
    "likelihood",
    "bayes factor",
    "model weight",
    "truth " + "certificate",
    "mio posterior",
    "mio evidence",
    "family " + "identification",
    "family " + "identified",
    "family classification",
    "geometry",
    "native solver " + "result",
    "external transfer " + "validated as " + "native",
    "validated as native",
    "native validated",
)
_EXTERNAL_TRANSFER_SOURCES = {
    TransferSource.ANICLASS_EXTERNAL.value,
    TransferSource.EXTERNAL_TRANSFER.value,
    TransferSource.EMPIRICAL_PROXY.value,
}


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _optional_non_empty(value: object | None, name: str) -> str | None:
    if value is None:
        return None
    return _non_empty(value, name)


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


def _normalise_claim_text(value: object) -> str:
    return " ".join(str(value).lower().replace("_", " ").replace("-", " ").split())


def _plain_json(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_plain_json(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("metadata floats must be finite")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    raise TypeError(f"value {value!r} is not JSON-compatible")


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _scan_reserved_language(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalise_claim_text(key)
            for forbidden in _FORBIDDEN_KEYS:
                if _normalise_claim_text(forbidden) in key_text:
                    raise ValueError(f"{name} contains reserved key {key!r}")
            _scan_reserved_language(item, name)
        return
    if isinstance(value, (str, bytes)):
        text = _normalise_claim_text(value)
        for term in _FORBIDDEN_TERMS:
            if _normalise_claim_text(term) in text:
                raise ValueError(f"{name} contains reserved report language: {term}")
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_reserved_language(item, name)


def _normalise_metadata(
    value: Mapping[str, object] | None,
    name: str,
) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    try:
        result = _plain_json(dict(value))
    except TypeError as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{name} must be a mapping")
    json.dumps(result, sort_keys=True, allow_nan=False)
    _scan_reserved_language(result, name)
    return result


def _response_vector(values: Sequence[object], name: str) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a non-string sequence")
    vector = np.asarray(tuple(float(value) for value in values), dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"{name} must be a non-empty vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain finite values")
    return vector


def _response_block(values: Sequence[Sequence[object]], n_obs: int) -> np.ndarray:
    if isinstance(values, (str, bytes)) or not values:
        return np.zeros((n_obs, 0), dtype=float)
    columns = [_response_vector(value, "nuisance_responses") for value in values]
    if any(column.size != n_obs for column in columns):
        raise ValueError("nuisance responses must have the same length as responses")
    return np.column_stack(columns)


def _covariance_matrix(value: object, n_obs: int) -> np.ndarray:
    covariance = np.asarray(value, dtype=float)
    if covariance.shape != (n_obs, n_obs):
        raise ValueError("covariance must be square with response-vector length")
    if not np.all(np.isfinite(covariance)):
        raise ValueError("covariance must contain finite values")
    if not np.allclose(covariance, covariance.T, rtol=1.0e-10, atol=1.0e-12):
        raise ValueError("covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(covariance)
    if np.any(eigenvalues < -1.0e-12):
        raise ValueError("covariance must be positive semidefinite")
    if np.any(eigenvalues <= 1.0e-12):
        raise ValueError("covariance must be positive definite for whitening")
    return covariance


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
    projector = np.eye(n_obs) - q @ q.T
    return projector, rank, tuple(float(value) for value in singular_values)


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    payload = _plain_json(asdict(manifest))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a mapping")
    return payload


def _validate_transfer(
    *,
    transfer_source: str,
    transfer_spec_id: str | None,
    transfer_metadata: Mapping[str, object] | None,
) -> tuple[str, str | None, dict[str, Any] | None]:
    source = _non_empty(transfer_source, "transfer_source")
    TransferSource(source)
    spec_id = _optional_non_empty(transfer_spec_id, "transfer_spec_id")
    metadata = (
        None
        if transfer_metadata is None
        else _normalise_metadata(transfer_metadata, "transfer_metadata")
    )
    if source == TransferSource.NONE.value:
        if spec_id is not None or metadata is not None:
            raise ValueError("transfer_source='none' cannot carry transfer provenance")
        return source, None, None
    if source not in _EXTERNAL_TRANSFER_SOURCES:
        raise ValueError("PR-060 response audit cannot claim native transfer provenance")
    if spec_id is None or metadata is None:
        raise ValueError("external response audit requires transfer_spec_id and metadata")
    validate_transfer_dependent_result(metadata)
    if str(metadata.get("transfer_source")) != source:
        raise ValueError("transfer_metadata source must match transfer_source")
    if str(metadata.get("transfer_id")) != spec_id:
        raise ValueError("transfer_metadata transfer_id must match transfer_spec_id")
    return source, spec_id, metadata


def _rank_precondition_blocked_reasons(
    audit: "ResponseOverlapAudit",
) -> tuple[str, ...]:
    reasons: list[str] = []
    if audit.claim_status != "identifiable_diagnostic_candidate":
        reasons.append(f"claim_status={audit.claim_status}")
    if audit.rank_status != "full_rank":
        reasons.append(f"rank_status={audit.rank_status}")
    if audit.projected_rank < 2:
        reasons.append("rank_deficient")
    if audit.rho_LB_GT is None:
        reasons.append("rho_unavailable")
    if audit.no_claim_reasons:
        reasons.extend(str(reason) for reason in audit.no_claim_reasons)
    if any(float(norm) <= audit.rank_threshold for norm in audit.projected_norms):
        reasons.append("zero_projected_response")
    if (
        audit.rho_LB_GT is not None
        and abs(float(audit.rho_LB_GT)) >= audit.max_abs_overlap_for_claim
    ):
        reasons.append("response_overlap_degenerate")
    return tuple(dict.fromkeys(reasons))


@dataclass(frozen=True)
class ResponseOverlapAudit:
    """Pre-inference rank audit for local-boost/global-tilt responses."""

    local_boost_response: tuple[float, ...]
    global_tilt_response: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]
    observable_labels: tuple[str, ...]
    artifact_id: str
    artifact_path: str
    input_hashes: tuple[str, ...]
    generating_command: str
    nuisance_responses: tuple[tuple[float, ...], ...] = ()
    nuisance_labels: tuple[str, ...] = ()
    rank_atol: float = 1.0e-12
    rank_rtol: float = 0.0
    max_abs_overlap_for_claim: float = 0.95
    git_commit: str | None = None
    worktree_state: str | None = None
    transfer_source: str = "none"
    transfer_spec_id: str | None = None
    transfer_metadata: Mapping[str, object] | None = None
    sky_support_status: str = "not_directional"
    mask_status: str = "not_applicable"
    covariance_status: str = "diagnostic_covariance_supplied"
    null_mock_status: str = "not_calibrated"
    artifact_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_CAVEAT,))

    def __post_init__(self) -> None:
        local = _response_vector(self.local_boost_response, "local_boost_response")
        global_response = _response_vector(
            self.global_tilt_response,
            "global_tilt_response",
        )
        if local.size != global_response.size:
            raise ValueError("local and global responses must have the same length")
        observable_labels = _tuple_of_str(
            self.observable_labels,
            "observable_labels",
            require_non_empty=True,
        )
        if len(observable_labels) != local.size:
            raise ValueError("observable_labels length must match responses")
        covariance = _covariance_matrix(self.covariance, local.size)
        nuisance = _response_block(self.nuisance_responses, local.size)
        nuisance_labels = _tuple_of_str(self.nuisance_labels, "nuisance_labels")
        if (
            nuisance.shape[1]
            and nuisance_labels
            and len(nuisance_labels) != nuisance.shape[1]
        ):
            raise ValueError("nuisance_labels length must match nuisance responses")

        rank_atol = float(self.rank_atol)
        rank_rtol = float(self.rank_rtol)
        if not math.isfinite(rank_atol) or rank_atol < 0.0:
            raise ValueError("rank_atol must be finite nonnegative")
        if not math.isfinite(rank_rtol) or rank_rtol < 0.0:
            raise ValueError("rank_rtol must be finite nonnegative")
        max_overlap = float(self.max_abs_overlap_for_claim)
        if not math.isfinite(max_overlap) or not 0.0 < max_overlap < 1.0:
            raise ValueError("max_abs_overlap_for_claim must be in (0, 1)")

        artifact_id = _non_empty(self.artifact_id, "artifact_id")
        artifact_path = _non_empty(self.artifact_path, "artifact_path")
        input_hashes = _tuple_of_str(
            self.input_hashes,
            "input_hashes",
            require_non_empty=True,
        )
        generating_command = _non_empty(self.generating_command, "generating_command")
        git_commit = _optional_non_empty(self.git_commit, "git_commit")
        worktree_state = _optional_non_empty(self.worktree_state, "worktree_state")
        if git_commit is None and worktree_state is None:
            raise ValueError("ResponseOverlapAudit requires git_commit or worktree_state")
        artifact_metadata = _normalise_metadata(
            self.artifact_metadata,
            "artifact_metadata",
        )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_CAVEAT not in caveats:
            caveats = (DEFAULT_CAVEAT, *caveats)
        _scan_reserved_language(caveats, "caveats")
        transfer_source, transfer_spec_id, transfer_metadata = _validate_transfer(
            transfer_source=self.transfer_source,
            transfer_spec_id=self.transfer_spec_id,
            transfer_metadata=self.transfer_metadata,
        )
        artifact_metadata = _freeze_json(artifact_metadata)
        transfer_metadata = (
            None if transfer_metadata is None else _freeze_json(transfer_metadata)
        )
        sky_support_status = _non_empty(self.sky_support_status, "sky_support_status")
        mask_status = _non_empty(self.mask_status, "mask_status")
        covariance_status = _non_empty(self.covariance_status, "covariance_status")
        null_mock_status = _non_empty(self.null_mock_status, "null_mock_status")

        whitening = _inverse_sqrt_covariance(covariance)
        response_matrix = np.column_stack((local, global_response))
        white_response = whitening @ response_matrix
        white_nuisance = whitening @ nuisance
        projector, nuisance_rank, nuisance_singular_values = _nuisance_projector(
            white_nuisance,
            atol=rank_atol,
            rtol=rank_rtol,
        )
        projected = projector @ white_response
        raw_singular_values = np.linalg.svd(white_response, compute_uv=False)
        projected_singular_values = np.linalg.svd(projected, compute_uv=False)
        raw_rank, _ = _rank_from_singular_values(
            raw_singular_values,
            atol=rank_atol,
            rtol=rank_rtol,
        )
        projected_rank, rank_threshold = _rank_from_singular_values(
            projected_singular_values,
            atol=rank_atol,
            rtol=rank_rtol,
        )
        projected_norms = np.linalg.norm(projected, axis=0)
        zero_projected = any(float(norm) <= rank_threshold for norm in projected_norms)
        if zero_projected:
            rho: float | None = None
        else:
            numerator = float(projected[:, 0] @ projected[:, 1])
            denominator = float(projected_norms[0] * projected_norms[1])
            rho = float(np.clip(numerator / denominator, -1.0, 1.0))

        no_claim_reasons: list[str] = []
        if projected_rank < 2:
            no_claim_reasons.append("rank_deficient")
        if zero_projected:
            no_claim_reasons.append("zero_projected_response")
        if rho is None:
            no_claim_reasons.append("rho_unavailable")
        if rho is not None and abs(rho) >= max_overlap:
            no_claim_reasons.append("response_overlap_degenerate")

        if no_claim_reasons:
            rank_status = "rank_deficient" if projected_rank < 2 else "overlap_degenerate"
            claim_status = "no_claim"
            model_run_gate = {
                "allowed": False,
                "blocked_reasons": [
                    "rank_audit_no_identifiable_direction",
                    *no_claim_reasons,
                ],
                "authorization_scope": "rank_precondition_only",
            }
        else:
            rank_status = "full_rank"
            claim_status = "identifiable_diagnostic_candidate"
            model_run_gate = {
                "allowed": True,
                "blocked_reasons": [],
                "authorization_scope": "rank_precondition_only",
            }
        condition_number = (
            float("inf")
            if projected_singular_values.size == 0
            or float(np.min(projected_singular_values)) <= rank_threshold
            else float(
                np.max(projected_singular_values) / np.min(projected_singular_values)
            )
        )
        config_hash = _stable_hash(
            {
                "artifact_id": artifact_id,
                "covariance": covariance.tolist(),
                "local_boost_response": local.tolist(),
                "global_tilt_response": global_response.tolist(),
                "nuisance_responses": nuisance.T.tolist(),
                "observable_labels": observable_labels,
                "rank_atol": rank_atol,
                "rank_rtol": rank_rtol,
                "schema_version": SCHEMA_VERSION,
            }
        )
        manifest = ArtifactManifest(
            artifact_id=artifact_id,
            artifact_path=artifact_path,
            owner=Owner.HTT,
            implementation_scope=ImplementationScope.HTT,
            claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
            production_status="diagnostic_only",
            created_by="htt.departure.response_overlap",
            git_commit=git_commit,
            config_hash=config_hash,
            input_hashes=list(input_hashes),
            code_version=git_commit or worktree_state or "unknown",
            schema_version=SCHEMA_VERSION,
            caveats=list(caveats),
            required_gates=[
                "rank_audit_recorded",
                "nuisance_projection_status_recorded",
                "no_claim_if_rank_deficient",
            ],
            passed_gates=["rank_audit_recorded", "nuisance_projection_status_recorded"],
            failed_gates=(
                []
                if model_run_gate["allowed"]
                else ["no_claim_if_rank_deficient"]
            ),
            statistics_definitions={
                "rho_LB_GT": "whitened projected cosine between local boost and global tilt response columns",
                "projected_rank": "SVD rank of nuisance-projected whitened response matrix",
                "rank_threshold": "rank_atol + rank_rtol * max(projected singular values)",
            },
        )

        object.__setattr__(self, "local_boost_response", tuple(float(v) for v in local))
        object.__setattr__(
            self,
            "global_tilt_response",
            tuple(float(v) for v in global_response),
        )
        object.__setattr__(
            self,
            "covariance",
            tuple(tuple(float(item) for item in row) for row in covariance),
        )
        object.__setattr__(
            self,
            "nuisance_responses",
            tuple(tuple(float(item) for item in row) for row in nuisance.T),
        )
        object.__setattr__(self, "observable_labels", observable_labels)
        object.__setattr__(self, "nuisance_labels", nuisance_labels)
        object.__setattr__(self, "rank_atol", rank_atol)
        object.__setattr__(self, "rank_rtol", rank_rtol)
        object.__setattr__(self, "max_abs_overlap_for_claim", max_overlap)
        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "artifact_path", artifact_path)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "transfer_source", transfer_source)
        object.__setattr__(self, "transfer_spec_id", transfer_spec_id)
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        object.__setattr__(self, "sky_support_status", sky_support_status)
        object.__setattr__(self, "mask_status", mask_status)
        object.__setattr__(self, "covariance_status", covariance_status)
        object.__setattr__(self, "null_mock_status", null_mock_status)
        object.__setattr__(self, "artifact_metadata", artifact_metadata)
        object.__setattr__(self, "caveats", caveats)
        object.__setattr__(self, "rho_LB_GT", rho)
        object.__setattr__(self, "raw_rank", raw_rank)
        object.__setattr__(self, "projected_rank", projected_rank)
        object.__setattr__(self, "nuisance_rank", nuisance_rank)
        object.__setattr__(self, "rank_threshold", rank_threshold)
        object.__setattr__(
            self,
            "singular_values",
            tuple(float(value) for value in projected_singular_values),
        )
        object.__setattr__(
            self,
            "raw_singular_values",
            tuple(float(value) for value in raw_singular_values),
        )
        object.__setattr__(self, "nuisance_singular_values", nuisance_singular_values)
        object.__setattr__(
            self,
            "projected_norms",
            tuple(float(v) for v in projected_norms),
        )
        object.__setattr__(self, "condition_number", condition_number)
        object.__setattr__(self, "null_space_dimension", 2 - projected_rank)
        object.__setattr__(self, "rank_status", rank_status)
        object.__setattr__(self, "claim_status", claim_status)
        object.__setattr__(
            self,
            "no_claim_reasons",
            tuple(dict.fromkeys(no_claim_reasons)),
        )
        object.__setattr__(
            self,
            "model_run_gate",
            MappingProxyType(
                {
                    "allowed": bool(model_run_gate["allowed"]),
                    "blocked_reasons": tuple(model_run_gate["blocked_reasons"]),
                    "authorization_scope": "rank_precondition_only",
                }
            ),
        )
        object.__setattr__(
            self,
            "nuisance_projection_status",
            "projected" if nuisance.shape[1] else "not_requested",
        )
        object.__setattr__(self, "manifest", manifest)

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": Owner.HTT.value,
            "implementation_scope": ImplementationScope.HTT.value,
            "claim_tier": ClaimTier.DIAGNOSTIC_ONLY.value,
            "production_status": "diagnostic_only",
            "schema_version": SCHEMA_VERSION,
            "manifest": _manifest_payload(self.manifest),
            "rho_LB_GT": self.rho_LB_GT,
            "raw_rank": self.raw_rank,
            "projected_rank": self.projected_rank,
            "nuisance_rank": self.nuisance_rank,
            "rank_status": self.rank_status,
            "claim_status": self.claim_status,
            "no_claim_reasons": list(self.no_claim_reasons),
            "model_run_gate": dict(self.model_run_gate),
            "rank_atol": self.rank_atol,
            "rank_rtol": self.rank_rtol,
            "rank_threshold": self.rank_threshold,
            "singular_values": list(self.singular_values),
            "raw_singular_values": list(self.raw_singular_values),
            "nuisance_singular_values": list(self.nuisance_singular_values),
            "projected_norms": list(self.projected_norms),
            "condition_number": self.condition_number,
            "null_space_dimension": self.null_space_dimension,
            "nuisance_projection_status": self.nuisance_projection_status,
            "observable_labels": list(self.observable_labels),
            "nuisance_labels": list(self.nuisance_labels),
            "local_boost_response": list(self.local_boost_response),
            "global_tilt_response": list(self.global_tilt_response),
            "nuisance_responses": [list(row) for row in self.nuisance_responses],
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "transfer_metadata": (
                None
                if self.transfer_metadata is None
                else _plain_json(self.transfer_metadata)
            ),
            "sky_support_status": self.sky_support_status,
            "mask_status": self.mask_status,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "config_hash": self.manifest.config_hash,
            "input_hashes": list(self.input_hashes),
            "artifact_metadata": _plain_json(self.artifact_metadata),
            "caveats": list(self.caveats),
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
        }


def build_response_overlap_audit(
    *,
    local_boost_response: Sequence[object],
    global_tilt_response: Sequence[object],
    covariance: object,
    observable_labels: Sequence[object],
    artifact_id: str,
    artifact_path: str,
    input_hashes: Sequence[object],
    generating_command: str,
    nuisance_responses: Sequence[Sequence[object]] = (),
    nuisance_labels: Sequence[object] = (),
    rank_atol: float = 1.0e-12,
    rank_rtol: float = 0.0,
    max_abs_overlap_for_claim: float = 0.95,
    git_commit: str | None = None,
    worktree_state: str | None = None,
    transfer_source: str = "none",
    transfer_spec_id: str | None = None,
    transfer_metadata: Mapping[str, object] | None = None,
    sky_support_status: str = "not_directional",
    mask_status: str = "not_applicable",
    covariance_status: str = "diagnostic_covariance_supplied",
    null_mock_status: str = "not_calibrated",
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> ResponseOverlapAudit:
    """Build a validated local-boost/global-tilt response-overlap audit."""

    return ResponseOverlapAudit(
        local_boost_response=tuple(float(value) for value in local_boost_response),
        global_tilt_response=tuple(float(value) for value in global_tilt_response),
        covariance=np.asarray(covariance, dtype=float),
        observable_labels=_tuple_of_str(
            observable_labels,
            "observable_labels",
            require_non_empty=True,
        ),
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        input_hashes=_tuple_of_str(
            input_hashes,
            "input_hashes",
            require_non_empty=True,
        ),
        generating_command=generating_command,
        nuisance_responses=tuple(
            tuple(float(item) for item in row) for row in nuisance_responses
        ),
        nuisance_labels=_tuple_of_str(nuisance_labels, "nuisance_labels"),
        rank_atol=rank_atol,
        rank_rtol=rank_rtol,
        max_abs_overlap_for_claim=max_abs_overlap_for_claim,
        git_commit=git_commit,
        worktree_state=worktree_state,
        transfer_source=transfer_source,
        transfer_spec_id=transfer_spec_id,
        transfer_metadata=transfer_metadata,
        sky_support_status=sky_support_status,
        mask_status=mask_status,
        covariance_status=covariance_status,
        null_mock_status=null_mock_status,
        artifact_metadata=artifact_metadata,
        caveats=(DEFAULT_CAVEAT,) if caveats is None else tuple(caveats),
    )


def require_rank_audit_for_model_run(
    audit: ResponseOverlapAudit | None,
) -> ResponseOverlapAudit:
    """Fail closed when the rank precondition is missing or no-claim.

    Passing this guard means only that the response-rank precondition did not
    block. Directional posterior/evidence emission must still pass the full HTT
    readiness gates.
    """

    if audit is None:
        raise RuntimeError("rank audit blocks model run: response_overlap_rank_audit_missing")
    if not isinstance(audit, ResponseOverlapAudit):
        raise TypeError("require_rank_audit_for_model_run expects ResponseOverlapAudit")
    blocked_reasons = _rank_precondition_blocked_reasons(audit)
    if blocked_reasons:
        reasons = ", ".join(
            str(reason) for reason in (
                "rank_audit_no_identifiable_direction",
                *blocked_reasons,
            )
        )
        raise RuntimeError(f"rank audit blocks model run: {reasons}")
    return audit


__all__ = [
    "DEFAULT_CAVEAT",
    "ResponseOverlapAudit",
    "SCHEMA_VERSION",
    "build_response_overlap_audit",
    "require_rank_audit_for_model_run",
]
