"""R106 H4: angular truncation / quadrature test of the VI_-1/9 sky-fluid photon q/E residual.

Config sweeps use the UNMODIFIED repo solver (R105, b234bb0e0):
  ell_max 4 -> 6 -> 8 with angular_basis(ell, max(16, ell+8)) at GL rings 16;
  GL rings 16 -> 24 -> 32 at ell_max 4.
Code VARIANT: the moving-Thomson kernel (gain columns, emission) is projected on
an auxiliary GL grid with RINGS rings while transport keeps 16 rings. The repo
MovingCollisionStage has no independent rest-frame quadrature order; it uses the
transport operator grid op._grid, so this variant decouples it.
Fixed: family VI_-1/9, epsilon 2e-4, n_picard 4, substeps_per_cell 2,
max_substep_depth 1.0, f_nu 0, record_history True.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
FAMILY = "VI_-1/9"
LEVELS = (48, 96, 192)


def _load_variant(moving_rings):
    """Load the variant moving stage and the solver copy under unique module names."""
    import bass.transport.coupled_einstein_boltzmann as live
    vdir = HERE / "variant"
    name_m = "r106_h4_moving_hiquad"
    spec = importlib.util.spec_from_file_location(name_m, vdir / "moving_collision_stage_hiquad.py")
    mm = importlib.util.module_from_spec(spec)
    sys.modules[name_m] = mm
    spec.loader.exec_module(mm)
    mm.RINGS = int(moving_rings)
    name_s = "r106_h4_coupled_hiquad"
    spec = importlib.util.spec_from_file_location(name_s, vdir / "coupled_hiquad.py")
    ms = importlib.util.module_from_spec(spec)
    sys.modules[name_s] = ms
    spec.loader.exec_module(ms)
    ms.HYREC_REF_CSV = live.HYREC_REF_CSV
    assert ms.MovingCollisionStage is mm.MovingCollisionStage
    return ms


def solve_task(task):
    """Run one solve in a fresh process and return per-cell diagnostics."""
    label, family, cells, ell, rings, moving_rings = task
    from bass.transport import coupled_einstein_boltzmann as live
    from scripts.r105.native_optical_refinement import angular_basis
    mod = live if moving_rings is None else _load_variant(moving_rings)
    op = angular_basis(ell, rings)
    cfg = mod.CoupledSolverConfig(
        n_cells=cells, ell_max=ell, n_picard=4, max_substep_depth=1.0,
        epsilon=2e-4, substeps_per_cell=2, record_history=True, massless_neutrino_fraction=0.0,
    )
    t0 = time.perf_counter()
    res = mod.solve_coupled_einstein_boltzmann(family, cfg, lie_op=op)
    wall = time.perf_counter() - t0
    h = res.history["picard_iterations"][-1]
    out = {
        "label": label, "family": family, "n_cells": cells, "ell_max": ell, "gl_rings": rings,
        "moving_kernel_rings": rings if moving_rings is None else int(moving_rings),
        "solver": "repo_R105_unmodified" if moving_rings is None else "variant_hiquad_moving_kernel",
        "solver_module_file": str(Path(mod.__file__).resolve()),
        "N_end": h["N_end"].tolist(),
        "q_sky": h["q_over_E_sky"][0].tolist(), "q_fluid": h["q_over_E_fluid"][0].tolist(),
        "pi_sky": h["pi_over_E_sky"][0].tolist(), "pi_fluid": h["pi_over_E_fluid"][0].tolist(),
        "delta_tau": h["delta_tau"].tolist(), "photon_substeps": h["photon_substeps"].tolist(),
        "hamiltonian_cell_ends_max": float(np.max(h["hamiltonian"])),
        "codazzi_cell_ends_max": float(np.max(h["codazzi"])),
        "thomson_sky": h["thomson_force_over_E_sky"].tolist(),
        "thomson_fluid": h["thomson_force_over_E_fluid"].tolist(),
        "max_hamiltonian": res.max_hamiltonian_residual, "max_codazzi": res.max_codazzi_residual,
        "max_jacobi": res.max_jacobi_residual, "max_stokes_reality": res.max_stokes_reality_err,
        "max_four_force_orthog_error": res.max_four_force_orthog_error,
        "picard_pi_rel_change": res.picard_pi_rel_change,
        "C2": {k: float(res.cl_final[k][2]) for k in ("T", "E", "B")},
        "C1T": float(res.cl_final["T"][1]),
        "total_optical_depth": res.total_optical_depth,
        "wall_s": wall,
        "worker_maxrss_kB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "pid": os.getpid(),
    }
    return out


def tasks_for(groups):
    table = {
        "control_l4_r16": (4, 16, None),
        "ell6_r16": (6, 16, None),
        "ell8_r16": (8, 16, None),
        "l4_r24": (4, 24, None),
        "l4_r32": (4, 32, None),
        "variant_kernel_r64": (4, 16, 64),
        "variant_kernel_r16_plumbing": (4, 16, 16),
    }
    out = []
    for g in groups:
        if g.startswith("FLRW:"):
            base = g.split(":", 1)[1]
            ell, rings, mr = table[base]
            out.append((g, "FLRW", 48, ell, rings, mr))
            continue
        if g.endswith("@48"):
            base = g[:-3]
            ell, rings, mr = table[base]
            out.append((g, FAMILY, 48, ell, rings, mr))
            continue
        ell, rings, mr = table[g]
        out.extend((g, FAMILY, n, ell, rings, mr) for n in LEVELS)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--groups", nargs="+", required=True)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not 1 <= a.workers <= 3:
        p.error("workers must be 1..3 on the shared workstation")
    tasks = tasks_for(a.groups)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=min(a.workers, len(tasks)), max_tasks_per_child=1) as pool:
        rows = list(pool.map(solve_task, tasks))
    files = {
        "repo_solver": ROOT / "htt/bass/transport/coupled_einstein_boltzmann.py",
        "repo_moving_stage": ROOT / "htt/bass/transport/moving_collision_stage.py",
        "repo_general_lie_stokes": ROOT / "htt/bass/transport/general_lie_stokes.py",
        "repo_common_time_moments": ROOT / "scripts/r105/common_time_moments.py",
        "repo_native_optical_refinement": ROOT / "scripts/r105/native_optical_refinement.py",
        "variant_solver_copy": HERE / "variant/coupled_hiquad.py",
        "variant_moving_stage": HERE / "variant/moving_collision_stage_hiquad.py",
        "driver": Path(__file__).resolve(),
    }
    payload = {
        "schema": "htt.r106.h4_angular.raw.1",
        "sha256": {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in files.items()},
        "python": platform.python_version(), "numpy": np.__version__,
        "env": {k: os.getenv(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "PYTHONPATH")},
        "groups": a.groups, "workers": a.workers, "wall_s_total": time.perf_counter() - t0,
        "runs": rows,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(payload, indent=1, allow_nan=False) + "\n")
    for r in rows:
        q = np.asarray(r["q_sky"]); f = np.asarray(r["q_fluid"])
        rel0 = np.linalg.norm(q[0] - f[0]) / max(np.linalg.norm(f[0]), 1e-300)
        print(f"{r['label']:32s} {r['family']:8s} N={r['n_cells']:4d} rel_first_native={rel0:.6e} "
              f"wall={r['wall_s']:.1f}s rss={r['worker_maxrss_kB']} kB")


if __name__ == "__main__":
    main()
