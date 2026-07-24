"""Diagnostic morphology-axis and alignment features for OBSSTAT.

OBSSTAT owns observable feature extraction only.  The records in this module
describe tensor-derived axes and antipodal alignments; they are not HTT
likelihood evidence, MIO certificates, transfer validation, native solver
results, or Bianchi family labels.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any

import numpy as np

from common.contracts import PreferredAxis
from common.sky_geometry import lb_to_unitvec, unitvec_to_lb

__all__ = [
    "DiagnosticMorphologyAxis",
    "MorphologyAxisSummary",
    "MorphologyNullCalibration",
    "summarize_morphology_axes",
]


_SCHEMA_VERSION = "obsstat.morphology.v1"
_FEATURE_CAVEAT = (
    "morphology-axis feature only; diagnostic descriptor, not model input, "
    "not MIO output, not morphology compatibility, and not a family label"
)
_ALLOWED_LOOK_ELSEWHERE = {
    "tracked",
    "look_elsewhere_tracked",
    "corrected",
    "look_elsewhere_corrected",
    "global_corrected",
}
_ALLOWED_GLOBAL_LOCAL_STATUS = {
    "global_corrected",
    "local_unadjusted_with_trials",
    "tracked_not_corrected",
}
_ALLOWED_PVALUE_KEYS = {
    "alignment_to_reference",
    "principal_axis_alignment",
    "plane_normal_alignment",
    "planarity",
    "axis_coherence",
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
)


@dataclass(frozen=True)
class MorphologyNullCalibration:
    """Null and look-elsewhere metadata for morphology feature p-values."""

    null_ensemble_ref: str
    look_elsewhere_status: str
    p_values: Mapping[str, float]
    mock_count: int
    covariance_status: str
    mask_status: str
    scan_volume: Mapping[str, Any]
    look_elsewhere_trials: int
    tail_definitions: Mapping[str, str] = field(default_factory=dict)
    caveats: tuple[str, ...] = (
        "morphology null metadata only; not HTT model output",
    )

    def __post_init__(self) -> None:
        if not str(self.null_ensemble_ref).strip():
            raise ValueError("MorphologyNullCalibration.null_ensemble_ref is required")
        status = str(self.look_elsewhere_status).strip().lower()
        if status not in _ALLOWED_LOOK_ELSEWHERE:
            raise ValueError(
                "MorphologyNullCalibration.look_elsewhere_status must document "
                "tracked or corrected look-elsewhere provenance"
            )
        p_values = {str(key): float(value) for key, value in self.p_values.items()}
        if not p_values:
            raise ValueError("MorphologyNullCalibration.p_values must be non-empty")
        for key, value in p_values.items():
            if key not in _ALLOWED_PVALUE_KEYS:
                raise ValueError(
                    "MorphologyNullCalibration.p_values keys must describe known "
                    f"morphology diagnostics; got {key!r}"
                )
            if not math.isfinite(value) or not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"MorphologyNullCalibration.p_values[{key!r}] must be in [0, 1]"
                )
        object.__setattr__(self, "p_values", p_values)
        tail_definitions = {
            str(key): str(value).strip()
            for key, value in self.tail_definitions.items()
        }
        missing_tail = [key for key in p_values if not tail_definitions.get(key)]
        if missing_tail:
            raise ValueError(
                "MorphologyNullCalibration.tail_definitions must cover every "
                f"p-value key: {missing_tail}"
            )
        object.__setattr__(self, "tail_definitions", tail_definitions)
        mock_count = int(self.mock_count)
        if mock_count < 100:
            raise ValueError("MorphologyNullCalibration.mock_count must be at least 100")
        object.__setattr__(self, "mock_count", mock_count)
        trials = int(self.look_elsewhere_trials)
        if trials <= 0:
            raise ValueError(
                "MorphologyNullCalibration.look_elsewhere_trials must be positive"
            )
        object.__setattr__(self, "look_elsewhere_trials", trials)
        if not str(self.covariance_status).strip():
            raise ValueError("MorphologyNullCalibration.covariance_status is required")
        if not str(self.mask_status).strip():
            raise ValueError("MorphologyNullCalibration.mask_status is required")
        scan_volume = _json_mapping(self.scan_volume)
        if not scan_volume:
            raise ValueError("MorphologyNullCalibration.scan_volume is required")
        _validate_scan_volume(scan_volume, p_values, trials)
        object.__setattr__(self, "scan_volume", scan_volume)
        object.__setattr__(
            self,
            "caveats",
            tuple(str(item) for item in self.caveats),
        )
        _reject_overclaim_text(
            {
                "null_ensemble_ref": self.null_ensemble_ref,
                "look_elsewhere_status": self.look_elsewhere_status,
                "tail_definitions": tail_definitions,
                "covariance_status": self.covariance_status,
                "mask_status": self.mask_status,
                "scan_volume": scan_volume,
                "caveats": self.caveats,
            }
        )

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-compatible null calibration metadata."""

        return {
            "null_ensemble_ref": self.null_ensemble_ref,
            "look_elsewhere_status": self.look_elsewhere_status,
            "p_values": dict(self.p_values),
            "tail_definitions": dict(self.tail_definitions),
            "mock_count": self.mock_count,
            "covariance_status": self.covariance_status,
            "mask_status": self.mask_status,
            "scan_volume": dict(self.scan_volume),
            "look_elsewhere_trials": self.look_elsewhere_trials,
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class DiagnosticMorphologyAxis:
    """Antipodal diagnostic axis extracted from an OBSSTAT morphology tensor."""

    vector: tuple[float, float, float]
    l_deg: float
    b_deg: float
    label: str
    axis_role: str
    axis_status: str
    provenance_hash: str
    production_allowed: bool = False
    axis_equivalence: str = "antipodal"
    source: str = "raw_diagnostic"
    weight_mode: str = "uniform_fallback"
    selection_mode: str = "none"
    eigenvalue: float | None = None
    eigenvalue_gap: float | None = None
    caveats: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        vector = _unit_vector(self.vector, "DiagnosticMorphologyAxis.vector")
        object.__setattr__(self, "vector", vector)
        l_deg = float(self.l_deg)
        b_deg = float(self.b_deg)
        if not math.isfinite(l_deg) or not (0.0 <= l_deg < 360.0):
            raise ValueError("DiagnosticMorphologyAxis.l_deg must be in [0, 360)")
        if not math.isfinite(b_deg) or not (-90.0 <= b_deg <= 90.0):
            raise ValueError("DiagnosticMorphologyAxis.b_deg must be in [-90, 90]")
        object.__setattr__(self, "l_deg", l_deg)
        object.__setattr__(self, "b_deg", b_deg)
        coordinate_vector = lb_to_unitvec(
            np.asarray(l_deg),
            np.asarray(b_deg),
        )
        if not math.isclose(
            abs(float(np.dot(np.asarray(vector), coordinate_vector))),
            1.0,
            rel_tol=1.0e-10,
            abs_tol=1.0e-12,
        ):
            raise ValueError(
                "DiagnosticMorphologyAxis vector must match its antipodal l_deg/b_deg"
            )
        if self.axis_role not in {
            "diagnostic_morphology_axis",
            "diagnostic_plane_normal_axis",
        }:
            raise ValueError("DiagnosticMorphologyAxis.axis_role is not allowed")
        if self.axis_status not in {"resolved", "degenerate", "rank_deficient"}:
            raise ValueError("DiagnosticMorphologyAxis.axis_status is not allowed")
        if self.axis_equivalence != "antipodal":
            raise ValueError("DiagnosticMorphologyAxis.axis_equivalence must be antipodal")
        if self.production_allowed:
            raise ValueError(
                "DiagnosticMorphologyAxis.production_allowed must remain False"
            )
        if self.source != "raw_diagnostic":
            raise ValueError("DiagnosticMorphologyAxis.source must be raw_diagnostic")
        if self.weight_mode != "uniform_fallback":
            raise ValueError(
                "DiagnosticMorphologyAxis.weight_mode must be uniform_fallback"
            )
        if self.selection_mode != "none":
            raise ValueError("DiagnosticMorphologyAxis.selection_mode must be none")
        if not str(self.label).strip():
            raise ValueError("DiagnosticMorphologyAxis.label is required")
        if not str(self.provenance_hash).strip():
            raise ValueError("DiagnosticMorphologyAxis.provenance_hash is required")
        object.__setattr__(
            self,
            "caveats",
            tuple(str(item) for item in self.caveats),
        )
        if self.axis_status != "resolved" and "degenerate" not in self.caveats:
            object.__setattr__(self, "caveats", (*self.caveats, "degenerate"))
        _reject_overclaim_text(
            {
                "label": self.label,
                "axis_role": self.axis_role,
                "axis_status": self.axis_status,
                "caveats": self.caveats,
            }
        )

    def to_preferred_axis(self) -> PreferredAxis:
        """Return a fail-closed COMMON axis adapter for gate-negative tests."""

        return PreferredAxis(
            l_deg=self.l_deg,
            b_deg=self.b_deg,
            label=self.label,
            source="raw_diagnostic",
            weight_mode="uniform_fallback",
            selection_mode="none",
            production_allowed=False,
            provenance_hash=self.provenance_hash,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-compatible diagnostic axis metadata."""

        payload = {
            "label": self.label,
            "axis_role": self.axis_role,
            "axis_status": self.axis_status,
            "axis_equivalence": self.axis_equivalence,
            "vector": list(self.vector),
            "l_deg": self.l_deg,
            "b_deg": self.b_deg,
            "source": self.source,
            "weight_mode": self.weight_mode,
            "selection_mode": self.selection_mode,
            "production_allowed": self.production_allowed,
            "provenance_hash": self.provenance_hash,
            "caveats": list(self.caveats),
        }
        if self.eigenvalue is not None:
            payload["eigenvalue"] = self.eigenvalue
        if self.eigenvalue_gap is not None:
            payload["eigenvalue_gap"] = self.eigenvalue_gap
        return payload


@dataclass(frozen=True)
class MorphologyAxisSummary:
    """Feature-only morphology-axis summary with explicit diagnostics."""

    principal_axis: DiagnosticMorphologyAxis
    plane_normal_axis: DiagnosticMorphologyAxis
    eigenvalues: tuple[float, float, float]
    eigenvalue_gaps: tuple[float, float]
    degeneracy_tolerance: float
    tensor_rank: int
    axis_identifiability_rank: int
    axis_identifiability_status: str
    effective_rank: float
    null_space_dimension: int
    condition_number: float | None
    condition_status: str
    planarity: Mapping[str, Any]
    alignment_features: Mapping[str, Mapping[str, Any]]
    definitions: Mapping[str, str]
    tensor_label: str = "morphology_tensor"
    statistic_role: str = "feature_only"
    model_role: str = "not_model_input"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    null_calibration: MorphologyNullCalibration | None = None
    config_hash: str = "sha256:config-not-supplied"
    input_hashes: tuple[str, ...] = field(default_factory=tuple)
    metadata_schema: str = _SCHEMA_VERSION
    caveats: tuple[str, ...] = (_FEATURE_CAVEAT,)

    def __post_init__(self) -> None:
        if self.claim_tier != "diagnostic_only":
            raise ValueError("MorphologyAxisSummary.claim_tier must be diagnostic_only")
        if self.model_role != "not_model_input":
            raise ValueError("MorphologyAxisSummary.model_role must be not_model_input")
        if self.transfer_source != "none":
            raise ValueError("MorphologyAxisSummary.transfer_source must be none")
        expected_role = (
            "null_calibrated_feature"
            if self.null_calibration is not None
            else "feature_only"
        )
        if self.statistic_role != expected_role:
            raise ValueError(
                "MorphologyAxisSummary.statistic_role must match null calibration "
                f"status: {expected_role}"
            )
        eigenvalues = tuple(float(value) for value in self.eigenvalues)
        if len(eigenvalues) != 3 or any(not math.isfinite(v) for v in eigenvalues):
            raise ValueError("MorphologyAxisSummary.eigenvalues must be three finite numbers")
        object.__setattr__(self, "eigenvalues", eigenvalues)
        gaps = tuple(float(value) for value in self.eigenvalue_gaps)
        if len(gaps) != 2 or any(not math.isfinite(v) or v < 0.0 for v in gaps):
            raise ValueError(
                "MorphologyAxisSummary.eigenvalue_gaps must be two non-negative numbers"
            )
        object.__setattr__(self, "eigenvalue_gaps", gaps)
        tol = float(self.degeneracy_tolerance)
        if not math.isfinite(tol) or tol < 0.0:
            raise ValueError(
                "MorphologyAxisSummary.degeneracy_tolerance must be non-negative"
            )
        object.__setattr__(self, "degeneracy_tolerance", tol)
        if int(self.tensor_rank) < 0 or int(self.tensor_rank) > 3:
            raise ValueError("MorphologyAxisSummary.tensor_rank must be in [0, 3]")
        object.__setattr__(self, "tensor_rank", int(self.tensor_rank))
        ident_rank = int(self.axis_identifiability_rank)
        if ident_rank < 0 or ident_rank > 2:
            raise ValueError(
                "MorphologyAxisSummary.axis_identifiability_rank must be in [0, 2]"
            )
        object.__setattr__(self, "axis_identifiability_rank", ident_rank)
        if self.axis_identifiability_status not in {
            "resolved",
            "partial",
            "degenerate",
        }:
            raise ValueError(
                "MorphologyAxisSummary.axis_identifiability_status is not allowed"
            )
        effective_rank = float(self.effective_rank)
        if not math.isfinite(effective_rank) or effective_rank < 0.0:
            raise ValueError("MorphologyAxisSummary.effective_rank must be non-negative")
        object.__setattr__(self, "effective_rank", effective_rank)
        null_dim = int(self.null_space_dimension)
        if null_dim < 0 or null_dim > 3:
            raise ValueError("MorphologyAxisSummary.null_space_dimension must be in [0, 3]")
        object.__setattr__(self, "null_space_dimension", null_dim)
        if self.condition_number is not None:
            condition = float(self.condition_number)
            if not math.isfinite(condition) or condition < 0.0:
                raise ValueError(
                    "MorphologyAxisSummary.condition_number must be non-negative"
                )
            object.__setattr__(self, "condition_number", condition)
        if self.condition_status not in {
            "finite",
            "singular_or_rank_deficient",
            "zero_tensor",
        }:
            raise ValueError("MorphologyAxisSummary.condition_status is not allowed")
        config_hash = str(self.config_hash).strip()
        if _is_placeholder_hash(config_hash):
            raise ValueError("MorphologyAxisSummary.config_hash must be explicit")
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "planarity", _json_mapping(self.planarity))
        object.__setattr__(
            self,
            "alignment_features",
            {
                str(key): _json_mapping(value)
                for key, value in self.alignment_features.items()
            },
        )
        object.__setattr__(
            self,
            "definitions",
            {str(key): str(value) for key, value in self.definitions.items()},
        )
        object.__setattr__(
            self,
            "input_hashes",
            _require_input_hashes(self.input_hashes),
        )
        object.__setattr__(
            self,
            "caveats",
            tuple(str(item) for item in self.caveats),
        )
        _reject_overclaim_text(
            {
                "tensor_label": self.tensor_label,
                "planarity": self.planarity,
                "alignment_features": self.alignment_features,
                "definitions": self.definitions,
                "caveats": self.caveats,
            }
        )

    def to_feature_payload(self) -> dict[str, Any]:
        """Return an OBSSTAT morphology feature block for ObservableVector."""

        payload: dict[str, Any] = {
            "metadata_schema": self.metadata_schema,
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": self.claim_tier,
            "production_status": "diagnostic_only",
            "statistic_role": self.statistic_role,
            "model_role": self.model_role,
            "transfer_source": self.transfer_source,
            "tensor_label": self.tensor_label,
            "axis_claim_status": "diagnostic_axis_not_production_axis",
            "principal_axis": self.principal_axis.to_payload(),
            "plane_normal_axis": self.plane_normal_axis.to_payload(),
            "axis_equivalence": "antipodal",
            "eigenvalues": list(self.eigenvalues),
            "eigenvalue_gaps": list(self.eigenvalue_gaps),
            "degeneracy_tolerance": self.degeneracy_tolerance,
            "tensor_rank": self.tensor_rank,
            "axis_identifiability_rank": self.axis_identifiability_rank,
            "axis_identifiability_status": self.axis_identifiability_status,
            "effective_rank": self.effective_rank,
            "tensor_null_space_dimension": self.null_space_dimension,
            "condition_number": self.condition_number,
            "condition_status": self.condition_status,
            "planarity": _json_payload_mapping(self.planarity),
            "alignment_features": {
                key: _json_payload_mapping(value)
                for key, value in self.alignment_features.items()
            },
            "definitions": dict(self.definitions),
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "claim_status": {
                "geometry_status": "blocked_pre_native_atlas",
                "family_status": "blocked_pre_native_atlas",
                "inference_status": "not_model_input",
                "mio_status": "not_mio_output",
                "production_axis_status": "not_production_axis",
            },
            "caveats": list(self.caveats),
        }
        if self.null_calibration is not None:
            payload["null_calibration"] = self.null_calibration.to_metadata()
        else:
            payload["null_calibration"] = {
                "status": "not_null_calibrated",
                "caveats": ["no morphology p-value or tail statistic supplied"],
            }
        return payload


def summarize_morphology_axes(
    *,
    morphology_tensor: Sequence[Sequence[float]],
    tensor_label: str = "morphology_tensor",
    reference_axes: Mapping[str, Sequence[float]] | None = None,
    null_calibration: MorphologyNullCalibration | None = None,
    degeneracy_tolerance: float = 1.0e-10,
    config_hash: str = "sha256:config-not-supplied",
    input_hashes: Sequence[str] = (),
    transfer_source: str = "none",
) -> MorphologyAxisSummary:
    """Extract diagnostic morphology axes and antipodal alignment features."""

    if transfer_source != "none":
        raise ValueError("summarize_morphology_axes transfer_source must be none")
    _reject_overclaim_text({"tensor_label": tensor_label})
    tensor = _prepare_tensor(morphology_tensor)
    values, vectors = np.linalg.eigh(tensor)
    order = np.argsort(values)[::-1]
    values_desc = values[order].astype(float)
    vectors_desc = vectors[:, order].T
    canonical_vectors = tuple(_canonical_antipodal(vec) for vec in vectors_desc)
    tolerance = _scaled_degeneracy_tolerance(values_desc, float(degeneracy_tolerance))
    gaps = (
        float(abs(values_desc[0] - values_desc[1])),
        float(abs(values_desc[1] - values_desc[2])),
    )
    principal_status = "resolved" if gaps[0] > tolerance else "degenerate"
    plane_status = "resolved" if gaps[1] > tolerance else "degenerate"
    rank = int(np.linalg.matrix_rank(tensor, tol=tolerance, hermitian=True))
    null_space_dimension = 3 - rank
    effective_rank = _effective_rank(values_desc)
    condition_metadata = _condition_metadata(values_desc, tolerance)
    axis_identifiability_rank = int(principal_status == "resolved") + int(
        plane_status == "resolved"
    )
    axis_identifiability_status = (
        "resolved"
        if axis_identifiability_rank == 2
        else "partial"
        if axis_identifiability_rank == 1
        else "degenerate"
    )
    provenance_seed = {
        "metadata_schema": _SCHEMA_VERSION,
        "tensor": tensor.tolist(),
        "tensor_label": tensor_label,
        "config_hash": config_hash,
        "input_hashes": list(input_hashes),
    }
    principal_axis = _axis_from_vector(
        canonical_vectors[0],
        label=f"{tensor_label}.principal_axis",
        axis_role="diagnostic_morphology_axis",
        axis_status=principal_status,
        eigenvalue=float(values_desc[0]),
        eigenvalue_gap=gaps[0],
        provenance_hash=_sha256_payload({**provenance_seed, "axis": "principal"}),
    )
    plane_normal_axis = _axis_from_vector(
        canonical_vectors[2],
        label=f"{tensor_label}.plane_normal_axis",
        axis_role="diagnostic_plane_normal_axis",
        axis_status=plane_status,
        eigenvalue=float(values_desc[2]),
        eigenvalue_gap=gaps[1],
        provenance_hash=_sha256_payload({**provenance_seed, "axis": "plane_normal"}),
    )
    alignments = _alignment_features(
        principal_axis.vector,
        reference_axes or {},
        axis_status=principal_status,
        eigenvalue_gap=gaps[0],
        degeneracy_tolerance=tolerance,
    )
    if null_calibration is not None:
        _require_null_keys_match_features(
            null_calibration,
            _available_pvalue_keys(reference_axes or {}),
        )
    definitions = {
        "tensor_definition": (
            "caller-supplied symmetric 3x3 morphology tensor; this module "
            "extracts descriptor axes but does not compute native morphology"
        ),
        "principal_axis": "eigenvector of largest eigenvalue, antipodal line",
        "plane_normal_axis": "eigenvector of smallest eigenvalue, antipodal line",
        "antipodal_angle_deg": "acos(abs(dot(axis, reference))) in degrees",
        "axiality_ratio": "(lambda_1 - lambda_2) / sum(abs(lambda_i))",
        "planarity_ratio": "(lambda_2 - lambda_3) / sum(abs(lambda_i))",
    }
    statistic_role = (
        "null_calibrated_feature"
        if null_calibration is not None
        else "feature_only"
    )
    return MorphologyAxisSummary(
        principal_axis=principal_axis,
        plane_normal_axis=plane_normal_axis,
        eigenvalues=tuple(float(value) for value in values_desc),
        eigenvalue_gaps=gaps,
        degeneracy_tolerance=tolerance,
        tensor_rank=rank,
        axis_identifiability_rank=axis_identifiability_rank,
        axis_identifiability_status=axis_identifiability_status,
        effective_rank=effective_rank,
        null_space_dimension=null_space_dimension,
        condition_number=condition_metadata["condition_number"],
        condition_status=condition_metadata["condition_status"],
        planarity={
            "axiality_ratio": _axiality_ratio(values_desc),
            "planarity_ratio": _planarity_ratio(values_desc),
            "input_tensor_trace": float(np.trace(tensor)),
            "status": "computed_from_morphology_tensor",
            "optimization_status": "not_axis_scan",
        },
        alignment_features=alignments,
        definitions=definitions,
        tensor_label=tensor_label,
        statistic_role=statistic_role,
        null_calibration=null_calibration,
        config_hash=str(config_hash),
        input_hashes=tuple(str(value) for value in input_hashes),
    )


def _prepare_tensor(value: Sequence[Sequence[float]]) -> np.ndarray:
    tensor = np.asarray(value, dtype=float)
    if tensor.shape != (3, 3):
        raise ValueError("morphology_tensor must be a 3x3 matrix")
    if not np.all(np.isfinite(tensor)):
        raise ValueError("morphology_tensor entries must be finite")
    if not np.allclose(tensor, tensor.T, rtol=1.0e-10, atol=1.0e-12):
        raise ValueError("morphology_tensor must be symmetric")
    return tensor


def _axis_from_vector(
    vector: tuple[float, float, float],
    *,
    label: str,
    axis_role: str,
    axis_status: str,
    eigenvalue: float,
    eigenvalue_gap: float,
    provenance_hash: str,
) -> DiagnosticMorphologyAxis:
    l_deg, b_deg = unitvec_to_lb(np.asarray(vector, dtype=float))
    return DiagnosticMorphologyAxis(
        vector=vector,
        l_deg=float(l_deg),
        b_deg=float(b_deg),
        label=label,
        axis_role=axis_role,
        axis_status=axis_status,
        eigenvalue=eigenvalue,
        eigenvalue_gap=eigenvalue_gap,
        provenance_hash=provenance_hash,
    )


def _alignment_features(
    axis: tuple[float, float, float],
    reference_axes: Mapping[str, Sequence[float]],
    *,
    axis_status: str,
    eigenvalue_gap: float,
    degeneracy_tolerance: float,
) -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {}
    axis_arr = np.asarray(axis, dtype=float)
    for label, reference in reference_axes.items():
        _reject_overclaim_text({"reference_axis_label": str(label)})
        ref_vec = np.asarray(_unit_vector(reference, f"reference_axes[{label!r}]"))
        if axis_status != "resolved":
            features[str(label)] = {
                "status": "axis_degenerate",
                "axis_equivalence": "antipodal",
                "antipodal_abs_dot": None,
                "antipodal_angle_deg": None,
                "eigenvalue_gap": float(eigenvalue_gap),
                "degeneracy_tolerance": float(degeneracy_tolerance),
                "definition": "acos(abs(dot(morphology_axis, reference_axis)))",
                "caveats": [
                    "alignment suppressed because the morphology axis is degenerate"
                ],
            }
            continue
        abs_dot = float(abs(np.clip(float(np.dot(axis_arr, ref_vec)), -1.0, 1.0)))
        angle_deg = float(math.degrees(math.acos(abs_dot)))
        features[str(label)] = {
            "axis_equivalence": "antipodal",
            "antipodal_abs_dot": abs_dot,
            "antipodal_angle_deg": angle_deg,
            "definition": "acos(abs(dot(morphology_axis, reference_axis)))",
        }
    return features


def _unit_vector(value: Sequence[float], label: str) -> tuple[float, float, float]:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (3,) or not np.all(np.isfinite(arr)):
        raise ValueError(f"{label} must be a finite 3-vector")
    norm = float(np.linalg.norm(arr))
    if norm <= 0.0:
        raise ValueError(f"{label} must have positive norm")
    return tuple(float(item) for item in arr / norm)


def _canonical_antipodal(value: Sequence[float]) -> tuple[float, float, float]:
    vec = np.asarray(_unit_vector(value, "eigenvector"), dtype=float)
    pivot = int(np.argmax(np.abs(vec)))
    if vec[pivot] < 0.0:
        vec = -vec
    return tuple(float(item) for item in vec)


def _effective_rank(values: np.ndarray) -> float:
    weights = np.abs(values.astype(float))
    total = float(weights.sum())
    if total <= 0.0:
        return 0.0
    p = weights / total
    entropy = -float(sum(float(x) * math.log(float(x)) for x in p if x > 0.0))
    return float(math.exp(entropy))


def _condition_metadata(values: np.ndarray, tolerance: float) -> dict[str, Any]:
    weights = np.sort(np.abs(values.astype(float)))
    if float(weights[-1]) <= tolerance:
        return {"condition_number": None, "condition_status": "zero_tensor"}
    if float(weights[0]) <= tolerance:
        return {
            "condition_number": None,
            "condition_status": "singular_or_rank_deficient",
        }
    return {"condition_number": float(weights[-1] / weights[0]), "condition_status": "finite"}


def _axiality_ratio(values: np.ndarray) -> float | None:
    denom = float(np.sum(np.abs(values)))
    if denom <= 0.0:
        return None
    return float((values[0] - values[1]) / denom)


def _planarity_ratio(values: np.ndarray) -> float | None:
    denom = float(np.sum(np.abs(values)))
    if denom <= 0.0:
        return None
    return float((values[1] - values[2]) / denom)


def _scaled_degeneracy_tolerance(values: np.ndarray, base_tolerance: float) -> float:
    if not math.isfinite(base_tolerance) or base_tolerance < 0.0:
        raise ValueError("degeneracy_tolerance must be finite and non-negative")
    scale = max(1.0, float(np.max(np.abs(values.astype(float)))))
    return float(base_tolerance * scale)


def _validate_scan_volume(
    scan_volume: Mapping[str, Any],
    p_values: Mapping[str, float],
    look_elsewhere_trials: int,
) -> None:
    required = {
        "targets",
        "statistic_keys",
        "look_elsewhere_trials",
        "global_local_status",
    }
    missing = sorted(field for field in required if field not in scan_volume)
    if missing:
        raise ValueError(
            "MorphologyNullCalibration.scan_volume missing required field(s): "
            + ", ".join(missing)
        )
    if int(scan_volume["look_elsewhere_trials"]) != int(look_elsewhere_trials):
        raise ValueError(
            "MorphologyNullCalibration.scan_volume look_elsewhere_trials mismatch"
        )
    status = str(scan_volume["global_local_status"]).strip().lower()
    if status not in _ALLOWED_GLOBAL_LOCAL_STATUS:
        raise ValueError(
            "MorphologyNullCalibration.scan_volume global_local_status is not allowed"
        )
    statistic_keys = _string_set(scan_volume["statistic_keys"])
    if set(p_values) != statistic_keys:
        raise ValueError(
            "MorphologyNullCalibration.scan_volume statistic_keys must match p_values"
        )
    if not _string_set(scan_volume["targets"]):
        raise ValueError("MorphologyNullCalibration.scan_volume targets is required")


def _require_null_keys_match_features(
    null_calibration: MorphologyNullCalibration,
    available_keys: set[str],
) -> None:
    missing = sorted(set(null_calibration.p_values) - available_keys)
    if missing:
        raise ValueError(
            "MorphologyNullCalibration p_values are not available for this "
            f"morphology summary: {missing}"
        )


def _available_pvalue_keys(reference_axes: Mapping[str, Sequence[float]]) -> set[str]:
    keys = {"planarity", "principal_axis_alignment", "plane_normal_alignment"}
    if reference_axes:
        keys.add("alignment_to_reference")
    return keys


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value} if value.strip() else set()
    try:
        return {str(item) for item in value if str(item).strip()}
    except TypeError as exc:
        raise ValueError("scan_volume entries must be string sequences") from exc


def _require_input_hashes(values: Sequence[str]) -> tuple[str, ...]:
    out = tuple(str(value).strip() for value in values)
    if not out or any(_is_placeholder_hash(value) for value in out):
        raise ValueError("MorphologyAxisSummary.input_hashes must be explicit")
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
            raise ValueError("morphology payload floats must be finite")
        return value
    return value


def _reject_overclaim_text(payload: Mapping[str, Any]) -> None:
    for path, text in _walk_string_values(payload):
        lower = text.lower()
        if any(part in lower for part in _FORBIDDEN_TEXT_PARTS):
            raise ValueError(f"morphology feature overclaim text at {path}")


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
