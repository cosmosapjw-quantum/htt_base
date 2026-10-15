#!/usr/bin/env python3
"""Actual FFP10 999-source empirical HTT box pushforward, not a posterior.

Preserves original observed Planck ONE SKY nine processing variants as
correlated alternatives, source-matched FFP10 CMB 999 IDs and paired 300
CMB+noise IDs; this is a finite simulation measure, not latent physical
kinematic draws. Unknown signed curvature/tilt leave full x/Q/Pi
unidentified despite algebraic MES sector ceilings. F, G_F undefined.
"""
from __future__ import annotations

import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.s02_ffp_source_partial_pushforward import (
 source_mes_box,scalar_mes_regression,pi_box_strict,descriptive_summary
)
from obsstat.publication_functionals import finite_functional_image

ROOT=Path(__file__).resolve().parents[1]
EPS=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/results_v2/conditional_ffp10_eps_samples.npz"
COEFF=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
PARENT=ROOT/"docs/research_program/observational_publication_20261015/results/S02_real_planck_typed_partial_v1/result.json"
K1=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
CACHE_SHA="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
COEFF_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
SOURCE_PARENT=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/results_v2/result.json"


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(8<<20),b""):
            h.update(data)
    return h.hexdigest()


def csv_source_case(box,tail,reg):
    return {"n_empirical_simulations":len(box["ids"]),
            "source_scope":"NOT_A_PHYSICAL_POSTERIOR",
            "distribution_of_mathematical_ceiling":descriptive_summary(box),
            "scalar_mes_regression":reg,
            "strict_box_Pi":{k:(v.tolist() if isinstance(v,np.ndarray) else v)
                             for k,v in tail.items()}}


def run(out:Path):
    if out.exists():raise FileExistsError("create-only numerical source result")
    start=time.perf_counter()
    if digest(COEFF)!=COEFF_SHA or digest(K1)!=CACHE_SHA:
        raise RuntimeError("original actual Planck or K1 489MB gated simulation archive changed")
    meta=json.loads(SOURCE_PARENT.read_text())
    old=json.loads(PARENT.read_text())
    if (meta["FFP10_cache_sha256"]!=CACHE_SHA or
        old["source_sky_realization_count"]!=1 or
        old["source_processing_product_count"]!=9):
        raise RuntimeError("previous source science identity changed")
    with np.load(COEFF,allow_pickle=False) as x:
        names=[str(v) for v in x["names_T"]]
        if len(names)!=9:
            raise RuntimeError("9 processing outputs refer to ONE true sky")
    with np.load(K1,allow_pickle=False) as k:
        cmbids=np.asarray(k["cmb_ids"])
        noiseids=np.asarray(k["noise_ids"])
    if len(cmbids)!=999 or len(noiseids)!=300 or len(set(map(str,cmbids)))!=999:
        raise RuntimeError("unique original 999 source realization IDs needed")
    if not np.array_equal(cmbids[:300],noiseids):
        raise RuntimeError("FFP10 paired noise and CMB IDs mismatch")
    with np.load(EPS,allow_pickle=False) as f:
        signal=np.asarray(f["eps_cmb_same_mask"],float)
        full=np.asarray(f["eps_cmb_full"],float)
        paired=np.asarray(f["eps_first300_paired"],float)
        pair_diff=np.asarray(f["eps_noise_difference"],float)
        mask_minus_full=np.asarray(f["eps_mask_minus_full"],float)
    if signal.shape!=(999,2) or full.shape!=(999,2) or paired.shape!=(300,2):
        raise RuntimeError("parent FFP10 source 999/300 epsilon array shapes changed")
    matching=float(np.max(abs(paired-signal[:300]-pair_diff)))
    if matching>3e-16 or np.max(abs((signal-full)-mask_minus_full))>3e-16:
        raise RuntimeError("FFP10 same simulation paired EPS and mask/full differences not identical")

    boxes={}
    checks={}
    for name,eps,ids in (("signal_masked_999",signal,cmbids),
                         ("signal_full_999",full,cmbids),
                         ("paired_CMB_noise_300",paired,cmbids[:300])):
        box=source_mes_box(eps,ids)
        boxes[name]=box
        checks[name]=scalar_mes_regression(eps)
    actual_lo=boxes["signal_masked_999"]["q_low"]
    lo_min=float(actual_lo.min());lo_max=float(actual_lo.max())
    grid=np.unique(np.r_[np.linspace(1.05*lo_min,.95*lo_max,161),-.01,0.,.5,1.])
    tails={name:pi_box_strict(box,grid) for name,box in boxes.items()}
    # Compare both "full" and masked source for same 999 IDs; never treat
    # them as independent draws or a physical selection-calibrated null.
    paired_Uerr={
      "maxabs_eps_pair_noise_regression":matching,
      "same_999_mask_minus_full_ratio_RMS":
       float(np.sqrt(np.mean((boxes["signal_masked_999"]["q_low"]-
                              boxes["signal_full_999"]["q_low"])**2))),
      "paired_300_CMB_noise_minus_CMB_ratio_RMS":
       float(np.sqrt(np.mean((boxes["paired_CMB_noise_300"]["q_low"]-
                              boxes["signal_masked_999"]["q_low"][:300])**2))),
    }

    # Under the *actual* 999 source simulation IDs we assign mathematical
    # unresolved physical sectors, not invented correlated Gaussian draws.
    # This invokes the original legacy-modern functionals exactly and
    # preserves 100% unknown probability mass before ANY renormalization.
    atoms=[]
    for ident,w,us in zip(cmbids,boxes["signal_masked_999"]["weights"],
                          boxes["signal_masked_999"]["U_sigma"],strict=True):
        atoms.append({
           "sample_id":"ffp10_cmb_"+str(ident),
           "weight":float(w),
           "congruence":"HYPOTHETICAL_U_NORMAL_NOT_PHYSICAL_OBSERVED_HISTORY",
           "components":{"Sigma2":None,"W2":None,
                         "Omega_tilt":None,"DeltaOmega_k":None},
           "U_sigma":float(us),"sector_value":None,
           "sector_ceiling":float(us),
           "depth_F":{"reference":None,"comparison":None}
        })
    finite=finite_functional_image(
        atoms,thresholds=[-.01,0.,.5,1.],gf_floor=.05,
        common_congruence="HYPOTHETICAL_U_NORMAL_NOT_PHYSICAL_OBSERVED_HISTORY",
        reference_bin="FAKE_DEPTH_UNAVAILABLE_SOURCE_REFERENCE",
        comparison_bin="FAKE_DEPTH_UNAVAILABLE_SOURCE_COMPARISON")
    if any(abs(finite["missing_mass"][key]-1)>2e-12
           for key in ("x_C","Q","F")):
        raise RuntimeError("unobserved Gauss sectors were silently filled")
    if not all(e["unconditional_outer_interval"]==[0.,1.]
               for e in finite["Pi_Q_strict_threshold_outer_intervals"]):
        raise RuntimeError("physical complete Q improperly collapsed")
    if finite["G_F"]["point_identified"]:
        raise RuntimeError("missing real depth F forced identified G_F")

    source={
       "schema":"htt.P1_S02_FFP10_full_simulation_empirical_partial_image/1",
       "date_KST":"2026-10-15",
       "input_gated_FFP10_cache_sha256":CACHE_SHA,
       "input_actual_planck_source_sha256":COEFF_SHA,
       "parent_FFP_999_epsilon_source_npz_sha256":digest(EPS),
       "previous_observed_one_sky_S02_sha256":digest(PARENT),
       "simulated_CMB_distinct_ids_count":999,
       "distinct_noise_ids_count":300,
       "source_paired_signal_noise_cmb_ids_equal":True,
       "observed_actual_CMB_sky_count":1,
       "observed_same_sky_processing_products":names,
       "processing_products_are_independent_latent_observations":False,
       "source_empirical_simulation_measure":"999 fixed source simulations each weight 1/999, not a posterior from cosmological data",
       "physical_C1_C2_intrinsic_eps1":"UNVERIFIED_AND_SET_TO_ZERO_COUNTERFACTUALLY",
       "MES_sector_anchors":{name:descriptive_summary(box)
                              for name,box in boxes.items()},
       "scalar_verification":checks,
       "strict_tail_Q_flat_untilted_mathematical_product_box":{
          name:csv_source_case(box,tails[name],checks[name])
          for name,box in boxes.items()},
       "registered_original_HTT_partial_functions_on_same_999_simulations":{
         "missing_mass":finite["missing_mass"],
         "Pi_Q_at_predeclared_thresholds":finite["Pi_Q_strict_threshold_outer_intervals"],
         "G_F_generic_unknown_depth_F_outer":finite["G_F"],
         "claim":"FORMAL_FUNCTIONAL_IMAGE_ON_FINITE_EMPIRICAL_SIMULATION_MEASURE_NOT_PHYSICAL_POSTERIOR",
       },
       "source_noise_and_mask_variation":paired_Uerr,
       "physical_total_signed_x_C":"UNBOUNDED_WITH_UNMEASURED_SIGNED_CURVATURE",
       "physical_full_Q_support":"UNBOUNDED_BOTH_SIGNS",
       "physical_full_Pi_Q_at_any_finite_threshold":[0.,1.],
       "F_posterior":"UNDEFINED_NOT_MEASURED",
       "G_F_actual_depth_function":"UNDEFINED_NO_SAME_DRAW_DEPTH_F",
       "actual_CF4_apparent_STF_used_as_physical_shear":False,
       "actual_planck_nine_products_combined_as_independent_likelihood":False,
       "physical_shear_vorticity_curvature_tilt_posterior":"ABSENT",
       "scientific_claim":"FFP10_SOURCE_COHORT_CONDITIONAL_ALGEBRAIC_PI_ENVELOPE_ONLY",
       "runtime_seconds":time.perf_counter()-start,
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n")
    np.savez_compressed(out/"ffp10_mes_conditional_pi_source.npz",
         cmb_ids=np.asarray(cmbids),noise_ids=np.asarray(noiseids),
         eps_masked=signal,eps_full=full,eps_paired=paired,
         thresholds=grid,
         masked_USigma=boxes["signal_masked_999"]["U_sigma"],
         masked_UOmega=boxes["signal_masked_999"]["U_omega"],
         masked_Q_box_low=boxes["signal_masked_999"]["q_low"],
         full_Q_box_low=boxes["signal_full_999"]["q_low"],
         paired_Q_box_low=boxes["paired_CMB_noise_300"]["q_low"],
         masked_pi_box_lower=tails["signal_masked_999"]["lower"],
         masked_pi_box_upper=tails["signal_masked_999"]["upper"],
         full_pi_box_lower=tails["signal_full_999"]["lower"],
         paired_pi_box_lower=tails["paired_CMB_noise_300"]["lower"])
    fig,axes=plt.subplots(1,2,figsize=(11.6,4.7),layout="constrained")
    x=grid
    for name,label in (("signal_masked_999","999 FFP10 CMB masked"),
                       ("signal_full_999","same 999 full HEALPix"),
                       ("paired_CMB_noise_300","first 300 CMB+noise same ID")):
        axes[0].plot(x,tails[name]["lower"],label=label)
    axes[0].plot(x,tails["signal_masked_999"]["upper"],ls=":",color="black",
                 label="flat/untilted Q box upper Pi")
    axes[0].set(xlim=(max(lo_min*1.08,-.015),0.002),
          xlabel="strict Q threshold t, only flat/untilted hypothetical box",
          ylabel="source empirical Pi_Q(t) completion envelope lower",
          title="999 simulations: conditional MES Q box, NOT observed posterior")
    axes[0].legend(fontsize=7);axes[0].grid(alpha=.2)
    axes[1].plot(x,np.zeros(len(x)),color="black",label="full unknown x/Q Pi lower")
    axes[1].plot(x,np.ones(len(x)),color="black",ls="--",label="full unknown x/Q Pi upper")
    axes[1].set(xlim=(-.01,1),ylim=(-.03,1.03),
          xlabel="strict Q threshold t",
          ylabel="conservative complete physical Pi_Q outer",
          title="Unobserved curvature and tilt: cannot fill missing mass")
    axes[1].legend(fontsize=7);axes[1].grid(alpha=.2)
    fig.savefig(out/"planck_ffp10_pi_q_partial_identification.png",dpi=150)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
        "# S02: 999 실제 FFP10 소스 모의실현의 부분식별 pushforward\n\n"
        "실제 Planck 동일 하늘 9개 처리는 독립 표본으로 가중하지 않는다. "
        "FFP10 CMB 999 source IDs를 하나의 empirical simulation law로만 사용. "
        "original MES geodesic eps1=0 C1/C2 UNVERIFIED 조건에서 각 source의 "
        "U_sigma/U_omega가 정의된다. flat/untilted 추가 가정의 box Q는 "
        "[-Uomega/Usigma,1]이며, 그 위 모든 수학적 completion의 strict "
        "Pi(t) 상/하한을 endpoint witness로 검산했다. "
        "물리적 Q에는 signed curvature, tilt, vorticity/shear history를 "
        "관측하지 않아 full Pi(t)=[0,1]밖에 없다. "
        "F depth와 G_F posterior는 정의되지 않는다. "
        "일반 추상 지지로서의 G_F floor [.05,20]을 실제 깊이 측정처럼 "
        "제시하면 안 된다.\n",encoding="utf-8")
    print("S02_FFP10_SOURCE_PARTIAL_COMPLETE",len(cmbids),"paired",len(noiseids),
          "U_sigma_med",np.median(boxes["signal_masked_999"]["U_sigma"]),
          "Q_low_median",np.median(boxes["signal_masked_999"]["q_low"]),
          "noise_effect_rms",paired_Uerr["paired_300_CMB_noise_minus_CMB_ratio_RMS"],
          "full_physical_undefined",finite["missing_mass"],flush=True)
    return source


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    run(a.output_dir)
