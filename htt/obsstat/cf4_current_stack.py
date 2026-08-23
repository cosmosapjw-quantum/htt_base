"""Current-stack CF4 affine-flow observable.

The operator fits exactly the radial projection of an isotropic affine trace,
a three-vector bulk flow, and a five-dimensional symmetric trace-free shear.
It consumes a full covariance
whose row order is bound to the catalogue, evaluates a predeclared finite set
of nuisance profiles, and abstains whenever either the nine-column affine
response or the eight-column flow response is weakly identified.

This module owns observable extraction only.  It emits neither a p-value nor a
local/global or Bianchi-family label.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np


COEFFICIENT_NAMES = (
    "isotropic_trace_over_3_km_s_mpc",
    "bulk_x_km_s",
    "bulk_y_km_s",
    "bulk_z_km_s",
    "shear_xx_km_s_mpc",
    "shear_yy_km_s_mpc",
    "shear_xy_km_s_mpc",
    "shear_xz_km_s_mpc",
    "shear_yz_km_s_mpc",
)


class Cf4CurrentStackError(ValueError):
    """Raised when the frozen CF4 operator contract fails closed."""


@dataclass(frozen=True)
class Cf4NuisanceProfile:
    """One admissible nuisance case, not a prior draw."""

    profile_id: str
    h0_km_s_mpc: float
    distance_scale: float
    covariance_scale: float

    def __post_init__(self) -> None:
        if not self.profile_id or not self.profile_id.isascii():
            raise Cf4CurrentStackError("nuisance profile id must be nonempty ASCII")
        for label, value in (
            ("H0", self.h0_km_s_mpc),
            ("distance scale", self.distance_scale),
            ("covariance scale", self.covariance_scale),
        ):
            if not np.isfinite(value) or value <= 0.0:
                raise Cf4CurrentStackError(f"{label} must be finite and positive")


@dataclass(frozen=True)
class Cf4OperatorConfig:
    depth_thresholds_mpc: tuple[float, ...]
    zoa_half_widths_deg: tuple[float, ...]
    nuisance_profiles: tuple[Cf4NuisanceProfile, ...]
    rank_relative_tolerance: float = 1.0e-10
    minimum_singular_value_ratio: float = 1.0e-6
    maximum_standardized_condition_number: float = 1.0e6

    def __post_init__(self) -> None:
        _strictly_increasing(self.depth_thresholds_mpc, "depth thresholds")
        _strictly_increasing(self.zoa_half_widths_deg, "ZoA half-widths")
        if any(value < 0.0 or value >= 90.0 for value in self.zoa_half_widths_deg):
            raise Cf4CurrentStackError("ZoA half-widths must lie in [0, 90)")
        if not self.nuisance_profiles:
            raise Cf4CurrentStackError("at least one nuisance profile is required")
        profile_ids = [profile.profile_id for profile in self.nuisance_profiles]
        if len(profile_ids) != len(set(profile_ids)):
            raise Cf4CurrentStackError("nuisance profiles must be unique")
        h0_values = {profile.h0_km_s_mpc for profile in self.nuisance_profiles}
        if len(h0_values) != 1:
            raise Cf4CurrentStackError(
                "H0 and distance scale may not be varied as independent nuisances"
            )
        if (
            not 0.0 < self.rank_relative_tolerance < 1.0
            or not 0.0 < self.minimum_singular_value_ratio <= 1.0
            or self.maximum_standardized_condition_number < 1.0
        ):
            raise Cf4CurrentStackError("rank thresholds are invalid")


@dataclass(frozen=True)
class Cf4OperatorInputs:
    group_ids: np.ndarray
    galactic_longitude_deg: np.ndarray
    galactic_latitude_deg: np.ndarray
    distance_mpc: np.ndarray
    cmb_velocity_km_s: np.ndarray
    covariance_km2_s2: np.ndarray
    covariance_group_ids: np.ndarray
    selected_group_ids: np.ndarray


def _strictly_increasing(values: Sequence[float], label: str) -> None:
    array = np.asarray(values, dtype=float)
    if (
        array.ndim != 1
        or len(array) == 0
        or not np.all(np.isfinite(array))
        or np.any(np.diff(array) <= 0.0)
    ):
        raise Cf4CurrentStackError(f"{label} must be strictly increasing")


def _canonical_hash(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def galactic_unit_vectors(
    longitude_deg: np.ndarray, latitude_deg: np.ndarray
) -> np.ndarray:
    longitude = np.radians(np.asarray(longitude_deg, dtype=float))
    latitude = np.radians(np.asarray(latitude_deg, dtype=float))
    if longitude.ndim != 1 or latitude.shape != longitude.shape:
        raise Cf4CurrentStackError("Galactic longitude/latitude shape mismatch")
    if (
        not np.all(np.isfinite(longitude))
        or not np.all(np.isfinite(latitude))
        or np.any(latitude < -np.pi / 2.0)
        or np.any(latitude > np.pi / 2.0)
    ):
        raise Cf4CurrentStackError("invalid Galactic coordinates")
    cosine = np.cos(latitude)
    return np.column_stack(
        (cosine * np.cos(longitude), cosine * np.sin(longitude), np.sin(latitude))
    )


def build_cf4_affine_design(
    directions: np.ndarray, distance_mpc: np.ndarray
) -> np.ndarray:
    """Build the exact ``trace/3 + 3 B + 5 S_STF`` radial design."""

    direction = np.asarray(directions, dtype=float)
    distance = np.asarray(distance_mpc, dtype=float)
    if direction.ndim != 2 or direction.shape[1] != 3:
        raise Cf4CurrentStackError("directions must have shape (N, 3)")
    if distance.shape != (len(direction),):
        raise Cf4CurrentStackError("distance shape mismatch")
    if (
        not np.all(np.isfinite(direction))
        or not np.all(np.isfinite(distance))
        or np.any(distance <= 0.0)
        or np.max(np.abs(np.linalg.norm(direction, axis=1) - 1.0)) > 1.0e-10
    ):
        raise Cf4CurrentStackError("affine design inputs are invalid")
    nx, ny, nz = direction.T
    return np.column_stack(
        (
            distance,
            nx,
            ny,
            nz,
            distance * (nx * nx - nz * nz),
            distance * (ny * ny - nz * nz),
            2.0 * distance * nx * ny,
            2.0 * distance * nx * nz,
            2.0 * distance * ny * nz,
        )
    )


def _validated_arrays(inputs: Cf4OperatorInputs) -> dict[str, np.ndarray]:
    ids = np.asarray(inputs.group_ids)
    covariance_ids = np.asarray(inputs.covariance_group_ids)
    selected_ids = np.asarray(inputs.selected_group_ids)
    if ids.ndim != 1 or len(ids) < 1 or len(np.unique(ids)) != len(ids):
        raise Cf4CurrentStackError("catalogue group ids must be unique")
    if covariance_ids.shape != ids.shape or not np.array_equal(covariance_ids, ids):
        raise Cf4CurrentStackError("covariance row order does not equal catalogue order")
    if selected_ids.ndim != 1 or len(np.unique(selected_ids)) != len(selected_ids):
        raise Cf4CurrentStackError("selected group ids must be unique")
    if not set(selected_ids.tolist()) <= set(ids.tolist()):
        raise Cf4CurrentStackError("row selection references an unknown group")
    vectors = {
        "longitude": np.asarray(inputs.galactic_longitude_deg, dtype=float),
        "latitude": np.asarray(inputs.galactic_latitude_deg, dtype=float),
        "distance": np.asarray(inputs.distance_mpc, dtype=float),
        "vcmb": np.asarray(inputs.cmb_velocity_km_s, dtype=float),
    }
    if any(value.shape != ids.shape for value in vectors.values()):
        raise Cf4CurrentStackError("catalogue column shape mismatch")
    if not all(np.all(np.isfinite(value)) for value in vectors.values()):
        raise Cf4CurrentStackError("catalogue contains non-finite values")
    if np.any(vectors["distance"] <= 0.0):
        raise Cf4CurrentStackError("catalogue distances must be positive")
    covariance = np.asarray(inputs.covariance_km2_s2, dtype=float)
    if covariance.shape != (len(ids), len(ids)):
        raise Cf4CurrentStackError("full covariance shape mismatch")
    if not np.all(np.isfinite(covariance)):
        raise Cf4CurrentStackError("full covariance contains non-finite values")
    if not np.allclose(covariance, covariance.T, rtol=1.0e-12, atol=1.0e-9):
        raise Cf4CurrentStackError("full covariance is asymmetric")
    off_diagonal = covariance - np.diag(np.diag(covariance))
    if not np.any(np.abs(off_diagonal) > 0.0):
        raise Cf4CurrentStackError("full covariance must contain off-diagonal terms")
    try:
        np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as exc:
        raise Cf4CurrentStackError(
            "full covariance must be positive definite without jitter repair"
        ) from exc
    return {
        "ids": ids,
        "selected_ids": selected_ids,
        "covariance": covariance,
        **vectors,
    }


def _rank_diagnostics(
    whitened: np.ndarray, config: Cf4OperatorConfig
) -> tuple[int, float, float | None, bool]:
    norms = np.linalg.norm(whitened, axis=0)
    if np.any(norms <= 0.0):
        return 0, 0.0, None, False
    singular = np.linalg.svd(whitened / norms, compute_uv=False)
    if len(singular) == 0 or singular[0] <= 0.0:
        return 0, 0.0, None, False
    rank = int(np.sum(singular > config.rank_relative_tolerance * singular[0]))
    ratio = float(singular[-1] / singular[0])
    condition = float(1.0 / ratio) if ratio > 0.0 else None
    pass_floor = (
        ratio >= config.minimum_singular_value_ratio
        and condition is not None
        and condition <= config.maximum_standardized_condition_number
    )
    return rank, ratio, condition, pass_floor


def _trace_only_membership(
    whitened_design: np.ndarray, whitened_response: np.ndarray
) -> tuple[bool, float, float]:
    """Test numerical membership in the exact isotropic-trace subspace."""

    trace = whitened_design[:, 0]
    denominator = float(trace @ trace)
    coefficient = float(trace @ whitened_response) / denominator
    residual_norm = float(
        np.linalg.norm(whitened_response - coefficient * trace)
    )
    scale = max(
        float(np.linalg.norm(whitened_response)),
        float(np.linalg.norm(coefficient * trace)),
        1.0,
    )
    tolerance = (
        64.0
        * np.finfo(float).eps
        * max(len(whitened_response), 1)
        * scale
    )
    return bool(residual_norm <= tolerance), residual_norm, float(tolerance)


def _fit_profile(
    *,
    directions: np.ndarray,
    base_distance: np.ndarray,
    vcmb: np.ndarray,
    covariance: np.ndarray,
    profile: Cf4NuisanceProfile,
    config: Cf4OperatorConfig,
) -> dict[str, object]:
    distance = base_distance * profile.distance_scale
    response = vcmb - profile.h0_km_s_mpc * distance
    design = build_cf4_affine_design(directions, distance)
    scaled_covariance = covariance * profile.covariance_scale**2
    try:
        cholesky = np.linalg.cholesky(scaled_covariance)
    except np.linalg.LinAlgError:
        return {
            "profile_id": profile.profile_id,
            "disposition": "COVARIANCE_INVALID_ABSTAIN",
            "coefficients": None,
            "coefficient_covariance": None,
            "diagnostics": {
                "affine_rank": 0,
                "affine_columns": 9,
                "projected_flow_rank": 0,
                "projected_flow_columns": 8,
            },
        }
    whitened_design = np.linalg.solve(cholesky, design)
    rank, ratio, condition, affine_floor = _rank_diagnostics(
        whitened_design, config
    )
    trace = whitened_design[:, :1]
    flow = whitened_design[:, 1:]
    if np.linalg.norm(trace) > 0.0:
        flow = flow - trace @ (
            np.linalg.solve(trace.T @ trace, trace.T @ flow)
        )
    flow_rank, flow_ratio, flow_condition, flow_floor = _rank_diagnostics(
        flow, config
    )
    diagnostics = {
        "affine_rank": rank,
        "affine_columns": 9,
        "affine_singular_value_ratio": ratio,
        "affine_standardized_condition_number": condition,
        "projected_flow_rank": flow_rank,
        "projected_flow_columns": 8,
        "projected_flow_singular_value_ratio": flow_ratio,
        "projected_flow_standardized_condition_number": flow_condition,
    }
    if rank < 9 or flow_rank < 8:
        return {
            "profile_id": profile.profile_id,
            "disposition": "RANK_DEFICIENT_ABSTAIN",
            "coefficients": None,
            "coefficient_covariance": None,
            "diagnostics": diagnostics,
        }
    if not affine_floor or not flow_floor:
        return {
            "profile_id": profile.profile_id,
            "disposition": "WEAK_ID_ABSTAIN",
            "coefficients": None,
            "coefficient_covariance": None,
            "diagnostics": diagnostics,
        }
    whitened_response = np.linalg.solve(cholesky, response)
    no_flow_member, no_flow_residual, no_flow_tolerance = _trace_only_membership(
        whitened_design, whitened_response
    )
    diagnostics.update(
        {
            "trace_only_residual_norm": no_flow_residual,
            "trace_only_numerical_tolerance": no_flow_tolerance,
        }
    )
    normal = whitened_design.T @ whitened_design
    coefficient_covariance = np.linalg.inv(normal)
    coefficients = coefficient_covariance @ (
        whitened_design.T @ whitened_response
    )
    return {
        "profile_id": profile.profile_id,
        "disposition": "IDENTIFIED_SET_MEMBER",
        "coefficients": coefficients.tolist(),
        "coefficient_covariance": coefficient_covariance.tolist(),
        "no_flow_member": no_flow_member,
        "diagnostics": diagnostics,
    }


def analyze_cf4_current_stack(
    inputs: Cf4OperatorInputs,
    config: Cf4OperatorConfig,
    *,
    observed: bool = False,
) -> dict[str, object]:
    """Evaluate the frozen depth-by-ZoA path with typed abstention."""

    arrays = _validated_arrays(inputs)
    ids = arrays["ids"]
    selected = np.isin(ids, arrays["selected_ids"])
    directions = galactic_unit_vectors(arrays["longitude"], arrays["latitude"])
    cells: list[dict[str, object]] = []
    dispositions: list[str] = []
    previous_by_zoa: dict[tuple[str, float], set[object]] = {}
    previous_by_depth: dict[tuple[str, float], set[object]] = {}
    for depth in config.depth_thresholds_mpc:
        for zoa in config.zoa_half_widths_deg:
            profiles: list[dict[str, object]] = []
            row_counts: dict[str, int] = {}
            row_hashes: dict[str, str] = {}
            for profile in config.nuisance_profiles:
                profile_distance = arrays["distance"] * profile.distance_scale
                mask = selected & (profile_distance <= depth) & (
                    np.abs(arrays["latitude"]) >= zoa
                )
                cell_ids = ids[mask]
                current = set(cell_ids.tolist())
                depth_key = (profile.profile_id, zoa)
                zoa_key = (profile.profile_id, depth)
                if (
                    depth_key in previous_by_zoa
                    and not previous_by_zoa[depth_key] <= current
                ):
                    raise Cf4CurrentStackError("depth masks are not nested")
                if (
                    zoa_key in previous_by_depth
                    and not current <= previous_by_depth[zoa_key]
                ):
                    raise Cf4CurrentStackError("ZoA masks are not reverse-nested")
                previous_by_zoa[depth_key] = current
                previous_by_depth[zoa_key] = current
                row_counts[profile.profile_id] = int(mask.sum())
                row_hashes[profile.profile_id] = _canonical_hash(cell_ids.tolist())
                if len(cell_ids) < 9:
                    profiles.append({
                        "profile_id": profile.profile_id,
                        "disposition": "RANK_DEFICIENT_ABSTAIN",
                        "coefficients": None,
                        "coefficient_covariance": None,
                        "diagnostics": {
                            "affine_rank": min(len(cell_ids), 8),
                            "affine_columns": 9,
                            "projected_flow_rank": min(len(cell_ids), 7),
                            "projected_flow_columns": 8,
                        },
                    })
                    continue
                sliced_covariance = arrays["covariance"][np.ix_(mask, mask)]
                profiles.append(
                    _fit_profile(
                        directions=directions[mask],
                        base_distance=arrays["distance"][mask],
                        vcmb=arrays["vcmb"][mask],
                        covariance=sliced_covariance,
                        profile=profile,
                        config=config,
                    )
                )
            dispositions.extend(str(profile["disposition"]) for profile in profiles)
            member_profiles = [
                profile
                for profile in profiles
                if profile["coefficients"] is not None
            ]
            members = [profile["coefficients"][1:] for profile in member_profiles]
            identified_set: Mapping[str, object]
            if len(members) == len(config.nuisance_profiles):
                member_array = np.asarray(members, dtype=float)
                contains_exact_no_flow = any(
                    profile["no_flow_member"] is True
                    for profile in member_profiles
                )
                identified_set = {
                    "status": "BOUNDED_DIAGNOSTIC_SET",
                    "profile_ids": [
                        profile.profile_id for profile in config.nuisance_profiles
                    ],
                    "joint_flow_members": member_array.tolist(),
                    "componentwise_projection_bounds": np.column_stack(
                        (member_array.min(axis=0), member_array.max(axis=0))
                    ).tolist(),
                    "no_flow_calibration_status": (
                        "EXACT_NO_FLOW_MEMBER_ABSTAIN"
                        if contains_exact_no_flow
                        else "UNAVAILABLE_ABSTAIN"
                    ),
                    "source_response_status": "UNAVAILABLE_ABSTAIN",
                }
            else:
                identified_set = {
                    "status": "UNBOUNDED_OR_UNDETERMINED_ABSTAIN",
                    "profile_ids": [
                        profile.profile_id for profile in config.nuisance_profiles
                    ],
                    "joint_flow_members": [],
                    "componentwise_projection_bounds": None,
                    "no_flow_calibration_status": "UNAVAILABLE_ABSTAIN",
                    "source_response_status": "UNAVAILABLE_ABSTAIN",
                }
            cells.append(
                {
                    "cell_id": f"depth={depth:g}|zoa={zoa:g}",
                    "depth_threshold_mpc": float(depth),
                    "zoa_half_width_deg": float(zoa),
                    "row_count": min(row_counts.values()),
                    "row_counts_by_profile": row_counts,
                    "ordered_group_ids_sha256_by_profile": row_hashes,
                    "profiles": profiles,
                    "identified_set": identified_set,
                }
            )
    if "RANK_DEFICIENT_ABSTAIN" in dispositions:
        terminal = "RANK_DEFICIENT_ABSTAIN"
    elif "WEAK_ID_ABSTAIN" in dispositions:
        terminal = "WEAK_ID_ABSTAIN"
    elif any(value != "IDENTIFIED_SET_MEMBER" for value in dispositions):
        terminal = "UNDETERMINED_ABSTAIN"
    elif any(
        cell["identified_set"]["no_flow_calibration_status"]
        == "EXACT_NO_FLOW_MEMBER_ABSTAIN"
        for cell in cells
    ):
        terminal = "EXACT_NO_FLOW_MEMBER_ABSTAIN"
    elif any(
        cell["identified_set"]["no_flow_calibration_status"]
        == "UNAVAILABLE_ABSTAIN"
        for cell in cells
    ):
        terminal = "NO_FLOW_CALIBRATION_UNAVAILABLE_ABSTAIN"
    else:
        terminal = "IDENTIFIED_SET_DIAGNOSTIC"
    contract = {
        "basis": "TRACE_OVER_3_PLUS_3B_PLUS_5_STF",
        "coefficient_count": 9,
        "coefficient_names": list(COEFFICIENT_NAMES),
        "coefficient_units": [
            "km s-1 Mpc-1",
            "km s-1",
            "km s-1",
            "km s-1",
            "km s-1 Mpc-1",
            "km s-1 Mpc-1",
            "km s-1 Mpc-1",
            "km s-1 Mpc-1",
            "km s-1 Mpc-1",
        ],
        "isotropic_trace_convention": "coefficient_equals_trace_over_3",
        "frame": "GALACTIC",
        "positive_velocity": "RECEDING",
        "distance_units": "Mpc",
        "velocity_units": "km s-1",
        "covariance_units": "(km s-1)^2",
        "depth_thresholds_mpc": list(config.depth_thresholds_mpc),
        "zoa_half_widths_deg": list(config.zoa_half_widths_deg),
        "nuisance_profiles": [profile.__dict__ for profile in config.nuisance_profiles],
        "rank_relative_tolerance": config.rank_relative_tolerance,
        "minimum_singular_value_ratio": config.minimum_singular_value_ratio,
        "maximum_standardized_condition_number": (
            config.maximum_standardized_condition_number
        ),
        "same_operator_for_observation_and_null": True,
    }
    return {
        "operator_contract": contract,
        "operator_identity": _canonical_hash(contract),
        "cells": cells,
        "terminal_disposition": terminal,
        "claim_tier_ceiling": "C3_DEPTH_DIRECTION_DIAGNOSTIC",
        "family_identification": "FORBIDDEN",
        "observed_statistic_seen": bool(observed),
        "observed_science_executed": bool(observed),
    }
