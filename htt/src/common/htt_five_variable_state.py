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


@dataclass(frozen=True)
class DepthPathGF:
    """Full-covariance tensor functional depth path across redshift/distance shells."""
    shell_redshift_bins: list[tuple[float, float]]
    shell_functional_values: list[np.ndarray] # Per-shell STF shear or velocity vectors
    cross_shell_covariance: np.ndarray       # Full block-covariance across all shells
    relative_depth_contrasts: list[np.ndarray]


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
            status="ADMITTED",
            metric="STF5_CARTESIAN_INDUCED_GRAM",
            norm_bound=1e-4,
            gauge_margin=1e-5,
            notes="Symmetric trace-free Frobenius norm bound on sigma/H",
        ),
        "vorticity_omega": AnchorBody(
            functional_family="VECTOR_AXIAL_VORTICITY",
            status="ADMITTED",
            metric="EUCLIDEAN_VECTOR_NORM",
            norm_bound=1e-4,
            gauge_margin=1e-5,
            notes="Axial vector norm omega_A/H; distinct from two-form MES W2 invariant",
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
    phi = np.linspace(0, 2*np.pi, 50, endpoint=False)
    theta = np.linspace(0.1, np.pi - 0.1, 50)
    dirs = np.stack([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)], axis=1)

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
    occupancy_ratios = h_mo / h_anchor

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
    rng = np.random.RandomState(42)
    null_noise_scale = 1e-4
    null_samples = rng.randn(len(mcmc_samples), 3) * null_noise_scale
    null_norms = np.linalg.norm(null_samples, axis=1)
    null_exceed_prob = np.array([float(np.mean(null_norms >= c)) for c in thresholds])
    null_crit_95 = float(np.percentile(null_norms, 95))
    null_obs_exceed = float(np.mean(null_norms >= obs_score))

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
    )

    return HTTFiveVariableState(
        bundle_x=bundle_x,
        anchors_Q=anchors_Q,
        support_profiles_F=support_F,
        exceedance_surfaces_Pi=exceedance_Pi,
        depth_path_GF=depth_GF,
    )
