#!/usr/bin/env python3
"""Actual tensorized Planck/FFP10 irrep source diagnostic and CF4 window adapter.

Original later PRs: typed anchor geometry PR254, matrix response PR255,
typefree paired tensor functionals PR262, departure tensors PR264.
This runner does NOT calculate old scalar signed x_C or call legacy
scalar F4 a tensor. Real harmonic irreps stay STF2 (5) and STF3 (7).

One actual Planck CMB sky processed in nine ways; same sky as one K1
SMICA source. FFP10 CMB 999 distinct source IDs and 300 paired
noise-only registered IDs. Empirical CMB-source covariance is not
a physical MES theorem, calibrated Planck p, shear/tilt posterior, or
CMB-CF4 joint likelihood. True kinematic tensor fields remain missing.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
from astropy import units as u
from scipy.linalg import solve_triangular

from obsstat.tensorized_lowell_source import (
  empirical_irrep_anchor,record,measured_directional_support,
  empirical_gauge_image,physical_unmeasured_tensor_image
)
from common.typefree_functionals import evaluate_paired_anchor
from obsstat.r7_cmb_product_response import real_design,real_to_stored
from obsstat.planck_lowell_irrep_projection import (
  real_harmonic_l2_to_stf,real_harmonic_l3_to_stf
)

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
OBS=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
L01=PUB/"results/L01_schur_999cmb_300noise_v2/source_lowell_nested_999plus300.npz"
CF4=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
OBS_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
CF4_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"


def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(4<<20),b""):
            h.update(block)
    return h.hexdigest()


def q5(v,labels=(.05,.16,.5,.84,.95)):
    return [float(x) for x in np.quantile(v,labels)]


def canonical_corr(c):
    # Source CMB empirical l2/3 covariance, not a physical universe
    l2=np.linalg.cholesky(c[:5,:5])
    l3=np.linalg.cholesky(c[5:,5:])
    val=solve_triangular(l2,c[:5,5:],lower=True,check_finite=False)
    val=solve_triangular(l3,val.T,lower=True,check_finite=False).T
    return np.linalg.svd(val,compute_uv=False)


def ell2_stf(src):
    q=real_harmonic_l2_to_stf(real_to_stored(np.asarray(src,float),2))
    if max(abs(q-q.T).ravel())>2e-13 or abs(np.trace(q))>2e-13:
        raise ValueError("original Planck tensor map not symmetric trace-free")
    return q


def ell3_stf(src):
    o=real_harmonic_l3_to_stf(real_to_stored(np.asarray(src,float),3))
    # Symmetric trace-free first pair/total by bridge original; standalone map checked with parity.
    if o.shape!=(3,3,3) or not np.isfinite(o).all():
        raise ValueError("source l3 STF shape drift")
    return o


def run(output:Path):
    if output.exists():raise FileExistsError("tensor-source result create-only")
    start=time.perf_counter()
    if digest(OBS)!=OBS_SHA or digest(CF4)!=CF4_SHA:
        raise RuntimeError("retained real Planck and selected CF4 sources no longer byte identical")
    with np.load(OBS,allow_pickle=False) as z:
        names=[str(x) for x in z["names_T"]]
        source9=np.asarray(z["coeff_T"][:,:12],float)
    if len(names)!=9 or len(set(names))!=9 or source9.shape!=(9,12):
        raise RuntimeError("9 Planck component-separated products of one sky required")
    with np.load(L01,allow_pickle=False) as z:
        actual5=np.asarray(z["observed_l5"][:,4:16],float)
        actual12=np.asarray(z["observed_l12"][:,4:16],float)
        sim5=np.asarray(z["cmb_l5_36"][:,4:16],float)
        sim12=np.asarray(z["cmb_l12_36"][:,4:16],float)
        ids=np.asarray(z["cmb_ids"])
        noiseids=np.asarray(z["noise_ids"])
        noise=np.asarray(z["noise_l5_36"][:,4:16],float)
    if (actual5.shape!=(1,12) or actual12.shape!=(1,12)
        or sim5.shape!=(999,12) or sim12.shape!=(999,12)
        or noise.shape!=(300,12) or len(set(ids.tolist()))!=999
        or not np.array_equal(ids[:300],noiseids)):
        raise RuntimeError("source-complete unique simulation and paired 300 noise IDs")
    # K1 SMICA and retained nine products are both source-processed outputs
    # of the same sky, but their byte-level low-l estimates need not coincide.
    K1_obs=actual5[0]
    actual_map_match=float(np.linalg.norm(
       K1_obs-source9[names.index("SMICA_FULL")]))
    source_cov=np.cov(sim5,rowvar=False)
    source_cov=(source_cov+source_cov.T)/2
    rho=canonical_corr(source_cov)
    if max(rho)>1+1e-11:
        raise RuntimeError("CMB source band canonical covariance violates correlation bound")

    axes=np.eye(3)
    look=np.concatenate((axes,-axes),axis=0)
    Y=real_design(look,ell_max=3)[:,4:16]
    outchannels={}
    actual_gauges={}
    src_array={}
    for ell,seg in ((2,slice(0,5)),(3,slice(5,12))):
        b=empirical_irrep_anchor(sim5[:,seg],ell=ell,source_hash=digest(L01))
        obsrec=record(b,f"one-observed-SMICA-K1-ell{ell}",K1_obs[seg])
        gauge=evaluate_paired_anchor(obsrec)
        if gauge.status!="DEFINED":
            raise RuntimeError("typed PR262 source ellipsoid missing")
        e=empirical_gauge_image(b,sim5[:,seg],ids,thresholds=(1.,2.,3.))
        unmeasured=physical_unmeasured_tensor_image(b,ids)
        Faxes=[measured_directional_support(b,K1_obs[seg],u)
               for u in Y[:,seg]]
        F=np.asarray([z["F_directional_support_ratio"] for z in Faxes])
        if ell==2:
            if np.max(abs(F[:3]-F[3:]))>3e-13:
                raise RuntimeError("even STF2 directional support parity failed")
        else:
            if np.max(abs(F[:3]+F[3:]))>3e-13:
                raise RuntimeError("odd STF3 directional support parity failed")
        # Actual source 999 on SAME ID (mask/fit lmax5 versus lmax12)
        # tensorized G_F path is a MASK/FIT diagnostic, NOT a physical
        # redshift-depth transfer or legacy scalar G_F.
        v5=sim5[:,seg]-b.source_mean
        v12=sim12[:,seg]-b.source_mean
        source_gauge12=np.sqrt(np.einsum("ni,ij,nj->n",v12,b.invcovariance,
                                        v12,optimize=True))
        gauge5=e["gauge"]
        delta=source_gauge12-gauge5
        qo=np.asarray([evaluate_paired_anchor(
          record(b,f"actual-processing-{name}",r[seg])).gauge
          for name,r in zip(names,source9,strict=True)])
        current={
          "irrep":"STF2_even" if ell==2 else "STF3_odd",
          "tensor_rank":ell,
          "harmonic_coordinate_dimension":2*ell+1,
          "empirical_covariance_eigenvalues_microK2":b.eigvals.tolist(),
          "condition_number":float(b.eigvals[-1]/b.eigvals[0]),
          "source_CMB_mean_microK":b.source_mean.tolist(),
          "source_empirical_Q_gauge_quantiles":q5(gauge5),
          "one_actual_sky_K1_Q_gauge":float(gauge.gauge),
          "actual_nine_processing_Q_gauges_dependent":dict(zip(names,qo.tolist())),
          "empirical_simulation_strict_Q_tails_NOT_P":e["tail"],
          "actual_one_sky_F_directional_profile_xyz_plus_minus":F.tolist(),
          "actual_F_plus_minus_parity_convention":"even" if ell==2 else "odd",
          "empirical_mask_fit_path_delta_Q_ellmax12_minus5_quantiles":q5(delta),
          "empirical_mask_fit_path_delta_Q_RMS":float(np.sqrt(np.mean(delta**2))),
          "actual_one_sky_mask_fit_path_delta_Q":float(
              np.sqrt((actual12[0,seg]-b.source_mean)@b.invcovariance@
                      (actual12[0,seg]-b.source_mean))-gauge.gauge),
          "physical_inferred_irrep":unmeasured,
          "CMB_to_physical_shear_MES_anchor":"NOT_CONSTRUCTED",
        }
        outchannels[str(ell)]=current
        src_array[str(ell)]={"source_gauge5":gauge5,
                              "source_gauge12":source_gauge12,
                              "sim_delta":delta}
        actual_gauges[str(ell)]=gauge.gauge

    # Independent direct STF tensor and original harmonic reconstruction
    q=ell2_stf(K1_obs[:5])
    octu=ell3_stf(K1_obs[5:])
    truth=Y@K1_obs
    model=np.einsum("ni,ij,nj->n",look,q,look,optimize=True)+np.einsum(
        "ni,nj,nk,ijk->n",look,look,look,octu,optimize=True)
    err=float(max(abs(model-truth)))
    if err>4e-12:raise RuntimeError("original tensor bridge not equivalent to real harmonics")

    # Correct ICRS CF4 -> Galactic Planck source angular operator; no
    # product of CMB and CF4 likelihoods, no GR sigma field inference.
    with np.load(CF4,allow_pickle=False) as z:
        n=np.asarray(z["n_J2000"],float)
        redshift=np.asarray(z["z_CMB"],float)
        groupid=np.asarray(z["group_id"],np.int64)
    if len(n)!=35970 or len(set(groupid.tolist()))!=len(n):
        raise RuntimeError("CF4 exact grouped 35970 source IDs")
    coord=SkyCoord(x=n[:,0]*u.one,y=n[:,1]*u.one,z=n[:,2]*u.one,
                   representation_type="cartesian",frame="icrs")
    gal=np.asarray(coord.galactic.cartesian.xyz.value).T
    desc=real_design(gal,ell_max=3)[:,4:16]
    fullP=desc.mean(axis=0)
    expval=fullP@K1_obs
    shells=[]
    for lo,hi in ((.01,.03),(.03,.05),(.05,.075),(.075,.10)):
        sel=(redshift>=lo)&(redshift<hi)
        v=desc[sel].mean(axis=0)
        shells.append({
          "z_lo":lo,"z_hi":hi,"CF4_actual_source_count":int(sel.sum()),
          "CF4_sky_window_even_STF2_source_temperature_mean_microK":
               float(v[:5]@K1_obs[:5]),
          "CF4_sky_window_odd_STF3_source_temperature_mean_microK":
               float(v[5:]@K1_obs[5:]),
          "combined_apparent_temperature_angular_mean_microK":float(v@K1_obs),
          "linear_source_window_12D":v.tolist(),
          "physical_cross_catalogue_posterior":"NOT_CONSTRUCTED",
        })
    if sum(s["CF4_actual_source_count"] for s in shells)!=35970:
        raise RuntimeError("real CF4 source shell partition drift")
    if abs(sum(s["CF4_actual_source_count"]*s[
        "combined_apparent_temperature_angular_mean_microK"]
        for s in shells)/35970-expval)>1e-13:
        raise RuntimeError("same source CF4 window angular mean mismatch")
    result={
       "schema":"htt.PR254_255_262_tensorized_Planck_CMB_FFP10_CF4_source_anchored/1",
       "date_KST":"2026-10-15",
       "physical_claim_tier":"EMPIRICAL_TENSOR_IRREP_ANCHOR_AND_SOURCE_CATALOGUE_WINDOW_NO_BIANCHI_LIKELIHOOD",
       "authoritative_later_method_prs":[254,255,256,257,258,262,264],
       "source_Planck_nine_products_sha256":OBS_SHA,
       "source_CF4_selected_groups_sha256":CF4_SHA,
       "source_actual_masked_CMB_999_300_npz_sha256":digest(L01),
       "physical_real_CMB_sky_count":1,
       "dependent_Planck_processing_products":names,
       "FFP10_unique_CMB_source_realizations":999,
       "FFP10_noise_same_ID_pairs":300,
       "CMB_signal_masked_ell2_5_and_ell3_7":"REAL_ORTHONORMAL_YLM_GALACTIC_THERMODYNAMIC_MICROK",
       "same_sky_retained_SMICA_FULL_minus_K1_source_12D_norm_microK":actual_map_match,
       "empirical_12D_source_band_cross_covariance_canonical_corr":rho.tolist(),
       "source_ell2_ell3_covariance_offblock_frobenius_relative":
           float(np.linalg.norm(source_cov[:5,5:],"fro")/
                 np.sqrt(np.linalg.norm(source_cov[:5,:5],"fro")*
                         np.linalg.norm(source_cov[5:,5:],"fro"))),
       "irrep_typed_anchors":outchannels,
       "actual_CMB_temperature_quadrupole_STF2_microK":q.tolist(),
       "actual_octupole_rank3_STF_tensor_microK":octu.tolist(),
       "STF_tensor_vs_real_harmonic_explicit_six_directions_maxabs_microK":err,
       "actual_CF4_35970_look_window_on_Planck_temperature_irreps":{
          "CF4_catalogue_is_an_independent_physical_sky":False,
          "CF4_source_actual_group_count":35970,
          "observed_Planck_lowell_one_sky_on_CF4_sightlines_microK":float(expval),
          "redshift_shells":shells,
          "cross_observation_joint_physical_likelihood":"NOT_CONSTRUCTED",
        },
       "tensorized_source_F_directional_not_legacy_filling_fraction":True,
       "tensorized_source_Q_anchor_gauge_not_legacy_signed_scalar_Q":True,
       "tensorized_source_Pi_empirical_exceedance_not_planck_null_p":True,
       "tensorized_source_GF_fit_mask_path_not_observed_depth_G_F":True,
       "physical_kinematic_state_sigma_omega_A_beta":"NOT_IDENTIFIED",
       "no_physical_tilt_or_Bianchi_mode_inference":True,
       "runtime_seconds":time.perf_counter()-start
    }
    output.mkdir(parents=True)
    (output/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    np.savez_compressed(output/"tensorized_source_ffp999.npz",
        cmb_ids=ids,noise_ids=noiseids,
        source_observed_l5_real12=actual5,
        source_observed_l12_real12=actual12,
        source_999_l5_real12=sim5,source_999_l12_real12=sim12,
        cov12=source_cov,
        gauge2_l5=src_array["2"]["source_gauge5"],
        gauge3_l5=src_array["3"]["source_gauge5"],
        gauge2_l12=src_array["2"]["source_gauge12"],
        gauge3_l12=src_array["3"]["source_gauge12"])
    fig,ax=plt.subplots(1,2,figsize=(12,4.4),layout="constrained")
    for i,ell in enumerate(("2","3")):
        values=src_array[ell]["source_gauge5"]
        ax[i].hist(values,bins=48,density=True,histtype="step",
                   label="999 FFP10 CMB empirical STF gauge")
        ax[i].axvline(actual_gauges[ell],color="black",ls="--",
                      label="one observed K1 SMICA STF gauge")
        ax[i].set(xlabel=f"STF rank {ell} source-covariance gauge, not MES",
                  ylabel="empirical source sample density",
                  title=f"Source tensor gauge / ell {ell}, no physical p")
        ax[i].legend(fontsize=7);ax[i].grid(alpha=.2)
    fig.savefig(output/"tensorized_planck_stf_empirical_source.png",dpi=145)
    plt.close(fig)
    (output/"REPORT_KO.md").write_text(
     "# Tensorized Planck STF2/STF3와 FFP10 999 source anchor\n\n"
     "PR254/255/262/264 typed tensor 방법론을 실제 thermodynamic T irreps에 적용. "
     "l2 five and l3 seven are independent typed tensor channels, and source "
     "CMB 999 unique simulations define descriptive empirical covariance bodies, "
     "NOT physical MES or calibrated sky noise covariance. "
     f"Source STF2 Q gauge={actual_gauges['2']:.6g}, STF3={actual_gauges['3']:.6g}. "
     f"Masked l2-l3 cross canonical correlations={rho.tolist()}. "
     f"Actual K1 vs separately registered SMICA_FULL retained 12D difference="
     f"{actual_map_match:.7g} microK, which is one sky under distinct processing. "
     "Directional F(n), paired mask/fit G_F-like path and sample empirical Pi are "
     "NOT physical anisotropy probabilities or legacy signed x_C. "
     "CF4 35970 real group directions rotated to Galactic give a deterministic "
     "angular observation window on same Planck sky, not a joint likelihood. "
     "Physical sigma/omega/A/tilt remains 100 percent unknown.\n",encoding="utf-8")
    print("TENSOR_SOURCE_999_DONE",
          "gauge2",actual_gauges["2"],"gauge3",actual_gauges["3"],
          "canon_corr",rho.tolist(),
          "CF4_avg",float(expval),
          "tensor_harmonic_error",err,flush=True)
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,required=True)
    a=parser.parse_args()
    run(a.output_dir)
