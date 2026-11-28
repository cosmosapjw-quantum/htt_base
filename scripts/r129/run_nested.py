"""New finest source-resolved tangent integrations; nested aggregation."""
import argparse,json,time,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from common.profiled_opacity_shapes import nested_groups,NodalBasis,nodal_metric,integrate_nested,aggregation,compact_sky
from common.initial_data_response import observe_columns
from common.physical_memory_budget import observation
from common.opacity_memory_kernel import NodalWindows
from common.fixed_tau_shapes import source_metrics
from scripts.r127.run_tangent import inputs,context,seed_matrix
from scripts.r127.plan import groups
from scripts.r129.verify_sources import DOC
from scripts.r128.spectra import read,norm,sha

def locks():
    const=json.loads((DOC/"C2_CONSTANTS.json").read_text());p={}
    for k,v in const["prior_receipts"].items():
        f=DOC.parent/v["path"];assert sha(f.read_bytes())==v["sha256"];p[k]=(f.parent,json.loads(f.read_text()))
    return p

def task(args):
    scratch,fam,m,L=args;inp=inputs(scratch);g=groups(inp["table"]);w=NodalBasis(inp["table"],nested_groups(g));c=context(inp,fam,m,L);s=c["system"]
    W,names=seed_matrix(c,fam);y=s["basis"]@W[:,0]
    start=time.monotonic();tol=2e-9 if L==12 else 2e-11;step=.025 if L==12 else .015
    r=integrate_nested(c,w,y,rtol=tol,max_step=step);O=observation(c)
    sky=observe_columns(r["end"][:,None],s,"host")[:,:,0];dsky=observe_columns(r["tangent"],s,"host")
    np.testing.assert_allclose(compact_sky(sky,m),O@r["end"],rtol=1e-12,atol=1e-13)
    np.testing.assert_allclose(compact_sky(dsky,m),O@r["tangent"],rtol=1e-12,atol=1e-13)
    prior=locks()["R127"];key=f"{fam}_m{m}_L{L}";a=read(prior[0],prior[1]["runs"][key])
    agg=np.einsum("mcg,gk->kmc",dsky,aggregation(4))
    gap=norm(agg-a["dsky"][:4,:,:,0])/norm(a["dsky"][:4,:,:,0])
    bg=norm(sky-a["sky"][:,:,0])/norm(a["sky"][:,:,0])
    path=DOC/"nested"/(key+".npz");np.savez_compressed(path,initial=y,weights=W[:,0],endpoint=r["end"],tangent=r["tangent"],sky=sky,dsky=dsky,eta=r["eta"],constraint=r["constraint"])
    rec={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"family":fam,"m":m,"L":L,"rtol":tol,"max_step":step,"nfev":r["nfev"],"max_constraint":r["max_constraint"],"coarse_window_relative":gap,"baseline_relative":bg,"prior_tangent_sha256":prior[1]["runs"][key]["sha256"],"wall_s":time.monotonic()-start}
    print(key,"aggregate gap",gap,"baseline",bg,"seconds",round(rec["wall_s"],2),flush=True)
    return key,rec

def main(scratch):
    inp=inputs(scratch);g=groups(inp["table"]);ng=nested_groups(g);w=NodalBasis(inp["table"],ng)
    root=DOC/"nested";root.mkdir(exist_ok=False);arr={"eta":inp["table"][:,0],"xe":inp["table"][:,1],"groups":ng};geo={}
    for fam in ("VII0","VIIh"):
        c=context(inp,fam,0,12);r=nodal_metric(c,w);r8=nodal_metric(c,w,8);old=source_metrics(c,NodalWindows(inp["table"],g))
        E=aggregation(4);np.testing.assert_allclose(E.T@r["t"],old["t"][:4],rtol=1e-12,atol=1e-13);np.testing.assert_allclose(E.T@r["M_tau"]@E,old["M_tau"][:4,:4],rtol=1e-12,atol=1e-13)
        geo[fam]={"tau":r["tau"],"t":r["t"].tolist(),"GL8_12_abs":max(float(np.max(abs(r[k]-r8[k]))) for k in ("t","M_tau","M_clock"))}
        for k in ("t","M_tau","M_clock"):arr[fam+"_"+k]=r[k]
    for n in (4,8,16):arr["aggregate_"+str(n)]=aggregation(n)
    path=DOC/"C6_METRIC.npz";np.savez_compressed(path,**arr)
    jobs=[(scratch,fam,m,L) for fam in ("VII0","VIIh") for m in (0,1,2) for L in (12,20)]
    with ProcessPoolExecutor(max_workers=3) as pool:records=dict(pool.map(task,jobs))
    out={"runs":records,"geometry":geo,"metric_sha256":sha(path.read_bytes()),"counts_by_node_group":np.bincount(ng).tolist(),"scope":"16 active nodal groups, tail locked; aggregate levels 4/8/16; fixed background"}
    (DOC/"C6_NESTED.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
