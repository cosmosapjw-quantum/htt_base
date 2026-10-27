"""Conditional optical response and shared seven-component compatibility.

All angular tensors use one orthonormal observer rest-frame basis and Frobenius
norms. This module does not assign physical meaning to catalogue harmonics.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import norm as robust_norm
from scipy.optimize import minimize, nnls

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


def _profile_d(o, k, d_obs, e_d, d_max, budget):
    """Normalized convex profile with independently checked primal and KKT conditions."""
    if d_max is not None and _safe_norm(d_obs) > e_d + d_max:
        return None, {'status': 'PHYSICAL_SET_EMPTY'}
    if e_d == 0:
        return d_obs.copy(), {'status': 'FIXED_DIRECT_DIPOLE', 'kkt_residual': 0.0}
    if d_max == 0:
        return np.zeros(3), {'status': 'SINGLETON_PHYSICAL_SET', 'kkt_residual': 0.0}

    # x=(d-d_obs)/e_d has a unit direct ball. Both objective and physical
    # constraint are scaled before SLSQP, so a small physical K cannot look flat.
    kd0 = _checked_matvec(k, d_obs)
    ke = k * e_d
    if np.any((np.asarray(k, np.longdouble)*np.longdouble(e_d) != 0) & (ke == 0)):
        raise NumericalProfileFailure('NUMERIC_RANGE', 'direct-ball response underflow')
    yscale = max(np.max(np.abs(o)), np.max(np.abs(kd0)),
                 np.max(np.abs(ke)), budget)
    if yscale == 0:
        yscale = 1.0  # all four inputs are exactly zero
    r0 = (o / yscale) - (kd0 / yscale)
    a = ke / yscale
    if not np.isfinite(r0).all() or not np.isfinite(a).all():
        raise NumericalProfileFailure('NUMERIC_RANGE', 'normalized objective outside finite range')
    dscale = max(np.max(np.abs(d_obs)), e_d, d_max or 0.0)
    center = d_obs / dscale
    width = e_d / dscale
    radius = d_max / dscale if d_max is not None else None

    def fun(x):
        r = r0 - a @ x
        return .5 * (r @ r)
    def jac(x):
        return -a.T @ (r0 - a @ x)
    constraints = [{'type':'ineq', 'fun':lambda x: 1.0-x@x,
                    'jac':lambda x: -2*x}]
    if radius is not None:
        constraints.append({'type':'ineq',
                            'fun':lambda x: radius**2 - (center+width*x)@(center+width*x),
                            'jac':lambda x: -2*width*(center+width*x)})
    x0 = np.zeros(3)
    if radius is not None and _safe_norm(center) > radius:
        x0 = ((radius/_safe_norm(center))-1)*center/width
        if _safe_norm(x0) > 1 + 1e-10:
            return None, {'status': 'PHYSICAL_SET_EMPTY'}
    sol = minimize(fun, x0, jac=jac, constraints=constraints, method='SLSQP',
                   options={'ftol':1e-13, 'maxiter':1000})
    x = np.asarray(sol.x, float)
    if not np.isfinite(x).all():
        raise NumericalProfileFailure('NUMERICAL_FAILURE', 'nonfinite optimizer iterate')
    slacks = np.array([c['fun'](x) for c in constraints], float)
    primal_error = max(0.0, -float(np.min(slacks)))
    gradient = jac(x)
    # At an active boundary, outward normals carry nonnegative multipliers.
    active = np.flatnonzero(slacks <= 1e-7)
    normals = np.column_stack([-constraints[i]['jac'](x) for i in active]) if len(active) else np.empty((3,0))
    if len(active):
        multipliers, _ = nnls(normals, -gradient)
        stationary = _safe_norm(gradient + normals @ multipliers)
        complementarity = float(np.max(np.abs(multipliers*slacks[active])))
    else:
        multipliers = np.empty(0)
        stationary = _safe_norm(gradient)
        complementarity = 0.0
    kkt_scale = max(1.0, _safe_norm(gradient), _safe_norm(a.T@a))
    kkt_error = max(primal_error, stationary/kkt_scale, complementarity)
    if kkt_error > 1e-8:
        raise NumericalProfileFailure('NUMERICAL_FAILURE',
             f'profile uncertified: solver={sol.message}; primal={primal_error:.3g}; '
             f'stationary={stationary:.3g}; complementary={complementarity:.3g}')
    d = d_obs + e_d*x
    if _safe_norm(d-d_obs) > e_d*(1+1e-8):
        raise NumericalProfileFailure('NUMERICAL_FAILURE', 'direct-ball feasibility lost on reconstruction')
    if d_max is not None and _safe_norm(d) > d_max*(1+1e-8):
        raise NumericalProfileFailure('NUMERICAL_FAILURE', 'physical-ball feasibility lost on reconstruction')
    return d, {'status':'KKT_CERTIFIED', 'solver_success':bool(sol.success),
               'primal_error':primal_error, 'stationarity_error':stationary,
               'complementarity_error':complementarity, 'kkt_residual':kkt_error,
               'active_constraints':active.tolist(), 'multipliers':multipliers.tolist()}


def joint_test(o, s, d_obs, budget, e_d=0.0, d_max=None, kappa=KAPPA):
    """Certified profiled membership in one seven-component residual ball."""
    o = np.asarray(o, float)
    d_obs = np.asarray(d_obs, float)
    s = validate_s(s)
    if o.shape != (7,) or d_obs.shape != (3,) or not np.isfinite(o).all() or not np.isfinite(d_obs).all():
        raise ValueError('finite seven-component O and three-component d required')
    if not np.isfinite([budget, e_d, kappa]).all() or budget < 0 or e_d < 0 or kappa == 0:
        raise ValueError('finite nonnegative radii and nonzero kappa required')
    if d_max is not None and (not np.isfinite(d_max) or d_max < 0):
        raise ValueError('invalid physical dipole radius')
    s_scale = np.max(np.abs(s))
    # Scale before forming L_S. A nonzero 1e-200 S must stay nonzero even
    # though M_S has no representable binary64 entries.
    l_unit = lift_matrix(s/s_scale) if s_scale else np.zeros((7,3))
    k = (kappa*s_scale)*l_unit
    profiled, certificate = _profile_d(o, k, d_obs, e_d, d_max, budget)
    if profiled is None:
        return {'compatible':False, 'physical_set_empty':True,
                'reason':'direct and physical dipole balls do not intersect',
                'profile_certificate':certificate}
    predicted = _checked_matvec(k, profiled)
    # Use scaled operands for the decision; squared magnitudes are display-only.
    yscale = max(np.max(np.abs(o)), np.max(np.abs(predicted)), budget)
    if yscale == 0:
        yscale = 1.0
    os = o/yscale
    ps = predicted/yscale
    rn = _safe_norm(os-ps)
    bn = budget/yscale
    if not np.isfinite([rn,bn]).all():
        raise NumericalProfileFailure('NUMERIC_RANGE','residual comparison outside finite range')
    residual = yscale*rn
    if rn and residual == 0:
        raise NumericalProfileFailure('NUMERIC_RANGE','nonzero residual below binary64 range')
    on, pn = _safe_norm(os), _safe_norm(ps)
    cancellation = (on > 0 and pn > 0 and rn <= .5*max(on,pn))
    allowance = 64*np.finfo(float).eps*max(on,pn) if cancellation else 0.0
    compatible = rn <= bn + allowance
    if s_scale == 0:
        perp_norm, parallel_norm = residual, 0.0
        inverse_d = None
        branch = 'S_ZERO_DIRECT_MEMBERSHIP'
    else:
        m_unit = l_unit.T @ l_unit
        o_unit = os
        coord = np.linalg.solve(m_unit, l_unit.T @ o_unit)
        perp_scaled = o_unit - l_unit @ coord
        parallel_scaled = l_unit @ coord - ps
        perp_norm = yscale*_safe_norm(perp_scaled)
        parallel_norm = yscale*_safe_norm(parallel_scaled)
        split_error = abs(np.hypot(_safe_norm(perp_scaled),_safe_norm(parallel_scaled))-rn)
        if split_error > 64*np.finfo(float).eps*max(on,pn):
            raise NumericalProfileFailure('NUMERICAL_FAILURE','seven-component split fails at signal scale')
        d_hat = (yscale/(kappa*s_scale))*coord
        if not np.isfinite(d_hat).all():
            raise NumericalProfileFailure('NUMERIC_RANGE','inverse dipole outside binary64 range')
        inverse_d = d_hat.tolist()
        branch = 'INVERTIBLE_S'
    score = None if budget == 0 else rn/bn
    if score is not None and not np.isfinite(score):
        score = None  # ratio exceeds representable range; verdict used scaled norms
    return {'branch':branch, 'perpendicular_norm':perp_norm,
            'parallel_norm':parallel_norm,
            'perpendicular_squared':perp_norm**2,
            'parallel_squared':parallel_norm**2,
            'inverse_d':inverse_d, 'profiled_d':profiled.tolist(),
            'residual_norm':residual, 'residual_squared':residual**2,
            'budget':float(budget), 'score':score,
            'compatible':bool(compatible), 'physical_set_empty':False,
            'profile_certificate':certificate,
            'roundoff_allowance_applied':bool(cancellation)}


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
