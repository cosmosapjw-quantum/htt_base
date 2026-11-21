"""R90 exact existing Quaia-G20.0/source-pixel cross-check without downloading catalogs.

Source is pre-existing R89 join (read-only) + freshly verified official
Zenodo G20.0/G20.5 maps in local Downloads. This supports map chart identity
for G20.0 only, not the scientific Gaia scan/null or G20.5 catalog join.
"""
import argparse
import hashlib
import json
from pathlib import Path
import healpy as hp
import numpy as np
from scripts.r90.download_minimal import DEST
from scripts.r90.sf_attribution import ROOT, BASE

JOIN=Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz")
OUT=BASE/"R90_SOLVERFREE_BIANCHI_ATTRIBUTION_20261121/QUAIA_COORDINATE_QUALIFICATION.json"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(2**20),b""):h.update(x)
    return h.hexdigest()

def evaluate():
    paths={k:DEST/f"selection_function_NSIDE64_G{k}.fits" for k in ("20.0","20.5")}
    mm={k:hp.read_map(str(p),field=0).astype(float) for k,p in paths.items()}
    with np.load(JOIN,allow_pickle=False) as j:
        ra=np.asarray(j["ra"],float)
        dec=np.asarray(j["dec"],float)
        g=np.asarray(j["phot_g_mean_mag"],float)
        pix=np.asarray(j["pixel_ring64"],int)
        val=np.asarray(j["selection_relative"],float)
    pixcalc=hp.ang2pix(64,np.deg2rad(90-dec),np.deg2rad(ra))
    if not (len(pix)==692154 and np.array_equal(pix,pixcalc)):
        raise RuntimeError("ICRS source->HEALPix pixel identity mismatch")
    d20=mm["20.0"][pix]-val
    if max(abs(d20))>1e-12 or np.any(g>=20.0):
        raise RuntimeError("G20.0 old exact source/map identity failed")
    d205=mm["20.5"][pix]-val
    return {
      "schema":"htt.r90.quaia_g20_frame_qualification/1",
      "status":"G20.0_ICRS_PIXEL_AND_SELECTION_JOIN_EXACT; G20.5_INDEPENDENT_CATALOG_UNCHECKED",
      "old_source_join_path":str(JOIN),
      "old_source_join_sha256":sha(JOIN),
      "official_file_shas":{k:sha(p) for k,p in paths.items()},
      "n_existing_source_rows_checked":int(len(ra)),
      "matching_ra_dec_to_preexisting_pixel_fraction":float(np.mean(pix==pixcalc)),
      "G20.0_join_selection_max_abs_error":float(np.max(abs(d20))),
      "G20.0_matched_rows_all_bright":True,
      "G20.5_matches_old_G20.0_join":False,
      "G20.5_minus_old_G20.0_median_abs":float(np.median(abs(d205))),
      "G20.5_vs_join_corr":float(np.corrcoef(mm["20.5"][pix],val)[0,1]),
      "coordinate_result":"ICRS RA/Dec HEALPix RING for matched G20.0 existing join source",
      "interpretive_limit":"This qualifies G20.0 source chart only; separate G20.5 joint catalog and source-specific physical covariance/null still unavailable",
      "physical_Pi":None,"physical_GF":None,"native_boltzmann_used":False,
    }

def main():
    ap=argparse.ArgumentParser()
    flags=ap.add_mutually_exclusive_group(required=True)
    flags.add_argument("--write",action="store_true")
    flags.add_argument("--check",action="store_true")
    args=ap.parse_args()
    res=evaluate()
    content=json.dumps(res,indent=2,ensure_ascii=False)+"\n"
    if args.write:
        with OUT.open("x") as f:f.write(content)
    else:
        if OUT.read_bytes()!=content.encode():raise RuntimeError("byte/content drift")
    print(json.dumps({"qualification":res["status"],"n":res["n_existing_source_rows_checked"],"mode":"write" if args.write else "check"}))

if __name__=="__main__":main()
