"""common.sky_geometry — unit-vector sphere utilities (COMMON-A §6.6).

Five public utilities:

* ``lb_to_unitvec`` / ``unitvec_to_lb`` — Galactic ↔ Cartesian.
* ``spherical_mean``                    — resultant-vector mean of (l, b, w).
* ``angular_separation_matrix``        — pairwise separations (degrees).
* ``galactic_plane_mask``              — ZoA hard cut.
* ``normalize_weights``                — §6.6 helper with production gate.

The naive arithmetic mean of longitude fails at the 0°/360° wrap; the
unit-vector mean is the standard sphere-correct replacement.
"""
from __future__ import annotations

import numpy as np


def lb_to_unitvec(l_deg: np.ndarray, b_deg: np.ndarray) -> np.ndarray:
    """Galactic (l, b) in degrees → Cartesian unit vectors, shape (..., 3)."""
    l = np.deg2rad(np.asarray(l_deg, dtype=float))
    b = np.deg2rad(np.asarray(b_deg, dtype=float))
    cb = np.cos(b)
    x = cb * np.cos(l)
    y = cb * np.sin(l)
    z = np.sin(b)
    return np.stack([x, y, z], axis=-1)


def unitvec_to_lb(vec: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Cartesian unit vectors → Galactic (l_deg, b_deg).

    ``l`` is returned in the conventional [0°, 360°) range; ``b`` in [−90°, 90°].
    """
    v = np.asarray(vec, dtype=float)
    x, y, z = v[..., 0], v[..., 1], v[..., 2]
    norm = np.sqrt(x * x + y * y + z * z)
    # Guard against zero-norm vectors by a safe NaN rather than silent unit.
    with np.errstate(invalid="ignore", divide="ignore"):
        xn = x / norm
        yn = y / norm
        zn = np.clip(z / norm, -1.0, 1.0)
    b = np.rad2deg(np.arcsin(zn))
    l = np.rad2deg(np.arctan2(yn, xn))
    l = np.mod(l, 360.0)
    return l, b


def spherical_mean(
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    w: np.ndarray | None = None,
) -> dict[str, float]:
    """Resultant-vector mean of (l, b) with weights w.

    Returns
    -------
    dict with keys ``l_deg``, ``b_deg``, ``resultant_R``. ``R ∈ [0, 1]``
    is the resultant length (1 → perfectly aligned, 0 → cancels to origin).
    The mean direction is degenerate when R = 0; we flag it by returning
    NaN longitudes.
    """
    l = np.asarray(l_deg, dtype=float)
    b = np.asarray(b_deg, dtype=float)
    if w is None:
        w = np.ones_like(l)
    w = np.asarray(w, dtype=float)
    if w.shape != l.shape:
        raise ValueError(
            f"weight shape {w.shape} does not match data shape {l.shape}"
        )
    wsum = float(w.sum())
    if wsum <= 0:
        raise ValueError(f"non-positive weight sum in spherical_mean: {wsum}")
    vec = lb_to_unitvec(l, b)                 # (N, 3)
    wbar = (w[..., None] * vec).sum(axis=0) / wsum
    R = float(np.linalg.norm(wbar))
    if R < 1e-12:
        return {"l_deg": float("nan"), "b_deg": float("nan"), "resultant_R": 0.0}
    l_mean, b_mean = unitvec_to_lb(wbar / R)
    return {"l_deg": float(l_mean), "b_deg": float(b_mean), "resultant_R": R}


def angular_separation_matrix(l_deg: np.ndarray, b_deg: np.ndarray) -> np.ndarray:
    """Pairwise angular separations in degrees, shape (N, N)."""
    vec = lb_to_unitvec(l_deg, b_deg)
    cos_sep = np.clip(vec @ vec.T, -1.0, 1.0)
    return np.rad2deg(np.arccos(cos_sep))


def galactic_plane_mask(b_deg: np.ndarray, half_angle_deg: float) -> np.ndarray:
    """Return a boolean mask keeping |b| ≥ half_angle (Zone of Avoidance cut)."""
    return np.abs(np.asarray(b_deg, dtype=float)) >= float(half_angle_deg)


def normalize_weights(
    w: np.ndarray,
    allow_uniform_fallback: bool = False,
) -> tuple[np.ndarray, str]:
    """Normalise directional weights to sum 1 with fallback provenance.

    Returns
    -------
    (w_norm, fallback_status) — fallback_status ∈
    {``'native_weights'``, ``'uniform_fallback_diagnostic_only'``}.

    Raises
    ------
    ValueError
        If all weights are zero and ``allow_uniform_fallback`` is False,
        or if the weight sum is non-positive.
    """
    w = np.asarray(w, dtype=float)
    if np.allclose(w, 0.0):
        if not allow_uniform_fallback:
            raise ValueError(
                "All directional weights are zero; uniform fallback is "
                "forbidden under the current SkySelectionConfig."
            )
        w_out = np.ones_like(w)
        return w_out / w_out.sum(), "uniform_fallback_diagnostic_only"
    s = float(w.sum())
    if s <= 0:
        raise ValueError(f"Non-positive weight sum: {s}")
    return w / s, "native_weights"
