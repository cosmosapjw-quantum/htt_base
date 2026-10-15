"""Exact event-local Lorentz frame transport for HTT observer/radiation/matter.

Convention: g=(-,+,+,+), photon k^a/E=(1,e) with e photon PROPAGATION,
U_B=gamma(U_A + beta^i e_i) where beta=B relative A in A's tetrad.
For 4-vector p_A, p_B=L(beta_B|A)p_A; L(-beta) is exact inverse.
Photon energy D=E_B/E_A=gamma(1-beta dot e_A);
observed sky look direction s=-e, opposite photon propagation.

beta_XY means velocity of frame X measured in comoving frame Y, i.e.
the SECOND index denotes observer frame. All returned vector components
are tied to the reported tetrad and cannot be subtracted blindly across
noncollinear boosts due to Wigner rotation.

Temperature is Planck thermodynamic blackbody: T_B(s_B)=D*T_A(s_A).
No collision source history or global matter/radiation tilt inferred.
"""
from __future__ import annotations

import math
from typing import Callable
import numpy as np

C_KM_S=299792.458


class FrameBoostError(ValueError):
    pass


def checked_beta(beta):
    b=np.asarray(beta)
    if b.shape!=(3,) or np.iscomplexobj(b) or not np.isfinite(b).all():
        raise FrameBoostError("one finite real 3-vector beta=v/c in bound orthonormal tetrad")
    b=np.asarray(b,float)
    speed2=float(np.dot(b,b))
    if not 0<=speed2<1 or 1-speed2<=1e-12:
        raise FrameBoostError("strictly subluminal numerically stable finite Lorentz boost required")
    return b


def gamma_beta(beta):
    b=checked_beta(beta)
    # (1-v)(1+v) avoids cancellation for speed2 near one.
    v=float(np.linalg.norm(b))
    return float(1/math.sqrt((1-v)*(1+v)))


def lorentz_to_moving(fourvector,beta):
    """Four vector in A tetrad -> canonical pure-boosted tetrad comoving B."""
    b=checked_beta(beta)
    p=np.asarray(fourvector)
    if (p.shape[-1:]!=(4,) or np.iscomplexobj(p) or not np.isfinite(p).all()):
        raise FrameBoostError("real finite contravariant Minkowski four-vector with last axis 4")
    p=np.asarray(p,float)
    g=gamma_beta(b)
    dot=np.einsum("...i,i->...",p[...,1:4],b,optimize=True)
    time=g*(p[...,0]-dot)
    # Stable (gamma-1)/beta^2 = gamma^2/(gamma+1), including beta=0.
    shift=(g*g/(g+1))*dot-g*p[...,0]
    xyz=p[...,1:4]+np.expand_dims(shift,-1)*b
    return np.concatenate((np.expand_dims(time,-1),xyz),axis=-1)


def lorentz_to_parent(fourvector,beta_child_in_parent):
    return lorentz_to_moving(fourvector,-checked_beta(beta_child_in_parent))


def minkowski_norm(fourvector):
    f=np.asarray(fourvector,float)
    if f.shape[-1:]!=(4,):
        raise FrameBoostError("4-vector with t and x,y,z required")
    return -f[...,0]**2+np.sum(f[...,1:4]**2,axis=-1)


def _unit_directions(directions):
    n=np.asarray(directions)
    if (n.shape[-1:]!=(3,) or np.iscomplexobj(n) or
        not np.isfinite(n).all()):
        raise FrameBoostError("finite photon propagation or sky look direction 3-vector")
    n=np.asarray(n,float)
    lens=np.linalg.norm(n,axis=-1)
    if not np.allclose(lens,1,atol=3e-12,rtol=0):
        raise FrameBoostError("unit physical direction required")
    return n


def photon_normal_to_moving(direction_in_normal,beta_moving_in_normal):
    """Return new propagation direction and E_moving/E_normal."""
    e=_unit_directions(direction_in_normal)
    source=np.concatenate((np.ones(e.shape[:-1]+(1,)),e),axis=-1)
    p=lorentz_to_moving(source,beta_moving_in_normal)
    D=p[...,0]
    if np.any(D<=0) or not np.isfinite(D).all():
        raise FrameBoostError("positive photon Doppler factor required")
    n=p[...,1:]/np.expand_dims(D,-1)
    if not np.allclose(np.linalg.norm(n,axis=-1),1,atol=1e-10):
        raise FrameBoostError("boosted photon failed null ray condition")
    return n,D


def photon_moving_to_normal(direction_in_moving,beta_moving_in_normal):
    """Return source photon propagation, E_moving/E_normal."""
    e=_unit_directions(direction_in_moving)
    q=np.concatenate((np.ones(e.shape[:-1]+(1,)),e),axis=-1)
    p=lorentz_to_parent(q,beta_moving_in_normal)
    invD=p[...,0]
    if np.any(invD<=0) or not np.isfinite(invD).all():
        raise FrameBoostError("inverse positive photon Doppler factor required")
    return p[...,1:]/np.expand_dims(invD,-1),1./invD


def boosted_sky_temperature(observed_sky_look,beta_observer_in_radiation,
                            source_temperature:Callable):
    """Thermodynamic source sky -> moving observer sky with exact aberration.

    Directions are sky LOOK vectors s=-e, as in HEALPix/Planck source maps.
    Source function maps sky-look to positive thermodynamic microK, scalar/batch.
    Return T_O and intrinsic source sky-look s_R for traceable source response.
    """
    sO=_unit_directions(observed_sky_look)
    eR,D=photon_moving_to_normal(-sO,beta_observer_in_radiation)
    sR=-eR
    T=np.asarray(source_temperature(sR))
    if (T.shape!=sO.shape[:-1] or np.iscomplexobj(T)
        or not np.isfinite(T).all() or np.any(T<=0)):
        raise FrameBoostError("source blackbody thermodynamic temperature must be positive")
    return np.asarray(D*T,float),sR,D


def four_velocity(beta):
    b=checked_beta(beta)
    return gamma_beta(b)*np.r_[1.,b]


def relative_velocity_of_A_measured_in_B(beta_A_normal,beta_B_normal):
    """A velocity in canonical B tetrad; not a vector in normal/M coordinates."""
    u=four_velocity(beta_A_normal)
    v=lorentz_to_moving(u,beta_B_normal)
    if v[0]<=0:raise FrameBoostError("nonfuture directed measured four-velocity")
    return checked_beta(v[1:]/v[0])


def frame_triad(beta_R_in_N,beta_M_in_N,beta_O_in_N):
    """Precise beta_AB velocity A seen by observer B, plus scalar checks.

    N is an arbitrary named reference 1+3 normal tetrad.
    Each returned beta_AB is expressed in observer B's canonical tetrad
    (boosted directly from N, with no implied globally defined axes).
    """
    bR=checked_beta(beta_R_in_N)
    bM=checked_beta(beta_M_in_N)
    bO=checked_beta(beta_O_in_N)
    def rel(a,b):return relative_velocity_of_A_measured_in_B(a,b)
    beta_RO=rel(bR,bO)
    beta_RM=rel(bR,bM)
    beta_MO=rel(bM,bO)
    beta_OR=rel(bO,bR)
    uR,uM,uO=[four_velocity(b) for b in (bR,bM,bO)]
    gamma_RO=-float(minkowski_inner(uR,uO))
    g1=gamma_beta(beta_RO)
    g2=gamma_beta(beta_OR)
    if not np.allclose([gamma_RO,g1,g2],gamma_RO,rtol=1e-11,atol=2e-11):
        raise FrameBoostError("inconsistent Lorentz-invariant relative speed")
    return {
      "beta_RO_R_in_observer_O_tetrad":beta_RO,
      "beta_RM_R_in_matter_M_tetrad":beta_RM,
      "beta_MO_M_in_observer_O_tetrad":beta_MO,
      "beta_OR_O_in_radiation_R_tetrad":beta_OR,
      "rapidity_R_observer_O":float(np.arccosh(gamma_RO)),
      "gamma_RO_invariant":gamma_RO,
      "source_scalar_rel_speed":float(np.linalg.norm(beta_RO)),
      "frame_coordinate_statement":
        "beta_AB is A-velocity in B canonical tetrad; noncollinear vectors have Wigner rotations",
      "physical_claim":"ONE_EVENT_LORENTZ_KINEMATICS_NOT_GLOBAL_TILT_HISTORY"
    }


def minkowski_inner(a,b):
    x=np.asarray(a)
    y=np.asarray(b)
    if x.shape!=(4,) or y.shape!=(4,):
        raise FrameBoostError("two four-vectors")
    return float(-x[0]*y[0]+np.dot(x[1:],y[1:]))


def legacy_rapidity_and_velocity_fraction(beta):
    """Separate three-velocity fraction from rapidity parameter rho."""
    b=checked_beta(beta)
    mod=float(np.linalg.norm(b))
    return {"velocity_fraction":mod,
            "rapidity_rho":float(np.arctanh(mod)),
            "gamma":gamma_beta(b),
            "not_interchangeable":"sinh(rho)!=beta; tanh(rho)=beta"}


def galactic_dipole_unit_vector(l_deg,b_deg):
    l,b=np.deg2rad([float(l_deg),float(b_deg)])
    if not np.isfinite([l,b]).all() or abs(b)>math.pi/2:
        raise FrameBoostError("finite Galactic longitude and latitude source axis required")
    return np.array([math.cos(b)*math.cos(l),
                     math.cos(b)*math.sin(l),math.sin(b)])



def one_event_frame_rank(beta_R_in_N,beta_O_in_N,*,step=1e-6):
    """Finite one-event map (beta_R,beta_O)->beta_OR and its rank/nullspace.

    At zero velocity, linearization is beta_OR=beta_ON-beta_RN, so J=[-I,I].
    This has rank 3 and a 3D nullspace: the same event-local radiation
    dipole relative motion does not identify separate source/background
    radiation velocity and observer velocity. It is NOT a universal
    no-go theorem once source histories/multiple observational channels
    exist; this is a bounded local Lorentz map fact.
    """
    bR=checked_beta(beta_R_in_N)
    bO=checked_beta(beta_O_in_N)
    if not np.isfinite(step) or not 1e-9<=step<=1e-3:
        raise FrameBoostError("finite difference step range [1e-9,1e-3]")
    x=np.r_[bR,bO]
    def f(y):
        return relative_velocity_of_A_measured_in_B(y[3:],y[:3])
    jac=np.empty((3,6))
    for i in range(6):
        plus=x.copy();minus=x.copy()
        plus[i]+=step;minus[i]-=step
        jac[:,i]=(f(plus)-f(minus))/(2*step)
    u,s,vh=np.linalg.svd(jac,full_matrices=True)
    rank=int(np.sum(s>s[0]*1e-10))
    null=vh[rank:,:]
    residual=float(np.max(abs(jac@null.T))) if len(null) else 0.
    if rank!=3 or residual>2e-9:
        raise FrameBoostError("observer-radiation one-event relative velocity Jacobian rank issue")
    return {
        "observed_relative_beta_OR":f(x),
        "jacobian_beta_R_then_beta_O":jac,
        "singular_values":s,
        "rank":rank,
        "nullspace_dimension":6-rank,
        "nullspace_residual_maxabs":residual,
        "assumptions":"one event, canonical pure boosts measured in common N tetrad, no source history",
        "physics":"finite Lorentz relative velocity observable alone cannot identify two 3-vectors"
    }



def kinematic_monopole_f4(beta):
    """Exact full-sky Teff fourth moment of a pure isotropic source monopole.

    Under a finite local observer boost beta (sky look vector s):
      Theta_O(s)=sqrt(1-|beta|^2)/(1-beta dot s).
    The exact angular average is
      <Theta_O^4>=(1+|beta|^2/3)/(1-|beta|^2);
      F4-1=4|beta|^2/[3(1-|beta|^2)].
    Wolfram exact integral verified. This is kinematic contamination of
    legacy Teff, NOT the legacy MIO filling fraction F, intrinsic CMB
    non-Gaussianity, global material tilt or physical 1+3 acceleration.
    """
    b=checked_beta(beta)
    v2=float(b@b)
    delta=4*v2/(3*(1-v2))
    return {"F4":1+delta,"deltaF4":delta,
            "beta2":v2,
            "type":"EXACT_BOOSTED_ISOTROPIC_MONOPOLE_KINEMATIC_TEFF_ONLY"}
