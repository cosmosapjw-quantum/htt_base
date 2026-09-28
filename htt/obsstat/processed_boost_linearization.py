"""First-order processed local-observer boost response for PMG-WU-011.

This companion module differentiates the reviewed WU-010 finite scalar
pullback before source transfer, HEALPix synthesis, the authoritative weighted
joint ``ell=0..5`` solve, post-fit target/source commonization, and retained
``ell=2..5`` selection.  The intrinsic generator in the outward sky convention
``n=-e`` and active observer boost ``+beta`` is

``delta_beta T = (beta.n) T - [beta-(beta.n)n].grad_S2 T``.

``healpy.alm2map_der1`` supplies ``d_theta`` and ``d_phi/sin(theta)`` for the
known band-limited source sky.  The signed generator is never sent through the
strict-positive absolute-temperature API.

The omitted-``ell=1`` mutation is deliberately audited in two spaces.  It
leaves an O(beta) pixel-space error, but an exact simultaneous weighted
``ell=0..5`` solve profiles ``ell=0,1`` and must not manufacture a retained
``ell=2..5`` response from that omission.  This is the Frisch--Waugh--Lovell
nuisance statement, not a claim that the physical dipole may be dropped from
the sky model.

No observed data, empirical velocity estimate, global matter-frame tilt,
polarization response, foreground exclusion, or Bianchi-family attribution is
introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math

import numpy as np

from .planck_pr3_operator import fit_joint_cutsky_alm
from .processed_boost_operator import (
    ProcessedBoostOperator,
    evaluate_processed_boost,
)
from .processed_boost_response import (
    FIT_LMAX,
    RETAINED_LMIN,
    PositiveAbsoluteSkySpec,
    ProcessedBoostError,
    _intrinsic_healpy_alm,
    healpix_sky_directions,
    joint_to_scientific_real,
)


_LINEAR_EVALUATION_SCHEMA = "HTT_WU011_PROCESSED_LINEAR_EVALUATION_V1"
_ALLOWED_LINEAR_MUTATIONS = {None, "WRONG_SIGN", "OMIT_L1"}
_MAP2ALM_ITERATIONS = 3
_DIRECTION_ATOL = 5.0e-13


def _healpy():
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - optional dependency gate
        raise ProcessedBoostError(
            "healpy is required for the WU-011 processed linearization path"
        ) from exc
    return hp


def _finite_beta(beta: object) -> np.ndarray:
    try:
        vector = np.asarray(beta, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError("beta must be a finite real three-vector") from exc
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError("beta must be a finite real three-vector")
    return vector


def _unit_direction(value: object) -> np.ndarray:
    vector = _finite_beta(value)
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or abs(norm - 1.0) > _DIRECTION_ATOL:
        raise ProcessedBoostError("beta direction must be a finite unit three-vector")
    return vector


def _amplitudes(values: object) -> tuple[float, ...]:
    try:
        result = tuple(float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            "amplitudes must contain at least three finite positive values"
        ) from exc
    if (
        len(result) < 3
        or any(not math.isfinite(value) or value <= 0.0 for value in result)
        or any(left <= right for left, right in zip(result, result[1:]))
    ):
        raise ProcessedBoostError(
            "amplitudes must be finite, positive, and strictly decreasing"
        )
    return result


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


def _scientific_retained_norm(values: object) -> float:
    vector = np.asarray(values, dtype=np.float64)
    expected = sum(2 * ell + 1 for ell in range(RETAINED_LMIN, FIT_LMAX + 1))
    if vector.shape != (expected,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError(
            "retained scientific carrier has the wrong finite shape"
        )
    cursor = 0
    norm2 = 0.0
    for ell in range(RETAINED_LMIN, FIT_LMAX + 1):
        norm2 += float(vector[cursor] ** 2)
        cursor += 1
        for _m in range(1, ell + 1):
            norm2 += 2.0 * float(
                vector[cursor] ** 2 + vector[cursor + 1] ** 2
            )
            cursor += 2
    if cursor != expected:
        raise ProcessedBoostError("retained scientific norm registry drifted")
    return math.sqrt(max(0.0, norm2))


def _positive_log_slope(amplitudes: tuple[float, ...], norms: tuple[float, ...]) -> float:
    if len(amplitudes) != len(norms) or len(norms) < 3:
        raise ProcessedBoostError("at least three residual norms are required")
    if any(not math.isfinite(value) or value <= 0.0 for value in norms):
        raise ProcessedBoostError(
            "residual norms must remain finite and above the numerical floor"
        )
    return float(np.polyfit(np.log(amplitudes), np.log(norms), 1)[0])


def intrinsic_scalar_generator_map(
    source_sky: PositiveAbsoluteSkySpec,
    beta: object,
    *,
    nside: int,
    processing_lmax: int,
) -> np.ndarray:
    """Evaluate the exact first-order Doppler-weight-one scalar generator.

    The result is a signed field linear in ``beta``.  It contains the physical
    monopole-induced dipole and every source-band coupling through
    ``ell=source_lmax+1`` within the declared numerical cutoff.
    """

    hp = _healpy()
    if type(source_sky) is not PositiveAbsoluteSkySpec:
        raise ProcessedBoostError("source sky must be an exact PositiveAbsoluteSkySpec")
    velocity = _finite_beta(beta)
    if type(nside) is not int or not hp.isnsideok(nside, nest=False):
        raise ProcessedBoostError("nside must be a valid positive HEALPix nside")
    if (
        type(processing_lmax) is not int
        or processing_lmax < source_sky.source_lmax + 1
        or processing_lmax > 3 * nside - 1
    ):
        raise ProcessedBoostError(
            "processing lmax must include the first-order raised source band"
        )

    intrinsic_alm = _intrinsic_healpy_alm(
        source_sky,
        processing_lmax=processing_lmax,
    )
    sky_map, d_theta, d_phi_over_sin = hp.alm2map_der1(
        intrinsic_alm,
        nside=nside,
        lmax=processing_lmax,
    )
    pixels = np.arange(hp.nside2npix(nside), dtype=np.int64)
    theta, phi = hp.pix2ang(nside, pixels, nest=False)
    directions = healpix_sky_directions(nside)
    e_theta = np.column_stack(
        (
            np.cos(theta) * np.cos(phi),
            np.cos(theta) * np.sin(phi),
            -np.sin(theta),
        )
    )
    e_phi = np.column_stack((-np.sin(phi), np.cos(phi), np.zeros_like(phi)))
    gradient = (
        np.asarray(d_theta, dtype=np.float64)[:, None] * e_theta
        + np.asarray(d_phi_over_sin, dtype=np.float64)[:, None] * e_phi
    )
    projection = directions @ velocity
    tangent_velocity = velocity[None, :] - projection[:, None] * directions
    generator = projection * np.asarray(sky_map, dtype=np.float64) - np.einsum(
        "ij,ij->i", tangent_velocity, gradient
    )
    if generator.shape != (hp.nside2npix(nside),) or not np.all(
        np.isfinite(generator)
    ):
        raise ProcessedBoostError("intrinsic scalar generator became nonfinite")
    return generator


def source_convolved_linear_map(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
    beta: object,
    *,
    mutation: str | None = None,
) -> np.ndarray:
    """Apply source transfer to the signed first-order generator field."""

    hp = _healpy()
    if type(operator) is not ProcessedBoostOperator:
        raise ProcessedBoostError("operator must be an exact ProcessedBoostOperator")
    if mutation not in _ALLOWED_LINEAR_MUTATIONS:
        raise ProcessedBoostError("linear mutation is outside the frozen registry")
    generator = intrinsic_scalar_generator_map(
        source_sky,
        beta,
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
    )
    if mutation == "WRONG_SIGN":
        generator = -generator
    generator_alm = hp.map2alm(
        generator,
        lmax=operator.processing_lmax,
        iter=_MAP2ALM_ITERATIONS,
        pol=False,
    )
    if mutation == "OMIT_L1":
        for m in range(0, 2):
            generator_alm[hp.Alm.getidx(operator.processing_lmax, 1, m)] = 0.0
    transfer = operator.source_beam * operator.source_pixel_window
    filtered_alm = hp.almxfl(generator_alm, transfer, inplace=False)
    pixel_map = hp.alm2map(
        filtered_alm,
        nside=operator.nside,
        lmax=operator.processing_lmax,
        pol=False,
    )
    result = np.asarray(pixel_map, dtype=np.float64)
    if result.shape != operator.mask.shape or not np.all(np.isfinite(result)):
        raise ProcessedBoostError("source-convolved linear map became nonfinite")
    return result


@dataclass(frozen=True)
class ProcessedLinearEvaluation:
    """Content-bound retained response of the processed first-order generator."""

    retained_coefficients: np.ndarray
    joint_all_coefficients: np.ndarray
    weighted_residual_norm: float
    beta: np.ndarray
    mutation: str | None
    operator_id: str
    source_sky_id: str
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        retained = np.asarray(self.retained_coefficients, dtype=np.float64)
        all_joint = np.asarray(self.joint_all_coefficients, dtype=np.float64)
        velocity = _finite_beta(self.beta)
        if retained.shape != (32,) or not np.all(np.isfinite(retained)):
            raise ProcessedBoostError("linear retained carrier has the wrong finite shape")
        if all_joint.shape != (36,) or not np.all(np.isfinite(all_joint)):
            raise ProcessedBoostError("linear joint carrier has the wrong finite shape")
        residual = float(self.weighted_residual_norm)
        if not math.isfinite(residual) or residual < 0.0:
            raise ProcessedBoostError("linear weighted residual must be finite and nonnegative")
        if self.mutation not in _ALLOWED_LINEAR_MUTATIONS:
            raise ProcessedBoostError("linear mutation is outside the frozen registry")
        sealed_retained = np.frombuffer(retained.astype("<f8").tobytes(), dtype="<f8")
        sealed_all = np.frombuffer(all_joint.astype("<f8").tobytes(), dtype="<f8")
        sealed_beta = np.frombuffer(velocity.astype("<f8").tobytes(), dtype="<f8")
        content_id = _canonical_hash(
            {
                "schema": _LINEAR_EVALUATION_SCHEMA,
                "operator_id": self.operator_id,
                "source_sky_id": self.source_sky_id,
                "mutation": self.mutation,
                "weighted_residual_norm_hex": residual.hex(),
            },
            sealed_retained,
            sealed_all,
            sealed_beta,
        )
        object.__setattr__(self, "retained_coefficients", sealed_retained)
        object.__setattr__(self, "joint_all_coefficients", sealed_all)
        object.__setattr__(self, "weighted_residual_norm", residual)
        object.__setattr__(self, "beta", sealed_beta)
        object.__setattr__(self, "content_id", content_id)


def evaluate_processed_linear_response(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
    beta: object,
    *,
    mutation: str | None = None,
) -> ProcessedLinearEvaluation:
    """Route the signed generator through the authoritative joint solver."""

    pixel_map = source_convolved_linear_map(
        source_sky,
        operator,
        beta,
        mutation=mutation,
    )
    fit = fit_joint_cutsky_alm(
        pixel_map,
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
    return ProcessedLinearEvaluation(
        retained_coefficients=retained,
        joint_all_coefficients=fit.all_coefficients,
        weighted_residual_norm=fit.weighted_residual_norm,
        beta=np.asarray(beta, dtype=np.float64),
        mutation=mutation,
        operator_id=operator.content_id,
        source_sky_id=source_sky.content_id,
    )


@dataclass(frozen=True)
class FiniteToLinearDiagnostic:
    amplitudes: tuple[float, ...]
    residual_norms: tuple[float, ...]
    scaled_quadratic_norms: tuple[float, ...]
    residual_slope: float
    scaled_plateau_relative_spread: float


@dataclass(frozen=True)
class MutationOrderDiagnostic:
    amplitudes: tuple[float, ...]
    wrong_sign_retained_norms: tuple[float, ...]
    omitted_l1_pixel_norms: tuple[float, ...]
    wrong_sign_retained_slope: float
    omitted_l1_pixel_slope: float
    omitted_l1_retained_relative_norm: float


def finite_to_linear_diagnostic(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
    *,
    beta_direction: object,
    amplitudes: object,
) -> FiniteToLinearDiagnostic:
    """Verify ``R(beta)-R(0)-G(beta)=O(|beta|^2)`` in retained space."""

    direction = _unit_direction(beta_direction)
    scales = _amplitudes(amplitudes)
    baseline = evaluate_processed_boost(
        source_sky,
        operator,
        np.zeros(3),
        mode="FINITE",
    )
    unit_linear = evaluate_processed_linear_response(
        source_sky,
        operator,
        direction,
    )
    norms: list[float] = []
    for amplitude in scales:
        finite = evaluate_processed_boost(
            source_sky,
            operator,
            amplitude * direction,
            mode="FINITE",
        )
        residual = (
            finite.retained_coefficients
            - baseline.retained_coefficients
            - amplitude * unit_linear.retained_coefficients
        )
        norms.append(_scientific_retained_norm(residual))
    residual_norms = tuple(norms)
    slope = _positive_log_slope(scales, residual_norms)
    scaled = tuple(
        norm / (amplitude * amplitude)
        for amplitude, norm in zip(scales, residual_norms)
    )
    centre = float(np.mean(scaled))
    if not math.isfinite(centre) or centre <= 0.0:
        raise ProcessedBoostError("scaled quadratic plateau is not finite and positive")
    spread = float((max(scaled) - min(scaled)) / centre)
    return FiniteToLinearDiagnostic(
        amplitudes=scales,
        residual_norms=residual_norms,
        scaled_quadratic_norms=scaled,
        residual_slope=slope,
        scaled_plateau_relative_spread=spread,
    )


def mutation_order_diagnostic(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
    *,
    beta_direction: object,
    amplitudes: object,
) -> MutationOrderDiagnostic:
    """Separate physical pixel mutations from nuisance-profiled retained modes."""

    direction = _unit_direction(beta_direction)
    scales = _amplitudes(amplitudes)
    baseline = evaluate_processed_boost(
        source_sky,
        operator,
        np.zeros(3),
        mode="FINITE",
    )
    baseline_map = source_convolved_linear_map(
        source_sky,
        operator,
        np.zeros(3),
    )
    # The linear zero map is exactly zero; using it here seals the signed-map
    # dimensions without reusing the positive finite-map type.
    if np.linalg.norm(baseline_map) != 0.0:
        raise ProcessedBoostError("zero-beta linear source map is not exactly zero")
    full_linear = evaluate_processed_linear_response(source_sky, operator, direction)
    wrong_linear = evaluate_processed_linear_response(
        source_sky,
        operator,
        direction,
        mutation="WRONG_SIGN",
    )
    omitted_linear = evaluate_processed_linear_response(
        source_sky,
        operator,
        direction,
        mutation="OMIT_L1",
    )
    omitted_map = source_convolved_linear_map(
        source_sky,
        operator,
        direction,
        mutation="OMIT_L1",
    )
    full_map = source_convolved_linear_map(source_sky, operator, direction)

    wrong_norms: list[float] = []
    omitted_pixel_norms: list[float] = []
    zero_finite_map = None
    from .processed_boost_response import source_convolved_finite_map

    zero_finite_map = source_convolved_finite_map(
        source_sky,
        np.zeros(3),
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
    ).pixel_map
    for amplitude in scales:
        finite = evaluate_processed_boost(
            source_sky,
            operator,
            amplitude * direction,
            mode="FINITE",
        )
        wrong_residual = (
            finite.retained_coefficients
            - baseline.retained_coefficients
            - amplitude * wrong_linear.retained_coefficients
        )
        wrong_norms.append(_scientific_retained_norm(wrong_residual))
        finite_map = source_convolved_finite_map(
            source_sky,
            amplitude * direction,
            nside=operator.nside,
            processing_lmax=operator.processing_lmax,
            source_beam=operator.source_beam,
            source_pixel_window=operator.source_pixel_window,
        ).pixel_map
        omitted_residual = finite_map - zero_finite_map - amplitude * omitted_map
        omitted_pixel_norms.append(float(np.linalg.norm(omitted_residual)))

    full_norm = _scientific_retained_norm(full_linear.retained_coefficients)
    omitted_difference = _scientific_retained_norm(
        full_linear.retained_coefficients - omitted_linear.retained_coefficients
    )
    relative = omitted_difference / max(full_norm, np.finfo(float).tiny)
    return MutationOrderDiagnostic(
        amplitudes=scales,
        wrong_sign_retained_norms=tuple(wrong_norms),
        omitted_l1_pixel_norms=tuple(omitted_pixel_norms),
        wrong_sign_retained_slope=_positive_log_slope(scales, tuple(wrong_norms)),
        omitted_l1_pixel_slope=_positive_log_slope(
            scales, tuple(omitted_pixel_norms)
        ),
        omitted_l1_retained_relative_norm=float(relative),
    )


__all__ = [
    "FiniteToLinearDiagnostic",
    "MutationOrderDiagnostic",
    "ProcessedLinearEvaluation",
    "evaluate_processed_linear_response",
    "finite_to_linear_diagnostic",
    "intrinsic_scalar_generator_map",
    "mutation_order_diagnostic",
    "source_convolved_linear_map",
]
