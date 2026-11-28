"""Independent finite-start sector integration and angular convergence evidence."""
import argparse,gzip,hashlib,io,json,time
from pathlib import Path
import numpy as np
from common.codazzi_linear_response import integrate_sector,sector_sky
from scripts.r120.native_scan import sources
from scripts.r124.verify_sources import DOC
def sha(b):return hashlib.sha256(b).hexdigest()
def pack(x):
    a=np.asarray(x);return np.stack((a.real,a.imag),axis=-1).tolist()
def un(v):
    a=np.asarray(v);return a[...,0]+1j*a[...,1]
def main(scratch):
    _,tab,ref,_=sources(scratch);lock=json.loads((DOC/"C1.json").read_text())
    assert sha(tab.read_bytes())==lock["opacity_sha256"]
    const=json.loads((DOC/"C2_CONSTANTS.json").read_text());table=np.loadtxt(tab,skiprows=1)
    p=DOC/"oracle";p.mkdir(exist_ok=False);out={}
    for family,a in (("VII0",0.),("VIIh",.005)):
        for m in (0,1):
            for L,tol,step,tag in ((8,2e-9,.025,"L8"),(12,2e-9,.025,"L12"),(20,2e-9,.025,"L20"),(20,2e-11,.01,"L20_tight")):
                name=f"{family}_m{m}_{tag}";t=time.monotonic()
                r=integrate_sector(ref["cosmology_anchors"],ref["neutrino_fraction_hyrec"],const["baryon_fraction"],table,const["c_sigma_T_m3_s"],.01,a,m,L,rtol=tol,max_step=step)
                h=r.pop("history");x=r.pop("endpoint")
                sky={f:sector_sky(x,m,L,8,f) for f in ("normal","host","spectator","radiation")}
                buf=io.StringIO();np.savetxt(buf,np.column_stack((h[:,0].real,h[:,1:].real,h[:,1:].imag)),header="eta s_re b_re c_re Fgamma_re Fnu_re J_re constraint_re s_im b_im c_im Fgamma_im Fnu_im J_im constraint_im",fmt="%.17e")
                raw=buf.getvalue().encode();fn=name+".tsv.gz";(p/fn).write_bytes(gzip.compress(raw,mtime=0))
                for key in ("initial_coflow","host_beta","spectator_beta","photon_energy_beta","total_radiation_beta","endpoint_codazzi"):r[key+"_ri"]=pack(r.pop(key))
                out[name]={**r,"endpoint_ri":pack(x),"sky_ri":{f:pack(v) for f,v in sky.items()},
                    "norms":{f:{"ell1":float(np.linalg.norm(v[:3])),"ell2_8":float(np.linalg.norm(v[3:])),"TEB_ell2_8":np.linalg.norm(v[3:],axis=0).tolist()} for f,v in sky.items()},
                    "history_file":"oracle/"+fn,"history_raw_sha256":sha(raw),"wall_s":time.monotonic()-t}
                print(name,"host high",out[name]["norms"]["host"]["ell2_8"],"dipole",out[name]["norms"]["host"]["ell1"],"Codazzi",r["max_codazzi"],"seconds",round(out[name]["wall_s"],2),flush=True)
    convergence={}
    for family in ("VII0","VIIh"):
        for m in (0,1):
            key=f"{family}_m{m}";target=un(out[key+"_L20_tight"]["sky_ri"]["host"])
            convergence[key]={tag:float(np.linalg.norm(un(out[key+"_"+tag]["sky_ri"]["host"])-target)/np.linalg.norm(target)) for tag in ("L8","L12","L20")}
    result={"runs":out,"convergence_to_L20_tight":convergence,"opacity_sha256":lock["opacity_sha256"],"constants_sha256":sha((DOC/"C2_CONSTANTS.json").read_bytes()),"scope":"finite-start linear anisotropy/momentum subsystem; no complete perturbed scalar background or observed covariance"}
    (DOC/"C6_ORACLE.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("CONVERGENCE",json.dumps(convergence),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
