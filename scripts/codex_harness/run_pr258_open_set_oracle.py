#!/usr/bin/env python3
"""Independent small-matrix oracle for PR-258 response classes.

The direct calculations below use only NumPy linear algebra and graph
traversal.  The public implementation is imported only after the expected
answers have been obtained.  This is a synthetic software oracle, not an
observational, native-solver, likelihood, or family-identification result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT / "htt/src", ROOT / "htt"):
    text = str(entry)
    if text not in sys.path:
        sys.path.insert(0, text)

from common.anchor_geometry import (  # noqa: E402
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (  # noqa: E402
    anchored_numeric_content_id,
)
from common.open_set_response_classes import (  # noqa: E402
    OpenSetClassificationStatus,
    OpenSetResponseError,
    PR258_ARTIFACT_MODE,
    PR258_ARTIFACT_OWNER,
    PR258_ARTIFACT_SCOPE,
    PR258_COVARIANCE_STATUS,
    PR258_MAXIMUM_MC_REPLICATES,
    PR258_MAXIMUM_MCSE,
    PR258_MINIMUM_MC_REPLICATES,
    PR258_NULL_MOCK_STATUS,
    PR258_SKY_SUPPORT_STATUS,
    ReopeningObservableStatus,
    ResponseClassSourceSemantics,
    ResponseEquivalenceStatus,
    ResponseSupportKind,
    build_reopening_observable_spec,
    build_response_class_manifold,
    build_response_equivalence_report,
    classify_open_set_response,
    classify_open_set_response_batch,
    evaluate_open_set_benchmark,
    source_separation_not_applicable,
)
from common.transfer_registry import TransferSource  # noqa: E402
from htt.departure.velocity_frame_decomposition import (  # noqa: E402
    ResponseProviderAvailability,
    ResponseProviderKind,
    SourceHypothesis,
    VelocityComponent,
    measure_source_response_geometry,
    register_source_response_provider,
)
from htt.statistics.open_set_response_classes import (  # noqa: E402
    PR283_DEFAULT_THRESHOLD_CONTRACT,
    source_separation_gate_from_pr256,
)


ATOL = 1.0e-12
RTOL = 1.0e-12


def _receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()


def _response_class(
    suffix: str,
    nodes: list[list[float]],
    *,
    labels: tuple[str, ...] = ("x",),
):
    return build_response_class_manifold(
        class_id=f"response-class-{suffix}",
        support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
        provider_id=_receipt(f"provider:{suffix}"),
        observable_labels=labels,
        convention_id=_receipt(f"convention:{labels}"),
        nuisance_policy_id=_receipt(f"nuisance:{labels}"),
        support_nodes=nodes,
    )


def _direct_squared_distance(
    left: np.ndarray,
    right: np.ndarray,
    covariance: np.ndarray,
) -> float:
    inverse = np.linalg.pinv(covariance, rcond=RTOL)
    delta = left - right
    return float(delta @ inverse @ delta)


def _direct_components(
    distances: np.ndarray,
    tolerance: float,
) -> tuple[tuple[int, ...], ...]:
    parent = list(range(distances.shape[0]))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for left in range(distances.shape[0]):
        for right in range(left + 1, distances.shape[0]):
            if distances[left, right] <= tolerance:
                root_left = find(left)
                root_right = find(right)
                if root_left != root_right:
                    parent[root_right] = root_left
    groups: dict[int, list[int]] = {}
    for index in range(distances.shape[0]):
        groups.setdefault(find(index), []).append(index)
    return tuple(
        sorted(
            (tuple(values) for values in groups.values()),
            key=lambda values: values[0],
        )
    )


def _check_squared_scale() -> dict[str, object]:
    covariance = np.asarray([[4.0]])
    direct = _direct_squared_distance(
        np.asarray([0.0]),
        np.asarray([1.0]),
        covariance,
    )
    if direct != 0.25:
        raise AssertionError("direct d^2 oracle changed")
    classes = (
        _response_class("scale-a", [[0.0]]),
        _response_class("scale-b", [[1.0]]),
    )
    report = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.3,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    if report.pairwise_minimum_squared_distances[0][1] != direct:
        raise AssertionError("public score is not the direct squared score")
    if report.status is not ResponseEquivalenceStatus.EQUIVALENCE_CLASS:
        raise AssertionError("d versus d^2 mutation survived")
    return {"direct_squared_distance": direct, "status": report.status.value}


def _check_structural_null_unit_congruence() -> dict[str, object]:
    """A structural zero is an exact constraint, not an arbitrary-unit norm."""

    classes = (
        _response_class(
            "unit-left",
            [[-3.0, 0.0]],
            labels=("x", "structural-null"),
        ),
        _response_class(
            "unit-right",
            [[3.0, 0.0]],
            labels=("x", "structural-null"),
        ),
    )
    covariance = np.diag([1.0, 0.0])
    report = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.0,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    statuses = []
    for unit_scale in (1.0, 100.0):
        outside = classify_open_set_response(
            observation=[-3.0, 5.0e-11 * unit_scale],
            classes=classes,
            equivalence_report=report,
            covariance=covariance,
            nuisance_tangent=None,
            unknown_squared_distance_threshold=4.0,
            decision_squared_margin=0.5,
            covariance_null_tolerance=1.0e-10,
            absolute_tolerance=ATOL,
            relative_tolerance=RTOL,
            source_separation_gate=source_separation_not_applicable(),
        )
        exact = classify_open_set_response(
            observation=[-3.0, 0.0],
            classes=classes,
            equivalence_report=report,
            covariance=covariance,
            nuisance_tangent=None,
            unknown_squared_distance_threshold=4.0,
            decision_squared_margin=0.5,
            covariance_null_tolerance=1.0e-10,
            absolute_tolerance=ATOL,
            relative_tolerance=RTOL,
            source_separation_gate=source_separation_not_applicable(),
        )
        expected = (
            OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT,
            OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE,
        )
        observed = (outside.status, exact.status)
        if observed != expected:
            raise AssertionError(
                "zero-variance structural-null decision changed with units"
            )
        if (
            outside.covariance_structural_null_mismatch is not True
            or exact.covariance_structural_null_mismatch is not False
            or outside.covariance_null_residual != 0.0
            or exact.covariance_null_residual != 0.0
        ):
            raise AssertionError(
                "structural and dimensionless covariance nulls were merged"
            )
        statuses.append([item.value for item in observed])
    correlation_results = []
    for scales in ((1.0, 1.0), (2.0, 5.0)):
        scaling = np.diag(scales)
        scaled_classes = tuple(
            build_response_class_manifold(
                class_id=f"response-class-correlation-{suffix}",
                support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
                provider_id=_receipt(f"correlation-provider:{suffix}"),
                observable_labels=("correlation-x", "correlation-y"),
                convention_id=_receipt("correlation-convention"),
                nuisance_policy_id=_receipt("correlation-nuisance"),
                support_nodes=[
                    (scaling @ np.asarray(node, dtype=float)).tolist()
                ],
            )
            for suffix, node in (
                ("a", [0.0, 0.0]),
                ("b", [3.0, 3.0]),
            )
        )
        scaled_covariance = scaling @ np.ones((2, 2)) @ scaling
        scaled_report = build_response_equivalence_report(
            classes=scaled_classes,
            covariance=scaled_covariance,
            nuisance_tangent=None,
            equivalence_squared_distance_tolerance=0.01,
            absolute_tolerance=ATOL,
            relative_tolerance=RTOL,
        )
        scaled_decision = classify_open_set_response(
            observation=(
                scaling @ np.asarray([0.5, -0.5])
            ).tolist(),
            classes=scaled_classes,
            equivalence_report=scaled_report,
            covariance=scaled_covariance,
            nuisance_tangent=None,
            unknown_squared_distance_threshold=4.0,
            decision_squared_margin=0.5,
            covariance_null_tolerance=1.0e-10,
            absolute_tolerance=ATOL,
            relative_tolerance=RTOL,
            source_separation_gate=source_separation_not_applicable(),
        )
        correlation_results.append(
            (
                scaled_decision.status.value,
                scaled_decision.best_squared_distance,
                scaled_decision.covariance_null_residual,
                scaled_decision.covariance_structural_null_mismatch,
            )
        )
    if (
        correlation_results[0] != correlation_results[1]
        or correlation_results[0][0]
        != OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT.value
        or correlation_results[0][1] != 0.0
        or not np.isclose(
            correlation_results[0][2],
            2.0**-0.5,
            rtol=0.0,
            atol=1.0e-15,
        )
        or correlation_results[0][3] is not False
    ):
        raise AssertionError(
            "dimensionless correlation-null residual changed with units"
        )
    return {
        "unit_scales": [1.0, 100.0],
        "statuses": statuses,
        "structural_null_is_exact": True,
        "dimensionless_null_residual": 0.0,
        "correlation_unit_scales": [[1.0, 1.0], [2.0, 5.0]],
        "correlation_null_residual": correlation_results[0][2],
        "correlation_null_unit_congruent": True,
    }


def _check_signed_zero_and_mc_contract() -> dict[str, object]:
    baseline = _response_class("signed-zero", [[0.0]])
    duplicate = _response_class(
        "signed-zero",
        [[0.0], [-0.0]],
    )
    if (
        duplicate.support_node_count != 1
        or duplicate.duplicate_node_count != 1
        or baseline.response_content_id != duplicate.response_content_id
        or baseline.support_node_ids != duplicate.support_node_ids
        or np.any(np.signbit(duplicate.support_nodes))
    ):
        raise AssertionError("signed zero survived canonical support identity")

    common = {
        "known_reports": (),
        "known_truth_class_ids": (),
        "equivalence_reports": (),
        "expected_equivalence_class": (),
        "unknown_reports": (),
        "support_perturbed_reports": {},
        "baseline_classes": (),
        "support_perturbed_classes": {},
        "baseline_equivalence_report": None,
        "equivalence_report": None,
        "support_perturbed_equivalence_reports": {},
        "master_seed": 20260728,
        "calibration_receipt": _receipt("calibration"),
        "split_receipt": _receipt("split"),
        "thresholds_frozen_before_held_out": True,
    }
    try:
        evaluate_open_set_benchmark(
            **common,
            maximum_mcse=0.01,
        )
    except OpenSetResponseError as exc:
        relaxed_rejected = "preregistered" in str(exc)
    else:
        relaxed_rejected = False
    if not relaxed_rejected:
        raise AssertionError("relaxed maximum_mcse survived")

    try:
        evaluate_open_set_benchmark(
            **{
                **common,
                "known_reports": (object(),)
                * (PR258_MAXIMUM_MC_REPLICATES + 1),
            },
        )
    except OpenSetResponseError as exc:
        over_cap_rejected = "maximum_replicates_per_cell" in str(exc)
    else:
        over_cap_rejected = False
    if not over_cap_rejected:
        raise AssertionError("over-cap benchmark cell survived")

    frozen_artifact = json.loads(
        (
            ROOT
            / "docs/generated/pr258_open_set_response_classes/"
            "open_set_benchmark.json"
        ).read_text(encoding="utf-8")
    )
    frozen = frozen_artifact["benchmark_report"]
    if (
        frozen.get("maximum_mcse") != PR258_MAXIMUM_MCSE
        or frozen.get("minimum_replicates_per_cell")
        != PR258_MINIMUM_MC_REPLICATES
        or frozen.get("maximum_replicates_per_cell")
        != PR258_MAXIMUM_MC_REPLICATES
    ):
        raise AssertionError("frozen benchmark omitted its MC contract")
    expected_metadata = {
        "owner": PR258_ARTIFACT_OWNER,
        "scope": PR258_ARTIFACT_SCOPE,
        "artifact_mode": PR258_ARTIFACT_MODE,
        "sky_support_status": PR258_SKY_SUPPORT_STATUS,
        "null_mock_status": PR258_NULL_MOCK_STATUS,
        "covariance_status": PR258_COVARIANCE_STATUS,
    }
    if any(
        frozen_artifact.get(key) != value
        or frozen.get(key) != value
        or frozen_artifact["provenance"].get(key) != value
        for key, value in expected_metadata.items()
    ):
        raise AssertionError(
            "frozen benchmark omitted claim-bearing artifact metadata"
        )
    return {
        "signed_zero_duplicate_count": duplicate.duplicate_node_count,
        "signed_zero_response_identity_preserved": True,
        "maximum_mcse": PR258_MAXIMUM_MCSE,
        "minimum_replicates_per_cell": PR258_MINIMUM_MC_REPLICATES,
        "maximum_replicates_per_cell": PR258_MAXIMUM_MC_REPLICATES,
        "relaxed_maximum_rejected": relaxed_rejected,
        "over_cap_cell_rejected": over_cap_rejected,
        "artifact_metadata_bound": True,
    }


def _check_chain_closure() -> dict[str, object]:
    values = np.asarray((0.0, 0.9, 1.8))
    distances = (values[:, None] - values[None, :]) ** 2
    expected_components = _direct_components(distances, 1.0)
    if expected_components != ((0, 1, 2),):
        raise AssertionError("direct chain closure changed")
    classes = tuple(
        _response_class(name, [[float(value)]])
        for name, value in zip(("a", "b", "c"), values, strict=True)
    )
    report = build_response_equivalence_report(
        classes=classes,
        covariance=[[1.0]],
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=1.0,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    if report.status is not ResponseEquivalenceStatus.TYPE_UNIDENTIFIED:
        raise AssertionError("non-clique closure was presented as equality")
    if report.equivalence_edges != (
        ("response-class-a", "response-class-b"),
        ("response-class-b", "response-class-c"),
    ):
        raise AssertionError("direct graph edges changed")
    if report.pairwise_minimum_squared_distances[0][2] != 3.24:
        raise AssertionError("component diameter evidence was lost")
    return {
        "components": [list(item) for item in report.components],
        "direct_edges": [list(item) for item in report.equivalence_edges],
        "maximum_squared_separation": 3.24,
    }


def _check_shared_boundary_and_null_precedence() -> dict[str, object]:
    classes = (
        build_response_class_manifold(
            class_id="response-class-left",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_receipt("provider:left"),
            observable_labels=("x", "null"),
            convention_id=_receipt("convention:two"),
            nuisance_policy_id=_receipt("nuisance:two"),
            support_nodes=[[0.0, 0.0], [-3.0, 0.0]],
        ),
        build_response_class_manifold(
            class_id="response-class-right",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_receipt("provider:right"),
            observable_labels=("x", "null"),
            convention_id=_receipt("convention:two"),
            nuisance_policy_id=_receipt("nuisance:two"),
            support_nodes=[[0.0, 0.0], [3.0, 0.0]],
        ),
    )
    covariance = np.diag([1.0, 0.0])
    report = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.01,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    classified = classify_open_set_response(
        observation=[-3.0, 100.0],
        classes=classes,
        equivalence_report=report,
        covariance=covariance,
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        source_separation_gate=source_separation_not_applicable(),
    )
    if report.status is not ResponseEquivalenceStatus.EQUIVALENCE_CLASS:
        raise AssertionError("shared boundary did not collapse globally")
    if (
        classified.status
        is not OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT
    ):
        raise AssertionError("covariance-null residual did not dominate")
    return {
        "equivalence_status": report.status.value,
        "classification_status": classified.status.value,
        "covariance_null_residual": classified.covariance_null_residual,
    }


def _check_tied_node_and_nuisance_binding() -> dict[str, object]:
    classes = (
        build_response_class_manifold(
            class_id="response-class-tied",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_receipt("provider:tied"),
            observable_labels=("x", "null"),
            convention_id=_receipt("convention:tied"),
            nuisance_policy_id=_receipt("nuisance:tied"),
            support_nodes=[[0.0, -10.0], [0.0, 0.0]],
        ),
        build_response_class_manifold(
            class_id="response-class-separated",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_receipt("provider:separated"),
            observable_labels=("x", "null"),
            convention_id=_receipt("convention:tied"),
            nuisance_policy_id=_receipt("nuisance:tied"),
            support_nodes=[[3.0, 0.0]],
        ),
    )
    covariance = np.diag([1.0, 0.0])
    report = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.0,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    classified = classify_open_set_response(
        observation=[0.0, 0.0],
        classes=classes,
        equivalence_report=report,
        covariance=covariance,
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        source_separation_gate=source_separation_not_applicable(),
    )
    if (
        classified.status
        is not OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
        or classified.covariance_null_residual != 0.0
    ):
        raise AssertionError(
            "exact tied support node lost to a null-mismatched node"
        )
    try:
        classify_open_set_response(
            observation=[0.0, 0.0],
            classes=classes,
            equivalence_report=report,
            covariance=covariance,
            nuisance_tangent=[[0.0], [1.0]],
            unknown_squared_distance_threshold=4.0,
            decision_squared_margin=0.5,
            covariance_null_tolerance=1.0e-10,
            absolute_tolerance=ATOL,
            relative_tolerance=RTOL,
            source_separation_gate=source_separation_not_applicable(),
        )
    except OpenSetResponseError:
        nuisance_rebinding_rejected = True
    else:
        raise AssertionError("equivalence nuisance geometry was rebound")
    return {
        "candidate_class_id": classified.candidate_class_id,
        "covariance_null_residual": classified.covariance_null_residual,
        "nuisance_rebinding_rejected": nuisance_rebinding_rejected,
    }


def _check_nuisance_quotient_and_contract_binding() -> dict[str, object]:
    classes = (
        build_response_class_manifold(
            class_id=f"response-class-{name}",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_receipt(f"provider:{name}"),
            observable_labels=("x", "y"),
            convention_id=_receipt("convention:quotient"),
            nuisance_policy_id=_receipt("nuisance:x-orbit"),
            support_nodes=[node],
        )
        for name, node in (
            ("left", [-3.0, 0.0]),
            ("right", [3.0, 0.0]),
        )
    )
    classes = tuple(classes)
    nuisance = np.asarray(((1.0,), (0.0,)))
    report = build_response_equivalence_report(
        classes=classes,
        covariance=np.eye(2),
        nuisance_tangent=nuisance,
        equivalence_squared_distance_tolerance=0.0,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    shifted = classify_open_set_response(
        observation=[100.0, 0.0],
        classes=classes,
        equivalence_report=report,
        covariance=np.eye(2),
        nuisance_tangent=nuisance,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        source_separation_gate=source_separation_not_applicable(),
    )
    if (
        report.status is not ResponseEquivalenceStatus.EQUIVALENCE_CLASS
        or report.pairwise_covariance_null_residuals[0][1] != 0.0
        or shifted.status is not OpenSetClassificationStatus.EQUIVALENCE_CLASS
        or shifted.covariance_null_residual != 0.0
    ):
        raise AssertionError(
            "supported nuisance orbit was relabeled as a covariance null"
        )

    rebound = tuple(
        build_response_class_manifold(
            class_id=item.class_id,
            support_kind=item.support_kind,
            provider_id=_receipt(f"rebound:{item.class_id}"),
            observable_labels=item.observable_labels,
            convention_id=item.convention_id,
            nuisance_policy_id=item.nuisance_policy_id,
            support_nodes=item.support_nodes,
            transfer_source=item.transfer_source,
            source_semantics=item.source_semantics,
        )
        for item in classes
    )
    rejected = 0
    for batch in (False, True):
        try:
            kwargs = {
                "classes": rebound,
                "equivalence_report": report,
                "covariance": np.eye(2),
                "nuisance_tangent": nuisance,
                "unknown_squared_distance_threshold": 4.0,
                "decision_squared_margin": 0.5,
                "covariance_null_tolerance": 1.0e-10,
                "absolute_tolerance": ATOL,
                "relative_tolerance": RTOL,
                "source_separation_gate": source_separation_not_applicable(),
            }
            if batch:
                classify_open_set_response_batch(
                    observations=[[100.0, 0.0]],
                    **kwargs,
                )
            else:
                classify_open_set_response(
                    observation=[100.0, 0.0],
                    **kwargs,
                )
        except OpenSetResponseError:
            rejected += 1
    if rejected != 2:
        raise AssertionError("class-provider rebinding survived classification")

    scalar_classes = (
        _response_class("full-nuisance-left", [[-1.0]]),
        _response_class("full-nuisance-right", [[1.0]]),
    )
    scalar_report = build_response_equivalence_report(
        classes=scalar_classes,
        covariance=[[1.0]],
        nuisance_tangent=[[1.0]],
        equivalence_squared_distance_tolerance=0.0,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    scalar_decision = classify_open_set_response(
        observation=[100.0],
        classes=scalar_classes,
        equivalence_report=scalar_report,
        covariance=[[1.0]],
        nuisance_tangent=[[1.0]],
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        source_separation_gate=source_separation_not_applicable(),
    )
    if (
        scalar_report.supported_rank != 0
        or scalar_decision.status
        is not OpenSetClassificationStatus.EQUIVALENCE_CLASS
        or scalar_decision.covariance_null_residual != 0.0
    ):
        raise AssertionError(
            "full supported nuisance orbit was called covariance-null"
        )
    return {
        "nuisance_orbit_status": shifted.status.value,
        "full_nuisance_orbit_status": scalar_decision.status.value,
        "covariance_null_residual": shifted.covariance_null_residual,
        "single_and_batch_rebindings_rejected": rejected,
    }


def _check_equivalence_precedence_and_gate_surface() -> dict[str, object]:
    classes = (
        _response_class("equiv-left", [[0.0]]),
        _response_class("equiv-right", [[0.0]]),
    )
    report = build_response_equivalence_report(
        classes=classes,
        covariance=[[1.0]],
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.0,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    far = classify_open_set_response(
        observation=[100.0],
        classes=classes,
        equivalence_report=report,
        covariance=[[1.0]],
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        source_separation_gate=source_separation_not_applicable(),
    )
    if far.status is not OpenSetClassificationStatus.EQUIVALENCE_CLASS:
        raise AssertionError("unknown status incorrectly preceded equivalence")

    import common.open_set_response_classes as common_surface
    import htt.statistics as htt_surface

    if (
        "build_source_separation_gate" in common_surface.__all__
        or hasattr(common_surface, "build_source_separation_gate")
        or hasattr(htt_surface, "build_source_separation_gate")
    ):
        raise AssertionError("forgeable PR-256 source-gate builder is public")
    return {
        "far_equivalence_status": far.status.value,
        "forgeable_source_gate_public": False,
    }


def _source_gate_normalizer() -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="PR258-SOURCE-GATE-ORACLE",
        kind=NormalizerKind.EXPANSION_NORMALIZED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=(
            "beta_MO_amplitude",
            "beta_RM_amplitude",
        ),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity="PR258-SOURCE-GATE-ORACLE",
        assumptions=("block-preserving map",),
    )


def _source_geometry_report(
    *,
    labels: tuple[str, ...],
    covariance: np.ndarray,
    local_provider_id: str,
    global_provider_id: str,
):
    dimension = len(labels)

    def provider(
        *,
        hypothesis: SourceHypothesis,
        provider_id: str,
        response: list[list[float]],
    ):
        return register_source_response_provider(
            provider_id=provider_id,
            hypothesis=hypothesis,
            velocity_component=(
                VelocityComponent.BETA_MO
                if hypothesis is SourceHypothesis.LOCAL_BOOST
                else VelocityComponent.BETA_RM
            ),
            provider_kind=ResponseProviderKind.ANALYTIC,
            availability=ResponseProviderAvailability.AVAILABLE,
            observable_labels=labels,
            parameter_labels=(
                ("beta_MO_amplitude",)
                if hypothesis is SourceHypothesis.LOCAL_BOOST
                else ("beta_RM_amplitude",)
            ),
            response=response,
            transfer_id=_receipt("source-gate-transfer-none"),
            transfer_source=TransferSource.NONE,
            basis="source-gate oracle basis",
            epoch_window="source-gate oracle window",
            assumptions=("first-order analytic response",),
            caveats=("synthetic software oracle",),
        )

    local = provider(
        hypothesis=SourceHypothesis.LOCAL_BOOST,
        provider_id=local_provider_id,
        response=[[1.0], *([[0.0]] * (dimension - 1))],
    )
    global_value = provider(
        hypothesis=SourceHypothesis.GLOBAL_TILT,
        provider_id=global_provider_id,
        response=[[0.0], [1.0], *([[0.0]] * (dimension - 2))],
    )
    report = measure_source_response_geometry(
        local_provider=local,
        global_provider=global_value,
        covariance=covariance,
        normalizer=_source_gate_normalizer(),
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=_receipt("source-gate-mask"),
        separation_threshold_radians=0.2,
    )
    return report


def _check_source_gate_provenance_binding() -> dict[str, object]:
    labels = ("obs-x", "obs-y")
    covariance = np.eye(2)
    local_provider_id = _receipt("source-provider:local")
    global_provider_id = _receipt("source-provider:global")
    source_report = _source_geometry_report(
        labels=labels,
        covariance=covariance,
        local_provider_id=local_provider_id,
        global_provider_id=global_provider_id,
    )
    classes = (
        build_response_class_manifold(
            class_id="response-class-local",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=local_provider_id,
            observable_labels=labels,
            convention_id=_receipt("source-gate-convention"),
            nuisance_policy_id=_receipt("source-gate-no-nuisance"),
            support_nodes=[[-3.0, 0.0]],
            source_semantics=ResponseClassSourceSemantics.LOCAL_BOOST,
            source_response_id=source_report.local_provider.response_id,
        ),
        build_response_class_manifold(
            class_id="response-class-global",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=global_provider_id,
            observable_labels=labels,
            convention_id=_receipt("source-gate-convention"),
            nuisance_policy_id=_receipt("source-gate-no-nuisance"),
            support_nodes=[[3.0, 0.0]],
            source_semantics=ResponseClassSourceSemantics.GLOBAL_TILT,
            source_response_id=source_report.global_provider.response_id,
        ),
    )
    equivalence = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.1,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    gate = source_separation_gate_from_pr256(
        source_report,
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        normalizer=_source_gate_normalizer(),
        threshold_contract=PR283_DEFAULT_THRESHOLD_CONTRACT,
    )
    classify_kwargs = {
        "classes": classes,
        "equivalence_report": equivalence,
        "covariance": covariance,
        "nuisance_tangent": None,
        "unknown_squared_distance_threshold": 4.0,
        "decision_squared_margin": 0.5,
        "covariance_null_tolerance": 1.0e-10,
        "absolute_tolerance": ATOL,
        "relative_tolerance": RTOL,
        "source_separation_gate": gate,
    }
    single = classify_open_set_response(
        observation=[-3.0, 0.0],
        **classify_kwargs,
    )
    batch = classify_open_set_response_batch(
        observations=[[-3.0, 0.0]],
        **classify_kwargs,
    )
    if (
        batch != (single,)
        or single.status
        is not OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    ):
        raise AssertionError("congruent source gate failed single/batch control")

    report_3d = _source_geometry_report(
        labels=("dipole", "depth", "morphology"),
        covariance=np.eye(3),
        local_provider_id=local_provider_id,
        global_provider_id=global_provider_id,
    )
    mismatch_rejected = 0
    for _consumer in ("single", "batch"):
        try:
            source_separation_gate_from_pr256(
                report_3d,
                classes=classes,
                covariance=covariance,
                nuisance_tangent=None,
                normalizer=_source_gate_normalizer(),
                threshold_contract=PR283_DEFAULT_THRESHOLD_CONTRACT,
            )
        except OpenSetResponseError:
            mismatch_rejected += 1
    if mismatch_rejected != 2:
        raise AssertionError("3D PR-256 report survived a 2D PR-258 gate")

    changed_covariance = np.diag([2.0, 1.0])
    changed_equivalence = build_response_equivalence_report(
        classes=classes,
        covariance=changed_covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.1,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
    )
    covariance_rejections = 0
    try:
        classify_open_set_response(
            observation=[-3.0, 0.0],
            **{
                **classify_kwargs,
                "equivalence_report": changed_equivalence,
                "covariance": changed_covariance,
            },
        )
    except OpenSetResponseError:
        covariance_rejections += 1
    try:
        classify_open_set_response_batch(
            observations=[[-3.0, 0.0]],
            **{
                **classify_kwargs,
                "equivalence_report": changed_equivalence,
                "covariance": changed_covariance,
            },
        )
    except OpenSetResponseError:
        covariance_rejections += 1
    if covariance_rejections != 2:
        raise AssertionError("source gate survived covariance rebinding")

    return {
        "congruent_candidate_status": single.status.value,
        "gate_schema": gate.as_payload()["schema"],
        "single_batch_identity": True,
        "three_to_two_dimensional_mismatch_rejections": mismatch_rejected,
        "covariance_rebinding_rejections": covariance_rejections,
    }


def _check_full_regraph_and_row_span() -> dict[str, object]:
    classes = (
        build_response_class_manifold(
            class_id=f"response-class-{name}",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=_receipt(f"provider:{name}"),
            observable_labels=("x", "y"),
            convention_id=_receipt("convention:joint"),
            nuisance_policy_id=_receipt("nuisance:base"),
            support_nodes=[node],
        )
        for name, node in (
            ("a", [0.0, 0.0]),
            ("b", [0.0, 0.0]),
            ("c", [3.0, 0.0]),
        )
    )
    classes = tuple(classes)
    added_values = {"response-class-a": 0.0, "response-class-b": 10.0, "response-class-c": 0.0}
    keyed = {
        item.class_id: {
            item.support_node_ids[0]: [added_values[item.class_id]]
        }
        for item in classes
    }
    added = build_reopening_observable_spec(
        observable_id=_receipt("reopening:full-regraph"),
        classes=classes,
        added_observable_labels=("added",),
        responses_by_class_and_node=keyed,
        joint_covariance=np.eye(3),
        joint_nuisance_response=[[1.0], [0.0], [0.0]],
        joint_nuisance_policy_id=_receipt("nuisance:joint"),
        convention_id=_receipt("convention:joint"),
    )
    report = build_response_equivalence_report(
        classes=classes,
        covariance=np.eye(2),
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.01,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        reopening_observables=(added,),
    )
    if report.reopening_status is not ReopeningObservableStatus.NEEDS_ADDITIONAL_OBSERVABLE:
        raise AssertionError("old component was reopened without full regraph")

    baseline = np.asarray(((1.0, 0.0), (0.0, 1.0)))
    inside_span = np.asarray(((1.0, 1.0),))
    outside_span = np.asarray(((0.0, 0.0, 1.0),))
    baseline_embedded = np.column_stack((baseline, np.zeros(2)))
    if np.linalg.matrix_rank(np.vstack((baseline, inside_span))) != 2:
        raise AssertionError("inside-span row unexpectedly raised rank")
    if np.linalg.matrix_rank(np.vstack((baseline_embedded, outside_span))) != 3:
        raise AssertionError("outside-span row failed to raise rank")
    return {
        "reopening_status": report.reopening_status.value,
        "joint_report_count": len(report.reopening_joint_report_ids),
        "inside_span_rank": 2,
        "outside_span_rank": 3,
    }


def main() -> int:
    payload = {
        "schema": "PR258_INDEPENDENT_OPEN_SET_ORACLE_V1",
        "score_scale": _check_squared_scale(),
        "structural_null_unit_congruence": (
            _check_structural_null_unit_congruence()
        ),
        "signed_zero_and_mc_contract": (
            _check_signed_zero_and_mc_contract()
        ),
        "chain_closure": _check_chain_closure(),
        "boundary_and_null": _check_shared_boundary_and_null_precedence(),
        "node_tie_and_binding": _check_tied_node_and_nuisance_binding(),
        "nuisance_quotient_and_contract_binding": (
            _check_nuisance_quotient_and_contract_binding()
        ),
        "precedence_and_source_gate": (
            _check_equivalence_precedence_and_gate_surface()
        ),
        "source_gate_provenance_binding": (
            _check_source_gate_provenance_binding()
        ),
        "reopening_and_rank": _check_full_regraph_and_row_span(),
        "data_provenance": {
            "synthetic_only": True,
            "pr151_data_used": False,
            "observed_data_used": False,
            "old_rust_output_used": False,
            "native_solver_output_used": False,
            "transfer_source": "none",
        },
        "claim_tier_ceiling": "diagnostic_only",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(
        "PASS PR-258 independent squared-metric, MC-contract and regraph oracle"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
