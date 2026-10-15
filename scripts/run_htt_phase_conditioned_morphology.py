#!/usr/bin/env python3
"""Actual Planck/FFP10 versus exact Gaussian fixed-C2,C3 phase-only benchmark.

Analysis is RETROSPECTIVE and SOURCE_CONDITIONAL, not an isotropy p-value.

The fixed-amplitude Gaussian phase law is mathematically exact only for
unmasked, isotropic, equal covariance in each ell, whereas the extracted
Planck and FFP10 coefficients are from a cut-sky simultaneous ell0..5
fit and source-dependent processing.  Never claim exchangeability.
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

from obsstat.teff_phase_conditioned_null import (
    theoretical_uniform_phase_moments,conditional_shape_null,
    source_rescale_phase_preserving,descriptive_source_rank
)
from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition
from obsstat.mes_eps_measurement_bridge import (
    fixed_ols_operator,fit_rows_of_simulated_maps
)
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from run_htt_planck_mes_eps_20261015 import _independent_source_mask

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
LEGACY=BASE/"legacy_modern_obs_integration_20261015"
RAW=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
SOURCE=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
PREVIOUS=LEGACY/"results/observed_planck_shape_v1/actual_and_ffp10_shape_source.npz"
EXPECTED_RAW_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
EXPECTED_SOURCE_SHA="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
SEED=20261015
DRAW_COUNT=16384


def digest(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as ff:
        for block in iter(lambda:ff.read(8<<20),b""):
            h.update(block)
    return h.hexdigest()


def quantiles(x):
    return [float(v) for v in np.quantile(np.asarray(x),[.05,.16,.50,.84,.95])]


def empirical_cdf_max_distance(a,b):
    """Descriptive empirical CDF maximum difference, NO significance value."""
    a=np.sort(np.asarray(a,float))
    b=np.sort(np.asarray(b,float))
    if a.ndim!=1 or b.ndim!=1 or len(a)==0 or len(b)==0:
        raise ValueError("nonempty sorted cohorts required")
    ticks=np.unique(np.concatenate([a,b]))
    dif=np.searchsorted(a,ticks,side="right")/len(a)-np.searchsorted(b,ticks,side="right")/len(b)
    return float(np.max(abs(dif)))


def run(output_dir:Path,*,phase_draws=DRAW_COUNT,seed=SEED):
    if output_dir.exists():
        raise FileExistsError("create-only source-conditioned research result directory")
    if digest(RAW)!=EXPECTED_RAW_SHA or digest(SOURCE)!=EXPECTED_SOURCE_SHA:
        raise RuntimeError("actual observed/source bank SHA256 mismatch")
    with np.load(RAW,allow_pickle=False) as f:
        names=[str(x) for x in f["names_T"]]
        actual=np.asarray(f["coeff_T"][:,:12],float)
    if actual.shape!=(9,12) or len(set(names))!=9:
        raise RuntimeError("exact nine same-sky source processing products expected")
    primary=actual[names.index("SMICA_FULL")]
    theory=theoretical_uniform_phase_moments(primary)
    iso=conditional_shape_null(primary,n_draws=phase_draws,seed=seed,chunk_size=512)
    obs=quartic_power_shape_decomposition(actual)
    obs_primary={
        "s3":float(obs["normalized_skewness"][names.index("SMICA_FULL")]),
        "k4":float(obs["normalized_kurtosis"][names.index("SMICA_FULL")])
    }
    if not np.isfinite(iso["s3"]).all() or not np.isfinite(iso["k4"]).all():
        raise RuntimeError("nonfinite exact ideal phase null")
    # Analytic expectation is the independent non-stochastic oracle.
    if abs(np.mean(iso["s3"]))>.03 or abs(np.mean(iso["k4"])-theory["theoretical_conditional_mean_k4"])>.035:
        raise RuntimeError("phase null Monte-Carlo disagrees with exact conditional moments")
    _,Y=pixel_fit_geometry(nside=64)
    with np.load(SOURCE,allow_pickle=False) as z:
        mask=np.asarray(z["common_mask"],float)
        selected,source_masks,maskmeta=_independent_source_mask(mask)
        if int(selected.sum())!=26846:
            raise RuntimeError("authentic Planck common T mask selected pixel count changed")
        op,opinfo=fixed_ols_operator(Y,selected)
        if z["cmb_maps"].shape!=(999,49152):
            raise RuntimeError("source saved FFP10 CMB-only bank changed")
        cmb=fit_rows_of_simulated_maps(z["cmb_maps"],selected,op,count=999,chunk=20)[:,4:16]
        src_ids=np.asarray(z["cmb_ids"],int)
    if len(src_ids)!=999 or len(set(src_ids.tolist()))!=999:
        raise RuntimeError("unique 999 simulation source IDs required")
    pre=quartic_power_shape_decomposition(cmb)
    reweighted=source_rescale_phase_preserving(cmb,primary)
    post=quartic_power_shape_decomposition(reweighted)
    with np.load(PREVIOUS,allow_pickle=False) as old:
        names_old=[str(x) for x in old["real_product_names"]]
        if names_old!=names or not np.array_equal(src_ids,old["simulated_ids"]):
            raise RuntimeError("historical unmodified FFP source IDs differ")
        np.testing.assert_allclose(pre["normalized_skewness"],old["simulated_skewness"],
                                   atol=2e-11,rtol=5e-13)
        np.testing.assert_allclose(pre["normalized_kurtosis"],old["simulated_kurtosis"],
                                   atol=2e-11,rtol=5e-13)
    # Confirm source rescaling changes per-ell amplitude but not angular phase.
    radii=np.array([np.linalg.norm(primary[:5]),np.linalg.norm(primary[5:])])
    if np.max(abs(np.linalg.norm(reweighted[:,:5],axis=1)-radii[0]))>1e-12:
        raise RuntimeError("FFP10 source reweight failed quadrupole normalization")
    if np.max(abs(np.linalg.norm(reweighted[:,5:12],axis=1)-radii[1]))>1e-12:
        raise RuntimeError("FFP10 source reweight failed octupole normalization")
    # Each source cohort generates different ANISOTROPY CONDITIONING; do not
    # pool them as independent or multiply their ranks.
    outcome={}
    for name,sample in (("ideal_gaussian_fixed_phase",iso),
                        ("FFP10_999_phase_reweighted",post),
                        ("FFP10_999_raw_processed_phase",pre)):
        result={}
        for key in ("s3","k4"):
            x=np.asarray(sample[key] if key in sample else sample["normalized_skewness" if key=="s3" else "normalized_kurtosis"])
            result[key]={
              "mean":float(np.mean(x)),"std":float(np.std(x,ddof=1)),
              "quantiles_05_16_50_84_95":quantiles(x),
              "descriptive_actual_SMICA_rank":descriptive_source_rank(
                obs_primary[key],x,centre=0. if key=="s3" else theory["theoretical_conditional_mean_k4"]),
            }
        outcome[name]=result
    iso_s=iso["s3"];iso_k=iso["k4"]
    comparison={
      "conditional_empirical_CDF_distance_s3":empirical_cdf_max_distance(iso_s,post["normalized_skewness"]),
      "conditional_empirical_CDF_distance_k4":empirical_cdf_max_distance(iso_k,post["normalized_kurtosis"]),
      "FFP10_reweighted_mean_k4_minus_analytic_isotropic_phase_expectation":
          float(np.mean(post["normalized_kurtosis"])-theory["theoretical_conditional_mean_k4"]),
      "ideal_MC_mean_k4_minus_analytic_expectation":
          float(np.mean(iso_k)-theory["theoretical_conditional_mean_k4"]),
    }
    result={
      "schema":"htt.P2_exact_conditional_fixed_C2_C3_phase_shape_source_comparison/1",
      "date_KST":"2026-10-15",
      "claim_tier":"RETROSPECTIVE_SOURCE_CONDITIONAL_MORPHOLOGY_NOT_A_CALIBRATED_PLANCK_P_VALUE",
      "study_stage":"P2_L02_PARTIAL_MATHEMATICAL_AND_SIMULATION_EVIDENCE_NOT_ACCEPTED_FULL_TASK",
      "parent_actual_legacy_teff_source":"legacy_modern_obs_integration_20261015/INTEGRATED_THEORY_CODING_OBSERVATIONS_KO.md",
      "source_observed_coeff_sha256":EXPECTED_RAW_SHA,
      "source_ffp10_cache_sha256":EXPECTED_SOURCE_SHA,
      "sampled_one_physical_observed_sky":1,
      "observed_processing_product_count":9,
      "source_ffp10_CMB_only_unique_realizations":999,
      "ideal_independent_phase_samples":phase_draws,
      "ideal_phase_random_seed":seed,
      "conditional_multipole_powers_actual_primary":theory,
      "observed_SMICA_FULL_shape":obs_primary,
      "observed_all_same_sky_processing_shapes":{
        name:{
            "s3":float(obs["normalized_skewness"][i]),
            "k4":float(obs["normalized_kurtosis"][i]),
            "ell3_over_ell2_power":float(obs["ell2_ell3_quadrupole_octupole_power_ratio"][i])
        } for i,name in enumerate(names)
      },
      "source_mask_selected_pixel_count":int(selected.sum()),
      "source_mask_files":source_masks,
      "conditional_result_by_distinct_law":outcome,
      "conditioned_source_vs_ideal_angular_shape_comparison":comparison,
      "statistical_law_scope":{
         "ideal":"fullsky Gaussian isotropic independent modes conditional on observed radial norms, NOT the actual masked fit law",
         "source":"999 actual saved FFP10 signal-only maps projected through same actual Planck mask OLS, with after-fit radial reweighting to one observed sky",
         "observed":"nine component-separated processing outputs of one physical sky, all selected before this conditional test",
         "foreground_systematics":"not qualified by source response",
         "instrument_beam_high_l":"not inverted, l>5 leakage remains",
         "multiple_statistics_selection":"retrospective after observing the actual source sky",
         "independent_observation_likelihood":"NOT_ESTABLISHED",
      },
      "phase_only_cosmological_detection":"WITHHELD",
      "all_observer_MES_physical_x_posterior":"NOT_IDENTIFIED"
    }
    output_dir.mkdir(parents=True)
    (output_dir/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    np.savez_compressed(output_dir/"phase_conditioned_source_arrays.npz",
        ideal_s3=iso_s,ideal_k4=iso_k,
        ideal_id=iso["simulation_unique_phase_ids"],
        source_ffp10_ids=src_ids,
        source_ffp10_reweighted_s3=post["normalized_skewness"],
        source_ffp10_reweighted_k4=post["normalized_kurtosis"],
        source_ffp10_original_s3=pre["normalized_skewness"],
        source_ffp10_original_k4=pre["normalized_kurtosis"],
        actual_product_names=np.asarray(names),
        actual_same_sky_s3=obs["normalized_skewness"],
        actual_same_sky_k4=obs["normalized_kurtosis"])
    fig,axes=plt.subplots(1,2,figsize=(12,4.4),layout="constrained")
    for col,(stat,actual,ideal_vals,ffp_vals,analytic) in enumerate((
        ("s3",obs_primary["s3"],iso_s,post["normalized_skewness"],0.),
        ("k4",obs_primary["k4"],iso_k,post["normalized_kurtosis"],
         theory["theoretical_conditional_mean_k4"])
    )):
        ax=axes[col]
        ax.hist(ideal_vals,bins=70,density=True,histtype="step",lw=1.5,
                label="Ideal uniform harmonic phases at observed C2,C3")
        ax.hist(ffp_vals,bins=42,density=True,histtype="step",lw=1.4,
                label="999 FFP10 mask-processed modes, amplitudes matched")
        ax.axvline(actual,color="black",ls="--",lw=1.5,
                   label="actual one-sky SMICA_FULL")
        ax.axvline(analytic,color="gray",ls=":",lw=1,
                   label="exact ideal-phase mean")
        ax.set(xlabel=stat+" amplitude-normalized angular shape",
               ylabel="descriptive normalized density, NOT p",
               title=("Third" if col==0 else "Fourth")+" sky moment")
        ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.savefig(output_dir/"planck_conditional_phase_vs_source_ffp10.png",dpi=155)
    plt.close(fig)
    (output_dir/"REPORT_KO.md").write_text(
      "# P2 L02: 동일 C2,C3 power 조건부 ideal Gaussian phase vs 실제 FFP10 source\\n\\n"
      "실제 SMICA_FULL C2,C3 계수 크기를 고정한 채 5D/7D 독립 unit-sphere phase "
      f"draw {phase_draws}개와, 원본 Planck temperature mask에 999개 FFP10 "
      "CMB-only를 투영한 뒤 각 l별 동일 power로 rescale한 source 분석을 수행. "
      f"실제 observed s3={obs_primary['s3']:.9g}, k4={obs_primary['k4']:.9g}; "
      f"analytic conditional ideal mean k4={theory['theoretical_conditional_mean_k4']:.9g}.\\n\\n"
      f"Empirical distribution CDF distance ideal vs source, "
      f"s3={comparison['conditional_empirical_CDF_distance_s3']:.6g}, "
      f"k4={comparison['conditional_empirical_CDF_distance_k4']:.6g}. "
      "모든 source는 한 실제 CMB 하늘의 파생량이며, FFP10 original beam/null "
      "response와 9개 처리 제품 사이의 확률적 교환 가능성은 미검증. "
      "이 데이터에서 s3/k4 통계를 고른 것은 retrospective이므로 어떠한 실제 "
      "cosmological anomaly p도 이 결과로 승인하지 않는다.\\n",
      encoding="utf-8")
    print("PHASE_NULL_SOURCE_DONE nphase",phase_draws,"nffp",len(post["normalized_skewness"]),
          "expected_k4",theory["theoretical_conditional_mean_k4"],
          "observed",obs_primary,"CDFs",comparison,flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--phase-draws",type=int,default=DRAW_COUNT)
    p.add_argument("--seed",type=int,default=SEED)
    z=p.parse_args()
    run(z.output_dir,phase_draws=z.phase_draws,seed=z.seed)
