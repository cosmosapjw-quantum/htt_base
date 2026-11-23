"""Matched R104-R105 optical-depth substep experiment in Bianchi VII_h and IX."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time

import numpy as np
import scipy

from bass.transport import coupled_einstein_boltzmann as live
from bass.transport.general_lie_stokes import GeneralLieStokesOperator
from scripts.r104.solver_axis_sweep import _solver

BASE_COMMIT="5a5f3b44d4fa5be65b71c2f80e715ebf9d1abf0a"
SOLVER_PATH="htt/bass/transport/coupled_einstein_boltzmann.py"
BASE_SHA="9ed4ecd7ddb312d0722d5ef0e9fd111518a359ba70f161e7674264e762813996"
ROOT=Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def angular_basis(ell=4, rings=12):
    return GeneralLieStokesOperator(ell,n_gl_theta=rings)


def run_case(args):
    fam,cells,capacity,picards,ref,epsilon=args
    return solve_case(fam,cells,capacity,picards,ref,epsilon)


def solve_case(fam,cells,capacity,picards,ref,epsilon,*,ell=4,rings=12,detailed=False):
    mod=_solver(ref) if ref else live
    extra={} if ref else {"max_substep_depth":capacity,"stage_rate_collision":False,"picard_rtol":None}  # R106 pin: keep R105 semantics
    cfg=mod.CoupledSolverConfig(ell_max=ell,n_cells=cells,n_picard=picards,epsilon=epsilon,
                                substeps_per_cell=2,record_history=True,**extra)
    t0=time.perf_counter()
    res=mod.solve_coupled_einstein_boltzmann(fam,cfg,lie_op=angular_basis(ell,rings))
    seconds=time.perf_counter()-t0
    history=res.history["picard_iterations"][-1]
    qf=history["q_over_E_fluid"][0]
    error=np.linalg.norm(history["q_over_E_sky"][0]-qf,axis=1)
    scale=np.linalg.norm(qf,axis=1)
    rel=np.divide(error,scale,out=np.zeros_like(error),where=(scale>0))
    field=np.concatenate([np.abs(qf).ravel(),np.abs(res.final_state)])
    if (not np.isfinite(field).all() or not np.isfinite(rel).all()
            or (fam=="FLRW" and np.any(field))):
        raise FloatingPointError(f"invalid final state or FLRW null for {fam}")
    row={"family":fam,"revision":"R104" if ref else "R105","n_cells":cells,"min_substeps":2,
            "max_substep_depth":capacity,"n_picard":picards,"ell_max":ell,"gl_rings":rings,
            "epsilon":epsilon,"relative_first":float(rel[0]),"relative_peak":float(rel.max()),
            "relative_final":float(rel[-1]),"absolute_final":float(error[-1]),
            "first_cell_depth":float(history["delta_tau"][0]),
            "n_photon_substeps_final_sweep":int(np.sum(history.get("photon_substeps",[2*cells]))),
            "C2T":float(res.cl_final["T"][2]),"C2E":float(res.cl_final["E"][2]),
            "C2B":float(res.cl_final["B"][2]),"max_codazzi":res.max_codazzi_residual,
            "max_hamiltonian":res.max_hamiltonian_residual,"max_stokes_reality":res.max_stokes_reality_err,
            "seconds":seconds}

    if detailed:
        # A relative residual has no scale on the FLRW zero-flux solution.
        # Select a defined relative peak when possible, otherwise the largest
        # absolute residual. Preserve the vector and reference magnitude.
        valid=scale>0
        peak=int(np.argmax(np.where(valid,rel,-1))) if valid.any() else int(np.argmax(error))
        signed={}
        for label,i in (("first",0),("peak",peak),("final",len(qf)-1)):
            qs=history["q_over_E_sky"][0,i]
            signed[label]={"cell_index":i,"N_end":float(history["N_end"][i]),
                           "sky":qs.tolist(),"fluid":qf[i].tolist(),"sky_minus_fluid":(qs-qf[i]).tolist(),
                           "absolute_norm":float(error[i]),"relative_norm":float(rel[i]) if valid[i] else None}
        for label, sample in signed.items():
            row["relative_"+label] = sample["relative_norm"]
        row["signed_photon_q_over_E"]=signed
        row["picard_pressure_change"]=res.picard_pi_rel_change
        row["max_jacobi"]=res.max_jacobi_residual
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--baseline-file",type=Path,help="offline copy of R104 coupled solver")
    p.add_argument("--workers",type=int,default=4)
    args=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        ref=Path(tmp)/"htt/bass/transport/coupled_r104.py"
        ref.parent.mkdir(parents=True)
        source=(args.baseline_file.read_bytes() if args.baseline_file else
                subprocess.check_output(["git","show",BASE_COMMIT+":"+SOLVER_PATH],cwd=ROOT))
        if hashlib.sha256(source).hexdigest()!=BASE_SHA:
            raise ValueError("reference file does not match R104")
        ref.write_bytes(source)
        tasks=[("FLRW",24,1.,2,None,0.)]
        for fam in ("VII_h","IX"):
            tasks.extend((fam,n,cap,4,str(ref) if baseline else None,2e-4)
                         for n,cap,baseline in [(24,None,True),(24,None,False),(24,1.,False),
                                                (24,.5,False),(48,None,True),(48,1.,False),(96,1.,False)])
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            rows=list(pool.map(run_case,tasks))
    comparisons={}
    ok=True
    for fam in ("VII_h","IX"):
        sub=[r for r in rows if r["family"]==fam]
        old,uniform,coarse,tight,mid_old,mid,fine=sub
        parity=max(abs(uniform[k]-old[k])/max(abs(old[k]),1e-30)
                   for k in ("C2T","C2E","C2B","relative_first","relative_final"))
        # The reference below measures grid sensitivity at fixed angular/feedback resolution.
        comparisons[fam]={"uniform_switch_max_relative_difference":parity,
            "first_error_reduction_N24":old["relative_first"]/coarse["relative_first"],
            "terminal_error_reduction_N24":old["relative_final"]/coarse["relative_final"],
            "first_error_reduction_N48":mid_old["relative_first"]/mid["relative_first"],
            "terminal_error_reduction_N48":mid_old["relative_final"]/mid["relative_final"],
            "C2T_relative_to_R105_N96":{"R104_N24":old["C2T"]/fine["C2T"]-1,
                                                 "R105_N24":coarse["C2T"]/fine["C2T"]-1,
                                                 "R104_N48":mid_old["C2T"]/fine["C2T"]-1,
                                                 "R105_N48":mid["C2T"]/fine["C2T"]-1},
            "terminal_change_half_depth_N24":tight["relative_final"]-coarse["relative_final"]}
        ok &= parity<1e-6 and coarse["relative_first"]<old["relative_first"] and coarse["relative_final"]<old["relative_final"]
    payload={"status":"pass_scoped" if ok else "review","reference_commit":BASE_COMMIT,
             "reference_solver_sha256":BASE_SHA,"candidate_solver_sha256":hashlib.sha256(Path(live.__file__).read_bytes()).hexdigest(),
             "scope":"homogeneous photons only, independently integrated angular and fluid q/E; same outer mesh and geometry per comparison",
             "frozen_photon_only_fraction_neutrino":0.,"workers":args.workers,"python":platform.python_version(),
             "numpy":np.__version__,"scipy":scipy.__version__,"OPENBLAS_NUM_THREADS":os.getenv("OPENBLAS_NUM_THREADS"),
             "comparisons":comparisons,"runs":rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2,allow_nan=False)+"\n")
    print(json.dumps(comparisons))
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
