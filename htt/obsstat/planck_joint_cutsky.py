"""Joint cut-sky low-ell estimator for the PR-315 Planck repair.

This module implements one weighted fit over all real harmonics with
``0 <= ell <= 5`` and returns only the retained ``2 <= ell <= 5`` block.
Pixels with zero analysis weight never enter the normal equations or residual.
Beam/pixel commonization is applied only after the joint masked fit.

The implementation is exploratory/non-authoritative until the exact observed
SMICA plus 300-pair rerun and claim-bearing review are complete.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np

from .planck_post275_lane import PlanckLaneContractError
from .planck_pr3_operator import (
    LMAX,
    LMIN,
    real_alm_layout,
    real_vector_to_alm,
)


SCHEMA_VERSION = "htt.obsstat.planck_joint_cutsky.v1"


def _healpy():
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - optional dependency boundary
        raise PlanckLaneContractError(
            "healpy is required by the Planck joint cut-sky estimator"
        ) from exc
    return hp


def _finite_vector(values: object, *, label: str) -> np.ndarray:
    try:
        vector = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlanckLaneContractError(f"{label} must be numeric") from exc
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        raise PlanckLaneContractError(f"{label} must be a finite non-empty vector")
    return vector


def _sha256_array(array: np.ndarray, *, role: str) -> str:
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(value.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(value.shape).encode("ascii") + b"\0")
    digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


def _real_harmonic_design_block(
    nside: int,
    pixels: np.ndarray,
    *,
    lmax: int,
) -> np.ndarray:
    hp = _healpy()
    from scipy.special import sph_harm_y

    theta, phi = hp.pix2ang(nside, pixels)
    layout = real_alm_layout(lmin=0, lmax=lmax)
    design = np.empty((pixels.size, len(layout)), dtype=float)
    for column, (ell, m, kind) in enumerate(layout):
        harmonic = sph_harm_y(ell, m, theta, phi)
        if m == 0:
            design[:, column] = harmonic.real
        elif kind == "real":
            design[:, column] = math.sqrt(2.0) * harmonic.real
        else:
            design[:, column] = math.sqrt(2.0) * harmonic.imag
    return design


def _retained_transfer_ratio(
    *,
    source_beam: object,
    source_pixel_window: object,
    target_beam: object,
    target_pixel_window: object,
    lmax: int,
    amplification_tolerance: float,
) -> np.ndarray:
    arrays = [
        _finite_vector(value, label=label)
        for value, label in (
            (source_beam, "source beam"),
            (source_pixel_window, "source pixel window"),
            (target_beam, "target beam"),
            (target_pixel_window, "target pixel window"),
        )
    ]
    if any(array.size < lmax + 1 for array in arrays):
        raise PlanckLaneContractError(
            "beam/pixel transfer does not cover the fitted band"
        )
    source = arrays[0][: lmax + 1] * arrays[1][: lmax + 1]
    target = arrays[2][: lmax + 1] * arrays[3][: lmax + 1]
    retained = slice(LMIN, lmax + 1)
    if np.any(source[retained] <= 0.0) or np.any(target[retained] <= 0.0):
        raise PlanckLaneContractError(
            "retained beam/pixel transfers must be positive"
        )
    ratio = np.ones(lmax + 1, dtype=float)
    ratio[retained] = target[retained] / source[retained]
    if np.any(ratio[retained] > 1.0 + amplification_tolerance):
        raise PlanckLaneContractError(
            "common target would amplify a retained source transfer"
        )
    return ratio


@dataclass(frozen=True)
class JointCutSkyLowEllFit:
    """Result of one joint weighted ``ell=0..lmax`` fit."""

    retained_alm: np.ndarray
    fitted_real_coefficients: np.ndarray
    normal_matrix: np.ndarray
    singular_values: tuple[float, ...]
    condition_number: float
    relative_singular_floor: float
    weighted_residual_norm: float
    lmax: int
    nside: int
    support_pixels: int
    basis_order: tuple[tuple[int, int, str], ...]
    mask_sha256: str
    normal_matrix_sha256: str
    schema: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        hp = _healpy()
        expected_dimension = len(real_alm_layout(lmin=0, lmax=self.lmax))
        if (
            self.retained_alm.shape != (hp.Alm.getsize(self.lmax),)
            or self.fitted_real_coefficients.shape != (expected_dimension,)
            or self.normal_matrix.shape != (expected_dimension, expected_dimension)
        ):
            raise PlanckLaneContractError(
                "joint cut-sky result dimensions drifted"
            )
        if not np.all(np.isfinite(self.fitted_real_coefficients)):
            raise PlanckLaneContractError(
                "joint cut-sky coefficients are not finite"
            )
        if not np.all(np.isfinite(self.normal_matrix)):
            raise PlanckLaneContractError(
                "joint cut-sky normal matrix is not finite"
            )
        if (
            not math.isfinite(self.condition_number)
            or not math.isfinite(self.relative_singular_floor)
            or not math.isfinite(self.weighted_residual_norm)
            or self.condition_number < 1.0
            or not 0.0 < self.relative_singular_floor <= 1.0
            or self.weighted_residual_norm < 0.0
        ):
            raise PlanckLaneContractError(
                "joint cut-sky diagnostics are invalid"
            )
        for ell in range(0, LMIN):
            for m in range(0, ell + 1):
                if self.retained_alm[hp.Alm.getidx(self.lmax, ell, m)] != 0.0:
                    raise PlanckLaneContractError(
                        "nuisance multipoles leaked into retained alm"
                    )


def fit_joint_cutsky_lowell(
    pixel_map: object,
    *,
    common_mask: object,
    source_beam: object,
    source_pixel_window: object,
    target_beam: object,
    target_pixel_window: object,
    lmax: int = LMAX,
    relative_threshold: float = 1e-10,
    condition_ceiling: float = 1e8,
    amplification_tolerance: float = 1e-10,
    chunk_size: int = 65_536,
) -> JointCutSkyLowEllFit:
    """Jointly fit nuisance and retained low multipoles on the cut sky.

    The fitted basis contains all real harmonics with ``0 <= ell <= lmax``.
    The nuisance block ``ell=0,1`` is solved simultaneously but zeroed in the
    returned packed alm. Only the retained ``ell>=2`` coefficients receive the
    source-to-target beam/pixel transfer.
    """

    hp = _healpy()
    values = _finite_vector(pixel_map, label="temperature map")
    weights = _finite_vector(common_mask, label="analysis mask")
    if values.shape != weights.shape:
        raise PlanckLaneContractError("map and mask pixelization differ")
    nside = hp.npix2nside(values.size)
    if (
        np.any(weights < 0.0)
        or np.any(weights > 1.0)
        or np.count_nonzero(weights) == 0
    ):
        raise PlanckLaneContractError(
            "analysis mask weights must lie in [0,1] with support"
        )
    if type(lmax) is not int or lmax < LMIN:
        raise PlanckLaneContractError("joint cut-sky lmax is invalid")
    if (
        not math.isfinite(relative_threshold)
        or not 0.0 < relative_threshold < 1.0
        or not math.isfinite(condition_ceiling)
        or condition_ceiling <= 1.0
        or type(chunk_size) is not int
        or chunk_size < 1
    ):
        raise PlanckLaneContractError(
            "joint cut-sky numerical thresholds are invalid"
        )

    layout = real_alm_layout(lmin=0, lmax=lmax)
    dimension = len(layout)
    normal = np.zeros((dimension, dimension), dtype=float)
    rhs = np.zeros(dimension, dtype=float)
    npix = values.size

    for start in range(0, npix, chunk_size):
        stop = min(npix, start + chunk_size)
        local_weights = weights[start:stop]
        if not np.any(local_weights > 0.0):
            continue
        pixels = np.arange(start, stop)
        design = _real_harmonic_design_block(nside, pixels, lmax=lmax)
        weighted_design = design * np.sqrt(local_weights)[:, None]
        normal += weighted_design.T @ weighted_design
        rhs += design.T @ (local_weights * values[start:stop])

    pixel_area = 4.0 * math.pi / npix
    normal *= pixel_area
    rhs *= pixel_area
    singular_values = np.linalg.svd(normal, compute_uv=False)
    if singular_values.size != dimension:
        raise PlanckLaneContractError(
            "joint cut-sky singular spectrum has the wrong dimension"
        )
    largest = float(singular_values[0])
    smallest = float(singular_values[-1])
    if (
        not math.isfinite(largest)
        or largest <= 0.0
        or smallest <= relative_threshold * largest
    ):
        raise PlanckLaneContractError(
            "joint cut-sky normal matrix is rank deficient"
        )
    condition = largest / smallest
    if not math.isfinite(condition) or condition > condition_ceiling:
        raise PlanckLaneContractError(
            "joint cut-sky normal matrix exceeds the condition ceiling"
        )
    coefficients = np.linalg.solve(normal, rhs)

    residual_sum = 0.0
    for start in range(0, npix, chunk_size):
        stop = min(npix, start + chunk_size)
        local_weights = weights[start:stop]
        if not np.any(local_weights > 0.0):
            continue
        pixels = np.arange(start, stop)
        design = _real_harmonic_design_block(nside, pixels, lmax=lmax)
        residual = values[start:stop] - design @ coefficients
        residual_sum += float(np.dot(local_weights, residual * residual))
    residual_norm = math.sqrt(pixel_area * max(0.0, residual_sum))

    fitted_alm = real_vector_to_alm(coefficients, lmin=0, lmax=lmax)
    for ell in range(0, LMIN):
        for m in range(0, ell + 1):
            fitted_alm[hp.Alm.getidx(lmax, ell, m)] = 0.0
    ratio = _retained_transfer_ratio(
        source_beam=source_beam,
        source_pixel_window=source_pixel_window,
        target_beam=target_beam,
        target_pixel_window=target_pixel_window,
        lmax=lmax,
        amplification_tolerance=amplification_tolerance,
    )
    retained_alm = hp.almxfl(fitted_alm, ratio, inplace=False)

    return JointCutSkyLowEllFit(
        retained_alm=np.asarray(retained_alm, dtype=np.complex128),
        fitted_real_coefficients=np.asarray(coefficients, dtype=float),
        normal_matrix=normal,
        singular_values=tuple(float(value) for value in singular_values),
        condition_number=condition,
        relative_singular_floor=smallest / largest,
        weighted_residual_norm=residual_norm,
        lmax=lmax,
        nside=nside,
        support_pixels=int(np.count_nonzero(weights)),
        basis_order=layout,
        mask_sha256=_sha256_array(weights, role="joint_cutsky_common_mask"),
        normal_matrix_sha256=_sha256_array(
            normal, role="joint_cutsky_normal_matrix"
        ),
    )


__all__ = [
    "JointCutSkyLowEllFit",
    "SCHEMA_VERSION",
    "fit_joint_cutsky_lowell",
]
