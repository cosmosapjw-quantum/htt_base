import numpy as np
import pytest

from common.kinematical_functionals import (
    FrameTransport,
    KinematicalState,
    KinematicalStateError,
    evaluate_kinematical_functionals,
    local_optical_jacobian,
    local_optical_response,
    transform_state_o3,
    stf2_components,
    stf2_from_components,
)
from common.relativistic_kinematics import METRIC
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
from common.orbit_nonlinearity import STF5_CARTESIAN_BASIS, stf5_to_matrix
from common.tensor_functionals_v1 import FunctionalDomainStatus
from common.transfer_registry import TransferSource


BASIS = "TETRAD_A"


def make_state(**overrides):
    values = dict(
        sample_id="sample-001",
        frame_id="matter-frame",
        congruence_id="matter-congruence",
        epoch_window_id="z=0.01",
        basis_id=BASIS,
        source_identity="manufactured-test-state",
        sigma=np.array([[0.2, 0.03, 0.0],
                        [0.03, -0.1, 0.02],
                        [0.0, 0.02, -0.1]]),
        omega=np.array([0.01, -0.02, 0.03]),
        acceleration=np.array([0.4, -0.1, 0.2]),
        beta_RM=np.array([0.02, -0.01, 0.005]),
        beta_MO=np.array([-0.001, 0.003, 0.002]),
        beta_RM_basis_id=BASIS,
        beta_MO_basis_id=BASIS,
        beta_RM_frame_id="matter-frame",
        beta_MO_frame_id="matter-frame",
        H=0.07,
    )
    values.update(overrides)
    return KinematicalState(**values)


def function_map(state, **kwargs):
    return {item.functional_id: item for item in evaluate_kinematical_functionals(state, **kwargs)}


def test_direct_and_mixed_kinematical_x_functionals():
    state = make_state()
    values = function_map(state)

    assert values["SIGMA_RAW"].status == "AVAILABLE"
    assert values["SIGMA_RAW"].dimension == 5
    assert values["OMEGA_RAW"].representation == "VECTOR_AXIAL"
    assert values["ACCEL_RAW"].units == "m s^-2"
    assert values["BETA_RM"].components.shape == (3,)
    assert values["BETA_RO_FIRST_ORDER_VIEW"].status == "CONDITIONAL_FIRST_ORDER"

    beta = state.beta_RM
    sigma = state.sigma
    assert values["SIGMA_CONTRACT_BETA"].components[0] == pytest.approx(beta @ sigma @ beta / state.H)
    assert values["BETA_DOT_OMEGA"].components[0] == pytest.approx(beta @ state.omega / state.H)
    np.testing.assert_allclose(
        values["SIGMA_BETA_VECTOR"].components,
        sigma @ beta / state.H,
    )
    np.testing.assert_allclose(
        values["BETA_CROSS_OMEGA"].components,
        np.cross(beta, state.omega) / state.H,
    )
    assert values["BETA_DOT_OMEGA"].parity == "ODD"
    assert values["BETA_CROSS_OMEGA"].parity == "EVEN"
    assert values["OMEGA_VECTOR_NORM2_H"].components[0] == pytest.approx(
        state.omega @ state.omega / state.H**2
    )


def test_missing_components_and_zero_h_are_not_zero_filled():
    missing = make_state(sigma=None, acceleration=None, H=0.0)
    values = function_map(missing)
    assert values["SIGMA_RAW"].status == "UNAVAILABLE"
    assert values["SIGMA_RAW"].dimension == 5
    assert values["SIGMA_RAW"].components is None
    assert values["ACCEL_RAW"].status == "UNAVAILABLE"
    assert values["SIGMA_H"].status == "UNAVAILABLE"

    zero_h = make_state(H=0.0)
    zero_values = function_map(zero_h)
    assert zero_values["SIGMA_H"].status == "UNDEFINED"
    assert zero_values["OMEGA_H"].status == "UNDEFINED"
    assert zero_values["ACCEL_C_H"].status == "UNDEFINED"
    assert zero_values["SIGMA_H"].components is None


def test_mixed_functional_requires_explicit_frame_transport():
    state = make_state(beta_RM_basis_id="RADIATION_TETRAD")
    missing_transport = function_map(state)
    assert missing_transport["BETA_RM"].status == "AVAILABLE"
    assert missing_transport["SIGMA_CONTRACT_BETA"].status == "FRAME_TRANSPORT_REQUIRED"
    assert "frame transport" in missing_transport["SIGMA_CONTRACT_BETA"].reason

    matrix = np.array([[0.0, -1.0, 0.0],
                       [1.0, 0.0, 0.0],
                       [0.0, 0.0, 1.0]])
    transport = FrameTransport(
        source_basis_id="RADIATION_TETRAD",
        target_basis_id=BASIS,
        matrix=matrix,
        transport_id="R_to_A_rotation",
    )
    values = function_map(state, frame_transports={("RADIATION_TETRAD", BASIS): transport})
    beta = matrix @ state.beta_RM
    assert values["SIGMA_CONTRACT_BETA"].status == "AVAILABLE"
    assert values["SIGMA_CONTRACT_BETA"].components[0] == pytest.approx(
        beta @ state.sigma @ beta / state.H
    )


def test_o3_action_preserves_polar_axial_and_mixed_parity():
    state = make_state()
    reflection = np.diag([-1.0, 1.0, 1.0])
    transformed = transform_state_o3(state, reflection, new_basis_id="REFLECTED_TETRAD")
    values = function_map(state)
    reflected_values = function_map(transformed)

    assert reflected_values["BETA_DOT_OMEGA"].components[0] == pytest.approx(
        -values["BETA_DOT_OMEGA"].components[0]
    )
    assert reflected_values["SIGMA_CONTRACT_BETA"].components[0] == pytest.approx(
        values["SIGMA_CONTRACT_BETA"].components[0]
    )
    np.testing.assert_allclose(
        reflected_values["BETA_CROSS_OMEGA"].components,
        reflection @ values["BETA_CROSS_OMEGA"].components,
    )
    np.testing.assert_allclose(
        transformed.omega,
        np.linalg.det(reflection) * reflection @ state.omega,
    )


def test_local_optical_acceleration_is_radial_not_leading_transverse():
    state = make_state(
        sigma=np.zeros((3, 3)),
        omega=np.zeros(3),
        acceleration=np.array([2.0, 0.0, 0.0]),
        H=0.5,
    )
    directions = np.array([[1.0, 0.0, 0.0],
                           [-1.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0]])
    prediction = local_optical_response(
        state, directions, direction_basis_id=BASIS, triad_rotation=np.zeros(3),
        triad_rotation_basis_id=BASIS, clock_scale=1.0, speed_of_light=10.0
    )
    np.testing.assert_allclose(prediction.radial_rate_s_inv, [0.3, 0.7, 0.5])
    np.testing.assert_allclose(prediction.fermi_walker_drift_s_inv, np.zeros((3, 3)))
    np.testing.assert_allclose(prediction.catalogue_drift_s_inv, np.zeros((3, 3)))


def test_vorticity_and_catalogue_rotation_are_the_same_leading_b1_column():
    state = make_state(sigma=np.zeros((3, 3)), acceleration=np.zeros(3), H=0.5)
    n = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    omega = np.array([0.0, 0.0, 0.1])
    pred = local_optical_response(
        KinematicalState(
            sample_id=state.sample_id, frame_id=state.frame_id,
            congruence_id=state.congruence_id, epoch_window_id=state.epoch_window_id,
            basis_id=state.basis_id, source_identity=state.source_identity,
            sigma=np.zeros((3, 3)), omega=omega, acceleration=np.zeros(3), H=0.5,
        ),
        n, direction_basis_id=BASIS,
        triad_rotation=np.array([0.0, 0.0, 0.2]),
        triad_rotation_basis_id=BASIS, speed_of_light=10.0
    )
    expected = np.cross(n, np.array([0.0, 0.0, 0.3]))
    np.testing.assert_allclose(pred.catalogue_drift_s_inv, expected)
    unresolved = local_optical_response(
        state, n, direction_basis_id=BASIS,
        triad_rotation=None, triad_rotation_basis_id=None, speed_of_light=10.0
    )
    assert unresolved.fermi_walker_drift_s_inv is not None
    assert unresolved.catalogue_drift_s_inv is None
    assert unresolved.transverse_status == "TRIAD_ROTATION_UNAVAILABLE_CATALOGUE_B1_UNRESOLVED"


def _tangent_basis(directions):
    result = []
    axes = np.eye(3)
    for n in directions:
        reference = axes[np.argmin(np.abs(n))]
        first = np.cross(n, reference)
        first = first / np.linalg.norm(first)
        second = np.cross(n, first)
        result.append([first, second])
    return np.asarray(result)


def test_local_optical_joint_jacobian_identifies_12_kinematical_components_but_not_triad_spin():
    raw = [
        (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        (3, 4, 0), (-3, -4, 0), (3, 0, 4), (-3, 0, -4), (0, 3, 4), (0, -3, -4),
    ]
    directions = np.asarray([np.asarray(v, dtype=float) / np.linalg.norm(v) for v in raw])
    tangents = _tangent_basis(directions)

    physical = local_optical_jacobian(
        directions, tangents, frame_id="observer-frame",
        congruence_id="test-congruence", basis_id=BASIS,
        include_triad_rotation=False
    )
    with_spin = local_optical_jacobian(
        directions, tangents, frame_id="observer-frame",
        congruence_id="test-congruence", basis_id=BASIS,
        include_triad_rotation=True
    )
    assert physical.matrix.shape == (36, 12)
    assert np.linalg.matrix_rank(physical.matrix) == 12
    assert with_spin.matrix.shape == (36, 15)
    assert np.linalg.matrix_rank(with_spin.matrix) == 12
    np.testing.assert_allclose(with_spin.matrix[:, 9:12], with_spin.matrix[:, 12:15])
    assert with_spin.parameter_names[6:9] == (
        "A_over_c_0", "A_over_c_1", "A_over_c_2"
    )


def test_velocity_jet_adapter_extracts_raw_congruence_kinematics():
    derivative = np.zeros((4, 4))
    derivative[0, 1:] = [0.05, -0.02, 0.01]
    derivative[1:, 1:] = np.array([
        [0.10, 0.03, 0.00],
        [-0.01, 0.20, 0.02],
        [0.00, -0.02, 0.30],
    ])
    triad = np.array([[0.0, 1.0, 0.0, 0.0],
                      [0.0, 0.0, 1.0, 0.0],
                      [0.0, 0.0, 0.0, 1.0]])
    state = KinematicalState.from_velocity_jet(
        u=[1.0, 0.0, 0.0, 0.0],
        derivative_covariant=derivative,
        spatial_triad=triad,
        speed_of_light=2.0,
        sample_id="jet-001",
        frame_id="observer-tetrad",
        congruence_id="test-congruence",
        epoch_window_id="local",
        basis_id=BASIS,
        source_identity="manufactured-velocity-jet",
    )
    assert state.H == pytest.approx(2.0 * 0.6 / 3.0)
    assert state.sigma.shape == (3, 3)
    assert state.omega.shape == (3,)
    assert state.acceleration.shape == (3,)
    assert state.acceleration[0] == pytest.approx(2.0**2 * 0.05)


def test_spatial_rotation_does_not_substitute_for_lorentz_frame_bridge():
    state = make_state(
        beta_RM_basis_id="RADIATION_TETRAD_AXES",
        beta_RM_frame_id="radiation-coordinate-frame",
    )
    rotation = np.array([[0.0, -1.0, 0.0],
                         [1.0, 0.0, 0.0],
                         [0.0, 0.0, 1.0]])
    transport = FrameTransport(
        source_basis_id="RADIATION_TETRAD_AXES",
        target_basis_id=BASIS,
        matrix=rotation,
        transport_id="spatial_axes_only",
    )
    values = function_map(
        state,
        frame_transports={("RADIATION_TETRAD_AXES", BASIS): transport},
    )
    assert values["BETA_RM"].status == "AVAILABLE"
    assert values["SIGMA_CONTRACT_BETA"].status == "RELATIVISTIC_FRAME_BRIDGE_REQUIRED"
    assert values["BETA_RO_FIRST_ORDER_VIEW"].status == "RELATIVISTIC_FRAME_BRIDGE_REQUIRED"



def make_canonical_joint_state(*, acceleration_available=True):
    frame = "observer-coordinate-frame"
    congruence = "matter-congruence"
    epoch = "z-window-0.01"
    averaging = "pointwise-local"
    basis = STF5_CARTESIAN_BASIS
    units = UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
    perturbative_order = "first_order_small_velocity"

    acceleration_hat = (
        (0.001, -0.002, 0.003)
        if acceleration_available
        else missing_component(
            "acceleration_polar3",
            "manufactured missing-acceleration case",
            required_for=("local radial optical response",),
        )
    )
    kinematics = CongruenceKinematics(
        sigma_stf5=(0.12, -0.07, 0.03, -0.02, 0.01),
        omega_axial3=(0.04, -0.02, 0.01),
        acceleration_polar3=acceleration_hat,
        frame=frame,
        congruence_id=congruence,
        epoch_window=epoch,
        averaging_scale=averaging,
        basis=basis,
        units_convention=units,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=perturbative_order,
        acceleration_normalization=(
            AccelerationNormalization.A_OVER_C_THETA
            if acceleration_available else None
        ),
    )
    beta_rm = (0.020, -0.010, 0.005)
    beta_mo = (-0.003, 0.002, 0.001)
    beta_ro = tuple(beta_rm[i] + beta_mo[i] for i in range(3))
    velocities = build_velocity_frame_bundle(
        beta_RO=beta_ro,
        beta_RM=beta_rm,
        beta_MO=beta_mo,
        coordinate_frame=frame,
        radiation_frame_id="radiation-rest-frame",
        matter_frame_id="matter-rest-frame",
        observer_frame_id="observer-rest-frame",
        basis=basis,
        epoch_window=epoch,
        averaging_scale=averaging,
        first_order_beta_ceiling=0.1,
        source_decomposition_id="manufactured-velocity-decomposition",
    )
    geometry = GeometryState(
        delta_omega_k=0.015,
        frame=frame,
        congruence_id=congruence,
        epoch_window=epoch,
        averaging_scale=averaging,
        basis=basis,
        units_convention=units,
        perturbative_order=perturbative_order,
    )
    return JointAnisotropyState(
        congruence_kinematics=kinematics,
        velocity_frames=velocities,
        geometry_state=geometry,
        frame=frame,
        congruence=congruence,
        epoch_window=epoch,
        averaging_scale=averaging,
        basis=basis,
        units_convention=units,
        perturbative_order=perturbative_order,
        beta_semantic_role=BetaSemanticRole.DIRECT_STATE,
        transfer_source=TransferSource.NONE,
        transfer_spec=None,
        source_kind=JointStateSourceKind.DIRECT,
        source_identity="manufactured-r39-joint-state",
    )


def test_canonical_joint_state_is_the_only_x_source_and_units_round_trip():
    joint = make_canonical_joint_state()
    theta = 0.21
    c = 299_792_458.0
    view = KinematicalState.from_joint_anisotropy_state(
        joint, expansion_scalar=theta, speed_of_light=c
    )

    assert view.canonical_state_id == joint.content_id
    np.testing.assert_allclose(
        view.sigma,
        theta * stf5_to_matrix(joint.congruence_kinematics.sigma_stf5),
    )
    np.testing.assert_allclose(
        view.omega,
        theta * np.asarray(joint.congruence_kinematics.omega_axial3),
    )
    np.testing.assert_allclose(
        view.acceleration,
        c * theta * np.asarray(joint.congruence_kinematics.acceleration_polar3),
    )
    assert view.beta_RM_frame_id == joint.velocity_frames.coordinate_frame
    assert view.beta_MO_frame_id == joint.velocity_frames.coordinate_frame
    assert view.velocity_frame_ids == (
        joint.velocity_frames.radiation_frame_id,
        joint.velocity_frames.matter_frame_id,
        joint.velocity_frames.observer_frame_id,
    )

    from common.kinematical_functionals import build_kinematical_x_bundle
    bundle = build_kinematical_x_bundle(
        joint, expansion_scalar=theta, speed_of_light=c
    )
    assert bundle.canonical_state_id == joint.content_id
    assert bundle.scope == "KINEMATICAL_FUNCTIONAL_SUBBUNDLE_ONLY"
    assert all(v.state_id == joint.content_id for v in bundle.physical_functionals)
    assert all(v.source_state_id == joint.content_id for v in bundle.canonical_functionals)

    physical = {v.functional_id: v for v in bundle.physical_functionals}
    assert physical["SIGMA_RAW"].units == "s^-1"
    assert physical["ACCEL_RAW"].units == "m s^-2"
    np.testing.assert_allclose(
        physical["ACCEL_RAW"].components,
        c * theta * np.asarray(joint.congruence_kinematics.acceleration_polar3),
    )
    np.testing.assert_allclose(
        physical["SIGMA_H"].components,
        3.0 * np.asarray(joint.congruence_kinematics.sigma_stf5),
    )
    np.testing.assert_allclose(
        stf2_from_components(stf2_components(view.sigma)),
        view.sigma,
    )
    assert physical["BETA_RO_CANONICAL_VIEW"].status == "AVAILABLE"
    np.testing.assert_allclose(
        physical["BETA_RO_CANONICAL_VIEW"].components,
        joint.velocity_frames.beta_RO,
    )
    np.testing.assert_allclose(
        physical["BETA_RO_FIRST_ORDER_VIEW"].components,
        np.asarray(joint.velocity_frames.beta_RM)
        + np.asarray(joint.velocity_frames.beta_MO),
    )
    np.testing.assert_allclose(
        physical["BETA_CLOSURE_RESIDUAL"].components,
        np.zeros(3),
    )

    canonical = {v.spec.functional_id: v for v in bundle.canonical_functionals}
    np.testing.assert_allclose(
        canonical["SIGMA_THETA_STF5"].value,
        joint.congruence_kinematics.sigma_stf5,
    )
    np.testing.assert_allclose(
        canonical["BETA_RM_SIGMA_BETA_RM_THETA"].value,
        np.asarray(joint.velocity_frames.beta_RM)
        @ stf5_to_matrix(joint.congruence_kinematics.sigma_stf5)
        @ np.asarray(joint.velocity_frames.beta_RM),
    )
    assert canonical["DELTA_OMEGA_K"].source_state_id == joint.content_id


def test_canonical_missing_acceleration_remains_missing_in_both_functional_layers():
    joint = make_canonical_joint_state(acceleration_available=False)
    from common.kinematical_functionals import build_kinematical_x_bundle
    bundle = build_kinematical_x_bundle(joint, expansion_scalar=0.21)
    physical = {v.functional_id: v for v in bundle.physical_functionals}
    canonical = {v.spec.functional_id: v for v in bundle.canonical_functionals}

    assert physical["ACCEL_RAW"].status == "UNAVAILABLE"
    assert physical["ACCEL_C_H"].status == "UNAVAILABLE"
    assert physical["BETA_DOT_ACCEL"].status == "UNAVAILABLE"
    assert canonical["ACCELERATION_C_THETA_POLAR3"].domain.status is FunctionalDomainStatus.MISSING_COMPONENT
    assert canonical["ACCELERATION_C_THETA_POLAR3"].value is None
