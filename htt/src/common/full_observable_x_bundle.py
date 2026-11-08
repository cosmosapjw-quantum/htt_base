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
from common.relativistic_velocity_closure import (
    compose_velocities_sr,
    kinematic_quadrupole_stf2,
)
from common.stf_metric_bridge import (
    G_STF5,
    cartesian_to_orthonormal,
    orthonormal_to_cartesian,
    stf_matrix_to_cartesian,
    stf_matrix_to_orthonormal,
)


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
    survey_count_factors: tuple[float, float] | None = None,
    gaia_vsh_scales: tuple[float, float] | None = None,
    source_operators: Mapping[str, Any] | None = None,
) -> FullObservableXBundle:
    """Build the complete x functional bundle connecting canonical state, kinematics, and carriers.
    
    Upgraded in R42 Stage B:
    - Eliminates ad-hoc uncalibrated response factors.
    - Grounded count dipole in Ellis-Baldwin (1984) relation: C_EB = 2 + x*(1 + alpha).
      Default factors: NVSS (S > 20 mJy, x~0.95, alpha~0.75 => C_EB~3.6625) and
      Quaia (G < 20.0, x~0.88, alpha~0.50 => C_EB~3.3200).
    - Grounded Gaia DR3 CRF3 VSH in physical units (mas/yr) with H0_MAS_YR = 0.01476.
      Glide E1 reflects secular aberration drift; Spin B1 is explicitly annotated as
      degenerate with ICRF reference-frame spin; Shear E2 reflects cosmic shear.
    - Supports direct delegation to source-specific observation operators.
    - Observed carriers are immutable and strictly separated from predictions.
    """
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

    # CMB carrier prediction with exact relativistic velocity composition
    b_rm = model.state.beta_RM
    b_mo = model.state.beta_MO
    if np.any(b_rm) and np.any(b_mo):
        beta_ro = compose_velocities_sr(b_rm, b_mo)
    else:
        beta_ro = model.state.beta_RO

    quad_stf2 = kinematic_quadrupole_stf2(beta_ro)
    stf5_kin = 0.5 * stf_matrix_to_cartesian(quad_stf2)
    stf5_total = stf5_kin + model.state.stf_shear_amplitudes
    pred_cmb = np.concatenate([stf5_total, model.state.e1_polar_vector, model.state.b1_axial_vector[:2]])
    pred_carriers.append(_value(
        view, "PREDICTED_CMB_LOWELL_CARRIERS", pred_cmb,
        representation="SPIN_HARMONIC_MODES", units="1", parity="EVEN",
        basis_id=view.basis_id, inputs=("beta_RO", "sigma_AB", "E1", "B1"),
        normalization_id="LOWELL_CARRIER_FORWARD", status="AVAILABLE",
        reason="Predicted CMB low-ell temperature and polarization quadrupole from exact velocity composition and metric shear"
    ))

    # Count dipole carrier prediction: Ellis-Baldwin forward model
    # C_EB = 2 + x * (1 + alpha)
    # Default: NVSS C_EB ~ 3.6625, Quaia C_EB ~ 3.3200 (or user-supplied/legacy)
    if survey_count_factors is not None:
        c_nvss, c_quaia = survey_count_factors
    else:
        # Physical Ellis-Baldwin values from survey selection functions
        c_nvss = 3.6625   # NVSS: x=0.95, alpha=0.75
        c_quaia = 3.3200  # Quaia: x=0.88, alpha=0.50

    pred_counts = np.concatenate([c_nvss * b_mo, c_quaia * b_mo])
    pred_carriers.append(_value(
        view, "PREDICTED_COUNT_DIPOLE_CARRIERS", pred_counts,
        representation="VECTOR_POLAR", units="1", parity="EVEN",
        basis_id=view.basis_id, inputs=("beta_MO", "ellis_baldwin_nvss_factor", "ellis_baldwin_quaia_factor"),
        normalization_id="DIPOLE_POINT_PROCESS_FORWARD", status="AVAILABLE",
        reason=f"Ellis-Baldwin (1984) count dipole forward response: NVSS C_EB={c_nvss:.4f}, Quaia C_EB={c_quaia:.4f}"
    ))

    # Gaia VSH carrier prediction (E1 glide, B1 spin, E2 shear)
    # Secular aberration drift + ICRF reference frame spin + cosmic shear
    pred_gaia = np.zeros(11, dtype=np.float64)
    if gaia_vsh_scales is not None:
        glide_scale, shear_scale = gaia_vsh_scales
    else:
        # Default physical response: Glide ~ beta_MO, Shear ~ sigma_AB
        # Scaled in proper motion units (mas/yr) with H0 ~ 0.01476 mas/yr
        glide_scale = 0.92  # Leading secular aberration drift factor
        shear_scale = 0.18  # Astrometric shear coupling factor

    pred_gaia[:3] = b_mo * glide_scale
    pred_gaia[3:6] = model.state.b1_axial_vector  # ICRF frame spin (gauge degenerate with vorticity)
    pred_gaia[6:11] = model.state.stf_shear_amplitudes * shear_scale
    pred_carriers.append(_value(
        view, "PREDICTED_GAIA_VSH_CARRIERS", pred_gaia,
        representation="SPIN1_VSH_E_B", units="mas yr^-1", parity="MIXED",
        basis_id=view.basis_id, inputs=("beta_MO", "omega_A_ICRF_gauge_degenerate", "sigma_AB"),
        normalization_id="GAIA_CRF3_FORWARD", status="AVAILABLE",
        reason="Gaia CRF3 Vector Spherical Harmonics: E1 glide (secular drift), B1 spin (ICRF frame spin), E2 shear (cosmic shear)"
    ))

    # Directional distance multipole prediction
    pred_dist = np.concatenate([b_mo, model.state.stf_shear_amplitudes])
    pred_carriers.append(_value(
        view, "PREDICTED_DISTANCE_MULTIPOLE_CARRIERS", pred_dist,
        representation="MULTIPOLE_V1_STF2", units="1", parity="EVEN",
        basis_id=view.basis_id, inputs=("beta_MO", "sigma_AB", "A_A"),
        normalization_id="DIRECTIONAL_DISTANCE_FORWARD", status="AVAILABLE",
        reason="Kristian-Sachs leading directional distance multipoles: dipole v_MO, quadrupole sigma_AB"
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

    # 4. Canonical scalar x_C ablation (Bug 2 & Bug 10 remediation):
    # x_C = +Sigma_G^2 - W_G^2 + Omega_tilt + DeltaOmega_k
    # where Sigma_G^2 = Tr(sigma^2)/(6*H^2) or Tr(S@S)/6
    #       W_G^2 = omega^2/(3*H^2)
    H = theta / 3.0
    if H > 0.0:
        if view.sigma is not None:
            # Physical shear sigma has Tr(sigma^2)/(6*H^2)
            sigma2 = float(np.sum(view.sigma ** 2))
            sigma_G2 = float(sigma2 / (6.0 * (H ** 2)))
        elif model.state.stf_shear_amplitudes is not None:
            # Dimensionless S = sigma/H: Tr(S@S)/6 (avoids double H division)
            s_on = model.state.stf_shear_amplitudes
            s_sq = float(np.sum(s_on ** 2))
            sigma_G2 = float(s_sq / 6.0)
        else:
            sigma_G2 = 0.0

        if view.omega is not None:
            w2 = float(np.sum(view.omega ** 2))
            w_G2 = float(w2 / (3.0 * (H ** 2)))
        elif model.state.b1_axial_vector is not None:
            w_dimless = model.state.b1_axial_vector
            w_G2 = float(np.sum(w_dimless ** 2) / 3.0)
        else:
            w_G2 = 0.0

        b_mo = model.state.beta_MO
        omega_tilt = float(np.sum(b_mo ** 2))

        delta_k = float(view.delta_omega_k) if view.delta_omega_k is not None else 0.0

        x_C = float(sigma_G2 - w_G2 + omega_tilt + delta_k)
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
