"""Source-bound conditional Planck dipole and endpoint frame operations.

The Gaussian error proxy is an explicit approximation to published error
components. It is not the official Planck likelihood or a measured full covariance.
"""
from __future__ import annotations
import numpy as np
from scipy.linalg import cho_factor,cho_solve

T_REF_K=2.72548
C_KM_S=299792.458
A_REF_MICROK=3362.08
L_DEG=264.021
B_DEG=48.253
SOURCES=('https://doi.org/10.1051/0004-6361/201832909',
         'https://doi.org/10.1051/0004-6361/201833880',
         'https://doi.org/10.1088/0004-637X/707/2/916')


def _vector(value):
    if np.iscomplexobj(value):raise ValueError('real three-vector required')
    v=np.asarray(value,dtype=float)
    if v.shape!=(3,) or not np.isfinite(v).all():raise ValueError('finite real three-vector required')
    return v


def direction(l_deg,b_deg):
    l,b=np.deg2rad([l_deg,b_deg])
    if not np.isfinite([l,b]).all() or abs(b)>np.pi/2:raise ValueError('finite Galactic direction required')
    return np.array([np.cos(b)*np.cos(l),np.cos(b)*np.sin(l),np.sin(b)])


def measurement_proxy():
    l,b=np.deg2rad([L_DEG,B_DEG]);a=A_REF_MICROK*1e-6
    n=direction(L_DEG,B_DEG)
    dl=np.array([-np.cos(b)*np.sin(l),np.cos(b)*np.cos(l),0.])
    db=np.array([-np.sin(b)*np.cos(l),-np.sin(b)*np.sin(l),np.cos(b)])
    j=np.column_stack((n,a*dl,a*db))/T_REF_K
    sigma=np.array([.99e-6,*np.deg2rad([.011,.005])])
    return a*n/T_REF_K,(j*sigma)@(j*sigma).T


def log_density(beta, *, extra_dipole):
    """extra_dipole must be supplied, including explicit kinematic-only zero."""
    observed,cov=measurement_proxy()
    b=_vector(beta);extra=_vector(extra_dipole)
    if b@b>=1:raise ValueError('subluminal beta required')
    mean=b+extra
    if mean.shape!=(3,) or not np.isfinite(mean).all():raise ValueError('finite supplied model dipole required')
    factor=cho_factor(cov,lower=True)
    r=observed-mean
    return float(-.5*(r@cho_solve(factor,r)+2*np.log(np.diag(factor[0])).sum()+3*np.log(2*np.pi)))


def physical_reference_dipole(t0_k):
    if not np.isfinite(t0_k) or t0_k<=0:raise ValueError('positive T0 required')
    return (t0_k/T_REF_K)*A_REF_MICROK*direction(L_DEG,B_DEG)


def compose_velocities(u,v):
    """O relative R, given canonical rotation-free R->M and M->O boosts."""
    u=_vector(u);v=_vector(v)
    if u.shape!=(3,) or v.shape!=(3,) or not np.isfinite(np.r_[u,v]).all() or u@u>=1 or v@v>=1:
        raise ValueError('two finite subluminal velocities required')
    g=1/np.sqrt(1-u@u);uv=u@v
    return (u+v/g+g/(g+1)*uv*u)/(1+uv)


def kinematic_quadrupole(beta,t0_microk):
    b=_vector(beta)
    if b.shape!=(3,) or not np.isfinite(b).all() or b@b>=1 or not np.isfinite(t0_microk) or t0_microk<=0:
        raise ValueError('subluminal beta and positive T0 required')
    return t0_microk*(np.outer(b,b)-(b@b)*np.eye(3)/3)


def change_removed_template(map_values,old_d,new_d,directions,processor, *, product_history):
    if not product_history or not product_history.get('dipole_removal_known'):
        raise ValueError('product correction provenance required')
    n=np.asarray(directions,dtype=float)
    if n.ndim!=2 or n.shape[1]!=3 or not np.allclose(np.linalg.norm(n,axis=1),1):raise ValueError('unit sky directions required')
    correction=np.asarray(processor(n@(_vector(old_d)-_vector(new_d))),dtype=float)
    m=np.asarray(map_values,dtype=float)
    if correction.shape!=m.shape or not np.isfinite(correction).all() or not np.isfinite(m).all():raise ValueError('finite matching processed template required')
    return m+correction
