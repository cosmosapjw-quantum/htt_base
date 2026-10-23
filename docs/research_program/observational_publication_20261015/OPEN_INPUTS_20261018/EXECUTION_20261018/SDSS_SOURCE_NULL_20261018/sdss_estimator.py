"""Finite source-diagnostic estimator; no archive parser or physical admission.

Released equatorial RA/Dec in degrees (epoch unestablished), z_obs as released.
The diagonal sigma_mu law below is a declared working law, not source covariance.
"""
from __future__ import annotations

import numpy as np

BASIS = ["nx", "ny", "nz", "nx2-nz2", "ny2-nz2", "2nxny", "2nxnz", "2nynz"]
WINDOWS = ["uniform", "gaussian_z006_sigma0012"]
ATOL_MAG = 1e-10
RTOL = 1e-8


def shape8(n):
    # Exact pure-kernel expression from D07; do not import its campaign module.
    x, y, z = np.asarray(n).T
    return np.column_stack([x, y, z, x*x-z*z, y*y-z*z, 2*x*y, 2*x*z, 2*y*z])


def directions(ra_deg, dec_deg):
    ra, dec = np.asarray(ra_deg, float), np.asarray(dec_deg, float)
    if ra.ndim != 1 or ra.shape != dec.shape or not np.isfinite([ra, dec]).all():
        raise ValueError("Finite equal-length RA/Dec vectors required")
    if np.any(np.abs(dec) > 90):
        raise ValueError("Declination outside physical angular range")
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)
    return np.column_stack((np.cos(dec)*np.cos(ra), np.cos(dec)*np.sin(ra), np.sin(dec)))


def _validate_vectors(X, errors, sigma, z_obs):
    X, errors, sigma, z_obs = (np.asarray(a, float) for a in (X, errors, sigma, z_obs))
    n = len(errors)
    if X.shape != (n, 8) or any(a.shape != (n,) for a in (errors, sigma, z_obs)):
        raise ValueError("Eight-column design and equal-length vectors required")
    if not all(np.isfinite(a).all() for a in (X, errors, sigma, z_obs)):
        raise ValueError("Invalid required value; no implicit deletion or zero fill")
    if np.any(sigma <= 0):
        raise ValueError("Nonpositive magnitude error")
    if np.any((z_obs < .01) | (z_obs > .1)):
        raise ValueError("Estimator accepts only already selected .01 <= z_obs <= .1")
    return X, errors, sigma, z_obs


def profiled_map(X, sigma, kernel):
    """Eight slope maps after profiling a free scalar intercept using w=k/sigma²."""
    weights = kernel / sigma**2
    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError("Invalid working weight")
    scalar_map = weights / weights.sum()
    center = scalar_map @ X
    centered = X - center
    root_w = np.sqrt(weights)
    whitened = centered * root_w[:, None]
    u, s, vt = np.linalg.svd(whitened, full_matrices=False)
    tolerance = max(whitened.shape) * np.finfo(float).eps * s[0] if len(s) else 0.
    rank = int(np.sum(s > tolerance))
    if rank != 8:
        raise ValueError(f"Rank-deficient angular design after intercept: rank={rank}; no ridge")
    # This is an SVD solution of the profiled eight-column least-squares problem.
    mapping = ((vt.T / s) @ u.T) * root_w
    return mapping, scalar_map, center, s


def fit_source_errors(ra_deg, dec_deg, z_obs, logdist_true, logdist, logdist_err):
    """Fit source-released mean-logdistance residuals, in magnitudes.

    No parser is provided until the actual source header has been qualified.
    logdist_err is the source distribution SD; never its location/scale parameter.
    """
    X = shape8(directions(ra_deg, dec_deg))
    true, measured, eta_sd = (np.asarray(a, float) for a in (logdist_true, logdist, logdist_err))
    if true.shape != measured.shape or true.shape != eta_sd.shape:
        raise ValueError("Logdistance arrays must have equal shape")
    error = -5. * (measured - true)
    sigma = 5. * eta_sd
    X, error, sigma, z_obs = _validate_vectors(X, error, sigma, z_obs)
    kernels = [np.ones(len(z_obs)), np.exp(-.5*((z_obs-.06)/.012)**2)]
    maps, means, intercepts, ranks = [], [], [], []
    for kernel in kernels:
        mapping, scalar_map, center, singular = profiled_map(X, sigma, kernel)
        slopes = mapping @ error
        mean = scalar_map @ error
        maps.append(mapping)
        means.append(mean)
        intercepts.append(mean-center@slopes)
        ranks.append(singular)
    mapping = np.vstack(maps)
    coefficients = mapping @ error
    # Both windows act on the same rows. The Gaussian kernel is not a precision
    # law, so neither inverse Gram nor zero cross-window covariance is used.
    covariance = (mapping * sigma**2) @ mapping.T
    if not np.isfinite(covariance).all() or np.any(np.diag(covariance) <= 0):
        raise ValueError("Invalid computed diagonal working covariance")
    return {"coefficients_mag": coefficients, "working_covariance_mag2": covariance,
            "weighted_scalar_mean_errors_mag": np.asarray(means),
            "profiled_intercepts_mag": np.asarray(intercepts), "slope_maps": mapping,
            "design": X, "error_mag": error, "sigma_mag": sigma,
            "window_kernels": np.asarray(kernels), "singular_values": np.asarray(ranks)}


def independent_full_intercept_lstsq(X, error, sigma, kernel):
    """Independent full nine-column weighted SVD/lstsq validation route."""
    full = np.column_stack((np.ones(len(error)), X))
    root_w = np.sqrt(kernel) / sigma
    coefficients, _, rank, _ = np.linalg.lstsq(full*root_w[:, None], error*root_w, rcond=None)
    if rank != 9:
        raise ValueError("Rank-deficient full-intercept validation design")
    return coefficients


def summarize(coefficients, working_covariances):
    """Descriptive finite-box summaries; no bias recentering or calibrated coverage."""
    from scipy.stats import norm
    values, cov = np.asarray(coefficients), np.asarray(working_covariances)
    if values.shape != (64, 16) or cov.shape != (64, 16, 16):
        raise ValueError("Frozen summary requires exactly 64 distinct-box Y0 vectors")
    if not np.isfinite(values).all() or not np.isfinite(cov).all():
        raise ValueError("Invalid finite-box result")
    diagonal = np.diagonal(cov, axis1=1, axis2=2)
    if np.any(diagonal <= 0):
        raise ValueError("Nonpositive working marginal variance")
    empirical = np.cov(values, rowvar=False, ddof=1)
    scatter = np.sqrt(np.diag(empirical))
    correlation = np.divide(empirical, scatter[:, None]*scatter[None, :],
                            out=np.full_like(empirical, np.nan),
                            where=(scatter[:, None]*scatter[None, :]) > 0)
    threshold = float(norm.ppf(1.-.05/32.))
    t = np.max(np.abs(values) / np.sqrt(diagonal), axis=1)
    return {"coefficient_means_mag": values.mean(axis=0),
            "coefficient_scatter_mag": scatter, "empirical_covariance_mag2": empirical,
            "empirical_crosswindow_correlation": correlation[:8, 8:],
            "mean_working_covariance_mag2": cov.mean(axis=0),
            "empirical_to_mean_working_variance_ratio": np.diag(empirical)/diagonal.mean(axis=0),
            "T_descriptive": t, "descriptive_threshold": threshold,
            "K_exceeding_descriptive_threshold": int(np.sum(t > threshold)), "N_boxes": 64,
            "bias_centering": "NONE", "coverage_claim": "NOT_CALIBRATED_PHYSICAL_OR_H02"}
