"""PR-145: CF4 radial-monopole and velocity-shape estimator mechanics.

From the authenticated CF4 raw distance observable (PR-144) a single
estimand registry computes the bulk-flow 3-vector with its FULL covariance
— the measurement-noise covariance PLUS the linear-theory cosmic-variance
covariance from the fiducial peculiar-velocity power spectrum (Gorski
radial/transverse correlation) — and a flow-plus-radial-monopole
constrained estimator.

Estimators are compared as VECTORS under the full covariance (a Mahalanobis
distance), never a scalar amplitude overlap. The bulk-flow significance is
reported under the FULL covariance: the cosmic-variance term dominates the
tiny measurement-noise term, so the honest significance is far below the
noise-only (formal) figure, and — because the linear cosmic-variance
covariance is a conservative lower bound on the total variance — the
reported significance is an UPPER bound.

Observable-estimator mechanics at ``roadmap_rescue_v1:C2`` only. The two
CF4 P0s (C1-K5-MV-F1, C3-K5-VCORR-ML-F1) stay OPEN with remediation-
CANDIDATE receipts; their closure is impossible before the PR-157
adjudication. The constrained median is never the truth, and no
nuisance/model is chosen to match a prior headline.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .velocity_power import (
    fiducial,
    velocity_correlation_functions,
)

SCHEMA_VERSION = "pr145.cf4_velocity_estimators.v1"

H0_CF4 = 74.6                 # km/s/Mpc, the CF4 value
SIGMA_NL = 250.0             # km/s, nonlinear velocity dispersion


class VelocityEstimatorError(ValueError):
    """Raised when the estimator discipline is violated."""


# --------------------------------------------------------------------------
# data + observable
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Cf4Sample:
    n: np.ndarray            # (N,3) radial unit vectors (equatorial)
    v: np.ndarray            # (N,) radial peculiar velocity (km/s, CMB frame)
    w: np.ndarray            # (N,) inverse-variance weights
    sig_v: np.ndarray        # (N,) per-group velocity uncertainty (km/s)
    pos_hmpc: np.ndarray     # (N,3) comoving position (Mpc/h, equatorial)
    sg: np.ndarray = None    # (N,3) supergalactic Cartesian (SGX,SGY,SGZ)

    def __post_init__(self) -> None:
        n = np.asarray(self.n)
        v = np.asarray(self.v)
        w = np.asarray(self.w)
        sig_v = np.asarray(self.sig_v)
        pos_hmpc = np.asarray(self.pos_hmpc)
        n_rows = len(v) if v.ndim == 1 else 0
        if (
            n_rows == 0
            or n.shape != (n_rows, 3)
            or w.shape != (n_rows,)
            or sig_v.shape != (n_rows,)
            or pos_hmpc.shape != (n_rows, 3)
        ):
            raise VelocityEstimatorError(
                "CF4 sample arrays have inconsistent estimator shapes")
        arrays = (n, v, w, sig_v, pos_hmpc)
        if any(not np.issubdtype(array.dtype, np.number)
               or not np.isrealobj(array)
               or not np.all(np.isfinite(array)) for array in arrays):
            raise VelocityEstimatorError(
                "CF4 sample arrays must contain finite real values")
        if np.any(w <= 0) or np.any(sig_v <= 0):
            raise VelocityEstimatorError(
                "CF4 weights and velocity uncertainties must be positive")
        sg = None if self.sg is None else np.asarray(self.sg)
        if sg is not None and (
            sg.shape != (n_rows, 3)
            or not np.issubdtype(sg.dtype, np.number)
            or not np.isrealobj(sg)
            or not np.all(np.isfinite(sg))
        ):
            raise VelocityEstimatorError(
                "CF4 supergalactic positions must be finite (N, 3) values")
        object.__setattr__(self, "n", n)
        object.__setattr__(self, "v", v)
        object.__setattr__(self, "w", w)
        object.__setattr__(self, "sig_v", sig_v)
        object.__setattr__(self, "pos_hmpc", pos_hmpc)
        object.__setattr__(self, "sg", sg)


def load_sample(groups_path, *, h0: float = H0_CF4,
                sigma_nl: float = SIGMA_NL) -> Cf4Sample:
    try:
        h0 = float(h0)
        sigma_nl = float(sigma_nl)
    except (TypeError, ValueError) as exc:
        raise VelocityEstimatorError(
            "CF4 H0 and nonlinear velocity dispersion must be real scalars"
        ) from exc
    if not np.isfinite(h0) or h0 <= 0:
        raise VelocityEstimatorError("CF4 H0 must be finite and positive")
    if not np.isfinite(sigma_nl) or sigma_nl < 0:
        raise VelocityEstimatorError(
            "CF4 nonlinear velocity dispersion must be finite and non-negative"
        )
    d = np.load(groups_path)
    dist = d["Dist"]
    v3k = d["V3k"]
    ra = np.radians(d["RAdeg"])
    dec = np.radians(d["DEdeg"])
    nhat = np.column_stack([np.cos(dec) * np.cos(ra),
                            np.cos(dec) * np.sin(ra), np.sin(dec)])
    vpec = v3k - h0 * dist
    sigma_d = np.log(10.0) / 5.0 * d["e_DMzp"] * dist
    sig_v = np.sqrt((h0 * sigma_d) ** 2 + sigma_nl ** 2)
    w = 1.0 / sig_v ** 2
    h = fiducial()["h"]
    pos = nhat * (dist * h)[:, None]
    sg = np.column_stack([d["SGX"], d["SGY"], d["SGZ"]]) \
        if all(k in d for k in ("SGX", "SGY", "SGZ")) else None
    return Cf4Sample(n=nhat, v=vpec, w=w, sig_v=sig_v, pos_hmpc=pos, sg=sg)


def subsample(sample: Cf4Sample, n_sub: int, seed: int) -> Cf4Sample:
    rng = np.random.Generator(np.random.PCG64(seed))
    n_tot = len(sample.v)
    if n_sub >= n_tot:
        return sample
    idx = rng.choice(n_tot, size=n_sub, replace=False)
    return Cf4Sample(n=sample.n[idx], v=sample.v[idx], w=sample.w[idx],
                     sig_v=sample.sig_v[idx], pos_hmpc=sample.pos_hmpc[idx],
                     sg=sample.sg[idx] if sample.sg is not None else None)


# --------------------------------------------------------------------------
# bulk flow estimator + covariances
# --------------------------------------------------------------------------
def _design_flow(sample: Cf4Sample, monopole: bool) -> np.ndarray:
    if monopole:
        return np.column_stack([sample.n, np.ones(len(sample.v))])
    return sample.n


def _wls(design: np.ndarray, v: np.ndarray, w: np.ndarray):
    a = np.einsum("i,ij,ik->jk", w, design, design)
    rank = np.linalg.matrix_rank(a)
    if rank < design.shape[1]:
        raise VelocityEstimatorError(
            f"rank-deficient design (rank {rank} < {design.shape[1]}) — no "
            "point estimate is emitted")
    a_inv = np.linalg.inv(a)
    coeffs = a_inv @ np.einsum("i,i,ij->j", w, v, design)
    return coeffs, a_inv, a


def cosmic_variance_M(sample: Cf4Sample, design: np.ndarray) -> np.ndarray:
    """Inner cosmic-variance matrix M = sum_ab w_a w_b d_a d_b^T C_ab.

    C_ab is the Gorski linear radial-velocity covariance (correctly
    normalized: C_aa = sigma_v_1d^2). Computed on the provided sample.
    """
    fid = fiducial()
    pos = sample.pos_hmpc
    n = sample.n
    w = sample.w
    sep = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    a_grid = np.concatenate([[0.0], np.geomspace(0.5, sep.max() + 1.0, 400)])
    psi_par, psi_perp = velocity_correlation_functions(
        fid["pk"], fid["hf2"], a_grid)
    par = np.interp(sep, a_grid, psi_par)
    perp = np.interp(sep, a_grid, psi_perp)
    diff = pos[:, None, :] - pos[None, :, :]
    sep_safe = np.where(sep > 0, sep, 1.0)
    rhat = diff / sep_safe[:, :, None]
    ca = np.einsum("abk,ak->ab", rhat, n)
    cb = np.einsum("abk,bk->ab", rhat, n)
    nn = n @ n.T
    c_ab = par * ca * cb + perp * (nn - ca * cb)
    np.fill_diagonal(c_ab, psi_par[0])       # r = 0 -> sigma_v_1d^2
    return np.einsum("a,b,ak,bl,ab->kl", w, w, design, design, c_ab)


@dataclass(frozen=True)
class EstimatorResult:
    label: str
    coeffs: np.ndarray
    noise_cov: np.ndarray
    cv_cov: np.ndarray

    @property
    def full_cov(self) -> np.ndarray:
        return self.noise_cov + self.cv_cov

    def bulk_flow_vector(self) -> np.ndarray:
        return self.coeffs[:3]

    def amplitude(self) -> float:
        return float(np.linalg.norm(self.coeffs[:3]))


def estimate(sample: Cf4Sample, *, monopole: bool, label: str
             ) -> EstimatorResult:
    design = _design_flow(sample, monopole)
    coeffs, a_inv, _ = _wls(design, sample.v, sample.w)
    m = cosmic_variance_M(sample, design)
    cv_cov = a_inv @ m @ a_inv
    return EstimatorResult(label=label, coeffs=coeffs, noise_cov=a_inv,
                           cv_cov=cv_cov)


# --------------------------------------------------------------------------
# significance (full covariance) + vector comparison
# --------------------------------------------------------------------------
def _chi2_sf(x: float, k: int) -> float:
    from math import erfc, exp, sqrt
    if k == 3:
        # chi2_3 survival via the regularized upper gamma (series/cf)
        return _gammaincc(1.5, x / 2.0)
    return _gammaincc(k / 2.0, x / 2.0)


def _gammaincc(a: float, x: float) -> float:
    from math import exp, lgamma, log
    if x <= 0:
        return 1.0
    if x < a + 1.0:
        term = 1.0 / a
        s = term
        n = a
        for _ in range(500):
            n += 1.0
            term *= x / n
            s += term
            if abs(term) < abs(s) * 1e-14:
                break
        return 1.0 - s * exp(-x + a * log(x) - lgamma(a))
    b = x + 1.0 - a
    c = 1e300
    dd = 1.0 / b
    hh = dd
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2.0
        dd = an * dd + b
        if abs(dd) < 1e-300:
            dd = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        dd = 1.0 / dd
        de = dd * c
        hh *= de
        if abs(de - 1.0) < 1e-14:
            break
    return hh * exp(-x + a * log(x) - lgamma(a))


def _sigma_from_chi2(chi2: float, dof: int) -> float:
    """Two-sided-equivalent Gaussian sigma from a chi-square tail p-value."""
    from math import sqrt
    p = _chi2_sf(chi2, dof)
    p = min(max(p, 1e-300), 1.0)
    return float(_inv_norm_sf(p / 2.0))


def _inv_norm_sf(q: float) -> float:
    # inverse survival of the standard normal (Acklam)
    from math import log, sqrt
    if q <= 0:
        return 40.0
    if q >= 1:
        return -40.0
    p = 1.0 - q
    a = [-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    dd = [7.784695709041462e-03, 3.224671290700398e-01,
          2.445134137142996e+00, 3.754408661907416e+00]
    plow = 0.02425
    if p < plow:
        r = (-2.0 * log(p)) ** 0.5
        return (((((c[0] * r + c[1]) * r + c[2]) * r + c[3]) * r + c[4]) * r
                + c[5]) / ((((dd[0] * r + dd[1]) * r + dd[2]) * r + dd[3])
                           * r + 1.0)
    if p <= 1 - plow:
        r = p - 0.5
        rr = r * r
        return (((((a[0] * rr + a[1]) * rr + a[2]) * rr + a[3]) * rr + a[4])
                * rr + a[5]) * r / (((((b[0] * rr + b[1]) * rr + b[2]) * rr
                                     + b[3]) * rr + b[4]) * rr + 1.0)
    r = (-2.0 * log(1 - p)) ** 0.5
    return -(((((c[0] * r + c[1]) * r + c[2]) * r + c[3]) * r + c[4]) * r
             + c[5]) / ((((dd[0] * r + dd[1]) * r + dd[2]) * r + dd[3])
                        * r + 1.0)


def significance(vector: np.ndarray, cov: np.ndarray) -> dict:
    chi2 = float(vector @ np.linalg.solve(cov, vector))
    return {"chi2": chi2, "dof": len(vector),
            "sigma": _sigma_from_chi2(chi2, len(vector))}


def full_covariance_significance(result: EstimatorResult) -> dict:
    b = result.bulk_flow_vector()
    noise_only = significance(b, result.noise_cov[:3, :3])
    full = significance(b, result.full_cov[:3, :3])
    if full["sigma"] >= noise_only["sigma"]:
        raise VelocityEstimatorError(
            "the full-covariance significance is not below the noise-only "
            "figure — the cosmic-variance covariance is not being applied")
    return {"amplitude_kms": result.amplitude(),
            "noise_only_sigma": noise_only["sigma"],
            "full_covariance_sigma": full["sigma"],
            "note": "the full-covariance significance is the honest figure; "
                    "the noise-only figure is a formal over-estimate; the "
                    "linear cosmic-variance covariance is a lower bound so "
                    "the reported significance is an upper bound"}


def compare_vectors(a: EstimatorResult, b: EstimatorResult) -> dict:
    """Mahalanobis distance of the flow-vector difference under summed cov."""
    diff = a.bulk_flow_vector() - b.bulk_flow_vector()
    cov = a.full_cov[:3, :3] + b.full_cov[:3, :3]
    sig = significance(diff, cov)
    return {"vector_difference_kms": diff.tolist(),
            "mahalanobis_chi2": sig["chi2"], "consistency_sigma": sig["sigma"],
            "note": "estimators compared as vectors under the full "
                    "covariance, never a scalar amplitude overlap"}


# --------------------------------------------------------------------------
# cosmic-variance correlation matrix + coverage injection
# --------------------------------------------------------------------------
def _cv_correlation_matrix(sample: Cf4Sample) -> np.ndarray:
    """The N x N Gorski radial-velocity correlation C_ab (km^2/s^2)."""
    fid = fiducial()
    pos, n = sample.pos_hmpc, sample.n
    sep = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    a_grid = np.concatenate([[0.0], np.geomspace(0.5, sep.max() + 1.0, 400)])
    psi_par, psi_perp = velocity_correlation_functions(
        fid["pk"], fid["hf2"], a_grid)
    par = np.interp(sep, a_grid, psi_par)
    perp = np.interp(sep, a_grid, psi_perp)
    diff = pos[:, None, :] - pos[None, :, :]
    sep_safe = np.where(sep > 0, sep, 1.0)
    rhat = diff / sep_safe[:, :, None]
    ca = np.einsum("abk,ak->ab", rhat, n)
    cb = np.einsum("abk,bk->ab", rhat, n)
    c_ab = par * ca * cb + perp * (n @ n.T - ca * cb)
    np.fill_diagonal(c_ab, psi_par[0])
    return c_ab


def coverage_injection(sample: Cf4Sample, flow_true, monopole_true, *,
                       n_inj: int, seed: int) -> dict:
    """Inject a known flow + monopole on top of correlated cosmic variance +
    measurement noise; report the coverage the FULL covariance gives AND the
    coverage the noise-only covariance gives.

    This is a covariance-PROPAGATION self-consistency check plus a
    full-versus-noise-only DISCRIMINATION: the data-generating covariance and
    the full assessed covariance share the same Gorski correlation, so nominal
    full coverage validates the propagation algebra (not the physical
    correctness of the P(k) / Gorski model); the noise-only assessed
    covariance UNDER-covers, which is the concrete failure the P0's formal
    error committed."""
    design = _design_flow(sample, monopole=True)
    a = np.einsum("i,ij,ik->jk", sample.w, design, design)
    a_inv = np.linalg.inv(a)
    m = cosmic_variance_M(sample, design)
    full_cov = a_inv + a_inv @ m @ a_inv
    sd_full = np.sqrt(np.diag(full_cov))
    sd_noise = np.sqrt(np.diag(a_inv))
    c_ab = _cv_correlation_matrix(sample)
    lchol = np.linalg.cholesky(c_ab + 1e-6 * np.eye(len(c_ab)))
    truth = np.concatenate([np.asarray(flow_true, float), [monopole_true]])
    rng = np.random.Generator(np.random.PCG64(seed))
    n_gal = len(sample.v)
    h68 = np.zeros(4)
    h95 = np.zeros(4)
    h68_noise = np.zeros(4)
    for _ in range(n_inj):
        v_cv = lchol @ rng.standard_normal(n_gal)
        noise = rng.normal(0.0, sample.sig_v)
        v = design @ truth + v_cv + noise
        coeffs = a_inv @ np.einsum("i,i,ij->j", sample.w, v, design)
        dev = np.abs(coeffs - truth)
        h68 += dev / sd_full <= 1.0
        h95 += dev / sd_full <= 1.959963985
        h68_noise += dev / sd_noise <= 1.0
    return {"n_injections": n_inj, "labels": ["Bx", "By", "Bz", "M"],
            "coverage_68": (h68 / n_inj).tolist(),
            "coverage_95": (h95 / n_inj).tolist(),
            "coverage_68_noise_only": (h68_noise / n_inj).tolist(),
            "note": "propagation self-consistency (the full covariance covers "
                    "at nominal 68/95 by construction) PLUS a full-vs-noise-"
                    "only discrimination (the noise-only covariance under-"
                    "covers far below 0.68); this validates the covariance "
                    "algebra and the necessity of the cosmic-variance term, "
                    "NOT the physical correctness of the P(k)/Gorski model"}


def require_coverage_in_band(coverage_report: dict, nominal: float,
                             half_width: float) -> None:
    try:
        nominal = float(nominal)
        half_width = float(half_width)
    except (TypeError, ValueError) as exc:
        raise VelocityEstimatorError(
            "coverage nominal and half-width must be real scalars"
        ) from exc
    if not np.isfinite(nominal):
        raise VelocityEstimatorError("coverage nominal must be finite")
    if np.isclose(nominal, 0.68, rtol=0.0, atol=1e-12):
        key = "coverage_68"
    elif np.isclose(nominal, 0.95, rtol=0.0, atol=1e-12):
        key = "coverage_95"
    else:
        raise VelocityEstimatorError(
            "coverage nominal must select the 0.68 or 0.95 report")
    if not np.isfinite(half_width) or not 0.0 <= half_width <= 1.0:
        raise VelocityEstimatorError(
            "coverage half-width must be finite and within [0, 1]")
    labels = coverage_report["labels"]
    values = coverage_report[key]
    if (
        isinstance(labels, (str, bytes))
        or isinstance(values, (str, bytes))
        or len(labels) == 0
        or len(labels) != len(values)
    ):
        raise VelocityEstimatorError(
            "coverage report must have one value for every component")
    for label, cov in zip(labels, values):
        if not np.isscalar(cov) or not np.isreal(cov) \
                or not np.isfinite(cov) or not 0.0 <= cov <= 1.0:
            raise VelocityEstimatorError(
                f"component {label} coverage must be finite and within [0, 1]")
        if abs(cov - nominal) > half_width:
            raise VelocityEstimatorError(
                f"component {label} coverage {cov:.3f} is outside the "
                f"{nominal} +/- {half_width} band — the covariance is "
                "mis-calibrated")


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def require_full_covariance_significance(kind: str) -> None:
    if kind in ("noise_only", "formal", "measurement_noise_only"):
        raise VelocityEstimatorError(
            "the measurement-noise-only (formal) significance may not be "
            "reported as the result; the full covariance is required")


def refuse_scalar_amplitude_overlap(comparison_kind: str) -> None:
    if comparison_kind in ("scalar_amplitude_overlap", "amplitude_only"):
        raise VelocityEstimatorError(
            "estimators are compared as vectors under the full covariance, "
            "not by a scalar amplitude overlap")


def refuse_constrained_median_as_truth(claim: str) -> None:
    if claim in ("constrained_median_truth", "median_is_truth"):
        raise VelocityEstimatorError(
            "the constrained-estimator median is not the truth")


def refuse_cf4_p0_closure(claim: str) -> None:
    if claim in ("cf4_p0_closed", "p0_resolved", "remediation_complete"):
        raise VelocityEstimatorError(
            "a CF4 P0 may not be closed before the PR-157 adjudication; "
            "PR-145 emits a remediation CANDIDATE only")


def require_eight_region_label(label: str) -> None:
    if label not in ("eight_region_partition", "eight_region"):
        raise VelocityEstimatorError(
            "the supergalactic partition is an eight-region partition, never "
            "loosely an octant subset")


# --------------------------------------------------------------------------
# eight-region partition
# --------------------------------------------------------------------------
def eight_region_partition(sample: Cf4Sample) -> dict:
    require_eight_region_label("eight_region_partition")
    if sample.sg is None:
        raise VelocityEstimatorError(
            "the supergalactic Cartesian columns (SGX/SGY/SGZ) are required "
            "for the eight-region partition; the equatorial position is not "
            "the supergalactic frame")
    signs = (sample.sg > 0).astype(int)
    region_id = signs[:, 0] * 4 + signs[:, 1] * 2 + signs[:, 2]
    counts = {int(r): int(np.sum(region_id == r)) for r in range(8)}
    min_count = min(counts.values())
    if min_count == 0:
        raise VelocityEstimatorError(
            "an eight-region partition region is empty — the leverage check "
            "requires all eight supergalactic octants populated")
    return {"scheme": "supergalactic_cartesian_octants_SGX_SGY_SGZ_sign",
            "n_regions": 8, "counts": counts, "min_count": min_count,
            "label": "eight_region_partition"}


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("constrained median is ", "the truth"),
        ("formal significance is ", "the result"),
        ("cf4 p0 ", "closed"),
        ("scalar amplitude overlap is ", "the comparison"),
        ("nuisance chosen to match ", "the headline"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise VelocityEstimatorError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(amplitude: float, noise_sigma: float,
                     full_sigma: float) -> str:
    return (
        f"CF4 bulk-flow estimator (full covariance = measurement noise + "
        f"linear cosmic variance): amplitude {amplitude:.0f} km/s; the "
        f"full-covariance significance {full_sigma:.1f} sigma is far below "
        f"the noise-only formal figure {noise_sigma:.1f} sigma, which the "
        f"cosmic-variance term corrects. Observable-estimator mechanics "
        f"only; the two CF4 P0s stay OPEN with remediation-candidate "
        f"receipts pending the PR-157 adjudication; no detection.")
