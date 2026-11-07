"""Full observable-carrier and tensor-x functional bundle.

Work Package A of HTT-R39 Observational Convergence.
Extends the kinematical functional sub-bundle to the complete x[s, alpha] = phi_alpha(Z_s)
bundle including:
  1. Direct physical kinematics (sigma_AB, omega_A, A_A, beta_RM, beta_MO)
  2. Normalized copies (sigma/H, omega/H, A/(cH))
  3. Mixed kinematic functionals (sigma.beta.beta/H, beta.omega/H, sigma.beta/H, beta x omega/H, beta.A/(cH), tr(sigma^3)/H^3, omega^2/H^2)
  4. Predicted observer-space carriers:
     - CMB low-ell T/E/B carriers
     - Selected source-count multipoles (Quaia/NVSS)
     - Gaia DR3 / CRF3 proper motion VSH carriers (E1 glide, B1 spin, E2 shear)
     - Directional-distance multipoles (Pantheon+/CF4)
  5. Immutable observed carriers with fixed source identity (role: OBSERVED_CARRIER)
  6. Optional scalar x_C ablation projection
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence
import numpy as np

from common.joint_anisotropy_state import JointAnisotropyState
from common.kinematical_functionals import (
    KinematicalState,
    KinematicalXBundle,
    FunctionalValue,
    build_kinematical_x_bundle,
    stf5_to_matrix,
    _value,
    _finite_scalar,
    _nonempty,
)
from common.kinematic_response import KinematicResponseModel


@dataclass(frozen=True)
class FullObservableXBundle:
    """Complete multi-probe tensor-x bundle combining physical kinematics and observable carriers."""

    canonical_state_id: str
    physical_view_state_id: str
    expansion_scalar: float
    speed_of_light: float
    kinematical_bundle: KinematicalXBundle
    predicted_carriers: tuple[FunctionalValue, ...]
    observed_carriers: tuple[FunctionalValue, ...]
    scalar_xC_ablation: float | None = None
    scope: str = "FULL_OBSERVABLE_X_BUNDLE"

    def __post_init__(self):
        _nonempty(self.canonical_state_id, "canonical_state_id")
        _nonempty(self.physical_view_state_id, "physical_view_state_id")
        if self.scope != "FULL_OBSERVABLE_X_BUNDLE":
            raise ValueError("Scope must be FULL_OBSERVABLE_X_BUNDLE")

    @property
    def all_functionals(self) -> tuple[FunctionalValue, ...]:
        """Flattened tuple of all physical functionals and predicted carriers."""
        return self.kinematical_bundle.physical_functionals + self.predicted_carriers


def build_full_observable_x_bundle(
    joint_state: JointAnisotropyState,
    model: KinematicResponseModel,
    *,
    expansion_scalar: float,
    speed_of_light: float = 299_792_458.0,
    sample_id: str | None = None,
    observed_carriers_dict: Mapping[str, np.ndarray] | None = None,
) -> FullObservableXBundle:
    """Build the complete x functional bundle connecting canonical state, kinematics, and carriers."""
    theta = _finite_scalar(expansion_scalar, "expansion_scalar")
    c = _finite_scalar(speed_of_light, "speed_of_light")

    # 1. Base kinematical x sub-bundle
    kin_bundle = build_kinematical_x_bundle(
        joint_state,
        expansion_scalar=theta,
        speed_of_light=c,
        sample_id=sample_id,
    )

    # 2. Derive predicted observable carriers from forward models
    pred_carriers: list[FunctionalValue] = []
    view = KinematicalState.from_joint_anisotropy_state(
        joint_state, expansion_scalar=theta, speed_of_light=c, sample_id=sample_id
    )

    # CMB carrier prediction
    beta_ro = model.state.beta_RO
    stf5_kin = np.array([
        0.5 * (beta_ro[0]**2 - (1.0/3.0)*np.sum(beta_ro**2)),
        0.5 * (beta_ro[1]**2 - (1.0/3.0)*np.sum(beta_ro**2)),
        beta_ro[0]*beta_ro[1],
        beta_ro[0]*beta_ro[2],
        beta_ro[1]*beta_ro[2],
    ])
    stf5_total = stf5_kin + model.state.stf_shear_amplitudes
    pred_cmb = np.concatenate([stf5_total, model.state.e1_polar_vector, model.state.b1_axial_vector[:2]])
    pred_carriers.append(_value(
        view, "PREDICTED_CMB_LOWELL_CARRIERS", pred_cmb,
        representation="SPIN_HARMONIC_MODES", units="1", parity="EVEN",
        basis_id=view.basis_id, inputs=("beta_RO", "sigma_AB", "E1", "B1"),
        normalization_id="LOWELL_CARRIER_FORWARD", status="AVAILABLE"
    ))

    # Count dipole carrier prediction
    b_mo = model.state.beta_MO
    pred_counts = np.concatenate([3.75 * b_mo, 3.40 * b_mo])
    pred_carriers.append(_value(
        view, "PREDICTED_COUNT_DIPOLE_CARRIERS", pred_counts,
        representation="VECTOR_POLAR", units="1", parity="EVEN",
        basis_id=view.basis_id, inputs=("beta_MO", "selection_factor"),
        normalization_id="DIPOLE_POINT_PROCESS_FORWARD", status="AVAILABLE"
    ))

    # Gaia VSH carrier prediction (E1 glide, B1 spin, E2 shear)
    pred_gaia = np.zeros(11, dtype=np.float64)
    pred_gaia[:3] = b_mo * 0.92
    pred_gaia[3:6] = model.state.b1_axial_vector
    pred_gaia[6:11] = model.state.stf_shear_amplitudes * 0.18
    pred_carriers.append(_value(
        view, "PREDICTED_GAIA_VSH_CARRIERS", pred_gaia,
        representation="SPIN1_VSH_E_B", units="mas yr^-1", parity="MIXED",
        basis_id=view.basis_id, inputs=("beta_MO", "omega_A", "sigma_AB"),
        normalization_id="GAIA_CRF3_FORWARD", status="AVAILABLE"
    ))

    # Directional distance multipole prediction
    pred_dist = np.concatenate([b_mo, model.state.stf_shear_amplitudes])
    pred_carriers.append(_value(
        view, "PREDICTED_DISTANCE_MULTIPOLE_CARRIERS", pred_dist,
        representation="MULTIPOLE_V1_STF2", units="1", parity="EVEN",
        basis_id=view.basis_id, inputs=("beta_MO", "sigma_AB", "A_A"),
        normalization_id="DIRECTIONAL_DISTANCE_FORWARD", status="AVAILABLE"
    ))

    # 3. Fixed observed carriers (role: OBSERVED_CARRIER)
    obs_carriers: list[FunctionalValue] = []
    if observed_carriers_dict is not None:
        for name, arr in observed_carriers_dict.items():
            obs_carriers.append(_value(
                view, f"OBSERVED_{name}", np.asarray(arr, dtype=np.float64),
                representation="OBSERVED_CARRIER", units="1", parity="EVEN",
                basis_id="OBSERVER_SKY", inputs=(),
                normalization_id="SOURCE_BOUND_EVIDENCE", status="AVAILABLE",
                reason="Fixed observed evidence with source provenance"
            ))

    # 4. Optional scalar x_C ablation:
    # x_C = DeltaOmega_k - (1/3) sigma_AB sigma^AB / H^2
    H = theta / 3.0
    sigma_mat = view.sigma
    if sigma_mat is not None and H > 0.0:
        sigma2 = float(np.sum(sigma_mat ** 2))
        delta_k = view.delta_omega_k if view.delta_omega_k is not None else 0.0
        x_C = float(delta_k - (1.0 / 3.0) * (sigma2 / (H**2)))
    else:
        x_C = None

    return FullObservableXBundle(
        canonical_state_id=joint_state.content_id,
        physical_view_state_id=view.state_id,
        expansion_scalar=theta,
        speed_of_light=c,
        kinematical_bundle=kin_bundle,
        predicted_carriers=tuple(pred_carriers),
        observed_carriers=tuple(obs_carriers),
        scalar_xC_ablation=x_C,
    )
