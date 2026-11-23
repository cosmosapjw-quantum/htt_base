"""Replay a compiled, regular AniCLASS tensor on BASS with the donor metric and opacity."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry

SOURCE_HEAD = "be1e43fcb1d7549710ba3ca2baa74bb0216bd228"
PARAMS = {
    "hierarchy":"tam", "statistics":"non_stochastic", "non_stochastic_type":"bianchi",
    "output":"tCl,pCl", "modes":"t", "Omega_k":"-0.01", "z_reio":"7.6711",
    "gauge":"synchronous", "k_output_values":"0.001", "l_max_tensors":"16",
    "multipole_normalization":"observable", "non_stochastic_format":"class",
    "write_background":"yes", "write_thermodynamics":"yes",
    "l_max_g_ten":"30", "l_max_pol_g_ten":"30", "l_max_ur_ten":"30",
    "radiation_streaming_approximation":"3", "perturbations_sampling_stepsize":"0.01",
    "tight_coupling_trigger_tau_c_over_tau_h":"0.005", "start_small_omega_tau":"0.001",
    "tol_perturbations_integration":"1e-9","hyper_x_min":"1e-7",
}


def load_history(folder):
    paths = {}
    for key, suffix in (("perturbations","perturbations_k0_t.dat"),
                        ("opacity","thermodynamics.dat"),("background","background.dat"),
                        ("observable","alm_q0_t.dat")):
        matches = list(folder.glob("*"+suffix))
        if len(matches) != 1:
            raise ValueError(f"expected one {suffix}, found {len(matches)}")
        paths[key] = matches[0]
    with paths["perturbations"].open() as stream:
        k = float(re.search(r"k\s*=\s*([^ ]+)", stream.readline())[1])
        header = stream.readline()
        if not all(f"{i}:{name}" in header for i,name in [(1,"tau [Mpc]"),(2,"a"),(5,"Re@Hdot"),(7,"Re@Theta_2"),(9,"Re@E_2"),(11,"Re@B_2")]):
            raise ValueError("incompatible raw tensor history header")
    p = np.loadtxt(paths["perturbations"])
    # Bianchi IX homogeneous tensor q=sqrt(9K), k=sqrt(6K), has no ell>=3 sources.
    if not np.isfinite(p).all() or np.max(abs(p[:,12:]))>1e-12 or np.any(np.diff(p[:,0])<=0):
        raise ValueError("nonfinite, unsorted, or nonclosed external quadrupole history")
    a = np.loadtxt(paths["opacity"],usecols=[2,4])
    a = a[np.argsort(a[:,0])]
    if np.any(np.diff(a[:,0])<=0) or np.min(a[:,1])<0:
        raise ValueError("positive conformal opacity on an ordered grid is required")
    bg = np.loadtxt(paths["background"],usecols=[0,3])
    h0 = bg[np.argmin(abs(bg[:,0])),1]
    radius_inverse = h0*np.sqrt(-float(PARAMS["Omega_k"]))
    if not np.isclose(k,np.sqrt(6)*radius_inverse,rtol=1e-10,atol=0):
        raise ValueError("donor does not identify its closed homogeneous tensor wavenumber")
    if a[0,0]>p[0,0] or a[-1,0]<p[-1,0]-1e-7:
        raise ValueError("opacity history misses perturbation trajectory")
    return p,a,radius_inverse,{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()}


def replay(folder):
    p,a,rinv,hashes=load_history(folder)
    op=GeneralLieStokesOperator(2,n_gl_theta=8)
    idx=[op.idx[c][2,2] for c in ("T","E","B")]
    # Mpc clock c*eta. Give BASS the IX spatial connection in inverse Mpc,
    # so delta_N in advance_cell is a physical conformal-length increment here.
    geom=LieGeometry(np.zeros((3,3)), np.zeros(3),2*rinv*np.eye(3))
    time=p[:,0]
    z=1/p[:,1]-1
    # All comparison points are actual source rows; start after tight coupling.
    rows=np.array([int(np.argmin(abs(z-v))) for v in (1600.,1100.,600.,8.,0.)])
    if not np.all(np.diff(rows)>0) or abs(p[rows[0],10]) == 0:
        raise ValueError("need nontrivial starting B quadrupole after tight coupling")
    mapping=np.array([1.,-1.,-1.])  # raw source tensor E/B -> BASS harmonic block
    ref_state=(p[:,6:12:2]+1j*p[:,7:12:2])*mapping
    hp=PchipInterpolator(time,p[:,4],extrapolate=False)
    hp_im=PchipInterpolator(time,p[:,5],extrapolate=False)
    opacity=PchipInterpolator(a[:,0],a[:,1],extrapolate=False)
    peaks=np.max(abs(ref_state[rows[0]:rows[-1]+1]),axis=0)
    records=[]
    for resolution in (64,128,256,512):
        base=np.geomspace(time[rows[0]],time[rows[-1]],resolution+1)
        knots=np.union1d(base,time[rows])
        y=np.zeros(op.dim,complex); y[idx]=ref_state[rows[0]]
        checkpoints=[y[idx].copy()]
        for ta,tb in zip(knots[:-1],knots[1:]):
            dt=tb-ta
            mid=.5*(ta+tb)
            forcing=np.zeros(op.dim,complex)
            forcing[idx[0]]=-dt*complex(hp(mid), hp_im(mid))
            y=op.advance_cell(y,dt,geom,float(dt*opacity(mid)),source_increment=forcing)
            if tb in time[rows[1:]]:
                checkpoints.append(y[idx].copy())
        actual=np.array(checkpoints)
        err=abs(actual-ref_state[rows])/peaks
        records.append({"nominal_cells":resolution,"actual_cells":len(knots)-1,
                        "max_checkpoints_error_by_channel_peak":np.max(err,axis=0).tolist(),
                        "final_raw_TEB_real":(actual[-1]*mapping).real.tolist()})
    final=np.array(records[-1]["max_checkpoints_error_by_channel_peak"])
    first=np.array(records[0]["max_checkpoints_error_by_channel_peak"])
    return {"model":"regular Bianchi IX tensor m=2, native photons on the externally supplied evolving metric; no independent Einstein or REC evolution",
            "curvature_radius_Mpc":1./rinv,"signed_basis_raw_TEB_to_native":mapping.tolist(),
            "matched_redshifts":z[rows].tolist(),"conformal_Mpc": time[rows].tolist(),
            "opacity_at_checkpoints_Mpc_inv":opacity(time[rows]).tolist(),"input_hashes":hashes,
            "external_TEB_checkpoints_real":(ref_state[rows]*mapping).real.tolist(),
            "external_TEB_checkpoints_imag":(ref_state[rows]*mapping).imag.tolist(),
            "max_ell3_through_ell6_abs":float(np.max(abs(p[:,12:]))),"channel_peak_scales":peaks.tolist(),
            "refinements":records,"pass_scoped":bool(np.all(final<2e-4) and np.all(final<first))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aniclass-root",required=True,type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    root=args.aniclass_root.resolve(); binary=root/"class"
    source = subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if source!=SOURCE_HEAD:
        raise ValueError("unexpected AniCLASS revision")
    with tempfile.TemporaryDirectory(prefix="htt-r103-closed-tensor-") as tmp:
        folder=Path(tmp); ini=folder/"ix.ini"
        ini.write_text("".join(f"{k} = {v}\n" for k,v in {**PARAMS,"root":str(folder/"out_")}.items()))
        run=subprocess.run([str(binary),str(ini)],cwd=root,env={**os.environ,"OMP_NUM_THREADS":"1"},
                           stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
        if run.returncode!=0:
            raise RuntimeError(run.stdout[-2200:])
        r=replay(folder)
    r.update({"aniclass_commit":source,"binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
              "ini_parameters":PARAMS,"OMP_NUM_THREADS":1})
    from bass.transport import general_lie_stokes
    r["native_transport_git_blob"]=subprocess.check_output(
        ["git","hash-object",general_lie_stokes.__file__],text=True).strip()
    value=json.dumps(r,indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(value)
    else:
        print(value,end="")
    return 0 if r["pass_scoped"] else 1


if __name__=="__main__":
    raise SystemExit(main())
