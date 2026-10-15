#!/usr/bin/env python3
"""Actual 35,970 CF4 directions audit of exact 1+3 one-event optical operator.

Three distinct source lanes, never multiplied into a fake likelihood:
(1) Legacy/modern registered 1+3 shear-omega-A-beta decomposition and
    exact null-geodesic energy drift;
(2) observed CF4 selected 35,970 J2000 look directions and redshift windows;
(3) actual same one Planck Galactic CMB sky, nine l2 harmonic processing
    alternatives, mapped to CF4 sky only as an ANGULAR representation check.

All physical kinematic amplitudes injected here are manufactured.
No inference of real covariant sigma, omega, four acceleration or tilt.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
from astropy import units as u

from obsstat.covariant_optical_kinematics import (
    unit_sky,angular_rank,optical_design,optical_rate,
    sigma_over_H,acceleration_vs_boost_dipole_span,euclidean_jet_limit
)
from obsstat.htt_kinematic_radial_identification import (
    antisymmetric_basis,MPC_KM
)
from obsstat.cf4_apparent_kinematic_distribution import stf2_orthonormal
from obsstat.legacy_teff_tensor_observation_bridge import (
    masked_planck_quadrupole_to_temperature_stf,T0_MICROK
)

ROOT=Path(__file__).resolve().parents[1]
CF4=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
PLANCK=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
H01=ROOT/"docs/research_program/observational_publication_20261015/results/H01_actual_cf4_v1/result.json"
OLD_K01=ROOT/"docs/research_program/observational_publication_20261015/results/K01_actual_cf4_radial_oracle_v1/result.json"
CF4_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
PLANCK_SHA="900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"


def digest(file):
    h=hashlib.sha256()
    with file.open("rb") as src:
        for block in iter(lambda:src.read(4<<20),b""):h.update(block)
    return h.hexdigest()


def ndarray(obj):
    if isinstance(obj,np.ndarray):return obj.tolist()
    if isinstance(obj,np.generic):return obj.item()
    if isinstance(obj,dict):return {k:ndarray(v) for k,v in obj.items()}
    return obj


def window_moments(n,which):
    """Moment of REAL source galaxy LOOK sky geometry, not physical CF4 rates."""
    x=n[which]
    if len(x)<50:raise RuntimeError("insufficient actual source angular shell")
    m=x.mean(axis=0)
    second=x.T@x/len(x)
    stf=second-np.eye(3)/3
    return {
       "source_N":len(x),
       "sky_look_dipole_mean_J2000":m.tolist(),
       "sky_look_dipole_norm":float(np.linalg.norm(m)),
       "sky_look_second_moment_eig":np.linalg.eigvalsh(second).tolist(),
       "sky_look_STF_window_norm":float(np.linalg.norm(stf)),
       "raw_second_moment_J2000":second.tolist(),
       "mean_n":m,"STF_second_moment":stf,
    }


def run(out:Path):
    if out.exists():raise FileExistsError("create-only exact 1+3 source-study result")
    if digest(CF4)!=CF4_SHA or digest(PLANCK)!=PLANCK_SHA:
        raise RuntimeError("the source CF4/Planck compact exact SHA identity changed")
    with np.load(CF4,allow_pickle=False) as src:
        n=unit_sky(src["n_J2000"])
        z=np.asarray(src["z_CMB"],float)
        groupid=np.asarray(src["group_id"],int)
        method=np.asarray(src["method_family"])
    if len(n)!=35970 or len(set(groupid.tolist()))!=len(n):
        raise RuntimeError("actual 35,970 CF4 groups unique and source-correct")
    old=json.loads(OLD_K01.read_text())
    if old["source_npz_sha256"]!=CF4_SHA or old["STF5_rank"]!=5:
        raise RuntimeError("actual previous Euclidean source angular null reference drift")
    geometry=angular_rank(n)
    if geometry["rank_H_A3_sigma5"]!=9 or geometry["rank_omega3"]!=0:
        raise RuntimeError("one-event 9D physical angular design lost rank")
    past=np.asarray(old["STF5_singular_values"],float)
    stf=optical_design(n)[:,4:9]
    sv=np.linalg.svd(stf,compute_uv=False)
    if np.max(abs(sv-past))>1e-11:
        raise RuntimeError("actual source STF5 angular basis differs from previous K01")
    overlap=acceleration_vs_boost_dipole_span(n)
    assert overlap["rank"]==3
    # Manufactured physical congruence rates for 1+3 injection: not fitted!
    h=74.6/MPC_KM
    a=np.array([2.,-4.,1.])/MPC_KM
    sig5=np.array([1.,-2.,3.,.5,-1.])/MPC_KM
    sigma=np.einsum("k,kij->ij",sig5,stf2_orthonormal(),optimize=True)
    omega=np.einsum("k,kij->ij",np.array([5.,-7.,9.])/MPC_KM,
                    antisymmetric_basis(),optimize=True)
    actual_y=optical_rate(n,theta_s_inv=3*h,sigma_s_inv=sigma,
                         omega_s_inv=omega,accel_s_inv=a)
    pure=optical_rate(n,theta_s_inv=3*h,sigma_s_inv=sigma,
                      omega_s_inv=np.zeros((3,3)),accel_s_inv=a)
    omega_insensitivity=float(np.max(abs(actual_y["negative_dlnE_dt_u_s_inv"]-
                                       pure["negative_dlnE_dt_u_s_inv"])))
    X=optical_design(n)
    y=X[:,:9]@np.r_[h,a,sig5]
    rerr=float(np.max(abs(y-actual_y["negative_dlnE_dt_u_s_inv"])))
    recovered=np.linalg.lstsq(X[:,:9],actual_y["negative_dlnE_dt_u_s_inv"]*MPC_KM,
                              rcond=None)[0]
    coeff_original=np.r_[h,a,sig5]*MPC_KM
    recovered_err=float(np.max(abs(recovered-coeff_original)))
    if recovered_err>1e-10 or rerr>2e-32 or omega_insensitivity>5e-32:
        raise RuntimeError(f"physical 1+3 synthetic sky injection failed {recovered_err}")
    # One-event physical photon energy drift angular H+sigma is the same
    # pure angular gradient contraction as local Euclidean jet, not real H_eff.
    G=np.array([[80.,4.,7.],[1.,90.,-3.],[-4.,5.,70.]])
    comparator=euclidean_jet_limit(n,G)
    # Real CF4 depth and selection geometry, not optical rate measurements.
    shells=((.01,.03),(.03,.05),(.05,.075),(.075,.1))
    groups=[]
    for lo,hi in shells:
        keep=(z>=lo)&(z<hi)
        w=window_moments(n,keep)
        groups.append({
            "z_lo":lo,"z_hi":hi,
            "source_count":w["source_N"],
            "mean_n_J2000":w["sky_look_dipole_mean_J2000"],
            "mean_n_norm":w["sky_look_dipole_norm"],
            "STF_selection_norm":w["sky_look_STF_window_norm"],
            "second_moment_eigenvalues":w["sky_look_second_moment_eig"],
            "synthetic_rate_mono_H_scaled":float(
                 np.mean(actual_y["negative_dlnE_dt_u_s_inv"][keep])/h),
            "synthetic_A_dipole_shift_over_H":float(
                 (-w["mean_n"]@a)/h),
            "synthetic_sigma_quadrupole_shift_over_H":float(
                 np.sum(sigma*w["STF_second_moment"])/h),
        })
    for row in groups:
        rhs=1+row["synthetic_A_dipole_shift_over_H"]+row["synthetic_sigma_quadrupole_shift_over_H"]
        if abs(row["synthetic_rate_mono_H_scaled"]-rhs)>3e-13:
            raise RuntimeError("CF4 angular selection monopole-dipole-quadrupole exact identity failed")
    # Galaxy LOOK vectors originate in ICRS J2000, Planck low-l harmonics
    # are Galactic. Transform the actual CF4 samples before any CMB shape
    # projection. This projects one observed map on an irregular catalogue
    # window, NOT a joint CMB–CF4 cosmological likelihood.
    icrs=SkyCoord(x=n[:,0]*u.one,y=n[:,1]*u.one,z=n[:,2]*u.one,
                  representation_type="cartesian",frame="icrs")
    transformed=np.array(icrs.galactic.cartesian.xyz.value).T
    transformed=unit_sky(transformed)
    with np.load(PLANCK,allow_pickle=False) as data:
        names=[str(v) for v in data["names_T"]]
        coefficients=np.asarray(data["coeff_T"],float)
    if coefficients.shape!=(9,32):
        raise RuntimeError("actual Planck source one sky 9-processing chart changed")
    projected={}
    for name,row in zip(names,coefficients):
        Q=masked_planck_quadrupole_to_temperature_stf(row[:5])
        q=np.einsum("ni,ij,nj->n",transformed,Q,transformed,optimize=True)
        expected=float(np.sum(row[:5]**2)/(4*np.pi*T0_MICROK*T0_MICROK))
        per_shell=[]
        for lo,hi in shells:
            select=(z>=lo)&(z<hi)
            per_shell.append({"lo":lo,"hi":hi,
                "CF4_angular_selection_mean_Theta2":float(q[select].mean()),
                "CF4_angular_selection_rms_Theta2":float(np.sqrt(np.mean(q[select]**2)))})
        projected[name]={
            "source_thermal_CMB_quadrupole_not_geometry_shear":True,
            "full_sky_rms_Theta2":float(np.sqrt(expected)),
            "CF4_angular_sample_rms_Theta2":float(np.sqrt(np.mean(q*q))),
            "CF4_angular_selection_mean_Theta2":float(np.mean(q)),
            "per_shell":per_shell,
        }
    report={
       "schema":"htt.K01_exact_one_event_covariant_optical_CF4_and_Planck_angular_source/1",
       "date_KST":"2026-10-15",
       "claim_tier":"THEOREM_LEVEL_EVENT_LOCAL_1PLUS3_KINEMATICS_SOURCE_GEOMETRY_NOT_COSMOLOGICAL_INFERENCE",
       "source_CF4_SHA256":CF4_SHA,
       "source_Planck_SHA256":PLANCK_SHA,
       "previous_euclidean_K01_result_SHA256":digest(OLD_K01),
       "actual_CF4_source_groups":len(n),
       "actual_CMB_cosmological_skies":1,
       "actual_Planck_processing_products":9,
       "local_photon_rule":"-(d ln E/dt_u)=Theta/3 + A dot e + sigma_ab e^a e^b, e=-sky_LOOK",
       "metric_signature":"-+++","epsilon123":1,
       "normalization":"Sigma=|sigma|/H; |sigma|=sqrt(sigma_ab sigma^ab/2)",
       "source_kinematical_optical_angular_rank":ndarray(geometry),
       "acceleration_vs_hypothetical_local_boost_angular_span":overlap,
       "synthetic_physical_event_injection_not_observation":{
          "H_km_s_Mpc":h*MPC_KM,"A_km_s_Mpc":(a*MPC_KM).tolist(),
          "sigma_STF5_km_s_Mpc":(sig5*MPC_KM).tolist(),
          "omega_3_km_s_Mpc":[5,-7,9],
          "Sigma_dimensionless":sigma_over_H(sigma,h),
          "recovered_H_A_sigma_STF9_maxabs_km_s_Mpc":recovered_err,
          "nabla_u_direct_vs_design_maxabs_s_inv":rerr,
          "omega_nonzero_vs_zero_maxabs_s_inv":omega_insensitivity,
          "local_Euclidean_CF4_jet_optical_limit_maxabs_s_inv":comparator["maxabs_error_s_inv"],
          "source_claim":"GENERATED_PARAMETERS_NOT_ESTIMATED_PHYSICAL_CF4_SHEAR_OR_A",
       },
       "actual_CF4_redshift_shell_sky_coverage":groups,
       "source_Galactic_Planck_quadrupole_projected_on_CF4_ICRS_sightlines":projected,
       "physical_linkage":{
           "legacy_x_F_Pi_Q_GF":"UNKNOWN_FULL_SECTORS_AND_JOINT_POSTERIOR",
           "STF_CF4_to_GR_cosmological_shear":"NOT_CALIBRATED",
           "A_acceleration_four_vector":"ANGULAR_COEFFICIENT_ONLY_NO_OBSERVATIONAL_OPTICAL_RATE",
           "omega_vorticity":"DIRECT_LOCAL_ENERGY_OPERATOR_BLIND_INTEGRATED_DIRECTION_TRANSFER_NOT_CHECKED",
           "beta_material_radiation_tilt":"REQUIRES_NAMED_FRAMES_AND_SOURCE_HISTORY",
           "Planck9_products":"ONE_PHYSICAL_SKY_NOT_9_REALIZATIONS",
           "CF4_H_eff":"LUMINOSITY_DISTANCE_OBSERVABLE_NOT_INSTANTANEOUS_LOG_PHOTON_ENERGY_DRIFT",
       },
       "physical_shear_vorticity_acceleration_detection":"NONE",
       "cosmological_Bianchi_family_inference":"NONE",
       "publication_claim":"K01_LOCAL_PHYSICAL_OPERATOR_SCOPED_ONLY",
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    np.savez_compressed(out/"source_sky_operator_geometry.npz",
        CF4_source_group_ids=groupid,
        CF4_source_z_cmb=z,
        optical_one_event_design9=X[:,:9],
        optical_one_event_omega_null3=X[:,9:],
        actual_Planck_product_names=np.asarray(names),
        actual_Planck_quadrupole_projected_CF4_look_shape=np.asarray(
           [v["CF4_angular_selection_mean_Theta2"] for v in projected.values()]))
    fig,axs=plt.subplots(1,2,figsize=(11,4.4),layout="constrained")
    indices=np.arange(len(shells))
    axs[0].plot(indices,[x["mean_n_norm"] for x in groups],"o-",label="look dipole mean norm")
    axs[0].plot(indices,[x["STF_selection_norm"] for x in groups],"s-",label="quadrupole sky-window STF norm")
    axs[0].set_xticks(indices,[f"{a:.3f}-{b:.3f}" for a,b in shells],rotation=30)
    axs[0].set(xlabel="Actual CF4 z_CMB shell; sky coverage only",
               ylabel="nonuniform catalogue angular moments",
               title="Window geometry distinguishes sky monopole from local anisotropy")
    axs[0].grid(alpha=.2);axs[0].legend(fontsize=8)
    axs[1].bar(indices-.16,[x["synthetic_A_dipole_shift_over_H"] for x in groups],
               width=.32,label="injected A sky dipole")
    axs[1].bar(indices+.16,[x["synthetic_sigma_quadrupole_shift_over_H"] for x in groups],
               width=.32,label="injected sigma sky quadrupole")
    axs[1].set_xticks(indices,[f"{a:.3f}-{b:.3f}" for a,b in shells],rotation=30)
    axs[1].set(xlabel="Real CF4 sky geometry; MANUFACTURED 1+3 rates",
               ylabel="synthetic selection shift relative to H",
               title="Not observed physical shear or acceleration")
    axs[1].grid(axis="y",alpha=.2);axs[1].legend(fontsize=8)
    fig.savefig(out/"cf4_covariant_optical_sightline_geometry.png",dpi=150)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
       "# K01: 완전한 한 사건의 1+3 에너지 변환과 CF4 시선 기하\n\n"
       "(-,+,+,+)에서 k=E(u+e), ∇_a u_b=-u_a A_b+Θ h_ab/3+σ_ab+ω_ab. "
       "방향이 관측자로 향하는 incoming photon e=-n이면 "
       "-d lnE/dt_u=H-A·n+σ_ij n_i n_j. "
       "ω의 직접 contraction은 0이지만 방향 수송/통합 영향은 남는다.\n\n"
       f"실제 CF4 {len(n)}개의 J2000 LOOK 방향에서 [H,A3,STF5] "
       f"angular design rank={geometry['rank_H_A3_sigma5']}, ω3 rank=0. "
       "가상 boost dipole과 A dipole의 angular column span은 동일 rank3이나 "
       "전자는 dimensionless β, 후자는 s^-1 acceleration으로 동일 물리가 아니다.\n\n"
       "각 z shell의 실제 look second moment와 드리프트 평균에 미치는 "
       "MANUFACTURED A/σ의 조건부 변동을 계산했고, 실제 Planck low-ell "
       "원본 한 하늘 9 처리 quad tensor를 Galactic 변환하여 CF4 sky "
       "selection에 투영했다. 이는 관측된 GR shear 또는 joint likelihood가 아니다.\n",
       encoding="utf-8")
    print("K01_ONE_CONGRUENCE_SOURCE_RESULT",
          "N",len(n),"rank",geometry["rank_H_A3_sigma5"],"omega_null",geometry["omega_nullity"],
          "cond",round(geometry["angular_condition_H_A_sigma"],6),
          "shells",[(x["source_count"],round(x["mean_n_norm"],5),
                     round(x["STF_selection_norm"],5)) for x in groups],
          "Sigma_synthetic",round(sigma_over_H(sigma,h),6),
          "max_injection_err",recovered_err)
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True,type=Path)
    args=ap.parse_args()
    run(args.output_dir)
