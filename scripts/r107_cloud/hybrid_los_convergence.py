"""R107 cloud: convergence of the hybrid line-of-sight transfer against the native hierarchy.

Synthetic, time-independent H-normalised Lie geometries with a tanh recombination
(no HYREC, no data).  For each geometry the native hierarchy is run at several
truncations L; the line-of-sight (LoS) sky is computed from the L=16 history.  Output:
low-ell agreement per L, LoS spectra on HEALPix, and the change of those spectra
under the three numerical axes (pixel resolution, ray step, node density).
Numerical evidence only; no physical claim.

Usage: PYTHONPATH=.:htt:htt/src python -m scripts.r107_cloud.hybrid_los_convergence --output OUT.json
"""

from __future__ import annotations

import argparse
import json
import platform
import time

import numpy as np
from scipy.integrate import quad

from bass.transport.general_bianchi_transfer import gl_sphere_grid
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry, stokes_maps_to_vector
from bass.transport.hybrid_los_transfer import SCHEMA, healpix_directions, history_from_native_states, los_alm_healpix, los_sky

SIGMA = np.array([[1.0e-3, 0.4e-3, 0.7e-3], [0.4e-3, -0.3e-3, 0.2e-3], [0.7e-3, 0.2e-3, -0.7e-3]])
CASES = {"weak_class_B": (0.05, 0.3), "focusing_class_B": (0.3, 0.6)}
N_START = -9.0


def kappa(v: float) -> float:
    """Opacity per e-fold of a tanh recombination at N = -7 (width 0.05) with a 2e-4 residual."""
    return 5e-2 * np.exp(-2.0 * v) * (0.5 * (1.0 + np.tanh((-7.0 - v) / 0.05)) + 2e-4)


def native(L: int, a_x: float, n2: float, n_cells: int, substeps: int = 4):
    op = GeneralLieStokesOperator(L)
    geom = LieGeometry(SIGMA, np.array([a_x, 0.0, 0.0]), np.diag([0.0, n2, n2]))
    N = np.linspace(N_START, 0.0, n_cells + 1)
    dtau = np.array([quad(kappa, N[k], N[k + 1], limit=200)[0] for k in range(n_cells)])
    S = np.zeros(op.dim, dtype=complex)
    states = [S.copy()]
    t0 = time.perf_counter()
    for k in range(n_cells):
        dN = N[k + 1] - N[k]
        S = op.advance_cell(S, dN, geom, dtau[k], source_increment=op.shear_source_vector(SIGMA, amplitude=dN),
                            substeps=substeps, bolometric_redshift=True)
        states.append(S.copy())
    seconds = time.perf_counter() - t0
    g = geom.pack_14()
    hist = history_from_native_states(op, N, np.array(states), dtau, np.array([N_START, 0.0]), np.stack([g, g]),
                                      provenance={"geometry": "synthetic constant", "a_x": a_x, "n2": n2, "L": L,
                                                  "n_cells": n_cells, "substeps": substeps})
    return op, hist, S, seconds


def low_ell(op, S, hist, n_gl: int = 32, L_out: int = 4) -> dict:
    _, _, d, _ = gl_sphere_grid(n_gl)
    sky = los_sky(hist, d.reshape(-1, 3), max_step=0.02)
    opo = GeneralLieStokesOperator(L_out)
    vec = stokes_maps_to_vector(np.stack([sky.T, sky.Q, sky.U, sky.V], -1), opo.idx, opo.dim, L=L_out, n_gl_theta=n_gl)
    out = {}
    for ch in ("T", "E", "B"):
        for ell in range(1 if ch == "T" else 2, L_out + 1):
            nat = np.array([S[op.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
            los = np.array([vec[opo.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
            out[f"{ch}{ell}"] = float(np.max(np.abs(los - nat)) / max(np.max(np.abs(nat)), 1e-300))
    return out


def spectra(hist, nside: int, lmax: int, max_step: float) -> tuple[dict, float]:
    import healpy as hp

    t0 = time.perf_counter()
    sky = los_sky(hist, healpix_directions(nside), max_step=max_step)
    alm = los_alm_healpix(sky, nside, lmax)
    cl = hp.alm2cl([alm["T"], alm["E"], alm["B"]], lmax=lmax)
    return {"TT": cl[0], "EE": cl[1], "BB": cl[2]}, time.perf_counter() - t0


def rel_change(a: dict, b: dict, lmax: int, floor: float = 1e-6) -> dict:
    out = {}
    for key in ("TT", "EE", "BB"):
        x, y = a[key][2:lmax + 1], b[key][2:lmax + 1]
        keep = x > floor * x.max()
        out[key] = float(np.max(np.abs(y[keep] - x[keep]) / x[keep])) if np.any(keep) else None
    return out


def power_ell(cl: np.ndarray, frac: float) -> int:
    c = np.cumsum((2 * np.arange(cl.size) + 1) * cl)
    return int(np.searchsorted(c, frac * c[-1]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--nside", type=int, default=64)
    ap.add_argument("--lmax", type=int, default=128)
    ap.add_argument("--cells", type=int, default=300)
    args = ap.parse_args()
    result = {"schema": "htt.r107.hybrid_los_convergence/1", "los_schema": SCHEMA, "python": platform.python_version(),
              "numpy": np.__version__, "geometry_note": "synthetic constant H-normalised Lie geometry, tanh recombination",
              "sigma_N": SIGMA.tolist(), "cases": {}}
    for name, (a_x, n2) in CASES.items():
        case = {"a_x": a_x, "n2": n2, "native_vs_los_low_ell": {}}
        for L in (8, 12, 16):
            op, hist, S, sec = native(L, a_x, n2, args.cells)
            case["native_vs_los_low_ell"][str(L)] = {"native_seconds": sec, "max_rel_diff": low_ell(op, S, hist)}
        base, t_base = spectra(hist, args.nside, args.lmax, 0.02)
        coarse, _ = spectra(hist, args.nside // 2, args.lmax // 2, 0.02)
        fine_step, _ = spectra(hist, args.nside, args.lmax, 0.01)
        _, hist2, _, _ = native(16, a_x, n2, 2 * args.cells)
        dense, _ = spectra(hist2, args.nside, args.lmax, 0.02)
        case["los_spectra"] = {k: v.tolist() for k, v in base.items()}
        case["los_seconds_base"] = t_base
        case["ell_99_percent_TT_power"] = power_ell(base["TT"], 0.99)
        case["ell_99_9_percent_TT_power"] = power_ell(base["TT"], 0.999)
        lcmp = args.lmax // 2 - 8
        case["max_rel_change"] = {
            "pixel_resolution_nside_half_vs_full_up_to_ell": lcmp,
            "nside_half": rel_change(base, coarse, lcmp),
            "ray_step_0p01_vs_0p02": rel_change(base, fine_step, args.lmax - 8),
            "cells_double": rel_change(base, dense, args.lmax - 8),
        }
        result["cases"][name] = case
        print(name, json.dumps({k: case[k] for k in ("ell_99_percent_TT_power", "max_rel_change")}))
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)


if __name__ == "__main__":
    main()
