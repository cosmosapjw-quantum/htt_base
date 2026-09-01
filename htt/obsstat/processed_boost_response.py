"""Authority, basis, and positive-sky contracts for WU-011.

This bounded implementation slice freezes the reviewed WU-010 predecessor,
the actual repository processing order, typed fail-closed terminals, the
conversion between scientific and joint-fit real-harmonic layouts, and a
strictly positive absolute thermodynamic-temperature source sky.

The source sky uses a global analytic positivity certificate obtained from
the spherical-harmonic addition theorem and Cauchy--Schwarz.  It performs no
silent clipping, monopole offset, data access, processed response, or velocity
inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math

import numpy as np
from scipy.special import sph_harm_y

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
_POSITIVE_SKY_SCHEMA = "HTT_WU011_POSITIVE_ABSOLUTE_SKY_V1"
_DIRECTION_ATOL = 5.0e-13


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


def _unit_directions(values: object) -> np.ndarray:
    try:
        directions = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            "sky directions must be finite unit three-vectors"
        ) from exc
    if (
        directions.ndim < 1
        or directions.shape[-1] != 3
        or not np.all(np.isfinite(directions))
    ):
        raise ProcessedBoostError("sky directions must be finite unit three-vectors")
    norms = np.linalg.norm(directions, axis=-1)
    if not np.allclose(norms, 1.0, rtol=0.0, atol=_DIRECTION_ATOL):
        raise ProcessedBoostError(
            "sky directions must be unit normalized; no silent projection is allowed"
        )
    return directions


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


def _scientific_block_norm(block: np.ndarray, ell: int) -> float:
    if block.shape != (2 * ell + 1,):
        raise ProcessedBoostError("scientific harmonic block registry drifted")
    norm2 = float(block[0] * block[0])
    if ell:
        pairs = block[1:].reshape(ell, 2)
        norm2 += 2.0 * float(np.einsum("ij,ij->", pairs, pairs))
    return math.sqrt(max(0.0, norm2))


def _anisotropy_supremum_bound(coefficients: np.ndarray, lmax: int) -> float:
    """Return a global full-sphere bound from addition theorem + Cauchy--Schwarz."""

    cursor = 0
    bound = 0.0
    for ell in range(1, lmax + 1):
        width = 2 * ell + 1
        block = coefficients[cursor : cursor + width]
        bound += math.sqrt((2.0 * ell + 1.0) / (4.0 * math.pi)) * (
            _scientific_block_norm(block, ell)
        )
        cursor += width
    if cursor != coefficients.size:
        raise ProcessedBoostError("positive-sky harmonic registry drifted")
    return float(bound)


@dataclass(frozen=True)
class PositiveAbsoluteSkySpec:
    """A globally certified positive thermodynamic-temperature source sky.

    ``monopole_temperature`` is the physical constant temperature ``T0``, not
    an ``a_00`` coefficient.  ``scientific_coefficients`` stores only
    ``ell=1..source_lmax`` in the repository scientific real convention.

    For each multipole, the addition theorem and Cauchy--Schwarz give

    ``|T_ell(n)| <= sqrt((2 ell+1)/(4 pi)) ||a_ell||_R``.

    The constructor requires the sum of these bounds to be strictly smaller
    than ``T0``; hence positivity holds on the entire sphere, not merely on a
    selected pixel grid.
    """

    monopole_temperature: float
    scientific_coefficients: np.ndarray
    source_lmax: int
    units: str
    anisotropy_supremum_bound: float = field(init=False)
    certified_temperature_margin: float = field(init=False)
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        if isinstance(self.monopole_temperature, bool):
            raise ProcessedBoostError(
                "monopole temperature must be a finite strictly positive real"
            )
        try:
            monopole = float(self.monopole_temperature)
        except (TypeError, ValueError) as exc:
            raise ProcessedBoostError(
                "monopole temperature must be a finite strictly positive real"
            ) from exc
        if not math.isfinite(monopole) or monopole <= 0.0:
            raise ProcessedBoostError(
                "monopole temperature must be finite and strictly positive"
            )
        if type(self.source_lmax) is not int or self.source_lmax != SOURCE_LMAX:
            raise ProcessedBoostError(
                f"source_lmax must equal the frozen WU-011 value {SOURCE_LMAX}"
            )
        if not isinstance(self.units, str) or not self.units.strip():
            raise ProcessedBoostError("temperature units must be a nonempty string")

        dimension = sum(2 * ell + 1 for ell in range(1, self.source_lmax + 1))
        coefficients = _finite_real_vector(
            self.scientific_coefficients,
            dimension=dimension,
            label="scientific stored-real anisotropy",
        )
        bound = _anisotropy_supremum_bound(coefficients, self.source_lmax)
        margin = monopole - bound
        if not math.isfinite(margin) or margin <= 0.0:
            raise ProcessedBoostError(
                "absolute thermodynamic-temperature sky is not certified strictly positive"
            )

        sealed = np.frombuffer(coefficients.astype("<f8").tobytes(), dtype="<f8")
        identity = {
            "schema": _POSITIVE_SKY_SCHEMA,
            "monopole_temperature_hex": monopole.hex(),
            "source_lmax": self.source_lmax,
            "units": self.units,
            "coefficient_dtype": sealed.dtype.str,
            "coefficient_shape": list(sealed.shape),
        }
        digest = hashlib.sha256()
        digest.update(
            json.dumps(
                identity,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        )
        digest.update(b"\0")
        digest.update(memoryview(sealed).cast("B"))

        object.__setattr__(self, "monopole_temperature", monopole)
        object.__setattr__(self, "scientific_coefficients", sealed)
        object.__setattr__(self, "units", self.units.strip())
        object.__setattr__(self, "anisotropy_supremum_bound", bound)
        object.__setattr__(self, "certified_temperature_margin", margin)
        object.__setattr__(self, "content_id", "sha256:" + digest.hexdigest())

    def evaluate(self, direction: object) -> np.ndarray:
        """Evaluate the certified absolute sky on one or more unit directions."""

        directions = _unit_directions(direction)
        theta = np.arccos(np.clip(directions[..., 2], -1.0, 1.0))
        phi = np.mod(np.arctan2(directions[..., 1], directions[..., 0]), 2.0 * math.pi)
        values = np.full(theta.shape, self.monopole_temperature, dtype=np.float64)
        cursor = 0
        for ell in range(1, self.source_lmax + 1):
            values += (
                self.scientific_coefficients[cursor]
                * sph_harm_y(ell, 0, theta, phi).real
            )
            cursor += 1
            for m in range(1, ell + 1):
                coefficient = complex(
                    self.scientific_coefficients[cursor],
                    self.scientific_coefficients[cursor + 1],
                )
                values += 2.0 * np.real(
                    coefficient * sph_harm_y(ell, m, theta, phi)
                )
                cursor += 2
        if cursor != self.scientific_coefficients.size:
            raise ProcessedBoostError("positive-sky evaluation registry drifted")
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ProcessedBoostError(
                "certified positive sky produced nonpositive or nonfinite values"
            )
        return values


__all__ = [
    "FIT_LMAX",
    "JOINT_ESTIMATOR_ID",
    "PROCESSING_ORDER",
    "PositiveAbsoluteSkySpec",
    "ProcessedBoostError",
    "ProcessedBoostTerminal",
    "RETAINED_LMIN",
    "SOURCE_LMAX",
    "WU010_CLOSEOUT_HEAD",
    "joint_to_scientific_real",
    "scientific_to_joint_real",
]
