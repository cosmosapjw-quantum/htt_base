"""Source-verified K01 GR photon drift bridge to real CF4/Planck sky shapes."""
import hashlib,json
from pathlib import Path
import numpy as np
import pytest

from astropy.coordinates import SkyCoord
from astropy import units as u
from obsstat.r7_cmb_product_response import real_design
from obsstat.legacy_teff_tensor_observation_bridge import (
    masked_planck_quadrupole_to_temperature_stf,T0_MICROK
)

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
RESULT=BASE/"results/K01_covariant_optical_CF4_Planck_v1/result.json"
CF4=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
PLANCK=ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"


def result():return json.loads(RESULT.read_text())


def test_K01_real_source_35970_J2000_and_SAG_same_sky_provenance():
    d=result()
    assert d["source_CF4_SHA256"]==hashlib.sha256(CF4.read_bytes()).hexdigest()
    assert d["source_Planck_SHA256"]==hashlib.sha256(PLANCK.read_bytes()).hexdigest()
    assert d["actual_CF4_source_groups"]==35970
    assert d["actual_CMB_cosmological_skies"]==1
    assert d["actual_Planck_processing_products"]==9
    assert d["metric_signature"]=="-+++"
    assert d["epsilon123"]==1
    assert d["normalization"]=="Sigma=|sigma|/H; |sigma|=sqrt(sigma_ab sigma^ab/2)"
    assert d["physical_shear_vorticity_acceleration_detection"]=="NONE"
    assert d["physical_linkage"]["CF4_H_eff"].startswith("LUMINOSITY_DISTANCE")


def test_exact_rank_and_source_angular_hypothetical_injection_not_CF4_measurement():
    z=result()
    x=z["source_kinematical_optical_angular_rank"]
    assert x["rank_H_A3_sigma5"]==9
    assert x["rank_omega3"]==0 and x["omega_nullity"]==3
    assert x["angular_condition_H_A_sigma"]==pytest.approx(5.3660955182317265,rel=1e-13)
    assert z["acceleration_vs_hypothetical_local_boost_angular_span"]["rank"]==3
    assert z["acceleration_vs_hypothetical_local_boost_angular_span"]["angular_nullity"]==3
    a=z["synthetic_physical_event_injection_not_observation"]
    assert a["Sigma_dimensionless"]==pytest.approx(.037015284910144976,rel=1e-13)
    assert a["recovered_H_A_sigma_STF9_maxabs_km_s_Mpc"]<1e-10
    assert a["nabla_u_direct_vs_design_maxabs_s_inv"]<1e-30
    assert a["omega_nonzero_vs_zero_maxabs_s_inv"]<1e-30
    assert a["source_claim"].startswith("GENERATED_PARAMETERS")


def test_source_window_monopole_mixing_is_exact_and_used_as_geometry_only():
    z=result()
    rows=z["actual_CF4_redshift_shell_sky_coverage"]
    assert [x["source_count"] for x in rows]==[8581,7833,8818,10738]
    assert sum(x["source_count"] for x in rows)==35970
    for x in rows:
        assert 0<=x["mean_n_norm"]<1
        assert x["STF_selection_norm"]>0
        assert sum(x["second_moment_eigenvalues"])==pytest.approx(1,abs=2e-14)
        assert x["synthetic_rate_mono_H_scaled"]==pytest.approx(
              1+x["synthetic_A_dipole_shift_over_H"]+
              x["synthetic_sigma_quadrupole_shift_over_H"],abs=2e-14)
    assert rows[-1]["mean_n_norm"]>rows[0]["mean_n_norm"]+.6


def test_galactic_Planck_harmonic_chart_on_actual_50_CF4_J2000_dirs():
    with np.load(CF4,allow_pickle=False) as z:
        n=np.asarray(z["n_J2000"][:50],float)
    source=SkyCoord(x=n[:,0]*u.one,y=n[:,1]*u.one,z=n[:,2]*u.one,
                    representation_type="cartesian",frame="icrs")
    ng=np.asarray(source.galactic.cartesian.xyz.value).T
    with np.load(PLANCK,allow_pickle=False) as z:
        names=[str(a) for a in z["names_T"]]
        coeff=np.asarray(z["coeff_T"],float)
    a=coeff[names.index("SMICA_FULL"),:5]
    Q=masked_planck_quadrupole_to_temperature_stf(a)
    tensor=np.einsum("ni,ij,nj->n",ng,Q,ng,optimize=True)
    harmonic=real_design(ng,ell_max=2)[:,4:9]@a/T0_MICROK
    np.testing.assert_allclose(tensor,harmonic,rtol=5e-14,atol=2e-20)
    res=result()["source_Galactic_Planck_quadrupole_projected_on_CF4_ICRS_sightlines"]["SMICA_FULL"]
    assert res["source_thermal_CMB_quadrupole_not_geometry_shear"] is True
    assert res["CF4_angular_selection_mean_Theta2"]==pytest.approx(
        8.202952222995385e-7,rel=1e-13)


def test_Bianchi_and_curvature_physical_claims_remain_gated():
    z=result()
    assert z["cosmological_Bianchi_family_inference"]=="NONE"
    assert z["physical_linkage"]["legacy_x_F_Pi_Q_GF"].startswith("UNKNOWN")
    assert z["physical_linkage"]["omega_vorticity"].startswith("DIRECT_LOCAL")
    assert z["physical_linkage"]["beta_material_radiation_tilt"].startswith("REQUIRES")
    j=json.loads((BASE/"PUBLICATION_DAG.json").read_text())
    byid={v["id"]:v for v in j["nodes"]}
    assert byid["K01"]["state"]=="completed_scoped"
    assert byid["K02"]["state"]=="completed_scoped"
    assert byid["K02"]["existing_evidence"]
    # K01 remains physically one-event; K02 adds source-conditional apparent
    # transfer stress only, and cannot certify K03/K04 observational physics.
    assert byid["K03"]["external_missing"]
    assert all(q["publication_status"]=="NOT_READY_TO_SUBMIT" for q in j["papers"])
