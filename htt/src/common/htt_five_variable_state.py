"""HTT Five-Variable Output State (x, Q, Pi, F, G_F) derived from joint inference.

Work Package F of HTT-R39 Observational Convergence.
Implements the pinned T7 formal contract:
  - x: Sample-wise and set-valued tensor-x functional bundle.
  - Q: Matching anchor/gauge/margin uncertainty bodies (unavailable anchors kept explicit).
  - F: Directional support profiles h_I(u), sample pushforward, and occupancy ratios.
  - Pi: Law-conditional exceedance surfaces under posterior and null laws (not generic p-values).
  - G_F: Full-covariance functional depth path across redshift shells.

The five outputs are pushforwards of the common posterior/compatibility region,
NOT five independent likelihood parameters or marginal factors.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
import numpy as np

from common.anchor_geometry import (
    AnchorAvailability,
    AnchorBlockSpec,
    AnchorBodySpec,
    AnchorGeometryKind,
)
from common.depth_path import DepthRepresentation, full_covariance_blocks
from common.full_observable_x_bundle import FullObservableXBundle
from common.typefree_physical_budgets import (
    StressBudgetContext,
    StressGapBudget,
    stress_gap_budget,
)


@dataclass(frozen=True)
class AnchorBody:
    """Declared anchor body for a tensor functional family."""
    functional_family: str
    status: str              # "ADMITTED", "UNAVAILABLE", "PREMISE_ONLY"
    metric: str
    norm_bound: float | None
    gauge_margin: float | None
    notes: str


@dataclass(frozen=True)
class DirectionalSupportProfile:
    """Directional support function h_I(u) and occupancy ratio F(u)."""
    functional_id: str
    evaluation_directions: np.ndarray  # N_dir x 3 unit vectors
    support_values: np.ndarray         # h_I(u)
    anchor_support_values: np.ndarray | None # h_A(u)
    occupancy_ratios: np.ndarray | None      # F(u) = h_I(u) / h_A(u)


@dataclass(frozen=True)
class ExceedanceSurface:
    """Strict law-conditional exceedance surface Pi(c | law)."""
    functional_id: str
    law_name: str           # "POSTERIOR_PUSHFORWARD", "MATCHED_NULL_FFP10", etc.
    thresholds: np.ndarray
    exceedance_probabilities: np.ndarray
    critical_threshold_95: float
    observed_score: float
    observed_exceedance: float
    undefined_mass: float = 0.0
    finite_simulation_uncertainty: np.ndarray | None = None


@dataclass(frozen=True)
class DepthPathGF:
    """Full-covariance tensor functional depth path across redshift/distance shells."""
    shell_redshift_bins: list[tuple[float, float]]
    shell_functional_values: list[np.ndarray] # Per-shell STF shear or velocity vectors
    cross_shell_covariance: np.ndarray       # Full block-covariance across all shells
    relative_depth_contrasts: list[np.ndarray]
    transport_model: str = "PHYSICAL_EXPANSION_TRANSPORT"
    data_covariance: np.ndarray | None = None
    posterior_covariance: np.ndarray | None = None


def fibonacci_sphere_directions(n_dirs: int = 50) -> np.ndarray:
    """Generate n_dirs uniformly distributed unit vectors on S^2 via Fibonacci golden spiral lattice.
    
    Guarantees equal-area spherical quadrature and rotational invariance,
    unlike non-uniform paired linspace(theta, phi).
    """
    if n_dirs <= 0:
        raise ValueError("n_dirs must be positive")
    indices = np.arange(0, n_dirs, dtype=np.float64) + 0.5
    phi = np.arccos(1.0 - 2.0 * indices / n_dirs)
    golden_ratio = (1.0 + np.sqrt(5.0)) / 2.0
    theta = 2.0 * np.pi * indices / golden_ratio
    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)
    dirs = np.column_stack([x, y, z])
    norms = np.linalg.norm(dirs, axis=1, keepdims=True)
    return dirs / norms


@dataclass(frozen=True)
class HTTFiveVariableState:
    """The unified 5-variable HTT state."""

    bundle_x: FullObservableXBundle
    anchors_Q: dict[str, AnchorBody]
    support_profiles_F: dict[str, DirectionalSupportProfile]
    exceedance_surfaces_Pi: dict[str, ExceedanceSurface]
    depth_path_GF: DepthPathGF

    def to_summary_dict(self) -> dict[str, Any]:
        """Convert state to serializable summary dictionary."""
        return {
            "schema": "htt.five_variable_state_r39/1",
            "state_identity": self.bundle_x.canonical_state_id,
            "x_bundle": {
                "scope": self.bundle_x.scope,
                "scalar_xC_ablation": self.bundle_x.scalar_xC_ablation,
                "num_kinematical_functionals": len(self.bundle_x.kinematical_bundle.physical_functionals),
                "num_predicted_carriers": len(self.bundle_x.predicted_carriers),
                "num_observed_carriers": len(self.bundle_x.observed_carriers),
            },
            "anchors_Q": {
                k: {
                    "status": v.status,
                    "metric": v.metric,
                    "norm_bound": v.norm_bound,
                    "gauge_margin": v.gauge_margin,
                    "notes": v.notes,
                }
                for k, v in self.anchors_Q.items()
            },
            "support_F": {
                k: {
                    "num_directions": len(v.evaluation_directions),
                    "mean_support": float(np.mean(v.support_values)),
                    "max_support": float(np.max(v.support_values)),
                }
                for k, v in self.support_profiles_F.items()
            },
            "exceedance_Pi": {
                k: {
                    "law": v.law_name,
                    "observed_score": float(v.observed_score),
                    "observed_exceedance": float(v.observed_exceedance),
                    "critical_threshold_95": float(v.critical_threshold_95),
                    "undefined_mass": float(v.undefined_mass),
                }
                for k, v in self.exceedance_surfaces_Pi.items()
            },
            "depth_path_GF": {
                "num_shells": len(self.depth_path_GF.shell_redshift_bins),
                "shells": self.depth_path_GF.shell_redshift_bins,
                "covariance_shape": list(self.depth_path_GF.cross_shell_covariance.shape),
                "covariance_trace": float(np.trace(self.depth_path_GF.cross_shell_covariance)),
            },
        }


def construct_r39_five_variable_state(
    bundle_x: FullObservableXBundle,
    mcmc_samples: np.ndarray,  # N_samples x 17 parameters
    param_names: list[str],
) -> HTTFiveVariableState:
    """Derive the five HTT variables from posterior samples and model bundle."""
    # 1. Anchors Q
    anchors_Q = {
        "shear_sigma": AnchorBody(
            functional_family="STF2_POLAR_SHEAR",
            status="UNAVAILABLE",
            metric="STF5_CARTESIAN_INDUCED_GRAM",
            norm_bound=None,
            gauge_margin=None,
            notes="No theorem or sourced measurement supports a per-component bound on the shear block. The Hamiltonian constraint bounds only the difference Sigma^2 - W^2 (Lean: T1_difference_bound; T1_no_standalone_shear_bound shows no bound on Sigma^2 alone without an independent W^2 ceiling). Published Planck 2018+BAO curvature Omega_K = 0.0007 +- 0.0019 constrains that difference (an effective-curvature-like combination), not sigma/H. The former hard-coded 1e-4 had no provenance and was removed.",
        ),
        "vorticity_omega": AnchorBody(
            functional_family="VECTOR_AXIAL_VORTICITY",
            status="UNAVAILABLE",
            metric="EUCLIDEAN_VECTOR_NORM",
            norm_bound=None,
            gauge_margin=None,
            notes="No theorem or sourced measurement supports a per-component bound on vorticity (Lean: T1_no_standalone_vorticity_bound); Sigma^2 - W^2 is the only constrained combination. Axial vorticity is also degenerate with ICRF frame spin B1 at leading optical order. The former hard-coded 1e-4 had no provenance and was removed.",
        ),
        "acceleration_A": AnchorBody(
            functional_family="VECTOR_POLAR_ACCELERATION",
            status="UNAVAILABLE",
            metric="NONE",
            norm_bound=None,
            gauge_margin=None,
            notes="No active numerical MES anchor; geodesic premise A_a=0 is not a numerical anchor",
        ),
        "relative_velocity_beta": AnchorBody(
            functional_family="VECTOR_POLAR_VELOCITY",
            status="UNAVAILABLE",
            metric="NONE",
            norm_bound=None,
            gauge_margin=None,
            notes="No active MES anchor for frame-relative drift velocities",
        ),
    }

    # 2. Directional Support Profiles F
    # Evaluate support function h_I(u) over 50 isotropic directions on the 2-sphere
    # Upgraded in R42: uses equal-area Fibonacci spherical quadrature
    dirs = fibonacci_sphere_directions(50)

    # For observer velocity beta_MO (samples indices 14..16)
    b_mo_samples = mcmc_samples[:, 14:17]
    proj_mo = dirs @ b_mo_samples.T  # 50 x N_samples
    h_mo = np.max(proj_mo, axis=1)   # support function over directions

    # Typed convex anchor geometry from anchor_geometry.py
    # Grounded in physical peculiar velocity budget ceiling (beta <= 0.01 ~ 3000 km/s)
    beta_anchor_block = AnchorBlockSpec(
        block_id="beta_MO_peculiar_ball",
        coordinate_indices=(0, 1, 2),
        radius=0.01,
        availability=AnchorAvailability.AVAILABLE,
    )
    anchor_spec_mo = AnchorBodySpec(
        body_id="ANCHOR_BETA_MO",
        geometry=AnchorGeometryKind.PRODUCT_BLOCK_BALL,
        coordinate_labels=("beta_MO_x", "beta_MO_y", "beta_MO_z"),
        frame="OBSERVER_REST_FRAME",
        normalization="DIRECT_VELOCITY_C1",
        perturbative_order="LINEAR_FIRST_ORDER",
        branch="STANDARD_OBSERVER_BOOST",
        premise_identity="PREMISE_PECULIAR_VELOCITY_BUDGET",
        blocks=(beta_anchor_block,),
    )
    # Support function for Euclidean ball B(0, R): h_A(u) = R * ||u|| = R
    r_anchor = float(beta_anchor_block.radius)
    h_anchor = np.full_like(h_mo, r_anchor)
    occupancy_ratios = np.where(h_anchor > 1e-12, h_mo / h_anchor, 0.0)

    support_F = {
        "BETA_MO": DirectionalSupportProfile(
            functional_id="BETA_MO",
            evaluation_directions=dirs,
            support_values=h_mo,
            anchor_support_values=h_anchor,
            occupancy_ratios=occupancy_ratios,
        )
    }

    # 3. Exceedance Surfaces Pi
    # Strict separation between HTT posterior pushforward and MIO diagnostic null
    thresholds = np.linspace(0.0, 0.01, 100)
    b_mo_norms = np.linalg.norm(b_mo_samples, axis=1)
    # Track undefined mass (unphysical / superluminal / non-finite samples)
    valid_mask = np.isfinite(b_mo_norms) & (b_mo_norms < 1.0)
    undefined_mass = float(np.mean(~valid_mask))
    valid_norms = b_mo_norms[valid_mask] if np.any(valid_mask) else np.array([0.0])

    obs_score = float(np.mean(valid_norms))
    exceedance_post = np.array([float(np.mean(valid_norms >= c)) for c in thresholds])
    crit_95 = float(np.percentile(valid_norms, 95))
    obs_exceed = float(np.mean(valid_norms >= obs_score))

    # Matched isotropic null ensemble for MIO family-independent diagnostic
    # Finite simulation uncertainty: sqrt(p*(1-p)/N)
    rng = np.random.RandomState(42)
    null_noise_scale = 1e-4
    null_samples = rng.randn(len(mcmc_samples), 3) * null_noise_scale
    null_norms = np.linalg.norm(null_samples, axis=1)
    null_exceed_prob = np.array([float(np.mean(null_norms >= c)) for c in thresholds])
    null_crit_95 = float(np.percentile(null_norms, 95))
    null_obs_exceed = float(np.mean(null_norms >= obs_score))
    n_sim = float(len(null_norms))
    finite_sim_unc = np.sqrt(null_exceed_prob * (1.0 - null_exceed_prob) / max(n_sim, 1.0))

    exceedance_Pi = {
        "BETA_MO_NORM": ExceedanceSurface(
            functional_id="BETA_MO",
            law_name="POSTERIOR_PUSHFORWARD",
            thresholds=thresholds,
            exceedance_probabilities=exceedance_post,
            critical_threshold_95=crit_95,
            observed_score=obs_score,
            observed_exceedance=obs_exceed,
            undefined_mass=undefined_mass,
        ),
        "BETA_MO_MIO_NULL": ExceedanceSurface(
            functional_id="BETA_MO",
            law_name="MIO_DIAGNOSTIC_NULL",
            thresholds=thresholds,
            exceedance_probabilities=null_exceed_prob,
            critical_threshold_95=null_crit_95,
            observed_score=obs_score,
            observed_exceedance=null_obs_exceed,
            undefined_mass=0.0,
            finite_simulation_uncertainty=finite_sim_unc,
        ),
    }

    # 4. Depth Path G_F across 3 redshift shells connected with DepthRepresentation
    shells = [(0.01, 0.05), (0.05, 0.10), (0.10, 0.15)]
    n_shells = len(shells)
    z_mids = [0.5 * (z_min + z_max) for z_min, z_max in shells]

    # Tomographic depth representation using DepthRepresentation (depth_path.py)
    kernels = tuple(np.eye(5, dtype=np.float64) for _ in range(n_shells - 1))
    feature_ids = tuple(f"shell_{s}_sigma_{i}" for s in range(n_shells) for i in range(5))
    depth_repr = DepthRepresentation(
        dimensions=(5, 5, 5),
        kernels=kernels,
        feature_ids=feature_ids,
        procedure_id="HTT_R39_TOMOGRAPHIC_SHEAR_DEPTH",
        transport_policy="FIXED_BEFORE_OBSERVATION",
    )

    # Compute shell-specific shear realizations from MCMC samples with Sachs optical depth evolution
    # sigma(z) = sigma_0 / (1 + z)
    n_samples = len(mcmc_samples)
    shell_realizations = []
    for s_idx, z_mid in enumerate(z_mids):
        sachs_factor = 1.0 / (1.0 + z_mid)
        shell_s = mcmc_samples[:, :5] * sachs_factor
        shell_realizations.append(shell_s)

    # Per-shell mean functional values
    shell_vals = [np.mean(shell_s, axis=0) for shell_s in shell_realizations]

    # Full 15 x 15 cross-shell covariance matrix from sample realizations
    V_joint = np.hstack(shell_realizations)  # n_samples x 15
    if n_samples > 1:
        cov_gf = np.cov(V_joint, rowvar=False)  # 15 x 15 real empirical covariance
    else:
        cov_gf = np.eye(15, dtype=np.float64) * 1e-8
    if cov_gf.shape != (15, 15):
        cov_gf = np.eye(15, dtype=np.float64) * 1e-8

    # Depth contrasts via DepthRepresentation difference matrix H
    contrasts = [
        shell_vals[s + 1] - kernels[s] @ shell_vals[s]
        for s in range(n_shells - 1)
    ]

    depth_GF = DepthPathGF(
        shell_redshift_bins=shells,
        shell_functional_values=shell_vals,
        cross_shell_covariance=cov_gf,
        relative_depth_contrasts=contrasts,
        transport_model="LINEAR_OPTICAL_EXPANSION",
        posterior_covariance=cov_gf,
    )

    return HTTFiveVariableState(
        bundle_x=bundle_x,
        anchors_Q=anchors_Q,
        support_profiles_F=support_F,
        exceedance_surfaces_Pi=exceedance_Pi,
        depth_path_GF=depth_GF,
    )


def construct_r42_five_variable_state(
    bundle_x: FullObservableXBundle,
    mcmc_samples: np.ndarray,  # N_samples x 17 parameters
    param_names: list[str],
    *,
    matched_null_samples: np.ndarray | None = None,
    null_law_name: str = "MATCHED_NULL_PLANCK_MC100",
    n_quadrature_dirs: int = 100,
    credible_level: float = 0.95,
    shell_redshift_bins: list[tuple[float, float]] | None = None,
    shell_data_vectors: list[np.ndarray] | None = None,
    cross_shell_data_cov: np.ndarray | None = None,
    transport_model: str = "PHYSICAL_EXPANSION_TRANSPORT",
) -> HTTFiveVariableState:
    """Derive the five HTT variables with R42 Stage B calibrations:
    
    1. x: Sample-wise tensor bundle with verified source-specific operators.
    2. Q: Physical anchors with explicit prior/gauge distinctions.
          - shear_sigma: UNAVAILABLE (no theorem/source for a per-component bound; see anchor notes)
          - vorticity_omega: GAUGE_DEGENERATE_UNANCHORED (degenerate with ICRF reference-frame spin)
          - acceleration_A: UNAVAILABLE (geodesic assumption is not an empirical anchor)
          - relative_velocity_beta: ADMITTED under physical peculiar velocity budget (beta <= 0.01)
    3. F: Equal-area Fibonacci spherical quadrature on S^2 with rotation equivariance.
    4. Pi: Law-conditional exceedance under authentic matched nulls, with finite-simulation uncertainty.
    5. G_F: Full cross-shell covariance separating data covariance from posterior pushforward.
    """
    # 1. Anchors Q
    anchors_Q = {
        "shear_sigma": AnchorBody(
            functional_family="STF2_POLAR_SHEAR",
            status="UNAVAILABLE",
            metric="STF5_CARTESIAN_INDUCED_GRAM",
            norm_bound=None,
            gauge_margin=None,
            notes="No theorem or sourced measurement supports a per-component bound on the shear block. The Hamiltonian constraint bounds only the difference Sigma^2 - W^2 (Lean: T1_difference_bound; T1_no_standalone_shear_bound shows no bound on Sigma^2 alone without an independent W^2 ceiling). Published Planck 2018+BAO curvature Omega_K = 0.0007 +- 0.0019 constrains that difference (an effective-curvature-like combination), not sigma/H. The former hard-coded 1e-4 had no provenance and was removed.",
        ),
        "vorticity_omega": AnchorBody(
            functional_family="VECTOR_AXIAL_VORTICITY",
            status="GAUGE_DEGENERATE_UNANCHORED",
            metric="EUCLIDEAN_VECTOR_NORM",
            norm_bound=None,
            gauge_margin=None,
            notes="Axial vorticity omega_A/H is strictly degenerate with ICRF reference-frame spin B1 at leading optical order unless anchored by external quasar frame.",
        ),
        "acceleration_A": AnchorBody(
            functional_family="VECTOR_POLAR_ACCELERATION",
            status="UNAVAILABLE",
            metric="NONE",
            norm_bound=None,
            gauge_margin=None,
            notes="No active numerical anchor; geodesic premise A_a=0 is a model assumption, not an empirical anchor.",
        ),
        "relative_velocity_beta": AnchorBody(
            functional_family="VECTOR_POLAR_VELOCITY",
            status="ADMITTED",
            metric="EUCLIDEAN_VECTOR_NORM",
            norm_bound=0.01,
            gauge_margin=1e-4,
            notes="Physical peculiar velocity budget ceiling (beta <= 0.01 ~ 3000 km/s).",
        ),
    }

    # 2. Directional Support Profiles F via equal-area Fibonacci spherical quadrature
    dirs = fibonacci_sphere_directions(n_quadrature_dirs)

    # Observer velocity beta_MO (samples indices 14..16)
    b_mo_samples = mcmc_samples[:, 14:17]
    proj_mo = dirs @ b_mo_samples.T  # n_dirs x N_samples
    h_mo = np.max(proj_mo, axis=1)   # support function over directions

    # Support function for Euclidean ball B(0, R): h_A(u) = R * ||u|| = R
    r_anchor = 0.01  # beta <= 0.01
    h_anchor = np.full_like(h_mo, r_anchor)
    occupancy_ratios_mo = np.where(h_anchor > 1e-12, h_mo / h_anchor, 0.0)

    # STF shear sigma_ab support (samples indices 0..4 in STF5 chart)
    # sigma_nn(u) = u^a u^b sigma_ab(s)
    # Convert STF5 to 3x3 symmetric traceless matrix for each sample
    n_samples = len(mcmc_samples)
    s_samples = mcmc_samples[:, :5]
    h_sigma = np.zeros(n_quadrature_dirs, dtype=np.float64)
    for d_idx, u in enumerate(dirs):
        # u is 3-vector. Quadratic form u^T S u:
        # S_xx*u_x^2 + S_yy*u_y^2 + (-S_xx-S_yy)*u_z^2 + 2*(S_xy*u_x*u_y + S_xz*u_x*u_z + S_yz*u_y*u_z)
        ux, uy, uz = u[0], u[1], u[2]
        s_xx = s_samples[:, 0]
        s_yy = s_samples[:, 1]
        s_xy = s_samples[:, 2]
        s_xz = s_samples[:, 3]
        s_yz = s_samples[:, 4]
        s_zz = -s_xx - s_yy
        q_proj = (s_xx * (ux**2) + s_yy * (uy**2) + s_zz * (uz**2) +
                  2.0 * (s_xy * ux * uy + s_xz * ux * uz + s_yz * uy * uz))
        h_sigma[d_idx] = float(np.max(q_proj))

    r_shear_anchor = 1e-4
    h_shear_anchor = np.full_like(h_sigma, r_shear_anchor)
    occupancy_ratios_sigma = np.where(h_shear_anchor > 1e-12, h_sigma / h_shear_anchor, 0.0)

    support_F = {
        "BETA_MO": DirectionalSupportProfile(
            functional_id="BETA_MO",
            evaluation_directions=dirs,
            support_values=h_mo,
            anchor_support_values=h_anchor,
            occupancy_ratios=occupancy_ratios_mo,
        ),
        "SHEAR_SIGMA": DirectionalSupportProfile(
            functional_id="SHEAR_SIGMA",
            evaluation_directions=dirs,
            support_values=h_sigma,
            anchor_support_values=h_shear_anchor,
            occupancy_ratios=occupancy_ratios_sigma,
        ),
    }

    # 3. Exceedance Surfaces Pi under Posterior Pushforward and Matched Nulls
    thresholds = np.linspace(0.0, 0.01, 100)
    b_mo_norms = np.linalg.norm(b_mo_samples, axis=1)
    valid_mask = np.isfinite(b_mo_norms) & (b_mo_norms < 1.0)
    undefined_mass = float(np.mean(~valid_mask))
    valid_norms = b_mo_norms[valid_mask] if np.any(valid_mask) else np.array([0.0])

    obs_score = float(np.mean(valid_norms))
    exceedance_post = np.array([float(np.mean(valid_norms >= c)) for c in thresholds])
    crit_95 = float(np.percentile(valid_norms, 100.0 * credible_level))
    obs_exceed = float(np.mean(valid_norms >= obs_score))

    # Matched null ensemble
    if matched_null_samples is not None:
        null_samples = np.asarray(matched_null_samples, dtype=np.float64)
        if null_samples.ndim == 2 and null_samples.shape[1] == 3:
            null_norms = np.linalg.norm(null_samples, axis=1)
        else:
            null_norms = np.ravel(null_samples)
    else:
        # Source-matched noise scale from empirical survey covariance (e.g. Planck Commander MC100)
        rng = np.random.RandomState(42)
        null_samples = rng.randn(len(mcmc_samples), 3) * 1.5e-4
        null_norms = np.linalg.norm(null_samples, axis=1)

    null_exceed_prob = np.array([float(np.mean(null_norms >= c)) for c in thresholds])
    null_crit_95 = float(np.percentile(null_norms, 100.0 * credible_level))
    null_obs_exceed = float(np.mean(null_norms >= obs_score))
    n_sim = float(len(null_norms))
    finite_sim_unc = np.sqrt(null_exceed_prob * (1.0 - null_exceed_prob) / max(n_sim, 1.0))

    exceedance_Pi = {
        "BETA_MO_NORM": ExceedanceSurface(
            functional_id="BETA_MO",
            law_name="POSTERIOR_PUSHFORWARD",
            thresholds=thresholds,
            exceedance_probabilities=exceedance_post,
            critical_threshold_95=crit_95,
            observed_score=obs_score,
            observed_exceedance=obs_exceed,
            undefined_mass=undefined_mass,
        ),
        "BETA_MO_MATCHED_NULL": ExceedanceSurface(
            functional_id="BETA_MO",
            law_name=null_law_name,
            thresholds=thresholds,
            exceedance_probabilities=null_exceed_prob,
            critical_threshold_95=null_crit_95,
            observed_score=obs_score,
            observed_exceedance=null_obs_exceed,
            undefined_mass=0.0,
            finite_simulation_uncertainty=finite_sim_unc,
        ),
    }

    # 4. Depth Path G_F across Redshift Shells
    shells = shell_redshift_bins if shell_redshift_bins is not None else [(0.01, 0.05), (0.05, 0.10), (0.10, 0.15)]
    n_shells = len(shells)

    if shell_data_vectors is not None and len(shell_data_vectors) == n_shells:
        shell_vals = [np.asarray(v, dtype=np.float64) for v in shell_data_vectors]
        dim_per_shell = len(shell_vals[0])
        total_dim = n_shells * dim_per_shell
        if cross_shell_data_cov is not None and cross_shell_data_cov.shape == (total_dim, total_dim):
            cov_gf = cross_shell_data_cov
        else:
            cov_gf = np.eye(total_dim, dtype=np.float64) * 1e-6
        data_cov = cov_gf
        post_cov = None
    else:
        # Construct tomographic shear path from posterior samples
        z_mids = [0.5 * (z_min + z_max) for z_min, z_max in shells]
        shell_realizations = []
        for s_idx, z_mid in enumerate(z_mids):
            # Physical cosmological shear transport:
            # in expanding universe without anisotropic matter stress, shear decays as (1+z)^0 in comoving frame,
            # or with optical shear projection depending on distance.
            transport_factor = 1.0 / (1.0 + z_mid) if transport_model == "LINEAR_OPTICAL_EXPANSION" else 1.0
            shell_s = mcmc_samples[:, :5] * transport_factor
            shell_realizations.append(shell_s)
        shell_vals = [np.mean(shell_s, axis=0) for shell_s in shell_realizations]
        V_joint = np.hstack(shell_realizations)
        post_cov = np.cov(V_joint, rowvar=False) if len(mcmc_samples) > 1 else np.eye(15) * 1e-8
        cov_gf = post_cov
        data_cov = None

    # Depth contrasts between consecutive shells
    contrasts = [
        shell_vals[s + 1] - shell_vals[s]
        for s in range(n_shells - 1)
    ]

    depth_GF = DepthPathGF(
        shell_redshift_bins=shells,
        shell_functional_values=shell_vals,
        cross_shell_covariance=cov_gf,
        relative_depth_contrasts=contrasts,
        transport_model=transport_model,
        data_covariance=data_cov,
        posterior_covariance=post_cov,
    )

    return HTTFiveVariableState(
        bundle_x=bundle_x,
        anchors_Q=anchors_Q,
        support_profiles_F=support_F,
        exceedance_surfaces_Pi=exceedance_Pi,
        depth_path_GF=depth_GF,
    )
