"""K03 nonradial PROPER-MOTION READINESS in a local Euclidean 1+3 jet limit.

For v_i(r n)=r G_ij n_j in a small-neighborhood Euclidean jet,
radial redshift sees n_i G_ij n_j (omega antisym zero).
A hypothetical measured transverse proper motion would see
  mu_tangent(n)=(I-nn^T) G n
in km/s/Mpc (divide by MPC_KM to get rad/s).

Shear STF5 produces a sphere-gradient E-type tangential field,
antisymmetric omega3 produces a divergence-free B-type field.
For full sky their overlap integral is zero (T symmetric vs W skew).
A real *CF4 SKY POSITION sample* can have nonzero E/B mixing.
CF4 source DOES NOT CONTAIN PROPER MOTIONS; this checks angular
preflight geometry and recovery only, not data inference, nor full GR
Bianchi photon polarization/collision/velocity transfer.
"""
from __future__ import annotations
import numpy as np
from scipy.linalg import eigh
from .cf4_apparent_kinematic_distribution import stf2_orthonormal
from .htt_kinematic_radial_identification import antisymmetric_basis,MPC_KM


class ProperMotionPreflightError(ValueError):
    pass


def unit_look(n):
    a=np.asarray(n)
    if (a.ndim!=2 or a.shape[1]!=3 or not np.isfinite(a).all()
        or np.iscomplexobj(a)
        or not np.allclose(np.sum(a*a,axis=1),1,rtol=0,atol=2e-11)):
        raise ProperMotionPreflightError("source sky look must be finite Nx3 unit")
    return np.asarray(a,float)


def tangential_jet_design(sky_look):
    n=unit_look(sky_look)
    T=stf2_orthonormal()
    W=antisymmetric_basis()
    e=np.einsum("kij,nj->nki",T,n,optimize=True)
    e-=np.einsum("ni,nk->nki",n,np.einsum("nki,ni->nk",e,n,optimize=True))
    b=np.einsum("kij,nj->nki",W,n,optimize=True)
    if max(abs(np.einsum("nki,ni->nk",e,n)).ravel())>2e-14:
        raise ProperMotionPreflightError("STF shear expected tangent")
    if max(abs(np.einsum("nki,ni->nk",b,n)).ravel())>2e-14:
        raise ProperMotionPreflightError("skew omega expected tangent")
    return e,b


def geometric_nonradial_rank(sky_look):
    n=unit_look(sky_look)
    if len(n)<20:raise ProperMotionPreflightError("at least 20 source sky samples")
    e,b=tangential_jet_design(n)
    A=np.transpose(e,(0,2,1)).reshape(-1,5)
    B=np.transpose(b,(0,2,1)).reshape(-1,3)
    Fa=A.T@A
    Fb=B.T@B
    C=A.T@B
    es=np.linalg.svd(np.column_stack((A,B)),compute_uv=False)
    r=int(np.count_nonzero(es>es[0]*1e-10))
    schur=Fb-C.T@np.linalg.solve(Fa,C)
    eig=eigh(schur,Fb,eigvals_only=True)
    if (r!=8 or np.min(eig)<=0 or np.max(eig)>1+1e-12):
        raise ProperMotionPreflightError("full tangent shear/omega basis not geometrically identifiable")
    return {"n_sightlines":len(n),"rank_tangential_5shear_3omega":r,
            "rank_omega_after_shear_profile":3,
            "relative_omega_information_eigenvalues_after_shear_profile":eig,
            "normalized_shear_omega_cross_operator_spectral_norm":
               float(np.sqrt(max(eigh(C.T@np.linalg.solve(Fa,C),Fb,eigvals_only=True)))),
            "radial_vorticity_mode_norm":float(np.linalg.norm(
              np.einsum("nki,ni->nk",b,n))),
            "source_physics":"HYPOTHETICAL_ANGULAR_GEOMETRY_NO_ACTUAL_PROPER_MOTION"
    }


def synthetic_transverse_recovery(sky_look,*,sigma_components,omega_components):
    n=unit_look(sky_look)
    s=np.asarray(sigma_components,float)
    o=np.asarray(omega_components,float)
    if s.shape!=(5,) or o.shape!=(3,) or not np.isfinite(s).all() or not np.isfinite(o).all():
        raise ProperMotionPreflightError("5 shear +3 rotation finite local jet amplitudes")
    E,B=tangential_jet_design(n)
    y=(np.einsum("nki,k->ni",E,s)+np.einsum("nki,k->ni",B,o))/MPC_KM  # s^-1 angular drift
    X=np.column_stack((np.transpose(E,(0,2,1)).reshape(-1,5),np.transpose(B,(0,2,1)).reshape(-1,3)))/MPC_KM
    # Avoid dividing tiny time-rate coefficients in conditioning: solve
    # dimensionless km/s/Mpc mathematical vector, then check proper units.
    fit=np.linalg.lstsq(X*MPC_KM,y.reshape(-1)*MPC_KM,rcond=None)[0]
    err=float(np.max(abs(fit-np.r_[s,o])))
    if err>2e-11:raise ProperMotionPreflightError("source sky tangential injection recovery failed")
    return {"recovered_jet_coefficients_km_s_Mpc":fit,
            "injection_maxabs_error_km_s_Mpc":err,
            "synthetic_median_vector_proper_motion_rad_s":
               float(np.median(np.linalg.norm(y,axis=1))),
            "actual_observed_proper_motion":"ABSENT_CF4_RADIAL_CATALOGUE_ONLY"}
