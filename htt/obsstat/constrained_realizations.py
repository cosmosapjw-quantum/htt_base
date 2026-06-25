"""BLOCK-K6 discharge mechanics: Hoffman-Ribak constrained-realization vorticity posterior.

The report's K6 reports vorticity as "structurally non-identifiable" because the
single Wiener-filter (WF) reconstruction is curl-suppressed. The Hoffman-Ribak
(1991) constrained-realization (CR) algorithm samples the field *posterior*
around the WF mean:

    s_CR = s_WF + (s_rand - WF[s_rand]).

Each CR carries a curl component; the CR *ensemble* is the vorticity posterior the
WF mean alone suppresses. This upgrades "non-identifiable" to "posterior mean ~0
with a prior-width error bar, dominated by the curl-suppressed prior". The same
CF4 WF/CR machinery (Bias-Gaussianization + WF/CR, Hoffman et al. 2024,
arXiv:2311.01340) also generates the release-matched forward mocks that discharge
the K5 cosmic-variance term.

This module is the *mechanics* on a toy Gaussian curl sector; the real 3D CF4
WF/CR run (the ensemble that turns this into the actual K6 posterior) remains
BLOCKED_MISSING_FIELD_REALIZATIONS until the CF4 field realizations are owned.
No detection is implied: a posterior mean ~0 with a prior-width bar is not a
vorticity measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


def wiener_filter_mean(data_constraint: float, signal_var: float, noise_var: float) -> float:
    """WF mean for a single mode: s_WF = (S/(S+N)) d. Curl-suppressed when the
    data place no constraint on the curl mode (data_constraint = 0)."""
    if signal_var < 0 or noise_var < 0:
        raise ValueError("variances must be nonnegative")
    return (signal_var / (signal_var + noise_var)) * data_constraint


def constrained_realization(data_constraint: float, signal_var: float, noise_var: float,
                            rng: np.random.Generator) -> float:
    """Hoffman-Ribak: s_CR = s_WF + (s_rand - WF[mock(s_rand)]). For a curl mode
    with no data constraint, s_WF = 0 but s_CR carries the prior fluctuation."""
    s_wf = wiener_filter_mean(data_constraint, signal_var, noise_var)
    s_rand = rng.normal(0.0, signal_var ** 0.5)
    d_rand = s_rand + rng.normal(0.0, noise_var ** 0.5)
    s_rand_wf = wiener_filter_mean(d_rand, signal_var, noise_var)
    return s_wf + (s_rand - s_rand_wf)


@dataclass(frozen=True)
class CurlPosterior:
    wf_estimate: float
    cr_mean: float
    cr_sd: float
    cr_p16: float
    cr_p84: float
    n_cr: int


def curl_posterior(signal_var: float = 1.0, noise_var: float = 0.5, n_cr: int = 400,
                   seed: int = 4242) -> CurlPosterior:
    """The vorticity (curl) posterior from a CR ensemble: the WF mean alone is
    ~0 (suppressed); the CR spread is the posterior the WF mean hides."""
    rng = np.random.default_rng(seed)
    wf = wiener_filter_mean(0.0, signal_var, noise_var)
    crs = np.array([constrained_realization(0.0, signal_var, noise_var, rng) for _ in range(n_cr)])
    return CurlPosterior(
        wf_estimate=float(wf),
        cr_mean=float(crs.mean()),
        cr_sd=float(crs.std(ddof=1)),
        cr_p16=float(np.percentile(crs, 16)),
        cr_p84=float(np.percentile(crs, 84)),
        n_cr=int(n_cr),
    )
