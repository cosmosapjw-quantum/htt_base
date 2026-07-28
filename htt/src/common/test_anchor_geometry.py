from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from common.anchor_geometry import (
    AdditiveRadialMargin,
    AnchorAvailability,
    AnchorBlockSpec,
    AnchorBodySpec,
    AnchorFamily,
    AnchorFamilyKind,
    AnchorGaugeInterval,
    AnchorGaugeStatus,
    AnchorGeometryError,
    AnchorGeometryKind,
    AnchorMarginReport,
    AnchorMarginStatus,
    AnchorVector,
    BenchmarkMetric,
    DenominatorZeroStatus,
    MarginIntervalStatus,
    MesBenchmarkDisposition,
    MetricDirection,
    NormalizerAvailability,
    NormalizerBenchmarkReport,
    NormalizerEvaluation,
    NormalizerEvaluationStatus,
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
    PolytopeHalfspace,
    ScalingInvarianceStatus,
    build_anchor_margin_report,
    build_normalizer_benchmark,
    check_anchor_scaling_invariance,
    evaluate_anchor_gauge,
    j1_outer_envelope_counterexample,
    j2_dependence_counterexample,
)

DRAW_RECEIPT = "sha256:" + "a" * 64
PURPOSE = NormalizerPurpose.RESPONSE_CONDITIONING


def _vector(
    values: tuple[float, ...],
    *,
    labels: tuple[str, ...] | None = None,
    frame: str = "registered-frame",
) -> AnchorVector:
    if labels is None:
        labels = tuple(f"u{index}" for index in range(len(values)))
    return AnchorVector(
        vector_id="fixture-vector",
        coordinate_labels=labels,
        values=values,
        frame=frame,
        normalization="H-normalized",
        perturbative_order="linear",
        branch="fixture-branch",
    )


def _body_kwargs(labels: tuple[str, ...]) -> dict[str, object]:
    return {
        "coordinate_labels": labels,
        "frame": "registered-frame",
        "normalization": "H-normalized",
        "perturbative_order": "linear",
        "branch": "fixture-branch",
        "premise_identity": "FIXTURE-PREMISE-V1",
    }


def _ball(
    body_id: str,
    radii: tuple[float, ...],
) -> AnchorBodySpec:
    labels = tuple(f"u{index}" for index in range(len(radii)))
    return AnchorBodySpec(
        body_id=body_id,
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        blocks=tuple(
            AnchorBlockSpec(
                block_id=f"{body_id}-block-{index}",
                coordinate_indices=(index,),
                radius=radius,
            )
            for index, radius in enumerate(radii)
        ),
        **_body_kwargs(labels),
    )


def _normalizer_specs(
    *,
    mes_availability: NormalizerAvailability = NormalizerAvailability.AVAILABLE,
) -> tuple[NormalizerSpec, ...]:
    specs = []
    for index, kind in enumerate(NormalizerKind, start=1):
        availability = (
            mes_availability
            if kind is NormalizerKind.MES_ANCHORED
            else NormalizerAvailability.AVAILABLE
        )
        specs.append(
            NormalizerSpec(
                normalizer_id=kind.value.lower(),
                kind=kind,
                purposes=tuple(NormalizerPurpose),
                coordinate_labels=("u0", "u1"),
                coordinate_map=(
                    ((float(index), 0.0), (0.0, float(index + 1)))
                    if availability is NormalizerAvailability.AVAILABLE
                    else ()
                ),
                source_identity=f"FIXTURE-{kind.value}",
                availability=availability,
                unavailable_reason=(
                    None
                    if availability is NormalizerAvailability.AVAILABLE
                    else "typed MES channel unavailable"
                ),
            )
        )
    return tuple(specs)


def _evaluations(
    specs: tuple[NormalizerSpec, ...],
    *,
    receipt: str = DRAW_RECEIPT,
) -> tuple[NormalizerEvaluation, ...]:
    metric_values = {
        NormalizerKind.EXPANSION_NORMALIZED: (0.2, 0.7),
        NormalizerKind.MES_ANCHORED: (0.3, 0.8),
        NormalizerKind.FISHER_WHITENED: (0.1, 0.5),
        NormalizerKind.TEMPLATE_LIMIT: (0.4, 0.6),
        NormalizerKind.DYNAMICAL_BREAKDOWN: (0.2, 0.4),
        NormalizerKind.PRIOR_QUANTILE: (0.5, 0.9),
    }
    evaluations = []
    for spec in specs:
        conditioning, portability = metric_values[spec.kind]
        for purpose in NormalizerPurpose:
            if spec.availability is NormalizerAvailability.UNAVAILABLE:
                evaluations.append(
                    NormalizerEvaluation(
                        normalizer_id=spec.normalizer_id,
                        purpose=purpose,
                        status=NormalizerEvaluationStatus.UNAVAILABLE,
                        metrics=(),
                        rank_before=None,
                        rank_after=None,
                        denominator_zero_status=DenominatorZeroStatus.FAIL_CLOSED,
                        likelihood_invariance_error=None,
                        base_draws_receipt=receipt,
                    )
                )
                continue
            evaluations.append(
                NormalizerEvaluation(
                    normalizer_id=spec.normalizer_id,
                    purpose=purpose,
                    status=NormalizerEvaluationStatus.EVALUATED,
                    metrics=(
                        BenchmarkMetric(
                            metric_id="condition_number_scaled",
                            value=conditioning,
                            direction=MetricDirection.LOWER_IS_BETTER,
                            evidence_identity=(
                                f"{spec.normalizer_id}:{purpose.value}:condition"
                            ),
                        ),
                        BenchmarkMetric(
                            metric_id="portability_score",
                            value=portability,
                            direction=MetricDirection.HIGHER_IS_BETTER,
                            evidence_identity=(
                                f"{spec.normalizer_id}:{purpose.value}:portability"
                            ),
                        ),
                    ),
                    rank_before=2,
                    rank_after=2,
                    denominator_zero_status=DenominatorZeroStatus.FAIL_CLOSED,
                    likelihood_invariance_error=0.0,
                    base_draws_receipt=receipt,
                )
            )
    return tuple(evaluations)


def test_product_ball_uses_maximum_typed_block_ratio() -> None:
    body = AnchorBodySpec(
        body_id="product",
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        blocks=(
            AnchorBlockSpec(
                block_id="plane",
                coordinate_indices=(0, 1),
                radius=2.0,
            ),
            AnchorBlockSpec(
                block_id="axis",
                coordinate_indices=(2,),
                radius=4.0,
            ),
        ),
        **_body_kwargs(("u0", "u1", "u2")),
    )
    gauge = evaluate_anchor_gauge(body, _vector((3.0, 4.0, 8.0)))
    assert gauge.status is AnchorGaugeStatus.DEFINED
    assert gauge.lower == pytest.approx(2.5)
    assert gauge.upper == pytest.approx(2.5)

    margins = build_anchor_margin_report(gauge)
    assert margins.status is AnchorMarginStatus.DEFINED
    assert margins.additive_radial_margin.lower == pytest.approx(-1.5)
    assert margins.multiplicative_boundary_scale.lower == pytest.approx(0.4)
    assert margins.relative_boundary_growth.lower == pytest.approx(-0.6)
    assert margins.raw_anchor_excess.lower == pytest.approx(1.5)


def test_seeded_product_ball_unit_sublevel_property() -> None:
    rng = np.random.default_rng(20260728)
    for index in range(128):
        radii = tuple(float(value) for value in rng.uniform(0.1, 3.0, size=3))
        values = tuple(float(value) for value in rng.normal(size=3))
        body = _ball(f"property-{index}", radii)
        gauge = evaluate_anchor_gauge(body, _vector(values))
        direct_membership = all(
            abs(value) <= radius
            for value, radius in zip(values, radii)
        )
        assert (gauge.upper <= 1.0) is direct_membership


def test_origin_has_infinite_multiplicative_not_unit_additive_headroom() -> None:
    gauge = evaluate_anchor_gauge(_ball("unit", (1.0,)), _vector((0.0,)))
    margins = build_anchor_margin_report(gauge)
    assert margins.additive_radial_margin.lower == 1.0
    assert (
        margins.multiplicative_boundary_scale.status
        is MarginIntervalStatus.POSITIVE_INFINITY
    )
    assert margins.multiplicative_boundary_scale.lower is None
    assert margins.relative_boundary_growth.lower is None


def test_ellipsoid_and_certified_symmetric_polytope_gauges() -> None:
    ellipsoid = AnchorBodySpec(
        body_id="ellipse",
        geometry=AnchorGeometryKind.ELLIPSOID,
        quadratic_form=((0.25, 0.0), (0.0, 1.0 / 9.0)),
        **_body_kwargs(("u0", "u1")),
    )
    assert evaluate_anchor_gauge(
        ellipsoid, _vector((2.0, 0.0))
    ).lower == pytest.approx(1.0)

    polytope = AnchorBodySpec(
        body_id="box",
        geometry=AnchorGeometryKind.POLYTOPE,
        halfspaces=(
            PolytopeHalfspace((1.0, 0.0), 2.0),
            PolytopeHalfspace((-1.0, 0.0), 2.0),
            PolytopeHalfspace((0.0, 1.0), 4.0),
            PolytopeHalfspace((0.0, -1.0), 4.0),
        ),
        **_body_kwargs(("u0", "u1")),
    )
    assert evaluate_anchor_gauge(
        polytope, _vector((1.0, 2.0))
    ).lower == pytest.approx(0.5)


def test_polytope_must_be_bounded_and_centrally_symmetric() -> None:
    with pytest.raises(AnchorGeometryError, match="centrally symmetric"):
        AnchorBodySpec(
            body_id="one-sided",
            geometry=AnchorGeometryKind.POLYTOPE,
            halfspaces=(
                PolytopeHalfspace((1.0, 0.0), 1.0),
                PolytopeHalfspace((0.0, 1.0), 1.0),
            ),
            **_body_kwargs(("u0", "u1")),
        )


def test_product_ball_block_id_is_an_unambiguous_identity() -> None:
    with pytest.raises(AnchorGeometryError, match="block_id"):
        AnchorBodySpec(
            body_id="duplicate-block-id",
            geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
            blocks=(
                AnchorBlockSpec(
                    block_id="same",
                    coordinate_indices=(0,),
                    radius=1.0,
                ),
                AnchorBlockSpec(
                    block_id="same",
                    coordinate_indices=(1,),
                    radius=1.0,
                ),
            ),
            **_body_kwargs(("u0", "u1")),
        )


def test_finite_family_returns_interval_and_nonconvex_union_has_no_single_gauge() -> None:
    vector = _vector((0.5,))
    small = _ball("small", (1.0,))
    large = _ball("large", (2.0,))
    finite = AnchorFamily(
        family_id="finite",
        kind=AnchorFamilyKind.FINITE_CONDITIONAL,
        bodies=(small, large),
        nuisance_identity="finite-branch-id",
    )
    finite_gauge = evaluate_anchor_gauge(finite, vector)
    assert finite_gauge.status is AnchorGaugeStatus.FINITE_CONDITIONAL
    assert (finite_gauge.lower, finite_gauge.upper) == pytest.approx((0.25, 0.5))
    assert build_anchor_margin_report(
        finite_gauge
    ).status is AnchorMarginStatus.CONDITIONAL_INTERVAL
    equal_finite = AnchorFamily(
        family_id="equal-finite",
        kind=AnchorFamilyKind.FINITE_CONDITIONAL,
        bodies=(_ball("equal-a", (1.0,)), _ball("equal-b", (1.0,))),
        nuisance_identity="unresolved-equal-branches",
    )
    equal_gauge = evaluate_anchor_gauge(equal_finite, vector)
    assert equal_gauge.point_identified is True
    assert (
        build_anchor_margin_report(equal_gauge).status
        is AnchorMarginStatus.CONDITIONAL_INTERVAL
    )

    nonconvex = AnchorFamily(
        family_id="union",
        kind=AnchorFamilyKind.NONCONVEX_UNION,
        bodies=(small, large),
        nuisance_identity="conditional-union",
    )
    union_gauge = evaluate_anchor_gauge(nonconvex, vector)
    assert (
        union_gauge.status
        is AnchorGaugeStatus.NONCONVEX_CONDITIONAL_ONLY
    )
    assert union_gauge.status is not AnchorGaugeStatus.DEFINED


def test_continuous_nuisance_refuses_hidden_discretization() -> None:
    family = AnchorFamily(
        family_id="continuous",
        kind=AnchorFamilyKind.CONTINUOUS_CONDITIONAL,
        nuisance_identity="theta-in-[0,1]",
        optimizer_contract="registered convex optimizer required",
        coordinate_labels=("u0",),
        frame="registered-frame",
        normalization="H-normalized",
        perturbative_order="linear",
        branch="fixture-branch",
    )
    gauge = evaluate_anchor_gauge(family, _vector((0.5,)))
    assert gauge.status is AnchorGaugeStatus.OPTIMIZER_REQUIRED
    assert gauge.lower is None and gauge.upper is None
    assert build_anchor_margin_report(
        gauge
    ).status is AnchorMarginStatus.UNAVAILABLE

    with pytest.raises(AnchorGeometryError, match="hidden discretization"):
        replace(family, bodies=(_ball("forbidden-grid", (1.0,)),))
    mismatched = evaluate_anchor_gauge(
        family,
        _vector((0.5,), frame="different-frame"),
    )
    assert mismatched.status is AnchorGaugeStatus.CHANNEL_MISMATCH


def test_anchor_family_requires_one_typed_channel() -> None:
    different_frame = replace(
        _ball("different-frame", (1.0,)),
        frame="other-frame",
    )
    with pytest.raises(AnchorGeometryError, match="one typed channel"):
        AnchorFamily(
            family_id="mixed-channel",
            kind=AnchorFamilyKind.FINITE_CONDITIONAL,
            bodies=(_ball("canonical", (1.0,)), different_frame),
            nuisance_identity="invalid-mixed-channel",
        )


def test_missing_block_fails_closed_instead_of_becoming_zero() -> None:
    body = AnchorBodySpec(
        body_id="missing-block",
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        blocks=(
            AnchorBlockSpec(
                block_id="available",
                coordinate_indices=(0,),
                radius=1.0,
            ),
            AnchorBlockSpec(
                block_id="missing",
                coordinate_indices=(1,),
                radius=None,
                availability=AnchorAvailability.MISSING,
                unavailable_reason="no typed physical anchor",
            ),
        ),
        **_body_kwargs(("u0", "u1")),
    )
    gauge = evaluate_anchor_gauge(body, _vector((0.5, 0.0)))
    assert gauge.status is AnchorGaugeStatus.ANCHOR_UNAVAILABLE
    assert gauge.lower is None


def test_one_missing_conditional_body_invalidates_whole_family_interval() -> None:
    missing = AnchorBodySpec(
        body_id="withheld",
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        availability=AnchorAvailability.WITHHELD,
        unavailable_reason="derivation withheld",
        **_body_kwargs(("u0",)),
    )
    family = AnchorFamily(
        family_id="partially-missing-family",
        kind=AnchorFamilyKind.FINITE_CONDITIONAL,
        bodies=(_ball("available-body", (1.0,)), missing),
        nuisance_identity="finite-branch",
    )
    gauge = evaluate_anchor_gauge(family, _vector((0.5,)))
    assert gauge.status is AnchorGaugeStatus.ANCHOR_UNAVAILABLE
    assert gauge.conditional_values == ()


def test_channel_mismatch_fails_closed() -> None:
    gauge = evaluate_anchor_gauge(
        _ball("unit", (1.0,)),
        _vector((0.5,), frame="different-frame"),
    )
    assert gauge.status is AnchorGaugeStatus.CHANNEL_MISMATCH
    assert gauge.lower is None


@pytest.mark.parametrize(
    "bad",
    (
        (True,),
        (float("nan"),),
        (float("inf"),),
        ("1.0",),
        (1.0 + 0.0j,),
    ),
)
def test_anchor_vectors_reject_bool_nonfinite_text_and_complex(
    bad: tuple[object, ...],
) -> None:
    with pytest.raises(AnchorGeometryError):
        _vector(bad)  # type: ignore[arg-type]


def test_raw_excess_serialization_is_not_an_evalue() -> None:
    report = build_anchor_margin_report(
        evaluate_anchor_gauge(_ball("unit", (1.0,)), _vector((2.0,)))
    )
    payload = report.as_payload()
    assert payload["raw_anchor_excess"]["lower"] == 1.0
    assert "e_value" not in payload
    assert payload["automatic_evidence_status"].startswith("FORBIDDEN")
    with pytest.raises(AnchorGeometryError, match="automatic evidence"):
        replace(report, automatic_evidence_status="CALIBRATED_E_VALUE")


def test_gauge_interval_rejects_inconsistent_external_construction() -> None:
    with pytest.raises(AnchorGeometryError, match="conditional_values"):
        AnchorGaugeInterval(
            anchor_id="empty-numeric",
            vector_id="fixture",
            lower=0.0,
            upper=0.0,
            status=AnchorGaugeStatus.DEFINED,
        )
    with pytest.raises(AnchorGeometryError, match="extrema"):
        AnchorGaugeInterval(
            anchor_id="inconsistent",
            vector_id="fixture",
            lower=0.0,
            upper=1.0,
            status=AnchorGaugeStatus.FINITE_CONDITIONAL,
            conditional_values=(("branch-a", 0.25), ("branch-b", 0.75)),
        )
    with pytest.raises(AnchorGeometryError, match="point identified"):
        AnchorGaugeInterval(
            anchor_id="not-a-point",
            vector_id="fixture",
            lower=0.25,
            upper=0.75,
            status=AnchorGaugeStatus.DEFINED,
            conditional_values=(("branch-a", 0.25), ("branch-b", 0.75)),
        )
    with pytest.raises(AnchorGeometryError, match="exactly one"):
        AnchorGaugeInterval(
            anchor_id="conditional-disguised-as-defined",
            vector_id="fixture",
            lower=0.5,
            upper=0.5,
            status=AnchorGaugeStatus.DEFINED,
            conditional_values=(("branch-a", 0.5), ("branch-b", 0.5)),
        )


def test_margin_report_rejects_intervals_not_derived_from_gauge() -> None:
    valid = build_anchor_margin_report(
        evaluate_anchor_gauge(_ball("unit", (1.0,)), _vector((0.5,)))
    )
    with pytest.raises(AnchorGeometryError, match="derived exactly"):
        replace(
            valid,
            additive_radial_margin=AdditiveRadialMargin(
                lower=999.0,
                upper=999.0,
                status=MarginIntervalStatus.FINITE,
            ),
        )


def test_invertible_scaling_preserves_rank_and_gaussian_likelihood() -> None:
    report = check_anchor_scaling_invariance(
        state=(0.4, -0.2),
        response=((1.0, 2.0), (0.5, -1.0), (1.5, 0.25)),
        anchor_scaling=((2.0, 0.25), (0.0, 0.5)),
        observed=(0.7, -0.1, 0.8),
        covariance=((1.0, 0.1, 0.0), (0.1, 1.5, 0.2), (0.0, 0.2, 2.0)),
    )
    assert report.status is ScalingInvarianceStatus.PASS
    assert report.original_rank == report.transformed_rank == 2
    assert report.absolute_error <= 1e-12
    assert "information gain from scaling" in report.forbidden_use

    with pytest.raises(AnchorGeometryError, match="invertible"):
        check_anchor_scaling_invariance(
            state=(0.4, -0.2),
            response=((1.0, 2.0),),
            anchor_scaling=((1.0, 0.0), (0.0, 0.0)),
            observed=(0.7,),
            covariance=((1.0,),),
        )


def test_seeded_invertible_scalings_never_create_rank() -> None:
    rng = np.random.default_rng(254)
    for _ in range(64):
        response = rng.normal(size=(5, 3))
        scaling = rng.normal(size=(3, 3))
        while abs(float(np.linalg.det(scaling))) < 0.1:
            scaling = rng.normal(size=(3, 3))
        report = check_anchor_scaling_invariance(
            state=rng.normal(size=3),
            response=response,
            anchor_scaling=scaling,
            observed=rng.normal(size=5),
            covariance=np.eye(5),
            atol=1e-9,
        )
        assert report.status is ScalingInvarianceStatus.PASS
        assert report.original_rank == report.transformed_rank


def test_purpose_specific_pareto_report_has_no_universal_score() -> None:
    specs = _normalizer_specs()
    report = build_normalizer_benchmark(
        specs=specs,
        evaluations=_evaluations(specs),
    )
    payload = report.as_payload()
    assert report.mes_disposition is MesBenchmarkDisposition.ONE_ANCHOR_AMONG_FAMILY
    assert payload["universal_winner"] is None
    assert payload["scalar_score"] is None
    assert "information gain from invertible scaling" in report.forbidden_use
    front = report.pareto_fronts[0].normalizer_ids
    assert "mes_anchored" in front
    assert "fisher_whitened" in front


def test_benchmark_requires_same_draws_and_rank_preservation() -> None:
    specs = _normalizer_specs()
    evaluations = list(_evaluations(specs))
    evaluations[-1] = replace(
        evaluations[-1],
        base_draws_receipt="sha256:" + "b" * 64,
    )
    with pytest.raises(AnchorGeometryError, match="same base draws"):
        build_normalizer_benchmark(specs=specs, evaluations=evaluations)

    with pytest.raises(AnchorGeometryError, match="must not change response rank"):
        replace(_evaluations(specs)[0], rank_after=3)


def test_benchmark_requires_shared_channel_purposes_and_zero_probe() -> None:
    specs = _normalizer_specs()
    changed_channel = list(specs)
    changed_channel[-1] = replace(
        changed_channel[-1],
        coordinate_labels=("other-0", "other-1"),
    )
    with pytest.raises(AnchorGeometryError, match="same coordinate channel"):
        build_normalizer_benchmark(
            specs=changed_channel,
            evaluations=_evaluations(tuple(changed_channel)),
        )

    changed_purposes = list(specs)
    changed_purposes[-1] = replace(
        changed_purposes[-1],
        purposes=(NormalizerPurpose.PREMISE_STRESS,),
    )
    with pytest.raises(AnchorGeometryError, match="complete shared purpose"):
        build_normalizer_benchmark(
            specs=changed_purposes,
            evaluations=_evaluations(tuple(changed_purposes)),
        )

    evaluations = list(_evaluations(specs))
    evaluations[0] = replace(
        evaluations[0],
        denominator_zero_status=DenominatorZeroStatus.NOT_APPLICABLE,
    )
    with pytest.raises(AnchorGeometryError, match="must fail closed"):
        build_normalizer_benchmark(specs=specs, evaluations=evaluations)


def test_unavailable_mes_is_reported_not_replaced() -> None:
    specs = _normalizer_specs(
        mes_availability=NormalizerAvailability.UNAVAILABLE
    )
    report = build_normalizer_benchmark(
        specs=specs,
        evaluations=_evaluations(specs),
    )
    assert report.mes_disposition is MesBenchmarkDisposition.UNAVAILABLE


def test_benchmark_report_constructor_cannot_bypass_builder_invariants() -> None:
    with pytest.raises(AnchorGeometryError, match="must not be empty"):
        NormalizerBenchmarkReport(
            specs=(),
            evaluations=(),
            pareto_fronts=(),
            mes_disposition=(
                MesBenchmarkDisposition.PRIMARY_FOR_REGISTERED_PURPOSES
            ),
            base_draws_receipt=DRAW_RECEIPT,
        )

    valid = build_normalizer_benchmark(
        specs=_normalizer_specs(),
        evaluations=_evaluations(_normalizer_specs()),
    )
    with pytest.raises(AnchorGeometryError, match="mes_disposition"):
        replace(
            valid,
            mes_disposition=(
                MesBenchmarkDisposition.PRIMARY_FOR_REGISTERED_PURPOSES
            ),
        )
    with pytest.raises(AnchorGeometryError, match="Pareto fronts"):
        replace(valid, pareto_fronts=())


def test_j1_and_j2_counterexamples_restrict_only_their_exact_scope() -> None:
    j1 = j1_outer_envelope_counterexample()
    j2 = j2_dependence_counterexample()
    assert j1.gate_outcome == "COUNTEREXAMPLE_FOUND"
    assert dict(j1.exact_facts)["rho_a_at_1_over_2"] == "1/2"
    assert dict(j1.exact_facts)["rho_b_at_1_over_2"] == "1/4"
    assert j2.gate_outcome == "COUNTEREXAMPLE_FOUND"
    assert dict(j2.exact_facts)["comonotone_exceedance_probability"] == "0"
    assert (
        dict(j2.exact_facts)["countermonotone_exceedance_probability"]
        == "1/2"
    )
    assert (
        dict(j2.exact_facts)["conclusion"]
        == "equal_marginals_do_not_determine_raw_ratio_exceedance"
    )
    fixed_denominator_exceedance = {
        sum(value / 1.5 > 1.0 for value in ordering) / len(ordering)
        for ordering in ((1.0, 2.0), (2.0, 1.0))
    }
    assert fixed_denominator_exceedance == {0.5}
    assert "narrower physical MES" in j1.forbidden_use[0]
    assert "every registered joint-law test" in j2.forbidden_use[0]


def test_zero_radius_and_singular_normalizer_are_destructive_ablations() -> None:
    with pytest.raises(AnchorGeometryError, match="positive"):
        AnchorBlockSpec(
            block_id="zero-radius",
            coordinate_indices=(0,),
            radius=0.0,
        )
    with pytest.raises(AnchorGeometryError, match="invertible"):
        NormalizerSpec(
            normalizer_id="singular",
            kind=NormalizerKind.MES_ANCHORED,
            purposes=(PURPOSE,),
            coordinate_labels=("u0", "u1"),
            coordinate_map=((1.0, 0.0), (0.0, 0.0)),
            source_identity="SINGULAR-MUTATION",
        )
