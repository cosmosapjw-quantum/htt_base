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
    MatchedComplexityHook,
    MatchedComplexityReport,
    build_matched_complexity_hook,
    enforce_matched_complexity,
    matched_complexity_report_artifact,
)
from htt.infer.null_competition import (
    NullCompetitionHook,
    NullCompetitionResult,
    build_null_competition_hook,
)
from htt.infer.estimators import BridgeResult, tilt_velocity, delta_q, lambda_J_pec, delta_H
from htt.infer.axis_gate import (
    AxisGateDecision,
    build_diagnostic_axis,
    evaluate_axis_gate,
    require_production_axis,
)
from htt.infer.likelihood_scope_guard import (
    DirectionalLikelihoodInput,
    LikelihoodScopeDecision,
    build_directional_likelihood_input,
    evaluate_likelihood_scope,
    guard_tsc_posterior_correction,
    reject_mio_certificate_merge,
)
from htt.infer.local_global_discrimination import (
    HypothesisResponseTemplate,
    build_discrimination_matrix_stub,
    default_response_library,
    next_observable_recommendation,
)
from htt.infer.ver2_directional_shell import (
    DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY,
    DirectionalEvidenceHooks,
    DirectionalHypothesisSpec,
    DirectionalInferencePolicy,
    DirectionalLikelihoodInputs,
    DirectionalReadiness,
    DirectionalResponseLibrary,
    assess_directional_readiness,
    build_directional_output_manifest,
    ProductionAxisGateResult,
    build_directional_likelihood_inputs,
    evaluate_production_axis_gate,
)

__all__ = [
    'LatentAxisModel', 'LatentAxisParams', 'dipole_projection',
    'DipoleVectorLikelihood',
    'SharedCauseResult', 'run_shared_cause_test',
    'ControlSpec', 'get_control', 'CONTROLS',
    'MatchedComplexityReport', 'MatchedComplexityHook',
    'enforce_matched_complexity', 'build_matched_complexity_hook',
    'matched_complexity_report_artifact', 'NullCompetitionHook',
    'NullCompetitionResult', 'build_null_competition_hook',
    'BridgeResult', 'tilt_velocity', 'delta_q', 'lambda_J_pec', 'delta_H',
    'AxisGateDecision', 'build_diagnostic_axis', 'evaluate_axis_gate',
    'require_production_axis', 'DirectionalLikelihoodInput',
    'LikelihoodScopeDecision', 'build_directional_likelihood_input',
    'evaluate_likelihood_scope', 'guard_tsc_posterior_correction',
    'reject_mio_certificate_merge', 'HypothesisResponseTemplate',
    'build_discrimination_matrix_stub', 'default_response_library',
    'next_observable_recommendation',
    'DirectionalHypothesisSpec', 'DirectionalResponseLibrary',
    'DirectionalInferencePolicy', 'DirectionalEvidenceHooks',
    'ProductionAxisGateResult', 'DirectionalLikelihoodInputs',
    'DirectionalReadiness',
    'DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY',
    'assess_directional_readiness', 'build_directional_output_manifest',
    'evaluate_production_axis_gate', 'build_directional_likelihood_inputs',
]
