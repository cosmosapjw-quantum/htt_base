"""Exact one-event covariant photon energy-loss angular operator (-,+,+,+).

At a local u=(1,0,0,0) tetrad, nabla_a u_b = -u_a A_b +
(Theta/3)h_ab+sigma_ab+omega_ab. For a future incoming photon
k^a=E(u^a+e^a) and sky look n=-e:
  -d ln E/dt_u = Theta/3 - A_i n^i + sigma_ij n^i n^j.
The antisymmetric omega cancels instantaneously; it can change the
direction transport and thus integrated cosmological observations.
All rates in s^-1, sky unit basis spatial epsilon_123=+1.

This is a mathematically exact local photon-source/congruence operator,
NOT an observational inference of cosmic shear, 4-acceleration, tilt
or H_eff from CF4 catalogue distances.
"""
from __future__ import annotations
import numpy as np
from .cf4_apparent_kinematic_distribution import stf2_orthonormal
from .htt_kinematic_radial_identification import (
    antisymmetric_basis,radial_velocity_jet,split_local_velocity_gradient,MPC_KM
)


class OpticalKinematicsError(ValueError):
    pass


def scalar(x,name):
    a=np.asarray(x)
    if a.ndim or np.iscomplexobj(a) or not np.isfinite(a).all():
        raise OpticalKinematicsError(f"{name}: finite real scalar required")
    return float(a)


def vector(x,name):
    a=np.asarray(x)
    if a.shape!=(3,) or np.iscomplexobj(a) or not np.isfinite(a).all():
        raise OpticalKinematicsError(f"{name}: finite real 3-vector required")
    return np.asarray(a,float)


def tensor(x,name,*,sym):
    a=np.asarray(x)
    if a.shape!=(3,3) or np.iscomplexobj(a) or not np.isfinite(a).all():
        raise OpticalKinematicsError(f"{name}: finite real 3x3 tensor required")
    a=np.asarray(a,float)
    scale=max(float(np.linalg.norm(a)),1e-25)
    if sym:
        if np.max(abs(a-a.T))>1e-12*scale or abs(np.trace(a))>1e-12*scale:
            raise OpticalKinematicsError("sigma symmetric trace-free required")
    elif np.max(abs(a+a.T))>1e-12*scale:
        raise OpticalKinematicsError("omega antisymmetric required")
    return a


def unit_sky(look):
    n=np.asarray(look)
    if (n.ndim!=2 or n.shape[1]!=3 or np.iscomplexobj(n)
        or not np.isfinite(n).all()
        or not np.allclose(np.sum(n*n,axis=1),1,atol=2e-11,rtol=0)):
        raise OpticalKinematicsError("finite Nx3 sky look unit vectors")
    return np.asarray(n,float)


def nabla_u(theta_s_inv,sigma_s_inv,omega_s_inv,accel_s_inv):
    """(nabla_a u_b) local tetrad, u^a=(1,0,0,0)."""
    t=scalar(theta_s_inv,"Theta")
    s=tensor(sigma_s_inv,"sigma",sym=True)
    w=tensor(omega_s_inv,"omega",sym=False)
    a=vector(accel_s_inv,"A")
    C=np.zeros((4,4))
    C[0,1:]=a
    C[1:,1:]=t/3*np.eye(3)+s+w
    return C


def optical_rate(look,*,theta_s_inv,sigma_s_inv,omega_s_inv,accel_s_inv):
    """Instantaneous negative d ln E/dt_u along photon, in s^-1.

    DO NOT apply directly as a measured CF4 luminosity-distance Hubble
    factor: a source-distance transfer is needed.
    """
    n=unit_sky(look)
    C=nabla_u(theta_s_inv,sigma_s_inv,omega_s_inv,accel_s_inv)
    k=np.column_stack((np.ones(len(n)),-n))
    full=np.einsum("ni,ij,nj->n",k,C,k,optimize=True)
    terms={"expansion":np.full(len(n),scalar(theta_s_inv,"Theta")/3),
           "acceleration_dipole":-n@vector(accel_s_inv,"A"),
           "shear_quadrupole":np.einsum("ni,ij,nj->n",n,
                          tensor(sigma_s_inv,"sigma",sym=True),n,optimize=True)}
    delta=full-sum(terms.values())
    if max(abs(delta))>3e-12*max(float(max(abs(full))),1e-20):
        raise OpticalKinematicsError("antisymmetric omega did not cancel")
    return {"negative_dlnE_dt_u_s_inv":full,"terms":terms,
            "omega_residual_s_inv":delta,
            "scope":"EXACT_ONE_EVENT_NULL_PHOTON_KINEMATICS_NO_OPTICAL_HISTORY",
            "look_is_minus_propagation":True}


def sigma_over_H(sigma_s_inv,H_s_inv):
    """Sigma=|sigma|/H with |sigma|=sqrt(sigma_ij sigma_ij /2)."""
    s=tensor(sigma_s_inv,"sigma",sym=True)
    h=scalar(H_s_inv,"H")
    if h<=0:raise OpticalKinematicsError("expanding H>0 required for Sigma")
    return float(np.sqrt(np.sum(s*s)/2)/h)


def optical_design(look):
    """Columns H, A_x/y/z, STF5 shear, vorticity3 (exact zeros)."""
    n=unit_sky(look)
    T=stf2_orthonormal()
    w=antisymmetric_basis()
    mat=np.column_stack([np.ones(len(n)),-n,
        np.einsum("ni,kij,nj->nk",n,T,n,optimize=True),
        np.einsum("ni,kij,nj->nk",n,w,n,optimize=True)])
    if np.max(abs(mat[:,9:]))>3e-14:
        raise OpticalKinematicsError("omega columns must cancel")
    return mat


def angular_rank(look):
    n=unit_sky(look)
    if len(n)<13:raise OpticalKinematicsError(">=13 unit directions required")
    X=optical_design(n)
    sv=np.linalg.svd(X[:,:9],compute_uv=False)
    rank=int(np.sum(sv>sv[0]*1e-11))
    return {"source_directions":len(n),"rank_H_A3_sigma5":rank,
            "rank_omega3":0,"omega_nullity":3,
            "singular_values_H_A3_sigma5":sv,
            "angular_condition_H_A_sigma":float(sv[0]/sv[-1]),
            "source_scope":"SIGHTLINE_GEOMETRY_NOT_CF4_OPTICAL_DRIFT_OR_SHEAR_LIKELIHOOD"}


def acceleration_vs_boost_dipole_span(look):
    """Pure angular rank; A [s^-1] and beta [1] physical laws differ."""
    n=unit_sky(look)
    a=-n
    b=n
    singular=np.linalg.svd(np.column_stack([a,b]),compute_uv=False)
    rank=int(np.sum(singular>singular[0]*1e-11))
    return {"angular_columns":6,"rank":rank,
            "angular_nullity":6-rank,
            "A_units":"s^-1","beta_units":"dimensionless",
            "physical_equivalence":"NOT_ESTABLISHED_DIFFERENT_SOURCE_KERNEL_AND_TIME_HISTORY"}


def euclidean_jet_limit(look,gradient_km_s_Mpc):
    """Same angular form as earlier Euclidean jet, but not same cosmology."""
    n=unit_sky(look)
    g=split_local_velocity_gradient(gradient_km_s_Mpc)
    optical=optical_rate(n,theta_s_inv=g["Theta_s_inv"],
        sigma_s_inv=g["sigma_s_inv"],
        omega_s_inv=g["omega_tensor_km_s_Mpc"]/MPC_KM,
        accel_s_inv=np.zeros(3))["negative_dlnE_dt_u_s_inv"]
    jet=radial_velocity_jet(n,gradient_km_s_Mpc)/MPC_KM
    err=float(np.max(abs(optical-jet)))
    if err>2e-12*max(float(np.max(abs(jet))),1e-23):
        raise OpticalKinematicsError("jet to one-event optical angular limit differs")
    return {"maxabs_error_s_inv":err,
            "source_rate_s_inv":optical,
            "jet_angular_limit_s_inv":jet,
            "physical_CF4_Hubble_equivalence":"NOT_ESTABLISHED"}
