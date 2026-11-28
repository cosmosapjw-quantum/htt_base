"""Source-bound finite-start tensor oracle and convergence ladder."""
import argparse,gzip,hashlib,io,json,time
from pathlib import Path
import numpy as np
from common.curved_tensor_response import integrate_tensor,tensor_sky,F2
from scripts.r120.native_scan import sources
from scripts.r123.verify_sources import DOC
def sha(b):return hashlib.sha256(b).hexdigest()
def pack(x):
    return np.stack((np.asarray(x).real,np.asarray(x).imag),axis=-1).tolist()
def main(scratch):
    _,tab,ref,_=sources(scratch);lock=json.loads((DOC/"C1.json").read_text())
    assert sha(tab.read_bytes())==lock["opacity_sha256"]
    const=json.loads((DOC/"C2_CONSTANTS.json").read_text());table=np.loadtxt(tab,skiprows=1)
    p=DOC/"oracle";p.mkdir(exist_ok=False)
    out={}
    for name,k,a,L,tol,step in [("I_L8",0,0,8,2e-10,.02)]+[(f"{family}_L{L}",.01,a,L,2e-9,.03) for family,a in (("VII0",0.),("VIIh",.005)) for L in (8,12,20)]+[(f"{family}_L20_tight",.01,a,20,2e-11,.01) for family,a in (("VII0",0.),("VIIh",.005))]:
        t=time.monotonic()
        r=integrate_tensor(ref["cosmology_anchors"],ref["neutrino_fraction_hyrec"],table,const["c_sigma_T_m3_s"],k,a,L,rtol=tol,max_step=step)
        h=r.pop("history");x=r.pop("endpoint");sky=tensor_sky(x,L,8)
        buf=io.StringIO();np.savetxt(buf,np.column_stack((h[:,0].real,h[:,1:].real,h[:,1:].imag)),header="eta s_re d_re s_im d_im",fmt="%.17e")
        raw=buf.getvalue().encode();fn=name+".tsv.gz";(p/fn).write_bytes(gzip.compress(raw,mtime=0))
        out[name]={**r,"endpoint_ri":pack(x),"sky_ri":pack(sky),"sky_norm":float(np.linalg.norm(sky)),"channel_norms":np.linalg.norm(sky,axis=0).tolist(),"history_file":"oracle/"+fn,"history_raw_sha256":sha(raw),"wall_s":time.monotonic()-t}
        print(name,"norm",out[name]["sky_norm"],"channels",out[name]["channel_norms"],"nfev",r["nfev"],flush=True)
    def un(z):
        x=np.asarray(z);return x[...,0]+1j*x[...,1]
    old=DOC.parent/"R122_PHYSICAL_SOURCE_RESPONSE_20261128";r=json.loads((old/"C6_ORACLE.json").read_text())["methods"]["Radau"]
    s,al,b,v=r["endpoint"];i=un(out["I_L8"]["endpoint_ri"]);n=7
    flat=np.array([i[0],i[2]/F2,i[2+n]/(np.sqrt(6)*F2),i[2+3*n]/F2])
    flat_error=float(np.linalg.norm(flat-[s,al,b,v])/np.linalg.norm([s,al,b,v]))
    convergence={}
    for family in ("VII0","VIIh"):
        target=un(out[family+"_L20_tight"]["sky_ri"])
        convergence[family]={n:float(np.linalg.norm(un(out[n]["sky_ri"])-target)/np.linalg.norm(target)) for n in (family+"_L8",family+"_L12",family+"_L20")}
    report={"runs":out,"flat_I_relative_to_R122_Radau":flat_error,"R122_reference_sha256":sha((old/"C6_ORACLE.json").read_bytes()),"convergence_to_finite_L20_tight":convergence,"opacity_sha256":lock["opacity_sha256"],"constants_sha256":sha((DOC/"C2_CONSTANTS.json").read_bytes()),"scope":"finite Galerkin L and finite-start tensor derivative, no nonlinear or observational validation"}
    (DOC/"C6_ORACLE.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print("CONVERGENCE",json.dumps(convergence),"flat",flat_error,flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
