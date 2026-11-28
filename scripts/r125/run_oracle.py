"""Source-locked batch propagation with finite angular/tolerance ladder."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from common.initial_data_response import build_system,integrate_columns,observe_columns,response_matrix
from scripts.r120.native_scan import sources
from scripts.r125.verify_sources import DOC
def sha(b):return hashlib.sha256(b).hexdigest()
def un(v):
    a=np.asarray(v);return a[...,0]+1j*a[...,1]
def norm(x):return float(np.linalg.norm(x))
def main(scratch):
    _,table,ref,_=sources(scratch);lock=json.loads((DOC/"C1.json").read_text())
    assert sha(table.read_bytes())==lock["opacity_sha256"]
    c=json.loads((DOC/"C2_CONSTANTS.json").read_text());tab=np.loadtxt(table,skiprows=1)
    root=DOC/"oracle";root.mkdir(exist_ok=False);records={};prior={}
    p123=DOC.parent/"R123_CURVED_LINEAR_ORACLE_20261128/C6_ORACLE.json"
    p124=DOC.parent/"R124_CODAZZI_LINEAR_SECTORS_20261128/C6_ORACLE.json"
    r123=json.loads(p123.read_text())["runs"];r124=json.loads(p124.read_text())["runs"]
    frames=("normal","host","radiation","spectator")
    for family,a in (("VII0",0.),("VIIh",.005)):
        for m in (0,1,2):
            key=f"{family}_m{m}"
            for L,tol,step,tag in ((12,2e-9,.025,"L12"),(20,2e-9,.025,"L20"),(20,2e-11,.01,"tight"),(20,2e-11,.01,"heldout")):
                t=time.monotonic();name=key+"_"+tag
                sys=build_system(ref["cosmology_anchors"],ref["neutrino_fraction_hyrec"],c["baryon_fraction"],tab,c["c_sigma_T_m3_s"],.01,a,m,L)
                labels=sys["labels"];weights=np.linspace(-.3,.4,len(labels))
                if m>0:weights=weights+1j*np.linspace(.2,-.1,len(labels))
                initial=(sys["basis"]@weights)[:,None] if tag=="heldout" else None
                r=integrate_columns(sys,initial=initial,rtol=tol,max_step=step)
                skies={f:observe_columns(r["endpoint"],sys,f) for f in frames}
                path=root/(name+".npz")
                np.savez_compressed(path,initial=r["initial"],endpoint=r["endpoint"],eta=r["eta"],constraint=r["constraint_history"],
                     labels=np.asarray(labels),weights=weights if tag=="heldout" else np.empty(0),**{"sky_"+f:v for f,v in skies.items()})
                records[name]={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"m":m,"L":L,"labels":labels,
                    "columns":r["endpoint"].shape[1],"nfev":r["nfev"],"rtol":tol,"max_step":step,
                    "max_constraint":r["max_constraint"],"wall_s":time.monotonic()-t,
                    "host_norms":np.linalg.norm(skies["host"],axis=(0,1)).tolist()}
                if tag=="tight":
                    if m<2:refsky=un(r124[key+"_L20_tight"]["sky_ri"]["host"])
                    else:refsky=np.vstack((np.zeros((3,3),complex),un(r123[family+"_L20_tight"]["sky_ri"])))
                    prior[key]=norm(skies["host"][:,:,0]-refsky)/norm(refsky)
                print(name,"columns",r["endpoint"].shape[1],"constraint",r["max_constraint"],"seconds",round(records[name]["wall_s"],2),flush=True)
    out={"runs":records,"prior_shear_relative":prior,"prior_sha256":{"R123":sha(p123.read_bytes()),"R124":sha(p124.read_bytes())},
        "opacity_sha256":lock["opacity_sha256"],"constants_sha256":sha((DOC/"C2_CONSTANTS.json").read_bytes()),
        "scope":"finite selected initial-data basis, no native radiation IC capability or calibrated likelihood"}
    (DOC/"C6_ORACLE.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print("PRIOR_SHEAR",json.dumps(prior),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
