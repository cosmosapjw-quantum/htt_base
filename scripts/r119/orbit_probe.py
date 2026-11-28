"""Actual R114 signed-sky orbit brackets and truncation sensitivity."""
import json
from pathlib import Path
import numpy as np
from common.morphology_orbit import profile_bounds
from scripts.r119.verify_atlas import open_atlas,HOME,OUT

def main():
    atlas=open_atlas(HOME/"c1_atlas/runs")
    names=[n for n in atlas.cases if n!="FLRW"]
    fine=[];coarse=[];sensitivity={}
    for n in atlas.cases:
        a=atlas.read(n).band(2,8);b=atlas.read(n,"h24_s2000").band(2,8)
        delta=float(np.linalg.norm(a-b));norm=float(np.linalg.norm(a))
        sensitivity[n]={"absolute_band_delta":delta,"relative_band_delta":delta/norm if n!="FLRW" and norm else None}
        if n!="FLRW":fine.append(a);coarse.append(b)
    lo,identity,hi=profile_bounds(fine,2,8)
    lo24,id24,hi24=profile_bounds(coarse,2,8)
    pairs=[]
    for i,a in enumerate(names):
        for j in range(i+1,len(names)):
            pairs.append({"pair":[a,names[j]],"lower":float(lo[i,j]),"identity_upper":float(identity[i,j]),
                "upper_64":float(hi[64][i,j]),"upper_256":float(hi[256][i,j]),
                "lower_h24":float(lo24[i,j]),"upper_256_h24":float(hi24[256][i,j])})
    out={"scope":"unweighted native TEB l=2..8 finite representative shape only; no likelihood",
        "seed":119,"random_rotations":[64,256],"identity_and_inverse_included":True,
        "harmonic_lmax_sensitivity":sensitivity,"pairs":pairs,
        "max_pair_upper_h24_h32_change":max(abs(p["upper_256"]-p["upper_256_h24"]) for p in pairs)}
    (OUT/"C8.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"pairs":len(pairs),"closest_sampled_upper":sorted(pairs,key=lambda p:p["upper_256"])[:8],
        "max_pair_upper_h24_h32_change":out["max_pair_upper_h24_h32_change"],
        "max_nonFLRW_relative_band_delta":max(v["relative_band_delta"] for v in sensitivity.values() if v["relative_band_delta"] is not None)},indent=2))
if __name__=="__main__":main()
