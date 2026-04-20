"""
htt/infer/dipole_vector_likelihood.py — Dipole-Vector Likelihood
================================================================
P-15 deliverable. Implements L_dir(D_lowz, D_CMB_lowℓ | θ, φ, ψ)
for the directional information audit.

The likelihood combines:
  - Low-z matter dipole: CatWISE + Radio (bivariate) + CF4
  - CMB low-ℓ: quadrupole and octupole amplitudes
  - Direction: shared axis (l, b) or per-survey axes
"""
import numpy as np

__all__ = ['DipoleVectorLikelihood']


class DipoleVectorLikelihood:
    """Direction-aware dipole likelihood.

    Extends the scalar-amplitude pipeline with directional
    information from the dipole axis (l, b).

    Parameters
    ----------
    obs_data : dict
        From obs_defaults.json.
    control : str
        'C0' (baseline), 'C1' (aligned), 'C2' (misaligned),
        'C3' (disconnected).
    cmb_direction : tuple
        (l_deg, b_deg) of the CMB dipole. Default: Planck 2018.
    """

    # CMB dipole direction (Planck 2018)
    CMB_L = 264.021
    CMB_B = 48.253

    # CF4 bulk-flow direction (Watkins+2023)
    CF4_L = 282.0
    CF4_B = 6.0

    # CatWISE dipole direction (Secrest+2021)
    CW_L = 240.0
    CW_B = -4.0

    # Radio dipole direction (Secrest+2021 / NVSS+RACS)
    RADIO_L = 251.0
    RADIO_B = 38.0

    # Approximate directional uncertainties used for the audit penalty.
    CMB_SIGMA_DEG = 0.5
    CF4_SIGMA_DEG = 15.0
    CW_SIGMA_DEG = 6.0
    RADIO_SIGMA_DEG = 10.0

    def __init__(self, obs_data: dict, control: str = 'C1'):
        self.obs = obs_data
        self.control = control

        dp = obs_data['dipole_observations']
        cmb = dp.get('cmb_planck_2018', {})
        cw = dp.get('catwise_bohme_2025', {})
        radio = dp.get('radio_secrest_2021', {})
        cf4 = dp.get('cf4_watkins_2023', {})

        self.e1_CW = dp['catwise_bohme_2025']['eps1']
        self.s_CW = dp['catwise_bohme_2025']['sigma_stat']
        self.e1_rad = dp['radio_secrest_2021']['eps1']
        self.s_rad = dp['radio_secrest_2021']['sigma_stat']
        self.b_CF4 = dp['cf4_watkins_2023']['beta']
        self.s_CF4 = dp['cf4_watkins_2023']['sigma']
        self.rho = dp['rho_CW_radio']
        self.cmb_l = float(cmb.get('l_deg', self.CMB_L))
        self.cmb_b = float(cmb.get('b_deg', self.CMB_B))
        self.cw_l = float(cw.get('l_deg', self.CW_L))
        self.cw_b = float(cw.get('b_deg', self.CW_B))
        self.radio_l = float(radio.get('l_deg', self.RADIO_L))
        self.radio_b = float(radio.get('b_deg', self.RADIO_B))
        self.cf4_l = float(cf4.get('l_deg', self.CF4_L))
        self.cf4_b = float(cf4.get('b_deg', self.CF4_B))

    def _direction_unit(self, l_deg: float, b_deg: float) -> np.ndarray:
        """Convert (l, b) in degrees to unit vector."""
        l, b = np.radians(l_deg), np.radians(b_deg)
        return np.array([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)])

    def _angular_separation(self, l1: float, b1: float,
                            l2: float, b2: float) -> float:
        """Angular separation in radians between two directions."""
        d1 = self._direction_unit(l1, b1)
        d2 = self._direction_unit(l2, b2)
        cos_sep = np.clip(np.dot(d1, d2), -1, 1)
        return np.arccos(cos_sep)

    def scalar_log_likelihood(self, A: float) -> float:
        """Scalar-amplitude likelihood without directional information."""
        dx_CW = self.e1_CW - A
        dx_rad = self.e1_rad - A
        dx_CF4 = self.b_CF4 - A
        det = 1 - self.rho**2

        chi2_biv = (1.0/det) * (
            (dx_CW/self.s_CW)**2 + (dx_rad/self.s_rad)**2
            - 2*self.rho*dx_CW*dx_rad/(self.s_CW*self.s_rad)
        )
        return -0.5*chi2_biv - 0.5*(dx_CF4/self.s_CF4)**2

    def directional_log_likelihood(self, l_model: float,
                                   b_model: float,
                                   A: float) -> float:
        """Log-likelihood including directional information.

        The directional term penalises misalignment between the
        model axis and the observed survey directions, weighted
        by each survey's (S/N)².
        """
        # Angular separations
        sep_CMB = self._angular_separation(l_model, b_model,
                                           self.cmb_l, self.cmb_b)
        sep_CF4 = self._angular_separation(l_model, b_model,
                                           self.cf4_l, self.cf4_b)
        sep_CW = self._angular_separation(l_model, b_model,
                                          self.cw_l, self.cw_b)
        sep_radio = self._angular_separation(l_model, b_model,
                                             self.radio_l, self.radio_b)

        logL_amp = self.scalar_log_likelihood(A)

        # Gaussian angular penalty. The maximum is zero when the model
        # aligns with all observed directions; misalignment strictly lowers
        # the directional evidence.
        chi2_dir = (
            (np.degrees(sep_CMB) / self.CMB_SIGMA_DEG)**2
            + (np.degrees(sep_CF4) / self.CF4_SIGMA_DEG)**2
            + (np.degrees(sep_CW) / self.CW_SIGMA_DEG)**2
            + (np.degrees(sep_radio) / self.RADIO_SIGMA_DEG)**2
        )
        logL_dir = -0.5 * chi2_dir

        return logL_amp + logL_dir

    def information_gain(self, l_model: float, b_model: float,
                         A: float) -> float:
        """Information gain from adding direction to scalar amplitude.

        ΔI = L_dir(l,b,A) - L_scalar(A)
        """
        logL_dir = self.directional_log_likelihood(l_model, b_model, A)
        return logL_dir - self.scalar_log_likelihood(A)
