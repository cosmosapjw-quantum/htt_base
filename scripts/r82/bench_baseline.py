"""R82 C1 original P1 same-source 2048x4 joint working-law baseline.

Only conditional source diagnostics, not a physical x_C posterior or independent
four-window likelihood. Uses original archived paired source values verbatim.
"""
import argparse
import hashlib
import json
import platform
import resource
import time
from pathlib import Path

import numpy as np

P1=Path("docs/research_program/observational_publication_20261015/CONTINUATION_20261018/P1/results")
FILE=P1/"paired_functional_arrays.npz"
SUMMARY=P1/"FUNCTIONAL_SENSITIVITY_RESULT.json"
SHA="cd38f438a0bf07385b07478c7b5c122df5af1e9bb48a5575fe1cad40ef261f27"

def file_sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for z in iter(lambda:f.read(1<<20),b""):
            h.update(z)
    return h.hexdigest()

def benchmark(call,reps=3):
    call()
    d=[]
    result=None
    for i in range(reps):
        t=time.perf_counter()
        result=call()
        d.append(time.perf_counter()-t)
    return result,{"median_seconds":float(np.median(d)),"minimum_seconds":min(d),"series_seconds":d}

def numpy_joint_scan(q,w,t):
    """Exact original sample-unit, strict >, paired any/all across 4 windows."""
    v=np.empty((len(t),6))
    for i,x in enumerate(t):
        mask=q>x
        v[i,:4]=w@mask
        v[i,4]=w@np.any(mask,axis=1)
        v[i,5]=w@np.all(mask,axis=1)
    return v

def numpy_floor_scan(q,w,anchors,floors):
    """Original apparent floor contrast: no physical GF or sector positivity."""
    out=np.empty((len(anchors),len(floors),3,3))
    for ia,a in enumerate(anchors):
        for j,f in enumerate(floors):
            v=np.maximum(q[:,1:]/a,f)/np.maximum(q[:,:1]/a,f)
            out[ia,j,:,0]=w@(v>1.)
            out[ia,j,:,1]=w@(v==1.)
            out[ia,j,:,2]=w@v
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--thresholds",type=int,default=1024)
    ap.add_argument("--anchors",type=int,default=32)
    ap.add_argument("--floors",type=int,default=24)
    ap.add_argument("--reps",type=int,default=3)
    args=ap.parse_args()
    if not 128<=args.thresholds<=8192 or not 8<=args.anchors<=128 or not 8<=args.floors<=128 or not 2<=args.reps<=8:
        raise ValueError("bounded reproducible benchmark only")
    if file_sha(FILE)!=SHA:raise RuntimeError("P1 original paired NPZ bytes changed")
    with np.load(FILE,allow_pickle=False) as z:
        q=z["q_app"].copy()
        w=z["weights"].copy()
        draws=z["draws"]
        ids=z["sample_id"].copy()
        physical=[z[k] for k in ("physical_Q","physical_F","physical_G_F")]
        assert draws.shape==(2048,4,9)
        assert all(np.isnan(x).all() for x in physical)
    assert q.shape==(2048,4) and w.shape==(2048,) and len(set(ids))==2048
    assert abs(w.sum()-1)<1e-14
    ts=np.linspace(0.,.125,args.thresholds)
    an=np.linspace(.025,.125,args.anchors)
    fl=np.linspace(.1,1.5,args.floors)
    tails,time_t=benchmark(lambda:numpy_joint_scan(q,w,ts),args.reps)
    floors,time_f=benchmark(lambda:numpy_floor_scan(q,w,an,fl),args.reps)
    snapshot=json.loads(SUMMARY.read_text())
    source_t=[d["threshold"] for d in snapshot["strict_exceedance"]]
    check=numpy_joint_scan(q,w,np.array(source_t))
    for k,x in enumerate(snapshot["strict_exceedance"]):
        np.testing.assert_allclose(check[k,:4],x["per_window"],atol=1e-15,rtol=0)
        assert abs(check[k,4]-x["any_window"])<1e-15
        assert abs(check[k,5]-x["all_windows"])<1e-15
    assert snapshot["physical_functionals"]["unknown_mass"]==1.
    out={
       "schema":"htt.r82.c1_original_p1_joint_four_window_baseline/1",
       "source_sha256":{str(FILE):SHA,str(SUMMARY):file_sha(SUMMARY)},
       "original_n_draws":2048,"joint_windows":4,
       "original_sample_ID_hash":hashlib.sha256("\n".join(ids).encode()).hexdigest(),
       "weight_total":float(w.sum()),
       "physical_Q_F_GF_unknown_all":True,
       "source_conditional_not_physical":"CF4 summary-conditioned coupled Sobol draw law; windows NOT independent and no source-calibrated physical optical response",
       "n_scan_thresholds":args.thresholds,"n_anchor":args.anchors,"n_floor":args.floors,
       "numpy_tail_baseline":time_t,"numpy_floor_baseline":time_f,
       "original_S02_archived_strict_tail_reproduced":True,
       "snapshot_strict_t_0p05":check[source_t.index(.05)].tolist(),
       "original_draws_not_modified":True,
       "max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "numpy":np.__version__,"python":platform.python_version()
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print("R82_C1_REAL_SOURCE",json.dumps({"n":len(q),
        "tail_baseline_s":time_t["median_seconds"],"floor_baseline_s":time_f["median_seconds"],
        "strict_t_0p05":out["snapshot_strict_t_0p05"]}))
if __name__=="__main__":main()
