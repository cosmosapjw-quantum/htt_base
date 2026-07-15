"""
htt/infer/survey_nuisance.py — Survey-Specific Nuisance Layer
================================================================
Milestone M2.3 deliverable. Dedicated module for per-survey systematic
error budgets, covariance matrices, and nuisance marginalization.

Each active non-CF4 survey contributing to the diagnostic carries
its own systematic error profile:

  - Cosmic Waves (CW): SNIa standardization residuals, host-galaxy
    correlations, selection effects.
  - Radio catalogs: beam systematics, RFI, catalog incompleteness.

The former CF4 nuisance entry is quarantined with channel c and is available
only in the exact historical source under ``legacy/cf4_p0``.  Active calls
that name CF4 fail before accepting a numerical payload.

The nuisance layer provides:
  1. Per-survey covariance matrices (diagonal + off-diagonal systematics).
  2. Nuisance parameter priors for marginalization.
  3. Survey-combination weights accounting for systematic budgets.
  4. Compatibility checks between surveys.
"""
import hashlib
import json
import platform
import numpy as np
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Tuple

from htt.core.cf4_observational_input import (
    OPEN_FINDING_IDS,
    require_cf4_observational_input,
)

__all__ = [
    'SurveyNuisance', 'SurveyCovariance', 'SURVEY_REGISTRY',
    'get_survey_nuisance', 'combined_covariance',
    'nuisance_marginal_correction', 'survey_compatibility_test',
    'survey_nuisance_report_artifact',
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
    delta_name: str             # nuisance parameter name (e.g. 'delta_CW')
    prior_width: float          # Gaussian prior width on the nuisance offset
    direction_systematic: float # systematic in direction (degrees)
    malmquist_correction: float # Malmquist bias correction factor
    selection_function: str     # description of selection


# ── Survey Registry ──────────────────────────────────────

_CW_COV = SurveyCovariance(
    name='CW', sigma_stat=0.35e-3, sigma_sys=0.03e-3,
    sigma_calibration=0.12e-3, n_objects=1200,
)
_RADIO_COV = SurveyCovariance(
    name='Radio', sigma_stat=0.50e-3, sigma_sys=0.08e-3,
    sigma_calibration=0.15e-3, n_objects=500,
)

SURVEY_REGISTRY: Dict[str, SurveyNuisance] = {
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


def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy-heavy structures to JSON-native values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Mapping):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    return obj


def _config_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash for report configuration payloads."""
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def get_survey_nuisance(name: str) -> SurveyNuisance:
    """Look up a survey's nuisance specification."""
    if name == 'CF4':
        require_cf4_observational_input(
            consumer='survey_nuisance.get_survey_nuisance',
        )
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

    for name in survey_names:
        if name == 'CF4':
            require_cf4_observational_input(
                consumer='survey_nuisance.combined_covariance',
            )
        if name not in SURVEY_REGISTRY:
            raise KeyError(
                f"Unknown survey: {name}. Available: {list(SURVEY_REGISTRY)}"
            )

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
    supplied_names = set(names)
    if sigma_values is not None:
        supplied_names.update(sigma_values)
    if 'CF4' in supplied_names:
        require_cf4_observational_input(
            consumer='survey_nuisance.survey_compatibility_test',
        )
    unknown = sorted(supplied_names.difference(SURVEY_REGISTRY))
    if unknown:
        raise KeyError(
            f"Unknown survey(s): {unknown}. Available: {list(SURVEY_REGISTRY)}"
        )
    if not names:
        raise ValueError('at least one active non-CF4 survey is required')
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


def survey_nuisance_report_artifact(
    beta_values: Dict[str, float],
    sigma_values: Dict[str, float] | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``survey_nuisance_report_v1.json`` for the active survey set.

    The current nuisance layer is intentionally conservative: it exposes
    only diagonal covariance terms and carries that limitation explicitly
    in the artifact so downstream consumers cannot mistake it for a full
    cross-survey calibration model.
    """
    surveys = list(beta_values)
    compatibility = survey_compatibility_test(beta_values, sigma_values=sigma_values)
    covariance = combined_covariance(surveys)
    marginalised = {
        survey: {
            'beta_raw': float(beta_values[survey]),
            'beta_corrected': float(nuisance_marginal_correction(beta_values[survey], survey)[0]),
            'sigma_marginalised': float(nuisance_marginal_correction(beta_values[survey], survey)[1]),
        }
        for survey in surveys
    }
    registry_snapshot = {
        survey: {
            'delta_name': SURVEY_REGISTRY[survey].delta_name,
            'prior_width': float(SURVEY_REGISTRY[survey].prior_width),
            'direction_systematic_deg': float(SURVEY_REGISTRY[survey].direction_systematic),
            'malmquist_correction': float(SURVEY_REGISTRY[survey].malmquist_correction),
            'selection_function': SURVEY_REGISTRY[survey].selection_function,
            'covariance': {
                'sigma_stat': float(SURVEY_REGISTRY[survey].covariance.sigma_stat),
                'sigma_sys': float(SURVEY_REGISTRY[survey].covariance.sigma_sys),
                'sigma_calibration': float(SURVEY_REGISTRY[survey].covariance.sigma_calibration),
                'n_objects': int(SURVEY_REGISTRY[survey].covariance.n_objects),
                'sigma_total': float(SURVEY_REGISTRY[survey].covariance.sigma_total),
            },
        }
        for survey in surveys
    }

    extra = dict(metadata or {})
    config_payload = {
        'beta_values': beta_values,
        'sigma_values': sigma_values,
        'metadata': extra,
    }
    return _jsonify({
        'artifact_name': 'survey_nuisance_report_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.infer.survey_nuisance.survey_nuisance_report_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'owner': 'HTT',
        'implementation_scope': 'non_cf4_survey_nuisance_diagnostic',
        'claim_tier': extra.get('claim_tier', 'diagnostic_only'),
        'scope_label': extra.get('scope_label', 'non_cf4_diagnostic'),
        'production_allowed': False,
        'excluded_channels': ['c'],
        'cf4_channel_status': 'QUARANTINED_OPEN_FINDINGS',
        'cf4_finding_ids': list(OPEN_FINDING_IDS),
        'off_diagonal_policy': 'diagonal_only_conservative',
        'known_limitations': [
            'shared calibration off-diagonal covariance terms are not modelled',
            'direction systematics are represented as scalar survey-level budgets',
        ],
        'surveys': surveys,
        'compatibility': compatibility,
        'covariance_matrix': covariance,
        'registry': registry_snapshot,
        'marginalised_estimates': marginalised,
    })
