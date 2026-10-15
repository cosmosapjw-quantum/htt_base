#!/usr/bin/env python3
"""Local observer finite CMB boost from real Planck l2+l3, plus CF4 window geometry.

This is a counterfactual event-local observer boost on source-processed
temperature harmonic coefficients that have already had their actual
kinematic dipole removed. It is NOT a physical "correction" of Planck
data or an inference of material/radiation tilt.

Three source lanes:
  - Legacy Teff directional blackbody source and modern 1+3 finite Lorentz;
  - Actual Planck PR3 one-sky nine processed l2/l3 real coefficients and mask;
  - Actual CF4 35970-group published J2000 depth-window angular response.
A common dipole direction may be expressed in both Galactic and ICRS, but
the CF4 z_CMB has already been corrected for local observer velocity.
No double correction is performed or presented as a physical effect.
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

from astropy.coordinates import SkyCoord
from astropy import units as u

from obsstat.finite_boost_observer_frame import (
 C_KM_S,boosted_sky_temperature,frame_triad,
 galactic_dipole_unit_vector,legacy_rapidity_and_velocity_fraction,
 gamma_beta,one_event_frame_rank,kinematic_monopole_f4
)
from obsstat.r7_cmb_product_response import (
    real_design,pixel_fit_geometry,real_to_stored
)
from obsstat.planck_lowell_irrep_projection import real_harmonic_l2_to_stf
from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition
from obsstat.mes_eps_measurement_bridge import (
    fixed_ols_operator,T0_MICROK
)
from run_htt_planck_mes_eps_20261015 import (
    _independent_source_mask,CACHE
)

ROOT=Path(__file__).resolve().parents[1]
PLANCK=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
HUBBLE=ROOT/"docs/research_program/observational_publication_20261015/results/H01_actual_cf4_v1/result.json"
PLANCK_SOURCE_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
CACHE_SHA="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
DIPOLE_SOURCE={
    "amplitude_microK":3362.08,
    "galactic_longitude_deg":264.021,
    "galactic_latitude_deg":48.253,
    "source":"Planck 2018 I, Solar dipole table 2, 2020 A&A 641 A1",
    "doi":"10.1051/0004-6361/201833880",
    "amplitude_is_first_order_velocity_reference":True
}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(8<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def response_of_one(coeff_source,sky,source_look,operator,D,dipole_coeff):
    # These actual saved harmonics are map-processed temperature fluctuations
    # in microK, NOT a physical cosmic-radiation rest-frame field.
    delta0=real_design(sky,ell_max=3)[:,4:16]@coeff_source
    deltaR=real_design(source_look,ell_max=3)[:,4:16]@coeff_source
    deltaBoost=D*deltaR
    low0=operator@delta0
    lowO=operator@deltaBoost
    # Monopole-generated kinetic terms are separately admitted counterfactuals.
    full=lowO+dipole_coeff
    if abs(np.max(np.abs(full-lowO-dipole_coeff)))>1e-8:
        raise RuntimeError("linear projected source/monopole boosted identity")
    real_quad=real_harmonic_l2_to_stf(real_to_stored(lowO[4:9],2))
    fiducial_quad=real_harmonic_l2_to_stf(real_to_stored(low0[4:9],2))
    shape0=quartic_power_shape_decomposition(low0[4:16][None,:])
    shapeO=quartic_power_shape_decomposition(lowO[4:16][None,:])
    return {
      "source_baseline_ell2_5_real_microK":low0[4:16].tolist(),
      "boosted_source_ell2_5_real_microK":lowO[4:16].tolist(),
      "boosted_source_with_kinetic_monopole_ell2_5_real_microK":full[4:16].tolist(),
      "l2_source_delta_norm_microK":float(np.linalg.norm(lowO[4:9]-low0[4:9])),
      "l3_source_delta_norm_microK":float(np.linalg.norm(lowO[9:16]-low0[9:16])),
      "l2_kinetic_monopole_norm_microK":float(np.linalg.norm(dipole_coeff[4:9])),
      "l2_source_stf_change_norm_microK":float(np.linalg.norm(real_quad-fiducial_quad)),
      "baseline_legacy_f4_l2l3_source_conditional":float(shape0["deltaF4"][0]),
      "boosted_legacy_f4_l2l3_source_conditional":float(shapeO["deltaF4"][0]),
      "baseline_morphology_s3":float(shape0["normalized_skewness"][0]),
      "boosted_morphology_s3":float(shapeO["normalized_skewness"][0]),
      "baseline_morphology_k4":float(shape0["normalized_kurtosis"][0]),
      "boosted_morphology_k4":float(shapeO["normalized_kurtosis"][0])
    }


def run(out:Path):
    if out.exists():
        raise FileExistsError("immutable create-only scientific source result")
    if digest(PLANCK)!=PLANCK_SOURCE_SHA or digest(CACHE)!=CACHE_SHA:
        raise RuntimeError("Planck source coefficient or prior K1 cache identity drift")
    with np.load(PLANCK,allow_pickle=False) as f:
        names=[str(z) for z in f["names_T"]]
        samples=np.asarray(f["coeff_T"][:,:12],float)
    if len(names)!=9 or samples.shape!=(9,12):
        raise RuntimeError("nine processed Planck products from ONE sky required")
    nside64sky,design=pixel_fit_geometry(nside=64)
    with np.load(CACHE,allow_pickle=False) as f:
        selected,masks,maskmeta=_independent_source_mask(np.asarray(f["common_mask"],float))
    if selected.sum()!=26846:
        raise RuntimeError("actual native Planck temperature source mask identity")
    sky=np.asarray(nside64sky[selected],float)
    R,source_info=fixed_ols_operator(design,selected)
    axis=galactic_dipole_unit_vector(
        DIPOLE_SOURCE["galactic_longitude_deg"],
        DIPOLE_SOURCE["galactic_latitude_deg"]
    )
    # amplitude/T0 is a declared first-order numerical velocity reference,
    # not an inverse fitted velocity with higher-order & dipole foregrounds.
    beta_speed=DIPOLE_SOURCE["amplitude_microK"]/T0_MICROK
    beta_or=axis*beta_speed
    # Radiation frame R at rest in local source chart, observer O moving beta.
    triad=frame_triad([0.,0.,0.],[0.,0.,0.],beta_or)
    therm=lambda s:np.full(s.shape[:-1],T0_MICROK)
    Tkin,source_look,D=boosted_sky_temperature(sky,beta_or,therm)
    boost_kin=R@(Tkin-T0_MICROK)
    source_no_boost=R@np.zeros(len(sky))
    if np.max(abs(source_no_boost))!=0:
        raise RuntimeError("zero normal-frame monopole subtraction")
    fitted_dipole=np.linalg.norm(
        # Direction sign follows unit sky LOOK not photon propagation.
        np.array([
            -boost_kin[2],-boost_kin[3],boost_kin[1]
        ])*np.sqrt(3/(4*np.pi))
    )
    # Exact projected dipole coefficient returns d vector with harmonic
    # l1 basis convention; isotropic source should point towards hot Galactic axis.
    from obsstat.legacy_teff_tensor_observation_bridge import real_l1_microK_to_temperature_dipole
    dipvector=real_l1_microK_to_temperature_dipole(boost_kin[1:4])*T0_MICROK
    dipole_direction_cos=float(np.dot(dipvector,axis)/np.linalg.norm(dipvector))
    if dipole_direction_cos<1-1e-7 or abs(np.linalg.norm(dipvector)-DIPOLE_SOURCE["amplitude_microK"])>.02:
        raise RuntimeError("source Galactic boost and observed Planck Solar dipole mismatch")
    # Finite monopole creates a *kinematic quadrupole* of O(beta^2).
    kin_stf=real_harmonic_l2_to_stf(real_to_stored(boost_kin[4:9],2))
    predicted=T0_MICROK*beta_speed**2 * (np.outer(axis,axis)-np.eye(3)/3)
    quad_discrepancy=float(np.max(abs(kin_stf-predicted)))
    if quad_discrepancy>2e-4:
        raise RuntimeError(f"boosted blackbody kinematic quadrupole oracle: {quad_discrepancy}")
    by={}
    for name,coeff in zip(names,samples):
        by[name]=response_of_one(coeff,sky,source_look,R,D,boost_kin)
        # Finite l2+l3-only baseline must reproduce saved input modes exactly.
        e=np.max(abs(np.asarray(by[name]["source_baseline_ell2_5_real_microK"])-coeff))
        if e>2e-10:
            raise RuntimeError(f"source real harmonic frame drift in {name}: {e}")
    # Relative 3-frame kinematics: M=N, R=N, O boosted.
    if np.linalg.norm(triad["beta_RO_R_in_observer_O_tetrad"]+beta_or)>2e-15:
        raise RuntimeError("matter-radiation frame sign contract drift")
    if np.linalg.norm(triad["beta_RM_R_in_matter_M_tetrad"])>2e-15:
        raise RuntimeError("matter-radiation reference frame was not co-moving")
    # CF4 published source window axes are J2000/ICRS, NOT Planck Galactic.
    # Counterfactual forward response only: redshift z_CMB already corrected.
    hubble=json.loads(HUBBLE.read_text())
    if hubble["source_groups"]!=35970:
        raise RuntimeError("CF4 selected real source grouping changed")
    gal=SkyCoord(l=DIPOLE_SOURCE["galactic_longitude_deg"]*u.deg,
                 b=DIPOLE_SOURCE["galactic_latitude_deg"]*u.deg,
                 frame="galactic")
    axis_icrs=np.asarray(gal.icrs.cartesian.xyz.value,float)
    velocity_j2000=axis_icrs*C_KM_S*beta_speed
    window=np.asarray(hubble["fit"]["bulk_response_per_km_s"],float)
    if window.shape!=(7,3):
        raise RuntimeError("CF4 registered 7 window response shape changed")
    counterfactual=window@velocity_j2000
    rank=one_event_frame_rank([0.,0.,0.],beta_or,step=1e-6)
    result={
      "schema":"htt.P4_one_event_finite_boost_and_source_planck_cf4_response/1",
      "date_KST":"2026-10-15",
      "physical_claim":"EVENT_LOCAL_OBSERVER_BOOST_AND_CONDITIONAL_SAME_SOURCE_PIPELINE_ONLY_NOT_GLOBAL_TILT",
      "Planck_temp_input_sha256":PLANCK_SOURCE_SHA,
      "Planck_K1_source_sha256":CACHE_SHA,
      "CF4_working_law_report_sha256":digest(HUBBLE),
      "one_actual_CMB_sky_with_processing_products":9,
      "SMICA_cartesian_frame":"GALACTIC look-sky vectors; incoming photon direction is OPPOSITE",
      "CF4_cartesian_frame":"ICRS J2000; converted by Astropy SkyCoord Gal->ICRS",
      "mean_temperature_T0_microK":T0_MICROK,
      "local_dipole_parameter_source":DIPOLE_SOURCE,
      "counterfactual_beta_OR_velocity_fraction":beta_speed,
      "exact_legacy_F4_of_local_boosted_pure_monopole":
         kinematic_monopole_f4(beta_or),
      "counterfactual_v_orbital_km_s":C_KM_S*beta_speed,
      "source_reference_velocity_direction_galactic":axis.tolist(),
      "source_reference_velocity_direction_ICRS":axis_icrs.tolist(),
      "observed_lowell_source_status":"Already observed/dipole-subtracted; reinterpreted as hypothetical radiation-rest l2+l3-only source, NOT physical deboost",
      "frame_triad_source_contract":{
        k:(v.tolist() if isinstance(v,np.ndarray) else v)
        for k,v in triad.items()},
      "rapidity_v_fraction":legacy_rapidity_and_velocity_fraction(beta_or),
      "source_support_T_nside64_selected":int(selected.sum()),
      "source_mask_identity":masks,
      "source_harmonic_fit_info":source_info,
      "finite_kinematic_monopole_to_observer":{
         "projected_l0_microK":float(boost_kin[0]),
         "projected_l1_real_microK":boost_kin[1:4].tolist(),
         "projected_dipole_norm_microK":float(np.linalg.norm(dipvector)),
         "dipole_axis_dot_source_Galactic":dipole_direction_cos,
         "projected_l2_real_microK":boost_kin[4:9].tolist(),
         "projected_l2_real_norm_microK":float(np.linalg.norm(boost_kin[4:9])),
         "projected_l2_STF_microK":kin_stf.tolist(),
         "analytic_l2_STF_muK":predicted.tolist(),
         "analytic_l2_STF_maxabs_residual_microK":quad_discrepancy,
      },
      "actual_same_sky_source_processing_by_product":by,
      "CF4_J2000_hypothetical_observer_bulk_projection":{
         "source_CF4_group_count":35970,
         "predeclared_windows":hubble["predeclared_windows"],
         "hypothetical_J2000_bulk_velocity_km_s":velocity_j2000.tolist(),
         "delta_logH_by_window_if_false_uncorrected_observer_velocity":counterfactual.tolist(),
         "semantic_status":"COUNTERFACTUAL_ONLY_CF4_Z_CMB_ALREADY_HAS_OBSERVER_VELOCITY_CORRECTION_NO_DOUBLE_APPLICATION",
      },
      "one_event_local_global_velocity_identifiability":{
         k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in rank.items()},
      "global_tilt_history_source_response":"ABSENT_NOT_SUBSTITUTED_BY_ENDPOINT_OBSERVER_BOOST",
      "CMB_instrument_noise_beam_high_l_observation_likelihood":"NOT_CONSTRUCTED",
      "CF4_physical_velocity_selection_likelihood":"NOT_CONSTRUCTED",
      "CMB_plus_CF4_joint_posterior":"NOT_CONSTRUCTED",
      "manuscript_ready":"NO",
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    labels=list(by)
    l2=np.array([by[k]["l2_source_delta_norm_microK"] for k in labels])
    l3=np.array([by[k]["l3_source_delta_norm_microK"] for k in labels])
    fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout="constrained")
    axes[0].plot(range(len(labels)),l2,"o-",label="l2 source aberration/modulation")
    axes[0].plot(range(len(labels)),l3,"s-",label="l3 source aberration/modulation")
    axes[0].axhline(float(np.linalg.norm(boost_kin[4:9])),color="black",ls=":",
                    label="pure monopole's kinematic l2, not observational shear")
    axes[0].set_xticks(range(len(labels)),labels,rotation=55,ha="right",fontsize=7)
    axes[0].set(ylabel="Finite boosted minus unboosted l=2/3 real coefficients [microK]",
                title="One Planck sky, nine processing schemes")
    axes[0].legend(fontsize=7);axes[0].grid(alpha=.2)
    axes[1].plot(range(len(counterfactual)),counterfactual,marker="o")
    axes[1].set_xticks(range(len(counterfactual)),
                       [x["id"] for x in hubble["predeclared_windows"]],
                       rotation=55,ha="right",fontsize=7)
    axes[1].axhline(0,color="black",ls=":")
    axes[1].set(xlabel="Original CF4 working-law windows (not an actual velocity correction)",
                ylabel="Hypothetical observer-like bulk contribution to logH",
                title="Galactic Planck axis translated to ICRS CF4: counterfactual only")
    axes[1].grid(alpha=.2)
    fig.savefig(out/"planck_finite_boost_and_cf4_counterfactual.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
       "# P4 V01: 정확한 국소 Lorentz frame bridge와 실제 Planck/CF4 소스 주입\n\n"
       "Frame beta_AB는 '관측자 B에서 본 프레임 A'의 3-velocity fraction이다. "
       "복사 R, 물질 M, 관측자 O 세 congruence/orthonormal tetrad의 event-local "
       "Lorentz map이 수학적으로 유효함을 확인했다. "
       f"Planck dipole first-order reference beta={beta_speed:.10g}, "
       f"v={C_KM_S*beta_speed:.7g} km/s, source axis Galactic "
       "(264.021°,48.253°).\n\n"
       f"Monopole blackbody T0 boost의 l1 dipole norm="
       f"{np.linalg.norm(dipvector):.7g} microK; l2 STF analytic "
       f"residual={quad_discrepancy:.6g} microK.\n\n"
       f"실제 source SMICA_FULL l2/l3 곱하고 angular aberration한 뒤 "
       f"l2 finite-source coefficient 변화 norm="
       f"{by['SMICA_FULL']['l2_source_delta_norm_microK']:.8g} microK, "
       f"l3={by['SMICA_FULL']['l3_source_delta_norm_microK']:.8g} microK.\n\n"
       "이것은 실제 Planck 소스 관측의 'boost correction'이 아니다: "
       "원래 processing에는 solar dipole가 제거되어 있고 여기서는 임의 l2+l3 "
       "관측 계수를 가정된 radiation-rest 소스로 다시 주입한 counterfactual이다. "
       "CF4 z_CMB도 기초 관측자의 속도 보정이 이미 적용되었으므로 "
       "위 observer velocity의 angular source projection은 중복 적용 불가능한 "
       "조건부 survey-window response check로만 보존했다. "
       "global tilted Bianchi emission/opacity history 및 source covariance 부재, "
       "physical beta_RM posterior나 rho와 beta 혼동 허용 불가.\n",encoding="utf-8")
    print("FINITE_BOOST_ACTUAL_PLANCK_CF4_RESULT",
          "beta",beta_speed,
          "dipole",np.linalg.norm(dipvector),
          "quad_norm",np.linalg.norm(boost_kin[4:9]),
          "quad_tensor_err",quad_discrepancy,
          "SMICA_ell2",by["SMICA_FULL"]["l2_source_delta_norm_microK"],
          "SMICA_ell3",by["SMICA_FULL"]["l3_source_delta_norm_microK"],
          "CF4logH",counterfactual[:4].tolist(),flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    run(a.output_dir)
