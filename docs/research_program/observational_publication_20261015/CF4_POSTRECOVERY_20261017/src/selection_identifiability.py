"""Statistical counterexamples to physical selection/calibration admission from released CF4 marginals.

Each result is an explicit finite-model construction, not a claim about true CF4 survey selection.
"""
from __future__ import annotations
import numpy as np


def selection_equivalent_parents(q,p):
    """Return selection s such that P_obs=q for a proposed positive parent p.

    q,p must be probability vectors with identical finite strictly positive support.
    s_i=c*q_i/p_i<=1 gives q_i=(p_i*s_i)/sum_j(p_j*s_j).
    Thus selected records alone do not fix the parent law or selection function.
    """
    q=np.asarray(q,dtype=float);p=np.asarray(p,dtype=float)
    if q.shape!=p.shape or q.ndim!=1 or q.size<2 or not np.isfinite(q).all() or not np.isfinite(p).all() or (q<=0).any() or (p<=0).any():
        raise ValueError('equal strictly positive finite 1D supports required')
    if not np.isclose(q.sum(),1.,atol=1e-12) or not np.isclose(p.sum(),1.,atol=1e-12):
        raise ValueError('normalized parent and observed law required')
    const=np.min(p/q)
    selection=const*q/p
    if not np.allclose(p*selection/(p@selection),q,atol=1e-12):raise ArithmeticError('construction failed')
    return selection


def indistinguishable_calibration_covariance(marginal_sigma,rho):
    """One equal-marginal-error PSD family: Sigma = D ((1-rho) I + rho 11^T) D.

    Pairwise cross-group calibration can range without changing any released
    marginal sigma. This is an identification example, not an empirical estimate.
    """
    s=np.asarray(marginal_sigma,dtype=float)
    if s.ndim!=1 or s.size<2 or not np.isfinite(s).all() or np.any(s<=0) or not (0<=rho<1):
        raise ValueError('finite positive sigmas and rho in [0,1) required')
    M=np.diag(s*s*(1-rho))+rho*np.outer(s,s)
    if not np.allclose(np.diag(M),s*s,atol=1e-12):raise ArithmeticError('marginals changed')
    return M


def double_count_factor(var,coefficient=2):
    """Duplicate perfectly correlated reported datum replicated coefficient times.

    Wrong iid treating copies as independent returns var/coefficient, whereas
    covariance = var 11^T has exactly rank 1; no new information.
    """
    if not np.isfinite(var) or var<=0 or not isinstance(coefficient,int) or coefficient<2:
        raise ValueError('positive var and >=2 duplicates')
    return {'true_information_rank':1,'incorrect_iid_variance':var/coefficient,'true_variance':var}


def fit_profile_nullspace(groups,features,rtol=1e-11):
    """Rank of angular features after profiling group calibration design.

    Does not impose identity X_monopole=sum(method) for multi-method group rows.
    """
    z=np.asarray(groups,dtype=float);x=np.asarray(features,dtype=float)
    if z.ndim!=2 or x.ndim!=2 or z.shape[0]!=x.shape[0] or z.shape[0]<2:
        raise ValueError('row matching designs needed')
    if not (np.isfinite(z).all() and np.isfinite(x).all()):raise ValueError('nonfinite design')
    rZ=np.linalg.matrix_rank(z,tol=rtol)
    rX=np.linalg.matrix_rank(x,tol=rtol)
    rZX=np.linalg.matrix_rank(np.column_stack([z,x]),tol=rtol)
    return {'rank_calibration_design':int(rZ),'rank_angular_design':int(rX),
            'rank_joint':int(rZX),'rank_angular_after_calibration':int(rZX-rZ)}
