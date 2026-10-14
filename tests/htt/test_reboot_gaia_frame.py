import importlib.util
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag

path=Path(__file__).resolve().parents[2]/'scripts/run_reboot_gaia_frame.py'
spec=importlib.util.spec_from_file_location('gaia_frame',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_sign_and_cross_product_geometry():
    a=m.design(np.array([0.]),np.array([0.]))[0]
    np.testing.assert_allclose(a,[[0,0,1,0,1,0],[0,-1,0,0,0,1]])
    ra,dec=np.deg2rad([33.,-22.]);n=np.array([np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)])
    tangent=np.array([[-np.sin(ra),np.cos(ra),0],[-np.sin(dec)*np.cos(ra),-np.sin(dec)*np.sin(ra),np.cos(dec)]])
    theta=np.arange(6.)/10
    np.testing.assert_allclose(m.design(np.array([33.]),np.array([-22.]))[0]@theta,tangent@(np.cross(theta[:3],n)+theta[3:]-(theta[3:]@n)*n),atol=1e-15)


def test_block_gls_injection_dense_and_unit_permutation():
    rng=np.random.default_rng(16);x=m.design(rng.uniform(0,360,20),rng.uniform(-80,80,20));truth=np.arange(6.)*.02
    c=np.tile(np.array([[.04,.01],[.01,.09]]),(20,1,1));y=x@truth
    result=m.block_fit(x,y,c);np.testing.assert_allclose(result['coefficients_mas_yr'],truth,atol=1e-15)
    flat=x.reshape(-1,6);dense=block_diag(*c);cov=np.linalg.inv(flat.T@np.linalg.solve(dense,flat))
    np.testing.assert_allclose(result['covariance_mas2_yr2'],cov,atol=1e-15)
    idx=rng.permutation(20);scaled=m.block_fit(x[idx],1000*y[idx],1e6*c[idx])
    np.testing.assert_allclose(np.array(scaled['coefficients_mas_yr'])/1000,truth,atol=1e-15)
