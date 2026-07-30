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
    GFMatchedNullForecastReport,
    MatchedNullCompetitionReport,
    NullCompetitionHook,
    NullCompetitionResult,
    build_gf_matched_null_forecast_report,
    build_matched_null_competition_report,
    build_null_competition_hook,
)
from htt.infer.prior_sweep import (
    InferenceAdequacyReport,
    PriorSweepReport,
    build_inference_adequacy_report,
    build_prior_sweep_report,
)
from htt.infer.posterior_predictive import (
    PosteriorPredictiveReport,
    build_posterior_predictive_report,
)
from htt.infer.posterior_exceedance import posterior_exceedance_summary
from htt.infer.conditional_exceedance import (
    ConditionalExceedanceProfile,
    ConditioningSource,
    EnvelopeCertificate,
    EnvelopeCertificateReport,
    ExceedanceLane,
    ExceedanceStatus,
    LikelihoodObjective,
    PosteriorCalibrationReport,
    PosteriorCalibrationStatus,
    PosteriorExceedance,
    SamplingDraws,
    SamplingLaw,
    SamplingLawSpec,
    build_conditional_exceedance_envelope,
    build_envelope_certificate_report,
    build_likelihood_objective,
    build_missing_probability_law_profile,
    build_posterior_calibration_report,
    build_posterior_exceedance,
    build_sampling_draws,
    build_sampling_law_spec,
    identified_vertex_id,
)
from htt.infer.depth_path import (
    DepthHypothesisClass,
    DepthLikelihoodResult,
    DepthModelPrediction,
    build_depth_model_prediction,
    evaluate_depth_path_likelihood,
)
from htt.infer.anisotropy_type_report import (
    LocalGlobalCompatibilityInput,
    build_local_global_compatibility_input,
)
from htt.infer.finite_mock import zero_trigger_upper_bound
from htt.infer.nuisance_rank import (
    NuisanceProjectedRankAudit,
    nuisance_projected_rank,
)
from htt.infer.fisher_compression import (
    FisherCompressionAudit,
    gaussian_covariance_fisher_full_and_diag,
)
from htt.infer.loocv import LoocvReport, build_loocv_report
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
    build_discrimination_matrix,
    build_discrimination_matrix_stub,
    default_response_library,
    next_observable_recommendation,
    whitened_inner_product,
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
    'NullCompetitionResult', 'MatchedNullCompetitionReport',
    'GFMatchedNullForecastReport',
    'build_gf_matched_null_forecast_report',
    'build_matched_null_competition_report', 'build_null_competition_hook',
    'zero_trigger_upper_bound', 'NuisanceProjectedRankAudit',
    'nuisance_projected_rank', 'FisherCompressionAudit',
    'gaussian_covariance_fisher_full_and_diag',
    'PriorSweepReport', 'InferenceAdequacyReport',
    'build_prior_sweep_report', 'build_inference_adequacy_report',
    'PosteriorPredictiveReport', 'build_posterior_predictive_report',
    'posterior_exceedance_summary',
    'ConditionalExceedanceProfile', 'ConditioningSource',
    'DepthHypothesisClass', 'DepthLikelihoodResult', 'DepthModelPrediction',
    'LocalGlobalCompatibilityInput',
    'EnvelopeCertificate', 'ExceedanceLane', 'ExceedanceStatus',
    'EnvelopeCertificateReport',
    'LikelihoodObjective', 'PosteriorCalibrationReport',
    'PosteriorCalibrationStatus', 'PosteriorExceedance',
    'SamplingDraws', 'SamplingLaw', 'SamplingLawSpec',
    'build_conditional_exceedance_envelope',
    'build_local_global_compatibility_input',
    'build_depth_model_prediction', 'evaluate_depth_path_likelihood',
    'build_envelope_certificate_report',
    'build_likelihood_objective',
    'build_missing_probability_law_profile',
    'build_posterior_calibration_report', 'build_posterior_exceedance',
    'build_sampling_draws', 'build_sampling_law_spec',
    'identified_vertex_id',
    'LoocvReport', 'build_loocv_report',
    'BridgeResult', 'tilt_velocity', 'delta_q', 'lambda_J_pec', 'delta_H',
    'AxisGateDecision', 'build_diagnostic_axis', 'evaluate_axis_gate',
    'require_production_axis', 'DirectionalLikelihoodInput',
    'LikelihoodScopeDecision', 'build_directional_likelihood_input',
    'evaluate_likelihood_scope', 'guard_tsc_posterior_correction',
    'reject_mio_certificate_merge', 'HypothesisResponseTemplate',
    'build_discrimination_matrix', 'build_discrimination_matrix_stub',
    'default_response_library', 'next_observable_recommendation',
    'whitened_inner_product',
    'DirectionalHypothesisSpec', 'DirectionalResponseLibrary',
    'DirectionalInferencePolicy', 'DirectionalEvidenceHooks',
    'ProductionAxisGateResult', 'DirectionalLikelihoodInputs',
    'DirectionalReadiness',
    'DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY',
    'assess_directional_readiness', 'build_directional_output_manifest',
    'evaluate_production_axis_gate', 'build_directional_likelihood_inputs',
]
