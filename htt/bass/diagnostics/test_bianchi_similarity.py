from __future__ import annotations
import numpy as np
import pytest
from bass.background.bianchi_types import ALL_BIANCHI_TYPES, all_bianchi_algebras, build_bianchi_algebra
from bass.diagnostics.bianchi_similarity import (
    classify_bianchi_type, geometry_fingerprint, recover_tilt_squared_components,
    spatial_ricci_from_structure_tensor, structure_tensor_from_an, tilt_orbit_fingerprint
)

def _rotation(seed=7):
    rng=np.random.default_rng(seed)
    q,_=np.linalg.qr(rng.normal(size=(3,3)))
    if np.linalg.det(q)<0: q[:,0]*=-1
    return q

@pytest.mark.parametrize("label",ALL_BIANCHI_TYPES)
def test_all_eleven_bianchi_algebras_classify_from_a_n(label):
    algebra=all_bianchi_algebras()[label]
    result=classify_bianchi_type(algebra.a,algebra.n)
    assert result.label==label
    assert np.linalg.norm(algebra.n@algebra.a)<1e-12

def test_type_iii_is_h_minus_one_member_of_vi_h():
    algebra=build_bianchi_algebra("III")
    result=classify_bianchi_type(algebra.a,algebra.n)
    assert result.label=="III"
    assert result.h_parameter==pytest.approx(-1.0)

def test_rotation_and_homothety_invariance():
    algebra=build_bianchi_algebra("VI_h")
    v=np.array([.17,-.23,.31])
    bg=geometry_fingerprint(algebra.a,algebra.n,algebra.C)
    bt=tilt_orbit_fingerprint(algebra.a,algebra.n,v)
    R=_rotation()
    scale=3.7
    aa=scale*R@algebra.a
    nn=scale*R@algebra.n@R.T
    CC=scale*np.einsum("kp,pqr,qi,rj->kij",R,algebra.C,R.T,R.T)
    gg=geometry_fingerprint(aa,nn,CC)
    tt=tilt_orbit_fingerprint(aa,nn,R@v)
    np.testing.assert_allclose([bg.normalized_a_norm,*bg.normalized_n_eigenvalues,*bg.normalized_ricci_eigenvalues],
                               [gg.normalized_a_norm,*gg.normalized_n_eigenvalues,*gg.normalized_ricci_eigenvalues],rtol=0,atol=2e-12)
    np.testing.assert_allclose([bt.speed_squared,bt.p1,bt.p2,bt.class_b_a_dot_v,bt.class_b_a_dot_v_cross_nv],
                               [tt.speed_squared,tt.p1,tt.p2,tt.class_b_a_dot_v,tt.class_b_a_dot_v_cross_nv],rtol=0,atol=2e-12)

def test_curvature_only_exact_cross_type_degeneracies():
    I=build_bianchi_algebra("I"); VII0=build_bianchi_algebra("VII_0")
    V=build_bianchi_algebra("V",a_twist=.8)
    VIIh=build_bianchi_algebra("VII_h",n1=.3,n3=.3,a_twist=.8)
    gI=geometry_fingerprint(I.a,I.n,I.C); gVII0=geometry_fingerprint(VII0.a,VII0.n,VII0.C)
    gV=geometry_fingerprint(V.a,V.n,V.C); gVIIh=geometry_fingerprint(VIIh.a,VIIh.n,VIIh.C)
    assert gI.flat_intrinsic_geometry and gVII0.flat_intrinsic_geometry
    np.testing.assert_allclose(gI.normalized_ricci_eigenvalues,gVII0.normalized_ricci_eigenvalues)
    assert gV.isotropic_intrinsic_curvature and gVIIh.isotropic_intrinsic_curvature
    np.testing.assert_allclose(gV.normalized_ricci_eigenvalues,gVIIh.normalized_ricci_eigenvalues)
    assert classify_bianchi_type(I.a,I.n).label!=classify_bianchi_type(VII0.a,VII0.n).label
    assert classify_bianchi_type(V.a,V.n).label!=classify_bianchi_type(VIIh.a,VIIh.n).label
    np.testing.assert_allclose(spatial_ricci_from_structure_tensor(V.C),
                               spatial_ricci_from_structure_tensor(VIIh.C),rtol=0,atol=1e-12)

def test_class_a_distinct_eigenvalues_identify_tilt_squared_orbit():
    algebra=build_bianchi_algebra("VI_0")
    eig,Q=np.linalg.eigh(algebra.n); v=np.array([.2,-.3,.4]); w=Q.T@v
    fp=tilt_orbit_fingerprint(algebra.a,algebra.n,v)
    recovered,rank,condition=recover_tilt_squared_components(algebra.a,algebra.n,fp.speed_squared,fp.p1,fp.p2)
    assert rank==3 and np.isfinite(condition)
    np.testing.assert_allclose(recovered,w**2,rtol=0,atol=1e-12)
    assert fp.class_a_v_nv_n2v_determinant is not None

def test_class_b_rank_two_tilt_uses_axis_and_chirality():
    algebra=build_bianchi_algebra("III")
    fp=tilt_orbit_fingerprint(algebra.a,algebra.n,np.array([.2,-.3,.4]))
    assert fp.class_b_a_dot_v is not None
    assert fp.class_b_a_dot_v_cross_nv is not None
    assert fp.continuous_azimuth_degeneracy_dof==0

@pytest.mark.parametrize("label,expected",[
    ("I",2),("II",1),("VI_0",0),("VII_0",1),("VIII",1),("IX",2),
    ("IV",0),("V",1),("III",0)
])
def test_tilt_orbit_degeneracy_strata(label,expected):
    algebra=build_bianchi_algebra(label)
    fp=tilt_orbit_fingerprint(algebra.a,algebra.n,np.array([.2,-.3,.4]))
    assert fp.continuous_azimuth_degeneracy_dof==expected

def test_type_vii_h_equal_eigenvalues_has_one_azimuth():
    algebra=build_bianchi_algebra("VII_h",n1=.3,n3=.3,a_twist=.8)
    fp=tilt_orbit_fingerprint(algebra.a,algebra.n,np.array([.2,-.3,.4]))
    assert fp.moment_rank==2 and fp.continuous_azimuth_degeneracy_dof==1

def test_invalid_tilt_speed_and_jacobi_data_fail_closed():
    algebra=build_bianchi_algebra("III")
    with pytest.raises(ValueError): tilt_orbit_fingerprint(algebra.a,algebra.n,np.array([1.,0.,0.]))
    with pytest.raises(ValueError): classify_bianchi_type(np.array([1.,1.,0.]),algebra.n)

@pytest.mark.parametrize("scale",[1e-6,.25,3.7,1e6])
def test_similarity_fingerprint_scale_invariant(scale):
    algebra=build_bianchi_algebra("VI_h")
    base=geometry_fingerprint(algebra.a,algebra.n)
    scaled=geometry_fingerprint(scale*algebra.a,scale*algebra.n)
    np.testing.assert_allclose([base.normalized_a_norm,*base.normalized_n_eigenvalues,*base.normalized_ricci_eigenvalues],
                               [scaled.normalized_a_norm,*scaled.normalized_n_eigenvalues,*scaled.normalized_ricci_eigenvalues],rtol=0,atol=2e-11)
    assert scaled.structure_scale_kappa==pytest.approx(scale*base.structure_scale_kappa)

def test_rank_deficient_moment_map_fails_closed():
    algebra=build_bianchi_algebra("VII_0")
    fp=tilt_orbit_fingerprint(algebra.a,algebra.n,np.array([.2,-.3,.4]))
    assert fp.moment_jacobian_rank==2 and np.isinf(fp.moment_condition_number)
    with pytest.raises(np.linalg.LinAlgError):
        recover_tilt_squared_components(algebra.a,algebra.n,fp.speed_squared,fp.p1,fp.p2)

def test_tilt_axis_cases_no_fake_azimuth():
    algebra=build_bianchi_algebra("V",a_twist=.8)
    f_axis=tilt_orbit_fingerprint(algebra.a,algebra.n,np.array([.3,0.,0.]))
    f_perp=tilt_orbit_fingerprint(algebra.a,algebra.n,np.array([0.,.3,0.]))
    assert f_axis.continuous_azimuth_degeneracy_dof==0
    assert f_perp.continuous_azimuth_degeneracy_dof==1
    I=build_bianchi_algebra("I")
    assert tilt_orbit_fingerprint(I.a,I.n,np.zeros(3)).continuous_azimuth_degeneracy_dof==0

def test_supplied_C_must_match_a_n():
    algebra=build_bianchi_algebra("V")
    wrong=algebra.C.copy(); wrong[0,1,2]+=.2
    with pytest.raises(ValueError): geometry_fingerprint(algebra.a,algebra.n,wrong)


def test_structure_builder_rejects_jacobi_violating_a_n():
    bad_a = np.array([0.4, 0.0, 0.0])
    bad_n = np.diag([1.0, 0.0, 0.0])
    with pytest.raises(ValueError, match="Jacobi"):
        structure_tensor_from_an(bad_a, bad_n)


def test_ricci_ingress_rejects_skew_non_lie_bracket():
    # [e0,e1]=e0 and [e1,e2]=e1 violate Jacobi for (e0,e1,e2).
    C = np.zeros((3, 3, 3), dtype=np.float64)
    C[0, 0, 1] = 1.0
    C[0, 1, 0] = -1.0
    C[1, 1, 2] = 1.0
    C[1, 2, 1] = -1.0
    with pytest.raises(ValueError, match="Jacobi"):
        spatial_ricci_from_structure_tensor(C)


def test_tilt_recovery_rejects_invalid_algebra_and_superluminal_speed():
    algebra = build_bianchi_algebra("III")
    with pytest.raises(ValueError, match="speed_squared"):
        recover_tilt_squared_components(algebra.a, algebra.n, 1.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="Jacobi"):
        recover_tilt_squared_components(
            np.array([0.4, 0.0, 0.0]), np.diag([1.0, 0.0, 0.0]),
            0.2, 0.0, 0.0
        )


@pytest.mark.parametrize("label", ALL_BIANCHI_TYPES)
def test_all_eleven_proper_rotation_and_homothety_invariance(label):
    algebra = all_bianchi_algebras()[label]
    index = list(ALL_BIANCHI_TYPES).index(label)
    R = _rotation(seed=100 + index)
    scale = 2.7
    v = np.array([0.11, -0.17, 0.23])
    base_g = geometry_fingerprint(algebra.a, algebra.n, algebra.C)
    base_t = tilt_orbit_fingerprint(algebra.a, algebra.n, v)
    aa = scale * (R @ algebra.a)
    nn = scale * (R @ algebra.n @ R.T)
    CC = scale * np.einsum("kp,pqr,qi,rj->kij", R, algebra.C, R.T, R.T)
    transformed_g = geometry_fingerprint(aa, nn, CC)
    transformed_t = tilt_orbit_fingerprint(aa, nn, R @ v)
    np.testing.assert_allclose(
        [base_g.normalized_a_norm, *base_g.normalized_n_eigenvalues,
         *base_g.normalized_ricci_eigenvalues],
        [transformed_g.normalized_a_norm, *transformed_g.normalized_n_eigenvalues,
         *transformed_g.normalized_ricci_eigenvalues],
        rtol=0.0, atol=3e-11
    )
    assert transformed_g.type_signature.label == base_g.type_signature.label
    for field in (
        "speed_squared", "p1", "p2", "class_b_a_dot_v",
        "class_b_a_dot_v_cross_nv", "class_a_v_nv_n2v_determinant"
    ):
        x, y = getattr(base_t, field), getattr(transformed_t, field)
        if x is None:
            assert y is None
        else:
            assert y == pytest.approx(x, abs=3e-11)
    assert transformed_t.moment_jacobian_rank == base_t.moment_jacobian_rank
    assert transformed_t.continuous_azimuth_degeneracy_dof == base_t.continuous_azimuth_degeneracy_dof
