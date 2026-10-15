#!/usr/bin/env python3
"""Actual Planck PR3 nine same-sky low-ell + FFP10 conditional MES-normalization study.

Sources are read only. Outputs are create-only. Do not infer a cosmological
almost-EGS bound, independent Planck likelihood, noise covariance or physical PTE.
"""
from __future__ import annotations
import argparse, hashlib, json, time, resource
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.io import fits

from obsstat.mes_eps_measurement_bridge import (
    eps_from_retained, geodesic_algebraic_sector_ceiling, eps_arrays,
    fixed_ols_operator, fit_rows_of_simulated_maps, gaussian_beam_l,
    pstf_norm_factor, T0_MICROK, nested_children_coverage_to_ring,
)
from obsstat.r7_cmb_product_response import pixel_fit_geometry, real_design

SOURCE_ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
RAW = Path("/mnt/extdrive/workdir/raw")
ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "docs/research_program/htt_mes_eps_loop9_20261015"
CACHE = SOURCE_ROOT / "workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz"
GATE = SOURCE_ROOT / "docs/generated/k1_e2e_cache_gate_ffp10_smica.json"
MASKS = [
 RAW / "planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
 RAW / "planck_pr3_smica_hm_20261015/COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits",
 RAW / "planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-OE-Misspix-Mask-Int_2048_R3.00.fits",
]
SOURCE_HASHES = {
 "coeff": "900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459",
 "loop5": "abbc49075634899499f1ba615c5f2ba0192e4f949d3d6cc8bfe2171bf862312a",
 "loop7": "124f9e5dabbf513461365d2cd8afc2d97f2b52b0a8697bc0cee2a941f937c542",
 "mes_sag": "00bb2c7c485ffb14433a90dae2d5d7709fbecd9c4eef986ec27d72f7dae5370e",
 "mes_mesa": "d500ffeef60f1f006393b7b2a21823b51bc4c9c9b41b7fb983f0393ce800217e",
}
SOURCE_MES = SOURCE_ROOT / "docs/audits/mes_primary_sources"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as s:
        for block in iter(lambda: s.read(8<<20), b""):
            h.update(block)
    return h.hexdigest()


def _independent_source_mask(k1_mask):
    """Exactly duplicate Loop5: native nested fine masks and 0.995 coarse cover."""
    m = None
    records = []
    for path in MASKS:
        if not path.is_file() or path.stat().st_size != 201335040:
            raise RuntimeError("missing actual pinned native Planck mask")
        sha = digest(path)
        with fits.open(path, memmap=True) as hdus:
            t=hdus[1]
            if (t.header.get("NSIDE") != 2048 or
                t.header.get("ORDERING") != "NESTED" or
                "TMASK" not in t.columns.names):
                raise RuntimeError("Planck native mask header not matched")
            fine=np.asarray(t.data["TMASK"])>.5
            if fine.shape != (50331648,):
                raise RuntimeError("wrong original NSIDE2048 Planck mask size")
            if m is None:
                m=fine.copy()
            else:
                m &= fine
        records.append({"file":str(path),"sha256":sha})
    # Nested nside2048 -> 64, 1024 consecutive children per coarse cell.
    # NESTED parents are not in the RING ordering of K1 and pixel_fit_geometry.
    # This mapping is essential to reproduce the same 26,846 pixels as Loop5.
    coarse=nested_children_coverage_to_ring(m,nside_in=2048,nside_out=64)
    selected=np.asarray(k1_mask>.5,dtype=bool) & (coarse>=.995)
    if int(selected.sum())!=26846:
        raise RuntimeError(f"Loop5 temperature support contract drift: {selected.sum()}!=26846")
    return selected,records,{"coverage_floor":.995,
                              "coarse_nside64_selected":int(selected.sum()),
                              "fine_nested_children_per_coarse_pixel":1024}


def qdesc(data):
    return np.quantile(data,[.05,.16,.50,.84,.95],axis=0).tolist()


def run(out:Path, *, n_cmb=999, n_noise=300):
    if out.exists():
        raise FileExistsError("create-only experimental result directory")
    t=time.perf_counter()
    input_dir=STUDY/"inputs"
    for label,fn in (("coeff","retained_common_support_coefficients.npz"),
                     ("loop5","planck_loop5_result.json"),
                     ("loop7","loop7_mes_scenarios.json")):
        if digest(input_dir/fn)!=SOURCE_HASHES[label]:
            raise RuntimeError(f"archived source {label} SHA-256 changed")
    for label,fn in (("mes_sag","sag1997_astro-ph_9904346_ApJ476_435.tex"),
                     ("mes_mesa","mesa_astro-ph_9501016_PRD51_1525.txt")):
        if digest(SOURCE_MES/fn)!=SOURCE_HASHES[label]:
            raise RuntimeError(f"MES primary source {label} identity drift")
    parent=json.loads((input_dir/"planck_loop5_result.json").read_text())
    previous=json.loads((input_dir/"loop7_mes_scenarios.json").read_text())
    if parent["common_T_nside64_pixel_count"]!=26846:
        raise RuntimeError("Loop5 common support drift")
    if parent["units"].startswith("microK") is False:
        raise RuntimeError("Planck source microkelvin identity drift")
    with np.load(input_dir/"retained_common_support_coefficients.npz",allow_pickle=False) as data:
        names=[str(z) for z in data["names_T"]]
        coeff=np.asarray(data["coeff_T"],float)
    if coeff.shape!=(9,32) or len(set(names))!=9:
        raise RuntimeError("exactly nine single-sky mutually related products required")
    map_rows={}
    eps_pairs=[]
    for name,v in zip(names,coeff):
        s=eps_from_retained(v)
        old=previous["active_PR124_geodesic_algebraic_e1_zero_scenarios"][name]
        if max(
             abs(s[str(j)]["sqrtCl_over_T0"]-old[f"eps{j}_sqrtCl_over_T0_proxy"])
             for j in (2,3)
        )>1e-14:
            raise RuntimeError("Loop7 raw harmonic sqrt-Cl baseline failed exact correspondence")
        b=geodesic_algebraic_sector_ceiling(
            s["2"]["SAG_eq17_covariant_rms_tensor_norm"],
            s["3"]["SAG_eq17_covariant_rms_tensor_norm"])
        eps_pairs.append([s[str(j)]["SAG_eq17_covariant_rms_tensor_norm"] for j in (2,3)])
        map_rows[name]={"ell2":s["2"],"ell3":s["3"],
                        "algebraic_eps1_zero":b,
                        "previous_shear_sector_anchor":old["registered_geodesic_sigma_sector_anchor"],
                        "new_over_old_anchor":b["Sigma2_anchor_only_if_conditions_met"] /
                                               old["registered_geodesic_sigma_sector_anchor"],
                        "same_realization_unit":"ONE_PHYSICAL_SKY_MULTIPLE_PROCESSED_PRODUCTS"}
    if list(parent["source_file_identities"])!=names:
        raise RuntimeError("nine map metadata ordering/identity drift")
    print("NINE_REAL_SKY_MAPS",len(map_rows),
          "SMICA_FULL_ELL2_ELL3",np.array(eps_pairs)[names.index("SMICA_FULL")],flush=True)

    if not GATE.is_file() or not CACHE.is_file():
        raise RuntimeError("registered FFP10 gate/cache raw products missing")
    gate=json.loads(GATE.read_text())
    expected=gate["cache_hash"].removeprefix("sha256:")
    if expected != parent["input_cache_sha256"].removeprefix("sha256:"):
        raise RuntimeError("FFP10 gate and source parent disagree")
    observed=digest(CACHE)
    if observed!=expected:
        raise RuntimeError("FFP10 original actual simulation cache does not match gate")
    if gate.get("n_checked",0)<1 or gate.get("safe_to_delete_raw",False) is True and not gate.get("cache_reproducibility_green",False):
        raise RuntimeError("FFP10 source-gate fail")

    n, X=pixel_fit_geometry(nside=64)
    fullmask=np.ones(len(n),bool)
    with np.load(CACHE,allow_pickle=False) as data:
        k1mask=np.asarray(data["common_mask"],float)
        selected,mask_ids,mask_info=_independent_source_mask(k1mask)
        op_mask,op_meta=fixed_ols_operator(X,selected)
        op_full,full_meta=fixed_ols_operator(X,fullmask)
        obs=np.asarray(data["observed_map"],float)
        obs_k1=(op_mask @ obs[selected])[4:16]
        if data["cmb_maps"].shape != (999,49152) or data["noise_maps"].shape!=(300,49152):
            raise RuntimeError("delivered FFP10 map count/shape mismatch")
        if not np.array_equal(np.unique(data["cmb_ids"]),np.sort(data["cmb_ids"])) or len(np.unique(data["cmb_ids"]))!=999:
            raise RuntimeError("CMB simulation IDs duplicated/unsorted")
        if len(np.unique(data["noise_ids"]))!=300:
            raise RuntimeError("noise simulation IDs duplicated")
        if n_cmb!=999 or n_noise!=300:
            raise RuntimeError("run requires exact registered full simulation cohorts")
        cmaps=data["cmb_maps"]
        c_mask=fit_rows_of_simulated_maps(cmaps,selected,op_mask,chunk=16)
        c_full=fit_rows_of_simulated_maps(cmaps,fullmask,op_full,chunk=16)
        del cmaps
        noise_maps=data["noise_maps"]
        n_mask=fit_rows_of_simulated_maps(noise_maps,selected,op_mask,chunk=16)
        del noise_maps
        ids={"cmb_first":int(data["cmb_ids"][0]),"cmb_last":int(data["cmb_ids"][-1]),
             "noise_first":int(data["noise_ids"][0]),"noise_last":int(data["noise_ids"][-1]),
             "cmb_count":n_cmb,"noise_count":n_noise}
    # The same simulator map is projected with exactly same linear estimator
    # under two different masks. This isolates a *processing response*, not
    # an independent astrophysical null or a physical Bianchi amplitude.
    eps_mask=eps_arrays(c_mask)
    eps_full=eps_arrays(c_full)
    eps_pair=eps_arrays(c_mask[:n_noise]+n_mask[:n_noise])
    noise_delta=eps_pair-eps_mask[:n_noise]
    mask_delta=eps_mask-eps_full
    sim_analysis={
      "ffp_999_cmb_signal_eps_mask_quantiles_05_16_50_84_95":qdesc(eps_mask),
      "ffp_999_cmb_signal_eps_full_pixel_quantiles_05_16_50_84_95":qdesc(eps_full),
      "ffp_999_matched_mask_minus_full_eps_rms":np.sqrt(np.mean(mask_delta**2,axis=0)).tolist(),
      "ffp_999_matched_mask_minus_full_eps_median":np.median(mask_delta,axis=0).tolist(),
      "ffp_999_matched_mask_minus_full_eps_quantiles_05_16_50_84_95":qdesc(mask_delta),
      "ffp_300_paired_noise_eps_quantiles_05_16_50_84_95":qdesc(eps_pair),
      "ffp_300_paired_noise_minus_signal_eps_rms":np.sqrt(np.mean(noise_delta**2,axis=0)).tolist(),
      "ffp_300_paired_noise_minus_signal_eps_median":np.median(noise_delta,axis=0).tolist(),
      "ffp_simulation_id_summary":ids,
      "source_model":"gated K1 FFP10 SMICA fixed-weight CMB signal and independent noise cache; not physical Planck low-l null",
      "real_map_compared_to_cache_observed_response_only": {
        "cache_obs_eps_l2_l3":eps_arrays(obs_k1[None,:])[0].tolist(),
        "loop5_SMICA_FULL_eps_l2_l3":[map_rows["SMICA_FULL"][f"ell{ell}"]["SAG_eq17_covariant_rms_tensor_norm"] for ell in (2,3)],
        "cache_difference_compared_only_after_separately_fitted_same_mask": (
             eps_arrays(obs_k1[None,:])[0]-np.array(eps_pairs)[names.index("SMICA_FULL")]
         ).tolist(),
        "no_joint_exchangeability_claim":True
      }
    }
    # Deterministic high-mode leakage operator on exact new same mask and
    # a full-sky HEALPix quadrature control; this is operator geometry, no sky fit.
    X8=real_design(n,ell_max=8)
    high=X8[:,36:]
    Lmasked=op_mask @ high[selected]
    Lfull=op_full @ high
    band_sl=slice(4,16)
    leakmask=Lmasked[band_sl,:]
    leakfull=Lfull[band_sl,:]
    leak_s=np.linalg.svd(leakmask,compute_uv=False)
    sim_analysis["mask_l6_to8_leakage"]={
      "rows_ell2_3":12,"high_mode_columns_ell6_8":45,
      "mask_operator_spectral_norm":float(leak_s[0]),
      "mask_operator_frobenius_norm":float(np.linalg.norm(leakmask)),
      "fullsky_pixel_quadrature_operator_spectral_norm":float(
            np.linalg.svd(leakfull,compute_uv=False)[0]),
      "fullsky_pixel_quadrature_operator_frobenius_norm":float(np.linalg.norm(leakfull)),
      "conditioned_lowell_design":op_meta,
      "fullsky_design":full_meta,
      "unmodelled_ell_gt_8": "UNKNOWN",
      "interpretation":"finite polynomial subspace leakage due to mask, not certified upper bound on unmodelled true high-l sky",
    }
    contrasts={}
    arr=np.array(eps_pairs)
    for a,b in (("SMICA_HM1","SMICA_HM2"),("SMICA_OE1","SMICA_OE2"),
                ("NILC_HM1","NILC_HM2"),("SMICA_FULL","NILC_FULL"),
                ("SMICA_FULL","SMICA_noSZ_FULL")):
        aa=arr[names.index(a)];bb=arr[names.index(b)]
        contrasts[a+"__"+b]={"same_sky_abs_delta_eps2_eps3":np.abs(aa-bb).tolist(),
                              "same_sky_relative_delta_eps2_eps3":(
                                  np.abs(aa-bb)/(.5*(aa+bb))).tolist(),
                              "statistical_independence":"NOT_ASSUMED"}
    ranges={
      "eps2_processing_min_max":[float(np.min(arr[:,0])),float(np.max(arr[:,0]))],
      "eps3_processing_min_max":[float(np.min(arr[:,1])),float(np.max(arr[:,1]))],
      "sigma_anchor_eps1_zero_processing_min_max":[
           float(min(x["algebraic_eps1_zero"]["Sigma2_anchor_only_if_conditions_met"] for x in map_rows.values())),
           float(max(x["algebraic_eps1_zero"]["Sigma2_anchor_only_if_conditions_met"] for x in map_rows.values()))
       ]
    }
    beam={
      "status":"ONLY_DECLARED_GAUSSIAN_CONVOLUTION_ILLUSTRATION_NOT_MEASURED_MAP_BEAM_OR_COMPONENT_TRANSFER",
      "fwhm_arcmin_scenarios":{
        str(v):{str(ell):{"B_l":gaussian_beam_l(ell,v),
                        "epsilon_deconvolution_multiplier":1/gaussian_beam_l(ell,v)}
                for ell in (2,3)}
         for v in (5.,10.)
      }
    }
    report={
      "schema":"htt.Planck_PR3_MES_PSTF_lowell_source_conditional/1",
      "claim_tier":"SOURCE_CONDITIONED_HARMONIC_NORMALIZATION_AND_SIMULATION_RESPONSE_ONLY",
      "date_KST":"2026-10-15",
      "parent_branch_head":"915d8bfd22b09f4d57fa5902110bc6fd8d3aa734",
      "original_research_ancestor_head":"13d8d85fa470d645d008986e8f77d8d0f70fdf54",
      "source_snapshots_sha256":SOURCE_HASHES,
      "FFP10_cache_sha256":observed,
      "FFP10_gate_sha256":digest(GATE),
      "raw_planck_temperature_mask_sha256":mask_ids,
      "nside64_selected_T_same_mask_n":mask_info["coarse_nside64_selected"],
      "same_sky_map_count":len(map_rows),
      "nine_same_sky_map_rows":map_rows,
      "same_sky_processing_eps_ranges":ranges,
      "same_sky_processing_pairs":contrasts,
      "SAG_eq_15_17_covariant_sqrtCl_conversion":{
         "ell2_factor":pstf_norm_factor(2),
         "ell3_factor":pstf_norm_factor(3),
         "temperature_monopole_microK":T0_MICROK,
         "normalization":"tau_A tau^A = (2ell+1)(2ell)!/(2^ell ell!^2)*sum_m |a_lm|^2/(4pi T0^2)",
         "primary_source":"SAG1997 ApJ476:435, arXiv:astro-ph/9904346, Eq(15),(17)-(19)",
         "application":"mathematical mapping of masked finite harmonic coefficients, not a bound on the true unmasked covariant temperature field"
      },
      "FFP10_conditional_processing":sim_analysis,
      "beam_scenarios":beam,
      "scientific_missing_fields":{
         "observer_residual_radiation_dipole":"UNMEASURED_OR_UNJUSTIFIED_ZERO",
         "Copernican_neighbourhood_multipole_derivatives":"UNKNOWN",
         "radiation_matter_congruence_link":"UNKNOWN",
         "true_fullsky_deconvolution_including_high_ell":"UNKNOWN",
         "physical_planck_Bianchi_transfer":"UNKNOWN",
         "actual_planck_joint_lowell_null":"NOT_ESTABLISHED",
         "physical_MES_shear_bound":"WITHHELD",
         "cosmic_observation_p_value":"NOT_CALIBRATED"
      },
      "runtime_elapsed_seconds":time.perf_counter()-t,
      "max_RSS_KiB_linux":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    np.savez_compressed(out/"conditional_ffp10_eps_samples.npz",
                        eps_cmb_full=eps_full,eps_cmb_same_mask=eps_mask,
                        eps_first300_paired=eps_pair,eps_noise_difference=noise_delta,
                        eps_mask_minus_full=mask_delta)
    fig,axs=plt.subplots(1,2,figsize=(11,4.7),layout="constrained")
    for j,l in enumerate((2,3)):
        axs[j].hist(eps_mask[:,j]*1e6, bins=36,alpha=.35,density=True,
                    label="FFP10 CMB 999 same-mask")
        axs[j].hist(eps_pair[:,j]*1e6,bins=25,histtype="step",lw=1.5,density=True,
                    label="FFP10 CMB+noise paired 300")
        axs[j].axvline(np.array(eps_pairs)[names.index("SMICA_FULL"),j]*1e6,
                       lw=1.6,color="black",label="actual SMICA_FULL processing")
        axs[j].set(xlabel=f"Conditional SAG PSTF norm ell={l}  [1e-6]",
                   ylabel="Descriptive simulated density",
                   title=f"ell={l}: same Planck common mask, not physical PTE")
        axs[j].legend(fontsize=7)
    fig.savefig(out/"planck_mes_eps_ffp_source_diagnostic.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
       "# 실제 Planck 저다중극과 공변 MES epsilon 연결 진단\n\n"
       "PR3 아홉 처리 산출물은 하나의 공통 하늘이며, FFP10 캐시는 **조건부 시뮬레이션 모델**이다. "
       "mask·beam·공변 미분 response가 보장되지 않아 실제 물리적 MES 상한은 산출하지 않는다.\n\n"
       f"- SAG(1997) Eqs 15,17: sqrt(C2)/T0 -> ||tau2|| factor {pstf_norm_factor(2):.10g}, "
       f"sqrt(C3)/T0 -> ||tau3|| factor {pstf_norm_factor(3):.10g}.\n"
       f"- SMICA_FULL observed tensor norm eps2={map_rows['SMICA_FULL']['ell2']['SAG_eq17_covariant_rms_tensor_norm']:.9g}, "
       f"eps3={map_rows['SMICA_FULL']['ell3']['SAG_eq17_covariant_rms_tensor_norm']:.9g} (masked projected-source expression).\n"
       f"- Across 9 one-sky products eps2={ranges['eps2_processing_min_max']}, eps3={ranges['eps3_processing_min_max']}.\n"
       f"- FFP10 999 matched sky mask-vs-full eps RMS={sim_analysis['ffp_999_matched_mask_minus_full_eps_rms']}; "
       f"300 paired-noise RMS={sim_analysis['ffp_300_paired_noise_minus_signal_eps_rms']}.\n"
       f"- Finite source l6..8 -> estimated ell2/3 mask-leak operator spectral norm="
       f"{sim_analysis['mask_l6_to8_leakage']['mask_operator_spectral_norm']:.6g}; "
       "NOT a global no-leakage bound for ell>8.\n"
       f"- Assumed geodesic eps1=0 algebraic sigma-sector anchor range: "
       f"{ranges['sigma_anchor_eps1_zero_processing_min_max']}. Not observational bound.\n\n"
       "**Unresolved:** true sky response/beam/filter; unmeasured CMB intrinsic eps1;"
       " Copernican spatial and temporal derivatives; radiation/matter observer motion;"
       " actual CMB Bianchi transport and empirical covariance/exchangeability. "
       "No new physical detection or physical-null p-value.\n",encoding="utf-8")
    print("COMPLETE_CASE", len(names),"processed maps, FFP10",n_cmb,n_noise,
          "selected", selected.sum(),"runtime_s",round(time.perf_counter()-t,3),
          "eps2/3_full",map_rows["SMICA_FULL"]["ell2"]["SAG_eq17_covariant_rms_tensor_norm"],
          map_rows["SMICA_FULL"]["ell3"]["SAG_eq17_covariant_rms_tensor_norm"],flush=True)
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    run(args.output_dir)
