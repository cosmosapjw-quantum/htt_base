"""R84 C8 exact original NVSS ring source multi-axis performance.

Compare original R74 ring softmax, optimized NumPy blocked source weights and
certified Fortran axes reduction on SAME 33k, 185 ring, three flux bins.
"""
import hashlib,json,platform,resource,time
from pathlib import Path
import numpy as np
from scripts.r84.bench_baseline import source,axes,CARRIER,R74
from htt.obsstat import p4_bianchi_fast as f

ROOT=Path("docs/research_program/observational_publication_20261015")
OUT=ROOT/"R84_PRE_DAG_NODES41_50_20261120/C8_BENCHMARK.json"


def timed(callback,n=5):
    callback()
    measurements=[]
    result=None
    for i in range(n):
        t=time.perf_counter()
        result=callback()
        measurements.append(time.perf_counter()-t)
    return result,{"median_seconds":float(np.median(measurements)),
                   "min_seconds":float(min(measurements)),"series_seconds":measurements,"reps":n}


def max_err(a,b):
    return float(np.max(abs(np.asarray(a)-np.asarray(b))))


def main():
    n,counts,g,k,V,prior=source()
    assert f._digest(CARRIER)==prior["source_hashes"]["R65_original_pixel_carrier"]
    prepared,pretime=timed(lambda:f.prepare_ring_source(n,g,counts,V,k),3)
    lib=f._certified_native()
    s={}
    for m in (32,96,256):
        aa=axes(m)
        base,t_numpy=timed(lambda:f.batch_ring_occ(n,aa,prepared,native_lib=None),5)
        native={}
        for threads in (1,4,8,12):
            got,t_native=timed(lambda:f.batch_ring_occ(
                n,aa,prepared,native_lib=lib,threads=threads),5)
            errors={"F_maxabs":max_err(got["F"],base["F"]),
                    "score_maxabs":max_err(got["gradient"],base["gradient"])}
            if errors["F_maxabs"]>2e-12 or errors["score_maxabs"]>2e-11:
                raise AssertionError(f"source numeric precision m={m} t={threads} {errors}")
            native[str(threads)]={"time":t_native,"errors":errors,
                  "speedup_vs_optimized_NumPy":t_numpy["median_seconds"]/t_native["median_seconds"]}
        s[str(m)]={"axes":m,"optimized_NumPy":t_numpy,"certified_Fortran":native,
                "source_pixels":len(n),"original_ring_count":prepared["ring_count"]}
    base_old=json.loads((OUT.parent/"C1_BASELINE.json").read_text())
    assert base_old["benchmark_direction_axes"]==32
    chosen=max((x["speedup_vs_optimized_NumPy"],int(workers),int(M))
               for M,results in s.items() for workers,x in results["certified_Fortran"].items() if int(M)>=96)
    target96=s["96"]["certified_Fortran"]
    best96=max(target96.items(),key=lambda t:t[1]["speedup_vs_optimized_NumPy"])
    can_promote=best96[1]["speedup_vs_optimized_NumPy"]>=1.15
    out={
      "schema":"htt.r84.c8_source_3band_mask_score_benchmark/1",
      "original_source_SHA256":{str(CARRIER):f._digest(CARRIER),str(R74):f._digest(R74)},
      "source_N_pixels":len(n),"rings":prepared["ring_count"],"flux_bins":3,
      "source_precomputation_benchmark":pretime,
      "same_source_axes":s,
      "original_r74_single_C1_reference_32axes_3bands_seconds":base_old["reference_original_source_32axis_3bin_seconds"],
      "best_at_96_axes_threads":int(best96[0]),
      "best_at_96_axes_Fortran_speedup_vs_optimized_numpy":best96[1]["speedup_vs_optimized_NumPy"],
      "R84_auto_native_admit_if_speedup_atleast_1p15":can_promote,
      "default_backend_selection":"fortran" if can_promote else "numpy",
      "compiler_source_sha":json.loads(Path('htt/obsstat/p4_lane.json').read_text())["source_sha256"],
      "system":{"python":platform.python_version(),"numpy":np.__version__,
                "max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "OpenBLAS_threads":1,"OpenMP_threads_tested":[1,4,8,12]},
      "bench_scope":"Core in-memory n_pix × n_axes conditional source occupancy F and beta-score; original pixel/ring inputs unchanged; no fit, cosmological bootstrap, physical signal, PV/Planck null or global tilt"}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"n":len(n),"prep_s":pretime["median_seconds"],
            "original32_s":out["original_r74_single_C1_reference_32axes_3bands_seconds"],
            "numpy96_s":s["96"]["optimized_NumPy"]["median_seconds"],
            "best96_threads":best96[0],
            "best96_fortran_s":best96[1]["time"]["median_seconds"],
            "speedup_vs_numpy96":out["best_at_96_axes_Fortran_speedup_vs_optimized_numpy"],
            "default":out["default_backend_selection"]},ensure_ascii=False))
if __name__=="__main__":main()
