"""Exact-source evidence and finite algebra for the selected initial-data space."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
def main():
    root=Path.home()/"workdir/htt_external_physics_20261015/reference_code/AniCLASS"
    git=lambda *a:subprocess.check_output(["git","-C",str(root),*a])
    rev=git("rev-parse","HEAD").decode().strip()
    assert rev=="be1e43fcb1d7549710ba3ca2baa74bb0216bd228"
    blob=git("show",rev+":source/perturbations.c")
    for phrase in (b"h_corr_2 = - ppw->pv->y",b"(6 + 8./5.*rho_fs/rho_r) *tau*tau",b"index_pt_gwdot] = 2.*h_corr_2/tau",b"index_pt_l2_ur] = -h_corr_2"):
        assert phrase in blob
    sha=lambda b:hashlib.sha256(b).hexdigest()
    rng=np.random.default_rng(125);res=0.;rank=[]
    for _ in range(100):
        om=float(rng.uniform(.1,.8));fb=float(rng.uniform(.05,.5));og=float(rng.uniform(.01,.1));on=float(rng.uniform(.01,.1));C=rng.uniform(0,.1)+1j*rng.uniform(0,.1)
        B=np.array([[1,0,0,0],[0,0,1,0],[0,0,0,1],[C/om,1-fb,-4*og/(3*om),-4*on/(3*om)],[C/om,-fb,-4*og/(3*om),-4*on/(3*om)]])
        row=np.array([-C,4*og/3,4*on/3,om*fb,om*(1-fb)])
        res=max(res,float(np.max(abs(row@B))));rank.append(int(np.linalg.matrix_rank(B)))
    assert res<1e-14 and min(rank)==4
    # Leading RD expansion coefficients; exact cancellation in the retained order.
    k,a,fn=.01,.005,.4082846699067635
    s=-4*k*(k-1j*a)/(6+8*fn/5);v=-2*s
    eq=2*s-(-s-2*k*(k-1j*a)+.4*fn*v)
    assert abs(eq)<1e-16
    out={"constraint_samples":100,"max_residual":res,"ranks":sorted(set(rank)),"regular_RD_coefficient_probe":{"s_per_d0_ri":[s.real,s.imag],"V_per_f2_ri":[v.real,v.imag],"residual":abs(eq),"scope":"algebraic leading RD identity, not z=1600 initial data"},
        "aniclass":{"commit":rev,"source_blob_sha256":sha(blob),"binary_sha256":sha((root/"class").read_bytes()),"source_path":"source/perturbations.c","lines":"6983-7034","actual_source_checked":True}}
    print(json.dumps(out,indent=2,allow_nan=False))
if __name__=="__main__":main()
