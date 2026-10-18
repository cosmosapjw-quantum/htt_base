"""Finite delivered-fit surrogate; never a physical Planck observer response.

The signed ell2..5 field is a *defined* perturbation of a blackbody temperature,
not an absolute temperature or an assertion that unobserved sectors vanish.
Directions are outward, beta=v/c, metric (-,+,+,+), Doppler weight one.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import qr, solve_triangular
from scipy.special import sph_harm_y


def design(directions, lmax):
    n = np.asarray(directions, dtype=float)
    if n.ndim != 2 or n.shape[1] != 3 or not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n, axis=1), 1., atol=5e-13, rtol=0):
        raise ValueError("FINITE_UNIT_DIRECTIONS")
    if type(lmax) is not int or not 0 <= lmax <= 32:
        raise ValueError("REGISTERED_LMAX")
    theta, phi = np.arccos(np.clip(n[:, 2], -1., 1.)), np.arctan2(n[:, 1], n[:, 0])
    columns = []
    for ell in range(lmax+1):
        columns.append(sph_harm_y(ell, 0, theta, phi).real)
        for m in range(1, ell+1):
            y = sph_harm_y(ell, m, theta, phi)
            columns.extend((np.sqrt(2.)*y.real, np.sqrt(2.)*y.imag))
    return np.column_stack(columns)


def sphere_rule(ntheta):
    x, w = np.polynomial.legendre.leggauss(ntheta)
    phi = np.arange(2*ntheta)*np.pi/ntheta
    xx, pp = np.meshgrid(x, phi, indexing="ij")
    n = np.column_stack((np.sqrt(1-xx.ravel()**2)*np.cos(pp.ravel()),
                         np.sqrt(1-xx.ravel()**2)*np.sin(pp.ravel()), xx.ravel()))
    return n, np.repeat(w, 2*ntheta)*np.pi/ntheta


def pullback_points(directions, beta):
    """Inverse aberration and exact Doppler factor in the boosted sky chart."""
    n = np.asarray(directions, dtype=float)
    b = np.asarray(beta, dtype=float)
    # Validate unit directions as well as the speed; do not normalize silently.
    if n.ndim != 2 or n.shape[1] != 3 or not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n, axis=1), 1., atol=5e-13, rtol=0):
        raise ValueError("FINITE_UNIT_DIRECTIONS")
    if b.shape != (3,) or not np.isfinite(b).all() or b@b >= 1:
        raise ValueError("FINITE_SUBLUMINAL_BETA")
    b2 = float(b@b)
    if b2 == 0:
        return n.copy(), np.ones(len(n))
    gamma = 1/np.sqrt(1-b2)
    dot = n@b
    # (gamma-1)/b² = gamma²/(gamma+1), avoiding cancellation near beta=0.
    coefficient = gamma*gamma/(gamma+1)*dot-gamma
    doppler = 1/(gamma*(1-dot))
    source = (n+coefficient[:, None]*b)*doppler[:, None]
    return source, doppler


def finite_modes(source, beta, directions, weights, output_design):
    """Quadrature coefficients of U_beta applied to a defined ell0..5 field."""
    a = np.asarray(source, dtype=float)
    if a.ndim != 2 or a.shape[0] != 36 or not np.isfinite(a).all():
        raise ValueError("FINITE_SOURCE36_COLUMNS")
    n, d = pullback_points(directions, beta)
    values = (design(n, 5)@a)*d[:, None]
    return output_design.T@(np.asarray(weights)[:, None]*values)


def beam_layout(beam, lmax):
    b = np.asarray(beam, dtype=float)
    if b.ndim != 1 or len(b) <= lmax or not np.isfinite(b[:lmax+1]).all():
        raise ValueError("FINITE_BEAM_REQUIRED")
    return np.repeat(b[:lmax+1], 2*np.arange(lmax+1)+1)


def defined_source(retained, beam):
    """Only the definition of a finite surrogate; no physical inverse map."""
    r = np.asarray(retained, dtype=float)
    if r.ndim != 2 or r.shape[0] != 32 or not np.isfinite(r).all():
        raise ValueError("RETAINED32_COLUMNS")
    layout = beam_layout(beam, 5)
    if np.any(layout[4:] <= 0):
        raise ValueError("SOURCE_SECTOR_BEAM_NOT_INVERTIBLE")
    source = np.zeros((36, r.shape[1]))
    source[4:] = r/layout[4:, None]
    return source


def fit_operator(low_design, selected):
    y = np.asarray(low_design, dtype=float)
    mask = np.asarray(selected)
    if y.ndim != 2 or y.shape[1] != 36 or mask.dtype != bool or mask.shape != (len(y),) or mask.sum() < 36 or not np.isfinite(y).all():
        raise ValueError("EXACT_FIT_SUPPORT")
    q, r = qr(y[mask], mode="economic")
    if np.linalg.cond(r) > 1e6:
        raise ValueError("UNSTABLE_FIT")
    return solve_triangular(r, q.T)


def nuisance_projected_response(low_design, selected, pixel_response):
    """FWL residualize actual pixel monopole/dipole, then fit ell2..5.

    This is an unweighted geometric quotient, not covariance whitening.
    """
    y = np.asarray(low_design)[selected]
    g = np.asarray(pixel_response)
    if g.ndim != 2 or g.shape[0] != len(y) or not np.isfinite(g).all():
        raise ValueError("MATCHED_PIXEL_RESPONSE")
    qn, _ = qr(y[:, :4], mode="economic")
    residual_y = y[:, 4:]-qn@(qn.T@y[:, 4:])
    residual_g = g-qn@(qn.T@g)
    q, r = qr(residual_y, mode="economic")
    return solve_triangular(r, q.T@residual_g), residual_g
