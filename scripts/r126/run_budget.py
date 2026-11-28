"""Forward physical-size budgets on exact source-bound opacity interventions."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from common.physical_memory_budget import build_context,integrate_budget,metric_weights,collision_action,observation
from common.initial_data_response import observe_columns
from scripts.r120.native_scan import sources
from scripts.r126.verify_sources import DOC
from scripts.r126.plan import make
def sha(b):return hashlib.sha256(b).hexdigest()
def inputs(scratch):
    _,table,ref,_=sources(scratch);lock=json.loads((DOC/"C1.json").read_text());c=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    assert sha(table.read_bytes())==lock["opacity_sha256"]==c["original_opacity_sha256"]
    return dict(anchors=ref["cosmology_anchors"],f_nu=ref["neutrino_fraction_hyrec"],f_b=c["baryon_fraction"],table=np.loadtxt(table,skiprows=1),c_sigma=c["c_sigma_T_m3_s"],k0=.01)
def context(inp,family,m,L):return build_context(**inp,a0=.005 if family=="VIIh" else 0.,m=m,L=L)
def tag(x):return {0.:"0",.25:"025",.5:"05",1.:"1"}[float(x)]
def main(scratch):
    inp=inputs(scratch);root=DOC/"budget";root.mkdir(exist_ok=False)
    plan=make();records={};local={};prior={}
    p125=DOC.parent/"R125_CONSTRAINED_INITIAL_DATA_20261128"
    prev=json.loads((p125/"C6_ORACLE.json").read_text());const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    assert sha((p125/"C6_ORACLE.json").read_bytes())==const["R125_oracle_sha256"]
    for fam in ("VII0","VIIh"):
        for m in (0,1,2):
            key=f"{fam}_m{m}"
            for L,scales,tol,step in ((plan["oracle_L"],plan["oracle_scales"],2e-10,.025),(plan["tight_L"],plan["tight_scales"],2e-11,.015)):
                c=context(inp,fam,m,L);s=c["system"];eye=np.eye(len(s["basis"]),dtype=complex)
                mismatch=0.;mineig=0.;sym=0.
                for t in inp["table"][np.unique(np.linspace(0,len(inp["table"])-1,25,dtype=int)),0]:
                    C=collision_action(c,t,eye);A=s["rhs"](t,eye)-c["zero"]["rhs"](t,eye)
                    mismatch=max(mismatch,float(np.linalg.norm(C-A)/max(1.,np.linalg.norm(C))))
                    w,_=metric_weights(c,t);Q=w[:,None]*C
                    eig=np.linalg.eigvalsh(-(Q+Q.conj().T));mineig=min(mineig,float(eig.min()/max(1.,eig.max())))
                    sym=max(sym,float(np.linalg.norm(Q-Q.conj().T)/max(1.,np.linalg.norm(Q))))
                local[f"{key}_L{L}"]={"relative_generator_gap":mismatch,"min_scaled_dissipation_eigenvalue":mineig,"weighted_symmetry_relative":sym,"source_knots":25}
                if mismatch>1e-12 or mineig< -1e-12 or sym>1e-12:raise RuntimeError("collision matrix mismatch")
                for scale in scales:
                    start=time.monotonic();name=f"{key}_L{L}_s{tag(scale)}";r=integrate_budget(c,scale,rtol=tol,max_step=step)
                    if r["closure_relative"]>2e-8 or r["min_D_eigenvalue"]< -1e-9:raise RuntimeError(f"budget invariant {name}: {r['closure_relative']}, {r['min_D_eigenvalue']}")
                    Y=r["endpoint"];frames={f:observation(c,f)@Y for f in ("normal","host","radiation","spectator")}
                    full=observe_columns(Y,s,"host")
                    path=root/(name+".npz")
                    arrays={k:r[k] for k in ("initial","endpoint","D","N","M","J","wi","wf","whitener","eta","constraint")}
                    np.savez_compressed(path,**arrays,labels=np.array(s["labels"]),sky_host=full,**{"response_"+f:z for f,z in frames.items()})
                    summary={k:v for k,v in r.items() if k not in arrays}
                    records[name]={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"family":fam,"m":m,"L":L,"labels":s["labels"],**summary,"wall_s":time.monotonic()-start}
                    if L==20 and scale==1.:
                        pr=prev["runs"][key+"_tight"];f=p125/pr["path"]
                        assert sha(f.read_bytes())==pr["sha256"]
                        with np.load(f,allow_pickle=False) as old:
                            z=old["sky_host"];prior[key]={"relative_sky":float(np.linalg.norm(full-z)/np.linalg.norm(z)),"prior_npz_sha256":pr["sha256"]}
                    print(name,"tau",round(r["tau"],5),"closure",r["closure_relative"],"PSD",r["min_D_eigenvalue"],"secs",round(records[name]["wall_s"],2),flush=True)
    out={"runs":records,"local_collision_audit":local,"prior_R125_baseline":prior,"opacity_sha256":const["original_opacity_sha256"],"constants_sha256":sha((DOC/"C2_CONSTANTS.json").read_bytes()),"plan_sha256":sha((DOC/"SCAN_PLAN.json").read_bytes()),"scope":"finite Galerkin physical-size budgets, scales other than one are controlled opacity interventions"}
    (DOC/"C6_BUDGET.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print("TOTAL",len(records),"prior",json.dumps(prior),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
