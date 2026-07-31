"""OBSSTAT-owned facade for repository-bound vector/tensor data preflight."""

from common.vector_tensor_data_admission import (
    AdmissionVerdict,
    ComponentBindingStatus,
    DataAdmissionDecision,
    DataAdmissionError,
    DataAdmissionReport,
    IdentityStatus,
    NO_ADMITTED_DATA_PILOT,
    PilotAuthorizationStatus,
    RepositoryComponentBinding,
    VectorTensorDataCandidate,
    build_data_admission_report,
    candidate_from_mapping,
    candidates_from_registry,
    evaluate_data_candidate,
)

__all__ = [
    "AdmissionVerdict",
    "ComponentBindingStatus",
    "DataAdmissionDecision",
    "DataAdmissionError",
    "DataAdmissionReport",
    "IdentityStatus",
    "NO_ADMITTED_DATA_PILOT",
    "PilotAuthorizationStatus",
    "RepositoryComponentBinding",
    "VectorTensorDataCandidate",
    "build_data_admission_report",
    "candidate_from_mapping",
    "candidates_from_registry",
    "evaluate_data_candidate",
]
