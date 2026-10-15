#!/usr/bin/env python3
"""Actual CF4 35,970 apparent STF vs unknown cosmological optical transfer.

Runs four labelled, *unverified* radial transfer shapes under the original
CF4 14-dimensional nuisance and diagonal working error law. Separately
checks the exact source method-STF calibration degeneracy and the unknown
global scalar physical optical kernel gain. Also source-reads the original
K01 one-congruence photon drift, previous validated CF4 Schur study and
legacy/Planck MES tensor aliases WITHOUT multiplying independent likelihoods.

Physical photon transfer, geodesic history, group correlated covariance,
source selection and calibrated method angular systematics remain unknown.
No observed cosmological shear/vorticity/A/beta or genuine posterior.
"""
from __future__ import annotations

import argparse,hashlib,json,resource,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.cf4_physical_transfer_identification import (
    KERNELS,cf4_working_model,profile_declared_family,
    physical_gain_degeneracy,method_quadrupole_span_certificate,
    angular_axis_cosine,method_angular_calibration_alias_matrix,KAPPA
)

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
SOURCE=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
OLD=ROOT/"docs/research_program/cf4_schur_loop8_20261015/results/result.json"
K01=PUB/"results/K01_covariant_optical_CF4_Planck_v1/result.json"
H01=PUB/"results/H01_actual_cf4_v1/result.json"
SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
ID_SHA="f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88"


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(8<<20),b""):h.update(part)
    return h.hexdigest()


def render(obj):
    if isinstance(obj,np.ndarray):return obj.tolist()
    if isinstance(obj,np.generic):return obj.item()
    if isinstance(obj,dict):return {k:render(v) for k,v in obj.items()}
    return obj


def run(output:Path):
    if output.exists():raise FileExistsError("source result create-only")
    start=time.perf_counter()
    if digest(SOURCE)!=SHA:
        raise RuntimeError("CF4 grouped 35970 source bytes differ from verified source")
    with np.load(SOURCE,allow_pickle=False) as f:
        z=np.asarray(f["z_CMB"],float)
        n=np.asarray(f["n_J2000"],float)
        methods=np.asarray(f["method_family"])
        mu=np.asarray(f["dmzp"],float)
        std=np.asarray(f["e_dmzp"],float)
        source_ids=np.asarray(f["group_id"],np.int64)
    if (len(z)!=35970 or
        hashlib.sha256(source_ids.astype("<i8").tobytes()).hexdigest()!=ID_SHA
        or sorted(set(methods.tolist()))!=["FP","OTHER","SN","TF"]):
        raise RuntimeError("CF4 actual grouped source, method partition or IDs drift")
    previous=json.loads(OLD.read_text())
    currentK01=json.loads(K01.read_text())
    currentH01=json.loads(H01.read_text())
    if (previous["source_n"]!=len(z) or
        previous["input_npz_sha256"]!=SHA or
        currentK01["actual_CF4_source_groups"]!=len(z) or
        currentK01["source_kinematical_optical_angular_rank"]["rank_H_A3_sigma5"]!=9
        or currentK01["source_kinematical_optical_angular_rank"]["rank_omega3"]!=0
        or currentH01["source_groups"]!=len(z)):
        raise RuntimeError("K01/H01/source previous scientific typed identity drift")

    profiles={}
    raw={}
    baseline=None
    for label in KERNELS:
        m=cf4_working_model(z,n,methods,mu,std,kernel_name=label)
        fit=profile_declared_family(m)
        if fit["rank"]!=5 or fit["nuisance_rank"]!=14:
            raise RuntimeError("registered 5D apparent STF or 14-dimensional nuisance rank lost")
        if label=="unit_angular_endpoint":
            past=previous["source_comparisons"]["all"]
            max_reg=float(np.max(abs(fit["gamma"]-np.asarray(past["apparent_stf_coefficients"]))))
            max_cov=float(np.max(abs(fit["cov"]-np.asarray(past["conditional_5x5_covariance"]))))
            if max_reg>1e-11 or max_cov>2e-12:
                raise RuntimeError(f"registered original Schur CF4 source regression failed: {max_reg}")
            baseline=fit
            baseline_regression={"apparent_STF_5vector_maxabs":max_reg,
                                 "5x5_working_covariance_maxabs":max_cov}
        profile={
          "source_scoped_STF_gamma_dimensionless":fit["gamma"],
          "source_conditional_diagonal_gaussian_covariance":fit["cov"],
          "apparent_frobenius_5norm":fit["conditional_apparent_frobenius_norm"],
          "relative_information_eigenvalues":fit["relative_eigenvalues"],
          "source_schur_apparent_rank":fit["rank"],
          "nuisance_rank":fit["nuisance_rank"],
          "source_group_count":len(z),
          "conditional_profile_chi2_per_dof":fit["chi2"]/fit["dof"],
          "source_STF_to_baseline_direction_cosine":1. if baseline is fit else angular_axis_cosine(baseline["gamma"],fit["gamma"]),
          "source_amplitude_ratio_to_baseline":float(
             fit["conditional_apparent_frobenius_norm"]/baseline["conditional_apparent_frobenius_norm"]),
          "transfer_shape_not_physical":"NOT_CALIBRATED_LUMINOSITY_DISTANCE_KERNEL",
        }
        profiles[label]=render(profile)
        raw[label]=(m,fit)
        print("K02 SOURCE MODEL",label,"conditional norm",profile["apparent_frobenius_5norm"],
              "anglecos",profile["source_STF_to_baseline_direction_cosine"],
              "lambda_min",profile["relative_information_eigenvalues"][0],flush=True)

    fixedmodel,fixedfit=raw[KERNELS[0]]
    # Exact arbitrary multiplicative optical transfer degeneracy for one
    # fixed kernel and the actual source y. Refit, not only rescale arrays.
    gain_test=[]
    for gain in (.1,1.,10.):
        m=cf4_working_model(z,n,methods,mu,std,kernel_name=KERNELS[0])
        m["design"][:,m["STF_slice"]]*=gain
        y=profile_declared_family(m)
        witness=physical_gain_degeneracy(fixedfit["gamma"],fixedfit["cov"],gain=gain)
        err1=float(np.max(abs(y["gamma"]-witness["conditional_gamma_for_gain"])))
        err2=float(np.max(abs(y["cov"]-witness["conditional_cov_for_gain"])))
        ierr=float(np.max(abs(y["relative_eigenvalues"]-fixedfit["relative_eigenvalues"])))
        if err1>5e-12 or err2>1e-11 or ierr>5e-12:
            raise RuntimeError("source gain normalization identity failed")
        gain_test.append({
            "declared_unverified_transfer_gain":gain,
            "source_refitted_apparent_STF_frobenius_norm":float(np.linalg.norm(y["gamma"])),
            "maxabs_gamma_scaling_identity":err1,
            "maxabs_covariance_scaling_identity":err2,
            "maxabs_relative_information_identity":ierr,
        })

    # Existing source obs y conditional injection test for one actual
    # registered model. Exact self-recovery of source STF shifts, not
    # measured physical CF4 geometry.
    offset=np.array([.012,-.016,.021,.006,-.003])
    inj={**fixedmodel,"residual":
         fixedmodel["residual"]+fixedmodel["design"][:,fixedmodel["STF_slice"]]@offset}
    injected=profile_declared_family(inj)
    injection_error=float(np.max(abs(injected["gamma"]-fixedfit["gamma"]-offset)))
    if injection_error>2e-12:
        raise RuntimeError("actual CF4 source STF injection recovery inaccurate")

    # Large worst-case physically unmeasured method-specific directional
    # calibration law: exact source B=sum_m B_m makes all STF positions
    # unidentifiable. This says nothing about actual CF4 occurrence.
    witness=method_quadrupole_span_certificate(z,n,methods,fixedmodel["g"])
    if (witness["global_STF_identified_rank_if_unrestricted_method_STF_allowed"]!=0
        or witness["source_method_nuisance_rank"]!=20):
        raise RuntimeError("method-specific angular nuisance exact degeneracy not reproduced")
    alias=method_angular_calibration_alias_matrix(fixedmodel,n,methods)
    L=alias["alias_gamma_per_method_quadrupole_mag"]
    # All method calibrations with same unmeasured angular STF pattern
    # mimic a global apparent shear gamma=-alpha/KAPPA at f=1.
    alpha=np.array([.03,0,0,0,0])
    common=np.tile(alpha,4)
    common_check=float(np.max(abs(L@common+alpha/KAPPA)))
    if common_check>3e-13:
        raise RuntimeError("method-angle calibration common-mode alias identity")
    illustrative_bias=float(np.linalg.norm(L@common))

    # Conditional direction vs physical units is a completely distinct map:
    # K01 photon dlnE/dt_u is in s^-1. No source radial-distance kernel
    # maps that local derivative into the data's delta mu.
    if currentK01["physical_shear_vorticity_acceleration_detection"]!="NONE":
        raise RuntimeError("K01 source accidentally promoted to physical shear measurement")
    result={
      "schema":"htt.P6_K02_source_apparent_STF_vs_physical_transfer_partial_identification/1",
      "date_KST":"2026-10-15",
      "source_CF4_group_npz_sha256":SHA,
      "source_group_ids_sha256":ID_SHA,
      "source_K01_covariant_optical_json_sha256":digest(K01),
      "prior_real_CF4_schur_json_sha256":digest(OLD),
      "prior_H01_source_json_sha256":digest(H01),
      "source_CF4_groups":len(z),
      "source_methods":sorted(set(methods.tolist())),
      "one_source_catalogue_realizations":1,
      "source_observed_quantity":"DMzp(z_CMB,n_J2000) - flat-LCDM mu_ref; grouped selection, not measured instantaneous optical drift",
      "source_model_units":"y=delta mu [mag], STF angular gamma dimensionless, 1+3 sigma/H dimensionless only after unknown physical transfer",
      "frozen_conditional_working_law":"H0 74.6, Omega_m .3153 flat-LCDM reference; sqrt(eDMzp^2 + .15mag^2 + (250 km/s dmu/dv)^2), method offsets/slopes, bulk and sky angular dipole",
      "source_K01_local_photon_rule":"-d ln E/dt_u=H - A dot look + sigma:look look, omega instant null; proper physical time s^-1",
      "actual_sky_source_matched_response_families":profiles,
      "exact_old_CF4_schur_regression":baseline_regression,
      "unknown_physical_transfer_overall_gain":{
         "gain_lambda_allowed":"ANY_POSITIVE_UNCALIBRATED",
         "source_model_linear_theorem":"B_(lambda f) = lambda B_f and gamma_hat(lambda f)=gamma_hat(f)/lambda, Cov=Cov(f)/lambda^2 with fixed nuisance",
         "same_actual_group_data_recomputed_gain_tests":gain_test,
         "physical_Sigma_amplitude_identified_interval":"UNBOUNDED_FROM_THIS_INPUT_MODEL",
         "physical_STF_orientation_identified":"ONLY_IF_KERNEL_SHAPE_AND_POSITIVE_GAIN_ASSUMED_FIXED",
         "source_likelihood_status":"DIAGONAL_WORKING_LAW_ONLY_NOT_PHYSICAL"
      },
      "method_specific_angular_STF_calibration_nuisance_counterexample":{
         **render(witness),
         "source_STF_mag_per_method_gain_5x20_matrix":L.tolist(),
         "hypothetical_common_method_quadrupole_mag":common.tolist(),
         "hypothetical_common_method_quadrupole_alias_gamma_frobenius_norm":illustrative_bias,
         "common_method_quadrupole_expected_gamma_change":(-alpha/KAPPA).tolist(),
         "common_source_invariance_maxabs":common_check,
         "physical_source_occurrence":"NOT_MEASURED_AN_UNRESTRICTED_NUISANCE_STRESS_TEST"
      },
      "conditional_STF_source_injection":{
         "stf_5_dimensionless_injected":offset.tolist(),
         "source_gamma_shift_observed_plus_injection_maxabs":injection_error,
         "physical_shear_inference":"NOT_PERFORMED"
      },
      "physical_identification_ranks":{
        "CF4_apparent_STF_given_fixed_kernel_and_standard_nuisance":5,
        "CF4_apparent_STF_with_unrestricted_4_method_STF_calibration":0,
        "one_event_covariant_photon_H_acceleration3_sigma5":9,
        "one_event_omega3_direct_radial":0,
        "material_radiation_tilt_beta3":"SOURCE_HISTORY_ABSENT",
        "physical_sigma_amplitude":"UNBOUNDED_WITH_UNKNOWN_KERNEL_GAIN_OR_CALIBRATION",
        "physical_sigma_orientation":"NOT_ROBUST_ACROSS_DECLARED_RADIAL_SHAPES",
      },
      "legacy_statistical_program":{
         "signed_x_F_Pi_Q_GF":"UNDEFINED_TOTAL_PHYSICAL_SECTORS_FROM_THIS_SOURCE",
         "one_congruence_sigma_hat":"UNKNOWN_BEAM_GEODESIC_SOURCE_KERNEL",
         "omega_A_beta":"UNKNOWN_NONRADIAL_AND_SOURCE_HISTORY",
         "formal_Planck_MES_epsilon":"CMB_SOURCE_ONLY_NO_ALL_OBSERVER_DERIVATIVES"
      },
      "standalone_claim":"ACTUAL_CF4_CONDITIONAL_APPARENT_QUAD_TRANSFER_STRESS_AND_EXACT_PARTIAL_IDENTIFICATION_COUNTEREXAMPLE",
      "Planck_CF4_joint_likelihood":"NOT_PRODUCED_DIFFERENT_SOURCE_AND_COMMON_CONGRUENCE_UNKNOWN",
      "actual_Cosmological_shear_vorticity_accel_beta_measurement":"NONE",
      "scientific_Journal_submission":"NOT_READY_TO_SUBMIT",
      "runtime_seconds":time.perf_counter()-start,
      "peak_RSS_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output.mkdir(parents=True)
    (output/"result.json").write_text(json.dumps(render(result),ensure_ascii=False,indent=2)+"\n")
    np.savez_compressed(output/"cf4_transfer_conditional_stf.npz",
       source_group_ids=source_ids,
       source_kernel_names=np.asarray(KERNELS),
       conditional_five_STF=np.stack([raw[k][1]["gamma"] for k in KERNELS]),
       conditional_source_cov=np.stack([raw[k][1]["cov"] for k in KERNELS]),
       relative_information_eigenvalues=np.stack([raw[k][1]["relative_eigenvalues"] for k in KERNELS]),
       method_angular_calibration_alias=L)
    fig,axes=plt.subplots(1,2,figsize=(11.2,4.7),layout="constrained")
    idx=np.arange(len(KERNELS))
    norms=[profiles[k]["apparent_frobenius_5norm"] for k in KERNELS]
    cos=[profiles[k]["source_STF_to_baseline_direction_cosine"] for k in KERNELS]
    axes[0].bar(idx,norms)
    axes[0].set_xticks(idx,["1","z/.05",".05/z","(1+z)/1.05"],rotation=20)
    axes[0].set(xlabel="Declared g(z) shape, not a physically known transfer",
                ylabel="conditional ||gamma_app||, dimensionless",
                title="One CF4 catalogue, four incompatible radial transfer assumptions")
    axes[0].grid(axis="y",alpha=.2)
    axes[1].plot(idx,cos,"o-",label="STF direction cosine vs g=1")
    axes[1].plot(idx,[profiles[k]["relative_information_eigenvalues"][0] for k in KERNELS],
                 "s-",label="minimum nuisance-profiled relative eigenvalue")
    axes[1].set_xticks(idx,["1","z/.05",".05/z","(1+z)/1.05"],rotation=20)
    axes[1].set(xlabel="Four *hypothetical* g(z) source response shapes",
                ylabel="conditional geometric/working-law diagnostic",
                title="STF direction and Schur information are kernel-dependent")
    axes[1].legend(fontsize=7);axes[1].grid(alpha=.2)
    fig.savefig(output/"cf4_physical_transfer_unknown_sensitivity.png",dpi=155)
    plt.close(fig)
    baseline=profiles[KERNELS[0]]
    (output/"REPORT_KO.md").write_text(
       "# P6 K02: 실제 CF4 apparent STF와 물리 광학 response 미식별성\n\n"
       "35,970 grouped source, z_CMB/DMzp/eDMzp/J2000 및 4개 method family. "
       "기존 source 14 nuisance 및 .15 mag +250 km/s diagonal working error를 "
       "고정하고, 서로 다른 선언적 radial shape g(z)에 대한 5차원 apparent STF를 "
       "다시 계산했다. g(z)는 실제 Bianchi/GR light-cone transfer가 아니다.\n\n"
       f"Baseline g=1 source STF norm={baseline['apparent_frobenius_5norm']:.9g}, "
       f"기존 exact Schur regression max={baseline_regression['apparent_STF_5vector_maxabs']:.3g}. "
       "Four radial-shape direction cosines and conditional eigenvalues in result.json.\n\n"
       "두 구성적 비식별성 증명: (1) unknown positive physical transfer gain lambda가 "
       "있으면 fitted gamma~1/lambda, covariance~1/lambda²로 재변환되어 실제 physical Sigma "
       "amplitude는 유한하게 식별되지 않는다. (2) 방향별 STF calibration을 네 method "
       "각각에 자유롭게 허용하면 global STF template B=sum_m B_m, "
       f"실제 source nuisance projection residual={witness['relative_projected_global_STF_norm']:.4g}; "
       "따라서 정확히 5개 global 템플릿이 상대 nuisance 공간에 소거된다. "
       "이 calibration 모형은 **가상의 worst-case 시스템atics**이며 CF4가 실제로 "
       "이런 오차를 가지고 있다는 증거는 아니다.\n\n"
       "K01에서 도출한 한 사건 -dlnE/dt_u = H-A dot skylook+sigma_nn 는 "
       "CF4 광도거리 residual mu_i를 직접 계산하는 광선수송함수가 아니며, "
       "그 중간 source-time/geodesic/peculiar covariance를 구현하지 않고 "
       "physical sigma, omega, A, beta를 fit한 것으로 판정하지 않는다. "
       "Legacy signed x,F,Pi,Q,G_F full posterior도 식별되지 않았다.\n",
       encoding="utf-8")
    print("CF4_K02_COMPLETE_SOURCE_CONDITIONAL",
          "norms",np.round(norms,7).tolist(),
          "axis_cos",np.round(cos,7).tolist(),
          "gain0.1_10",[x["source_refitted_apparent_STF_frobenius_norm"] for x in gain_test],
          "calibration_global_STF_projection",witness["relative_projected_global_STF_norm"],
          "runtime",round(result["runtime_seconds"],4),flush=True)
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    run(args.output_dir)
