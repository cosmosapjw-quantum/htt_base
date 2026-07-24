"""Template-fit diagnostics for OBSSTAT feature payloads.

OBSSTAT owns caller-supplied observable feature extraction only.  The template
fit records a deterministic mean-template amplitude and weighted chi-square
improvement; it is not HTT model output, a MIO diagnostic report, a native
solver result, transfer validation, morphology compatibility, or a Bianchi
family label.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any

import numpy as np

__all__ = [
    "CovarianceAssumption",
    "OrientationScanMetadata",
    "TemplateFitDiagnostic",
    "fit_template_diagnostic",
]


_SCHEMA_VERSION = "obsstat.template_fit.v1"
_SCAN_SCHEMA_VERSION = "obsstat.template_fit.orientation_scan.v1"
_COVARIANCE_SCHEMA_VERSION = "obsstat.template_fit.covariance_assumption.v1"
_FEATURE_CAVEAT = (
    "template-fit feature only; deterministic mean-template diagnostic, "
    "not HTT model output, not MIO output, and not a family label"
)
_ALLOWED_COVARIANCE_KINDS = {
    "identity",
    "diagonal_inverse_variance",
    "full_covariance",
}
_REQUIRED_SCAN_VOLUME_FIELDS = {
    "orientation_parameterization",
    "orientation_count",
    "global_local_status",
}
_ALLOWED_GLOBAL_LOCAL_STATUS = {
    "global_corrected",
    "tracked_not_corrected",
    "local_unadjusted_with_trials",
}
_FORBIDDEN_TEXT_PARTS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "certificate",
    "truth",
    "geometry detected",
    "detected geometry",
    "family identified",
    "family identification",
    "family ranking",
    "native solver result",
    "morphology compatibility",
)


@dataclass(frozen=True)
class OrientationScanMetadata:
    """Orientation-grid metadata for a deterministic template scan."""

    scan_id: str
    orientation_parameterization: str
    orientation_count: int
    scan_volume: Mapping[str, Any]
    coordinate_frame: str
    sky_support_status: str
    mask_status: str
    config_hash: str
    input_hashes: Sequence[str]
    best_orientation: Mapping[str, Any] = field(default_factory=dict)
    orientation_units: str = "degrees"
    look_elsewhere_status: str = "tracked_not_corrected"
    caveats: tuple[str, ...] = (
        "orientation scan metadata only; no calibrated tail probability supplied",
    )
    metadata_schema: str = _SCAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.metadata_schema != _SCAN_SCHEMA_VERSION:
            raise ValueError("OrientationScanMetadata.metadata_schema is not allowed")
        if not str(self.scan_id).strip():
            raise ValueError("OrientationScanMetadata.scan_id is required")
        if not str(self.orientation_parameterization).strip():
            raise ValueError(
                "OrientationScanMetadata.orientation_parameterization is required"
            )
        count = int(self.orientation_count)
        if count <= 0:
            raise ValueError("OrientationScanMetadata.orientation_count must be positive")
        object.__setattr__(self, "orientation_count", count)
        scan_volume = _json_mapping(self.scan_volume)
        missing = sorted(_REQUIRED_SCAN_VOLUME_FIELDS - set(scan_volume))
        if missing:
            raise ValueError(
                "OrientationScanMetadata.scan_volume missing required field(s): "
                + ", ".join(missing)
            )
        if int(scan_volume["orientation_count"]) != count:
            raise ValueError(
                "OrientationScanMetadata.scan_volume orientation_count mismatch"
            )
        if str(scan_volume["orientation_parameterization"]) != str(
            self.orientation_parameterization
        ):
            raise ValueError(
                "OrientationScanMetadata.scan_volume orientation_parameterization "
                "mismatch"
            )
        status = str(scan_volume["global_local_status"]).strip().lower()
        if status not in _ALLOWED_GLOBAL_LOCAL_STATUS:
            raise ValueError(
                "OrientationScanMetadata.scan_volume global_local_status is not allowed"
            )
        object.__setattr__(self, "scan_volume", scan_volume)
        if not str(self.coordinate_frame).strip():
            raise ValueError("OrientationScanMetadata.coordinate_frame is required")
        if not str(self.sky_support_status).strip():
            raise ValueError("OrientationScanMetadata.sky_support_status is required")
        if not str(self.mask_status).strip():
            raise ValueError("OrientationScanMetadata.mask_status is required")
        if not str(self.orientation_units).strip():
            raise ValueError("OrientationScanMetadata.orientation_units is required")
        if not str(self.look_elsewhere_status).strip():
            raise ValueError("OrientationScanMetadata.look_elsewhere_status is required")
        object.__setattr__(self, "config_hash", _require_hash(self.config_hash, "config_hash"))
        object.__setattr__(
            self,
            "input_hashes",
            _require_input_hashes(self.input_hashes, label="input_hashes"),
        )
        object.__setattr__(self, "best_orientation", _json_mapping(self.best_orientation))
        object.__setattr__(self, "caveats", tuple(str(item) for item in self.caveats))
        _reject_overclaim_text(
            {
                "scan_id": self.scan_id,
                "orientation_parameterization": self.orientation_parameterization,
                "scan_volume": self.scan_volume,
                "coordinate_frame": self.coordinate_frame,
                "sky_support_status": self.sky_support_status,
                "mask_status": self.mask_status,
                "best_orientation": self.best_orientation,
                "orientation_units": self.orientation_units,
                "look_elsewhere_status": self.look_elsewhere_status,
                "caveats": self.caveats,
            }
        )

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-compatible orientation scan metadata."""

        return {
            "metadata_schema": self.metadata_schema,
            "scan_id": self.scan_id,
            "orientation_parameterization": self.orientation_parameterization,
            "orientation_count": self.orientation_count,
            "scan_volume": dict(self.scan_volume),
            "scan_volume_hash": _sha256_payload(self.scan_volume),
            "coordinate_frame": self.coordinate_frame,
            "sky_support_status": self.sky_support_status,
            "mask_status": self.mask_status,
            "best_orientation": dict(self.best_orientation),
            "orientation_units": self.orientation_units,
            "look_elsewhere_status": self.look_elsewhere_status,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class CovarianceAssumption:
    """Declared weighting operator for the template mean branch."""

    kind: str
    covariance_status: str = "identity_weighting"
    inverse_variance_weights: Sequence[float] | None = None
    covariance_matrix: Sequence[Sequence[float]] | None = None
    metadata_schema: str = _COVARIANCE_SCHEMA_VERSION
    caveats: tuple[str, ...] = (
        "covariance metadata is a weighting assumption for the template mean branch",
    )

    def __post_init__(self) -> None:
        if self.metadata_schema != _COVARIANCE_SCHEMA_VERSION:
            raise ValueError("CovarianceAssumption.metadata_schema is not allowed")
        kind = str(self.kind).strip().lower()
        if "anomaly" in kind:
            raise ValueError(
                "covariance anomaly statistics belong in a separate OBSSTAT "
                "covariance branch"
            )
        if kind not in _ALLOWED_COVARIANCE_KINDS:
            raise ValueError(f"CovarianceAssumption.kind is not allowed: {self.kind!r}")
        object.__setattr__(self, "kind", kind)
        status = str(self.covariance_status).strip()
        if not status:
            raise ValueError("CovarianceAssumption.covariance_status is required")
        object.__setattr__(self, "covariance_status", status)
        if kind == "identity":
            if self.inverse_variance_weights is not None or self.covariance_matrix is not None:
                raise ValueError("identity covariance assumption cannot carry weights")
        elif kind == "diagonal_inverse_variance":
            if self.inverse_variance_weights is None:
                raise ValueError("diagonal_inverse_variance values are required")
            weights = _finite_vector(
                self.inverse_variance_weights,
                label="diagonal_inverse_variance",
            )
            if np.any(weights <= 0.0):
                raise ValueError(
                    "diagonal_inverse_variance entries must be positive finite"
                )
            object.__setattr__(
                self,
                "inverse_variance_weights",
                tuple(float(value) for value in weights),
            )
            if self.covariance_matrix is not None:
                raise ValueError(
                    "diagonal_inverse_variance cannot also carry covariance_matrix"
                )
        elif kind == "full_covariance":
            if self.covariance_matrix is None:
                raise ValueError("full_covariance matrix is required")
            matrix = _finite_square_matrix(self.covariance_matrix, label="covariance_matrix")
            if not np.allclose(matrix, matrix.T, rtol=1.0e-10, atol=1.0e-12):
                raise ValueError("full_covariance matrix must be symmetric")
            try:
                np.linalg.cholesky(matrix)
            except np.linalg.LinAlgError as exc:
                raise ValueError(
                    "full_covariance matrix must be positive definite"
                ) from exc
            object.__setattr__(
                self,
                "covariance_matrix",
                tuple(tuple(float(item) for item in row) for row in matrix),
            )
            if self.inverse_variance_weights is not None:
                raise ValueError("full_covariance cannot also carry diagonal weights")
        object.__setattr__(self, "caveats", tuple(str(item) for item in self.caveats))
        _reject_overclaim_text(
            {
                "kind": self.kind,
                "covariance_status": self.covariance_status,
                "caveats": self.caveats,
            }
        )

    @classmethod
    def identity(
        cls,
        *,
        covariance_status: str = "identity_weighting",
    ) -> CovarianceAssumption:
        return cls(kind="identity", covariance_status=covariance_status)

    @classmethod
    def diagonal_inverse_variance(
        cls,
        values: Sequence[float],
        *,
        covariance_status: str = "diagonal_inverse_variance_supplied",
    ) -> CovarianceAssumption:
        return cls(
            kind="diagonal_inverse_variance",
            inverse_variance_weights=tuple(values),
            covariance_status=covariance_status,
        )

    @classmethod
    def full_covariance(
        cls,
        matrix: Sequence[Sequence[float]],
        *,
        covariance_status: str = "full_positive_definite_covariance_supplied",
    ) -> CovarianceAssumption:
        return cls(
            kind="full_covariance",
            covariance_matrix=tuple(tuple(row) for row in matrix),
            covariance_status=covariance_status,
        )

    def weighted_dot(self, left: np.ndarray, right: np.ndarray) -> float:
        """Return ``left.T W right`` for the declared weighting operator."""

        self._require_dimension(left.shape[0])
        if self.kind == "identity":
            return float(np.dot(left, right))
        if self.kind == "diagonal_inverse_variance":
            weights = np.asarray(self.inverse_variance_weights, dtype=float)
            return float(np.dot(left * weights, right))
        matrix = np.asarray(self.covariance_matrix, dtype=float)
        weighted_right = np.linalg.solve(matrix, right)
        return float(np.dot(left, weighted_right))

    def to_metadata(self, *, vector_length: int | None = None) -> dict[str, Any]:
        """Return JSON-compatible covariance weighting metadata."""

        if vector_length is not None:
            self._require_dimension(int(vector_length))
        payload: dict[str, Any] = {
            "metadata_schema": self.metadata_schema,
            "kind": self.kind,
            "covariance_status": self.covariance_status,
            "weighting_role": "template_mean_branch_only",
            "covariance_anomaly_status": "not_evaluated",
            "caveats": list(self.caveats),
        }
        if vector_length is not None:
            payload["vector_length"] = int(vector_length)
        if self.kind == "diagonal_inverse_variance":
            weights = np.asarray(self.inverse_variance_weights, dtype=float)
            payload.update(
                {
                    "weights_hash": _sha256_payload({"weights": weights.tolist()}),
                    "min_weight": float(np.min(weights)),
                    "max_weight": float(np.max(weights)),
                }
            )
        elif self.kind == "full_covariance":
            matrix = np.asarray(self.covariance_matrix, dtype=float)
            payload.update(
                {
                    "covariance_matrix_hash": _sha256_payload(
                        {"covariance_matrix": matrix.tolist()}
                    ),
                    "matrix_shape": list(matrix.shape),
                    "positive_definite_status": "checked_by_cholesky",
                }
            )
        return payload

    def _require_dimension(self, length: int) -> None:
        if self.kind == "identity":
            return
        if self.kind == "diagonal_inverse_variance":
            if len(tuple(self.inverse_variance_weights or ())) != int(length):
                raise ValueError(
                    "diagonal_inverse_variance length must match observed vector"
                )
            return
        matrix = np.asarray(self.covariance_matrix, dtype=float)
        if matrix.shape != (int(length), int(length)):
            raise ValueError("full_covariance shape must match observed vector")


@dataclass(frozen=True)
class TemplateFitDiagnostic:
    """Feature-only deterministic template amplitude diagnostic."""

    amplitude: float
    delta_chi2: float
    chi2_without_template: float
    chi2_with_template: float
    template_norm_weighted: float
    observed_norm_weighted: float
    residual_norm_weighted: float
    vector_length: int
    orientation_scan: OrientationScanMetadata
    covariance_assumption: CovarianceAssumption
    template_label: str = "template"
    rank_status: str = "full_rank_template_direction"
    statistic_role: str = "feature_only"
    model_role: str = "not_model_input"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    config_hash: str = "sha256:config-not-supplied"
    input_hashes: Sequence[str] = field(default_factory=tuple)
    generating_command: str = ""
    git_commit: str | None = None
    worktree_state: str | None = None
    metadata_schema: str = _SCHEMA_VERSION
    caveats: tuple[str, ...] = (_FEATURE_CAVEAT,)

    def __post_init__(self) -> None:
        if self.metadata_schema != _SCHEMA_VERSION:
            raise ValueError("TemplateFitDiagnostic.metadata_schema is not allowed")
        if self.statistic_role != "feature_only":
            raise ValueError("TemplateFitDiagnostic.statistic_role must be feature_only")
        if self.model_role != "not_model_input":
            raise ValueError("TemplateFitDiagnostic.model_role must be not_model_input")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("TemplateFitDiagnostic.claim_tier must be diagnostic_only")
        if self.transfer_source != "none":
            raise ValueError("TemplateFitDiagnostic.transfer_source must be none")
        for field_name in (
            "amplitude",
            "delta_chi2",
            "chi2_without_template",
            "chi2_with_template",
            "template_norm_weighted",
            "observed_norm_weighted",
            "residual_norm_weighted",
        ):
            value = float(getattr(self, field_name))
            if not math.isfinite(value):
                raise ValueError(f"TemplateFitDiagnostic.{field_name} must be finite")
            object.__setattr__(self, field_name, value)
        for field_name in (
            "chi2_without_template",
            "chi2_with_template",
            "template_norm_weighted",
            "observed_norm_weighted",
            "residual_norm_weighted",
        ):
            if float(getattr(self, field_name)) < 0.0:
                raise ValueError(
                    "TemplateFitDiagnostic chi-square values must be non-negative"
                )
        if self.template_norm_weighted <= 0.0:
            raise ValueError(
                "TemplateFitDiagnostic.template_norm_weighted must be positive"
            )
        expected_delta = self.chi2_without_template - self.chi2_with_template
        subtraction_tolerance = max(
            1.0e-12,
            64.0
            * np.finfo(float).eps
            * max(
                abs(self.chi2_without_template),
                abs(self.chi2_with_template),
                abs(self.delta_chi2),
                1.0,
            ),
        )
        if not math.isclose(
            self.delta_chi2,
            expected_delta,
            rel_tol=1.0e-10,
            abs_tol=subtraction_tolerance,
        ):
            raise ValueError(
                "TemplateFitDiagnostic.delta_chi2 must equal "
                "chi2_without_template - chi2_with_template"
            )
        expected_fit_delta = self.amplitude**2 * self.template_norm_weighted
        if not math.isclose(
            self.delta_chi2,
            expected_fit_delta,
            rel_tol=1.0e-10,
            abs_tol=1.0e-12,
        ):
            raise ValueError(
                "TemplateFitDiagnostic.delta_chi2 must match amplitude and "
                "template_norm_weighted"
            )
        if self.delta_chi2 < -1.0e-12:
            raise ValueError(
                "TemplateFitDiagnostic.delta_chi2 must be non-negative for "
                "a fitted template diagnostic"
            )
        if not math.isclose(
            self.observed_norm_weighted,
            self.chi2_without_template,
            rel_tol=1.0e-10,
            abs_tol=1.0e-12,
        ):
            raise ValueError(
                "TemplateFitDiagnostic.observed_norm_weighted must equal "
                "chi2_without_template"
            )
        if not math.isclose(
            self.residual_norm_weighted,
            self.chi2_with_template,
            rel_tol=1.0e-10,
            abs_tol=1.0e-12,
        ):
            raise ValueError(
                "TemplateFitDiagnostic.residual_norm_weighted must equal "
                "chi2_with_template"
            )
        length = int(self.vector_length)
        if length <= 0:
            raise ValueError("TemplateFitDiagnostic.vector_length must be positive")
        object.__setattr__(self, "vector_length", length)
        if not str(self.template_label).strip():
            raise ValueError("TemplateFitDiagnostic.template_label is required")
        if not str(self.rank_status).strip():
            raise ValueError("TemplateFitDiagnostic.rank_status is required")
        object.__setattr__(self, "config_hash", _require_hash(self.config_hash, "config_hash"))
        object.__setattr__(
            self,
            "input_hashes",
            _require_input_hashes(self.input_hashes, label="input_hashes"),
        )
        if not str(self.generating_command).strip():
            raise ValueError("TemplateFitDiagnostic.generating_command is required")
        if not (self.git_commit or self.worktree_state):
            raise ValueError(
                "TemplateFitDiagnostic requires git_commit or worktree_state"
            )
        object.__setattr__(self, "caveats", tuple(str(item) for item in self.caveats))
        _reject_overclaim_text(
            {
                "template_label": self.template_label,
                "rank_status": self.rank_status,
                "generating_command": self.generating_command,
                "git_commit": self.git_commit or "",
                "worktree_state": self.worktree_state or "",
                "caveats": self.caveats,
            }
        )

    def to_feature_payload(self) -> dict[str, Any]:
        """Return an OBSSTAT template-fit feature block for ObservableVector."""

        covariance_metadata = self.covariance_assumption.to_metadata(
            vector_length=self.vector_length
        )
        orientation_metadata = self.orientation_scan.to_metadata()
        template_branch = {
            "branch_role": "deterministic_template_mean_fit",
            "template_label": self.template_label,
            "amplitude": self.amplitude,
            "delta_chi2": self.delta_chi2,
            "DeltaChi2": self.delta_chi2,
            "chi2_without_template": self.chi2_without_template,
            "chi2_with_template": self.chi2_with_template,
            "template_norm_weighted": self.template_norm_weighted,
            "observed_norm_weighted": self.observed_norm_weighted,
            "residual_norm_weighted": self.residual_norm_weighted,
            "rank_status": self.rank_status,
            "orientation_scan": orientation_metadata,
            "covariance_assumption_ref": "covariance_branch.covariance_assumption",
        }
        covariance_branch = {
            "branch_role": "template_weighting_assumption_only",
            "covariance_assumption": covariance_metadata,
            "covariance_anomaly_status": "not_evaluated",
            "collapsed_with_template_mean": False,
            "caveats": [
                "covariance anomaly features must be emitted by a separate "
                "OBSSTAT covariance branch"
            ],
        }
        payload: dict[str, Any] = {
            "metadata_schema": self.metadata_schema,
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": self.claim_tier,
            "production_status": "diagnostic_only",
            "statistic_role": self.statistic_role,
            "model_role": self.model_role,
            "transfer_source": self.transfer_source,
            "template_mean_branch": template_branch,
            "covariance_branch": covariance_branch,
            "branch_separation": {
                "template_mean_branch": "deterministic_template_mean_fit",
                "covariance_branch": "weighting_metadata_only",
                "merged_statistic_allowed": False,
                "covariance_anomaly_result_status": "not_evaluated",
            },
            "orientation_scan_volume": dict(orientation_metadata["scan_volume"]),
            "orientation_scan_volume_hash": orientation_metadata["scan_volume_hash"],
            "covariance_assumption": covariance_metadata,
            "sky_support_status": self.orientation_scan.sky_support_status,
            "mask_status": self.orientation_scan.mask_status,
            "covariance_status": self.covariance_assumption.covariance_status,
            "null_mock_status": "not_supplied",
            "null_calibration": {
                "status": "not_null_calibrated",
                "caveats": ["no matched null ensemble supplied"],
            },
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "claim_status": {
                "geometry_status": "blocked_pre_native_atlas",
                "family_status": "blocked_pre_native_atlas",
                "inference_status": "not_model_input",
                "mio_status": "not_mio_output",
                "covariance_anomaly_status": "not_evaluated",
            },
            "definitions": {
                "amplitude": "a_hat=(t^T W y)/(t^T W t)",
                "DeltaChi2": "chi2_without_template - chi2_with_template",
                "covariance_assumption": (
                    "declared weighting operator W for the deterministic "
                    "template mean fit"
                ),
                "orientation_scan_volume": (
                    "caller-supplied orientation grid metadata; no calibrated "
                    "tail probability is emitted"
                ),
            },
            "caveats": list(self.caveats),
        }
        if self.git_commit is not None:
            payload["git_commit"] = self.git_commit
        if self.worktree_state is not None:
            payload["worktree_state"] = self.worktree_state
        return _json_payload_mapping(payload)


def fit_template_diagnostic(
    *,
    observed: Sequence[float],
    template: Sequence[float],
    orientation_scan: OrientationScanMetadata,
    covariance_assumption: CovarianceAssumption | None = None,
    template_label: str = "template",
    config_hash: str = "sha256:config-not-supplied",
    input_hashes: Sequence[str] = (),
    generating_command: str = "",
    git_commit: str | None = None,
    worktree_state: str | None = None,
    covariance_anomaly_statistic: object | None = None,
) -> TemplateFitDiagnostic:
    """Fit one deterministic template amplitude as an OBSSTAT diagnostic."""

    if covariance_anomaly_statistic is not None:
        raise ValueError(
            "covariance anomaly statistics require a separate OBSSTAT "
            "covariance branch"
        )
    observed_vec, template_vec = _prepare_observed_template(observed, template)
    assumption = covariance_assumption or CovarianceAssumption.identity()
    assumption._require_dimension(observed_vec.shape[0])
    template_norm = assumption.weighted_dot(template_vec, template_vec)
    if not math.isfinite(template_norm) or template_norm <= 0.0:
        raise ValueError("template vector must have positive weighted norm")
    numerator = assumption.weighted_dot(template_vec, observed_vec)
    amplitude = float(numerator / template_norm)
    residual = observed_vec - amplitude * template_vec
    chi2_without = assumption.weighted_dot(observed_vec, observed_vec)
    chi2_with = assumption.weighted_dot(residual, residual)
    delta_chi2 = amplitude**2 * template_norm
    return TemplateFitDiagnostic(
        amplitude=amplitude,
        delta_chi2=float(delta_chi2),
        chi2_without_template=float(chi2_without),
        chi2_with_template=float(chi2_with),
        template_norm_weighted=float(template_norm),
        observed_norm_weighted=float(chi2_without),
        residual_norm_weighted=float(chi2_with),
        vector_length=int(observed_vec.shape[0]),
        orientation_scan=orientation_scan,
        covariance_assumption=assumption,
        template_label=str(template_label),
        rank_status="full_rank_template_direction",
        config_hash=str(config_hash),
        input_hashes=tuple(str(value) for value in input_hashes),
        generating_command=str(generating_command),
        git_commit=git_commit,
        worktree_state=worktree_state,
    )


def _prepare_observed_template(
    observed: Sequence[float],
    template: Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    observed_vec = np.asarray(observed, dtype=float)
    template_vec = np.asarray(template, dtype=float)
    if (
        observed_vec.ndim != 1
        or template_vec.ndim != 1
        or observed_vec.shape != template_vec.shape
        or observed_vec.shape[0] == 0
    ):
        raise ValueError(
            "observed and template vectors must have the same finite "
            "one-dimensional shape"
        )
    if not np.all(np.isfinite(observed_vec)):
        raise ValueError("observed vector entries must be finite")
    if not np.all(np.isfinite(template_vec)):
        raise ValueError("template vector entries must be finite")
    if float(np.linalg.norm(template_vec)) <= 0.0:
        raise ValueError("template vector must have positive norm")
    return observed_vec.astype(float), template_vec.astype(float)


def _finite_vector(value: Sequence[float], *, label: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.ndim != 1 or vector.shape[0] == 0:
        raise ValueError(f"{label} must be a non-empty one-dimensional vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{label} entries must be finite")
    return vector.astype(float)


def _finite_square_matrix(
    value: Sequence[Sequence[float]],
    *,
    label: str,
) -> np.ndarray:
    matrix = np.asarray(value, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
        raise ValueError(f"{label} must be a non-empty square matrix")
    if not np.all(np.isfinite(matrix)):
        raise ValueError(f"{label} entries must be finite")
    return matrix.astype(float)


def _require_hash(value: str, label: str) -> str:
    token = str(value).strip()
    if _is_placeholder_hash(token):
        raise ValueError(f"{label} must be explicit")
    return token


def _require_input_hashes(values: Sequence[str], *, label: str) -> tuple[str, ...]:
    out = tuple(str(value).strip() for value in values)
    if not out or any(_is_placeholder_hash(value) for value in out):
        raise ValueError(f"{label} must be explicit")
    return out


def _is_placeholder_hash(value: str) -> bool:
    token = str(value).strip().lower()
    if not token:
        return True
    return any(
        marker in token
        for marker in ("not-supplied", "placeholder", "pending", "unknown")
    )


def _sha256_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _json_payload_mapping(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _json_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _json_ready(value) for key, value in payload.items()}


def _json_payload_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _json_ready(value) for key, value in payload.items()}


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return _json_payload_mapping(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("template-fit payload floats must be finite")
        return value
    return value


def _reject_overclaim_text(payload: Mapping[str, Any]) -> None:
    for path, text in _walk_string_values(payload):
        lower = text.lower()
        if any(part in lower for part in _FORBIDDEN_TEXT_PARTS):
            raise ValueError(f"forbidden claim language in template fit metadata at {path}")


def _walk_string_values(
    payload: Mapping[str, Any],
    prefix: str = "",
) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            values.extend(_walk_string_values(value, path))
        elif isinstance(value, (tuple, list)):
            for idx, item in enumerate(value):
                if isinstance(item, Mapping):
                    values.extend(_walk_string_values(item, f"{path}.{idx}"))
                elif isinstance(item, str):
                    values.append((f"{path}.{idx}", item))
        elif isinstance(value, str):
            values.append((path, value))
    return tuple(values)
