"""Direct re-read of every archived R121 production result and external output."""
import gzip, hashlib, io, json, math
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from scripts.r121.verify_sources import DOC
from scripts.r121.plan import make
from scripts.r121.analyze_scan import load
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    plan=make();pts={v["name"]:v for v in plan["points"]};count=0;files=0;out={}
    for mode in ("base","fine"):
        rows,skies=load(mode);good=[]
        for v in rows:
            n=v["name"]
            if v["status"]!="validated_scoped":continue
            if v["exit_code"]!=0:raise ValueError("invalid run status")
            d=DOC/"raw"/mode/n
            if sha((d/"point.lie").read_bytes())!=v["lie_sha256"] or (d/"point.lie").read_text()!=lie_text(pts[n],3.610288143119805e-10):raise ValueError("initial Lie file mismatch")
            raw={}
            for key,h in v["hashes"].items():
                raw[key]=gzip.decompress((d/(key+".gz")).read_bytes()) if key in ("diagnostics.tsv","recombination.tsv") else (d/key).read_bytes()
                if sha(raw[key])!=h:raise ValueError("raw file SHA mismatch: "+n+"/"+key)
                files+=1
            a,cl=decode_signed_modes(raw["los_modes.tsv"],8)
            c=np.loadtxt(io.BytesIO(raw["los_cl.tsv"]),skiprows=1)
            np.testing.assert_allclose(cl,c[:,1:],rtol=2e-11,atol=1e-24)
            np.testing.assert_allclose(np.linalg.norm(a[4:]),v["norm"],rtol=2e-13,atol=1e-18)
            dg=np.genfromtxt(io.BytesIO(raw["diagnostics.tsv"]),names=True)
            rc=np.genfromtxt(io.BytesIO(raw["recombination.tsv"]),names=True)
            stop=math.log(1601/21);idx=np.flatnonzero(rc["eta"]<=stop+1e-12)[-1]
            drift=float(np.max(np.abs(rc["delta_xe"][idx:]-rc["delta_xe"][idx])))
            if drift!=0:raise ValueError("REC drift")
            check={"max_gauss":float(np.max(abs(dg["gauss"]))),"max_codazzi":float(np.max(np.sqrt(sum(dg[k]**2 for k in ("codazzi_x","codazzi_y","codazzi_z"))))),
                "max_jacobi":float(np.max(abs(dg["jacobi_norm"]))),"min_screen":float(np.min(dg["min_screen_eigenvalue"]))}
            for k,val in check.items():np.testing.assert_allclose(val,v[k],rtol=2e-13,atol=1e-24)
            if check["min_screen"]<0:raise ValueError("negative screen")
            rt=dict(l.split("=",1) for l in raw["run.txt"].decode().splitlines() if "=" in l)
            if rt["lie_type_initial"]!=rt["lie_type_final"] or rt["lie_type_initial"]!=pts[n]["expected_type"]:raise ValueError("Lie label mismatch")
            h0,h1=rt["lie_h_initial"],rt["lie_h_final"]
            if h0.startswith("Some("):
                x,y=float(h0[5:-1]),float(h1[5:-1]);np.testing.assert_allclose(x,pts[n]["parameters"]["h"],rtol=1e-10,atol=1e-14)
                if abs(y-x)/abs(x)>1e-10:raise ValueError("h drift")
            elif h0!=h1 or pts[n]["kind"]!="control":raise ValueError("missing h")
            good.append(v);count+=1
        out[mode]={"requested":len(rows),"verified":len(good),"failures":[v["name"] for v in rows if v["status"]!="validated_scoped"],
            "max_gauss":max(v["max_gauss"] for v in good),"max_codazzi":max(v["max_codazzi"] for v in good),
            "max_jacobi":max(v["max_jacobi"] for v in good),"min_screen":min(v["min_screen"] for v in good),
            "max_h_relative_drift":max(v["h_relative_drift"] for v in good if v["h_relative_drift"] is not None),
            "max_spectrum_abs_error":max(v["spectrum_abs_error"] for v in good)}
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text());ext=x["external_aniclass"];external=0
    for n,h in ext["archived_raw_sha256"].items():
        if sha(gzip.decompress((DOC/"external_aniclass"/(n+".gz")).read_bytes()))!=h:raise ValueError("external hash mismatch")
        external+=1
    result={"runs":out,"verified_runs":count,"native_raw_files_verified":files,"external_raw_files_verified":external,
            "scope":"recomputed finite native source checks, not independent reviewer or survey calibration"}
    (DOC/"C9_AUDIT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
