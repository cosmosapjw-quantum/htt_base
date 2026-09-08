"""T3 rate-normalized shear and vorticity from a declared radiation jet."""
from __future__ import annotations
import math
import numpy as np
from .r7_contracts import RadiationJet, PhysicalState, finite_array


def kinematics_from_radiation_jet(jet) -> PhysicalState:
    if not isinstance(jet,RadiationJet): raise TypeError("typed RadiationJet required")
    if not math.isfinite(jet.theta) or jet.theta<=0 or not math.isfinite(jet.tbar) or jet.tbar<=0:
        raise ValueError("Theta=3H and absolute temperature must be positive")
    if jet.convention not in {"OUTWARD","PROPAGATION"}: raise ValueError("explicit outward/propagation convention")
    if not jet.frame or not jet.domain_id: raise ValueError("frame and derivative domain required")
    assumptions=("geodesic radiation observer","collisionless photons","first order about isotropic radiation",
                 "dot and projected D have rate units; antisymmetrization includes 1/2")
    if not jet.geodesic or not jet.collisionless or jet.approximation!="FIRST_ORDER":
        return PhysicalState(None,None,jet.theta,jet.frame,jet.domain_id,"UNSUPPORTED_PHYSICAL_PREMISES",assumptions)
    required=("q","q_dot","tbar_dot","grad_d","div_o","curl_d","curl_d_dot","curl_div_q")
    missing=tuple(k for k in required if getattr(jet,k) is None)
    if missing: return PhysicalState(None,None,jet.theta,jet.frame,jet.domain_id,"MISSING_RADIATION_JET",assumptions,missing)
    q=finite_array(jet.q,shape=(3,3));qd=finite_array(jet.q_dot,shape=(3,3))
    if not math.isfinite(jet.tbar_dot): raise ValueError("finite temperature derivative required")
    normalized_dot=qd/jet.tbar-q*jet.tbar_dot/jet.tbar**2
    # grad_d/div_o/C and E are derivatives of NORMALIZED brightness moments;
    # q/q_dot alone are absolute K and K/s, retaining the temperature derivative.
    grad=finite_array(jet.grad_d,shape=(3,3));div=finite_array(jet.div_o,shape=(3,3))
    c=finite_array(jet.curl_d,shape=(3,3));cd=finite_array(jet.curl_d_dot,shape=(3,3))
    e=finite_array(jet.curl_div_q,shape=(3,3))
    for name,value in (("curl_d",c),("curl_d_dot",cd),("curl_div_q",e)):
        if not np.allclose(value,-value.T,rtol=0,atol=32*np.finfo(float).eps*np.linalg.norm(value)):
            raise ValueError(f"{name} must be antisymmetric with 1/2 convention")
    sym=(grad+grad.T)/2-np.eye(3)*np.trace(grad)/3
    sign=1. if jet.convention=="OUTWARD" else -1.
    sigma=-normalized_dot+sign*(sym+3*div/7)
    omega=sign*(3*cd/jet.theta+c)-6*e/(5*jet.theta)
    status="FIRST_ORDER_MODEL_CONDITIONAL" if jet.remainder_bound is None else "BOUNDED_REMAINDER_MODEL_CONDITIONAL"
    if jet.remainder_bound is not None and (len(jet.remainder_bound)!=2 or any(not math.isfinite(v) or v<0 for v in jet.remainder_bound)):
        raise ValueError("nonnegative finite rate remainder bounds required")
    return PhysicalState(sigma/jet.theta,omega/jet.theta,jet.theta,jet.frame,jet.domain_id,status,assumptions)
