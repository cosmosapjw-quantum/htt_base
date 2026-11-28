"""Independent re-read of every selected archived output and oracle history."""
import gzip,hashlib,io,json,math
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from scripts.r123.verify_sources import DOC
from scripts.r123.plan import make
from scripts.r123.analyze_scan import load
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    points={v["name"]:v for v in make()["points"]};count=0;files=0;out={}
    for mode in ("base","fine","angular"):
        records,skies=load(mode);good=[]
        for n,r in records.items():
            if r["status"]!="validated_scoped":continue
            if r["exit_code"]!=0:raise ValueError("bad exit status")
            p=points[n];d=DOC/"raw"/mode/n
            if sha((d/"point.lie").read_bytes())!=r["lie_sha256"] or (d/"point.lie").read_text()!=lie_text(p,3.610288143119805e-10):raise ValueError("initial data identity")
            raw={}
            expected={"los_modes.tsv","los_cl.tsv","run.txt","diagnostics.tsv"}
            if p["recombination"]=="matched":expected.add("recombination.tsv")
            if set(r["hashes"])!=expected:raise ValueError("output population mismatch")
            for key,h in r["hashes"].items():
                raw[key]=gzip.decompress((d/(key+".gz")).read_bytes()) if key in ("diagnostics.tsv","recombination.tsv") else (d/key).read_bytes()
                if sha(raw[key])!=h:raise ValueError("source SHA mismatch: "+n+"/"+key)
                files+=1
            sky,cl=decode_signed_modes(raw["los_modes.tsv"],8)
            c=np.loadtxt(io.BytesIO(raw["los_cl.tsv"]),skiprows=1)
            np.testing.assert_allclose(cl,c[:,1:],rtol=2e-11,atol=1e-24)
            np.testing.assert_allclose(np.linalg.norm(sky[4:]),r["norm"],rtol=2e-13,atol=1e-18)
            dg=np.genfromtxt(io.BytesIO(raw["diagnostics.tsv"]),names=True)
            check={"max_gauss":float(np.max(abs(dg["gauss"]))),"max_codazzi":float(np.max(np.sqrt(sum(dg[k]**2 for k in ("codazzi_x","codazzi_y","codazzi_z"))))),
                "max_jacobi":float(np.max(abs(dg["jacobi_norm"]))),"min_screen":float(np.min(dg["min_screen_eigenvalue"])),"depth":float(dg["proper_depth"][-1])}
            for k,val in check.items():np.testing.assert_allclose(val,r[k],rtol=2e-13,atol=1e-24)
            if check["min_screen"]<0:raise ValueError("negative screen")
            if "recombination.tsv" in raw:
                rc=np.genfromtxt(io.BytesIO(raw["recombination.tsv"]),names=True);stop=math.log(1601/21)
                idx=np.flatnonzero(rc["eta"]<=stop+1e-12)[-1]
                if np.max(np.abs(rc["delta_xe"][idx:]-rc["delta_xe"][idx]))!=0 or r["post_stop_drift"]!=0:raise ValueError("REC drift")
            elif r["post_stop_drift"] is not None:raise ValueError("invented table-only REC correction")
            rt=dict(l.split("=",1) for l in raw["run.txt"].decode().splitlines() if "=" in l)
            if rt["lie_type_initial"]!=rt["lie_type_final"] or rt["lie_type_initial"]!=p["expected_type"]:raise ValueError("Lie label mismatch")
            if rt["observer_frame"]!="host":raise ValueError("frame mismatch")
            h0,h1=rt["lie_h_initial"],rt["lie_h_final"]
            if h0.startswith("Some("):
                x,y=float(h0[5:-1]),float(h1[5:-1]);np.testing.assert_allclose(x,p["parameters"]["h"],rtol=1e-10,atol=1e-14)
                if abs(y-x)/abs(x)>1e-10:raise ValueError("h drift")
            elif h0!=h1 or h0!="None" or p["kind"]!="oracle":raise ValueError("missing h")
            good.append(r);count+=1
        out[mode]={"requested":len(records),"verified":len(good),"failures":[n for n,r in records.items() if r["status"]!="validated_scoped"],
            "max_gauss":max(v["max_gauss"] for v in good),"max_codazzi":max(v["max_codazzi"] for v in good),
            "max_jacobi":max(v["max_jacobi"] for v in good),"min_screen":min(v["min_screen"] for v in good),
            "max_h_relative_drift":max(v["h_relative_drift"] for v in good if v["h_relative_drift"] is not None),
            "max_spectrum_abs_error":max(v["spectrum_abs_error"] for v in good)}
    from common.curved_tensor_response import tensor_sky
    from scripts.r123.analyze_scan import un
    oracle=json.loads((DOC/"C6_ORACLE.json").read_text())
    lock=json.loads((DOC/"C1.json").read_text())
    assert oracle["opacity_sha256"]==lock["opacity_sha256"]
    assert oracle["constants_sha256"]==sha((DOC/"C2_CONSTANTS.json").read_bytes())
    prior=DOC.parent/"R122_PHYSICAL_SOURCE_RESPONSE_20261128/C6_ORACLE.json"
    assert oracle["R122_reference_sha256"]==sha(prior.read_bytes())
    for v in oracle["runs"].values():
        raw=gzip.decompress((DOC/v["history_file"]).read_bytes())
        if sha(raw)!=v["history_raw_sha256"]:raise ValueError("oracle history SHA")
        a=np.loadtxt(io.BytesIO(raw))
        y=un(v["endpoint_ri"])
        np.testing.assert_allclose(a[-1,1:3]+1j*a[-1,3:5],y[:2],rtol=0,atol=0)
        np.testing.assert_allclose(a[0,1:3],[1.,0.],rtol=0,atol=0)
        np.testing.assert_allclose(tensor_sky(y,v["L"],8),un(v["sky_ri"]),rtol=0,atol=0)
        if a[0,0]!=0 or not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0):raise ValueError("oracle clock")
    result={"runs":out,"verified_runs":count,"native_raw_files_verified":files,"oracle_histories_verified":len(oracle["runs"]),
            "scope":"direct source re-read and finite diagnostics; not independent reviewer or survey calibration"}
    (DOC/"C9_AUDIT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
