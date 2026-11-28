"""Metric-constrained signed opacity-shape spectra, locked R127 transfer arrays."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from common.fixed_tau_shapes import source_metrics,constrained_basis,real_map
from common.opacity_memory_kernel import NodalWindows
from common.physical_memory_budget import metric_weights
from scripts.r127.run_tangent import inputs,context
from scripts.r127.plan import groups,LABELS
from scripts.r128.verify_sources import DOC
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(a):return float(np.linalg.norm(a))
def read(p,r):
    f=p/r["path"];assert sha(f.read_bytes())==r["sha256"]
    with np.load(f,allow_pickle=False) as x:return {k:x[k] for k in x.files}
def project_amplitude(A,b):
    q=np.r_[b.real.ravel(),b.imag.ravel()]
    return A-np.outer(q,q@A)/(q@q)
def main(scratch):
    inp=inputs(scratch);w=NodalWindows(inp["table"],groups(inp["table"]))
    const=json.loads((DOC/"C2_CONSTANTS.json").read_text());old=DOC.parent/"R127_OPACITY_MEMORY_KERNEL_20261128"
    assert sha((old/"C6_TANGENT.json").read_bytes())==const["R127_tangent_sha256"]
    tr=json.loads((old/"C6_TANGENT.json").read_text())["runs"]
    geom={};out={};arrays={}
    active={"full":[0,1,2,3,4],"tail_locked":[0,1,2,3],"late_swap":[2,3]}
    for fam in ("VII0","VIIh"):
        c=context(inp,fam,0,20);q=source_metrics(c,w);q8=source_metrics(c,w,8)
        geom[fam]={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in q.items() if k!="nodal"}
        geom[fam]["GL8_12_max_abs"]=max(float(np.max(abs(q[k]-q8[k]))) for k in ("t","M_tau","M_clock","nodal"))
        for k in ("t","M_tau","M_clock","nodal"):arrays[fam+"_"+k]=q[k]
        assert abs(q["nodal"].sum()-q["tau"])<1e-10
        np.testing.assert_allclose(q["M_tau"]@np.ones(5),q["t"]/q["tau"],atol=2e-14)
        for m in (0,1,2):
            key=f"{fam}_m{m}";c=context(inp,fam,m,20);a=read(old,tr[key+"_L20"]);lo=read(old,tr[key+"_L12"])
            np.testing.assert_allclose(q["t"],a["tau"],rtol=1e-12,atol=1e-13)
            y=a["initial"][:,0];wi,_=metric_weights(c,0.);size=float(np.vdot(y,wi*y).real);scale=np.sqrt(size)
            d=a["dsky"][:,:,:,0]/scale;dl=lo["dsky"][:,:,:,0]/scale;sky=a["sky"][:,:,0]/scale;skylo=lo["sky"][:,:,0]/scale
            R=real_map(d);RL=real_map(dl);rows={}
            for metric in ("M_tau","M_clock"):
                rows[metric]={}
                for tag,act in active.items():
                    B=constrained_basis(q[metric],q["t"],act)
                    assert np.max(abs(q["t"]@B))<1e-10
                    np.testing.assert_allclose(B.T@q[metric]@B,np.eye(B.shape[1]),rtol=1e-12,atol=1e-12)
                    bb={}
                    for profile,A,AL in (("full",R,RL),("high",real_map(d[:,3:]),real_map(dl[:,3:])),("amplitude_profiled",project_amplitude(R,sky),project_amplitude(RL,skylo))):
                        X=A@B;XL=AL@B;u,s,vh=np.linalg.svd(X,full_matrices=False);V=B@vh.T
                        for j in range(V.shape[1]):
                            if V[np.argmax(abs(V[:,j])),j]<0:V[:,j]*=-1
                        gap=float(np.linalg.norm(X-XL,ord=2))
                        bb[profile]={"singular_values":s.tolist(),"empirical_op_difference":gap,"count_above_difference":int(np.sum(s>gap)),
                            "directions":V.tolist(),"max_depth_residual":float(np.max(abs(q["t"]@V)))}
                        arrays[f"{key}_{metric}_{tag}_{profile}_B"]=B
                        arrays[f"{key}_{metric}_{tag}_{profile}_X"]=X
                        arrays[f"{key}_{metric}_{tag}_{profile}_XL"]=XL
                    rows[metric][tag]=bb
            out[key]={"initial_physical_size":size,"prior_tight_sha":tr[key+"_L20"]["sha256"],"prior_coarse_sha":tr[key+"_L12"]["sha256"],"baseline_norm":norm(sky),"metrics":rows}
            print(key,"tau/full",rows["M_tau"]["full"]["full"]["singular_values"],"tail locked",rows["M_tau"]["tail_locked"]["full"]["singular_values"],"clock/tail",rows["M_clock"]["tail_locked"]["full"]["singular_values"],flush=True)
    path=DOC/"C6_SPECTRA.npz";np.savez_compressed(path,**arrays)
    out={"geometry":geom,"sectors":out,"npz_sha256":sha(path.read_bytes()),"scope":"conditional finite signed response; empirical discrepancies, no survey likelihood or prior"}
    (DOC/"C6_SPECTRA.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
