"""HTT public surface for COMMON-owned open-set response diagnostics.

The response quotient and classification types remain COMMON contracts.
HTT may consume their synthetic decisions, but this module does not create a
family likelihood, posterior, or native-solver response.
"""

import hashlib
import json
from collections.abc import Sequence

from common.open_set_response_classes import (
    FiniteSupportPerturbationKind,
    FutureNativeResponseAdapterSpec,
    OpenSetBenchmarkReport,
    OpenSetBenchmarkStatus,
    OpenSetClassificationReport,
    OpenSetClassificationStatus,
    OpenSetResponseError,
    PR258_MAXIMUM_MCSE,
    PR258_MAXIMUM_MC_REPLICATES,
    PR258_MINIMUM_MC_REPLICATES,
    ReopeningObservableStatus,
    ReopeningObservableSpec,
    ResponseClassSourceSemantics,
    ResponseClassManifoldSpec,
    ResponseEquivalenceClassReport,
    ResponseEquivalenceStatus,
    ResponseSupportKind,
    SourceSeparationGate,
    SourceSeparationGateStatus,
    build_future_native_response_adapter,
    build_reopening_observable_spec,
    build_response_class_manifold,
    build_response_equivalence_report,
    _build_source_separation_gate,
    classify_open_set_response,
    classify_open_set_response_batch,
    evaluate_open_set_benchmark,
    source_separation_not_applicable,
)
from htt.departure.velocity_frame_decomposition import (
    SourceResponseGeometryReport,
)


def source_separation_gate_from_pr256(
    report: SourceResponseGeometryReport,
    *,
    classes: Sequence[ResponseClassManifoldSpec],
    covariance: object,
    nuisance_tangent: object | None,
) -> SourceSeparationGate:
    """Project one exact and target-congruent PR-256 report into the gate."""

    if type(report) is not SourceResponseGeometryReport:
        raise OpenSetResponseError(
            "report must be a factory-derived SourceResponseGeometryReport"
        )
    encoded = json.dumps(
        report.as_payload(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    report_id = f"sha256:{hashlib.sha256(encoded).hexdigest()}"
    status = SourceSeparationGateStatus(report.status.value)
    return _build_source_separation_gate(
        status=status,
        report_id=report_id,
        classes=classes,
        covariance=covariance,
        nuisance_tangent=nuisance_tangent,
        source_observable_labels=report.observable_labels,
        source_covariance=report.covariance_replay_matrix,
        source_covariance_id=report.covariance_id,
        source_nuisance_tangent=report.nuisance_replay_matrix,
        source_provider_ids=(
            (
                ResponseClassSourceSemantics.LOCAL_BOOST.value,
                report.local_provider.provider_id,
            ),
            (
                ResponseClassSourceSemantics.GLOBAL_TILT.value,
                report.global_provider.provider_id,
            ),
        ),
        source_response_ids=(
            (
                ResponseClassSourceSemantics.LOCAL_BOOST.value,
                report.local_provider.response_id,
            ),
            (
                ResponseClassSourceSemantics.GLOBAL_TILT.value,
                report.global_provider.response_id,
            ),
        ),
        source_transfer_contracts=(
            (
                ResponseClassSourceSemantics.LOCAL_BOOST.value,
                report.local_provider.transfer_id,
                report.local_provider.transfer_source.value,
            ),
            (
                ResponseClassSourceSemantics.GLOBAL_TILT.value,
                report.global_provider.transfer_id,
                report.global_provider.transfer_source.value,
            ),
        ),
        source_frame_contracts=(
            (
                ResponseClassSourceSemantics.LOCAL_BOOST.value,
                report.local_provider.basis,
                report.local_provider.epoch_window,
                report.local_provider.perturbative_order,
            ),
            (
                ResponseClassSourceSemantics.GLOBAL_TILT.value,
                report.global_provider.basis,
                report.global_provider.epoch_window,
                report.global_provider.perturbative_order,
            ),
        ),
        source_mask_id=report.mask_id,
        source_normalizer_id=report.normalizer_id,
        source_normalizer_identity=report.normalizer_source_identity,
    )

__all__ = [
    "FiniteSupportPerturbationKind",
    "FutureNativeResponseAdapterSpec",
    "OpenSetBenchmarkReport",
    "OpenSetBenchmarkStatus",
    "OpenSetClassificationReport",
    "OpenSetClassificationStatus",
    "OpenSetResponseError",
    "PR258_MAXIMUM_MCSE",
    "PR258_MAXIMUM_MC_REPLICATES",
    "PR258_MINIMUM_MC_REPLICATES",
    "ReopeningObservableStatus",
    "ReopeningObservableSpec",
    "ResponseClassSourceSemantics",
    "ResponseClassManifoldSpec",
    "ResponseEquivalenceClassReport",
    "ResponseEquivalenceStatus",
    "ResponseSupportKind",
    "SourceSeparationGate",
    "SourceSeparationGateStatus",
    "build_future_native_response_adapter",
    "build_reopening_observable_spec",
    "build_response_class_manifold",
    "build_response_equivalence_report",
    "classify_open_set_response",
    "classify_open_set_response_batch",
    "evaluate_open_set_benchmark",
    "source_separation_gate_from_pr256",
    "source_separation_not_applicable",
]
