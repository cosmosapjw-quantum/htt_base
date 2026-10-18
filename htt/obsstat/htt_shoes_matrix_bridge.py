"""Exact finite-dimensional Gaussian source/data matrix bridge for SH0ES 2022.

Official SH0ES y(3492), L(47x3492), C(3492x3492) represent a single
simultaneous distance-ladder model. This module neither constructs nor
claims the SH0ES-CF4 overlap source map or its cross covariance. A
SH0ES parameter posterior is NOT an independent CF4 likelihood.
"""
from __future__ import annotations
import numpy as np
from scipy.linalg import cholesky,cho_factor,cho_solve,solve_triangular


class Sh0esMatrixError(ValueError):
    pass


def _check(y,A,C):
    if any(np.iscomplexobj(q) for q in (y,A,C)):
        raise Sh0esMatrixError('real source vectors and covariance required')
    vec=np.asarray(y,dtype=float)
    design=np.asarray(A,dtype=float)
    cov=np.asarray(C,dtype=float)
    if (vec.ndim!=1 or design.ndim!=2 or design.shape[0]!=len(vec)
        or design.shape[1]<1 or design.shape[1]>=len(vec)
        or cov.shape!=(len(vec),len(vec))
        or not np.isfinite(vec).all() or not np.isfinite(design).all()
        or not np.isfinite(cov).all()
        or not np.allclose(cov,cov.T,rtol=1e-10,atol=1e-10)):
        raise Sh0esMatrixError('invalid SH0ES real finite same-row Gaussian system')
    return vec,design,cov


def whitened_linear_gls(y,A,C):
    """Unregularized GLS beta and full covariance, full prescribed C.

    Chi2 is the covariance-weighted fit residual, and no covariance scalar
    inflation/rescale or unreported prior is imposed. Original real matrix
    with full rank is required. Official benchmark theta from a separate
    file must be compared, never silently substituted for fitted theta.
    """
    vec,mat,cov=_check(y,A,C)
    try:
        ch=cholesky(cov,lower=True,check_finite=False)
        wy=solve_triangular(ch,vec,lower=True,check_finite=False)
        wm=solve_triangular(ch,mat,lower=True,check_finite=False)
        gram=wm.T@wm
        cg=cho_factor(gram,lower=True,check_finite=False)
        beta=cho_solve(cg,wm.T@wy,check_finite=False)
        pcov=cho_solve(cg,np.eye(mat.shape[1]),check_finite=False)
    except (np.linalg.LinAlgError,ValueError) as exc:
        raise Sh0esMatrixError(f'positive definite source covariance/full design required: {exc}') from exc
    r=wy-wm@beta
    gradient=wm.T@r
    target=wm.T@wy
    eig=np.linalg.eigvalsh(gram)
    if eig[0]<=0 or not np.isfinite(eig).all():
        raise Sh0esMatrixError('nonidentifiable/defective ladder matrix')
    out={
        'estimate':beta,
        'estimate_covariance':(pcov+pcov.T)*.5,
        'estimate_sigma':np.sqrt(np.diag(pcov)),
        'normal_matrix':gram,
        'rank':len(beta),
        'condition_number_normal_matrix':float(eig[-1]/eig[0]),
        'full_chi_squared':float(r@r),
        'residual_dof':len(vec)-len(beta),
        'normal_equation_gradient_relative':float(np.linalg.norm(gradient)/(np.linalg.norm(target)+1e-300)),
        'source_model':'fixed covariance and 47 published design parameters, no physical alternate source model'
    }
    return out


def conditional_template_information(template,A,C):
    """Fisher information for a fixed added observed-row template after Q marginalization.

    The profile curvature is ||(I-P_CA) C^-1/2 t||². It vanishes
    EXACTLY if t is in col(A); cannot transfer a SH0ES calibration
    to CF4 until a source-ID-aware loading B to shared anchors is given.
    """
    if np.iscomplexobj(template):
        raise Sh0esMatrixError('real explicit source template expected')
    t=np.asarray(template,dtype=float)
    if t.ndim!=1 or not np.isfinite(t).all():
        raise Sh0esMatrixError('real fixed finite source template required')
    a,m,c=_check(t,A,C)
    try:
        ch=cholesky(c,lower=True,check_finite=False)
        wt=solve_triangular(ch,a,lower=True,check_finite=False)
        wa=solve_triangular(ch,m,lower=True,check_finite=False)
        b=np.linalg.lstsq(wa,wt,rcond=1e-12)[0]
    except (np.linalg.LinAlgError,ValueError) as exc:
        raise Sh0esMatrixError(f'conditional projection invalid: {exc}') from exc
    raw=float(wt@wt)
    ret=float(np.linalg.norm(wt-wa@b)**2)
    if raw<=0:
        raise Sh0esMatrixError('zero template norm no information')
    return {
        'raw_fisher_information':raw,
        'conditioned_fisher_information':ret,
        'retained_information_fraction':float(np.clip(ret/raw,0,1)),
        'projected_parameter_norm':float(np.linalg.norm(b)),
        'interpretation':'algebraic source-template nuisance quotient, no inferred H0/CF4 zeropoint or SH0ES alternative likelihood'
    }


def assert_cross_catalogue_source_map(cross_loading,ladder_parameter_covariance,*,n_cf4):
    """Require explicit CF4-to-ladder parameter loadings and verified positive PSD.

    This only computes a *hypothetical mathematical transfer* B V B^T.
    Without published source/event identity and the true same-anchor loading
    this function must NOT be used to declare an empirical CF4 prior.
    """
    if cross_loading is None:
        raise Sh0esMatrixError('cross-catalogue matched source loading is REQUIRED')
    if np.iscomplexobj(cross_loading) or np.iscomplexobj(ladder_parameter_covariance):
        raise Sh0esMatrixError('real matched source calibration loadings required')
    b=np.asarray(cross_loading,dtype=float)
    cov=np.asarray(ladder_parameter_covariance,dtype=float)
    if (b.ndim!=2 or b.shape[0]!=n_cf4 or cov.shape!=(b.shape[1],b.shape[1])
        or not np.isfinite(b).all() or not np.isfinite(cov).all()
        or not np.allclose(cov,cov.T,atol=1e-11,rtol=1e-10)
        or np.linalg.eigvalsh(cov)[0]<=0):
        raise Sh0esMatrixError('calibrator prior/CF4 source-map identity not qualified')
    result=b@cov@b.T
    return (result+result.T)*.5


def joint_shared_anchor_covariance(D_first,D_second,loading_first,loading_second,
                                  shared_anchor_covariance):
    """Joint Gaussian covariance under ONE common multi-method anchor vector.

    This is a closed finite mathematical law for any source-qualified
    loading matrices. It does NOT construct a real SH0ES-CF4 source map,
    and it must not be applied to published datasets without matching
    common source IDs and the validated same-anchor parameterization.

    [D1+Z1 K Z1.T, Z1 K Z2.T]
    [Z2 K Z1.T, D2+Z2 K Z2.T]
    """
    arrays=(D_first,D_second,loading_first,loading_second,shared_anchor_covariance)
    if any(np.iscomplexobj(x) for x in arrays):
        raise Sh0esMatrixError('real source-level covariance required')
    d1,d2,z1,z2,k=map(lambda x:np.asarray(x,dtype=float),arrays)
    if (d1.ndim!=2 or d1.shape[0]!=d1.shape[1] or
        d2.ndim!=2 or d2.shape[0]!=d2.shape[1] or
        z1.shape[0]!=len(d1) or z2.shape[0]!=len(d2) or
        z1.ndim!=2 or z2.ndim!=2 or
        z1.shape[1]!=z2.shape[1] or k.shape!=(z1.shape[1],z1.shape[1]) or
        not all(np.isfinite(x).all() for x in (d1,d2,z1,z2,k)) or
        not all(np.allclose(x,x.T,atol=1e-12,rtol=1e-10) for x in (d1,d2,k))):
        raise Sh0esMatrixError('joint measurement/calibrator matrix contract invalid')
    if np.linalg.eigvalsh(d1)[0]<=0 or np.linalg.eigvalsh(d2)[0]<=0:
        raise Sh0esMatrixError('strict measurement covariance positive definite needed')
    if np.linalg.eigvalsh(k)[0]<-1e-11*max(1.,np.linalg.norm(k)):
        raise Sh0esMatrixError('source-anchor common covariance must be PSD')
    z=np.vstack((z1,z2))
    from scipy.linalg import block_diag
    full=block_diag(d1,d2)+z@((k+k.T)*.5)@z.T
    return (full+full.T)*.5
