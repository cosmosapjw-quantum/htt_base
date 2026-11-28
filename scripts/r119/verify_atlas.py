"""Read genuine historical R114 output; optionally execute the pinned binary."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from common.bianchi_transfer_adapter import BianchiTransferAdapter
from common.native_morphology_atlas import sha256, decode_signed_modes

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs/research_program/observational_publication_20261015"
REF=DOC/"R114_LOCAL_UNIVERSAL_LIE_SKY_20261125"
OUT=DOC/"R119_NATIVE_CLASSIFICATION_INTAKE_20261128"
HOME=Path.home()/"Downloads/htt_r114"

def open_atlas(raw_root):
    return BianchiTransferAdapter.open_deterministic_atlas(
        OUT/"ATLAS_MANIFEST.json",raw_root,REF/"C1_HARMONIC_LONG_ATLAS.json",REF/"EXECUTED_COMMANDS.json")

def compare_cl(s,path):
    v=np.loadtxt(path,skiprows=1)
    if v.shape!=(s.ell_max+1,7) or not np.array_equal(v[:,0],np.arange(s.ell_max+1)):
        raise ValueError("full spectrum layout")
    np.testing.assert_allclose(v[:,1:],s.cl,rtol=2e-11,atol=1e-24)
    return float(np.max(np.abs(v[:,1:]-s.cl)))

def fresh_replay(binary,expected_hash):
    if sha256(binary.read_bytes())!=expected_hash:
        raise ValueError("fresh replay binary identity mismatch")
    results={}
    with tempfile.TemporaryDirectory(prefix="htt-r119-native-") as td:
        for name,shear in (("FLRW","0"),("I","0.001")):
            dest=Path(td)/name
            args=[str(binary),"--out",str(dest),"--family",name,"--shear",shear,"--duration","0.1",
                "--steps","32","--nmu","8","--nphi","16","--lmax","4","--tau","0.03",
                "--electron-beta","0,0,0","--dust-beta","0,0,0","--observer-beta","0,0,0",
                "--feedback","tracer","--route","harmonic","--harmonic-lmax","8",
                "--los-lmax","8","--los-ntheta","12","--los-nphi","24"]
            proc=subprocess.run(args,capture_output=True,text=True,timeout=60)
            result={"argv":[x if x!=str(dest) else "<new_temp_output>" for x in args],"exit_code":proc.returncode}
            if proc.returncode==0:
                raw=(dest/"los_modes.tsv").read_bytes();a,cl=decode_signed_modes(raw,8)
                v=np.loadtxt(dest/"los_cl.tsv",skiprows=1)
                np.testing.assert_array_equal(v[:,0],np.arange(9))
                np.testing.assert_allclose(cl,v[:,1:],rtol=2e-11,atol=1e-24)
                result.update({"los_modes_sha256":sha256(raw),"shape":list(a.shape),"band_norm":float(np.linalg.norm(a[4:])),
                    "max_cl_abs_error":float(np.max(np.abs(cl-v[:,1:])))})
                (OUT/f"FRESH_{name}_LOS_MODES.tsv").write_bytes(raw)
            else:
                result.update({"stderr":proc.stderr[-3000:],"stdout":proc.stdout[-3000:]})
            results[name]=result
    return results

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--raw-root",type=Path,default=HOME/"c1_atlas/runs")
    parser.add_argument("--fresh",action="store_true")
    args=parser.parse_args()
    atlas=open_atlas(args.raw_root);meta=atlas.metadata
    cases={}
    for name in atlas.cases:
        s=atlas.read(name)
        cases[name]={"source_sha256":s.source_sha256,"producer_revision":s.producer_revision,
            "shape":list(s.alm.shape),"ell2_8_norm":float(np.linalg.norm(s.band(2,8))),
            "full_cl_error":compare_cl(s,args.raw_root/name/s.tag/"los_cl.tsv")}
    out={"claim_ceiling":meta["claim_ceiling"],"cases":cases,
        "max_full_cl_error":max(x["full_cl_error"] for x in cases.values())}
    if args.fresh:
        out["fresh_replay"] = fresh_replay(HOME/"bin/homogeneous_sky_r114",meta["binary_sha256"])
        for name,record in out["fresh_replay"].items():
            if record["exit_code"]!=0:print("FRESH REPLAY BLOCKED",name,record)
    (OUT/"C7.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"cases":len(cases),"max_full_cl_error":out["max_full_cl_error"],
        "fresh_replay":out.get("fresh_replay")},indent=2))

if __name__=="__main__":main()
