"""Finite-face extrema for a quadratic on a coordinate box and the R61 phi box.

In exact arithmetic, every box extremum is stationary on the relative interior
of its smallest face. Enumerating 3**n faces therefore gives the exact range.
This implementation uses SVD/linear solves/LP in float64 and explicitly reports
its diagnostics and guard; it is NOT a formal interval-arithmetic proof.
"""
from __future__ import annotations

import itertools
import numpy as np
from scipy.optimize import linprog


class BoxExtremaNumericalError(RuntimeError):
    """Numerically ambiguous face rank, stationarity, or LP failure."""


def _valid_box(lower, upper):
    lo, hi = np.asarray(lower, float), np.asarray(upper, float)
    if lo.ndim != 1 or hi.shape != lo.shape or not 1 <= len(lo) <= 3:
        raise ValueError('A box must have between one and three coordinates.')
    if not np.isfinite(lo).all() or not np.isfinite(hi).all() or np.any(lo > hi):
        raise ValueError('Box bounds must be finite and lower <= upper.')
    return lo, hi


def quadratic_box_range(matrix, lower, upper, *, rank_rtol=1e-12):
    """Range of x.T matrix x on a closed n<=3 box by all-face enumeration.

    Nonzero box centers, indefinite matrices, singular/flat faces, and collapsed
    coordinate intervals are supported. Singular consistent faces use an LP to
    find a stationary point within that face. An unresolved numerical ambiguity
    raises BoxExtremaNumericalError instead of silently omitting the face.
    """
    lo, hi = _valid_box(lower, upper)
    Q = np.asarray(matrix, float)
    n = len(lo)
    if Q.shape != (n, n) or not np.isfinite(Q).all():
        raise ValueError('matrix must be a finite square matrix matching the box.')
    eps = np.finfo(float).eps
    scaleQ = max(float(np.linalg.norm(Q, 2)), np.finfo(float).tiny)
    if np.max(np.abs(Q-Q.T)) > 64*eps*scaleQ:
        raise ValueError('matrix must be symmetric.')
    if not np.isfinite(rank_rtol) or rank_rtol < 256*eps or rank_rtol >= 1:
        raise ValueError('rank_rtol must be finite, >=256*eps and <1.')
    Q = (Q+Q.T)/2
    maxx = np.maximum(np.abs(lo), np.abs(hi))
    xscale = max(float(np.max(maxx)), np.finfo(float).tiny)
    feasibility_tol = 128*eps*xscale
    stats = {
        'faces_enumerated': 0, 'vertices': 0, 'full_rank_stationary_faces': 0,
        'singular_faces': 0, 'singular_inconsistent_faces': 0,
        'singular_consistent_lp_feasible': 0, 'singular_consistent_lp_infeasible': 0,
        'stationary_points_outside_face': 0, 'candidate_count': 0,
        'max_retained_condition_number': 1., 'max_stationarity_residual_abs': 0.,
        'max_discarded_singular_value': 0., 'max_feasibility_clipping_distance': 0.,
    }
    candidates = []
    for face in itertools.product((-1, 0, 1), repeat=n):
        stats['faces_enumerated'] += 1
        free = np.flatnonzero(np.array(face) == 0)
        fixed = np.flatnonzero(np.array(face) != 0)
        x = np.zeros(n)
        for j in fixed:
            x[j] = lo[j] if face[j] == -1 else hi[j]
        condition, rank, residual, method = 1., 0, 0., 'VERTEX'
        if len(free):
            A = Q[np.ix_(free, free)]
            rhs = -Q[np.ix_(free, fixed)]@x[fixed]
            U, singular, Vh = np.linalg.svd(A)
            a_scale = float(singular[0]) if len(singular) else 0.
            threshold = rank_rtol*a_scale
            rank = int(np.sum(singular > threshold)) if a_scale else 0
            if rank:
                condition = float(singular[0]/singular[rank-1])
                stats['max_retained_condition_number'] = max(stats['max_retained_condition_number'], condition)
            if rank == len(free):
                xf = np.linalg.solve(A, rhs)
                stats['full_rank_stationary_faces'] += 1
                method = 'FULL_RANK_SOLVE'
            else:
                stats['singular_faces'] += 1
                discarded = float(np.max(singular[rank:])) if len(singular[rank:]) else 0.
                stats['max_discarded_singular_value'] = max(stats['max_discarded_singular_value'], discarded)
                # A small genuinely nonzero mode can make a near-singular face
                # numerically ambiguous. Do not silently call it exactly flat.
                if discarded > 256*eps*a_scale:
                    raise BoxExtremaNumericalError(
                        f'Ambiguous numerical rank on face {face}: discarded={discarded:g}, scale={a_scale:g}')
                xp = Vh[:rank].T@((U[:, :rank].T@rhs)/singular[:rank]) if rank else np.zeros(len(free))
                consistency = float(np.linalg.norm(A@xp-rhs, np.inf))
                consistency_tol = 512*eps*max(scaleQ*xscale, float(np.linalg.norm(rhs, np.inf)),
                                              a_scale*float(np.linalg.norm(xp)), np.finfo(float).tiny)
                if consistency > consistency_tol:
                    stats['singular_inconsistent_faces'] += 1
                    continue
                # Solve for a point in the affine stationary set, normalized
                # to a unit box so small physical beta coordinates remain safe.
                mid = (lo[free]+hi[free])/2
                half = (hi[free]-lo[free])/2
                Aeq = Vh[:rank]*half[None, :]
                beq = (U[:, :rank].T@rhs)/singular[:rank] - Vh[:rank]@mid if rank else np.empty(0)
                rowscale = np.linalg.norm(Aeq, axis=1) if rank else np.empty(0)
                usable = rowscale > 0
                if np.any(np.abs(beq[~usable]) > 512*eps*xscale):
                    stats['singular_consistent_lp_infeasible'] += 1
                    continue
                An = Aeq[usable]/rowscale[usable, None]
                bn = beq[usable]/rowscale[usable]
                lp = linprog(np.zeros(len(free)), A_eq=An if len(An) else None,
                             b_eq=bn if len(An) else None, bounds=[(-1., 1.)]*len(free),
                             method='highs', options={'primal_feasibility_tolerance': 1e-10,
                                                       'dual_feasibility_tolerance': 1e-10})
                if lp.status == 2:
                    stats['singular_consistent_lp_infeasible'] += 1
                    continue
                if not lp.success:
                    raise BoxExtremaNumericalError(f'Stationary-set LP failed on face {face}: {lp.message}')
                xf = mid+half*lp.x
                stats['singular_consistent_lp_feasible'] += 1
                method = 'SINGULAR_CONSISTENT_LP'
            if not np.isfinite(xf).all():
                raise BoxExtremaNumericalError(f'Nonfinite stationary point on face {face}.')
            if np.any(xf < lo[free]-feasibility_tol) or np.any(xf > hi[free]+feasibility_tol):
                stats['stationary_points_outside_face'] += 1
                continue
            clipped = np.clip(xf, lo[free], hi[free])
            stats['max_feasibility_clipping_distance'] = max(
                stats['max_feasibility_clipping_distance'], float(np.linalg.norm(clipped-xf)))
            x[free] = clipped
            residual = float(np.linalg.norm(A@clipped-rhs, np.inf))
            allowed_residual = 1e-9*max(scaleQ*xscale, float(np.linalg.norm(rhs, np.inf)), np.finfo(float).tiny)
            if residual > allowed_residual:
                raise BoxExtremaNumericalError(f'Stationarity residual too large on face {face}: {residual:g}')
            stats['max_stationarity_residual_abs'] = max(stats['max_stationarity_residual_abs'], residual)
        else:
            stats['vertices'] += 1
        value = float(x@Q@x)
        candidates.append({'value': value, 'x': x.tolist(), 'face': list(face),
                           'method': method, 'free_rank': rank,
                           'retained_condition_number': condition,
                           'stationarity_residual_abs': residual})
    stats['candidate_count'] = len(candidates)
    if not candidates:
        raise BoxExtremaNumericalError('No feasible candidates; vertices should always be present.')
    minimum = min(candidates, key=lambda v: v['value'])
    maximum = max(candidates, key=lambda v: v['value'])
    value_scale = max(float(maxx@np.abs(Q)@maxx), np.finfo(float).tiny)
    guard = float(2048*eps*value_scale
                  + 2*stats['max_stationarity_residual_abs']*float(np.sum(hi-lo))
                  + 2*stats['max_discarded_singular_value']*float(maxx@maxx))
    return {'minimum': minimum['value'], 'maximum': maximum['value'],
            'minimum_witness': minimum, 'maximum_witness': maximum,
            'guard': guard, 'guarded_range': [minimum['value']-guard, maximum['value']+guard],
            'diagnostics': stats, 'rank_rtol': rank_rtol,
            'method': 'ALL_FACE_STATIONARY_ENUMERATION',
            'arithmetic': 'FLOAT64_FINITE_FACE_ENUMERATION_NOT_FORMAL_INTERVAL_PROOF',
            'guard_interpretation': 'roundoff/rank/residual scale allowance; not a directed-rounding certificate'}


def mixed_invariant_box_range(beta_lower, beta_upper, kappa_lower, kappa_upper,
                              stf_basis, rho=0., *, rank_rtol=1e-12):
    """Actual coordinate-box range of beta.T(K-Qcal)beta, with STF RMS cap rho."""
    blo, bhi = _valid_box(beta_lower, beta_upper)
    klo, khi = np.asarray(kappa_lower, float), np.asarray(kappa_upper, float)
    E = np.asarray(stf_basis, float)
    if len(blo) != 3 or klo.shape != (5,) or khi.shape != (5,) or E.shape != (5, 3, 3):
        raise ValueError('Expected beta3, kappa5 and basis (5,3,3).')
    if not np.isfinite(klo).all() or not np.isfinite(khi).all() or np.any(klo > khi):
        raise ValueError('kappa bounds must be finite and ordered.')
    if not np.isfinite(rho) or rho < 0:
        raise ValueError('rho must be finite and nonnegative.')
    if (not np.isfinite(E).all()
            or not np.allclose(E, E.transpose(0, 2, 1), atol=1e-12, rtol=0)
            or not np.allclose(np.trace(E, axis1=1, axis2=2), 0, atol=1e-12, rtol=0)
            or not np.allclose(np.einsum('aij,bij->ab', E, E), np.eye(5), atol=1e-12, rtol=0)):
        raise ValueError('basis must be Frobenius-orthonormal STF5.')
    a = np.sqrt(5)*rho
    endpoints = {'minimum': None, 'maximum': None}
    diagnostics = {'kappa_corners': 32, 'quadratic_box_calls': 0, 'faces_enumerated': 0,
                   'singular_faces': 0, 'singular_consistent_lp_feasible': 0,
                   'singular_inconsistent_faces': 0, 'max_retained_condition_number': 1.,
                   'max_stationarity_residual_abs': 0., 'max_guard': 0.}
    for bits in itertools.product((0, 1), repeat=5):
        kappa = np.where(bits, khi, klo)
        K = np.einsum('a,aij->ij', kappa, E)
        for key, sign in (('minimum', -1), ('maximum', 1)):
            q = quadratic_box_range(K+sign*a*np.eye(3), blo, bhi, rank_rtol=rank_rtol)
            diagnostics['quadratic_box_calls'] += 1
            d = q['diagnostics']
            for stat in ('faces_enumerated', 'singular_faces', 'singular_consistent_lp_feasible',
                         'singular_inconsistent_faces'):
                diagnostics[stat] += d[stat]
            for stat in ('max_retained_condition_number', 'max_stationarity_residual_abs'):
                diagnostics[stat] = max(diagnostics[stat], d[stat])
            diagnostics['max_guard'] = max(diagnostics['max_guard'], q['guard'])
            value = q[key]
            old = endpoints[key]
            if old is None or (value < old['phi'] if sign < 0 else value > old['phi']):
                b = np.array(q[key+'_witness']['x'])
                b2 = float(b@b)
                Qcal = np.zeros((3, 3))
                if b2 and rho:
                    T = np.outer(b, b)-b2*np.eye(3)/3
                    Qcal = -sign*np.sqrt(15/2)*rho*T/np.linalg.norm(T, 'fro')
                reconstructed = float(b@(K-Qcal)@b)
                endpoints[key] = {'phi': value, 'beta': b.tolist(), 'kappa': kappa.tolist(),
                                  'kappa_corner': list(bits), 'Qcal': Qcal.tolist(),
                                  'reconstructed_phi': reconstructed,
                                  'reconstruction_abs_error': abs(reconstructed-value),
                                  'calibration_fullsky_rms': float(np.sqrt(2/15)*np.linalg.norm(Qcal, 'fro')),
                                  'quadratic_witness': q[key+'_witness'], 'corner_guard': q['guard']}
    low, high = endpoints['minimum']['phi'], endpoints['maximum']['phi']
    guard = diagnostics['max_guard']
    return {'range': [low, high], 'width': high-low,
            'guarded_range': [low-guard, high+guard], 'guarded_width': high-low+2*guard,
            'guard': guard, 'minimum_witness': endpoints['minimum'],
            'maximum_witness': endpoints['maximum'], 'rho': float(rho),
            'diagnostics': diagnostics,
            'beta_lower': blo.tolist(), 'beta_upper': bhi.tolist(),
            'kappa_lower': klo.tolist(), 'kappa_upper': khi.tolist(),
            'method': '32_KAPPA_CORNERS_TIMES_27_BETA_FACES_PER_ENDPOINT',
            'arithmetic': 'FLOAT64_FINITE_FACE_ENUMERATION_NOT_FORMAL_INTERVAL_PROOF',
            'interpretation': 'actual coordinate-box extrema by a complete finite exact-arithmetic characterization; numerical guards are not formal certification'}
