#!/usr/bin/env python3
"""Actual Planck/FFP10 single-sky masked low-ell truncation sensitivity.

Includes l=6..12 in the same finite OLS map fit; intentionally NOT an actual
beam/pixel/foreground deconvolution nor a physical Planck p-value.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.r7_cmb_product_response import pixel_fit_geometry,real_design
from obsstat.publication_lowell_response import (
    source_fit_matrix,leakage_matrix,source_map_fit,band_rms,
)
from obsstat.mes_eps_measurement_bridge import eps_arrays,T0_MICROK
from run_htt_planck_mes_eps_20261015 import (
    _independent_source_mask,CACHE,GATE,
)

ROOT=Path(__file__).resolve().parents[1]
LOOP9=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/results_v2/result.json"
DECLARED_CACHE_SHA="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for b in iter(lambda:fh.read(8<<20),b""):h.update(b)
    return h.hexdigest()


def run(out,*,sim_count=48):
    if out.exists():raise FileExistsError("create-only L01 source results directory")
    start=time.perf_counter()
    previous=json.loads(LOOP9.read_text())
    gate=json.loads(GATE.read_text())
    if (digest(CACHE)!=DECLARED_CACHE_SHA or
        gate["cache_hash"].removeprefix("sha256:")!=DECLARED_CACHE_SHA):
        raise RuntimeError("FFP10 source cache hash gate changed")
    if previous["nside64_selected_T_same_mask_n"]!=26846:
        raise RuntimeError("prior Planck native T mask identity unmatched")
    if not 1<=sim_count<=100:
        raise RuntimeError("predeclared source-conditioned sanity cohort 1..100")
    with np.load(CACHE,allow_pickle=False) as inp:
        common=np.asarray(inp["common_mask"],float)
        observed=np.asarray(inp["observed_map"],float)
        sim=np.array(inp["cmb_maps"][:sim_count],copy=True)
        ids=np.array(inp["cmb_ids"][:sim_count],copy=True)
    if observed.shape!=(49152,) or sim.shape!=(sim_count,49152) or len(np.unique(ids))!=sim_count:
        raise RuntimeError("Planck source map shape or independent simulation ID mismatch")
    mask,maskfiles,maskinfo=_independent_source_mask(common)
    directions,low=pixel_fit_geometry(nside=64)
    design=real_design(directions,ell_max=12)
    if low.shape!=(49152,36) or design.shape!=(49152,169):
        raise RuntimeError("fixed orthonormal real harmonic design geometry wrong")
    if np.max(abs(design[:,:36]-low))>8e-15:
        raise RuntimeError("expanded harmonic chart changed l<=5 original estimator")
    Rmask,meta=source_fit_matrix(low,mask)
    Rfull,fmeta=source_fit_matrix(low,np.ones(len(mask),bool))
    obs_base=Rmask@observed[mask]
    eps_base=eps_arrays(obs_base[None,:])[0]
    ref=np.array(previous["FFP10_conditional_processing"]["real_map_compared_to_cache_observed_response_only"]["cache_obs_eps_l2_l3"])
    if np.max(abs(ref-eps_base))>2e-12:
        raise RuntimeError("actual observed cache baseline eps2,eps3 not previous release")
    modes={}
    simbase=None
    for lmax in (5,8,10,12):
        p=(lmax+1)**2
        coeff,info=source_map_fit(np.vstack((observed[None,:],sim)),design[:,:p],mask)
        obs=coeff[0]
        sims=coeff[1:]
        # The frozen MES tensor adapter consumes ONLY the first 36 l<=5 columns.
        # Higher fitted columns are nuisance modes, not a new epsilon definition.
        eps_obs=eps_arrays(obs[None,:36])[0]
        eps_sim=eps_arrays(sims[:,:36])
        if lmax==5:
            simbase=eps_sim.copy()
        high=design[:,36:p]
        Lmask,mask_summary=leakage_matrix(low,high,mask)
        Lfull,full_summary=leakage_matrix(low,high,np.ones(len(mask),bool))
        modes[str(lmax)]={
            "lmax":lmax,
            "source_pixel_count":info["sampled_pixels"],
            "design_columns":p,
            "design_condition":info["design_condition"],
            "masked_lowband_highmode_leakage":mask_summary,
            "fullsky_pixel_lowband_highmode_leakage":full_summary,
            "actual_observed_source_eps_l2_l3":eps_obs.tolist(),
            "actual_observed_ell2_C_microK2":float(band_rms(obs,ell=2)**2),
            "actual_observed_ell3_C_microK2":float(band_rms(obs,ell=3)**2),
            "actual_source_selected_pixel_residual_rms_microK":info["residual_rms_microK"][0],
            "simulation_48_selected_ell2_eps_median":float(np.median(eps_sim[:,0])),
            "simulation_48_selected_ell3_eps_median":float(np.median(eps_sim[:,1])),
            "simulation_48_mean_delta_to_lmax5_eps_l2_l3":np.mean(eps_sim-simbase,axis=0).tolist(),
            "simulation_48_rms_delta_to_lmax5_eps_l2_l3":np.sqrt(np.mean((eps_sim-simbase)**2,axis=0)).tolist(),
            "actual_delta_to_lmax5_eps_l2_l3":(eps_obs-eps_base).tolist(),
        }
        print("L",lmax,"observed_eps",np.round(eps_obs*1e6,6).tolist(),
              "mask_alias_norm",round(mask_summary["spectral_norm"],6),
              "fit_cond",round(info["design_condition"],4),flush=True)
    norms=[modes[str(l)]["masked_lowband_highmode_leakage"]["spectral_norm"] for l in (5,8,10,12)]
    if np.min(np.diff(norms))< -2e-11:
        raise RuntimeError("nested high-mode operator spectral norm decreased")
    result={
       "schema":"htt.Planck_source_lmax5to12_masked_response/1",
       "claim":"ACTUAL_GATED_PLANCK_SOURCE_CONDITIONAL_FINITE_IMAGE_ONLY",
       "cache_sha256":DECLARED_CACHE_SHA,
       "loop9_result_sha256":digest(LOOP9),
       "native_masks":maskfiles,
       "mask_source":maskinfo,
       "unit":"thermodynamic microK maps, epsilon=SAG PSFT norm dimensionless",
       "shared_cmb_sky":"ONE_SKY_MULTIPLE_REPROCESSED_ESTIMATORS",
       "simulated_cmb_maps_from_K1":sim_count,
       "simulation_ids":ids.astype(int).tolist(),
       "source_simulation_claim":"FIRST48_SAVED_REALIZATIONS_DESCRIPTIVE_FIXED_WEIGHT_FFP10_NOT_CALIBRATED_NULL",
       "fit_windows":{"nside":64,"ordering":"RING","low_fit":"l0..5 simultaneous",
                      "further_fit":[8,10,12],"retained_for_eps":[2,3]},
       "fit_results":modes,
       "physical_transfer_limits":{
           "beam":"NOT_SOURCE_DECONVOLVED",
           "foreground":"FIXED_RELEASE_WEIGHT_NOT_QUALIFIED_NULL",
           "polarized_spin2":"NOT_INCLUDED_TEMPERATURE_ONLY",
           "ell_gt_12":"UNKNOWN",
           "observed_likelihood":"NOT_CALIBRATED",
       },
       "elapsed_seconds":time.perf_counter()-start,
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout="constrained")
    ellmax=np.array([5,8,10,12])
    eps=np.array([modes[str(k)]["actual_observed_source_eps_l2_l3"] for k in ellmax])
    for k in range(2):
        axes[0].plot(ellmax,eps[:,k]*1e6,marker="o",label=f"SAG eps{2+k} x10^6")
    axes[0].set(xlabel="Simultaneous fitted lmax",ylabel="observed-source tensor norm [1e-6]",
                title="Single gated SMICA observed map: finite harmonic fit")
    axes[0].grid(alpha=.2);axes[0].legend()
    axes[1].plot(ellmax,[modes[str(k)]["masked_lowband_highmode_leakage"]["spectral_norm"]
                         for k in ellmax],marker="o",label="masked source")
    axes[1].plot(ellmax,[modes[str(k)]["fullsky_pixel_lowband_highmode_leakage"]["spectral_norm"]
                         for k in ellmax],marker="s",label="full HEALPix quadrature")
    axes[1].set(xlabel="Highest injected l of finite high-mode basis",
                ylabel="||l>5 -> fitted l2/3|| operator",title="Declared high-mode leakage (not true-sky bound)")
    axes[1].grid(alpha=.2);axes[1].legend()
    fig.savefig(out/"planck_lmax_mask_leakage.png",dpi=150)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
        "# Planck 실제 SMICA source의 lmax 민감도\n\n"
        "Source K1 gated observed map과 조건부 FFP10 처음 48개 각각을 NSIDE64 "
        "동일 26,846 온도 픽셀의 l0..5/8/10/12 finite real harmonics로 적합했다. "
        "모든 모델은 하나의 실제 하늘을 재분석한 결과이며 독립 새 관측이 아니다.\n\n"
        f"실제 observed source eps2/3 순서(lmax 5,8,10,12): {eps.tolist()}. "
        f"동일 mask highmode l6..lmax spectral norms: {norms}.\n\n"
        "이 결과는 고차원 모형에 따른 저다중극 투영 이동이지 beam/foreground "
        "deconvolution, polarized T/E/B, 또는 물리 Planck anomaly p가 아니다. "
        "ell>12 highmode 영향은 계산하지 않았다. P2 L01 물리 beam/spin2 gate는 별도 미완.\n",encoding="utf-8")
    print("L01_SOURCE_RUN_COMPLETED nside64",mask.sum(),
          "source_eps_lmax12",np.round(eps[-1],10).tolist(),
          "elapsed",round(time.perf_counter()-start,3))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--sim-count",type=int,default=48)
    a=p.parse_args()
    run(a.output_dir,sim_count=a.sim_count)
