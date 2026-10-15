#!/usr/bin/env python3
"""K03 external nonradial proper-motion preparation on actual CF4 sky geometry.

No CF4 transverse velocities are observed. Only real *directions* are
used to test that proposed nonradial observable has independent omega
mode columns after profiling shear. Not a proper-motion likelihood.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from obsstat.k03_nonradial_proper_motion_preflight import (
 geometric_nonradial_rank,synthetic_transverse_recovery
)
ROOT=Path(__file__).resolve().parents[1]
CF4=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"


def run(out):
    if out.exists():raise FileExistsError("create-only source angular geometry output")
    if hashlib.sha256(CF4.read_bytes()).hexdigest()!=SHA:
        raise RuntimeError("CF4 immutable selected catalogue identity drift")
    with np.load(CF4,allow_pickle=False) as f:
        n=np.asarray(f["n_J2000"],float)
        z=np.asarray(f["z_CMB"],float)
    if n.shape!=(35970,3) or z.shape!=(35970,):
        raise RuntimeError("actual 35970 grouped source sightline count required")
    reference=geometric_nonradial_rank(n)
    rng=np.random.default_rng(44)
    iso=rng.normal(size=(18000,3))
    iso/=np.linalg.norm(iso,axis=1)[:,None]
    full=geometric_nonradial_rank(iso)
    sources=[]
    for lo,hi in ((.01,.03),(.03,.05),(.05,.075),(.075,.1)):
        mask=(z>=lo)&(z<hi)
        info=geometric_nonradial_rank(n[mask])
        sources.append({"low_z":lo,"high_z":hi,
                        "groups":int(mask.sum()),
                        "omega_after_shear_relative_information":
                         info["relative_omega_information_eigenvalues_after_shear_profile"].tolist(),
                        "shear_omega_angular_subspace_overlap":
                         info["normalized_shear_omega_cross_operator_spectral_norm"],
                        "physical_data_present":False})
    injection=synthetic_transverse_recovery(
        n,sigma_components=[1.,-2.,3.,.5,-1.],
        omega_components=[5.,-7.,9.])
    if (reference["rank_tangential_5shear_3omega"]!=8
        or injection["injection_maxabs_error_km_s_Mpc"]>2e-11):
        raise RuntimeError("source K03 mathematical preflight not identifiable")
    result={
       "schema":"htt.K03_preflight_nonradial_vorticity_angular_source/1",
       "date_KST":"2026-10-15",
       "source_CF4_SHA256":SHA,
       "source_real_group_sightlines":len(n),
       "source_declared_kinematics":"LOCAL_EUCLIDEAN_LINEAR_VELOCITY_JET_ONLY",
       "physical_law":"mu_tangent=(I-n n^T) G n, G=H I+S+W; omega radial nWn=0, transverse Wn may be nonzero",
       "source_geometry":{
           k:(v.tolist() if isinstance(v,np.ndarray) else v)
           for k,v in reference.items()},
       "isotropic_random_sky_geometry":{
           k:(v.tolist() if isinstance(v,np.ndarray) else v)
           for k,v in full.items()},
       "actual_CF4_depth_shells":sources,
       "manufactured_velocity_gradient_rates":{
           k:(v.tolist() if isinstance(v,np.ndarray) else v)
           for k,v in injection.items()},
       "physical_nonradial_proper_motion_observations":"NOT_IN_CF4_RELEASED_GROUP_SOURCE",
       "GR_Bianchi_global_vorticity_transfer":"NOT_IMPLEMENTED_IN_THIS_EUCLIDEAN_PREFLIGHT",
       "source_frame_correlated_covariance":"NOT_SUPPLIED",
       "K03_DAG_state":"EXTERNALLY_BLOCKED_AND_UNCHANGED",
       "scientific_claim":"ANGULAR_READINESS_ONLY_NO_OMEGA_DETECTION"
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    fig,ax=plt.subplots(figsize=(9.2,4.4),layout="constrained")
    a=np.arange(len(sources))
    info=np.asarray([v["omega_after_shear_relative_information"] for v in sources])
    for j in range(3):
        ax.plot(a,info[:,j],marker="o",label=f"omega mode {j+1} profiled")
    ax.set_xticks(a,[f"{v['low_z']:.3f}-{v['high_z']:.3f}" for v in sources])
    ax.set(xlabel="actual CF4 directional source redshift shell",
           ylabel="relative geometric omega information vs fixed shear",
           title="Hypothetical transverse channel, NOT observed proper motion")
    ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.savefig(out/"cf4_k03_hypothetical_tangent_omega_geometry.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
      "# K03 외부 관측 입력 사전준비: nonradial transverse response\n\n"
      "실제 CF4 35,970 grouped source의 angular n_J2000만 사용한다. "
      "물리적으로 관측된 proper motion, 1+3 global source transfer, "
      "source correlated covariance는 없다. 국소 Euclidean first-jet에서 "
      "radial nWn=0, tangential (I-nn)Wn=Wn이며, "
      "tangent shear5+omega3 설계의 rank8와"
      f"omega-after-shear rank3를 관측창별 검증. 전체 CF4 방향의 "
      f"omega-profiled relative eigen={sources[0]['omega_after_shear_relative_information']}, "
      "자세한 shell별 결과는 JSON 참고. "
      "이 결과는 K03 외부입력 준비증거이며 완료/검출이 아니다.\n",encoding="utf-8")
    print("K03_HYPOTHETICAL_TANGENT_SOURCE",len(n),
          "angular_rank",reference["rank_tangential_5shear_3omega"],
          "omega_after_shear",reference["relative_omega_information_eigenvalues_after_shear_profile"].tolist(),
          "injection_maxabs",injection["injection_maxabs_error_km_s_Mpc"],flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    run(a.output_dir)
