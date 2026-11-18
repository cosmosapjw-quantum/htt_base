"""Gaia E/B design: tests are synthetic and algebraic, not physical validation."""
import numpy as np
from scripts.r67.gaia_frame import eb_design, accumulate, finalize


def sphere(n=600,seed=123):
    rng=np.random.default_rng(seed)
    ra=rng.uniform(0,2*np.pi,n)
    sin_dec=rng.uniform(-1,1,n)
    dec=np.arcsin(sin_dec)
    return ra,dec


def test_eb_correct_vector_rotation_and_tangency():
    ra,dec=sphere()
    n,B=eb_design(ra,dec)
    omega=np.array([.2,-.1,.05])
    r=np.cross(omega,n)
    e_ra=B[:,0,:3]
    e_dec=B[:,1,:3]
    mu=np.column_stack([np.sum(r*e_ra,axis=1),np.sum(r*e_dec,axis=1)])
    np.testing.assert_allclose(mu,np.einsum('nij,j->ni',B[:, :,3:],omega),atol=1e-14)
    np.testing.assert_allclose(np.sum(n*e_ra,axis=1),0,atol=1e-14)
    np.testing.assert_allclose(np.sum(n*e_dec,axis=1),0,atol=1e-14)


def test_eb_full_sky_injection_recovers_all_six():
    ra,dec=sphere(seed=37)
    _,B=eb_design(ra,dec)
    beta=np.array([.01,-.002,.004,.0003,.003,-.001])
    mu=np.einsum('nij,j->ni',B,beta)
    F,s,chi=accumulate(B,mu,np.full(len(ra),.5),
                       np.full(len(ra),.7),np.full(len(ra),.1))
    res=finalize(F,s,chi,len(ra))
    assert res['rank']==6
    np.testing.assert_allclose(res['coefs_EB_masyr'],beta,atol=1e-14)
    assert abs(res['chi2_per_degree_working'])<1e-12


def test_gaia_real_geometry_rank_optional():
    from pathlib import Path
    from astropy.io import fits
    path=Path('/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits')
    if not path.exists():return
    with fits.open(path,memmap=True) as h:
        t=h[1].data[:5000]
        n,B=eb_design(np.deg2rad(t['ra']),np.deg2rad(t['dec']))
        assert len(n)==5000
        assert np.linalg.matrix_rank(B.reshape(-1,6))==6
