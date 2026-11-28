"""Source-bound independent continuous linear I oracle; two solver methods."""
import argparse,gzip,hashlib,io,json
from pathlib import Path
import numpy as np
from common.finite_start_bianchi_i import integrate_response,axial_sky
from scripts.r120.native_scan import sources
from scripts.r122.verify_sources import DOC
def sha(b):return hashlib.sha256(b).hexdigest()
def main(scratch):
    binary,tab,ref,_=sources(scratch)
    lock=json.loads((DOC/"C1.json").read_text())
    assert sha(tab.read_bytes())==lock["opacity_sha256"]
    constants=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    table=np.loadtxt(tab,skiprows=1);out={}
    for method,tol,step in (("DOP853",2e-10,.02),("Radau",5e-11,.01)):
        r=integrate_response(ref["cosmology_anchors"],ref["neutrino_fraction_hyrec"],table,constants["c_sigma_T_m3_s"],method=method,rtol=tol,atol=tol/100,max_step=step)
        buf=io.StringIO();np.savetxt(buf,r.pop("history"),header="eta s alpha beta v",fmt="%.17e")
        raw=buf.getvalue().encode();name="ORACLE_"+method+".tsv.gz";(DOC/name).write_bytes(gzip.compress(raw,mtime=0))
        x=axial_sky(r["endpoint"],1.)
        out[method]={**r,"endpoint":r["endpoint"].tolist(),"unit_seed_T20":float(x[2,0].real),"unit_seed_E20":float(x[2,1].real),"history_file":name,"history_raw_sha256":sha(raw)}
    a=np.asarray(out["DOP853"]["endpoint"]);b=np.asarray(out["Radau"]["endpoint"])
    diff=float(np.linalg.norm(a-b)/np.linalg.norm(b))
    report={"methods":out,"endpoint_relative_difference":diff,"opacity_sha256":lock["opacity_sha256"],"constants_sha256":sha((DOC/"C2_CONSTANTS.json").read_bytes()),
      "scope":"continuous linear flat I, same finite-start table history, unit derivative not finite unit shear"}
    (DOC/"C6_ORACLE.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
