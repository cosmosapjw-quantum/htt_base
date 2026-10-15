#!/usr/bin/env python3
"""Observed CF4 log-H_eff(z, n) window and angular-leakage diagnostics.

H_W is a survey-conditioned apparent Hubble *quotient*, not physical expansion.
Do not quote these small diagonal-law formal errors as full survey uncertainty.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from obsstat.htt_hubble_depth_window import source_log_hubble,directional_window_summary,C_KM_S

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
SOURCE_HASH="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
BASELINE_COMMIT="58bb3fa00093e36b5915c8ba87f03d7b14568bd8"
WINDOWS=[
  {"id":"shell_01_03","min_z":.01,"max_z":.03},
  {"id":"shell_03_05","min_z":.03,"max_z":.05},
  {"id":"shell_05_075","min_z":.05,"max_z":.075},
  {"id":"shell_075_10","min_z":.075,"max_z":.10},
  {"id":"cumulative_01_05","min_z":.01,"max_z":.05},
  {"id":"cumulative_01_075","min_z":.01,"max_z":.075},
  {"id":"cumulative_01_10","min_z":.01,"max_z":.10},
]


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1<<20),b""):h.update(buf)
    return h.hexdigest()


def serializable(summary):
    return {k:(v.tolist() if isinstance(v,np.ndarray) else v)
            for k,v in summary.items() if k!="weight_operator"}


def run(out, *, sigma_velocity_kms=250.):
    if out.exists():raise FileExistsError("create-only scientific artifact directory")
    t=time.perf_counter()
    if digest(SOURCE)!=SOURCE_HASH:raise RuntimeError("CF4 selected source byte identity mismatch")
    with np.load(SOURCE,allow_pickle=False) as f:
        z=np.asarray(f["z_CMB"],float)
        n=np.asarray(f["n_J2000"],float)
        mu=np.asarray(f["dmzp"],float)
        err=np.asarray(f["e_dmzp"],float)
        group=np.asarray(f["group_id"])
        methods=np.asarray(f["method_family"]).astype("U40")
    if len(z)!=35970 or len(np.unique(group))!=35970:
        raise RuntimeError("wrong selected actual CF4 group identity")
    y,sd=source_log_hubble(z,mu,err,velocity_dispersion_kms=sigma_velocity_kms)
    p=directional_window_summary(z,n,y,sd,methods,group,WINDOWS,min_sources=300)
    if sum(p["source_count"][:4])!=35970:
        raise RuntimeError("window partition does not preserve 35,970 groups")
    first=serializable(p)
    # Method-out sensitivities are sensitivity, not independent realizations.
    method_out={}
    for m in sorted(set(methods)):
        keep=methods!=m
        slist=WINDOWS[:4]
        try:
            q=directional_window_summary(z[keep],n[keep],y[keep],sd[keep],
                methods[keep],group[keep],slist,min_sources=100)
            method_out["without_"+str(m)]={
                "count":int(keep.sum()),"source_count":q["source_count"],
                "H_eff_km_s_Mpc":q["H_eff_km_s_Mpc"].tolist(),
                "bulk_response_norm_per_300_km_s":
                    np.linalg.norm(q["bulk_response_per_300_km_s"],axis=1).tolist(),
            }
        except Exception as exc:
            # Cannot compare unsupported samples; preserve exact failure.
            method_out["without_"+str(m)]={"status":"UNSUPPORTED","reason":str(exc)}
    bulk_mag=300*np.linalg.norm(p["bulk_response_per_km_s"],axis=1)
    masked_kd=np.linalg.norm(p["angular_dipole_response"],axis=1)
    out.mkdir(parents=True)
    result={
        "schema":"htt.CF4_observed_logH_directional_window/1",
        "claim_status":"SOURCE_CONDITIONAL_REAL_CF4_DIAGNOSTIC_NOT_PHYSICAL_EXPANSION_RATE",
        "input_npz_sha256":SOURCE_HASH,"parent_head":BASELINE_COMMIT,
        "estimator":"weighted geometric mean of cz / D_DM; logH=ln(cz)-ln(10)/5*(DMzp-25)",
        "source_frame":"Vcmb/c proxy, J2000 directions, grouped CF4",
        "source_units":"z dimensionless, DMzp/eDMzp magnitudes, cz km/s, D_DM Mpc, H_eff km/s/Mpc",
        "measurement_law":"eDMzp Gaussian modulus and independent working velocity width only; no shared method/selection/cosmic covariance",
        "working_velocity_dispersion_kms":sigma_velocity_kms,
        "source_groups":len(z),"raw_exposure":"Use registered 35,970-source published subset only, not independent new galaxy catalog",
        "predeclared_windows":WINDOWS,
        "fit":first,
        "bulk_leakage_norm_per_300_km_s":bulk_mag.tolist(),
        "angular_dipole_leakage_norm":masked_kd.tolist(),
        "method_leave_one_out":method_out,
        "relative_cosmological_H_identification":"NO_PHYSICAL_COVARIANT_TRANSFER",
        "cosmic_variance_and_selection":"UNRESOLVED",
        "actual_survey_posterior":"NOT_ESTABLISHED",
        "elapsed_seconds":time.perf_counter()-t,
    }
    (out/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    a=np.arange(4)
    fig,axes=plt.subplots(1,2,figsize=(10.5,4.2),layout="constrained")
    for name,cross,start in [("shell",0,0),("cumulative",1,4)]:
        pass
    h=p["H_eff_km_s_Mpc"]; formal=p["H_eff_conditional_1sigma_km_s_Mpc"]
    axes[0].errorbar(a,h[:4],yerr=formal[:4],marker="o",capsize=3,
                     label="CF4 apparent shell H_eff ± formal diagonal-law 1σ")
    axes[0].set_xticks(a,[".01–.03",".03–.05",".05–.075",".075–.10"])
    axes[0].set(xlabel="CMB-proxy redshift window",ylabel="H_eff [km/s/Mpc]",
                title="Selected CF4: nonphysical source-law estimator")
    axes[0].grid(alpha=.2);axes[0].legend(fontsize=7)
    axes[1].plot(a,bulk_mag[:4],marker="o",label="|survey k_B|×300 km/s")
    axes[1].plot(a,masked_kd[:4],marker="s",label="|survey k_D|")
    axes[1].set_xticks(a,[".01–.03",".03–.05",".05–.075",".075–.10"])
    axes[1].set(xlabel="CMB-proxy redshift window",
                ylabel="response [dimensionless δ lnH]",title="Mask/method leakage coefficients")
    axes[1].grid(alpha=.2);axes[1].legend(fontsize=7)
    fig.savefig(out/"cf4_hubble_window_trajectory.png",dpi=150)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
      "# CF4 35,970 실제 그룹의 redshift-dependent Hubble 관측창\n\n"
      "표본은 published Cosmicflows-4 group에서 고른 동일 35,970개이며 새로운 독립 표본은 아니다. "
      "zcmb/c 및 DMzp로 만든 log(cz/D) estimator는 H_eff apparent/source-conditional이고 "
      "물리적 Θ/3, Bianchi shear 또는 cosmological H0 posterior가 아니다.\n\n"
      f"Window source counts: {first['source_count']}. "
      f"Shell H_eff [km/s/Mpc]: {first['H_eff_km_s_Mpc'][:4]}. "
      f"Shell bulk response |kB*300km/s|: {bulk_mag[:4].tolist()}.\n\n"
      "Covariance는 겹치는 각 window에 같은 group ID를 통한 working diagonal C만 전파한다. "
      "실제 shared calibration/peculiar cosmic velocity/selection의 비대각 covariance는 미제공, "
      "따라서 신뢰구간, 비등방성 검출 유의도, physical tensor shear posterior로 승격하지 않는다.\n",
      encoding="utf-8")
    print("RUN_PASS n",len(z),"shells",p["source_count"][:4],
          "H",np.round(h[:4],4).tolist(),
          "bulk_leak_300km_s",np.round(bulk_mag[:4],7).tolist())
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--velocity-width-kms",type=float,default=250.)
    args=parser.parse_args()
    run(args.output_dir,sigma_velocity_kms=args.velocity_width_kms)
