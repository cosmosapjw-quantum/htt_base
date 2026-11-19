"""R79 pre-DAG preparation: red-green tests for ten typed numerical operations.

Includes deterministic synthetic and exact/source-scoped comparison, not actual
cosmological parameter inference.
"""
import os
import numpy as np
import pytest
from scripts.r67.gaia_frame import accumulate as reference_vsh
from scripts.r68.fiveview_geometry import E,stf_matrix,stf_coordinates

def api():
    from htt.obsstat import pre_dag_fast as x
    return x

def gaussian_case(n=97,p=16,seed=18):
    rng=np.random.default_rng(seed)
    B=np.ascontiguousarray(rng.normal(size=(n,2,p)))
    y=rng.normal(scale=.1,size=(n,2))
    e1=rng.uniform(.3,3.,size=n)
    e2=rng.uniform(.3,3.,size=n)
    rho=rng.uniform(-.7,.7,size=n)
    return B,y,e1,e2,rho

def test_gaia_correlated_weights_matches_original_reference():
    B,y,e1,e2,rho=gaussian_case()
    baseline=reference_vsh(B,y,e1,e2,rho)
    actual=api().accumulate_gaia(B,y,e1,e2,rho)
    for a,b in zip(actual,baseline):
        np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-12)

def test_gaia_native_if_explicitly_compiled_matches_original():
    lib=os.environ.get("HTT_R79_GAIA_SO")
    if lib is None:pytest.skip("Optional native library not built")
    B,y,e1,e2,rho=gaussian_case(n=1007,seed=8)
    baseline=reference_vsh(B,y,e1,e2,rho)
    actual=api().accumulate_gaia(B,y,e1,e2,rho,native_lib=lib)
    for a,b in zip(actual,baseline):
        np.testing.assert_allclose(a,b,rtol=2e-11,atol=1e-10)

@pytest.mark.parametrize("bad",["zero_error","rho_one","nonfinite","shape"])
def test_gaia_invalid_input_rejected_without_partial_result(bad):
    B,y,e1,e2,rho=gaussian_case()
    if bad=="zero_error":e1[0]=0
    elif bad=="rho_one":rho[0]=1
    elif bad=="nonfinite":B[0,1,3]=np.nan
    else:y=y[:-1]
    with pytest.raises(ValueError):
        api().accumulate_gaia(B,y,e1,e2,rho)

def test_fortran_or_numpy_hemisphere_moments_reference():
    n=np.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.],
                [-1.,0.,0.],[0.,-1.,0.],[0.,0.,-1.]])
    w=np.array([1.,2.,3.,4.,5.,6.])
    axis=np.array([0.,0.,1.])
    lib=os.environ.get("HTT_R79_HEMI_SO")
    ans=api().hemisphere_moments(n,axis,weights=w,native_lib=lib)
    upper=n[:,2]>0
    lower=~upper
    for h,mask in enumerate((lower,upper)):
        expected=w[mask]
        np.testing.assert_allclose(ans["weights"][h],expected.sum())
        np.testing.assert_allclose(ans["means"][h],np.average(n[mask],axis=0,weights=expected))
        np.testing.assert_allclose(ans["second"][h],np.einsum("n,ni,nj->ij",expected,n[mask],n[mask])/expected.sum())

@pytest.mark.parametrize("bad",["zero_axis","negative_weights","nonunit"])
def test_hemisphere_invalid_source_rejected(bad):
    n=np.eye(3)
    axis=np.array([0.,0.,1.])
    w=np.ones(3)
    if bad=="zero_axis":axis[:]=0
    elif bad=="negative_weights":w[0]=-1
    else:n[0,0]=2
    with pytest.raises(ValueError):
        api().hemisphere_moments(n,axis,weights=w)

def test_ring_logsumexp_invariant_to_1000_offset_and_axial_null():
    rng=np.random.default_rng(12)
    n=rng.normal(size=(250,3))
    # Each ring has one fixed n_z. The derivatives in z must cancel.
    ids=np.repeat(np.arange(5),50)
    n[:,2]=ids*.2
    e=(n[:,0]>.15)
    logw=rng.normal(size=len(ids))
    totals=np.array([20.,25.,35.,40.,10.])
    a=api().ring_softmax_occupancy(logw,ids,e,totals,directions=n,k=3.)
    b=api().ring_softmax_occupancy(logw+1000,ids,e,totals,directions=n,k=3.)
    np.testing.assert_allclose(a["F"],b["F"],rtol=0,atol=1e-14)
    np.testing.assert_allclose(a["dF_dbeta"],b["dF_dbeta"],rtol=0,atol=1e-13)
    assert abs(a["dF_dbeta"][2])<2e-14

def test_stf_SO3_rotation_preserves_shape_and_tensor_norm():
    R=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    v=np.array([.04,-.02,.015,-.012,.002])
    u=api().rotate_stf(v,R)
    expected=R@stf_matrix(v)@R.T
    np.testing.assert_allclose(stf_matrix(u),expected,rtol=2e-14,atol=1e-15)
    np.testing.assert_allclose(np.linalg.norm(u),np.linalg.norm(v),rtol=1e-14)
    with pytest.raises(ValueError):api().rotate_stf(v,np.diag([-1.,1.,1.]))

def test_confidence_support_uses_joint_ellipsoid_not_independent_boxes():
    mean=np.array([1.,2.])
    cov=np.array([[4.,.9],[.9,3.]])
    row=np.array([[1.,2.],[-1.,1.]])
    lo,up=api().confidence_support(mean,cov,row,cutoff=5.991)
    mid=row@mean
    rad=np.sqrt(5.991*np.einsum("ni,ij,nj->n",row,cov,row))
    np.testing.assert_allclose(lo,mid-rad)
    np.testing.assert_allclose(up,mid+rad)

def test_online_covariance_matches_sample_numpy_across_irregular_chunks():
    rng=np.random.default_rng(77)
    rows=rng.normal(size=(155,5))+.3
    obj=api().OnlineCovariance(5)
    for z in (rows[:17],rows[17:143],rows[143:]):obj.update(z)
    assert obj.count==155
    np.testing.assert_allclose(obj.mean,rows.mean(axis=0),atol=1e-14)
    np.testing.assert_allclose(obj.covariance(),np.cov(rows,rowvar=False),rtol=1e-13,atol=1e-14)
    with pytest.raises(ValueError):api().OnlineCovariance(4).covariance()

def test_photon_psd_detects_invalid_flux_and_missing_flux():
    S=stf_matrix(np.zeros(5))
    x=api().photon_feasibility(S,f=None)
    assert x["admissible"] is None and x["flux_missing"]
    small=api().photon_feasibility(S,f=np.array([.1,0.,0.]))
    large=api().photon_feasibility(S,f=np.array([.9,0.,0.]))
    assert small["admissible"] and not large["admissible"]
    np.testing.assert_allclose(small["pressure_eig"],np.full(3,1/3),atol=1e-14)

def test_codazzi_map_general_class_A_and_exceptional_class_B():
    m=api().codazzi_map(np.zeros(3),np.diag([1.,2.,3.]))
    assert np.linalg.matrix_rank(m)==3
    ex=api().codazzi_map(np.array([1.,0.,0.]),np.diag([0.,3.,-3.]))
    assert np.linalg.matrix_rank(ex)==2
    np.testing.assert_allclose(np.array([0.,3.,3.])@ex,np.zeros(5),atol=1e-14)
    with pytest.raises(ValueError):
        api().codazzi_map(np.ones(3),np.eye(3))

def test_sachs_rhs_flat_and_focusing_conventions():
    J=np.eye(2)*3
    K=np.eye(2)
    state=np.r_[J.ravel(),K.ravel()]
    out=api().sachs_rhs(state,np.eye(2)*.1)
    np.testing.assert_allclose(out[:4],K.ravel())
    np.testing.assert_allclose(out[4:],(-.1*J).ravel())

def test_schur_covariance_spd_and_correlated_cross_block():
    C=np.array([[3.,.8,0.],[.8,2.,.5],[0.,.5,1.]])
    exp=C[1:,1:]-np.outer(C[1:,0],C[0,1:])/C[0,0]
    np.testing.assert_allclose(api().schur_covariance(C,1),exp,rtol=2e-14,atol=1e-14)
    with pytest.raises(ValueError):api().schur_covariance(np.zeros((3,3)),1)

def test_radial_design_rank_and_single_radius_degeneracy():
    rng=np.random.default_rng(33)
    x=rng.normal(size=(150,3));x/=np.linalg.norm(x,axis=1)[:,None]
    var=np.linspace(40.,400.,150)
    A=api().radial_design(var,x,reference_mpc=100.)
    B=api().radial_design(np.ones(150)*150,x,reference_mpc=100.)
    assert A.shape==(150,12)
    assert np.linalg.matrix_rank(A)==12
    assert np.linalg.matrix_rank(B)==9

def test_persistent_default_lane_selects_native_cpp_on_representative_gaia(monkeypatch):
    monkeypatch.delenv("HTT_ANALYSIS_BACKEND",raising=False)
    B,y,e1,e2,rho=gaussian_case(n=5000,p=16,seed=99)
    out=api().accumulate_gaia(B,y,e1,e2,rho)
    ref=reference_vsh(B,y,e1,e2,rho)
    for a,b in zip(out,ref):
        np.testing.assert_allclose(a,b,rtol=2e-11,atol=1e-10)
    assert api().analysis_lane_policy()["mode"]=="auto"
    actual=api().last_backend_receipt()
    assert actual["used"]=="cpp_native"
    assert actual["source_certified"] is True

def test_persistent_default_lane_selects_native_fortran_on_actual_mask_sized_batch(monkeypatch):
    monkeypatch.delenv("HTT_ANALYSIS_BACKEND",raising=False)
    n=np.tile(np.eye(3), (800,1))
    n[::2]*=-1
    w=np.ones(len(n))
    a=api().hemisphere_moments(n,np.array([0.,0.,1.]),weights=w)
    assert a["counts"].sum()==len(n)
    actual=api().last_backend_receipt()
    assert actual["used"]=="fortran_native"
    assert actual["source_certified"] is True

def test_analysis_lane_numpy_override_reverses_native_default(monkeypatch):
    monkeypatch.setenv("HTT_ANALYSIS_BACKEND","numpy")
    B,y,e1,e2,rho=gaussian_case(n=5000,seed=101)
    api().accumulate_gaia(B,y,e1,e2,rho)
    assert api().last_backend_receipt()["used"]=="numpy_reference"
    n=np.tile(np.eye(3),(500,1));n[::2]*=-1
    api().hemisphere_moments(n,np.array([0.,0.,1.]))
    assert api().last_backend_receipt()["used"]=="numpy_reference"

def test_original_gaia_entrypoint_defaults_to_accelerated_lane(monkeypatch):
    monkeypatch.delenv("HTT_ANALYSIS_BACKEND",raising=False)
    from scripts.r67.gaia_frame import accumulate, accumulate_numpy
    B,y,e1,e2,rho=gaussian_case(n=6000,seed=88)
    expected=accumulate_numpy(B,y,e1,e2,rho)
    observed=accumulate(B,y,e1,e2,rho)
    for a,b in zip(observed,expected):
        np.testing.assert_allclose(a,b,rtol=2e-11,atol=1e-10)
    assert api().last_backend_receipt()["used"]=="cpp_native"

def test_unavailable_auto_compiler_is_explicit_numpy_fallback(monkeypatch):
    monkeypatch.delenv("HTT_ANALYSIS_BACKEND",raising=False)
    import htt.obsstat.pre_dag_fast as m
    def unavailable(*args,**kwargs):
        raise RuntimeError("TEST_SIMULATED_COMPILER_UNAVAILABLE")
    monkeypatch.setattr(m,"_certified_cached_native",unavailable,raising=False)
    B,y,e1,e2,rho=gaussian_case(n=5000,seed=76)
    observed=m.accumulate_gaia(B,y,e1,e2,rho)
    ref=reference_vsh(B,y,e1,e2,rho)
    for a,b in zip(observed,ref):
        np.testing.assert_allclose(a,b,rtol=1e-13,atol=1e-13)
    receipt=m.last_backend_receipt()
    assert receipt["used"]=="numpy_reference"
    assert receipt["fallback_reason"].startswith("TEST_SIMULATED_COMPILER_UNAVAILABLE")
