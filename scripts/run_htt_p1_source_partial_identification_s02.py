#!/usr/bin/env python3
"""Actual Planck source-conditioned MES algebra and missing-physics partial ID.

Never converts 9 same-sky processing alternatives to 9 posterior atoms.
The physical signed x_C and Pi_Q remain unconstrained without a verified
common-congruence kinematic/tilt/curvature joint observation law.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from obsstat.publication_source_partial_identification import (
    source_case_from_planck_temperature_alm,
    strict_tail_probability_identified_set,
)

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
SOURCE_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
PREVIOUS=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/results_v2/result.json"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(out:Path):
    if out.exists():
        raise FileExistsError("create-only P1 source-conditioned result")
    if digest(INPUT)!=SOURCE_SHA:
        raise RuntimeError("actual same-sky Planck source coefficients changed")
    j=json.loads(PREVIOUS.read_text())
    with np.load(INPUT,allow_pickle=False) as data:
        names=[str(z) for z in data["names_T"]]
        x=np.asarray(data["coeff_T"],float)
    if x.shape!=(9,32) or len(set(names))!=9:
        raise RuntimeError("exactly 9 related processing images from one sky")
    per={}
    for name,row in zip(names,x):
        case=source_case_from_planck_temperature_alm(row)
        parent=j["nine_same_sky_map_rows"][name]["algebraic_eps1_zero"]
        assert np.isclose(case["U_sigma"],parent["Sigma2_anchor_only_if_conditions_met"],rtol=2e-13,atol=0)
        assert np.isclose(case["U_omega"],parent["W2_anchor_only_if_conditions_met"],rtol=2e-13,atol=0)
        intervals={}
        for threshold in (-.01,0.,.5,1.):
            intervals[str(threshold)]={
                "full_physically_unidentified_Pi_Q_outer_interval":
                    strict_tail_probability_identified_set(threshold,case["full_unknown_curvature_tilt_Q_domain"]),
                "flat_untilted_extra_assumptions_any_probability_measure_Pi_outer_interval":
                    strict_tail_probability_identified_set(threshold,case["flat_untilted_counterfactual_Q_outer_interval"]),
            }
        per[name]={"conditional_source_mes":case,
                   "probability_measure_without_joint_posterior":intervals}
    sigma=np.asarray([per[m]["conditional_source_mes"]["U_sigma"] for m in names])
    omega=np.asarray([per[m]["conditional_source_mes"]["U_omega"] for m in names])
    ratio=np.asarray([per[m]["conditional_source_mes"]["U_omega_over_U_sigma"] for m in names])
    result={
        "schema":"htt.P1_S02_real_planck_same_sky_conditioned_partial_identification/1",
        "claim_tier":"ACTUAL_9_SOURCE_PROCESSING_ALGEBRAIC_CONDITIONAL_ONLY_NOT_PHYSICAL_JOINT_POSTERIOR",
        "date":"2026-10-15",
        "input_source_sha256":SOURCE_SHA,
        "parent_previous_result_sha256":digest(PREVIOUS),
        "source_sky_realization_count":1,
        "source_processing_product_count":9,
        "processing_product_weights_or_Bayesian_probability":"NOT_ASSIGNED",
        "sample_product_independence":"FALSE_SAME_PHYSICAL_CMB_SKY",
        "observer_intrinsic_eps1_scenario":"EQUAL_ZERO_HYPOTHESIS_NOT_MEASURED",
        "all_fundamental_observers_C1_C2":"UNVERIFIED",
        "full_physical_signed_x_C_identified":"NO",
        "full_Q_compatibility_set":"UNBOUNDED_SIGNED_REALS_WHEN_CURVATURE_UNRESTRICTED",
        "full_Pi_Q_conservative_outer_interval_at_any_finite_threshold":[0.,1.],
        "F_positive_sector_posterior":"ABSENT",
        "GF_depth_posterior":"ABSENT",
        "actual_CF4_source_frame_tensor_joint_posterior":"ABSENT",
        "flat_untilted_counterfactual_branch":"NOT_AN_INFERRED_OBSERVED_PHYSICAL_STATE",
        "per_same_sky_source":per,
        "processing_envelope":{
            "U_sigma_minmax":[float(sigma.min()),float(sigma.max())],
            "U_omega_minmax":[float(omega.min()),float(omega.max())],
            "ratio_Uomega_over_Usigma_minmax":[float(ratio.min()),float(ratio.max())],
            "U_sigma_spread_rel_to_SMICA_FULL":float((sigma.max()-sigma.min())/sigma[names.index("SMICA_FULL")]),
            "covariant_real_source_cl_to_tau":"SAG eq17 as confirmed by previous Loop9",
        },
        "positive_result":"source-conditioned MES denominator amplitude processing dependence reproducible",
        "negative_identification_result":"source CMB multipoles do not identify total signed x or Pi even with MES hypothetical sector ceilings"
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    fig,ax=plt.subplots(1,2,figsize=(11,4.2),layout="constrained")
    t=np.arange(len(names))
    ax[0].plot(t,sigma*1e9,"o-",label="conditional U_sigma (x10^-9)")
    ax[0].plot(t,omega*1e9,"s-",label="conditional U_omega (x10^-9)")
    ax[0].set_xticks(t,names,rotation=52,ha="right",fontsize=7)
    ax[0].set(ylabel="hypothetical sector upper norm squared [10^-9]",
              title="One Planck sky: MES source-processing sensitivity")
    ax[0].grid(alpha=.2);ax[0].legend(fontsize=8)
    ax[1].plot(t,-ratio,marker="o",label="flat untilted Q hypothetical lower")
    ax[1].axhline(1,color="black",ls="--",label="flat untilted Q hypothetical upper")
    ax[1].set_xticks(t,names,rotation=52,ha="right",fontsize=7)
    ax[1].set(ylabel="Counterfactual signed Q support, NOT posterior",
              title="With unmeasured curvature: full Q remains unbounded")
    ax[1].grid(alpha=.2);ax[1].legend(fontsize=8)
    fig.savefig(out/"planck_mes_counterfactual_identifiability.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
      "# P1 S02: 실제 Planck 동일 하늘의 MES source denominator와 물리적 미식별성\n\n"
      "실제 Planck 처리 제품 9개는 하나의 하늘이다. 이 코드에서 processing 제품에 "
      "확률 가중치를 부여하지 않으며, posterior 표본 9개라고 부르지 않는다.\n\n"
      f"eps1=0과 모든 관측자 C1/C2 미분 조건을 '추가 가정'했을 때 계산되는 "
      f"shear-sector U_sigma 범위는 {float(sigma.min()):.9g}–{float(sigma.max()):.9g}; "
      f"omega-sector U_omega 범위는 {float(omega.min()):.9g}–{float(omega.max()):.9g}. "
      f"선택한 SMICA_FULL 대비 U_sigma processing spread는 "
      f"{result['processing_envelope']['U_sigma_spread_rel_to_SMICA_FULL']:.4%}.\n\n"
      "조건부 counterfactual flat+untilted+geodesic 0<=Sigma2<=U_sigma, "
      "0<=W2<=U_omega일 때 Q∈[-U_omega/U_sigma,1]이다. "
      "하지만 미측정 curvature DeltaOmega_k를 unrestricted signed로 남기면 x_C와 Q는 "
      "실수 전체에 미식별이며, 어떤 t에서나 Pi_Q(t)∈[0,1]밖에 말할 수 없다. "
      "이는 posterior p-value나 유의성 구간이 아니다. "
      "F 및 G_F도 표본에 대한 실제 positive-sector와 depth source가 없어 미측정이다.\n",
      encoding="utf-8")
    print("S02_REAL_ONE_SKY",len(names),"U_SIGMA_RANGE",sigma.min(),sigma.max(),
          "U_OMEGA_RANGE",omega.min(),omega.max(),
          "Q_FULL_UNIDENTIFIED")
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    run(a.output_dir)
