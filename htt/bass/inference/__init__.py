"""bass.inference — FB-11 inference scaffolding.

This package is introduced at FB-META-11 for inference-only contracts.
During the skeleton cycle, public surfaces document the future posterior
and evidence workflow but raise `NotImplementedError` rather than
opening a fake sampling path.
"""

from bass.inference.bayes import BayesFactorResult, bayes_factor
from bass.inference.diagnostics import ess, geweke, r_hat, trace_plot_data
from bass.inference.drivers.emcee_driver import PosteriorSample, run_posterior
from bass.inference.priors import (
    Prior,
    prior_direction,
    prior_observer_boost,
    prior_rapidity,
    prior_structure_constants,
    prior_Sigma_mnu,
)

__all__ = [
    "BayesFactorResult",
    "Prior",
    "PosteriorSample",
    "bayes_factor",
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
