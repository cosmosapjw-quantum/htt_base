"""LR-06D: maximum-likelihood bulk-flow estimator for a peculiar-velocity catalog.

Model: each group i has a radial peculiar velocity Vpec_i along its line of sight
unit vector n_i, with Gaussian error sigma_i. The bulk flow B (a 3-vector) is the
minimum-variance estimator

    A = sum_i n_i n_i^T / sigma_i^2 ,   b = sum_i n_i Vpec_i / sigma_i^2 ,
    B_hat = A^{-1} b ,                  Cov(B_hat) = A^{-1} .

sigma_i combines the distance-modulus velocity error and an intrinsic 1D
dispersion sigma_star added in quadrature. This is observer-side feature
extraction (OBSSTAT): a kinematic descriptor, not a model evidence, and not a
global-tilt or Bianchi-geometry claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

LN10_OVER_5 = np.log(10.0) / 5.0


@dataclass(frozen=True)
class BulkFlow:
    vector: np.ndarray        # B_hat (km/s), Cartesian
    covariance: np.ndarray    # Cov(B_hat) (km/s)^2
    amplitude: float          # |B_hat| (km/s)
    amplitude_error: float    # 1-sigma on |B|
    n_groups: int
    sigma_star: float

    def as_dict(self) -> dict:
        return {"vector_kms": self.vector.tolist(), "amplitude_kms": self.amplitude,
                "amplitude_error_kms": self.amplitude_error, "n_groups": self.n_groups,
                "sigma_star_kms": self.sigma_star,
                "covariance": self.covariance.tolist()}


def velocity_error(e_dm: np.ndarray, v_cosmo: np.ndarray) -> np.ndarray:
    """Peculiar-velocity error from the distance-modulus uncertainty:
    sigma_v = (ln10/5) * e_DM * V_cosmo (the log-distance-ratio error)."""
    return LN10_OVER_5 * np.asarray(e_dm, dtype=float) * np.abs(np.asarray(v_cosmo, dtype=float))


def estimate_bulk_flow(unit_vectors: np.ndarray, vpec: np.ndarray, sigma: np.ndarray,
                       sigma_star: float = 250.0) -> BulkFlow:
    n = np.asarray(unit_vectors, dtype=float)
    v = np.asarray(vpec, dtype=float)
    s = np.asarray(sigma, dtype=float)
    if n.ndim != 2 or n.shape[1] != 3 or v.shape[0] != n.shape[0]:
        raise ValueError("unit_vectors (N,3), vpec (N,) required")
    w = 1.0 / (s * s + sigma_star * sigma_star)
    A = np.einsum("i,ij,ik->jk", w, n, n)
    b = np.einsum("i,ij->j", w * v, n)
    cov = np.linalg.inv(A)
    B = cov @ b
    amp = float(np.linalg.norm(B))
    # error on amplitude: project covariance onto the B direction.
    if amp > 0:
        u = B / amp
        amp_err = float(np.sqrt(u @ cov @ u))
    else:
        amp_err = float(np.sqrt(np.trace(cov) / 3.0))
    return BulkFlow(B, cov, amp, amp_err, int(n.shape[0]), float(sigma_star))


def fit_sigma_star(unit_vectors: np.ndarray, vpec: np.ndarray, sigma_meas: np.ndarray,
                   grid: np.ndarray | None = None) -> float:
    """Pick sigma_star so the reduced chi^2 of the bulk-flow residual is ~1."""
    if grid is None:
        grid = np.linspace(50.0, 600.0, 56)
    n = np.asarray(unit_vectors, dtype=float)
    v = np.asarray(vpec, dtype=float)
    best, best_obj = float(grid[0]), np.inf
    for ss in grid:
        bf = estimate_bulk_flow(n, v, sigma_meas, sigma_star=ss)
        resid = v - n @ bf.vector
        w = 1.0 / (sigma_meas ** 2 + ss ** 2)
        chi2_red = float(np.sum(w * resid ** 2) / (len(v) - 3))
        if abs(chi2_red - 1.0) < best_obj:
            best_obj, best = abs(chi2_red - 1.0), float(ss)
    return best


def forward_mock_coverage(unit_vectors: np.ndarray, sigma: np.ndarray, b_true: np.ndarray,
                          sigma_star: float, n_mock: int = 400, seed: int = 7) -> dict:
    """Inject b_true, draw noisy mocks with the real geometry+errors, recover, and
    report the 1-sigma coverage of the injected amplitude."""
    n = np.asarray(unit_vectors, dtype=float)
    s = np.asarray(sigma, dtype=float)
    b_true = np.asarray(b_true, dtype=float)
    rng = np.random.default_rng(seed)
    amp_true = float(np.linalg.norm(b_true))
    covered = 0
    recovered = []
    tot = np.sqrt(s ** 2 + sigma_star ** 2)
    for _ in range(n_mock):
        v = n @ b_true + rng.normal(0.0, tot)
        bf = estimate_bulk_flow(n, v, s, sigma_star=sigma_star)
        recovered.append(bf.amplitude)
        if abs(bf.amplitude - amp_true) <= bf.amplitude_error:
            covered += 1
    return {"injected_amplitude_kms": amp_true, "n_mock": int(n_mock),
            "recovered_mean_kms": float(np.mean(recovered)),
            "recovered_std_kms": float(np.std(recovered, ddof=1)),
            "one_sigma_coverage": covered / n_mock}
