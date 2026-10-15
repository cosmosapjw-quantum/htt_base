#!/usr/bin/env python3
"""Actual Planck/FFP10 exact finite quadrupole+octupole Teff quartic moment.

Combines original legacy Teff functional with modern orthonormal l2+l3
harmonic response and the previously source-verified Planck/FFP10 same-sky
and independent simulation archive. The deltaF4 is a deterministic
*bandlimited source statistic*, not a new physical CMB likelihood or
an additional observation independent of the original a_lm.

Only ell2 and ell3 are included; unmeasured intrinsic ell1 and all ell>=4
are absent from the declared finite ansatz, NOT certified physically zero.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.legacy_teff_octupole_exact import moment_delta_l23
from obsstat.mes_eps_measurement_bridge import fixed_ols_operator,fit_rows_of_simulated_maps
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from run_htt_planck_mes_eps_20261015 import _independent_source_mask

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"docs/research_program/observational_publication_20261015/legacy_modern_obs_integration_20261015"
SOURCE=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
OLD=STUDY/"results/observed_planck_cf4_f4_v2/result.json"
CACHE=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
SOURCE_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
CACHE_SHA="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()


def qs(values):
    return [float(x) for x in np.quantile(values,[.05,.16,.5,.84,.95])]


def run(out:Path):
    if out.exists():raise FileExistsError("create-only F4 l2+l3 extension")
    begin=time.perf_counter()
    if sha(SOURCE)!=SOURCE_SHA or sha(CACHE)!=CACHE_SHA:
        raise RuntimeError("source Planck native coefficients or FFP10 compact bytes changed")
    old=json.loads(OLD.read_text())
    assert old["schema"]=="htt.legacy-modern-real-observation-teff-F4/1"
    with np.load(SOURCE,allow_pickle=False) as f:
        names=[str(v) for v in f["names_T"]]
        actual=np.asarray(f["coeff_T"],float)
    if actual.shape!=(9,32):raise RuntimeError("same-sky Planck 9×32 source changed")
    q=moment_delta_l23(actual[:,:12])
    ref=moment_delta_l23(actual[:,:12],n_mu=24,n_phi=48)
    quadrature_residual=float(np.max(abs(q["deltaF4"]-ref["deltaF4"])))
    if quadrature_residual>2e-22:
        raise RuntimeError(f"source l2+3 exact quadrature convergence failed {quadrature_residual}")
    l2prev=np.array([old["native_planck_9_same_sky_processing"]["cases"][name]["deltaF4_quadrupole_only"]
                     for name in names])
    l2_identity_residual=float(np.max(abs(q["deltaF4_quad_only"]-l2prev)))
    if l2_identity_residual>2e-22:
        raise RuntimeError(f"extension did not reproduce original quadrupole F4 {l2_identity_residual}")

    n,X=pixel_fit_geometry(nside=64)
    with np.load(CACHE,allow_pickle=False) as c:
        mask=np.asarray(c["common_mask"],float)
        selected,files,meta=_independent_source_mask(mask)
        if selected.sum()!=26846:
            raise RuntimeError("authentic Planck source temperature mask mismatch")
        operator,operator_info=fixed_ols_operator(X,selected)
        obs=(operator@np.asarray(c["observed_map"])[selected])[4:16]
        cmb_fit=fit_rows_of_simulated_maps(c["cmb_maps"],selected,operator,count=999,chunk=20)[:,4:16]
        noise_fit=fit_rows_of_simulated_maps(c["noise_maps"],selected,operator,count=300,chunk=20)[:,4:16]
        cmb_ids=np.asarray(c["cmb_ids"],int)
        noise_ids=np.asarray(c["noise_ids"],int)
    if len(set(cmb_ids))!=999 or len(set(noise_ids))!=300:
        raise RuntimeError("FFP10 source simulation IDs must be unique")
    bc=moment_delta_l23(cmb_fit)
    bn=moment_delta_l23(noise_fit)
    bp=moment_delta_l23(cmb_fit[:300]+noise_fit)
    obs_c=moment_delta_l23(obs[None,:])
    analog_same_sky=np.array([q["deltaF4"][i] for i in range(len(names))])
    dataset={
       "schema":"htt.Planck_FFP10_exact_bandlimited_Teff_l2_l3/1",
       "date_KST":"2026-10-15",
       "claim":"ACTUAL_SOURCE_CONDITIONAL_BANDLIMITED_MOMENT_NOT_A_COSMOLOGICAL_NULL_OR_ADDITIONAL_DATA_LIKELIHOOD",
       "source_planck_temperature_coeff_sha256":SOURCE_SHA,
       "source_ffp10_source_cache_sha256":CACHE_SHA,
       "previous_legacy_quadrupole_result_sha256":sha(OLD),
       "n_actual_cosmological_skies":1,
       "n_actual_sky_processing_products":9,
       "n_cmb_only_simulations":999,
       "n_noise_only_simulations":300,
       "same_sky_processing_product_names":names,
       "selection_nside64_pix":int(selected.sum()),
       "selection_mask_sources":files,
       "bandlimited_scope":"orthonormal real ell2 five+ell3 seven, masked source OLS; ell1 and ell>=4 not measured here",
       "analytic_contract":"F4-1=6<δΘ²>+4<δΘ³>+<δΘ⁴>; full sky exact only for declared finite harmonic field",
       "quadrature_source_16x32_to_24x48_deltaF4_maxabs":quadrature_residual,
       "prior_l2_only_identity_maxabs":l2_identity_residual,
       "per_actual_same_sky_processing":{
         name:{
          "deltaF4_l2_only":float(q["deltaF4_quad_only"][i]),
          "deltaF4_l3_only":float(q["deltaF4_oct_only"][i]),
          "deltaF4_l2_l3":float(q["deltaF4"][i]),
          "deltaF4_coupling_l2_l3":float(q["deltaF4_morphology_coupling"][i]),
          "quadrupole_fraction_of_total_deltaF4":float(q["deltaF4_quad_only"][i]/q["deltaF4"][i]),
          "octupole_fraction_of_total_deltaF4":float(q["deltaF4_oct_only"][i]/q["deltaF4"][i]),
          "third_moment":float(q["cubic"][i]),
          "Tbol_bandlimited_shift_microK":float(q["Tbol_delta_microK"][i]),
         } for i,name in enumerate(names)},
       "observed_9_processing_deltaF4_l2_l3_range":[float(q["deltaF4"].min()),float(q["deltaF4"].max())],
       "observed_9_processing_l2_l3_coupling_range":[float(q["deltaF4_morphology_coupling"].min()),
                                                       float(q["deltaF4_morphology_coupling"].max())],
       "FFP10_cmb_only_deltaF4_l2_l3_quantiles":qs(bc["deltaF4"]),
       "FFP10_noise_only_deltaF4_l2_l3_quantiles":qs(bn["deltaF4"]),
       "FFP10_first300_paired_deltaF4_l2_l3_quantiles":qs(bp["deltaF4"]),
       "FFP10_cmb_only_deltaF4_morph_coupling_quantiles":qs(bc["deltaF4_morphology_coupling"]),
       "source_FFP10_observed_processed_map_deltaF4":float(obs_c["deltaF4"][0]),
       "source_cached_observed_minus_actual_SMICA_full_deltaF4":float(
           obs_c["deltaF4"][0]-q["deltaF4"][names.index("SMICA_FULL")]),
       "all_processing_products_independent":"FALSE_SAME_PHYSICAL_SKY",
       "calibrated_null_p":"NOT_ADMITTED",
       "other_probes_CF4_joint_physical_transfer":"NOT_SUPPLIED",
       "legacy_F_is_not_F4":True,
       "runtime_elapsed_seconds":time.perf_counter()-begin,
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(dataset,indent=2,ensure_ascii=False)+"\n")
    np.savez_compressed(out/"teff_bandlimited_source_arrays.npz",
        names=np.asarray(names),
        actual_delta_l2=q["deltaF4_quad_only"],
        actual_delta_l3=q["deltaF4_oct_only"],
        actual_delta_l23=q["deltaF4"],
        actual_coupling=q["deltaF4_morphology_coupling"],
        cmb_ids=cmb_ids,cmb_delta_l23=bc["deltaF4"],
        noise_ids=noise_ids,noise_delta_l23=bn["deltaF4"],
        paired_delta_l23=bp["deltaF4"])
    fig,axes=plt.subplots(1,2,figsize=(11.7,4.6),layout="constrained")
    ii=np.arange(len(names))
    axes[0].plot(ii,q["deltaF4_quad_only"]*1e9,"o-",label="legacy exact ell2 only")
    axes[0].plot(ii,q["deltaF4"]*1e9,"s-",label="extended ell2 + ell3")
    axes[0].set_xticks(ii,names,rotation=50,ha="right",fontsize=8)
    axes[0].set(ylabel="Bandlimited delta F4 [1e-9]",
                title="Same actual Planck sky, two declared harmonic models")
    axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
    axes[1].hist(bc["deltaF4"]*1e9,bins=32,density=True,
                 histtype="step",label="999 FFP10 CMB-only (conditional)")
    axes[1].hist(bp["deltaF4"]*1e9,bins=22,density=True,
                 histtype="step",label="300 CMB+noise paired")
    axes[1].axvline(q["deltaF4"][names.index("SMICA_FULL")]*1e9,
                    color="black",ls="--",label="actual SMICA_FULL")
    axes[1].set(xlabel="Source finite ell2+3 deltaF4 [1e-9]",
                ylabel="descriptive density, NOT calibrated null p",
                title="FFP10 source-matched processing under fixed model")
    axes[1].legend(fontsize=7);axes[1].grid(alpha=.2)
    fig.savefig(out/"legacy_teff_quadrupole_octupole_extension.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
       "# Legacy Teff exact O(3) source moment: quadrupole→octupole 확장\n\n"
       "기존 TeffMomentMap의 ell<=2 dipole/quadrupole finite ansatz를, 실제 Planck "
       "사중극 5개+팔중극 7개 real harmonic source field의 exact spherical fourth moment로 "
       "확장하였다. 적분은 16 Gauss–Legendre×32 azimuth nodes를 사용하고 24×48로 "
       "차수 독립 검산했다.\n\n"
       f"같은 실제 하늘 9 processing products의 deltaF4(ell2+l3) 범위="
       f"{dataset['observed_9_processing_deltaF4_l2_l3_range']}; "
       f"quadrupole-only 이전 결과 재현 residual={l2_identity_residual:.3g}; "
       f"quadrature convergence max residual={quadrature_residual:.3g}.\n\n"
       "source FFP10 CMB-only 999, noise-only 300, 첫300 같은 ID pairing 조건부 배열을 "
       "실제 Planck 공통 temperature mask 26846개의 operator로 처리했다. "
       "이것은 l>=4, 실제 intrinsic dipole, beam, foreground/cosmic physics가 빠진 "
       "정확한 유한차원 통계량이지 실제 복사장 전체의 F4 측정이나 새 확률적 likelihood가 아니다. "
       "Legacy filling F와도 구별한다.\n",encoding="utf-8")
    print("L23_REAL_SOURCE_EXACT_F4",
          "range",dataset["observed_9_processing_deltaF4_l2_l3_range"],
          "quad_ref",l2_identity_residual,
          "quadrature",quadrature_residual,
          "CMB",len(bc["deltaF4"]),
          "noise",len(bn["deltaF4"]),flush=True)
    return dataset


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    run(args.output_dir)
