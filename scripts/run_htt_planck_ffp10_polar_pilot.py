#!/usr/bin/env python3
"""Exact-source Planck FFP10 SMICA Q/U pilot on native RING simulation pixels.

For each selected raw CMB/noise realization, project native Q/U through
the SAME observed Planck NSIDE2048->64 PMASK and ell2..5 physical spin2
least-squares operator. Raw FFP10 FITS headers do not supply COORDSYS or
POLCCONV. Results are conditional on an assumed unchanged U+ chart;
NOT a physical Planck null, p-value, evidence, or Bianchi detection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
import numpy as np

from obsstat.planck_ffp10_polarized_lowell import (
    PlanckFFPPolarError,build_parent_lookup,coarse_selected_mean_rings,
    load_ffp10_pol_projected,projected_covariance_and_rank,
    split_source_contrasts
)
from obsstat.planck_spin2_source_response import (
    real_spin2_design,fit_spin2_operator,source_EB_band_powers,
    source_polar_mask
)

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
PREV=BASE/"results/L01_raw_SMICA_spin2_v1/smica_full_polarization_finite_modes.npz"
SOURCE=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
SIMDIR=Path("/mnt/extdrive/workdir/raw/planck_ffp10/smica")
CMB_CACHE=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
SOURCE_NPZ_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
EXPECTED_FILE_SIZE=603987840
MASKS=[
 Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"),
 Path("/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits"),
 Path("/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits"),
]


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as ff:
        for chunk in iter(lambda:ff.read(16<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def band_power_vector(a,meta):
    data=source_EB_band_powers(np.asarray(a)[None,:],meta)
    return [float(data[str(ell)][spin][0]) for ell,spin in (
        (2,"E"),(2,"B"),(3,"E"),(3,"B"))]


def run(out:Path,*,cmb_count=8,noise_count=8,source_full_sha=True):
    if out.exists():
        raise FileExistsError("create-only and immutable source output directory")
    if not (1<=cmb_count<=24 and 1<=noise_count<=24):
        raise ValueError("scoped pilot supports 1..24 unique CMB and noise realizations")
    t=time.perf_counter()
    if digest(SOURCE)!=SOURCE_NPZ_SHA:
        raise RuntimeError("PR3 retained source coefficients identity drift")
    with np.load(SOURCE,allow_pickle=False) as a:
        names=[str(x) for x in a["names_EB"]]
        archived=np.asarray(a["coeff_EB"],float)
        if archived.shape!=(8,64):
            raise RuntimeError("wrong Planck polarization prior source")
        contrasts=split_source_contrasts(archived,names)
        observed_ref=archived[names.index("SMICA_FULL")]
    with np.load(PREV,allow_pickle=False) as a:
        prior=np.asarray(a["low_coeff64"],float)
    if np.max(abs(observed_ref-prior))>1e-10:
        raise RuntimeError("native Planck observed source differs from prior exact refit")
    selected,maskinfo,fine=source_polar_mask(MASKS,return_fine=True)
    assert int(selected.sum())==30021
    idx=build_parent_lookup(2048,64,selected,fine)
    del fine
    design,meta=real_spin2_design(nside=64,lmax=5)
    op,operatorinfo=fit_spin2_operator(design,selected)
    entries={}
    data={}
    for label,n in (("cmb",cmb_count),("noise",noise_count)):
        directory=SIMDIR/(label+"_mc")
        cohort=[]
        coeffs=[]
        for mc in range(n):
            path=directory/(f"dx12_v3_smica_{label}_mc_{mc:05d}_raw.fits")
            if not path.is_file() or path.stat().st_size!=EXPECTED_FILE_SIZE:
                raise RuntimeError(f"missing actual source file or unexpected size: {path}")
            # One source realization contributes one row. No modulo ID recycling.
            input_sha=digest(path) if source_full_sha else None
            record=load_ffp10_pol_projected(path,idx,op,
                  u_sign=1,include_intensity=(label=="cmb" and mc==0))
            coeffs.append(record["coefficients_microK"])
            row={"mc_id":mc,
                 "source_basename":path.name,
                 "source_size_bytes":path.stat().st_size,
                 "source_sha256":input_sha,
                 "source_header":record["source"]["header"],
                 "selected_Q_U_microK_rms":record["selected_Q_U_microK_rms"],
                 "lowell_power_uK2":band_power_vector(record["coefficients_microK"],meta)}
            if label=="cmb" and mc==0:
                # Source-independent RING->NESTED pixel projection validation:
                # compare unmasked intensity coarse selected parent means with
                # existing full PR150 temperature cache for the SAME MC ID.
                from astropy.io import fits
                with fits.open(path,memmap=True) as ff:
                    native=ff[1].data["INTENSITY"].reshape(-1)
                    intensity=coarse_selected_mean_rings(native,idx,use_source_mask=False)*1e6
                with np.load(CMB_CACHE,allow_pickle=False) as cache:
                    ids=np.asarray(cache["cmb_ids"])
                    ci=np.where(ids==mc)[0]
                    if len(ci)!=1: raise RuntimeError("existing PR150 MC ID not unique")
                    reference=np.asarray(cache["cmb_maps"][int(ci[0])],float)[selected]
                e=np.abs(intensity-reference)
                row["independent_raw_to_k1_temperature_control"]={
                    "rms_microK":float(np.sqrt(np.mean(e*e))),
                    "maxabs_microK":float(np.max(e)),
                    "source_operators":"our NESTED parent float64 mean versus previous source hp.ud_grade float32 reductions",
                }
                if np.max(e)>1e-3:
                    raise RuntimeError("FFP10 native RING downsampling not source compatible")
            cohort.append(row)
            print(f"FFP10_{label.upper()} mc={mc:02d} norm={np.linalg.norm(coeffs[-1]):.5g}"
                  f" source_full_sha={input_sha is not None}",flush=True)
        entries[label]=cohort
        data[label]=np.vstack(coeffs)
    signals=data["cmb"]
    noise=data["noise"]
    pair_n=min(cmb_count,noise_count)
    if pair_n<=0:raise RuntimeError("actual disjoint CMB+noise paired draw missing")
    matched=signals[:pair_n]+noise[:pair_n]
    cvar=projected_covariance_and_rank(signals)
    nvar=projected_covariance_and_rank(noise)
    nb={"CMB_signal_conditional_cov_rank":int(cvar["empirical_rank"]),
        "noise_conditional_cov_rank":int(nvar["empirical_rank"]),
        "CMB_max_empirical_rank":int(cvar["max_empirical_rank"]),
        "noise_max_empirical_rank":int(nvar["max_empirical_rank"])}
    obsbands=band_power_vector(observed_ref,meta)
    signalbands=np.array([band_power_vector(z,meta) for z in signals])
    noisebands=np.array([band_power_vector(z,meta) for z in noise])
    matchedbands=np.array([band_power_vector(z,meta) for z in matched])
    def empirical_stats(a):
        return {"medians":np.median(a,axis=0).tolist(),
                "min":np.min(a,axis=0).tolist(),
                "max":np.max(a,axis=0).tolist(),
                "sample_count":len(a)}
    # Pointwise quadratic identity, includes CMB–noise cross in the same draw.
    crossbands=np.empty_like(matchedbands)
    for k in range(pair_n):
        for j,(ell,spin) in enumerate(((2,"E"),(2,"B"),(3,"E"),(3,"B"))):
            offset=0 if ell==2 else 10
            offset+=0 if spin=="E" else 2*ell+1
            aa=signals[k,offset:offset+2*ell+1]
            bb=noise[k,offset:offset+2*ell+1]
            crossbands[k,j]=2*np.dot(aa,bb)/(2*ell+1)
    residual=matchedbands-signalbands[:pair_n]-noisebands[:pair_n]-crossbands
    if np.max(abs(residual))>1e-12:
        raise RuntimeError("paired CMB+noise spin2 power decomposition failed")
    split_norms={name:float(np.linalg.norm(v)) for name,v in contrasts.items()}
    result={
      "schema":"htt.FFP10_POL_SMICA_lowell_native_stokes_source_pilot/1",
      "source_kind":"SOURCE_CONDITIONED_MATCHED_CMB_PLUS_NOISE_SCOPED_PILOT",
      "scientific_claim":"NOT_A_PLANCK_COSMOLOGY_NULL_OR_BIANCHI_INFERENCE",
      "simulation_raw_source_cmb_count":cmb_count,
      "simulation_raw_source_noise_count":noise_count,
      "simulation_unique_pair_count":pair_n,
      "source_format":"native HEALPIX RING NSIDE2048 3*1024E packed IQU in K_CMB",
      "source_COORDFRAME":"UNSPECIFIED_IN_FITS_HEADER",
      "source_POLCONV":"UNSPECIFIED_IN_FITS_HEADER",
      "formal_sim_U_sign_chart":"U_PLUS_ASSUMED",
      "observed_actual_Q_U_reference":"fixed prior lowell SMICA_FULL native PMASK l2..5 fit",
      "actual_observed_one_sky_four_EB_bands_microK2":obsbands,
      "source_native_pol_mask":maskinfo,
      "source_HEALPix_lookup_sha256":idx.idx_sha256,
      "source_operator":operatorinfo,
      "source_banks":entries,
      "covariance_numerical_rank":nb,
      "CMB_only_empirical_bands":empirical_stats(signalbands),
      "noise_only_empirical_bands":empirical_stats(noisebands),
      "CMB_plus_noise_matched_empirical_bands":empirical_stats(matchedbands),
      "signal_noise_cross_empirical_bands":empirical_stats(crossbands),
      "quadratic_closure_maxabs":float(np.max(abs(residual))),
      "same_sky_hm_oe_64D_contrasts":split_norms,
      "limitations":[
        "8/8 or user-selected <=24 cohort is a SUBSET of delivered 999/300; not full sampled null",
        "No verified simulation-vs-observed COORDSYS/POLCCONV frame matching from raw FITS header",
        "No independent noise simulation for each observed HM/OE split conditional map",
        "Signal-simulation and noise realization ID paired 1:1 with no recycling",
        "Possible simulation residual foreground/systematic mismatch and Planck polarized B is noise dominated",
        "Empirical noise covariance rank <= N_noise-1, no inverse/p-value/Bianchi family claim",
        "All actual processed Planck SMICA/NILC/HM/OE are SAME COSMOLOGICAL SKY",
        "Finite ell<=5 masked real spin2 fit, unmodeled high ell and beam transfer not corrected",
      ],
      "execution":{"elapsed_seconds":time.perf_counter()-t,
                   "max_rss_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
    }
    out.mkdir(parents=True)
    # NPZ has small 64D coefficients, NO source FITS copy in Git.
    np.savez_compressed(out/"paired_coefficients_lowell.npz",
        signal_microK=signals,noise_microK=noise,
        signal_plus_noise_microK=matched,
        observed_microK=observed_ref,
        signal_bandpower_microK2=signalbands,
        noise_bandpower_microK2=noisebands,
        pair_bandpower_microK2=matchedbands)
    (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    (out/"REPORT_KO.md").write_text(
        "# Planck FFP10 실제 원본 Q/U의 소수 코호트 matched pilot\n\n"
        f"실제 NSIDE2048 RING FFP10 SMICA CMB-only {cmb_count}개 + noise-only {noise_count}개 "
        f"실현을 고유 ID로 읽어 실제 Planck observed PMASK selected {idx.n_selected} NSIDE64 "
        "픽셀의 물리적 spin2 Q/U 응답으로 투영했다. "
        f"선택한 independent source-cohort paired ID 수={pair_n}.\n\n"
        "실제 관측 한 하늘의 8 processing product를 simulation realization이라고 세지 않았다. "
        "원본 파일의 POLCCONV와 COORDSYS는 지정되지 않았으며 U+ chart 가정만 사용했다. "
        "여기서 scalar E/B power 값은 finite source/mask estimator의 output이고 실제 "
        "Planck physical conditional null probability가 아니다.\n\n"
        f"실제 source observed EE2/BB2/EE3/BB3={obsbands}; noise median="
        f"{np.median(noisebands,axis=0).tolist()}; matched median="
        f"{np.median(matchedbands,axis=0).tolist()}.\n\n"
        f"Source CMB+noise harmonic power identity residual="
        f"{result['quadratic_closure_maxabs']:.4g} microK². "
        f"Noise covariance rank={nvar['empirical_rank']} of 64D, "
        "not enough for a full 64D inverse and no significance rank claim. "
        "Physical E/B cov/Planck frame, component-separation noise and source "
        "selection simulation adequacy still require validation.\n",
        encoding="utf-8")
    print("PILOT_END",result["execution"],"obs",obsbands,
          "noise_medians",result["noise_only_empirical_bands"]["medians"],flush=True)
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--cmb-count",type=int,default=8)
    ap.add_argument("--noise-count",type=int,default=8)
    ap.add_argument("--skip-full-sha",action="store_true")
    args=ap.parse_args()
    run(args.output_dir,cmb_count=args.cmb_count,noise_count=args.noise_count,
        source_full_sha=not args.skip_full_sha)
