#!/usr/bin/env python3
"""Synthetic numerical witnesses for the publishable analysis programme.

These experiments validate theorem mechanics only. They do not consume real
Planck or CF4 inputs and must not be reported as measured data results.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def _sha256_like_label(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    import hashlib

    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def spherical_jn(l: int, x: np.ndarray) -> np.ndarray:
    """Small self-contained spherical Bessel functions for l=0..3."""

    x = np.asarray(x, dtype=float)
    out = np.zeros_like(x)
    # The sin/cos closed forms suffer cancellation for low-k witnesses.
    # Use the leading series over the small-x range relevant here.
    small = np.abs(x) < 1e-3
    xs = x[~small]

    if l == 0:
        out[small] = 1.0 - x[small] ** 2 / 6.0
        out[~small] = np.sin(xs) / xs
    elif l == 1:
        out[small] = x[small] / 3.0
        out[~small] = np.sin(xs) / xs**2 - np.cos(xs) / xs
    elif l == 2:
        out[small] = x[small] ** 2 / 15.0
        out[~small] = (3.0 / xs**3 - 1.0 / xs) * np.sin(xs) - 3.0 * np.cos(xs) / xs**2
    elif l == 3:
        out[small] = x[small] ** 3 / 105.0
        out[~small] = (15.0 / xs**4 - 6.0 / xs**2) * np.sin(xs) - (15.0 / xs**3 - 1.0 / xs) * np.cos(xs)
    else:
        raise ValueError("this witness implements l=0..3 only")
    return out


def rank_evalue_experiment(seed: int = 17, n_sims: int = 50_000) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    response = np.array(
        [
            [1.0, 0.2, 0.0, 0.0],
            [0.4, 1.0, 0.0, 0.0],
            [0.8, -0.2, 0.0, 0.0],
            [-0.1, 0.5, 0.0, 0.0],
            [0.2, 0.1, 0.0, 0.0],
            [0.6, 0.7, 0.0, 0.0],
        ],
        dtype=float,
    )
    rank = int(np.linalg.matrix_rank(response, tol=1e-12))
    blind_norms = np.linalg.norm(response[:, 2:], axis=0)

    # E-values with exact unit mean under an exponential null. Convex mixtures
    # remain e-values and have Markov threshold control in expectation.
    e_values = rng.exponential(scale=1.0, size=(n_sims, 4))
    weights = np.array([0.45, 0.25, 0.20, 0.10])
    e_mix = e_values @ weights
    mean_e = float(np.mean(e_mix))
    exceedance = {
        "alpha_0.10": float(np.mean(e_mix >= 10.0)),
        "alpha_0.05": float(np.mean(e_mix >= 20.0)),
        "alpha_0.01": float(np.mean(e_mix >= 100.0)),
    }
    pass_markov = exceedance["alpha_0.10"] <= 0.10 and exceedance["alpha_0.05"] <= 0.05 and exceedance["alpha_0.01"] <= 0.01

    observed_stat = 2.75
    null_stats = rng.gamma(shape=rank, scale=1.0 / rank, size=n_sims)
    plus_one_p = float((np.count_nonzero(null_stats >= observed_stat) + 1) / (n_sims + 1))

    result = {
        "experiment": "rank_evalue",
        "owner": "HTT",
        "claim_tier": "synthetic_theorem_witness",
        "rank": rank,
        "blind_column_norms": blind_norms.tolist(),
        "mean_e_value": mean_e,
        "markov_exceedance": exceedance,
        "plus_one_rank_p_synthetic": plus_one_p,
        "pass": rank == 2 and bool(np.all(blind_norms <= 1e-12)) and abs(mean_e - 1.0) < 0.02 and pass_markov,
        "caveats": ["synthetic null only", "no observed data", "no native solver output"],
    }
    result["config_hash"] = _sha256_like_label({"seed": seed, "n_sims": n_sims, "response": response.tolist()})
    return result


def boltzmann_visibility_experiment(n_grid: int = 4096) -> dict[str, Any]:
    eta = np.linspace(0.0, 1.0, n_grid)
    eta0 = 1.0
    visibility = np.exp(-0.5 * ((eta - 0.72) / 0.055) ** 2)
    visibility /= np.trapezoid(visibility, eta)
    source = np.exp(-2.0 * eta) * (1.0 + 0.15 * eta)
    bound = float(np.trapezoid(visibility * np.abs(source), eta))

    k_grid = np.geomspace(1e-3, 30.0, 96)
    transfers: dict[str, list[float]] = {}
    bounds_ok = True
    small_k_scaling_ok = True
    for ell in (2, 3):
        vals = []
        for k in k_grid:
            x = k * (eta0 - eta)
            val = float(np.trapezoid(visibility * source * spherical_jn(ell, x), eta))
            vals.append(val)
            bounds_ok = bounds_ok and abs(val) <= bound + 1e-10
        transfers[f"ell_{ell}"] = vals
        ratio = abs(vals[1] / vals[0])
        expected = (k_grid[1] / k_grid[0]) ** ell
        small_k_scaling_ok = small_k_scaling_ok and 0.60 <= ratio / expected <= 1.40

    # Volterra/ODE memory witness.
    z = np.linspace(0.0, 1.0, n_grid)
    gamma = 3.0
    pi_source = 1.0 + 0.5 * z
    ode = np.zeros_like(z)
    ode[0] = pi_source[0]
    dz = z[1] - z[0]
    for i in range(1, z.size):
        ode[i] = ode[i - 1] + dz * (-gamma * (ode[i - 1] - pi_source[i - 1]))
    volterra = np.zeros_like(z)
    for i in range(z.size):
        kernel = np.exp(-gamma * (z[i] - z[: i + 1]))
        volterra[i] = math.exp(-gamma * z[i]) * ode[0] + np.trapezoid(gamma * kernel * pi_source[: i + 1], z[: i + 1])
    volterra_error = float(np.max(np.abs(ode - volterra)))
    depth_gap = float(ode[-1] / ode[0])

    result = {
        "experiment": "boltzmann_visibility",
        "owner": "BASS_PY",
        "claim_tier": "synthetic_theorem_witness",
        "visibility_l1": float(np.trapezoid(visibility, eta)),
        "source_bound": bound,
        "max_abs_transfer": float(max(abs(v) for values in transfers.values() for v in values)),
        "bounds_ok": bool(bounds_ok),
        "small_k_scaling_ok": bool(small_k_scaling_ok),
        "volterra_ode_max_error": volterra_error,
        "depth_gap_for_growing_source": depth_gap,
        "pass": bool(bounds_ok and small_k_scaling_ok and volterra_error < 2e-3 and depth_gap > 1.0),
        "caveats": ["single-mode visibility toy", "not full native atlas", "no real map data"],
    }
    result["config_hash"] = _sha256_like_label({"n_grid": n_grid, "gamma": gamma})
    return result


def local_global_response_experiment(seed: int = 23) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    local = np.array([1.0, 0.4, -0.1, 0.0, 0.2, 0.1])
    global_tilt = np.array([0.1, 0.8, 0.3, 0.5, -0.1, 0.2])
    systematic = np.array([0.9, 0.35, -0.05, 0.02, 0.18, 0.08])
    local /= np.linalg.norm(local)
    global_tilt /= np.linalg.norm(global_tilt)
    systematic /= np.linalg.norm(systematic)

    nuisance = np.column_stack([local, systematic])
    q, _ = np.linalg.qr(nuisance)
    residual = global_tilt - q @ (q.T @ global_tilt)
    residual_norm = float(np.linalg.norm(residual))
    overlap = float(abs(np.dot(local, global_tilt)))
    candidate_status = "candidate" if residual_norm > 0.25 else "blocked_rank_deficient"

    null_residuals = []
    for _ in range(2000):
        draw = rng.normal(size=6)
        draw /= np.linalg.norm(draw)
        r = draw - q @ (q.T @ draw)
        null_residuals.append(float(np.linalg.norm(r)))
    percentile = float(np.mean(np.array(null_residuals) <= residual_norm))

    result = {
        "experiment": "local_global_response",
        "owner": "HTT",
        "claim_tier": "synthetic_design_witness",
        "local_global_overlap_abs": overlap,
        "global_residual_after_local_systematic_projection": residual_norm,
        "null_percentile_synthetic": percentile,
        "candidate_status": candidate_status,
        "pass": candidate_status == "candidate" and residual_norm > 0.25,
        "caveats": ["synthetic response vectors", "requires matched nulls before real claim"],
    }
    result["config_hash"] = _sha256_like_label({"seed": seed})
    return result


def run_all(experiment: str = "all") -> dict[str, Any]:
    available = {
        "rank_evalue": rank_evalue_experiment,
        "boltzmann_visibility": boltzmann_visibility_experiment,
        "local_global_response": local_global_response_experiment,
    }
    if experiment == "all":
        results = [fn() for fn in available.values()]
    else:
        if experiment not in available:
            raise SystemExit(f"unknown experiment: {experiment}")
        results = [available[experiment]()]
    return {
        "schema_version": "htt.publishable_analysis_pack.synthetic_experiments.v1",
        "owner": "COMMON",
        "claim_tier": "synthetic_mechanics_only",
        "native_solver_result": False,
        "all_pass": all(bool(item["pass"]) for item in results),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="all", choices=["all", "rank_evalue", "boltzmann_visibility", "local_global_response"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    payload = run_all(args.experiment)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
