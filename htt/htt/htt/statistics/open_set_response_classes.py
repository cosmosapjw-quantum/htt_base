"""HTT public surface for COMMON-owned open-set response diagnostics.

The response quotient and classification types remain COMMON contracts.
HTT may consume their synthetic decisions, but this module does not create a
family likelihood, posterior, or native-solver response.
"""

import hashlib
import json
from collections.abc import Sequence

from common.anchor_geometry import NormalizerSpec
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
    _nuisance_contract,
    classify_open_set_response,
    classify_open_set_response_batch,
    evaluate_open_set_benchmark,
    source_separation_not_applicable,
)
from common.anchored_response_geometry import AnchoredResponseStatus
from common.source_separation import (
    WeakIdentificationThresholdContract,
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)
from htt.departure.velocity_frame_decomposition import (
    SourceResponseGeometryReport,
    VelocityFrameError,
    revalidate_source_response_geometry,
)


PR283_DEFAULT_THRESHOLD_CONTRACT = build_weak_identification_threshold_contract(
    minimum_principal_angle_radians=0.2,
    minimum_normalizer_bound_relative_joint_singular_value=0.01,
    parameter_coordinate_units="dimensionless_beta_c_equals_1",
)


def source_separation_gate_from_pr256(
    report: SourceResponseGeometryReport,
    *,
    classes: Sequence[ResponseClassManifoldSpec],
    covariance: object,
    nuisance_tangent: object | None,
    normalizer: NormalizerSpec,
    threshold_contract: WeakIdentificationThresholdContract,
) -> SourceSeparationGate:
    """Project one exact and target-congruent PR-256 report into the gate."""

    if type(report) is not SourceResponseGeometryReport:
        raise OpenSetResponseError(
            "report must be a factory-derived SourceResponseGeometryReport"
        )
    if type(normalizer) is not NormalizerSpec:
        raise OpenSetResponseError("normalizer must be an exact NormalizerSpec")
    try:
        report = revalidate_source_response_geometry(
            report,
            normalizer=normalizer,
        )
    except VelocityFrameError as exc:
        raise OpenSetResponseError(
            "PR-256 source geometry report failed exact replay"
        ) from exc
    if type(threshold_contract) is not WeakIdentificationThresholdContract:
        raise OpenSetResponseError(
            "threshold_contract must be a factory-derived PR-283 contract"
        )
    encoded = json.dumps(
        report.as_payload(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    report_id = f"sha256:{hashlib.sha256(encoded).hexdigest()}"
    if (
        report.separation_threshold_radians
        != threshold_contract.minimum_principal_angle_radians
    ):
        raise OpenSetResponseError(
            "PR-283 angle threshold differs from the PR-256 measurement threshold"
        )
    _, nuisance_tangent_id = _nuisance_contract(
        nuisance_tangent,
        dimension=len(report.observable_labels),
        field="nuisance_tangent",
    )
    provider_available = report.status.value != "MISSING_RESPONSE_PROVIDER"
    covariance_supported = bool(
        report.common_geometry is not None
        and report.common_geometry.status is AnchoredResponseStatus.MEASURED
    )
    decision = evaluate_source_separation(
        source_geometry_report_id=report_id,
        covariance_id=report.covariance_id,
        nuisance_tangent_id=nuisance_tangent_id,
        normalizer_id=report.normalizer_id,
        normalizer_source_identity=report.normalizer_source_identity,
        normalizer_coordinate_map_id=report.normalizer_coordinate_map_id,
        parameter_coordinate_units=report.parameter_coordinate_units,
        provider_available=provider_available,
        covariance_supported=covariance_supported,
        local_parameter_count=len(report.local_parameter_labels),
        global_parameter_count=len(report.global_parameter_labels),
        local_rank=report.local_rank,
        global_rank=report.global_rank,
        joint_rank=report.joint_rank,
        principal_angles_radians=report.principal_angles_radians,
        joint_singular_values=report.joint_singular_values,
        threshold_contract=threshold_contract,
    )
    status = SourceSeparationGateStatus(decision.status.value)
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
        source_normalizer_coordinate_map_id=report.normalizer_coordinate_map_id,
        source_parameter_coordinate_units=report.parameter_coordinate_units,
        source_separation_decision=decision,
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
    "WeakIdentificationThresholdContract",
    "build_future_native_response_adapter",
    "build_reopening_observable_spec",
    "build_response_class_manifold",
    "build_response_equivalence_report",
    "build_weak_identification_threshold_contract",
    "classify_open_set_response",
    "classify_open_set_response_batch",
    "evaluate_open_set_benchmark",
    "source_separation_gate_from_pr256",
    "source_separation_not_applicable",
    "PR283_DEFAULT_THRESHOLD_CONTRACT",
]
