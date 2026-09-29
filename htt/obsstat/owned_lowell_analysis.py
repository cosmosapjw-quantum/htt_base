"""Strict NSIDE16 temperature low-ell diagnostics for owner-held maps."""
from __future__ import annotations

from typing import Any

import numpy as np


def analyze_nside16_map(
    data: np.ndarray,
    mask: np.ndarray,
    *,
    dataset_id: str,
    units: str,
    ordering: str,
    frame: str,
) -> dict[str, Any]:
    import healpy as hp

    array = np.asarray(data, dtype=float)
    if array.ndim == 1:
        temperature, polarization_status = array, "UNAVAILABLE_NO_Q_U"
    elif array.ndim == 2 and array.shape[0] in {1, 3}:
        temperature = array[0]
        polarization_status = "PRESENT_NOT_ANALYZED_SPIN_CONVENTION_UNBOUND" if array.shape[0] == 3 else "UNAVAILABLE_NO_Q_U"
    else:
        raise ValueError("map must be I or ordered I/Q/U rows")
    expected = hp.nside2npix(16)
    keep = np.asarray(mask, dtype=float)
    if temperature.shape != (expected,) or keep.shape != (expected,):
        raise ValueError("DATA-03 requires map and mask at NSIDE16")
    if units not in {"uK_CMB", "uK"} or ordering != "RING" or frame.upper() not in {"G", "GALACTIC"}:
        raise ValueError("explicit uK thermodynamic, RING, Galactic contract required")
    if not np.isfinite(temperature).all() or not np.isfinite(keep).all() or np.any((keep < 0) | (keep > 1)):
        raise ValueError("map/mask must be finite and mask-valued in [0,1]")
    support = keep > 0
    if support.sum() < 36:
        raise ValueError("insufficient supported pixels for ell0..5 fit")
    vectors = np.asarray(hp.pix2vec(16, np.arange(expected))).T
    design = np.column_stack([np.ones(expected), vectors])
    coefficients, _, rank, _ = np.linalg.lstsq(design[support], temperature[support], rcond=None)
    if rank != 4:
        raise ValueError("monopole/dipole support is rank deficient")
    cleaned = temperature - design @ coefficients
    weighted = cleaned * keep
    alm = hp.map2alm(weighted, lmax=5, iter=3)
    carrier: list[float] = []
    by_ell: dict[str, list[float]] = {}
    for ell in range(2, 6):
        block = [float(np.real(alm[hp.Alm.getidx(5, ell, 0)]))]
        for m in range(1, ell + 1):
            value = alm[hp.Alm.getidx(5, ell, m)]
            block.extend([float(np.real(value)), float(np.imag(value))])
        by_ell[str(ell)] = block
        carrier.extend(block)
    return {
        "schema": "htt.owned_lowell_analysis/v1",
        "dataset_id": dataset_id,
        "nside": 16,
        "ordering": ordering,
        "frame": "GALACTIC",
        "units": units,
        "mask_kind": "binary" if np.all((keep == 0) | (keep == 1)) else "apodized",
        "supported_pixels": int(support.sum()),
        "monopole_dipole_fit": coefficients.tolist(),
        "carrier_layout": "ell2..5:m0_real_then_m1..mell_real_imag",
        "carrier_components": carrier,
        "carrier_dimension": len(carrier),
        "by_ell": by_ell,
        "polarization_status": polarization_status,
        "null_law": "UNAVAILABLE",
        "p_value": None,
        "same_sky_independence": "NOT_ASSUMED",
        "claim_ceiling": "descriptive morphology only",
    }
