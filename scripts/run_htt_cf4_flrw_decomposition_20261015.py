#!/usr/bin/env python3
"""Real Cosmicflows-4 FLRW-geometry versus method-composition decomposition.

Exactly source-conditioned: 35,970 published selected CF4 group rows,
a declared flat-LCDM luminosity-distance curve, diagonal model widths
and fixed method/redshift survey windows. No calibrated selection/velocity
likelihood, physical expansion anisotropy or cosmological posterior.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from obsstat.cf4_flrw_method_decomposition import (
    method_depth_source_moments, reference_residual_moments,
    exact_symmetric_decomposition, constant_method_standardization,
)

ROOT=Path(__file__).resolve().parents[1]
CF4=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
PRIOR=ROOT/"docs/research_program/observational_publication_20261015/results/H01_actual_cf4_v1/result.json"
METHOD_STRESS=ROOT/"docs/research_program/observational_publication_20261015/results/H02_cf4_method_calibration_v2/result.json"
SOURCE_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(4<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def _plain(x):
    if isinstance(x,np.ndarray):
        return x.tolist()
    if isinstance(x,np.generic):
        return x.item()
    if isinstance(x,dict):
        return {str(k):_plain(v) for k,v in x.items()}
    if isinstance(x,list):
        return [_plain(v) for v in x]
    return x


def analyze(out:Path, *,H0=74.6,omega_m=.3153):
    if out.exists():
        raise FileExistsError("create-only CF4 observed-source research outputs")
    if digest(CF4)!=SOURCE_SHA:
        raise RuntimeError("CF4 original 35,970 group source content identity changed")
    pre=json.loads(PRIOR.read_text())
    stress=json.loads(METHOD_STRESS.read_text())
    windows=pre["predeclared_windows"][:4]
    if [v["id"] for v in windows]!=["shell_01_03","shell_03_05","shell_05_075","shell_075_10"]:
        raise RuntimeError("source original H01 shell declaration mismatched")
    with np.load(CF4,allow_pickle=False) as f:
        z=np.asarray(f["z_CMB"],float)
        mu=np.asarray(f["dmzp"],float)
        err=np.asarray(f["e_dmzp"],float)
        method=np.asarray(f["method_family"])
        group=np.asarray(f["group_id"])
    if len(group)!=35970 or len(np.unique(group))!=len(group):
        raise RuntimeError("CF4 published filtered group assignment changed")
    c=method_depth_source_moments(z,mu,err,method,group,windows,
                                   velocity_dispersion_kms=250.)
    flrw=reference_residual_moments(c,z,H0=H0,omega_m=omega_m)
    shell_raw=c["raw_shell_logh"]
    if np.max(abs(shell_raw-np.array(pre["fit"]["logH_window_mean"][:4])))>1e-13:
        raise RuntimeError("native source log-H shell baseline not reproduced")
    if np.max(abs(c["method_weight_fraction"]-
                  np.array(stress["method_weight_fractions_by_window"][:4])))>4e-13:
        raise RuntimeError("previous source method weight provenance changed")
    f=c["method_weight_fraction"]
    pairs={
        "raw_log_cz_over_dL":exact_symmetric_decomposition(
            f[0],f[-1],c["method_logh_means"][0],c["method_logh_means"][-1]),
        "flat_LCDM_reference":exact_symmetric_decomposition(
            f[0],f[-1],flrw["reference_method_logh_mean"][0],
            flrw["reference_method_logh_mean"][-1]),
        "FLRW_reference_subtracted":exact_symmetric_decomposition(
            f[0],f[-1],flrw["residual_method_logh_mean"][0],
            flrw["residual_method_logh_mean"][-1]),
    }
    if abs(pairs["raw_log_cz_over_dL"]["total"] -
           pairs["flat_LCDM_reference"]["total"] -
           pairs["FLRW_reference_subtracted"]["total"])>2e-12:
        raise RuntimeError("raw=reference+residual decomposition not additive")
    # Exactly the same method populations in all radial shells, no model-m
    # extrapolation is performed inside a method; far TF/OTHER have low counts.
    mixes={}
    for name,method_pi in [
        ("all_methods_minimum_weight_fraction",None),
        ("FP_SN_equal_if_available",np.array([
             .5 if m in ("FP","SN") else 0. for m in c["method_names"]])),
        ("FP_only",np.array([1. if m=="FP" else 0. for m in c["method_names"]])),
    ]:
        kw={} if method_pi is None else {"policy":"declared","declared_weights":method_pi}
        obs=constant_method_standardization(c,c["method_logh_means"],**kw)
        ref=constant_method_standardization(c,flrw["reference_method_logh_mean"],
                                             policy="declared",declared_weights=obs["method_mix_pi"])
        residual=constant_method_standardization(c,flrw["residual_method_logh_mean"],
                                             policy="declared",declared_weights=obs["method_mix_pi"])
        if np.max(abs(obs["logh"]-ref["logh"]-residual["logh"]))>1e-12:
            raise RuntimeError("method-standardized observable not additive")
        mixes[name]={
           "method_pi":obs["method_mix_pi"],
           "source_observed_H_eff":np.exp(obs["logh"]),
           "reference_H_eff":np.exp(ref["logh"]),
           "source_residual_log_ratio":residual["logh"],
           "source_residual_far_minus_near":residual["logh"][-1]-residual["logh"][0],
           "formal_diagonal_1sigma_logh":residual["conditional_1sigma_logh"],
           "source_Kish_N":residual["source_kish_effective_n"],
           "max_reweight_relative_method_share":obs["max_observation_reweight_relative_to_original_shell_method_fraction"],
           "constant_additive_method_zero_point_contrast_invariance":True,
           "physical_sample_selection_matched":False,
        }
    method_residual=flrw["residual_method_logh_mean"]
    method_raw=c["method_logh_means"]
    per_method={}
    for i,name in enumerate(c["method_names"]):
        per_method[name]={
            "counts":c["counts"][:,i],
            "Kish_effective_n":c["effective_n_by_method_cell"][:,i],
            "mean_source_H_eff":np.exp(method_raw[:,i]),
            "source_residual_logH":method_residual[:,i],
            "near_far_residual_logH_difference":method_residual[-1,i]-method_residual[0,i],
            "formal_1sigma_logH":np.sqrt(c["method_logh_variance_diagonal"][:,i]),
            "minimum_methods_far_support_warning":bool(c["counts"][-1,i]<30),
        }
    # Physical flat-LCDM H0 changes a common offset and is eliminated by
    # far-near differences. Changing Omega_m is a physical reference sensitivity.
    om_scenarios={}
    for testom in (.20,.25,.3153,.40):
        zz=reference_residual_moments(c,z,H0=H0,omega_m=testom)
        om_scenarios[str(testom)]={
            "Omega_m_assumed":testom,
            "source_residual_logH_mean":zz["residual_shell_logh"],
            "residual_far_minus_near":float(
                    zz["residual_shell_logh"][-1]-zz["residual_shell_logh"][0])
        }
    # Transport the prior *hypothetical* constant method zero-point boxes
    # through the FLRW-reference-subtracted residual. Reference distances
    # depend on z, not on the method constant, so the Jacobian is unchanged.
    r_delta=pairs["FLRW_reference_subtracted"]["total"]
    stress_boxes={}
    for name,entry in stress["calibration_box_scenarios"].items():
        halfwidth=float(entry["max_abs_logH_shell_far_minus_near"])
        stress_boxes[name]={
            "assumed_max_abs_method_zero_point_mag":float(name),
            "max_abs_shift_source_residual_far_near_logH":halfwidth,
            "source_residual_far_near_support_under_assumed_box":[
                r_delta-halfwidth,r_delta+halfwidth],
            "zero_contained_as_scenario_only":bool(
                r_delta-halfwidth<=0<=r_delta+halfwidth),
            "interpretation":"HYPOTHETICAL_BOX_NOT_OBSERVED_CALIBRATION_INTERVAL",
        }
    other_h0=reference_residual_moments(c,z,H0=70.,omega_m=omega_m)
    delta=np.diff(other_h0["residual_shell_logh"]-flrw["residual_shell_logh"])
    if np.max(abs(delta))>2e-13:
        raise RuntimeError("source residual depth contrasts changed under H0 global redefinition")
    ref_ratio=np.exp(flrw["reference_shell_logh"])
    obs_ratio=np.exp(shell_raw)
    if not np.allclose(obs_ratio,np.asarray(pre["fit"]["H_eff_km_s_Mpc"][:4]),rtol=0,atol=5e-11):
        raise RuntimeError("cosmographic source reference changed observed logH baseline")
    result={
        "schema":"htt.CF4_35970_FLRW_distance_and_method_decomposition/1",
        "date_KST":"2026-10-15",
        "source_npz_sha256":SOURCE_SHA,
        "source_prior_H01_sha256":digest(PRIOR),
        "source_prior_method_stress_sha256":digest(METHOD_STRESS),
        "source_groups":len(group),
        "source_frame":"published CF4 group Vcmb/c (redshift proxy), DMzp, e_DMzp",
        "metric_conventions":"FLRW reference H0 74.6 km s^-1 Mpc^-1, Omega_m .3153, flat",
        "working_sigma":"reported distance-modulus error plus assumed independent 250km/s dispersion",
        "claim_tier":"ACTUAL_CF4_SOURCE_CONDITIONED_BACKGROUND_RESIDUAL_AND_METHOD_DECOMPOSITION",
        "source_observable_not_physical_Hz":"h_i=ln(cz_i/D_DM_i); H_eff!=physical H(z)",
        "flat_LCDM_ref_no_fit":"ln(cz_i/dL_LCDM(z_i)); each source before aggregation",
        "windows":[{"lo":a,"hi":b} for a,b in c["bins"]],
        "method_names":c["method_names"],
        "method_source_counts":c["counts"],
        "method_source_Kish_N":c["effective_n_by_method_cell"],
        "source_method_weight_fractions":f,
        "source_method_logH_means":method_raw,
        "FLRW_reference_method_logH_means":flrw["reference_method_logh_mean"],
        "FLRW_reference_subtracted_method_logH_means":method_residual,
        "source_observed_H_eff_km_s_Mpc":obs_ratio,
        "flat_LCDM_expected_source_aggregated_cz_over_dL_km_s_Mpc":ref_ratio,
        "source_residual_logH_by_shell":flrw["residual_shell_logh"],
        "source_residual_shell_formal_diagonal_1sigma_logH":
            np.sqrt(np.diag(c["raw_shell_diagonal_covariance"])),
        "observed_vs_reference_H_eff_shell_ratio":np.exp(flrw["residual_shell_logh"]),
        "far_near_two_term_decomposition":pairs,
        "method_specific":per_method,
        "residual_sensitivity_under_hypothetical_method_calibration_boxes":stress_boxes,
        "common_method_standardized_results":mixes,
        "Omega_m_assumed_reference_scenarios":om_scenarios,
        "reference_H0_70_vs74p6_same_omega_m_contrast_maxabs_difference":float(np.max(abs(delta))),
        "selection_bias_corrected":"NO",
        "shared_method_calibration_and_peculiar_velocity_covariance":"UNQUALIFIED",
        "physical_beyond_FLRW_claim":"WITHHELD",
        "independent_observational_null_p_value":"NONE",
        "source_parity_and_conclusion":"Physical flat LCDM distance response explains part of depth decline; sample method mixing term alone has opposite sign. Within-method residual still is not physical H(z).",
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(_plain(result),indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    # Reproducible plot on same predeclared, non-overlapping four windows.
    fig,axes=plt.subplots(1,3,figsize=(15.4,4.7),layout="constrained")
    pos=np.arange(4)
    labs=[".01–.03",".03–.05",".05–.075",".075–.10"]
    axes[0].plot(pos,obs_ratio,"o-",label="actual CF4 apparent c z /dL")
    axes[0].plot(pos,ref_ratio,"s-",label="isotropic flat-LCDM reference")
    axes[0].set(xlabel="CMB-frame z",ylabel="selected H_eff [km/s/Mpc]",
                title="Distance-redshift shape vs actual CF4")
    axes[0].set_xticks(pos,labs,rotation=20)
    axes[0].legend(fontsize=7);axes[0].grid(alpha=.2)
    for m in c["method_names"]:
        axes[1].plot(pos,method_residual[:,c["method_names"].index(m)],"o-",label=m)
    axes[1].plot(pos,flrw["residual_shell_logh"],"k--",label="original method mix")
    axes[1].set(xlabel="CMB-frame z",ylabel="log(cz/Dobs)−log(cz/dLref)",
                title="After FLRW reference: method-specific residuals")
    axes[1].set_xticks(pos,labs,rotation=20)
    axes[1].legend(fontsize=7);axes[1].grid(alpha=.2)
    nm=["raw","flat ref","residual"]
    ks=["raw_log_cz_over_dL","flat_LCDM_reference","FLRW_reference_subtracted"]
    a=np.arange(3)
    width=.28
    axes[2].bar(a-width,[pairs[k]["total"] for k in ks],width,label="total")
    axes[2].bar(a,[pairs[k]["composition"] for k in ks],width,label="method mix")
    axes[2].bar(a+width,[pairs[k]["within_method"] for k in ks],width,label="within method")
    axes[2].set_xticks(a,nm)
    axes[2].set(ylabel="far-near delta log H_eff",title="Exact two-term, noncausal accounting")
    axes[2].legend(fontsize=7);axes[2].grid(axis="y",alpha=.2)
    fig.savefig(out/"cf4_flrw_method_decomposition.png",dpi=160)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
       "# P3 H02: 실제 CF4 source의 FLRW 거리곡선 분리 + 방법 구성 분해\n\n"
       "입력은 원래 선택된 35,970 CF4 grouped source, z_CMB, DMzp, e_DMzp, "
       "4가지 방법 FP/OTHER/SN/TF다. 같은 H01 네 겹치지 않는 적색편이 bin과 "
       "동일 대각 working covariance 및 sigma_v=250 km/s만 사용한다.\n\n"
       f"Observed apparent H_eff={obs_ratio.tolist()} km/s/Mpc; "
       f"flat LCDM H0={H0}, Ωm={omega_m} baseline={ref_ratio.tolist()}; "
       f"source mean residual ln(cz/Dobs)−ln(cz/dLref)={flrw['residual_shell_logh'].tolist()}.\n\n"
       "원시 apparent H_eff의 적색편이 의존성 상당 부분은 FLRW luminosity "
       "distance 자체의 정상적인 광학적 redshift dependence를 포함하므로 "
       "관측 H_eff를 물리 H(z), shear 또는 global tilt로 읽으면 안 된다.\n\n"
       f"Far-near raw two-term={pairs['raw_log_cz_over_dL']}; "
       f"FLRW baseline={pairs['flat_LCDM_reference']}; "
       f"source residual={pairs['FLRW_reference_subtracted']}.\n\n"
       f"FLRW-baseline-subtracted contrast에 이전 가정상 offset box [0.03,0.05,0.10] mag를 적용하면 "
       f"0.03 scenario support={stress_boxes['0.03']['source_residual_far_near_support_under_assumed_box']}, "
       f"0.05 scenario support={stress_boxes['0.05']['source_residual_far_near_support_under_assumed_box']}. "
       "이들은 측정된 95% 신뢰구간이 아니며 실제 CF4 calibration 불확실성을 나타내지 않는다.\n\n"
       "Symmetric method-mix decomposition에서 composition term은 실제 "
       "near/far downward residual을 반대로 상쇄하고, within-method term은 "
       "음수로 남는다. 이는 model-free causal attribution이 아니라 source "
       "weight를 고정한 정확한 대수적 회계이다.\n\n"
       f"Common method min-share π={mixes['all_methods_minimum_weight_fraction']['method_pi'].tolist()}; "
       f"standardized source residual far-near={mixes['all_methods_minimum_weight_fraction']['source_residual_far_minus_near']:.9g}. "
       "원거리 OTHER 및 TF의 소수 객체는 extrapolation/coverage 문제이며, "
       "method-standardized result도 true cosmological H(z)나 selection-bias "
       "correction으로 승격하지 않는다.\n\n"
       "물리적 보고서 진행에 필요한 입력: redshift-dependent method selection, "
       "group/zero-point shared covariance, peculiar-velocity field and "
       "observer/source frame redshift model, independent tracer validation. "
       "정규 FLRW의 비등방성 없는 예측도 후보 모델에 반드시 포함한다.\n",encoding="utf-8")
    print("P3_SOURCE_REAL_35970_FLRW_METHOD_DECOMP", {
      "obs_far_near":round(pairs["raw_log_cz_over_dL"]["total"],9),
      "FLRW_far_near":round(pairs["flat_LCDM_reference"]["total"],9),
      "residual_far_near":round(pairs["FLRW_reference_subtracted"]["total"],9),
      "residual_mix":round(pairs["FLRW_reference_subtracted"]["composition"],9),
      "residual_within":round(pairs["FLRW_reference_subtracted"]["within_method"],9),
    })
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--H0",type=float,default=74.6)
    p.add_argument("--omega-m",type=float,default=.3153)
    x=p.parse_args()
    analyze(x.output_dir,H0=x.H0,omega_m=x.omega_m)
