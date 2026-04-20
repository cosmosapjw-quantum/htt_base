"""VER2 sparse covariance and BiPoSH-proxy shells."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from bass.spectrum.off_diagonal_covariance import (
    build_sparse_covariance_entries,
    compute_covariance_psd_guard,
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


def build_sparse_covariance_proxy(
    covariance_bundle: Mapping[str, object],
    *,
    harmonic_convention: str,
    threshold: float = 0.0,
) -> dict[str, object]:
    """Return a manifest-friendly sparse proxy for off-diagonal morphology."""
    entries = build_sparse_covariance_entries(covariance_bundle, threshold=threshold)
    unique_index_count = sum(len(rows) for rows in entries.values())
    representation = "biposh_sparse"
    sample = next((rows[0] for rows in entries.values() if rows), None)
    caveats: list[str] = []
    if sample is None or "mode" in sample:
        representation = "sparse_mode_block_proxy"
        caveats.append("mode_block_proxy_not_full_biposh")
    return {
        "representation": representation,
        "harmonic_convention": harmonic_convention,
        "entries": entries,
        "unique_index_count": unique_index_count,
        "frobenius_offdiag_norms": {
            spec: _frobenius_norm(rows) for spec, rows in entries.items()
        },
        "caveats": tuple(caveats),
    }


def build_covariance_feature_summary(
    covariance_bundle: Mapping[str, object],
    *,
    harmonic_convention: str,
    threshold: float = 0.0,
    psd_tolerance: float = 1.0e-12,
) -> dict[str, object]:
    """Return guard metadata for covariance-aware observable shells."""
    sparse = build_sparse_covariance_proxy(
        covariance_bundle,
        harmonic_convention=harmonic_convention,
        threshold=threshold,
    )
    anisotropy_tensor = covariance_bundle.get("anisotropy_tensor")
    trace_free = None
    if anisotropy_tensor is not None:
        tensor = np.asarray(anisotropy_tensor, dtype=float)
        trace_free = bool(abs(float(np.trace(tensor))) <= 1.0e-12)
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
        "caveats": tuple(sparse["caveats"]),
    }
