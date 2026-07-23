from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from htt_ext.lowell.alm import axisymmetric_alm, correlated_real_alms
from htt_ext.lowell.poles import pole_from_alm
from htt_ext.types import ShellGrid, SourceModel


@dataclass(frozen=True)
class RemoteFieldSimulation:
    redshifts: tuple[float, ...]
    dipole_true: np.ndarray
    dipole_reconstructed: np.ndarray
    quadrupole_true: np.ndarray
    quadrupole_reconstructed: np.ndarray
    dipole_poles: tuple[tuple[float, float, float], ...]
    quadrupole_poles: tuple[tuple[float, float, float], ...]
    model: str


def simulate_remote_fields(
    grid: ShellGrid,
    *,
    model: SourceModel | str,
    seed: int = 20260722,
    axis: tuple[float, float, float] = (0.25, -0.45, 0.8573214099),
    dipole_noise: float = 0.8,
    quadrupole_noise: float = 1.4,
) -> RemoteFieldSimulation:
    """Toy remote dipole/quadrupole field and noisy reconstruction.

    The DGP is deliberately transparent and only validates the HTT source-
    discrimination and partial-identification machinery.  PRs in the roadmap
    replace the covariance and kernels with CAMB/CLASS/GLASS and kSZ/pSZ
    quadratic-estimator predictions.
    """
    model = SourceModel(model)
    rng = np.random.default_rng(seed)
    z = np.asarray(grid.redshifts)
    cov = np.exp(-np.abs(z[:, None] - z[None, :]) / 0.5)
    dip = correlated_real_alms(1, cov, rng)
    quad = correlated_real_alms(2, 0.7 * cov, rng)
    n = np.asarray(axis, dtype=float)
    n /= np.linalg.norm(n)

    if model in {SourceModel.GLOBAL_COHERENT, SourceModel.MIXTURE}:
        prof = 1.6 / np.sqrt(1.0 + z)
        dip += prof[:, None] * axisymmetric_alm(1, n, 1.0)[None, :]
        quad += 0.75 * prof[:, None] * axisymmetric_alm(2, n, 1.0)[None, :]
    if model in {SourceModel.LOCAL_STRUCTURE, SourceModel.MIXTURE}:
        prof = 1.8 * np.exp(-(z / 0.22) ** 2)
        local_axis = np.array([-0.5, 0.75, 0.4330127019])
        local_axis /= np.linalg.norm(local_axis)
        dip += prof[:, None] * axisymmetric_alm(1, local_axis, 1.0)[None, :]
        quad += 0.45 * prof[:, None] * axisymmetric_alm(2, local_axis, 1.0)[None, :]
    # A local observer boost is deliberately absent from remote fields.

    dip_rec = dip + dipole_noise * correlated_real_alms(1, np.eye(grid.size), rng)
    quad_rec = quad + quadrupole_noise * correlated_real_alms(2, np.eye(grid.size), rng)
    dip_poles = tuple(tuple(float(x) for x in pole_from_alm(a, 1)[0]) for a in dip_rec)
    quad_poles = tuple(tuple(float(x) for x in pole_from_alm(a, 2)[0]) for a in quad_rec)
    return RemoteFieldSimulation(
        grid.redshifts,
        dip,
        dip_rec,
        quad,
        quad_rec,
        dip_poles,
        quad_poles,
        model.value,
    )
