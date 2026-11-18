"""Scientific semantics and finite algebra checks for R68.

These are mathematical/synthetic verification, not a new cosmic anomaly test.
"""
import numpy as np
import pytest
from scipy.stats import chi2

from scripts.r68.fiveview_geometry import (
    E, stf_matrix, stf_coordinates, stf_shape, radiation_stress_gauge,
    linear_target_identifiability, nuisance_projected_fisher,
    best_axis_quadrupole_statistic, calibrate_axis_null,
    transported_difference_covariance,
    r66_reused_stress
)


def so3(seed=14):
    rng=np.random.default_rng(seed)
    q,_=np.linalg.qr(rng.normal(size=(3,3)))
    if np.linalg.det(q)<0:q[:,0]*=-1
    return q


def test_stf_orthonormal_basis_and_inverse():
    gram=np.einsum("aij,bij->ab",E,E)
    np.testing.assert_allclose(gram,np.eye(5),atol=1e-14)
    rng=np.random.default_rng(42)
    v=rng.normal(size=(10,5))
    np.testing.assert_allclose(stf_coordinates(stf_matrix(v)),v,atol=1e-14)
    with pytest.raises(ValueError,match="trace-free"):
        stf_coordinates(np.eye(3))


def test_shape_invariants_rotation_and_discriminant():
    rng=np.random.default_rng(9)
    R=so3()
    for i in range(30):
        S=stf_matrix(rng.normal(size=5))
        Sp=R@S@R.T
        inv=stf_shape(S); inv2=stf_shape(Sp)
        for name in inv:
            np.testing.assert_allclose(inv[name],inv2[name],atol=1e-11)
        l=np.linalg.eigvalsh(S)
        D=np.prod([(l[a]-l[b])**2 for a,b in ((0,1),(0,2),(1,2))])
        np.testing.assert_allclose(inv["discriminant"],D,atol=1e-11)


def test_orbit_strata_and_signed_shape():
    axial=np.diag([2.,-1.,-1.])
    negative=-axial
    generic=np.diag([1.,0.,-1.])
    np.testing.assert_allclose(stf_shape(axial)["signed_chi"],1.)
    np.testing.assert_allclose(stf_shape(negative)["signed_chi"],-1.)
    np.testing.assert_allclose(stf_shape(generic)["signed_chi"],0.)
    assert np.isclose(stf_shape(axial)["discriminant"],0)
    assert stf_shape(generic)["discriminant"]>0


def test_photon_body_asymmetric_gauge_positive_and_rotation():
    S=np.diag([2/3.,-1/3.,-1/3.])
    assert np.isclose(radiation_stress_gauge(S),1)
    assert np.isclose(radiation_stress_gauge(-S),2)
    R=so3()
    np.testing.assert_allclose(radiation_stress_gauge(R@S@R.T),
                               radiation_stress_gauge(S),atol=1e-14)
    S2=stf_matrix(np.array([.02,-.01,.015,.001,.013]))
    assert radiation_stress_gauge(S2)<1
    assert np.all(np.linalg.eigvalsh(S2+np.eye(3)/3)>0)


def test_gaussian_nuisance_projected_fisher_exact():
    J=np.array([[1],[1]],float)
    N=np.array([[1],[-1]],float)
    F=nuisance_projected_fisher(J,N,np.eye(2))
    np.testing.assert_allclose(F,[[2.]])
    assert np.allclose(nuisance_projected_fisher(J,np.empty((2,0)),np.eye(2)),F)
    with pytest.raises(ValueError):
        nuisance_projected_fisher(J,N,np.ones((2,2)))


def test_linear_target_modulus_and_null():
    A=np.array([[2.,0,0],[0,1.,0]])
    good=linear_target_identifiability(A,[[1,0,0]])
    bad=linear_target_identifiability(A,[[0,0,1]])
    assert good["identified"] and good["nullity"]==1
    assert np.isclose(good["stability_modulus"],.5)
    assert not bad["identified"] and np.isinf(bad["stability_modulus"])


def test_unknown_axis_profile_against_numerical_grid():
    rng=np.random.default_rng(17)
    z=rng.normal(size=5)
    S=stf_matrix(z)
    stat=best_axis_quadrupole_statistic(z)
    l=np.linalg.eigvalsh(S)
    np.testing.assert_allclose(stat,1.5*max(l**2),atol=1e-14)
    n=rng.normal(size=(100000,3))
    n/=np.linalg.norm(n,axis=1)[:,None]
    maxgrid=1.5*np.max((n@S*n).sum(axis=1)**2)
    assert maxgrid<=stat+1e-12
    assert maxgrid>=stat*.98


def test_unknown_axis_null_is_not_chi1():
    p=calibrate_axis_null(draws=10000,seed=19)
    assert 8.5<p["q95"]<11
    assert .44<p["chi1_false_rejection_at_nominal5pct"]<.55
    assert 0<p["chi5_false_rejection_at_nominal5pct"]<.06


def test_depth_transport_needs_cross_covariance():
    Cii=np.array([[.5,.1],[.1,.8]])
    Cjj=np.array([[.8,.1],[.1,.3]])
    Cij=np.array([[.2,.01],[.02,.1]])
    T=np.array([[1,.2],[-.1,1.]])
    joint=np.block([[Cii,Cij],[Cij.T,Cjj]])
    D=np.hstack((-T,np.eye(2)))
    actual=D@joint@D.T
    pred=transported_difference_covariance(Cii,Cjj,Cij,T)
    np.testing.assert_allclose(pred,actual,atol=1e-14)
    assert np.linalg.norm(pred-(Cjj+T@Cii@T.T))>1e-3


def test_real_r66_retained_sky_not_full_physical_law():
    from pathlib import Path
    p=Path("docs/research_program/observational_publication_20261015/R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json")
    if not p.exists():
        pytest.skip("R66 original source not mounted")
    data=r66_reused_stress(p)
    assert data["R66_carrier_identity"]=="807b8eb391b6d150596ab431885f4b720bcafedd52fffdfe61c6db132661cc48"
    assert len(data["results"])==2
    assert all(0<r["gauge_from_positive_intensity"]<.0001 for r in data["results"].values())
    assert data["qualification"].startswith("NOT exact total-sky")
    assert data["R66_source_file_sha256"]=="6d9c3f11a23995565dca25fe8ae02ef1ad79b3bc3f8ddf99f3c8c0a497b39d01"

def test_nuisance_units_invariant_and_duplicate_columns():
    J=np.array([[1.]],float);C=np.eye(1)
    F1=nuisance_projected_fisher(J,np.array([[1.]]),C)
    Fsmall=nuisance_projected_fisher(J,np.array([[1e-12]]),C)
    Fdup=nuisance_projected_fisher(J,np.array([[1e-12,2e-12]]),C)
    np.testing.assert_allclose(F1,[[0.]],atol=1e-12)
    np.testing.assert_allclose(Fsmall,F1,atol=1e-12)
    np.testing.assert_allclose(Fdup,F1,atol=1e-12)


def test_tiny_nonzero_target_leakage_is_never_certified_identified():
    A=np.array([[1.,0.]])
    tiny=linear_target_identifiability(A,[[0.,1e-12]])
    assert tiny["identified"] is None
    assert tiny["numerical_status"]=="NUMERICALLY_AMBIGUOUS_NULL_LEAKAGE"
    assert tiny["stability_modulus"] is None
    exact_bad=linear_target_identifiability(A,[[0.,1.]])
    assert exact_bad["identified"] is False


def test_relative_stf_domain_at_tiny_scale():
    tiny=np.diag([2.,-1.,-1.])*1e-26
    assert np.isclose(stf_shape(tiny)["signed_chi"],1.)
    np.testing.assert_allclose(stf_coordinates(tiny),
                               np.einsum("ij,aij->a",tiny,E),atol=0)
    with pytest.raises(ValueError,match="trace-free"):
        stf_coordinates(np.eye(3)*1e-13)
    with pytest.raises(ValueError,match="trace-free"):
        radiation_stress_gauge(np.eye(3)*1e-13)


def test_r66_byte_hash_fails_closed_on_source_mutation(tmp_path):
    from pathlib import Path
    p=Path("docs/research_program/observational_publication_20261015/R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json")
    if not p.exists():pytest.skip("Original R66 source absent")
    raw=p.read_bytes()
    q=tmp_path/"tampered.json"
    q.write_bytes(raw.replace(b'"T0_K": 2.72548',b'"T0_K": 2.70000',1))
    assert q.read_bytes()!=raw
    with pytest.raises(ValueError,match="byte identity"):
        r66_reused_stress(q)
