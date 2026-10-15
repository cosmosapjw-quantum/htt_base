#!/usr/bin/env python3
"""Real Planck PR3 8 polarization processed-source modes and spin2 high-l response.

Reads immutable source coefficient cache and actual native Planck polarization
masks (NSIDE2048 NESTED). Measures finite high-l E/B -> retained low E/B
leakage on exactly the common confidence mask; NO sky physical B likelihood.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.planck_spin2_source_response import (
    real_spin2_design,finite_spin2_leakage,source_EB_band_powers,
    source_polar_mask,
)

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs"
NPZ=DATA/"retained_common_support_coefficients.npz"
PARENT=DATA/"planck_loop5_result.json"
NPZ_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
MASKS=[
 Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"),
 Path("/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits"),
 Path("/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits"),
]


def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(4<<20),b""):h.update(block)
    return h.hexdigest()


def run(out:Path):
    if out.exists():raise FileExistsError("create-only result directory expected")
    if digest(NPZ)!=NPZ_SHA:
        raise RuntimeError("registered Planck real-spin source coefficient bytes mismatch")
    parent=json.loads(PARENT.read_text())
    if parent["common_POL_nside64_pixel_count"]!=30021:
        raise RuntimeError("parent Planck polarization count drift")
    with np.load(NPZ,allow_pickle=False) as n:
        names=[str(s) for s in n["names_EB"]]
        arr=np.asarray(n["coeff_EB"],float)
        archived=json.loads(str(n["column_spin_metadata_json"].item()))
    if len(names)!=8 or arr.shape!=(8,64) or len(set(names))!=8:
        raise RuntimeError("source native Planck spin coefficients must be 8 same-sky products")
    if len(archived)!=64:
        raise RuntimeError("source spin coefficient chart changed")
    # Native pol common source mask: official, HM missing pixels, OE missing.
    selected,mask_desc=source_polar_mask(MASKS,nside_in=2048,nside_out=64)
    if selected.sum()!=30021:
        raise RuntimeError(f"actual source polarization mask selected={selected.sum()} rather than 30021")
    # Healpy spin harmonic template for source Q/U Stokes frame; actual measured
    # coefficients are the PREVIOUS released native map fits, not new independent sky.
    X,meta=real_spin2_design(nside=64,lmax=8)
    low=meta[:64]
    for i,(orig,new) in enumerate(zip(archived,low)):
        if (int(orig["ell"]),str(orig["E_or_B"]),int(orig["m"]),str(orig["phase"]))!=(
            new["ell"],new["spin"],new["m"],new["phase"]):
            raise RuntimeError(f"source real-spin E/B column convention mismatch {i}")
    low_x=X[:,:64]
    high_x=X[:,64:]
    high_meta=meta[64:]
    _,masked=finite_spin2_leakage(low_x,high_x,low,high_meta,selected)
    _,full=finite_spin2_leakage(low_x,high_x,low,high_meta,np.ones(len(selected),bool))
    powers=source_EB_band_powers(arr,low)
    parent_cmp=parent["same_sky_polarization_contrasts"]
    k={v:i for i,v in enumerate(names)}
    smica_hm=np.linalg.norm((arr[k["SMICA_HM1"]]-arr[k["SMICA_HM2"]])*.5)
    if abs(smica_hm-float(parent_cmp["SMICA_HM_split_difference_EB_norm_microK"]))>2e-10:
        raise RuntimeError("previous same-sky Planck polarization split source mismatch")
    contrasts={}
    for label,na,nb in [
       ("SMICA_HM","SMICA_HM1","SMICA_HM2"),
       ("SMICA_OE","SMICA_OE1","SMICA_OE2"),
       ("NILC_HM","NILC_HM1","NILC_HM2"),
       ("FULL_SMICA_VS_NILC","SMICA_FULL","NILC_FULL")]:
        a=arr[k[na]];b=arr[k[nb]]
        d=a-b
        entry={"full_64D_EB_norm_microK":float(np.linalg.norm(d)),
               "relative_EB_norm_to_average":float(np.linalg.norm(d)/np.linalg.norm((a+b)/2)),
               "per_ell_E_B_difference_C_microK2":{
                 str(l):{spin:float(source_EB_band_powers(d[None,:],low)[str(l)][spin][0])
                         for spin in ("E","B")} for l in (2,3)}
        }
        contrasts[label]=entry
    report={
        "schema":"htt.Planck_real_spin2_EB_source_and_highmode_mask_response/1",
        "science_status":"ACTUAL_ONE_SKY_EIGHT_PROCESSING_SOURCE_EB_AND_FINITE_HIGHMODE_OPERATOR_ONLY",
        "source_npz_sha256":NPZ_SHA,
        "parent_result_sha256":digest(PARENT),
        "native_pol_masks":[{"path":str(p),"sha256":digest(p)} for p in MASKS],
        "native_pol_mask_details":mask_desc,
        "temperature_mask_not_reused_for_polarization":True,
        "spin_source_product_names":names,
        "source_EB_coefficients_shape":[8,64],
        "source_real_spin_chart":"for ell2..5, E then B, m0, sqrt2 Re, sqrt2 Im (negative Im sign stored complex)",
        "per_ell_EB_source_C_microK2":{
            ell:{spin:powers[ell][spin].tolist() for spin in ("E","B")}
            for ell in ("2","3","4","5")
        },
        "same_physical_sky_processed_source_contrasts":contrasts,
        "masked_l6to8_EB_leakage":masked,
        "full_pixel_l6to8_EB_leakage":full,
        "finite_low_span":{"ell_min":2,"ell_max":5,"real_EB_columns":64},
        "finite_high_span":{"ell_min":6,"ell_max":8,"real_EB_columns":90},
        "physical_limitations":{
           "source_EB_only_masked_ell2to5":"TRUE",
           "no_actual_high_ell_EB_true_source_amplitudes":"TRUE",
           "no_spin2_actual_raw_map_refit_lmax8":"TRUE",
           "no_matched_end_to_end_polarization_noise_null":"TRUE",
           "no_pol_noise_B_mode_cosmology_significance":"TRUE",
           "no_physical_Bianchi_source_likelihood":"TRUE",
           "further_full_transfer_beam_pixel_foregrounds":"UNQUALIFIED"
        },
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout="constrained")
    t=np.arange(len(names))
    for ell,spin,marker in [("2","E","o"),("3","E","s"),("2","B","^"),("3","B","d")]:
        axes[0].plot(t,powers[ell][spin],marker=marker,label=f"{spin}{spin} ell={ell}")
    axes[0].set_xticks(t,names,rotation=52,ha="right",fontsize=7)
    axes[0].set(ylabel="Finite masked spin2 E/B C_ell [microK^2]",
                title="One Planck sky across 8 processing products")
    axes[0].legend(fontsize=7);axes[0].grid(alpha=.2)
    modes=[("E_from_E","E<-E"),("B_from_E","B<-E"),
           ("E_from_B","E<-B"),("B_from_B","B<-B")]
    a=np.arange(4)
    width=.35
    axes[1].bar(a-width/2,[masked[k+"_spectral_norm"] for k,_ in modes],
                width,label="Actual common POL mask")
    axes[1].bar(a+width/2,[full[k+"_spectral_norm"] for k,_ in modes],
                width,label="Full NSIDE64 pixel chart")
    axes[1].set_xticks(a,[n for _,n in modes])
    axes[1].set(ylabel="ell6..8 -> ell2..5 finite spectral norm",
                title="Declared polarization higher-mode alias, not a sky error")
    axes[1].legend(fontsize=8);axes[1].grid(axis="y",alpha=.2)
    fig.savefig(out/"planck_spin2_source_pol_alias.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
       "# P2 L01: Planck PR3 실제 편광 처리 8개와 physical spin2 응답\n\n"
       f"한 실제 Planck 하늘 8개 처리 결과의 l2..5 E/B 모드를 source-hashed NPZ에서 사용. "
       f"물리적인 spin2 HEALPix Q/U 연산자로 원본 NSIDE2048 PMASK 세 개를 교집합, "
       f"RING NSIDE64 선택 {int(selected.sum())}개를 원본과 재현. "
       "Temperature TMASK 26846개의 재사용을 명시적으로 거부.\n\n"
       f"Finite ell6..8의 저차 ell2..5 masked alias spectral norm: "
       f"E<-E={masked['E_from_E_spectral_norm']:.6g}; "
       f"B<-E={masked['B_from_E_spectral_norm']:.6g}; "
       f"E<-B={masked['E_from_B_spectral_norm']:.6g}; "
       f"B<-B={masked['B_from_B_spectral_norm']:.6g}. "
       "원본 observed ell>5 E/B amplitudes는 지금 추출하지 않았으므로, "
       "이 값은 실제 우주의 B-mode 누출량 상한이 아니고 finite mask transfer 연산자이다.\n\n"
       "Planck 2018 VII 논문은 B polarization이 모든 scale에서 noise dominated임을 "
       "명시한다. 따라서 이 결과는 새로운 B 검출, cosmic parity violation, "
       "물리적 Bianchi posterior, anomaly p를 제공하지 않는다. "
       "완전한 beam/foreground/actual high-ell E/B map과 end-to-end null "
       "matched simulation은 아직 source qualification이 필요하다.\n",
       encoding="utf-8")
    print("PLANCK_SPIN2_POL",int(selected.sum()),"products",len(names),
          "masked_E_to_B",masked["B_from_E_spectral_norm"],
          "masked_B_to_E",masked["E_from_B_spectral_norm"])
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    run(a.output_dir)
