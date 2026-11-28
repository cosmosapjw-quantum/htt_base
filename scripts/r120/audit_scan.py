"""Recompute compact archived output checks against the execution receipts."""
import ast,gzip,hashlib,io,json,math
from pathlib import Path
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from scripts.r120.native_scan import DOC,R114

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    plan=json.loads((DOC/"SCAN_PLAN.json").read_text())
    lock=json.loads((DOC/"C1.json").read_text())
    ref=json.loads(R114.read_text())
    points={p["name"]:p for p in plan["points"]}
    want={"base":list(points),"fine":plan["fine_time"],"angular":plan["fine_angular"]}
    out={"runs":{},"scope":"recompute archived signed sky, native spectra, time-resolved residuals, source identities; no independent model review"}
    count=0;raw_count=0;max_h_drift=0.;max_flux_error=0.;max_rec_drift=0.
    for mode,names in want.items():
        x=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text())
        if x["plan_sha256"]!=sha((DOC/"SCAN_PLAN.json").read_bytes()) or x["binary_sha256"]!=lock["binary_sha256"]["bass"] or x["opacity_sha256"]!=lock["opacity_sha256"]:raise ValueError("scan identity mismatch")
        r=x["records"]
        if [v["point"] for v in r]!=names:raise ValueError("missing or reordered registered point")
        failures=[];verified=0
        for v in r:
            n=v["point"];p=points[n]
            if v["status"]!="validated_scoped":
                failures.append({"point":n,"error":v.get("error")});continue
            if v["exit_code"]!=0:raise ValueError("inconsistent execution status")
            d=DOC/"raw"/mode/n
            assert (d/"point.lie").read_text()==lie_text(p,ref["cosmology_anchors"]["omega_lambda_emit"])
            blobs={}
            for key,h in v["file_sha256"].items():
                raw=gzip.decompress((d/(key+".gz")).read_bytes()) if key in ("diagnostics.tsv","recombination.tsv") else (d/key).read_bytes()
                if sha(raw)!=h:raise ValueError("raw file hash mismatch "+mode+"/"+n+"/"+key)
                blobs[key]=raw;raw_count+=1
            a,cl=decode_signed_modes(blobs["los_modes.tsv"],8)
            native=np.loadtxt(io.BytesIO(blobs["los_cl.tsv"]),skiprows=1)
            np.testing.assert_allclose(cl,native[:,1:],rtol=2e-11,atol=1e-24)
            np.testing.assert_allclose(np.linalg.norm(a[4:]),v["signed_norm"],rtol=2e-13,atol=1e-18)
            dg=np.genfromtxt(io.BytesIO(blobs["diagnostics.tsv"]),names=True)
            rc=np.genfromtxt(io.BytesIO(blobs["recombination.tsv"]),names=True)
            computed={"max_gauss":float(np.max(abs(dg["gauss"]))),"max_codazzi":float(np.max(np.sqrt(sum(dg[k]**2 for k in ("codazzi_x","codazzi_y","codazzi_z"))))),
                "max_jacobi":float(np.max(abs(dg["jacobi_norm"]))),"min_screen":float(np.min(dg["min_screen_eigenvalue"])),"depth":float(dg["proper_depth"][-1])}
            for k,value in computed.items():np.testing.assert_allclose(value,v[k],rtol=2e-13,atol=1e-24)
            if computed["min_screen"]<0:raise ValueError("negative sampled screen eigenvalue")
            stop=math.log(1601/21);i=np.flatnonzero(rc["eta"]<=stop+1e-12)[-1]
            drift=float(np.max(abs(rc["delta_xe"][i:]-rc["delta_xe"][i])))
            assert drift==v["post_stop_drift"]==0;max_rec_drift=max(max_rec_drift,drift)
            rt=dict(line.split("=",1) for line in blobs["run.txt"].decode().splitlines() if "=" in line)
            assert rt["lie_type_initial"]==rt["lie_type_final"]==p["expected_type"]
            hi=rt["lie_h_initial"];hf=rt["lie_h_final"]
            if hi.startswith("Some("):
                i0=float(hi[5:-1]);i1=float(hf[5:-1])
                hd=abs(i1-i0)/abs(i0);max_h_drift=max(max_h_drift,hd)
                assert hd<1e-10
                n6=p["N6"];a0=p["A3"][0]
                if n6[1]*n6[2]!=0:
                    np.testing.assert_allclose(i0,a0*a0/(n6[1]*n6[2]),rtol=2e-10,atol=1e-14)
            else:assert hi==hf=="None"
            if "required_initial_q_over_E" in rt:
                f=np.asarray(ast.literal_eval(rt["required_initial_q_over_E"]),float)
                err=float(np.linalg.norm(f-v["initial_geometry"]["required_flux_over_E"]))
                max_flux_error=max(max_flux_error,err)
                np.testing.assert_allclose(f,v["initial_geometry"]["required_flux_over_E"],rtol=1e-8,atol=1e-12)
            count+=1;verified+=1
        out["runs"][mode]={"requested":len(names),"verified":verified,"failures":failures}
    out.update({"verified_runs":count,"verified_raw_files":raw_count,"max_relative_h_drift":max_h_drift,
                "max_initial_flux_abs_error":max_flux_error,"max_rec_post_stop_drift":max_rec_drift})
    (DOC/"C9_RAW_AUDIT.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
