"""
htt/infer/survey_nuisance.py — Survey-Specific Nuisance Layer
================================================================
Milestone M2.3 deliverable. Dedicated module for per-survey systematic
error budgets, covariance matrices, and nuisance marginalization.

Each low-z survey contributing to the bulk-flow measurement carries
its own systematic error profile:

  - CosmicFlows-4 (CF4): Tully-Fisher calibration, Malmquist bias,
    peculiar velocity scatter, inhomogeneous spatial coverage.
  - Cosmic Waves (CW): SNIa standardization residuals, host-galaxy
    correlations, selection effects.
  - Radio catalogs: beam systematics, RFI, catalog incompleteness.

The nuisance layer provides:
  1. Per-survey covariance matrices (diagonal + off-diagonal systematics).
  2. Nuisance parameter priors for marginalization.
  3. Survey-combination weights accounting for systematic budgets.
  4. Compatibility checks between surveys.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

__all__ = [
    'SurveyNuisance', 'SurveyCovariance', 'SURVEY_REGISTRY',
    'get_survey_nuisance', 'combined_covariance',
    'nuisance_marginal_correction', 'survey_compatibility_test',
]


@dataclass(frozen=True)
class SurveyCovariance:
    """Covariance structure for one survey's systematic budget."""
    name: str
    sigma_stat: float           # statistical error on β (per-object)
    sigma_sys: float            # systematic floor on β
    sigma_calibration: float    # calibration uncertainty
    n_objects: int              # number of objects in survey
    sigma_total: float = 0.0   # total per-survey β uncertainty

    def __post_init__(self):
        if self.sigma_total == 0.0:
            object.__setattr__(self, 'sigma_total',
                np.sqrt(self.sigma_stat**2 / self.n_objects +
                        self.sigma_sys**2 +
                        self.sigma_calibration**2))


@dataclass(frozen=True)
class SurveyNuisance:
    """Full nuisance specification for one survey."""
    covariance: SurveyCovariance
    delta_name: str             # nuisance parameter name (e.g. 'delta_CF4')
    prior_width: float          # Gaussian prior width on the nuisance offset
    direction_systematic: float # systematic in direction (degrees)
    malmquist_correction: float # Malmquist bias correction factor
    selection_function: str     # description of selection


# ── Survey Registry ──────────────────────────────────────

_CF4_COV = SurveyCovariance(
    name='CF4', sigma_stat=0.22e-3, sigma_sys=0.05e-3,
    sigma_calibration=0.08e-3, n_objects=8000,
)
_CW_COV = SurveyCovariance(
    name='CW', sigma_stat=0.35e-3, sigma_sys=0.03e-3,
    sigma_calibration=0.12e-3, n_objects=1200,
)
_RADIO_COV = SurveyCovariance(
    name='Radio', sigma_stat=0.50e-3, sigma_sys=0.08e-3,
    sigma_calibration=0.15e-3, n_objects=500,
)

SURVEY_REGISTRY: Dict[str, SurveyNuisance] = {
    'CF4': SurveyNuisance(
        covariance=_CF4_COV,
        delta_name='delta_CF4',
        prior_width=0.1e-3,
        direction_systematic=5.0,
        malmquist_correction=1.02,
        selection_function='Volume-limited TF/FP with Malmquist correction',
    ),
    'CW': SurveyNuisance(
        covariance=_CW_COV,
        delta_name='delta_CW',
        prior_width=0.15e-3,
        direction_systematic=3.0,
        malmquist_correction=1.0,
        selection_function='SNIa with host-galaxy standardization',
    ),
    'Radio': SurveyNuisance(
        covariance=_RADIO_COV,
        delta_name='delta_rad',
        prior_width=0.2e-3,
        direction_systematic=8.0,
        malmquist_correction=1.0,
        selection_function='Flux-limited radio continuum',
    ),
}


def get_survey_nuisance(name: str) -> SurveyNuisance:
    """Look up a survey's nuisance specification."""
    if name not in SURVEY_REGISTRY:
        raise KeyError(f"Unknown survey: {name}. "
                       f"Available: {list(SURVEY_REGISTRY.keys())}")
    return SURVEY_REGISTRY[name]


def combined_covariance(survey_names: List[str] = None) -> np.ndarray:
    """Build the combined covariance matrix across surveys.

    Returns a diagonal covariance matrix for the survey β measurements.
    Off-diagonal terms from shared calibration are set to zero for now
    (conservative: overly broad, not overly narrow).

    Parameters
    ----------
    survey_names : list of str, optional
        Surveys to include. Default: all registered surveys.

    Returns
    -------
    cov : ndarray, shape (n_surveys, n_surveys)
        Combined covariance matrix.
    """
    if survey_names is None:
        survey_names = list(SURVEY_REGISTRY.keys())

    n = len(survey_names)
    cov = np.zeros((n, n))
    for i, name in enumerate(survey_names):
        s = SURVEY_REGISTRY[name].covariance
        cov[i, i] = s.sigma_total**2

    return cov


def nuisance_marginal_correction(beta_hat: float,
                                 survey_name: str) -> Tuple[float, float]:
    """Apply nuisance marginalization correction to a β estimate.

    Returns the corrected β and its enlarged uncertainty.
    The nuisance offset δ_survey is marginalized over its Gaussian prior.

    Parameters
    ----------
    beta_hat : float
        Raw β estimate from the survey.
    survey_name : str
        Survey name.

    Returns
    -------
    beta_corrected : float
        Same as beta_hat (marginalization doesn't shift the mean for symmetric priors).
    sigma_enlarged : float
        Enlarged uncertainty including nuisance marginalization.
    """
    s = get_survey_nuisance(survey_name)
    sigma_data = s.covariance.sigma_total
    sigma_prior = s.prior_width
    # Marginalization over δ adds prior width in quadrature
    sigma_enlarged = np.sqrt(sigma_data**2 + sigma_prior**2)
    return beta_hat, sigma_enlarged


def survey_compatibility_test(beta_values: Dict[str, float],
                              sigma_values: Dict[str, float] = None,
                              ) -> dict:
    """Test compatibility of β measurements across surveys.

    Computes a χ² statistic for the hypothesis that all surveys
    measure the same β, accounting for survey-specific uncertainties.

    Parameters
    ----------
    beta_values : dict
        {survey_name: β_estimate}
    sigma_values : dict, optional
        {survey_name: σ_β}. If None, uses registry values.

    Returns
    -------
    dict with chi2, dof, p_value, compatible (bool).
    """
    from scipy.stats import chi2 as chi2_dist

    names = list(beta_values.keys())
    betas = np.array([beta_values[n] for n in names])

    if sigma_values is None:
        sigmas = np.array([SURVEY_REGISTRY[n].covariance.sigma_total
                           for n in names])
    else:
        sigmas = np.array([sigma_values[n] for n in names])

    # Inverse-variance weighted mean
    w = 1.0 / sigmas**2
    beta_mean = np.sum(w * betas) / np.sum(w)

    # χ²
    chi2_val = float(np.sum(w * (betas - beta_mean)**2))
    dof = len(names) - 1
    p_value = float(chi2_dist.sf(chi2_val, dof)) if dof > 0 else 1.0

    return {
        'chi2': chi2_val,
        'dof': dof,
        'p_value': p_value,
        'beta_mean': float(beta_mean),
        'compatible': p_value > 0.05,
        'surveys': names,
    }
