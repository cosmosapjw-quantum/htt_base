"""Bounded mathematical preconditions for V03/K03/H02/L03.

MATH_CONDITIONAL only: no actual Gaia proper-motion likelihood, no tilted
Einstein-Boltzmann source, no Planck E2E simulation, no empirical CF4 selection.
"""
import numpy as np

def radial_and_transverse_operators(directions):
    """Velocity field v(x)=J x near observer, physical J [1/s].

    For x=r*n: v_rad/r=n.J.n and proper angular motion mu=P_n J n (1/s).
    Returns A_rad [N,9], A_tan [N,3,9], one joint identity J n.
    """
    n=np.asarray(directions,float)
    if n.ndim!=2 or n.shape[1]!=3 or not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n,axis=1),1,rtol=0,atol=1e-12):raise ValueError('unit directions required')
    Jn=np.einsum('ai,nj->naij',np.eye(3),n).reshape(len(n),3,9)
    rad=np.einsum('ni,nij->nj',n,Jn)
    P=np.eye(3)[None,:,:]-np.einsum('ni,nj->nij',n,n)
    tan=np.einsum('nik,nkj->nij',P,Jn)
    return rad,tan

def visibility_history_design(kernels,grid,history_basis):
    """Toy intensity dipole: y_i = beta_observer + integral d eta g_i(eta) beta_material(eta).
    This is a formal source-history Jacobian ONLY; real polarized transfer includes
    Thomson angular couplings, polarization E/B and all source-frame quantities.
    """
    g=np.asarray(kernels,float);t=np.asarray(grid,float);B=np.asarray(history_basis,float)
    if t.ndim!=1 or len(t)<4 or np.any(np.diff(t)<=0) or g.ndim!=2 or g.shape[1]!=len(t) or B.ndim!=2 or B.shape[1]!=len(t) or np.any(g<0):raise ValueError('source history grid')
    I=np.trapezoid(g,t,axis=1)
    if not np.allclose(I,1,rtol=1e-4,atol=1e-5):raise ValueError('kernel must be normalized before comparison')
    return np.column_stack([np.ones(len(g)),np.trapezoid(g[:,None,:]*B[None,:,:],t,axis=2)])

def common_method_calibration_covariance(group_distance_km,method_family,latent_cov):
    """C_cal=Z V Z^T in squared (km/s)^2. Conditional covariance family only."""
    d=np.asarray(group_distance_km,float);families=np.asarray(method_family)
    V=np.asarray(latent_cov,float)
    if V.ndim!=2 or V.shape[0]!=V.shape[1] or not np.allclose(V,V.T,atol=1e-12) or np.linalg.eigvalsh(V)[0]<-1e-12:raise ValueError('calibration covariance must be PSD')
    names=np.unique(families)
    if V.shape[0]!=len(names) or len(d)!=len(families):raise ValueError('family covariance shape')
    Z=d[:,None]*(families[:,None]==names[None,:])
    return Z@V@Z.T

def simple_null_mixture(n,eta,seed=2026):
    """Empirical proxy: one sky S reused across channels, independent N noise.
    NOT a Planck E2E null. This shows the independence unit difference.
    """
    if n<10 or not 0<=eta<=1: raise ValueError('parameters')
    rng=np.random.default_rng(seed)
    signal=rng.normal(size=(n,1));noise=rng.normal(size=(n,2))
    observed=np.sqrt(eta)*signal+np.sqrt(1-eta)*noise
    return observed,signal,noise
