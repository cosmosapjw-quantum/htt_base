"""PR-261 canonical joint vector/tensor anisotropy-state contracts."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from common.joint_anisotropy_state import (
    AccelerationNormalization,
    BetaSemanticRole,
    CongruenceKinematics,
    GeometryCompleteness,
    GeometryState,
    JOINT_STATE_CLAIM_CEILING,
    JointAnisotropyState,
    JointAnisotropyStateError,
    JointStateSourceKind,
    LegacyAdapterStatus,
    LegacyDepartureAdapterReport,
    LegacyDepartureBinding,
    MissingComponent,
    MissingComponentStatus,
    UnitsConvention,
    VelocityClosureStatus,
    VelocityNormalization,
    adapt_legacy_departure_state,
    apply_o3_action,
    build_velocity_frame_bundle,
    convert_acceleration_units,
    departure_state_content_id,
    from_pr256_velocity_payload,
    missing_component,
)
from common.orbit_nonlinearity import (
    DEPARTURE_O3_PARITY,
    DEPARTURE_O3_UNITS,
    O3Transform,
    STF5_CARTESIAN_BASIS,
    transform_departure_state,
)
from common.statistical_foundations import DepartureState
from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferSource,
    TransferValidRange,
)
from htt.departure.velocity_frame_decomposition import (
    build_velocity_frame_decomposition,
)


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "htt/src/common/joint_anisotropy_state.py"
SPEC = ROOT / "docs/research_program/vector_tensor/pr261_spec.yaml"
POLICY = (
    ROOT
    / "docs/research_program/vector_tensor/pr261_publication_policy.json"
)
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"

FRAME = "registered observer Cartesian tetrad"
CONGRUENCE = "registered matter congruence"
EPOCH = "z in [0, 0.1]"
SCALE = "100 Mpc"
ORDER = "registered linear kinematic order"


def _missing(name: str) -> MissingComponent:
    return missing_component(
        name,
        f"{name} unavailable in fixture",
        required_for=("complete fixture",),
    )


def _kinematics(
    *,
    acceleration: object = (0.01, -0.02, 0.03),
    units: UnitsConvention = UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
    frame: str = FRAME,
    congruence: str = CONGRUENCE,
) -> CongruenceKinematics:
    normalization = (
        None
        if isinstance(acceleration, MissingComponent)
        else (
            AccelerationNormalization.A_OVER_C_THETA
            if units is UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
            else AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
        )
    )
    return CongruenceKinematics(
        sigma_stf5=(0.2, -0.1, 0.03, -0.04, 0.05),
        omega_axial3=(0.01, -0.02, 0.03),
        acceleration_polar3=acceleration,
        frame=frame,
        congruence_id=congruence,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=units,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=ORDER,
        acceleration_normalization=normalization,
    )


def _velocity(
    *,
    beta_ro: object = (0.003, 0.001, -0.001),
    beta_rm: object = (0.001, 0.001, 0.0),
    beta_mo: object = (0.002, 0.0, -0.001),
    frame: str = FRAME,
    epoch: str = EPOCH,
) -> object:
    return build_velocity_frame_bundle(
        beta_RO=beta_ro,
        beta_RM=beta_rm,
        beta_MO=beta_mo,
        coordinate_frame=frame,
        radiation_frame_id="radiation-rest-frame",
        matter_frame_id="matter-rest-frame",
        observer_frame_id="local-observer-frame",
        basis=STF5_CARTESIAN_BASIS,
        epoch_window=epoch,
        averaging_scale=SCALE,
        first_order_beta_ceiling=0.01,
    )


def _geometry(
    *,
    frame: str = FRAME,
    congruence: str = CONGRUENCE,
    units: UnitsConvention = UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
) -> GeometryState:
    return GeometryState(
        delta_omega_k=-0.02,
        frame=frame,
        congruence_id=congruence,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=units,
        perturbative_order=ORDER,
    )


def _external_transfer() -> TransferFunctionSpec:
    return TransferFunctionSpec(
        transfer_id="external.pr261.fixture",
        source=TransferSource.EXTERNAL_TRANSFER,
        family="generic_anisotropy_fixture",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=30,
        ),
        observable_kind=ObservableKind.TEMPLATE,
        normalization="registered fixture normalization",
        calibration_status=CalibrationStatus.EXTERNAL_CALIBRATED,
        caveats=(
            "external-transfer path",
            "transfer-conditional diagnostic only",
        ),
        source_ref="fixture:pr261",
        version="pr261-test-v1",
    )


def _joint(
    *,
    kinematics: CongruenceKinematics | None = None,
    velocity: object | None = None,
    geometry: GeometryState | None = None,
    transfer: bool = False,
) -> JointAnisotropyState:
    spec = _external_transfer() if transfer else None
    return JointAnisotropyState(
        congruence_kinematics=(
            _kinematics() if kinematics is None else kinematics
        ),
        velocity_frames=_velocity() if velocity is None else velocity,
        geometry_state=_geometry() if geometry is None else geometry,
        frame=FRAME,
        congruence=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        perturbative_order=ORDER,
        beta_semantic_role=BetaSemanticRole.DIRECT_STATE,
        transfer_source=(
            TransferSource.EXTERNAL_TRANSFER
            if transfer
            else TransferSource.NONE
        ),
        transfer_spec=spec,
        source_kind=JointStateSourceKind.DIRECT,
        source_identity="PR261-DIRECT-FIXTURE",
    )


def _legacy_state() -> DepartureState:
    return DepartureState(
        sigma_ab=(0.2, -0.1, 0.03, -0.04, 0.05),
        omega_a=(0.01, -0.02, 0.03),
        beta_a=(0.001, 0.002, -0.001),
        delta_omega_k=-0.02,
        frame=FRAME,
        congruence=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units=DEPARTURE_O3_UNITS,
        parity=DEPARTURE_O3_PARITY,
        perturbative_order=ORDER,
    )


def _legacy_binding(
    role: BetaSemanticRole = BetaSemanticRole.BETA_RM,
    state: DepartureState | None = None,
) -> LegacyDepartureBinding:
    bound_state = _legacy_state() if state is None else state
    return LegacyDepartureBinding(
        beta_semantic_role=role,
        source_state_id=departure_state_content_id(bound_state),
        semantic_authority_id=(
            "sha256:"
            + hashlib.sha256(
                b"PR261 test semantic authority"
            ).hexdigest()
        ),
        assumptions=(
            "fixture explicitly binds legacy beta semantics",
            "legacy components already use the declared normalizations",
        ),
        source_basis=STF5_CARTESIAN_BASIS,
        source_units=DEPARTURE_O3_UNITS,
        source_parity=DEPARTURE_O3_PARITY,
        sigma_normalization="SIGMA_OVER_THETA_STF5",
        omega_normalization="OMEGA_OVER_THETA_AXIAL3",
        beta_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        radiation_frame_id="radiation-rest-frame",
        matter_frame_id="matter-rest-frame",
        observer_frame_id="local-observer-frame",
        first_order_beta_ceiling=0.01,
    )


def test_pr261_spec_card_and_review_policy_bind_exact_scope() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    backlog = yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))
    card = next(row for row in backlog["prs"] if row["id"] == "PR-261")

    assert spec["work_unit_id"] == "PR-261"
    assert spec["change_set_id"] == "CS-PR261-JOINT-ANISOTROPY-STATE"
    assert spec["controlling_assumptions"]["metric_signature"] == "(-,+,+,+)"
    assert spec["controlling_assumptions"]["native_lowell_solver_available"] is False
    assert {
        "CongruenceKinematics",
        "VelocityFrameBundle",
        "GeometryState",
        "JointAnisotropyState",
        "MissingComponent",
    } == set(spec["required_public_types"])
    assert set(card["depends"]) == {"PR-260", "PR-249", "PR-256"}
    assert card["claim_tier_ceiling"] == "diagnostic_only"
    assert policy["policy_id"] == "PR261-PUBLICATION-POLICY"
    assert policy["publication_requires_external_publisher"] is True
    assert policy["ordinary_agent_push_forbidden"] is True
    assert {row["id"] for row in policy["required_commands"]} == {
        "pr261-focused",
        "pr261-adjacent",
        "pr261-dag-strict",
        "pr261-claim-language",
        "pr261-smoke",
    }
    assert {
        "typed_missingness",
        "units_and_acceleration_normalization",
        "legacy_value_and_role_safety",
        "o3_action_and_parity",
        "transfer_provenance",
        "claim_ceiling",
    } <= set(policy["required_review_cells"])


def test_joint_state_round_trip_binds_component_and_transfer_identities() -> None:
    state = _joint(transfer=True)
    serialized = json.loads(
        json.dumps(state.to_payload(), sort_keys=True, allow_nan=False)
    )

    replay = JointAnisotropyState.from_payload(serialized)

    assert replay == state
    assert replay.content_id == state.content_id
    assert replay.kinematics_ref == state.congruence_kinematics.content_id
    assert replay.velocity_ref == state.velocity_frames.content_id
    assert replay.geometry_ref == state.geometry_state.content_id
    assert replay.transfer_spec == _external_transfer()
    assert replay.claim_ceiling == JOINT_STATE_CLAIM_CEILING
    assert "Bianchi family identification" in replay.forbidden_use


def test_serialized_refs_claim_boundary_and_unknown_fields_fail_closed() -> None:
    state = _joint()
    payload = state.to_payload()

    bad_ref = dict(payload)
    bad_ref["kinematics_ref"] = "sha256:" + "0" * 64
    with pytest.raises(JointAnisotropyStateError, match="kinematics_ref"):
        JointAnisotropyState.from_payload(bad_ref)

    bad_claim = dict(payload)
    bad_claim["claim_ceiling"] = "native_family_identification"
    with pytest.raises(JointAnisotropyStateError, match="claim ceiling"):
        JointAnisotropyState.from_payload(bad_claim)

    extra = dict(payload)
    extra["silent_scalar_promotion"] = True
    with pytest.raises(JointAnisotropyStateError, match="keys mismatch"):
        JointAnisotropyState.from_payload(extra)


def test_acceleration_units_are_typed_and_mismatches_are_rejected() -> None:
    with pytest.raises(
        JointAnisotropyStateError,
        match="does not match units_convention",
    ):
        replace(
            _kinematics(),
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            ),
        )

    with pytest.raises(
        JointAnisotropyStateError,
        match="requires acceleration_normalization",
    ):
        replace(_kinematics(), acceleration_normalization=None)

    with pytest.raises(
        JointAnisotropyStateError,
        match="must not carry a normalization",
    ):
        _kinematics(acceleration=_missing("acceleration_polar3")).__class__(
            sigma_stf5=(0.0,) * 5,
            omega_axial3=(0.0,) * 3,
            acceleration_polar3=_missing("acceleration_polar3"),
            frame=FRAME,
            congruence_id=CONGRUENCE,
            epoch_window=EPOCH,
            averaging_scale=SCALE,
            basis=STF5_CARTESIAN_BASIS,
            units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
            velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
            perturbative_order=ORDER,
            acceleration_normalization=(
                AccelerationNormalization.A_OVER_C_THETA
            ),
        )


def test_explicit_c_and_natural_unit_acceleration_round_trip_is_explicit() -> None:
    source = _kinematics(acceleration=(0.125, -0.25, 0.5))

    natural = convert_acceleration_units(
        source,
        UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
        c_numeric_in_source_velocity_units=8.0,
    )
    replay = convert_acceleration_units(
        natural,
        UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        c_numeric_in_source_velocity_units=8.0,
    )

    assert natural.acceleration_polar3 == (1.0, -2.0, 4.0)
    assert (
        natural.acceleration_normalization
        is AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
    )
    assert replay.acceleration_polar3 == source.acceleration_polar3
    assert replay.units_convention is source.units_convention
    with pytest.raises(JointAnisotropyStateError, match="positive"):
        convert_acceleration_units(
            source,
            UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED,
            c_numeric_in_source_velocity_units=0.0,
        )


@pytest.mark.parametrize(
    ("component", "replacement_value", "match"),
    [
        ("frame", "wrong frame", "kinematics.frame"),
        ("congruence", "wrong congruence", "kinematics.congruence_id"),
        ("epoch_window", "wrong epoch", "kinematics.epoch_window"),
        ("averaging_scale", "wrong scale", "kinematics.averaging_scale"),
    ],
)
def test_joint_state_rejects_frame_congruence_and_support_mismatch(
    component: str,
    replacement_value: str,
    match: str,
) -> None:
    kwargs = _joint().__dict__.copy()
    kwargs[component] = replacement_value
    with pytest.raises(JointAnisotropyStateError, match=match):
        JointAnisotropyState(**kwargs)


def test_partial_components_remain_typed_and_never_become_zero() -> None:
    acceleration = _missing("acceleration_polar3")
    kinematics = _kinematics(acceleration=acceleration)
    velocity = _velocity(
        beta_ro=_missing("beta_RO"),
        beta_rm=(0.001, 0.0, 0.0),
        beta_mo=(0.002, 0.0, 0.0),
    )
    geometry = _geometry()
    state = _joint(
        kinematics=kinematics,
        velocity=velocity,
        geometry=geometry,
    )

    assert state.congruence_kinematics.acceleration_polar3 is acceleration
    assert isinstance(state.velocity_frames.beta_RO, MissingComponent)
    assert (
        state.velocity_frames.status
        is VelocityClosureStatus.MISSING_COMPONENT
    )
    assert state.geometry_state.completeness is GeometryCompleteness.PARTIAL
    assert isinstance(
        state.geometry_state.spatial_curvature_stf5,
        MissingComponent,
    )
    assert (
        state.geometry_state.spatial_curvature_stf5.status
        is MissingComponentStatus.NEEDS_NATIVE
    )
    assert state.geometry_state.delta_omega_k == -0.02


def test_velocity_bundle_does_not_derive_missing_component() -> None:
    bundle = _velocity(
        beta_ro=_missing("beta_RO"),
        beta_rm=(0.001, 0.0, 0.0),
        beta_mo=(0.002, 0.0, 0.0),
    )

    assert isinstance(bundle.beta_RO, MissingComponent)
    assert bundle.beta_RM == (0.001, 0.0, 0.0)
    assert bundle.beta_MO == (0.002, 0.0, 0.0)
    assert isinstance(bundle.closure_residual, MissingComponent)
    assert bundle.status is VelocityClosureStatus.MISSING_COMPONENT


def test_pr256_adapter_replays_closure_without_common_to_htt_dependency() -> None:
    report = build_velocity_frame_decomposition(
        beta_RO=(0.003, 0.001, -0.001),
        beta_RM=(0.001, 0.001, 0.0),
        beta_MO=(0.002, 0.0, -0.001),
        basis=STF5_CARTESIAN_BASIS,
        epoch_window=EPOCH,
        first_order_beta_ceiling=0.01,
    )

    bundle = from_pr256_velocity_payload(
        report.as_payload(),
        coordinate_frame=FRAME,
        radiation_frame_id="radiation-rest-frame",
        matter_frame_id="matter-rest-frame",
        observer_frame_id="local-observer-frame",
        averaging_scale=SCALE,
    )

    assert bundle.status.value == report.status.value
    assert bundle.beta_RO == report.beta_RO
    assert bundle.closure_residual == report.closure_residual
    assert isinstance(bundle.source_decomposition_id, str)
    source = MODULE.read_text(encoding="utf-8")
    assert "from htt." not in source
    assert "import htt." not in source
    assert "from tsc" not in source.lower()
    assert "from teff" not in source.lower()

    promoted = report.as_payload()
    promoted["forbidden_use"] = []
    with pytest.raises(JointAnisotropyStateError, match="claim boundary"):
        from_pr256_velocity_payload(
            promoted,
            coordinate_frame=FRAME,
            radiation_frame_id="radiation-rest-frame",
            matter_frame_id="matter-rest-frame",
            observer_frame_id="local-observer-frame",
            averaging_scale=SCALE,
        )


def test_legacy_adapter_abstains_without_semantic_binding() -> None:
    legacy = _legacy_state()
    before = legacy.vector

    report = adapt_legacy_departure_state(legacy, None)

    assert report.status is LegacyAdapterStatus.ABSTAIN
    assert report.joint_state is None
    assert isinstance(report.binding_id, MissingComponent)
    assert report.binding_id.status is MissingComponentStatus.ABSTAIN
    assert report.preserved_legacy_vector == before == legacy.vector
    with pytest.raises(JointAnisotropyStateError, match="must be created"):
        LegacyDepartureAdapterReport(
            status=LegacyAdapterStatus.ABSTAIN,
            source_state_id=report.source_state_id,
            binding_id=report.binding_id,
            joint_state=None,
            disposition=report.disposition,
            preserved_legacy_vector=before,
        )


def test_legacy_adapter_preserves_values_and_maps_only_declared_beta_role() -> None:
    legacy = _legacy_state()
    original_payload = legacy.__dict__.copy()

    report = adapt_legacy_departure_state(
        legacy,
        _legacy_binding(BetaSemanticRole.BETA_MO),
    )

    assert report.status is LegacyAdapterStatus.ADAPTED
    assert report.joint_state is not None
    joint = report.joint_state
    assert joint.beta_semantic_role is BetaSemanticRole.BETA_MO
    assert joint.velocity_frames.beta_MO == legacy.beta_a
    assert isinstance(joint.velocity_frames.beta_RO, MissingComponent)
    assert isinstance(joint.velocity_frames.beta_RM, MissingComponent)
    assert isinstance(
        joint.congruence_kinematics.acceleration_polar3,
        MissingComponent,
    )
    assert joint.geometry_state.delta_omega_k == legacy.delta_omega_k
    assert legacy.__dict__ == original_payload
    assert legacy.vector == report.preserved_legacy_vector


def test_legacy_adapter_refuses_metadata_drift_and_unresolved_role() -> None:
    legacy = _legacy_state()
    bad_binding = replace(_legacy_binding(), source_units="wrong units")

    report = adapt_legacy_departure_state(legacy, bad_binding)

    assert report.status is LegacyAdapterStatus.ABSTAIN
    assert report.joint_state is None
    assert report.disposition is not None
    assert "units" in report.disposition.reason
    different_state = replace(legacy, beta_a=(0.002, 0.002, -0.001))
    identity_report = adapt_legacy_departure_state(
        different_state,
        _legacy_binding(state=legacy),
    )
    assert identity_report.status is LegacyAdapterStatus.ABSTAIN
    assert identity_report.disposition is not None
    assert "source_state_id" in identity_report.disposition.reason
    with pytest.raises(JointAnisotropyStateError, match="requires BETA"):
        _legacy_binding(BetaSemanticRole.UNRESOLVED)


def test_o3_action_matches_legacy_action_and_keeps_polar_axial_types() -> None:
    legacy = _legacy_state()
    adapted = adapt_legacy_departure_state(legacy, _legacy_binding())
    assert adapted.joint_state is not None
    reflection = O3Transform(
        matrix=((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        transform_id="reflection-x",
        coordinate_frame=FRAME,
    )

    joint_reflected = apply_o3_action(adapted.joint_state, reflection)
    legacy_reflected = transform_departure_state(legacy, reflection)

    assert (
        joint_reflected.congruence_kinematics.sigma_stf5
        == legacy_reflected.sigma_ab
    )
    assert (
        joint_reflected.congruence_kinematics.omega_axial3
        == legacy_reflected.omega_a
    )
    assert joint_reflected.velocity_frames.beta_RM == legacy_reflected.beta_a
    assert (
        joint_reflected.source_kind is JointStateSourceKind.O3_ACTION
    )
    assert joint_reflected.geometry_state.delta_omega_k == legacy.delta_omega_k


def test_full_geometry_o3_parity_distinguishes_magnetic_weyl() -> None:
    tensor = (0.2, -0.1, 0.03, -0.04, 0.05)
    geometry = replace(
        _geometry(),
        spatial_curvature_stf5=tensor,
        electric_weyl_stf5=tensor,
        magnetic_weyl_stf5=tensor,
        anisotropic_stress_stf5=tensor,
    )
    state = _joint(geometry=geometry)
    inversion = O3Transform(
        matrix=((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
        transform_id="inversion",
        coordinate_frame=FRAME,
    )

    transformed = apply_o3_action(state, inversion)

    assert transformed.geometry_state.completeness is (
        GeometryCompleteness.COMPLETE_REGISTERED_COMPONENTS
    )
    assert transformed.geometry_state.spatial_curvature_stf5 == tensor
    assert transformed.geometry_state.electric_weyl_stf5 == tensor
    assert transformed.geometry_state.magnetic_weyl_stf5 == tuple(
        -value for value in tensor
    )
    assert transformed.geometry_state.anisotropic_stress_stf5 == tensor


@pytest.mark.parametrize(
    "sigma",
    [
        (0.2, 0.2, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
    ],
)
def test_repeated_eigenvalue_and_zero_shear_states_round_trip_without_label(
    sigma: tuple[float, ...],
) -> None:
    kinematics = replace(_kinematics(), sigma_stf5=sigma)
    state = _joint(kinematics=kinematics)

    replay = JointAnisotropyState.from_payload(state.to_payload())

    assert replay.congruence_kinematics.sigma_stf5 == sigma
    assert not hasattr(replay, "orbit_stratum")
    assert not hasattr(replay, "family")


def test_non_geodesic_acceleration_is_congruence_typed_not_an_mes_ceiling() -> None:
    kinematics = _kinematics(
        congruence="non-geodesic photon-baryon congruence",
        acceleration=(0.01, 0.0, 0.0),
    )
    geometry = _geometry(
        congruence="non-geodesic photon-baryon congruence",
    )
    state = JointAnisotropyState(
        congruence_kinematics=kinematics,
        velocity_frames=_velocity(),
        geometry_state=geometry,
        frame=FRAME,
        congruence="non-geodesic photon-baryon congruence",
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        perturbative_order=ORDER,
        beta_semantic_role=BetaSemanticRole.DIRECT_STATE,
        transfer_source=TransferSource.NONE,
        transfer_spec=None,
        source_kind=JointStateSourceKind.DIRECT,
        source_identity="PR261-NONGEODESIC-FIXTURE",
    )

    assert state.congruence_kinematics.congruence_id == state.congruence
    assert not hasattr(state.congruence_kinematics, "mes_ceiling")
    assert any(
        "geometry detection" in item for item in state.forbidden_use
    )


@pytest.mark.parametrize(
    ("beta_ro", "beta_rm", "beta_mo", "expected"),
    [
        (
            (0.0, 0.0, 0.0),
            _missing("beta_RM"),
            (0.001, 0.0, 0.0),
            VelocityClosureStatus.SUM_ONLY,
        ),
        (
            _missing("beta_RO"),
            (0.001, 0.0, 0.0),
            _missing("beta_MO"),
            VelocityClosureStatus.MISSING_COMPONENT,
        ),
        (
            _missing("beta_RO"),
            _missing("beta_RM"),
            _missing("beta_MO"),
            VelocityClosureStatus.MISSING_COMPONENT,
        ),
    ],
)
def test_local_global_and_no_tilt_limits_remain_diagnostic_only(
    beta_ro: object,
    beta_rm: object,
    beta_mo: object,
    expected: VelocityClosureStatus,
) -> None:
    kinematics = CongruenceKinematics(
        sigma_stf5=(0.0,) * 5,
        omega_axial3=(0.0,) * 3,
        acceleration_polar3=_missing("acceleration_polar3"),
        frame=FRAME,
        congruence_id=CONGRUENCE,
        epoch_window=EPOCH,
        averaging_scale=SCALE,
        basis=STF5_CARTESIAN_BASIS,
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=ORDER,
        acceleration_normalization=None,
    )
    state = _joint(
        kinematics=kinematics,
        velocity=_velocity(
            beta_ro=beta_ro,
            beta_rm=beta_rm,
            beta_mo=beta_mo,
        ),
        geometry=replace(_geometry(), delta_omega_k=0.0),
    )

    assert state.velocity_frames.status is expected
    assert state.geometry_state.completeness is GeometryCompleteness.PARTIAL
    assert "FLRW converse from component zeros" in state.forbidden_use
    assert not hasattr(state, "family")
    assert not hasattr(state, "posterior")


def test_transfer_binding_and_numeric_shape_mutations_fail_closed() -> None:
    with pytest.raises(JointAnisotropyStateError, match="requires"):
        replace(
            _joint(),
            transfer_source=TransferSource.EXTERNAL_TRANSFER,
            transfer_spec=None,
        )
    with pytest.raises(JointAnisotropyStateError, match="must match"):
        replace(
            _joint(transfer=True),
            transfer_source=TransferSource.EMPIRICAL_PROXY,
        )
    with pytest.raises(JointAnisotropyStateError, match="length 5"):
        replace(_kinematics(), sigma_stf5=(0.0,) * 4)
    with pytest.raises(JointAnisotropyStateError, match="must not be boolean"):
        replace(
            _kinematics(),
            omega_axial3=(True, 0.0, 0.0),
        )
    with pytest.raises(JointAnisotropyStateError, match="finite"):
        replace(
            _geometry(),
            delta_omega_k=np.nan,
        )


def test_velocity_closure_mismatch_and_frame_action_refusal() -> None:
    bundle = _velocity(
        beta_ro=(0.009, 0.0, 0.0),
        beta_rm=(0.001, 0.0, 0.0),
        beta_mo=(0.001, 0.0, 0.0),
    )
    assert bundle.status is VelocityClosureStatus.CLOSURE_MISMATCH

    wrong_frame = O3Transform(
        matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        transform_id="wrong-frame",
        coordinate_frame="different coordinate frame",
    )
    with pytest.raises(JointAnisotropyStateError, match="frames must match"):
        apply_o3_action(_joint(), wrong_frame)
