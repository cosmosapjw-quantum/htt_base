"""Massless two-radiation closure, homogeneous thermal IC and time refinement."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

import numpy as np

from bass.transport.coupled_einstein_boltzmann import (
    CoupledSolverConfig, _species_thomson_forces, build_early_family_state, solve_coupled_einstein_boltzmann,
)
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, max_stokes_reality_error, vector_to_stokes_maps


def solve_case(args):
    family, cells, fraction, picard = args
    op = GeneralLieStokesOperator(4)
    cfg = CoupledSolverConfig(ell_max=4, n_cells=cells, substeps_per_cell=2, n_picard=picard,
                              massless_neutrino_fraction=fraction, epsilon=0. if family=="FLRW" else 2e-4)
    result = solve_coupled_einstein_boltzmann(family, cfg, lie_op=op)
    nu = result.neutrino_final_state
    pol = [i for ch in ("E","B","V") for i in op.idx[ch].values()]
    if nu is not None and np.any(nu[pol]):
        raise ArithmeticError("collisionless massless neutrino polarization must vanish")
    if family=="FLRW" and (np.any(result.final_state) or (nu is not None and np.any(nu))):
        raise ArithmeticError("nonzero homogeneous FLRW angular response")
    if (nu is None) != (fraction==0.):
        raise ArithmeticError("incorrect active hierarchy")
    row = {"family":family,"cells":cells,"fraction":fraction,"picard":picard,
           "max_hamiltonian":result.max_hamiltonian_residual,"max_codazzi":result.max_codazzi_residual,
           "max_jacobi":result.max_jacobi_residual,"photon_norm":float(np.linalg.norm(result.final_state)),
           "neutrino_norm":None if nu is None else float(np.linalg.norm(nu)),
           "neutrino_polarization_max":None if nu is None else float(np.max(np.abs(nu[pol]))),
           "max_neutrino_reality":None if nu is None else float(max_stokes_reality_error(nu, op.idx)),
           "Omega_r":build_early_family_state(family,epsilon=cfg.epsilon)[1].Omega_r,
           "picard_stress_change":result.picard_pi_rel_change}
    p_direction = -op._grid[2].reshape(-1, 3)
    row["angular_vs_fluid_flux"] = {}
    for name, state in (("radiation", result.final_state), ("neutrino", nu)):
        if state is None:
            continue
        theta = vector_to_stokes_maps(state, op.idx, L=op.L, n_gl_theta=op.n_gl_theta)[..., 0].ravel()
        w = op._grid[3].ravel()
        q_angular = (4*w*theta) @ p_direction / (w @ (1+4*theta))
        v = result.trajectory.species_v_grid[name][-1]
        q_fluid = 4*v/(3+v @ v)
        err = float(np.linalg.norm(q_angular - q_fluid))
        norm = float(np.linalg.norm(q_fluid))
        row["angular_vs_fluid_flux"][name] = {"dimensionless_absolute":err, "relative":err/norm if norm else None}
    return row,result.final_state,nu


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--cells", type=int, default=48)
    p.add_argument("--N-eff", type=float, default=3.044,
                   help="Assume massless neutrinos with T_nu/T_gamma=(4/11)^(1/3)")
    args = p.parse_args()
    ratio = 7/8*(4/11)**(4/3)*args.N_eff
    if not np.isfinite(ratio) or ratio<=0 or args.cells<8:
        p.error("positive N_eff and at least eight base cells are required")
    f=ratio/(1+ratio)
    cases=[("FLRW",args.cells,0.,1),("FLRW",args.cells,f,2),
           ("VII_h",args.cells,0.,2),("VII_h",2*args.cells,f,3),
           ("VII_h",2*args.cells,f,4),("VII_h",4*args.cells,f,4),*(("VII_h",n*args.cells,f,2) for n in (1,2,4))]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        outputs=list(pool.map(solve_case,cases))
    rows=[r for r,_,_ in outputs]
    refinement={}
    for j,key in ((1,"photon"),(2,"neutrino")):
        fields=[out[j] for out in outputs[-3:]]
        scale=float(np.linalg.norm(fields[-1]))
        steps=[float(np.linalg.norm(a-b)/scale) for a,b in zip(fields,fields[1:])]
        refinement[key]={"relative_successive_differences":steps,"coarse_to_fine_ratio":steps[0]/steps[1]}
        if steps[1]>=steps[0] or not np.isfinite(steps[1]):
            raise ArithmeticError(f"{key} time mesh failed to refine: {steps}")
    with_nu=outputs[-3][1]
    without_nu=outputs[2][1]
    split_effect=float(np.linalg.norm(with_nu-without_nu)/np.linalg.norm(without_nu))
    if split_effect<=0:
        raise ArithmeticError("radiation split did not affect photon solution")
    T_gamma=np.diag([1.,1/3,1/3,1/3])
    forces=_species_thomson_forces(T_gamma,np.array([.21,.03,-.08]),2.5,4,0,2)
    if not np.any(forces[0]) or np.any(forces[3]) or np.any(np.sum(forces,axis=0)):
        raise ArithmeticError("radiation collision force contract failed")
    result={"status":"pass_scoped","closure":"homogeneous, massless thermal IC with common tilt; one collisionless brightness hierarchy, photon-only Thomson",
            "N_eff":args.N_eff,"fraction":f,"Omega_gamma":(1-f)*rows[0]["Omega_r"],"Omega_nu":f*rows[0]["Omega_r"],
            "scope_ell_max":4, "substeps":2,"controlled_abs_neutrino_four_force":float(np.linalg.norm(forces[3])),
            "controlled_abs_sum_collisional_force":float(np.linalg.norm(np.sum(forces,axis=0))),
            "relative_photon_change_at_fixed_Omega_r":split_effect,"runs":rows,"mesh_refinement":refinement}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(refinement))


if __name__ == "__main__":
    main()
