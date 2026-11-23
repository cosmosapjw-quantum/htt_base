"""Compare nested, simultaneous photon q/E samples in the exceptional VI_-1/9 solution."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
from pathlib import Path
from time import perf_counter

import numpy as np

from bass.transport import coupled_einstein_boltzmann as coupled
from scripts.r105.native_optical_refinement import angular_basis
from scripts.r105.solver_axes import identity, save

COARSE = 48
LEVELS = (48, 96, 192)
FAMILY = "VI_-1/9"


def nested_samples(common, edges, sky, fluid):
    """Use exact solver endpoints; q is in the solver normal frame for both estimates."""
    common, edges, sky, fluid = map(np.asarray, (common, edges, sky, fluid))
    if common.ndim != 1 or not common.size or edges.ndim != 1 or not edges.size:
        raise ValueError("expected nonempty one-dimensional endpoint arrays")
    if sky.shape != (len(edges), 3) or fluid.shape != sky.shape:
        raise ValueError("expected one momentum vector per cell and species")
    if not all(np.isfinite(a).all() for a in (common, edges, sky, fluid)):
        raise ValueError("nonfinite endpoint or photon momentum")
    if np.any(np.diff(common) <= 0) or np.any(np.diff(edges) <= 0):
        raise ValueError("cell endpoints must increase in ln(a)")
    stride, rem = divmod(len(edges), len(common))
    if rem or not stride:
        raise ValueError("fine grid must be an integer refinement of the coarse grid")
    index = np.arange(1, len(common) + 1) * stride - 1
    if not np.array_equal(edges[index], common):
        raise ValueError("corresponding ln(a) endpoints do not match exactly")
    samples = []
    for idx in index:
        diff = sky[idx] - fluid[idx]
        absolute = float(np.linalg.norm(diff))
        scale = float(np.linalg.norm(fluid[idx]))
        samples.append({
            "cell_index": int(idx), "sky": sky[idx].tolist(), "fluid": fluid[idx].tolist(),
            "sky_minus_fluid": diff.tolist(), "absolute_norm": absolute,
            "relative_norm": absolute / scale if scale else None,
        })
    return samples


def solve(cells):
    cfg = coupled.CoupledSolverConfig(
        n_cells=cells, ell_max=4, n_picard=4, max_substep_depth=1.0,
        epsilon=2e-4, substeps_per_cell=2, record_history=True,
        stage_rate_collision=False, picard_rtol=None,  # R106 pin: reproduce R105 exactly
    )
    start = perf_counter()
    out = coupled.solve_coupled_einstein_boltzmann(FAMILY, cfg, lie_op=angular_basis(4, 16))
    history = out.history["picard_iterations"][-1]
    return {
        "edges": history["N_end"], "sky": history["q_over_E_sky"][0],
        "fluid": history["q_over_E_fluid"][0], "wall_s": perf_counter() - start,
        "native_first_depth": float(history["delta_tau"][0]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    with ProcessPoolExecutor(max_workers=min(args.workers, len(LEVELS))) as pool:
        results = dict(zip(LEVELS, pool.map(solve, LEVELS)))
    common = results[COARSE]["edges"]
    aligned = {
        n: nested_samples(common, r["edges"], r["sky"], r["fluid"]) for n, r in results.items()
    }
    native_first = {}
    for n, r in results.items():
        first = nested_samples(r["edges"][:1], r["edges"][:1], r["sky"][:1], r["fluid"][:1])[0]
        native_first[n] = {"ln_a": float(r["edges"][0]), "delta_tau": r["native_first_depth"], **first}
    rows = [
        {"ln_a": float(t), "by_n_cells": {n: aligned[n][i] for n in LEVELS}}
        for i, t in enumerate(common)
    ]
    rel = np.asarray([[row["relative_norm"] for row in aligned[n]] for n in LEVELS], dtype=float)
    if not np.isfinite(rel).all():
        raise ValueError("the tilted fixture requires nonzero finite reference momenta")
    summary = {}
    for index, (a, b) in enumerate(zip(LEVELS, LEVELS[1:])):
        err_a, err_b = rel[index:index+2]
        worsened = np.flatnonzero(err_b > err_a)
        summary[f"{a}_to_{b}"] = {
            "n_strictly_smaller": int(np.sum(err_b < err_a)), "n_equal": int(np.sum(err_b == err_a)),
            "larger_coarse_indices": worsened.tolist(), "first_common_pair": [err_a[0], err_b[0]],
            "peak_common_pair": [err_a.max(), err_b.max()], "last_common_pair": [err_a[-1], err_b[-1]],
        }
    sources = identity()
    sources["sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    save(args.output, {
        "schema": "htt.r105.common_time_moments.1", "status": "executed", "physics_identity": sources,
        "family": FAMILY, "epsilon": 2e-4, "ell_max": 4, "gl_rings": 16, "n_picard": 4,
        "neutrino_fraction": 0.0, "min_substeps": 2, "max_substep_depth": 1.0,
        "comparison": "Final Picard photon sky minus fluid q/E in the shared solver normal frame; "
                      "samples use exactly equal cell endpoints in ln(a). Relative norm divides by |fluid q/E|.",
        "native_first": native_first, "summary": summary, "common_endpoints": rows,
        "wall_s_by_n_cells": {n: r["wall_s"] for n, r in results.items()},
    })
    print(f"{len(rows)} exactly matched VI_-1/9 endpoints for {LEVELS}; saved {args.output}")


if __name__ == "__main__":
    main()
