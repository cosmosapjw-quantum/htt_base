"""R82 C8 exact-source alternative algorithms vs certified C++/Fortran.

Compare old source-per-threshold NumPy, optimized sorted weighted empirical
survival, optional C++ tails; original apparent floor scan, chunked NumPy,
and optional Fortran. Source identity/weights/coupled window semantics fixed.
"""
import argparse
import hashlib
import json
import platform
import resource
import time
from pathlib import Path

import numpy as np

from htt.obsstat import p1_fast
from scripts.r82.bench_baseline import (FILE,SUMMARY,SHA,numpy_joint_scan,
                                        numpy_floor_scan)


def sorted_source_tails(q,w,ts,reason=None):
    """6 lower/upper strict survival curves; 2*6 source-coherent event score axes."""
    if reason is None:reason=np.zeros_like(q,dtype=np.int8)
    known=reason==0
    known_lo=np.where(known,q,-np.inf)
    possible_hi=np.where(known,q,np.inf)
    lower_values=np.column_stack([known_lo,np.max(known_lo,axis=1),
                                  np.min(known_lo,axis=1)])
    upper_values=np.column_stack([possible_hi,np.max(possible_hi,axis=1),
                                  np.min(possible_hi,axis=1)])
    out=np.empty((len(ts),2,6))
    for typ,rows in enumerate((lower_values,upper_values)):
        for j in range(6):
            vals=rows[:,j]
            ix=np.argsort(vals,kind="stable")
            sorted_v=vals[ix]
            revsum=np.cumsum(w[ix][::-1],dtype=float)[::-1]
            suffix=np.r_[revsum,0.]
            loc=np.searchsorted(sorted_v,ts,side="right")
            out[:,typ,j]=suffix[loc]
    return out


def chunked_floor_numpy(q,w,anchors,floors,block=16):
    out=np.empty((len(anchors),len(floors),3,3))
    for ia,a in enumerate(anchors):
        for lo in range(0,len(floors),block):
            hi=min(lo+block,len(floors))
            cut=(a*floors[lo:hi])[None,:,None]
            ratios=np.maximum(q[:,None,1:],cut)/np.maximum(q[:,None,:1],cut)
            out[ia,lo:hi,:,0]=np.einsum("n,naj->aj",w,ratios>1)
            out[ia,lo:hi,:,1]=np.einsum("n,naj->aj",w,ratios==1)
            out[ia,lo:hi,:,2]=np.einsum("n,naj->aj",w,ratios)
    return out


def timed(call,n=5):
    call()
    series=[]
    out=None
    for k in range(n):
        t=time.perf_counter()
        out=call()
        series.append(time.perf_counter()-t)
    return out,{"runs_seconds":series,"median_seconds":float(np.median(series)),
                "minimum_seconds":float(min(series)),"repeats":n}


def compare(x,y):
    a=np.asarray(x,dtype=float);b=np.asarray(y,dtype=float)
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-200))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--repeat",type=int,default=5)
    args=ap.parse_args()
    if not 3<=args.repeat<=8:raise ValueError("bounded benchmark only")
    if hashlib.sha256(FILE.read_bytes()).hexdigest()!=SHA:
        raise ValueError("pinned original paired draw file changed")
    with np.load(FILE,allow_pickle=False) as z:
        q=z["q_app"].copy()
        w=z["weights"].copy()
    assert q.shape==(2048,4) and np.isclose(w.sum(),1,atol=1e-14)
    results={}
    libcpp=p1_fast._certified_native("tails")
    libf=p1_fast._certified_native("floor")
    for nt in (1024,4096):
        thresholds=np.linspace(0,.125,nt)
        old,old_speed=timed(lambda:numpy_joint_scan(q,w,thresholds),args.repeat)
        sort,sort_speed=timed(lambda:sorted_source_tails(q,w,thresholds),args.repeat)
        err=compare(sort[:,0,:],old)
        assert err<2e-11
        case={"old_per_threshold_NumPy":old_speed,
              "new_sorted_NumPy":sort_speed,
              "new_sorted_vs_old_rel_error":err,
              "native_CPP":{}}
        for workers in (1,4,8):
            def kernel():
                ans=p1_fast.joint_tail_bounds(q,w,thresholds,
                              native_lib=libcpp,threads=workers)
                return np.stack((ans["lower"],ans["upper"]),axis=1)
            val,speed=timed(kernel,args.repeat)
            diff=compare(val,sort)
            assert diff<2e-11,diff
            case["native_CPP"][str(workers)]={
               "time":speed,"rel_error_against_sorted":diff,
               "speedup_vs_original":old_speed["median_seconds"]/speed["median_seconds"],
               "speedup_vs_optimized_sorted":sort_speed["median_seconds"]/speed["median_seconds"]}
        case["new_sorted_speedup_vs_original"]=old_speed["median_seconds"]/sort_speed["median_seconds"]
        results[str(nt)]=case
    # Explicit missing rows mathematical counterexample separate from actual
    # original physical unknown-mass-1 sector.
    mask_reason=np.zeros(q.shape,np.int8)
    mask_reason[::7,2]=1
    mask_reason[::11,1]=2
    mixed=q.copy()
    mixed[mask_reason!=0]=np.nan
    tt=np.linspace(0,.125,128)
    base=p1_fast.joint_tail_bounds(mixed,w,tt,missing_codes=mask_reason,native_lib=None)
    sorted_out=sorted_source_tails(mixed,w,tt,mask_reason)
    for ix,key in enumerate(("lower","upper")):
        assert compare(base[key],sorted_out[:,ix,:])<2e-11
    mixed_error=float(max(compare(base[key],sorted_out[:,ix,:])
                          for ix,key in enumerate(("lower","upper"))))
    grids={}
    for na,nf in ((32,24),(64,64)):
        anchors=np.linspace(.025,.125,na)
        floors=np.linspace(.1,1.5,nf)
        old,old_t=timed(lambda:numpy_floor_scan(q,w,anchors,floors),args.repeat)
        vec,vec_t=timed(lambda:chunked_floor_numpy(q,w,anchors,floors),args.repeat)
        err=compare(vec,old)
        assert err<2e-11,err
        case={"old_source_NumPy":old_t,"new_chunked_NumPy":vec_t,
              "new_chunked_vs_old_rel_error":err,"native_Fortran":{}}
        for workers in (1,4,8):
            def floor_kernel():
                b=p1_fast.floor_depth_grid(q,w,anchors,floors,
                                           native_lib=libf,threads=workers)
                return np.stack((b["strict_above_one"],b["tie_one"],b["mean_ratio"]),axis=-1)
            native,elapsed=timed(floor_kernel,args.repeat)
            errn=compare(native,vec)
            assert errn<2e-11,errn
            case["native_Fortran"][str(workers)]={
                "time":elapsed,"rel_error_vs_chunked_NumPy":errn,
                "speedup_vs_original":old_t["median_seconds"]/elapsed["median_seconds"],
                "speedup_vs_chunked":vec_t["median_seconds"]/elapsed["median_seconds"]}
        case["chunked_speedup_vs_original"]=old_t["median_seconds"]/vec_t["median_seconds"]
        grids[f"{na}x{nf}"]=case
    x={"schema":"htt.r82.c8_source_comparable_native_and_algorithm_bench/1",
       "input_sha256":{str(FILE):SHA,str(SUMMARY):hashlib.sha256(SUMMARY.read_bytes()).hexdigest()},
       "original_joint_unit":"2048 original coupled draws x four original overlapping CF4 windows",
       "source_errors":"Original w=1/2048; Q_app conditional not physical x_C; no source independent null",
       "tail_thresholds":results,"anchor_floor_grids":grids,
       "synthetic_partial_unknown_sorted_reference_error":mixed_error,
       "runtime":{"python":platform.python_version(),"numpy":np.__version__,
                  "RSS_max_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  "openblas_threads":"1","native_worker_counts":[1,4,8]},
       "speed_claim_scope":"in-memory original conditional q_app numerical functions, no P1 full source-to-observable cosmological likelihood"}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
    print("R82_C8_RESULTS",json.dumps({
      "sorted_tail_1024_vs_old":results["1024"]["new_sorted_speedup_vs_original"],
      "CPP8_vs_sorted1024":results["1024"]["native_CPP"]["8"]["speedup_vs_optimized_sorted"],
      "Fortran8_32x24_vs_original":grids["32x24"]["native_Fortran"]["8"]["speedup_vs_original"],
      "Fortran8_64x64_vs_chunked":grids["64x64"]["native_Fortran"]["8"]["speedup_vs_chunked"],
      "mixed_unknown_rel_error":mixed_error}))
if __name__=="__main__":main()
