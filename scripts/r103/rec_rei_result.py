"""R103 REC/REI probes and two-Picard coupled FLRW and Bianchi V runs."""
import argparse
import json
import platform
from pathlib import Path
import numpy as np
import scipy
from scipy.interpolate import CubicSpline

from bass.recombination.baryon_history import BaryonHistory
from bass.recombination.opacity_history import OpacityHistory
from bass.recombination.reionization import ReionizationParameters
from bass.recombination.tilted_hyrec import integrate_tilted_recombination, load_hyrec_atomic_tables
from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann


def calculate():
    tables = load_hyrec_atomic_tables()
    times = np.linspace(-2, 0, 17)
    H = np.full_like(times, 2e-17)
    v = np.tile([0.2, -0.1, 0.0], (len(times), 1))
    a = H[:, None]*[0.3, 0., 0.]
    zero = np.zeros((len(times),3,3))
    b = BaryonHistory(times, H, zero, a, zero, v)
    x = np.linspace(-2, 0, 61)
    current_error = np.max(np.abs([b.hydrogen_factor(t)/np.exp(0.12*t)-1 for t in x]))
    theta_error = np.max(np.abs([b.theta(t)/(H[0]*(3-0.12)/np.sqrt(0.95))-1 for t in x]))
    nodes, rates = np.arange(6.), np.array([1e8,0,0,0,1e-20,1e-20])
    grid = np.linspace(0,5,501)
    op = OpacityHistory(nodes,rates)
    thin = float(op.cells([4.,5.]).delta_tau[0])
    mu = OpacityHistory(x,np.full_like(x,0.72),beta=[0.2,0,0],direction=[1,0,0])
    c = mu.cells(x)
    slab_error = np.max(np.abs(c.delta_tau - np.diff(x)*0.72*0.8))
    if not (current_error < 1e-13 and theta_error < 1e-13 and abs(thin/1e-20-1) < 1e-14 and slab_error < 1e-14):
        raise ArithmeticError("current/optical fixture mismatch")

    def history_check(z):
        h = integrate_tilted_recombination(z, tables=tables, reionization=ReionizationParameters())
        cells = h.opacity_history().cells(h.N_grid)
        transmission = np.exp(-h.kappa[0])
        return {"node_count":len(z), "cell_mass_plus_transmission":float(cells.visibility_mass.sum()+transmission),
                "sampled_trapezoid_plus_transmission":float(np.trapezoid(h.visibility,h.N_grid)+transmission)}
    sparse = np.linspace(1500,0,301)
    refined = np.unique(np.r_[sparse,np.linspace(0,18,181)])[::-1]
    histories = [history_check(sparse), history_check(refined)]
    if any(abs(r["cell_mass_plus_transmission"]-1)>3e-15 for r in histories):
        raise ArithmeticError("finite history transmission mismatch")
    if abs(histories[-1]["sampled_trapezoid_plus_transmission"] - 1)>2e-3:
        raise ArithmeticError("resolved nodal visibility outside the original tolerance")
    coupled = {}
    cfg = CoupledSolverConfig(ell_max=2,n_cells=24,n_picard=2,substeps_per_cell=2)
    for family in ("FLRW","V"):
        out = solve_coupled_einstein_boltzmann(family,cfg,tables=tables)
        cells = out.recombination.opacity_history().cells(out.trajectory.N_grid)
        coupled[family] = {"tau":out.total_optical_depth,
                           "max_abs_stokes":float(np.max(np.abs(out.final_state))),
                           "hamiltonian_relative":out.max_hamiltonian_residual,
                           "codazzi_relative":out.max_codazzi_residual,
                           "closure_error":float(abs(cells.visibility_mass.sum()+np.exp(-out.total_optical_depth)-1))}
        if coupled[family]["closure_error"]>3e-15:
            raise ArithmeticError("coupled visibility normalization")
    if coupled["FLRW"]["max_abs_stokes"] != 0 or coupled["V"]["max_abs_stokes"] == 0:
        raise ArithmeticError("isotropic or anisotropic coupled control failed")
    return {"scope":"Homogeneous background, expanding Sobolev rays, cold Thomson, tabulated HYREC and homogeneous tanh REI. Two Picard passes with a prescribed Saha warm start. Counts exclude calibration or family attribution.",
            "baseline":"664845022", "atomic_sha256":tables.sha256_manifest,
            "software":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
            "class_b":{"max_relative_Da3_error":current_error, "max_relative_theta_error":theta_error},
            "opacity":{"adversarial_cubic_min":float(CubicSpline(nodes,rates)(grid).min()),
                       "pchip_min":float(op.rate(grid).min()),"late_cell_depth":thin,
                       "max_directional_slab_depth_error":slab_error},
            "visibility":histories,"coupled_controls":{"ell_max":2,"n_cells":24,"picard":2,"families":coupled}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=calculate()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
