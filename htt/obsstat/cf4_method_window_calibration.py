"""CF4 source-window dependence on declared method zero-point nuisance.

For fixed source grouping, weights, and observed z:
    log H_W = sum_i L_Wi log(c z_i/D_i)
    d log H_W / d delta_mu_m = -(ln 10)/5 sum_{i:method=m} L_Wi.

This is exact for additive method zero-point shifts in distance moduli,
including arbitrary shift amplitudes, conditional on FIXED selection and
fixed weights. It is NOT an estimate of the real method zero-point error,
nor a survey-calibrated CF4 likelihood.
"""
from __future__ import annotations
import numpy as np
from .htt_hubble_depth_window import K_LOG


class Cf4CalibrationDomainError(ValueError):
    pass


def method_response(weight_operator, method, *, declared_methods=None):
    """Return method weight fractions F_Wm and gradient d logH_W /d mu_m."""
    L=np.asarray(weight_operator)
    method=np.asarray(method)
    if (L.ndim!=2 or np.iscomplexobj(L) or not np.isfinite(L).all()
        or len(method)!=L.shape[1] or method.ndim!=1
        or np.iscomplexobj(method) or
        not np.allclose(np.sum(L,axis=1),1.,atol=5e-12,rtol=0)
        or np.any(L<0)):
        raise Cf4CalibrationDomainError("finite normalized nonnegative window source weights")
    names=sorted(set(str(x) for x in method)) if declared_methods is None else list(declared_methods)
    if not names or len(set(names))!=len(names) or any(not isinstance(z,str) or not z for z in names):
        raise Cf4CalibrationDomainError("distinct nonempty method names required")
    if sorted(names)!=sorted(set(str(x) for x in method)):
        raise Cf4CalibrationDomainError("method categories not identified in source labels")
    M=np.column_stack([L@(method==m) for m in names])
    if not np.allclose(M.sum(axis=1),1.,atol=5e-12,rtol=0):
        raise Cf4CalibrationDomainError("method fractions do not partition source weight")
    return {"names":names,"weighted_fractions":M,"logH_jacobian_mag_inv":-K_LOG*M}


def calibration_propagation(source_response, *,
                            magnitude_bounds=None,
                            magnitude_covariance=None):
    """Absolute box-bound shift and optional assumed PSD zero-point covariance.

    Common zero-point shifts affect all logH bins equally, so contrasts cancel.
    A covariance law can be singular, e.g. perfectly common-mode calibration.
    Neither model is presumed to be the true CF4 method-calibration law.
    """
    F=np.asarray(source_response["weighted_fractions"])
    names=source_response["names"]
    if F.ndim!=2 or F.shape[1]!=len(names):
        raise Cf4CalibrationDomainError("method-response shape mismatch")
    jac=-K_LOG*F
    result={"method_names":names,"response_magnitude":F,
            "logH_jacobian_mag_inv":jac}
    if magnitude_bounds is not None:
        b=np.asarray(magnitude_bounds,dtype=float)
        if (b.shape!=(len(names),) or not np.isfinite(b).all()
            or np.any(b<0)):
            raise Cf4CalibrationDomainError("nonnegative finite method magnitude box")
        result["assumed_method_magnitude_box"]=b
        result["max_abs_shift_logH_per_window"]=np.abs(jac)@b
        diff=jac[:,None,:]-jac[None,:,:]
        result["max_abs_shift_logH_pairwise_contrast"]=np.einsum(
            "ijm,m->ij",np.abs(diff),b,optimize=True)
        result["zero_common_mode_contrast"]=bool(
            np.max(abs(diff.sum(axis=2)))<1e-12
        )
    if magnitude_covariance is not None:
        cov=np.asarray(magnitude_covariance)
        if (np.iscomplexobj(cov) or cov.shape!=(len(names),len(names))
            or not np.isfinite(cov).all()
            or not np.allclose(cov,cov.T,rtol=1e-12,atol=1e-13)):
            raise Cf4CalibrationDomainError("symmetric real method covariance expected")
        eig=np.linalg.eigvalsh(cov)
        if eig[0]<-1e-12*max(abs(eig[-1]),1e-30):
            raise Cf4CalibrationDomainError("PSD method covariance required")
        shifted=jac@cov@jac.T
        shifted=(shifted+shifted.T)/2
        if np.min(np.linalg.eigvalsh(shifted))<-1e-12*max(np.linalg.norm(shifted,2),1e-30):
            raise Cf4CalibrationDomainError("propagated covariance failed PSD")
        result["assumed_magnitude_covariance"]=cov
        result["propagated_logH_covariance"]=shifted
        # IMPORTANT: do not form Var(W-V)=Var(W)+Var(V)-2 Cov(W,V).
        # That loses all digits for a rank-one perfectly common zero-point.
        # Whiten the method covariance FIRST and then difference the rows;
        # the resulting squared norm is manifestly nonnegative and stable.
        vals,vecs=np.linalg.eigh(cov)
        # LAPACK may resolve a mathematically rank-one PSD matrix with tiny
        # positive spurious eigenvalues at machine rounding. Do not pretend
        # those have measured physical covariance support. The cutoff is a
        # numerical eigensolver resolution, not an adjustable science prior.
        floor=64*np.finfo(float).eps*max(float(vals[-1]),1e-300)
        covariance_sqrt=vecs*np.sqrt(np.where(vals>floor,vals,0.))[None,:]
        contrast_jac=jac[:,None,:]-jac[None,:,:]
        contrast_white=np.einsum("ijm,mk->ijk",contrast_jac,covariance_sqrt,optimize=True)
        pair_sigma=np.linalg.norm(contrast_white,axis=2)
        result["pairwise_contrast_std_logH"]=pair_sigma
    return result


def paired_method_decomposition(weights, method,
                                window_i:int, window_j:int):
    """Physically named window contrast, remains a working-law diagnostic."""
    a=method_response(weights,method)
    L=a["weighted_fractions"]
    if (not isinstance(window_i,int) or not isinstance(window_j,int)
        or min(window_i,window_j)<0 or max(window_i,window_j)>=len(L)
        or window_i==window_j):
        raise Cf4CalibrationDomainError("two distinct valid source windows required")
    return {"method_names":a["names"],
            "weight_fraction_difference":L[window_j]-L[window_i],
            "difference_jacobian_mag_inv":(-K_LOG*(L[window_j]-L[window_i])),
            "common_offset_response":float(
                (-K_LOG*(L[window_j]-L[window_i])).sum())}
