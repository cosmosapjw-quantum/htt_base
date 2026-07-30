"""PR-263 stratified parity-typed orbit catalogue contracts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import yaml

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
from common.orbit_catalogue_v2 import (
    OrbitCatalogueV2Spec,
    PR257_POLYNOMIAL_NAMES,
    orbit_catalogue_v2,
)
from common.orbit_catalogue_v3 import (
    CatalogueProofStatus,
    ChartCoordinateStatus,
    ChartOverlapStatus,
    CyclicChartStatus,
    InvariantAlgebraicForm,
    InvariantAvailability,
    JointStabilizerStatus,
    LegacyBetaChannel,
    LegacyV2AdapterStatus,
    ORBIT_V3_CLAIM_CEILING,
    OrbitActionGroup,
    OrbitCatalogueV3Error,
    OrbitCatalogueV3Report,
    OrbitCatalogueV3Spec,
    OrbitScalarParity,
    OrbitVectorChannel,
    ShearOrbitStratum,
    ShearStabilizer,
    adapt_joint_state_to_orbit_catalogue_v2,
    apply_orbit_group_action,
    build_orbit_catalogue_v3_spec,
    orbit_catalogue_v3,
    revalidate_orbit_catalogue_v3,
)
from common.orbit_nonlinearity import (
    DEPARTURE_O3_PARITY,
    DEPARTURE_O3_UNITS,
    O3Transform,
    STF5_CARTESIAN_BASIS,
)
from common.statistical_foundations import DepartureState
from common.transfer_registry import TransferSource


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/research_program/vector_tensor/pr263_spec.yaml"
BACKLOG_PATH = ROOT / "docs/codex_handoff/pr_backlog.yaml"
FRAME = "PR263 registered Cartesian tetrad"
CONGRUENCE = "PR263 registered matter congruence"
EPOCH = "PR263 synthetic epoch"
SCALE = "PR263 synthetic averaging scale"
ORDER = "PR263 diagnostic polynomial order"


def _joint(
    *,
    sigma: tuple[float, ...] = (1.0, 2.0, 0.0, 0.0, 0.0),
    omega: tuple[float, ...] = (1.0, 2.0, 3.0),
    acceleration_missing: bool = False,
    beta_rm: tuple[float, ...] | None = (0.001, 0.002, 0.003),
    beta_mo: tuple[float, ...] | None = (-0.0002, 0.0004, -0.0001),
) -> JointAnisotropyState:
    acceleration = (
        missing_component(
            "acceleration_polar3",
            "acceleration unavailable in PR-263 fixture",
            required_for=("Gram-Krylov signature",),
        )
        if acceleration_missing
        else (0.01, 0.02, 0.03)
    )
    kinematics = CongruenceKinematics(
        sigma_stf5=sigma,
        omega_axial3=omega,
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
    missing_rm = missing_component(
        "beta_RM",
        "beta_RM unavailable in PR-263 fixture",
        required_for=("explicit beta_RM chart",),
    )
    missing_mo = missing_component(
        "beta_MO",
        "beta_MO unavailable in PR-263 fixture",
        required_for=("explicit beta_MO chart",),
    )
    rm = missing_rm if beta_rm is None else beta_rm
    mo = missing_mo if beta_mo is None else beta_mo
    if beta_rm is not None and beta_mo is not None:
        ro: object = tuple(
            beta_rm[index] + beta_mo[index] for index in range(3)
        )
    else:
        ro = missing_component(
            "beta_RO",
            "beta_RO is not derived from missing velocity channels",
            required_for=("explicit beta_RO compatibility adapter",),
        )
    velocity = build_velocity_frame_bundle(
        beta_RO=ro,
        beta_RM=rm,
        beta_MO=mo,
        coordinate_frame=FRAME,
        radiation_frame_id="PR263 radiation frame",
        matter_frame_id="PR263 matter frame",
        observer_frame_id="PR263 observer frame",
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
        source_identity=(
            f"PR263-{sigma!r}-{omega!r}-{acceleration_missing}-"
            f"{beta_rm!r}-{beta_mo!r}"
        ),
    )


def _spec(
    group: OrbitActionGroup = OrbitActionGroup.O3,
):
    return build_orbit_catalogue_v3_spec(
        catalogue_id=f"PR263-{group.value}-CATALOGUE",
        action_group=group,
    )


def _v2_catalogue() -> OrbitCatalogueV2Spec:
    return OrbitCatalogueV2Spec(
        catalog_id="PR263-V2-COMPATIBILITY",
        polynomial_names=PR257_POLYNOMIAL_NAMES,
        multiplicity_method="MAX_ABS_Z_FIXED_CATALOGUE_V1",
        alignment_null_id="PR263-V2-NULL",
        preregistration_id="PR263-V2-PREREGISTRATION",
        cas_contract_id="PR263-V2-CAS-REFERENCE",
    )


def _transform(
    matrix: tuple[tuple[float, float, float], ...],
    transform_id: str,
) -> O3Transform:
    return O3Transform(
        matrix=matrix,
        transform_id=transform_id,
        coordinate_frame=FRAME,
    )


def _assert_joint_numeric_equal(
    left: JointAnisotropyState,
    right: JointAnisotropyState,
) -> None:
    assert np.allclose(
        left.congruence_kinematics.sigma_stf5,
        right.congruence_kinematics.sigma_stf5,
    )
    assert np.allclose(
        left.congruence_kinematics.omega_axial3,
        right.congruence_kinematics.omega_axial3,
    )
    assert np.allclose(
        left.congruence_kinematics.acceleration_polar3,
        right.congruence_kinematics.acceleration_polar3,
    )
    assert np.allclose(left.velocity_frames.beta_RM, right.velocity_frames.beta_RM)
    assert np.allclose(left.velocity_frames.beta_MO, right.velocity_frames.beta_MO)


def test_pr263_spec_and_card_bind_local_unproven_scope() -> None:
    document = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    backlog = yaml.safe_load(BACKLOG_PATH.read_text(encoding="utf-8"))
    card = next(row for row in backlog["prs"] if row["id"] == "PR-263")

    assert document["dependencies"] == ["PR-261", "PR-257"]
    assert document["owner"] == card["owner"] == "OBSSTAT"
    assert document["contract_owner"] == "COMMON"
    assert document["contributors"] == card["contributors"] == ["COMMON"]
    assert document["atlas_boundary"]["generic_orbit_separation_status"] == (
        "UNPROVEN"
    )
    assert document["atlas_boundary"]["global_chart_completeness_status"] == (
        "UNPROVEN"
    )
    assert document["legacy"]["automatic_scalar_or_beta_promotion"] == (
        "forbidden"
    )
    assert card["depends"] == ["PR-261", "PR-257"]
    assert card["claim_tier_ceiling"] == ORBIT_V3_CLAIM_CEILING


def test_group_action_composes_and_so3_refuses_improper_action() -> None:
    state = _joint()
    rz = _transform(
        ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "PR263-RZ90",
    )
    rx = _transform(
        ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
        "PR263-RX90",
    )
    composed = _transform(
        tuple(
            tuple(float(value) for value in row)
            for row in np.asarray(rx.matrix) @ np.asarray(rz.matrix)
        ),
        "PR263-RX90-RZ90",
    )
    sequential = apply_orbit_group_action(
        apply_orbit_group_action(state, rz, group=OrbitActionGroup.SO3),
        rx,
        group=OrbitActionGroup.SO3,
    )
    direct = apply_orbit_group_action(
        state,
        composed,
        group=OrbitActionGroup.SO3,
    )
    _assert_joint_numeric_equal(sequential, direct)

    reflection = _transform(
        ((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
        "PR263-REFLECTION",
    )
    with pytest.raises(OrbitCatalogueV3Error, match="SO3 action refuses"):
        apply_orbit_group_action(
            state,
            reflection,
            group=OrbitActionGroup.SO3,
        )
    reflected = apply_orbit_group_action(
        state,
        reflection,
        group=OrbitActionGroup.O3,
    )
    assert np.allclose(
        reflected.congruence_kinematics.omega_axial3,
        state.congruence_kinematics.omega_axial3,
    )
    assert np.allclose(
        reflected.velocity_frames.beta_RM,
        -np.asarray(state.velocity_frames.beta_RM),
    )


def test_all_signature_entries_obey_o3_scalar_pseudoscalar_typing() -> None:
    state = _joint()
    reflection = _transform(
        ((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
        "PR263-REFLECTION-PARITY",
    )
    original = orbit_catalogue_v3(state, _spec())
    reflected = orbit_catalogue_v3(
        apply_orbit_group_action(
            state,
            reflection,
            group=OrbitActionGroup.O3,
        ),
        _spec(),
    )
    for name, item in original.invariants_by_name.items():
        counterpart = reflected.invariants_by_name[name]
        assert counterpart.availability is item.availability
        if item.availability is not InvariantAvailability.AVAILABLE:
            continue
        expected = (
            item.value
            if item.parity is OrbitScalarParity.O3_SCALAR
            else -item.value
        )
        assert counterpart.value == pytest.approx(
            expected,
            rel=1.0e-11,
            abs=1.0e-11,
        )
    assert (
        original.invariants_by_name["K:omega_axial3"].parity
        is OrbitScalarParity.O3_SCALAR
    )
    assert (
        original.invariants_by_name["K:beta_RM"].parity
        is OrbitScalarParity.O3_PSEUDOSCALAR
    )


def test_random_o3_actions_preserve_the_registered_parity_law() -> None:
    state = _joint()
    reference = orbit_catalogue_v3(state, _spec())
    reference_charts = {chart.channel: chart for chart in reference.charts}
    for seed in range(12):
        rng = np.random.default_rng(seed)
        matrix, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        desired_determinant = -1 if seed % 2 else 1
        if np.linalg.det(matrix) * desired_determinant < 0.0:
            matrix[:, 0] *= -1.0
        transform = _transform(
            tuple(
                tuple(float(value) for value in row)
                for row in matrix
            ),
            f"PR263-RANDOM-O3-{seed}",
        )
        transformed = orbit_catalogue_v3(
            apply_orbit_group_action(
                state,
                transform,
                group=OrbitActionGroup.O3,
            ),
            _spec(),
        )
        for item in reference.invariants:
            counterpart = transformed.invariants_by_name[item.name]
            if item.availability is not InvariantAvailability.AVAILABLE:
                continue
            parity_sign = (
                1.0
                if item.parity is OrbitScalarParity.O3_SCALAR
                else float(transform.determinant)
            )
            assert counterpart.value == pytest.approx(
                parity_sign * item.value,
                rel=1.0e-10,
                abs=1.0e-10,
            )
        for chart in transformed.charts:
            reference_chart = reference_charts[chart.channel]
            assert chart.singular_values == pytest.approx(
                reference_chart.singular_values,
                rel=1.0e-10,
                abs=1.0e-10,
            )
            determinant_sign = (
                1.0
                if chart.vector_parity.value == "AXIAL"
                else float(transform.determinant)
            )
            assert chart.determinant == pytest.approx(
                determinant_sign * reference_chart.determinant,
                rel=1.0e-10,
                abs=1.0e-10,
            )


@pytest.mark.parametrize(
    ("sigma", "status", "stabilizer"),
    (
        (
            (0.0, 0.0, 0.0, 0.0, 0.0),
            ShearOrbitStratum.ZERO_SHEAR,
            ShearStabilizer.O3_FULL,
        ),
        (
            (1.0, 1.0, 0.0, 0.0, 0.0),
            ShearOrbitStratum.REPEATED_EIGENVALUE,
            ShearStabilizer.O3_AXISYMMETRIC_O2_X_Z2,
        ),
        (
            (1.0, 2.0, 0.0, 0.0, 0.0),
            ShearOrbitStratum.SIMPLE_SPECTRUM,
            ShearStabilizer.O3_SIMPLE_SIGN_EIGHT,
        ),
        (
            (1.0, 1.0 + 1.0e-13, 0.0, 0.0, 0.0),
            ShearOrbitStratum.NUMERICALLY_UNRESOLVED,
            ShearStabilizer.NUMERICALLY_UNRESOLVED,
        ),
    ),
)
def test_shear_strata_and_stabilizer_boundaries(
    sigma: tuple[float, ...],
    status: ShearOrbitStratum,
    stabilizer: ShearStabilizer,
) -> None:
    report = orbit_catalogue_v3(_joint(sigma=sigma), _spec())
    assert report.stratum.status is status
    assert report.stabilizer.shear_stabilizer is stabilizer
    assert not report.stabilizer.globally_certified
    assert (
        report.spec.generic_orbit_separation_status
        is CatalogueProofStatus.UNPROVEN
    )
    assert (
        report.spec.global_chart_completeness_status
        is CatalogueProofStatus.UNPROVEN
    )
    if status is ShearOrbitStratum.ZERO_SHEAR:
        assert (
            report.invariants_by_name["J_sigma"].availability
            is InvariantAvailability.MISSING_COMPONENT
        )


def test_stabilizer_vocabulary_tracks_o3_versus_so3_action_group() -> None:
    expected = {
        (OrbitActionGroup.SO3, (0.0, 0.0, 0.0, 0.0, 0.0)): (
            ShearStabilizer.SO3_FULL
        ),
        (OrbitActionGroup.O3, (0.0, 0.0, 0.0, 0.0, 0.0)): (
            ShearStabilizer.O3_FULL
        ),
        (OrbitActionGroup.SO3, (1.0, 1.0, 0.0, 0.0, 0.0)): (
            ShearStabilizer.SO3_AXISYMMETRIC_O2
        ),
        (OrbitActionGroup.O3, (1.0, 1.0, 0.0, 0.0, 0.0)): (
            ShearStabilizer.O3_AXISYMMETRIC_O2_X_Z2
        ),
        (OrbitActionGroup.SO3, (1.0, 2.0, 0.0, 0.0, 0.0)): (
            ShearStabilizer.SO3_SIMPLE_KLEIN_FOUR
        ),
        (OrbitActionGroup.O3, (1.0, 2.0, 0.0, 0.0, 0.0)): (
            ShearStabilizer.O3_SIMPLE_SIGN_EIGHT
        ),
    }
    for (group, sigma), stabilizer in expected.items():
        report = orbit_catalogue_v3(
            _joint(sigma=sigma),
            _spec(group),
        )
        assert report.stabilizer.shear_stabilizer is stabilizer


def test_cyclic_charts_are_local_conditioned_candidates_with_overlaps() -> None:
    report = orbit_catalogue_v3(_joint(), _spec())
    candidates = tuple(
        chart
        for chart in report.charts
        if chart.status is CyclicChartStatus.NUMERICALLY_CYCLIC_CANDIDATE
    )
    assert candidates
    assert all(
        chart.coordinate_status is ChartCoordinateStatus.COMPLETE
        for chart in report.charts
    )
    assert all(len(chart.coordinates) == 14 for chart in report.charts)
    assert all(chart.local_only for chart in report.charts)
    assert (
        report.stabilizer.joint_status
        is JointStabilizerStatus.NUMERICALLY_TRIVIAL_CANDIDATE
    )
    assert report.stabilizer.selected_chart is not None
    assert any(
        overlap.status is ChartOverlapStatus.DEFINED_LOCAL_OVERLAP
        for overlap in report.chart_overlaps
    )
    assert all(overlap.local_only for overlap in report.chart_overlaps)

    zero = orbit_catalogue_v3(
        _joint(
            sigma=(0.0, 0.0, 0.0, 0.0, 0.0),
            omega=(0.0, 0.0, 0.0),
            beta_rm=(0.0, 0.0, 0.0),
            beta_mo=(0.0, 0.0, 0.0),
        ),
        _spec(),
    )
    assert all(
        chart.status is CyclicChartStatus.NONCYCLIC
        for chart in zero.charts
        if chart.channel is not OrbitVectorChannel.ACCELERATION
    )
    assert all(
        chart.condition_number is None
        for chart in zero.charts
        if chart.status is CyclicChartStatus.NONCYCLIC
    )
    assert (
        zero.stabilizer.joint_status
        is JointStabilizerStatus.RESIDUAL_STABILIZER_UNRESOLVED
    )


def test_missing_channels_are_typed_in_charts_and_signature() -> None:
    state = _joint(
        acceleration_missing=True,
        beta_rm=None,
    )
    report = orbit_catalogue_v3(state, _spec())
    assert set(report.missing_components) == {
        "acceleration_polar3",
        "beta_RM",
    }
    charts = {chart.channel: chart for chart in report.charts}
    assert (
        charts[OrbitVectorChannel.ACCELERATION].status
        is CyclicChartStatus.MISSING_COMPONENT
    )
    assert (
        charts[OrbitVectorChannel.BETA_RM].status
        is CyclicChartStatus.MISSING_COMPONENT
    )
    assert (
        report.invariants_by_name["K:beta_RM"].availability
        is InvariantAvailability.MISSING_COMPONENT
    )
    assert all(
        chart.coordinate_status is ChartCoordinateStatus.PARTIAL
        for chart in report.charts
    )
    assert report.stabilizer.selected_chart is None
    assert (
        report.stabilizer.joint_status
        is JointStabilizerStatus.RESIDUAL_STABILIZER_UNRESOLVED
    )
    assert all(
        item.value is None
        for item in report.invariants
        if item.availability is InvariantAvailability.MISSING_COMPONENT
    )


def test_signature_is_registered_closure_and_j_sigma_is_degree_zero() -> None:
    report = orbit_catalogue_v3(_joint(), _spec())
    assert len(report.invariants) == 42
    assert len({item.name for item in report.invariants}) == 42
    j_sigma = report.invariants_by_name["J_sigma"]
    assert j_sigma.homogeneous_degree == 0
    assert (
        j_sigma.algebraic_form
        is InvariantAlgebraicForm.NORMALIZED_RATIONAL
    )
    assert -1.0 <= j_sigma.value <= 1.0
    assert all(
        item.algebraic_form is InvariantAlgebraicForm.POLYNOMIAL
        for item in report.invariants
        if item.name != "J_sigma"
    )


def test_v2_adapter_requires_explicit_channel_and_replays_exactly() -> None:
    state = _joint()
    catalogue = _v2_catalogue()
    adapter = adapt_joint_state_to_orbit_catalogue_v2(
        state,
        beta_channel=LegacyBetaChannel.BETA_RM,
        catalogue=catalogue,
    )
    assert adapter.status is LegacyV2AdapterStatus.ADAPTED
    assert not adapter.automatic_beta_selection
    assert adapter.v2_report is not None
    direct = orbit_catalogue_v2(
        DepartureState(
            sigma_ab=state.congruence_kinematics.sigma_stf5,
            omega_a=state.congruence_kinematics.omega_axial3,
            beta_a=state.velocity_frames.beta_RM,
            delta_omega_k=state.geometry_state.delta_omega_k,
            frame=FRAME,
            congruence=CONGRUENCE,
            epoch_window=EPOCH,
            averaging_scale=SCALE,
            basis=STF5_CARTESIAN_BASIS,
            units=DEPARTURE_O3_UNITS,
            parity=DEPARTURE_O3_PARITY,
            perturbative_order=ORDER,
        ),
        catalogue,
    )
    assert adapter.v2_report.as_payload() == direct.as_payload()

    missing = adapt_joint_state_to_orbit_catalogue_v2(
        _joint(beta_rm=None),
        beta_channel=LegacyBetaChannel.BETA_RM,
        catalogue=catalogue,
    )
    assert missing.status is LegacyV2AdapterStatus.MISSING_COMPONENT
    assert missing.v2_report is None
    assert missing.missing_components == ("beta_RM",)


def test_k_omega_closes_v2_nongeneric_witness_without_promotion() -> None:
    catalogue = _v2_catalogue()
    positive_state = _joint(
        omega=(1.0, 2.0, 3.0),
        beta_rm=(0.0, 0.0, 0.0),
        beta_mo=(0.0, 0.0, 0.0),
    )
    negative_state = _joint(
        omega=(-1.0, -2.0, -3.0),
        beta_rm=(0.0, 0.0, 0.0),
        beta_mo=(0.0, 0.0, 0.0),
    )
    positive_v2 = adapt_joint_state_to_orbit_catalogue_v2(
        positive_state,
        beta_channel=LegacyBetaChannel.BETA_RM,
        catalogue=catalogue,
    ).v2_report
    negative_v2 = adapt_joint_state_to_orbit_catalogue_v2(
        negative_state,
        beta_channel=LegacyBetaChannel.BETA_RM,
        catalogue=catalogue,
    ).v2_report
    assert positive_v2 is not None and negative_v2 is not None
    assert positive_v2.polynomial_values == negative_v2.polynomial_values

    positive_v3 = orbit_catalogue_v3(positive_state, _spec())
    negative_v3 = orbit_catalogue_v3(negative_state, _spec())
    k_positive = positive_v3.invariants_by_name["K:omega_axial3"]
    k_negative = negative_v3.invariants_by_name["K:omega_axial3"]
    assert k_positive.value == pytest.approx(-k_negative.value)
    assert abs(k_positive.value) == pytest.approx(120.0)
    assert k_positive.parity is OrbitScalarParity.O3_SCALAR
    assert (
        positive_v3.spec.generic_orbit_separation_status
        is CatalogueProofStatus.UNPROVEN
    )


def test_spec_state_and_report_mutations_fail_closed() -> None:
    spec = _spec()
    payload = spec.to_payload()
    payload["generic_orbit_separation_status"] = "PROVEN"
    with pytest.raises(OrbitCatalogueV3Error):
        type(spec).from_payload(payload)

    object.__setattr__(spec, "claim_ceiling", "family_identified")
    with pytest.raises(OrbitCatalogueV3Error, match="canonical replay"):
        orbit_catalogue_v3(_joint(), spec)

    state = _joint()
    object.__setattr__(
        state.congruence_kinematics,
        "parity_contract",
        "SIGMA_AND_OMEGA_UNTYPED",
    )
    with pytest.raises(OrbitCatalogueV3Error, match="joint state failed"):
        orbit_catalogue_v3(state, _spec())

    canonical_state = _joint()
    report = orbit_catalogue_v3(canonical_state, _spec())
    object.__setattr__(report, "claim_ceiling", "family_identified")
    with pytest.raises(OrbitCatalogueV3Error, match="does not match"):
        revalidate_orbit_catalogue_v3(report, canonical_state)

    canonical_report = orbit_catalogue_v3(canonical_state, _spec())
    with pytest.raises(OrbitCatalogueV3Error, match="coordinate_status"):
        replace(
            canonical_report.charts[0],
            coordinate_status=ChartCoordinateStatus.PARTIAL,
        )
    object.__setattr__(
        canonical_report.charts[0],
        "coordinates",
        canonical_report.charts[0].coordinates[:-1],
    )
    with pytest.raises(OrbitCatalogueV3Error, match="does not match"):
        revalidate_orbit_catalogue_v3(
            canonical_report,
            canonical_state,
        )


def test_no_nearest_family_or_global_proof_surface_exists() -> None:
    report = orbit_catalogue_v3(_joint(), _spec())
    payload = report.as_payload()
    assert payload["claim_ceiling"] == ORBIT_V3_CLAIM_CEILING
    assert payload["spec"]["generic_orbit_separation_status"] == "UNPROVEN"
    assert payload["spec"]["degree_completeness_status"] == "UNPROVEN"
    assert payload["spec"]["global_chart_completeness_status"] == "UNPROVEN"
    assert not {
        "nearest_family",
        "family_label",
        "geometry_label",
        "posterior",
        "likelihood",
        "evidence",
    }.intersection(payload)


def test_obsstat_bridge_reuses_common_contract_without_inference_surface() -> None:
    import obsstat
    import obsstat.orbit_catalogue_v3 as bridge

    assert bridge.OrbitCatalogueV3Report is OrbitCatalogueV3Report
    assert obsstat.OrbitCatalogueV3Spec is OrbitCatalogueV3Spec
    assert obsstat.evaluate_orbit_catalogue_v3 is orbit_catalogue_v3
    assert bridge.__obsstat_owned__ is True
    public = set(bridge.__all__)
    assert not any(
        token in name.lower()
        for name in public
        for token in (
            "posterior",
            "likelihood",
            "evidence",
            "nearest",
            "family",
            "classify",
        )
    )
