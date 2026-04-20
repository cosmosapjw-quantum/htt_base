"""Posterior inference, diagnostics, and evidence helpers for FB-11."""

from bass.inference.bayes import BayesFactorResult, bayes_factor
from bass.inference.diagnostics import (
    ESS_THRESHOLD,
    GEWEKE_ABS_Z_THRESHOLD,
    R_HAT_THRESHOLD,
    convergence_report,
    ess,
    geweke,
    r_hat,
    trace_plot_data,
)
from bass.inference.drivers.emcee_driver import PosteriorSample, run_posterior
from bass.inference.priors import (
    Prior,
    SUN_CMB_DIPOLE_DIRECTION,
    prior_direction,
    prior_observer_boost,
    prior_rapidity,
    prior_structure_constants,
    prior_Sigma_mnu,
)

__all__ = [
    "BayesFactorResult",
    "ESS_THRESHOLD",
    "GEWEKE_ABS_Z_THRESHOLD",
    "Prior",
    "PosteriorSample",
    "R_HAT_THRESHOLD",
    "SUN_CMB_DIPOLE_DIRECTION",
    "bayes_factor",
    "convergence_report",
    "ess",
    "geweke",
    "prior_rapidity",
    "prior_direction",
    "prior_Sigma_mnu",
    "prior_observer_boost",
    "prior_structure_constants",
    "r_hat",
    "run_posterior",
    "trace_plot_data",
]
