"""EGS3 A3 / A4: Pi e-value calibration + Rao-Blackwell sufficiency.

A3 (Pi exceedance e-value calibration). The MIO Pi is a threshold-exceedance
curve, disciplined as "not a probability" and samplewise-dominated by a bound
curve (registry S4). We promote it to a CALIBRATED CERTIFICATE: from the null
exceedance alpha = P_null(score > t), the indicator e-value

    E(x) = 1[x > t] / alpha

has null expectation E_null[E] = 1, so Markov gives the false-exceedance bound

    P_null( E >= 1/beta ) <= beta .

When only an upper bound alpha_bound >= alpha is available (the S4 domination),
the conservative e-value E_bound = 1[x>t]/alpha_bound has E_null[E_bound] <= 1,
which keeps the Markov guarantee one-sided (conservative). This turns Pi from
"not a probability" into an e-value with a stated, provable error rate.

A4 (Rao-Blackwell sufficiency). For the rank-2 identifiable subspace, the
sufficient statistic T = (a2, a3, bulk-dipole) Rao-Blackwellises any unbiased
estimator: theta_RB = E[theta_raw | T] has Var(theta_RB) <= Var(theta_raw).
A per-object raw estimator that ignores T is therefore dominated.

All synthetic mechanics; diagnostic-only; no detection or family ID.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# --------------------------------------------------------------------------- #
# A3 - Pi exceedance e-value calibration
# --------------------------------------------------------------------------- #
def exceedance_evalue(score: float, threshold: float, null_exceedance: float) -> float:
    """E(x) = 1[x > t] / alpha, with alpha = P_null(score > t) (or an upper bound).

    `null_exceedance` must be the KNOWN (or upper-bounded) null exceedance. Do NOT
    pass a raw finite-sample estimate k/n here: at k=0 it is zero and raises, and a
    raw plug-in is anti-conservative because E[1/alpha_hat] > 1/alpha (Jensen). Use
    `exceedance_evalue_finite_null` for an estimated null (audit FM4)."""
    if not (0.0 < null_exceedance <= 1.0):
        raise ValueError("null_exceedance must be in (0,1]")
    return (1.0 if score > threshold else 0.0) / null_exceedance


def exceedance_evalue_finite_null(score: float, threshold: float,
                                  n_exceed: int, n_null: int) -> float:
    """Finite-null (plug-in) e-value with the conservative add-one estimate
    alpha_hat = (k + 1) / (n + 1),  k = #{null sample > t},  n = null size.

    Fixes the two failure modes of dividing a raw k/n exceedance into the indicator
    (audit FM4):
      * k = 0 no longer divides by zero (alpha_hat = 1/(n+1) > 0) -- no crash;
      * (k+1)/(n+1) >= k/n is a conservative OVER-estimate of alpha, so the e-value
        is not anti-conservative under the Jensen inflation E[1/alpha_hat] > 1/alpha
        that a raw plug-in suffers; the Markov guarantee P_null(E >= 1/beta) <= beta
        is preserved under the finite registered null.
    The e-value's error rate is still calibrated to the registered null's
    idealisation (e.g. GRF-LambdaCDM); the correction only removes the finite-sample
    estimation pathology, not the null misspecification."""
    if n_null <= 0:
        raise ValueError("n_null must be positive")
    if not (0 <= n_exceed <= n_null):
        raise ValueError("n_exceed must satisfy 0 <= n_exceed <= n_null")
    alpha_hat = (n_exceed + 1.0) / (n_null + 1.0)
    return (1.0 if score > threshold else 0.0) / alpha_hat


@dataclass(frozen=True)
class EValueCalibration:
    threshold: float
    null_exceedance: float
    null_mean_evalue: float
    beta_grid: tuple[float, ...]
    empirical_false_rate: tuple[float, ...]
    markov_holds: bool
    n_sims: int


def evalue_markov_calibration(n_sims: int = 20000, threshold: float = 1.5,
                              beta_grid=(0.5, 0.2, 0.1, 0.05, 0.02),
                              seed: int = 71) -> EValueCalibration:
    """MC-verify that E = 1[x>t]/alpha is a valid e-value: null mean ~1 and the
    Markov false-exceedance rate P_null(E >= 1/beta) <= beta holds for all beta."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n_sims)                       # registered null
    alpha = float(np.mean(x > threshold))
    if alpha == 0.0:
        raise ValueError("threshold too extreme for the null sample")
    e = (x > threshold).astype(float) / alpha
    null_mean = float(e.mean())
    rates = tuple(float(np.mean(e >= 1.0 / b)) for b in beta_grid)
    markov = all(r <= b + 3.0 / np.sqrt(n_sims) for r, b in zip(rates, beta_grid))
    return EValueCalibration(threshold, alpha, null_mean, tuple(beta_grid), rates,
                             bool(markov), int(n_sims))


def domination_is_conservative(sample_exceedance: float, bound_exceedance: float) -> bool:
    """S4 domination -> the bound-based e-value has null expectation <= 1
    (conservative): requires bound_exceedance >= sample_exceedance."""
    return bool(bound_exceedance >= sample_exceedance > 0.0)


# --------------------------------------------------------------------------- #
# A4 - Rao-Blackwell sufficiency for the reachable sectors
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RaoBlackwellResult:
    raw_variance: float
    rb_variance: float
    dominates: bool
    n_groups: int
    n_per_group: int


def rao_blackwell_demonstration(n_groups: int = 200, n_per_group: int = 40,
                                theta_true: float = 1.0, extra_noise: float = 1.0,
                                seed: int = 17) -> RaoBlackwellResult:
    """The sufficient statistic T (here the per-group mean, standing in for
    (a2,a3,dipole)) Rao-Blackwellises a noisy raw estimator: conditioning on T
    cannot increase variance. We compare a raw per-sample estimator against its
    conditional expectation given T over many groups."""
    rng = np.random.default_rng(seed)
    raw_ests = np.empty(n_groups)
    rb_ests = np.empty(n_groups)
    for i in range(n_groups):
        samples = theta_true + rng.standard_normal(n_per_group)
        # raw estimator: a single sample plus independent extra noise (ignores T)
        raw_ests[i] = samples[0] + extra_noise * rng.standard_normal()
        # Rao-Blackwell: E[raw | T], T = sufficient (sample mean for a Gaussian)
        rb_ests[i] = float(samples.mean())
    raw_var = float(raw_ests.var(ddof=1))
    rb_var = float(rb_ests.var(ddof=1))
    return RaoBlackwellResult(raw_var, rb_var, bool(rb_var <= raw_var),
                              int(n_groups), int(n_per_group))
