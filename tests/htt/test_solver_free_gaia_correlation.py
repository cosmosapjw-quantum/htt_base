"""Falsifiers for marginal-preserving tangent angular correlation."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

path=Path(__file__).resolve().parents[2]/'scripts/run_solver_free_gaia_correlation.py'
spec=importlib.util.spec_from_file_location('sf_gaia_correlation',path)
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def test_dense_psd_marginals_tangent_and_cartesian_rotations():
    result=g.checks_fixture()
    assert result['dense_relative_error_max']<1e-12
    assert result['source_covariance_eigenvalue_min']>-1e-12
    assert result['marginal_relative_error_max']<1e-12
    assert result['local_tangent_rotation_relative_error']<1e-12
    assert result['global_cartesian_rotation_relative_error']<1e-12
    assert result['block_partition_relative_error']<1e-12


def test_half_angle_meaning_and_coincident_points():
    for angle in g.HALF_ANGLES:
        n,_=g.sky_frame([0,angle],[0,0])
        k=g.kernel_block(n,n,angle)
        np.testing.assert_allclose(np.diag(k),1,rtol=0,atol=0)
        np.testing.assert_allclose(k[0,1],.5,rtol=1e-12,atol=0)
        duplicate=np.repeat(n[:1],3,axis=0)
        np.testing.assert_array_equal(g.kernel_block(duplicate,duplicate,angle),np.ones((3,3)))


def test_colocated_rank_three_limit_and_independent_endpoint():
    n,e=g.sky_frame([0]*4,[0]*4)
    c=np.repeat(np.eye(2)[None],4,axis=0)
    rng=np.random.default_rng(31);m=rng.normal(size=(6,4,2))
    h,v0,a=g.latent_response(m,c,e)
    vc=g.correlated_coefficient_covariance(n,h,5,2)
    expected=np.sum(h,axis=0)@np.sum(h,axis=0).T
    np.testing.assert_allclose(vc,expected,atol=1e-13)
    np.testing.assert_array_equal(g.mixed_covariance(v0,vc,0),v0)
    np.testing.assert_array_equal(g.mixed_covariance(v0,vc,1),vc)
    dense,full=g.dense_fixture(n,a,m,5,1)
    assert np.linalg.matrix_rank(full,tol=1e-10)==2
    np.testing.assert_allclose(vc,dense,atol=1e-13)


@pytest.mark.parametrize('rho',[-.1,1.1,np.nan,np.inf,1j,[.1]])
def test_invalid_rho_fails(rho):
    with pytest.raises(ValueError):g.mixed_covariance(np.eye(6),np.eye(6),rho)


@pytest.mark.parametrize('angle',[0,-1,181,np.nan,np.inf,1j,[5]])
def test_invalid_length_fails(angle):
    with pytest.raises(ValueError):g.kernel_block(np.eye(3),np.eye(3),angle)


@pytest.mark.parametrize('block',[0,4097,True,2.5])
def test_invalid_block_size_fails(block):
    with pytest.raises(ValueError):g.correlated_coefficient_covariance(np.eye(3),np.ones((3,6,3)),5,block)


def test_invalid_covariance_and_frame_fail_without_floor():
    for c in [np.array([[[1,.2],[0,1]]]),np.array([[[1,0],[0,0]]]),np.array([[[1,2],[2,1]]]),np.array([[[1,0],[0,np.nan]]])]:
        with pytest.raises(ValueError):g.principal_root(c)
    with pytest.raises(ValueError):g.sky_frame([0],[91])
    with pytest.raises(ValueError):g.latent_response(np.ones((6,1,2)),np.eye(2)[None],np.ones((1,2,3)))
    with pytest.raises(ValueError):g.correlated_coefficient_covariance(np.array([[2,0,0]]),np.ones((1,6,3)),5)
