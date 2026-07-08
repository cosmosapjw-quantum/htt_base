"""EGS3 Axis E: posterior prior-exposure on null response directions (P28).

Statement (P28). If the likelihood depends on g only through R g and the prior
factorizes across a null coordinate j (column j of R identically zero, prior
pi(g) = pi_j(g_j) pi_{-j}(g_{-j})), then the posterior marginal of g_j EQUALS its
prior marginal: the likelihood contributes no factor in g_j, so it cancels in the
marginalization. Consequently the KL divergence between prior and posterior
RESTRICTED to the null sigma-field is exactly zero, and any pushforward probability
P_post(Z > t) whose statistic Z loads on a null direction is a PRIOR statement in
that direction, not a data statement. Fail-closed reporting must therefore label
such pushforwards prior-exposed (this is the guard behind the existing
``prior_contaminated`` classification in `departure_posteriors`).

The converse direction is also demonstrated: with a COUPLED prior (off-diagonal
prior covariance between a reachable and a null coordinate) the posterior null
marginal moves -- but only through the prior coupling, never through the
likelihood; the witness reports that KL as prior-driven.

Everything here is closed-form Gaussian conjugate algebra plus a seeded sampling
cross-check; no data enters.

Claim discipline. Diagnostic-only; no detection, family/geometry, native-solver, or
posterior-on-real-data claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

__all__ = [
    "kl_gaussians",
    "PriorLeakWitness",
    "gaussian_prior_exposure_witness",
]


def kl_gaussians(mu0, S0, mu1, S1) -> float:
    """KL( N(mu0, S0) || N(mu1, S1) ) for 1-D or n-D Gaussians."""
    mu0 = np.atleast_1d(np.asarray(mu0, dtype=float))
    mu1 = np.atleast_1d(np.asarray(mu1, dtype=float))
    S0 = np.atleast_2d(np.asarray(S0, dtype=float))
    S1 = np.atleast_2d(np.asarray(S1, dtype=float))
    k = mu0.size
    S1_inv = np.linalg.inv(S1)
    diff = mu1 - mu0
    val = (np.trace(S1_inv @ S0) + diff @ S1_inv @ diff - k
           + math.log(max(np.linalg.det(S1), 1e-300))
           - math.log(max(np.linalg.det(S0), 1e-300)))
    return 0.5 * float(val)


@dataclass(frozen=True)
class PriorLeakWitness:
    kl_null_block: float
    max_abs_moment_diff: float
    coupled_prior_kl: float
    n_samples: int
    seed: int


def gaussian_prior_exposure_witness(*, seed: int = 20260708,
                                    n_samples: int = 20000) -> PriorLeakWitness:
    """Closed-form + sampled witness of P28 on a 3-coordinate toy.

    g = (g_reach1, g_null, g_reach2); R has a zero middle column; y = R g + eps,
    eps ~ N(0, I). Factorized prior: posterior marginal on g_null == prior (KL = 0
    exactly). Coupled prior (reach1-null covariance 0.6): the null marginal moves,
    KL > 0, labelled prior-driven."""
    rng = np.random.default_rng(seed)
    R = np.array([[1.0, 0.0, 0.0],
                  [0.0, 0.0, 1.0],
                  [1.0, 0.0, 1.0],
                  [1.0, 0.0, -1.0]])
    g_true = np.array([0.7, 0.0, -0.3])
    y = R @ g_true + rng.normal(size=R.shape[0])

    def posterior(prior_cov: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        prec = R.T @ R + np.linalg.inv(prior_cov)
        cov = np.linalg.inv(prec)
        mean = cov @ (R.T @ y)               # prior mean zero
        return mean, cov

    # factorized prior: diagonal covariance
    prior_var_null = 2.0
    prior_fact = np.diag([1.5, prior_var_null, 1.5])
    mean_f, cov_f = posterior(prior_fact)
    kl_null = kl_gaussians(0.0, prior_var_null, mean_f[1], cov_f[1, 1])

    # sampling cross-check of the null marginal moments
    samples = rng.multivariate_normal(mean_f, cov_f, size=int(n_samples))
    moment_diff = max(abs(float(samples[:, 1].mean()) - 0.0),
                      abs(float(samples[:, 1].var(ddof=1)) - prior_var_null))
    # normalize by the MC sampling scale so the witness is n_samples-stable
    moment_scale = prior_var_null / math.sqrt(float(n_samples))
    moment_diff_normalized = moment_diff / (3.0 * moment_scale)

    # coupled prior: reach1-null off-diagonal
    prior_coupled = np.array([[1.5, 0.6, 0.0],
                              [0.6, prior_var_null, 0.0],
                              [0.0, 0.0, 1.5]])
    mean_c, cov_c = posterior(prior_coupled)
    kl_coupled = kl_gaussians(0.0, prior_var_null, mean_c[1], cov_c[1, 1])

    return PriorLeakWitness(
        kl_null_block=float(kl_null),
        max_abs_moment_diff=float(moment_diff_normalized),
        coupled_prior_kl=float(kl_coupled),
        n_samples=int(n_samples), seed=int(seed),
    )
