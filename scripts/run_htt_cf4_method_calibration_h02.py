#!/usr/bin/env python3
"""Actual 35,970-group CF4 method/depth zero-point sensitivity experiment.

No empirical method covariance is supplied by the frozen CF4 group table.
Three absolute magnitude boxes and two explicitly hypothetical covariance
laws are computed as scenario sensitivities, not fitted calibration errors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from obsstat.cf4_method_window_calibration import (
    method_response, calibration_propagation, paired_method_decomposition
)
from obsstat.htt_hubble_depth_window import (
    K_LOG, source_log_hubble, directional_window_summary
)

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
SOURCE_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
PARENT=ROOT/"docs/research_program/observational_publication_20261015/results/H01_actual_cf4_v1/result.json"
BOXES=[.03,.05,.10]
ASSUMED_DIAGONAL_SIGMA=.05


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonify(obj):
    if isinstance(obj,np.ndarray):
        return obj.tolist()
    if isinstance(obj,np.generic):
        return obj.item()
    if isinstance(obj,dict):
        return {k:jsonify(v) for k,v in obj.items()}
    if isinstance(obj,list):
        return [jsonify(z) for z in obj]
    return obj


def run(output:Path):
    if output.exists():raise FileExistsError("create-only experimental output expected")
    if sha(SOURCE)!=SOURCE_SHA:
        raise RuntimeError("CF4 original filtered group source SHA identity drift")
    parent=json.loads(PARENT.read_text())
    wins=parent["predeclared_windows"]
    with np.load(SOURCE,allow_pickle=False) as data:
        z=np.asarray(data["z_CMB"],float)
        n=np.asarray(data["n_J2000"],float)
        mu=np.asarray(data["dmzp"],float)
        err=np.asarray(data["e_dmzp"],float)
        grp=np.asarray(data["group_id"])
        method=np.asarray(data["method_family"])
    assert len(z)==35970 and len(set(grp.tolist()))==35970
    y,s=source_log_hubble(z,mu,err,velocity_dispersion_kms=250)
    s0=directional_window_summary(z,n,y,s,method,grp,wins,min_sources=300)
    parent_means=np.asarray(parent["fit"]["logH_window_mean"])
    if not np.allclose(s0["logH_window_mean"],parent_means,rtol=0,atol=1e-13):
        raise RuntimeError("source window estimator changed since H01")
    q=method_response(s0["weight_operator"],method)
    F=q["weighted_fractions"]
    names=q["names"]
    envelope={}
    for size in BOXES:
        e=calibration_propagation(q,magnitude_bounds=np.full(len(names),size))
        envelope[str(size)]={
            "per_method_abs_bound_mag":size,
            "max_logH_shift_each_window":e["max_abs_shift_logH_per_window"],
            "max_abs_logH_shell_far_minus_near":
                   e["max_abs_shift_logH_pairwise_contrast"][0,3],
            "pairwise_contrast_absolute_box":e["max_abs_shift_logH_pairwise_contrast"],
            "exactly_common_offset_cancels_in_contrast":
                   e["zero_common_mode_contrast"],
        }
    sig=ASSUMED_DIAGONAL_SIGMA
    independent=calibration_propagation(
        q,magnitude_covariance=np.eye(len(names))*sig**2)
    fully_common=calibration_propagation(
        q,magnitude_covariance=np.ones((len(names),len(names)))*sig**2)
    if fully_common["pairwise_contrast_std_logH"][0,3]>1e-13:
        raise RuntimeError("rank-one common calibration zero-point must cancel in contrast")
    contrast=paired_method_decomposition(s0["weight_operator"],method,0,3)
    obs_delta=parent_means[3]-parent_means[0]
    lo_10=envelope["0.1"]["max_abs_logH_shell_far_minus_near"]
    # Calibrate ONE deterministic parameter case by actually perturbing source
    # magnitudes and refitting all seven fixed windows. Method weights do not move.
    mu_shift=np.asarray([.02,-.03,.04,-.05])
    ymoved,smoved=source_log_hubble(
        z,mu+np.asarray([mu_shift[names.index(str(m))] for m in method]),
        err,velocity_dispersion_kms=250)
    if not np.array_equal(s,smoved):
        raise RuntimeError("working sigma changed under a constant mu zero-point")
    new=directional_window_summary(z,n,ymoved,smoved,method,grp,wins,min_sources=300)
    predicted=q["logH_jacobian_mag_inv"]@mu_shift
    observed=new["logH_window_mean"]-s0["logH_window_mean"]
    identity_error=float(np.max(np.abs(predicted-observed)))
    if identity_error>5e-13:
        raise RuntimeError(f"real CF4 perturbation response error: {identity_error}")
    # Four disjoint shell means span the cumulative means under fixed weights;
    # seven-window raw working covariance should be PSD and rank <= four.
    cov=np.asarray(s0["covariance_logH_working_diagonal_only"])
    sv=np.linalg.svd(cov,compute_uv=False)
    rank=int(np.sum(sv>sv[0]*1e-10))
    if rank!=4:
        raise RuntimeError(f"cross-window covariance rank {rank} differs from 4 shell basis")
    result={
       "schema":"htt.CF4_real_source_method_window_zero_point_sensitivity/1",
       "date":"2026-10-15",
       "source_input_sha256":SOURCE_SHA,
       "parent_H01_result_sha256":sha(PARENT),
       "source_n_groups":int(len(grp)),
       "source_conditioning":"SOURCE_CONDITIONAL_DIAGONAL_WORKING_LAW_NOT_SURVEY_CALIBRATED",
       "calibration_semantics":"HYPOTHETICAL METHOD-SPECIFIC MAG ZERO-POINT BOXES/COVARIANCE, NOT MEASURED UNCERTAINTY",
       "fixed_source_windows":wins,
       "method_order":names,
       "method_weight_fractions_by_window":F.tolist(),
       "method_gradient_delta_logH_per_mag":q["logH_jacobian_mag_inv"].tolist(),
       "observed_logH_far_minus_near":float(obs_delta),
       "observed_far_near_H_ratio":float(np.exp(obs_delta)),
       "calibration_box_scenarios":jsonify(envelope),
       "assumed_covariance_scenarios":{
           "per_method_independent_sigma_mag":sig,
           "independent_0p05_mag_calibration_logH_covariance":
               independent["propagated_logH_covariance"].tolist(),
           "independent_0p05_mag_far_near_contrast_1sigma":
               float(independent["pairwise_contrast_std_logH"][0,3]),
           "fully_common_0p05_mag_calibration_logH_covariance":
               fully_common["propagated_logH_covariance"].tolist(),
           "fully_common_0p05_mag_far_near_contrast_1sigma":
               float(fully_common["pairwise_contrast_std_logH"][0,3]),
       },
       "far_near_method_fraction_difference":contrast["weight_fraction_difference"].tolist(),
       "far_near_gradient_per_mag":contrast["difference_jacobian_mag_inv"].tolist(),
       "calibration_box0p1_contrast_fraction_of_observed_logH_change":
           float(lo_10/abs(obs_delta)),
       "cross_window_working_law_covariance_rank":rank,
       "cross_window_working_law_singular_values":sv.tolist(),
       "fixed_source_perturbation_response_check":{
          "shift_by_order_mag":mu_shift.tolist(),
          "observed_shift_logH":observed.tolist(),
          "analytic_shift_logH":predicted.tolist(),
          "maxabs_residual":identity_error,
       },
       "physical_H0_evolution_claim":"WITHHELD",
       "actual_method_selection_and_calibration_likelihood":"UNQUALIFIED",
       "independent_mock_false_positive_coverage":"NOT_RUN",
    }
    output.mkdir(parents=True)
    (output/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    fig,ax=plt.subplots(1,2,figsize=(11.4,4.4),layout="constrained")
    shells=np.arange(4)
    for k,name in enumerate(names):
        ax[0].plot(shells,F[:4,k],marker="o",label=name)
    ax[0].set_xticks(shells,[".01-.03",".03-.05",".05-.075",".075-.10"])
    ax[0].set(xlabel="CMB redshift proxy shell",ylabel="WLS method weight fraction",
              title="Released CF4 selected group method changes")
    ax[0].legend(fontsize=8);ax[0].grid(alpha=.2)
    ax[1].axhline(obs_delta,color="black",lw=1.5,
                  label="observed far-near log H_eff difference")
    a=np.arange(len(BOXES))
    wid=np.array([envelope[str(v)]["max_abs_logH_shell_far_minus_near"] for v in BOXES])
    ax[1].errorbar(a,np.zeros(len(a)),yerr=wid,marker="o",capsize=4,
                   label="hypothetical |delta mu_m| box support")
    ax[1].set_xticks(a,[str(v) for v in BOXES])
    ax[1].set(xlabel="Assumed max method |zero-point| [mag]",
              ylabel="shift in far-near log H_eff",
              title="Sensitivity ONLY; calibration law not measured")
    ax[1].grid(alpha=.2);ax[1].legend(fontsize=7)
    fig.savefig(output/"cf4_method_calibration_envelope.png",dpi=150)
    plt.close(fig)
    (output/"REPORT_KO.md").write_text(
      "# H02: 실제 CF4 깊이별 가중치와 calibration 영점 시나리오\n\n"
      f"35,970개 실제 CF4 grouped source, method order={names}. "
      "한 하늘의 overlapping windows and original source errors, no new independent samples.\n\n"
      f"Near/far delta lnH={obs_delta:.9g}; "
      f"assuming independently free absolute method offsets up to 0.1 mag, "
      f"support shift={lo_10:.9g}, ratio={lo_10/abs(obs_delta):.6f}. "
      "**0.1 mag is a hypothetical stress scale, NOT CF4 empirical method calibration uncertainty**.\n\n"
      f"Under assumed independent 0.05-mag method zero-point uncertainty, "
      f"contrast std={independent['pairwise_contrast_std_logH'][0,3]:.9g}; "
      "perfectly common 0.05-mag offset cancels between depth windows. "
      f"One fixed-source injection residual={identity_error:.3g}. "
      f"Seven overlapping window covariance rank={rank} because four shell basis components; "
      "do not invert seven-window covariance without source-aware reduction.\n\n"
      "Conclusion: distance-trend is strongly confounded by indicator method composition; "
      "this computation does NOT claim the trend is caused by calibration or measured "
      "physical H(z), and does not calibrate the true CF4 selection/flow covariance. "
      "Thus DAG H02 remains BLOCKED_PHYSICAL_EMPIRICAL_LAW with useful scoped evidence.\n",
      encoding="utf-8")
    print("H02_REAL_CF4_SOURCE_N",len(grp),"methods",names,
          "ratio",round(lo_10/abs(obs_delta),6),
          "nuisance_injection_residual",identity_error,
          "rank",rank)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    run(args.output_dir)
