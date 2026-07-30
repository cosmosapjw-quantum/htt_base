from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from common.anchor_geometry import (
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import anchored_numeric_content_id
from common.open_set_response_classes import (
    FiniteSupportPerturbationKind,
    FutureNativeResponseAdapterSpec,
    OpenSetBenchmarkStatus,
    OpenSetClassificationStatus,
    OpenSetResponseError,
    ReopeningObservableStatus,
    PR258_ARTIFACT_MODE,
    PR258_ARTIFACT_OWNER,
    PR258_ARTIFACT_SCOPE,
    PR258_COVARIANCE_STATUS,
    PR258_MAXIMUM_MC_REPLICATES,
    PR258_NULL_MOCK_STATUS,
    PR258_SKY_SUPPORT_STATUS,
    ResponseClassSourceSemantics,
    ResponseEquivalenceStatus,
    ResponseSupportKind,
    SourceSeparationGateStatus,
    build_future_native_response_adapter,
    build_reopening_observable_spec,
    build_response_class_manifold,
    build_response_equivalence_report,
    classify_open_set_response,
    classify_open_set_response_batch,
    evaluate_open_set_benchmark,
    source_separation_not_applicable,
)
from common.transfer_registry import TransferSource
from htt.departure.velocity_frame_decomposition import (
    ResponseProviderAvailability,
    ResponseProviderKind,
    SourceHypothesis,
    VelocityComponent,
    measure_source_response_geometry,
    register_source_response_provider,
)
from htt.statistics.open_set_response_classes import (
    source_separation_gate_from_pr256,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _id(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('ascii')).hexdigest()}"


def _class(
    suffix: str,
    nodes: object | None,
    *,
    kind: ResponseSupportKind = ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
    transfer_source: TransferSource | None = TransferSource.NONE,
    source_semantics=ResponseClassSourceSemantics.NEUTRAL,
    source_response_id: str | None = None,
    provider_id: str | None = None,
    observable_labels=("obs-x", "obs-y"),
    convention_id: str | None = None,
    nuisance_policy_id: str | None = None,
):
    return build_response_class_manifold(
        class_id=f"response-class-{suffix}",
        support_kind=kind,
        provider_id=(
            _id(f"provider:{suffix}") if provider_id is None else provider_id
        ),
        observable_labels=observable_labels,
        convention_id=(
            _id("convention") if convention_id is None else convention_id
        ),
        nuisance_policy_id=(
            _id("nuisance:none")
            if nuisance_policy_id is None
            else nuisance_policy_id
        ),
        support_nodes=nodes,
        transfer_source=transfer_source,
        source_semantics=source_semantics,
        source_response_id=source_response_id,
    )


def _equivalence(
    classes,
    *,
    covariance=np.eye(2),
    nuisance_tangent=None,
    tolerance=0.1,
    reopening_observables=None,
):
    return build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=nuisance_tangent,
        equivalence_squared_distance_tolerance=tolerance,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        reopening_observables=reopening_observables,
    )


def _reopening(
    classes,
    *,
    suffix="polarization",
    values=(0.0, 1.0),
    available=True,
    joint_covariance=None,
):
    if not available:
        return build_reopening_observable_spec(
            observable_id=_id(f"reopening:{suffix}"),
            classes=classes,
            added_observable_labels=(f"added-{suffix}",),
            responses_by_class_and_node=None,
            joint_covariance=None,
            joint_nuisance_response=None,
            joint_nuisance_policy_id=None,
            convention_id=_id("convention"),
        )
    responses = {}
    for item, value in zip(classes, values, strict=True):
        responses[item.class_id] = {
            node_id: [value] for node_id in item.support_node_ids
        }
    dimension = len(classes[0].observable_labels) + 1
    return build_reopening_observable_spec(
        observable_id=_id(f"reopening:{suffix}"),
        classes=classes,
        added_observable_labels=(f"added-{suffix}",),
        responses_by_class_and_node=responses,
        joint_covariance=(
            np.eye(dimension)
            if joint_covariance is None
            else joint_covariance
        ),
        joint_nuisance_response=None,
        joint_nuisance_policy_id=_id(f"joint-nuisance:{suffix}"),
        convention_id=_id("convention"),
    )


def _classify(
    observation,
    classes,
    equivalence_report,
    *,
    covariance=np.eye(2),
    nuisance_tangent=None,
    unknown_threshold=4.0,
    margin=0.5,
    null_tolerance=1.0e-10,
    source_gate=None,
):
    return classify_open_set_response(
        observation=observation,
        classes=classes,
        equivalence_report=equivalence_report,
        covariance=covariance,
        nuisance_tangent=nuisance_tangent,
        unknown_squared_distance_threshold=unknown_threshold,
        decision_squared_margin=margin,
        covariance_null_tolerance=null_tolerance,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=(
            source_separation_not_applicable()
            if source_gate is None
            else source_gate
        ),
    )


def _benchmark_class_library(
    kind: FiniteSupportPerturbationKind | None = None,
    *,
    flip_expansion: bool = False,
):
    if kind is FiniteSupportPerturbationKind.EXACT_DUPLICATE:
        left = [[-3.0, 0.0], [-2.8, 0.0], [-3.0, -0.0]]
        right = [[2.8, 0.0], [3.0, 0.0], [3.0, -0.0]]
    elif kind is FiniteSupportPerturbationKind.REFINEMENT:
        left = [[-3.0, 0.0], [-2.9, 0.0], [-2.8, 0.0]]
        right = [[2.8, 0.0], [2.9, 0.0], [3.0, 0.0]]
    elif kind is FiniteSupportPerturbationKind.EXPANSION:
        left = [[-3.2, 0.0], [-3.0, 0.0], [-2.8, 0.0]]
        right = (
            [[-3.0, 0.0], [2.8, 0.0], [3.0, 0.0]]
            if flip_expansion
            else [[2.8, 0.0], [3.0, 0.0], [3.2, 0.0]]
        )
    elif kind is FiniteSupportPerturbationKind.CONTRACTION:
        left = [[-2.8, 0.0]]
        right = [[2.8, 0.0]]
    elif kind is FiniteSupportPerturbationKind.BOUNDARY_RESTRICTION:
        left = [[-3.0, 0.0]]
        right = [[3.0, 0.0]]
    else:
        left = [[-3.0, 0.0], [-2.8, 0.0]]
        right = [[2.8, 0.0], [3.0, 0.0]]
    return (_class("left", left), _class("right", right))


def _benchmark_perturbation_inputs(
    observation,
    *,
    count: int,
    flip_expansion: bool = False,
):
    classes_by_kind = {}
    equivalence_by_kind = {}
    reports_by_kind = {}
    for kind in FiniteSupportPerturbationKind:
        classes = _benchmark_class_library(
            kind,
            flip_expansion=(
                flip_expansion
                and kind is FiniteSupportPerturbationKind.EXPANSION
            ),
        )
        equivalence = _equivalence(classes)
        decision = _classify(observation, classes, equivalence)
        classes_by_kind[kind] = classes
        equivalence_by_kind[kind] = equivalence
        reports_by_kind[kind] = (decision,) * count
    return classes_by_kind, equivalence_by_kind, reports_by_kind


def _pr256_report(
    *,
    separable: bool,
    observable_labels,
    covariance,
    local_provider_id: str,
    global_provider_id: str,
    nuisance_tangent=None,
):
    dimension = len(observable_labels)

    def provider(
        hypothesis: SourceHypothesis,
        response: object,
    ):
        local = hypothesis is SourceHypothesis.LOCAL_BOOST
        return register_source_response_provider(
            provider_id=(
                local_provider_id if local else global_provider_id
            ),
            hypothesis=hypothesis,
            velocity_component=(
                VelocityComponent.BETA_MO
                if local
                else VelocityComponent.BETA_RM
            ),
            provider_kind=ResponseProviderKind.ANALYTIC,
            availability=ResponseProviderAvailability.AVAILABLE,
            observable_labels=observable_labels,
            parameter_labels=(
                ("beta_MO_amplitude",)
                if local
                else ("beta_RM_amplitude",)
            ),
            response=response,
            transfer_id=_id("pr256-transfer-none"),
            transfer_source=TransferSource.NONE,
            basis="registered synthetic basis",
            epoch_window="registered synthetic window",
            assumptions=("first-order analytic response",),
            caveats=("hypothesis-only response",),
        )

    report = measure_source_response_geometry(
        local_provider=provider(
            SourceHypothesis.LOCAL_BOOST,
            [[1.0], *([[0.0]] * (dimension - 1))],
        ),
        global_provider=provider(
            SourceHypothesis.GLOBAL_TILT,
            (
                [[0.0], [1.0], *([[0.0]] * (dimension - 2))]
                if separable
                else [[2.0], *([[0.0]] * (dimension - 1))]
            ),
        ),
        covariance=covariance,
        normalizer=NormalizerSpec(
            normalizer_id="pr258-pr256-projection-normalizer",
            kind=NormalizerKind.MES_ANCHORED,
            purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
            coordinate_labels=(
                "beta_MO_amplitude",
                "beta_RM_amplitude",
            ),
            coordinate_map=((1.0, 0.0), (0.0, 1.0)),
            source_identity="PR258-PR256-PROJECTION-TEST",
            assumptions=("block-preserving map",),
        ),
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=_id("pr256-mask"),
        nuisance_response=nuisance_tangent,
        separation_threshold_radians=0.2,
    )
    return report


def _pr256_source_gate(
    *,
    separable: bool,
    classes,
    covariance=np.eye(2),
    nuisance_tangent=None,
):
    local = next(
        item
        for item in classes
        if item.source_semantics is ResponseClassSourceSemantics.LOCAL_BOOST
    )
    global_value = next(
        item
        for item in classes
        if item.source_semantics is ResponseClassSourceSemantics.GLOBAL_TILT
    )
    report = _pr256_report(
        separable=separable,
        observable_labels=local.observable_labels,
        covariance=covariance,
        local_provider_id=local.provider_id,
        global_provider_id=global_value.provider_id,
        nuisance_tangent=nuisance_tangent,
    )
    return report, source_separation_gate_from_pr256(
        report,
        classes=classes,
        covariance=covariance,
        nuisance_tangent=nuisance_tangent,
    )


def _source_classes(*, separable: bool):
    local_response_id = anchored_numeric_content_id(
        np.asarray([[1.0], [0.0]], dtype=np.float64)
    )
    global_response_id = anchored_numeric_content_id(
        np.asarray(
            [[0.0], [1.0]] if separable else [[2.0], [0.0]],
            dtype=np.float64,
        )
    )
    return (
        _class(
            "local",
            [[-3.0, 0.0]],
            source_semantics=ResponseClassSourceSemantics.LOCAL_BOOST,
            source_response_id=local_response_id,
        ),
        _class(
            "global",
            [[3.0, 0.0]],
            source_semantics=ResponseClassSourceSemantics.GLOBAL_TILT,
            source_response_id=global_response_id,
        ),
    )


def test_response_support_is_typed_canonical_and_duplicate_invariant() -> None:
    baseline = _class("a", [[-3.0, 0.0], [-2.0, 0.0]])
    permuted = _class(
        "a",
        [[-2.0, 0.0], [-3.0, 0.0], [-3.0, 0.0]],
    )

    assert baseline.response_content_id == permuted.response_content_id
    assert baseline.support_node_count == permuted.support_node_count == 2
    assert baseline.duplicate_node_count == 0
    assert permuted.duplicate_node_count == 1
    assert baseline.support_nodes.flags.writeable is False
    with pytest.raises(ValueError):
        baseline.support_nodes[0, 0] = 0.0


@pytest.mark.parametrize(
    "class_id",
    ["BI", "BVIIh", "family-ix", "response-class-A", ""],
)
def test_family_or_unsafe_labels_cannot_enter_response_class_namespace(
    class_id: str,
) -> None:
    with pytest.raises(OpenSetResponseError, match="response-class"):
        build_response_class_manifold(
            class_id=class_id,
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_id("provider"),
            observable_labels=("x",),
            convention_id=_id("convention"),
            nuisance_policy_id=_id("nuisance"),
            support_nodes=[[0.0]],
            transfer_source=TransferSource.NONE,
        )


@pytest.mark.parametrize(
    "nodes",
    [
        [],
        [[True, 0.0]],
        [[np.nan, 0.0]],
        [[np.inf, 0.0]],
        [[1.0]],
        [["1", 0.0]],
    ],
)
def test_malformed_response_support_fails_closed(nodes: object) -> None:
    with pytest.raises(OpenSetResponseError):
        _class("bad", nodes)


def test_finite_support_rejects_external_or_native_transfer_provenance() -> None:
    with pytest.raises(OpenSetResponseError, match="transfer_source=none"):
        _class(
            "external",
            [[0.0, 0.0]],
            transfer_source=TransferSource.EXTERNAL_TRANSFER,
        )
    with pytest.raises(OpenSetResponseError, match="transfer_source=none"):
        _class(
            "native",
            [[0.0, 0.0]],
            transfer_source=TransferSource.BASS_NATIVE_VALIDATED,
        )


def test_future_native_adapter_is_schema_only_and_needs_native() -> None:
    adapter = build_future_native_response_adapter(
        adapter_id=_id("future-native-adapter"),
        observable_labels=("T2", "T3", "E2", "B2"),
        convention_id=_id("harmonic-convention"),
    )

    assert isinstance(adapter, FutureNativeResponseAdapterSpec)
    assert adapter.status is ResponseSupportKind.NEEDS_NATIVE
    assert adapter.response_values is None
    assert (
        adapter.transfer_source_required
        is TransferSource.BASS_NATIVE_VALIDATED
    )
    assert "validation_receipt" in adapter.required_fields
    with pytest.raises(OpenSetResponseError, match="factory-derived"):
        FutureNativeResponseAdapterSpec(
            adapter_id=_id("forged"),
            status=ResponseSupportKind.NEEDS_NATIVE,
            observable_labels=("T2",),
            convention_id=_id("convention"),
        )


def test_shared_flrw_boundary_collapses_classes_and_never_forces_label() -> None:
    classes = (
        _class("left", [[0.0, 0.0], [-3.0, 0.0]]),
        _class("right", [[0.0, 0.0], [3.0, 0.0]]),
    )
    report = _equivalence(classes)

    assert report.status is ResponseEquivalenceStatus.EQUIVALENCE_CLASS
    assert report.components == (
        ("response-class-left", "response-class-right"),
    )
    classified = _classify([-3.0, 0.0], classes, report)
    assert classified.status is OpenSetClassificationStatus.EQUIVALENCE_CLASS
    assert classified.candidate_class_id is None
    assert classified.returned_equivalence_class == report.components[0]


def test_nontransitive_tolerance_graph_is_type_unidentified_not_equality() -> None:
    classes = (
        _class("a", [[0.00, 0.0]]),
        _class("b", [[0.09, 0.0]]),
        _class("c", [[0.18, 0.0]]),
    )
    report = _equivalence(classes, tolerance=0.01)

    assert report.status is ResponseEquivalenceStatus.TYPE_UNIDENTIFIED
    assert report.components == (
        ("response-class-a", "response-class-b", "response-class-c"),
    )
    assert (
        report.pairwise_minimum_squared_distances[0][2]
        > report.equivalence_squared_distance_tolerance
    )
    classified = _classify([0.0, 0.0], classes, report)
    assert classified.status is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
    assert classified.candidate_class_id is None


def test_preregistered_reopening_observable_and_missing_provider_are_distinct() -> None:
    classes = (
        _class("left", [[0.0, 0.0]]),
        _class("right", [[0.0, 0.0]]),
    )
    reopened = _equivalence(
        classes,
        reopening_observables=(_reopening(classes),),
    )
    missing = _equivalence(
        classes,
        reopening_observables=(
            _reopening(
                classes,
                suffix="remote-dipole",
                available=False,
            ),
        ),
    )

    assert reopened.reopening_status is ReopeningObservableStatus.REOPENED
    assert reopened.minimal_reopening_observable_ids == (
        _id("reopening:polarization"),
    )
    assert (
        missing.reopening_status
        is ReopeningObservableStatus.MISSING_RESPONSE_PROVIDER
    )
    assert missing.missing_reopening_provider_ids == (
        _id("reopening:remote-dipole"),
    )


def test_separated_candidate_ambiguous_and_unknown_decisions() -> None:
    classes = (
        _class("left", [[-3.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    report = _equivalence(classes)
    assert report.status is ResponseEquivalenceStatus.SEPARATED

    left = _classify([-3.0, 0.0], classes, report)
    ambiguous = _classify(
        [0.0, 0.0],
        classes,
        report,
        unknown_threshold=10.0,
    )
    unknown = _classify([0.0, 10.0], classes, report)

    assert left.status is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    assert left.candidate_class_id == "response-class-left"
    assert ambiguous.status is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
    assert ambiguous.candidate_class_id is None
    assert unknown.status is OpenSetClassificationStatus.UNKNOWN_CLASS
    assert unknown.candidate_class_id is None


def test_covariance_null_and_nuisance_directions_are_retained() -> None:
    classes = (
        _class("left", [[-3.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    singular_covariance = np.diag([1.0, 0.0])
    report = _equivalence(classes, covariance=singular_covariance)
    outside = _classify(
        [-3.0, 1.0],
        classes,
        report,
        covariance=singular_covariance,
    )

    assert outside.status is OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT
    assert outside.covariance_null_residual == 0.0
    assert outside.covariance_structural_null_mismatch is True

    nuisance = np.asarray([[1.0], [0.0]])
    nuisance_report = _equivalence(
        classes,
        nuisance_tangent=nuisance,
    )
    assert nuisance_report.supported_rank == 1
    assert (
        nuisance_report.status
        is ResponseEquivalenceStatus.EQUIVALENCE_CLASS
    )
    assert nuisance_report.pairwise_covariance_null_residuals[0][1] == pytest.approx(
        0.0
    )
    nuisance_shift = _classify(
        [100.0, 0.0],
        classes,
        nuisance_report,
        nuisance_tangent=nuisance,
    )
    assert (
        nuisance_shift.status
        is OpenSetClassificationStatus.EQUIVALENCE_CLASS
    )
    assert nuisance_shift.covariance_null_residual == 0.0
    assert nuisance_shift.covariance_structural_null_mismatch is False


def test_full_supported_nuisance_orbit_is_unidentified_not_covariance_null() -> None:
    classes = (
        build_response_class_manifold(
            class_id="response-class-left",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_id("full-nuisance:left"),
            observable_labels=("x",),
            convention_id=_id("full-nuisance:convention"),
            nuisance_policy_id=_id("full-nuisance:policy"),
            support_nodes=[[-1.0]],
        ),
        build_response_class_manifold(
            class_id="response-class-right",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_id("full-nuisance:right"),
            observable_labels=("x",),
            convention_id=_id("full-nuisance:convention"),
            nuisance_policy_id=_id("full-nuisance:policy"),
            support_nodes=[[1.0]],
        ),
    )
    report = build_response_equivalence_report(
        classes=classes,
        covariance=[[1.0]],
        nuisance_tangent=[[1.0]],
        equivalence_squared_distance_tolerance=0.0,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
    )
    classified = classify_open_set_response(
        observation=[100.0],
        classes=classes,
        equivalence_report=report,
        covariance=[[1.0]],
        nuisance_tangent=[[1.0]],
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=source_separation_not_applicable(),
    )

    assert report.supported_rank == 0
    assert report.status is ResponseEquivalenceStatus.EQUIVALENCE_CLASS
    assert classified.status is OpenSetClassificationStatus.EQUIVALENCE_CLASS
    assert classified.covariance_null_residual == 0.0


def test_squared_distance_contract_and_unit_congruence_are_explicit() -> None:
    scalar_classes = (
        build_response_class_manifold(
            class_id="response-class-a",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_id("scalar:a"),
            observable_labels=("x",),
            convention_id=_id("scalar-convention"),
            nuisance_policy_id=_id("scalar-nuisance"),
            support_nodes=[[0.0]],
        ),
        build_response_class_manifold(
            class_id="response-class-b",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_id("scalar:b"),
            observable_labels=("x",),
            convention_id=_id("scalar-convention"),
            nuisance_policy_id=_id("scalar-nuisance"),
            support_nodes=[[1.0]],
        ),
    )
    report = build_response_equivalence_report(
        classes=scalar_classes,
        covariance=[[4.0]],
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.3,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
    )
    assert report.pairwise_minimum_squared_distances[0][1] == pytest.approx(
        0.25
    )
    assert report.status is ResponseEquivalenceStatus.EQUIVALENCE_CLASS

    base_classes = (
        _class("left", [[-3.0, 1.0]]),
        _class("right", [[3.0, -1.0]]),
    )
    scaled_classes = tuple(
        build_response_class_manifold(
            class_id=item.class_id,
            support_kind=item.support_kind,
            provider_id=item.provider_id,
            observable_labels=item.observable_labels,
            convention_id=item.convention_id,
            nuisance_policy_id=item.nuisance_policy_id,
            support_nodes=[
                [2.0 * row[0], row[1]] for row in item.support_nodes
            ],
        )
        for item in base_classes
    )
    base = _equivalence(base_classes)
    scaled = _equivalence(
        scaled_classes,
        covariance=np.diag([4.0, 1.0]),
    )
    assert (
        base.pairwise_minimum_squared_distances
        == scaled.pairwise_minimum_squared_distances
    )


def test_covariance_null_residual_dominates_candidate_and_null_classes_merge() -> None:
    classes = (
        _class("a", [[0.0, 0.0]]),
        _class("b", [[0.0, 10.0]]),
    )
    covariance = np.diag([1.0, 0.0])
    report = _equivalence(classes, covariance=covariance)
    assert report.status is ResponseEquivalenceStatus.EQUIVALENCE_CLASS
    assert report.pairwise_minimum_squared_distances[0][1] == 0.0
    classified = _classify(
        [0.0, 100.0],
        classes,
        report,
        covariance=covariance,
    )
    assert (
        classified.status
        is OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT
    )
    assert classified.candidate_class_id is None
    assert classified.covariance_structural_null_mismatch is True
    assert (
        report.pairwise_covariance_structural_null_mismatches[0][1]
        is True
    )


def test_zero_variance_structural_null_is_exact_and_unit_congruent() -> None:
    statuses = []
    report_ids = []
    for scale in (1.0, 100.0):
        classes = (
            _class("left", [[-3.0, 0.0]]),
            _class("right", [[3.0, 0.0]]),
        )
        covariance = np.diag([1.0, 0.0])
        report = _equivalence(classes, covariance=covariance)
        outside = _classify(
            [-3.0, 5.0e-11 * scale],
            classes,
            report,
            covariance=covariance,
        )
        exact = _classify(
            [-3.0, 0.0],
            classes,
            report,
            covariance=covariance,
        )
        statuses.append((outside.status, exact.status))
        report_ids.append(report.report_id)
        assert outside.covariance_structural_null_mismatch is True
        assert outside.covariance_null_residual == 0.0
        assert exact.covariance_structural_null_mismatch is False
        assert exact.covariance_null_residual == 0.0

    assert statuses == [
        (
            OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT,
            OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE,
        ),
        (
            OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT,
            OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE,
        ),
    ]
    assert report_ids[0] == report_ids[1]

    correlation_null_results = []
    for scales in ((1.0, 1.0), (2.0, 5.0)):
        scaling = np.diag(scales)
        scaled_classes = tuple(
            build_response_class_manifold(
                class_id=f"response-class-{suffix}",
                support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
                provider_id=_id(f"correlation-null:{suffix}"),
                observable_labels=("obs-x", "obs-y"),
                convention_id=_id("correlation-null:convention"),
                nuisance_policy_id=_id("correlation-null:nuisance"),
                support_nodes=[
                    (scaling @ np.asarray(node, dtype=float)).tolist()
                ],
            )
            for suffix, node in (
                ("a", [0.0, 0.0]),
                ("b", [3.0, 3.0]),
            )
        )
        covariance = scaling @ np.ones((2, 2)) @ scaling
        report = _equivalence(
            scaled_classes,
            covariance=covariance,
            tolerance=0.01,
        )
        decision = _classify(
            (scaling @ np.asarray([0.5, -0.5])).tolist(),
            scaled_classes,
            report,
            covariance=covariance,
        )
        correlation_null_results.append(
            (
                decision.status,
                decision.best_squared_distance,
                decision.covariance_null_residual,
                decision.covariance_structural_null_mismatch,
            )
        )
    assert correlation_null_results[0] == correlation_null_results[1]
    assert (
        correlation_null_results[0][0]
        is OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT
    )
    assert correlation_null_results[0][1] == 0.0
    assert correlation_null_results[0][2] == pytest.approx(2.0**-0.5)
    assert correlation_null_results[0][3] is False


def test_supported_score_ties_choose_the_node_with_smallest_null_residual() -> None:
    classes = (
        _class("a", [[0.0, -10.0], [0.0, 0.0]]),
        _class("b", [[3.0, 0.0]]),
    )
    covariance = np.diag([1.0, 0.0])
    report = _equivalence(
        classes,
        covariance=covariance,
        tolerance=0.0,
    )
    classified = _classify(
        [0.0, 0.0],
        classes,
        report,
        covariance=covariance,
    )

    assert (
        classified.status
        is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    )
    assert classified.candidate_class_id == "response-class-a"
    assert classified.covariance_null_residual == 0.0


def test_classification_rejects_nuisance_geometry_rebinding() -> None:
    classes = (
        _class("left", [[-3.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    report = _equivalence(classes, nuisance_tangent=None)

    with pytest.raises(OpenSetResponseError, match="nuisance tangent"):
        _classify(
            [-3.0, 0.0],
            classes,
            report,
            nuisance_tangent=[[0.0], [1.0]],
        )


def test_classification_rejects_class_contract_rebinding_single_and_batch() -> None:
    classes = (
        _class("left", [[-3.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    report = _equivalence(classes)

    for field in ("provider_id", "convention_id", "nuisance_policy_id"):
        rebound = []
        for item in classes:
            values = {
                "provider_id": item.provider_id,
                "convention_id": item.convention_id,
                "nuisance_policy_id": item.nuisance_policy_id,
            }
            values[field] = _id(
                f"rebound:{field}:{item.class_id if field == 'provider_id' else 'shared'}"
            )
            rebound.append(
                build_response_class_manifold(
                    class_id=item.class_id,
                    support_kind=item.support_kind,
                    provider_id=values["provider_id"],
                    observable_labels=item.observable_labels,
                    convention_id=values["convention_id"],
                    nuisance_policy_id=values["nuisance_policy_id"],
                    support_nodes=item.support_nodes,
                    transfer_source=item.transfer_source,
                    source_semantics=item.source_semantics,
                )
            )
        rebound_classes = tuple(rebound)
        with pytest.raises(OpenSetResponseError, match="contract differs"):
            _classify(
                [-3.0, 0.0],
                rebound_classes,
                report,
            )
        with pytest.raises(OpenSetResponseError, match="contract differs"):
            classify_open_set_response_batch(
                observations=[[-3.0, 0.0]],
                classes=rebound_classes,
                equivalence_report=report,
                covariance=np.eye(2),
                nuisance_tangent=None,
                unknown_squared_distance_threshold=4.0,
                decision_squared_margin=0.5,
                covariance_null_tolerance=1.0e-10,
                absolute_tolerance=1.0e-12,
                relative_tolerance=1.0e-12,
                source_separation_gate=source_separation_not_applicable(),
            )


def test_node_keyed_reopening_rejects_identity_drift_and_regraphs_globally() -> None:
    classes = (
        _class("a", [[0.0, 0.0]]),
        _class("b", [[0.0, 0.0]]),
        _class("c", [[3.0, 0.0]]),
    )
    bad = {
        item.class_id: {
            node_id: [float(index)]
            for node_id in item.support_node_ids
        }
        for index, item in enumerate(classes)
    }
    bad["response-class-a"] = {_id("wrong-node"): [0.0]}
    with pytest.raises(OpenSetResponseError, match="node identities"):
        build_reopening_observable_spec(
            observable_id=_id("bad-node-alignment"),
            classes=classes,
            added_observable_labels=("added",),
            responses_by_class_and_node=bad,
            joint_covariance=np.eye(3),
            joint_nuisance_response=None,
            joint_nuisance_policy_id=_id("joint"),
            convention_id=_id("convention"),
        )

    scalar_rows = {
        item.class_id: {
            node_id: 1.0 for node_id in item.support_node_ids
        }
        for item in classes
    }
    with pytest.raises(OpenSetResponseError, match="numeric sequence"):
        build_reopening_observable_spec(
            observable_id=_id("scalar-row"),
            classes=classes,
            added_observable_labels=("added",),
            responses_by_class_and_node=scalar_rows,
            joint_covariance=np.eye(3),
            joint_nuisance_response=None,
            joint_nuisance_policy_id=_id("joint"),
            convention_id=_id("convention"),
        )

    responses = {
        classes[0].class_id: {classes[0].support_node_ids[0]: [0.0]},
        classes[1].class_id: {classes[1].support_node_ids[0]: [10.0]},
        classes[2].class_id: {classes[2].support_node_ids[0]: [0.0]},
    }
    reopening = build_reopening_observable_spec(
        observable_id=_id("full-regraph"),
        classes=classes,
        added_observable_labels=("added",),
        responses_by_class_and_node=responses,
        joint_covariance=np.eye(3),
        joint_nuisance_response=[[1.0], [0.0], [0.0]],
        joint_nuisance_policy_id=_id("joint-remove-base-x"),
        convention_id=_id("convention"),
    )
    report = _equivalence(
        classes,
        reopening_observables=(reopening,),
    )
    assert report.reopening_status is ReopeningObservableStatus.NEEDS_ADDITIONAL_OBSERVABLE
    assert len(report.reopening_joint_report_ids) == 1


def test_local_global_source_gate_dominates_finite_node_candidate() -> None:
    classes = _source_classes(separable=True)
    report = _equivalence(classes)
    with pytest.raises(OpenSetResponseError, match="PR-256"):
        _classify([-3.0, 0.0], classes, report)
    sum_only_classes = _source_classes(separable=False)
    sum_only_equivalence = _equivalence(sum_only_classes)
    sum_only_report, sum_only = _pr256_source_gate(
        separable=False,
        classes=sum_only_classes,
    )
    assert (
        sum_only_report.status.value
        == SourceSeparationGateStatus.SUM_ONLY.value
    )
    blocked = _classify(
        [-3.0, 0.0],
        sum_only_classes,
        sum_only_equivalence,
        source_gate=sum_only,
    )
    assert blocked.status is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
    assert blocked.candidate_class_id is None
    _, separable = _pr256_source_gate(
        separable=True,
        classes=classes,
    )
    candidate = _classify(
        [-3.0, 0.0],
        classes,
        report,
        source_gate=separable,
    )
    assert (
        candidate.status
        is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    )

    mixed = (
        _class("neutral", [[0.0, 0.0]]),
        _class(
            "local-only",
            [[3.0, 0.0]],
            source_semantics=ResponseClassSourceSemantics.LOCAL_BOOST,
            source_response_id=_id("source-response:local-only"),
        ),
    )
    with pytest.raises(OpenSetResponseError, match="must not be mixed"):
        _equivalence(mixed)


def test_source_gate_cannot_be_forged_from_status_and_arbitrary_receipt() -> None:
    import common.open_set_response_classes as common_surface
    import htt.statistics as htt_surface

    assert "build_source_separation_gate" not in common_surface.__all__
    assert not hasattr(common_surface, "build_source_separation_gate")
    assert not hasattr(htt_surface, "build_source_separation_gate")


def test_htt_facade_projects_an_exact_pr256_source_geometry_report() -> None:
    classes = _source_classes(separable=True)
    report, gate = _pr256_source_gate(
        separable=True,
        classes=classes,
    )

    assert gate.status is SourceSeparationGateStatus.SEPARABLE_CANDIDATE
    assert gate.report_id is not None
    assert gate.report_id.startswith("sha256:")
    assert gate.observable_labels == ("obs-x", "obs-y")
    assert gate.class_contract_ids
    assert gate.gate_id.startswith("sha256:")


def test_source_gate_binds_exact_geometry_and_provider_provenance() -> None:
    classes = _source_classes(separable=True)
    equivalence = _equivalence(classes)
    _, gate = _pr256_source_gate(
        separable=True,
        classes=classes,
    )
    single = _classify(
        [-3.0, 0.0],
        classes,
        equivalence,
        source_gate=gate,
    )
    batch = classify_open_set_response_batch(
        observations=[[-3.0, 0.0]],
        classes=classes,
        equivalence_report=equivalence,
        covariance=np.eye(2),
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=gate,
    )
    assert batch == (single,)
    assert single.status is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE

    report_3d = _pr256_report(
        separable=True,
        observable_labels=("dipole", "depth", "morphology"),
        covariance=np.eye(3),
        local_provider_id=classes[0].provider_id,
        global_provider_id=classes[1].provider_id,
    )
    for _consumer in ("single", "batch"):
        with pytest.raises(OpenSetResponseError, match="observable labels"):
            source_separation_gate_from_pr256(
                report_3d,
                classes=classes,
                covariance=np.eye(2),
                nuisance_tangent=None,
            )

    changed_covariance = np.diag([2.0, 1.0])
    changed_covariance_report = _equivalence(
        classes,
        covariance=changed_covariance,
    )
    with pytest.raises(OpenSetResponseError, match="not bound"):
        _classify(
            [-3.0, 0.0],
            classes,
            changed_covariance_report,
            covariance=changed_covariance,
            source_gate=gate,
        )
    with pytest.raises(OpenSetResponseError, match="not bound"):
        classify_open_set_response_batch(
            observations=[[-3.0, 0.0]],
            classes=classes,
            equivalence_report=changed_covariance_report,
            covariance=changed_covariance,
            nuisance_tangent=None,
            unknown_squared_distance_threshold=4.0,
            decision_squared_margin=0.5,
            covariance_null_tolerance=1.0e-10,
            absolute_tolerance=1.0e-12,
            relative_tolerance=1.0e-12,
            source_separation_gate=gate,
        )

    nuisance_tangent = np.asarray([[1.0], [0.0]], dtype=np.float64)
    nuisance_report = _equivalence(
        classes,
        nuisance_tangent=nuisance_tangent,
    )
    with pytest.raises(OpenSetResponseError, match="not bound"):
        _classify(
            [-3.0, 0.0],
            classes,
            nuisance_report,
            nuisance_tangent=nuisance_tangent,
            source_gate=gate,
        )
    with pytest.raises(OpenSetResponseError, match="not bound"):
        classify_open_set_response_batch(
            observations=[[-3.0, 0.0]],
            classes=classes,
            equivalence_report=nuisance_report,
            covariance=np.eye(2),
            nuisance_tangent=nuisance_tangent,
            unknown_squared_distance_threshold=4.0,
            decision_squared_margin=0.5,
            covariance_null_tolerance=1.0e-10,
            absolute_tolerance=1.0e-12,
            relative_tolerance=1.0e-12,
            source_separation_gate=gate,
        )

    wrong_provider_classes = (
        _class(
            "local",
            [[-3.0, 0.0]],
            provider_id=_id("provider:wrong-local"),
            source_semantics=ResponseClassSourceSemantics.LOCAL_BOOST,
            source_response_id=classes[0].source_response_id,
        ),
        classes[1],
    )
    congruent_report, _ = _pr256_source_gate(
        separable=True,
        classes=classes,
    )
    with pytest.raises(OpenSetResponseError, match="provider identity"):
        source_separation_gate_from_pr256(
            congruent_report,
            classes=wrong_provider_classes,
            covariance=np.eye(2),
            nuisance_tangent=None,
        )

    wrong_response_classes = (
        _class(
            "local",
            [[-3.0, 0.0]],
            source_semantics=ResponseClassSourceSemantics.LOCAL_BOOST,
            source_response_id=_id("response:wrong-local"),
        ),
        classes[1],
    )
    with pytest.raises(OpenSetResponseError, match="response identity"):
        source_separation_gate_from_pr256(
            congruent_report,
            classes=wrong_response_classes,
            covariance=np.eye(2),
            nuisance_tangent=None,
        )


def test_exact_decision_boundaries_abstain_conservatively() -> None:
    classes = (
        _class("left", [[-1.0, 0.0]]),
        _class("right", [[1.0, 0.0]]),
    )
    report = _equivalence(classes, tolerance=0.0)
    at_unknown_boundary = _classify(
        [0.0, 2.0],
        classes,
        report,
        unknown_threshold=5.0,
        margin=0.0,
    )
    assert (
        at_unknown_boundary.status
        is OpenSetClassificationStatus.UNKNOWN_CLASS
    )
    at_margin_boundary = _classify(
        [0.0, 0.0],
        classes,
        report,
        unknown_threshold=2.0,
        margin=0.0,
    )
    assert (
        at_margin_boundary.status
        is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
    )


def test_global_equivalence_precedes_unknown_tube_exterior() -> None:
    classes = (
        _class("equiv-a", [[0.0, 0.0]]),
        _class("equiv-b", [[0.0, 0.0]]),
    )
    report = _equivalence(classes)
    far = _classify([0.0, 100.0], classes, report)

    assert far.status is OpenSetClassificationStatus.EQUIVALENCE_CLASS
    assert far.returned_equivalence_class == report.components[0]
    assert far.candidate_class_id is None


def test_zero_supported_covariance_and_missing_native_provider_fail_closed() -> None:
    finite_classes = (
        _class("left", [[-3.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    zero_report = _equivalence(finite_classes, covariance=np.zeros((2, 2)))
    assert (
        zero_report.status
        is ResponseEquivalenceStatus.OUTSIDE_SUPPORTED_QUOTIENT
    )
    zero_classification = _classify(
        [-3.0, 0.0],
        finite_classes,
        zero_report,
        covariance=np.zeros((2, 2)),
    )
    assert (
        zero_classification.status
        is OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT
    )

    native = _class(
        "future",
        None,
        kind=ResponseSupportKind.NEEDS_NATIVE,
        transfer_source=None,
    )
    missing_report = _equivalence((finite_classes[0], native))
    assert (
        missing_report.status
        is ResponseEquivalenceStatus.MISSING_RESPONSE_PROVIDER
    )
    assert all(
        value is None
        for row in missing_report.pairwise_minimum_squared_distances
        for value in row
    )
    assert "NaN" not in json.dumps(missing_report.as_payload())
    missing_classification = _classify(
        [-3.0, 0.0],
        (finite_classes[0], native),
        missing_report,
    )
    assert missing_classification.status is OpenSetClassificationStatus.NEEDS_NATIVE


def test_exact_duplicate_support_nodes_do_not_change_decision() -> None:
    baseline_classes = (
        _class("left", [[-3.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    duplicated_classes = (
        _class("left", [[-3.0, 0.0], [-3.0, 0.0]]),
        _class("right", [[3.0, 0.0], [3.0, 0.0], [3.0, 0.0]]),
    )
    baseline_report = _equivalence(baseline_classes)
    duplicated_report = _equivalence(duplicated_classes)
    baseline = _classify([-3.0, 0.0], baseline_classes, baseline_report)
    duplicated = _classify(
        [-3.0, 0.0],
        duplicated_classes,
        duplicated_report,
    )

    assert baseline.status is duplicated.status
    assert baseline.candidate_class_id == duplicated.candidate_class_id
    assert baseline_classes[0].response_content_id == duplicated_classes[0].response_content_id


def test_signed_zero_is_canonical_duplicate_not_refinement() -> None:
    import common.open_set_response_classes as common_surface

    baseline_classes = (
        _class("zero", [[0.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    signed_zero_classes = (
        _class(
            "zero",
            [
                [0.0, 0.0],
                [-0.0, 0.0],
                [0.0, -0.0],
                [-0.0, -0.0],
            ],
        ),
        _class("right", [[3.0, -0.0]]),
    )

    assert signed_zero_classes[0].support_node_count == 1
    assert signed_zero_classes[0].duplicate_node_count == 3
    assert not np.any(np.signbit(signed_zero_classes[0].support_nodes))
    assert (
        baseline_classes[0].response_content_id
        == signed_zero_classes[0].response_content_id
    )
    assert (
        baseline_classes[0].support_node_ids
        == signed_zero_classes[0].support_node_ids
    )

    baseline_report = _equivalence(baseline_classes)
    signed_zero_report = _equivalence(signed_zero_classes)
    assert baseline_report.report_id == signed_zero_report.report_id
    baseline = _classify([0.0, 0.0], baseline_classes, baseline_report)
    signed_zero = _classify(
        [0.0, 0.0],
        signed_zero_classes,
        signed_zero_report,
    )
    assert baseline.as_payload() == signed_zero.as_payload()

    accepted = common_surface._validate_finite_support_perturbation(
        kind=FiniteSupportPerturbationKind.EXACT_DUPLICATE,
        baseline=baseline_classes,
        perturbed=signed_zero_classes,
    )
    assert {
        item.class_id: item.response_content_id for item in accepted
    } == {
        item.class_id: item.response_content_id
        for item in signed_zero_classes
    }
    with pytest.raises(OpenSetResponseError, match="cannot reuse"):
        common_surface._validate_finite_support_perturbation(
            kind=FiniteSupportPerturbationKind.REFINEMENT,
            baseline=baseline_classes,
            perturbed=signed_zero_classes,
        )


def test_benchmark_reports_open_set_metrics_and_precision_status() -> None:
    separated_classes = _benchmark_class_library()
    separated_report = _equivalence(separated_classes)
    left = _classify([-3.0, 0.0], separated_classes, separated_report)
    unknown = _classify([0.0, 10.0], separated_classes, separated_report)

    equivalent_classes = (
        _class("equiv-a", [[0.0, 0.0]]),
        _class("equiv-b", [[0.0, 0.0]]),
    )
    equivalent_report = _equivalence(
        equivalent_classes,
        reopening_observables=(_reopening(equivalent_classes),),
    )
    equivalent = _classify(
        [0.0, 0.0],
        equivalent_classes,
        equivalent_report,
    )
    count = 20_000
    (
        perturbed_classes,
        perturbed_equivalence_reports,
        perturbed_reports,
    ) = _benchmark_perturbation_inputs([-3.0, 0.0], count=count)
    benchmark = evaluate_open_set_benchmark(
        known_reports=(left,) * count,
        known_truth_class_ids=("response-class-left",) * count,
        equivalence_reports=(equivalent,) * count,
        expected_equivalence_class=equivalent_report.components[0],
        unknown_reports=(unknown,) * count,
        support_perturbed_reports=perturbed_reports,
        baseline_classes=separated_classes,
        support_perturbed_classes=perturbed_classes,
        baseline_equivalence_report=separated_report,
        equivalence_report=equivalent_report,
        support_perturbed_equivalence_reports=(
            perturbed_equivalence_reports
        ),
        master_seed=20260728,
        calibration_receipt=_id("fixed-before-generation"),
        split_receipt=_id("split-60-20-20"),
        thresholds_frozen_before_held_out=True,
    )

    assert benchmark.status is OpenSetBenchmarkStatus.MEASURED_PASS
    assert benchmark.false_response_class_candidate_rate == 0.0
    assert benchmark.equivalence_class_coverage == 1.0
    assert benchmark.unknown_generator_conditional_detection_rate == 1.0
    assert dict(
        benchmark.finite_support_perturbation_sensitivity_rates
    ) == {
        kind: 0.0 for kind in FiniteSupportPerturbationKind
    }
    assert benchmark.minimal_reopening_observable_ids == (
        _id("reopening:polarization"),
    )
    assert benchmark.observed_data_used is False
    assert benchmark.pr151_data_used is False
    assert benchmark.old_rust_output_used is False
    assert benchmark.native_solver_output_used is False
    assert benchmark.maximum_mcse == 0.0025
    assert benchmark.minimum_replicates_per_cell == 20_000
    assert (
        benchmark.maximum_replicates_per_cell
        == PR258_MAXIMUM_MC_REPLICATES
    )
    assert benchmark.as_payload()["maximum_mcse"] == 0.0025
    assert benchmark.as_payload()["minimum_replicates_per_cell"] == 20_000
    assert (
        benchmark.as_payload()["maximum_replicates_per_cell"]
        == PR258_MAXIMUM_MC_REPLICATES
    )
    artifact_metadata = {
        "owner": PR258_ARTIFACT_OWNER,
        "scope": PR258_ARTIFACT_SCOPE,
        "artifact_mode": PR258_ARTIFACT_MODE,
        "sky_support_status": PR258_SKY_SUPPORT_STATUS,
        "null_mock_status": PR258_NULL_MOCK_STATUS,
        "covariance_status": PR258_COVARIANCE_STATUS,
    }
    assert {
        key: benchmark.as_payload()[key]
        for key in artifact_metadata
    } == artifact_metadata
    assert (
        benchmark.as_payload()["schema"]
        == "PR258_OPEN_SET_BENCHMARK_REPORT_V3"
    )

    inconclusive = evaluate_open_set_benchmark(
        known_reports=(left,),
        known_truth_class_ids=("response-class-left",),
        equivalence_reports=(equivalent,),
        expected_equivalence_class=equivalent_report.components[0],
        unknown_reports=(unknown,),
        support_perturbed_reports={
            kind: reports[:1]
            for kind, reports in perturbed_reports.items()
        },
        baseline_classes=separated_classes,
        support_perturbed_classes=perturbed_classes,
        baseline_equivalence_report=separated_report,
        equivalence_report=equivalent_report,
        support_perturbed_equivalence_reports={
            kind: report
            for kind, report in perturbed_equivalence_reports.items()
        },
        master_seed=20260728,
        calibration_receipt=_id("fixed-before-generation"),
        split_receipt=_id("split-60-20-20"),
        thresholds_frozen_before_held_out=True,
    )
    assert (
        inconclusive.status
        is OpenSetBenchmarkStatus.INCONCLUSIVE_MC_PRECISION
    )


def test_benchmark_binds_reports_and_requires_every_support_perturbation() -> None:
    classes = _benchmark_class_library()
    baseline_report = _equivalence(classes)
    known = _classify([-3.0, 0.0], classes, baseline_report)
    unknown = _classify([0.0, 10.0], classes, baseline_report)
    equivalent_classes = (
        _class("equiv-a", [[0.0, 0.0]]),
        _class("equiv-b", [[0.0, 0.0]]),
    )
    equivalent_report = _equivalence(equivalent_classes)
    equivalent = _classify(
        [0.0, 0.0],
        equivalent_classes,
        equivalent_report,
    )
    (
        complete_classes,
        complete_equivalence,
        complete_reports,
    ) = _benchmark_perturbation_inputs([-3.0, 0.0], count=1)
    common = {
        "known_reports": (known,),
        "known_truth_class_ids": ("response-class-left",),
        "equivalence_reports": (equivalent,),
        "expected_equivalence_class": equivalent_report.components[0],
        "unknown_reports": (unknown,),
        "baseline_classes": classes,
        "baseline_equivalence_report": baseline_report,
        "equivalence_report": equivalent_report,
        "master_seed": 20260728,
        "calibration_receipt": _id("fixed-before-generation"),
        "split_receipt": _id("split-60-20-20"),
        "thresholds_frozen_before_held_out": True,
    }

    with pytest.raises(OpenSetResponseError, match="every registered"):
        evaluate_open_set_benchmark(
            **common,
            support_perturbed_reports={
                FiniteSupportPerturbationKind.EXACT_DUPLICATE: (
                    complete_reports[
                        FiniteSupportPerturbationKind.EXACT_DUPLICATE
                    ]
                ),
            },
            support_perturbed_classes={
                FiniteSupportPerturbationKind.EXACT_DUPLICATE: (
                    complete_classes[
                        FiniteSupportPerturbationKind.EXACT_DUPLICATE
                    ]
                ),
            },
            support_perturbed_equivalence_reports={
                FiniteSupportPerturbationKind.EXACT_DUPLICATE: (
                    complete_equivalence[
                        FiniteSupportPerturbationKind.EXACT_DUPLICATE
                    ]
                ),
            },
        )

    unrelated_classes = (
        _class("other-a", [[-1.0, 0.0]]),
        _class("other-b", [[1.0, 0.0]]),
    )
    unrelated_report = _equivalence(unrelated_classes)
    with pytest.raises(OpenSetResponseError, match="equivalence-cell"):
        evaluate_open_set_benchmark(
            **{
                **common,
                "equivalence_report": unrelated_report,
            },
            support_perturbed_reports=complete_reports,
            support_perturbed_classes=complete_classes,
            support_perturbed_equivalence_reports=complete_equivalence,
        )

    with pytest.raises(OpenSetResponseError, match="cannot reuse"):
        mislabeled_classes = {
            kind: (
                complete_classes[kind]
                if kind is FiniteSupportPerturbationKind.EXACT_DUPLICATE
                else classes
            )
            for kind in FiniteSupportPerturbationKind
        }
        mislabeled_reports = {
            kind: (
                complete_reports[kind]
                if kind is FiniteSupportPerturbationKind.EXACT_DUPLICATE
                else (known,)
            )
            for kind in FiniteSupportPerturbationKind
        }
        mislabeled_equivalence = {
            kind: (
                complete_equivalence[kind]
                if kind is FiniteSupportPerturbationKind.EXACT_DUPLICATE
                else baseline_report
            )
            for kind in FiniteSupportPerturbationKind
        }
        evaluate_open_set_benchmark(
            **common,
            support_perturbed_reports=mislabeled_reports,
            support_perturbed_classes=mislabeled_classes,
            support_perturbed_equivalence_reports=mislabeled_equivalence,
        )


def test_benchmark_rejects_precision_relaxation_and_over_cap_cells() -> None:
    classes = _benchmark_class_library()
    baseline_report = _equivalence(classes)
    known = _classify([-3.0, 0.0], classes, baseline_report)
    unknown = _classify([0.0, 10.0], classes, baseline_report)
    equivalent_classes = (
        _class("equiv-a", [[0.0, 0.0]]),
        _class("equiv-b", [[0.0, 0.0]]),
    )
    equivalent_report = _equivalence(equivalent_classes)
    equivalent = _classify(
        [0.0, 0.0],
        equivalent_classes,
        equivalent_report,
    )
    (
        perturbed_classes,
        perturbed_equivalence,
        perturbed_reports,
    ) = _benchmark_perturbation_inputs([-3.0, 0.0], count=1)
    common = {
        "known_reports": (known,),
        "known_truth_class_ids": ("response-class-left",),
        "equivalence_reports": (equivalent,),
        "expected_equivalence_class": equivalent_report.components[0],
        "unknown_reports": (unknown,),
        "support_perturbed_reports": perturbed_reports,
        "baseline_classes": classes,
        "support_perturbed_classes": perturbed_classes,
        "baseline_equivalence_report": baseline_report,
        "equivalence_report": equivalent_report,
        "support_perturbed_equivalence_reports": perturbed_equivalence,
        "master_seed": 20260728,
        "calibration_receipt": _id("fixed-before-generation"),
        "split_receipt": _id("split-60-20-20"),
        "thresholds_frozen_before_held_out": True,
    }

    with pytest.raises(OpenSetResponseError, match="preregistered"):
        evaluate_open_set_benchmark(
            **common,
            maximum_mcse=0.01,
        )

    for field, report in (
        ("known_reports", known),
        ("equivalence_reports", equivalent),
        ("unknown_reports", unknown),
    ):
        with pytest.raises(
            OpenSetResponseError,
            match="maximum_replicates_per_cell",
        ):
            evaluate_open_set_benchmark(
                **{
                    **common,
                    field: (report,)
                    * (PR258_MAXIMUM_MC_REPLICATES + 1),
                },
            )

    with pytest.raises(
        OpenSetResponseError,
        match="maximum_replicates_per_cell",
    ):
        evaluate_open_set_benchmark(
            **{
                **common,
                "support_perturbed_reports": {
                    **perturbed_reports,
                    FiniteSupportPerturbationKind.EXACT_DUPLICATE: (
                        perturbed_reports[
                            FiniteSupportPerturbationKind.EXACT_DUPLICATE
                        ][0],
                    )
                    * (PR258_MAXIMUM_MC_REPLICATES + 1),
                },
            },
        )


def test_benchmark_support_sensitivity_detects_a_decision_flip() -> None:
    classes = _benchmark_class_library()
    baseline_report = _equivalence(classes)
    known = _classify([-3.0, 0.0], classes, baseline_report)
    unknown = _classify([0.0, 10.0], classes, baseline_report)
    equivalent_classes = (
        _class("equiv-a", [[0.0, 0.0]]),
        _class("equiv-b", [[0.0, 0.0]]),
    )
    equivalent_report = _equivalence(equivalent_classes)
    equivalent = _classify(
        [0.0, 0.0],
        equivalent_classes,
        equivalent_report,
    )
    (
        perturbed_classes,
        perturbed_equivalence,
        perturbed_reports,
    ) = _benchmark_perturbation_inputs(
        [-3.0, 0.0],
        count=1,
        flip_expansion=True,
    )

    benchmark = evaluate_open_set_benchmark(
        known_reports=(known,),
        known_truth_class_ids=("response-class-left",),
        equivalence_reports=(equivalent,),
        expected_equivalence_class=equivalent_report.components[0],
        unknown_reports=(unknown,),
        support_perturbed_reports=perturbed_reports,
        baseline_classes=classes,
        support_perturbed_classes=perturbed_classes,
        baseline_equivalence_report=baseline_report,
        equivalence_report=equivalent_report,
        support_perturbed_equivalence_reports=perturbed_equivalence,
        master_seed=20260728,
        calibration_receipt=_id("fixed-before-generation"),
        split_receipt=_id("split-60-20-20"),
        thresholds_frozen_before_held_out=True,
    )

    assert dict(
        benchmark.finite_support_perturbation_sensitivity_rates
    )[FiniteSupportPerturbationKind.EXPANSION] == 1.0


def test_machine_claim_tier_and_forbidden_inference_keys_are_absent() -> None:
    classes = (
        _class("left", [[-3.0, 0.0]]),
        _class("right", [[3.0, 0.0]]),
    )
    equivalence = _equivalence(classes)
    decision = _classify([-3.0, 0.0], classes, equivalence)
    payload = {
        "equivalence": equivalence.as_payload(),
        "decision": decision.as_payload(),
    }
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["decision"]["claim_tier_ceiling"] == "diagnostic_only"
    assert payload["decision"]["roadmap_claim_level"]["level"] == "C2"
    banned_keys = {
        "family_probability",
        "family_posterior",
        "bayes_factor",
        "p_value",
        "e_value",
        "likelihood",
        "log_likelihood",
        "Q",
        "Pi",
        "F",
        "G_F",
        "native_geometry",
        "detected_family",
        "identified_family",
    }

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    assert banned_keys.isdisjoint(set(keys(payload)))
    assert "Bianchi family identified" not in encoded
    assert "geometry detected" not in encoded


def test_htt_public_api_reexports_common_identity() -> None:
    import common.open_set_response_classes as common_api
    import htt.statistics as statistics
    import htt.statistics.open_set_response_classes as htt_api

    assert htt_api.ResponseClassManifoldSpec is common_api.ResponseClassManifoldSpec
    assert statistics.ResponseClassManifoldSpec is common_api.ResponseClassManifoldSpec
    assert statistics.classify_open_set_response is common_api.classify_open_set_response


def test_pr219_and_statistical_foundation_authority_bytes_are_unchanged() -> None:
    expected = {
        "htt/src/common/revival_response_quotient.py": (
            "cc9802426d7af2eb29d77eef89f63e7eb3a220d935243c87fdf34ac757899d22"
        ),
        "docs/generated/pr219_result_card.json": (
            "a1615e4df9f59712d482b30be374874d66a480c97ba18a453838858aa45bc222"
        ),
        "docs/research_program/revival/pr219_spec.yaml": (
            "56a860c315e9c134b2d545c0fd0af6876f3c6b031d96c2fe5f50c32ede43650e"
        ),
        "docs/research_program/STAT_FOUNDATIONS_REVIEW_20260727.md": (
            "61a3ded47a9925cbddd620635c32c075d02eec2ca038824d440acc5f49e4c87a"
        ),
    }
    observed = {
        path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        for path in expected
    }
    assert observed == expected
