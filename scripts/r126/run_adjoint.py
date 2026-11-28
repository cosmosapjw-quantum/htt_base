"""Separate forward/backward goal derivative, independent FD and transfer check."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from common.physical_memory_budget import adjoint_objective
from scripts.r126.run_budget import inputs,context
from scripts.r126.verify_sources import DOC
def sha(b):return hashlib.sha256(b).hexdigest()
def main(scratch):
    inp=inputs(scratch);report=json.loads((DOC/"C6_BUDGET.json").read_text())
    root=DOC/"adjoint";root.mkdir(exist_ok=False);records={}
    for fam,m in (("VII0",0),("VIIh",1),("VIIh",2)):
        key=f"{fam}_m{m}";t=time.monotonic();c=context(inp,fam,m,20)
        labels=c["system"]["labels"];w=np.linspace(-.3,.4,len(labels))
        if m:w=w+1j*np.linspace(.2,-.1,len(labels))
        r=adjoint_objective(c,1.,w,rtol=2e-11,widths=(.01,.003))
        br=report["runs"][key+"_L20_s1"];p=DOC/br["path"]
        assert sha(p.read_bytes())==br["sha256"]
        with np.load(p,allow_pickle=False) as b:
            R=b["response_host"];y=R@w;v=R.conj().T@r["z"]
            projection_gap=float(np.linalg.norm(r["z"]-y)/max(np.linalg.norm(y),1e-30))
            adjoint_gap=float(np.linalg.norm(r["initial_gradient"]-v)/max(np.linalg.norm(v),1e-30))
        path=root/(key+".npz")
        arrays={k:r.pop(k) for k in ("p0","z","initial_gradient","weights")}
        np.savez_compressed(path,**arrays)
        records[key]={**r,"projection_relative":projection_gap,"adjoint_transfer_relative":adjoint_gap,
                      "path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"budget_sha256":br["sha256"],"wall_s":time.monotonic()-t}
        print(key,"gradient",r["gradient"],"duality",r["duality_relative"],"adjoint map",adjoint_gap,"FD",r["fd"],flush=True)
    result={"runs":records,"scope":"independent forward/backward integration of terminal host squared sky objective; opacity multiplier derivative, no nonlinear microphysics sensitivity"}
    (DOC/"C7_ADJOINT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
