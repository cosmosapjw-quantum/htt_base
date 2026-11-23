"""Evolve native Stokes collision cells on the BASS Gauss--Legendre sky.

From the repository root:
    PYTHONPATH=.:htt:htt/src python -m scripts.r101.coherency_history

The default demonstration reads the repository HyRec-2 recombination reference
between z=1150 and 950. Shear/H, baryon velocity/c, and the initial I,Q,U,V
sky are prescribed perturbation fixtures. The default run exposes the final
signed all-m coefficients of the forced collision subproblem.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from bass.collision.coherency import ThomsonCoherencyPropagator
from bass.transport.general_bianchi_transfer import (
    _spherical_screen_basis, gl_sphere_grid, scalar_alm_from_map, spin2_alm_from_qu,
)
from bass.transport.stokes_fourier import FourierStokesPropagator

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "htt/bass/recombination/fixtures/recombination_ref_planck2018.csv"


def evolve_cells(operator, initial, delta_tau, source_increments=None):
    """Evolve in chronological order with an optional integrated source per cell."""
    depths = np.asarray(delta_tau)
    if depths.ndim != 1 or not np.isrealobj(depths) or not np.all(np.isfinite(depths)) or np.any(depths < 0):
        raise ValueError("delta_tau must contain finite nonnegative scalar cell depths")
    sky = operator.advance(initial, 0.)
    if source_increments is None:
        # All cells share one electron frame and no intervening actions.
        return operator.advance(sky, float(np.sum(depths)))
    sources = np.asarray(source_increments)
    if sources.shape != (len(depths), *sky.shape):
        raise ValueError("source_increments must match the time and Stokes sky dimensions")
    for depth, source in zip(depths, sources):
        sky = operator.advance_with_source(sky, depth, source)
    return sky


def alm_from_stokes(sky, theta, phi, weights, ell_max):
    """Return every signed (ell,m) in I,V for ell>=0 and E,B for ell>=2."""
    if np.iscomplexobj(sky):
        real = alm_from_stokes(np.real(sky), theta, phi, weights, ell_max)
        imag = alm_from_stokes(np.imag(sky), theta, phi, weights, ell_max)
        return {ch: {lm: a+1j*imag[ch][lm] for lm,a in modes.items()}
                for ch,modes in real.items()}
    I, Q, U, V = np.reshape(sky, (*theta.shape, 4)).transpose(2, 0, 1)
    E, B = spin2_alm_from_qu(Q, U, theta, phi, weights, ell_max)
    return {"I": scalar_alm_from_map(I, theta, phi, weights, ell_max),
            "E": E, "B": B, "V": scalar_alm_from_map(V, theta, phi, weights, ell_max)}


def recombination_case(reference=REFERENCE, ell_max=6, n_theta=12, k_per_mpc=None, substeps=1):
    if not (2 <= ell_max < n_theta):
        raise ValueError("require 2 <= ell_max < n_theta for this Gauss--Legendre readout")
    with Path(reference).open() as stream:
        rows = csv.DictReader(line for line in stream if not line.startswith("#"))
        series = [(float(r["z"]), float(r["kappa"]), float(r["tau_dot"]))
                  for r in rows if 950 <= float(r["z"]) <= 1150]
    if not series:
        raise ValueError("reference must include the z=950..1150 recombination interval")
    z, kappa, opacity_per_mpc = np.array(series).T
    if z[0] != 950 or z[-1] != 1150 or np.any(np.diff(z) <= 0) or np.any(np.diff(kappa) < 0):
        raise ValueError("expected increasing tabulated redshift and optical depth with both interval endpoints")
    depths = -np.diff(kappa[::-1])
    dN = -np.diff(np.log1p(z[::-1]))
    theta, phi, direction_grid, weights = gl_sphere_grid(n_theta)
    n = direction_grid.reshape(-1, 3)
    u, v = _spherical_screen_basis(n)
    nx, ny, nz = n.T
    initial = np.zeros((len(n), 4))
    initial[:, 0] = 1e-4*(nx*ny + nz**3)
    initial[:, 3] = 3e-5*(nx - .3*ny + .7*nz) + 1e-5*(3*nz*nz-1)
    shear_over_H = 1e-4*np.array([[.7, .3, -.2], [.3, -1., .1], [-.2, .1, .3]])
    baryon_beta = 2e-5*np.array([1., -.5, .2])
    source = np.zeros((len(depths), len(n), 4))
    source[:, :, 0] = (-dN[:, None]*np.einsum("ni,ij,nj->n", n, shear_over_H, n)
                       + depths[:, None]*(n @ baryon_beta))
    extra = {}
    if k_per_mpc is None:
        operator = ThomsonCoherencyPropagator(n, weights.ravel(), u, v)
        final = evolve_cells(operator, initial, depths, source)
    else:
        if np.any(opacity_per_mpc <= 0.) or not np.all(np.isfinite(opacity_per_mpc)):
            raise ValueError("the reference Fourier case requires positive tabulated d(kappa)/d(chi)")
        # Integrate dchi = d(tau)/opacity using tabulated conformal opacity [Mpc^-1].
        inv = 1./opacity_per_mpc[::-1]
        distances = .5*(inv[1:] + inv[:-1])*depths
        transport = FourierStokesPropagator(n, weights.ravel(), k_per_mpc, u, v)
        final = initial
        for dist, depth, f in zip(distances, depths, source):
            final = transport.advance(final, dist, depth, source_increment=f, substeps=substeps)
        extra = {"fourier_k_per_mpc": np.asarray(k_per_mpc).tolist(),
                 "total_comoving_path_mpc": float(distances.sum()), "substeps_per_cell": substeps,
                 "spatial_transport": "flat FLRW single Fourier mode with prescribed source amplitudes"}
    alm = alm_from_stokes(final, theta, phi, weights, ell_max)
    return {"scope": "electron-rest collision plus prescribed linear shear and baryon-dipole forcing",
            "clock": "HyRec-2 recombination table, forward increments of cumulative kappa",
            "z_start": float(z[-1]), "z_end": float(z[0]), "cells": len(depths),
            "total_optical_depth": float(depths.sum()), "n_directions": len(n), "ell_max": ell_max,
            **extra, "alm": {ch: [[l, m, float(val.real), float(val.imag)] for (l,m), val in modes.items()]
                    for ch, modes in alm.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--ell-max", type=int, default=6)
    parser.add_argument("--n-theta", type=int, default=12)
    parser.add_argument("--k-per-mpc", type=float, nargs=3, help="propagate one comoving Fourier wavevector")
    parser.add_argument("--substeps", type=int, default=1)
    args = parser.parse_args()
    case = recombination_case(args.reference, args.ell_max, args.n_theta, args.k_per_mpc, args.substeps)
    print(json.dumps(case, allow_nan=False))


if __name__ == "__main__":
    main()
