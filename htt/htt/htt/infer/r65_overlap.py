"""Same-source overlap covariance of retained count-fit influence vectors.

This is an empirical source-Poisson influence/sandwich law for two selections
of the SAME Gaussian-component provider catalogue. Disjoint bins have no
within-selection object overlap; shared_counts binds actual cross-selection
memberships. This does not calibrate cosmological LSS, component multiplicity,
uncertain calibration, or a joint law for independent surveys.
"""
from __future__ import annotations

import numpy as np


def _counts(value, name, shape):
    n = np.asarray(value, dtype=float)
    if (n.shape != shape or not np.isfinite(n).all() or np.any(n < 0)
            or np.any(n != np.floor(n))):
        raise ValueError(f'{name} must have shape{shape} and nonnegative finite integer counts')
    return n


def _influences(value, name):
    a = np.asarray(value, dtype=float)
    if a.ndim != 3 or min(a.shape) == 0 or not np.isfinite(a).all():
        raise ValueError(f'{name} must be finite nonempty (bins,pixels,coordinates)')
    return a


def _spectrum(cov):
    eigen = np.linalg.eigvalsh(cov)
    scale = float(np.max(np.abs(eigen)))
    tol = np.finfo(float).eps * len(eigen) * scale * 64
    return {'rank': int(np.count_nonzero(eigen > tol)),
            'min_eigenvalue': float(eigen[0]), 'max_eigenvalue': float(eigen[-1]),
            'rank_tolerance': float(tol), 'positive_semidefinite_within_roundoff': bool(eigen[0] >= -tol),
            'eigenvalues': eigen}


def source_overlap_sandwich(influence_left, counts_left, influence_right,
                            counts_right, shared_counts):
    """Return LL,RR,LR, joint and (same-dimension) left-minus-right covariance.

    A[b,p,:] is the influence on the final retained left coefficient vector of
    ONE object in bin b,pixel p; B[c,p,:] is its right counterpart. Counts must
    use one common pixel support and actual disjoint-bin memberships within
    each selection. Unmatched objects are admitted. shared[b,c,p] cannot sum
    above either marginal count. No artificial ridge, clipping, or independence
    assumption is added.

    The returned covariance is the observed event Gram sum, hence PSD in exact
    arithmetic. Tiny negative eigenvalues are reported with a roundoff scale;
    they are retained, never repaired silently. Contrast=L-R requires K=L and
    the caller's common coordinate convention.
    """
    a = _influences(influence_left, 'influence_left')
    b = _influences(influence_right, 'influence_right')
    nb, npix, k = a.shape
    nc, pp, l = b.shape
    if npix != pp:
        raise ValueError('left and right must share exactly the same pixel support/order')
    nl = _counts(counts_left, 'counts_left', (nb, npix))
    nr = _counts(counts_right, 'counts_right', (nc, npix))
    shared = _counts(shared_counts, 'shared_counts', (nb, nc, npix))
    if np.any(shared.sum(axis=1) > nl) or np.any(shared.sum(axis=0) > nr):
        raise ValueError('shared memberships exceed a left or right marginal pixel count')
    ll = np.einsum('bp,bpi,bpj->ij', nl, a, a, optimize=True)
    rr = np.einsum('cp,cpi,cpj->ij', nr, b, b, optimize=True)
    lr = np.einsum('bcp,bpi,cpj->ij', shared, a, b, optimize=True)
    ll, rr = (ll+ll.T)/2, (rr+rr.T)/2
    joint = np.block([[ll, lr], [lr.T, rr]])
    if not np.isfinite(joint).all():
        raise ValueError('covariance overflow; rescale influence coordinates')
    diag = _spectrum(joint)
    if not diag['positive_semidefinite_within_roundoff']:
        raise ArithmeticError('event covariance is materially non-PSD; inspect numerical scaling')
    contrast = None
    contrast_diag = None
    if k == l:
        contrast = ll + rr - lr - lr.T
        contrast = (contrast+contrast.T)/2
        contrast_diag = _spectrum(contrast)
        # Cancellation can make its roundoff scale much smaller than the
        # parent blocks. Report a physically appropriate parent-scale tolerance.
        parent_scale = max(float(np.linalg.norm(ll, 2)), float(np.linalg.norm(rr, 2)), float(np.linalg.norm(lr, 2)))
        contrast_tol = 64*np.finfo(float).eps*k*parent_scale
        contrast_diag['parent_scale_roundoff_tolerance'] = contrast_tol
        contrast_diag['rank_tolerance'] = contrast_tol
        contrast_diag['rank'] = int(np.count_nonzero(contrast_diag['eigenvalues'] > contrast_tol))
        contrast_diag['positive_semidefinite_within_roundoff'] = bool(contrast_diag['min_eigenvalue'] >= -contrast_tol)
        if not contrast_diag['positive_semidefinite_within_roundoff']:
            raise ArithmeticError('contrast covariance is materially non-PSD')
    return {'covariance_left': ll, 'covariance_right': rr, 'covariance_cross': lr,
            'covariance_joint': joint, 'covariance_contrast': contrast,
            'joint_diagnostics': diag, 'contrast_diagnostics': contrast_diag,
            'n_left': int(nl.sum()), 'n_right': int(nr.sum()), 'n_shared': int(shared.sum()),
            'n_unmatched_left': int((nl-shared.sum(axis=1)).sum()),
            'n_unmatched_right': int((nr-shared.sum(axis=0)).sum()),
            'law': 'empirical source-Poisson influence/sandwich; actual same-provider component memberships',
            'contrast_convention': 'left minus right in common coefficient coordinates' if k == l else None,
            'physical_LSS_calibrated': False, 'independent_surveys': False, 'ridge_added': 0.0}


def paired_common_covariance(influence_left, counts_left, influence_right,
                             counts_right, shared_counts):
    """Named entry point for paired peak-versus-integrated common coefficients."""
    return source_overlap_sandwich(influence_left, counts_left,
                                  influence_right, counts_right, shared_counts)


def common_influences(experiments, fit, maps, *, parameter_indices=(0, 1)):
    """Compute one-source influences after conditional ring/nuisance profiling.

    For each bin,pixel: A_bp=(f_bp-mean_q,ring) M_b C_theta[:,J].
    `fit` is the existing fit_joint result: its complete covariance and
    per_experiment_estimates are used, including fitted STF nuisance/offsets.
    All experiments must cover the SAME pixel order. This function evaluates
    probabilities only: it performs no fit. Returns shape(bins,pixels,len(J)).
    """
    experiments, maps = list(experiments), list(maps)
    if not experiments or len(experiments) != len(maps):
        raise ValueError('one map per nonempty experiment list is required')
    covariance = np.asarray(fit['covariance'], dtype=float)
    estimates = fit['per_experiment_estimates']
    if (covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1]
            or not np.isfinite(covariance).all()
            or not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0)):
        raise ValueError('fit requires finite symmetric complete parameter covariance')
    raw_indices = np.asarray(parameter_indices)
    if (raw_indices.ndim != 1 or raw_indices.size == 0 or not np.issubdtype(raw_indices.dtype, np.integer)
            or len(set(raw_indices.tolist())) != len(raw_indices)
            or np.any(raw_indices < 0) or np.any(raw_indices >= len(covariance))):
        raise ValueError('invalid retained parameter indices')
    if len(estimates) != len(experiments):
        raise ValueError('per-experiment fitted states are required')
    npix = len(experiments[0].counts)
    output = []
    for exp, matrix, theta in zip(experiments, maps, estimates):
        f = np.asarray(exp.features, float)
        matrix = np.asarray(matrix, float)
        if (f.ndim != 2 or f.shape[0] != npix
                or matrix.shape != (f.shape[1], len(covariance))
                or not np.isfinite(matrix).all() or not np.isfinite(f).all()):
            raise ValueError('inconsistent pixel support/features/parameter map')
        prob = np.asarray(exp.probabilities(theta), float)
        if prob.shape != (npix,) or not np.isfinite(prob).all() or np.any(prob < 0):
            raise ValueError('invalid conditional probabilities')
        sums = np.bincount(exp.groups, weights=prob, minlength=exp.n_groups)
        if not np.allclose(sums, 1., rtol=0, atol=2e-12):
            raise ValueError('probabilities must be normalized in every ring')
        means = np.column_stack([np.bincount(exp.groups, weights=prob*f[:,j], minlength=exp.n_groups)
                                 for j in range(f.shape[1])])
        influence = (f-means[exp.groups]) @ matrix @ covariance[:, raw_indices]
        if not np.isfinite(influence).all():
            raise ValueError('influence overflow')
        output.append(influence)
    return np.stack(output)
