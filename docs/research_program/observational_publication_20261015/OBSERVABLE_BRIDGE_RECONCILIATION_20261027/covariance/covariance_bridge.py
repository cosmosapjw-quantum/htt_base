"""Finite GLS and exact linear covariance transport; no evolution solver.

The caller owns the physical mean, selection model and uncertainty calibration.
All coordinates and matrices must share their declared order, frame and units.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_triangular


def _array(value, ndim, name):
    a = np.asarray(value, dtype=float)
    if a.ndim != ndim or not np.isfinite(a).all():
        raise ValueError(f"{name}: expected finite {ndim}-dimensional array")
    return a


def _symmetric(value, name):
    a = _array(value, 2, name)
    if a.shape[0] != a.shape[1]:
        raise ValueError(f"{name}: must be square")
    tol = 64 * np.finfo(float).eps * max(1, a.shape[0])
    scale = max(float(np.max(np.abs(a), initial=0)), np.finfo(float).tiny)
    if np.max(np.abs(a-a.T), initial=0) > tol*scale:
        raise ValueError(f"{name}: not symmetric")
    return (a+a.T)/2


def gls_svd(y, design, covariance, *, relative_rank_tolerance=None):
    """GLS using Cholesky whitening and unit-column SVD.

    Returns an identifiable fitted mean even if columns are rank deficient.
    Parameter estimates/covariance are returned only for a full-column-rank
    design. An arbitrary pseudoinverse parameter vector is not a physical result.
    No null probability or empirical coverage is supplied by this function.
    """
    y = _array(y, 1, "y")
    X = _array(design, 2, "design")
    C = _symmetric(covariance, "covariance")
    if X.shape[0] != y.size or C.shape != (y.size,y.size):
        raise ValueError("incompatible y/design/covariance dimensions")
    if y.size == 0 or X.shape[1] == 0:
        raise ValueError("empty observation or design")
    try:
        L = np.linalg.cholesky(C)
    except np.linalg.LinAlgError as exc:
        raise ValueError("covariance must be positive definite") from exc
    b = solve_triangular(L,y,lower=True)
    W = solve_triangular(L,X,lower=True)
    scales = np.linalg.norm(W,axis=0)
    active = scales > 0
    if not active.any():
        raise ValueError("design has no nonzero columns")
    Z = W[:,active]/scales[active]
    U,s,Vt = np.linalg.svd(Z,full_matrices=False)
    rtol = (max(Z.shape)*np.finfo(float).eps if relative_rank_tolerance is None
            else float(relative_rank_tolerance))
    if not 0 <= rtol < 1:
        raise ValueError("relative rank tolerance must lie in [0,1)")
    rank = int(np.count_nonzero(s > rtol*s[0]))
    Q = U[:,:rank]
    mean_white = Q@(Q.T@b)
    residual_white = b-mean_white
    full_rank = rank == X.shape[1]
    beta = beta_cov = None
    if full_rank:
        beta = ((Vt.T/s)@(U.T@b))/scales
        inverse = Vt.T/s
        beta_cov = (inverse@inverse.T)/scales[:,None]/scales[None,:]
    return {
        "statistic": float(residual_white@residual_white),
        "rank": rank,
        "residual_dof": int(y.size-rank),
        "parameters_identified": full_rank,
        "beta": beta,
        "beta_covariance": beta_cov,
        "fitted_mean": L@mean_white,
        "whitened_residual": residual_white,
        "column_norms": scales,
        "scaled_singular_values": s,
        "scaled_condition": float(s[0]/s[rank-1]) if full_rank else None,
        "raw_unit_dependent_condition": float(np.linalg.cond(W)) if full_rank else None,
    }


def transport_covariance(A, independent_variance, correlated_factor=None,
                         calibration_response=None, calibration_covariance=None,
                         *, ownership, block_size=4096):
    """Compute A diag(D) A^T + (A V)(A V)^T + K Sigma K^T.

    A is the *fixed* p-by-N observation operator, including nuisance projection
    when applicable; V is an N-by-r factor in input-observable units. K maps
    calibration parameters directly to the p output coordinates. All cross-window
    blocks are retained. The N-by-N input covariance is never constructed.

    ownership maps active component names ('independent', 'correlated',
    'calibration') to disjoint lists of physical uncertainty-source labels.
    It is a declared contract, not a proof that an empirical decomposition exists.
    An already-total covariance is not an 'independent_variance' input.
    Cross-correlated source classes must be jointly factored before calling.
    """
    A = _array(A,2,"A")
    D = _array(independent_variance,1,"independent_variance")
    p,N = A.shape
    if p == 0 or N == 0 or D.shape != (N,) or np.any(D<0):
        raise ValueError("A/D dimensions or nonnegative-variance contract violated")
    if not isinstance(block_size,int) or block_size <= 0:
        raise ValueError("block_size must be a positive integer")
    V = None if correlated_factor is None else _array(correlated_factor,2,"V")
    if V is not None and V.shape[0] != N:
        raise ValueError("V must have N input rows")
    if (calibration_response is None) != (calibration_covariance is None):
        raise ValueError("calibration response and covariance must be supplied together")
    K = Sigma = None
    if calibration_response is not None:
        K = _array(calibration_response,2,"K")
        Sigma = _symmetric(calibration_covariance,"Sigma")
        if K.shape[0] != p or Sigma.shape != (K.shape[1],K.shape[1]):
            raise ValueError("K/Sigma dimensions do not match output")
        ev = np.linalg.eigvalsh(Sigma)
        tol = 64*np.finfo(float).eps*max(1,len(ev))*max(np.max(np.abs(ev),initial=0),np.finfo(float).tiny)
        if np.min(ev,initial=0) < -tol:
            raise ValueError("Sigma must be positive semidefinite")
    active = ["independent"] + (["correlated"] if V is not None else []) + (["calibration"] if K is not None else [])
    if not isinstance(ownership,dict) or set(ownership) != set(active):
        raise ValueError("ownership must name precisely the active source components")
    seen = set()
    for name in active:
        labels = ownership[name]
        if not isinstance(labels,(list,tuple)) or not labels or not all(isinstance(x,str) and x.strip() for x in labels):
            raise ValueError("each component needs nonempty physical source labels")
        if len(set(labels)) != len(labels) or seen.intersection(labels):
            raise ValueError("physical uncertainty source is counted more than once")
        seen.update(labels)
    CD = np.zeros((p,p))
    AV = np.zeros((p,V.shape[1])) if V is not None else None
    for i in range(0,N,block_size):
        sl = slice(i,min(i+block_size,N))
        B = A[:,sl]
        CD += (B*D[sl])@B.T
        if V is not None:
            AV += B@V[sl,:]
    CV = AV@AV.T if AV is not None else np.zeros_like(CD)
    CK = K@Sigma@K.T if K is not None else np.zeros_like(CD)
    total = CD+CV+CK
    return {"total":(total+total.T)/2,"independent":CD,
            "correlated":CV,"calibration":CK,"projected_factor":AV,
            "input_count":N,"output_count":p,"ownership":ownership}
