"""R94 science-aware benchmark of C++17 vs prior R93 source, all 999 T alms.

Benchmarks only same-accuracy solver kernels with no change in data sources,
statistic, mask, noise pairing or scientific interpretation. Native builds are
source SHA-addressed under ~/Downloads, not in repository or user's BASS env.
"""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from sympy.physics.wigner import wigner_3j

from scripts.r94.gaunt_fast import gaunt_l2_stepup,build_terms,project,loo_diagonal_fast,_native_so,sha
from scripts.r93.smica_ffp999_biposh import gaunt_terms,project_biposh,loo_diag_q,iso_theory_cl
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122/GAUNT_CXX_SOURCE_BENCHMARK.json"
INPUT=Path.home()/"Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz"
R93_RESULT=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121/SMICA_999_NSIDE64_BIPOSH_RESULT.json"

def benchmark():
 if not INPUT.exists() or not R93_RESULT.exists():raise FileNotFoundError("R93 source absent")
 with np.load(INPUT,allow_pickle=False) as p:
  a=p["paired_masked_alm_lmax48"].astype(np.complex128)
  obs=p["observed_masked_alm_lmax48"].astype(np.complex128)
  mcids=np.asarray(p["cmb_ids"],int)
 if a.shape!=(999,1225):raise RuntimeError("wrong alm shape")
 historic=json.loads(R93_RESULT.read_text())
 times={}
 c=iso_theory_cl()
 t=time.perf_counter()
 reference=gaunt_terms(c)
 times["sympy_wigner_coeff_build_s"]=time.perf_counter()-t
 t=time.perf_counter()
 terms=build_terms(c,48)
 times["closedform_coeff_build_s"]=time.perf_counter()-t
 testcount=0
 max_dif_gaunt=0
 for l in (2,3,4,10,40,46):
  for m in (-l,0,l):
   for M in (0,1,2):
    exact=(-1)**m*np.sqrt(5*(2*l+1)*(2*(l+2)+1)/(4*np.pi))*float(wigner_3j(l,2,l+2,0,0,0))*float(wigner_3j(l,2,l+2,-m,M,m-M))
    fast=gaunt_l2_stepup(l,m,M)
    max_dif_gaunt=max(max_dif_gaunt,abs(fast-exact))
    testcount+=1
 if max_dif_gaunt>3e-14:raise RuntimeError("closed-form coefficient mismatch")
 # First do a compiled warm-up to exclude compiler wall time.
 _,so=_native_so()
 xwarm=project(a[:2],terms,backend="native")
 t=time.perf_counter(); ref=project_biposh(a,reference); times["original_R93_python_project_s"]=time.perf_counter()-t
 t=time.perf_counter(); npv=project(a,terms,backend="numpy"); times["R94_numpy_project_s"]=time.perf_counter()-t
 t=time.perf_counter(); native=project(a,terms,backend="native"); times["R94_Cxx17_project_s"]=time.perf_counter()-t
 projection_max=float(np.max(abs(ref-native)))
 numpy_max=float(np.max(abs(ref-npv)))
 if projection_max>2e-12 or numpy_max>2e-12:
  raise RuntimeError("Gaunt projection numerical parity failed")
 ref2=ref.reshape(999,20)
 new2=native.reshape(999,20)
 with np.load(INPUT,allow_pickle=False) as p:
  obsalm=p["observed_masked_alm_lmax48"].astype(np.complex128)
 obsnew=project(obsalm[None,:],terms,backend="native").reshape(20)
 obsol=project_biposh(obsalm[None,:],reference).reshape(20)
 if np.max(abs(obsnew-obsol))>3e-12:raise RuntimeError("observed source parity failed")
 subset=mcids<300
 t=time.perf_counter(); oldq=loo_diag_q(ref2[subset],obsol); times["original_R93_LOO_300_s"]=time.perf_counter()-t
 t=time.perf_counter(); fastq=loo_diagonal_fast(new2[subset],obsnew); times["R94_LOO_300_s"]=time.perf_counter()-t
 t=time.perf_counter(); old999=loo_diag_q(ref2,obsol); times["original_R93_LOO_999_s"]=time.perf_counter()-t
 t=time.perf_counter(); fast999=loo_diagonal_fast(new2,obsnew); times["R94_LOO_999_s"]=time.perf_counter()-t
 if oldq["null_tail_count"]!=fastq["null_tail_count"] or old999["null_tail_count"]!=fast999["null_tail_count"]:
  raise RuntimeError("leave-one-out rank disagrees with original math")
 if historic["global_unique_noise_300"]["null_tail_count"]!=fastq["null_tail_count"]:
  raise RuntimeError("R93 scientific 300-source tail count drift")
 if historic["global_noise_reused_999"]["null_tail_count"]!=fast999["null_tail_count"]:
  raise RuntimeError("R93 scientific 999-source tail count drift")
 return {
  "schema":"htt.r94.gaunt_cpp_openmp_full_999_benchmark/1",
  "source_identity":{
   "R93_private_alm_sha256":sha(INPUT),
   "R93_statistic_sha256":sha(R93_RESULT),
   "R94_code_source_sha256":sha(Path(__file__).with_name("gaunt_fast.py")),
   "R94_CPP_source_sha256":sha(Path(__file__).with_name("gaunt_core.cpp")),
   "native_binary_path":str(so),"native_binary_sha256":sha(so)},
  "fixed_params":{"n_cmb":999,"n_unique_noise":300,"lmax":48,"band_count":4,
                  "M_components":5,"estimate":"same exact original R93 Gaunt and LOO"},
  "n_exact_sympy_gaunt_reference_cases":testcount,
  "max_gaunt_abs_error":max_dif_gaunt,
  "projector_max_abs_error_vs_R93_native":projection_max,
  "projector_max_abs_error_vs_R93_numpy":numpy_max,
  "timings_s":times,
  "kernel_speedup_sympy_gaunt_generation":times["sympy_wigner_coeff_build_s"]/times["closedform_coeff_build_s"],
  "kernel_speedup_R93_projection_Cxx17":times["original_R93_python_project_s"]/times["R94_Cxx17_project_s"],
  "kernel_speedup_R93_LOO_999":times["original_R93_LOO_999_s"]/times["R94_LOO_999_s"],
  "mc_rank_no_change":{"300":float(fastq["rank_p"]),"999":float(fast999["rank_p"]),
                       "300_tail":fastq["null_tail_count"],"999_tail":fast999["null_tail_count"]},
  "science_status":"IMPLEMENTATION_PARITY_ONLY_NO_UPGRADE_OF_PVALUE",
  "end_to_end_speedup_not_claimed":True}

def main():
 if OUT.exists():raise RuntimeError("create-only")
 result=benchmark()
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"times":result["timings_s"],"speedups":[result["kernel_speedup_sympy_gaunt_generation"],result["kernel_speedup_R93_projection_Cxx17"],result["kernel_speedup_R93_LOO_999"]],"ranks":result["mc_rank_no_change"]}))
if __name__=="__main__":main()
