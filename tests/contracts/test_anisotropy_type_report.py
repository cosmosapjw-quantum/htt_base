"""PR-267 abstaining anisotropy-compatibility report contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from common.anchor_geometry import (
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (
    AnchoredResponseStatus,
    PrincipalAngleStatus,
    anchored_numeric_content_id,
    measure_anchored_response_geometry,
)
from common.anisotropy_type_report import (
    ANISOTROPY_TYPE_CLAIM_CEILING,
    ANISOTROPY_TYPE_FAMILY_GATE,
    AnisotropyCompatibilityStatus,
    AnisotropyTypeReportError,
    GeometryInformationStatus,
    LocalGlobalCompatibility,
    build_anisotropy_type_report,
    build_open_set_replay_inputs,
)
from common.conditional_exceedance import (
    ConditioningSource,
    ExceedanceLane,
    SamplingLaw,
    build_missing_probability_law_profile,
    build_null_calibrated_exceedance,
    build_sampling_draws,
    build_sampling_law_spec,
)
from common.depth_path import (
    DepthCoherenceStatus,
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
)
from common.open_set_response_classes import (
    OpenSetClassificationStatus,
    ResponseClassSourceSemantics,
    ResponseSupportKind,
    build_response_class_manifold,
    build_response_equivalence_report,
    classify_open_set_response,
    source_separation_not_applicable,
)
from common.orbit_catalogue_v3 import (
    CatalogueProofStatus,
    OrbitActionGroup,
    build_orbit_catalogue_v3_spec,
    orbit_catalogue_v3,
)
from common.orbit_nonlinearity import STF5_CARTESIAN_BASIS
from common.sky_support import build_sky_support_from_mask
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


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/vector_tensor/pr267_spec.yaml"
POLICY = (
    ROOT
    / "docs/research_program/vector_tensor/pr267_publication_policy.json"
)
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
FRAME = "PR267 registered Cartesian tetrad"
CONGRUENCE = "PR267 registered matter congruence"
EPOCH = "PR267 synthetic epoch"
SCALE = "PR267 synthetic averaging scale"
ORDER = "PR267 diagnostic order"


def _receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()


def _joint(*, geometry_complete: bool = True) -> JointAnisotropyState:
    kinematics = CongruenceKinematics(
        sigma_stf5=(0.2, -0.1, 0.03, -0.04, 0.05),
        omega_axial3=(0.01, -0.02, 0.03),
        acceleration_polar3=(0.02, 0.01, -0.01),
        frame=FRAME,
        congruence_id=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=ORDER,
        acceleration_normalization=AccelerationNormalization.A_OVER_C_THETA,
    )
    velocity = build_velocity_frame_bundle(
        beta_RO=(0.003, 0.001, -0.001),
        beta_RM=(0.001, 0.001, 0.0),
        beta_MO=(0.002, 0.0, -0.001),
        coordinate_frame=FRAME,
        radiation_frame_id="PR267 radiation frame",
        matter_frame_id="PR267 matter frame",
        observer_frame_id="PR267 observer frame",
        basis=STF5_CARTESIAN_BASIS,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        first_order_beta_ceiling=0.01,
    )
    tensors = (
        {
            "spatial_curvature_stf5": (0.1, -0.05, 0.01, 0.02, -0.01),
            "electric_weyl_stf5": (0.02, -0.01, 0.0, 0.01, 0.0),
            "magnetic_weyl_stf5": (0.01, -0.005, 0.0, 0.0, 0.0),
            "anisotropic_stress_stf5": (
                0.03,
                -0.015,
                0.005,
                -0.005,
                0.0,
            ),
        }
        if geometry_complete
        else {}
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
        **tensors,
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
        source_identity=f"PR267-JOINT-{geometry_complete}",
    )


def _orbit(state: JointAnisotropyState):
    spec = build_orbit_catalogue_v3_spec(
        catalogue_id="PR267-O3-RESPONSE-COMPATIBILITY",
        action_group=OrbitActionGroup.O3,
    )
    return orbit_catalogue_v3(state, spec)


def _anchored(*, rank_deficient: bool = False):
    normalizer = NormalizerSpec(
        normalizer_id="PR267-ANCHORED-NORMALIZER",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("u0", "u1"),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity="PR267-ANCHORED-COORDINATES",
        assumptions=("synthetic identity anchor",),
    )
    response = (
        ((1.0, 2.0), (0.0, 0.0), (0.0, 0.0))
        if rank_deficient
        else ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0))
    )
    covariance = np.eye(3)
    report = measure_anchored_response_geometry(
        response=response,
        covariance=covariance,
        normalizer=normalizer,
        parameter_labels=("u0", "u1"),
        transfer_id=_receipt("PR267-ANCHORED-TRANSFER-NONE"),
        transfer_source=TransferSource.NONE,
        mask_id=_receipt("PR267-ANCHORED-MASK"),
        covariance_id=anchored_numeric_content_id(covariance),
        comparison_response=response,
    )
    return report, normalizer, response


def _source_normalizer() -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="PR267-SOURCE-NORMALIZER",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("beta_MO_amplitude", "beta_RM_amplitude"),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity="PR267-SOURCE-COORDINATES",
        assumptions=("block-preserving synthetic map",),
    )


def _source_provider(
    hypothesis: SourceHypothesis,
    response: object,
):
    local = hypothesis is SourceHypothesis.LOCAL_BOOST
    return register_source_response_provider(
        provider_id=_receipt(f"PR267-PROVIDER-{hypothesis.value}"),
        hypothesis=hypothesis,
        velocity_component=(
            VelocityComponent.BETA_MO
            if local
            else VelocityComponent.BETA_RM
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
        transfer_id=_receipt("PR267-SOURCE-TRANSFER-NONE"),
        transfer_source=TransferSource.NONE,
        basis="PR267 registered response basis",
        epoch_window="PR267 registered response window",
        assumptions=("first-order analytic synthetic response",),
        caveats=("hypothesis-only response",),
    )


def _source_report(*, separable: bool = True):
    covariance = np.eye(2)
    normalizer = _source_normalizer()
    report = measure_source_response_geometry(
        local_provider=_source_provider(
            SourceHypothesis.LOCAL_BOOST,
            ((1.0,), (0.0,)),
        ),
        global_provider=_source_provider(
            SourceHypothesis.GLOBAL_TILT,
            ((0.0,), (1.0,)) if separable else ((2.0,), (0.0,)),
        ),
        covariance=covariance,
        normalizer=normalizer,
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=_receipt("PR267-SOURCE-MASK"),
        separation_threshold_radians=0.2,
    )
    return report, normalizer, covariance


def _source_classes(
    report,
    *,
    equivalent: bool = False,
    neutral: bool = False,
):
    local_nodes = ((-3.0, 0.0),)
    global_nodes = local_nodes if equivalent else ((3.0, 0.0),)
    return (
        build_response_class_manifold(
            class_id="response-class-local",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=report.local_provider.provider_id,
            observable_labels=report.observable_labels,
            convention_id=_receipt("PR267-RESPONSE-CONVENTION"),
            nuisance_policy_id=_receipt("PR267-NO-NUISANCE"),
            support_nodes=local_nodes,
            transfer_source=TransferSource.NONE,
            source_semantics=(
                ResponseClassSourceSemantics.NEUTRAL
                if neutral
                else ResponseClassSourceSemantics.LOCAL_BOOST
            ),
            source_response_id=(
                None if neutral else report.local_provider.response_id
            ),
        ),
        build_response_class_manifold(
            class_id="response-class-global",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=report.global_provider.provider_id,
            observable_labels=report.observable_labels,
            convention_id=_receipt("PR267-RESPONSE-CONVENTION"),
            nuisance_policy_id=_receipt("PR267-NO-NUISANCE"),
            support_nodes=global_nodes,
            transfer_source=TransferSource.NONE,
            source_semantics=(
                ResponseClassSourceSemantics.NEUTRAL
                if neutral
                else ResponseClassSourceSemantics.GLOBAL_TILT
            ),
            source_response_id=(
                None if neutral else report.global_provider.response_id
            ),
        ),
    )


def _open_set(
    source_report,
    source_normalizer,
    covariance,
    *,
    observation=(-3.0, 0.0),
    equivalent: bool = False,
    use_source_gate: bool = True,
):
    classes = _source_classes(
        source_report,
        equivalent=equivalent,
        neutral=not use_source_gate,
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
    gate = (
        source_separation_gate_from_pr256(
            source_report,
            classes=classes,
            covariance=covariance,
            nuisance_tangent=None,
            normalizer=source_normalizer,
            threshold_contract=PR283_DEFAULT_THRESHOLD_CONTRACT,
        )
        if use_source_gate
        else source_separation_not_applicable()
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
    return replay


def _profile(*, defined: bool = True):
    if not defined:
        return build_missing_probability_law_profile(
            profile_id="PR267-NO-LAW",
            functional_id="pr264.tr_sigma2",
            thresholds=(0.0, 1.0),
            conditioning_id="PR267-MISSING-CONDITIONING",
            reason="no probability law was admitted",
        )
    law = build_sampling_law_spec(
        law_id="PR267-MATCHED-NULL-LAW",
        sampling_law=SamplingLaw.FIXED_INJECTION_MOCK,
        conditioning_source=ConditioningSource.INJECTED,
        lane=ExceedanceLane.MIO_NULL,
        source_identity="PR267 preregistered synthetic null DGP",
        covariance_id="PR267-NULL-COVARIANCE",
        transfer_source="none",
        assumptions=("exchangeable draws under the synthetic null",),
    )
    draws = build_sampling_draws(
        draws_id="PR267-MATCHED-NULL-DRAWS",
        law=law,
        values=(0.1, 0.2, 0.4, 0.8),
        source_artifact_id="PR267-MATCHED-NULL-SOURCE",
        sample_unit="dimensionless functional value",
    )
    return build_null_calibrated_exceedance(
        profile_id="PR267-NULL-EXCEEDANCE",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.0, 0.5),
        law=law,
        draws=draws,
        conditioning_id="PR267-MATCHED-NULL-CONDITIONING",
        alpha=0.05,
    ).profile


def _stratum(suffix: str, *, depth: float, kept: tuple[int, ...]):
    mask = np.zeros(2, dtype=bool)
    mask[list(kept)] = True
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="GALACTIC",
        completeness_status="synthetic_fixture_complete",
        selection_mode=f"PR267-{suffix}",
        mock_coverage_status="synthetic_fixture",
        pixelization="PR267_TWO_PIXEL_FIXTURE",
    )
    return build_mask_stratum(
        stratum_id=f"PR267-{suffix}",
        depth_coordinate=depth,
        depth_unit="redshift_proxy",
        support_unit_ids=tuple(f"pixel-{index}" for index in kept),
        support_universe_size=2,
        sky_support=support,
        selection_id=f"sha256:selection-{suffix}",
        covariance_id=f"sha256:covariance-{suffix}",
        source_artifact_id=f"sha256:source-{suffix}",
        feature_names=("obs-x", "obs-y"),
        feature_unit="dimensionless_observable",
        assumptions=("synthetic observer-side fixture",),
    )


def _depth(*, defined: bool = True):
    strata = (
        _stratum("D1", depth=0.1, kept=(0, 1)),
        _stratum("D2", depth=0.2, kept=(0,)),
    )
    kernel = build_transport_kernel(
        transport_id="PR267-K12",
        source=strata[0],
        target=strata[1],
        matrix=((1.0, 0.0), (0.0, 1.0)),
        mask_transport_id="sha256:mask-k12",
        selection_transport_id="sha256:selection-k12",
        covariance_transport_id="sha256:covariance-k12",
        method_id="PR267-LINEAR-TRANSPORT-V1",
        assumptions=("dimensionless deterministic transport",),
    )
    path = build_depth_path(
        path_id="PR267-PATH",
        strata=strata,
        kernels=(kernel,),
    )
    covariance = (
        ((0.1, 0.0), (0.0, 0.1))
        if defined
        else ((0.0, 0.0), (0.0, 0.0))
    )
    steps = tuple(
        build_observable_feature_step(
            step_id=f"PR267-STEP-{stratum.stratum_id}",
            stratum=stratum,
            values=(1.0, 2.0),
            covariance=covariance,
            source_artifact_id=f"sha256:feature-{stratum.stratum_id}",
            extraction_method_id="PR267-SYNTHETIC-FEATURE-V1",
            sample_count=32,
        )
        for stratum in strata
    )
    coherence = build_depth_coherence_report(
        report_id="PR267-DEPTH-COHERENCE",
        path=path,
        steps=steps,
    )
    return path, coherence


def _inputs(
    *,
    geometry_complete: bool = True,
    anchored_rank_deficient: bool = False,
    source_separable: bool = True,
    observation=(-3.0, 0.0),
    equivalent: bool = False,
    use_source_gate: bool = True,
    profile_defined: bool = True,
    depth_defined: bool = True,
):
    state = _joint(geometry_complete=geometry_complete)
    anchored, anchored_normalizer, comparison = _anchored(
        rank_deficient=anchored_rank_deficient
    )
    source, source_normalizer, covariance = _source_report(
        separable=source_separable
    )
    local_global = build_local_global_compatibility_input(
        report=source,
        normalizer=source_normalizer,
    )
    open_set = _open_set(
        source,
        source_normalizer,
        covariance,
        observation=observation,
        equivalent=equivalent,
        use_source_gate=use_source_gate,
    )
    path, coherence = _depth(defined=depth_defined)
    return {
        "report_id": "PR267-ANISOTROPY-TYPE-REPORT",
        "joint_state": state,
        "orbit_report": _orbit(state),
        "anchored_response": anchored,
        "anchored_normalizer": anchored_normalizer,
        "anchored_comparison_response": comparison,
        "local_global": local_global,
        "open_set": open_set,
        "conditional_exceedance": _profile(defined=profile_defined),
        "depth_path": path,
        "depth_coherence": coherence,
    }


def _build(**overrides):
    return build_anisotropy_type_report(**_inputs(**overrides))


def test_spec_card_and_policy_bind_dependencies_and_c2_ceiling() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    backlog = yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))
    card = next(row for row in backlog["prs"] if row["id"] == "PR-267")
    dependencies = [
        "PR-263",
        "PR-265",
        "PR-266",
        "PR-255",
        "PR-256",
        "PR-258",
    ]
    assert spec["dependencies"] == card["depends"] == dependencies
    assert spec["owner"] == card["owner"] == "COMMON"
    assert spec["contributors"] == card["contributors"] == [
        "OBSSTAT",
        "MIO",
        "HTT",
    ]
    assert spec["claim_boundary"]["ceiling"] == "diagnostic_only"
    assert spec["family_identification_gate"]["c6_status"] == "BLOCKED"
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == (
        "BLOCKED_PRE_NATIVE_ATLAS"
    )


def test_complete_inputs_yield_only_response_compatibility_candidate() -> None:
    report = _build()
    assert report.compatibility_status is (
        AnisotropyCompatibilityStatus.RESPONSE_COMPATIBILITY_CANDIDATE
    )
    assert report.geometry_information_status is (
        GeometryInformationStatus.COMPLETE
    )
    assert report.anchored_status is AnchoredResponseStatus.MEASURED
    assert report.anchored_principal_angle_status is PrincipalAngleStatus.DEFINED
    assert report.local_global_status is (
        LocalGlobalCompatibility.SEPARABLE_CANDIDATE
    )
    assert report.open_set_status is (
        OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    )
    assert report.response_class_ids == ("response-class-local",)
    assert report.depth_coherence_status is DepthCoherenceStatus.DEFINED
    assert report.claim_ceiling == ANISOTROPY_TYPE_CLAIM_CEILING
    assert report.family_identification_gate == ANISOTROPY_TYPE_FAMILY_GATE
    assert report.orbit_proof_statuses == (
        CatalogueProofStatus.UNPROVEN.value,
        CatalogueProofStatus.UNPROVEN.value,
        CatalogueProofStatus.UNPROVEN.value,
    )


def test_missing_geometry_yields_partial_without_nearest_label() -> None:
    report = _build(geometry_complete=False)
    assert report.geometry_information_status is GeometryInformationStatus.MISSING
    assert report.compatibility_status is (
        AnisotropyCompatibilityStatus.PARTIAL_DIAGNOSTIC
    )
    assert len(
        [value for value in report.missingness if value.startswith("geometry:")]
    ) == 4
    payload = report.as_payload()
    assert "family_label" not in payload
    assert "nearest_label" not in payload
    assert "geometry_label" not in payload


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        (
            {"anchored_rank_deficient": True},
            AnisotropyCompatibilityStatus.INDETERMINATE,
        ),
        (
            {"source_separable": False},
            AnisotropyCompatibilityStatus.INDETERMINATE,
        ),
        (
            {
                "equivalent": True,
            },
            AnisotropyCompatibilityStatus.INDETERMINATE,
        ),
        (
            {"observation": (10.0, 10.0)},
            AnisotropyCompatibilityStatus.UNKNOWN,
        ),
        (
            {"profile_defined": False},
            AnisotropyCompatibilityStatus.PARTIAL_DIAGNOSTIC,
        ),
        (
            {"depth_defined": False},
            AnisotropyCompatibilityStatus.PARTIAL_DIAGNOSTIC,
        ),
    ),
)
def test_abstention_precedence(kwargs, expected) -> None:
    report = _build(**kwargs)
    assert report.compatibility_status is expected
    if expected is not (
        AnisotropyCompatibilityStatus.RESPONSE_COMPATIBILITY_CANDIDATE
    ):
        assert "nearest_label" not in report.as_payload()


def test_pr256_adapter_matches_pr258_source_gate_exactly() -> None:
    values = _inputs()
    local_global = values["local_global"]
    gate = values["open_set"].source_separation_gate
    assert local_global.source_report_id == gate.report_id
    assert local_global.status.value == gate.status.value
    assert local_global.claim_ceiling == "diagnostic_only"


@pytest.mark.parametrize(
    "smuggled_id",
    (
        "response-class-type-vii-h",
        "response-class-type-ix",
        "response-class-neutral-type-vii-h",
    ),
)
def test_only_exact_role_vocabulary_can_enter_report(
    smuggled_id: str,
) -> None:
    source, _, covariance = _source_report()
    smuggled = build_response_class_manifold(
        class_id=smuggled_id,
        support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
        provider_id=_receipt(f"PR267-SMUGGLED-{smuggled_id}"),
        observable_labels=source.observable_labels,
        convention_id=_receipt("PR267-SMUGGLED-CONVENTION"),
        nuisance_policy_id=_receipt("PR267-SMUGGLED-NUISANCE"),
        support_nodes=((-3.0, 0.0),),
        transfer_source=TransferSource.NONE,
        source_semantics=ResponseClassSourceSemantics.NEUTRAL,
        source_response_id=None,
    )
    control = build_response_class_manifold(
        class_id="response-class-control",
        support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
        provider_id=_receipt("PR267-SMUGGLED-CONTROL"),
        observable_labels=source.observable_labels,
        convention_id=_receipt("PR267-SMUGGLED-CONVENTION"),
        nuisance_policy_id=_receipt("PR267-SMUGGLED-NUISANCE"),
        support_nodes=((3.0, 0.0),),
        transfer_source=TransferSource.NONE,
        source_semantics=ResponseClassSourceSemantics.NEUTRAL,
        source_response_id=None,
    )
    classes = (smuggled, control)
    equivalence = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.1,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        reopening_observables=(),
    )
    gate = source_separation_not_applicable()
    classification = classify_open_set_response(
        observation=(-3.0, 0.0),
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
    assert classification.status is (
        OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    )
    with pytest.raises(
        AnisotropyTypeReportError,
        match="exact registered neutral/local/global",
    ):
        build_open_set_replay_inputs(
            classification_report=classification,
            classes=classes,
            equivalence_report=equivalence,
            observation=(-3.0, 0.0),
            covariance=covariance,
            nuisance_tangent=None,
            source_separation_gate=gate,
            absolute_tolerance=1.0e-12,
            relative_tolerance=1.0e-12,
        )


def test_registered_ids_are_fixed_by_source_semantics() -> None:
    values = _inputs()
    assert {
        item.source_semantics: item.class_id
        for item in values["open_set"].classes
    } == {
        ResponseClassSourceSemantics.LOCAL_BOOST: "response-class-local",
        ResponseClassSourceSemantics.GLOBAL_TILT: "response-class-global",
    }


def test_source_gate_mismatch_is_rejected() -> None:
    values = _inputs()
    local_global = values["local_global"]
    object.__setattr__(
        local_global,
        "source_report_id",
        _receipt("PR267-FORGED-SOURCE-REPORT"),
    )
    with pytest.raises(
        AnisotropyTypeReportError,
        match="identity drifted",
    ):
        build_anisotropy_type_report(**values)


@pytest.mark.parametrize(
    "name",
    (
        "open_set",
        "conditional_exceedance",
        "depth_coherence",
    ),
)
def test_sealed_upstream_mutation_is_rejected(name: str) -> None:
    values = _inputs()
    target = values[name]
    if name == "open_set":
        object.__setattr__(
            target.classification_report,
            "candidate_class_id",
            "response-class-forged",
        )
    elif name == "conditional_exceedance":
        object.__setattr__(target, "profile_id", "PR267-FORGED-PROFILE")
    else:
        object.__setattr__(target, "report_id", "PR267-FORGED-DEPTH")
    with pytest.raises((AnisotropyTypeReportError, ValueError)):
        build_anisotropy_type_report(**values)


def test_orbit_and_anchored_replay_mutations_are_rejected() -> None:
    orbit_values = _inputs()
    object.__setattr__(
        orbit_values["orbit_report"].stratum,
        "discriminant",
        999.0,
    )
    with pytest.raises(ValueError, match="does not match"):
        build_anisotropy_type_report(**orbit_values)

    anchored_values = _inputs()
    object.__setattr__(
        anchored_values["anchored_response"],
        "rank",
        0,
    )
    with pytest.raises(
        AnisotropyTypeReportError,
        match="failed exact replay",
    ):
        build_anisotropy_type_report(**anchored_values)


def test_public_surfaces_preserve_owner_separation() -> None:
    import htt.infer.anisotropy_type_report as htt_surface
    import mio.formalism.depth_path as mio_depth
    import obsstat.depth_path as obsstat_depth

    assert hasattr(htt_surface, "build_local_global_compatibility_input")
    assert not hasattr(htt_surface, "build_anisotropy_type_report")
    assert not hasattr(htt_surface, "build_conditional_exceedance_envelope")
    assert not hasattr(mio_depth, "build_anisotropy_type_report")
    assert not hasattr(obsstat_depth, "build_anisotropy_type_report")
