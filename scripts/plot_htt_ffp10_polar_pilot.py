#!/usr/bin/env python3
"""Compact descriptive four-band figures for a non-qualified FFP10 POL pilot.

Simulation cohort is deliberately small and the frame/pol convention is not
declared in raw FFP10 FITS, so NO anomaly p-value is computed.
"""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.planck_ffp10_polarized_lowell import split_source_contrasts
from obsstat.planck_spin2_source_response import real_spin2_design,source_EB_band_powers

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"


def sample_bands(samples,mode_metadata):
    x=np.asarray(samples)
    if x.ndim!=2 or x.shape[1]!=len(mode_metadata):
        raise ValueError("actual source-coupled 64D E/B vectors expected")
    k=source_EB_band_powers(x,mode_metadata)
    return np.column_stack([k[str(ell)][mode] for ell,mode in (
       (2,"E"),(2,"B"),(3,"E"),(3,"B"))])


def summarize(source_dir:Path):
    source_dir=source_dir.resolve()
    f=source_dir/"result.json"
    if not f.is_file():raise FileNotFoundError(f)
    summary=json.loads(f.read_text())
    with np.load(source_dir/"paired_coefficients_lowell.npz",allow_pickle=False) as d:
        signal=np.asarray(d["signal_microK"])
        noise=np.asarray(d["noise_microK"])
        matched=np.asarray(d["signal_plus_noise_microK"])
        observed=np.asarray(d["observed_microK"])
    if len(observed)!=64 or signal.shape!=(len(signal),64) or noise.shape!=(len(noise),64):
        raise ValueError("64D source-mode chart and cohort sizes mismatch")
    _,meta=real_spin2_design(nside=8,lmax=5)
    s=sample_bands(signal,meta)
    n=sample_bands(noise,meta)
    a=sample_bands(matched,meta)
    o=sample_bands(observed[None,:],meta)[0]
    with np.load(SOURCE,allow_pickle=False) as raw:
        names=[str(z) for z in raw["names_EB"]]
        data=np.asarray(raw["coeff_EB"],float)
    split=split_source_contrasts(data,names)
    hm=sample_bands(split["HM_half_difference"][None,:],meta)[0]
    oe=sample_bands(split["OE_half_difference"][None,:],meta)[0]
    co=np.column_stack([s,n,a])
    labels=["E, ell2","B, ell2","E, ell3","B, ell3"]
    n_pairs=len(a)
    dsc={
        "schema":"htt.FFP10_POL_12pair_DESCRIPTIVE_SOURCE_SUMMARY/1",
        "input_source_dir":str(source_dir.relative_to(ROOT)),
        "observed_source_bands_microK2":o.tolist(),
        "source_split_HM_halfdiff_power_microK2":hm.tolist(),
        "source_split_OE_halfdiff_power_microK2":oe.tolist(),
        "distinct_realizations":{"cmb":len(s),"noise":len(n),"paired":n_pairs},
        "same_physical_sky_processing_products_not_independent":True,
        "formal_small_cohort_mc_tail_resolution_if_exchangeable_only":1/(n_pairs+1),
        "observation_and_MC_exchangeability":"NOT_ADMITTED_NO_PHYSICAL_P_VALUE",
        "labels":labels,
        "noise_only_median_microK2":np.median(n,axis=0).tolist(),
        "noise_only_max_microK2":np.max(n,axis=0).tolist(),
        "observed_to_noise_median_ratio_DESCRIPTIVE_ONLY":
            (o/np.maximum(np.median(n,axis=0),1e-300)).tolist(),
        "physical_limitations":[
            "FFP10 source header POLCCONV/COORDSYS unspecified",
            "Noise-only full-mission sims are not source-matched HM/OE split differences",
            "n<=24 pilot is not a cosmic / foreground complete null",
            "zero CMB power and residual polarization foregrounds still model-dependent",
        ]
    }
    fig,axs=plt.subplots(2,2,figsize=(11,8),layout="constrained")
    for j,ax in enumerate(axs.ravel()):
        for loc,(name,bands) in enumerate((("CMB-only",s),("noise-only",n),
                                           ("CMB+noise ID-paired",a))):
            ax.scatter(np.full(len(bands),loc,dtype=float)
                       +np.linspace(-.15,.15,len(bands)),
                       bands[:,j],s=12,alpha=.7,label=name)
            ax.plot([loc-.25,loc+.25],
                    [float(np.median(bands[:,j]))]*2,lw=2)
        ax.axhline(o[j],ls="--",lw=1.5,color="black",label="real SMICA_FULL")
        ax.set_xticks(np.arange(3),["CMB","noise","paired"])
        ax.set(ylabel="finite masked C_ell [microK²]",
               title=labels[j]+" (NO calibrated null)")
        ax.grid(axis="y",alpha=.2)
        if j==0:ax.legend(fontsize=7)
    fig.savefig(source_dir/"observed_FFP10_polarization_four_bands.png",dpi=150)
    plt.close(fig)
    out=source_dir/"DESCRIPTIVE_SUMMARY.json"
    out.write_text(json.dumps(dsc,indent=2,ensure_ascii=False)+"\n")
    print("SUMMARY_SOURCE_BANDS",o.tolist(),"noise_median",np.median(n,axis=0).tolist(),
          "tail_min_if_qualified",dsc["formal_small_cohort_mc_tail_resolution_if_exchangeable_only"])
    return dsc


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",type=Path,required=True)
    args=ap.parse_args()
    summarize(args.input_dir)
