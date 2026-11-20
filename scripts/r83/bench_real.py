"""R83 C8 matched 35,970-CF4 H03 QR, optimized NumPy and C++ GLM timings.

4×9 working source window coefficients and full same-source 36×36 covariance.
No independent PV or Planck source-null supplied.
"""
import hashlib,json,platform,resource,sys,time
from pathlib import Path

import numpy as np
from htt.obsstat import p2p3_fast as F
from htt.obsstat.p3_fortran_bridge import _certified_fortran

ROOT=Path("docs/research_program/observational_publication_20261015")
H03=ROOT/"H03_20261016/src"
SRC=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
OUT=ROOT/"R83_PRE_DAG_NODES31_40_20261120/C8_BENCHMARK.json"
SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"

def timed(fn,reps):
    fn()
    arr=[]
    out=None
    for _ in range(reps):
        t=time.perf_counter()
        out=fn()
        arr.append(time.perf_counter()-t)
    return out,{"median_seconds":float(np.median(arr)),
                "min_seconds":float(min(arr)),"repetitions":reps,"series_seconds":arr}

def relative(x,y):
    a=np.asarray(x,dtype=float);b=np.asarray(y,dtype=float)
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-200))

def main():
    if F.sha(SRC)!=SHA:raise RuntimeError("original CF4 35970 selected source sha drift")
    sys.path.insert(0,str(H03.resolve()))
    import h03_tomography as H
    s=H.source(SRC)
    d=H.proxy_distance(s.mu);sigma=H.working_sigma(d,s.e_mu)
    X=H.velocity_design(d,s.n)
    y=H.C_KM_S*s.z
    weights=np.column_stack([H.window(s.z,sigma,c) for c in H.CENTERS])
    assert len(X)==35970 and weights.shape==(35970,4)
    arch=json.loads((ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json").read_text())
    archive_theta=np.array([v["theta9"] for v in arch["monopole_dipole_STF2_windows"]])
    archive_C=np.array(arch["joint_covariance_36x36"])
    def old_qr():
        models=[H.fit(X,y,weights[:,j],influence=True) for j in range(4)]
        A=np.vstack([q["A"] for q in models])
        C=H.joint_covariance(A,sigma)[0]
        theta=np.array([q["theta"] for q in models])
        return theta,C
    old,old_t=timed(old_qr,5)
    fast_numpy,py_t=timed(lambda:F.four_window_working_gls(X,y,weights,sigma,native_lib=None),5)
    for k,original in (("theta",archive_theta),("joint_cov",archive_C)):
        num=fast_numpy[k]
        if relative(num,original)>2e-10 or np.max(abs(num-original))>1e-9:
            raise AssertionError(f"NumPy original H03 regression {k}")
    native_path=F._certified_native()
    native={}
    for t in (1,4,8):
        out,sec=timed(lambda:F.four_window_working_gls(
             X,y,weights,sigma,native_lib=native_path,threads=t),5)
        errs={
            "theta_relative_to_QR":relative(out["theta"],old[0]),
            "theta_maxabs_to_archive":float(np.max(abs(out["theta"]-archive_theta))),
            "joint_cov_relative_to_QR":relative(out["joint_cov"],old[1]),
            "joint_cov_maxabs_to_archive":float(np.max(abs(out["joint_cov"]-archive_C))),
            "F_relative_to_numpy":relative(out["F"],fast_numpy["F"]),
            "score_relative_to_numpy":relative(out["score"],fast_numpy["score"])}
        if errs["theta_relative_to_QR"]>2e-10 or errs["joint_cov_relative_to_QR"]>2e-10:
            raise AssertionError(f"native source H03 precision {t}: {errs}")
        native[str(t)]={"time":sec,"errors":errs,
            "fullspeed_vs_QR":old_t["median_seconds"]/sec["median_seconds"],
            "fullspeed_vs_numpy":py_t["median_seconds"]/sec["median_seconds"]}
    fortran={}
    libf=_certified_fortran()
    for nt in (1,4,8,12):
        out,sec=timed(lambda:F.four_window_working_gls(
            X,y,weights,sigma,native_lib=libf,threads=nt),5)
        errs={
            "theta_relative_to_QR":relative(out["theta"],old[0]),
            "theta_maxabs_to_archive":float(np.max(abs(out["theta"]-archive_theta))),
            "joint_cov_relative_to_QR":relative(out["joint_cov"],old[1]),
            "joint_cov_maxabs_to_archive":float(np.max(abs(out["joint_cov"]-archive_C))),
            "F_relative_to_numpy":relative(out["F"],fast_numpy["F"]),
            "score_relative_to_numpy":relative(out["score"],fast_numpy["score"])}
        if errs["theta_relative_to_QR"]>2e-10 or errs["joint_cov_relative_to_QR"]>2e-10:
            raise AssertionError(f"Fortran source H03 precision {nt}: {errs}")
        fortran[str(nt)]={"time":sec,"errors":errs,
            "fullspeed_vs_QR":old_t["median_seconds"]/sec["median_seconds"],
            "fullspeed_vs_numpy":py_t["median_seconds"]/sec["median_seconds"]}
    choices=([("cpp",int(nt),row) for nt,row in native.items()] +
             [("fortran",int(nt),row) for nt,row in fortran.items()])
    chosen=max(choices,key=lambda item:item[2]["fullspeed_vs_numpy"])
    faster=chosen[2]["fullspeed_vs_numpy"]>1.15
    admit=(chosen[0],chosen[1]) if faster else ("numpy",1)
    experiment={"schema":"htt.r83.c8_original_H03_four_window_speed_precision/1",
      "source_sha256":{str(SRC):SHA,
         str(ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json"):
          F.sha(ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json")},
      "source_group_count":len(X),"n_windows":4,"n_features":9,
      "working_noise":"diagonal 250 km/s plus source modulus scatter; not correlated PV/selection",
      "original_QR_4x9_and_36cov":old_t,
      "optimized_NumPy_Blas_4x9_and_36cov":py_t,
      "NumPy_vs_QR_speedup":old_t["median_seconds"]/py_t["median_seconds"],
      "native_cpp":native,"native_fortran":fortran,
      "winning_native_kind":chosen[0],
      "winning_native_threads":int(chosen[1]),
      "winning_native_vs_numpy_speedup":chosen[2]["fullspeed_vs_numpy"],
      "native_auto_admission_at_least_1p15x":bool(faster),
      "recommended_default_kind":admit[0],
      "recommended_default_workers":admit[1],
      "error_bounds":"theta relative<2e-10 and C relative<2e-10, absolute theta <=1e-9 and C <=1e-9 on this actual source",
      "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "openblas_threads":1,"machine":platform.platform(),
      "python":platform.python_version(),"numpy":np.__version__,
      "scope":"Only in-memory source-selected weighted normal matrices and 36x36 conditional covariance, no full empirical PV source transfer or cosmological inference"}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(experiment,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"original_QR_s":old_t["median_seconds"],
        "numpy_optimized_s":py_t["median_seconds"],
        "winning_kind":chosen[0],"winning_threads":chosen[1],
        "winner_s":chosen[2]["time"]["median_seconds"],
        "winner_to_numpy":chosen[2]["fullspeed_vs_numpy"],
        "winner_to_QR":chosen[2]["fullspeed_vs_QR"],
        "admit_native_default":faster,
        "rss_MiB":experiment["peak_rss_kib"]/1024}))
if __name__=="__main__":main()
