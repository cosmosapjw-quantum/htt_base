"""Independent backward channel goals and GL4/8 source-knot integration."""
import argparse,json,time
from pathlib import Path
import numpy as np
from common.opacity_memory_kernel import NodalWindows,goal_kernel
from scripts.r127.run_tangent import inputs,context,seed_matrix,sha
from scripts.r127.plan import groups,LABELS
from scripts.r127.verify_sources import DOC
def main(scratch):
    inp=inputs(scratch);w=NodalWindows(inp["table"],groups(inp["table"]));root=DOC/"kernel";root.mkdir(exist_ok=False)
    prior=DOC.parent/"R126_PHYSICAL_MEMORY_LOSS_20261128";pr=json.loads((prior/"C7_ADJOINT.json").read_text())["runs"];const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    assert sha((prior/"C7_ADJOINT.json").read_bytes())==const["R126_adjoint_sha256"]
    t=json.loads((DOC/"C6_TANGENT.json").read_text())["runs"];records={}
    for fam in ("VII0","VIIh"):
        for m in (0,1,2):
            key=f"{fam}_m{m}";start=time.monotonic();c=context(inp,fam,m,20);V,names=seed_matrix(c,fam);y=c["system"]["basis"]@V[:,0]
            r=goal_kernel(c,w,y,rtol=2e-11,max_step=.015)
            tr=t[key+"_L20"];tp=DOC/tr["path"];assert sha(tp.read_bytes())==tr["sha256"]
            with np.load(tp,allow_pickle=False) as a:
                g=a["goal"][:,:,0];z=a["z"][:,0];tau=a["tau"]
            delta=r["group_gradient"]-g;ref=max(np.linalg.norm(g),1e-30);gap=float(np.linalg.norm(delta)/ref)
            path=root/(key+".npz");arrays={k:v for k,v in r.items() if isinstance(v,np.ndarray)}
            np.savez_compressed(path,**arrays,groups=w.groups,source_eta=w.table[:,0],source_xe=w.table[:,1],tangent_goal=g)
            out={k:v for k,v in r.items() if k not in arrays}
            rec={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"tangent_sha256":tr["sha256"],**out,
                 "group_gradient":r["group_gradient"].tolist(),"absolute_mass":r["absolute_mass"].tolist(),"loss":r["loss"].tolist(),"tau":r["tau"].tolist(),"objective":r["objective"].tolist(),
                 "adjoint_tangent_relative":gap,"adjoint_tangent_abs_max":float(np.max(abs(delta))),"baseline_sky_relative":float(np.linalg.norm(r["z"]-z)/np.linalg.norm(z)),
                 "tau_gap_max":float(np.max(abs(r["tau"]-tau))),"global_derivative":float(r["group_gradient"].sum()),"wall_s":time.monotonic()-start}
            if key in pr:
                rec["prior_R126_global_gradient"]=pr[key]["gradient"];rec["prior_R126_global_abs_gap"]=abs(rec["global_derivative"]-pr[key]["gradient"])
            records[key]=rec
            print(key,"channel gradients",np.round(r["group_gradient"],9).tolist(),"gap",gap,"quad",r["quadrature_group_abs"],"global",rec["global_derivative"],"seconds",round(rec["wall_s"],2),flush=True)
    out={"runs":records,"windows":list(LABELS),"scope":"adjoint channel objectives, source-knot gradients and physical dissipation; not stochastic Fisher sensitivity"}
    (DOC/"C7_KERNEL.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
