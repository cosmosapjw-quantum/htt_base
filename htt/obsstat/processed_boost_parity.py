"""Audit-only nuisance and historical parity checks for PMG-WU-011.

The production path remains ``fit_joint_cutsky_alm``.  This module constructs
an independent weighted Frisch--Waugh--Lovell (FWL) retained solution from the
frozen normal matrix and a separately accumulated weighted right-hand side.
It also compares the reviewed WU-010 direction-safe pullback with the older
fixed-axis ``ExactBoostOperator`` on their narrow common full-sky domain.

These are validation objects, not alternative production estimators.  They do
not admit observed data, estimate or subtract ``beta``, identify global tilt,
or make a Bianchi-family or polarization claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math

import numpy as np

from .boost_biposh_residual import (
    DIPOLE_B_DEG,
    DIPOLE_L_DEG,
    ExactBoostOperator,
)
from .lorentz_sky_pullback import pullback_thermodynamic_temperature_field
from .planck_pr3_operator import _real_harmonic_design_block
from .processed_boost_operator import ProcessedBoostOperator
from .processed_boost_response import (
    FIT_LMAX,
    RETAINED_LMIN,
    PositiveAbsoluteSkySpec,
    ProcessedBoostError,
    healpix_sky_directions,
    joint_to_scientific_real,
)


_FWL_SCHEMA = "HTT_WU011_WEIGHTED_FWL_PARITY_V1"
_HISTORICAL_SCHEMA = "HTT_WU011_HISTORICAL_FIXED_AXIS_PARITY_V1"
_NUISANCE_DIMENSION = sum(2 * ell + 1 for ell in range(0, RETAINED_LMIN))
_RETAINED_DIMENSION = sum(
    2 * ell + 1 for ell in range(RETAINED_LMIN, FIT_LMAX + 1)
)


class HistoricalParityDomainError(ProcessedBoostError):
    """Raised when the historical and generic boost operators do not overlap."""


def _finite_vector(values: object, *, size: int, label: str) -> np.ndarray:
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            f"{label} must be a finite real vector with shape ({size},)"
        ) from exc
    if raw.dtype.kind not in "iuf" or raw.dtype.kind == "b":
        raise ProcessedBoostError(
            f"{label} must be a finite real vector with shape ({size},)"
        )
    vector = np.asarray(raw, dtype=np.float64)
    if vector.shape != (size,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError(
            f"{label} must be a finite real vector with shape ({size},)"
        )
    return vector


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


def _weighted_rhs(pixel_map: object, operator: ProcessedBoostOperator) -> np.ndarray:
    values = _finite_vector(
        pixel_map,
        size=operator.mask.size,
        label="temperature map",
    )
    joint = operator.joint_operator
    weights = operator.mask
    rhs = np.zeros(joint.dimension, dtype=np.float64)
    chunk_size = min(values.size, 65_536)
    for start in range(0, values.size, chunk_size):
        stop = min(values.size, start + chunk_size)
        local_weights = weights[start:stop]
        support = local_weights > 0.0
        if not np.any(support):
            continue
        pixels = np.arange(start, stop, dtype=np.int64)[support]
        design = _real_harmonic_design_block(
            joint.nside,
            pixels,
            lmin=joint.lmin,
            lmax=joint.lmax,
        )
        rhs += design.T @ (
            local_weights[support] * values[start:stop][support]
        )
    rhs *= 4.0 * math.pi / values.size
    if not np.all(np.isfinite(rhs)):
        raise ProcessedBoostError("weighted FWL right-hand side became nonfinite")
    return rhs


def _rank_and_condition(
    matrix: np.ndarray,
    *,
    relative_threshold: float,
) -> tuple[tuple[float, ...], int, float]:
    singular = np.linalg.svd(matrix, compute_uv=False)
    if singular.ndim != 1 or singular.size == 0 or not np.all(np.isfinite(singular)):
        raise ProcessedBoostError("FWL singular-value calculation failed")
    largest = float(singular[0])
    threshold = relative_threshold * largest
    rank = int(np.count_nonzero(singular > threshold)) if largest > 0.0 else 0
    condition = (
        largest / float(singular[rank - 1])
        if rank > 0
        else math.inf
    )
    return tuple(float(value) for value in singular), rank, float(condition)


def _commonization_factors(operator: ProcessedBoostOperator) -> np.ndarray:
    source = operator.source_beam * operator.source_pixel_window
    target = operator.target_beam * operator.target_pixel_window
    factors = np.asarray(
        [
            target[operator.joint_operator.basis_order[index][0]]
            / source[operator.joint_operator.basis_order[index][0]]
            for index in operator.joint_operator.retained_indices
        ],
        dtype=np.float64,
    )
    return _sealed(
        factors,
        shape=(_RETAINED_DIMENSION,),
        label="post-fit commonization factors",
    )


@dataclass(frozen=True)
class WeightedFWLParity:
    """Independent retained FWL solution and exact full-solve parity data."""

    retained_joint_coefficients: np.ndarray
    retained_scientific_coefficients: np.ndarray
    profiled_rhs: np.ndarray
    nuisance_rank: int
    nuisance_singular_values: tuple[float, ...]
    schur_rank: int
    schur_singular_values: tuple[float, ...]
    schur_condition_number: float
    full_solve_max_abs_residual: float
    operator_id: str
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        retained_joint = _sealed(
            self.retained_joint_coefficients,
            shape=(_RETAINED_DIMENSION,),
            label="FWL retained joint coefficients",
        )
        retained_scientific = _sealed(
            self.retained_scientific_coefficients,
            shape=(_RETAINED_DIMENSION,),
            label="FWL retained scientific coefficients",
        )
        profiled_rhs = _sealed(
            self.profiled_rhs,
            shape=(_RETAINED_DIMENSION,),
            label="FWL profiled right-hand side",
        )
        if self.nuisance_rank != _NUISANCE_DIMENSION:
            raise ProcessedBoostError("FWL nuisance block is not full rank")
        if self.schur_rank != _RETAINED_DIMENSION:
            raise ProcessedBoostError("FWL retained Schur complement is not full rank")
        if not math.isfinite(self.schur_condition_number) or self.schur_condition_number < 1.0:
            raise ProcessedBoostError("FWL Schur condition number is invalid")
        residual = float(self.full_solve_max_abs_residual)
        if not math.isfinite(residual) or residual < 0.0:
            raise ProcessedBoostError("FWL/full-solve residual is invalid")
        if not isinstance(self.operator_id, str) or not self.operator_id:
            raise ProcessedBoostError("FWL operator identity is required")
        content_id = _canonical_hash(
            {
                "schema": _FWL_SCHEMA,
                "operator_id": self.operator_id,
                "nuisance_rank": self.nuisance_rank,
                "schur_rank": self.schur_rank,
                "schur_condition_number_hex": self.schur_condition_number.hex(),
                "full_solve_max_abs_residual_hex": residual.hex(),
                "nuisance_singular_values_hex": [
                    float(value).hex() for value in self.nuisance_singular_values
                ],
                "schur_singular_values_hex": [
                    float(value).hex() for value in self.schur_singular_values
                ],
            },
            retained_joint,
            retained_scientific,
            profiled_rhs,
        )
        object.__setattr__(self, "retained_joint_coefficients", retained_joint)
        object.__setattr__(self, "retained_scientific_coefficients", retained_scientific)
        object.__setattr__(self, "profiled_rhs", profiled_rhs)
        object.__setattr__(self, "full_solve_max_abs_residual", residual)
        object.__setattr__(self, "content_id", content_id)

    @property
    def profiled_rhs_norm(self) -> float:
        return float(np.linalg.norm(self.profiled_rhs))


def weighted_fwl_retained_solution(
    pixel_map: object,
    operator: ProcessedBoostOperator,
) -> WeightedFWLParity:
    """Solve the retained block through the audit-only weighted FWL identity."""

    if type(operator) is not ProcessedBoostOperator:
        raise ProcessedBoostError("operator must be an exact ProcessedBoostOperator")
    joint = operator.joint_operator
    retained = np.asarray(joint.retained_indices, dtype=np.int64)
    nuisance = np.asarray(
        [index for index in range(joint.dimension) if index not in set(retained)],
        dtype=np.int64,
    )
    if nuisance.size != _NUISANCE_DIMENSION or retained.size != _RETAINED_DIMENSION:
        raise ProcessedBoostError("FWL nuisance/retained registry drifted")

    normal = joint.normal_matrix
    rhs = _weighted_rhs(pixel_map, operator)
    n_nn = normal[np.ix_(nuisance, nuisance)]
    n_nr = normal[np.ix_(nuisance, retained)]
    n_rn = normal[np.ix_(retained, nuisance)]
    n_rr = normal[np.ix_(retained, retained)]
    rhs_n = rhs[nuisance]
    rhs_r = rhs[retained]

    nuisance_singular, nuisance_rank, _ = _rank_and_condition(
        n_nn,
        relative_threshold=joint.relative_threshold,
    )
    if nuisance_rank != _NUISANCE_DIMENSION:
        raise ProcessedBoostError("weighted nuisance normal block is rank deficient")
    try:
        inv_n_rhs = np.linalg.solve(n_nn, rhs_n)
        inv_n_nr = np.linalg.solve(n_nn, n_nr)
    except np.linalg.LinAlgError as exc:
        raise ProcessedBoostError("weighted nuisance solve became singular") from exc
    schur = n_rr - n_rn @ inv_n_nr
    profiled_rhs = rhs_r - n_rn @ inv_n_rhs
    schur_singular, schur_rank, schur_condition = _rank_and_condition(
        schur,
        relative_threshold=joint.relative_threshold,
    )
    if schur_rank != _RETAINED_DIMENSION:
        raise ProcessedBoostError("weighted retained Schur complement is rank deficient")
    try:
        retained_joint = np.linalg.solve(schur, profiled_rhs)
        full_solution = np.linalg.solve(normal, rhs)
    except np.linalg.LinAlgError as exc:
        raise ProcessedBoostError("weighted FWL or full solve became singular") from exc
    full_residual = float(np.max(np.abs(retained_joint - full_solution[retained])))

    commonized_joint = retained_joint * _commonization_factors(operator)
    retained_scientific = joint_to_scientific_real(
        commonized_joint,
        lmin=RETAINED_LMIN,
        lmax=FIT_LMAX,
    )
    return WeightedFWLParity(
        retained_joint_coefficients=retained_joint,
        retained_scientific_coefficients=retained_scientific,
        profiled_rhs=profiled_rhs,
        nuisance_rank=nuisance_rank,
        nuisance_singular_values=nuisance_singular,
        schur_rank=schur_rank,
        schur_singular_values=schur_singular,
        schur_condition_number=schur_condition,
        full_solve_max_abs_residual=full_residual,
        operator_id=operator.content_id,
    )


@dataclass(frozen=True)
class HistoricalFixedAxisParity:
    """Narrow full-sky overlap report for generic and historical operators."""

    relative_increment_residual: float
    sign_mutation_relative_residual: float
    generic_increment_norm: float
    legacy_increment_norm: float
    max_abs_increment_residual: float
    nside: int
    lmax: int
    beta: float
    source_sky_id: str
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        fields = (
            self.relative_increment_residual,
            self.sign_mutation_relative_residual,
            self.generic_increment_norm,
            self.legacy_increment_norm,
            self.max_abs_increment_residual,
        )
        if any(not math.isfinite(float(value)) or float(value) < 0.0 for value in fields):
            raise ProcessedBoostError("historical parity diagnostics are invalid")
        if not isinstance(self.source_sky_id, str) or not self.source_sky_id:
            raise ProcessedBoostError("historical parity source identity is required")
        content_id = _canonical_hash(
            {
                "schema": _HISTORICAL_SCHEMA,
                "nside": self.nside,
                "lmax": self.lmax,
                "beta_hex": float(self.beta).hex(),
                "source_sky_id": self.source_sky_id,
                "relative_increment_residual_hex": float(
                    self.relative_increment_residual
                ).hex(),
                "sign_mutation_relative_residual_hex": float(
                    self.sign_mutation_relative_residual
                ).hex(),
                "generic_increment_norm_hex": float(self.generic_increment_norm).hex(),
                "legacy_increment_norm_hex": float(self.legacy_increment_norm).hex(),
                "max_abs_increment_residual_hex": float(
                    self.max_abs_increment_residual
                ).hex(),
            }
        )
        object.__setattr__(self, "content_id", content_id)


def historical_fixed_axis_parity(
    source_sky: PositiveAbsoluteSkySpec,
    *,
    nside: int,
    lmax: int,
    beta: float,
) -> HistoricalFixedAxisParity:
    """Compare finite boost increments on the fixed solar-dipole axis.

    The comparison subtracts each implementation's own zero-boost replay, so
    the result probes the finite boost increment rather than pretending that
    the historical map2alm/alm synthesis baseline is exact.
    """

    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise HistoricalParityDomainError(
            "historical parity requires an exact PositiveAbsoluteSkySpec"
        )
    hp = __import__("healpy")
    if type(nside) is not int or not hp.isnsideok(nside, nest=False):
        raise HistoricalParityDomainError("historical parity requires a valid nside")
    if (
        type(lmax) is not int
        or lmax < source_sky.source_lmax
        or lmax > 3 * nside - 1
    ):
        raise HistoricalParityDomainError(
            "historical parity lmax must contain the source band and obey the HEALPix ceiling"
        )
    if isinstance(beta, bool):
        raise HistoricalParityDomainError("historical parity beta must be nonzero and subluminal")
    try:
        speed = float(beta)
    except (TypeError, ValueError) as exc:
        raise HistoricalParityDomainError(
            "historical parity beta must be nonzero and subluminal"
        ) from exc
    if not math.isfinite(speed) or speed == 0.0 or abs(speed) >= 1.0:
        raise HistoricalParityDomainError(
            "historical parity beta must be nonzero and subluminal"
        )

    directions = healpix_sky_directions(nside)
    intrinsic = source_sky.evaluate(directions)
    b_hat = np.asarray(
        hp.rotator.dir2vec(DIPOLE_L_DEG, DIPOLE_B_DEG, lonlat=True),
        dtype=np.float64,
    )
    b_hat /= np.linalg.norm(b_hat)
    velocity = speed * b_hat

    generic_plus = pullback_thermodynamic_temperature_field(
        directions,
        velocity,
        source_sky.evaluate,
    )
    generic_minus = pullback_thermodynamic_temperature_field(
        directions,
        -velocity,
        source_sky.evaluate,
    )
    generic_increment = generic_plus - intrinsic
    sign_mutation_increment = generic_minus - intrinsic

    legacy_plus = ExactBoostOperator(nside=nside, lmax=lmax, beta=speed)(intrinsic)
    legacy_zero = ExactBoostOperator(nside=nside, lmax=lmax, beta=0.0)(intrinsic)
    legacy_increment = legacy_plus - legacy_zero

    generic_norm = float(np.linalg.norm(generic_increment))
    legacy_norm = float(np.linalg.norm(legacy_increment))
    scale = max(generic_norm, np.finfo(float).tiny)
    residual = legacy_increment - generic_increment
    sign_residual = legacy_increment - sign_mutation_increment
    return HistoricalFixedAxisParity(
        relative_increment_residual=float(np.linalg.norm(residual) / scale),
        sign_mutation_relative_residual=float(np.linalg.norm(sign_residual) / scale),
        generic_increment_norm=generic_norm,
        legacy_increment_norm=legacy_norm,
        max_abs_increment_residual=float(np.max(np.abs(residual))),
        nside=nside,
        lmax=lmax,
        beta=speed,
        source_sky_id=source_sky.content_id,
    )


__all__ = [
    "HistoricalFixedAxisParity",
    "HistoricalParityDomainError",
    "WeightedFWLParity",
    "historical_fixed_axis_parity",
    "weighted_fwl_retained_solution",
]
