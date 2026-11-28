"""Exact-source fixed-clock nodal window tangents, finite L comparison."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from common.physical_memory_budget import build_context,observation
from common.initial_data_response import observe_columns
from common.opacity_memory_kernel import NodalWindows,integrate_windows
from scripts.r120.native_scan import sources
from scripts.r127.plan import groups,LABELS
from scripts.r127.verify_sources import DOC
def sha(b):return hashlib.sha256(b).hexdigest()
def inputs(scratch):
    _,table,ref,_=sources(scratch);lock=json.loads((DOC/"C1.json").read_text());c=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    assert sha(table.read_bytes())==lock["opacity_sha256"]==c["original_opacity_sha256"]
    return dict(anchors=ref["cosmology_anchors"],f_nu=ref["neutrino_fraction_hyrec"],f_b=c["baryon_fraction"],table=np.loadtxt(table,skiprows=1),c_sigma=c["c_sigma_T_m3_s"],k0=.01)
def context(inp,fam,m,L):
    return build_context(**inp,a0=.005 if fam=="VIIh" else 0.,m=m,L=L)
def seed_matrix(c,fam):
    s=c["system"];m=c["m"];labels=s["labels"];w=np.linspace(-.3,.4,len(labels)).astype(complex)
    if m:w+=1j*np.linspace(.2,-.1,len(labels))
    weights=[w];names=["heldout"]
    if fam=="VIIh" and m in (1,2):
        label="relative_dust" if m==1 else "metric";v=np.zeros(len(labels),complex);v[labels.index(label)]=1
        weights.append(v);names.append(label)
    return np.column_stack(weights),names
def main(scratch):
    inp=inputs(scratch);w=NodalWindows(inp["table"],groups(inp["table"]));root=DOC/"tangent";root.mkdir(exist_ok=False)
    prior=DOC.parent/"R126_PHYSICAL_MEMORY_LOSS_20261128";pr=json.loads((prior/"C6_BUDGET.json").read_text());const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    assert sha((prior/"C6_BUDGET.json").read_bytes())==const["R126_budget_sha256"]
    records={}
    for fam in ("VII0","VIIh"):
        for m in (0,1,2):
            for L,tol,step in ((12,2e-9,.025),(20,2e-11,.015)):
                key=f"{fam}_m{m}_L{L}";start=time.monotonic();c=context(inp,fam,m,L);s=c["system"];V,names=seed_matrix(c,fam)
                Y0=s["basis"]@V;r=integrate_windows(c,w,Y0,rtol=tol,max_step=step);O=observation(c)
                z=O@r["end"];dz=np.stack([O@q for q in r["tangent"]],axis=0)
                goal=np.stack([np.real(np.einsum("ip,wip->wp",z[i::3].conj(),dz[:,i::3,:])) for i in range(3)])
                sky=observe_columns(r["end"],s,"host");dsky=np.stack([observe_columns(q,s,"host") for q in r["tangent"]])
                path=root/(key+".npz")
                np.savez_compressed(path,initial=Y0,endpoint=r["end"],tangent=r["tangent"],weights=V,names=np.array(names),eta=r["eta"],constraint=r["constraint"],tau=r["tau"],z=z,dz=dz,goal=goal,sky=sky,dsky=dsky)
                rec={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"family":fam,"m":m,"L":L,"seeds":names,"rtol":tol,"max_step":step,"nfev":r["nfev"],"max_constraint":r["max_constraint"],"tau":r["tau"].tolist(),"goal_derivative":goal[:,:,0].tolist(),"wall_s":time.monotonic()-start}
                if L==20:
                    b=pr["runs"][f"{fam}_m{m}_L20_s1"];bp=prior/b["path"];assert sha(bp.read_bytes())==b["sha256"]
                    with np.load(bp,allow_pickle=False) as a:target=a["response_host"]@V
                    rec["prior_R126_sky_relative"]=float(np.linalg.norm(z-target)/np.linalg.norm(target));rec["prior_npz_sha256"]=b["sha256"]
                records[key]=rec;print(key,"tau",np.round(r["tau"],6).tolist(),"goal",np.round(goal[:,:,0].sum(axis=0),8).tolist(),"seconds",round(rec["wall_s"],2),flush=True)
    out={"runs":records,"source_sha256":const["original_opacity_sha256"],"plan_sha256":sha((DOC/"SCAN_PLAN.json").read_bytes()),"windows":list(LABELS),"scope":"signed finite-start fixed-background nodal window tangents"}
    (DOC/"C6_TANGENT.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
