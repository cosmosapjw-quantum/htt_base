"""R83 production-preflight CLI for source-bound fast CF4 H03 four-window core.

Reads the authentic original 35,970-group selected source and produces only a
working-law 4x9 + 36x36 diagnostic. Does not overwrite old H03 results.
"""
import argparse,hashlib,json,platform,sys,time
from pathlib import Path

import numpy as np
from htt.obsstat import p2p3_fast

ROOT=Path("docs/research_program/observational_publication_20261015")
SRC=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
H03=ROOT/"H03_20261016/src"
ARCHIVE=ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json"
SOURCE_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"

def run(source=SRC,*,expected=SOURCE_SHA):
    if p2p3_fast.sha(source)!=expected:
        raise ValueError("H03 source SHA mismatch: no source substitution")
    sys.path.insert(0,str(H03.resolve()))
    import h03_tomography as H
    start=time.perf_counter()
    s=H.source(source,expected_sha=expected)
    d=H.proxy_distance(s.mu)
    sig=H.working_sigma(d,s.e_mu)
    X=H.velocity_design(d,s.n)
    w=np.column_stack([H.window(s.z,sig,c) for c in H.CENTERS])
    y=H.C_KM_S*s.z
    io_model_elapsed=time.perf_counter()-start
    start=time.perf_counter()
    o=p2p3_fast.four_window_working_gls(X,y,w,sig)
    kernel_elapsed=time.perf_counter()-start
    receipt=p2p3_fast.last_p2p3_receipt()
    if receipt["used"]=="native_failed":
        raise RuntimeError("native kernel run not successfully completed")
    ref=json.loads(ARCHIVE.read_text())
    theta=np.asarray([x["theta9"] for x in ref["monopole_dipole_STF2_windows"]])
    C=np.asarray(ref["joint_covariance_36x36"])
    dtheta=float(np.max(abs(theta-o["theta"])))
    dc=float(np.max(abs(C-o["joint_cov"])))
    if dtheta>1e-9 or dc>1e-9:
        raise AssertionError(f"original H03 source replay exceeds numerical acceptance: {dtheta}, {dc}")
    # Original source includes exactly four overlapping working redshift windows;
    # the covariance between them is not zero/independent.
    return {"schema":"htt.r83.fast_H03_CF4_source_conditional/1",
        "source_sha256":expected,"archived_H03_source_sha256":p2p3_fast.sha(ARCHIVE),
        "source_group_count":len(s.z),"source_units":"km/s/Mpc working expansion proxy, not actual H(z,n)",
        "window_centers":list(H.CENTERS),"window_width_z":H.WIDTH,
        "theta4x9":o["theta"].tolist(),"joint_covariance_36x36":o["joint_cov"].tolist(),
        "offdiag_9x9_cov_Frobenius":float(np.linalg.norm(o["joint_cov"][:9,9:18])),
        "max_original_theta_absolute_error":dtheta,
        "max_original_covariance_absolute_error":dc,
        "source_and_design_prepare_seconds":io_model_elapsed,
        "full_conditional_core_seconds":kernel_elapsed,
        "actual_backend":receipt,"python_version":platform.python_version(),
        "science_gate":"H03 completed_scoped original; H02 real PV/calibration source unresolved",
        "actual_H_z_n":None,"full_source_PV_selection_calibration_cov":None,
        "physical_Pi":None,
        "paper_claim":"NUMERICAL_SOURCE_CONDITIONAL_ONLY"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,default=SRC)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():raise FileExistsError("create-only fast preflight output")
    result=run(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"source_n":result["source_group_count"],
          "backend":result["actual_backend"]["used"],
          "original_theta_error":result["max_original_theta_absolute_error"],
          "original_cov_error":result["max_original_covariance_absolute_error"],
          "kernel_sec":result["full_conditional_core_seconds"]},ensure_ascii=False))
if __name__=="__main__":main()
