"""R84 H04-H06 / V01-V06 / B01 source-conditioned preflight tests.

Original R65/R74 NVSS 33k/185 rings/3 bins; no physical velocity/null inferred.
"""
import json
import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy import units as u
from htt.obsstat.pre_dag_fast import ring_softmax_occupancy


def new():
    from htt.obsstat import p4_bianchi_fast
    return p4_bianchi_fast


@pytest.fixture(scope="module")
def actual():
    from scripts.r84.bench_baseline import source
    n,counts,groups,k,V,old=source()
    cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
    axis=np.array([np.cos(cmb.dec.rad)*np.cos(cmb.ra.rad),
                   np.cos(cmb.dec.rad)*np.sin(cmb.ra.rad),np.sin(cmb.dec.rad)])
    return n,counts,groups,k,V,old,axis


def test_source_3bin_185rings_original_weights_sum_one_and_zero_score(actual):
    n,c,g,k,V,old,axis=actual
    src=new().prepare_ring_source(n,g,c,V,k)
    assert src["weight"].shape==(33000,3)
    assert src["score"].shape==(33000,3,3)
    np.testing.assert_allclose(src["weight"].sum(axis=0),np.ones(3),atol=2e-13)
    np.testing.assert_allclose(src["score"].sum(axis=0),np.zeros((3,3)),atol=3e-13)
    assert src["ring_count"]==185


def test_original_R74_source_CMB_axis_exact_conditional_F_and_gradient(actual):
    n,c,g,k,V,old,axis=actual
    prepared=new().prepare_ring_source(n,g,c,V,k)
    ans=new().batch_ring_occ(n,axis[None,:],prepared,native_lib=None)
    assert ans["F"].shape==(1,3) and ans["gradient"].shape==(1,3,3)
    for band in range(3):
        saved=old["actual_R65_masked_F_response"]["source_geometry_and_exact_ring_z_null"][f"bin_{band+1}"]
        np.testing.assert_allclose(ans["F"][0,band],saved["F_ring_predicted_at_beta0"],atol=2e-13,rtol=0)
        np.testing.assert_allclose(ans["gradient"][0,band],saved["F_ring_kinematic_score_gradient"],atol=2e-12,rtol=0)
    assert ans["physical_beta_measured"] is False and ans["physical_Pi"] is None


def test_R74_conditional_beta_derivative_finite_difference_original_source(actual):
    n,c,g,k,V,old,axis=actual
    baseline=new().prepare_ring_source(n,g,c,V,k)
    grad=new().batch_ring_occ(n,axis[None,:],baseline,native_lib=None)["gradient"][0]
    step=1e-5
    for coord in range(3):
        delta=np.zeros(3);delta[coord]=step
        pos=new().prepare_ring_source(n,g,c,V,k,beta=delta)
        neg=new().prepare_ring_source(n,g,c,V,k,beta=-delta)
        fp=new().batch_ring_occ(n,axis[None,:],pos,native_lib=None)["F"][0]
        fm=new().batch_ring_occ(n,axis[None,:],neg,native_lib=None)["F"][0]
        np.testing.assert_allclose((fp-fm)/(2*step),grad[:,coord],atol=3e-8,rtol=0)


def test_multi_axis_native_fortran_same_source_and_worker_stability(actual):
    import os
    lib=os.environ.get("HTT_R84_SCORE_SO")
    if not lib:pytest.skip("certified R84 Fortran library not yet compiled")
    from scripts.r84.bench_baseline import axes
    n,c,g,k,V,_,axis=actual
    base=new().prepare_ring_source(n,g,c,V,k)
    ax=np.vstack([axis,axes(48)])
    ref=new().batch_ring_occ(n,ax,base,native_lib=None)
    previous=None
    for workers in (1,4,8):
        got=new().batch_ring_occ(n,ax,base,native_lib=lib,threads=workers)
        np.testing.assert_allclose(got["F"],ref["F"],atol=2e-12,rtol=0)
        np.testing.assert_allclose(got["gradient"],ref["gradient"],atol=2e-11,rtol=0)
        if previous is not None:
            np.testing.assert_array_equal(previous,got["F"])
        previous=got["F"]


def test_group_identity_permutation_is_invariant_and_all_sky_score_zero(actual):
    n,c,g,k,V,old,axis=actual
    rng=np.random.default_rng(84)
    order=rng.permutation(len(n))
    original=new().prepare_ring_source(n,g,c,V,k)
    shuffled=new().prepare_ring_source(n[order],g[order],c[:,order],V,k)
    a=new().batch_ring_occ(n,np.vstack([axis,-axis]),original,native_lib=None)
    b=new().batch_ring_occ(n[order],np.vstack([axis,-axis]),shuffled,native_lib=None)
    np.testing.assert_allclose(a["F"],b["F"],atol=4e-12,rtol=0)
    np.testing.assert_allclose(a["gradient"],b["gradient"],atol=4e-12,rtol=0)
    # A and its complement partition exactly unless a pixel lies on the boundary.
    np.testing.assert_allclose(a["F"].sum(axis=0),np.ones(3),atol=3e-12)
    np.testing.assert_allclose(a["gradient"].sum(axis=0),np.zeros((3,3)),atol=3e-12)


def test_bad_source_group_or_normalization_is_rejected(actual):
    n,c,g,k,V,*_=actual
    with pytest.raises(ValueError):
        new().prepare_ring_source(n,g+1,c,V,k)
    bad=c.copy();bad[0,0]=-10
    with pytest.raises(ValueError):
        new().prepare_ring_source(n,g,bad,V,k)
    with pytest.raises(ValueError):
        new().prepare_ring_source(n*2,g,c,V,k)


def test_original_Bianchi_11_canonical_jacobi_codazzi_and_exception():
    r=new().validate_bianchi_registry()
    assert r["canonical_count"]==11
    assert r["all_Jacobi_N_a_zero"]
    assert all(0<=e["Lie_codazzi_rank"]<=3 for e in r["canonical"])
    assert r["exceptional_VI_minus_1_over_9"]["distinct_twelfth_type"] is False
    assert r["exceptional_VI_minus_1_over_9"]["source_specific_rank"]==2
    assert r["external_all_m_polarization_verified"] is False


def test_independent_local_global_information_rank_not_from_normalized_null():
    C=np.eye(6)
    L=np.eye(6)[:,:2]
    G=np.column_stack((L[:,0],np.eye(6)[:,4]))
    result=new().source_conditional_local_global_rank(L,G,C)
    assert result["rank_local"]==2 and result["rank_increment_global"]==1
    assert result["physical_tilt_identified"] is False
    assert result["physical_Pi"] is None
    with pytest.raises(ValueError):
        new().source_conditional_local_global_rank(L,G,np.zeros((6,6)))


def test_historical_H04_P4_hold_and_B01_scoped_states():
    x=new().historical_41_50_status()
    assert x["science_nodes"]["H04"]=="pending"
    assert x["science_nodes"]["V01"]=="completed_scoped"
    assert x["science_nodes"]["V04"]=="pending"
    assert x["science_nodes"]["B01"]=="completed_scoped"
    assert x["next_actual_science_ID"]=="SQ-CF4"
    assert x["new_observational_physical_Pi"] is None
    assert x["H04_complete_PV_selection_covariance"] is None


def test_actual_96axis_default_auto_uses_certified_fortran(actual,monkeypatch):
    from scripts.r84.bench_baseline import axes
    monkeypatch.delenv("HTT_ANALYSIS_BACKEND",raising=False)
    n,c,g,k,V,_,axis=actual
    src=new().prepare_ring_source(n,g,c,V,k)
    out=new().batch_ring_occ(n,np.vstack([axis,axes(96)]),src)
    receipt=new().last_p4_receipt()
    assert receipt["used"]=="fortran_native_ring_score"
    assert receipt["source_certified"] and receipt["threads"]==12
    assert out["physical_Pi"] is None and out["actual_physical_GF"] is None


def test_source_SHA_mutation_auto_numpy_fallback_without_reusing_native(actual,monkeypatch,tmp_path):
    from scripts.r84.bench_baseline import axes
    n,c,g,k,V,_,_=actual
    src=new().prepare_ring_source(n,g,c,V,k)
    library=new()
    original=library.SOURCE
    changed=tmp_path/"changed_p4.f90"
    changed.write_bytes(original.read_bytes()+b"\n! intentionally uncertified change\n")
    monkeypatch.setattr(library,"SOURCE",changed)
    monkeypatch.setenv("HTT_ANALYSIS_BACKEND","auto")
    out=library.batch_ring_occ(n,axes(20),src)
    receipt=library.last_p4_receipt()
    assert out["F"].shape==(20,3)
    assert receipt["used"]=="numpy_block_blas_ring_score"
    assert not receipt["source_certified"]
    assert "uncertified_R84_Fortran_source_SHA_changed" in receipt["fallback_reason"]
