"""PR13AH: observables reintegration with 4-way summary separation.

Scope (HTT-P0-AH, INDEPENDENT_TRACKS_PLAN.md §2.4, plus AUDIT_PHASE_IND_TRACKS_W1W2 R1):
-----------------------------------------------------------------------------------------
Splits ``reintegrate_observables`` into four disjoint summary channels:

  1. ``raw_summary``                 — diagnostic_only
  2. ``zoa_masked_summary``          — diagnostic_only
  3. ``selection_aware_summary``     — Mode 1 baseline
  4. ``mock_calibrated_summary``     — Mode 2 fiducial (COMMON-F gated)

The three geometric channels use the sphere-correct resultant-vector mean
from ``common.sky_geometry.spherical_mean`` (COMMON-A, which ships in the
same commit set). The ``mock_calibrated_summary`` slot still carries
``calibration_pending=True`` until COMMON-F lands the bias-correction backend;
downstream consumers must read per-channel metadata rather than assuming any
equivalence between the four channels.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from common.sky_geometry import spherical_mean as _spherical_mean


@dataclass(frozen=True)
class ChannelSummary:
    """Per-channel direction summary with provenance metadata."""

    l_deg: float
    b_deg: float
    resultant_R: float
    source: str                         # 'raw' | 'zoa_masked' | 'selection_aware' | 'mock_calibrated'
    selection_mode: str                 # 'none' | 'zoa_hard_cut' | 'angular_completeness' | 'mock_calibrated'
    diagnostic_only: bool
    calibration_pending: bool = False   # flipped False once COMMON-F lands
    meta: Mapping[str, Any] = field(default_factory=dict)


def _sphere_mean_tuple(l: np.ndarray, b: np.ndarray, w: np.ndarray) -> tuple[float, float, float]:
    """Thin tuple wrapper around ``common.sky_geometry.spherical_mean``."""
    res = _spherical_mean(l, b, w)
    return res["l_deg"], res["b_deg"], res["resultant_R"]


def _zoa_mask(b_deg: np.ndarray, half_angle_deg: float) -> np.ndarray:
    return np.abs(b_deg) >= float(half_angle_deg)


def reintegrate_observables(catalog: Mapping[str, np.ndarray],
                            sky_config: Mapping[str, Any]) -> dict[str, ChannelSummary]:
    """Produce the four-summary bundle.

    Parameters
    ----------
    catalog : mapping with keys ``'l'``, ``'b'``, ``'w'`` (numpy arrays).
    sky_config : mapping providing at least ``'zoa_half_angle_deg'``.

    Returns
    -------
    dict with keys ``raw_summary``, ``zoa_masked_summary``,
    ``selection_aware_summary``, ``mock_calibrated_summary``, each a
    ``ChannelSummary``.
    """
    l = np.asarray(catalog["l"], dtype=float)
    b = np.asarray(catalog["b"], dtype=float)
    w = np.asarray(catalog["w"], dtype=float)

    half_angle = float(sky_config["zoa_half_angle_deg"])

    l_raw, b_raw, R_raw = _sphere_mean_tuple(l, b, np.ones_like(l))
    raw_summary = ChannelSummary(
        l_deg=l_raw, b_deg=b_raw, resultant_R=R_raw,
        source="raw", selection_mode="none", diagnostic_only=True,
        meta={"n_sources": int(l.size)},
    )

    mask = _zoa_mask(b, half_angle)
    if mask.any():
        l_z, b_z, R_z = _sphere_mean_tuple(l[mask], b[mask], w[mask])
        zoa_summary = ChannelSummary(
            l_deg=l_z, b_deg=b_z, resultant_R=R_z,
            source="zoa_masked", selection_mode="zoa_hard_cut",
            diagnostic_only=True,
            meta={"n_sources": int(mask.sum()),
                  "zoa_half_angle_deg": half_angle},
        )
    else:
        zoa_summary = ChannelSummary(
            l_deg=float("nan"), b_deg=float("nan"), resultant_R=0.0,
            source="zoa_masked", selection_mode="zoa_hard_cut",
            diagnostic_only=True,
            meta={"n_sources": 0, "zoa_half_angle_deg": half_angle,
                  "empty": True},
        )

    # Selection-aware: until COMMON-B's healpix_selection lands, reuse the
    # zoa_masked sample set with the catalogue weights (no completeness map
    # applied yet). This is the Mode-1 structural slot, not the final value.
    if mask.any():
        l_s, b_s, R_s = _sphere_mean_tuple(l[mask], b[mask], w[mask])
        selection_summary = ChannelSummary(
            l_deg=l_s, b_deg=b_s, resultant_R=R_s,
            source="selection_aware", selection_mode="angular_completeness",
            diagnostic_only=False,
            meta={"n_sources": int(mask.sum()),
                  "completeness_pending": True},
        )
    else:
        selection_summary = ChannelSummary(
            l_deg=float("nan"), b_deg=float("nan"), resultant_R=0.0,
            source="selection_aware", selection_mode="angular_completeness",
            diagnostic_only=False,
            meta={"n_sources": 0, "empty": True,
                  "completeness_pending": True},
        )

    # Mock-calibrated: COMMON-F will supply the bias-correction backend.
    # For now we deep-clone the selection-aware result but tag it explicitly
    # so downstream cannot mistake the placeholder for a calibrated value.
    mock_summary = ChannelSummary(
        l_deg=selection_summary.l_deg,
        b_deg=selection_summary.b_deg,
        resultant_R=selection_summary.resultant_R,
        source="mock_calibrated",
        selection_mode="mock_calibrated",
        diagnostic_only=False,
        calibration_pending=True,
        meta={**dict(selection_summary.meta),
              "note": "COMMON-F not yet landed; duplicate of selection-aware"},
    )

    return {
        "raw_summary": raw_summary,
        "zoa_masked_summary": zoa_summary,
        "selection_aware_summary": selection_summary,
        "mock_calibrated_summary": mock_summary,
    }
