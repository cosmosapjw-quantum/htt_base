"""H03 mean-design method-zeropoint gauge, conditional on fixed source distances/weights.

A first-order distance-modulus calibration shift changes an estimated distance by
kappa*d*delta_mu_m. Four unconstrained method shifts include a common global
rescaling, so absolute apparent monopole normalization is unidentifiable from
weighted *mean design* alone without an anchor. No full calibrated CF4 likelihood.
"""
from __future__ import annotations
import numpy as np
from scipy.linalg import qr,svdvals
from h03_tomography import METHODS,velocity_design

def calibration_rank(d,n,w,method)->dict:
    d=np.asarray(d,float);n=np.asarray(n,float);w=np.asarray(w,float);method=np.asarray(method)
    if d.ndim!=1 or n.shape!=(len(d),3) or w.shape!=d.shape or method.shape!=d.shape or not np.isfinite(w).all() or np.any(w<0):raise ValueError('source rows and W fixed required')
    if set(np.unique(method))!=set(METHODS):raise ValueError('the four released group method families must be represented')
    x=velocity_design(d,n);Z=np.column_stack([d*(method==m) for m in METHODS]);s=np.sqrt(w)
    # Identity: mean expansion monopole column equals sum of four method-offset columns.
    explicit=float(np.linalg.norm(x[:,0]-np.sum(Z,axis=1))/max(1,np.linalg.norm(x[:,0])))
    joined=np.column_stack([x,Z])*s[:,None]
    sing=svdvals(joined)
    rank=int(np.sum(sing>sing[0]*1e-10))
    if explicit>1e-13 or rank!=12:raise AssertionError('method calibration gauge/rank mismatch')
    q,r=qr(s[:,None]*Z,mode='economic')
    projected=s[:,None]*x-q@(q.T@(s[:,None]*x))
    singproj=svdvals(projected)
    srank=int(np.sum(singproj>singproj[0]*1e-10))
    if srank!=8:raise AssertionError('nuisance-projected mean model must have 8 identifiable combinations')
    return {'design':'[d*(1,n_i,n_i T_A n_i), d*1{method=m}] in fixed W mean only',
            'raw_columns':13,'mean_design_rank':rank,'mean_design_nullity':13-rank,
            'explicit_monopole_equals_sum_methods_relative_residual':explicit,
            'projected_nuisance_columns':4,'remaining_theta_rank':srank,
            'remaining_theta_nullity':9-srank,
            'mean_design_singular_values':sing.tolist(),
            'projected_theta_singular_values':singproj.tolist(),
            'admission':'MATHEMATICAL_FIRST_ORDER_CALIBRATION_GAUGE_NOT_CF4_LIKELIHOOD'}
