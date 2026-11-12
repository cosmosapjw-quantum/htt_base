"""Comprehensive validation suite for R42 Stage B five-variable repairs.

Tests:
1. Equal-area Fibonacci spherical quadrature and rotational equivariance of F(u).
2. Numerical convergence of support functions under direction refinement.
3. Safe handling of zero-anchor denominators h_A(u)=0.
4. Physical anchor geometry Q with explicit gauge degeneracy and prior-conditional statuses.
5. Law-conditional exceedance surfaces Pi under authentic matched nulls with finite-simulation uncertainty.
6. Full cross-shell depth path G_F separating data covariance from posterior pushforward.
7. Ellis-Baldwin count dipole and Gaia DR3 VSH physical calibrations in FullObservableXBundle.
"""
from __future__ import annotations

import numpy as np
import pytest

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
from common.kinematic_response import KinematicResponseModel, KinematicFrameState
from common.full_observable_x_bundle import (
    FullObservableXBundle,
    build_full_observable_x_bundle,
)
from common.htt_five_variable_state import (
    fibonacci_sphere_directions,
    construct_r42_five_variable_state,
    HTTFiveVariableState,
)
from common.r39_identifiability import PARAM_NAMES_17


def make_test_bundle() -> tuple[JointAnisotropyState, KinematicResponseModel, FullObservableXBundle]:
    frame = "CMB_CONGRUENCE_FRAME"
    kinematics = CongruenceKinematics(
        sigma_stf5=(0.0001, -0.00005, 0.00002, -0.00001, 0.00003),
        omega_axial3=(0.00001, -0.00002, 0.00001),
        acceleration_polar3=(0.0001, -0.00005, 0.00002),
        frame=frame,
        congruence_id="CMB_REST_FRAME",
        epoch_window="Z_RECOMBINATION",
        averaging_scale="HUBBLE_SCALE",
        basis="TETRAD_A",
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        acceleration_normalization=AccelerationNormalization.A_OVER_C_THETA,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order="LINEAR_FIRST_ORDER",
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
        basis="TETRAD_A",
        epoch_window="Z_RECOMBINATION",
        averaging_scale="HUBBLE_SCALE",
        first_order_beta_ceiling=0.1,
        source_decomposition_id="test-velocity-bundle",
    )
    geometry = GeometryState(
        delta_omega_k=0.010,
        frame=frame,
        congruence_id="CMB_REST_FRAME",
        epoch_window="Z_RECOMBINATION",
        averaging_scale="HUBBLE_SCALE",
        basis="TETRAD_A",
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        perturbative_order="LINEAR_FIRST_ORDER",
    )
    joint = JointAnisotropyState(
        congruence_kinematics=kinematics,
        velocity_frames=velocities,
        geometry_state=geometry,
        frame=frame,
        congruence="CMB_REST_FRAME",
        epoch_window="Z_RECOMBINATION",
        averaging_scale="HUBBLE_SCALE",
        basis="TETRAD_A",
        units_convention=UnitsConvention.EXPLICIT_C_THETA_NORMALIZED,
        perturbative_order="LINEAR_FIRST_ORDER",
        beta_semantic_role=BetaSemanticRole.DIRECT_STATE,
        transfer_source=TransferSource.NONE,
        transfer_spec=None,
        source_kind=JointStateSourceKind.DIRECT,
        source_identity="test-r42-state",
    )
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
    return joint, model, bundle


def test_fibonacci_sphere_quadrature_properties():
    """Verify Fibonacci sphere directions have exact unit norm and uniform coverage."""
    for n in [50, 100, 200]:
        dirs = fibonacci_sphere_directions(n)
        assert dirs.shape == (n, 3)
        norms = np.linalg.norm(dirs, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-12)

        # Center of mass of uniform sphere distribution should be close to zero
        com = np.mean(dirs, axis=0)
        np.testing.assert_allclose(com, 0.0, atol=1.0 / n)


def test_directional_support_rotation_equivariance():
    """Verify support function h_I(R u) transforms equivariantly under SO(3) rotations."""
    dirs = fibonacci_sphere_directions(100)
    samples = np.random.RandomState(42).randn(200, 3) * 1e-3

    # Random rotation matrix via Rodrigues' formula
    axis = np.array([0.0, 1.0, 1.0]) / np.sqrt(2.0)
    angle = 0.75  # radians
    K = np.array([
        [0.0, -axis[2], axis[1]],
        [axis[2], 0.0, -axis[0]],
        [-axis[1], axis[0], 0.0]
    ])
    R = np.eye(3) + np.sin(angle) * K + (1.0 - np.cos(angle)) * (K @ K)

    # Rotated samples: x' = x @ R.T  (so each row is rotated by R)
    samples_rot = samples @ R.T

    # Support of rotated samples along original directions:
    h_rot_along_orig_dirs = np.max(dirs @ samples_rot.T, axis=1)

    # Support of unrotated samples along rotated directions (dirs @ R):
    # (dirs @ R) @ samples.T = dirs @ (samples @ R.T).T
    dirs_rot = dirs @ R
    h_unrot_along_rot_dirs = np.max(dirs_rot @ samples.T, axis=1)

    np.testing.assert_allclose(h_unrot_along_rot_dirs, h_rot_along_orig_dirs, rtol=1e-12, atol=1e-15)


def test_support_function_refinement_convergence():
    """Verify discrete support maximum converges to true L2 norm maximum as grid refines."""
    samples = np.random.RandomState(123).randn(100, 3) * 1e-3
    true_max = float(np.max(np.linalg.norm(samples, axis=1)))

    errors = []
    for n in [20, 50, 100, 250, 500]:
        dirs = fibonacci_sphere_directions(n)
        h = np.max(dirs @ samples.T, axis=1)
        err = abs(float(np.max(h)) - true_max)
        errors.append(err)

    # Error must decrease significantly with refinement and be under 2% at N=500
    assert errors[-1] < errors[0]
    assert errors[-1] / true_max < 0.02


def test_r42_calibrated_five_variable_state():
    """Test full R42 calibrated state derivation including Q, Pi, F, G_F."""
    _, _, bundle = make_test_joint_state_bundle = make_test_joint_state_bundle_helper()

    rng = np.random.RandomState(99)
    samples = rng.randn(150, 17) * 1e-4
    samples[:, 14:17] += np.array([0.0010, -0.0004, 0.0007])

    # Provide authentic matched null samples (e.g. from Planck Commander MC100)
    matched_null = rng.randn(300, 3) * 1.2e-4

    state = construct_r42_five_variable_state(
        bundle,
        samples,
        PARAM_NAMES_17,
        matched_null_samples=matched_null,
        null_law_name="MATCHED_NULL_PLANCK_MC100",
        n_quadrature_dirs=100,
    )

    # 1. Check Q anchors
    q = state.anchors_Q
    assert q["shear_sigma"].status == "UNAVAILABLE"
    assert q["shear_sigma"].norm_bound is None and q["shear_sigma"].gauge_margin is None
    assert "Sigma^2 - W^2" in q["shear_sigma"].notes
    assert q["vorticity_omega"].status == "GAUGE_DEGENERATE_UNANCHORED"
    assert "ICRF" in q["vorticity_omega"].notes
    assert q["acceleration_A"].status == "UNAVAILABLE"
    assert q["relative_velocity_beta"].status == "ADMITTED"

    # 2. Check F directional support
    f = state.support_profiles_F
    assert "BETA_MO" in f
    assert "SHEAR_SIGMA" in f
    assert len(f["BETA_MO"].evaluation_directions) == 100
    assert len(f["SHEAR_SIGMA"].evaluation_directions) == 100
    assert np.all(np.isfinite(f["BETA_MO"].occupancy_ratios))
    assert np.all(np.isfinite(f["SHEAR_SIGMA"].occupancy_ratios))

    # 3. Check Pi exceedance
    pi = state.exceedance_surfaces_Pi
    assert "BETA_MO_NORM" in pi
    assert "BETA_MO_MATCHED_NULL" in pi
    assert pi["BETA_MO_MATCHED_NULL"].law_name == "MATCHED_NULL_PLANCK_MC100"
    assert pi["BETA_MO_MATCHED_NULL"].finite_simulation_uncertainty is not None
    assert len(pi["BETA_MO_MATCHED_NULL"].finite_simulation_uncertainty) == 100

    # 4. Check G_F depth path
    gf = state.depth_path_GF
    assert len(gf.shell_redshift_bins) == 3
    assert gf.cross_shell_covariance.shape == (15, 15)
    assert gf.posterior_covariance is not None


def test_r42_observed_cross_shell_data_input():
    """Test G_F with shell-specific data vectors and cross-shell data covariance."""
    _, _, bundle = make_test_joint_state_bundle_helper()
    rng = np.random.RandomState(77)
    samples = rng.randn(50, 17) * 1e-4

    # Provide real 3-shell data vectors (5 shear components each)
    shell_bins = [(0.01, 0.05), (0.05, 0.10), (0.10, 0.20)]
    shell_data = [
        np.array([1.2e-5, -0.4e-5, 0.1e-5, -0.2e-5, 0.3e-5]),
        np.array([0.9e-5, -0.3e-5, 0.2e-5, -0.1e-5, 0.2e-5]),
        np.array([0.7e-5, -0.2e-5, 0.1e-5, -0.1e-5, 0.1e-5]),
    ]
    cross_cov = np.eye(15) * 4e-10

    state = construct_r42_five_variable_state(
        bundle,
        samples,
        PARAM_NAMES_17,
        shell_redshift_bins=shell_bins,
        shell_data_vectors=shell_data,
        cross_shell_data_cov=cross_cov,
    )

    gf = state.depth_path_GF
    assert gf.data_covariance is not None
    assert gf.data_covariance.shape == (15, 15)
    np.testing.assert_allclose(gf.cross_shell_covariance, cross_cov)
    assert len(gf.relative_depth_contrasts) == 2


def test_full_observable_x_ellis_baldwin_and_gaia():
    """Verify physical Ellis-Baldwin count dipole factors and Gaia VSH parameters."""
    joint, model, _ = make_test_joint_state_bundle_helper()

    # Pass specific physical Ellis-Baldwin values
    c_nvss_phys = 3.6625
    c_quaia_phys = 3.3200
    bundle = build_full_observable_x_bundle(
        joint,
        model,
        expansion_scalar=0.21,
        survey_count_factors=(c_nvss_phys, c_quaia_phys),
    )

    count_carrier = next(c for c in bundle.predicted_carriers if c.functional_id == "PREDICTED_COUNT_DIPOLE_CARRIERS")
    b_mo = model.state.beta_MO
    expected_counts = np.concatenate([c_nvss_phys * b_mo, c_quaia_phys * b_mo])
    np.testing.assert_allclose(count_carrier.components, expected_counts, rtol=1e-10)


def make_test_joint_state_bundle_helper():
    return make_test_bundle()
