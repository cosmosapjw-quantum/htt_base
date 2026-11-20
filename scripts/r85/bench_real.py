"""R85 C8 real K02 35,970 source 4×12/32D benchmark against original QR.

All benchmarks use identical CF4 IDs, source-matched error/weights, BLAS=1;
results are source working inference, NOT physical sigma/omega/Planck null.
"""
import hashlib,json,platform,resource,sys,time
from pathlib import Path
import numpy as np
from htt.obsstat import p5p6_fast as F

ROOT=Path("docs/research_program/observational_publication_20261015")
SRC=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
K02=ROOT/"NEXT_20261016/K02"
OUT=ROOT/"R85_PRE_DAG_NODES51_60_20261120/C8_BENCHMARK.json"

def timed(func,reps=5):
    func()
    times=[]
    out=None
    for _ in range(reps):
        begin=time.perf_counter()
        out=func()
        times.append(time.perf_counter()-begin)
    return out,{"median_s":float(np.median(times)),"min_s":float(np.min(times)),
                "repeats":reps,"series_s":times}

def compare(a,b):
    A=np.asarray(a,float);B=np.asarray(b,float)
    return {"maxabs":float(np.max(abs(A-B))),
            "relative_norm":float(np.linalg.norm(A-B)/max(np.linalg.norm(B),1e-200))}

def main():
    assert F._sha(SRC)==F.SOURCE_SHA
    source=F.prepare_cf4_method_source(SRC)
    sys.path.insert(0,str(K02.resolve()))
    import k02_source_identification as old
    ref0,original_t=timed(lambda:old.compute(SRC),3)
    ref,pytime=timed(lambda:F.k02_method_profiled(source,native_lib=None),5)
    oldshape=np.array(ref0["identified_working_shape8_kmsMpc"])
    oldC=np.array(ref0["joint_shape_cov32"])
    cmp0={"shape8":compare(ref["shape8"],oldshape),
          "cov32":compare(ref["joint_cov32"],oldC)}
    assert all(v["relative_norm"]<2e-10 for v in cmp0.values())
    native_lib=F._certified_fortran()
    cases={}
    for workers in (1,4,8,12):
        value,ts=timed(lambda:F.k02_method_profiled(
             source,native_lib=native_lib,threads=workers),5)
        err={
          "shape8_vs_original_QR":compare(value["shape8"],oldshape),
          "cov32_vs_original_QR":compare(value["joint_cov32"],oldC),
          "shape8_vs_optimized_NumPy":compare(value["shape8"],ref["shape8"]),
          "cov32_vs_optimized_NumPy":compare(value["joint_cov32"],ref["joint_cov32"]),
          "F_vs_NumPy":compare(value["F12"],ref["F12"]),
          "score_vs_NumPy":compare(value["score12"],ref["score12"])}
        assert all(v["relative_norm"]<2e-10 for v in err.values()),(workers,err)
        assert err["shape8_vs_original_QR"]["maxabs"]<1e-9
        assert err["cov32_vs_original_QR"]["maxabs"]<1e-9
        cases[str(workers)]={"time":ts,"errors":err,
          "speedup_vs_original_QR":original_t["median_s"]/ts["median_s"],
          "speedup_vs_optimized_NumPy":pytime["median_s"]/ts["median_s"]}
    best_key=max(cases,key=lambda k:cases[k]["speedup_vs_optimized_NumPy"])
    best=cases[best_key]
    source_native_wins=best["speedup_vs_optimized_NumPy"]>1.15
    result={
      "schema":"htt.r85.c8_real_CF4_4x12_32D_source_accurate_benchmark/1",
      "source_sha256":{str(SRC):F._sha(SRC),str(K02/"k02_source_identification.py"):F._sha(K02/"k02_source_identification.py")},
      "original_n":source["N"],"methods":source["method_names"],
      "working_law":"actual CF4 fixed 4 method intercepts +8 shape, 4 windows with same source diagonal noise; not real optical normal sigma",
      "original_full_4window_QR_32cov":original_t,
      "optimized_NumPy_4window_Fscore_G48_then_32cov":pytime,
      "original_QR_vs_NumPy_precision":cmp0,
      "source_Fortran_compensated_workers":cases,
      "best_native_threads":int(best_key),
      "best_native_speedup_vs_optimized_NumPy":best["speedup_vs_optimized_NumPy"],
      "native_auto_default_admitted":source_native_wins,
      "source_recommended_default":"fortran_source_info_cross" if source_native_wins else "numpy_blas_source",
      "numerical_condition_F":ref["condition_F"],
      "source_C32_eigen_min":ref["source_eig_min"],
      "source_original_cross_cov_norm":float(np.linalg.norm(ref["joint_cov32"][:8,8:16])),
      "backend_accuracy":"all original shape8/C32 >= good to 2e-10 relative and 1e-9 abs",
      "resources":{"maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   "python":platform.python_version(),"numpy":np.__version__,
                   "OpenBLAS_threads":1,"native_threads":[1,4,8,12]},
      "interpretation":"in-memory 35970-group core source numerical benchmark only, no raw source IO or full physical source/null"}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"old_QR_s":original_t["median_s"],"new_NumPy_s":pytime["median_s"],
      "Fortran_fastest_threads":best_key,"Fortran_s":best["time"]["median_s"],
      "Fortran_to_NumPy":best["speedup_vs_optimized_NumPy"],
      "Fortran_to_QR":best["speedup_vs_original_QR"],
      "Fortran_default":source_native_wins,"max_cov_error":best["errors"]["cov32_vs_original_QR"]["maxabs"]}))
if __name__=="__main__":main()
