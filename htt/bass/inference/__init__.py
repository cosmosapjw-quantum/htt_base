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
from bass.inference.live_binding import (
    FittingBlockedError,
    LiveObserverBoostProblem,
    build_live_observer_boost_problem,
    build_type_i_native_validation_problem,
    run_type_i_native_validation_posterior,
)
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
    "FittingBlockedError",
    "GEWEKE_ABS_Z_THRESHOLD",
    "Prior",
    "PosteriorSample",
    "R_HAT_THRESHOLD",
    "SUN_CMB_DIPOLE_DIRECTION",
    "LiveObserverBoostProblem",
    "bayes_factor",
    "build_live_observer_boost_problem",
    "build_type_i_native_validation_problem",
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
    "run_type_i_native_validation_posterior",
    "trace_plot_data",
]
