"""Conditional optical response and shared seven-component compatibility.

All angular tensors use one orthonormal observer rest-frame basis and Frobenius
norms. This module does not assign physical meaning to catalogue harmonics.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import norm as robust_norm
from scipy.optimize import minimize
import mpmath as mp

KAPPA = 5.0 / np.log(10.0)


def stf2(a):
    a = np.asarray(a, float)
    return (a + a.T) / 2 - np.trace(a) * np.eye(3) / 3


def stf3(a):
    a = np.asarray(a, float)
    a = sum(np.transpose(a, p) for p in ((0, 1, 2), (0, 2, 1), (1, 0, 2),
                                          (1, 2, 0), (2, 0, 1), (2, 1, 0))) / 6
    t = np.einsum('iik->k', a)
    return a - (np.einsum('ij,k->ijk', np.eye(3), t)
                + np.einsum('ik,j->ijk', np.eye(3), t)
                + np.einsum('jk,i->ijk', np.eye(3), t)) / 5


def stf_basis(rank):
    """Deterministic Frobenius-orthonormal basis, without absolute scale cutoffs."""
    if rank not in (2, 3):
        raise ValueError('rank must be 2 or 3')
    basis = []
    for index in np.ndindex(*([3] * rank)):
        a = np.zeros([3] * rank)
        a[index] = 1
        v = (stf2(a) if rank == 2 else stf3(a)).ravel()
        for b in basis:
            v -= np.dot(v, b) * b
        norm = np.linalg.norm(v)
        if norm > 1e-13:  # fixed unit monomials only; not an input-domain threshold
            basis.append(v / norm)
    assert len(basis) == (5 if rank == 2 else 7)
    return np.array(basis).reshape((-1,) + (3,) * rank)


B2 = stf_basis(2)
B3 = stf_basis(3)


def validate_s(s):
    s = np.asarray(s, float)
    if s.shape != (3, 3) or not np.isfinite(s).all():
        raise ValueError('S must be finite 3x3')
    scale = np.max(np.abs(s))
    if scale and robust_norm(s / scale - stf2(s / scale)) > 1e-12 * robust_norm(s / scale):
        raise ValueError('S must be symmetric trace-free')
    return s


def lift_matrix(s):
    """Seven by three coordinates of L_S d = STF(sym(d tensor S))."""
    s = validate_s(s)
    eye = np.eye(3)
    return np.array([[np.einsum('ijk,ijk', b, stf3(np.einsum('i,jk->ijk', e, s)))
                      for e in eye] for b in B3])


def m_matrix(s):
    s = validate_s(s)
    return np.sum(s * s) * np.eye(3) / 3 + 2 * (s @ s) / 5


def joint_budget(epsilon, e_o, b_z, b_sel, e_s, d_max, kappa=KAPPA):
    """Hubble protocol H7 outer-ball radius; all terms dimensionless magnitude."""
    values = np.array([epsilon, e_o, b_z, b_sel, e_s, d_max], float)
    if not np.isfinite(values).all() or (values < 0).any() or epsilon >= 1:
        raise ValueError('finite nonnegative terms and epsilon < 1 required')
    e3 = np.sqrt(35 / 2) * abs(kappa) * epsilon**3 / (3 * (1 - epsilon))
    return {'angular_E3': e3, 'observational_eO': e_o, 'finite_z_Bz': b_z,
            'selection_Bsel': b_sel,
            'uncertain_S': abs(kappa) * np.sqrt(3 / 5) * e_s * d_max,
            'total': e3 + e_o + b_z + b_sel + abs(kappa) * np.sqrt(3 / 5) * e_s * d_max}


class NumericalProfileFailure(RuntimeError):
    """A mathematical compatibility verdict could not be certified numerically."""

    def __init__(self, code, detail):
        self.code = code
        super().__init__(f'{code}: {detail}')


def _safe_norm(v):
    """BLAS scaled sum of squares; np.linalg.norm underflows at 1e-200."""
    return float(robust_norm(np.asarray(v, float)))


def _checked_matvec(a, v):
    """Raise if finite binary64 silently loses a nonzero matrix-vector term."""
    exact_range = np.asarray(a, np.longdouble) @ np.asarray(v, np.longdouble)
    result = np.asarray(a, float) @ np.asarray(v, float)
    if not np.isfinite(result).all() or np.any((exact_range != 0) & (result == 0)):
        raise NumericalProfileFailure('NUMERIC_RANGE', 'matrix-vector response underflow/overflow')
    return result


def _mp_float(v):
    """Exact binary64 input interpreted in a 100-decimal-digit work context."""
    num, den = float(v).as_integer_ratio()
    return mp.mpf(num) / den


def _mp_norm(v):
    return mp.sqrt(sum(x*x for x in v))


def _mp_data(o, k, d_obs, e_d, d_max, budget):
    om = [_mp_float(x) for x in o]
    km = [[_mp_float(x) for x in row] for row in k]
    dm = [_mp_float(x) for x in d_obs]
    return om, km, dm, _mp_float(e_d), None if d_max is None else _mp_float(d_max), _mp_float(budget)


def _mp_feasible(d, center, e_d, d_max):
    if _mp_norm([d[i]-center[i] for i in range(3)]) > e_d:
        return False
    return d_max is None or _mp_norm(d) <= d_max


def _feasible_anchor(d_obs, e_d, d_max):
    """A known feasible point, or None for an empty/tangent numeric case."""
    if d_max is None or _verified_feasible(d_obs,d_obs,e_d,d_max):
        return d_obs.copy()
    n = _safe_norm(d_obs)
    if n == 0:
        return d_obs.copy()
    # Move strictly inside the physical ball; verify the original direct ball
    # later with exact-binary arithmetic, never a normalized optimizer slack.
    d = d_obs*min(1.0,d_max/n)*(1-16*np.finfo(float).eps)
    return d if _verified_feasible(d,d_obs,e_d,d_max) else None


def _verified_feasible(d, d_obs, e_d, d_max):
    if d is None or not np.isfinite(d).all():
        return False
    with mp.workdps(100):
        center=[_mp_float(x) for x in d_obs]
        return _mp_feasible([_mp_float(x) for x in d], center,
                            _mp_float(e_d), None if d_max is None else _mp_float(d_max))


def _repair_witness(candidate, anchor, d_obs, e_d, d_max):
    """Move an optimizer proposal toward a proven feasible anchor.

    This only changes the candidate. The final decision recomputes its
    seven-component response from the exact binary64 values.
    """
    if _verified_feasible(candidate,d_obs,e_d,d_max):
        return candidate
    if not _verified_feasible(anchor,d_obs,e_d,d_max):
        return None
    lo,hi=0.0,1.0
    best=anchor
    for _ in range(60):
        mid=(lo+hi)/2
        trial=anchor+mid*(candidate-anchor)
        if _verified_feasible(trial,d_obs,e_d,d_max):
            lo=mid; best=trial
        else:
            hi=mid
    return best


def _profile_candidate(o, k, d_obs, e_d, d_max):
    """Optimization proposes a point; it never certifies a verdict."""
    if e_d == 0:
        return d_obs.copy(), 'FIXED_DIRECT_DIPOLE'
    if d_max == 0:
        return np.zeros(3), 'SINGLETON_PHYSICAL_SET'
    a = k*e_d
    if np.any((np.asarray(k,np.longdouble)*np.longdouble(e_d) != 0) & (a == 0)):
        raise NumericalProfileFailure('NUMERIC_RANGE','direct-ball response underflow')
    a_scale = np.max(np.abs(a))
    anchor = _feasible_anchor(d_obs,e_d,d_max)
    if a_scale == 0:
        return anchor, 'FLAT_RESPONSE_ANCHOR'
    a_unit = a/a_scale
    b = o-_checked_matvec(k,d_obs)
    h = a_unit.T@a_unit
    # Normalize by the nonzero varying curvature. A large fixed perpendicular
    # residual or B must not create an arbitrary stationarity floor.
    g_long = np.asarray(a_unit,np.longdouble).T@np.asarray(b,np.longdouble)/np.longdouble(a_scale)
    if not np.isfinite(g_long).all() or np.any(np.abs(g_long)>np.finfo(float).max):
        raise NumericalProfileFailure('NUMERIC_RANGE','normalized linear objective outside binary64')
    g = np.asarray(g_long,float)
    x_ls = np.linalg.solve(h,g)
    if np.isfinite(x_ls).all():
        d_ls = d_obs+e_d*x_ls
        if np.isfinite(d_ls).all() and _safe_norm(x_ls)<1 and (d_max is None or _safe_norm(d_ls)<d_max):
            return d_ls, 'UNCONSTRAINED_LS_CANDIDATE'
    d_scale = max(np.max(np.abs(d_obs)),e_d,d_max or 0.0)
    center=d_obs/d_scale; width=e_d/d_scale
    radius=None if d_max is None else d_max/d_scale
    x0=np.zeros(3) if anchor is None else (anchor-d_obs)/e_d
    def objective(x): return .5*x@h@x-g@x
    def gradient(x): return h@x-g
    constraints=[{'type':'ineq','fun':lambda x:1-x@x,'jac':lambda x:-2*x}]
    if radius is not None:
        constraints.append({'type':'ineq',
            'fun':lambda x:radius**2-(center+width*x)@(center+width*x),
            'jac':lambda x:-2*width*(center+width*x)})
    sol=minimize(objective,x0,jac=gradient,constraints=constraints,
                 method='SLSQP',options={'ftol':1e-14,'maxiter':1200})
    if not np.isfinite(sol.x).all():
        raise NumericalProfileFailure('NUMERICAL_FAILURE','nonfinite candidate optimizer iterate')
    candidate=d_obs+e_d*sol.x
    if not np.isfinite(candidate).all():
        raise NumericalProfileFailure('NUMERIC_RANGE','candidate reconstruction outside binary64')
    # Projection is only a candidate repair. The scientific decision below
    # independently rechecks both original balls and the recomputed residual.
    candidate=_repair_witness(candidate,anchor,d_obs,e_d,d_max)
    return candidate, 'NORMALIZED_QUADRATIC_CANDIDATE'


def _norm_certificate(o, k, d_obs, e_d, d_max, budget, candidate):
    """Primal upper and norm-support dual lower bounds in high precision.

    For any unit u, ||O-Kd|| >= u.O-u.Kd. The support of an intersection
    is at most the minimum of each ball support. This lower bound is valid
    without optimizer convergence. Conservative source/rounding envelopes
    are applied before either decision.
    """
    with mp.workdps(100):
        om,km,center,ed,physical,bm=_mp_data(o,k,d_obs,e_d,d_max,budget)
        center_norm=_mp_norm(center)
        if physical is not None and center_norm>ed+physical:
            return {'status':'PHYSICAL_SET_EMPTY'}
        cap=center_norm+ed if physical is None else min(center_norm+ed,physical)
        kf=mp.sqrt(sum(x*x for row in km for x in row))
        on=_mp_norm(om)
        operator_error=64*_mp_float(np.finfo(float).eps)*kf*cap
        global_allowance=64*_mp_float(np.finfo(float).eps)*max(on,kf*cap)
        scale=max(on,kf*cap,bm)
        mp_error=mp.mpf('1e-75')*scale
        if candidate is None:
            candidate=_feasible_anchor(d_obs,e_d,d_max)
        if candidate is None:
            raise NumericalProfileFailure('NUMERICAL_FAILURE','no representable feasible witness')
        witness=[_mp_float(x) for x in candidate]
        if not _mp_feasible(witness,center,ed,physical):
            fallback=_feasible_anchor(d_obs,e_d,d_max)
            if fallback is None:
                raise NumericalProfileFailure('NUMERICAL_FAILURE','candidate outside both original balls')
            witness=[_mp_float(x) for x in fallback]
            if not _mp_feasible(witness,center,ed,physical):
                raise NumericalProfileFailure('NUMERICAL_FAILURE','no verified original-ball witness')
            candidate=fallback
        predicted=[sum(km[i][j]*witness[j] for j in range(3)) for i in range(7)]
        residual=[om[i]-predicted[i] for i in range(7)]
        rn=_mp_norm(residual); pn=_mp_norm(predicted)
        cancellation=(on>0 and pn>0 and rn<=mp.mpf('.5')*max(on,pn))
        local_allowance=64*_mp_float(np.finfo(float).eps)*max(on,pn) if cancellation else mp.mpf(0)
        upper=rn+operator_error+mp_error
        directions=[]
        if on>0: directions.append([x/on for x in om])
        if rn>0: directions.append([x/rn for x in residual])
        lower=mp.mpf(0)
        for u in directions:
            kt=[sum(km[i][j]*u[i] for i in range(7)) for j in range(3)]
            kt_norm=_mp_norm(kt)
            direct=sum(kt[j]*center[j] for j in range(3))+ed*kt_norm
            support=direct if physical is None else min(direct,physical*kt_norm)
            bound=sum(u[i]*om[i] for i in range(7))-support
            lower=max(lower,bound)
        lower=max(mp.mpf(0),lower-operator_error-mp_error)
        if upper<=bm+local_allowance:
            verdict=True
        elif lower>bm+global_allowance:
            verdict=False
        else:
            raise NumericalProfileFailure('NUMERICAL_FAILURE',
                'certified residual interval straddles the unchanged budget')
        def finite_output(v,label):
            f=float(v)
            if not np.isfinite(f) or (v!=0 and f==0):
                raise NumericalProfileFailure('NUMERIC_RANGE',f'{label} outside binary64 display range')
            return f
        return {'status':'NORM_BOUNDS_CERTIFIED','compatible':verdict,
                'witness':candidate.tolist(),'residual_norm':finite_output(rn,'residual norm'),
                'lower_bound':finite_output(lower,'lower bound') if lower else 0.0,
                'upper_bound':finite_output(upper,'upper bound') if upper else 0.0,
                'operator_error_envelope':finite_output(operator_error,'operator envelope') if operator_error else 0.0,
                'cancellation_allowance':finite_output(local_allowance,'cancellation allowance') if local_allowance else 0.0,
                'roundoff_allowance_applied':bool(cancellation),
                'direct_distance':finite_output(_mp_norm([witness[i]-center[i] for i in range(3)]),'direct distance'),
                'physical_norm':finite_output(_mp_norm(witness),'physical norm')}


def _display_square(v,label):
    exact=np.longdouble(v)*np.longdouble(v)
    if not np.isfinite(exact) or exact>np.finfo(float).max:
        raise NumericalProfileFailure('NUMERIC_RANGE',f'{label} square outside binary64 display range')
    if exact!=0 and exact<np.nextafter(0.0,1.0):
        return None,'BELOW_BINARY64_RANGE_DISPLAY_ONLY'
    return float(exact),'FINITE'


def joint_test(o, s, d_obs, budget, e_d=0.0, d_max=None, kappa=KAPPA):
    """Original-ball membership from a verified witness or conservative bound."""
    o=np.asarray(o,float); d_obs=np.asarray(d_obs,float); s=validate_s(s)
    if o.shape!=(7,) or d_obs.shape!=(3,) or not np.isfinite(o).all() or not np.isfinite(d_obs).all():
        raise ValueError('finite seven-component O and three-component d required')
    if not np.isfinite([budget,e_d,kappa]).all() or budget<0 or e_d<0 or kappa==0:
        raise ValueError('finite nonnegative radii and nonzero kappa required')
    if d_max is not None and (not np.isfinite(d_max) or d_max<0):
        raise ValueError('invalid physical dipole radius')
    s_scale=np.max(np.abs(s))
    l_unit=lift_matrix(s/s_scale) if s_scale else np.zeros((7,3))
    k=(kappa*s_scale)*l_unit
    if d_max is not None:
        with mp.workdps(100):
            center=[_mp_float(x) for x in d_obs]
            if _mp_norm(center)>_mp_float(e_d)+_mp_float(d_max):
                return {'compatible':False,'physical_set_empty':True,
                        'reason':'direct and physical dipole balls do not intersect',
                        'profile_certificate':{'status':'PHYSICAL_SET_EMPTY'}}
    candidate,method=_profile_candidate(o,k,d_obs,e_d,d_max)
    cert=_norm_certificate(o,k,d_obs,e_d,d_max,budget,candidate)
    if cert['status']=='PHYSICAL_SET_EMPTY':
        return {'compatible':False,'physical_set_empty':True,
                'reason':'direct and physical dipole balls do not intersect',
                'profile_certificate':cert}
    d=np.asarray(cert['witness'],float)
    predicted=_checked_matvec(k,d)
    yscale=max(np.max(np.abs(o)),np.max(np.abs(predicted)))
    if yscale==0: yscale=1.0
    os=o/yscale; ps=predicted/yscale
    rn_scaled=_safe_norm(os-ps)
    if s_scale==0:
        perp_norm=cert['residual_norm']; parallel_norm=0.0
        inverse_d=None; branch='S_ZERO_DIRECT_MEMBERSHIP'
    else:
        m_unit=l_unit.T@l_unit
        coord=np.linalg.solve(m_unit,l_unit.T@os)
        perp_norm=yscale*_safe_norm(os-l_unit@coord)
        parallel_norm=yscale*_safe_norm(l_unit@coord-ps)
        if abs(np.hypot(_safe_norm(os-l_unit@coord),_safe_norm(l_unit@coord-ps))-rn_scaled)>64*np.finfo(float).eps*max(_safe_norm(os),_safe_norm(ps)):
            raise NumericalProfileFailure('NUMERICAL_FAILURE','seven-component split fails at signal scale')
        d_hat=(yscale/(kappa*s_scale))*coord
        if not np.isfinite(d_hat).all():
            raise NumericalProfileFailure('NUMERIC_RANGE','inverse dipole outside binary64 range')
        inverse_d=d_hat.tolist(); branch='INVERTIBLE_S'
    residual_sq,residual_sq_status=_display_square(cert['residual_norm'],'residual')
    perp_sq,perp_sq_status=_display_square(perp_norm,'perpendicular')
    parallel_sq,parallel_sq_status=_display_square(parallel_norm,'parallel')
    score=None if budget==0 else cert['upper_bound']/budget
    if score is not None and not np.isfinite(score):
        raise NumericalProfileFailure('NUMERIC_RANGE','profile upper-score outside binary64')
    return {'branch':branch,'perpendicular_norm':perp_norm,'parallel_norm':parallel_norm,
            'perpendicular_squared':perp_sq,'parallel_squared':parallel_sq,
            'squared_display_status':{'residual':residual_sq_status,'perpendicular':perp_sq_status,'parallel':parallel_sq_status},
            'inverse_d':inverse_d,'profiled_d':d.tolist(),'residual_norm':cert['residual_norm'],
            'residual_squared':residual_sq,'budget':float(budget),'score':score,
            'score_kind':'CERTIFIED_UPPER_BOUND' if budget else 'UNDEFINED_ZERO_BUDGET',
            'certified_lower_bound':cert['lower_bound'],'certified_upper_bound':cert['upper_bound'],
            'compatible':bool(cert['compatible']),'physical_set_empty':False,
            'profile_certificate':{**cert,'candidate_method':method},
            'roundoff_allowance_applied':cert['roundoff_allowance_applied']}


def source_design(n):
    """Raw magnitude fit: intercept, signed dipole, STF2, STF3."""
    n = np.asarray(n, float)
    if n.ndim != 2 or n.shape[1] != 3 or not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n, axis=1), 1, atol=1e-12):
        raise ValueError('unit source directions required')
    return np.column_stack((np.ones(len(n)), n,
                            np.einsum('aij,ni,nj->na', B2, n, n),
                            np.einsum('aijk,ni,nj,nk->na', B3, n, n, n)))


def raw_estimator(n, weights=None):
    """Return K: sampled raw magnitudes -> (direct d, seven O)."""
    x = source_design(n)
    if weights is None:
        weights = np.ones(len(x))
    weights = np.asarray(weights, float)
    if weights.shape != (len(x),) or not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError('positive finite source weights required')
    xw = x * np.sqrt(weights[:, None])
    if np.linalg.matrix_rank(xw) != 16:
        raise ValueError('selected design loses signed STF information')
    fit = np.linalg.pinv(xw) @ np.diag(np.sqrt(weights))
    selector = np.zeros((10, 16))
    selector[:3, 1:4] = -np.eye(3) / KAPPA
    selector[3:, 9:] = np.eye(7)
    return selector @ fit


def raw_to_target(n, s, d, weights=None, raw_covariance=None):
    """Exact finite sampling response and local Jacobian before data attribution."""
    n = np.asarray(n, float)
    s = validate_s(s)
    d = np.asarray(d, float)
    q = n @ d + np.einsum('ni,ij,nj->n', n, s, n)
    if np.min(1 + q) <= 0:
        raise ValueError('logarithm physical domain fails')
    y = -KAPPA * np.log1p(q)
    k = raw_estimator(n, weights)
    summary = k @ y
    v = np.column_stack((n, np.einsum('aij,ni,nj->na', B2, n, n)))
    jac = k @ (-KAPPA * v / (1 + q[:, None]))
    result = {'raw_magnitude': y, 'summary': summary, 'jacobian_d_S': jac,
              'estimator': k, 'source_response': v}
    if raw_covariance is not None:
        c = np.asarray(raw_covariance, float)
        if c.shape != (len(n), len(n)) or not np.isfinite(c).all() or not np.allclose(c, c.T, atol=1e-12):
            raise ValueError('finite symmetric full raw covariance required')
        if np.min(np.linalg.eigvalsh(c)) < -1e-12 * max(np.linalg.norm(c, 2), np.finfo(float).tiny):
            raise ValueError('raw covariance not positive semidefinite')
        result['summary_covariance'] = k @ c @ k.T
    return result


def residual_covariance(summary_covariance, s, kappa=KAPPA):
    """Push full d/O cross covariance into O-kappa L_S d; no zero filling."""
    c = np.asarray(summary_covariance, float)
    if c.shape != (10, 10) or not np.isfinite(c).all():
        raise ValueError('full 10x10 joint covariance required')
    a = np.column_stack((-kappa * lift_matrix(s), np.eye(7)))
    return a @ c @ a.T


def boost_chart(z, d_l, gamma):
    """Maartens et al. (27), (62), (68) at a fixed ray; gamma is Doppler Γ>0."""
    z = np.asarray(z, float)
    d_l = np.asarray(d_l, float)
    if gamma <= 0 or not np.isfinite(gamma) or np.any(z <= -1) or np.any(d_l < 0):
        raise ValueError('invalid chart domain')
    z_tilde = (1 + z) / gamma - 1
    d_l_tilde = d_l / gamma
    return {'z_tilde': z_tilde, 'd_l_tilde': d_l_tilde,
            'd_l_star': d_l / (1 + z)**2,
            'd_l_star_tilde': d_l_tilde / (1 + z_tilde)**2,
            'vertex_z_tilde': 1 / gamma - 1}


def boost_dipole(s, beta):
    """First-order dust moving-observer coefficient, not a raw fit operator."""
    return -2 * (np.eye(3) + validate_s(s)) @ np.asarray(beta, float)


def invert_boost(s, d):
    a = np.eye(3) + validate_s(s)
    if np.min(np.abs(np.linalg.eigvalsh(a))) <= 1e-12 * max(np.linalg.norm(a, 2), np.finfo(float).tiny):
        raise ValueError('I+S singular/ill-conditioned')
    return -np.linalg.solve(a, d) / 2
