"""Authority, positive-sky, and source-transfer contracts for WU-011.

This bounded implementation slice freezes the reviewed WU-010 predecessor,
the actual repository processing order, typed fail-closed terminals, the
conversion between scientific and joint-fit real-harmonic layouts, a globally
certified positive thermodynamic-temperature source sky, and the first finite
HEALPix source-transfer path.

The source sky uses a global analytic positivity certificate obtained from
the spherical-harmonic addition theorem and Cauchy--Schwarz.  The finite map
path reuses the reviewed WU-010 direction-safe field pullback and keeps the
physical source transfer after the boost.  A separately identified
``TRANSFER_BEFORE_BOOST`` mutation exists only for adversarial testing.

No raw data, joint cut-sky result, empirical velocity estimate, global tilt,
or Bianchi-family inference is produced here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math

import numpy as np
from scipy.special import sph_harm_y

from .lorentz_sky_pullback import (
    lorentz_factor,
    pullback_thermodynamic_temperature_field,
)
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
_SOURCE_MAP_SCHEMA = "HTT_WU011_SOURCE_CONVOLVED_FINITE_MAP_V1"
_DIRECTION_ATOL = 5.0e-13
_MAP2ALM_ITERATIONS = 3
_ALLOWED_SOURCE_MUTATIONS = {None, "TRANSFER_BEFORE_BOOST"}


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


def _healpy():
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - optional dependency gate
        raise ProcessedBoostError(
            "healpy is required for the WU-011 HEALPix source-transfer path"
        ) from exc
    return hp


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


def _finite_beta(beta: object) -> np.ndarray:
    try:
        vector = np.asarray(beta, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError("beta must be a finite real three-vector") from exc
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError("beta must be a finite real three-vector")
    # Reuse the reviewed WU-010 domain gate rather than copying its gamma rule.
    lorentz_factor(vector)
    return vector


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
        canonical_units = self.units.strip() if isinstance(self.units, str) else ""
        if not canonical_units:
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
            "units": canonical_units,
        }
        content_id = _canonical_hash(identity, sealed)

        object.__setattr__(self, "monopole_temperature", monopole)
        object.__setattr__(self, "scientific_coefficients", sealed)
        object.__setattr__(self, "units", canonical_units)
        object.__setattr__(self, "anisotropy_supremum_bound", bound)
        object.__setattr__(self, "certified_temperature_margin", margin)
        object.__setattr__(self, "content_id", content_id)

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


def healpix_sky_directions(nside: object) -> np.ndarray:
    """Return immutable RING-ordered outward HEALPix sky directions."""

    hp = _healpy()
    if type(nside) is not int or not hp.isnsideok(nside):
        raise ProcessedBoostError("nside must be a valid positive HEALPix nside")
    pixels = np.arange(hp.nside2npix(nside), dtype=np.int64)
    x, y, z = hp.pix2vec(nside, pixels, nest=False)
    directions = np.column_stack((x, y, z)).astype("<f8", copy=False)
    if not np.allclose(
        np.linalg.norm(directions, axis=1), 1.0, rtol=0.0, atol=2.0e-15
    ):
        raise ProcessedBoostError("HEALPix direction registry is not unit normalized")
    return np.frombuffer(directions.tobytes(), dtype="<f8").reshape(-1, 3)


def _validated_transfer(
    values: object,
    *,
    processing_lmax: int,
    label: str,
) -> np.ndarray:
    vector = _finite_real_vector(
        values,
        dimension=processing_lmax + 1,
        label=f"{label} transfer",
    )
    if np.any(vector <= 0.0):
        raise ProcessedBoostError(f"{label} transfer must be strictly positive")
    return vector


def _evaluate_packed_real_alm(
    alm: np.ndarray,
    direction: object,
    *,
    lmax: int,
) -> np.ndarray:
    """Evaluate a real-map healpy packed alm at arbitrary unit directions."""

    hp = _healpy()
    directions = _unit_directions(direction)
    coefficients = np.asarray(alm, dtype=np.complex128)
    if coefficients.shape != (hp.Alm.getsize(lmax),) or not np.all(
        np.isfinite(coefficients)
    ):
        raise ProcessedBoostError("packed source alm has the wrong finite shape")
    theta = np.arccos(np.clip(directions[..., 2], -1.0, 1.0))
    phi = np.mod(np.arctan2(directions[..., 1], directions[..., 0]), 2.0 * math.pi)
    values = np.zeros(theta.shape, dtype=np.float64)
    for ell in range(lmax + 1):
        m0 = coefficients[hp.Alm.getidx(lmax, ell, 0)]
        values += float(m0.real) * sph_harm_y(ell, 0, theta, phi).real
        for m in range(1, ell + 1):
            coefficient = coefficients[hp.Alm.getidx(lmax, ell, m)]
            values += 2.0 * np.real(
                coefficient * sph_harm_y(ell, m, theta, phi)
            )
    if not np.all(np.isfinite(values)):
        raise ProcessedBoostError("packed source alm evaluation became nonfinite")
    return values


@dataclass(frozen=True)
class SourceConvolvedMap:
    """Content-bound finite map after the declared source-transfer ordering."""

    pixel_map: np.ndarray
    beta: np.ndarray
    nside: int
    processing_lmax: int
    source_sky_id: str
    transfer_id: str
    mutation: str | None
    content_id: str

    def __post_init__(self) -> None:
        hp = _healpy()
        values = np.asarray(self.pixel_map, dtype=np.float64)
        velocity = _finite_beta(self.beta)
        if values.shape != (hp.nside2npix(self.nside),) or not np.all(
            np.isfinite(values)
        ):
            raise ProcessedBoostError("source-convolved pixel map has the wrong finite shape")
        if self.mutation not in _ALLOWED_SOURCE_MUTATIONS:
            raise ProcessedBoostError("source-transfer mutation is outside the frozen registry")
        sealed_map = np.frombuffer(values.astype("<f8").tobytes(), dtype="<f8")
        sealed_beta = np.frombuffer(velocity.astype("<f8").tobytes(), dtype="<f8")
        object.__setattr__(self, "pixel_map", sealed_map)
        object.__setattr__(self, "beta", sealed_beta)


def source_convolved_finite_map(
    source_sky: PositiveAbsoluteSkySpec,
    beta: object,
    *,
    nside: int,
    processing_lmax: int,
    source_beam: object,
    source_pixel_window: object,
    mutation: str | None = None,
) -> SourceConvolvedMap:
    """Apply the finite local boost and registered source transfer on HEALPix.

    Baseline order is exact finite field pullback followed by the source beam
    and pixel-window convolution.  ``TRANSFER_BEFORE_BOOST`` deliberately
    reverses those two operations and is content-bound as a mutation.

    ``processing_lmax`` is the explicit numerical harmonic cutoff of this
    bounded source-transfer operator.  It must include the intrinsic source
    band and obey the standard HEALPix ``3*nside-1`` ceiling.
    """

    hp = _healpy()
    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise ProcessedBoostError("source sky must be an exact PositiveAbsoluteSkySpec")
    velocity = _finite_beta(beta)
    if type(nside) is not int or not hp.isnsideok(nside):
        raise ProcessedBoostError("nside must be a valid positive HEALPix nside")
    if (
        type(processing_lmax) is not int
        or processing_lmax < source_sky.source_lmax
        or processing_lmax > 3 * nside - 1
    ):
        raise ProcessedBoostError(
            "processing lmax must include the source band and not exceed 3*nside-1"
        )
    if mutation not in _ALLOWED_SOURCE_MUTATIONS:
        raise ProcessedBoostError("source-transfer mutation is outside the frozen registry")
    beam = _validated_transfer(
        source_beam,
        processing_lmax=processing_lmax,
        label="source beam",
    )
    pixel_window = _validated_transfer(
        source_pixel_window,
        processing_lmax=processing_lmax,
        label="source pixel-window",
    )
    transfer = beam * pixel_window
    directions = healpix_sky_directions(nside)

    if mutation is None:
        boosted = pullback_thermodynamic_temperature_field(
            directions,
            velocity,
            source_sky.evaluate,
        )
        boosted_alm = hp.map2alm(
            boosted,
            lmax=processing_lmax,
            iter=_MAP2ALM_ITERATIONS,
            pol=False,
        )
        filtered_alm = hp.almxfl(boosted_alm, transfer, inplace=False)
        pixel_map = hp.alm2map(
            filtered_alm,
            nside=nside,
            lmax=processing_lmax,
            pol=False,
        )
    else:
        intrinsic_map = source_sky.evaluate(directions)
        intrinsic_alm = hp.map2alm(
            intrinsic_map,
            lmax=processing_lmax,
            iter=_MAP2ALM_ITERATIONS,
            pol=False,
        )
        filtered_alm = hp.almxfl(intrinsic_alm, transfer, inplace=False)

        def filtered_source(query_direction: np.ndarray) -> np.ndarray:
            return _evaluate_packed_real_alm(
                filtered_alm,
                query_direction,
                lmax=processing_lmax,
            )

        pixel_map = pullback_thermodynamic_temperature_field(
            directions,
            velocity,
            filtered_source,
        )

    pixel_map = np.asarray(pixel_map, dtype=np.float64)
    if pixel_map.shape != (hp.nside2npix(nside),) or not np.all(
        np.isfinite(pixel_map)
    ):
        raise ProcessedBoostError("source-convolved finite map became nonfinite")

    transfer_id = _canonical_hash(
        {
            "schema": "HTT_WU011_SOURCE_TRANSFER_V1",
            "processing_lmax": processing_lmax,
        },
        beam,
        pixel_window,
    )
    content_id = _canonical_hash(
        {
            "schema": _SOURCE_MAP_SCHEMA,
            "source_sky_id": source_sky.content_id,
            "nside": nside,
            "processing_lmax": processing_lmax,
            "transfer_id": transfer_id,
            "mutation": mutation,
            "healpy_version": hp.__version__,
            "map2alm_iterations": _MAP2ALM_ITERATIONS,
        },
        velocity,
        pixel_map,
    )
    return SourceConvolvedMap(
        pixel_map=pixel_map,
        beta=velocity,
        nside=nside,
        processing_lmax=processing_lmax,
        source_sky_id=source_sky.content_id,
        transfer_id=transfer_id,
        mutation=mutation,
        content_id=content_id,
    )


__all__ = [
    "FIT_LMAX",
    "JOINT_ESTIMATOR_ID",
    "PROCESSING_ORDER",
    "PositiveAbsoluteSkySpec",
    "ProcessedBoostError",
    "ProcessedBoostTerminal",
    "RETAINED_LMIN",
    "SOURCE_LMAX",
    "SourceConvolvedMap",
    "WU010_CLOSEOUT_HEAD",
    "healpix_sky_directions",
    "joint_to_scientific_real",
    "scientific_to_joint_real",
    "source_convolved_finite_map",
]
