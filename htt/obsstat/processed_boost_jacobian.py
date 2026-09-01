"""Processed source-coefficient Jacobian for PMG-WU-011.

This module materializes the first-order response of the retained scientific
``ell=2..5`` carrier to the physical monopole temperature and scientific
stored-real ``ell=1..6`` source coefficients.  The tensor order is
``(beta_axis, retained_output, source_mode)`` with shape ``(3, 32, 49)``.

The implementation deliberately reuses the reviewed processed linear path.  A
strictly positive reference monopole is added to every source-mode injection;
the independently processed monopole response is subtracted before dividing
by the injected coefficient.  This preserves the physical absolute-
thermodynamic-temperature domain without treating the signed generator as an
absolute temperature field.

In the continuum operator the physical monopole produces only a first-order
dipole, which is profiled by the simultaneous ``ell=0,1`` nuisance solve.  The
HEALPix ``map2alm`` replay used by the implemented linear path can nevertheless
leave a small retained numerical column.  Raw full-matrix rank and the
physically relevant non-monopole rank are therefore reported separately.  The
raw numerical column is never promoted to monopole identifiability.

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

from .processed_boost_linearization import evaluate_processed_linear_response
from .processed_boost_operator import ProcessedBoostOperator
from .processed_boost_response import (
    FIT_LMAX,
    RETAINED_LMIN,
    SOURCE_LMAX,
    PositiveAbsoluteSkySpec,
    ProcessedBoostError,
)


_JACOBIAN_SCHEMA = "HTT_WU011_PROCESSED_COEFFICIENT_JACOBIAN_V1"
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
    """Return ``T0`` followed by scientific stored-real ``ell=1..6`` modes."""

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


def _singular_diagnostics(
    matrix: np.ndarray,
    *,
    relative_threshold: float,
) -> tuple[tuple[float, ...], int, float]:
    singular = np.linalg.svd(matrix, compute_uv=False)
    if singular.ndim != 1 or singular.size == 0 or not np.all(np.isfinite(singular)):
        raise ProcessedBoostError("Jacobian singular-value calculation failed")
    largest = float(singular[0])
    if largest <= 0.0:
        return tuple(float(value) for value in singular), 0, math.inf
    threshold = relative_threshold * largest
    rank = int(np.count_nonzero(singular > threshold))
    if rank == 0:
        condition = math.inf
    else:
        condition = largest / float(singular[rank - 1])
    return tuple(float(value) for value in singular), rank, float(condition)


@dataclass(frozen=True)
class ProcessedBoostJacobian:
    """Content-bound processed coefficient response and diagnostics."""

    tensor: np.ndarray
    source_registry: tuple[ScientificMode, ...]
    output_registry: tuple[ScientificMode, ...]
    operator_id: str
    reference_monopole_temperature: float
    basis_amplitude: float
    units: str
    rank_relative_threshold: float = _DEFAULT_RANK_RELATIVE_THRESHOLD
    ell6_alias_block: np.ndarray = field(init=False)
    axis_singular_values: tuple[tuple[float, ...], ...] = field(init=False)
    axis_ranks: tuple[int, ...] = field(init=False)
    axis_condition_numbers: tuple[float, ...] = field(init=False)
    combined_singular_values: tuple[float, ...] = field(init=False)
    combined_rank: int = field(init=False)
    combined_condition_number: float = field(init=False)
    nonmonopole_singular_values: tuple[float, ...] = field(init=False)
    nonmonopole_rank: int = field(init=False)
    nonmonopole_condition_number: float = field(init=False)
    monopole_retained_norm: float = field(init=False)
    monopole_relative_to_nonmonopole_max: float = field(init=False)
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        tensor = _sealed(
            self.tensor,
            shape=(_BETA_DIMENSION, _OUTPUT_DIMENSION, _SOURCE_DIMENSION),
            label="processed coefficient Jacobian",
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

        axis_singular: list[tuple[float, ...]] = []
        axis_ranks: list[int] = []
        axis_conditions: list[float] = []
        for axis in range(_BETA_DIMENSION):
            singular, rank, condition = _singular_diagnostics(
                tensor[axis],
                relative_threshold=threshold,
            )
            axis_singular.append(singular)
            axis_ranks.append(rank)
            axis_conditions.append(condition)

        combined = tensor.reshape(_BETA_DIMENSION * _OUTPUT_DIMENSION, _SOURCE_DIMENSION)
        combined_singular, combined_rank, combined_condition = _singular_diagnostics(
            combined,
            relative_threshold=threshold,
        )
        nonmonopole = tensor[:, :, 1:].reshape(
            _BETA_DIMENSION * _OUTPUT_DIMENSION, _SOURCE_DIMENSION - 1
        )
        nonmonopole_singular, nonmonopole_rank, nonmonopole_condition = (
            _singular_diagnostics(
                nonmonopole,
                relative_threshold=threshold,
            )
        )
        alias = _sealed(
            tensor[:, :, _ELL6_START:_ELL6_STOP],
            shape=(_BETA_DIMENSION, _OUTPUT_DIMENSION, 2 * SOURCE_LMAX + 1),
            label="ell=6 alias block",
        )
        monopole_norm = float(np.linalg.norm(tensor[:, :, 0]))
        nonmonopole_column_norms = np.linalg.norm(tensor[:, :, 1:], axis=(0, 1))
        nonmonopole_max = float(np.max(nonmonopole_column_norms))
        if not math.isfinite(nonmonopole_max) or nonmonopole_max <= 0.0:
            raise ProcessedBoostError("non-monopole Jacobian block has zero response")
        monopole_relative = monopole_norm / nonmonopole_max
        content_id = _canonical_hash(
            {
                "schema": _JACOBIAN_SCHEMA,
                "operator_id": self.operator_id,
                "source_registry": [
                    [mode.ell, mode.m, mode.component] for mode in expected_source
                ],
                "output_registry": [
                    [mode.ell, mode.m, mode.component] for mode in expected_output
                ],
                "reference_monopole_temperature_hex": reference.hex(),
                "basis_amplitude_hex": amplitude.hex(),
                "units": units,
                "rank_relative_threshold_hex": threshold.hex(),
                "raw_combined_rank": combined_rank,
                "nonmonopole_rank": nonmonopole_rank,
                "monopole_relative_to_nonmonopole_max_hex": monopole_relative.hex(),
            },
            tensor,
            alias,
        )

        object.__setattr__(self, "tensor", tensor)
        object.__setattr__(self, "source_registry", expected_source)
        object.__setattr__(self, "output_registry", expected_output)
        object.__setattr__(self, "reference_monopole_temperature", reference)
        object.__setattr__(self, "basis_amplitude", amplitude)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "rank_relative_threshold", threshold)
        object.__setattr__(self, "ell6_alias_block", alias)
        object.__setattr__(self, "axis_singular_values", tuple(axis_singular))
        object.__setattr__(self, "axis_ranks", tuple(axis_ranks))
        object.__setattr__(self, "axis_condition_numbers", tuple(axis_conditions))
        object.__setattr__(self, "combined_singular_values", combined_singular)
        object.__setattr__(self, "combined_rank", combined_rank)
        object.__setattr__(self, "combined_condition_number", combined_condition)
        object.__setattr__(self, "nonmonopole_singular_values", nonmonopole_singular)
        object.__setattr__(self, "nonmonopole_rank", nonmonopole_rank)
        object.__setattr__(self, "nonmonopole_condition_number", nonmonopole_condition)
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
    """Materialize the registered ``(3,32,49)`` processed response tensor."""

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

    tensor = np.empty(
        (_BETA_DIMENSION, _OUTPUT_DIMENSION, _SOURCE_DIMENSION), dtype=np.float64
    )
    for axis, beta in enumerate(np.eye(_BETA_DIMENSION, dtype=np.float64)):
        monopole_response = evaluate_processed_linear_response(
            monopole_sky,
            operator,
            beta,
        ).retained_coefficients
        tensor[axis, :, 0] = monopole_response / reference
        for source_index, injected_sky in enumerate(injected_skies, start=1):
            response = evaluate_processed_linear_response(
                injected_sky,
                operator,
                beta,
            ).retained_coefficients
            tensor[axis, :, source_index] = (
                response - monopole_response
            ) / amplitude

    if not np.all(np.isfinite(tensor)):
        raise ProcessedBoostError("processed coefficient Jacobian became nonfinite")
    return ProcessedBoostJacobian(
        tensor=tensor,
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


def predict_processed_linear_response(
    jacobian: ProcessedBoostJacobian,
    source_sky: PositiveAbsoluteSkySpec,
    beta: object,
) -> np.ndarray:
    """Contract the coefficient Jacobian with one source sky and velocity."""

    if type(jacobian) is not ProcessedBoostJacobian:
        raise ProcessedBoostError("jacobian must be an exact ProcessedBoostJacobian")
    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise ProcessedBoostError("source sky must be an exact PositiveAbsoluteSkySpec")
    if source_sky.units != jacobian.units:
        raise ProcessedBoostError("source and Jacobian temperature units differ")
    velocity = _finite_beta(beta)
    source = source_coordinate_vector(source_sky)
    predicted = np.einsum(
        "i,ioj,j->o",
        velocity,
        jacobian.tensor,
        source,
        optimize=True,
    )
    return _sealed(
        predicted,
        shape=(_OUTPUT_DIMENSION,),
        label="predicted processed linear response",
    )


__all__ = [
    "ProcessedBoostJacobian",
    "ScientificMode",
    "build_processed_boost_jacobian",
    "output_mode_registry",
    "predict_processed_linear_response",
    "source_coordinate_vector",
    "source_mode_registry",
]
