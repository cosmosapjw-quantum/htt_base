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


def _canonical_text_tuple(
    values: Sequence[str], *, label: str, expected_size: int
) -> tuple[str, ...]:
    result = tuple(_text(value, label=f"{label} entry") for value in values)
    if len(result) != expected_size:
        raise HscKidsCurrentStackError(f"{label} length drifted")
    return result


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
    redshift: np.ndarray
    weights: np.ndarray
    sky_xy_radians: np.ndarray

    def __post_init__(self) -> None:
        _validate_survey_identity(self.identity)
        gamma1 = _finite_vector(self.gamma1, label="gamma1")
        gamma2 = _finite_vector(self.gamma2, label="gamma2")
        redshift = _finite_vector(self.redshift, label="redshift")
        weights = _finite_vector(self.weights, label="weights")
        sky = _finite_matrix(self.sky_xy_radians, label="flat-sky coordinates")
        bins = np.asarray(self.bin_index)
        if (
            gamma1.shape != gamma2.shape
            or gamma1.shape != redshift.shape
            or gamma1.shape != weights.shape
            or bins.shape != gamma1.shape
            or sky.shape != (gamma1.size, 2)
            or not np.issubdtype(bins.dtype, np.integer)
            or np.any(bins < 0)
            or np.any(redshift < 0.0)
            or np.any(weights <= 0.0)
        ):
            raise HscKidsCurrentStackError("raw spin-2 row arrays are inconsistent")
        object.__setattr__(self, "gamma1", gamma1.copy())
        object.__setattr__(self, "gamma2", gamma2.copy())
        object.__setattr__(self, "bin_index", bins.astype(int, copy=True))
        object.__setattr__(self, "redshift", redshift.copy())
        object.__setattr__(self, "weights", weights.copy())
        object.__setattr__(self, "sky_xy_radians", sky.copy())


@dataclass(frozen=True, init=False)
class LabelledEBField:
    identity: SurveyIdentity
    e_mode: np.ndarray
    b_mode: np.ndarray
    bin_index: np.ndarray
    redshift: np.ndarray
    weights: np.ndarray
    sky_xy_radians: np.ndarray
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
        redshift=field.redshift,
        weights=field.weights,
        sky_xy_radians=field.sky_xy_radians,
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
    orthogonal = np.allclose(
        matrix.T @ matrix, np.eye(2 * rows), atol=1.0e-12, rtol=1.0e-12
    )
    source_rows = np.arange(2 * rows) % rows
    support = [
        len(set(source_rows[np.flatnonzero(np.abs(line) > 1.0e-12)]))
        for line in matrix
    ]
    cross_components = all(
        np.any(np.abs(line[:rows]) > 1.0e-12)
        and np.any(np.abs(line[rows:]) > 1.0e-12)
        for line in matrix
    )
    if (
        np.linalg.matrix_rank(matrix) != 2 * rows
        or not orthogonal
        or (rows > 1 and min(support) < 2)
        or not cross_components
    ):
        raise HscKidsCurrentStackError(
            "E/B provider must be a normalized nonlocal spin-2 transform"
        )
    output = matrix @ np.concatenate([field.gamma1, field.gamma2])
    result = object.__new__(LabelledEBField)
    values = {
        "identity": field.identity,
        "e_mode": output[:rows],
        "b_mode": output[rows:],
        "bin_index": field.bin_index,
        "redshift": field.redshift,
        "weights": field.weights,
        "sky_xy_radians": field.sky_xy_radians,
        "provider_id": provider,
        "output_order": "E_THEN_B",
    }
    for name, value in values.items():
        object.__setattr__(result, name, value.copy() if isinstance(value, np.ndarray) else value)
    return result


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
    shear_calibration_factor: float
    response_factor: float


@dataclass(frozen=True)
class TomographyResult:
    survey_id: str
    bins: tuple[TomographyBin, ...]
    feature_order: tuple[str, ...]
    pseudo_features: np.ndarray
    flat_sky_wavevector: tuple[float, float]


def execute_tomography(
    field: LabelledEBField,
    *,
    bins: Sequence[TomographyBin],
    n_z_weights: object,
    mask_weights: object,
    flat_sky_wavevector: object,
) -> TomographyResult:
    """Execute masked flat-sky E/B pseudo-power in frozen pair order."""

    if not isinstance(field, LabelledEBField) or isinstance(bins, (str, bytes)):
        raise HscKidsCurrentStackError("labelled E/B tomography input is required")
    ordered = tuple(bins)
    nz = _finite_vector(n_z_weights, label="tomographic n(z) weights")
    mask = _finite_vector(mask_weights, label="tomographic mask weights")
    if nz.shape != field.weights.shape or mask.shape != field.weights.shape:
        raise HscKidsCurrentStackError("tomography row weights are incomplete")
    if np.any(nz <= 0.0) or np.any(mask <= 0.0):
        raise HscKidsCurrentStackError("tomography row weights must be positive")
    wavevector = _finite_vector(flat_sky_wavevector, label="flat-sky wavevector")
    if wavevector.shape != (2,) or float(np.linalg.norm(wavevector)) <= 0.0:
        raise HscKidsCurrentStackError("flat-sky wavevector must be nonzero and two-dimensional")
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
        expected_ids = (
            f"{field.identity.n_z_component}:{row.bin_id}",
            f"{field.identity.calibration_component}:{row.bin_id}",
            f"{field.identity.calibration_component}:"
            f"{field.identity.calibration_role}:{row.bin_id}",
        )
        if (
            not _text(row.bin_id, label="tomography bin id").lower().startswith(prefix)
            or (row.n_z_id, row.calibration_id, row.response_id) != expected_ids
        ):
            raise HscKidsCurrentStackError("tomography identities must remain survey-specific")
        selected = field.bin_index == row.bin_index
        upper_ok = field.redshift <= row.z_max if index == len(ordered) - 1 else field.redshift < row.z_max
        if (
            not np.any(selected)
            or not np.all((field.redshift[selected] >= row.z_min) & upper_ok[selected])
        ):
            raise HscKidsCurrentStackError("tomography bin is metadata-only or empty")
        if (
            not math.isfinite(row.shear_calibration_factor)
            or not math.isfinite(row.response_factor)
            or row.shear_calibration_factor <= 0.0
            or row.response_factor <= 0.0
        ):
            raise HscKidsCurrentStackError("tomography calibration/response is invalid")
    if set(np.unique(field.bin_index)) != set(range(len(ordered))):
        raise HscKidsCurrentStackError("row assignments are outside tomography bins")

    e_modes: list[complex] = []
    b_modes: list[complex] = []
    for row in ordered:
        selected = field.bin_index == row.bin_index
        effective = field.weights[selected] * nz[selected] * mask[selected]
        correction = row.shear_calibration_factor / row.response_factor
        phase = np.exp(-1j * (field.sky_xy_radians[selected] @ wavevector))
        normalization = float(np.sum(effective))
        e_modes.append(correction * np.sum(effective * field.e_mode[selected] * phase) / normalization)
        b_modes.append(correction * np.sum(effective * field.b_mode[selected] * phase) / normalization)
    names: list[str] = []
    values: list[float] = []
    wave_label = ",".join(f"{value:g}" for value in wavevector)
    for left in range(len(ordered)):
        for right in range(left, len(ordered)):
            stem = f"{field.identity.survey_id}:{ordered[left].bin_id}x{ordered[right].bin_id}:k={wave_label}"
            names.extend((f"{stem}:EE", f"{stem}:BB"))
            values.extend(
                (
                    float(np.real(e_modes[left] * np.conjugate(e_modes[right]))),
                    float(np.real(b_modes[left] * np.conjugate(b_modes[right]))),
                )
            )
    return TomographyResult(
        survey_id=field.identity.survey_id,
        bins=ordered,
        feature_order=tuple(names),
        pseudo_features=np.asarray(values, dtype=float),
        flat_sky_wavevector=(float(wavevector[0]), float(wavevector[1])),
    )


@dataclass(frozen=True)
class PseudoClOperator:
    operator_id: str
    mask_id: str
    feature_order: tuple[str, ...]
    mixing_matrix: np.ndarray
    inverse_matrix: np.ndarray
    pure_e_pseudo_response: np.ndarray
    pure_b_pseudo_response: np.ndarray

    @classmethod
    def build(
        cls,
        *,
        operator_id: object,
        mask_id: object,
        feature_order: Sequence[str],
        mixing_matrix: object,
        inverse_matrix: object,
        pure_e_pseudo_response: object,
        pure_b_pseudo_response: object,
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
        pure_e_response = _finite_vector(
            pure_e_pseudo_response, label="independent pure-E pseudo response"
        )
        pure_b_response = _finite_vector(
            pure_b_pseudo_response, label="independent pure-B pseudo response"
        )
        if pure_e_response.shape != (size,) or pure_b_response.shape != (size,):
            raise HscKidsCurrentStackError("pure-mode response shape drifted")
        return cls(
            operator_id=_text(operator_id, label="operator id"),
            mask_id=_text(mask_id, label="mask id"),
            feature_order=order,
            mixing_matrix=matrix.copy(),
            inverse_matrix=inverse.copy(),
            pure_e_pseudo_response=pure_e_response.copy(),
            pure_b_pseudo_response=pure_b_response.copy(),
        )

    def deconvolve(
        self,
        pseudo_features: object,
        *,
        feature_order: Sequence[str] | None = None,
    ) -> np.ndarray:
        if feature_order is not None and tuple(feature_order) != self.feature_order:
            raise HscKidsCurrentStackError("pseudo-Cl feature order drifted")
        values = _finite_vector(pseudo_features, label="pseudo bandpowers")
        if values.shape != (len(self.feature_order),):
            raise HscKidsCurrentStackError("pseudo bandpower order is incomplete")
        return self.inverse_matrix @ values

    def pure_mode_oracle(self) -> dict[str, object]:
        e_indices = [index for index, name in enumerate(self.feature_order) if name.endswith(":EE")]
        b_indices = [index for index, name in enumerate(self.feature_order) if name.endswith(":BB")]
        if not e_indices or len(e_indices) != len(b_indices):
            raise HscKidsCurrentStackError("two-way E/B feature order is incomplete")
        recovered_e = self.deconvolve(self.pure_e_pseudo_response)
        recovered_b = self.deconvolve(self.pure_b_pseudo_response)
        e_to_b = float(np.max(np.abs(recovered_e[b_indices])))
        b_to_e = float(np.max(np.abs(recovered_b[e_indices])))
        e_amplitude_error = float(np.max(np.abs(recovered_e[e_indices] - 1.0)))
        b_amplitude_error = float(np.max(np.abs(recovered_b[b_indices] - 1.0)))
        tolerance = 1.0e-12
        if (
            e_to_b > tolerance
            or b_to_e > tolerance
            or e_amplitude_error > tolerance
            or b_amplitude_error > tolerance
        ):
            raise HscKidsCurrentStackError("two-way pure-mode leakage oracle failed")
        return {
            "pure_e_to_b_max_abs": e_to_b,
            "pure_b_to_e_max_abs": b_to_e,
            "pure_e_amplitude_error": e_amplitude_error,
            "pure_b_amplitude_error": b_amplitude_error,
            "oracle_source": "independent_mask_injection_response",
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


def transported_headless_axis_alignment(
    *, start: object, end: object, left_tangent: object, right_tangent: object
) -> float:
    endpoint = _unit_vector(end, label="transport endpoint")
    right = _unit_vector(right_tangent, label="comparison tangent")
    if not math.isclose(float(np.dot(endpoint, right)), 0.0, abs_tol=1.0e-12):
        raise HscKidsCurrentStackError("comparison axis is not tangent at endpoint")
    transported = parallel_transport_axis(
        start=start, end=endpoint, tangent=left_tangent
    )
    return abs(float(np.dot(transported, right)))


@dataclass(frozen=True, init=False)
class PairedSameSkyJointCovariance:
    """Factory-only evidence derived from row-paired same-sky null features."""

    hsc_feature_order: tuple[str, ...]
    kids_feature_order: tuple[str, ...]
    hsc_feature_units: tuple[str, ...]
    kids_feature_units: tuple[str, ...]
    hsc_normalization_ids: tuple[str, ...]
    kids_normalization_ids: tuple[str, ...]
    realization_ids: tuple[str, ...]
    realization_source_identity: str
    sky_realization_role: str
    overlap_support_identity: str
    hsc_operator_identity: str
    kids_operator_identity: str
    centering_rule: str
    denominator_rule: str
    sample_count: int
    joint_covariance: np.ndarray
    hsc_covariance: np.ndarray
    kids_covariance: np.ndarray
    cross_covariance: np.ndarray
    covariance_rank: int
    psd_tolerance: float
    condition_number: float | None
    whitening_status: str


def derive_paired_same_sky_joint_covariance(
    *,
    hsc_null_features: object,
    kids_null_features: object,
    hsc_feature_order: Sequence[str],
    kids_feature_order: Sequence[str],
    hsc_feature_units: Sequence[str],
    kids_feature_units: Sequence[str],
    hsc_normalization_ids: Sequence[str],
    kids_normalization_ids: Sequence[str],
    hsc_realization_ids: Sequence[str],
    kids_realization_ids: Sequence[str],
    realization_source_identity: str,
    sky_realization_role: str,
    overlap_support_identity: str,
    hsc_operator_identity: str,
    kids_operator_identity: str,
    centering_rule: str = "JOINT_SAMPLE_MEAN",
    denominator_rule: str = "N_MINUS_ONE",
) -> PairedSameSkyJointCovariance:
    """Derive one full covariance from paired HSC/KiDS null rows.

    The pairing is scientific evidence: the two feature rows must be generated
    from the same cosmic realization on a declared common support.  An exact
    zero cross block is therefore an estimated result, not missing information.
    """

    hsc = _finite_matrix(hsc_null_features, label="HSC paired-null features")
    kids = _finite_matrix(kids_null_features, label="KiDS paired-null features")
    if hsc.shape[0] != kids.shape[0] or hsc.shape[0] < 2:
        raise HscKidsCurrentStackError(
            "paired same-sky nulls require at least two aligned rows"
        )
    hsc_order = _canonical_text_tuple(
        hsc_feature_order, label="HSC feature order", expected_size=hsc.shape[1]
    )
    kids_order = _canonical_text_tuple(
        kids_feature_order, label="KiDS feature order", expected_size=kids.shape[1]
    )
    if not all(name.startswith("HSC:") for name in hsc_order) or not all(
        name.startswith("KiDS:") for name in kids_order
    ):
        raise HscKidsCurrentStackError("paired covariance survey feature order drifted")
    hsc_units = _canonical_text_tuple(
        hsc_feature_units, label="HSC feature units", expected_size=hsc.shape[1]
    )
    kids_units = _canonical_text_tuple(
        kids_feature_units, label="KiDS feature units", expected_size=kids.shape[1]
    )
    hsc_norms = _canonical_text_tuple(
        hsc_normalization_ids,
        label="HSC normalization IDs",
        expected_size=hsc.shape[1],
    )
    kids_norms = _canonical_text_tuple(
        kids_normalization_ids,
        label="KiDS normalization IDs",
        expected_size=kids.shape[1],
    )
    if len(set((*hsc_norms, *kids_norms))) != hsc.shape[1] + kids.shape[1]:
        raise HscKidsCurrentStackError("paired covariance normalization IDs are not unique")

    hsc_ids = _canonical_text_tuple(
        hsc_realization_ids,
        label="HSC realization IDs",
        expected_size=hsc.shape[0],
    )
    kids_ids = _canonical_text_tuple(
        kids_realization_ids,
        label="KiDS realization IDs",
        expected_size=kids.shape[0],
    )
    if hsc_ids != kids_ids or len(set(hsc_ids)) != len(hsc_ids):
        raise HscKidsCurrentStackError(
            "paired same-sky realization IDs must be identical, ordered, and unique"
        )
    if sky_realization_role != "PAIRED_SAME_SKY_COSMIC_REALIZATION":
        raise HscKidsCurrentStackError("paired null sky-realization role drifted")
    if centering_rule != "JOINT_SAMPLE_MEAN" or denominator_rule != "N_MINUS_ONE":
        raise HscKidsCurrentStackError("paired sample-covariance estimator drifted")

    source_identity = _text(
        realization_source_identity, label="realization source identity"
    )
    overlap_identity = _text(
        overlap_support_identity, label="overlap support identity"
    )
    hsc_operator = _text(hsc_operator_identity, label="HSC operator identity")
    kids_operator = _text(kids_operator_identity, label="KiDS operator identity")

    joint = np.column_stack([hsc, kids])
    centered = joint - np.mean(joint, axis=0, keepdims=True)
    covariance = (centered.T @ centered) / float(joint.shape[0] - 1)
    covariance = 0.5 * (covariance + covariance.T)
    eigenvalues = np.linalg.eigvalsh(covariance)
    spectral_scale = max(
        float(np.max(np.abs(eigenvalues))), np.finfo(float).tiny
    )
    psd_tolerance = (
        64.0 * np.finfo(float).eps * covariance.shape[0] * spectral_scale
    )
    if float(eigenvalues[0]) < -psd_tolerance:
        raise HscKidsCurrentStackError("derived joint covariance is not positive semidefinite")
    covariance_rank = int(np.count_nonzero(eigenvalues > psd_tolerance))
    condition_number: float | None = None
    whitening_status = "COVARIANCE_VALID_WHITENING_UNAVAILABLE"
    if covariance_rank == covariance.shape[0]:
        condition = float(np.linalg.cond(covariance))
        try:
            np.linalg.cholesky(covariance)
        except np.linalg.LinAlgError:
            pass
        else:
            if math.isfinite(condition) and condition <= MAXIMUM_COVARIANCE_CONDITION:
                condition_number = condition
                whitening_status = "CHOLESKY_READY_WITHIN_CONDITION_LIMIT"

    hsc_size = hsc.shape[1]
    immutable_arrays: dict[str, np.ndarray] = {}
    for name, array in {
        "joint_covariance": covariance,
        "hsc_covariance": covariance[:hsc_size, :hsc_size],
        "kids_covariance": covariance[hsc_size:, hsc_size:],
        "cross_covariance": covariance[:hsc_size, hsc_size:],
    }.items():
        frozen = np.array(array, dtype=float, copy=True)
        frozen.setflags(write=False)
        immutable_arrays[name] = frozen
    values = {
        "hsc_feature_order": hsc_order,
        "kids_feature_order": kids_order,
        "hsc_feature_units": hsc_units,
        "kids_feature_units": kids_units,
        "hsc_normalization_ids": hsc_norms,
        "kids_normalization_ids": kids_norms,
        "realization_ids": hsc_ids,
        "realization_source_identity": source_identity,
        "sky_realization_role": sky_realization_role,
        "overlap_support_identity": overlap_identity,
        "hsc_operator_identity": hsc_operator,
        "kids_operator_identity": kids_operator,
        "centering_rule": centering_rule,
        "denominator_rule": denominator_rule,
        "sample_count": joint.shape[0],
        **immutable_arrays,
        "covariance_rank": covariance_rank,
        "psd_tolerance": psd_tolerance,
        "condition_number": condition_number,
        "whitening_status": whitening_status,
    }
    evidence = object.__new__(PairedSameSkyJointCovariance)
    for field_name, value in values.items():
        object.__setattr__(evidence, field_name, value)
    return evidence


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
            "LOCAL_STRUCTURAL_FULL_INCREMENTAL_RANK"
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
    joint_covariance_evidence: PairedSameSkyJointCovariance | None,
    nuisance_response: object,
    candidate_response: object,
    response_feature_order: Sequence[str],
    observed: bool,
) -> dict[str, object]:
    """Validate paired-null covariance and report local structural rank."""

    if type(observed) is not bool:
        raise HscKidsCurrentStackError("observed state must be one boolean")
    hsc = _finite_vector(hsc_features, label="HSC features")
    kids = _finite_vector(kids_features, label="KiDS features")
    hsc_order = tuple(hsc_feature_order)
    kids_order = tuple(kids_feature_order)
    joint_order = (*hsc_order, *kids_order)
    if (
        len(hsc_order) != hsc.size
        or len(kids_order) != kids.size
        or len(set(hsc_order)) != len(hsc_order)
        or len(set(kids_order)) != len(kids_order)
        or not all(name.startswith("HSC:") for name in hsc_order)
        or not all(name.startswith("KiDS:") for name in kids_order)
    ):
        raise HscKidsCurrentStackError("joint feature order drifted")
    if tuple(response_feature_order) != joint_order:
        raise HscKidsCurrentStackError("response feature order drifted")
    if joint_covariance_evidence is None:
        return {
            "capability": "HSC_KIDS_TYPED_SPIN2_TOMOGRAPHY_AND_JOINT_RANK_CLOSURE",
            "joint_covariance": {
                "status": "CROSS_INFORMATION_ABSENT_ABSTAIN",
                "cross_block_evidenced": False,
                "likelihood_ready": False,
            },
            "terminal_disposition": "NON_IDENTIFIED_CROSS_SURVEY_COVARIANCE",
            "response_rank": None,
            "p_value": None,
            "forced_source_label": None,
            "observed_statistic_seen": bool(observed),
            "observed_science_executed": bool(observed),
        }
    if not isinstance(joint_covariance_evidence, PairedSameSkyJointCovariance):
        raise HscKidsCurrentStackError(
            "joint covariance must come from the paired same-sky factory"
        )
    evidence = joint_covariance_evidence
    if evidence.hsc_feature_order != hsc_order or evidence.kids_feature_order != kids_order:
        raise HscKidsCurrentStackError("paired covariance feature order drifted")
    joint_covariance = evidence.joint_covariance
    if joint_covariance.shape != (hsc.size + kids.size, hsc.size + kids.size):
        raise HscKidsCurrentStackError("paired joint covariance shape drifted")
    covariance_report = {
        "status": "PAIRED_SAME_SKY_JOINT_COVARIANCE_VALID",
        "derivation": "CENTERED_PAIRED_ROW_SAMPLE_COVARIANCE",
        "centering_rule": evidence.centering_rule,
        "denominator_rule": evidence.denominator_rule,
        "sample_count": evidence.sample_count,
        "covariance_rank": evidence.covariance_rank,
        "dimension": int(joint_covariance.shape[0]),
        "psd_tolerance": evidence.psd_tolerance,
        "condition_number": evidence.condition_number,
        "whitening_status": evidence.whitening_status,
        "cross_block_evidenced": True,
        "cross_block_zero": bool(
            np.all(np.abs(evidence.cross_covariance) <= evidence.psd_tolerance)
        ),
        "diagonalized": False,
        "covariance_unit_rule": "OUTER_PRODUCT_OF_ORDERED_FEATURE_UNITS",
        "feature_units": [*evidence.hsc_feature_units, *evidence.kids_feature_units],
        "normalization_ids": [
            *evidence.hsc_normalization_ids,
            *evidence.kids_normalization_ids,
        ],
        "realization_source_identity": evidence.realization_source_identity,
        "sky_realization_role": evidence.sky_realization_role,
        "overlap_support_identity": evidence.overlap_support_identity,
        "operator_identities": {
            "HSC": evidence.hsc_operator_identity,
            "KiDS": evidence.kids_operator_identity,
        },
        "likelihood_ready": False,
        "finite_mock_precision_correction": None,
    }
    if evidence.whitening_status != "CHOLESKY_READY_WITHIN_CONDITION_LIMIT":
        return {
            "capability": "HSC_KIDS_TYPED_SPIN2_TOMOGRAPHY_AND_JOINT_RANK_CLOSURE",
            "feature_order": list(joint_order),
            "joint_covariance": covariance_report,
            "terminal_disposition": "COVARIANCE_VALID_WHITENING_UNAVAILABLE",
            "response_rank": None,
            "global_identification": "NOT_ESTABLISHED",
            "p_value": None,
            "forced_source_label": None,
            "observed_statistic_seen": bool(observed),
            "observed_science_executed": bool(observed),
        }
    rank = _whitened_incremental_rank(
        joint_covariance, nuisance_response, candidate_response
    )
    terminal = (
        "SYNTHETIC_OPERATOR_CLOSURE_PASS"
        if rank["status"] == "LOCAL_STRUCTURAL_FULL_INCREMENTAL_RANK" and not observed
        else "OBSERVED_OPERATOR_DIAGNOSTIC_COMPLETE"
        if rank["status"] == "LOCAL_STRUCTURAL_FULL_INCREMENTAL_RANK"
        else "NON_IDENTIFIED_ABSTAIN"
    )
    return {
        "capability": "HSC_KIDS_TYPED_SPIN2_TOMOGRAPHY_AND_JOINT_RANK_CLOSURE",
        "feature_order": list(joint_order),
        "joint_covariance": covariance_report,
        "response_rank": rank,
        "terminal_disposition": terminal,
        "global_identification": "NOT_ESTABLISHED",
        "global_claim_boundary": "NO_VALID_GLOBAL_RESPONSE_NO_GLOBAL_CLAIM",
        "p_value": None,
        "forced_source_label": None,
        "observed_statistic_seen": bool(observed),
        "observed_science_executed": bool(observed),
    }
