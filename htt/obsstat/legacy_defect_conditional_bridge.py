"""Explicitly source-conditional legacy 2026 defect pushforward.

This code preserves the manuscript's *mathematical* signed-defect
bookkeeping and three layers x,Q,Pi while refusing to label bulk flows
as homogeneous Bianchi tilt or dipole counts as observed CMB multipoles.
The literature-reported velocity amplitudes are NOT a new data
likelihood. CF4 two radii share the same underlying survey, not
independent measurements. The underlying MES coefficients are
LEGACY ANSATZ; this module does not prove their general applicability.
"""
from __future__ import annotations
import numpy as np

C_KMS=299792.458
T0_uK=2.72548e6


class LegacyDefectBridgeError(ValueError):
    pass


def scalar_proxy_from_Cl(cl_microK2,ell,*,T0microK=T0_uK):
    """Explicit harmonic scalar convention sqrt(C_l)/T0, not STF norm.

    For a statistically isotropic real harmonic realization,
    C_l=(sum over full real coefficients a_lm²)/(2ell+1).
    Thus this convention is scalar power amplitude and does not
    directly equal the PSTF tensor norm or axisymmetric |a_l0|.
    """
    if np.iscomplexobj(cl_microK2): raise LegacyDefectBridgeError('real Cl only')
    cl=np.asarray(cl_microK2,float)
    if not isinstance(ell,int) or ell<1 or T0microK<=0 or not np.isfinite(cl).all() or np.any(cl<0):
        raise LegacyDefectBridgeError('nonnegative measured temperature power and T0 needed')
    return np.sqrt(cl)/T0microK


def mes_scenario_ceiling(eps1,eps2,eps3):
    """Legacy manuscript formulas conditional on its almost-EGS assumptions.

    NOT a measurement or an official Planck selection-calibrated CMB
    posterior. ε1 from matter number-counts is NOT the required CMB
    temperature multipole; its use is a legacy cross-probe scenario only.
    """
    vals=np.asarray([eps1,eps2,eps3],dtype=float)
    if not np.isfinite(vals).all() or np.any(vals<0):
        raise LegacyDefectBridgeError('nonnegative real legacy epsilon multipoles required')
    Bsig=5/3*eps1+3*eps2+3/7*eps3
    Bw=.75*eps1+2*eps2+2/7*eps3
    Ba=.75*eps1+eps2+3/14*eps3
    return {
      'B_sigma':float(Bsig),'B_omega':float(Bw),'B_accel':float(Ba),
      'Sigma2_max':float(1.5*Bsig*Bsig),
      'W2_max':float(1.5*Bw*Bw),
      'A2_max':float(1.5*Ba*Ba),
      'bound_status':'LEGACY_COEFFICIENTS_ASSUMPTION_CONDITIONED_NOT_SOURCE_TRANSFER_VALIDATED',
      'vorticity_note':'W2_max is an algebraic ceiling, not vorticity distribution; no inferred P(W2|D)',
      'acceleration_note':'A2_max is an algebraic ceiling, not four-acceleration distribution',
    }


def matter_tilt_density(beta,omega_m=.3153,w=0):
    if np.iscomplexobj(beta): raise LegacyDefectBridgeError('real tilt rapidity required')
    b=np.asarray(beta,float)
    if not np.isfinite(b).all() or omega_m<0 or w<=-1:
        raise LegacyDefectBridgeError('finite proper dimensionless bulk-tilt proxy')
    return (1+w)*omega_m*np.sinh(b)**2


def legacy_pushforward_of_external_bulk_proxy(
    mean_km_s,sigma_km_s,eps2,eps3,*,eps1_ref,
    omega_m=.3153,draws=100000,seed=20261015,
    extra_curvature=0,extra_shear=0,extra_vorticity=0):
    """Independent illustrative velocity-amplitude Gaussian into x/Q/Pi.

    If extra source terms are zero, this is the pure-tilt/flat comparator
    LEGACY BOOKKEEPING, not evidence for global beyond-FLRW geometry.
    External bulk amplitudes from different windows cannot be naively
    combined or treated as a homogeneous matter-vs-geometry rapidity.
    """
    vals=np.asarray([mean_km_s,sigma_km_s,eps2,eps3,eps1_ref,omega_m,
                     extra_curvature,extra_shear,extra_vorticity],float)
    if (not np.isfinite(vals).all() or mean_km_s<0 or sigma_km_s<0 or
       eps1_ref<0 or eps2<0 or eps3<0 or omega_m<=0 or
       extra_shear<0 or extra_vorticity<0 or draws<1000):
        raise LegacyDefectBridgeError('source Gaussian, epsilon and signed-defect contract violated')
    cs=mes_scenario_ceiling(eps1_ref,eps2,eps3)
    rng=np.random.default_rng(seed)
    v=np.maximum(0.,rng.normal(mean_km_s,sigma_km_s,size=draws))
    beta=v/C_KMS
    ot=matter_tilt_density(beta,omega_m,0)
    x=extra_shear-extra_vorticity+ot+extra_curvature
    Q=x/cs['Sigma2_max']
    qs=[.025,.16,.5,.84,.975]
    return {
      'source_bulk_flow_mean_km_s':float(mean_km_s),
      'source_bulk_flow_reported_sigma_km_s':float(sigma_km_s),
      'kinematic_beta_magnitude_proxy_quantiles':np.quantile(beta,qs).tolist(),
      'Omega_tilt_quantiles':np.quantile(ot,qs).tolist(),
      'x_quantiles':np.quantile(x,qs).tolist(),
      'occupancy_quantiles':np.quantile(Q,qs).tolist(),
      'exceedance_probability_by_threshold':{str(t):float(np.mean(Q>t)) for t in (.01,.05,.1,.5,1)},
      'MES_ceiling':cs['Sigma2_max'],
      'conditional_integrated_sample_draws':int(draws),
      'source_model':'EXTERNAL_REPORTED_BULK_FLOW_GAUSSIAN_PROXY_AND_LEGACY_IDENTITY_NO_JOINT_COSMOLOGY',
      'physics_assumptions':['set geometry-frame Sigma2,W2 and curvature comparator difference to zero unless extra terms declared',
        'identify bulk magnitude v/c with background matter-geometry rapidity ONLY FOR THIS ILLUSTRATIVE SCENARIO',
        'uncertainty on published bulk-flow amplitude treated as univariate Gaussian, not a new catalogue posterior',
        'epsilon1 reference must refer to chosen scenario and CMB/MATTER source type in calling script',
        'MES coefficients, almost-EGS Copernican derivatives and frame transport not re-proven here']
    }
