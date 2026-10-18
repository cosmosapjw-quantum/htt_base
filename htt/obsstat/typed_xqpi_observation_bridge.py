"""PR-248..258 typed observation/anchor vs PR-521 legacy x,Q,Pi bridge.

A conditional *speed-amplitude scenario* has an exactly calculable x,Q,Pi
pushforward when the caller assumes the bulk speed/c equals one homogeneous
matter-geometry rapidity and sets other sectors to zero. A genuine physical
defect distribution remains unidentified without that physical transport,
its nuisance/curvature sectors and a valid total-x normalizer.

The registered MES geodesic anchors are only channel-matched one-way linear
consistency stress bounds; neither shear ceiling is a signed total-x budget.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import asinh,sqrt,sinh
import numpy as np
from scipy.stats import norm
from common.statistical_foundations import (
    AnchorConditioning,AnchorStatus,
    registered_geodesic_mes_anchors, quarantined_shear_anchors,
    ScalarRange,evaluate_sector_stress, StressStatus,
)

C_KM_S=299792.458

class TypedDefectBridgeError(ValueError):
    pass


def _number(x,name,*,nonnegative=False,positive=False):
    if isinstance(x,(bool,np.bool_)) or np.iscomplexobj(x):
        raise TypedDefectBridgeError(f'{name} must be real numeric')
    try:v=float(x)
    except (TypeError,ValueError,OverflowError) as exc:
        raise TypedDefectBridgeError(f'{name} must be real numeric') from exc
    if not np.isfinite(v) or (nonnegative and v<0) or (positive and v<=0):
        raise TypedDefectBridgeError(f'{name} out of physical or finite domain')
    return v


def analytic_conditional_tail(q,mean_km_s,sigma_km_s,omega_m,
                              shear_only_legacy_ceiling,*,x_offset=0.):
    """P((x_offset+Om sinh^2(max(0,N(mu,sigma))/c))/xc > q), Gaussian scenario.

    Strict > retains the zero-speed atom at all q for which threshold
    equals offset. Signed x_offset is a specified algebraic *scenario*
    component, not a measured source curvature or vorticity posterior.
    """
    q=_number(q,'threshold')
    mu=_number(mean_km_s,'bulk speed mean',nonnegative=True)
    sig=_number(sigma_km_s,'bulk speed sigma',positive=True)
    om=_number(omega_m,'matter source density',positive=True)
    xc=_number(shear_only_legacy_ceiling,'legacy shear denominator',positive=True)
    x0=_number(x_offset,'source-conditional signed offset')
    target=q*xc-x0
    if not np.isfinite(target):
        raise TypedDefectBridgeError('nonfinite target')
    if target<0:
        return 1.
    if target==0:
        # As specified, speed is max(0,Z), with atom at V=0.
        return float(norm.sf(-mu/sig))
    cut=C_KM_S*asinh(sqrt(target/om))
    return float(norm.sf((cut-mu)/sig))


def paired_velocity_quantile_atoms(mean_km_s,sigma_km_s,n):
    """Deterministic Gaussian law midpoint quadrature, one latent ID per atom.

    All Planck processing sources must use this SAME underlying speed draw
    vector, never independent cosmological skies or a stacked posterior.
    """
    mu=_number(mean_km_s,'mean',nonnegative=True)
    sd=_number(sigma_km_s,'sd',positive=True)
    if type(n) is not int or not 32<=n<=16384 or n&(n-1):
        raise TypedDefectBridgeError('power-of-two n in [32,16384]')
    u=(np.arange(n,dtype=float)+.5)/n
    v=np.maximum(0.,mu+sd*norm.ppf(u))
    ids=tuple(f'vgauss-{i:05d}' for i in range(n))
    return ids,v


def conditionally_matter_tilt(v_kms,omega_m):
    """Only under declared V/c == homogeneous beta assumption."""
    if np.iscomplexobj(v_kms):
        raise TypedDefectBridgeError('real speeds needed')
    v=np.asarray(v_kms,dtype=float)
    if v.ndim!=1 or not np.isfinite(v).all() or np.any(v<0):
        raise TypedDefectBridgeError('finite nonnegative speed samples')
    o=_number(omega_m,'Om',positive=True)
    return o*np.sinh(v/C_KM_S)**2


def nine_same_sky_geodesic_anchor_scenarios(multipoles):
    """Registry output under eps1=0, never physical bounds from sqrt(Cl) alone.

    The observed sky alone does not establish required almost-EGS spatial
    derivatives, frame-bound covariant epsilon values or sky null.
    """
    if not isinstance(multipoles,dict) or not multipoles:
        raise TypedDefectBridgeError('named same-sky map responses required')
    result={}
    for name,packet in multipoles.items():
        if not isinstance(name,str) or not name or not isinstance(packet,dict):
            raise TypedDefectBridgeError('source map name/multipole response required')
        e2=_number(packet['epsilon2_explicit_sqrtCl_over_T0'],'eps2',positive=True)
        e3=_number(packet['epsilon3_explicit_sqrtCl_over_T0'],'eps3',positive=True)
        try:
            a=registered_geodesic_mes_anchors(
                eps1=0.,eps2=e2,eps3=e3,
                attribution='SAG observer-motion-subtracted zero residual dipole algebraic scenario',
                conditioning=AnchorConditioning.REALIZATION_CONDITIONAL)
        except (ValueError,TypeError) as exc:
            raise TypedDefectBridgeError(f'source PR124 geodesic hierarchy rejected {name}') from exc
        if (a['sigma'].status is not AnchorStatus.VERIFIED
            or a['omega'].status is not AnchorStatus.VERIFIED
            or a['acceleration'].status is not AnchorStatus.NO_MES_ANCHOR):
            raise TypedDefectBridgeError('PR124 registered branches/status changed')
        legacy=quarantined_shear_anchors(
            eps1=0.,eps2=e2,eps3=e3,
            attribution='historical prior only',
            conditioning=AnchorConditioning.REALIZATION_CONDITIONAL)
        # Explicitly attempt to normalize a CF4 apparent expansion quadrupole
        # from another source frame. The typed authority MUST NOT accept this.
        stress=evaluate_sector_stress(
            sector='Sigma2',numerator=ScalarRange(0.,1e-3),
            numerator_channel_key=('CF4 local apparent modulus anisotropy','source-specific sky-frame',
                'not-geodesic-MES','local-volume','apparent shear proxy'),
            anchor=a['sigma'])
        if stress.status is not StressStatus.CHANNEL_MISMATCH:
            raise TypedDefectBridgeError('channel mismatch incorrectly promoted')
        result[name]={
            'eps1_assumption':'ZERO_OBSERVER_MOTION_SUBTRACTED_COSMOLOGICAL_DIPOLE',
            'eps2_sqrtCl_over_T0_proxy':e2,'eps3_sqrtCl_over_T0_proxy':e3,
            'registered_geodesic_sigma_sector_anchor':a['sigma'].value,
            'registered_geodesic_omega_sector_anchor':a['omega'].value,
            'geodesic_acceleration_sector_anchor_status':a['acceleration'].status.value,
            'anisotropic_curvature_anchor_status':a['anisotropic_curvature'].status.value,
            'CF4_apparent_shear_proxy_to_geodesic_MES_stress_status':stress.status.value,
            'legacy_corrected_shear_anchor_status':legacy['frame_corrected'].status.value,
            'physical_observation_admission':'NOT_VALIDATED_DIFFERENT_EPSILON_CONVENTION_AND_ALMOST_EGS_DERIVATIVES',
        }
    return result


def get_legacy_ceiling(eps1,eps2,eps3):
    """Historical formula for *shear-only* denominator, never x_total max."""
    a=[_number(v,k,nonnegative=True) for v,k in zip((eps1,eps2,eps3),('e1','e2','e3'))]
    b=5*a[0]/3+3*a[1]+3*a[2]/7
    return 1.5*b*b


def strict_known_pi(q,weights,ceiling,t):
    """Direct finite oracle, not a registered observed physical posterior."""
    x=np.asarray(q,dtype=float)
    w=np.asarray(weights,dtype=float)
    if (x.ndim!=1 or w.shape!=x.shape or np.any(w<0)
        or not np.isfinite(x).all() or not np.isfinite(w).all() or w.sum()<=0):
        raise TypedDefectBridgeError('finite image mass cannot be silently dropped')
    c=_number(ceiling,'ceiling',positive=True)
    threshold=_number(t,'threshold')
    return float(w[x/c>threshold].sum()/w.sum())


__all__=['TypedDefectBridgeError','analytic_conditional_tail','paired_velocity_quantile_atoms',
    'conditionally_matter_tilt','nine_same_sky_geodesic_anchor_scenarios',
    'get_legacy_ceiling','strict_known_pi','C_KM_S']
