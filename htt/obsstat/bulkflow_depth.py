"""Pure-numpy bulk-flow-versus-depth aggregation for OBSSTAT.

Volume-averaged peculiar-velocity (bulk-flow) vectors in radial shells, plus a
bootstrap apex-dispersion estimate. Observer-side kinematic descriptors only:
not HTT evidence, not a cosmological-frame-violation claim, not Bianchi family
identification. The caller supplies positions and velocities in a single
Cartesian frame; frame conversion to Galactic (l, b) is the driver's job.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np

__all__ = [
    "radial_shell_bulkflow",
    "bootstrap_apex_dispersion",
    "angle_between_deg",
]


def angle_between_deg(u: Sequence[float], v: Sequence[float]) -> float:
    """Directional angle in [0, 180] between two velocity-apex vectors."""
    a = np.asarray(u, dtype=float)
    b = np.asarray(v, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        raise ValueError("cannot take the angle of a zero vector")
    cos = float(np.dot(a, b) / (na * nb))
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def radial_shell_bulkflow(
    positions: np.ndarray,
    velocities: np.ndarray,
    edges: Sequence[float],
) -> list[dict]:
    """Return the volume-averaged bulk-flow vector per radial shell.

    ``positions`` and ``velocities`` are (N, 3) Cartesian arrays in a shared
    frame. ``edges`` are the shell boundaries (length B+1). Each output row has
    the shell radii, point count, mean bulk-flow vector, magnitude, and apex
    unit vector. Empty shells are skipped.
    """

    pos = np.asarray(positions, dtype=float)
    vel = np.asarray(velocities, dtype=float)
    if pos.shape != vel.shape or pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError("positions and velocities must be matching (N, 3) arrays")
    edge_list = [float(e) for e in edges]
    if len(edge_list) < 2 or any(b <= a for a, b in zip(edge_list, edge_list[1:])):
        raise ValueError("edges must be strictly increasing with length >= 2")
    radius = np.linalg.norm(pos, axis=1)
    rows: list[dict] = []
    for lo, hi in zip(edge_list[:-1], edge_list[1:]):
        mask = (radius >= lo) & (radius < hi)
        n = int(np.count_nonzero(mask))
        if n == 0:
            continue
        bulk = vel[mask].mean(axis=0)
        magnitude = float(np.linalg.norm(bulk))
        apex_unit = (bulk / magnitude) if magnitude > 0.0 else np.zeros(3)
        rows.append(
            {
                "r_lo": lo,
                "r_hi": hi,
                "r_mean": float(radius[mask].mean()),
                "n": n,
                "bulk_vector": bulk,
                "bulk_magnitude": magnitude,
                "apex_unit": apex_unit,
            }
        )
    return rows


def bootstrap_apex_dispersion(
    velocities_in_shell: np.ndarray,
    *,
    n_boot: int,
    seed: int,
) -> dict:
    """Bootstrap the bulk-flow apex of one shell over its member cells.

    Returns the magnitude percentiles and the median angular dispersion (deg)
    of the resampled apex about the full-shell apex. The resampling is over
    (correlated) reconstruction cells, so the dispersion is a lower bound on the
    true direction uncertainty, not a full covariance.
    """

    vel = np.asarray(velocities_in_shell, dtype=float)
    if vel.ndim != 2 or vel.shape[1] != 3 or vel.shape[0] == 0:
        raise ValueError("velocities_in_shell must be a non-empty (N, 3) array")
    rng = np.random.default_rng(seed)
    n = vel.shape[0]
    base = vel.mean(axis=0)
    base_mag = float(np.linalg.norm(base))
    mags: list[float] = []
    angles: list[float] = []
    for _ in range(int(n_boot)):
        idx = rng.integers(0, n, size=n)
        sample = vel[idx].mean(axis=0)
        mags.append(float(np.linalg.norm(sample)))
        if base_mag > 0.0 and np.linalg.norm(sample) > 0.0:
            angles.append(angle_between_deg(sample, base))
    return {
        "bulk_magnitude": base_mag,
        "bulk_magnitude_p16": float(np.percentile(mags, 16)),
        "bulk_magnitude_p84": float(np.percentile(mags, 84)),
        "apex_angular_dispersion_deg_median": float(np.median(angles)) if angles else 0.0,
        "apex_angular_dispersion_deg_p84": float(np.percentile(angles, 84)) if angles else 0.0,
        "n_boot": int(n_boot),
    }
