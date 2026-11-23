"""Finite baryon-proper-time chemistry and Thomson depth on a class-A N grid.

Conditional on supplied, cellwise-frozen transition rates. All dimensional
inputs are SI. The observer is at the final grid edge. Photon directions point
along propagation in the normal orthonormal tetrad.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import frexp, ldexp

import numpy as np
from numpy.typing import ArrayLike
from scipy.linalg import expm, expm_frechet

from .reionization import C_LIGHT, SIGMA_T


@dataclass(frozen=True)
class ChemistryTangent:
    """Fixed-grid directional derivatives of the named inputs, zero if omitted.

    Rate, initial-population and unit-direction tangents must respect their
    linear equality constraints. Interior rate and population derivatives may
    have either sign. At a boundary the caller specifies a feasible one-sided
    direction if the derivative is to represent a physical perturbation.
    """

    proper_generators_s: ArrayLike | None = None
    initial_population: ArrayLike | None = None
    electron_yield: ArrayLike | None = None
    hubble_normal_s: ArrayLike | None = None
    beta: ArrayLike | None = None
    photon_direction: ArrayLike | None = None
    comoving_hydrogen_m3: float = 0.0


@dataclass(frozen=True)
class ChemistryObservables:
    """Node populations and electron fractions, cell depths and visibility."""

    population: np.ndarray
    x_e: np.ndarray
    delta_optical_depth: np.ndarray
    optical_depth_to_observer: np.ndarray
    visibility_bin_probability: np.ndarray


@dataclass(frozen=True)
class ChemistryHistory(ChemistryObservables):
    tangent: ChemistryObservables | None


def _real_array(value, name):
    if np.iscomplexobj(value):
        raise ValueError(f"{name} must be real")
    result = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be finite")
    return result


def _input(value, shape, name, *, cells=None):
    arr = _real_array(value, name)
    if cells is None:
        if arr.shape == shape:
            return arr
    else:
        if arr.shape == shape:
            return np.broadcast_to(arr, (cells, *shape))
        if arr.shape == (cells, *shape):
            return arr
    raise ValueError(f"invalid shape for {name}: {arr.shape}")


def _direction(value, shape, name, *, cells=None):
    if value is None:
        return np.zeros(shape if cells is None else (cells, *shape))
    return _input(value, shape, name, cells=cells)


def _check_zero_sum(values, axis, name):
    # Use each column's own scale: physical rates can be far below one per s.
    scale = np.abs(values).sum(axis=axis)
    if np.any(np.abs(values.sum(axis=axis)) > 64 * np.finfo(float).eps * scale):
        raise ValueError(f"{name} must sum to zero")


def _chemical_step(rate, charge, width, drate, dcharge):
    """Column-stochastic transition and exponentially weighted electron reward.

    Squaring a floating-point matrix whose column sums drift by epsilon can
    amplify that drift by 2**s. The normalized stochastic transition and its
    differentiated normalization preserve the exact mass identities at each
    doubling. The reward uses its own analytic density factor at each scale.
    """
    k = charge.size
    scaled_norm = width * max(3.0, np.max(-np.diag(rate)))
    doublings = max(0, frexp(scaled_norm)[1])
    h = ldexp(float(width), -doublings)
    matrix = np.zeros((k + 1, k + 1))
    matrix[:k, :k] = rate * h - np.eye(k) * (3.0 * h)
    matrix[-1, :k] = charge * h
    if drate is None:
        propagator = expm(matrix)
        dtrans = dreward = None
    else:
        dmatrix = np.zeros_like(matrix)
        dmatrix[:k, :k] = drate * h
        dmatrix[-1, :k] = dcharge * h
        propagator, derivative = expm_frechet(matrix, dmatrix)
        dtrans = derivative[:k, :k] * np.exp(3.0 * h)
        dreward = derivative[-1, :k]
    trans = propagator[:k, :k] * np.exp(3.0 * h)
    reward = propagator[-1, :k]
    for i in range(doublings + 1):
        column_sums = trans.sum(axis=0)
        trans = trans / column_sums
        if dtrans is not None:
            dtrans = (dtrans - trans * dtrans.sum(axis=0)) / column_sums
        if i == doublings:
            break
        attenuation = np.exp(-3.0 * h)
        if dtrans is not None:
            dreward = dreward + attenuation * (dreward @ trans + reward @ dtrans)
            dtrans = dtrans @ trans + trans @ dtrans
        reward = reward + attenuation * (reward @ trans)
        trans = trans @ trans
        h *= 2.0
    return trans, reward, dtrans, dreward


def _to_observer(cell_depth):
    return np.r_[np.cumsum(cell_depth[::-1])[::-1], 0.0]


def evolve_clocked_chemistry(
    N_edges: ArrayLike,
    initial_population: ArrayLike,
    electron_yield: ArrayLike,
    proper_generators_s: ArrayLike,
    hubble_normal_s: ArrayLike,
    beta: ArrayLike,
    photon_direction: ArrayLike,
    comoving_hydrogen_m3: float,
    *,
    tangent: ChemistryTangent | None = None,
) -> ChemistryHistory:
    """Propagate a supplied finite chemical network, its opacity, and its tangent.

    Use strictly increasing N=ln(a) edges. For k states supply an initial
    probability column (k,) and a nonnegative electron-per-H readout (k,).
    A proper generator (k,k) has rates in s^-1, nonnegative off-diagonals and
    zero column sums. H_n>0 is in s^-1, beta=v_b/c is subluminal and the ray
    direction is a normal-frame unit vector. Any of these last four inputs
    may have a leading cell axis for piecewise-constant coefficients.

    The positive scalar anchor is n_H,rest Gamma a^3 in m^-3. Hydrogen current
    conservation in a homogeneous class-A background fixes its constancy.
    Composition and bulk velocity are common to the cell; the transition law
    (and any radiative or density dependence of its tangent) is supplied by
    the caller. A single ray can have one direction per cell. All tangents
    hold the N edges fixed, including the epoch of observation.
    """
    edges = _real_array(N_edges, "N_edges")
    if edges.ndim != 1 or len(edges) < 2 or np.any(np.diff(edges) <= 0):
        raise ValueError("N_edges must be strictly increasing with at least two entries")
    ncell = len(edges) - 1
    init = _real_array(initial_population, "initial_population")
    if init.ndim != 1 or not init.size or np.any(init < 0) or abs(init.sum() - 1.0) > 1e-12:
        raise ValueError("initial_population must be a nonnegative probability column")
    k = init.size
    charge = _input(electron_yield, (k,), "electron_yield")
    rates = _input(proper_generators_s, (k, k), "proper_generators_s", cells=ncell)
    hubble = _input(hubble_normal_s, (), "hubble_normal_s", cells=ncell)
    velocity = _input(beta, (3,), "beta", cells=ncell)
    rays = _input(photon_direction, (3,), "photon_direction", cells=ncell)
    anchor = _input(comoving_hydrogen_m3, (), "comoving_hydrogen_m3")
    _check_zero_sum(rates, 1, "proper generator columns")
    if np.any(rates[:, ~np.eye(k, dtype=bool)] < 0.0):
        raise ValueError("proper generator off-diagonals must be nonnegative")
    if np.any(charge < 0) or np.any(hubble <= 0) or anchor <= 0:
        raise ValueError("nonnegative electron yields, positive H_n and hydrogen anchor required")
    beta2 = np.einsum("ij,ij->i", velocity, velocity)
    if np.any(beta2 >= 1.0):
        raise ValueError("beta must be subluminal")
    if not np.allclose(np.linalg.norm(rays, axis=1), 1.0, atol=2e-13, rtol=0):
        raise ValueError("photon_direction must have unit norm")
    # Stable at near-collinear relativistic velocity, algebraically 1 - beta.n.
    one_minus_beta_dot_n = 0.5 * (1 - beta2 + np.sum((velocity - rays)**2, axis=1))
    inv_gamma = np.sqrt(1.0 - beta2)
    frac = np.empty((ncell + 1, k))
    frac[0] = init
    depth = np.empty(ncell)

    if tangent is not None:
        dfrac = np.empty_like(frac)
        dfrac[0] = _direction(tangent.initial_population, (k,), "d_initial_population")
        _check_zero_sum(dfrac[0], 0, "initial_population tangent")
        dcharge = _direction(tangent.electron_yield, (k,), "d_electron_yield")
        drates = _direction(tangent.proper_generators_s, (k, k), "d_proper_generators_s", cells=ncell)
        _check_zero_sum(drates, 1, "proper generator tangent columns")
        dh = _direction(tangent.hubble_normal_s, (), "d_hubble_normal_s", cells=ncell)
        dv = _direction(tangent.beta, (3,), "d_beta", cells=ncell)
        dn = _direction(tangent.photon_direction, (3,), "d_photon_direction", cells=ncell)
        if np.any(np.abs(np.sum(rays * dn, axis=1)) > 2e-12 * np.linalg.norm(dn, axis=1)):
            raise ValueError("photon_direction tangent must be orthogonal to the ray")
        danchor = _input(tangent.comoving_hydrogen_m3, (), "d_comoving_hydrogen_m3")
        ddepth = np.empty_like(depth)

    with np.errstate(over="raise", divide="raise", invalid="raise"):
        for j, width in enumerate(np.diff(edges)):
            per_efold = inv_gamma[j] / hubble[j]
            rate = rates[j] * per_efold
            drate = dcharge_cell = None
            if tangent is not None:
                dlog_clock = -np.dot(velocity[j], dv[j]) / (1.0 - beta2[j]) - dh[j] / hubble[j]
                drate = drates[j] * per_efold + rate * dlog_clock
                dcharge_cell = dcharge
            trans, reward, dtrans, dreward = _chemical_step(rate, charge, width, drate, dcharge_cell)
            frac[j+1] = trans @ frac[j]
            integrated_charge = reward @ frac[j]
            multiplier = SIGMA_T * C_LIGHT * anchor * np.exp(-3.0 * edges[j]) / hubble[j]
            angular_factor = one_minus_beta_dot_n[j]
            depth[j] = multiplier * angular_factor * integrated_charge
            if tangent is not None:
                dfrac[j+1] = dtrans @ frac[j] + trans @ dfrac[j]
                dintegral = dreward @ frac[j] + reward @ dfrac[j]
                dangular = -np.dot(dv[j], rays[j]) - np.dot(velocity[j], dn[j])
                dmult = multiplier * (danchor / anchor - dh[j] / hubble[j])
                ddepth[j] = ((dmult * angular_factor + multiplier * dangular) * integrated_charge
                             + multiplier * angular_factor * dintegral)

        if (not np.isfinite(frac).all() or not np.isfinite(depth).all()
                or np.any(frac < 0.0) or np.any(depth < 0.0)
                or not np.allclose(frac.sum(axis=1), 1.0, atol=2e-10, rtol=0)):
            raise FloatingPointError("chemical propagation lost finiteness, mass or positivity")
        kappa = _to_observer(depth)
        transmission = np.exp(-kappa[1:])
        local_probability = -np.expm1(-depth)
        probability = transmission * local_probability
        x_e = frac @ charge
        derivative = None
        if tangent is not None:
            dkappa = _to_observer(ddepth)
            dprob = transmission * (np.exp(-depth) * ddepth - local_probability * dkappa[1:])
            dxe = dfrac @ charge + frac @ dcharge
            if not all(np.isfinite(x).all() for x in (dfrac, dxe, ddepth, dkappa, dprob)):
                raise FloatingPointError("nonfinite chemistry or optical depth tangent")
            derivative = ChemistryObservables(dfrac, dxe, ddepth, dkappa, dprob)
    return ChemistryHistory(frac, x_e, depth, kappa, probability, derivative)
