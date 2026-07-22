from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from htt_ext.types import PoleDefinition, PoleTrajectory, ShellGrid, SourceModel
from .alm import axisymmetric_alm, correlated_real_alms
from .poles import pole_from_alm


@dataclass(frozen=True)
class ShellPoleSimulation:
    model: str
    grid: ShellGrid
    ells: tuple[int, ...]
    shell_alms: dict[int, np.ndarray]
    cumulative_alms: dict[int, np.ndarray]
    shell_trajectories: dict[int, PoleTrajectory]
    cumulative_trajectories: dict[int, PoleTrajectory]
    injected_axis: tuple[float, float, float]


def _correlation_matrix(redshifts: np.ndarray, corr_length: float) -> np.ndarray:
    dz = np.abs(redshifts[:, None] - redshifts[None, :])
    return np.exp(-dz / max(corr_length, 1e-6))


def _profile(redshifts: np.ndarray, model: SourceModel) -> np.ndarray:
    if model == SourceModel.GLOBAL_COHERENT:
        return 1.0 / np.sqrt(1.0 + redshifts)
    if model == SourceModel.LOCAL_STRUCTURE:
        return np.exp(-(redshifts / 0.18) ** 2)
    if model == SourceModel.MIXTURE:
        return 0.65 / np.sqrt(1.0 + redshifts) + 0.35 * np.exp(-(redshifts / 0.18) ** 2)
    return np.zeros_like(redshifts)


def simulate_shell_poles(
    grid: ShellGrid,
    *,
    ells: tuple[int, ...] = (1, 2, 3),
    model: SourceModel | str = SourceModel.ISOTROPIC,
    seed: int = 20260722,
    injected_axis: tuple[float, float, float] = (0.25, -0.45, 0.8573214099),
    stochastic_variance: float = 1.0,
    correlation_length: float = 0.45,
    coherent_amplitudes: dict[int, float] | None = None,
    observer_boost_amplitudes: dict[int, float] | None = None,
    pole_definition: PoleDefinition | str = PoleDefinition.ANISOTROPY_TENSOR,
) -> ShellPoleSimulation:
    """Generate dependency-free shell and cumulative low-ell pole trajectories.

    This is a reference DGP, not a physical Boltzmann solver.  Its purpose is to
    exercise source-identification, coverage, rank and mutation gates before the
    CAMB/CLASS/GLASS and native-Bianchi tracks are connected.
    """
    model = SourceModel(model)
    rng = np.random.default_rng(seed)
    z = np.asarray(grid.redshifts, dtype=float)
    w = np.asarray(grid.weights, dtype=float)
    axis = np.asarray(injected_axis, dtype=float)
    axis /= np.linalg.norm(axis)
    coherent_amplitudes = coherent_amplitudes or {1: 2.2, 2: 1.2, 3: 0.7}
    observer_boost_amplitudes = observer_boost_amplitudes or {1: 5.0, 2: 0.7, 3: 0.25}

    corr = _correlation_matrix(z, correlation_length) * stochastic_variance
    shell_alms: dict[int, np.ndarray] = {}
    cumulative_alms: dict[int, np.ndarray] = {}
    shell_trajectories: dict[int, PoleTrajectory] = {}
    cumulative_trajectories: dict[int, PoleTrajectory] = {}

    for ell in ells:
        a = correlated_real_alms(ell, corr, rng)
        prof = _profile(z, model)
        if model in {SourceModel.GLOBAL_COHERENT, SourceModel.LOCAL_STRUCTURE, SourceModel.MIXTURE}:
            template = axisymmetric_alm(ell, axis, coherent_amplitudes.get(ell, 0.0))
            a = a + prof[:, None] * template[None, :]

        # A local observer boost is an endpoint term, not a remote shell source.
        endpoint = np.zeros(2 * ell + 1, dtype=np.complex128)
        if model in {SourceModel.LOCAL_BOOST, SourceModel.MIXTURE}:
            endpoint = axisymmetric_alm(ell, axis, observer_boost_amplitudes.get(ell, 0.0))

        cumulative = np.cumsum(w[:, None] * a, axis=0) + endpoint[None, :]
        shell_alms[ell] = a
        cumulative_alms[ell] = cumulative

        shell_poles, shell_vals = [], []
        cumulative_poles, cumulative_vals = [], []
        for k in range(grid.size):
            p, vals = pole_from_alm(a[k], ell, pole_definition)
            cp, cvals = pole_from_alm(cumulative[k], ell, pole_definition)
            shell_poles.append(tuple(float(x) for x in p))
            shell_vals.append(tuple(float(x) for x in vals))
            cumulative_poles.append(tuple(float(x) for x in cp))
            cumulative_vals.append(tuple(float(x) for x in cvals))
        shell_trajectories[ell] = PoleTrajectory(
            ell,
            grid.redshifts,
            tuple(shell_poles),
            tuple(shell_vals),
        )
        cumulative_trajectories[ell] = PoleTrajectory(
            ell,
            grid.redshifts,
            tuple(cumulative_poles),
            tuple(cumulative_vals),
        )

    return ShellPoleSimulation(
        model=model.value,
        grid=grid,
        ells=ells,
        shell_alms=shell_alms,
        cumulative_alms=cumulative_alms,
        shell_trajectories=shell_trajectories,
        cumulative_trajectories=cumulative_trajectories,
        injected_axis=tuple(float(x) for x in axis),
    )
