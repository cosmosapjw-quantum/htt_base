"""R81 C8 benchmark: exact selected CF4 35970 rows, matched numeric accuracy.

Measures only in-memory kernels; no science-source PV/selection covariance,
optical inference or end-to-end catalogue read rate claim.
"""
import argparse
import hashlib
import json
import platform
import resource
import time
from pathlib import Path

import numpy as np
from htt.obsstat import phy_fast
from htt.obsstat.pre_dag_fast import radial_design
from scripts.r81.bench_baseline import axes
from scripts.r68.fiveview_geometry import E

SELECTED=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
TABLE4=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
PIN="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1<<20),b""):h.update(c)
 return h.hexdigest()

def timed(f,n=5):
 f()
 series=[]
 ans=None
 for _ in range(n):
  t=time.perf_counter()
  ans=f()
  series.append(time.perf_counter()-t)
 return ans,{"median_seconds":float(np.median(series)),
             "min_seconds":float(min(series)),"repeats":n,"series_seconds":series}

def l2_rel(x,y):
 v=np.asarray(x,float)
 w=np.asarray(y,float)
 return float(np.linalg.norm(v-w)/max(np.linalg.norm(v),1e-200))

def full_mask_compare(a,b):
 differences={}
 for key in ("weights","means","second"):
  differences[key+"_rel"]=l2_rel(a[key],b[key])
  differences[key+"_maxabs"]=float(np.max(np.abs(a[key]-b[key])))
 differences["counts_maxabs"]=int(np.max(abs(a["counts"]-b["counts"])))
 return differences

def radial_compare(a,b):
 F,sc,chi=a
 f,s,c=b
 return {"F_rel":l2_rel(F,f),"score_rel":l2_rel(sc,s),
         "chi_rel":l2_rel(chi,c),
         "beta_rel":l2_rel(np.linalg.solve(F,sc),np.linalg.solve(f,s)),
         "inv_F_rel":l2_rel(np.linalg.inv(F),np.linalg.inv(f)),
         "min_F_eig_rel":l2_rel(np.linalg.eigvalsh(F)[0],np.linalg.eigvalsh(f)[0])}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--repeat",type=int,default=5)
 args=p.parse_args()
 if not 3<=args.repeat<=8:raise ValueError("bounded benchmark")
 if sha(SELECTED)!=PIN:raise RuntimeError("selected source changed")
 with np.load(SELECTED,allow_pickle=False) as z:
  n=z["n_J2000"].copy();w=1/(z["e_dmzp"]**2);ids=z["group_id"].copy()
 assert len(n)==35970
 lib_mask=phy_fast._certified_native("mask")
 lib_gram=phy_fast._certified_native("gram")
 checks={}
 for M in (32,96,256):
  a=axes(M)
  ref,baseline=timed(lambda:phy_fast.multi_axis_hemisphere(n,a,weights=w,native_lib=None),args.repeat)
  cases={}
  for nt in (1,4,8):
   obs,speed=timed(lambda:phy_fast.multi_axis_hemisphere(n,a,weights=w,native_lib=lib_mask,threads=nt),args.repeat)
   errs=full_mask_compare(ref,obs)
   assert max(v for k,v in errs.items() if k.endswith("_rel"))<2e-11,errs
   assert errs["counts_maxabs"]==0
   cases[str(nt)]={"bench":speed,"errors":errs,
                   "speedup_median":baseline["median_seconds"]/speed["median_seconds"]}
  checks[str(M)]={"numpy":baseline,"fortran":cases,
                  "n_input":len(n),"weights_are_marginal_e_dmzp_inverse_variance":True,
                  "native_auto_threshold_pass":bool(len(n)*M>=100000)}
 lines={int(x[:7]):x for x in TABLE4.read_text().splitlines() if x.strip()}
 assert len(lines)==38053
 r=np.array([float(lines[int(g)][21:26]) for g in ids])
 X=radial_design(r,n,reference_mpc=100.)
 y=np.log10(r)-np.mean(np.log10(r))
 baseline,base_t=timed(lambda:phy_fast.weighted_radial_stats(X,w,y,native_lib=None),args.repeat)
 gresults={}
 for nt in (1,4,8):
  obs,t=timed(lambda:phy_fast.weighted_radial_stats(X,w,y,native_lib=lib_gram,threads=nt),args.repeat)
  errs=radial_compare(baseline,obs)
  assert max(errs.values())<2e-11,errs
  gresults[str(nt)]={"bench":t,"errors":errs,
                      "speedup_median":base_t["median_seconds"]/t["median_seconds"]}
 # The criterion for adopting C++ by default is measured improvement.
 # It is not about construction language or hypothetical throughput.
 best=max((v["speedup_median"],nt) for nt,v in gresults.items())
 numpy_remains=best[0]<1.15
 effective={"auto_fortran_batch_mask":True,
      "auto_cpp_gram_recommended_by_this_machine":not numpy_remains,
      "cpp_gram_required_improvement_gate":1.15,
      "fastest_cpp_threads":int(best[1]),"fastest_cpp_speedup":best[0],
      "default_policy_expected":"numpy radial Gram if native <=15% faster; otherwise evaluate auto policy with C9 review"}
 result={"schema":"htt.r81.c8_matched_source_kernel_bench/1",
  "source_sha256":{str(SELECTED):PIN,str(TABLE4):sha(TABLE4)},
  "model":"actual signed 35970 selected CF4 source geometry and marginal group errors; response synthetic detrended log r",
  "hardware":{"python":platform.python_version(),"numpy":np.__version__,
              "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "openblas_threads":"1","omp_workers":[1,4,8]},
  "mask_batches":checks,"weighted_radial_design":{
     "p":X.shape[1],"n":X.shape[0],"condition":float(np.linalg.cond(baseline[0])),
     "numpy":base_t,"CPP":gresults},
  "backend_adoption":effective,
  "source_nuisance_limit":"diagonal magnitude variance w not the source-correlated PV+calibration+selection likelihood",
  "bench_scope":"in-memory kernel only; no source FITS/table read, no physical/optical model timing"}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"n":len(n),"fortran96x":
 checks["96"]["fortran"]["8"]["speedup_median"],
 "fortran256x":checks["256"]["fortran"]["8"]["speedup_median"],
 "cpp_radial_best":best,"cpp_gram_stays_numpy":numpy_remains,
 "max_mask_rel":max(v["errors"]["second_rel"] for z in checks.values() for v in z["fortran"].values())}))
if __name__=="__main__":main()
