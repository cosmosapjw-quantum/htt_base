"""HTT core subpackage.

The active package exports dependency-light constants, typed anchors/stress,
weighted summaries, and configuration.  Older monolithic modules remain
importable by their explicit paths for historical reproduction only:

Legacy modules include:
  ssot                  : Single Source of Truth (constants, conversions)
  bounds                : now the active typed MES-anchor/stress facade
  evidence_models       : 15 Bianchi evidence models
  evidence_models_R03a  : R03a revision with inactive-parameter audit
  teff_extended         : historical nonlinear T_eff corrections
  tilted_flrw           : Tilted FLRW kinematics
  analysis_extended     : historical scalar ratio/scenario outputs
  departure_posteriors  : historical x/Q/Pi posterior projections
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

# Typed statistical-foundation surface.  Historical float bounds are available
# only from tsc_legacy.htt_core_bounds and are intentionally not re-exported.
from htt.core.bounds import (
    AnchorAuthorityKind,
    AnchorConditioning,
    AnchorStatus,
    AnchorStressReport,
    MESAnchorSpec,
    ScalarRange,
    SectorStress,
    StressStatus,
    evaluate_sector_stress,
    quarantined_shear_anchors,
    registered_geodesic_mes_anchors,
)

# Dependency-light summaries.  Importing the active core package must not
# activate the historical scalar-projection posterior engine.
from htt.core.weighted_statistics import weighted_hpd, weighted_quantile

# Configuration
from htt.core.pipeline_config import PipelineConfig

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id

__all__ = [
    'C', 'load_obs', 'eps_ell', 'D_ell_from_eps', 'sigma_H_from_Sig2',
    'AnchorAuthorityKind', 'AnchorConditioning', 'AnchorStatus',
    'AnchorStressReport', 'MESAnchorSpec', 'ScalarRange', 'SectorStress',
    'StressStatus', 'evaluate_sector_stress', 'quarantined_shear_anchors',
    'registered_geodesic_mes_anchors',
    'weighted_hpd', 'weighted_quantile',
    'PipelineConfig',
]
