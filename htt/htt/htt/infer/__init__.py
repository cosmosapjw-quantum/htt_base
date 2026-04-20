"""HTT infer subpackage -- Stage 2 inference engine.

Modules
-------
latent_axis              : Shared latent dipole direction + amplitude
dipole_vector_likelihood : L_dir(D_lowz, D_CMB_lowl | theta, phi, psi)
shared_cause             : Shared-cause vs structured-null competition
control_registry         : C0-C3 control models
matched_complexity       : Parameter-count + prior-width enforcement
estimators               : Bridge estimators (velocity-depth, delta_H, delta_q, Jeans)
"""

from htt.infer.latent_axis import LatentAxisModel, LatentAxisParams, dipole_projection
from htt.infer.dipole_vector_likelihood import DipoleVectorLikelihood
from htt.infer.shared_cause import SharedCauseResult, run_shared_cause_test
from htt.infer.control_registry import ControlSpec, get_control, CONTROLS
from htt.infer.matched_complexity import (
    MatchedComplexityReport,
    enforce_matched_complexity,
    matched_complexity_report_artifact,
)
from htt.infer.estimators import BridgeResult, tilt_velocity, delta_q, lambda_J_pec, delta_H

__all__ = [
    'LatentAxisModel', 'LatentAxisParams', 'dipole_projection',
    'DipoleVectorLikelihood',
    'SharedCauseResult', 'run_shared_cause_test',
    'ControlSpec', 'get_control', 'CONTROLS',
    'MatchedComplexityReport', 'enforce_matched_complexity',
    'matched_complexity_report_artifact',
    'BridgeResult', 'tilt_velocity', 'delta_q', 'lambda_J_pec', 'delta_H',
]
