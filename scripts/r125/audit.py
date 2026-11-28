"""Independent re-read of every selected archived output and oracle history."""
import gzip,hashlib,io,json,math
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from scripts.r125.verify_sources import DOC
from scripts.r125.plan import make
from scripts.r125.analyze_scan import load
def sha(b):return hashlib.sha256(b).hexdigest()

def main(scratch):
    points={v["name"]:v for v in make()["points"]};count=0;files=0;out={}
    for mode in ("base","fine"):
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
            if rt["observer_frame"]!=p["observer_frame"]:raise ValueError("frame mismatch")
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
    from common.initial_data_response import build_system,observe_columns,response_matrix
    from scripts.r125.analyze_scan import read_oracle
    from scripts.r120.native_scan import sources
    import argparse
    oracle=json.loads((DOC/"C6_ORACLE.json").read_text())
    lock=json.loads((DOC/"C1.json").read_text())
    assert oracle["opacity_sha256"]==lock["opacity_sha256"]
    const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    assert oracle["constants_sha256"]==sha((DOC/"C2_CONSTANTS.json").read_bytes())
    for name,path in (("R123","R123_CURVED_LINEAR_ORACLE_20261128"),("R124","R124_CODAZZI_LINEAR_SECTORS_20261128")):
        assert oracle["prior_sha256"][name]==sha((DOC.parent/path/"C6_ORACLE.json").read_bytes())
    _,table,ref,_=sources(scratch);assert sha(table.read_bytes())==lock["opacity_sha256"]
    tab=np.loadtxt(table,skiprows=1);checked=0
    for key,v in oracle["runs"].items():
        a=read_oracle(v);m,L=v["m"],v["L"]
        sys=build_system(ref["cosmology_anchors"],ref["neutrino_fraction_hyrec"],const["baryon_fraction"],tab,const["c_sigma_T_m3_s"],.01,.005 if key.startswith("VIIh") else 0.,m,L)
        assert a["labels"].tolist()==v["labels"]==sys["labels"]
        expected=(sys["basis"]@a["weights"])[:,None] if key.endswith("heldout") else sys["basis"]
        np.testing.assert_allclose(a["initial"],expected,atol=0,rtol=0)
        assert a["endpoint"].shape==a["initial"].shape
        np.testing.assert_array_equal(a["eta"],tab[:,0])
        assert a["constraint"].shape==(len(tab),v["columns"])
        assert all(np.isfinite(x).all() for n,x in a.items() if n!="labels")
        np.testing.assert_allclose(a["constraint"][0],sys["constraint"](0.,a["initial"]),atol=1e-15,rtol=1e-12)
        np.testing.assert_allclose(a["constraint"][-1],sys["constraint"](a["eta"][-1],a["endpoint"]),atol=1e-15,rtol=1e-12)
        np.testing.assert_allclose(np.max(abs(a["constraint"])),v["max_constraint"],atol=0,rtol=1e-14)
        for frame in ("normal","host","radiation","spectator"):
            np.testing.assert_allclose(observe_columns(a["endpoint"],sys,frame),a["sky_"+frame],atol=0,rtol=0)
            x=a["sky_"+frame]
            np.testing.assert_allclose(np.linalg.norm(response_matrix(x,m),axis=0),np.linalg.norm(x,axis=(0,1)),rtol=1e-13,atol=1e-14)
        checked+=1
    result={"runs":out,"verified_runs":count,"native_raw_files_verified":files,"oracle_npz_verified":checked,
            "scope":"raw source/hash, exact IC/endpoints and observation re-read; stored intermediate constraint traces audited, not independently re-integrated"}
    (DOC/"C9_AUDIT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args()
    main(a.scratch)
