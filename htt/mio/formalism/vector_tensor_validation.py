"""MIO diagnostic-only view of the PR-272 validation contracts.

Likelihood, posterior, evidence, SBC, and HTT model-comparison builders are
intentionally absent from this module.
"""

from common.vector_tensor_statistical_inference import (
    MioDepthDiagnosticCrossCheck,
    PillarSInferenceError,
    ValidationStatus,
    build_mio_depth_cross_check,
)

__all__ = [
    "MioDepthDiagnosticCrossCheck",
    "PillarSInferenceError",
    "ValidationStatus",
    "build_mio_depth_cross_check",
]
