"""Finite linear/quadrature controls. No Planck data are synthesized here."""
import importlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


def api():
    return importlib.import_module('l01_fixed_region_grid_audit')


def test_feature_exists_before_numerical_use():
    assert importlib.util.find_spec('l01_fixed_region_grid_audit') is not None


@pytest.mark.parametrize('ratio', [1, 2, 4])
def test_nested_children_preserve_region_and_area(ratio):
    m = api(); a = np.arange(48) % 3 == 0
    b = m.refine_nested_mask(a, 2, 2*ratio)
    assert b.dtype == np.bool_
    assert b.shape == (48*ratio**2,)
    assert np.all(b.reshape(48,ratio**2) == a[:,None])
    assert b.mean() == a.mean()


@pytest.mark.parametrize('bad', ['order', 'shape', 'type', 'ratio'])
def test_invalid_refinement(bad):
    m=api(); a=np.ones(48,dtype=bool); n=2; h=4
    if bad=='order':h=1
    if bad=='shape':a=a[:-1]
    if bad=='type':a=a.astype(float)
    if bad=='ratio':h=3
    with pytest.raises(ValueError):m.refine_nested_mask(a,n,h)


@pytest.mark.parametrize('chunk', [7, 19, 80])
def test_chunked_projection_agrees_with_independent_lstsq(chunk):
    m=api(); rng=np.random.default_rng(20261017)
    # Blocks must each use [Qchunk,Uchunk], not arbitrary contiguous A rows.
    q=rng.normal(size=(80,6));u=rng.normal(size=(80,6))
    data=rng.normal(size=(2,80,3))*1e-6
    mask=rng.random(80)>.25
    moments=m.Moments(6,3)
    for first in range(0,80,chunk):
        s=slice(first,min(80,first+chunk))
        moments.add(np.vstack([q[s],u[s]]),np.vstack([data[0,s],data[1,s]]),mask[s])
    r=moments.solve(4*np.pi/80)
    a=np.vstack([q[mask],u[mask]]);b=np.vstack([data[0,mask],data[1,mask]])
    expected=np.linalg.lstsq(a,b,rcond=None)[0]
    np.testing.assert_allclose(r['coefficients'],expected,rtol=1e-12,atol=1e-20)
    assert r['normal_residual_relative'] < 1e-14
    assert r['selected_pixels'] == int(mask.sum())


def test_moment_change_identity_and_bound():
    m=api(); g0=np.array([[2.,1.],[1.,3.]]);g1=np.array([[3.,1.],[1.,4.]])
    b0=np.array([[1.,2.],[3.,-1.]]);b1=np.array([[2.,-1.],[1.,4.]])
    old=m.solve_moments(g0,b0,8);new=m.solve_moments(g1,b1,8)
    r=m.moment_change(old,new)
    np.testing.assert_allclose(r['change'],new['coefficients']-old['coefficients'],atol=1e-14)
    assert max(r['identity_residual_relative']) < 1e-14
    assert np.all(np.linalg.norm(r['change'],axis=0) <= r['finite_step_bound_K_CMB']*(1+1e-13))


def test_joint_moment_rescaling_does_not_change_projection():
    m=api();g=np.diag([1.,2.,4.]);b=np.arange(6,dtype=float).reshape(3,2)*1e-9
    a=m.solve_moments(g,b,10);z=m.solve_moments(g/4,b/4,40)
    np.testing.assert_allclose(a['coefficients'],z['coefficients'],atol=0,rtol=1e-14)
    assert np.linalg.norm(m.moment_change(a,z)['change']) < 1e-22


@pytest.mark.parametrize('bad', ['indefinite','asymmetric','singular','illconditioned','nan'])
def test_bad_moments_refused(bad):
    m=api();g=np.eye(3);b=np.ones((3,2))
    if bad=='indefinite':g[0,0]=-1
    if bad=='asymmetric':g[0,1]=.1
    if bad=='singular':g[0,0]=0
    if bad=='illconditioned':g[0,0]=1e-12
    if bad=='nan':b[0,0]=np.nan
    with pytest.raises(ValueError):m.solve_moments(g,b,10)


def test_no_hidden_masked_nonfinite_or_wrong_shape():
    m=api();a=np.eye(4);d=np.ones((4,1));w=np.array([True,False])
    z=m.Moments(4,1)
    with pytest.raises(ValueError):z.add(a,d[:-1],w)
    d[3]=np.nan
    with pytest.raises(ValueError):z.add(a,d,w)


def test_low_signal_recovered_and_mixed_term_response():
    m=api();rng=np.random.default_rng(12);a=rng.normal(size=(100,8));c=rng.normal(size=(8,2))*1e-6
    g=a.T@a;b=g@c
    r=m.solve_moments(g,b,50)
    np.testing.assert_allclose(r['coefficients'],c,rtol=1e-14,atol=1e-20)
    pert=m.solve_moments(1.1*g,1.1*b+1e-5*np.ones_like(b),50)
    change=m.moment_change(r,pert)
    assert max(change['identity_residual_relative']) < 1e-13


def test_baseline_replay_uses_vectors_not_only_norms():
    m=api();x=np.array([[1.,0.],[0.,1.]])*1e-6
    assert m.baseline_residual(x,x,1e-6) == 0
    with pytest.raises(ValueError,match='BASELINE'):
        m.baseline_residual(x,x[::-1],1e-6)


def test_cli_help_without_healpy(tmp_path):
    m=api();r=subprocess.run([sys.executable,m.__file__,'--help'],cwd=tmp_path,capture_output=True,text=True)
    assert r.returncode==0 and '--band-dirs' in r.stdout and '--nsides' in r.stdout


def test_mixed_grid_cutoff_identity_is_exposed():
    m=api(); assert hasattr(m,'mixed_step')
    a=np.array([1.,2.]);cut=np.array([.1,.4]);grid=np.array([.3,-.1])
    np.testing.assert_allclose(m.mixed_step(a,a+cut,a+grid,a+grid+cut),0,atol=1e-15)
    np.testing.assert_allclose(m.mixed_step(a,a+cut,a+grid,a+grid+2*cut),cut,atol=1e-15)


def test_spherical_full_sky_control_reduces_grid_leakage():
    # Actual checked-in Wigner basis and HEALPix RING centers, not fake healpy.
    from spin2_finite import block_design, spin2_shell
    from healpix_ring_coords import pix2ang_ring
    m=api(); errors=[]
    for n in (8,16,32):
        N=12*n*n;z=m.Moments(64,1)
        for first in range(0,N,2048):
            end=min(N,first+2048);theta,phi=pix2ang_ring(n,np.arange(first,end))
            z.add(block_design(theta,phi,2,5),spin2_shell(theta,phi,6)[:,0:1],np.ones(end-first,dtype=bool))
        r=z.solve(4*np.pi/N);errors.append(np.linalg.norm(r['coefficients']))
    assert errors[2] < errors[1] < errors[0]
    assert errors[0]/errors[2]>10
