"""
htt/nulls/mask_leakage.py — Galactic Mask Leakage Null (N2)
============================================================
Simulates residual Galactic contamination leaking through the
sky mask, creating a spurious dipole correlated with |b_gal|.
"""
import numpy as np
from .common_interface import NullFamily, NullDataset

__all__ = ['MaskLeakageNull']


class MaskLeakageNull(NullFamily):
    """N2: Galactic mask-leakage systematic.

    Inflates σ_CW and σ_rad proportional to Galactic latitude
    dependence, simulating foreground contamination.
    """
    name = "mask_leakage"

    def __init__(self, contamination_frac: float = 0.15):
        self.contamination_frac = contamination_frac

    def generate(self, seed: int, obs_base: dict) -> NullDataset:
        rng = np.random.default_rng(seed)

        cw = obs_base['dipole_observations']['catwise_bohme_2025']
        rad = obs_base['dipole_observations']['radio_secrest_2021']
        cf4 = obs_base['dipole_observations']['cf4_watkins_2023']

        # Galactic leakage adds a systematic dipole aligned with b_gal
        A_gal = self.contamination_frac * cw['eps1']
        e1_CW = abs(rng.normal(A_gal, cw['sigma_stat']))
        e1_rad = abs(rng.normal(A_gal * 0.5, rad['sigma_stat']))
        b_CF4 = abs(rng.normal(0, cf4['sigma']))

        return NullDataset(
            seed=seed, family=self.name,
            e1_CW=e1_CW, e1_CW_s=cw['sigma_stat'],
            e1_rad=e1_rad, e1_rad_s=rad['sigma_stat'],
            rho_CW_radio=0.3,  # elevated correlation from shared foreground
            b_CF4=b_CF4, b_CF4_s=cf4['sigma'],
            eps2=3.56e-6, eps3=6.07e-6,
            systematic_amplitude=A_gal,
            systematic_type='mask_leakage',
        )
