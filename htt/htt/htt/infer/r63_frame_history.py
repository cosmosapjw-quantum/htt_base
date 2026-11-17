"""Conditional first-order frame/history responses for the fixed R63 experiment.

Sourceward unit directions; physical velocities in km/s; eta is a natural-log
distance residual. This module supplies source kernels and noise-metric response
diagnostics, not a new fit or a Boltzmann/Einstein evolution solver. Existing
R58 fit_linear owns likelihood fitting. Fixed-covariance Gaussian claims and the
compensated dust/radiation material/reference contract remain explicit premises.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import linalg, special

C_KM_S = 299792.458


def _finite(value, name, *, ndim=None):
    out = np.asarray(value, dtype=float)
    if (ndim is not None and out.ndim != ndim) or not np.isfinite(out).all():
        raise ValueError(f"{name} must be finite with ndim={ndim}")
    return out


def _densities(omega_m, omega_r):
    m, r = float(omega_m), float(omega_r)
    if not np.isfinite([m, r]).all() or min(m, r) < 0 or m+r > 1:
        raise ValueError("need Omega_m,Omega_r >= 0 and Omega_m+Omega_r <= 1")
    return m, r


@lru_cache(maxsize=8)
def _quadrature(order):
    if isinstance(order, (bool, np.bool_)) or not isinstance(order, (int, np.integer)) or order < 8:
        raise ValueError("quadrature_order must be an integer >= 8")
    x, w = leggauss(int(order))
    u, w = (x+1)/2, w/2
    u.setflags(write=False)
    w.setflags(write=False)
    return u, w


def background_factors(z, omega_m, omega_r, *, quadrature_order=64):
    """Flat dust+radiation+Lambda distance factors, at positive quoted z.

    Returns dimensionless chi_hat=H0*chi/c, E=H/H0, A and h, and g_per_km_s
    in (km/s)^-1. Omega_Lambda=1-Omega_m-Omega_r. Gauss-Legendre quadrature
    integrates the exact fixed background, without a low-z distance series.
    The h calculation avoids subtracting two numbers near one at small z.
    Check order refinement over the actual redshift range before claiming an
    accuracy; the returned order itself is not an error certificate.
    """
    z = _finite(z, "z")
    if z.size == 0 or np.any(z <= 0):
        raise ValueError("z must be nonempty and strictly positive")
    m, r = _densities(omega_m, omega_r)
    u, weights = _quadrature(quadrature_order)
    flat = z.ravel()
    chi, ee, aa, gg, hh = [np.empty_like(flat) for _ in range(5)]
    # A fixed-size chunk bounds memory for the real ~36k-source catalogue.
    for begin in range(0, flat.size, 4096):
        end = min(begin+4096, flat.size)
        zz = flat[begin:end, None]
        a, b = 1+zz, 1+zz*u[None, :]
        ea2 = m*a**3+r*a**4+1-m-r
        eb2 = m*b**3+r*b**4+1-m-r
        ea, eb = np.sqrt(ea2), np.sqrt(eb2)
        # d = int_0^1 [E(z)/E(zu)-1] du, factored before subtraction.
        difference = zz*(1-u[None, :])*(
            m*(a*a+a*b+b*b)+r*(a**3+a*a*b+a*b*b+b**3))
        d = (difference/(eb*(ea+eb))) @ weights
        e = ea[:, 0]
        z1 = zz[:, 0]
        chi_chunk = z1*(1+d)/e
        a_chunk = (1+z1)/(z1*(1+d))
        h_chunk = (1+z1)*d/(1+d)
        chi[begin:end], ee[begin:end] = chi_chunk, e
        aa[begin:end], gg[begin:end], hh[begin:end] = a_chunk, (a_chunk-1)/C_KM_S, h_chunk
    if not all(np.isfinite(v).all() for v in (chi, ee, aa, gg, hh)):
        raise ValueError("background factors overflowed; restrict the numerical redshift domain")
    return dict(chi_hat=chi.reshape(z.shape), E=ee.reshape(z.shape),
                A=aa.reshape(z.shape), g_per_km_s=gg.reshape(z.shape),
                h=hh.reshape(z.shape), omega_lambda=1-m-r,
                quadrature_order=int(quadrature_order))


def processed_eta(g, n, source_velocity, observer_velocity, redshift_correction,
                  distance_correction, calibration):
    """First-order source eta for fixed published redshift/distance corrections.

    Velocities/corrections are in km/s; calibration is a dimensionless dipole.
    source_velocity is (3,) or (N,3); all other vector arguments are (3,).
    g is (N,) in (km/s)^-1. This is a linear response, not a remainder bound;
    small velocities AND small Doppler displacement relative to z are required.
    Fixed corrections are not treated as independent measured velocities.
    """
    directions = _finite(n, "n", ndim=2)
    factors = _finite(g, "g", ndim=1)
    if directions.shape != (factors.size, 3) or factors.size == 0:
        raise ValueError("need g(N) and n(N,3), with N>0")
    if np.any(np.abs(np.linalg.norm(directions, axis=1)-1) > 1e-10):
        raise ValueError("n must contain unit sourceward directions")
    source = _finite(source_velocity, "source_velocity")
    if source.shape not in ((3,), directions.shape):
        raise ValueError("source_velocity must have shape (3,) or (N,3)")
    vectors = [_finite(v, label, ndim=1) for v, label in (
        (observer_velocity, "observer_velocity"), (redshift_correction, "redshift_correction"),
        (distance_correction, "distance_correction"), (calibration, "calibration"))]
    if any(v.shape != (3,) for v in vectors):
        raise ValueError("observer, correction and calibration vectors must have shape (3,)")
    observer, vr, vd, cal = vectors
    if np.any(np.linalg.norm(source, axis=-1) >= C_KM_S) or np.linalg.norm(observer) >= C_KM_S:
        raise ValueError("source and observer physical velocities must be subluminal")
    effective = source-observer+vr
    angular = cal+(2*vr-observer-vd)/C_KM_S
    return factors*np.sum(directions*effective, axis=1)+directions@angular


def residualized_response(cov, nuisance, target, *, rank_rtol=1e-12):
    """Whiten and profile a linear target against declared nuisance columns.

    residual is in whitened data units per target-parameter unit; information
    is residual.T@residual. Nuisance columns are equilibrated before the SVD,
    preserving units under nonsingular column rescaling. Target singular values
    retain caller units. Their rank threshold is relative to the ORIGINAL
    whitened target, never to roundoff left after a saturated projection.
    A full-row-rank nuisance design returns certified algebraic zero residual.
    Numerical rank remains conditional on the stated tolerance and source model.
    """
    c = _finite(cov, "covariance", ndim=2)
    n = _finite(nuisance, "nuisance", ndim=2)
    t = _finite(target, "target", ndim=2)
    rows = c.shape[0]
    if c.shape != (rows, rows) or rows == 0 or n.shape[0] != rows or t.shape[0] != rows or t.shape[1] == 0:
        raise ValueError("need covariance(N,N), nuisance(N,K), target(N,P), N,P>0")
    if not np.isfinite(rank_rtol) or not 0 < rank_rtol < 1:
        raise ValueError("rank_rtol must lie strictly between zero and one")
    cscale = np.max(np.abs(c))
    if cscale == 0 or np.max(np.abs(c-c.T)) > 1e-10*cscale:
        raise ValueError("covariance must be symmetric positive definite")
    try:
        chol = linalg.cholesky((c+c.T)/2, lower=True, check_finite=False)
    except linalg.LinAlgError as exc:
        raise ValueError("covariance must be symmetric positive definite") from exc
    nw = linalg.solve_triangular(chol, n, lower=True, check_finite=False)
    tw = linalg.solve_triangular(chol, t, lower=True, check_finite=False)
    if not np.isfinite(nw).all() or not np.isfinite(tw).all():
        raise ValueError("whitened response overflowed")
    # scipy's vector norm uses the scaled BLAS norm, avoiding squared underflow.
    norms = np.array([linalg.norm(nw[:, j]) for j in range(nw.shape[1])])
    nonzero = norms > 0
    if np.any(nonzero):
        u, ns, _ = linalg.svd(nw[:, nonzero]/norms[nonzero], full_matrices=False)
        nuisance_rank = int(np.count_nonzero(ns > rank_rtol*ns[0]))
        q = u[:, :nuisance_rank]
    else:
        ns, nuisance_rank, q = np.empty(0), 0, np.empty((rows, 0))
    original_singular = linalg.svdvals(tw)
    target_scale = float(original_singular[0])
    full_span = nuisance_rank == rows
    residual = np.zeros_like(tw) if full_span else tw-q@(q.T@tw)
    singular = linalg.svdvals(residual)
    target_threshold = rank_rtol*target_scale
    target_rank = 0 if target_scale == 0 else int(np.count_nonzero(singular > target_threshold))
    info = residual.T@residual
    return dict(residual=residual, information=(info+info.T)/2,
                singular_values=singular, nuisance_rank=nuisance_rank,
                nuisance_singular_values_equilibrated=ns,
                nuisance_column_norms=norms, target_rank=target_rank,
                target_rank_threshold=target_threshold,
                original_target_singular_values=original_singular,
                full_nuisance_span=full_span, rank_rtol=float(rank_rtol),
                rank_status="FULL_NUISANCE_SPAN_ZERO" if full_span else "NUMERICAL_RANK_AT_DECLARED_TOLERANCE")


def oracle_power(distance, alpha=0.1):
    """Neyman-Pearson upper bound Phi(Phi^-1(alpha)+distance).

    distance is a nonnegative Mahalanobis mean separation, dimensionless.
    For a common known Gaussian C, the nearest simple null gives an upper bound
    for every test with uniform size <=alpha over the declared composite null.
    It is not achieved-power calibration of a selected composite test, and a
    distance based on data-estimated amplitude is a descriptive plug-in value.
    """
    a = float(alpha)
    d = _finite(distance, "distance")
    if not np.isfinite(a) or not 0 < a < 1 or np.any(d < 0):
        raise ValueError("need distance>=0 and 0<alpha<1")
    value = special.ndtr(special.ndtri(a)+d)
    return float(value) if value.ndim == 0 else value


def compensated_velocity_bound(omega_m, omega_r, z_max, beta_star):
    """Matter/radiation-only bound on |U| in km/s, U=(1+R)c b.

    z_max is the earliest redshift of the DECLARED physical interval, not
    automatically the largest catalogue redshift. R=3Omega_m/(4Omega_r).
    Observer speed and Doppler/Taylor displacement must be checked separately.
    beta_star is a declared perturbative speed ceiling, not an optical error.
    """
    m, r = _densities(omega_m, omega_r)
    z, bound = float(z_max), float(beta_star)
    if m <= 0 or r <= 0 or not np.isfinite([z, bound]).all() or z < 0 or not 0 < bound < 1:
        raise ValueError("need positive matter/radiation, z_max>=0 and 0<beta_star<1")
    ratio = 3*m/(4*r)
    return C_KM_S*bound*(1+ratio)/max(1+z, ratio)


def compensated_body(U, redshift_correction, omega_m, omega_r, z_max, beta_star):
    """Evaluate the complete instantaneous speed body in the tied-reference model.

    U and fixed redshift_correction have km/s units. The observer equation uses
    the additional photon-energy-rest/CMB-reference contract. This does not test
    accumulated metric errors or the direction-dependent optical displacement.
    """
    u, vr = _finite(U, "U", ndim=1), _finite(redshift_correction, "redshift_correction", ndim=1)
    if u.shape != (3,) or vr.shape != (3,):
        raise ValueError("U and redshift_correction must be 3-vectors")
    u_bound = compensated_velocity_bound(omega_m, omega_r, z_max, beta_star)
    ratio = 3*float(omega_m)/(4*float(omega_r))
    w = u/(1+ratio)
    radiation = -ratio*w
    observer = vr+radiation
    beta_m_max = (1+float(z_max))*linalg.norm(w)/C_KM_S
    beta_r = linalg.norm(radiation)/C_KM_S
    beta_o = linalg.norm(observer)/C_KM_S
    return dict(R=ratio, W_km_s=w, radiation_velocity_km_s=radiation,
                observer_velocity_km_s=observer, matter_beta_max=beta_m_max,
                radiation_beta=beta_r, observer_beta=beta_o,
                max_beta=max(beta_m_max, beta_r, beta_o),
                admissible_speed_body=max(beta_m_max, beta_r, beta_o) <= float(beta_star),
                U_matter_radiation_bound_km_s=u_bound,
                optical_remainder_status="NOT_EVALUATED")
