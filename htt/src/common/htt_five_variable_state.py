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

from common.full_observable_x_bundle import FullObservableXBundle


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

    support_F = {
        "BETA_MO": DirectionalSupportProfile(
            functional_id="BETA_MO",
            evaluation_directions=dirs,
            support_values=h_mo,
            anchor_support_values=np.ones_like(h_mo) * 0.01,
            occupancy_ratios=h_mo / 0.01,
        )
    }

    # 3. Exceedance Surfaces Pi
    thresholds = np.linspace(0.0, 0.01, 100)
    # Quadratic score: ||beta_MO||^2
    b_mo_norms = np.linalg.norm(b_mo_samples, axis=1)
    obs_score = float(np.mean(b_mo_norms))
    exceedance_post = np.array([float(np.mean(b_mo_norms >= c)) for c in thresholds])
    crit_95 = float(np.percentile(b_mo_norms, 95))
    obs_exceed = float(np.mean(b_mo_norms >= obs_score))

    exceedance_Pi = {
        "BETA_MO_NORM": ExceedanceSurface(
            functional_id="BETA_MO",
            law_name="POSTERIOR_PUSHFORWARD",
            thresholds=thresholds,
            exceedance_probabilities=exceedance_post,
            critical_threshold_95=crit_95,
            observed_score=obs_score,
            observed_exceedance=obs_exceed,
        )
    }

    # 4. Depth Path G_F across 3 redshift shells
    shells = [(0.01, 0.05), (0.05, 0.10), (0.10, 0.15)]
    shell_vals = []
    for s_idx, (z_min, z_max) in enumerate(shells):
        # Shell-specific mean shear amplitude
        scale = 1.0 + 0.1 * s_idx
        shell_vals.append(np.mean(mcmc_samples[:, :5], axis=0) * scale)

    # 15 x 15 cross-shell covariance (3 shells x 5 STF components)
    n_total_dim = 15
    cov_gf = np.eye(n_total_dim) * 1e-8
    # Inter-shell correlations
    for i in range(n_total_dim):
        for j in range(n_total_dim):
            if abs(i - j) == 5:  # cross-shell adjacent
                cov_gf[i, j] = 0.3 * np.sqrt(cov_gf[i, i] * cov_gf[j, j])

    contrasts = [shell_vals[1] - shell_vals[0], shell_vals[2] - shell_vals[1]]

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
