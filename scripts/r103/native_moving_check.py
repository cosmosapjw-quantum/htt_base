"""Reproduce finite-domain R103 Thomson and active coupled-family checks."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.linalg import expm

from bass.background.general_tilted_evolution import energy_momentum_ratio_from_primitive, primitive_from_energy_momentum_ratio
from bass.transport.coupled_einstein_boltzmann import (
    ALL_SEVEN_FAMILIES, CoupledSolverConfig, solve_coupled_einstein_boltzmann,
)
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, vector_to_stokes_maps
from bass.transport.moving_collision_stage import MovingCollisionStage, initial_radiation_stokes


def modal_metrics():
    op = GeneralLieStokesOperator(6)
    beta0 = np.array([.24, -.19, .07])
    logE, flux_ratio = energy_momentum_ratio_from_primitive(2.8, beta0, 1/3)
    _, _, _, T = primitive_from_energy_momentum_ratio(logE, flux_ratio, 1/3)
    sky = vector_to_stokes_maps(initial_radiation_stokes(op, beta0), op.idx, L=op.L, n_gl_theta=op.n_gl_theta)
    n = op._grid[2].reshape(-1, 3)
    k4 = np.column_stack([np.ones(len(n)), -n])
    weighted_I = op._grid[3].ravel()*(1+4*sky[..., 0].ravel())*T[0,0]/(4*np.pi)
    recovered = np.einsum('n,ni,nj->ij', weighted_I, k4, k4)
    ratio_error = np.max(abs(T-recovered))/T[0,0]

    beta = np.array([.13, -.11, .06])
    mov = MovingCollisionStage(op, beta)
    K = mov.loss.toarray() + mov.left @ mov.right_h
    k = np.array([.3,.1,-.5])
    geom = np.zeros(14)
    base = op.base_operator(geom, k_eff=k)
    rng = np.random.default_rng(103)
    y = rng.normal(size=op.dim) + 1j*rng.normal(size=op.dim)
    exact = expm(.8*base.toarray()+3*K) @ y
    errors = []
    for nsub in (4,8,16):
        v = op.advance_cell(y, .8, geom, 3., k_eff=k, substeps=nsub, moving_collision=mov)
        errors.append(float(np.linalg.norm(v-exact)/np.linalg.norm(exact)))
    depth = 1000.
    stage = mov.factor_sdirk_stage(base, .25, 4000.)(y)
    residual = float(np.linalg.norm(stage - .25*(base @ stage) - depth*mov.apply(stage) - y)/np.linalg.norm(y))
    ratios = [a/b for a,b in zip(errors, errors[1:])]
    if ratio_error >= 1e-13 or residual >= 1e-11 or min(ratios)<=3.8:
        raise ArithmeticError("modal accuracy contract failed")
    return {"ell_max":6,"normal_quadrature_n_theta":op.n_gl_theta,"stokes_dimension":op.dim,
            "ic_beta":beta0.tolist(),"ic_stress_max_abs_over_energy":float(ratio_error),
            "collision_beta":beta.tolist(),"stage_depth":depth,"stiff_relative_residual":residual,
            "Fourier_k":k.tolist(),"delta_N":.8,"delta_tau":3.0,"substeps":[4,8,16],
            "relative_state_error_vs_expm":errors,"successive_error_ratios":ratios}


def run_family(args):
    family, hand, ell, cells, picard, epsilon = args
    cfg = CoupledSolverConfig(ell_max=ell,n_cells=cells,n_picard=picard,handedness=hand,
                              epsilon=0. if family=="FLRW" else epsilon)
    out = solve_coupled_einstein_boltzmann(family, cfg)
    if max(out.max_jacobi_residual, out.max_hamiltonian_residual, out.max_codazzi_residual)>cfg.constraint_abort_tol:
        raise ArithmeticError("constraint acceptance failed")
    l2 = {ch:float(out.cl_final[ch][2]) for ch in ("T","E","B","V")}
    if family=="FLRW" and any(np.any(cl) for cl in out.cl_final.values()):
        raise ArithmeticError("nonzero FLRW response")
    if family!="FLRW" and min(l2["T"],l2["E"])<=0:
        raise ArithmeticError("missing TT or EE response")
    return {"family":family,"handedness":hand,"ell_max":ell,"n_cells":cells,
            "n_picard":picard,"epsilon":cfg.epsilon,"substeps":cfg.substeps_per_cell,
            "max_jacobi":out.max_jacobi_residual,"max_hamiltonian":out.max_hamiltonian_residual,
            "max_codazzi":out.max_codazzi_residual,"max_ub_dot_F":out.max_four_force_orthog_error,
            "max_reality":out.max_stokes_reality_err,"picard_pi_rel_change":out.picard_pi_rel_change,
            "Cl2":l2, "tau_anchor":out.total_optical_depth}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--ell", type=int, default=4)
    p.add_argument("--cells", type=int, default=32)
    p.add_argument("--picard", type=int, default=2)
    p.add_argument("--epsilon", type=float, default=2e-4)
    a = p.parse_args()
    t0=time.perf_counter()
    modal=modal_metrics()
    tasks=[(f, h, a.ell, a.cells, a.picard, a.epsilon)
           for f in ALL_SEVEN_FAMILIES for h in ((1,-1) if f=="VII_h" else (1,))]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        per_family=list(pool.map(run_family,tasks))
    result={"status":"pass_scoped","physics_scope":"cold Thomson in conserved anchor; midpoint geometry, finite harmonic closure; one radiation species",
            "parent_revision":"664845022a9600ad925d6c1332143395aac5ed90","modal":modal,"coupled_families":per_family,
            "python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,
            "workers":a.workers, "OPENBLAS_NUM_THREADS":os.getenv("OPENBLAS_NUM_THREADS"),
            "elapsed_seconds":time.perf_counter()-t0}
    a.output.parent.mkdir(exist_ok=True,parents=True)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(modal,allow_nan=False))


if __name__ == "__main__":
    main()
