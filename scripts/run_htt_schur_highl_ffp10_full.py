#!/usr/bin/env python3
"""Real Planck PR3 masked low/high-l Schur profile, 999+300 FFP10 propagation.

Actual same-source Planck SMICA K1 observed map plus source-gated FFP10
999 signal, 300 noise; paired first300 are signal+noise sharing each
ID (not third independent source). Fit low ell0..5 then nuisance ell6..12
simultaneously and report the EXACT low-ell difference; propagate to
legacy Teff l2+l3 shape s3/k4 and source conditional SAG eps2/eps3.

One observed CMB sky, source-conditioned diagnostics only. No physically
validated beam, foreground, ell>12 truncation bound or Planck null p.
"""
from __future__ import annotations

import argparse,hashlib,json,resource,time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.masked_schur_highl_temperature import (
    make_geometry,nested_lmax_source_coefficients,nominal_beam_window
)
from obsstat.r7_cmb_product_response import pixel_fit_geometry,real_design
from obsstat.mes_eps_measurement_bridge import eps_arrays
from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition
from run_htt_planck_mes_eps_20261015 import _independent_source_mask,CACHE

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
PREVIOUS=PUB/"results/L01_actual_planck_v1/result.json"
PHASE_SOURCE=PUB/"legacy_modern_obs_integration_20261015/results/observed_planck_shape_v1/result.json"
CACHE_SHA="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
ELLS=(5,8,10,12)


def digest(file):
    h=hashlib.sha256()
    with Path(file).open('rb') as src:
        for part in iter(lambda:src.read(8<<20),b''):h.update(part)
    return h.hexdigest()


def quantiles(x):
    return [float(v) for v in np.quantile(x,[.05,.16,.5,.84,.95])]


def to_stats(x):
    z=np.asarray(x,float)
    return {"n":int(len(z)),
            "mean":float(np.mean(z)),
            "median":float(np.median(z)),
            "rms":float(np.sqrt(np.mean(z*z))),
            "q05_16_50_84_95":quantiles(z)}


def morph(low):
    """Return signed higher moments and low-ell covariant epsilon."""
    a=np.asarray(low,float)
    assert a.ndim==2 and a.shape[1]==36
    q=quartic_power_shape_decomposition(a[:,4:16])
    eps=eps_arrays(a)
    return {
       "s3":np.asarray(q["normalized_skewness"]),
       "k4":np.asarray(q["normalized_kurtosis"]),
       "delta_F4_l23":np.asarray(q["deltaF4"]),
       "eps2":np.asarray(eps[:,0]),
       "eps3":np.asarray(eps[:,1]),
       "C2_microK2":np.sum(a[:,4:9]**2,axis=1)/5.,
       "C3_microK2":np.sum(a[:,9:16]**2,axis=1)/7.,
    }


def fit_bank(source,geometry):
    x=nested_lmax_source_coefficients(source,geometry,chunk=32)
    return {k:v for k,v in x["lowl_by_lmax"].items()}, x["Schur_identity_relative_max"]


def describe_source_bank(fits):
    m={k:morph(fits[k]) for k in fits}
    # Always paired within each source ID across lmax.
    baseline=m["5"]
    summary={}
    for name in m:
        group=m[name]
        small=[]
        for key in ("eps2","eps3","C2_microK2","C3_microK2","s3","k4","delta_F4_l23"):
            diff=group[key]-baseline[key]
            small.append((key,to_stats(group[key]),to_stats(diff)))
        dist=np.linalg.norm(fits[name][:,4:16]-fits["5"][:,4:16],axis=1)
        summary[name]={
            "features":{key:{"absolute":now,"paired_minus_lmax5":delta}
                        for key,now,delta in small},
            "low_ell2to3_real12_change_norm_microK":to_stats(dist)
        }
    return summary,m


def run(output:Path,*,n_cmb=999,n_noise=300):
    if output.exists():raise FileExistsError("create-only high-l result directory")
    if (not isinstance(n_cmb,int) or not isinstance(n_noise,int)
        or not 1<=n_cmb<=999 or not 1<=n_noise<=300):
        raise ValueError("source register has 999 CMB and 300 noise maximum")
    start=time.perf_counter()
    if digest(CACHE)!=CACHE_SHA:
        raise RuntimeError("K1 original FFP10 source cache SHA changed")
    previous=json.loads(PREVIOUS.read_text())
    phase=json.loads(PHASE_SOURCE.read_text())
    if previous["simulated_cmb_maps_from_K1"]!=48:
        raise RuntimeError("baseline original source scope error")
    if int(phase["one_real_cmb_sky_processing_products"])!=9:
        raise RuntimeError("one actual CMB sky processed nine ways was changed")
    sky,base=pixel_fit_geometry(nside=64)
    extended=real_design(sky,ell_max=12)
    if np.max(abs(extended[:,:36]-base))>1e-14:
        raise RuntimeError("modern full source real harmonic chart differs")
    with np.load(CACHE,allow_pickle=False) as source:
        m,mask_ids,meta=_independent_source_mask(
            np.asarray(source["common_mask"],float))
        if m.sum()!=26846:
            raise RuntimeError("exact native Planck TMASK selected 26846 changed")
        geo=make_geometry(extended,m)
        transfer=nominal_beam_window(geo)
        obs=np.asarray(source["observed_map"],float)
        if obs.shape!=(49152,):raise RuntimeError("source actual observed HEALPix map shape")
        observed,obs_error=fit_bank(obs,geo)
        ids=np.asarray(source["cmb_ids"][:n_cmb],int)
        noise_ids=np.asarray(source["noise_ids"][:n_noise],int)
        if len(set(ids))!=n_cmb or len(set(noise_ids))!=n_noise:
            raise RuntimeError("duplicate source simulation realization IDs")
        sig,sig_error=fit_bank(source["cmb_maps"][:n_cmb],geo)
        noise,noise_error=fit_bank(source["noise_maps"][:n_noise],geo)
    ref=previous["fit_results"]
    observed_eps= {key:eps_arrays(observed[key])[0] for key in map(str,ELLS)}
    for key,e in observed_eps.items():
        target=np.asarray(ref[key]["actual_observed_source_eps_l2_l3"])
        if np.max(abs(e-target))>3e-12:
            raise RuntimeError(f"previous physical source observable changed lmax={key}")
    if n_cmb>=48:
        old48=np.asarray(ref["12"]["simulation_48_rms_delta_to_lmax5_eps_l2_l3"])
        t1=eps_arrays(sig["12"][:48])
        t0=eps_arrays(sig["5"][:48])
        actual=np.sqrt(np.mean((t1-t0)**2,axis=0))
        if np.max(abs(actual-old48))>3e-12:
            raise RuntimeError("48-source previous experimental cohort not reproduced")
    n_pair=min(n_noise,n_cmb)
    if not np.array_equal(ids[:n_pair],noise_ids[:n_pair]):
        raise RuntimeError("paired CMB and noise must have SAME registered FFP10 source ID")
    pair={key:sig[key][:n_pair]+noise[key][:n_pair] for key in sig}
    obs_summary,obs_values=describe_source_bank(observed)
    signal_summary,sim_values=describe_source_bank(sig)
    noise_summary,noise_values=describe_source_bank(noise)
    pair_summary,pair_values=describe_source_bank(pair)
    # Paired absolute change ranks are exploratory source statistics, NEVER
    # physical Planck anomaly PTEs or independent posterior probabilities.
    descriptive={}
    for stat in ("s3","k4"):
        obs_change=float(obs_values["12"][stat][0]-obs_values["5"][stat][0])
        channel={}
        for key,name in ((sim_values,"signal_999"),(noise_values,"noise_300"),
                         (pair_values,"paired_signal_plus_noise_300")):
            delta=np.asarray(key["12"][stat])-np.asarray(key["5"][stat])
            channel[name]={
               "n":len(delta),
               "source_cohort_count_ge_observed_abs":int(np.count_nonzero(abs(delta)>=abs(obs_change))),
               "descriptive_fraction_abs_ge":float(np.mean(abs(delta)>=abs(obs_change))),
               "source_null_p":"NOT_ADMITTED_POSTHOC_SOURCE_QUALIFICATION_ABSENT",
            }
        descriptive[stat]={"actual_single_sky_l5_to12_delta":obs_change,
                           "cohort_descriptive_conditioned_abs_rank":channel}
    # identity linearity before nonlinear Teff transforms
    for lmax in map(str,ELLS):
        np.testing.assert_allclose(pair[lmax],sig[lmax][:n_pair]+noise[lmax][:n_pair],
                                   rtol=0,atol=0)
    cf4=PUB/"results/H02_flrw_method_decomposition_v2/result.json"
    j=json.loads(cf4.read_text())
    if j["source_groups"]!=35970 or j["physical_beyond_FLRW_claim"]!="WITHHELD":
        raise RuntimeError("independent actual CF4 FLRW benchmark source changed")
    result={
       "schema":"htt.Planck_high_l_Schur_all_FFP10_T_source_method/1",
       "date_KST":"2026-10-15",
       "claim":"ACTUAL_SMICA_SOURCE_AND_FFP10_FULL_CONDITIONAL_METHOD_SENSITIVITY_NOT_PHYSICAL_ANOMALY_NULL",
       "original_source_input_CMB_hash":CACHE_SHA,
       "prior_48_realization_l5to12_result_sha256":digest(PREVIOUS),
       "legacy_exact_Teff_shape_prior_result_sha256":digest(PHASE_SOURCE),
       "actual_CMB_physical_sky_count":1,
       "actual_OBSERVED_processed_map_in_this_run":"SMICA_K1_registered_one_map",
       "FFP_CMB_unique_source_realizations":n_cmb,
       "FFP_noise_unique_source_realizations":n_noise,
       "FFP_CMB_noise_source_unique_id_paired":n_pair,
       "FFP_CMB_source_ids":ids.tolist(),
       "FFP_noise_source_ids":noise_ids.tolist(),
       "native_temperature_mask":mask_ids,
       "source_mask_selected_pixel_count":int(m.sum()),
       "source_geometry":geo.diagnostics,
       "nominal_isotropic_beam_pixel_scenario":transfer,
       "real_harmonic_ellmax_fitted":list(ELLS),
       "Schur_normal_equation_identity":"aL_restricted-aL_joint=GLL^-1_GLH aH_joint on ONE same selected pixel vector",
       "Schur_identity_relative_residual_by_bank":{
          "one_real_source":obs_error,
          "CMB_999":sig_error,
          "noise_300":noise_error},
       "source_simulation_pairing_status":"EXACT_IDENTICAL_FFP10_IDS_FIRST_N_WITHOUT_RECYCLING",
       "retrospective_observed_lmax5_to12_delta_abs_ranks_NOT_P":descriptive,
       "source_summaries":{
          "observed_single_sky":obs_summary,
          "FFP_CMB_signal_only":signal_summary,
          "FFP_noise_only":noise_summary,
          "FFP_same_id_CMB_plus_noise":pair_summary},
       "independent_CF4_actual_source_context":{
          "source":"real CF4 35,970 groups, separate scalar FLRW baseline and method offsets",
          "source_result_sha256":digest(cf4),
          "source_far_near_logH_observed":j["far_near_two_term_decomposition"]["raw_log_cz_over_dL"],
          "no_joint_likelihood_with_planck":True,
          "no_physical_shear_from_CF4_window":True},
       "legacy_MES_kinematical_x_F_Pi_Q_Gf":"NOT_IDENTIFIED_FROM_CMB_MODEL_F4_OR_MASK_RESPONSE",
       "actual_release_effective_beam":"UNQUALIFIED_NOMINAL_SCENARIO_ONLY",
       "ell_gt12_remainder":"UNKNOWN",
       "Planck_systematics_foreground_covariance":"NOT_QUALIFIED",
       "Planck_p_value":"NOT_ADMITTED",
       "P2_L01_scientific_state":"PENDING_BEAM_SPIN2_AND_MATCHED_END_TO_END_SOURCE",
       "P4_V02_scientific_state":"WAITING_ON_L01",
       "runtime_elapsed_seconds":time.perf_counter()-start,
       "runtime_peak_RSS_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output.mkdir(parents=True)
    (output/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    np.savez_compressed(output/"source_lowell_nested_999plus300.npz",
         observed_l5=observed["5"],observed_l12=observed["12"],
         cmb_ids=ids,noise_ids=noise_ids,
         cmb_l5_36=sig["5"],cmb_l12_36=sig["12"],
         noise_l5_36=noise["5"],noise_l12_36=noise["12"],
         paired_l5_36=pair["5"],paired_l12_36=pair["12"])
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout="constrained")
    actual=np.arange(len(ELLS))
    for key,col in (("s3",0),("k4",1)):
        y=np.asarray([obs_values[str(lmax)][key][0] for lmax in ELLS])
        axes[col].plot(actual,y,"o-",label="one actual SMICA K1 source")
        med=np.asarray([np.median(sim_values[str(lmax)][key]) for lmax in ELLS])
        low=np.asarray([np.quantile(sim_values[str(lmax)][key],.16) for lmax in ELLS])
        hi=np.asarray([np.quantile(sim_values[str(lmax)][key],.84) for lmax in ELLS])
        axes[col].plot(actual,med,"s-",label=f"{n_cmb} CMB FFP10 median, conditional")
        axes[col].fill_between(actual,low,hi,alpha=.2,label="CMB .16 to .84 quantile")
        axes[col].set_xticks(actual,[str(z) for z in ELLS])
        axes[col].set(xlabel="Simultaneous masked fit ellmax",
                      ylabel=key+" finite exact legacy Teff morphology",
                      title="High-ell nuisance profile source stability (NOT null p)")
        axes[col].grid(alpha=.2);axes[col].legend(fontsize=7)
    fig.savefig(output/"planck_schur_lmax_shape_source.png",dpi=150)
    plt.close(fig)
    (output/"REPORT_KO.md").write_text(
      "# P2 L01 실제 Planck+FFP10 Schur high-l masked source 분해\n\n"
      f"실제 K1 registered SMICA 온도 지도 한 개, 동일 NSIDE64 RING mask {int(m.sum())}개, "
      f"FFP10 CMB {n_cmb}개, noise {n_noise}개, 동일 ID로 paired CMB+noise {n_pair}개를 "
      "동시 l0..5 / l0..8 / l0..10 / l0..12 real harmonic으로 적합.\n\n"
      "각 source에 대해 restricted minus joint l2/3은 full joint l6..12 "
      "coeff와 mask block K=GLL^-1GLH의 정확한 곱이다. 별도 profile Schur "
      "S=GLL-GLHGHH^-1GHL 구현으로 crosscheck.\n\n"
      f"Mask source high6..12 to low ell2/3 spectral norm="
      f"{geo.diagnostics['low_ell2to3_high_nuisance_norm']:.9g}; "
      f"profile information minimum relative to original low Gram="
      f"{geo.diagnostics['profile_information_min']:.9g}. "
      "Legacy F4 l2/l3 shape (s3,k4) 변화는 실제 observer source와 같은 ID "
      "FFP signal/noise에 따라 다르며, 곧바로 관측 우주론 anomaly라고 부르지 않는다.\n\n"
      "Planck original 2018 IV는 source component filtering과 smoothing을 포함하며 "
      "여기서는 5 arcmin Gaussian×NSIDE64 pixel-window를 ONLY NOMINAL SCENARIO로 "
      "분리했다. 실제 released effective SMICA transfer/foreground/high ell>12는 "
      "미확인이다. CF4 FLRW source와 Planck 자료는 별개 관측으로 보존하고 "
      "physical shear/tilt/x/Q/Pi posterior로 묶지 않는다.\n",encoding="utf-8")
    obs_shape=obs_summary["12"]["features"]
    print("L01_L5to12_999CMB_300NOISE source completed",
          "Schur_low_profile",geo.diagnostics["profile_information_min"],
          "masked_high_norm",geo.diagnostics["low_ell2to3_high_nuisance_norm"],
          "observed_s3",obs_shape["s3"]["absolute"]["median"],
          "observed_s3_change",obs_shape["s3"]["paired_minus_lmax5"]["median"],
          "observed_k4_change",obs_shape["k4"]["paired_minus_lmax5"]["median"],
          "runtime",result["runtime_elapsed_seconds"],flush=True)
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--cmb-count",type=int,default=999)
    ap.add_argument("--noise-count",type=int,default=300)
    args=ap.parse_args()
    run(args.output_dir,n_cmb=args.cmb_count,n_noise=args.noise_count)
