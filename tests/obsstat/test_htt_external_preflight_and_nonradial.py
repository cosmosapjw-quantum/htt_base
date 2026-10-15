"""External physics blocker nonpromotion, K03 hypothetical transverse rank."""
import json
from pathlib import Path
import numpy as np
import pytest
from obsstat.k03_nonradial_proper_motion_preflight import (
    ProperMotionPreflightError,geometric_nonradial_rank,
    tangential_jet_design,synthetic_transverse_recovery
)
from obsstat.htt_kinematic_radial_identification import antisymmetric_basis

ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT/"docs/research_program/observational_publication_20261015"


def dirs(n=300):
    r=np.random.default_rng(88)
    v=r.normal(size=(n,3))
    return v/np.linalg.norm(v,axis=1)[:,None]


def test_exact_radial_antisym_null_and_transverse_tangent_witness():
    n=dirs()
    e,b=tangential_jet_design(n)
    assert e.shape==(len(n),5,3)
    assert b.shape==(len(n),3,3)
    assert np.max(abs(np.einsum("nki,ni->nk",e,n)))<4e-14
    assert np.max(abs(np.einsum("nki,ni->nk",b,n)))<4e-14
    omega=np.einsum("k,kij->ij",[5.,-7.,9.],antisymmetric_basis())
    assert np.max(abs(np.einsum("ni,ij,nj->n",n,omega,n)))<4e-15
    tangent=np.einsum("ij,nj->ni",omega,n)
    assert np.max(np.linalg.norm(tangent,axis=1))>1
    assert geometric_nonradial_rank(n)["rank_tangential_5shear_3omega"]==8


def test_transverse_synthetic_same_geometry_recovery():
    n=dirs(800)
    z=synthetic_transverse_recovery(n,
         sigma_components=[1.,-2.,3.,.5,-1.],
         omega_components=[5.,-7.,9.])
    np.testing.assert_allclose(z["recovered_jet_coefficients_km_s_Mpc"],
      [1.,-2.,3.,.5,-1.,5.,-7.,9.],atol=2e-12)
    assert z["actual_observed_proper_motion"].startswith("ABSENT")
    assert z["injection_maxabs_error_km_s_Mpc"]<2e-12


def test_real_CF4_35970_sightline_rank_three_is_only_preparation():
    p=PUB/"results/K03_CF4_NONRADIAL_PREP_v1/result.json"
    x=json.loads(p.read_text())
    z=x["source_geometry"]
    assert x["source_real_group_sightlines"]==35970
    assert z["rank_tangential_5shear_3omega"]==8
    assert z["rank_omega_after_shear_profile"]==3
    assert z["radial_vorticity_mode_norm"]<3e-13
    assert z["relative_omega_information_eigenvalues_after_shear_profile"]==pytest.approx(
        [.5282989022778516,.7223403252303943,.9306794733898427],rel=1e-12)
    assert len(x["actual_CF4_depth_shells"])==4
    assert sum(k["groups"] for k in x["actual_CF4_depth_shells"])==35970
    assert x["physical_nonradial_proper_motion_observations"].startswith("NOT_IN_CF4")
    assert x["K03_DAG_state"].startswith("EXTERNALLY_BLOCKED")
    assert x["manufactured_velocity_gradient_rates"]["injection_maxabs_error_km_s_Mpc"]<3e-12


def test_seven_blocked_preflight_source_paths_and_unchanged_DAG():
    p=PUB/"results/EXTERNAL_BLOCKED_PREFLIGHT_20261015_v2/result.json"
    x=json.loads(p.read_text())
    assert x["external_blocked_node_count"]==7
    assert x["real_physical_qualified_new_sources"]==0
    assert x["local_candidates_existing_count"]==21
    assert set(x["blockers"])=={"S04","L03","H02","V03","B02","K03","K04"}
    dag=json.loads((PUB/"PUBLICATION_DAG.json").read_text())
    blocked={node["id"]:node for node in dag["nodes"] if node["external_missing"]}
    assert set(blocked)==set(x["blockers"])
    for key,node in x["blockers"].items():
        assert node["authoritative_DAG_state"]=="pending"
        assert node["authoritative_DAG_external_missing"]==blocked[key]["external_missing"]
        assert node["qualified_real_physical_source_satisfied"] is False
        assert all(v["exists"] for v in node["local_candidate_artifacts"])
        assert node["preparation"]["missing"]
    assert x["no_DAG_status_modified_by_preflight"] is True


def test_nonradial_bad_directions_rejected():
    with pytest.raises(ProperMotionPreflightError):
        geometric_nonradial_rank(np.ones((30,3)))
    with pytest.raises(ProperMotionPreflightError):
        geometric_nonradial_rank(dirs(10))
    with pytest.raises(ProperMotionPreflightError):
        synthetic_transverse_recovery(dirs(),sigma_components=np.zeros(6),
           omega_components=np.zeros(3))
