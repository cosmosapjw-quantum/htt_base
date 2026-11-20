"""C1 baseline: original selected CF4 35,970-group multi-axis mask and radial Gram.

This is a computational benchmark only. No calibrated method/PV covariance, nor
new independent Hubble/tilt/shear significance.
"""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
from htt.obsstat.pre_dag_fast import radial_design, hemisphere_moments

SELECTED=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
R80=Path("docs/research_program/observational_publication_20261015/R80_SQ_CF4_SOURCE_BINDING_20261120/RESULT.json")
R78=Path("docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json")
T4=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
SELECTED_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"

def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def axes(count):
    i=np.arange(count,dtype=float)
    z=1-2*(i+.5)/count
    az=np.mod(i*np.pi*(3-np.sqrt(5)),2*np.pi)
    return np.ascontiguousarray(np.column_stack([np.sqrt(1-z*z)*np.cos(az),
                                    np.sqrt(1-z*z)*np.sin(az),z]),dtype=float)

def reference_masks(n,axes_array,weights):
    result=[]
    for v in axes_array:
        # The original R79 scalar code explicitly uses NumPy for this baseline.
        obj=hemisphere_moments(n,v,weights,native_lib=None)
        result.append([obj["weights"].tolist(),obj["means"].tolist(),obj["second"].tolist()])
    return result

def bench(f,n):
    f()
    runs=[]
    for _ in range(n):
        t=time.perf_counter()
        f()
        runs.append(time.perf_counter()-t)
    return {"median_s":float(np.median(runs)),"min_s":float(min(runs)),"runs_s":runs}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--axes",type=int,default=96)
    ap.add_argument("--repeats",type=int,default=3)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    if not (32<=a.axes<=512 and 2<=a.repeats<=10):
        raise ValueError("bounded benchmark only")
    assert digest(SELECTED)==SELECTED_SHA
    source=json.loads(R80.read_text())
    assert source["exact_selected_group_count"]==35970
    dag=json.loads(R78.read_text())
    assert dag["count_total_graph_nodes"]==60
    with np.load(SELECTED,allow_pickle=False) as z:
        n=z["n_J2000"].copy()
        e=z["e_dmzp"].copy()
        IDs=z["group_id"].copy()
    # Weighting corresponds to original per-group distance-modulus marginal
    # uncertainty, not to the complete correlated PV/zero-point likelihood.
    w=1/(e*e)
    arr=axes(a.axes)
    refmask=reference_masks(n,arr,w)
    mask_perf=bench(lambda:reference_masks(n,arr,w),a.repeats)
    lines={int(x[:7]):x for x in T4.read_text().splitlines() if x.strip()}
    r=np.array([float(lines[int(g)][21:26]) for g in IDs])
    X=radial_design(r,n,reference_mpc=100.)
    y=(np.log10(r)-np.mean(np.log10(r))) # bounded synthetic detrended response
    gram=lambda: (X.T@(w[:,None]*X), X.T@(w*y), float(w@(y*y)))
    g,score,chi=gram()
    assert np.min(np.linalg.eigvalsh(g))>0
    gram_perf=bench(gram,a.repeats)
    out={"schema":"htt.r81.c1_physical_DAG_nodes11_20_baseline/1",
       "source_sha256":{str(SELECTED):digest(SELECTED),str(R80):digest(R80),str(T4):digest(T4)},
       "original_science_42_SHA":dag["original_42_payload_sha256"],
       "ordinal_interpretation":"R79 1..10 = first ten of 11 source qualifiers. R81 11=SQ-NATIVE, 12..18=PHY01..07, 19..20=E0/E1 original immutable evidence nodes",
       "n_source_groups":len(n),"n_axes":a.axes,
       "methods":"NumPy R79 explicitly native_lib=None for reference mask; BLAS single-thread weighted 12D Gram",
       "weight_source":"actual selected e_dmzp inverse squared, NOT full 35970x35970 PV/calibration source covariance",
       "response":"synthetic detrended log distance, NOT fitted physical velocity/Hubble",
       "mask_baseline":mask_perf,"radial12_baseline":gram_perf,
       "mask_ref_case0":refmask[0],
       "gram_norm":float(np.linalg.norm(g)),
       "gram_min_eigen":float(np.min(np.linalg.eigvalsh(g))),
       "gram_condition":float(np.linalg.cond(g)),
       "score_norm":float(np.linalg.norm(score)),
       "chisq":chi,
       "python":platform.python_version(),"numpy":np.__version__,
       "evidence":"real selected CF4 geometry and marginal group errors with intentionally synthetic response; independent full source C unavailable"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"groups":len(n),"axes":a.axes,"numpy_mask_median":mask_perf["median_s"],
      "numpy_radial_gram_median":gram_perf["median_s"],"gram_cond":out["gram_condition"]}))
if __name__=="__main__": main()
