"""Authority and basis contracts for the WU-011 processed boost response.

This first GREEN slice deliberately contains no sky synthesis, processed
coefficient response, data access, or velocity estimator.  It freezes the
reviewed WU-010 predecessor, the actual repository processing order, typed
fail-closed terminals, and the conversion between two real-harmonic layouts:

* scientific stored-real: ``(a_l0, Re a_l1, Im a_l1, ...)``;
* joint-fit real basis: ``(a_l0, sqrt(2) Re a_l1, -sqrt(2) Im a_l1, ...)``.

The irrational basis conversion is numerically invertible to floating-point
roundoff, not byte-identical.  No silent truncation, padding, projection, or
nonfinite input is accepted.
"""

from __future__ import annotations

from enum import Enum
import math

import numpy as np

from .planck_pr3_operator import JOINT_CUTSKY_ESTIMATOR_ID


WU010_CLOSEOUT_HEAD = "29427a1f7f2c5d46e43ffe03053c4ac13e969228"
JOINT_ESTIMATOR_ID = JOINT_CUTSKY_ESTIMATOR_ID
SOURCE_LMAX = 6
FIT_LMAX = 5
RETAINED_LMIN = 2
PROCESSING_ORDER = (
    "FINITE_OR_LINEAR_BOOST",
    "SOURCE_BEAM_PIXEL_TRANSFER",
    "HEALPIX_SYNTHESIS",
    "WEIGHTED_JOINT_L0_L5_SOLVE",
    "POSTFIT_TARGET_SOURCE_COMMONIZATION",
    "RETAIN_L2_L5",
)


class ProcessedBoostError(ValueError):
    """Raised when a WU-011 processed-response contract is violated."""


class ProcessedBoostTerminal(str, Enum):
    """Typed terminal states for the complete WU-011 work unit."""

    PASS_SYNTHETIC_PROCESSED_RESPONSE = "PASS_SYNTHETIC_PROCESSED_RESPONSE"
    BLOCKED_BY_MOVED_AUTHORITY = "BLOCKED_BY_MOVED_AUTHORITY"
    BLOCKED_BY_BASIS_MISMATCH = "BLOCKED_BY_BASIS_MISMATCH"
    BLOCKED_BY_MISSING_ABSOLUTE_T = "BLOCKED_BY_MISSING_ABSOLUTE_T"
    BLOCKED_BY_OPERATOR_IDENTITY_MISMATCH = (
        "BLOCKED_BY_OPERATOR_IDENTITY_MISMATCH"
    )
    BLOCKED_BY_REPLAY_MISMATCH = "BLOCKED_BY_REPLAY_MISMATCH"
    BLOCKED_BY_LINEARIZATION_FAILURE = "BLOCKED_BY_LINEARIZATION_FAILURE"
    BLOCKED_BY_SIGN_MUTATION_SURVIVAL = "BLOCKED_BY_SIGN_MUTATION_SURVIVAL"
    BLOCKED_BY_RANK_DEFICIENCY = "BLOCKED_BY_RANK_DEFICIENCY"
    BLOCKED_BY_CONDITION_CEILING = "BLOCKED_BY_CONDITION_CEILING"
    BLOCKED_BY_TRANSFER_UNRESOLVED = "BLOCKED_BY_TRANSFER_UNRESOLVED"
    BLOCKED_BY_NUISANCE_DEFINITION = "BLOCKED_BY_NUISANCE_DEFINITION"
    BLOCKED_BY_ALIAS_UNCONTROLLED = "BLOCKED_BY_ALIAS_UNCONTROLLED"
    BLOCKED_BY_HISTORICAL_PARITY_FAILURE = (
        "BLOCKED_BY_HISTORICAL_PARITY_FAILURE"
    )
    BLOCKED_BY_NULL_EXCHANGEABILITY_FAILURE = (
        "BLOCKED_BY_NULL_EXCHANGEABILITY_FAILURE"
    )
    NO_ADMISSIBLE_NEW_RESULT = "NO_ADMISSIBLE_NEW_RESULT"


def _validated_band(lmin: object, lmax: object) -> tuple[int, int, int]:
    if type(lmin) is not int or type(lmax) is not int or not 0 <= lmin <= lmax:
        raise ValueError("real-harmonic band must satisfy integer 0 <= lmin <= lmax")
    dimension = sum(2 * ell + 1 for ell in range(lmin, lmax + 1))
    return lmin, lmax, dimension


def _finite_real_vector(
    values: object,
    *,
    dimension: int,
    label: str,
) -> np.ndarray:
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            f"{label} carrier must be a finite real vector with shape ({dimension},)"
        ) from exc
    if raw.dtype.kind not in "iuf" or raw.dtype.kind == "b":
        raise ProcessedBoostError(
            f"{label} carrier must be a finite real vector with shape ({dimension},)"
        )
    vector = np.asarray(raw, dtype=np.float64)
    if vector.shape != (dimension,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError(
            f"{label} carrier must be finite with shape ({dimension},)"
        )
    return vector


def scientific_to_joint_real(
    values: object,
    *,
    lmin: int,
    lmax: int,
) -> np.ndarray:
    """Convert scientific stored-real coefficients to the joint-fit basis.

    For every ``m>0`` pair, the real component is multiplied by ``sqrt(2)``
    and the imaginary component by ``-sqrt(2)``.  The input is not mutated.
    """

    lmin, lmax, dimension = _validated_band(lmin, lmax)
    output = _finite_real_vector(
        values,
        dimension=dimension,
        label="scientific stored-real",
    ).copy()
    root_two = math.sqrt(2.0)
    cursor = 0
    for ell in range(lmin, lmax + 1):
        cursor += 1  # m=0
        for _m in range(1, ell + 1):
            output[cursor] *= root_two
            output[cursor + 1] *= -root_two
            cursor += 2
    if cursor != dimension:  # defensive registry invariant
        raise ProcessedBoostError("scientific stored-real basis registry drifted")
    return output


def joint_to_scientific_real(
    values: object,
    *,
    lmin: int,
    lmax: int,
) -> np.ndarray:
    """Convert the joint-fit real basis to scientific stored-real coefficients."""

    lmin, lmax, dimension = _validated_band(lmin, lmax)
    output = _finite_real_vector(
        values,
        dimension=dimension,
        label="joint-real",
    ).copy()
    root_two = math.sqrt(2.0)
    cursor = 0
    for ell in range(lmin, lmax + 1):
        cursor += 1  # m=0
        for _m in range(1, ell + 1):
            output[cursor] /= root_two
            output[cursor + 1] /= -root_two
            cursor += 2
    if cursor != dimension:  # defensive registry invariant
        raise ProcessedBoostError("joint-real basis registry drifted")
    return output


__all__ = [
    "FIT_LMAX",
    "JOINT_ESTIMATOR_ID",
    "PROCESSING_ORDER",
    "ProcessedBoostError",
    "ProcessedBoostTerminal",
    "RETAINED_LMIN",
    "SOURCE_LMAX",
    "WU010_CLOSEOUT_HEAD",
    "joint_to_scientific_real",
    "scientific_to_joint_real",
]
