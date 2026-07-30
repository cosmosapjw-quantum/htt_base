"""PR-264 vector/tensor departure-statistics successor contracts."""

from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from common.anchor_geometry import (
    AnchorBlockSpec,
    AnchorBodySpec,
    AnchorFamily,
    AnchorFamilyKind,
    AnchorGeometryKind,
    AnchorVector,
    PolytopeHalfspace,
)
from common.joint_anisotropy_state import (
    AccelerationNormalization,
    BetaSemanticRole,
    CongruenceKinematics,
    GeometryState,
    JointAnisotropyState,
    JointStateSourceKind,
    UnitsConvention,
    VelocityNormalization,
    apply_o3_action,
    build_velocity_frame_bundle,
    missing_component,
)
from common.orbit_nonlinearity import (
    O3Transform,
    STF5_CARTESIAN_BASIS,
)
from common.tensor_departure_statistics import (
    CertifiedFunctionalPushforward,
    DirectionalRatioStatus,
    LegacyCompatibilityStatus,
    OCCUPANCY_MEASURE_KIND,
    OccupancyMeasureStatus,
    PushforwardSummaryStatus,
    SUPPORT_CATALOGUE_STATUS,
    ScalarizationPolicy,
    SupportUtilizationStatus,
    TENSOR_DEPARTURE_CLAIM_CEILING,
    TensorDepartureStatisticsError,
    build_certified_functional_pushforward,
    build_legacy_xqpi_fg_view,
    build_occupancy_measure,
    build_support_utilization_profile,
)
from common.tensor_functionals import (
    FunctionalStressStatus,
    TensorFunctionalOperator,
    TensorFunctionalResult,
    build_tensor_functional_spec,
    evaluate_tensor_functional,
)
from common.transfer_registry import TransferSource


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/research_program/vector_tensor/pr264_spec.yaml"
BACKLOG_PATH = ROOT / "docs/codex_handoff/pr_backlog.yaml"
FRAME = "PR264 registered Cartesian tetrad"
CONGRUENCE = "PR264 registered matter congruence"
EPOCH = "PR264 synthetic epoch"
SCALE = "PR264 synthetic averaging scale"
ORDER = "PR264 diagnostic tensor order"
NORMALIZATION = "PR264_FUNCTIONAL_COORDINATES_V1"
BRANCH = "PRE_SOLVER_DIAGNOSTIC"


def _joint(
    scale: float = 1.0,
    *,
    acceleration_missing: bool = False,
) -> JointAnisotropyState:
    acceleration = (
        missing_component(
            "acceleration_polar3",
            "acceleration unavailable in PR-264 fixture",
            required_for=("acceleration functional",),
        )
        if acceleration_missing
        else (0.01 * scale, -0.02 * scale, 0.03 * scale)
    )
    kinematics = CongruenceKinematics(
        sigma_stf5=tuple(
            scale * value
            for value in (0.2, -0.1, 0.03, -0.04, 0.05)
        ),
        omega_axial3=tuple(
            scale * value for value in (0.1, -0.2, 0.3)
        ),
        acceleration_polar3=acceleration,
        frame=FRAME,
        congruence_id=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=ORDER,
        acceleration_normalization=(
            None
            if acceleration_missing
            else AccelerationNormalization.A_OVER_C_THETA
        ),
    )
    velocity = build_velocity_frame_bundle(
        beta_RO=(0.003, 0.001, -0.001),
        beta_RM=(0.001, 0.001, 0.0),
        beta_MO=(0.002, 0.0, -0.001),
        coordinate_frame=FRAME,
        radiation_frame_id="PR264 radiation frame",
        matter_frame_id="PR264 matter frame",
        observer_frame_id="PR264 observer frame",
        basis=STF5_CARTESIAN_BASIS,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        first_order_beta_ceiling=0.01,
    )
    geometry = GeometryState(
        delta_omega_k=-0.02,
        frame=FRAME,
        congruence_id=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        perturbative_order=ORDER,
    )
    return JointAnisotropyState(
        congruence_kinematics=kinematics,
        velocity_frames=velocity,
        geometry_state=geometry,
        frame=FRAME,
        congruence=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        perturbative_order=ORDER,
        beta_semantic_role=BetaSemanticRole.DIRECT_STATE,
        transfer_source=TransferSource.NONE,
        transfer_spec=None,
        source_kind=JointStateSourceKind.DIRECT,
        source_identity=f"PR264-DIRECT-{scale.hex()}-{acceleration_missing}",
    )


def _spec(operator: TensorFunctionalOperator, anchor_id: str):
    return build_tensor_functional_spec(
        functional_id=f"pr264.{operator.value.lower()}",
        operator=operator,
        frame=FRAME,
        congruence=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        normalization=NORMALIZATION,
        perturbative_order=ORDER,
        branch=BRANCH,
        anchor_id=anchor_id,
    )


def _ball(spec, radius: float = 1.0) -> AnchorBodySpec:
    return AnchorBodySpec(
        body_id=spec.anchor_id,
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        coordinate_labels=spec.coordinate_labels,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
        premise_identity="PR264 REGISTERED SYNTHETIC PREMISE",
        blocks=(
            AnchorBlockSpec(
                block_id="all",
                coordinate_indices=tuple(
                    range(math.prod(spec.output_shape))
                ),
                radius=radius,
            ),
        ),
    )


def _stf_ellipsoid(spec, radius: float = 1.0) -> AnchorBodySpec:
    matrix = np.asarray(
        (
            (2.0, 1.0, 0.0, 0.0, 0.0),
            (1.0, 2.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 2.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 2.0, 0.0),
            (0.0, 0.0, 0.0, 0.0, 2.0),
        )
    ) / radius**2
    return AnchorBodySpec(
        body_id=spec.anchor_id,
        geometry=AnchorGeometryKind.ELLIPSOID,
        coordinate_labels=spec.coordinate_labels,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
        premise_identity="PR264 REGISTERED STF PREMISE",
        quadratic_form=tuple(tuple(value for value in row) for row in matrix),
    )


def _functional_family():
    scalar = _spec(TensorFunctionalOperator.TR_SIGMA2, "anchor.scalar")
    vector = _spec(TensorFunctionalOperator.OMEGA_AXIAL3, "anchor.vector")
    tensor = _spec(TensorFunctionalOperator.SIGMA_STF5, "anchor.tensor")
    return (
        (scalar, _ball(scalar, radius=1.0)),
        (vector, _ball(vector, radius=1.0)),
        (tensor, _stf_ellipsoid(tensor, radius=1.0)),
    )


def _rows(scales=(0.5, 1.0, 1.5)):
    family = _functional_family()
    return tuple(
        tuple(
            evaluate_tensor_functional(_joint(scale), spec, anchor=anchor)
            for spec, anchor in family
        )
        for scale in scales
    )


def _policies(rows):
    return {
        rows[0][0].spec.functional_id: ScalarizationPolicy.SCALAR_IDENTITY,
        rows[0][1].spec.functional_id: ScalarizationPolicy.EUCLIDEAN_NORM,
        rows[0][2].spec.functional_id: ScalarizationPolicy.STF_FROBENIUS_NORM,
    }


def _pushforward(scales=(0.5, 1.0, 1.5)):
    rows = _rows(scales)
    return build_certified_functional_pushforward(
        pushforward_id="PR264-SYNTHETIC-PUSHFORWARD",
        samples=rows,
        scalarization_policies=_policies(rows),
    )


def _channel_vector(
    vector_id: str,
    values,
    *,
    frame: str = FRAME,
) -> AnchorVector:
    values = tuple(values)
    return AnchorVector(
        vector_id=vector_id,
        coordinate_labels=tuple(
            f"support:{index}" for index in range(len(values))
        ),
        values=values,
        frame=frame,
        normalization=NORMALIZATION,
        perturbative_order=ORDER,
        branch=BRANCH,
    )


def _support_ball(
    dimension: int,
    radius: float = 1.0,
    *,
    frame: str = FRAME,
) -> AnchorBodySpec:
    labels = tuple(f"support:{index}" for index in range(dimension))
    return AnchorBodySpec(
        body_id=f"PR264-SUPPORT-BALL-{dimension}-{radius.hex()}",
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        coordinate_labels=labels,
        frame=frame,
        normalization=NORMALIZATION,
        perturbative_order=ORDER,
        branch=BRANCH,
        premise_identity="PR264 SUPPORT PREMISE",
        blocks=(
            AnchorBlockSpec(
                block_id="all",
                coordinate_indices=tuple(range(dimension)),
                radius=radius,
            ),
        ),
    )


def test_spec_and_backlog_bind_the_required_pr264_contract() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    backlog = yaml.safe_load(BACKLOG_PATH.read_text())
    card = next(card for card in backlog["prs"] if card["id"] == "PR-264")
    assert spec["work_unit_id"] == "PR-264"
    assert spec["dependencies"] == ["PR-262", "PR-263"]
    assert card["depends"] == ["PR-262", "PR-263"]
    assert spec["claim_boundary"]["ceiling"] == "diagnostic_only"
    assert {
        "CertifiedFunctionalPushforward",
        "SupportUtilizationProfile",
        "OccupancyMeasure",
        "LegacyXQPiFGView",
    } <= set(spec["public_contract"]["types"])


def test_pushforward_keeps_raw_x_q_points_bounds_and_summaries_separate() -> None:
    rows = _rows()
    result = build_certified_functional_pushforward(
        pushforward_id="PR264-PUSHFORWARD",
        samples=rows,
        scalarization_policies=_policies(rows),
        quantile_levels=(0.25, 0.5, 0.75),
    )
    assert result.summary_status is PushforwardSummaryStatus.DEFINED
    assert result.means is not None
    assert result.covariance is not None
    assert result.quantiles_by_functional is not None
    assert result.raw_sample_by_functional[0][1] == rows[0][1].value
    assert result.sample_by_functional[0][1] == pytest.approx(
        np.linalg.norm(rows[0][1].value)
    )
    assert result.q_point_by_functional[0][0] == pytest.approx(
        rows[0][0].stress.point_estimate
    )
    assert result.q_bounds_by_functional[0][0] == pytest.approx(
        (
            rows[0][0].stress.point_estimate,
            rows[0][0].stress.point_estimate,
        )
    )
    assert result.claim_ceiling == TENSOR_DEPARTURE_CLAIM_CEILING
    assert "content_id" in result.as_payload()


def test_pushforward_is_sample_wise_and_never_substitutes_ratio_of_means() -> None:
    result = _pushforward((0.25, 0.75, 1.5))
    scalar_q = tuple(row[0] for row in result.q_point_by_functional)
    assert scalar_q == pytest.approx(
        tuple(_rows((scale,))[0][0].stress.point_estimate for scale in (0.25, 0.75, 1.5))
    )
    assert result.means[0] == pytest.approx(
        sum(row[0] for row in result.sample_by_functional) / 3.0
    )
    assert "ratio_of_means" not in result.as_payload()


def test_non_scalar_scalarization_must_be_explicit_and_type_compatible() -> None:
    rows = _rows()
    missing = dict(_policies(rows))
    missing.pop(rows[0][2].spec.functional_id)
    with pytest.raises(
        TensorDepartureStatisticsError, match="every functional"
    ):
        build_certified_functional_pushforward(
            pushforward_id="PR264-MISSING-POLICY",
            samples=rows,
            scalarization_policies=missing,
        )
    bad = dict(_policies(rows))
    bad[rows[0][2].spec.functional_id] = ScalarizationPolicy.EUCLIDEAN_NORM
    with pytest.raises(
        TensorDepartureStatisticsError, match="polar or axial"
    ):
        build_certified_functional_pushforward(
            pushforward_id="PR264-BAD-POLICY",
            samples=rows,
            scalarization_policies=bad,
        )


def test_missing_component_remains_none_and_blocks_derived_summaries() -> None:
    spec = _spec(
        TensorFunctionalOperator.ACCELERATION_POLAR3,
        "anchor.acceleration",
    )
    anchor = _ball(spec)
    rows = (
        (evaluate_tensor_functional(_joint(), spec, anchor=anchor),),
        (
            evaluate_tensor_functional(
                _joint(acceleration_missing=True), spec, anchor=anchor
            ),
        ),
    )
    result = build_certified_functional_pushforward(
        pushforward_id="PR264-PARTIAL",
        samples=rows,
        scalarization_policies={
            spec.functional_id: ScalarizationPolicy.EUCLIDEAN_NORM
        },
    )
    assert result.sample_by_functional[1] == (None,)
    assert result.q_point_by_functional[1] == (None,)
    assert result.means is None
    assert result.covariance is None
    assert result.summary_status is PushforwardSummaryStatus.PARTIAL_MISSING


def test_conditional_anchor_has_bounds_but_no_fabricated_q_point() -> None:
    spec = _spec(TensorFunctionalOperator.OMEGA2, "anchor.family")
    body_a = replace(_ball(spec, radius=1.0), body_id="anchor.a")
    body_b = replace(_ball(spec, radius=2.0), body_id="anchor.b")
    family = AnchorFamily(
        family_id="anchor.family",
        kind=AnchorFamilyKind.FINITE_CONDITIONAL,
        bodies=(body_a, body_b),
        nuisance_identity="PR264 finite anchor nuisance",
    )
    value = evaluate_tensor_functional(_joint(), spec, anchor=family)
    assert value.stress.status is FunctionalStressStatus.CONDITIONAL
    result = build_certified_functional_pushforward(
        pushforward_id="PR264-CONDITIONAL",
        samples=((value,),),
        scalarization_policies={
            spec.functional_id: ScalarizationPolicy.SCALAR_IDENTITY
        },
    )
    assert result.q_point_by_functional == ((None,),)
    assert result.q_bounds_by_functional[0][0] is not None


def test_vector_and_tensor_scalarizations_are_o3_covariant() -> None:
    state = _joint()
    transform = O3Transform(
        matrix=((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        transform_id="PR264-Z-QUARTER-TURN",
        coordinate_frame=FRAME,
    )
    rotated = apply_o3_action(state, transform)
    family = _functional_family()[1:]
    rows = tuple(
        tuple(
            evaluate_tensor_functional(candidate, spec, anchor=anchor)
            for spec, anchor in family
        )
        for candidate in (state, rotated)
    )
    result = build_certified_functional_pushforward(
        pushforward_id="PR264-O3",
        samples=rows,
        scalarization_policies={
            rows[0][0].spec.functional_id: ScalarizationPolicy.EUCLIDEAN_NORM,
            rows[0][1].spec.functional_id: (
                ScalarizationPolicy.STF_FROBENIUS_NORM
            ),
        },
    )
    assert result.sample_by_functional[0] == pytest.approx(
        result.sample_by_functional[1], rel=1e-12, abs=1e-12
    )
    assert result.q_point_by_functional[0] == pytest.approx(
        result.q_point_by_functional[1], rel=1e-12, abs=1e-12
    )


def test_support_profile_scalar_singleton_reduces_to_anchor_gauge() -> None:
    anchor = _support_ball(1, radius=2.0)
    point = _channel_vector("point", (0.5,))
    directions = (
        _channel_vector("plus", (1.0,)),
        _channel_vector("minus", (-1.0,)),
    )
    profile = build_support_utilization_profile(
        identified_set_id="PR264-SCALAR-SINGLETON",
        identified_points=(point,),
        anchor=anchor,
        directions=directions,
    )
    assert profile.status is SupportUtilizationStatus.DEFINED
    assert profile.signed_support_ratios == pytest.approx((0.25, -0.25))
    assert profile.antipodal_support_ratios == pytest.approx((0.25, 0.25))
    assert profile.maximum_utilization == pytest.approx(0.25)
    assert profile.maximum_registered_utilization == pytest.approx(0.25)
    assert profile.direction_catalogue_status == SUPPORT_CATALOGUE_STATUS
    assert profile.witness_point_ids == ("point",)


def test_support_profile_is_rotation_covariant_for_ball_anchor() -> None:
    rotation = np.asarray(
        ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    )
    points = (
        np.asarray((0.2, 0.4, -0.1)),
        np.asarray((-0.3, 0.1, 0.2)),
    )
    directions = (
        np.asarray((1.0, 0.0, 0.0)),
        np.asarray((0.0, 1.0, 1.0)),
    )

    def build(prefix, matrix):
        return build_support_utilization_profile(
            identified_set_id=f"PR264-{prefix}",
            identified_points=tuple(
                _channel_vector(f"{prefix}-p{i}", matrix @ value)
                for i, value in enumerate(points)
            ),
            anchor=_support_ball(3, radius=1.25),
            directions=tuple(
                _channel_vector(f"{prefix}-u{i}", matrix @ value)
                for i, value in enumerate(directions)
            ),
        )

    base = build("BASE", np.eye(3))
    turned = build("TURNED", rotation)
    assert turned.signed_support_ratios == pytest.approx(
        base.signed_support_ratios, rel=1e-12, abs=1e-12
    )
    assert turned.antipodal_support_ratios == pytest.approx(
        base.antipodal_support_ratios, rel=1e-12, abs=1e-12
    )
    assert turned.maximum_utilization == pytest.approx(
        base.maximum_utilization, rel=1e-12, abs=1e-12
    )


def test_zero_direction_is_typed_denominator_collapse_not_zero_ratio() -> None:
    profile = build_support_utilization_profile(
        identified_set_id="PR264-ZERO-DIRECTION",
        identified_points=(_channel_vector("point", (0.2, -0.1)),),
        anchor=_support_ball(2),
        directions=(
            _channel_vector("zero", (0.0, 0.0)),
            _channel_vector("x", (1.0, 0.0)),
        ),
    )
    assert (
        profile.status
        is SupportUtilizationStatus.PARTIAL_DENOMINATOR_COLLAPSE
    )
    assert (
        profile.directional_statuses[0]
        is DirectionalRatioStatus.DENOMINATOR_COLLAPSE
    )
    assert profile.signed_support_ratios[0] is None
    assert profile.maximum_utilization == pytest.approx(math.sqrt(0.05))


def test_zero_identified_support_is_valid_but_missing_set_is_not_imputed() -> None:
    anchor = _support_ball(2)
    zero = build_support_utilization_profile(
        identified_set_id="PR264-ZERO-POINT",
        identified_points=(_channel_vector("zero-point", (0.0, 0.0)),),
        anchor=anchor,
        directions=(_channel_vector("x", (1.0, 0.0)),),
    )
    assert zero.maximum_utilization == 0.0
    assert zero.signed_support_ratios == (0.0,)
    missing = build_support_utilization_profile(
        identified_set_id="PR264-MISSING-SET",
        identified_points=(),
        anchor=anchor,
        directions=(_channel_vector("x", (1.0, 0.0)),),
        missing_reason="required tensor channel is absent",
    )
    assert missing.status is SupportUtilizationStatus.MISSING_IDENTIFIED_SET
    assert missing.maximum_utilization is None
    assert missing.signed_support_ratios == (None,)


def test_support_channel_mismatch_fails_closed() -> None:
    profile = build_support_utilization_profile(
        identified_set_id="PR264-MISMATCH",
        identified_points=(
            _channel_vector("point", (0.1, 0.2), frame="wrong frame"),
        ),
        anchor=_support_ball(2),
        directions=(_channel_vector("x", (1.0, 0.0)),),
    )
    assert profile.status is SupportUtilizationStatus.CHANNEL_MISMATCH
    assert profile.maximum_utilization is None


def test_ellipsoid_and_polytope_support_match_registered_geometry() -> None:
    labels = ("support:0", "support:1")
    ellipsoid = AnchorBodySpec(
        body_id="PR264-ELLIPSOID",
        geometry=AnchorGeometryKind.ELLIPSOID,
        coordinate_labels=labels,
        frame=FRAME,
        normalization=NORMALIZATION,
        perturbative_order=ORDER,
        branch=BRANCH,
        premise_identity="PR264 ELLIPSOID",
        quadratic_form=((4.0, 0.0), (0.0, 1.0)),
    )
    halfspaces = tuple(
        PolytopeHalfspace(normal=normal, bound=1.0)
        for normal in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0))
    )
    polytope = AnchorBodySpec(
        body_id="PR264-POLYTOPE",
        geometry=AnchorGeometryKind.POLYTOPE,
        coordinate_labels=labels,
        frame=FRAME,
        normalization=NORMALIZATION,
        perturbative_order=ORDER,
        branch=BRANCH,
        premise_identity="PR264 POLYTOPE",
        halfspaces=halfspaces,
    )
    point = _channel_vector("point", (0.25, 0.5))
    direction = _channel_vector("diagonal", (1.0, 1.0))
    ellipse_profile = build_support_utilization_profile(
        identified_set_id="ellipse",
        identified_points=(point,),
        anchor=ellipsoid,
        directions=(direction,),
    )
    box_profile = build_support_utilization_profile(
        identified_set_id="box",
        identified_points=(point,),
        anchor=polytope,
        directions=(direction,),
    )
    assert ellipse_profile.anchor_supports == pytest.approx(
        (math.sqrt(1.25),)
    )
    assert ellipse_profile.maximum_utilization == pytest.approx(
        math.sqrt(0.5)
    )
    assert box_profile.anchor_supports == pytest.approx((2.0,))
    assert box_profile.maximum_utilization == pytest.approx(0.5)


@pytest.mark.parametrize("seed", range(12))
def test_randomized_ball_support_gauge_duality_and_scaling(seed: int) -> None:
    rng = np.random.default_rng(seed)
    point = rng.normal(size=3)
    direction = rng.normal(size=3)
    radius = float(rng.uniform(0.2, 2.0))

    def profile(scale: float):
        return build_support_utilization_profile(
            identified_set_id=f"PR264-RANDOM-{seed}-{scale}",
            identified_points=(
                _channel_vector("point", scale * point),
            ),
            anchor=_support_ball(3, radius=scale * radius),
            directions=(_channel_vector("direction", direction),),
        )

    base = profile(1.0)
    rescaled = profile(7.0)
    assert base.maximum_utilization == pytest.approx(
        np.linalg.norm(point) / radius
    )
    assert rescaled.maximum_utilization == pytest.approx(
        base.maximum_utilization, rel=1e-12, abs=1e-12
    )
    assert rescaled.signed_support_ratios == pytest.approx(
        base.signed_support_ratios, rel=1e-12, abs=1e-12
    )


def test_occupancy_measure_is_empirical_monotone_and_not_physical() -> None:
    pushforward = _pushforward()
    functional_id = pushforward.functional_ids[0]
    measure = build_occupancy_measure(
        measure_id="PR264-LEVEL-SET-MASS",
        pushforward=pushforward,
        functional_id=functional_id,
        thresholds=(0.0, 0.05, 0.2, 1.0),
    )
    assert measure.status is OccupancyMeasureStatus.DEFINED
    assert measure.measure_kind == OCCUPANCY_MEASURE_KIND
    assert measure.empirical_level_set_mass is not None
    assert all(
        left >= right
        for left, right in zip(
            measure.empirical_level_set_mass,
            measure.empirical_level_set_mass[1:],
        )
    )
    assert any(
        "physical occupancy" in phrase for phrase in measure.forbidden_use
    )


def test_signed_functional_cannot_create_occupancy_measure() -> None:
    spec = _spec(TensorFunctionalOperator.TR_SIGMA3, "anchor.signed")
    anchor = _ball(spec)
    row = (evaluate_tensor_functional(_joint(), spec, anchor=anchor),)
    pushforward = build_certified_functional_pushforward(
        pushforward_id="PR264-SIGNED",
        samples=(row,),
        scalarization_policies={
            spec.functional_id: ScalarizationPolicy.SCALAR_IDENTITY
        },
    )
    measure = build_occupancy_measure(
        measure_id="PR264-SIGNED-REFUSAL",
        pushforward=pushforward,
        functional_id=spec.functional_id,
        thresholds=(0.1,),
    )
    assert measure.status is OccupancyMeasureStatus.INELIGIBLE_FUNCTIONAL
    assert measure.empirical_level_set_mass is None


def test_legacy_scalar_view_matches_x_q_f_and_keeps_pi_gf_pending() -> None:
    legacy = {"x": 0.2, "Q": 0.1, "Pi": 0.03, "F": 0.1, "G_F": 1.2}
    successor = {
        "x": 0.2 + 1e-13,
        "Q": 0.1,
        "Pi": None,
        "F": 0.1,
        "G_F": None,
    }
    view = build_legacy_xqpi_fg_view(
        view_id="PR264-LEGACY",
        legacy_values=legacy,
        successor_values=successor,
        tolerance=1e-12,
        source_identity="PR264 FROZEN LEGACY FIXTURE",
    )
    assert view.statuses == (
        LegacyCompatibilityStatus.MATCHED,
        LegacyCompatibilityStatus.MATCHED,
        LegacyCompatibilityStatus.PRESERVED_PENDING_TYPED_SUCCESSOR,
        LegacyCompatibilityStatus.MATCHED,
        LegacyCompatibilityStatus.PRESERVED_PENDING_TYPED_SUCCESSOR,
    )
    assert view.legacy_values == tuple(legacy[name] for name in view.names)
    assert view.all_available_successors_match


def test_legacy_mismatch_is_reported_not_hidden_by_tolerance_rewrite() -> None:
    view = build_legacy_xqpi_fg_view(
        view_id="PR264-LEGACY-MISMATCH",
        legacy_values={name: 1.0 for name in ("x", "Q", "Pi", "F", "G_F")},
        successor_values={
            "x": 1.2,
            "Q": 1.0,
            "Pi": None,
            "F": 1.0,
            "G_F": None,
        },
        tolerance=1e-6,
        source_identity="PR264 MUTATION",
    )
    assert view.statuses[0] is LegacyCompatibilityStatus.MISMATCH
    assert not view.all_available_successors_match


def test_pr264_cannot_prepopulate_pi_or_depth_path_gf_successors() -> None:
    for name in ("Pi", "G_F"):
        successor = {
            "x": 1.0,
            "Q": 1.0,
            "Pi": None,
            "F": 1.0,
            "G_F": None,
        }
        successor[name] = 1.0
        with pytest.raises(
            TensorDepartureStatisticsError, match="remain unavailable"
        ):
            build_legacy_xqpi_fg_view(
                view_id=f"PR264-EARLY-{name}",
                legacy_values={
                    key: 1.0 for key in ("x", "Q", "Pi", "F", "G_F")
                },
                successor_values=successor,
                tolerance=1e-12,
                source_identity="PR264 EARLY SUCCESSOR MUTATION",
            )


def test_result_identity_seals_reject_post_construction_mutation() -> None:
    pushforward = _pushforward()
    object.__setattr__(pushforward, "claim_ceiling", "posterior")
    with pytest.raises(TensorDepartureStatisticsError, match="drifted"):
        pushforward.as_payload()


def test_mio_bridge_exports_diagnostics_without_inference_builders() -> None:
    import mio.formalism as formalism
    import mio.formalism.tensor_departure_statistics as bridge

    assert (
        formalism.CertifiedFunctionalPushforward
        is CertifiedFunctionalPushforward
    )
    assert (
        bridge.build_support_utilization_profile
        is build_support_utilization_profile
    )
    forbidden = {
        "build_mio_posterior",
        "build_mio_likelihood",
        "build_mio_evidence",
    }
    assert not any(hasattr(formalism, name) for name in forbidden)
