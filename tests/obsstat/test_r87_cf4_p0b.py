"""P0-B: source group genealogy, projected method contrasts and heldout.

Fail-closed physics: same-group method overlap is one group, not independent
galaxies or a physical correlated PV/selection/null posterior.
"""
import numpy as np
import pytest
from htt.obsstat import cf4_p0b as cf
from pathlib import Path

SRC=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")


@pytest.fixture(scope="module")
def actual():
    return cf.load_cf4_method_source()


def test_exact_raw_selected_lineage_and_seven_presence(actual):
    assert len(actual.group_id)==35970
    assert actual.method_presence.shape==(35970,7)
    assert actual.method_modulus.shape==(35970,6)
    assert actual.method_sigma.shape==(35970,6)
    assert len(np.unique(actual.group_id))==35970
    assert actual.method_names==("SNIA","FP","TF","SBFO","SBFI","SNII")
    assert int((actual.method_presence.sum(axis=1)==0).sum())==185
    assert int((actual.method_presence.sum(axis=1)>1).sum())==926
    assert sum(actual.selected_family_counts.values())==35970
    assert actual.raw_method_field_role=="ALREADY_INTERCALIBRATED_GROUPED_DISTANCE_ESTIMATES_NOT_RAW_ZERO_POINTS"


def test_group_projection_matches_independent_profiled_dummy_small_case():
    # Explicit group dummy nuisance exactly cancels any common alpha, PV and
    # one shared constant modulus offset, but not method-dependent offsets.
    gmu=np.array([[31.,31.5,31.7,0,0,0],[32.,32.5,32.7,0,0,0],
                  [34.,34.5,34.7,0,0,0],[36.,36.5,36.7,0,0,0]])
    gs=np.where(gmu>0,.2,np.inf)
    result=cf.profile_method_offsets(gmu,gs,ref_index=0)
    np.testing.assert_allclose(result["delta_mag"][0:3],[0,.5,.7],atol=2e-11,rtol=0)
    np.testing.assert_allclose(result["fisher_full"]@np.ones(6),np.zeros(6),atol=1e-12)
    # Rank-limited output on 3 observed methods, not invent zeros for absent ones.
    assert result["rank_effective"]==2
    assert np.isnan(result["delta_mag"][3:]).all()


def test_source_method_network_components_and_non_duplicate_groups(actual):
    x=cf.profile_method_offsets(actual.method_modulus,actual.method_sigma)
    assert x["n_distinct_supported_groups"]==int(np.sum(np.isfinite(actual.method_sigma).sum(axis=1)>=2))
    assert x["rank_effective"]>=3
    assert x["n_distinct_supported_groups"]<35970
    assert x["delta_mag"][0]==0.
    assert np.all(np.isfinite(x["delta_mag"][1:]))
    assert x["fisher_null_one_max"] < 1e-12*np.linalg.norm(x["fisher_full"],ord=np.inf)


def test_any_true_distance_or_common_velocity_shift_cancels_contrasts(actual):
    mu=actual.method_modulus[:600].copy()
    sigma=actual.method_sigma[:600].copy()
    base=cf.method_information(mu,sigma)
    shift=np.linspace(-.35,.75,len(mu))
    changed=np.where(np.isfinite(sigma),mu+shift[:,None],mu)
    repeat=cf.method_information(changed,sigma)
    np.testing.assert_allclose(base["F"],repeat["F"],atol=1e-10,rtol=0)
    np.testing.assert_allclose(base["b"],repeat["b"],atol=1e-9,rtol=0)


def test_four_fixed_RA_sector_heldout_is_group_disjoint_not_calibration_independent(actual):
    held=cf.spatial_group_heldout(actual)
    assert len(held["folds"])==4
    assert all(row["unique_group_ID_train_vs_test_overlap"]==0 for row in held["folds"])
    assert sum(row["test_groups"] for row in held["folds"])==35970
    assert all(row["finite_working_loss"] for row in held["folds"])
    assert held["independent_upstream_zero_point_calibration"] is False
    assert held["qualified_selection_PV_coverage"] is False


def test_invalid_nonfinite_or_negative_sigma_rejected():
    mu=np.array([[34.,35.,np.nan,0,0,0],[34.1,35.1,np.nan,0,0,0]])
    good=np.array([[.2,.2,np.inf,np.inf,np.inf,np.inf]]*2)
    with pytest.raises(ValueError):
        cf.method_information(mu,np.where(good==np.inf,0,good))
    bad=good.copy();bad[0,0]=np.nan
    with pytest.raises(ValueError):
        cf.method_information(mu,bad)


def test_conditional_PV_woodbury_scenario_is_not_physical_covariance(actual):
    # The physical cosmological covariance S_PV is NOT calibrated by the source.
    sample=cf.pv_sensitivity_scenario(actual,bulk_sigma_kms=150.,shear_sigma_kms_per_mpc=1.5)
    assert sample["source_N"]==35970
    assert sample["F_conditioned"].shape==(9,9)
    assert sample["source_assumed_low_rank_modes"]==8
    assert sample["source_matched_PV_field_ensemble_qualified"] is False
    assert sample["source_selection_C_qualified"] is False
    assert sample["physical_Pi"] is None
    assert sample["observed_normal_shear"] is None


def test_no_full_physical_covariance_or_pvalue_without_external_source(actual):
    x=cf.p0b_claim_gate(actual)
    assert x["actual_full_C_qualified"] is False
    assert x["source_valid_raw_method_DM"] is True
    assert x["actual_spatial_calibration_heldout_qualified"] is False
    assert x["physical_p_value"] is None
    assert x["P0_B_physics_status"]=="BLOCKED_PHYSICAL_PV_CALIBRATION_SELECTION_AND_HELDOUT"


def test_exact_shear_PV_is_in_H03_design_span_but_bulk_is_not(actual):
    shear=cf.pv_sensitivity_scenario(actual,bulk_sigma_kms=0.,
                                    shear_sigma_kms_per_mpc=1.5)
    assert shear["source_assumed_low_rank_modes"]==5
    assert max(shear["source_modes_distance_to_H03_mean_span_relative"])<1e-12
    assert shear["working_gls_beta_max_abs_difference"]<1e-8
    assert shear["covariance_trace_ratio"]>1
    assert shear["source_modes_fully_in_mean_span"] is True
    assert shear["source_span_theorem_covariance_relative_error"]<1e-9
    bulk=cf.pv_sensitivity_scenario(actual,bulk_sigma_kms=150.,
                                   shear_sigma_kms_per_mpc=0.)
    assert bulk["source_assumed_low_rank_modes"]==3
    assert min(bulk["source_modes_distance_to_H03_mean_span_relative"])>1e-3
    assert bulk["source_modes_fully_in_mean_span"] is False
    assert bulk["source_span_theorem_covariance_relative_error"] is None
    assert bulk["covariance_trace_ratio"]>1
    assert bulk["physical_Pi"] is None


def test_two_method_groups_agree_with_independent_edge_information(actual):
    err=actual.method_sigma
    only=(np.isfinite(err).sum(axis=1)==2)
    mu=actual.method_modulus[only]
    sigma=err[only]
    model=cf.method_information(mu,sigma)
    F=np.zeros((6,6));b=np.zeros(6)
    for row,sd in zip(mu,sigma):
        i,j=np.where(np.isfinite(sd))[0]
        weight=1/(sd[i]**2+sd[j]**2)
        edge=np.zeros(6);edge[i]=1;edge[j]=-1
        F+=weight*np.outer(edge,edge)
        b+=weight*edge*(row[i]-row[j])
    np.testing.assert_allclose(F,model["F"],atol=1e-10,rtol=1e-12)
    np.testing.assert_allclose(b,model["b"],atol=1e-10,rtol=1e-12)


def test_exact_source_array_identity_required_before_claim(actual):
    from dataclasses import replace
    assert cf.validate_source_identity(actual)
    mod=actual.method_modulus.copy()
    mod[[0,10000]]=mod[[10000,0]]
    altered=replace(actual,method_modulus=mod)
    with pytest.raises(ValueError,match="source.*identity|fingerprint"):
        cf.validate_source_identity(altered)
