"""Unit tests for FullObservableXBundle and carrier predictions."""
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


def test_build_full_observable_x_bundle():
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

    observed_dict = {
        "PLANCK_LOWELL": np.array([1e-5, 2e-5]),
        "QUAIA_DIPOLE": np.array([0.02, 0.01, -0.01]),
    }

    bundle = build_full_observable_x_bundle(
        joint,
        model,
        expansion_scalar=0.21,
        observed_carriers_dict=observed_dict,
    )

    assert bundle.canonical_state_id == joint.content_id
    assert bundle.scope == "FULL_OBSERVABLE_X_BUNDLE"
    assert len(bundle.predicted_carriers) == 4
    assert len(bundle.observed_carriers) == 2
    assert bundle.scalar_xC_ablation is not None

    # Check predicted carrier IDs
    pred_ids = {c.functional_id for c in bundle.predicted_carriers}
    assert "PREDICTED_CMB_LOWELL_CARRIERS" in pred_ids
    assert "PREDICTED_COUNT_DIPOLE_CARRIERS" in pred_ids
    assert "PREDICTED_GAIA_VSH_CARRIERS" in pred_ids
    assert "PREDICTED_DISTANCE_MULTIPOLE_CARRIERS" in pred_ids

    # Check observed carrier IDs
    obs_ids = {c.functional_id for c in bundle.observed_carriers}
    assert "OBSERVED_PLANCK_LOWELL" in obs_ids
    assert "OBSERVED_QUAIA_DIPOLE" in obs_ids

    # Check all_functionals property
    assert len(bundle.all_functionals) == len(bundle.kinematical_bundle.physical_functionals) + 4
