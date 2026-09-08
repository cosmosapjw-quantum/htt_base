"""Direction-indexed scalar dipole/STF extraction for PR-326.

OBSSTAT owns only the observable moment estimate.  The full-sky path uses the
registered ``3/(4 pi)`` and ``15/(8 pi)`` integrals after verifying the supplied
quadrature through degree four.  The current exactness contract is deliberately
limited to fields with ``ell <= 2``.  Masked or discrete samples use one bound
weighted joint monopole/dipole/STF fit under that same no-omitted-mode scope.
Neither path identifies a physical shear, vorticity, geometry, or Bianchi
family.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Sequence

import numpy as np

from common.mes_directional_state import (
    MAX_DIRECTIONAL_DESIGN_CONDITION,
    DirectionConvention,
    DirectionalBridgeError,
    DirectionalEstimatorKind,
    DirectionalFieldParity,
    DirectionalMomentEstimate,
    SphericalSecondMomentCertificate,
    certify_spherical_second_moment,
    make_directional_moment_estimate,
)
from common.observable_irrep_state import (
    ObservableIrrepBlock,
    ObservableIrrepRepresentation,
    ObservableIrrepState,
    build_cartesian_stf_irrep_block,
)


_FOUR_PI = 4.0 * math.pi
_QUADRATURE_ATOL = 8.0e-12
_UNIT_ATOL = 2.0e-12


def _numeric_identity(values: object, *, role: str) -> str:
    try:
        array = np.asarray(values, dtype="<f8")
    except (TypeError, ValueError) as exc:
        raise DirectionalBridgeError(f"{role} must be finite numeric content") from exc
    if array.size == 0 or not np.all(np.isfinite(array)):
        raise DirectionalBridgeError(f"{role} must be finite numeric content")
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(role.encode("utf-8") + b"\0")
    digest.update(contiguous.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(contiguous.shape).encode("ascii") + b"\0")
    digest.update(memoryview(contiguous).cast("B"))
    return "sha256:" + digest.hexdigest()


def _canonical_identity(payload: object, *, role: str) -> str:
    encoded = json.dumps(
        {"role": role, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validated_samples(
    directions: object,
    values: object,
    weights: object,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    try:
        direction_array = np.asarray(directions, dtype=float)
        value_array = np.asarray(values, dtype=float)
        weight_array = np.asarray(weights, dtype=float)
    except (TypeError, ValueError) as exc:
        raise DirectionalBridgeError("direction-indexed samples must be numeric") from exc
    if (
        direction_array.ndim != 2
        or direction_array.shape[1:] != (3,)
        or value_array.shape != (len(direction_array),)
        or weight_array.shape != (len(direction_array),)
        or len(direction_array) == 0
        or not np.all(np.isfinite(direction_array))
        or not np.all(np.isfinite(value_array))
        or not np.all(np.isfinite(weight_array))
        or np.any(weight_array < 0.0)
    ):
        raise DirectionalBridgeError(
            "directions, values and non-negative weights must align and be finite"
        )
    norms = np.linalg.norm(direction_array, axis=1)
    if not np.allclose(norms, 1.0, rtol=0.0, atol=_UNIT_ATOL):
        raise DirectionalBridgeError("directions must be unit 3-vectors")
    return direction_array, value_array, weight_array


def _stf_projection(matrix: np.ndarray) -> np.ndarray:
    symmetric = 0.5 * (matrix + matrix.T)
    return symmetric - np.eye(3) * float(np.trace(symmetric)) / 3.0


def _quadrature_is_registered(directions: np.ndarray, weights: np.ndarray) -> bool:
    identity = np.eye(3)
    second = np.einsum("n,ni,nj->ij", weights, directions, directions)
    third = np.einsum("n,ni,nj,nk->ijk", weights, directions, directions, directions)
    fourth = np.einsum(
        "n,ni,nj,nk,nl->ijkl", weights, directions, directions, directions, directions
    )
    expected_fourth = np.empty((3, 3, 3, 3), dtype=float)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for ell in range(3):
                    expected_fourth[i, j, k, ell] = _FOUR_PI / 15.0 * (
                        identity[i, j] * identity[k, ell]
                        + identity[i, k] * identity[j, ell]
                        + identity[i, ell] * identity[j, k]
                    )
    return all(
        (
            math.isclose(
                float(weights.sum()), _FOUR_PI, rel_tol=0.0, abs_tol=_QUADRATURE_ATOL
            ),
            np.allclose(
                np.einsum("n,ni->i", weights, directions),
                0.0,
                rtol=0.0,
                atol=_QUADRATURE_ATOL,
            ),
            np.allclose(
                second,
                _FOUR_PI / 3.0 * identity,
                rtol=0.0,
                atol=_QUADRATURE_ATOL,
            ),
            np.allclose(third, 0.0, rtol=0.0, atol=_QUADRATURE_ATOL),
            np.allclose(
                fourth,
                expected_fourth,
                rtol=0.0,
                atol=_QUADRATURE_ATOL,
            ),
        )
    )


def _fit_design(directions: np.ndarray) -> np.ndarray:
    x, y, z = directions.T
    return np.column_stack(
        (
            np.ones(len(directions)),
            x,
            y,
            z,
            x * x - z * z,
            y * y - z * z,
            2.0 * x * y,
            2.0 * x * z,
            2.0 * y * z,
        )
    )


def _scale_aware_design_condition(weighted_design: np.ndarray) -> float:
    """Condition the column-normalized design so units/scales cannot hide rank."""

    column_norms = np.linalg.norm(weighted_design, axis=0)
    if not np.all(np.isfinite(column_norms)) or np.any(column_norms == 0.0):
        return math.inf
    normalized = weighted_design / column_norms
    singular_values = np.linalg.svd(normalized, compute_uv=False)
    if (
        singular_values.shape != (9,)
        or not np.all(np.isfinite(singular_values))
        or singular_values[-1] <= 0.0
    ):
        return math.inf
    return float(singular_values[0] / singular_values[-1])


def _make_estimate(
    *,
    monopole: float,
    dipole: np.ndarray,
    stf2: np.ndarray,
    directions: np.ndarray,
    values: np.ndarray,
    weights: np.ndarray,
    field_parity: DirectionalFieldParity,
    field_quantity: str,
    field_units: str,
    field_bandlimit: int,
    estimator_kind: DirectionalEstimatorKind,
    direction_frame: str,
    direction_convention: DirectionConvention,
    mask_identity: str,
    transfer_identity: str,
    field_identity: str,
    covariance_identity: str,
    support_size: int,
    design_rank: int,
    design_condition: float,
    residual: float,
) -> DirectionalMomentEstimate:
    if direction_convention is not DirectionConvention.RIGHT_HANDED_ACTIVE_O3:
        raise DirectionalBridgeError(
            "direction_convention must be RIGHT_HANDED_ACTIVE_O3"
        )
    support_identity = _numeric_identity(directions, role="direction_indexed_support")
    weight_identity = _numeric_identity(weights, role="directional_estimator_weights")
    field_content_identity = _numeric_identity(
        np.column_stack((directions, values)), role="direction_indexed_field_content"
    )
    bound_field_identity = _canonical_identity(
        {"declared_field_identity": field_identity, "content": field_content_identity},
        role="bound_direction_indexed_field",
    )
    return make_directional_moment_estimate(
        monopole=monopole,
        dipole=dipole,
        stf2=_stf_projection(stf2),
        field_parity=field_parity,
        estimator_kind=estimator_kind,
        direction_frame=direction_frame,
        direction_convention=direction_convention,
        field_quantity=field_quantity,
        field_units=field_units,
        field_bandlimit=field_bandlimit,
        support_identity=support_identity,
        weight_identity=weight_identity,
        mask_identity=mask_identity,
        transfer_identity=transfer_identity,
        field_identity=bound_field_identity,
        covariance_identity=covariance_identity,
        support_size=support_size,
        design_rank=design_rank,
        design_condition_number=design_condition,
        max_design_condition_number=MAX_DIRECTIONAL_DESIGN_CONDITION,
        weighted_residual_norm=residual,
    )


def estimate_full_sky_directional_moments(
    *,
    directions: Sequence[Sequence[float]],
    values: Sequence[float],
    weights: Sequence[float],
    field_parity: DirectionalFieldParity,
    field_quantity: str,
    field_units: str,
    field_bandlimit: int,
    direction_frame: str,
    direction_convention: DirectionConvention,
    mask_identity: str,
    transfer_identity: str,
    field_identity: str,
    covariance_identity: str,
) -> DirectionalMomentEstimate:
    """Apply the registered full-sky normalization for an ``ell <= 2`` field."""

    direction_array, value_array, weight_array = _validated_samples(
        directions, values, weights
    )
    if not _quadrature_is_registered(direction_array, weight_array):
        raise DirectionalBridgeError(
            "full-sky quadrature does not reproduce registered sphere moments"
        )
    monopole = float(np.dot(weight_array, value_array) / _FOUR_PI)
    dipole = 3.0 / _FOUR_PI * np.einsum(
        "n,n,ni->i", weight_array, value_array, direction_array
    )
    raw_second = np.einsum(
        "n,n,ni,nj->ij", weight_array, value_array, direction_array, direction_array
    )
    stf2 = 15.0 / (8.0 * math.pi) * _stf_projection(raw_second)
    design = _fit_design(direction_array)
    weighted_design = np.sqrt(weight_array)[:, None] * design
    design_condition = _scale_aware_design_condition(weighted_design)
    if design_condition > MAX_DIRECTIONAL_DESIGN_CONDITION:
        raise DirectionalBridgeError(
            "BLOCKED_DIRECTIONAL_SUPPORT: full-sky design is ill-conditioned"
        )
    reconstructed = design @ np.asarray(
        (
            monopole,
            *dipole,
            stf2[0, 0],
            stf2[1, 1],
            stf2[0, 1],
            stf2[0, 2],
            stf2[1, 2],
        )
    )
    residual = float(
        np.linalg.norm(np.sqrt(weight_array) * (value_array - reconstructed))
    )
    return _make_estimate(
        monopole=monopole,
        dipole=dipole,
        stf2=stf2,
        directions=direction_array,
        values=value_array,
        weights=weight_array,
        field_parity=field_parity,
        field_quantity=field_quantity,
        field_units=field_units,
        field_bandlimit=field_bandlimit,
        estimator_kind=DirectionalEstimatorKind.FULL_SKY_QUADRATURE,
        direction_frame=direction_frame,
        direction_convention=direction_convention,
        mask_identity=mask_identity,
        transfer_identity=transfer_identity,
        field_identity=field_identity,
        covariance_identity=covariance_identity,
        support_size=len(direction_array),
        design_rank=int(np.linalg.matrix_rank(design)),
        design_condition=design_condition,
        residual=residual,
    )


def estimate_joint_fit_directional_moments(
    *,
    directions: Sequence[Sequence[float]],
    values: Sequence[float],
    weights: Sequence[float],
    support_mask: Sequence[bool],
    field_parity: DirectionalFieldParity,
    field_quantity: str,
    field_units: str,
    field_bandlimit: int,
    direction_frame: str,
    direction_convention: DirectionConvention,
    mask_identity: str,
    transfer_identity: str,
    field_identity: str,
    covariance_identity: str,
) -> DirectionalMomentEstimate:
    """Fit an ``ell <= 2`` field jointly on one masked/discrete support."""

    direction_array, value_array, weight_array = _validated_samples(
        directions, values, weights
    )
    mask = np.asarray(support_mask)
    if mask.shape != (len(direction_array),) or mask.dtype.kind != "b":
        raise DirectionalBridgeError("support_mask must be a boolean row mask")
    active = mask & (weight_array > 0.0)
    selected_directions = direction_array[active]
    selected_values = value_array[active]
    selected_weights = weight_array[active]
    design = _fit_design(selected_directions)
    weighted_design = np.sqrt(selected_weights)[:, None] * design
    weighted_values = np.sqrt(selected_weights) * selected_values
    rank = int(np.linalg.matrix_rank(weighted_design))
    if len(selected_values) < 9 or rank != 9:
        raise DirectionalBridgeError(
            "BLOCKED_DIRECTIONAL_SUPPORT: weighted joint design rank is below 9"
        )
    design_condition = _scale_aware_design_condition(weighted_design)
    if design_condition > MAX_DIRECTIONAL_DESIGN_CONDITION:
        raise DirectionalBridgeError(
            "BLOCKED_DIRECTIONAL_SUPPORT: weighted joint design is ill-conditioned"
        )
    coefficients, _, fitted_rank, _ = np.linalg.lstsq(
        weighted_design, weighted_values, rcond=None
    )
    if int(fitted_rank) != 9:
        raise DirectionalBridgeError(
            "BLOCKED_DIRECTIONAL_SUPPORT: weighted joint fit lost rank"
        )
    monopole = float(coefficients[0])
    dipole = coefficients[1:4]
    sxx, syy, sxy, sxz, syz = coefficients[4:]
    stf2 = np.asarray(
        ((sxx, sxy, sxz), (sxy, syy, syz), (sxz, syz, -sxx - syy)),
        dtype=float,
    )
    residual = float(np.linalg.norm(weighted_design @ coefficients - weighted_values))
    exact_mask_identity = _canonical_identity(
        {
            "declared_mask_identity": mask_identity,
            "active_rows": [bool(value) for value in active],
        },
        role="bound_directional_support_mask",
    )
    return _make_estimate(
        monopole=monopole,
        dipole=dipole,
        stf2=stf2,
        directions=selected_directions,
        values=selected_values,
        weights=selected_weights,
        field_parity=field_parity,
        field_quantity=field_quantity,
        field_units=field_units,
        field_bandlimit=field_bandlimit,
        estimator_kind=DirectionalEstimatorKind.WEIGHTED_JOINT_HARMONIC_FIT,
        direction_frame=direction_frame,
        direction_convention=direction_convention,
        mask_identity=exact_mask_identity,
        transfer_identity=transfer_identity,
        field_identity=field_identity,
        covariance_identity=covariance_identity,
        support_size=len(selected_values),
        design_rank=rank,
        design_condition=design_condition,
        residual=residual,
    )


def certify_antipodal_measure_moments(
    *,
    directions: Sequence[Sequence[float]],
    probability_weights: Sequence[float],
    support_identity: str,
) -> SphericalSecondMomentCertificate:
    """Bind the constructive antipodal zero-mean second-moment branch only."""

    direction_array, _, weights = _validated_samples(
        directions,
        np.zeros(len(directions), dtype=float),
        probability_weights,
    )
    if not math.isclose(float(weights.sum()), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY")
    for index, direction in enumerate(direction_array):
        matches = np.flatnonzero(
            np.linalg.norm(direction_array + direction, axis=1) <= _UNIT_ATOL
        )
        if not any(
            math.isclose(
                float(weights[index]),
                float(weights[match]),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for match in matches
        ):
            raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY")
    mean = np.einsum("n,ni->i", weights, direction_array)
    second = np.einsum("n,ni,nj->ij", weights, direction_array, direction_array)
    bound_support_identity = _canonical_identity(
        {
            "declared_support_identity": support_identity,
            "directions": _numeric_identity(direction_array, role="antipodal_directions"),
            "probabilities": _numeric_identity(weights, role="antipodal_probabilities"),
        },
        role="antipodal_measure_support",
    )
    return certify_spherical_second_moment(
        mean=mean,
        second_moment=second,
        support_identity=bound_support_identity,
    )


def adapt_directional_moments_to_observable_irrep_state(
    *,
    directional_moments: DirectionalMomentEstimate,
    parent_harmonic: ObservableIrrepBlock,
    projection_identity: str,
) -> ObservableIrrepState:
    """Adapt the measured STF2 only; retain the dipole in its legacy carrier.

    No registered retained-carrier representation exists here for ell=1, and
    the existing directional estimator is explicitly limited to ell<=2.
    Consequently this boundary refuses ell=3 instead of promoting content.
    """

    if type(directional_moments) is not DirectionalMomentEstimate:
        raise DirectionalBridgeError(
            "directional_moments must be an exact DirectionalMomentEstimate"
        )
    if type(parent_harmonic) is not ObservableIrrepBlock:
        raise DirectionalBridgeError(
            "parent_harmonic must be an exact ell=2 harmonic block"
        )
    if (
        parent_harmonic.ell != 2
        or parent_harmonic.representation
        is not ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_5
    ):
        raise DirectionalBridgeError(
            "directional adapter requires an ell=2 parent for STF2 only"
        )
    support = parent_harmonic.support
    if (
        support.frame != directional_moments.direction_frame
        or support.units != directional_moments.field_units
        or support.source_identity != directional_moments.field_identity
        or support.operator_identity != directional_moments.estimator_identity
    ):
        raise DirectionalBridgeError(
            "directional and harmonic frame/units/source/operator metadata mismatch"
        )
    raw = directional_moments.stf2
    block = build_cartesian_stf_irrep_block(
        parent=parent_harmonic,
        components=(raw[0][0], raw[1][1], raw[0][1], raw[0][2], raw[1][2]),
        basis="CARTESIAN_STF2_MATRIX_COMPONENTS_XX_YY_XY_XZ_YZ_V1",
        projection_identity=projection_identity,
    )
    return ObservableIrrepState(
        blocks=(block,),
        frame=block.support.frame,
        basis=block.support.basis,
        units=block.support.units,
        source_identity=block.support.source_identity,
        operator_identity=block.support.operator_identity,
        row_identity=block.support.row_identity,
    )


__all__ = [
    "adapt_directional_moments_to_observable_irrep_state",
    "certify_antipodal_measure_moments",
    "estimate_full_sky_directional_moments",
    "estimate_joint_fit_directional_moments",
]
