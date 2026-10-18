"""Theorem-matched checks for the observational boost bridge."""
from __future__ import annotations

import numpy as np
import pytest

from obsstat.boost_response import first_order_quadrupole_boost
from obsstat.lorentz_sky_pullback import pullback_thermodynamic_temperature_field
from obsstat.processed_boost_theory_bridge import (
    ProcessedBoostBridgeError, first_order_sky_generator,
    fisher_with_high_mode_stress, processed_boost_jacobian,
    real_harmonics_with_gradients,
)
from obsstat.r7_cmb_product_response import real_design


def _sky(count=270, seed=572):
    n = np.random.default_rng(seed).normal(size=(count, 3))
    return n/np.linalg.norm(n, axis=1, keepdims=True)


def test_exact_harmonic_layout_and_spherical_derivatives():
    n = _sky()
    y, dt, dp = real_harmonics_with_gradients(n, lmax=5)
    np.testing.assert_allclose(y, real_design(n, ell_max=5), rtol=0, atol=2e-13)
    assert y.shape == (270, 36)
    rng = np.random.default_rng(1)
    a = rng.normal(size=y.shape[1])
    beta = np.array([.37, -.28, .11])
    g = first_order_sky_generator(n, (y, dt, dp), a)
    assert np.isfinite(g).all()
    h=2e-5
    sky = lambda x: 800. + real_design(x, ell_max=5) @ a
    exact_plus = pullback_thermodynamic_temperature_field(n, h*beta, sky)
    exact_minus = pullback_thermodynamic_temperature_field(n, -h*beta, sky)
    # The monopole 800 is omitted from input a: include its n term on the RHS.
    np.testing.assert_allclose((exact_plus-exact_minus)/(2*h), g@beta+800.*(n@beta), rtol=3e-7, atol=8e-5)


def test_quadrupole_to_octupole_plus_dipole_independent_oracle():
    n=_sky(360,75)
    q=np.array([[1.7, .2, -.4],[.2,-.6,.3],[-.4,.3,-1.1]])
    beta=np.array([.002,-.001,.003])
    a=np.linalg.lstsq(real_design(n,ell_max=2),
                      np.einsum('ni,ij,nj->n',n,q,n),rcond=None)[0]
    # Only l2 is present.
    a[:4]=0.
    packet=real_harmonics_with_gradients(n,lmax=2)
    g=first_order_sky_generator(n,packet,a)@beta
    expected=first_order_quadrupole_boost(q,beta,n)
    np.testing.assert_allclose(g,expected,rtol=3e-13,atol=3e-14)


def test_monopole_dipole_are_removed_by_joint_fit():
    n=_sky(400,40)
    y=real_design(n,ell_max=5)
    p=np.linalg.pinv(y)
    source=n*123.
    out=processed_boost_jacobian(source,np.ones(len(n),bool),p)
    assert out.shape==(32,3)
    assert np.max(np.abs(out))<1e-11


def test_fisher_decreases_under_additional_high_mode_covariance():
    rng=np.random.default_rng(87)
    j=rng.normal(size=(32,3))
    z=rng.normal(size=(32,32))
    c=z@z.T+2*np.eye(32)
    k=rng.normal(size=(32,12))
    infos=[fisher_with_high_mode_stress(j,c,k,s) for s in (0, .3,2.,8.)]
    for prior,after in zip(infos,infos[1:]):
        assert np.linalg.eigvalsh(prior-after).min()>-2e-11
    assert np.linalg.eigvalsh(infos[0]).min()>0
    with pytest.raises(ProcessedBoostBridgeError):
        fisher_with_high_mode_stress(j,c,k,-.1)


def test_pole_and_nonunit_fail_closed():
    with pytest.raises(ProcessedBoostBridgeError,match='pole'):
        real_harmonics_with_gradients(np.array([[0.,0.,1.]]),lmax=3)
    with pytest.raises(ProcessedBoostBridgeError,match='unit'):
        real_harmonics_with_gradients(np.array([[1.,1.,1.]]),lmax=3)


def test_independent_healpy_harmonic_and_spin_derivative_oracle():
    """Independent HEALPix libsharp path vs SciPy sph_harm_y derivatives."""
    hp=pytest.importorskip('healpy')
    n=np.column_stack(hp.pix2vec(8,np.arange(hp.nside2npix(8))))
    lmax=6
    y,dt,dp=real_harmonics_with_gradients(n,lmax=lmax)
    rng=np.random.default_rng(20261015)
    a=rng.normal(size=(lmax+1)**2)
    alm=np.zeros(hp.Alm.getsize(lmax),dtype=complex)
    j=0
    for ell in range(lmax+1):
        alm[hp.Alm.getidx(lmax,ell,0)]=a[j]
        j+=1
        for m in range(1,ell+1):
            alm[hp.Alm.getidx(lmax,ell,m)]=(a[j]-1j*a[j+1])/np.sqrt(2)
            j+=2
    m,td,pd=hp.alm2map_der1(alm,8,lmax=lmax)
    np.testing.assert_allclose(m,y@a,rtol=0,atol=1e-12)
    np.testing.assert_allclose(td,dt@a,rtol=0,atol=1e-12)
    np.testing.assert_allclose(pd,dp@a,rtol=0,atol=1e-12)
