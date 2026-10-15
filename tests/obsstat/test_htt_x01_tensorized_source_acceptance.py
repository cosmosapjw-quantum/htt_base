"""Source actual 999 STF2/3 and X01 six-paper typed authority acceptance."""
import hashlib,json
from pathlib import Path
import numpy as np
import pytest

from common.typefree_functionals import evaluate_paired_anchor
from obsstat.tensorized_lowell_source import (
    empirical_irrep_anchor,record,measured_directional_support
)
ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
D=PUB/"results/X01_tensorized_stf_planck_ffp999_v2"
B=PUB/"results/X01_tensorized_source_bindings_v3"
SOURCE=PUB/"results/L01_schur_999cmb_300noise_v2/source_lowell_nested_999plus300.npz"
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def result():
    return json.loads((D/"result.json").read_text())


def test_actual_Planck_source_tensor_stf2_stf3_and_empirical_not_cosmological():
    z=result()
    assert z["physical_real_CMB_sky_count"]==1
    assert z["FFP10_unique_CMB_source_realizations"]==999
    assert z["FFP10_noise_same_ID_pairs"]==300
    assert z["physical_kinematic_state_sigma_omega_A_beta"]=="NOT_IDENTIFIED"
    assert z["source_actual_masked_CMB_999_300_npz_sha256"]==H(SOURCE)
    assert z["STF_tensor_vs_real_harmonic_explicit_six_directions_maxabs_microK"]<2e-13
    q=np.asarray(z["actual_CMB_temperature_quadrupole_STF2_microK"])
    assert q.shape==(3,3)
    np.testing.assert_allclose(q,q.T,atol=1e-13)
    assert abs(np.trace(q))<1e-13
    o=np.asarray(z["actual_octupole_rank3_STF_tensor_microK"])
    assert o.shape==(3,3,3)
    for j in range(3):
        assert abs(np.trace(o[:,:,j]))<4e-13
    assert z["tensorized_source_GF_fit_mask_path_not_observed_depth_G_F"] is True


def test_typed_tensor_Q_F_Pi_and_missing_physical_irrep():
    z=result()
    for key,ell in (("2",2),("3",3)):
        x=z["irrep_typed_anchors"][key]
        assert x["tensor_rank"]==ell
        assert x["harmonic_coordinate_dimension"]==2*ell+1
        assert x["one_actual_sky_K1_Q_gauge"]>0
        assert x["empirical_mask_fit_path_delta_Q_RMS"]>0
        assert len(x["source_empirical_Q_gauge_quantiles"])==5
        assert len(x["actual_nine_processing_Q_gauges_dependent"])==9
        assert len(x["actual_one_sky_F_directional_profile_xyz_plus_minus"])==6
        assert x["physical_inferred_irrep"]["physical_tensor_image_undefined_mass"]==1.
        assert x["physical_inferred_irrep"]["physical_tensor_exceedance_outer"]==[0.,1.]
        assert all(t["status"].endswith("NOT_PLANCK_P_VALUE") for t in
                   x["empirical_simulation_strict_Q_tails_NOT_P"])
        v=np.asarray(x["actual_one_sky_F_directional_profile_xyz_plus_minus"])
        if ell==2:np.testing.assert_allclose(v[:3],v[3:],atol=3e-14)
        else:np.testing.assert_allclose(v[:3],-v[3:],atol=3e-14)


def test_passive_orthogonal_source_reparametrization_preserves_gauge_and_F():
    with np.load(SOURCE,allow_pickle=False) as z:
        a=np.asarray(z["cmb_l5_36"][:,:],float)[:,4:9]
        actual=np.asarray(z["observed_l5"][0,4:9],float)
    x=empirical_irrep_anchor(a,ell=2,source_hash=H(SOURCE))
    q0=evaluate_paired_anchor(record(x,"actual",actual)).gauge
    direction=np.array([.1,-.23,.4,.15,-.7])
    f0=measured_directional_support(x,actual,direction)["F_directional_support_ratio"]
    rng=np.random.default_rng(6)
    U,_=np.linalg.qr(rng.normal(size=(5,5)))
    rotated=a@U
    y=empirical_irrep_anchor(rotated,ell=2,source_hash=H(SOURCE))
    q1=evaluate_paired_anchor(record(y,"actual-rotated",actual@U)).gauge
    f1=measured_directional_support(y,actual@U,direction@U)["F_directional_support_ratio"]
    assert q1==pytest.approx(q0,abs=2e-12)
    assert f1==pytest.approx(f0,abs=2e-13)


def test_real_cf4_group_window_is_deterministic_not_joint_likelihood():
    z=result()["actual_CF4_35970_look_window_on_Planck_temperature_irreps"]
    assert z["CF4_source_actual_group_count"]==35970
    assert len(z["redshift_shells"])==4
    assert sum(q["CF4_actual_source_count"] for q in z["redshift_shells"])==35970
    for q in z["redshift_shells"]:
        assert q["combined_apparent_temperature_angular_mean_microK"]==pytest.approx(
          q["CF4_sky_window_even_STF2_source_temperature_mean_microK"]+
          q["CF4_sky_window_odd_STF3_source_temperature_mean_microK"],abs=2e-14)
        assert q["physical_cross_catalogue_posterior"]=="NOT_CONSTRUCTED"
    assert z["observed_Planck_lowell_one_sky_on_CF4_sightlines_microK"]==pytest.approx(
        2.910818076242285,rel=1e-12)


def test_X01_six_paper_source_authority_and_overlap_graph_with_7_pending():
    z=json.loads((B/"SOURCE_BINDINGS.json").read_text())
    assert len(z["sources"])==11
    assert len(z["source_id_overlap_edges"])==9
    assert len(z["method_original_later_PR_commits"])==7
    assert set(z["source_binding_per_six_papers"])=={"P1","P2","P3","P4","P5","P6"}
    for paper in z["source_binding_per_six_papers"].values():
        assert paper["missing"] and paper["sources"]
        assert set(paper["sources"]) <= set(z["sources"])
    assert z["historical_source_design_rechecked"][6]["authority"]=="LOCAL_ONLY_UNTRACKED_AT_REDESIGN"
    assert z["real_native_physics_source_qualified_now"]==0
    assert z["external_blockers_remain_open"]==7
    assert z["same_cosmological_joint_likelihood_not_built"] is True
    assert z["sources"]["K1_FFP10_RAW"]["sha256"]=="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
    assert all(src["actual_scientific_source_present"] and len(src["sha256"])==64
               for src in z["sources"].values())
    assert all(edge["independent_likelihood"] is not True
               for edge in z["source_id_overlap_edges"])


def test_external_tensor_requirements_not_source_qualification_or_proper_motion():
    z=json.loads((B/"EXTERNAL_TENSOR_INPUTS.json").read_text())
    assert z["physical_new_source_qualified"]==0
    assert set(z["contracts"])=={"S04","L03","H02","V03","B02","K03","K04"}
    assert "spin1" in z["contracts"]["K03"]["tensor"]
    assert "11 Bianchi" in z["contracts"]["B02"]["tensor"]
    dag=json.loads((PUB/"PUBLICATION_DAG.json").read_text())
    nodes={t["id"]:t for t in dag["nodes"]}
    assert nodes["X01"]["state"]=="completed_scoped"
    assert nodes["S03"]["state"]=="pending"
    assert nodes["K03"]["external_missing"]
    assert nodes["B02"]["external_missing"]
    assert all(p["publication_status"]=="NOT_READY_TO_SUBMIT" for p in dag["papers"])
