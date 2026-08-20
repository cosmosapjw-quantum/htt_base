"""HTT-owned PR-273 blind synthetic state-to-report integration.

``analyze_blind_challenge`` accepts no truth-vault argument and has no file
access.  It composes existing typed COMMON/OBSSTAT/MIO/HTT contracts and
returns a sealed synthetic submission.  Unblinding is performed separately
by :mod:`common.blind_synthetic_contract`.
"""

from __future__ import annotations

import hashlib
import math
from typing import Mapping, Sequence

import numpy as np

from common.anchor_geometry import (
    AnchorBlockSpec,
    AnchorBodySpec,
    AnchorGeometryKind,
    AnchorVector,
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (
    anchored_numeric_content_id,
    measure_anchored_response_geometry,
)
# PR-273 is a frozen historical blind result. Its analyzer intentionally
# retains the exact V1 type-report implementation after the PR-281 successor.
from common.anisotropy_type_report_v1 import (
    build_anisotropy_type_report,
    build_open_set_replay_inputs,
)
from common.blind_synthetic_contract import (
    BLIND_SYNTHETIC_CLAIM_CEILING,
    BlindSyntheticChallenge,
    BlindSyntheticContractError,
    BlindSyntheticSubmission,
    build_blind_synthetic_submission,
)
from common.conditional_exceedance import (
    ConditioningSource,
    ExceedanceLane,
    SamplingLaw,
    build_null_calibrated_exceedance,
    build_sampling_draws,
    build_sampling_law_spec,
)
from common.depth_path import (
    build_depth_coherence_report,
    build_depth_path,
    build_mask_stratum,
    build_observable_feature_step,
    build_transport_kernel,
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
    build_velocity_frame_bundle,
    missing_component,
)
from common.open_set_response_classes import (
    ResponseClassSourceSemantics,
    ResponseSupportKind,
    build_response_class_manifold,
    build_response_equivalence_report,
    classify_open_set_response,
)
from common.orbit_catalogue_v3 import (
    OrbitActionGroup,
    build_orbit_catalogue_v3_spec,
    orbit_catalogue_v3,
)
from common.orbit_nonlinearity import STF5_CARTESIAN_BASIS
from common.sky_support import build_sky_support_from_mask
from common.tensor_departure_statistics import (
    ScalarizationPolicy,
    build_certified_functional_pushforward,
    build_occupancy_measure,
    build_support_utilization_profile,
)
from common.tensor_functionals import (
    TensorFunctionalOperator,
    build_tensor_functional_spec,
    evaluate_tensor_functional,
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
from htt.infer.anisotropy_type_report import (
    build_local_global_compatibility_input,
)
from htt.statistics.open_set_response_classes import (
    PR283_DEFAULT_THRESHOLD_CONTRACT,
    source_separation_gate_from_pr256,
)


FRAME = "PR273 registered Cartesian tetrad"
CONGRUENCE = "PR273 registered matter congruence"
EPOCH = "PR273 synthetic epoch"
SCALE = "PR273 synthetic averaging scale"
ORDER = "PR273 diagnostic tensor order"
NORMALIZATION = "PR273_FUNCTIONAL_COORDINATES_V1"
BRANCH = "PRE_SOLVER_SYNTHETIC_DIAGNOSTIC"
DEPTH_ALERT_THRESHOLD = 25.0
ANALYZER_ID = "HTT-PR273-TYPED-PIPELINE-V1"


def _receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()


def _numeric_vector(
    value: object,
    *,
    name: str,
    length: int,
    allow_missing: bool = False,
) -> tuple[float, ...] | None:
    if value is None and allow_missing:
        return None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise BlindSyntheticContractError(f"{name} must be a vector")
    out = tuple(float(item) for item in value)
    if len(out) != length or any(not math.isfinite(item) for item in out):
        raise BlindSyntheticContractError(
            f"{name} must contain {length} finite values"
        )
    return out


def _case_mapping(case: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = case.get(name)
    if not isinstance(value, Mapping):
        raise BlindSyntheticContractError(f"{name} must be a mapping")
    return value


def _scaled(values: tuple[float, ...], scale: float) -> tuple[float, ...]:
    return tuple(scale * value for value in values)


def _state_from_case(
    case: Mapping[str, object],
    *,
    scale: float,
) -> JointAnisotropyState:
    case_id = str(case["case_id"])
    raw = _case_mapping(case, "state")
    sigma = _numeric_vector(raw.get("sigma_stf5"), name="sigma_stf5", length=5)
    omega = _numeric_vector(raw.get("omega_axial3"), name="omega_axial3", length=3)
    acceleration = _numeric_vector(
        raw.get("acceleration_polar3"),
        name="acceleration_polar3",
        length=3,
        allow_missing=True,
    )
    beta_rm = _numeric_vector(raw.get("beta_rm"), name="beta_rm", length=3)
    beta_mo = _numeric_vector(raw.get("beta_mo"), name="beta_mo", length=3)
    geometry_stf = _numeric_vector(
        raw.get("geometry_stf5"),
        name="geometry_stf5",
        length=5,
        allow_missing=True,
    )
    assert sigma is not None
    assert omega is not None
    assert beta_rm is not None
    assert beta_mo is not None
    acceleration_value: object
    acceleration_normalization: AccelerationNormalization | None
    if acceleration is None:
        acceleration_value = missing_component(
            "acceleration_polar3",
            "PR-273 challenge marks this observer-side channel unavailable",
            required_for=("acceleration functional", "joint orbit signature"),
        )
        acceleration_normalization = None
    else:
        acceleration_value = _scaled(acceleration, scale)
        acceleration_normalization = AccelerationNormalization.A_OVER_C_THETA
    kinematics = CongruenceKinematics(
        sigma_stf5=_scaled(sigma, scale),
        omega_axial3=_scaled(omega, scale),
        acceleration_polar3=acceleration_value,
        frame=FRAME,
        congruence_id=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=ORDER,
        acceleration_normalization=acceleration_normalization,
    )
    rm = _scaled(beta_rm, scale)
    mo = _scaled(beta_mo, scale)
    ro = tuple(left + right for left, right in zip(rm, mo, strict=True))
    velocity = build_velocity_frame_bundle(
        beta_RO=ro,
        beta_RM=rm,
        beta_MO=mo,
        coordinate_frame=FRAME,
        radiation_frame_id="PR273 radiation frame",
        matter_frame_id="PR273 matter frame",
        observer_frame_id="PR273 observer frame",
        basis=STF5_CARTESIAN_BASIS,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        first_order_beta_ceiling=0.02,
    )
    geometry_kwargs: dict[str, object] = {}
    if geometry_stf is not None:
        geometry_kwargs = {
            "spatial_curvature_stf5": _scaled(geometry_stf, scale),
            "electric_weyl_stf5": _scaled(geometry_stf, 0.2 * scale),
            "magnetic_weyl_stf5": _scaled(geometry_stf, 0.1 * scale),
            "anisotropic_stress_stf5": _scaled(geometry_stf, 0.3 * scale),
        }
    geometry = GeometryState(
        delta_omega_k=-0.02 * scale,
        frame=FRAME,
        congruence_id=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        perturbative_order=ORDER,
        **geometry_kwargs,
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
        source_identity=f"PR273-{case_id}-{scale.hex()}",
    )


def _functional_spec(
    case_id: str,
    operator: TensorFunctionalOperator,
) -> object:
    return build_tensor_functional_spec(
        functional_id=f"pr273.{case_id.lower()}.{operator.value.lower()}",
        operator=operator,
        frame=FRAME,
        congruence=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        normalization=NORMALIZATION,
        perturbative_order=ORDER,
        branch=BRANCH,
        anchor_id=f"pr273.anchor.{case_id.lower()}.{operator.value.lower()}",
    )


def _anchor(spec: object) -> AnchorBodySpec:
    return AnchorBodySpec(
        body_id=spec.anchor_id,
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        coordinate_labels=spec.coordinate_labels,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
        premise_identity="PR273 REGISTERED SYNTHETIC PREMISE",
        blocks=(
            AnchorBlockSpec(
                block_id="all",
                coordinate_indices=tuple(range(math.prod(spec.output_shape))),
                radius=1.0,
            ),
        ),
    )


def _functional_chain(
    challenge: BlindSyntheticChallenge,
    case: Mapping[str, object],
) -> dict[str, object]:
    case_id = str(case["case_id"])
    operators = (
        TensorFunctionalOperator.TR_SIGMA2,
        TensorFunctionalOperator.OMEGA_AXIAL3,
        TensorFunctionalOperator.SIGMA_STF5,
        TensorFunctionalOperator.ACCELERATION_POLAR3,
    )
    specs = tuple(_functional_spec(case_id, operator) for operator in operators)
    anchors = {spec.functional_id: _anchor(spec) for spec in specs}
    states = tuple(
        _state_from_case(case, scale=scale)
        for scale in challenge.functional_scales
    )
    rows = tuple(
        tuple(
            evaluate_tensor_functional(
                state,
                spec,
                anchor=anchors[spec.functional_id],
            )
            for spec in specs
        )
        for state in states
    )
    policies = {
        specs[0].functional_id: ScalarizationPolicy.SCALAR_IDENTITY,
        specs[1].functional_id: ScalarizationPolicy.EUCLIDEAN_NORM,
        specs[2].functional_id: ScalarizationPolicy.STF_FROBENIUS_NORM,
        specs[3].functional_id: ScalarizationPolicy.EUCLIDEAN_NORM,
    }
    pushforward = build_certified_functional_pushforward(
        pushforward_id=f"PR273-{case_id}-PUSHFORWARD",
        samples=rows,
        source_states=states,
        anchors=anchors,
        scalarization_policies=policies,
    )
    vector_spec = specs[1]
    vector_anchor = anchors[vector_spec.functional_id]
    points = tuple(
        AnchorVector(
            vector_id=f"PR273-{case_id}-POINT-{index}",
            coordinate_labels=vector_spec.coordinate_labels,
            values=tuple(float(value) for value in result.value),
            frame=vector_spec.frame,
            normalization=vector_spec.normalization,
            perturbative_order=vector_spec.perturbative_order,
            branch=vector_spec.branch,
        )
        for index, result in enumerate(row[1] for row in rows)
    )
    directions = tuple(
        AnchorVector(
            vector_id=f"PR273-{case_id}-DIRECTION-{index}",
            coordinate_labels=vector_spec.coordinate_labels,
            values=tuple(
                1.0 if coordinate == index else 0.0
                for coordinate in range(3)
            ),
            frame=vector_spec.frame,
            normalization=vector_spec.normalization,
            perturbative_order=vector_spec.perturbative_order,
            branch=vector_spec.branch,
        )
        for index in range(3)
    )
    support = build_support_utilization_profile(
        identified_set_id=f"PR273-{case_id}-IDENTIFIED-POINTS",
        identified_points=points,
        anchor=vector_anchor,
        directions=directions,
    )
    occupancy = build_occupancy_measure(
        measure_id=f"PR273-{case_id}-OCCUPANCY",
        pushforward=pushforward,
        functional_id=specs[0].functional_id,
        thresholds=(0.0, 0.25, 0.5, 1.0),
    )
    middle = len(rows) // 2
    functional_statuses = tuple(
        result.domain.status.value for result in rows[middle]
    )
    return {
        "state": states[middle],
        "rows": rows,
        "functional_result_ids": tuple(
            result.result_id for result in rows[middle]
        ),
        "functional_statuses": functional_statuses,
        "pushforward": pushforward,
        "x_values": tuple(pushforward.sample_by_functional[middle]),
        "q_values": tuple(pushforward.q_point_by_functional[middle]),
        "support": support,
        "occupancy": occupancy,
        "missing_functional": any(
            status == "MISSING_COMPONENT" for status in functional_statuses
        ),
    }


def _orbit(state: JointAnisotropyState, case_id: str):
    spec = build_orbit_catalogue_v3_spec(
        catalogue_id=f"PR273-{case_id}-O3-CATALOGUE",
        action_group=OrbitActionGroup.O3,
    )
    return orbit_catalogue_v3(state, spec)


def _conditional_profile(
    challenge: BlindSyntheticChallenge,
    case_id: str,
    functional_id: str,
):
    law = build_sampling_law_spec(
        law_id=f"PR273-{case_id}-MATCHED-NULL-LAW",
        sampling_law=SamplingLaw.FIXED_INJECTION_MOCK,
        conditioning_source=ConditioningSource.INJECTED,
        lane=ExceedanceLane.MIO_NULL,
        source_identity="PR273 preregistered synthetic null DGP",
        covariance_id=f"PR273-{case_id}-NULL-COVARIANCE",
        transfer_source="none",
        assumptions=("finite exchangeable challenge draws",),
    )
    draws = build_sampling_draws(
        draws_id=f"PR273-{case_id}-MATCHED-NULL-DRAWS",
        law=law,
        values=challenge.null_draws,
        source_artifact_id=challenge.content_id,
        sample_unit="dimensionless functional value",
    )
    return build_null_calibrated_exceedance(
        profile_id=f"PR273-{case_id}-NULL-EXCEEDANCE",
        functional_id=functional_id,
        thresholds=(0.0, 0.25, 0.5),
        law=law,
        draws=draws,
        conditioning_id=f"PR273-{case_id}-MATCHED-NULL-CONDITIONING",
        alpha=0.05,
    ).profile


def _depth_chain(case: Mapping[str, object]):
    case_id = str(case["case_id"])
    raw = _case_mapping(case, "depth")
    supports = _sequence_pair(raw.get("support"), "depth.support")
    features = _sequence_pair(raw.get("features"), "depth.features")
    covariance_scales = _numeric_vector(
        raw.get("covariance_scale"),
        name="depth.covariance_scale",
        length=2,
    )
    assert covariance_scales is not None
    strata = []
    for index, support_ids in enumerate(supports):
        kept = tuple(int(value) for value in support_ids)
        mask = np.zeros(2, dtype=bool)
        mask[list(kept)] = True
        sky_support = build_sky_support_from_mask(
            mask,
            coordinate_frame="GALACTIC",
            completeness_status="synthetic_fixture_complete",
            selection_mode=f"PR273-{case_id}-D{index + 1}",
            mock_coverage_status="synthetic_fixture",
            pixelization="PR273_TWO_PIXEL_FIXTURE",
        )
        strata.append(
            build_mask_stratum(
                stratum_id=f"PR273-{case_id}-D{index + 1}",
                depth_coordinate=0.1 * (index + 1),
                depth_unit="redshift_proxy",
                support_unit_ids=tuple(
                    f"pixel-{value}" for value in kept
                ),
                support_universe_size=2,
                sky_support=sky_support,
                selection_id=_receipt(f"PR273-{case_id}-SELECTION-{index}"),
                covariance_id=_receipt(f"PR273-{case_id}-COVARIANCE-{index}"),
                source_artifact_id=_receipt(f"PR273-{case_id}-SOURCE-{index}"),
                feature_names=("obs-x", "obs-y"),
                feature_unit="dimensionless_observable",
                assumptions=("synthetic observer-side fixture",),
            )
        )
    kernel = build_transport_kernel(
        transport_id=f"PR273-{case_id}-K12",
        source=strata[0],
        target=strata[1],
        matrix=((1.0, 0.0), (0.0, 1.0)),
        mask_transport_id=_receipt(f"PR273-{case_id}-MASK-K12"),
        selection_transport_id=_receipt(f"PR273-{case_id}-SELECTION-K12"),
        covariance_transport_id=_receipt(f"PR273-{case_id}-COVARIANCE-K12"),
        method_id="PR273-LINEAR-TRANSPORT-V1",
        assumptions=("dimensionless deterministic transport",),
    )
    path = build_depth_path(
        path_id=f"PR273-{case_id}-PATH",
        strata=tuple(strata),
        kernels=(kernel,),
    )
    steps = tuple(
        build_observable_feature_step(
            step_id=f"PR273-{case_id}-STEP-{index + 1}",
            stratum=stratum,
            values=tuple(float(value) for value in feature),
            covariance=(
                (covariance_scales[index], 0.0),
                (0.0, covariance_scales[index]),
            ),
            source_artifact_id=_receipt(
                f"PR273-{case_id}-FEATURE-{index}"
            ),
            extraction_method_id="PR273-SYNTHETIC-FEATURE-V1",
            sample_count=32,
        )
        for index, (stratum, feature) in enumerate(
            zip(strata, features, strict=True)
        )
    )
    coherence = build_depth_coherence_report(
        report_id=f"PR273-{case_id}-DEPTH-COHERENCE",
        path=path,
        steps=steps,
    )
    return path, coherence


def _sequence_pair(value: object, name: str) -> tuple[tuple[object, ...], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise BlindSyntheticContractError(f"{name} must be a sequence")
    out = tuple(
        tuple(item)
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes))
        else ()
        for item in value
    )
    if len(out) != 2 or any(not item for item in out):
        raise BlindSyntheticContractError(
            f"{name} must contain two non-empty sequences"
        )
    return out


def _anchored(case_id: str):
    normalizer = NormalizerSpec(
        normalizer_id=f"PR273-{case_id}-ANCHORED-NORMALIZER",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("u0", "u1"),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity=f"PR273-{case_id}-ANCHORED-COORDINATES",
        assumptions=("synthetic identity anchor",),
    )
    response = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))
    covariance = np.eye(3)
    report = measure_anchored_response_geometry(
        response=response,
        covariance=covariance,
        normalizer=normalizer,
        parameter_labels=("u0", "u1"),
        transfer_id=_receipt(f"PR273-{case_id}-ANCHORED-TRANSFER-NONE"),
        transfer_source=TransferSource.NONE,
        mask_id=_receipt(f"PR273-{case_id}-ANCHORED-MASK"),
        covariance_id=anchored_numeric_content_id(covariance),
        comparison_response=response,
    )
    return report, normalizer, response


def _source_normalizer(case_id: str) -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id=f"PR273-{case_id}-SOURCE-NORMALIZER",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("beta_MO_amplitude", "beta_RM_amplitude"),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity=f"PR273-{case_id}-SOURCE-COORDINATES",
        assumptions=("block-preserving synthetic map",),
    )


def _source_provider(
    *,
    case_id: str,
    hypothesis: SourceHypothesis,
    response: Sequence[Sequence[float]],
):
    local = hypothesis is SourceHypothesis.LOCAL_BOOST
    return register_source_response_provider(
        provider_id=_receipt(f"PR273-{case_id}-PROVIDER-{hypothesis.value}"),
        hypothesis=hypothesis,
        velocity_component=(
            VelocityComponent.BETA_MO if local else VelocityComponent.BETA_RM
        ),
        provider_kind=ResponseProviderKind.ANALYTIC,
        availability=ResponseProviderAvailability.AVAILABLE,
        observable_labels=("obs-x", "obs-y"),
        parameter_labels=(
            ("beta_MO_amplitude",)
            if local
            else ("beta_RM_amplitude",)
        ),
        response=response,
        transfer_id=_receipt(f"PR273-{case_id}-SOURCE-TRANSFER-NONE"),
        transfer_source=TransferSource.NONE,
        basis="PR273 registered response basis",
        epoch_window="PR273 registered response window",
        assumptions=("first-order analytic synthetic response",),
        caveats=("hypothesis-only response",),
    )


def _source_and_open_set(case: Mapping[str, object]):
    case_id = str(case["case_id"])
    raw = _case_mapping(case, "responses")
    local_response = _sequence_pair(raw.get("local"), "responses.local")
    global_response = _sequence_pair(raw.get("global"), "responses.global")
    observation = _numeric_vector(
        raw.get("observation"), name="responses.observation", length=2
    )
    assert observation is not None
    covariance = np.eye(2)
    normalizer = _source_normalizer(case_id)
    report = measure_source_response_geometry(
        local_provider=_source_provider(
            case_id=case_id,
            hypothesis=SourceHypothesis.LOCAL_BOOST,
            response=local_response,
        ),
        global_provider=_source_provider(
            case_id=case_id,
            hypothesis=SourceHypothesis.GLOBAL_TILT,
            response=global_response,
        ),
        covariance=covariance,
        normalizer=normalizer,
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=_receipt(f"PR273-{case_id}-SOURCE-MASK"),
        separation_threshold_radians=0.2,
    )
    local_global = build_local_global_compatibility_input(
        report=report,
        normalizer=normalizer,
    )
    classes = (
        build_response_class_manifold(
            class_id="response-class-local",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=report.local_provider.provider_id,
            observable_labels=report.observable_labels,
            convention_id=_receipt("PR273-RESPONSE-CONVENTION"),
            nuisance_policy_id=_receipt("PR273-NO-NUISANCE"),
            support_nodes=((-3.0, 0.0),),
            transfer_source=TransferSource.NONE,
            source_semantics=ResponseClassSourceSemantics.LOCAL_BOOST,
            source_response_id=report.local_provider.response_id,
        ),
        build_response_class_manifold(
            class_id="response-class-global",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=report.global_provider.provider_id,
            observable_labels=report.observable_labels,
            convention_id=_receipt("PR273-RESPONSE-CONVENTION"),
            nuisance_policy_id=_receipt("PR273-NO-NUISANCE"),
            support_nodes=((3.0, 0.0),),
            transfer_source=TransferSource.NONE,
            source_semantics=ResponseClassSourceSemantics.GLOBAL_TILT,
            source_response_id=report.global_provider.response_id,
        ),
    )
    equivalence = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.1,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        reopening_observables=(),
    )
    gate = source_separation_gate_from_pr256(
        report,
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        normalizer=normalizer,
        threshold_contract=PR283_DEFAULT_THRESHOLD_CONTRACT,
    )
    classification = classify_open_set_response(
        observation=observation,
        classes=classes,
        equivalence_report=equivalence,
        covariance=covariance,
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=gate,
    )
    replay = build_open_set_replay_inputs(
        classification_report=classification,
        classes=classes,
        equivalence_report=equivalence,
        observation=observation,
        covariance=covariance,
        nuisance_tangent=None,
        source_separation_gate=gate,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
    )
    return local_global, replay


def _case_result(
    challenge: BlindSyntheticChallenge,
    case: Mapping[str, object],
) -> dict[str, object]:
    case_id = str(case["case_id"])
    functional = _functional_chain(challenge, case)
    state = functional["state"]
    orbit = _orbit(state, case_id)
    conditional = _conditional_profile(
        challenge,
        case_id,
        functional["rows"][0][0].spec.functional_id,
    )
    path, coherence = _depth_chain(case)
    anchored, anchored_normalizer, comparison = _anchored(case_id)
    local_global, open_set = _source_and_open_set(case)
    type_report = build_anisotropy_type_report(
        report_id=f"PR273-{case_id}-ANISOTROPY-TYPE-REPORT",
        joint_state=state,
        orbit_report=orbit,
        anchored_response=anchored,
        anchored_normalizer=anchored_normalizer,
        anchored_comparison_response=comparison,
        local_global=local_global,
        open_set=open_set,
        conditional_exceedance=conditional,
        depth_path=path,
        depth_coherence=coherence,
    )
    score = coherence.mean_normalized_score
    return {
        "case_id": case_id,
        "partition": challenge.partition_for(case_id),
        "state_content_id": state.content_id,
        "functional_result_ids": list(functional["functional_result_ids"]),
        "functional_statuses": list(functional["functional_statuses"]),
        "orbit_content_id": orbit.report_id,
        "orbit_stratum": orbit.stratum.status.value,
        "pushforward_content_id": functional["pushforward"].content_id,
        "x_values": list(functional["x_values"]),
        "q_values": list(functional["q_values"]),
        "support_utilization_content_id": functional["support"].content_id,
        "support_utilization_status": functional["support"].status.value,
        "occupancy_content_id": functional["occupancy"].content_id,
        "occupancy_status": functional["occupancy"].status.value,
        "conditional_exceedance_content_id": conditional.content_id,
        "conditional_exceedance_status": conditional.status.value,
        "depth_path_content_id": path.content_id,
        "depth_coherence_content_id": coherence.content_id,
        "depth_coherence_status": coherence.status.value,
        "depth_mean_normalized_score": score,
        "depth_alert": score is not None and score > DEPTH_ALERT_THRESHOLD,
        "type_report_content_id": type_report.content_id,
        "geometry_status": type_report.geometry_information_status.value,
        "local_global_status": type_report.local_global_status.value,
        "compatibility_status": type_report.compatibility_status.value,
        "missing_functional": functional["missing_functional"],
        "claim_ceiling": BLIND_SYNTHETIC_CLAIM_CEILING,
        "transfer_source": "none",
    }


def analyze_blind_challenge(
    challenge: BlindSyntheticChallenge,
) -> BlindSyntheticSubmission:
    """Analyze a challenge without accepting a truth-vault capability."""

    if type(challenge) is not BlindSyntheticChallenge:
        raise TypeError("challenge must be exact BlindSyntheticChallenge")
    challenge.as_payload()
    results = tuple(_case_result(challenge, case) for case in challenge.cases)
    return build_blind_synthetic_submission(
        submission_id=f"{challenge.challenge_id}-ANALYST-SUBMISSION",
        analyzer_id=ANALYZER_ID,
        challenge=challenge,
        case_results=results,
    )


__all__ = [
    "ANALYZER_ID",
    "DEPTH_ALERT_THRESHOLD",
    "analyze_blind_challenge",
]
