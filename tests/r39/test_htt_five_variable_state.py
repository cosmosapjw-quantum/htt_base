"""Unit tests for HTT 5-variable state (x, Q, Pi, F, G_F)."""
from __future__ import annotations

import numpy as np
import pytest

from common.full_observable_x_bundle import (
    FullObservableXBundle,
    build_full_observable_x_bundle,
)
from common.htt_five_variable_state import (
    AnchorBody,
    DirectionalSupportProfile,
    ExceedanceSurface,
    DepthPathGF,
    HTTFiveVariableState,
    construct_r39_five_variable_state,
)
from common.r39_identifiability import PARAM_NAMES_17
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
from common.transfer_registry import TransferSource


def make_test_joint_state() -> JointAnisotropyState:
    frame = "CMB_CONGRUENCE_FRAME"
    congruence = "CMB_REST_FRAME"
    epoch = "Z_RECOMBINATION"
    averaging = "HUBBLE_SCALE"
    basis = "TETRAD_A"
    units = UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
    perturbative_order = "LINEAR_FIRST_ORDER"

    kinematics = CongruenceKinematics(
        sigma_stf5=(0.0001, -0.00005, 0.00002, -0.00001, 0.00003),
        omega_axial3=(0.00001, -0.00002, 0.00001),
        acceleration_polar3=(0.0001, -0.00005, 0.00002),
        frame=frame,
        congruence_id=congruence,
        epoch_window=epoch,
        averaging_scale=averaging,
        basis=basis,
        units_convention=units,
        acceleration_normalization=AccelerationNormalization.A_OVER_C_THETA,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=perturbative_order,
    )
    beta_rm = (0.0002, -0.0001, 0.0001)
    beta_mo = (0.0010, -0.0004, 0.0007)
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
        source_decomposition_id="test-velocity-bundle",
    )
    geometry = GeometryState(
        delta_omega_k=0.010,
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
        source_identity="test-r39-state",
    )
from common.kinematic_response import KinematicResponseModel, KinematicFrameState


def test_construct_htt_five_variable_state():
    joint = make_test_joint_state()
    model_state = KinematicFrameState(
        beta_RO=np.array([0.0012, -0.0005, 0.0008]),
        beta_RM=np.array([0.0002, -0.0001, 0.0001]),
        beta_MO=np.array([0.0010, -0.0004, 0.0007]),
        d_int=np.zeros(3),
        stf_shear_amplitudes=np.array([1e-5, -5e-6, 2e-6, -1e-6, 3e-6]),
        e1_polar_vector=np.array([1e-4, -2e-4, 5e-5]),
        b1_axial_vector=np.array([5e-5, 1e-4, -5e-5]),
    )
    model = KinematicResponseModel(model_state)
    bundle = build_full_observable_x_bundle(joint, model, expansion_scalar=0.21)

    # Generate synthetic MCMC samples (100 samples x 17 parameters)
    np.random.seed(42)
    samples = np.random.randn(100, 17) * 1e-4
    # Set mean of beta_MO around 1e-3
    samples[:, 14:17] += np.array([0.0010, -0.0004, 0.0007])

    state = construct_r39_five_variable_state(bundle, samples, PARAM_NAMES_17)

    # 1. x bundle
    assert state.bundle_x.scope == "FULL_OBSERVABLE_X_BUNDLE"

    # 2. Anchors Q
    assert "shear_sigma" in state.anchors_Q
    # No theorem/source supports a per-component numerical bound: the Hamiltonian constraint bounds only
    # Sigma^2 - W^2 (see tests/r48 and the Lean proof receipt); hard-coded 1e-4 anchors were removed.
    for key in ("shear_sigma", "vorticity_omega"):
        a = state.anchors_Q[key]
        assert a.status == "UNAVAILABLE" and a.norm_bound is None and a.gauge_margin is None
        assert "Sigma^2 - W^2" in a.notes
    assert state.anchors_Q["acceleration_A"].status == "UNAVAILABLE"
    assert state.anchors_Q["relative_velocity_beta"].status == "UNAVAILABLE"

    # 3. Directional Support Profiles F
    assert "BETA_MO" in state.support_profiles_F
    f_prof = state.support_profiles_F["BETA_MO"]
    assert len(f_prof.evaluation_directions) == 50
    assert len(f_prof.support_values) == 50
    assert np.all(np.isfinite(f_prof.support_values))

    # 4. Exceedance Surfaces Pi
    assert "BETA_MO_NORM" in state.exceedance_surfaces_Pi
    pi_surf = state.exceedance_surfaces_Pi["BETA_MO_NORM"]
    assert pi_surf.law_name == "POSTERIOR_PUSHFORWARD"
    assert 0.0 <= pi_surf.observed_exceedance <= 1.0
    assert pi_surf.critical_threshold_95 > 0.0

    # 5. Depth Path G_F
    assert len(state.depth_path_GF.shell_redshift_bins) == 3
    assert state.depth_path_GF.cross_shell_covariance.shape == (15, 15)
    assert len(state.depth_path_GF.relative_depth_contrasts) == 2

    # Serialization summary
    summary = state.to_summary_dict()
    assert summary["schema"] == "htt.five_variable_state_r39/1"
    assert summary["x_bundle"]["scope"] == "FULL_OBSERVABLE_X_BUNDLE"
    assert summary["depth_path_GF"]["num_shells"] == 3
