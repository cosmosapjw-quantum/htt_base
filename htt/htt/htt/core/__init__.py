"""HTT core subpackage -- legacy inference modules.

13 modules ported from the monolithic HTT pipeline:
  ssot                  : Single Source of Truth (constants, conversions)
  bounds                : MES algebraic bounds (B_sigma, B_omega, B_accel)
  evidence_models       : 15 Bianchi evidence models
  evidence_models_R03a  : R03a revision with inactive-parameter audit
  teff_extended         : Nonlinear T_eff corrections
  tilted_flrw           : Tilted FLRW kinematics
  analysis_extended     : Filling fraction, scenarios, forecasts
  departure_posteriors  : Departure posterior computation (x, Q, Pi)
  catalog_likelihood    : Catalog-level likelihood
  h0_sensitivity        : H0 sensitivity analysis
  pipeline              : Master pipeline runner (SCRIPT — not importable)
  pipeline_config       : Extracted PipelineConfig (importable)
  plot_style            : Figure styling

Note: pipeline.py is a monolithic runner script (800+ lines).
It cannot be safely imported as a library module. Use
pipeline_config.py for configuration access.
"""

# Core constants and conversions
from htt.core.ssot import C, load_obs, eps_ell, D_ell_from_eps, sigma_H_from_Sig2

# Bounds
from htt.core.bounds import (
    B_sigma, B_omega, B_accel, B_sigma_corrected,
    Sig2_max_MES,
)

# Departure posteriors
from htt.core.departure_posteriors import weighted_hpd, weighted_quantile

# Configuration
from htt.core.pipeline_config import PipelineConfig

__all__ = [
    'C', 'load_obs', 'eps_ell', 'D_ell_from_eps', 'sigma_H_from_Sig2',
    'B_sigma', 'B_omega', 'B_accel', 'B_sigma_corrected', 'Sig2_max_MES',
    'weighted_hpd', 'weighted_quantile',
    'PipelineConfig',
]
