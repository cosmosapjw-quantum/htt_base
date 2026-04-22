"""VER2 sparse covariance and BiPoSH-proxy shells."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from bass.spectrum.off_diagonal_covariance import (
    build_dense_harmonic_covariance,
    build_sparse_covariance_entries,
    build_sparse_harmonic_entries,
    compute_covariance_invariant_guard,
    compute_covariance_psd_guard,
    compute_covariance_symmetry_guard,
)

__all__ = [
    "build_covariance_feature_summary",
    "build_sparse_covariance_proxy",
]


def _frobenius_norm(entries: list[dict[str, object]]) -> float:
    if not entries:
        return 0.0
    values = np.asarray([float(item["value"]) for item in entries], dtype=float)
    return float(np.linalg.norm(values))


def _local_global_degeneracy(
    covariance_bundle: Mapping[str, object],
    *,
    unique_index_count: int,
) -> dict[str, object]:
    offdiag_strength = float(covariance_bundle.get("offdiag_strength", 0.0))
    rotation_strength = float(covariance_bundle.get("rotation_strength", 0.0))
    preferred_axis_present = covariance_bundle.get("preferred_axis") is not None
    if unique_index_count == 0 and offdiag_strength == 0.0 and rotation_strength == 0.0:
        status = "not_applicable_isotropic"
        distinguishing_observables: tuple[str, ...] = ()
    else:
        status = "observer_source_discrimination_pending"
        distinguishing_observables = ("BiPoSH", "BB", "template")
    return {
        "represented": True,
        "status": status,
        "preferred_axis_present": preferred_axis_present,
        "offdiag_strength": offdiag_strength,
        "rotation_strength": rotation_strength,
        "distinguishing_observables": distinguishing_observables,
        "required_followup": (
            "atlas_response_overlap",
            "htt_discrimination_matrix",
        ),
    }


def _angular_reconstruction_guard(
    angular_payload: Mapping[str, object] | None,
    *,
    ell_max: int,
) -> dict[str, object]:
    if angular_payload is None:
        return {
            "available": False,
            "passed": False,
            "reason": "missing_angular_payload",
            "quadrature_points": None,
            "quadrature_rule": None,
            "coefficient_representation": None,
        }
    directions = angular_payload.get("sphere_directions")
    weights = angular_payload.get("sphere_weights")
    samples = angular_payload.get("sphere_samples")
    values = angular_payload.get("values")
    if directions is None or weights is None or samples is None or values is None:
        return {
            "available": True,
            "passed": False,
            "reason": "incomplete_reconstruction_payload",
            "quadrature_points": None,
            "quadrature_rule": angular_payload.get("quadrature_rule"),
            "coefficient_representation": angular_payload.get("coefficient_representation"),
        }
    dirs = np.asarray(directions, dtype=float)
    wts = np.asarray(weights, dtype=float)
    sample_arr = np.asarray(samples, dtype=float)
    coeff_arr = np.asarray(values, dtype=float)
    expected_coeff_size = (int(ell_max) + 1) ** 2
    passed = (
        dirs.ndim == 2
        and dirs.shape[1] == 3
        and wts.shape == (dirs.shape[0],)
        and sample_arr.shape == (dirs.shape[0],)
        and coeff_arr.shape == (expected_coeff_size,)
        and np.all(np.isfinite(dirs))
        and np.all(np.isfinite(wts))
        and np.all(np.isfinite(sample_arr))
        and np.all(np.isfinite(coeff_arr))
    )
    return {
        "available": True,
        "passed": bool(passed),
        "reason": "ok" if passed else "shape_or_finiteness_mismatch",
        "quadrature_points": int(dirs.shape[0]),
        "quadrature_rule": angular_payload.get("quadrature_rule"),
        "coefficient_representation": angular_payload.get("coefficient_representation"),
    }


def build_sparse_covariance_proxy(
    covariance_bundle: Mapping[str, object],
    *,
    harmonic_convention: str,
    threshold: float = 0.0,
    angular_payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return a manifest-friendly sparse proxy for off-diagonal morphology."""
    ell = np.asarray(covariance_bundle.get("ell", ()), dtype=int)
    ell_max = int(ell[-1]) if ell.size else 0
    angular_guard = _angular_reconstruction_guard(
        angular_payload,
        ell_max=ell_max,
    )
    if angular_guard["passed"]:
        entries = build_sparse_harmonic_entries(covariance_bundle, threshold=threshold)
        representation = "low_ell_harmonic_sparse_basis"
        caveats: list[str] = ["basis_reduced_not_full_biposh"]
    else:
        entries = build_sparse_covariance_entries(covariance_bundle, threshold=threshold)
        representation = "biposh_sparse"
        sample = next((rows[0] for rows in entries.values() if rows), None)
        caveats = []
        if sample is None or "mode" in sample:
            representation = "sparse_mode_block_proxy"
            caveats.append("mode_block_proxy_not_full_biposh")
    null_proxy_status = (
        "consistent_with_isotropic_null"
        if sum(len(rows) for rows in entries.values()) == 0
        and float(covariance_bundle.get("offdiag_strength", 0.0)) == 0.0
        and float(covariance_bundle.get("rotation_strength", 0.0)) == 0.0
        else "anisotropic_or_unresolved"
    )
    unique_index_count = sum(len(rows) for rows in entries.values())
    return {
        "representation": representation,
        "harmonic_convention": harmonic_convention,
        "entries": entries,
        "unique_index_count": unique_index_count,
        "frobenius_offdiag_norms": {
            spec: _frobenius_norm(rows) for spec, rows in entries.items()
        },
        "supports_full_biposh": representation == "biposh_sparse",
        "supports_basis_reduced_morphology": representation == "low_ell_harmonic_sparse_basis",
        "basis_reduction_status": (
            "sphere_supported_harmonic_sparse"
            if representation == "low_ell_harmonic_sparse_basis"
            else "mode_proxy_only"
        ),
        "angular_reconstruction_guard": angular_guard,
        "null_proxy_status": null_proxy_status,
        "caveats": tuple(caveats),
    }


def build_covariance_feature_summary(
    covariance_bundle: Mapping[str, object],
    *,
    harmonic_convention: str,
    threshold: float = 0.0,
    psd_tolerance: float = 1.0e-12,
    angular_payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return guard metadata for covariance-aware observable shells."""
    sparse = build_sparse_covariance_proxy(
        covariance_bundle,
        harmonic_convention=harmonic_convention,
        threshold=threshold,
        angular_payload=angular_payload,
    )
    dense_harmonic = None
    if bool(sparse["angular_reconstruction_guard"]["passed"]):
        dense_harmonic = build_dense_harmonic_covariance(
            covariance_bundle,
            threshold=threshold,
        )
    anisotropy_tensor = covariance_bundle.get("anisotropy_tensor")
    trace_free = None
    if anisotropy_tensor is not None:
        tensor = np.asarray(anisotropy_tensor, dtype=float)
        trace_free = bool(abs(float(np.trace(tensor))) <= 1.0e-12)
    symmetry_guard = compute_covariance_symmetry_guard(
        covariance_bundle,
        atol=psd_tolerance,
    )
    invariant_guard = compute_covariance_invariant_guard(
        covariance_bundle,
        atol=psd_tolerance,
    )
    harmonic_gaussian_ready = bool(
        dense_harmonic is not None
        and compute_covariance_psd_guard(
            covariance_bundle,
            atol=psd_tolerance,
        )["passed"]
        and symmetry_guard["passed"]
        and invariant_guard["passed"]
    )
    return {
        "representation": sparse["representation"],
        "harmonic_convention": harmonic_convention,
        "sparse_index_count": sparse["unique_index_count"],
        "frobenius_offdiag_norms": dict(sparse["frobenius_offdiag_norms"]),
        "psd_guard": compute_covariance_psd_guard(
            covariance_bundle,
            atol=psd_tolerance,
        ),
        "structure_label": covariance_bundle.get("structure_label", "unknown"),
        "offdiag_strength": float(covariance_bundle.get("offdiag_strength", 0.0)),
        "rotation_strength": float(covariance_bundle.get("rotation_strength", 0.0)),
        "anisotropy_tensor_tracefree": trace_free,
        "supports_full_biposh": bool(sparse["supports_full_biposh"]),
        "supports_basis_reduced_morphology": bool(sparse["supports_basis_reduced_morphology"]),
        "supports_harmonic_gaussian": harmonic_gaussian_ready,
        "harmonic_gaussian_covariance": dense_harmonic,
        "basis_reduction_status": str(sparse["basis_reduction_status"]),
        "angular_reconstruction_guard": dict(sparse["angular_reconstruction_guard"]),
        "null_proxy_status": str(sparse["null_proxy_status"]),
        "symmetry_guard": symmetry_guard,
        "invariant_guard": invariant_guard,
        "local_global_degeneracy": _local_global_degeneracy(
            covariance_bundle,
            unique_index_count=int(sparse["unique_index_count"]),
        ),
        "caveats": tuple(sparse["caveats"]),
    }
