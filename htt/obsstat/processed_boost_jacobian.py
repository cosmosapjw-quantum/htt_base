"""Processed source-coefficient Jacobian for PMG-WU-011.

The scientific response maps the physical monopole temperature plus stored-real
``ell=1..6`` source coefficients to the retained stored-real ``ell=2..5``
carrier. Its tensor order is ``(beta_axis, retained_output, source_mode)`` and
its shape is ``(3, 32, 49)``.

The exact continuum monopole response is a pure dipole and is therefore a
structural null after the simultaneous ``ell=0,1`` nuisance fit. Numerical
HEALPix replay leakage is preserved separately from the scientific tensor.
Condition diagnostics use the Parseval metrics of the stored-real harmonic
coordinates; raw-coordinate singular values remain available only as numerical
diagnostics.

For source ``ell=6`` the first-order generator has physical ``ell=5`` and
raised ``ell=7`` channels. Their processed contributions are stored separately,
so the physical nearest-neighbour response is never labelled as aliasing.

No observed data, empirical velocity estimate, boost subtraction, global
matter-frame tilt, polarization response, foreground exclusion, or Bianchi-
family attribution is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math

import numpy as np

from .planck_pr3_operator import fit_joint_cutsky_alm
from .processed_boost_linearization import (
    evaluate_processed_linear_response,
    intrinsic_scalar_generator_map,
)
from .processed_boost_operator import ProcessedBoostOperator
from .processed_boost_response import (
    FIT_LMAX,
    RETAINED_LMIN,
    SOURCE_LMAX,
    PositiveAbsoluteSkySpec,
    ProcessedBoostError,
    joint_to_scientific_real,
)


_JACOBIAN_SCHEMA = "HTT_WU011_PROCESSED_COEFFICIENT_JACOBIAN_V2"
_SOURCE_DIMENSION = 1 + sum(2 * ell + 1 for ell in range(1, SOURCE_LMAX + 1))
_OUTPUT_DIMENSION = sum(
    2 * ell + 1 for ell in range(RETAINED_LMIN, FIT_LMAX + 1)
)
_BETA_DIMENSION = 3
_ELL6_START = 1 + sum(2 * ell + 1 for ell in range(1, SOURCE_LMAX))
_ELL6_STOP = _ELL6_START + 2 * SOURCE_LMAX + 1
_DEFAULT_REFERENCE_MONOPOLE = 1.0
_DEFAULT_BASIS_AMPLITUDE = 0.125
_DEFAULT_RANK_RELATIVE_THRESHOLD = 1.0e-10
_MAP2ALM_ITERATIONS = 3


@dataclass(frozen=True, order=True)
class ScientificMode:
    """One coordinate in the scientific stored-real harmonic convention."""

    ell: int
    m: int
    component: str

    def __post_init__(self) -> None:
        if type(self.ell) is not int or type(self.m) is not int:
            raise ProcessedBoostError("scientific mode indices must be integers")
        if self.ell < 0 or self.m < 0 or self.m > self.ell:
            raise ProcessedBoostError("scientific mode indices are outside their domain")
        if self.component not in {"REAL", "IMAG"}:
            raise ProcessedBoostError("scientific mode component must be REAL or IMAG")
        if self.m == 0 and self.component != "REAL":
            raise ProcessedBoostError("m=0 scientific modes have only a REAL component")

    @property
    def coordinate_role(self) -> str:
        if self.ell == 0 and self.m == 0:
            return "PHYSICAL_MONOPOLE_TEMPERATURE"
        return "HARMONIC_COEFFICIENT"

    @property
    def field_basis(self) -> str:
        if self.coordinate_role == "PHYSICAL_MONOPOLE_TEMPERATURE":
            return "CONSTANT_ONE"
        return "ORTHONORMAL_CONDON_SHORTLEY_STORED_REAL"

    @property
    def harmonic_adapter(self) -> str:
        if self.coordinate_role == "PHYSICAL_MONOPOLE_TEMPERATURE":
            return "a00=sqrt(4*pi)*T0"
        return "IDENTITY"


def _scientific_registry(lmin: int, lmax: int) -> tuple[ScientificMode, ...]:
    if type(lmin) is not int or type(lmax) is not int or not 0 <= lmin <= lmax:
        raise ProcessedBoostError("scientific registry requires 0 <= lmin <= lmax")
    rows: list[ScientificMode] = []
    for ell in range(lmin, lmax + 1):
        rows.append(ScientificMode(ell, 0, "REAL"))
        for m in range(1, ell + 1):
            rows.extend(
                (ScientificMode(ell, m, "REAL"), ScientificMode(ell, m, "IMAG"))
            )
    return tuple(rows)


def source_mode_registry() -> tuple[ScientificMode, ...]:
    """Return physical ``T0`` followed by stored-real ``ell=1..6`` modes."""

    return (ScientificMode(0, 0, "REAL"),) + _scientific_registry(1, SOURCE_LMAX)


def output_mode_registry() -> tuple[ScientificMode, ...]:
    """Return the retained scientific stored-real ``ell=2..5`` modes."""

    return _scientific_registry(RETAINED_LMIN, FIT_LMAX)


def _finite_positive_scalar(value: object, *, label: str) -> float:
    if isinstance(value, bool):
        raise ProcessedBoostError(f"{label} must be a finite strictly positive real")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            f"{label} must be a finite strictly positive real"
        ) from exc
    if not math.isfinite(result) or result <= 0.0:
        raise ProcessedBoostError(f"{label} must be a finite strictly positive real")
    return result


def _finite_beta(beta: object) -> np.ndarray:
    try:
        result = np.asarray(beta, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError("beta must be a finite real three-vector") from exc
    if result.shape != (3,) or not np.all(np.isfinite(result)):
        raise ProcessedBoostError("beta must be a finite real three-vector")
    return result


def _sealed(values: object, *, shape: tuple[int, ...], label: str) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(f"{label} has the wrong finite shape") from exc
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ProcessedBoostError(f"{label} has the wrong finite shape")
    return np.frombuffer(
        np.ascontiguousarray(array, dtype="<f8").tobytes(), dtype="<f8"
    ).reshape(shape)


def _canonical_hash(payload: dict[str, object], *arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    )
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(b"\0")
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(b"\0")
        digest.update(repr(value.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


def _nonzero_condition(singular: tuple[float, ...], rank: int) -> float:
    if rank <= 0:
        return math.inf
    return float(singular[0] / singular[rank - 1])


def _singular_diagnostics(
    matrix: np.ndarray,
    *,
    relative_threshold: float,
) -> tuple[tuple[float, ...], int, float]:
    singular_array = np.linalg.svd(matrix, compute_uv=False)
    if (
        singular_array.ndim != 1
        or singular_array.size == 0
        or not np.all(np.isfinite(singular_array))
    ):
        raise ProcessedBoostError("Jacobian singular-value calculation failed")
    singular = tuple(float(value) for value in singular_array)
    largest = singular[0]
    if largest <= 0.0:
        return singular, 0, math.inf
    threshold = relative_threshold * largest
    rank = int(np.count_nonzero(singular_array > threshold))
    if rank < min(matrix.shape):
        condition = math.inf
    else:
        condition = _nonzero_condition(singular, rank)
    return singular, rank, float(condition)


def _metric_diagonal(registry: tuple[ScientificMode, ...]) -> np.ndarray:
    diagonal = np.empty(len(registry), dtype=np.float64)
    for index, mode in enumerate(registry):
        if mode.coordinate_role == "PHYSICAL_MONOPOLE_TEMPERATURE":
            diagonal[index] = 4.0 * math.pi
        elif mode.m == 0:
            diagonal[index] = 1.0
        else:
            diagonal[index] = 2.0
    return _sealed(
        diagonal,
        shape=(len(registry),),
        label="scientific stored-real metric diagonal",
    )


def metric_whitened_matrix(
    matrix: object,
    *,
    source_metric_diagonal: object,
    output_metric_diagonal: object,
) -> np.ndarray:
    """Return the Parseval-metric-whitened representation of a linear map."""

    try:
        raw = np.asarray(matrix, dtype=np.float64)
        source_metric = np.asarray(source_metric_diagonal, dtype=np.float64)
        output_metric = np.asarray(output_metric_diagonal, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError("metric whitening inputs must be finite real arrays") from exc
    if raw.ndim != 2 or not np.all(np.isfinite(raw)):
        raise ProcessedBoostError("matrix for metric whitening must be finite and rank two")
    if (
        source_metric.shape != (raw.shape[1],)
        or output_metric.shape != (raw.shape[0],)
        or not np.all(np.isfinite(source_metric))
        or not np.all(np.isfinite(output_metric))
        or np.any(source_metric <= 0.0)
        or np.any(output_metric <= 0.0)
    ):
        raise ProcessedBoostError("metric diagonals must be finite, positive, and dimension matched")
    whitened = (
        np.sqrt(output_metric)[:, None]
        * raw
        / np.sqrt(source_metric)[None, :]
    )
    return _sealed(
        whitened,
        shape=raw.shape,
        label="metric-whitened Jacobian matrix",
    )


@dataclass(frozen=True)
class FullSkyMetricReference:
    """Exact irreducible full-sky reference for the registered bands."""

    sigma_squared_by_source_ell: tuple[float, ...]
    multiplicities: tuple[int, ...]
    anisotropy_rank: int
    structural_monopole_nullity: int
    nonzero_condition_number: float


def full_sky_metric_reference() -> FullSkyMetricReference:
    """Return the exact full-sky ``ell=1..6 -> ell=2..5`` spectrum."""

    sigma_squared = (
        8.0 / 3.0,
        27.0 / 5.0,
        13.0,
        21.0,
        125.0 / 11.0,
        216.0 / 13.0,
    )
    multiplicities = (3, 5, 7, 9, 11, 13)
    return FullSkyMetricReference(
        sigma_squared_by_source_ell=sigma_squared,
        multiplicities=multiplicities,
        anisotropy_rank=sum(multiplicities),
        structural_monopole_nullity=1,
        nonzero_condition_number=math.sqrt(63.0 / 8.0),
    )


def _healpy():
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - optional dependency gate
        raise ProcessedBoostError(
            "healpy is required for the WU-011 Jacobian decomposition"
        ) from exc
    return hp


def _evaluate_processed_linear_band(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
    beta: object,
    *,
    retained_intrinsic_ells: tuple[int, ...],
) -> np.ndarray:
    """Route selected intrinsic generator multipoles through the processed fit."""

    hp = _healpy()
    velocity = _finite_beta(beta)
    allowed = tuple(sorted(set(retained_intrinsic_ells)))
    if not allowed or any(
        type(ell) is not int or ell < 0 or ell > operator.processing_lmax
        for ell in allowed
    ):
        raise ProcessedBoostError("intrinsic generator band is outside the processing range")

    generator = intrinsic_scalar_generator_map(
        source_sky,
        velocity,
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
    )
    generator_alm = hp.map2alm(
        generator,
        lmax=operator.processing_lmax,
        iter=_MAP2ALM_ITERATIONS,
        pol=False,
    )
    selector = np.zeros(operator.processing_lmax + 1, dtype=np.float64)
    selector[list(allowed)] = 1.0
    selected_alm = hp.almxfl(generator_alm, selector, inplace=False)
    source_transfer = operator.source_beam * operator.source_pixel_window
    filtered_alm = hp.almxfl(selected_alm, source_transfer, inplace=False)
    pixel_map = hp.alm2map(
        filtered_alm,
        nside=operator.nside,
        lmax=operator.processing_lmax,
        pol=False,
    )
    fit = fit_joint_cutsky_alm(
        np.asarray(pixel_map, dtype=np.float64),
        mask=operator.mask,
        operator=operator.joint_operator,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
        target_beam=operator.target_beam,
        target_pixel_window=operator.target_pixel_window,
    )
    retained = joint_to_scientific_real(
        fit.retained_coefficients,
        lmin=RETAINED_LMIN,
        lmax=FIT_LMAX,
    )
    return _sealed(
        retained,
        shape=(_OUTPUT_DIMENSION,),
        label="band-selected processed linear response",
    )


@dataclass(frozen=True)
class ProcessedBoostJacobian:
    """Content-bound scientific response, replay diagnostics, and alias split."""

    tensor: np.ndarray
    ell6_expected_neighbor_l5_block: np.ndarray
    ell6_cutsky_alias_residual: np.ndarray
    source_registry: tuple[ScientificMode, ...]
    output_registry: tuple[ScientificMode, ...]
    operator_id: str
    reference_monopole_temperature: float
    basis_amplitude: float
    units: str
    rank_relative_threshold: float = _DEFAULT_RANK_RELATIVE_THRESHOLD
    raw_replay_tensor: np.ndarray = field(init=False)
    monopole_replay_leakage: np.ndarray = field(init=False)
    source_metric_diagonal: np.ndarray = field(init=False)
    output_metric_diagonal: np.ndarray = field(init=False)
    metric_whitened_stacked_matrix: np.ndarray = field(init=False)
    metric_whitened_singular_values: tuple[float, ...] = field(init=False)
    metric_whitened_rank: int = field(init=False)
    metric_whitened_condition_number: float = field(init=False)
    metric_whitened_nonzero_condition_number: float = field(init=False)
    ell6_source_response_block: np.ndarray = field(init=False)
    ell6_decomposition_residual: np.ndarray = field(init=False)
    axis_singular_values: tuple[tuple[float, ...], ...] = field(init=False)
    axis_ranks: tuple[int, ...] = field(init=False)
    axis_condition_numbers: tuple[float, ...] = field(init=False)
    combined_singular_values: tuple[float, ...] = field(init=False)
    combined_rank: int = field(init=False)
    combined_condition_number: float = field(init=False)
    nonmonopole_singular_values: tuple[float, ...] = field(init=False)
    nonmonopole_rank: int = field(init=False)
    nonmonopole_condition_number: float = field(init=False)
    raw_combined_singular_values: tuple[float, ...] = field(init=False)
    raw_combined_rank: int = field(init=False)
    raw_combined_condition_number: float = field(init=False)
    monopole_replay_leakage_norm: float = field(init=False)
    monopole_retained_norm: float = field(init=False)
    monopole_relative_to_nonmonopole_max: float = field(init=False)
    content_id: str = field(init=False)

    @property
    def ell6_alias_block(self) -> np.ndarray:
        """Deprecated compatibility alias for the raised-channel residual."""

        return self.ell6_cutsky_alias_residual

    def __post_init__(self) -> None:
        raw_tensor = _sealed(
            self.tensor,
            shape=(_BETA_DIMENSION, _OUTPUT_DIMENSION, _SOURCE_DIMENSION),
            label="raw replay coefficient Jacobian",
        )
        expected_source = source_mode_registry()
        expected_output = output_mode_registry()
        if tuple(self.source_registry) != expected_source:
            raise ProcessedBoostError("Jacobian source registry drifted")
        if tuple(self.output_registry) != expected_output:
            raise ProcessedBoostError("Jacobian output registry drifted")
        if not isinstance(self.operator_id, str) or not self.operator_id:
            raise ProcessedBoostError("processed operator identity is required")
        reference = _finite_positive_scalar(
            self.reference_monopole_temperature,
            label="reference monopole temperature",
        )
        amplitude = _finite_positive_scalar(
            self.basis_amplitude,
            label="basis amplitude",
        )
        units = self.units.strip() if isinstance(self.units, str) else ""
        if not units:
            raise ProcessedBoostError("Jacobian temperature units must be nonempty")
        threshold = float(self.rank_relative_threshold)
        if not math.isfinite(threshold) or not 0.0 < threshold < 1.0:
            raise ProcessedBoostError(
                "Jacobian rank relative threshold must lie strictly between zero and one"
            )

        scientific_array = np.asarray(raw_tensor, dtype=np.float64).copy()
        scientific_array[:, :, 0] = 0.0
        scientific_tensor = _sealed(
            scientific_array,
            shape=raw_tensor.shape,
            label="scientific coefficient Jacobian",
        )
        monopole_leakage = _sealed(
            raw_tensor[:, :, 0],
            shape=(_BETA_DIMENSION, _OUTPUT_DIMENSION),
            label="monopole replay leakage",
        )

        neighbor = _sealed(
            self.ell6_expected_neighbor_l5_block,
            shape=(_BETA_DIMENSION, _OUTPUT_DIMENSION, 2 * SOURCE_LMAX + 1),
            label="ell=6 expected neighbour block",
        )
        raised_alias = _sealed(
            self.ell6_cutsky_alias_residual,
            shape=(_BETA_DIMENSION, _OUTPUT_DIMENSION, 2 * SOURCE_LMAX + 1),
            label="ell=6 raised-channel alias residual",
        )
        ell6_source = _sealed(
            scientific_tensor[:, :, _ELL6_START:_ELL6_STOP],
            shape=(_BETA_DIMENSION, _OUTPUT_DIMENSION, 2 * SOURCE_LMAX + 1),
            label="ell=6 total source-response block",
        )
        decomposition = _sealed(
            ell6_source - (neighbor + raised_alias),
            shape=ell6_source.shape,
            label="ell=6 decomposition numerical residual",
        )

        source_metric = _metric_diagonal(expected_source)
        output_metric = _metric_diagonal(expected_output)
        stacked = scientific_tensor.reshape(
            _BETA_DIMENSION * _OUTPUT_DIMENSION, _SOURCE_DIMENSION
        )
        stacked_output_metric = np.tile(output_metric, _BETA_DIMENSION)
        whitened = metric_whitened_matrix(
            stacked,
            source_metric_diagonal=source_metric,
            output_metric_diagonal=stacked_output_metric,
        )
        metric_singular, metric_rank, metric_condition = _singular_diagnostics(
            whitened,
            relative_threshold=threshold,
        )
        metric_nonzero_condition = _nonzero_condition(metric_singular, metric_rank)

        axis_singular: list[tuple[float, ...]] = []
        axis_ranks: list[int] = []
        axis_conditions: list[float] = []
        for axis in range(_BETA_DIMENSION):
            singular, rank, condition = _singular_diagnostics(
                scientific_tensor[axis],
                relative_threshold=threshold,
            )
            axis_singular.append(singular)
            axis_ranks.append(rank)
            axis_conditions.append(condition)

        combined_singular, combined_rank, combined_condition = _singular_diagnostics(
            stacked,
            relative_threshold=threshold,
        )
        nonmonopole = scientific_tensor[:, :, 1:].reshape(
            _BETA_DIMENSION * _OUTPUT_DIMENSION, _SOURCE_DIMENSION - 1
        )
        nonmonopole_singular, nonmonopole_rank, nonmonopole_condition = (
            _singular_diagnostics(
                nonmonopole,
                relative_threshold=threshold,
            )
        )
        raw_combined = raw_tensor.reshape(
            _BETA_DIMENSION * _OUTPUT_DIMENSION, _SOURCE_DIMENSION
        )
        raw_singular, raw_rank, raw_condition = _singular_diagnostics(
            raw_combined,
            relative_threshold=threshold,
        )

        monopole_norm = float(np.linalg.norm(monopole_leakage))
        nonmonopole_column_norms = np.linalg.norm(
            scientific_tensor[:, :, 1:], axis=(0, 1)
        )
        nonmonopole_max = float(np.max(nonmonopole_column_norms))
        if not math.isfinite(nonmonopole_max) or nonmonopole_max <= 0.0:
            raise ProcessedBoostError("non-monopole Jacobian block has zero response")
        monopole_relative = monopole_norm / nonmonopole_max

        content_id = _canonical_hash(
            {
                "schema": _JACOBIAN_SCHEMA,
                "operator_id": self.operator_id,
                "source_registry": [
                    [
                        mode.ell,
                        mode.m,
                        mode.component,
                        mode.coordinate_role,
                        mode.field_basis,
                        mode.harmonic_adapter,
                    ]
                    for mode in expected_source
                ],
                "output_registry": [
                    [mode.ell, mode.m, mode.component] for mode in expected_output
                ],
                "reference_monopole_temperature_hex": reference.hex(),
                "basis_amplitude_hex": amplitude.hex(),
                "units": units,
                "rank_relative_threshold_hex": threshold.hex(),
                "scientific_combined_rank": combined_rank,
                "raw_combined_rank": raw_rank,
                "metric_whitened_rank": metric_rank,
                "monopole_relative_to_nonmonopole_max_hex": monopole_relative.hex(),
                "ell6_semantics": "PHYSICAL_L5_PLUS_RAISED_L7_ALIAS_PLUS_NUMERICAL_REMAINDER",
            },
            scientific_tensor,
            raw_tensor,
            monopole_leakage,
            source_metric,
            output_metric,
            whitened,
            ell6_source,
            neighbor,
            raised_alias,
            decomposition,
        )

        object.__setattr__(self, "tensor", scientific_tensor)
        object.__setattr__(self, "raw_replay_tensor", raw_tensor)
        object.__setattr__(self, "monopole_replay_leakage", monopole_leakage)
        object.__setattr__(self, "source_registry", expected_source)
        object.__setattr__(self, "output_registry", expected_output)
        object.__setattr__(self, "reference_monopole_temperature", reference)
        object.__setattr__(self, "basis_amplitude", amplitude)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "rank_relative_threshold", threshold)
        object.__setattr__(self, "source_metric_diagonal", source_metric)
        object.__setattr__(self, "output_metric_diagonal", output_metric)
        object.__setattr__(self, "metric_whitened_stacked_matrix", whitened)
        object.__setattr__(self, "metric_whitened_singular_values", metric_singular)
        object.__setattr__(self, "metric_whitened_rank", metric_rank)
        object.__setattr__(self, "metric_whitened_condition_number", metric_condition)
        object.__setattr__(
            self,
            "metric_whitened_nonzero_condition_number",
            metric_nonzero_condition,
        )
        object.__setattr__(self, "ell6_source_response_block", ell6_source)
        object.__setattr__(self, "ell6_expected_neighbor_l5_block", neighbor)
        object.__setattr__(self, "ell6_cutsky_alias_residual", raised_alias)
        object.__setattr__(self, "ell6_decomposition_residual", decomposition)
        object.__setattr__(self, "axis_singular_values", tuple(axis_singular))
        object.__setattr__(self, "axis_ranks", tuple(axis_ranks))
        object.__setattr__(self, "axis_condition_numbers", tuple(axis_conditions))
        object.__setattr__(self, "combined_singular_values", combined_singular)
        object.__setattr__(self, "combined_rank", combined_rank)
        object.__setattr__(self, "combined_condition_number", combined_condition)
        object.__setattr__(self, "nonmonopole_singular_values", nonmonopole_singular)
        object.__setattr__(self, "nonmonopole_rank", nonmonopole_rank)
        object.__setattr__(self, "nonmonopole_condition_number", nonmonopole_condition)
        object.__setattr__(self, "raw_combined_singular_values", raw_singular)
        object.__setattr__(self, "raw_combined_rank", raw_rank)
        object.__setattr__(self, "raw_combined_condition_number", raw_condition)
        object.__setattr__(self, "monopole_replay_leakage_norm", monopole_norm)
        object.__setattr__(self, "monopole_retained_norm", monopole_norm)
        object.__setattr__(
            self,
            "monopole_relative_to_nonmonopole_max",
            float(monopole_relative),
        )
        object.__setattr__(self, "content_id", content_id)


def build_processed_boost_jacobian(
    operator: ProcessedBoostOperator,
    *,
    reference_monopole_temperature: float = _DEFAULT_REFERENCE_MONOPOLE,
    basis_amplitude: float = _DEFAULT_BASIS_AMPLITUDE,
    units: str = "K_CMB",
    rank_relative_threshold: float = _DEFAULT_RANK_RELATIVE_THRESHOLD,
) -> ProcessedBoostJacobian:
    """Materialize the registered scientific and numerical response objects."""

    if type(operator) is not ProcessedBoostOperator:
        raise ProcessedBoostError("operator must be an exact ProcessedBoostOperator")
    if operator.processing_lmax < SOURCE_LMAX + 1:
        raise ProcessedBoostError(
            "Jacobian processing lmax must include the first-order raised source band"
        )
    reference = _finite_positive_scalar(
        reference_monopole_temperature,
        label="reference monopole temperature",
    )
    amplitude = _finite_positive_scalar(basis_amplitude, label="basis amplitude")
    canonical_units = units.strip() if isinstance(units, str) else ""
    if not canonical_units:
        raise ProcessedBoostError("Jacobian temperature units must be nonempty")

    zero_coefficients = np.zeros(_SOURCE_DIMENSION - 1, dtype=np.float64)
    monopole_sky = PositiveAbsoluteSkySpec(
        reference,
        zero_coefficients,
        SOURCE_LMAX,
        canonical_units,
    )
    injected_skies: list[PositiveAbsoluteSkySpec] = []
    for coordinate in range(_SOURCE_DIMENSION - 1):
        coefficients = zero_coefficients.copy()
        coefficients[coordinate] = amplitude
        injected_skies.append(
            PositiveAbsoluteSkySpec(
                reference,
                coefficients,
                SOURCE_LMAX,
                canonical_units,
            )
        )

    raw_tensor = np.empty(
        (_BETA_DIMENSION, _OUTPUT_DIMENSION, _SOURCE_DIMENSION), dtype=np.float64
    )
    ell6_neighbor = np.empty(
        (_BETA_DIMENSION, _OUTPUT_DIMENSION, 2 * SOURCE_LMAX + 1),
        dtype=np.float64,
    )
    ell6_raised_alias = np.empty_like(ell6_neighbor)

    ell6_injected = injected_skies[_ELL6_START - 1 : _ELL6_STOP - 1]
    if len(ell6_injected) != 2 * SOURCE_LMAX + 1:
        raise ProcessedBoostError("ell=6 source registry slice drifted")

    for axis, beta in enumerate(np.eye(_BETA_DIMENSION, dtype=np.float64)):
        monopole_response = evaluate_processed_linear_response(
            monopole_sky,
            operator,
            beta,
        ).retained_coefficients
        raw_tensor[axis, :, 0] = monopole_response / reference
        for source_index, injected_sky in enumerate(injected_skies, start=1):
            response = evaluate_processed_linear_response(
                injected_sky,
                operator,
                beta,
            ).retained_coefficients
            raw_tensor[axis, :, source_index] = (
                response - monopole_response
            ) / amplitude

        monopole_l5 = _evaluate_processed_linear_band(
            monopole_sky,
            operator,
            beta,
            retained_intrinsic_ells=(5,),
        )
        monopole_l7 = _evaluate_processed_linear_band(
            monopole_sky,
            operator,
            beta,
            retained_intrinsic_ells=(7,),
        )
        for local_index, injected_sky in enumerate(ell6_injected):
            neighbor = _evaluate_processed_linear_band(
                injected_sky,
                operator,
                beta,
                retained_intrinsic_ells=(5,),
            )
            raised = _evaluate_processed_linear_band(
                injected_sky,
                operator,
                beta,
                retained_intrinsic_ells=(7,),
            )
            ell6_neighbor[axis, :, local_index] = (
                neighbor - monopole_l5
            ) / amplitude
            ell6_raised_alias[axis, :, local_index] = (
                raised - monopole_l7
            ) / amplitude

    if (
        not np.all(np.isfinite(raw_tensor))
        or not np.all(np.isfinite(ell6_neighbor))
        or not np.all(np.isfinite(ell6_raised_alias))
    ):
        raise ProcessedBoostError("processed coefficient Jacobian became nonfinite")
    return ProcessedBoostJacobian(
        tensor=raw_tensor,
        ell6_expected_neighbor_l5_block=ell6_neighbor,
        ell6_cutsky_alias_residual=ell6_raised_alias,
        source_registry=source_mode_registry(),
        output_registry=output_mode_registry(),
        operator_id=operator.content_id,
        reference_monopole_temperature=reference,
        basis_amplitude=amplitude,
        units=canonical_units,
        rank_relative_threshold=rank_relative_threshold,
    )


def source_coordinate_vector(source_sky: PositiveAbsoluteSkySpec) -> np.ndarray:
    """Return ``(T0, a_1m, ..., a_6m)`` in the registered scientific layout."""

    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise ProcessedBoostError("source sky must be an exact PositiveAbsoluteSkySpec")
    if source_sky.source_lmax != SOURCE_LMAX:
        raise ProcessedBoostError("source sky does not cover the frozen ell=0..6 registry")
    values = np.concatenate(
        (
            np.array([source_sky.monopole_temperature], dtype=np.float64),
            np.asarray(source_sky.scientific_coefficients, dtype=np.float64),
        )
    )
    return _sealed(
        values,
        shape=(_SOURCE_DIMENSION,),
        label="scientific source-coordinate vector",
    )


def _predict_with_tensor(
    tensor: np.ndarray,
    source_sky: PositiveAbsoluteSkySpec,
    beta: object,
) -> np.ndarray:
    velocity = _finite_beta(beta)
    source = source_coordinate_vector(source_sky)
    predicted = np.einsum(
        "i,ioj,j->o",
        velocity,
        tensor,
        source,
        optimize=True,
    )
    return _sealed(
        predicted,
        shape=(_OUTPUT_DIMENSION,),
        label="predicted processed linear response",
    )


def predict_processed_linear_response(
    jacobian: ProcessedBoostJacobian,
    source_sky: PositiveAbsoluteSkySpec,
    beta: object,
) -> np.ndarray:
    """Predict the scientific response with the exact physical ``T0`` null."""

    if type(jacobian) is not ProcessedBoostJacobian:
        raise ProcessedBoostError("jacobian must be an exact ProcessedBoostJacobian")
    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise ProcessedBoostError("source sky must be an exact PositiveAbsoluteSkySpec")
    if source_sky.units != jacobian.units:
        raise ProcessedBoostError("source and Jacobian temperature units differ")
    return _predict_with_tensor(jacobian.tensor, source_sky, beta)


def predict_processed_replay_linear_response(
    jacobian: ProcessedBoostJacobian,
    source_sky: PositiveAbsoluteSkySpec,
    beta: object,
) -> np.ndarray:
    """Predict the current HEALPix replay, including disclosed monopole leakage."""

    if type(jacobian) is not ProcessedBoostJacobian:
        raise ProcessedBoostError("jacobian must be an exact ProcessedBoostJacobian")
    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise ProcessedBoostError("source sky must be an exact PositiveAbsoluteSkySpec")
    if source_sky.units != jacobian.units:
        raise ProcessedBoostError("source and Jacobian temperature units differ")
    return _predict_with_tensor(jacobian.raw_replay_tensor, source_sky, beta)


__all__ = [
    "FullSkyMetricReference",
    "ProcessedBoostJacobian",
    "ScientificMode",
    "build_processed_boost_jacobian",
    "full_sky_metric_reference",
    "metric_whitened_matrix",
    "output_mode_registry",
    "predict_processed_linear_response",
    "predict_processed_replay_linear_response",
    "source_coordinate_vector",
    "source_mode_registry",
]
