import ast
import importlib.util
from pathlib import Path
import subprocess
import numpy as np
import pytest
from scipy.stats import ncx2

s=importlib.util.spec_from_file_location('a22_astrometry',Path(__file__).with_name('model.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def test_dense_woodbury_posterior_and_logdet_with_zero_variance():
    rng=np.random.default_rng(45);z=rng.normal(size=(120,m.NF))*.05;y=rng.normal(size=120)
    # Correlated two-component N, explicitly whitened rather than diagonalized away.
    rawx=z.reshape(60,2,m.NF);rawy=y.reshape(60,2)
    sa=np.linspace(.7,1.4,60);sd=sa[::-1]+.2;rho=np.linspace(-.7,.5,60)
    zw,yw=m.whiten(rawx,rawy,sa,sd,rho);g=zw.T@zw;b=zw.T@yw
    for model in m.family(g)[::7]:
        p=model['p'];c=np.eye(len(zw))+(zw*p)@zw.T
        ci=np.linalg.solve(c,np.eye(len(c)))
        np.testing.assert_allclose(model['R']@b,p*(zw.T@ci@yw),rtol=1e-10,atol=1e-10)
        sign,ld=np.linalg.slogdet(c);assert sign==1 and abs(ld-model['logdet'])<1e-8
        # Independent active-prior precision reference avoids subtracting two
        # ~10000 matrices to recover variances near1. Zero-prior modes stay zero.
        active=p>0;cov=np.zeros_like(g)
        prec=g[np.ix_(active,active)]+np.diag(1/p[active])
        cov[np.ix_(active,active)]=np.linalg.solve(prec,np.eye(active.sum()))
        np.testing.assert_allclose(model['R'],cov,rtol=1e-10,atol=1e-10)
        # Signal GLS after marginalizing only H, using a separate dense C.
        ch=np.eye(len(zw))+(zw[:,m.NG:]*p[m.NG:])@zw[:,m.NG:].T
        wd=np.linalg.solve(ch,zw[:,:m.NG]);wy=np.linalg.solve(ch,yw)
        v=np.linalg.inv(zw[:,:m.NG].T@wd)
        np.testing.assert_allclose(model['gls_cov'],v,rtol=1e-10,atol=1e-10)
        np.testing.assert_allclose(model['gls_map']@b,v@zw[:,:m.NG].T@wy,rtol=1e-10,atol=1e-10)


def test_nondiagonal_prior_basis_reparameterization():
    rng=np.random.default_rng(12);x=rng.normal(size=(40,4));l=rng.normal(size=(4,3));g=x.T@x
    r,ld=m.factor_posterior(g,l)
    transform=rng.normal(size=(4,4))+3*np.eye(4)
    xp=x@transform;lp=np.linalg.solve(transform,l)
    rp,ldp=m.factor_posterior(xp.T@xp,lp)
    np.testing.assert_allclose(x@r@x.T,xp@rp@xp.T,atol=1e-12,rtol=1e-10)
    assert abs(ld-ldp)<1e-10
    with pytest.raises(ValueError):m.lowrank_posterior(g,np.array([1,1,-1,1]))


def test_vsh_full_sphere_orthogonality_and_cartesian_donor():
    u,w=np.polynomial.legendre.leggauss(14);phi=np.arange(32)*360/32
    ra=np.tile(phi,len(u));dec=np.repeat(np.rad2deg(np.arcsin(u)),len(phi));weight=np.repeat(w/64,len(phi))
    h=m.vsh(ra,dec,[2,3,4]);gram=np.einsum('nki,nkj,n->ij',h,h,weight)
    np.testing.assert_allclose(gram,np.eye(42),atol=1e-12,rtol=1e-12)
    x=m.dipole(ra,dec)
    np.testing.assert_allclose(np.einsum('nki,nji->nkj',x,x),np.broadcast_to(2*np.eye(2),(len(ra),2,2)),atol=1e-14,rtol=0)
    text=subprocess.check_output(['git','cat-file','-p','3f237024c57b1369a657821607cb0b1f520bc01e']).decode()
    fn=next(a for a in ast.parse(text).body if isinstance(a,ast.FunctionDef) and a.name=='design')
    scope={'np':np};exec(ast.get_source_segment(text,fn),scope)
    np.testing.assert_allclose(x,scope['design'](ra,dec)[:,:,[3,4,5,0,1,2]],atol=1e-14,rtol=0)


def test_chunk_order_and_gaussian_score_root():
    rng=np.random.default_rng(19);x=rng.normal(size=(100,2,12));y=rng.normal(size=(100,2))
    sa=np.ones(100);sd=np.ones(100)*2;rho=np.ones(100)*.6
    wx,wy=m.whiten(x,y,sa,sd,rho);g=wx.T@wx;b=wx.T@wy
    gs=np.zeros_like(g);bs=np.zeros_like(b)
    for ix in [np.arange(75,100),np.arange(0,25),np.arange(25,75)]:
        xx,yy=m.whiten(x[ix],y[ix],sa[ix],sd[ix],rho[ix]);gs+=xx.T@xx;bs+=xx.T@yy
    np.testing.assert_allclose(gs,g,atol=1e-12,rtol=1e-12);np.testing.assert_allclose(bs,b,atol=1e-12,rtol=1e-12)
    root=m.score_root(g);np.testing.assert_allclose(root@root.T,g,atol=1e-10,rtol=1e-10)


def test_known_cut_bound_against_noncentral_chi_square():
    for mean in [0.,.3,1.]:
        for radius in [.5,2.,5.]:
            actual=ncx2.sf(radius**2,2,mean**2)
            bound=m.radial_cut_failure_bound(radius,mean,1.)
            assert actual<=bound+1e-14
    with pytest.raises(ValueError):m.radial_cut_failure_bound(1,0,0)


def test_singular_signal_is_not_pseudoinverted():
    rng=np.random.default_rng(6);x=rng.normal(size=(120,m.NF));x[:,1]=x[:,0]
    with pytest.raises((np.linalg.LinAlgError,ArithmeticError)):m.family(x.T@x)
