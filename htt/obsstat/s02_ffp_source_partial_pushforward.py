"""Simulation-EMPIRICAL HTT MES boxes, not physical posteriors.

For 999 distinct FFP10 CMB source maps, eps_l come from fixed Planck
masked source processing. Counterfactual C1/C2 geodesic MES and
intrinsic eps1=0 give U_sigma,U_omega but do not observe sigma or omega.
Flat/untilted *algebraic* Q=(Sigma²-W²)/U_sigma has per-map box
[-U_omega/U_sigma,1]. Full signed curvature/tilt-unrestricted Q
remains the real line. Pi_Q is an identified set, NOT a null p-value.
"""
from __future__ import annotations
import numpy as np
from .mes_eps_measurement_bridge import geodesic_algebraic_sector_ceiling

class SourceSimulationPartialError(ValueError):
    pass

def source_mes_box(eps,ids,weights=None):
    eps=np.asarray(eps)
    ids=np.asarray(ids)
    if (eps.ndim!=2 or eps.shape[1]!=2 or len(eps)<1
        or np.iscomplexobj(eps) or not np.isfinite(eps).all()
        or np.any(eps<0) or len(ids)!=len(eps)
        or len(set(map(str,ids)))!=len(eps)):
        raise SourceSimulationPartialError("finite nonnegative 2D eps and unique source IDs required")
    a=np.asarray(eps,float)
    w=(np.full(len(a),1/len(a)) if weights is None else np.asarray(weights))
    if (w.shape!=(len(a),) or np.iscomplexobj(w) or not np.isfinite(w).all()
        or np.any(w<0) or not np.isclose(np.sum(w),1,atol=1e-12,rtol=0)):
        raise SourceSimulationPartialError("normalized nonnegative empirical weights required")
    us=1.5*(3*a[:,0]+3*a[:,1]/7)**2
    uw=1.5*(2*a[:,0]/15)**2
    if np.any(us<=0) or not np.isfinite(us).all() or not np.isfinite(uw).all():
        raise SourceSimulationPartialError("positive MES shear anchor required for Q")
    low=-uw/us
    if np.any(low>0) or np.any(low< -1):
        raise SourceSimulationPartialError("invalid registered geodesic epsilon ratio")
    return {"eps":a,"ids":ids,"weights":np.asarray(w,float),
            "U_sigma":us,"U_omega":uw,"q_low":low,"q_high":np.ones(len(a)),
            "model":"C1_C2_UNVERIFIED_EPS1_ZERO_FLAT_UNTILTED_BOX",
            "source_status":"SIMULATION_EMPIRICAL_NOT_COSMOLOGICAL_POSTERIOR"}

def scalar_mes_regression(eps):
    a=np.asarray(eps,float)
    if a.ndim!=2 or a.shape[1]!=2 or len(a)==0:
        raise SourceSimulationPartialError("N×2 eps rows")
    indices=np.unique(np.linspace(0,len(a)-1,min(13,len(a)),dtype=int))
    err=0.
    for i in indices:
        s=geodesic_algebraic_sector_ceiling(float(a[i,0]),float(a[i,1]),eps1=0.)
        err=max(err,abs(1.5*(3*a[i,0]+3*a[i,1]/7)**2-s["Sigma2_anchor_only_if_conditions_met"]),
                abs(1.5*(2*a[i,0]/15)**2-s["W2_anchor_only_if_conditions_met"]))
    if err>2e-22:raise SourceSimulationPartialError("batch vs scalar MES mismatch")
    return {"n_verified_rows":len(indices),"maxabs":float(err)}

def pi_box_strict(box,thresholds):
    """Per-simulation sharp endpoint witnesses for algebraic independent boxes."""
    grid=np.asarray(thresholds)
    if (grid.ndim!=1 or len(grid)<1 or np.iscomplexobj(grid)
        or not np.isfinite(grid).all() or not np.all(np.diff(grid)>0)):
        raise SourceSimulationPartialError("strict increasing finite thresholds required")
    t=np.asarray(grid,float)
    lo=np.asarray(box["q_low"],float)
    hi=np.asarray(box["q_high"],float)
    w=np.asarray(box["weights"],float)
    if np.any(lo>hi) or not np.isclose(sum(w),1,rtol=0,atol=1e-12):
        raise SourceSimulationPartialError("valid normalized product box expected")
    lower=np.sum(w[:,None]*(lo[:,None]>t[None,:]),axis=0)
    upper=np.sum(w[:,None]*(hi[:,None]>t[None,:]),axis=0)
    err=max(max(abs(lower-np.array([w@(lo>v) for v in t]))),
            max(abs(upper-np.array([w@(hi>v) for v in t]))))
    if err>5e-13:raise SourceSimulationPartialError("endpoint completion witness mismatch")
    return {"thresholds":t,"lower":lower,"upper":upper,
            "full_Q_lower":np.zeros(len(t)),"full_Q_upper":np.ones(len(t)),
            "corner_witness_maxabs":float(err),
            "sharpness":"ALGEBRAIC_PRODUCT_BOX_ONLY_NOT_PHYSICAL_POSTERIOR"}

def descriptive_summary(box):
    def q(a):return np.quantile(a,[.05,.16,.5,.84,.95]).tolist()
    return {"source_N":len(box["ids"]),
            "U_sigma_q05_16_50_84_95":q(box["U_sigma"]),
            "U_omega_q05_16_50_84_95":q(box["U_omega"]),
            "Q_lower_q05_16_50_84_95":q(box["q_low"]),
            "source_claim":"SOURCE_SIMULATION_EMPIRICAL_NOT_PHYSICAL_SHEAR_POSTERIOR"}
