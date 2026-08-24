"""Typed, observation-neutral HSC/KiDS spin-2 operator closure for PR-310.

This module owns only observer-side feature construction and numerical
identifiability diagnostics.  Raw catalogue component pairs are never named
E/B; an explicit registered linear provider must transform them first.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np


MINIMUM_SINGULAR_VALUE_RATIO = 1.0e-6
MAXIMUM_COVARIANCE_CONDITION = 1.0e10
SURVEY_COMPONENT_CONTRACTS = {
    "HSC": {
        "release_id": "HSC_S19A_Y3",
        "product_component": "hsc_product",
        "mask_component": "hsc_mask",
        "randoms_component": "hsc_randoms",
        "psf_component": "hsc_psf",
        "n_z_component": "hsc_n_z",
        "calibration_component": "hsc_shear_calibration",
        "covariance_component": "hsc_covariance",
        "calibration_role": "multiplicative_shear_calibration",
    },
    "KiDS": {
        "release_id": "KIDS_1000_DR4_1",
        "product_component": "kids_product",
        "mask_component": "kids_mask",
        "randoms_component": "kids_randoms",
        "psf_component": "kids_psf",
        "n_z_component": "kids_n_z",
        "calibration_component": "kids_shear_response",
        "covariance_component": "kids_covariance",
        "calibration_role": "lensfit_shear_response",
    },
}


class HscKidsCurrentStackError(ValueError):
    """Raised when the PR-310 science contract fails closed."""


def _text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise HscKidsCurrentStackError(f"{label} must be non-empty canonical text")
    return value


def _finite_vector(value: object, *, label: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise HscKidsCurrentStackError(f"{label} must be a finite vector") from exc
    if array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)):
        raise HscKidsCurrentStackError(f"{label} must be a finite vector")
    return array


def _finite_matrix(value: object, *, label: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise HscKidsCurrentStackError(f"{label} must be a finite matrix") from exc
    if array.ndim != 2 or 0 in array.shape or not np.all(np.isfinite(array)):
        raise HscKidsCurrentStackError(f"{label} must be a finite matrix")
    return array


@dataclass(frozen=True)
class SurveyIdentity:
    survey_id: str
    release_id: str
    product_component: str
    mask_component: str
    randoms_component: str
    psf_component: str
    n_z_component: str
    calibration_component: str
    covariance_component: str
    calibration_role: str
    component_order: str
    tangent_basis: str
    spin_convention: str


def _validate_survey_identity(identity: SurveyIdentity) -> None:
    if not isinstance(identity, SurveyIdentity) or identity.survey_id not in {
        "HSC",
        "KiDS",
    }:
        raise HscKidsCurrentStackError("survey identity must be HSC or KiDS")
    expected = SURVEY_COMPONENT_CONTRACTS[identity.survey_id]
    for field, value in expected.items():
        if getattr(identity, field) != value:
            raise HscKidsCurrentStackError(
                f"{identity.survey_id} {field.removesuffix('_component')} identity drifted"
            )
    if identity.component_order != "GAMMA1_THEN_GAMMA2":
        raise HscKidsCurrentStackError("raw spin component order drifted")
    if identity.tangent_basis != "RIGHT_HANDED_NORTH_EAST_SKY":
        raise HscKidsCurrentStackError("right-handed tangent basis drifted")
    if identity.spin_convention != "PASSIVE_EXP_MINUS_2I_PSI":
        raise HscKidsCurrentStackError("spin-2 sign convention drifted")


def validate_survey_pair(hsc: SurveyIdentity, kids: SurveyIdentity) -> None:
    """Require distinct, role-complete HSC S19A/Y3 and KiDS DR4.1 inputs."""

    _validate_survey_identity(hsc)
    _validate_survey_identity(kids)
    if hsc.survey_id != "HSC" or kids.survey_id != "KiDS":
        raise HscKidsCurrentStackError("HSC and KiDS survey order drifted")
    hsc_values = set(hsc.__dict__.values())
    kids_values = set(kids.__dict__.values())
    shared = hsc_values & kids_values
    allowed = {
        "GAMMA1_THEN_GAMMA2",
        "RIGHT_HANDED_NORTH_EAST_SKY",
        "PASSIVE_EXP_MINUS_2I_PSI",
    }
    if shared - allowed:
        raise HscKidsCurrentStackError("HSC and KiDS product identities collapsed")


@dataclass(frozen=True)
class RawSpin2Field:
    identity: SurveyIdentity
    gamma1: np.ndarray
    gamma2: np.ndarray
    bin_index: np.ndarray
    weights: np.ndarray

    def __post_init__(self) -> None:
        _validate_survey_identity(self.identity)
        gamma1 = _finite_vector(self.gamma1, label="gamma1")
        gamma2 = _finite_vector(self.gamma2, label="gamma2")
        weights = _finite_vector(self.weights, label="weights")
        bins = np.asarray(self.bin_index)
        if (
            gamma1.shape != gamma2.shape
            or gamma1.shape != weights.shape
            or bins.shape != gamma1.shape
            or not np.issubdtype(bins.dtype, np.integer)
            or np.any(bins < 0)
            or np.any(weights <= 0.0)
        ):
            raise HscKidsCurrentStackError("raw spin-2 row arrays are inconsistent")
        object.__setattr__(self, "gamma1", gamma1.copy())
        object.__setattr__(self, "gamma2", gamma2.copy())
        object.__setattr__(self, "bin_index", bins.astype(int, copy=True))
        object.__setattr__(self, "weights", weights.copy())


@dataclass(frozen=True)
class LabelledEBField:
    identity: SurveyIdentity
    e_mode: np.ndarray
    b_mode: np.ndarray
    bin_index: np.ndarray
    weights: np.ndarray
    provider_id: str
    output_order: str = "E_THEN_B"


def rotate_raw_components(field: RawSpin2Field, angle_radians: float) -> RawSpin2Field:
    """Passively rotate a spin-2 component pair by ``exp(-2 i psi)``."""

    if not isinstance(field, RawSpin2Field) or not math.isfinite(angle_radians):
        raise HscKidsCurrentStackError("spin-2 rotation input is invalid")
    cosine = math.cos(2.0 * angle_radians)
    sine = math.sin(2.0 * angle_radians)
    return RawSpin2Field(
        identity=field.identity,
        gamma1=cosine * field.gamma1 + sine * field.gamma2,
        gamma2=cosine * field.gamma2 - sine * field.gamma1,
        bin_index=field.bin_index,
        weights=field.weights,
    )


def label_eb(
    field: RawSpin2Field,
    *,
    provider_matrix: object,
    provider_id: object,
    output_order: object,
) -> LabelledEBField:
    """Apply a declared nonlocal linear provider before emitting E/B labels."""

    if not isinstance(field, RawSpin2Field):
        raise HscKidsCurrentStackError("raw spin-2 provider input is required")
    if output_order != "E_THEN_B":
        raise HscKidsCurrentStackError("E/B output order drifted")
    provider = _text(provider_id, label="E/B provider identity")
    rows = field.gamma1.size
    matrix = _finite_matrix(provider_matrix, label="E/B provider matrix")
    if matrix.shape != (2 * rows, 2 * rows):
        raise HscKidsCurrentStackError("E/B provider matrix shape drifted")
    if np.allclose(matrix, np.eye(2 * rows), rtol=0.0, atol=1.0e-15):
        raise HscKidsCurrentStackError("raw spin pair cannot be relabelled as E/B")
    if np.linalg.matrix_rank(matrix) != 2 * rows:
        raise HscKidsCurrentStackError("E/B provider is rank deficient")
    output = matrix @ np.concatenate([field.gamma1, field.gamma2])
    return LabelledEBField(
        identity=field.identity,
        e_mode=output[:rows],
        b_mode=output[rows:],
        bin_index=field.bin_index.copy(),
        weights=field.weights.copy(),
        provider_id=provider,
    )


@dataclass(frozen=True)
class TomographyBin:
    survey_id: str
    bin_index: int
    bin_id: str
    z_min: float
    z_max: float
    n_z_id: str
    calibration_id: str
    response_id: str


@dataclass(frozen=True)
class TomographyResult:
    survey_id: str
    bins: tuple[TomographyBin, ...]
    feature_order: tuple[str, ...]
    true_features: np.ndarray


def execute_tomography(
    field: LabelledEBField,
    *,
    bins: Sequence[TomographyBin],
) -> TomographyResult:
    """Execute weighted E/B auto/cross-bin features in frozen pair order."""

    if not isinstance(field, LabelledEBField) or isinstance(bins, (str, bytes)):
        raise HscKidsCurrentStackError("labelled E/B tomography input is required")
    ordered = tuple(bins)
    if len(ordered) < 2 or tuple(row.bin_index for row in ordered) != tuple(
        range(len(ordered))
    ):
        raise HscKidsCurrentStackError("tomography bins must be complete and ordered")
    prefix = field.identity.survey_id.lower()
    for index, row in enumerate(ordered):
        if not isinstance(row, TomographyBin) or row.survey_id != field.identity.survey_id:
            raise HscKidsCurrentStackError("tomography survey identity drifted")
        if (
            not math.isfinite(row.z_min)
            or not math.isfinite(row.z_max)
            or not 0.0 <= row.z_min < row.z_max
            or (index and not math.isclose(ordered[index - 1].z_max, row.z_min))
        ):
            raise HscKidsCurrentStackError("tomography redshift bins must be contiguous")
        if not all(
            _text(value, label="tomography identity").lower().startswith(prefix)
            for value in (row.bin_id, row.n_z_id, row.calibration_id, row.response_id)
        ):
            raise HscKidsCurrentStackError("tomography identities must remain survey-specific")
        if not np.any(field.bin_index == row.bin_index):
            raise HscKidsCurrentStackError("tomography bin is metadata-only or empty")
    if set(np.unique(field.bin_index)) != set(range(len(ordered))):
        raise HscKidsCurrentStackError("row assignments are outside tomography bins")

    e_means: list[float] = []
    b_means: list[float] = []
    for row in ordered:
        selected = field.bin_index == row.bin_index
        e_means.append(float(np.average(field.e_mode[selected], weights=field.weights[selected])))
        b_means.append(float(np.average(field.b_mode[selected], weights=field.weights[selected])))
    names: list[str] = []
    values: list[float] = []
    for left in range(len(ordered)):
        for right in range(left, len(ordered)):
            stem = f"{field.identity.survey_id}:{ordered[left].bin_id}x{ordered[right].bin_id}"
            names.extend((f"{stem}:EE", f"{stem}:BB"))
            values.extend((e_means[left] * e_means[right], b_means[left] * b_means[right]))
    return TomographyResult(
        survey_id=field.identity.survey_id,
        bins=ordered,
        feature_order=tuple(names),
        true_features=np.asarray(values, dtype=float),
    )


@dataclass(frozen=True)
class PseudoClOperator:
    operator_id: str
    mask_id: str
    feature_order: tuple[str, ...]
    mixing_matrix: np.ndarray
    inverse_matrix: np.ndarray

    @classmethod
    def build(
        cls,
        *,
        operator_id: object,
        mask_id: object,
        feature_order: Sequence[str],
        mixing_matrix: object,
        inverse_matrix: object,
    ) -> "PseudoClOperator":
        order = tuple(_text(item, label="feature id") for item in feature_order)
        if not order or len(order) != len(set(order)):
            raise HscKidsCurrentStackError("pseudo-Cl feature order is invalid")
        matrix = _finite_matrix(mixing_matrix, label="mask-coupling matrix")
        inverse = _finite_matrix(inverse_matrix, label="mask-coupling inverse")
        size = len(order)
        if matrix.shape != (size, size) or inverse.shape != (size, size):
            raise HscKidsCurrentStackError("mask-coupling shape drifted")
        if np.allclose(matrix, np.eye(size), rtol=0.0, atol=1.0e-15):
            raise HscKidsCurrentStackError("pure-mode oracle requires a nontrivial mask")
        if not np.allclose(inverse @ matrix, np.eye(size), atol=1.0e-12, rtol=1.0e-12):
            raise HscKidsCurrentStackError("mask-coupling inverse is invalid")
        return cls(
            operator_id=_text(operator_id, label="operator id"),
            mask_id=_text(mask_id, label="mask id"),
            feature_order=order,
            mixing_matrix=matrix.copy(),
            inverse_matrix=inverse.copy(),
        )

    def apply(
        self,
        true_features: object,
        *,
        feature_order: Sequence[str] | None = None,
    ) -> np.ndarray:
        if feature_order is not None and tuple(feature_order) != self.feature_order:
            raise HscKidsCurrentStackError("pseudo-Cl feature order drifted")
        values = _finite_vector(true_features, label="true bandpowers")
        if values.shape != (len(self.feature_order),):
            raise HscKidsCurrentStackError("true bandpower order is incomplete")
        return self.inverse_matrix @ (self.mixing_matrix @ values)

    def pure_mode_oracle(self) -> dict[str, object]:
        e_indices = [index for index, name in enumerate(self.feature_order) if name.endswith(":EE")]
        b_indices = [index for index, name in enumerate(self.feature_order) if name.endswith(":BB")]
        if not e_indices or len(e_indices) != len(b_indices):
            raise HscKidsCurrentStackError("two-way E/B feature order is incomplete")
        pure_e = np.zeros(len(self.feature_order))
        pure_b = np.zeros(len(self.feature_order))
        pure_e[e_indices] = 1.0
        pure_b[b_indices] = 1.0
        recovered_e = self.apply(pure_e)
        recovered_b = self.apply(pure_b)
        e_to_b = float(np.max(np.abs(recovered_e[b_indices])))
        b_to_e = float(np.max(np.abs(recovered_b[e_indices])))
        tolerance = 1.0e-12
        if e_to_b > tolerance or b_to_e > tolerance:
            raise HscKidsCurrentStackError("two-way pure-mode leakage oracle failed")
        return {
            "pure_e_to_b_max_abs": e_to_b,
            "pure_b_to_e_max_abs": b_to_e,
            "status": "TWO_WAY_PURE_MODE_PASS",
        }


def _unit_vector(value: object, *, label: str) -> np.ndarray:
    vector = _finite_vector(value, label=label)
    norm = float(np.linalg.norm(vector))
    if vector.shape != (3,) or not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
        raise HscKidsCurrentStackError(f"{label} must be one unit three-vector")
    return vector


def parallel_transport_axis(*, start: object, end: object, tangent: object) -> np.ndarray:
    """Transport a tangent axis along the shortest non-antipodal great circle."""

    start_vector = _unit_vector(start, label="transport start")
    end_vector = _unit_vector(end, label="transport end")
    tangent_vector = _unit_vector(tangent, label="transport tangent")
    if abs(float(np.dot(start_vector, tangent_vector))) > 1.0e-12:
        raise HscKidsCurrentStackError("transport input is not tangent at start")
    cross = np.cross(start_vector, end_vector)
    sine = float(np.linalg.norm(cross))
    cosine = float(np.dot(start_vector, end_vector))
    if sine <= 1.0e-14:
        if cosine < 0.0:
            raise HscKidsCurrentStackError("antipodal transport path is ambiguous")
        return tangent_vector.copy()
    axis = cross / sine
    angle = math.atan2(sine, cosine)
    transported = (
        tangent_vector * math.cos(angle)
        + np.cross(axis, tangent_vector) * math.sin(angle)
        + axis * float(np.dot(axis, tangent_vector)) * (1.0 - math.cos(angle))
    )
    transported -= end_vector * float(np.dot(end_vector, transported))
    norm = float(np.linalg.norm(transported))
    if norm <= 0.0:
        raise HscKidsCurrentStackError("parallel transport collapsed")
    return transported / norm


def headless_axis_alignment(left: object, right: object) -> float:
    return abs(float(np.dot(_unit_vector(left, label="left axis"), _unit_vector(right, label="right axis"))))


def _valid_covariance(matrix: object, *, size: int) -> np.ndarray | None:
    try:
        covariance = _finite_matrix(matrix, label="covariance")
    except HscKidsCurrentStackError:
        return None
    if covariance.shape != (size, size):
        return None
    if not np.allclose(covariance, covariance.T, atol=1.0e-12, rtol=1.0e-12):
        return None
    try:
        np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError:
        return None
    condition = float(np.linalg.cond(covariance))
    return covariance if math.isfinite(condition) and condition <= MAXIMUM_COVARIANCE_CONDITION else None


def _svd_rank(matrix: np.ndarray, *, threshold_ratio: float) -> tuple[int, list[float]]:
    singular = np.linalg.svd(matrix, compute_uv=False)
    largest = float(singular[0]) if singular.size else 0.0
    threshold = largest * threshold_ratio
    rank = int(np.count_nonzero(singular > threshold)) if largest > 0.0 else 0
    return rank, [float(value) for value in singular]


def _whitened_incremental_rank(
    covariance: np.ndarray,
    nuisance_response: object,
    candidate_response: object,
) -> dict[str, object]:
    nuisance = _finite_matrix(nuisance_response, label="nuisance response")
    candidate = _finite_matrix(candidate_response, label="candidate response")
    rows = covariance.shape[0]
    if nuisance.shape[0] != rows or candidate.shape[0] != rows:
        raise HscKidsCurrentStackError("response feature order is inconsistent")
    lower = np.linalg.cholesky(covariance)

    def whiten_scale(matrix: np.ndarray) -> tuple[np.ndarray, bool]:
        whitened = np.linalg.solve(lower, matrix)
        norms = np.linalg.norm(whitened, axis=0)
        nonzero = bool(np.all(np.isfinite(norms)) and np.all(norms > np.finfo(float).tiny))
        return (whitened / norms if nonzero else whitened), nonzero

    nuisance_scaled, nuisance_nonzero = whiten_scale(nuisance)
    candidate_scaled, candidate_nonzero = whiten_scale(candidate)
    if not nuisance_nonzero or not candidate_nonzero:
        return {
            "status": "NON_IDENTIFIED_ABSTAIN",
            "nuisance_rank": 0,
            "joint_rank": 0,
            "incremental_rank": 0,
            "candidate_columns": int(candidate.shape[1]),
            "whitening": "cholesky_left",
            "column_scaling": "covariance_whitened_l2",
            "threshold_ratio": MINIMUM_SINGULAR_VALUE_RATIO,
        }
    nuisance_rank, nuisance_singular = _svd_rank(
        nuisance_scaled, threshold_ratio=MINIMUM_SINGULAR_VALUE_RATIO
    )
    joint_rank, joint_singular = _svd_rank(
        np.column_stack([nuisance_scaled, candidate_scaled]),
        threshold_ratio=MINIMUM_SINGULAR_VALUE_RATIO,
    )
    incremental = joint_rank - nuisance_rank
    expected = int(candidate.shape[1])
    return {
        "status": (
            "FULL_INCREMENTAL_RANK"
            if incremental == expected
            else "NON_IDENTIFIED_ABSTAIN"
        ),
        "nuisance_rank": nuisance_rank,
        "joint_rank": joint_rank,
        "incremental_rank": incremental,
        "candidate_columns": expected,
        "nuisance_singular_values": nuisance_singular,
        "joint_singular_values": joint_singular,
        "whitening": "cholesky_left",
        "column_scaling": "covariance_whitened_l2",
        "threshold_ratio": MINIMUM_SINGULAR_VALUE_RATIO,
    }


def analyze_joint_response(
    *,
    hsc_features: object,
    kids_features: object,
    hsc_feature_order: Sequence[str],
    kids_feature_order: Sequence[str],
    hsc_covariance: object,
    kids_covariance: object,
    cross_covariance: object | None,
    nuisance_response: object,
    candidate_response: object,
    observed: bool,
) -> dict[str, object]:
    """Validate full covariance and report scale-stable incremental rank."""

    if type(observed) is not bool:
        raise HscKidsCurrentStackError("observed state must be one boolean")
    hsc = _finite_vector(hsc_features, label="HSC features")
    kids = _finite_vector(kids_features, label="KiDS features")
    hsc_order = tuple(hsc_feature_order)
    kids_order = tuple(kids_feature_order)
    if (
        len(hsc_order) != hsc.size
        or len(kids_order) != kids.size
        or len(set(hsc_order)) != len(hsc_order)
        or len(set(kids_order)) != len(kids_order)
        or not all(name.startswith("HSC:") for name in hsc_order)
        or not all(name.startswith("KiDS:") for name in kids_order)
    ):
        raise HscKidsCurrentStackError("joint feature order drifted")
    hsc_cov = _valid_covariance(hsc_covariance, size=hsc.size)
    kids_cov = _valid_covariance(kids_covariance, size=kids.size)
    try:
        cross = _finite_matrix(cross_covariance, label="cross covariance")
    except HscKidsCurrentStackError:
        cross = np.empty((0, 0))
    covariance_valid = (
        hsc_cov is not None
        and kids_cov is not None
        and cross.shape == (hsc.size, kids.size)
        and bool(np.any(np.abs(cross) > 1.0e-15))
    )
    joint_covariance: np.ndarray | None = None
    if covariance_valid:
        joint_covariance = np.block([[hsc_cov, cross], [cross.T, kids_cov]])
        joint_covariance = _valid_covariance(joint_covariance, size=hsc.size + kids.size)
        covariance_valid = joint_covariance is not None
    if not covariance_valid or joint_covariance is None:
        return {
            "capability": "HSC_KIDS_TYPED_SPIN2_TOMOGRAPHY_AND_JOINT_RANK_CLOSURE",
            "terminal_disposition": "JOINT_COVARIANCE_REQUIRED_ABSTAIN",
            "response_rank": None,
            "p_value": None,
            "forced_source_label": None,
            "observed_statistic_seen": False,
            "observed_science_executed": False,
        }
    rank = _whitened_incremental_rank(
        joint_covariance, nuisance_response, candidate_response
    )
    terminal = (
        "SYNTHETIC_OPERATOR_CLOSURE_PASS"
        if rank["status"] == "FULL_INCREMENTAL_RANK" and not observed
        else "OBSERVED_OPERATOR_DIAGNOSTIC_COMPLETE"
        if rank["status"] == "FULL_INCREMENTAL_RANK"
        else "NON_IDENTIFIED_ABSTAIN"
    )
    return {
        "capability": "HSC_KIDS_TYPED_SPIN2_TOMOGRAPHY_AND_JOINT_RANK_CLOSURE",
        "feature_order": [*hsc_order, *kids_order],
        "joint_covariance": {
            "status": "FULL_CROSS_SURVEY_COVARIANCE_VALID",
            "cross_block_nonzero": True,
            "condition_number": float(np.linalg.cond(joint_covariance)),
            "diagonalized": False,
        },
        "response_rank": rank,
        "terminal_disposition": terminal,
        "global_claim_boundary": "NO_VALID_GLOBAL_RESPONSE_NO_GLOBAL_CLAIM",
        "p_value": None,
        "forced_source_label": None,
        "observed_statistic_seen": bool(observed),
        "observed_science_executed": bool(observed),
    }
