"""R82 E2-S05 source-coupled numerical preflight.

The only underlying P1 source is one 2048-row coupled 4-window working law;
the tests do not assert a physically calibrated posterior or Planck independence.
"""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pytest

P1=Path("docs/research_program/observational_publication_20261015/CONTINUATION_20261018/P1/results")
SRC=P1/"paired_functional_arrays.npz"
SNAP=P1/"FUNCTIONAL_SENSITIVITY_RESULT.json"


def prep():
    from htt.obsstat import p1_fast
    return p1_fast


def actual():
    with np.load(SRC,allow_pickle=False) as z:
        return z["q_app"].copy(),z["weights"].copy(),z["sample_id"].copy()


def test_red_identity_original_joint_source_four_windows():
    q,w,ids=actual()
    assert q.shape==(2048,4)
    assert len(np.unique(ids))==len(ids)==2048
    assert abs(w.sum()-1)<1e-15
    assert np.isfinite(q).all() and (q>=0).all()


def test_strict_inequality_known_ties_and_missing_unrenormalized():
    q=np.array([[.5,.8,.4,.8],[np.nan,.2,.6,.2],[.3,.1,np.nan,.2]])
    w=np.array([.2,.3,.5])
    reasons=np.array([[0,0,0,0],[1,0,0,0],[0,0,2,0]],dtype=np.int8)
    got=prep().joint_tail_bounds(q,w,[.5],missing_codes=reasons,native_lib=None)
    np.testing.assert_allclose(got["lower"][0],np.array([0,.2,.3,.2,.5,0]),atol=1e-14)
    np.testing.assert_allclose(got["upper"][0],np.array([.3,.2,.8,.2,1.,0]),atol=1e-14)
    assert got["missing_unmeasured_mass_per_window"][0]==pytest.approx(.3)
    assert got["missing_uncertified_mass_per_window"][2]==pytest.approx(.5)
    assert got["physical_Pi"] is None
    assert got["four_windows_shared_sample_ID"]


def test_physical_all_missing_is_unknown_mass_one_no_fake_event():
    q=np.full((9,4),np.nan)
    w=np.full(9,1/9)
    code=np.ones((9,4),dtype=np.int8)
    out=prep().joint_tail_bounds(q,w,[0.,.5,1.],missing_codes=code,native_lib=None)
    np.testing.assert_allclose(out["lower"],np.zeros((3,6)),atol=1e-14)
    np.testing.assert_allclose(out["upper"],np.ones((3,6)),atol=1e-14)
    assert out["physical_Pi"] is None


@pytest.mark.parametrize("kind",["bad_mass","bad_missing","duplicate_ID","bad_threshold","nonfinite_inf","negative_weight"])
def test_bad_provenance_and_numerics_fail_closed(kind):
    q=np.full((5,4),.3)
    w=np.full(5,.2)
    r=np.zeros((5,4),dtype=np.int8)
    ids=np.array(["a","b","c","d","e"])
    ts=np.array([.2,.4])
    if kind=="bad_mass":w[0]=.4
    elif kind=="bad_missing":q[0,2]=np.nan
    elif kind=="duplicate_ID":ids[4]="b"
    elif kind=="bad_threshold":ts[:]=.2
    elif kind=="nonfinite_inf":q[1,0]=np.inf
    elif kind=="negative_weight":w[0]=-.2
    with pytest.raises((ValueError,TypeError)):
        prep().joint_tail_bounds(q,w,ts,missing_codes=r,sample_ids=ids,native_lib=None)


def test_original_2048_real_source_strict_tail_exact_archived_values():
    q,w,ids=actual()
    summary=json.loads(SNAP.read_text())
    ts=np.array([row["threshold"] for row in summary["strict_exceedance"]])
    result=prep().joint_tail_bounds(q,w,ts,sample_ids=ids,native_lib=None)
    assert result["unknown_mass_per_window"]==[0,0,0,0]
    for k,row in enumerate(summary["strict_exceedance"]):
        np.testing.assert_allclose(result["lower"][k,:4],row["per_window"],rtol=0,atol=2e-14)
        assert result["lower"][k,4]==pytest.approx(row["any_window"],abs=2e-14)
        assert result["lower"][k,5]==pytest.approx(row["all_windows"],abs=2e-14)
    np.testing.assert_allclose(result["lower"],result["upper"],rtol=0,atol=2e-14)
    assert result["physical_Pi"] is None


def test_original_2048_Cpp_source_tail_if_optional_native():
    lib=os.environ.get("HTT_R82_TAIL_SO")
    if not lib:pytest.skip("R82 native C++ not built")
    q,w,ids=actual()
    ts=np.linspace(0,.12,256)
    base=prep().joint_tail_bounds(q,w,ts,sample_ids=ids,native_lib=None)
    for threads in (1,4,8):
        got=prep().joint_tail_bounds(q,w,ts,sample_ids=ids,native_lib=lib,threads=threads)
        for key in ("lower","upper"):
            np.testing.assert_allclose(got[key],base[key],atol=2e-11,rtol=2e-11)
        assert got["physical_Pi"] is None


def test_floor_anchor_product_identity_and_original_tie_contract():
    q=np.array([[.0,.0,.02,.05],[.03,.03,.1,.04]])
    w=np.array([.4,.6])
    a=prep().floor_depth_grid(q,w,[.05,.1],[.5,.25],native_lib=None)
    np.testing.assert_array_equal(a["strict_above_one"][0,0],a["strict_above_one"][1,1])
    np.testing.assert_array_equal(a["tie_one"][0,0],a["tie_one"][1,1])
    np.testing.assert_allclose(a["mean_ratio"][0,0],a["mean_ratio"][1,1],atol=0,rtol=0)
    # source first row q0=q1=0 is clipped to anchor*floor in both numerator & denominator
    assert a["tie_one"][0,0,0]>=.4
    assert a["physical_GF"] is None


def test_original_saved_floor_cumulative_joint_draws():
    q,w,ids=actual()
    summary=json.loads(SNAP.read_text())
    floors=[row["floor"] for row in summary["floor_depth_sensitivity"]]
    out=prep().floor_depth_grid(q,w,[.05],floors,native_lib=None)
    for j,row in enumerate(summary["floor_depth_sensitivity"]):
        np.testing.assert_allclose(out["strict_above_one"][0,j],row["strict_mass_above_1"],atol=2e-14,rtol=0)
        np.testing.assert_allclose(out["tie_one"][0,j],row["tie_mass_at_1"],atol=2e-14,rtol=0)


def test_original_2048_Fortran_floor_source_parity_optional():
    lib=os.environ.get("HTT_R82_FLOOR_SO")
    if not lib:pytest.skip("R82 Fortran native not built")
    q,w,ids=actual()
    anchors=np.linspace(.025,.1,13)
    floors=np.linspace(.1,1.5,18)
    a=prep().floor_depth_grid(q,w,anchors,floors,native_lib=None)
    for threads in (1,4,8):
        b=prep().floor_depth_grid(q,w,anchors,floors,native_lib=lib,threads=threads)
        for field in ("strict_above_one","tie_one","mean_ratio"):
            np.testing.assert_allclose(a[field],b[field],atol=2e-11,rtol=2e-11)


def test_E2_E3_X01_X02_X03_S01_protected_source_evidence():
    result=prep().historical_evidence_21_30()
    ids=[str(i) for i in ("E2","E3","X01","X02","X03","S01","S02","S03","S04","S05")]
    assert set(result["science_nodes"])==set(ids)
    assert result["science_nodes"]["S02"]=="blocked_input"
    assert result["E2_planck_same_sky_maps"]==9
    assert result["E2_planck_selected_pixels"]==26846
    assert result["X03_new_observational_null"]=="NOT_REGISTERED_FOR_NEW_OBSERVATIONAL_NULL"
    assert result["original_R78_science_status_changed"] is False
    assert result["actual_observed_physical_x_C"] is False


def test_finite_depth_invalid_inputs_and_sign_clean_not_clipped():
    q=np.ones((5,4))
    w=np.full(5,.2)
    with pytest.raises(ValueError):
        prep().floor_depth_grid(q,w,[0.],[.5])
    with pytest.raises(ValueError):
        prep().floor_depth_grid(q,w,[.1],[-.5])
    with pytest.raises(ValueError):
        prep().floor_depth_grid(np.full((5,4),-1.),w,[.1],[.1])
