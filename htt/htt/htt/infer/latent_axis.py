"""
htt/infer/latent_axis.py — Shared Latent-Axis Dipole Model
============================================================
P-15 deliverable. The latent-axis model posits a single dipole
direction (l, b) shared by all surveys, with per-survey amplitudes
and nuisance parameters.

Parameters:
  - (l, b): Galactic longitude/latitude of the common dipole axis
  - A: common amplitude (= β in the tilt interpretation)
  - δ_CW, δ_rad: survey-specific amplitude offsets
  - σ_sys_CW, σ_sys_rad: systematic uncertainty floors

Channel ``c`` is excluded while the PR-120 CF4 findings remain OPEN.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Tuple

from htt.core.cf4_observational_input import OPEN_FINDING_IDS

__all__ = ['LatentAxisModel', 'LatentAxisParams', 'dipole_projection']


@dataclass
class LatentAxisParams:
    """Parameters for the latent-axis dipole model."""
    l_deg: float        # Galactic longitude [deg]
    b_deg: float        # Galactic latitude [deg]
    A: float            # Common amplitude (β)
    delta_CW: float = 0.0    # CatWISE offset
    delta_rad: float = 0.0   # Radio offset
    sigma_sys_CW: float = 0.0
    sigma_sys_rad: float = 0.0

    @property
    def l_rad(self) -> float:
        return np.radians(self.l_deg)

    @property
    def b_rad(self) -> float:
        return np.radians(self.b_deg)

    @property
    def direction(self) -> np.ndarray:
        """Unit vector in Galactic coordinates."""
        cl, sl = np.cos(self.l_rad), np.sin(self.l_rad)
        cb, sb = np.cos(self.b_rad), np.sin(self.b_rad)
        return np.array([cb * cl, cb * sl, sb])


def dipole_projection(direction: np.ndarray,
                      obs_direction: np.ndarray,
                      amplitude: float) -> float:
    """Project a dipole onto an observation direction.

    Returns the observed amplitude = A * cos(θ), where θ is the
    angle between the dipole axis and the observation direction.
    For number-count dipoles, the full amplitude is observed
    (projection factor = 1) because ε₁ is the monopole amplitude.
    """
    cos_theta = np.dot(direction, obs_direction)
    return amplitude * cos_theta


class LatentAxisModel:
    """Shared latent-axis dipole model.

    The model assumes all surveys measure the same underlying
    dipole direction (l, b) with a common amplitude A, modulated
    by per-survey offsets and nuisances.

    Parameters
    ----------
    obs_data : dict
        Observational data from obs_defaults.json.
    """

    # CMB dipole direction (Planck 2018)
    CMB_L_DEG = 264.021
    CMB_B_DEG = 48.253

    def __init__(self, obs_data: dict):
        self.obs = obs_data
        self.ndim = 7  # l, b, A, δ_CW, δ_rad, σ_sys_CW, σ_sys_rad
        self.excluded_channels = ('c',)
        self.cf4_channel_status = 'QUARANTINED_OPEN_FINDINGS'
        self.cf4_finding_ids = OPEN_FINDING_IDS

        # Extract observational values
        dp = obs_data['dipole_observations']
        self.e1_CW = dp['catwise_bohme_2025']['eps1']
        self.s_CW = dp['catwise_bohme_2025']['sigma_stat']
        self.e1_rad = dp['radio_secrest_2021']['eps1']
        self.s_rad = dp['radio_secrest_2021']['sigma_stat']
        self.rho = dp['rho_CW_radio']

    def prior_transform(self, u: np.ndarray) -> np.ndarray:
        """Map [0,1]^7 → the active non-CF4 parameter space."""
        theta = np.empty(7)
        theta[0] = u[0] * 360          # l ∈ [0, 360)
        theta[1] = np.degrees(np.arcsin(2*u[1] - 1))  # b ∈ [-90, 90]
        theta[2] = 10**(u[2] * 4 - 6)  # A ∈ [10⁻⁶, 10⁻²] log-uniform
        theta[3] = (u[3] - 0.5) * 2e-3  # δ_CW ∈ [-1e-3, 1e-3]
        theta[4] = (u[4] - 0.5) * 2e-3  # δ_rad
        theta[5] = u[5] * 5e-4          # σ_sys_CW ∈ [0, 5e-4]
        theta[6] = u[6] * 5e-4          # σ_sys_rad
        return theta

    def log_likelihood(self, theta: np.ndarray) -> float:
        """Log-likelihood for the latent-axis model."""
        l, b, A, d_CW, d_rad, ss_CW, ss_rad = theta

        # Predicted amplitudes
        pred_CW = A + d_CW
        pred_rad = A + d_rad

        # Effective uncertainties (stat + sys in quadrature)
        s_eff_CW = np.sqrt(self.s_CW**2 + ss_CW**2)
        s_eff_rad = np.sqrt(self.s_rad**2 + ss_rad**2)

        # Channel b: bivariate Gaussian for CW + Radio
        dx_CW = self.e1_CW - pred_CW
        dx_rad = self.e1_rad - pred_rad
        rho = self.rho
        det = 1 - rho**2
        if det <= 0:
            return -1e30

        chi2_biv = (1.0 / det) * (
            (dx_CW / s_eff_CW)**2
            + (dx_rad / s_eff_rad)**2
            - 2 * rho * dx_CW * dx_rad / (s_eff_CW * s_eff_rad)
        )
        logL_biv = -0.5 * chi2_biv - np.log(2*np.pi*s_eff_CW*s_eff_rad*np.sqrt(det))

        # Direction prior: uniform on sphere (already encoded in prior_transform)
        # No additional direction-dependent term needed

        return logL_biv
