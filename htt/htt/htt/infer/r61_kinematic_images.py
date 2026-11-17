"""Confidence images of one full-covariance kinematic experiment.

The Gaussian confidence cutoff is supplied by the caller. It is never replaced
by a scalar chi-square cutoff merely because the reported image is scalar.
Quadratic extrema use the global trust-region dual, including the hard case.
Certificates are floating-point primal/dual checks, not interval-arithmetic
proofs. Deterministic calibration budgets remain sensitivity assumptions.
"""
from __future__ import annotations

import numpy as np
from scipy import linalg, optimize

C_KM_S = 299792.458
MAG_PER_LOG_DISTANCE = 5.0 / np.log(10.0)


def stf_basis():
    e = np.zeros((5, 3, 3))
    e[0] = np.diag([1., -1., 0.]) / np.sqrt(2.)
    e[1] = np.diag([1., 1., -2.]) / np.sqrt(6.)
    for k, (i, j) in enumerate([(0, 1), (0, 2), (1, 2)], 2):
        e[k, i, j] = e[k, j, i] = 1. / np.sqrt(2.)
    return e


def _vector(x, name):
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or x.size == 0 or not np.isfinite(x).all():
        raise ValueError(name + ' must be a nonempty finite vector')
    return x


def _symmetric(a, n, name, *, positive=False):
    a = np.asarray(a, dtype=float)
    if a.shape != (n, n) or not np.isfinite(a).all():
        raise ValueError(name + ' has invalid shape or nonfinite entries')
    scale = max(float(np.max(np.abs(a))), np.finfo(float).tiny)
    if np.max(np.abs(a - a.T)) > 1e-11 * scale:
        raise ValueError(name + ' must be symmetric')
    a = .5 * (a + a.T)
    if positive:
        try:
            linalg.cholesky(a, lower=True)
        except linalg.LinAlgError as exc:
            raise ValueError(name + ' must be positive definite') from exc
    return a


def quadratic_ball_extreme(matrix, linear, constant=0., *, sense='min'):
    """Extremize u.T B u + 2 b.T u + c on ||u||<=1.

    Returns a feasible witness and global dual enclosure. Minima satisfy
    (B+lambda I)u=-b, lambda>=0, B+lambda I>=0 and complementarity.
    The dual lower bound is c-lambda-b.T(B+lambda I)^-1 b.
    A tiny positive shift resolves the dual in singular hard cases; the
    resulting numerical gap is exposed rather than hidden by rank truncation.
    """
    b = _vector(linear, 'linear')
    B = _symmetric(matrix, b.size, 'matrix')
    if sense not in ('min', 'max') or not np.isfinite(constant):
        raise ValueError('invalid sense or constant')
    sign = 1. if sense == 'min' else -1.
    B, b, c = sign * B, sign * b, sign * float(constant)
    scale = max(float(np.linalg.norm(B, 2)), float(np.linalg.norm(b)),
                np.finfo(float).tiny)
    if not np.any(B) and not np.any(b):
        return dict(value=sign*c, bound=sign*c, optimality_gap=0.,
                    witness=np.zeros(b.size), multiplier=0., norm=0.,
                    stationarity=0., hard_case=False, sense=sense)
    d, U = linalg.eigh(B / scale)
    g = U.T @ (b / scale)
    lower = max(0., -float(d[0]))
    eps_shift = 256. * np.finfo(float).eps * max(1., float(np.max(np.abs(d))))
    safe_lower = lower + eps_shift
    at = -g / (d + safe_lower)
    hard = False
    if lower == 0. and d[0] > eps_shift:
        free = -g / d
        if np.linalg.norm(free) <= 1.:
            coords, lam = free, 0.
        else:
            coords = None
    else:
        coords = None
    if coords is None:
        if np.linalg.norm(at) > 1.:
            def norm_excess(lam):
                return float(np.linalg.norm(g / (d + lam)) - 1.)
            upper = max(1., 2.*safe_lower, float(np.linalg.norm(g)) + np.max(np.abs(d)))
            while norm_excess(upper) > 0.:
                upper *= 2.
            lam = optimize.brentq(norm_excess, safe_lower, upper,
                                   xtol=np.nextafter(0., 1.), rtol=1e-14, maxiter=256)
            coords = -g / (d + lam)
        elif lower == 0.:
            # PSD singular/interior case; the dual shift quantifies the small
            # regularization used to obtain a feasible representative.
            coords, lam = at, 0.
        else:
            # The minimum-eigenvalue eigenspace supplies the missing norm.
            # Any unresolved nonzero forcing is visible in the dual gap.
            coords = at.copy()
            coords[0] = 0.
            remaining = max(0., 1. - float(coords @ coords))
            coords[0] = (-1. if g[0] >= 0. else 1.) * np.sqrt(remaining)
            lam, hard = lower, True
    norm = float(np.linalg.norm(coords))
    if norm > 1.:
        coords /= norm
    u = U @ coords
    u /= max(1., float(np.linalg.norm(u)))
    value_min = float(u @ B @ u + 2.*b @ u + c)
    lam_cert = max(lam, safe_lower)
    den = d + lam_cert
    if np.any(den <= 0.):
        raise ArithmeticError('dual shift did not resolve positive definiteness')
    bound_min = c - scale * (lam_cert + float(np.sum(g*g / den)))
    numerical_pad = 128.*np.finfo(float).eps * (abs(c) + scale * (1.+np.linalg.norm(g)))
    bound_min -= numerical_pad
    gap = value_min - bound_min
    if gap < -numerical_pad or not np.isfinite(gap):
        raise ArithmeticError('invalid trust-region primal/dual comparison')
    gap = max(0., float(gap))
    if gap > 2e-9 * (scale + abs(c)):
        raise ArithmeticError('unresolved trust-region extremum; primal/dual gap too large')
    return dict(value=sign*value_min, bound=sign*bound_min,
                optimality_gap=gap, witness=u, multiplier=float(lam*scale),
                norm=float(np.linalg.norm(u)),
                stationarity=float(np.linalg.norm(B@u+b+lam*scale*u)),
                hard_case=hard, sense=sense)


def quadratic_ellipsoid_range(center, covariance, matrix, *, linear=None,
                              constant=0., cutoff):
    """Global image of x.T M x + l.T x + c on one supplied ellipsoid."""
    h = _vector(center, 'center')
    C = _symmetric(covariance, h.size, 'covariance', positive=True)
    M = _symmetric(matrix, h.size, 'matrix')
    ell = np.zeros_like(h) if linear is None else _vector(linear, 'linear')
    if ell.shape != h.shape or not np.isfinite(cutoff) or cutoff <= 0.:
        raise ValueError('invalid linear vector or confidence cutoff')
    A = np.sqrt(cutoff) * linalg.cholesky(C, lower=True)
    B, b = A.T @ M @ A, A.T @ (M@h+.5*ell)
    c = float(h@M@h + ell@h + constant)
    results = {}
    for sense in ['min', 'max']:
        ans = quadratic_ball_extreme(B, b, c, sense=sense)
        u = ans['witness'].copy()
        x = h + A @ u
        direct = float(x@M@x + ell@x + constant)
        ans.update(parameter_witness=x, ball_witness=u,
                   direct_value=direct, mahalanobis2=float(cutoff*(u@u)))
        results[sense] = ans
    return dict(lower=results['min']['bound'], upper=results['max']['bound'],
                feasible_lower=results['min']['direct_value'],
                feasible_upper=results['max']['direct_value'],
                minimum=results['min'], maximum=results['max'], cutoff=float(cutoff),
                guarantee='global trust-region characterization; floating primal/dual enclosure')


def norm_ellipsoid_range(center, covariance, *, cutoff):
    h = _vector(center, 'center')
    ans = quadratic_ellipsoid_range(h, covariance, np.eye(h.size), cutoff=cutoff)
    return dict(lower=float(np.sqrt(max(0., ans['lower']))),
                upper=float(np.sqrt(max(0., ans['upper']))),
                feasible_lower=float(np.linalg.norm(ans['minimum']['parameter_witness'])),
                feasible_upper=float(np.linalg.norm(ans['maximum']['parameter_witness'])),
                quadratic_result=ans)


def inflated_norm_range(center, covariance, *, cutoff, calibration_radius=0., divisor=1.):
    """Exact norm endpoints for an ellipsoid plus a Euclidean ball."""
    if (not np.isfinite(calibration_radius) or calibration_radius < 0.
            or not np.isfinite(divisor) or divisor <= 0.):
        raise ValueError('invalid calibration radius or divisor')
    ans = norm_ellipsoid_range(center, covariance, cutoff=cutoff)
    return dict(lower=max(0., ans['lower']-calibration_radius)/divisor,
                upper=(ans['upper']+calibration_radius)/divisor,
                statistical=ans, calibration_radius=float(calibration_radius),
                divisor=float(divisor),
                geometry='ellipsoid Minkowski-summed with Euclidean calibration ball')


def kinematic_images(center11, covariance11, *, cutoff, rho=0.):
    """Conditional images in s=sigma/H, a=A/(cH), beta=V/c.

    Calibration xi=(dcal,qcal) has xi.T diag(I3/3,2I5/15) xi<=rho².
    Absolute H and omega are absent from this experiment. Point estimates
    below use zero calibration; finite budgets produce set-valued inference.
    """
    h = _vector(center11, 'center11')
    if h.shape != (11,) or not np.isfinite(rho) or rho < 0.:
        raise ValueError('need alpha11 and finite nonnegative rho')
    C = _symmetric(covariance11, 11, 'covariance11', positive=True)
    beta = inflated_norm_range(h[:3]/C_KM_S, C[:3,:3]/C_KM_S**2,
                               cutoff=cutoff)
    accel = inflated_norm_range(-h[3:6], C[3:6,3:6], cutoff=cutoff,
                                calibration_radius=np.sqrt(3.)*rho)
    shear = inflated_norm_range(h[6:], C[6:,6:], cutoff=cutoff,
                                calibration_radius=np.sqrt(7.5)*rho, divisor=np.sqrt(6.))
    angular_weight = np.sqrt(np.r_[np.ones(3)/3., np.ones(5)*2./15.])
    angular = inflated_norm_range(angular_weight*h[3:],
                 angular_weight[:,None]*C[3:,3:]*angular_weight[None,:],
                 cutoff=cutoff, calibration_radius=rho)
    M = np.zeros((11,11))
    for j in range(3): M[j,j+3] = M[j+3,j] = -1./(2.*C_KM_S)
    work = quadratic_ellipsoid_range(h,C,M,cutoff=cutoff)
    enlargement = np.sqrt(3.)*rho*beta['upper']
    work['with_calibration'] = dict(lower=work['lower']-enlargement,
             upper=work['upper']+enlargement, radius=enlargement,
             sharp=bool(rho==0.),
             meaning='conservative enclosure using the same ellipsoid beta-norm upper bound')
    widths = np.sqrt(cutoff*np.diag(C))
    blo,bhi=(h[:3]-widths[:3])/C_KM_S,(h[:3]+widths[:3])/C_KM_S
    alo,ahi=-h[3:6]-widths[3:6],-h[3:6]+widths[3:6]
    products=np.stack([blo*alo,blo*ahi,bhi*alo,bhi*ahi])
    boxlower,boxupper=float(products.min(axis=0).sum()),float(products.max(axis=0).sum())
    work['coordinate_box_comparator'] = dict(lower=boxlower,upper=boxupper,
               width_ratio=(boxupper-boxlower)/(work['upper']-work['lower']),
               meaning='box containing same simultaneous ellipsoid; no independence assumption')
    return dict(Sigma=shear,acceleration_over_cH=accel,relative_speed_over_c=beta,
                directional_expansion_rms=angular,beta_dot_a=work,
                point_zero_calibration=dict(Sigma=float(np.linalg.norm(h[6:])/np.sqrt(6.)),
                    acceleration_over_cH=float(np.linalg.norm(h[3:6])),
                    relative_speed_over_c=float(np.linalg.norm(h[:3])/C_KM_S),
                    directional_expansion_rms=float(np.linalg.norm(angular_weight*h[3:])),
                    beta_dot_a=float(-h[:3]@h[3:6]/C_KM_S)),
                cutoff=float(cutoff),rho=float(rho),
                calibration_rms_magnitude=float(MAG_PER_LOG_DISTANCE*rho))


def directional_expansion_support(center11,covariance11,directions,*,cutoff,rho=0.):
    """Simultaneous projection of H_dir/H-1 = -a.n+s:nn."""
    h=_vector(center11,'center11'); C=_symmetric(covariance11,11,'covariance11',positive=True)
    n=np.asarray(directions,float)
    if (h.size!=11 or n.ndim!=2 or n.shape[1]!=3 or not np.isfinite(n).all()
            or np.max(np.abs(np.linalg.norm(n,axis=1)-1.))>1e-10
            or not np.isfinite(rho) or rho<0 or not np.isfinite(cutoff) or cutoff<=0):
        raise ValueError('invalid directional support inputs')
    contrasts=np.column_stack((np.zeros_like(n),n,np.einsum('ni,aij,nj->na',n,stf_basis(),n)))
    center=contrasts@h
    statistical=np.sqrt(cutoff*np.einsum('ni,ij,nj->n',contrasts,C,contrasts))
    calibration=np.sqrt(8.)*rho
    return dict(center=center,lower=center-statistical-calibration,
                upper=center+statistical+calibration,statistical_radius=statistical,
                calibration_radius=float(calibration),
                meaning='all directions share one joint confidence set; sampled directions do not certify a sky extremum')
