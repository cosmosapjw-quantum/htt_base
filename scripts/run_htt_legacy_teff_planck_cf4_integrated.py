#!/usr/bin/env python3
"""Three-lineage HTT legacy Teff -> tensorized response -> actual observational source.

ACTUAL Planck PR3 one-sky 9 temperature-processing products, gated FFP10
CMB-only 999/noise-only 300, plus a SEPARATE CF4 grouped-source
flat-LCDM reference from the verified independent observation branch.

Only temperature l2 is used for exact Teff F4(delta), and the dipole
is *explicitly set to zero as a source-truncated scenario* (not observed
intrinsic CMB epsilon1=0 or physical vanishing 4-acceleration). This
calculation yields a finite ansatz deterministic feature, NOT a new
cosmological likelihood, physical fourth energy moment, physical
shear/tilt posterior, or independent CMB evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.legacy_teff_tensor_observation_bridge import (
    T0_MICROK,
    legacy_f4_exact_increment,
    bolometric_proxy_shift_microK,
    masked_planck_quadrupole_to_temperature_stf,
    quadrupole_morphology_stf,
    old_axis_A_W_Q_V_to_tensors,
    real_harmonic_quadrupole_source_consistency,
)
from obsstat.mes_eps_measurement_bridge import (
    fixed_ols_operator,fit_rows_of_simulated_maps
)
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from run_htt_planck_mes_eps_20261015 import _independent_source_mask

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"docs/research_program/observational_publication_20261015/legacy_modern_obs_integration_20261015"
LEGACY=STUDY/"inputs/original_legacy_teff_extended.py"
SOURCE=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
CACHE=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
GATE=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/generated/k1_e2e_cache_gate_ffp10_smica.json")
CF4=ROOT/"docs/research_program/observational_publication_20261015/results/H02_flrw_method_decomposition_v2/result.json"
EXPECTED={
 "legacy":"39593691b86d5af1fb1ea2e7e02a9798a589b968d23d088288ed6d3b83aebf53",
 "planck":"900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459",
 "ffp":"86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb",
}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):
            h.update(b)
    return h.hexdigest()


def _legacy_module_snapshot():
    if sha(LEGACY)!=EXPECTED["legacy"]:
        raise RuntimeError("legacy Teff original user-code bytes changed")
    spec=importlib.util.spec_from_file_location(
        "_legacy_httt_teff_source_original_sha3959",LEGACY)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _source_moments(harmonic_l2):
    """Vectorized source l2 5D REAL harmonics, not source physical sigma."""
    a=np.asarray(harmonic_l2)
    if a.ndim!=2 or a.shape[1]!=5 or not np.isfinite(a).all():
        raise ValueError("complete finite l2 5D real harmonic source rows expected")
    s=masked_planck_quadrupole_to_temperature_stf(a)
    t=legacy_f4_exact_increment(np.zeros((len(a),3)),s,require_positive=True)
    morphology=quadrupole_morphology_stf(s)
    # Direct real-sky harmonic identity: <t²>=sum_m a_lm²/(4pi T0²)
    harmonic_power=np.sum(a*a,axis=1)/(4*np.pi*T0_MICROK**2)
    residual=float(np.max(abs(t["mean_t2"]-harmonic_power)))
    if residual>2e-22:
        raise RuntimeError(f"spherical harmonic/STF temperature variance mismatch {residual}")
    return {"deltaF4":np.asarray(t["delta_F4"]),
            "t2":np.asarray(t["mean_t2"]),
            "t3":np.asarray(t["mean_t3"]),
            "t4":np.asarray(t["mean_t4"]),
            "chi3":np.asarray(morphology),
            "temp_bol_microK":np.asarray(bolometric_proxy_shift_microK(t["delta_F4"])),
            "orthonormal_real_m2_to_fullsky_mean_t2_maxabs":residual}


def quantiles(a):
    return [float(v) for v in np.quantile(np.asarray(a,dtype=float),
                                          [.05,.16,.5,.84,.95])]


def run(out:Path):
    if out.exists():raise FileExistsError("create-only study result directory")
    tstart=time.perf_counter()
    legacy=_legacy_module_snapshot()
    if sha(SOURCE)!=EXPECTED["planck"]:
        raise RuntimeError("real Planck source retained 9 product coefficient byte mismatch")
    gate=json.loads(GATE.read_text())
    if gate["cache_hash"].removeprefix("sha256:")!=EXPECTED["ffp"]:
        raise RuntimeError("previous independent FFP10 source gate mismatch")
    if sha(CACHE)!=EXPECTED["ffp"]:
        raise RuntimeError("actual FFP10 compact CMB+noise cache identity mismatch")
    if not gate["cache_reproducibility_green"] or gate["n_checked"]!=1299:
        raise RuntimeError("FFP10 prior 999+300 source gate not sufficient")

    with np.load(SOURCE,allow_pickle=False) as f:
        names=[str(x) for x in f["names_T"]]
        actual=np.asarray(f["coeff_T"],float)
    if actual.shape!=(9,32) or len(set(names))!=9:
        raise RuntimeError("only 9 processing products of ONE actual sky allowed")
    for k,vec in enumerate(actual):
        err=real_harmonic_quadrupole_source_consistency(vec[:5])
        if err>8e-20:
            raise RuntimeError(f"modern real->STF source harmonics mismatch {names[k]}")
    a=_source_moments(actual[:,:5])
    case={}
    for j,name in enumerate(names):
        case[name]={"deltaF4_quadrupole_only":float(a["deltaF4"][j]),
                    "delta_Tbol_uK_quadrupole_only":float(a["temp_bol_microK"][j]),
                    "quadrupole_stf_chi3":float(a["chi3"][j]),
                    "source_orthonormal_quad_variance":float(a["t2"][j]),
                    "mean_t3":float(a["t3"][j]),
                    "mean_t4":float(a["t4"][j]),
                    "physical_original_fullsky_moment":"NOT_IDENTIFIED_BY_MASKED_SOURCE"}
    legacy_cases=[]
    legacy_map=legacy.TeffMomentMap(N_theta=40,N_phi=32)
    for A,W,Q,V in ((.12,.06,.08,.04),(-.09,.03,.11,.04),(.05,0.,-.08,.01)):
        d,s=old_axis_A_W_Q_V_to_tensors(A,W,Q,V)
        old=float(legacy_map.moment(A,W,Q,V,alpha=4))
        new=float(legacy_f4_exact_increment(d,s)["F4"])
        legacy_cases.append({"A":A,"W":W,"Q":Q,"V":V,
                             "old_grid_40x32_F4":old,"exact_invariant_F4":new,
                             "absolute_difference":abs(old-new)})
    if max(q["absolute_difference"] for q in legacy_cases)>3e-14:
        raise RuntimeError("actual original legacy .moment and modern exact F4 disagree")

    n,y=pixel_fit_geometry(nside=64)
    with np.load(CACHE,allow_pickle=False) as f:
        mask=np.asarray(f["common_mask"],float)
        chosen,mask_ids,maskinfo=_independent_source_mask(mask)
        R,geometry=fixed_ols_operator(y,chosen)
        if len(chosen)!=49152 or int(chosen.sum())!=26846:
            raise RuntimeError("previous actual Planck T source mask drift")
        observed=np.asarray(f["observed_map"],float)
        obsfit=(R@observed[chosen])[4:9]
        if f["cmb_maps"].shape!=(999,49152) or f["noise_maps"].shape!=(300,49152):
            raise RuntimeError("source FFP10 999 and 300 realization matrices required")
        ids_cmb=np.asarray(f["cmb_ids"])
        ids_noise=np.asarray(f["noise_ids"])
        if len(set(ids_cmb.tolist()))!=999 or len(set(ids_noise.tolist()))!=300:
            raise RuntimeError("source FFP IDs repeated")
        # Process all actual source CMB and noise maps with ONE source mask operator.
        cmb_fit=fit_rows_of_simulated_maps(f["cmb_maps"],chosen,R,
                                           count=999,chunk=20)
        noise_fit=fit_rows_of_simulated_maps(f["noise_maps"],chosen,R,
                                             count=300,chunk=20)
    b=_source_moments(cmb_fit[:,4:9])
    c=_source_moments(noise_fit[:,4:9])
    pair_fit=cmb_fit[:300,4:9]+noise_fit[:,4:9]
    p=_source_moments(pair_fit)
    cached_obs=_source_moments(obsfit[None,:])
    std_comparison={
      "source_law":"same released FFP10 CMB-only/noise-only 999/300 fixed-weight bank and one observed SMICA processed sky",
      "source_gate_SHA256":EXPECTED["ffp"],
      "cmb_count":999,"noise_count":300,"paired_cohort":300,
      "cmb_unique_ids":True,"noise_unique_ids":True,
      "same_sky_processing_count":9,
      "CMB_only_deltaF4_quantiles_05_16_50_84_95":quantiles(b["deltaF4"]),
      "CMB_only_quad_chi3_quantiles_05_16_50_84_95":quantiles(b["chi3"]),
      "noise_only_deltaF4_quantiles_05_16_50_84_95":quantiles(c["deltaF4"]),
      "paired_CMB_plus_noise_deltaF4_quantiles_05_16_50_84_95":quantiles(p["deltaF4"]),
      "paired_delta_vs_signal_rms":float(np.sqrt(np.mean((p["deltaF4"]-b["deltaF4"][:300])**2))),
      "cache_observed_deltaF4":float(cached_obs["deltaF4"][0]),
      "cache_obs_minus_native_SMICA_FULL_deltaF4":float(
          cached_obs["deltaF4"][0]-case["SMICA_FULL"]["deltaF4_quadrupole_only"]),
      "physical_observed_null_p":"NOT_ESTABLISHED",
    }

    csrc=json.loads(CF4.read_text())
    if csrc["source_groups"]!=35970 or csrc["physical_beyond_FLRW_claim"]!="WITHHELD":
        raise RuntimeError("CF4 independent FLRW branch scientific source scope drift")
    cf={
      "source":"independent CF4 35970-group FLRW baseline/method decomposed result",
      "source_result_sha256":sha(CF4),
      "claim":csrc["claim_tier"],
      "flat_lcdm_reference_parameters":csrc["flat_LCDM_ref_no_fit"],
      "source_shell_observed_H_eff":csrc["source_observed_H_eff_km_s_Mpc"],
      "source_shell_isotropic_FLRW_cz_over_dL":csrc["flat_LCDM_expected_source_aggregated_cz_over_dL_km_s_Mpc"],
      "source_shell_residual_logH":csrc["source_residual_logH_by_shell"],
      "far_near_decomposition":csrc["far_near_two_term_decomposition"],
      "independent_joint_CMB_CF4_likelihood":"NOT_SUPPLIED",
      "physical_common_congruence_transfer":"NOT_SUPPLIED",
    }
    # On separate CF4 source law, no Planck data is multiplied into any
    # observational posterior. It is a side-by-side physical null model
    # comparison, with CMB response and CF4 redshift window still distinct.

    result={
      "schema":"htt.legacy-modern-real-observation-teff-F4/1",
      "date_KST":"2026-10-15",
      "claim_tier":"CONDITIONAL_SOURCE_OBSERVABLE_INVARIANT_NOT_PHYSICAL_COSMOLOGY_DETECTION",
      "source_lineages":{
        "original_legacy_user_code":{
          "path":str(LEGACY.relative_to(ROOT)),"SHA256":EXPECTED["legacy"],
          "TeffMomentMap_origin":"TeffMomentMap.theta_field/moment, A-W-Q-V directional ansatz",
          "legacy_mes_constants_used_for_observations":False,
        },
        "modern_irrep":{
          "source":"htt/obsstat/planck_lowell_irrep_projection.py and r7_cmb_product_response.py",
          "orthonormal_real_basis":"l2 a20, sqrt2 Re/Im a2m in thermodynamic microK",
          "temperature_tensor_not_physical_shear":True,
          "S_cartesian_frame":"registered Planck J2000/Galactic map harmonic chart as source",
          "T0_microK":T0_MICROK,
        },
        "independent_observations":{
          "Planck_pr3_one_sky_retained_source_SHA256":EXPECTED["planck"],
          "CF4_source_ref":str(CF4.relative_to(ROOT)),
          "CF4_source_result_sha256":sha(CF4),
          "PR531_532_prior_observation_analysis":"historical/conditional comparison only; no multiplication as independent likelihood",
        },
      },
      "analytic_contract":{
          "Theta":"1 + d dot n + n^T S n; S STF, dimensionless temperature field",
          "F4":"mean fullsky Theta^4 exact under finite ansatz",
          "F4_not_legacy_F":True,
          "d_hypothesis":"ZERO_IN_TRUNCATED_L2_MODEL_ONLY; intrinsic l1 NOT MEASURED",
          "l3_and_higher_truncated":"TRUE",
          "selected_masked_projection_only":"TRUE",
          "fullsky_quadrupole_source_not_directly_observed":"TRUE",
      },
      "legacy_exact_vs_original_quad_cases":legacy_cases,
      "native_planck_9_same_sky_processing":{
         "names":names,"cases":case,
         "deltaF4_minmax":[float(a["deltaF4"].min()),float(a["deltaF4"].max())],
         "chi3_minmax":[float(a["chi3"].min()),float(a["chi3"].max())],
         "deltaTbol_microK_minmax":[float(a["temp_bol_microK"].min()),float(a["temp_bol_microK"].max())],
         "quadratic_fraction_median":float(np.median((6*a["t2"])/a["deltaF4"])),
         "cubic_fraction_median":float(np.median((4*a["t3"])/a["deltaF4"])),
         "quartic_fraction_median":float(np.median(a["t4"]/a["deltaF4"])),
         "orthonormal_l2_variance_test_maxabs":a["orthonormal_real_m2_to_fullsky_mean_t2_maxabs"],
      },
      "FFP10_CMB_NOISE_conditional":std_comparison,
      "CF4_isotropic_FLRW_and_method_composition_separate_observation":cf,
      "not_admitted_for_total_x_Q_Pi_F_GF":{
        "physical_sigma_W_A_beta":"NOT_IDENTIFIED",
        "Bianchi_transport":"NO_VALIDATED_RESPONSE",
        "physical_joint_CMB_CF4_sample":"ABSENT",
        "signed_Gauss_defect_posterior":"ABSENT",
        "calibrated_planck_null":"NOT_ESTABLISHED",
      },
      "runtime_seconds":time.perf_counter()-tstart,
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    # Save only small derived arrays, raw external source remains read-only.
    np.savez_compressed(out/"teff_source_conditioned_samples.npz",
         actual_names=np.asarray(names),
         actual_deltaF4=a["deltaF4"],
         actual_chi3=a["chi3"],
         actual_Tbol_microK=a["temp_bol_microK"],
         cmb_ids=ids_cmb,cmb_deltaF4=b["deltaF4"],
         cmb_chi3=b["chi3"],noise_ids=ids_noise,
         noise_deltaF4=c["deltaF4"],
         paired_deltaF4=p["deltaF4"])
    # One figure: each channel has a distinct physical/source interpretation.
    fig,axs=plt.subplots(1,2,figsize=(12.5,4.6),layout="constrained")
    vals=a["deltaF4"]
    axs[0].plot(np.arange(len(names)),vals*1e9,"o-",label="actual Planck 9 processing variants")
    axs[0].axhline(np.median(b["deltaF4"])*1e9,
                   ls="--",label="999 FFP10 CMB-only sample median")
    axs[0].set_xticks(np.arange(len(names)),names,rotation=50,ha="right",fontsize=8)
    axs[0].set(xlabel="Same sky under different processing; NOT 9 independent universes",
               ylabel="quadrupole-only delta F4 [1e-9]",
               title="Legacy Teff exact tensor invariant on measured Planck source")
    axs[0].grid(alpha=.2);axs[0].legend(fontsize=7)
    x=np.array(cf["source_shell_residual_logH"][:4],dtype=float)
    # The independent P3 FLRW source windows are keyed by (lo,hi), not
    # paper-DAG id. Display their AUTHENTIC source bounds.
    labels=[f"{float(z['lo']):.3f}-{float(z['hi']):.3f}"
            for z in csrc["windows"][:4]]
    axs[1].plot(np.arange(4),x,"s-",label="Observed CF4 - sourcewise isotropic FLRW reference")
    axs[1].axhline(0,color="gray",ls="--")
    axs[1].set_xticks(np.arange(4),labels,rotation=45,ha="right",fontsize=8)
    axs[1].set(xlabel="CF4 grouped source z windows",
               ylabel="residual log(cz/D) vs flat-FLRW reference",
               title="Separate CF4 analysis, NOT a joint CMB–CF4 likelihood")
    axs[1].grid(alpha=.2);axs[1].legend(fontsize=7)
    fig.savefig(out/"legacy_teff_planck_and_separate_cf4.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
      "# Legacy Teff × 현대 STF × 독립 관측의 실제 통합\\n\\n"
      f"Legacy 실제 teff_extended.py SHA={EXPECTED['legacy']}, 기존 TeffMomentMap.moment와 "
      f"현재 O(3) 불변식의 40×32 구면 구적 차이 최대="
      f"{max(z['absolute_difference'] for z in legacy_cases):.4g}.\\n\\n"
      "실제 Planck PR3의 하나의 하늘(9개 처리 방법)의 온도 사중극 모드로 "
      "완전히 선언된 l=2-only directional ansatz의 F4=<Theta^4>를 계산했다. "
      "관측 고유 ℓ=1이 없으므로 d=0은 formal source truncation이고 진짜 "
      "intrinsic dipole 0이라는 관측 사실이 아니다. l=3 이상의 모든 모드도 F4에서 제외.\\n\\n"
      f"아홉 처리 결과 deltaF4 range={result['native_planck_9_same_sky_processing']['deltaF4_minmax']}; "
      f"quadrupole STF shape chi3 range={result['native_planck_9_same_sky_processing']['chi3_minmax']}; "
      f"deltaTbol microK range={result['native_planck_9_same_sky_processing']['deltaTbol_microK_minmax']}.\\n\\n"
      "FFP10 source checksum이 검증된 999개 CMB-only와 300개 noise-only 결과를 동일 "
      "선택 mask operator에서 비교했지만 source-conditioned diagnostic이며 physical null p가 아니다.\\n\\n"
      "동시에 별도 연구 브랜치의 CF4 35,970개 데이터에서 isotropic flat-LCDM luminosity-distance "
      "response를 제거한 redshift-window residual을 그대로 인계했다. 이 결과와 CMB "
      "quadrupole을 하나의 likelihood로 곱하지 않았다. 두 소스 공통 기하·물질·방사 프레임 "
      "response, cross covariance, physical transfer가 검증되기 전에는 x,Q,Pi posterior 미확정.\\n",
      encoding="utf-8")
    print("LEGACY_ACTUAL_F4_FFPCF4_PASS",
          "Planck delta range",result["native_planck_9_same_sky_processing"]["deltaF4_minmax"],
          "chi range",result["native_planck_9_same_sky_processing"]["chi3_minmax"],
          "F4 ffpsims",len(b["deltaF4"]),len(c["deltaF4"]),
          "runtime",round(result["runtime_seconds"],3),flush=True)
    return result


if __name__=="__main__":
    pp=argparse.ArgumentParser()
    pp.add_argument("--output-dir",type=Path,required=True)
    args=pp.parse_args()
    run(args.output_dir)
