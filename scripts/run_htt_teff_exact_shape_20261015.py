#!/usr/bin/env python3
"""P2/P1 actual-source exact Teff l2+l3: power-only versus angular-shape contribution.

One observed Planck CMB sky, nine processing variants; source-gated FFP10
999 CMB signal and 300 noise maps processed with the SAME temperature mask.
All new metrics are deterministic functions of the same harmonic data.
No cosmic null p-value, sourceframe shear posterior or independent likelihood.
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

from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition
from obsstat.mes_eps_measurement_bridge import fixed_ols_operator,fit_rows_of_simulated_maps
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from run_htt_planck_mes_eps_20261015 import _independent_source_mask

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
CACHE=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
L23=ROOT/"docs/research_program/observational_publication_20261015/legacy_modern_obs_integration_20261015/results/observed_planck_l23_exact_F4_v1/result.json"
EXPECT={"source":"900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459",
        "cache":"86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for c in iter(lambda:f.read(8<<20),b""):
            h.update(c)
    return h.hexdigest()


def quants(x):
    return np.quantile(np.asarray(x),[.05,.16,.5,.84,.95]).tolist()


def _analytic_power_only(a):
    # source real-lm orthonormality is part of the registered source layout.
    return 6*np.sum(np.asarray(a,float)**2,axis=1)/(
        4*np.pi*(2.72548e6)**2)


def calculate(path):
    if path.exists():
        raise FileExistsError("create-only output path")
    if sha(SOURCE)!=EXPECT["source"] or sha(CACHE)!=EXPECT["cache"]:
        raise RuntimeError("source image/FFP source bytes changed")
    previous=json.loads(L23.read_text())
    if previous["source_planck_temperature_coeff_sha256"]!=EXPECT["source"]:
        raise RuntimeError("previous source layout changed")
    with np.load(SOURCE,allow_pickle=False) as z:
        names=[str(x) for x in z["names_T"]]
        observed=np.asarray(z["coeff_T"][:,:12],float)
    if observed.shape!=(9,12) or len(set(names))!=9:
        raise RuntimeError("Planck nine processing images of ONE physical sky expected")
    a=quartic_power_shape_decomposition(observed)
    first_l23=previous["per_actual_same_sky_processing"]
    for i,name in enumerate(names):
        assert abs(a["deltaF4"][i]-
                   first_l23[name]["deltaF4_l2_l3"])<1e-22
        assert abs(a["power_only_6variance"][i]-
                   _analytic_power_only(observed[i:i+1])[0])<3e-24
    _,Y=pixel_fit_geometry(nside=64)
    with np.load(CACHE,allow_pickle=False) as z:
        mask=np.asarray(z["common_mask"],float)
        selected,source_masks,meta=_independent_source_mask(mask)
        if selected.sum()!=26846:
            raise RuntimeError("common source temperature mask mismatch")
        op,opmeta=fixed_ols_operator(Y,selected)
        if z["cmb_maps"].shape!=(999,49152) or z["noise_maps"].shape!=(300,49152):
            raise RuntimeError("expected exact 999/300 cache arrays")
        cm=np.asarray(fit_rows_of_simulated_maps(z["cmb_maps"],selected,op,count=999,chunk=20))
        no=np.asarray(fit_rows_of_simulated_maps(z["noise_maps"],selected,op,count=300,chunk=20))
        ids_signal=np.asarray(z["cmb_ids"],int)
        ids_noise=np.asarray(z["noise_ids"],int)
    assert len(set(ids_signal.tolist()))==999 and len(set(ids_noise.tolist()))==300
    b=quartic_power_shape_decomposition(cm[:,4:16])
    c=quartic_power_shape_decomposition(no[:,4:16])
    p=quartic_power_shape_decomposition(cm[:300,4:16]+no[:,4:16])
    for label,rec in (("actual",a),("cmb",b),("noise",c),("paired",p)):
        if np.max(np.abs(rec["deltaF4"]-
                         rec["power_only_6variance"]-
                         rec["shape_excess_4cubic_plus_quartic"]))>6e-24:
            raise RuntimeError(label+" exact power/shape decomposition failed")
    max_excess=np.max(np.abs(a["shape_excess_4cubic_plus_quartic"]))
    max_amp=np.max(a["power_only_6variance"])
    results={
        "schema":"htt.integrated_legacy_exact_Teff_l23_power_shape/1",
        "input_planck_source_SHA256":EXPECT["source"],
        "input_ffp10_cache_SHA256":EXPECT["cache"],
        "reference_legacy_l23_result_SHA256":sha(L23),
        "claim":"DETERMINISTIC_SAME_SOURCE_CMB_FEATURE_NOT_PHYSICAL_INDEPENDENT_EVIDENCE",
        "one_real_cmb_sky_processing_products":9,
        "CMB_only_simulation_ids_count":999,
        "noise_only_simulation_ids_count":300,
        "paired_first300_noise_count":300,
        "source_masks":source_masks,
        "selected_temperature_pixels":int(selected.sum()),
        "source_harmonic_convention":"real orthonormal spherical harmonics l=2,3, total 12 coefficients microK",
        "power_theorem":"6 <t^2> = 6 sum_{l=2,3,m} a_lm^2/(4pi T0^2)",
        "shape_theorem":"F4 - 1 -6<t^2> = 4<t^3> + <t^4>; normalized s3=<t^3>/v^(3/2), k4=<t^4>/v^2",
        "same_sky_9":{
            names[i]:{
               "power_only_6variance":float(a["power_only_6variance"][i]),
               "higher_order_shape_excess":float(a["shape_excess_4cubic_plus_quartic"][i]),
               "total_deltaF4":float(a["deltaF4"][i]),
               "normalized_skewness":float(a["normalized_skewness"][i]),
               "normalized_kurtosis":float(a["normalized_kurtosis"][i]),
               "ell3_over_ell2_power":float(a["ell2_ell3_quadrupole_octupole_power_ratio"][i])
            } for i in range(len(names))},
        "nine_same_sky_shape_excess_maxabs":float(max_excess),
        "nine_same_sky_shape_over_power_bound":float(max_excess/np.min(a["power_only_6variance"])),
        "CMB_only_skewness_quantiles":quants(b["normalized_skewness"]),
        "CMB_only_kurtosis_quantiles":quants(b["normalized_kurtosis"]),
        "CMB_only_shape_excess_quantiles":quants(b["shape_excess_4cubic_plus_quartic"]),
        "noise_only_shape_excess_quantiles":quants(c["shape_excess_4cubic_plus_quartic"]),
        "paired_shape_excess_quantiles":quants(p["shape_excess_4cubic_plus_quartic"]),
        "CMB_only_deltaF4_quantiles":quants(b["deltaF4"]),
        "actual_vs_sim_null":"NO_P_VALUE_RELEASE_AND_SELECTION_NOT_END_TO_END_QUALIFIED",
        "legacy_filling_F":"NOT_EQUAL_TO_F4",
        "scientific_admission":{
            "P2_temperature_morphology":"SOURCE_CONDITIONAL_ONLY",
            "P1_x_F_Pi_Q_GF":"NO_JOINT_POSTERIOR",
            "P3_CF4_joint_with_CMB":"NO_COMMON_TRANSFER_COVARIANCE",
            "P4_global_tilt_vs_boost":"NOT_MEASURED",
        },
    }
    path.mkdir(parents=True)
    (path/"result.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
    np.savez_compressed(path/"actual_and_ffp10_shape_source.npz",
                        real_product_names=np.array(names),
                        observed_skewness=a["normalized_skewness"],
                        observed_kurtosis=a["normalized_kurtosis"],
                        observed_shape_excess=a["shape_excess_4cubic_plus_quartic"],
                        simulated_ids=ids_signal, simulated_skewness=b["normalized_skewness"],
                        simulated_kurtosis=b["normalized_kurtosis"],
                        noise_ids=ids_noise)
    fig,axs=plt.subplots(1,2,figsize=(12.2,4.8),layout="constrained")
    x=np.arange(len(names))
    axs[0].plot(x,a["power_only_6variance"]*1e10,marker="o",label="power-only 6<t²>")
    axs[0].plot(x,a["shape_excess_4cubic_plus_quartic"]*1e16,marker="s",
                label="higher-order shape excess ×10^16")
    axs[0].set_xticks(x,names,rotation=55,ha="right",fontsize=7)
    axs[0].set(xlabel="One Planck sky: 9 processing pipelines",
              ylabel="two components shown with DISTINCT multipliers",
              title="Exact legacy Teff F4: power dominates shape residual")
    axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
    axs[1].hist(b["normalized_skewness"],bins=36,histtype="step",
                density=True,label="999 conditional FFP10 CMB samples")
    axs[1].axvline(a["normalized_skewness"][names.index("SMICA_FULL")],
                    color="black",ls="--",label="actual SMICA_FULL")
    axs[1].set(xlabel="s3=<t³>/<t²>^(3/2), source finite ell2+3",
               ylabel="descriptive density, NOT calibrated p",
               title="Angular shape distinct from power normalization")
    axs[1].legend(fontsize=8);axs[1].grid(alpha=.2)
    fig.savefig(path/"planck_teff_power_vs_shape.png",dpi=150)
    plt.close(fig)
    (path/"REPORT_KO.md").write_text(
      "# Legacy Teff F4: observational Planck ell2+ell3 power와 morphology 분해\n\n"
      "실제 legacy TeffMomentMap의 F4를 정규직교 real Y_lm l2+l3에 정확히 연결. "
      "이 소스는 하나의 관측 CMB 하늘 9 processing 결과와 원본 FFP10 999 CMB/300 noise에 "
      "대해 통일된 온도 공통 mask(26,846)를 사용한다.\n\n"
      "Analytic variance identity: v=sum_m |a_lm|²/(4πT0²). "
      "Higher-order shape residual e=4<t³>+<t⁴>. "
      f"실제 9 결과 e 최대절대값={max_excess:.6g}, "
      f"power 대비 보수적 비={results['nine_same_sky_shape_over_power_bound']:.6g}; "
      f"SMICA_FULL s3={a['normalized_skewness'][names.index('SMICA_FULL')]:.9g}, "
      f"k4={a['normalized_kurtosis'][names.index('SMICA_FULL')]:.9g}.\n\n"
      "Shape normalized statistic은 단순 C2/C3 재표현보다 형태 정보를 남길 수 있으나, "
      "원본 계수의 함수이므로 독립 likelihood로 다시 곱할 수 없다. "
      "mask/beam/high-ell, observer dipole, FFP10 end-to-end null이 검증되기 전에는 "
      "형태 anomaly p나 physical shear/tilt 제약으로 승격하지 않는다.\n",
      encoding="utf-8")
    print("SHAPE_REAL_SOURCE_RESULT",{
      "SMICA":results["same_sky_9"]["SMICA_FULL"],
      "shape_excess_max":max_excess,
      "relative_to_power":results["nine_same_sky_shape_over_power_bound"],
      "999_CMB_skew_quantiles":results["CMB_only_skewness_quantiles"]
    })
    return results


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    calculate(args.output_dir)
