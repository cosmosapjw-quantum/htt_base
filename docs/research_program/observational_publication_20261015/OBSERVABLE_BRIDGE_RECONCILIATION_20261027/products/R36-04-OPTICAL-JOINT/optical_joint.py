"""Conditional optical response and shared seven-component compatibility.

All angular tensors use one orthonormal observer rest-frame basis and Frobenius
norms. This module does not assign physical meaning to catalogue harmonics.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

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
    scale = max(np.linalg.norm(s), np.finfo(float).tiny)
    if np.linalg.norm(s - stf2(s)) > 1e-12 * scale:
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


def joint_test(o, s, d_obs, budget, e_d=0.0, d_max=None, kappa=KAPPA):
    """Profile a direct-dipole ball against one shared STF3 residual ball.

    A finite direct radius is a supplied uncertainty, never inferred here.
    With S=0 the test remains direct membership and no inverse is attempted.
    """
    o = np.asarray(o, float)
    d_obs = np.asarray(d_obs, float)
    s = validate_s(s)
    if o.shape != (7,) or d_obs.shape != (3,) or not np.isfinite(o).all() or not np.isfinite(d_obs).all():
        raise ValueError('finite seven-component O and three-component d required')
    if not np.isfinite([budget, e_d]).all() or budget < 0 or e_d < 0:
        raise ValueError('nonnegative finite radii required')
    if d_max is not None and (not np.isfinite(d_max) or d_max < 0):
        raise ValueError('invalid physical dipole radius')
    l = lift_matrix(s)
    k = kappa * l
    eps = np.finfo(float).eps
    if d_max is not None and np.linalg.norm(d_obs) > d_max + e_d + 32*eps*max(np.linalg.norm(d_obs), d_max, e_d):
        return {'compatible': False, 'physical_set_empty': True, 'reason': 'direct dipole ball misses physical radius'}
    def objective(d):
        r = o - k @ d
        return float(r @ r)
    if e_d == 0:
        profiled = d_obs.copy()
    elif d_max == 0:
        profiled = np.zeros(3)
    else:
        constraints = [{'type': 'ineq', 'fun': lambda d: e_d**2 - np.sum((d-d_obs)**2)}]
        if d_max is not None:
            constraints.append({'type': 'ineq', 'fun': lambda d: d_max**2 - np.sum(d**2)})
        start = d_obs.copy()
        if d_max is not None and np.linalg.norm(start) > d_max:
            start *= d_max / np.linalg.norm(start)
        solution = minimize(objective, start, method='SLSQP', constraints=constraints,
                            options={'ftol': 1e-15, 'maxiter': 2000})
        profiled = solution.x
        feasibility = np.linalg.norm(profiled-d_obs) <= e_d + 1e-9 * max(e_d, np.linalg.norm(d_obs), np.linalg.norm(profiled))
        if d_max is not None:
            feasibility &= np.linalg.norm(profiled) <= d_max + 1e-9 * max(d_max, np.linalg.norm(profiled))
        if not feasibility or (not solution.success and np.linalg.norm(solution.jac) > 1e-7):
            raise RuntimeError(f'dipole profile failed: {solution.message}')
    squared = objective(profiled)
    if np.linalg.norm(s) == 0:
        split = {'branch': 'S_ZERO_DIRECT_MEMBERSHIP', 'perpendicular_squared': squared,
                 'parallel_squared': 0.0, 'inverse_d': None}
    else:
        # Scale first: M_S may underflow for a valid but very small nonzero S.
        scale = np.max(np.abs(s))
        l_unit = lift_matrix(s / scale)
        m_unit = l_unit.T @ l_unit
        d_hat = np.linalg.solve(m_unit, l_unit.T @ (o / (kappa * scale)))
        perp = o - k @ d_hat
        parallel = float(np.linalg.norm(k @ (d_hat-profiled))**2)
        split = {'branch': 'INVERTIBLE_S', 'perpendicular_squared': float(perp @ perp),
                 'parallel_squared': float(parallel), 'inverse_d': d_hat.tolist()}
        split_norm = np.hypot(np.sqrt(split['perpendicular_squared']), np.sqrt(parallel))
        signal_scale = max(np.linalg.norm(o), np.linalg.norm(k @ profiled))
        if abs(np.sqrt(squared) - split_norm) > 64*eps*signal_scale:
            raise AssertionError('orthogonal decomposition failed')
    if d_max is not None and np.linalg.norm(profiled) > d_max + 1e-9 * max(d_max, np.linalg.norm(profiled)):
        raise ValueError('profiled physical domain violation')
    residual = np.sqrt(squared)
    if budget == 0:
        compatible = residual <= 64*eps*max(np.linalg.norm(o), np.linalg.norm(k@profiled))
    else:
        compatible = residual <= budget*(1+64*eps)
    return {**split, 'profiled_d': profiled.tolist(), 'residual_squared': squared,
            'budget': float(budget), 'score': float(np.sqrt(squared) / budget) if budget else (0.0 if squared == 0 else None),
            'compatible': bool(compatible),
            'physical_set_empty': False}


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
