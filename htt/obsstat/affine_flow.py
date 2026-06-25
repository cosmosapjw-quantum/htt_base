"""LR-06F: affine velocity-gradient decomposition of a 3D reconstruction field.

Within a sphere of radius R about the observer, fit the linear (affine) flow

    v_j(r) = B_j + M_ji r_i ,   M_ji = d v_j / d r_i ,

and split the velocity-gradient tensor M into its physical parts:

    expansion  Theta = tr(M)                  (the local Hubble-like divergence)
    shear      sigma = sym(M) - (Theta/3) I   (trace-free symmetric rate of strain)
    vorticity  omega = antisym(M)             (the curl; axial vector w)

``B`` is the residual bulk flow. Vorticity from a reconstruction is
reconstruction-conditioned (potential/Wiener-filter reconstructions suppress
curl by construction), so a recovered omega is a property of the reconstruction,
not a detected physical vorticity; the curl-injection check validates only that
the estimator *would* recover an injected curl.

This module is OBSSTAT observer-side feature extraction only: no model
likelihood, no posterior, no Bianchi family or geometry claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class AffineFlow:
    bulk: np.ndarray          # B_j  (km/s)
    gradient: np.ndarray      # M_ji (km/s / Mpc)
    expansion: float          # Theta = tr(M)  (km/s / Mpc)
    shear: np.ndarray         # trace-free symmetric (km/s / Mpc)
    vorticity_axial: np.ndarray   # w = (1/2) curl v  (km/s / Mpc)
    n_cells: int
    radius: float

    @property
    def bulk_amplitude(self) -> float:
        return float(np.linalg.norm(self.bulk))

    @property
    def shear_amplitude(self) -> float:
        return float(np.sqrt(0.5 * np.einsum("ij,ij", self.shear, self.shear)))

    @property
    def vorticity_amplitude(self) -> float:
        return float(np.linalg.norm(self.vorticity_axial))


def decompose_gradient(M: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    M = np.asarray(M, dtype=float)
    theta = float(np.trace(M))
    sym = 0.5 * (M + M.T)
    shear = sym - np.eye(3) * theta / 3.0
    anti = 0.5 * (M - M.T)
    # axial vector w_k = -1/2 eps_kij anti_ij ; here w = 1/2 curl v.
    w = np.array([anti[2, 1], anti[0, 2], anti[1, 0]], dtype=float)
    return theta, shear, w


def fit_affine_flow(positions: np.ndarray, velocities: np.ndarray, radius: float | None = None) -> AffineFlow:
    """Least-squares affine fit v = B + M r over the supplied cells.

    positions: (N,3) Mpc, velocities: (N,3) km/s. If radius is given, only cells
    with |r| <= radius are used.
    """
    p = np.asarray(positions, dtype=float)
    v = np.asarray(velocities, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or v.shape != p.shape:
        raise ValueError("positions and velocities must both be (N,3)")
    if radius is not None:
        mask = np.einsum("ij,ij->i", p, p) <= radius * radius
        p, v = p[mask], v[mask]
    n = p.shape[0]
    if n < 4:
        raise ValueError("need at least 4 cells for an affine fit")
    design = np.column_stack([np.ones(n), p])           # (N,4): [1, x, y, z]
    coeff, *_ = np.linalg.lstsq(design, v, rcond=None)  # (4,3)
    bulk = coeff[0]
    M = coeff[1:].T                                     # M_ji = d v_j / d r_i
    theta, shear, w = decompose_gradient(M)
    return AffineFlow(bulk, M, theta, shear, w, n, float(radius) if radius is not None else float("inf"))


def bootstrap_affine(positions: np.ndarray, velocities: np.ndarray, radius: float,
                     n_boot: int = 500, seed: int = 12345) -> dict:
    """Bootstrap over cells. Cells are spatially correlated, so the spread is a
    lower bound on the true uncertainty, not a calibrated covariance."""
    p = np.asarray(positions, dtype=float)
    v = np.asarray(velocities, dtype=float)
    mask = np.einsum("ij,ij->i", p, p) <= radius * radius
    p, v = p[mask], v[mask]
    n = p.shape[0]
    rng = np.random.default_rng(seed)
    bulk_amp, theta, shear_amp, vort_amp = [], [], [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        fit = fit_affine_flow(p[idx], v[idx])
        bulk_amp.append(fit.bulk_amplitude)
        theta.append(fit.expansion)
        shear_amp.append(fit.shear_amplitude)
        vort_amp.append(fit.vorticity_amplitude)
    def stat(a):
        a = np.asarray(a)
        return {"mean": float(a.mean()), "std": float(a.std(ddof=1)),
                "p16": float(np.percentile(a, 16)), "p84": float(np.percentile(a, 84))}
    return {"n_cells": int(n), "n_boot": int(n_boot),
            "bulk_amplitude": stat(bulk_amp), "expansion": stat(theta),
            "shear_amplitude": stat(shear_amp), "vorticity_amplitude": stat(vort_amp)}


def curl_injection_recovery(positions: np.ndarray, velocities: np.ndarray, radius: float,
                            omega_inject: np.ndarray) -> dict:
    """Inject a solid-body rotation v += omega x r and check the recovered curl.

    Validates the estimator's curl channel independently of whether the
    reconstruction itself carries vorticity.
    """
    p = np.asarray(positions, dtype=float)
    v = np.asarray(velocities, dtype=float)
    omega = np.asarray(omega_inject, dtype=float).reshape(3)
    base = fit_affine_flow(p, v, radius)
    injected = v + np.cross(omega, p)
    rec = fit_affine_flow(p, injected, radius)
    # solid-body rotation omega gives vorticity axial vector w = omega.
    recovered = rec.vorticity_axial - base.vorticity_axial
    err = float(np.linalg.norm(recovered - omega))
    return {"omega_injected": omega.tolist(), "omega_recovered": recovered.tolist(),
            "abs_error": err, "rel_error": err / float(np.linalg.norm(omega) + 1e-30)}


def potential_flow_projection(positions: np.ndarray, velocities: np.ndarray) -> np.ndarray:
    """Toy curl-suppressing reconstruction: keep only the symmetric affine mode.

    Returns ``B + r . sym(M)^T`` — a potential-flow surrogate that, by
    construction, carries no antisymmetric (vorticity) component.
    """
    fit = fit_affine_flow(positions, velocities)
    symmetric = 0.5 * (fit.gradient + fit.gradient.T)
    return fit.bulk[None, :] + np.asarray(positions, dtype=float) @ symmetric.T


def curl_suppression_ensemble(*, realizations: int = 300, cells: int = 450,
                              seed: int = 20260625) -> dict:
    """PR08-004 mechanics demo: a curl-suppressing reconstruction makes physical
    vorticity unidentifiable even when the pre-reconstruction field carries it.

    This is a *structural non-identifiability* result, not a vorticity detection.
    The full field-realization posterior remains BLOCKED_MISSING_FIELD_REALIZATIONS.
    """
    rng = np.random.default_rng(seed)
    positions = rng.uniform(-120.0, 120.0, size=(cells, 3))
    positions = positions[np.linalg.norm(positions, axis=1) < 120.0]
    B = np.array([120.0, -55.0, 35.0])
    shear = np.array([[0.018, 0.004, -0.002], [0.004, -0.010, 0.003], [-0.002, 0.003, -0.008]])
    theta = 0.012
    omega = np.array([0.006, -0.004, 0.009])
    Omega = np.array([[0.0, -omega[2], omega[1]], [omega[2], 0.0, -omega[0]], [-omega[1], omega[0], 0.0]])
    M = shear + np.eye(3) * theta / 3.0 + Omega
    truth_velocity = B[None, :] + positions @ M.T
    full_omega = []; proj_omega = []; full_bulk = []
    for _ in range(realizations):
        noisy = truth_velocity + rng.normal(scale=18.0, size=truth_velocity.shape)
        full = fit_affine_flow(positions, noisy)
        proj = fit_affine_flow(positions, potential_flow_projection(positions, noisy))
        full_omega.append(full.vorticity_axial); full_bulk.append(full.bulk)
        proj_omega.append(proj.vorticity_axial)
    full_omega = np.asarray(full_omega); proj_omega = np.asarray(proj_omega)
    return {
        "schema": "htt.pr08_004.k6_curl_suppression.synthetic.v1",
        "realizations": int(realizations), "cells": int(positions.shape[0]),
        "truth_bulk": B.tolist(), "truth_vorticity": omega.tolist(),
        "full_reconstruction_bulk_mean": np.mean(full_bulk, axis=0).tolist(),
        "full_reconstruction_vorticity_mean": np.mean(full_omega, axis=0).tolist(),
        "full_reconstruction_vorticity_sd": np.std(full_omega, axis=0, ddof=1).tolist(),
        "potential_projected_vorticity_mean": np.mean(proj_omega, axis=0).tolist(),
        "potential_projected_vorticity_max_norm": float(np.max(np.linalg.norm(proj_omega, axis=1))),
        "conclusion": "a curl-suppressing reconstruction makes physical vorticity unidentifiable even when the pre-reconstruction field contains it",
    }
