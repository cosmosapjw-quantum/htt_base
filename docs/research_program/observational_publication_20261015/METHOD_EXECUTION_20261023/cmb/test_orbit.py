"""Targeted checks of the retained CMB orbit experiment."""
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.special import sph_harm_y
from scipy.spatial.transform import Rotation


HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("cmb_orbit", HERE/"orbit.py")
orb=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=orb
SPEC.loader.exec_module(orb)
projection=orb.load_module("test_cmb_projection", orb.ROOT/"htt/obsstat/planck_lowell_irrep_projection.py")


def _alm_from_canonical(ell, block):
    alm={(ell,0):complex(block[0])}
    for m in range(1,ell+1):
        a=complex(block[2*m-1],-block[2*m])/np.sqrt(2)
        alm[ell,m]=a
        alm[ell,-m]=(-1)**m*a.conjugate()
    return alm


def _sky(alm, ell, vectors):
    theta=np.arccos(np.clip(vectors[:,2],-1,1))
    phi=np.arctan2(vectors[:,1],vectors[:,0])
    return np.real(sum(alm[ell,m]*sph_harm_y(ell,m,theta,phi) for m in range(-ell,ell+1)))


def _tensor_sky(tensor, ell, vectors):
    if ell==2:
        return np.einsum("ni,ij,nj->n",vectors,tensor,vectors)
    return np.einsum("ni,nj,nk,ijk->n",vectors,vectors,vectors,tensor)


@pytest.mark.parametrize("ell,index",[(ell,index) for ell in (2,3) for index in range(2*ell+1)])
def test_all_12_basis_maps_norms_and_inverse(ell,index):
    # The reference map is evaluated independently through SciPy's complex
    # orthonormal Condon-Shortley harmonics, including the negative-m reality rule.
    block=np.zeros(2*ell+1)
    block[index]=1e-5
    _,q,o=orb.carrier(_alm_from_canonical(ell,block) | _alm_from_canonical(5-ell,np.zeros(2*(5-ell)+1)),projection)
    tensor=q if ell==2 else o
    directions=np.random.default_rng(20261023).normal(size=(64,3))
    directions/=np.linalg.norm(directions,axis=1)[:,None]
    np.testing.assert_allclose(_tensor_sky(tensor,ell,directions),_sky(_alm_from_canonical(ell,block),ell,directions),rtol=2e-14,atol=2e-20)
    expected_norm_factor={2:15/(8*np.pi),3:35/(8*np.pi)}[ell]
    np.testing.assert_allclose(np.linalg.norm(tensor)**2,expected_norm_factor*np.linalg.norm(block)**2,rtol=3e-14)
    inverse=projection.stf2_to_real_harmonic(q) if ell==2 else projection.stf3_to_real_harmonic(o)
    np.testing.assert_allclose(orb.projection_raw_to_canonical(inverse),block,rtol=2e-14,atol=2e-20)


def test_pure_a20_ninety_degree_rotation_has_zero_orbit_distance():
    a=np.zeros(5); a[0]=1e-5
    b=np.zeros(5); b[0]=-5e-6; b[3]=np.sqrt(3/8)*1e-5; b[3]*=np.sqrt(2)
    # b[3] is the canonical sqrt(2) Re a22 coordinate.
    zero=np.zeros(7)
    aa=_alm_from_canonical(2,a) | _alm_from_canonical(3,zero)
    bb=_alm_from_canonical(2,b) | _alm_from_canonical(3,zero)
    np.testing.assert_allclose([bb[2,0].real,bb[2,2].real,bb[2,-2].real],
                               [-5e-6,np.sqrt(3/8)*1e-5,np.sqrt(3/8)*1e-5],rtol=2e-14)
    ca=orb.carrier(aa,projection); cb=orb.carrier(bb,projection)
    r=Rotation.from_euler("y",90,degrees=True).as_matrix()
    np.testing.assert_allclose(cb[1],r@ca[1]@r.T,rtol=2e-14,atol=2e-20)
    directions=np.random.default_rng(12).normal(size=(32,3))
    directions/=np.linalg.norm(directions,axis=1)[:,None]
    np.testing.assert_allclose(_sky(aa,2,directions),_sky(bb,2,directions@r),rtol=2e-14,atol=2e-20)
    interval=orb.orbit_bounds(ca,cb)
    assert interval["lower"]<1e-12
    assert interval["feasible_upper"]<1e-8


@pytest.mark.parametrize("ell",[2,3])
def test_general_proper_rotation_covariance(ell):
    rng=np.random.default_rng(9182+ell)
    block=rng.normal(size=2*ell+1)*1e-5
    alm=_alm_from_canonical(ell,block) | _alm_from_canonical(5-ell,np.zeros(2*(5-ell)+1))
    _,q,o=orb.carrier(alm,projection)
    tensor=q if ell==2 else o
    r=Rotation.from_euler("xyz",[.41,-.28,.73]).as_matrix()
    directions=rng.normal(size=(64,3)); directions/=np.linalg.norm(directions,axis=1)[:,None]
    rotated=r@tensor@r.T if ell==2 else np.einsum("ia,jb,kc,abc->ijk",r,r,r,tensor)
    np.testing.assert_allclose(_tensor_sky(rotated,ell,directions),_sky(alm,ell,directions@r),rtol=3e-14,atol=3e-20)


def test_exact_rotation_and_degenerate_stratum():
    # The bound must survive repeated eigenvalues and a vanishing octupole.
    q=np.diag([2e-7,-1e-7,-1e-7])
    o=np.zeros((3,3,3))
    r=Rotation.from_euler("xyz",[.2,-.3,.5]).as_matrix()
    p=r@q@r.T
    interval=orb.orbit_bounds((None,q,o),(None,p,o))
    assert 0<=interval["lower"]<=interval["feasible_upper"]
    assert interval["lower"]<1e-12
    assert interval["feasible_upper"]<1e-9
    assert interval["SO3_orthogonality_residual"]<1e-12
    assert interval["SO3_determinant_residual"]<1e-12


def test_zero_tensor_stratum():
    zero=(None,np.zeros((3,3)),np.zeros((3,3,3)))
    interval=orb.orbit_bounds(zero,zero)
    assert interval["lower"]==interval["feasible_upper"]==0


def test_retained_result_contract():
    d=json.loads((HERE/"RESULT.json").read_text())
    assert d["packet_id"]==orb.PACKET and d["input_identity"]==orb.INPUT_ID
    assert len(d["bundles"])==60 and len(d["comparisons"])==57
    assert len(d["processing_support"])==9
    assert d["p_value"] is None and d["matched_total_field_law"]=="ABSENT"
    assert d["equal_scalar_phase_control"]["C2_C3_relative_power_residual"]<1e-12
    assert d["equal_scalar_phase_control"]["orbit_interval"]["lower"]>0
    for row in d["comparisons"]:
        bound=row["interval"]
        assert 0<=bound["lower"]<=bound["feasible_upper"]
        assert bound["SO3_orthogonality_residual"]<1e-12
        assert bound["SO3_determinant_residual"]<1e-12
    assert {x["source"] for x in d["bundles"]}=={"hash_pinned_primary","pilot_cached"}
    for row in d["processing_support"]:
        assert len(row["support_plus"])==len(row["support_minus"])==12
        assert row["processing_set_size"]==5
