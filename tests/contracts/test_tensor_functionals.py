"""PR-262 tensor-functional and shared PR-254 anchor contracts."""

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
    AnchorGeometryError,
    AnchorGeometryKind,
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
    VelocityFrameBundle,
    VelocityNormalization,
    apply_o3_action,
    build_velocity_frame_bundle,
    missing_component,
)
from common.orbit_nonlinearity import O3Transform, STF5_CARTESIAN_BASIS
from common.tensor_functionals import (
    FUNCTIONAL_CLAIM_CEILING,
    FUNCTIONAL_FORBIDDEN_USE,
    FunctionalAdmissibilityStatus,
    FunctionalAnchorStatus,
    FunctionalDomainStatus,
    FunctionalO3Type,
    FunctionalSignClass,
    FunctionalStressStatus,
    TensorFunctionalError,
    TensorFunctionalOperator,
    TensorFunctionalResult,
    TensorFunctionalSpec,
    build_tensor_functional_spec,
    evaluate_tensor_functional,
    revalidate_tensor_functional_result,
)
from common.transfer_registry import TransferSource


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/research_program/vector_tensor/pr262_spec.yaml"
BACKLOG_PATH = ROOT / "docs/codex_handoff/pr_backlog.yaml"

FRAME = "registered observer Cartesian tetrad"
CONGRUENCE = "registered matter congruence"
EPOCH = "z in [0, 0.1]"
SCALE = "100 Mpc"
ORDER = "registered linear kinematic order"
NORMALIZATION = "PR262_FUNCTIONAL_COORDINATES_V1"
BRANCH = "PRE_SOLVER_DIAGNOSTIC"


def _joint(
    *,
    sigma_scale: float = 1.0,
    acceleration_missing: bool = False,
) -> JointAnisotropyState:
    acceleration = (
        missing_component(
            "acceleration_polar3",
            "acceleration unavailable in PR-262 fixture",
            required_for=("acceleration functional",),
        )
        if acceleration_missing
        else (0.01, -0.02, 0.03)
    )
    kinematics = CongruenceKinematics(
        sigma_stf5=tuple(
            sigma_scale * value
            for value in (0.2, -0.1, 0.03, -0.04, 0.05)
        ),
        omega_axial3=(0.01, -0.02, 0.03),
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
        radiation_frame_id="radiation-rest-frame",
        matter_frame_id="matter-rest-frame",
        observer_frame_id="local-observer-frame",
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
        source_identity=f"PR262-DIRECT-FIXTURE-{sigma_scale.hex()}",
    )


def _joint_with_basis(basis: str) -> JointAnisotropyState:
    state = _joint()
    kinematics_payload = state.congruence_kinematics.to_payload()
    kinematics_payload["basis"] = basis
    velocity_payload = state.velocity_frames.to_payload()
    velocity_payload["basis"] = basis
    geometry_payload = state.geometry_state.to_payload()
    geometry_payload["basis"] = basis
    return replace(
        state,
        congruence_kinematics=CongruenceKinematics.from_payload(
            kinematics_payload
        ),
        velocity_frames=VelocityFrameBundle.from_payload(velocity_payload),
        geometry_state=GeometryState.from_payload(geometry_payload),
        basis=basis,
    )


def _spec(
    operator: TensorFunctionalOperator,
    *,
    functional_id: str | None = None,
    anchor_id: str | None = None,
    frame: str = FRAME,
) -> TensorFunctionalSpec:
    return build_tensor_functional_spec(
        functional_id=(
            functional_id
            if functional_id is not None
            else f"pr262.{operator.value.lower()}"
        ),
        operator=operator,
        frame=frame,
        congruence=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        normalization=NORMALIZATION,
        perturbative_order=ORDER,
        branch=BRANCH,
        anchor_id=anchor_id,
    )


def _ball(
    spec: TensorFunctionalSpec,
    *,
    body_id: str,
    radius: float,
) -> AnchorBodySpec:
    return AnchorBodySpec(
        body_id=body_id,
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        coordinate_labels=spec.coordinate_labels,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
        premise_identity="PR262-REGISTERED-PREMISE",
        blocks=(
            AnchorBlockSpec(
                block_id="all-coordinates",
                coordinate_indices=tuple(
                    range(math.prod(spec.output_shape))
                ),
                radius=radius,
            ),
        ),
        assumptions=("synthetic contract fixture",),
    )


def _ellipsoid(
    spec: TensorFunctionalSpec,
    *,
    body_id: str,
) -> AnchorBodySpec:
    dimension = math.prod(spec.output_shape)
    return AnchorBodySpec(
        body_id=body_id,
        geometry=AnchorGeometryKind.ELLIPSOID,
        coordinate_labels=spec.coordinate_labels,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
        premise_identity="PR262-REGISTERED-PREMISE",
        quadratic_form=tuple(
            tuple(1.0 if i == j else 0.0 for j in range(dimension))
            for i in range(dimension)
        ),
    )


def _polytope(
    spec: TensorFunctionalSpec,
    *,
    body_id: str,
) -> AnchorBodySpec:
    dimension = math.prod(spec.output_shape)
    halfspaces = []
    for index in range(dimension):
        plus = [0.0] * dimension
        plus[index] = 1.0
        minus = [0.0] * dimension
        minus[index] = -1.0
        halfspaces.extend(
            (
                PolytopeHalfspace(tuple(plus), 1.0),
                PolytopeHalfspace(tuple(minus), 1.0),
            )
        )
    return AnchorBodySpec(
        body_id=body_id,
        geometry=AnchorGeometryKind.POLYTOPE,
        coordinate_labels=spec.coordinate_labels,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
        premise_identity="PR262-REGISTERED-PREMISE",
        halfspaces=tuple(halfspaces),
    )


def test_pr262_spec_and_card_bind_shared_anchor_scope() -> None:
    document = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    backlog = yaml.safe_load(BACKLOG_PATH.read_text(encoding="utf-8"))
    card = next(row for row in backlog["prs"] if row["id"] == "PR-262")

    assert document["dependencies"] == ["PR-261", "PR-254"]
    assert document["anchor_authority"]["reused_module"] == (
        "common.anchor_geometry"
    )
    assert document["anchor_authority"]["parallel_anchor_hierarchy"] == (
        "forbidden"
    )
    assert document["claim_boundary"]["ceiling"] == "diagnostic_only"
    assert card["depends"] == ["PR-261", "PR-254"]
    assert card["claim_tier_ceiling"] == "diagnostic_only"


@pytest.mark.parametrize(
    ("operator", "shape", "o3_type", "degree", "sign_class"),
    (
        (
            TensorFunctionalOperator.SIGMA_STF5,
            (5,),
            FunctionalO3Type.STF2_TENSOR,
            1,
            FunctionalSignClass.EQUIVARIANT,
        ),
        (
            TensorFunctionalOperator.OMEGA_AXIAL3,
            (3,),
            FunctionalO3Type.AXIAL_VECTOR,
            1,
            FunctionalSignClass.EQUIVARIANT,
        ),
        (
            TensorFunctionalOperator.TR_SIGMA2,
            (1,),
            FunctionalO3Type.SCALAR,
            2,
            FunctionalSignClass.SIGN_DEFINITE,
        ),
        (
            TensorFunctionalOperator.BETA_RM_DOT_OMEGA,
            (1,),
            FunctionalO3Type.PSEUDOSCALAR,
            2,
            FunctionalSignClass.SIGNED,
        ),
    ),
)
def test_spec_registry_fixes_shape_degree_parity_and_sign(
    operator: TensorFunctionalOperator,
    shape: tuple[int, ...],
    o3_type: FunctionalO3Type,
    degree: int,
    sign_class: FunctionalSignClass,
) -> None:
    spec = _spec(operator)
    assert spec.output_shape == shape
    assert spec.o3_type is o3_type
    assert spec.tensor_degree == degree
    assert spec.sign_class is sign_class
    assert TensorFunctionalSpec.from_payload(spec.to_payload()) == spec
    assert spec.spec_id.startswith("sha256:")


def test_spec_and_result_are_factory_only_and_metadata_is_closed() -> None:
    spec = _spec(TensorFunctionalOperator.TR_SIGMA2)
    kwargs = {
        field: getattr(spec, field)
        for field in (
            "functional_id",
            "operator",
            "output_shape",
            "coordinate_labels",
            "tensor_degree",
            "o3_type",
            "sign_class",
            "required_components",
            "frame",
            "congruence",
            "epoch_window",
            "averaging_scale",
            "normalization",
            "perturbative_order",
            "branch",
            "anchor_id",
        )
    }
    with pytest.raises(TensorFunctionalError, match="must be created"):
        TensorFunctionalSpec(**kwargs)

    result = evaluate_tensor_functional(_joint(), spec)
    result_kwargs = {
        field: getattr(result, field)
        for field in (
            "spec",
            "source_state_id",
            "value",
            "domain",
            "codomain",
            "anchor",
            "admissibility",
            "stress",
            "transfer_source",
        )
    }
    with pytest.raises(TensorFunctionalError, match="must be created"):
        TensorFunctionalResult(**result_kwargs)

    payload = spec.to_payload()
    payload["tensor_degree"] = 7
    with pytest.raises(TensorFunctionalError, match="tensor_degree"):
        TensorFunctionalSpec.from_payload(payload)

    payload = spec.to_payload()
    payload["coordinate_labels"] = ["unregistered:value"]
    with pytest.raises(TensorFunctionalError, match="coordinate_labels"):
        TensorFunctionalSpec.from_payload(payload)


def test_spec_identity_seal_refuses_operator_and_claim_lane_mutation() -> None:
    spec = _spec(
        TensorFunctionalOperator.TR_SIGMA2,
        anchor_id="pr262.mutation.anchor",
    )
    object.__setattr__(
        spec,
        "operator",
        TensorFunctionalOperator.TR_SIGMA3,
    )
    with pytest.raises(
        TensorFunctionalError,
        match="functional spec failed canonical replay",
    ):
        evaluate_tensor_functional(
            _joint(sigma_scale=-1.0),
            spec,
            anchor=_ball(
                spec,
                body_id="pr262.mutation.anchor",
                radius=1.0,
            ),
        )

    original = _spec(TensorFunctionalOperator.TR_SIGMA2)
    result = evaluate_tensor_functional(_joint(), original)
    object.__setattr__(original, "claim_ceiling", "family_identified")
    object.__setattr__(original, "allowed_use", ("likelihood",))
    assert result.spec.claim_ceiling == FUNCTIONAL_CLAIM_CEILING
    assert result.spec.allowed_use != ("likelihood",)
    assert result.as_payload()["claim_ceiling"] == FUNCTIONAL_CLAIM_CEILING

    object.__setattr__(result.spec, "claim_ceiling", "family_identified")
    object.__setattr__(result.spec, "allowed_use", ("likelihood",))
    with pytest.raises(TensorFunctionalError, match="identity drifted"):
        result.as_payload()
    with pytest.raises(
        TensorFunctionalError,
        match="functional spec failed canonical replay",
    ):
        revalidate_tensor_functional_result(result, _joint())


def test_noncanonical_stf_basis_is_a_typed_forbidden_domain() -> None:
    state = _joint_with_basis("NONCANONICAL_STF5_BASIS")
    for operator in TensorFunctionalOperator:
        result = evaluate_tensor_functional(state, _spec(operator))
        assert result.domain.status is FunctionalDomainStatus.FORBIDDEN_DOMAIN
        assert result.domain.reasons
        assert result.value is None
        assert result.anchor.status is FunctionalAnchorStatus.NOT_REQUESTED
        assert result.stress.status is FunctionalStressStatus.UNAVAILABLE
        assert (
            result.admissibility.status
            is FunctionalAdmissibilityStatus.ABSTAIN
        )
        assert not result.admissibility.signed_score_eligible
        assert not result.admissibility.occupancy_eligible
        assert not result.admissibility.exceedance_eligible


def test_value_domain_codomain_anchor_admissibility_and_stress_are_separate() -> None:
    spec = _spec(
        TensorFunctionalOperator.OMEGA_AXIAL3,
        anchor_id="pr262.omega.anchor",
    )
    anchor = _ball(spec, body_id="pr262.omega.anchor", radius=0.05)
    result = evaluate_tensor_functional(_joint(), spec, anchor=anchor)

    assert result.value == (0.01, -0.02, 0.03)
    assert result.domain.status is FunctionalDomainStatus.ADMISSIBLE
    assert result.codomain.shape == (3,)
    assert result.codomain.o3_type is FunctionalO3Type.AXIAL_VECTOR
    assert result.anchor.status is FunctionalAnchorStatus.DEFINED
    assert result.anchor.gauge is not None
    assert result.anchor.margin is not None
    assert result.stress.status is FunctionalStressStatus.DEFINED
    assert result.stress.point_estimate == pytest.approx(
        np.linalg.norm(result.value) / 0.05
    )
    assert (
        result.admissibility.status
        is FunctionalAdmissibilityStatus.ADMISSIBLE
    )
    assert result.admissibility.signed_score_eligible
    assert not result.admissibility.occupancy_eligible
    assert result.result_id.startswith("sha256:")


def test_missing_component_abstains_without_zero_or_anchor_value() -> None:
    spec = _spec(
        TensorFunctionalOperator.ACCELERATION_POLAR3,
        anchor_id="pr262.acceleration.anchor",
    )
    anchor = _ball(
        spec,
        body_id="pr262.acceleration.anchor",
        radius=0.1,
    )
    result = evaluate_tensor_functional(
        _joint(acceleration_missing=True),
        spec,
        anchor=anchor,
    )

    assert result.value is None
    assert result.domain.status is FunctionalDomainStatus.MISSING_COMPONENT
    assert result.domain.missing_components == ("acceleration_polar3",)
    assert result.anchor.status is FunctionalAnchorStatus.ANCHOR_UNAVAILABLE
    assert result.stress.status is FunctionalStressStatus.UNAVAILABLE
    assert (
        result.admissibility.status
        is FunctionalAdmissibilityStatus.ABSTAIN
    )
    assert not result.admissibility.exceedance_eligible


def test_metadata_and_anchor_channel_mismatch_fail_closed() -> None:
    mismatched_spec = _spec(
        TensorFunctionalOperator.TR_SIGMA2,
        frame="different frame",
    )
    result = evaluate_tensor_functional(_joint(), mismatched_spec)
    assert result.value is None
    assert result.domain.status is FunctionalDomainStatus.METADATA_MISMATCH
    assert result.domain.mismatched_metadata == ("frame",)

    spec = _spec(
        TensorFunctionalOperator.TR_SIGMA2,
        anchor_id="expected.anchor",
    )
    wrong_id = _ball(spec, body_id="wrong.anchor", radius=1.0)
    report = evaluate_tensor_functional(_joint(), spec, anchor=wrong_id)
    assert report.anchor.status is FunctionalAnchorStatus.CHANNEL_MISMATCH
    assert report.stress.status is FunctionalStressStatus.UNAVAILABLE

    wrong_channel = replace(
        _ball(spec, body_id="expected.anchor", radius=1.0),
        frame="different frame",
    )
    report = evaluate_tensor_functional(_joint(), spec, anchor=wrong_channel)
    assert report.anchor.status is FunctionalAnchorStatus.CHANNEL_MISMATCH


def test_rank_deficient_and_noncompact_anchor_mutations_are_refused() -> None:
    spec = _spec(
        TensorFunctionalOperator.OMEGA_AXIAL3,
        anchor_id="mutated.anchor",
    )
    ellipsoid = _ellipsoid(spec, body_id="mutated.anchor")
    object.__setattr__(
        ellipsoid,
        "quadratic_form",
        ((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    )
    report = evaluate_tensor_functional(_joint(), spec, anchor=ellipsoid)
    assert report.anchor.status is FunctionalAnchorStatus.RANK_DEFICIENT
    assert report.value is not None
    assert report.stress.status is FunctionalStressStatus.UNAVAILABLE

    polytope = _polytope(spec, body_id="mutated.anchor")
    object.__setattr__(
        polytope,
        "halfspaces",
        tuple(polytope.halfspaces[::2]),
    )
    report = evaluate_tensor_functional(_joint(), spec, anchor=polytope)
    assert report.anchor.status is FunctionalAnchorStatus.NON_COMPACT_SUPPORT
    assert report.stress.status is FunctionalStressStatus.UNAVAILABLE


def test_invalid_rank_or_support_is_rejected_at_pr254_constructor() -> None:
    spec = _spec(TensorFunctionalOperator.OMEGA_AXIAL3)
    with pytest.raises(AnchorGeometryError, match="positive definite"):
        AnchorBodySpec(
            body_id="rank-deficient",
            geometry=AnchorGeometryKind.ELLIPSOID,
            coordinate_labels=spec.coordinate_labels,
            frame=spec.frame,
            normalization=spec.normalization,
            perturbative_order=spec.perturbative_order,
            branch=spec.branch,
            premise_identity="fixture",
            quadratic_form=(
                (1.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
        )
    with pytest.raises(AnchorGeometryError, match="centrally symmetric"):
        AnchorBodySpec(
            body_id="noncompact",
            geometry=AnchorGeometryKind.POLYTOPE,
            coordinate_labels=spec.coordinate_labels,
            frame=spec.frame,
            normalization=spec.normalization,
            perturbative_order=spec.perturbative_order,
            branch=spec.branch,
            premise_identity="fixture",
            halfspaces=(
                PolytopeHalfspace((1.0, 0.0, 0.0), 1.0),
                PolytopeHalfspace((0.0, 1.0, 0.0), 1.0),
                PolytopeHalfspace((0.0, 0.0, 1.0), 1.0),
            ),
        )


def test_continuous_family_reuses_optimizer_required_refusal() -> None:
    spec = _spec(
        TensorFunctionalOperator.TR_SIGMA2,
        anchor_id="continuous.anchor",
    )
    family = AnchorFamily(
        family_id="continuous.anchor",
        kind=AnchorFamilyKind.CONTINUOUS_CONDITIONAL,
        nuisance_identity="continuous nuisance",
        optimizer_contract="registered optimizer not executed",
        coordinate_labels=spec.coordinate_labels,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
    )
    result = evaluate_tensor_functional(_joint(), spec, anchor=family)
    assert result.anchor.status is FunctionalAnchorStatus.OPTIMIZER_REQUIRED
    assert result.stress.status is FunctionalStressStatus.UNAVAILABLE


def test_anchor_scaling_and_homogeneous_functional_scaling() -> None:
    base_spec = _spec(
        TensorFunctionalOperator.TR_SIGMA2,
        anchor_id="sigma2.anchor",
    )
    base = evaluate_tensor_functional(
        _joint(sigma_scale=1.0),
        base_spec,
        anchor=_ball(base_spec, body_id="sigma2.anchor", radius=0.2),
    )
    scaled = evaluate_tensor_functional(
        _joint(sigma_scale=3.0),
        base_spec,
        anchor=_ball(
            base_spec,
            body_id="sigma2.anchor",
            radius=0.2 * 3.0**2,
        ),
    )
    assert scaled.scalar_value == pytest.approx(base.scalar_value * 9.0)
    assert scaled.stress.point_estimate == pytest.approx(
        base.stress.point_estimate
    )


@pytest.mark.parametrize("seed", range(12))
def test_random_o3_covariance_and_parity_metamorphics(seed: int) -> None:
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(3, 3))
    q, _ = np.linalg.qr(raw)
    if seed % 2:
        q[:, 0] *= -1.0
    transform = O3Transform(
        matrix=tuple(tuple(float(value) for value in row) for row in q),
        transform_id=f"pr262-random-{seed}",
        coordinate_frame=FRAME,
    )
    state = _joint()
    transformed = apply_o3_action(state, transform)

    scalar_spec = _spec(TensorFunctionalOperator.TR_SIGMA2)
    before_scalar = evaluate_tensor_functional(state, scalar_spec).scalar_value
    after_scalar = evaluate_tensor_functional(
        transformed, scalar_spec
    ).scalar_value
    assert after_scalar == pytest.approx(before_scalar, rel=1e-12, abs=1e-14)

    pseudo_spec = _spec(TensorFunctionalOperator.BETA_RM_DOT_OMEGA)
    before_pseudo = evaluate_tensor_functional(
        state, pseudo_spec
    ).scalar_value
    after_pseudo = evaluate_tensor_functional(
        transformed, pseudo_spec
    ).scalar_value
    assert after_pseudo == pytest.approx(
        transform.determinant * before_pseudo,
        rel=1e-12,
        abs=1e-14,
    )

    omega_spec = _spec(
        TensorFunctionalOperator.OMEGA_AXIAL3,
        anchor_id="o3.omega.anchor",
    )
    omega_anchor = _ball(
        omega_spec,
        body_id="o3.omega.anchor",
        radius=0.1,
    )
    before_stress = evaluate_tensor_functional(
        state,
        omega_spec,
        anchor=omega_anchor,
    ).stress.point_estimate
    after_stress = evaluate_tensor_functional(
        transformed,
        omega_spec,
        anchor=omega_anchor,
    ).stress.point_estimate
    assert after_stress == pytest.approx(
        before_stress,
        rel=1e-12,
        abs=1e-14,
    )


def test_sign_definite_anchor_is_the_only_occupancy_eligible_class() -> None:
    positive = _spec(
        TensorFunctionalOperator.TR_SIGMA2,
        anchor_id="positive.anchor",
    )
    positive_result = evaluate_tensor_functional(
        _joint(),
        positive,
        anchor=_ball(positive, body_id="positive.anchor", radius=1.0),
    )
    assert positive_result.admissibility.occupancy_eligible

    signed = _spec(
        TensorFunctionalOperator.TR_SIGMA3,
        anchor_id="signed.anchor",
    )
    signed_result = evaluate_tensor_functional(
        _joint(),
        signed,
        anchor=_ball(signed, body_id="signed.anchor", radius=1.0),
    )
    assert signed_result.admissibility.signed_score_eligible
    assert not signed_result.admissibility.occupancy_eligible


def test_mio_bridge_is_same_common_contract_and_has_no_inference_surface() -> None:
    import mio.formalism as mio_formalism
    import mio.formalism.tensor_functionals as bridge

    assert bridge.TensorFunctionalSpec is TensorFunctionalSpec
    assert mio_formalism.TensorFunctionalResult is TensorFunctionalResult
    assert bridge.__mio_owned__ is True
    public = set(bridge.__all__)
    assert not any(
        token in name.lower()
        for name in public
        for token in ("posterior", "likelihood", "evidence")
    )


def test_claim_ceiling_transfer_provenance_and_forbidden_language_are_retained() -> None:
    result = evaluate_tensor_functional(
        _joint(),
        _spec(TensorFunctionalOperator.TR_SIGMA2),
    )
    assert result.claim_ceiling == FUNCTIONAL_CLAIM_CEILING
    assert result.transfer_source == TransferSource.NONE.value
    assert result.forbidden_use == FUNCTIONAL_FORBIDDEN_USE
    payload = result.as_payload()
    rendered = str(payload).lower()
    assert "diagnostic_only" in rendered
    assert "bianchi family identification" in rendered
    assert "native solver validation" in rendered


def test_bool_nan_shape_and_claim_mutations_are_rejected() -> None:
    with pytest.raises(TensorFunctionalError, match="integer"):
        spec = _spec(TensorFunctionalOperator.TR_SIGMA2)
        payload = spec.to_payload()
        payload["output_shape"] = [True]
        TensorFunctionalSpec.from_payload(payload)

    spec = _spec(TensorFunctionalOperator.TR_SIGMA2)
    payload = spec.to_payload()
    payload["claim_ceiling"] = "family_identified"
    with pytest.raises(TensorFunctionalError, match="claim ceiling"):
        TensorFunctionalSpec.from_payload(payload)

    result = evaluate_tensor_functional(_joint(), spec)
    object.__setattr__(result, "value", (float("nan"),))
    with pytest.raises(TensorFunctionalError, match="fields do not match"):
        revalidate_tensor_functional_result(result, _joint())
