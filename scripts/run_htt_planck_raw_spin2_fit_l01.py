#!/usr/bin/env python3
"""Actual Planck SMICA_FULL raw Q/U native FITS, same POL mask and spin2 high-mode fit.

Performs read-only chunked NSIDE2048 NESTED -> NSIDE64 RING masked Q/U mean,
then source-frame E/B joint OLS for ell<=5 and ell<=8. A matched l<=5 fit
must reproduce the previously published eight-product SMICA_FULL coefficients.
This is NOT beam- or high-l physically debiased E/B or physical B-mode PTE.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from astropy.io import fits
import healpy as hp

from obsstat.planck_spin2_source_response import (
    source_polar_mask,real_spin2_design,fit_spin2_operator,
    source_EB_band_powers
)

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path("/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits")
BASE=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs"
NPZ=BASE/"retained_common_support_coefficients.npz"
NPZ_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
MASKS=[
 Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"),
 Path("/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits"),
 Path("/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits"),
]


def digest(file):
    h=hashlib.sha256()
    with file.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()


def raw_nested_masked_mean(column, source_mask, *, nside_in=2048,
                           nside_out=64,chunk=384):
    """Exact input NESTED -> output RING masked coarse mean."""
    if (not hp.isnsideok(nside_in) or not hp.isnsideok(nside_out)
        or nside_in<nside_out or nside_in % nside_out or chunk<1):
        raise ValueError("valid HEALPix downgrade required")
    nside64=hp.nside2npix(nside_out)
    children=(nside_in//nside_out)**2
    nside2048=hp.nside2npix(nside_in)
    if len(column)!=nside2048 or source_mask.shape!=(nside2048,) or source_mask.dtype!=bool:
        raise ValueError("native NESTED map and common mask required")
    values=np.full(nside64,np.nan,float)
    coverage=np.zeros(nside64,float)
    for lo in range(0,nside64,chunk):
        hi=min(nside64,lo+chunk)
        sl=slice(lo*children,hi*children)
        V=np.asarray(column[sl],float).reshape(hi-lo,children)
        m=source_mask[sl].reshape(hi-lo,children)
        good=m&np.isfinite(V)&(V>-1e20)
        count=good.sum(axis=1)
        numer=np.sum(np.where(good,V,0.),axis=1,dtype=float)
        values[lo:hi]=np.divide(numer,count,out=np.full(hi-lo,np.nan),where=count>0)
        coverage[lo:hi]=count/children
    return hp.reorder(values,n2r=True),hp.reorder(coverage,n2r=True)


def band_summary(a,meta):
    z=source_EB_band_powers(a[None,:],meta)
    return {ell:{spin:float(v[0]) for spin,v in vals.items()} for ell,vals in z.items()}


def run(out:Path):
    if out.exists():raise FileExistsError("create-only actual raw polarization output")
    if SOURCE.stat().st_size!=2013312960:
        raise RuntimeError("wrong Planck PR3 full SMICA native FITS")
    if digest(NPZ)!=NPZ_SHA:
        raise RuntimeError("source EB lowell coefficient cache not immutable")
    with np.load(NPZ,allow_pickle=False) as v:
        names=[str(x) for x in v["names_EB"]]
        old=np.asarray(v["coeff_EB"][names.index("SMICA_FULL")],float)
        colmeta=json.loads(str(v["column_spin_metadata_json"].item()))
    chosen,mmeta,fine=source_polar_mask(MASKS,return_fine=True)
    if chosen.sum()!=30021:
        raise RuntimeError("POL source mask native common selected count mismatch")
    with fits.open(SOURCE,memmap=True) as ff:
        hd=ff[1]
        if (hd.header.get("NSIDE")!=2048
            or hd.header.get("ORDERING")!="NESTED"
            or hd.header.get("TUNIT2")!="K_CMB"
            or hd.header.get("TUNIT3")!="K_CMB"
            or not {"Q_STOKES","U_STOKES"}<=set(hd.columns.names)):
            raise RuntimeError("raw Planck SMICA FULL physical Q/U input contract mismatch")
        Q,cq=raw_nested_masked_mean(hd.data["Q_STOKES"],fine)
        U,cu=raw_nested_masked_mean(hd.data["U_STOKES"],fine)
    if (not np.isfinite(Q[chosen]).all() or
        not np.isfinite(U[chosen]).all() or
        np.min(cq[chosen])<.995-1e-13 or np.min(cu[chosen])<.995-1e-13):
        raise RuntimeError("real Planck Stokes source has insufficient selected coverage")
    del fine
    design,meta=real_spin2_design(nside=64,lmax=8)
    for i,(orig,new) in enumerate(zip(colmeta,meta[:64])):
        if (int(orig["ell"]),str(orig["E_or_B"]),int(orig["m"]),str(orig["phase"]))!=(
           new["ell"],new["spin"],new["m"],new["phase"]):
            raise RuntimeError(f"published spin2 chart differs on mode {i}")
    sel=np.r_[chosen,chosen]
    stacked=np.r_[Q[chosen],U[chosen]]*1e6
    low,low_meta=fit_spin2_operator(design[:,:64],chosen)
    full,full_meta=fit_spin2_operator(design,chosen)
    coeff_low=low@stacked
    coeff_high=full@stacked
    max_abs_diff=float(np.max(np.abs(coeff_low-old)))
    if max_abs_diff>3e-6:
        raise RuntimeError(f"source original l2..5 spin2 coefficients not reproduced: maxabs {max_abs_diff}")
    remainder_low=np.linalg.norm(stacked-(design[:,:64][sel]@coeff_low))/np.sqrt(len(stacked))
    remainder_high=np.linalg.norm(stacked-(design[sel]@coeff_high))/np.sqrt(len(stacked))
    power_low=band_summary(coeff_low,meta[:64])
    power_high=band_summary(coeff_high,meta)
    rows={
        "schema":"htt.Planck_SMICA_FULL_raw_QU_spin2_lmax5_vs8/1",
        "claim":"ACTUAL_NATIVE_PLANCK_QU_REPRODUCED_AND_FINITE_LMAX8_SENSITIVITY_ONLY",
        "actual_source_fits_path":str(SOURCE),
        "actual_source_size":SOURCE.stat().st_size,
        "actual_source_sha256":digest(SOURCE),
        "source_cached_lowell_npz_sha256":NPZ_SHA,
        "native_P_mask_selected_64":int(chosen.sum()),
        "mask":mmeta,
        "input_units":"K_CMB raw; microK fitted",
        "full_input_2048":"NESTED",
        "reduced_output_64":"RING",
        "original_source_lowell_coefficients_maxabs_microK":max_abs_diff,
        "fit_ellmax5":low_meta,
        "fit_ellmax8":full_meta,
        "source_EB_ell2to5_power_ellmax5":power_low,
        "source_EB_ell2to8_power_ellmax8":power_high,
        "source_lowell_coeff_movement":{
            "ell2to5_real64_maxabs_microK":float(np.max(np.abs(coeff_high[:64]-coeff_low))),
            "ell2to5_real64_norm_microK":float(np.linalg.norm(coeff_high[:64]-coeff_low)),
            "source_B_ell2_Cratio_lmax8_over5":float(power_high["2"]["B"]/power_low["2"]["B"]) if power_low["2"]["B"]>0 else None,
            "source_B_ell3_Cratio_lmax8_over5":float(power_high["3"]["B"]/power_low["3"]["B"]) if power_low["3"]["B"]>0 else None,
        },
        "selected_Q_U_residual_rms_microK_ellmax5":float(remainder_low),
        "selected_Q_U_residual_rms_microK_ellmax8":float(remainder_high),
        "true_fullsky_EB_deconvolution":"NOT_PERFORMED",
        "instrument_beam_component_separation_transfer":"NOT_QUALIFIED",
        "polarization_foreground_and_noise_null":"NOT_QUALIFIED",
        "pure_EB_and_B_null_pvalue":"NOT_QUALIFIED",
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
    # 154 coefficients only; the raw Q/U 2*49k output is lightweight.
    np.savez_compressed(out/"smica_full_polarization_finite_modes.npz",
                        low_coeff64=coeff_low,
                        extended_coeff154=coeff_high,
                        selected_nside64_ring_pol=np.asarray(chosen,bool))
    (out/"REPORT_KO.md").write_text(
       "# Planck 실제 SMICA_FULL raw 2 GB Q/U 편광: spin2 ellmax5→8\n\n"
       "원본 NSIDE2048 NESTED Stokes Q/U를 직접 읽되 수정하지 않고, "
       "실제 Planck 공통 PMASK/halfmission/oddeven의 selected 30021 low pix에서만 "
       "nested chunk reduction 후 RING spin2 fit을 수행했다.\n\n"
       f"동일 ellmax5 source cached 저차 계수를 직접 재현한 max difference={max_abs_diff:.6g} microK.\n"
       f"ellmax5→8 진짜 raw same-sky E/B l2..5 finite coefficient 이동 norm="
       f"{rows['source_lowell_coeff_movement']['ell2to5_real64_norm_microK']:.6g} microK, "
       f"ell2 BB C ratio={rows['source_lowell_coeff_movement']['source_B_ell2_Cratio_lmax8_over5']:.6g}.\n\n"
       "This is a refit sensitivity under a fixed selection, NOT a physically unbiased "
       "full-sky E/B, primordial B detection, anomaly p, or Bianchi likelihood. "
       "Source beam, high-ell beyond 8, polarized systematics and physical null missing.\n",
       encoding="utf-8")
    print("RAW_SMICA_POL_SPIN2_REPRODUCED",max_abs_diff,
          "low_vs_high_norm",rows["source_lowell_coeff_movement"]["ell2to5_real64_norm_microK"],
          "B2_ratio",rows["source_lowell_coeff_movement"]["source_B_ell2_Cratio_lmax8_over5"])
    return rows


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    args=p.parse_args()
    run(args.output_dir)
